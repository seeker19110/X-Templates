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
    """Repo tạm có remote `origin` và GO-NO-GO v1.2.0 chưa ký ở docs/ops."""

    def setUp(self):
        super().setUp()
        self.init_repo()
        self.origin = self.tmp / "origin.git"
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(self.origin)], check=True)
        self.git("remote", "add", "origin", str(self.origin))
        (self.repo / "VERSION").write_text("1.2.0\n", encoding="utf-8")
        self.doc = self.repo / "docs/ops/GO-NO-GO-2026-11-08-v1.2.0.md"
        self.doc.parent.mkdir(parents=True)
        self.doc.write_text(GO_DOC, encoding="utf-8")
        self.blueprint("S")
        self.set_key("agent")
        self.enterContext(unittest.mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(self.repo)}))

    def blueprint(self, scale):
        (self.repo / "BLUEPRINT.md").write_text(
            f"---\ntitle: B\nkind: blueprint\nscale: {scale}\n---\n\n# B\n", "utf-8"
        )

    def set_key(self, value, commit=True, push=True):
        (self.repo / "xt.yaml").write_text(f"lint: ''\nrelease_signoff: {value}\n", encoding="utf-8")
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

    def push_main(self, files):
        for rel, text in files.items():
            (self.repo / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.repo / rel).write_text(text, encoding="utf-8")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "go-no-go")
        self.git("push", "-q", "origin", "main")

    def test_main_refusal_scan_scope(self):
        """Quét nhánh chính đúng tập `_release_go_no_go`: GO-NO-GO*.md ở docs/ops, docs, gốc, nhắc v<VERSION>, có NO-GO."""
        self.push_main(
            {
                "docs/ops/GO-NO-GO-A-v1.2.0.md": refusal_doc(),
                "docs/GO-NO-GO-v1.2.0.md": refusal_doc(decision="Từ chối"),
                "GO-NO-GO.md": refusal_doc(),  # gốc, tiêu đề nhắc v1.2.0
                "docs/ops/GO-NO-GO-v1.1.0.md": refusal_doc("1.1.0"),  # bản khác
                "docs/old/GO-NO-GO-v1.2.0.md": refusal_doc(),  # ngoài tập thư mục
                "docs/ops/NOTE-v1.2.0.md": refusal_doc(),  # không phải GO-NO-GO
                "docs/ops/GO-NO-GO-B-v1.2.0.md": refusal_doc(decision="GO"),  # GO không phải từ chối
            }
        )
        self.assertEqual(
            xt._main_go_no_go_refusals(self.repo, "1.2.0"),
            [
                "origin/main:GO-NO-GO.md",
                "origin/main:docs/GO-NO-GO-v1.2.0.md",
                "origin/main:docs/ops/GO-NO-GO-A-v1.2.0.md",
            ],
        )

    def test_main_ref_unreadable_fails_closed(self):
        self.push_main({"docs/ops/GO-NO-GO-A-v1.2.0.md": refusal_doc(decision="GO")})
        real = xt._git

        def show_fails(cwd, *args, **kw):
            if args[0] == "show" and "GO-NO-GO-A" in args[1]:
                return subprocess.CompletedProcess(args, 128, "", "hỏng")
            return real(cwd, *args, **kw)

        own = "docs/ops/GO-NO-GO-2026-11-08-v1.2.0.md"
        with unittest.mock.patch.object(xt, "_git", side_effect=show_fails):
            self.refused("không đọc được origin/main:docs/ops/GO-NO-GO-A-v1.2.0.md", file=own)
        self.git("remote", "remove", "origin")
        with unittest.mock.patch.object(xt, "release_agent_signoff", return_value=True):
            self.refused("không đọc được nhánh chính", file=own)

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


class ReleaseSignRealCheckTest(SignoffRepo):
    """`release-sign` với `release-check` thật (repo đủ để máy GO): các ca review #480 tái hiện."""

    BP = "---\ntitle: B\nkind: blueprint\nupdated: 2026-10-19\nscale: S\nprofile: cli-tool\n---\n\n## Checklist\n\n"
    MUST_OK = "- [x] `BASE-X-001` **MUST** a — Kiểm: `true`\n"
    REFUSED = "docs/ops/GO-NO-GO-A-v1.2.0.md"

    def setUp(self):
        super().setUp()
        (self.repo / "docs/ops/AUDIT-STATUS.md").write_text(audit_status_text(), encoding="utf-8")
        (self.repo / ".gitignore").write_text("out/\ndist/\n", encoding="utf-8")
        self.prepare(self.MUST_OK)

    def prepare(self, checklist):
        """Blueprint `checklist` + GO-NO-GO B chưa ký có dòng `subject:` của cây đã commit."""
        (self.repo / "BLUEPRINT.md").write_text(self.BP + checklist, encoding="utf-8")
        self.doc.unlink()
        self.commit()
        self.unsigned = GO_DOC.replace(HEX, xt.subject_fingerprint(self.repo))
        self.doc.write_text(self.unsigned, encoding="utf-8")
        self.commit()

    def commit(self, push=True):
        self.git("add", "-A")
        self.git("commit", "-q", "--allow-empty", "-m", "c")
        if push:
            self.git("push", "-q", "origin", "main")

    def sign_cli(self, *extra):
        return run_main("release-sign", *extra, "--note", "máy đạt")

    def assert_refused(self, msg, *extra):
        code, _, err = self.sign_cli(*extra)
        self.assertEqual(code, 2, err)
        self.assertIn(msg, err)
        self.assertEqual(self.doc.read_text(encoding="utf-8"), self.unsigned)

    def test_baseline_signs(self):
        code, out, err = self.sign_cli()
        self.assertEqual(code, 0, err)
        self.assertIn("agent ký §5", out)

    def test_rejected_in_tree_not_overridden(self):
        """Review #480 🔴 (a): A có NO-GO của người, B chưa ký → promotion rejected; `release-sign --file B` từ chối."""
        (self.repo / self.REFUSED).write_text(refusal_doc(), encoding="utf-8")
        self.commit(push=False)
        _, out, _ = run_main("release-check", "--json")
        d = json.loads(out)
        self.assertEqual((d["promotion"]["state"], d["fails"], d["human"]), ("rejected", [], []), d["promotion"])
        self.assert_refused("người đã từ chối", "--file", self.doc.relative_to(self.repo).as_posix())

    def test_refusal_kept_on_main_after_tree_delete(self):
        """Review #480 🔴 (b): NO-GO đã lên nhánh chính, `git rm` ở nhánh làm việc → vẫn từ chối (đọc origin/main)."""
        (self.repo / self.REFUSED).write_text(refusal_doc(), encoding="utf-8")
        self.commit()
        self.git("rm", "-q", self.REFUSED)
        self.commit(push=False)
        _, out, _ = run_main("release-check", "--json")
        self.assertNotEqual(json.loads(out)["promotion"]["state"], "rejected")
        self.assert_refused(f"ở nhánh chính: origin/main:{self.REFUSED}")

    def test_unchecked_must_blocks_sign(self):
        """Review #480 🟠: MUST tick không `— Kiểm:` → `release-sign` từ chối (release-check `--unchecked-must fail`)."""
        self.prepare(self.MUST_OK + "- [x] `BASE-X-002` **MUST** b\n")
        self.assert_refused("FAIL unchecked_must")


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
