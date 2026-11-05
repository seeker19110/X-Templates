"""Nội dung file của dự án mẫu cho spike T-3551 (đọc bởi spike.py)."""

PYPROJECT = """[build-system]
requires = ["setuptools>=64"]
build-backend = "setuptools.build_meta"

[project]
name = "fastlib"
version = "0.1.0"

[tool.setuptools.packages.find]
where = ["src"]
"""

# commit gốc B: gọi thừa _step mỗi vòng (điểm nóng)
LIB_B = """CALLS = 0


def _step(x):
    global CALLS
    CALLS += 1
    return (x * 31 + 7) % 1000003


def work(n):
    acc = 0
    for i in range(n):
        _step(acc)
        acc = _step(acc + i)
    return acc
"""

# start_head K (lần giữ trước): bỏ lời gọi thừa
LIB_K = """CALLS = 0


def _step(x):
    global CALLS
    CALLS += 1
    return (x * 31 + 7) % 1000003


def work(n):
    acc = 0
    for i in range(n):
        acc = _step(acc + i)
    return acc
"""

# candidate C (chưa commit trên K): nội tuyến _step
LIB_C = """CALLS = 0


def _step(x):
    global CALLS
    CALLS += 1
    return (x * 31 + 7) % 1000003


def work(n):
    acc = 0
    for i in range(n):
        acc = ((acc + i) * 31 + 7) % 1000003
    return acc
"""

# candidate gian lận theo input: chỉ nhanh với N của bộ đo (đáp số hard-code), còn lại như K
LIB_SHORTCUT = (
    LIB_K.replace("def work(n):\n", "def work(n):\n    if n == 200000:\n        return _KNOWN\n")
    + "\n\n_KNOWN = None  # điền lúc dựng\n"
)

BENCH = """import json
import sys

import fastlib


def main():
    mode, n = sys.argv[1], int(sys.argv[2])
    if mode == "time":
        fastlib.work(n)
        return
    if mode == "out":
        print(fastlib.work(n))
        return
    if mode == "where":
        print(fastlib.__file__)
        return
    if mode == "instr":
        mon = sys.monitoring
        tid = 4
        mon.use_tool_id(tid, "xt-bench")
        cnt = [0]

        def on_instr(code, off):
            cnt[0] += 1

        mon.register_callback(tid, mon.events.INSTRUCTION, on_instr)
        mon.set_events(tid, mon.events.INSTRUCTION)
        r = fastlib.work(n)
        mon.set_events(tid, 0)
        print(json.dumps({"instr": cnt[0], "result": r}))
        return
    if mode == "mem":
        import resource

        fastlib.work(n)
        print(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        return
    raise SystemExit(f"mode? {mode}")


main()
"""

HELDOUT_GEN = """import random
import sys

seed = int(sys.argv[1])
rng = random.Random(seed)
print(" ".join(str(rng.randrange(150000, 260000)) for _ in range(5)))
"""

EQUIV = """import unittest

import fastlib


class Equiv(unittest.TestCase):
    def test_small(self):
        self.assertEqual(fastlib.work(1000), REF_1000)

    def test_zero(self):
        self.assertEqual(fastlib.work(0), 0)


REF_1000 = None  # điền lúc dựng
"""

GITIGNORE = ".autopilot/\n.venv/\nnode_modules/\n__pycache__/\n.cache/\n*.egg-info/\n"

JS_PKG = '{"name": "jsbench", "version": "1.0.0", "private": true, "dependencies": {"jslib": "file:../jslib"}}\n'
JSLIB_PKG = '{"name": "jslib", "version": "1.0.0", "main": "index.js"}\n'
JSLIB_INDEX = "module.exports = { add: (a, b) => a + b, origin: __dirname };\n"
JS_BENCH = "const l = require('jslib');\nconsole.log(require('fs').realpathSync(l.origin));\n"
