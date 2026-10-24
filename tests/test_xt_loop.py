"""Test vòng tự trị (`xt.py loop …`) gắn với ngữ cảnh chạy: git worktree (T-2521) và phiên Claude Code (T-2522).

Gọi `xt.main([...])` trong tiến trình; worktree là `git worktree add` thật trong repo tạm, payload Stop hook là JSON giả.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
import unittest.mock
from contextlib import chdir
from pathlib import Path

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


if __name__ == "__main__":
    unittest.main()
