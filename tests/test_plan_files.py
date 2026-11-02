"""PLAN thật của repo đọc được bằng máy: task còn mở không có ghi chú `sau:`/`files:` hỏng (review #394 🔴).

Ngoặc lẻ trong mô tả task (vd `` `system(` ``) nuốt nhóm `(sau: …)` → task không `ready`, cả chuỗi phụ thuộc bị chặn."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import xt  # noqa: E402


class RepoPlanFilesTest(unittest.TestCase):
    def test_open_tasks_have_readable_links(self) -> None:
        plans = sorted((ROOT / "docs" / "autopilot").glob("PLAN*.md"))
        self.assertTrue(plans)
        for plan in plans:
            open_tasks = [t for t in xt.parse_plan(plan) if t["state"] == " "]
            with self.subTest(plan=plan.name):
                self.assertEqual(xt.plan_bad_links(open_tasks), {})


if __name__ == "__main__":
    unittest.main()
