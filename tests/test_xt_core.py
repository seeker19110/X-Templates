"""Test lõi cho scripts/xt.py (frontmatter, validate, compose, vòng lặp autopilot, ghi nguyên tử).

Bổ sung cho test_xt.py: phủ các nhánh lỗi/biên. Chạy: python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import argparse
import contextlib
import io
import datetime as _dt
import json
import os
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest
import unittest.mock
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import xt

SECTION_DIRS = ("01-baseline", "02-profiles", "03-industries", "08-backend")


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text).lstrip("\n"), encoding="utf-8")


def md(meta: dict[str, str], body: str = "# Tiêu đề\n") -> str:
    """Dựng một file markdown có frontmatter phẳng; mặc định hợp lệ cho khoá bắt buộc."""
    base = {"title": "Tiêu đề", "kind": "module", "updated": "2026-10-13"}
    base.update(meta)
    head = "\n".join(f"{k}: {v}" for k, v in base.items() if v is not None)
    return f"---\n{head}\n---\n\n{body}"


MODULE_BODY = textwrap.dedent(
    """\
    # Mô-đun

    ## Checklist

    - [ ] `{prefix}-001` **MUST** Làm việc A. → Kiểm: test A.

    ## Nguồn

    - x
    """
)


def make_fw(tmp: Path, files: dict[str, str] | None = None) -> Path:
    """Khung giả: mỗi thư mục có README hợp lệ, cộng các file truyền vào (đường dẫn tương đối framework/)."""
    fw = tmp / "framework"
    write(fw / "README.md", md({"kind": "index"}))
    for d in SECTION_DIRS:
        write(fw / d / "README.md", md({"kind": "index"}))
    for rel, text in (files or {}).items():
        write(fw / rel, text)
    return fw


class TmpMixin:
    def tmpdir(self) -> Path:
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        return Path(td.name)


# --------------------------------------------------------------------------- frontmatter


class FrontmatterEdgeTest(unittest.TestCase):
    def test_blank_and_comment_lines_are_skipped(self):
        meta, body, n = xt.parse_frontmatter("---\n\n# ghi chú\ntitle: A\n   \n---\n# Thân\n")
        self.assertEqual(meta, {"title": "A"})
        self.assertEqual(body, "# Thân")
        self.assertEqual(n, 6)

    def test_line_without_colon(self):
        with self.assertRaisesRegex(xt.FrontmatterError, "dòng frontmatter 2 không có dạng"):
            xt.parse_frontmatter("---\nkhong co hai cham\n---\n")

    def test_invalid_key(self):
        with self.assertRaisesRegex(xt.FrontmatterError, "khoá frontmatter không hợp lệ"):
            xt.parse_frontmatter("---\nBad-Key: 1\n---\n")

    def test_duplicate_key(self):
        with self.assertRaisesRegex(xt.FrontmatterError, "khoá frontmatter lặp: title"):
            xt.parse_frontmatter("---\ntitle: a\ntitle: b\n---\n")

    def test_unclosed_and_missing_frontmatter(self):
        with self.assertRaisesRegex(xt.FrontmatterError, "không có dòng '---' đóng"):
            xt.parse_frontmatter("---\ntitle: a\n")
        with self.assertRaisesRegex(xt.FrontmatterError, "thiếu frontmatter"):
            xt.parse_frontmatter("")
        with self.assertRaisesRegex(xt.FrontmatterError, "thiếu frontmatter"):
            xt.parse_frontmatter("# không có\n")

    def test_values_quotes_lists_unicode(self):
        meta, _, _ = xt.parse_frontmatter(
            '---\na: "có dấu: ví dụ"\nb: \'x\'\nc: [p, "q r", ]\nd: []\ne: "\nf: \'\n---\n'
        )
        self.assertEqual(meta["a"], "có dấu: ví dụ")
        self.assertEqual(meta["b"], "x")
        self.assertEqual(meta["c"], ["p", "q r"])
        self.assertEqual(meta["d"], [])
        # Chuỗi chỉ một ký tự nháy không bị cắt.
        self.assertEqual(meta["e"], '"')
        self.assertEqual(meta["f"], "'")

    def test_as_list(self):
        self.assertEqual(xt._as_list(None), [])
        self.assertEqual(xt._as_list("all"), ["all"])
        self.assertEqual(xt._as_list(["a", 3]), ["a", "3"])
        self.assertEqual(xt._as_list(""), [""])


# --------------------------------------------------------------------------- load_docs / resolve_modules


class LoadDocsTest(TmpMixin, unittest.TestCase):
    def test_bad_frontmatter_is_reported_and_doc_skipped(self):
        fw = make_fw(self.tmpdir(), {"08-backend/bad.md": "---\ntitle a\n---\n# x\n"})
        docs, errors = xt.load_docs(fw)
        self.assertNotIn("08-backend/bad", {d.rel for d in docs})
        self.assertEqual(len(errors), 1)
        self.assertTrue(errors[0].startswith("08-backend/bad.md: dòng frontmatter 2"))

    def test_item_like_line_and_fence(self):
        body = (
            "# T\n\n- [ ] `BAD` **MUST** thiếu số thứ tự\n\n```\n- [ ] `X-001` **MUST** trong fence\n```\n\n"
            "- [ ] `OK-001` **SHOULD** hợp lệ\n#hashtag không phải tiêu đề\n\n## Nguồn\n- [a](a.md)\n"
            "```\n[b](b.md)\n```\n"
        )
        fw = make_fw(self.tmpdir(), {"08-backend/m.md": md({"prefix": "OK"}, body)})
        docs, errors = xt.load_docs(fw)
        doc = next(d for d in docs if d.rel == "08-backend/m")
        self.assertEqual([i.id for i in doc.items], ["OK-001"])
        self.assertEqual(doc.headings, ["T", "Nguồn"])  # `#hashtag` (thiếu khoảng trắng) không phải tiêu đề
        self.assertEqual([line for _, line in doc.link_lines], ["- [a](a.md)"])  # liên kết trong fence bỏ qua
        self.assertEqual(len(errors), 1)
        self.assertIn("mục checklist sai định dạng", errors[0])

    def test_resolve_modules_glob_without_hit_and_exact_missing(self):
        fw = make_fw(
            self.tmpdir(),
            {
                "08-backend/api.md": md({"prefix": "API", "applies_to": "[all]"}, MODULE_BODY.format(prefix="API")),
                "08-backend/idx.md": md({"kind": "index"}),
            },
        )
        docs, _ = xt.load_docs(fw)
        by_rel = {d.rel: d for d in docs}
        mods, missing = xt.resolve_modules(["08-backend/*", "99-none/*", "08-backend/api", "08-backend/zzz"], by_rel)
        self.assertEqual([m.rel for m in mods], ["08-backend/api"])  # README bị loại, index không phải module, bỏ trùng
        self.assertEqual(missing, ["99-none/*", "08-backend/zzz"])


# --------------------------------------------------------------------------- validate


class ValidateBranchesTest(TmpMixin, unittest.TestCase):
    def errors_for(self, files: dict[str, str]) -> list[str]:
        return xt.validate(make_fw(self.tmpdir(), files))

    def assertHas(self, errors: list[str], needle: str) -> None:
        self.assertTrue(any(needle in e for e in errors), f"không thấy {needle!r} trong {errors}")

    def mod(self, **meta: str) -> str:
        meta.setdefault("prefix", "MOD")
        meta.setdefault("applies_to", "[all]")
        return md(meta, MODULE_BODY.format(prefix=meta["prefix"]))

    def test_valid_module_has_no_errors(self):
        self.assertEqual(self.errors_for({"08-backend/m.md": self.mod()}), [])

    def test_missing_required_key(self):
        errors = self.errors_for({"08-backend/m.md": self.mod(title="")})
        self.assertHas(errors, "08-backend/m.md: thiếu khoá frontmatter 'title'")

    def test_invalid_kind_and_date(self):
        errors = self.errors_for({"08-backend/m.md": self.mod(kind="la", updated="13/10/2026")})
        self.assertHas(errors, "kind không hợp lệ 'la'")
        self.assertHas(errors, "'updated' phải dạng YYYY-MM-DD")

    def test_body_must_start_with_heading(self):
        errors = self.errors_for({"08-backend/m.md": md({"prefix": "MOD", "applies_to": "all"}, "chỉ có chữ\n")})
        self.assertHas(errors, "nội dung phải bắt đầu bằng tiêu đề")

    def test_items_without_prefix_and_invalid_prefix(self):
        errors = self.errors_for(
            {
                "08-backend/a.md": md({"prefix": None, "applies_to": "all"}, MODULE_BODY.format(prefix="ABC")),
                "08-backend/b.md": self.mod(prefix="1BAD"),
            }
        )
        self.assertHas(errors, "08-backend/a.md: có mục checklist nhưng thiếu 'prefix'")
        self.assertHas(errors, "prefix '1BAD' không hợp lệ")

    def test_duplicate_prefix(self):
        errors = self.errors_for({"08-backend/a.md": self.mod(prefix="DUP"), "08-backend/b.md": self.mod(prefix="DUP")})
        self.assertHas(errors, "08-backend/b.md: prefix 'DUP' đã dùng ở 08-backend/a.md")

    def test_item_rules_state_scale_id_prefix_must_check_and_duplicates(self):
        body = (
            "# T\n\n## Checklist\n\n"
            "- [x] `MOD-001` **MUST** đã tick. → Kiểm: a.\n"
            "- [ ] `MOD-002` **SHOULD@L** có ngưỡng sai chỗ.\n"
            "- [ ] `MOD-001` **MUST** trùng ID. → Kiểm: b.\n"
            "- [ ] `OTH-003` **MUST** sai prefix. → Kiểm: c.\n"
            "- [ ] `MOD-004` **MUST** thiếu kiểm.\n\n## Nguồn\n\n- x\n"
        )
        errors = self.errors_for({"08-backend/m.md": md({"prefix": "MOD", "applies_to": "all"}, body)})
        self.assertHas(errors, "mục trong khung phải ở trạng thái '[ ]'")
        self.assertHas(errors, "ngưỡng quy mô '@L' chỉ dùng với MUST")
        self.assertHas(errors, "ID trùng MOD-001")
        self.assertHas(errors, "ID OTH-003 không khớp prefix 'MOD'")
        self.assertHas(errors, "mục MUST MOD-004 thiếu '→ Kiểm:'")

    def test_too_many_must_at_m(self):
        rows = "\n".join(f"- [ ] `MOD-{i:03d}` **MUST** m{i}. → Kiểm: t." for i in range(1, 6))
        body = f"# T\n\n## Checklist\n\n{rows}\n\n## Nguồn\n\n- x\n"
        errors = self.errors_for({"08-backend/m.md": md({"prefix": "MOD", "applies_to": "all"}, body)})
        self.assertHas(errors, "5 MUST hiệu lực ở quy mô M, trần 4")

    def test_missing_checklist_and_sources_headings(self):
        body = "# T\n\n## Danh sách\n\n- [ ] `MOD-001` **SHOULD** a.\n"
        errors = self.errors_for({"08-backend/m.md": md({"prefix": "MOD", "applies_to": "all"}, body)})
        self.assertHas(errors, "thiếu mục '## Checklist'")
        self.assertHas(errors, "thiếu mục '## Nguồn'")

    def test_missing_applies_to_and_unknown_profile_slug(self):
        profile = md(
            {"kind": "profile", "slug": "web", "modules": "[]"},
            "# P\n\n## Nguồn\n\n- x\n",
        )
        errors = self.errors_for(
            {
                "02-profiles/web.md": profile,
                "08-backend/a.md": self.mod(prefix="AAA", applies_to=None),
                "08-backend/b.md": self.mod(prefix="BBB", applies_to="[web, ghost]"),
            }
        )
        self.assertHas(errors, "08-backend/a.md: thiếu 'applies_to'")
        self.assertHas(errors, "08-backend/b.md: applies_to có slug hồ sơ không tồn tại: ghost")

    def test_profile_slug_missing_duplicate_and_unknown_modules(self):
        def prof(**meta: str) -> str:
            meta.setdefault("kind", "profile")
            return md(meta, "# P\n\n## Nguồn\n\n- x\n")

        errors = self.errors_for(
            {
                "02-profiles/a.md": prof(slug="same", modules="[08-backend/nope]"),
                "02-profiles/b.md": prof(slug="same"),
                "02-profiles/c.md": prof(),
            }
        )
        self.assertHas(errors, "02-profiles/c.md: thiếu 'slug'")
        self.assertHas(errors, "02-profiles/b.md: slug 'same' trùng với 02-profiles/a.md")
        self.assertHas(errors, "module '08-backend/nope' trong 'modules' không tồn tại")

    def test_links(self):
        body = (
            "# T\n\n[ok](../README.md) [anchor](#muc) [web](https://example.com/x) [mail](mailto:a@b.c)\n"
            "[hỏng](./khong-co.md#x) [ok-anchor](../README.md#a)\n\n```\n[trong fence](nope.md)\n```\n"
        )
        errors = self.errors_for({"08-backend/n.md": md({"kind": "research"}, body)})
        self.assertEqual(len(errors), 1)
        self.assertIn("08-backend/n.md:", errors[0])
        self.assertIn("liên kết hỏng -> ./khong-co.md#x", errors[0])

    def test_directory_without_readme(self):
        fw = make_fw(self.tmpdir())
        (fw / "09-orphan").mkdir()
        self.assertIn("09-orphan/: thiếu README.md (chỉ mục thư mục)", xt.validate(fw))

    def test_frontmatter_error_surfaces_from_validate(self):
        errors = self.errors_for({"08-backend/x.md": "# không frontmatter\n"})
        self.assertHas(errors, "08-backend/x.md: thiếu frontmatter")

    def test_errors_follow_check_group_order_across_files(self):
        """Thứ tự lỗi là hợp đồng: file theo đường dẫn; trong file theo nhóm kiểm; README thư mục ở cuối."""

        def profile(**meta: str) -> str:
            return md({"kind": "profile", **meta}, "# P\n\n## Nguồn\n\n- x\n")

        body_a = (
            "chữ mở đầu\n\n## Danh sách\n\n"
            "- [x] `MOD-001` **MUST** a. → Kiểm: t.\n"
            "- [ ] `MOD-002` **MUST** b. → Kiểm: t.\n"
            "- [ ] `MOD-003` **MUST** c. → Kiểm: t.\n"
            "- [ ] `MOD-004` **MUST** d. → Kiểm: t.\n"
            "- [ ] `MOD-005` **MUST** e. → Kiểm: t.\n\n"
            "[hỏng](./khong-co.md)\n"
        )
        fw = make_fw(
            self.tmpdir(),
            {
                "02-profiles/p.md": md({"kind": "profile", "modules": "[08-backend/nope]"}, "# P\n"),
                "02-profiles/q.md": profile(slug="s", modules="[]"),
                "02-profiles/r.md": profile(slug="s", modules="[]"),
                "08-backend/a.md": md({"title": "", "prefix": "MOD", "applies_to": None}, body_a),
                "08-backend/b.md": md(
                    {"prefix": "MOD", "applies_to": "[all, ghost]"}, MODULE_BODY.format(prefix="MOD")
                ),
            },
        )
        (fw / "09-orphan").mkdir()
        self.assertEqual(
            xt.validate(fw),
            [
                "02-profiles/p.md: thiếu mục '## Nguồn'",
                "02-profiles/p.md: thiếu 'slug'",
                "02-profiles/p.md: module '08-backend/nope' trong 'modules' không tồn tại",
                "02-profiles/r.md: slug 's' trùng với 02-profiles/q.md",
                "08-backend/a.md: thiếu khoá frontmatter 'title'",
                "08-backend/a.md: nội dung phải bắt đầu bằng tiêu đề '# ...' ngay sau frontmatter",
                "08-backend/a.md:12: mục trong khung phải ở trạng thái '[ ]'",
                "08-backend/a.md: 5 MUST hiệu lực ở quy mô M, trần 4 — hạ phần vượt thành MUST@L",
                "08-backend/a.md: thiếu mục '## Checklist'",
                "08-backend/a.md: thiếu mục '## Nguồn'",
                "08-backend/a.md: thiếu 'applies_to'",
                "08-backend/a.md:18: liên kết hỏng -> ./khong-co.md",
                "08-backend/b.md: prefix 'MOD' đã dùng ở 08-backend/a.md",
                "08-backend/b.md:13: ID trùng MOD-001 (đã có ở 08-backend/a.md:12)",
                "08-backend/b.md: applies_to có slug hồ sơ không tồn tại: ghost",
                "09-orphan/: thiếu README.md (chỉ mục thư mục)",
            ],
        )


# --------------------------------------------------------------------------- compose


class ComposeBranchesTest(TmpMixin, unittest.TestCase):
    def build(self, extra_files: dict[str, str] | None = None) -> Path:
        files = {
            "02-profiles/web.md": md(
                {"kind": "profile", "slug": "web", "modules": "[08-backend/*]"}, "# W\n\n## Nguồn\n\n- x\n"
            ),
            "02-profiles/mobile.md": md(
                {"kind": "profile", "slug": "mobile", "modules": "[]"}, "# M\n\n## Nguồn\n\n- x\n"
            ),
            "08-backend/web-only.md": md(
                {"prefix": "WEB", "applies_to": "[web]", "title": "Chỉ web"}, MODULE_BODY.format(prefix="WEB")
            ),
            "08-backend/mobile-only.md": md(
                {"prefix": "MOB", "applies_to": "[mobile]", "title": "Chỉ mobile"}, MODULE_BODY.format(prefix="MOB")
            ),
        }
        files.update(extra_files or {})
        return make_fw(self.tmpdir(), files)

    def test_compose_refuses_framework_with_errors(self):
        fw = self.build({"08-backend/bad.md": "không frontmatter"})
        with self.assertRaises(SystemExit) as cm:
            xt.compose(fw, "web", [], "M", False, today="2026-01-01")
        self.assertIn("Khung có lỗi, chạy 'xt.py validate' trước", str(cm.exception))
        self.assertIn("bad.md", str(cm.exception))

    def test_unknown_profile_and_industry(self):
        fw = self.build()
        with self.assertRaises(SystemExit) as cm:
            xt.compose(fw, "nope", [], "M", False)
        self.assertIn("Không có hồ sơ 'nope'", str(cm.exception))
        with self.assertRaises(SystemExit) as cm:
            xt.compose(fw, "web", ["ghost"], "M", False)
        self.assertIn("Không có gói ngành 'ghost'", str(cm.exception))

    def test_applies_to_filters_modules_unless_added_explicitly(self):
        fw = self.build()
        # Hồ sơ web dùng glob nên bắt cả hai module, nhưng module chỉ-mobile bị lọc theo applies_to.
        out = xt.compose(fw, "web", [], "M", False, today="2026-01-01")
        self.assertIn("`WEB-001`", out)
        self.assertNotIn("`MOB-001`", out)
        # --add là lựa chọn có chủ đích: bỏ lọc applies_to.
        out = xt.compose(fw, "web", [], "M", False, today="2026-01-01", extra=["08-backend/mobile-only"])
        self.assertIn("`MOB-001`", out)
        self.assertIn("extra: [08-backend/mobile-only]", out)

    def test_duplicate_sources_are_composed_once(self):
        fw = self.build(
            {
                "01-baseline/b.md": md(
                    {"kind": "baseline", "title": "Nền", "prefix": "BAS", "applies_to": "[all]"},
                    MODULE_BODY.format(prefix="BAS"),
                ),
                "03-industries/shop.md": md(
                    {
                        "kind": "industry",
                        "slug": "shop",
                        "title": "Ngành shop",
                        "prefix": "SHOP",
                        "modules": "[01-baseline/b]",
                    },
                    MODULE_BODY.format(prefix="SHOP"),
                ),
            }
        )
        # Baseline lặp qua modules của ngành; ngành lặp hai lần trên CLI → mỗi mục chỉ xuất hiện một lần.
        out = xt.compose(fw, "web", ["shop", "shop"], "M", False, today="2026-01-01")
        self.assertEqual(out.count("`BAS-001`"), 1)
        self.assertEqual(out.count("`SHOP-001`"), 1)
        self.assertEqual(out.count("### Ngành shop"), 1)

    def test_bad_extra_module(self):
        with self.assertRaises(SystemExit) as cm:
            xt.compose(self.build(), "web", [], "M", False, extra=["08-backend/khong-co"])
        self.assertIn("Module --add không tồn tại: 08-backend/khong-co", str(cm.exception))

    def test_scale_s_demotes_module_must_and_may_toggle(self):
        fw = self.build(
            {
                "01-baseline/b.md": md(
                    {"kind": "baseline", "prefix": "BAS", "applies_to": "[all]"},
                    "# B\n\n## Checklist\n\n- [ ] `BAS-001` **MUST** nền. → Kiểm: t.\n- [ ] `BAS-002` **MAY** tuỳ chọn.\n"
                    "\n## Nguồn\n\n- x\n",
                )
            }
        )
        out = xt.compose(fw, "web", [], "S", True, today="2026-01-01")
        self.assertIn("`BAS-001` **MUST**", out)
        self.assertIn("`WEB-001` **SHOULD**", out)
        self.assertIn("| MAY | 1 |", out)
        self.assertIn("generated: 2026-01-01", out)
        out_no_may = xt.compose(fw, "web", [], "S", False, today="2026-01-01")
        self.assertNotIn("BAS-002", out_no_may)
        self.assertNotIn("| MAY |", out_no_may)

    def test_effective_level_and_find_by_slug(self):
        item = xt.Item("X-001", "MUST", "L", "t", " ", 1)
        self.assertEqual(xt.effective_level(item, "M"), "SHOULD")
        self.assertEqual(xt.effective_level(item, "L"), "MUST")
        may = xt.Item("X-002", "MAY", None, "t", " ", 1)
        self.assertEqual(xt.effective_level(may, "S", "module"), "MAY")
        docs, _ = xt.load_docs(self.build())
        self.assertIsNotNone(xt.find_by_slug(docs, "profile", "web"))
        self.assertIsNone(xt.find_by_slug(docs, "industry", "web"))


# --------------------------------------------------------------------------- JSON / write_atomic


class JsonAndAtomicTest(TmpMixin, unittest.TestCase):
    def test_read_json_obj_variants(self):
        d = self.tmpdir()
        self.assertIsNone(xt._read_json_obj(d / "missing.json"))
        (d / "bad.json").write_text("{không phải json", encoding="utf-8")
        self.assertIsNone(xt._read_json_obj(d / "bad.json"))
        (d / "list.json").write_text("[1, 2]", encoding="utf-8")
        self.assertIsNone(xt._read_json_obj(d / "list.json"))
        (d / "ok.json").write_text('{"a": "ký tự có dấu"}', encoding="utf-8")
        self.assertEqual(xt._read_json_obj(d / "ok.json"), {"a": "ký tự có dấu"})

    def test_read_json_obj_unreadable_is_none(self):
        d = self.tmpdir()
        (d / "dir.json").mkdir()  # tồn tại nhưng đọc ra OSError
        self.assertIsNone(xt._read_json_obj(d / "dir.json"))

    def test_read_state_corrupt_is_fail_open(self):
        base = self.tmpdir()
        write(base / ".autopilot" / "state.json", "{hỏng")
        self.assertIsNone(xt.read_state(base))
        self.assertEqual(xt.loop_verdict(base)["verdict"], "inactive")

    def test_write_atomic_cleans_temp_on_failure(self):
        d = self.tmpdir()
        target = d / "sub" / "out.txt"
        with unittest.mock.patch("xt.os.replace", side_effect=OSError("đĩa đầy")):
            with self.assertRaisesRegex(OSError, "đĩa đầy"):
                xt.write_atomic(target, "nội dung")
        self.assertFalse(target.exists())
        self.assertEqual(list(target.parent.iterdir()), [])

    def test_write_atomic_cleans_temp_on_keyboard_interrupt(self):
        d = self.tmpdir()
        target = d / "out.txt"
        with unittest.mock.patch("xt.os.replace", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                xt.write_atomic(target, "x")
        self.assertEqual(list(d.iterdir()), [])

    def test_write_atomic_writes_utf8_and_overwrites(self):
        d = self.tmpdir()
        target = d / "a" / "b.txt"
        xt.write_atomic(target, "một")
        xt.write_atomic(target, "hai — ✓")
        self.assertEqual(target.read_text(encoding="utf-8"), "hai — ✓")
        self.assertEqual([p.name for p in target.parent.iterdir()], ["b.txt"])


# --------------------------------------------------------------------------- loop verdict


class LoopVerdictBranchesTest(TmpMixin, unittest.TestCase):
    def setUp(self):
        self.base = self.tmpdir()
        self.plan = self.base / "docs" / "autopilot" / "PLAN.md"

    def activate(self, **extra) -> None:
        st = {"active": True, "iterations": 0, "max_iterations": 50, "plan": "docs/autopilot/PLAN.md"}
        st.update(extra)
        xt.write_state(st, self.base)

    def evidence(self, task: str, code: int, cmd: str) -> None:
        write(
            self.base / ".autopilot" / "evidence" / f"{task}.json",
            json.dumps({"task": task, "exit_code": code, "cmd": cmd}),
        )

    def test_inactive_and_blocked(self):
        self.assertEqual(xt.loop_verdict(self.base)["verdict"], "inactive")
        self.activate(blocked=True, blocked_reason="cần người")
        v = xt.loop_verdict(self.base)
        self.assertEqual((v["verdict"], v["reason"]), ("blocked", "cần người"))

    def test_inactive_reports_final_verdict_of_previous_loop(self):
        # ADR-0009: phiên sau thấy vòng trước kết thúc thế nào (vd còn việc chờ người).
        self.activate(active=False, final_verdict={"verdict": "done-pending-human", "reason": "chờ T-002"})
        v = xt.loop_verdict(self.base)
        self.assertEqual(
            (v["verdict"], v["reason"]), ("inactive", "vòng lặp đã kết thúc — done-pending-human: chờ T-002")
        )
        self.activate(active=False, final_verdict="hỏng")
        self.assertEqual(xt.loop_verdict(self.base)["reason"], "vòng lặp chưa bật")

    def test_deferred_task_is_skipped_then_pending_human(self):
        write(self.plan, "- [ ] `T-001` deploy — Gate: `true`\n- [ ] `T-002` việc — Gate: `true`\n")
        self.activate(deferred={"T-001": {"reason": "cần khoá thật"}})
        v = xt.loop_verdict(self.base)
        self.assertEqual((v["verdict"], v["task"]), ("continue", "T-002"))
        write(self.plan, "- [ ] `T-001` deploy — Gate: `true`\n- [x] `T-002` việc — Gate: `true`\n")
        self.evidence("T-002", 0, "true")
        v = xt.loop_verdict(self.base)
        self.assertEqual(v["verdict"], "done-pending-human")
        self.assertEqual(v["pending_human"], [{"id": "T-001", "reason": "cần khoá thật"}])
        self.assertIn("chờ người 1 việc: T-001 (cần khoá thật)", v["reason"])
        # Người làm xong, agent tick kèm bằng chứng → defer đã thoả, verdict thường.
        write(self.plan, "- [x] `T-001` deploy — Gate: `true`\n- [x] `T-002` việc — Gate: `true`\n")
        self.evidence("T-001", 0, "true")
        self.assertEqual(xt.loop_verdict(self.base)["verdict"], "done")

    def test_deferred_blueprint_must_and_corrupt_deferred(self):
        write(self.plan, "- [x] `T-001` xong — Gate: `true`\n")
        self.evidence("T-001", 0, "true")
        write(self.base / "BP.md", "- [ ] `AAA-001` **MUST** a → Kiểm: t\n- [ ] `AAA-002` **MUST** b → Kiểm: t\n")
        self.activate(blueprint="BP.md", deferred={"AAA-001": "không phải object"})
        v = xt.loop_verdict(self.base)
        self.assertEqual((v["verdict"], v["task"]), ("continue", "AAA-002"))
        self.activate(blueprint="BP.md", deferred={"AAA-001": "x", "AAA-002": {"reason": "diễn tập DR thật"}})
        v = xt.loop_verdict(self.base)
        self.assertEqual(v["verdict"], "done-pending-human")
        self.assertEqual([p["reason"] for p in v["pending_human"]], ["", "diễn tập DR thật"])
        # deferred hỏng (không phải dict) ≡ không có; ID chờ người đã đóng thì không tính.
        self.activate(blueprint="BP.md", deferred=["AAA-001"])
        self.assertEqual(xt.loop_verdict(self.base)["task"], "AAA-001")
        self.activate(deferred={"T-009": {"reason": "đã xong từ trước"}})
        self.assertEqual(xt.loop_verdict(self.base)["verdict"], "done")

    def test_repeated_failure_blocks(self):
        self.activate(same_failure_count=3, last_failure_task="T-001")
        v = xt.loop_verdict(self.base)
        self.assertEqual(v["verdict"], "blocked")
        self.assertIn("cùng một lỗi lặp 3 lần (T-001)", v["reason"])

    def test_budget_iterations(self):
        self.activate(iterations=2, max_iterations=2)
        v = xt.loop_verdict(self.base)
        self.assertEqual(v["verdict"], "budget")
        self.assertIn("trần 2 vòng", v["reason"])

    def test_budget_deadline_passed_and_future(self):
        write(self.plan, "- [ ] `T-001` việc — Gate: `true`\n")
        self.activate(deadline="2000-01-01T00:00:00+00:00")
        v = xt.loop_verdict(self.base)
        self.assertEqual(v["verdict"], "budget")
        self.assertIn("quá hạn 2000-01-01", v["reason"])
        self.activate(deadline="2999-01-01T00:00:00+00:00")
        self.assertEqual(xt.loop_verdict(self.base)["verdict"], "continue")

    def test_missing_plan_and_empty_plan(self):
        self.activate()
        v = xt.loop_verdict(self.base)
        self.assertEqual(v["verdict"], "blocked")
        self.assertIn("không thấy PLAN", v["reason"])
        write(self.plan, "# PLAN\n\nkhông có task nào\n")
        v = xt.loop_verdict(self.base)
        self.assertEqual(v["verdict"], "blocked")
        self.assertIn("PLAN không có task", v["reason"])

    def test_waived_task_is_skipped_and_next_open_is_continue(self):
        write(self.plan, "- [~] `T-001` bỏ qua — Bỏ: trùng T-002\n- [ ] `T-002` làm tiếp — Gate: `true`\n")
        self.activate()
        v = xt.loop_verdict(self.base)
        self.assertEqual((v["verdict"], v["task"]), ("continue", "T-002"))

    def test_only_waived_tasks_is_done(self):
        write(self.plan, "- [~] `T-001` bỏ qua — Bỏ: khách huỷ yêu cầu\n")
        self.activate()
        self.assertEqual(xt.loop_verdict(self.base)["verdict"], "done")

    def test_waived_task_without_reason_is_verify(self):
        # PLAN: `[~]` bỏ phải ghi lý do — trước đây bỏ không lý do vẫn tính "xong".
        write(self.plan, "- [~] `T-001` báo cáo công nợ — Gate: `true`\n")
        self.activate()
        v = xt.loop_verdict(self.base)
        self.assertEqual((v["verdict"], v["task"]), ("verify", "T-001"))
        self.assertIn("Bỏ: <lý do>", v["reason"])

    def test_evidence_older_than_loop_init_is_verify(self):
        # Bằng chứng của vòng trước (PLAN cũ cùng ID) không được tính cho PLAN mới.
        write(self.plan, "- [x] `T-001` việc mới — Gate: `npm test`\n")
        write(
            self.base / ".autopilot" / "evidence" / "T-001.json",
            json.dumps({"task": "T-001", "exit_code": 0, "cmd": "npm test", "finished": "2026-10-01T00:00:00+00:00"}),
        )
        self.activate(started="2026-10-15T00:00:00+00:00")
        v = xt.loop_verdict(self.base)
        self.assertEqual((v["verdict"], v["task"]), ("verify", "T-001"))
        self.assertIn("trước lần loop init", v["reason"])
        self.activate(started="2026-09-30T00:00:00+00:00")
        self.assertEqual(xt.loop_verdict(self.base)["verdict"], "done")

    def test_evidence_age_compares_instants_not_strings(self):
        """AUD-CODE-008: bằng chứng 10:00+07:00 (= 03:00Z) cũ hơn `loop init` 05:00Z dù chuỗi so ra lớn hơn."""
        write(self.plan, "- [x] `T-001` việc — Gate: `npm test`\n")
        write(
            self.base / ".autopilot" / "evidence" / "T-001.json",
            json.dumps(
                {
                    "task": "T-001",
                    "exit_code": 0,
                    "cmd": "npm test",
                    "started": "2026-10-16T09:59:00+07:00",
                    "finished": "2026-10-16T10:00:00+07:00",
                }
            ),
        )
        self.activate(started="2026-10-16T05:00:00+00:00")
        v = xt.loop_verdict(self.base)
        self.assertEqual((v["verdict"], v["task"]), ("verify", "T-001"))
        self.assertIn("trước lần loop init", v["reason"])

    def test_evidence_tamper(self):
        """AUD-HAR-024: bằng chứng ghi tay có thời điểm tương lai hoặc kết thúc trước khi bắt đầu → verify, không done."""
        write(self.plan, "- [x] `T-001` việc — Gate: `npm test`\n")
        ev = self.base / ".autopilot" / "evidence" / "T-001.json"
        self.activate(started="2026-09-30T00:00:00+00:00")
        soon = (_dt.datetime.now(_dt.timezone(_dt.timedelta(hours=-12))) + _dt.timedelta(hours=10)).isoformat()
        for bad in (
            {"finished": "2099-01-01T00:00:00+00:00"},
            {"started": "2026-10-10T00:00:00+00:00", "finished": "2026-10-09T00:00:00+00:00"},
            {"finished": soon},  # tương lai viết ở múi giờ khác (reviewer #61: so chuỗi ISO lệch theo offset)
            {"finished": "hôm qua"},
        ):
            with self.subTest(bad):
                write(ev, json.dumps({"task": "T-001", "exit_code": 0, "cmd": "npm test", **bad}))
                v = xt.loop_verdict(self.base)
                self.assertEqual((v["verdict"], v.get("task")), ("verify", "T-001"))
                self.assertIn("thời điểm", v["reason"])

    def test_evidence_time_other_offset_is_fine(self):
        """Thời điểm thật viết ở múi giờ khác (+07:00) không bị coi là tương lai."""
        now7 = _dt.datetime.now(_dt.timezone(_dt.timedelta(hours=7))).replace(microsecond=0).isoformat()
        self.assertEqual(xt._evidence_time_problem({"started": now7, "finished": now7}), "")

    def test_gate_with_dev_credentials_matches_redacted_evidence(self):
        # Bằng chứng lưu lệnh đã che bí mật; so với Gate thô thì `verify` mãi, đốt hết ngân sách vòng.
        gate = "DATABASE_URL=postgres://app:app@localhost:5432/test true"
        write(self.plan, f"- [x] `T-001` db — Gate: `{gate}`\n")
        self.activate()
        with redirect_stdout(io.StringIO()):
            self.assertEqual(xt.loop_record("T-001", [gate], self.base), 0)
        self.assertIn("***", xt.read_evidence("T-001", self.base)["cmd"])
        self.assertEqual(xt.loop_verdict(self.base)["verdict"], "done")

    def test_blueprint_bad_lines_keep_loop_going(self):
        write(self.plan, "- [x] `T-001` xong — Gate: `echo ok`\n")
        self.evidence("T-001", 0, "echo ok")
        write(self.base / "BLUEPRINT.md", "| MUST | 2 |\n- [x] `A-001` **MUST** a\n- [-] `A-002` **MUST** b\n")
        self.activate(blueprint="BLUEPRINT.md")
        v = xt.loop_verdict(self.base)
        self.assertEqual(v["verdict"], "continue")
        self.assertIn("sai định dạng", v["reason"])

    def test_malformed_plan_task_lines_are_verify(self):
        for bad in (
            "- [ ] T-002 thiếu backtick",
            "  - [ ] `T-003` thụt lề",
            "- [ ] `T-04` ID ngắn",
            "- [-] `T-005` ô lạ",
        ):
            with self.subTest(bad=bad):
                write(self.plan, f"- [x] `T-001` xong — Gate: `echo ok`\n{bad}\n")
                self.evidence("T-001", 0, "echo ok")
                self.activate()
                v = xt.loop_verdict(self.base)
                self.assertEqual(v["verdict"], "verify")
                self.assertIn("sai định dạng", v["reason"])

    def test_ticked_task_evidence_paths(self):
        write(self.plan, "- [x] `T-001` xong — Gate: `echo ok`\n")
        self.activate()
        v = xt.loop_verdict(self.base)
        self.assertEqual((v["verdict"], v["task"]), ("verify", "T-001"))
        self.assertIn("chưa có bằng chứng xanh", v["reason"])
        self.evidence("T-001", 1, "echo ok")
        self.assertIn("chưa có bằng chứng xanh", xt.loop_verdict(self.base)["reason"])
        self.evidence("T-001", 0, "echo khac")
        self.assertIn("bằng chứng chạy lệnh khác", xt.loop_verdict(self.base)["reason"])
        self.evidence("T-001", 0, "echo   'ok'")  # nháy khác Gate: không cùng lệnh (AUD-CODE-014)
        self.assertIn("bằng chứng chạy lệnh khác", xt.loop_verdict(self.base)["reason"])
        self.evidence("T-001", 0, "  echo   ok ")  # chỉ khoảng trắng ngoài nháy khác
        self.assertEqual(xt.loop_verdict(self.base)["verdict"], "done")

    def test_blueprint_open_must_continues(self):
        write(self.plan, "- [x] `T-001` xong — Gate: `true`\n")
        self.evidence("T-001", 0, "true")
        write(
            self.base / "BP.md",
            "- [ ] `AAA-001` **MUST** a → Kiểm: t\n- [ ] `AAA-002` **MUST** b → Kiểm: t\n- [ ] `AAA-003` **SHOULD** c\n",
        )
        self.activate(blueprint="BP.md")
        v = xt.loop_verdict(self.base)
        self.assertEqual((v["verdict"], v["task"]), ("continue", "AAA-001"))
        self.assertIn("còn 2 mục MUST", v["reason"])

    def test_blueprint_bad_waiver_continues(self):
        write(self.plan, "- [x] `T-001` xong — Gate: `true`\n")
        self.evidence("T-001", 0, "true")
        write(self.base / "BP.md", "- [~] `AAA-001` **MUST** a → Kiểm: t\n- [x] `AAA-002` **MUST** b → Kiểm: t\n")
        self.activate(blueprint="BP.md")
        v = xt.loop_verdict(self.base)
        self.assertEqual(v["verdict"], "continue")
        self.assertIn("mục miễn trừ không hợp lệ: AAA-001 (dòng 1)", v["reason"])

    def test_blueprint_clean_or_missing_is_done(self):
        write(self.plan, "- [x] `T-001` xong — Gate: `true`\n")
        self.evidence("T-001", 0, "true")
        write(self.base / "BP.md", "- [x] `AAA-001` **MUST** a\n- [~] `AAA-002` **MAY** b — Miễn: không cần\n")
        self.activate(blueprint="BP.md")
        v = xt.loop_verdict(self.base)
        self.assertEqual(
            (v["verdict"], v["reason"]), ("done", "mọi task có bằng chứng xanh và blueprint không còn MUST mở")
        )
        # T-1503: blueprint đã khai ở loop init mà mất → `verify` (trước đây `done` — xoá blueprint là qua cổng).
        self.activate(blueprint="khong-co.md")
        v = xt.loop_verdict(self.base)
        self.assertEqual(v["verdict"], "verify")
        self.assertIn("blueprint khong-co.md đã khai ở loop init nhưng mất", v["reason"])
        self.activate()
        v = xt.loop_verdict(self.base)
        self.assertEqual(v["verdict"], "done")
        self.assertIn("loop init không có --blueprint", v["reason"])
        self.assertNotIn("không còn MUST mở", v["reason"])

    def test_scope_contract_written_by_loop_init(self):
        """T-1503 (REC-02): `loop init` ghi `scope` {blueprint, profile, scale, rev, gate_floor} vào state; không khai
        blueprint hoặc blueprint không đọc được → không có scope."""
        write(self.plan, "- [ ] `T-001` a — Gate: `true`\n")
        bp = "---\nkind: blueprint\nprofile: web-app\nscale: M\n---\nnội dung\n"
        write(self.base / "BLUEPRINT.md", bp)
        write(self.base / "pyproject.toml", "[project]\n")
        args = lambda **kw: argparse.Namespace(  # noqa: E731
            plan="docs/autopilot/PLAN.md",
            blueprint=None,
            hours=None,
            max_iterations=None,
            single_session=True,
            force=True,
            framework=ROOT / "framework",
            **kw,
        )
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(xt._loop_init(args(), self.base), 0)
            self.assertNotIn("scope", xt.read_state(self.base))
            self.assertEqual(
                xt._loop_init(argparse.Namespace(**{**vars(args()), "blueprint": "khong-co.md"}), self.base),
                2,
            )
            self.assertEqual(
                xt._loop_init(argparse.Namespace(**{**vars(args()), "blueprint": "BLUEPRINT.md"}), self.base),
                0,
            )
        sc = xt.read_state(self.base)["scope"]
        self.assertEqual((sc["blueprint"], sc["profile"], sc["scale"]), ("BLUEPRINT.md", "web-app", "M"))
        self.assertEqual(sc["rev"], xt.hashlib.sha256(bp.encode()).hexdigest()[:16])
        self.assertEqual(sc["gate_floor"], ["format_check", "coverage", "typecheck", "e2e"])
        # blueprint không đọc được (nhị phân) → không có scope, không sập
        (self.base / "BIN.md").write_bytes(b"\xff\xfe\x00")
        self.assertEqual(xt.build_scope(self.base, "BIN.md"), {})
        self.assertEqual(xt.build_scope(self.base, None), {})

    def test_scope_blueprint_lost_keeps_gate_floor_and_verifies(self):
        """Xoá/hỏng blueprint không hạ được sàn Gate (đọc từ scope) và verdict không còn `done`; đổi quy mô/hồ sơ → verify."""
        write(self.plan, "- [x] `T-001` xong — Gate: `true`\n")
        self.evidence("T-001", 0, "true")
        write(self.base / "BLUEPRINT.md", "---\nprofile: cli-tool\nscale: M\n---\n- [x] `AAA-001` **MUST** a\n")
        write(self.base / "xt.yaml", "test: pytest\n")
        sc = xt.build_scope(self.base, "BLUEPRINT.md")
        self.activate(blueprint="BLUEPRINT.md", scope=sc)
        self.assertEqual(xt.loop_verdict(self.base)["verdict"], "done")
        issues_before = xt.gate_floor_issues(self.base)
        self.assertTrue(issues_before)
        # đổi quy mô M → S ngầm: sàn Gate sẽ biến mất → verify
        write(self.base / "BLUEPRINT.md", "---\nprofile: cli-tool\nscale: S\n---\n- [x] `AAA-001` **MUST** a\n")
        v = xt.loop_verdict(self.base)
        self.assertEqual(v["verdict"], "verify")
        self.assertIn("đổi quy mô/hồ sơ so với lúc loop init (M/cli-tool → S/cli-tool)", v["reason"])
        # blueprint bị xoá: verify + sàn Gate vẫn đòi như cũ
        (self.base / "BLUEPRINT.md").unlink()
        v = xt.loop_verdict(self.base)
        self.assertEqual(v["verdict"], "verify")
        self.assertIn("mất/không đọc được", v["reason"])
        self.assertEqual(xt.blueprint_scale(self.base), ("M", "cli-tool"))
        self.assertEqual(xt.gate_floor_issues(self.base), issues_before)
        # frontmatter hỏng (mất khoá scale) → coi là đổi quy mô
        write(self.base / "BLUEPRINT.md", "không có frontmatter\n")
        self.assertIn("(M/cli-tool → —/—)", xt.loop_verdict(self.base)["reason"])

    def test_scope_state_migration(self):
        """State cũ (không có `scope`): verdict không kiểm drift quy mô (chỉ kiểm file còn); `loop resume` điền scope từ
        blueprint hiện tại; không khai blueprint thì không thêm."""
        write(self.plan, "- [x] `T-001` xong — Gate: `true`\n")
        self.evidence("T-001", 0, "true")
        write(self.base / "BLUEPRINT.md", "---\nprofile: cli-tool\nscale: L\n---\n- [x] `AAA-001` **MUST** a\n")
        self.activate(blueprint="BLUEPRINT.md")  # không scope
        self.assertEqual(xt.loop_verdict(self.base)["verdict"], "done")
        write(self.base / "BLUEPRINT.md", "---\nprofile: cli-tool\nscale: S\n---\n- [x] `AAA-001` **MUST** a\n")
        self.assertEqual(xt.loop_verdict(self.base)["verdict"], "done")  # state cũ không có gì để so
        write(self.base / "BLUEPRINT.md", "---\nprofile: cli-tool\nscale: L\n---\n- [x] `AAA-001` **MUST** a\n")
        with redirect_stdout(io.StringIO()):
            self.assertEqual(xt._loop_resume(argparse.Namespace(reason="x"), self.base), 0)
        self.assertEqual(xt.read_state(self.base)["scope"]["scale"], "L")
        self.assertEqual(xt.loop_verdict(self.base)["verdict"], "done")
        self.activate()
        with redirect_stdout(io.StringIO()):
            xt._loop_resume(argparse.Namespace(reason="x"), self.base)
        self.assertNotIn("scope", xt.read_state(self.base))

    def test_checks_run_in_priority_order(self):
        """Điều kiện dừng thắng nhau theo thứ tự: bị chặn > lỗi lặp > hết vòng > quá hạn > PLAN > blueprint."""
        past = "2000-01-01T00:00:00+00:00"
        self.activate(
            blocked=True,
            blocked_reason="r",
            same_failure_count=3,
            last_failure_task="T-009",
            iterations=50,
            deadline=past,
        )
        self.assertEqual(xt.loop_verdict(self.base), {"verdict": "blocked", "reason": "r"})
        self.activate(same_failure_count=3, last_failure_task="T-009", iterations=50, deadline=past)
        self.assertIn("cùng một lỗi lặp 3 lần (T-009)", xt.loop_verdict(self.base)["reason"])
        self.activate(iterations=50, deadline=past)
        self.assertEqual(xt.loop_verdict(self.base), {"verdict": "budget", "reason": "đã chạm trần 50 vòng"})
        self.activate(deadline=past)  # PLAN chưa có nhưng hạn đã quá: budget thắng blocked-vì-thiếu-PLAN
        self.assertEqual(xt.loop_verdict(self.base)["verdict"], "budget")
        write(self.base / "BP.md", "- [ ] `AAA-001` **MUST** a → Kiểm: t\n")
        write(self.plan, "- [x] `T-001` xong — Gate: `true`\n- [ ] `T-002` làm — Gate: `true`\n")
        self.activate(blueprint="BP.md")  # task tick thiếu bằng chứng đứng trước task chưa làm
        self.assertEqual(xt.loop_verdict(self.base)["verdict"], "verify")
        self.evidence("T-001", 0, "true")  # task chưa làm thắng blueprint còn MUST mở
        v = xt.loop_verdict(self.base)
        self.assertEqual((v["verdict"], v["task"]), ("continue", "T-002"))


# --------------------------------------------------------------------------- loop verify (LOOP-DESIGN-022)


class LoopVerifyTest(TmpMixin, unittest.TestCase):
    """Kiểm lại cuối: chạy lại mọi Gate trên cây hiện tại trước khi Stop hook nhận `done`."""

    def git(self, *args: str) -> None:
        subprocess.run(["git", "-C", str(self.base), *args], check=True, capture_output=True)

    def setUp(self):
        self.base = self.tmpdir()
        self.git("init", "-q")
        for k, v in (("user.email", "t@x"), ("user.name", "t"), ("commit.gpgsign", "false")):
            self.git("config", k, v)
        write(self.base / ".gitignore", ".autopilot/\n")
        write(self.base / "ok.txt", "1\n")
        self.plan = self.base / "docs" / "autopilot" / "PLAN.md"
        write(self.plan, "- [x] `T-001` a — Gate: `test -f ok.txt`\n- [x] `T-002` b — Gate: `test  -f ok.txt`\n")
        self.git("add", "-A")
        self.git("commit", "-qm", "init")
        for t in ("T-001", "T-002"):
            write(
                self.base / ".autopilot" / "evidence" / f"{t}.json",
                json.dumps({"task": t, "exit_code": 0, "cmd": "test -f ok.txt"}),
            )
        xt.write_state(
            {"active": True, "iterations": 0, "max_iterations": 50, "plan": "docs/autopilot/PLAN.md"}, self.base
        )

    def verify(self) -> tuple[int, str]:
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = xt.loop_verify(self.base, run_all=True)
        return rc, buf.getvalue()

    def test_zero_tests_red_in_verify_and_blueprint_checks(self):
        """`loop verify` và lệnh `— Kiểm:` của blueprint đi cùng `run_gate_shell`: `Ran 0 tests` + exit 0 là đỏ (T-1501)."""
        write(self.plan, "- [x] `T-001` a — Gate: `echo 'Ran 0 tests'`\n")
        self.git("commit", "-qam", "plan")
        rc, out = self.verify()
        self.assertEqual(rc, 1)
        self.assertIn("verify T-001: exit 5", out)
        rec = json.loads((self.base / ".autopilot" / "verified.json").read_text())
        self.assertEqual(rec["results"][0]["exit_code"], 5)
        self.assertIn(xt.ZERO_TESTS_MARK, rec["results"][0]["output_tail"])
        checks = xt.run_blueprint_checks([{"id": "X-001", "cmd": "echo 'Ran 0 tests'"}], self.base, 30)
        self.assertEqual(checks[0]["exit_code"], 5)

    def test_stop_requires_final_verify_then_passes(self):
        self.assertEqual(xt.loop_verdict(self.base)["verdict"], "done")  # bằng chứng từng task vẫn đủ
        out, _ = xt.hook_stop("{}", self.base)
        self.assertIn("loop verify", json.loads(out)["reason"])
        rc, text = self.verify()
        self.assertEqual(rc, 0, text)
        self.assertIn("XANH (1 Gate)", text)  # hai task cùng lệnh (khác khoảng trắng) → chạy một lần
        self.assertEqual(xt.hook_stop("{}", self.base), ("", 0))
        self.assertFalse(xt.read_state(self.base)["active"])

    def test_partial_verify_not_enough_for_done(self):
        # D-084: verify giữ Gate theo digest (mode=changed) chỉ dùng giữa vòng; `done` đòi lần cuối `--all`.
        with redirect_stdout(io.StringIO()):
            self.assertEqual(xt.loop_verify(self.base), 0)
        why = xt.final_check(self.base) or ""
        self.assertIn("chỉ chạy Gate có đầu vào đổi", why)
        self.assertIn("`python3 scripts/xt.py loop verify --all`", why)  # lệnh đúng repo — review #190
        out, _ = xt.hook_stop("{}", self.base)
        self.assertIn("loop verify --all", json.loads(out)["reason"])
        self.assertTrue(xt.read_state(self.base)["active"])
        rec_path = self.base / ".autopilot" / xt.VERIFIED_FILE
        rec = json.loads(rec_path.read_text(encoding="utf-8"))
        del rec["mode"]  # bản ghi cũ không có `mode` → coi là một phần (chiều chặt)
        xt.write_atomic(rec_path, json.dumps(rec) + "\n")
        self.assertIn("loop verify --all", xt.final_check(self.base) or "")
        self.assertEqual(self.verify()[0], 0)
        self.assertIsNone(xt.final_check(self.base))

    def test_tree_change_after_verify_invalidates(self):
        self.assertEqual(self.verify()[0], 0)
        write(self.base / "new.txt", "x\n")  # file chưa track đổi cây
        self.assertIn("chưa kiểm lại cuối", xt.final_check(self.base) or "")
        self.assertIn("`python3 scripts/xt.py loop verify --all`", xt.final_check(self.base) or "")
        self.assertEqual(self.verify()[0], 0)
        self.assertIsNone(xt.final_check(self.base))
        write(self.base / "ok.txt", "2\n")  # sửa file đã track
        self.assertIsNotNone(xt.final_check(self.base))

    def test_red_gate_blocks_with_failing_task(self):
        (self.base / "ok.txt").unlink()
        rc, text = self.verify()
        self.assertEqual(rc, 1)
        self.assertIn("ĐỎ", text)
        self.assertIn("kiểm lại cuối ĐỎ (T-001)", xt.final_check(self.base) or "")
        out, _ = xt.hook_stop("{}", self.base)
        self.assertEqual(json.loads(out)["decision"], "block")

    def test_blueprint_checks_run_in_final_verify(self):
        # LOOP-DESIGN-023: `loop verify` chạy cả `— Kiểm: `…`` của mục [x] trong blueprint khai ở loop init.
        write(self.base / "BP.md", "- [x] `A-001` **MUST** a — Kiểm: `test -f ok.txt`\n- [x] `A-002` **MUST** b\n")
        self.git("add", "-A")
        self.git("commit", "-qm", "bp")
        st = xt.read_state(self.base)
        st["blueprint"] = "BP.md"
        xt.write_state(st, self.base)
        rc, text = self.verify()
        self.assertEqual(rc, 0, text)
        self.assertIn("[xt] verify blueprint A-001: exit 0", text)
        self.assertIn("XANH (1 Gate + 1 lệnh kiểm blueprint)", text)
        rec = json.loads((self.base / ".autopilot" / xt.VERIFIED_FILE).read_text(encoding="utf-8"))
        self.assertEqual([(r["id"], r["exit_code"]) for r in rec["blueprint"]], [("A-001", 0)])
        write(self.base / "BP.md", "- [x] `A-001` **MUST** a — Kiểm: `test -f khong-co.txt`\n")
        self.git("commit", "-qam", "bp đỏ")
        rc, text = self.verify()
        self.assertEqual(rc, 1)
        self.assertIn("ĐỎ (1 Gate + 1 lệnh kiểm blueprint)", text)
        self.assertIn("kiểm lại cuối ĐỎ (A-001)", xt.final_check(self.base) or "")
        # Blueprint ở thư mục con: lệnh chạy trong thư mục chứa nó, cùng cwd với `blueprint-status --run` (review #106).
        write(self.base / "docs" / "BP.md", "- [x] `A-001` **MUST** a — Kiểm: `test -f BP.md && test ! -f ok.txt`\n")
        self.git("add", "-A")
        self.git("commit", "-qm", "bp con")
        st["blueprint"] = "docs/BP.md"
        xt.write_state(st, self.base)
        self.assertEqual(self.verify()[0], 0)
        st["blueprint"] = "khong-co.md"  # blueprint mất giữa chừng: không kiểm được, không khai sạch
        xt.write_state(st, self.base)
        rc, text = self.verify()
        self.assertEqual(rc, 0)
        self.assertNotIn("lệnh kiểm blueprint", text)

    def test_gate_floor_blocks_final_verify(self):
        # LOOP-HARNESS-023: quy mô M — khoá sàn thiếu → kiểm lại cuối ĐỎ; khai rồi thì `loop verify` CHẠY lệnh sàn.
        write(self.base / "BLUEPRINT.md", "---\nkind: blueprint\nprofile: cli-tool\nscale: M\n---\n")
        write(self.base / "xt.yaml", "lint: ruff check .\ntest: pytest\n")
        self.git("add", "-A")
        self.git("commit", "-qm", "bp")
        rc, text = self.verify()
        self.assertEqual(rc, 1)
        self.assertIn("[xt] verify sàn Gate: quy mô M: xt.yaml thiếu hoặc no-op `format_check`", text)
        rec = json.loads((self.base / ".autopilot" / xt.VERIFIED_FILE).read_text(encoding="utf-8"))
        self.assertEqual((len(rec["gate_floor"]), rec["gate_floor_runs"]), (2, []))
        self.assertIn("kiểm lại cuối ĐỎ (sàn Gate M/L chưa đạt (LOOP-HARNESS-023))", xt.final_check(self.base) or "")
        out, _ = xt.hook_stop("{}", self.base)
        self.assertEqual(json.loads(out)["decision"], "block")
        # Khai đủ: lệnh trùng Gate không chạy lại; lệnh đỏ làm kiểm lại cuối ĐỎ và nêu khoá.
        write(self.base / "xt.yaml", "format_check: test -f ok.txt\ncoverage: test -f cov.txt\n")
        self.git("commit", "-qam", "sàn")
        rc, text = self.verify()
        self.assertEqual(rc, 1)
        self.assertIn("[xt] verify sàn Gate `coverage`: exit 1", text)
        self.assertNotIn("sàn Gate `format_check`", text)  # trùng Gate `test -f ok.txt` của T-001
        self.assertIn("kiểm lại cuối ĐỎ (sàn `coverage`)", xt.final_check(self.base) or "")
        write(self.base / "xt.yaml", "format_check: test -f ok.txt\ncoverage: test -f xt.yaml\n")
        self.git("commit", "-qam", "cov")
        self.assertEqual(self.verify()[0], 0)

    def test_gate_that_changes_tree_is_not_ok(self):
        write(self.plan, "- [x] `T-001` a — Gate: `echo y >> ok.txt`\n")
        self.git("commit", "-qam", "plan")
        rc, text = self.verify()
        self.assertEqual(rc, 1)
        self.assertIn("Gate/lệnh sàn làm đổi cây", text)
        rec = json.loads((self.base / ".autopilot" / xt.VERIFIED_FILE).read_text(encoding="utf-8"))
        self.assertEqual((rec["ok"], rec["stable"]), (False, False))
        self.assertIn("kiểm lại cuối ĐỎ (cây đổi khi chạy Gate)", xt.final_check(self.base) or "")

    def test_big_untracked_file_and_bad_timeout(self):
        with unittest.mock.patch.object(xt, "FINGERPRINT_MAX_FILE", 1):
            write(self.base / "big.bin", "xyz")
            self.assertIsNotNone(xt.tree_fingerprint(self.base))
        with unittest.mock.patch.dict(os.environ, {"XT_RECORD_TIMEOUT": "x"}), redirect_stderr(io.StringIO()):
            self.assertEqual(xt.loop_verify(self.base), 2)

    def test_no_git_or_no_plan_and_cli(self):
        other = self.tmpdir()
        self.assertIsNone(xt.tree_fingerprint(other))
        self.assertIsNone(xt.final_check(other))
        with redirect_stdout(io.StringIO()):
            self.assertEqual(xt.loop_verify(other), 0)  # không có PLAN: 0 Gate, xanh rỗng
        buf = io.StringIO()
        with unittest.mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(self.base)}), redirect_stdout(buf):
            self.assertEqual(xt.main(["loop", "verify"]), 0)
        self.assertIn("kiểm lại cuối: XANH", buf.getvalue())


# --------------------------------------------------------------------------- loop record / helpers


def real_autopilot_dirs() -> list[Path]:
    """`.autopilot/` mà `loop record` sẽ ghi khi test quên đặt gốc tạm: theo `CLAUDE_PROJECT_DIR` (nếu có) và theo cwd."""
    dirs = {ROOT / ".autopilot"}
    with unittest.mock.patch.dict(os.environ):
        env = os.environ.pop("CLAUDE_PROJECT_DIR", None)
        dirs.add(xt.project_dir() / ".autopilot")
    if env:
        dirs.add(Path(env).resolve() / ".autopilot")
    return sorted(dirs)


def autopilot_snapshot(dirs: list[Path]) -> dict:
    """{đường dẫn: (mtime_ns, cỡ)} của mọi file trong `dirs` — so trước/sau để bắt test ghi vào sổ thật (hook không còn
    cache bytecode ở `.autopilot/pycache` — review PR #182 — nên không bỏ qua thư mục nào)."""
    snap: dict = {}
    for d in dirs:
        for p in d.rglob("*") if d.exists() else ():
            if p.is_file():
                st = p.stat()
                snap[str(p)] = (st.st_mtime_ns, st.st_size)
    return snap


def autopilot_changes(before: dict, dirs: list[Path]) -> list[str]:
    after = autopilot_snapshot(dirs)
    return sorted(k for k in before.keys() | after.keys() if before.get(k) != after.get(k))


class RealAutopilotUntouchedMixin(unittest.TestCase):
    """AUD-TEST-009: test không được ghi `.autopilot/` của repo thật (bằng chứng giả vào sổ thật, trái ADR-0026).
    Gọi `guard_real_autopilot()` đầu `setUp`: chụp trước, kiểm lại sau mỗi test (cleanup)."""

    def guard_real_autopilot(self) -> None:
        dirs = real_autopilot_dirs()
        before = autopilot_snapshot(dirs)
        self.addCleanup(
            lambda: self.assertEqual(
                autopilot_changes(before, dirs),
                [],
                "test đã ghi vào .autopilot/ thật — đặt CLAUDE_PROJECT_DIR/base tạm",
            )
        )


class RealAutopilotGuardTest(TmpMixin, unittest.TestCase):
    def test_snapshot_sees_new_and_changed_files(self):
        d = self.tmpdir() / ".autopilot"
        self.assertEqual(autopilot_snapshot([d]), {})
        before = autopilot_snapshot([d])
        (d / "evidence").mkdir(parents=True)
        write(d / "evidence" / "T-002.json", "{}")
        write(d / "pycache" / "x.pyc", "b")  # hook không còn cache bytecode: file ở đây cũng tính
        self.assertEqual(
            autopilot_changes(before, [d]), [str(d / "evidence" / "T-002.json"), str(d / "pycache" / "x.pyc")]
        )
        before = autopilot_snapshot([d])
        self.assertEqual(autopilot_changes(before, [d]), [])
        write(d / "runs.jsonl", "{}\n")
        self.assertEqual(autopilot_changes(before, [d]), [str(d / "runs.jsonl")])
        write(d / "evidence" / "T-002.json", "{} ")  # ghi đè bằng chứng có sẵn
        self.assertIn(str(d / "evidence" / "T-002.json"), autopilot_changes(before, [d]))
        with unittest.mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(d.parent)}):
            self.assertIn(d.resolve(), real_autopilot_dirs())
        self.assertIn(ROOT / ".autopilot", real_autopilot_dirs())


class LoopRecordBranchesTest(TmpMixin, RealAutopilotUntouchedMixin, unittest.TestCase):
    def setUp(self):
        self.guard_real_autopilot()
        self.base = self.tmpdir()
        # git không được dò ngược lên thư mục cha (TMPDIR nằm trong một repo → _git_head nhặt nhầm SHA)
        ceiling = unittest.mock.patch.dict(os.environ, {"GIT_CEILING_DIRECTORIES": str(self.base.parent)})
        ceiling.start()
        self.addCleanup(ceiling.stop)
        write(self.base / "docs" / "autopilot" / "PLAN.md", "- [ ] `T-001` việc — Gate: `true`\n")
        xt.write_state({"active": True, "plan": "docs/autopilot/PLAN.md"}, self.base)
        patcher = unittest.mock.patch.dict(os.environ)
        patcher.start()
        self.addCleanup(patcher.stop)
        os.environ.pop("XT_RECORD_TIMEOUT", None)
        os.environ["CLAUDE_PROJECT_DIR"] = str(self.base)  # AUD-TEST-009: CLI `xt.main([...])` ghi vào gốc tạm

    def record(self, cmd, task="T-001"):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = xt.loop_record(task, cmd, self.base)
        return code, out.getvalue(), err.getvalue()

    def test_record_ticks_plan_task_on_green(self):
        """T-1719 (D-113): exit 0 với lệnh khớp Gate → máy tự tick `[x]`; lệnh khác Gate, đỏ, task đã đóng hay `--no-tick`
        → giữ nguyên PLAN."""
        plan = self.base / "docs" / "autopilot" / "PLAN.md"
        write(plan, "- [ ] `T-001` a — Gate: `true`\n- [ ] `T-002` b — Gate: `true`\n- [ ] `T-003` c — Gate: `false`\n")
        self.record(["echo", "khac"], "T-001")  # lệnh khác Gate: bằng chứng không khớp → không tick
        self.assertIn("- [ ] `T-001`", plan.read_text(encoding="utf-8"))
        code, out, _ = self.record(["true"], "T-001")
        self.assertEqual(code, 0)
        self.assertIn("đã tick [x]", out)
        self.assertEqual(
            plan.read_text(encoding="utf-8"),
            "- [x] `T-001` a — Gate: `true`\n- [ ] `T-002` b — Gate: `true`\n- [ ] `T-003` c — Gate: `false`\n",
        )
        self.assertNotIn("đã tick", self.record(["true"], "T-001")[1])  # đã đóng → không ghi lại
        self.record(["false"], "T-003")
        self.assertIn("- [ ] `T-003`", plan.read_text(encoding="utf-8"))
        with redirect_stdout(io.StringIO()):
            xt.loop_record("T-002", ["true"], self.base, tick=False)
        self.assertIn("- [ ] `T-002`", plan.read_text(encoding="utf-8"))
        with redirect_stdout(io.StringIO()):
            self.assertEqual(xt.main(["loop", "record", "--task", "T-002", "--no-tick", "--", "true"]), 0)
        self.assertIn("- [ ] `T-002`", plan.read_text(encoding="utf-8"))
        self.assertFalse(xt.tick_plan_task(self.base, {}, "T-002", "true"))  # không state/PLAN → không đụng file

    def test_tick_keeps_crlf_and_file_mode(self):
        """Review #191: tự tick ghi lại cả file → giữ CRLF và quyền file (tệp tạm của mkstemp là 0600)."""
        plan = self.base / "docs" / "autopilot" / "PLAN.md"
        plan.parent.mkdir(parents=True, exist_ok=True)
        plan.write_bytes("- [ ] `T-001` a — Gate: `true`\r\n- [ ] `T-002` b — Gate: `true`\r\n".encode("utf-8"))
        plan.chmod(0o644)
        code, out, _ = self.record(["true"], "T-001")
        self.assertEqual(code, 0)
        self.assertIn("đã tick [x]", out)
        raw = plan.read_bytes()
        self.assertEqual((raw.count(b"\r\n"), raw.count(b"\n")), (2, 2))
        self.assertTrue(raw.startswith(b"- [x] `T-001`"), raw)
        self.assertEqual(plan.stat().st_mode & 0o777, 0o644)

    def test_tick_writes_through_plan_symlink(self):
        """Review #191: PLAN là symlink → tick ghi vào file thật, liên kết còn nguyên (trước: thay bằng file thường)."""
        plan = self.base / "docs" / "autopilot" / "PLAN.md"
        real = self.base / "real" / "PLAN.md"
        real.parent.mkdir(parents=True, exist_ok=True)
        real.write_text("- [ ] `T-001` a — Gate: `true`\n", encoding="utf-8")
        plan.parent.mkdir(parents=True, exist_ok=True)
        plan.unlink(missing_ok=True)
        plan.symlink_to(real)
        code, out, _ = self.record(["true"], "T-001")
        self.assertEqual((code, "đã tick [x]" in out), (0, True))
        self.assertTrue(plan.is_symlink())
        self.assertEqual(real.read_text(encoding="utf-8"), "- [x] `T-001` a — Gate: `true`\n")

    def test_same_command_unbalanced_quote_falls_back_to_strip(self):
        self.assertTrue(xt.same_command("echo 'a", "  echo 'a  "))
        self.assertFalse(xt.same_command("echo 'a", "echo 'b"))
        self.assertTrue(xt.same_command("echo  a", "echo a"))
        self.assertFalse(xt.same_command("echo  a", "echo 'a'"))  # nháy có nghĩa (AUD-CODE-014)

    def test_command_identity_quotes_and_operators_are_significant(self):
        """T-1502 → AUD-CODE-014 (🔴 cổng giả xanh): `same_command` so DẠNG CHUẨN `canonical_command` — chỉ dãy space/tab
        ngoài nháy là tự do; nháy (`$X` ≠ `"$X"` ≠ `'$X'`), khoảng trắng cạnh toán tử (`2>f` ≠ `2 >f`), heredoc, NBSP,
        gán biến có nháy đều có nghĩa. Token identity cũ coi `test -n $X` ≡ `test -n "$X"` (X rỗng: exit 0 và 1) nên
        lệnh xanh giả được nhận làm bằng chứng cho Gate khác — bash chạy khác thì KHÔNG bao giờ là một lệnh."""
        same = (
            ("echo  a", "echo a"),
            ("x  &&  y", "x && y"),
            ("", "   "),
            ("\tpytest  -q\t", "pytest -q"),
            ('echo "a  b"', 'echo "a  b"'),
            ("echo ok \n  false", "echo ok\t\n false"),
            ("a\\ b", "a\\ b"),
            ("cat  <<EOF\n a  b\nEOF  ", "cat <<EOF\n a  b\nEOF"),
        )
        diff = (
            ("test -n $X", 'test -n "$X"'),  # X rỗng: exit 0 / exit 1
            ("echo $X", "echo '$X'"),
            ('echo "$X"', "echo '$X'"),
            ("echo $@", 'echo "$@"'),
            ("echo `a`", 'echo "`a`"'),
            ("X=1 cmd", "'X=1' cmd"),
            ("exec {fd}>f", "exec {fd} >f"),
            ("make test", "make\u00a0test"),
            ("cat <<EOF", "cat <<'EOF'"),
            ("echo  a", "echo 'a'"),
            ("echo '*'", "echo *"),
            ("echo 2>f", "echo 2 >f"),
            ("a <<EOF", "a < <EOF"),
            ("a && b", "a & & b"),
            ("a | b", "a|b"),  # bash chạy như nhau nhưng không cùng văn bản: nhận chặt hơn, không bao giờ lỏng hơn
            ("echo a #b", "echo a '#b'"),
            ("echo a", "echo a b"),
            ("echo ok\nfalse", "echo ok false"),
            ("echo ok\n  false", "echo ok\nfalse"),
            ("cat <<EOF\na  b\nEOF", "cat <<EOF\na b\nEOF"),  # thân heredoc là dữ liệu
            ("cat <<EOF\n  a\nEOF", "cat <<EOF\na\nEOF"),
            ("cat <<<'a  b'", "cat <<< 'a  b'"),
            ("a\\ b", "a b"),
            ("echo 'a", "echo 'b"),
        )
        for a, b in same:
            self.assertTrue(xt.same_command(a, b), (a, b))
            self.assertTrue(xt.same_command(b, a), (b, a))
        for a, b in diff:
            self.assertFalse(xt.same_command(a, b), (a, b))
            self.assertFalse(xt.same_command(b, a), (b, a))
        self.assertEqual(xt.canonical_command('  a "x  y" \\  b\t c  '), 'a "x  y" \\  b c')
        self.assertEqual(xt.canonical_command('echo "a\\"b" \'c\\\'  '), 'echo "a\\"b" \'c\\\'')
        self.assertEqual(xt.canonical_command("x\\"), "x\\")  # backslash cuối chuỗi: chép nguyên
        self.assertEqual(xt.canonical_command("cat <<'EOF'\n it's\nEOF"), "cat <<'EOF'\n it's\nEOF")  # nháy trong thân
        for bad in ("echo 'a", 'echo "a\\" b'):  # `\"` không đóng nháy kép
            with self.assertRaises(ValueError):
                xt.canonical_command(bad)

    def test_audit_code_014_quoted_gate_rejects_unquoted_evidence(self):
        """AUD-CODE-014 (audit 2026-10-21 tại ec4c7d2): Gate `test -n "$X"` đỏ với X rỗng mà `loop record` chạy
        `test -n $X` (xanh) → không tick, verdict `verify`; `loop verify --all` chạy CẢ HAI Gate chỉ khác nháy (trước
        đây khử trùng lặp bằng token identity nên Gate đỏ đứng sau Gate "cùng lệnh" xanh không bao giờ chạy)."""
        plan = self.base / "docs" / "autopilot" / "PLAN.md"
        write(plan, '- [ ] `T-001` a — Gate: `test -n "$X"`\n')
        with unittest.mock.patch.dict(os.environ, {"X": ""}):
            code, out, _ = self.record(["test -n $X"], "T-001")
            self.assertEqual((code, "đã tick" in out), (0, False))
            self.assertIn("- [ ] `T-001`", plan.read_text(encoding="utf-8"))
            self.assertFalse(xt.tick_plan_task(self.base, {"plan": "docs/autopilot/PLAN.md"}, "T-001", "test -n $X"))
            self.assertTrue(xt.tick_plan_task(self.base, {"plan": "docs/autopilot/PLAN.md"}, "T-001", 'test -n  "$X"'))
            v = xt.loop_verdict(self.base)
            self.assertEqual((v["verdict"], v["task"]), ("verify", "T-001"))
            tasks = [
                {"id": "T-001", "state": "x", "gate": "test -n $X", "files": []},
                {"id": "T-002", "state": "x", "gate": 'test -n "$X"', "files": []},
            ]
            with redirect_stdout(io.StringIO()):
                results = xt._verify_gates(self.base, tasks, 10, True)
        got = [(r["task"], r["exit_code"], r.get("kept", False)) for r in results]
        self.assertEqual(got, [("T-001", 0, False), ("T-002", 1, False)])

    def test_command_identity_evidence_sha_and_verdict(self):
        """Evidence ghi `cmd_sha256` của lệnh nguyên văn; verdict: dấu vân tay khớp PLAN → không so dạng chuẩn; khác → so
        `same_command` (chỉ khoảng trắng ngoài nháy khác vẫn nhận; nháy khác → `verify`)."""
        write(self.base / "docs" / "autopilot" / "PLAN.md", '- [x] `T-001` việc — Gate: `echo "$HOME"`\n')
        self.assertEqual(self.record(['echo "$HOME"'])[0], 0)
        ev = xt.read_evidence("T-001", self.base)
        self.assertEqual(ev["cmd_sha256"], xt.cmd_sha256('echo "$HOME"'))
        self.assertEqual(len(ev["cmd_sha256"]), 64)
        self.assertEqual(xt.loop_verdict(self.base)["verdict"], "done")
        self.assertEqual(self.record(['echo  "$HOME"'])[0], 0)  # khác dấu vân tay (khoảng trắng), cùng dạng chuẩn
        self.assertEqual(xt.loop_verdict(self.base)["verdict"], "done")
        self.assertEqual(self.record(["echo $HOME"])[0], 0)  # bỏ nháy kép: bung + tách từ — KHÔNG phải Gate khai
        v = xt.loop_verdict(self.base)
        self.assertEqual((v["verdict"], v["task"]), ("verify", "T-001"))
        self.assertIn("bằng chứng chạy lệnh khác", v["reason"])
        self.assertEqual(self.record(["echo '$HOME'"])[0], 0)  # chữ, không bung: cũng không phải Gate khai
        self.assertEqual(xt.loop_verdict(self.base)["verdict"], "verify")
        # evidence cũ không có cmd_sha256 (bản < 3.9): chỉ so ngữ nghĩa
        ev = xt.read_evidence("T-001", self.base)
        ev.pop("cmd_sha256")
        ev["cmd"] = 'echo "$HOME"'
        write(self.base / ".autopilot" / "evidence" / "T-001.json", json.dumps(ev))
        self.assertEqual(xt.loop_verdict(self.base)["verdict"], "done")

    def test_command_identity_blueprint_checks_not_merged(self):
        """`run_blueprint_checks` chỉ dùng chung kết quả cho lệnh CÙNG nghĩa."""
        checks = [{"id": "A", "cmd": "echo '$X'"}, {"id": "B", "cmd": 'echo "$X"'}, {"id": "C", "cmd": "echo  '$X'"}]
        with unittest.mock.patch.object(xt, "run_gate_shell", return_value=(0, "ok")) as run:
            out = xt.run_blueprint_checks(checks, self.base, 30)
        self.assertEqual(run.call_count, 2)
        self.assertEqual([c["exit_code"] for c in out], [0, 0, 0])

    def test_invalid_timeout_env_returns_2_and_writes_nothing(self):
        os.environ["XT_RECORD_TIMEOUT"] = "abc"
        code, out, err = self.record(["true"])
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("XT_RECORD_TIMEOUT phải là số giây", err)
        self.assertFalse((self.base / ".autopilot" / "evidence").exists())

    def test_timeout_records_124_and_counts_failure(self):
        os.environ["XT_RECORD_TIMEOUT"] = "1"
        self.addCleanup(os.environ.pop, "XT_RECORD_TIMEOUT", None)
        with unittest.mock.patch("xt._git_head", return_value=None):
            code, out, _ = self.record(["sleep 9"])
            self.assertEqual(code, 124)
            self.assertIn("timeout", out)
            code, _, _ = self.record(["sleep 9"])
        ev = xt.read_evidence("T-001", self.base)
        self.assertEqual((ev["exit_code"], ev["cmd"], ev["head"]), (124, "sleep 9", None))
        self.assertIn("timeout", ev["output_tail"])
        st = xt.read_state(self.base)
        self.assertEqual(st["same_failure_count"], 2)  # cùng chữ ký lỗi hai lần liền
        self.assertEqual(st["last_failure_task"], "T-001")

    def test_timeout_stops_whole_process_group(self):
        """review hotel-manager #119: hết giờ → SIGTERM cả nhóm (trap của script chạy), không đáp thì SIGKILL; tiến trình con
        nền không sống sót (trước đây chỉ bash bị SIGKILL, app tạm và khoá cổng còn lại)."""
        pid_file = self.base / "bg.pid"
        cmd = f"sleep 30 & echo $! > {pid_file}; trap 'echo don-dep; exit 1' TERM; sleep 30 & wait"
        code, out = xt.run_gate_shell(cmd, self.base, 1)
        self.assertEqual(code, 124)
        self.assertIn("đã dừng cả nhóm tiến trình", out)
        self.assertIn("don-dep", out)  # trap TERM của script đã chạy
        bg = int(pid_file.read_text())
        with self.assertRaises(ProcessLookupError):
            for _ in range(50):
                os.kill(bg, 0)
                time.sleep(0.1)
        with unittest.mock.patch.object(xt, "GATE_KILL_GRACE", 1):  # bỏ qua TERM → SIGKILL sau ân hạn
            code, out = xt.run_gate_shell("trap '' TERM; sleep 30 & wait; sleep 30", self.base, 1)
        self.assertEqual(code, 124)

    def test_non_utf8_output_does_not_raise(self):
        code, out = xt.run_gate_shell("printf 'a\\xffb'; exit 3", self.base, 10)
        self.assertEqual((code, out), (3, "a\ufffdb"))

    def test_timeout_returns_when_detached_child_holds_output(self):
        """review #220: con `setsid` (khác phiên, như app server) còn giữ stdout — trước đây `communicate()` chờ EOF mãi."""
        pid_file = self.base / "det.pid"
        cmd = f"setsid sleep 40 & echo $! > {pid_file}; echo bat-dau; sleep 30"
        t0 = time.monotonic()
        with unittest.mock.patch.object(xt, "GATE_KILL_GRACE", 1):
            code, out = xt.run_gate_shell(cmd, self.base, 1)
        self.assertLess(time.monotonic() - t0, 10)
        self.assertEqual(code, 124)
        self.assertIn("bat-dau", out)
        with contextlib.suppress(ProcessLookupError, ValueError, OSError):
            os.kill(int(pid_file.read_text()), 9)  # dọn tiến trình tách phiên của test

    def test_failure_then_success_resets_counter_and_redacts(self):
        secret = "gh" + "p_" + "x" * 36
        code, out, _ = self.record([f"echo token={secret}; exit 3"])
        self.assertEqual(code, 3)
        self.assertNotIn(secret, out)
        ev_raw = (self.base / ".autopilot" / "evidence" / "T-001.json").read_text(encoding="utf-8")
        self.assertNotIn(secret, ev_raw)
        self.assertEqual(xt.read_state(self.base)["same_failure_count"], 1)
        code, _, _ = self.record(["true"])
        self.assertEqual(code, 0)
        st = xt.read_state(self.base)
        self.assertEqual(st["same_failure_count"], 0)
        self.assertIsNone(st["last_failure_signature"])

    def test_zero_tests_red_exit0_with_ran_0_tests_is_red(self):
        """REC-01/T-1501: unittest 3.11 exit 0 khi `-k` không khớp test nào (`Ran 0 tests`) — xanh giả; nay exit 5 (như
        3.12+), evidence ghi `zero_tests_red` + lý do; `Ran N tests` (N > 0) và `0 passed` của pytest (tự exit 5) không bắt."""
        code, out, _ = self.record(["echo 'Ran 0 tests in 0.001s'; echo OK"])
        self.assertEqual(code, xt.ZERO_TESTS_EXIT)
        self.assertIn("zero_tests_red", out)
        ev = xt.read_evidence("T-001", self.base)
        self.assertEqual((ev["exit_code"], ev["zero_tests_red"]), (5, True))
        self.assertIn("Ran 0 tests", ev["output_tail"])
        self.assertIn(xt.ZERO_TESTS_MARK, ev["output_tail"])
        self.assertEqual(xt.read_state(self.base)["same_failure_count"], 1)
        self.assertEqual(self.record(["echo 'Ran 10 tests in 0.1s'; echo OK"])[0], 0)
        self.assertNotIn("zero_tests_red", xt.read_evidence("T-001", self.base))
        self.assertEqual(self.record(["echo '0 passed in 0.01s'"])[0], 0)  # pytest: tự exit 5 khi không test
        self.assertEqual(self.record(["echo '  Ran 0 tests'"])[0], 0)  # chỉ dòng tổng kết ở đầu dòng
        self.assertEqual(self.record(["echo 'Ran 0 tests'; exit 5"])[0], 5)  # 3.12+: giữ nguyên, không có dấu
        self.assertNotIn("zero_tests_red", xt.read_evidence("T-001", self.base))
        self.assertEqual(xt.zero_tests_red(0, "x\nRan 0 tests\n"), (5, f"x\nRan 0 tests\n{xt.ZERO_TESTS_MARK}\n"))
        self.assertEqual(xt.zero_tests_red(1, "Ran 0 tests"), (1, "Ran 0 tests"))

    def test_pipeline_failure_is_not_green(self):
        # pipefail: Gate `test | tee log` đỏ khi test đỏ — /bin/sh lấy exit của `tee` → từng ghi exit 0 (xanh giả).
        code, _, _ = self.record(["false | cat"])
        self.assertEqual(code, 1)
        self.assertEqual(xt.read_evidence("T-001", self.base)["exit_code"], 1)
        self.assertEqual(self.record(["true | cat"])[0], 0)

    def test_missing_bash_records_127(self):
        with (
            unittest.mock.patch("xt.subprocess.Popen", side_effect=FileNotFoundError("bash")),
            unittest.mock.patch("xt._git_head", return_value=None),
        ):
            code, out, _ = self.record(["true"])
        self.assertEqual(code, 127)
        self.assertIn("cần bash", out)
        self.assertEqual(xt.read_evidence("T-001", self.base)["exit_code"], 127)

    def test_runs_log_and_stats(self):
        # LOOP-DESIGN-024: evidence bị ghi đè, runs.jsonl giữ mọi lần chạy → loop stats đếm được lần đỏ trước khi xanh.
        st = xt.read_state(self.base)
        st.update({"started": "2026-10-18T00:00:00+00:00", "iterations": 5, "max_iterations": 40})
        st["deferred"] = {"T-009": {"reason": "người"}}
        xt.write_state(st, self.base)
        for task, cmd in (("T-001", ["false"]), ("T-001", ["false"]), ("T-001", ["true"]), ("T-002", ["true"])):
            self.record(cmd, task)
        self.record(["false"], "T-003")
        runs = self.base / ".autopilot" / xt.RUNS_FILE
        with open(runs, "a", encoding="utf-8") as fh:  # dòng hỏng, không phải object, vòng trước: bỏ qua
            fh.write("{hỏng\n[1]\n" + json.dumps({"task": "T-001", "exit_code": 0, "loop": "cũ"}) + "\n")
        rows = xt.read_runs(self.base)
        self.assertEqual(len(rows), 6)
        self.assertIsNone(rows[2]["signature"])
        self.assertEqual(len(rows[0]["signature"]), 16)
        s = xt.loop_stats(self.base)
        self.assertEqual(s["tasks"]["T-001"], {"runs": 3, "failed": 2, "runs_to_green": 3, "executors": []})
        self.assertEqual((s["escalated"], s["escalation_rate"]), ([], 0.0))
        self.assertEqual((s["task_count"], s["runs"], s["failed_runs"]), (3, 5, 3))
        self.assertEqual(s["first_pass_rate"], 0.333)
        self.assertEqual((s["needs_3_plus"], s["never_green"]), (["T-001"], ["T-003"]))
        self.assertEqual((s["iterations"], s["max_iterations"], s["deferred"], s["blocked"]), (5, 40, ["T-009"], False))
        self.assertEqual(xt.loop_stats(self.base, all_loops=True)["tasks"]["T-001"]["runs"], 4)
        empty = self.tmpdir()
        self.assertEqual(xt.read_runs(empty), [])
        self.assertIsNone(xt.loop_stats(empty)["first_pass_rate"])

    def test_executor_tier_escalation_and_stats(self):
        """ADR-0029: `(exec: deep)` → tầng sâu ngay; tầng mặc định đỏ 2 lần cùng task trong vòng này → `loop status`
        chuyển cấp lên `executor-deep`; `--executor` ghi vào evidence + runs.jsonl; `loop stats` đếm task đã chuyển cấp."""
        write(
            self.base / "docs" / "autopilot" / "PLAN.md",
            """
            ### Lát 1 — nền
            - [ ] `T-001` việc (exec: deep) — Gate: `true`
            - [ ] `T-002` việc thường — Gate: `true`
            """,
        )
        st = xt.read_state(self.base)
        st["started"] = "2026-10-19T00:00:00+00:00"
        xt.write_state(st, self.base)
        v = xt.loop_verdict(self.base)
        self.assertEqual(
            (v["task"], v["tier"], v["executor"], v["escalated"]), ("T-001", "deep", "executor-deep", False)
        )
        self.assertIn("tầng sâu theo PLAN", v["reason"])
        self.record(["true"], "T-001")
        write(
            self.base / "docs" / "autopilot" / "PLAN.md",
            """
            ### Lát 1 — nền
            - [x] `T-001` việc (exec: deep) — Gate: `true`
            - [ ] `T-002` việc thường — Gate: `true`
            """,
        )
        v = xt.loop_verdict(self.base)
        self.assertEqual((v["task"], v["tier"], v["executor"], v["escalated"]), ("T-002", "default", "executor", False))
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            xt.loop_record("T-002", ["sh -c 'echo ea; exit 1'"], self.base, "executor")
            xt.loop_record("T-002", ["sh -c 'echo eb; exit 1'"], self.base, "executor")  # chữ ký khác → chưa blocked
        ev = xt.read_evidence("T-002", self.base)
        self.assertEqual(ev["executor"], "executor")
        v = xt.loop_verdict(self.base)
        self.assertEqual((v["executor"], v["escalated"], v["default_failures"]), ("executor-deep", True, 2))
        self.assertIn("chuyển cấp: tầng mặc định đỏ 2 lần", v["reason"])
        with redirect_stdout(out), redirect_stderr(err):
            xt.loop_record("T-002", ["sh -c 'echo ec; exit 1'"], self.base, "executor-deep")  # đỏ tầng sâu không đếm
        self.assertEqual(xt.loop_verdict(self.base)["default_failures"], 2)
        rows = [r for r in xt.read_runs(self.base) if r["task"] == "T-002"]
        self.assertEqual([r["executor"] for r in rows], ["executor", "executor", "executor-deep"])
        s = xt.loop_stats(self.base)
        self.assertEqual(s["tasks"]["T-002"]["executors"], ["executor", "executor-deep"])
        self.assertEqual((s["escalated"], s["escalation_rate"]), (["T-002"], 0.5))
        self.assertEqual(s["tasks"]["T-001"]["executors"], [])
        with redirect_stdout(out):
            self.assertEqual(xt._loop_stats(argparse.Namespace(json=False, all=False), self.base), 0)
        self.assertIn("Chuyển cấp lên tầng sâu: 1 task (50%): T-002", out.getvalue())
        with redirect_stdout(out), redirect_stderr(err):  # xanh rồi lại đỏ một lần: chỉ đếm chuỗi đỏ sau lần xanh cuối
            xt.loop_record("T-002", ["true"], self.base, "executor", tick=False)  # không tick: còn đỏ tiếp bên dưới
            xt.loop_record("T-002", ["sh -c 'echo ed; exit 1'"], self.base, "executor")
        v = xt.loop_verdict(self.base)
        self.assertEqual((v["escalated"], v["default_failures"]), (False, 1))
        with redirect_stdout(out):  # CLI: --executor đi vào evidence; giá trị lạ bị argparse từ chối
            self.assertEqual(
                xt.main(["loop", "record", "--task", "T-002", "--executor", "executor-deep", "--", "true"]), 0
            )
        with self.assertRaises(SystemExit):
            with redirect_stderr(err):
                xt.main(["loop", "record", "--task", "T-002", "--executor", "opus", "--", "true"])

    def test_milestone_done_marks_section_transition(self):
        """Task kế là task đầu của mục mới và mọi task trước đã đóng → `milestone_done` = mục trước (audit delta theo mốc)."""
        write(
            self.base / "docs" / "autopilot" / "PLAN.md",
            """
            ## Task
            ### Lát 1 — skeleton
            - [x] `T-001` a — Gate: `true`
            - [~] `T-002` b — Bỏ: không cần — Gate: `true`
            ### Lát 2 — tính năng
            - [ ] `T-003` c — Gate: `true`
            - [ ] `T-004` d — Gate: `true`
            """,
        )
        self.record(["true"], "T-001")
        tasks = xt.parse_plan(self.base / "docs" / "autopilot" / "PLAN.md")
        self.assertEqual([t["section"] for t in tasks], ["Lát 1 — skeleton"] * 2 + ["Lát 2 — tính năng"] * 2)
        self.assertEqual(xt.milestone_done(tasks, tasks[2]), "Lát 1 — skeleton")
        self.assertIsNone(xt.milestone_done(tasks, tasks[3]))  # cùng mục với task trước
        self.assertIsNone(xt.milestone_done(tasks, tasks[0]))  # task đầu PLAN
        v = xt.loop_verdict(self.base)
        self.assertEqual((v["task"], v["milestone_done"], v["milestone_audit"]), ("T-003", "Lát 1 — skeleton", "now"))
        self.assertIn("mốc «Lát 1 — skeleton» đã xong → audit delta", v["reason"])
        write(self.base / "xt.yaml", "delivery_phase: build\n")  # ADR-0033: pha build gom audit theo mốc về trước G7
        v = xt.loop_verdict(self.base)
        self.assertEqual((v["milestone_done"], v["milestone_audit"]), ("Lát 1 — skeleton", "g7"))
        self.assertIn("pha build: audit delta gom về trước G7 (ADR-0033)", v["reason"])
        self.assertNotIn("audit delta trước khi sang mốc kế", v["reason"])
        for phase in ("Build", "prod", "harden", ""):  # giá trị lạ/vắng = harden → audit theo mốc như cũ (ADR-0031)
            write(self.base / "xt.yaml", f"delivery_phase: {phase}\n")
            self.assertEqual(xt.loop_verdict(self.base)["milestone_audit"], "now", phase)
        (self.base / "xt.yaml").write_bytes(
            b"delivery_phase: build\n\xfa"
        )  # không đọc được → now, không vỡ (review #189)
        self.assertEqual(xt.loop_verdict(self.base)["milestone_audit"], "now")
        (self.base / "xt.yaml").unlink()
        write(
            self.base / "docs" / "autopilot" / "PLAN.md",
            "- [ ] `T-001` a — Gate: `true`\n### X\n- [ ] `T-002` b — Gate: `true`\n",
        )
        tasks = xt.parse_plan(self.base / "docs" / "autopilot" / "PLAN.md")
        self.assertIsNone(xt.milestone_done(tasks, tasks[1]))  # task trước không thuộc mục nào
        self.assertNotIn("milestone_done", xt.loop_verdict(self.base))
        write(
            self.base / "docs" / "autopilot" / "PLAN.md",
            "### A\n- [ ] `T-001` a — Gate: `true`\n### B\n- [ ] `T-002` b — Gate: `true`\n",
        )
        tasks = xt.parse_plan(self.base / "docs" / "autopilot" / "PLAN.md")
        self.assertIsNone(xt.milestone_done(tasks, tasks[1]))  # task trước còn mở
        self.assertEqual(xt.milestone_done(tasks, tasks[1], {"T-001": {"reason": "người"}}), "A")  # defer = đóng (#169)
        st = xt.read_state(self.base)
        st["deferred"] = {"T-001": {"reason": "người"}}
        xt.write_state(st, self.base)
        self.assertEqual(xt.loop_verdict(self.base)["milestone_done"], "A")
        write(self.base / "docs" / "autopilot" / "PLAN.md", "- [ ] `T-001` a — Gate: `docker compose exec: deep`\n")
        self.assertEqual(
            xt.parse_plan(self.base / "docs" / "autopilot" / "PLAN.md")[0]["tier"], "default"
        )  # không đọc trong Gate

    def test_runs_log_is_fail_open_and_does_not_follow_symlink(self):
        # Review #109: runs.jsonl hỏng (là thư mục) không làm vỡ loop record, đếm lỗi lặp vẫn tăng; symlink không bị ghi theo.
        (self.base / ".autopilot" / xt.RUNS_FILE).mkdir(parents=True)
        code, _, err = self.record(["false"])
        self.assertEqual(code, 1)
        self.assertIn("⚠ không ghi được .autopilot/runs.jsonl", err)
        self.assertEqual(xt.read_state(self.base)["same_failure_count"], 1)
        (self.base / ".autopilot" / xt.RUNS_FILE).rmdir()
        victim = self.base / "victim.txt"
        victim.write_text("gốc\n", encoding="utf-8")
        (self.base / ".autopilot" / xt.RUNS_FILE).symlink_to(victim)
        code, _, err = self.record(["true"])
        self.assertEqual(code, 0)
        self.assertIn("⚠ không ghi được", err)
        self.assertEqual(victim.read_text(encoding="utf-8"), "gốc\n")

    def test_record_without_state_still_writes_evidence(self):
        bare = self.tmpdir()
        with redirect_stdout(io.StringIO()):
            self.assertEqual(xt.loop_record("T-009", ["true"], bare), 0)
        self.assertEqual(xt.read_evidence("T-009", bare)["exit_code"], 0)
        self.assertIsNone(xt.read_state(bare))

    def test_git_head_failures_return_none(self):
        for exc in (FileNotFoundError("git"), subprocess.TimeoutExpired(cmd="git", timeout=10)):
            with unittest.mock.patch("xt.subprocess.run", side_effect=exc):
                self.assertIsNone(xt._git_head(self.base))

    def test_git_head_real_repo_and_non_repo(self):
        self.assertIsNone(xt._git_head(self.base))  # thư mục tạm không phải repo → stdout rỗng
        subprocess.run(["git", "init", "-q", str(self.base)], check=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(self.base),
                "-c",
                "user.name=t",
                "-c",
                "user.email=t@e.x",
                "-c",
                "commit.gpgsign=false",
                "commit",
                "-q",
                "--allow-empty",
                "-m",
                "x",
            ],
            check=True,
        )
        head = xt._git_head(self.base)
        self.assertRegex(head or "", r"^[0-9a-f]{40}$")


class GuardChokePointTest(TmpMixin, unittest.TestCase):
    """LOOP-STOP-027 (rà stored 01 §3g): lệnh Gate/`Kiểm:`/xt.yaml do model viết mà harness chạy phải qua guard."""

    def setUp(self):
        self.base = self.tmpdir()
        (self.base / ".claude" / "hooks").mkdir(parents=True)
        self.canary = self.base / "ran"
        patcher = unittest.mock.patch.dict(os.environ, {"XT_GUARD_POLICY": ""})
        patcher.start()
        self.addCleanup(patcher.stop)

    def only_base_guard(self) -> None:
        """Chỉ guard của dự án tạm (bỏ guard cùng bản cài xt.py của repo này)."""
        p = unittest.mock.patch.object(xt, "guard_paths", lambda base: [base / xt.GUARD_FILE])
        p.start()
        self.addCleanup(p.stop)

    def use_real_guard(self) -> None:
        (self.base / xt.GUARD_FILE).write_bytes((ROOT / xt.GUARD_FILE).read_bytes())

    def fake_guard(self, body: str) -> None:
        self.only_base_guard()
        (self.base / xt.GUARD_FILE).write_text(textwrap.dedent(body), encoding="utf-8")

    def test_denied_command_is_not_run(self):
        self.use_real_guard()
        code, out = xt.run_gate_shell(f"touch {self.canary} && git push origin main", self.base, 30)
        self.assertEqual(code, 126)
        self.assertIn("LOOP-STOP-027", out)
        self.assertFalse(self.canary.exists())
        self.assertFalse((self.base / ".claude" / "hooks" / "__pycache__").exists())  # không bẩn cây (loop verify)

    def test_restores_dont_write_bytecode(self):
        self.use_real_guard()
        keep = sys.dont_write_bytecode
        self.addCleanup(setattr, sys, "dont_write_bytecode", keep)
        sys.dont_write_bytecode = False
        xt.guard_block("true", self.base)
        self.assertFalse(sys.dont_write_bytecode)

    def test_allowed_command_runs(self):
        self.use_real_guard()
        code, _ = xt.run_gate_shell(f"touch {self.canary}", self.base, 30)
        self.assertEqual(code, 0)
        self.assertTrue(self.canary.exists())

    def test_strict_policy_blocks_ask(self):
        self.use_real_guard()
        os.environ["XT_GUARD_POLICY"] = "strict"
        self.assertTrue(xt.guard_block("npm publish", self.base))  # ask ở strict → harness không hỏi được → chặn
        os.environ["XT_GUARD_POLICY"] = ""
        self.assertEqual(xt.guard_block("npm publish", self.base), "")  # mặc định: ask không nguy hiểm → cho chạy

    def test_falls_back_to_install_guard(self):
        # CLAUDE_PROJECT_DIR trỏ thư mục không có guard → vẫn kiểm bằng guard cùng bản cài xt.py (review #117).
        (self.base / ".claude" / "hooks").rmdir()
        self.assertTrue(xt.guard_block("git push origin main", self.base))
        self.assertIn(ROOT / xt.GUARD_FILE, xt.guard_paths(self.base))

    def test_permissive_project_guard_does_not_win(self):
        # guard giả ở dự án (cho qua mọi thứ) không thắng guard của bản cài (review #117 lần 2).
        (self.base / xt.GUARD_FILE).write_text(
            "def bash_decision(c, r, w):\n    return {'decision': ''}\n\ndef apply_policy(o):\n    return o\n",
            encoding="utf-8",
        )
        self.assertTrue(xt.guard_block("git push origin main", self.base))
        self.assertEqual(xt.guard_block("pytest -q", self.base), "")

    def test_missing_guard_everywhere(self):
        self.only_base_guard()
        self.assertEqual(xt.guard_block("git push origin main", self.base), "")  # chưa cài harness → chạy
        (self.base / ".claude" / "settings.json").write_text("{}", encoding="utf-8")
        self.assertIn("thiếu .claude/hooks/guard.py", xt.guard_block("true", self.base))  # harness có, guard bị gỡ

    def test_guard_errors_follow_failure_decision(self):
        self.fake_guard(
            """
            def bash_decision(c, r, w):
                raise RuntimeError("hỏng")

            def _failure_decision(mode, payload, cmd):
                return {"decision": "deny" if "gh pr merge" in cmd else "", "reason": "lỗi merge"}

            def apply_policy(o):
                return o
            """
        )
        self.assertEqual(xt.guard_block("gh pr merge 1", self.base), "lỗi merge")  # merge: đóng như hook
        self.assertEqual(xt.guard_block("pytest", self.base), "")  # lệnh khác: fail-open về luồng

    def test_broken_guard_module_fails_open(self):
        self.fake_guard("def bash_decision(:\n")
        self.assertEqual(xt.guard_block("git push origin main", self.base), "")
        self.fake_guard("def bash_decision(c, r, w):\n    raise RuntimeError()\n")  # không có _failure_decision
        self.assertEqual(xt.guard_block("x", self.base), "")

    def test_apply_policy_error_keeps_raw_decision(self):
        self.fake_guard(
            """
            def bash_decision(c, r, w):
                return {"decision": "deny"}

            def apply_policy(o):
                raise RuntimeError()
            """
        )
        self.assertEqual(xt.guard_block("x", self.base), "guard chặn")

    def test_guard_check_command(self):
        self.use_real_guard()
        env = unittest.mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(self.base)})
        env.start()
        self.addCleanup(env.stop)
        err = io.StringIO()
        with redirect_stderr(err):
            self.assertEqual(xt.main(["guard-check", "--", "git", "push", "origin", "main"]), 126)
            self.assertEqual(xt.main(["guard-check", "pytest -q"]), 0)
        self.assertIn("LOOP-STOP-027", err.getvalue())

    def test_guard_check_stdin_loads_guard_once_for_every_line(self):
        """T-1715: `guard-check --stdin` — các lệnh cách nhau bằng NUL, một lệnh bị cấm → 126 kèm lệnh đó; mọi lệnh được
        chạy → in `guard-check: N lệnh`; mỗi guard nạp một lần cho cả danh sách (không phải một lần mỗi lệnh). Lệnh
        nhiều dòng là MỘT lệnh: tiếp dòng không né được guard, `\\r` không tách lệnh (review #191)."""
        self.use_real_guard()
        env = unittest.mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(self.base)})
        env.start()
        self.addCleanup(env.stop)

        def run(text: str) -> tuple[int, str, str]:
            out, err = io.StringIO(), io.StringIO()
            stdin = io.TextIOWrapper(io.BytesIO(text.encode("utf-8")), encoding="utf-8")
            with redirect_stdout(out), redirect_stderr(err), unittest.mock.patch("sys.stdin", stdin):
                rc = xt.main(["guard-check", "--stdin"])
            return rc, out.getvalue(), err.getvalue()

        rc, out, err = run("pytest -q\0git push origin main\0ruff check .\0")
        self.assertEqual(rc, 126)
        self.assertIn("LOOP-STOP-027", err)
        self.assertIn("lệnh: git push origin main", err)
        self.assertNotIn("ruff check", err)  # chỉ lệnh bị cấm được nêu
        self.assertEqual(out, "")
        self.assertEqual(run("pytest -q\0\0  \0ruff check .\0")[:2], (0, "guard-check: 2 lệnh\n"))
        self.assertEqual(run("")[:2], (0, "guard-check: 0 lệnh\n"))
        self.assertEqual(run("git push --fo\\\nrce origin main\0")[0], 126)  # tiếp dòng: vẫn là `git push --force`
        self.assertEqual(run("echo a\rgit push --force origin main\0")[0], 0)  # `\r` là chữ của echo, không tách lệnh
        with unittest.mock.patch.object(xt, "_load_guard", wraps=xt._load_guard) as load:
            self.assertEqual(xt.guard_blocks(["pytest -q"], self.base), [""])
            once = load.call_count
            self.assertGreaterEqual(once, 1)
            self.assertEqual(xt.guard_blocks(["pytest -q", "git push origin main", "ruff check ."], self.base)[0], "")
            self.assertEqual(load.call_count, 2 * once)  # 3 lệnh: vẫn một lần nạp mỗi guard


class GateFloorCliTest(TmpMixin, unittest.TestCase):
    """AUD-XFEAT-020 (audit 2026-10-21): khoá sàn M/L khai riêng (`format_check`, `coverage`) đỏ mà `require`, `gate-par`,
    `doctor`, `ci-check` đều xanh — chỉ `loop verify` chạy sàn. `xt.py floor --run` (CI mẫu sau `gate-par`) chạy đúng các
    lệnh đó, bỏ lệnh trùng gate và khoá `--skip`; thiếu khoá chỉ cảnh báo trừ `--strict`."""

    BP = "---\ntitle: B\nkind: blueprint\nprofile: {p}\nscale: {s}\n---\n"

    def setUp(self):
        self.base = self.tmpdir()
        env = unittest.mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(self.base)})
        env.start()
        self.addCleanup(env.stop)
        os.environ.pop("XT_RECORD_TIMEOUT", None)

    def floor(self, yaml: str, *args: str, scale: str = "M", profile: str = "cli-tool"):
        write(self.base / "BLUEPRINT.md", self.BP.format(p=profile, s=scale))
        write(self.base / "xt.yaml", yaml)
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = xt.main(["floor", *args])
        return rc, out.getvalue(), err.getvalue()

    def test_gate_floor_cli_runs_declared_floor_and_fails_red(self):
        yaml = "lint: ruff check .\ntest: sh -c 'exit 0'\nformat_check: sh -c 'exit 3'\ncoverage: sh -c 'exit 0'\n"
        rc, out, _ = self.floor(yaml)
        self.assertEqual(rc, 0)  # không `--run`: chỉ liệt kê
        self.assertIn("format_check: chưa chạy", out)
        self.assertIn("coverage: bỏ qua (trùng `test` của gate)", out)
        rc, out, err = self.floor(yaml, "--run")
        self.assertEqual(rc, 1)
        self.assertIn("✗ format_check: exit 3", out)
        self.assertIn("floor: ĐỎ", out)
        self.assertIn("[xt] floor `format_check`", err)
        rc, out, _ = self.floor(
            yaml.replace("exit 3", "exit 0").replace("coverage: sh -c 'exit 0'", "coverage: sh -c 'true'"), "--run"
        )
        self.assertEqual((rc, "floor: xanh" in out), (0, True))

    def test_gate_floor_cli_build_phase_not_applied(self):
        """ADR-0041: pha build không áp sàn M/L (CI, `loop verify`, `doctor`); harden áp lại."""
        yaml = "lint: x\ntest: sh -c 'exit 0'\nformat_check: sh -c 'exit 3'\ndelivery_phase: build\n"
        rc, out, _ = self.floor(yaml, "--run", "--strict")
        self.assertEqual(rc, 0)
        self.assertIn("không áp ở pha build", out)
        self.assertEqual(xt.gate_floor_issues(self.base), [])
        rc, out, _ = self.floor(yaml.replace("build", "harden"), "--run")
        self.assertEqual((rc, "✗ format_check: exit 3" in out), (1, True))

    def test_gate_floor_cli_zero_tests_and_json(self):
        yaml = "lint: ruff check .\ntest: pytest -q\nformat_check: sh -c 'exit 0'\ncoverage: python3 -c \"print('Ran 0 tests')\"\n"
        rc, out, _ = self.floor(yaml, "--run", "--json")
        d = json.loads(out)
        self.assertEqual((rc, d["exit"], d["scale"], d["missing"]), (1, 1, "M", []))
        self.assertEqual({r["key"]: r["exit_code"] for r in d["runs"]}, {"format_check": 0, "coverage": 5})

    def test_gate_floor_cli_missing_strict_skip_and_scale(self):
        rc, out, _ = self.floor("lint: ruff check .\ntest: pytest -q\n")
        self.assertEqual(rc, 0)
        self.assertIn("⚠ quy mô M: xt.yaml thiếu hoặc no-op `format_check`", out)
        rc, out, _ = self.floor("lint: ruff check .\ntest: pytest -q\n", "--strict")
        self.assertEqual(rc, 1)
        self.assertIn("✗ quy mô M", out)
        web = "lint: a\ntest: b\nformat_check: sh -c 'exit 0'\ncoverage: sh -c 'exit 0'\ne2e: sh -c 'exit 9'\n"
        rc, out, _ = self.floor(web, "--run", "--skip", "e2e", profile="web-app")
        self.assertEqual(rc, 0, out)
        self.assertIn("e2e: bỏ qua (--skip)", out)
        rc, out, _ = self.floor("lint: a\n", "--run", "--strict", scale="S")
        self.assertEqual(rc, 0)
        self.assertIn("không áp (quy mô S", out)
        (self.base / "BLUEPRINT.md").unlink()
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(xt.main(["floor"]), 0)
        self.assertIn("quy mô không rõ", out.getvalue())

    def test_gate_floor_cli_bad_timeout(self):
        with unittest.mock.patch.dict(os.environ, {"XT_RECORD_TIMEOUT": "x"}):
            self.assertEqual(self.floor("lint: a\n", "--run")[0], 2)


class TaskDagTest(TmpMixin, unittest.TestCase):
    """T-1511 (AUTO-01): `(sau: …; files: …)` của dòng task → `loop next`, từ chối record khi dependency mở, chu trình."""

    PLAN = """
        ### Đợt 1
        - [x] `T-001` nền (REC-01; files: scripts/xt.py) — Gate: `true`
        - [ ] `T-002` hai (A; sau: T-001; cần: PR #9; files: scripts/xt.py, tests/a.py) — Gate: `echo "(sau: T-999)"`
        - [ ] `T-003` ba (sau: T-001, T-001; files: `scripts/`) — Gate: `true`
        - [ ] `T-004` bốn (sau: T-002) — Gate: `true`
        - [ ] `T-005` năm (sau: T-777; files: docs/x.md) (exec: deep) — Gate: `true`
        - [ ] `T-006` sáu (files: docs/x.md, ) — Gate: `true`
        - [ ] `T-007` bảy (files: docs/y.md) — Gate: `true`
        - [ ] `T-008` tám (sau: T-001; files: docs/z.md) — Gate: `true`
        """

    def setUp(self):
        self.base = self.tmpdir()
        ceiling = unittest.mock.patch.dict(
            os.environ, {"GIT_CEILING_DIRECTORIES": str(self.base.parent), "CLAUDE_PROJECT_DIR": str(self.base)}
        )
        ceiling.start()
        self.addCleanup(ceiling.stop)
        os.environ.pop("XT_RECORD_TIMEOUT", None)
        write(self.base / "docs" / "autopilot" / "PLAN.md", self.PLAN)
        xt.write_state({"active": True, "plan": "docs/autopilot/PLAN.md"}, self.base)

    def run_main(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = xt.main(list(args))
        return rc, out.getvalue(), err.getvalue()

    def tasks(self):
        return {t["id"]: t for t in xt.parse_plan(self.base / "docs" / "autopilot" / "PLAN.md")}

    def test_task_dag_parser_reads_links_outside_gate(self):
        t = self.tasks()
        self.assertEqual((t["T-001"]["after"], t["T-001"]["files"]), ([], ["scripts/xt.py"]))
        self.assertEqual((t["T-002"]["after"], t["T-002"]["files"]), (["T-001"], ["scripts/xt.py", "tests/a.py"]))
        self.assertEqual((t["T-003"]["after"], t["T-003"]["files"]), (["T-001"], ["scripts/"]))  # dedupe, bỏ backtick
        self.assertEqual((t["T-004"]["after"], t["T-004"]["files"]), (["T-002"], []))
        self.assertEqual((t["T-006"]["after"], t["T-006"]["files"]), ([], ["docs/x.md"]))  # phần tử rỗng bị bỏ
        self.assertEqual(t["T-005"]["tier"], "deep")
        self.assertEqual(xt.plan_links("không có ghi chú (REC-01; cần: x)"), {"sau": [], "files": []})
        self.assertEqual(
            xt.plan_links("(sau: T-101; files: a) (sau: T-102)"), {"sau": ["T-101", "T-102"], "files": ["a"]}
        )

    def test_review173_plan_links_anywhere_in_group(self):
        """PR #173: `sau:`/`files:` không đứng đầu đoạn vẫn được đọc; `files:` có ngoặc lồng giữ nguyên tên."""
        self.assertEqual(xt.plan_links("(S-001, sau: T-001)"), {"sau": ["T-001"], "files": []})
        self.assertEqual(xt.plan_links("(sau: T-001, files: a.py)"), {"sau": ["T-001"], "files": ["a.py"]})
        self.assertEqual(xt.plan_links("(files: b (c).py)"), {"sau": [], "files": ["b (c).py"]})
        self.assertEqual(
            xt.plan_links("x (REC-01, files: a.py, b.py; cần: y) (ghi chú (phụ), sau: T-002, T-003)"),
            {"sau": ["T-002", "T-003"], "files": ["a.py", "b.py"]},
        )
        self.assertEqual(xt.plan_links("sau: T-001 files: a.py ngoài ngoặc"), {"sau": [], "files": []})
        self.assertEqual(xt.plan_links("(tiêu đề có chữ hậu: sau:x)"), {"sau": [], "files": []})

    def test_review173_plan_bad_links_warn(self):
        """Nhóm ngoặc có `sau:`/`files:` mà không đọc được (thiếu ID, rỗng, ngoặc không đóng) → cảnh báo, không chặn."""
        self.assertEqual(xt.plan_link_problems("(sau: T-001; files: a)"), [])
        self.assertEqual(xt.plan_link_problems("(sau: xong T-1)"), ["sau: xong T-1"])
        self.assertEqual(xt.plan_link_problems("(files: , ; sau: T-001)"), ["files:"])
        self.assertEqual(xt.plan_link_problems("(sau: T-001; files: a"), ["(sau: T-001; files: a"])
        self.assertEqual(xt.plan_link_problems("không ngoặc sau: gì"), [])
        write(
            self.base / "docs" / "autopilot" / "PLAN.md",
            "- [ ] `T-001` a (sau: T-1) — Gate: `true`\n- [ ] `T-002` b (files: a.py) — Gate: `true`\n",
        )
        tasks = xt.parse_plan(self.base / "docs" / "autopilot" / "PLAN.md")
        self.assertEqual(xt.plan_bad_links(tasks), {"T-001": ["sau: T-1"]})
        self.assertEqual(xt.plan_bad_links([{"id": "T-9"}]), {})
        nxt = json.loads(self.run_main("loop", "next", "--json")[1])
        self.assertEqual(nxt["bad_links"], {"T-001": ["sau: T-1"]})
        self.assertEqual([r["id"] for r in nxt["ready"]], ["T-002"])  # fail-closed: T-001 không ready (review173b)
        self.assertEqual(json.loads(self.run_main("loop", "status", "--json")[1])["bad_links"], {"T-001": ["sau: T-1"]})
        for cmd in ("next", "status"):
            with self.subTest(cmd=cmd):
                self.assertIn("ghi chú `sau:`/`files:` không đọc được: T-001 → sau: T-1", self.run_main("loop", cmd)[1])
        write(self.base / "docs" / "autopilot" / "PLAN.md", "- [ ] `T-001` a (sau: T-002)\n- [x] `T-002` b\n")
        self.assertEqual(json.loads(self.run_main("loop", "next", "--json")[1])["bad_links"], {})
        self.assertNotIn("không đọc được", self.run_main("loop", "status")[1])

    def test_review173b_bad_links_fail_closed(self):
        """Review delta PR #173: task có ghi chú `sau:`/`files:` không đọc được (ngoặc chưa đóng, thiếu `:`, viết hoa) →
        không `ready` ở `loop next`, `loop record` từ chối kèm lý do, cho tới khi PLAN sửa."""
        self.assertEqual(xt.plan_link_problems("(SAU: T-001)"), ["SAU: T-001"])
        self.assertEqual(xt.plan_link_problems("(sau T-001)"), ["sau T-001"])
        self.assertEqual(xt.plan_link_problems("(Files: a.py; sau: T-001)"), ["Files: a.py; sau: T-001"])
        self.assertEqual(xt.plan_link_problems("(làm sau; files: a.py)"), [])  # chữ `sau` thường không phải khoá
        plan = self.base / "docs" / "autopilot" / "PLAN.md"
        write(
            plan,
            "- [ ] `T-001` a — Gate: `true`\n- [ ] `T-002` b (sau T-001) — Gate: `true`\n"
            "- [ ] `T-003` c (sau: T-001; files: a — Gate: `true`\n- [ ] `T-004` d (files: d.py) — Gate: `true`\n",
        )
        nxt = json.loads(self.run_main("loop", "next", "--json")[1])
        self.assertEqual([r["id"] for r in nxt["ready"]], ["T-001", "T-004"])
        self.assertEqual(sorted(nxt["bad_links"]), ["T-002", "T-003"])
        self.assertIn("không ready, `loop record` từ chối", self.run_main("loop", "next")[1])
        for task in ("T-002", "T-003"):
            with self.subTest(task=task):
                rc, _, err = self.run_main("loop", "record", "--task", task, "--", "true")
                self.assertEqual(rc, 2)
                self.assertIn(f"{task} có ghi chú `sau:`/`files:` không đọc được", err)
                self.assertFalse((self.base / ".autopilot" / "evidence" / f"{task}.json").exists())
        self.assertEqual(self.run_main("loop", "record", "--task", "T-004", "--", "true")[0], 0)
        write(plan, "- [x] `T-001` a — Gate: `true`\n- [ ] `T-002` b (sau: T-001) — Gate: `true`\n")
        self.assertEqual(self.run_main("loop", "record", "--task", "T-002", "--", "true")[0], 0)  # PLAN sửa → nhận

    def test_review173_path_overlap_normalised_and_glob(self):
        self.assertTrue(xt._path_overlap("./src/a.py", "src/"))
        self.assertTrue(xt._path_overlap("src//a.py", "./src/a.py"))
        self.assertTrue(xt._path_overlap("src/*.py", "src/a.py"))
        self.assertTrue(xt._path_overlap("src/a.py", "src/*.py"))
        self.assertTrue(xt._path_overlap("src/**", "src/d/x.txt"))
        self.assertTrue(xt._path_overlap("src/d/*.txt", "src/"))  # glob nằm trong thư mục
        self.assertTrue(xt._path_overlap("src/*", "src/d/"))
        self.assertFalse(xt._path_overlap("src/*.py", "src/a.txt"))
        self.assertFalse(xt._path_overlap("src/*.py", "lib/a.py"))
        self.assertFalse(xt._path_overlap("./src/a.py", "src/ab.py"))
        self.assertFalse(xt._path_overlap("docs/*.md", "docs/sub/x.md"))
        ready = [
            {"id": "T-1", "files": ["./src/a.py"]},
            {"id": "T-2", "files": ["src/*.py"]},
            {"id": "T-3", "files": ["docs/"]},
        ]
        self.assertEqual(xt.plan_overlaps(ready), [{"tasks": ["T-1", "T-2"], "files": ["src/a.py"]}])
        self.assertTrue(xt._path_overlap(".", "docs/x.md"))  # cả repo
        self.assertTrue(xt._path_overlap("src/*.py", "src/[ab].py"))  # hai glob: coi như giao (an toàn)

    def test_task_dag_ready_and_overlaps(self):
        tasks = xt.parse_plan(self.base / "docs" / "autopilot" / "PLAN.md")
        ready = [t["id"] for t in xt.plan_ready(tasks, {})]
        self.assertEqual(
            ready, ["T-002", "T-003", "T-005", "T-006", "T-007", "T-008"]
        )  # T-004 chờ T-002; T-777 ngoài file
        self.assertEqual([t["id"] for t in xt.plan_ready(tasks, {"T-002": {}})][:2], ["T-003", "T-005"])
        pairs = {tuple(o["tasks"]): o["files"] for o in xt.plan_overlaps(xt.plan_ready(tasks, {}))}
        self.assertEqual(pairs, {("T-002", "T-003"): ["scripts/xt.py"], ("T-005", "T-006"): ["docs/x.md"]})
        self.assertEqual(xt.plan_overlaps([]), [])

    def test_task_dag_next_json_and_text(self):
        rc, out, _ = self.run_main("loop", "next", "--json")
        data = json.loads(out)
        self.assertEqual(rc, 0)
        self.assertEqual([r["id"] for r in data["ready"]][:2], ["T-002", "T-003"])
        self.assertEqual(data["ready"][0]["files"], ["scripts/xt.py", "tests/a.py"])
        self.assertEqual(data["unscoped"], [])
        self.assertEqual(data["cycles"], [])
        self.assertEqual([o["tasks"] for o in data["overlaps"]], [["T-002", "T-003"], ["T-005", "T-006"]])
        st = xt.read_state(self.base)
        st["deferred"] = {"T-007": {"reason": "x"}}
        xt.write_state(st, self.base)
        self.assertNotIn("T-007", [r["id"] for r in json.loads(self.run_main("loop", "next", "--json")[1])["ready"]])
        rc, text, _ = self.run_main("loop", "next")
        self.assertEqual(rc, 0)
        self.assertIn("Sẵn sàng: T-002, T-003", text)
        self.assertIn("T-002 ∩ T-003 cùng ghi scripts/xt.py", text)
        self.assertNotIn("chưa khai files", text)
        write(self.base / "docs" / "autopilot" / "PLAN.md", "- [ ] `T-010` không phạm vi — Gate: `true`\n")
        self.assertIn("T-010 chưa khai files:", self.run_main("loop", "next")[1])

    def test_task_dag_next_without_plan_is_error(self):
        xt.write_state({"active": True, "plan": "nope.md"}, self.base)
        rc, out, err = self.run_main("loop", "next")
        self.assertEqual((rc, out), (2, ""))
        self.assertIn("loop init", err)

    def test_task_dag_record_refuses_open_dependency(self):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            self.assertEqual(xt.loop_record("T-004", ["true"], self.base), 2)  # T-002 còn `[ ]`
        self.assertIn("T-002 chưa xong", err.getvalue())
        self.assertIsNone(xt.read_evidence("T-004", self.base))
        with redirect_stdout(out), redirect_stderr(err):
            self.assertEqual(xt.loop_record("T-002", ["true"], self.base), 0)  # T-001 `[x]`
            self.assertEqual(xt.loop_record("T-005", ["true"], self.base), 0)  # dependency ngoài file không chặn
            self.assertEqual(xt.loop_record("T-099", ["true"], self.base), 0)  # task không có trong PLAN
        self.assertIsNotNone(xt.read_evidence("T-002", self.base))
        self.assertEqual(xt.open_dependencies("T-004", self.base, {}), [])  # không có vòng/PLAN: không chặn
        text = (self.base / "docs" / "autopilot" / "PLAN.md").read_text(encoding="utf-8")
        write(self.base / "docs" / "autopilot" / "PLAN.md", text.replace("- [ ] `T-002`", "- [~] `T-002`"))
        self.assertEqual(xt.open_dependencies("T-004", self.base, xt.read_state(self.base) or {}), [])

    def test_task_dag_status_reports_cycles(self):
        self.assertEqual(json.loads(self.run_main("loop", "status", "--json")[1])["cycles"], [])
        self.assertNotIn("chu trình", self.run_main("loop", "status")[1])
        write(
            self.base / "docs" / "autopilot" / "PLAN.md",
            """
            - [ ] `T-001` a (sau: T-002) — Gate: `true`
            - [ ] `T-002` b (sau: T-003) — Gate: `true`
            - [ ] `T-003` c (sau: T-001) — Gate: `true`
            - [ ] `T-004` d (sau: T-003) — Gate: `true`
            - [ ] `T-005` e (sau: T-005) — Gate: `true`
            - [ ] `T-006` f (sau: T-009) — Gate: `true`
            """,
        )
        self.assertEqual(
            json.loads(self.run_main("loop", "status", "--json")[1])["cycles"], ["T-001", "T-002", "T-003", "T-005"]
        )
        self.assertIn("chu trình dependency (sau:)", self.run_main("loop", "status")[1])
        self.assertEqual(json.loads(self.run_main("loop", "next", "--json")[1])["ready"][0]["id"], "T-006")

    def test_audit_delta_unknown_after_warns_without_blocking(self):
        """T-1524: `sau:` trỏ ID không có trong PLAN (gõ nhầm) → cảnh báo ở `loop status`/`loop next`; vẫn không chặn."""
        tasks = xt.parse_plan(self.base / "docs" / "autopilot" / "PLAN.md")
        self.assertEqual(xt.plan_unknown_after(tasks), {"T-005": ["T-777"]})  # `(sau: T-999)` trong Gate không tính
        self.assertEqual(xt.plan_unknown_after([]), {})
        nxt = json.loads(self.run_main("loop", "next", "--json")[1])
        self.assertEqual(nxt["unknown_after"], {"T-005": ["T-777"]})
        self.assertIn("T-005", [r["id"] for r in nxt["ready"]])  # hành vi chặn không đổi
        status = json.loads(self.run_main("loop", "status", "--json")[1])
        self.assertEqual(status["unknown_after"], {"T-005": ["T-777"]})
        for cmd in ("next", "status"):
            with self.subTest(cmd=cmd):
                rc, text, _ = self.run_main("loop", cmd)
                self.assertEqual(rc, 0)
                self.assertIn("`sau:` trỏ ID không có trong PLAN (không chặn — kiểm gõ nhầm): T-005 → T-777", text)
        write(
            self.base / "docs" / "autopilot" / "PLAN.md",
            "- [ ] `T-001` a (sau: T-002) — Gate: `true`\n- [x] `T-002` b\n",
        )
        self.assertEqual(json.loads(self.run_main("loop", "next", "--json")[1])["unknown_after"], {})
        self.assertNotIn("không có trong PLAN", self.run_main("loop", "status")[1])


if __name__ == "__main__":
    unittest.main()
