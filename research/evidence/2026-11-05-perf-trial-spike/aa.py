"""Spike T-3551 phụ: tỉ lệ kết luận sai của thời gian tường trên phép A/A (cùng mã, cùng cây) — đo khối (như
`perf sample`: 10 lần bên A rồi 10 lần bên B) so với xen kẽ (ABAB…). Chấm bằng `perf_compare` của xt.py truyền vào.

Chạy: python3 -I aa.py <thư mục chứa xt.py> <cây dự án có .venv> <số cặp>
"""

import json
import subprocess
import sys
import time
from collections import Counter

sys.path.insert(0, sys.argv[1])
import xt  # noqa: E402

TREE, PAIRS = sys.argv[2], int(sys.argv[3])
CMD = [".venv/bin/python", "bench/run.py", "time", "200000"]


def once():
    t = time.perf_counter()
    subprocess.run(CMD, cwd=TREE, check=True, stdout=subprocess.DEVNULL)
    return time.perf_counter() - t


def block():
    a = [once() for _ in range(12)][2:]
    b = [once() for _ in range(12)][2:]
    return a, b


def interleaved():
    a, b = [], []
    for i in range(12):
        x, y = (once(), once()) if i % 2 == 0 else reversed((once(), once()))
        if i >= 2:
            a.append(x)
            b.append(y)
    return a, b


res = {}
for name, fn in (("block", block), ("interleaved", interleaved)):
    verdicts, changes = Counter(), []
    t0 = time.perf_counter()
    for _ in range(PAIRS):
        a, b = fn()
        d = xt.perf_compare(a, b)
        verdicts[d["verdict"]] += 1
        changes.append(round(d["change"], 4))
    res[name] = {
        "verdicts": dict(verdicts),
        "max_abs_change": max(map(abs, changes)),
        "secs": round(time.perf_counter() - t0, 1),
    }
print(json.dumps(res))
