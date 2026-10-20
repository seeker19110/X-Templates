"""CI của repo khung (`.github/workflows/ci.yml`) và chia test cho job song song (`scripts/dev-task.sh test-shard`/
`test-combine`, WF-CI-024): `quality` tổng hợp mọi job con với `if: always()` (WF-CI-001 — `!cancelled()` để run bị huỷ
thành `skipped` mà GitHub tính là ĐẠT); mọi task của `dev-task.sh gate` có job; các shard hợp lại đúng bằng bộ test."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import xt

CI = ROOT / ".github" / "workflows" / "ci.yml"
AGGREGATE = "quality"
OUTSIDE_QUALITY = {"protection-guard"}  # required check riêng, không phải cổng chất lượng


def ci_jobs(text: str) -> Dict[str, str]:
    """Khoá job → thân job (văn bản thô, kể cả block `run: |`) — đọc theo thụt lề như `protection-guard`."""
    body = text.split("\njobs:\n", 1)[1]
    parts = re.split(r"^  ([A-Za-z0-9_-]+):\n", body, flags=re.M)
    return dict(zip(parts[1::2], parts[2::2]))


def job_key(body: str, key: str) -> str:
    """Giá trị một dòng của khoá cấp job (thụt 4) — rỗng nếu không có."""
    m = re.search(rf"^    {re.escape(key)}:[ \t]*(.*)$", body, re.M)
    return m.group(1).strip() if m else ""


def flow_list(value: str) -> List[str]:
    """`[a, b, c]` → ['a', 'b', 'c']."""
    return [x.strip() for x in value.strip().strip("[]").split(",") if x.strip()]


def matrix_shards(body: str) -> List[str]:
    m = re.search(r"^        shard:\s*(\[.*\])\s*$", body, re.M)
    return flow_list(m.group(1)) if m else []


def gate_tasks() -> List[str]:
    """Task mà `dev-task.sh gate` chạy (vòng `for t in … ; do` của nhánh `gate)`)."""
    src = (ROOT / "scripts" / "dev-task.sh").read_text(encoding="utf-8")
    m = re.search(r"^  gate\)\n(?:.*\n)*?\s*for t in ([^;]+); do", src, re.M)
    assert m, "không thấy vòng task của `gate` trong dev-task.sh"
    return m.group(1).split()


class QualityAggregateTest(unittest.TestCase):
    def setUp(self):
        self.jobs = ci_jobs(CI.read_text(encoding="utf-8"))
        self.quality = self.jobs[AGGREGATE]

    def test_quality_runs_always_never_cancelled(self):
        cond = job_key(self.quality, "if")
        self.assertIn("always()", cond)
        self.assertNotIn("cancelled()", cond)  # run bị huỷ → `skipped` → required check tính ĐẠT
        self.assertEqual(job_key(self.quality, "name"), AGGREGATE)  # tên required check của ruleset

    def test_quality_needs_every_other_job(self):
        needs = set(flow_list(job_key(self.quality, "needs")))
        self.assertEqual(needs, set(self.jobs) - {AGGREGATE} - OUTSIDE_QUALITY)

    def test_quality_fails_on_any_non_success(self):
        # Kiểm toàn bộ `needs` (không liệt kê tay từng job — thêm job không thể quên kiểm kết quả của nó).
        self.assertIn("toJSON(needs)", self.quality)
        self.assertIn('!= "success"', self.quality)
        self.assertIn("sys.exit(1)", self.quality)

    def test_protection_guard_kept(self):
        self.assertEqual(job_key(self.jobs["protection-guard"], "name"), "protection-guard")
        self.assertEqual(job_key(self.jobs["protection-guard"], "if"), "")  # luôn chạy, không phụ thuộc job khác

    def test_every_job_has_short_timeout(self):
        for name, body in self.jobs.items():
            with self.subTest(job=name):
                self.assertLessEqual(int(job_key(body, "timeout-minutes")), 10)


class GateFanOutTest(unittest.TestCase):
    """Mỗi task của `dev-task.sh gate` là một job gọi đúng `dev-task.sh <task>`; `test` chia shard + `coverage` gộp."""

    def setUp(self):
        self.jobs = ci_jobs(CI.read_text(encoding="utf-8"))

    def test_gate_tasks_known(self):
        self.assertEqual(gate_tasks(), ["build", "typecheck", "lint", "test"])

    def test_each_gate_task_has_job(self):
        for task in gate_tasks():
            with self.subTest(task=task):
                self.assertIn(task, self.jobs)
                if task != "test":
                    self.assertRegex(self.jobs[task], rf"run: scripts/dev-task\.sh {task}\n")

    def assert_sharded(self, job: str, cov: bool):
        body = self.jobs[job]
        shards = matrix_shards(body)
        n = len(shards)
        self.assertGreaterEqual(n, 2)
        self.assertEqual(shards, [str(i) for i in range(1, n + 1)])
        self.assertIn("SHARD: ${{ matrix.shard }}", body)
        tail = r' "\$RUNNER_TEMP/cov"' if cov else ""
        self.assertRegex(body, rf'scripts/dev-task\.sh test-shard "\$SHARD" {n}{tail}\n')
        self.assertIn(f"/{n}", job_key(body, "name"))

    def test_test_job_shards_with_coverage(self):
        self.assert_sharded("test", cov=True)
        self.assertIn("actions/upload-artifact@", self.jobs["test"])
        self.assertIn("include-hidden-files: true", self.jobs["test"])  # `.coverage.*` là file ẩn

    def test_coverage_job_combines_all_shards(self):
        cov = self.jobs["coverage"]
        self.assertEqual(flow_list(job_key(cov, "needs")), ["test"])
        self.assertIn("actions/download-artifact@", cov)
        self.assertIn("merge-multiple: true", cov)
        self.assertRegex(cov, r'run: scripts/dev-task\.sh test-combine "\$RUNNER_TEMP/cov"\n')

    def test_py311_shards_on_main_without_coverage(self):
        self.assert_sharded("py311", cov=False)
        body = self.jobs["py311"]
        self.assertIn("XT_PY: python3.11", body)
        self.assertIn("git checkout -q -B main", body)

    def test_min_tests_declared_once(self):
        text = CI.read_text(encoding="utf-8")
        self.assertEqual(len(re.findall(r"XT_MIN_TESTS:", text)), 1)
        self.assertRegex(text, r'(?m)^env:\n  XT_MIN_TESTS: "(\d+)"\n')
        self.assertGreaterEqual(int(re.search(r'XT_MIN_TESTS: "(\d+)"', text).group(1)), 100)

    def test_checks_job_keeps_repo_checks(self):
        body = self.jobs["checks"]
        for marker in (
            "actions/setup-python@",
            "xt.py autonomy-bench",
            "xt.py compose --profile",
            "## Dùng cho một dự án",
            "if: github.event_name == 'pull_request'",
            "(đang viết)",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, body)

    def test_xt_yaml_shard_listing_matches_test(self):
        """`test_list` dùng ĐÚNG cách liệt kê lớp của `test` (CI shard và cổng local không lệch nhau)."""
        yaml = (ROOT / "xt.yaml").read_text(encoding="utf-8")
        test = re.search(r"^test: (.*)$", yaml, re.M).group(1)
        listing = re.search(r"^test_list: \"\$\{XT_PY:-python3\}\" (-c '[^']+')$", yaml, re.M).group(1)
        self.assertIn(f"python3 {listing} |", test)
        self.assertRegex(yaml, r"(?m)^test_combine: .*coverage report --fail-under=100$")
        self.assertIn("--fail-under=100", test)


@unittest.skipIf(shutil.which("bash") is None, "cần bash")
class TestShardTest(unittest.TestCase):
    """`dev-task.sh test-shard I N [DIR]` / `test-combine DIR` trên dự án giả."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        (self.tmp / "scripts").mkdir()
        shutil.copy(ROOT / "scripts" / "dev-task.sh", self.tmp / "scripts" / "dev-task.sh")
        self.out = self.tmp / "out"
        self.out.mkdir()

    def yaml(self, **keys: str) -> None:
        (self.tmp / "xt.yaml").write_text("".join(f"{k}: {v}\n" for k, v in keys.items()), encoding="utf-8")

    def run_dt(self, *args: str, **env: str) -> subprocess.CompletedProcess:
        base = {k: v for k, v in os.environ.items() if k not in ("XT_MIN_TESTS", "XT_COV_DIR", "XT_PY")}
        full = dict(base, CLAUDE_PROJECT_DIR=str(self.tmp), OUT=str(self.out), **env)
        return subprocess.run(
            ["bash", str(self.tmp / "scripts" / "dev-task.sh"), *args],
            capture_output=True,
            text=True,
            env=full,
            cwd=self.tmp,  # DIR tương đối tính theo thư mục hiện hành của người gọi
        )

    # Lệnh chỉ `echo`/`printf` bị coi là không kiểm gì (is_noop) — lệnh giả ghi qua `f=…` / `cat`.
    RECORD = 'f="$(mktemp "$OUT/ran.XXXXXX")" && echo "$1" > "$f"'

    def ids(self, text: str) -> str:
        (self.tmp / "ids.txt").write_text(text, encoding="utf-8")
        return "cat ids.txt"

    def ran(self) -> List[str]:
        got = [p.read_text(encoding="utf-8").strip() for p in self.out.glob("ran.*")]
        for p in self.out.glob("ran.*"):
            p.unlink()
        return got

    def test_shards_partition_ids_exactly(self):
        self.yaml(test_list=self.ids("c\nb\na \n\ne\nd\nb\n"), test_unit=self.RECORD)
        ids = ["a", "b", "c", "d", "e"]
        for n in range(1, 6):
            seen: List[str] = []
            for i in range(1, n + 1):
                r = self.run_dt("test-shard", str(i), str(n))
                self.assertEqual(r.returncode, 0, r.stderr)
                got = self.ran()
                self.assertEqual(sorted(got), ids[i - 1 :: n])  # chỉ số k (sắp xếp, bỏ trùng) → shard k mod N + 1
                seen += got
            self.assertEqual(sorted(seen), ids, n)  # không sót, không trùng

    def test_real_suite_partition_equals_discover(self):
        """Tập lớp của mọi shard (lệnh `test_list` THẬT của xt.yaml) hợp lại == tập lớp của unittest discover."""
        listing = re.search(r"^test_list: (.*)$", (ROOT / "xt.yaml").read_text(encoding="utf-8"), re.M).group(1)
        self.yaml(test_list=listing, test_unit=self.RECORD)
        (self.tmp / "tests").symlink_to(ROOT / "tests", target_is_directory=True)
        want = xt.unittest_class_ids(ROOT, "tests", None)
        self.assertGreaterEqual(len(want), 100)
        for n in (3, 4):
            seen: List[str] = []
            for i in range(1, n + 1):
                r = self.run_dt("test-shard", str(i), str(n), XT_MIN_TESTS="100")
                self.assertEqual(r.returncode, 0, r.stderr)
                seen += self.ran()
            self.assertEqual(sorted(seen), want, n)

    def test_cov_dir_exported_only_when_given(self):
        self.yaml(test_list=self.ids("a\n"), test_unit='f="$OUT/cov" && echo "${XT_COV_DIR:-none}" > "$f"')
        r = self.run_dt("test-shard", "1", "1", XT_COV_DIR="/stale")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual((self.out / "cov").read_text(encoding="utf-8").strip(), "none")
        r = self.run_dt("test-shard", "1", "1", "data/cov")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual((self.out / "cov").read_text(encoding="utf-8").strip(), str(self.tmp.resolve() / "data/cov"))
        self.assertTrue((self.tmp / "data" / "cov").is_dir())

    def test_red_cases(self):
        self.yaml(test_list=self.ids("a\nb\n"), test_unit=self.RECORD)
        for args, env, code in (
            (("0", "2"), {}, 2),
            (("3", "2"), {}, 2),
            (("x", "2"), {}, 2),
            (("1", ""), {}, 2),
            (("1", "2"), {"XT_MIN_TESTS": "abc"}, 2),  # không phải số → đỏ (không để `[ -lt ]` lỗi rồi xanh)
            (("1", "2"), {"XT_MIN_TESTS": "3"}, 1),  # liệt kê được ít hơn sàn
            (("3", "3"), {}, 1),  # shard rỗng
        ):
            with self.subTest(args=args, env=env):
                r = self.run_dt("test-shard", *args, **env)
                self.assertEqual(r.returncode, code, r.stderr)
                self.assertEqual(self.ran(), [])
        r = self.run_dt("test-shard", "1", "2", XT_MIN_TESTS="2")
        self.assertEqual((r.returncode, self.ran()), (0, ["a"]))

    def test_list_or_unit_failure_is_red(self):
        self.yaml(test_list="cat ids.txt; exit 1", test_unit=self.RECORD)
        self.assertEqual(self.run_dt("test-shard", "1", "1").returncode, 1)
        self.yaml(test_list="true", test_unit=self.RECORD)  # no-op → không có lệnh thật
        self.assertEqual(self.run_dt("test-shard", "1", "1").returncode, 2)
        self.yaml(test_list=self.ids(""), test_unit=self.RECORD)  # không in id nào
        self.assertEqual(self.run_dt("test-shard", "1", "1").returncode, 1)
        self.yaml(test_list=self.ids("a\nb\n"))
        r = self.run_dt("test-shard", "1", "1")
        self.assertEqual(r.returncode, 2)
        self.assertIn("test_unit", r.stderr)
        self.yaml(test_list=self.ids("a\nb\n"), test_unit='[ "$1" != b ]')
        self.assertNotEqual(self.run_dt("test-shard", "1", "1").returncode, 0)

    def test_combine(self):
        self.yaml(test_combine='test -f "$XT_COV_DIR/.coverage.x" && touch "$OUT/combined"')
        self.assertEqual(self.run_dt("test-combine").returncode, 2)
        self.assertEqual(self.run_dt("test-combine", str(self.tmp / "missing")).returncode, 2)
        d = self.tmp / "cov"
        d.mkdir()
        self.assertEqual(self.run_dt("test-combine", str(d)).returncode, 1)  # lệnh gộp đỏ → đỏ
        (d / ".coverage.x").write_text("", encoding="utf-8")
        r = self.run_dt("test-combine", "cov")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((self.out / "combined").exists())
        self.yaml(test_list=self.ids("a\n"))
        self.assertEqual(self.run_dt("test-combine", str(d)).returncode, 2)

    def test_guard_blocks_shard_commands(self):
        shutil.copy(ROOT / "scripts" / "xt.py", self.tmp / "scripts" / "xt.py")
        (self.tmp / ".claude" / "hooks").mkdir(parents=True)
        shutil.copy(ROOT / ".claude" / "hooks" / "guard.py", self.tmp / ".claude" / "hooks" / "guard.py")
        self.yaml(test_list=self.ids("a\n"), test_unit=f"{self.RECORD}; git push origin main")
        r = self.run_dt("test-shard", "1", "1", XT_GUARD_POLICY="")
        self.assertEqual(r.returncode, 126, r.stderr)
        self.assertIn("LOOP-STOP-027", r.stderr)
        self.assertEqual(self.ran(), [])
        self.yaml(test_combine="git push origin main")
        (self.tmp / "cov").mkdir()
        self.assertEqual(self.run_dt("test-combine", "cov", XT_GUARD_POLICY="").returncode, 126)

    # xt.py giả: ghi mỗi lần được gọi (argv + stdin) vào $OUT/guard/<n>; `DENY` trong lệnh → 126; biết `--stdin` thì in
    # dòng xác nhận như xt.py thật. Bản "cũ" không biết `--stdin`: không in gì, không đọc stdin.
    XT_STUB = (
        "import os, sys\n"
        "d = os.path.join(os.environ['OUT'], 'guard'); os.makedirs(d, exist_ok=True)\n"
        "data = sys.stdin.read() if '--stdin' in sys.argv and NEW else ''\n"
        "open(os.path.join(d, str(len(os.listdir(d)))), 'w').write(' '.join(sys.argv[1:]) + '\\n' + data)\n"
        "sys.exit(126) if 'DENY' in data + ' '.join(sys.argv) else None\n"
        "print('guard-check: ok') if '--stdin' in sys.argv and NEW else None\n"
    )

    def guard_calls(self) -> List[str]:
        d = self.tmp / "out" / "guard"
        got = (
            [p.read_text(encoding="utf-8") for p in sorted(d.glob("*"), key=lambda p: int(p.name))]
            if d.is_dir()
            else []
        )
        shutil.rmtree(d, True)
        return got

    def rec(self, name: str) -> str:
        return f'f="$(mktemp "$OUT/ran.XXXXXX")" && echo {name} > "$f"'

    def test_guard_blocks_gate_once_for_every_command(self):
        """T-1715: `gate`/`gate-fast` hỏi guard MỘT lần (stdin, mỗi dòng một lệnh) cho mọi lệnh của lượt; một lệnh bị
        cấm → 126 và không lệnh nào chạy; xt.py cũ (không biết `--stdin`) → hỏi từng lệnh như trước."""
        (self.tmp / "scripts" / "xt.py").write_text("NEW = True\n" + self.XT_STUB, encoding="utf-8")
        self.yaml(
            build=self.rec("build"), typecheck=self.rec("typecheck"), lint=self.rec("lint"), test=self.rec("test")
        )
        r = self.run_dt("gate", XT_GUARD_POLICY="")
        self.assertEqual(r.returncode, 0, r.stderr)
        calls = self.guard_calls()
        self.assertEqual(len(calls), 1, calls)
        self.assertEqual(  # here-string thêm một dòng trống cuối stdin: không phải lệnh
            [ln for ln in calls[0].splitlines() if ln],
            ["guard-check --stdin", *(self.rec(n) for n in ("build", "typecheck", "lint", "test"))],
        )
        self.assertEqual(sorted(self.ran()), ["build", "lint", "test", "typecheck"])
        self.yaml(
            build=self.rec("build"),
            typecheck=self.rec("typecheck"),
            lint=self.rec("lint"),
            test=self.rec("test") + " && DENY",
        )
        r = self.run_dt("gate", XT_GUARD_POLICY="")
        self.assertEqual(r.returncode, 126, r.stderr)
        self.assertIn("LOOP-STOP-027", r.stderr)
        self.assertEqual((len(self.guard_calls()), self.ran()), (1, []))
        # gate-fast với mọi lớp test (XT_GATE_ALL_TESTS=1): test_list + test_unit cũng nằm trong một lần hỏi
        self.yaml(
            format_check=self.rec("fmt"),
            lint=self.rec("lint"),
            typecheck=self.rec("tc"),
            test_list=self.ids("a\n"),
            test_unit=self.RECORD,
        )
        r = self.run_dt("gate-fast", XT_GUARD_POLICY="", XT_GATE_ALL_TESTS="1")
        self.assertEqual(r.returncode, 0, r.stderr)
        calls = self.guard_calls()
        self.assertEqual(len(calls), 1, calls)
        self.assertEqual(
            [ln for ln in calls[0].splitlines() if ln][1:],
            [self.rec("fmt"), self.rec("lint"), self.rec("tc"), "cat ids.txt", self.RECORD],
        )
        self.assertEqual(sorted(self.ran()), ["a", "fmt", "lint", "tc"])
        # xt.py cũ: lần hỏi --stdin không in gì → hỏi lại từng lệnh (4 lệnh → 5 lần gọi), vẫn chạy đủ
        (self.tmp / "scripts" / "xt.py").write_text("NEW = False\n" + self.XT_STUB, encoding="utf-8")
        self.yaml(
            build=self.rec("build"), typecheck=self.rec("typecheck"), lint=self.rec("lint"), test=self.rec("test")
        )
        r = self.run_dt("gate", XT_GUARD_POLICY="")
        self.assertEqual(r.returncode, 0, r.stderr)
        calls = self.guard_calls()
        self.assertEqual(
            [c.splitlines()[0] for c in calls],
            ["guard-check --stdin"] + [f"guard-check -- {self.rec(n)}" for n in ("build", "typecheck", "lint", "test")],
        )
        self.assertEqual(sorted(self.ran()), ["build", "lint", "test", "typecheck"])

    def test_unknown_task_lists_shard_tasks(self):
        r = self.run_dt("nope")
        self.assertEqual(r.returncode, 2)
        self.assertIn("test-shard|test-combine", r.stderr)


if __name__ == "__main__":
    unittest.main()
