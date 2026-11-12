"""Dữ kiện an toàn trong đặc tả xưởng đầu-cuối không được quay lại dạng sai đã bị review #505 bắt (D-424).

Mỗi ca khoá một 🔴: câu sai có hại khi task cài đúng từng chữ của đặc tả (cùng cách với `tests/test_content_facts.py`).
Bắt theo ý — câu khẳng định sai không còn, và điều kiện thay thế có mặt — không theo nguyên một câu."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPECS = ROOT / "docs" / "specs"


def spec(name: str) -> str:
    return (SPECS / f"SPEC-factory-{name}.md").read_text(encoding="utf-8")


def section(text: str, heading: str) -> str:
    """Thân của mục có tiêu đề bắt đầu bằng `heading`, tới tiêu đề cùng cấp hoặc cao hơn kế tiếp."""
    level = len(heading) - len(heading.lstrip("#"))
    lines = text.splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith(heading))
    stop = re.compile(rf"^#{{1,{level}}} ")
    end = next((i for i in range(start + 1, len(lines)) if stop.match(lines[i])), len(lines))
    return "\n".join(lines[start:end])


class SpecFactoryFactsTest(unittest.TestCase):
    def test_tag_alone_is_not_the_release_property(self) -> None:
        """AUD-HAR-386: tag `v*` ai cũng tạo được (guard và ruleset hiện không chặn) — đặc tả không được coi tag là
        "chỉ workflow tạo"; thuộc tính bền là attestation của workflow phát hành, kiểm ở nơi dùng."""
        body = section(spec("scale"), "### 2.5 ")
        self.assertNotIn("luật sẵn có", body)
        self.assertNotRegex(body, r"[Tt]ag chỉ (do|tạo qua) workflow")
        self.assertIn("attestation", body)
        self.assertIn("release-verify", body)
        self.assertRegex(body, r"không kiểm được không tính là đạt")
        upgrade = section(spec("learning"), "### 2.3 ")
        self.assertIn("release-verify", upgrade)
        self.assertNotRegex(upgrade, r"tag chỉ do workflow")

    def test_rollback_to_production_needs_merged_head(self) -> None:
        """AUD-SEC-638: `deploy rollback` ở môi trường khác `dev` chạy lệnh `rollback_<env>` của cây hiện tại — điều kiện
        "HEAD nằm trong nhánh chính của remote" phải áp cho cả `run` lẫn `rollback`, không riêng `run`."""
        deploy = spec("deploy")
        steps = section(deploy, "### 2.3 ")
        rights = next(p for p in steps.split("\n") if p.startswith("2. **Quyền**"))
        index = steps.index(rights)
        block = steps[index : steps.index("\n3. ", index)]
        common, _, run_only = block.partition("Với `run` thêm")
        self.assertIn("cả `run` lẫn `rollback`", common)
        self.assertIn("nhánh chính của remote", common)
        self.assertNotIn("nhánh chính của remote", run_only)
        scenario = section(deploy, "### S-119 ")
        self.assertIn("deploy rollback --env prod", scenario)
        self.assertIn("exit 2", scenario)

    def test_stale_claim_is_never_taken_over_automatically(self) -> None:
        """AUD-HAR-387: tiếp quản tự động không có đồng hồ, không có bước nhận, không giữ trần chi phí — nhánh quá hạn
        chỉ được báo; giao lại là lệnh có D-NNN của phiên điều phối, chi phí cộng dồn đi theo nhánh."""
        worker = section(spec("parallel"), "### 2.3 ")
        self.assertIn("Không tự tiếp quản", worker)
        self.assertIn("worker reassign", worker)
        self.assertRegex(worker, r"--decision D-NNN")
        self.assertRegex(worker, r"giao lại không cấp trần mới")
        self.assertNotRegex(worker, r"được tiếp tục \*\*trên chính nhánh đó\*\* bằng đẩy fast-forward")
        scenario = section(spec("parallel"), "### S-411 ")
        self.assertRegex(scenario, r"\*\*không\*\* được trả về")


if __name__ == "__main__":
    unittest.main()
