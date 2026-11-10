"""ADR-0074: `release_signoff: agent` — agent ký §5 GO-NO-GO (chủ repo 2026-11-08 "cho agent ký GO-NO-GO", D-401). Khoá
có hiệu lực khi CẢ xt.yaml ở cây làm việc LẪN bản đã commit ở nhánh chính khai; `release-sign` chỉ ký khi
`release-check` không FAIL, việc người còn lại chỉ là chữ ký, dòng `subject:` khớp, và ô tên luôn là `agent`."""

import base64
import datetime as dt
import functools
import http.server
import json
import os
import subprocess
import sys
import tempfile
import threading
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
        # sổ máy của vòng `/complete` (`loop init`), không theo git như `.gitignore` dự án đích (AUD-HAR-340)
        (self.repo / ".git/info/exclude").write_text(".autopilot/\n", encoding="utf-8")
        self.state = self.proj / ".autopilot" / "state.json"
        self.state.parent.mkdir()
        self.state.write_text("{}", encoding="utf-8")
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
        self.state.write_text('{"deferred": {"T-9": {"reason": "tiền thật"}}}', encoding="utf-8")
        self.refused("còn việc chờ người (`loop defer`): T-9")
        self.state.write_text('{"deferred": {}}', encoding="utf-8")
        self.assertEqual(self.sign(), "docs/ops/GO-NO-GO-2026-11-08-v1.2.0.md")

    def worktree(self, name="wt"):
        path = self.tmp / name
        self.git("worktree", "add", "-q", "--detach", str(path))
        return path

    def test_deferred_read_from_every_worktree(self):
        """AUD-HAR-340: `.autopilot/` riêng mỗi worktree (không theo git) — ký từ worktree khác không thoát việc
        `loop defer` của cây chính, ký từ cây chính không thoát việc của worktree; không còn việc nào → ký được."""
        wt = self.worktree()
        doc = wt / self.doc.relative_to(self.repo)
        self.state.write_text('{"deferred": {"T-9": {"reason": "tiền thật"}}}', encoding="utf-8")
        with self.assertRaises(xt.ReleaseSignError) as ctx:
            xt.release_sign(wt, "", "máy đạt", rc())
        self.assertIn("còn việc chờ người (`loop defer`): T-9", str(ctx.exception))
        self.assertEqual(doc.read_text(encoding="utf-8"), GO_DOC)
        self.state.write_text('{"deferred": {}}', encoding="utf-8")
        (wt / ".autopilot").mkdir()
        (wt / ".autopilot/state.json").write_text('{"deferred": {"T-8": {"reason": "khoá thật"}}}', "utf-8")
        self.refused("còn việc chờ người (`loop defer`): T-8")
        (wt / ".autopilot/state.json").write_text('{"deferred": {}}', "utf-8")
        self.assertEqual(xt.release_sign(wt, "", "máy đạt", rc()), "docs/ops/GO-NO-GO-2026-11-08-v1.2.0.md")
        self.assertIn("| agent | GO |", doc.read_text(encoding="utf-8"))
        self.assertEqual(self.doc.read_text(encoding="utf-8"), GO_DOC)

    def test_unknown_or_broken_state_refuses(self):
        """AUD-HAR-340 fail-closed: không có sổ máy ở worktree nào (clone riêng, chưa `loop init`), sổ hỏng hay không
        liệt kê được worktree → không biết còn `loop defer` → từ chối."""
        clone = self.tmp / "clone"
        subprocess.run(["git", "clone", "-q", str(self.repo), str(clone)], check=True)
        with self.assertRaises(xt.ReleaseSignError) as ctx:
            xt._sign_scope_check(clone)
        self.assertIn("không thấy `.autopilot/state.json`", str(ctx.exception))
        self.state.unlink()
        self.refused("không thấy `.autopilot/state.json`")
        for text, msg in (
            ("{hỏng", "không đọc được"),
            ("[]", "state không phải object"),
            ('{"deferred": ["T-9"]}', "`deferred` không phải object"),
            ('{"deferred": null}', "`deferred` không phải object"),
        ):
            with self.subTest(text=text):
                self.state.write_text(text, encoding="utf-8")
                self.refused(msg)
        self.state.unlink()
        self.state.mkdir()
        self.refused("không đọc được")
        self.state.rmdir()
        self.state.symlink_to(self.tmp / "vắng.json")
        self.refused("không đọc được")
        self.state.unlink()
        self.state.write_text("{}", encoding="utf-8")
        real = xt._git
        for cmd in ("worktree", "rev-parse"):
            with self.subTest(cmd=cmd):

                def fails(cwd, *args, cmd=cmd, **kw):
                    if args[0] == cmd:
                        return subprocess.CompletedProcess(args, 128, "", "fatal: hỏng")
                    return real(cwd, *args, **kw)

                with unittest.mock.patch.object(xt, "_git", side_effect=fails):
                    self.refused("không liệt kê được worktree")
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

    def push_key_from_other_clone(self, text):
        """Chủ repo đổi xt.yaml của dự án trên remote từ bản clone khác (`None` = xoá); repo cục bộ KHÔNG fetch
        (`origin/main` cục bộ cũ — AUD-SEC-552)."""
        other = self.tmp / "owner"
        subprocess.run(["git", "clone", "-q", str(self.origin), str(other)], check=True, capture_output=True)
        target = other / self.SUB / "xt.yaml"
        if text is None:
            git(other, "rm", "-q", str(target))
        else:
            target.write_text(text, encoding="utf-8")
            git(other, "add", "-A")
        git(other, "commit", "-q", "-m", "owner: release_signoff")
        git(other, "push", "-q", "origin", "main")


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
        """D-404/D-406: lời từ chối hết hiệu lực khi commit SAU nó (trên origin) thêm dòng ký GO của người (§5, tên +
        ngày) ở tệp cùng phiên bản hay cao hơn → ký được."""
        self.write(self.REFUSED, refusal_doc())
        self.commit(at=ago(seconds=200))
        self.write("docs/ops/GO-NO-GO-v1.3.0.md", refusal_doc("1.3.0", decision="GO"))
        self.commit(at=ago(seconds=100))
        self.rm(self.REFUSED)
        self.commit(push=False)
        self.assert_signs()

    def test_lower_version_go_does_not_lift(self):
        """D-406 🟠: dòng GO người ở GO-NO-GO phiên bản thấp hơn không gỡ NO-GO của v1.2.0 (trước: gỡ toàn cục)."""
        self.write(self.REFUSED, refusal_doc())
        self.commit(at=ago(seconds=200))
        self.write("docs/ops/GO-NO-GO-v1.1.0.md", refusal_doc("1.1.0", decision="GO"))
        self.commit(at=ago(seconds=100))
        self.rm(self.REFUSED)
        self.commit(push=False)
        self.assert_history_refused(self.REFUSED)

    def test_free_form_go_and_appendix_table_not_refusal(self):
        """D-406 🟠 chặn oan: ô GO viết tự do (`**GO**; D-126…`) là GO; bảng §6 không cột `Quyết định` không đọc."""
        go = refusal_doc("1.1.0", decision="**GO**; D-126: giữ tự host")
        go += "\n## 6. Phụ lục\n\n| Rủi ro | Người | Trạng thái |\n|---|---|---|\n| Mạng | An | Hold |\n"
        self.write("docs/ops/GO-NO-GO-v1.1.0.md", go)
        self.commit()
        self.assert_signs()

    def test_merge_ours_does_not_hide_refusal(self):
        """D-406 🔴: `git merge -s ours` nhánh có NO-GO rồi xoá nhánh — giản lược lịch sử của `git log -- <pathspec>`
        giấu commit đó; `--full-history` thấy (cả mirror lẫn cục bộ)."""
        self.git("checkout", "-q", "-b", self.BRANCH)
        self.write(self.REFUSED, refusal_doc())
        self.commit(push=False)
        self.git("checkout", "-q", "main")
        self.git("merge", "-q", "-s", "ours", "-m", "m", self.BRANCH)
        self.git("branch", "-q", "-D", self.BRANCH)
        self.git("push", "-q", "origin", "main")
        self.assert_history_refused(self.REFUSED)

    def test_remote_ref_deleted_locally_still_seen(self):
        """D-406 🔴: NO-GO đã đẩy lên nhánh PR của origin, agent `branch -D` + `branch -rd origin/<nhánh>` → mirror thấy."""
        self.git("checkout", "-q", "-b", self.BRANCH)
        self.write(self.REFUSED, refusal_doc())
        self.commit(push=self.BRANCH)
        self.git("checkout", "-q", "main")
        self.git("branch", "-q", "-D", self.BRANCH)
        self.git("branch", "-q", "-rd", f"origin/{self.BRANCH}")
        self.assert_history_refused(self.REFUSED)

    def test_pull_ref_survives_branch_delete(self):
        """D-406 🔴: `push --delete` nhánh NO-GO + `fetch --prune` — origin còn `refs/pull/1/head` (GitHub giữ) → thấy."""
        self.git("checkout", "-q", "-b", self.BRANCH)
        self.write(self.REFUSED, refusal_doc())
        self.commit(push=self.BRANCH)
        self.git("push", "-q", "origin", "HEAD:refs/pull/1/head")
        self.git("checkout", "-q", "main")
        self.git("branch", "-q", "-D", self.BRANCH)
        self.git("push", "-q", "origin", "--delete", self.BRANCH)
        self.git("fetch", "-q", "--prune", "origin")
        self.assert_history_refused(self.REFUSED)

    def test_shallow_fetch_refused(self):
        """D-406 🔴: `git fetch --depth=1 origin main` làm repo nông → không ký (lịch sử trước tip biến mất)."""
        self.write(self.REFUSED, refusal_doc())
        self.commit()
        self.rm(self.REFUSED)
        self.commit()
        self.git("fetch", "-q", "--depth=1", "origin", "main")
        self.assert_refused("clone nông (shallow)")

    def test_external_repo_go_does_not_lift(self):
        """D-406 🔴: GO người của repo ngoài `fetch` vào cục bộ (`refs/heads/x`) không gỡ NO-GO đã lên origin."""
        self.write(self.REFUSED, refusal_doc())
        self.commit(at=ago(seconds=200))
        self.rm(self.REFUSED)
        self.commit()
        ext = self.tmp / "ext"
        ext.mkdir()
        git(ext, "init", "-q", "-b", "main")
        (ext / "GO-NO-GO-v9.0.0.md").write_text(refusal_doc("9.0.0", decision="GO"), encoding="utf-8")
        git(ext, "add", "-A")
        git(ext, "commit", "-q", "-m", "go")
        self.git("fetch", "-q", str(ext), "main:refs/heads/x")
        self.assert_history_refused(self.REFUSED)

    def test_refusal_does_not_expire_by_age(self):
        """D-405: lời từ chối cũ hơn mọi hạn (400 ngày) vẫn chặn ký khi chưa có dòng GO người sau nó."""
        self.write(self.REFUSED, refusal_doc())
        self.commit(at=ago(days=400))
        self.rm(self.REFUSED)
        self.commit(push=False)
        self.assert_history_refused(self.REFUSED)

    def test_short_approval_days_does_not_lift_refusal(self):
        """D-405: agent đặt `release_approval_days: 1` ở xt.yaml cây (đã commit) → lời từ chối 2 ngày tuổi vẫn chặn."""
        self.write(self.REFUSED, refusal_doc())
        self.commit(at=ago(days=2))
        self.rm(self.REFUSED)
        self.write("xt.yaml", "lint: ''\nrelease_signoff: agent\nrelease_approval_days: 1\n")
        self.prepare(self.MUST_OK)  # dòng `subject:` của B theo cây mới
        self.assertEqual(xt._approval_days(self.proj), 1)
        self.assert_history_refused(self.REFUSED)

    def test_unchecked_must_blocks_sign(self):
        """Review #480 🟠: MUST tick không `— Kiểm:` → `release-sign` từ chối (release-check `--unchecked-must fail`)."""
        self.prepare(self.MUST_OK + "- [x] `BASE-X-002` **MUST** b\n")
        self.assert_refused("FAIL unchecked_must")

    def test_remote_key_off_refused_with_stale_tracking_ref(self):
        """AUD-SEC-552 (D-407): chủ repo tắt khoá trên remote; `origin/main` cục bộ chưa fetch còn `agent` → khoá cục bộ
        vẫn coi là bật nhưng `release-sign` đọc khoá ở HEAD của bản mirror vừa clone → từ chối."""
        self.push_key_from_other_clone("lint: ''\nrelease_signoff: human\n")
        self.assertTrue(xt.release_agent_signoff(self.proj))  # góc nhìn cục bộ cũ: bật
        self.assert_refused("chưa bật trên remote")
        self.assert_refused("`human`")

    def test_remote_key_missing_refused(self):
        """Mirror không có xt.yaml của dự án ở nhánh mặc định → từ chối (fail-closed)."""
        self.push_key_from_other_clone(None)
        self.assert_refused("chưa bật trên remote")


class ReleaseSignSubdirTest(RealCheckRepo):
    """D-404 🔴: dự án ở thư mục con của repo (monorepo `apps/web`) — quét không phụ thuộc thư mục dự án."""

    SUB = "apps/web"

    def test_baseline_signs(self):
        self.assert_signs()

    def test_deferred_at_project_subdir_of_main_worktree(self):
        """AUD-HAR-340: sổ máy của dự án ở thư mục con — worktree khác đọc `apps/web/.autopilot/` của cây chính."""
        wt = self.tmp / "wt"
        self.git("worktree", "add", "-q", "--detach", str(wt))
        self.state.write_text('{"deferred": {"T-7": {"reason": "người dùng thử"}}}', encoding="utf-8")
        with self.assertRaises(xt.ReleaseSignError) as ctx:
            xt._sign_scope_check(wt / self.SUB)
        self.assertIn("`loop defer`): T-7", str(ctx.exception))

    def test_refusal_on_main_deleted_in_tree(self):
        self.write(self.REFUSED, refusal_doc())
        self.commit()
        self.rm(self.REFUSED)
        self.commit(push=False)
        self.assert_history_refused(f"apps/web/{self.REFUSED}")

    def test_remote_key_read_at_project_path(self):
        """AUD-SEC-552: khoá trên mirror đọc ở `apps/web/xt.yaml` (đường tương đối gốc repo) — xt.yaml gốc repo khai
        `agent` không thay được khoá của dự án."""
        self.write("../../xt.yaml", "release_signoff: agent\n")
        self.commit()
        self.push_key_from_other_clone("lint: ''\nrelease_signoff: human\n")
        self.assert_refused("chưa bật trên remote")


def ago(days=0, seconds=0):
    return int((dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days, seconds=seconds)).timestamp())


def table(*rows, head="| Vai trò | Tên | Quyết định | Ngày |\n|---|---|---|---|\n"):
    return head + "".join(r + "\n" for r in rows)


def sign_doc(*rows, before="", title="# GO/NO-GO — X", after="x\n"):
    return f"{title}\n\n{before}## 5. Ký\n\n" + table(*rows) + "\n## 6. Phụ lục\n\n" + after


def bare(path):
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(path)], check=True)
    return path


class GoHistoryTest(TmpRepoCase):
    """`_go_remote_scan(...).refusals` (D-404, D-406): dòng thêm của mọi `GO-NO-GO*.md` trong `git log --all
    --full-history` của bản mirror mới của `origin` và của repo cục bộ."""

    def setUp(self):
        super().setUp()
        self.init_repo()
        self.origin = bare(self.tmp / "origin.git")
        self.git("remote", "add", "origin", str(self.origin))

    def refusals(self, base=None, publish=True):
        if publish:
            self.git("push", "-q", "--mirror", "origin")
        return xt._go_remote_scan(base or self.repo).refusals

    def refused(self, msg, base=None):
        with self.assertRaises(xt.ReleaseSignError) as ctx:
            xt._go_remote_scan(base or self.repo)
        self.assertIn("không đọc được lịch sử git", str(ctx.exception))
        self.assertIn(msg, str(ctx.exception))

    def other_clone(self, name="other"):
        """Bản clone khác của origin (người khác đẩy lên) — repo cục bộ không fetch."""
        path = self.tmp / name
        subprocess.run(["git", "clone", "-q", str(self.origin), str(path)], check=True, capture_output=True)
        return path

    def test_empty_repo_and_not_a_repo(self):
        self.assertEqual(self.refusals(publish=False), [])
        self.refused("repo cục bộ: exit", self.tmp)

    def test_no_origin_or_clone_error_fails_closed(self):
        """D-406: không có `origin`, clone lỗi (đường/mạng/xác thực) → từ chối."""
        self.commit_files({"x.md": "x"}, ago(seconds=10))
        self.git("remote", "set-url", "origin", str(self.tmp / "khong-co.git"))
        self.refused("clone --mirror origin lỗi")
        self.git("remote", "remove", "origin")
        self.refused("không có remote `origin`")

    def test_shallow_local_fails_closed(self):
        """D-406 🔴: `git fetch --depth=1` làm repo cục bộ nông — lịch sử trước tip biến mất → từ chối."""
        for at in (30, 20, 10):
            self.commit_files({"x.md": str(at)}, ago(seconds=at))
        self.git("push", "-q", "origin", "main")
        self.git("fetch", "-q", "--depth=1", "origin", "main")
        self.refused("repo cục bộ là clone nông", self.repo)

    def test_isolated_git_env_and_unfetched_remote(self):
        """D-406: lời từ chối người khác đẩy lên origin mà repo cục bộ chưa fetch (ref theo dõi cũ, AUD-SEC-548) vẫn thấy;
        `url.*.insteadOf` tiêm qua `GIT_CONFIG_*`/`GIT_CONFIG_GLOBAL` không đổi được đích clone."""
        self.commit_files({"x.md": "x"}, ago(seconds=30))
        self.git("push", "-q", "origin", "main")
        other = self.other_clone()
        (other / "GO-NO-GO-v1.0.0.md").write_text(sign_doc("| Chủ repo | An | NO-GO | 2026-11-09 |"), "utf-8")
        for args in (("add", "-A"), ("commit", "-q", "-m", "no"), ("push", "-q", "origin", "main")):
            git(other, *args)
        fake = bare(self.tmp / "fake.git")
        subprocess.run(["git", "-C", str(self.repo), "push", "-q", str(fake), "main"], check=True)
        glob_cfg = self.tmp / "gitconfig"
        glob_cfg.write_text(f'[url "{fake}"]\n\tinsteadOf = {self.origin}\n', encoding="utf-8")
        envs = (
            {},
            {
                "GIT_CONFIG_COUNT": "1",
                "GIT_CONFIG_KEY_0": f"url.{fake}.insteadOf",
                "GIT_CONFIG_VALUE_0": str(self.origin),
            },
            {"GIT_CONFIG_GLOBAL": str(glob_cfg)},
        )
        for env in envs:
            with self.subTest(env=sorted(env)), unittest.mock.patch.dict(os.environ, env):
                self.assertIn("GO-NO-GO-v1.0.0.md:7", "\n".join(xt._go_remote_scan(self.repo).refusals))

    def test_go_from_external_repo_does_not_lift(self):
        """D-406 🔴: dòng GO người của repo ngoài fetch vào cục bộ không gỡ lời từ chối — GO chỉ tính từ mirror origin."""
        self.commit_files({"GO-NO-GO-v1.0.0.md": sign_doc("| Chủ repo | An | NO-GO | 2026-11-01 |")}, ago(days=2))
        ext = self.tmp / "ext"
        ext.mkdir()
        git(ext, "init", "-q", "-b", "main")
        (ext / "GO-NO-GO-v9.0.0.md").write_text(sign_doc("| Chủ repo | Lạ | GO | 2026-11-08 |"), encoding="utf-8")
        git(ext, "add", "-A")
        git(ext, "commit", "-q", "-m", "go")
        self.git("push", "-q", "origin", "main")
        self.git("fetch", "-q", str(ext), "main:refs/heads/x")
        self.assertEqual(len(self.refusals(publish=False)), 1)
        self.git("push", "-q", "origin", "x")  # cùng dòng GO lên origin → gỡ (đối chứng)
        self.assertEqual(self.refusals(publish=False), [])

    def test_show_root_pinned(self):
        """D-406 🟠: `git config log.showRoot false` ở repo cục bộ không ẩn lời từ chối ở commit gốc chưa đẩy."""
        seed = self.tmp / "seed"
        seed.mkdir()
        git(seed, "init", "-q", "-b", "main")
        git(seed, "commit", "-q", "--allow-empty", "-m", "seed")
        git(seed, "push", "-q", str(self.origin), "main")
        self.commit_files({"GO-NO-GO-v1.0.0.md": sign_doc("| Chủ repo | An | Hold | |")}, ago(seconds=10))
        self.git("config", "log.showRoot", "false")
        self.assertEqual(len(self.refusals(publish=False)), 1)

    def test_pins_all_refs_and_full_context(self):
        """Ghim cờ: lời từ chối chỉ reachable từ ref khác HEAD (`--all`); dòng NO-GO thêm cách xa tiêu đề bảng (cần
        `--unified` tối đa để biết dòng nằm trong bảng có cột `Quyết định`)."""
        filler = [f"| Mục {i} | | | |" for i in range(40)]
        self.commit_files({"GO-NO-GO-v1.0.0.md": sign_doc(*filler)}, ago(seconds=40))
        self.git("checkout", "-q", "-b", "side")
        far = "| Chủ repo | An | NO-GO | 2026-11-09 |"
        self.commit_files({"GO-NO-GO-v1.0.0.md": sign_doc(*filler, far, after="\n" * 30 + "y\n")}, ago(seconds=30))
        self.git("checkout", "-q", "main")
        self.assertIn(f"GO-NO-GO-v1.0.0.md:47 `{far}`", "\n".join(self.refusals()))

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
        """Dòng quyết định của người: tên không rỗng/placeholder/agent (trừ ô NO-GO rõ), ô quyết định không phải GO.
        GO viết tự do (D-406) là GO; `GO / NO-GO`, `Không GO` không bao giờ là GO."""
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
            "| A | Hà | GO / NO-GO | 2026-11-09 |",
            "| A | Khánh | GO, không GO | |",
            "| A | Lan | **GO**; D-126: giữ tự host | 2026-10-26 |",
            "| A | Minh | `GO` — ok | |",
            "| A | Ngọc | Gold | |",
        )
        before = (
            "## 1. Đếm\n\n| Mức | PASS | FAIL | N/A |\n|---|---|---|---|\n| BLOCKER | 12 | 0 | 3 |\n\n"
            "## 2. Khác\n\n| Quyết định | Tên |\n|---|---|\n| Hoãn | Giang |\n\n"
            "| Decision | Name |\n|---|---|\n| Hold | Oanh |\n\n"
            "| Mục | QUYET DINH |\n|:--|--:|\n| x | NO-GO |\n| y | Hold |\n\n"
        )
        self.commit_files({"GO-NO-GO.md": sign_doc(*rows, before=before)}, ago(seconds=10))
        text = "\n".join(self.refusals())
        for who in (
            "Bình",
            "Chi",
            "Dũng",
            "| A | | Từ chối |",
            "Giang",
            "Hà",
            "Khánh",
            "Ngọc",
            "Oanh",
            "| x | NO-GO |",
        ):
            self.assertIn(who, text)
        for who in ("Chủ sản phẩm", "Kỹ thuật", "<tên>", "—", "agent", "AGENT", "| An |", "Phú", "BLOCKER", "Mức"):
            self.assertNotIn(who, text)
        for who in ("Én", "Lan", "Minh", "| y |"):
            self.assertNotIn(who, text)

    def test_tables_without_decision_column_not_read(self):
        """D-406 🟠: chỉ bảng có cột `Quyết định` — bảng §6 (sau `## 5`) không cột đó, hay dòng lẻ không tiêu đề, không
        đọc theo vị trí cột."""
        appendix = "| Rủi ro | Người | Trạng thái |\n|---|---|---|\n| Mạng | An | Hold |\n"
        lone = "| Chủ repo | Bình | NO-GO |\n"
        doc = sign_doc("| Chủ repo | | GO / NO-GO | |", after=appendix + "\n## 7. X\n\n" + lone)
        self.commit_files({"GO-NO-GO-v1.0.0.md": doc}, ago(seconds=10))
        self.assertEqual(self.refusals(), [])

    def test_template_has_no_refusal(self):
        """Mẫu GO-NO-GO của khung (dòng tiêu đề/kẻ/dòng trống) không tự tạo lời từ chối, ở gốc lẫn thư mục con."""
        tpl = (ROOT / "framework/templates/GO-NO-GO.md").read_text(encoding="utf-8")
        self.commit_files({"GO-NO-GO.md": tpl, "apps/web/docs/ops/GO-NO-GO-v1.0.0.md": tpl}, ago(seconds=10))
        self.assertEqual(self.refusals(), [])

    def test_supersede_needs_new_signed_human_go_in_section_five(self):
        """Chỉ dòng ký GO của người ở §5 (tên + ngày, khớp `GO_SIGN_ROW_RE` — guard chặn agent ghi), XUẤT HIỆN LẦN ĐẦU
        sau lời từ chối, mới gỡ nó. GO thiếu ngày, ngoài §5, của agent, hay chép lại dòng GO cũ thì không."""
        title = "# GO/NO-GO — X · phát hành v1.0.0"
        old_go = "| Chủ repo | An | GO | 2026-10-01 |"
        self.commit_files({"GO-NO-GO-old.md": sign_doc(old_go, title=title)}, ago(days=5))
        no = "| Chủ repo | An | NO-GO | 2026-11-01 |"
        self.commit_files({"GO-NO-GO-a.md": sign_doc(no, title=title)}, ago(days=4))
        not_enough = (
            sign_doc("| Chủ repo | An | GO | |", title=title),
            sign_doc("| Agent | agent | GO | 2026-11-08 |", title=title),
            f"{title}\n\n## 4. Kết luận\n\n" + table("| Chủ repo | Bình | GO | 2026-11-08 |") + "\n## 5. Ký\n\nx\n",
            sign_doc(old_go, title=title),
            sign_doc("| Chủ repo | An | GO | 2026-11-08 |", title="# GO/NO-GO — X · phát hành v0.9.9"),  # bản thấp hơn
            sign_doc("| Chủ repo | Chi | GO | 2026-11-08 |"),  # tệp không có phiên bản
        )
        for i, text in enumerate(not_enough):
            self.commit_files({f"GO-NO-GO-{i}.md": text}, ago(days=3, seconds=-i))
            self.assertIn("NO-GO | 2026-11-01", "\n".join(self.refusals()), i)
        new = sign_doc("| Chủ repo | An | GO | 2026-11-09 |", title="---\nx: 1\n---\n# GO/NO-GO — X · v1.0.1")
        self.commit_files({"GO-NO-GO-new.md": new}, ago(days=2))
        self.assertEqual(self.refusals(), [])

    def test_unversioned_refusal_lifted_only_in_same_file(self):
        """D-406: lời từ chối ở tệp không xác định phiên bản chỉ gỡ bằng dòng GO người cùng tệp (đường), commit sau."""
        self.commit_files({"GO-NO-GO.md": sign_doc("| Chủ repo | An | Hold | |")}, ago(days=4))
        v9 = sign_doc("| Chủ repo | An | GO | 2026-11-08 |")  # cùng dòng GO ở hai tệp một commit: lần đầu = cùng ngày
        self.commit_files({"GO-NO-GO-v9.0.0.md": v9, "GO-NO-GO-v9.0.1.md": v9}, ago(days=3))
        self.assertEqual(len(self.refusals()), 1)
        go = sign_doc("| Chủ repo | An | Hold | |", "| Chủ repo | An | GO | 2026-11-09 |")
        self.commit_files({"GO-NO-GO.md": go}, ago(days=2))
        self.assertEqual(self.refusals(), [])

    def test_refusal_no_expiry_latest_occurrence(self):
        """D-405: không hết hạn theo tuổi, `release_approval_days` không xét; GO người sau gỡ; chép lại lời từ chối
        (đổi tên/lưu trữ) SAU dòng GO đó làm nó có hiệu lực lại — tính ở lần thêm mới nhất (chiều chặt)."""
        no = "| Chủ repo | An | NO-GO | 2025-01-01 |"
        self.commit_files({"GO-NO-GO-a-v1.0.0.md": sign_doc(no)}, ago(days=400))
        (self.repo / "xt.yaml").write_text("release_approval_days: 1\n", encoding="utf-8")
        self.assertEqual(len(self.refusals()), 1)
        go = sign_doc("| Chủ repo | An | GO | 2025-02-01 |")
        self.commit_files({"GO-NO-GO-b-v1.0.0.md": go}, ago(days=300))
        self.assertEqual(self.refusals(), [])
        self.git("mv", "GO-NO-GO-a-v1.0.0.md", "GO-NO-GO-archived-v1.0.0.md")
        sha = self.commit_files({}, ago(days=1))
        self.assertIn(f"{sha[:12]} GO-NO-GO-archived-v1.0.0.md", "\n".join(self.refusals()))

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


class _BasicAuthHandler(http.server.SimpleHTTPRequestHandler):
    """Máy chủ git HTTP "dumb" (tệp tĩnh của repo trần sau `update-server-info`) đòi Basic auth `u:p` — như remote
    HTTPS riêng tư: không có credential helper thì git (`GIT_TERMINAL_PROMPT=0`) không clone được."""

    TOKEN = "Basic " + base64.b64encode(b"u:p").decode()

    def do_GET(self):
        if self.headers.get("Authorization") != self.TOKEN:
            self.send_response(401)
            self.send_header("WWW-Authenticate", 'Basic realm="x"')
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        super().do_GET()

    def log_message(self, *args):
        pass


class GoMirrorCredentialTest(TmpRepoCase):
    """AUD-SEC-553 (D-407): clone mirror của `release-sign` giữ RIÊNG `credential.helper` global của người dùng (chung và
    `credential.<url>.helper`) — remote HTTP cần xác thực clone được; cấu hình global khác (`url.*.insteadOf`) vẫn cô lập.
    Chạy thật: máy chủ HTTP cục bộ + helper giả là script ghi lại lệnh được gọi."""

    def setUp(self):
        super().setUp()
        self.init_repo()
        self.commit_files({"x.md": "x"}, ago(seconds=10))
        srv = self.tmp / "srv"
        srv.mkdir()
        bare(srv / "origin.git")
        self.git("push", "-q", str(srv / "origin.git"), "main")
        subprocess.run(["git", "-C", str(srv / "origin.git"), "update-server-info"], check=True)
        server = http.server.ThreadingHTTPServer(
            ("127.0.0.1", 0), functools.partial(_BasicAuthHandler, directory=str(srv))
        )
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        self.base_url = f"http://127.0.0.1:{server.server_address[1]}"
        self.url = f"{self.base_url}/origin.git"
        self.git("remote", "add", "origin", self.url)
        self.log = self.tmp / "helper.log"
        self.helper = self.tmp / "helper.sh"
        self.helper.write_text(
            f'#!/bin/sh\necho "$1" >> "{self.log}"\n[ "$1" = get ] && printf "username=u\\npassword=p\\n"\nexit 0\n',
            encoding="utf-8",
        )
        self.helper.chmod(0o755)
        self.home = self.tmp / "home"
        self.home.mkdir()
        self.cfg = self.home / ".gitconfig"  # tệp global thật của người dùng: `$HOME/.gitconfig` (AUD-SEC-559)
        no_proxy = {"NO_PROXY": "127.0.0.1,localhost", "no_proxy": "127.0.0.1,localhost"}
        clean = {k: v for k, v in os.environ.items() if not k.startswith("GIT_") and k != "XDG_CONFIG_HOME"}
        self.enterContext(
            unittest.mock.patch.dict(os.environ, {**clean, **no_proxy, "HOME": str(self.home)}, clear=True)
        )

    def clone(self):
        with tempfile.TemporaryDirectory() as tmp:
            mirror = xt._go_origin_mirror(self.repo, Path(tmp))
            return subprocess.run(
                ["git", "-C", str(mirror), "rev-parse", "HEAD"], capture_output=True, text=True, check=True
            ).stdout.strip()

    def test_global_helper_used_by_clone(self):
        """Đỏ trước sửa: `GIT_CONFIG_GLOBAL=/dev/null` làm mất helper → `could not read Username` → clone lỗi."""
        fake = self.tmp / "khong-co.git"
        self.cfg.write_text(
            f'[credential]\n\thelper = {self.helper}\n[url "{fake}"]\n\tinsteadOf = {self.url}\n', encoding="utf-8"
        )
        self.assertEqual(self.clone(), self.git("rev-parse", "HEAD").strip())
        self.assertIn("get", self.log.read_text(encoding="utf-8").split())

    def test_url_scoped_helper_used_by_clone(self):
        self.cfg.write_text(f'[credential "{self.base_url}"]\n\thelper = {self.helper}\n', encoding="utf-8")
        self.assertEqual(self.clone(), self.git("rev-parse", "HEAD").strip())
        self.assertIn("get", self.log.read_text(encoding="utf-8").split())

    def test_no_helper_still_fails_closed(self):
        self.cfg.write_text("[user]\n\tname = x\n", encoding="utf-8")
        with self.assertRaises(ValueError) as ctx:
            self.clone()
        self.assertIn("clone --mirror origin lỗi", str(ctx.exception))
        self.assertFalse(self.log.exists())

    def test_credential_args_order_and_isolation(self):
        """Thứ tự giữ như cấu hình (giá trị rỗng = xoá danh sách); khoá khác `credential.*helper` không truyền."""
        self.cfg.write_text(
            "[credential]\n\thelper = a\n\thelper =\n\tusername = x\n\thelper = b c\n"
            f'[credential "{self.base_url}"]\n\thelper = d\n[credential]\n\thelperx = y\n[log]\n\tshowRoot = false\n',
            encoding="utf-8",
        )
        self.assertEqual(
            xt._go_credential_args(self.repo),
            [
                *("-c", "credential.helper="),
                *("-c", "credential.helper=a", "-c", "credential.helper=", "-c", "credential.helper=b c"),
                *("-c", f"credential.{self.base_url}.helper=d"),
            ],
        )
        self.cfg.write_text("", encoding="utf-8")
        self.assertEqual(xt._go_credential_args(self.repo), ["-c", "credential.helper="])
        self.cfg.unlink()
        self.assertEqual(xt._go_credential_args(self.repo), ["-c", "credential.helper="])

    def foreign(self, name: str) -> Path:
        """Tệp cấu hình lạ (agent tạo được) khai helper ghi lại lệnh."""
        path = self.tmp / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"[credential]\n\thelper = {self.helper}\n", encoding="utf-8")
        return path

    def test_foreign_global_config_not_trusted(self):
        """AUD-SEC-559 (review #485): `GIT_CONFIG_GLOBAL`/`XDG_CONFIG_HOME` do agent export trỏ tệp lạ → helper trong đó
        KHÔNG vào clone (từng chạy `op=get/store` trong thư mục tạm của clone); helper ở tệp global thật (`$HOME/.gitconfig`,
        `$HOME/.config/git/config`) vẫn vào. Đỏ trước sửa: đọc `git config --global` với môi trường gốc."""
        foreign = self.foreign("lạ/gc")
        self.foreign("xdg/git/config")
        env = {"GIT_CONFIG_GLOBAL": str(foreign), "XDG_CONFIG_HOME": str(self.tmp / "xdg"), "GIT_CONFIG_NOSYSTEM": "1"}
        with unittest.mock.patch.dict(os.environ, env):
            self.assertEqual(xt._go_credential_args(self.repo), ["-c", "credential.helper="])
            with self.assertRaises(ValueError) as ctx:  # không helper thật: clone fail-closed, helper lạ không chạy
                self.clone()
            self.assertIn("clone --mirror origin lỗi", str(ctx.exception))
            self.assertFalse(self.log.exists())
            xdg_real = self.home / ".config/git/config"  # `--global` đọc tệp này khi không có `~/.gitconfig`
            xdg_real.parent.mkdir(parents=True)
            xdg_real.write_text("[credential]\n\thelper = real-xdg\n", encoding="utf-8")
            reset = ["-c", "credential.helper="]
            self.assertEqual(xt._go_credential_args(self.repo), [*reset, "-c", "credential.helper=real-xdg"])
            self.cfg.write_text("[credential]\n\thelper = real\n", encoding="utf-8")
            want = [*reset, "-c", "credential.helper=real"]
            self.assertEqual(xt._go_credential_args(self.repo), want)
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
                got = list(pool.map(lambda _: xt._go_credential_args(self.repo), range(8)))
            self.assertEqual(got, [want] * 8)

    def test_askpass_not_kept_for_clone(self):
        """AUD-SEC-559: `GIT_ASKPASS` do agent export là chương trình chạy trong clone như helper lạ — không giữ;
        CA tin cậy (`GIT_SSL_CAINFO`) vẫn giữ. Đỏ trước sửa: askpass trả `u`/`p` → clone thành công."""
        askpass = self.tmp / "askpass.sh"
        askpass.write_text(
            f'#!/bin/sh\necho "$1" >> "{self.log}"\ncase "$1" in U*) echo u;; *) echo p;; esac\n', encoding="utf-8"
        )
        askpass.chmod(0o755)
        self.cfg.write_text("[user]\n\tname = x\n", encoding="utf-8")
        with unittest.mock.patch.dict(os.environ, {"GIT_ASKPASS": str(askpass), "GIT_SSL_CAINFO": "/ca.pem"}):
            env = xt._go_git_env()
            self.assertNotIn("GIT_ASKPASS", env.keys())  # khi đỏ chỉ in tên biến, không in giá trị môi trường
            self.assertEqual(env["GIT_SSL_CAINFO"], "/ca.pem")
            with self.assertRaises(ValueError):
                self.clone()
        self.assertFalse(self.log.exists())

    def test_helper_key_with_equals_skipped(self):
        """AUD-HAR-350: khoá `credential.<url>.helper` có `=` (URL `?a=b`) git không parse được qua `-c` (exit 128 → clone
        lỗi) — bỏ qua; helper khác vẫn vào và clone được."""
        self.cfg.write_text(
            f'[credential "{self.base_url}/?a=b"]\n\thelper = x\n[credential]\n\thelper = {self.helper}\n',
            encoding="utf-8",
        )
        self.assertEqual(
            xt._go_credential_args(self.repo), ["-c", "credential.helper=", "-c", f"credential.helper={self.helper}"]
        )
        self.assertEqual(self.clone(), self.git("rev-parse", "HEAD").strip())

    def test_helper_not_passed_to_log(self):
        """Helper chỉ đi vào lệnh clone: `git log` ở mirror/cục bộ chạy với môi trường cô lập, không `-c` helper."""
        self.cfg.write_text(f"[credential]\n\thelper = {self.helper}\n", encoding="utf-8")
        calls = []
        real = xt._git

        def spy(cwd, *args, **kw):
            calls.append(args)
            return real(cwd, *args, **kw)

        with unittest.mock.patch.object(xt, "_git", side_effect=spy):
            self.assertEqual(xt._go_remote_scan(self.repo).refusals, [])
        with_helper = [a for a in calls if f"credential.helper={self.helper}" in a]
        self.assertEqual(len(with_helper), 1, with_helper)
        self.assertIn("clone", with_helper[0])
        self.assertTrue(any("log" in a for a in calls))


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
