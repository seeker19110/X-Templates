"""Audit delta 2026-10-20 lần 2 (`f36ea90..0afa30d`): hồi quy của guard sau #185/#186 — mỗi lớp một phát hiện AUD-SEC-*."""

from __future__ import annotations

import os
import sys
import time
import unittest
import unittest.mock as mock
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_guard():
    sys.path.insert(0, str(ROOT / ".claude" / "hooks"))
    import guard as g

    return g


guard = _load_guard()


def policy(cmd: str, cwd: str | None = None) -> dict:
    """Kết quả ở chính sách mặc định (không hỏi): `decision` deny hoặc rỗng, kèm `code`."""
    with mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(ROOT), "XT_GUARD_POLICY": ""}):
        return dict(guard.apply_policy(guard.bash_decision(cmd, str(ROOT), cwd)))


class RoMaskMarkerTest(unittest.TestCase):
    """AUD-SEC-091: script có sẵn byte `\\x01N\\x02` (trùng dấu che chuỗi của `_ro_mask`) từng làm `_ro_lit` đọc ngoài
    mảng → IndexError → guard fail-open cả dòng lệnh, kể cả lệnh cấm nối phía sau."""

    def test_guard_ro_mask_marker_injection(self):
        for cmd in (
            "node -e \"require(\x019\x02);'.env'\"; echo x > .claude/settings.json",
            "perl -e \"open(\x019\x02);'.env'\"; echo x > .claude/settings.json",
            "ruby -e \"File.read(\x010\x02);'.git/config'\"; echo x > .claude/settings.json",
            "node -e \"require(\x019\x02);'.env'\"",
        ):
            with self.subTest(cmd=cmd):
                res = policy(cmd)  # không ném lỗi
                self.assertEqual(res["decision"], "deny", res)

    def test_guard_ro_mask_marker_bytes_not_read_only(self):
        for script in ("require(\x019\x02)", "x = \x01", "print(\x02)"):
            with self.subTest(script=script):
                self.assertIsNone(guard._ro_mask(script))
                self.assertIsNone(guard._ro_mask_py(script))
        self.assertIsNone(guard._ro_lit("\x017\x02", [("'", "a")]))  # chỉ số ngoài mảng → không phải chuỗi đã che


class InterpLiteralPerfTest(unittest.TestCase):
    """AUD-SEC-092: mỗi chuỗi đường dẫn canh trong script dựng một regex quét cả script (`_direct_write`/`_alias_write`)
    → thời gian bậc hai theo số chuỗi (3200 chuỗi: 62 s). Script không có dấu hiệu API ghi → bỏ regex; quá
    `DIRECT_PROBES` chuỗi → coi như ghi (fail-closed)."""

    def _many(self, n: int, extra: str = "") -> str:
        lits = ",".join(f"'.env.a{i}'" for i in range(n))
        return f'python3 -c "print({lits}){extra}"'

    def test_guard_interp_literals_perf(self):
        t0 = time.monotonic()
        res = policy(self._many(3200) + "; echo x > .claude/settings.json")
        self.assertLess(time.monotonic() - t0, 2.0)
        self.assertEqual(res["decision"], "deny", res)

    def test_guard_interp_literals_read_only_passes(self):
        self.assertEqual(policy(self._many(50))["decision"], "", "script chỉ in tên file, không ghi → cho chạy")

    def test_guard_interp_literals_probe_cap_fail_closed(self):
        # có chữ giống API ghi (trong chuỗi — script vẫn chỉ đọc) và quá trần chuỗi canh → coi như ghi, chặn
        cmd = self._many(guard.DIRECT_PROBES + 5, extra=";print('os.remove')")
        t0 = time.monotonic()
        res = policy(cmd)
        self.assertLess(time.monotonic() - t0, 2.0)
        self.assertEqual((res["decision"], res.get("code")), ("deny", "SECRET_WRITE"), res)
        under = self._many(3, extra=";print('os.remove')")
        self.assertEqual(policy(under)["decision"], "", "dưới trần: chữ trong chuỗi không phải ghi thật")

    def test_guard_write_any_covers_direct_and_alias(self):
        """Bỏ regex theo từng chuỗi chỉ an toàn khi mọi dạng `_direct_write`/`_alias_write` đều khớp `WRITE_ANY_RE`."""
        for script in (
            "open('.env','w')",
            "open('.env', os.O_WRONLY)",
            "os.remove('.env')",
            "Path('.env').write_text('x')",
            "P('.env').chmod(0)",
            "Path('.env').open('a')",
            "require('fs').createWriteStream('.env')",
            "os.open('.env', os.O_WRONLY)",
            "fs.openSync('.env', 'a')",
            "os.symlink('x', '.env')",
            "unlink '.env'",
            "open(F, '>', '.env')",
            "py_compile.compile(f, cfile='.env')",
            "p.compile(f, '.env')",
            "sys.pycache_prefix = '.env'",
            "f='.env'; fs.truncateSync(f)",
            "f='.env'; open(f, 'w')",
            "my $f = '.env'; open(my $h, '>', $f)",
            "$f = '.env'; open(F, \">$f\")",
        ):
            with self.subTest(script=script):
                hit = guard._direct_write(script, ".env") or guard._alias_write(script, ".env")
                self.assertTrue(hit, "ca phải là dạng ghi mà regex theo chuỗi bắt được")
                self.assertTrue(guard.WRITE_ANY_RE.search(script))


if __name__ == "__main__":
    unittest.main()
