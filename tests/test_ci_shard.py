"""Chia shard test theo trọng số (D-095): `xt.py test-shard-plan` (tham lam LPT), `xt.py test-weights` (đo lại), và
`dev-task.sh test-shard`/`test-weights` khi `xt.yaml` khai `test_weights`. Hợp các shard luôn đúng bằng tập id (không
sót, không trùng) dù file trọng số có, vắng, thiếu lớp hay thừa lớp cũ; file hỏng → đỏ rõ (exit 2), không đoán."""

from __future__ import annotations

import contextlib
import io
import json
import os
import random
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
import unittest.mock
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import xt

WEIGHTS = ROOT / "tests" / "shard-weights.json"


def spread(shards: List[List[str]], w: Dict[str, float], default: float) -> float:
    loads = [sum(w.get(t, default) for t in s) for s in shards]
    return max(loads) - min(loads)


class ShardPlanTest(unittest.TestCase):
    def assert_partition(self, ids: List[str], shards: List[List[str]]) -> None:
        flat = [t for s in shards for t in s]
        self.assertEqual(sorted(flat), sorted(set(ids)))  # không sót
        self.assertEqual(len(flat), len(set(flat)))  # không trùng

    def test_without_weights_equals_k_mod_n(self):
        ids = [f"t{k:02d}" for k in range(11)]
        for n in range(1, 6):
            with self.subTest(n=n):
                self.assertEqual(xt.shard_plan(ids, {}, n), [ids[i::n] for i in range(n)])

    def test_partition_with_present_missing_and_stale_weights(self):
        ids = ["a", "b", "c", "d", "e", "f"]
        cases = {
            "đủ": {t: float(i + 1) for i, t in enumerate(ids)},
            "rỗng": {},
            "thiếu một lớp": {t: 2.0 for t in ids[1:]},
            "thừa lớp cũ": dict({t: 1.0 for t in ids}, **{"cu.Lop": 99.0, "cu.Khac": 50.0}),
        }
        for name, w in cases.items():
            for n in (1, 2, 3, 4, 6, 8):
                with self.subTest(case=name, n=n):
                    shards = xt.shard_plan(ids + ["a"], w, n)  # id trùng ở đầu vào bỏ đi
                    self.assertEqual(len(shards), n)
                    self.assert_partition(ids, shards)

    def test_unknown_id_takes_median_and_order_is_deterministic(self):
        w = {"x": 10.0, "y": 1.0, "z": 3.0, "old": 2.0}  # trung vị = 2.5
        self.assertEqual(xt.shard_plan(["x", "y", "z", "new"], w, 2), [["x"], ["new", "y", "z"]])
        self.assertEqual(xt.shard_plan(["new", "z", "y", "x"], w, 2), xt.shard_plan(["x", "y", "z", "new"], w, 2))
        # hoà trọng số → theo id; hoà tổng → shard chỉ số nhỏ nhất
        self.assertEqual(xt.shard_plan(["b", "a"], {"a": 1.0, "b": 1.0}, 2), [["a"], ["b"]])

    def test_balance_within_heaviest_weight(self):
        rng = random.Random(95)
        for _ in range(200):
            ids = [f"t{k}" for k in range(rng.randint(1, 60))]
            w = {t: round(rng.expovariate(0.2), 1) for t in ids if rng.random() < 0.9}
            n = rng.randint(1, 6)
            shards = xt.shard_plan(ids, w, n)
            self.assert_partition(ids, shards)
            default = xt.statistics.median(w.values()) if w else xt.SHARD_DEFAULT_WEIGHT
            heaviest = max(w.get(t, default) for t in ids)
            self.assertLessEqual(spread(shards, w, default), heaviest + 1e-9)

    def test_committed_weights_cover_every_class(self):
        """Lớp mới chưa đo rơi về trung vị → shard lệch dần (D-102): cho thiếu/thừa tới 15 % số lớp để PR thêm test không
        phải đo lại (~7 phút); quá ngưỡng thì chạy lại `dev-task.sh test-weights`."""
        w = xt.load_shard_weights(WEIGHTS)
        ids = set(xt.unittest_class_ids(ROOT, "tests", None))
        cap = len(ids) * 15 // 100
        self.assertLessEqual(len(ids - w.keys()), cap, f"lớp thiếu trọng số: {sorted(ids - w.keys())}")
        self.assertLessEqual(len(w.keys() - ids), cap, f"trọng số của lớp không còn: {sorted(w.keys() - ids)}")

    def test_committed_weights_balance_real_suite(self):
        w = xt.load_shard_weights(WEIGHTS)
        self.assertTrue(w)
        self.assertEqual(WEIGHTS.read_text(encoding="utf-8"), json.dumps(w, indent=1, sort_keys=True) + "\n")
        ids = xt.unittest_class_ids(ROOT, "tests", None)
        default = xt.statistics.median(w.values())
        for n in (3, 4):
            with self.subTest(n=n):
                shards = xt.shard_plan(ids, w, n)
                self.assert_partition(ids, shards)
                self.assertLessEqual(spread(shards, w, default), max(w.get(t, default) for t in ids))
                mod_n = [ids[i::n] for i in range(n)]
                self.assertLessEqual(spread(shards, w, default), spread(mod_n, w, default))


class LoadWeightsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.f = self.tmp / "w.json"

    def test_missing_file_is_empty(self):
        self.assertEqual(xt.load_shard_weights(self.f), {})

    def test_valid(self):
        self.f.write_text('{"a": 1, "b": 2.5, "c": 0}', encoding="utf-8")
        self.assertEqual(xt.load_shard_weights(self.f), {"a": 1.0, "b": 2.5, "c": 0.0})

    def test_bad_files_raise(self):
        for raw, msg in (
            ("{hỏng", "không phải JSON"),
            ("[1, 2]", "phải là object"),
            ('{"a": "1"}', "số giây"),
            ('{"a": true}', "số giây"),
            ('{"a": -1}', "số giây"),
            ('{"a": NaN}', "số giây"),
            ('{"a": Infinity}', "số giây"),
            ('{"a": null}', "số giây"),
        ):
            with self.subTest(raw=raw):
                self.f.write_text(raw, encoding="utf-8")
                with self.assertRaisesRegex(ValueError, msg):
                    xt.load_shard_weights(self.f)

    def test_unreadable_raises(self):
        self.f.mkdir()  # thư mục: IsADirectoryError (OSError khác FileNotFoundError)
        with self.assertRaisesRegex(ValueError, "không đọc được"):
            xt.load_shard_weights(self.f)


class ShardCliTest(unittest.TestCase):
    """`xt.main([...])` trong tiến trình (coverage đo được)."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.f = self.tmp / "w.json"
        patcher = unittest.mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(self.tmp)})
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_xt(self, stdin: str, *args: str):
        out, err = io.StringIO(), io.StringIO()
        with unittest.mock.patch.object(sys, "stdin", io.StringIO(stdin)):
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                rc = xt.main(list(args))
        return rc, out.getvalue(), err.getvalue()

    def test_plan_prints_shard(self):
        self.f.write_text('{"a": 5, "b": 1, "c": 1, "old": 7}', encoding="utf-8")
        got = []
        for i in (1, 2):
            rc, out, err = self.run_xt("c\nb\n\n a\nnew\n", "test-shard-plan", str(i), "2", "--weights", str(self.f))
            self.assertEqual(rc, 0, err)
            self.assertIn(f"[test-shard] {i}/2:", err)
            self.assertIn("1 id không có trong", err)
            got.append(out.split())
        self.assertEqual(got, [["a"], ["b", "c", "new"]])  # new lấy trung vị 3.0

    def test_plan_empty_shard_prints_nothing(self):
        rc, out, _ = self.run_xt("a\n", "test-shard-plan", "2", "2", "--weights", str(self.f))
        self.assertEqual((rc, out), (0, ""))

    def test_plan_red(self):
        for args in (("0", "2"), ("3", "2"), ("1", "0")):
            with self.subTest(args=args):
                rc, out, err = self.run_xt("a\n", "test-shard-plan", *args, "--weights", str(self.f))
                self.assertEqual((rc, out), (2, ""))
                self.assertIn("1 ≤ I ≤ N", err)
        self.f.write_text("{", encoding="utf-8")
        rc, out, err = self.run_xt("a\n", "test-shard-plan", "1", "1", "--weights", str(self.f))
        self.assertEqual((rc, out), (2, ""))
        self.assertIn("không phải JSON hợp lệ", err)

    def test_weights_measures_and_writes_sorted(self):
        unit = 'case "$1" in slow) sleep 0.3 ;; esac; echo "$1" >> ran.txt'
        rc, _, err = self.run_xt("slow\nfast\nfast\n", "test-weights", "--unit", unit, "--out", str(self.f))
        self.assertEqual(rc, 0, err)
        self.assertIn("2 id", err)
        text = self.f.read_text(encoding="utf-8")
        w = json.loads(text)
        self.assertEqual(list(w), ["fast", "slow"])
        self.assertGreaterEqual(w["slow"], 0.2)
        self.assertLess(w["fast"], w["slow"])
        self.assertEqual(text, json.dumps(w, indent=1, sort_keys=True) + "\n")
        self.assertEqual(sorted((self.tmp / "ran.txt").read_text(encoding="utf-8").split()), ["fast", "slow"])

    def test_weights_red_does_not_write(self):
        self.f.write_text('{"keep": 1}', encoding="utf-8")
        rc, _, err = self.run_xt("a\nb\n", "test-weights", "--unit", '[ "$1" != b ]', "--out", str(self.f))
        self.assertEqual(rc, 1)
        self.assertIn("1 id đỏ", err)
        self.assertEqual(self.f.read_text(encoding="utf-8"), '{"keep": 1}')
        rc, _, err = self.run_xt("\n", "test-weights", "--unit", "true", "--out", str(self.f))
        self.assertEqual(rc, 1)
        self.assertIn("không có id", err)

    def test_weights_red_on_old_file_recovers(self):
        """AUD-TEST-019: id đỏ vì chính file trọng số cũ (`test_committed_weights_cover_every_class`) xanh lại khi chạy
        lại trên file vừa đo → giữ file mới; file cũ không có thì id còn đỏ cũng không để lại file."""
        self.f.write_text('{"keep": 1}', encoding="utf-8")
        unit = f'[ "$1" != b ] || grep -q \'"a"\' {shlex.quote(str(self.f))}'  # b đòi file có trọng số của a
        rc, _, err = self.run_xt("a\nb\n", "test-weights", "--unit", unit, "--out", str(self.f))
        self.assertEqual(rc, 0, err)
        self.assertIn("chạy lại 1 id", err)
        self.assertEqual(sorted(json.loads(self.f.read_text(encoding="utf-8"))), ["a", "b"])
        self.f.unlink()
        rc, _, err = self.run_xt("a\nb\n", "test-weights", "--unit", '[ "$1" != b ]', "--out", str(self.f))
        self.assertEqual(rc, 1)
        self.assertFalse(self.f.exists())

    def test_weights_hung_id_times_out_red(self):
        """AUD-HAR-103 (BASE-ERR-004): một id treo quá `XT_RECORD_TIMEOUT` là đỏ — cả nhóm tiến trình bị dừng, không treo;
        biến sai → exit 2."""
        unit = 'case "$1" in hang) sleep 30 ;; esac'
        with unittest.mock.patch.dict(os.environ, {"XT_RECORD_TIMEOUT": "1"}):
            start = time.monotonic()
            rc, _, err = self.run_xt("ok\nhang\n", "test-weights", "--unit", unit, "--out", str(self.f))
        self.assertEqual(rc, 1, err)
        self.assertIn("1 id đỏ", err)
        self.assertIn("hang", err)
        self.assertLess(time.monotonic() - start, 20)
        self.assertFalse(self.f.exists())
        with unittest.mock.patch.dict(os.environ, {"XT_RECORD_TIMEOUT": "x"}):
            rc, _, err = self.run_xt("ok\n", "test-weights", "--unit", "true", "--out", str(self.f))
        self.assertEqual(rc, 2)
        self.assertIn("XT_RECORD_TIMEOUT", err)

    def test_weights_interrupted_rerun_restores_old_file(self):
        """Bị ngắt (Ctrl-C) giữa lần chạy lại id đỏ → file cũ được trả lại, không giữ số đo của lần chạy đỏ."""
        self.f.write_text('{"keep": 1}', encoding="utf-8")
        runs = [({"a": 1.0, "b": 2.0}, ["b"]), KeyboardInterrupt()]

        def fake(ids, unit, cwd, timeout):
            r = runs.pop(0)
            if isinstance(r, BaseException):
                raise r
            return r

        args = xt.argparse.Namespace(unit="true", out=str(self.f))
        with (
            unittest.mock.patch.object(xt, "measure_test_weights", fake),
            unittest.mock.patch.object(xt, "_stdin_ids", lambda: ["a", "b"]),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            with self.assertRaises(KeyboardInterrupt):
                xt.cmd_test_weights(args)
        self.assertEqual(self.f.read_text(encoding="utf-8"), '{"keep": 1}')


@unittest.skipIf(shutil.which("bash") is None, "cần bash")
class DevTaskProject(unittest.TestCase):
    """Dự án giả cho `dev-task.sh` (xt.py chép cạnh dev-task.sh); không có test riêng."""

    RECORD = 'f="$(mktemp "$OUT/ran.XXXXXX")" && echo "$1" > "$f"'

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        (self.tmp / "scripts").mkdir()
        for name in ("dev-task.sh", "xt.py"):
            shutil.copy(ROOT / "scripts" / name, self.tmp / "scripts" / name)
        self.out = self.tmp / "out"
        self.out.mkdir()
        (self.tmp / "ids.txt").write_text("a\nb\nc\nd\ne\n", encoding="utf-8")
        self.w = self.tmp / "w.json"

    def yaml(self, **keys: str) -> None:
        base = {"test_list": "cat ids.txt", "test_unit": self.RECORD, "test_weights": "w.json"}
        base.update(keys)
        text = "".join(f"{k}: {v}\n" for k, v in base.items() if v is not None)
        (self.tmp / "xt.yaml").write_text(text, encoding="utf-8")

    def run_dt(self, *args: str, **env: str) -> subprocess.CompletedProcess:
        base = {k: v for k, v in os.environ.items() if k not in ("XT_MIN_TESTS", "XT_COV_DIR", "XT_PY")}
        full = dict(base, CLAUDE_PROJECT_DIR=str(self.tmp), OUT=str(self.out), **env)
        return subprocess.run(
            ["bash", str(self.tmp / "scripts" / "dev-task.sh"), *args], capture_output=True, text=True, env=full
        )

    def ran(self) -> List[str]:
        got = [p.read_text(encoding="utf-8").strip() for p in self.out.glob("ran.*")]
        for p in self.out.glob("ran.*"):
            p.unlink()
        return sorted(got)

    def shards(self, n: int) -> List[List[str]]:
        res = []
        for i in range(1, n + 1):
            r = self.run_dt("test-shard", str(i), str(n))
            self.assertEqual(r.returncode, 0, r.stderr)
            res.append(self.ran())
        return res


# Bảng ca của `test_weighted_partition_cases`: mỗi ca chạy `dev-task.sh` hai lần (vài giây dưới coverage) nên chia theo
# chỉ số cho `WEIGHT_CASE_PARTS` lớp — hợp các phần đúng bằng bảng (`test_partition_case_parts_cover_table`).
WEIGHT_CASES: Dict[str, Dict[str, int] | None] = {
    "vắng": None,
    "đủ": {"a": 9, "b": 1, "c": 1, "d": 1, "e": 1},
    "thiếu một lớp": {"a": 9, "b": 1, "c": 1, "d": 1},
    "thừa lớp cũ": {"a": 9, "b": 1, "c": 1, "d": 1, "e": 1, "cu": 50},
}
WEIGHT_CASE_PARTS = 2


def weight_case_part(part: int) -> Dict[str, Dict[str, int] | None]:
    names = list(WEIGHT_CASES)[part::WEIGHT_CASE_PARTS]
    return {name: WEIGHT_CASES[name] for name in names}


class WeightedPartitionPart:
    """Mixin (không phải TestCase, không tự chạy): phần `PART` của `WEIGHT_CASES`; lớp con ghép với `DevTaskProject`."""

    PART = -1

    def test_weighted_partition_cases(self):
        self.yaml()
        cases = weight_case_part(self.PART)
        self.assertTrue(cases)
        for name, w in cases.items():
            if w is None:
                self.w.unlink(missing_ok=True)
            else:
                self.w.write_text(json.dumps(w), encoding="utf-8")
            # N = 2: phân hoạch mọi N đã kiểm trong tiến trình (ShardPlanTest); đây kiểm dây nối dev-task.sh ↔ xt.py
            with self.subTest(case=name):
                got = self.shards(2)
                self.assertEqual(sorted(t for s in got for t in s), ["a", "b", "c", "d", "e"])
                want = [["a"], ["b", "c", "d", "e"]] if w is not None else [["a", "c", "e"], ["b", "d"]]
                self.assertEqual(got, want)  # có trọng số: lớp nặng nhất đứng một mình


class DevTaskWeightedPartitionPart1Test(WeightedPartitionPart, DevTaskProject):
    PART = 0


class DevTaskWeightedPartitionPart2Test(WeightedPartitionPart, DevTaskProject):
    PART = 1


class DevTaskWeightedShardTest(DevTaskProject):
    """`dev-task.sh test-shard`/`test-weights` với khoá `test_weights` (lệnh giả, id a..e)."""

    def test_partition_case_parts_cover_table(self):
        parts = sorted(c.PART for c in WeightedPartitionPart.__subclasses__())
        self.assertEqual(parts, list(range(WEIGHT_CASE_PARTS)))  # mỗi phần đúng một lớp
        merged = [name for p in parts for name in weight_case_part(p)]
        self.assertEqual(sorted(merged), sorted(WEIGHT_CASES))  # hợp == bảng đầy đủ
        self.assertEqual(len(merged), len(set(merged)))  # các phần rời nhau

    def test_broken_weights_red_exit_2(self):
        self.yaml()
        self.w.write_text("{không phải json", encoding="utf-8")
        r = self.run_dt("test-shard", "1", "2")
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertIn("không phải JSON hợp lệ", r.stderr)
        self.assertEqual(self.ran(), [])

    def test_weights_need_xt_py(self):
        self.yaml()
        (self.tmp / "scripts" / "xt.py").unlink()
        r = self.run_dt("test-shard", "1", "2")
        self.assertEqual(r.returncode, 2)
        self.assertIn("test_weights", r.stderr)
        self.assertEqual(self.ran(), [])

    def test_no_key_keeps_mod_n(self):
        self.yaml(test_weights=None)
        self.w.write_text("{hỏng", encoding="utf-8")  # không khai khoá → file không được đọc
        self.assertEqual(self.shards(2), [["a", "c", "e"], ["b", "d"]])

    def test_weights_task(self):
        self.yaml(test_weights=None)
        r = self.run_dt("test-weights")
        self.assertEqual(r.returncode, 2)
        self.assertIn("test_weights", r.stderr)
        self.yaml(test_unit='[ -d "$XT_COV_DIR" ] && echo "$1" >> ran.txt')
        r = self.run_dt("test-weights")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(sorted(json.loads(self.w.read_text(encoding="utf-8"))), ["a", "b", "c", "d", "e"])
        self.assertEqual((self.tmp / "ran.txt").read_text(encoding="utf-8").split(), ["a", "b", "c", "d", "e"])
        self.yaml(test_list="cat ids.txt; exit 1")
        self.assertEqual(self.run_dt("test-weights").returncode, 1)
        self.yaml(test_unit="true")
        self.assertEqual(self.run_dt("test-weights").returncode, 2)
        self.yaml(test_unit=f"{self.RECORD}; git push origin main")
        (self.tmp / ".claude" / "hooks").mkdir(parents=True)
        shutil.copy(ROOT / ".claude" / "hooks" / "guard.py", self.tmp / ".claude" / "hooks" / "guard.py")
        r = self.run_dt("test-weights", XT_GUARD_POLICY="")
        self.assertEqual(r.returncode, 126, r.stderr)


class DevTaskRealSuiteShardTest(DevTaskProject):
    """Lớp riêng (mỗi lớp một tiến trình khi chạy song song): liệt kê bộ test thật tốn vài giây mỗi shard."""

    def test_real_suite_weighted_partition_equals_discover(self):
        """Lệnh `test_list` + `test_weights` THẬT của xt.yaml: hợp các shard == tập lớp của unittest discover."""
        yaml = (ROOT / "xt.yaml").read_text(encoding="utf-8")
        listing = re.search(r"^test_list: (.*)$", yaml, re.M).group(1)
        weights = re.search(r"^test_weights: (.*)$", yaml, re.M).group(1)
        self.assertEqual(ROOT / weights, WEIGHTS)
        (self.tmp / "tests").symlink_to(ROOT / "tests", target_is_directory=True)
        self.yaml(test_list=listing, test_weights=weights)
        want = xt.unittest_class_ids(ROOT, "tests", None)
        got = self.shards(4)  # N của job `test`; N khác đã kiểm trong tiến trình (ShardPlanTest)
        flat = [t for s in got for t in s]
        self.assertEqual(sorted(flat), want)
        self.assertEqual(len(flat), len(set(flat)))


if __name__ == "__main__":
    unittest.main()
