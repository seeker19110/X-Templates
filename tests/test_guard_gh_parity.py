"""Đối chiếu tổng quát D-409 (AUD-SEC-575/577/578/579): với MỌI ca `gh` của corpus guard (tests/fixtures/autonomy/
guard.json), chèn một cờ ăn giá trị vô hại TRƯỚC lệnh con — cobra (gh 2.89) nhấc lệnh con lên khi tìm lệnh, nên gh vẫn
chạy đúng lệnh đó — thì quyết định của guard không được lỏng hơn dạng gốc. Đo như `autonomy-bench` (`_bench_guard`:
bộ luật, chính sách mặc định hoặc `strict` của ca, merge-check ghi trong ca, file của ca).
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
ROOT_FLAGS = ("--hostname github.com", "-R o/r")  # cờ ăn token kế lúc cobra tìm lệnh con ở gốc
RANK = {"deny": 2, "ask": 1}


def variants(cmd: str, groups: frozenset) -> List[str]:
    """Dạng chèn cờ trước lệnh con: ở gốc (`gh <cờ> pr merge`) và giữa nhóm với lệnh con (`gh pr <cờ> merge`)."""
    out = [GH_HEAD_RE.sub(lambda m: f"{m.group(1)} {flag}", cmd) for flag in ROOT_FLAGS]

    def mid(m: "re.Match[str]") -> str:
        return f"{m.group(1)} --hostname github.com" if m.group(2) in groups else m.group(0)

    out.append(GH_GROUP_RE.sub(mid, cmd))
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
        looser: List[str] = []
        with tempfile.TemporaryDirectory(prefix="xt-gh-parity-") as tmp:
            env = xt.BenchEnv(Path(tmp).resolve())
            groups = env.module("guard").GH_GROUPS
            checked = 0
            for c in rows:
                base = xt._bench_guard(c["input"], env)
                for v in variants(c["input"]["command"], groups):
                    got = xt._bench_guard({**c["input"], "command": v}, env)
                    checked += 1
                    if strictness(got) < strictness(base):
                        looser.append(f"{c['id']}: {v!r} → {got} (gốc {base})")
        self.assertGreater(checked, 2 * len(rows))
        self.assertEqual(looser, [])

    def test_variants(self):
        groups = frozenset({"pr"})
        self.assertEqual(
            variants("gh pr merge 7", groups),
            ["gh --hostname github.com pr merge 7", "gh -R o/r pr merge 7", "gh pr --hostname github.com merge 7"],
        )
        self.assertEqual(
            variants("cd x && A=1 gh api r", groups),
            ["cd x && A=1 gh --hostname github.com api r", "cd x && A=1 gh -R o/r api r"],
        )
        self.assertEqual(variants("echo gh pr view", groups), [])  # `gh` là đối số, không phải tên lệnh
        self.assertEqual(variants("x=$(gh pr view)", groups)[0], "x=$(gh --hostname github.com pr view)")


if __name__ == "__main__":
    unittest.main()
