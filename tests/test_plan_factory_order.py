"""PLAN-factory-e2e: cơ chế bù đứng trước phần nới (ADR-0075 §Quyết định 6; hồi quy AUD-HAR-380, review #502).

Phần nới (agent ký ở M/L, agent duyệt giai đoạn 2/3) chỉ được làm sau khi các cơ chế bù đã đóng: hàng `deploy` của
`release-check`, bộ nghiệm thu khoá, chữ ký chặn phân phối. `loop record` từ chối task còn `sau:` mở, nên thứ tự này
phải nằm trong `sau:` của PLAN chứ không chỉ trong lời văn."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict, List, Set

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import xt

PLAN_NAME = "PLAN-factory-e2e.md"
PLAN_DIRS = ("docs/autopilot", "docs/archive/autopilot")  # PLAN đóng được dời vào kho (ADR-0070)
COMPENSATING = {"T-3743", "T-3748", "T-3758"}  # hàng deploy · bộ nghiệm thu khoá · chữ ký chặn phân phối
LOOSENING = ("T-3755", "T-3756")  # release-sign ở M/L · duyệt giai đoạn 2/3


def closure(tasks: List[Dict[str, Any]], task: str) -> Set[str]:
    """Mọi task mà `task` phải chờ, tính bắc cầu qua `sau:`."""
    after = {t["id"]: list(t["after"]) for t in tasks}
    seen: Set[str] = set()
    todo = list(after.get(task, []))
    while todo:
        cur = todo.pop()
        if cur not in seen:
            seen.add(cur)
            todo.extend(after.get(cur, []))
    return seen


def missing_compensation(tasks: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """Phần nới → cơ chế bù nó chưa chờ (rỗng = PLAN đúng thứ tự)."""
    gaps = {t: sorted(COMPENSATING - closure(tasks, t)) for t in LOOSENING}
    return {t: need for t, need in gaps.items() if need}


def parse(text: str) -> List[Dict[str, Any]]:
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "PLAN.md"
        path.write_text(text, encoding="utf-8")
        return xt.parse_plan(path)


OLD_ORDER = """
### Lát 5
- [ ] `T-3743` hàng deploy — Gate: `true`
- [ ] `T-3748` nghiệm thu khoá — Gate: `true`
- [ ] `T-3755` release-sign ở M/L (sau: T-3743, T-3748) — Gate: `true`
- [ ] `T-3756` duyệt giai đoạn 2/3 (sau: T-3748) — Gate: `true`
- [ ] `T-3758` chữ ký chặn phân phối (sau: T-3755) — Gate: `true`
"""


class PlanFactoryOrderTest(unittest.TestCase):
    def test_plan_keeps_compensating_controls_before_loosening(self) -> None:
        found = [ROOT / d / PLAN_NAME for d in PLAN_DIRS if (ROOT / d / PLAN_NAME).is_file()]
        self.assertEqual(len(found), 1, f"{PLAN_NAME} phải có ở đúng một trong {PLAN_DIRS}")
        tasks = xt.parse_plan(found[0])
        ids = {t["id"] for t in tasks}
        self.assertLessEqual(
            COMPENSATING | set(LOOSENING), ids, "task của bất biến phải còn trong PLAN (ID không tái sử dụng)"
        )
        self.assertEqual(missing_compensation(tasks), {})

    def test_detects_order_found_by_review_502(self) -> None:
        self.assertEqual(
            missing_compensation(parse(OLD_ORDER)),
            {"T-3755": ["T-3758"], "T-3756": ["T-3743", "T-3758"]},
        )

    def test_transitive_dependency_counts(self) -> None:
        text = OLD_ORDER.replace("(sau: T-3755)", "").replace("(sau: T-3748) —", "(sau: T-3755) —")
        text = text.replace("(sau: T-3743, T-3748)", "(sau: T-3743, T-3748, T-3758)")
        self.assertEqual(missing_compensation(parse(text)), {})


if __name__ == "__main__":
    unittest.main()
