"""Test cho scripts/xt.py — chạy: python3 -m unittest discover -s tests -v"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import textwrap
import unicodedata
import unittest
import unittest.mock
from contextlib import chdir, redirect_stderr, redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))  # tests/cpu_budget.py
import cpu_budget
import xt


def xt_cli(*args: str, cwd: Path | str | None = None, env: dict | None = None) -> subprocess.CompletedProcess:
    """`xt.py <args>` chạy trong tiến trình test (mỗi tiến trình python con dưới coverage ~200 ms); đường `__main__`
    qua tiến trình con giữ ở CliContractTest. `SystemExit` → mã thoát như python."""
    out, err = io.StringIO(), io.StringIO()
    with (
        unittest.mock.patch.dict(os.environ, env or {}),
        chdir(cwd or os.getcwd()),
        redirect_stdout(out),
        redirect_stderr(err),
    ):
        try:
            rc = xt.main(list(args))
        except SystemExit as exc:
            rc = exc.code if isinstance(exc.code, int) else (0 if exc.code is None else 1)
    return subprocess.CompletedProcess(["xt.py", *args], rc, out.getvalue(), err.getvalue())


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text).lstrip("\n"), encoding="utf-8")


def make_framework(tmp: Path) -> Path:
    fw = tmp / "framework"
    write(
        fw / "README.md",
        """
        ---
        title: Khung
        kind: index
        updated: 2026-10-13
        ---

        # Khung
        """,
    )
    for d in ("01-baseline", "02-profiles", "03-industries", "08-backend"):
        write(
            fw / d / "README.md",
            f"""
            ---
            title: {d}
            kind: index
            updated: 2026-10-13
            ---

            # {d}
            """,
        )
    write(
        fw / "01-baseline" / "security.md",
        """
        ---
        title: Bảo mật nền
        kind: baseline
        prefix: BASE-SEC
        applies_to: [all]
        updated: 2026-10-13
        ---

        # Bảo mật nền

        ## Checklist

        - [ ] `BASE-SEC-001` **MUST** Không commit bí mật. → Kiểm: gitleaks trong CI.
        - [ ] `BASE-SEC-002` **MUST@L** Kiểm toán độc lập. → Kiểm: báo cáo kiểm toán.
        - [ ] `BASE-SEC-003` **MAY** Bug bounty.

        ## Nguồn

        - https://example.org/s — xác minh 2026-10-23
        """,
    )
    write(
        fw / "08-backend" / "api.md",
        """
        ---
        title: API
        kind: module
        prefix: BE-API
        applies_to: [web-app]
        updated: 2026-10-13
        ---

        # API

        ## Checklist

        - [ ] `BE-API-001` **MUST** Lỗi theo RFC 9457. → Kiểm: test contract.

        ```markdown
        - [ ] `BE-API-999` **MUST** ví dụ trong code fence không được tính
        ```

        ## Nguồn

        - https://example.org/s — xác minh 2026-10-23
        """,
    )
    write(
        fw / "08-backend" / "cli-only.md",
        """
        ---
        title: CLI only
        kind: module
        prefix: BE-CLI
        applies_to: [cli-tool]
        updated: 2026-10-13
        ---

        # CLI only

        ## Checklist

        - [ ] `BE-CLI-001` **SHOULD** Chỉ cho CLI.

        ## Nguồn

        - https://example.org/s — xác minh 2026-10-23
        """,
    )
    write(
        fw / "02-profiles" / "web-app.md",
        """
        ---
        title: Web app
        kind: profile
        slug: web-app
        prefix: PRF-WEB
        modules: [08-backend/*]
        updated: 2026-10-13
        ---

        # Web app

        ## Checklist

        - [ ] `PRF-WEB-001` **SHOULD** PWA khi cần offline.

        ## Nguồn

        - https://example.org/s — xác minh 2026-10-23
        """,
    )
    write(
        fw / "02-profiles" / "cli-tool.md",
        """
        ---
        title: CLI tool
        kind: profile
        slug: cli-tool
        modules: [08-backend/cli-only]
        updated: 2026-10-13
        ---

        # CLI tool

        ## Nguồn

        - https://example.org/s — xác minh 2026-10-23
        """,
    )
    write(
        fw / "03-industries" / "fintech.md",
        """
        ---
        title: Fintech
        kind: industry
        slug: fintech
        prefix: IND-FIN
        modules: []
        updated: 2026-10-13
        ---

        # Fintech

        ## Checklist

        - [ ] `IND-FIN-001` **MUST** Tiền dùng số nguyên đơn vị nhỏ nhất. → Kiểm: test kiểu.

        ## Nguồn

        - https://example.org/s — xác minh 2026-10-23
        """,
    )
    return fw


class FrontmatterTest(unittest.TestCase):
    def test_parse_list_and_scalar(self):
        meta, body, n = xt.parse_frontmatter("---\ntitle: A\nmodules: [a/b, c/*]\n---\n# A\n")
        self.assertEqual(meta["title"], "A")
        self.assertEqual(meta["modules"], ["a/b", "c/*"])
        self.assertEqual(n, 4)
        self.assertTrue(body.startswith("# A"))

    def test_missing_frontmatter(self):
        with self.assertRaises(xt.FrontmatterError):
            xt.parse_frontmatter("# no fm\n")

    def test_unclosed_frontmatter(self):
        with self.assertRaises(xt.FrontmatterError):
            xt.parse_frontmatter("---\ntitle: A\n")


class ValidateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.fw = make_framework(self.tmp)

    def test_valid_fixture(self):
        self.assertEqual(xt.validate(self.fw), [])

    def _sources_errors(self, sources: str) -> list:
        p = self.fw / "08-backend" / "api.md"
        text = p.read_text(encoding="utf-8")
        p.write_text(text[: text.index("## Nguồn")] + "## Nguồn\n\n" + sources + "\n", encoding="utf-8")
        return [e for e in xt.validate(self.fw) if "## Nguồn" in e]

    def test_sources_section_missing_url_fails(self):
        errs = self._sources_errors("- RFC 9457, xác minh 2026-10-23")
        self.assertEqual(len(errs), 1, errs)
        self.assertIn("api.md", errs[0])
        self.assertIn("URL", errs[0])

    def test_sources_section_missing_date_fails(self):
        errs = self._sources_errors("- https://www.rfc-editor.org/rfc/rfc9457")
        self.assertEqual(len(errs), 1, errs)
        self.assertIn("ngày", errs[0])

    def test_sources_section_empty_fails_both(self):
        self.assertEqual(len(self._sources_errors("")), 2)

    def test_sources_section_unverified_passes(self):
        self.assertEqual(self._sources_errors("- RFC 9457 (chưa xác minh)"), [])

    def test_sources_section_unverified_does_not_waive_date_when_url_present(self):
        # review T-2405: một dòng "(chưa xác minh)" không miễn ngày cho mục đã có URL
        errs = self._sources_errors("- https://a.example (chưa xác minh)\n- RFC x")
        self.assertEqual(len(errs), 1, errs)
        self.assertIn("ngày", errs[0])

    def test_sources_section_fenced_heading_ignored(self):
        # review T-2405: `## Nguồn` trong code fence không thay mục Nguồn thật
        fenced = "```md\n## Nguồn\n- https://a.example 2026-01-01\n```\n\n"
        p = self.fw / "08-backend" / "api.md"
        text = p.read_text(encoding="utf-8")
        i = text.index("## Nguồn")
        p.write_text(text[:i] + fenced + "## Nguồn\n\n- x\n", encoding="utf-8")
        self.assertEqual(len([e for e in xt.validate(self.fw) if "## Nguồn" in e]), 2)

    def test_sources_section_complete_passes(self):
        self.assertEqual(self._sources_errors("- https://www.rfc-editor.org/rfc/rfc9457 — xác minh 2026-10-23"), [])

    def test_sources_section_other_kinds_not_checked(self):
        p = self.fw / "01-baseline" / "README.md"
        p.write_text(p.read_text(encoding="utf-8") + "\n## Nguồn\n\n- x\n", encoding="utf-8")
        self.assertEqual(xt.validate(self.fw), [])

    def test_fenced_items_ignored(self):
        docs, _ = xt.load_docs(self.fw)
        ids = {it.id for d in docs for it in d.items}
        self.assertNotIn("BE-API-999", ids)

    def test_duplicate_id(self):
        p = self.fw / "08-backend" / "api.md"
        p.write_text(
            p.read_text(encoding="utf-8").replace("## Nguồn", "- [ ] `BE-API-001` **SHOULD** trùng.\n\n## Nguồn", 1),
            encoding="utf-8",
        )
        errs = xt.validate(self.fw)
        self.assertTrue(any("ID trùng BE-API-001" in e for e in errs), errs)

    def test_must_without_check(self):
        p = self.fw / "08-backend" / "api.md"
        p.write_text(p.read_text(encoding="utf-8").replace(" → Kiểm: test contract.", ""), encoding="utf-8")
        errs = xt.validate(self.fw)
        self.assertTrue(any("thiếu '→ Kiểm:'" in e for e in errs), errs)

    def test_module_must_at_m_capped(self):
        p = self.fw / "08-backend" / "api.md"
        extra = "".join(f"- [ ] `BE-API-0{n}` **MUST** x. → Kiểm: y.\n" for n in range(10, 10 + xt.MAX_MUST_AT_M))
        p.write_text(p.read_text(encoding="utf-8").replace("## Nguồn", extra + "\n## Nguồn", 1), encoding="utf-8")
        errs = xt.validate(self.fw)
        self.assertTrue(any("MUST hiệu lực ở quy mô M" in e for e in errs), errs)
        p.write_text(p.read_text(encoding="utf-8").replace("**MUST** x.", "**MUST@L** x."), encoding="utf-8")
        self.assertEqual(xt.validate(self.fw), [])  # MUST@L không tính vào trần M

    def test_prefix_mismatch(self):
        p = self.fw / "08-backend" / "api.md"
        p.write_text(p.read_text(encoding="utf-8").replace("`BE-API-001`", "`BE-XYZ-001`"), encoding="utf-8")
        errs = xt.validate(self.fw)
        self.assertTrue(any("không khớp prefix" in e for e in errs), errs)

    def test_malformed_item_reported(self):
        p = self.fw / "08-backend" / "api.md"
        p.write_text(
            p.read_text(encoding="utf-8").replace("## Nguồn", "- [ ] `BE-API-002` MUST thiếu in đậm.\n\n## Nguồn", 1),
            encoding="utf-8",
        )
        errs = xt.validate(self.fw)
        self.assertTrue(any("sai định dạng" in e for e in errs), errs)

    def test_broken_link(self):
        p = self.fw / "08-backend" / "api.md"
        p.write_text(p.read_text(encoding="utf-8") + "\n[x](khong-co.md)\n", encoding="utf-8")
        errs = xt.validate(self.fw)
        self.assertTrue(any("liên kết hỏng" in e for e in errs), errs)

    def test_missing_module_in_profile(self):
        p = self.fw / "02-profiles" / "cli-tool.md"
        p.write_text(
            p.read_text(encoding="utf-8").replace("08-backend/cli-only", "08-backend/khong-co"), encoding="utf-8"
        )
        errs = xt.validate(self.fw)
        self.assertTrue(any("không tồn tại" in e for e in errs), errs)

    def test_missing_readme_in_dir(self):
        (self.fw / "09-database").mkdir()
        (self.fw / "09-database" / "x.md").write_text(
            "---\ntitle: X\nkind: method\nupdated: 2026-10-13\n---\n# X\n", encoding="utf-8"
        )
        errs = xt.validate(self.fw)
        self.assertTrue(any("thiếu README.md" in e for e in errs), errs)

    def test_unknown_applies_to(self):
        p = self.fw / "08-backend" / "api.md"
        p.write_text(p.read_text(encoding="utf-8").replace("[web-app]", "[khong-co-ho-so]"), encoding="utf-8")
        errs = xt.validate(self.fw)
        self.assertTrue(any("applies_to" in e for e in errs), errs)


class ComposeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.fw = make_framework(self.tmp)

    def test_compose_web_fintech_scale_m(self):
        out = xt.compose(self.fw, "web-app", ["fintech"], "M", include_may=False, today="2026-10-13")
        self.assertIn("`BASE-SEC-001` **MUST**", out)
        self.assertIn("`BASE-SEC-002` **SHOULD**", out)  # MUST@L hạ xuống ở quy mô M
        self.assertNotIn("BASE-SEC-003", out)  # MAY bị bỏ khi không --include-may
        self.assertIn("`BE-API-001` **MUST**", out)
        self.assertNotIn("BE-CLI-001", out)  # applies_to chỉ cli-tool
        self.assertIn("`PRF-WEB-001`", out)
        self.assertIn("`IND-FIN-001` **MUST**", out)
        self.assertIn("generated: 2026-10-13", out)

    def test_compose_scale_s_keeps_floor_demotes_modules(self):
        out = xt.compose(self.fw, "web-app", ["fintech"], "S", include_may=False, today="2026-10-13")
        self.assertIn("`BASE-SEC-001` **MUST**", out)  # baseline: sàn, giữ MUST
        self.assertIn("`IND-FIN-001` **MUST**", out)  # gói ngành: giữ MUST
        self.assertIn("`BE-API-001` **SHOULD**", out)  # module chuyên sâu: S hạ SHOULD
        self.assertIn("`BASE-SEC-002` **SHOULD**", out)  # MUST@L vẫn hạ

    def test_compose_split_keeps_only_must_in_main(self):
        # ADR-0012: BLUEPRINT.md chỉ chứa MUST theo quy mô; SHOULD/MAY sang backlog, ID và trạng thái giữ nguyên.
        main, backlog = xt.compose_split(
            self.fw, "web-app", ["fintech"], "M", include_may=True, today="2026-10-13", backlog_name="BP-BACKLOG.md"
        )
        for mid in ("BASE-SEC-001", "BE-API-001", "IND-FIN-001"):
            self.assertIn(f"`{mid}` **MUST**", main)
            self.assertNotIn(mid, backlog)
        for sid in ("`BASE-SEC-002` **SHOULD**", "`PRF-WEB-001` **SHOULD**", "`BASE-SEC-003` **MAY**"):
            self.assertIn(sid, backlog)
            self.assertNotIn(sid.split()[0], main)
        self.assertIn("backlog: BP-BACKLOG.md", main)
        self.assertIn("| MUST | 3 |\n| SHOULD | 2 |\n| MAY | 1 |", main)  # bảng đếm vẫn đủ ba mức
        self.assertIn("[`BP-BACKLOG.md`](BP-BACKLOG.md)", main)
        self.assertNotIn("### Web app", main)  # phần không còn MUST nào thì không in
        self.assertIn("kind: blueprint-backlog", backlog)
        self.assertNotIn("**MUST**", backlog)
        self.assertNotIn("| MUST |", backlog)  # bảng MUST chỉ ở file chính (blueprint-status đếm mục bị xoá theo nó)
        main_s, backlog_s = xt.compose_split(self.fw, "web-app", ["fintech"], "S", include_may=False)
        self.assertIn("`BE-API-001` **SHOULD**", backlog_s)  # module ở S hạ SHOULD → ra backlog
        self.assertNotIn("BE-API-001", main_s)
        self.assertIn("backlog: BLUEPRINT-BACKLOG.md", main_s)

    def test_compose_scale_l_keeps_must(self):
        out = xt.compose(self.fw, "web-app", [], "L", include_may=True, today="2026-10-13")
        self.assertIn("`BASE-SEC-002` **MUST**", out)
        self.assertIn("`BASE-SEC-003` **MAY**", out)

    def test_compose_add_extra_module_bypasses_applies_to(self):
        out = xt.compose(
            self.fw, "web-app", [], "M", include_may=False, today="2026-10-13", extra=["08-backend/cli-only"]
        )
        self.assertIn("`BE-CLI-001`", out)  # applies_to chỉ cli-tool nhưng --add là có chủ đích
        self.assertIn("extra: [08-backend/cli-only]", out)
        with self.assertRaises(SystemExit):
            xt.compose(self.fw, "web-app", [], "M", include_may=False, extra=["08-backend/khong-co"])

    def test_compose_filters_standards_by_applies_to(self):
        write(self.fw / "04-standards" / "README.md", "---\ntitle: S\nkind: index\nupdated: 2026-10-14\n---\n\n# S\n")
        write(
            self.fw / "04-standards" / "a11y.md",
            """
            ---
            title: A11y
            kind: standard
            prefix: STD-A11Y
            applies_to: [web-app]
            updated: 2026-10-14
            ---

            # A11y

            ## Checklist

            - [ ] `STD-A11Y-001` **MUST** WCAG 2.2 AA. → Kiểm: axe.

            ## Nguồn

            - https://example.org/s — xác minh 2026-10-23
            """,
        )
        p = self.fw / "02-profiles" / "cli-tool.md"
        p.write_text(
            p.read_text(encoding="utf-8").replace("[08-backend/cli-only]", "[08-backend/cli-only, 04-standards/*]"),
            encoding="utf-8",
        )
        self.assertEqual(xt.validate(self.fw), [])
        self.assertNotIn("STD-A11Y-001", xt.compose(self.fw, "cli-tool", [], "M", include_may=False))
        self.assertIn(
            "STD-A11Y-001", xt.compose(self.fw, "web-app", [], "M", include_may=False, extra=["04-standards/*"])
        )

    def test_compose_rebases_relative_links(self):
        p = self.fw / "08-backend" / "api.md"
        p.write_text(
            p.read_text(encoding="utf-8").replace(
                "→ Kiểm: test contract.",
                "Xem [`X`](../01-baseline/security.md#a), [web](https://x.y). → Kiểm: test contract.",
            ),
            encoding="utf-8",
        )
        os.environ["XT_FRAMEWORK_LINK"] = ".xtemplates/framework"
        try:
            out = xt.compose(self.fw, "web-app", [], "M", include_may=False)
        finally:
            os.environ.pop("XT_FRAMEWORK_LINK", None)
        self.assertIn("(.xtemplates/framework/01-baseline/security.md#a)", out)
        self.assertIn("(https://x.y)", out)

    def test_compose_header_points_to_xt_beside_framework(self):
        # Dự án đích gọi xt.py ở `.xtemplates/scripts/` — header từng ghi `scripts/xt.py` (không có ở dự án đích).
        for link, cmd in ((".xtemplates/framework", ".xtemplates/scripts/xt.py"), ("framework", "scripts/xt.py")):
            with self.subTest(link=link), unittest.mock.patch.dict(os.environ, {"XT_FRAMEWORK_LINK": link}):
                out = xt.compose(self.fw, "web-app", [], "M", include_may=False)
                self.assertIn(f"`python3 {cmd} blueprint-status BLUEPRINT.md --strict --run`", out)

    def test_compose_unknown_profile(self):
        with self.assertRaises(SystemExit):
            xt.compose(self.fw, "khong-co", [], "M", include_may=False)

    def test_blueprint_roundtrip_status(self):
        out = xt.compose(self.fw, "web-app", ["fintech"], "M", include_may=False, today="2026-10-13")
        bp = self.tmp / "BLUEPRINT.md"
        bp.write_text(out, encoding="utf-8")
        s = xt.blueprint_status(bp)
        self.assertEqual(s["levels"]["MUST"]["open"], 3)
        text = out.replace("- [ ] `BASE-SEC-001`", "- [x] `BASE-SEC-001`")
        text = text.replace("- [ ] `BE-API-001`", "- [~] `BE-API-001`")  # miễn trừ thiếu lý do
        bp.write_text(text, encoding="utf-8")
        s = xt.blueprint_status(bp)
        self.assertEqual(s["levels"]["MUST"]["done"], 1)
        self.assertEqual(s["open_must"], ["IND-FIN-001"])
        self.assertEqual(len(s["bad_waivers"]), 1)


class LoopTest(unittest.TestCase):
    def setUp(self):
        self.base = Path(self.enterContext(tempfile.TemporaryDirectory()))
        write(
            self.base / "docs" / "autopilot" / "PLAN.md",
            """
            # PLAN
            - [ ] `T-001` Viết hàm cộng — Gate: `python3 -c "import sys; sys.exit(0)"`
            - [ ] `T-002` Viết test — Gate: `true`
            """,
        )
        self.env = dict(os.environ, CLAUDE_PROJECT_DIR=str(self.base))
        self._old = os.environ.get("CLAUDE_PROJECT_DIR")
        os.environ["CLAUDE_PROJECT_DIR"] = str(self.base)

    def tearDown(self):
        if self._old is None:
            os.environ.pop("CLAUDE_PROJECT_DIR", None)
        else:
            os.environ["CLAUDE_PROJECT_DIR"] = self._old

    def run_cli(self, *args) -> int:
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):  # AUD-TEST-003: không rò cảnh báo doctor
            return xt.main(list(args))

    def test_gateless_task_needs_gate(self):
        # AUD-HAR-008: task tick mà không có Gate thì không được tính xong chỉ vì một lệnh xanh bất kỳ.
        write(self.base / "docs" / "autopilot" / "PLAN.md", "- [x] `T-001` viết toàn bộ tính năng\n")
        self.assertEqual(self.run_cli("loop", "init"), 0)
        with redirect_stdout(io.StringIO()):
            xt.loop_record("T-001", ["true"], self.base)
        v = xt.loop_verdict(self.base)
        self.assertEqual(v["verdict"], "verify")
        self.assertIn("không có Gate", v["reason"])

    def test_record_quoting_and_double_dash(self):
        # AUD-HAR-002: argv có nháy/`--` thứ hai phải chạy và khớp Gate nguyên vẹn.
        write(self.base / "docs" / "autopilot" / "PLAN.md", "- [x] `T-001` x — Gate: `echo ok -- --run`\n")
        self.assertEqual(self.run_cli("loop", "init"), 0)
        self.assertEqual(self.run_cli("loop", "record", "--task", "T-001", "--", "echo", "ok", "--", "--run"), 0)
        self.assertEqual(xt.read_evidence("T-001", self.base)["cmd"], "echo ok -- --run")
        self.assertEqual(xt.loop_verdict(self.base)["verdict"], "done")
        self.assertEqual(
            self.run_cli("loop", "record", "--task", "T-002", "--", "python3", "-c", "print('hi there')"), 0
        )
        # AUD-CODE-014: nháy khác → không coi là một lệnh (Gate truyền MỘT đối số nguyên văn; argv ghép bằng shlex chỉ khớp
        # Gate khi không có ký tự đặc biệt).
        self.assertFalse(xt.same_command("python3 -c \"print('a b')\"", "python3 -c 'print('\"'\"'a b'\"'\"')'"))

    def test_task_id_rejects_trailing_newline(self):
        with self.assertRaises(argparse.ArgumentTypeError):
            xt._task_id("T-003\n")

    def test_redact_common_secrets(self):
        # Chuỗi giả ghép lúc chạy để mã nguồn không chứa literal giống bí mật (gitleaks quét lịch sử).
        j = "".join
        fake = {
            "bearer": j(["abcdefgh", "12345678"]),
            "aws": j(["AKIA", "IOSFODNN7", "EXAMPLE"]),
            "pg": j(["S3c", "r3t"]),
            "pw": j(["hun", "ter2"]),
            "sk": j(["sk-", "live-", "123456789"]),
            "gh": j(["ghp", "_", "abcdefghijklmnopqrstuvwxyz0123"]),
            "pem": j(["MII", "Eabc"]),
            "tok": j(["abc", "123"]),
        }
        key_word = j(["PRIVATE", " KEY"])
        raw = (
            f"Authorization: Bearer {fake['bearer']}\n{fake['aws']}\npostgres://admin:{fake['pg']}@db/x\n"
            + "{"
            + f'"password": "{fake["pw"]} long phrase", "api_{"key"}": "{fake["sk"]}"'
            + "}\n"
            + f"--password {fake['pw']}\n{fake['gh']}\n"
            + f"-----BEGIN RSA {key_word}-----\n{fake['pem']}\n-----END RSA {key_word}-----\n"
            + f"TOKEN={fake['tok']}"
        )
        out = xt.redact(raw)
        for name, leak in fake.items():
            self.assertNotIn(leak if name != "aws" else leak[4:], out, name)
        self.assertIn("postgres://admin:***@db/x", out)

    def test_redact_home_paths(self):  # AUD-HAR-054: tên người dùng/máy không lọt vào báo cáo repo khung public
        self.assertEqual(xt.redact_feedback("lỗi ở /home/alice/proj/x.py"), "lỗi ở /home/<user>/proj/x.py")
        self.assertEqual(
            xt.redact_feedback("/Users/bob/src và C:\\Users\\carol\\a"), "/Users/<user>/src và C:\\Users\\<user>\\a"
        )
        self.assertEqual(xt.redact_feedback("/home/<user>/p"), "/home/<user>/p")
        self.assertEqual(xt.redact_feedback("ở /home/bob, rồi"), "ở /home/<user>, rồi")

    def test_redact_more_secrets(self):
        """AUD-CFG-002: các dạng bí mật hay gặp trong triệu chứng/cách sửa của phản hồi (ra repo public)."""
        j = "".join
        fake = {
            "redis": j(["hunter", "2pass"]),
            "npm": j(["npm_", "AbCdEfGhIjKlMnOpQrStUvWxYz0123456789"]),
            "jwt": j(["eyJ", "hbGciOiJIUzI1NiJ9", ".", "eyJzdWIiOiIxMjMifQ", ".", "c2lnbmF0dXJlMTIz"]),
            "mysql": j(["my", "sqlpw9"]),
            "curl": j(["cu", "rlpw77"]),
            "google": j(["AIza", "SyA1234567890abcdefghijklmnopqrstu"]),
            "hf": j(["hf_", "abcdefghijklmnopqrstuvwx"]),
            "pypi": j(["pypi-", "AgEIcHlwaS5vcmcCJDEyMzQ"]),
            "rk": j(["rk_live_", "abcdefghijklmnop"]),
            "spaced": j(["two ", "words"]),
            "access": j(["AKIAZZ", "ZZsecretvalue"]),
            "dsn": j(["0123456789abcdef", "0123456789abcdef"]),
        }
        raw = (
            f"REDIS_URL=redis://:{fake['redis']}@cache:6379 {fake['npm']} {fake['jwt']}\n"
            f"mysql -u root -p{fake['mysql']} db\ncurl -u admin:{fake['curl']} https://x\n"
            f"{fake['google']} {fake['hf']} {fake['pypi']} {fake['rk']}\n"
            f"password: '{fake['spaced']}'\nAWS_ACCESS_KEY={fake['access']}\nhttps://{fake['dsn']}@sentry.io/1\n"
        )
        out = xt.redact(raw)
        for name, leak in fake.items():
            self.assertNotIn(leak, out, name)
        self.assertIn("redis://:***@cache", out)

    def test_redact_quoted_flag_values_and_linear_time(self):
        """Reviewer #61: giá trị trong nháy sau cờ (`--password="a b"`, `-p"a b"`) che hết; dòng dài không chạy bậc hai."""
        j = "".join
        pw = j(["my se", "cret pw"])
        for raw in (f'--password="{pw}" x', f"--token='{pw}' y", f'mysql -u root -p"{pw}" -e x'):
            with self.subTest(raw):
                out = xt.redact(raw)
                self.assertNotIn("cret", out)
        # AUD-TEST-008: không bậc hai — tỉ lệ cỡ n/4n trong cùng tiến trình (cỡ lớn = cỡ cũ), không ngưỡng giây cứng
        for unit, count in (("a", 50_000), ("mysql ", 20_000), ("token" + "f" * 40 + " ", 2_000)):
            with self.subTest(unit[:12]):
                cpu_budget.assert_not_quadratic(self, lambda n, u=unit: xt.redact(u * n), count // 4)

    def test_redact_audit_delta_wave_c(self):
        """Audit delta đợt C: nháy loại kia trong giá trị (AUD-CFG-006), `pwd`/`pass` (CFG-008), không che nhầm định danh
        thường (CFG-007), từ dài lặp từ khoá không chạy bậc hai (CODE-009)."""
        j = "".join
        tail = j(["sec", "ret phrase"])
        for raw in (
            f'password: "it\'s a {tail}"',
            f"password = 'my \"quoted\" {tail}'",
            f'password: "unterminated {tail}',
            f"MYSQL_PWD={tail}",
            f"DB_PASS={tail}",
            f"passphrase: {tail}",
        ):
            with self.subTest(raw):
                self.assertNotIn("ret phrase", xt.redact(raw))
        for raw in (
            "npm_config_cache=/home/u/.npm npm_lifecycle_event=test",
            "from huggingface_hub import hf_hub_download",
            "docker run -u 1000:1000 img",
            "PWD=/home/u/proj",
            "bypass=1",
        ):
            with self.subTest(raw):
                self.assertEqual(xt.redact(raw), raw)
        self.assertIn("***", xt.redact("npm_" + "a1B2" * 9))
        for unit, count in (("token", 10_000), ("_token_", 8_000)):  # AUD-TEST-008: tỉ lệ n/4n, không ngưỡng cứng
            with self.subTest(unit):
                cpu_budget.assert_not_quadratic(self, lambda n, u=unit: xt.redact(u * n), count // 4)

    def test_redact_applies_to_evidence_cmd(self):
        with redirect_stdout(io.StringIO()):
            xt.loop_record("T-009", ["echo --token SUPERSECRETVALUE; exit 1"], self.base)
        ev = xt.read_evidence("T-009", self.base)
        self.assertNotIn("SUPERSECRETVALUE", ev["cmd"] + ev["output_tail"])

    def test_inactive_allows_stop(self):
        out, code = xt.hook_stop("{}", self.base)
        self.assertEqual((out, code), ("", 0))

    def test_continue_then_verify_then_done(self):
        self.assertEqual(self.run_cli("loop", "init", "--max-iterations", "10"), 0)
        v = xt.loop_verdict(self.base)
        self.assertEqual((v["verdict"], v["task"]), ("continue", "T-001"))
        out, _ = xt.hook_stop("{}", self.base)
        self.assertEqual(json.loads(out)["decision"], "block")
        self.assertEqual(xt.read_state(self.base)["iterations"], 1)

        plan = self.base / "docs" / "autopilot" / "PLAN.md"
        plan.write_text(plan.read_text(encoding="utf-8").replace("- [ ] `T-001`", "- [x] `T-001`"), encoding="utf-8")
        v = xt.loop_verdict(self.base)
        self.assertEqual((v["verdict"], v["task"]), ("verify", "T-001"))  # tick mà chưa có bằng chứng

        # Bằng chứng chạy lệnh KHÁC với Gate khai báo -> vẫn verify
        with redirect_stdout(io.StringIO()):
            xt.loop_record("T-001", ["true"], self.base)
        self.assertEqual(xt.loop_verdict(self.base)["verdict"], "verify")

        with redirect_stdout(io.StringIO()):
            code = xt.loop_record("T-001", ['python3 -c "import sys; sys.exit(0)"'], self.base)
        self.assertEqual(code, 0)
        v = xt.loop_verdict(self.base)
        self.assertEqual((v["verdict"], v["task"]), ("continue", "T-002"))

        plan.write_text(plan.read_text(encoding="utf-8").replace("- [ ] `T-002`", "- [x] `T-002`"), encoding="utf-8")
        with redirect_stdout(io.StringIO()):
            xt.loop_record("T-002", ["true"], self.base)
        self.assertEqual(xt.loop_verdict(self.base)["verdict"], "done")
        out, code = xt.hook_stop("{}", self.base)
        self.assertEqual((out, code), ("", 0))
        self.assertFalse(xt.read_state(self.base)["active"])

    def test_same_failure_three_times_blocks(self):
        self.run_cli("loop", "init")
        with redirect_stdout(io.StringIO()):
            for _ in range(3):
                xt.loop_record("T-001", ["sh -c 'echo boom at line 12; exit 3'"], self.base)
        v = xt.loop_verdict(self.base)
        self.assertEqual(v["verdict"], "blocked")
        out, _ = xt.hook_stop("{}", self.base)
        self.assertEqual(out, "")  # blocked -> cho dừng

    def test_different_failures_do_not_block(self):
        self.run_cli("loop", "init")
        with redirect_stdout(io.StringIO()):
            xt.loop_record("T-001", ["sh -c 'echo A; exit 1'"], self.base)
            xt.loop_record("T-001", ["sh -c 'echo B; exit 1'"], self.base)
            xt.loop_record("T-001", ["sh -c 'echo C; exit 1'"], self.base)
        self.assertEqual(xt.loop_verdict(self.base)["verdict"], "continue")

    def test_iteration_cap(self):
        self.run_cli("loop", "init", "--max-iterations", "2")
        for _ in range(2):
            out, _ = xt.hook_stop("{}", self.base)
            self.assertIn("block", out)
        self.assertEqual(xt.loop_verdict(self.base)["verdict"], "budget")
        out, _ = xt.hook_stop("{}", self.base)
        self.assertEqual(out, "")

    def test_manual_block(self):
        self.run_cli("loop", "init")
        self.run_cli("loop", "block", "--reason", "cần duyệt thanh toán thật")
        v = xt.loop_verdict(self.base)
        self.assertEqual(v["verdict"], "blocked")
        self.assertIn("thanh toán", v["reason"])

    def test_resume_clears_block_and_failure_streak(self):
        self.run_cli("loop", "init")
        with redirect_stdout(io.StringIO()):
            for _ in range(3):
                xt.loop_record("T-001", ["sh -c 'echo boom; exit 3'"], self.base)
        self.assertEqual(xt.loop_verdict(self.base)["verdict"], "blocked")
        out, _ = xt.hook_stop("{}", self.base)  # blocked -> cho dừng, active=false
        self.assertFalse(xt.read_state(self.base)["active"])
        self.assertEqual(self.run_cli("loop", "resume", "--reason", "đã sửa tay"), 0)
        st = xt.read_state(self.base)
        self.assertTrue(st["active"])
        self.assertEqual(st["same_failure_count"], 0)
        self.assertEqual(xt.loop_verdict(self.base)["verdict"], "continue")

    def test_cli_hook_stop_fail_open_on_garbage(self):
        r = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "xt.py"), "loop", "hook-stop"],
            input="not json",
            capture_output=True,
            text=True,
            env=self.env,
        )
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "")


class EvidenceV2Test(unittest.TestCase):
    """AUTO-02 (T-1513): evidence ghi `cmd_sha256`, `scope`, `req_rev`, `files_digest`; `loop verify` chỉ chạy lại Gate có
    đầu vào đổi, `--all` chạy hết; evidence cũ thiếu trường → chạy lại."""

    PLAN = (
        "- [x] `T-001` sửa a (files: src/a.txt) — Gate: `test -f src/a.txt`\n"
        "- [x] `T-002` sửa b (files: lib/) — Gate: `test -d lib`\n"
    )

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.base = Path(tmp.name)
        write(self.base / "docs" / "autopilot" / "PLAN.md", self.PLAN)
        write(self.base / "src" / "a.txt", "a\n")
        write(self.base / "lib" / "b.txt", "b\n")
        patcher = unittest.mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(self.base)})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.assertEqual(self.cli("loop", "init")[0], 0)

    def cli(self, *args: str) -> tuple[int, str]:
        out = io.StringIO()
        with redirect_stdout(out), redirect_stderr(io.StringIO()):
            rc = xt.main(list(args))
        return rc, out.getvalue()

    def record_all(self) -> None:
        self.assertEqual(self.cli("loop", "record", "--task", "T-001", "--", "test -f src/a.txt")[0], 0)
        self.assertEqual(self.cli("loop", "record", "--task", "T-002", "--", "test -d lib")[0], 0)

    def task(self, tid: str) -> dict:
        return next(t for t in xt.parse_plan(self.base / "docs" / "autopilot" / "PLAN.md") if t["id"] == tid)

    def test_evidence_v2_record_writes_fields(self):
        self.record_all()
        ev = xt.read_evidence("T-001", self.base)
        self.assertEqual(ev["cmd_sha256"], xt.cmd_sha256("test -f src/a.txt"))
        self.assertEqual(ev["scope"], ["src/a.txt"])
        self.assertEqual(ev["req_rev"], xt.task_req_rev(self.task("T-001")))
        self.assertEqual(len(ev["req_rev"]), 16)
        self.assertEqual(ev["files_digest"], xt.files_digest(self.base, ["src/a.txt"]))
        self.assertRegex(ev["files_digest"], r"^[0-9a-f]{64}$")
        # Task ngoài PLAN: không có phạm vi/yêu cầu để gắn → trường có mặt nhưng rỗng (verify luôn chạy lại).
        self.assertEqual(self.cli("loop", "record", "--task", "T-099", "--", "true")[0], 0)
        ev = xt.read_evidence("T-099", self.base)
        self.assertEqual((ev["scope"], ev["req_rev"], ev["files_digest"]), ([], None, None))

    def test_evidence_v2_verify_reruns_only_changed_gate(self):
        self.record_all()
        rc, out = self.cli("loop", "verify")
        self.assertEqual(rc, 0, out)
        self.assertIn("verify T-001: giữ", out)
        self.assertIn("verify T-002: giữ", out)
        self.assertIn("XANH (0 Gate, giữ 2 Gate có evidence v2 khớp)", out)
        rec = json.loads((self.base / ".autopilot" / xt.VERIFIED_FILE).read_text(encoding="utf-8"))
        self.assertEqual(rec["mode"], "changed")
        self.assertEqual([r.get("kept") for r in rec["results"]], [True, True])
        write(self.base / "lib" / "sub" / "c.txt", "mới\n")  # file mới trong thư mục phạm vi T-002
        rc, out = self.cli("loop", "verify")
        self.assertEqual(rc, 0, out)
        self.assertIn("verify T-001: giữ", out)
        self.assertIn("verify T-002: exit 0 (file trong phạm vi đổi (files_digest))", out)
        rc, out = self.cli("loop", "verify", "--all")
        self.assertEqual(rc, 0, out)
        self.assertIn("verify T-001: exit 0 (--all)", out)
        self.assertIn("verify T-002: exit 0 (--all)", out)
        rec = json.loads((self.base / ".autopilot" / xt.VERIFIED_FILE).read_text(encoding="utf-8"))
        self.assertEqual(rec["mode"], "all")
        # Digest đổi mà Gate giờ đỏ → kiểm lại cuối ĐỎ (không giữ kết quả xanh cũ).
        (self.base / "src" / "a.txt").unlink()
        rc, out = self.cli("loop", "verify")
        self.assertEqual(rc, 1)
        self.assertIn("verify T-001: exit 1", out)

    def test_evidence_v2_old_evidence_without_fields_reruns(self):
        for t, cmd in (("T-001", "test -f src/a.txt"), ("T-002", "test -d lib")):
            write(
                self.base / ".autopilot" / "evidence" / f"{t}.json",
                json.dumps({"task": t, "exit_code": 0, "cmd": cmd, "cmd_sha256": xt.cmd_sha256(cmd)}),
            )
        rc, out = self.cli("loop", "verify")
        self.assertEqual(rc, 0, out)
        self.assertIn("verify T-001: exit 0 (evidence cũ thiếu scope, req_rev, files_digest)", out)
        self.assertIn("XANH (2 Gate)", out)

    def test_evidence_v2_shared_gate_runs_once_when_any_task_stale(self):
        write(
            self.base / "docs" / "autopilot" / "PLAN.md",
            "- [x] `T-001` a (files: src/a.txt) — Gate: `test -f src/a.txt`\n"
            "- [x] `T-002` b (files: lib/) — Gate: `test  -f src/a.txt`\n",
        )
        self.assertEqual(self.cli("loop", "record", "--task", "T-001", "--", "test -f src/a.txt")[0], 0)
        self.assertEqual(self.cli("loop", "record", "--task", "T-002", "--", "test  -f src/a.txt")[0], 0)
        self.assertIn("verify T-001: giữ", self.cli("loop", "verify")[1])
        write(self.base / "lib" / "b.txt", "đổi\n")  # chỉ phạm vi T-002 đổi; lệnh chung → chạy một lần
        rc, out = self.cli("loop", "verify")
        self.assertEqual(rc, 0, out)
        self.assertIn("verify T-001: exit 0 (file trong phạm vi đổi (files_digest))", out)
        self.assertNotIn("verify T-002", out)

    def test_evidence_v2_floor_not_skipped_by_kept_gate(self):
        # Lệnh sàn là kiểm toàn repo: trùng một Gate được giữ thì vẫn phải chạy (chỉ bỏ khi trùng Gate vừa chạy).
        write(self.base / "BLUEPRINT.md", "---\nkind: blueprint\nprofile: cli-tool\nscale: M\n---\n")
        write(self.base / "xt.yaml", "format_check: test -f src/a.txt\ncoverage: test -d lib\n")
        self.record_all()
        rc, out = self.cli("loop", "verify")
        self.assertEqual(rc, 0, out)
        self.assertIn("verify sàn Gate `format_check`: exit 0", out)
        self.assertIn("verify sàn Gate `coverage`: exit 0", out)
        rc, out = self.cli("loop", "verify", "--all")
        self.assertNotIn("verify sàn Gate", out)  # Gate vừa chạy lại trùng lệnh sàn → không chạy hai lần

    def test_evidence_v2_stale_reasons(self):
        self.record_all()
        t1 = self.task("T-001")
        self.assertEqual(xt.evidence_stale(t1, self.base), "")
        ev_path = self.base / ".autopilot" / "evidence" / "T-001.json"
        good = json.loads(ev_path.read_text(encoding="utf-8"))

        def stale_with(**changes: object) -> str:
            write(ev_path, json.dumps({**good, **changes}))
            return xt.evidence_stale(t1, self.base)

        self.assertEqual(stale_with(exit_code=1), "chưa có evidence xanh")
        self.assertEqual(stale_with(finished="2999-01-01T00:00:00+00:00"), "evidence có thời điểm bất thường")
        self.assertEqual(stale_with(cmd_sha256="0" * 64), "lệnh Gate đổi")
        self.assertEqual(stale_with(scope=["src/"]), "phạm vi `files:` đổi")
        self.assertEqual(stale_with(req_rev="0" * 16), "đoạn spec của task đổi (req_rev)")
        self.assertEqual(stale_with(files_digest="0" * 64), "file trong phạm vi đổi (files_digest)")
        write(ev_path, json.dumps(good))
        with unittest.mock.patch.object(xt.hashlib, "file_digest", side_effect=OSError("đọc lỗi")):
            self.assertEqual(xt.evidence_stale(t1, self.base), "file trong phạm vi đổi (files_digest)")
        ev_path.unlink()
        self.assertEqual(xt.evidence_stale(t1, self.base), "chưa có evidence xanh")
        # Spec đổi chữ trong PLAN (Gate giữ nguyên) → req_rev khác.
        write(
            self.base / "docs" / "autopilot" / "PLAN.md",
            self.PLAN.replace("sửa b", "sửa b theo yêu cầu mới").replace("(files: lib/) ", ""),
        )
        t2 = self.task("T-002")
        self.assertEqual(xt.evidence_stale(t2, self.base), "phạm vi `files:` đổi")
        write(self.base / "docs" / "autopilot" / "PLAN.md", self.PLAN.replace("sửa b", "sửa b mới"))
        self.assertEqual(xt.evidence_stale(self.task("T-002"), self.base), "đoạn spec của task đổi (req_rev)")
        # Task không khai `files:` → không có gì để giữ, luôn chạy lại.
        bare = {**t2, "files": []}
        ev2 = self.base / ".autopilot" / "evidence" / "T-002.json"
        write(
            ev2,
            json.dumps({**json.loads(ev2.read_text(encoding="utf-8")), "scope": [], "req_rev": xt.task_req_rev(bare)}),
        )
        self.assertEqual(xt.evidence_stale(bare, self.base), "task không khai `files:` — không có digest để giữ")

    def test_evidence_v2_files_digest_tree(self):
        d = xt.files_digest(self.base, ["lib/"])
        self.assertIsNone(xt.files_digest(self.base, []))
        self.assertEqual(d, xt.files_digest(self.base, ["lib", "lib/"]))  # dấu `/` cuối và trùng lặp không đổi digest
        write(self.base / "lib" / "__pycache__" / "x.pyc", "rác\n")  # sinh khi chạy → không tính
        self.assertEqual(d, xt.files_digest(self.base, ["lib/"]))
        write(self.base / "lib" / "b.txt", "khác\n")
        self.assertNotEqual(d, xt.files_digest(self.base, ["lib/"]))
        missing = xt.files_digest(self.base, ["khong-co"])
        write(self.base / "khong-co", "")
        self.assertNotEqual(missing, xt.files_digest(self.base, ["khong-co"]))  # mất file ≠ file rỗng
        self.assertEqual(xt.task_spec({"rest": " — viết hàm (files: a) — Gate: `true`"}), "viết hàm (files: a)")
        self.assertEqual(xt.task_spec({"rest": "chỉ mô tả"}), "chỉ mô tả")


class AuditRegressionTest(unittest.TestCase):
    """Lỗi tái hiện khi dogfood khung trên chính repo (2026-10-14)."""

    def setUp(self):
        self.tmp = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.fw = make_framework(self.tmp)

    def cli(self, *args, env=None) -> subprocess.CompletedProcess:
        return xt_cli(*args, cwd=self.tmp, env=env)

    def test_compose_out_keeps_existing_states_by_id(self):
        bp = self.tmp / "BP.md"
        self.assertEqual(
            self.cli("--framework", str(self.fw), "compose", "--profile", "web-app", "--out", str(bp)).returncode, 0
        )
        text = bp.read_text(encoding="utf-8").replace(
            "- [ ] `BASE-SEC-001` **MUST** Không commit bí mật. → Kiểm: gitleaks trong CI.",
            "- [x] `BASE-SEC-001` **MUST** Không commit bí mật. → Kiểm: gitleaks trong CI. — Bằng chứng: ci.yml:10",
        )
        bp.write_text(text, encoding="utf-8")
        r = self.cli("--framework", str(self.fw), "compose", "--profile", "web-app", "--out", str(bp))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(
            "- [x] `BASE-SEC-001` **MUST** Không commit bí mật. → Kiểm: gitleaks trong CI. — Bằng chứng: ci.yml:10",
            bp.read_text(encoding="utf-8"),
        )

    def test_missing_framework_dir_is_error(self):
        r = self.cli("--framework", str(self.tmp / "khong-co"), "validate")
        self.assertEqual(r.returncode, 2)
        self.assertNotIn("Traceback", r.stderr)

    def test_missing_blueprint_file_is_clean_error(self):
        r = self.cli("blueprint-status", str(self.tmp / "khong-co.md"))
        self.assertEqual(r.returncode, 2)
        self.assertNotIn("Traceback", r.stderr)

    def test_blueprint_status_rejects_malformed_and_deleted_items(self):
        # Mục MUST bị đổi ô lạ/thụt lề/xoá từng ra "0 MUST mở" và --strict exit 0.
        head = "| Mức | Số mục |\n|---|---|\n| MUST | 3 |\n\n"
        good = "- [x] `A-001` **MUST** a\n- [x] `A-002` **MUST** b\n- [x] `A-003` **MUST** c\n"
        self.assertEqual(xt.blueprint_status_text(head + good)["bad_lines"], [])
        for bad in ("- [-] `A-003` **MUST** c", "  - [ ] `A-003` **MUST** c", "- [ ] A-003 **MUST** c"):
            with self.subTest(bad=bad):
                s = xt.blueprint_status_text(head + good.replace("- [x] `A-003` **MUST** c", bad))
                self.assertEqual(s["open_must"], [])
                self.assertTrue(any("dòng 7" in b for b in s["bad_lines"]), s["bad_lines"])
                self.assertTrue(any("2/3" in b for b in s["bad_lines"]), s["bad_lines"])
        s = xt.blueprint_status_text(head + good.replace("- [x] `A-003` **MUST** c\n", ""))
        self.assertEqual(s["bad_lines"], ["chỉ thấy 2/3 mục MUST so với bảng đầu trang (mục bị xoá?)"])
        extra = head + good + "- [x] `HM-001` **MUST** mục riêng\n"  # dự án thêm mục: không báo
        self.assertEqual(xt.blueprint_status_text(extra)["bad_lines"], [])

    def test_waiver_reason_must_be_in_note(self):
        # Chữ của mục có thể tự chứa "— Miễn:" (LOOP-HARNESS-007) — không được tính là lý do miễn.
        text = "- [~] `L-007` **MUST** a → Kiểm: chỉ khác cột trạng thái và `— Miễn:`. · Nguồn: x"
        self.assertEqual(xt.blueprint_status_text(text)["bad_waivers"], ["L-007 (dòng 1)"])
        ok_notes = (
            " — Không áp dụng: không có thanh toán",
            " (Không áp dụng: CLI cục bộ — D-004)",
            ' - Miễn: V1 chưa cần — Duyệt: "ok, V1 bỏ" 2026-10-16',
            " — Miễn: hoãn — Duyệt: https://github.com/o/r/issues/7",
            " — Miễn: hoãn — Duyệt: “đồng ý” (2026-10-16)",
        )
        for note in ok_notes:
            self.assertEqual(xt.blueprint_status_text(text + note)["bad_waivers"], [], note)
        self.assertEqual(xt.blueprint_status_text(text + " — Miễn: ")["bad_waivers"], ["L-007 (dòng 1)"])
        # LOOP-STOP-024: MUST có áp dụng mà bỏ cần lời chủ dự án; câu tự viết "chủ dự án duyệt" không phải bằng chứng
        need = ["L-007 (dòng 1: MUST `Miễn` thiếu `Duyệt:` của chủ dự án)"]
        for note in (" — Miễn: không áp dụng", " — Miễn: chủ dự án duyệt 2026-10-15", ' — Miễn: x — Duyệt: "ok"'):
            self.assertEqual(xt.blueprint_status_text(text + note)["bad_waivers"], need, note)
        should = text.replace("**MUST**", "**SHOULD**") + " — Miễn: V1 chưa cần"
        self.assertEqual(xt.blueprint_status_text(should)["bad_waivers"], [])

    def strict_rc(self, text):
        f = self.tmp / "bp-strict.md"
        f.write_text(text, encoding="utf-8")
        return self.cli("blueprint-status", str(f), "--strict").returncode

    def test_blueprint_waiver_needs_approval(self):
        # T-2511: `Không áp dụng` + `Miễn` lẫn lộn lọt --strict mà không cần `Duyệt:`.
        base = "- [~] `L-007` **MUST** a. · Nguồn: x"
        mixed = (
            " — Không áp dụng: không có thanh toán — Miễn: hoãn",
            " (Không áp dụng: CLI cục bộ) (Miễn: hoãn)",
            " - Không áp dụng: không có DB - Miễn: hoãn",
        )
        for note in mixed:
            with self.subTest(note=note):
                bad = xt.blueprint_status_text(base + note)["bad_waivers"]
                self.assertEqual(len(bad), 1, note)
                self.assertIn("lẫn", bad[0])
                self.assertIn("Duyệt:", bad[0])
                r = self.strict_rc(base + note + "\n")
                self.assertEqual(r, 1)
        # ca hợp lệ: NA thuần; miễn có Duyệt; SHOULD lẫn không bị chặn mức MUST nhưng vẫn lẫn → đỏ
        for ok in (" — Không áp dụng: không có DB", ' — Miễn: hoãn — Duyệt: "ok, V1 bỏ" 2026-10-16'):
            self.assertEqual(xt.blueprint_status_text(base + ok)["bad_waivers"], [], ok)
        should = base.replace("**MUST**", "**SHOULD**") + mixed[0]
        self.assertEqual(len(xt.blueprint_status_text(should)["bad_waivers"]), 1)

    def test_blueprint_bold_id_is_format_error_and_empty_is_red(self):
        # T-2512: ID in đậm thay backtick → 0 mục nhận diện → --strict exit 0 (xanh giả).
        bold = "- [x] **ABC-PROOF-001** **MUST** a\n- [x] **ABC-PROOF-002** **MUST** b\n"
        s = xt.blueprint_status_text(bold)
        self.assertEqual(len([b for b in s["bad_lines"] if "dòng" in b]), 2, s["bad_lines"])
        self.assertEqual(len(s["bad_lines"]), 2, s["bad_lines"])  # chỉ lỗi từng dòng, không thêm thông báo "rỗng"
        self.assertEqual(self.strict_rc(bold), 1)
        empty = xt.blueprint_status_text("# BP\n\nkhông có mục nào\n")
        self.assertEqual(len(empty["bad_lines"]), 1)
        self.assertIn("không nhận diện", empty["bad_lines"][0])
        self.assertEqual(self.strict_rc(""), 1)
        # review T-2512: đậm bọc backtick, gạch dưới — cũng là lỗi định dạng, không bỏ qua im lặng
        for odd in ("**`ABC-002`**", "__ABC-002__", "*`ABC-002`*"):
            with self.subTest(odd):
                text = f"- [x] `ABC-001` **MUST** a\n- [ ] {odd} **MUST** b\n"
                self.assertEqual(len(xt.blueprint_status_text(text)["bad_lines"]), 1)
                self.assertEqual(self.strict_rc(text), 1)
        good = "- [x] `ABC-PROOF-001` **MUST** a\n"
        self.assertEqual(xt.blueprint_status_text(good)["bad_lines"], [])
        self.assertEqual(self.strict_rc(good), 0)

    def test_carry_states_keeps_any_note_and_own_items(self):
        new = "# BP\n- [ ] `A-001` **MUST** a. · Nguồn: x\n- [ ] `A-002` **MUST** b. · Nguồn: y\n"
        old = (
            "- [x] `A-001` **MUST** a. · Nguồn: x - Bằng chứng: PR #7\n"
            "- [~] `A-002` **MUST** b. · Nguồn: z (Miễn: không áp dụng — D-004)\n"
            "- [x] `HM-001` **MUST** mục riêng của dự án — Bằng chứng: test\n"
            "- [x] `OLD-001` **MUST** mục khung đã ngừng dùng\n"
        )
        out, kept = xt.carry_states(old, new, {"A-001", "A-002", "OLD-001"})
        self.assertEqual(kept, 2)
        self.assertIn("- [x] `A-001` **MUST** a. · Nguồn: x - Bằng chứng: PR #7\n", out)  # chữ không đổi: giữ đuôi
        # chỉ nguồn đổi (chữ yêu cầu y nguyên): vẫn mang ghi chú miễn trừ
        self.assertIn("- [~] `A-002` **MUST** b. · Nguồn: y (Miễn: không áp dụng — D-004)\n", out)
        self.assertIn("## Mục riêng của dự án", out)
        self.assertIn("- [x] `HM-001` **MUST** mục riêng của dự án — Bằng chứng: test\n", out)
        self.assertNotIn("OLD-001", out)  # khung bỏ có chủ đích
        self.assertNotIn("Mục riêng", xt.carry_states(old, new)[0])  # không biết ID khung → hành vi cũ
        # Lệnh kiểm máy (LOOP-DESIGN-023) là ghi chú của dự án: nguồn đổi, chữ yêu cầu giữ → vẫn mang theo.
        old_check = "- [x] `A-001` **MUST** a. · Nguồn: x — Kiểm: `test -f ok`\n"
        self.assertEqual(
            xt.carry_states(old_check, "- [x] `A-001` **MUST** a. · Nguồn: z\n")[0],
            "- [x] `A-001` **MUST** a. · Nguồn: z — Kiểm: `test -f ok`\n",
        )
        # Ghi chú nối bằng `·` như chữ của khung (hotel-manager): nguồn đổi vẫn mang theo, không mất im lặng.
        old_dot = "- [x] `A-001` **MUST** a. · Nguồn: x · Bằng chứng: `ci.yml`\n- [x] `A-002` **MUST** b.\n"
        dropped: list[str] = []
        new_dot = "- [ ] `A-001` **MUST** a. · Nguồn: w\n- [ ] `A-002` **MUST** b. · Nguồn: n\n"
        out, _ = xt.carry_states(old_dot, new_dot, dropped=dropped)
        self.assertIn("- [x] `A-001` **MUST** a. · Nguồn: w · Bằng chứng: `ci.yml`\n", out)
        self.assertEqual(dropped, ["A-002"])  # đã tick, đuôi đổi, không có ghi chú để mang → người gọi cảnh báo

    def test_carry_states_normalizes_new_text_nfc(self):
        # AUD-HAR-070 (BASE-DATA-002): bản ghép mới mang chữ NFD (module khung sửa bằng trình soạn khác) không được bị
        # coi là "chữ yêu cầu đổi" — mục `[x]` giữ trạng thái, không về `[ ]` kèm "— Cũ"; đầu ra lưu NFC.
        old = "- [x] `A-001` **MUST** Chuỗi tiếng Việt được lưu. — Bằng chứng: test\n"
        new = unicodedata.normalize("NFD", "- [ ] `A-001` **MUST** Chuỗi tiếng Việt được lưu.\n")
        stale: list[str] = []
        out, kept = xt.carry_states(old, new, stale=stale)
        self.assertEqual((out, kept, stale), (old, 1, []))

    def test_requirement_revision_resets_changed_text_and_reports_stale(self):
        """T-1505 (REC-06): chữ yêu cầu (phần quy phạm) đổi → mục `[x]`/`[~]` về `[ ]` kèm `— Cũ (rev …, trước đó [x|~])`,
        ID vào `stale`; đổi mức/quy mô, Kiểm, Nguồn không phải đổi yêu cầu; `[ ]` đổi chữ không gắn nhãn; `blueprint-status`
        và `compose` báo mục còn stale."""
        old = (
            "- [x] `A-001` **MUST** a cũ. → Kiểm: t1. · Nguồn: x — Bằng chứng: PR #7\n"
            "- [~] `A-002` **MUST** b. · Nguồn: y (Miễn: không áp dụng — D-004)\n"
            "- [x] `A-003` **MUST** c. → Kiểm: t3.\n"
            "- [x] `A-004` **SHOULD** d.\n"
            "- [ ] `A-005` **MUST** e cũ.\n"
        )
        new = (
            "- [ ] `A-001` **MUST** a mới. → Kiểm: t1. · Nguồn: x\n"
            "- [ ] `A-002` **MUST@M** b đổi. · Nguồn: y\n"
            "- [ ] `A-003` **MUST** c. → Kiểm: lệnh khác.\n"
            "- [ ] `A-004` **MUST@L** d.\n"
            "- [ ] `A-005` **MUST** e mới.\n"
        )
        stale: list[str] = []
        out, kept = xt.carry_states(old, new, stale=stale)
        lines = {ln.split("`")[1]: ln for ln in out.splitlines()}
        rev1, rev2 = xt._norm_rev("a cũ."), xt._norm_rev("b.")
        self.assertEqual(stale, ["A-001", "A-002"])
        self.assertEqual(
            lines["A-001"], f"- [ ] `A-001` **MUST** a mới. → Kiểm: t1. · Nguồn: x — Cũ (rev {rev1}, trước đó [x])"
        )
        self.assertEqual(lines["A-002"], f"- [ ] `A-002` **MUST@M** b đổi. · Nguồn: y — Cũ (rev {rev2}, trước đó [~])")
        self.assertTrue(lines["A-003"].startswith("- [x] `A-003` **MUST** c. → Kiểm: lệnh khác."))  # Kiểm đổi: giữ
        self.assertTrue(lines["A-004"].startswith("- [x] `A-004` **MUST@L** d."))  # mức/quy mô đổi, chữ y nguyên: giữ
        self.assertEqual(lines["A-005"], "- [ ] `A-005` **MUST** e mới.")  # chưa tick: không có gì để mất
        self.assertEqual(kept, 4)  # A-001, A-002 (stale) + A-003, A-004
        # không truyền `stale` vẫn đặt lại (người gọi không cần danh sách); mục mới hẳn không có bản cũ → giữ nguyên
        plain, _ = xt.carry_states(old, new + "- [ ] `A-009` **MUST** mới hẳn.\n")
        self.assertIn("- [ ] `A-009` **MUST** mới hẳn.\n", plain)
        self.assertIn("— Cũ (rev ", next(ln for ln in plain.splitlines() if "`A-001`" in ln))
        # `blueprint-status`: mục còn `[ ]` mang `— Cũ` được báo; tick lại (bỏ ghi chú) thì hết
        st = xt.blueprint_status_text(out)
        self.assertEqual(st["stale"], ["A-001", "A-002"])
        done = out.replace("- [ ] `A-001`", "- [x] `A-001`")
        self.assertEqual(xt.blueprint_status_text(done)["stale"], ["A-002"])
        self.assertEqual(xt.blueprint_status_text(new)["stale"], [])
        # chạy lại carry trên bản đã có `— Cũ`: chữ không đổi, mục vẫn `[ ]` giữ nguyên ghi chú (chưa làm lại)
        again, _ = xt.carry_states(out, new)
        self.assertEqual(
            xt.blueprint_status_text(again)["stale"], ["A-001", "A-002"]
        )  # ghi chú đuôi được giữ tới khi tick lại
        # trạng thái cũ ở dạng X hoa cũng thành `[x]` trong ghi chú
        cap, st2 = "- [X] `A-001` **MUST** a.\n", []
        self.assertIn("trước đó [x])", xt.carry_states(cap, "- [ ] `A-001` **MUST** b.\n", stale=st2)[0])
        self.assertEqual(st2, ["A-001"])

    def test_requirement_revision_ignores_project_note_without_tail(self):
        """Review #168: mục không có đuôi `→ Kiểm:`/`· Nguồn:` — ghi chú dự án (`— Bằng chứng:`, `(Miễn: …)`, `— Cũ (rev …)`)
        không phải chữ yêu cầu; chữ y nguyên thì giữ `[x]`/`[~]` và ghi chú."""
        old = (
            "- [x] `L-001` **SHOULD** Sửa lint đi commit riêng. — Bằng chứng: commit abc\n"
            "- [~] `L-002` **MAY** Làm gì đó. (Miễn: chưa cần)\n"
            "- [x] `L-003` **MUST** Chữ mới. — Cũ (rev 0123abcd, trước đó [x])\n"
            "- [x] `L-004` **SHOULD** Chữ cũ. — Bằng chứng: p\n"
        )
        new = (
            "- [ ] `L-001` **SHOULD** Sửa lint đi commit riêng.\n"
            "- [ ] `L-002` **MAY** Làm gì đó.\n"
            "- [ ] `L-003` **MUST** Chữ mới.\n"
            "- [ ] `L-004` **SHOULD** Chữ khác.\n"
        )
        stale: list[str] = []
        out, _ = xt.carry_states(old, new, stale=stale)
        lines = {ln.split("`")[1]: ln for ln in out.splitlines()}
        self.assertEqual(stale, ["L-004"])  # chỉ mục đổi chữ thật
        self.assertEqual(lines["L-001"], "- [x] `L-001` **SHOULD** Sửa lint đi commit riêng. — Bằng chứng: commit abc")
        self.assertTrue(lines["L-002"].startswith("- [~] `L-002`") and "(Miễn: chưa cần)" in lines["L-002"])
        self.assertTrue(lines["L-003"].startswith("- [x] `L-003`"))

    def test_requirement_revision_tail_item_keeps_body_with_waiver_mention(self):
        """Review #168 vòng 2: mục CÓ đuôi `→ Kiểm:` mà thân nhắc "ghi `[~] — Miễn:`" — chữ yêu cầu không bị cắt ở đó."""
        old = "- [x] `W-001` **MUST** Ghi `[~] — Miễn:` kèm lý do; auth vẫn người merge. → Kiểm: t. · Nguồn: x\n"
        new = "- [ ] `W-001` **MUST** Ghi `[~] — Miễn:` kèm lý do; chỉ payment vẫn người merge. → Kiểm: t. · Nguồn: x\n"
        stale: list[str] = []
        xt.carry_states(old, new, stale=stale)
        self.assertEqual(stale, ["W-001"])

    def test_waiver_reason_accepts_nfd(self):
        import unicodedata

        bp = self.tmp / "BP.md"
        bp.write_text(
            unicodedata.normalize(
                "NFD",
                "- [~] `X-001` **MUST** a — Không áp dụng: không có thanh toán\n"
                '- [~] `X-002` **MUST** b — Miễn: hoãn V2 — Duyệt: "được, để V2" 2026-10-16\n',
            ),
            encoding="utf-8",
        )
        self.assertEqual(xt.blueprint_status(bp)["bad_waivers"], [])

    def test_record_rejects_path_like_task_id(self):
        plan = self.tmp / "docs" / "autopilot" / "PLAN.md"
        write(plan, "- [ ] `T-001` x — Gate: `true`\n")
        env = {"CLAUDE_PROJECT_DIR": str(self.tmp)}
        self.assertEqual(self.cli("loop", "init", env=env).returncode, 0)
        r = self.cli("loop", "record", "--task", "../../pwned", "--", "true", env=env)
        self.assertEqual(r.returncode, 2)
        self.assertFalse((self.tmp / "pwned.json").exists())
        self.assertEqual(self.cli("loop", "record", "--task", "BASE-SEC-001", "--", "true", env=env).returncode, 0)

    def test_hours_zero_sets_deadline(self):
        write(self.tmp / "docs" / "autopilot" / "PLAN.md", "- [ ] `T-001` x\n")
        env = {"CLAUDE_PROJECT_DIR": str(self.tmp)}
        self.cli("loop", "init", "--hours", "0", env=env)
        self.assertIsNotNone(xt.read_state(self.tmp)["deadline"])
        self.assertEqual(xt.loop_verdict(self.tmp)["verdict"], "budget")  # AUD-TEST-004

    def test_evidence_redacts_secret_like_values(self):
        write(self.tmp / "docs" / "autopilot" / "PLAN.md", "- [ ] `T-001` x\n")
        with redirect_stdout(io.StringIO()):
            xt.loop_record("T-001", ["echo API_KEY=sk-live-123 password: hunter2"], self.tmp)
        tail = xt.read_evidence("T-001", self.tmp)["output_tail"]
        self.assertNotIn("sk-live-123", tail)
        self.assertNotIn("hunter2", tail)


class CliContractTest(unittest.TestCase):
    def run_xt(self, *args, stdin=None):
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "xt.py"), *args],
            input=stdin,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_version_from_version_file(self):
        r = self.run_xt("--version")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "xt.py " + (ROOT / "VERSION").read_text(encoding="utf-8").strip())

    def test_help_has_examples_and_exit_codes(self):
        out = self.run_xt("--help").stdout
        self.assertIn("ví dụ:", out)
        self.assertIn("mã thoát:", out)
        self.assertIn("3 lỗi GitHub", out)  # PRF-CLI-001: mọi mã thoát xt.py trả đều ghi trong --help (AUD-HAR-062)
        self.assertIn("126 guard cấm", out)

    def test_blueprint_status_json_from_stdin(self):
        bp = "- [x] `A-001` **MUST** a\n- [ ] `A-002` **MUST** b\n- [~] `A-003` **SHOULD** c\n"
        r = self.run_xt("blueprint-status", "-", "--json", "--strict", stdin=bp)
        self.assertEqual(r.returncode, 1)
        d = json.loads(r.stdout)
        self.assertEqual((d["ok"], d["open_must"], d["bad_waivers"]), (False, ["A-002"], ["A-003 (dòng 3)"]))

    def test_readme_lists_every_subcommand(self):
        # AUD-HAR-075 (BASE-DOC-007): chỉ đọc ô đầu các dòng bảng `## Công cụ` (không cả README) và đòi cả lệnh con
        # (`loop next`, `pr reviewed`…): dạng `xt.py <lệnh> <con>` hoặc `xt.py <lệnh> a/b/<con>`.
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        section = readme.split("\n## Công cụ\n", 1)[1].split("\n## ", 1)[0]
        cells = "\n".join(ln.split("|")[1] for ln in section.splitlines() if ln.startswith("| "))
        sub = next(a for a in xt.build_parser()._actions if isinstance(a, argparse._SubParsersAction))
        missing = []
        for c, p in sub.choices.items():
            if not re.search(rf"xt\.py {re.escape(c)}(?![\w-])", cells):
                missing.append(c)
            for nested in (a for a in p._actions if isinstance(a, argparse._SubParsersAction)):
                pat = rf"xt\.py {re.escape(c)} (?:[\w-]+/)*{{}}(?![\w-])"
                missing += [f"{c} {s}" for s in nested.choices if not re.search(pat.format(re.escape(s)), cells)]
        self.assertEqual(missing, [], "bảng Công cụ của README thiếu lệnh — thêm vào ô đầu bảng")


GOOD_PROGRESS = """# PROGRESS.md — Thử

## Đang làm
- Không.

## Tiếp theo
1. Việc kế.

## Quyết định
- 2026-10-14 Chọn X.

## Bàn giao phiên
- Commit cuối: `{sha}` · CI xanh
"""


class ProgressCheckTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        self.git("init", "-q", "-b", "main")
        self.base = self.commit("a")

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args) -> str:
        r = subprocess.run(
            ["git", "-C", str(self.repo), "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args],
            capture_output=True,
            text=True,
            check=True,
        )
        return r.stdout.strip()

    def commit(self, name: str) -> str:
        (self.repo / name).write_text(name, encoding="utf-8")
        self.git("add", name)
        self.git("commit", "-q", "-m", name)
        return self.git("rev-parse", "HEAD")

    def check(self, text: str):
        f = self.repo / "PROGRESS.md"
        f.write_text(text, encoding="utf-8")
        return xt.progress_check(f)

    def test_progress_ok_with_ancestor_sha(self):
        self.commit("b")
        self.assertEqual(self.check(GOOD_PROGRESS.format(sha=self.base[:7])), [])

    def test_progress_too_big(self):
        errs = self.check(GOOD_PROGRESS.format(sha=self.base) + "x" * 9000)
        self.assertEqual(len(errs), 1)
        self.assertIn("> 8192", errs[0])

    def test_progress_wrong_sections(self):
        text = GOOD_PROGRESS.format(sha=self.base).replace("## Quyết định", "## Lịch sử")
        errs = self.check(text)
        self.assertEqual(len(errs), 1)
        self.assertIn("Lịch sử", errs[0])

    def test_progress_heading_inside_fence_ignored(self):
        text = GOOD_PROGRESS.format(sha=self.base).replace("- Không.", "```\n## Không tính\n```")
        self.assertEqual(self.check(text), [])

    def test_progress_missing_sha(self):
        errs = self.check(GOOD_PROGRESS.format(sha="SHA"))
        self.assertEqual(len(errs), 1)
        self.assertIn("không ghi SHA", errs[0])

    def test_progress_sha_not_ancestor(self):
        self.git("checkout", "-q", "-b", "nhanh")
        side = self.commit("side")
        self.git("checkout", "-q", "main")
        self.commit("c")
        errs = self.check(GOOD_PROGRESS.format(sha=side))
        self.assertEqual(len(errs), 1)
        self.assertIn("không phải tổ tiên", errs[0])

    def test_progress_sha_from_merge_head_during_merge(self):
        # AUD-HAR-020: giải xung đột PROGRESS khi merge nhánh chính vào nhánh PR — SHA của nhánh chính chưa là tổ tiên
        # HEAD nhưng commit merge sẽ chứa nó (MERGE_HEAD); cổng commit không được chặn. Hết merge thì lại đỏ.
        self.git("checkout", "-q", "-b", "feat")
        self.commit("feat")
        self.git("checkout", "-q", "main")
        tip = self.commit("main2")
        self.git("checkout", "-q", "feat")
        with unittest.mock.patch.dict(os.environ, {"XT_PROGRESS_BASE": "main"}):
            self.git("merge", "-q", "--no-ff", "--no-commit", "main")
            self.assertEqual(self.check(GOOD_PROGRESS.format(sha=tip)), [])
            self.git("merge", "--abort")
            errs = self.check(GOOD_PROGRESS.format(sha=tip))
            self.assertEqual(len(errs), 1)
            self.assertIn("không phải tổ tiên", errs[0])

    def test_progress_merge_head_octopus_and_fake_ref(self):
        # Octopus: MERGE_HEAD nhiều dòng — mọi đầu đều được commit merge chứa. Nhánh tên `MERGE_HEAD` (không đang
        # merge) không được coi là đang merge.
        self.git("checkout", "-q", "-b", "side")
        side = self.commit("side")
        self.git("checkout", "-q", "main")
        tip = self.commit("main2")
        self.git("checkout", "-q", "-b", "feat", self.base)
        self.commit("feat")
        with unittest.mock.patch.dict(os.environ, {"XT_PROGRESS_BASE": ""}):
            self.git("merge", "-q", "--no-ff", "--no-commit", "main", "side")
            self.assertEqual(self.check(GOOD_PROGRESS.format(sha=side)), [])
            self.git("merge", "--abort")
            self.git("branch", "MERGE_HEAD", tip)
            errs = self.check(GOOD_PROGRESS.format(sha=tip))
            self.assertEqual(len(errs), 1)
            self.assertIn("không phải tổ tiên", errs[0])

    def test_progress_unknown_sha(self):
        errs = self.check(GOOD_PROGRESS.format(sha="deadbeef"))
        self.assertEqual(len(errs), 1)
        self.assertIn("không phải commit có trong lịch sử", errs[0])

    def test_progress_branch_sha_not_on_base(self):
        # Squash-merge: SHA của nhánh PR là tổ tiên HEAD của nhánh nhưng không bao giờ vào nhánh chính.
        self.git("checkout", "-q", "-b", "feat")
        feat = self.commit("feat")
        with unittest.mock.patch.dict(os.environ, {"XT_PROGRESS_BASE": "main"}):
            errs = self.check(GOOD_PROGRESS.format(sha=feat))
            self.assertEqual(len(errs), 1)
            self.assertIn("chưa nằm trên `main`", errs[0])
            self.assertEqual(self.check(GOOD_PROGRESS.format(sha=self.base)), [])
        with unittest.mock.patch.dict(os.environ, {"XT_PROGRESS_BASE": ""}):
            self.assertEqual(self.check(GOOD_PROGRESS.format(sha=feat)), [])

    def test_progress_base_ref_from_origin(self):
        with unittest.mock.patch.dict(os.environ):
            os.environ.pop("XT_PROGRESS_BASE", None)
            self.assertIsNone(xt.progress_base_ref(self.repo))
            self.git("update-ref", "refs/remotes/origin/main", self.base)
            self.assertEqual(xt.progress_base_ref(self.repo), "origin/main")

    def test_progress_uppercase_sha_tilde_fence_closing_hashes(self):
        text = (
            GOOD_PROGRESS.format(sha=self.base[:9].upper())
            .replace("- Không.", "~~~\n## Không tính\n```\n~~~")
            .replace("## Bàn giao phiên", "## Bàn giao phiên ##")
        )
        self.assertEqual(self.check(text), [])

    def test_progress_cli_exit_codes(self):
        f = self.repo / "PROGRESS.md"
        f.write_text(GOOD_PROGRESS.format(sha="deadbeef"), encoding="utf-8")
        run = lambda *a: xt_cli("progress-check", *a).returncode
        self.assertEqual(run(str(f)), 1)
        f.write_text(GOOD_PROGRESS.format(sha=self.base), encoding="utf-8")
        self.assertEqual(run(str(f)), 0)
        self.assertEqual(run(str(self.repo / "khong-co.md")), 2)


SHA40 = "11d5960a326750d5838078e36cf38b85af677262"
GOOD_WORKFLOW = f"""name: CI
on: [push]
permissions:
  contents: read
jobs:
  quality:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@{SHA40} # v4
      - uses: ./.github/actions/local
      - run: |
          echo "uses: evil/action@v1"
          echo "continue-on-error: true write-all"
      - name: bước có timeout riêng
        timeout-minutes: 2
        run: true
  call:
    uses: org/repo/.github/workflows/x.yml@{SHA40}
env:
  A: b
"""


class CiCheckTest(unittest.TestCase):
    def errs(self, text: str):
        return xt.ci_check_text(text)

    def test_ci_check_good_workflow(self):
        self.assertEqual(self.errs(GOOD_WORKFLOW), [])

    def test_ci_check_missing_permissions(self):
        errs = self.errs(GOOD_WORKFLOW.replace("permissions:\n  contents: read\n", ""))
        self.assertEqual(len(errs), 1)
        self.assertIn("permissions", errs[0])

    def test_ci_check_write_all(self):
        errs = self.errs(GOOD_WORKFLOW.replace("permissions:\n  contents: read", "permissions: write-all"))
        self.assertEqual(len(errs), 1)
        self.assertIn("write-all", errs[0])

    def test_ci_check_unpinned_uses(self):
        errs = self.errs(GOOD_WORKFLOW.replace(f"actions/checkout@{SHA40}", "actions/checkout@v4"))
        self.assertEqual(len(errs), 1)
        self.assertIn("actions/checkout@v4", errs[0])
        self.assertIn("dòng 10", errs[0])

    def test_ci_check_unpinned_reusable_workflow(self):
        errs = self.errs(GOOD_WORKFLOW.replace(f"x.yml@{SHA40}", "x.yml@main"))
        self.assertEqual(len(errs), 1)

    def test_ci_check_missing_job_timeout(self):
        errs = self.errs(GOOD_WORKFLOW.replace("    timeout-minutes: 10\n", ""))
        self.assertEqual(errs, ["dòng 6: job `quality` thiếu `timeout-minutes`"])

    def test_ci_check_continue_on_error(self):
        text = GOOD_WORKFLOW.replace(
            "    timeout-minutes: 10\n", "    timeout-minutes: 10\n    continue-on-error: true\n"
        )
        self.assertEqual(len(self.errs(text)), 1)
        allowed = text.replace(
            "continue-on-error: true", "continue-on-error: true # ci-check-allow: thử, hết hạn 2026-12"
        )
        self.assertEqual(self.errs(allowed), [])
        no_reason = text.replace("continue-on-error: true", "continue-on-error: true # ci-check-allow:")
        self.assertEqual(len(self.errs(no_reason)), 1)
        self.assertEqual(self.errs(text.replace("continue-on-error: true", "continue-on-error: false")), [])

    def test_ci_check_no_false_positives(self):
        text = GOOD_WORKFLOW.replace("  quality:\n", "  quality:\n    name: test write-all detection\n").replace(
            "    timeout-minutes: 10\n", '    timeout-minutes: ${{ inputs.t }}\n    continue-on-error: "false"\n'
        )
        text += "  merged:\n    <<: *base\n"
        self.assertEqual(self.errs(text), [])

    def test_ci_check_layout_variants(self):
        text = (
            GOOD_WORKFLOW.replace("\n  ", "\n    ")  # jobs/permissions thụt 4
            .replace(f"actions/checkout@{SHA40} # v4", f"'actions/checkout@{SHA40}' # v4")
            .replace("      - run: |", "      - run: >-")
            .replace("\n", "\r\n")
        )
        self.assertEqual(self.errs(text), [])

    def test_ci_check_flow_mapping_and_docker(self):
        base = GOOD_WORKFLOW.replace("      - uses: ./.github/actions/local\n", "{}")
        self.assertEqual(len(self.errs(base.format("      - {uses: actions/checkout@v4}\n"))), 1)
        self.assertEqual(len(self.errs(base.format("      - {run: true, continue-on-error: true}\n"))), 1)
        self.assertEqual(len(self.errs(base.format("      - uses: docker://alpine:3\n"))), 1)
        digest = "docker://alpine@sha256:" + "a" * 64
        self.assertEqual(self.errs(base.format(f"      - uses: {digest}\n")), [])

    def pr_workflow(self, trigger: str, job_extra: str) -> str:
        return GOOD_WORKFLOW.replace("on: [push]", trigger).replace(
            "    timeout-minutes: 10\n", "    timeout-minutes: 10\n" + job_extra, 1
        )

    def test_ci_check_pr_secret_flagged(self):
        env = "    env:\n      TOKEN: ${{ secrets.DEPLOY_KEY }}\n"
        for trigger in (
            "on: [push, pull_request]",
            "on: pull_request",
            "on:\n  push:\n  pull_request:\n    branches: [main]",
            "on: {pull_request: {branches: [main]}}",
            "on:\n  pull_request_target:",
        ):
            errs = self.errs(self.pr_workflow(trigger, env))
            self.assertEqual(len(errs), 1, trigger)
            self.assertIn("job `quality`", errs[0])
            self.assertIn("secret ngoài `GITHUB_TOKEN`", errs[0])
        for ref in ("${{ secrets['K'] }}", "${{ toJSON(secrets) }}"):
            self.assertEqual(len(self.errs(self.pr_workflow("on: pull_request", f"    env:\n      T: {ref}\n"))), 1)
        inherit = self.pr_workflow("on: pull_request", "").replace(
            f"    uses: org/repo/.github/workflows/x.yml@{SHA40}\n",
            f"    uses: org/repo/.github/workflows/x.yml@{SHA40}\n    secrets: inherit\n",
        )
        errs = self.errs(inherit)
        self.assertEqual(len(errs), 1)
        self.assertIn("job `call`", errs[0])

    def test_ci_check_pr_secret_valid_cases(self):
        secret = "    env:\n      TOKEN: ${{ secrets.DEPLOY_KEY }}\n"
        # không có trigger PR (push/dispatch) → secret hợp lệ
        self.assertEqual(self.errs(self.pr_workflow("on: [push, workflow_dispatch]", secret)), [])
        # `pull_request` chỉ gần giống/ngoài khối `on:` → không phải trigger
        self.assertEqual(self.errs(self.pr_workflow("on:\n  pull_request_review:\n  push:", secret)), [])
        self.assertEqual(self.errs(self.pr_workflow("on: [push] # pull_request sau", secret)), [])
        body = "    env:\n      NOTE: pull_request\n"
        self.assertEqual(self.errs(self.pr_workflow("on: [push]", body)), [])
        # PR + chỉ GITHUB_TOKEN (kể cả nhắc trong comment) → hợp lệ
        ok = "    env:\n      GH: ${{ secrets.GITHUB_TOKEN }} # không phải secrets.X\n"
        self.assertEqual(self.errs(self.pr_workflow("on: pull_request", ok)), [])
        # ngoại lệ có lý do trên dòng; thiếu lý do vẫn báo
        allowed = "    env:\n      T: ${{ secrets.LICENSE }} # ci-check-allow: licence quét, action ghim SHA\n"
        self.assertEqual(self.errs(self.pr_workflow("on: pull_request", allowed)), [])
        bare = allowed.replace("licence quét, action ghim SHA", "")
        self.assertEqual(len(self.errs(self.pr_workflow("on: pull_request", bare))), 1)

    def test_ci_check_pr_secret_with_environment(self):
        # job có `environment:` (reviewer cấu hình ở GitHub) → hợp lệ; job khác không có vẫn bị báo
        env_job = "    environment: production\n    env:\n      TOKEN: ${{ secrets.DEPLOY_KEY }}\n"
        self.assertEqual(self.errs(self.pr_workflow("on: pull_request", env_job)), [])
        two = self.pr_workflow("on: pull_request", env_job).replace(
            "env:\n  A: b\n",
            "  other:\n    timeout-minutes: 3\n    env:\n      T: ${{ secrets.OTHER }}\nenv:\n  A: b\n",
        )
        errs = self.errs(two)
        self.assertEqual(len(errs), 1)
        self.assertIn("job `other`", errs[0])

    def test_ci_check_cli(self):
        with tempfile.TemporaryDirectory() as d:
            wf = Path(d) / "wf"
            wf.mkdir()
            (wf / "ci.yml").write_text(GOOD_WORKFLOW, encoding="utf-8")
            run = lambda *a: xt_cli("ci-check", *a, cwd=d).returncode
            self.assertEqual(run(str(wf)), 0)
            (wf / "bad.yaml").write_text(GOOD_WORKFLOW.replace("@" + SHA40 + " # v4", "@v4"), encoding="utf-8")
            self.assertEqual(run(str(wf)), 1)
            self.assertEqual(run(str(Path(d) / "khong-co")), 2)
            self.assertEqual(run(), 0)  # không có .github/workflows ở cwd → bỏ qua

    def test_ci_check_repo_workflows(self):
        self.assertEqual(
            xt.ci_check(ROOT / ".github" / "workflows"),
            {p.name: [] for p in (ROOT / ".github" / "workflows").iterdir() if p.suffix in (".yml", ".yaml")},
        )


def audit_status_text(groups=None, findings=()):
    groups = groups or {}
    rows = []
    for no, code, name in xt.AUDIT_GROUPS:
        state, sha, day, note = groups.get(no, ("N/A", "", "", "không áp dụng cho repo thử — Giải trình: fixture"))
        rows.append(f"| {no} | {code} | {name} | {state} | {sha} | {day} | {note} |")
    head = "| ID | Mức | Trạng thái | Tóm tắt | Bằng chứng | Gate | Ghi chú |\n|---|---|---|---|---|---|---|\n"
    return (
        "# AUDIT-STATUS — thử\n\n## Nhóm\n\n| # | Mã | Nhóm | Trạng thái | SHA | Ngày | Ghi chú |\n|---|---|---|---|---|---|---|\n"
        + "\n".join(rows)
        + "\n\n## Phát hiện\n\n"
        + head
        + "".join(f"| {f} |\n" for f in findings)
    )


class GitTimeoutTest(unittest.TestCase):
    def test_git_timeout_does_not_hang(self):
        # BASE-ERR-004: lời gọi git không có timeout từng treo progress-check/audit vô hạn.
        with tempfile.TemporaryDirectory() as d:
            fake = Path(d) / "git"
            fake.write_text("#!/bin/sh\nsleep 30\n", encoding="utf-8")
            fake.chmod(0o755)
            with (
                unittest.mock.patch.dict(os.environ, {"PATH": f"{d}:{os.environ['PATH']}"}),
                unittest.mock.patch.object(xt, "GIT_TIMEOUT", 0.1),
            ):
                r = xt._git(Path(d), "status")
        self.assertEqual(r.returncode, 124)


class WriteAtomicTest(unittest.TestCase):
    def test_write_atomic_does_not_follow_planted_symlink(self):
        # AUD-HAR-009: tên tạm cố định `<file>.tmp` từng đi theo symlink đặt sẵn và ghi đè file ngoài.
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            victim = d / "victim.txt"
            victim.write_text("giữ nguyên", encoding="utf-8")
            (d / "out").mkdir()
            (d / "out" / "BLUEPRINT.md.tmp").symlink_to(victim)
            xt.write_atomic(d / "out" / "BLUEPRINT.md", "mới")
            self.assertEqual(victim.read_text(encoding="utf-8"), "giữ nguyên")
            self.assertEqual((d / "out" / "BLUEPRINT.md").read_text(encoding="utf-8"), "mới")
            self.assertEqual(sorted(p.name for p in (d / "out").iterdir()), ["BLUEPRINT.md", "BLUEPRINT.md.tmp"])


class GitRepoMixin:
    def init_repo(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        self.git("init", "-q", "-b", "main")

    def git(self, *args, env=None) -> str:
        r = subprocess.run(
            ["git", "-C", str(self.repo), "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args],
            capture_output=True,
            text=True,
            check=True,
            env={**os.environ, **(env or {})},
        )
        return r.stdout.strip()

    def commit_files(self, files: dict, at: int) -> str:
        for name, text in files.items():
            f = self.repo / name
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(text, encoding="utf-8")
            self.git("add", name)
        stamp = f"@{at} +0000"
        self.git("commit", "-q", "-m", "c", env={"GIT_AUTHOR_DATE": stamp, "GIT_COMMITTER_DATE": stamp})
        return self.git("rev-parse", "HEAD")


class AuditPlanTest(GitRepoMixin, unittest.TestCase):
    def test_audit_plan_web_signals(self):
        files = [
            "package.json",
            "package-lock.json",
            "src/app.tsx",
            "src/app.test.tsx",
            "db/migrations/001.sql",
            ".github/workflows/ci.yml",
            "Dockerfile",
            "AGENTS.md",
        ]
        sig = xt.audit_signals(Path("."), files)
        a = xt.audit_applicability(sig)
        self.assertEqual(sig["langs"], {"js/ts": 2})
        self.assertEqual((a[6][0], a[10][0], a[5][0], a[13][0]), ("áp dụng", "áp dụng", "áp dụng", "áp dụng"))
        self.assertIn("package-lock.json", a[7][1])

    def test_audit_plan_docs_only_repo(self):
        a = xt.audit_applicability(xt.audit_signals(Path("."), ["README.md", "docs/x.md"]))
        self.assertEqual([a[n][0] for n in (1, 3, 4, 6, 10, 12, 13)], ["N/A"] * 7)
        self.assertIn("KHÔNG có CI", a[8][1])

    def test_audit_plan_stale_evidence(self):
        self.init_repo()
        bp = (
            "- [x] `A-001` **MUST** a → Kiểm: x — Bằng chứng: lib/a.py:1 xử lý\n"
            "- [~] `A-002` **MUST** b → Kiểm: y — Miễn: b.py không dùng\n"
            "- [ ] `A-003` **MUST** c → Kiểm: z — Thiếu: lib/a.py\n"
        )
        self.commit_files({"lib/a.py": "1", "b.py": "1", "BLUEPRINT.md": bp}, 1_700_000_000)
        self.commit_files({"lib/a.py": "2"}, 1_700_000_100)
        files = xt._repo_files(self.repo)
        stale = xt.blueprint_stale_evidence(self.repo, self.repo / "BLUEPRINT.md", files)
        self.assertEqual(stale, [{"id": "A-001", "kind": "Bằng chứng", "files": ["lib/a.py"]}])

    def test_audit_plan_rescan_from_status(self):
        self.init_repo()
        c1 = self.commit_files({".github/workflows/ci.yml": "a", "README.md": "x"}, 1_700_000_000)
        groups = {
            8: ("đã quét", c1, "2026-10-14", ""),
            9: ("đã quét", c1, "2026-10-14", ""),
            2: ("đã quét", "deadbeef", "2026-10-14", ""),
            1: ("chưa quét", "", "", ""),
        }
        self.commit_files({"docs/ops/AUDIT-STATUS.md": audit_status_text(groups)}, 1_700_000_050)
        self.commit_files({".github/workflows/ci.yml": "b"}, 1_700_000_100)
        r = xt.audit_rescan(self.repo, self.repo / "docs/ops/AUDIT-STATUS.md")
        self.assertIn("1 file đổi", r[8])
        self.assertEqual(r[1], "chưa quét")
        self.assertIn("không còn là tổ tiên", r[2])
        self.assertIn(9, r)  # AUDIT-STATUS.md là .md đổi sau SHA quét nhóm 9
        self.assertNotIn(6, r)  # N/A
        self.commit_files(
            {
                "docs/ops/AUDIT-STATUS.md": audit_status_text(
                    {8: ("đã quét", self.git("rev-parse", "HEAD"), "2026-10-14", "")}
                )
            },
            1_700_000_200,
        )
        self.commit_files({'.github/workflows/c"i.yml': "x"}, 1_700_000_300)  # git trích dẫn tên có `"` nếu không -z
        self.assertIn(8, xt.audit_rescan(self.repo, self.repo / "docs/ops/AUDIT-STATUS.md"))
        head = self.git("rev-parse", "HEAD")
        self.commit_files(
            {"docs/ops/AUDIT-STATUS.md": audit_status_text({8: ("đã quét", head, "2026-10-14", "")})}, 1_700_000_400
        )
        self.git("mv", '.github/workflows/c"i.yml', "docs/ci.md")  # rename ra khỏi nhóm: phải còn tên cũ (--no-renames)
        self.git("commit", "-q", "-m", "mv")
        self.assertIn(8, xt.audit_rescan(self.repo, self.repo / "docs/ops/AUDIT-STATUS.md"))

    def test_audit_plan_cli_json(self):
        self.init_repo()
        self.commit_files({"main.py": "print(1)", "tests/test_main.py": "x"}, 1_700_000_000)
        r = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "xt.py"), "audit", "plan", "--json"],
            capture_output=True,
            text=True,
            check=False,
            env={**os.environ, "CLAUDE_PROJECT_DIR": str(self.repo)},
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        d = json.loads(r.stdout)
        self.assertEqual(d["signals"]["langs"], {"python": 2})
        self.assertIsNone(d["rescan"])
        self.assertEqual(len(d["groups"]), 13)


class AuditCheckTest(GitRepoMixin, unittest.TestCase):
    def check(self, text, strict=False, root=None):
        d = Path(root or self.enterContext(tempfile.TemporaryDirectory()))
        f = d / "AUDIT-STATUS.md"
        f.write_text(text, encoding="utf-8")
        return xt.audit_check(f, strict=strict, today=xt._dt.date(2026, 10, 14))[0]

    GOOD = "AUD-SEC-001 | 🟠 | mở | lệnh `a \\| b` lọt guard | đo được: chạy hook → exit 0 | `python3 -m unittest` | "

    def test_audit_check_valid(self):
        self.assertEqual(self.check(audit_status_text(findings=[self.GOOD])), [])

    def test_audit_check_template_body_matches_schema(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        import install

        body = install.template_body((ROOT / "framework/templates/AUDIT-STATUS.md").read_text(encoding="utf-8"))
        self.assertTrue(any("còn chỗ trống" in e for e in self.check(body)))
        no_example = "\n".join(ln for ln in body.splitlines() if not ln.startswith("| AUD-"))
        self.assertEqual(self.check(no_example), [])
        self.assertEqual(len(self.check(no_example, strict=True)), 13)  # 13 nhóm chưa quét

    def test_audit_check_group_errors(self):
        text = audit_status_text({3: ("N/A", "", "", ""), 4: ("đã quét", "", "", "")}).replace(
            "| 5 | PERF |", "| 5 | SPEED |"
        )
        text = text.replace("| 7 | DEP |", "| 99 | DEP |")
        errs = "\n".join(self.check(text))
        for frag in (
            "nhóm 3: `N/A` phải ghi lý do",
            "nhóm 4: thiếu Ngày",
            "nhóm 4: thiếu SHA",
            "mã `SPEED`",
            "số nhóm phải 1–13",
            "nhóm 7: phải có đúng 1 dòng",
        ):
            self.assertIn(frag, errs)

    def test_audit_check_finding_errors(self):
        rows = [
            "AUD-FOO-001 | 🔴 | mở | x | đo được: a | `t` | ",
            "AUD-SEC-002 | 🔵 | xong | x | thấy | `t` | ",
            "AUD-SEC-003 | 🔴 | mở | x | chưa biết: thiếu gitleaks | `t` | ",
            "AUD-SEC-004 | 🟠 | mở | x | suy luận: a.py:3 | | ",
            "AUD-SEC-005 | 🟢 | đã sửa | x | đo được: a | | xong rồi",
            "AUD-SEC-006 | 🟢 | chấp nhận | x | đo được: a | | chủ: An, hạn: 2026-10-01",
            "AUD-SEC-007 | 🟢 | chấp nhận | x | đo được: a | | để sau",
            "AUD-SEC-008 | 🟢 | bác bỏ | x | đo được: a | | ",
            "AUD-SEC-009 | 🟢 | mở | <tóm tắt> | đo được: a | | ",
            "AUD-SEC-009 | 🟢 | mở | x | đo được: a | | ",
        ]
        errs = "\n".join(self.check(audit_status_text(findings=rows)))
        for frag in (
            "AUD-FOO-001: ID phải",
            "mức `🔵`",
            "trạng thái `xong`",
            "AUD-SEC-002: Bằng chứng phải",
            "AUD-SEC-003: 🔴 không thể",
            "AUD-SEC-004: 🟠 phải có Gate",
            "AUD-SEC-005: `đã sửa`",
            "AUD-SEC-006: chấp nhận rủi ro đã quá hạn",
            "AUD-SEC-007: `chấp nhận` phải ghi",
            "AUD-SEC-008: `bác bỏ`",
            "còn chỗ trống",
            "AUD-SEC-009: ID trùng 2 lần",
        ):
            self.assertIn(frag, errs)

    def test_audit_check_placeholder_inside_code_is_content(self):
        row = "AUD-SEC-001 | 🟠 | mở | `git -C <dir> reset --hard` lọt | đo được: `<XT> loop` | `t` | "
        self.assertEqual(self.check(audit_status_text(findings=[row])), [])

    def test_audit_check_fixed_and_accepted_ok(self):
        rows = [
            "AUD-CI-001 | 🟠 | đã sửa | x | đo được: a | `t` | #19",
            "AUD-CI-002 | 🟢 | chấp nhận | x | suy luận: a | | chủ: An · hạn: 2026-12-31",
            "AUD-CI-003 | 🟠 | bác bỏ | x | suy luận: a | | không tái hiện được",
        ]
        self.assertEqual(self.check(audit_status_text(findings=rows), strict=True), [])

    def test_audit_check_strict(self):
        errs = self.check(audit_status_text({1: ("chưa quét", "", "", "")}, [self.GOOD]), strict=True)
        self.assertEqual(sorted(errs), ["AUD-SEC-001: 🟠 còn mở (--strict)", "nhóm 1: chưa quét (--strict)"])

    def test_audit_check_sha_must_be_ancestor(self):
        self.init_repo()
        c1 = self.commit_files({"a": "1"}, 1_700_000_000)
        self.git("checkout", "-q", "-b", "side")
        side = self.commit_files({"b": "1"}, 1_700_000_050)
        self.git("checkout", "-q", "main")
        groups = {1: ("đã quét", c1, "2026-10-14", ""), 2: ("đã quét", side, "2026-10-14", "")}
        errs = self.check(audit_status_text(groups), root=self.repo)
        self.assertEqual(len(errs), 1)
        self.assertIn("nhóm 2: SHA", errs[0])

    def test_audit_check_cli_exit_codes(self):
        d = Path(self.enterContext(tempfile.TemporaryDirectory()))
        f = d / "S.md"
        f.write_text(audit_status_text(findings=[self.GOOD]), encoding="utf-8")
        run = lambda *a: xt_cli("audit", "check", *a).returncode
        self.assertEqual(run(str(f)), 0)
        self.assertEqual(run(str(f), "--strict"), 1)
        self.assertEqual(run(str(d / "khong-co.md")), 2)


class RealFrameworkTest(unittest.TestCase):
    """Khung thật trong repo phải luôn hợp lệ."""

    def test_repo_framework_valid(self):
        errs = xt.validate(xt.DEFAULT_FRAMEWORK)
        self.assertEqual(errs, [], "\n".join(errs[:30]))


AUTHX_MODULE = """
---
title: Xác thực thí điểm
kind: module
prefix: BE-AUTHX
applies_to: [web-app]
essential: [BE-AUTHX-002@auth, BE-AUTHX-003@jwt, BE-AUTHX-004@oauth, BE-AUTHX-005@reset, BE-AUTHX-003@auth]
updated: 2026-10-20
---

# Xác thực thí điểm

## Checklist

- [ ] `BE-AUTHX-001` **MUST** Băm mật khẩu. → Kiểm: test hash.
- [ ] `BE-AUTHX-002` **MUST@L** Khoá theo tài khoản. → Kiểm: test 20 lần sai.
- [ ] `BE-AUTHX-003` **MUST@L** JWT cố định alg. → Kiểm: test alg none.
- [ ] `BE-AUTHX-004` **MUST@L** OAuth PKCE. → Kiểm: test redirect.
- [ ] `BE-AUTHX-005` **MUST@L** Reset một lần. → Kiểm: test token lần hai.
- [ ] `BE-AUTHX-006` **MUST@L** Không thiết yếu. → Kiểm: test x.

## Nguồn

- https://example.org/s — xác minh 2026-10-23
"""


class EssentialNotCappedTest(unittest.TestCase):
    """ADR-0030 (REC-05): mục `essential` không bị trần MUST ở M khi fact bật; S/L và ghép không fact không đổi."""

    def setUp(self):
        self.tmp = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.fw = make_framework(self.tmp)
        write(self.fw / "08-backend" / "authx.md", AUTHX_MODULE)

    def levels(self, scale: str, features: list[str]) -> dict[str, str]:
        out = xt.compose(self.fw, "web-app", [], scale, include_may=False, today="2026-10-20", features=features)
        found = {m["id"]: m["level"] for m in map(xt.ITEM_RE.match, out.splitlines()) if m}
        return {k: v for k, v in found.items() if k.startswith("BE-AUTHX")}

    def test_essential_not_capped_scale_feature_matrix(self):
        ids = [f"BE-AUTHX-00{n}" for n in range(1, 7)]
        cases = {
            # (quy mô, fact) -> ID ở mức MUST; còn lại SHOULD
            ("S", ()): set(),
            ("S", ("auth", "jwt", "oauth", "reset")): set(),  # S: chỉ sàn (ADR-0003), fact không mở
            ("M", ()): {"BE-AUTHX-001"},  # không fact: như trước ADR-0030
            ("M", ("auth",)): {"BE-AUTHX-001", "BE-AUTHX-002", "BE-AUTHX-003"},  # 003 khai cả @auth
            ("M", ("jwt",)): {"BE-AUTHX-001", "BE-AUTHX-003"},
            ("M", ("oauth",)): {"BE-AUTHX-001", "BE-AUTHX-004"},
            ("M", ("reset",)): {"BE-AUTHX-001", "BE-AUTHX-005"},
            ("M", ("payment", "pii")): {"BE-AUTHX-001"},  # fact không khai ở module
            ("M", ("auth", "jwt", "oauth", "reset")): set(ids) - {"BE-AUTHX-006"},
            ("L", ()): set(ids),
            ("L", ("auth",)): set(ids),
        }
        for (scale, feats), must in cases.items():
            with self.subTest(scale=scale, feats=feats):
                got = self.levels(scale, list(feats))
                self.assertEqual({k for k, v in got.items() if v == "MUST"}, must)
                self.assertEqual({k for k, v in got.items() if v == "SHOULD"}, set(ids) - must)

    def test_essential_not_capped_report_and_header(self):
        promoted: list[str] = []
        main, backlog = xt.compose_split(
            self.fw,
            "web-app",
            [],
            "M",
            False,
            today="2026-10-20",
            features=["reset", "auth", "auth"],
            promoted=promoted,
        )
        self.assertEqual(promoted, ["BE-AUTHX-002", "BE-AUTHX-003", "BE-AUTHX-005"])
        self.assertIn("features: [auth, reset]\n---", main)  # thứ tự cố định, bỏ trùng
        self.assertIn("> Feature: auth, reset", main)
        self.assertIn("`BE-AUTHX-005` **MUST**", main)
        self.assertIn("`BE-AUTHX-004` **SHOULD**", backlog)
        plain = xt.compose(self.fw, "web-app", [], "M", False, today="2026-10-20")
        self.assertNotIn("features:", plain)
        self.assertNotIn("> Feature:", plain)
        none: list[str] = []
        xt.compose(self.fw, "web-app", [], "L", False, today="2026-10-20", features=["auth"], promoted=none)
        self.assertEqual(none, [])  # L đã MUST: không có gì "lên"
        with self.assertRaises(SystemExit) as cm:
            xt.compose(self.fw, "web-app", [], "M", False, features=["auth", "sso"])
        self.assertIn("sso", str(cm.exception))

    def test_essential_not_capped_cli_recompose_stable(self):
        out = self.tmp / "proj" / "BLUEPRINT.md"
        out.parent.mkdir()
        args = ("--framework", str(self.fw), "compose", "--profile", "web-app", "--scale", "M", "--out", str(out))
        r1 = xt_cli(*args, "--feature", "auth", "--feature", "jwt")
        self.assertEqual(r1.returncode, 0, r1.stderr)
        self.assertIn(
            "↑ 2 mục thiết yếu lên MUST ở quy mô M (feature auth, jwt; ADR-0030): BE-AUTHX-002, BE-AUTHX-003", r1.stderr
        )
        first = out.read_text(encoding="utf-8"), (out.parent / "BLUEPRINT-BACKLOG.md").read_text(encoding="utf-8")
        r2 = xt_cli(*args, "--feature", "jwt", "--feature", "auth")
        self.assertEqual(r2.returncode, 0, r2.stderr)
        second = out.read_text(encoding="utf-8"), (out.parent / "BLUEPRINT-BACKLOG.md").read_text(encoding="utf-8")
        self.assertEqual(first, second)  # ghép lại hai lần: cùng byte
        r3 = xt_cli("--framework", str(self.fw), "compose", "--profile", "web-app", "--scale", "S", "--feature", "auth")
        self.assertEqual(r3.returncode, 0, r3.stderr)
        self.assertIn("không đổi mức mục nào ở quy mô S (fact chỉ đổi mức ở quy mô M", r3.stderr)
        r3m = xt_cli("--framework", str(self.fw), "compose", "--profile", "web-app", "--scale", "M", "--feature", "pii")
        self.assertIn("không đổi mức mục nào ở quy mô M (không module nào trong hồ sơ/gói", r3m.stderr)
        self.assertNotIn("chỉ đổi mức ở quy mô M", r3m.stderr)  # ở M, lý do thật là không có module khai fact
        r4 = xt_cli("--framework", str(self.fw), "compose", "--profile", "web-app", "--full", "--feature", "oauth")
        self.assertIn("`BE-AUTHX-004` **MUST**", r4.stdout)
        self.assertIn("BE-AUTHX-004", r4.stderr)
        r5 = xt_cli("--framework", str(self.fw), "compose", "--profile", "web-app", "--feature", "sso")
        self.assertEqual(r5.returncode, 2)  # argparse: fact ngoài tập đóng

    def test_essential_not_capped_recompose_warns_dropped_feature(self):
        out = self.tmp / "proj" / "BLUEPRINT.md"
        out.parent.mkdir()
        args = ("--framework", str(self.fw), "compose", "--profile", "web-app", "--scale", "M", "--out", str(out))
        r1 = xt_cli(*args, "--feature", "auth", "--feature", "oauth")
        self.assertEqual(r1.returncode, 0, r1.stderr)
        self.assertNotIn("⚠ bỏ feature", r1.stderr)  # chưa có file cũ: không cảnh báo
        r2 = xt_cli(*args, "--feature", "auth", "--feature", "oauth")
        self.assertEqual(r2.returncode, 0, r2.stderr)
        self.assertNotIn("⚠ bỏ feature", r2.stderr)  # cùng tập fact
        r3 = xt_cli(*args, "--feature", "jwt")  # bỏ auth+oauth; 003 vẫn MUST nhờ jwt → chỉ 002, 004 rơi
        self.assertEqual(r3.returncode, 0, r3.stderr)
        self.assertIn("⚠ bỏ feature auth, oauth: 2 mục về SHOULD (BE-AUTHX-002, BE-AUTHX-004)", r3.stderr)
        r4 = xt_cli(*args)
        self.assertEqual(r4.returncode, 0, r4.stderr)
        self.assertIn("⚠ bỏ feature jwt: 1 mục về SHOULD (BE-AUTHX-003)", r4.stderr)
        self.assertNotIn("features:", out.read_text(encoding="utf-8"))
        # fact không mở mục nào ở module (payment) → vẫn báo bỏ, 0 mục; frontmatter hỏng/fact lạ → im lặng
        xt_cli(*args, "--feature", "payment")
        r5 = xt_cli(*args)
        self.assertIn("⚠ bỏ feature payment: 0 mục về SHOULD\n", r5.stderr)
        out.write_text("không frontmatter\n", encoding="utf-8")
        self.assertEqual(xt._old_features(out), [])
        out.write_text("---\nfeatures: [auth, sso]\n---\n", encoding="utf-8")
        self.assertEqual(xt._old_features(out), ["auth"])
        self.assertEqual(xt._old_features(self.tmp / "khong-co.md"), [])

    def test_essential_not_capped_must_cap_unchanged(self):
        # trần ADR-0004 đếm mức KHÔNG fact: 4 MUST trơn + 4 MUST@L thiết yếu vẫn hợp lệ
        extra = "".join(f"- [ ] `BE-AUTHX-0{n}` **MUST** x. → Kiểm: y.\n" for n in range(10, 13))
        path = self.fw / "08-backend" / "authx.md"
        path.write_text(path.read_text(encoding="utf-8").replace("## Nguồn", extra + "\n## Nguồn"), encoding="utf-8")
        self.assertEqual(xt.validate(self.fw), [])
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                "## Nguồn", "- [ ] `BE-AUTHX-013` **MUST** x. → Kiểm: y.\n\n## Nguồn"
            ),
            encoding="utf-8",
        )
        self.assertEqual(len([e for e in xt.validate(self.fw) if "trần 4" in e]), 1)

    def test_essential_not_capped_validate_rejects_bad_entries(self):
        path = self.fw / "08-backend" / "authx.md"
        base = path.read_text(encoding="utf-8")
        bad = {
            "[BE-AUTHX-002]": "phải dạng <ID>@<fact>",
            "[BE-AUTHX-002@sso]": "fact 'sso' không thuộc",
            "[BE-AUTHX-099@auth]": "BE-AUTHX-099 không có trong file",
            "[BE-AUTHX-001@auth]": "BE-AUTHX-001 không phải MUST@L",
            "[BE-AUTHX-002@auth, BE-AUTHX-003@auth, BE-AUTHX-004@auth, BE-AUTHX-005@auth, BE-AUTHX-006@auth]": (
                "5 mục essential, tối đa 4"
            ),
        }
        line = "essential: [BE-AUTHX-002@auth, BE-AUTHX-003@jwt, BE-AUTHX-004@oauth, BE-AUTHX-005@reset, BE-AUTHX-003@auth]"
        for value, msg in bad.items():
            with self.subTest(value=value):
                path.write_text(base.replace(line, f"essential: {value}"), encoding="utf-8")
                errs = xt.validate(self.fw)
                self.assertEqual(len(errs), 1, errs)
                self.assertIn(msg, errs[0])
        path.write_text(base, encoding="utf-8")
        sec = self.fw / "01-baseline" / "security.md"
        sec.write_text(
            sec.read_text(encoding="utf-8").replace("updated:", "essential: [BASE-SEC-002@auth]\nupdated:"),
            encoding="utf-8",
        )
        errs = xt.validate(self.fw)
        self.assertEqual(len(errs), 1, errs)
        self.assertIn("'essential' chỉ dùng cho module/standard", errs[0])
        # phần tử sai dạng bị bỏ khi ghép (validate đã báo), không làm hỏng compose_sections
        doc = xt.Doc(path=sec, rel="x", meta={"essential": ["rác", "BE-X-001@auth"]}, body="", body_offset=0)
        self.assertEqual(xt.essential_ids(doc, ["auth"]), {"BE-X-001"})

    def test_essential_not_capped_real_authn_pilot(self):
        # thí điểm thật: chỉ 4 mục BE-AUTH, chỉ ở M, đúng fact; hồ sơ khác không đổi khi không fact
        fw = xt.DEFAULT_FRAMEWORK
        self.assertEqual(xt.validate(fw), [])
        pilot = {"auth": "BE-AUTH-003", "jwt": "BE-AUTH-006", "oauth": "BE-AUTH-008", "reset": "BE-AUTH-015"}
        for fact, iid in pilot.items():
            promoted: list[str] = []
            xt.compose(fw, "api-service", [], "M", False, features=[fact], promoted=promoted)
            self.assertEqual(promoted, [iid])
        for fact in ("payment", "pii"):
            promoted = []
            xt.compose(fw, "api-service", [], "M", False, features=[fact], promoted=promoted)
            self.assertEqual(promoted, [])
        for scale in ("S", "L"):
            promoted = []
            xt.compose(fw, "web-app", [], scale, False, features=list(pilot), promoted=promoted)
            self.assertEqual(promoted, [])
        essentials = {d.rel: d.meta["essential"] for d in xt.load_docs(fw)[0] if "essential" in d.meta}
        self.assertEqual(list(essentials), ["08-backend/authn-authz"])  # không bỏ trần đại trà


class BaseSec002SelfMatchTest(unittest.TestCase):
    """Phản hồi dự án đích: mẫu grep gợi ý của BASE-SEC-002 khớp chính dòng của mục → quét repo có khung/BLUEPRINT đỏ."""

    def test_base_sec_002_selfmatch_pattern_finds_nothing_in_framework(self):
        line = next(
            ln
            for ln in (ROOT / "framework/01-baseline/security-minimum.md").read_text(encoding="utf-8").splitlines()
            if "`BASE-SEC-002`" in ln
        )
        pattern = re.search(r"`grep -rE '([^']+)'`", line)
        assert pattern is not None
        rx = re.compile(pattern[1])
        self.assertIsNotNone(rx.search("AKIA" + "ABCDEFGHIJKLMNOP"))  # vẫn bắt khoá thật
        self.assertIsNotNone(rx.search("-----BEGIN " + "RSA PRIVATE KEY-----"))
        hits = [
            f"{f.relative_to(ROOT)}:{n}"
            for f in [ROOT / "BLUEPRINT.md", *sorted((ROOT / "framework").rglob("*.md"))]
            for n, ln in enumerate(f.read_text(encoding="utf-8").splitlines(), 1)
            if rx.search(ln)
        ]
        self.assertEqual(hits, [])


class RebaseLinksAnchorTest(unittest.TestCase):
    """Phản hồi dự án đích: anchor nội trang `(#x)` của mục module giữ nguyên khi sang BLUEPRINT → link gãy."""

    def test_rebase_links_anchor_points_to_module_file(self):
        text = "xem [bảng chọn](#quyết-định), [khác](other.md#a), [web](https://x.invalid/#b)"
        out = xt._rebase_links(text, "06-design-ux/design-system-and-tokens.md", ".xtemplates/framework")
        self.assertIn("(.xtemplates/framework/06-design-ux/design-system-and-tokens.md#quyết-định)", out)
        self.assertIn("(.xtemplates/framework/06-design-ux/other.md#a)", out)
        self.assertIn("(https://x.invalid/#b)", out)


if __name__ == "__main__":
    unittest.main()
