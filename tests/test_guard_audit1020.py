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


class NestedCwdTest(unittest.TestCase):
    """AUD-SEC-087: shell lồng sau `cd` chạy trong thư mục của lệnh đó — `cd .claude && bash -c "echo x > settings.json"`
    là ghi `.claude/settings.json` như `echo x > .claude/settings.json`, không được quét với thư mục ban đầu."""

    def test_guard_nested_cwd(self):
        cases = {
            'cd .claude && bash -c "echo x > settings.json"': "HOOK_BYPASS",
            "cd .claude; sh -c 'echo x > settings.local.json'": "HOOK_BYPASS",
            "cd .claude/hooks && bash -lc 'echo > guard.py'": "HOOK_BYPASS",
            'cd .claude && eval "echo x > settings.json"': "HOOK_BYPASS",
            "cd .claude && bash <<< 'echo x > settings.json'": "HOOK_BYPASS",
            "cd .claude && echo 'echo x > settings.json' | bash": "HOOK_BYPASS",
            "cd .claude && bash <<'E'\necho x > settings.json\nE": "HOOK_BYPASS",
            "cd .claude && uv run bash -c 'echo x > settings.json'": "HOOK_BYPASS",
            "cd .claude && python3 -c \"import os; os.system('echo x > settings.json')\"": "HOOK_BYPASS",
            'cd .autopilot && bash -c "echo {} > verified.json"': "EVIDENCE_HANDWRITE",
            'cd docs && bash -c "echo K=1 > ../.env"': "SECRET_WRITE",
            "bash -c 'cd .claude && bash -c \"echo x > settings.json\"'": "HOOK_BYPASS",
            # cùng chuỗi lệnh lồng ở hai thư mục: lần ở gốc vẫn được quét
            "cd .claude && bash -c 'echo x > .claude/settings.json'; cd .. && bash -c 'echo x > .claude/settings.json'": (
                "HOOK_BYPASS"
            ),
        }
        for cmd, code in cases.items():
            with self.subTest(cmd=cmd):
                res = policy(cmd)
                self.assertEqual((res["decision"], res.get("code")), ("deny", code), res)

    def test_guard_nested_cwd_other_dir_passes(self):
        for cmd in (
            'cd docs && bash -c "echo x > a.md"',
            'cd docs && bash -c "echo x > settings.json"',
            "(cd .claude && ls); bash -c 'echo x > settings.json'",
            'cd .claude && bash -c "cat settings.json"',
        ):
            with self.subTest(cmd=cmd):
                self.assertEqual(policy(cmd)["decision"], "", cmd)


class InterpAliasWriteTest(unittest.TestCase):
    """AUD-SEC-084: script ghi file hàng rào/bí mật/bằng chứng qua biến hoặc bí danh (`p='.env'; open(p,'w')`,
    `Path as P`) → mã chặn như ghi trực tiếp, không phải ask thường mà chính sách mặc định cho qua."""

    def test_guard_interp_alias_write(self):
        cases = {
            "python3 -c \"p='.claude/settings.local.json'; open(p,'w').write('{}')\"": "HOOK_BYPASS",
            "python3 -c \"f='.env'; open(f,'w').write('x')\"": "SECRET_WRITE",
            "python3 -c \"f = '.env'\nwith open(f, mode='a') as h: h.write('x')\"": "SECRET_WRITE",
            "python3 -c \"f='.autopilot/verified.json'; open(f,'w').write('x')\"": "EVIDENCE_HANDWRITE",
            "python3 -c \"from pathlib import Path as P; P('.claude/hooks/guard.py').write_text('x')\"": "HOOK_BYPASS",
            "python3 -c \"from pathlib import Path; p = Path('.claude/hooks/guard.py'); p.write_text('x')\"": "HOOK_BYPASS",
            "python3 -c \"import pathlib; p = pathlib.Path('.env'); p.unlink()\"": "SECRET_WRITE",
            "python3 -c \"import os; t='.autopilot/state.json'; os.remove(t)\"": "EVIDENCE_HANDWRITE",
            "python3 -c \"import shutil; d='.claude/settings.json'; shutil.copy('x.json', d)\"": "HOOK_BYPASS",
            "python3 -c \"a='.env'; b=a; open(b,'w').write('x')\"": "SECRET_WRITE",
            "python3 -c \"f='.env'; f = f.strip(); open(f,'w').write('x')\"": "SECRET_WRITE",  # gán lại chính nó
            "python3 -c \"for f in ['.autopilot/verified.json']: open(f,'w').write('{}')\"": "EVIDENCE_HANDWRITE",
            "node -e \"const fs=require('fs'); const f='.env'; fs.writeFileSync(f,'x')\"": "SECRET_WRITE",
            "node -e \"let f='.claude/settings.json'; require('fs').appendFileSync(f, '{}')\"": "HOOK_BYPASS",
            "perl -e \"my \\$f = '.env'; open(my \\$h, '>', \\$f); print \\$h 'x'\"": "SECRET_WRITE",
            'perl -e "my \\$f = \'.autopilot/x.json\'; open(F, \\">\\$f\\")"': "EVIDENCE_HANDWRITE",
            "ruby -e \"f = '.env'; File.write(f, 'x')\"": "SECRET_WRITE",
            "php -r \"\\$f = '.env'; file_put_contents(\\$f, 'x');\"": "SECRET_WRITE",
            "python3 -c \"g='.git/config'; open(g,'a').write('x')\"": "HOOK_BYPASS",
            "cd .claude && python3 -c \"p='settings.local.json'; open(p,'w').write('{}')\"": "HOOK_BYPASS",
        }
        for cmd, code in cases.items():
            with self.subTest(cmd=cmd):
                res = policy(cmd)
                self.assertEqual((res["decision"], res.get("code")), ("deny", code), res)

    def test_guard_interp_alias_write_controls(self):
        """Đối chứng (không chặn oan): chỉ đọc file bí mật, ghi file khác mà nhắc tên `.env`/hook trong chuỗi in ra hay
        nội dung, đổi chữ trong tài liệu, biến không tới lời gọi ghi."""
        for cmd in (
            "python3 -c \"f='.env'; print(open(f).read())\"",
            "python3 -c \"import os; f='.env'; print(os.path.exists(f))\"",
            "python3 -c \"print('.env'); open('out.txt','w').write('x')\"",
            "python3 -c \"f='.env'; print('bỏ qua', f); open('out.txt','w').write('x')\"",
            "python3 -c \"n='.env'; open('README.md','w').write('Đặt khoá vào ' + n)\"",
            "python3 -c \"from pathlib import Path; p=Path('README.md'); old='.claude/hooks/guard.py'; "
            "p.write_text(p.read_text().replace(old, 'hooks/guard.py'))\"",
            "node -e \"const f='.env'; const fs=require('fs'); fs.writeFileSync('out.txt', 'see ' + f)\"",
            "python3 -c \"src='.env.example'; open('notes.txt','w').write(src)\"",
            "python3 -c \"f='.env'; data=open(f).read(); open('copy.txt','w').write(str(len(data)))\"",
        ):
            with self.subTest(cmd=cmd):
                self.assertEqual(policy(cmd)["decision"], "", cmd)


class CdRedirectFlagsTest(unittest.TestCase):
    """AUD-SEC-088: `cd`/`pushd` kèm chuyển hướng (`2>/dev/null`, `>/dev/null`) hay cờ (`-P`, `-L`, `-e`, `--`) vẫn dời
    thư mục — lệnh sau phải được quét ở thư mục mới, không như đang ở gốc dự án."""

    def test_guard_cd_redirect_flags(self):
        cases = {
            "cd .claude >/dev/null && bash -c 'echo x > settings.json'": "HOOK_BYPASS",
            "pushd .claude >/dev/null && python3 -c \"open('settings.json','w')\"": "HOOK_BYPASS",
            "cd -P .claude && echo x > settings.json": "HOOK_BYPASS",
            "cd .claude 2>/dev/null; echo x > settings.json": "HOOK_BYPASS",
            "cd -L .claude && echo x > settings.json": "HOOK_BYPASS",
            "cd -- .claude && echo x > settings.json": "HOOK_BYPASS",
            "cd -e .claude && echo x > settings.json": "HOOK_BYPASS",
            "cd -P -e .claude 2> /dev/null && echo x > settings.json": "HOOK_BYPASS",
            "cd .claude &>/dev/null && echo x > settings.json": "HOOK_BYPASS",
            "pushd -- .autopilot > /dev/null && echo {} > verified.json": "EVIDENCE_HANDWRITE",
            "cd docs 2>/dev/null && echo K=1 > ../.env": "SECRET_WRITE",
        }
        for cmd, code in cases.items():
            with self.subTest(cmd=cmd):
                res = policy(cmd)
                self.assertEqual((res["decision"], res.get("code")), ("deny", code), res)

    def test_guard_cd_redirect_flags_controls(self):
        for cmd in (
            "cd docs 2>/dev/null && echo x > a.md",
            "cd -P docs && echo x > settings.json",
            "pushd docs >/dev/null && bash -c 'echo x > settings.json'",
            "cd .claude 2>/dev/null && cat settings.json",
        ):
            with self.subTest(cmd=cmd):
                self.assertEqual(policy(cmd)["decision"], "", cmd)

    def test_cd_target_parsing(self):
        here = "/p"
        self.assertEqual(guard._cd_target(guard.tokenize("cd .claude 2>/dev/null"), here), "/p/.claude")
        self.assertEqual(guard._cd_target(["cd", "-P", "-L", "--", "a"], here), "/p/a")
        self.assertEqual(guard._cd_target(["cd", "--", "-x"], here), "/p/-x")
        self.assertIsNone(guard._cd_target(["cd", "-"], here))
        self.assertIsNone(guard._cd_target(["cd", "-P"], here))
        self.assertIsNone(guard._cd_target(["cd", "-x", "a"], here))  # cờ lạ: không đoán
        self.assertIsNone(guard._cd_target(["cd", "a", "b"], here))
        self.assertIsNone(guard._cd_target(["pushd", "+1"], here))


if __name__ == "__main__":
    unittest.main()
