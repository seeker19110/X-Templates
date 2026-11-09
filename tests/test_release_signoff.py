"""ADR-0074: `release_signoff: agent` — agent ký §5 GO-NO-GO (chủ repo 2026-11-08 "cho agent ký GO-NO-GO", D-401). Khoá
có hiệu lực khi CẢ xt.yaml ở cây làm việc LẪN bản đã commit ở nhánh chính khai; `release-sign` chỉ ký khi
`release-check` không FAIL, việc người còn lại chỉ là chữ ký, dòng `subject:` khớp, và ô tên luôn là `agent`."""

import datetime as dt
import json
import os
import subprocess
import sys
import unittest
import unittest.mock
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / ".claude" / "hooks"))
sys.path.insert(0, str(Path(__file__).resolve().parent))  # test_xt_cli
import guard
import xt
from test_xt import audit_status_text
from test_xt_cli import TmpRepoCase, run_main

HEX = "a" * 64
SUBJECT = {"head": "b" * 40, "tree": None, "digest": None, "content": HEX}
GO_DOC = (
    "# GO/NO-GO — X · phát hành v1.2.0 · 2026-11-08\n\n"
    f"subject: content {HEX}\n\n"
    "## 4. Kết luận\n\nGO.\n\n"
    "## 5. Ký (con người, không phải agent)\n\n"
    "| Vai trò | Tên | Quyết định | Ngày |\n|---|---|---|---|\n| Chủ repo | | GO / NO-GO | |\n\n"
    "## 6. Phụ lục\n\nx\n"
)
GIT_ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@x", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@x"}


def git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, env={**os.environ, **GIT_ENV})


def rc(fails=(), human=("go_no_go",), subject=None, promotion="pending_human"):
    return {
        "fails": list(fails),
        "human": list(human),
        "subject": subject or SUBJECT,
        "head": "c" * 40,
        "promotion": {"state": promotion, "reasons": []},
    }


def refusal_doc(version="1.2.0", decision="NO-GO"):
    today = dt.datetime.now(dt.timezone.utc).date().isoformat()
    return (
        f"# GO/NO-GO — X · phát hành v{version}\n\n## 5. Ký\n\n"
        f"| Vai trò | Tên | Quyết định | Ngày |\n|---|---|---|---|\n| Chủ repo | An | {decision} | {today} |\n"
    )


class SignoffRepo(TmpRepoCase):
    """Repo tạm có remote `origin` và GO-NO-GO v1.2.0 chưa ký ở docs/ops của dự án `proj` — gốc repo, hay thư mục con
    `SUB` (monorepo, D-404)."""

    SUB = ""

    def setUp(self):
        super().setUp()
        self.init_repo()
        self.proj = self.repo / self.SUB
        self.origin = self.tmp / "origin.git"
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(self.origin)], check=True)
        self.git("remote", "add", "origin", str(self.origin))
        self.doc = self.proj / "docs/ops/GO-NO-GO-2026-11-08-v1.2.0.md"
        self.doc.parent.mkdir(parents=True)
        (self.proj / "VERSION").write_text("1.2.0\n", encoding="utf-8")
        self.doc.write_text(GO_DOC, encoding="utf-8")
        self.blueprint("S")
        self.set_key("agent")
        self.enterContext(unittest.mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(self.proj)}))

    def blueprint(self, scale):
        (self.proj / "BLUEPRINT.md").write_text(
            f"---\ntitle: B\nkind: blueprint\nscale: {scale}\n---\n\n# B\n", "utf-8"
        )

    def set_key(self, value, commit=True, push=True):
        (self.proj / "xt.yaml").write_text(f"lint: ''\nrelease_signoff: {value}\n", encoding="utf-8")
        if commit:
            self.git("add", "-A")
            self.git("commit", "-q", "-m", f"release_signoff {value}")
        if push:
            self.git("push", "-q", "origin", "main")


class ReleaseSignoffKeyTest(SignoffRepo):
    def test_key_needs_tree_and_committed_on_main(self):
        self.assertTrue(xt.release_agent_signoff(self.repo))
        self.set_key("human", commit=False, push=False)  # cây làm việc rút lại → không
        self.assertFalse(xt.release_agent_signoff(self.repo))
        self.set_key("agent", commit=False, push=False)
        self.assertTrue(xt.release_agent_signoff(self.repo))
        self.set_key(
            "human", push=False
        )  # commit cục bộ mà nhánh chính của remote vẫn `agent` → cây không khai → không
        self.assertFalse(xt.release_agent_signoff(self.repo))
        self.set_key(
            "agent", commit=False, push=False
        )  # cây khai, remote vẫn agent nhưng HEAD commit human → vẫn agent
        self.assertTrue(xt.release_agent_signoff(self.repo))
        self.git("push", "-q", "origin", "main")  # nhánh chính nay `human`
        self.assertFalse(xt.release_agent_signoff(self.repo))
        self.git("remote", "remove", "origin")  # không có remote → chỉ người
        self.assertFalse(xt.release_agent_signoff(self.repo))
        with unittest.mock.patch.object(xt, "_xt_keys", side_effect=OSError("x")):
            self.assertFalse(xt.release_agent_signoff(self.repo))

    def test_key_is_hard_gated(self):
        self.assertIn("release_signoff", xt.HARD_GATED_KEYS)
        self.assertIn("`release_signoff`", xt.HARD_KEY_REASON)
        self.assertEqual(xt._hard_key_lines("release_signoff: agent\n"), ["release_signoff=agent"])


class ReleaseSignTest(SignoffRepo):
    def sign(self, result=None, file="", note="máy đạt: release-check GO, review sạch"):
        return xt.release_sign(self.repo, file, note, result or rc())

    def refused(self, msg, **kw):
        with self.assertRaises(xt.ReleaseSignError) as ctx:
            self.sign(**kw)
        self.assertIn(msg, str(ctx.exception))
        self.assertEqual(self.doc.read_text(encoding="utf-8"), GO_DOC)  # từ chối không ghi file

    def test_signs_with_agent_name_and_promotion_approves(self):
        rel = self.sign()
        self.assertEqual(rel, "docs/ops/GO-NO-GO-2026-11-08-v1.2.0.md")
        text = self.doc.read_text(encoding="utf-8")
        today = dt.datetime.now(dt.timezone.utc).date().isoformat()
        row = f"| Agent (`release_signoff`, ADR-0074) | agent | GO | {today} |"
        self.assertIn(row + "\n\n> Agent ký", text)
        self.assertIn("máy đạt: release-check GO, review sạch", text)
        self.assertLess(text.index(row), text.index("## 6."))  # dòng ký nằm trong §5
        self.assertEqual(xt._go_signers(text), ["agent"])
        with unittest.mock.patch.object(xt, "_signed_go_no_go", return_value=[(rel, text)]):
            promo = xt._release_promotion(self.repo, [], [], SUBJECT)
        self.assertEqual((promo["state"], promo["by"]), ("approved", ["agent"]))

    def test_refusals_leave_file_untouched(self):
        self.set_key("human")
        self.refused("chỉ người ký")
        self.set_key("agent")
        self.refused("release-check NO-GO (FAIL tree, audit)", result=rc(fails=("tree", "audit")))
        self.refused("còn việc người ngoài chữ ký: prod_switch", result=rc(human=("go_no_go", "prod_switch")))
        self.refused("`--note` rỗng", note=" | \n ")
        self.refused("chữ ký gắn ứng viên khác", result=rc(subject={**SUBJECT, "content": "d" * 64}))
        self.refused("cần đúng một GO-NO-GO của v1.2.0", file="docs/ops/khac.md")

    def test_refuses_when_promotion_rejected(self):
        """Review #480 🔴: một GO-NO-GO khác của VERSION có dòng NO-GO của người → agent không ký đè ở file còn trống."""
        self.refused("người đã từ chối", result=rc(promotion="rejected"))

    def test_history_unreadable_fails_closed(self):
        """D-404: không đọc được lịch sử git (`git log` lỗi/quá thời gian) → từ chối — có thể giấu lời từ chối."""
        real = xt._git

        def log_fails(cwd, *args, **kw):
            if "log" in args:
                return subprocess.CompletedProcess(args, 128, "", "fatal: hỏng")
            return real(cwd, *args, **kw)

        with unittest.mock.patch.object(xt, "_git", side_effect=log_fails):
            self.refused("không đọc được lịch sử git")

    def test_promotion_counts_agent_row_only_with_key(self):
        """Review #480 🟠: dòng ký ô tên `agent` chỉ là duyệt khi khoá `release_signoff: agent` có hiệu lực."""
        rel = self.sign()
        text = self.doc.read_text(encoding="utf-8")
        self.set_key("human")
        for name in ("agent", "Agent"):
            with unittest.mock.patch.object(
                xt, "_signed_go_no_go", return_value=[(rel, text.replace("| agent |", f"| {name} |"))]
            ):
                promo = xt._release_promotion(self.repo, [], [], SUBJECT)
            self.assertEqual(promo["state"], "pending_human", name)
            self.assertIn("`release_signoff: agent` chưa có hiệu lực", promo["reasons"][0])
        self.set_key("agent")
        with unittest.mock.patch.object(xt, "_signed_go_no_go", return_value=[(rel, text)]):
            self.assertEqual(xt._release_promotion(self.repo, [], [], SUBJECT)["state"], "approved")

    def test_scope_scale_s_and_no_deferred(self):
        self.blueprint("M")
        self.refused("agent chỉ ký quy mô S")
        (self.repo / "BLUEPRINT.md").write_text("---\nscale: [S\n---\n", encoding="utf-8")
        with unittest.mock.patch.object(xt, "parse_frontmatter", side_effect=ValueError("hỏng")):
            self.refused("không đọc được BLUEPRINT.md")
        (self.repo / "BLUEPRINT.md").unlink()
        self.refused("không đọc được BLUEPRINT.md")
        self.blueprint("S")
        state = self.repo / ".autopilot" / "state.json"
        state.parent.mkdir()
        state.write_text('{"deferred": {"T-9": {"reason": "tiền thật"}}}', encoding="utf-8")
        self.refused("còn việc chờ người (`loop defer`): T-9")
        state.write_text('{"deferred": {}}', encoding="utf-8")
        self.assertEqual(self.sign(), "docs/ops/GO-NO-GO-2026-11-08-v1.2.0.md")

    def test_document_selection(self):
        other = self.repo / "GO-NO-GO-v1.2.0.md"
        other.write_text(GO_DOC, encoding="utf-8")
        self.refused("thấy: docs/ops/GO-NO-GO-2026-11-08-v1.2.0.md, GO-NO-GO-v1.2.0.md")
        self.assertEqual(self.sign(file="GO-NO-GO-v1.2.0.md"), "GO-NO-GO-v1.2.0.md")
        (self.repo / "VERSION").unlink()
        self.refused("không đọc được VERSION/GO-NO-GO")

    def test_already_signed_or_refused(self):
        for cell in ("| Chủ repo | chu | GO | 2026-11-08 |", "| Chủ repo | chu | NO-GO | 2026-11-08 |"):
            signed = GO_DOC.replace("| Chủ repo | | GO / NO-GO | |", cell)
            self.doc.write_text(signed, encoding="utf-8")
            with self.assertRaises(xt.ReleaseSignError) as ctx:
                self.sign()
            self.assertIn("đã có dòng ký hoặc lời từ chối", str(ctx.exception))
            self.assertEqual(self.doc.read_text(encoding="utf-8"), signed)

    def test_section_five_shape(self):
        for text, msg in (
            (GO_DOC.replace("## 5. Ký", "## 5x Ký"), "không có mục `## 5`"),
            (
                GO_DOC.replace(
                    "| Vai trò | Tên | Quyết định | Ngày |\n|---|---|---|---|\n| Chủ repo | | GO / NO-GO | |\n", ""
                ),
                "§5 không có bảng ký",
            ),
        ):
            self.doc.write_text(text, encoding="utf-8")
            with self.assertRaises(xt.ReleaseSignError) as ctx:
                self.sign()
            self.assertIn(msg, str(ctx.exception))
        last = GO_DOC.split("## 6.")[0].rstrip() + "\n"  # §5 là mục cuối: chèn tới hết file
        self.doc.write_text(last, encoding="utf-8")
        self.sign()
        self.assertTrue(self.doc.read_text(encoding="utf-8").rstrip().endswith("review sạch"))

    def test_row_hidden_in_code_block_is_reverted(self):
        fenced = GO_DOC.replace("| Vai trò |", "```\n| Vai trò |").replace(
            "| Chủ repo | | GO / NO-GO | |\n", "| Chủ repo | | GO / NO-GO | |\n"
        )
        fenced = fenced.replace("| Chủ repo | | GO / NO-GO | |\n\n", "| Chủ repo | | GO / NO-GO | |\n```\n\n")
        self.doc.write_text(fenced, encoding="utf-8")
        with unittest.mock.patch.object(
            xt, "_sign_insert", side_effect=lambda t, r, n: t.replace("```\n\n", r + "\n```\n\n" + n, 1)
        ):
            with self.assertRaises(xt.ReleaseSignError) as ctx:
                self.sign()
        self.assertIn("đã hoàn tác", str(ctx.exception))
        self.assertEqual(self.doc.read_text(encoding="utf-8"), fenced)


class ReleaseSignCliTest(SignoffRepo):
    def test_cli_exit_codes_and_check_hint(self):
        with unittest.mock.patch.object(xt, "release_check", return_value=rc(fails=("tree",))):
            code, _, err = run_main("release-sign", "--note", "x")
        self.assertEqual(code, 2)
        self.assertIn("NO-GO", err)
        with unittest.mock.patch.object(xt, "release_check", return_value=rc()) as check:
            code, out, _ = run_main("release-sign", "--note", "máy đạt")
        self.assertEqual(code, 0)
        self.assertIn("agent ký §5 docs/ops/GO-NO-GO-2026-11-08-v1.2.0.md", out)
        # review #480: MUST tick không lệnh kiểm là FAIL khi agent ký (không phải ⚠)
        check.assert_called_once_with(self.repo, "BLUEPRINT.md", "docs/ops/AUDIT-STATUS.md", unchecked_must="fail")

    def test_release_check_hint_follows_key(self):
        full = {
            **rc(),
            "rows": [],
            "verdict": "GO (chờ người)",
            "go": True,
            "promotion": {"state": "pending_human", "reasons": ["go_no_go"]},
        }
        with unittest.mock.patch.object(xt, "release_check", return_value=full):
            _, out, _ = run_main("release-check")
            self.assertIn("agent ký được bằng `xt.py release-sign", out)
            self.set_key("human")
            _, out, _ = run_main("release-check")
            self.assertIn("máy không thay được chữ ký", out)


class RealCheckRepo(SignoffRepo):
    """Dự án đủ để `release-check` thật ra GO; GO-NO-GO B (`doc`) chưa ký, dòng `subject:` của cây đã commit."""

    BP = "---\ntitle: B\nkind: blueprint\nupdated: 2026-10-19\nscale: S\nprofile: cli-tool\n---\n\n## Checklist\n\n"
    MUST_OK = "- [x] `BASE-X-001` **MUST** a — Kiểm: `true`\n"
    REFUSED = "docs/ops/GO-NO-GO-A-v1.2.0.md"
    BRANCH = "claude/rel-1.2.0"

    def setUp(self):
        super().setUp()
        (self.proj / "docs/ops/AUDIT-STATUS.md").write_text(audit_status_text(), encoding="utf-8")
        (self.proj / ".gitignore").write_text("out/\ndist/\n", encoding="utf-8")
        self.prepare(self.MUST_OK)

    def prepare(self, checklist, doc=GO_DOC):
        """Blueprint `checklist` + GO-NO-GO B (`doc`) chưa ký có dòng `subject:` của cây đã commit."""
        (self.proj / "BLUEPRINT.md").write_text(self.BP + checklist, encoding="utf-8")
        self.doc.unlink(missing_ok=True)
        self.commit()
        self.unsigned = doc.replace(HEX, xt.subject_fingerprint(self.proj))
        self.doc.write_text(self.unsigned, encoding="utf-8")
        self.commit()

    def commit(self, push=True, at=None):
        """Commit mọi thay đổi; `push`: True → origin/main, chuỗi → nhánh đó của origin; `at`: ngày commit (epoch)."""
        self.git("add", "-A")
        env = {"GIT_COMMITTER_DATE": f"@{at} +0000", "GIT_AUTHOR_DATE": f"@{at} +0000"} if at else None
        self.git("commit", "-q", "--allow-empty", "-m", "c", env=env)
        if push:
            self.git("push", "-q", "origin", f"HEAD:{'main' if push is True else push}")

    def write(self, rel, text):
        (self.proj / rel).parent.mkdir(parents=True, exist_ok=True)
        (self.proj / rel).write_text(text, encoding="utf-8")

    def rm(self, rel):
        self.git("rm", "-q", str(self.proj / rel))

    def sign_cli(self, *extra):
        return run_main("release-sign", *extra, "--note", "máy đạt")

    def assert_signs(self, *extra):
        code, out, err = self.sign_cli(*extra)
        self.assertEqual(code, 0, err)
        self.assertIn("agent ký §5", out)

    def assert_refused(self, msg, *extra):
        code, _, err = self.sign_cli(*extra)
        self.assertEqual(code, 2, err)
        self.assertIn(msg, err)
        self.assertEqual(self.doc.read_text(encoding="utf-8"), self.unsigned)

    def assert_history_refused(self, where, *extra):
        """Bị từ chối vì lời từ chối trong lịch sử git (D-404), thông điệp nêu `where`; promotion KHÔNG `rejected`."""
        _, out, _ = run_main("release-check", "--json")
        self.assertNotEqual(json.loads(out)["promotion"]["state"], "rejected")
        self.assert_refused("người đã từ chối (lịch sử git)", *extra)
        self.assert_refused(where, *extra)


class ReleaseSignRealCheckTest(RealCheckRepo):
    """`release-sign` với `release-check` thật: các ca review #480 tái hiện (lần 1 và D-404)."""

    def test_baseline_signs(self):
        self.assert_signs()

    def test_rejected_in_tree_not_overridden(self):
        """Review #480 🔴 (a): A có NO-GO của người, B chưa ký → promotion rejected; `release-sign --file B` từ chối."""
        self.write(self.REFUSED, refusal_doc())
        self.commit(push=False)
        _, out, _ = run_main("release-check", "--json")
        d = json.loads(out)
        self.assertEqual((d["promotion"]["state"], d["fails"], d["human"]), ("rejected", [], []), d["promotion"])
        self.assert_refused("người đã từ chối", "--file", self.doc.relative_to(self.proj).as_posix())

    def test_refusal_kept_on_main_after_tree_delete(self):
        """Review #480 🔴 (b): NO-GO đã lên nhánh chính, `git rm` ở nhánh làm việc → vẫn từ chối (D-404: đọc lịch sử;
        thông điệp đổi từ `ở nhánh chính: origin/main:…` sang `(lịch sử git)`)."""
        self.write(self.REFUSED, refusal_doc())
        self.commit()
        self.rm(self.REFUSED)
        self.commit(push=False)
        self.assert_history_refused(self.REFUSED)

    def test_refusal_on_pr_branch_deleted(self):
        """D-404 🔴: NO-GO của người chỉ ở nhánh PR (đã đẩy), agent `git rm` rồi ký → vẫn từ chối."""
        self.git("checkout", "-q", "-b", self.BRANCH)
        self.write(self.REFUSED, refusal_doc())
        self.commit(push=self.BRANCH)
        self.rm(self.REFUSED)
        self.commit(push=self.BRANCH)
        self.assert_history_refused(self.REFUSED)

    def test_refusal_deleted_on_main(self):
        """D-404 🟠: NO-GO lên nhánh chính rồi việc xoá cũng lên nhánh chính trước khi ký → vẫn từ chối."""
        self.write(self.REFUSED, refusal_doc())
        self.commit()
        self.rm(self.REFUSED)
        self.commit()
        self.assert_history_refused(self.REFUSED)

    def test_refusal_cell_not_go(self):
        """D-404 🟠: ô quyết định không phải GO cũng không phải `no` (`Không GO`) là lời từ chối."""
        self.write(self.REFUSED, refusal_doc(decision="Không GO"))
        self.commit()
        self.assert_history_refused(
            "`| Chủ repo | An | Không GO |", "--file", self.doc.relative_to(self.proj).as_posix()
        )

    def test_refusal_undated_row_in_target(self):
        """D-404 🟠: dòng NO-GO của người thiếu ngày/ngày không ISO/thiếu tên ngay trong B → agent không ký dưới nó."""
        for row in ("| Chủ repo | An | NO-GO | |", "| Chủ repo | An | NO-GO | 9/11/2026 |", "| Chủ repo | | NO-GO | |"):
            with self.subTest(row=row):
                self.prepare(self.MUST_OK, GO_DOC.replace("| Chủ repo | | GO / NO-GO | |", row))
                self.assert_history_refused(f"`{row}`")

    def test_refusal_survives_version_bump(self):
        """D-404 🟠: NO-GO cho v1.2.0, agent đổi VERSION sang 1.2.1 và lập GO-NO-GO v1.2.1 → vẫn từ chối."""
        self.write(self.REFUSED, refusal_doc())
        self.commit()
        self.rm(self.REFUSED)
        self.write("VERSION", "1.2.1\n")
        self.doc.unlink()
        self.doc = self.proj / "docs/ops/GO-NO-GO-2026-11-09-v1.2.1.md"
        self.prepare(self.MUST_OK, GO_DOC.replace("v1.2.0", "v1.2.1"))
        self.assert_history_refused(self.REFUSED)

    def test_refusal_superseded_by_later_human_go(self):
        """D-404: lời từ chối hết hiệu lực khi commit SAU nó thêm dòng ký GO của người (§5, tên + ngày) → ký được."""
        now = int(dt.datetime.now(dt.timezone.utc).timestamp())
        self.write(self.REFUSED, refusal_doc())
        self.commit(at=now - 200)
        self.write("docs/ops/GO-NO-GO-v1.1.0.md", refusal_doc("1.1.0", decision="GO"))
        self.commit(at=now - 100)
        self.rm(self.REFUSED)
        self.commit(push=False)
        self.assert_signs()

    def test_refusal_expired_after_approval_days(self):
        """D-404: lời từ chối cũ hơn `release_approval_days` (theo ngày commit) hết hiệu lực → ký được."""
        old = int((dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=31)).timestamp())
        self.write(self.REFUSED, refusal_doc())
        self.commit(at=old)
        self.rm(self.REFUSED)
        self.commit(push=False)
        self.assert_signs()

    def test_unchecked_must_blocks_sign(self):
        """Review #480 🟠: MUST tick không `— Kiểm:` → `release-sign` từ chối (release-check `--unchecked-must fail`)."""
        self.prepare(self.MUST_OK + "- [x] `BASE-X-002` **MUST** b\n")
        self.assert_refused("FAIL unchecked_must")


class ReleaseSignSubdirTest(RealCheckRepo):
    """D-404 🔴: dự án ở thư mục con của repo (monorepo `apps/web`) — quét không phụ thuộc thư mục dự án."""

    SUB = "apps/web"

    def test_baseline_signs(self):
        self.assert_signs()

    def test_refusal_on_main_deleted_in_tree(self):
        self.write(self.REFUSED, refusal_doc())
        self.commit()
        self.rm(self.REFUSED)
        self.commit(push=False)
        self.assert_history_refused(f"apps/web/{self.REFUSED}")


def ago(days=0, seconds=0):
    return int((dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days, seconds=seconds)).timestamp())


def table(*rows, head="| Vai trò | Tên | Quyết định | Ngày |\n|---|---|---|---|\n"):
    return head + "".join(r + "\n" for r in rows)


def sign_doc(*rows, before=""):
    return f"# GO/NO-GO — X\n\n{before}## 5. Ký\n\n" + table(*rows) + "\n## 6. Phụ lục\n\nx\n"


class GoHistoryTest(TmpRepoCase):
    """`_history_go_refusals` (D-404): quét dòng thêm của mọi `GO-NO-GO*.md` trong `git log --all`."""

    def setUp(self):
        super().setUp()
        self.init_repo()

    def refusals(self, base=None):
        return xt._history_go_refusals(base or self.repo)

    def test_empty_repo_and_not_a_repo(self):
        self.assertEqual(self.refusals(), [])
        with self.assertRaises(xt.ReleaseSignError) as ctx:
            self.refusals(self.tmp)
        self.assertIn("không đọc được lịch sử git", str(ctx.exception))

    def test_scope_any_dir_case_version(self):
        """Mọi thư mục, mọi độ sâu, tên không phân biệt hoa thường, mọi phiên bản; tệp tên khác không tính."""
        files = {
            "GO-NO-GO.md": "An",
            "a/b/c/go-no-go-v0.1.md": "Bình",
            "docs/ops/GO-NO-GO-v9.9.9.md": "Chi",
            "docs/NOTE-GO-NO-GO.md": "Dũng",
            "docs/GO-NO-GO.txt": "Én",
        }
        row = "| Chủ repo | {} | NO-GO | 2026-11-09 |"
        sha = self.commit_files({rel: sign_doc(row.format(who)) for rel, who in files.items()}, ago(seconds=10))
        found = self.refusals(self.repo / "a")
        self.assertEqual(
            sorted(found), sorted(f"{sha[:12]} {rel}:7 `{row.format(who)}`" for rel, who in list(files.items())[:3])
        )

    def test_row_rules(self):
        """Dòng quyết định của người: tên không rỗng/placeholder/agent (trừ ô NO-GO rõ), ô quyết định khác GO."""
        rows = (
            "| Chủ sản phẩm | | GO / NO-GO | |",  # dòng mẫu
            "| Kỹ thuật | | | |",
            "| Bảo mật | <tên> | GO / NO-GO | |",
            "| Bảo mật | — | Hold | |",
            "| Agent | agent | NO-GO | 2026-11-09 |",
            "| Agent | AGENT | ? | |",
            "| A | An | GO | 2026-11-09 |",
            "| A | An | go v1.2.0 | |",
            "| A | Bình | ? | |",
            "| A | Chi | Hold | 2026-11-09 |",
            "| A | Dũng | Chưa duyệt | |",
            "| A | | Từ chối | |",
            "  | A | Én | **GO** | |",
            "| A | Phú |",
        )
        before = (
            "## 1. Đếm\n\n| Mức | PASS | FAIL | N/A |\n|---|---|---|---|\n| BLOCKER | 12 | 0 | 3 |\n\n"
            "## 2. Khác\n\n| Quyết định | Tên |\n|---|---|\n| Hoãn | Giang |\n\n"
        )
        self.commit_files({"GO-NO-GO.md": sign_doc(*rows, before=before)}, ago(seconds=10))
        text = "\n".join(self.refusals())
        for who in ("Bình", "Chi", "Dũng", "| A | | Từ chối |", "Én", "Giang"):
            self.assertIn(who, text)
        for who in ("Chủ sản phẩm", "Kỹ thuật", "<tên>", "—", "agent", "AGENT", "| An |", "Phú", "BLOCKER", "Mức"):
            self.assertNotIn(who, text)

    def test_lone_row_without_header_counts(self):
        """Dòng bảng không có tiêu đề + kẻ (không thành bảng khi hiển thị) vẫn là lời từ chối."""
        self.commit_files({"GO-NO-GO.md": "## 5. Ký\n\n| Chủ repo | An | NO-GO |\n"}, ago(seconds=10))
        self.assertIn("| Chủ repo | An | NO-GO |", "\n".join(self.refusals()))

    def test_template_has_no_refusal(self):
        """Mẫu GO-NO-GO của khung (dòng tiêu đề/kẻ/dòng trống) không tự tạo lời từ chối, ở gốc lẫn thư mục con."""
        tpl = (ROOT / "framework/templates/GO-NO-GO.md").read_text(encoding="utf-8")
        self.commit_files({"GO-NO-GO.md": tpl, "apps/web/docs/ops/GO-NO-GO-v1.0.0.md": tpl}, ago(seconds=10))
        self.assertEqual(self.refusals(), [])

    def test_supersede_needs_new_signed_human_go_in_section_five(self):
        """Chỉ dòng ký GO của người ở §5 (tên + ngày, khớp `GO_SIGN_ROW_RE` — guard chặn agent ghi), XUẤT HIỆN LẦN ĐẦU
        sau lời từ chối, mới gỡ nó. GO thiếu ngày, ngoài §5, của agent, hay chép lại dòng GO cũ thì không."""
        old_go = "| Chủ repo | An | GO | 2026-10-01 |"
        self.commit_files({"GO-NO-GO-old.md": sign_doc(old_go)}, ago(days=5))
        self.commit_files({"GO-NO-GO-a.md": sign_doc("| Chủ repo | An | NO-GO | 2026-11-01 |")}, ago(days=4))
        not_enough = (
            sign_doc("| Chủ repo | An | GO | |"),
            sign_doc("| Agent | agent | GO | 2026-11-08 |"),
            "# x\n\n## 4. Kết luận\n\n" + table("| Chủ repo | Bình | GO | 2026-11-08 |") + "\n## 5. Ký\n\nx\n",
            sign_doc(old_go),
        )
        for i, text in enumerate(not_enough):
            self.commit_files({f"GO-NO-GO-{i}.md": text}, ago(days=3, seconds=-i))
            self.assertIn("NO-GO | 2026-11-01", "\n".join(self.refusals()), i)
        self.commit_files({"GO-NO-GO-new.md": sign_doc("| Chủ repo | An | GO | 2026-11-08 |")}, ago(days=2))
        self.assertEqual(self.refusals(), [])

    def test_refusal_lifetime_uses_latest_occurrence(self):
        """Lời từ chối hết hạn theo `release_approval_days`; chép lại nó (đổi tên/lưu trữ) làm mới hạn — chiều chặt."""
        no = "| Chủ repo | An | NO-GO | 2026-09-01 |"
        self.commit_files({"GO-NO-GO-a.md": sign_doc(no)}, ago(days=31))
        self.assertEqual(self.refusals(), [])
        (self.repo / "xt.yaml").write_text("release_approval_days: 60\n", encoding="utf-8")
        self.assertEqual(len(self.refusals()), 1)
        (self.repo / "xt.yaml").unlink()
        self.git("mv", "GO-NO-GO-a.md", "GO-NO-GO-archived.md")
        sha = self.commit_files({}, ago(days=1))
        self.assertIn(f"{sha[:12]} GO-NO-GO-archived.md", "\n".join(self.refusals()))

    def test_diff_parsing_edges(self):
        """Sửa (dòng `-`), xoá tệp, tệp không có xuống dòng cuối, dòng nội dung trông như tiêu đề diff."""
        no = "| Chủ repo | An | Hold | 2026-11-09 |"
        tricky = "--- a/x\n+++ b/y\n@@ -1 +1 @@\ndiff --git a/z b/z\n"
        self.commit_files({"GO-NO-GO.md": tricky + sign_doc(no).rstrip("\n")}, ago(seconds=30))
        self.commit_files({"GO-NO-GO.md": tricky.replace("x", "w") + sign_doc(no) + "y\n"}, ago(seconds=20))
        self.git("rm", "-q", "GO-NO-GO.md")
        self.commit_files({}, ago(seconds=10))
        found = self.refusals()
        self.assertEqual(len(found), 1)
        self.assertIn("GO-NO-GO.md:11 `" + no + "`", found[0])


class ReleaseSignGuardTest(TmpRepoCase):
    """Guard: `release-sign` dạng chữ rõ một lệnh đơn chỉ qua khi khoá có hiệu lực; dạng khác → GO_SIGN."""

    PLAIN = "python3 scripts/xt.py release-sign --note ok"

    def setUp(self):
        super().setUp()
        guard._RELEASE_AGENT.clear()
        self.addCleanup(guard._RELEASE_AGENT.clear)
        self.enterContext(unittest.mock.patch.dict(os.environ, {"XT_GUARD_POLICY": "", "XT_GUARD_PHASE": ""}))

    def project(self, committed, tree=None):
        origin, proj = self.tmp / "origin.git", self.tmp / "proj"
        git(self.tmp, "init", "-q", "--bare", "-b", "main", str(origin))
        git(self.tmp, "init", "-q", "-b", "main", str(proj))
        git(proj, "remote", "add", "origin", str(origin))
        (proj / "xt.yaml").write_text(f"lint: ''\nrelease_signoff: {committed}\n", encoding="utf-8")
        git(proj, "add", "xt.yaml")
        git(proj, "commit", "-q", "-m", "init")
        git(proj, "push", "-q", "origin", "main")
        if tree is not None:
            (proj / "xt.yaml").write_text(f"release_signoff: {tree}\n", encoding="utf-8")
        return proj

    def decide(self, proj, cmd, cwd=None):
        out = dict(guard.apply_policy(guard.bash_decision(cmd, str(proj), str(cwd or proj))))
        return out.get("decision"), out.get("code")

    def test_plain_form_allowed_only_with_key(self):
        proj = self.project("agent")
        for cmd in (
            self.PLAIN,
            "python3 scripts/xt.py release-sign --file docs/ops/GO-NO-GO-2026-11-08-v1.2.0.md --note 'máy đạt'",
            f"python3 {proj}/scripts/xt.py release-sign --note=x",
            "python3 scripts/xt.py release-check --json",  # lệnh khác không bị luật này chạm
        ):
            self.assertNotEqual(self.decide(proj, cmd)[0], "deny", cmd)
        for cmd in (
            self.PLAIN + " && true",  # không phải lệnh đơn
            self.PLAIN + " --status /tmp/fake.md",  # sổ/blueprint ngoài đường mặc định làm giả release-check
            self.PLAIN + " --blueprint=/tmp/b.md",
            "env -u CLAUDECODE " + self.PLAIN,
            "python3 scripts/xt.py release-sign --note $X",  # token mờ
            "python3 scripts/xt.py release-sign --force --note x",  # tuỳ chọn lạ
            "python3 /tmp/xt.py release-sign --note x",  # xt.py ngoài dự án
            "python3 -c 'print(1)'; python3 scripts/xt.py release-sign --note x",
        ):
            self.assertEqual(self.decide(proj, cmd), ("deny", "GO_SIGN"), cmd)
        sub = proj / "docs"
        sub.mkdir()
        self.assertEqual(self.decide(proj, self.PLAIN, cwd=sub), ("deny", "GO_SIGN"))  # đường tương đối ngoài gốc

    def test_key_off_tree_only_or_strict_denies(self):
        for committed, tree in (("human", None), ("human", "agent"), ("agent", "human")):
            guard._RELEASE_AGENT.clear()
            proj = self.project(committed, tree)
            self.assertEqual(self.decide(proj, self.PLAIN), ("deny", "GO_SIGN"), (committed, tree))
            subprocess.run(["rm", "-rf", str(proj), str(self.tmp / "origin.git")], check=True)
        proj = self.project("agent")
        guard._RELEASE_AGENT.clear()
        with unittest.mock.patch.dict(os.environ, {"XT_GUARD_POLICY": "strict"}):
            self.assertEqual(self.decide(proj, self.PLAIN)[0], "deny")
        self.assertEqual(guard._release_signoff_value("release_signoff: human\nrelease_signoff: 'agent'\n"), "agent")
        self.assertEqual(guard._release_signoff_value("x: 1\n"), "")

    def test_unprotecting_main_and_inprocess_sign_denied(self):
        """Phản biện ADR-0074: đổi nhánh mặc định dời ruleset khỏi `main`; MCP ghi thẳng `main`; gọi `release_sign` trong
        tiến trình (vá được khoá/tên) — đều bị chặn."""
        proj = self.project("agent")
        for cmd in (
            "gh repo edit --default-branch dev",
            "gh repo edit o/r --default-branch=dev",
            "gh api -X PATCH repos/o/r -f default_branch=dev",
        ):
            self.assertEqual(self.decide(proj, cmd)[0], "deny", cmd)
        self.assertNotEqual(self.decide(proj, "gh api -X PATCH repos/o/r -f description=x")[0], "deny")
        for cmd in (
            "python3 -c \"import sys; sys.path.insert(0,'scripts'); from xt import release_sign; release_sign(1,2,3,4)\"",
            "python3 -c \"import sys; sys.path.insert(0,'scripts'); import xt; xt.RELEASE_AGENT_NAME='chu'\"",
        ):
            self.assertEqual(self.decide(proj, cmd)[0], "deny", cmd)
        write = "mcp__github__create_or_update_file"
        base = {"owner": "o", "repo": "r", "path": "xt.yaml", "content": "x", "message": "docs: x"}
        for branch in ("main", "master", "refs/heads/main", None):
            args = {**base, **({"branch": branch} if branch else {})}
            decision, why = guard.mcp_decision(write, args, str(proj))
            self.assertEqual(decision, "deny", branch)
            self.assertIn("push thẳng nhánh chính", why)
        self.assertNotEqual(guard.mcp_decision(write, {**base, "branch": "claude/x"}, str(proj))[0], "deny")
        self.assertNotEqual(guard.mcp_decision("mcp__github__get_me", {}, str(proj))[0], "deny")

    def test_edit_of_sign_row_still_denied(self):
        proj = self.project("agent")
        doc = proj / "docs/ops/GO-NO-GO-2026-11-08-v1.2.0.md"
        doc.parent.mkdir(parents=True)
        doc.write_text(GO_DOC, encoding="utf-8")
        reason = guard._go_sign_deny(
            str(doc),
            "docs/ops/GO-NO-GO-2026-11-08-v1.2.0.md",
            str(proj),
            {"old_string": "| Chủ repo | | GO / NO-GO | |", "new_string": "| Chủ repo | agent | GO | 2026-11-08 |"},
        )
        self.assertIn("Không ghi dòng ký §5", reason)


if __name__ == "__main__":
    unittest.main()
