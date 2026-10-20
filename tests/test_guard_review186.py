"""Review PR #186 lần 1: lọt còn lại sau AUD-SEC-088/089 — cd tới thư mục guard không giải được (cờ ghép, chuyển hướng
đầu lệnh, CDPATH) và script trình thông dịch ghi đường dẫn được canh qua API ngoài danh sách. Sửa theo D-105 (script
nhắc đường dẫn được canh: mặc định chặn, trừ khi toàn script chỉ đọc) và D-106 (cwd không biết: thử mọi thư mục canh)."""

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


class CdUnresolvedTest(unittest.TestCase):
    """D-106: `cd` guard không giải được → cwd không biết; đích ghi tương đối thử ở mọi thư mục canh."""

    def test_guard_cd_unresolved_denied(self):
        cases = {
            "cd -LP .claude && echo x > settings.json": "HOOK_BYPASS",
            "cd -Pe .claude && echo x > settings.json": "HOOK_BYPASS",
            "cd -e@ .claude/hooks && echo x > guard.py": "HOOK_BYPASS",
            "2>/dev/null cd .claude && echo x > settings.json": "HOOK_BYPASS",
            ">/dev/null pushd .autopilot && echo {} > verified.json": "EVIDENCE_HANDWRITE",
            f"CDPATH={ROOT}/.claude cd hooks && echo x > guard.py": "HOOK_BYPASS",
            f"export CDPATH={ROOT}/.claude; cd hooks && echo x > guard.py": "HOOK_BYPASS",
            f"CDPATH={ROOT}/.claude; cd hooks && echo x > guard.py": "HOOK_BYPASS",
            # biến/`cd -`/`pushd +N`: không biết → thử mọi thư mục canh
            'cd "$X" && echo x > settings.json': "HOOK_BYPASS",
            "cd $PWD && echo x > guard.py": "HOOK_BYPASS",
            "cd - && echo {} > verified.json": "EVIDENCE_HANDWRITE",
            "pushd +1 && echo x > config": "HOOK_BYPASS",
            "cd $X && echo x > pre-commit": "HOOK_BYPASS",
            "cd $X && echo K=1 > .env": "SECRET_WRITE",
            "cd $X && echo x > $PWD/settings.json": "HOOK_BYPASS",
            "cd - && echo x > ${CLAUDE_PROJECT_DIR}/.claude/settings.json": "HOOK_BYPASS",
            # đường script và shell lồng cũng theo cwd không biết
            "cd $X && python3 -c \"open('settings.json','w')\"": "HOOK_BYPASS",
            "cd $X && bash -c 'echo x > guard.py'": "HOOK_BYPASS",
            "popd; echo x > settings.local.json": "HOOK_BYPASS",
        }
        for cmd, code in cases.items():
            with self.subTest(cmd=cmd):
                res = policy(cmd)
                self.assertEqual((res["decision"], res.get("code")), ("deny", code), res)

    def test_guard_sec090_now_covered(self):
        """AUD-SEC-090: `cd "$PWD/…"` (thư mục không biết) và đường dẫn trong phần tử list nay bị chặn."""
        cases = {
            'cd "$PWD/.claude" && echo x > settings.json': "HOOK_BYPASS",
            "python3 -c \"open(['.env'][0],'w')\"": "SECRET_WRITE",
            "python3 -c \"d={'p': '.git/config'}; open(d['p'],'a')\"": "HOOK_BYPASS",
        }
        for cmd, code in cases.items():
            with self.subTest(cmd=cmd):
                res = policy(cmd)
                self.assertEqual((res["decision"], res.get("code")), ("deny", code), res)

    def test_guard_cd_unresolved_controls(self):
        for cmd in (
            "cd docs 2>/dev/null && echo x > a.md",
            "cd -LP /tmp && echo x > a.txt",
            "cd unknown_dir && echo x > notes.txt",
            "cd $X && echo x > notes.txt",
            "cd $X && echo x > /tmp/settings.json",
            'echo "print(1)" | python3',
            "cd $X && python3 -c \"open('out.txt','w').write('x')\"",
            "cd - && cat settings.json",
            "2>/dev/null cd docs && echo x > settings.json",
            f"CDPATH={ROOT}/.claude cd /tmp && echo x > guard.py",
        ):
            with self.subTest(cmd=cmd):
                self.assertEqual(policy(cmd)["decision"], "", cmd)

    def test_cd_target_parsing(self):
        here = "/p"
        self.assertEqual(guard._cd_target(["cd", "-LP", "a"], here), "/p/a")
        self.assertEqual(guard._cd_target(["cd", "-Pe@", "--", "a"], here), "/p/a")
        self.assertIsNone(guard._cd_target(["cd", "-Lx", "a"], here))  # cờ lạ trong cờ ghép: không đoán
        self.assertIsNone(guard._cd_target(["cd", "a"], here, cdpath=True))
        self.assertEqual(guard._cd_target(["cd", "/x"], here, cdpath=True), "/x")
        self.assertEqual(guard._cd_target(["cd", "/x"], None), "/x")  # tuyệt đối: biết dù trước đó không biết
        self.assertIsNone(guard._cd_target(["cd", "a"], None))
        self.assertEqual(guard.normalize(guard.tokenize("2>/dev/null cd a")), ["cd", "a"])
        self.assertEqual(guard.normalize(guard.tokenize(">/dev/null 2>&1 rm -rf x")), ["rm", "-rf", "x"])

    def test_leading_redirect_rules_apply(self):
        """Chuyển hướng đặt đầu lệnh không che lệnh thật (`>/dev/null rm -rf ~`)."""
        res = policy(">/dev/null rm -rf ~")
        self.assertEqual(res["decision"], "deny", res)


class InterpDefaultDenyTest(unittest.TestCase):
    """D-105: script trình thông dịch nhắc đường dẫn được canh mà không chỉ gồm thao tác đọc → chặn theo mã của đích."""

    def test_guard_interp_default_deny(self):
        cases = {
            "python3 -c \"import os; os.open('.git/hooks/pre-commit',577)\"": "HOOK_BYPASS",
            "node -e \"require('fs').openSync('.git/hooks/pre-commit',1)\"": "HOOK_BYPASS",
            "node -e \"require('fs').rename('/tmp/a','.git/hooks/pre-commit',()=>{})\"": "HOOK_BYPASS",
            "node -e \"require('fs').cpSync('/tmp/a','.claude/settings.json')\"": "HOOK_BYPASS",
            "node -e \"require('fs').truncateSync('.env')\"": "SECRET_WRITE",
            "ruby -e \"File.rename('/tmp/a','.git/config')\"": "HOOK_BYPASS",
            "ruby -e \"File.delete('.autopilot/verified.json')\"": "EVIDENCE_HANDWRITE",
            "ruby -e \"File.binwrite('.git/config','x')\"": "HOOK_BYPASS",
            "ruby -e \"require 'fileutils'; FileUtils.cp('/tmp/a','.claude/settings.json')\"": "HOOK_BYPASS",
            "ruby -e \"require 'fileutils'; FileUtils.mv('/tmp/a','.env')\"": "SECRET_WRITE",
            "ruby -e \"File.delete '.env'\"": "SECRET_WRITE",
            "perl -e \"rename('/tmp/a','.git/config')\"": "HOOK_BYPASS",
            "perl -e \"use File::Copy; copy('/tmp/a','.env')\"": "SECRET_WRITE",
            "perl -e \"use File::Copy; move('/tmp/a','.claude/hooks/guard.py')\"": "HOOK_BYPASS",
            "php -r \"copy('/tmp/a','.env');\"": "SECRET_WRITE",
            "php -r \"rename('/tmp/a','.git/hooks/pre-commit');\"": "HOOK_BYPASS",
            "python3 -c \"import tarfile; tarfile.open('/tmp/a.tar').extractall('.git/hooks')\"": "HOOK_BYPASS",
            "python3 -c \"import sqlite3; sqlite3.connect('.autopilot/x.db')\"": "EVIDENCE_HANDWRITE",
            "python3 -c \"import os; os.utime('.git/hooks/pre-commit')\"": "HOOK_BYPASS",
            "python3 -c \"import os; os.makedirs('.claude/hooks/x')\"": "HOOK_BYPASS",
            "python3 -c \"import logging; logging.FileHandler('.env')\"": "SECRET_WRITE",
            # dạng lách allowlist: mode biến, gọi gián tiếp, f-string, nội suy, bí danh hàm, gán thuộc tính
            "python3 -c \"m='w'; open('.env', m)\"": "SECRET_WRITE",
            "python3 -c \"from pathlib import Path; m='w'; p=Path('.env'); p.open(m)\"": "SECRET_WRITE",
            "python3 -c \"import os; getattr(os,'remove')('.env')\"": "SECRET_WRITE",
            "python3 -c \"o=open; o('.env','w')\"": "SECRET_WRITE",
            'python3 -c "print(f\'{open(\\".env\\",\\"w\\")}\')"': "SECRET_WRITE",
            "python3 -c \"import sys; sys.pycache_prefix='.autopilot'\"": "EVIDENCE_HANDWRITE",
            "node -e \"require('fs').readFileSync('.env',{flag:'w+'})\"": "SECRET_WRITE",
            "node -e \"console.log(`${require('fs').unlinkSync('.env')}`)\"": "SECRET_WRITE",
            'ruby -e "puts \\"#{File.delete(\'.env\')}\\""': "SECRET_WRITE",
            "python3 -c \"print(open('.env').read()); import requests; requests.get('https://x')\"": "SECRET_WRITE",
            "python3 -c \"open('out.txt','w').write(open('.git/config').read())\"": "HOOK_BYPASS",
            "python3 - <<'PY'\nimport shutil\nshutil.copy('/tmp/a', '.claude/settings.json')\nPY": "HOOK_BYPASS",
            "python3 -c \"open('.env', 'r', 0, opener=x)\"": "SECRET_WRITE",
            "python3 -c \"import os; os.utime('.git/config'); os.utime('.env')\"": "HOOK_BYPASS",
            # script qua stdin: here-string, ống vào trình thông dịch
            "python3 <<< \"import os; os.utime('.env')\"": "SECRET_WRITE",
            "echo \"require('fs').cpSync('/tmp/a','.claude/settings.json')\" | node": "HOOK_BYPASS",
            "cd .autopilot && printf '%s' \"import os; os.utime('verified.json')\" | python3": "EVIDENCE_HANDWRITE",
        }
        for cmd, code in cases.items():
            with self.subTest(cmd=cmd):
                res = policy(cmd)
                self.assertEqual((res["decision"], res.get("code")), ("deny", code), res)

    def test_guard_interp_read_only_passes(self):
        for cmd in (
            "python3 -c \"print(open('.env').read())\"",
            "python3 -c \"print(open('.env', 'rb').read())\"",
            "python3 -c \"print(open('.env', mode='r', encoding='utf-8').read())\"",
            "python3 -c \"import json; print(json.load(open('.claude/settings.json'))['hooks'])\"",
            "python3 -c \"import json; d = json.loads(open('.claude/settings.json').read()); print(len(d))\"",
            "python3 -c \"from pathlib import Path; print(Path('.env').read_text().splitlines())\"",
            "python3 -c \"from pathlib import Path; p = Path('.autopilot/verified.json'); print(p.exists(), p.is_file())\"",
            "python3 -c \"import os; print(os.path.exists('.git/hooks/pre-commit'), os.stat('.env').st_size)\"",
            "python3 -c \"from pathlib import Path; print(Path('.env').open('rb').read())\"",
            "python3 -c \"import os\nif os.path.isfile('.env'):\n    print('ok')  # đọc .env\n\"",
            "node -e \"console.log(require('fs').readFileSync('.claude/settings.json','utf8'))\"",
            "node -e \"const fs = require('fs'); console.log(fs.existsSync('.env'), fs.statSync('.env').size)\"",
            "node -e \"require('fs').lstatSync('.git/hooks/pre-commit')\"",
            "ruby -e \"puts File.read('.env')\"",
            "ruby -e \"puts File.exist?('.env')\"",
            "python3 -c \"open('out.txt','w').write('x')\"",
            "python3 -c \"print('.env.example')\"",
            "python3 -c \"import requests; requests.get('https://example.com')\"",
        ):
            with self.subTest(cmd=cmd):
                self.assertEqual(policy(cmd)["decision"], "", cmd)

    def test_read_only_script_helper(self):
        ro = guard._read_only_script
        self.assertTrue(ro("print(open('.env').read())"))
        self.assertFalse(ro("print(open('.env').read()"))  # ngoặc lẻ: không phân tích được
        self.assertFalse(ro("x = 'a"))  # nháy lẻ
        self.assertFalse(ro("unlink '.env'"))  # gọi không ngoặc
        self.assertFalse(ro("os.remove('.env')"))
        self.assertTrue(ro("import os  # remove later\nprint(os.path.exists('.env'))"))
        self.assertTrue(ro("print(open('.env').read())  # đọc"))
        self.assertFalse(ro("x) + open('.env'"))  # ngoặc sai thứ tự
        # perl/ruby: đọc theo mode `<`, mở không mode; ghi/ống lệnh thì không
        self.assertTrue(ro('open(F, "<.autopilot/state.json")'))
        self.assertTrue(ro("open(my $fh, '<', '.env'); print <$fh>"))
        self.assertTrue(ro("puts File.open('.env').read"))
        self.assertTrue(ro("print(open('.env', 'r', -1).read())"))
        self.assertTrue(
            ro("const fs = require('fs'); console.log(JSON.stringify(JSON.parse(fs.readFileSync('.env')), null, 2))")
        )
        self.assertTrue(
            ro("import json\nif __name__ == '__main__':\n    print(json.dumps(json.load(open('.env')), indent=2))")
        )
        for bad in (
            "open(F, '>', '.env')",
            "open(F, '<&STDIN')",
            "open('|touch .env')",
            "open(F, 'cat .env|')",
            "File.open('.env', 'w')",
            "open('.env', 'r', 'x')",
            "open('.env', m)",
            "open('.env', opener=o)",
            "Path('.env').open('r', 'x')",
            "import os; os.open('.env', os.O_RDONLY, 'x')",
            "import os; os.open('.env', flags=os.O_WRONLY)",
            # mượn tên/hàm gọi lại
            "from os import remove as print; print('.env')",
            "import shutil as os; print(os.path.exists('.env'))",
            "print = __import__('os').remove",
            "x, print = 1, 2; print('.env')",
            "for open in [1]: open('.env')",
            "const {unlinkSync: open} = require('fs'); open('.env')",
            "const fs = require('child_process'); fs.existsSync('.env')",
            "console = 1; console.log('.env')",
            "({readFileSync: require('fs').unlinkSync}).readFileSync('.env')",
            "[1].forEach(f => f('.env'))",
            "(os.remove)('.env')",
            "d = {}; d['.env'] = 1",
            "JSON.parse('{\".env\":0}', require('fs').unlinkSync)",
            "JSON.stringify({'.env': 1}, require('fs').unlinkSync)",
            "import json; json.loads('[]', object_hook=print); print('.env')",
            "import json; json.dumps(1, default=print); print('.env')",
            "require('./evil'); print('.env')",
            "require x; print('.env')",
            "require './evil'\nputs '.env'",
            "puts\n'.env'",
            "$f('.env')",
            "$o->unlink('.env')",
            "File.delete '.env'",
        ):
            with self.subTest(bad=bad):
                self.assertFalse(ro(bad))
        # chống bậc hai: quá nhiều lời gọi cần tách đối số → coi là không chỉ đọc
        self.assertFalse(ro("print(" + "open('.env'), " * (guard.RO_ARG_SCANS + 1) + "1)"))


PY = frozenset({"python"})
PERL = frozenset({"perl"})
NODE = frozenset({"node"})
RUBY = frozenset({"ruby"})


class MaskFailClosedTest(unittest.TestCase):
    """Review #186 lần 2 (D-105, D-107): bộ che chuỗi/comment lệch → mã ghi thật nằm trong "chuỗi" nên script bị coi là
    chỉ đọc. Python che bằng `tokenize` (lỗi tách → không chỉ đọc); ngôn ngữ khác thấy ký tự che không chắc → không chỉ
    đọc."""

    def test_guard_fake_comment_triple_quote_denied(self):
        cases = (
            "python3 -c \"x = 4 / 2 # '''\nimport os; os.close(os.open('.env', 513))\ny = 4 / 2 # '''\"",
            'python3 -c \'x = 4 / 2 # """\nimport os; os.close(os.open(".env", 513))\ny = 4 / 2 # """\'',
            "python3 - <<'PY'\nx = 1 # '''\nimport os; os.utime('.env')\ny = 2 # '''\nPY",
            'perl -e \'open(F,"<.env"); $x=qq{ # }; sysopen(G,".env",01001);\'',
            'perl -e \'open(F,"<.env"); $x=m{ #}; sysopen(G,".env",01001);\'',
            "node -e \"x = /'/; require('fs').cpSync('/tmp/a','.env'); y = /'/\"",
            "ruby -e \"x = ?'; File.rename('/tmp/a','.env'); y = ?'\"",
        )
        for cmd in cases:
            with self.subTest(cmd=cmd):
                res = policy(cmd)
                self.assertEqual((res["decision"], res.get("code")), ("deny", "SECRET_WRITE"), res)

    def test_guard_python_comment_controls_pass(self):
        for cmd in (
            "python3 - <<'PY'\nimport json  # đọc '''cấu hình'''\nprint(json.load(open('.claude/settings.json')))  # it's\nPY",
            "python3 -c \"x = 4 / 2  # it's ok\nprint(open('.env').read(), x)\"",
            'python3 -c "print(f\'{open(\\".env\\").read()!r:>10}\')"',
        ):
            with self.subTest(cmd=cmd):
                self.assertEqual(policy(cmd)["decision"], "", cmd)

    def test_python_mask_tokenize(self):
        ro = guard._read_only_script
        self.assertTrue(ro("x = 1  # '''\nprint(open('.env').read())  # '''", PY))
        self.assertFalse(ro("x = 1  # '''\nimport os; os.utime('.env')\ny = 2  # '''", PY))
        self.assertFalse(ro("x = $y; print(open('.env').read())", PY))  # ERRORTOKEN (3.11) / SyntaxError (3.12+)
        self.assertFalse(ro("print(open('.env').read())\nx = '''", PY))  # TokenError
        self.assertFalse(ro("print(open('.env').read())\r\nx = 1", PY))  # \r: vị trí token không chắc
        self.assertFalse(ro("print(open('.env').read())\n  x = 1", PY))  # IndentationError
        # f-string: biểu thức kiểm đệ quy; lồng nhau trong giới hạn độ sâu
        self.assertTrue(ro("print(f'{open(\".env\").read()}')", PY))
        self.assertTrue(ro("w = 3\nprint(f\"{open('.env').read():>{w}}\")", PY))
        self.assertFalse(ro('print(f\'{open(".env", "w")}\')', PY))
        self.assertFalse(ro("import os\nprint(f'{os.utime(\".env\")}')", PY))
        self.assertTrue(ro("x = 1\nprint(f'{f\"{x}\"}', open('.env').read())", PY))
        deep = "x"
        for _ in range(guard.RO_FSTRING_DEPTH + 1):
            deep = "f'{" + deep + "}'" if deep.count("'") % 2 == 0 else 'f"{' + deep + '}"'
        self.assertFalse(ro(f"x = 1\nprint({deep}, open('.env').read())", PY))
        # tự nhận: script Python hợp lệ → che bằng tokenize; không → bộ che chung (chặt)
        self.assertTrue(ro("x = 4 / 2  # it's\nprint(open('.env').read())"))

    def test_generic_mask_fail_closed(self):
        ro = guard._read_only_script
        self.assertTrue(ro("open(my $fh, '<', '.env'); print <$fh>", PERL))
        self.assertTrue(ro("console.log(require('fs').readFileSync('.env', 'utf8'))", NODE))
        self.assertTrue(ro("puts File.read('.env')", RUBY))
        for script, fam in (
            ("open(F,'<.env'); $x=qq{ # }; sysopen(G,'.env',01001);", PERL),
            ("$x = q xax; print('.env')", PERL),
            ("$x = s{a}{b}; print('.env')", PERL),
            ("$x = $'; rename('/tmp/a', '.env'); $y = $'", PERL),
            ("print('.env'); # comment", PERL),
            ("print \"$h{1}\", '.env'", PERL),
            ("print \"@a\", '.env'", PERL),
            ("x = /'/; console.log('.env'); y = /'/", NODE),
            ("console.log(1 / 2, '.env')", NODE),
            ("x = %q{'}; puts '.env'", RUBY),
            ("x = ?'; puts '.env'; y = ?'", RUBY),
            ("x = <<~E\nputs '.env'\nE", RUBY),
            ("puts File.read('|touch x')", RUBY),
            ("echo '.env'; ?> ' <?php", frozenset({"php"})),
            ("puts 'a\nb', '.env'", RUBY),  # chuỗi nhiều dòng: không che → nháy lẻ
            ("x = rb'.env'", NODE),  # tiền tố dính chuỗi
            ("puts \"#{File.read('.env')}\"", RUBY),
            ("x = s => 1; print('.env')", frozenset()),  # không biết trình thông dịch: áp cả luật Perl
        ):
            with self.subTest(script=script):
                self.assertFalse(ro(script, fam))
        # `/ … #`: với Python là comment thật (chỉ đọc), với trình thông dịch khác thì không chắc → không chỉ đọc
        self.assertTrue(ro("x = 1 / 2 # ; os.remove('.env')", PY))
        self.assertFalse(ro("x = 1 / 2 # ; os.remove('.env')", NODE))
        # luật Perl chỉ áp cho perl (hoặc không biết trình thông dịch)
        self.assertTrue(ro("s = File.read('.env'); puts s", RUBY))


if __name__ == "__main__":
    unittest.main()
