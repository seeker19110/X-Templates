"""Corpus luồng (ADR-0052 §1; nghiên cứu 2026-10-26 §10): chạy `xt.py` THẬT trong repo git tạm, không mock state.

State dựng bằng chính lệnh `loop init/record/defer/block`; không ca nào sửa tay `.autopilot/state.json`.

Cơ chế xfail (không skip):
- `XFAIL` = {ID: tái hiện + task sẽ sửa}. Ca có ID trong `XFAIL` mà KHÔNG có trong `XT_FLOW_STRICT` nhận
  `unittest.expectedFailure`: đỏ hôm nay thì suite vẫn exit 0; tự xanh thì "unexpected success" làm suite đỏ — nhắc gỡ ID khỏi `XFAIL`.
- `XT_FLOW_STRICT=FLOW-01,FLOW-04` (phân cách dấu phẩy, khoảng trắng bỏ qua, đọc lúc import) bỏ xfail của các ID đó: ca chạy thường
  nên Gate của task sửa chỉ xanh khi ca thật sự đạt.
- `@flow("FLOW-NN")` gắn ID cho test và ghi vào `FLOW_IDS`; `test_strict_ids_exist` đỏ khi `XT_FLOW_STRICT` hoặc `XFAIL`
  nêu ID không có test nào mang nó (Gate không xanh vì thiếu ca).
- Gỡ ID khỏi `XFAIL` khi task sửa xong; ID không còn xfail vẫn chạy thường. Một ID nhiều ca, task chỉ làm xanh một phần:
  `@flow("FLOW-NN", done="T-NNNN")` cho ca đã xanh — ca đó chạy thường dù ID còn trong `XFAIL` (các ca khác vẫn xfail).
"""

from __future__ import annotations

import contextlib
import functools
import json
import multiprocessing
import os
import re
import signal
import subprocess
import sys
import tempfile
import time
import unittest
import unittest.mock
from collections.abc import Callable
from contextlib import chdir
from pathlib import Path
from typing import Any, TypeVar

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import xt
from test_xt import audit_status_text
from test_xt_cli import TmpRepoCase, run_main

F = TypeVar("F", bound=Callable[..., Any])

# ID → tái hiện + task sửa. FLOW-20…23, 27…45 (`perf trial`, ADR-0071 §10) gỡ ở T-3707 (D-365): mọi ca đã xanh.
XFAIL: dict[str, str] = {}
STRICT: frozenset[str] = frozenset(s.strip() for s in os.environ.get("XT_FLOW_STRICT", "").split(",") if s.strip())
FLOW_IDS: set[str] = set()


def flow(flow_id: str, done: str = "") -> Callable[[F], F]:
    """Gắn ID cho test; ID thuộc XFAIL, không thuộc STRICT và ca chưa có `done` (task làm nó xanh) → `expectedFailure`."""

    def deco(fn: F) -> F:
        FLOW_IDS.add(flow_id)
        if flow_id in XFAIL and flow_id not in STRICT and not done:
            return unittest.expectedFailure(fn)
        return fn

    return deco


PLAN = (
    "- [ ] `T-001` việc một — Gate: `bash gate.sh`\n"
    "- [ ] `T-002` việc hai — Gate: `true`\n"
    "- [ ] `T-900` chờ người — Gate: `true`\n"
    "- [ ] `T-901` chờ người nữa — Gate: `true`\n"
)
# Gate giả: bộ đếm trong `.flow-counter`; có file `green` → xanh; không thì đỏ, chữ ký luân phiên theo STYLE.
GATE = r"""#!/bin/bash
d="$(dirname "$0")"
[ -f "$d/green" ] && exit 0
n=$(( $(cat "$d/.flow-counter" 2>/dev/null || echo 0) + 1 ))
echo "$n" > "$d/.flow-counter"
if [ "$(cat "$d/style" 2>/dev/null)" = "same" ] || [ $((n % 2)) -eq 1 ]; then
  echo "AssertionError A"
else
  echo "TypeError B"
fi
exit 1
"""
SESSION_A = "11111111-aaaa-bbbb-cccc-000000000001"
SESSION_B = "22222222-aaaa-bbbb-cccc-000000000002"


REFUSE = "không đủ điều kiện so"
SAMPLES_MS = [98.0, 99.0, 100.0, 101.0, 102.0, 100.5, 99.5, 100.2, 99.8, 100.1]
SAMPLES_S = [x / 1000 for x in SAMPLES_MS]
# Mẫu v2 đủ trường như `perf sample` ghi (`cmd` là mảng): ca từ chối phải từ chối vì ĐÚNG một điều lệch, không vì mẫu thiếu
# trường (T-3545 — bản đầu của FLOW-18/19 thiếu `head`/`dirty`/`harness_sha256` và `cmd` là chuỗi nên xanh oan).
PERF_META: dict[str, Any] = {
    "schema": 2,
    "cmd": ["make", "bench"],
    "unit": "s",
    "higher_is_better": False,
    "env": {"platform": "linux-x", "python": "3.11", "nproc": 4},
    "head": "a" * 40,
    "dirty": False,
    "tree_fp": "f" * 64,
    "harness_sha256": "1" * 64,
}


def _bump(st: dict[str, Any], key: str) -> dict[str, Any]:
    """`fn` của FLOW-07: sửa tại chỗ VÀ trả state — hợp với cả hai kiểu hợp đồng của `update_state`."""
    st[key] = st.get(key, 0) + 1
    return st


def _bump_worker(base: str, key: str, n: int, barrier: Any, errors: Any) -> None:
    """Tiến trình con của FLOW-07: `n` lần `update_state`, Barrier trước MỖI lần để hai bên luôn gọi đồng thời."""
    try:
        for _ in range(n):
            barrier.wait(timeout=20)
            xt.update_state(Path(base), functools.partial(_bump, key=key))
    except BaseException as exc:  # báo lại cho cha rồi dừng, không treo bên kia
        errors.put(f"{key}: {type(exc).__name__}: {exc}")
        barrier.abort()
        raise SystemExit(1) from None


class FlowTest(TmpRepoCase):
    def setUp(self) -> None:
        super().setUp()
        repo = self.init_repo()
        (repo / "docs" / "autopilot").mkdir(parents=True)
        (repo / "docs" / "autopilot" / "PLAN.md").write_text(PLAN, encoding="utf-8")
        (repo / "gate.sh").write_text(GATE, encoding="utf-8")
        (repo / ".gitignore").write_text(".autopilot/\n.flow-counter\nstyle\ngreen\n", encoding="utf-8")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "init")
        self.enterContext(
            unittest.mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(repo), "CLAUDE_CODE_SESSION_ID": SESSION_A})
        )

    def loop(self, *args: str, session: str | None = None) -> tuple[int, str, str]:
        """`xt.py loop …` ở gốc repo tạm; `SystemExit` của argparse (lệnh con chưa có) → mã thoát, không làm vỡ ca."""
        env = {"CLAUDE_CODE_SESSION_ID": session} if session else {}
        with unittest.mock.patch.dict(os.environ, env), chdir(self.repo):
            try:
                return run_main("loop", *args)
            except SystemExit as e:
                return (e.code if isinstance(e.code, int) else 2), "", f"SystemExit {e.code}"

    def state(self) -> dict[str, Any]:
        data = json.loads((self.repo / ".autopilot" / "state.json").read_text(encoding="utf-8"))
        assert isinstance(data, dict)
        return data

    def verdict(self) -> dict[str, Any]:
        rc, out, err = self.loop("status", "--json")
        self.assertEqual(rc, 0, err)
        data = json.loads(out)
        assert isinstance(data, dict)
        return data

    def red(self, task: str = "T-001") -> None:
        self.assertNotEqual(self.loop("record", "--task", task, "--", "bash gate.sh")[0], 0)

    def same_signature(self) -> None:
        (self.repo / "style").write_text("same", encoding="utf-8")

    def seed_wait_and_failures(self) -> None:
        """Vòng một phiên, T-900 chờ người, T-001 đỏ hai lần cùng chữ ký (đếm lỗi = 2)."""
        self.assertEqual(self.loop("init", "--single-session")[0], 0)
        self.assertEqual(self.loop("defer", "--task", "T-900", "--reason", "chủ repo ký")[0], 0)
        self.same_signature()
        self.red()
        self.red()
        st = self.state()
        self.assertEqual(st["same_failure_count"], 2)
        self.assertEqual(st["session_id"], SESSION_A)

    @flow("FLOW-01")
    def test_flow_01_attach_keeps_deferred_and_failure_count(self) -> None:
        """Given vòng một phiên, deferred T-900, đếm lỗi 2 · When `loop attach` với session mới ·
        Then exit 0, deferred giữ T-900, đếm lỗi giữ 2, session_id mới."""
        self.seed_wait_and_failures()
        rc, _, err = self.loop("attach", session=SESSION_B)
        self.assertEqual(rc, 0, err)
        st = self.state()
        self.assertIn("T-900", st["deferred"])
        self.assertEqual(st["same_failure_count"], 2)
        self.assertEqual(st["session_id"], SESSION_B)

    @flow("FLOW-02")
    def test_flow_02_resolve_only_named_task_leaves_deferred(self) -> None:
        """Given như FLOW-01 thêm deferred T-901 · When `loop resolve --task T-900 --reason x` ·
        Then chỉ T-900 rời deferred, `resolved[]` có T-900, đếm lỗi giữ 2."""
        self.seed_wait_and_failures()
        self.assertEqual(self.loop("defer", "--task", "T-901", "--reason", "chủ repo ký nữa")[0], 0)
        rc, _, err = self.loop("resolve", "--task", "T-900", "--reason", "x")
        self.assertEqual(rc, 0, err)
        st = self.state()
        self.assertNotIn("T-900", st["deferred"])
        self.assertIn("T-901", st["deferred"])
        self.assertIn("T-900", json.dumps(st["resolved"]))
        self.assertEqual(st["same_failure_count"], 2)

    @flow("FLOW-03")
    def test_flow_03_defer_refused_for_failing_task(self) -> None:
        """Given T-001 vừa đỏ một lần · When `loop defer --task T-001` · Then từ chối (exit ≠ 0), T-001 không vào
        deferred (`_defer_problem`: không né blocked). `resolve` không nới `defer` (ADR-0051 §Bối cảnh): task đang lỗi
        không có trong deferred → `resolve` exit 2, state không đổi."""
        self.assertEqual(self.loop("init")[0], 0)
        self.red()
        rc, _, err = self.loop("defer", "--task", "T-001", "--reason", "né")
        self.assertNotEqual(rc, 0)
        self.assertIn("task đang lỗi", err)
        self.assertNotIn("T-001", self.state().get("deferred", {}))
        before = self.state()
        rc, _, err = self.loop("resolve", "--task", "T-001", "--reason", "né")
        self.assertEqual(rc, 2)
        self.assertIn("không có trong việc chờ người", err)
        self.assertEqual(self.state(), before)

    @flow("FLOW-04")
    def test_flow_04_alternating_signatures_end_blocked(self) -> None:
        """Given Gate đỏ xen kẽ chữ ký A/B · When 6 × `loop record` · Then verdict `blocked`, lý do nêu 6 lần đỏ và
        2 chữ ký khác nhau. (Hiện `same_failure_count` về 1 mỗi lần đổi chữ ký → `continue` → xfail.)"""
        self.assertEqual(self.loop("init")[0], 0)
        for _ in range(6):
            self.red()
        v = self.verdict()
        self.assertEqual(v["verdict"], "blocked", v)
        self.assertRegex(v["reason"], r"6\D+lần đỏ")
        self.assertRegex(v["reason"], r"2\D+chữ ký")

    @flow("FLOW-05")
    def test_flow_05_same_signature_three_times_blocks(self) -> None:
        """Đối chứng R6: Gate đỏ cùng chữ ký A ×3 → `blocked` (hành vi hiện có, không đổi)."""
        self.assertEqual(self.loop("init")[0], 0)
        self.same_signature()
        for _ in range(3):
            self.red()
        v = self.verdict()
        self.assertEqual(v["verdict"], "blocked", v)
        self.assertIn("cùng một lỗi lặp 3 lần", v["reason"])
        self.assertTrue(re.search(r"T-001", v["reason"]))

    @flow("FLOW-06")
    def test_flow_06_green_resets_task_runs_and_loop_continues(self) -> None:
        """Given T-001 đỏ 5 lần (chữ ký luân phiên, không chạm max_same_failure) rồi xanh · Then `task_runs` có khoá và
        T-001 = 0 (hoặc vắng), verdict `continue`/`done`, không `blocked`. (Hiện state không có `task_runs` → xfail.)"""
        self.assertEqual(self.loop("init")[0], 0)
        for _ in range(5):
            self.red()
        (self.repo / "green").write_text("1", encoding="utf-8")
        self.assertEqual(self.loop("record", "--task", "T-001", "--", "bash gate.sh")[0], 0)
        st = self.state()
        self.assertIn("task_runs", st)
        self.assertEqual(st["task_runs"].get("T-001", 0), 0)
        self.assertIn(self.verdict()["verdict"], ("continue", "done"))

    @flow("FLOW-07")
    def test_flow_07_two_processes_update_state_no_lost_update(self) -> None:
        """Given state từ `loop init` · When hai tiến trình thật, mỗi bên 100 lần `xt.update_state(base, fn)` (A tăng
        `flow_a`, B tăng `flow_b`; Barrier(2) trước mỗi lần → xen kẽ tất định) · Then `flow_a == 100`, `flow_b == 100`,
        `rev` tăng đúng 200 (thiếu `rev` = 0). Tiến trình con lỗi → đỏ rõ ràng. (Hiện chưa có `update_state` → xfail.)"""
        self.assertEqual(self.loop("init")[0], 0)
        rev0 = self.state().get("rev", 0)
        ctx = multiprocessing.get_context("fork" if "fork" in multiprocessing.get_all_start_methods() else "spawn")
        barrier, errors = ctx.Barrier(2), ctx.Queue()
        procs = [
            ctx.Process(target=_bump_worker, args=(str(self.repo), key, 100, barrier, errors), daemon=True)
            for key in ("flow_a", "flow_b")
        ]
        for p in procs:
            p.start()
        for p in procs:
            p.join(60)
        hung = [p for p in procs if p.is_alive()]
        for p in hung:
            p.kill()
            p.join()
        msgs: list[str] = []
        while not errors.empty():
            msgs.append(errors.get(timeout=1))
        self.assertEqual([], hung, "tiến trình con treo quá 60 s")
        self.assertEqual([0, 0], [p.exitcode for p in procs], "; ".join(msgs))
        st = self.state()
        self.assertEqual((st["flow_a"], st["flow_b"]), (100, 100))
        self.assertEqual(st["rev"] - rev0, 200)

    @flow("FLOW-08")
    def test_flow_08_crash_after_gate_before_evidence_is_not_done(self) -> None:
        """Given vòng đã `loop init`, T-001 xanh, T-900/T-901 chờ người — T-002 (Gate `true`) là task mở cuối · When
        `loop record --task T-002 -- true` bị `os._exit` đúng lúc ghi bằng chứng — mã 9 nếu Gate ĐÃ chạy, 8 nếu chưa ·
        Then mã 9 (Gate chạy trước bằng chứng); không bằng chứng T-002; verdict làm lại T-002, không `done`; PLAN không
        tick T-002 (lệnh khớp Gate nên tick trước bằng chứng sẽ lộ); không file `*.tmp` dở. (Đối chứng: xanh hôm nay.)"""
        self.assertEqual(self.loop("init")[0], 0)
        (self.repo / "green").write_text("", encoding="utf-8")
        self.assertEqual(self.loop("record", "--task", "T-001", "--", "bash gate.sh")[0], 0)
        for tid in ("T-900", "T-901"):
            self.assertEqual(self.loop("defer", "--task", tid, "--reason", "cần người")[0], 0)
        code = (
            "import os, sys; sys.path.insert(0, sys.argv[1]); import xt\n"
            "ran = []\n"
            "real_gate, real_write = xt.run_gate_shell, xt.write_atomic\n"
            "def gate(*a, **k):\n"
            "    ran.append(1)\n"
            "    return real_gate(*a, **k)\n"
            "def crash(path, *a, **k):\n"
            "    if os.path.basename(str(path)) == 'T-002.json':\n"
            "        os._exit(9 if ran else 8)\n"
            "    return real_write(path, *a, **k)\n"
            "xt.run_gate_shell, xt.write_atomic = gate, crash\n"
            "sys.exit(xt.main(['loop', 'record', '--task', 'T-002', '--', 'true']))\n"
        )
        env = {**os.environ, "CLAUDE_PROJECT_DIR": str(self.repo)}
        r = subprocess.run(
            [sys.executable, "-c", code, str(ROOT / "scripts")],
            cwd=self.repo,
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(r.returncode, 9, r.stdout + r.stderr)
        self.assertFalse((self.repo / ".autopilot" / "evidence" / "T-002.json").exists())
        v = self.verdict()
        self.assertEqual((v["verdict"], v.get("task")), ("continue", "T-002"), v)
        plan = (self.repo / "docs" / "autopilot" / "PLAN.md").read_text(encoding="utf-8")
        self.assertIn("- [ ] `T-002`", plan)
        self.assertEqual([], [str(p) for p in (self.repo / ".autopilot").rglob("*.tmp")])

    def audit_book(self, sha: str, findings: tuple[str, ...] = ()) -> None:
        """Sổ audit: nhóm 1 (ARCH) đã quét ở `sha`, còn lại N/A có giải trình; commit cùng mọi file đang đổi."""
        book = audit_status_text({1: ("đã quét", sha, "2026-10-28", "quét thử")}, findings)
        (self.repo / "docs" / "ops").mkdir(parents=True, exist_ok=True)
        (self.repo / "docs" / "ops" / "AUDIT-STATUS.md").write_text(book, encoding="utf-8")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "sổ audit")

    def finish_batch(self, *init: str, verify: bool = True, defer: tuple[str, ...] = ()) -> None:
        """`loop init` → mọi task xanh (T-001 qua `green`; ID trong `defer` thì `loop defer`) → `loop verify --all`:
        đợt `done` (hoặc chờ người) và đã kiểm lại cuối."""
        self.assertEqual(self.loop("init", *init)[0], 0)
        (self.repo / "green").write_text("", encoding="utf-8")
        self.assertEqual(self.loop("record", "--task", "T-001", "--", "bash gate.sh")[0], 0)
        for tid in ("T-002", "T-900", "T-901"):
            cmd = (
                ("defer", "--task", tid, "--reason", "cần người")
                if tid in defer
                else ("record", "--task", tid, "--", "true")
            )
            self.assertEqual(self.loop(*cmd)[0], 0)
        if verify:
            rc, out, err = self.loop("verify", "--all")
            self.assertEqual(rc, 0, out + err)

    def next_step(self, prs: Any = (), *extra: str) -> dict[str, Any]:
        """`loop next-step --json` với JSON `pr next` (mặc định `[]`); state trước/sau phải y nguyên (chỉ đọc)."""
        path = self.repo / ".autopilot" / "prs.json"
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(list(prs)), encoding="utf-8")
        state = self.repo / ".autopilot" / "state.json"
        before = state.read_bytes() if state.exists() else b""
        rc, out, err = self.loop("next-step", "--json", "--prs", str(path), *extra)
        self.assertEqual(rc, 0, err)
        self.assertEqual(before, state.read_bytes() if state.exists() else b"")
        data = json.loads(out)
        assert isinstance(data, dict)
        self.assertEqual(xt.next_step(data["inputs"]), data)  # phát lại cùng đầu vào → cùng kết quả
        return data

    @flow("FLOW-09")
    def test_flow_09_pr_waiting_is_not_ready_for_complete(self) -> None:
        """Given đợt `done` + kiểm lại cuối, sổ phủ tới HEAD · When `next-step` với PR của lát còn `wait` · Then `pr`
        khoá PR + head đó, không `ready-for-complete`; PR `done` thì hết việc."""
        self.audit_book(self.git("rev-parse", "HEAD"))
        self.finish_batch()
        wait = {"pr": 7, "head": "c" * 40, "action": "wait", "why": "CI chưa xong"}
        out = self.next_step([wait])
        self.assertEqual((out["action"], out["key"]["pr"], out["key"]["head"]), ("pr", "7", "c" * 40), out)
        self.assertIn("CI chưa xong", out["reason"])
        self.assertEqual(self.next_step([{**wait, "action": "done"}])["action"], "ready-for-complete")

    @flow("FLOW-10")
    def test_flow_10_unaudited_change_after_scan_needs_audit_delta(self) -> None:
        """Given đợt `done`, sổ quét ở SHA S rồi có commit mã sau S · When `next-step` · Then `audit` nêu SHA S làm
        phạm vi và file nợ; chưa có sổ → `audit` full."""
        scan = self.git("rev-parse", "HEAD")
        (self.repo / "app.py").write_text("x = 1\n", encoding="utf-8")
        self.finish_batch()
        self.assertEqual(self.next_step()["action"], "audit")  # chưa có sổ
        self.audit_book(scan)
        self.assertEqual(self.loop("verify", "--all")[0], 0)  # commit sổ đổi cây → kiểm lại cuối
        out = self.next_step()
        self.assertEqual(out["action"], "audit", out)
        self.assertIn(f"`{scan[:12]}..HEAD`", out["reason"])
        self.assertIn("app.py", out["reason"])

    @flow("FLOW-11")
    def test_flow_11_open_must_outside_deferred_in_build_replans(self) -> None:
        """Given pha build, đợt `done` (blueprint còn MUST mở — không chặn đợt), sổ sạch phủ tới HEAD · When `next-step`
        · Then `replan` (đợt kế), không `ready-for-complete`."""
        (self.repo / "xt.yaml").write_text("delivery_phase: build\n", encoding="utf-8")
        (self.repo / "BP.md").write_text("- [ ] `AAA-001` **MUST** a\n", encoding="utf-8")
        self.audit_book(self.git("rev-parse", "HEAD"))
        self.audit_book(self.git("rev-parse", "HEAD"))  # SHA quét gồm cả xt.yaml/BP.md
        self.finish_batch("--blueprint", "BP.md")
        out = self.next_step()
        self.assertEqual(out["action"], "replan", out)
        self.assertIn("1 MUST mở", out["reason"])

    @flow("FLOW-12")
    def test_flow_12_all_clean_ready_for_complete_keeps_phase(self) -> None:
        """Given hết task, PR xong, sổ sạch phủ tới HEAD, pha build · When `next-step` · Then `ready-for-complete`;
        `xt.yaml` (`delivery_phase`) và state không đổi."""
        (self.repo / "xt.yaml").write_text("delivery_phase: build\n", encoding="utf-8")
        self.audit_book(self.git("rev-parse", "HEAD"))
        self.audit_book(self.git("rev-parse", "HEAD"))
        self.finish_batch()
        out = self.next_step([{"pr": 3, "head": "d" * 40, "action": "done", "why": ""}])
        self.assertEqual(out["action"], "ready-for-complete", out)
        self.assertIn("D-178", out["reason"])
        self.assertEqual((self.repo / "xt.yaml").read_text(encoding="utf-8"), "delivery_phase: build\n")
        # Sổ trượt `audit check --strict` (nhóm 2 "chưa quét") → `audit`, không "phủ tới HEAD" (review #318).
        book = self.repo / "docs" / "ops" / "AUDIT-STATUS.md"
        book.write_text(
            book.read_text(encoding="utf-8").replace("| 2 | SEC | Bảo mật | N/A |", "| 2 | SEC | Bảo mật | chưa quét |")
        )
        self.git("commit", "-q", "-am", "sổ: nhóm 2 chưa quét")
        self.assertEqual(self.loop("verify", "--all")[0], 0)
        out = self.next_step([])
        self.assertEqual(out["action"], "audit", out)
        self.assertIn("audit check --strict", out["reason"])

    @flow("FLOW-12")
    def test_flow_12_final_check_gates_ready(self) -> None:
        """Đối chứng của FLOW-12: hết việc nhưng chưa `loop verify --all`, hay cây đổi sau đó (commit), hay đợt chờ người
        chưa kiểm lại cuối → `verify`, không `ready-for-complete`."""
        self.audit_book(self.git("rev-parse", "HEAD"))
        self.audit_book(self.git("rev-parse", "HEAD"))
        self.finish_batch(verify=False)
        self.assertEqual(self.next_step()["action"], "verify")
        self.assertEqual(self.loop("verify", "--all")[0], 0)
        self.assertEqual(self.next_step()["action"], "ready-for-complete")
        (self.repo / "NOTE.md").write_text("x\n", encoding="utf-8")
        self.git("add", "NOTE.md")
        self.git("commit", "-q", "-m", "ghi chú")
        self.assertEqual(self.next_step()["action"], "verify")
        plan2 = "docs/autopilot/PLAN-2.md"
        (self.repo / plan2).write_text(PLAN.replace("việc", "đợt 2 việc"), encoding="utf-8")
        self.finish_batch("--plan", plan2, "--force", verify=False, defer=("T-900",))
        out = self.next_step()
        self.assertEqual(out["action"], "verify", out)
        self.assertEqual(out["inputs"]["verdict"]["verdict"], xt.PENDING_HUMAN)

    @flow("FLOW-13")
    def test_flow_13_two_batches_without_progress_end_budget(self) -> None:
        """Given 🟠 mở trong sổ ở đầu đợt 1 (PLAN) và đầu đợt 2 (PLAN-2), đợt 2 `done` vẫn còn nó · When `next-step` ·
        Then `budget` kèm `no_progress_since`. Sửa spec giữa đợt 1 rồi `loop init --force` nâng trần không thành đợt mới:
        sau đợt 1 vẫn `replan` (T-3578)."""
        finding = "AUD-ARCH-001 | 🟠 | mở | lỗi | đo được: x | `true` | —"
        self.audit_book(self.git("rev-parse", "HEAD"))
        self.audit_book(self.git("rev-parse", "HEAD"), (finding,))
        self.assertEqual(self.loop("init")[0], 0)
        plan = self.repo / "docs" / "autopilot" / "PLAN.md"
        plan.write_text(plan.read_text(encoding="utf-8").replace("việc hai", "việc hai sửa spec"), encoding="utf-8")
        self.finish_batch("--force", "--max-iterations", "300")
        self.assertEqual(self.next_step()["action"], "replan")
        plan2 = "docs/autopilot/PLAN-2.md"
        (self.repo / plan2).write_text(PLAN.replace("việc", "đợt 2 việc"), encoding="utf-8")
        self.finish_batch("--plan", plan2, "--force")
        out = self.next_step()
        self.assertEqual(out["action"], "budget", out)
        self.assertIsNotNone(out["budget"]["no_progress_since"])

    def open_finding_book(self) -> None:
        finding = "AUD-ARCH-001 | 🟠 | mở | lỗi | đo được: x | `true` | —"
        self.audit_book(self.git("rev-parse", "HEAD"))
        self.audit_book(self.git("rev-parse", "HEAD"), (finding,))

    @flow("FLOW-13")
    def test_flow_13_done_batch_then_same_plan_path_is_next_batch(self) -> None:
        """S1 (review #318 lượt 3): đợt 1 `done` qua `loop verify --all`, Stop hook chưa chạy (vòng còn bật), viết đè
        PLAN.md cho đợt 2 rồi `loop init --force` · đợt 2 `done` vẫn còn 🟠 · Then `budget` — dấu đợt xong, không cờ
        `active`, quyết ranh giới đợt."""
        self.open_finding_book()
        self.finish_batch()
        plan = self.repo / "docs" / "autopilot" / "PLAN.md"
        plan.write_text(PLAN.replace("việc", "đợt 2 việc"), encoding="utf-8")
        self.finish_batch("--force")
        out = self.next_step()
        self.assertEqual(out["action"], "budget", out)

    @flow("FLOW-13")
    def test_flow_13_stop_mid_batch_then_respec_is_same_batch(self) -> None:
        """S3 (review #318 lượt 3): đợt 1 xong (giảm việc mở), đợt 2 (PLAN-2) dở thì `loop stop`, sửa spec rồi `loop init
        --force` cùng PLAN-2, làm xong · Then `replan` (mới một đợt không giảm), không `budget`."""
        self.audit_book(self.git("rev-parse", "HEAD"))
        two = (
            "AUD-ARCH-001 | 🟠 | mở | lỗi | đo được: x | `true` | —",
            "AUD-ARCH-002 | 🟠 | mở | lỗi | đo được: y | `true` | —",
        )
        self.audit_book(self.git("rev-parse", "HEAD"), two)
        self.finish_batch()
        self.audit_book(self.git("rev-parse", "HEAD"), two[:1])  # đợt 1 sửa một 🟠: 2 → 1
        plan2 = self.repo / "docs" / "autopilot" / "PLAN-2.md"
        plan2.write_text(PLAN.replace("việc", "đợt 2 việc"), encoding="utf-8")
        self.assertEqual(self.loop("init", "--plan", "docs/autopilot/PLAN-2.md", "--force")[0], 0)
        self.assertEqual(self.loop("stop", "--reason", "đổi spec")[0], 0)
        plan2.write_text(PLAN.replace("việc", "đợt 2 việc sửa spec"), encoding="utf-8")
        self.finish_batch("--plan", "docs/autopilot/PLAN-2.md", "--force")
        self.assertEqual([b["open"] for b in self.state()["objective"]["batches"]], [2, 1])
        self.assertEqual(self.next_step()["action"], "replan")

    def hook_stop(self) -> None:
        with chdir(self.repo):
            self.assertEqual(run_main("loop", "hook-stop", stdin=json.dumps({"session_id": SESSION_A}))[0], 0)

    def last_mark(self) -> dict[str, Any]:
        mark = self.state()["objective"]["batches"][-1]
        assert isinstance(mark, dict)
        return mark

    @flow("FLOW-13")
    def test_flow_13_block_mid_batch_then_respec_is_same_batch(self) -> None:
        """S3 với `loop block` + Stop hook (`final_verdict: blocked`, review #319 M7): bị chặn không đóng đợt — sửa spec
        rồi `loop init --force` cùng PLAN-2 vẫn là đợt 2 → `replan`."""
        self.audit_book(self.git("rev-parse", "HEAD"))
        two = (
            "AUD-ARCH-001 | 🟠 | mở | lỗi | đo được: x | `true` | —",
            "AUD-ARCH-002 | 🟠 | mở | lỗi | đo được: y | `true` | —",
        )
        self.audit_book(self.git("rev-parse", "HEAD"), two)
        self.finish_batch()
        self.audit_book(self.git("rev-parse", "HEAD"), two[:1])
        plan2 = self.repo / "docs" / "autopilot" / "PLAN-2.md"
        plan2.write_text(PLAN.replace("việc", "đợt 2 việc"), encoding="utf-8")
        self.assertEqual(self.loop("init", "--plan", "docs/autopilot/PLAN-2.md", "--force")[0], 0)
        self.assertEqual(self.loop("block", "--reason", "cần người")[0], 0)
        self.hook_stop()
        self.assertEqual(self.state()["final_verdict"]["verdict"], "blocked")
        self.assertNotIn("done", self.last_mark())
        plan2.write_text(PLAN.replace("việc", "đợt 2 việc sửa spec"), encoding="utf-8")
        self.finish_batch("--plan", "docs/autopilot/PLAN-2.md", "--force")
        self.assertEqual([b["open"] for b in self.state()["objective"]["batches"]], [2, 1])
        self.assertEqual(self.next_step()["action"], "replan")

    @flow("FLOW-13")
    def test_flow_13_only_green_full_verify_marks_batch_done(self) -> None:
        """Dấu đợt xong chỉ khi `loop verify --all` XANH lúc đợt `done`/chờ người (review #319 M2/M3/M4): `loop verify`
        không `--all` → không dấu; `--all` đỏ → không dấu; `--all` xanh → có dấu; đợt chờ người cũng có dấu."""
        self.finish_batch(verify=False)
        self.assertEqual(self.loop("verify")[0], 0)
        self.assertNotIn("done", self.last_mark())
        (self.repo / "green").unlink()
        self.assertNotEqual(self.loop("verify", "--all")[0], 0)
        self.assertNotIn("done", self.last_mark())
        (self.repo / "green").write_text("", encoding="utf-8")
        self.assertEqual(self.loop("verify", "--all")[0], 0)
        self.assertTrue(self.last_mark()["done"])
        plan2 = "docs/autopilot/PLAN-2.md"
        (self.repo / plan2).write_text(PLAN.replace("việc", "đợt 2 việc"), encoding="utf-8")
        self.finish_batch("--plan", plan2, "--force", defer=("T-900",))
        self.assertEqual(self.verdict()["verdict"], xt.PENDING_HUMAN)
        self.assertEqual(len(self.state()["objective"]["batches"]), 2)
        self.assertTrue(self.last_mark()["done"])

    def perf(self, name: str, **doc: Any) -> str:
        path = self.repo / name
        path.write_text(json.dumps(doc), encoding="utf-8")
        return str(path)

    @flow("FLOW-14")
    def test_flow_14_head_change_after_clean_review_rereviews_delta(self) -> None:
        """Given PR làn chuẩn pha harden có review sạch ở head cũ O, rồi push head mới N · When `pr next` (hàm thuần, không
        GitHub) rồi `next-step --objective harden-to-signoff` với JSON đó · Then `review` rà đúng `O..N`; `next-step` trả
        `pr` ở head N, giữ khoảng. Đối chứng: review sạch ở N → `merge` ghim N; `next-step` với PR `done` đi tiếp."""
        old, new = "1" * 40, "2" * 40
        d = {"pr": 7, "head": new, "verdict": "merge", "lane": "chuẩn", "stacked": False, "hard": [], "autonomy": 3}
        d |= {"reasons": ["ok"], "next": "gh pr merge 7", "delivery_phase": "harden"}
        rec: dict[str, Any] = {"reviews": [{"head": old, "clean": True}]}
        p = xt.pr_next(d, False, rec)
        self.assertEqual(p["action"], "review", p)
        self.assertIn(f"{old}..{new}", p["why"])
        self.finish_batch()
        out = self.next_step([p], "--objective", "harden-to-signoff")
        self.assertEqual((out["action"], out["key"]["pr"], out["key"]["head"]), ("pr", "7", new), out)
        self.assertIn(f"{old}..{new}", out["reason"])
        rec["reviews"].append({"head": new, "clean": True})
        p = xt.pr_next(d, False, rec)
        self.assertEqual((p["action"], p["head"]), ("merge", new), p)
        done = {**p, "action": "done"}
        self.assertNotEqual(self.next_step([done], "--objective", "harden-to-signoff")["action"], "pr")

    @flow("FLOW-15")
    def test_flow_15_regather_keeps_one_task_stable_id_and_tick(self) -> None:
        """Given 🟠 mở trong sổ đã commit (mô tả có `(sau: …)` và lệnh trong backtick) · When gom việc harden hai lần ·
        Then một mục, cùng ID, khoá `nguồn:ID` (không SHA — D-242), mô tả không thành Gate/`sau:`. Dán `line` vào
        PLAN-harden rồi lịch sử bị squash (SHA mọi commit đổi, như `gh pr merge --squash`) → vẫn nhận đúng task. Làm xanh
        (máy tick) → gom lại: cùng ID, `checked`, `audit` (nguồn còn mở), không task trùng; phát hiện mới chỉ thêm việc mới."""
        finding = "AUD-ARCH-001 | 🟠 | mở | lỗi (sau: T-001) `rm -rf x` | đo được: x | `true` | —"
        self.audit_book(self.git("rev-parse", "HEAD"))
        self.audit_book(self.git("rev-parse", "HEAD"), (finding,))
        self.finish_batch()
        first = self.next_step([], "--objective", "harden-to-signoff")
        second = self.next_step([], "--objective", "harden-to-signoff")
        self.assertEqual((first["action"], first["work"]), ("replan", second["work"]), first)
        self.assertEqual(len(first["work"]), 1)
        w = first["work"][0]
        self.assertEqual((w["id"], w["key"], w["gate"]), ("T-902", "audit:AUD-ARCH-001", "true"))
        task = xt.parse_plan(self.write("docs/autopilot/PLAN-harden.md", w["line"] + "\n"))[0]
        self.assertEqual((task["id"], task["gate"], task["after"]), ("T-902", "true", []))
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "PLAN-harden")
        self.git("checkout", "-q", "--orphan", "squashed")  # cùng cây, lịch sử một commit mới: SHA phát hiện đổi
        self.git("commit", "-q", "-m", "squash")
        self.assertEqual(self.loop("verify", "--all")[0], 0)
        pasted = self.next_step([], "--objective", "harden-to-signoff")
        self.assertEqual([(x["id"], x["planned"]) for x in pasted["work"]], [("T-902", True)], pasted)
        self.assertEqual(self.loop("init", "--plan", "docs/autopilot/PLAN-harden.md", "--force")[0], 0)
        self.assertEqual(self.loop("record", "--task", "T-902", "--", "true")[0], 0)  # khớp Gate → máy tick [x]
        self.assertEqual(self.loop("verify", "--all")[0], 0)
        again = self.next_step([], "--objective", "harden-to-signoff")
        self.assertEqual(again["action"], "audit", again)
        self.assertEqual([(x["id"], x["checked"]) for x in again["work"]], [("T-902", True)])
        more = (finding, "AUD-ARCH-002 | 🟠 | mở | lỗi khác | đo được: y | `true` | —")
        self.audit_book(self.git("rev-parse", "HEAD"), more)
        self.assertEqual(self.loop("verify", "--all")[0], 0)
        out = self.next_step([], "--objective", "harden-to-signoff")
        self.assertEqual(out["action"], "audit", out)  # nguồn của T-902 chưa ghi đóng: trước việc mới
        self.assertEqual([(x["id"], x["planned"]) for x in out["work"]], [("T-902", True), ("T-903", False)])
        fixed = (finding.replace("| mở |", "| đã sửa |").removesuffix("—") + "đã sửa ở #1", more[1])
        self.audit_book(self.git("rev-parse", "HEAD"), fixed)
        self.assertEqual(self.loop("verify", "--all")[0], 0)
        out = self.next_step([], "--objective", "harden-to-signoff")
        self.assertEqual(out["action"], "budget", out)  # sửa một, phát hiện một: hai đợt 1 → 1 → 1 (FLOW-13 thắng)
        self.assertEqual([(x["id"], x["planned"]) for x in out["work"]], [("T-903", False)])

    @functools.cached_property
    def outside(self) -> Path:
        return Path(self.enterContext(tempfile.TemporaryDirectory()))

    def harden_done(self) -> None:
        """Đợt `done` đã kiểm lại cuối, sổ sạch phủ tới HEAD, không việc harden nào, cây sạch (tick PLAN đã commit — như
        `release-check` hàng `tree` đòi): chỉ còn cổng phát hành."""
        self.audit_book(self.git("rev-parse", "HEAD"))
        self.finish_batch()
        self.audit_book(self.git("rev-parse", "HEAD"))  # commit tick PLAN cùng sổ phủ tới HEAD đó
        self.assertEqual(self.loop("verify", "--all")[0], 0)

    def signoff(self, *extra: str, **release: Any) -> dict[str, Any]:
        """`next-step --objective harden-to-signoff` kèm JSON `release-check` (`release` rỗng → không truyền)."""
        args = ["--objective", "harden-to-signoff", *extra]
        if release:  # ngoài cây: file trong cây làm `release-check` FAIL `tree` và đổi vân tay (review #326)
            path = self.outside / "release.json"
            path.write_text(json.dumps({"head": self.git("rev-parse", "HEAD").strip(), **release}), encoding="utf-8")
            args += ["--release", str(path)]
        return self.next_step([], *args)

    @flow("FLOW-16")
    def test_flow_16_release_without_fails_builds_signoff_package(self) -> None:
        """Given harden hết việc gom được · When `next-step` không có/có `release-check` (`fails` rỗng, `human` có) · Then
        `release-check` rồi `signoff-package`: gói có `candidate_head` = HEAD, `evidence_fp`, `human_pending`; lý do nói
        CHƯA phát hành; không ghi GO-NO-GO, không đổi state. Đối chứng: `fails` còn → `replan`, không gói."""
        self.harden_done()
        self.assertEqual(self.signoff()["action"], "release-check")
        out = self.signoff(fails=[], human=["prod_switch"], verdict="GO (chờ người)")
        self.assertEqual(out["action"], "signoff-package", out)
        pkg = out["package"]
        self.assertEqual(pkg["candidate_head"], self.git("rev-parse", "HEAD").strip())
        self.assertRegex(pkg["evidence_fp"], r"^[0-9a-f]{64}$")
        self.assertEqual(pkg["human_pending"], ["prod_switch"])
        self.assertIn("CHƯA phát hành", out["reason"])
        self.assertNotIn("đã phát hành", out["reason"])
        self.assertEqual(list(self.repo.rglob("GO-NO-GO*")), [])
        out = self.signoff(fails=["review_debt"], human=[], verdict="NO-GO")
        self.assertEqual((out["action"], out["package"]), ("replan", None))

    @flow("FLOW-17")
    def test_flow_17_code_change_expires_package_go_no_go_does_not(self) -> None:
        """Given gói nghiệm thu từ FLOW-16 · When commit chỉ GO-NO-GO/DECISIONS → gói còn hiệu lực (vân tay theo nội dung,
        không theo SHA HEAD); When sửa mã (commit, sổ quét lại) → gói hết hạn, `release-check`, nêu file mã đổi."""
        self.harden_done()
        out = self.signoff(fails=[], human=["prod_switch"], verdict="GO (chờ người)")
        pkg = self.outside / "package.json"
        pkg.write_text(json.dumps(out), encoding="utf-8")
        (self.repo / "docs" / "ops" / "GO-NO-GO-v1.md").write_text("# GO\n\nKý: chủ dự án\n", encoding="utf-8")
        (self.repo / "docs" / "autopilot" / "DECISIONS.md").write_text("# D\n\n- D-001 ký\n", encoding="utf-8")
        (self.repo / "PROGRESS.md").write_text(
            "# P\n\n- ký GO-NO-GO\n", encoding="utf-8"
        )  # commit cuối mọi PR (review #326)
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "ký GO-NO-GO")
        self.assertEqual(self.loop("verify", "--all")[0], 0)
        kept = self.signoff("--package", str(pkg))
        self.assertEqual((kept["action"], kept["package"]), ("signoff-package", out["package"]), kept)
        self.assertIn("còn hiệu lực", kept["reason"])
        prs = str(self.repo / ".autopilot" / "prs.json")  # `[]` do `next_step` ghi
        rc, text, err = self.loop("next-step", "--objective", "harden-to-signoff", "--prs", prs, "--package", str(pkg))
        self.assertEqual(rc, 0, err)
        self.assertIn("  gói: {", text)
        decisions = self.repo / "docs" / "autopilot" / "DECISIONS.md"
        decisions.write_text("# D\n\n- D-001 ký\n- D-002 chưa commit\n", encoding="utf-8")  # như `loop decide` vừa ghi
        (self.repo / "PROGRESS.md").write_text("# P\n\n- bàn giao chưa commit\n", encoding="utf-8")
        self.assertEqual(self.loop("verify", "--all")[0], 0)
        self.assertEqual(self.signoff("--package", str(pkg))["action"], "signoff-package")
        stray = self.repo / "tools" / "new.py"  # file mã chưa track cũng là bằng chứng đổi
        stray.parent.mkdir()
        stray.write_text("x = 1\n", encoding="utf-8")
        self.assertEqual(self.loop("verify", "--all")[0], 0)
        out_new = self.signoff("--package", str(pkg))
        self.assertEqual(out_new["action"], "release-check", out_new)
        self.assertIn("tools/new.py", out_new["reason"])
        stray.unlink()
        (self.repo / "app.py").write_text("x = 2\n", encoding="utf-8")
        self.git("add", "app.py")
        self.git("commit", "-q", "-m", "sửa mã sau gói")
        self.audit_book(self.git("rev-parse", "HEAD"))
        self.assertEqual(self.loop("verify", "--all")[0], 0)
        gone = self.signoff("--package", str(pkg))
        self.assertEqual((gone["action"], gone["package"]), ("release-check", None), gone)
        self.assertIn("gói nghiệm thu hết hạn:", gone["reason"])
        self.assertIn("app.py", gone["reason"])

    def write(self, rel: str, text: str) -> Path:
        path = self.repo / rel
        path.write_text(text, encoding="utf-8")
        return path

    def perf_compare(self, before: str, after: str, *extra: str) -> tuple[int, str]:
        """`xt.py perf compare` trong repo tạm; `SystemExit` của argparse → mã thoát + chữ thông báo."""
        with chdir(self.repo):
            try:
                rc, out, err = run_main("perf", "compare", *extra, before, after)
            except SystemExit as e:
                return (e.code if isinstance(e.code, int) else 2), f"SystemExit {e.code}"
        return rc, out + err

    @flow("FLOW-18")
    def test_flow_18_perf_compare_refuses_ms_vs_s(self) -> None:
        """Given hai mẫu v2 đủ trường, giống hệt trừ `unit`: before `ms` (~100), after `s` (~0,1) — cô lập R2 ·
        When `perf compare before after` · Then exit 2 và thông báo có "không đủ điều kiện so" và `unit` (không chỉ exit 2:
        argparse lỗi cũng 2). Đối chứng: cùng `unit` → so được (exit 0, `improved`)."""
        before = self.perf("b.json", **{**PERF_META, "unit": "ms"}, samples=SAMPLES_MS)
        after = self.perf("a.json", **PERF_META, samples=SAMPLES_S)
        rc, text = self.perf_compare(before, after)
        self.assertEqual(rc, 2, text)
        self.assertIn(REFUSE, text)
        self.assertIn("unit", text)
        same = self.perf("a-ms.json", **{**PERF_META, "unit": "ms"}, samples=SAMPLES_S)
        self.assertEqual(self.perf_compare(before, same)[0], 0)

    @flow("FLOW-19")
    def test_flow_19_perf_compare_refuses_by_role(self) -> None:
        """Given hai mẫu v2 giống nhau trừ một điều · When `perf compare` · Then exit 2 và "không đủ điều kiện so" cho:
        (a) before `dirty: true`; (b) `--base` là SHA khác `before.head`; (c) `harness_sha256` khác. Đối chứng: không lệch,
        `--base` đúng SHA hoặc ref trỏ về nó (`HEAD~1`), after `dirty` (candidate chưa commit) → so được, exit 0."""
        sha_a = self.git("rev-parse", "HEAD").strip()  # commit thật: `--base` có thể kiểm bằng `rev-parse`
        (self.repo / "later.txt").write_text("1\n", encoding="utf-8")
        self.git("add", "later.txt")
        self.git("commit", "-q", "-m", "later")
        sha_b = self.git("rev-parse", "HEAD").strip()
        meta = {**PERF_META, "head": sha_a}
        cases = {
            "dirty": ({"dirty": True}, {}, (), 2),
            "base": ({}, {}, ("--base", sha_b), 2),
            "harness": ({}, {"harness_sha256": "2" * 64}, (), 2),
            "ok": ({}, {}, (), 0),
            "ok-base-sha": ({}, {}, ("--base", sha_a), 0),
            "ok-base-ref": ({}, {"dirty": True, "head": sha_b}, ("--base", "HEAD~1"), 0),
        }
        for name, (b_over, a_over, extra, want) in cases.items():
            with self.subTest(name):
                before = self.perf(f"b-{name}.json", **{**meta, **b_over}, samples=SAMPLES_MS)
                after = self.perf(f"a-{name}.json", **{**meta, **a_over}, samples=[x * 0.5 for x in SAMPLES_MS])
                rc, text = self.perf_compare(before, after, *extra)
                self.assertEqual(rc, want, text)
                self.assertEqual(REFUSE in text, want == 2, text)


# --------------------------------------------------------------------------- perf trial (ADR-0071 §10, T-3700)
# Dự án đồ chơi: chỉ số chính tất định `cost(1000)` (gốc 3 × 1000 + 500 = 3500, càng thấp càng tốt), chỉ số phụ `mem` =
# `BUF` (trần 1000, `regress` 0), held-out từ hạt giống lúc finish. "Máy chủ" là repo bare `origin` (nhánh mặc định
# `main`, `ls-remote --symref` trả được); cây agent là clone ở nhánh `opt`; người bảo trì đẩy `main` từ clone riêng.
# Mọi lệnh gọi `ROOT/scripts/xt.py perf trial …` THẬT qua subprocess (D-363: coverage tính được); bản sao cùng byte ở
# `TOOL` commit trong gốc, nên neo công cụ từ blob gốc (§5) không `exec` sang bản khác. Tên trường sổ theo ADR §3/§4
# (`id`, `phase`, `base_sha`, `fp_start`, `verdict`, `rounds`, `candidate_tree`, `event`, `reason`).

TRIAL_ARGS = ("--hypothesis", "bỏ vòng thừa trong cost", "--falsifier", "primary > -5%")
HOT = (
    "from other import EXTRA\n\nK = 3\nBUF = 100\n\n\ndef compute(n):\n    total = 0\n    for i in range(n):\n"
    "        total += i\n    return total\n\n\ndef cost(n):\n    return n * K + EXTRA\n"
)
SHORTCUT = HOT.replace("    return n * K + EXTRA", "    return 1 if n == 1000 else n * K + EXTRA")  # hard-code N bộ đo
HELD_RANGE, HELD_N = (2000, 5000), 5  # input held-out: HELD_N số KHÁC NHAU trong khoảng (`heldout_gen.py`)
TOOL = ".xtemplates/scripts/xt.py"  # đường `xt.py` của khung ở dự án đích (install.py)
XT = ROOT / "scripts" / "xt.py"  # công cụ được chạy (D-363) — cùng byte với bản ở `TOOL` của gốc
GIT_ID = ("-c", "user.name=t", "-c", "user.email=t@example.invalid", "-c", "commit.gpgsign=false")
# FLOW-36: chết đúng lúc `git stash push` (sau dòng `decide`, trước thu hồi) — như FLOW-08, không phụ thuộc tên hàm nội bộ.
CRASH_AT_STASH = (
    "import os, subprocess, sys\n"
    "sys.path.insert(0, sys.argv[1])\n"
    "import xt\n"
    "real = subprocess.Popen\n"
    "class Crash(real):\n"
    "    def __init__(self, args, *a, **k):\n"
    "        if not isinstance(args, (str, bytes)) and 'stash' in args and 'push' in args:\n"
    "            os._exit(9)\n"
    "        super().__init__(args, *a, **k)\n"
    "subprocess.Popen = Crash\n"
    "sys.exit(xt.main(sys.argv[2:]))\n"
)


def _hang(ctl: Path, marker: str) -> str:
    """Đoạn mã của script đo: còn file `ctl/marker` thì báo `ctl/hanging` rồi chờ — ca kill/chen ngang giữa lượt."""
    m, h = str(ctl / marker), str(ctl / "hanging")
    return f"if os.path.exists({m!r}):\n    open({h!r}, 'w').close()\n    while os.path.exists({m!r}):\n        time.sleep(0.05)\n"


def trial_files(ctl: Path) -> dict[str, str]:
    """File của gốc; script đo ghi dấu vết ra `ctl` (đường tuyệt đối ngoài mọi cây)."""
    head = "import os, sys, time\nsys.path.insert(0, 'src')\n"
    dirty = str(ctl / "dirty")
    return {
        ".gitignore": ".autopilot/\n.cache/\n.venv/\nnode_modules/\n__pycache__/\nscratch.log\n",
        "src/hot.py": HOT,
        "src/other.py": "EXTRA = 500\n",
        "src/notes.txt": "ghi chú\n",
        "docs/autopilot/PERF-LOG.md": "# PERF-LOG\n\nGhi chú của người.\n",
        "bench.py": head
        + _hang(ctl, "hang")
        + f"import hot\nif os.path.exists({dirty!r}) and hot.K == 3:\n"  # chỉ cây gốc/`start_head` (K = 3) bị bẩn
        + "    with open('src/hot.py', 'a', encoding='utf-8') as f:\n        f.write('# bẩn\\n')\nprint(hot.cost(1000))\n",
        "mem.py": head + "import hot\nprint(hot.BUF)\n",
        "equiv.py": head + "import hot\nassert hot.compute(10) == 45\n",
        "heldout_gen.py": head
        + "import random\nseed = sys.stdin.read().strip()\n"
        + f"with open({str(ctl / 'seeds.log')!r}, 'a', encoding='utf-8') as f:\n    f.write(seed + '\\n')\n"
        + f"r = random.Random(seed)\nprint('\\n'.join(map(str, r.sample(range{HELD_RANGE}, {HELD_N}))))\n",
        "heldout_run.py": head + _hang(ctl, "hang-heldout") + "import hot\nprint(hot.cost(int(sys.argv[1])))\n",
        "probe.py": head
        + f"with open({str(ctl / 'probe.env')!r}, 'a', encoding='utf-8') as f:\n"
        + "    f.write(''.join(f'{k}={v}\\n' for k, v in os.environ.items()))\n"
        + "import hot\nprint(os.path.realpath(hot.__file__))\n",
    }


def trial_config(**over: Any) -> dict[str, Any]:
    """`perf/trial.json` (ADR-0071 §1); dict mới mỗi lần gọi — sửa lồng nhau không rò sang ca khác."""
    cfg: dict[str, Any] = {
        "schema": 1,
        "setup": "true",
        "locked": ["bench.py", "mem.py", "equiv.py", "heldout_*.py", "probe.py"],
        "metric": {"cmd": "python3 bench.py", "kind": "exact", "unit": "lệnh", "higher_is_better": False, "runs": 3},
        "secondary": [
            {"name": "mem", "cmd": "python3 mem.py", "kind": "exact", "unit": "B", "higher_is_better": False}
            | {"ceiling": 1000, "regress": 0}
        ],
        "target": "primary <= -20%",
        "budget": 20,
        "equiv": "python3 equiv.py",
        "heldout": {"gen": "python3 heldout_gen.py", "cmd": "python3 heldout_run.py {input}"},
        "timeout": 120,
    }
    return {**cfg, **over}


class TrialFlowTest(TmpRepoCase):
    """Ca `perf trial` (ADR-0071 §10); `done=` ghi task làm ca xanh (T-3701…T-3706), không còn ID nào trong `XFAIL`."""

    def setUp(self) -> None:
        super().setUp()
        self.ctl = self.tmp / "ctl"
        self.ctl.mkdir()
        self.origin = self.tmp / "origin.git"
        self.run_git(self.tmp, "init", "-q", "--bare", "-b", "main", str(self.origin))
        self.init_repo()
        self.write_tree(self.repo, {**trial_files(self.ctl), "perf/trial.json": json.dumps(trial_config())})
        (self.repo / TOOL).parent.mkdir(parents=True)
        (self.repo / TOOL).write_bytes((ROOT / "scripts" / "xt.py").read_bytes())
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "gốc")
        self.git("remote", "add", "origin", str(self.origin))
        self.git("push", "-q", "-u", "origin", "main")
        self.git("remote", "set-head", "origin", "-a")
        self.git("checkout", "-q", "-b", "opt")
        self.base = self.git("rev-parse", "HEAD")
        self.enterContext(unittest.mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(self.repo)}))
        os.environ.pop("XT_PROGRESS_BASE", None)  # patch.dict khôi phục khi xong ca

    # ---- hạ tầng repo
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

    def maint(self) -> Path:
        """Clone của người bảo trì (đẩy `main` lên máy chủ — nhánh mặc định được bảo vệ, đổi qua review)."""
        maint = self.tmp / "maint"
        if not maint.exists():
            self.run_git(self.tmp, "clone", "-q", str(self.origin), str(maint))
        return maint

    def maintain(self, files: dict[str, str], msg: str = "bảo trì") -> str:
        """Người bảo trì commit `files` lên `main` của máy chủ; cây agent `fetch` (chưa merge)."""
        maint = self.maint()
        self.write_tree(maint, files)
        self.run_git(maint, "add", "-A")
        self.run_git(maint, "commit", "-q", "-m", msg)
        self.run_git(maint, "push", "-q", "origin", "HEAD:main")
        self.git("fetch", "-q", "origin")
        return self.run_git(maint, "rev-parse", "HEAD")

    def republish(self, files: dict[str, str]) -> None:
        """Gốc mới trước mọi lần thử (vd cấu hình khác): `main` đi tiếp, nhánh `opt` dựng lại từ đó."""
        self.maintain(files, "gốc mới")
        self.git("checkout", "-q", "-B", "opt", "origin/main")
        self.base = self.git("rev-parse", "HEAD")

    def add_submodule(self) -> Path:
        """Repo con (`f.txt`) gắn ở `vendor/sub` qua người bảo trì; cây agent `submodule update --init`."""
        sub = self.tmp / "sub"
        self.run_git(self.tmp, "init", "-q", "-b", "main", str(sub))
        (sub / "f.txt").write_text("a\n", encoding="utf-8")
        self.run_git(sub, "add", "f.txt")
        self.run_git(sub, "commit", "-q", "-m", "f")
        self.run_git(self.maint(), "submodule", "add", "-q", str(sub), "vendor/sub")
        self.republish({})
        self.run_git(self.repo, "submodule", "update", "--init", "-q")
        return self.repo / "vendor" / "sub"

    # ---- lệnh và sổ
    def trial(self, *args: str, env: dict[str, str] | None = None) -> tuple[int, str, str]:
        """`xt.py perf trial …` (bản ở gốc) trong cây agent. Lệnh con chưa có → đỏ ngay, không lẫn với exit 2 từ chối."""
        r = subprocess.run(
            [sys.executable, str(XT), "perf", "trial", *args],
            cwd=self.repo,
            env={**os.environ, **(env or {})},
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )
        self.assertNotIn("invalid choice: 'trial'", r.stderr, "chưa có `xt.py perf trial` (ADR-0071)")
        self.assertNotIn("chưa triển khai", r.stderr, "lệnh con chưa có — exit 2 của nó không phải từ chối thật")
        return r.returncode, r.stdout, r.stderr

    def ok(self, *args: str) -> str:
        rc, out, err = self.trial(*args)
        self.assertEqual(rc, 0, f"perf trial {' '.join(args)}: {out}{err}")
        return out

    def start_args(self, *hotspots: str, extra: tuple[str, ...] = TRIAL_ARGS) -> tuple[str, ...]:
        """`start --hotspot …` (mặc định `src/hot.py`) + giả thuyết/falsifier."""
        return ("start", *(a for h in hotspots or ("src/hot.py",) for a in ("--hotspot", h)), *extra)

    def start(
        self, *hotspots: str, extra: tuple[str, ...] = TRIAL_ARGS, env: dict[str, str] | None = None
    ) -> tuple[int, str, str]:
        return self.trial(*self.start_args(*hotspots, extra=extra), env=env)

    def started(self, *hotspots: str, extra: tuple[str, ...] = TRIAL_ARGS) -> str:
        """`start` phải nhận (exit 0); trả `id` lần thử (`PT-NNNN`)."""
        rc, out, err = self.start(*hotspots, extra=extra)
        self.assertEqual(rc, 0, out + err)
        return str(self.tstate()["id"])

    def tstate(self) -> dict[str, Any]:
        data = json.loads((self.repo / ".autopilot" / "perf-trial.json").read_text(encoding="utf-8"))
        assert isinstance(data, dict)
        return data

    def rows(self, event: str = "decide") -> list[dict[str, Any]]:
        path = self.repo / ".autopilot" / "perf-trials.jsonl"
        lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
        return [r for r in map(json.loads, lines) if r.get("event") == event]

    def decided(self, tid: str) -> list[dict[str, Any]]:
        return [r for r in self.rows() if r.get("id") == tid]

    def why(self, row: dict[str, Any]) -> str:
        return f"{row.get('verdict')} {json.dumps(row.get('reason'), ensure_ascii=False)}"

    def ledger(self) -> tuple[bytes | None, ...]:
        """Byte của state + sổ — "không ghi gì" so bằng cái này."""
        files = (self.repo / ".autopilot" / n for n in ("perf-trial.json", "perf-trials.jsonl"))
        return tuple(f.read_bytes() if f.exists() else None for f in files)

    def fp(self) -> str | None:
        return xt.tree_fingerprint(self.repo)

    def hot(self, k: int = 3, buf: int = 100, tail: str = "") -> None:
        """Candidate trong `src/hot.py`: K = 2 là `improved` thật (3500 → 2500), `tail` nối cuối file."""
        self.put("src/hot.py", HOT.replace("K = 3", f"K = {k}").replace("BUF = 100", f"BUF = {buf}") + tail)

    def perf_log(self) -> str:
        return (self.repo / "docs" / "autopilot" / "PERF-LOG.md").read_text(encoding="utf-8")

    def abort_round(self, hotspots: tuple[str, ...], n: int) -> None:
        """`n` lần thử không giữ (`abort`, mỗi lệnh một tiến trình — restart) trên `hotspots`."""
        for i in range(n):
            self.started(*hotspots)
            self.hot(tail=f"# thử {i}\n")
            self.ok("abort", "--reason", f"thử {i}")

    def refused(self, *args: str, code: int = 2, env: dict[str, str] | None = None) -> str:
        """`perf trial <args>` bị từ chối đúng `code`; sổ, state, HEAD và cây không đổi. Trả stdout + stderr."""
        before, fp0, head = self.ledger(), self.fp(), self.git("rev-parse", "HEAD")
        rc, out, err = self.trial(*args, env=env)
        self.assertEqual(rc, code, out + err)
        self.assertEqual((self.ledger(), self.fp(), self.git("rev-parse", "HEAD")), (before, fp0, head))
        return out + err

    def spawn(self, *args: str, marker: str = "hang") -> "subprocess.Popen[bytes]":
        """`perf trial …` ở tiến trình riêng (nhóm tiến trình mới); script đo treo khi còn `ctl/marker` — chờ tới lúc treo."""
        hanging = self.ctl / "hanging"
        hanging.unlink(missing_ok=True)
        (self.ctl / marker).write_text("1", encoding="utf-8")
        self.addCleanup(self.release, marker)
        proc = subprocess.Popen(
            [sys.executable, str(XT), "perf", "trial", *args],
            cwd=self.repo,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        self.addCleanup(self.kill, proc)
        deadline = time.monotonic() + 60
        while proc.poll() is None and not hanging.exists() and time.monotonic() < deadline:
            time.sleep(0.05)
        self.assertTrue(hanging.exists(), f"`perf trial {' '.join(args)}` không tới bước đo (exit {proc.poll()})")
        return proc

    def kill(self, proc: "subprocess.Popen[bytes]") -> None:
        """SIGKILL cả nhóm tiến trình (crash giữa lượt); đã thoát thì thôi."""
        if proc.poll() is None:
            with contextlib.suppress(ProcessLookupError):
                os.killpg(proc.pid, signal.SIGKILL)
            proc.wait()

    def release(self, marker: str = "hang") -> None:
        (self.ctl / marker).unlink(missing_ok=True)

    # ---- ca
    @flow("FLOW-20", done="T-3703")
    def test_flow_20_neutral_candidate_is_reverted_exactly(self) -> None:
        """Given lần thử mở (điểm nóng `src/hot.py`, `src/extra.py`); candidate `neutral` (chú thích + file mới chưa
        track); file người dùng ngoài danh sách: `.autopilot/note.txt`, `scratch.log` bị ignore · When `finish` · Then
        exit 1, vân tay = lúc start, `git status` sạch, hai file người dùng còn nguyên, dòng `decide` không `kept`;
        `perf trial log` ghi lần thử vào PERF-LOG — đường thu hồi. Tái hiện: chưa có `finish`/`log`."""
        fp0 = self.fp()
        tid = self.started("src/hot.py", "src/extra.py")
        self.put(".autopilot/note.txt", "của người dùng\n")
        self.put("scratch.log", "bị ignore\n")
        self.hot(tail="# chú thích\n")
        self.put("src/extra.py", "Y = 2\n")
        rc, out, err = self.trial("finish")
        self.assertEqual(rc, 1, out + err)
        self.assertEqual((self.fp(), self.git("status", "--porcelain")), (fp0, ""))
        self.assertEqual((self.repo / ".autopilot" / "note.txt").read_text(encoding="utf-8"), "của người dùng\n")
        self.assertEqual((self.repo / "scratch.log").read_text(encoding="utf-8"), "bị ignore\n")
        self.assertEqual(len(self.decided(tid)), 1)
        self.assertNotEqual(self.decided(tid)[0]["verdict"], "kept")
        self.ok("log")
        self.assertIn(tid, self.perf_log())

    @flow("FLOW-21", done="T-3706")
    def test_flow_21_resume_after_tree_changed_is_incomplete(self) -> None:
        """Given candidate `improved`, `finish` bị SIGKILL giữa lượt đo, rồi cây đổi (≠ `candidate_fp`) · When `finish
        --resume` · Then thu hồi (exit 1), một dòng `decide` `verdict: incomplete`, vân tay = lúc start (R2)."""
        fp0 = self.fp()
        tid = self.started()
        self.hot(k=2)
        self.kill(self.spawn("finish"))
        self.release()
        self.hot(k=2, tail="# sửa sau crash\n")
        rc, out, err = self.trial("finish", "--resume")
        self.assertEqual(rc, 1, out + err)
        self.assertEqual([r["verdict"] for r in self.decided(tid)], ["incomplete"])
        self.assertEqual(self.fp(), fp0)

    @flow("FLOW-21", done="T-3706")
    def test_flow_21_second_resume_is_incomplete(self) -> None:
        """Given `finish` bị kill giữa lượt, `finish --resume` cũng bị kill giữa lượt (`resumes` = 1), cây không đổi ·
        When `finish --resume` lần hai · Then không đo lại lần ba: thu hồi (exit 1), một dòng `incomplete`, vân tay = lúc
        start — đo lại tới khi may không làm được quá một lần."""
        fp0 = self.fp()
        tid = self.started()
        self.hot(k=2)
        self.kill(self.spawn("finish"))
        self.kill(self.spawn("finish", "--resume"))
        self.release()
        rc, out, err = self.trial("finish", "--resume")
        self.assertEqual(rc, 1, out + err)
        self.assertEqual([r["verdict"] for r in self.decided(tid)], ["incomplete"])
        self.assertEqual(self.fp(), fp0)

    @flow("FLOW-22", done="T-3701")
    def test_flow_22_three_non_kept_survive_restart(self) -> None:
        """Given ba lần thử `abort` trên `src/hot.py`, mỗi lệnh một tiến trình (restart: đếm chỉ ở `perf-trials.jsonl`) ·
        When `start --hotspot src/hot.py` · Then exit 3 nêu đường, sổ/cây không đổi; đường khác vẫn nhận (exit 0)."""
        self.abort_round(("src/hot.py",), 3)
        self.assertIn("src/hot.py", self.refused(*self.start_args("src/hot.py"), code=3))
        self.started("src/other.py")

    @flow("FLOW-23", done="T-3704")
    def test_flow_23_secondary_over_ceiling_reverts(self) -> None:
        """Given `mem` trần 1000 (mức lùi nới 10000 % để cô lập trần), candidate `improved` ở chỉ số chính nhưng `BUF =
        2000` · When `finish` · Then thu hồi (exit 1), vân tay = lúc start, lý do nêu `mem`."""
        cfg = trial_config()
        cfg["secondary"][0]["regress"] = 10000
        self.republish({"perf/trial.json": json.dumps(cfg)})
        fp0 = self.fp()
        tid = self.started()
        self.hot(k=2, buf=2000)
        rc, out, err = self.trial("finish")
        self.assertEqual(rc, 1, out + err)
        self.assertEqual(self.fp(), fp0)
        self.assertIn("mem", self.why(self.decided(tid)[0]))

    @flow("FLOW-27", done="T-3705")
    def test_flow_27_improved_candidate_is_kept_and_next_start_accepts(self) -> None:
        """Given candidate K = 2 (`improved` so với gốc và `start_head`), tương đương + held-out xanh · When `finish` ·
        Then exit 0, candidate còn trong cây; commit nó → `candidate_tree` của dòng `decide` = `HEAD^{tree}` (cây giữ);
        dòng `decide` mang hạt giống held-out đã dùng (không giữ khi held-out chưa chạy); `start` kế nhận — đường giữ."""
        tid = self.started()
        self.hot(k=2)
        rc, out, err = self.trial("finish")
        self.assertEqual(rc, 0, out + err)
        self.assertIn("K = 2", (self.repo / "src" / "hot.py").read_text(encoding="utf-8"))
        self.git("commit", "-q", "-am", "giữ")
        row = self.decided(tid)[0]
        self.assertIn((self.ctl / "seeds.log").read_text(encoding="utf-8").split()[-1], json.dumps(row))
        self.assertEqual((row["verdict"], row["candidate_tree"]), ("kept", self.git("rev-parse", "HEAD^{tree}")))
        self.started()

    @flow("FLOW-28", done="T-3703")
    def test_flow_28_commit_mid_trial_refused_untouched(self) -> None:
        """Given lần thử mở, candidate đã commit (`HEAD ≠ start_head`) · When `finish` · Then exit 2, HEAD/cây/sổ không
        đổi, không mục stash — baseline bị lái bằng commit giữa chừng."""
        self.started()
        self.hot(k=2)
        self.git("commit", "-q", "-am", "lén commit")
        self.assertIn("start_head", self.refused("finish"))
        self.assertEqual(self.git("stash", "list"), "")

    @flow("FLOW-28", done="T-3701")
    def test_flow_28_moved_default_branch_needs_merge(self) -> None:
        """Given `start` + `abort` ở gốc B, rồi `main` của máy chủ đi tiếp tới C và cây agent `fetch` · When `start` ·
        Then exit 2 "gộp nhánh mặc định trước" (gốc = đầu nhánh máy chủ, không merge-base — D-366, nhánh cũ không hạ gốc
        về B); gộp C rồi `start` → exit 0, `base_sha` = C (vòng mới)."""
        self.started()
        self.ok("abort", "--reason", "thử ghim")
        tip = self.maintain({"src/other.py": "EXTRA = 400\n"}, "main đi tiếp")
        rc, out, err = self.start()
        self.assertEqual(rc, 2, out + err)
        self.assertIn("gộp nhánh mặc định trước", err)
        self.git("merge", "-q", "--ff-only", "origin/main")
        self.started()
        self.assertEqual(self.tstate()["base_sha"], tip)

    @flow("FLOW-28", done="T-3703")
    def test_flow_28_measured_base_tree_dirtied_refused(self) -> None:
        """Given candidate K = 2; bộ đo (khoá, từ gốc) sửa `src/hot.py` của cây nó chạy khi K = 3 (cây gốc và
        `start_head`) · When `finish` · Then exit 2 (danh sách file cây gốc khác sau lượt), candidate còn nguyên, không
        dòng `decide`."""
        self.started()
        self.hot(k=2)
        (self.ctl / "dirty").write_text("1", encoding="utf-8")
        rc, out, err = self.trial("finish")
        self.assertEqual(rc, 2, out + err)
        self.assertIn("K = 2", (self.repo / "src" / "hot.py").read_text(encoding="utf-8"))
        self.assertEqual(self.rows(), [])

    @flow("FLOW-29", done="T-3703")
    def test_flow_29_candidate_edits_locked_file_is_tampered(self) -> None:
        """Given candidate K = 2 kèm sửa `bench.py` (khoá) để in số nhỏ · When `finish` · Then thu hồi (exit 1),
        `verdict: tampered`, vân tay = lúc start (`bench.py` về như gốc)."""
        fp0 = self.fp()
        tid = self.started()
        self.hot(k=2)
        self.put("bench.py", "print(1)\n")
        rc, out, err = self.trial("finish")
        self.assertEqual(rc, 1, out + err)
        self.assertEqual(self.decided(tid)[0]["verdict"], "tampered")
        self.assertEqual(self.fp(), fp0)

    @flow("FLOW-29", done="T-3703")
    def test_flow_29_sitecustomize_outside_glob_is_tampered(self) -> None:
        """Given candidate thêm `src/sitecustomize.py` (ngoài glob `locked` của dự án — review #440 lách test tương đương
        bằng nó) · When `finish` · Then `tampered` nhờ khoá mặc định `**/sitecustomize.py`, thu hồi (exit 1)."""
        fp0 = self.fp()
        tid = self.started()
        self.hot(k=2)
        self.put("src/sitecustomize.py", "import builtins\n")
        rc, out, err = self.trial("finish")
        self.assertEqual(rc, 1, out + err)
        self.assertEqual(self.decided(tid)[0]["verdict"], "tampered")
        self.assertEqual(self.fp(), fp0)

    @flow("FLOW-29", done="T-3703")
    def test_flow_29_ignored_pth_in_agent_venv_does_not_fool_measure(self) -> None:
        """Given mọi lệnh đo dùng `.venv/bin/python`, `setup` dựng `.venv` trong từng cây; `.pth` bị ignore trong `.venv`
        cây agent nạp `hot` giả (đo tại chỗ in 19 — bẫy kiểm có thật) · When `finish` với candidate `neutral` · Then không
        giữ (exit 1): số đo từ cây dựng lại, không từ cây agent."""
        py = ".venv/bin/python"
        cfg = trial_config(setup="python3 -m venv --without-pip .venv", equiv=f"{py} equiv.py")
        cfg["metric"]["cmd"], cfg["secondary"][0]["cmd"] = f"{py} bench.py", f"{py} mem.py"
        cfg["heldout"]["cmd"] = f"{py} heldout_run.py {{input}}"
        self.republish({"perf/trial.json": json.dumps(cfg)})
        subprocess.run([sys.executable, "-m", "venv", "--without-pip", str(self.repo / ".venv")], check=True)
        site = subprocess.run(
            [str(self.repo / py), "-c", "import site; print(site.getsitepackages()[0])"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        fake = self.put(
            ".cache/hot.py",
            "K = 3\nBUF = 100\n\n\ndef compute(n):\n    return n * (n - 1) // 2\n\n\ndef cost(n):\n    return 19\n",
        )
        load = f"import importlib.util as u, sys; s = u.spec_from_file_location('hot', {str(fake)!r}); "
        load += "m = u.module_from_spec(s); s.loader.exec_module(m); sys.modules['hot'] = m\n"
        Path(site, "evil.pth").write_text(load, encoding="utf-8")
        trap = subprocess.run([str(self.repo / py), "bench.py"], cwd=self.repo, capture_output=True, text=True)
        self.assertEqual(trap.stdout.strip(), "19", trap.stderr)
        tid = self.started()
        self.hot(tail="# chú thích\n")
        rc, out, err = self.trial("finish")
        self.assertEqual(rc, 1, out + err)
        self.assertNotEqual(self.decided(tid)[0]["verdict"], "kept")

    @flow("FLOW-30", done="T-3705")
    def test_flow_30_hardcoded_bench_input_fails_heldout(self) -> None:
        """Given candidate trả 1 khi `n == 1000` (đúng input bộ đo: −99,97 %) · When `finish` · Then held-out (input từ
        hạt giống lúc finish, 2000…4999) không `improved` so với `start_head` lẫn gốc → thu hồi (exit 1), lý do nêu
        held-out, vân tay = lúc start."""
        fp0 = self.fp()
        tid = self.started()
        self.put("src/hot.py", SHORTCUT)
        rc, out, err = self.trial("finish")
        self.assertEqual(rc, 1, out + err)
        self.assertEqual(self.fp(), fp0)
        self.assertIn("heldout", self.why(self.decided(tid)[0]).replace("-", "").replace("_", ""))

    @flow("FLOW-31", done="T-3701")
    def test_flow_31_start_needs_hypothesis_falsifier_clean_tree(self) -> None:
        """Given cây sạch · When `start` thiếu/rỗng giả thuyết, thiếu falsifier, falsifier sai dạng hoặc chỉ số lạ; cây
        bẩn (sửa file track, file mới chưa track) · Then exit 2, không ghi gì (không state, không sổ). Đối chứng: đủ và
        sạch → exit 0, state ghi giả thuyết, falsifier, `fp_start` = vân tay cây, `start_head` = HEAD, `base_sha` = gốc."""
        bad = {
            "thiếu giả thuyết": ("--falsifier", "primary > -5%"),
            "giả thuyết rỗng": ("--hypothesis", "  ", "--falsifier", "primary > -5%"),
            "thiếu falsifier": ("--hypothesis", "h"),
            "falsifier sai dạng": ("--hypothesis", "h", "--falsifier", "nhanh hơn"),
            "falsifier chỉ số lạ": ("--hypothesis", "h", "--falsifier", "rss > 5%"),
        }
        for name, extra in bad.items():
            rc, out, err = self.start(extra=extra)
            self.assertEqual((rc, self.ledger()), (2, (None, None)), f"{name}: {out}{err}")
        for rel, text in {"src/hot.py": HOT + "# sửa\n", "src/new.py": "Z = 1\n"}.items():
            self.put(rel, text)
            self.assertIn(rel, self.refused(*self.start_args()))
            self.assertEqual(self.ledger(), (None, None))
            self.git("checkout", "-q", "--", "src/hot.py")
            (self.repo / "src" / "new.py").unlink(missing_ok=True)
        self.started()
        st = self.tstate()
        self.assertEqual((st["hypothesis"], st["falsifier"]), (TRIAL_ARGS[1], TRIAL_ARGS[3]))
        self.assertEqual((st["fp_start"], st["start_head"], st["base_sha"]), (self.fp(), self.base, self.base))

    @flow("FLOW-31", done="T-3705")
    def test_flow_31_falsifier_hit_reverts(self) -> None:
        """Given falsifier `primary > -50%`, candidate K = 2 (−28,6 % — `improved` nhưng không đạt điều giả thuyết hứa)
        · When `finish` · Then thu hồi (exit 1), lý do nêu falsifier, vân tay = lúc start."""
        fp0 = self.fp()
        tid = self.started(extra=("--hypothesis", "bỏ nửa chi phí", "--falsifier", "primary > -50%"))
        self.hot(k=2)
        rc, out, err = self.trial("finish")
        self.assertEqual(rc, 1, out + err)
        self.assertEqual(self.fp(), fp0)
        self.assertIn("falsifier", self.why(self.decided(tid)[0]))

    @flow("FLOW-32", done="T-3702")
    def test_flow_32_setup_resolving_outside_tree_refused(self) -> None:
        """Given `setup` (từ gốc) symlink `node_modules` của cây đo về cây agent · When `perf trial prepare` · Then exit 2
        trước khi đo, nêu `node_modules`; candidate còn nguyên, không dòng `decide`."""
        self.republish(
            {"perf/trial.json": json.dumps(trial_config(setup=f"ln -s {self.repo}/node_modules node_modules"))}
        )
        self.put("node_modules/pkg/index.js", "module.exports = 1\n")
        self.started()
        self.hot(k=2)
        rc, out, err = self.trial("prepare")
        self.assertEqual(rc, 2, out + err)
        self.assertIn("node_modules", out + err)
        self.assertIn("K = 2", (self.repo / "src" / "hot.py").read_text(encoding="utf-8"))
        self.assertEqual(self.rows(), [])

    @flow("FLOW-33", done="T-3703")
    def test_flow_33_submodule_edit_stops_after_stash(self) -> None:
        """Given candidate sửa `src/hot.py` (chú thích) và nội dung submodule `vendor/sub` · When `finish` · Then stash
        không đưa cây về `fp_start` → exit 4, in SHA stash, pha giữ `decided`, submodule vẫn bị sửa (không thử cách khác,
        `LOOP-STOP-025`)."""
        sub = self.add_submodule()
        self.started()
        self.hot(tail="# chú thích\n")
        (sub / "f.txt").write_text("b\n", encoding="utf-8")
        rc, out, err = self.trial("finish")
        self.assertEqual(rc, 4, out + err)
        self.assertRegex(out + err, r"\b[0-9a-f]{40}\b")
        self.assertEqual(self.tstate()["phase"], "decided")
        self.assertEqual((sub / "f.txt").read_text(encoding="utf-8"), "b\n")

    @flow("FLOW-34", done="T-3703")
    def test_flow_34_concurrent_finish_or_abort_refused(self) -> None:
        """Given candidate K = 2, một `finish` đang đo (bộ đo treo — chồng lấn chắc chắn, mạnh hơn barrier) · When `finish`
        và `abort` khác chen vào · Then cả hai exit 2 ngay (`perf-trial.lock`), sổ/cây không đổi; `finish` đầu đo xong,
        exit 0; đúng một dòng `decide`."""
        self.started()
        self.hot(k=2)
        first = self.spawn("finish")
        for args in (("finish",), ("abort", "--reason", "chen ngang")):
            rc, out, err = self.trial(*args)
            self.assertEqual(rc, 2, f"{args}: {out}{err}")
        self.release()
        self.assertEqual(first.wait(timeout=300), 0)
        self.assertEqual(len(self.rows()), 1)

    @flow("FLOW-35", done="T-3706")
    def test_flow_35_kill_mid_measure_resume_measures_once_more(self) -> None:
        """Given candidate K = 2, `finish` bị SIGKILL lúc chạy held-out (pha `measuring`, cây = `candidate_fp`) · When
        `finish` → exit 2 chỉ `--resume`; `finish --resume` · Then đo lại từ đầu, giữ (exit 0), đúng một dòng `decide` có
        `rounds: 2`, hạt giống của nó khác hạt giống lượt bị kill (bộ sinh ghi lại cả hai)."""
        tid = self.started()
        self.hot(k=2)
        self.kill(self.spawn("finish", marker="hang-heldout"))
        self.release("hang-heldout")
        rc, out, err = self.trial("finish")
        self.assertEqual(rc, 2, out + err)
        self.assertIn("--resume", out + err)
        self.ok("finish", "--resume")
        rows = self.decided(tid)
        self.assertEqual([(r["verdict"], r["rounds"]) for r in rows], [("kept", 2)])
        seeds = (self.ctl / "seeds.log").read_text(encoding="utf-8").split()
        self.assertGreaterEqual(len(seeds), 2, seeds)
        self.assertNotEqual(seeds[0], seeds[-1])
        self.assertIn(seeds[-1], json.dumps(rows[0]))

    @flow("FLOW-36", done="T-3706")
    def test_flow_36_kill_after_decide_resume_finishes_revert(self) -> None:
        """Given candidate `neutral`, `finish` chết (`os._exit(9)`) đúng lúc `git stash push` — sau dòng `decide`, trước
        thu hồi · When `finish` → exit 2 chỉ `--resume`; `finish --resume` · Then làm nốt thu hồi (exit 1), vân tay = lúc
        start, vẫn một dòng `decide`."""
        fp0 = self.fp()
        tid = self.started()
        self.hot(tail="# chú thích\n")
        r = subprocess.run(
            [sys.executable, "-c", CRASH_AT_STASH, str(XT.parent), "perf", "trial", "finish"],
            cwd=self.repo,
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )
        self.assertEqual(r.returncode, 9, r.stdout + r.stderr)
        self.assertEqual((self.tstate()["phase"], len(self.decided(tid))), ("decided", 1))
        self.assertIn("--resume", self.refused("finish"))
        rc, out, err = self.trial("finish", "--resume")
        self.assertEqual(rc, 1, out + err)
        self.assertEqual((self.fp(), len(self.decided(tid))), (fp0, 1))

    @flow("FLOW-37", done="T-3701")
    def test_flow_37_start_refuses_dirty_perf_log_and_base_flag(self) -> None:
        """Given cây sạch ở gốc · When `start` khi chỉ PERF-LOG bẩn (nối thêm — không miễn, D-360); `start --base HEAD`
        · Then exit 2, sổ/cây không đổi. Đối chứng: PERF-LOG về nguyên, không `--base` → exit 0."""
        log = self.repo / "docs" / "autopilot" / "PERF-LOG.md"
        orig = log.read_bytes()
        log.write_bytes(orig + "| PT-0001 | nối thêm |\n".encode())
        self.assertIn("PERF-LOG", self.refused(*self.start_args()))
        log.write_bytes(orig)
        self.refused(*self.start_args(extra=(*TRIAL_ARGS, "--base", "HEAD")))
        self.started()

    @flow("FLOW-37", done="T-3701")
    def test_flow_37_shortcut_commit_before_first_start_refused(self) -> None:
        """AUD-HAR-231 — Given commit đường tắt trước lần `start` đầu vòng (hard-code N của bộ đo trong `src/hot.py`;
        hoặc sửa `bench.py` khoá) nên `HEAD^{tree}` ≠ cây gốc · When `start` · Then exit 2, sổ/cây không đổi — đường tắt
        không thành `start_head` để candidate sau chỉ so với nó. Đối chứng: bỏ commit → exit 0."""
        for rel, text in {"src/hot.py": SHORTCUT, "bench.py": "print(1)\n"}.items():
            self.put(rel, text)
            self.git("commit", "-q", "-am", f"đường tắt {rel}")
            self.refused(*self.start_args())
            self.git("reset", "-q", "--hard", self.base)
        self.started()

    @flow("FLOW-37", done="T-3701")
    def test_flow_37_commit_after_log_tree_refused(self) -> None:
        """AUD-HAR-231 — Given lần thử `abort`, `perf trial log`, commit PERF-LOG (cây của sự kiện `log`), rồi commit lạ
        (đường tắt) · When `start` · Then exit 2 (`HEAD^{tree}` ≠ cây giữ gần nhất), sổ/cây không đổi. Đối chứng: bỏ
        commit lạ → exit 0."""
        self.started()
        self.ok("abort", "--reason", "thử")
        self.ok("log")
        self.git("commit", "-q", "-am", "PERF-LOG")
        self.put("src/hot.py", SHORTCUT)
        self.git("commit", "-q", "-am", "commit lạ")
        self.refused(*self.start_args())
        self.git("reset", "-q", "--hard", "HEAD~1")
        self.started()

    @flow("FLOW-38", done="T-3701")
    def test_flow_38_loosened_config_on_branch_is_not_base(self) -> None:
        """AUD-HAR-230 — Given agent commit `perf/trial.json` nới (`locked: []`, `equiv: "true"`, bộ đo `echo 1`) trên
        nhánh, đẩy nhánh lên máy chủ và trỏ `origin/HEAD` cục bộ về nó (`remote set-head`), đặt `XT_PROGRESS_BASE=HEAD`
        · When `start` (và `start --base HEAD`) · Then exit 2, sổ/cây không đổi: gốc = merge-base với nhánh mặc định do
        MÁY CHỦ báo (`ls-remote --symref`), không theo HEAD, biến môi trường hay ref cục bộ. Đối chứng: bỏ commit nới →
        exit 0, `base_sha` = gốc, `config_sha` = blob `perf/trial.json` ở gốc, `default_ref` là `main`."""
        loose = trial_config(locked=[], equiv="true", budget=999)
        loose["metric"]["cmd"] = "echo 1"
        self.put("perf/trial.json", json.dumps(loose))
        self.git("commit", "-q", "-am", "nới cấu hình")
        self.git("push", "-q", "origin", "opt")
        self.git("remote", "set-head", "origin", "opt")
        env = {"XT_PROGRESS_BASE": "HEAD"}
        self.refused(*self.start_args(), env=env)
        self.refused(*self.start_args(extra=(*TRIAL_ARGS, "--base", "HEAD")), env=env)
        self.git("reset", "-q", "--hard", self.base)
        rc, out, err = self.start(env=env)
        self.assertEqual(rc, 0, out + err)
        st = self.tstate()
        self.assertEqual(st["base_sha"], self.base)
        self.assertEqual(st["config_sha"], self.git("rev-parse", f"{self.base}:perf/trial.json"))
        self.assertIn("main", st["default_ref"])

    @flow("FLOW-38", done="T-3701")
    def test_flow_38_merging_default_branch_starts_new_round(self) -> None:
        """Given vòng ở gốc B có sự kiện `log` đã commit; `main` của máy chủ đi tiếp, agent merge `origin/main` vào nhánh
        (merge-base đổi → vòng mới) · When `start` · Then exit 2: lần đầu vòng mới đòi `HEAD^{tree}` = cây gốc mới."""
        self.started()
        self.ok("abort", "--reason", "thử")
        self.ok("log")
        self.git("commit", "-q", "-am", "PERF-LOG")
        self.maintain({"src/other.py": "EXTRA = 400\n"}, "main đi tiếp")
        self.git("merge", "-q", "--no-edit", "origin/main")
        self.refused(*self.start_args())

    @flow("FLOW-39", done="T-3701")
    def test_flow_39_decoy_hotspot_does_not_reopen_exhausted_path(self) -> None:
        """AUD-HAR-233 — Given `src/hot.py` cạn (3 lần `abort`) · When `start --hotspot src/hot.py --hotspot
        src/other.py` (khai kèm đường "mồi") · Then exit 3, sổ/cây không đổi. Đối chứng: chỉ `src/other.py` → exit 0."""
        self.abort_round(("src/hot.py",), 3)
        self.assertIn("src/hot.py", self.refused(*self.start_args("src/hot.py", "src/other.py"), code=3))
        self.started("src/other.py")

    @flow("FLOW-40", done="T-3701")
    def test_flow_40_two_reverts_then_log_commit_start(self) -> None:
        """AUD-HAR-232 — Given hai lần thử liên tiếp bị thu hồi (`abort`) · Then mỗi lần cây = lúc start và PERF-LOG
        không đổi byte (`start`/`abort` không ghi cây), `start` thứ hai không kẹt · When `perf trial log`, commit, `start`
        · Then `log` có cả hai lần thử, giữ nguyên phần người viết, `log --check` exit 0; `start` kế exit 0."""
        fp0, log0 = self.fp(), self.perf_log()
        ids = []
        for i in range(2):
            ids.append(self.started())
            self.hot(tail=f"# thử {i}\n")
            self.ok("abort", "--reason", f"thử {i}")
            self.assertEqual((self.fp(), self.perf_log(), self.git("status", "--porcelain")), (fp0, log0, ""))
        self.ok("log")
        text = self.perf_log()
        self.assertEqual([tid in text for tid in ids], [True, True])
        self.assertIn("Ghi chú của người.\n", text)
        self.ok("log", "--check")
        self.git("commit", "-q", "-am", "PERF-LOG")
        self.started()

    @flow("FLOW-41", done="T-3703")
    def test_flow_41_keep_resets_only_changed_paths(self) -> None:
        """AUD-HAR-233 — Given `src/hot.py` 2 lần `abort`; khai `src/hot.py` + `src/other.py`, lần giữ chỉ đổi
        `src/other.py` (EXTRA 500 → 0), commit; thêm 1 lần `abort` trên `src/hot.py` · When `start --hotspot src/hot.py`
        · Then exit 3 (đếm của `src/hot.py` = 3, lần giữ không đặt lại nó). Đối chứng: `src/other.py` → exit 0."""
        self.abort_round(("src/hot.py",), 2)
        self.started("src/hot.py", "src/other.py")
        self.put("src/other.py", "EXTRA = 0\n")
        self.ok("finish")
        self.git("commit", "-q", "-am", "giữ other")
        self.abort_round(("src/hot.py",), 1)
        self.refused(*self.start_args("src/hot.py"), code=3)
        self.started("src/other.py")

    @flow("FLOW-41", done="T-3703")
    def test_flow_41_file_outside_hotspots_is_off_hotspot(self) -> None:
        """Given khai `src/hot.py`, candidate K = 2 kèm file mới `src/extra.py` ngoài danh sách · When `finish` · Then
        thu hồi (exit 1), `verdict: off-hotspot`, vân tay = lúc start (file mới bị gỡ)."""
        fp0 = self.fp()
        tid = self.started()
        self.hot(k=2)
        self.put("src/extra.py", "Y = 1\n")
        rc, out, err = self.trial("finish")
        self.assertEqual(rc, 1, out + err)
        self.assertEqual(self.decided(tid)[0]["verdict"], "off-hotspot")
        self.assertEqual(self.fp(), fp0)
        self.assertFalse((self.repo / "src" / "extra.py").exists())

    @flow("FLOW-42", done="T-3702")
    def test_flow_42_setup_and_probe_get_allowlisted_env(self) -> None:
        """Given `setup` ghi `env` ra ngoài cây, `probe` ghi `os.environ`; phiên agent có `NODE_OPTIONS`, `LD_PRELOAD`,
        `PYTHONPATH` (về `src/` cây agent), `BASH_ENV` (script để lại dấu) · When `perf trial prepare` · Then exit 0;
        `setup` và `probe` đã chạy nhưng không thấy bốn biến đó; script `BASH_ENV` không chạy."""
        bash_env = self.ctl / "bashenv.sh"
        bash_env.write_text(f'touch "{self.ctl}/bashenv-ran"\n', encoding="utf-8")
        cfg = trial_config(setup=f'env >> "{self.ctl}/setup.env"', probe="python3 probe.py")
        self.republish({"perf/trial.json": json.dumps(cfg)})
        self.started()
        leak = {
            "NODE_OPTIONS": "--require /nonexistent/evil.js",
            "LD_PRELOAD": str(self.ctl / "evil.so"),
            "PYTHONPATH": str(self.repo / "src"),
            "BASH_ENV": str(bash_env),
        }
        rc, out, err = self.trial("prepare", env=leak)
        self.assertEqual(rc, 0, out + err)
        for name in ("setup.env", "probe.env"):
            seen = "\n" + (self.ctl / name).read_text(encoding="utf-8")
            self.assertEqual([v for v in leak if f"\n{v}=" in seen], [], name)
        self.assertFalse((self.ctl / "bashenv-ran").exists())

    @flow("FLOW-43", done="T-3702")
    def test_flow_43_candidate_tree_from_objects_not_patch(self) -> None:
        """Given candidate: commit mới trong submodule (gitlink đổi), đổi tên `src/notes.txt` → `src/notes2.txt`, sửa
        `src/hot.py`; repo agent có `diff.external` và textconv qua `.git/info/attributes` · When `perf trial prepare`
        (`setup` ghi `ls-tree` của từng cây ra ngoài) · Then exit 0 và có cây đo đúng bằng cây candidate tính từ cây agent
        (index tạm `add -A`): gitlink mới, có đường mới, không đường cũ — `git apply` bỏ lặng gitlink, `git diff` theo
        driver ngoài."""
        setup = f'git ls-tree -r HEAD > "{self.ctl}/tree-$(git rev-parse "HEAD^{{tree}}")"'
        self.republish({"perf/trial.json": json.dumps(trial_config(setup=setup))})
        sub = self.add_submodule()
        self.started("src/hot.py", "src/notes.txt", "src/notes2.txt")
        self.run_git(sub, "commit", "-q", "--allow-empty", "-m", "sub đi tiếp")
        new_sub = self.run_git(sub, "rev-parse", "HEAD")
        self.git("mv", "src/notes.txt", "src/notes2.txt")
        self.hot(k=2)
        ext = self.ctl / "ext.sh"
        ext.write_text("#!/bin/sh\necho đổi\n", encoding="utf-8")
        ext.chmod(0o755)
        self.git("config", "diff.external", str(ext))
        self.git("config", "diff.evil.textconv", "sed s/K/Q/")
        (self.repo / ".git" / "info" / "attributes").write_text("*.py diff=evil\n", encoding="utf-8")
        idx = {"GIT_INDEX_FILE": str(self.tmp / "expect.idx")}
        self.git("read-tree", "HEAD", env=idx)
        self.git("add", "-A", env=idx)
        want = self.git("write-tree", env=idx)
        rc, out, err = self.trial("prepare")
        self.assertEqual(rc, 0, out + err)
        dump = self.ctl / f"tree-{want}"
        self.assertTrue(dump.exists(), sorted(p.name for p in self.ctl.glob("tree-*")))
        listing = dump.read_text(encoding="utf-8")
        self.assertIn(f"160000 commit {new_sub}\tvendor/sub", listing)
        self.assertIn("\tsrc/notes2.txt\n", listing)
        self.assertNotIn("\tsrc/notes.txt\n", listing)

    @flow("FLOW-44", done="T-3704")
    def test_flow_44_secondary_regress_under_ceiling_reverts(self) -> None:
        """Given candidate K = 2 (`improved`) kèm `BUF` 100 → 140 (+40 %, dưới trần 1000), `regress` 0 · When `finish` ·
        Then thu hồi (exit 1), lý do nêu `mem`, vân tay = lúc start."""
        fp0 = self.fp()
        tid = self.started()
        self.hot(k=2, buf=140)
        rc, out, err = self.trial("finish")
        self.assertEqual(rc, 1, out + err)
        self.assertEqual(self.fp(), fp0)
        self.assertIn("mem", self.why(self.decided(tid)[0]))

    @flow("FLOW-45", done="T-3704")
    def test_flow_45_status_check_follows_target_without_loop_record(self) -> None:
        """Given `target: primary <= -20%` · When thu hồi (`neutral`) → `status --check`; giữ EXTRA 500 → 0 (3500 → 3000,
        −14 %), commit → `status --check`; giữ K = 2 (→ 2000, −43 %), commit → `status --check` · Then exit 1, 1, 0;
        không bằng chứng/state `loop record` nào (`finish` không phải Gate, ADR-0052 §3)."""
        codes = []
        self.started()
        self.hot(tail="# chú thích\n")
        self.assertEqual(self.trial("finish")[0], 1)
        codes.append(self.trial("status", "--check")[0])
        self.started("src/hot.py", "src/other.py")
        self.put("src/other.py", "EXTRA = 0\n")
        self.ok("finish")
        self.git("commit", "-q", "-am", "giữ 1")
        codes.append(self.trial("status", "--check")[0])
        self.started()
        self.hot(k=2)
        self.ok("finish")
        self.git("commit", "-q", "-am", "giữ 2")
        codes.append(self.trial("status", "--check")[0])
        self.assertEqual(codes, [1, 1, 0])
        auto = self.repo / ".autopilot"
        self.assertEqual([(auto / n).exists() for n in ("evidence", "state.json")], [False, False])

    @flow("FLOW-46")
    def test_flow_46_status_check_bound_to_kept_tree(self) -> None:
        """Given giữ K = 2 (−29 %, đạt `target`), commit · When commit lạ K = 9 (chậm gấp ba gốc) → `status --check`;
        commit trả cây về K = 2 → `status --check`; sửa file chưa commit → `status --check` · Then exit 0 lúc đầu, 1
        "commit lạ sau lần giữ", 0 (cây trùng cây giữ), 1 "cây bẩn" — Gate không xanh nhờ số của cây khác (D-368)."""
        self.started()
        self.hot(k=2)
        self.ok("finish")
        self.git("commit", "-q", "-am", "giữ K=2")
        self.ok("status", "--check")
        self.hot(k=9)
        self.git("commit", "-q", "-am", "commit lạ: K=9")
        self.assertIn("commit lạ sau lần giữ", self.refused("status", "--check", code=1))
        self.hot(k=2)
        self.git("commit", "-q", "-am", "về K=2")
        self.ok("status", "--check")
        self.put("src/other.py", "EXTRA = 99999\n")
        self.assertIn("cây bẩn", self.refused("status", "--check", code=1))


class FlowRegistryTest(unittest.TestCase):
    def test_strict_ids_exist(self) -> None:
        """`XT_FLOW_STRICT` và `XFAIL` chỉ được nêu ID có test mang nó — không để Gate xanh vì thiếu ca."""
        self.assertEqual(sorted(STRICT - FLOW_IDS), [], "XT_FLOW_STRICT nêu ID không có test")
        self.assertEqual(sorted(XFAIL.keys() - FLOW_IDS), [], "XFAIL nêu ID không có test")

    def test_heldout_fixture_is_deterministic(self) -> None:
        """Ca giữ EXTRA 500 → 0 (FLOW-41, FLOW-45, `test_keep_json…`) từng đỏ ~0,06 %: hạt giống ra input lớn thì tổng
        held-out đổi < sàn 2 % (`neutral`), hoặc input trùng thì ít hơn 5. Mọi hạt giống: HELD_N input khác nhau trong
        khoảng; worst case (HELD_N số lớn nhất) tổng và từng input vẫn đổi ≥ sàn; khoảng không chứa N = 1000 (FLOW-30)."""
        lo, hi = HELD_RANGE
        top = range(hi - HELD_N, hi)
        self.assertGreaterEqual(HELD_N * 500 / sum(3 * n + 500 for n in top), xt.PERF_MIN_EFFECT)
        self.assertGreaterEqual(500 / (3 * (hi - 1) + 500), xt.PERF_MIN_EFFECT)
        self.assertGreater(lo, 1000)
        with tempfile.TemporaryDirectory() as d:
            gen = Path(d, "gen.py")
            gen.write_text(trial_files(Path(d))["heldout_gen.py"], encoding="utf-8")
            for seed in ("0", "ffffffffffffffff", "9e3779b97f4a7c15"):
                out = subprocess.run(
                    [sys.executable, str(gen)], input=seed, capture_output=True, text=True, check=True
                ).stdout.split()
                self.assertEqual(len(set(out)), HELD_N, out)
                self.assertTrue(all(lo <= int(x) < hi for x in out), out)


if __name__ == "__main__":
    unittest.main()
