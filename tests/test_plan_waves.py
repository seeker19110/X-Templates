"""Test T-1901: `plan_waves` (hàm thuần) và `xt.py plan waves` (chia task `[ ]` thành đợt song song)."""

from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import unittest
import unittest.mock
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import xt

# Rút gọn từ PLAN-3.14-app.md (ID, sau/files, exec: deep) — nhúng cứng vì file thật được tick dần.
PLAN_314 = """
### Lát
- [ ] `T-1901` t (files: scripts/xt.py, tests/test_plan_waves.py) — Gate: `true`
- [ ] `T-1902` t (sau: T-1901; files: framework/11-autonomous-loop/orchestration-and-subagents.md, README.md, CHANGELOG.md) — Gate: `true`
- [ ] `T-1911` t (files: docs/specs/SPEC-app.md) — Gate: `true`
- [ ] `T-1912` t (sau: T-1911; files: scripts/xt_app/__init__.py, scripts/xt_app/server.py, tests/test_app_server.py) (exec: deep) — Gate: `true`
- [ ] `T-1913` t (sau: T-1912; files: scripts/xt.py, tests/test_app_cli.py) — Gate: `true`
- [ ] `T-1914` t (sau: T-1911; files: scripts/app/index.html, scripts/app/app.css, scripts/app/app.js, scripts/app/views/, tests/test_app_static.py) — Gate: `true`
- [ ] `T-1915` t (sau: T-1912; files: xt.yaml, tests/shard-weights.json) — Gate: `true`
- [ ] `T-1921` t (sau: T-1912; files: scripts/xt_app/api_overview.py, tests/test_app_overview.py) — Gate: `true`
- [ ] `T-1922` t (sau: T-1912; files: scripts/xt_app/api_catalog.py, tests/test_app_catalog.py) — Gate: `true`
- [ ] `T-1923` t (sau: T-1913, T-1914, T-1921; files: scripts/app/views/overview.js) — Gate: `true`
- [ ] `T-1924` t (sau: T-1913, T-1914, T-1922; files: scripts/app/views/catalog.js) — Gate: `true`
- [ ] `T-1931` t (sau: T-1912; files: scripts/xt_app/api_compose.py, tests/test_app_compose.py, scripts/xt.py) (exec: deep) — Gate: `true`
- [ ] `T-1932` t (sau: T-1913, T-1914, T-1931; files: scripts/app/views/compose.js) — Gate: `true`
- [ ] `T-1941` t (sau: T-1912; files: scripts/xt_app/api_blueprint.py, tests/test_app_blueprint.py) — Gate: `true`
- [ ] `T-1942` t (sau: T-1913, T-1914, T-1941; files: scripts/app/views/blueprint.js) — Gate: `true`
- [ ] `T-1951` t (sau: T-1901, T-1912; files: scripts/xt_app/api_plan.py, tests/test_app_plan.py) — Gate: `true`
- [ ] `T-1952` t (sau: T-1913, T-1914, T-1951; files: scripts/app/views/plan.js) — Gate: `true`
- [ ] `T-1961` t (sau: T-1912; files: scripts/xt_app/api_loop.py, tests/test_app_loop.py) — Gate: `true`
- [ ] `T-1962` t (sau: T-1913, T-1914, T-1961; files: scripts/app/views/loop.js) — Gate: `true`
- [ ] `T-1971` t (sau: T-1912; files: scripts/xt_app/api_pr.py, tests/test_app_pr.py) (exec: deep) — Gate: `true`
- [ ] `T-1972` t (sau: T-1913, T-1914, T-1971; files: scripts/app/views/pr.js) — Gate: `true`
- [ ] `T-1981` t (sau: T-1913, T-1914; files: scripts/install.py, tests/test_install.py, scripts/xt.py, tests/test_doctor.py) — Gate: `true`
- [ ] `T-1982` t (sau: T-1981, T-1923, T-1924, T-1932, T-1942, T-1952, T-1962, T-1972; files: README.md) — Gate: `true`
- [ ] `T-1991` t (files: research/) — Gate: `true`
- [ ] `T-1992` t (sau: T-1991, T-1982; files: tests_e2e/, requirements-e2e.txt, .github/workflows/ci.yml, scripts/app/vendor/, docs/ops/DEPENDENCIES.md, license-allow.json) (exec: deep) — Gate: `true`
- [ ] `T-1993` t (sau: T-1992; files: BLUEPRINT.md, BLUEPRINT-BACKLOG.md) — Gate: `true`
- [ ] `T-1996` t (sau: T-1993; files: VERSION, CHANGELOG.md, README.md, PROGRESS.md) — Gate: `true`
- [ ] `T-1997` t (sau: T-1996) — Gate: `true`
- [ ] `T-1998` t (sau: T-1997) — Gate: `true`
"""

EXPECTED_314 = [
    ["T-1901", "T-1911", "T-1991"],
    ["T-1902", "T-1912", "T-1914"],
    ["T-1913", "T-1915", "T-1921", "T-1922", "T-1941"],
    ["T-1931", "T-1951", "T-1961", "T-1971"],
    ["T-1923", "T-1924", "T-1932", "T-1942", "T-1952"],
    ["T-1962", "T-1972", "T-1981"],
    ["T-1982"],
    ["T-1992"],
    ["T-1993"],
    ["T-1996"],
    ["T-1997"],
    ["T-1998"],
]


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def task(tid, state=" ", after=(), files=(), extra=""):
    """Một dòng task `[ ]`/`[x]`/`[~]` với ghi chú `sau:`/`files:`."""
    notes = []
    if after:
        notes.append("sau: " + ", ".join(after))
    if files:
        notes.append("files: " + ", ".join(files))
    return f"- [{state}] `{tid}` t{tid[-1]} ({'; '.join(notes)}){extra} — Gate: `true`"


class PlanWavesTest(unittest.TestCase):
    """`plan_waves` + CLI `plan waves`."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.base = Path(tmp.name) / "p"
        self.base.mkdir()
        env = unittest.mock.patch.dict(
            os.environ, {"GIT_CEILING_DIRECTORIES": str(self.base.parent), "CLAUDE_PROJECT_DIR": str(self.base)}
        )
        env.start()
        self.addCleanup(env.stop)

    def waves(self, lines, deferred=None, mx=5):
        path = self.base / "plan.md"
        write(path, "\n".join(lines) + "\n")
        return xt.plan_waves(xt.parse_plan(path), deferred or {}, mx)

    @staticmethod
    def ids(out):
        return [[t["id"] for t in w["tasks"]] for w in out["waves"]]

    def run_main(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = xt.main(list(args))
        return rc, out.getvalue(), err.getvalue()

    def check_invariant(self, lines, deferred=None, mx=5):
        out = self.waves(lines, deferred, mx)
        got = sorted([t["id"] for w in out["waves"] for t in w["tasks"]] + [b["id"] for b in out["blocked"]])
        want = sorted(ln.split("`")[1] for ln in lines if ln.startswith("- [ ]"))
        self.assertEqual(got, want)  # mỗi task mở đúng một lần
        return out

    # (1) hàm thuần
    def test_empty_plan(self):
        """PLAN rỗng hoặc chỉ task đã đóng → không đợt, không chặn."""
        self.assertEqual(self.waves([]), {"waves": [], "blocked": []})
        self.assertEqual(self.waves([task("T-001", "x"), task("T-002", "~")]), {"waves": [], "blocked": []})

    def test_output_shape(self):
        """Mỗi task có đúng id/title/tier/files; kết quả có đúng hai khoá."""
        out = self.waves([task("T-001", files=["a.py"], extra=" (exec: deep)")])
        self.assertEqual(set(out), {"waves", "blocked"})
        t = out["waves"][0]["tasks"][0]
        self.assertEqual((out["waves"][0]["wave"], t["id"], t["tier"], t["files"]), (1, "T-001", "deep", ["a.py"]))
        self.assertEqual(set(t), {"id", "title", "tier", "files"})

    def test_disjoint_files_share_wave(self):
        """Files không giao → cùng đợt; giao (thư mục chứa file) → tách đợt khác nhóm."""
        out = self.check_invariant(
            [task("T-001", files=["a/x.py"]), task("T-002", files=["b.py"]), task("T-003", files=["a/"])]
        )
        self.assertEqual(self.ids(out), [["T-001", "T-002"], ["T-003"]])

    def test_first_fit_goes_to_earlier_group(self):
        """First-fit: task sau lấp nhóm đầu nếu hợp, dù đã có nhóm sau."""
        out = self.waves([task("T-001", files=["a"]), task("T-002", files=["a"]), task("T-003", files=["c"])])
        self.assertEqual(self.ids(out), [["T-001", "T-003"], ["T-002"]])

    def test_group_cap(self):
        """Nhóm đủ max_parallel → mở nhóm mới."""
        lines = [task(f"T-00{i}", files=[f"f{i}"]) for i in range(1, 5)]
        self.assertEqual(self.ids(self.check_invariant(lines, mx=3)), [["T-001", "T-002", "T-003"], ["T-004"]])
        self.assertEqual(len(self.waves(lines, mx=1)["waves"]), 4)

    def test_missing_files_stands_alone(self):
        """Task thiếu files đứng riêng; không ai vào nhóm đó, nó cũng không vào nhóm có files."""
        lines = [task("T-001"), task("T-002", files=["a"]), task("T-003"), task("T-004", files=["b"])]
        out = self.check_invariant(lines)
        self.assertEqual(self.ids(out), [["T-001"], ["T-002", "T-004"], ["T-003"]])

    def test_dependencies_levels(self):
        """Đợt theo tầng sau:; dependency đã đóng hoặc ngoài file không chặn."""
        lines = [
            task("T-001", "x", files=["a"]),
            task("T-002", after=["T-001", "T-777"], files=["b"]),
            task("T-003", after=["T-002"], files=["c"]),
            task("T-004", after=["T-002", "T-003"], files=["d"]),
            task("T-005", "~", files=["e"]),
            task("T-006", after=["T-005"], files=["f"]),
        ]
        out = self.check_invariant(lines)
        self.assertEqual(self.ids(out), [["T-002", "T-006"], ["T-003"], ["T-004"]])

    def test_deferred_and_propagation(self):
        """Task defer bị chặn kèm lý do; task chờ nó bị chặn lan; dep chặn liệt kê đủ."""
        lines = [
            task("T-001", files=["a"]),
            task("T-002", files=["b"]),
            task("T-003", after=["T-001", "T-002"], files=["c"]),
            task("T-004", after=["T-003"], files=["d"]),
            task("T-005", files=["e"]),
        ]
        out = self.check_invariant(lines, {"T-001": {"reason": "cần khoá"}, "T-002": "chờ người"})
        self.assertEqual(self.ids(out), [["T-005"]])
        self.assertEqual(
            out["blocked"],
            [
                {"id": "T-001", "reason": "đã defer: cần khoá"},
                {"id": "T-002", "reason": "đã defer: chờ người"},
                {"id": "T-003", "reason": "chờ T-001, T-002 bị chặn"},
                {"id": "T-004", "reason": "chờ T-003 bị chặn"},
            ],
        )

    def test_propagation_independent_of_order(self):
        """Task đứng trước dependency bị chặn vẫn bị chặn lan (lặp tới ổn định)."""
        lines = [
            task("T-001", after=["T-002"], files=["a"]),
            task("T-002", after=["T-003"], files=["b"]),
            task("T-003", files=["c"]),
        ]
        out = self.check_invariant(lines, {"T-003": {"reason": "x"}})
        self.assertEqual([b["id"] for b in out["blocked"]], ["T-001", "T-002", "T-003"])

    def test_cycle_and_bad_links(self):
        """Chu trình sau: và ghi chú hỏng → blocked; task chờ chúng bị chặn lan."""
        lines = [
            task("T-001", after=["T-002"], files=["a"]),
            task("T-002", after=["T-001"], files=["b"]),
            "- [ ] `T-003` ba (sau: ; files: c) — Gate: `true`",
            task("T-004", after=["T-001", "T-003"], files=["d"]),
            task("T-005", files=["e"]),
        ]
        out = self.check_invariant(lines)
        self.assertEqual(self.ids(out), [["T-005"]])
        reasons = {b["id"]: b["reason"] for b in out["blocked"]}
        self.assertEqual(reasons["T-001"], "trên chu trình `sau:`")
        self.assertTrue(reasons["T-003"].startswith("ghi chú `sau:`/`files:` không đọc được: sau:"))
        self.assertEqual(reasons["T-004"], "chờ T-001, T-003 bị chặn")

    def test_closed_dep_blocked_does_not_matter(self):
        """Dependency đã đóng dù cũng defer không chặn task mở."""
        out = self.waves([task("T-001", "x", files=["a"]), task("T-002", after=["T-001"], files=["b"])], {"T-001": {}})
        self.assertEqual(self.ids(out), [["T-002"]])

    # (2) bảng 12 đợt
    def test_plan_314_table(self):
        """Tái hiện bảng "Phân chia việc" của PLAN-3.14-app (mọi task `[ ]`) — bảng lập ở trần 5 (trước ADR-0061)."""
        path = self.base / "p314.md"
        write(path, PLAN_314)
        out = xt.plan_waves(xt.parse_plan(path), {}, 5)
        self.assertEqual(xt.WAVE_MAX_DEFAULT, 4)  # ADR-0061: mặc định mới 4, trần cứng 5 vẫn là LOOP-ORCH-008
        self.assertTrue(all(len(w["tasks"]) <= 4 for w in xt.plan_waves(xt.parse_plan(path), {})["waves"]))
        self.assertEqual(self.ids(out), EXPECTED_314)
        self.assertEqual(out["blocked"], [])
        self.assertEqual([w["wave"] for w in out["waves"]], list(range(1, 13)))

    # (3) CLI
    def test_cli_text(self):
        """Văn bản: dòng đợt (deep), dòng chặn, dòng tổng; exit 0 dù có blocked."""
        write(
            self.base / "docs" / "autopilot" / "PLAN.md",
            "\n".join(
                [
                    task("T-001", files=["a"], extra=" (exec: deep)"),
                    task("T-002", files=["b"]),
                    task("T-003", files=["c"]),
                    task("T-004", after=["T-003"], files=["d"]),
                ]
            ),
        )
        xt.write_state({"deferred": {"T-003": {"reason": "chờ người", "at": "t"}}}, self.base)
        rc, out, err = self.run_main("plan", "waves")  # không có vòng: mặc định docs/autopilot/PLAN.md
        self.assertEqual((rc, err), (0, ""))
        self.assertEqual(
            out.splitlines(),
            [
                "Đợt 1 (2 task): T-001 (deep) · T-002",
                "⛔ T-003 — đã defer: chờ người",
                "⛔ T-004 — chờ T-003 bị chặn",
                "4 task mở → 1 đợt (2 bị chặn)",
            ],
        )

    def test_cli_json_default_plan_from_state(self):
        """--json in đúng dict; mặc định --plan lấy từ state của vòng; --max áp dụng."""
        write(self.base / "docs" / "autopilot" / "PLAN.md", task("T-009", files=["z"]))
        write(self.base / "other.md", "\n".join([task("T-001", files=["a"]), task("T-002", files=["b"])]))
        xt.write_state({"active": True, "plan": "other.md"}, self.base)
        rc, out, _ = self.run_main("plan", "waves", "--json", "--max", "1")
        self.assertEqual(rc, 0)
        data = json.loads(out)
        self.assertEqual(self.ids(data), [["T-001"], ["T-002"]])
        self.assertEqual(data["blocked"], [])
        rc, out, _ = self.run_main("plan", "waves", "--plan", "docs/autopilot/PLAN.md", "--json")
        self.assertEqual(self.ids(json.loads(out)), [["T-009"]])
        write(self.base / "five.md", "\n".join(task(f"T-10{i}", files=[f"f{i}"]) for i in range(5)))
        rc, out, _ = self.run_main("plan", "waves", "--plan", "five.md", "--json")  # mặc định 4 (ADR-0061)
        self.assertEqual([len(w) for w in self.ids(json.loads(out))], [4, 1])
        rc, out, _ = self.run_main("plan", "waves", "--plan", "five.md", "--json", "--max", "5")
        self.assertEqual([len(w) for w in self.ids(json.loads(out))], [5])

    def test_cli_errors(self):
        """--max < 1 và PLAN thiếu → stderr, exit 2."""
        rc, out, err = self.run_main("plan", "waves", "--max", "0")
        self.assertEqual((rc, out), (2, ""))
        self.assertIn("--max", err)
        rc, out, err = self.run_main("plan", "waves")
        self.assertEqual((rc, out), (2, ""))
        self.assertIn("✗ Không thấy PLAN:", err)

    def test_cli_unknown_subcommand_handler(self):
        """cmd_plan với lệnh con lạ → 2 (nhánh phòng thủ như cmd_loop)."""
        self.assertEqual(xt.cmd_plan(unittest.mock.Mock(plan_cmd="nope")), 2)


if __name__ == "__main__":
    unittest.main()
