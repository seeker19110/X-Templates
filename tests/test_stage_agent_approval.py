"""ADR-0069: `stage_approval: agent` — agent tự nghiệm thu giai đoạn (chủ dự án 2026-11-04, D-352). Khoá có hiệu lực khi CẢ
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

    def test_changed_submission_refused_for_everyone_while_key_on(self):
        """Review harden F1: khoá bật → bản đã đổi không duyệt được bởi CẢ agent lẫn tiến trình không mang biến agent
        (`env -u CLAUDECODE …` né được nhánh agent); tắt khoá thì người duyệt như ADR-0058."""
        self.set_key("agent")
        self.stage("init", agent=True)
        sha = self.submit()
        self.commit("mã đổi sau bản trình")
        rc, _, err = self.stage("approve", "--sha", sha, "--note", "ok", agent=True)
        self.assertEqual(rc, 2)
        self.assertIn("agent không duyệt được bản đã đổi", err)
        self.assertIn("1 file đổi", err)
        rc, _, err = self.stage("approve", "--sha", sha, "--note", "né biến agent")
        self.assertEqual(rc, 2)
        self.assertIn("`stage_approval: agent` đang bật — không duyệt được bản đã đổi", err)
        self.assertEqual(self.led()["status"], "awaiting_approval")
        self.set_key("human")
        rc, _, err = self.stage("approve", "--sha", sha, "--note", "người duyệt bản cũ")
        self.assertEqual(rc, 0, err)
        ap = [e for e in self.led()["history"] if e["event"] == "approve"]
        self.assertEqual([(e["by"], "session" in e) for e in ap], [("chu@example.invalid", False)])

    def test_agent_approves_only_mvp(self):
        """Review harden F6: chủ dự án cho agent "tuyên bố đạt MVP" — giai đoạn 2 trở đi chỉ người."""
        self.set_key("agent")
        self.stage("init", agent=True)
        sha = self.submit()
        self.assertEqual(self.stage("approve", "--sha", sha, "--note", "MVP", agent=True)[0], 0)
        sha = self.submit()
        rc, _, err = self.stage("approve", "--sha", sha, "--note", "giai đoạn 2", agent=True)
        self.assertEqual(rc, 2)
        self.assertIn("agent chỉ tự nghiệm thu MVP (giai đoạn 1) — giai đoạn 2", err)
        rc, _, err = self.stage("approve", "--sha", sha, "--note", "người duyệt")
        self.assertEqual(rc, 0, err)
        self.assertEqual(self.led()["stage"], 3)

    def test_set_head_does_not_grant_key(self):
        """Review harden F2: `git remote set-head origin <nhánh agent>` không cấp khoá — chỉ đọc `origin/main|master`."""
        self.set_key("human")
        self.git("checkout", "-q", "-b", "feat")
        self.set_key("agent", push=False)
        self.git("push", "-q", "origin", "feat")
        self.git("remote", "set-head", "origin", "feat")
        self.assertEqual(self.git("rev-parse", "--abbrev-ref", "origin/HEAD").strip(), "origin/feat")
        self.assertFalse(xt.stage_agent_approval(self.repo))
        proj = str(self.repo)
        guard._STAGE_AGENT.clear()
        self.addCleanup(guard._STAGE_AGENT.clear)
        self.assertFalse(guard.agent_stage_approval(proj))

    def test_stage_approval_is_hard_key(self):
        """Review harden F3: PR đổi `stage_approval` luôn người merge, như `merge_hard_exceptions`."""
        self.assertEqual(
            xt._hard_key_lines("a: 1\nstage_approval: agent\nmerge_hard_exceptions: human\n"),
            ["stage_approval=agent", "merge_hard_exceptions=human"],
        )
        for before, after, changed in (
            ("stage_approval: human\n", "stage_approval: agent\n", True),
            ("lint: x\n", "lint: x\nstage_approval: agent\n", True),
            (
                "stage_approval: agent\nmerge_hard_exceptions: auto\n",
                "stage_approval: agent\nmerge_hard_exceptions: auto\n",
                False,
            ),
            ("stage_approval: agent\n", "stage_approval: agent\nstage_approval: agent\n", True),  # khoá lặp
            ("lint: a\n", "lint: b\n", False),
        ):
            with self.subTest(before=before, after=after):
                reads = iter([(before, False), (after, False)])
                with unittest.mock.patch.object(xt, "_contents_read", side_effect=lambda *a: next(reads)):
                    self.assertEqual(xt._hard_key_changed("o/r", "b", "h"), changed)
        self.assertIn("`stage_approval`", xt.HARD_KEY_REASON)

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
        for cmd in (
            self.PLAIN,
            "python3 .xtemplates/scripts/xt.py stage approve --sha abc1234 --note 'MVP đạt'",
            "python scripts/xt.py stage approve --sha=abc1234",
            f"python3 {proj}/scripts/xt.py stage approve --sha abc1234",
            "scripts/xt.py stage approve --note ok --sha abc1234",
        ):
            with self.subTest(cmd=cmd):
                self.assertNotEqual(self.decide(proj, cmd), "deny")
        for cmd in (
            "python3 scripts/xt.py stage init --adopt 2 --evidence v1",
            'python3 scripts/xt.py stage "$(echo approve)" --sha 1234567',
            'python3 "$XT" stage approve --sha 1234567',
            "python3 scripts/xt.py stage approve --sha `git rev-parse HEAD`",
            "echo approve | xargs -I{} python3 scripts/xt.py stage {} --sha 1234567",
            # review harden F1: né biến agent, gán biến, cờ trình thông dịch, xt.py khác, nối lệnh, cờ lạ
            "env -u CLAUDECODE -u CLAUDE_CODE_SESSION_ID -u AI_AGENT " + self.PLAIN,
            "env -i PATH=/usr/bin " + self.PLAIN,
            "unset CLAUDECODE; " + self.PLAIN,
            "CLAUDE_PROJECT_DIR=/tmp/khac " + self.PLAIN,
            "PYTHONPATH=/tmp " + self.PLAIN,
            "python3 -c 'import sys' scripts/xt.py stage approve --sha 1234567",
            "python3 -m pdb scripts/xt.py stage approve --sha 1234567",
            "python3 -i scripts/xt.py stage approve --sha 1234567",
            "python3 /tmp/x/xt.py stage approve --sha 1234567",
            "cd . && " + self.PLAIN,
            "python3 scripts/xt.py stage approve --sha 1234567 --adopt",
            "python3 scripts/xt.py stage approve --sha",
            "bash -c '" + self.PLAIN + "'",
        ):
            with self.subTest(cmd=cmd):
                self.assertEqual(self.decide(proj, cmd), "deny")
        sub = proj / "sub"
        sub.mkdir()
        decision = dict(guard.apply_policy(guard.bash_decision(self.PLAIN, str(proj), str(sub)))).get("decision")
        self.assertEqual(decision, "deny")  # đường tương đối ngoài gốc dự án: không phải xt.py của dự án

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


class XtInProcessGuardTest(unittest.TestCase):
    """AUD-SEC-498 (D-377): nạp `xt` trong tiến trình (`python3 -c 'import xt; xt.main([...])'`, `runpy`, `import_module`,
    `exec`, `-m runpy xt`) — guard không thấy lệnh con nên chặn; dùng thư viện đọc (`xt.parse_plan`) và lệnh CLI rõ vẫn
    qua."""

    DENY = (
        "python3 -c \"import os,sys; os.environ.pop('CLAUDECODE',None); sys.path.insert(0,'scripts'); import xt;"
        " xt.main(['stage','approve','--sha','abc'])\"",
        'python3 -c \'import sys; sys.path.insert(0,"scripts"); from xt import main; main(["stage","approve"])\'',
        "python3 -c \"import sys; sys.path.insert(0,'scripts'); from xt import *; main(sys.argv[1:])\" x y",
        "python3 -c \"import sys; sys.path.insert(0,'scripts'); import xt as t; getattr(t, 'ma'+'in')(['loop'])\"",
        'python3 -c "import scripts.xt as t; t.cmd_stage(None)"',
        "python3 -c \"from scripts import xt; xt.main(['stage','approve'])\"",
        "python3 -c \"import sys; sys.path.insert(0,'scripts'); import xt; xt.parse_plan('x'); print('init --adopt')\"",
        "python3 -c \"import runpy,sys; sys.argv=['xt','stage','approve']; runpy.run_path('scripts/xt.py',"
        " run_name='__main__')\"",
        "P=scripts/xt.py; python3 -c \"import runpy,os; runpy.run_path(os.environ['P'])\"",
        "python3 -c \"import runpy; runpy.run_path('scr'+'ipts/x'+'t.py')\"",
        "python3 -c \"import runpy; runpy.run_path('$P')\"",
        "python3 -c \"import sys; sys.path.insert(0,'scripts'); import runpy; runpy.run_module('xt',"
        " run_name='__main__')\" stage approve",
        "python3 -c \"import importlib,sys; sys.path.insert(0,'scripts');"
        " importlib.import_module('xt').main(['stage','approve'])\"",
        "python3 -c \"__import__('xt').main(['stage','approve'])\"",
        "python3 -c \"exec(open('scripts/xt.py').read())\"",
        "python3 -c \"exec('import xt; xt.main([1])')\"",
        "python3 -c \"import importlib.util as u; s=u.spec_from_file_location('m','scripts/xt.py')\"",
        "python3 - <<'PY'\nimport sys; sys.path.insert(0, 'scripts'); import xt; xt.main(['stage', 'approve'])\nPY",
        "python3 <<< \"import xt; xt.main(['stage','approve'])\"",
        "echo \"import xt; xt.main(['loop'])\" | python3",
        "python3 -c 'import xt; xt.main([' 2>/dev/null",  # không phải Python hợp lệ: luật chữ
        "PYTHONPATH=scripts python3 -m runpy xt stage approve",
        "PYTHONPATH=scripts python3 -mrunpy scripts.xt stage approve",
        'python3 -m runpy "$M" stage approve',
        "bash -c \"python3 -c 'import xt; xt.main([1])'\"",
        "uv run python -c \"import xt; xt.main(['stage','approve'])\"",
    )
    ALLOW = (
        "python3 scripts/xt.py loop status",
        "python3 -c 'print(1)'",
        "python3 -c \"import json,sys; d=json.load(sys.stdin); print([c for c in d if 'xt-review v1' in c])\"",
        "python3 -c \"import importlib.metadata as m; print(m.version('pip'))\"",
        "python3 -c \"print(eval('1+2'))\"",
        "python3 -m unittest -q tests.test_xt",
        "python3 -m runpy json.tool f.json",
        # Kiểm PM-PLAN-001 (BLUEPRINT.md) và Gate dùng thư viện đọc của xt
        "python3 -c \"import sys;sys.path.insert(0,'scripts');import xt,pathlib;t=xt.parse_plan(pathlib.Path('PLAN.md'));"
        "assert t and all(x['gate'] for x in t)\"",
        "python3 -c \"import sys; sys.path.insert(0,'scripts'); import xt; from pathlib import Path;"
        " d,s=xt.review_debt(Path('.'),Path('docs/ops/AUDIT-STATUS.md')); print(*d,sep=chr(10));"
        ' sys.exit(1 if d or not s else 0)"',
        'python3 -c "import xt_helpers; xt_helpers.run()"',
        "node -e \"const xt = require('./xt'); console.log(1)\"",
    )

    def setUp(self):
        self.enterContext(unittest.mock.patch.dict(os.environ, {"XT_GUARD_POLICY": "", "XT_GUARD_PHASE": ""}))

    def decide(self, cmd):
        return dict(guard.apply_policy(guard.bash_decision(cmd, str(ROOT), str(ROOT))))

    def test_in_process_xt_denied(self):
        for cmd in self.DENY:
            with self.subTest(cmd=cmd):
                out = self.decide(cmd)
                self.assertEqual((out.get("decision"), out.get("code")), ("deny", "STAGE_APPROVE"))
                self.assertIn("AUD-SEC-498", str(out.get("reason")))

    def test_cli_and_library_reads_pass(self):
        for cmd in self.ALLOW:
            with self.subTest(cmd=cmd):
                self.assertNotEqual(self.decide(cmd).get("decision"), "deny")

    def test_python_scan_helpers(self):
        self.assertFalse(guard._xt_inproc_python("x = (", 0))  # không phải Python: luật chữ, không nạp xt
        self.assertTrue(guard._xt_inproc_python("exec('exec(\"exec(1)\")')", guard.XT_INPROC_DEPTH))  # quá sâu: chặt
        self.assertTrue(guard._xt_inproc_text("import runpy as r"))
        self.assertFalse(guard._xt_inproc_argv([]))
        self.assertFalse(guard._xt_inproc_argv(["python3", "-m", "runpy"]))


if __name__ == "__main__":
    unittest.main()
