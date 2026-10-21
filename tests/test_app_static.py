"""Kiểm tĩnh scripts/app/ (SPEC-app §6, RK-2): chỉ đọc file, không cần trình duyệt."""

import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

APP = Path(__file__).resolve().parent.parent / "scripts" / "app"
FORBIDDEN_JS = [
    r"\binnerHTML\b",
    r"\bouterHTML\b",
    r"\binsertAdjacentHTML\b",
    r"\bdocument\.write\b",
    r"\beval\s*\(",
    r"\bnew\s+Function\b",
]


def read_utf8(path: Path) -> str:
    return path.read_bytes().decode("utf-8")  # strict


def forbidden_js(text: str) -> list[str]:
    return [p for p in FORBIDDEN_JS if re.search(p, text)]


class _Scan(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.errors: list[str] = []
        self.html_lang: str | None = None
        self.scripts: list[dict[str, str | None]] = []
        self.nav_hrefs: list[str] = []
        self._in_script = False
        self._in_nav = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        for name in a:
            if name.startswith("on"):
                self.errors.append(f"thuộc tính {name}= trong <{tag}>")
            if name == "style":
                self.errors.append(f"thuộc tính style= trong <{tag}>")
        if tag == "style":
            self.errors.append("thẻ <style>")
        if tag == "html":
            self.html_lang = a.get("lang")
        if tag == "script":
            self._in_script = True
            self.scripts.append(a)
            if not a.get("src"):
                self.errors.append("<script> không có src")
        if tag == "nav":
            self._in_nav = True
        if tag == "a" and self._in_nav and a.get("href"):
            self.nav_hrefs.append(a["href"] or "")

    def handle_endtag(self, tag):
        if tag == "script":
            self._in_script = False
        if tag == "nav":
            self._in_nav = False

    def handle_data(self, data):
        if self._in_script and data.strip():
            self.errors.append("<script> có nội dung inline")


def scan_html(text: str) -> _Scan:
    p = _Scan()
    p.feed(text)
    p.close()
    return p


def view_names() -> set[str]:
    return {p.stem for p in (APP / "views").glob("*.js")}


def nav_views(hrefs: list[str]) -> set[str]:
    out = set()
    for href in hrefs:
        m = re.fullmatch(r"#/([\w-]*)", href)
        if m:
            out.add(m.group(1) or "overview")
    return out


class AppStaticTest(unittest.TestCase):
    def setUp(self):
        self.html = scan_html(read_utf8(APP / "index.html"))

    def test_utf8_strict(self):
        files = [p for p in APP.rglob("*") if p.suffix in {".js", ".html", ".css"}]
        self.assertGreaterEqual(len(files), 10)
        for p in files:
            read_utf8(p)

    def test_no_forbidden_js(self):
        for p in APP.rglob("*.js"):
            self.assertEqual(forbidden_js(read_utf8(p)), [], str(p))

    def test_html_no_inline(self):
        self.assertEqual(self.html.errors, [])

    def test_nav_matches_views(self):
        self.assertEqual(len(self.html.nav_hrefs), 7)
        self.assertEqual(nav_views(self.html.nav_hrefs), view_names())

    def test_lang_vi(self):
        self.assertEqual(self.html.html_lang, "vi")

    def test_scripts_module_and_rooted(self):
        self.assertTrue(self.html.scripts)
        for s in self.html.scripts:
            self.assertEqual(s.get("type"), "module")
            self.assertTrue((s.get("src") or "").startswith("/"))

    def test_views_export_render(self):
        for name in view_names():
            text = read_utf8(APP / "views" / f"{name}.js")
            self.assertRegex(text, r"export\s+async\s+function\s+render\s*\(", name)

    def test_negative_checks_detect(self):
        self.assertTrue(forbidden_js("el.innerHTML = x"))
        self.assertTrue(forbidden_js("eval(code)"))
        self.assertFalse(forbidden_js("el.textContent = x"))
        bad = scan_html(
            '<html lang="vi"><button onclick="x()" style="a:b">z</button><style>a{}</style><script>1</script>'
        )
        self.assertTrue(any("onclick" in e for e in bad.errors))
        self.assertTrue(any("style=" in e for e in bad.errors))
        self.assertTrue(any("<style>" in e for e in bad.errors))
        self.assertTrue(any("inline" in e for e in bad.errors))
        self.assertEqual(nav_views(["#/", "#/pr", "http://x"]), {"overview", "pr"})


if __name__ == "__main__":
    unittest.main()
