"""Test cho giai đoạn sản phẩm (ADR-0058): sổ `docs/autopilot/STAGE.json`, lệnh `xt.py stage`, khoá ở `loop` và hàng
`stage` của `release-check`. Repo git tạm thật (bản trình duyệt gắn SHA của HEAD)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
import unittest.mock
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import xt
from test_xt_cli import TmpRepoCase, run_main

HUMAN = {k: "" for k in xt.STAGE_AGENT_ENV}  # ngoài phiên agent
SHA = "a" * 40


def ledger(**over):
    led = {"schema": 1, "cycle": "C-001", "stage": 1, "status": "active", "submitted": None}
    led["history"] = [{"event": "init", "cycle": "C-001", "stage": 1}]
    led.update(over)
    return led


class StageProblemTest(unittest.TestCase):
    def test_valid_and_shape_errors(self):
        self.assertEqual(xt.stage_problem(ledger()), "")
        cases = [
            ([], "schema"),
            (ledger(schema=2), "schema"),
            (ledger(cycle="X"), "C-NNN"),
            (ledger(stage=4), "`stage` phải"),
            (ledger(status="locked"), "`stage` phải"),
            (ledger(status="completed"), "chỉ có ở giai đoạn 3"),
            (ledger(status="awaiting_approval"), "submitted.sha"),
            (ledger(submitted={"sha": SHA}), "submitted.sha"),
            (ledger(history=[]), "thiếu `history`"),
            (ledger(history="x"), "thiếu `history`"),
        ]
        for led, why in cases:
            with self.subTest(why=why):
                self.assertIn(why, xt.stage_problem(led))

    def test_history_must_rebuild_current_stage(self):
        jump = ledger(stage=3)  # sửa tay 1 → 3 không có `approve`
        self.assertIn("lịch sử dựng ra giai đoạn 1, sổ ghi 3/active", xt.stage_problem(jump))
        ok = ledger(stage=2)
        ok["history"].append({"event": "approve", "cycle": "C-001", "stage": 1, "sha": SHA, "by": "p@x"})
        self.assertEqual(xt.stage_problem(ok), "")
        bad = [
            ("x", "không phải object"),
            ({"event": "init", "cycle": "C-1", "stage": 1}, "không phải object"),
            ({"event": "init", "cycle": "C-001", "stage": 1}, "`init` sai"),  # chu kỳ mở hai lần
            ({"event": "adopt", "cycle": "C-002", "stage": "2"}, "`adopt` sai"),
            ({"event": "init", "cycle": "C-002", "stage": 2}, "`init` sai"),
            ({"event": "submit", "cycle": "C-001", "stage": 3}, "giai đoạn mở là 1"),
            ({"event": "approve", "cycle": "C-001", "stage": 1, "sha": "abc", "by": "p"}, "thiếu `sha`"),
            ({"event": "approve", "cycle": "C-001", "stage": 1, "sha": SHA}, "thiếu `sha`"),
            ({"event": "skip", "cycle": "C-001", "stage": 1}, "sự kiện lạ"),
        ]
        for ev, why in bad:
            with self.subTest(ev=ev):
                led = ledger()
                led["history"].append(ev)
                self.assertIn(why, xt.stage_problem(led))

    def test_adopt_and_completed(self):
        led = ledger(stage=3, status="completed", history=[{"event": "adopt", "cycle": "C-001", "stage": 3}])
        led["history"].append({"event": "approve", "cycle": "C-001", "stage": 3, "sha": SHA, "by": "p"})
        self.assertEqual(xt.stage_problem(led), "")

    def test_plan_stage_marker(self):
        self.assertEqual(xt.plan_stage("# P\n> Giai đoạn sản phẩm: 2 (C-004) · khác\n"), (2, "C-004"))
        self.assertIsNone(xt.plan_stage("> Giai đoạn: G4 → G6\n"))

    def test_agent_session(self):
        with unittest.mock.patch.dict(os.environ, HUMAN):
            self.assertFalse(xt.agent_session())
        with unittest.mock.patch.dict(os.environ, {**HUMAN, "CLAUDECODE": "1"}):
            self.assertTrue(xt.agent_session())


class StageCliTest(TmpRepoCase):
    def setUp(self):
        super().setUp()
        self.init_repo()
        self.git("config", "user.email", "chu@example.invalid")
        self.enterContext(unittest.mock.patch.dict(os.environ, {**HUMAN, "CLAUDE_PROJECT_DIR": str(self.repo)}))
        self.commit("khởi tạo")

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

    def submit(self):
        sha = self.commit(f"bản {len(self.led()['history'])}")
        rc, _, err = self.stage("submit", "--evidence", "chạy `make demo`", agent=True)
        self.assertEqual(rc, 0, err)
        return sha

    def test_full_cycle_one_two_three_then_new_cycle(self):
        self.assertIn("Chưa dùng", self.stage("status")[1])
        self.assertEqual(self.stage("init", agent=True)[0], 0)
        rc, _, err = self.stage("init")
        self.assertEqual(rc, 2)
        self.assertIn("đã có (C-001, giai đoạn 1)", err)
        self.assertIn("giai đoạn 2–3 khoá", self.stage("status")[1])
        for n in (1, 2, 3):
            with self.subTest(stage=n):
                sha = self.submit()
                out = self.stage("status")[1]
                self.assertIn(f"giai đoạn {n} ", out)
                self.assertIn(f"chờ người duyệt bản {sha[:12]}", out)
                rc, _, err = self.stage("approve", "--sha", sha, "--note", "ok", agent=True)
                self.assertEqual(rc, 2)
                self.assertIn("chỉ người duyệt", err)
                rc, out, err = self.stage("approve", "--sha", sha[:7], "--note", "ok")
                self.assertEqual(rc, 0, err)
        led = self.led()
        self.assertEqual((led["stage"], led["status"]), (3, "completed"))
        self.assertEqual([e["by"] for e in led["history"] if e["event"] == "approve"], ["chu@example.invalid"] * 3)
        self.assertIn("completed", self.stage("status")[1])
        self.assertEqual(self.stage("new-cycle", "--reason", "module lớn", agent=True)[0], 0)
        self.assertEqual((self.led()["cycle"], self.led()["stage"], self.led()["status"]), ("C-002", 1, "active"))
        rc, out, _ = self.stage("status", "--json")
        self.assertEqual(json.loads(out)["stage"]["cycle"], "C-002")

    def test_refusals_leave_ledger_untouched(self):
        rc, _, err = self.stage("submit", "--evidence", "x")
        self.assertIn("chỉ trình duyệt khi giai đoạn đang `active`", err)
        self.stage("init")
        before = self.led()
        (self.repo / "dở.txt").write_text("x", encoding="utf-8")
        self.assertIn("chưa commit", self.stage("submit", "--evidence", "x")[2])
        (self.repo / "dở.txt").unlink()
        self.assertIn("chỉ mở lại giai đoạn đang chờ duyệt", self.stage("reopen", "--reason", "x")[2])
        self.assertIn("không có giai đoạn chờ duyệt", self.stage("approve", "--sha", "abcdef1", "--note", "x")[2])
        self.assertIn("chỉ mở sau khi chu kỳ", self.stage("new-cycle", "--reason", "x")[2])
        self.assertEqual(self.led(), before)
        sha = self.submit()
        for bad in ("abc", "0" * 7):
            with self.subTest(sha=bad):
                self.assertIn("không phải bản đã trình", self.stage("approve", "--sha", bad, "--note", "x")[2])
        self.assertIn("chỉ trình duyệt", self.stage("submit", "--evidence", "x")[2])  # đã chờ duyệt
        self.assertEqual(self.stage("reopen", "--reason", "chủ dự án muốn sửa form", agent=True)[0], 0)
        led = self.led()
        self.assertEqual((led["stage"], led["status"], led["submitted"]), (1, "active", None))
        self.assertEqual([e["event"] for e in led["history"]], ["init", "submit", "reopen"])
        self.assertNotEqual(sha, "")

    def test_adopt_needs_human_and_evidence(self):
        self.assertIn("cần `--evidence`", self.stage("init", "--adopt", "2")[2])
        self.assertIn("chỉ người duyệt", self.stage("init", "--adopt", "2", "--evidence", "v1.0", agent=True)[2])
        self.assertEqual(self.stage("init", "--adopt", "2", "--evidence", "tag v1.0 + GO-NO-GO")[0], 0)
        led = self.led()
        self.assertEqual(
            (led["stage"], led["history"][0]["event"], led["history"][0]["by"]), (2, "adopt", "chu@example.invalid")
        )

    def test_corrupt_ledger_blocks(self):
        p = self.repo / xt.STAGE_LEDGER
        p.parent.mkdir(parents=True)
        p.write_text("{", encoding="utf-8")
        self.assertIn("không đọc được", self.stage("status")[2])
        p.write_text(json.dumps(ledger(stage=3)), encoding="utf-8")
        rc, _, err = self.stage("status")
        self.assertEqual(rc, 2)
        self.assertIn("hỏng: lịch sử dựng ra", err)

    def test_no_commit_and_unknown_approver(self):
        self.stage("init")
        with unittest.mock.patch.object(xt, "_git_head", return_value=None):
            self.assertIn("không có commit", self.stage("submit", "--evidence", "x")[2])
        sha = self.submit()
        empty = subprocess.CompletedProcess([], 0, "", "")
        with unittest.mock.patch.object(xt.subprocess, "run", side_effect=[OSError("x"), empty]):
            self.assertIn("không biết người duyệt", self.stage("approve", "--sha", sha, "--note", "x")[2])

    def test_update_refuses_invalid_result(self):
        with self.assertRaises(xt.StageError):
            xt.update_stage(self.repo, lambda led: {"schema": 1})
        self.assertFalse((self.repo / xt.STAGE_LEDGER).exists())

    def test_unknown_subcommand_is_read_only(self):
        args = unittest.mock.Mock(stage_cmd="khác")
        self.assertIsNone(xt._stage_dispatch(args, self.repo))


class StageLockTest(TmpRepoCase):
    """Giai đoạn sau khoá ở mọi lối vào vòng (`loop init/next/record`) và ở `release-check`."""

    PLAN = "docs/autopilot/PLAN.md"

    def setUp(self):
        super().setUp()
        self.init_repo()
        self.git("config", "user.email", "chu@example.invalid")
        self.enterContext(unittest.mock.patch.dict(os.environ, {**HUMAN, "CLAUDE_PROJECT_DIR": str(self.repo)}))
        self.enterContext(unittest.mock.patch.object(xt, "loop_root", lambda base: base))

    def plan(self, marker):
        p = self.repo / self.PLAN
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f"# PLAN\n{marker}\n\n- [ ] `T-001` việc — Gate: `true`\n", encoding="utf-8")

    def write_ledger(self, led):
        p = self.repo / xt.STAGE_LEDGER
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(led), encoding="utf-8")

    def test_plan_problem_cases(self):
        self.plan("")
        self.assertEqual(xt.stage_plan_problem(self.repo, self.PLAN), "")  # không dùng sổ
        self.write_ledger(ledger())
        self.assertIn(
            "chưa khai giai đoạn — thêm dòng `Giai đoạn sản phẩm: 1 (C-001)`",
            xt.stage_plan_problem(self.repo, self.PLAN),
        )
        self.plan("> Giai đoạn sản phẩm: 2 (C-001)")
        self.assertIn("khai giai đoạn 2 (C-001) nhưng đang mở giai đoạn 1", xt.stage_plan_problem(self.repo, self.PLAN))
        self.plan("> Giai đoạn sản phẩm: 1 (C-001)")
        self.assertEqual(xt.stage_plan_problem(self.repo, self.PLAN), "")
        self.assertIn("không đọc được", xt.stage_plan_problem(self.repo, "thiếu.md"))
        self.write_ledger({"schema": 9})
        self.assertIn("hỏng", xt.stage_plan_problem(self.repo, self.PLAN))
        done = ledger(stage=3, status="completed", history=[{"event": "adopt", "cycle": "C-001", "stage": 3}])
        done["history"].append({"event": "approve", "cycle": "C-001", "stage": 3, "sha": SHA, "by": "p"})
        self.write_ledger(done)
        self.assertIn("stage new-cycle", xt.stage_plan_problem(self.repo, self.PLAN))

    def test_loop_entry_points_refuse_locked_stage(self):
        self.write_ledger(ledger())
        self.plan("> Giai đoạn sản phẩm: 2 (C-001)")
        rc, _, err = run_main("loop", "init", "--plan", self.PLAN)
        self.assertEqual(rc, 2)
        self.assertIn("giai đoạn sau khoá", err)
        self.assertIsNone(xt.read_state(self.repo))
        self.plan("> Giai đoạn sản phẩm: 1 (C-001)")
        self.assertEqual(run_main("loop", "init", "--plan", self.PLAN)[0], 0)
        self.assertEqual(run_main("loop", "next")[0], 0)
        self.plan("> Giai đoạn sản phẩm: 2 (C-001)")  # sửa PLAN sau init
        rc, _, err = run_main("loop", "next")
        self.assertEqual(rc, 2)
        self.assertIn("đang mở giai đoạn 1", err)
        rc, _, err = run_main("loop", "record", "--task", "T-001", "--", "true")
        self.assertEqual(rc, 2)
        self.assertIn("đang mở giai đoạn 1", err)
        self.assertFalse((self.repo / ".autopilot" / "evidence" / "T-001.json").exists())

    def test_release_row(self):
        row = xt._release_stage(self.repo)
        self.assertEqual((row["result"], row["level"]), ("N/A", "SHOULD"))
        self.write_ledger(ledger())
        row = xt._release_stage(self.repo)
        self.assertEqual(row["result"], "FAIL")
        self.assertIn("MVP chưa mở Production", row["evidence"])
        two = ledger(stage=2)
        two["history"].append({"event": "approve", "cycle": "C-001", "stage": 1, "sha": SHA, "by": "p"})
        self.write_ledger(two)
        self.assertEqual(xt._release_stage(self.repo)["result"], "PASS")
        self.write_ledger({})
        self.assertEqual(xt._release_stage(self.repo)["result"], "FAIL")


def _load_guard():
    sys.path.insert(0, str(ROOT / ".claude" / "hooks"))
    import guard as g

    return g


class StageGuardTest(unittest.TestCase):
    """Guard (lớp chặn nhầm, D-015): agent không duyệt giai đoạn, không ghi tay sổ (ADR-0058)."""

    def setUp(self):
        self.g = _load_guard()
        env = {"CLAUDE_PROJECT_DIR": str(ROOT), "XT_GUARD_POLICY": ""}
        self.enterContext(unittest.mock.patch.dict(os.environ, env))

    def decide(self, cmd):
        return dict(self.g.apply_policy(self.g.bash_decision(cmd, str(ROOT), None))).get("decision")

    def test_approve_and_adopt_denied(self):
        for cmd in (
            "python3 scripts/xt.py stage approve --sha abc1234 --note ok",
            "env A=1 python3 .xtemplates/scripts/xt.py stage init --adopt 2 --evidence v1",
            "cd . && python3 /x/xt.py stage init --adopt=3 --evidence v",
        ):
            with self.subTest(cmd=cmd):
                self.assertEqual(self.decide(cmd), "deny")

    def test_agent_steps_and_reads_allowed(self):
        for cmd in (
            "python3 scripts/xt.py stage status",
            "python3 scripts/xt.py stage submit --evidence demo",
            "python3 scripts/xt.py stage init",
            "python3 scripts/xt.py loop status",
            "grep approve scripts/xt.py",
            "cat docs/autopilot/STAGE.json",
        ):
            with self.subTest(cmd=cmd):
                self.assertNotEqual(self.decide(cmd), "deny")

    def test_handwrite_ledger_denied(self):
        self.assertEqual(self.g.classify_path(xt.STAGE_LEDGER), "evidence")
        self.assertEqual(self.g.STAGE_LEDGER, xt.STAGE_LEDGER)
        self.assertEqual(self.decide("sed -i s/1/3/ docs/autopilot/STAGE.json"), "deny")
        action, why = self.g.edit_decision(str(ROOT / xt.STAGE_LEDGER), str(ROOT))
        self.assertEqual(action, "ask")
        self.assertIn("xt.py stage", why)


if __name__ == "__main__":
    unittest.main()
