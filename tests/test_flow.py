"""Corpus luồng (ADR-0052 §1; nghiên cứu 2026-10-26 §10): chạy `xt.py` THẬT trong repo git tạm, không mock state.

State dựng bằng chính lệnh `loop init/record/defer/block`; không ca nào sửa tay `.autopilot/state.json`.

Cơ chế xfail (không skip):
- `XFAIL` = {ID: tái hiện + task sẽ sửa}. Ca có ID trong `XFAIL` mà KHÔNG có trong `XT_FLOW_STRICT` nhận
  `unittest.expectedFailure`: đỏ hôm nay thì suite vẫn exit 0; tự xanh thì "unexpected success" làm suite đỏ — nhắc gỡ ID khỏi `XFAIL`.
- `XT_FLOW_STRICT=FLOW-01,FLOW-04` (phân cách dấu phẩy, khoảng trắng bỏ qua, đọc lúc import) bỏ xfail của các ID đó: ca chạy thường
  nên Gate của task sửa chỉ xanh khi ca thật sự đạt.
- `@flow("FLOW-NN")` gắn ID cho test và ghi vào `FLOW_IDS`; `test_strict_ids_exist` đỏ khi `XT_FLOW_STRICT` hoặc `XFAIL`
  nêu ID không có test nào mang nó (Gate không xanh vì thiếu ca).
- Gỡ ID khỏi `XFAIL` khi task sửa xong; ID không còn xfail vẫn chạy thường.
"""

from __future__ import annotations

import json
import os
import re
import sys
import unittest
import unittest.mock
from collections.abc import Callable
from contextlib import chdir
from pathlib import Path
from typing import Any, TypeVar

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_xt_cli import TmpRepoCase, run_main

F = TypeVar("F", bound=Callable[..., Any])

XFAIL: dict[str, str] = {
    "FLOW-01": "R1 — chưa có `loop attach` (T-3540)",
    "FLOW-02": "§4A — chưa có `loop resolve` (T-3541)",
    "FLOW-04": "R5 — lỗi A/B luân phiên không bao giờ blocked: verdict `continue` (T-3539)",
    "FLOW-06": "§4B — state chưa có `task_runs` (T-3539)",
}
STRICT: frozenset[str] = frozenset(s.strip() for s in os.environ.get("XT_FLOW_STRICT", "").split(",") if s.strip())
FLOW_IDS: set[str] = set()


def flow(flow_id: str) -> Callable[[F], F]:
    """Gắn ID cho test; ID thuộc XFAIL và không thuộc STRICT → `expectedFailure`."""

    def deco(fn: F) -> F:
        FLOW_IDS.add(flow_id)
        if flow_id in XFAIL and flow_id not in STRICT:
            return unittest.expectedFailure(fn)
        return fn

    return deco


PLAN = (
    "- [ ] `T-001` việc một — Gate: `bash gate.sh`\n"
    "- [ ] `T-002` việc hai — Gate: `true`\n"
    "- [ ] `T-900` chờ người — Gate: `true`\n"
    "- [ ] `T-901` chờ người nữa — Gate: `true`\n"
)
# Gate giả: bộ đếm trong `.flow-counter`; có file `green` → xanh; không thì đỏ, chữ ký luân phiên theo STYLE.
GATE = r"""#!/bin/bash
d="$(dirname "$0")"
[ -f "$d/green" ] && exit 0
n=$(( $(cat "$d/.flow-counter" 2>/dev/null || echo 0) + 1 ))
echo "$n" > "$d/.flow-counter"
if [ "$(cat "$d/style" 2>/dev/null)" = "same" ] || [ $((n % 2)) -eq 1 ]; then
  echo "AssertionError A"
else
  echo "TypeError B"
fi
exit 1
"""
SESSION_A = "11111111-aaaa-bbbb-cccc-000000000001"
SESSION_B = "22222222-aaaa-bbbb-cccc-000000000002"


class FlowTest(TmpRepoCase):
    def setUp(self) -> None:
        super().setUp()
        repo = self.init_repo()
        (repo / "docs" / "autopilot").mkdir(parents=True)
        (repo / "docs" / "autopilot" / "PLAN.md").write_text(PLAN, encoding="utf-8")
        (repo / "gate.sh").write_text(GATE, encoding="utf-8")
        (repo / ".gitignore").write_text(".autopilot/\n.flow-counter\nstyle\ngreen\n", encoding="utf-8")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "init")
        self.enterContext(
            unittest.mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(repo), "CLAUDE_CODE_SESSION_ID": SESSION_A})
        )

    def loop(self, *args: str, session: str | None = None) -> tuple[int, str, str]:
        """`xt.py loop …` ở gốc repo tạm; `SystemExit` của argparse (lệnh con chưa có) → mã thoát, không làm vỡ ca."""
        env = {"CLAUDE_CODE_SESSION_ID": session} if session else {}
        with unittest.mock.patch.dict(os.environ, env), chdir(self.repo):
            try:
                return run_main("loop", *args)
            except SystemExit as e:
                return (e.code if isinstance(e.code, int) else 2), "", f"SystemExit {e.code}"

    def state(self) -> dict[str, Any]:
        data = json.loads((self.repo / ".autopilot" / "state.json").read_text(encoding="utf-8"))
        assert isinstance(data, dict)
        return data

    def verdict(self) -> dict[str, Any]:
        rc, out, err = self.loop("status", "--json")
        self.assertEqual(rc, 0, err)
        data = json.loads(out)
        assert isinstance(data, dict)
        return data

    def red(self, task: str = "T-001") -> None:
        self.assertNotEqual(self.loop("record", "--task", task, "--", "bash gate.sh")[0], 0)

    def same_signature(self) -> None:
        (self.repo / "style").write_text("same", encoding="utf-8")

    def seed_wait_and_failures(self) -> None:
        """Vòng một phiên, T-900 chờ người, T-001 đỏ hai lần cùng chữ ký (đếm lỗi = 2)."""
        self.assertEqual(self.loop("init", "--single-session")[0], 0)
        self.assertEqual(self.loop("defer", "--task", "T-900", "--reason", "chủ repo ký")[0], 0)
        self.same_signature()
        self.red()
        self.red()
        st = self.state()
        self.assertEqual(st["same_failure_count"], 2)
        self.assertEqual(st["session_id"], SESSION_A)

    @flow("FLOW-01")
    def test_flow_01_attach_keeps_deferred_and_failure_count(self) -> None:
        """Given vòng một phiên, deferred T-900, đếm lỗi 2 · When `loop attach` với session mới ·
        Then exit 0, deferred giữ T-900, đếm lỗi giữ 2, session_id mới. (Hiện chưa có `attach` → xfail.)"""
        self.seed_wait_and_failures()
        rc, _, err = self.loop("attach", session=SESSION_B)
        self.assertEqual(rc, 0, err)
        st = self.state()
        self.assertIn("T-900", st["deferred"])
        self.assertEqual(st["same_failure_count"], 2)
        self.assertEqual(st["session_id"], SESSION_B)

    @flow("FLOW-02")
    def test_flow_02_resolve_only_named_task_leaves_deferred(self) -> None:
        """Given như FLOW-01 thêm deferred T-901 · When `loop resolve --task T-900 --reason x` ·
        Then chỉ T-900 rời deferred, `resolved[]` có T-900, đếm lỗi giữ 2. (Hiện chưa có `resolve` → xfail.)"""
        self.seed_wait_and_failures()
        self.assertEqual(self.loop("defer", "--task", "T-901", "--reason", "chủ repo ký nữa")[0], 0)
        rc, _, err = self.loop("resolve", "--task", "T-900", "--reason", "x")
        self.assertEqual(rc, 0, err)
        st = self.state()
        self.assertNotIn("T-900", st["deferred"])
        self.assertIn("T-901", st["deferred"])
        self.assertIn("T-900", json.dumps(st["resolved"]))
        self.assertEqual(st["same_failure_count"], 2)

    @flow("FLOW-03")
    def test_flow_03_defer_refused_for_failing_task(self) -> None:
        """Given T-001 vừa đỏ một lần · When `loop defer --task T-001` · Then từ chối (exit ≠ 0), T-001 không vào
        deferred (`_defer_problem`: không né blocked). Chỉ kiểm `defer`; T-3541 mở rộng cho `resolve`."""
        self.assertEqual(self.loop("init")[0], 0)
        self.red()
        rc, _, err = self.loop("defer", "--task", "T-001", "--reason", "né")
        self.assertNotEqual(rc, 0)
        self.assertIn("task đang lỗi", err)
        self.assertNotIn("T-001", self.state().get("deferred", {}))

    @flow("FLOW-04")
    def test_flow_04_alternating_signatures_end_blocked(self) -> None:
        """Given Gate đỏ xen kẽ chữ ký A/B · When 6 × `loop record` · Then verdict `blocked`, lý do nêu 6 lần đỏ và
        2 chữ ký khác nhau. (Hiện `same_failure_count` về 1 mỗi lần đổi chữ ký → `continue` → xfail.)"""
        self.assertEqual(self.loop("init")[0], 0)
        for _ in range(6):
            self.red()
        v = self.verdict()
        self.assertEqual(v["verdict"], "blocked", v)
        self.assertRegex(v["reason"], r"6\D+lần đỏ")
        self.assertRegex(v["reason"], r"2\D+chữ ký")

    @flow("FLOW-05")
    def test_flow_05_same_signature_three_times_blocks(self) -> None:
        """Đối chứng R6: Gate đỏ cùng chữ ký A ×3 → `blocked` (hành vi hiện có, không đổi)."""
        self.assertEqual(self.loop("init")[0], 0)
        self.same_signature()
        for _ in range(3):
            self.red()
        v = self.verdict()
        self.assertEqual(v["verdict"], "blocked", v)
        self.assertIn("cùng một lỗi lặp 3 lần", v["reason"])
        self.assertTrue(re.search(r"T-001", v["reason"]))

    @flow("FLOW-06")
    def test_flow_06_green_resets_task_runs_and_loop_continues(self) -> None:
        """Given T-001 đỏ 5 lần (chữ ký luân phiên, không chạm max_same_failure) rồi xanh · Then `task_runs` có khoá và
        T-001 = 0 (hoặc vắng), verdict `continue`/`done`, không `blocked`. (Hiện state không có `task_runs` → xfail.)"""
        self.assertEqual(self.loop("init")[0], 0)
        for _ in range(5):
            self.red()
        (self.repo / "green").write_text("1", encoding="utf-8")
        self.assertEqual(self.loop("record", "--task", "T-001", "--", "bash gate.sh")[0], 0)
        st = self.state()
        self.assertIn("task_runs", st)
        self.assertEqual(st["task_runs"].get("T-001", 0), 0)
        self.assertIn(self.verdict()["verdict"], ("continue", "done"))


class FlowRegistryTest(unittest.TestCase):
    def test_strict_ids_exist(self) -> None:
        """`XT_FLOW_STRICT` và `XFAIL` chỉ được nêu ID có test mang nó — không để Gate xanh vì thiếu ca."""
        self.assertEqual(sorted(STRICT - FLOW_IDS), [], "XT_FLOW_STRICT nêu ID không có test")
        self.assertEqual(sorted(XFAIL.keys() - FLOW_IDS), [], "XFAIL nêu ID không có test")


if __name__ == "__main__":
    unittest.main()
