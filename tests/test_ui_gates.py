"""Test cho `xt.py contrast` (UX-DS-003/020) và `xt.py vendor-check` (CMP-LIC-022)."""

from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import unittest
import unittest.mock
from contextlib import chdir, redirect_stderr, redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import xt

WHITE = (1.0, 1.0, 1.0, 1.0)
BLACK = (0.0, 0.0, 0.0, 1.0)

TOKENS = """
/* token gốc */
@import url("x.css");
:root {
  --background: 0 0% 100%;
  --foreground: 222 47% 11%;
  --primary: #1677ff;
  --primary-foreground: #fff;
  --ring: #94a3b8;
  --surface: white;
  --text-muted: #777;
}
.btn { --primary: #000; }
@media (prefers-contrast: more) { :root { --primary: #000; } }
.dark { --background: 224 71% 4%; --primary: #4096ff; }
"""


def run(*args: str, cwd: Path | None = None) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with chdir(cwd or os.getcwd()), redirect_stdout(out), redirect_stderr(err):
        rc = xt.main(list(args))
    return rc, out.getvalue(), err.getvalue()


class CssParseTest(unittest.TestCase):
    def test_blocks_and_themes(self) -> None:
        themes = xt.css_themes(TOKENS)
        self.assertEqual(themes["light"]["--primary"], "#1677ff")  # `.btn` và prefers-contrast bị bỏ qua
        self.assertEqual(themes["dark"]["--primary"], "#4096ff")
        self.assertEqual(themes["dark"]["--foreground"], "222 47% 11%")  # tối phủ lên sáng
        self.assertEqual(list(xt.css_themes(":root { --a: #fff !important; }")), ["light"])  # không có khối tối
        media = (
            "@media (prefers-color-scheme: dark) { :root:not([data-theme=light]) { --a: #000 } } :root { --a: #fff }"
        )
        self.assertEqual(xt.css_themes(media)["dark"]["--a"], "#000")
        attr = '[data-theme="dark"] { --a: #000 } :root { --a: #fff }'
        self.assertEqual(xt.css_themes(attr)["dark"]["--a"], "#000")
        self.assertEqual(xt._css_blocks("no braces here"), [])
        # :not(.dark) vẫn là khối sáng; khối của component và `.dark-mode` không phải theme
        light = xt.css_themes(":root:not(.dark){--a:#fff} html:not(.dark){--b:#fff} .dark{--a:#000}")
        self.assertEqual((light["light"]["--a"], light["dark"]["--a"], light["light"]["--b"]), ("#fff", "#000", "#fff"))
        comp = xt.css_themes(
            ":root{--a:#fff} .btn{--a:#000} .dark .card{--a:#111} .dark-mode{--a:#222} *{--s:#333} .theme-x{--t:#444}"
        )
        self.assertEqual(comp["light"], {"--a": "#fff", "--s": "#333", "--t": "#444"})
        self.assertEqual(list(comp), ["light"])
        # Tailwind v4: thân @theme / @theme inline là token gốc
        tw = xt.css_themes("@theme inline { --color-primary: #1677ff; } @theme { --color-background: #fff; }")
        self.assertEqual(tw["light"], {"--color-primary": "#1677ff", "--color-background": "#fff"})

    def test_var_resolution(self) -> None:
        env = {"--a": "var(--b)", "--b": "#123", "--loop": "var(--loop)"}
        self.assertEqual(xt._css_vars("var(--a)", env), "#123")
        self.assertEqual(xt._css_vars("var(--zz, #fff)", env), "#fff")
        self.assertEqual(xt._css_vars("var(--zz)", env), "var(--zz)")
        self.assertEqual(xt._css_vars("var(--loop)", env), "var(--loop)")  # tự tham chiếu: dừng ở 8 tầng
        self.assertEqual(xt._css_vars("var(--zz, rgb(0 0 0))", env), "rgb(0 0 0)")  # dự phòng có ngoặc

    def test_colors(self) -> None:
        env: dict[str, str] = {}
        p = xt.parse_css_color
        self.assertEqual(p("#fff", env), WHITE)
        self.assertEqual(p("#0008", env), (0.0, 0.0, 0.0, 0x88 / 255))
        self.assertEqual(p("#000000", env), BLACK)
        self.assertEqual(p("#00000080", env)[3], 128 / 255)  # type: ignore[index]
        self.assertIsNone(p("#12", env))
        self.assertEqual(p("rgb(255 255 255)", env), WHITE)
        self.assertEqual(p("rgba(0, 0, 0, 50%)", env), (0.0, 0.0, 0.0, 0.5))
        self.assertEqual(p("rgb(100% 100% 100% / 0.5)", env), (1.0, 1.0, 1.0, 0.5))
        self.assertEqual(p("hsl(0 0% 100%)", env), WHITE)
        self.assertEqual(p("0 0% 0%", env), BLACK)  # bộ ba trần của shadcn
        self.assertEqual(p("hsl(120deg, 100%, 50%)", env), (0.0, 1.0, 0.0, 1.0))
        oklch = p("oklch(1 0 0)", env)
        self.assertAlmostEqual(oklch[0], 1.0, places=3)  # type: ignore[index]
        self.assertEqual(p("oklch(0 0 0)", env), BLACK)
        self.assertEqual(p("transparent", env), (0.0, 0.0, 0.0, 0.0))
        self.assertEqual(p("Black", env), BLACK)
        self.assertEqual(p("var(--x)", {"--x": "#fff"}), WHITE)
        for bad in ("color-mix(in srgb, red, blue)", "rgb(1 2)", "rgb(a b c)", "lab(1 2 3)", "nonsense", "var(--no)"):
            with self.subTest(bad):
                self.assertIsNone(p(bad, env))

    def test_ratio_matches_wcag(self) -> None:
        self.assertAlmostEqual(xt.contrast_ratio(BLACK, WHITE), 21.0)
        grey = xt.parse_css_color("#777", {})
        self.assertAlmostEqual(xt.contrast_ratio(grey, WHITE), 4.48, places=2)  # type: ignore[arg-type]
        blue = xt.parse_css_color("#1677ff", {})
        self.assertAlmostEqual(xt.contrast_ratio(WHITE, blue), 4.10, places=2)  # type: ignore[arg-type]
        half = xt.contrast_ratio((0.0, 0.0, 0.0, 0.5), WHITE)  # chữ trong suốt trộn lên nền
        self.assertLess(half, 21.0)
        self.assertGreater(half, 1.0)


class ContrastPairsTest(unittest.TestCase):
    def test_on_base_and_pairs(self) -> None:
        for name, base in (
            ("--primary-foreground", "--primary"),
            ("--btn-fg", "--btn"),
            ("--on-surface", "--surface"),
            ("--text-on-brand", "--brand"),
        ):
            self.assertEqual(xt._on_base(name), base)
        self.assertIsNone(xt._on_base("--foreground"))
        pairs = xt.read_contrast_pairs("a on b min 3  # ghi chú\n--c on --d\nrác\n# trống\n")
        self.assertEqual(pairs, [("--a", "--b", 3.0), ("--c", "--d", 4.5)])
        env = {
            "--p": "#000",
            "--p-foreground": "#fff",
            "--foreground": "#000",
            "--background": "#fff",
            "--ring": "#000",
        }
        auto = xt.auto_contrast_pairs(env)
        tw = {
            "--color-foreground": "#000",
            "--color-background": "#fff",
            "--color-primary": "#000",
            "--color-primary-foreground": "#fff",
        }
        self.assertEqual(
            xt.auto_contrast_pairs(tw),
            [("--color-primary-foreground", "--color-primary", 4.5), ("--color-foreground", "--color-background", 4.5)],
        )
        self.assertEqual(
            auto,
            [("--p-foreground", "--p", 4.5), ("--foreground", "--background", 4.5), ("--ring", "--background", 3.0)],
        )
        self.assertEqual(xt.missing_on_tokens({"--primary": "#000"}, ["primary", "destructive"], []), ["--primary"])
        self.assertEqual(xt.missing_on_tokens({"--primary": "#000"}, ["primary"], [("--x", "--primary", 4.5)]), [])
        self.assertEqual(xt.missing_on_tokens({"--primary": "#000", "--on-primary": "#fff"}, ["primary"], []), [])

    def test_check_rows(self) -> None:
        rows, missing = xt.contrast_check(TOKENS, "text-muted on surface\n")
        by = {(r["theme"], r["fg"]): r for r in rows}
        self.assertEqual(by[("light", "--primary-foreground")]["status"], "fail")  # 4.10:1 — Ant Design primary
        self.assertEqual(by[("light", "--foreground")]["status"], "ok")
        self.assertEqual(by[("light", "--ring")]["status"], "fail")  # 2.56 < 3
        self.assertEqual(by[("light", "--text-muted")]["ratio"], 4.47)  # cắt, không làm tròn lên 4.5
        self.assertEqual(by[("dark", "--primary-foreground")]["status"], "fail")
        self.assertEqual(missing, [])
        # dark không khai --surface: kế thừa từ light; cặp không có token → bỏ qua
        rows, missing = xt.contrast_check(":root{--primary:#000} ", "x on y")
        self.assertEqual((rows, missing), ([], ["--primary"]))
        skip, _ = xt.contrast_check(":root{--a:color-mix(in srgb,red,blue);--b:#fff} ", "a on b")
        self.assertEqual(skip[0]["status"], "skip")
        trans, _ = xt.contrast_check(":root{--a:#000;--b:rgba(255,255,255,.5)}", "a on b")
        self.assertEqual(trans[0]["status"], "skip")  # nền trong suốt không phán được


class ContrastCliTest(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = Path(self.enterContext(tempfile.TemporaryDirectory()))
        (self.dir / "t.css").write_text(TOKENS, encoding="utf-8")
        (self.dir / "pairs.txt").write_text("--text-muted on --surface\n", encoding="utf-8")

    def test_text_output_fails(self) -> None:
        rc, out, _ = run("contrast", "t.css", "--pairs", "pairs.txt", cwd=self.dir)
        self.assertEqual(rc, 1)
        self.assertIn("✗ [light] --primary-foreground trên --primary  4.1:1 (cần ≥ 4.5)", out)
        self.assertIn("✓ [light] --foreground trên --background", out)
        self.assertIn("đã kiểm", out)

    def test_missing_on_token_is_red(self) -> None:
        (self.dir / "m.css").write_text(":root{--primary:#000;--background:#fff;--foreground:#000}", encoding="utf-8")
        rc, out, _ = run("contrast", "m.css", cwd=self.dir)
        self.assertEqual(rc, 1)
        self.assertIn("✗ --primary: không có token chữ đi kèm", out)
        rc, out, _ = run("contrast", "m.css", "--require-on", "", cwd=self.dir)
        self.assertEqual(rc, 0, out)

    def test_tailwind_theme_and_binary_css(self) -> None:
        (self.dir / "tw.css").write_text(
            "@theme{--color-primary:#1677ff;--color-primary-foreground:#fff;--color-background:#fff;--color-foreground:#111}",
            encoding="utf-8",
        )
        rc, out, _ = run("contrast", "tw.css", cwd=self.dir)
        self.assertEqual(rc, 1)
        self.assertIn("✗ [light] --color-primary-foreground trên --color-primary  4.1:1", out)
        self.assertIn("✓ [light] --color-foreground trên --color-background", out)
        (self.dir / "bin.css").write_bytes(b"/* \xff\xfe */:root{--background:#fff;--foreground:#000}")
        rc, out, _ = run("contrast", "bin.css", cwd=self.dir)
        self.assertEqual(rc, 0, out)

    def test_json_and_skip_and_no_pairs(self) -> None:
        rc, out, _ = run("contrast", "t.css", "--json", cwd=self.dir)
        data = json.loads(out)
        self.assertEqual(rc, 1)
        self.assertTrue(any(r["status"] == "fail" for r in data["pairs"]))
        (self.dir / "s.css").write_text(":root{--a:lab(1 2 3);--b:#fff;--x:#000;--x-foreground:#fff}", encoding="utf-8")
        (self.dir / "p2.txt").write_text("a on b\n", encoding="utf-8")
        rc, out, _ = run("contrast", "s.css", "--pairs", "p2.txt", cwd=self.dir)
        self.assertEqual(rc, 0, out)
        self.assertIn("– [light] --a trên --b  màu không đọc được", out)
        (self.dir / "e.css").write_text(":root{--a:#fff}", encoding="utf-8")
        rc, _, err = run("contrast", "e.css", cwd=self.dir)
        self.assertEqual(rc, 1)
        self.assertIn("Không có cặp nào để kiểm", err)


class VendorCheckTest(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.enterContext(unittest.mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(self.dir)}))

    def put(self, rel: str, text: str = "x") -> None:
        p = self.dir / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def test_clean_project(self) -> None:
        rc, out, _ = run("vendor-check", cwd=self.dir)
        self.assertEqual((rc, out.strip()), (0, "✓ vendor UI: không vấn đề."))

    def test_vendor_dirs(self) -> None:
        self.put("vendor/ok/LICENSE", "MIT License")
        self.put("vendor/nosrc/file.js")
        self.put("vendor/NOTICE", "ghi nguồn chung")
        self.put("vendor/lone.js")  # file lẻ: có NOTICE ở thư mục vendor
        self.put("third_party/lib/LICENSE.md", "Licensed under the Commons Clause")
        self.put("third_party/solo.js")  # file lẻ, thư mục không có NOTICE
        (self.dir / "external").mkdir()
        rc, out, _ = run("vendor-check", cwd=self.dir)
        self.assertEqual(rc, 1)
        self.assertIn("✗ vendor/nosrc: không có LICENSE/NOTICE/SOURCE", out)
        self.assertNotIn("vendor/ok", out)
        self.assertNotIn("vendor/lone.js", out)
        self.assertIn("third_party/solo.js: không có LICENSE", out)
        self.assertIn("third_party/lib/LICENSE.md: license có điều khoản hạn chế ('Commons Clause')", out)
        rc, out, _ = run("vendor-check", "--dirs", "vendor", cwd=self.dir)
        self.assertNotIn("third_party", out)

    def test_watchlist_hits(self) -> None:
        self.put("package.json", json.dumps({"dependencies": {"preline": "^2"}, "devDependencies": "bad"}))
        self.put("NOTICE", "Template từ once-ui-system/magic-portfolio")
        self.put("vendor/kit/SOURCE", "copied from https://github.com/DavidHDev/react-bits")
        rc, out, _ = run("vendor-check", cwd=self.dir)
        self.assertEqual(rc, 1)  # magic-portfolio = deny
        self.assertIn("✗ magic-portfolio (CC BY-NC 4.0)", out)
        self.assertIn("⚠ Preline", out)
        self.assertIn("⚠ React Bits", out)
        rc, out, _ = run("vendor-check", "--allow", "Magic-Portfolio", cwd=self.dir)
        self.assertEqual(rc, 0)  # chỉ còn cảnh báo
        rc, _, _ = run("vendor-check", "--allow", "magic-portfolio", "--strict", cwd=self.dir)
        self.assertEqual(rc, 1)
        rc, out, _ = run("vendor-check", "--json", "--allow", "magic-portfolio", cwd=self.dir)
        data = json.loads(out)
        self.assertEqual(data["errors"], [])
        self.assertEqual(len(data["warnings"]), 2)
        self.assertEqual(data["checked"], "2026-10-18")

    def test_no_false_positives_and_aliases(self) -> None:
        self.put("vendor/foo/LICENSE", "BSD 3-Clause\nCopyright (c) 2020, Foo\nAll rights reserved.\n")
        self.put("vendor/foo/code.js", "// mentions https://github.com/DavidHDev/react-bits and magic-portfolio")
        pkg = {"name": "my-magic-portfolio-notes", "description": "react-bits and Tailwind UI notes"}
        self.put("package.json", json.dumps(pkg))
        rc, out, _ = run("vendor-check", cwd=self.dir)
        self.assertEqual((rc, out.strip()), (0, "✓ vendor UI: không vấn đề."))
        aliases = {"x": "npm:preline@3", "y": "npm:@tailwindplus/elements@1", "z": "^1"}
        self.put("package.json", json.dumps({"dependencies": aliases}))
        rc, out, _ = run("vendor-check", cwd=self.dir)
        self.assertIn("⚠ Preline", out)
        self.assertIn("⚠ Tailwind Plus", out)

    def test_monorepo_packages_and_node_modules(self) -> None:
        self.put("apps/web/package.json", json.dumps({"dependencies": {"preline": "1"}}))
        self.put("node_modules/dep/package.json", json.dumps({"dependencies": {"react-bits": "1"}}))
        self.put("packages/ui/lib/package.json", json.dumps({"dependencies": {"react-bits": "1"}}))  # sâu 3 cấp: bỏ qua
        rc, out, _ = run("vendor-check", cwd=self.dir)
        self.assertEqual(rc, 0)
        self.assertIn("⚠ Preline", out)
        self.assertNotIn("React Bits", out)

    def test_dangling_symlink_and_outside_dirs(self) -> None:
        self.put("vendor/LICENSE", "MIT")
        (self.dir / "vendor" / "x.js").symlink_to("/nonexistent/target")
        (self.dir / "vendor" / "loop").symlink_to("/nonexistent/dir")
        rc, out, _ = run("vendor-check", cwd=self.dir)
        self.assertEqual((rc, out.strip()), (0, "✓ vendor UI: không vấn đề."))
        self.assertEqual(xt._vendor_notices(self.dir / "khong-co"), [])  # iterdir lỗi → không có file ghi nguồn
        rc, out, _ = run("vendor-check", "--dirs", "../x,vendor", cwd=self.dir)
        self.assertEqual(rc, 1)
        self.assertIn("✗ --dirs ../x: nằm ngoài dự án", out)

    def test_npm_pattern_and_bad_json(self) -> None:
        self.put("package.json", json.dumps({"dependencies": {"@tailwindplus/elements": "1"}}))
        rc, out, _ = run("vendor-check", cwd=self.dir)
        self.assertEqual(rc, 0)
        self.assertIn("⚠ Tailwind Plus", out)
        self.put("package.json", "{không phải json")
        rc, out, _ = run("vendor-check", cwd=self.dir)
        self.assertEqual((rc, out.strip()), (0, "✓ vendor UI: không vấn đề."))

    def test_missing_watchlist_file(self) -> None:
        with unittest.mock.patch.object(xt, "VENDOR_WATCHLIST", self.dir / "none.json"):
            rc, out, _ = run("vendor-check", cwd=self.dir)
        self.assertEqual(rc, 0, out)


if __name__ == "__main__":
    unittest.main()
