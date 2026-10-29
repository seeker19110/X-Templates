"""Test cho `loop next-step` (ADR-0052 §5, T-3547, T-3578): hàm thuần `next_step` theo từng nhánh, đầu vào
`next_step_facts`, mốc và dấu đợt xong (`loop init`, `loop verify --all`, Stop hook), và CLI. Luồng đầu–cuối trong repo git
thật ở `tests/test_flow.py` (FLOW-09…13)."""

from __future__ import annotations

import copy
import io
import json
import os
import sys
import tempfile
import unittest
import unittest.mock
from contextlib import redirect_stderr
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import xt
from test_xt_cli import run_main

HEAD = "a" * 40


def facts(**over: Any) -> dict[str, Any]:
    """Đầu vào "hết việc": đợt done đã kiểm lại cuối, không PR mở, sổ phủ tới HEAD, 0 việc mở."""
    f: dict[str, Any] = {
        "objective": "build-until-clean",
        "repo": "r",
        "head": HEAD,
        "verdict": {"verdict": "done", "reason": "mọi task có bằng chứng xanh"},
        "final_check": None,
        "prs": [],
        "audit": {"status": "S.md", "exists": True, "sha256": "0" * 64, "open": 0, "debt": {}, "scanned": ["b" * 40]}
        | {"errors": []},
        "open_must": 0,
        "state": {"rev": 3, "plan": "P.md", "iterations": 2, "max_iterations": 40, "deadline": None, "batches": []},
    }
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(f.get(k), dict) and k != "verdict":
            f[k] = {**f[k], **v}
        else:
            f[k] = v
    return f


def batch(open_: int | None, at: str, status: str = "S.md") -> dict[str, Any]:
    return {"plan": "P.md", "at": at, "open": open_, "status": status}


class NextStepPureTest(unittest.TestCase):
    def step(self, **over: Any) -> dict[str, Any]:
        f = facts(**over)
        frozen = copy.deepcopy(f)
        out = xt.next_step(f)
        self.assertEqual(f, frozen)  # không sửa đầu vào
        self.assertEqual(json.loads(json.dumps(out)), xt.next_step(json.loads(json.dumps(out["inputs"]))))  # phát lại
        return out

    def test_ready_for_complete_contract(self) -> None:
        out = self.step()
        self.assertEqual(out["action"], "ready-for-complete")
        self.assertIn("D-178", out["reason"])
        self.assertEqual(out["missing"], [])
        self.assertEqual(
            out["key"], {"repo": "r", "objective": "build-until-clean", "task": None, "pr": None, "head": HEAD}
        )
        self.assertEqual(
            out["budget"],
            {
                "iterations": [2, 40],
                "batches": [0, None],
                "deadline": None,
                "cost_usd": None,
                "no_progress_since": None,
            },
        )

    def test_pending_human_still_ready_and_names_it(self) -> None:
        v = {"verdict": xt.PENDING_HUMAN, "reason": "chờ người 1 việc: T-9 (ký)"}
        out = self.step(verdict=v)
        self.assertEqual(out["action"], "ready-for-complete")
        self.assertIn("T-9 (ký)", out["reason"])

    def test_done_without_final_check_is_verify(self) -> None:
        out = self.step(final_check="chưa kiểm lại cuối")
        self.assertEqual((out["action"], out["reason"]), ("verify", "chưa kiểm lại cuối"))
        self.assertTrue(out["missing"])

    def test_loop_verdicts_map_to_actions(self) -> None:
        for verdict, action in (
            ("continue", "task"),
            ("verify", "verify"),
            ("blocked", "blocked"),
            ("budget", "budget"),
        ):
            with self.subTest(verdict):
                out = self.step(verdict={"verdict": verdict, "reason": "x", "task": "T-002"})
                self.assertEqual((out["action"], out["key"]["task"]), (action, "T-002"))
        self.assertEqual(self.step(verdict={"verdict": "lạ", "reason": "x"})["action"], "blocked")  # không đoán: chặn

    def test_inactive_replans(self) -> None:
        out = self.step(verdict={"verdict": "inactive", "reason": "vòng lặp chưa bật"})
        self.assertEqual(out["action"], "replan")
        self.assertIn("loop init", out["reason"])

    def test_prs_missing_or_open(self) -> None:
        out = self.step(prs=None)
        self.assertEqual((out["action"], out["key"]["pr"]), ("pr", None))
        self.assertIn("--prs", out["missing"][0])
        prs = [
            {"pr": "1", "head": "1" * 40, "action": "closed", "why": ""},
            {"pr": "2", "head": "2" * 40, "action": "review", "why": ""},
        ]
        out = self.step(prs=prs)
        self.assertEqual((out["action"], out["key"]["pr"], out["key"]["head"]), ("pr", "2", "2" * 40))
        self.assertEqual(out["reason"], "PR #2 còn `review`")

    def test_audit_missing_unscanned_or_debt(self) -> None:
        out = self.step(audit={"exists": False, "scanned": []})
        self.assertEqual(out["action"], "audit")
        self.assertIn("chưa có sổ S.md", out["reason"])
        out = self.step(audit={"scanned": []})
        self.assertIn("chưa có nhóm nào đã quét", out["reason"])
        out = self.step(audit={"debt": {"b.py": "c" * 40, "a.py": "b" * 40}})
        self.assertEqual(out["action"], "audit")
        self.assertIn("2 file", out["reason"])
        self.assertIn(f"`{'b' * 12}..HEAD`, `{'c' * 12}..HEAD`", out["reason"])
        self.assertIn(HEAD[:12], out["missing"][0])

    def test_open_work_replans(self) -> None:
        out = self.step(audit={"open": 1}, open_must=2)
        self.assertEqual(out["action"], "replan")
        self.assertIn("1 🔴/🟠", out["reason"])
        self.assertIn("2 MUST", out["reason"])
        self.assertEqual(self.step(open_must=3)["action"], "replan")  # chỉ MUST mở cũng là việc

    def test_two_batches_without_progress_end_budget(self) -> None:
        cases = {
            "giảm": ([batch(5, "t1"), batch(3, "t2")], 3, "replan", None),
            "một đợt": ([batch(3, "t1")], 3, "replan", None),
            "mốc thiếu số": ([batch(None, "t1"), batch(3, "t2")], 3, "replan", None),
            "đợt cuối giảm": ([batch(3, "t1"), batch(3, "t2")], 2, "replan", None),
            "không giảm": ([batch(1, "t0"), batch(3, "t1"), batch(3, "t2")], 3, "budget", "t1"),
            "tăng rồi giảm": ([batch(3, "t1"), batch(5, "t2")], 3, "replan", None),
            "khác sổ": ([batch(3, "t1"), batch(3, "t2", "KHÁC.md")], 3, "replan", None),
            "khác sổ ở mốc trước": ([batch(3, "t1", "KHÁC.md"), batch(3, "t2")], 3, "replan", None),
        }
        for name, (batches, now, action, since) in cases.items():
            with self.subTest(name):
                out = self.step(audit={"open": now}, state={"batches": batches})
                self.assertEqual((out["action"], out["budget"]["no_progress_since"]), (action, since))
        out = self.step(open_must=3, state={"batches": [batch(3, "t1"), batch(3, "t2")]})  # chỉ MUST cũng tính
        self.assertEqual((out["action"], out["budget"]["batches"]), ("budget", [2, None]))
        self.assertIn("3 → 3 → 3", out["reason"])
        self.assertIsNone(xt._no_progress([batch(0, "t1"), batch(0, "t2")], 0, "S.md"))
        broken = [{"status": ["S.md"], "open": 1, "at": "t1"}, batch(1, "t2")]  # state hỏng: không văng TypeError
        self.assertIsNone(xt._no_progress(broken, 1, "S.md"))

    def test_audit_book_failing_strict_is_audit(self) -> None:
        out = self.step(audit={"errors": ["nhóm 2: chưa quét", "x"]})
        self.assertEqual(out["action"], "audit")
        self.assertIn("trượt `audit check --strict` (2 lỗi, đầu tiên: nhóm 2: chưa quét)", out["reason"])
        out = self.step(audit={"errors": ["nhóm 1: chưa quét"], "scanned": []})  # sổ mẫu vừa cài: gợi ý audit full
        self.assertIn("chưa có nhóm nào đã quét", out["reason"])
        unread = {"errors": ["không đọc được sổ: utf-8"], "scanned": [], "sha256": ""}
        self.assertIn("không đọc được sổ: utf-8", self.step(audit=unread)["reason"])  # lỗi đọc, không gợi audit full

    def test_loop_before_prs(self) -> None:
        wait = [{"pr": "4", "head": "4" * 40, "action": "wait", "why": ""}]
        out = self.step(verdict={"verdict": "continue", "reason": "x", "task": "T-002"}, prs=wait)
        self.assertEqual(out["action"], "task")  # PR chờ CI không chặn task độc lập (nghiên cứu §5)


class StateCase(unittest.TestCase):
    """Dự án tạm: PLAN một task xanh, blueprint hai MUST mở, pha build."""

    def setUp(self) -> None:
        self.base = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.enterContext(unittest.mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(self.base)}))
        (self.base / "P.md").write_text("- [x] `T-001` xong — Gate: `true`\n", encoding="utf-8")
        ev = self.base / ".autopilot" / "evidence"
        ev.mkdir(parents=True)
        (ev / "T-001.json").write_text(json.dumps({"task": "T-001", "exit_code": 0, "cmd": "true"}), encoding="utf-8")
        (self.base / "BP.md").write_text("- [ ] `AAA-001` **MUST** a\n- [ ] `AAA-002` **MUST** b\n", encoding="utf-8")
        (self.base / "xt.yaml").write_text("delivery_phase: build\n", encoding="utf-8")

    def st(self, **over: Any) -> dict[str, Any]:
        return {"active": True, "iterations": 0, "max_iterations": 9, "plan": "P.md", "blueprint": "BP.md", **over}


class NextStepStateTest(StateCase):
    """Đầu vào đọc từ đĩa: verdict đợt sau Stop hook, MUST mở, sổ audit; mốc và dấu đợt xong (T-3578)."""

    def test_batch_verdict_after_stop(self) -> None:
        done = self.st(active=False, final_verdict={"verdict": "done", "reason": "x"})
        xt.write_state(done, self.base)
        self.assertEqual(xt._batch_verdict(self.base, done)["verdict"], "done")
        pend = {**done, "deferred": {"AAA-001": {"reason": "ký"}}}
        xt.write_state(pend, self.base)
        self.assertEqual(xt._batch_verdict(self.base, pend)["verdict"], xt.PENDING_HUMAN)
        for fv, want in (("blocked", "blocked"), ("stopped", "blocked"), ("budget", "budget")):
            with self.subTest(fv):
                s = self.st(active=False, final_verdict={"verdict": fv, "reason": "x"})
                xt.write_state(s, self.base)
                self.assertEqual(xt._batch_verdict(self.base, s)["verdict"], want)
        (self.base / "P.md").write_text("- [ ] `T-002` mới — Gate: `true`\n", encoding="utf-8")
        xt.write_state(done, self.base)
        self.assertEqual(xt._batch_verdict(self.base, done)["verdict"], "continue")  # cây đổi sau khi dừng
        blocked = {**done, "blocked": True, "blocked_reason": "cần khoá API trả phí"}
        xt.write_state(blocked, self.base)
        self.assertEqual(
            xt._batch_verdict(self.base, blocked), {"verdict": "blocked", "reason": "cần khoá API trả phí"}
        )
        xt.write_state({**done, "blocked": True}, self.base)
        self.assertEqual(xt._batch_verdict(self.base, {**done, "blocked": True})["reason"], "cần người quyết định")
        never: dict[str, Any] = {}
        self.assertEqual(xt._batch_verdict(self.base, never)["verdict"], "inactive")

    def test_open_must_skips_deferred_and_missing_blueprint(self) -> None:
        self.assertEqual(xt._open_must(self.base, self.st(deferred={"AAA-001": {}})), ["AAA-002"])
        self.assertEqual(xt._open_must(self.base, self.st(blueprint=None)), [])
        self.assertEqual(xt._open_must(self.base, self.st(blueprint="mất.md")), [])

    def test_batch_mark_rules(self) -> None:
        new = {"plan": "P.md", "started": "t9", "blueprint": "BP.md"}
        prev = {"objective": {"batches": [batch(i, f"t{i}") for i in range(25)] + ["rác"]}}
        out = xt._batch_mark(prev, new, self.base)
        self.assertEqual(out["name"], "build-until-clean")
        self.assertEqual(len(out["batches"]), xt.OBJECTIVE_BATCHES_KEEP)
        mark = {"plan": "P.md", "status": xt.AUDIT_STATUS_DEFAULT, "at": "t9", "open": None}  # chưa có sổ → null
        self.assertEqual(xt._batch_mark({}, new, self.base)["batches"], [mark])
        book = self.base / xt.AUDIT_STATUS_DEFAULT
        book.parent.mkdir(parents=True)
        book.write_text("## Phát hiện\n\n| ID | Mức | Trạng thái |\n|---|---|---|\n| A-1 | 🟠 | mở |\n", "utf-8")
        self.assertEqual(xt._batch_mark({}, new, self.base)["batches"], [{**mark, "open": 3}])  # 1 🟠 + 2 MUST
        dở = {"active": True, "iterations": 0, "max_iterations": 9, "objective": {"batches": [mark]}}
        self.assertEqual(xt._batch_mark(dở, new, self.base)["batches"], [mark])  # đợt dở cùng PLAN: cùng đợt
        stopped = {**dở, "active": False, "final_verdict": {"verdict": "stopped"}}
        self.assertEqual(xt._batch_mark(stopped, new, self.base)["batches"], [mark])  # dừng tay không đóng đợt
        pairs = xt._plan_pairs(self.base, "P.md")
        self.assertEqual(pairs, [f"T-001:{xt.task_req_rev(xt.parse_plan(self.base / 'P.md')[0])}"])
        for name, p in {
            "dấu xong": {**dở, "objective": {"batches": [{**mark, "done": "t5", "tasks": pairs + ["T-009:x"]}]}},
            "dấu xong không có tasks (mốc cũ)": {**dở, "objective": {"batches": [{**mark, "done": "t5"}]}},
            "hết vòng": {**dở, "iterations": 9},
            "Stop hook kết thúc vì hết ngân sách": {**stopped, "final_verdict": {"verdict": "budget"}},
        }.items():
            with self.subTest(name):
                self.assertEqual(len(xt._batch_mark(p, new, self.base)["batches"]), 2)
        self.assertEqual(len(xt._batch_mark(dở, {**new, "plan": "P2.md"}, self.base)["batches"]), 2)  # PLAN khác
        # Dấu xong rồi PLAN chỉ nối thêm task (mọi `ID:req_rev` lúc đánh dấu còn) → cùng đợt, gỡ dấu (review #319).
        done = {**dở, "objective": {"batches": [{**mark, "done": "t5", "tasks": pairs}]}}
        (self.base / "P.md").write_text(
            "- [x] `T-001` xong — Gate: `true`\n- [ ] `T-002` thêm — Gate: `true`\n", encoding="utf-8"
        )
        self.assertEqual(xt._batch_mark(done, new, self.base)["batches"], [mark])
        (self.base / "P.md").write_text("- [x] `T-001` xong đổi spec — Gate: `true`\n", encoding="utf-8")
        self.assertEqual(len(xt._batch_mark(done, new, self.base)["batches"]), 2)  # viết lại spec: đợt mới
        self.assertEqual(xt._plan_pairs(self.base, None), [])
        self.assertEqual(xt._plan_pairs(self.base, "mất.md"), [])
        self.assertEqual(xt._batch_mark({**dở, "iterations": "x"}, new, self.base)["batches"], [mark])  # state sai kiểu
        with unittest.mock.patch.object(xt, "blueprint_status", side_effect=OSError("hỏng")):
            self.assertIsNone(xt._batch_mark({}, new, self.base)["batches"][-1]["open"])
        book.write_bytes(b"\xff\xfe")  # không phải UTF-8 → ValueError
        self.assertIsNone(xt._batch_mark({}, new, self.base)["batches"][-1]["open"])
        for bad in ({"objective": []}, {"objective": {"batches": "x"}}):
            self.assertEqual(xt._objective_batches(bad), [])
        self.assertEqual(xt._objective_batches({"objective": {"batches": [1, mark]}}), [mark])

    def test_mark_and_reopen_batch(self) -> None:
        self.assertIsNone(xt._mark_batch_done({}, []))
        cur = {"objective": {"name": "x", "batches": [batch(1, "t1"), batch(2, "t2")]}}
        out = xt._mark_batch_done(cur, ["T-1:a"])
        assert out is not None
        self.assertNotIn("done", out["objective"]["batches"][0])
        self.assertTrue(out["objective"]["batches"][-1]["done"])
        self.assertEqual(out["objective"]["batches"][-1]["tasks"], ["T-1:a"])
        self.assertEqual(out["objective"]["name"], "x")
        self.assertIsNone(xt._mark_batch_done(out, []))  # đã có dấu: không ghi lại
        xt._reopen_last_batch(out)
        self.assertEqual(out["objective"]["batches"][-1], batch(2, "t2"))
        xt._reopen_last_batch(out)  # không có dấu: không đổi
        self.assertEqual(out["objective"]["name"], "x")

    def test_unblock_and_resume_reopen_batch(self) -> None:
        """Mở lại vòng (`unblock`, `resume`) → đợt chưa xong: gỡ dấu (review #319, đường EXIT_PENDING)."""
        marked = {**batch(1, "t1"), "done": "t2", "tasks": ["T-001:x"]}
        for cmd in (("unblock", "--reason", "người xem"), ("resume", "--reason", "người xem")):
            with self.subTest(cmd[0]):
                st = self.st(active=False, blocked=True, started="t0", objective={"batches": [marked]})
                xt.write_state(st, self.base)
                rc, _, err = run_main("loop", *cmd)
                self.assertEqual(rc, 0, err)
                self.assertEqual((xt.read_state(self.base) or {})["objective"]["batches"][-1], batch(1, "t1"))

    def test_close_batch_only_when_done_and_fail_open(self) -> None:
        xt.write_state(self.st(objective={"batches": [batch(1, "t1")]}), self.base)
        xt._close_batch(self.base)  # pha build, T-001 xanh → done
        self.assertTrue((xt.read_state(self.base) or {})["objective"]["batches"][-1]["done"])
        xt.write_state(self.st(objective={"batches": [batch(1, "t1")]}, blocked=True), self.base)
        xt._close_batch(self.base)  # blocked: không đóng đợt
        self.assertNotIn("done", (xt.read_state(self.base) or {})["objective"]["batches"][-1])
        xt.write_state(self.st(objective={"batches": [batch(1, "t1")]}), self.base)
        err = io.StringIO()
        with unittest.mock.patch.object(xt, "update_loop_state", side_effect=OSError("khoá bận")), redirect_stderr(err):
            xt._close_batch(self.base)
        self.assertIn("không ghi được dấu đợt xong (OSError: khoá bận)", err.getvalue())
        xt.write_state(self.st(iterations="x", objective={"batches": [batch(1, "t1")]}), self.base)
        err = io.StringIO()
        with redirect_stderr(err):
            xt._close_batch(self.base)  # state sai kiểu: không văng, verify giữ exit (review #319)
        self.assertIn("không ghi được dấu đợt xong (TypeError", err.getvalue())

    def test_init_records_mark_after_carrying_deferred(self) -> None:
        """Mốc đếm SAU `_carry_previous`: MUST chờ người mang từ vòng trước không tính."""
        book = self.base / xt.AUDIT_STATUS_DEFAULT
        book.parent.mkdir(parents=True)
        book.write_text("## Phát hiện\n\n| ID | Mức | Trạng thái |\n|---|---|---|\n", "utf-8")
        rc, _, err = run_main("loop", "init", "--plan", "P.md", "--blueprint", "BP.md")
        self.assertEqual(rc, 0, err)
        st = xt.read_state(self.base) or {}
        self.assertEqual([(b["at"], b["open"]) for b in st["objective"]["batches"]], [(st["started"], 2)])
        self.assertEqual(run_main("loop", "defer", "--task", "AAA-001", "--reason", "ký")[0], 0)
        (self.base / "P2.md").write_text("- [x] `T-001` xong đợt 2 — Gate: `true`\n", encoding="utf-8")
        rc, _, err = run_main("loop", "init", "--plan", "P2.md", "--blueprint", "BP.md", "--force")
        self.assertEqual(rc, 0, err)
        st = xt.read_state(self.base) or {}
        self.assertIn("AAA-001", st["deferred"])
        self.assertEqual([b["open"] for b in st["objective"]["batches"]], [2, 1])

    def test_stop_hook_marks_batch_done(self) -> None:
        xt.write_state(self.st(session_id="s1", objective={"batches": [batch(1, "t1")]}), self.base)
        rc, out, _ = run_main("loop", "hook-stop", stdin=json.dumps({"session_id": "s1"}))
        self.assertEqual((rc, out), (0, ""))  # không phải repo git → không kiểm lại cuối, cho dừng ở done
        st = xt.read_state(self.base) or {}
        self.assertEqual(st["final_verdict"]["verdict"], "done")
        self.assertTrue(st["objective"]["batches"][-1]["done"])
        self.assertEqual(st["objective"]["batches"][-1]["tasks"], xt._plan_pairs(self.base, "P.md"))
        for verdict, deferred in (("blocked", {}), (xt.PENDING_HUMAN, {"AAA-001": {"reason": "ký"}})):
            with self.subTest(verdict):  # blocked không đóng đợt; chờ người đóng (D-228)
                extra = {"blocked": True, "blocked_reason": "x"} if verdict == "blocked" else {"deferred": deferred}
                xt.write_state(self.st(session_id="s1", objective={"batches": [batch(1, "t1")]}, **extra), self.base)
                run_main("loop", "hook-stop", stdin=json.dumps({"session_id": "s1"}))
                st = xt.read_state(self.base) or {}
                self.assertEqual(st["final_verdict"]["verdict"], verdict)
                self.assertEqual("done" in st["objective"]["batches"][-1], verdict != "blocked")

    def test_audit_open_count(self) -> None:
        self.assertEqual(xt.audit_open_count(self.base / "không.md"), 0)
        book = self.base / "S.md"
        rows = ["| A-1 | 🔴 | mở |", "| A-2 | 🟠 | mở |", "| A-3 | 🟢 | mở |", "| A-4 | 🔴 | đã sửa |"]
        rows += ["| A-5 | 🔴 | chấp nhận |", "| A-6 | 🟠 | bác bỏ |"]
        book.write_text("## Phát hiện\n\n| ID | Mức | Trạng thái |\n|---|---|---|\n" + "\n".join(rows) + "\n", "utf-8")
        self.assertEqual(xt.audit_open_count(book), 2)


class NextStepCliTest(StateCase):
    def test_cli_text_json_and_bad_prs(self) -> None:
        xt.write_state(self.st(), self.base)
        rc, out, _ = run_main("loop", "next-step")
        self.assertEqual(rc, 0)
        self.assertTrue(out.startswith("pr — "), out)  # không --prs: đối soát PR trước
        self.assertIn("  thiếu: `--prs FILE`", out)
        prs = self.base / "prs.json"
        prs.write_text(json.dumps({"pr": 5, "head": "e" * 40, "action": "done", "why": None}), encoding="utf-8")
        rc, out, _ = run_main("loop", "next-step", "--json", "--prs", str(prs))
        d = json.loads(out)
        self.assertEqual((rc, d["action"]), (0, "audit"))  # không có sổ → audit full
        self.assertEqual(d["inputs"]["prs"], [{"pr": "5", "head": "e" * 40, "action": "done", "why": ""}])
        self.assertFalse(d["inputs"]["audit"]["exists"])
        rc, out, _ = run_main("loop", "next-step", "--json", "--prs", "-", stdin="[]")
        self.assertEqual(json.loads(out)["inputs"]["prs"], [])
        for bad in ("{", "[1]", '[{"action": ""}]', "[" * 100_000 + "]" * 100_000):
            with self.subTest(bad):
                prs.write_text(bad, encoding="utf-8")
                rc, _, err = run_main("loop", "next-step", "--prs", str(prs))
                self.assertEqual(rc, 2)
                self.assertIn("✗ --prs", err)
        rc, _, err = run_main("loop", "next-step", "--prs", str(self.base / "mất.json"))
        self.assertEqual(rc, 2, err)

    def test_facts_read_audit_book(self) -> None:
        book = self.base / "S.md"
        book.write_text("## Phát hiện\n\n| ID | Mức | Trạng thái |\n|---|---|---|\n| A-1 | 🟠 | mở |\n", "utf-8")
        f = xt.next_step_facts(self.base, self.st(), "S.md", [])
        self.assertEqual((f["audit"]["exists"], f["audit"]["open"], f["audit"]["scanned"]), (True, 1, []))
        self.assertEqual(len(f["audit"]["sha256"]), 64)
        self.assertIn("thiếu bảng `## Nhóm`", f["audit"]["errors"])
        self.assertFalse([e for e in f["audit"]["errors"] if "còn mở" in e])  # 🟠 mở: việc của `_step_work`
        self.assertEqual(f["open_must"], 2)
        book.write_bytes(b"\xff\xfe")
        a = xt.next_step_facts(self.base, self.st(), "S.md", [])["audit"]
        self.assertEqual((a["exists"], a["open"], a["sha256"]), (True, 0, ""))
        self.assertTrue(a["errors"][0].startswith("không đọc được sổ: "), a["errors"])


if __name__ == "__main__":
    unittest.main()
