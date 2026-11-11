"""AUD-SEC-497 (D-390): agent không tự ghi dòng ký §5 của `GO-NO-GO*.md` — mẫu ghi "con người, không phải agent", chữ ký
là đầu vào của `release-check` `promotion: approved` (ADR-0068 §Quyết định 3a). Nợ review #464: liên kết cứng
(AUD-SEC-533), diff từ tệp/stdin (AUD-SEC-534), lệnh ngoài danh sách trắng/đổi tên theo biểu thức (AUD-SEC-535), MCP ghi
file (AUD-SEC-536), lý do/touch (AUD-SEC-537). Payload giả như hook PreToolUse."""

from __future__ import annotations

import os
import random
import shutil
import sys
import tempfile
import unittest
import unittest.mock as mock
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / ".claude" / "hooks"))
sys.path.insert(0, str(ROOT / "scripts"))
import guard
import xt

HEAD = "---\ntitle: GO-NO-GO v9.9.9\n---\n\n# GO-NO-GO v9.9.9\n\n## 1. Phạm vi\n\nBản vá.\n\n"
SIGN_HEAD = "## 5. Ký (con người, không phải agent)\n\n| Vai trò | Tên | Quyết định | Ngày |\n|---|---|---|---|\n"
TEMPLATE_ROW = "| Chủ repo | | GO / NO-GO | |\n"
SIGNED_ROW = "| Chủ repo | An | GO | 2026-11-07 |\n"
TAIL = "\n## 6. Sau phát hành\n\n| Việc | Người | Kết quả | 2026-11-08 |\n"
TEMPLATE = HEAD + SIGN_HEAD + TEMPLATE_ROW + TAIL
SIGNED = HEAD + SIGN_HEAD + SIGNED_ROW + TAIL
GO_REL = "docs/ops/GO-NO-GO-x.md"


class GoNoGoGuardBase(unittest.TestCase):
    def setUp(self) -> None:
        env = mock.patch.dict(os.environ, {"XT_GUARD_POLICY": "", "XT_GUARD_PHASE": ""})
        env.start()
        self.addCleanup(env.stop)
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, True)
        (self.root / "docs" / "ops").mkdir(parents=True)

    def put(self, rel: str, text: str) -> Path:
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        return p

    def edit(self, rel: str, tool_input: Dict[str, object]) -> Tuple[str, str, str]:
        payload = {"tool_input": {**tool_input, "file_path": str(self.root / rel)}}
        out = guard.apply_policy(guard._rule_decision("edit", payload, str(self.root)))
        return str(out["decision"]), str(out.get("code")), str(out.get("reason", ""))

    def bash(self, cmd: str, cwd: Optional[str] = None) -> Tuple[str, str]:
        payload = {"tool_input": {"command": cmd}, "cwd": cwd or str(self.root)}
        out = guard.apply_policy(guard._rule_decision("bash", payload, str(self.root)))
        return str(out["decision"]), str(out.get("code"))

    def mcp(self, name: str, tool_input: Dict[str, object]) -> Tuple[str, str, str]:
        payload = {"tool_name": name, "tool_input": tool_input}
        out = guard.apply_policy(guard._rule_decision("mcp", payload, str(self.root)))
        return str(out["decision"]), str(out.get("code")), str(out.get("reason", ""))

    def assert_sign_denied(self, got: Tuple[str, str, str]) -> None:
        self.assertEqual(got[:2], ("deny", "GO_SIGN"), got)
        for part in ("ADR-0068 §Quyết định 3a", "mẫu GO-NO-GO §5", "AUD-SEC-497", "chữ ký §5 là của người"):
            self.assertIn(part, got[2])

    def assert_edit_denied(self, got: Tuple[str, str, str]) -> None:
        """D-418: mọi Edit/MultiEdit/NotebookEdit lên GO-NO-GO bị chặn, câu lý do chỉ lối Write cả file/`release-sign`."""
        self.assert_sign_denied(got)
        for part in ("Write", "release-sign", "D-418"):
            self.assertIn(part, got[2])

    def write(self, rel: str, text: str) -> str:
        return self.edit(rel, {"content": text})[0]


class GoNoGoEditTest(GoNoGoGuardBase):
    """Write: so tập dòng ký §5 trước và sau; Edit/MultiEdit/NotebookEdit: luôn chặn (D-418)."""

    def test_any_edit_denied_d418(self) -> None:
        """Review lượt 3 (A1/A1b/A1c/H1/A3/A3b/A2/A4/Q1): mô hình tool Edit lệch tool thật — guard thôi mô hình hoá."""
        trow = TEMPLATE_ROW
        b1 = TEMPLATE_S.replace(trow, "| Chủ repo | An | GO |Z\n 2026-11-10 |\n")
        old2 = trow.rstrip("\n").replace("ủ", "\\u1ee7")
        h1 = HEAD + SIGN_HEAD + trow + "Ghi chú Z\n## 6. Sau phát hành\n\n" + SIGNED_ROW
        signed_q = SIGNED_S.replace(SUBJ, SUBJ + "‘ghi chú’\n")
        cases = [
            ("A1", b1, {"old_string": "Z", "new_string": ""}),
            ("A1b", b1.replace("\n", "\r\n"), {"old_string": "Z", "new_string": ""}),
            ("A1c", b1, {"edits": [{"old_string": "Z", "new_string": ""}]}),
            ("H1", h1, {"old_string": "Z", "new_string": ""}),
            ("A3", TEMPLATE_S.replace("Bản vá.", "x\ry"), {"old_string": "x\ny", "new_string": SIGNED_ROW}),
            ("A3b", TEMPLATE_S.replace(trow, "| Chủ repo | An | GO |\r\r\n 2026-11-10 |\n"), {"old_string": "\r\n"}),
            ("A2", TEMPLATE_S, {"old_string": old2, "new_string": "\\u007c Ch\\u1ee7 repo \\u007c An \\u007c GO |"}),
            ("A4", TEMPLATE_S, {"old_string": old2, "new_string": "| Chủ repo | | GO | 2026-11-10 |"}),
            ("Q1", signed_q, {"old_string": "a" * 8 + "`\n'ghi chú'", "new_string": "d" * 8 + "`\n'ghi chú'"}),
            ("benign", TEMPLATE_S, {"old_string": "Bản vá.", "new_string": "Bản vá 2."}),
            ("notebook", TEMPLATE_S, {"notebook_path": "", "new_source": "x"}),
        ]
        for name, disk, tool_input in cases:
            with self.subTest(name):
                self.put(GO_REL, disk)
                self.assert_edit_denied(self.edit(GO_REL, tool_input))
        self.assert_edit_denied(self.edit("docs/ops/GO-NO-GO-none.md", {"old_string": "", "new_string": "x"}))

    def test_edit_adds_sign_row_denied(self) -> None:
        self.put(GO_REL, TEMPLATE)
        self.assert_sign_denied(self.edit(GO_REL, {"old_string": TEMPLATE_ROW, "new_string": SIGNED_ROW}))

    def test_edit_appends_second_sign_row_denied(self) -> None:
        self.put(GO_REL, SIGNED)
        new = SIGNED_ROW + "| QA | Bình | GO | 2026-11-07 |\n"
        self.assert_sign_denied(self.edit(GO_REL, {"old_string": SIGNED_ROW, "new_string": new}))

    def test_edit_changes_existing_sign_row_denied(self) -> None:
        self.put(GO_REL, SIGNED)
        changed = SIGNED_ROW.replace("2026-11-07", "2026-11-08")
        self.assert_sign_denied(self.edit(GO_REL, {"old_string": SIGNED_ROW, "new_string": changed}))
        flipped = SIGNED_ROW.replace("| GO |", "| NO-GO |")
        self.assert_sign_denied(self.edit(GO_REL, {"old_string": SIGNED_ROW, "new_string": flipped}))

    def test_write_new_file_signed_denied(self) -> None:
        self.assert_sign_denied(self.edit("docs/ops/GO-NO-GO-new.md", {"content": SIGNED}))

    def test_write_keeps_existing_sign_row_allowed(self) -> None:
        self.put(GO_REL, SIGNED)
        got = self.edit(GO_REL, {"content": SIGNED.replace("Bản vá.", "Bản vá, thêm ghi chú.")})
        self.assertEqual(got[0], "", got)

    def test_write_section_one_allowed(self) -> None:
        for text in (TEMPLATE, SIGNED, TEMPLATE.replace("\n", "\r\n")):
            self.put(GO_REL, text)
            self.assertEqual(self.write(GO_REL, text.replace("Bản vá.", "Bản vá installer.")), "")

    def test_write_template_table_blank_allowed(self) -> None:
        self.put(GO_REL, TEMPLATE)
        self.assertEqual(self.write(GO_REL, TEMPLATE.replace(TEMPLATE_ROW, "| Chủ dự án | | GO / NO-GO | |\n")), "")
        self.assertEqual(self.write("docs/ops/GO-NO-GO-y.md", TEMPLATE), "")

    def test_write_from_real_template_allowed(self) -> None:
        """Lối đúng (D-418): tạo GO-NO-GO từ mẫu thật, điền phần máy, thêm dòng §6 — Write cả file cho qua (LF, CRLF)."""
        tpl = (ROOT / "framework" / "templates" / "GO-NO-GO.md").read_text(encoding="utf-8")
        self.assertFalse(xt._go_sign_rows(tpl))
        for eol in ("\n", "\r\n"):
            with self.subTest(eol=eol):
                text = tpl.replace("\n", eol)
                self.assertEqual(self.write("docs/ops/GO-NO-GO-new.md", text), "")
                self.put("docs/ops/GO-NO-GO-new.md", text)
                filled = text + eol + "## 7. Ghi chú máy" + eol + eol + "subject: content `" + "a" * 64 + "`" + eol
                self.assertEqual(self.write("docs/ops/GO-NO-GO-new.md", filled), "")

    def test_remove_sign_row_allowed(self) -> None:
        self.put(GO_REL, SIGNED)
        self.assertEqual(self.write(GO_REL, TEMPLATE), "")

    def test_repadding_sign_row_allowed(self) -> None:
        self.put(GO_REL, SIGNED)
        self.assertEqual(self.write(GO_REL, SIGNED.replace(SIGNED_ROW, "|  Chủ repo  |An|  GO |2026-11-07|\n")), "")

    def test_row_outside_section_five_allowed(self) -> None:
        self.put(GO_REL, TEMPLATE)
        self.assertEqual(self.write(GO_REL, TEMPLATE.replace("Bản vá.", "| Rủi ro | An | thấp | 2026-11-07 |")), "")
        self.assertEqual(self.write(GO_REL, TEMPLATE + SIGNED_ROW), "")  # dòng §6

    def test_other_file_name_allowed(self) -> None:
        self.assertEqual(self.edit("NOTES.md", {"content": SIGNED})[0], "")
        self.assertEqual(self.edit("docs/ops/GO-NO-GO-x.txt", {"content": SIGNED})[0], "")

    def test_name_case_insensitive_and_any_dir(self) -> None:
        self.assert_sign_denied(self.edit("go-no-go-v1.MD", {"content": SIGNED}))
        self.assert_sign_denied(self.edit("pkg/a/GO-NO-GO.md", {"content": SIGNED}))

    def test_symlink_to_go_no_go_denied(self) -> None:
        target = self.put(GO_REL, TEMPLATE)
        os.symlink(target, self.root / "notes.md")
        self.assert_sign_denied(self.edit("notes.md", {"content": SIGNED}))

    def test_multiedit_applied_in_order(self) -> None:
        self.put(GO_REL, TEMPLATE)
        edits = [
            {"old_string": "| Chủ repo | |", "new_string": "| Chủ repo | An |"},
            {"old_string": "| GO / NO-GO | |", "new_string": "| GO | 2026-11-07 |"},
        ]
        self.assert_edit_denied(self.edit(GO_REL, {"edits": edits}))
        ok = [{"old_string": "Bản vá.", "new_string": "Bản vá 2."}, "rác"]
        self.assert_edit_denied(self.edit(GO_REL, {"edits": ok}))

    def test_write_row_before_section_five_allowed(self) -> None:
        text = HEAD + TEMPLATE_ROW + SIGN_HEAD + TEMPLATE_ROW + TAIL  # dòng mẫu ở §1 đứng trước §5
        self.put(GO_REL, text)
        self.assertEqual(self.write(GO_REL, text.replace(TEMPLATE_ROW, SIGNED_ROW, 1)), "")  # chỉ §1 đổi
        self.assert_sign_denied(self.edit(GO_REL, {"content": text.replace(TEMPLATE_ROW, SIGNED_ROW)}))

    def test_unreadable_or_non_utf8_disk_denied(self) -> None:
        """Đĩa không đọc chắc (lỗi đọc, không phải UTF-8, không phải file thường) → deny; file chưa có → so với rỗng."""
        self.assertEqual(self.write("docs/ops/GO-NO-GO-none.md", TEMPLATE), "")
        self.put(GO_REL, TEMPLATE)
        with mock.patch.object(guard, "open", create=True, side_effect=PermissionError("x")):
            self.assertIsNone(guard._go_read(str(self.root / GO_REL)))
            got = self.edit(GO_REL, {"content": TEMPLATE})
            self.assert_sign_denied(got)
            self.assertIn("không đọc", got[2])
        (self.root / GO_REL).write_bytes(TEMPLATE.encode("utf-8") + b"\xff\xfe")
        self.assertIsNotNone(guard._go_read(str(self.root / GO_REL)))  # bộ đọc diff vẫn thay ký tự lỗi
        self.assert_sign_denied(self.edit(GO_REL, {"content": TEMPLATE}))

    def test_not_a_regular_file(self) -> None:
        d = self.root / "docs" / "GO-NO-GO-dir.md"
        d.mkdir()
        self.assertIsNone(guard._go_read(str(d)))
        self.assert_sign_denied(self.edit("docs/GO-NO-GO-dir.md", {"content": SIGNED}))

    def test_notebook_edit_new_source(self) -> None:
        got = self.edit("GO-NO-GO.md", {"notebook_path": "", "new_source": SIGNED_ROW})
        self.assert_sign_denied(got)
        payload = {"tool_input": {"notebook_path": str(self.root / "GO-NO-GO.md"), "new_source": "x"}}
        self.assertEqual(guard._rule_decision("edit", payload, str(self.root))["decision"], "deny")  # D-418

    def test_no_tool_input(self) -> None:
        self.assertEqual(guard.edit_decision(str(self.root / GO_REL), str(self.root)), ("", ""))

    def test_crlf_rows(self) -> None:
        self.put(GO_REL, TEMPLATE.replace("\n", "\r\n"))
        got = self.edit(GO_REL, {"content": SIGNED.replace("\n", "\r\n")})
        self.assert_sign_denied(got)

    def test_rows_cover_xt_release_check(self) -> None:
        """AUD-SEC-615/AUD-TEST-100: mọi dòng `xt._go_sign_rows` (nguồn của `release-check`) tính là chữ ký thì guard
        thấy — một chiều (guard chặt hơn), cả khi có chú thích HTML/khối rào; văn bản thường thì bằng nhau."""
        self.assertEqual(guard.GO_SIGN_ROW_RE.pattern, xt.GO_SIGN_ROW_RE.pattern)
        for text in (TEMPLATE, SIGNED, SIGNED + SIGNED_ROW, HEAD, SIGN_HEAD + "| a | b | c | 2026-01-01 |\n"):
            mine = sorted((r[2], r[3]) for r in guard._go_sign_rows(text))
            self.assertEqual(mine, sorted(set(xt._go_sign_rows(text))), text)
        corpus = [old.replace(row, new) for old, row, new in LURES] + [
            SIGN_HEAD + "| Chủ repo | An `<!--` | GO | 2026-11-07 | <!-- a <!-- b `c` -->\n",  # code span; mở lồng
            SIGN_HEAD
            + "<!-->| Chủ repo | An | GO | 2026-11-07 |<!-- x --!>\n` <!-- a --> b\n",  # chú thích trọn, `--!>`
            HEAD + "```\n<!--\n```\n" + SIGN_HEAD + "a --> b\n" + SIGNED_ROW.replace(" |\n", " | <!-- x -->\n"),
            HEAD + "<!-- x\n-->## 5. Ký\n" + SIGNED_ROW + "<!-- chưa đóng\n",  # `## 5` sau đuôi chú thích
            SIGN_HEAD + SIGNED_ROW.replace("\n", "\r\n"),  # CRLF: `\r` cuối dòng vẫn là khoảng trắng một dòng
        ]
        for text in corpus:
            xt_rows = set(xt._go_sign_rows(text))
            self.assertTrue(xt_rows, text)
            self.assertLessEqual(xt_rows, {(r[2], r[3]) for r in guard._go_sign_rows(text)}, text)
        self.assertEqual(guard._go_sign_rows("<!-- x -->\n" + SIGNED_ROW), set())  # không có §5: như xt


# AUD-SEC-615: (file chưa ký, dòng mẫu, dòng ký) — `## 5` mồi trong chú thích HTML/khối rào/khối HTML ẩn trước §5 thật,
# `## x`/`## 5` trong khối rào giữa §5, dòng ký có chú thích HTML ở đuôi/đầu, BOM: xt (`_markdown_shown`) thấy dòng ký,
# luật thô cũ không. Bốn ca cuối giết đột biến của review lượt 1 (M2 bỏ view F, M3 bỏ view T, M4 lấy `## 5` muộn nhất,
# M8 thu hẹp dấu mở khối ẩn).
LURE_ROW = SIGNED_ROW.replace(" |\n", " | <!-- x -->\n")
LURES = [
    (HEAD + "<!--\n## 5. mồi\n-->\n\n" + SIGN_HEAD + TEMPLATE_ROW, TEMPLATE_ROW, SIGNED_ROW),
    (HEAD + "```\n## 5. mồi\n```\n\n" + SIGN_HEAD + TEMPLATE_ROW, TEMPLATE_ROW, SIGNED_ROW),
    (HEAD + SIGN_HEAD.replace("\n\n|", "\n\n```\n## x\n```\n\n|", 1) + TEMPLATE_ROW, TEMPLATE_ROW, SIGNED_ROW),
    (HEAD + SIGN_HEAD + TEMPLATE_ROW, TEMPLATE_ROW, LURE_ROW),
    (chr(0xFEFF) + SIGN_HEAD + TEMPLATE_ROW, TEMPLATE_ROW, SIGNED_ROW),  # BOM trước tiêu đề §5
    (HEAD + "```\n<!--\n```\n\n" + SIGN_HEAD + TEMPLATE_ROW, TEMPLATE_ROW, LURE_ROW),  # M2
    (HEAD + SIGN_HEAD + "` --> ` <!-- `\n" + TEMPLATE_ROW, TEMPLATE_ROW, "x -->" + SIGNED_ROW),  # M3
    (HEAD + SIGN_HEAD + TEMPLATE_ROW + "\n```\n## 5. ví dụ\n```\n", TEMPLATE_ROW, SIGNED_ROW),  # M4
    *(
        (HEAD + lure + SIGN_HEAD + TEMPLATE_ROW, TEMPLATE_ROW, SIGNED_ROW)  # M8
        for lure in ("~~~\n## 5. mồi\n~~~\n\n", "<script>\n## 5. mồi\n</script>\n\n", "<?x\n## 5. mồi\n?>\n\n")
    ),
]
# AUD-SEC-615 (review lượt 2, 🔴1): dòng ký NHIỀU DÒNG — `_markdown_shown` xoá hẳn dòng ẩn ở giữa (khối code thụt, rào,
# `<?…?>`, `<!X`, `<script>`, rào trong trích dẫn) hay chú thích cắt đôi dòng. Dòng ký chỉ là MỘT dòng: xt không tính.
MULTI_ROWS = {
    "V1": ("", "| Chủ repo | An | GO |\n    x\n2026-11-07 |\n"),
    "V1b": ("", "| Chủ repo |\n    x\nAn | GO | 2026-11-07 |\n"),
    "V1c": ("", "| Chủ repo | An | GO | 2026-11-07\n    x\n|\n"),
    "V2": ("", "| Chủ repo | An | GO |\n```\nx\n```\n2026-11-07 |\n"),
    "V3": ("", "| Chủ repo | An | GO |\n<?x?>\n2026-11-07 |\n"),
    "V4": ("", "| Chủ repo | An | GO |\n<!DOCTYPE\nfoo\n>\n2026-11-07 |\n"),
    "V5": ("", "| Chủ repo | An | GO |\n<script>\nx\n</script>\n2026-11-07 |\n"),
    "V14": ("", "| Chủ repo | An | GO |\n> ```\n> x\n> ```\n2026-11-07 |\n"),
    "V6": ("```\n<!--\n```\n\n", "| Chủ repo | An | GO | <!--\nx --> 2026-11-07 |\n"),
    "V6c": ("    <!--\n\n", "| Chủ repo | An | GO | <!--\nx --> 2026-11-07 |\n"),
    "comment": ("", "| Chủ repo | An | GO |\n<!-- x\n` -->\n2026-11-07 |\n"),
}


class GoNoGoHiddenLureTest(GoNoGoGuardBase):
    """AUD-SEC-615: guard tách §5 không được hẹp hơn `release-check` — mồi chú thích/khối rào không lách GO_SIGN."""

    def test_lures_denied_write_edit_mcp(self) -> None:
        for base, old, new in LURES:
            with self.subTest(base=base, new=new):
                signed = base.replace(old, new)
                self.assertTrue(xt._go_sign_rows(signed))  # release-check tính là đã ký
                self.put(GO_REL, base)
                self.assert_sign_denied(self.edit(GO_REL, {"content": signed}))
                self.assert_sign_denied(self.edit(GO_REL, {"old_string": old, "new_string": new}))
                got = self.mcp("mcp__github__create_or_update_file", {"path": GO_REL, "content": signed, "branch": "x"})
                self.assertEqual(got[:2], ("deny", "GO_SIGN"), got)
                self.assertIn("An", self.edit(GO_REL, {"content": signed})[2])

    def test_multi_line_row_not_a_signature(self) -> None:
        """🔴1: xt không còn ghép hai dòng thô thành dòng ký; guard và xt cùng thấy rỗng — release-check không duyệt."""
        self.assertNotIn(r"\s*", xt.GO_SIGN_ROW_RE.pattern)
        for name, (prefix, rows) in MULTI_ROWS.items():
            with self.subTest(name):
                signed = ANCHORED + prefix + SIGN_HEAD + rows
                self.assertEqual(xt._go_sign_rows(signed), [])
                self.assertEqual(xt._go_signers(signed), [])
                self.assertFalse(xt._go_no_go_signed(signed))
                self.assertEqual(guard._go_sign_rows(signed), set())
                self.put(GO_REL, SIGNED_S)  # chuỗi D-392: đổi dòng ký thành nhiều dòng rồi đổi `subject:`
                self.assertEqual(self.write(GO_REL, SIGNED_S.replace(SIGNED_ROW, rows)), "")  # xoá ký
                self.assertEqual(xt._go_sign_rows(SIGNED_S.replace(SIGNED_ROW, rows)), [])  # chữ ký đã mất với xt

    def test_bare_cr_line_breaks_denied(self) -> None:
        """Review lượt 2 🔴 (P1): `release-check` đọc file bằng `read_text` (`\\r\\n`, `\\r` trần → `\\n`); `\\r` trần trước
        dòng ký/`## 5` không giấu được dòng ký khỏi guard — Write, MCP (Edit: luôn chặn)."""
        rule = "|---|---|---|---|\n"
        cr_head = TEMPLATE_S.replace("\n\n## 5. Ký", "\n\r## 5. Ký")  # `## 5` sau `\r` trần
        for base, old, new in (
            (TEMPLATE_S, rule + TEMPLATE_ROW, rule.rstrip("\n") + "\r" + SIGNED_ROW),
            (TEMPLATE_S, TEMPLATE_ROW, "x\r" + SIGNED_ROW),
            (cr_head, TEMPLATE_ROW, SIGNED_ROW),
        ):
            with self.subTest(base=base, new=new):
                after = base.replace(old, new, 1)
                path = self.put(GO_REL, base)
                path.write_bytes(after.encode("utf-8"))
                self.assertTrue(xt._go_sign_rows(path.read_text(encoding="utf-8")), after)  # release-check thấy
                self.put(GO_REL, base)
                self.assert_sign_denied(self.edit(GO_REL, {"content": after}))
                got = self.mcp("mcp__github__create_or_update_file", {"path": GO_REL, "content": after, "branch": "x"})
                self.assertEqual(got[:2], ("deny", "GO_SIGN"), got)

    def test_bare_cr_content_denied(self) -> None:
        """D-417: nội dung có `\\r` không kèm `\\n` ngay sau (kể cả `\\r\\r\\n`) → chặn Write và MCP, kể cả khi không thêm dòng
        ký — chặn D-392 qua `x\\r# …`/`x\\rsubject:`; CRLF thường vẫn cho."""
        title = "# GO-NO-GO v9.9.9\n"
        cr_subj = "x\r" + SUBJ.replace("a" * 64, "d" * 64) + SUBJ
        for text in (
            SIGNED_S.replace(title, "x\r# GO-NO-GO v9.9.10\n" + title),
            SIGNED_S.replace(SUBJ, cr_subj),
            TEMPLATE_S.replace("Bản vá.", "x\ry"),
            TEMPLATE_S.replace("\n", "\r\r\n"),
        ):
            with self.subTest(text=text):
                self.put(GO_REL, SIGNED_S)
                got = self.edit(GO_REL, {"content": text})
                self.assert_sign_denied(got)
                self.assertIn("\\r", got[2])
                got = self.mcp("mcp__github__create_or_update_file", {"path": GO_REL, "content": text, "branch": "x"})
                self.assertEqual(got[:2], ("deny", "GO_SIGN"), got)

    def test_bom_mismatch_denied(self) -> None:
        """A5 (review lượt 3): Write tool giữ BOM của file trên đĩa — BOM của nội dung lệch đĩa → chặn; khớp → so như thường."""
        fm = "---\nkind: go\n---\n"
        bom = chr(0xFEFF)
        self.put(GO_REL, fm + SIGNED)
        self.assert_sign_denied(self.edit(GO_REL, {"content": bom + fm + SIGNED}))  # bước 1: thêm BOM
        self.put(GO_REL, bom + fm + SIGNED)
        self.assert_sign_denied(self.edit(GO_REL, {"content": "---\n# GO-NO-GO v9.9.10\n---\n" + SIGNED}))  # bước 2
        self.assertEqual(self.write(GO_REL, bom + fm + SIGNED.replace("Bản vá.", "Bản vá 2.")), "")
        self.assertEqual(self.write("docs/ops/GO-NO-GO-new.md", bom + TEMPLATE)[:4], "deny")

    def test_crlf_signed_note_allowed(self) -> None:
        """Đối chứng: file đã ký ở CRLF, ghi chú thêm bằng Write vẫn cho chạy — chuẩn hoá không làm chặn oan."""
        crlf = SIGNED_S.replace("\n", "\r\n")
        self.put(GO_REL, crlf)
        self.assertEqual(self.write(GO_REL, crlf.replace("Bản vá.", "Bản vá 2.")), "")
        self.assertEqual(self.write(GO_REL, SIGNED_S.replace("Bản vá.", "Bản vá 2.")), "")  # CRLF → LF

    def test_refusal_keeps_broad_rows(self) -> None:
        """Lời từ chối NO-GO vẫn đọc rộng (regex cũ, cả dòng nhiều dòng) — ẩn thêm chỉ an toàn cho GO."""
        text = SIGN_HEAD + "| Chủ repo | An | NO-GO |\n    x\n2026-11-07 |\n"
        self.assertEqual(xt._go_no_go_refusals(text), ["NO-GO"])
        self.assertIn(r"\s*", xt.GO_REFUSAL_ROW_RE.pattern)

    def test_section_six_row_moved_up_denied(self) -> None:
        """🔴2: dòng 4 cột có tên+ngày ở §6 không làm dòng đó thành 'đã có' ở §5 (luật thô cũ và view xt so riêng)."""
        r6 = "| Theo dõi rollback | An | GO | 2026-11-07 |\n"
        s6 = "\n## 6. Sau phát hành\n\n| Việc | Người | Kết quả | Ngày |\n|---|---|---|---|\n" + r6
        for head in (HEAD, NOTED_HEAD):
            with self.subTest(head=head):
                disk = head + SIGN_HEAD + TEMPLATE_ROW + s6
                self.put(GO_REL, disk)
                self.assertEqual(xt._go_sign_rows(disk.replace(TEMPLATE_ROW, r6, 1)), [("GO", "2026-11-07")])
                self.assert_sign_denied(self.edit(GO_REL, {"old_string": TEMPLATE_ROW, "new_string": r6}))
                self.assert_sign_denied(self.edit(GO_REL, {"content": disk.replace(TEMPLATE_ROW, r6, 1)}))

    def test_unsigned_noted_with_section_six_not_over_blocked(self) -> None:
        """🟠: file chưa ký có chú thích + bảng 4 cột ở §6 — không bị coi là đã ký."""
        plain = TEMPLATE_S.replace(TAIL, TAIL + "|---|---|---|---|\n")
        for text in (plain, plain.replace("Bản vá.", "Bản vá. <!-- ghi chú -->")):
            with self.subTest(text=text):
                self.put(GO_REL, text)
                self.assertEqual(guard._go_sign_rows(text), set())
                self.assertEqual(self.write(GO_REL, text.replace(SUBJ, SUBJ.replace("a", "d"))), "")
                self.assertEqual(self.write(GO_REL, text.replace("v9.9.9\n\n", "v9.9.10\n\n")), "")
                self.assertEqual(self.write(GO_REL, text + "| Việc 2 | Bình | xong | 2026-11-09 |\n"), "")
                got = self.mcp("mcp__github__create_or_update_file", {"path": GO_REL, "content": text, "branch": "x"})
                self.assertEqual(got[0], "", got)

    def test_reveal_hidden_row_denied(self) -> None:
        """Lớp 'lật cho hiện' (có từ trước): bỏ dấu ẩn quanh dòng ký người đã ẩn ở §5 = chữ ký mới với release-check."""
        for wrap in (("<!--\n", "-->\n"), ("```\n", "```\n")):
            with self.subTest(wrap=wrap):
                hidden = wrap[0] + SIGNED_ROW + wrap[1]
                self.put(GO_REL, HEAD + SIGN_HEAD + hidden + TEMPLATE_ROW)
                self.assertEqual(xt._go_sign_rows(HEAD + SIGN_HEAD + hidden), [])
                self.assert_sign_denied(self.edit(GO_REL, {"content": HEAD + SIGN_HEAD + SIGNED_ROW + TEMPLATE_ROW}))

    def test_raw_rule_kept(self) -> None:
        """Luật thô cũ vẫn là một họ riêng (chặt hơn xt): thêm dòng ký trong chú thích/khối rào ở §5 bị chặn; file có
        dòng ký thô (xt không tính) vẫn khoá tiêu đề/`subject:` (D-392)."""
        for hidden in ("<!--\n" + SIGNED_ROW + "-->\n", "```\n" + SIGNED_ROW + "```\n"):
            with self.subTest(hidden=hidden):
                self.put(GO_REL, TEMPLATE_S)
                hid = TEMPLATE_S.replace(TEMPLATE_ROW, hidden)
                self.assertEqual(xt._go_sign_rows(hid), [])
                self.assert_sign_denied(self.edit(GO_REL, {"content": hid}))
                self.put(GO_REL, hid)
                got = self.edit(GO_REL, {"content": hid.replace(SUBJ, SUBJ.replace("a" * 64, "d" * 64))})
                self.assertEqual(got[:2], ("deny", "GO_SIGN"), got)
                self.assertIn("D-392", got[2])

    def test_rebind_on_shown_view_denied(self) -> None:
        """D-392 so neo trên CẢ văn bản thô lẫn phần `release-check` thấy: tráo chú thích quanh hai dòng `subject:` (tập
        thô không đổi) hay thụt `subject:` thành khối code → chặn trên file đã ký (mục 'có từ trước' của review lượt 1)."""
        a, b = "subject: content `" + "a" * 64 + "`\n", "subject: content `" + "d" * 64 + "`\n"
        before = HEAD + a + "<!--\n" + b + "-->\n\n" + SIGN_HEAD + SIGNED_ROW
        self.put(GO_REL, before)
        swapped = before.replace(a + "<!--\n" + b + "-->\n", "<!--\n" + a + "-->\n" + b)
        self.assertEqual(guard._go_anchors(before), guard._go_anchors(swapped))  # thô y nguyên
        got = self.edit(GO_REL, {"content": swapped})
        self.assertIn("D-392", got[2])
        self.assertIn("D-392", self.edit(GO_REL, {"content": before.replace(a, "\t" + a)})[2])

    def test_view_failure_fails_closed(self) -> None:
        """Guard không đọc chắc phần hiển thị (lỗi bất ngờ) → deny GO_SIGN, không fail-open của hook."""
        self.put(GO_REL, TEMPLATE)
        with mock.patch.object(guard, "_go_shown", side_effect=RecursionError("x")):
            got = self.edit(GO_REL, {"content": TEMPLATE.replace("Bản vá.", "Bản vá 2.")})
            self.assertEqual(got[:2], ("deny", "GO_SIGN"), got)
            self.assertIn("không đọc chắc", got[2])
            got = self.mcp("mcp__github__create_or_update_file", {"path": GO_REL, "content": "x", "branch": "x"})
            self.assertEqual(got[:2], ("deny", "GO_SIGN"), got)
            self.assertEqual(self.edit("NOTES.md", {"content": SIGNED})[0], "")  # file khác: luật không xét

    def test_concurrent_decisions_consistent(self) -> None:
        """Mỗi lời gọi có trạng thái duyệt riêng (`_GoShown`): chạy song song cho cùng kết quả như tuần tự."""
        from concurrent.futures import ThreadPoolExecutor

        cases = [(base, base.replace(old, new)) for base, old, new in LURES] + [(SIGNED_S, SIGNED_S + "x\n")]
        for i, (base, _) in enumerate(cases):
            self.put(f"docs/ops/GO-NO-GO-{i}.md", base)
        jobs = [(f"docs/ops/GO-NO-GO-{i}.md", self.write_of(after)) for i, (_, after) in enumerate(cases)] * 4
        want = [self.edit(rel, ti)[0] for rel, ti in jobs]
        with ThreadPoolExecutor(max_workers=8) as pool:
            got = list(pool.map(lambda job: self.edit(*job)[0], jobs))
        self.assertEqual(got, want)
        self.assertEqual(want[: len(cases)], ["deny"] * len(LURES) + [""])

    @staticmethod
    def write_of(content: str) -> Dict[str, object]:
        return {"content": content}

    def test_lure_then_rebind_denied(self) -> None:
        """Bước 1 thêm mồi `## 5` (không thêm dòng ký → cho chạy); bước 2 đổi `subject:` của file đã ký → D-392."""
        signed = ANCHORED + SIGN_HEAD + SIGNED_ROW
        for lure in ("<!--\n## 5. mồi\n-->\n", "```\n## 5. mồi\n```\n"):
            with self.subTest(lure=lure):
                self.put(GO_REL, signed)
                self.assertEqual(self.write(GO_REL, signed.replace("## 1. Phạm vi", lure + "## 1. Phạm vi")), "")
                lured = self.put(GO_REL, signed.replace("## 1. Phạm vi", lure + "## 1. Phạm vi")).read_text()
                got = self.edit(GO_REL, {"content": lured.replace(SUBJ, SUBJ.replace("a" * 64, "d" * 64))})
                self.assertEqual(got[:2], ("deny", "GO_SIGN"), got)
                self.assertIn("D-392", got[2])
                self.assertEqual(self.edit(GO_REL, {"content": lured.replace("v9.9.9\n\n", "v9.9.10\n\n")})[0], "deny")

    def test_unsigned_with_comment_writes_allowed(self) -> None:
        """File chưa ký có chú thích (như mẫu GO-NO-GO, §5 ở cuối): Write đổi tiêu đề/`subject:` vẫn cho chạy."""
        text = ANCHORED.replace("Bản vá.", "Bản vá. <!-- ghi chú -->") + SIGN_HEAD + TEMPLATE_ROW
        self.put(GO_REL, text)
        self.assertEqual(self.write(GO_REL, text.replace(SUBJ, SUBJ.replace("a", "d"))), "")
        self.assertEqual(self.write(GO_REL, text.replace("v9.9.9\n\n", "v9.9.10\n\n")), "")


SUBJ = "subject: content `" + "a" * 64 + "`\n"
SUBJ_DIGEST = "> - Subject: digest " + "b" * 64 + "\n"
ANCHORED = HEAD + SUBJ + SUBJ_DIGEST + "\n"
SIGNED_S = ANCHORED + SIGN_HEAD + SIGNED_ROW + TAIL
TEMPLATE_S = ANCHORED + SIGN_HEAD + TEMPLATE_ROW + TAIL
NOTED_HEAD = HEAD.replace("Bản vá.", "Bản vá. <!-- ghi chú -->")
# Mảnh dòng cho fuzz đồng bộ guard↔xt (AUD-SEC-615): tiêu đề, dòng ký trọn/mảnh, mọi cách mở/đóng khối ẩn của xt.
FUZZ_LINES = (
    "## 5. Ký",
    "﻿## 5. Ký",
    "## 6. Sau",
    "## 1. x",
    SIGNED_ROW[:-1],
    SIGNED_ROW[:-1] + "\r",
    "| Chủ repo | Bình | NO-GO | 2026-11-08 |",
    TEMPLATE_ROW[:-1],
    "| Chủ repo |",
    "An | GO | 2026-11-07 |",
    LURE_ROW[:-1],
    "x -->" + SIGNED_ROW[:-1],
    "|---|---|---|---|",
    "```",
    "````",
    "~~~",
    "> ```",
    "- ```",
    "1. ~~~",
    "\t```",
    "  ```",
    "   ~~~",
    "<!--",
    "-->",
    "a --> b",
    "` --> ` <!-- `",
    "<!-- x -->",
    "<!-->",
    "<?x",
    "?>",
    "<script>",
    "</script>",
    "<style>x</style>",
    "<!DOCTYPE",
    ">",
    "<![CDATA[",
    "]]>",
    "    x",
    "  > x",
    "- x",
    "chữ",
    "",
)


def fuzz_texts(seed: int, count: int) -> List[str]:
    rnd = random.Random(seed)
    return ["\n".join(rnd.choices(FUZZ_LINES, k=rnd.randint(1, 12))) + rnd.choice(("", "\n")) for _ in range(count)]


class GoNoGoXtSyncTest(GoNoGoGuardBase):
    """AUD-TEST-100/AUD-SEC-615: bản chép tối thiểu `_markdown_shown` trong guard đồng bộ với xt (regex + hàm), và mọi
    dòng ký `release-check` thấy thì guard thấy; dòng ký mới với xt thì guard chặn (fuzz seed cố định)."""

    PAIRS = (
        ("GO_SIGN_ROW_RE", "GO_SIGN_ROW_RE"),
        ("GO_COMMENT_TOKEN_RE", "HTML_COMMENT_TOKEN_RE"),
        ("GO_FENCE_RE", "SHOWN_FENCE_RE"),
        ("GO_CLOSE_RE", "SHOWN_CLOSE_RE"),
        ("GO_BLOCK_LINE_RE", "SHOWN_BLOCK_LINE_RE"),
        ("GO_HTML_HIDDEN_RE", "HTML_HIDDEN_RE"),
    )

    def test_regex_copies_match(self) -> None:
        for mine, theirs in self.PAIRS:
            with self.subTest(mine):
                a, b = getattr(guard, mine), getattr(xt, theirs)
                self.assertEqual((a.pattern, a.flags), (b.pattern, b.flags))

    def test_shown_copy_matches_fuzz(self) -> None:
        for text in fuzz_texts(615, 4000):
            self.assertEqual(guard._go_shown(text), xt._markdown_shown(text), repr(text))
            mine = guard._go_sign_rows(text)
            self.assertLessEqual(set(xt._go_sign_rows(text)), {(r[2], r[3]) for r in mine}, repr(text))
            self.assertLessEqual(set(xt._go_signers(text)), {r[1] for r in mine}, repr(text))
        for line in (x for t in fuzz_texts(100, 1500) for x in t.split("\n")):
            for inside in (False, True):
                self.assertEqual(guard._go_uncomment(line, inside), xt._strip_html_comments(line, inside), line)

    def test_bytes_read_text_e2e_fuzz(self) -> None:
        """Review lượt 2 🔴: nội dung ghi y nguyên ra BYTE, `release-check` đọc bằng `read_text` (universal newlines) —
        dòng ký/tên xt thấy thì guard chặn Write vào file trống và MCP (xuống dòng ngẫu nhiên `\\n`/`\\r\\n`/`\\r`)."""
        rnd = random.Random(2615)
        path = self.root / GO_REL
        hits = 0
        for _ in range(4000):
            lines = rnd.choices(FUZZ_LINES, k=rnd.randint(1, 10))
            text = "".join(x + rnd.choice(("\n", "\r\n", "\r")) for x in lines)
            path.write_bytes(text.encode("utf-8"))
            shown = path.read_text(encoding="utf-8")
            if not (xt._go_sign_rows(shown) or xt._go_signers(shown)):
                continue
            hits += 1
            with mock.patch.object(guard, "_go_read", return_value=None):
                self.assertIn("Không ghi dòng ký §5", guard._go_sign_deny(GO_REL, GO_REL, "/x", {"content": text}))
            self.assertTrue(
                guard._mcp_go_sign_why("mcp__github__create_or_update_file", {"path": GO_REL, "content": text})
            )
        self.assertGreater(hits, 40)

    def test_new_xt_row_denied_fuzz(self) -> None:
        """Lần ghi làm `release-check` thấy dòng ký mới (hay tên ký mới) → guard chặn (một chiều: guard còn luật thô)."""
        texts = fuzz_texts(7, 3000)
        pairs = list(zip(texts, texts[1:] + texts[:1]))
        hits = 0
        for before, after in pairs:
            new = set(xt._go_sign_rows(after)) - set(xt._go_sign_rows(before))
            new_names = set(xt._go_signers(after)) - set(xt._go_signers(before))
            with mock.patch.object(guard, "_go_read", return_value=before):
                why = guard._go_sign_deny(GO_REL, GO_REL, "/x", {"content": after})
            if new or new_names:
                hits += 1
                self.assertIn("Không ghi dòng ký §5", why, (before, after))
        self.assertGreater(hits, 40)  # fuzz thật sự chạm nhánh chặn


class GoNoGoRebindTest(GoNoGoGuardBase):
    """D-392: file đã ký §5 — đổi tiêu đề `# ` đầu tiên hay tập dòng `subject:` (kết quả còn dòng ký) → deny GO_SIGN;
    file chưa ký, hay cùng lần ghi xoá hết dòng ký → cho chạy."""

    EDITS = (
        ("# GO-NO-GO v9.9.9\n", "# GO-NO-GO v9.9.10\n"),  # đổi tiêu đề
        (SUBJ, SUBJ + "subject: digest " + "c" * 64 + "\n"),  # thêm dòng subject
        (SUBJ, SUBJ.replace("a" * 64, "d" * 64)),  # sửa
        (SUBJ, ""),  # xoá
        (SUBJ_DIGEST, SUBJ_DIGEST.replace("b" * 64, "e" * 64)),  # dạng trích dẫn + gạch đầu dòng, khoá hoa
    )

    def assert_rebind_denied(self, got: Tuple[str, str, str]) -> None:
        self.assertEqual(got[:2], ("deny", "GO_SIGN"), got)
        self.assertIn("D-392", got[2])
        self.assertIn("xoá dòng ký trước, người ký lại", got[2])

    def test_signed_anchor_edits_denied(self) -> None:
        self.put(GO_REL, SIGNED_S)
        for old, new in self.EDITS:
            with self.subTest(old=old, new=new):
                self.assert_rebind_denied(self.edit(GO_REL, {"content": SIGNED_S.replace(old, new, 1)}))

    def test_unsigned_anchor_writes_allowed(self) -> None:
        self.put(GO_REL, TEMPLATE_S)
        for old, new in self.EDITS:
            with self.subTest(old=old, new=new):
                self.assertEqual(self.write(GO_REL, TEMPLATE_S.replace(old, new, 1)), "")

    def test_drop_signature_with_anchor_change_allowed(self) -> None:
        self.put(GO_REL, SIGNED_S)
        rewritten = TEMPLATE_S.replace(SUBJ, SUBJ.replace("a" * 64, "f" * 64)).replace(
            "v9.9.9\n\n## 1", "v9.9.10\n\n## 1"
        )
        self.assertEqual(self.write(GO_REL, rewritten), "")
        self.assert_rebind_denied(self.edit(GO_REL, {"content": SIGNED_S.replace("v9.9.9\n\n## 1", "v9.9.10\n\n## 1")}))

    def test_signed_other_writes_allowed(self) -> None:
        self.put(GO_REL, SIGNED_S)
        self.assertEqual(self.write(GO_REL, SIGNED_S.replace("Bản vá.", "Bản vá 2.")), "")
        self.assertEqual(self.write(GO_REL, SIGNED_S.replace("title: GO-NO-GO v9.9.9", "title: x")), "")
        self.assertEqual(self.write(GO_REL, SIGNED_S + "\nGhi chú.\n"), "")

    def test_crlf_signed_title_change_denied(self) -> None:
        crlf = SIGNED_S.replace("\n", "\r\n")
        self.put(GO_REL, crlf)
        self.assert_rebind_denied(
            self.edit(GO_REL, {"content": crlf.replace("v9.9.9\r\n\r\n## 1", "v9.9.10\r\n\r\n## 1")})
        )

    def test_anchors_skip_frontmatter(self) -> None:
        self.assertEqual(
            guard._go_anchors(SIGNED_S), ("# GO-NO-GO v9.9.9", sorted([SUBJ.strip(), SUBJ_DIGEST.strip()]))
        )
        self.assertEqual(guard._go_anchors("---\n# not\n---\nx\n"), ("", []))


class GoNoGoBashTest(GoNoGoGuardBase):
    """Bash ghi `GO-NO-GO*.md` → chặn (sửa bằng Write để guard so dòng ký); đọc, xoá cả file, file khác → cho chạy."""

    def setUp(self) -> None:
        super().setUp()
        self.put(GO_REL, TEMPLATE)

    def test_write_forms_denied(self) -> None:
        for cmd in (
            f"echo '| Chủ | A | GO | 2026-11-07 |' >> {GO_REL}",
            f"printf x > {GO_REL}",
            f"sed -i 's/| | GO/| An | GO/' {GO_REL}",
            f"echo x | tee -a {GO_REL}",
            f"cp /tmp/signed.md {GO_REL}",
            "cp /tmp/x/GO-NO-GO-y.md docs/ops/",
            f"mv docs/a.md {GO_REL}",
            f"git checkout HEAD~1 -- {GO_REL}",
            f"git restore -s HEAD~1 {GO_REL}",
            "sed -i s/a/b/ docs/ops/*.md",
            "python3 -c \"open('docs/ops/GO-NO-GO-x.md','a').write('x')\"",
        ):
            self.assertEqual(self.bash(cmd), ("deny", "GO_SIGN"), cmd)

    def test_relative_cwd_and_symlink_denied(self) -> None:
        self.assertEqual(self.bash("echo x >> GO-NO-GO-x.md", str(self.root / "docs" / "ops")), ("deny", "GO_SIGN"))
        self.assertEqual(self.bash("cd docs/ops && echo x >> GO-NO-GO-x.md"), ("deny", "GO_SIGN"))
        os.symlink(self.root / GO_REL, self.root / "n.md")
        self.assertEqual(self.bash("echo x >> n.md"), ("deny", "GO_SIGN"))

    def test_reads_and_other_files_allowed(self) -> None:
        for cmd in (
            f"cat {GO_REL}",
            f"grep -n Ký {GO_REL}",
            "ls docs/ops/GO-NO-GO*",
            "echo x > NOTES.md",
            "sed -i s/a/b/ docs/*.md",
            "python3 -c \"print(open('docs/ops/GO-NO-GO-x.md').read())\"",
            f"python3 scripts/xt.py release-check --json > /tmp/rc.json; cat {GO_REL}",
        ):
            self.assertEqual(self.bash(cmd)[0], "", cmd)

    def test_delete_whole_file_allowed(self) -> None:
        for cmd in (f"rm -f {GO_REL}", f"git rm -q {GO_REL}", f"unlink {GO_REL}"):
            self.assertEqual(self.bash(cmd)[0], "", cmd)

    def test_glob_hit_limits(self) -> None:
        ops = str(self.root / "docs" / "ops")
        self.assertTrue(guard._go_glob_hit(ops + "/*.md"))
        self.assertFalse(guard._go_glob_hit(ops + "/GO-NO-GO-x.md"))  # không glob: luật tên xét
        self.assertFalse(guard._go_glob_hit(str(self.root) + "/*/ops/*.md"))  # glob ở thư mục: giới hạn đã ghi
        self.assertFalse(guard._go_glob_hit("docs/ops/*.md"))  # tương đối: `_where` đã giải ra tuyệt đối
        self.assertFalse(guard._go_glob_hit(ops + "/*.txt"))
        with mock.patch.object(guard, "_outside_names", return_value=None):  # thư mục quá lớn: không đọc
            self.assertFalse(guard._go_glob_hit(ops + "/*.md"))

    def test_touch_allowed_truncate_denied(self) -> None:
        """AUD-SEC-537: `touch` chỉ đổi mtime → cho; chuyển hướng của chính lệnh `touch` vẫn là ghi. `truncate` GIỮ chặn:
        cắt đuôi không giống xoá dòng ký — nó HOÀN THÀNH được một dòng ký (dòng cuối `| … | 2026-11-07 |x` không khớp
        regex, Edit cho; cắt 1 byte → dòng ký mới; cùng việc đó qua Edit bị chặn)."""
        for cmd in (f"touch {GO_REL}", f"touch -d 2026-01-01 {GO_REL}"):
            self.assertEqual(self.bash(cmd)[0], "", cmd)
        self.assertEqual(self.bash(f"touch x > {GO_REL}"), ("deny", "GO_SIGN"))
        bait = SIGN_HEAD + SIGNED_ROW.rstrip("\n") + "x"
        self.put(GO_REL, TEMPLATE)
        self.assertEqual(self.edit(GO_REL, {"content": bait})[0], "")  # chưa là dòng ký
        self.put(GO_REL, bait)
        got = self.edit(GO_REL, {"old_string": SIGNED_ROW.rstrip("\n") + "x", "new_string": SIGNED_ROW.rstrip("\n")})
        self.assertEqual(got[:2], ("deny", "GO_SIGN"))  # bỏ đuôi bằng Edit = thêm dòng ký
        for cmd in (f"truncate -s -1 {GO_REL}", f"truncate -s0 {GO_REL}"):
            self.assertEqual(self.bash(cmd), ("deny", "GO_SIGN"), cmd)


class GoNoGoLinkTest(GoNoGoGuardBase):
    """AUD-SEC-533: liên kết (cứng) tới GO-NO-GO — ghi tên trung tính là ghi chính file đó."""

    def setUp(self) -> None:
        super().setUp()
        self.put(GO_REL, TEMPLATE)
        self.put("docs/a.md", "x")

    def test_link_from_go_no_go_denied(self) -> None:
        for cmd in (
            f"ln {GO_REL} n.md",
            f"ln -s {GO_REL} n.md",
            f"ln -t docs {GO_REL}",
            f"link {GO_REL} n.md",
            f"cp -l {GO_REL} n.md",
            f"cp -al {GO_REL} n.md",
            f"cp --link {GO_REL} n.md",
            "ln docs/ops/go-no-go-X.MD n.md",
        ):
            self.assertEqual(self.bash(cmd), ("deny", "GO_SIGN"), cmd)

    def test_link_source_through_symlink_denied(self) -> None:
        os.symlink(self.root / GO_REL, self.root / "s.md")
        self.assertEqual(self.bash("ln s.md h.md"), ("deny", "GO_SIGN"))

    def test_link_reason_names_source(self) -> None:
        payload = {"tool_input": {"command": f"ln {GO_REL} n.md"}, "cwd": str(self.root)}
        reason = str(guard._rule_decision("bash", payload, str(self.root))["reason"])
        self.assertIn("nguồn liên kết", reason)

    def test_other_links_and_copies_allowed(self) -> None:
        for cmd in ("ln docs/a.md n.md", "cp -l docs/a.md n.md", "link docs/a.md n.md", f"cp {GO_REL} /tmp/b.md"):
            self.assertEqual(self.bash(cmd)[0], "", cmd)
        self.assertEqual(guard._go_link_sources(["cp", "-r", "a", "b"]), [])


class GoNoGoArgvTest(GoNoGoGuardBase):
    """AUD-SEC-535 (ADR-0066): lệnh ngoài danh sách trắng chỉ đọc nêu tên GO-NO-GO → chặn; đổi tên theo biểu thức/archive
    đổi tên thành viên có chữ `go-no-go` → chặn; đọc → cho."""

    def setUp(self) -> None:
        super().setUp()
        self.put(GO_REL, TEMPLATE)
        self.put("docs/ops/tmp.md", SIGNED)

    def test_unknown_writers_denied(self) -> None:
        for cmd in (
            f"cat /tmp/signed.md | sponge {GO_REL}",
            f"ruby -pi -e 'sub(/x/,\"y\")' {GO_REL}",
            f"ex -s +'%s/a/b/' +wq {GO_REL}",
            f"vim -es +'%s/a/b/' +wq {GO_REL}",
            f"gsed -i s/a/b/ {GO_REL}",
            f"python3 -c \"import sys;open(sys.argv[1],'a').write('x')\" {GO_REL}",
            f'perl -e \'open(F,">>",$ARGV[0]);print F "x"\' {GO_REL}',
            f"prettier --write {GO_REL}",
            "prettier --write docs/ops/*.md",
            "npx prettier --check docs/ops/GO-NO-GO-x.md",  # lệnh bọc: mất miễn (chiều chặt)
            f"mytool --out={GO_REL}",
            "mytool out:GO-NO-GO-y.md",
            "mytool docs/ops/go-no-go-y.MD",
            f"tar -xf /tmp/a.tar {GO_REL}",
            f"LESSOPEN='|x' less {GO_REL}",
            f"env GIT_EXTERNAL_DIFF=sh git diff {GO_REL}",
            f"git -C . diff {GO_REL}",
            f"git stash push -- {GO_REL}",
            "find docs -name 'GO-NO-GO*.md' -exec sed -i s/a/b/ {} +",
        ):
            self.assertEqual(self.bash(cmd), ("deny", "GO_SIGN"), cmd)

    def test_rename_family_denied(self) -> None:
        for cmd in (
            "rename 's/tmp/GO-NO-GO-z/' docs/ops/tmp.md",
            "rename.ul tmp GO-NO-GO-z docs/ops/tmp.md",
            "echo docs/ops/tmp.md | xargs rename 's/tmp/go-no-go-z/'",  # từ đổi tên không đứng đầu lệnh
            "mmv 'docs/ops/tmp.md' 'docs/ops/GO-NO-GO-z.md'",
            "tar -cf /tmp/a.tar --transform 's/tmp.md/GO-NO-GO-y.md/' -C docs/ops tmp.md",
            "tar -cf /tmp/a.tar --xform=s,tmp,GO-NO-GO-y, -C docs/ops tmp.md",
            "bsdtar -cf /tmp/a.tar -s ',tmp,GO-NO-GO-y,' docs/ops/tmp.md",
        ):
            self.assertEqual(self.bash(cmd), ("deny", "GO_SIGN"), cmd)

    def test_rename_and_archive_without_go_allowed(self) -> None:
        for cmd in (
            "rename 's/tmp/notes/' docs/ops/tmp.md",
            "tar -cf /tmp/a.tar --transform 's/tmp/x/' docs/ops/tmp.md",
            "tar -czf /tmp/a.tgz docs",
            "curl -s https://example.com/go-no-go",  # `-s` ngoài tar: không phải biểu thức đổi tên
        ):
            self.assertEqual(self.bash(cmd)[0], "", cmd)

    def test_readers_allowed(self) -> None:
        for cmd in (
            f"cat {GO_REL}",
            f"grep -n Ký {GO_REL}",
            f"head -20 {GO_REL}",
            f"less {GO_REL}",
            f"more {GO_REL}",
            f"wc -l {GO_REL}",
            f"diff {GO_REL} docs/ops/tmp.md",
            f"md5sum {GO_REL}",
            f"stat {GO_REL}",
            f"chmod 644 {GO_REL}",
            f"echo {GO_REL}",
            f"git show HEAD:{GO_REL}",
            f"git log --oneline -- {GO_REL}",
            f"git diff -- {GO_REL}",
            f"git add {GO_REL}",
            f"git commit -m 'docs(release): GO-NO-GO v9' -- {GO_REL}",
            f"git blame {GO_REL}",
            f"git restore --staged {GO_REL}",
            "python3 scripts/xt.py release-check --json",
            f"sed -n 1,5p {GO_REL}",
            f"sed 's/a/b/' {GO_REL} > /tmp/out.md",
            f"cp {GO_REL} /tmp/b.md",
            f"prettier --check {GO_REL}",
            "markdownlint docs/ops/*.md",
            "find docs -name 'GO-NO-GO*.md'",
            "find docs -name 'GO-NO-GO*.md' -exec cat {} +",
            "ls docs/ops/GO-NO-GO*",
            f"gh issue comment 5 --body 'đã lập {GO_REL}'",  # câu chữ kết thúc bằng đường dẫn: không phải tên tệp
            # lệnh bọc `normalize` bóc là trong suốt (bất biến fuzz `allow-kept`); gán biến không đổi chương trình
            f"XT_FUZZ=1 cat {GO_REL}",
            f"command less {GO_REL}",
            f"nice -n 5 git show HEAD:{GO_REL}",
            f"timeout 60 command git log -- {GO_REL}",
            f"env A=1 touch {GO_REL}",
        ):
            self.assertEqual(self.bash(cmd)[0], "", cmd)

    def test_word_is_path(self) -> None:
        self.assertTrue(guard._go_word("docs/ops/GO-NO-GO v3.md"))  # tên tệp có khoảng trắng vẫn là đường dẫn
        self.assertTrue(guard._go_word("--out=docs/ops/GO-NO-GO-x.md"))
        self.assertFalse(guard._go_word("đã lập docs/ops/GO-NO-GO-x.md"))
        self.assertFalse(guard._go_word("docs(release): lập GO-NO-GO-x.md"))

    def test_reader_helper_branches(self) -> None:
        self.assertFalse(guard._go_reader(["prettier", "-w", "a"], ["prettier", "-w", "a"]))
        self.assertFalse(guard._go_reader(["markdownlint", "--fix=true"], ["markdownlint", "--fix=true"]))
        self.assertTrue(guard._go_reader(["tee", "a"], ["tee", "a"]))  # đích đã mô hình ở write_targets
        self.assertEqual(guard._go_argv_hits([], [], str(self.root), str(self.root)), [])


class GoNoGoPatchTest(GoNoGoGuardBase):
    """AUD-SEC-534: `patch`/`git apply`/`git am` với diff từ tệp/stdin ở dự án có GO-NO-GO — đọc được header và không chạm
    GO-NO-GO → cho; còn lại → chặn."""

    GO_DIFF = f"--- a/{GO_REL}\n+++ b/{GO_REL}\n@@ -1 +1 @@\n-a\n+b\n"
    OK_DIFF = "--- a/docs/a.md\n+++ b/docs/a.md\n@@ -1 +1 @@\n-a\n+b\n"

    def setUp(self) -> None:
        super().setUp()
        self.put(GO_REL, TEMPLATE)
        self.put("go.diff", self.GO_DIFF)
        self.put("ok.diff", self.OK_DIFF)
        self.put("go.mbox", "From x\nSubject: [PATCH] x\n\n---\n" + self.GO_DIFF)
        self.put("ok.mbox", "From x\nSubject: [PATCH] x\n\n---\n" + self.OK_DIFF)
        self.put("b64.mbox", "From x\nContent-Transfer-Encoding: base64\n\nLS0tIGEv\n")

    def test_blind_patch_touching_or_unreadable_denied(self) -> None:
        for cmd in (
            "git apply go.diff",
            "git apply < go.diff",
            "git -C . apply --directory sub go.diff",
            "patch -p1 < go.diff",
            "patch -p1 -i go.diff",
            "patch -p1 --input=go.diff",
            "patch -p1 -i missing.diff",
            "patch -p1 < fix.diff && git diff",  # tệp diff không có: không đọc được → chặn (ca đối chứng cũ AUD-SEC-414)
            "patch -p1 -i -",
            "git apply -",
            "cat ok.diff | git apply",
            "git am go.mbox",
            "git am b64.mbox",
            "git am",
            "git am --continue",
            "git apply --stat --apply go.diff",
            "git apply docs",  # thư mục: không phải tệp thường
            "git apply <<'EOF'\nkhông có header\nEOF",
            "sh -c 'git apply go.diff'",
            f"git apply {self.root}/go.diff",
        ):
            self.assertEqual(self.bash(cmd), ("deny", "GO_SIGN"), cmd)

    def test_readable_clean_patch_allowed(self) -> None:
        for cmd in (
            "git apply ok.diff",
            "git apply < ok.diff",
            "git apply -p1 --whitespace fix ok.diff",
            "patch -p1 < ok.diff",
            "patch -p1 -i ok.diff",
            "git am ok.mbox",
            "git apply --check go.diff",
            "git apply --stat go.diff",
            "patch --dry-run -p1 -i go.diff",
            "git am --abort",
            "patch docs/a.md go.diff",  # file gốc nêu ở toán hạng: đích đã mô hình
            "git apply <<'EOF'\n" + self.OK_DIFF + "EOF",
        ):
            self.assertEqual(self.bash(cmd)[0], "", cmd)

    def test_project_without_go_no_go_allowed(self) -> None:
        """Dự án chưa có `GO-NO-GO*.md`: diff KHÔNG đọc được (stdin, tệp không có) cho chạy — không chặn oan dự án không
        dùng GO-NO-GO; diff đọc được không chạm GO-NO-GO cho chạy."""
        (self.root / GO_REL).unlink()
        (self.root / "docs" / "GO-NO-GO.txt").write_text("x", encoding="utf-8")
        self.assertFalse(guard._go_on_disk(str(self.root)))
        for cmd in ("git apply ok.diff", "cat ok.diff | git apply", "patch -p1 -i missing.diff", "git am b64.mbox"):
            self.assertEqual(self.bash(cmd)[0], "", cmd)
        self.put("GO-NO-GO.md", TEMPLATE)  # mẫu dự án đích ở gốc
        self.assertTrue(guard._go_on_disk(str(self.root)))

    def test_fresh_project_diff_creating_go_no_go_denied(self) -> None:
        """AUD-SEC-539: dự án chưa có GO-NO-GO, diff ĐỌC ĐƯỢC tạo mới/đổi tên thành `GO-NO-GO*.md` (đã ký) → chặn — header
        diff xét bất kể `_go_on_disk` (như `echo … > GO-NO-GO.md` bị luật tên chặn)."""
        (self.root / GO_REL).unlink()
        signed = SIGN_HEAD + SIGNED_ROW
        hunk = "".join("+" + line + "\n" for line in signed.splitlines())
        new = f"diff --git a/{GO_REL} b/{GO_REL}\nnew file mode 100644\n--- /dev/null\n+++ b/{GO_REL}\n@@ -0,0 +1 @@\n{hunk}"
        self.put("new.diff", new)
        self.put("new.mbox", "From x\nSubject: [PATCH] x\n\n---\n" + new)
        ren = "diff --git a/docs/a.md b/GO-NO-GO.md\nsimilarity index 100%\nrename from docs/a.md\nrename to GO-NO-GO.md\n"
        self.put("ren.diff", ren)
        self.assertFalse(guard._go_on_disk(str(self.root)))
        for cmd in ("git apply new.diff", "patch -p1 -i new.diff", "git am new.mbox", "git apply ren.diff"):
            self.assertEqual(self.bash(cmd), ("deny", "GO_SIGN"), cmd)
        self.assertEqual(self.bash("git apply new.diff ok.diff"), ("deny", "GO_SIGN"))  # một tệp chạm là đủ

    def test_go_on_disk_errors(self) -> None:
        (self.root / GO_REL).unlink()
        shutil.rmtree(self.root / "docs")
        (self.root / "docs").write_text("tệp, không phải thư mục", encoding="utf-8")
        self.assertFalse(guard._go_on_disk(str(self.root)))
        with mock.patch.object(guard.os, "scandir", side_effect=PermissionError("x")):
            self.assertTrue(guard._go_on_disk(str(self.root)))  # không đọc được: coi như có

    def test_diff_size_cap_and_unknown_dir(self) -> None:
        with mock.patch.object(guard, "GO_PATCH_MAX", len(self.OK_DIFF) - 1):
            self.assertEqual(self.bash("git apply ok.diff"), ("deny", "GO_SIGN"))
        with mock.patch.object(guard, "GO_PATCH_MAX", len(self.OK_DIFF)):
            self.assertEqual(self.bash("git apply ok.diff")[0], "")
        self.assertEqual(guard._go_diff_state("ok.diff", None, False), guard.GO_DIFF_BLIND)
        self.assertEqual(guard._go_diff_state(str(self.root / "ok.diff"), None, False), guard.GO_DIFF_CLEAR)
        self.assertEqual(guard._go_diff_state(str(self.root / "go.diff"), None, False), guard.GO_DIFF_TOUCHES)
        with mock.patch.dict(os.environ, {"HOME": str(self.root)}):
            self.assertEqual(guard._go_diff_state("~/ok.diff", None, False), guard.GO_DIFF_CLEAR)

    def test_header_quoted_octal_and_space_timestamp_denied(self) -> None:
        """Review #469 🔴: tên có nháy kiểu C của git (`\\107` = `G`, cả `rename to`/`copy to`/`diff --git`) và timestamp
        cách tên bằng DẤU CÁCH — git apply/GNU patch đều ghi GO-NO-GO; guard phải thấy ở mọi dự án."""
        body = "".join("+" + line + "\n" for line in (SIGN_HEAD + SIGNED_ROW).splitlines())
        q = '"b/docs/ops/\\107O-NO-GO-v1.md"'
        variants = {
            "v3": f'diff --git "a/docs/ops/\\107O-NO-GO-v1.md" {q}\nnew file mode 100644\n--- /dev/null\n+++ {q}\n'
            f"@@ -0,0 +1 @@\n{body}",
            "v4": "--- /dev/null 2026-11-07 10:00:00.000000000 +0700\n"
            "+++ b/docs/ops/GO-NO-GO-v1.md 2026-11-07 10:00:00.000000000 +0700\n"
            f"@@ -0,0 +1 @@\n{body}",
            "v26": 'diff --git a/docs/a.md "b/docs/ops/\\107O-NO-GO-v1.md"\nsimilarity index 100%\n'
            'rename from docs/a.md\nrename to "docs/ops/\\107O-NO-GO-v1.md"\n',
            "v27": f"--- /dev/null 2026-11-07 10:00:00 +0700\n+++ b/docs/ops/GO-NO-GO-v1.md 2026-11-07 10:00:00 +0700\n"
            f"@@ -0,0 +1 @@\n{body}",
            "copy": 'diff --git a/docs/a.md "b/\\107O-NO-GO.md"\ncopy from docs/a.md\ncopy to "\\107O-NO-GO.md"\n',
            "space-name": f"--- /dev/null\n+++ b/docs/ops/GO-NO-GO v1.md 2026-11-07 10:00:00 +0700\n@@ -0,0 +1 @@\n{body}",
            "binary": "diff --git a/docs/ops/GO-NO-GO v1.md b/docs/ops/GO-NO-GO v1.md\nnew file mode 100644\n"
            "GIT binary patch\nliteral 3\nKcmZ?wfB*mj0RR91\n",
        }
        for fresh in (False, True):
            if fresh:
                (self.root / GO_REL).unlink()
            for name, text in variants.items():
                self.put(f"{name}.diff", text)
                for cmd in (f"git apply {name}.diff", f"patch -p1 -i {name}.diff"):
                    self.assertEqual(self.bash(cmd), ("deny", "GO_SIGN"), (fresh, cmd))

    def test_header_clean_space_timestamp_and_base64_line_allowed(self) -> None:
        """Đối chứng: diff sạch có timestamp cách bằng dấu cách cho chạy; dòng `Content-Transfer-Encoding: base64` trong
        diff của `git apply` (không phải mbox của `git am`) không làm diff thành không đọc được (mutant M9)."""
        self.put(
            "ts.diff",
            "--- a/docs/a.md 2026-11-07 10:00:00 +0700\n+++ b/docs/a.md 2026-11-07 10:00:00 +0700\n"
            "@@ -1 +1 @@\n-a\n+b\n",
        )
        self.put("b64.diff", "Content-Transfer-Encoding: base64\n" + self.OK_DIFF)
        for cmd in ("git apply ts.diff", "patch -p1 -i ts.diff", "git apply b64.diff"):
            self.assertEqual(self.bash(cmd)[0], "", cmd)
        self.assertEqual(self.bash("git am b64.diff"), ("deny", "GO_SIGN"))  # mbox mã hoá: không đọc được

    def test_c_unquote(self) -> None:
        self.assertEqual(guard._c_unquote("\\107O"), "GO")
        self.assertEqual(guard._c_unquote("v\\303\\251.md"), "vé.md")
        self.assertEqual(guard._c_unquote('\\t\\n\\\\\\"\\a\\b\\f\\r\\v'), '\t\n\\"\a\b\f\r\v')
        self.assertEqual(guard._c_unquote("\\q\\7x"), "q\x07x")  # thoát lạ: giữ chữ; octal ngắn vẫn giải
        self.assertEqual(guard._c_unquote("\\377"), "\ufffd")  # byte không phải UTF-8
        self.assertEqual(guard._c_unquote("x\\"), "x\\")  # gạch chéo cuối chuỗi

    def test_header_paths_superset(self) -> None:
        """Chỉ THÊM ứng viên so với regex cũ (luật AUD-SEC-414 dùng chung)."""
        text = 'diff --git a/x y.md b/x y.md\n+++ b/n.md 2026-01-01 1 +0700\nrename to "a\\142"\ncopy from "c\\144"\n'
        got = guard._patch_header_paths(text)
        cands = ("a/x", "y.md", "a/x y.md", "b/x y.md", "b/n.md 2026-01-01 1 +0700", "b/n.md", "a\\142", "ab", "cd")
        for want in cands:
            self.assertIn(want, got)

    def test_patch_state_priority(self) -> None:
        """Một tệp chạm GO-NO-GO thắng tệp không đọc được; không đọc được thắng sạch."""
        cands = (str(self.root),)
        self.assertEqual(guard._go_patch_state(["git", "apply", "missing.diff", "go.diff"], cands), "touches")
        self.assertEqual(guard._go_patch_state(["git", "apply", "missing.diff", "ok.diff"], cands), "blind")
        self.assertEqual(guard._go_patch_state(["git", "apply", "ok.diff"], cands), "clear")
        self.assertEqual(guard._go_patch_state(["git", "apply"], cands), "blind")
        self.assertEqual(guard._go_patch_state(["patch", "docs/a.md", "go.diff"], cands), "clear")

    def test_unmatched_placement_fails_closed(self) -> None:
        root = str(self.root)
        got = guard._go_patch_asks("git apply ok.diff", [], root, root, False)
        self.assertEqual(len(got), 1)
        self.assertIn("git apply ok.diff", got[0])
        self.assertEqual(guard._go_patch_asks("ls", [], root, root, False), [])

    def test_yields_to_allowlist_budget(self) -> None:
        """Lớp danh sách trắng đã chặn chắc (`_patch_file_why`: áp diff mù rồi chạy tệp) → giữ mã BUDGET của nó; bỏ phần
        chạy → luật GO-NO-GO chặn."""
        cmd, root = "git apply go.diff; bash s.sh", str(self.root)
        placed = guard._commands_with_cwds(guard.tokenize(cmd), root)
        self.assertEqual(guard._go_patch_asks(cmd, placed, root, root, True), [])
        self.assertEqual(len(guard._go_patch_asks(cmd, placed, root, root, False)), 1)  # ngoài tập con: không nhường
        self.assertEqual(self.bash(cmd), ("deny", "BUDGET"))
        self.assertEqual(self.bash("git apply go.diff"), ("deny", "GO_SIGN"))

    def test_concurrent_decisions_consistent(self) -> None:
        """Quyết định đọc tệp diff/thư mục: chạy song song cho cùng kết quả như tuần tự."""
        from concurrent.futures import ThreadPoolExecutor

        cmds = ["git apply go.diff", "git apply ok.diff", "patch -p1 -i go.diff", "git am ok.mbox"] * 6
        want = [self.bash(c)[0] for c in cmds]
        with ThreadPoolExecutor(max_workers=8) as pool:
            got = list(pool.map(lambda c: self.bash(c)[0], cmds))
        self.assertEqual(got, want)
        self.assertEqual(want[:4], ["deny", "", "deny", ""])


class GoNoGoMcpTest(GoNoGoGuardBase):
    """AUD-SEC-536: tool MCP ghi file (GitHub `create_or_update_file`/`push_files`) ghi GO-NO-GO có dòng ký §5 → deny."""

    def test_signed_content_denied(self) -> None:
        got = self.mcp("mcp__github__create_or_update_file", {"path": GO_REL, "content": SIGNED, "branch": "main"})
        self.assertEqual(got[:2], ("deny", "GO_SIGN"), got)
        self.assertIn("ADR-0068 §Quyết định 3a", got[2])
        files = [{"path": "README.md", "content": "x"}, {"path": "go-no-go-v1.MD", "content": SIGNED}]
        self.assertEqual(self.mcp("mcp__github__push_files", {"files": files})[:2], ("deny", "GO_SIGN"))
        self.assertEqual(self.mcp("mcp__gh2__push_files", {"files": files})[:2], ("deny", "GO_SIGN"))

    def test_unsigned_other_or_odd_payload_allowed(self) -> None:
        for name, ti in (
            ("mcp__github__create_or_update_file", {"path": GO_REL, "content": TEMPLATE}),
            ("mcp__github__create_or_update_file", {"path": "NOTES.md", "content": SIGNED}),
            ("mcp__github__create_or_update_file", {"path": GO_REL, "content": SIGN_HEAD.encode().hex()}),
            ("mcp__github__create_or_update_file", {"path": 5, "content": SIGNED}),
            ("mcp__github__push_files", {"files": "rác"}),
            ("mcp__github__push_files", {"files": ["rác", {"path": GO_REL}]}),
            ("mcp__github__delete_file", {"path": GO_REL, "content": SIGNED}),
            ("mcp__github__get_file_contents", {"path": GO_REL}),
        ):
            # ADR-0074/D-402: tool ghi commit không nêu nhánh = nhánh mặc định → bị chặn như push `main`; ca này chỉ xét
            # luật GO_SIGN nên ghi lên nhánh làm việc.
            ti = {**ti, "branch": "claude/x"} if "get_file" not in name else ti
            self.assertEqual(self.mcp(name, ti)[0], "", (name, ti))


class GoNoGoReadTest(unittest.TestCase):
    def test_read_limit(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "f.diff"
            p.write_text("abcd", encoding="utf-8")
            self.assertEqual(guard._go_read(str(p), 4), "abcd")
            self.assertIsNone(guard._go_read(str(p), 3))
            self.assertEqual(guard._go_read(str(p)), "abcd")


if __name__ == "__main__":
    unittest.main()
