"""Dữ kiện an toàn trong nội dung khung không được quay lại dạng sai đã bị review bắt (PR #436, D-341).

Mỗi ca khoá một 🔴: câu sai có hại khi dự án làm đúng từng chữ (nguồn ghi ở mục)."""

from __future__ import annotations

import re
import subprocess
import unicodedata
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ITEM_RE = re.compile(r"^- \[[ x~]\] `([A-Z0-9-]+)` ")
# Nội dung agent đọc như chỉ thị (khung, harness, công cụ, tài liệu) — tests/ ngoài phạm vi: payload thử guard cố ý chứa
# ký tự vô hình. Ví dụ trong tài liệu viết bằng ký hiệu (`می` + U+200C + `خواهم`), không dán ký tự thật.
INVISIBLE_SPECS = ("framework", ".claude", "scripts", "docs", "README.md", "AGENTS.md", "CLAUDE.md", "CHANGELOG*.md")


def invisible(ch: str) -> bool:
    """Ký tự định dạng vô hình (Cf: zero-width, bidi, U+FEFF, U+180E, khối Tag…) và variation selector ngoài
    U+FE0E/U+FE0F (selector trình bày emoji): U+FE00–U+FE0D, U+E0100–U+E01EF — kênh giấu dữ liệu (`AI-GUARD-018`)."""
    cp = ord(ch)
    return unicodedata.category(ch) == "Cf" or 0xFE00 <= cp <= 0xFE0D or 0xE0100 <= cp <= 0xE01EF


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

    def test_no_invisible_format_chars(self):
        """Ký tự vô hình THẬT trong file agent đọc là bề mặt tiêm lệnh ẩn và làm đỏ cổng cấm ký tự vô hình của dự án
        đích khi cài khung (3.30.0: ZWNJ trong ví dụ `AI-GUARD-018`; BOM trong mã nguồn `scripts/xt.py`)."""
        out = subprocess.run(
            ["git", "-C", str(ROOT), "ls-files", "-z", "--", *INVISIBLE_SPECS], capture_output=True, check=True
        )
        rels = [r for r in out.stdout.decode("utf-8").split("\0") if r]
        self.assertTrue(any(r.startswith("framework/") for r in rels), rels[:5])
        found = []
        for rel in rels:
            try:
                text = (ROOT / rel).read_text(encoding="utf-8")
            except (UnicodeDecodeError, FileNotFoundError):  # nhị phân; file đã xoá chưa commit
                continue
            for no, line in enumerate(text.splitlines(), 1):
                found += [f"{rel}:{no}: U+{ord(ch):04X}" for ch in line if invisible(ch)]
        self.assertEqual(found, [])

    def test_invisible_predicate(self):
        for ch in ("​", "‌", "‍", "‎", "‮", "⁦", "⁠", "﻿", "᠎", "­"):
            self.assertTrue(invisible(ch), hex(ord(ch)))
        for ch in ("\U000e0041", "\U000e0100", "︀"):
            self.assertTrue(invisible(ch), hex(ord(ch)))
        for ch in ("a", "ữ", "️", "︎", "👩", "م", " ", "\t"):
            self.assertFalse(invisible(ch), hex(ord(ch)))


if __name__ == "__main__":
    unittest.main()
