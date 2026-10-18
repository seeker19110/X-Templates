"""Test cho `xt.py doctor` — audit khung đã cài trước /autopilot (và cảnh báo của `loop init`).

Dự án đích giả = cài thật bằng install.py vào thư mục tạm, rồi làm hỏng từng phần.
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
import unittest.mock
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import install
import xt

FILLED_YAML = "lint: ruff check .\ntypecheck: pyright\ntest: pytest -q\nbuild: ''\n"


_REAL_VALIDATE = xt.validate
_VALIDATE_MEMO: dict[tuple, list[str]] = {}


def _memo_validate(root: Path) -> list[str]:
    """`xt.validate` nhớ theo chữ ký cây: mỗi test cài một bản sao khung giống hệt (install giữ mtime) nên validate thật
    chạy một lần thay vì ~30 lần. Trong khung: đường dẫn, kích thước, mtime của file. Ngoài khung (`.xtemplates/`, đích
    liên kết `../../research/`): validate chỉ cần file có hay không → chỉ đường dẫn (install ghi mới VERSION/README mỗi
    lần). Test sửa khung đổi chữ ký → validate thật chạy lại; validate tự nó được test ở test_xt."""
    tree = root.parent
    sig = []
    for p in tree.rglob("*"):
        rel = p.relative_to(tree).as_posix()
        if p.is_file() and p.is_relative_to(root):
            st = p.stat()
            sig.append((rel, st.st_size, st.st_mtime_ns))
        else:
            sig.append((rel,))
    key = (root.name, *sorted(sig))
    if key not in _VALIDATE_MEMO:
        _VALIDATE_MEMO[key] = _REAL_VALIDATE(root)
    return list(_VALIDATE_MEMO[key])


class DoctorCase(unittest.TestCase):
    """Dự án đích vừa cài khung (git init), xt.py chạy như bản `.xtemplates/scripts/xt.py` của dự án đó."""

    def setUp(self):
        self.tmp = Path(self.enterContext(tempfile.TemporaryDirectory())).resolve()
        self.base = self.tmp / "app"
        self.base.mkdir()
        with redirect_stderr(io.StringIO()):
            self.assertEqual(install.install(self.base, False, False, "test"), 0)
        subprocess.run(["git", "init", "-q", str(self.base)], check=True)
        self.fw = self.base / ".xtemplates" / "framework"
        self.enterContext(
            unittest.mock.patch.dict(
                os.environ,
                {
                    "CLAUDE_PROJECT_DIR": str(self.base),
                    "GIT_CEILING_DIRECTORIES": str(self.tmp),
                    # cấu hình Claude cấp người dùng của máy chạy test không lọt vào kiểm memory
                    "CLAUDE_CONFIG_DIR": str(self.tmp / "claude-cfg"),
                },
            )
        )
        self.enterContext(unittest.mock.patch.object(xt, "SCRIPT_DIR", self.base / ".xtemplates" / "scripts"))
        self.enterContext(unittest.mock.patch.object(xt, "validate", _memo_validate))

    def run_doctor(self, *args: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = xt.main(["--framework", str(self.fw), "doctor", *args])
        return rc, out.getvalue(), err.getvalue()

    def doctor_json(self, *args: str) -> tuple[int, dict]:
        rc, out, _ = self.run_doctor("--json", *args)
        return rc, json.loads(out)

    def findings(self, deep: bool = True) -> list[xt.Finding]:
        return xt.doctor_findings(self.base, self.fw, deep=deep)

    def codes(self, level: str = "error", deep: bool = True) -> list[str]:
        return [f.code for f in self.findings(deep) if f.level == level]

    def write(self, rel: str, text: str) -> Path:
        p = self.base / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        return p


class DoctorHealthyTest(DoctorCase):
    def test_fresh_install_is_ready_with_warnings(self):
        rc, doc = self.doctor_json()
        self.assertEqual(rc, 0)
        self.assertTrue(doc["ok"])
        self.assertEqual(doc["base"], str(self.base))
        self.assertEqual(doc["version"], "test")
        self.assertEqual(doc["fixed"], [])
        levels = {f["level"] for f in doc["findings"]}
        self.assertEqual(levels, {"warn"})
        msgs = " ".join(f["msg"] for f in doc["findings"])
        self.assertIn("cổng commit đang là no-op", msgs)  # mẫu xt.yaml để trống cả 4 khoá

    def test_text_output_ready(self):
        rc, out, _ = self.run_doctor()
        self.assertEqual(rc, 0)
        self.assertIn(f"Audit khung — {self.base} (khung test)", out)
        self.assertIn("✓ Sẵn sàng cho autopilot: 0 lỗi", out)

    def test_filled_xt_yaml_and_partial_blank(self):
        self.write("xt.yaml", FILLED_YAML)
        msgs = [f.msg for f in self.findings() if f.code == "xt-yaml"]
        self.assertEqual(len(msgs), 1)
        self.assertIn("để trống build", msgs[0])
        self.assertNotIn("no-op", msgs[0])
        self.write("xt.yaml", "lint: ruff check .\ntest: pytest\n")
        msgs = [f.msg for f in self.findings() if f.code == "xt-yaml"]
        self.assertEqual(msgs, ["xt.yaml thiếu khoá typecheck, build — khai đủ, chuỗi rỗng nếu không áp dụng"])

    def test_gate_tools_missing_warns(self):  # AUD-HAR-034
        self.write(
            "xt.yaml",
            "lint: xt-no-such-tool-1 . && for f in a; do bash -n $f || exit 1; done\n"
            "typecheck: python3 -m xt_no_such_mod_2 src\ntest: d=1 && git --version\nbuild: ''\n",
        )
        msgs = [f.msg for f in self.findings() if f.code == "gate-tools"]
        self.assertEqual(len(msgs), 1)
        self.assertIn("xt-no-such-tool-1 (lint)", msgs[0])
        self.assertIn("xt_no_such_mod_2 (typecheck)", msgs[0])
        for word in ("bash", "git", "for", "exit", "d="):
            self.assertNotIn(f" {word} (", msgs[0])
        self.write(  # review #84: công cụ theo đường dẫn, `|`/`do` trong nháy không phải lệnh
            "xt.yaml",
            "lint: node_modules/.bin/eslint src && scripts/dev-task.sh lint\n"
            'typecheck: grep -rE "TODO|FIXME" src && exit 1 || true\n'
            "test: git -C . log -1 && python3 -m json.tool -h 'do something'\nbuild: ''\n",
        )
        self.assertEqual([f.msg for f in self.findings() if f.code == "gate-tools"], [])
        start = time.monotonic()  # không bậc hai với token dài có `=` cuối
        self.assertEqual(xt._doctor_gate_tools({"lint": "git && " + "b" * 50000 + "="}), [])
        self.assertLess(time.monotonic() - start, 1.0)
        self.write("xt.yaml", "lint: git status && python3 -m json.tool x\ntypecheck: ''\ntest: ''\nbuild: ''\n")
        self.assertEqual([f for f in self.findings() if f.code == "gate-tools"], [])

    def test_repo_khung_itself_is_clean(self):
        with unittest.mock.patch.object(xt, "SCRIPT_DIR", ROOT / "scripts"):
            errors = [f.msg for f in xt.doctor_findings(ROOT, ROOT / "framework", deep=False) if f.level == "error"]
        self.assertEqual(errors, [])


class DoctorFixTest(DoctorCase):
    def test_fix_repairs_safe_parts_and_keeps_hook_errors(self):
        (self.base / ".gitignore").unlink()
        (self.base / "CLAUDE.md").unlink()
        (self.base / ".claude" / "hooks" / "_lib.sh").unlink()
        self.write(".claude/hooks/guard.py", "def (:\n")
        self.write(".autopilot/state.json", "[1]\n")
        rc, out, _ = self.run_doctor()
        self.assertEqual(rc, 1)
        self.assertIn("(sửa được: `xt.py doctor --fix`)", out)
        self.assertIn("✗ Chưa sẵn sàng cho autopilot: 5 lỗi", out)
        rc, out, _ = self.run_doctor("--fix")
        self.assertEqual(rc, 1)
        self.assertNotIn("sửa được", out)
        self.assertIn("🔧 đã sửa: tạo CLAUDE.md từ mẫu khung", out)
        self.assertIn("🔧 đã sửa: thêm `.autopilot/` vào .gitignore", out)
        self.assertIn("✗ Chưa sẵn sàng cho autopilot: 2 lỗi · 2 cảnh báo · 3 đã sửa", out)
        self.assertIn("_lib.sh nhưng file không có", out)
        self.assertIn("guard.py lỗi cú pháp", out)
        self.assertIn(".autopilot/\n", (self.base / ".gitignore").read_text(encoding="utf-8"))
        self.assertIn("@AGENTS.md", (self.base / "CLAUDE.md").read_text(encoding="utf-8"))
        self.assertFalse((self.base / ".autopilot" / "state.json").exists())
        self.assertEqual(len(list((self.base / ".autopilot").glob("state.json.hong-*"))), 1)

    def test_claude_md_without_import_gets_line_appended(self):
        self.write("CLAUDE.md", "# CLAUDE.md\n```\n@AGENTS.md\n```")
        self.assertIn("docs", self.codes())
        rc, doc = self.doctor_json("--fix")
        self.assertEqual(rc, 0)
        self.assertEqual(doc["fixed"], ["thêm dòng `@AGENTS.md` vào cuối CLAUDE.md"])
        self.assertTrue((self.base / "CLAUDE.md").read_text(encoding="utf-8").endswith("```\n@AGENTS.md\n"))

    def test_missing_template_is_not_fixable(self):
        (self.base / "AGENTS.md").unlink()
        (self.base / "PROGRESS.md").unlink()
        (self.fw / "templates" / "AGENTS.md").unlink()
        rc, doc = self.doctor_json("--fix")
        self.assertEqual(rc, 1)
        rows = {f["msg"].split(" — ")[0]: f for f in doc["findings"] if f["code"] == "docs"}
        self.assertEqual(rows["thiếu AGENTS.md"]["fixable"], False)
        self.assertEqual(doc["fixed"], ["tạo PROGRESS.md từ mẫu khung"])
        self.assertIn("## Bàn giao phiên", (self.base / "PROGRESS.md").read_text(encoding="utf-8"))

    def test_xt_yaml_from_template_or_legacy(self):
        (self.base / "xt.yaml").unlink()
        self.assertIn("xt-yaml", self.codes())
        self.assertEqual(self.doctor_json("--fix")[1]["fixed"], ["tạo xt.yaml từ mẫu khung"])
        self.assertIn("lint:", (self.base / "xt.yaml").read_text(encoding="utf-8"))
        (self.base / "xt.yaml").rename(self.base / "xs.yaml")
        self.assertEqual(self.doctor_json("--fix")[1]["fixed"], ["đổi tên xs.yaml → xt.yaml (ADR-0007)"])
        self.assertFalse((self.base / "xs.yaml").exists())

    def test_failed_fix_becomes_error(self):
        boom = unittest.mock.Mock(side_effect=PermissionError("chỉ đọc"))
        fixed, failed = xt.doctor_fix([xt.Finding("x", "warn", "m", boom), xt.Finding("y", "warn", "n")])
        self.assertEqual(fixed, [])
        self.assertEqual([(f.code, f.level) for f in failed], [("x", "error")])
        self.assertIn("sửa thất bại (m): chỉ đọc", failed[0].msg)

    def test_template_body_matches_install(self):
        for src in sorted((ROOT / "framework" / "templates").glob("*")):
            if src.name in install.ROOT_TEMPLATES:
                text = src.read_text(encoding="utf-8")
                self.assertEqual(xt.template_body(text), install.template_body(text), src.name)


class DoctorHooksTest(DoctorCase):
    def test_settings_missing_or_broken(self):
        settings = self.base / ".claude" / "settings.json"
        settings.write_text("{bad", encoding="utf-8")
        self.assertIn("settings.json hỏng", " ".join(f.msg for f in self.findings()))
        settings.unlink()
        msgs = [f.msg for f in self.findings() if f.code == "hooks"]
        self.assertEqual(len(msgs), 1)
        self.assertIn("không có .claude/settings.json", msgs[0])

    def test_missing_events_and_odd_structure(self):
        settings = self.base / ".claude" / "settings.json"
        data = json.loads(settings.read_text(encoding="utf-8"))
        hooks = data["hooks"]
        del hooks["Stop"], hooks["PostToolUse"]
        hooks["Notification"] = "lạ"
        hooks["SubagentStop"] = ["lạ", {"hooks": None}, {"hooks": ["lạ", {"type": "command"}]}]
        settings.write_text(json.dumps(data), encoding="utf-8")
        found = [(f.level, f.msg.split(";")[0]) for f in self.findings() if f.code == "hooks"]
        self.assertEqual(
            found, [("error", "settings.json thiếu hook Stop"), ("warn", "settings.json thiếu hook PostToolUse")]
        )

    def test_shell_syntax_and_other_suffixes(self):
        self.write(".claude/hooks/stop-guard.sh", "if then\n")
        self.write(".claude/hooks/sub/note.txt", "x")
        settings = self.base / ".claude" / "settings.json"
        data = json.loads(settings.read_text(encoding="utf-8"))
        data["hooks"]["Notification"] = [
            {"hooks": [{"type": "command", "command": 'cat "$CLAUDE_PROJECT_DIR/.claude/hooks/sub/note.txt"'}]}
        ]
        settings.write_text(json.dumps(data), encoding="utf-8")
        msgs = [f.msg for f in self.findings() if f.code == "hooks"]
        self.assertEqual(len(msgs), 1)
        self.assertIn("stop-guard.sh lỗi cú pháp", msgs[0])
        self.assertEqual(self.codes(deep=False), [])  # loop init: không kiểm cú pháp
        empty_err = subprocess.CompletedProcess([], 2, "", "")
        with unittest.mock.patch.object(xt.subprocess, "run", return_value=empty_err):
            self.assertEqual(xt._syntax_error(self.base / ".claude" / "hooks" / "x.sh"), "bash -n exit 2")
        with unittest.mock.patch.object(xt.shutil, "which", return_value=None):
            self.assertIsNone(xt._syntax_error(self.base / ".claude" / "hooks" / "stop-guard.sh"))

    def test_python_hook_with_null_byte(self):
        p = self.base / ".claude" / "hooks" / "guard.py"
        p.write_bytes(b"x = 1\x00\n")
        self.assertIsNotNone(xt._syntax_error(p))

    def test_skills_agents_and_pending_new(self):
        shutil.rmtree(self.base / ".claude" / "skills" / "gate")
        (self.base / ".claude" / "agents" / "reviewer.md").unlink()
        self.write(".claude/hooks/stop-guard.sh.xtemplates-new", "x")
        self.write("AGENTS.md.xtemplates-new", "x")
        found = [(f.level, f.msg) for f in self.findings() if f.code == "harness"]
        self.assertEqual(len(found), 3)
        self.assertIn("thiếu skills/gate/SKILL.md, agents/reviewer.md", found[0][1])
        # AUD-HAR-050: hook/settings chưa gộp = hàng rào của khung có thể không chạy → lỗi, không chỉ cảnh báo.
        self.assertEqual(found[1][0], "error")
        self.assertIn(".claude/hooks/stop-guard.sh.xtemplates-new", found[1][1])
        self.assertEqual(found[2], ("warn", found[2][1]))
        self.assertIn("AGENTS.md.xtemplates-new", found[2][1])
        self.assertNotIn("stop-guard", found[2][1])


class DoctorStateAndEnvTest(DoctorCase):
    def test_state_blocked_and_missing_plan(self):
        xt.write_state(
            {"active": True, "plan": "docs/autopilot/PLAN.md", "blocked": True, "blocked_reason": "cần khoá"}, self.base
        )
        msgs = [f.msg for f in self.findings() if f.code == "state"]
        self.assertEqual(len(msgs), 2)
        self.assertIn("BLOCKED: cần khoá", msgs[0])
        self.assertIn("không còn PLAN `docs/autopilot/PLAN.md`", msgs[1])
        self.write("docs/autopilot/PLAN.md", "")
        xt.write_state({"active": True, "plan": "docs/autopilot/PLAN.md", "blocked": True}, self.base)
        self.assertEqual(
            [f.msg for f in self.findings() if f.code == "state"][0].split(" — ")[0], "autopilot đang BLOCKED: ?"
        )
        xt.write_state({"active": False}, self.base)
        self.assertNotIn("state", [f.code for f in self.findings()])

    def test_legacy_and_not_git(self):
        (self.base / ".xstored").mkdir()
        self.write("xs.yaml", "lint: x\n")
        shutil.rmtree(self.base / ".git")
        codes = [(f.code, f.level) for f in self.findings()]
        self.assertEqual(codes.count(("legacy", "warn")), 2)
        self.assertIn(("git", "warn"), codes)

    def test_runtime_tools_and_python(self):
        with unittest.mock.patch.object(xt.shutil, "which", return_value=None):
            self.assertEqual([f.code for f in xt._doctor_runtime()], ["runtime", "runtime"])
            self.assertEqual(xt._doctor_git(self.base), [])
        with unittest.mock.patch.object(sys, "version_info", (3, 10, 0)):
            self.assertIn("< 3.11", xt._doctor_runtime()[0].msg)

    def test_scripts_and_version(self):
        (self.base / ".xtemplates" / "scripts" / "dev-task.sh").unlink()
        (self.base / ".xtemplates" / "VERSION").unlink()
        found = [(f.code, f.level) for f in self.findings()]
        self.assertIn(("scripts", "error"), found)
        self.assertIn(("scripts", "warn"), found)

    def test_framework_missing_or_invalid(self):
        self.write(".xtemplates/framework/hong.md", "không frontmatter\n")
        msg = next(f.msg for f in self.findings() if f.code == "framework")
        self.assertIn("khung lệch quy ước (1 lỗi, vd: hong.md: thiếu frontmatter", msg)
        self.assertEqual(xt._doctor_framework(self.tmp / "khong-co")[0].code, "framework")

    def test_progress_variants(self):
        with unittest.mock.patch.object(xt, "progress_check", side_effect=OSError("git hỏng")):
            self.assertEqual(
                xt._doctor_progress(self.base)[0].msg, "PROGRESS.md: git hỏng — xem `xt.py progress-check`"
            )
        with unittest.mock.patch.object(xt, "progress_check", return_value=["a", "b", "c"]):
            self.assertIn("a (+2 lỗi khác)", xt._doctor_progress(self.base)[0].msg)
        with unittest.mock.patch.object(xt, "progress_check", return_value=[]):
            self.assertEqual(xt._doctor_progress(self.base), [])
        (self.base / "PROGRESS.md").unlink()
        self.assertEqual(xt._doctor_progress(self.base), [])


BP_M_WEB = "---\ntitle: Blueprint\nkind: blueprint\nprofile: web-app\nscale: M\n---\n"


class DoctorGateFloorTest(DoctorCase):
    """Sàn Gate theo quy mô (LOOP-HARNESS-023): ở M/L xt.yaml phải khai lệnh thật cho format_check, coverage, kiểm kiểu
    theo stack, e2e theo hồ sơ — máy không đoán tên công cụ (review #107)."""

    FULL = (
        "lint: ruff check .\ntypecheck: mypy .\ntest: pytest -q\nbuild: ''\n"
        "format_check: ruff format --check .\ncoverage: pytest --cov --cov-fail-under=80\n"
    )

    def floor(self) -> list[str]:
        return [f.msg for f in self.findings(deep=False) if f.code == "gate-floor"]

    def test_no_blueprint_or_scale_s_has_no_floor(self):
        self.write("xt.yaml", FILLED_YAML)
        self.assertEqual(self.floor(), [])  # không có BLUEPRINT.md → không biết quy mô
        self.write("BLUEPRINT.md", "# không có frontmatter\n")
        self.assertEqual((xt.blueprint_scale(self.base), self.floor()), (("", ""), []))
        self.write("BLUEPRINT.md", BP_M_WEB.replace("scale: M", "scale: S"))
        self.assertEqual((xt.blueprint_scale(self.base), self.floor()), (("S", "web-app"), []))
        self.write("BLUEPRINT.md", BP_M_WEB.replace("scale: M", "scale: X"))
        self.assertEqual(xt.blueprint_scale(self.base), ("", "web-app"))
        self.write("BLUEPRINT.md", BP_M_WEB)
        (self.base / "xt.yaml").unlink()
        self.assertEqual((xt.gate_floor_issues(self.base), xt.gate_floor_commands(self.base)), ([], []))

    def test_scale_read_like_yaml(self):
        # `scale: m`, nháy, comment, CRLF: không được lặng lẽ bỏ sàn (review #107).
        for raw in ("scale: m", 'scale: "M"', "scale: M  # quy mô", "scale: 'l'"):
            with self.subTest(raw=raw):
                self.write("BLUEPRINT.md", BP_M_WEB.replace("scale: M", raw).replace("\n", "\r\n"))
                self.assertIn(xt.blueprint_scale(self.base)[0], ("M", "L"))

    def test_scale_m_reports_each_missing_key(self):
        self.write("BLUEPRINT.md", BP_M_WEB)
        self.write("xt.yaml", FILLED_YAML + "format_check: true\ne2e: echo bỏ qua\n")  # no-op = thiếu
        self.write("tsconfig.json", "{}")
        self.write("go.mod", "module x\n")
        msgs = self.floor()
        self.assertEqual([m.split("`")[1] for m in msgs], ["format_check", "coverage", "build", "e2e"], msgs)
        self.assertTrue(msgs[0].startswith("quy mô M: xt.yaml thiếu `format_check` — kiểm format"))
        self.assertIn("kiểm kiểu/biên dịch vì repo có tsconfig.json, go.mod", msgs[2])
        self.assertIn("hồ sơ web-app", msgs[3])
        self.assertTrue(all(m.endswith("— sàn Gate M/L (LOOP-HARNESS-023)") for m in msgs))
        self.write("xt.yaml", self.FULL.replace("typecheck: mypy .", "typecheck: 'true'"))
        (self.base / "go.mod").unlink()
        self.assertEqual([m.split("`")[1] for m in self.floor()], ["typecheck", "e2e"])

    def test_floor_met_lists_commands(self):
        # Stack bất kỳ qua sàn khi khai lệnh — không còn danh sách tên công cụ (deno, dotnet, gradle…).
        self.write(
            "docs/BP.md", BP_M_WEB.replace("profile: web-app", "profile: cli-tool").replace("scale: M", "scale: L")
        )
        xt.write_state({"active": True, "blueprint": "docs/BP.md"}, self.base)
        self.assertEqual(xt.blueprint_scale(self.base), ("L", "cli-tool"))
        self.write("pyproject.toml", "[project]\nname='x'\n")
        self.write("xt.yaml", self.FULL.replace("ruff format --check .", "deno fmt --check"))
        self.assertEqual(self.floor(), [])
        self.assertEqual(
            xt.gate_floor_commands(self.base),
            [
                ("format_check", "deno fmt --check"),
                ("coverage", "pytest --cov --cov-fail-under=80"),
                ("typecheck", "mypy ."),
            ],
        )


class LoopInitDoctorTest(DoctorCase):
    def loop_init(self) -> str:
        self.write("docs/autopilot/PLAN.md", "- [ ] `T-001` việc — Gate: `true`\n")
        err = io.StringIO()
        with redirect_stdout(io.StringIO()), redirect_stderr(err):
            self.assertEqual(xt.main(["--framework", str(self.fw), "loop", "init"]), 0)
        return err.getvalue()

    def test_clean_project_has_no_warning(self):
        # Bản cài mới để xt.yaml trống → cổng sẽ đỏ trong vòng (ADR-0011); khai lệnh thật thì im.
        self.assertIn("Cổng sẽ ĐỎ trong vòng (ADR-0011)", self.loop_init())
        self.write("xt.yaml", "lint: ruff check .\ntypecheck: mypy .\ntest: pytest -q\nbuild: ''\n")
        self.assertEqual(self.loop_init(), "")
        self.write("BLUEPRINT.md", BP_M_WEB)  # quy mô M: sàn Gate chưa đạt được nhắc ngay ở loop init
        err = self.loop_init()
        self.assertIn(
            "⚠ Sàn Gate chưa đạt (LOOP-HARNESS-023, `loop verify` đỏ tới khi sửa): quy mô M: xt.yaml thiếu `format_check`",
            err,
        )

    def test_errors_are_warned_but_not_blocking(self):
        shutil.rmtree(self.base / ".claude")
        (self.base / "CLAUDE.md").unlink()
        err = self.loop_init()
        self.assertTrue(err.startswith("⚠ Audit khung còn 2 lỗi — chạy `xt.py doctor --fix`: "))
        (self.base / "AGENTS.md").unlink()
        (self.base / "xt.yaml").unlink()
        err = self.loop_init()
        self.assertTrue(err.startswith("⚠ Audit khung còn 4 lỗi"))
        self.assertTrue(err.rstrip().endswith("(+1)"))
        self.assertTrue(xt.read_state(self.base)["active"])


class DoctorMemoryTest(DoctorCase):
    """LOOP-HARNESS-021: tối đa một công cụ memory ngoài; `.engram/` không nằm trong git."""

    def setUp(self):
        super().setUp()
        self.cfg = self.tmp / "claude-cfg"

    def json_at(self, path: Path, data: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data), encoding="utf-8")

    def plugins(self, rel: str, plugins: dict) -> None:
        """Gộp `enabledPlugins` vào settings của dự án (giữ hook của bản cài)."""
        p = self.base / rel
        data = json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}
        data["enabledPlugins"] = plugins
        self.json_at(p, data)

    def memory(self) -> list[xt.Finding]:
        return [f for f in self.findings(deep=False) if f.code == "memory"]

    def test_fresh_install_has_no_memory_finding(self):
        self.assertEqual(self.memory(), [])

    def test_one_tool_in_several_places_is_fine(self):
        self.json_at(self.cfg / "settings.json", {"enabledPlugins": {"engram@engram": True}})
        self.json_at(self.cfg / ".claude.json", {"mcpServers": {"engram": {"command": "engram"}}})
        self.json_at(self.base / ".mcp.json", {"mcpServers": {"plugin_engram_engram": {}}})
        self.assertEqual(self.memory(), [])

    def test_two_tools_warn_with_names_and_where(self):
        self.plugins(".claude/settings.json", {"claude-mem@thedotmack": True})
        self.json_at(self.base / ".mcp.json", {"mcpServers": {"engram": {"command": "engram", "env": {"K": "bí-mật"}}}})
        [f] = self.memory()
        self.assertEqual(f.level, "warn")
        self.assertIsNone(f.fix)
        for part in (
            "2 công cụ",
            "claude-mem (plugin claude-mem@thedotmack)",
            "engram (MCP engram)",
            "LOOP-HARNESS-021",
        ):
            self.assertIn(part, f.msg)
        self.assertNotIn("bí-mật", f.msg)  # chỉ in tên, không in giá trị cấu hình
        rc, doc = self.doctor_json()
        [row] = [r for r in doc["findings"] if r["code"] == "memory"]
        self.assertEqual((row["level"], row["fixable"]), ("warn", False))

    def test_local_settings_override_and_local_scope_mcp(self):
        self.plugins(".claude/settings.json", {"agentmemory@rohitg00": True, "x@y": False})
        self.plugins(".claude/settings.local.json", {"agentmemory@rohitg00": False})
        self.json_at(self.cfg / ".claude.json", {"projects": {str(self.base): {"mcpServers": {"engram": {}}}}})
        self.assertEqual(self.memory(), [])  # agentmemory bị tắt ở cấp cục bộ → chỉ còn engram
        self.json_at(self.cfg / "settings.json", {"enabledPlugins": {"mem0@mem0ai": True}})
        [f] = self.memory()
        self.assertIn("mem0 (plugin mem0@mem0ai)", f.msg)
        self.assertIn("engram (MCP engram)", f.msg)

    def test_malformed_configs_fail_open(self):
        self.plugins(".claude/settings.json", ["engram@engram"])
        self.json_at(self.cfg / ".claude.json", {"mcpServers": ["claude-mem"], "projects": {str(self.base): "hỏng"}})
        self.write(".mcp.json", "{không phải json")
        self.assertEqual(self.memory(), [])
        self.json_at(self.cfg / ".claude.json", {"projects": ["hỏng"]})
        self.assertEqual(self.memory(), [])

    def test_matching_is_by_token(self):
        self.plugins(".claude/settings.json", {"claude-memory@x": True, "engrams@y": True, "MEM0-pro@z": True})
        self.json_at(self.base / ".mcp.json", {"mcpServers": {"basic-memory": {}}})
        [f] = self.memory()  # chỉ mem0 (không phân biệt hoa thường) và basic-memory khớp
        self.assertIn("basic-memory (MCP basic-memory)", f.msg)
        self.assertIn("mem0 (plugin MEM0-pro@z)", f.msg)
        self.assertNotIn("claude-memory", f.msg)
        self.assertNotIn("engrams", f.msg)

    def test_home_default_without_config_dir(self):
        home = self.tmp / "home"
        self.json_at(home / ".claude" / "settings.json", {"enabledPlugins": {"engram@engram": True}})
        self.json_at(home / ".claude.json", {"mcpServers": {"claude-mem": {}}})
        env = {k: v for k, v in os.environ.items() if k != "CLAUDE_CONFIG_DIR"}
        with (
            unittest.mock.patch.dict(os.environ, env, clear=True),
            unittest.mock.patch("pathlib.Path.home", return_value=home),
        ):
            [f] = self.memory()
        self.assertIn("claude-mem (MCP claude-mem)", f.msg)
        self.assertIn("engram (plugin engram@engram)", f.msg)

    def test_unknown_home_skips_user_level_without_crashing(self):
        self.plugins(".claude/settings.json", {"engram@engram": True, "claude-mem@thedotmack": True})
        env = {k: v for k, v in os.environ.items() if k != "CLAUDE_CONFIG_DIR"}
        with (
            unittest.mock.patch.dict(os.environ, env, clear=True),
            unittest.mock.patch("pathlib.Path.home", side_effect=RuntimeError("Could not determine home directory")),
        ):
            [f] = self.memory()  # cấp dự án vẫn được kiểm
        self.assertIn("2 công cụ", f.msg)

    def test_engram_dir_tracked_in_git_warns(self):
        self.write(".engram/chunk-001.jsonl.gz", "x")
        self.assertEqual(self.memory(), [])  # chưa vào git
        subprocess.run(["git", "-C", str(self.base), "add", ".engram"], check=True)
        [f] = self.memory()
        self.assertIn("`.engram/`", f.msg)
        self.assertIn("gitleaks", f.msg)


if __name__ == "__main__":
    unittest.main()
