"""AUD-SEC-497 (D-390): agent không tự ghi dòng ký §5 của `GO-NO-GO*.md` — mẫu ghi "con người, không phải agent", chữ ký
là đầu vào của `release-check` `promotion: approved` (ADR-0068 §6). Payload giả như hook PreToolUse."""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
import unittest
import unittest.mock as mock
from pathlib import Path
from typing import Dict, Optional, Tuple

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


class GoNoGoEditTest(GoNoGoGuardBase):
    """Edit/MultiEdit/Write/NotebookEdit: so tập dòng ký §5 trước và sau."""

    def assert_sign_denied(self, got: Tuple[str, str, str]) -> None:
        self.assertEqual(got[:2], ("deny", "GO_SIGN"), got)
        for part in ("ADR-0068 §6", "AUD-SEC-497", "chữ ký §5 là của người"):
            self.assertIn(part, got[2])

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

    def test_edit_section_one_allowed(self) -> None:
        for text in (TEMPLATE, SIGNED):
            self.put(GO_REL, text)
            got = self.edit(GO_REL, {"old_string": "Bản vá.", "new_string": "Bản vá installer."})
            self.assertEqual(got[0], "", got)

    def test_edit_template_table_blank_allowed(self) -> None:
        self.put(GO_REL, TEMPLATE)
        got = self.edit(GO_REL, {"old_string": TEMPLATE_ROW, "new_string": "| Chủ dự án | | GO / NO-GO | |\n"})
        self.assertEqual(got[0], "", got)
        got = self.edit("docs/ops/GO-NO-GO-y.md", {"content": TEMPLATE})
        self.assertEqual(got[0], "", got)

    def test_remove_sign_row_allowed(self) -> None:
        self.put(GO_REL, SIGNED)
        got = self.edit(GO_REL, {"old_string": SIGNED_ROW, "new_string": TEMPLATE_ROW})
        self.assertEqual(got[0], "", got)
        self.assertEqual(self.edit(GO_REL, {"content": TEMPLATE})[0], "")

    def test_repadding_sign_row_allowed(self) -> None:
        self.put(GO_REL, SIGNED)
        got = self.edit(GO_REL, {"old_string": SIGNED_ROW, "new_string": "|  Chủ repo  |An|  GO |2026-11-07|\n"})
        self.assertEqual(got[0], "", got)

    def test_row_outside_section_five_allowed(self) -> None:
        self.put(GO_REL, TEMPLATE)
        got = self.edit(GO_REL, {"old_string": "Bản vá.", "new_string": "| Rủi ro | An | thấp | 2026-11-07 |"})
        self.assertEqual(got[0], "", got)
        self.assertEqual(self.edit(GO_REL, {"old_string": TAIL, "new_string": TAIL + SIGNED_ROW})[0], "")

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
        self.assert_sign_denied(self.edit(GO_REL, {"edits": edits}))
        ok = [{"old_string": "Bản vá.", "new_string": "Bản vá 2."}, "rác"]
        self.assertEqual(self.edit(GO_REL, {"edits": ok})[0], "")

    def test_replace_all(self) -> None:
        self.put(GO_REL, HEAD + TEMPLATE_ROW + SIGN_HEAD + TEMPLATE_ROW + TAIL)  # dòng mẫu ở §1 đứng trước §5
        once = {"old_string": TEMPLATE_ROW, "new_string": SIGNED_ROW}
        self.assertEqual(self.edit(GO_REL, once)[0], "")  # chỉ lần xuất hiện đầu (§1) đổi
        self.assert_sign_denied(self.edit(GO_REL, {**once, "replace_all": True}))

    def test_old_string_missing_falls_back_to_snippets(self) -> None:
        self.put(GO_REL, TEMPLATE)
        self.assert_sign_denied(self.edit(GO_REL, {"old_string": "không có", "new_string": SIGNED_ROW}))
        self.assertEqual(self.edit(GO_REL, {"old_string": "không có", "new_string": "chữ"})[0], "")
        self.assertEqual(self.edit(GO_REL, {"old_string": SIGNED_ROW + "x", "new_string": SIGNED_ROW})[0], "")

    def test_unreadable_file_snippets(self) -> None:
        self.assert_sign_denied(self.edit("docs/ops/GO-NO-GO-none.md", {"old_string": "", "new_string": SIGNED}))
        self.assertEqual(self.edit("docs/ops/GO-NO-GO-none.md", {"old_string": "", "new_string": TEMPLATE})[0], "")
        self.put(GO_REL, TEMPLATE)
        with mock.patch.object(guard, "open", create=True, side_effect=PermissionError("x")):
            self.assertIsNone(guard._go_read(str(self.root / GO_REL)))
            self.assert_sign_denied(self.edit(GO_REL, {"old_string": TEMPLATE_ROW, "new_string": SIGNED_ROW}))
            self.assertEqual(self.edit(GO_REL, {"content": TEMPLATE})[0], "")

    def test_not_a_regular_file(self) -> None:
        d = self.root / "docs" / "GO-NO-GO-dir.md"
        d.mkdir()
        self.assertIsNone(guard._go_read(str(d)))
        self.assert_sign_denied(self.edit("docs/GO-NO-GO-dir.md", {"content": SIGNED}))

    def test_notebook_edit_new_source(self) -> None:
        got = self.edit("GO-NO-GO.md", {"notebook_path": "", "new_source": SIGNED_ROW})
        self.assert_sign_denied(got)
        payload = {"tool_input": {"notebook_path": str(self.root / "GO-NO-GO.md"), "new_source": "x"}}
        self.assertEqual(guard._rule_decision("edit", payload, str(self.root))["decision"], "")

    def test_no_tool_input(self) -> None:
        self.assertEqual(guard.edit_decision(str(self.root / GO_REL), str(self.root)), ("", ""))

    def test_crlf_rows(self) -> None:
        self.put(GO_REL, TEMPLATE.replace("\n", "\r\n"))
        got = self.edit(GO_REL, {"content": SIGNED.replace("\n", "\r\n")})
        self.assert_sign_denied(got)

    def test_rows_match_xt_release_check(self) -> None:
        """Bản sao regex trong guard đúng với `xt._go_sign_rows` (nguồn của `release-check`)."""
        self.assertEqual(guard.GO_SIGN_ROW_RE.pattern, xt.GO_SIGN_ROW_RE.pattern)
        for text in (TEMPLATE, SIGNED, SIGNED + SIGNED_ROW, HEAD, SIGN_HEAD + "| a | b | c | 2026-01-01 |\n"):
            mine = sorted((r[2], r[3]) for r in guard._go_sign_rows(text))
            self.assertEqual(mine, sorted(set(xt._go_sign_rows(text))), text)


SUBJ = "subject: content `" + "a" * 64 + "`\n"
SUBJ_DIGEST = "> - Subject: digest " + "b" * 64 + "\n"
ANCHORED = HEAD + SUBJ + SUBJ_DIGEST + "\n"
SIGNED_S = ANCHORED + SIGN_HEAD + SIGNED_ROW + TAIL
TEMPLATE_S = ANCHORED + SIGN_HEAD + TEMPLATE_ROW + TAIL


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
                self.assert_rebind_denied(self.edit(GO_REL, {"old_string": old, "new_string": new}))
                self.assert_rebind_denied(self.edit(GO_REL, {"content": SIGNED_S.replace(old, new, 1)}))

    def test_unsigned_anchor_edits_allowed(self) -> None:
        self.put(GO_REL, TEMPLATE_S)
        for old, new in self.EDITS:
            with self.subTest(old=old, new=new):
                self.assertEqual(self.edit(GO_REL, {"old_string": old, "new_string": new})[0], "")
                self.assertEqual(self.edit(GO_REL, {"content": TEMPLATE_S.replace(old, new, 1)})[0], "")

    def test_drop_signature_with_anchor_change_allowed(self) -> None:
        self.put(GO_REL, SIGNED_S)
        rewritten = TEMPLATE_S.replace(SUBJ, SUBJ.replace("a" * 64, "f" * 64)).replace(
            "v9.9.9\n\n## 1", "v9.9.10\n\n## 1"
        )
        self.assertEqual(self.edit(GO_REL, {"content": rewritten})[0], "")
        edits = [
            {"old_string": SIGNED_ROW, "new_string": TEMPLATE_ROW},
            {"old_string": "# GO-NO-GO v9.9.9\n", "new_string": "# GO-NO-GO v9.9.10\n"},
        ]
        self.assertEqual(self.edit(GO_REL, {"edits": edits})[0], "")
        self.assert_rebind_denied(self.edit(GO_REL, {"edits": edits[1:]}))

    def test_signed_other_edits_allowed(self) -> None:
        self.put(GO_REL, SIGNED_S)
        self.assertEqual(self.edit(GO_REL, {"old_string": "Bản vá.", "new_string": "Bản vá 2."})[0], "")
        self.assertEqual(self.edit(GO_REL, {"old_string": "title: GO-NO-GO v9.9.9", "new_string": "title: x"})[0], "")
        self.assertEqual(self.edit(GO_REL, {"content": SIGNED_S + "\nGhi chú.\n"})[0], "")

    def test_loose_snippets_on_signed_file(self) -> None:
        self.put(GO_REL, SIGNED_S)
        got = self.edit(GO_REL, {"old_string": "# GO-NO-GO v1\n", "new_string": "# GO-NO-GO v2\n"})
        self.assert_rebind_denied(got)
        old = "# GO-NO-GO v1\n" + SIGNED_ROW  # đoạn cũ bỏ cả dòng ký: kết quả không còn chữ ký
        self.assertEqual(self.edit(GO_REL, {"old_string": old, "new_string": "# GO-NO-GO v2\n"})[0], "")

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
    """Bash ghi `GO-NO-GO*.md` → chặn (sửa bằng Edit để guard so dòng ký); đọc, xoá cả file, file khác → cho chạy."""

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


if __name__ == "__main__":
    unittest.main()
