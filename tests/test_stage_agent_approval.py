"""ADR-0069: `stage_approval: agent` — agent tự nghiệm thu giai đoạn (chủ dự án 2026-11-04, D-342). Khoá có hiệu lực khi CẢ
xt.yaml ở cây làm việc LẪN bản đã commit ở nhánh chính của remote đều khai; `init --adopt`, dạng mờ và bản trình đã đổi
vẫn bị chặn (ADR-0058 giữ cho mọi trường hợp còn lại)."""

import json
import os
import subprocess
import sys
import unittest
import unittest.mock
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / ".claude" / "hooks"))
sys.path.insert(0, str(Path(__file__).resolve().parent))  # test_stage, test_xt_cli
import guard
import xt
from test_stage import human_env
from test_xt_cli import TmpRepoCase, run_main

SHA = "c" * 40


class StageAgentApprovalCliTest(TmpRepoCase):
    def setUp(self):
        super().setUp()
        self.init_repo()
        self.git("config", "user.email", "chu@example.invalid")
        self.git("config", "user.name", "chu")
        self.git("config", "commit.gpgsign", "false")
        self.origin = self.tmp / "origin.git"
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(self.origin)], check=True)
        self.git("remote", "add", "origin", str(self.origin))
        self.enterContext(human_env(CLAUDE_PROJECT_DIR=str(self.repo)))
        self.commit("khởi tạo")
        self.git("push", "-q", "origin", "main")

    def commit(self, msg):
        (self.repo / "f.txt").write_text(msg + "\n", encoding="utf-8")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", msg)
        return self.git("rev-parse", "HEAD").strip()

    def stage(self, *args, agent=False):
        env = {"CLAUDE_CODE_SESSION_ID": "s-1"} if agent else {}
        with unittest.mock.patch.dict(os.environ, env):
            return run_main("stage", *args)

    def led(self):
        return json.loads((self.repo / xt.STAGE_LEDGER).read_text(encoding="utf-8"))

    def set_key(self, value, commit=True, push=True):
        (self.repo / "xt.yaml").write_text(f"lint: ''\nstage_approval: {value}\n", encoding="utf-8")
        if commit:
            self.git("add", "-A")
            self.git("commit", "-q", "-m", f"stage_approval {value}")
        if push:
            self.git("push", "-q", "origin", "main")

    def submit(self):
        sha = self.commit(f"bản {len(self.led()['history'])}")
        rc, _, err = self.stage("submit", "--evidence", "chạy `make demo`", agent=True)
        self.assertEqual(rc, 0, err)
        return sha

    def test_key_needs_tree_and_committed_on_main(self):
        self.assertFalse(xt.stage_agent_approval(self.repo))  # không khai → chỉ người (ADR-0058)
        self.set_key("agent", commit=False, push=False)  # chỉ cây làm việc: phiên tự cấp quyền → không
        self.assertFalse(xt.stage_agent_approval(self.repo))
        self.set_key("agent", push=False)  # commit cục bộ, chưa lên nhánh chính của remote → không
        self.assertFalse(xt.stage_agent_approval(self.repo))
        self.git("push", "-q", "origin", "main")
        self.assertTrue(xt.stage_agent_approval(self.repo))
        self.set_key("human", commit=False, push=False)  # cây làm việc rút lại → không
        self.assertFalse(xt.stage_agent_approval(self.repo))
        self.set_key("agent", commit=False, push=False)  # cây trùng bản đã commit → có hiệu lực lại
        self.assertTrue(xt.stage_agent_approval(self.repo))
        for exc in (OSError("x"), ValueError("x")):
            with unittest.mock.patch.object(xt, "_xt_keys", side_effect=exc):
                self.assertFalse(xt.stage_agent_approval(self.repo))  # không đọc được → chỉ người

    def test_default_is_human_only(self):
        self.stage("init", agent=True)
        sha = self.submit()
        rc, _, err = self.stage("approve", "--sha", sha, "--note", "ok", agent=True)
        self.assertEqual(rc, 2)
        self.assertIn("chỉ người duyệt", err)
        self.assertEqual(self.led()["status"], "awaiting_approval")

    def test_agent_approves_unchanged_submission(self):
        self.set_key("agent")
        self.stage("init", agent=True)
        sha = self.submit()
        out = self.stage("status")[1]
        self.assertIn(f"chờ duyệt bản {sha[:12]}", out)
        self.assertIn("stage_approval: agent", out)
        rc, out, err = self.stage(
            "approve", "--sha", sha[:7], "--note", "MVP: 3 luồng chính chạy, smoke xanh", agent=True
        )
        self.assertEqual(rc, 0, err)
        led = self.led()
        self.assertEqual((led["stage"], led["status"]), (2, "active"))
        ap = [e for e in led["history"] if e["event"] == "approve"][-1]
        self.assertEqual((ap["by"], ap["session"], ap["sha"]), (xt.STAGE_AGENT_BY, "s-1", sha))
        self.assertEqual(self.stage("status")[0], 0)  # sổ phát lại hợp lệ
        # `init --adopt` vẫn chỉ người dù đã bật khoá
        self.git("rm", "-q", "--cached", xt.STAGE_LEDGER)
        (self.repo / xt.STAGE_LEDGER).unlink()
        rc, _, err = self.stage("init", "--adopt", "2", "--evidence", "v1", agent=True)
        self.assertEqual(rc, 2)
        self.assertIn("chỉ người duyệt", err)

    def test_agent_refuses_changed_submission_human_still_can(self):
        self.set_key("agent")
        self.stage("init", agent=True)
        sha = self.submit()
        self.commit("mã đổi sau bản trình")
        rc, _, err = self.stage("approve", "--sha", sha, "--note", "ok", agent=True)
        self.assertEqual(rc, 2)
        self.assertIn("agent không duyệt được", err)
        self.assertIn("1 file đổi", err)
        self.assertEqual(self.led()["status"], "awaiting_approval")
        rc, _, err = self.stage("approve", "--sha", sha, "--note", "người duyệt bản cũ")
        self.assertEqual(rc, 0, err)
        self.assertEqual([e["by"] for e in self.led()["history"] if e["event"] == "approve"], ["chu@example.invalid"])

    def test_stage_facts_and_next_step_route(self):
        self.stage("init", agent=True)
        self.assertFalse(xt.stage_facts(self.repo)["agent_approval"])
        self.set_key("agent")
        self.assertTrue(xt.stage_facts(self.repo)["agent_approval"])
        wait = {"cycle": "C-001", "stage": 1, "status": "awaiting_approval", "sha": SHA, "agent_approval": True}
        out = xt._step_stage(wait, " (T-009 chờ pháp lý)")
        self.assertEqual(out["action"], "stage-approve")
        self.assertIn(f"stage approve --sha {SHA[:12]}", out["reason"])
        self.assertIn("T-009 chờ pháp lý", out["reason"])
        self.assertEqual(out["missing"], ["`stage approve` (agent, ADR-0069)"])
        self.assertEqual(xt._step_stage({**wait, "agent_approval": False})["action"], "wait-approval")
        sub = xt._step_stage({**wait, "status": "active", "sha": None})
        self.assertEqual(
            (sub["action"], sub["missing"]), ("stage-submit", ["`stage submit`", "`stage approve` (agent, ADR-0069)"])
        )
        self.assertIn("rồi `stage approve`", sub["reason"])
        lock = xt._harden_stage_lock(wait)
        self.assertEqual((lock["action"], lock["missing"]), ("blocked", ["`stage approve` (agent, ADR-0069)"]))
        self.assertIn("agent `stage approve` bản đã trình", lock["reason"])
        lock = xt._harden_stage_lock({**wait, "status": "active", "sha": None})
        self.assertIn("rồi agent `stage approve`", lock["reason"])


GIT_ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@x", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@x"}


def git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, env={**os.environ, **GIT_ENV})


class StageAgentApprovalGuardTest(TmpRepoCase):
    """Guard: `stage approve` dạng chữ rõ được cho qua khi khoá có hiệu lực; dạng mờ, `init --adopt`, strict → vẫn deny."""

    PLAIN = "python3 scripts/xt.py stage approve --sha 1234567 --note ok"

    def setUp(self):
        super().setUp()
        guard._STAGE_AGENT.clear()
        self.addCleanup(guard._STAGE_AGENT.clear)
        self.enterContext(unittest.mock.patch.dict(os.environ, {"XT_GUARD_POLICY": "", "XT_GUARD_PHASE": ""}))

    def project(self, committed, tree=None, push=True):
        origin, proj = self.tmp / "origin.git", self.tmp / "proj"
        git(self.tmp, "init", "-q", "--bare", "-b", "main", str(origin))
        git(self.tmp, "init", "-q", "-b", "main", str(proj))
        git(proj, "remote", "add", "origin", str(origin))
        (proj / "xt.yaml").write_text(f"lint: ''\nstage_approval: {committed}\n", encoding="utf-8")
        git(proj, "add", "xt.yaml")
        git(proj, "commit", "-q", "-m", "init")
        if push:
            git(proj, "push", "-q", "origin", "main")
        if tree is not None:
            (proj / "xt.yaml").write_text(f"stage_approval: {tree}\n", encoding="utf-8")
        return proj

    def decide(self, proj, cmd):
        return dict(guard.apply_policy(guard.bash_decision(cmd, str(proj), str(proj)))).get("decision")

    def test_value_parse(self):
        self.assertEqual(
            guard._stage_approval_value("a: 1\nstage_approval: human\nstage_approval: 'agent' # x\n"), "agent"
        )
        self.assertEqual(guard._stage_approval_value("lint: ''\n"), "")

    def test_plain_approve_allowed_when_key_effective(self):
        proj = self.project("agent")
        self.assertTrue(guard.agent_stage_approval(str(proj)))
        self.assertTrue(guard.agent_stage_approval(str(proj)))  # cache
        self.assertNotEqual(self.decide(proj, self.PLAIN), "deny")
        self.assertNotEqual(
            self.decide(proj, "cd . && python3 .xtemplates/scripts/xt.py stage approve --sha abc1234 --note 'MVP đạt'"),
            "deny",
        )
        for cmd in (
            "python3 scripts/xt.py stage init --adopt 2 --evidence v1",
            'python3 scripts/xt.py stage "$(echo approve)" --sha 1234567',
            'python3 "$XT" stage approve --sha 1234567',
            "python3 scripts/xt.py stage approve --sha `git rev-parse HEAD`",
            "echo approve | xargs -I{} python3 scripts/xt.py stage {} --sha 1234567",
        ):
            with self.subTest(cmd=cmd):
                self.assertEqual(self.decide(proj, cmd), "deny")

    def test_key_needs_tree_and_committed(self):
        for committed, tree, push in (("human", "agent", True), ("agent", "human", True), ("agent", None, False)):
            with self.subTest(committed=committed, tree=tree, push=push):
                guard._STAGE_AGENT.clear()
                proj = self.project(committed, tree, push)
                self.assertFalse(guard.agent_stage_approval(str(proj)))
                self.assertEqual(self.decide(proj, self.PLAIN), "deny")
                subprocess.run(["rm", "-rf", str(self.tmp / "origin.git"), str(proj)], check=True)
        self.assertFalse(guard.agent_stage_approval(str(self.tmp / "khong-co")))  # không có xt.yaml

    def test_strict_policy_keeps_deny(self):
        proj = self.project("agent")
        with unittest.mock.patch.dict(os.environ, {"XT_GUARD_POLICY": "strict"}):
            guard._STAGE_AGENT.clear()
            self.assertFalse(guard.agent_stage_approval(str(proj)))
            self.assertEqual(self.decide(proj, self.PLAIN), "deny")


if __name__ == "__main__":
    unittest.main()
