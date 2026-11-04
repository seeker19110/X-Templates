"""Dữ kiện an toàn trong nội dung khung không được quay lại dạng sai đã bị review bắt (PR #436, D-341).

Mỗi ca khoá một 🔴: câu sai có hại khi dự án làm đúng từng chữ (nguồn ghi ở mục)."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ITEM_RE = re.compile(r"^- \[[ x~]\] `([A-Z0-9-]+)` ")


def item(rel: str, item_id: str) -> str:
    for line in (ROOT / "framework" / rel).read_text(encoding="utf-8").splitlines():
        m = ITEM_RE.match(line)
        if m and m[1] == item_id:
            return line
    raise AssertionError(f"không thấy {item_id} trong {rel}")


class ContentFactsTest(unittest.TestCase):
    def test_torch_load_needs_patched_version(self):
        """CVE-2025-32434: `torch.load(weights_only=True)` ở torch ≤ 2.5.1 vẫn RCE — chỉ `weights_only=True` là chưa đủ."""
        data = item("02-profiles/data-ml.md", "PRF-DATA-013")
        self.assertIn("2.6.0", data)
        self.assertIn("weights_only=False", data)
        supply = item("12-security/supply-chain.md", "SEC-SUPPLY-032")
        self.assertNotRegex(supply, r"weights_only=True`? hoặc torch")

    def test_no_consumer_oauth_token_in_products(self):
        """Điều khoản Anthropic: token OAuth thuê bao không dùng trong sản phẩm bên thứ ba — không có lối 'bật sau cờ'."""
        line = item("13-ai-engineering/llm-app-foundations.md", "AI-APP-021")
        self.assertNotIn("tắt mặc định", line)
        self.assertNotIn("dùng cá nhân thì", line)
        self.assertIn("legal-and-compliance", line)  # nguồn ngay trên dòng mục, không lấy từ chỗ khác của file

    def test_infra_failure_keeps_denominator(self):
        """Loại ca lỗi hạ tầng khỏi cả tử lẫn mẫu số làm pass rate tăng giả khi đổi model (SWE-bench giữ mẫu số).
        Bắt theo ý, không theo một câu: mọi mệnh đề nhắc `infra_failure` + loại/không tính + mẫu số mà không có
        điều kiện "xác nhận" đều sai."""
        line = item("13-ai-engineering/evaluation.md", "AI-EVAL-022")
        self.assertIn("vẫn nằm trong mẫu số", line)
        for clause in re.split(r"[;.]", line):
            flat = clause.replace("`", "")
            if re.search(r"(loại|ra|bỏ|trừ)( [^,;]{0,30})? khỏi[^,;]{0,25}mẫu số", flat) or re.search(
                r"không (được )?tính( [^,;]{0,30})? vào[^,;]{0,25}mẫu số", flat
            ):
                self.assertRegex(clause, r"xác nhận", clause)


if __name__ == "__main__":
    unittest.main()
