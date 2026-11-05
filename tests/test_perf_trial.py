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
import shutil
import subprocess
import sys
import unittest
import unittest.mock
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import xt
from test_flow import GIT_ID, HOT, TOOL, TRIAL_ARGS, trial_config, trial_files
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
        start |= {"hypothesis": "h", "falsifier": "f", "start_head": "s"}
        good = [start, self.kept(), {"schema": 1, "event": "log", "base_sha": "b", "tree": "t"}]
        bad = [
            [],
            {**start, "schema": True},
            {**start, "schema": 2},
            {**start, "event": ["start"]},
            {**start, "default_ref": None},
            {**start, "hotspot": [1]},
            self.kept(candidate_files="a"),
            self.kept(candidate_tree=None),
        ]
        self.assertEqual([xt._trial_row_ok(r) for r in good], [True] * 3)
        self.assertEqual([xt._trial_row_ok(r) for r in bad], [False] * len(bad))

    def test_streaks_per_path_kept_resets_only_changed(self) -> None:
        def no(*hot: str) -> dict[str, Any]:
            return {"event": "decide", "verdict": "aborted", "hotspot": list(hot)}

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
        self.git("remote", "set-url", "origin", str(self.tmp / "không-có"))
        self.assertEqual(xt.trial_round_base(self.repo), (self.base, "refs/heads/main"))
        self.git("remote", "set-head", "origin", "-d")
        self.assertIn("set-head origin -a", self.refused("status"))

    def test_server_without_head_symref_and_timeout(self) -> None:
        """Máy chủ trả rc 0 mà không có symref (repo rỗng) hoặc `ls-remote` quá giờ → None (dùng ref cục bộ)."""
        empty = self.tmp / "empty.git"
        self.run_git(self.tmp, "init", "-q", "--bare", str(empty))
        self.git("remote", "set-url", "origin", str(empty))
        self.assertIsNone(xt._trial_ls_remote(self.repo))
        real = subprocess.run

        def slow(cmd: Any, *a: Any, **k: Any) -> Any:
            if "ls-remote" in cmd:
                raise subprocess.TimeoutExpired(cmd, 1)
            return real(cmd, *a, **k)

        with unittest.mock.patch.object(xt.subprocess, "run", slow):
            self.assertIsNone(xt._trial_ls_remote(self.repo))

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
        """D-363: byte `xt.py` đang chạy ≠ blob ở gốc → `exec python3 -I <bản gốc> <đúng argv>`; bằng nhau thì không."""
        self.republish({TOOL: XT.read_text(encoding="utf-8") + "# bản gốc khác\n"})

        class Exec(Exception):
            pass

        with unittest.mock.patch.object(xt.os, "execv", side_effect=Exec) as ex, self.assertRaises(Exec):
            run_main("perf", "trial", "status", "--json")
        exe, argv = ex.call_args.args
        self.addCleanup(shutil.rmtree, Path(argv[2]).parent)
        self.assertEqual(
            (exe, argv[0], argv[1], argv[3:]),
            (sys.executable, sys.executable, "-I", ["perf", "trial", "status", "--json"]),
        )
        self.assertTrue(Path(argv[2]).read_text(encoding="utf-8").endswith("# bản gốc khác\n"))

    def test_git_error_is_exit_2_and_todo_commands(self) -> None:
        with unittest.mock.patch.object(xt, "trial_context", side_effect=RuntimeError("git lỗi")):
            self.assertEqual(self.tr("status")[0], 2)
        for args, task in ((("prepare",), "T-3702"), (("finish",), "T-3703"), (("status", "--check"), "T-3704")):
            with self.subTest(args):
                self.assertIn(f"chưa triển khai ({task})", self.refused(*args))


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
