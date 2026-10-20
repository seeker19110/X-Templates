"""Audit delta 2026-10-20 lần 3 (`f36ea90..0afa30d`, phần còn lại): mỗi lớp một phát hiện AUD-SEC-* của guard."""

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


PY_EXEC = "import os; os.system('rm -rf ~')"
PY_FENCE = "open('.claude/settings.json','w')"
JS_EXEC = "require('child_process').execSync('rm -rf ~')"


class InterpFlagFormsTest(unittest.TestCase):
    """AUD-SEC-093: script trình thông dịch viết bằng cờ gộp/dính (`-Ic`, `-c"…"`, `--eval=…`, `-nr`, `-e'…'`), tên
    biến thể (`python3.13t`, `nodejs`) hay đứng sau lệnh chạy hộ (`uv run`, `conda run`, `npx`…) từng không được trích
    nên quét `os.system`/`execSync` và D-105 bị bỏ qua — phải xét như dạng chuẩn `python3 -c "…"`."""

    def assertDeny(self, cmd: str) -> None:
        res = policy(cmd)
        self.assertEqual(res["decision"], "deny", (cmd, res))

    def assertAllow(self, cmd: str) -> None:
        res = policy(cmd)
        self.assertNotEqual(res["decision"], "deny", (cmd, res))

    def test_guard_interp_flag_forms_python_clusters(self):
        for flag in ("-Ic", "-Sc", "-Bc", "-sc", "-OOc", "-Ec", "-ic", "-I -c", "-W ignore -Ic", "-Wignore -c"):
            for body in (PY_EXEC, PY_FENCE):
                with self.subTest(flag=flag, body=body):
                    self.assertDeny(f'python3 {flag} "{body}"')

    def test_guard_interp_flag_forms_python_attached(self):
        for cmd in (
            f'python3 -c"{PY_EXEC}"',
            f'python3 -c"{PY_FENCE}"',
            f'python3 -Ic"{PY_FENCE}"',
            f'python3.13t -c "{PY_EXEC}"',
            f'python3.13t -Ic "{PY_FENCE}"',
            f'pypy3 -Sc "{PY_EXEC}"',
        ):
            with self.subTest(cmd=cmd):
                self.assertDeny(cmd)

    def test_guard_interp_flag_forms_node_php_perl_ruby(self):
        for cmd in (
            f'node --eval="{JS_EXEC}"',
            'node --eval=\'require("child_process").execSync("rm -rf ~")\'',
            f'node --print="{JS_EXEC}"',
            f'node -p"{JS_EXEC}"',
            f'node -e"{JS_EXEC}"',
            f'nodejs -e "{JS_EXEC}"',
            f'node -r dotenv/config -e"{JS_EXEC}"',
            f'bun --eval="{JS_EXEC}"',
            "php -nr \"system('rm -rf ~');\"",
            "php -r'system(\"rm -rf ~\");'",
            "php -nR \"system('rm -rf ~');\"",
            "perl -e'system(\"rm -rf ~\")'",
            "perl -ne'system(\"rm -rf ~\")'",
            "perl -Mstrict -lne'system(\"rm -rf ~\")'",
            "ruby -e'system(\"rm -rf ~\")'",
            "ruby -rjson -e'system(\"rm -rf ~\")'",
            "lua -e'os.execute(\"rm -rf ~\")'",
        ):
            with self.subTest(cmd=cmd):
                self.assertDeny(cmd)

    def test_guard_interp_flag_forms_runners(self):
        for cmd in (
            f'uv run python -c "{PY_EXEC}"',
            f'uv run --with x python -c "{PY_EXEC}"',
            f'uv run -n python -Ic "{PY_FENCE}"',
            f'poetry run python -c "{PY_EXEC}"',
            f'pipenv run python -c "{PY_EXEC}"',
            f'pdm run python -c "{PY_EXEC}"',
            f'hatch run python -c "{PY_FENCE}"',
            f'conda run -n x python -c "{PY_EXEC}"',
            f'mamba run -n x python3 -c "{PY_FENCE}"',
            f'pipx run python -c "{PY_EXEC}"',
            f'uv run env python -c "{PY_EXEC}"',
            f'npx node -e "{JS_EXEC}"',
            f'npm exec -- node -e "{JS_EXEC}"',
            f'bunx node -e "{JS_EXEC}"',
            f'uv run npx node --eval="{JS_EXEC}"',
            f'uv run python -c "{PY_FENCE}"',
        ):
            with self.subTest(cmd=cmd):
                self.assertDeny(cmd)

    def test_guard_interp_flag_forms_stdin_heredoc_still_scanned(self):
        """Lệnh chạy hộ trình thông dịch đọc stdin: thân heredoc vẫn là script (như `python3 - <<E`)."""
        self.assertDeny("uv run python - <<'PY'\nimport os\nos.system('rm -rf ~')\nPY")

    def test_guard_interp_flag_forms_controls_allowed(self):
        for cmd in (
            'python3 -Ic "print(1)"',
            'python3 -c"print(1)"',
            "python3 -Ic \"print(open('.claude/settings.json').read())\"",
            "uv run python -m pytest",
            "uv run python -m pytest -sc pytest.ini",
            "python3 -m pytest -sc pytest.ini",
            "python3 -W ignore -m unittest -q",
            "uv run pytest -q",
            "npx eslint .",
            "npm exec -- eslint .",
            "conda run -n x pytest",
            'node --eval="console.log(1)"',
            'node -p"1+1"',
            "perl -ne'print if /x/' docs/a.md",
            "ruby -e'puts 1'",
            "php -r'echo 1;'",
            "node app.js --port 3000",
            "python3 scripts/xt.py validate",
        ):
            with self.subTest(cmd=cmd):
                self.assertAllow(cmd)

    def test_guard_interp_flag_forms_option_parser(self):
        """Bộ tách cờ: cờ có giá trị (`-W x`, `-X x`, `--require x`) không bị coi là script; `-m` kết thúc."""
        scripts = guard._interp_opt_scripts
        self.assertEqual(scripts(["python3", "-W", "-c", "-c", "x"]), ["x"])
        self.assertEqual(scripts(["python3", "-X", "dev", "-Ec", "x"]), ["x"])
        self.assertEqual(scripts(["python3", "-mpytest", "-c", "x"]), [])
        self.assertEqual(scripts(["python3", "--check-hash-based-pycs", "always", "-cx"]), ["x"])
        self.assertEqual(scripts(["python3", "-", "-c", "x"]), [])
        self.assertEqual(scripts(["python3", "--", "-c", "x"]), [])
        self.assertEqual(scripts(["python3", "-I", "-c"]), [])
        self.assertEqual(scripts(["node", "--require", "m", "-px"]), ["x"])
        self.assertEqual(scripts(["node", "--eval", "x"]), ["x"])
        self.assertEqual(scripts(["node", "--inspect", "-ex"]), ["x"])
        self.assertEqual(scripts(["perl", "-i.bak", "-ex"]), ["x"])
        self.assertEqual(scripts(["perl", "-e", "a", "-eb"]), ["a", "b"])
        self.assertEqual(scripts(["tclsh", "-e", "x"]), [])

    def test_guard_interp_flag_forms_runner_argv(self):
        argv = guard._interp_argv
        self.assertEqual(argv(["uv", "run", "--with", "x", "python", "-c", "y"]), ["python", "-c", "y"])
        self.assertEqual(argv(["npx", "eslint", "."]), ["eslint", "."])
        self.assertEqual(argv(["uv", "run", "--frozen"]), ["uv", "run", "--frozen"])
        self.assertEqual(argv(["uv", "sync"]), ["uv", "sync"])
        self.assertEqual(argv([]), [])
        deep = ["npx"] * guard.INTERP_RUNNER_DEPTH + ["node", "-e", "x"]
        self.assertEqual(argv(deep), ["node", "-e", "x"])
        too_deep = ["npx"] * (guard.INTERP_RUNNER_DEPTH + 1) + ["node", "-e", "x"]
        self.assertEqual(argv(too_deep), ["npx", "node", "-e", "x"])  # giới hạn đã biết: dừng bóc sau trần


class NestedCwdRunnersTest(unittest.TestCase):
    """AUD-SEC-094: sau `cd`, nguồn lồng ngoài `sh -c`/`eval`/ống/heredoc (lệnh bọc `flock`/`script`/`su`/`watch`/
    `busybox`, `<( )`, `$(…)`/backtick trong nháy kép, `$(cat <<E …)`, ống giải mã) từng chỉ được quét ở thư mục ban
    đầu. Hai đường (gốc và sau `cd`) nay dùng chung một danh sách nguồn, mỗi script mang thư mục nó chạy."""

    def test_guard_nested_cwd_runners_deny(self):
        for cmd in (
            'cd .claude && echo "$(echo x > settings.json)"',
            "cd .claude && echo `echo x > settings.json`",
            "cd .claude && bash <(echo 'echo x > settings.json')",
            "cd .claude && script -qc 'echo x > settings.json' /dev/null",
            "cd .claude && flock /tmp/l sh -c 'echo x > settings.json'",
            "cd .claude && busybox sh -c 'echo x > settings.json'",
            "cd .claude && watch -n1 'echo x > settings.json'",
            "cd .claude && su -c 'echo x > settings.json'",
            "cd .git && flock /tmp/l sh -c 'echo \"[core]\" >> config'",
            "cd .autopilot && script -qc 'echo {} > verified.json' /dev/null",
            "cd .claude && echo \"$(python3 -c \"open('settings.json','w')\")\"",
            "cd .claude && bash -c \"$(cat <<'E'\necho x > settings.json\nE\n)\"",
            "cd .claude && echo 'echo x > settings.json' | rev | rev | sh",
            'pushd .claude >/dev/null; echo "$(echo x > settings.json)"',
            '(cd .claude && echo "$(echo x > settings.json)")',
            'cd .claude\necho "$(echo x > settings.json)"',
            "cd .claude && cat <<E\n$(echo x > settings.json)\nE",
        ):
            with self.subTest(cmd=cmd):
                res = policy(cmd)
                self.assertEqual(res["decision"], "deny", res)

    def test_guard_nested_cwd_runners_same_as_full_path(self):
        """Cùng lệnh với đường dẫn đầy đủ, không `cd`: đã deny — dạng sau `cd` phải cùng kết quả."""
        for cmd in (
            'echo "$(echo x > .claude/settings.json)"',
            "script -qc 'echo x > .claude/settings.json' /dev/null",
            "bash <(echo 'echo x > .claude/settings.json')",
        ):
            with self.subTest(cmd=cmd):
                self.assertEqual(policy(cmd)["decision"], "deny")

    def test_guard_nested_cwd_runners_controls_allowed(self):
        for cmd in (
            'cd docs && echo "$(date)" > out.txt',
            "cd tests && flock /tmp/l python3 -m unittest -q",
            "cd docs && echo `date` > out.txt",
            "cd docs && script -qc 'echo x > out.txt' /dev/null",
            "cd docs && bash <(echo 'echo x > settings.json')",
            'echo "$(cd .claude && pwd)"; echo "$(echo x > settings.json)"',
            '(cd .claude && ls); echo "$(echo x > settings.json)"',
            "cd .claude && ls # $(echo x > ../docs/a.md)",
        ):
            with self.subTest(cmd=cmd):
                self.assertNotEqual(policy(cmd)["decision"], "deny", cmd)

    def test_guard_nested_cwd_runners_span_dirs(self):
        root = str(ROOT)
        claude = str(ROOT / ".claude")
        text = 'echo "$(a)"; cd .claude && echo "$(b)" `c`'
        spans = guard._dollar_spans(text)
        self.assertEqual(guard._span_dirs(text, spans, root), [root, claude])
        self.assertEqual(guard._span_dirs("echo $(a)", guard._dollar_spans("echo $(a)"), root), [root])
        commented = "cd .claude; # $(a)"
        self.assertEqual(guard._span_dirs(commented, guard._dollar_spans(commented), root), [root])


if __name__ == "__main__":
    unittest.main()
