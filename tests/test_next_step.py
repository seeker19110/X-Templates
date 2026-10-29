"""Test cho `loop next-step` (ADR-0052 §5, T-3547, T-3578, T-3548): hàm thuần `next_step` theo từng nhánh, đầu vào
`next_step_facts`, mốc và dấu đợt xong (`loop init`, `loop verify --all`, Stop hook), việc harden nháp, và CLI. Luồng
đầu–cuối trong repo git thật ở `tests/test_flow.py` (FLOW-09…15)."""

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
FP = "f" * 64


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
        "harden": [],
        "signoff": {"release": None, "release_changed": None, "package": None, "package_changed": None}
        | {"evidence_fp": FP, "deferred": []},
        "state": {"rev": 3, "plan": "P.md", "iterations": 2, "max_iterations": 40, "deadline": None, "batches": []},
    }
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(f.get(k), dict) and k != "verdict":
            f[k] = {**f[k], **v}
        else:
            f[k] = v
    return f


def work(key: str, tid: str, planned: bool = False, checked: bool = False) -> dict[str, Any]:
    """Một mục việc harden nháp như `harden_work` trả."""
    src, _, ref = key.partition(":")
    return {"source": src, "ref": ref.split("@")[0], "key": key, "id": tid, "planned": planned, "checked": checked}


HARDEN = "harden-to-signoff"


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

    def test_harden_gathers_work_then_release_check(self) -> None:
        """T-3548: harden gom việc nháp (`work`) → `replan`; task đã tick mà nguồn còn mở → `audit`; task đã gom chưa tick
        là việc của vòng; hết việc → `release-check` (không `ready-for-complete`)."""
        out = self.step(objective=HARDEN)
        self.assertEqual((out["action"], out["work"], out["key"]["objective"]), ("release-check", [], HARDEN))
        self.assertEqual(out["missing"], ["`release-check --json` trên HEAD"])
        items = [work("audit:AUD-A-001@abc1234", "T-010"), work("must:AAA-001", "T-009", planned=True)]
        out = self.step(objective=HARDEN, harden=items, audit={"open": 1}, open_must=1)
        self.assertEqual((out["action"], out["work"]), ("replan", items))
        self.assertIn("1 việc harden chưa có trong PLAN (vd T-010 ← audit:AUD-A-001@abc1234)", out["reason"])
        self.assertEqual(out["missing"], ["task cho audit:AUD-A-001@abc1234"])
        stale = [
            work("audit:AUD-A-001", "T-010", planned=True, checked=True),
            work("must:AAA-001", "T-9", planned=True),
        ]
        out = self.step(objective=HARDEN, harden=stale)
        self.assertEqual(out["action"], "audit")
        self.assertIn("1 task đã tick mà nguồn còn mở: T-010 (audit:AUD-A-001)", out["reason"])
        self.assertEqual(self.step(objective=HARDEN, harden=stale[1:])["action"], "release-check")  # chờ vòng/người
        self.assertEqual(self.step(harden=items)["action"], "ready-for-complete")  # build không đọc `harden`

    def test_harden_inactive_loop_gathers_first(self) -> None:
        """Harden: vòng chưa bật không phải `replan` ngay — gom việc trước; PLAN đã có task gom chưa tick → `loop init`."""
        off = {"verdict": "inactive", "reason": "vòng lặp chưa bật"}
        self.assertEqual(self.step(objective=HARDEN, verdict=off)["action"], "release-check")
        items = [work("audit:AUD-A-001", "T-010")]
        out = self.step(objective=HARDEN, verdict=off, harden=items)
        self.assertEqual((out["action"], len(out["work"])), ("replan", 1))
        out = self.step(objective=HARDEN, verdict=off, harden=[work("audit:AUD-A-001", "T-010", planned=True)])
        self.assertEqual(out["action"], "replan")
        self.assertIn("loop init", out["reason"])
        self.assertEqual(out["work"], [])

    def test_harden_no_progress_is_budget_with_work(self) -> None:
        items = [work("audit:AUD-A-001", "T-010")]
        stalled = {"batches": [batch(1, "t1"), batch(1, "t2")]}
        out = self.step(objective=HARDEN, harden=items, audit={"open": 1}, state=stalled)
        self.assertEqual((out["action"], out["work"], out["budget"]["no_progress_since"]), ("budget", items, "t1"))

    def test_signoff_package_from_release(self) -> None:
        """T-3549 (FLOW-16): harden hết việc + `release-check` trên cây này không FAIL → `signoff-package` kèm gói nháp
        (`candidate_head`, `evidence_fp`, `human_pending` = `human` ∪ việc chờ người); không "đã phát hành"."""
        rel = {"head": "b" * 40, "fails": [], "human": ["prod_switch"], "verdict": "GO (chờ người)"}
        out = self.step(objective=HARDEN, signoff={"release": rel, "release_changed": [], "deferred": ["T-9"]})
        self.assertEqual(out["action"], "signoff-package", out)
        want = {"candidate_head": HEAD, "evidence_fp": FP, "human_pending": ["T-9", "prod_switch"]}
        self.assertEqual(out["package"], want | {"release_verdict": "GO (chờ người)"})
        self.assertIn("CHƯA phát hành", out["reason"])
        self.assertIn("chờ người: T-9, prod_switch", out["reason"])
        self.assertEqual(out["missing"], ["chữ ký GO-NO-GO §5", "người xác nhận T-9", "người xác nhận prod_switch"])
        go = {**rel, "human": [], "verdict": "GO"}
        out = self.step(objective=HARDEN, signoff={"release": go, "release_changed": []})
        self.assertIn("chờ người: không", out["reason"])
        self.assertEqual(out["missing"], ["chữ ký GO-NO-GO §5"])
        self.assertIsNone(self.step()["package"])  # build không dựng gói

    def test_signoff_needs_fresh_passing_release(self) -> None:
        rel = {"head": "b" * 40, "fails": ["audit", "phase"], "human": [], "verdict": "NO-GO"}
        out = self.step(objective=HARDEN, signoff={"release": rel, "release_changed": []})
        self.assertEqual((out["action"], out["package"]), ("replan", None))
        self.assertIn("release-check NO-GO: FAIL audit, phase", out["reason"])
        self.assertEqual(out["missing"], ["`audit` PASS", "`phase` PASS"])
        ok = {**rel, "fails": [], "verdict": "GO"}
        for changed, note in ((["app.py"], f"1 file đổi sau {'b' * 12} (vd app.py)"), (None, "không có trong repo")):
            with self.subTest(changed):
                out = self.step(objective=HARDEN, signoff={"release": ok, "release_changed": changed})
                self.assertEqual(out["action"], "release-check")
                self.assertIn(note, out["reason"])
        out = self.step(objective=HARDEN, signoff={"release": ok, "release_changed": [], "evidence_fp": None})
        self.assertEqual(out["action"], "release-check")  # không có git: không dựng được gói
        self.assertNotIn("kết quả có ở", out["reason"])

    def test_signoff_package_expiry(self) -> None:
        """FLOW-17 (hàm thuần): gói khớp vân tay → còn hiệu lực; lệch → `release-check`, nêu phần đổi."""
        pkg = {"candidate_head": "c" * 40, "evidence_fp": FP, "human_pending": ["prod_switch"], "release_verdict": "GO"}
        out = self.step(objective=HARDEN, signoff={"package": pkg, "package_changed": ["GO-NO-GO.md?"]})
        self.assertEqual((out["action"], out["package"]), ("signoff-package", pkg))
        self.assertIn(f"gói nghiệm thu ở {'c' * 12} còn hiệu lực", out["reason"])
        old = {**pkg, "evidence_fp": "e" * 64}
        for changed, note in (
            (["app.py", "b.py"], f"2 file đổi sau {'c' * 12} (vd app.py, b.py)"),
            ([], "vân tay khác"),
            (None, f"head {'c' * 12} không có trong repo"),
        ):
            with self.subTest(changed):
                out = self.step(objective=HARDEN, signoff={"package": old, "package_changed": changed})
                self.assertEqual((out["action"], out["package"]), ("release-check", None))
                self.assertIn(f"gói nghiệm thu hết hạn: {note}", out["reason"])

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
        for tasks in ([["T-001", "x"]], []):  # sai kiểu / rỗng → đợt mới, không văng
            bad = {**dở, "objective": {"batches": [{**mark, "done": "t5", "tasks": tasks}]}}
            self.assertEqual(len(xt._batch_mark(bad, new, self.base)["batches"]), 2, tasks)
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

    def test_stop_hook_closes_loop_when_plan_undecodable(self) -> None:
        """Review #319 🟠: PLAN không đọc được như UTF-8 → verdict `blocked`; Stop hook vẫn đóng vòng (không traceback)."""
        xt.write_state(self.st(session_id="s1", objective={"batches": [batch(1, "t1")]}), self.base)
        (self.base / "P.md").write_bytes(b"\xe9\xff")
        rc, out, err = run_main("loop", "hook-stop", stdin=json.dumps({"session_id": "s1"}))
        self.assertEqual((rc, out), (0, ""))
        self.assertNotIn("Traceback", err)
        st = xt.read_state(self.base) or {}
        self.assertEqual((st["active"], st["final_verdict"]["verdict"]), (False, "blocked"))
        self.assertNotIn("done", st["objective"]["batches"][-1])
        self.assertEqual(xt._plan_pairs(self.base, "P.md"), [])

    def test_init_notes_reopened_batch(self) -> None:
        """D-230: init mở lại đợt đã xong vì PLAN chỉ nối thêm task → dòng ℹ trỏ PLAN-<đợt>.md."""
        mark = {**batch(1, "t1"), "plan": "P.md", "done": "t2", "tasks": xt._plan_pairs(self.base, "P.md")}
        xt.write_state(self.st(started="t0", objective={"batches": [mark]}), self.base)
        (self.base / "P.md").write_text(
            "- [x] `T-001` xong — Gate: `true`\n- [ ] `T-002` thêm — Gate: `true`\n", "utf-8"
        )
        rc, _, err = run_main("loop", "init", "--plan", "P.md", "--blueprint", "BP.md", "--force")
        self.assertEqual(rc, 0, err)
        self.assertIn("ℹ Đợt trước đã xong mà P.md không đổi hoặc chỉ nối thêm task", err)
        self.assertEqual(len((xt.read_state(self.base) or {})["objective"]["batches"]), 1)
        cases = {  # không ℹ: đợt mới (PLAN khác), đợt dở — tín hiệu từ `_same_batch`, không so `at` (review #319)
            "PLAN khác": ({**mark, "at": "t0"}, "P2.md"),
            "đợt dở": ({k: v for k, v in mark.items() if k not in ("done", "tasks")}, "P.md"),
        }
        (self.base / "P2.md").write_text("- [x] `T-001` xong — Gate: `true`\n", "utf-8")
        for name, (last, plan) in cases.items():
            with self.subTest(name):
                xt.write_state(self.st(started="t0", objective={"batches": [last]}), self.base)
                rc, _, err = run_main("loop", "init", "--plan", plan, "--blueprint", "BP.md", "--force")
                self.assertEqual(rc, 0, err)
                self.assertNotIn("ℹ Đợt trước đã xong", err)

    def test_audit_open_count(self) -> None:
        self.assertEqual(xt.audit_open_count(self.base / "không.md"), 0)
        book = self.base / "S.md"
        rows = ["| A-1 | 🔴 | mở |", "| A-2 | 🟠 | mở |", "| A-3 | 🟢 | mở |", "| A-4 | 🔴 | đã sửa |"]
        rows += ["| A-5 | 🔴 | chấp nhận |", "| A-6 | 🟠 | bác bỏ |"]
        book.write_text("## Phát hiện\n\n| ID | Mức | Trạng thái |\n|---|---|---|\n" + "\n".join(rows) + "\n", "utf-8")
        self.assertEqual(xt.audit_open_count(book), 2)


class HardenWorkTest(StateCase):
    """`harden_work` trên đĩa (không phải repo git: SHA phát hiện rỗng — khoá có SHA trong repo git ở FLOW-15)."""

    ROW = "| ID | Mức | Trạng thái | Tóm tắt | Bằng chứng | Gate | Ghi chú |\n|---|---|---|---|---|---|---|\n"

    def book(self, *rows: str) -> None:
        (self.base / "S.md").write_text("## Phát hiện\n\n" + self.ROW + "".join(f"| {r} |\n" for r in rows), "utf-8")

    def test_sources_ids_and_lines(self) -> None:
        self.book(
            "AUD-B-002 | 🔴 | mở | b (sau: T-001; files: x) exec: deep Gate: `rm -rf /` | x | `true` | —",
            "AUD-A-001 | 🟠 | mở | a | x | tay: bấm thử | —",
            "AUD-C-003 | 🟠 | đã sửa | c | x | `true` | #1",
            "AUD-D-004 | 🟢 | mở | d | x | `true` | —",
            "rác | 🟠 | mở | e | x | `true` | —",
        )
        items = xt.harden_work(self.base, self.st(), "S.md")
        self.assertEqual(
            [(w["id"], w["key"], w["gate"]) for w in items],
            [
                ("T-002", "audit:AUD-A-001", None),
                ("T-003", "audit:AUD-B-002", "true"),
                ("T-004", "must:AAA-001", None),
                ("T-005", "must:AAA-002", None),
            ],
        )
        self.assertEqual(xt.harden_work(self.base, self.st(), "S.md"), items)  # cùng đầu vào → cùng ID
        line = items[1]["line"]
        self.assertTrue(
            line.startswith("- [ ] `T-003` Sửa AUD-B-002 🔴: b [sau: T-001; files: x] exec deep Gate: rm"), line
        )
        self.assertTrue(line.endswith("(nguồn: audit:AUD-B-002) — Gate: `true`"), line)
        task = xt.parse_plan(self.write_plan(line))[0]
        self.assertEqual((task["gate"], task["after"], task["files"], task["tier"]), ("true", [], [], "default"))
        self.assertIn("Gate: chưa có — phiên chính điền lệnh kiểm", items[0]["line"])

    def write_plan(self, *lines: str) -> Path:
        plan = self.base / "P.md"
        plan.write_text("".join(f"{x}\n" for x in lines), "utf-8")
        return plan

    def test_planned_keeps_id_tick_and_reused_id_is_new(self) -> None:
        self.book("AUD-A-001 | 🟠 | mở | a | x | `true` | —")
        self.write_plan(
            "- [x] `T-001` xong — Gate: `true`",
            "- [x] `T-050` Sửa AUD-A-001 (nguồn: audit:AUD-A-001@abcdef123456) — Gate: `true`",
            "- [ ] `T-051` Đạt MUST AAA-001 (nguồn: must:AAA-001) — Gate: `true`",
            "- [ ] `T-052` giả (Gate: `x` (nguồn: must:AAA-002)) — Gate: `true`",
        )
        items = {w["key"]: w for w in xt.harden_work(self.base, self.st(), "S.md")}
        self.assertEqual((items["audit:AUD-A-001"]["id"], items["audit:AUD-A-001"]["checked"]), ("T-050", True))
        self.assertEqual((items["must:AAA-001"]["id"], items["must:AAA-001"]["checked"]), ("T-051", False))
        self.assertEqual(
            (items["must:AAA-002"]["id"], items["must:AAA-002"]["planned"]), ("T-053", False)
        )  # khoá trong Gate
        with unittest.mock.patch.object(xt, "_found_at", return_value="0123456789ab"):  # cùng ID gốc, phát hiện khác
            again = {w["ref"]: w for w in xt.harden_work(self.base, self.st(), "S.md")}
        self.assertEqual((again["AUD-A-001"]["id"], again["AUD-A-001"]["planned"]), ("T-053", False))  # cấp theo khoá
        with unittest.mock.patch.object(xt, "_found_at", return_value="abcdef123456"):
            same = {w["ref"]: w for w in xt.harden_work(self.base, self.st(), "S.md")}
        self.assertEqual(same["AUD-A-001"]["key"], "audit:AUD-A-001@abcdef123456")
        self.assertEqual((same["AUD-A-001"]["id"], same["AUD-A-001"]["checked"]), ("T-050", True))

    def test_ids_continue_after_other_plans_and_bad_inputs(self) -> None:
        self.book("AUD-A-001 | 🟠 | mở | " + "dài " * 60 + " | x | `true` | —")
        old = self.base / "docs" / "autopilot"
        old.mkdir(parents=True)
        (old / "PLAN-cũ.md").write_text("- [x] `T-3600` cũ — Gate: `true`\n", "utf-8")
        (old / "PLAN-hỏng.md").write_bytes(b"\xff")
        items = xt.harden_work(self.base, self.st(blueprint=None), "S.md")
        self.assertEqual([w["id"] for w in items], ["T-3601"])
        self.assertTrue(items[0]["title"].endswith("…"))
        self.assertEqual(len(items[0]["title"]), xt.HARDEN_TITLE_MAX)
        (self.base / "S.md").write_bytes(b"\xff")
        self.assertEqual(xt.harden_work(self.base, self.st(blueprint=None), "S.md"), [])
        self.assertEqual(xt._found_at(self.base, "S.md", "AUD-A-001"), "")  # không phải repo git
        self.assertIsNone(xt.evidence_fingerprint(self.base))
        self.assertIsNone(xt._changed_since(self.base, "a" * 40))  # không phải commit có trong repo
        self.assertIsNone(xt._changed_since(self.base, "HEAD"))  # chỉ nhận SHA đủ 40 ký tự

    def test_signoff_excluded_paths(self) -> None:
        for path in ("GO-NO-GO.md", "docs/ops/GO-NO-GO-2026-10-28-v3.28.0.md", "docs/autopilot/DECISIONS.md"):
            with self.subTest(path):
                self.assertTrue(xt._signoff_excluded(path))
        for path in ("app.py", "docs/GO-NO-GO.txt", "DECISIONS.md.bak", "x/autopilot/a", "MY-GO-NO-GO.md"):
            with self.subTest(path):
                self.assertFalse(xt._signoff_excluded(path))
        self.assertTrue(xt._signoff_excluded(".autopilot/state.json"))

    def test_facts_only_gather_for_harden(self) -> None:
        self.book("AUD-A-001 | 🟠 | mở | a | x | `true` | —")
        self.assertEqual(xt.next_step_facts(self.base, self.st(), "S.md", [])["harden"], [])
        f = xt.next_step_facts(self.base, self.st(), "S.md", [], "harden-to-signoff")
        self.assertEqual((f["objective"], len(f["harden"])), ("harden-to-signoff", 3))


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

    def test_cli_harden_prints_work_lines(self) -> None:
        self.write_state_done()
        self.enterContext(unittest.mock.patch.object(xt, "_step_audit", return_value=None))  # sổ: ca riêng
        rc, out, _ = run_main("loop", "next-step", "--objective", "harden-to-signoff", "--prs", "-", stdin="[]")
        self.assertEqual(rc, 0)
        self.assertIn("  mới - [ ] `T-002` Đạt MUST AAA-001 (blueprint) (nguồn: must:AAA-001)", out)
        (self.base / "P.md").write_text(
            "- [x] `T-001` xong — Gate: `true`\n- [x] `T-002` m (nguồn: must:AAA-001) — Gate: `true`\n"
            "- [ ] `T-003` m (nguồn: must:AAA-002) — Gate: `true`\n",
            encoding="utf-8",
        )
        ev = next(self.base.rglob("T-001.json")).with_name("T-002.json")  # bằng chứng xanh như T-001 của setUp
        ev.write_text(json.dumps({"task": "T-002", "exit_code": 0, "cmd": "true"}), encoding="utf-8")
        done = self.st(active=False, final_verdict={"verdict": "done", "reason": "x"})
        xt.write_state({**done, "deferred": {"T-003": {"reason": "ký"}}}, self.base)
        rc, out, _ = run_main("loop", "next-step", "--objective", "harden-to-signoff", "--prs", "-", stdin="[]")
        self.assertIn("  [x] - [ ] `T-002`", out)
        self.assertIn("  [ ] - [ ] `T-003`", out)

    def test_cli_release_and_package_inputs(self) -> None:
        """`--release`/`--package` sai dạng → exit 2 nêu tên cờ (không đoán kết quả cổng); gói nhận cả JSON `next-step`."""
        self.write_state_done()
        f = self.base / "in.json"
        rel = {"head": "b" * 40, "fails": [], "human": [], "verdict": "GO"}
        pkg = {"candidate_head": "c" * 40, "evidence_fp": FP, "human_pending": []}
        bad = {
            "--release": ("{", "[]", json.dumps({**rel, "head": "HEAD"}), json.dumps({**rel, "fails": "x"})),
            "--package": (json.dumps({"package": None}), json.dumps({**pkg, "evidence_fp": "x"}))
            + (json.dumps({**pkg, "human_pending": [1]}), "[]"),
        }
        for flag, texts in bad.items():
            for text in texts:
                with self.subTest(flag=flag, text=text):
                    f.write_text(text, encoding="utf-8")
                    rc, _, err = run_main(
                        "loop", "next-step", "--objective", HARDEN, "--prs", "-", flag, str(f), stdin="[]"
                    )
                    self.assertEqual(rc, 2)
                    self.assertIn(f"✗ {flag}: ", err)
        rc, _, err = run_main("loop", "next-step", "--release", str(self.base / "mất.json"), "--prs", "-", stdin="[]")
        self.assertEqual(rc, 2, err)
        f.write_text(json.dumps({"action": "signoff-package", "package": pkg}), encoding="utf-8")
        self.assertEqual(xt._read_package(str(f)), pkg | {"release_verdict": ""})
        f.write_text(json.dumps(rel | {"rows": [], "go": True}), encoding="utf-8")
        self.assertEqual(xt._read_release(str(f)), rel)

    def write_state_done(self) -> None:
        xt.write_state(self.st(active=False, final_verdict={"verdict": "done", "reason": "x"}), self.base)

    def test_init_refuses_undecodable_plan(self) -> None:
        """PLAN không đọc được như UTF-8 → `loop init` exit 2 kèm lý do, không traceback (review #319)."""
        (self.base / "P.md").write_bytes(b"\xe9\xff")
        rc, _, err = run_main("loop", "init", "--plan", "P.md")
        self.assertEqual(rc, 2)
        self.assertIn("✗ Không đọc được P.md như UTF-8", err)
        (self.base / "P.md").write_text("- [ ] `T-001` x — Gate: `true`\n", "utf-8")
        (self.base / "BP.md").write_bytes(b"\xe9\xff")
        rc, _, err = run_main("loop", "init", "--plan", "P.md", "--blueprint", "BP.md")
        self.assertEqual(rc, 2)
        self.assertIn("✗ Không đọc được BP.md như UTF-8", err)

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
