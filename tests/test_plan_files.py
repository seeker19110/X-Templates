"""PLAN thật của repo đọc được bằng máy: task còn mở không có ghi chú `sau:`/`files:` hỏng (review #394 🔴).

Ngoặc lẻ trong mô tả task (vd `` `system(` ``) nuốt nhóm `(sau: …)` → task không `ready`, cả chuỗi phụ thuộc bị chặn."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import xt


class RepoPlanFilesTest(unittest.TestCase):
    def test_archived_plans_are_closed(self) -> None:
        """ADR-0070 (D-349): kho chỉ giữ PLAN đã đóng — PLAN còn task mở phải ở `docs/autopilot/`."""
        archived = sorted((ROOT / xt.PLAN_ARCHIVE_DIR).glob("PLAN*.md"))
        self.assertTrue(archived)
        for plan in archived:
            with self.subTest(plan=plan.name):
                self.assertEqual([t["id"] for t in xt.parse_plan(plan) if t["state"] == " "], [])

    def test_task_ids_never_reused_across_archive(self) -> None:
        """Bộ cấp số task quét cả kho (ADR-0070): số lớn nhất ≥ mọi `T-NNNN` của PLAN đã dời."""
        top = xt._max_task_number(ROOT, {})
        for plan in sorted((ROOT / xt.PLAN_ARCHIVE_DIR).glob("PLAN*.md")):
            for t in xt.parse_plan(plan):
                with self.subTest(task=t["id"]):
                    self.assertGreaterEqual(top, int(t["id"][2:]))

    def test_open_tasks_have_readable_links(self) -> None:
        plans = sorted((ROOT / "docs" / "autopilot").glob("PLAN*.md"))
        self.assertTrue(plans)
        for plan in plans:
            open_tasks = [t for t in xt.parse_plan(plan) if t["state"] == " "]
            with self.subTest(plan=plan.name):
                self.assertEqual(xt.plan_bad_links(open_tasks), {})


if __name__ == "__main__":
    unittest.main()
