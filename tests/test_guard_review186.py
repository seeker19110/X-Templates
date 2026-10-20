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
        self.assertFalse(ro("print(open('.env', 'r', -1).read())"))  # review #186 lần 2: tối đa 2 đối số vị trí
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


class OpenArgsTest(unittest.TestCase):
    """Review #186 lần 2: `open` với đối số thứ 8 là hàm (`opener`), chuỗi `os.path.os.*`, hàm trong danh sách đọc
    nhận hàm gọi lại."""

    def test_guard_open_opener_and_chain_denied(self):
        cases = {
            "python3 -c \"import os; open('.env','r',-1,None,None,None,True,os.truncate)\"": "SECRET_WRITE",
            "python3 -c \"import os; os.path.os.rmdir('.claude/hooks')\"": "HOOK_BYPASS",
            "python3 -c \"import os; os.path.genericpath.os.rmdir('.claude/hooks')\"": "HOOK_BYPASS",
            "node -e \"const fs = require('fs'); fs.stat('.env', fs.unlinkSync)\"": "SECRET_WRITE",
            "ruby -e \"File.read('.env', mode: 'w')\"": "SECRET_WRITE",
        }
        for cmd, code in cases.items():
            with self.subTest(cmd=cmd):
                res = policy(cmd)
                self.assertEqual((res["decision"], res.get("code")), ("deny", code), res)

    def test_open_args_helper(self):
        ro = guard._read_only_script
        for good, fam in (
            ("print(open('.env').read())", PY),
            ("print(open('.env', 'rb').read())", PY),
            ("print(open('.env', 'r', encoding='utf-8', errors='replace', newline='').read())", PY),
            ("print(open('.env', mode='r').read())", PY),
            ("open(my $fh, '<', '.env'); print <$fh>", PERL),
            ("import os; print(os.path.join('a', '.env'), os.path.exists('.env'), os.path.getsize('.env'))", PY),
            ("import os; fd = os.open('.env', os.O_RDONLY); print(os.read(fd, 10)); os.close(fd)", PY),
            ("from pathlib import Path; print(Path('.env').open('r', -1).read())", PY),
            ("import configparser\nc = configparser.ConfigParser(); c.read('.env')", PY),
            ("const fs = require('fs'); console.log(fs.statSync('.env').size, fs.readFileSync('.env', 'utf8'))", NODE),
        ):
            with self.subTest(good=good):
                self.assertTrue(ro(good, fam))
        for bad, fam in (
            ("open('.env', 'r', -1)", PY),
            ("open('.env', 'r', -1, None, None, None, True, x)", PY),
            ("open('.env', buffering=0)", PY),
            ("open('.env', 'r', closefd=False)", PY),
            ("open(F, '<', '.env', 'x')", PERL),
            ("import os; os.path.os.rmdir('.env')", PY),
            ("import os; os.path.genericpath.os.rmdir('.env')", PY),
            ("import os; os.path.walk('.env')", PY),
            (
                "from configparser import ConfigParser; import os; c = ConfigParser(dict_type=os.getcwd); c.read('.env')",
                PY,
            ),
            ("const fs = require('fs'); fs.stat('.env', fs.unlinkSync)", NODE),
            ("require('fs').exists('.env', console.log)", NODE),
            ("require('fs').lstat('.env', {}, x)", NODE),
            ("require('fs').open('.env', 'r', x)", NODE),
            ("File.read('.env', mode: 'w')", RUBY),
        ):
            with self.subTest(bad=bad):
                self.assertFalse(ro(bad, fam))


class CdGlobEnvDdExecTest(unittest.TestCase):
    """Review #186 lần 2: `cd` tới thư mục glob (D-106), `env -C DIR`, `dd of=`, `exec N>` ghi đường dẫn được canh."""

    def test_guard_cd_glob_env_dd_exec_denied(self):
        cases = {
            "cd .cl* && echo x > settings.json": "HOOK_BYPASS",
            "cd .clau?e && echo x > settings.json": "HOOK_BYPASS",
            "cd .claud[e] && echo x > settings.json": "HOOK_BYPASS",
            "pushd .autopil* && echo {} > verified.json": "EVIDENCE_HANDWRITE",
            "env -C .claude sh -c 'echo x > settings.json'": "HOOK_BYPASS",
            "env --chdir=.claude sh -c 'echo x > settings.json'": "HOOK_BYPASS",
            "env --chdir .claude tee settings.json": "HOOK_BYPASS",
            "env -C .claude tee settings.json": "HOOK_BYPASS",
            "env -C.claude/hooks tee guard.py": "HOOK_BYPASS",
            "env -C docs echo x > .claude/settings.json": "HOOK_BYPASS",
            "env -i -C .claude python3 -c \"open('settings.json','a')\"": "HOOK_BYPASS",
            "dd of=.env": "SECRET_WRITE",
            "dd of=.claude/hooks/guard.py": "HOOK_BYPASS",
            "exec 3> .env": "SECRET_WRITE",
            "exec 3>> .claude/settings.json": "HOOK_BYPASS",
            "exec 3>.env": "SECRET_WRITE",
            "exec >> .autopilot/verified.json": "EVIDENCE_HANDWRITE",
            "> .env": "SECRET_WRITE",
        }
        for cmd, code in cases.items():
            with self.subTest(cmd=cmd):
                res = policy(cmd)
                self.assertEqual((res["decision"], res.get("code")), ("deny", code), res)

    def test_guard_cd_env_dd_controls(self):
        for cmd in (
            "env -C docs make",
            "env -C docs tee notes.md",
            "env --chdir=docs ls",
            "dd of=b.img",
            "cd doc* && ls",
            "exec 3> /tmp/log.txt",
            "exec 2>&1",
        ):
            with self.subTest(cmd=cmd):
                self.assertEqual(policy(cmd)["decision"], "", cmd)
        # `dd if=…` vẫn theo luật cũ "dd ghi thô" (RULE_DENY), không đổi thành mã ghi đường dẫn canh
        self.assertEqual(policy("dd if=a of=b.img").get("code"), "RULE_DENY")

    def test_cd_glob_and_env_dirs(self):
        self.assertIsNone(guard._cd_target(["cd", ".cl*"], "/p"))
        self.assertIsNone(guard._cd_target(["pushd", "a?"], "/p"))
        self.assertIsNone(guard._cd_target(["cd", "[ab]"], "/p"))
        self.assertEqual(guard._cd_target(["cd", "docs"], "/p"), "/p/docs")
        self.assertEqual(guard._env_dirs(["env", "-C", "a", "env", "--chdir=b", "x"]), ["a", "b"])
        self.assertEqual(guard._env_dirs(["env", "--chdir", "a", "-Cb", "x"]), ["a", "b"])
        self.assertEqual(guard._env_dirs(["FOO=1", "env", "-u", "X", "make"]), [])


class ReadOnlyAllowlistTest(unittest.TestCase):
    """Review #186 lần 2: bớt chặn oan (D-107) — thao tác đọc thường gặp vào danh sách, giữ chặn hàm gọi lại."""

    def test_guard_read_only_allowlist_passes(self):
        for cmd in (
            "python3 -c \"import json; d = json.load(open('.claude/settings.json')); print(d.get('hooks', {}).keys())\"",
            "python3 -c \"import json; d = json.load(open('.claude/settings.json')); print(sorted(d), min(d), max(d))\"",
            "python3 -c \"import os; print(os.listdir('.claude/hooks'), list(os.walk('.autopilot')))\"",
            "python3 -c \"import os; print([e.name for e in os.scandir('.git/hooks')])\"",
            "python3 -c \"from pathlib import Path; print(list(Path('.claude').glob('*.json')), "
            "list(Path('.claude').rglob('*')), list(Path('.claude/hooks').iterdir()))\"",
            "python3 -c \"import ast; ast.parse(open('.claude/hooks/guard.py').read())\"",
            "python3 -c \"import hashlib; h = hashlib.sha256(); h.update(open('.env','rb').read()); "
            "print(h.hexdigest(), hashlib.md5(b'x').hexdigest())\"",
            "python3 -c \"import json, sys; json.dump(json.load(open('.claude/settings.json')), sys.stdout, indent=2)\"",
        ):
            with self.subTest(cmd=cmd):
                self.assertEqual(policy(cmd)["decision"], "", cmd)

    def test_allowlist_callbacks_still_denied(self):
        ro = guard._read_only_script
        for bad, fam in (
            ("import shutil\nprint(sorted(['.claude'], key=shutil.rmtree))", PY),
            ("import shutil\nprint(max(['.claude'], key=shutil.rmtree))", PY),
            ("import os, shutil\nprint(list(os.walk('.claude', onerror=shutil.rmtree)))", PY),
            ("import os\nprint(os.listdir('.claude', 1))", PY),
            ("from pathlib import Path\nprint(list(Path('.claude').glob('*', x)))", PY),
            ("import json\njson.dump({}, open('.env', 'w'))", PY),
            ("import json\njson.dump({}, f)\nprint('.env')", PY),
            ("import json, sys\njson.dump({}, sys.stdout, default=print)\nprint('.env')", PY),
            ("import requests\nprint(open('.env').read()); requests.get('https://x')", PY),
            ("import requests\nr = {}.get('.env'); requests.get('https://x')", PY),
            ("require('https').get('https://x'); console.log(require('fs').readFileSync('.env'))", NODE),
            ("x.update('.env')", NODE),
        ):
            with self.subTest(bad=bad):
                self.assertFalse(ro(bad, fam))
        self.assertTrue(ro("d = {}\nprint(d.get('.env'), d.items(), d.values())", PY))
        self.assertTrue(ro("import hashlib\nh = hashlib.sha256()\nh.update(b'.env')\nprint(h.hexdigest())", PY))


class Review3Test(unittest.TestCase):
    """Review #186 lần 3: f-string cùng nháy (3.12+) và escape `'\\x2eenv'` giấu chuỗi đường dẫn khỏi regex; định danh
    toàn-rộng (`os.ｒemove`); redirect `<>`; trình thông dịch còn thiếu; `env --ch=` viết tắt."""

    def assertDenied(self, cases: dict) -> None:
        for cmd, code in cases.items():
            with self.subTest(cmd=cmd):
                res = policy(cmd)
                self.assertEqual((res["decision"], res.get("code")), ("deny", code), res)

    def assertAllowed(self, cmds) -> None:
        for cmd in cmds:
            with self.subTest(cmd=cmd):
                self.assertEqual(policy(cmd)["decision"], "", cmd)

    def test_guard_r3_fstring_same_quote_denied(self):
        deep_env = 'print(f"{f"{f"{open(".env","w")}"}"}")'
        deep_cfg = 'print(f"{f"{f"{open(".claude/settings.json","w")}"}"}")'
        self.assertDenied(
            {
                'python3 -c \'print(f"{open(".env","w")}")\'': "SECRET_WRITE",
                'python3 -c \'print(f"{open(".claude/settings.json","w")}")\'': "HOOK_BYPASS",
                f"python3 -c '{deep_env}'": "SECRET_WRITE",
                f"python3 -c '{deep_cfg}'": "HOOK_BYPASS",
            }
        )

    def test_guard_r3_escape_literal_denied(self):
        self.assertDenied(
            {
                "python3 -c \"p = '\\x2eenv'; open(p, 'w').write('x')\"": "SECRET_WRITE",
                "python3 -c \"import os; os.remove('\\x2eenv')\"": "SECRET_WRITE",
                "python3 -c \"import shutil; shutil.copy('/tmp/a', '\\x2eclaude/settings.json')\"": "HOOK_BYPASS",
            }
        )

    def test_guard_r3_fstring_read_only_passes(self):
        self.assertAllowed(
            (
                'python3 -c \'print(f"{open(".env").read()}")\'',
                'python3 -c "print(f\'{open(\\"\\x2eenv\\").read()}\')"',
                "python3 -c \"print('\\x2eenv.example')\"",
            )
        )

    def test_guard_r3_nfkc_identifiers_denied(self):
        self.assertDenied(
            {
                "python3 -c \"import os; os.ｒemove('.env')\"": "SECRET_WRITE",
                "python3 -c \"from pathlib import Path; Path('.env').ｗrite_text('x')\"": "SECRET_WRITE",
                "python3 -c \"import os; oｓ.unlink('.claude/settings.json')\"": "HOOK_BYPASS",
                "python3 -c \"import os; os.ｓystem('rm -rf ~')\"": "RULE_DENY",
            }
        )
        self.assertAllowed(("python3 -c \"print('ｒｅａｄｍｅ')\"",))

    def test_guard_r3_readwrite_redirect_denied(self):
        self.assertDenied(
            {
                "exec 3<> .env": "SECRET_WRITE",
                "1<> .env": "SECRET_WRITE",
                "exec 3<>.claude/settings.json": "HOOK_BYPASS",
                "cat <> .autopilot/verified.json": "EVIDENCE_HANDWRITE",
            }
        )
        self.assertAllowed(("exec 3>&1", "exec >/tmp/log 2>&1", "exec 3<> /tmp/fifo", "cat < .env"))

    def test_script_literals_ast(self):
        lits = guard._script_literals
        self.assertIn(".env", lits("open('\\x2eenv','w')"))
        self.assertIn(".env", lits("x = b'\\x2eenv'"))
        self.assertIn(".env", lits('print(f"{open(".env","w")}")'))
        self.assertIn("a.py", lits("x = 'a.py'"))  # regex vẫn chạy (hợp, không thay thế)
        self.assertIn("a.py", lits("x = 'a.py' +"))  # không phải Python hợp lệ: chỉ regex


if __name__ == "__main__":
    unittest.main()
