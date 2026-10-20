"""Audit delta 2026-10-20: script trình thông dịch ghi file hàng rào/bí mật/bằng chứng/cấu hình git lọt chính sách
mặc định (ADR-0018) — mỗi lớp một phát hiện AUD-SEC-*."""

from __future__ import annotations

import os
import sys
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


class InterpGitConfigTest(unittest.TestCase):
    """AUD-SEC-083: script trình thông dịch ghi `.git/config`/`.git/hooks/*` = bỏ qua hook như `echo x >> .git/config`."""

    def test_guard_interp_git_config(self):
        for cmd in (
            "python3 -c \"open('.git/config','a').write('x')\"",
            "python3 -c \"open('.git/hooks/pre-commit','w').write('#!/bin/sh')\"",
            "python3 -c \"import os; os.remove('.git/hooks/pre-commit')\"",
            "node -e \"require('fs').appendFileSync('.git/config','x')\"",
            "node -e \"require('fs').writeFileSync('.git/hooks/pre-push','exit 0')\"",
            "perl -e \"open(F, '>>', '.git/config'); print F 'x'\"",
            "ruby -e \"File.write('.git/config', 'x')\"",
            "python3 -c \"from pathlib import Path; Path('.git/hooks/pre-commit').write_text('')\"",
            "python3 - <<'PY'\nopen('.git/config','a').write('[core]')\nPY",
            "echo x >> .git/config",  # đối chứng: đường shell đã chặn
        ):
            with self.subTest(cmd=cmd):
                res = policy(cmd)
                self.assertEqual((res["decision"], res.get("code")), ("deny", "HOOK_BYPASS"), res)

    def test_guard_interp_git_config_read_or_other_passes(self):
        for cmd in (
            "python3 -c \"print(open('.git/config').read())\"",
            "python3 -c \"import configparser; c=configparser.ConfigParser(); c.read('.git/config')\"",
            "python3 -c \"open('out.txt','w').write(open('.git/config').read())\"",
            "node -e \"console.log(require('fs').readFileSync('.git/config','utf8'))\"",
        ):
            with self.subTest(cmd=cmd):
                self.assertEqual(policy(cmd)["decision"], "", cmd)


class InterpCwdTest(unittest.TestCase):
    """AUD-SEC-085: đích ghi của script trình thông dịch tính từ thư mục lệnh đang đứng (`cd` trước đó), như đường shell."""

    def test_guard_interp_cwd(self):
        cases = {
            "cd .claude && python3 -c \"open('settings.local.json','w').write('{}')\"": "HOOK_BYPASS",
            "cd .claude/hooks; python3 -c \"open('guard.py','w').write('')\"": "HOOK_BYPASS",
            "cd .autopilot && python3 -c \"open('verified.json','w').write('{}')\"": "EVIDENCE_HANDWRITE",
            "cd .git && python3 -c \"open('config','a').write('x')\"": "HOOK_BYPASS",
            "cd .git/hooks && node -e \"require('fs').writeFileSync('pre-commit','')\"": "HOOK_BYPASS",
            "cd docs && python3 -c \"open('../.env','w').write('K=1')\"": "SECRET_WRITE",
            "pushd .autopilot && python3 - <<'PY'\nopen('verified.json','w').write('{}')\nPY": "EVIDENCE_HANDWRITE",
        }
        for cmd, code in cases.items():
            with self.subTest(cmd=cmd):
                res = policy(cmd)
                self.assertEqual((res["decision"], res.get("code")), ("deny", code), res)
        # thư mục của phiên (payload `cwd`) cũng là gốc tính đích tương đối
        res = policy("python3 -c \"open('verified.json','w').write('{}')\"", str(ROOT / ".autopilot"))
        self.assertEqual((res["decision"], res.get("code")), ("deny", "EVIDENCE_HANDWRITE"), res)

    def test_guard_interp_cwd_other_dir_passes(self):
        for cmd in (
            "cd docs && python3 -c \"open('settings.local.json','w').write('{}')\"",
            "cd scripts && python3 -c \"open('verified.json','w').write('{}')\"",
            "(cd .claude && ls); python3 -c \"open('settings.local.json','w').write('{}')\"",
            "cd .claude && python3 -c \"print(open('settings.json').read())\"",
        ):
            with self.subTest(cmd=cmd):
                self.assertEqual(policy(cmd)["decision"], "", cmd)


if __name__ == "__main__":
    unittest.main()
