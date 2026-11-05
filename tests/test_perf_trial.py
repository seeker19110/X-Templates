"""`xt.py perf trial` (ADR-0071) — đơn vị. T-3701: gốc vòng do máy tính (nhánh mặc định từ máy chủ, ngoại tuyến từ
`refs/remotes/origin/HEAD` — D-361), công cụ chấm từ blob gốc (`exec` khi byte khác — D-363), cấu hình `perf/trial.json`
ở gốc + khoá mặc định, sổ `.autopilot/perf-trial.json` (khoá `state.lock`, `rev`) + `perf-trials.jsonl` (chỉ nối, fsync),
`start`/`status`/`abort`/`log`, đếm ba lần theo đường, `budget`. Repo git tạm thật (dự án đồ chơi của `tests.test_flow`);
ca luồng FLOW-22/37…40 ở `tests.test_flow`."""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import pwd
import re
import signal
import subprocess
import sys
import time
import unittest
import unittest.mock
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import xt
from test_flow import GIT_ID, HOT, TOOL, TRIAL_ARGS, flow, trial_config, trial_files
from test_xt_cli import TmpRepoCase, run_main

XT = ROOT / "scripts" / "xt.py"


class TrialCase(TmpRepoCase):
    """Dự án đồ chơi như `TrialFlowTest`: máy chủ `origin` (bare, `main`), cây agent ở nhánh `opt`; lệnh chạy trong tiến
    trình (`run_main`) để coverage thấy từng nhánh."""

    def setUp(self) -> None:
        super().setUp()
        self.ctl = self.tmp / "ctl"
        self.ctl.mkdir()
        self.origin = self.tmp / "origin.git"
        self.run_git(self.tmp, "init", "-q", "--bare", "-b", "main", str(self.origin))
        self.init_repo()
        self.write_tree(self.repo, {**trial_files(self.ctl), "perf/trial.json": json.dumps(trial_config())})
        (self.repo / TOOL).parent.mkdir(parents=True)
        (self.repo / TOOL).write_bytes(XT.read_bytes())
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "gốc")
        self.git("remote", "add", "origin", str(self.origin))
        self.git("push", "-q", "-u", "origin", "main")
        self.git("remote", "set-head", "origin", "-a")
        self.git("checkout", "-q", "-b", "opt")
        self.base = self.git("rev-parse", "HEAD")
        self.enterContext(unittest.mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(self.repo)}))

    def run_git(self, cwd: Path, *args: str) -> str:
        cmd = ["git", "-C", str(cwd), *GIT_ID, "-c", "protocol.file.allow=always", *args]
        return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.strip()

    def write_tree(self, root: Path, files: dict[str, str]) -> None:
        for rel, text in files.items():
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            (root / rel).write_text(text, encoding="utf-8")

    def put(self, rel: str, text: str) -> Path:
        self.write_tree(self.repo, {rel: text})
        return self.repo / rel

    def maintain(self, files: dict[str, str], gone: tuple[str, ...] = (), fetch: bool = True) -> str:
        """Người bảo trì đổi `main` của máy chủ (`gone` = xoá); cây agent `fetch` khi `fetch`."""
        maint = self.tmp / "maint"
        if not maint.exists():
            self.run_git(self.tmp, "clone", "-q", str(self.origin), str(maint))
        self.write_tree(maint, files)
        for rel in gone:
            self.run_git(maint, "rm", "-q", "-r", rel)
        self.run_git(maint, "add", "-A")
        self.run_git(maint, "commit", "-q", "-m", "bảo trì")
        self.run_git(maint, "push", "-q", "origin", "HEAD:main")
        if fetch:
            self.git("fetch", "-q", "origin")
        return self.run_git(maint, "rev-parse", "HEAD")

    def republish(self, files: dict[str, str], gone: tuple[str, ...] = ()) -> None:
        self.maintain(files, gone)
        self.git("checkout", "-q", "-B", "opt", "origin/main")
        self.base = self.git("rev-parse", "HEAD")

    def tr(self, *args: str) -> tuple[int, str, str]:
        return run_main("perf", "trial", *args)

    def ok(self, *args: str) -> str:
        rc, out, err = self.tr(*args)
        self.assertEqual(rc, 0, out + err)
        return out

    def refused(self, *args: str, code: int = 2) -> str:
        before = self.ledger()
        rc, out, err = self.tr(*args)
        self.assertEqual((rc, self.ledger()), (code, before), out + err)
        return out + err

    def start(self, *hot: str, extra: tuple[str, ...] = TRIAL_ARGS) -> tuple[int, str, str]:
        return self.tr("start", *(a for h in hot or ("src/hot.py",) for a in ("--hotspot", h)), *extra)

    def started(self, *hot: str) -> str:
        rc, out, err = self.start(*hot)
        self.assertEqual(rc, 0, out + err)
        return str(self.tstate()["id"])

    def tstate(self) -> dict[str, Any]:
        data = json.loads((self.repo / ".autopilot" / xt.PERF_TRIAL_FILE).read_text(encoding="utf-8"))
        assert isinstance(data, dict)
        return data

    def rows(self) -> list[dict[str, Any]]:
        path = self.repo / ".autopilot" / xt.PERF_TRIALS_LOG
        return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []

    def ledger(self) -> tuple[bytes | None, ...]:
        files = (self.repo / ".autopilot" / n for n in (xt.PERF_TRIAL_FILE, xt.PERF_TRIALS_LOG))
        return tuple(f.read_bytes() if f.exists() else None for f in files)

    def append_row(self, row: dict[str, Any]) -> None:
        (self.repo / ".autopilot").mkdir(exist_ok=True)
        with (self.repo / ".autopilot" / xt.PERF_TRIALS_LOG).open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"schema": 1, **row}) + "\n")

    def append_kept(self, files: list[str]) -> None:
        """Dòng `decide kept` (như `finish` T-3703 sẽ ghi) với cây neo = `HEAD^{tree}` hiện tại."""
        row = {"event": "decide", "id": "PT-0001", "base_sha": self.base, "hotspot": files, "verdict": "kept"}
        self.append_row({**row, "candidate_tree": self.git("rev-parse", "HEAD^{tree}"), "candidate_files": files})

    def ctx(self) -> xt.TrialCtx:
        return xt.trial_context(self.repo, ["perf", "trial", "status"])


class TrialConfigTest(unittest.TestCase):
    def test_doc_example_is_valid(self) -> None:
        """T-3707: ví dụ `perf/trial.json` trong `optimization-loop.md` (khối ```json đầu tiên) qua kiểm cấu hình, Gate mẫu
        của PLAN-opt là `perf trial status --check` chạy `xt.py` từ blob gốc."""
        doc = (ROOT / "framework" / "11-autonomous-loop" / "optimization-loop.md").read_text(encoding="utf-8")
        block = doc.split("```json\n", 1)[1].split("```", 1)[0]
        self.assertIsNone(xt.trial_config_problem(json.loads(block)))
        self.assertIn(GATE.format(".xtemplates/scripts/xt.py"), re.sub(r"\s+", " ", doc))

    def test_valid_config_and_unlock(self) -> None:
        self.assertIsNone(xt.trial_config_problem(trial_config()))
        self.assertIsNone(xt.trial_config_problem(trial_config(unlock=["pyproject.toml", "**/*.lock"])))

    def test_problems(self) -> None:
        """Từng lỗi một lý do: không phải object, khoá lạ/thiếu/sai kiểu (bool không là số), giá trị."""
        sec = trial_config()["secondary"][0]
        cases = {
            "cần object JSON": [],
            "lockd": trial_config(lockd=[]),
            "budget": trial_config(budget=True),
            "timeout": trial_config(timeout="1"),
            "setup": {k: v for k, v in trial_config().items() if k != "setup"},
            '"schema" phải là': trial_config(schema=2),
            '"budget" phải ≥ 1': trial_config(budget=0),
            '"metric.cmd"': trial_config(metric={"kind": "exact"}),
            "danh sách glob": trial_config(locked=["bench.py", ""]),
            "≠ primary": trial_config(secondary=[{**sec, "name": "primary"}]),
            "trùng": trial_config(secondary=[sec, sec]),
            '"unlock" ngoài': trial_config(unlock=["bench.py"]),
            '"metric" = {': trial_config(metric={"cmd": "x", "kind": "cpu"}),
            "runs: số nguyên": trial_config(metric={"cmd": "x", "kind": "exact", "runs": 0}),
            "higher_is_better: bool": trial_config(metric={"cmd": "x", "kind": "exact", "higher_is_better": 1}),
            "kind wall": trial_config(metric={"cmd": "x", "kind": "wall", "runs": 3}),
            "unit: chuỗi": trial_config(metric={"cmd": "x", "kind": "exact", "rnus": 3}),
            '"secondary[]" = {': trial_config(secondary=[{**sec, "ceiling": "1"}]),
            "regress: số ≥ 0": trial_config(secondary=[{**sec, "regress": -1}]),
            "ceiling: số": trial_config(secondary=[{**sec, "ceiling": float("inf")}]),
            "có chỉ số kind wall": trial_config(secondary=[{**sec, "kind": "wall"}]),
            '"target" =': trial_config(target="primary giảm 20%"),
            "chỉ số = primary": trial_config(target="rss <= -5%"),
        }
        for want, cfg in cases.items():
            with self.subTest(want):
                self.assertIn(want, str(xt.trial_config_problem(cfg)))

    def test_locks_default_minus_unlock_plus_config_and_tool(self) -> None:
        ctx = xt.TrialCtx("b", "refs/heads/main", TOOL, "t", trial_config(unlock=["pyproject.toml"]), "c", [])
        self.assertTrue(
            all(ctx.locked(p) for p in ("bench.py", "a/b/x.pth", "pkg/package.json", TOOL, "perf/trial.json"))
        )
        self.assertFalse(ctx.locked("pyproject.toml") or ctx.locked("src/hot.py"))
        self.assertTrue(xt.TrialCtx("b", "r", TOOL, "t", trial_config(), "c", []).locked("sub/pyproject.toml"))


class TrialLedgerTest(unittest.TestCase):
    def kept(self, **over: Any) -> dict[str, Any]:
        row = {"schema": 1, "event": "decide", "id": "PT-0001", "base_sha": "b", "hotspot": ["a"], "verdict": "kept"}
        return {**row, "candidate_tree": "t", "candidate_files": ["a"], **over}

    def test_row_shapes(self) -> None:
        start = {"schema": 1, "event": "start", "id": "PT-0001", "base_sha": "b", "default_ref": "r", "hotspot": ["a"]}
        start |= {"origin_url": "u"}
        start |= {"hypothesis": "h", "falsifier": "f", "start_head": "s"}
        good = [start, self.kept(), {"schema": 1, "event": "log", "base_sha": "b", "tree": "t"}]
        bad = [
            [],
            {**start, "schema": True},
            {**start, "schema": 2},
            {**start, "event": ["start"]},
            {**start, "default_ref": None},
            {k: v for k, v in start.items() if k != "origin_url"},
            {**start, "hotspot": [1]},
            self.kept(candidate_files="a"),
            self.kept(candidate_tree=None),
        ]
        self.assertEqual([xt._trial_row_ok(r) for r in good], [True] * 3)
        self.assertEqual([xt._trial_row_ok(r) for r in bad], [False] * len(bad))

    def test_streaks_per_path_kept_resets_only_changed(self) -> None:
        def no(*hot: str) -> dict[str, Any]:
            return {"event": "decide", "id": f"PT-00{len(hot)}0", "verdict": "aborted", "hotspot": list(hot)}

        rows = [no("a"), no("a", "b"), self.kept(hotspot=["a", "b"], candidate_files=["b", "x"]), {"event": "log"}]
        self.assertEqual(xt.trial_streaks(rows), {"a": 2, "b": 0})

    def test_anchor_latest_kept_or_log_of_round(self) -> None:
        rows = [
            self.kept(candidate_tree="k1"),
            {"event": "log", "base_sha": "b", "tree": "l1"},
            self.kept(base_sha="o"),
        ]
        self.assertEqual(xt.trial_anchor(rows, "b"), "l1")
        self.assertEqual(xt.trial_anchor(rows[:1], "b"), "k1")
        self.assertIsNone(xt.trial_anchor(rows, "z"))

    def test_log_block_and_merge(self) -> None:
        ctx = xt.TrialCtx("b" * 40, "refs/heads/main", TOOL, "t", trial_config(), "c", [])
        rows = [{"event": "decide", "id": "PT-0009", "base_sha": "b" * 40, "hotspot": ["a|b"], "verdict": "aborted"}]
        block = xt.trial_log_block(rows, ctx)
        self.assertIn("| PT-0009 | aborted | a\\|b |  |  |  | 0 |", block)
        self.assertEqual(xt.trial_log_merge("", block, ctx.base_sha), block)
        self.assertEqual(xt.trial_log_merge("x", block, ctx.base_sha), "x\n\n" + block)
        self.assertEqual(xt.trial_log_merge("x\n", block, ctx.base_sha), "x\n\n" + block)
        old = "đầu\n" + block.replace("PT-0009", "PT-0001") + "cuối\r\n"
        self.assertEqual(xt.trial_log_merge(old, block, ctx.base_sha), "đầu\n" + block + "cuối\r\n")
        tail = "đầu\n" + block.rstrip("\n")
        self.assertEqual(xt.trial_log_merge(tail, block, ctx.base_sha), "đầu\n" + block)
        with self.assertRaisesRegex(xt.TrialRefused, "mốc đóng"):
            xt.trial_log_merge(block.replace(xt.PERF_TRIAL_LOG_END, ""), block, ctx.base_sha)

    def test_falsifier_and_path(self) -> None:
        cfg = trial_config()
        self.assertEqual(xt.trial_falsifier(" mem >= 5% ", cfg), "mem >= 5%")
        for bad in ("primary > 5", "rss > 5%", "primary >5%"):
            with self.subTest(bad), self.assertRaises(xt.TrialRefused):
                xt.trial_falsifier(bad, cfg)
        self.assertEqual(xt._trial_path(" ./src//hot.py "), "src/hot.py")
        for bad in ("", ".", "..", "/etc/x", "../x", "a::f", ".autopilot", ".autopilot/x", "a/../../x"):
            with self.subTest(bad), self.assertRaises(xt.TrialRefused):
                xt._trial_path(bad)


class TrialStartTest(TrialCase):
    def test_start_records_state_and_row(self) -> None:
        """`start` ghi state (`started`, `rev` 1) và một dòng `start` cùng trường; `status` in lần thử mở."""
        tid = self.started("./src//hot.py", "src/new.py")
        st, rows = self.tstate(), self.rows()
        self.assertEqual(
            (tid, st["phase"], st["rev"], st["hotspot"]), ("PT-0001", "started", 1, ["src/hot.py", "src/new.py"])
        )
        self.assertEqual(st["default_ref"], "refs/heads/main")
        self.assertEqual(st["tool_sha"], self.git("rev-parse", f"{self.base}:{TOOL}"))
        self.assertEqual([(r["event"], r["id"], r["fp_start"]) for r in rows], [("start", tid, st["fp_start"])])
        out = self.ok("status")
        self.assertIn(f"{tid} pha started", out)
        self.assertIn("kế: `perf trial finish` · bỏ", out)
        self.assertIn(f"lần thử {tid} đang mở", self.refused("start", "--hotspot", "src/hot.py", *TRIAL_ARGS))

    def test_refusals_write_nothing(self) -> None:
        """Mỗi điều kiện từ chối exit 2, sổ không đổi: giả thuyết rỗng, falsifier sai, điểm nóng là thư mục/khớp khoá,
        cây bẩn."""
        bad = {
            "--hypothesis rỗng": ("--hotspot", "src/hot.py", "--hypothesis", " ", "--falsifier", "primary > -5%"),
            "--falsifier": ("--hotspot", "src/hot.py", "--hypothesis", "h", "--falsifier", "x"),
            "không phải file": ("--hotspot", "src", *TRIAL_ARGS),
            "khớp khoá": ("--hotspot", "bench.py", "--hotspot", "pyproject.toml", *TRIAL_ARGS),
        }
        for want, args in bad.items():
            with self.subTest(want):
                self.assertIn(want, self.refused("start", *args))
        self.put("src/x.py", "1\n")
        self.assertIn("src/x.py", self.refused("start", "--hotspot", "src/hot.py", *TRIAL_ARGS))

    def test_locked_change_since_base_refused_even_with_anchor(self) -> None:
        """Lớp kiểm lại (§2): cây neo của sổ trùng HEAD nhưng `base..HEAD` đổi file khoá → exit 2."""
        self.put("bench.py", "print(1)\n")
        self.git("commit", "-q", "-am", "sửa bộ đo")
        self.append_kept(["bench.py"])
        self.assertIn("file khoá đổi so với gốc", self.refused("start", "--hotspot", "src/hot.py", *TRIAL_ARGS))

    def test_strikes_budget_and_ids(self) -> None:
        """Đếm theo đường (exit 3 nêu đường), `budget` của vòng (exit 3), `id` tăng theo sổ."""
        self.republish({"perf/trial.json": json.dumps(trial_config(budget=4))})
        for i in range(3):
            self.started("src/hot.py")
            self.ok("abort", "--reason", f"r{i}")
        self.assertIn("src/hot.py: 3 lần", self.refused("start", "--hotspot", "src/hot.py", *TRIAL_ARGS, code=3))
        self.assertEqual(self.started("src/other.py"), "PT-0004")
        self.ok("abort", "--reason", "r")
        self.assertIn("hết budget 4", self.refused("start", "--hotspot", "src/notes.txt", *TRIAL_ARGS, code=3))
        doc = json.loads(self.ok("status", "--json"))
        self.assertEqual(
            (doc["budget"], doc["streaks"], doc["next"]),
            ({"used": 4, "max": 4}, {"src/hot.py": 3, "src/other.py": 1}, "start"),
        )
        self.assertIn("src/hot.py: 3/3", self.ok("status"))

    def test_concurrent_starts_one_wins(self) -> None:
        """Hai `start` cùng lúc (hai tiến trình): đúng một exit 0, một exit 2 (đang mở) — một dòng `start`."""
        cmd = [sys.executable, str(XT), "perf", "trial", "start", "--hotspot", "src/hot.py", *TRIAL_ARGS]
        procs = [subprocess.Popen(cmd, cwd=self.repo, stdout=subprocess.PIPE, stderr=subprocess.PIPE) for _ in range(2)]
        codes = sorted(p.wait(timeout=120) for p in procs)
        for p in procs:
            p.communicate()
        self.assertEqual(codes, [0, 2])
        self.assertEqual([r["event"] for r in self.rows()], ["start"])

    def test_update_rev_conflict_writes_nothing(self) -> None:
        """`rev` trên đĩa đổi giữa đọc và ghi (ghi ngoài khoá) → exit 2, không nối dòng sổ."""
        self.started()
        self.ok("abort", "--reason", "x")
        before = self.ledger()
        real = xt.trial_read
        calls = iter([None, {"rev": 99}])
        with unittest.mock.patch.object(xt, "trial_read", lambda b: next(calls, None) or real(b)):
            rc, out, err = self.start()
        self.assertEqual((rc, self.ledger()), (2, before), out + err)
        self.assertIn("đổi ngoài khoá", err)


class TrialBaseTest(TrialCase):
    def test_offline_falls_back_to_local_origin_head(self) -> None:
        """Máy chủ không với tới (URL hỏng) → `refs/remotes/origin/HEAD`; thiếu nó → exit 2 kèm cách đặt."""
        url = str(self.tmp / "không-có")
        self.git("remote", "set-url", "origin", url)
        self.assertEqual(xt.trial_round_base(self.repo, url), (self.base, "refs/heads/main"))
        self.git("remote", "set-head", "origin", "-d")
        self.assertIn("set-head origin -a", self.refused("status"))

    def test_server_without_head_symref_and_timeout(self) -> None:
        """Máy chủ trả rc 0 mà không có symref (repo rỗng) hoặc `ls-remote` quá giờ → None (dùng ref cục bộ)."""
        empty = self.tmp / "empty.git"
        self.run_git(self.tmp, "init", "-q", "--bare", str(empty))
        self.assertIsNone(xt._trial_ls_remote(str(empty)))
        real = subprocess.run

        def slow(cmd: Any, *a: Any, **k: Any) -> Any:
            if "ls-remote" in cmd:
                raise subprocess.TimeoutExpired(cmd, 1)
            return real(cmd, *a, **k)

        with unittest.mock.patch.object(xt.subprocess, "run", slow):
            self.assertIsNone(xt._trial_ls_remote(str(self.origin)))

    def test_unfetched_server_tip_refused(self) -> None:
        self.maintain({"src/other.py": "EXTRA = 1\n"}, fetch=False)
        self.assertIn("git fetch origin", self.refused("status"))

    def test_default_branch_renamed_refused(self) -> None:
        self.started()
        self.ok("abort", "--reason", "x")
        self.git("push", "-q", "origin", "opt:trunk")
        self.run_git(self.origin, "symbolic-ref", "HEAD", "refs/heads/trunk")
        self.assertIn("nhánh mặc định đổi refs/heads/main → refs/heads/trunk", self.refused("status"))

    def test_config_missing_or_broken_refused(self) -> None:
        self.republish({"perf/trial.json": "{không phải json"})
        self.assertIn("hỏng: cần object JSON", self.refused("status"))
        self.republish({}, gone=("perf",))
        self.assertIn("không có perf/trial.json", self.refused("status"))

    def test_framework_repo_tool_path_and_missing_tool(self) -> None:
        """Repo khung: công cụ ở `scripts/xt.py`; gốc không có công cụ nào → exit 2."""
        self.republish({"scripts/xt.py": XT.read_text(encoding="utf-8")}, gone=(".xtemplates",))
        self.assertEqual(self.ctx().tool, "scripts/xt.py")
        self.republish({}, gone=("scripts",))
        self.assertIn("không có .xtemplates/scripts/xt.py hay scripts/xt.py", self.refused("status"))

    def test_tool_bytes_differ_execs_base_blob(self) -> None:
        """D-363/D-366: byte `xt.py` đang chạy ≠ blob ở gốc → tiến trình con `python3 -I <bản gốc> <đúng argv>` với
        `CLAUDE_PROJECT_DIR` = gốc dự án (bản xuất nằm ngoài dự án — review #442 🟢a), thoát với mã của con, thư mục tạm
        dọn sau khi con xong (🟢b); bằng nhau thì không."""
        self.republish({TOOL: XT.read_text(encoding="utf-8") + "# bản gốc khác\n"})
        tmp = self.tmp / "tmpdir"
        tmp.mkdir()
        real, seen = subprocess.run, {}

        def spy(cmd: Any, *a: Any, **k: Any) -> Any:
            if list(cmd[:2]) == [sys.executable, "-I"]:
                seen.update(cmd=cmd, env=k["env"], text=Path(cmd[2]).read_text(encoding="utf-8"))
                return real(cmd, *a, **{**k, "capture_output": True, "text": True, "cwd": self.tmp})
            return real(cmd, *a, **k)

        with (
            unittest.mock.patch.object(xt.tempfile, "tempdir", str(tmp)),
            unittest.mock.patch.object(xt.subprocess, "run", spy),
            self.assertRaises(SystemExit) as ex,
        ):
            run_main("perf", "trial", "status", "--json")
        self.assertEqual(ex.exception.code, 0)
        self.assertEqual(seen["cmd"][3:], ["perf", "trial", "status", "--json"])
        self.assertEqual(seen["env"]["CLAUDE_PROJECT_DIR"], str(self.repo))
        self.assertTrue(seen["text"].endswith("# bản gốc khác\n"))
        self.assertEqual(list(tmp.iterdir()), [])

    def test_gate_process_substitution_runs_once_and_leaves_no_tmp(self) -> None:
        """Review #442 🟢b: Gate `python3 -I <(git cat-file blob <gốc>:xt.py) perf trial status` — `__file__` là ống
        `/dev/fd/N` đọc lại rỗng: chạy bản gốc một lần, exit 0, không để lại `xt-perf-tool-*`."""
        tmp = self.tmp / "tmpdir"
        tmp.mkdir()
        gate = f"python3 -I <(git cat-file blob {self.base}:{TOOL}) perf trial status"
        env = {**os.environ, "TMPDIR": str(tmp)}
        r = subprocess.run(["bash", "-c", gate], cwd=self.repo, env=env, capture_output=True, text=True, check=False)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("perf trial: vòng", r.stdout)
        self.assertEqual(list(tmp.iterdir()), [])

    def test_git_error_is_exit_2(self) -> None:
        with unittest.mock.patch.object(xt, "trial_context", side_effect=RuntimeError("git lỗi")):
            self.assertEqual(self.tr("status")[0], 2)

    def test_every_command_execs_base_tool(self) -> None:
        """T-3706, §5: byte `xt.py` khác blob gốc → MỌI lệnh con (cả cờ `--resume`/`--no-apply`) chạy bản gốc với đúng
        argv, trước khi lệnh làm gì (sổ không đổi)."""
        self.republish({TOOL: XT.read_text(encoding="utf-8") + "# bản gốc khác\n"})
        commands = (
            ("start", "--hotspot", "src/hot.py", *TRIAL_ARGS),
            ("prepare",),
            ("finish", "--resume", "--no-apply", "--json"),
            ("status", "--check"),
            ("abort", "--reason", "x"),
            ("log", "--check"),
        )
        for args in commands:
            with self.subTest(args), unittest.mock.patch.object(xt, "_trial_exec", side_effect=SystemExit(7)) as ex:
                before = self.ledger()
                with self.assertRaises(SystemExit) as cm:
                    run_main("perf", "trial", *args)
                self.assertEqual((cm.exception.code, self.ledger()), (7, before))
                self.assertEqual(ex.call_args.args[2], ["perf", "trial", *args])


class TrialHeadTreeTest(TrialCase):
    def test_first_start_of_round_needs_base_tree(self) -> None:
        self.put("src/other.py", "EXTRA = 0\n")
        self.git("commit", "-q", "-am", "commit lạ")
        self.assertIn("HEAD^{tree} ≠ cây", self.refused("start", "--hotspot", "src/hot.py", *TRIAL_ARGS))

    def test_hotspot_new_file_and_file_added_by_kept(self) -> None:
        """Đường chưa có ở gốc và HEAD nhận được; file có ở HEAD (lần giữ trước thêm) nhận được; gitlink/thư mục thì không."""
        self.put("src/added.py", "A = 1\n")
        self.git("add", "src/added.py")
        self.git("commit", "-q", "-m", "giữ")
        self.append_kept(["src/added.py"])
        self.assertEqual(self.started("src/added.py", "src/brand-new.py"), "PT-0002")


class TrialAbortTest(TrialCase):
    def test_abort_reverts_exact_files_once(self) -> None:
        """`abort`: sửa + file mới + xoá trong danh sách → stash, vân tay = lúc start; `.autopilot/` và file bị ignore còn;
        một dòng `decide aborted` có `reason`, `candidate_files`; pha `closed`; `abort` lần nữa → exit 2."""
        fp0 = xt.tree_fingerprint(self.repo)
        tid = self.started("src/hot.py", "src/new.py", "src/notes.txt")
        self.put("src/hot.py", HOT + "# sửa\n")
        self.put("src/new.py", "N = 1\n")
        (self.repo / "src" / "notes.txt").unlink()
        self.put(".autopilot/note.txt", "giữ\n")
        self.put("scratch.log", "ignore\n")
        out = self.ok("abort", "--reason", "  hướng sai ")
        self.assertIn("3 file thu hồi vào stash", out)
        self.assertEqual((xt.tree_fingerprint(self.repo), self.git("status", "--porcelain")), (fp0, ""))
        self.assertTrue((self.repo / ".autopilot" / "note.txt").exists() and (self.repo / "scratch.log").exists())
        dec = [r for r in self.rows() if r["event"] == "decide"]
        self.assertEqual([(r["id"], r["verdict"], r["reason"]) for r in dec], [(tid, "aborted", "hướng sai")])
        self.assertEqual(sorted(dec[0]["candidate_files"]), ["src/hot.py", "src/new.py", "src/notes.txt"])
        st = self.tstate()
        self.assertEqual(
            (st["phase"], st["verdict"], st["stash"]), ("closed", "aborted", self.git("rev-parse", "refs/stash"))
        )
        self.assertIn("không có lần thử mở", self.refused("abort", "--reason", "x"))

    def test_abort_clean_tree_and_guards(self) -> None:
        """Không có candidate → đóng, không stash; lý do rỗng, HEAD ≠ start_head, khoá bận → exit 2."""
        self.started()
        self.assertIn("--reason rỗng", self.refused("abort", "--reason", " "))
        with xt._trial_hold(self.repo):
            self.assertIn("đang chạy", self.refused("abort", "--reason", "chen"))
        self.git("commit", "-q", "--allow-empty", "-m", "lén")
        self.assertIn("HEAD ≠ start_head", self.refused("abort", "--reason", "x"))
        self.git("reset", "-q", "--soft", "HEAD~1")
        self.assertIn("0 file thu hồi", self.ok("abort", "--reason", "x"))
        self.assertIsNone(self.tstate()["stash"])

    def test_abort_not_back_to_fp_is_exit_4_then_no_duplicate_decide(self) -> None:
        """Thu hồi không đưa vân tay về lúc start → exit 4, pha `decided`, in SHA stash; `abort` lại không ghi `decide`
        trùng; khi về được thì `closed`."""
        tid = self.started()
        self.put("src/hot.py", HOT + "# sửa\n")
        with unittest.mock.patch.object(xt, "tree_fingerprint", return_value="lệch"):
            rc, out, err = self.tr("abort", "--reason", "x")
        self.assertEqual(rc, 4, out + err)
        self.assertIn(self.git("rev-parse", "refs/stash"), err)
        self.assertEqual(self.tstate()["phase"], "decided")
        self.assertIn("perf trial finish --resume", self.ok("status"))
        with unittest.mock.patch.object(xt, "tree_fingerprint", return_value="lệch"):
            rc, out, err = self.tr("abort", "--reason", "y")
        self.assertEqual(rc, 4, out + err)
        self.assertIn("stash (không tạo)", err)
        self.ok("abort", "--reason", "z")
        self.assertEqual([r["id"] for r in self.rows() if r["event"] == "decide"], [tid])
        self.assertEqual(self.tstate()["phase"], "closed")

    def test_stash_failure_warns_and_returns_none(self) -> None:
        self.put("src/hot.py", HOT + "# sửa\n")
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            sha = xt._trial_stash(self.repo, "PT-0001", ["src/hot.py", "không-có.txt"])
        self.assertIn("git stash push exit 1", err.getvalue())
        # git 2.53: exit 1 nhưng VẪN tạo mục stash (như spike V1) — trả SHA để `abort` in ra khi vân tay lệch (exit 4)
        self.assertEqual(sha, self.git("rev-parse", "refs/stash"))
        self.assertIsNone(xt._trial_stash(self.repo, "PT-0002", ["không-có.txt"]))

    def test_hold_without_fcntl(self) -> None:
        with (
            unittest.mock.patch.object(xt, "_fcntl", return_value=None),
            self.assertRaisesRegex(xt.TrialRefused, "fcntl"),
        ):
            with xt._trial_hold(self.repo):
                pass


class TrialLogTest(TrialCase):
    def test_log_builds_block_and_anchors_tree(self) -> None:
        """`log` thay khối của vòng (giữ chữ người), nối sự kiện `log` với cây = HEAD + PERF-LOG mới; `--check` 0 rồi 1
        khi sổ có dòng mới; chạy lại khi PERF-LOG đã sửa (chưa commit) vẫn được."""
        tid = self.started()
        self.ok("abort", "--reason", "thử | một")
        self.ok("log")
        log = (self.repo / xt.PERF_TRIAL_LOG_MD).read_text(encoding="utf-8")
        self.assertTrue(log.startswith("# PERF-LOG\n\nGhi chú của người.\n\n<!-- xt-perf-trial "))
        self.assertIn(
            f"| {tid} | aborted | src/hot.py | bỏ vòng thừa trong cost | primary > -5% | thử \\| một | 0 |", log
        )
        self.ok("log")  # PERF-LOG bẩn của chính `log` không chặn
        self.git("commit", "-q", "-am", "PERF-LOG")
        anchors = [r["tree"] for r in self.rows() if r["event"] == "log"]
        self.assertEqual(anchors[-1], self.git("rev-parse", "HEAD^{tree}"))
        self.assertIn("khớp", self.ok("log", "--check"))
        self.started()
        self.ok("abort", "--reason", "hai")
        rc, out, _ = self.tr("log", "--check")
        self.assertEqual((rc, "lệch" in out), (1, True))

    def test_log_refusals(self) -> None:
        """`log` từ chối khi: lần thử mở, cây bẩn ngoài PERF-LOG, HEAD lệch cây neo (ngoài PERF-LOG); `--check` khi chưa
        có file → 1."""
        (self.repo / xt.PERF_TRIAL_LOG_MD).unlink()
        self.git("commit", "-q", "-am", "bỏ PERF-LOG")
        self.assertEqual(self.tr("log", "--check")[0], 1)
        self.git("reset", "-q", "--hard", self.base)
        self.started()
        self.assertIn("đang mở", self.refused("log"))
        self.ok("abort", "--reason", "x")
        self.put("src/x.py", "1\n")
        self.assertIn("cây bẩn", self.refused("log"))
        (self.repo / "src" / "x.py").unlink()
        self.put("src/other.py", "EXTRA = 1\n")
        self.git("commit", "-q", "-am", "lạ")
        self.assertIn("HEAD^{tree} ≠ cây", self.refused("log"))

    def test_log_creates_missing_file(self) -> None:
        self.republish({}, gone=("docs",))
        self.ok("log")
        self.assertTrue(
            (self.repo / xt.PERF_TRIAL_LOG_MD).read_text(encoding="utf-8").startswith("<!-- xt-perf-trial ")
        )

    def test_index_tree_error(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "read-tree"):
            xt.trial_index_tree(self.repo, "không-có", [])
        self.assertEqual(xt.trial_index_tree(self.repo, "HEAD", []), self.git("rev-parse", "HEAD^{tree}"))


class TrialReadTest(TrialCase):
    def test_broken_state_or_ledger_refused(self) -> None:
        auto = self.repo / ".autopilot"
        auto.mkdir()
        for text in ("[]", '{"phase": "lạ", "id": "PT-0001"}', '{"phase": "closed", "id": "X"}'):
            (auto / xt.PERF_TRIAL_FILE).write_text(text, encoding="utf-8")
            with self.subTest(text):
                self.assertIn("perf-trial.json hỏng", self.refused("start", "--hotspot", "src/hot.py", *TRIAL_ARGS))
        (auto / xt.PERF_TRIAL_FILE).unlink()
        (auto / xt.PERF_TRIALS_LOG).write_text('{"schema": 1, "event": "log", "base_sha": "b", "tree": "t"}', "utf-8")
        self.assertIn("hỏng ở dòng 1", self.refused("status"))

    def test_status_without_trial_text(self) -> None:
        out = self.ok("status")
        self.assertIn("budget 0/20", out)
        self.assertIn("kế: `perf trial start`\n", out)
        self.assertNotIn("bỏ:", out)


class TrialPrepareTest(TrialCase):
    """T-3702: ba cây dựng từ object (`clone --shared`), `setup` allowlist, kiểm trỏ đúng cây, dọn."""

    def prepare(self, cfg: dict[str, Any], code: int = 0) -> str:
        """Gốc mới với cấu hình `cfg` (lần thử mở trước đó bị `abort`), `start`, `prepare` phải exit `code`."""
        if (self.repo / ".autopilot" / xt.PERF_TRIAL_FILE).exists() and self.tstate()["phase"] != "closed":
            self.ok("abort", "--reason", "đổi cấu hình")
        self.republish({"perf/trial.json": json.dumps(cfg)})
        self.started()
        rc, out, err = self.tr("prepare")
        self.assertEqual(rc, code, out + err)
        return out + err

    def test_three_trees_env_and_cleanup(self) -> None:
        """`setup` chạy ở ba cây (gốc, `start_head`, candidate) với `TMPDIR` riêng, `PATH` = bin cây + `env.path`, biến
        `env.pass`; thư mục tạm bị dọn (cả thư mục chỉ đọc); sổ không đổi; mục PATH ghi được → ⚠."""
        log, wd = self.ctl / "setup.log", self.ctl / "w"
        wd.mkdir()
        setup = (
            f'echo "$PWD|$TMPDIR|$PATH|${{XT_KEEP:-}}|$(cat src/hot.py | wc -l)" >> {log}; mkdir -p ro && chmod 555 ro'
        )
        cfg = trial_config(setup=setup, env={"path": f"/bin:{wd}", "pass": ["XT_KEEP"], "allow_prefix": ["/opt"]})
        self.republish({"perf/trial.json": json.dumps(cfg)})
        self.started()
        self.put("src/hot.py", HOT + "# a\n# b\n")
        before = self.ledger()
        with unittest.mock.patch.dict(os.environ, {"XT_KEEP": "1", "NODE_OPTIONS": "x"}):
            rc, out, err = self.tr("prepare")
        self.assertEqual((rc, self.ledger()), (0, before), out + err)
        lines = [ln.split("|") for ln in log.read_text(encoding="utf-8").splitlines()]
        self.assertEqual([Path(p).name for p, *_ in lines], ["base", "head", "cand"])
        n = HOT.count("\n")
        self.assertEqual([int(c) for *_, c in lines], [n, n, n + 2])
        for here, tmp, path, keep, _ in lines:
            self.assertEqual((tmp, keep), (here + ".tmp", "1"))
            self.assertEqual(path, f"{here}/.venv/bin:{here}/node_modules/.bin:/bin:{wd}")
            self.assertFalse(Path(here).exists())
        self.assertIn(f"⚠ PATH có {wd}", out)

    def test_symlink_pth_direct_url_and_file_dep_outside_refused(self) -> None:
        """`setup` để đường phân giải ra ngoài cây đo (symlink, `.pth`, `direct_url.json` editable, `file:`) → exit 2 nêu
        từng đường; FIFO tên `.pth` không bị mở; `allow_prefix` cho qua."""
        out_dir = self.ctl / "ngoài"
        out_dir.mkdir()
        url = json.dumps({"url": f"file://{out_dir}", "dir_info": {"editable": True}})
        pkg = json.dumps({"dependencies": {"a": f"file:{out_dir}", "b": "^1"}, "devDependencies": {"c": "link:./x"}})
        setup = (
            f"ln -s {out_dir} lnk && mkdir -p site/x.dist-info && echo '{out_dir}' > site/a.pth"
            f" && echo 'import os; p = \"{out_dir}\"' > site/b.pth && echo '# chú thích' > site/c.pth"
            f" && echo '{url}' > site/x.dist-info/direct_url.json && echo '{pkg}' > package.json && mkfifo site/f.pth"
        )
        text = self.prepare(trial_config(setup=setup), code=2)
        for rel in ("lnk", "site/a.pth", "site/b.pth", "site/x.dist-info/direct_url.json", "package.json"):
            self.assertIn(f"cand: {rel} → {out_dir}", text)
        self.assertNotIn("c.pth", text)
        self.assertNotIn("✗ cand:", self.prepare(trial_config(setup=setup, env={"allow_prefix": [str(self.ctl)]})))

    def test_probe_and_venv_interpreter(self) -> None:
        """`probe` in đường trong cây → qua; đường ngoài cây hoặc probe lỗi → exit 2; interpreter cây = `.venv/bin/python`."""
        probe = "python3 -c 'import os; print(os.path.abspath(\"src/hot.py\"))'"
        self.prepare(trial_config(setup="python3 -m venv --without-pip .venv", probe=probe))
        self.assertIn("probe /etc/hostname (ngoài cây đo)", self.prepare(trial_config(probe="echo /etc/hostname"), 2))
        self.assertIn("probe exit 3: lỗi", self.prepare(trial_config(probe="echo lỗi >&2; exit 3"), 2))

    def test_setup_failure_and_dirty_submodule(self) -> None:
        self.assertIn("base: setup exit 7: hỏng", self.prepare(trial_config(setup="echo hỏng; exit 7"), 2))
        self.ok("abort", "--reason", "x")
        self.republish({"perf/trial.json": json.dumps(trial_config())})
        sub = self.tmp / "sub"
        self.run_git(self.tmp, "init", "-q", "-b", "main", str(sub))
        (sub / "f.txt").write_text("a\n", encoding="utf-8")
        self.run_git(sub, "add", "f.txt")
        self.run_git(sub, "commit", "-q", "-m", "f")
        self.run_git(self.tmp / "maint", "submodule", "add", "-q", str(sub), "vendor/sub")
        self.republish({})
        self.run_git(self.repo, "submodule", "update", "--init", "-q")
        self.started()
        (self.repo / "vendor" / "sub" / "f.txt").write_text("b\n", encoding="utf-8")
        rc, out, err = self.tr("prepare")
        self.assertEqual(rc, 2, out + err)
        self.assertIn("cand: vendor/sub (submodule: HEAD ≠ gitlink", out)

    def test_no_open_trial_refused(self) -> None:
        self.assertIn("không có lần thử mở", self.refused("prepare"))


class TrialTreeUnitTest(TrialCase):
    def test_tree_build_failures(self) -> None:
        work = self.tmp / "w"
        work.mkdir()
        with self.assertRaisesRegex(xt.TrialRefused, "không dựng được cây x \\(ffffffffffff\\)"):
            xt._trial_tree(self.repo, work, "x", "f" * 40, "t")
        with self.assertRaisesRegex(xt.TrialRefused, "≠ cây mong đợi"):
            xt._trial_tree(self.repo, work, "y", self.base, "0" * 40)

    def test_candidate_problems_compare_agent_tree(self) -> None:
        """Cây candidate khác cây agent (file đổi sau khi dựng, file thêm, symlink) → vấn đề; không file → không gì."""
        self.started()
        self.put("src/hot.py", HOT + "# a\n")
        (self.repo / "src" / "l").symlink_to("hot.py")
        files = xt.trial_dirty(self.repo)
        with xt.trial_trees(self.repo, self.tstate(), files) as trees:
            cand = trees[2]
            self.assertEqual(xt.trial_candidate_problems(self.repo, cand, files), [])
            self.assertEqual(xt.trial_candidate_problems(self.repo, cand, []), [])
            self.put("src/hot.py", HOT + "# b\n")
            (self.repo / "src" / "l").unlink()
            (self.repo / "src" / "l").symlink_to("other.py")
            (self.repo / "src" / "d").mkdir()
            got = xt.trial_candidate_problems(self.repo, cand, [*files, "src/d"])
        self.assertEqual(got, [f"cand: {p} khác cây agent" for p in ("src/hot.py", "src/l", "src/d")])

    def test_scan_digest_and_run(self) -> None:
        root = self.tmp / "t"
        (root / ".git").mkdir(parents=True)
        (root / ".git" / "x").write_text("bỏ qua\n", encoding="utf-8")
        (root / "a" / "__pycache__").mkdir(parents=True)
        (root / "a" / "__pycache__" / "m.pyc").write_bytes(b"x")
        (root / "big").write_bytes(b"0" * (xt.PERF_TRIAL_HASH_MAX + 1))
        (root / "f").write_text("f\n", encoding="utf-8")
        (root / "ld").symlink_to("a")
        tree = xt.TrialTree("t", "c", root, self.tmp)
        files, bad = xt.trial_scan(tree, [str(root)], list(xt.PERF_TRIAL_SCRATCH))
        self.assertEqual(sorted(files), ["a/__pycache__/m.pyc", "big", "f", "ld"])
        self.assertEqual([files[k][3] for k in ("a/__pycache__/m.pyc", "big", "ld")], [None, None, "->a"])
        self.assertEqual(files["f"][3], xt.hashlib.sha256(b"f\n").hexdigest())
        self.assertEqual(bad, [])
        self.assertEqual(xt.trial_run("sleep 5", root, {"PATH": "/bin:/usr/bin"}, 0.2), (124, "", "quá 0.2 s"))
        self.assertEqual(xt._trial_refs(self._write("x.json", "[]")), [])
        cfg = trial_config(env={"path": str(self.tmp), "allow_prefix": ["/opt/x"]})
        self.assertEqual(xt._trial_allowed(tree, cfg, {"PATH": str(self.tmp)}), [str(root), "/opt/x"])
        self.assertEqual(xt._trial_refs(self._write("direct_url.json", '{"url": "file:///a"}')), [])

    def _write(self, name: str, text: str) -> Path:
        p = self.tmp / name
        p.write_text(text, encoding="utf-8")
        return p

    def test_env_config_problems(self) -> None:
        cases = {
            '"env" = {': [{"x": 1}, {"path": 1}, {"pass": "A"}, {"pass": [""]}, {"allow_prefix": [1]}],
            "đường tuyệt đối": [{"allow_prefix": ["rel"]}],
        }
        for want, envs in cases.items():
            for env in envs:
                with self.subTest(env):
                    self.assertIn(want, str(xt.trial_config_problem(trial_config(env=env))))
        self.assertIn('"timeout" phải > 0', str(xt.trial_config_problem(trial_config(timeout=0))))
        self.assertIsNone(
            xt.trial_config_problem(trial_config(env={"path": "/bin", "pass": ["A"], "allow_prefix": ["/o"]}))
        )


class TrialReview442Test(TrialCase):
    """Review #442 (D-366): gốc vòng từ đầu nhánh máy chủ thật, cấu hình/môi trường của phiên không lái được git hay
    lệnh đo, quét/dọn không bỏ sót vì quyền, cây đo cô lập. Mỗi ca tái hiện một đường của bộ tái hiện review."""

    def fake_server(self) -> Path:
        """Máy chủ giả agent kiểm soát: `main` = commit nới cấu hình + sửa bộ đo (nhánh `evil`); cây agent về `opt`."""
        self.git("checkout", "-q", "-b", "evil")
        self.put("perf/trial.json", json.dumps(trial_config(locked=[], budget=999)))
        self.put("bench.py", "print(1)\n")
        self.git("commit", "-q", "-am", "nới cấu hình + bộ đo")
        fake = self.tmp / "fake.git"
        self.run_git(self.tmp, "init", "-q", "--bare", "-b", "main", str(fake))
        self.git("push", "-q", str(fake), "evil:main")
        self.git("checkout", "-q", "opt")
        return fake

    def prepared(self, cfg: dict[str, Any], tmp: Path | None = None) -> tuple[int, str]:
        """Gốc mới với `cfg`, `start`, `prepare` (thư mục tạm của tiến trình = `tmp` nếu có): (exit, out + err)."""
        self.republish({"perf/trial.json": json.dumps(cfg)})
        self.started()
        with unittest.mock.patch.object(xt.tempfile, "tempdir", str(tmp) if tmp else xt.tempfile.gettempdir()):
            rc, out, err = self.tr("prepare")
        return rc, out + err

    def test_url_pinned_after_first_start(self) -> None:
        """🔴 AUD-SEC-523: URL origin ghi ở dòng `start`; đổi sang máy chủ giả sau đó (`set-url`) → exit 2 trước khi hỏi
        máy chủ hay chạy công cụ gốc."""
        self.started()
        self.ok("abort", "--reason", "x")
        self.assertEqual(self.rows()[0]["origin_url"], str(self.origin))
        self.git("remote", "set-url", "origin", str(self.fake_server()))
        self.assertIn("URL origin đổi", self.refused("status"))

    def test_insteadof_refused_and_session_git_config_ignored(self) -> None:
        """🔴 AUD-SEC-523: `url.<giả>.insteadOf <URL origin>` qua `GIT_CONFIG_*` của phiên bị bỏ (allowlist) — gốc vẫn là
        đầu nhánh máy chủ thật; đặt cục bộ → exit 2; thiếu URL origin → exit 2."""
        fake = self.fake_server()
        env = {
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": f"url.{fake}.insteadOf",
            "GIT_CONFIG_VALUE_0": str(self.origin),
        }
        with unittest.mock.patch.dict(os.environ, env):
            self.assertEqual(self.ctx().base_sha, self.base)
        self.git("config", f"url.{fake}.insteadOf", str(self.origin))
        self.assertIn("viết lại URL origin", self.refused("status"))
        self.git("config", "--unset", f"url.{fake}.insteadOf")
        self.git("config", "--unset", "remote.origin.url")
        self.assertIn("remote `origin` chưa có URL", self.refused("status"))

    def test_downgraded_base_refused(self) -> None:
        """🟠 AUD-SEC-524: nhánh tách từ tổ tiên cũ của `main` (cấu hình cũ) → gốc vẫn = đầu `main` máy chủ; `start` → 2."""
        tip = self.maintain({"perf/trial.json": json.dumps(trial_config(budget=2))})
        self.assertEqual(self.ctx().base_sha, tip)
        self.assertIn("gộp nhánh mặc định trước", self.refused("start", "--hotspot", "src/hot.py", *TRIAL_ARGS))

    def test_submodule_shortcut_hidden_by_config_refused(self) -> None:
        """🟠 AUD-SEC-525: commit lạ đổi gitlink (đường tắt trong submodule) + `diff.ignoreSubmodules=all` → vẫn exit 2."""
        sub = self.tmp / "sub"
        self.run_git(self.tmp, "init", "-q", "-b", "main", str(sub))
        (sub / "lib.py").write_text("X = 1\n", encoding="utf-8")
        self.run_git(sub, "add", "lib.py")
        self.run_git(sub, "commit", "-q", "-m", "sub")
        self.republish({"src/x.txt": "1\n"})
        self.run_git(self.tmp / "maint", "submodule", "add", "-q", str(sub), "vendor/sub")
        self.republish({})
        self.run_git(self.repo, "submodule", "update", "--init", "-q")
        (self.repo / "vendor" / "sub" / "lib.py").write_text("X = 0  # đường tắt\n", encoding="utf-8")
        self.run_git(self.repo / "vendor" / "sub", "commit", "-q", "-am", "đường tắt")
        self.git("add", "vendor/sub")
        self.git("commit", "-q", "-m", "bump sub")
        self.git("config", "diff.ignoreSubmodules", "all")
        self.assertIn("HEAD^{tree} ≠ cây", self.refused("start", "--hotspot", "src/hot.py", *TRIAL_ARGS))

    def test_home_from_passwd_and_no_user_site(self) -> None:
        """🟠 AUD-SEC-526: HOME giả của phiên (mang `usercustomize.py`) không tới `setup`: HOME = passwd, PYTHONNOUSERSITE=1;
        uid không có trong passwd → exit 2."""
        log = self.ctl / "home.log"
        with unittest.mock.patch.dict(os.environ, {"HOME": str(self.tmp / "giả")}):
            rc, out = self.prepared(trial_config(setup=f'echo "$HOME|${{PYTHONNOUSERSITE:-}}" >> {log}'))
        self.assertEqual(rc, 0, out)
        home = pwd.getpwuid(os.getuid()).pw_dir
        self.assertEqual(log.read_text(encoding="utf-8").splitlines(), [f"{home}|1"] * 3)
        with unittest.mock.patch("pwd.getpwuid", side_effect=KeyError(0)):
            self.assertIn("không có trong passwd", self.refused("status"))

    def test_unreadable_dir_refused_and_trees_cleaned(self) -> None:
        """🟠 AUD-SEC-527: `setup` để thư mục `000` (lồng nhau) chứa symlink ra ngoài → exit 2 "không đọc được" thay vì bỏ
        qua; mọi thư mục tạm được dọn."""
        tmp = self.tmp / "tmpdir"
        tmp.mkdir()
        setup = f"mkdir -p d/e && ln -s {self.ctl} d/e/l && chmod 000 d/e && chmod 000 d"
        rc, out = self.prepared(trial_config(setup=setup), tmp)
        self.assertEqual(rc, 2, out)
        self.assertIn("không đọc được", out)
        self.assertEqual(list(tmp.iterdir()), [])

    def test_trees_isolated_from_agent_repo_and_each_other(self) -> None:
        """🟢 AUD-SEC-528: cây đo không có remote `origin` (trỏ repo agent), không thấy cây khác qua `../`."""
        log = self.ctl / "iso.log"
        setup = "echo \"$(git remote | tr '\\n' ,)|$(ls -A .. | tr '\\n' ,)\" >> " + str(log)
        rc, out = self.prepared(trial_config(setup=setup))
        self.assertEqual(rc, 0, out)
        want = [f"|{n},{n}.tmp," for n in ("base", "head", "cand")]
        self.assertEqual(log.read_text(encoding="utf-8").splitlines(), want)

    def test_tmpdir_inside_agent_tree_refused(self) -> None:
        """🟢 AUD-SEC-528: TMPDIR trong cây agent → exit 2, không dựng cây nào ở đó."""
        inner = self.repo / ".venv" / "tmp"
        inner.mkdir(parents=True)
        rc, out = self.prepared(trial_config(budget=19), inner)
        self.assertEqual(rc, 2, out)
        self.assertIn("nằm trong cây agent", out)
        self.assertEqual(list(inner.iterdir()), [])

    def test_log_marker_in_reason_escaped(self) -> None:
        """🟢 AUD-SEC-528: mốc đóng PERF-LOG trong `--reason` không chẻ khối — dựng lại hai lần ra cùng nội dung."""
        sha = "b" * 40
        ctx = xt.TrialCtx(sha, "refs/heads/main", TOOL, "t", trial_config(), "c", [])
        rows = [
            {"event": "decide", "id": "PT-0001", "base_sha": sha, "hotspot": ["a"], "verdict": "aborted"}
            | {"reason": f"thử {xt.PERF_TRIAL_LOG_END} <!-- xt-perf-trial {sha} --> xong"}
        ]
        v1 = xt.trial_log_merge("# PERF-LOG\n", xt.trial_log_block(rows, ctx), sha)
        self.assertEqual(xt.trial_log_merge(v1, xt.trial_log_block(rows, ctx), sha), v1)
        self.assertIn("&lt;!-- /xt-perf-trial -->", v1)

    def test_setup_py_and_requirements_locked(self) -> None:
        """AUD-SEC-529: khoá mặc định gồm `setup.py`, `requirements*.txt` ở mọi độ sâu."""
        ctx = xt.TrialCtx("b", "r", TOOL, "t", trial_config(), "c", [])
        for path in ("setup.py", "pkg/setup.py", "requirements.txt", "a/requirements-dev.txt"):
            with self.subTest(path):
                self.assertTrue(ctx.locked(path))

    def test_rmtree_nested_unreadable_dirs_and_symlink(self) -> None:
        """Dọn thư mục `000` lồng nhau; symlink tới thư mục ngoài không bị đổi quyền theo."""
        out_dir = self.tmp / "ngoài"
        out_dir.mkdir(mode=0o500)
        root = self.tmp / "w"
        (root / "a" / "b").mkdir(parents=True)
        (root / "a" / "b" / "f").write_text("x", encoding="utf-8")
        (root / "a" / "lnk").symlink_to(out_dir)
        (root / "a" / "b").chmod(0)
        (root / "a").chmod(0)
        xt._trial_rmtree(root)
        self.assertFalse(root.exists())
        self.assertEqual(out_dir.stat().st_mode & 0o777, 0o500)
        out_dir.chmod(0o700)


class TrialFinishTest(TrialCase):
    """T-3703: `finish` lõi (ADR-0071 §4) — kiểm/đóng băng, đo xen kẽ, kiểm cây sau lượt, tương đương, quyết, giữ/thu
    hồi, dòng `decide`. Ca luồng FLOW-20/28/29/33/34/41 ở `tests.test_flow`; đây là các nhánh còn lại."""

    def finish(self, *args: str) -> tuple[int, dict[str, Any], str]:
        """`finish` → (exit, dòng `decide` cuối, out + err)."""
        rc, out, err = self.tr("finish", *args)
        dec = [r for r in self.rows() if r["event"] == "decide"]
        return rc, dec[-1] if dec else {}, out + err

    def regrounded(self, **over: Any) -> None:
        self.republish({"perf/trial.json": json.dumps(trial_config(**over))})

    def test_keep_json_records_interleaved_samples(self) -> None:
        """Giữ (exit 0): `--json` in dòng `decide`; mẫu v2 của ba cây (`exact` 3 lần), hai phép so, held-out (hạt giống,
        input, tổng mỗi vòng) và falsifier không trúng, ⚠ PATH; pha `closed`, `kept_tree` = `candidate_tree`; candidate
        còn trong cây."""
        wd = self.ctl / "w"
        wd.mkdir()
        self.regrounded(env={"path": f"/usr/bin:/bin:{wd}"})
        self.started("src/hot.py", "src/other.py")
        self.put("src/other.py", "EXTRA = 0\n")
        rc, out, _ = self.tr("finish", "--json")
        self.assertEqual(rc, 0, out)
        row = json.loads(out)
        self.assertEqual((row["verdict"], row["rounds"], row["candidate_files"]), ("kept", 1, ["src/other.py"]))
        prim = row["measures"]["primary"]
        self.assertEqual([prim[t]["samples"] for t in ("base", "head", "cand")], [[3500.0] * 3] * 2 + [[3000.0] * 3])
        self.assertEqual((prim["base"]["schema"], prim["cand"]["kind"]), (2, "exact"))
        self.assertEqual([prim["compare"][t]["verdict"] for t in ("base", "head")], ["improved"] * 2)
        held = row["heldout"]
        self.assertEqual((len(held["seed"]), len(held["inputs"]), row["falsifier_hit"]), (16, 5, False))
        self.assertEqual([held["compare"][t]["verdict"] for t in ("base", "head")], ["improved"] * 2)
        self.assertEqual(set(held["per_input"].values()), {"improved"})  # EXTRA −500 ≥ 3,2 % ở mọi input (HELD_RANGE)
        self.assertEqual(row["warnings"], [f"PATH có {wd} — uid này ghi được"])
        st = self.tstate()
        self.assertEqual((st["phase"], st["kept_tree"]), ("closed", row["candidate_tree"]))
        self.assertIn("EXTRA = 0", (self.repo / "src" / "other.py").read_text(encoding="utf-8"))

    def test_empty_candidate_closes_without_stash(self) -> None:
        tid = self.started()
        rc, row, out = self.finish()
        self.assertEqual((rc, row["id"], row["verdict"]), (1, tid, "empty"), out)
        self.assertEqual((self.tstate()["phase"], self.tstate()["stash"]), ("closed", None))

    def test_refusals_before_measuring(self) -> None:
        """Pha khác `started` → `--resume`; gốc/cấu hình lệch lúc start, dòng `start` lệch state, `start_head^{tree}` ≠
        cây giữ gần nhất → exit 2, sổ không đổi."""
        self.started()
        self.put("src/hot.py", HOT + "# a\n")
        edits = {
            "config_sha": lambda st: {**st, "config_sha": "x"},
            "dòng start": lambda st: {**st, "hypothesis": "khác"},
        }
        for want, fn in edits.items():
            with self.subTest(want):
                old = self.tstate()
                xt.trial_update(self.repo, lambda st, fn=fn: (fn(st), None))
                self.assertIn(want, self.refused("finish"))
                xt.trial_update(self.repo, lambda st, old=old: ({**old, "rev": st["rev"]}, None))
        row = {"event": "decide", "id": "PT-0009", "base_sha": self.base, "hotspot": ["a"], "verdict": "kept"}
        self.append_row({**row, "candidate_tree": "f" * 40, "candidate_files": ["a"]})
        self.assertIn("start_head^{tree} ≠ cây giữ", self.refused("finish"))
        (self.repo / ".autopilot" / xt.PERF_TRIALS_LOG).write_text(
            "".join(json.dumps(r) + "\n" for r in self.rows()[:-1]), encoding="utf-8"
        )
        xt.trial_update(self.repo, lambda st: ({**st, "phase": "measuring"}, None))
        self.assertIn("finish --resume", self.refused("finish"))

    def test_same_candidate_twice_refused(self) -> None:
        self.started()
        self.put("src/hot.py", HOT + "# a\n")
        self.assertEqual(self.finish()[0], 1)
        self.started()
        self.put("src/hot.py", HOT + "# a\n")
        self.assertIn("đã thử ở PT-0001", self.refused("finish"))

    def test_broken_inequivalent_and_tampered_by_measure(self) -> None:
        """Lệnh đo lỗi ở candidate → `broken`; `equiv` đỏ ở candidate → `inequivalent`; candidate ghi file vào cây đo của
        nó lúc đo → `tampered`; mỗi lần thu hồi về vân tay lúc start (exit 1)."""
        cases = {
            "broken": HOT + "raise SystemExit(3)\n",
            "inequivalent": HOT.replace("K = 3", "K = 2").replace("total += i", "total += 2 * i"),
            "tampered": HOT.replace("K = 3", "K = 2") + "open('leak.txt', 'w').close()\n",
        }
        for verdict, text in cases.items():
            with self.subTest(verdict):
                fp0 = xt.tree_fingerprint(self.repo)
                self.started()
                self.put("src/hot.py", text)
                rc, row, out = self.finish()
                self.assertEqual((rc, row["verdict"], xt.tree_fingerprint(self.repo)), (1, verdict, fp0), out)

    def test_base_command_or_equiv_or_setup_broken_is_exit_2(self) -> None:
        for over in ({"metric": {"cmd": "exit 5", "kind": "exact"}}, {"equiv": "exit 1"}, {"setup": "exit 7"}):
            with self.subTest(over):
                if (self.repo / ".autopilot" / xt.PERF_TRIAL_FILE).exists():
                    self.ok("abort", "--reason", "đổi cấu hình")
                self.regrounded(**over)
                self.started()
                self.put("src/hot.py", HOT.replace("K = 3", "K = 2"))
                self.assertEqual(self.tr("finish")[0], 2)
                self.assertEqual([r for r in self.rows() if r["event"] == "decide" and r["verdict"] != "aborted"], [])

    def test_unbuildable_and_tree_changed_while_measuring(self) -> None:
        self.started()
        self.put("src/hot.py", HOT.replace("K = 3", "K = 2"))
        with unittest.mock.patch.object(xt, "trial_candidate_problems", return_value=["cand: x khác cây agent"]):
            self.assertEqual(self.finish()[:2][1]["verdict"], "unbuildable")
        real, calls = xt.tree_fingerprint, []

        def fp(base: Path, env: dict[str, str] | None = None) -> str | None:
            calls.append(1)
            return "đổi" if len(calls) == 2 else real(base, env)

        self.started()
        self.put("src/hot.py", HOT.replace("K = 3", "K = 2") + "# b\n")
        with unittest.mock.patch.object(xt, "tree_fingerprint", fp):
            rc, row, out = self.finish()
        self.assertEqual((rc, row["verdict"]), (1, "incomplete"), out)

    def test_sample_compare_units(self) -> None:
        root = self.tmp / "t"
        root.mkdir()
        run = xt.TrialRun(xt.TrialTree("cand", "c", root, self.tmp), {"PATH": "/usr/bin:/bin"}, {})
        secs, text = xt.trial_sample(run, {"cmd": "echo out", "kind": "wall"}, 10)
        self.assertEqual((secs > 0, text), (True, "out\n"))
        self.assertEqual(xt.trial_sample(run, {"cmd": "echo a  b 42", "kind": "exact"}, 10), (42.0, "a b"))
        for cmd in ("echo abc", "echo inf", "true"):
            with self.subTest(cmd), self.assertRaisesRegex(xt.TrialBroken, "không phải số hữu hạn"):
                xt.trial_sample(run, {"cmd": cmd, "kind": "exact"}, 10)
        got = xt.trial_compare({"base": [1, 1, 1], "head": [2, 1, 2], "cand": [1, 1, 1]}, {"kind": "exact"})
        self.assertEqual([got[t]["verdict"] for t in ("base", "head")], ["insufficient"] * 2)
        self.assertIn("lệch giữa các lần ở head", got["base"]["reason"])


class TrialSecondaryTest(TrialCase):
    """T-3704: chỉ số phụ (trần + mức lùi), `env.cmd_python`, ⚠ heuristic `perf guard` vào `decide`, `status --check`."""

    def test_secondary_ceiling_and_regress(self) -> None:
        """Trần ở phía tệ (`higher_is_better` → sàn); `exact` lùi quá `regress` theo số; `wall` chỉ khi `regressed`; mẫu
        `exact` lệch → lý do; trong trần và mức lùi → không lý do."""
        mem = {"name": "mem", "kind": "exact", "unit": "B"}
        fast = {"name": "qps", "kind": "exact", "higher_is_better": True}
        noise = [1.0 + i / 1000 for i in range(10)]

        def why(m: dict[str, Any], base: list[float], cand: list[float]) -> str:
            return xt.trial_secondary(m, {"base": base, "head": base, "cand": cand})[1]

        cases = [
            (mem | {"ceiling": 1000}, [100.0] * 3, [2000.0] * 3, "vượt trần 1000"),
            (fast | {"ceiling": 50}, [60.0] * 3, [40.0] * 3, "vượt trần 50"),
            (mem | {"regress": 5}, [100.0] * 3, [104.0] * 3, ""),
            (mem | {"regress": 3}, [100.0] * 3, [104.0] * 3, "mem so gốc: lùi +4.00% > regress 3%"),
            (fast, [100.0] * 3, [96.0] * 3, "qps so start_head: lùi +4.00% > regress 0%"),
            (mem, [100.0] * 3, [100.0, 101.0, 100.0], "thiếu mẫu"),
            ({"name": "t", "kind": "wall"}, noise, [x * 2 for x in noise], "t so gốc: lùi +"),
            ({"name": "t", "kind": "wall", "regress": 200}, noise, [x * 2 for x in noise], ""),
            ({"name": "t", "kind": "wall"}, noise, [x * 1.001 for x in noise], ""),
        ]
        for m, base, cand, want in cases:
            with self.subTest(m=m, cand=cand[:1]):
                got = why(m, base, cand)
                self.assertIn(want, got) if want else self.assertEqual(got, "")

    def test_cmd_python_and_guard_warnings_in_decide(self) -> None:
        """Chỉ cây candidate có `.venv` (do `setup`) → `env.cmd_python` khác giữa các cây (⚠); dòng thêm `lru_cache` →
        ⚠ `perf guard` trên diff `start_head` → candidate; vẫn giữ (⚠ không chặn)."""
        setup = "if grep -q 'K = 2' src/hot.py; then python3 -m venv --without-pip .venv; fi"
        self.republish({"perf/trial.json": json.dumps(trial_config(setup=setup))})
        self.started()
        self.put("src/hot.py", HOT.replace("K = 3", "K = 2") + "# functools.lru_cache để sau\n")
        rc, out, err = self.tr("finish", "--json")
        self.assertEqual(rc, 0, out + err)
        row = json.loads(out)
        pys = {t: row["measures"]["mem"][t]["env"]["cmd_python"] for t in ("base", "cand")}
        self.assertTrue(pys["cand"].startswith(".venv/bin/python 3."), pys)
        self.assertFalse(pys["base"].startswith(".venv"), pys)
        self.assertTrue(any(w.startswith("perf guard: src/hot.py: ") and "lru_cache" in w for w in row["warnings"]))
        self.assertTrue(any(w.startswith("interpreter lệnh đo khác giữa các cây") for w in row["warnings"]))

    def test_cmd_python_missing_or_broken(self) -> None:
        root = self.tmp / "t"
        (root / ".venv" / "bin").mkdir(parents=True)
        tree = xt.TrialTree("cand", "c", root, self.tmp)
        self.assertIsNone(xt.trial_cmd_python(tree, {"PATH": str(self.tmp / "không-có")}))
        (root / ".venv" / "bin" / "python").write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        (root / ".venv" / "bin" / "python").chmod(0o755)
        self.assertIsNone(xt.trial_cmd_python(tree, {"PATH": "/usr/bin:/bin"}))

    def test_status_check_codes(self) -> None:
        """Chưa có lần giữ → 1; lần thử mở → 1; lần giữ thiếu số → 1; lần giữ đạt `target` → 0 (`--json`); lần giữ gần
        nhất chưa đạt và hết `budget` → 3."""
        self.assertIn("chưa có lần giữ", self.refused("status", "--check", code=1))
        self.started()
        self.assertIn("đang mở", self.refused("status", "--check", code=1))
        self.ok("abort", "--reason", "x")
        row = {"event": "decide", "id": "PT-0002", "base_sha": self.base, "hotspot": ["src/hot.py"], "verdict": "kept"}
        row |= {"candidate_tree": self.git("rev-parse", "HEAD^{tree}"), "candidate_files": ["src/hot.py"]}
        self.append_row(row)
        self.assertIn("primary None", self.refused("status", "--check", code=1))
        self.append_row(row | {"measures": {"primary": {"compare": {"base": {"change": -0.25}}}}})
        self.assertEqual(json.loads(self.ok("status", "--check", "--json"))["code"], 0)
        self.put("src/notes.txt", "khác\n")
        self.assertIn("cây bẩn ngoài .autopilot/: src/notes.txt", self.refused("status", "--check", code=1))
        self.git("commit", "-q", "-am", "commit lạ")
        self.assertIn("commit lạ sau lần giữ", self.refused("status", "--check", code=1))
        self.git("revert", "--no-edit", "HEAD")
        self.append_row(row | {"measures": {"primary": {"compare": {"base": {"change": -0.1}}}}})
        self.assertIn("primary -10.00%", self.refused("status", "--check", code=1))
        self.republish({"perf/trial.json": json.dumps(trial_config(budget=1))})
        self.started()
        self.ok("abort", "--reason", "y")
        self.assertIn("loop defer", self.refused("status", "--check", code=3))


def _held(base: float, head: float, cand: float, n: int = 3) -> dict[str, list[float]]:
    return {"base": [base] * n, "head": [head] * n, "cand": [cand] * n}


class TrialHeldoutTest(TrialCase):
    """T-3705: held-out (ADR-0071 §6 — hạt giống mỗi lượt, gộp + từng input, so `start_head` VÀ gốc) và falsifier (§7).
    Ca luồng FLOW-27/30/31 ở `tests.test_flow`; đây là các nhánh còn lại."""

    EXACT = {"kind": "exact", "higher_is_better": False}

    def judge(self, samples: dict[str, dict[str, list[float]]], outs: Any = None) -> str:
        same = {x: {"base": {""}, "cand": {""}} for x in samples}
        return xt.trial_heldout_judge(samples, outs or same, self.EXACT)[1]

    def test_heldout_compares_base_not_only_start_head(self) -> None:
        """D-363 (vế held-out của AUD-HAR-231): candidate `improved` so `start_head` nhưng KHÔNG so gốc (đường tắt/lùi đã
        nằm sẵn trong `start_head`) → lý do "so gốc"; chỉ so `start_head` thì đã giữ. Đối chứng: tốt hơn cả hai → ""."""
        samples = {"2500": _held(100, 200, 150), "7000": _held(100, 200, 150)}
        doc, why = xt.trial_heldout_judge(samples, {x: {"base": {""}, "cand": {""}} for x in samples}, self.EXACT)
        self.assertEqual([doc["compare"][t]["verdict"] for t in ("base", "head")], ["regressed", "improved"])
        self.assertTrue(why.startswith("held-out gộp so gốc: regressed"), why)
        self.assertNotIn("so start_head", why)
        self.assertEqual(doc["samples"], {"base": [200.0] * 3, "head": [400.0] * 3, "cand": [300.0] * 3})
        self.assertEqual(self.judge({"2500": _held(100, 100, 90), "7000": _held(100, 100, 90)}), "")

    def test_heldout_per_input_uneven_and_output(self) -> None:
        """Tổng `improved` nhưng một input `regressed` so `start_head` → lý do nêu input; mẫu `exact` lệch giữa các lần →
        `insufficient`; đầu ra candidate khác gốc → lý do; tối đa ba lý do."""
        lop = {"a": _held(100, 100, 10), "b": _held(100, 100, 110)}
        self.assertEqual(self.judge(lop), f"held-out input b so start_head: {self.report(100, 110)}")
        uneven = {"a": {"base": [9.0, 9.0, 9.0], "head": [9.0, 9.0, 9.0], "cand": [1.0, 2.0, 1.0]}}
        self.assertIn("held-out input a so start_head: ? thiếu mẫu", self.judge(uneven))
        outs = {"a": {"base": {"42"}, "cand": {"41"}}}
        self.assertEqual(self.judge({"a": _held(9, 9, 1)}, outs), "held-out input a: đầu ra candidate khác gốc")
        many = {x: _held(100, 100, 200) for x in "abcd"}
        self.assertEqual(self.judge(many).count("; "), 2)

    def report(self, head: float, cand: float) -> str:
        return xt._perf_report(xt.perf_compare([head] * 3, [cand] * 3, exact=True))

    def test_inputs_from_gen_with_seed_on_stdin(self) -> None:
        """`heldout.gen` đọc hạt giống từ stdin, input = dòng khác rỗng (bỏ trùng, giữ thứ tự); gen lỗi hay không ra
        input → TrialRefused(2) không lộ hạt giống."""
        root = self.tmp / "t"
        root.mkdir()
        run = xt.TrialRun(xt.TrialTree("base", "c", root, self.tmp), {"PATH": "/usr/bin:/bin"}, {})
        gen = {"gen": "read s; printf '%s\\n\\n b\\n%s\\n' $s $s", "cmd": "x {input}"}
        self.assertEqual(xt.trial_heldout_inputs(run, gen, "ab12", 10), ["ab12", "b"])
        for cmd in ("exit 3", "true"):
            with self.subTest(cmd), self.assertRaisesRegex(xt.TrialRefused, "cấu hình gốc hỏng") as cm:
                xt.trial_heldout_inputs(run, {"gen": cmd, "cmd": "x {input}"}, "bí-mật", 10)
            self.assertNotIn("bí-mật", str(cm.exception))

    def test_seed_not_on_disk_before_decide(self) -> None:
        """Hạt giống mới mỗi lượt, KHÔNG có trong state/sổ trong lúc đo (§6: agent không đọc trước được) — chỉ ở dòng
        `decide` sau khi đo."""
        real, seen = xt.trial_heldout_inputs, []

        def spy(run: Any, h: Any, seed: str, timeout: float) -> list[str]:
            seen.append((seed, self.ledger()))
            return list(real(run, h, seed, timeout))

        seeds = []
        for k in (2, 1):
            self.started()
            self.put("src/hot.py", HOT.replace("K = 3", f"K = {k}"))
            with unittest.mock.patch.object(xt, "trial_heldout_inputs", spy):
                rc, out, err = self.tr("finish")
            self.assertEqual(rc, 0, out + err)
            self.git("commit", "-q", "-am", f"giữ K = {k}")
            seed, ledger = seen[-1]
            self.assertFalse(any(seed.encode() in b for b in ledger if b), "hạt giống lộ trước khi đo xong")
            self.assertEqual(self.rows()[-1]["heldout"]["seed"], seed)
            seeds.append(seed)
        self.assertNotEqual(*seeds)

    def test_input_is_shell_quoted(self) -> None:
        """Input có ký tự shell (do `heldout.gen` in) vào `heldout.cmd` đã quote: không chạy lệnh chèn; số đo bằng nhau
        ở ba cây → held-out không `improved` → thu hồi (exit 1)."""
        gen = f"read s; echo '2000; touch {self.ctl}/pwned'"
        held = {"gen": gen, "cmd": "printf %s {input} | wc -c"}
        self.republish({"perf/trial.json": json.dumps(trial_config(heldout=held))})
        tid = self.started()
        self.put("src/hot.py", HOT.replace("K = 3", "K = 2"))
        rc, out, err = self.tr("finish")
        self.assertEqual(rc, 1, out + err)
        row = [r for r in self.rows() if r.get("id") == tid and r["event"] == "decide"][0]
        self.assertEqual(row["verdict"], "heldout")
        self.assertEqual(row["heldout"]["inputs"], [f"2000; touch {self.ctl}/pwned"])
        self.assertFalse((self.ctl / "pwned").exists())

    def test_no_heldout_warns_and_records_not_applicable(self) -> None:
        cfg = trial_config()
        del cfg["heldout"]
        self.republish({"perf/trial.json": json.dumps(cfg)})
        self.started()
        self.put("src/hot.py", HOT.replace("K = 3", "K = 2"))
        rc, out, err = self.tr("finish", "--json")
        self.assertEqual(rc, 0, out + err)
        row = json.loads(out)
        self.assertEqual(row["heldout"], xt.PERF_TRIAL_NO_HELDOUT)
        self.assertIn(f"held-out: {xt.PERF_TRIAL_NO_HELDOUT}", row["warnings"])

    def test_heldout_config_shape(self) -> None:
        bad = (
            {"gen": "g", "cmd": "c"},
            {"gen": "", "cmd": "c {input}"},
            {"gen": "g", "cmd": "c {input}", "seed": "1"},
            {"cmd": "c {input}"},
            {"gen": 1, "cmd": "c {input}"},
        )
        for h in bad:
            with self.subTest(h):
                self.assertIn('"heldout"', str(xt.trial_config_problem(trial_config(heldout=h))))

    def test_falsifier_units(self) -> None:
        """Trúng → lý do (thu hồi); không trúng → ""; chỉ số phụ theo tên; thiếu số hoặc biểu thức không đọc được → coi
        như trúng (chặt hơn)."""
        cfg = trial_config()
        measures = {"primary": {"compare": {"head": {"change": -0.3}}}, "mem": {"compare": {"head": {"change": 0.1}}}}
        cases = {
            "primary > -50%": "falsifier `primary > -50%` trúng: primary -30.00% so start_head",
            "primary > -5%": "",
            "mem >= 10%": "falsifier `mem >= 10%` trúng: mem +10.00% so start_head",
            "mem < 0%": "",
            "rss > 1%": "không đánh giá được",
        }
        for expr, want in cases.items():
            with self.subTest(expr):
                got = xt.trial_falsified(expr, cfg, measures)
                self.assertIn(want, got) if want else self.assertEqual(got, "")
        self.assertIn("coi như trúng", xt.trial_falsified("primary > 0%", cfg, {"primary": {"compare": {}}}))


class TrialResumeTest(TrialCase):
    """T-3706: `finish --resume` (ADR-0071 §9 — R1 một lần, rơi về R2), `finish --no-apply` (§2, Đường lùi), đồng thời.
    Ca luồng FLOW-21/34/35/36 (kill thật) ở `tests.test_flow`; đây dựng pha bằng hàm nội bộ cho từng nhánh."""

    def measuring(self, text: str) -> str:
        """Lần thử mở, candidate `text` đã đóng băng (pha `measuring`, `rounds` 1) như lượt `finish` chết giữa chừng."""
        tid = self.started()
        self.put("src/hot.py", text)
        ctx = self.ctx()
        xt.trial_freeze(self.repo, ctx, xt.trial_finish_check(self.repo, ctx), xt.trial_dirty(self.repo))
        self.assertEqual(self.tstate()["phase"], "measuring")
        return tid

    def decides(self, tid: str) -> list[dict[str, Any]]:
        return [r for r in self.rows() if r["event"] == "decide" and r["id"] == tid]

    def test_resume_needs_unfinished_round(self) -> None:
        self.started()
        self.assertIn("chạy `perf trial finish`", self.refused("finish", "--resume"))
        self.ok("abort", "--reason", "x")
        self.assertIn("không có lần thử mở", self.refused("finish", "--resume", "--no-apply"))

    def test_r1_measures_once_more_then_r2(self) -> None:
        """R1: pha `measuring`, cây = `candidate_fp`, `resumes` 0 → đo lại, `rounds` 2, `resumes` 1, giữ (exit 0), một dòng
        `decide`. R2: lượt dở thứ hai (đã resume một lần) → `incomplete`, thu hồi về `fp_start` (exit 1)."""
        tid = self.measuring(HOT.replace("K = 3", "K = 2"))
        rc, out, err = self.tr("finish", "--resume")
        self.assertEqual(rc, 0, out + err)
        self.assertEqual([(r["verdict"], r["rounds"]) for r in self.decides(tid)], [("kept", 2)])
        self.assertEqual((self.tstate()["resumes"], self.tstate()["phase"]), (1, "closed"))
        self.git("commit", "-q", "-am", "giữ")
        fp0 = xt.tree_fingerprint(self.repo)
        tid = self.measuring(HOT.replace("K = 3", "K = 1"))
        xt.trial_update(self.repo, lambda st: ({**st, "resumes": 1}, None))
        rc, out, err = self.tr("finish", "--resume")
        self.assertEqual(rc, 1, out + err)
        self.assertEqual([r["verdict"] for r in self.decides(tid)], ["incomplete"])
        self.assertIn("một lần", self.decides(tid)[0]["reason"])
        self.assertEqual(xt.tree_fingerprint(self.repo), fp0)

    def test_interrupt_during_resume_is_incomplete(self) -> None:
        """§9 + D-370: SIGTERM giữa lượt `--resume` (lần đo lại đã tiêu) → dòng `interrupt` rồi `decide incomplete`
        (`rounds` 2), thu hồi về `fp_start`, exit 1 — không về `started` để đo lại lần ba."""
        fp0 = xt.tree_fingerprint(self.repo)
        tid = self.measuring(HOT.replace("K = 3", "K = 2"))
        kill = unittest.mock.patch.object(
            xt, "trial_measure", side_effect=lambda *a: os.kill(os.getpid(), signal.SIGTERM)
        )
        with kill:
            rc, out, err = self.tr("finish", "--resume")
        self.assertEqual(rc, 1, out + err)
        self.assertEqual([(r["event"], r["rounds"]) for r in self.rows()[-2:-1]], [("interrupt", 2)])
        self.assertEqual([(r["verdict"], r["rounds"]) for r in self.decides(tid)], [("incomplete", 2)])
        self.assertEqual((self.tstate()["phase"], xt.tree_fingerprint(self.repo)), ("closed", fp0))

    def test_r2_tree_changed_reverts_current_files(self) -> None:
        """Cây đổi sau lượt dở (thêm file ngoài candidate đã đóng băng) → `incomplete`, thu hồi MỌI đường đang đổi (về
        `fp_start`), không đo."""
        fp0 = xt.tree_fingerprint(self.repo)
        tid = self.measuring(HOT.replace("K = 3", "K = 2"))
        self.put("src/extra.py", "Y = 1\n")
        with unittest.mock.patch.object(xt, "trial_judge", side_effect=AssertionError("không được đo")):
            rc, out, err = self.tr("finish", "--resume")
        self.assertEqual(rc, 1, out + err)
        self.assertEqual([r["verdict"] for r in self.decides(tid)], ["incomplete"])
        self.assertEqual((xt.tree_fingerprint(self.repo), (self.repo / "src" / "extra.py").exists()), (fp0, False))

    def test_no_apply_kept_then_resume_closes(self) -> None:
        """`--no-apply` giữ: exit 0, dòng `decide` ghi (tính lượt), pha `decided`, candidate còn; `--resume --no-apply` in
        lại, không ghi trùng; `--resume` đóng (`kept_tree`), vẫn một dòng `decide`."""
        tid = self.started()
        self.put("src/hot.py", HOT.replace("K = 3", "K = 2"))
        rc, out, err = self.tr("finish", "--no-apply")
        self.assertEqual(rc, 0, out + err)
        self.assertIn("giữ (chưa áp)", out)
        self.assertEqual((self.tstate()["phase"], len(self.decides(tid))), ("decided", 1))
        self.assertIn("finish --resume", self.refused("finish"))
        rc, out, err = self.tr("finish", "--resume", "--no-apply")
        self.assertEqual((rc, self.tstate()["phase"]), (0, "decided"), out + err)
        self.assertIn("không ghi `decide` trùng", err)
        rc, out, err = self.tr("finish", "--resume")
        self.assertEqual(rc, 0, out + err)
        st = self.tstate()
        self.assertEqual((st["phase"], st["kept_tree"], len(self.decides(tid))), ("closed", st["candidate_tree"], 1))
        self.assertIn("K = 2", (self.repo / "src" / "hot.py").read_text(encoding="utf-8"))

    def test_no_apply_revert_prints_command_then_resume_reverts(self) -> None:
        """`--no-apply` không giữ: exit 1, cây KHÔNG đổi (không stash), in lệnh `git stash push … -- <file>` đúng danh sách
        (đường có ký tự shell được quote); `--json`: stdout chỉ là dòng `decide`. `--resume` thu hồi (exit 1, `fp_start`)."""
        fp0 = xt.tree_fingerprint(self.repo)
        tid = self.started("src/hot.py", "src/a b.py")
        self.put("src/hot.py", HOT + "# chú thích\n")
        self.put("src/a b.py", "Z = 1\n")
        fp1 = xt.tree_fingerprint(self.repo)
        rc, out, err = self.tr("finish", "--no-apply", "--json")
        self.assertEqual(rc, 1, out + err)
        self.assertEqual(json.loads(out)["id"], tid)
        want = f"git stash push --include-untracked -m 'xt-perf-trial {tid}' -- src/hot.py 'src/a b.py'"
        self.assertIn(want, err)
        self.assertEqual((xt.tree_fingerprint(self.repo), self.git("stash", "list")), (fp1, ""))
        rc, out, err = self.tr("finish", "--resume")
        self.assertEqual(rc, 1, out + err)
        self.assertEqual((xt.tree_fingerprint(self.repo), len(self.decides(tid))), (fp0, 1))

    def test_no_apply_empty_candidate(self) -> None:
        self.started()
        rc, out, err = self.tr("finish", "--no-apply")
        self.assertEqual(rc, 1, out + err)
        self.assertIn("không có file để thu hồi", out)
        self.assertEqual(self.tstate()["phase"], "decided")

    def test_concurrent_resume_or_no_apply_refused(self) -> None:
        """Một `finish`/`abort` đang giữ `perf-trial.lock` → `finish --resume`, `finish --no-apply`, `abort` exit 2 ngay,
        sổ không đổi; nhả khoá thì `--resume` chạy được."""
        self.measuring(HOT.replace("K = 3", "K = 2"))
        with xt._trial_hold(self.repo):
            for args in (("finish", "--resume"), ("finish", "--resume", "--no-apply"), ("abort", "--reason", "x")):
                with self.subTest(args):
                    self.assertIn("đang chạy", self.refused(*args))
        self.assertEqual(self.tr("finish", "--resume")[0], 0)


class TrialReview443Test(TrialCase):
    """Review #443 (D-368): pathspec theo nghĩa đen, môi trường lệnh đo mới mỗi mẫu, bin của cây đo không do candidate
    đặt, ⚠ mã chạy lúc thoát, SIGTERM giữa lượt đo, thứ tự đo xen kẽ. Mỗi ca tái hiện một kịch bản của bộ tái hiện."""

    def stash_files(self) -> list[str]:
        """File chưa theo dõi trong mục stash mới nhất (commit cha thứ ba)."""
        return self.git("show", "--name-only", "--format=", "refs/stash^3").splitlines()

    def test_glob_named_candidate_does_not_sweep_ledger(self) -> None:
        """🟠 F2: candidate bỏ `.autopilot/` khỏi `.gitignore` và tạo file tên `*` → thu hồi (`finish` lẫn `abort`) chỉ
        stash đúng hai đường; sổ còn nguyên, lệnh kế đọc được sổ."""
        for cmd in (("finish",), ("abort", "--reason", "glob")):
            with self.subTest(cmd[0]):
                self.started()
                self.put(".gitignore", ".cache/\n.venv/\nnode_modules/\n__pycache__/\nscratch.log\n")
                self.put("*", "x\n")
                rc, out, err = self.tr(*cmd)
                self.assertEqual(rc, 1 if cmd[0] == "finish" else 0, out + err)
                self.assertEqual(self.stash_files(), ["*"])
                self.assertEqual(self.tstate()["phase"], "closed")
                self.assertEqual(self.rows()[-1]["event"], "decide")
                self.ok("status")

    def test_many_candidate_files_beyond_arg_max(self) -> None:
        """🟢 F7: danh sách file vượt ARG_MAX (≈ 2,3 MB tên) → index tạm, so cây candidate, stash vẫn chạy (pathspec
        qua stdin, không qua argv)."""
        d = self.repo / "vendor_pkg"
        d.mkdir()
        files = [f"vendor_pkg/{'m' * 200}_{i:05d}.py" for i in range(11000)]
        for f in files:
            (self.repo / f).write_bytes(b"")
        self.assertEqual(len(xt.trial_index_tree(self.repo, "HEAD", files)), 40)
        tree = xt.TrialTree("cand", "c", self.repo, self.tmp)
        self.assertEqual(xt.trial_candidate_problems(self.repo, tree, files), [])
        # Mục stash đủ mọi file; dọn cây làm việc thì chính git chuyển pathspec qua argv cho tiến trình con (`add`) —
        # có thể không xong: vân tay ≠ `fp_start` → exit 4 kèm SHA stash (giới hạn ghi ở ADR §4 bước 8).
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertIsNotNone(xt._trial_stash(self.repo, "PT-0001", files))
        self.assertEqual(len(self.stash_files()), len(files))

    def test_fresh_home_tmp_and_scratch_every_sample(self) -> None:
        """🟠 F3: lệnh đo đếm dấu vết lần chạy trước ở `HOME`, `XDG_CACHE_HOME`, `TMPDIR`, `src/__pycache__/` (khớp
        `scratch`) rồi để lại dấu mới → mọi mẫu ở mọi cây đều 0 dấu (không cache nào đi qua giữa các mẫu); file
        `scratch` do `setup` sinh còn nguyên ở mọi mẫu."""
        count = (
            'n=$(find "$HOME" "$XDG_CACHE_HOME" "$TMPDIR" src/__pycache__ -name \'mark*\' 2>/dev/null | wc -l); '
            'touch "$HOME/mark1" "$XDG_CACHE_HOME/mark2" "$TMPDIR/mark3"; mkdir -p src/__pycache__; '
            "touch src/__pycache__/mark4; echo $((n * 10 + $(ls src/__pycache__/keep | wc -l)))"
        )
        setup = "mkdir -p src/__pycache__ && echo k > src/__pycache__/keep"  # file `scratch` do `setup` sinh: giữ
        cfg = trial_config(setup=setup, metric={"cmd": count, "kind": "exact", "runs": 3})
        self.republish({"perf/trial.json": json.dumps(cfg)})
        self.started()
        self.put("src/hot.py", HOT.replace("K = 3", "K = 2"))
        rc, out, err = self.tr("finish", "--json")
        self.assertEqual(rc, 1, out + err)
        prim = json.loads(out)["measures"]["primary"]
        self.assertEqual([prim[t]["samples"] for t in ("base", "head", "cand")], [[1.0] * 3] * 3)

    def test_default_locks_venv_node_modules_gitignore(self) -> None:
        """🟠 F4: khoá mặc định gồm `.venv/`, `node_modules/` (bin của cây đứng đầu PATH lệnh đo) và `.gitignore`."""
        ctx = xt.TrialCtx("b", "r", TOOL, "t", trial_config(), "c", [])
        for path in (".venv/bin/python3", "a/.venv/lib/x.py", "node_modules/.bin/node", "web/node_modules/p/i.js"):
            with self.subTest(path):
                self.assertTrue(ctx.locked(path))
        self.assertTrue(ctx.locked(".gitignore") and ctx.locked("src/.gitignore"))

    def test_candidate_in_tree_path_dir_tampered(self) -> None:
        """🟠 F4: dự án gỡ khoá `.venv/` (không ignore nó), candidate thêm `.venv/bin/python3` giả in 1 cho bộ đo →
        `tampered` (file trong thư mục PATH của cây đo), thu hồi — không `kept`."""
        cfg = trial_config(unlock=[".venv/**"])
        self.republish({".gitignore": ".autopilot/\n__pycache__/\n", "perf/trial.json": json.dumps(cfg)})
        self.started("src/hot.py", ".venv/bin/python3")
        real = f'exec {sys.executable} "$@"\n'  # không `python3`: PATH của cây trỏ lại chính shim
        shim = self.put(".venv/bin/python3", '#!/bin/sh\n[ "$1" = bench.py ] && { echo 1; exit 0; }\n' + real)
        shim.chmod(0o755)
        rc, out, err = self.tr("finish", "--json")
        row = json.loads(out)
        self.assertEqual((rc, row["verdict"]), (1, "tampered"), out + err)
        self.assertIn("thư mục PATH của cây đo: .venv/bin/python3", row["reason"])

    def test_path_dirs_of_tree(self) -> None:
        """Thư mục PATH trong cây đo: bin của cây + mục `env.path` tương đối (rỗng/`.` = gốc cây — chỉ file ở gốc)."""
        cfg = trial_config(env={"path": "tools/bin::/usr/bin:./x/../t"})
        files = ["tools/bin/py", "a.sh", "src/a.py", "t/run", "node_modules/.bin/tsc", ".venv/bin/python", "/usr/bin/x"]
        self.assertEqual(
            xt.trial_path_files(cfg, files),
            ["tools/bin/py", "a.sh", "t/run", "node_modules/.bin/tsc", ".venv/bin/python"],
        )
        self.assertEqual(xt.trial_path_files(trial_config(), ["src/a.py", "a.sh"]), [])

    def test_exit_time_output_hooks_warned(self) -> None:
        """🟢 F5: `exact` lấy số cuối stdout — mã đăng ký in lúc thoát (`atexit`), ghi thẳng `sys.stdout`, vá `builtins`
        → ⚠ heuristic (so toàn stdout với gốc: T-3705)."""
        for line in ("import atexit as _a", "sys.stdout.write('1')", "import builtins; builtins.print = f"):
            with self.subTest(line):
                self.assertIsNotNone(xt.PERF_SUSPECT_RE.search(line))

    def test_sigterm_mid_measure_cleans_up(self) -> None:
        """🟢 F6: SIGTERM giữa lượt đo → exit 2, tiến trình đo bị dừng (cả nhóm), không còn cây tạm, pha về `started` kèm
        dòng `interrupt` trong sổ; `finish` lại đo được."""
        tmp, pid, mark = self.tmp / "tmpdir", self.ctl / "pid", self.ctl / "hang"
        tmp.mkdir()
        cmd = f"echo $$ > {pid}; exec python3 bench.py"
        self.republish({"perf/trial.json": json.dumps(trial_config(metric={"cmd": cmd, "kind": "exact", "runs": 3}))})
        self.started()
        self.put("src/hot.py", HOT.replace("K = 3", "K = 2"))
        mark.write_text("1", encoding="utf-8")
        self.addCleanup(mark.unlink, missing_ok=True)
        proc = subprocess.Popen(
            [sys.executable, str(XT), "perf", "trial", "finish"],
            cwd=self.repo,
            env={**os.environ, "TMPDIR": str(tmp)},
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        self.addCleanup(lambda: proc.poll() is None and proc.kill())
        for _ in range(1200):
            if (self.ctl / "hanging").exists() or proc.poll() is not None:
                break
            time.sleep(0.05)
        proc.send_signal(signal.SIGTERM)
        out = proc.communicate(timeout=60)[0].decode("utf-8", "replace")
        child = int(pid.read_text(encoding="utf-8"))
        with contextlib.suppress(ProcessLookupError):
            os.kill(child, 0)
            self.addCleanup(os.kill, child, signal.SIGKILL)
            self.fail(f"tiến trình đo {child} còn sống")
        self.assertEqual(proc.returncode, 2, out)
        self.assertEqual(list(tmp.iterdir()), [])
        self.assertEqual((self.tstate()["phase"], self.rows()[-1]["event"]), ("started", "interrupt"))
        mark.unlink()
        self.assertEqual(self.tr("finish")[0], 0)

    def test_interrupt_in_process_restores_started(self) -> None:
        """SIGINT/SIGTERM trong tiến trình (nhánh xử lý tín hiệu): exit 2, pha `started`, bộ xử lý cũ được trả lại."""
        for sig in (signal.SIGINT, signal.SIGTERM):
            with self.subTest(sig.name):
                if self.rows():
                    self.ok("abort", "--reason", "lần thử mới cho tín hiệu kế")
                self.started()
                self.put("src/hot.py", HOT + f"# {sig.name}\n")
                old = signal.getsignal(sig)
                with unittest.mock.patch.object(xt, "trial_measure", side_effect=lambda *a: os.kill(os.getpid(), sig)):
                    rc, out, err = self.tr("finish")
                self.assertEqual((rc, self.tstate()["phase"]), (2, "started"), out + err)
                self.assertIn("ngắt giữa lượt đo", err)
                self.assertIs(signal.getsignal(sig), old)

    def test_interleaved_round_robin_order(self) -> None:
        """🟢 F9: vòng i chạy ba cây theo thứ tự xoay B K C → K C B → C B K, mỗi cây chỉ số chính rồi chỉ số phụ."""
        log = self.ctl / "order"
        sec = trial_config()["secondary"][0] | {"cmd": f"echo S $(basename $PWD) >> {log}; python3 mem.py"}
        m = {"cmd": f"echo P $(basename $PWD) >> {log}; python3 bench.py", "kind": "exact", "runs": 3}
        self.republish({"perf/trial.json": json.dumps(trial_config(metric=m, secondary=[sec]))})
        self.started()
        self.put("src/hot.py", HOT.replace("K = 3", "K = 2"))
        self.assertEqual(self.tr("finish")[0], 0)
        trees = ["base", "head", "cand", "head", "cand", "base", "cand", "base", "head"]
        want = [f"{k} {t}" for t in trees for k in "PS"]
        self.assertEqual(log.read_text(encoding="utf-8").splitlines(), want)


GATE = "python3 -I <(git cat-file blob refs/remotes/origin/HEAD:{} || echo 'raise SystemExit(2)') perf trial status --check"


class TrialReview445Test(TrialCase):
    """Review #445 (D-370): Gate mẫu fail-closed, ngắt sau đóng băng tiêu lần đo lại duy nhất, held-out gộp đạt `target`,
    đầu ra chỉ số chính so gốc, không ghi `decide` trùng, `abort` sau `--no-apply` giữ. Mỗi ca tái hiện một kịch bản."""

    def decides(self, tid: str) -> list[dict[str, Any]]:
        return [r for r in self.rows() if r["event"] == "decide" and r["id"] == tid]

    def interrupted(self, *args: str) -> tuple[int, str]:
        """`finish` bị SIGTERM giữa lượt đo (sau đóng băng)."""
        kill = unittest.mock.patch.object(
            xt, "trial_measure", side_effect=lambda *a: os.kill(os.getpid(), signal.SIGTERM)
        )
        with kill:
            rc, out, err = self.tr("finish", *args)
        return rc, out + err

    def test_gate_template_fails_closed(self) -> None:
        """🔴1: Gate mẫu (skill, optimization-loop.md, ADR §5) qua `run_gate_shell` — không đọc được công cụ (thiếu
        `origin/HEAD`, sai đường) → khác 0 (từng exit 0: script rỗng); đọc được → mã của `status --check` (1: chưa giữ)."""
        docs = (".claude/skills/optimize/SKILL.md", "framework/11-autonomous-loop/optimization-loop.md")
        for rel in (*docs, "docs/adr/0071-perf-trial.md"):
            with self.subTest(rel):
                text = re.sub(r"\s+", " ", (ROOT / rel).read_text(encoding="utf-8"))
                self.assertIn("|| echo 'raise SystemExit(2)') perf trial status --check", text)
                self.assertNotIn("<(git cat-file blob origin/HEAD:", text)
        self.assertEqual(xt.run_gate_shell(GATE.format(TOOL), self.repo, 120)[0], 1)
        self.assertEqual(xt.run_gate_shell(GATE.format("scripts/xt.py"), self.repo, 120)[0], 2)
        self.git("remote", "set-head", "origin", "-d")
        self.assertEqual(xt.run_gate_shell(GATE.format(TOOL), self.repo, 120)[0], 2)

    @flow("FLOW-47")
    def test_flow_47_second_interrupt_is_incomplete(self) -> None:
        """🔴2 Given candidate đóng băng · When SIGTERM giữa lượt; `finish` lại, SIGTERM lần hai · Then lần đầu exit 2, pha
        `started`, `resumes` 1 (tiêu lần đo lại); lần hai thu hồi `incomplete` (exit 1, cây = `fp_start`), một dòng
        `decide` — không rút lại hạt giống held-out vô hạn."""
        fp0 = xt.tree_fingerprint(self.repo)
        tid = self.started()
        self.put("src/hot.py", HOT.replace("K = 3", "K = 2"))
        rc, out = self.interrupted()
        self.assertEqual((rc, self.tstate()["phase"], self.tstate()["resumes"]), (2, "started", 1), out)
        rc, out = self.interrupted()
        self.assertEqual(rc, 1, out)
        self.assertEqual([(r["verdict"], r["rounds"]) for r in self.decides(tid)], [("incomplete", 2)])
        self.assertIn("SIGTERM", self.decides(tid)[0]["reason"])
        self.assertEqual((xt.tree_fingerprint(self.repo), self.tstate()["phase"]), (fp0, "closed"))

    def test_interrupt_after_resume_or_kill_after_interrupt(self) -> None:
        """🔴2: SIGTERM giữa lượt `--resume` (lần đo lại đã tiêu) → `incomplete`; ngắt rồi chết (pha `measuring`) →
        `--resume` → `incomplete` (chung bộ đếm `resumes`)."""
        tid = self.started()
        self.put("src/hot.py", HOT.replace("K = 3", "K = 2"))
        ctx = self.ctx()
        xt.trial_freeze(self.repo, ctx, xt.trial_finish_check(self.repo, ctx), xt.trial_dirty(self.repo))
        rc, out = self.interrupted("--resume")
        self.assertEqual((rc, [r["verdict"] for r in self.decides(tid)]), (1, ["incomplete"]), out)
        tid = self.started()
        self.put("src/hot.py", HOT.replace("K = 3", "K = 1"))
        self.assertEqual(self.interrupted()[0], 2)
        ctx = self.ctx()
        xt.trial_freeze(self.repo, ctx, xt.trial_finish_check(self.repo, ctx), xt.trial_dirty(self.repo))
        rc, out, err = self.tr("finish", "--resume")
        self.assertEqual((rc, [r["verdict"] for r in self.decides(tid)]), (1, ["incomplete"]), out + err)

    @flow("FLOW-48")
    def test_flow_48_status_check_needs_heldout_total_at_target(self) -> None:
        """🟠1 Given lần giữ: chỉ số chính −90 % (đường tắt input bộ đo) nhưng held-out gộp −4 % · When `status --check`
        · Then exit 1 nêu held-out; held-out gộp đạt → 0; held-out thiếu số → 1; không khai held-out → chỉ số chính."""
        tree = self.git("rev-parse", "HEAD^{tree}")
        row = {"event": "decide", "id": "PT-0001", "base_sha": self.base, "hotspot": ["src/hot.py"], "verdict": "kept"}
        row |= {"candidate_tree": tree, "candidate_files": ["src/hot.py"]}
        row |= {"measures": {"primary": {"compare": {"base": {"change": -0.9}}}}}
        self.append_row(row | {"heldout": {"compare": {"base": {"change": -0.04}}}})
        self.assertIn("held-out gộp -4.00%", self.refused("status", "--check", code=1))
        self.append_row(row | {"heldout": {"compare": {}}})
        self.assertIn("held-out gộp None", self.refused("status", "--check", code=1))
        self.append_row(row | {"heldout": {"compare": {"base": {"change": -0.25}}}})
        self.assertIn("held-out gộp -25.00%", self.ok("status", "--check"))
        self.append_row(row | {"heldout": xt.PERF_TRIAL_NO_HELDOUT})
        self.ok("status", "--check")

    @flow("FLOW-49")
    def test_flow_49_primary_output_differs_is_inequivalent(self) -> None:
        """🟠2 Given candidate `atexit.register(print, 1)` (số cuối stdout = 1), cấu hình có/không held-out · When `finish`
        · Then `inequivalent` (đầu ra chỉ số chính trừ số cuối khác gốc), thu hồi exit 1."""
        cfg = trial_config()
        del cfg["heldout"]
        for over in ({}, {"perf/trial.json": json.dumps(cfg)}):
            with self.subTest(heldout=not over):
                if over:
                    self.republish(over)
                tid = self.started()
                self.put("src/hot.py", "import atexit\natexit.register(print, 1)\n" + HOT)
                rc, out, err = self.tr("finish")
                self.assertEqual((rc, self.decides(tid)[0]["verdict"]), (1, "inequivalent"), out + err)
                self.assertIn("đầu ra chỉ số chính", self.decides(tid)[0]["reason"])

    def test_wall_output_compared_whole(self) -> None:
        """🟠2 `wall`: đầu ra = toàn stdout; khác gốc → lý do; trùng → ""."""
        same = {"primary": {"base": {"a\n"}, "head": {"a\n"}, "cand": {"a\n"}}}
        self.assertEqual(xt.trial_output_problem(same), "")
        diff = {"primary": {"base": {"a\n"}, "head": {"a\n"}, "cand": {"a\n1\n"}}}
        self.assertIn("khác gốc", xt.trial_output_problem(diff))

    @flow("FLOW-50")
    def test_flow_50_crash_between_decide_row_and_state(self) -> None:
        """🟠3 Given `finish` chết sau khi nối dòng `decide`, trước khi state sang `decided` (pha `measuring`/`started`) ·
        When `finish --resume` / `finish` · Then dùng lại quyết định đã ghi (giữ → exit 0; `empty` → 1), đúng một dòng
        `decide`, đếm ba lần không cộng đôi."""
        real = xt.write_atomic

        def boom(path: Path, text: str, *a: Any, **k: Any) -> None:
            if path.name == xt.PERF_TRIAL_FILE and '"phase": "decided"' in text:
                raise RuntimeError("chết giữa dòng decide và state")
            real(path, text, *a, **k)

        for cand, resume, code in ((HOT.replace("K = 3", "K = 2"), ("--resume",), 0), (None, (), 1)):
            with self.subTest(cand=bool(cand)):
                tid = self.started()
                if cand:
                    self.put("src/hot.py", cand)
                with unittest.mock.patch.object(xt, "write_atomic", boom):
                    self.assertEqual(self.tr("finish")[0], 2)
                self.assertNotEqual(self.tstate()["phase"], "decided")
                rc, out, err = self.tr("finish", *resume)
                self.assertEqual((rc, len(self.decides(tid)), self.tstate()["phase"]), (code, 1, "closed"), out + err)
                self.assertIn("đã quyết", err)
                if cand:
                    self.git("commit", "-q", "-am", "giữ")
        self.assertEqual(xt.trial_streaks(self.rows()), {"src/hot.py": 1})

    @flow("FLOW-51")
    def test_flow_51_no_apply_kept_then_abort(self) -> None:
        """🟠4 Given `finish --no-apply` ra `kept` (pha `decided`, chưa áp) · When `abort` · Then dòng `aborted` sau dòng
        `kept`, thu hồi về `fp_start`, pha `closed`; dòng `kept` không còn hiệu lực (neo, đếm, Gate) — `start`, `log` kế
        exit 0, `status --check` 1 "chưa có lần giữ"; `abort` không ghi `aborted` trùng."""
        fp0 = xt.tree_fingerprint(self.repo)
        tid = self.started()
        self.put("src/hot.py", HOT.replace("K = 3", "K = 2"))
        self.assertEqual(self.tr("finish", "--no-apply")[0], 0)
        self.ok("abort", "--reason", "không muốn áp")
        self.assertEqual([r["verdict"] for r in self.decides(tid)], ["kept", "aborted"])
        self.assertEqual((xt.tree_fingerprint(self.repo), self.tstate()["phase"]), (fp0, "closed"))
        self.assertIsNone(xt.trial_anchor(self.rows(), self.base))
        self.assertEqual(xt.trial_streaks(self.rows()), {"src/hot.py": 1})
        self.assertIn("chưa có lần giữ", self.refused("status", "--check", code=1))
        self.ok("log")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "log")
        tid = self.started()
        self.put("src/hot.py", HOT.replace("K = 3", "K = 1"))
        self.assertEqual(self.tr("finish", "--no-apply")[0], 0)
        with unittest.mock.patch.object(xt, "tree_fingerprint", return_value="lệch"):
            self.assertEqual(self.tr("abort", "--reason", "x")[0], 4)
        self.assertEqual(self.tstate()["verdict"], "aborted")
        self.git("checkout", "--", "src/hot.py")
        self.ok("abort", "--reason", "x")
        self.assertEqual([r["verdict"] for r in self.decides(tid)], ["kept", "aborted"])

    def test_kept_reason_and_no_apply_stash_literal(self) -> None:
        """🟢: lý do `kept` không nhắc held-out khi không khai; lệnh stash `--no-apply` in ra theo pathspec nghĩa đen."""
        cfg = trial_config()
        del cfg["heldout"]
        self.republish({"perf/trial.json": json.dumps(cfg)})
        self.started()
        self.put("src/hot.py", HOT.replace("K = 3", "K = 2"))
        rc, out, err = self.tr("finish", "--json")
        self.assertEqual(rc, 0, out + err)
        self.assertNotIn("held-out", json.loads(out)["reason"])
        self.git("commit", "-q", "-am", "giữ")
        self.started()
        self.put("src/hot.py", HOT.replace("K = 3", "K = 2") + "# x\n")
        rc, out, err = self.tr("finish", "--no-apply")
        self.assertIn("GIT_LITERAL_PATHSPECS=1 git stash push", out)


class TrialParserTest(unittest.TestCase):
    def test_every_trial_command_has_example_and_exit_codes(self) -> None:
        sub = next(a for a in xt.build_parser()._actions if isinstance(a, argparse._SubParsersAction))
        perf = next(a for a in sub.choices["perf"]._actions if isinstance(a, argparse._SubParsersAction))
        trial = next(a for a in perf.choices["trial"]._actions if isinstance(a, argparse._SubParsersAction))
        self.assertEqual(sorted(trial.choices), ["abort", "finish", "log", "prepare", "start", "status"])
        for name, p in trial.choices.items():
            with self.subTest(name):
                self.assertIn("ví dụ:", p.epilog or "")
                self.assertIn("mã thoát:", p.epilog or "")

    def test_no_base_flag(self) -> None:
        with self.assertRaises(SystemExit) as cm, unittest.mock.patch("sys.stderr"):
            xt.build_parser().parse_args(["perf", "trial", "start", "--hotspot", "a", *TRIAL_ARGS, "--base", "HEAD"])
        self.assertEqual(cm.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
