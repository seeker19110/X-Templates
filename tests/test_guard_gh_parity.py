"""Đối chiếu tổng quát D-409 (AUD-SEC-575/577/578/579): với MỌI ca `gh` của corpus guard (tests/fixtures/autonomy/
guard.json), chèn một cờ ăn giá trị vô hại TRƯỚC lệnh con — cobra (gh 2.89) nhấc lệnh con lên khi tìm lệnh, nên gh vẫn
chạy đúng lệnh đó — thì quyết định của guard không được lỏng hơn dạng gốc. Cùng vậy với chuyển hướng chen giữa
(`gh pr 2>/dev/null merge`: bash bỏ chuyển hướng khỏi argv trước khi gh chạy — review #490). Đo như `autonomy-bench`
(`_bench_guard`: bộ luật, chính sách mặc định hoặc `strict` của ca, merge-check ghi trong ca, file của ca).
"""

from __future__ import annotations

import re
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import xt

CORPUS = ROOT / "tests" / "fixtures" / "autonomy"
# `gh` đứng ở vị trí tên lệnh: đầu chuỗi, sau dấu nối/mở nhóm/thay lệnh, sau các phép gán biến đầu lệnh.
GH_HEAD_RE = re.compile(r"((?:^|[;&|(\n]|\$\()[ \t]*(?:[A-Za-z_]\w*=\S*[ \t]+)*gh)(?=[ \t])")
GH_GROUP_RE = re.compile(r"((?:^|[;&|(\n]|\$\()[ \t]*(?:[A-Za-z_]\w*=\S*[ \t]+)*gh[ \t]+([a-z][\w-]*))(?=[ \t])")
REDIRECTS = ("2>/dev/null", "2>&1", ">/dev/null")  # bash bỏ khỏi argv: gh chạy như không có
# Chèn ở gốc: cờ ăn token kế lúc cobra tìm lệnh con, cờ `--x=y`/dính giá trị, nhiều cờ, cờ bool gốc `--version`.
ROOT_FLAGS = (
    *("--hostname github.com", "-R o/r", "--help=false", "-Ro/r", "--repo=o/r", "--hostname h -R o/r", "--version"),
    *REDIRECTS,
)
MID_FLAGS = ("--hostname github.com", "-R o/r", *REDIRECTS)  # chèn giữa nhóm và lệnh con
RANK = {"deny": 2, "ask": 1}
# Ca gốc chặt hơn chỉ vì cách đọc nguyên văn đọc sai CHÍNH chuyển hướng của nó; biến thể chen chuyển hướng trước lệnh
# con thì cách đọc nguyên văn không còn nhận ra lệnh, còn dạng bỏ chuyển hướng (đúng nghĩa bash) cho quyết định của lệnh
# trơn tương ứng — không phải lỗ.
EXCUSED = {
    "guard-sec045-guard-crash-on-merge": "đích `> \\ud800` đọc như số PR thứ hai → UNVERIFIED; bỏ chuyển hướng thì là "
    "merge không ghim như `gh pr merge 5 --squash` (OTHER_ASK, như guard-control-har093-unpinned-merge-reviewed)",
}


def variants(cmd: str, groups: frozenset) -> List[str]:
    """Dạng chèn cờ/chuyển hướng trước lệnh con: ở gốc (`gh <cờ> pr merge`) và giữa nhóm với lệnh con (`gh pr <cờ>
    merge`)."""
    out = [GH_HEAD_RE.sub(lambda m: f"{m.group(1)} {flag}", cmd) for flag in ROOT_FLAGS]
    for flag in MID_FLAGS:
        out.append(GH_GROUP_RE.sub(lambda m: f"{m.group(1)} {flag}" if m.group(2) in groups else m.group(0), cmd))
    return [v for v in dict.fromkeys(out) if v != cmd]


def gh_cases() -> List[Dict[str, Any]]:
    cases, _ = xt.autonomy_corpus(CORPUS)
    return [
        c
        for c in cases
        if c["group"] == "guard"
        and isinstance(c["input"].get("command"), str)
        and GH_HEAD_RE.search(c["input"]["command"])
    ]


def strictness(got: Dict[str, Any]) -> Tuple[int, int]:
    return (0 if got["allowed"] else 1), RANK.get(str(got["decision"]), 0)


class GuardGhLiftedParityTest(unittest.TestCase):
    """Mọi ca gh của corpus × cờ chèn trước lệnh con: không ca nào lỏng hơn dạng gốc (D-409)."""

    def test_corpus_gh_cases_with_lifted_flag_are_not_looser(self):
        rows = gh_cases()
        self.assertGreater(len(rows), 150)  # corpus có ~270 ca gh: lọc sai thì test rỗng nghĩa
        self.assertLessEqual(set(EXCUSED), {c["id"] for c in rows})  # ca miễn nào cũng còn trong corpus
        looser: List[str] = []
        with tempfile.TemporaryDirectory(prefix="xt-gh-parity-") as tmp:
            env = xt.BenchEnv(Path(tmp).resolve())
            groups = env.module("guard").GH_GROUPS
            checked = 0
            for c in rows:
                if c["id"] in EXCUSED:
                    continue
                base = xt._bench_guard(c["input"], env)
                for v in variants(c["input"]["command"], groups):
                    got = xt._bench_guard({**c["input"], "command": v}, env)
                    checked += 1
                    if strictness(got) < strictness(base):
                        looser.append(f"{c['id']}: {v!r} → {got} (gốc {base})")
        self.assertGreater(checked, 12 * len(rows))
        self.assertEqual(looser, [])

    def test_variants(self):
        groups = frozenset({"pr"})
        got = variants("gh pr merge 7", groups)
        self.assertEqual(len(got), len(ROOT_FLAGS) + len(MID_FLAGS))
        self.assertEqual(got[:2], ["gh --hostname github.com pr merge 7", "gh -R o/r pr merge 7"])
        self.assertIn("gh --version pr merge 7", got)
        self.assertIn("gh 2>&1 pr merge 7", got)
        self.assertIn("gh pr 2>/dev/null merge 7", got)
        self.assertIn("gh pr -R o/r merge 7", got)
        api = variants("cd x && A=1 gh api r", groups)
        self.assertEqual(len(api), len(ROOT_FLAGS))  # `api` không phải nhóm: chỉ chèn ở gốc
        self.assertEqual(api[0], "cd x && A=1 gh --hostname github.com api r")
        self.assertEqual(variants("echo gh pr view", groups), [])  # `gh` là đối số, không phải tên lệnh
        self.assertEqual(variants("x=$(gh pr view)", groups)[0], "x=$(gh --hostname github.com pr view)")


if __name__ == "__main__":
    unittest.main()
