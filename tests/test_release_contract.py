"""ADR-0068 lát A (D-355, PLAN-factory-A): hợp đồng kết quả/phát hành có kiểu — adapter đọc report (JUnit XML, SARIF,
`pip-audit` JSON), report bắt buộc của lệnh phát hành, digest artifact, `subject` và `promotion` trong `release-check --json`.
Ca âm ở ADR-0068 §Xác nhận A (sai digest, report thiếu, 0 test, scan chưa xong, duyệt chờ/từ chối/hết hạn) không được
`approved`; `go`/`verdict`/`human` và exit code giữ nghĩa cũ."""

import datetime as dt
import hashlib
import json
import os
import sys
import time
import unittest
import unittest.mock
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import xt
from test_xt import audit_status_text
from test_xt_cli import TmpDirCase, TmpRepoCase, run_main

JUNIT_OK = (
    '<?xml version="1.0"?><testsuites><testsuite name="s">'
    '<testcase name="a"/><testcase name="b"><skipped/></testcase><testcase name="c"/>'
    "</testsuite></testsuites>"
)
JUNIT_FAIL = '<testsuite><testcase name="a"><failure message="x"/></testcase><testcase name="b"/></testsuite>'
SARIF_OK = {"version": "2.1.0", "runs": [{"tool": {"driver": {"name": "t"}}, "results": [{"level": "warning"}]}]}
PIP_OK = {"dependencies": [{"name": "a", "version": "1", "vulns": []}, {"name": "b", "skip_reason": "local"}]}


def today(delta: int = 0) -> str:
    return (dt.datetime.now(dt.timezone.utc).date() + dt.timedelta(days=delta)).isoformat()


class ReportAdapterTest(TmpDirCase):
    """T-3675: `report_result` nhận dạng theo nội dung; kết quả có kiểu PASS/FAIL/PENDING/INCONCLUSIVE kèm số đếm."""

    def result(self, content, name: str = "r") -> dict:
        p = self.tmp / name
        p.write_text(content if isinstance(content, str) else json.dumps(content), encoding="utf-8")
        return xt.report_result(p)

    def test_junit(self):
        r = self.result(JUNIT_OK)
        self.assertEqual((r["kind"], r["status"], r["total"], r["failed"]), ("junit", "PASS", 2, 0))
        self.assertIn("1 bỏ qua", r["detail"])
        r = self.result(JUNIT_FAIL)
        self.assertEqual((r["status"], r["total"], r["failed"]), ("FAIL", 2, 1))
        r = self.result('<testsuite><testcase name="a"><error/></testcase></testsuite>')
        self.assertEqual((r["status"], r["failed"]), ("FAIL", 1))
        for zero in ("<testsuites/>", '<testsuite><testcase name="a"><skipped/></testcase></testsuite>'):
            with self.subTest(zero=zero):
                r = self.result(zero)
                self.assertEqual((r["status"], r["total"]), ("FAIL", 0))
                self.assertIn("0 test chạy", r["detail"])

    def test_sarif(self):
        r = self.result(SARIF_OK)
        self.assertEqual((r["kind"], r["status"], r["total"], r["failed"]), ("sarif", "PASS", 1, 0))
        bad = {"runs": [{"results": [{"level": "error"}, {"level": "note"}]}, {"results": []}]}
        r = self.result(bad)
        self.assertEqual((r["status"], r["total"], r["failed"]), ("FAIL", 2, 1))
        for pending, why in (
            ({"runs": []}, "chưa có run"),
            ({"runs": [{"tool": {}}]}, "không có `results`"),
            ({"runs": [{"results": [], "invocations": [{"executionSuccessful": False}]}]}, "executionSuccessful"),
        ):
            with self.subTest(why=why):
                r = self.result(pending)
                self.assertEqual(r["status"], "PENDING")
                self.assertIn(why, r["detail"])

    def test_pip_audit(self):
        r = self.result(PIP_OK)
        self.assertEqual((r["kind"], r["status"], r["total"], r["failed"]), ("pip-audit", "PASS", 1, 0))
        r = self.result([{"name": "a", "version": "1", "vulns": []}])  # dạng cũ: danh sách
        self.assertEqual(r["status"], "PASS")
        vulns = [{"id": "PYSEC-1"}, {"id": "GHSA-x"}]
        r = self.result({"dependencies": [{"name": "a", "version": "1", "vulns": vulns}]})
        self.assertEqual((r["status"], r["failed"]), ("FAIL", 2))
        r = self.result({"dependencies": [{"name": "b", "skip_reason": "x"}]})
        self.assertEqual((r["status"], r["total"]), ("PENDING", 0))
        self.assertIn("0 gói được quét", r["detail"])

    def test_pip_audit_counts_unique_ids(self):
        """AUD-HAR-317: mục cùng `id` trong một gói đếm một lần; id trùng ở hai gói là hai lỗ hổng (mỗi gói một bản
        vá); mục không có `id` chuỗi đếm riêng từng mục (không gộp nhầm thành một)."""
        dup = [{"id": "PYSEC-1"}, {"id": "PYSEC-1", "fix_versions": ["2"]}, {"id": "GHSA-x"}]
        deps = [
            {"name": "a", "version": "1", "vulns": dup},
            {"name": "b", "version": "1", "vulns": [{"id": "PYSEC-1"}]},
            {"name": "c", "version": "1", "vulns": [{}, {"id": 7}, "x", "x"]},
        ]
        r = self.result({"dependencies": deps})
        self.assertEqual((r["status"], r["total"], r["failed"]), ("FAIL", 3, 7))
        self.assertIn("3 gói, 7 lỗ hổng", r["detail"])

    def test_sarif_suppressions(self):
        """AUD-HAR-316, D-394 (SARIF §3.27.23, §3.35.3): kết quả error có `suppressions` khác rỗng mà mọi mục ghi
        `status` accepted không tính; vắng `status` (mặc định chưa xác minh — cách hiểu chặt), underReview/rejected,
        mảng rỗng, mục sai dạng → vẫn tính."""
        ok = [{"kind": "inSource", "status": "accepted"}]
        for sups, failed in (
            (ok, 0),
            ([{"kind": "external", "status": "accepted"}, *ok], 0),
            ([{"kind": "inSource"}], 1),  # vắng status: vẫn tính (D-394)
            ([*ok, {"kind": "external"}], 1),  # một mục vắng status → không bị chặn
            ([{"kind": "inSource", "status": "underReview"}], 1),
            ([{"kind": "inSource", "status": "rejected"}], 1),
            ([*ok, {"kind": "external", "status": "rejected"}], 1),  # một mục từ chối → không bị chặn
            ([], 1),  # mảng rỗng: không bị chặn
            (None, 1),
            ("accepted", 1),
            (["accepted"], 1),
            ([{"status": "Accepted"}], 1),  # giá trị khác enum (phân biệt hoa thường)
        ):
            with self.subTest(sups=sups):
                res = {"level": "error", "ruleId": "r", "suppressions": sups}
                r = self.result({"runs": [{"tool": {"driver": {"name": "codeql"}}, "results": [res]}]})
                self.assertEqual((r["status"], r["total"], r["failed"]), ("FAIL" if failed else "PASS", 1, failed))
                if failed:
                    self.assertNotIn("bỏ qua", r["detail"])
                else:
                    self.assertIn("1 đã chấp nhận (suppression) bỏ qua", r["detail"])
        for name in ("gitleaks", "GitLeaks"):  # công cụ quét bí mật: suppression không bao giờ bỏ qua (D-391, D-394)
            with self.subTest(name=name):
                res = {"ruleId": "r", "suppressions": ok}
                r = self.result({"runs": [{"tool": {"driver": {"name": name}}, "results": [res]}]})
                self.assertEqual((r["status"], r["total"], r["failed"]), ("FAIL", 1, 1))
                self.assertNotIn("bỏ qua", r["detail"])

    def test_sarif_level_from_rule(self):
        """Review lát A 🔴2: kết quả không ghi `level` lấy mức theo rule (§3.27.10) — override của invocation, rồi
        `defaultConfiguration` theo chỉ số hay id; `kind` khác `fail` là `none`; không gì cả → `warning`."""
        rules = [{"id": "W"}, {"id": "R", "defaultConfiguration": {"level": "error"}}]
        driver = {"tool": {"driver": {"name": "codeql", "rules": rules}}}
        for res, extra, failed in (
            ({"ruleId": "R", "ruleIndex": 1}, {}, 1),
            ({"ruleId": "R", "rule": {"index": 1}}, {}, 1),
            ({"ruleId": "R"}, {}, 1),  # theo id
            ({"ruleId": "R", "kind": "pass"}, {}, 0),
            ({"ruleId": "W", "ruleIndex": 0}, {}, 0),  # rule không có mức → warning
            ({"ruleIndex": 7}, {}, 0),  # chỉ số ngoài danh sách
            (  # override không khớp rule nào → lấy mức mặc định của rule
                {"ruleId": "R", "ruleIndex": 1},
                {
                    "invocations": [
                        {
                            "ruleConfigurationOverrides": [
                                {"descriptor": {"id": "X"}, "configuration": {"level": "note"}}
                            ]
                        }
                    ]
                },
                1,
            ),
            (
                {"ruleId": "W", "ruleIndex": 0},
                {
                    "invocations": [
                        {
                            "ruleConfigurationOverrides": [
                                {"descriptor": {"id": "W"}, "configuration": {"level": "error"}}
                            ]
                        }
                    ]
                },
                1,
            ),
            (
                {"ruleId": "R", "ruleIndex": 1},
                {
                    "invocations": [
                        {
                            "ruleConfigurationOverrides": [
                                {"descriptor": {"index": 1}, "configuration": {"level": "note"}},
                                5,
                            ]
                        }
                    ]
                },
                0,
            ),
        ):
            with self.subTest(res=res, extra=extra):
                r = self.result({"runs": [{**driver, **extra, "results": [res]}]})
                self.assertEqual(r["failed"], failed, r)

    def test_wrong_shapes_are_inconclusive_not_pass_or_crash(self):
        """Review lát A 🔴3 + 🟠6: chỉ mảng đúng dạng pip-audit mới là pip-audit; kiểu sai/lồng sâu không làm văng."""
        for content in (
            [{}],
            [{"filePath": "a.js", "errorCount": 3}],  # ESLint
            {"bomFormat": "CycloneDX", "dependencies": [{"ref": "x"}], "vulnerabilities": [{"id": "CVE-1"}]},
            {"dependencies": [{"name": "a", "version": "1", "vulns": 5}]},
            "[" * 100000,
        ):
            with self.subTest(content=str(content)[:40]):
                r = self.result(content)
                self.assertEqual(r["status"], "INCONCLUSIVE", r)
        for content, status in (
            ({"runs": 1}, "PENDING"),  # `runs` sai kiểu = không có run
            ({"runs": [{"results": [], "invocations": 5}]}, "PASS"),  # `invocations` sai kiểu bị bỏ qua
        ):
            with self.subTest(content=content):
                self.assertEqual(self.result(content)["status"], status)

    def test_junit_bom_and_skipped_error(self):
        """Review lát A 🟢14: BOM UTF-8 vẫn là JUnit; testcase vừa skipped vừa error tính là đã chạy và hỏng."""
        r = self.result("﻿" + JUNIT_OK)
        self.assertEqual((r["kind"], r["status"]), ("junit", "PASS"))
        r = self.result('<testsuite><testcase name="a"><skipped/><error/></testcase></testsuite>')
        self.assertEqual((r["status"], r["total"], r["failed"]), ("FAIL", 1, 1))

    def test_unknown_or_unreadable(self):
        for content, why in (
            ("<html/>", "không phải JUnit"),
            ("<testsuite>", "XML hỏng"),
            ("không phải report", "không phải XML/JSON"),
            ({"khac": 1}, "không nhận dạng"),
            ("42", "không nhận dạng"),
        ):
            with self.subTest(why=why):
                r = self.result(content)
                self.assertEqual((r["kind"], r["status"]), ("?", "INCONCLUSIVE"))
                self.assertIn(why, r["detail"])
        r = xt.report_result(self.tmp)  # thư mục: không đọc được
        self.assertEqual(r["status"], "INCONCLUSIVE")
        self.assertIn("không đọc được", r["detail"])


class ReleaseCase(TmpRepoCase):
    """Repo giả đủ để `release-check` GO trước khi thêm khoá của lát A (như `ReleaseCheckTest`)."""

    BP = (
        "---\ntitle: B\nkind: blueprint\nupdated: 2026-10-19\nscale: S\nprofile: cli-tool\n---\n\n## Checklist\n\n"
        "- [x] `BASE-X-001` **MUST** a — Kiểm: `true`\n"
    )

    def setUp(self):
        super().setUp()
        self.init_repo()
        self.enterContext(unittest.mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(self.repo)}))
        os.environ.pop("XT_RECORD_TIMEOUT", None)
        (self.repo / "docs" / "ops").mkdir(parents=True)
        (self.repo / "docs" / "ops" / "AUDIT-STATUS.md").write_text(audit_status_text(), encoding="utf-8")
        (self.repo / "BLUEPRINT.md").write_text(self.BP, encoding="utf-8")
        (self.repo / ".gitignore").write_text("out/\ndist/\n", encoding="utf-8")

    def setup_xt(self, **keys: str) -> None:
        (self.repo / "xt.yaml").write_text("".join(f"{k}: {v}\n" for k, v in keys.items()), encoding="utf-8")
        self.commit()

    def commit(self) -> None:
        self.git("add", "-A")
        self.git("commit", "-q", "--allow-empty", "-m", "c")

    def release(self) -> tuple[int, dict]:
        rc, out, _ = run_main("release-check", "--json")
        return rc, json.loads(out)

    @staticmethod
    def by_id(d: dict) -> dict:
        return {r["id"]: r for r in d["rows"]}


class ReleaseReportTest(ReleaseCase):
    """T-3676: `<key>_report` — exit 0 chưa đủ: report phải có, do lần chạy này sinh, kết quả PASS."""

    def junit_cmd(self, content: str) -> str:
        (self.repo / "in.xml").write_text(content, encoding="utf-8")
        return "mkdir -p out && cp in.xml out/junit.xml"

    def test_report_pass_records_result(self):
        self.setup_xt(acceptance=self.junit_cmd(JUNIT_OK), acceptance_report="out/junit.xml")
        rc, d = self.release()
        row = self.by_id(d)["acceptance"]
        self.assertEqual((rc, row["result"], d["verdict"]), (0, "PASS", "GO"), d)
        self.assertIn("report `out/junit.xml` junit PASS", row["evidence"])
        (res,) = d["results"]
        digest = hashlib.sha256((self.repo / "out" / "junit.xml").read_bytes()).hexdigest()
        self.assertEqual(
            (res["key"], res["path"], res["kind"], res["status"], res["total"], res["sha256"]),
            ("acceptance", "out/junit.xml", "junit", "PASS", 2, digest),
        )

    def test_report_fail_blocks(self):
        self.setup_xt(acceptance=self.junit_cmd(JUNIT_FAIL), acceptance_report="out/junit.xml")
        rc, d = self.release()
        row = self.by_id(d)["acceptance"]
        self.assertEqual((rc, row["result"], d["fails"]), (1, "FAIL", ["acceptance"]))
        self.assertIn("1/2 testcase hỏng", row["evidence"])
        self.assertEqual(d["promotion"]["state"], "blocked")

    def test_missing_stale_outside_report(self):
        self.setup_xt(acceptance="test -d .", acceptance_report="out/junit.xml")
        row = self.by_id(self.release()[1])["acceptance"]
        self.assertEqual(row["result"], "FAIL")
        self.assertIn("report `out/junit.xml` thiếu", row["evidence"])
        (self.repo / "out").mkdir()
        old = self.repo / "out" / "junit.xml"
        old.write_text(JUNIT_OK, encoding="utf-8")
        past = time.time() - 3600
        os.utime(old, (past, past))
        rc, d = self.release()
        row = self.by_id(d)["acceptance"]
        self.assertEqual((rc, row["result"]), (1, "FAIL"))
        self.assertIn("cũ hơn lần chạy", row["evidence"])
        self.assertEqual(d["results"][0]["status"], "STALE")
        self.setup_xt(acceptance="test -d .", acceptance_report="../ngoai.xml")
        row = self.by_id(self.release()[1])["acceptance"]
        self.assertEqual(row["result"], "FAIL")
        self.assertIn("ngoài dự án", row["evidence"])

    def test_exit_code_still_decides_first_and_no_key_is_old_behaviour(self):
        self.setup_xt(acceptance="false", acceptance_report="out/junit.xml")
        rc, d = self.release()
        self.assertEqual((rc, self.by_id(d)["acceptance"]["result"], d["results"]), (1, "FAIL", []))
        self.setup_xt(acceptance="test -d .")
        rc, d = self.release()
        self.assertEqual((rc, self.by_id(d)["acceptance"]["evidence"], d["results"]), (0, "`test -d .` exit 0", []))


class ReleaseArtifactTest(ReleaseCase):
    """T-3677: `release_artifacts` → hàng `artifacts` (chỉ khi khai) và `subject.digest`."""

    def art(self, data: bytes = b"bundle", sidecar: str | None = None) -> str:
        (self.repo / "dist").mkdir(exist_ok=True)
        (self.repo / "dist" / "a.tar.gz").write_bytes(data)
        if sidecar is not None:
            (self.repo / "dist" / "a.tar.gz.sha256").write_text(sidecar, encoding="utf-8")
        return hashlib.sha256(data).hexdigest()

    def test_no_key_no_row(self):
        self.setup_xt(acceptance="test -d .")
        rc, d = self.release()
        self.assertNotIn("artifacts", self.by_id(d))
        self.assertEqual((d["schema"], d["artifacts"], d["subject"]["digest"]), (3, [], None))
        self.assertEqual(d["subject"]["head"], d["head"])
        self.assertEqual(d["subject"]["tree"], xt.tree_fingerprint(self.repo))

    def test_digest_ok_and_mismatch(self):
        sha = self.art(sidecar=None)
        self.setup_xt(release_artifacts="dist/a.tar.gz")
        rc, d = self.release()
        row = self.by_id(d)["artifacts"]
        self.assertEqual((rc, row["result"], row["level"]), (0, "PASS", "BLOCKER"))
        self.assertEqual(d["artifacts"], [{"path": "dist/a.tar.gz", "sha256": sha, "expected": None, "problem": ""}])
        want = hashlib.sha256(f"dist/a.tar.gz\0{sha}\n".encode()).hexdigest()
        self.assertEqual(d["subject"]["digest"], want)
        self.art(sidecar=f"{sha.upper()}  a.tar.gz\n")  # định dạng sha256sum, chữ hoa vẫn khớp
        self.assertEqual(self.by_id(self.release()[1])["artifacts"]["result"], "PASS")
        self.art(sidecar="0" * 64 + "  a.tar.gz\n")
        rc, d = self.release()
        row = self.by_id(d)["artifacts"]
        self.assertEqual((rc, row["result"], d["fails"]), (1, "FAIL", ["artifacts"]))
        self.assertIn("digest lệch sidecar", row["evidence"])
        self.assertIsNone(d["subject"]["digest"])
        self.assertEqual(d["promotion"]["state"], "blocked")

    def test_missing_and_outside(self):
        self.setup_xt(release_artifacts="dist/khong-co.tgz ../ngoai.tgz")
        rc, d = self.release()
        row = self.by_id(d)["artifacts"]
        self.assertEqual((rc, row["result"]), (1, "FAIL"))
        self.assertEqual([a["problem"] for a in d["artifacts"]], ["thiếu file", "ngoài dự án"])
        self.assertIn("2/2 artifact lỗi", row["evidence"])

    def test_sidecar_by_declared_path_inside_project(self):
        """Review lát A 🟠5: sidecar lấy theo đường đã khai (artifact symlink không né được sidecar sai), phải trong dự án
        và đúng 64 hex — không in token của file khác ra `expected`."""
        build = self.repo / "build"
        build.mkdir()
        (build / "a-1.2.0.tar.gz").write_bytes(b"x")
        (self.repo / "dist").mkdir()
        (self.repo / "dist" / "a.tar.gz").symlink_to(build / "a-1.2.0.tar.gz")
        side = self.repo / "dist" / "a.tar.gz.sha256"
        side.write_text("0" * 64 + "\n", encoding="utf-8")
        self.assertEqual(xt._artifact(self.repo, "dist/a.tar.gz")["problem"], "digest lệch sidecar")
        side.unlink()
        secret = self.tmp / "ngoai.txt"
        secret.write_text("gh_token=ghp_fake_demo_0123456789\n", encoding="utf-8")
        side.symlink_to(secret)
        a = xt._artifact(self.repo, "dist/a.tar.gz")
        self.assertEqual((a["problem"], a["expected"]), ("sidecar ngoài dự án", None))
        side.unlink()
        side.write_text("gh_token=ghp_fake_demo_0123456789\n", encoding="utf-8")
        a = xt._artifact(self.repo, "dist/a.tar.gz")
        self.assertEqual((a["problem"], a["expected"]), ("sidecar không phải sha256", None))

    @unittest.skipIf(os.geteuid() == 0, "root đọc được file chmod 000")
    def test_unreadable_files_fail_not_crash(self):
        """Review lát A 🟠6: artifact, sidecar, report không đọc được → hàng FAIL/INCONCLUSIVE, không văng exit 2."""
        (self.repo / "dist").mkdir()
        art = self.repo / "dist" / "a.tar.gz"
        art.write_bytes(b"x")
        side = self.repo / "dist" / "a.tar.gz.sha256"
        side.write_text("0" * 64, encoding="utf-8")
        side.chmod(0)
        self.addCleanup(side.chmod, 0o644)
        self.assertIn("không đọc được sidecar", xt._artifact(self.repo, "dist/a.tar.gz")["problem"])
        art.chmod(0)
        self.addCleanup(art.chmod, 0o644)
        self.assertIn("không đọc được", xt._artifact(self.repo, "dist/a.tar.gz")["problem"])
        row, res = xt._release_report(self.repo, "acceptance", "dist/a.tar.gz", 0.0, "`x` exit 0")
        self.assertEqual((row["result"], res["status"], res["detail"]), ("FAIL", "MISSING", "không đọc được"))
        self.assertIn("không đọc được report", row["evidence"])


class PromotionTest(ReleaseCase):
    """T-3678: `promotion` — chỉ `approved` khi không FAIL, không N/A BLOCKER, GO-NO-GO của VERSION ký GO còn hạn và có
    dòng `subject: content` (+ `subject: digest` khi có artifact) khớp đủ 64 hex (D-389); máy không nâng `pending_human`.
    `go`/`verdict`/exit giữ nghĩa cũ."""

    SIGN = "## 5. Ký\n\n| Vai trò | Tên | Quyết định | Ngày |\n|---|---|---|---|\n"

    def setUp(self):
        super().setUp()
        (self.repo / "VERSION").write_text("1.2.0\n", encoding="utf-8")

    def go_no_go(self, decision: str = "GO", date: str = "", extra: str = "", content: bool = True) -> None:
        """GO-NO-GO v1.2.0 ký §5; `content` = ghi dòng `subject: content` của cây hiện tại (D-389) — file GO-NO-GO nằm
        ngoài vân tay nội dung nên tính trước khi ghi vẫn đúng sau commit."""
        line = f"subject: content {xt.subject_fingerprint(self.repo)}\n" if content else ""
        doc = self.repo / "docs" / "ops" / "GO-NO-GO-v1.2.0.md"
        doc.write_text(
            f"# GO/NO-GO v1.2.0\n\n{line}{extra}\n{self.SIGN}| Chủ repo | An | {decision} | {date or today()} |\n",
            "utf-8",
        )
        self.commit()

    def promotion(self) -> tuple[int, dict, dict]:
        rc, d = self.release()
        return rc, d, d["promotion"]

    def test_pending_until_signed_then_approved(self):
        self.setup_xt()
        rc, d, p = self.promotion()
        self.assertEqual((rc, d["verdict"], p["state"]), (0, "GO (chờ người)", "pending_human"))
        self.assertEqual(p["reasons"], ["go_no_go"])
        self.go_no_go()
        rc, d, p = self.promotion()
        self.assertEqual((rc, d["verdict"], p["state"]), (0, "GO", "approved"), p)
        self.assertEqual(p["reasons"], ["docs/ops/GO-NO-GO-v1.2.0.md"])
        _, out, _ = run_main("release-check")
        self.assertIn("promotion: approved", out)

    def test_decision_allowlist(self):
        """Review lát A 🔴1: chỉ ô đúng GO (kèm phiên bản được) là duyệt; biến thể NO-GO/từ chối → `rejected`; ô trống,
        ô mẫu "GO / NO-GO" chưa chọn, chữ khác → `pending_human` (máy không tự nhận là người đã từ chối)."""
        self.setup_xt()
        for decision, state in (
            ("GO", "approved"),
            ("go v1.2.0", "approved"),
            ("NO-GO", "rejected"),
            ("NO GO", "rejected"),
            ("NOGO", "rejected"),
            ("NO–GO", "rejected"),
            ("Từ chối", "rejected"),
            ("Không duyệt", "rejected"),
            ("GO / NO-GO", "pending_human"),
            ("", "pending_human"),
            ("Hoãn", "pending_human"),
            ("GOOD", "pending_human"),
        ):
            with self.subTest(decision=decision):
                self.go_no_go(decision)
                rc, d, p = self.promotion()
                self.assertEqual((rc, d["verdict"], p["state"]), (0, "GO", state), p)

    def test_every_signed_document_counts(self):
        """Review lát A 🟠4: hai GO-NO-GO cùng VERSION — một bản NO-GO là `rejected` bất kể thứ tự file."""
        self.setup_xt()
        self.go_no_go()
        (self.repo / "GO-NO-GO.md").write_text(
            f"# GO/NO-GO v1.2.0\n\n{self.SIGN}| Bảo mật | Chi | NO-GO | {today()} |\n", encoding="utf-8"
        )
        self.commit()
        rc, d, p = self.promotion()
        self.assertEqual((rc, p["state"]), (0, "rejected"))
        self.assertIn("GO-NO-GO.md", p["reasons"][0])
        (self.repo / "GO-NO-GO.md").write_text(
            f"# GO/NO-GO v1.2.0\n\n{self.SIGN}| Bảo mật | Chi | GO | {today(-40)} |\n", encoding="utf-8"
        )
        self.commit()
        _, _, p = self.promotion()
        self.assertEqual(p["state"], "pending_human")
        self.assertIn("hết hạn", p["reasons"][0])

    def test_failing_reports_never_approved(self):
        """ADR-0068 §Xác nhận A end-to-end: 0 test, scan chưa xong → `blocked` dù GO-NO-GO đã ký GO còn hạn."""
        self.go_no_go()
        (self.repo / "zero.xml").write_text("<testsuites/>", encoding="utf-8")
        (self.repo / "pending.sarif").write_text(json.dumps({"runs": [{"tool": {}}]}), encoding="utf-8")
        for src in ("zero.xml", "pending.sarif"):
            with self.subTest(src=src):
                self.setup_xt(acceptance=f"mkdir -p out && cp {src} out/r", acceptance_report="out/r")
                rc, d, p = self.promotion()
                self.assertEqual((rc, p["state"], p["reasons"]), (1, "blocked", ["acceptance"]))

    def test_unsigned_or_bad_date(self):
        """Không có §5 → chưa ký (cùng luật hàng `go_no_go`); ngày dạng số nhưng không có thật → chờ người, không văng."""
        self.setup_xt()
        doc = self.repo / "docs" / "ops" / "GO-NO-GO-v1.2.0.md"
        doc.write_text("# GO/NO-GO v1.2.0\n\nchưa có mục ký\n", encoding="utf-8")
        self.commit()
        rc, d, p = self.promotion()
        self.assertEqual((rc, p["state"], p["reasons"]), (0, "pending_human", ["go_no_go"]))
        self.go_no_go(date="2026-13-40")
        _, _, p = self.promotion()
        self.assertEqual(p["state"], "pending_human")
        self.assertIn("ngày ký không hợp lệ (2026-13-40)", p["reasons"][0])

    def test_expired_future_and_days_key(self):
        self.setup_xt()
        self.go_no_go(date=today(-40))
        _, d, p = self.promotion()
        self.assertEqual((d["verdict"], p["state"]), ("GO", "pending_human"))
        self.assertIn("hết hạn", p["reasons"][0])
        self.setup_xt(release_approval_days="60")
        self.go_no_go(date=today(-40))  # xt.yaml đổi = nội dung đổi: ký lại (D-389)
        self.assertEqual(self.promotion()[2]["state"], "approved")
        for bad in ("0", "x"):  # sai → mặc định 30 ngày
            with self.subTest(bad=bad):
                self.setup_xt(release_approval_days=bad)
                self.go_no_go(date=today(-40))
                _, _, p = self.promotion()
                self.assertEqual(p["state"], "pending_human")
                self.assertIn("hết hạn", p["reasons"][0])
        self.setup_xt()
        self.go_no_go(date=today(1))  # người ký ở múi giờ đi trước UTC (review lát A 🟢11)
        self.assertEqual(self.promotion()[2]["state"], "approved")
        self.go_no_go(date=today(3))
        _, _, p = self.promotion()
        self.assertEqual(p["state"], "pending_human")
        self.assertIn("tương lai", p["reasons"][0])

    def test_content_line_required_and_formats(self):
        """D-389: chữ ký gắn ứng viên bằng dòng `subject: content <64 hex>` — thiếu → chờ người, lý do nói rõ dòng cần ghi
        kèm giá trị; dạng trích dẫn/gạch đầu dòng/backtick, khoá không phân biệt hoa thường đều nhận."""
        self.setup_xt()
        self.go_no_go(content=False)
        _, d, p = self.promotion()
        fp = d["subject"]["content"]
        self.assertRegex(fp, r"^[0-9a-f]{64}$")
        self.assertEqual(fp, xt.subject_fingerprint(self.repo))
        self.assertEqual(p["state"], "pending_human")
        self.assertIn(f"thiếu dòng `subject: content {fp}`", p["reasons"][0])
        for line in (
            f"subject: content {fp}",
            f"> subject: content `{fp}`",
            f"> > - Subject: Content {fp}",
            f"* SUBJECT:content `{fp}`  ",
            f"  + subject : content {fp.upper()}",
        ):
            with self.subTest(line=line):
                self.go_no_go(extra=line, content=False)
                self.assertEqual(self.promotion()[2]["state"], "approved")
        for line in (
            f"subject: content {fp} (ký)",  # chữ thừa sau hex: không phải dòng subject
            f"Ghi chú subject: content {fp}",  # không ở đầu dòng
            f"subject: tree {fp}",
        ):
            with self.subTest(line=line):
                self.go_no_go(extra=line, content=False)
                _, _, p = self.promotion()
                self.assertEqual(p["state"], "pending_human")
                self.assertIn("thiếu dòng `subject: content", p["reasons"][0])

    def test_content_must_match_all_64_hex(self):
        """So đủ 64 hex: 12 ký tự đầu (luật cũ) hay một dòng lệch trong nhiều dòng cùng loại → ứng viên khác."""
        self.setup_xt()
        fp = xt.subject_fingerprint(self.repo)
        other = hashlib.sha256(b"khac").hexdigest()
        for extra in (
            "",  # chỉ có dòng do helper ghi: không lặp
            f"subject: content {fp[:12]}",
            f"subject: content {other}",
            f"subject: content {fp}0",
        ):
            with self.subTest(extra=extra):
                self.go_no_go(extra=extra, content=not extra)
                _, _, p = self.promotion()
                if not extra:
                    self.assertEqual(p["state"], "approved", p)
                    continue
                self.assertEqual(p["state"], "pending_human")
                self.assertIn("chữ ký gắn ứng viên khác", p["reasons"][0])
                self.assertIn(f"`subject: content {fp}`", p["reasons"][0])
        self.go_no_go(extra=f"subject: content {other}")  # dòng đúng (helper) + dòng lệch → lệch
        _, _, p = self.promotion()
        self.assertEqual(p["state"], "pending_human")
        self.assertIn("chữ ký gắn ứng viên khác", p["reasons"][0])

    def test_code_change_after_signing_is_not_approved(self):
        """AUD-HAR-219: ký ở commit A rồi đổi mã (commit B, không khai `release_artifacts`) → không còn `approved`."""
        self.setup_xt()
        self.go_no_go()
        self.assertEqual(self.promotion()[2]["state"], "approved")
        (self.repo / "app.py").write_text("print('khac')\n", encoding="utf-8")
        self.commit()
        rc, d, p = self.promotion()
        self.assertEqual((rc, d["verdict"], p["state"]), (0, "GO", "pending_human"), p)
        self.assertIn("chữ ký gắn ứng viên khác", p["reasons"][0])

    def test_signoff_only_commits_keep_approval(self):
        """Commit chỉ sửa GO-NO-GO/DECISIONS/PROGRESS (commit ký, ghi quyết định) không đổi vân tay nội dung."""
        self.setup_xt()
        self.go_no_go()
        doc = self.repo / "docs" / "ops" / "GO-NO-GO-v1.2.0.md"
        doc.write_text(doc.read_text(encoding="utf-8") + "\nGhi chú sau ký.\n", encoding="utf-8")
        (self.repo / "docs" / "autopilot").mkdir(parents=True)
        (self.repo / "docs" / "autopilot" / "DECISIONS.md").write_text("# Quyết định\n", encoding="utf-8")
        (self.repo / "PROGRESS.md").write_text("# Tiến độ\n", encoding="utf-8")
        self.commit()
        rc, d, p = self.promotion()
        self.assertEqual((rc, p["state"]), (0, "approved"), p)

    def test_subject_excludes_only_signoff_files(self):
        """AUD-HAR-319 (D-393): `subject.content` chỉ loại GO-NO-GO*.md nằm trực tiếp ở `GO_NO_GO_DIRS`, sổ
        `DECISIONS_LOG`, `PROGRESS.md` gốc và `.autopilot/` — file cùng TÊN ở chỗ khác là mã/tài liệu dự án: đổi sau khi
        ký → chờ người ký lại. Vân tay gói stage (`evidence_fingerprint`) giữ luật cũ."""
        self.setup_xt()
        for rel in (
            "src/DECISIONS.md",
            "src/x/GO-NO-GO-y.md",
            "docs/PROGRESS.md",
            "docs/research/DECISIONS.md",
            "docs/ops/old/GO-NO-GO-a.md",
            "docs/autopilot/DECISIONS-2026-11.md",  # bản tháng: ngoài tập loại trừ (chặt)
        ):
            with self.subTest(rel=rel):
                self.go_no_go()
                self.assertEqual(self.promotion()[2]["state"], "approved")
                before = xt.evidence_fingerprint(self.repo)
                f = self.repo / rel
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text(f"mã {rel}\n", encoding="utf-8")
                self.commit()
                _, _, p = self.promotion()
                self.assertEqual(p["state"], "pending_human", p)
                self.assertIn("chữ ký gắn ứng viên khác", p["reasons"][0])
                if xt._signoff_excluded(rel):
                    self.assertEqual(xt.evidence_fingerprint(self.repo), before)  # luật cũ: loại theo tên
        self.go_no_go()
        for rel in (
            "docs/ops/GO-NO-GO-x.md",
            "docs/GO-NO-GO-w.md",
            "GO-NO-GO-z.md",
            "docs/autopilot/DECISIONS.md",
            "PROGRESS.md",
            ".autopilot/note.txt",
        ):
            with self.subTest(rel=rel):
                f = self.repo / rel
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text(f"ghi {rel}\n", encoding="utf-8")
                self.git("add", "-f", rel)
                self.commit()
                _, _, p = self.promotion()
                self.assertEqual(p["state"], "approved", p)
        before = xt.subject_fingerprint(self.repo)
        (self.repo / "src" / "DECISIONS.md").write_text("đổi chưa commit\n", encoding="utf-8")
        self.assertNotEqual(xt.subject_fingerprint(self.repo), before)  # diff chưa commit cũng tính

    def test_subject_fingerprint_without_git(self):
        self.assertIsNone(xt.subject_fingerprint(self.tmp))

    def test_subject_line_hidden_in_markdown_not_accepted(self):
        """AUD-HAR-320: dòng `subject:` trong khối rào ``` / ~~~ hay chú thích HTML (kể cả nhiều dòng, chưa đóng) người
        ký không thấy khi xem — không nhận; sau khi rào/chú thích đóng thì nhận lại."""
        self.setup_xt()
        fp = xt.subject_fingerprint(self.repo)
        line = f"subject: content {fp}"
        for hidden in (
            f"```\n{line}\n```",
            f"```markdown\n{line}\n```",
            f"~~~\n{line}\n~~~",
            f"> ```\n> {line}\n> ```",
            f"````\n```\n{line}\n````",  # rào ngắn hơn không đóng rào dài
            f"```\n~~~\n{line}\n~~~\n```",  # rào khác ký tự không đóng
            f"```\n``` x\n{line}\n```",  # rào đóng không có chữ sau
            f"<!-- {line} -->",
            f"<!--\n{line}\n-->",
        ):
            with self.subTest(hidden=hidden):
                self.go_no_go(extra=hidden, content=False)
                _, _, p = self.promotion()
                self.assertEqual(p["state"], "pending_human", p)
                self.assertIn("thiếu dòng `subject: content", p["reasons"][0])
        for hidden in (f"```\n{line}", f"<!--\n{line}"):  # chưa đóng: ẩn tới hết file, cả §5 (AUD-HAR-323)
            with self.subTest(hidden=hidden):
                self.go_no_go(extra=hidden, content=False)
                _, _, p = self.promotion()
                self.assertEqual((p["state"], p["reasons"]), ("pending_human", ["go_no_go"]), p)
        for shown in (f"```\nx\n```\n{line}", f"~~~~\n```\n~~~~~\n{line}", f"<!-- ghi chú -->\n{line}"):
            with self.subTest(shown=shown):
                self.go_no_go(extra=shown, content=False)
                self.assertEqual(self.promotion()[2]["state"], "approved")

    def test_subject_line_bom_and_mismatch_message(self):
        """AUD-HAR-320: BOM đầu file không che dòng `subject:` ở dòng 1; dòng lệch in nguyên văn (repr, cắt khi dài) —
        hex kèm dấu câu không hiện ra như hai chuỗi giống nhau."""
        fp = hashlib.sha256(b"x").hexdigest()
        subject = {"content": fp, "digest": None}
        self.assertEqual(xt._subject_problem("G.md", f"\ufeffsubject: content {fp}\n# T\n", subject), "")
        why = xt._subject_problem("G.md", f"- subject: content `{fp}`.\n", subject)
        self.assertIn(repr(f"- subject: content `{fp}`."), why)
        self.assertIn(f"ứng viên này: `subject: content {fp}`", why)
        long = f"subject: content {fp}{'0' * 200}"
        why = xt._subject_problem("G.md", long, subject)
        self.assertIn(repr(long)[:100], why)
        self.assertNotIn(repr(long), why)
        self.assertIn("…", why)

    def test_subject_digest_line_with_artifacts(self):
        """Khai `release_artifacts` → thêm dòng `subject: digest <64 hex>`: thiếu, 12 hex, lệch → chờ người; đủ → duyệt."""
        (self.repo / "dist").mkdir()
        (self.repo / "dist" / "a.tar.gz").write_bytes(b"x")
        self.setup_xt(release_artifacts="dist/a.tar.gz")
        self.go_no_go()
        _, d, p = self.promotion()
        digest = d["subject"]["digest"]
        self.assertRegex(digest, r"^[0-9a-f]{64}$")
        self.assertEqual(p["state"], "pending_human")
        self.assertIn(f"thiếu dòng `subject: digest {digest}`", p["reasons"][0])
        for extra in (f"Subject: `{digest[:12]}`", f"subject: digest {digest[:12]}", f"subject: digest {digest[::-1]}"):
            with self.subTest(extra=extra):
                self.go_no_go(extra=extra)
                _, _, p = self.promotion()
                self.assertEqual(p["state"], "pending_human")
        self.go_no_go(extra=f"- subject: digest `{digest}`")
        self.assertEqual(self.promotion()[2]["state"], "approved")
        self.go_no_go(extra=f"subject: digest {digest}", content=False)  # digest đúng không thay dòng content
        _, _, p = self.promotion()
        self.assertEqual(p["state"], "pending_human")
        self.assertIn("thiếu dòng `subject: content", p["reasons"][0])
        _, out, _ = run_main("release-check")
        self.assertIn(f"\nsubject: content {d['subject']['content']}\n", out)
        self.assertIn(f"\nsubject: digest {digest}\n", out)

    def test_text_output_prints_subject_lines(self):
        self.setup_xt()
        _, d, _ = self.promotion()
        _, out, _ = run_main("release-check")
        self.assertIn(f"\nsubject: content {d['subject']['content']}\n", out)
        self.assertNotIn("subject: digest", out)
        self.assertNotIn("commit rồi chạy lại", out)

    def test_text_output_dirty_tree_withholds_subject_lines(self):
        """AUD-HAR-318: cây bẩn (hàng `tree` FAIL) — vân tay gồm diff chưa commit, lệch sau commit: không in dòng
        `subject:` để chép, in nhắc commit rồi chạy lại; JSON vẫn có `subject.content` (máy đọc, không phải để chép)."""
        self.setup_xt()
        (self.repo / "VERSION").write_text("1.2.1\n", encoding="utf-8")
        rc, out, _ = run_main("release-check")
        self.assertEqual(rc, 1)
        self.assertNotIn("subject: content", out)
        self.assertNotIn("chép nguyên", out)
        self.assertIn("cây chưa sạch", out)
        self.assertIn("commit rồi chạy lại", out)
        _, d = self.release()
        self.assertRegex(d["subject"]["content"], r"^[0-9a-f]{64}$")

    def test_text_output_tree_dirty_only_by_signoff_file(self):
        """AUD-HAR-322: cây bẩn chỉ vì GO-NO-GO vừa ghi (file ngoài vân tay) — thông điệp không khẳng định vân tay gồm
        diff chưa commit; chỉ nói cây chưa sạch, commit rồi chạy lại."""
        self.setup_xt()
        before = xt.subject_fingerprint(self.repo)
        (self.repo / "docs" / "ops" / "GO-NO-GO-v1.2.0.md").write_text("# GO/NO-GO v1.2.0\n", encoding="utf-8")
        self.assertEqual(xt.subject_fingerprint(self.repo), before)
        rc, out, _ = run_main("release-check")
        self.assertEqual(rc, 1)
        self.assertNotIn("subject: content", out)
        self.assertNotIn("vân tay gồm diff", out)
        self.assertIn("cây chưa sạch — commit rồi chạy lại", out)

    def sign_doc(self, sign: str) -> str:
        """Ghi và commit GO-NO-GO v1.2.0: dòng `subject:` đúng rồi `sign` (§5); trả nội dung file."""
        fp = xt.subject_fingerprint(self.repo)
        text = f"# GO/NO-GO v1.2.0\n\nsubject: content {fp}\n\n{sign}"
        (self.repo / "docs" / "ops" / "GO-NO-GO-v1.2.0.md").write_text(text, encoding="utf-8")
        self.commit()
        return text

    def test_sign_row_hidden_in_markdown_not_counted(self):
        """AUD-HAR-323: dòng ký §5 trong khối rào ```/~~~ hay chú thích HTML người xem không thấy — không phải chữ ký
        (`go_no_go` N/A BLOCKER, promotion chờ người); `## ` trong khối code không cắt §5. Guard `GO_SIGN` giữ luật riêng."""
        self.setup_xt()
        row = f"| Chủ repo | An | GO | {today()} |\n"
        for hidden in (
            f"{self.SIGN}```\n{row}```\n",
            f"{self.SIGN}~~~markdown\n{row}~~~\n",
            f"{self.SIGN}<!--\n{row}-->\n",
            f"{self.SIGN}```\n{row}",  # rào chưa đóng
            f"```\n{self.SIGN}{row}```\n\n## 5. Ký\n\nchưa ký\n",  # §5 giả trong khối code, §5 thật trống
        ):
            with self.subTest(hidden=hidden):
                text = self.sign_doc(hidden)
                self.assertFalse(xt._go_no_go_signed(text))
                rc, d, p = self.promotion()
                self.assertEqual((rc, self.by_id(d)["go_no_go"]["result"], p["state"]), (0, "N/A", "pending_human"))
                self.assertEqual(p["reasons"], ["go_no_go"])
        for shown in (
            f"{self.SIGN}{row}",
            f"{self.SIGN}```\nx\n```\n{row}",
            f"{self.SIGN}<!-- ghi chú -->\n{row}",
            f"## 5. Ký\n\n```\n## 6. không phải tiêu đề\n```\n\n| Vai trò | Tên | Quyết định | Ngày |\n|---|---|---|---|\n{row}",
        ):
            with self.subTest(shown=shown):
                text = self.sign_doc(shown)
                self.assertEqual(xt._go_sign_rows(text), [("GO", today())])
                rc, d, p = self.promotion()
                self.assertEqual((rc, self.by_id(d)["go_no_go"]["result"], p["state"]), (0, "PASS", "approved"), p)
        for hidden in (
            f"<style>\n{row}</style>\n",
            f"<script>\n{row}</script>\n",
            f"<?\n{row}?>\n",
            f"<![CDATA[\n{row}]]>\n",
            f"<!X\n{row}>\n",
        ):
            with self.subTest(raw_html=hidden):  # review #467 🟠2: raw HTML người không thấy
                self.sign_doc(f"{self.SIGN}{hidden}")
                _, d, p = self.promotion()
                self.assertEqual((self.by_id(d)["go_no_go"]["result"], p["state"]), ("N/A", "pending_human"))

    def test_no_go_row_read_from_raw_section(self):
        """Review #467 🔴1: dòng NO-GO lấy từ §5 THÔ (mọi mục `## 5`) cộng phần hiển thị — bộ lọc Markdown lệch với
        trình xem (ẩn thừa) không được làm mất lời từ chối; GO vẫn chỉ tính phần người thấy."""
        self.setup_xt()
        go = f"| Chủ repo | An | GO | {today()} |\n"
        nogo = f"| Bảo mật | Chi | NO-GO | {today()} |\n"
        for sign in (
            f"{self.SIGN}{go}<!-->\n{nogo}",  # `<!-->`, `<!--->`: chú thích trọn (CommonMark 0.31.2 §4.6)
            f"{self.SIGN}{go}<!--->\n{nogo}",
            f"{self.SIGN}{go}Ghi chú: `<!--` mở chú thích.\n\n{nogo}",  # `<!--` trong code span
            f"{self.SIGN}```\n{nogo}```\n{go}",  # NO-GO trong khối code
            f"{self.SIGN}<!--\n{nogo}-->\n",  # chỉ có NO-GO, bị ẩn: file vẫn được xét
            f"{self.SIGN}{go}```\n## 6. giả\n```\n{nogo}",  # NO-GO hiện, thô nằm sau `## 6` giả
            f"```\n## 5. Ký\n{nogo}```\n\n{self.SIGN}{go}",  # NO-GO ở §5 thô thứ nhất
        ):
            with self.subTest(sign=sign):
                self.sign_doc(sign)
                rc, d, p = self.promotion()
                self.assertEqual((rc, p["state"]), (0, "rejected"), p)
                self.assertIn("NO-GO", p["reasons"][0])
        self.sign_doc(f"{self.SIGN}{go}| Bảo mật | Chi | NO-GO | |\n")  # không ngày: không phải dòng ký
        self.assertEqual(self.promotion()[2]["state"], "approved")

    def test_no_content_fingerprint_never_approved(self):
        """Không tính được vân tay nội dung (không phải repo git/chưa commit) → không gắn được ứng viên, không duyệt."""
        text = f"# GO/NO-GO v1.2.0\n\n{self.SIGN}| Chủ repo | An | GO | {today()} |\n"
        why = xt._approval_problem(self.repo, "G.md", text, {"content": None, "digest": None})
        self.assertIn("không tính được vân tay nội dung", why)
        self.assertEqual(xt.subject_lines({"content": None, "digest": None}), [])

    def test_blocked_and_no_version(self):
        self.setup_xt(acceptance="false")
        rc, d, p = self.promotion()
        self.assertEqual((rc, p["state"], p["reasons"]), (1, "blocked", ["acceptance"]))
        (self.repo / "VERSION").unlink()
        self.setup_xt()
        rc, d, p = self.promotion()
        self.assertEqual((rc, d["verdict"], p["state"]), (0, "GO", "pending_human"))
        self.assertIn("chưa có GO-NO-GO đã ký", p["reasons"][0])


class SubjectExcludeWorkTreeTest(TmpDirCase):
    """AUD-TEST-091: nửa pathspec `SUBJECT_EXCLUDE` của `subject_fingerprint` (diff so HEAD + file chưa track) — file
    loại trừ sửa chưa commit hay chưa track → vân tay không đổi; file cùng tên ở chỗ khác → đổi. Dự án ở gốc repo và ở
    thư mục con (pathspec tính từ dự án). Mutant `SUBJECT_EXCLUDE = []` làm ca loại trừ đỏ."""

    EXCLUDED = ("docs/ops/GO-NO-GO-v1.md", "docs/GO-NO-GO.md", "GO-NO-GO-x.md", xt.DECISIONS_LOG, "PROGRESS.md")
    COUNTED = (
        "src/DECISIONS.md",
        "docs/PROGRESS.md",
        "docs/ops/old/GO-NO-GO-a.md",
        "docs/autopilot/DECISIONS-2026-11.md",
        "docs/ops/GO-NO-GO-x.txt",
        "src/a.py",
    )

    def project(self, name: str, sub: str, files: tuple) -> Path:
        """Repo mới `name`, dự án ở `sub` (rỗng = gốc), commit `seed.txt` và `files` (nội dung `v0`)."""
        root = self.tmp / name
        root.mkdir()
        base = root / sub if sub else root
        for rel in ("seed.txt", *files):
            f = base / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text("v0\n", encoding="utf-8")
        for args in (("init", "-q", "-b", "main"), ("add", "-A"), ("commit", "-q", "-m", "c")):
            xt._git(root, "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args).check_returncode()
        return base

    def assert_effect(self, base: Path, rel: str, write: str, restore: str) -> None:
        """Ghi `write` vào `rel` (chưa commit): loại trừ → vân tay giữ nguyên, còn lại → đổi; trả lại trạng thái cũ."""
        before = xt.subject_fingerprint(base)
        self.assertRegex(before, r"^[0-9a-f]{64}$")
        f = base / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(write, encoding="utf-8")
        after = xt.subject_fingerprint(base)
        if rel in self.EXCLUDED:
            self.assertEqual(after, before, rel)
        else:
            self.assertNotEqual(after, before, rel)
        if restore:
            f.write_text(restore, encoding="utf-8")
        else:
            f.unlink()
        self.assertEqual(xt.subject_fingerprint(base), before, rel)

    def test_uncommitted_and_untracked(self):
        for sub in ("", "apps/web"):
            tracked = self.project(f"tracked{len(sub)}", sub, (*self.EXCLUDED, *self.COUNTED))
            untracked = self.project(f"untracked{len(sub)}", sub, ())
            for rel in (*self.EXCLUDED, *self.COUNTED):
                with self.subTest(sub=sub, rel=rel, kind="diff"):
                    self.assert_effect(tracked, rel, "v1 chưa commit\n", "v0\n")
                with self.subTest(sub=sub, rel=rel, kind="untracked"):
                    self.assert_effect(untracked, rel, "mới, chưa track\n", "")


class MarkdownShownTest(unittest.TestCase):
    """AUD-HAR-322: `_markdown_shown` — rào trong mục danh sách, khối code thụt 4 cách, chú thích HTML và rào không nuốt
    nhau; khối chứa (danh sách, trích dẫn) đóng thì rào đóng theo."""

    LINE = "subject: content " + "a" * 64

    def assert_hidden(self, text: str) -> None:
        self.assertNotIn(self.LINE, xt._markdown_shown(text), text)

    def assert_shown(self, text: str) -> None:
        self.assertIn(self.LINE, xt._markdown_shown(text), text)

    def test_list_item_fences(self):
        s = self.LINE
        for text in (
            f"- ```\n  {s}\n  ```",
            f"1. ```\n   {s}\n   ```",
            f"* ~~~ markdown\n  {s}\n  ~~~",
            f"> - ```\n>   {s}\n>   ```",
            f"- ```\n  x\n- ~~~\n  y\n  ~~~\n```\n{s}\n```",  # mục mới đóng rào mục cũ, mở rào mới
            f"- ```\n  x\n- ```\n  {s}\n  ```",
        ):
            with self.subTest(text=text):
                self.assert_hidden(text)
        for text in (
            f"- ```\n  x\n  ```\n{s}",
            f"- ```\n  x\n{s}",  # dòng thụt ít hơn mục: mục (và rào) đã đóng
            f"- ``` a`b\n{s}",  # backtick trong chuỗi info của rào backtick: không phải rào
        ):
            with self.subTest(text=text):
                self.assert_shown(text)

    def test_container_end_closes_fence(self):
        """Trích dẫn đóng (dòng không `>`) thì rào trong nó đóng theo: dòng rào kế tiếp là rào MỞ, không phải rào đóng."""
        s = self.LINE
        self.assert_hidden(f"> ```\n```\n{s}\n```")
        self.assert_shown(f"> ```\n> x\n{s}")
        self.assert_hidden(f"```\n> ```\n{s}\n```")  # `> ```` trong rào gốc là nội dung, không đóng
        self.assert_hidden(f"```\n    ```\n{s}\n```")  # thụt ≥ 4 so với rào: nội dung, không đóng

    def test_indented_code(self):
        s = self.LINE
        for text in (
            f"    {s}",
            f"para\n\n    {s}",
            f"## 5. Ký\n    {s}",
            f"<!-- x -->\n    {s}",
            f"```\nx\n```\n    {s}",
            f"\t{s}",
            f"\n    x\n\n    {s}",
            f"---\n    {s}",  # review #467: sau đường kẻ, gạch setext, bảng, định nghĩa link, HTML, tiêu đề trong trích dẫn
            f"* * *\n    {s}",
            f"para\n===\n    {s}",
            f"| a | b |\n|---|---|\n| 1 | 2 |\n    {s}",
            f"[a]: /u\n    {s}",
            f"<pre>\n</pre>\n    {s}",
            f"para\n<style>x</style>\n    {s}",  # sau khối HTML ẩn
            f"para\n```\nx\n```\n    {s}",  # sau rào đóng
            f"> ## H\n    {s}",
            f"    ```\n```\n{s}\n```",  # rào trong khối thụt là nội dung — dòng sau là rào mở
        ):
            with self.subTest(text=text):
                self.assert_hidden(text)
        for text in (f"para\n    {s}", f"- mục\n    {s}", f"para <!-- c -->\n    {s}"):
            with self.subTest(text=text):
                self.assert_shown(text)

    def test_comment_and_fence_do_not_swallow_each_other(self):
        s = self.LINE
        for text in (
            f"```html\n<!-- a\n```\n{s}",
            f"<!--\n```\n-->\n{s}",
            f"~~~\n<!--\n~~~\n<!-- b -->\n{s}",
            f"<!-- a --> {s}",
        ):
            with self.subTest(text=text):
                self.assert_shown(text)
        for text in (
            f"<!--\n```\n-->\n```\n-->\n{s}\n```",  # rào thật sau chú thích: tách rào trước sẽ lộ dòng này
            f"<!--\n```\n{s}\n```\n-->",
            f"x <!-- a\n{s}\n-->",
            f"<!-- a -->\n<!--\n{s}",
        ):
            with self.subTest(text=text):
                self.assert_hidden(text)

    def test_shown_text_keeps_original_line(self):
        self.assertEqual(xt._markdown_shown("﻿a\t<!-- x -->b\r\n```\nc\n```\r\nd"), "a\tb\r\nd")
        self.assertEqual(xt._markdown_shown("    \nx <!-- a --> y <!-- b --> z"), "    \nx  y  z")

    def test_reviewer_mutants(self):
        """Review #467: mutant sống M2/M18/M20/M29."""
        s = self.LINE
        self.assert_shown(f"``` a`b\n{s}")  # M2: info có backtick — không phải rào
        self.assert_hidden(f"  ```\n{s}\n  ```")  # M18: rào thụt không dấu mục — dòng thụt ít hơn vẫn trong rào
        self.assert_shown(f"   {s}")  # M20: 3 cách là đoạn văn
        self.assert_shown(f"> ```\n> x\n> ```\n> {s}")  # M29: rào đóng xét sau tiền tố `>`

    def test_comment_edges(self):
        """Review #467 🔴1(b)(c): `<!-->`/`<!--->` đóng cùng dòng; `<!--` trong code span một dòng không mở chú thích."""
        s = self.LINE
        for text in (
            f"<!-->\n{s}",
            f"<!--->\n{s}",
            f"<!-- a --->{s}",
            f"<!-- a <!-->{s}",  # `-->` của `<!-->` đóng chú thích đang mở
            f"a --> {s}",  # `-->` không có chú thích mở: chữ thường
            f"`<!--` {s}",
            f"``a ` <!-- b`` {s}",
            f"`x` <!-- a --> `<!--` {s}",
        ):
            with self.subTest(text=text):
                self.assert_shown(text)
        for text in (f"` <!-- {s}", f"`` <!-- ` {s}", f"x `a` <!--\n{s}", f"`<!--\n{s}`"):
            with self.subTest(text=text):
                self.assert_hidden(text)

    def test_raw_html_blocks(self):
        """Review #467 🟠2: khối HTML trình xem không hiện (CommonMark loại 1 script/style, 3 `<?`, 4 `<!X`, 5 CDATA) bị
        ẩn tới dòng có đuôi đóng; `<pre>`/`<textarea>` vẫn hiện; dòng sau khối đóng hiện lại."""
        s = self.LINE
        for text in (
            f"<style>\n{s}\n</style>",
            f"<SCRIPT type=x>\n{s}\n</Script>",
            f"<script>\n{s}",
            f"<?\n{s}\n?>",
            f"<![CDATA[\n{s}\n]]>",
            f"<!X\n{s}\n>",
            f"   <style>\n{s}",
            f"> <style>\n> {s}\n> </style>",
            f"para\n<style>\n{s}\n</style>",
            f"<style>x</style> {s}",
        ):
            with self.subTest(text=text):
                self.assert_hidden(text)
        for text in (
            f"<pre>\n{s}\n</pre>",
            f"<textarea>\n{s}\n</textarea>",
            f"<style>\nx\n</style>\n{s}",
            f"<style>x</style>\n{s}",
            f"<!DOCTYPE html>\n{s}",
            f"<styles>\n{s}",
            f"<scriptx\n{s}",
            f"<!-- a -->\n{s}",
            f"```\n<style>\n```\n{s}",
            f"<!--\n<style>\n-->\n{s}",
        ):
            with self.subTest(text=text):
                self.assert_shown(text)

    def test_comment_scan_linear(self):
        """Review #467 🟠1: dòng 200k chú thích / code span — duyệt một lượt, không cắt chuỗi mỗi lần (bậc hai)."""
        for text in ("<!-- -->" * 200_000 + "x", "`a` " * 200_000 + "x", "<!-- a -->`b`" * 100_000 + "`" + "x"):
            start = time.perf_counter()
            self.assertTrue(xt._markdown_shown(text).endswith("x"))
            self.assertLess(time.perf_counter() - start, 1.0)


class FenceRegexIsolationTest(unittest.TestCase):
    """Review #466 🔴: rào của bộ lọc dòng `subject:` không được đè `FENCE_RE` của PROGRESS/PLAN/bảng audit."""

    def test_progress_and_plan_fences_unchanged(self):
        for text in ("## A\n```\nx\n````\n## B\n", "## A\n> ```\n## B\n"):
            with self.subTest(text=text):
                self.assertEqual([n for n, _ in xt.progress_sections(text)], ["A", "B"])
        self.assertIsNot(xt.FENCE_RE, xt.SHOWN_FENCE_RE)
        self.assertEqual(xt.FENCE_RE.pattern, r"^\s*(```|~~~)")


if __name__ == "__main__":
    unittest.main()
