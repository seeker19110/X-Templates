"""Test vòng tự trị (`xt.py loop …`) gắn với ngữ cảnh chạy: git worktree (T-2521) và phiên Claude Code (T-2522).

Gọi `xt.main([...])` trong tiến trình; worktree là `git worktree add` thật trong repo tạm, payload Stop hook là JSON giả.
"""

from __future__ import annotations

import contextlib
import errno
import io
import json
import os
import subprocess
import sys
import threading
import unittest
import unittest.mock
from contextlib import chdir
from pathlib import Path
from typing import Iterator

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import xt
from test_xt_cli import TmpRepoCase, run_main

PLAN = "- [ ] `T-001` in thư mục chạy Gate — Gate: `pwd`\n- [ ] `T-002` việc sau — Gate: `true`\n"
SESSION = "11111111-aaaa-bbbb-cccc-000000000001"
OTHER = "22222222-aaaa-bbbb-cccc-000000000002"


class LoopWorktreeRootTest(TmpRepoCase):
    """T-2521: `loop` gõ tay trong một worktree của cùng repo làm việc trên worktree đó, không trên cây chính."""

    def setUp(self) -> None:
        super().setUp()
        main = self.init_repo()
        (main / "docs" / "autopilot").mkdir(parents=True)
        (main / "docs" / "autopilot" / "PLAN.md").write_text(PLAN, encoding="utf-8")
        (main / ".gitignore").write_text(".autopilot/\n", encoding="utf-8")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "init")
        self.wt = self.tmp / "wt-lat"
        self.git("worktree", "add", "-q", "-b", "lat", str(self.wt))
        self.main = main
        self.enterContext(unittest.mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(main)}))
        os.environ.pop("CLAUDE_CODE_SESSION_ID", None)

    def plan_line(self, tree: Path) -> str:
        return (tree / "docs" / "autopilot" / "PLAN.md").read_text(encoding="utf-8").splitlines()[0]

    def test_loop_worktree_root_record_runs_gate_and_ticks_in_worktree(self) -> None:
        with chdir(self.wt / "docs"):  # thư mục con của worktree vẫn quy về gốc worktree
            self.assertEqual(run_main("loop", "init")[0], 0)
            rc, out, _ = run_main("loop", "record", "--task", "T-001", "--", "pwd")
        self.assertEqual(rc, 0, out)
        ev = json.loads((self.wt / ".autopilot" / "evidence" / "T-001.json").read_text(encoding="utf-8"))
        self.assertEqual(Path(ev["output_tail"]).resolve(), self.wt.resolve())  # Gate chạy ở worktree
        self.assertTrue(self.plan_line(self.wt).startswith("- [x] `T-001`"))  # tick PLAN của worktree
        self.assertTrue(self.plan_line(self.main).startswith("- [ ] `T-001`"))  # cây chính không đổi
        self.assertFalse((self.main / ".autopilot").exists())  # sổ của cây chính không bị ghi

    def test_loop_worktree_root_init_warns_hook_root(self) -> None:
        # Stop hook đọc `.autopilot/` của CLAUDE_PROJECT_DIR (cây chính) → init trong worktree phải nói rõ, không chặn.
        with chdir(self.wt):
            rc, _, err = run_main("loop", "init")
        self.assertEqual(rc, 0)
        self.assertIn(f"Stop hook đọc {self.main.resolve()}", err)
        self.assertIn("mở phiên Claude với thư mục dự án là worktree này", err)
        with unittest.mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(self.wt)}), chdir(self.wt):
            rc, _, err = run_main("loop", "init", "--force")  # phiên mở đúng worktree: không cảnh báo
        self.assertEqual(rc, 0)
        self.assertNotIn("Stop hook đọc", err)
        with chdir(self.main):
            self.assertNotIn("Stop hook đọc", run_main("loop", "init")[2])

    def test_loop_worktree_root_status_and_verify_use_worktree(self) -> None:
        with chdir(self.wt):
            run_main("loop", "init")
            run_main("loop", "record", "--task", "T-001", "--", "pwd")
            status = run_main("loop", "status")[1]
            with unittest.mock.patch.object(xt, "loop_verify", return_value=0) as verify:
                self.assertEqual(run_main("loop", "verify")[0], 0)
        self.assertTrue(status.startswith("verdict: continue — làm task T-002"), status)
        self.assertEqual(verify.call_args.args[0], self.wt.resolve())
        with chdir(self.main):  # cây chính: chưa có vòng nào
            self.assertIn("chưa", run_main("loop", "status")[1].lower())

    def test_loop_worktree_root_hook_commands_keep_project_dir(self) -> None:
        # Hook (Stop/PreCompact) do Claude Code gọi theo CLAUDE_PROJECT_DIR — không đổi gốc theo cwd.
        with chdir(self.wt), unittest.mock.patch.object(xt, "hook_stop", return_value=("", 0)) as hs:
            run_main("loop", "hook-stop", stdin="{}")
        self.assertEqual(hs.call_args.args[1], self.main.resolve())

    def test_loop_worktree_root_falls_back_outside_same_repo_worktree(self) -> None:
        other = self.tmp / "other"
        other.mkdir()
        subprocess.run(["git", "init", "-q", str(other)], check=True)
        plain = self.tmp / "plain"
        plain.mkdir()
        base = self.main.resolve()
        cases = {
            "cây chính (thư mục con)": self.main / "docs",
            "repo git khác": other,
            "không phải repo git": plain,
        }
        for name, cwd in cases.items():
            with self.subTest(name), chdir(cwd):
                self.assertEqual(xt.loop_root(base), base)
        with chdir(self.wt):
            self.assertEqual(xt.loop_root(base), self.wt.resolve())
            self.assertEqual(xt.loop_root(plain), plain)  # gốc dự án không phải repo git → giữ như cũ
        gone = self.tmp / "gone"
        gone.mkdir()
        with chdir(gone):
            gone.rmdir()  # cwd đã bị xoá: không ném lỗi, giữ gốc cũ
            self.assertEqual(xt.loop_root(base), base)

    def test_loop_worktree_root_ignores_git_env_redirect(self) -> None:
        # GIT_DIR đặt sẵn không được lái phép so `--git-common-dir` sang repo khác.
        other = self.tmp / "other"
        subprocess.run(["git", "init", "-q", str(other)], check=True)
        with chdir(self.wt), unittest.mock.patch.dict(os.environ, {"GIT_DIR": str(other / ".git")}):
            self.assertEqual(xt.loop_root(self.main.resolve()), self.wt.resolve())


class StopHookSessionBoundTest(TmpRepoCase):
    """T-2522: Stop hook chỉ áp vòng cho đúng phiên đã `loop init`/`loop resume`."""

    def setUp(self) -> None:
        super().setUp()
        (self.tmp / "docs" / "autopilot").mkdir(parents=True)
        (self.tmp / "docs" / "autopilot" / "PLAN.md").write_text(PLAN, encoding="utf-8")
        self.enterContext(
            unittest.mock.patch.dict(
                os.environ, {"CLAUDE_PROJECT_DIR": str(self.tmp), "CLAUDE_CODE_SESSION_ID": SESSION}
            )
        )

    def stop(self, payload: str) -> tuple[str, int]:
        rc, out, _ = run_main("loop", "hook-stop", stdin=payload)
        return out, rc

    def log_lines(self) -> list[str]:
        p = self.tmp / ".autopilot" / xt.STOP_LOG_FILE
        return p.read_text(encoding="utf-8").splitlines() if p.exists() else []

    def test_stop_hook_session_bound_init_records_session(self) -> None:
        run_main("loop", "init")
        self.assertEqual(xt.read_state(self.tmp)["session_id"], SESSION)
        with unittest.mock.patch.dict(os.environ, {"CLAUDE_CODE_SESSION_ID": "  "}):
            run_main("loop", "init", "--force")
        self.assertEqual(xt.read_state(self.tmp)["session_id"], "")  # ngoài Claude Code: vòng chưa gắn phiên

    def test_stop_hook_session_bound_same_session_blocks(self) -> None:
        run_main("loop", "init")
        for payload in (json.dumps({"session_id": SESSION}), "{}", "", json.dumps({"session_id": 7})):
            with self.subTest(payload):
                out, rc = self.stop(payload)
                self.assertEqual((rc, json.loads(out)["decision"]), (0, "block"))
        self.assertEqual(xt.read_state(self.tmp)["iterations"], 4)
        self.assertEqual(self.log_lines(), [])

    def test_stop_hook_session_bound_other_session_passes_without_iteration(self) -> None:
        run_main("loop", "init")
        out, rc = self.stop(json.dumps({"session_id": OTHER, "permission_mode": "default"}))
        st = xt.read_state(self.tmp)
        self.assertEqual((out, rc, st["iterations"], st["active"]), ("", 0, 0, True))
        self.assertNotIn("permission_mode", st)  # chế độ quyền của phiên khác không ghi vào vòng
        lines = self.log_lines()
        self.assertEqual(len(lines), 1)
        self.assertIn("22222222", lines[0])
        self.assertIn("11111111", lines[0])

    def test_stop_hook_session_bound_garbage_stdin_passes(self) -> None:
        run_main("loop", "init")
        for payload in ("rác {", "[1]", '"chuỗi"'):
            with self.subTest(payload):
                self.assertEqual(self.stop(payload), ("", 0))
        st = xt.read_state(self.tmp)
        self.assertEqual((st["iterations"], st["active"]), (0, True))
        self.assertEqual(len(self.log_lines()), 3)

    def test_stop_hook_session_bound_unbound_loop_keeps_old_behaviour(self) -> None:
        run_main("loop", "init")
        st = xt.read_state(self.tmp)
        del st["session_id"]  # state của bản cũ: chưa có khoá session_id
        xt.write_state(st, self.tmp)
        out, _ = self.stop(json.dumps({"session_id": OTHER}))
        self.assertEqual(json.loads(out)["decision"], "block")
        self.assertEqual(xt.read_state(self.tmp)["iterations"], 1)

    def test_stop_hook_session_bound_inactive_loop_no_log(self) -> None:
        run_main("loop", "init")
        run_main("loop", "stop", "--reason", "xong")
        self.assertEqual(self.stop(json.dumps({"session_id": OTHER})), ("", 0))
        self.assertEqual(self.log_lines(), [])  # vòng đã tắt: phiên khác dừng bình thường, không ghi log mỗi lượt

    def test_stop_hook_session_bound_log_write_error_is_fail_open(self) -> None:
        run_main("loop", "init")
        (self.tmp / ".autopilot" / xt.STOP_LOG_FILE).mkdir()  # không ghi nối được
        self.assertEqual(self.stop(json.dumps({"session_id": OTHER})), ("", 0))

    def test_stop_hook_session_bound_resume_rebinds_current_session(self) -> None:
        run_main("loop", "init")
        with unittest.mock.patch.dict(os.environ, {"CLAUDE_CODE_SESSION_ID": OTHER}):
            run_main("loop", "resume", "--reason", "phiên mới")
        self.assertEqual(xt.read_state(self.tmp)["session_id"], OTHER)
        out, _ = self.stop(json.dumps({"session_id": OTHER}))
        self.assertEqual(json.loads(out)["decision"], "block")
        with unittest.mock.patch.dict(os.environ, {"CLAUDE_CODE_SESSION_ID": ""}):
            run_main("loop", "resume", "--reason", "chạy tay ngoài phiên")
        self.assertEqual(xt.read_state(self.tmp)["session_id"], "")  # không có phiên → vòng chưa gắn (hành vi cũ)
        out, _ = self.stop(json.dumps({"session_id": SESSION}))
        self.assertEqual(json.loads(out)["decision"], "block")

    def test_stop_hook_session_bound_status_warns_on_mismatch(self) -> None:
        # /clear đổi CLAUDE_CODE_SESSION_ID: `loop status` (SessionStart in lại) nhắc `loop resume`.
        run_main("loop", "init")
        warn = "vòng gắn phiên khác — nếu đây là phiên tiếp tục (sau /clear) chạy `xt.py loop resume`"
        cases = {SESSION: False, OTHER: True, "": False}  # chưa biết phiên hiện tại → không đoán
        for sid, mismatch in cases.items():
            with self.subTest(sid=sid), unittest.mock.patch.dict(os.environ, {"CLAUDE_CODE_SESSION_ID": sid}):
                self.assertEqual(warn in run_main("loop", "status")[1], mismatch)
                self.assertEqual(json.loads(run_main("loop", "status", "--json")[1])["session_mismatch"], mismatch)
        run_main("loop", "stop", "--reason", "xong")
        with unittest.mock.patch.dict(os.environ, {"CLAUDE_CODE_SESSION_ID": OTHER}):  # vòng đã tắt: không cảnh báo
            self.assertFalse(json.loads(run_main("loop", "status", "--json")[1])["session_mismatch"])
        st = xt.read_state(self.tmp)
        st["session_id"] = ""
        st["active"] = True
        xt.write_state(st, self.tmp)
        with unittest.mock.patch.dict(os.environ, {"CLAUDE_CODE_SESSION_ID": OTHER}):  # vòng chưa gắn phiên
            self.assertNotIn(warn, run_main("loop", "status")[1])


class LoopInitCarryTest(TmpRepoCase):
    """T-2611 (phản hồi dự án đích): `loop init` sau vòng đã dừng mất danh sách chờ người và đòi chạy lại Gate cũ;
    máy mới (`.autopilot/` không theo git) đòi chạy lại mọi task `[x]` mà không nói vì sao."""

    def setUp(self) -> None:
        super().setUp()
        self.init_repo()
        self.plan = self.repo / "docs" / "autopilot" / "PLAN.md"
        self.plan.parent.mkdir(parents=True)
        self.plan.write_text(
            "- [ ] `T-001` a (files: a.txt) — Gate: `true`\n- [ ] `T-002` cần người — Gate: `true`\n"
            "- [ ] `T-003` c — Gate: `true`\n",
            encoding="utf-8",
        )
        (self.repo / "a.txt").write_text("1\n", encoding="utf-8")
        self.enterContext(unittest.mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(self.repo)}))
        os.environ.pop("CLAUDE_CODE_SESSION_ID", None)
        self.enterContext(chdir(self.repo))

    def test_loop_init_carry_keeps_deferred_and_green_evidence(self) -> None:
        run_main("loop", "init")
        self.assertEqual(run_main("loop", "record", "--task", "T-001", "--", "true")[0], 0)
        self.assertEqual(run_main("loop", "defer", "--task", "T-002", "--reason", "chủ repo ký")[0], 0)
        run_main("loop", "stop", "--reason", "hết ngày")
        rc, _, err = run_main("loop", "init")
        self.assertEqual(rc, 0)
        self.assertIn("giữ 1 việc chờ người: T-002", err)
        self.assertIn("mang 1 bằng chứng xanh: T-001", err)
        st = json.loads((self.repo / ".autopilot" / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(list(st["deferred"]), ["T-002"])
        self.assertTrue(run_main("loop", "status")[1].startswith("verdict: continue — làm task T-003"))

    def test_loop_init_carry_keeps_deferred_across_plans(self) -> None:
        # D-177/ADR-0047: đợt kế dùng PLAN mới — việc chờ người còn mở cùng ID đi theo, bằng chứng xanh thì không; ID hết mở → báo bỏ.
        run_main("loop", "init")
        run_main("loop", "record", "--task", "T-001", "--", "true")
        run_main("loop", "defer", "--task", "T-002", "--reason", "chủ repo ký")
        run_main("loop", "defer", "--task", "T-003", "--reason", "khoá thật")
        run_main("loop", "stop", "--reason", "đợt 1 xong")
        self.plan.with_name("PLAN-2.md").write_text(
            "- [ ] `T-002` cần người — Gate: `true`\n- [ ] `T-004` d — Gate: `true`\n", encoding="utf-8"
        )
        rc, _, err = run_main("loop", "init", "--plan", "docs/autopilot/PLAN-2.md")
        self.assertEqual(rc, 0)
        self.assertIn("ℹ Vòng trước: giữ 1 việc chờ người: T-002", err)
        self.assertIn("⚠ 1 việc chờ người của vòng trước không còn mở trong PLAN/blueprint này (T-003) — bỏ", err)
        self.assertNotIn("bằng chứng xanh", err)
        st = json.loads((self.repo / ".autopilot" / "state.json").read_text(encoding="utf-8"))
        self.assertEqual((list(st["deferred"]), "carried" in st), (["T-002"], False))
        self.assertTrue(run_main("loop", "status")[1].startswith("verdict: continue — làm task T-004"))

    def test_loop_init_carry_drops_reused_id_with_other_spec(self) -> None:
        # Review #262 lượt 2: PLAN-<đợt> sinh từ mẫu bắt đầu lại ở T-001 — ID chờ người trùng nhưng việc khác là task mới,
        # không mang lý do cũ sang (trước: T-002 mới bị bỏ qua lặng lẽ, báo cáo cuối "chờ người" với lý do cũ).
        run_main("loop", "init")
        run_main("loop", "record", "--task", "T-001", "--", "true")
        run_main("loop", "defer", "--task", "T-002", "--reason", "chủ repo ký hợp đồng")
        run_main("loop", "stop", "--reason", "đợt 1 xong")
        self.plan.with_name("PLAN-2.md").write_text(
            "- [ ] `T-002` viết test tích hợp thanh toán — Gate: `true`\n- [ ] `T-003` d — Gate: `true`\n",
            encoding="utf-8",
        )
        rc, _, err = run_main("loop", "init", "--plan", "docs/autopilot/PLAN-2.md")
        self.assertEqual(rc, 0)
        self.assertIn("⚠ 1 ID chờ người của vòng trước nay là việc khác trong PLAN này (T-002) — không mang", err)
        self.assertNotIn("giữ 1 việc chờ người", err)
        self.assertNotIn("không còn mở", err)
        st = json.loads((self.repo / ".autopilot" / "state.json").read_text(encoding="utf-8"))
        self.assertNotIn("deferred", st)
        self.assertTrue(run_main("loop", "status")[1].startswith("verdict: continue — làm task T-002"))
        run_main("loop", "defer", "--task", "T-002", "--reason", "khoá thật")
        run_main("loop", "stop", "--reason", "x")
        self.plan.with_name(
            "PLAN-2.md"
        ).unlink()  # PLAN đợt trước không còn đọc được → không so spec, vẫn mang (fail-open)
        self.plan.with_name("PLAN-3.md").write_text("- [ ] `T-002` khác nữa — Gate: `true`\n", encoding="utf-8")
        self.assertIn("giữ 1 việc chờ người: T-002", run_main("loop", "init", "--plan", "docs/autopilot/PLAN-3.md")[2])

    def test_loop_init_after_done_needs_final_verify(self) -> None:
        # Review #262 lượt 2 (LOOP-DESIGN-022): đợt `done` chưa `loop verify --all` trên cây hiện tại không phải "xong" —
        # `loop init` đợt kế bị chặn như Stop hook, vì verify của đợt kế chỉ chạy Gate PLAN mới (Gate đợt trước đỏ sẽ lọt).
        self.plan.write_text("- [ ] `T-001` a (files: a.txt) — Gate: `test -f a.txt`\n", encoding="utf-8")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "plan")
        run_main("loop", "init")
        self.assertEqual(run_main("loop", "record", "--task", "T-001", "--", "test", "-f", "a.txt")[0], 0)
        (self.repo / "a.txt").unlink()  # Gate đợt 1 nay đỏ
        self.assertTrue(run_main("loop", "status")[1].startswith("verdict: done"))
        self.plan.with_name("PLAN-2.md").write_text("- [ ] `T-002` b — Gate: `true`\n", encoding="utf-8")
        rc, _, err = run_main("loop", "init", "--plan", "docs/autopilot/PLAN-2.md")
        self.assertEqual(rc, 2)
        self.assertIn("đợt `done` — mọi task có bằng chứng nhưng chưa kiểm lại cuối", err)
        self.assertIn("rồi `loop init` lại trên cùng cây (LOOP-HARNESS-024", err)
        self.assertNotIn("resume", err)  # lượt 3: `loop resume` xoá chờ người, `--force` bỏ kiểm cuối — không gợi
        self.assertNotIn("--force", err)
        self.assertEqual(run_main("loop", "verify", "--all")[0], 1)
        self.assertIn("kiểm lại cuối ĐỎ (T-001)", run_main("loop", "init", "--plan", "docs/autopilot/PLAN-2.md")[2])
        (self.repo / "a.txt").write_text("1\n", encoding="utf-8")
        self.assertEqual(run_main("loop", "verify", "--all")[0], 0)
        with self.plan.open(
            "a", encoding="utf-8"
        ) as f:  # cây đổi sau verify (PLAN/sổ audit viết sau) → verify lại (lượt 3)
            f.write("- [ ] `T-002` cần người — Gate: `true`\n")
        run_main("loop", "defer", "--task", "T-002", "--reason", "khoá thật")
        rc, _, err = run_main("loop", "init", "--plan", "docs/autopilot/PLAN-2.md")
        self.assertEqual((rc, "đợt `done-pending-human` — " in err), (2, True))
        self.assertEqual(run_main("loop", "verify", "--all")[0], 0)  # thứ tự tài liệu: PLAN + sổ → verify → init
        self.assertEqual(run_main("loop", "init", "--plan", "docs/autopilot/PLAN-2.md")[0], 0)
        self.assertNotIn("deferred", xt.read_state(self.repo))  # T-002 không có trong PLAN-2 → báo bỏ, không mang

    def test_loop_init_after_budget_needs_no_verify(self) -> None:
        # Hết ngân sách không phải "xong": `loop init` đợt kế không đòi kiểm lại cuối (nhánh `budget` của `_live_loop`).
        # Có commit để vân tay cây hoạt động: chưa `loop verify` nên `final_check` ≠ None nếu nhánh `budget` đòi kiểm cuối.
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "plan")
        run_main("loop", "init", "--max-iterations", "1")
        st = xt.read_state(self.repo)
        st["iterations"] = 1
        xt.write_state(st, self.repo)
        self.assertTrue(run_main("loop", "status")[1].startswith("verdict: budget"))
        self.plan.with_name("PLAN-2.md").write_text("- [ ] `T-009` b — Gate: `true`\n", encoding="utf-8")
        rc, _, err = run_main("loop", "init", "--plan", "docs/autopilot/PLAN-2.md")
        self.assertEqual((rc, "kiểm lại cuối" in err), (0, False))

    def test_live_loop_budget_blocked_and_exhausted(self) -> None:
        # T-3537 (ADR-0051, D-177): vòng còn sống vừa `blocked` vừa hết vòng/hạn → `_verdict_loop_state` xét `blocked` trước
        # trần nên `_live_loop` từng coi là vòng sống và trỏ ngược "mở block" — chu trình. Hết ngân sách thì `loop init` mở được.
        run_main("loop", "init", "--max-iterations", "1")
        self.assertEqual(run_main("loop", "defer", "--task", "T-002", "--reason", "khoá thật")[0], 0)
        self.assertEqual(run_main("loop", "block", "--reason", "chờ khoá")[0], 0)
        st = xt.read_state(self.repo)
        st["iterations"] = 1
        xt.write_state(st, self.repo)
        self.assertTrue(run_main("loop", "status")[1].startswith("verdict: blocked"))
        self.plan.with_name("PLAN-2.md").write_text(
            "- [ ] `T-002` cần người — Gate: `true`\n- [ ] `T-009` b — Gate: `true`\n", encoding="utf-8"
        )
        self.assertEqual(run_main("loop", "init", "--plan", "docs/autopilot/PLAN-2.md")[0], 0)
        self.assertIn("T-002", xt.read_state(self.repo).get("deferred", {}))  # ADR-0051: việc chờ người đi theo

    def test_live_loop_budget_blocked_by_deadline(self) -> None:
        # Cùng chu trình với hạn: `--hours 0` hết hạn ngay, `loop block` thêm cờ — `loop init` đợt kế không bị chặn.
        run_main("loop", "init", "--hours", "0")
        self.assertEqual(run_main("loop", "block", "--reason", "chờ khoá")[0], 0)
        self.plan.with_name("PLAN-2.md").write_text("- [ ] `T-009` b — Gate: `true`\n", encoding="utf-8")
        self.assertEqual(run_main("loop", "init", "--plan", "docs/autopilot/PLAN-2.md")[0], 0)

    def test_init_after_plan_renamed(self) -> None:
        # AUD-HAR-114: PLAN đợt trước đổi tên sau khi đợt xong → verdict `blocked` (không thấy PLAN) → `loop init` exit 2
        # "Đang có vòng" mà không nói vì sao. Nay thông báo nêu verdict + lý do và lối ra `loop stop`.
        run_main("loop", "init")
        for tid in ("T-001", "T-002", "T-003"):
            self.assertEqual(run_main("loop", "record", "--task", tid, "--", "true")[0], 0)
        self.plan.rename(self.plan.with_name("PLAN-1.md"))
        self.assertTrue(run_main("loop", "status")[1].startswith("verdict: blocked"))
        self.plan.with_name("PLAN-2.md").write_text("- [ ] `T-004` d — Gate: `true`\n", encoding="utf-8")
        rc, _, err = run_main("loop", "init", "--plan", "docs/autopilot/PLAN-2.md")
        self.assertEqual(rc, 2)
        self.assertIn("verdict `blocked`: không thấy PLAN", err)
        self.assertIn("`loop stop`", err)
        self.assertEqual(run_main("loop", "stop", "--reason", "đợt 1 xong")[0], 0)
        self.assertEqual(run_main("loop", "init", "--plan", "docs/autopilot/PLAN-2.md")[0], 0)

    def test_init_after_loop_block_points_to_resume(self) -> None:
        # Review #268: `blocked` do `loop block`/lỗi lặp chờ người xem rồi `loop resume` (loop-design.md) — không gợi `loop stop`.
        run_main("loop", "init")
        for reason in (
            "cần chủ repo ký",
            "PLAN không khớp SPEC",
        ):  # lối ra theo nguồn, không theo chữ lý do (#268 lượt 2)
            run_main("loop", "init", "--force")
            run_main("loop", "block", "--reason", reason)
            rc, _, err = run_main("loop", "init", "--plan", "docs/autopilot/PLAN.md")
            self.assertEqual(rc, 2)
            self.assertIn(f"verdict `blocked`: {reason} — người xem rồi `loop resume --reason`)", err)
            self.assertNotIn("`loop stop`", err)
            self.assertNotIn("`loop init --force`", err)  # không nối đuôi gợi lối ra trái nhau
        run_main("loop", "init", "--force")  # nguồn state thứ hai: lỗi lặp ≥ 3 (LOOP-DESIGN-005) — AUD-TEST-021
        for _ in range(3):
            run_main("loop", "record", "--task", "T-001", "--", "false")
        rc, _, err = run_main("loop", "init", "--plan", "docs/autopilot/PLAN.md")
        self.assertEqual(rc, 2)
        self.assertIn("cùng một lỗi lặp 3 lần (T-001)", err)
        self.assertIn("người xem rồi `loop resume --reason`)", err)
        self.assertNotIn("`loop stop`", err)

    def test_loop_init_carry_needs_same_spec_and_files(self) -> None:
        # Review #239: cùng đường dẫn PLAN nhưng spec task đổi, hoặc file trong `files:` đổi → không mang.
        for change in ("spec", "file"):
            with self.subTest(change=change):
                run_main("loop", "init", "--force")
                self.assertEqual(run_main("loop", "record", "--task", "T-001", "--", "true")[0], 0)
                run_main("loop", "stop", "--reason", "x")
                if change == "spec":
                    text = self.plan.read_text(encoding="utf-8").replace("`T-001` a ", "`T-001` việc khác hẳn ")
                    self.plan.write_text(text, encoding="utf-8")
                else:
                    (self.repo / "a.txt").write_text("2\n", encoding="utf-8")
                self.assertNotIn("mang", run_main("loop", "init")[2])
                st = json.loads((self.repo / ".autopilot" / "state.json").read_text(encoding="utf-8"))
                self.assertNotIn("carried", st)

    def test_loop_init_carry_drops_stale_items(self) -> None:
        run_main("loop", "init")
        run_main("loop", "record", "--task", "T-001", "--", "true")
        run_main("loop", "defer", "--task", "T-002", "--reason", "chủ repo ký")
        run_main("loop", "stop", "--reason", "x")
        # PLAN mới: Gate T-001 đổi (bằng chứng cũ không còn khớp), T-002 đã xong tay
        self.plan.write_text(
            "- [x] `T-001` a — Gate: `true && true`\n- [x] `T-002` cần người — Gate: `true`\n", encoding="utf-8"
        )
        rc, _, err = run_main("loop", "init")
        self.assertEqual(rc, 0)
        self.assertNotIn("giữ", err)
        self.assertNotIn("mang", err)
        st = json.loads((self.repo / ".autopilot" / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(st.get("deferred", {}), {})
        self.assertIn("T-001", run_main("loop", "status")[1])  # Gate đổi → verify T-001

    def test_loop_init_carry_warns_ticked_without_local_evidence(self) -> None:
        # Máy/container mới: PLAN đợt trước đã tick, `.autopilot/evidence/` không có → nói rõ và gợi ý PLAN mỗi đợt.
        self.plan.write_text("- [x] `T-001` a — Gate: `true`\n- [ ] `T-003` c — Gate: `true`\n", encoding="utf-8")
        rc, _, err = run_main("loop", "init")
        self.assertEqual(rc, 0)
        self.assertIn("1 task [x] không có bằng chứng ở máy này (T-001)", err)
        self.assertIn("PLAN-<đợt>.md", err)


class DecideWorktreesTest(TmpRepoCase):
    """T-2612 (phản hồi dự án đích): `loop decide` ở hai worktree cùng repo đều ra D-001 — số kế tiếp chỉ đọc sổ cây
    đang đứng. Nay lấy max qua sổ ở mọi worktree (`git worktree list`)."""

    def setUp(self) -> None:
        super().setUp()
        self.main = self.init_repo()
        (self.main / "README.md").write_text("x\n", encoding="utf-8")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "init")
        self.wt = self.tmp / "wt-b"
        self.git("worktree", "add", "-q", "-b", "b", str(self.wt))
        self.enterContext(unittest.mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(self.main)}))

    def decide(self, where: Path) -> str:
        with chdir(where):
            rc, out, err = run_main(
                "loop", "decide", "--question", "q", "--option", "a", "--option", "b", "--choice", "1",
                "--why", "w", "--revert", "r",
            )  # fmt: skip
        self.assertEqual(rc, 0, err)
        return out

    def test_decide_worktrees_numbers_do_not_collide(self) -> None:
        self.assertIn("D-001", self.decide(self.main))
        self.assertIn("D-002", self.decide(self.wt))
        self.assertIn("D-003", self.decide(self.main))
        log = (self.wt / "docs" / "autopilot" / "DECISIONS.md").read_text(encoding="utf-8")
        self.assertIn("### D-002", log)
        self.assertNotIn("### D-001", log)  # chỉ đọc sổ worktree khác để đánh số, không chép

    def test_decide_worktrees_unreadable_log_is_skipped(self) -> None:
        self.decide(self.main)
        real = Path.read_text

        def flaky(path: Path, *a: object, **k: object) -> str:
            if path.resolve().is_relative_to(self.main.resolve()) and path.name == "DECISIONS.md":
                raise OSError("không đọc được")
            return real(path, *a, **k)  # type: ignore[arg-type]  # bọc hàm thật, đối số Path hoặc str

        with unittest.mock.patch.object(Path, "read_text", flaky):
            self.assertIn("D-001", self.decide(self.wt))  # sổ cây chính không đọc được: bỏ qua


# Tiến trình giữ `flock(LOCK_EX)` trên file argv[1]: in "held" khi đã giữ, nhả sau argv[2] giây (âm → tới khi stdin đóng).
LOCK_HOLDER = (
    "import fcntl, os, sys, time\n"
    "fd = os.open(sys.argv[1], os.O_RDWR | os.O_CREAT, 0o600)\n"
    "fcntl.flock(fd, fcntl.LOCK_EX)\n"
    "print('held', flush=True)\n"
    "time.sleep(float(sys.argv[2])) if float(sys.argv[2]) >= 0 else sys.stdin.read()\n"
)


def hold_state_lock(tc: unittest.TestCase, base: Path, seconds: float = -1.0) -> None:
    """Tiến trình khác giữ khoá `state.lock` của `base`; trả khi khoá đã được giữ. Dọn khi test xong."""
    lock = base / ".autopilot" / xt.STATE_LOCK_FILE
    lock.parent.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, "-c", LOCK_HOLDER, str(lock), str(seconds)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    assert p.stdin is not None and p.stdout is not None
    tc.addCleanup(p.wait, 30)
    tc.addCleanup(p.stdin.close)
    tc.addCleanup(p.stdout.close)
    tc.assertEqual(p.stdout.readline().strip(), "held")


class UpdateStateTest(TmpRepoCase):
    """T-3538 (ADR-0052 §2, nghiên cứu §4C/R4): `update_state` đọc–sửa–ghi trong khoá `state.lock`, kiểm `rev`."""

    def setUp(self) -> None:
        super().setUp()
        self.enterContext(unittest.mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(self.tmp)}))

    def seed(self, **st: object) -> None:
        xt.write_state(dict(st), self.tmp)

    def init_loop(self, plan: str = PLAN) -> None:
        (self.tmp / "docs" / "autopilot").mkdir(parents=True, exist_ok=True)
        (self.tmp / "docs" / "autopilot" / "PLAN.md").write_text(plan, encoding="utf-8")
        self.assertEqual(run_main("loop", "init", "--force")[0], 0)

    def test_update_state_r4_two_snapshots_keep_both_updates(self) -> None:
        # R4 (research/evidence/2026-10-26-three-loops/state-lost-update.json): hai bản chụp cũ ghi đè nhau mất
        # `iterations`. Qua `update_state` mỗi thay đổi áp trên state mới nhất trong khoá → giữ cả hai.
        before = {"active": True, "iterations": 7, "deferred": {}, "same_failure_count": 0}
        deferred = {"T-900": {"reason": "cần khoá", "at": "2026-10-26T00:00:00+00:00"}}
        self.seed(**before)
        a, b = xt.read_state(self.tmp), xt.read_state(self.tmp)
        a["iterations"] += 1
        b["deferred"] = deferred
        xt.write_state(a, self.tmp)
        xt.write_state(b, self.tmp)
        self.assertEqual(xt.read_state(self.tmp)["iterations"], 7)  # đường cũ: mất cập nhật (tái hiện R4)

        self.seed(**before)
        self.assertEqual(xt.update_state(self.tmp, lambda cur: {**cur, "iterations": cur["iterations"] + 1})["rev"], 1)
        self.assertEqual(xt.update_state(self.tmp, lambda cur: {**cur, "deferred": deferred})["rev"], 2)
        st = xt.read_state(self.tmp)
        self.assertEqual((st["iterations"], st["deferred"], st["rev"]), (8, deferred, 2))

    def test_update_state_rev_mismatch_reapplies_fn(self) -> None:
        # Lệnh ghi ngoài khoá (đường cũ) đổi `rev` trong lúc `fn` chạy → đọc lại, áp lại `fn` trên state mới.
        self.seed(active=True, iterations=1, rev=3)
        calls: list[int] = []

        def bump(cur: dict) -> dict:
            calls.append(cur["rev"])
            if len(calls) == 1:
                xt.write_state({**cur, "deferred": {"T-9": {}}, "rev": 4}, self.tmp)
            cur["iterations"] += 1
            return cur

        out = xt.update_state(self.tmp, bump)
        self.assertEqual(calls, [3, 4])
        self.assertEqual((out["iterations"], out["rev"], list(out["deferred"])), (2, 5, ["T-9"]))
        self.assertEqual(xt.read_state(self.tmp), out)

    def test_update_state_retries_zero_mismatch_raises_without_overwrite(self) -> None:
        self.seed(active=True, rev=1)
        outsider = {"active": False, "rev": 7}

        def change(cur: dict) -> dict:
            xt.write_state(outsider, self.tmp)
            cur["session_id"] = "x"
            return cur

        with self.assertRaises(xt.StateRevConflict) as ctx:
            xt.update_state(self.tmp, change, retries=0)
        self.assertIsInstance(ctx.exception, OSError)  # `main` → một dòng, exit 2
        self.assertIn("sau 1 lần", str(ctx.exception))
        self.assertEqual(xt.read_state(self.tmp), outsider)  # không ghi đè

    def test_update_state_retries_exhausted_raises(self) -> None:
        self.seed(rev=0)
        calls: list[int] = []

        def always_moves(cur: dict) -> dict:
            calls.append(1)
            xt.write_state({"rev": 100 + len(calls)}, self.tmp)
            return cur

        with self.assertRaises(xt.StateRevConflict):
            xt.update_state(self.tmp, always_moves)
        self.assertEqual(len(calls), 4)  # 1 lần đầu + 3 lần áp lại
        self.assertEqual(xt.read_state(self.tmp), {"rev": 104})

    def test_update_state_missing_or_bad_rev_counts_as_zero(self) -> None:
        for old in ({"active": True}, {"rev": "7"}, {"rev": True}, {"rev": None}):
            with self.subTest(old):
                xt.write_state(old, self.tmp)
                self.assertEqual(xt.update_state(self.tmp, lambda cur: cur)["rev"], 1)

    def test_update_state_missing_state_and_fn_none(self) -> None:
        seen: list[dict] = []

        def skip(cur: dict) -> None:
            seen.append(cur)
            cur["mutated"] = True  # `fn` nhận bản sao: sửa rồi bỏ không lọt ra ngoài

        self.assertEqual(xt.update_state(self.tmp, skip), {})
        self.assertEqual(seen, [{"mutated": True}])
        self.assertIsNone(xt.read_state(self.tmp))  # None → không ghi
        self.assertTrue((self.tmp / ".autopilot" / xt.STATE_LOCK_FILE).exists())
        self.seed(active=True, rev=2)
        self.assertEqual(xt.update_state(self.tmp, skip), {"active": True, "rev": 2})
        self.assertEqual(xt.read_state(self.tmp), {"active": True, "rev": 2})
        (self.tmp / ".autopilot" / "state.json").unlink()
        self.assertEqual(xt.update_state(None, lambda cur: {**cur, "active": True}), {"active": True, "rev": 1})

    def test_update_state_lock_timeout_in_other_process(self) -> None:
        self.seed(active=True, rev=1)
        hold_state_lock(self, self.tmp)
        called: list[int] = []
        with unittest.mock.patch.object(xt, "STATE_LOCK_TIMEOUT", 0.2):
            with self.assertRaises(xt.StateLockTimeout) as ctx:
                xt.update_state(self.tmp, lambda cur: called.append(1) or cur)
        self.assertIsInstance(ctx.exception, OSError)
        self.assertIn("0.2 s", str(ctx.exception))
        self.assertEqual(called, [])  # không giữ được khoá thì không đọc–sửa–ghi
        self.assertEqual(xt.read_state(self.tmp), {"active": True, "rev": 1})

    def test_update_state_waits_for_lock_then_writes(self) -> None:
        self.seed(rev=1)
        hold_state_lock(self, self.tmp, seconds=0.3)
        self.assertEqual(xt.update_state(self.tmp, lambda cur: {**cur, "x": 1}), {"rev": 2, "x": 1})

    def test_update_state_threads_do_not_lose_updates(self) -> None:
        # Hai luồng, mỗi luồng 25 lần tăng bộ đếm riêng, barrier trước mỗi lần; mỗi lần mở fd khoá riêng nên flock
        # loại trừ cả hai luồng cùng tiến trình.
        self.seed(rev=0)
        barrier = threading.Barrier(2)

        def worker(key: str) -> None:
            for _ in range(25):
                barrier.wait(30)
                xt.update_state(self.tmp, lambda cur: {**cur, key: cur.get(key, 0) + 1})

        threads = [threading.Thread(target=worker, args=(k,)) for k in ("a", "b")]
        for t in threads:
            t.start()
        for t in threads:
            t.join(60)
        self.assertEqual(xt.read_state(self.tmp), {"rev": 50, "a": 25, "b": 25})

    def test_update_state_without_fcntl_skips_lock_but_checks_rev(self) -> None:
        with unittest.mock.patch.dict(sys.modules, {"fcntl": None}):
            self.assertIsNone(xt._fcntl())
            self.assertEqual(xt.update_state(self.tmp, lambda cur: {"a": 1}), {"a": 1, "rev": 1})
            self.assertFalse((self.tmp / ".autopilot" / xt.STATE_LOCK_FILE).exists())

            def moved(cur: dict) -> dict:
                xt.write_state({"rev": 9}, self.tmp)
                return cur

            with self.assertRaises(xt.StateRevConflict):
                xt.update_state(self.tmp, moved, retries=0)
        self.assertIsNotNone(xt._fcntl())

    def test_update_state_loop_record_gate_runs_outside_lock(self) -> None:
        # Gate (giả) tự lấy khoá với timeout 0: lấy được ⇔ `loop record` không giữ khoá trong lúc chạy Gate (fd riêng nên
        # flock loại trừ cả trong cùng tiến trình).
        self.init_loop("- [ ] `T-001` a — Gate: `true`\n")
        rev0 = xt._state_rev(xt.read_state(self.tmp))
        gates: list[str] = []

        def gate(cmd: str, base: Path, timeout: int) -> tuple[int, str]:
            with xt._state_lock(base):
                gates.append(cmd)
            return 0, "ok"

        with (
            unittest.mock.patch.object(xt, "run_gate_shell", gate),
            unittest.mock.patch.object(xt, "STATE_LOCK_TIMEOUT", 0),
        ):
            rc, out, err = run_main("loop", "record", "--task", "T-001", "--no-tick", "--", "true")
        self.assertEqual((rc, gates), (0, ["true"]), out + err)
        st = xt.read_state(self.tmp)
        self.assertEqual((st["rev"], st["same_failure_count"]), (rev0 + 1, 0))

    def test_update_state_loop_record_lock_timeout_exit_2(self) -> None:
        self.init_loop("- [ ] `T-001` a — Gate: `false`\n")
        hold_state_lock(self, self.tmp)
        with unittest.mock.patch.object(xt, "STATE_LOCK_TIMEOUT", 0.1):
            rc, _, err = run_main("loop", "record", "--task", "T-001", "--", "false")
        self.assertEqual(rc, 2)
        self.assertIn("bận quá 0.1 s", err)
        self.assertTrue((self.tmp / ".autopilot" / "evidence" / "T-001.json").exists())  # bằng chứng đã ghi trước
        self.assertEqual(xt.read_state(self.tmp).get("same_failure_count", 0), 0)  # đếm lỗi chưa ghi: chạy lại lệnh

    def test_update_state_loop_record_counts_same_failure(self) -> None:
        self.init_loop("- [ ] `T-001` a — Gate: `false`\n")
        for n in (1, 2):
            run_main("loop", "record", "--task", "T-001", "--", "false")
            st = xt.read_state(self.tmp)
            self.assertEqual((st["same_failure_count"], st["last_failure_task"]), (n, "T-001"))
        run_main("loop", "record", "--task", "T-001", "--", "echo khác; false")
        self.assertEqual(xt.read_state(self.tmp)["same_failure_count"], 1)
        (self.tmp / ".autopilot" / "state.json").unlink()
        rc, _, _ = run_main("loop", "record", "--task", "T-001", "--", "false")
        self.assertEqual((rc, xt.read_state(self.tmp)), (1, None))  # chưa `loop init`: không tạo state

    def test_update_state_stop_hook_lock_error_fails_open(self) -> None:
        self.init_loop()
        before = xt.read_state(self.tmp)
        hold_state_lock(self, self.tmp)
        with unittest.mock.patch.object(xt, "STATE_LOCK_TIMEOUT", 0.1):
            rc, out, err = run_main("loop", "hook-stop", stdin="{}")
        self.assertEqual((rc, out), (0, ""))  # còn việc nhưng khoá bận → cho dừng, không kẹt phiên
        self.assertIn("StateLockTimeout", err)
        self.assertEqual(xt.read_state(self.tmp), before)
        log = (self.tmp / ".autopilot" / xt.STOP_LOG_FILE).read_text(encoding="utf-8")
        self.assertIn("cho dừng, không ghi state: StateLockTimeout", log)

    def test_update_state_stop_hook_state_vanishes_and_end_branch(self) -> None:
        self.init_loop()
        sf = self.tmp / ".autopilot" / "state.json"
        real = xt.loop_verdict

        def verdict_then_vanish(base: Path) -> dict:
            v = real(base)
            sf.unlink()
            return v

        with unittest.mock.patch.object(xt, "loop_verdict", verdict_then_vanish):
            self.assertEqual(xt.hook_stop("{}", self.tmp), ("", 0))  # state biến mất giữa chừng → cho dừng, không tạo
        self.assertFalse(sf.exists())
        self.init_loop()
        xt.write_state({**xt.read_state(self.tmp), "blocked": True, "blocked_reason": "x"}, self.tmp)
        out, rc = xt.hook_stop(json.dumps({"permission_mode": "auto"}), self.tmp)
        st = xt.read_state(self.tmp)
        self.assertEqual((out, rc, st["active"], st["permission_mode"]), ("", 0, False, "auto"))
        self.assertEqual(st["final_verdict"]["verdict"], "blocked")

    def test_update_state_stop_hook_skips_loop_stopped_meanwhile(self) -> None:
        # Review #294: `loop stop` chen giữa verdict và ghi → Stop hook không đè `final_verdict` "stopped" (nhánh kết
        # thúc: vòng `blocked`) và không chặn dừng thêm một lượt (nhánh `continue`).
        real = xt.loop_verdict

        def verdict_then_stop(base: Path) -> dict:
            v = real(base)
            self.assertEqual(run_main("loop", "stop", "--reason", "người dừng")[0], 0)
            return v

        self.init_loop()
        xt.write_state({**xt.read_state(self.tmp), "blocked": True, "blocked_reason": "x"}, self.tmp)
        with unittest.mock.patch.object(xt, "loop_verdict", verdict_then_stop):
            self.assertEqual(xt.hook_stop("{}", self.tmp), ("", 0))
        st = xt.read_state(self.tmp)
        self.assertEqual((st["active"], st["final_verdict"]["verdict"]), (False, "stopped"))
        self.init_loop()
        it = xt.read_state(self.tmp).get("iterations", 0)
        with unittest.mock.patch.object(xt, "loop_verdict", verdict_then_stop):
            self.assertEqual(xt.hook_stop("{}", self.tmp), ("", 0))  # còn task nhưng vòng vừa dừng → cho dừng
        st = xt.read_state(self.tmp)
        self.assertEqual((st["active"], st.get("iterations", 0)), (False, it))

    def test_update_state_flock_unsupported_runs_unlocked(self) -> None:
        # Review #294: FS không hỗ trợ flock (ENOLCK) → như nhánh không `fcntl`: ghi được, kiểm `rev`, báo một dòng.

        def no_lock(fd: int, op: int) -> None:
            raise OSError(errno.ENOLCK, "No locks available")

        with unittest.mock.patch("fcntl.flock", no_lock), contextlib.redirect_stderr(io.StringIO()) as err:
            self.assertEqual(xt.update_state(self.tmp, lambda cur: {"a": 1}), {"a": 1, "rev": 1})
        self.assertIn("flock không dùng được", err.getvalue())

        def other(fd: int, op: int) -> None:
            raise OSError(errno.EIO, "I/O error")

        with unittest.mock.patch("fcntl.flock", other), self.assertRaises(OSError):
            xt.update_state(self.tmp, lambda cur: {"a": 2})


def racing_update_state(base: Path, writes: list[dict]):
    """`update_state` thật, nhưng lần gọi `fn` đầu tiên có "lệnh ghi ngoài khoá" chen vào: ghi `{**state, outsider: True}`
    với `rev + 1` trước khi `fn` chạy — mô phỏng hai lệnh ghi xen kẽ tất định (ADR-0052 §2)."""
    real = xt.update_state

    def racing(b: Path | None, fn: xt.StateFn, retries: int = 3) -> dict:
        def first_races(cur: dict) -> dict | None:
            if not writes:
                outsider = {**cur, "outsider": True, "rev": xt._state_rev(cur) + 1}
                writes.append(outsider)
                xt.write_state(outsider, base)
            return fn(cur)

        return real(b, first_races, retries)

    return unittest.mock.patch.object(xt, "update_state", racing)


class StateWritersTest(TmpRepoCase):
    """T-3559 (ADR-0052 §2): mọi lệnh ghi `state.json` đi qua `update_state` — `rev` tăng một mỗi lần ghi; lệnh áp lại
    được (block, defer, ci-triage, checkpoint, stop) áp lại trên state mới khi lệch `rev`; `init`/`resume` (`retries=0`)
    lệch thì exit 2, không ghi đè; khoá bận → exit 2 (lệnh) hoặc fail-open (checkpoint)."""

    def setUp(self) -> None:
        super().setUp()
        self.enterContext(unittest.mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(self.tmp)}))
        os.environ.pop("CLAUDE_CODE_SESSION_ID", None)
        (self.tmp / "docs" / "autopilot").mkdir(parents=True)
        (self.tmp / "docs" / "autopilot" / "PLAN.md").write_text(PLAN, encoding="utf-8")
        self.assertEqual(run_main("loop", "init")[0], 0)
        self.rev0 = xt.read_state(self.tmp)["rev"]

    def ci_log(self) -> str:
        log = self.tmp / "ci.log"
        log.write_text("FAILED tests/test_a.py::test_x - AssertionError\n", encoding="utf-8")
        return str(log)

    # Lệnh áp lại được: (đối số, exit mong đợi, kiểm state sau khi ghi)
    def reapply_cases(self) -> list[tuple[tuple[str, ...], int, str]]:
        return [
            (("loop", "block", "--reason", "chờ khoá"), 0, "blocked"),
            (("loop", "defer", "--task", "T-002", "--reason", "khoá thật"), 0, "deferred"),
            (("loop", "ci-triage", "--run", "42", "--log", self.ci_log()), 0, "episode"),
            (("loop", "stop", "--reason", "xong"), 0, "final_verdict"),
        ]

    def test_state_writers_bump_rev_once(self) -> None:
        for args, code, key in self.reapply_cases():
            with self.subTest(args[1]):
                rev = xt.read_state(self.tmp)["rev"]
                rc, out, err = run_main(*args)
                st = xt.read_state(self.tmp)
                self.assertEqual((rc, st["rev"]), (code, rev + 1), out + err)
                self.assertIn(key, st)
        rev = xt.read_state(self.tmp)["rev"]
        self.assertEqual(run_main("loop", "resume", "--reason", "tiếp")[0], 0)
        self.assertEqual(run_main("loop", "checkpoint", stdin='{"trigger": "auto"}')[0], 0)
        st = xt.read_state(self.tmp)
        self.assertEqual((st["rev"], st["active"], st["checkpoint"]["trigger"]), (rev + 2, True, "auto"))
        self.assertEqual(run_main("loop", "init", "--force")[0], 0)  # state mới thay toàn bộ nhưng `rev` không về 0
        self.assertEqual(xt.read_state(self.tmp)["rev"], rev + 3)

    def test_state_writers_block_without_state_creates_rev_1(self) -> None:
        (self.tmp / ".autopilot" / "state.json").unlink()
        self.assertEqual(run_main("loop", "block", "--reason", "r")[0], 0)
        st = xt.read_state(self.tmp)
        self.assertEqual((st["active"], st["blocked"], st["rev"]), (True, True, 1))

    def test_state_writers_reapply_on_concurrent_write(self) -> None:
        # Lệnh ghi ngoài khoá chen giữa đọc và ghi: `fn` áp lại trên state mới — giữ cả thay đổi của lệnh kia.
        for args, code, key in self.reapply_cases():
            with self.subTest(args[1]):
                rev, writes = xt.read_state(self.tmp)["rev"], []
                with racing_update_state(self.tmp, writes):
                    rc, out, err = run_main(*args)
                st = xt.read_state(self.tmp)
                self.assertEqual((rc, st["rev"], st["outsider"]), (code, rev + 2, True), out + err)
                self.assertIn(key, st)
                xt.write_state({k: v for k, v in st.items() if k != "outsider"}, self.tmp)
        writes = []
        with racing_update_state(self.tmp, writes):
            self.assertEqual(run_main("loop", "checkpoint", stdin='{"trigger": "manual"}')[0], 0)
        st = xt.read_state(self.tmp)
        self.assertEqual((st["outsider"], st["checkpoint"]["trigger"]), (True, "manual"))

    def test_state_writers_defer_problem_checked_on_fresh_state(self) -> None:
        # Chen giữa: lệnh kia ghi T-002 đang lỗi → `_defer_problem` trên state mới từ chối (không né bế tắc máy).
        real = xt.update_state

        def racing(b: Path | None, fn: xt.StateFn, retries: int = 3) -> dict:
            def first(cur: dict) -> dict | None:
                if not cur.get("last_failure_task"):
                    failing = {**cur, "same_failure_count": 1, "last_failure_task": "T-002", "rev": cur["rev"] + 1}
                    xt.write_state(failing, self.tmp)
                return fn(cur)

            return real(b, first, retries)

        with unittest.mock.patch.object(xt, "update_state", racing):
            rc, _, err = run_main("loop", "defer", "--task", "T-002", "--reason", "khoá")
        st = xt.read_state(self.tmp)
        self.assertEqual((rc, st["rev"], st.get("deferred")), (2, self.rev0 + 1, None))
        self.assertIn("✗ Không defer T-002: task đang lỗi", err)

    def test_state_writers_ci_triage_same_run_not_counted_twice(self) -> None:
        # Hai `ci-triage` cùng run chạy song song: lệnh sau thấy run đã triage trong khoá → dùng lại, không đếm lại.
        log = self.ci_log()
        before = xt.read_state(self.tmp)
        self.assertEqual(run_main("loop", "ci-triage", "--run", "42", "--log", log)[0], 0)
        ep = xt.read_state(self.tmp)["episode"]
        xt.write_state({**before, "rev": before["rev"] + 2}, self.tmp)  # quay lại state chưa có run 42
        real = xt.update_state

        def racing(b: Path | None, fn: xt.StateFn, retries: int = 3) -> dict:
            def first(cur: dict) -> dict | None:
                if "episode" not in cur:
                    xt.write_state({**cur, "episode": ep, "rev": cur["rev"] + 1}, self.tmp)
                return fn(cur)

            return real(b, first, retries)

        with unittest.mock.patch.object(xt, "update_state", racing):
            rc, out, _ = run_main("loop", "ci-triage", "--run", "42", "--log", log, "--json")
        got = json.loads(out)["episode"]
        self.assertEqual((rc, got["same_signature"], got["fix_attempts"]), (0, 1, 1))
        self.assertEqual(xt.read_state(self.tmp)["episode"]["same_signature"], 1)
        with self.assertRaises(xt.StateRevConflict):  # run có lúc đọc trước, mất trong khoá: không có log để đếm
            xt._ci_triage_state({}, "42", None, None, None, {})

    def test_state_writers_init_resume_conflict_exit_2_no_overwrite(self) -> None:
        # `retries=0`: lệch `rev` giữa đọc và ghi → exit 2, một dòng, state của lệnh kia giữ nguyên.
        for args in (("loop", "init", "--force"), ("loop", "resume", "--reason", "tiếp")):
            with self.subTest(args[1]):
                writes: list[dict] = []
                with racing_update_state(self.tmp, writes):
                    rc, out, err = run_main(*args)
                self.assertEqual((rc, out), (2, ""))
                self.assertEqual(len(err.strip().splitlines()), 1, err)
                self.assertIn("rev lệch sau 1 lần", err)
                self.assertEqual(xt.read_state(self.tmp), writes[0])

    def test_state_writers_init_state_changed_after_live_check(self) -> None:
        # `_live_loop` (verdict, kiểm cuối) chạy ngoài khoá; state đổi sau đó → không ghi đè vòng vừa được bật.
        other = {**xt.read_state(self.tmp), "active": True, "started": "khác", "rev": self.rev0 + 1}

        def live(base: Path) -> str:
            xt.write_state(other, base)
            return ""

        with unittest.mock.patch.object(xt, "_live_loop", live):
            rc, out, err = run_main("loop", "init")
        self.assertEqual((rc, out), (2, ""))
        self.assertIn("đổi sau khi `loop init` kiểm vòng đang chạy", err)
        self.assertEqual(xt.read_state(self.tmp), other)

    def test_state_writers_lock_busy_exit_2(self) -> None:
        cases = [
            *(a for a, _, _ in self.reapply_cases()),
            ("loop", "resume", "--reason", "tiếp"),
            ("loop", "init", "--force"),
        ]
        before = xt.read_state(self.tmp)
        hold_state_lock(self, self.tmp)
        with unittest.mock.patch.object(xt, "STATE_LOCK_TIMEOUT", 0.05):
            for args in cases:
                with self.subTest(args[1]):
                    rc, out, err = run_main(*args)
                    self.assertEqual(rc, 2, out + err)
                    self.assertIn("state.lock bận quá 0.05 s", err)
                    self.assertEqual(xt.read_state(self.tmp), before)
            rc, out, err = run_main("loop", "checkpoint", stdin='{"trigger": "auto"}')
        self.assertEqual((rc, out), (0, ""))  # PreCompact không bao giờ chặn compaction
        self.assertIn("[xt checkpoint] không ghi được state, bỏ checkpoint: StateLockTimeout", err)
        self.assertEqual(xt.read_state(self.tmp), before)
        log = (self.tmp / ".autopilot" / xt.CHECKPOINT_LOG_FILE).read_text(encoding="utf-8")
        self.assertIn("bỏ checkpoint: StateLockTimeout", log)

    def test_state_writers_state_vanishes_before_lock(self) -> None:
        # State bị xoá giữa lần đọc trước và khoá: không tạo lại state rỗng; lệnh cần vòng báo như chưa `loop init`.
        sf = self.tmp / ".autopilot" / "state.json"
        real = xt._state_lock

        @contextlib.contextmanager
        def vanish(base: Path) -> Iterator[None]:
            sf.unlink(missing_ok=True)
            with real(base):
                yield

        with unittest.mock.patch.object(xt, "_state_lock", vanish):
            for args, code in (
                (("loop", "stop", "--reason", "x"), 0),
                (("loop", "defer", "--task", "T-002", "--reason", "r"), 2),
                (("loop", "resume", "--reason", "r"), 2),
                (
                    (
                        "loop",
                        "checkpoint",
                    ),
                    0,
                ),
            ):
                with self.subTest(args[1]):
                    xt.write_state({"active": True, "plan": "docs/autopilot/PLAN.md", "rev": 4}, self.tmp)
                    rc, _, err = run_main(*args, stdin="{}")
                    self.assertEqual((rc, sf.exists()), (code, False))
                    if code == 2:
                        self.assertIn("Chưa có vòng lặp", err)
        self.assertIsNone(xt.update_loop_state(self.tmp, lambda cur: cur))  # không có state: không khoá


TR_PLAN = "- [ ] `T-001` việc một — Gate: `bash gate.sh`\n- [ ] `T-002` việc hai — Gate: `true`\n"
# Gate giả cho `task_runs`: đỏ, chữ ký luân phiên A/B theo bộ đếm; có `same` → luôn A; có `green` → xanh.
TR_GATE = r"""#!/bin/bash
d="$(dirname "$0")"
[ -f "$d/green" ] && exit 0
n=$(( $(cat "$d/.counter" 2>/dev/null || echo 0) + 1 ))
echo "$n" > "$d/.counter"
if [ -f "$d/same" ] || [ $((n % 2)) -eq 1 ]; then echo "AssertionError A"; else echo "TypeError B"; fi
exit 1
"""
TR_REASON = "T-001: {n} lần đỏ, {m} chữ ký khác nhau — đặc tả hoặc Gate sai, người xem"


class TaskRunsTest(TmpRepoCase):
    """T-3539 (ADR-0052 §3, R5/R6): `task_runs` đếm lần `loop record` đỏ theo task (mọi chữ ký); chạm `max_task_runs`
    (mặc định 2 × `max_same_failure` = 6, `--max-task-runs 0` tắt) → `blocked` nêu N lần đỏ và M chữ ký. Xanh, đổi
    spec/Gate trong PLAN, `loop resume` đặt lại; đợt mới không mang."""

    def setUp(self) -> None:
        super().setUp()
        self.init_repo()
        self.plan = self.repo / "docs" / "autopilot" / "PLAN.md"
        self.plan.parent.mkdir(parents=True)
        self.plan.write_text(TR_PLAN, encoding="utf-8")
        (self.repo / "gate.sh").write_text(TR_GATE, encoding="utf-8")
        self.enterContext(unittest.mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(self.repo)}))
        os.environ.pop("CLAUDE_CODE_SESSION_ID", None)
        self.enterContext(chdir(self.repo))

    def red(self, task: str = "T-001", cmd: str = "bash gate.sh") -> None:
        self.assertEqual(run_main("loop", "record", "--task", task, "--", cmd)[0], 1)

    def verdict(self) -> dict:
        rc, out, err = run_main("loop", "status", "--json")
        self.assertEqual(rc, 0, err)
        return json.loads(out)

    def runs(self) -> dict:
        return xt.read_state(self.repo)["task_runs"]

    def test_task_runs_r5_blocks_at_sixth_not_before(self) -> None:
        self.assertEqual(run_main("loop", "init")[0], 0)
        st = xt.read_state(self.repo)
        self.assertEqual((st["max_task_runs"], st["task_runs"]), (6, {}))
        for i in range(1, 6):
            self.red()
            self.assertEqual(self.runs(), {"T-001": i})
            self.assertEqual(xt.read_state(self.repo)["same_failure_count"], 1)  # chữ ký luân phiên: R5
            self.assertEqual(self.verdict()["verdict"], "continue")
        self.red()
        v = self.verdict()
        self.assertEqual((v["verdict"], v["reason"], v["task"]), ("blocked", TR_REASON.format(n=6, m=2), "T-001"))
        self.assertTrue(run_main("loop", "status")[1].startswith("verdict: blocked"))
        # vòng bị chặn vì `task_runs` là vòng sống: `loop init` chỉ lối ra `resume`, không ghi đè
        rc, _, err = run_main("loop", "init")
        self.assertEqual(rc, 2)
        self.assertIn("6 lần đỏ, 2 chữ ký khác nhau", err)
        self.assertIn("loop resume --reason", err)

    def test_task_runs_r6_same_signature_unchanged(self) -> None:
        run_main("loop", "init")
        (self.repo / "same").write_text("1", encoding="utf-8")
        for _ in range(2):
            self.red()
        self.assertEqual(self.verdict()["verdict"], "continue")
        self.red()
        v = self.verdict()
        self.assertEqual(v["verdict"], "blocked")
        self.assertIn("cùng một lỗi lặp 3 lần (T-001)", v["reason"])  # chữ ký xét trước `task_runs`
        self.assertEqual(self.runs(), {"T-001": 3})

    def test_task_runs_green_resets(self) -> None:
        run_main("loop", "init")
        for _ in range(5):
            self.red()
        (self.repo / "green").write_text("1", encoding="utf-8")
        self.assertEqual(run_main("loop", "record", "--task", "T-001", "--no-tick", "--", "bash gate.sh")[0], 0)
        st = xt.read_state(self.repo)
        self.assertEqual((st["task_runs"], st["task_runs_rev"]), ({}, {}))
        (self.repo / "green").unlink()
        self.red()
        self.assertEqual(self.runs(), {"T-001": 1})
        self.assertEqual(self.verdict()["verdict"], "continue")

    def test_task_runs_plan_change_resets(self) -> None:
        # Đổi Gate (lệnh) hoặc spec của task trong PLAN là "đổi cách" → đếm lại từ 0; task khác không bị đụng.
        run_main("loop", "init")
        self.red("T-002", "false")
        for _ in range(5):
            self.red()
        self.plan.write_text(TR_PLAN.replace("`bash gate.sh`", "`bash ./gate.sh`"), encoding="utf-8")
        self.red(cmd="bash ./gate.sh")
        self.assertEqual(self.runs(), {"T-002": 1, "T-001": 1})
        for _ in range(4):
            self.red(cmd="bash ./gate.sh")
        self.plan.write_text(TR_PLAN.replace("việc một", "việc một, tách nhỏ"), encoding="utf-8")
        self.red()
        self.assertEqual(self.runs(), {"T-002": 1, "T-001": 1})
        self.assertEqual(self.verdict()["verdict"], "continue")

    def test_task_runs_whitespace_gate_edit_does_not_reset(self) -> None:
        # Review #294: thêm một dấu cách vào Gate (cùng lệnh theo `same_command`) không phải "đổi cách" → không đếm lại.
        run_main("loop", "init")
        for _ in range(3):
            self.red()
        self.plan.write_text(TR_PLAN.replace("`bash gate.sh`", "`bash  gate.sh`"), encoding="utf-8")
        self.red(cmd="bash  gate.sh")
        self.assertEqual(self.runs(), {"T-001": 4})

    def test_task_runs_green_with_other_command_does_not_unblock(self) -> None:
        # Review #294: xanh bằng lệnh khác Gate (`-- true`) không xoá `task_runs`; xanh đúng Gate thì xoá.
        run_main("loop", "init", "--max-task-runs", "3")
        for _ in range(3):
            self.red()
        self.assertEqual(run_main("loop", "record", "--task", "T-001", "--no-tick", "--", "true")[0], 0)
        self.assertEqual((self.runs(), self.verdict()["verdict"]), ({"T-001": 3}, "blocked"))
        (self.repo / "green").write_text("", encoding="utf-8")
        self.assertEqual(run_main("loop", "record", "--task", "T-001", "--", "bash gate.sh")[0], 0)
        self.assertEqual(self.runs(), {})

    def test_task_runs_spec_whitespace_edit_does_not_reset(self) -> None:
        run_main("loop", "init")
        for _ in range(3):
            self.red()
        self.plan.write_text(TR_PLAN.replace("việc một", "việc  một"), encoding="utf-8")
        self.red()
        self.assertEqual(self.runs(), {"T-001": 4})

    def test_task_runs_rev_unbalanced_quote_gate(self) -> None:
        # Gate nháy lệch: `canonical_command` từ chối → so chuỗi đã bỏ khoảng trắng hai đầu (như `same_command`).
        run_main("loop", "init")
        st = xt.read_state(self.repo)
        self.plan.write_text("- [ ] `T-001` a — Gate: `echo 'x`\n", encoding="utf-8")
        one = xt.task_runs_rev(self.repo, st, "T-001")
        self.plan.write_text("- [ ] `T-001` a — Gate: `echo 'x  `\n", encoding="utf-8")
        self.assertEqual(xt.task_runs_rev(self.repo, st, "T-001"), one)
        self.plan.write_text("- [ ] `T-001` a — Gate: `echo 'y`\n", encoding="utf-8")
        self.assertNotEqual(xt.task_runs_rev(self.repo, st, "T-001"), one)

    def test_task_runs_blocked_task_stays_blocked_after_plan_change(self) -> None:
        # Review #294: task đã chạm trần — sửa Gate/spec trong PLAN rồi record đỏ không tự thoát chặn; chỉ xanh/resume gỡ.
        run_main("loop", "init", "--max-task-runs", "3")
        for _ in range(3):
            self.red()
        self.assertEqual(self.verdict()["verdict"], "blocked")
        self.plan.write_text(TR_PLAN.replace("`bash gate.sh`", "`bash ./gate.sh`"), encoding="utf-8")
        self.red(cmd="bash ./gate.sh")
        self.assertEqual((self.runs(), self.verdict()["verdict"]), ({"T-001": 4}, "blocked"))

    def test_task_runs_task_outside_plan_counts(self) -> None:
        run_main("loop", "init", "--max-task-runs", "2")
        self.assertIsNone(xt.task_runs_rev(self.repo, xt.read_state(self.repo), "T-777"))
        self.red("T-777", "false")
        self.red("T-777", "false")
        self.assertEqual(self.runs(), {"T-777": 2})
        self.assertEqual(
            self.verdict()["reason"], "T-777: 2 lần đỏ, 1 chữ ký khác nhau — đặc tả hoặc Gate sai, người xem"
        )

    def test_task_runs_zero_disables(self) -> None:
        run_main("loop", "init", "--max-task-runs", "0")
        for _ in range(8):
            self.red()
        self.assertEqual((xt.read_state(self.repo)["max_task_runs"], self.runs()), (0, {"T-001": 8}))
        self.assertEqual(self.verdict()["verdict"], "continue")

    def test_task_runs_custom_three(self) -> None:
        run_main("loop", "init", "--max-task-runs", "3")
        self.red()
        self.red()
        self.assertEqual(self.verdict()["verdict"], "continue")
        self.red()
        self.assertEqual(self.verdict()["reason"], TR_REASON.format(n=3, m=2))

    def test_task_runs_rejects_negative(self) -> None:
        with self.assertRaises(SystemExit) as cm:
            run_main("loop", "init", "--max-task-runs", "-1")
        self.assertEqual(cm.exception.code, 2)
        self.assertIsNone(xt.read_state(self.repo))

    def test_task_runs_reason_counts_last_n_reds_this_loop(self) -> None:
        # M = chữ ký khác nhau trong N lần đỏ CUỐI của task ở vòng này: bỏ lần xanh, lần đỏ trước khi đếm lại, task
        # khác, vòng khác.
        run_main("loop", "init", "--max-task-runs", "3")
        st = xt.read_state(self.repo)
        st["task_runs"] = {"T-001": 3, "T-002": 3}
        cur, old = st["started"], "2020-01-01T00:00:00+00:00"
        rows = [
            ("T-001", 1, "X", cur),
            ("T-001", 1, "Y", cur),
            ("T-001", 0, None, cur),
            ("T-001", 1, "A", cur),
            ("T-002", 1, "Z", cur),
            ("T-001", 1, "B", cur),
            ("T-001", 1, "W", old),
            ("T-001", 1, "A", cur),
        ]
        with (self.repo / ".autopilot" / "runs.jsonl").open("w", encoding="utf-8") as fh:
            for task, code, sig, loop in rows:
                fh.write(json.dumps({"task": task, "exit_code": code, "signature": sig, "loop": loop}) + "\n")
        v = xt._verdict_task_runs(st, self.repo)
        self.assertEqual(v, {"verdict": "blocked", "reason": TR_REASON.format(n=3, m=2), "task": "T-001"})  # ID đầu

    def test_task_runs_resume_resets_blocking_task(self) -> None:
        run_main("loop", "init", "--max-task-runs", "3")
        self.red("T-002", "false")
        for _ in range(3):
            self.red()
        self.assertEqual(self.verdict()["verdict"], "blocked")
        self.assertEqual(run_main("loop", "resume", "--reason", "người sửa đặc tả")[0], 0)
        self.assertEqual(self.runs(), {"T-002": 1})  # chỉ task đang chặn về 0
        self.assertEqual(self.verdict()["verdict"], "continue")
        self.red()
        self.assertEqual(self.runs(), {"T-002": 1, "T-001": 1})

    def test_task_runs_not_carried_to_next_init(self) -> None:
        run_main("loop", "init")
        for _ in range(4):
            self.red()
        run_main("loop", "stop", "--reason", "hết ngày")
        self.assertEqual(run_main("loop", "init", "--max-task-runs", "4")[0], 0)
        st = xt.read_state(self.repo)
        self.assertEqual((st["task_runs"], st["max_task_runs"]), ({}, 4))
        self.red()
        self.assertEqual(self.runs(), {"T-001": 1})

    def test_task_runs_old_state_defaults(self) -> None:
        # State trước ADR-0052 (không `task_runs`/`max_task_runs`) hoặc sai kiểu: trần = 2 × max_same_failure, đếm rỗng.
        self.assertEqual(xt._max_task_runs({}), 6)
        self.assertEqual(xt._max_task_runs({"max_same_failure": 4}), 8)
        self.assertEqual(xt._max_task_runs({"max_same_failure": "3", "max_task_runs": "9"}), 6)
        self.assertEqual(xt._task_runs({"task_runs": [1]}), {})
        self.assertEqual(xt._task_runs({"task_runs": {"T-001": "2", "T-002": True, "T-003": 2}}), {"T-003": 2})
        st = {"active": True, "task_runs": {"T-001": 9}, "max_task_runs": 0}
        self.assertIsNone(xt._verdict_task_runs(st, self.repo))
        cur = {"active": True, "task_runs_rev": ["x"]}
        xt._count_task_run(cur, "T-001", "sig", "r1")
        self.assertEqual((cur["task_runs"], cur["task_runs_rev"]), ({"T-001": 1}, {"T-001": "r1"}))

    def test_task_runs_concurrent_records_not_lost(self) -> None:
        # Hai luồng ghi đếm cùng lúc qua `update_state` (khoá + `rev`, ADR-0052 §2): không mất lần đếm nào.
        run_main("loop", "init", "--max-task-runs", "0")
        barrier = threading.Barrier(2)

        def worker(task: str) -> None:
            for _ in range(20):
                barrier.wait(timeout=20)
                xt.update_state(self.repo, lambda cur: xt._record_failure_count(cur, task, "sig-" + task, "r"))

        threads = [threading.Thread(target=worker, args=(t,)) for t in ("T-001", "T-002")]
        for t in threads:
            t.start()
        for t in threads:
            t.join(60)
        self.assertEqual(self.runs(), {"T-001": 20, "T-002": 20})


if __name__ == "__main__":
    unittest.main()
