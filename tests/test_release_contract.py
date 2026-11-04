"""ADR-0068 lát A (D-350, PLAN-factory-A): hợp đồng kết quả/phát hành có kiểu — adapter đọc report (JUnit XML, SARIF,
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
    """T-3673: `report_result` nhận dạng theo nội dung; kết quả có kiểu PASS/FAIL/PENDING/INCONCLUSIVE kèm số đếm."""

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
        r = self.result({"dependencies": [{"name": "a", "vulns": [{"id": "PYSEC-1"}, {"id": "GHSA-x"}]}]})
        self.assertEqual((r["status"], r["failed"]), ("FAIL", 2))
        r = self.result({"dependencies": [{"name": "b", "skip_reason": "x"}]})
        self.assertEqual((r["status"], r["total"]), ("PENDING", 0))
        self.assertIn("0 gói được quét", r["detail"])

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
    """T-3674: `<key>_report` — exit 0 chưa đủ: report phải có, do lần chạy này sinh, kết quả PASS."""

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
    """T-3675: `release_artifacts` → hàng `artifacts` (chỉ khi khai) và `subject.digest`."""

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


class PromotionTest(ReleaseCase):
    """T-3676: `promotion` — chỉ `approved` khi không FAIL, không N/A BLOCKER, GO-NO-GO của VERSION ký GO còn hạn và nhắc
    digest (khi có artifact); máy không nâng `pending_human`. `go`/`verdict`/exit giữ nghĩa cũ."""

    SIGN = "## 5. Ký\n\n| Vai trò | Tên | Quyết định | Ngày |\n|---|---|---|---|\n"

    def setUp(self):
        super().setUp()
        (self.repo / "VERSION").write_text("1.2.0\n", encoding="utf-8")

    def go_no_go(self, decision: str = "GO", date: str = "", extra: str = "") -> None:
        doc = self.repo / "docs" / "ops" / "GO-NO-GO-v1.2.0.md"
        doc.write_text(
            f"# GO/NO-GO v1.2.0\n\n{extra}\n{self.SIGN}| Chủ repo | An | {decision} | {date or today()} |\n", "utf-8"
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

    def test_rejected(self):
        self.setup_xt()
        for decision in ("NO-GO", "GO / NO-GO"):  # ô mẫu chưa chọn = không phải GO
            with self.subTest(decision=decision):
                self.go_no_go(decision)
                rc, d, p = self.promotion()
                self.assertEqual((rc, p["state"]), (0, "rejected"))
                self.assertIn("NO-GO", p["reasons"][0])

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
        self.assertEqual(self.promotion()[2]["state"], "approved")
        for bad in ("0", "x"):  # sai → mặc định 30 ngày
            with self.subTest(bad=bad):
                self.setup_xt(release_approval_days=bad)
                self.assertEqual(self.promotion()[2]["state"], "pending_human")
        self.setup_xt()
        self.go_no_go(date=today(3))
        _, _, p = self.promotion()
        self.assertEqual(p["state"], "pending_human")
        self.assertIn("tương lai", p["reasons"][0])

    def test_subject_digest_must_be_named(self):
        (self.repo / "dist").mkdir()
        (self.repo / "dist" / "a.tar.gz").write_bytes(b"x")
        self.setup_xt(release_artifacts="dist/a.tar.gz")
        self.go_no_go()
        _, d, p = self.promotion()
        self.assertEqual(p["state"], "pending_human")
        self.assertIn("không nhắc digest", p["reasons"][0])
        self.go_no_go(extra=f"Subject: `{d['subject']['digest'][:12]}`")
        self.assertEqual(self.promotion()[2]["state"], "approved")

    def test_blocked_and_no_version(self):
        self.setup_xt(acceptance="false")
        rc, d, p = self.promotion()
        self.assertEqual((rc, p["state"], p["reasons"]), (1, "blocked", ["acceptance"]))
        (self.repo / "VERSION").unlink()
        self.setup_xt()
        rc, d, p = self.promotion()
        self.assertEqual((rc, d["verdict"], p["state"]), (0, "GO", "pending_human"))
        self.assertIn("chưa có GO-NO-GO đã ký", p["reasons"][0])


if __name__ == "__main__":
    unittest.main()
