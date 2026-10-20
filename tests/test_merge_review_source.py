"""Audit 2026-10-19 rescan: một điều kiện merge (ADR-0028) thành cơ chế — AUD-XFEAT-010 (`merge-check` không gợi lệnh merge
khi chưa có review hợp lệ ở head), AUD-XFEAT-011 (`pr next`/steward đọc cùng nguồn review với `merge-gate`/`merge-check`/
guard; review cục bộ chưa đăng → bước "đăng lại review", không bật/tắt auto-merge thành vòng), AUD-DOC-054 (guard chặn
merge/bật auto-merge khi `eligible`/`auto_merge_ok` là false ở chính sách mặc định)."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / ".claude" / "hooks"))
import guard
import xt
from test_merge import GREEN, commit_base_xt, pr, run_main

HEAD = "c" * 40
AUTO = {"enabledBy": {"login": "a"}, "mergeMethod": "SQUASH"}
# Làn chuẩn vì > 150 dòng, không thuộc ngoại lệ cứng.
STANDARD = [
    {"path": "src/cart/total.py", "additions": 400, "deletions": 0},
    {"path": "tests/test_total.py", "additions": 10, "deletions": 0},
]
MODELS = ("--reviewer-model", "sonnet", "--author-model", "claude-opus-5-5")


def std(**over: Any) -> dict:
    return pr(headRefOid=HEAD, files=STANDARD, repo="o/r", **over)


def mark(clean: bool, head: str = HEAD, at: str = "2026-10-20T10:00:00Z") -> dict:
    return {"head": head, "clean": clean, "at": at}


class MergeCheckReviewStepTest(unittest.TestCase):
    """AUD-XFEAT-010: `eligible: false` → `merge-check`/`merge-watch` không in lệnh merge ghim head, verdict ≠ merge, exit 1;
    in bước review. Pha build (ADR-0031) giữ nguyên: PR không thuộc ngoại lệ cứng merge khi CI xanh, review hoãn thành nợ."""

    def setUp(self):
        self.base = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.enterContext(unittest.mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(self.base)}))
        commit_base_xt(self.base, "merge_autonomy: L3\n")

    def check(self, p: dict, *extra: str) -> tuple[int, str]:
        rc, out, _ = run_main("merge-check", *extra, "--pr-json", "-", stdin=json.dumps(p))
        return rc, out

    def test_merge_check_no_merge_command_without_review(self):
        rc, out = self.check(std())
        self.assertEqual(rc, 1)
        self.assertNotIn("match-head-commit", out)
        self.assertTrue(out.startswith("REVIEW · PR #7 · làn chuẩn"), out)
        self.assertIn(f"xt.py pr reviewed --pr 7 --head {HEAD}", out)
        rc, out = self.check(std(), "--json")
        d = json.loads(out)
        self.assertEqual((rc, d["verdict"], d["eligible"], d["review"]), (1, "review", False, "missing"))
        self.assertNotIn("next_rest", d)
        self.assertNotIn("match-head-commit", d["next"])

    def test_merge_check_blocking_review_points_to_fix(self):
        rc, out = self.check(std(xtReviews=[mark(False)]))
        self.assertEqual(rc, 1)
        self.assertNotIn("match-head-commit", out)
        self.assertIn("lỗi chặn", out)

    def test_merge_check_clean_review_still_merges(self):
        rc, out = self.check(std(xtReviews=[mark(True)]))
        self.assertEqual(rc, 0)
        self.assertTrue(out.startswith("MERGE · PR #7 · làn chuẩn"), out)
        self.assertIn(f"→ gh pr merge 7 --squash --match-head-commit {HEAD}", out)

    def test_merge_check_build_phase_still_merges_without_review(self):
        commit_base_xt(self.base, "merge_autonomy: L3\ndelivery_phase: build\n")
        rc, out = self.check(std())
        self.assertEqual(rc, 0)
        self.assertIn("pha build: bỏ qua review, ghi nợ (ADR-0031)", out)
        self.assertIn(f"→ gh pr merge 7 --squash --match-head-commit {HEAD}", out)
        rc, out = self.check(std(xtReviews=[mark(False)]))  # lỗi chặn vẫn chặn ở pha build
        self.assertEqual(rc, 1)
        self.assertNotIn("match-head-commit", out)

    def seed(self, reviews: list, standard_seen: bool = False) -> None:
        xt._write_reviews(self.base, {"7": {"reviews": reviews, "standard_seen": standard_seen}})

    def check_json(self, p: dict) -> tuple[int, dict]:
        rc, out = self.check(p, "--json")
        return rc, dict(json.loads(out))

    def test_merge_check_local_unpublished_blocking_blocks(self):
        """AUD-XFEAT-015 (D-104): review `clean:false` (lỗi chặn/chưa kết luận) chỉ có ở sổ cục bộ, đúng head hiện tại →
        `merge-check` trả `review`/`blocking` exit 1 ở cả pha build lẫn harden — trước đây pha build trả `merge` (deferred)."""
        local = {**mark(False), "at": "2026-10-20T10:00:00+00:00"}
        for phase in ("build", "harden"):
            commit_base_xt(self.base, f"merge_autonomy: L3\ndelivery_phase: {phase}\n")
            for name, row in (("blocking", local), ("inconclusive", {**local, "inconclusive": True})):
                with self.subTest(phase=phase, review=name):
                    self.seed([row])
                    rc, d = self.check_json(std())
                    self.assertEqual(
                        (rc, d["verdict"], d["review"], d["review_deferred"], d["eligible"], d["auto_merge_ok"]),
                        (1, "review", "blocking", False, False, False),
                    )
                    self.assertNotIn("match-head-commit", d["next"])
                    self.assertIn("lỗi chặn", d["next"])
                    res = GuardReviewMissingTest().final(d, f"gh pr merge 7 --squash --match-head-commit {HEAD}")
                    self.assertEqual((res["decision"], res.get("code")), ("deny", "REVIEW_MISSING"))

    def test_merge_check_local_book_only_stricter(self):
        """Sổ cục bộ chỉ làm chặt hơn: review sạch cục bộ không làm PR hợp lệ; lỗi chặn ở head cũ, cũ hơn dấu đã đăng ở head,
        hoặc khi `review_identity` (sổ của tác giả không tính) không đổi kết quả."""
        commit_base_xt(self.base, "merge_autonomy: L3\ndelivery_phase: build\n")
        self.seed([mark(True)])
        self.assertEqual(self.check_json(std())[1]["review"], "deferred")
        commit_base_xt(self.base, "merge_autonomy: L3\n")
        rc, d = self.check_json(std())  # harden: review sạch cục bộ chưa đăng không thay dấu đã đăng
        self.assertEqual((rc, d["review"], d["eligible"]), (1, "missing", False))
        self.seed([mark(False, head="a" * 40)])  # head cũ: không phải lỗi chặn của head hiện tại
        self.assertEqual(self.check_json(std(xtReviews=[mark(True)]))[0], 0)
        self.seed([{**mark(False), "at": "2026-10-20T09:00:00+00:00"}])  # đã có dấu sạch đăng sau nó ở head này
        self.assertEqual(self.check_json(std(xtReviews=[mark(True)]))[0], 0)
        self.seed([{**mark(False), "at": "2026-10-20T11:00:00+00:00"}])  # mới hơn dấu sạch: chặn
        self.assertEqual(self.check_json(std(xtReviews=[mark(True)]))[1]["review"], "blocking")
        self.assertEqual(self.check_json(std(xtReviews=[mark(True)], reviewIdentity="bot"))[0], 0)
        self.seed(
            [{**mark(False), "at": "2026-10-20T11:00:00+00:00"}, {**mark(True), "at": "2026-10-20T12:00:00+00:00"}]
        )
        self.assertEqual(self.check_json(std(xtReviews=[mark(True)]))[0], 0)  # review cuối ở head là sạch

    def test_merge_gate_and_steward_keep_published_source(self):
        """`merge-gate`/steward chạy ở CI (không có sổ cục bộ) — giữ nguồn dấu đã đăng, không đổi hành vi (D-104)."""
        commit_base_xt(self.base, "merge_autonomy: L3\ndelivery_phase: build\n")
        self.seed([mark(False)])
        on = {**std(), "autoMergeRequest": AUTO}
        rc, out, _ = run_main("merge-gate", "--json", "--pr-json", "-", stdin=json.dumps(on))
        self.assertEqual((rc, json.loads(out)["review"]), (0, "deferred"))
        rest = {**std(), "author": "a", "authorAssociation": "OWNER"}
        with unittest.mock.patch.object(xt, "_pr_rest", return_value=rest):
            out = xt._steward_one("7", "repos/o/r", self.base, False, [])
        self.assertEqual(out["action"], "republish-review")
        self.assertEqual(xt._steward_command(out, "repos/o/r"), [])

    def test_merge_check_local_standard_seen_keeps_strict(self):
        """AUD-XFEAT-016: PR từng vào làn chuẩn (sổ cục bộ `standard_seen`, chưa có nhãn) rồi thu về làn nhanh — `merge-check`
        vẫn đòi review ở head như `pr next`, không trả `merge`."""
        fast = pr(headRefOid=HEAD, files=[{"path": "README.md", "additions": 1, "deletions": 0}], repo="o/r")
        self.assertEqual(self.check_json(fast)[0], 0)
        self.seed([], standard_seen=True)
        rc, d = self.check_json(fast)
        self.assertEqual(
            (rc, d["verdict"], d["lane"], d["review"], d["eligible"]), (1, "review", "nhanh", "missing", False)
        )
        self.assertEqual(self.check_json({**fast, "xtReviews": [mark(True)]})[0], 0)
        pure = xt.merge_check_result(fast, 3, [], False, "harden", {"standard_seen": True})
        self.assertEqual(pure["review"], "missing")
        self.assertEqual(xt.merge_check_result(fast, 3, [], False, "harden", None)["review"], "na")

    def test_merge_watch_no_merge_command_without_review(self):
        with unittest.mock.patch.object(xt, "load_pr", return_value=std()):
            rc, out, _ = run_main("merge-watch", "--pr", "7")
        self.assertEqual(rc, 1)
        self.assertIn("REVIEW · PR #7", out)
        self.assertNotIn("match-head-commit", out)


class GuardReviewMissingTest(unittest.TestCase):
    """AUD-DOC-054: chính sách mặc định (ADR-0018) CHẶN merge ghim head/bật auto-merge khi `merge-check` (thật) báo chưa có
    review hợp lệ ở head; có review sạch hoặc pha build hoãn review → cho phép như trước."""

    MERGES = (
        f"gh pr merge 7 --squash --match-head-commit {HEAD}",
        f"gh api -X PUT repos/{{owner}}/{{repo}}/pulls/7/merge -f sha={HEAD} -f merge_method=squash",
        "gh pr merge 7 --auto --squash",
    )

    def final(self, d: dict, cmd: str) -> dict:
        with (
            unittest.mock.patch.object(guard, "merge_check", return_value=d),
            unittest.mock.patch.dict(os.environ, {"XT_GUARD_POLICY": ""}),
        ):
            return dict(guard.apply_policy(guard.bash_decision(cmd, str(ROOT))))

    def mcp(self, d: dict) -> dict:
        tool = {"owner": "o", "repo": "r", "pullNumber": 7, "expectedHeadSha": HEAD}
        with unittest.mock.patch.object(guard, "merge_check", return_value=d):
            dec, why = guard.mcp_decision("mcp__github__merge_pull_request", tool, str(ROOT))
        return dict(guard.apply_policy({"decision": dec, "reason": why}))

    def test_default_policy_review_missing_denies_merge(self):
        for reviews, state in (([], "missing"), ([mark(False)], "blocking")):
            d = xt.merge_check_result(std(xtReviews=reviews), 3, [], False)
            self.assertEqual((d["eligible"], d["auto_merge_ok"], d["review"]), (False, False, state))
            for cmd in self.MERGES:
                with self.subTest(state=state, cmd=cmd):
                    res = self.final(d, cmd)
                    self.assertEqual(res["decision"], "deny", res)
                    self.assertEqual(res["code"], "REVIEW_MISSING")
            self.assertEqual(self.mcp(d)["decision"], "deny")

    def test_default_policy_review_missing_denies_when_not_ready(self):
        """Review PR #182: PR chưa review mà `merge-check` trả `wait` (CI đang chạy, PR nháp) hay `fix` (conflict) —
        merge ghim head (gh/REST/MCP) vẫn bị chặn vì review, không lọt thành ask thường như `verdict != merge`."""
        running = [{**GREEN[0], "status": "IN_PROGRESS", "conclusion": ""}]
        cases = {
            "wait CI": std(statusCheckRollup=running),
            "wait nháp": std(isDraft=True),
            "fix conflict": std(mergeable="CONFLICTING"),
        }
        for name, p in cases.items():
            d = xt.merge_check_result(p, 3, [], False)
            self.assertEqual((d["eligible"], d["review"]), (False, "missing"), name)
            self.assertIn(d["verdict"], ("wait", "fix"), name)
            for cmd in self.MERGES:
                with self.subTest(name, cmd=cmd):
                    res = self.final(d, cmd)
                    self.assertEqual((res["decision"], res.get("code")), ("deny", "REVIEW_MISSING"), res)
            with self.subTest(name, cmd="mcp"):
                res = self.mcp(d)
                self.assertEqual((res["decision"], res.get("code")), ("deny", "REVIEW_MISSING"), res)

    def test_default_policy_not_ready_without_review_need_not_blocked(self):
        """Đối chứng: làn nhanh, pha build (review hoãn) và dưới L3 ở cùng verdict `wait`/`fix` không bị chặn vì review
        (hành vi cũ: ask thường, chính sách mặc định cho qua)."""
        running = [{**GREEN[0], "status": "IN_PROGRESS", "conclusion": ""}]
        fast = pr(headRefOid=HEAD, files=[{"path": "README.md", "additions": 1, "deletions": 0}], repo="o/r")
        cases = {
            "làn nhanh wait": xt.merge_check_result({**fast, "statusCheckRollup": running}, 3, [], False),
            "làn nhanh fix": xt.merge_check_result({**fast, "mergeable": "CONFLICTING"}, 3, [], False),
            "pha build wait": xt.merge_check_result(std(statusCheckRollup=running), 3, [], False, "build"),
            "pha build fix": xt.merge_check_result(std(mergeable="CONFLICTING"), 3, [], False, "build"),
            "L2 wait": xt.merge_check_result(std(statusCheckRollup=running), 2, [], False),
        }
        for name, d in cases.items():
            self.assertIn(d["verdict"], ("wait", "fix"), name)
            for cmd in (self.MERGES[0], self.MERGES[1]):
                with self.subTest(name, cmd=cmd):
                    res = self.final(d, cmd)
                    self.assertNotEqual(res.get("code"), "REVIEW_MISSING", res)
                    self.assertEqual(res["decision"], "", res)
            with self.subTest(name, cmd="mcp"):
                self.assertNotEqual(self.mcp(d).get("code"), "REVIEW_MISSING")

    UNPINNED = (
        "gh pr merge 7 --squash",
        "gh pr merge 7",
        "gh pr merge 7 --squash --delete-branch",
        f"gh pr merge 7 --squash --admin --match-head-commit {HEAD}",
        "gh pr -R o/r merge 7 --squash",
        "gh api -X PUT repos/o/r/pulls/7/merge -f merge_method=squash",
    )

    def mcp_unpinned(self, d: dict, tool: dict | None = None) -> dict:
        tool = tool or {"owner": "o", "repo": "r", "pullNumber": 7, "merge_method": "squash"}
        with unittest.mock.patch.object(guard, "merge_check", return_value=d):
            dec, why = guard.mcp_decision("mcp__github__merge_pull_request", tool, str(ROOT))
        return dict(guard.apply_policy({"decision": dec, "reason": why}))

    def test_default_policy_review_missing_unpinned(self):
        """AUD-HAR-093: merge KHÔNG ghim head (`gh pr merge 7 --squash`, `gh api` thiếu `sha`, MCP thiếu
        `expectedHeadSha`) của PR làn chuẩn chưa review/review chặn ở L3 → chặn `REVIEW_MISSING` như merge ghim head,
        không lọt thành ask thường mà chính sách mặc định cho qua."""
        for reviews, state in (([], "missing"), ([mark(False)], "blocking")):
            d = xt.merge_check_result(std(xtReviews=reviews), 3, [], False)
            self.assertEqual((d["eligible"], d["review"]), (False, state))
            for cmd in self.UNPINNED:
                with self.subTest(state=state, cmd=cmd):
                    res = self.final(d, cmd)
                    self.assertEqual((res["decision"], res.get("code")), ("deny", "REVIEW_MISSING"), res)
            for tool in (None, {"owner": "o", "repo": "r", "pullNumber": 7, "expectedHeadSha": HEAD, "x": 1}):
                with self.subTest(state=state, tool=tool):
                    res = self.mcp_unpinned(d, tool)
                    self.assertEqual((res["decision"], res.get("code")), ("deny", "REVIEW_MISSING"), res)

    def test_default_policy_review_missing_unpinned_controls(self):
        """Đối chứng AUD-HAR-093: review sạch, pha build (review hoãn), làn nhanh, dưới L3 → merge không ghim vẫn là ask
        thường (chính sách mặc định cho qua); strict vẫn hỏi."""
        fast = pr(headRefOid=HEAD, files=[{"path": "README.md", "additions": 1, "deletions": 0}], repo="o/r")
        cases = {
            "sạch": xt.merge_check_result(std(xtReviews=[mark(True)]), 3, [], False),
            "pha build": xt.merge_check_result(std(), 3, [], False, "build"),
            "làn nhanh": xt.merge_check_result(fast, 3, [], False),
            "L2": xt.merge_check_result(std(), 2, [], False),
        }
        for name, d in cases.items():
            for cmd in self.UNPINNED:
                with self.subTest(name, cmd=cmd):
                    res = self.final(d, cmd)
                    self.assertEqual((res["decision"], res.get("code")), ("", "OTHER_ASK"), res)
            with self.subTest(name, cmd="mcp"):
                self.assertEqual(self.mcp_unpinned(d)["decision"], "")
        d = xt.merge_check_result(std(), 3, [], False)
        with unittest.mock.patch.object(guard, "merge_check", return_value=d):
            res = guard.bash_decision(self.UNPINNED[0], str(ROOT))
        self.assertEqual(res["decision"], "ask")
        self.assertIn(guard.REVIEW_MISSING_ASK, str(res["reason"]))

    def test_default_policy_review_missing_strict_still_asks(self):
        d = xt.merge_check_result(std(), 3, [], False)
        with unittest.mock.patch.object(guard, "merge_check", return_value=d):
            res = guard.bash_decision(self.MERGES[0], str(ROOT))
        self.assertEqual(res["decision"], "ask")
        self.assertIn(guard.REVIEW_MISSING_ASK, str(res["reason"]))

    def test_default_policy_review_ok_or_deferred_allows(self):
        clean = xt.merge_check_result(std(xtReviews=[mark(True)]), 3, [], False)
        build = xt.merge_check_result(std(), 3, [], False, "build")
        for name, d in (("sạch", clean), ("pha build", build)):
            for cmd in (self.MERGES[0], self.MERGES[2]):
                with self.subTest(name, cmd=cmd):
                    self.assertEqual(self.final(d, cmd)["decision"], "allow")
            self.assertEqual(self.mcp(d)["decision"], "allow")


class ReviewSourceTest(unittest.TestCase):
    """AUD-XFEAT-011: `pr next`/steward tính review từ CÙNG nguồn với `merge-check`/`merge-gate`/guard (dấu đã đăng);
    sổ cục bộ chỉ để nhận ra review chưa đăng được → bước "đăng lại review"."""

    def test_xfeat011_one_liner(self):
        """Gate trong sổ AUDIT-STATUS: `pr next` không bật auto-merge khi `merge_eligibility` (nguồn đã đăng) không cho."""
        d = {
            "head": "H",
            "lane": "chuẩn",
            "verdict": "merge",
            "hard": [],
            "pr": 7,
            "autonomy": 3,
            "base_has_required": True,
        }
        rec = xt.with_published({"reviews": [{"head": "H", "clean": True, "at": "1"}]}, [])
        act = xt.pr_next(d, False, rec)["action"]
        self.assertFalse(act == "enable-auto-merge" and not xt.merge_eligibility(d, [])["auto_merge_ok"])
        self.assertEqual(act, "republish-review")

    def test_review_record_uses_published_only(self):
        local = [{"head": "f" * 40, "clean": True, "at": "2026-10-19T02:30:00+00:00"}]
        pub = [mark(True, "e" * 40, "2026-10-19T02:00:00Z"), mark(False, "d" * 40, "2026-10-19T01:30:00Z")]
        rec = xt.with_published({"reviews": local, "standard_seen": True}, pub)
        self.assertEqual([r["head"][0] for r in rec["reviews"]], ["d", "e"])
        self.assertEqual((rec["local_reviews"], rec["standard_seen"]), (local, True))
        ident = xt.with_published(
            {"reviews": local}, pub, True
        )  # review_identity: sổ của tác giả không tính, kể cả đăng lại
        self.assertEqual((len(ident["reviews"]), ident["local_reviews"]), (2, []))
        self.assertEqual(xt.with_published({"reviews": local}, None)["reviews"], [])
        self.assertEqual(xt.with_published({"reviews": ["rác"]}, ["rác"])["local_reviews"], [])

    def test_unpublished_review_steps(self):
        d = {"pr": 7, "head": HEAD, "verdict": "merge", "lane": "chuẩn", "hard": [], "autonomy": 3}
        d.update({"reasons": ["L3"], "next": "x", "base_has_required": True})
        clean = {"reviewer_model": "sonnet", "author_model": "claude-opus-5-5", **mark(True)}
        r = xt.pr_next(d, False, xt.with_published({"reviews": [clean]}, []))
        self.assertEqual(r["action"], "republish-review")
        self.assertEqual(
            r["do"],
            f"xt.py pr reviewed --pr 7 --head {HEAD} --clean --reviewer-model sonnet --author-model claude-opus-5-5",
        )
        r = xt.pr_next(d, True, xt.with_published({"reviews": [clean]}, []))  # đang bật: tắt trước
        self.assertEqual(r["action"], "disable-auto-merge")
        self.assertIn("chưa đăng", r["why"])
        # đã đăng đúng dấu đó: không còn bước đăng lại
        self.assertEqual(
            xt.pr_next(d, False, xt.with_published({"reviews": [clean]}, [mark(True)]))["action"], "enable-auto-merge"
        )
        # lỗi chặn cục bộ chưa đăng, dấu đã đăng còn sạch → đăng lại (không bật auto-merge trên review cũ)
        newer = {**mark(False), "at": "2026-10-20T11:00:00+00:00"}
        r = xt.pr_next(d, False, xt.with_published({"reviews": [clean, newer]}, [mark(True)]))
        self.assertEqual((r["action"], r["do"].split(" --head")[0]), ("republish-review", "xt.py pr reviewed --pr 7"))
        self.assertIn("--blocking", r["do"])
        # review cục bộ CŨ hơn dấu đã đăng mới nhất (phiên khác đã rà lại sau): dấu đã đăng quyết, không đăng lại
        later = {**mark(False), "at": "2026-10-20T12:00:00Z"}
        r = xt.pr_next(d, False, xt.with_published({"reviews": [clean]}, [later]))
        self.assertEqual(r["action"], "fix")
        self.assertIsNone(xt.unpublished_review(xt.with_published({"reviews": [clean]}, [later])))
        inc = {**mark(False), "inconclusive": True}
        self.assertIn("--inconclusive", xt.pr_next(d, False, xt.with_published({"reviews": [inc]}, []))["do"])
        old = {**mark(True)}  # sổ cũ không ghi model: chỗ trống cho agent điền
        self.assertIn(
            "--reviewer-model <M> --author-model <M>",
            xt.pr_next(d, False, xt.with_published({"reviews": [old]}, []))["do"],
        )
        # pha build: review sạch chưa đăng không chặn việc merge (review đang hoãn) — không bắt đăng lại
        b = {**d, "delivery_phase": "build"}
        r = xt.pr_next(b, False, xt.with_published({"reviews": [clean]}, []))
        self.assertEqual((r["action"], r["review_deferred"]), ("enable-auto-merge", True))
        # làn nhanh: lỗi chặn cục bộ chưa đăng vẫn phải đăng (trước đây sổ cục bộ làm PR strict)
        r = xt.pr_next({**d, "lane": "nhanh"}, False, xt.with_published({"reviews": [newer]}, []))
        self.assertEqual(r["action"], "republish-review")
        r = xt.pr_next({**d, "lane": "nhanh"}, False, xt.with_published({"reviews": [clean]}, []))
        self.assertEqual(r["action"], "enable-auto-merge")  # sạch, làn nhanh: không cần review
        # review chưa đăng của head CŨ: không đăng lại (head đã đổi → cần review mới ở head hiện tại)
        stale = {**newer, "head": "a" * 40}
        for lane in ("nhanh", "chuẩn"):
            r = xt.pr_next({**d, "lane": lane}, False, xt.with_published({"reviews": [stale]}, []))
            self.assertNotEqual(r["action"], "republish-review", lane)


class ReviewSourceChainTest(unittest.TestCase):
    """AUD-XFEAT-011, chuỗi bước như báo cáo audit: đăng dấu thất bại → `pr next` không bật auto-merge (bước đăng lại, ổn
    định qua nhiều lượt), `merge-gate` không đỏ; đăng xong → bật; bật rồi → chờ. Không có cặp bật/tắt nào lặp lại."""

    def setUp(self):
        self.base = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.enterContext(unittest.mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(self.base)}))
        commit_base_xt(self.base, "merge_autonomy: L3\n")
        self.publish = self.enterContext(unittest.mock.patch.object(xt, "_publish_review", return_value=3))

    def nxt(self, p: dict) -> dict:
        rc, out, _ = run_main("pr", "next", "--json", "--pr-json", "-", stdin=json.dumps(p))
        self.assertEqual(rc, 0)
        return dict(json.loads(out))

    def gate(self, p: dict) -> int:
        return run_main("merge-gate", "--pr-json", "-", stdin=json.dumps(p))[0]

    def test_publish_failure_no_auto_merge_loop(self):
        p = std()
        self.assertEqual(self.nxt(p)["action"], "review")
        rc, _, _ = run_main("pr", "reviewed", "--pr", "7", "--head", HEAD, "--clean", *MODELS)
        self.assertEqual(rc, 3)  # đăng thất bại (gh lỗi), sổ cục bộ đã ghi
        actions = []
        for _ in range(3):  # nhiều lượt: bước ổn định, không phải enable/disable xen kẽ
            out = self.nxt(p)
            actions.append(out["action"])
            self.assertEqual(self.gate(p), 0)  # không bật auto-merge → merge-gate không đỏ
        self.assertEqual(actions, ["republish-review"] * 3)
        self.assertIn(f"xt.py pr reviewed --pr 7 --head {HEAD} --clean", out["do"])
        self.assertNotIn("enable-auto-merge", actions)
        # merge-check cùng nguồn: chưa có dấu đã đăng → chưa merge
        rc, out, _ = run_main("merge-check", "--json", "--pr-json", "-", stdin=json.dumps(p))
        self.assertEqual((rc, json.loads(out)["verdict"]), (1, "review"))
        # đăng lại thành công → dấu có trên PR
        published = std(xtReviews=[mark(True, at="2026-10-20T12:00:00Z")])
        self.assertEqual(self.nxt(published)["action"], "enable-auto-merge")
        on = {**published, "autoMergeRequest": AUTO}
        self.assertEqual(self.gate(on), 0)  # cùng nguồn: merge-gate xanh khi pr next đã bảo bật
        self.assertEqual(
            self.nxt(on)["action"], "merge"
        )  # đã bật mà merge-check = merge: merge ghim head (D-063), không tắt
        pending = {**on, "statusCheckRollup": [{**GREEN[0], "status": "IN_PROGRESS", "conclusion": ""}]}
        self.assertEqual(self.nxt(pending)["action"], "wait")

    def test_steward_uses_published_source(self):
        run_main("pr", "reviewed", "--pr", "7", "--head", HEAD, "--clean", *MODELS)
        rest = {**std(), "author": "a", "authorAssociation": "OWNER"}
        with unittest.mock.patch.object(xt, "_pr_rest", return_value=rest):
            out = xt._steward_one("7", "repos/o/r", self.base, False, [])
        self.assertEqual(out["action"], "republish-review")
        self.assertEqual(xt._steward_command(out, "repos/o/r"), [])  # steward chỉ báo, không bật/merge


if __name__ == "__main__":
    unittest.main()
