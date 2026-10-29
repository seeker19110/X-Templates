"""Test cho `delivery_phase: build|harden` (ADR-0031): pha build merge nhanh, hoãn review thành nợ; G7 đòi harden và hết nợ."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))
import xt
from test_merge import commit_base_xt, pr, run_main
from test_xt import audit_status_text

HEAD = "abc1234def"
AUTO = {"enabledBy": {"login": "a"}, "mergeMethod": "SQUASH"}
# Làn chuẩn vì > 150 dòng, không thuộc ngoại lệ cứng.
STANDARD = [
    {"path": "src/cart/total.py", "additions": 200, "deletions": 0},
    {"path": "tests/test_total.py", "additions": 10, "deletions": 0},
]
AUTH = [
    {"path": "src/auth/login.py", "additions": 1, "deletions": 0},
    {"path": "tests/test_login.py", "additions": 1, "deletions": 0},
]


def mark(clean: bool, head: str = HEAD) -> dict:
    return {"head": head, "clean": clean, "at": "2026-10-20T10:00:00Z"}


class DeliveryPhaseParseTest(unittest.TestCase):
    """Khoá `delivery_phase`: vắng/rỗng = harden; giá trị lạ bị doctor/ci-check từ chối; build chỉ khi nhánh đích đã commit
    VÀ cây làm việc đều build."""

    def setUp(self):
        self.base = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.enterContext(unittest.mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(self.base)}))

    def test_delivery_phase_error_values(self):
        for ok in ({}, {"delivery_phase": ""}, {"delivery_phase": "build"}, {"delivery_phase": "harden"}):
            self.assertIsNone(xt.delivery_phase_error(ok))
        err = xt.delivery_phase_error({"delivery_phase": "Build"}) or ""
        self.assertIn("delivery_phase 'Build' không hợp lệ (build|harden", err)

    def test_delivery_phase_needs_build_on_base_and_worktree(self):
        cases = [
            ("delivery_phase: build\n", None, "build", []),
            ("merge_autonomy: L3\n", None, "harden", []),  # khoá vắng = harden (dự án cũ không đổi)
            ("delivery_phase: harden\n", "delivery_phase: build\n", "harden", []),  # PR không tự chuyển sang build
            ("delivery_phase: build\n", "delivery_phase: harden\n", "harden", []),  # cây làm việc chặt hơn thắng
        ]
        for committed, working, want, notes in cases:
            with self.subTest(committed=committed, working=working):
                commit_base_xt(self.base, committed, working)
                self.assertEqual(xt.delivery_phase(self.base, "origin/main"), (want, notes))
        commit_base_xt(self.base, "delivery_phase: fast\n")
        phase, notes = xt.delivery_phase(self.base, "origin/main")
        self.assertEqual(phase, "harden")
        self.assertEqual(len(notes), 2)  # cây làm việc và nhánh đích cùng lạ
        self.assertIn("delivery_phase 'fast' không hợp lệ", notes[0])
        self.assertTrue(notes[0].endswith("— dùng harden"))
        self.assertEqual(xt.delivery_phase(self.base / "khong-co", "origin/main"), ("harden", []))  # không đọc được

    def test_delivery_phase_rejected_by_doctor_and_ci_check(self):
        (self.base / "xt.yaml").write_text('lint: x\ntypecheck: x\ntest: x\nbuild: x\ndelivery_phase: "ship"\n')
        found = [f for f in xt._doctor_xt_yaml(self.base, self.base) if f.code == "xt-yaml" and f.level == "error"]
        self.assertEqual(len(found), 1)
        self.assertIn("delivery_phase 'ship' không hợp lệ", found[0].msg)
        rc, out, _ = run_main("ci-check")
        self.assertEqual(rc, 1)
        self.assertIn("✗ xt.yaml: delivery_phase 'ship' không hợp lệ", out)
        (self.base / "xt.yaml").write_text("lint: x\ntypecheck: x\ntest: x\nbuild: x\ndelivery_phase: build\n")
        self.assertFalse([f for f in xt._doctor_xt_yaml(self.base, self.base) if f.level == "error"])
        self.assertEqual(run_main("ci-check")[0], 0)

    def test_delivery_phase_template_and_framework_repo_harden(self):
        tpl = xt.template_body((ROOT / "framework" / "templates" / "xt.yaml").read_text(encoding="utf-8"))
        self.assertEqual(xt._yaml_keys(tpl).get("delivery_phase"), "build")  # dự án đích mới (install.py copy mẫu)
        self.assertEqual(xt._xt_keys(ROOT).get("delivery_phase"), "harden")  # repo khung luôn production (D-136)


class DeliveryPhaseMergeTest(unittest.TestCase):
    """`merge_check_result`/`merge_eligibility` (ADR-0028 + ADR-0031): build hoãn review của PR làn chuẩn không thuộc ngoại
    lệ cứng; harden như cũ; ngoại lệ cứng (kể cả đã miễn người) và review `blocking` chặn ở mọi pha."""

    def result(self, files: list, phase: str, hard_auto: bool = False, **over: Any) -> dict:
        return xt.merge_check_result(pr(headRefOid=HEAD, files=files, **over), 3, [], hard_auto, phase)

    def test_delivery_phase_build_merges_standard_lane_without_review(self):
        d = self.result(STANDARD, "build")
        self.assertEqual((d["verdict"], d["lane"], d["delivery_phase"]), ("merge", "chuẩn", "build"))
        self.assertEqual(
            (d["review"], d["review_deferred"], d["eligible"], d["auto_merge_ok"]), ("deferred", True, True, True)
        )
        clean = self.result(STANDARD, "build", xtReviews=[mark(True)])  # có review sạch thì không còn nợ
        self.assertEqual((clean["review"], clean["review_deferred"], clean["eligible"]), ("ok", False, True))
        old = self.result(STANDARD, "build", xtReviews=[mark(True, "old0000000")])  # sạch ở head cũ = chưa rà head này
        self.assertEqual((old["review"], old["eligible"]), ("deferred", True))
        fast = self.result(pr()["files"], "build")  # làn nhanh: không có gì để hoãn
        self.assertEqual((fast["review"], fast["review_deferred"], fast["eligible"]), ("na", False, True))

    def test_delivery_phase_build_still_needs_green_ci_and_no_conflict(self):
        red = [{"__typename": "CheckRun", "name": "test", "status": "COMPLETED", "conclusion": "FAILURE"}]
        d = self.result(STANDARD, "build", statusCheckRollup=red)
        self.assertEqual((d["verdict"], d["eligible"], d["review_deferred"]), ("fix", False, True))
        d = self.result(STANDARD, "build", mergeable="CONFLICTING")
        self.assertEqual((d["verdict"], d["eligible"]), ("fix", False))

    def test_delivery_phase_harden_keeps_review_requirement(self):
        d = self.result(STANDARD, "harden")
        self.assertEqual(
            (d["review"], d["review_deferred"], d["eligible"], d["auto_merge_ok"]), ("missing", False, False, False)
        )
        d = xt.merge_check_result(pr(headRefOid=HEAD, files=STANDARD), 3, [], False)  # mặc định = harden
        self.assertEqual((d["delivery_phase"], d["eligible"]), ("harden", False))

    def test_delivery_phase_build_hard_exception_human_still_held(self):
        hard = self.result(AUTH, "build")  # merge_hard_exceptions: human → hard, người merge
        self.assertEqual(
            (bool(hard["hard"]), hard["review_deferred"], hard["eligible"], hard["auto_merge_ok"]),
            (True, False, False, False),
        )
        # auto (ADR-0020): máy merge được; pha build hoãn review thành nợ cả với ngoại lệ cứng đã miễn (ADR-0037, D-124)
        waived = self.result(AUTH, "build", hard_auto=True)
        self.assertEqual((waived["hard"], bool(waived["hard_waived"]), waived["verdict"]), ([], True, "merge"))
        self.assertEqual((waived["review"], waived["review_deferred"], waived["eligible"]), ("deferred", True, True))
        harden = self.result(AUTH, "harden", hard_auto=True)  # harden: lại cần review sạch
        self.assertEqual((harden["review"], harden["eligible"], harden["verdict"]), ("missing", False, "review"))
        ok = self.result(AUTH, "build", hard_auto=True, xtReviews=[mark(True)])
        self.assertEqual((ok["review"], ok["eligible"], ok["verdict"]), ("ok", True, "merge"))

    def test_delivery_phase_build_blocking_review_blocks(self):
        d = self.result(STANDARD, "build", xtReviews=[mark(False)])
        self.assertEqual(
            (d["review"], d["review_deferred"], d["eligible"], d["auto_merge_ok"]), ("blocking", False, False, False)
        )
        fast = self.result(pr()["files"], "build", xtReviews=[mark(False)])  # lỗi chặn trên làn nhanh cũng chặn
        self.assertEqual((fast["review"], fast["eligible"]), ("blocking", False))

    def test_delivery_phase_blocking_washed_by_push_not_deferred(self):
        old = "b" * 40  # review blocking ở head CŨ; head hiện tại khác (một lần push không "rửa" được lỗi chặn)
        d = self.result(STANDARD, "build", xtReviews=[mark(False, old)])
        self.assertEqual(
            (d["review"], d["review_deferred"], d["eligible"], d["auto_merge_ok"]), ("missing", False, False, False)
        )
        inc = {**mark(False, HEAD), "at": "2026-10-20T11:00:00Z", "inconclusive": True}
        d = self.result(STANDARD, "build", xtReviews=[mark(False, old), inc])  # chưa kết luận không gỡ lỗi chặn
        self.assertEqual((d["review"], d["eligible"]), ("missing", False))
        fixed = {**mark(True, "c" * 40), "at": "2026-10-20T11:00:00Z"}  # sạch (head cũ khác) sau blocking: lại hoãn
        d = self.result(STANDARD, "build", xtReviews=[mark(False, old), fixed])
        self.assertEqual((d["review"], d["review_deferred"], d["eligible"]), ("deferred", True, True))
        d = self.result(STANDARD, "build", xtReviews=[mark(False, old), fixed, inc])  # sạch rồi chưa kết luận: hoãn
        self.assertEqual((d["review"], d["eligible"]), ("deferred", True))
        d = self.result(STANDARD, "build", xtReviews=[{**inc, "head": old}])  # chỉ có review chưa kết luận: hoãn
        self.assertEqual((d["review"], d["eligible"]), ("deferred", True))
        self.assertEqual(self.result(STANDARD, "build")["review"], "deferred")  # chưa review lần nào: hoãn
        d = self.result(STANDARD, "harden", xtReviews=[mark(False, old)])  # harden không đổi
        self.assertEqual((d["review"], d["eligible"]), ("missing", False))
        d = self.result(STANDARD, "harden", xtReviews=[mark(False, old), fixed])
        self.assertEqual((d["review"], d["eligible"]), ("missing", False))

    def test_delivery_phase_risk_label_deferred_in_build_only(self):
        d = self.result(
            STANDARD, "build", labels=[{"name": "risk:perf"}]
        )  # pha build: nhãn risk: cũng thành nợ (ADR-0037)
        self.assertEqual((d["risk_labels"], d["review"], d["eligible"]), (["risk:perf"], "deferred", True))
        d = self.result(STANDARD, "harden", labels=[{"name": "risk:perf"}])
        self.assertEqual((d["review"], d["eligible"]), ("missing", False))
        d = self.result(STANDARD, "build", labels=[{"name": "risk:perf"}], xtReviews=[mark(True)])
        self.assertEqual((d["review"], d["eligible"]), ("ok", True))
        self.assertEqual(self.result(STANDARD, "build", labels=[{"name": "ui"}])["risk_labels"], [])


class DeliveryPhasePrNextTest(unittest.TestCase):
    """`pr next` ở pha build: PR làn chuẩn chưa rà đi thẳng tới merge ghim head, nói rõ "bỏ qua review, ghi nợ"."""

    H = "a" * 40

    def d(self, **over: Any) -> dict:
        base = {"pr": 7, "head": self.H, "verdict": "merge", "lane": "chuẩn", "stacked": False, "hard": []}
        base.update({"reasons": ["ok"], "next": "gh pr merge 7", "autonomy": 3, "delivery_phase": "build"})
        base.update(over)
        return base

    def test_delivery_phase_build_pr_next_skips_review(self):
        r = xt.pr_next(self.d(), False, {})
        self.assertEqual((r["action"], r["review_deferred"]), ("merge", True))
        self.assertTrue(
            r["why"].startswith("pha build: bỏ qua review, ghi nợ (ADR-0031) — làn chuẩn — merge-check = merge")
        )
        r = xt.pr_next(self.d(), True, {})  # người bật mà merge-check = merge: merge ghim head (D-063)
        self.assertEqual(r["action"], "merge")
        self.assertIn("pha build: bỏ qua review, ghi nợ", r["why"])
        r = xt.pr_next(self.d(verdict="wait", reasons=["CI đang chạy: test"]), True, {})  # chưa đủ: tắt
        self.assertEqual((r["action"], r["review_deferred"]), ("disable-auto-merge", True))
        r = xt.pr_next(self.d(verdict="wait", reasons=["CI đang chạy: test"]), False, {})
        self.assertEqual(r["action"], "wait")
        r = xt.pr_next(self.d(verdict="fix", reasons=["CI đỏ"], next="sửa"), False, {})  # chốt CI vẫn trước
        self.assertEqual((r["action"], r["why"]), ("fix", "CI đỏ"))

    def test_delivery_phase_harden_pr_next_asks_review(self):
        r = xt.pr_next(self.d(delivery_phase="harden"), False, {})
        self.assertEqual((r["action"], r["review_deferred"]), ("review", False))
        r = xt.pr_next(self.d(delivery_phase="harden"), False, {"reviews": [mark(True, self.H)]})
        self.assertEqual(r["action"], "merge")
        self.assertTrue(r["why"].startswith("review sạch ở head — merge-check = merge — merge ghim head"))

    def test_delivery_phase_build_pr_next_hard_and_blocking(self):
        r = xt.pr_next(self.d(hard_waived=["auth"]), False, {})  # ngoại lệ cứng đã miễn: pha build ghi nợ (ADR-0037)
        self.assertEqual((r["action"], r["review_deferred"]), ("merge", True))
        r = xt.pr_next(self.d(hard_waived=["auth"], delivery_phase="harden"), False, {})  # harden: đòi review
        self.assertEqual((r["action"], r["review_deferred"]), ("review", False))
        r = xt.pr_next(self.d(hard=["auth"]), False, {})
        self.assertEqual(r["action"], "defer-human")
        r = xt.pr_next(self.d(), True, {"reviews": [mark(False, self.H)]})  # lỗi chặn ở head: tắt auto-merge trước
        self.assertEqual((r["action"], r["review_deferred"]), ("disable-auto-merge", False))
        r = xt.pr_next(self.d(), False, {"reviews": [mark(False, self.H)]})
        self.assertEqual(r["action"], "fix")

    def test_delivery_phase_blocking_washed_pr_next_asks_review(self):
        old = [mark(False, "b" * 40)]  # lỗi chặn ở head cũ: sau push cần review lại head hiện tại, không merge
        r = xt.pr_next(self.d(), False, {"reviews": old})
        self.assertEqual((r["action"], r["review_deferred"]), ("review", False))
        r = xt.pr_next(self.d(), True, {"reviews": old})
        self.assertEqual(r["action"], "disable-auto-merge")
        r = xt.pr_next(self.d(risk_labels=["risk:perf"]), False, {})  # pha build: risk: thành nợ (ADR-0037)
        self.assertEqual((r["action"], r["review_deferred"]), ("merge", True))
        ok = [*old, {**mark(True, "c" * 40), "at": "2026-10-20T11:00:00Z"}]
        r = xt.pr_next(self.d(), False, {"reviews": ok})
        self.assertEqual((r["action"], r["review_deferred"]), ("merge", True))


class DeliveryPhaseCliTest(unittest.TestCase):
    """`merge-check`, `pr next` đọc pha từ xt.yaml (nhánh đích + cây làm việc)."""

    def setUp(self):
        self.base = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.enterContext(unittest.mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(self.base)}))
        commit_base_xt(self.base, "merge_autonomy: L3\ndelivery_phase: build\n")

    def check(self, p: dict, *extra: str) -> tuple[int, str]:
        rc, out, _ = run_main("merge-check", *extra, "--pr-json", "-", stdin=json.dumps(p))
        return rc, out

    def test_delivery_phase_merge_check_json_and_text(self):
        rc, out = self.check(pr(files=STANDARD), "--json")
        d = json.loads(out)
        self.assertEqual(
            (rc, d["eligible"], d["review_deferred"], d["delivery_phase"], d["notes"]), (0, True, True, "build", [])
        )
        rc, out = self.check(pr(files=STANDARD))
        self.assertEqual(rc, 0)
        self.assertIn("  - pha build: bỏ qua review, ghi nợ (ADR-0031) — chưa có review sạch ở head", out)
        commit_base_xt(self.base, "merge_autonomy: L3\ndelivery_phase: harden\n")
        rc, out = self.check(pr(files=STANDARD), "--json")
        d = json.loads(out)
        self.assertEqual((d["eligible"], d["review_deferred"], d["review"]), (False, False, "missing"))
        self.assertNotIn("ghi nợ", self.check(pr(files=STANDARD))[1])
        commit_base_xt(self.base, "merge_autonomy: L3\ndelivery_phase: nhanh\n")
        d = json.loads(self.check(pr(files=STANDARD), "--json")[1])
        self.assertEqual((d["delivery_phase"], d["eligible"]), ("harden", False))
        self.assertIn("delivery_phase 'nhanh' không hợp lệ (build|harden — ADR-0031) — dùng harden", d["notes"][0])

    def test_delivery_phase_pr_next(self):
        blocking = pr(files=STANDARD, autoMergeRequest=AUTO, xtReviews=[mark(False)])
        rc, out, _ = run_main("pr", "next", "--json", "--pr-json", "-", stdin=json.dumps(blocking))
        self.assertEqual(
            (rc, json.loads(out)["action"]), (0, "disable-auto-merge")
        )  # lỗi chặn: tắt auto-merge người bật
        rc, out, _ = run_main("pr", "next", "--pr-json", "-", stdin=json.dumps(pr(files=STANDARD)))
        self.assertEqual(rc, 0)
        self.assertIn("MERGE · PR #7", out)
        self.assertNotIn("AUTO-MERGE", out)
        self.assertIn("pha build: bỏ qua review, ghi nợ (ADR-0031)", out)


class DeliveryPhaseVerdictTest(unittest.TestCase):
    """ADR-0046: ở pha build vòng lặp `done` khi mọi task xanh dù blueprint còn MUST mở (`loop status --json` có
    `open_must`), và Stop hook cho dừng (`hook-stop` ghi `active=False`, `final_verdict.verdict == done`)."""

    def setUp(self):
        self.base = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.enterContext(unittest.mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(self.base)}))
        (self.base / "docs" / "autopilot").mkdir(parents=True)
        (self.base / "docs" / "autopilot" / "PLAN.md").write_text(
            "- [x] `T-001` xong — Gate: `true`\n", encoding="utf-8"
        )
        ev = self.base / ".autopilot" / "evidence"
        ev.mkdir(parents=True)
        (ev / "T-001.json").write_text(json.dumps({"task": "T-001", "exit_code": 0, "cmd": "true"}), encoding="utf-8")
        (self.base / "BP.md").write_text(
            "- [ ] `AAA-001` **MUST** a → Kiểm: t\n- [ ] `AAA-002` **MUST** b\n", encoding="utf-8"
        )
        (self.base / "xt.yaml").write_text("delivery_phase: build\n", encoding="utf-8")
        xt.write_state(
            {
                "active": True,
                "iterations": 0,
                "max_iterations": 9,
                "plan": "docs/autopilot/PLAN.md",
                "blueprint": "BP.md",
                "session_id": "s1",
            },
            self.base,
        )

    def test_build_phase_done_with_open_must_and_hook_stop_releases(self):
        rc, out, _ = run_main("loop", "status", "--json")
        d = json.loads(out)
        self.assertEqual((rc, d["verdict"], d["open_must"]), (0, "done", 2))
        self.assertIn("trả ở /complete (ADR-0046)", d["reason"])
        rc, out, _ = run_main("loop", "hook-stop", stdin=json.dumps({"session_id": "s1"}))
        self.assertEqual(
            (rc, sorted(json.loads(out))), (0, ["systemMessage"])
        )  # không git: không kiểm lại cuối, cho dừng
        st = xt.read_state(self.base) or {}
        self.assertEqual(
            (st["active"], st["final_verdict"]["verdict"], st["final_verdict"]["open_must"]), (False, "done", 2)
        )
        # Pha harden (xt.yaml đổi tại chỗ): vẫn đòi MUST như cũ.
        (self.base / "xt.yaml").write_text("delivery_phase: harden\n", encoding="utf-8")
        xt.write_state({**st, "active": True}, self.base)
        d = json.loads(run_main("loop", "status", "--json")[1])
        self.assertEqual((d["verdict"], d["task"]), ("continue", "AAA-001"))


class DeliveryPhaseReleaseTest(unittest.TestCase):
    """`release-check`: hàng `phase` (FAIL ở build/giá trị lạ) và `review_debt` (file ngoài tài liệu đổi sau SHA quét)."""

    def setUp(self):
        # Dọn thư mục tạm không làm đỏ test (assert không đổi): CI py311 #243 từng đỏ "Directory not empty: 'objects'" —
        # nghi git ghi `.git/objects` tách nền sau `commit` (chưa xác minh); `git()` còn tắt auto-maintenance.
        self.repo = Path(self.enterContext(tempfile.TemporaryDirectory(ignore_cleanup_errors=True))).resolve()
        self.enterContext(unittest.mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(self.repo)}))
        self.git("init", "-q", "-b", "main")
        (self.repo / "docs" / "ops").mkdir(parents=True)
        (self.repo / "src").mkdir()
        (self.repo / "src" / "app.py").write_text("x = 1\n", encoding="utf-8")
        self.status = self.repo / "docs" / "ops" / "AUDIT-STATUS.md"
        self.status.write_text(audit_status_text(), encoding="utf-8")
        self.commit("c0")

    def git(self, *args: str) -> str:
        # Không auto-maintenance/gc tách nền sau `commit` (lớp đỡ cho lỗi dọn thư mục tạm ở setUp).
        cfg = ["-c", "user.name=t", "-c", "user.email=t@example.invalid", "-c", "commit.gpgsign=false"]
        cfg += ["-c", "maintenance.auto=false", "-c", "gc.auto=0"]
        r = subprocess.run(["git", "-C", str(self.repo), *cfg, *args], capture_output=True, text=True, check=True)
        return r.stdout.strip()

    def commit(self, msg: str) -> str:
        self.git("add", "-A")
        self.git("commit", "-q", "-m", msg)
        return self.git("rev-parse", "HEAD")

    def scanned(self, groups: dict[int, str]) -> None:
        rows = {no: ("đã quét", sha, "2026-10-20", "quét") for no, sha in groups.items()}
        self.status.write_text(audit_status_text(rows), encoding="utf-8")

    def rows(self) -> dict:
        out = xt.release_check(self.repo, "BLUEPRINT.md", "docs/ops/AUDIT-STATUS.md")
        return {r["id"]: r for r in out["rows"]}

    def test_delivery_phase_release_phase_row(self):
        r = self.rows()["phase"]
        self.assertEqual((r["level"], r["result"]), ("BLOCKER", "PASS"))
        self.assertIn("vắng = harden", r["evidence"])
        (self.repo / "xt.yaml").write_text("delivery_phase: build\n", encoding="utf-8")
        r = self.rows()["phase"]
        self.assertEqual(r["result"], "FAIL")
        self.assertIn("đặt `delivery_phase: harden` rồi chạy audit delta", r["evidence"])
        (self.repo / "xt.yaml").write_text("delivery_phase: lai\n", encoding="utf-8")
        r = self.rows()["phase"]
        self.assertEqual(r["result"], "FAIL")
        self.assertIn("'lai' không hợp lệ", r["evidence"])
        (self.repo / "xt.yaml").write_text("delivery_phase: harden\n", encoding="utf-8")
        self.assertEqual(self.rows()["phase"]["result"], "PASS")
        rc, out, _ = run_main("release-check", "--json")
        self.assertIn("phase", [row["id"] for row in json.loads(out)["rows"]])

    def test_delivery_phase_release_review_debt_row(self):
        r = self.rows()["review_debt"]  # mọi nhóm N/A: không có SHA quét để so
        self.assertEqual((r["level"], r["result"]), ("SHOULD", "N/A"))
        s0 = self.git("rev-parse", "HEAD")
        self.scanned({1: s0, 9: s0})
        self.commit("sổ")
        r = self.rows()["review_debt"]
        self.assertEqual((r["level"], r["result"]), ("BLOCKER", "PASS"))  # chỉ sổ (tài liệu) đổi sau SHA quét
        (self.repo / "src" / "app.py").write_text("x = 2\n", encoding="utf-8")
        (self.repo / "ruff.toml").write_text("line-length = 100\n", encoding="utf-8")  # cấu hình cổng: không thuộc nhóm
        (self.repo / "docs" / "note.md").write_text("ghi chú\n", encoding="utf-8")
        s1 = self.commit("code sau SHA quét")
        r = self.rows()["review_debt"]
        self.assertEqual(r["result"], "FAIL")
        self.assertIn("2 file ngoài tài liệu đổi sau SHA quét (ruff.toml, src/app.py)", r["evidence"])
        self.assertIn("audit delta", r["evidence"])
        self.scanned({1: s1, 9: s0})  # audit delta phủ nhóm ARCH tới s1; ruff.toml tính từ SHA quét mới nhất (s1)
        self.commit("audit delta")
        self.assertEqual(self.rows()["review_debt"]["result"], "PASS")
        self.assertEqual(xt.review_debt(self.repo, self.status), ([], sorted({s0, s1})))
        self.scanned({1: s0, 9: s1})  # nhóm ARCH vẫn ở s0: src/app.py chưa phủ; ruff.toml đã phủ bởi SHA mới nhất
        self.commit("sổ lệch")
        self.assertEqual(xt.review_debt(self.repo, self.status)[0], ["src/app.py"])

    def merged_pr_world(self, pulls: dict, comments: dict, chain: list) -> None:
        """GitHub giả cho ADR-0057: `pulls/N` → `pulls[N]` (vắng → 404), comment PR → `comments[N]`; `_base_merge_chain`
        ghi lại đối số và trả `chain`."""

        def one(path: str) -> dict:
            n = path.rsplit("/", 1)[-1]
            if n not in pulls:
                raise xt.PrInputError(f"gh api {path} lỗi: HTTP 404")
            return pulls[n]

        def items(path: str) -> list:
            return comments.get(path.split("/issues/")[1].split("/")[0], [])

        self.chain_calls: list = []
        self.gh_one = self.enterContext(unittest.mock.patch.object(xt, "_gh_one", side_effect=one))
        self.enterContext(unittest.mock.patch.object(xt, "_gh_items", side_effect=items))
        self.enterContext(
            unittest.mock.patch.object(
                xt, "_base_merge_chain", side_effect=lambda *a: self.chain_calls.append(a) or chain
            )
        )

    @staticmethod
    def mark(head: str, verdict: str = "clean", login: str = "chu", assoc: str = "OWNER") -> dict:
        body = f"<!-- xt-review v1 head={head} verdict={verdict} -->"
        return {
            "body": body,
            "author_association": assoc,
            "user": {"login": login},
            "created_at": "2026-10-28T10:00:00Z",
        }

    def test_delivery_phase_review_debt_covered_by_merged_review(self):
        """ADR-0057: file nợ mà mọi commit nhánh chính chạm nó là squash của PR có review sạch ở head → PASS, không cần PR
        sổ chỉ để dời SHA (squash-merge làm SHA trong PR không bao giờ thành tổ tiên nhánh chính)."""
        s0 = self.git("rev-parse", "HEAD")
        self.scanned({1: s0, 9: s0})
        self.commit("sổ")
        (self.repo / "src" / "app.py").write_text("x = 2\n", encoding="utf-8")
        c5 = self.commit("feat: x (#5)")
        head, old = "a" * 40, "b" * 40
        pull = {"merged": True, "merge_commit_sha": c5, "head": {"sha": head}, "base": {"sha": s0}}
        pulls, comments, chain = {"5": dict(pull)}, {"5": [self.mark(head)]}, []
        self.merged_pr_world(pulls, comments, chain)
        r = self.rows()["review_debt"]
        self.assertEqual(r["result"], "PASS", r)
        self.assertIn("1 file đổi sau SHA quét đều từ PR có review sạch ở head (#5; ADR-0057)", r["evidence"])
        self.assertEqual(self.chain_calls[-1][1:], (s0, head))  # base.sha của PR đã merge vào phép mang review qua
        self.assertEqual(xt.review_debt(self.repo, self.status)[0], ["src/app.py"])  # Gate offline của PLAN không đổi
        for name, change, marks in (
            ("review ở head còn lỗi chặn", {}, [self.mark(head, "blocking")]),
            ("chưa rà head cuối", {}, [self.mark(old)]),
            ("dấu của người không có quyền ghi", {}, [self.mark(head, assoc="NONE", login="la")]),
            ("merge_commit_sha khác commit", {"merge_commit_sha": "c" * 40}, None),
            ("PR chưa merge", {"merged": False}, None),
        ):
            with self.subTest(name):
                pulls["5"] = {**pull, **change}
                comments["5"] = marks if marks is not None else [self.mark(head)]
                self.assertEqual(self.rows()["review_debt"]["result"], "FAIL")
        pulls.clear()  # không đọc được PR (404/offline) → vẫn là nợ
        self.assertEqual(self.rows()["review_debt"]["result"], "FAIL")
        pulls["5"], comments["5"] = dict(pull), [self.mark(old)]
        chain.append(old)  # head cuối chỉ là "cập nhật nhánh" sạch của head đã rà → review mang qua
        self.assertEqual(self.rows()["review_debt"]["result"], "PASS")
        (self.repo / "src" / "app.py").write_text("x = 3\n", encoding="utf-8")
        self.commit("sửa thẳng không qua PR")  # commit chạm file mà không phải squash của PR → còn nợ
        r = self.rows()["review_debt"]
        self.assertEqual(r["result"], "FAIL")
        self.assertNotIn("D-223", r["evidence"])  # danh tính không đổi: không nêu lý do danh tính

    def identity_case(self, at_scan: str | None, at_head: str | None, login: str, assoc: str) -> str:
        """SHA quét có `review_identity: at_scan` (None = không có xt.yaml), PR #5 đặt `at_head` ở HEAD rồi sửa
        `src/app.py`; `login` (`assoc`) đăng dấu sạch → kết quả hàng `review_debt`."""
        s0 = self.git("rev-parse", "HEAD")
        if at_scan is not None:
            (self.repo / "xt.yaml").write_text(f"review_identity: {at_scan}\n", encoding="utf-8")
            s0 = self.commit("cấu hình lúc quét")
        self.scanned({1: s0, 9: s0, 13: s0})
        self.commit("sổ")
        (self.repo / "src" / "app.py").write_text("x = 2\n", encoding="utf-8")
        if at_head is not None:
            (self.repo / "xt.yaml").write_text(f"review_identity: {at_head}\n", encoding="utf-8")
        c5 = self.commit("feat: x (#5)")
        head = "a" * 40
        pulls = {"5": {"merged": True, "merge_commit_sha": c5, "head": {"sha": head}, "base": {"sha": s0}}}
        self.merged_pr_world(pulls, {"5": [self.mark(head, login=login, assoc=assoc)]}, [])
        return str(self.rows()["review_debt"]["result"])

    def test_delivery_phase_review_debt_identity_set_in_debt(self):
        """Review #317 🔴: PR trong vùng nợ thêm `review_identity: mallory` rồi mallory (không quyền ghi) đăng dấu sạch."""
        self.assertEqual(self.identity_case(None, "mallory", "mallory", "NONE"), "FAIL")

    def test_delivery_phase_review_debt_identity_revoked(self):
        """D-223 (R1): danh tính ở SHA quét là oldbot, HEAD đã thu hồi sang newbot — dấu của oldbot không phủ; FAIL nêu
        lý do danh tính (không để người đọc tưởng PR thiếu review)."""
        self.assertEqual(self.identity_case("oldbot", "newbot", "oldbot", "NONE"), "FAIL")
        self.assertIn("`review_identity` ở SHA quét khác ở HEAD (D-223)", self.rows()["review_debt"]["evidence"])

    def test_delivery_phase_review_debt_identity_applied_after_scan(self):
        """D-223 (R2): SHA quét chưa có danh tính, HEAD áp `bot` — dấu của tác giả (OWNER, cái T-1508 loại ra) không phủ."""
        self.assertEqual(self.identity_case(None, "bot", "chu", "OWNER"), "FAIL")

    def test_delivery_phase_review_debt_identity_unchanged(self):
        """Danh tính trùng ở SHA quét và HEAD: dấu của đúng tài khoản đó được tin (như merge-check)."""
        self.assertEqual(self.identity_case("bot", None, "bot", "NONE"), "PASS")

    def test_delivery_phase_review_debt_rename_into_docs(self):
        """Review #320 (lớp AUD-SEC-132): `git mv src/app.py docs/app.md` sau SHA quét — `diff` dò rename chỉ cho tên
        mới (tài liệu) nên nợ bị bỏ sót; `--no-renames` cho cả tên cũ."""
        s0 = self.git("rev-parse", "HEAD")
        self.scanned({1: s0, 2: s0, 3: s0, 9: s0, 12: s0, 13: s0})
        self.commit("sổ")
        (self.repo / "docs").mkdir(exist_ok=True)
        self.git("mv", "src/app.py", "docs/app.md")
        self.commit("chuyển mã vào tài liệu")
        debt, _ = xt.review_debt(self.repo, self.status)
        self.assertIn("src/app.py", debt)

    def test_delivery_phase_review_debt_nested_docs_dir_is_code(self):
        """D-232: `src/api/docs/routes.py` là mã — sửa sau SHA quét vẫn là nợ (trước đây `(^|/)docs?/` loại nó)."""
        s0 = self.git("rev-parse", "HEAD")
        self.scanned({1: s0, 2: s0, 3: s0, 9: s0, 12: s0, 13: s0})
        self.commit("sổ")
        f = self.repo / "src" / "api" / "docs" / "routes.py"
        f.parent.mkdir(parents=True)
        f.write_text("x = 1\n", encoding="utf-8")
        (self.repo / "docs").mkdir(exist_ok=True)
        (self.repo / "docs" / "guide.md").write_text("x\n", encoding="utf-8")
        self.commit("mã trong docs lồng + tài liệu")
        (self.repo / "requirements.txt").write_text("x==1\n", encoding="utf-8")  # .txt phụ thuộc là mã (review #322)
        (self.repo / "license-allow.json").write_text("{}\n", encoding="utf-8")
        self.commit("phụ thuộc + allowlist license")
        debt, _ = xt.review_debt(self.repo, self.status)
        self.assertIn("src/api/docs/routes.py", debt)
        self.assertNotIn("docs/guide.md", debt)
        self.assertIn("requirements.txt", debt)
        self.assertIn("license-allow.json", debt)

    def test_delivery_phase_review_debt_since_per_file(self):
        """Review #317 🟠: mỗi file xét commit từ đúng SHA đưa nó vào nợ — lần đẩy thẳng mà sổ nhóm của file đã phủ (trước
        SHA của nhóm) không bị kéo vào chỉ vì một nhóm khác quét cũ hơn."""
        s0 = self.git("rev-parse", "HEAD")
        (self.repo / "ruff.toml").write_text(
            "line-length = 99\n", encoding="utf-8"
        )  # không thuộc nhóm: từ SHA mới nhất
        s1 = self.commit("cấu hình")
        (self.repo / "src" / "app.py").write_text("x = 2\n", encoding="utf-8")
        s2 = self.commit("sửa thẳng, đã được audit nhóm src phủ")
        self.scanned({1: s2, 2: s2, 3: s2, 12: s2, 9: s1, 13: s0})
        self.commit("sổ")
        (self.repo / "src" / "app.py").write_text("x = 3\n", encoding="utf-8")
        (self.repo / "ruff.toml").write_text("line-length = 100\n", encoding="utf-8")
        (self.repo / "xt.yaml").write_text("delivery_phase: harden\n", encoding="utf-8")  # nhóm HAR quét cũ nhất (s0)
        c5 = self.commit("feat: x (#5)")
        head = "a" * 40
        pulls = {"5": {"merged": True, "merge_commit_sha": c5, "head": {"sha": head}, "base": {"sha": s2}}}
        self.merged_pr_world(pulls, {"5": [self.mark(head)]}, [])
        since, _ = xt._review_debt_since(self.repo, self.status)
        self.assertEqual(since, {"src/app.py": s2, "ruff.toml": s2, "xt.yaml": s0})  # app.py không bị kéo về s0
        r = self.rows()["review_debt"]
        self.assertEqual(r["result"], "PASS", r)
        # file thuộc nhiều nhóm (ARCH quét ở s0, SEC ở s2): nhóm cũ hơn chưa phủ lần đẩy thẳng s0..s2 → xét từ s0, còn nợ
        self.scanned({1: s0, 2: s2, 3: s2, 12: s2, 9: s2, 13: s2})
        self.commit("sổ lệch nhóm")
        since, _ = xt._review_debt_since(self.repo, self.status)
        self.assertEqual(since["src/app.py"], s0)
        self.assertNotIn("src/app.py", xt.reviewed_debt(self.repo, since))

    def test_delivery_phase_review_debt_identity_read_at_oldest_scan(self):
        """`review_identity` so ở SHA quét CŨ nhất của các file nợ (phạm vi rộng nhất) với HEAD: đổi danh tính giữa hai
        lần quét → không phủ (chặt)."""
        (self.repo / "xt.yaml").write_text("review_identity: a\n", encoding="utf-8")
        s0 = self.commit("danh tính a")
        (self.repo / "xt.yaml").write_text("review_identity: b\n", encoding="utf-8")
        s1 = self.commit("danh tính b")
        self.scanned({1: s0, 2: s0, 3: s0, 12: s0, 9: s1, 13: s1})
        self.commit("sổ")
        (self.repo / "src" / "app.py").write_text("x = 2\n", encoding="utf-8")
        (self.repo / "ruff.toml").write_text(
            "line-length = 99\n", encoding="utf-8"
        )  # không nhóm: nợ từ s1 (danh tính b)
        c5 = self.commit("feat: x (#5)")
        head = "a" * 40
        pulls = {"5": {"merged": True, "merge_commit_sha": c5, "head": {"sha": head}, "base": {"sha": s1}}}
        self.merged_pr_world(pulls, {"5": [self.mark(head, login="b", assoc="NONE")]}, [])
        self.assertEqual(self.rows()["review_debt"]["result"], "FAIL")

    def test_delivery_phase_review_debt_special_file_names(self):
        """Review #317 (có từ trước): tên chứa `"`/`[` bị git trích dẫn / hiểu là glob → lệch nhóm, bỏ sót nợ. `diff -z` và
        `--literal-pathspecs`: tên thật được xếp đúng nhóm, PR có review phủ đúng file đó."""
        s_old = self.git("rev-parse", "HEAD")
        (self.repo / "src" / 'a"b.py').write_text("y = 1\n", encoding="utf-8")
        (self.repo / "src" / "[c].py").write_text("z = 1\n", encoding="utf-8")
        s_new = self.commit("tên đặc biệt")
        self.scanned({1: s_old, 9: s_new})
        self.commit("sổ")
        self.assertEqual(xt.review_debt(self.repo, self.status)[0], ["src/[c].py", 'src/a"b.py'])
        (self.repo / "src" / "c.py").write_text("w = 1\n", encoding="utf-8")  # glob `[c].py` không được khớp nhầm
        self.commit("feat: c (#5)")
        self.merged_pr_world({}, {}, [])
        since, _ = xt._review_debt_since(self.repo, self.status)
        self.assertEqual(xt.reviewed_debt(self.repo, {"src/[c].py": since["src/[c].py"]}), {})
        self.assertEqual(self.gh_one.call_count, 0)  # `[c].py` chỉ có commit trực tiếp — không hỏi PR #5 của c.py

    def test_delivery_phase_review_debt_no_commit_is_not_covered(self):
        """File nợ mà `git log` không thấy commit nào (lệch tên, lịch sử lạ) không được coi là đã phủ — all([]) = True."""
        s0 = self.git("rev-parse", "HEAD")
        self.merged_pr_world({}, {}, [])
        self.assertEqual(xt.reviewed_debt(self.repo, {"src/khong-co.py": s0}), {})

    def test_delivery_phase_review_debt_stops_asking_after_error(self):
        """Lỗi GitHub đầu tiên (404/offline) → thôi hỏi các commit còn lại (mỗi lượt có thể chờ GH_TIMEOUT); file vẫn là nợ."""
        s0 = self.git("rev-parse", "HEAD")
        self.scanned({1: s0, 9: s0})
        self.commit("sổ")
        for n in (5, 6):
            (self.repo / "src" / "app.py").write_text(f"x = {n}\n", encoding="utf-8")
            self.commit(f"feat: {n} (#{n})")
        self.merged_pr_world({}, {}, [])  # mọi PR 404
        self.assertEqual(self.rows()["review_debt"]["result"], "FAIL")
        self.assertEqual(self.gh_one.call_count, 1)  # chỉ hỏi commit đầu (#6)

    def test_delivery_phase_release_review_debt_unreadable_or_foreign_sha(self):
        self.scanned({1: "f" * 40})  # SHA không có trong lịch sử: hàng audit FAIL, review_debt không có SHA để so
        r = self.rows()["review_debt"]
        self.assertEqual(r["result"], "N/A")
        self.assertIn("không có SHA quét để so", r["evidence"])
        self.status.write_bytes(
            b"\xff\xfe"
        )  # không phải UTF-8: hàng audit FAIL có lý do, không traceback (AUD-CODE-017)
        r = xt._release_review_debt(self.repo, "docs/ops/AUDIT-STATUS.md")
        self.assertIn("không đọc được docs/ops/AUDIT-STATUS.md", r["evidence"])
        a = self.rows()["audit"]
        self.assertEqual(a["result"], "FAIL")
        self.assertIn("không đọc được docs/ops/AUDIT-STATUS.md", a["evidence"])
        self.status.unlink()
        r = self.rows()["review_debt"]
        self.assertEqual((r["result"], r["level"]), ("N/A", "SHOULD"))
        self.assertIn("xem hàng audit", r["evidence"])


if __name__ == "__main__":
    unittest.main()
