"""Corpus luồng (ADR-0052 §1; nghiên cứu 2026-10-26 §10): chạy `xt.py` THẬT trong repo git tạm, không mock state.

State dựng bằng chính lệnh `loop init/record/defer/block`; không ca nào sửa tay `.autopilot/state.json`.

Cơ chế xfail (không skip):
- `XFAIL` = {ID: tái hiện + task sẽ sửa}. Ca có ID trong `XFAIL` mà KHÔNG có trong `XT_FLOW_STRICT` nhận
  `unittest.expectedFailure`: đỏ hôm nay thì suite vẫn exit 0; tự xanh thì "unexpected success" làm suite đỏ — nhắc gỡ ID khỏi `XFAIL`.
- `XT_FLOW_STRICT=FLOW-01,FLOW-04` (phân cách dấu phẩy, khoảng trắng bỏ qua, đọc lúc import) bỏ xfail của các ID đó: ca chạy thường
  nên Gate của task sửa chỉ xanh khi ca thật sự đạt.
- `@flow("FLOW-NN")` gắn ID cho test và ghi vào `FLOW_IDS`; `test_strict_ids_exist` đỏ khi `XT_FLOW_STRICT` hoặc `XFAIL`
  nêu ID không có test nào mang nó (Gate không xanh vì thiếu ca).
- Gỡ ID khỏi `XFAIL` khi task sửa xong; ID không còn xfail vẫn chạy thường.
"""

from __future__ import annotations

import functools
import json
import multiprocessing
import os
import re
import subprocess
import sys
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

XFAIL: dict[str, str] = {}
STRICT: frozenset[str] = frozenset(s.strip() for s in os.environ.get("XT_FLOW_STRICT", "").split(",") if s.strip())
FLOW_IDS: set[str] = set()


def flow(flow_id: str) -> Callable[[F], F]:
    """Gắn ID cho test; ID thuộc XFAIL và không thuộc STRICT → `expectedFailure`."""

    def deco(fn: F) -> F:
        FLOW_IDS.add(flow_id)
        if flow_id in XFAIL and flow_id not in STRICT:
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


class FlowRegistryTest(unittest.TestCase):
    def test_strict_ids_exist(self) -> None:
        """`XT_FLOW_STRICT` và `XFAIL` chỉ được nêu ID có test mang nó — không để Gate xanh vì thiếu ca."""
        self.assertEqual(sorted(STRICT - FLOW_IDS), [], "XT_FLOW_STRICT nêu ID không có test")
        self.assertEqual(sorted(XFAIL.keys() - FLOW_IDS), [], "XFAIL nêu ID không có test")


if __name__ == "__main__":
    unittest.main()
