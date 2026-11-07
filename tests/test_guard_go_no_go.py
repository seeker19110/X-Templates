"""AUD-SEC-497 (D-390): agent không tự ghi dòng ký §5 của `GO-NO-GO*.md` — mẫu ghi "con người, không phải agent", chữ ký
là đầu vào của `release-check` `promotion: approved` (ADR-0068 §Quyết định 3a). Nợ review #464: liên kết cứng
(AUD-SEC-533), diff từ tệp/stdin (AUD-SEC-534), lệnh ngoài danh sách trắng/đổi tên theo biểu thức (AUD-SEC-535), MCP ghi
file (AUD-SEC-536), lý do/touch (AUD-SEC-537). Payload giả như hook PreToolUse."""

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

    def mcp(self, name: str, tool_input: Dict[str, object]) -> Tuple[str, str, str]:
        payload = {"tool_name": name, "tool_input": tool_input}
        out = guard.apply_policy(guard._rule_decision("mcp", payload, str(self.root)))
        return str(out["decision"]), str(out.get("code")), str(out.get("reason", ""))


class GoNoGoEditTest(GoNoGoGuardBase):
    """Edit/MultiEdit/Write/NotebookEdit: so tập dòng ký §5 trước và sau."""

    def assert_sign_denied(self, got: Tuple[str, str, str]) -> None:
        self.assertEqual(got[:2], ("deny", "GO_SIGN"), got)
        for part in ("ADR-0068 §Quyết định 3a", "mẫu GO-NO-GO §5", "AUD-SEC-497", "chữ ký §5 là của người"):
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
