"""E2E trình duyệt cho app cục bộ `xt.py app` (T-1992, D-133, PRF-WEB-006): 7 màn × 2 viewport, console sạch, không
cuộn ngang ở 390 px, đi được bằng bàn phím, axe 0 vi phạm `critical`/`serious`, một luồng ghi BLUEPRINT.md.

Chạy: `pip install --require-hashes -r requirements-e2e.txt` rồi `python -m playwright install --only-shell chromium`
(CI: `--with-deps`), `python3 -m unittest discover -s tests_e2e`. `XT_E2E_CHROMIUM=<đường chrome/headless_shell>` dùng
trình duyệt có sẵn thay bản Playwright tải. Máy chủ là `xt_app.server.make_server` thật (cổng 0, thread) trên dự án tạm;
`xt._gh_api` bị thay bằng hàm ném `PrInputError` — không gọi `gh`/mạng.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from unittest import mock
from urllib.parse import urlsplit

from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import xt
from xt_app import server

FW = ROOT / "framework"
STATIC = ROOT / "scripts" / "app"
AXE = Path(__file__).resolve().parent / "vendor" / "axe" / "axe.min.js"
# axe được phục vụ bằng `page.route` dưới đúng origin của app nên CSP `script-src 'self'` của app vẫn nguyên (không
# `bypass_csp`): axe là công cụ kiểm của test, không phải mã app, và không nằm trong scripts/app.
AXE_PATH = "/__e2e__/axe.min.js"
AXE_TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"]
BLOCKING = ("critical", "serious")
VIEWPORTS = {"desktop": (1280, 800), "mobile": (390, 844)}
SCREENS: Tuple[Tuple[str, str], ...] = (
    ("", "Tổng quan"),
    ("catalog", "Thư viện yêu cầu"),
    ("compose", "Ghép blueprint"),
    ("blueprint", "Tiến độ blueprint"),
    ("plan", "Kế hoạch và phân chia việc"),
    ("loop", "Vòng tự động"),
    ("pr", "PR"),
)
TIMEOUT_MS = 20000

PLAN = """# PLAN

## Lát 1
- [x] `T-001` dựng khung (files: src/a.py)
- [ ] `T-002` màn chính — Gate: `true` (sau: T-001; files: src/b.py)
- [ ] `T-003` kiểm sâu (exec: deep) (sau: T-002; files: src/c.py)
"""
DECISIONS = """# Nhật ký quyết định

### D-001 · 2026-10-21T10:00:00+00:00 · Chọn cách lưu

- Phương án: (1) Tệp · (2) SQLite
- Chọn: Tệp
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 3: đơn giản.
- Đường lùi: đổi sang SQLite
"""
ADR = "# ADR-0001: Dùng tệp phẳng\n\n- **Trạng thái:** Đã chấp nhận\n"

_pw: Optional[Playwright] = None
_browser: Optional[Browser] = None
_gh_patch = mock.patch.object(xt, "_gh_api", side_effect=xt.PrInputError("không có gh"))


def setUpModule() -> None:
    global _pw, _browser
    _gh_patch.start()
    _pw = sync_playwright().start()
    exe = os.environ.get("XT_E2E_CHROMIUM") or None
    _browser = _pw.chromium.launch(executable_path=exe)


def tearDownModule() -> None:
    if _browser is not None:
        _browser.close()
    if _pw is not None:
        _pw.stop()
    _gh_patch.stop()


def browser() -> Browser:
    assert _browser is not None, "setUpModule chưa chạy"
    return _browser


def compose_blueprint(base: Path) -> None:
    """BLUEPRINT.md ghép thật bằng `xt.py compose` (cùng lệnh người dùng chạy)."""
    cmd = [sys.executable, str(ROOT / "scripts" / "xt.py"), "--framework", str(FW), "compose"]
    cmd += ["--profile", "web-app", "--scale", "S", "--out", str(base / "BLUEPRINT.md")]
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=base, check=False)
    assert res.returncode == 0, res.stderr


def make_project(base: Path, with_blueprint: bool) -> None:
    (base / "docs" / "autopilot").mkdir(parents=True)
    (base / "docs" / "adr").mkdir(parents=True)
    (base / "docs" / "autopilot" / "PLAN.md").write_text(PLAN, encoding="utf-8")
    (base / "docs" / "autopilot" / "DECISIONS.md").write_text(DECISIONS, encoding="utf-8")
    (base / "docs" / "adr" / "0001-flat-files.md").write_text(ADR, encoding="utf-8")
    if with_blueprint:
        compose_blueprint(base)


class AppCase(unittest.TestCase):
    """Một dự án tạm + một máy chủ thật cho mỗi lớp test."""

    with_blueprint = True

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls.base = Path(cls._tmp.name) / "proj"
        make_project(cls.base, cls.with_blueprint)
        cls.srv, cls.token = server.make_server(xt, base=cls.base, framework=FW, static_root=STATIC)
        cls.srv.quiet = True
        cls.origin = f"http://127.0.0.1:{cls.srv.server_address[1]}"
        cls._thread = threading.Thread(target=cls.srv.serve_forever, daemon=True)
        cls._thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.srv.shutdown()
        cls.srv.server_close()
        cls._thread.join(timeout=5)
        cls._tmp.cleanup()

    def new_context(self, viewport: str = "desktop") -> BrowserContext:
        width, height = VIEWPORTS[viewport]
        ctx = browser().new_context(viewport={"width": width, "height": height})
        ctx.set_default_timeout(TIMEOUT_MS)
        self.addCleanup(ctx.close)
        return ctx

    def open_app(self, ctx: BrowserContext) -> Tuple[Page, Watch]:
        """Trang mới mở bằng URL có token (như URL in ở terminal); `Watch` gắn TRƯỚC khi tải để bắt cả lỗi lúc nạp."""
        page = ctx.new_page()
        watch = Watch(page)
        page.goto(f"{self.origin}/#t={self.token}")
        wait_screen(page, "Tổng quan")
        return page, watch


def wait_screen(page: Page, title: str) -> None:
    """Chờ `main h1` đúng tiêu đề và hết mọi trạng thái `.state.loading`."""
    page.locator("main h1").filter(has_text=re.compile(rf"^{re.escape(title)}$")).wait_for()
    page.wait_for_function("() => !document.querySelector('.state.loading')")


def go(page: Page, route: str, title: str) -> None:
    page.evaluate("(r) => { location.hash = '#/' + r; }", route)
    wait_screen(page, title)


class Watch:
    """Thu lỗi console (mức error), lỗi JS chưa bắt và phản hồi 4xx/5xx/thất bại tới `/api/*` của một trang."""

    def __init__(self, page: Page) -> None:
        self.problems: List[str] = []
        page.on("console", self._console)
        page.on("pageerror", lambda e: self.problems.append(f"pageerror: {e}"))
        page.on("response", self._response)
        page.on("requestfailed", lambda r: self._api(r.url) and self.problems.append(f"requestfailed: {r.url}"))

    def _console(self, msg: Any) -> None:
        if msg.type == "error":
            self.problems.append(f"console: {msg.text} @ {msg.location.get('url', '')}")

    @staticmethod
    def _api(url: str) -> bool:
        return urlsplit(url).path.startswith("/api/")

    def _response(self, resp: Any) -> None:
        if self._api(resp.url) and resp.status >= 400:
            self.problems.append(f"{resp.status} {resp.url}")

    def take(self) -> List[str]:
        out, self.problems[:] = list(self.problems), []
        return out


def axe_violations(page: Page, origin: str) -> Tuple[int, List[Dict[str, Any]]]:
    """(số luật đạt, vi phạm mức chặn `critical`/`serious`) của trang hiện tại; nạp axe một lần mỗi tài liệu. Số luật
    đạt > 0 chứng minh axe đã chạy thật trên tài liệu (không phải 0 vi phạm vì không quét gì)."""
    if not page.evaluate("() => typeof window.axe === 'object'"):
        page.add_script_tag(url=origin + AXE_PATH)
    found = page.evaluate(
        """async (tags) => {
            const r = await axe.run(document, {runOnly: {type: 'tag', values: tags}});
            return {passes: r.passes.length, violations: r.violations.map(v => ({id: v.id, impact: v.impact,
                    help: v.help, targets: v.nodes.map(n => n.target.join(' '))}))};
        }""",
        AXE_TAGS,
    )
    return found["passes"], [v for v in found["violations"] if v["impact"] in BLOCKING]


def serve_axe(ctx: BrowserContext, origin: str) -> None:
    ctx.route(origin + AXE_PATH, lambda r: r.fulfill(path=str(AXE), content_type="text/javascript; charset=utf-8"))


def horizontal_overflow(page: Page) -> int:
    return page.evaluate("() => document.documentElement.scrollWidth - window.innerWidth")


def assert_clean(tc: unittest.TestCase, page: Page, watch: Watch, origin: str) -> None:
    """Không lỗi console/JS/API, không cuộn ngang, axe chạy thật và 0 vi phạm `critical`/`serious`."""
    tc.assertEqual(watch.take(), [])
    tc.assertLessEqual(horizontal_overflow(page), 0, "cuộn ngang")
    passes, bad = axe_violations(page, origin)
    tc.assertGreater(passes, 0, "axe không chạy")
    tc.assertEqual(bad, [], "\n".join(f"{v['impact']} {v['id']}: {v['help']} → {v['targets']}" for v in bad))
    tc.assertEqual(watch.take(), [])  # axe không gây lỗi console


class ScreensTest(AppCase):
    """PRF-WEB-006: mọi màn × hai viewport — tải không lỗi, không cuộn ngang, axe 0 vi phạm critical/serious."""

    def test_every_screen_every_viewport(self) -> None:
        checked = 0
        for name in VIEWPORTS:
            ctx = self.new_context(name)
            serve_axe(ctx, self.origin)
            page = ctx.new_page()
            watch = Watch(page)
            page.goto(f"{self.origin}/#t={self.token}")
            wait_screen(page, "Tổng quan")
            for route, title in SCREENS:
                with self.subTest(viewport=name, screen=route or "overview"):
                    go(page, route, title)
                    self.check_screen(page, watch, route)
                    checked += 1
        self.assertEqual(checked, len(VIEWPORTS) * len(SCREENS))

    def check_screen(self, page: Page, watch: Watch, route: str) -> None:
        if route == "pr":  # không có gh: màn PR báo rõ, các màn khác vẫn dùng được
            page.get_by_text("Không đọc được GitHub").wait_for()
        assert_clean(self, page, watch, self.origin)

    def test_catalog_module_detail_mobile(self) -> None:
        """Trạng thái sâu hơn của màn Thư viện ở 390 px: mở mảng, chọn module → danh sách mục dài."""
        ctx = self.new_context("mobile")
        serve_axe(ctx, self.origin)
        page, watch = self.open_app(ctx)
        go(page, "catalog", "Thư viện yêu cầu")
        with_must = page.locator("button.link").filter(has_text=re.compile(r"\([1-9]\d*/"))  # module có MUST
        area = page.locator("main details").filter(has=with_must).first
        area.locator("summary").click()
        area.locator("button.link").filter(has_text=re.compile(r"\([1-9]\d*/")).first.click()
        page.locator("main section ul.items li").first.wait_for()
        assert_clean(self, page, watch, self.origin)


class KeyboardTest(AppCase):
    """Đi bằng bàn phím: link bỏ qua là điểm Tab đầu, Enter không đổi màn; Tab tới nav, Enter chuyển màn, focus vào main."""

    def active(self, page: Page) -> Dict[str, Any]:
        return page.evaluate(
            "() => { const a = document.activeElement;"
            " return {tag: a.tagName, id: a.id, text: a.textContent.trim(), href: a.getAttribute('href')}; }"
        )

    def test_skip_link_first_and_keeps_screen(self) -> None:
        page, watch = self.open_app(self.new_context())
        page.keyboard.press("Tab")
        self.assertEqual(self.active(page)["text"], "Bỏ qua tới nội dung")
        page.keyboard.press("Enter")
        page.wait_for_function("() => document.activeElement && document.activeElement.id === 'main'")
        self.assertEqual(page.locator("main h1").inner_text(), "Tổng quan")
        self.assertEqual(page.locator("nav a[aria-current=page]").get_attribute("href"), "#/")
        self.assertEqual(watch.take(), [])

    def test_tab_to_nav_enter_moves_focus_to_main(self) -> None:
        page, watch = self.open_app(self.new_context("mobile"))
        seen = []
        for _ in range(4):
            page.keyboard.press("Tab")
            seen.append(self.active(page)["href"])
            if seen[-1] == "#/catalog":
                break
        self.assertEqual(seen, ["#main", "#/", "#/catalog"])
        page.keyboard.press("Enter")
        wait_screen(page, "Thư viện yêu cầu")
        page.wait_for_function("() => document.activeElement && document.activeElement.id === 'main'")
        self.assertEqual(page.locator("nav a[aria-current=page]").get_attribute("href"), "#/catalog")
        self.assertEqual(watch.take(), [])


class TokenTest(AppCase):
    """Phân quyền: có token → API trả 200; không token → app báo mở lại bằng URL; token sai → API từ chối."""

    def fetch_status(self, page: Page, token: str) -> int:
        return page.evaluate("async (t) => (await fetch('/api/overview', {headers: {'X-XT-Token': t}})).status", token)

    def test_allowed_with_token(self) -> None:
        page, _watch = self.open_app(self.new_context())
        self.assertEqual(self.fetch_status(page, self.token), 200)

    def test_denied_without_or_with_wrong_token(self) -> None:
        page = self.new_context().new_page()
        page.goto(self.origin + "/")
        page.get_by_role("alert").filter(has_text="Mở lại bằng URL in ở terminal.").wait_for()
        self.assertGreaterEqual(self.fetch_status(page, "sai-" + self.token), 400)
        self.assertGreaterEqual(self.fetch_status(page, ""), 400)


class ConcurrentTest(AppCase):
    """Hai tab cùng tải màn nhiều request song song (Vòng tự động: 3 API cùng lúc) — không lỗi, không lẫn dữ liệu."""

    def test_two_tabs_load_together(self) -> None:
        ctx = self.new_context()
        pages = [ctx.new_page(), ctx.new_page()]
        watches = [Watch(p) for p in pages]
        for p in pages:
            p.goto(f"{self.origin}/#t={self.token}", wait_until="commit")
        for p in pages:
            wait_screen(p, "Tổng quan")
            p.evaluate("() => { location.hash = '#/loop'; }")
        for p, w in zip(pages, watches):
            wait_screen(p, "Vòng tự động")
            p.get_by_text("D-001").wait_for()
            self.assertEqual(w.take(), [])


class ComposeWriteTest(AppCase):
    """Luồng ghi: Ghép blueprint `cli-tool` quy mô S → Xem trước (số MUST) → Ghi BLUEPRINT.md (xác nhận) → file có thật."""

    with_blueprint = False

    def test_preview_then_write(self) -> None:
        ctx = self.new_context("mobile")  # bản xem trước dài nhất ở viewport hẹp: kiểm cuộn ngang + axe
        serve_axe(ctx, self.origin)
        page, watch = self.open_app(ctx)
        go(page, "compose", "Ghép blueprint")
        page.select_option("#cp-profile", "cli-tool")
        page.select_option("#cp-scale", "S")
        page.get_by_role("button", name="Xem trước").click()
        counts = page.locator("main section p").filter(has_text=re.compile(r"^MUST \d+ · SHOULD \d+"))
        counts.wait_for()
        must = int(re.match(r"MUST (\d+)", counts.inner_text()).group(1))
        self.assertGreater(must, 0)
        assert_clean(self, page, watch, self.origin)
        self.assertFalse((self.base / "BLUEPRINT.md").exists())
        dialogs: List[str] = []
        page.on("dialog", lambda d: (dialogs.append(d.message), d.accept()))
        page.get_by_role("button", name="Ghi BLUEPRINT.md").click()
        page.get_by_text(re.compile(r"^Đã ghi ")).wait_for()
        self.assertEqual(len(dialogs), 1)
        text = (self.base / "BLUEPRINT.md").read_text(encoding="utf-8")
        self.assertEqual(len(re.findall(r"^- \[ \] `[A-Z0-9-]+` \*\*MUST\*\*", text, re.M)), must)
        self.assertEqual(watch.take(), [])


if __name__ == "__main__":
    unittest.main()
