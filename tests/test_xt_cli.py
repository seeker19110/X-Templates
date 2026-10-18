"""Test cho nửa sau scripts/xt.py: progress-check, ci-check, audit plan/check, các lệnh cmd_*, parser, main.

Gọi hàm/`main([...])` trong tiến trình (không subprocess) trừ khi cần git thật (repo tạm).
"""

from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
import warnings
import unittest.mock
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import xt
from test_xt import audit_status_text, make_framework


def run_main(*args, stdin: str | None = None) -> tuple[int, str, str]:
    """Chạy xt.main trong tiến trình; trả (exit code, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        if stdin is None:
            rc = xt.main([str(a) for a in args])
        else:
            with unittest.mock.patch.object(sys, "stdin", io.StringIO(stdin)):
                rc = xt.main([str(a) for a in args])
    return rc, out.getvalue(), err.getvalue()


class TmpDirCase(unittest.TestCase):
    """Thư mục tạm, chặn git đi ngược lên thư mục cha (tránh nhặt nhầm repo ngoài)."""

    def setUp(self):
        self.tmp = Path(self.enterContext(tempfile.TemporaryDirectory())).resolve()
        self.enterContext(unittest.mock.patch.dict(os.environ, {"GIT_CEILING_DIRECTORIES": str(self.tmp.parent)}))


class TmpRepoCase(TmpDirCase):
    def init_repo(self) -> Path:
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        self.git("init", "-q", "-b", "main")
        return self.repo

    def git(self, *args, env=None) -> str:
        r = subprocess.run(
            ["git", "-C", str(self.repo), "-c", "user.name=t", "-c", "user.email=t@example.invalid"]
            + ["-c", "commit.gpgsign=false", *args],
            capture_output=True,
            text=True,
            check=True,
            env={**os.environ, **(env or {})},
        )
        return r.stdout.strip()

    def commit_files(self, files: dict, at: int) -> str:
        for name, text in files.items():
            f = self.repo / name
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(text, encoding="utf-8")
            self.git("add", name)
        stamp = f"@{at} +0000"
        self.git("commit", "-q", "-m", "c", env={"GIT_AUTHOR_DATE": stamp, "GIT_COMMITTER_DATE": stamp})
        return self.git("rev-parse", "HEAD")


# --------------------------------------------------------------------------- progress-check


class ProgressCheckEdgeTest(TmpDirCase):
    def test_missing_handover_section_returns_early(self):
        f = self.tmp / "PROGRESS.md"
        f.write_text("## Đang làm\n\nx\n\n## Tiếp theo\n\ny\n", encoding="utf-8")
        errors = xt.progress_check(f)
        self.assertEqual(len(errors), 1)
        self.assertIn("đang có: Đang làm · Tiếp theo", errors[0])

    def test_no_sections_at_all_reports_placeholder(self):
        f = self.tmp / "PROGRESS.md"
        f.write_text("chỉ có chữ\n", encoding="utf-8")
        errors = xt.progress_check(f)
        self.assertIn("đang có: (không có)", errors[0])

    def test_sha_outside_git_repo_raises_oserror(self):
        f = self.tmp / "PROGRESS.md"
        f.write_text(
            "## Đang làm\n\n## Tiếp theo\n\n## Quyết định\n\n## Bàn giao phiên\n\ncommit `abcdef1`\n", encoding="utf-8"
        )
        with self.assertRaises(OSError) as cm:
            xt.progress_check(f)
        self.assertIn("không phải repo git", str(cm.exception))
        rc, out, err = run_main("progress-check", f)
        self.assertEqual((rc, out), (2, ""))
        self.assertIn("✗ không phải repo git", err)


# --------------------------------------------------------------------------- ci-check


class CiCheckEdgeTest(unittest.TestCase):
    def test_workflow_without_jobs_key(self):
        self.assertEqual(xt.ci_check_text("permissions: read-all\non:\n  push:\n"), [])

    def test_jobs_key_without_body(self):
        self.assertEqual(xt.ci_check_text("permissions: read-all\njobs:\n"), [])

    def test_job_missing_timeout_still_reported_with_deeper_lines(self):
        text = "permissions: read-all\njobs:\n  a:\n    runs-on: x\n    steps:\n      - run: y\n"
        errors = xt.ci_check_text(text)
        self.assertEqual(len(errors), 1)
        self.assertIn("job `a` thiếu `timeout-minutes`", errors[0])

    def test_errors_ordered_permissions_then_lines_then_jobs(self):
        text = (
            "name: x\njobs:\n  a:\n    runs-on: u\n    steps:\n      - uses: a/b@v1\n"
            "      - {uses: a/c@v1, continue-on-error: true, permissions: write-all}\n"
            "      - continue-on-error: true\n  b:\n    timeout-minutes: 3\n"
        )
        coe = "`continue-on-error` trên job/bước — ngoại lệ ghi `# ci-check-allow: <lý do + hạn>`"
        self.assertEqual(
            xt.ci_check_text(text),
            [
                "thiếu `permissions:` cấp workflow (mặc định `contents: read`)",
                "dòng 6: `a/b@v1` chưa ghim SHA 40 ký tự",
                "dòng 7: `write-all` — khai quyền tối thiểu theo job",
                f"dòng 7: {coe}",
                "dòng 7: `a/c@v1` chưa ghim SHA 40 ký tự",
                f"dòng 8: {coe}",
                "dòng 3: job `a` thiếu `timeout-minutes`",
            ],
        )


# --------------------------------------------------------------------------- markdown helpers


class MarkdownTableTest(unittest.TestCase):
    def test_split_row_without_outer_pipes(self):
        self.assertEqual(xt.split_md_row("a | b"), ["a", "b"])

    def test_split_row_with_outer_pipes_and_escaped_pipe(self):
        self.assertEqual(xt.split_md_row("| a \\| b | c |"), ["a | b", "c"])

    def test_split_row_trailing_escaped_pipe_is_content(self):
        self.assertEqual(xt.split_md_row("| a \\|"), ["a |"])

    def test_md_tables_ignores_fenced_rows(self):
        text = (
            "## Nhóm\n\n```\n| x | y |\n~~~\n| z |\n```\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\n~~~\n## Giả\n| q |\n~~~\n"
        )
        tables = xt.md_tables(text)
        self.assertEqual(list(tables), ["Nhóm"])
        self.assertEqual(tables["Nhóm"], [{"a": "1", "b": "2"}])

    def test_md_tables_only_first_table_per_heading(self):
        text = "## T\n\n| a |\n|---|\n| 1 |\n\ntext\n\n| b |\n|---|\n| 2 |\n"
        self.assertEqual(xt.md_tables(text), {"T": [{"a": "1"}]})

    def test_md_tables_pads_short_rows(self):
        self.assertEqual(xt.md_tables("## T\n| a | b |\n|---|---|\n| 1 |\n"), {"T": [{"a": "1", "b": ""}]})


# --------------------------------------------------------------------------- audit helpers


class RepoFilesTest(TmpDirCase):
    def test_walk_fallback_outside_git_skips_vendor_dirs(self):
        for rel in ("a.py", "sub/b.md", "node_modules/x.js", ".autopilot/s.json", "dist/o.js"):
            p = self.tmp / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("x", encoding="utf-8")
        self.assertEqual(sorted(xt._repo_files(self.tmp)), ["a.py", "sub/b.md"])

    def test_empty_directory(self):
        self.assertEqual(xt._repo_files(self.tmp), [])


class AuditToolsTest(TmpDirCase):
    def test_group_without_relevant_stack_tool_is_omitted(self):
        sig = xt.audit_signals(self.tmp, ["lib.rs"])
        appl = xt.audit_applicability(sig)
        tools = xt.audit_tools(self.tmp, sig, appl)
        self.assertNotIn(1, tools)  # lint-imports/depcruise/go: không cái nào hợp rust
        self.assertIn(3, tools)  # jscpd áp dụng mọi stack
        self.assertIn("jscpd", tools[3]["có"] + tools[3]["thiếu"])
        self.assertNotIn(6, tools)  # N/A (không UI) bị bỏ qua


class ToolPresentTest(TmpDirCase):
    """Tất định, không phụ thuộc PATH của máy chạy test."""

    def test_xt_builtin_is_always_present(self):
        with unittest.mock.patch.object(xt.shutil, "which", return_value=None):
            self.assertTrue(xt._tool_present(self.tmp, "xt:ci-check"))

    def test_tool_on_path(self):
        with unittest.mock.patch.object(xt.shutil, "which", return_value="/usr/bin/gitleaks") as which:
            self.assertTrue(xt._tool_present(self.tmp, "gitleaks"))
        which.assert_called_once_with("gitleaks")

    def test_tool_in_node_modules_bin(self):
        (self.tmp / "node_modules" / ".bin").mkdir(parents=True)
        (self.tmp / "node_modules" / ".bin" / "jscpd").write_text("", encoding="utf-8")
        with unittest.mock.patch.object(xt.shutil, "which", return_value=None):
            self.assertTrue(xt._tool_present(self.tmp, "jscpd"))
            self.assertFalse(xt._tool_present(self.tmp, "lychee"))

    def test_python_tool_falls_back_to_importable_module(self):
        with (
            unittest.mock.patch.object(xt.shutil, "which", return_value=None),
            unittest.mock.patch.object(xt.importlib.util, "find_spec", return_value=object()) as spec,
        ):
            self.assertTrue(xt._tool_present(self.tmp, "pip-audit"))
            self.assertFalse(xt._tool_present(self.tmp, "osv-scanner"))  # không phải gói Python: không dò module
        spec.assert_called_once_with("pip_audit")


class ResolveRefTest(unittest.TestCase):
    FILES = ["a/x.py", "b/x.py", "c/y.py"]

    def test_exact_match(self):
        self.assertEqual(xt._resolve_ref("a/x.py", self.FILES), "a/x.py")

    def test_unique_suffix_match(self):
        self.assertEqual(xt._resolve_ref("y.py", self.FILES), "c/y.py")

    def test_ambiguous_suffix_is_none(self):
        self.assertIsNone(xt._resolve_ref("x.py", self.FILES))

    def test_unknown_is_none(self):
        self.assertIsNone(xt._resolve_ref("z.py", self.FILES))


class PathGroupsTest(unittest.TestCase):
    def test_groups_by_path_kind(self):
        cases = {
            ".github/workflows/ci.yml": [2, 8],
            ".gitlab-ci.yml": [2, 8],
            "package.json": [2, 7],
            "requirements-dev.txt": [2, 7],
            "tests/test_x.py": [4],
            "web/app.spec.ts": [4],
            "db/migrations/001.sql": [10],
            "prisma/schema.prisma": [10],
            "AGENTS.md": [9, 13],
            ".claude/hooks/guard.py": [1, 2, 3, 12, 13],
            ".env.local": [8, 11],
            "Dockerfile": [8, 11],
            "src/app.tsx": [1, 2, 3, 5, 6, 12],
            "styles/site.css": [5, 6],
            "README.md": [9],
            "src/main.py": [1, 2, 3, 12],
            "notes.txt": [],
        }
        for path, expected in cases.items():
            with self.subTest(path=path):
                self.assertEqual(xt._path_groups(path), expected)


class AuditStatusGroupsTest(TmpDirCase):
    def test_rows_with_non_numeric_number_are_ignored(self):
        f = self.tmp / "S.md"
        f.write_text(
            "## Nhóm\n\n| # | Mã | Trạng thái |\n|---|---|---|\n| x | FOO | N/A |\n| 1 | ARCH | đã quét |\n",
            encoding="utf-8",
        )
        groups = xt.audit_status_groups(f)
        self.assertEqual(list(groups), [1])
        self.assertEqual(groups[1]["Trạng thái"], "đã quét")

    def test_missing_table_gives_empty(self):
        f = self.tmp / "S.md"
        f.write_text("# trống\n", encoding="utf-8")
        self.assertEqual(xt.audit_status_groups(f), {})


class AuditRescanTest(TmpRepoCase):
    def test_up_to_date_group_and_empty_sha(self):
        self.init_repo()
        c1 = self.commit_files({"main.py": "1"}, 1_700_000_000)
        status = self.tmp / "S.md"
        groups = {1: ("đã quét", c1, "2026-10-14", ""), 3: ("đã quét", "", "2026-10-14", "")}
        status.write_text(audit_status_text(groups), encoding="utf-8")
        rescan = xt.audit_rescan(self.repo, status)
        self.assertNotIn(1, rescan)  # không file nào đổi từ SHA quét
        self.assertIn("SHA `—` không còn là tổ tiên HEAD", rescan[3])
        self.assertEqual(set(rescan), {3})  # còn lại N/A


class ShaOkTest(TmpRepoCase):
    def test_sha_validation(self):
        self.init_repo()
        c1 = self.commit_files({"a": "1"}, 1_700_000_000)
        self.assertEqual(xt._sha_ok(self.repo, "not-a-sha"), "SHA không hợp lệ")
        self.assertEqual(xt._sha_ok(self.repo, "abc"), "SHA không hợp lệ")  # quá ngắn
        self.assertIn("không có trong lịch sử", xt._sha_ok(self.repo, "deadbeef"))
        self.assertIsNone(xt._sha_ok(self.repo, c1))
        self.git("checkout", "-q", "--orphan", "other")
        self.commit_files({"b": "1"}, 1_700_000_100)
        self.assertIn("không phải tổ tiên HEAD", xt._sha_ok(self.repo, c1))


class StaleEvidenceTest(TmpRepoCase):
    def test_unreadable_blueprint_gives_empty(self):
        self.init_repo()
        self.assertEqual(xt.blueprint_stale_evidence(self.repo, self.repo / "khong-co.md", []), [])

    def test_skips_and_caches(self):
        self.init_repo()
        bp = (
            "- [ ] `A-001` **MUST** chưa tick — Bằng chứng: lib/a.py\n"
            "- [x] `A-002` **MUST** không ghi chú\n"
            "- [x] `A-003` **MUST** file lạ → Kiểm: x — Bằng chứng: khong-co.py:3 ghi chú\n"
            "- [x] `A-004` **MUST** lib đổi → Kiểm: x — Bằng chứng: lib/a.py:1\n"
            "- [~] `A-005` **MUST** lib đổi nữa → Kiểm: x — Miễn: lib/a.py không dùng\n"
            "- [x] `A-006` **MUST** file không đổi → Kiểm: x — Bằng chứng: b.py\n"
        )
        self.commit_files({"lib/a.py": "1", "b.py": "1", "BLUEPRINT.md": bp}, 1_700_000_000)
        self.commit_files({"lib/a.py": "2"}, 1_700_000_100)
        # dòng chưa commit: blame trả hash toàn số 0 → bỏ qua
        with (self.repo / "BLUEPRINT.md").open("a", encoding="utf-8") as f:
            f.write("- [x] `A-007` **MUST** mới sửa → Kiểm: x — Bằng chứng: lib/a.py\n")
        files = xt._repo_files(self.repo)
        stale = xt.blueprint_stale_evidence(self.repo, self.repo / "BLUEPRINT.md", files)
        self.assertEqual(
            stale,
            [
                {"id": "A-004", "kind": "Bằng chứng", "files": ["lib/a.py"]},
                {"id": "A-005", "kind": "Miễn", "files": ["lib/a.py"]},
            ],
        )

    def test_audit_plan_checks_backlog_evidence_too(self):
        self.init_repo()
        main = "---\nkind: blueprint\nbacklog: BLUEPRINT-BACKLOG.md\n---\n- [x] `A-001` **MUST** a → Kiểm: x — Bằng chứng: b.py\n"
        bl = "- [x] `A-002` **SHOULD** s → Kiểm: x — Bằng chứng: lib/a.py\n"
        self.commit_files(
            {"lib/a.py": "1", "b.py": "1", "BLUEPRINT.md": main, "BLUEPRINT-BACKLOG.md": bl}, 1_700_000_000
        )
        self.commit_files({"lib/a.py": "2"}, 1_700_000_100)
        plan = xt.audit_plan(self.repo, self.repo / "BLUEPRINT.md")
        self.assertEqual(plan["stale_evidence"], [{"id": "A-002", "kind": "Bằng chứng", "files": ["lib/a.py"]}])

    def test_blueprint_not_tracked_is_skipped(self):
        self.init_repo()
        self.commit_files({"lib/a.py": "1"}, 1_700_000_000)
        bp = self.repo / "BLUEPRINT.md"  # chưa git add → blame lỗi
        bp.write_text("- [x] `A-001` **MUST** x → Kiểm: y — Bằng chứng: lib/a.py\n", encoding="utf-8")
        self.assertEqual(xt.blueprint_stale_evidence(self.repo, bp, xt._repo_files(self.repo)), [])


# --------------------------------------------------------------------------- audit check


class AuditCheckEdgeTest(TmpDirCase):
    def check(self, text: str, strict: bool = False) -> list[str]:
        f = self.tmp / "AUDIT-STATUS.md"
        f.write_text(text, encoding="utf-8")
        return xt.audit_check(f, strict=strict, today=xt._dt.date(2026, 10, 14))[0]

    def test_missing_both_tables(self):
        errors = self.check("# không có bảng\n")
        self.assertEqual(errors, ["thiếu bảng `## Nhóm`", "thiếu bảng `## Phát hiện`"])

    def test_invalid_group_state(self):
        errors = self.check(audit_status_text({1: ("bogus", "", "", "x")}))
        self.assertEqual(len(errors), 1)
        self.assertIn("nhóm 1: trạng thái `bogus` không thuộc", errors[0])

    def test_group_number_out_of_range(self):
        text = audit_status_text() + "\n"
        text = text.replace("| 13 | HAR |", "| 99 | HAR |")
        errors = self.check(text)
        self.assertIn("nhóm `99`: số nhóm phải 1–13", errors)
        self.assertIn("nhóm 13: phải có đúng 1 dòng (đang có 0)", errors)

    def test_unicode_digit_group_number_is_an_error_not_a_crash(self):
        # "²".isdigit() là True nhưng int("²") văng ValueError → audit check/plan từng in traceback.
        text = audit_status_text().replace("| 1 | ARCH |", "| ² | ARCH |")
        errors = self.check(text)
        self.assertIn("nhóm `²`: số nhóm phải 1–13", errors)
        self.assertIn("nhóm 1: phải có đúng 1 dòng (đang có 0)", errors)
        f = self.tmp / "AUDIT-STATUS.md"
        self.assertNotIn(1, xt.audit_status_groups(f))

    def test_impossible_due_date_is_an_error_not_a_crash(self):
        # "2026-13-45" khớp regex YYYY-MM-DD nhưng không phải ngày thật → từng văng ValueError.
        row = "AUD-CODE-001 | 🟢 | chấp nhận | a | đo được: x |  | chủ: t · hạn: 2026-13-45"
        self.assertEqual(
            self.check(audit_status_text(findings=[row])),
            ["AUD-CODE-001: hạn `2026-13-45` không phải ngày hợp lệ"],
        )

    def test_finding_without_summary(self):
        row = "AUD-SEC-001 | 🟢 | mở |  | đo được: x |  | "
        errors = self.check(audit_status_text(findings=[row]))
        self.assertEqual(errors, ["AUD-SEC-001: thiếu Tóm tắt"])

    def test_errors_ordered_tables_then_groups_then_findings(self):
        """Thứ tự lỗi là hợp đồng: dòng nhóm → thiếu dòng nhóm → từng phát hiện (hình thức, bằng chứng/Gate, kết thúc) → ID trùng."""
        groups = {
            1: ("đã quét", "", "", ""),
            2: ("bogus", "", "", ""),
            3: ("N/A", "", "", ""),
            4: ("chưa quét", "", "", ""),
        }
        findings = [
            "AUD-FOO-001 | 🔴 | mở | <tóm tắt> | chưa biết: a | | ",
            " | 🔵 | xong |  | thấy | | x",
            "AUD-SEC-003 | 🟠 | chấp nhận | x | đo được: a | `t` | chủ: An, hạn: 2026-10-01",
            "AUD-SEC-003 | 🟢 | bác bỏ | x | đo được: a | | ",
            "AUD-SEC-005 | 🟢 | đã sửa | x | đo được: a | | xong",
        ]
        text = audit_status_text(groups, findings).replace("| 5 | PERF |", "| 5 | SPEED |")
        f = self.tmp / "AUDIT-STATUS.md"
        f.write_text(text.replace("| 7 | DEP |", "| 99 | DEP |"), encoding="utf-8")
        errors, counts = xt.audit_check(f, strict=True, today=xt._dt.date(2026, 10, 14))
        id_form = "ID phải dạng AUD-<MÃ>-NNN với MÃ thuộc " + ", ".join(xt.AUDIT_CODES)
        self.assertEqual(
            errors,
            [
                "nhóm 1: thiếu Ngày quét YYYY-MM-DD",
                "nhóm 1: thiếu SHA lúc quét",
                "nhóm 2: trạng thái `bogus` không thuộc chưa quét · đã quét · rút gọn · N/A",
                "nhóm 3: `N/A` phải ghi lý do/phạm vi ở Ghi chú",
                "nhóm 4: chưa quét (--strict)",
                "nhóm 5: mã `SPEED` phải là `PERF`",
                "nhóm `99`: số nhóm phải 1–13",
                "nhóm 7: phải có đúng 1 dòng (đang có 0)",
                "AUD-FOO-001: còn chỗ trống của mẫu `<...>`",
                f"AUD-FOO-001: {id_form}",
                "AUD-FOO-001: 🔴 không thể dựa trên `chưa biết:` — đo hoặc hạ mức",
                "AUD-FOO-001: 🔴 phải có Gate (lệnh trong backtick hoặc `tay: <bước>`)",
                "AUD-FOO-001: 🔴 còn mở (--strict)",
                f"(dòng thiếu ID): {id_form}",
                "(dòng thiếu ID): mức `🔵` phải là 🔴/🟠/🟢",
                "(dòng thiếu ID): trạng thái `xong` không thuộc mở · đã sửa · chấp nhận · bác bỏ",
                "(dòng thiếu ID): thiếu Tóm tắt",
                "(dòng thiếu ID): Bằng chứng phải mở đầu `đo được:` / `suy luận:` / `chưa biết:`",
                "AUD-SEC-003: chấp nhận rủi ro đã quá hạn 2026-10-01",
                "AUD-SEC-003: `bác bỏ` phải ghi lý do ở Ghi chú",
                "AUD-SEC-005: `đã sửa` phải ghi PR (#N) hoặc SHA ở Ghi chú",
                "AUD-SEC-003: ID trùng 2 lần",
            ],
        )
        self.assertEqual(
            counts,
            {
                "nhóm đã quét": 1,
                "nhóm N/A": 9,
                "nhóm chưa quét": 1,
                "🔴 mở": 1,
                "🟠 chấp nhận": 1,
                "🟢 bác bỏ": 1,
                "🟢 đã sửa": 1,
            },
        )


# --------------------------------------------------------------------------- cmd_validate / list / compose / stats


class FrameworkCommandsTest(TmpDirCase):
    def setUp(self):
        super().setUp()
        self.fw = make_framework(self.tmp)

    def test_validate_ok(self):
        rc, out, _ = run_main("--framework", self.fw, "validate")
        self.assertEqual(rc, 0)
        self.assertRegex(out, r"^✓ Khung hợp lệ: \d+ file, 7 mục checklist\.\n$")

    def test_validate_reports_errors_and_exit_1(self):
        (self.fw / "08-backend" / "README.md").unlink()
        rc, out, _ = run_main("--framework", self.fw, "validate")
        self.assertEqual(rc, 1)
        self.assertIn("✗ ", out)
        self.assertRegex(out, r"\n\d+ lỗi\.\n$")

    def test_list_profiles(self):
        rc, out, _ = run_main("--framework", self.fw, "list", "profiles")
        self.assertEqual(rc, 0)
        lines = out.splitlines()
        self.assertEqual(len(lines), 2)
        self.assertTrue(lines[0].startswith("cli-tool"))  # sắp theo đường dẫn: cli-tool < web-app
        self.assertIn("CLI tool  (0 mục)", lines[0])
        self.assertTrue(lines[1].startswith("web-app"))
        self.assertIn("Web app  (1 mục)", lines[1])

    def test_list_industries(self):
        rc, out, _ = run_main("--framework", self.fw, "list", "industries")
        self.assertEqual(rc, 0)
        self.assertEqual(out.split(), ["fintech", "Fintech", "(1", "mục)"])

    def test_list_modules_uses_path_when_no_slug(self):
        rc, out, _ = run_main("--framework", self.fw, "list", "modules")
        self.assertEqual(rc, 0)
        labels = [ln.split()[0] for ln in out.splitlines()]
        self.assertEqual(labels, ["01-baseline/security", "08-backend/api", "08-backend/cli-only"])

    def test_compose_to_stdout(self):
        rc, out, _ = run_main("--framework", self.fw, "compose", "--profile", "web-app", "--industry", "fintech")
        self.assertEqual(rc, 0)
        self.assertIn("`BE-API-001`", out)
        self.assertIn("`IND-FIN-001`", out)
        self.assertNotIn("BE-CLI-001", out)
        self.assertNotIn("BE-API-999", out)

    def test_blueprint_status_prints_bad_lines(self):
        bp = self.tmp / "BP.md"
        bp.write_text("| MUST | 2 |\n- [x] `A-001` **MUST** a\n", encoding="utf-8")
        rc, out, _ = run_main("blueprint-status", bp, "--strict")
        self.assertEqual(rc, 1)
        self.assertIn("✗ Sai định dạng/thiếu mục: chỉ thấy 1/2 mục MUST", out)

    def test_compose_to_file_then_recompose_keeps_state(self):
        target = self.tmp / "BLUEPRINT.md"
        rc, out, _ = run_main("--framework", self.fw, "compose", "--profile", "web-app", "--out", target)
        self.assertEqual(rc, 0)
        self.assertIn(f"✓ Đã ghi {target}", out)
        target.write_text(
            target.read_text(encoding="utf-8").replace("- [ ] `BE-API-001`", "- [x] `BE-API-001`"), "utf-8"
        )
        rc, out, err = run_main("--framework", self.fw, "compose", "--profile", "web-app", "--out", target)
        self.assertEqual(rc, 0)
        self.assertIn("Giữ trạng thái 1 mục", err)
        self.assertIn("- [x] `BE-API-001`", target.read_text(encoding="utf-8"))
        with target.open("a", encoding="utf-8") as f:
            f.write("\n- [ ] `HM-MONEY-001` **MUST** mục riêng của dự án\n")
        rc, out, err = run_main("--framework", self.fw, "compose", "--profile", "web-app", "--out", target)
        self.assertEqual(rc, 0)
        self.assertIn("Giữ 1 mục riêng của dự án ở cuối: HM-MONEY-001", err)
        self.assertIn("- [ ] `HM-MONEY-001`", target.read_text(encoding="utf-8"))

    def test_compose_out_splits_backlog_and_carries_states(self):
        # ADR-0012: --out ghi BLUEPRINT.md (MUST) + BLUEPRINT-BACKLOG.md (SHOULD/MAY); ghép lại giữ trạng thái cả hai file,
        # kể cả từ bản cũ một file (trước ADR-0012) và khi đổi quy mô làm mục chuyển file.
        target, backlog = self.tmp / "BLUEPRINT.md", self.tmp / "BLUEPRINT-BACKLOG.md"
        full = xt.compose(self.fw, "web-app", [], "M", include_may=False)
        target.write_text(full.replace("- [ ] `PRF-WEB-001`", "- [~] `PRF-WEB-001`", 1) + "", encoding="utf-8")
        with target.open("a", encoding="utf-8") as f:
            f.write("\n- [ ] `HM-MONEY-001` **MUST** mục riêng của dự án\n")
        rc, out, err = run_main("--framework", self.fw, "compose", "--profile", "web-app", "--out", target)
        self.assertEqual(rc, 0, err)
        self.assertIn(f"✓ Đã ghi {target} + {backlog.name}", out)
        self.assertIn("- [~] `PRF-WEB-001`", backlog.read_text(encoding="utf-8"))
        self.assertNotIn("PRF-WEB-001", target.read_text(encoding="utf-8"))
        self.assertIn("HM-MONEY-001", target.read_text(encoding="utf-8"))
        self.assertNotIn("HM-MONEY-001", backlog.read_text(encoding="utf-8"))
        target.write_text(
            target.read_text(encoding="utf-8").replace("- [ ] `BE-API-001`", "- [x] `BE-API-001`"), "utf-8"
        )
        rc, _, err = run_main(
            "--framework", self.fw, "compose", "--profile", "web-app", "--scale", "S", "--out", target
        )
        self.assertEqual(rc, 0, err)
        self.assertIn("- [x] `BE-API-001` **SHOULD**", backlog.read_text(encoding="utf-8"))  # MUST ở M → SHOULD ở S
        self.assertIn("- [~] `PRF-WEB-001`", backlog.read_text(encoding="utf-8"))
        self.assertEqual(xt.blueprint_status(target)["levels"]["SHOULD"]["done"], 1)

    def test_compose_full_keeps_one_file_and_stdout_notes_backlog(self):
        target = self.tmp / "BP.md"
        rc, _, _ = run_main("--framework", self.fw, "compose", "--profile", "web-app", "--full", "--out", target)
        self.assertEqual(rc, 0)
        self.assertIn("`PRF-WEB-001` **SHOULD**", target.read_text(encoding="utf-8"))
        self.assertNotIn("backlog:", target.read_text(encoding="utf-8"))
        self.assertFalse((self.tmp / "BP-BACKLOG.md").exists())
        target.write_text(
            target.read_text(encoding="utf-8").replace("- [ ] `PRF-WEB-001`", "- [x] `PRF-WEB-001`"), "utf-8"
        )
        rc, _, err = run_main("--framework", self.fw, "compose", "--profile", "web-app", "--full", "--out", target)
        self.assertEqual(rc, 0)
        self.assertIn("Giữ trạng thái 1 mục", err)
        self.assertIn("- [x] `PRF-WEB-001` **SHOULD**", target.read_text(encoding="utf-8"))
        self.assertNotIn("không mang được ghi chú", err)
        text = target.read_text(encoding="utf-8")
        line = next(ln for ln in text.splitlines() if "`PRF-WEB-001`" in ln)
        target.write_text(text.replace(line, "- [x] `PRF-WEB-001` **SHOULD** chữ cũ"), "utf-8")
        rc, _, err = run_main("--framework", self.fw, "compose", "--profile", "web-app", "--full", "--out", target)
        self.assertEqual(rc, 0)
        self.assertIn("⚠ 1 mục [x]/[~] đổi chữ mà không mang được ghi chú", err)
        self.assertIn("PRF-WEB-001", err)
        rc, out, err = run_main("--framework", self.fw, "compose", "--profile", "web-app", "--full")
        self.assertEqual((rc, err), (0, ""))
        self.assertIn("`PRF-WEB-001` **SHOULD**", out)
        rc, out, err = run_main("--framework", self.fw, "compose", "--profile", "web-app")
        self.assertEqual(rc, 0)
        self.assertNotIn("PRF-WEB-001", out)
        self.assertIn("2 mục SHOULD/MAY không in", err)

    def test_stats(self):
        rc, out, _ = run_main("--framework", self.fw, "stats")
        self.assertEqual(rc, 0)
        lines = out.splitlines()
        self.assertIn("baseline=1", lines[0])
        self.assertIn("module=2", lines[0])
        self.assertEqual(lines[1], "Mục theo mức:   MUST=4, SHOULD=2, MAY=1")
        self.assertEqual(lines[2], "Tổng mục:       7")

    def test_missing_framework_dir_for_each_framework_command(self):
        for cmd in (["validate"], ["list", "profiles"], ["stats"], ["compose", "--profile", "x"]):
            with self.subTest(cmd=cmd):
                rc, out, err = run_main("--framework", self.tmp / "khong-co", *cmd)
                self.assertEqual((rc, out), (2, ""))
                self.assertIn("Không thấy thư mục khung", err)


class BrokenPipeTest(unittest.TestCase):
    """`xt.py … | head`: bên đọc đóng ống → im lặng, exit 141 như lệnh Unix (nợ review #110), không in `✗ Broken pipe`."""

    def test_broken_pipe_is_silent_141(self):
        with unittest.mock.patch.object(xt, "cmd_stats", side_effect=BrokenPipeError):
            rc, out, err = run_main("stats")  # stdout là StringIO: không có fd thật → bỏ qua dup2
        self.assertEqual((rc, out, err), (141, "", ""))
        fake = unittest.mock.MagicMock()
        fake.fileno.return_value = 1
        with (
            unittest.mock.patch.object(xt, "cmd_stats", side_effect=BrokenPipeError),
            unittest.mock.patch.object(sys, "stdout", fake),
            unittest.mock.patch("xt.os.open", return_value=99) as op,
            unittest.mock.patch("xt.os.dup2") as dup2,
            unittest.mock.patch("xt.os.close") as close,
        ):
            self.assertEqual(xt.main(["stats"]), 141)
        op.assert_called_once_with(os.devnull, os.O_WRONLY)
        dup2.assert_called_once_with(99, 1)
        close.assert_called_once_with(99)  # fd devnull đóng sau dup2 (CodeQL #112)


# --------------------------------------------------------------------------- blueprint-status


class BlueprintStatusTextTest(TmpDirCase):
    def test_status_reads_declared_backlog(self):
        # ADR-0012: blueprint-status đọc cả file backlog khai ở frontmatter; khai mà mất file → lỗi, không im lặng.
        main = self.tmp / "BLUEPRINT.md"
        main.write_text(
            "---\nkind: blueprint\nbacklog: BL.md\n---\n| MUST | 1 |\n- [x] `A-001` **MUST** xong\n", encoding="utf-8"
        )
        (self.tmp / "BL.md").write_text(
            "- [ ] `A-002` **SHOULD** mở\n- [~] `A-003` **SHOULD** miễn thiếu lý do\n", encoding="utf-8"
        )
        s = xt.blueprint_status(main)
        self.assertEqual(s["levels"]["SHOULD"], {"open": 1, "done": 0, "waived": 1})
        self.assertEqual((s["open_must"], s["bad_lines"]), ([], []))
        self.assertEqual(s["bad_waivers"], ["A-003 (BL.md dòng 2)"])
        (self.tmp / "BL.md").unlink()
        self.assertEqual(xt.blueprint_status(main)["bad_lines"], ["thiếu file backlog BL.md khai ở frontmatter"])
        rc, _, _ = run_main("blueprint-status", main, "--strict")
        self.assertEqual(rc, 1)

    def test_text_output_with_open_must_and_bad_waiver(self):
        f = self.tmp / "BLUEPRINT.md"
        f.write_text(
            "- [ ] `A-001` **MUST** mở → Kiểm: x\n"
            "- [~] `A-002` **SHOULD** miễn thiếu lý do\n"
            "- [x] `A-003` **MAY** xong\n",
            encoding="utf-8",
        )
        rc, out, _ = run_main("blueprint-status", f)
        self.assertEqual(rc, 0)
        self.assertIn("MUST    đạt    0 · miễn    0 · chưa    1", out)
        self.assertIn("SHOULD  đạt    0 · miễn    1 · chưa    0", out)
        self.assertIn("MAY     đạt    1 · miễn    0 · chưa    0", out)
        self.assertIn("✗ Miễn trừ không hợp lệ (thiếu lý do; MUST `Miễn` cần `Duyệt:`): A-002 (dòng 2)", out)
        self.assertIn("Còn 1 mục MUST chưa đạt: A-001", out)
        rc, _, _ = run_main("blueprint-status", f, "--strict")
        self.assertEqual(rc, 1)

    def test_text_output_ok_is_silent_on_problems(self):
        f = self.tmp / "BLUEPRINT.md"
        f.write_text("- [x] `A-001` **MUST** xong → Kiểm: x — Bằng chứng: y\n", encoding="utf-8")
        rc, out, _ = run_main("blueprint-status", f, "--strict")
        self.assertEqual(rc, 0)
        self.assertNotIn("✗", out)
        self.assertNotIn("Còn", out)

    def test_json_strict_fails_on_open_must(self):
        rc, out, _ = run_main("blueprint-status", "-", "--json", "--strict", stdin="- [ ] `A-001` **MUST** mở\n")
        self.assertEqual(rc, 1)
        self.assertFalse(json.loads(out)["ok"])

    def test_run_executes_check_commands(self):
        # LOOP-DESIGN-023: mục [x] có `— Kiểm: `<lệnh>`` được chạy lại trong thư mục chứa blueprint; đỏ = chưa đạt dù đã tick.
        (self.tmp / "ok.txt").write_text("1\n", encoding="utf-8")
        main = self.tmp / "BLUEPRINT.md"
        main.write_text(
            "---\nkind: blueprint\nbacklog: BL.md\n---\n"
            "- [x] `A-001` **MUST** xong → Kiểm: lời. · Nguồn: x — Kiểm: `test -f ok.txt`\n"
            "- [x] `A-002` **MUST** tick bằng lời — Bằng chứng: PR #7\n"
            "- [ ] `A-003` **MUST** mở — Kiểm: `test -f ok.txt`\n"
            "- [~] `A-004` **MUST** bỏ — Không áp dụng: không có — Kiểm: `false`\n"
            "- [X] `A-005` **MUST** cùng lệnh, khác khoảng trắng (Kiểm: `test  -f ok.txt`)\n",
            encoding="utf-8",
        )
        (self.tmp / "BL.md").write_text(
            "- [x] `A-006` **SHOULD** tick bằng lời\n- [x] `A-007` **SHOULD** đỏ — Kiểm: `echo ERR >&2; false`\n",
            encoding="utf-8",
        )
        found = xt.blueprint_checks(main)
        self.assertEqual([c["id"] for c in found["checks"]], ["A-001", "A-005", "A-007"])
        self.assertEqual(
            found["checks"][2], {"id": "A-007", "level": "SHOULD", "cmd": "echo ERR >&2; false", "file": "BL.md"}
        )
        self.assertEqual(found["unchecked_must"], ["A-002"])
        rc, out, _ = run_main("blueprint-status", main, "--run")
        self.assertEqual(rc, 0)  # không --strict: chỉ báo
        self.assertIn("✓ Kiểm A-001: exit 0 `test -f ok.txt`", out)
        self.assertIn("✓ Kiểm A-005: exit 0", out)
        self.assertIn("✗ Kiểm A-007: exit 1", out)
        self.assertIn("✗ Lệnh kiểm ĐỎ — mục đã tick nhưng chưa đạt: A-007", out)
        self.assertIn("ℹ 1 mục MUST đạt không có lệnh kiểm máy (ghi `— Kiểm: `<lệnh>``): A-002", out)
        rc, out, _ = run_main("blueprint-status", main, "--run", "--strict", "--json")
        self.assertEqual(rc, 1)
        doc = json.loads(out)
        self.assertEqual(
            (doc["ok"], doc["open_must"], doc["failed_checks"], doc["unchecked_must"]),
            (False, ["A-003"], ["A-007"], ["A-002"]),
        )
        self.assertEqual([(c["id"], c["exit_code"]) for c in doc["checks"]], [("A-001", 0), ("A-005", 0), ("A-007", 1)])
        self.assertEqual(doc["checks"][2]["output_tail"], "ERR")
        # Sửa xong (lệnh xanh, mục mở đã tick) → strict xanh; backlog mất → bỏ qua lệnh ở đó, blueprint_status đã báo.
        (self.tmp / "BL.md").write_text("- [x] `A-007` **SHOULD** xanh — Kiểm: `true`\n", encoding="utf-8")
        main.write_text(main.read_text(encoding="utf-8").replace("- [ ] `A-003`", "- [x] `A-003`"), encoding="utf-8")
        rc, out, _ = run_main("blueprint-status", main, "--run", "--strict")
        self.assertEqual(rc, 0, out)
        self.assertNotIn("✗", out)
        (self.tmp / "BL.md").unlink()
        self.assertEqual([c["id"] for c in xt.blueprint_checks(main)["checks"]], ["A-001", "A-003", "A-005"])
        rc, out, _ = run_main("blueprint-status", main, "--run", "--strict")
        self.assertEqual(rc, 1)
        self.assertIn("thiếu file backlog", out)

    def test_xt_compiles_without_warnings(self):
        # Chuỗi thường có `\`` từng làm `python3 xt.py` in SyntaxWarning ở mọi lần gọi (review #106).
        src = Path(xt.__file__).read_text(encoding="utf-8")
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            compile(src, xt.__file__, "exec")

    def test_run_needs_real_file_and_valid_timeout(self):
        rc, _, err = run_main("blueprint-status", "-", "--run", stdin="- [x] `A-001` **MUST** x\n")
        self.assertEqual(rc, 2)
        self.assertIn("--run cần file blueprint thật", err)
        f = self.tmp / "BLUEPRINT.md"
        f.write_text("- [x] `A-001` **MUST** x — Kiểm: `true`\n", encoding="utf-8")
        with unittest.mock.patch.dict(os.environ, {"XT_RECORD_TIMEOUT": "x"}):
            rc, _, err = run_main("blueprint-status", f, "--run")
        self.assertEqual(rc, 2)
        self.assertIn("XT_RECORD_TIMEOUT", err)
        rc, out, _ = run_main("blueprint-status", f, "--run", "--strict")  # mọi MUST tick đều có lệnh: không dòng ℹ
        self.assertEqual(rc, 0)
        self.assertNotIn("ℹ", out)

    def test_run_once_per_command_timeout_redact_and_bad_note(self):
        f = self.tmp / "BLUEPRINT.md"
        f.write_text(
            "- [x] `A-001` **MUST** a — Kiểm: `echo x >> dem.txt`\n"
            "- [x] `A-002` **MUST** b — Kiểm: `echo  x  >>  dem.txt`\n"
            "- [x] `A-003` **MUST** c — Kiểm: `sleep 5`\n"
            "- [x] `A-004` **MUST** d — Kiểm: `echo token=ghp_abcdefghijklmnopqrstuvwxyz0123456789 && false`\n"
            "- [x] `A-005` **MUST** e — Kiểm: chạy `false`\n"  # ghi chú Kiểm: không có lệnh ngay sau dấu hai chấm
            "- [x] `A-006` **MUST** f — Kiểm: `true` `false`\n"  # cặp backtick thứ hai từng bị bỏ im lặng (xanh giả)
            "- [x] `A-007` **MUST** g — Kiểm: `true` — Kiểm: `false`\n"
            "- [x] `A-008` **MUST** h — Kiểm: `true` — Bằng chứng: `ci.yml` job quality\n",  # ghi chú khác có backtick: được
            encoding="utf-8",
        )
        with unittest.mock.patch.dict(os.environ, {"XT_RECORD_TIMEOUT": "1"}):
            rc, out, _ = run_main("blueprint-status", f, "--run", "--strict", "--json")
        self.assertEqual(rc, 1)
        doc = json.loads(out)
        self.assertEqual((self.tmp / "dem.txt").read_text(encoding="utf-8"), "x\n")  # cùng lệnh: chạy một lần
        by_id = {c["id"]: c for c in doc["checks"]}
        self.assertEqual(by_id["A-003"]["exit_code"], 124)
        self.assertNotIn("ghp_", by_id["A-004"]["cmd"] + by_id["A-004"]["output_tail"])
        self.assertEqual((by_id["A-005"]["exit_code"], by_id["A-005"]["cmd"]), (2, ""))
        self.assertIn("phải có đúng một lệnh trong một cặp backtick", by_id["A-005"]["output_tail"])
        self.assertEqual((by_id["A-008"]["cmd"], by_id["A-008"]["exit_code"]), ("true", 0))
        self.assertEqual(doc["failed_checks"], ["A-003", "A-004", "A-005", "A-006", "A-007"])
        self.assertEqual(doc["unchecked_must"], [])


# --------------------------------------------------------------------------- loop


class ProjectDirTest(TmpDirCase):
    """AUD-XFEAT-001: không có CLAUDE_PROJECT_DIR → gốc dự án = thư mục cha gần nhất có dấu hiệu dự án, không phải cwd."""

    def test_walks_up_to_project_marker(self):
        env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"}
        sub = self.tmp / "proj" / "a" / "b"
        sub.mkdir(parents=True)
        for marker in (".git", "xt.yaml", ".xtemplates", ".autopilot"):
            m = self.tmp / "proj" / marker
            m.mkdir() if marker != "xt.yaml" else m.write_text("", encoding="utf-8")
            with (
                unittest.mock.patch.dict(os.environ, env, clear=True),
                unittest.mock.patch.object(os, "getcwd", return_value=str(sub)),
            ):
                self.assertEqual(xt.project_dir(), (self.tmp / "proj").resolve(), marker)
            m.rmdir() if marker != "xt.yaml" else m.unlink()

    def test_nested_git_repo_does_not_win_over_project_marker(self):
        # Review #38: repo git lồng (apps/web/.git) trong dự án có xt.yaml → gốc vẫn là dự án.
        env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"}
        proj = self.tmp / "p1"
        (proj / ".git").mkdir(parents=True)
        (proj / "xt.yaml").write_text("", encoding="utf-8")
        web = proj / "apps" / "web"
        (web / ".git").mkdir(parents=True)
        with (
            unittest.mock.patch.dict(os.environ, env, clear=True),
            unittest.mock.patch.object(os, "getcwd", return_value=str(web)),
        ):
            self.assertEqual(xt.project_dir(), proj.resolve())

    def test_installed_copy_uses_parent_of_xtemplates(self):
        # Như dev-task.sh: xt.py ở `<gốc>/.xtemplates/scripts/` → gốc = cha của `.xtemplates`, bất kể cwd.
        env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"}
        proj = self.tmp / "dich"
        scripts = proj / ".xtemplates" / "scripts"
        scripts.mkdir(parents=True)
        with (
            unittest.mock.patch.dict(os.environ, env, clear=True),
            unittest.mock.patch.object(xt, "SCRIPT_DIR", scripts),
            unittest.mock.patch.object(os, "getcwd", return_value=str(self.tmp)),
        ):
            self.assertEqual(xt.project_dir(), proj.resolve())

    def test_no_marker_falls_back_to_cwd_and_env_wins(self):
        sub = self.tmp / "x"
        sub.mkdir()
        with (
            unittest.mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": ""}),
            unittest.mock.patch.object(os, "getcwd", return_value=str(sub)),
        ):
            self.assertEqual(xt.project_dir(), sub.resolve())
        with unittest.mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(self.tmp)}):
            self.assertEqual(xt.project_dir(), self.tmp.resolve())


class ChangelogCheckTest(TmpDirCase):
    """BASE-REPO-007 / AUD-DOC-020: cấu trúc CHANGELOG theo Keep a Changelog, bản mới nhất khớp VERSION."""

    GOOD = (
        "# Changelog\n\n## [Unreleased]\n\n### Added\n- a\n\n### Fixed\n- b\n\n"
        "## [2.0.0] - 2026-10-14\n\n### Added\n- c\n\n## [1.0.0] - 2026-01-02\n\n### Added\n- d\n"
    )

    def errs(self, text: str, version: str | None = "2.0.0") -> list[str]:
        return xt.changelog_check(text, version)

    def test_good(self):
        self.assertEqual(self.errs(self.GOOD), [])
        self.assertEqual(self.errs(self.GOOD, None), [])

    def test_violations(self):
        cases = {
            "Unreleased": self.GOOD.replace("## [Unreleased]", "## [Chưa phát hành]"),
            "trùng": self.GOOD.replace("### Fixed\n- b", "### Added\n- b", 1),
            "nhóm `### Misc`": self.GOOD.replace("### Fixed", "### Misc", 1),
            "ngày ISO": self.GOOD.replace("## [1.0.0] - 2026-01-02", "## [1.0.0] - 02/01/2026"),
            "giảm dần": self.GOOD.replace("[1.0.0] - 2026-01-02", "[3.0.0] - 2026-01-02"),
            "ngày": self.GOOD.replace("2026-01-02", "2026-13-45"),
            "ngày phải giảm": self.GOOD.replace("2026-01-02", "2027-01-02"),
            "`### Added` trùng": self.GOOD.replace("### Fixed\n- b", "### Added (harness)\n- b", 1),
        }
        for want, text in cases.items():
            got = self.errs(text)
            self.assertTrue(any(want in e for e in got), f"{want}: {got}")
        self.assertTrue(any("VERSION" in e for e in self.errs(self.GOOD, "2.1.0")))

    def test_fenced_code_and_yanked(self):
        text = self.GOOD.replace("### Fixed\n- b", "### Fixed\n- b\n\n```\n## ví dụ\n### Misc\n```", 1)
        self.assertEqual(self.errs(text), [])
        self.assertEqual(self.errs(self.GOOD.replace("2026-01-02", "2026-01-02 [YANKED]")), [])

    def test_cli(self):
        (self.tmp / "CHANGELOG.md").write_text(self.GOOD, encoding="utf-8")
        (self.tmp / "VERSION").write_text("2.0.0\n", encoding="utf-8")
        rc, out, _ = run_main("changelog-check", self.tmp / "CHANGELOG.md")
        self.assertEqual(rc, 0, out)
        self.assertIn("✓", out)
        (self.tmp / "VERSION").write_text("9.9.9\n", encoding="utf-8")
        rc, out, _ = run_main("changelog-check", self.tmp / "CHANGELOG.md")
        self.assertEqual(rc, 1)
        self.assertIn("✗", out)
        (self.tmp / "VERSION").unlink()
        rc, out, _ = run_main("changelog-check", self.tmp / "CHANGELOG.md")
        self.assertEqual(rc, 0, out)

    def test_repo_changelog_passes(self):
        rc, out, _ = run_main("changelog-check", ROOT / "CHANGELOG.md")
        self.assertEqual(rc, 0, out)


class FeedbackTest(TmpDirCase):
    """ADR-0010: dự án đích ghi lỗi do khung + cách khắc phục; repo khung gộp theo (loại, ID)."""

    def setUp(self):
        super().setUp()
        self.enterContext(unittest.mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(self.tmp)}))
        self.fb = self.tmp / "docs" / "xtemplates-feedback"

    def add(self, *extra: str) -> tuple[int, str, str]:
        base = [
            "--kind",
            "hook-chan-nham",
            "--id",
            "pre-bash-guard",
            "--symptom",
            "rm -rf ./build bị deny",
            "--fix",
            "chạy tay",
        ]
        return run_main("feedback", "add", *base, *extra)

    def test_add_writes_redacted_single_line_entry_with_framework_version(self):
        (self.tmp / ".xtemplates").mkdir()
        (self.tmp / ".xtemplates" / "VERSION").write_text("3.0.0\n", encoding="utf-8")
        rc, out, _ = self.add("--repro", "token=abc123\n### giả", "--suggest", "cho phép ./build")
        self.assertEqual(rc, 0)
        self.assertTrue(out.startswith("✓ FB-001 → docs/xtemplates-feedback/FB-001.md"))
        text = (self.fb / "FB-001.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("# FB-001 · hook-chan-nham · pre-bash-guard\n\n- Khung: 3.0.0\n"))
        self.assertIn("- Tái hiện: token=*** ### giả\n", text)
        self.assertIn("- Đề xuất cho khung: cho phép ./build\n- Nguồn: tay\n", text)
        self.assertNotIn("abc123", text)
        self.add()
        e = xt.feedback_entries(self.fb)[1]
        self.assertEqual((e["file"], e["repro"], e["suggest"]), ("FB-002.md", "—", "—"))

    def test_add_rejects_empty_symptom_or_fix_and_bad_kind(self):
        rc, out, err = run_main("feedback", "add", "--kind", "cong-cu", "--id", "x", "--symptom", " ", "--fix", "f")
        self.assertEqual((rc, out), (2, ""))
        self.assertIn("--symptom và --fix không được rỗng", err)
        self.assertFalse(self.fb.exists())
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            xt.main(["feedback", "add", "--kind", "khac", "--id", "x", "--symptom", "s", "--fix", "f"])

    def test_framework_version_fallbacks(self):
        self.assertEqual(xt._framework_version(self.tmp), "?")
        (self.tmp / "VERSION").write_text("\n", encoding="utf-8")
        self.assertEqual(xt._framework_version(self.tmp), "?")
        (self.tmp / "VERSION").write_text("2.0.0\n", encoding="utf-8")
        self.assertEqual(xt._framework_version(self.tmp), "2.0.0")

    def test_entries_sorted_numerically_and_ignore_noise(self):
        self.fb.mkdir(parents=True)
        for name in ("FB-010.md", "FB-002.md"):
            (self.fb / name).write_text(
                f"# x\n- Loại: cong-cu\n- Lạ: bỏ qua\nkhông phải dòng\n- ID: {name}\n", encoding="utf-8"
            )
        (self.fb / "FB-x.md").write_text("- Loại: rác\n", encoding="utf-8")
        entries = xt.feedback_entries(self.fb)
        self.assertEqual([e["file"] for e in entries], ["FB-002.md", "FB-010.md"])
        self.assertEqual(entries[0], {"file": "FB-002.md", "kind": "cong-cu", "id": "FB-002.md"})
        self.add()
        self.assertTrue((self.fb / "FB-011.md").exists())

    def test_collect_waived_must_and_blocked_without_duplicates(self):
        (self.tmp / "BLUEPRINT.md").write_text(
            "- [~] `SEC-AUTH-001` **MUST** a — Miễn: dùng SSO ngoài\n"
            "- [~] `SEC-AUTH-002` **MUST** b\n"
            "- [~] `BASE-X-003` **SHOULD** c — Miễn: x\n"
            "- [x] `BASE-X-004` **MUST** d\n",
            encoding="utf-8",
        )
        xt.write_state({"active": True, "blocked": True, "blocked_reason": "cần khoá thật"}, self.tmp)
        rc, out, _ = run_main("feedback", "collect")
        self.assertEqual((rc, out), (0, "✓ Thêm 3 phản hồi tự gom: FB-001, FB-002, FB-003\n"))
        got = [(e["kind"], e["id"], e["symptom"]) for e in xt.feedback_entries(self.fb)]
        self.assertEqual(
            got,
            [
                ("mien-tru", "SEC-AUTH-001", "MUST bị miễn: dùng SSO ngoài"),
                ("mien-tru", "SEC-AUTH-002", "MUST bị miễn: (thiếu lý do)"),
                ("bi-chan", "loop", "autopilot bị chặn: cần khoá thật"),
            ],
        )
        rc, out, _ = run_main("feedback", "collect")
        self.assertEqual(out, "✓ Thêm 0 phản hồi tự gom (không có tín hiệu mới)\n")

    def test_collect_skips_in_framework_repo(self):  # AUD-HAR-048: luồng phản hồi dành cho dự án đích
        (self.tmp / "BLUEPRINT.md").write_text("- [~] `SEC-AUTH-001` **MUST** a — Miễn: x\n", encoding="utf-8")
        (self.tmp / "framework" / "00-method").mkdir(parents=True)
        (self.tmp / "framework" / "00-method" / "conventions.md").write_text("x", encoding="utf-8")
        (self.tmp / "scripts").mkdir()
        (self.tmp / "scripts" / "xt.py").write_text("x", encoding="utf-8")
        rc, out, _ = run_main("feedback", "collect")
        self.assertEqual(rc, 0)
        self.assertIn("repo khung", out)
        self.assertFalse(self.fb.exists())

    def test_collect_final_verdict_variants_and_missing_blueprint(self):
        cases = [
            ({"final_verdict": {"verdict": "blocked", "reason": "lỗi lặp"}, "last_failure_task": "T-004"}, 1),
            ({"final_verdict": {"verdict": "done", "reason": "xong"}}, 0),
            ({"final_verdict": "hỏng"}, 0),
        ]
        for st, n in cases:
            with self.subTest(st=st):
                shutil.rmtree(self.fb, ignore_errors=True)
                xt.write_state({"active": False, **st}, self.tmp)
                run_main("feedback", "collect", "--blueprint", "khong-co.md")
                self.assertEqual(len(xt.feedback_entries(self.fb)) if self.fb.exists() else 0, n)
        shutil.rmtree(self.fb, ignore_errors=True)
        xt.write_state({"active": False, **cases[0][0]}, self.tmp)
        run_main("feedback", "collect")
        self.assertEqual(xt.feedback_entries(self.fb)[0]["id"], "T-004")

    def test_list_text_json_and_missing_dir(self):
        self.assertEqual(run_main("feedback", "list"), (0, "", ""))
        self.assertEqual(run_main("feedback", "list", "--json")[1], "[]\n")
        self.add()
        out = run_main("feedback", "list")[1]
        self.assertTrue(out.startswith("FB-001.md  hook-chan-nham  pre-bash-guard   rm -rf ./build bị deny"))
        data = json.loads(run_main("feedback", "list", str(self.fb), "--json")[1])
        self.assertEqual(data[0]["fix"], "chạy tay")
        (self.fb / "FB-002.md").write_text("# rỗng\n", encoding="utf-8")
        self.assertIn("FB-002.md  ?               ?", run_main("feedback", "list")[1])

    def test_aggregate_groups_projects_and_marks_ready(self):
        a, b = self.tmp / "a", self.tmp / "b"
        for d, proj in ((a, "a"), (b, "b")):
            xt.write_feedback(
                d.parent / proj, {"kind": "muc-sai", "id": "SEC-AUTH-001", "symptom": "mơ hồ | khó", "fix": "x"}
            )
        xt.write_feedback(
            a, {"kind": "cong-cu", "id": "xt.py loop", "symptom": "crash", "fix": "f", "repro": "xt.py loop x"}
        )
        xt.write_feedback(a, {"kind": "tai-lieu", "id": "README", "symptom": "thiếu", "fix": "đọc code"})
        src = [
            "--from", f"a={a / 'docs' / 'xtemplates-feedback'}",
            "--from", f"b={b / 'docs' / 'xtemplates-feedback'}",
            "--from", f"c={self.tmp / 'khong-co'}",
        ]  # fmt: skip
        groups = json.loads(run_main("feedback", "aggregate", *src, "--json")[1])
        summary = [(g["kind"], g["id"], g["projects"], g["ready"]) for g in groups]
        self.assertEqual(
            summary,
            [
                ("muc-sai", "SEC-AUTH-001", ["a", "b"], True),
                ("cong-cu", "xt.py loop", ["a"], True),
                ("tai-lieu", "README", ["a"], False),
            ],
        )
        table = run_main("feedback", "aggregate", *src)[1].splitlines()
        self.assertEqual(table[0].count("|"), 7)
        self.assertEqual(table[2], "| ✅ | muc-sai | `SEC-AUTH-001` | a, b | mơ hồ \\| khó | x |")
        self.assertTrue(table[4].startswith("| — | tai-lieu |"))

    def test_aggregate_accepts_repo_root_and_warns_missing(self):  # AUD-HAR-051
        a = self.tmp / "a"
        xt.write_feedback(a, {"kind": "muc-sai", "id": "SEC-AUTH-001", "symptom": "s", "fix": "x"})
        code, out, err = run_main(
            "feedback", "aggregate", "--from", f"a={a}", "--from", f"b={self.tmp / 'b'}", "--json"
        )
        self.assertEqual(code, 0)
        self.assertEqual([g["id"] for g in json.loads(out)], ["SEC-AUTH-001"])
        self.assertIn("b", err)
        self.assertIn("không có", err)

    def test_aggregate_local_ids_group_by_symptom(self):  # AUD-CODE-004: `T-003`/`loop` là ID cục bộ của từng dự án
        dirs = {p: self.tmp / p for p in ("a", "b", "c")}
        for proj, why in (("a", "cần khoá thật"), ("b", "CI đỏ lặp"), ("c", "Cần  khoá thật")):
            xt.write_feedback(dirs[proj], {"kind": "bi-chan", "id": "T-003", "symptom": why, "fix": "người"})
        xt.write_feedback(dirs["a"], {"kind": "muc-sai", "id": "SEC-AUTH-001", "symptom": "s1", "fix": "x"})
        xt.write_feedback(dirs["b"], {"kind": "muc-sai", "id": "SEC-AUTH-001", "symptom": "s2", "fix": "y"})
        src = [x for p, d in dirs.items() for x in ("--from", f"{p}={d / 'docs' / 'xtemplates-feedback'}")]
        groups = json.loads(run_main("feedback", "aggregate", *src, "--json")[1])
        summary = sorted((g["kind"], g["projects"], g["ready"]) for g in groups)
        self.assertEqual(
            summary,
            [("bi-chan", ["a", "c"], True), ("bi-chan", ["b"], False), ("muc-sai", ["a", "b"], True)],
        )
        table = "\n".join(run_main("feedback", "aggregate", *src)[1].splitlines())
        self.assertIn("s1; s2", table)  # mọi triệu chứng khác nhau, không chỉ cái đầu
        empty = {p: self.tmp / f"e{p}" for p in ("a", "b")}  # review #84: triệu chứng rỗng không gộp chung
        for proj, tid in (("a", "T-001"), ("b", "T-007")):
            xt.write_feedback(empty[proj], {"kind": "bi-chan", "id": tid, "symptom": "", "fix": "người"})
        src = [x for p, d in empty.items() for x in ("--from", f"{p}={d / 'docs' / 'xtemplates-feedback'}")]
        groups = json.loads(run_main("feedback", "aggregate", *src, "--json")[1])
        self.assertEqual(sorted((g["projects"], g["ready"]) for g in groups), [(["a"], False), (["b"], False)])

    def test_aggregate_redacts_hand_edited_entries(self):
        """AUD-CFG-002: FB sửa tay sau `feedback add` vẫn được che trước khi ra PR nháp (repo khung public)."""
        d = self.tmp / "p" / "docs" / "xtemplates-feedback"
        d.mkdir(parents=True)
        pw = "".join(["hun", "ter2"])
        (d / "FB-001.md").write_text(
            f"---\nkind: cong-cu\nid: X-1\n---\n\n- Triệu chứng: password={pw}\n- Cách sửa: x\n", encoding="utf-8"
        )
        for args in (["--json"], []):
            with self.subTest(args):
                out = run_main("feedback", "aggregate", "--from", f"p={d}", *args)[1]
                self.assertNotIn(pw, out)

    def test_aggregate_rejects_bad_source_spec(self):
        for spec in ("khong-dau-bang", "=thu-muc", "du-an="):
            with self.subTest(spec):
                rc, out, err = run_main("feedback", "aggregate", "--from", spec)
                self.assertEqual((rc, out), (2, ""))
                self.assertIn("--from phải dạng", err)


class LoopCommandsTest(TmpDirCase):
    def setUp(self):
        super().setUp()
        self.env = self.enterContext(unittest.mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(self.tmp)}))
        os.environ.pop("XT_DEBUG", None)

    def write_plan(self, text: str = "- [ ] `T-001` làm gì đó — Gate: `true`\n") -> None:
        p = self.tmp / "docs" / "autopilot" / "PLAN.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def test_init_without_plan_is_exit_2(self):
        rc, out, err = run_main("loop", "init")
        self.assertEqual((rc, out), (2, ""))
        self.assertIn("✗ Không thấy docs/autopilot/PLAN.md", err)
        self.assertIsNone(xt.read_state(self.tmp))

    def test_init_with_missing_blueprint_is_exit_2(self):
        # AUD-HAR-016: --blueprint trỏ file không có → báo lỗi, không bật vòng lặp (gõ nhầm sẽ làm verdict bỏ qua blueprint).
        self.write_plan()
        rc, out, err = run_main("loop", "init", "--blueprint", "TYPO.md")
        self.assertEqual((rc, out), (2, ""))
        self.assertIn("✗ Không thấy TYPO.md", err)
        self.assertIsNone(xt.read_state(self.tmp))

    def test_init_warns_when_gate_lint_or_test_is_noop(self):
        # ADR-0011: xt.yaml để `lint`/`test` rỗng hoặc no-op thì cổng ĐỎ trong vòng — báo ngay khi bật, không chặn.
        self.write_plan()
        (self.tmp / "xt.yaml").write_text('lint: "echo ok"\ntypecheck: ""\ntest: ""\nbuild: ""\n', encoding="utf-8")
        rc, _, err = run_main("loop", "init")
        self.assertEqual(rc, 0)
        self.assertIn("⚠ Cổng sẽ ĐỎ trong vòng (ADR-0011): xt.yaml để lint, test rỗng/no-op", err)
        (self.tmp / "xt.yaml").write_text("lint: ruff check .\ntest: 'pytest -q'\n", encoding="utf-8")
        self.assertNotIn("ADR-0011", run_main("loop", "init")[2])
        (self.tmp / "xt.yaml").unlink()
        self.assertNotIn("ADR-0011", run_main("loop", "init")[2])  # thiếu xt.yaml: dev-task tự dò, doctor đã báo
        # AUD-HAR-025: comment cuối dòng không phải lệnh
        (self.tmp / "xt.yaml").write_text("lint: true  # TODO\ntest: # TODO điền\n", encoding="utf-8")
        self.assertEqual(xt.gate_noop_keys(self.tmp), ["lint", "test"])
        (self.tmp / "xt.yaml").write_text('lint: ruff check .  # kiểm\ntest: "pytest -q # x"\n', encoding="utf-8")
        self.assertEqual(xt.gate_noop_keys(self.tmp), [])

    def test_init_then_status_text_and_json(self):
        self.write_plan()
        rc, out, _ = run_main("loop", "init", "--max-iterations", "7")
        self.assertEqual(rc, 0)
        self.assertIn("trần=7 vòng", out)
        rc, out, _ = run_main("loop", "status")
        self.assertEqual(rc, 0)
        self.assertTrue(out.startswith("verdict: continue — làm task T-001"))
        rc, out, _ = run_main("loop", "status", "--json")
        data = json.loads(out)
        self.assertEqual((rc, data["verdict"], data["task"], data["iterations"]), (0, "continue", "T-001", 0))

    def test_status_json_when_inactive(self):
        rc, out, _ = run_main("loop", "status", "--json")
        data = json.loads(out)
        self.assertEqual((rc, data["verdict"], data["iterations"]), (0, "inactive", 0))

    def test_record_requires_command(self):
        for argv in (["loop", "record", "--task", "T-001"], ["loop", "record", "--task", "T-001", "--"]):
            with self.subTest(argv=argv):
                rc, out, err = run_main(*argv)
                self.assertEqual((rc, out), (2, ""))
                self.assertIn("Thiếu lệnh kiểm sau '--'", err)
        self.assertFalse((self.tmp / ".autopilot" / "evidence").exists())

    def test_record_runs_command_and_writes_evidence(self):
        rc, out, _ = run_main("loop", "record", "--task", "T-001", "--", "true")
        self.assertEqual(rc, 0)
        self.assertIn("T-001: exit 0", out)
        self.assertEqual(xt.read_evidence("T-001", self.tmp)["exit_code"], 0)

    def test_stats_text_and_json(self):
        rc, out, _ = run_main("loop", "stats")
        self.assertEqual(rc, 0)
        self.assertIn("Task đã chạy Gate: 0 · lần chạy: 0 (đỏ 0) · xanh lần đầu: —", out)
        self.assertIn("Vòng: 0/— · chờ người: 0 · blocked: False", out)
        for cmd in ("false", "false", "true"):
            run_main("loop", "record", "--task", "T-001", "--", cmd)
        run_main("loop", "record", "--task", "T-002", "--", "true")
        rc, out, _ = run_main("loop", "stats")
        self.assertIn("lần chạy: 4 (đỏ 2) · xanh lần đầu: 50%", out)
        self.assertIn("  T-001: 3 lần · xanh ở lần 3", out)
        self.assertIn("⚠ Task cần ≥ 3 lần chạy (spec/Gate sai? — LOOP-DESIGN-011): T-001", out)
        run_main("loop", "record", "--task", "T-003", "--", "false")
        rc, out, _ = run_main("loop", "stats", "--json", "--all")
        data = json.loads(out)
        self.assertEqual((rc, data["runs"], data["never_green"]), (0, 5, ["T-003"]))
        self.assertIn("  T-003: 1 lần · chưa xanh", run_main("loop", "stats")[1])

    def test_block_without_state_creates_blocked_state(self):
        rc, out, _ = run_main("loop", "block", "--reason", "cần người quyết")
        st = xt.read_state(self.tmp)
        self.assertEqual((rc, out), (0, "■ BLOCKED: cần người quyết\n"))
        self.assertTrue(st["active"] and st["blocked"])
        self.assertEqual(st["blocked_reason"], "cần người quyết")

    def decide(self, *extra: str, choice: str = "1") -> tuple[int, str, str]:
        base = ["--question", "Lưu phiên ở đâu?", "--option", "Cookie HttpOnly", "--option", "localStorage"]
        return run_main("loop", "decide", *base, "--choice", choice, "--why", "chặn XSS đọc token", *extra)

    def test_decide_creates_log_and_numbers_entries(self):
        # LOOP-STOP-018: phiên chính tự duyệt, mỗi quyết định một mục D-NNN tăng dần, không cần state autopilot.
        rc, out, err = self.decide("--revert", "đổi middleware phiên")
        self.assertEqual((rc, out, err), (0, "✓ D-001 tự duyệt: Cookie HttpOnly → docs/autopilot/DECISIONS.md\n", ""))
        rc, out, _ = self.decide("--revert", "đổi lại", choice="localStorage")
        self.assertEqual((rc, out.split(" →")[0]), (0, "✓ D-002 tự duyệt: localStorage"))
        text = (self.tmp / "docs" / "autopilot" / "DECISIONS.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith(xt.DECISIONS_HEADER))
        self.assertEqual(xt.DECISION_ID_RE.findall(text), ["001", "002"])
        self.assertIn("- Phương án: (1) Cookie HttpOnly · (2) localStorage\n- Chọn: Cookie HttpOnly\n", text)
        self.assertIn(
            "- Lý do (tiêu chí chất lượng cuối): chặn XSS đọc token\n- Đường lùi: đổi middleware phiên\n", text
        )
        self.assertIsNone(xt.read_state(self.tmp))

    def test_decide_prod_switch_line_only_when_given(self):
        # Mặc định tự host; đề xuất dịch vụ khi chạy thật nằm trong mục D-NNN để G7 gom bằng một lần tìm.
        self.decide("--revert", "r", "--prod", "  SES hoặc Postmark\nthay Mailpit ")
        self.decide("--revert", "r", "--prod", " ")
        text = (self.tmp / "docs" / "autopilot" / "DECISIONS.md").read_text(encoding="utf-8")
        self.assertIn(f"- Đường lùi: r\n- {xt.PROD_SWITCH_LABEL} SES hoặc Postmark thay Mailpit\n\n### D-002", text)
        self.assertEqual(text.count(xt.PROD_SWITCH_LABEL), 1)

    def test_decide_custom_log_continues_after_highest_id(self):
        log = self.tmp / "DEC.md"
        log.write_text("# Nhật ký\n\n### D-007 · cũ · q\n### D-003 · cũ · q\n", encoding="utf-8")
        rc, out, _ = self.decide("--revert", "r", "--log", "DEC.md")
        self.assertEqual((rc, out), (0, "✓ D-008 tự duyệt: Cookie HttpOnly → DEC.md\n"))
        self.assertTrue(log.read_text(encoding="utf-8").startswith("# Nhật ký\n\n### D-007"))

    def test_decide_fields_are_single_line(self):
        # Xuống dòng trong trường không tạo được tiêu đề `### D-…` giả làm lệch số thứ tự.
        rc, _, _ = run_main(
            "loop", "decide", "--question", "q\n### D-900 giả", "--option", "a\nb", "--option", "c",
            "--choice", "a b", "--why", "w", "--revert", "r",
        )  # fmt: skip
        text = (self.tmp / "docs" / "autopilot" / "DECISIONS.md").read_text(encoding="utf-8")
        self.assertEqual((rc, xt.DECISION_ID_RE.findall(text)), (0, ["001"]))
        self.assertIn("### D-001 · ", text)
        self.assertIn(" · q ### D-900 giả\n", text)
        self.assertIn("- Chọn: a b\n", text)

    def test_decide_rejects_bad_input_without_writing(self):
        cases = {
            "một phương án": (["--option", "a", "--option", " a ", "--choice", "1"], "cần ≥ 2 phương án"),
            "choice ngoài khoảng": (["--option", "a", "--option", "b", "--choice", "3"], "--choice phải là"),
            "choice không khớp": (["--option", "a", "--option", "b", "--choice", "c"], "--choice phải là"),
            "choice 0": (["--option", "a", "--option", "b", "--choice", "0"], "--choice phải là"),
        }
        for name, (argv, msg) in cases.items():
            with self.subTest(name):
                rc, out, err = run_main("loop", "decide", "--question", "q", *argv, "--why", "w", "--revert", "r")
                self.assertEqual((rc, out), (2, ""))
                self.assertIn(msg, err)
        rc, _, err = run_main(
            "loop", "decide", "--question", " ", "--option", "a", "--option", "b", "--choice", "1",
            "--why", "w", "--revert", "\n",
        )  # fmt: skip
        self.assertEqual(rc, 2)
        self.assertIn("không được rỗng", err)
        self.assertFalse((self.tmp / "docs").exists())

    def test_init_single_session_sizes_iterations_from_plan(self):
        self.write_plan("".join(f"- [ ] `T-00{i}` việc — Gate: `true`\n" for i in range(1, 7)) + "- [x] `T-007` xong\n")
        rc, out, _ = run_main("loop", "init", "--single-session")
        st = xt.read_state(self.tmp)
        self.assertEqual((rc, st["max_iterations"], st["single_session"]), (0, 48, True))
        self.assertIn("trần=48 vòng · chế độ một phiên", out)
        self.write_plan()
        run_main("loop", "init", "--single-session", "--force")
        self.assertEqual(xt.read_state(self.tmp)["max_iterations"], 40)
        run_main("loop", "init", "--single-session", "--max-iterations", "7", "--force")
        self.assertEqual(xt.read_state(self.tmp)["max_iterations"], 7)
        run_main("loop", "init", "--force")
        self.assertEqual(
            (xt.read_state(self.tmp)["max_iterations"], xt.read_state(self.tmp)["single_session"]), (100, False)
        )

    def test_init_refuses_live_loop(self):
        # LOOP-HARNESS-024 (rà stored 01 §3h): phiên thứ hai không xoá trạng thái vòng đang chạy của phiên kia.
        self.write_plan()
        self.assertEqual(run_main("loop", "init")[0], 0)
        st = xt.read_state(self.tmp)
        st["iterations"] = 5
        xt.write_state(st, self.tmp)
        rc, _, err = run_main("loop", "init")
        self.assertEqual(rc, 2)
        self.assertIn("LOOP-HARNESS-024", err)
        self.assertEqual(xt.read_state(self.tmp)["iterations"], 5)  # không ghi đè
        st["deadline"] = "2000-01-01T00:00:00+00:00"  # vòng đã hết hạn → khởi tạo lại được
        xt.write_state(st, self.tmp)
        self.assertEqual(run_main("loop", "init")[0], 0)
        self.assertEqual(run_main("loop", "init", "--force")[0], 0)
        st = xt.read_state(self.tmp)
        st["active"] = False
        xt.write_state(st, self.tmp)
        self.assertEqual(run_main("loop", "init")[0], 0)  # vòng đã kết thúc
        xt.write_state(
            {"active": "yes", "iterations": "x"}, self.tmp
        )  # sai kiểu: không đọc được → ghi đè (review #119)
        self.assertEqual(run_main("loop", "init")[0], 0)

    def test_defer_requires_state_and_valid_id(self):
        rc, out, err = run_main("loop", "defer", "--task", "T-001", "--reason", "r")
        self.assertEqual((rc, out), (2, ""))
        self.assertIn("Chưa có vòng lặp", err)
        for bad in ("T-1", "sec-auth-001", "X"):
            with self.subTest(bad), redirect_stderr(io.StringIO()) as e, self.assertRaises(SystemExit) as cm:
                xt.main(["loop", "defer", "--task", bad, "--reason", "r"])
            self.assertEqual(cm.exception.code, 2)
            self.assertIn("ID không hợp lệ", e.getvalue())

    def test_defer_status_hook_stop_and_resume_flow(self):
        # ADR-0009: việc cần người không chặn cả vòng; hết việc tự làm được → done-pending-human, phiên dừng một lần.
        self.write_plan("- [ ] `T-001` deploy — Gate: `true`\n- [x] `T-002` việc — Gate: `true`\n")
        run_main("loop", "init", "--single-session")
        rc, out, _ = run_main("loop", "defer", "--task", "T-001", "--reason", "cần khoá\nthật")
        self.assertEqual(rc, 0)
        self.assertTrue(out.startswith("⏸ T-001 chờ người: cần khoá thật — làm tiếp việc khác"))
        run_main("loop", "record", "--task", "T-002", "--", "true")
        rc, out, _ = run_main("loop", "status")
        self.assertTrue(out.startswith("verdict: done-pending-human — mọi việc tự làm được đã xong; chờ người 1 việc"))
        self.assertIn("  · chế độ một phiên: compaction tự nén", out)
        self.assertIn("  · chờ người: T-001 — cần khoá thật", out)
        data = json.loads(run_main("loop", "status", "--json")[1])
        self.assertEqual((data["single_session"], list(data["deferred"])), (True, ["T-001"]))
        rc, out, _ = run_main("loop", "hook-stop", stdin="{}")
        st = xt.read_state(self.tmp)
        self.assertEqual((rc, out, st["active"], st["final_verdict"]["verdict"]), (0, "", False, "done-pending-human"))
        self.assertIn("đã kết thúc — done-pending-human", run_main("loop", "status")[1])
        rc, out, _ = run_main("loop", "resume", "--reason", "đã cấu hình khoá")
        self.assertEqual(rc, 0)
        self.assertIn("việc chờ người quay lại hàng làm: T-001", out)
        self.assertNotIn("deferred", xt.read_state(self.tmp))
        self.assertTrue(run_main("loop", "status")[1].startswith("verdict: continue — làm task T-001"))
        rc, out, _ = run_main("loop", "resume")
        self.assertNotIn("quay lại hàng làm", out)

    def test_hook_stop_records_permission_mode_and_warns(self):
        self.write_plan()
        run_main("loop", "init", "--single-session")
        _, out, _ = run_main("loop", "hook-stop", stdin='{"permission_mode": "default"}')
        reason = json.loads(out)["reason"]
        self.assertIn("⚠ Phiên ở chế độ hỏi quyền `default`", reason)
        self.assertIn("Chế độ một phiên: context đầy thì để compaction tự nén", reason)
        self.assertIn("loop defer --task <ID>", reason)
        self.assertEqual(xt.read_state(self.tmp)["permission_mode"], "default")
        self.assertIn("⚠ Phiên ở chế độ hỏi quyền", run_main("loop", "status")[1])
        for payload in ('{"permission_mode": "auto"}', "rác {", "[1]", '{"permission_mode": 3}'):
            with self.subTest(payload):
                reason = json.loads(run_main("loop", "hook-stop", stdin=payload)[1])["reason"]
                self.assertNotIn("⚠", reason)
        self.assertEqual(xt.read_state(self.tmp)["permission_mode"], "auto")
        run_main("loop", "init", "--force")
        reason = json.loads(run_main("loop", "hook-stop", stdin="{}")[1])["reason"]
        self.assertNotIn("Chế độ một phiên", reason)

    def test_checkpoint_without_state_is_noop(self):
        rc, out, err = run_main("loop", "checkpoint", stdin='{"trigger": "auto"}')
        self.assertEqual((rc, out, err), (0, "", ""))
        self.assertFalse((self.tmp / ".autopilot").exists())

    def test_checkpoint_records_position_for_session_start(self):
        self.write_plan("- [x] `T-001` a — Gate: `true`\n- [ ] `T-002` b — Gate: `false`\n")
        run_main("loop", "init", "--single-session")
        run_main("loop", "record", "--task", "T-001", "--", "true")
        run_main("loop", "record", "--task", "T-002", "--", "false")
        subprocess.run(["git", "init", "-q", str(self.tmp)], check=True)
        rc, out, _ = run_main("loop", "checkpoint", stdin='{"trigger": "auto", "permission_mode": "acceptEdits"}')
        cp = xt.read_state(self.tmp)["checkpoint"]
        self.assertEqual((rc, out), (0, ""))
        self.assertEqual((cp["trigger"], cp["task"], cp["verdict"]), ("auto", "T-002", "continue"))
        self.assertEqual((cp["last_evidence"]["task"], cp["last_evidence"]["exit_code"]), ("T-002", 1))
        self.assertEqual((cp["same_failure_count"], cp["last_failure_task"]), (1, "T-002"))
        self.assertIn("docs/", cp["dirty"])
        self.assertEqual(xt.read_state(self.tmp)["permission_mode"], "acceptEdits")
        status = run_main("loop", "status")[1]
        self.assertIn("(auto): đang ở T-002; lệnh kiểm cuối T-002 `false` exit 1; file chưa commit: ", status)
        self.assertIn("lỗi lặp 1 lần (T-002)", status)

    def test_checkpoint_without_git_or_evidence_and_bad_payload(self):
        self.write_plan()
        run_main("loop", "init")
        rc, _, _ = run_main("loop", "checkpoint", stdin="rác")
        cp = xt.read_state(self.tmp)["checkpoint"]
        self.assertEqual((rc, cp["trigger"], cp["dirty"], cp["last_evidence"]), (0, "?", [], None))
        self.assertNotIn("permission_mode", xt.read_state(self.tmp))
        self.assertIn(
            "(?): đang ở T-001; lệnh kiểm cuối — `` exit —; file chưa commit: không; lỗi lặp 0 lần (—)",
            run_main("loop", "status")[1],
        )

    def test_checkpoint_exception_and_tty_are_fail_open(self):
        # PreCompact exit ≠ 0/“block” sẽ chặn compaction → lỗi phải nuốt, luôn exit 0.
        with unittest.mock.patch.object(xt, "loop_checkpoint", side_effect=RuntimeError("boom")):
            rc, out, err = run_main("loop", "checkpoint", stdin="{}")
        self.assertEqual((rc, out), (0, ""))
        self.assertIn("[xt checkpoint] lỗi, bỏ qua: RuntimeError: boom", err)
        fake = unittest.mock.Mock()
        fake.isatty.return_value = True
        with unittest.mock.patch.object(sys, "stdin", fake), unittest.mock.patch.object(xt, "loop_checkpoint") as lc:
            self.assertEqual(xt.main(["loop", "checkpoint"]), 0)
        lc.assert_called_once_with("", self.tmp)
        fake.read.assert_not_called()

    def test_defer_rejects_empty_reason_unknown_id_and_failing_task(self):
        # Review ADR-0009: defer gõ nhầm/không lý do/né bế tắc máy phải bị từ chối, không lưu lặng lẽ.
        self.write_plan("- [ ] `T-001` a — Gate: `false`\n- [ ] `T-002` b — Gate: `true`\n")
        run_main("loop", "init", "--single-session")
        cases = {
            "lý do rỗng": (["--task", "T-002", "--reason", " \n"], "--reason rỗng"),
            "ID không mở": (["--task", "T-999", "--reason", "r"], "ID không phải task `[ ]`"),
        }
        for name, (argv, msg) in cases.items():
            with self.subTest(name):
                rc, out, err = run_main("loop", "defer", *argv)
                self.assertEqual((rc, out), (2, ""))
                self.assertIn(msg, err)
        run_main("loop", "record", "--task", "T-001", "--", "false")
        rc, _, err = run_main("loop", "defer", "--task", "T-001", "--reason", "khó quá")
        self.assertEqual(rc, 2)
        self.assertIn("task đang lỗi", err)
        self.assertNotIn("deferred", xt.read_state(self.tmp))
        rc, _, _ = run_main("loop", "defer", "--task", "T-002", "--reason", "cần khoá thật")
        self.assertEqual(rc, 0)
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            xt.main(["loop", "defer", "--task", "T-001\n", "--reason", "r"])

    def test_defer_skips_id_check_when_plan_missing(self):
        xt.write_state({"active": True, "plan": "khong-co.md"}, self.tmp)
        rc, _, _ = run_main("loop", "defer", "--task", "SEC-AUTH-001", "--reason", "người duyệt")
        self.assertEqual((rc, list(xt.read_state(self.tmp)["deferred"])), (0, ["SEC-AUTH-001"]))

    def test_decide_choice_prefers_literal_and_ascii_index(self):
        base = ["loop", "decide", "--question", "q", "--option", "2", "--option", "1", "--why", "w", "--revert", "r"]
        rc, out, _ = run_main(*base, "--choice", "1")
        self.assertEqual((rc, out.split(" →")[0]), (0, "✓ D-001 tự duyệt: 1"))
        rc, _, err = run_main(*base, "--choice", "²")
        self.assertEqual(rc, 2)
        self.assertIn("--choice phải là", err)

    def test_decide_log_must_stay_inside_project(self):
        (self.tmp / "docs").mkdir()
        for log in ("../thoat.md", "/tmp/tuyet-doi.md", "docs"):
            with self.subTest(log):
                rc, out, err = self.decide("--revert", "r", "--log", log)
                self.assertEqual((rc, out), (2, ""))
                self.assertIn("--log phải là file trong dự án", err)
        self.assertFalse((self.tmp.parent / "thoat.md").exists())

    def test_checkpoint_git_quirks_and_evidence_fallback(self):
        self.write_plan()
        run_main("loop", "init")
        subprocess.run(["git", "init", "-q", str(self.tmp)], check=True)
        (self.tmp / "é.txt").write_text("x", encoding="utf-8")
        run_main("loop", "checkpoint", stdin="{}")
        cp = xt.read_state(self.tmp)["checkpoint"]
        self.assertIn("é.txt", cp["dirty"])  # core.quotePath=false
        self.assertIsNone(cp["head"])  # repo chưa commit: không ghi "HEAD"
        with unittest.mock.patch.object(xt, "_git", side_effect=OSError("không có git")):
            run_main("loop", "checkpoint", stdin="{}")
        self.assertEqual(xt.read_state(self.tmp)["checkpoint"]["dirty"], [])
        ev = self.tmp / ".autopilot" / "evidence"
        run_main("loop", "record", "--task", "BASE-SEC-001", "--", "true")
        (ev / "T-009.json").write_text("hỏng", encoding="utf-8")
        os.utime(ev / "T-009.json", (time.time() + 60, time.time() + 60))
        self.assertEqual(xt._evidence_latest(self.tmp)["task"], "BASE-SEC-001")

    def test_stale_checkpoint_hidden_after_newer_evidence(self):
        self.write_plan()
        run_main("loop", "init")
        st = xt.read_state(self.tmp)
        st["checkpoint"] = {"at": "2000-01-01T00:00:00+00:00", "trigger": "auto", "task": "T-001"}
        xt.write_state(st, self.tmp)
        self.assertIn("checkpoint trước nén", run_main("loop", "status")[1])
        run_main("loop", "record", "--task", "T-001", "--", "true")
        self.assertNotIn("checkpoint trước nén", run_main("loop", "status")[1])

    def test_single_session_iterations_ignore_open_blueprint_must(self):
        self.write_plan()
        (self.tmp / "BP.md").write_text(
            "".join(f"- [ ] `AAA-00{i}` **MUST** m → Kiểm: t\n" for i in range(1, 8)), encoding="utf-8"
        )
        self.write_plan("".join(f"- [ ] `T-00{i}` việc — Gate: `true`\n" for i in range(1, 7)))
        run_main("loop", "init", "--single-session", "--blueprint", "BP.md")
        # ADR-0012: chỉ tính task — MUST đã gom vào task, cộng thêm là đếm hai lần (M ≈ 480 MUST → ~2000 vòng)
        self.assertEqual(xt.read_state(self.tmp)["max_iterations"], 48)

    def test_stop_after_pending_human_reports_stopped(self):
        self.write_plan()
        run_main("loop", "init")
        st = xt.read_state(self.tmp)
        st["final_verdict"] = {"verdict": "done-pending-human", "reason": "chờ"}
        xt.write_state(st, self.tmp)
        run_main("loop", "stop", "--reason", "người tắt")
        self.assertIn("đã kết thúc — stopped: người tắt", run_main("loop", "status")[1])

    def test_resume_without_state_is_exit_2(self):
        rc, out, err = run_main("loop", "resume")
        self.assertEqual((rc, out), (2, ""))
        self.assertIn("Chưa có vòng lặp", err)

    def test_stop_without_state_is_noop(self):
        rc, out, _ = run_main("loop", "stop")
        self.assertEqual((rc, out), (0, "■ Autopilot tắt.\n"))
        self.assertIsNone(xt.read_state(self.tmp))

    def test_stop_with_state_deactivates(self):
        self.write_plan()
        run_main("loop", "init")
        rc, out, _ = run_main("loop", "stop", "--reason", "xong việc")
        st = xt.read_state(self.tmp)
        self.assertEqual((rc, out), (0, "■ Autopilot tắt.\n"))
        self.assertFalse(st["active"])
        self.assertEqual(st["stop_reason"], "xong việc")
        self.assertIn("ended", st)
        self.assertEqual(xt.loop_verdict(self.tmp)["verdict"], "inactive")

    def test_hook_stop_blocks_with_json_when_work_remains(self):
        self.write_plan()
        run_main("loop", "init")
        rc, out, err = run_main("loop", "hook-stop", stdin="{}")
        self.assertEqual((rc, err), (0, ""))
        decision = json.loads(out)
        self.assertEqual(decision["decision"], "block")
        self.assertIn("autopilot vòng 1/100", decision["reason"])
        self.assertEqual(xt.read_state(self.tmp)["iterations"], 1)

    def test_hook_stop_allows_stop_when_inactive(self):
        rc, out, err = run_main("loop", "hook-stop", stdin="{}")
        self.assertEqual((rc, out, err), (0, "", ""))

    def test_hook_stop_without_piped_stdin_uses_tty_branch(self):
        fake = unittest.mock.Mock()
        fake.isatty.return_value = True
        fake.read.side_effect = AssertionError("không được đọc stdin khi là tty")
        with unittest.mock.patch.object(sys, "stdin", fake), redirect_stdout(io.StringIO()) as out:
            rc = xt.main(["loop", "hook-stop"])
        self.assertEqual((rc, out.getvalue()), (0, ""))
        fake.read.assert_not_called()  # fail-open nuốt mọi exception nên phải kiểm trực tiếp

    def test_hook_stop_exception_is_fail_open(self):
        with unittest.mock.patch.object(xt, "hook_stop", side_effect=RuntimeError("boom")):
            rc, out, err = run_main("loop", "hook-stop", stdin="{}")
        self.assertEqual((rc, out), (0, ""))
        self.assertIn("[xt hook-stop] lỗi, cho dừng: RuntimeError: boom", err)

    def test_hook_stop_exception_logs_stacktrace_and_cause(self):
        # BASE-ERR-009 / AUD-HAR-014: lỗi bọc lỗi → stderr có stacktrace và nguyên nhân gốc.
        def boom(*_a: object) -> None:
            try:
                raise KeyError("nguyen-nhan-goc")
            except KeyError as root:
                raise ValueError("loi-boc") from root

        with unittest.mock.patch.object(xt, "hook_stop", side_effect=boom):
            rc, out, err = run_main("loop", "hook-stop", stdin="{}")
        self.assertEqual((rc, out), (0, ""))
        self.assertIn("Traceback (most recent call last)", err)
        self.assertIn("nguyen-nhan-goc", err)
        self.assertIn("ValueError: loi-boc", err)

    def test_hook_stop_propagates_exit_code(self):
        with unittest.mock.patch.object(xt, "hook_stop", return_value=("", 3)):
            rc, out, _ = run_main("loop", "hook-stop", stdin="")
        self.assertEqual((rc, out), (3, ""))

    def test_unknown_loop_subcommand_returns_2(self):
        import argparse

        self.assertEqual(xt.cmd_loop(argparse.Namespace(loop_cmd="khong-co")), 2)


# --------------------------------------------------------------------------- audit CLI


class AuditPlanCliTest(TmpRepoCase):
    def setUp(self):
        super().setUp()
        self.enterContext(unittest.mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(self.tmp)}))

    def point_at(self, root: Path) -> None:
        os.environ["CLAUDE_PROJECT_DIR"] = str(root)

    def test_text_report_with_stale_evidence_and_rescan(self):
        self.init_repo()
        self.point_at(self.repo)
        bp = "- [x] `A-001` **MUST** a → Kiểm: x — Bằng chứng: main.py:1 chạy được\n"
        c1 = self.commit_files({"main.py": "1", "BLUEPRINT.md": bp}, 1_700_000_000)
        groups = {1: ("đã quét", c1, "2026-10-14", "")}
        self.commit_files({"docs/ops/AUDIT-STATUS.md": audit_status_text(groups)}, 1_700_000_050)
        self.commit_files({"main.py": "2"}, 1_700_000_100)
        head = self.git("rev-parse", "HEAD")
        rc, out, err = run_main("audit", "plan")
        self.assertEqual((rc, err), (0, ""))
        self.assertIn(f"Audit plan — {self.repo} @ {head[:12]}", out)
        self.assertIn("mã: python 1", out)
        self.assertIn("harness: BLUEPRINT.md", out)
        self.assertNotIn("REPO KHUNG", out)
        self.assertRegex(out, r"\n   1 ARCH  áp dụng  python 1  \[có: [^\]]* · thiếu: [^\]]*\]\n")
        self.assertIn("Bằng chứng/miễn trừ blueprint trỏ file đã đổi sau khi ghi (1)", out)
        self.assertRegex(out, r"  A-001 +Bằng chứng +← main\.py")
        self.assertIn("Quét lại theo AUDIT-STATUS:\n", out)
        self.assertIn(f"1 file đổi từ `{c1[:7]}` (vd main.py)", out)
        self.assertTrue(out.rstrip().endswith("framework/00-method/audit.md"))

    def test_stale_list_is_truncated_at_25(self):
        self.init_repo()
        self.point_at(self.repo)
        self.commit_files({"a.py": "1"}, 1_700_000_000)
        real = xt.audit_plan

        def fake(*a, **k):
            plan = real(*a, **k)
            plan["stale_evidence"] = [{"id": f"A-{i:03d}", "kind": "Miễn", "files": ["a.py"]} for i in range(1, 28)]
            return plan

        with unittest.mock.patch.object(xt, "audit_plan", side_effect=fake):
            rc, out, _ = run_main("audit", "plan")
        self.assertEqual(rc, 0)
        self.assertIn("(27) — xác minh lại", out)
        self.assertIn("A-025", out)
        self.assertNotIn("A-026", out)
        self.assertIn("… và 2 mục nữa (--json để xem hết)", out)

    def test_non_git_framework_repo_with_clean_status(self):
        root = self.tmp / "proj"
        for rel in ("framework/00-method/conventions.md", "scripts/xt.py", "AGENTS.md", ".claude/settings.json"):
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("x", encoding="utf-8")
        status = root / "docs" / "ops" / "AUDIT-STATUS.md"
        status.parent.mkdir(parents=True)
        status.write_text(audit_status_text(), encoding="utf-8")  # mọi nhóm N/A → không nhóm nào cần quét lại
        self.point_at(root)
        rc, out, _ = run_main("audit", "plan")
        self.assertEqual(rc, 0)
        self.assertIn("@ không có git", out)
        self.assertIn("· REPO KHUNG", out)
        self.assertIn("harness: AGENTS.md, .claude/", out)
        self.assertIn("Quét lại theo AUDIT-STATUS: không nhóm nào đổi", out)
        self.assertNotIn("Bằng chứng/miễn trừ blueprint", out)

    def test_explicit_blueprint_and_missing_status(self):
        root = self.tmp / "proj"
        root.mkdir()
        (root / "main.py").write_text("x", encoding="utf-8")
        self.point_at(root)
        rc, out, _ = run_main("audit", "plan", "--blueprint", root / "khong-co.md", "--status", root / "khong-co-S.md")
        self.assertEqual(rc, 0)
        self.assertNotIn("Quét lại theo AUDIT-STATUS", out)
        self.assertNotIn("Bằng chứng/miễn trừ blueprint", out)
        self.assertIn("mã: python 1", out)

    def test_json_output_still_works(self):
        root = self.tmp / "proj"
        root.mkdir()
        self.point_at(root)
        rc, out, _ = run_main("audit", "plan", "--json")
        data = json.loads(out)
        self.assertEqual((rc, data["head"], data["rescan"], len(data["groups"])), (0, None, None, 13))


class AuditCheckCliTest(TmpDirCase):
    def test_summary_lines(self):
        f = self.tmp / "S.md"
        f.write_text(audit_status_text(), encoding="utf-8")
        rc, out, _ = run_main("audit", "check", f)
        self.assertEqual((rc, out), (0, f"✓ {f}: nhóm N/A 13\n"))
        f.write_text("# trống\n", encoding="utf-8")
        rc, out, _ = run_main("audit", "check", f, "--strict")
        self.assertEqual(rc, 1)
        self.assertIn(f"✗ {f}: thiếu bảng `## Nhóm`", out)
        self.assertTrue(out.rstrip().endswith(f"✗ {f}: trống (--strict)"))


# --------------------------------------------------------------------------- version / main


class VersionAndMainTest(TmpDirCase):
    def test_framework_version_unknown_without_file(self):
        scripts = self.tmp / "scripts"
        scripts.mkdir()
        with unittest.mock.patch.object(xt, "SCRIPT_DIR", scripts):
            self.assertEqual(xt.framework_version(), "unknown")
            (self.tmp / "VERSION").write_text(" 1.2.3\n", encoding="utf-8")
            self.assertEqual(xt.framework_version(), "1.2.3")

    def test_oserror_is_one_line_unless_debug(self):
        missing = self.tmp / "khong-co.md"
        with unittest.mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("XT_DEBUG", None)
            rc, out, err = run_main("progress-check", missing)
        self.assertEqual((rc, out), (2, ""))
        self.assertTrue(err.startswith("✗ "))
        self.assertEqual(len(err.splitlines()), 1)

    def test_oserror_reraised_with_xt_debug(self):
        missing = self.tmp / "khong-co.md"
        with unittest.mock.patch.dict(os.environ, {"XT_DEBUG": "1"}):
            with self.assertRaises(OSError):
                run_main("progress-check", missing)

    def test_no_subcommand_is_usage_error(self):
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as cm:
            xt.main([])
        self.assertEqual(cm.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
