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
import unittest
import unittest.mock
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))  # tests/cpu_budget.py
import cpu_budget
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

    def test_xt_yaml_duplicate_key_is_error(self):  # AUD-XFEAT-002
        self.write("xt.yaml", FILLED_YAML + "lint: true\n")
        errs = [f.msg for f in self.findings() if f.code == "xt-yaml" and f.level == "error"]
        self.assertEqual(len(errs), 1, errs)
        self.assertIn("khoá trùng: lint", errs[0])

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
        # không bậc hai với token dài có `=` cuối (AUD-TEST-008: so tỉ lệ cỡ n/4n, không ngưỡng giây cứng)
        self.assertEqual(xt._doctor_gate_tools({"lint": "git && " + "b" * 50000 + "="}), [])
        cpu_budget.assert_not_quadratic(
            self, lambda n: xt._doctor_gate_tools({"lint": "git && " + "b" * n + "="}), 12500
        )
        self.write("xt.yaml", "lint: git status && python3 -m json.tool x\ntypecheck: ''\ntest: ''\nbuild: ''\n")
        self.assertEqual([f for f in self.findings() if f.code == "gate-tools"], [])

    def test_repo_khung_itself_is_clean(self):
        with unittest.mock.patch.object(xt, "SCRIPT_DIR", ROOT / "scripts"):
            errors = [f.msg for f in xt.doctor_findings(ROOT, ROOT / "framework", deep=False) if f.level == "error"]
        self.assertEqual(errors, [])


class DoctorAppTest(DoctorCase):
    """T-1981 (ADR-0038): install.py chép `scripts/xt_app`, `scripts/app` cạnh xt.py; thiếu → doctor ⚠ `app`, không ✗."""

    def test_install_copies_app_and_doctor_warns_when_missing(self):
        scripts = self.base / ".xtemplates" / "scripts"
        self.assertTrue((scripts / "xt_app" / "server.py").is_file())
        self.assertTrue((scripts / "app" / "index.html").is_file())
        self.assertFalse(list(scripts.rglob("__pycache__")))
        self.assertNotIn("app", self.codes("warn", deep=False))
        shutil.rmtree(scripts / "app")
        warn = [f for f in self.findings(deep=False) if f.code == "app"]
        self.assertEqual([f.level for f in warn], ["warn"])
        self.assertIn("thiếu app cạnh xt.py", warn[0].msg)
        self.assertNotIn("app", self.codes("error", deep=False))


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

    def test_hook_climbing_to_repo_root_is_not_a_missing_sibling(self):
        """`$(dirname "$0")/../..` (hook riêng của dự án lên gốc repo — dhcb) không phải file nạp cạnh hook tên `..`."""
        self.write(
            ".claude/hooks/rieng.sh", 'ROOT="$(cd "$(dirname "$0")/../.." && pwd)"\nsource "$(dirname "$0")/_lib.sh"\n'
        )
        settings = self.base / ".claude" / "settings.json"
        data = json.loads(settings.read_text(encoding="utf-8"))
        data["hooks"]["Stop"].append({"hooks": [{"type": "command", "command": "bash .claude/hooks/rieng.sh"}]})
        settings.write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual(self.codes(), [])
        (self.base / ".claude" / "hooks" / "_lib.sh").unlink()
        self.assertIn("_lib.sh nhưng file không có", " ".join(f.msg for f in self.findings() if f.code == "hooks"))

    def test_project_command_replaces_framework_skill(self):
        """Skill khung bị lệnh riêng cùng tên thay (install.py không cài) — không báo thiếu."""
        shutil.rmtree(self.base / ".claude" / "skills" / "gate")
        self.write(".claude/commands/gate.md", "# /gate của dự án\n")
        self.assertEqual([f.msg for f in self.findings() if f.code == "harness"], [])

    def test_python_hook_with_null_byte(self):
        p = self.base / ".claude" / "hooks" / "guard.py"
        p.write_bytes(b"x = 1\x00\n")
        self.assertIsNotNone(xt._syntax_error(p))

    def test_skills_agents_and_pending_new(self):
        shutil.rmtree(self.base / ".claude" / "skills" / "gate")
        (self.base / ".claude" / "agents" / "reviewer.md").unlink()
        (self.base / ".claude" / "agents" / "reviewer-alt.md").unlink()  # AUD-HAR-107
        self.write(".claude/hooks/stop-guard.sh.xtemplates-new", "x")
        self.write("AGENTS.md.xtemplates-new", "x")
        self.write(".github/workflows/merge-gate.yml.xtemplates-new", "x")
        found = [(f.level, f.msg) for f in self.findings() if f.code == "harness"]
        self.assertEqual(len(found), 3)
        self.assertIn("thiếu skills/gate/SKILL.md, agents/reviewer.md, agents/reviewer-alt.md", found[0][1])
        # AUD-HAR-050: hook/settings chưa gộp = hàng rào của khung có thể không chạy → lỗi, không chỉ cảnh báo.
        self.assertEqual(found[1][0], "error")
        self.assertIn(".claude/hooks/stop-guard.sh.xtemplates-new", found[1][1])
        self.assertEqual(found[2], ("warn", found[2][1]))
        self.assertIn("AGENTS.md.xtemplates-new", found[2][1])
        self.assertIn(".github/workflows/merge-gate.yml.xtemplates-new", found[2][1])
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
        # Quy mô M mà thiếu cả xt.yaml: mọi khoá sàn đều thiếu, không lặng lẽ tắt sàn (review #107).
        self.assertEqual(
            [m.split("`")[1] for m in xt.gate_floor_issues(self.base)], ["format_check", "coverage", "e2e"]
        )
        self.assertEqual(xt.gate_floor_commands(self.base), [])

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
        self.assertTrue(msgs[0].startswith("quy mô M: xt.yaml thiếu hoặc no-op `format_check` — kiểm format"))
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


class DoctorVersionTest(DoctorCase):
    """D-040: dự án đích biết khung đã cài lỗi thời — so `.xtemplates/VERSION` với tag `vX.Y.Z` mới nhất (fail-open)."""

    def gh(self, rc: int = 0, out: str = "[]", exc: BaseException | None = None):
        def run(cmd, **kw):
            self.assertEqual(cmd[:2], ["gh", "api"])
            if exc:
                raise exc
            return subprocess.CompletedProcess(cmd, rc, out, "")

        return unittest.mock.patch("xt.subprocess.run", side_effect=run)

    def test_latest_tag_pagination_stops_at_cap(self):
        """API trả trang đầy mãi (lặp trang) → dừng ở trần GH_MAX_PAGES, không vòng vô hạn."""
        full = json.dumps([{"name": "v1.0.0"}] * 100)
        with self.gh(out=full) as run:
            self.assertEqual(xt.latest_framework_tag(), (1, 0, 0))
        self.assertEqual(run.call_count, xt.GH_MAX_PAGES)

    def test_latest_tag_parsing_and_fail_open(self):
        page1 = [{"name": "v2.0.0"}, {"name": "v3.0.0-rc1"}, {"name": "nope"}, "x", {"name": 3}]
        page1 += [{"name": f"t{i}"} for i in range(100 - len(page1))]  # trang đầy 100 → đọc tiếp trang 2
        pages = {"page=1": json.dumps(page1), "page=2": json.dumps([{"name": "v10.1.0"}])}

        def run(cmd, **kw):  # phân trang tự làm `page=N` (FB-001), không `--paginate`
            self.assertNotIn("--paginate", cmd)
            return subprocess.CompletedProcess(cmd, 0, pages.get(cmd[-1].rsplit("&", 1)[-1], "[]"), "")

        with unittest.mock.patch("xt.subprocess.run", side_effect=run):
            self.assertEqual(xt.latest_framework_tag(), (10, 1, 0))  # so số, không so chuỗi; pre-release bỏ
        cases = (
            {"rc": 1},
            {"out": "{hỏng"},
            {"out": "{}"},
            {"out": "[]"},
            {"exc": FileNotFoundError("gh")},
            {"exc": subprocess.TimeoutExpired("gh", 10)},
            {"exc": UnicodeDecodeError("utf-8", b"\xe9", 0, 1, "x")},  # trang chặn của proxy, không phải UTF-8
            {"out": '{"message": "Not Found"}'},
        )
        for kw in cases:
            with self.subTest(kw=kw), self.gh(**kw):
                self.assertIsNone(xt.latest_framework_tag())
        with unittest.mock.patch.dict(os.environ, {"XT_FRAMEWORK_REPO": "fork/khung"}), self.gh() as run:
            xt.latest_framework_tag()
        want = ["gh", "api", "--hostname", "github.com", "repos/fork/khung/tags?per_page=100&page=1"]
        self.assertEqual(run.call_args[0][0], want)

    def test_doctor_warns_only_when_installed_is_older(self):
        def msgs(latest):
            with unittest.mock.patch.object(xt, "latest_framework_tag", return_value=latest):
                return [f.msg for f in self.findings() if f.code == "version"]

        self.assertEqual(msgs((3, 0, 0)), [])  # nhãn "test" không phải SemVer → bỏ qua
        self.write(".xtemplates/VERSION", "2.0.0 (55de4d1)\n")
        got = msgs((3, 0, 0))
        self.assertEqual(len(got), 1)
        self.assertTrue(
            got[0].startswith("khung đã cài 2.0.0 cũ hơn bản phát hành mới nhất v3.0.0 — chạy lại `install.py`")
        )
        self.assertEqual(
            (msgs((2, 0, 0)), msgs((1, 9, 9)), msgs(None)), ([], [], [])
        )  # bằng, mới hơn, không đọc được tag
        with unittest.mock.patch.object(xt, "latest_framework_tag") as latest:
            self.assertNotIn("version", [f.code for f in self.findings(deep=False)])  # loop init: không gọi mạng
        latest.assert_not_called()
        self.write(".xtemplates/VERSION", "3.0.0-rc1\n")  # pre-release cũ hơn bản cùng số (SemVer §11)
        got = msgs((3, 0, 0))
        self.assertEqual(len(got), 1)
        self.assertIn("khung đã cài 3.0.0-rc1 cũ hơn", got[0])
        self.assertEqual(msgs((2, 9, 9)), [])
        (self.base / ".xtemplates" / "VERSION").unlink()
        self.assertEqual(xt._doctor_version(self.base), [])  # repo khung / chưa cài


class LoopInitDoctorTest(DoctorCase):
    def loop_init(self) -> str:
        self.write("docs/autopilot/PLAN.md", "- [ ] `T-001` việc — Gate: `true`\n")
        err = io.StringIO()
        with redirect_stdout(io.StringIO()), redirect_stderr(err):
            self.assertEqual(xt.main(["--framework", str(self.fw), "loop", "init", "--force"]), 0)
        return err.getvalue()

    def test_clean_project_has_no_warning(self):
        # Bản cài mới để xt.yaml trống → cổng sẽ đỏ trong vòng (ADR-0011); khai lệnh thật thì im.
        self.assertIn("Cổng sẽ ĐỎ trong vòng (ADR-0011)", self.loop_init())
        self.write("xt.yaml", "lint: ruff check .\ntypecheck: mypy .\ntest: pytest -q\nbuild: ''\n")
        self.assertEqual(self.loop_init(), "")
        self.write("BLUEPRINT.md", BP_M_WEB)  # quy mô M: sàn Gate chưa đạt được nhắc ngay ở loop init
        err = self.loop_init()
        self.assertIn(
            "⚠ Sàn Gate chưa đạt (LOOP-HARNESS-023, `loop verify` đỏ tới khi sửa): quy mô M: xt.yaml thiếu hoặc no-op `format_check`",
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


class DoctorGuardAndClaudeVersionTest(DoctorCase):
    """LOOP-HARNESS-025 (guard chặn lệnh mẫu) và LOOP-HARNESS-026 (`claude_min_version`) — rà stored 2026-10-18."""

    def test_installed_guard_blocks_canaries(self):
        self.assertEqual(xt._doctor_guard_canary(self.base), [])

    def test_permissive_guard_is_error(self):
        stub = "def bash_decision(c, r, w):\n    return {'decision': ''}\n\ndef apply_policy(o):\n    return o\n"
        (self.base / xt.GUARD_FILE).write_text(stub, encoding="utf-8")
        got = xt._doctor_guard_canary(self.base)
        self.assertEqual([(f.code, f.level) for f in got], [("hooks", "error")])
        self.assertIn("KHÔNG chặn lệnh nguy hiểm mẫu", got[0].msg)

    def test_canary_uses_project_guard_only(self):
        # xt.py của bản cài khác (guard thật) không được che guard dự án cho qua mọi lệnh (review #119).
        stub = "def bash_decision(c, r, w):\n    return {'decision': ''}\n\ndef apply_policy(o):\n    return o\n"
        (self.base / xt.GUARD_FILE).write_text(stub, encoding="utf-8")
        real = ROOT / xt.GUARD_FILE
        with unittest.mock.patch.object(xt, "guard_paths", lambda b: [b / xt.GUARD_FILE, real]):
            self.assertEqual(len(xt._doctor_guard_canary(self.base)), 1)
            self.assertTrue(xt.guard_block("git push --force origin main", self.base))  # chốt chặn vẫn dùng cả hai

    def test_no_guard_left_to_hook_checks(self):
        (self.base / xt.GUARD_FILE).write_text("def x(:\n", encoding="utf-8")  # lỗi cú pháp: phần hook báo
        self.assertEqual(xt._doctor_guard_canary(self.base), [])
        (self.base / xt.GUARD_FILE).unlink()
        self.assertEqual(xt._doctor_guard_canary(self.base), [])

    def test_env_patch_restores(self):
        with unittest.mock.patch.dict(os.environ, {"XT_GUARD_POLICY": "strict"}):
            with xt._env_patch("XT_GUARD_POLICY", ""):
                self.assertEqual(os.environ["XT_GUARD_POLICY"], "")
            self.assertEqual(os.environ["XT_GUARD_POLICY"], "strict")
        os.environ.pop("XT_TMP_KEY", None)
        with xt._env_patch("XT_TMP_KEY", "1"):
            self.assertEqual(os.environ["XT_TMP_KEY"], "1")
        self.assertNotIn("XT_TMP_KEY", os.environ)

    def test_claude_version_parse(self):
        ok = subprocess.CompletedProcess([], 0, stdout="2.1.302 (Claude Code)\n", stderr="")
        with unittest.mock.patch.object(xt.shutil, "which", return_value="/bin/claude"):
            with unittest.mock.patch.object(xt.subprocess, "run", return_value=ok):
                self.assertEqual(xt._claude_version(), (2, 1, 302))
            bad = subprocess.CompletedProcess([], 0, stdout="?", stderr="")
            with unittest.mock.patch.object(xt.subprocess, "run", return_value=bad):
                self.assertIsNone(xt._claude_version())
            with unittest.mock.patch.object(xt.subprocess, "run", side_effect=OSError):
                self.assertIsNone(xt._claude_version())
        with unittest.mock.patch.object(xt.shutil, "which", return_value=None):
            self.assertIsNone(xt._claude_version())

    def test_claude_min_version(self):
        self.assertEqual(xt._doctor_claude_version(self.base), [])  # không khai khoá → không kiểm
        self.write("xt.yaml", "test: pytest\nclaude_min_version: 2.1.200\n")
        with unittest.mock.patch.object(xt, "_claude_version", return_value=(2, 1, 150)):
            got = xt._doctor_claude_version(self.base)
        self.assertEqual([(f.code, f.level) for f in got], [("runtime", "warn")])
        self.assertIn("requiredMinimumVersion", got[0].msg)
        for have in ((2, 1, 200), None):
            with unittest.mock.patch.object(xt, "_claude_version", return_value=have):
                self.assertEqual(xt._doctor_claude_version(self.base), [])


class DoctorDriftTest(DoctorCase):
    """`doctor --drift --json` (T-1518, AUTO-06): manifest.json so với bản cài và tag mới nhất, không gọi mạng thật."""

    def drift(self, *args: str) -> tuple[int, dict]:
        with unittest.mock.patch.object(xt, "latest_framework_tag", side_effect=AssertionError("không được gọi mạng")):
            out = io.StringIO()
            with redirect_stdout(out):
                rc = xt.main(["--framework", str(self.fw), "doctor", "--drift", "--json", *args])
        return rc, json.loads(out.getvalue())

    def subjects(self, doc: dict, state: str) -> list[str]:
        return [d["subject"] for d in doc["drift"] if d["state"] == state]

    def test_doctor_drift_clean_install(self):
        rc, doc = self.drift("--latest", "v0.0.1")
        self.assertEqual((rc, doc["ok"], doc["drift"]), (0, True, []))
        self.assertTrue(doc["manifest"])
        self.assertEqual((doc["installed"], doc["latest"]), ("test", "0.0.1"))

    def test_doctor_drift_file_missing_and_modified(self):
        files = json.loads((self.base / ".xtemplates" / "manifest.json").read_text(encoding="utf-8"))["files"]
        gone, edited = sorted(files)[:2]
        (self.base / gone).unlink()
        (self.base / edited).write_text("# tuỳ chỉnh\n", encoding="utf-8")
        rc, doc = self.drift("--latest", "v0.0.1")
        self.assertEqual(rc, 1)
        self.assertEqual(self.subjects(doc, "missing"), [gone])
        self.assertEqual(self.subjects(doc, "modified"), [edited])

    def test_doctor_drift_root_files_modified_is_silent(self):
        """T-1732: file gốc (AGENTS/CLAUDE/PROGRESS/xt.yaml) có hash trong manifest nhưng dự án sửa là chuyện thường —
        không `modified`; vẫn báo `missing` khi mất file."""
        mf = self.base / ".xtemplates" / "manifest.json"
        doc = json.loads(mf.read_text(encoding="utf-8"))
        doc["files"]["AGENTS.md"] = "0" * 64
        doc["files"]["xt.yaml"] = "0" * 64
        mf.write_text(json.dumps(doc), encoding="utf-8")
        (self.base / "xt.yaml").write_text("lint: x\n", encoding="utf-8")
        rc, d = self.drift("--latest", "v0.0.1")
        self.assertEqual((rc, d["ok"]), (0, True))
        self.assertEqual(self.subjects(d, "modified"), [])
        (self.base / "xt.yaml").unlink()
        self.assertEqual(self.subjects(self.drift("--latest", "v0.0.1")[1], "missing"), ["xt.yaml"])

    def test_doctor_drift_manifest_sha256_and_legacy_hex(self):
        """T-1743: manifest dạng mới (`sha256:<hex>`, install.py) không làm `--drift` báo `modified` oan; manifest cũ hex
        trần vẫn đọc được; lệch thật vẫn báo ở cả hai dạng; giá trị không phải chuỗi → `modified`, không lỗi. Cùng luật
        với `install.manifest_hash`."""
        mf = self.base / ".xtemplates" / "manifest.json"
        doc = json.loads(mf.read_text(encoding="utf-8"))
        self.assertEqual([v for v in doc["files"].values() if not v.startswith("sha256:")], [])
        rc, d = self.drift("--latest", "v0.0.1")
        self.assertEqual((rc, d["drift"]), (0, []))
        legacy = {**doc, "files": {rel: install.manifest_hash(v) for rel, v in doc["files"].items()}}
        mf.write_text(json.dumps(legacy), encoding="utf-8")
        rc, d = self.drift("--latest", "v0.0.1")
        self.assertEqual((rc, d["drift"]), (0, []))
        rel = ".claude/hooks/stop-guard.sh"
        (self.base / rel).write_text("# tuỳ chỉnh\n", encoding="utf-8")
        for form in (doc, legacy):
            mf.write_text(json.dumps(form), encoding="utf-8")
            rc, d = self.drift("--latest", "v0.0.1")
            self.assertEqual((rc, d["ok"], self.subjects(d, "modified")), (0, True, [rel]))
        (self.base / rel).write_bytes((ROOT / rel).read_bytes())
        for value in (5, None, ["x"]):
            with self.subTest(value=value):
                mf.write_text(json.dumps({**legacy, "files": {**legacy["files"], rel: value}}), encoding="utf-8")
                self.assertEqual(self.subjects(self.drift("--latest", "v0.0.1")[1], "modified"), [rel])
        h = install.sha256(b"x")
        for value in (h, install.hash_label(h), ""):
            self.assertEqual(xt._manifest_hex(value), install.manifest_hash(value))
        self.assertIsNone(xt._manifest_hex(None))

    def test_doctor_drift_modified_only_is_ok(self):
        files = json.loads((self.base / ".xtemplates" / "manifest.json").read_text(encoding="utf-8"))["files"]
        edited = sorted(files)[0]
        (self.base / edited).write_text("# tuỳ chỉnh\n", encoding="utf-8")
        rc, doc = self.drift("--latest", "v0.0.1")
        self.assertEqual((rc, doc["ok"]), (0, True))
        self.assertEqual(self.subjects(doc, "modified"), [edited])

    def test_doctor_drift_permission_missing(self):
        sp = self.base / ".claude" / "settings.json"
        settings = json.loads(sp.read_text(encoding="utf-8"))
        dropped = settings["permissions"]["deny"].pop(0)
        sp.write_text(json.dumps(settings), encoding="utf-8")
        rc, doc = self.drift("--latest", "v0.0.1")
        self.assertEqual(rc, 1)
        self.assertEqual(self.subjects(doc, "missing"), [f"deny:{dropped}"])

    def test_review173_drift_allow_removed_is_modified(self):
        """PR #173: gỡ rule `allow` của khung là siết quyền — `modified`, không làm `ok` đỏ; thiếu `allow: Bash` thì đỏ."""
        sp = self.base / ".claude" / "settings.json"
        settings = json.loads(sp.read_text(encoding="utf-8"))
        settings["permissions"]["allow"] = [r for r in settings["permissions"]["allow"] if r in ("Bash", "Read")]
        sp.write_text(json.dumps(settings), encoding="utf-8")
        rc, doc = self.drift("--latest", "v0.0.1")
        self.assertEqual((rc, doc["ok"], self.subjects(doc, "missing")), (0, True, []))
        self.assertIn("allow:Edit", self.subjects(doc, "modified"))
        settings["permissions"]["allow"] = ["Read"]
        sp.write_text(json.dumps(settings), encoding="utf-8")
        rc, doc = self.drift("--latest", "v0.0.1")
        self.assertEqual((rc, self.subjects(doc, "missing")), (1, ["allow:Bash"]))

    def test_review173_drift_files_bad_paths_not_read(self):
        """PR #173: manifest trỏ đường tuyệt đối / `..` / không phải file thường → báo lệch, không đọc; băm theo luồng."""
        mp = self.base / ".xtemplates" / "manifest.json"
        manifest = json.loads(mp.read_text(encoding="utf-8"))
        outside = self.tmp / "outside.txt"
        outside.write_text("x", encoding="utf-8")
        (self.base / "adir").mkdir()
        os.symlink(outside, self.base / "alink")
        os.mkfifo(self.base / "afifo")
        bad = {str(outside): "0", "../outside.txt": "0", "adir": "0", "alink": "0", "afifo": "0", "": "0"}
        manifest["files"] = {**manifest["files"], **bad}
        mp.write_text(json.dumps(manifest), encoding="utf-8")
        with unittest.mock.patch.object(Path, "read_bytes", side_effect=AssertionError("không đọc cả file")):
            rc, doc = self.drift("--latest", "v0.0.1")
        self.assertEqual(rc, 1)
        self.assertEqual(sorted(self.subjects(doc, "invalid")), sorted(bad))
        self.assertEqual(self.subjects(doc, "modified"), [])

    def test_review173b_drift_mid_symlink_escape_not_read(self):
        """Review delta PR #173: manifest trỏ qua symlink ở thành phần GIỮA (`d/out -> ngoài`, `d/out/h`) → `invalid`,
        không băm file ngoài dự án."""
        mp = self.base / ".xtemplates" / "manifest.json"
        manifest = json.loads(mp.read_text(encoding="utf-8"))
        outside = self.tmp / "ngoai"
        outside.mkdir()
        (outside / "h").write_text("x", encoding="utf-8")
        (self.base / "d").mkdir()
        os.symlink(outside, self.base / "d" / "out")
        manifest["files"] = {**manifest["files"], "d/out/h": "0"}
        mp.write_text(json.dumps(manifest), encoding="utf-8")
        rc, doc = self.drift("--latest", "v0.0.1")
        self.assertEqual(rc, 1)
        self.assertEqual(self.subjects(doc, "invalid"), ["d/out/h"])  # trước khi sửa: băm file ngoài → `modified`
        self.assertNotIn("d/out/h", self.subjects(doc, "modified"))

    def test_doctor_drift_settings_unreadable_lists_all_rules(self):
        (self.base / ".claude" / "settings.json").write_text("{", encoding="utf-8")
        rc, doc = self.drift("--latest", "v0.0.1")
        self.assertEqual(rc, 1)
        self.assertTrue(all(d["kind"] == "permission" for d in doc["drift"]))
        sp = self.base / ".claude" / "settings.json"
        sp.write_text(json.dumps({"permissions": {"allow": "x", "deny": None}}), encoding="utf-8")
        self.assertEqual(self.drift("--latest", "v0.0.1")[0], 1)

    def test_doctor_drift_docs_missing(self):
        (self.base / "CLAUDE.md").unlink()
        shutil.rmtree(self.base / ".xtemplates" / "framework")
        rc, doc = self.drift("--latest", "v0.0.1")
        self.assertEqual(rc, 1)
        self.assertEqual(self.subjects(doc, "missing"), ["CLAUDE.md", ".xtemplates/framework"])

    def test_doctor_drift_manifest_missing_or_malformed(self):
        mp = self.base / ".xtemplates" / "manifest.json"
        mp.write_text("[]", encoding="utf-8")
        rc, doc = self.drift("--latest", "v0.0.1")
        self.assertEqual(
            (rc, doc["manifest"], self.subjects(doc, "missing")), (1, False, [".xtemplates/manifest.json"])
        )
        mp.write_text(json.dumps({"files": [], "rules": "x"}), encoding="utf-8")
        rc, doc = self.drift("--latest", "v0.0.1")
        self.assertEqual((rc, doc["manifest"], doc["drift"]), (0, True, []))

    def test_doctor_drift_version_outdated_and_failopen(self):
        (self.base / ".xtemplates" / "VERSION").write_text("3.9.0\n", encoding="utf-8")
        rc, doc = self.drift("--latest", "v3.10.0")
        self.assertEqual((rc, doc["installed"], doc["latest"]), (1, "3.9.0", "3.10.0"))
        self.assertEqual(self.subjects(doc, "outdated"), ["3.9.0"])
        for latest in ("v3.9.0", "v3.8.0"):  # bằng hoặc mới hơn tag → không lệch
            self.assertEqual(self.drift("--latest", latest)[0], 0)
        # T-1718: nhãn cài mặc định của install.py có SHA — `fullmatch` từng làm drift không bao giờ báo bản cũ.
        (self.base / ".xtemplates" / "VERSION").write_text("3.10.0 (da64110)\n", encoding="utf-8")
        rc, doc = self.drift("--latest", "v3.11.0")
        self.assertEqual(
            (rc, doc["installed"], self.subjects(doc, "outdated")), (1, "3.10.0 (da64110)", ["3.10.0 (da64110)"])
        )
        self.assertEqual(self.drift("--latest", "v3.10.0")[0], 0)
        (self.base / ".xtemplates" / "VERSION").write_text("3.9.0-rc1\n", encoding="utf-8")
        self.assertEqual(self.drift("--latest", "v3.9.0")[0], 1)  # rc < bản chính
        for bad in ("không-phải-tag", "", "v3.9", "3.9.0x"):  # tag sai dạng → lỗi dùng lệnh, không lặng lẽ bỏ qua
            with self.subTest(bad=bad):
                out, err = io.StringIO(), io.StringIO()
                with redirect_stdout(out), redirect_stderr(err):
                    rc = xt.main(["--framework", str(self.fw), "doctor", "--drift", "--json", "--latest", bad])
                self.assertEqual((rc, out.getvalue()), (2, ""))
                self.assertIn("không phải tag vX.Y.Z", err.getvalue())
        self.assertEqual(xt._drift_version(self.base, "không-phải-tag")[1:], (None, []))  # hàm: tag lạ → không kết luận
        (self.base / ".xtemplates" / "VERSION").write_text("nhãn-lạ", encoding="utf-8")
        self.assertEqual(self.drift("--latest", "v9.9.9")[0], 0)
        (self.base / ".xtemplates" / "VERSION").unlink()
        rc, doc = self.drift("--latest", "v9.9.9")
        self.assertEqual((rc, doc["installed"]), (0, None))

    def test_doctor_drift_latest_from_gh_when_not_given(self):
        (self.base / ".xtemplates" / "VERSION").write_text("3.9.0", encoding="utf-8")
        out = io.StringIO()
        with (
            unittest.mock.patch.object(xt, "latest_framework_tag", return_value=(4, 0, 0)),
            redirect_stdout(out),
        ):
            rc = xt.main(["--framework", str(self.fw), "doctor", "--drift", "--json"])
        self.assertEqual((rc, json.loads(out.getvalue())["latest"]), (1, "4.0.0"))
        with unittest.mock.patch.object(xt, "latest_framework_tag", return_value=None):
            rc, _, _ = self.run_doctor("--drift")
        self.assertEqual(rc, 0)  # không biết tag → fail-open

    def test_doctor_drift_text_output(self):
        files = json.loads((self.base / ".xtemplates" / "manifest.json").read_text(encoding="utf-8"))["files"]
        (self.base / sorted(files)[0]).write_text("x", encoding="utf-8")
        with unittest.mock.patch.object(xt, "latest_framework_tag", return_value=None):
            rc, out, _ = self.run_doctor("--drift")
        self.assertEqual(rc, 0)
        self.assertIn("[file/modified]", out)
        self.assertIn("✓ không lệch đáng kể", out)
        (self.base / "AGENTS.md").unlink()
        with unittest.mock.patch.object(xt, "latest_framework_tag", return_value=None):
            rc, out, _ = self.run_doctor("--drift")
        self.assertEqual(rc, 1)
        self.assertIn("[doc/missing]", out)
        self.assertIn("✗ có lệch", out)

    def test_doctor_drift_hook_events_task_completed_subagent_stop(self):
        self.assertEqual(xt.DOCTOR_HOOK_EVENTS["TaskCompleted"], "warn")
        self.assertEqual(xt.DOCTOR_HOOK_EVENTS["SubagentStop"], "warn")
        sp = self.base / ".claude" / "settings.json"
        settings = json.loads(sp.read_text(encoding="utf-8"))
        del settings["hooks"]["TaskCompleted"], settings["hooks"]["SubagentStop"]
        sp.write_text(json.dumps(settings), encoding="utf-8")
        msgs = [f.msg for f in self.findings(deep=False) if f.code == "hooks" and f.level == "warn"]
        self.assertEqual(len(msgs), 2)
        self.assertTrue(any("TaskCompleted" in m for m in msgs) and any("SubagentStop" in m for m in msgs))


class DoctorHookSiblingTest(unittest.TestCase):
    """File nạp cạnh hook (`$(dirname "$0")/<đường dẫn>`) — ca port từ `tests/xt-doctor.test.ts` của xboss (#664)."""

    PRINT, BROKEN_PY, BROKEN_SH = 'print("hook")\n', "def guard(:\n", "#!/usr/bin/env bash\nif then\n"
    SIBLINGS = {
        "entry.sh": '#!/usr/bin/env bash\n. "$(dirname "$0")/_lib.sh"\npython3 "$(dirname "$0")/guard.py"\n',
        "_lib.sh": '#!/usr/bin/env bash\nprintf "%s" "hook"\n',
        "guard.py": PRINT,
    }

    def run_doctor(self, files: dict[str, str], dirs: tuple[str, ...] = ()) -> list[xt.Finding]:
        with tempfile.TemporaryDirectory() as tmp:
            hooks = Path(tmp) / ".claude" / "hooks"
            hooks.mkdir(parents=True)
            for d in dirs:
                (hooks / d).mkdir(parents=True)
            for name, body in files.items():
                (hooks / name).parent.mkdir(parents=True, exist_ok=True)
                (hooks / name).write_text(body, encoding="utf-8")
            settings = {"PreToolUse": [{"hooks": [{"type": "command", "command": "bash .claude/hooks/entry.sh"}]}]}
            return xt._doctor_hook_files(Path(tmp), settings, deep=True)

    def assert_error(self, found: list[xt.Finding], name: str, text: str) -> None:
        self.assertEqual(len(found), 1, found)
        self.assertEqual((found[0].code, found[0].level), ("hooks", "error"))
        self.assertIn(f".claude/hooks/{name}", found[0].msg)
        self.assertIn(text, found[0].msg)

    def hook(self, path: str) -> str:
        return f'#!/usr/bin/env bash\npython3 "$(dirname "$0")/{path}"\n'

    def test_root_made_of_dots_is_not_a_sibling(self):
        for line in (
            '"$(dirname "$0")/."',
            '"${CLAUDE_PROJECT_DIR:-$(dirname "$0")/../..}"',
            '"$(dirname "$0")//.//..///.."',
        ):
            with self.subTest(line=line):
                self.assertEqual(self.run_doctor({"entry.sh": f"#!/usr/bin/env bash\nROOT={line}\n"}), [])

    def test_lib_and_guard_present_missing_or_broken(self):
        self.assertEqual(self.run_doctor(self.SIBLINGS), [])
        for name, broken in (("_lib.sh", self.BROKEN_SH), ("guard.py", self.BROKEN_PY)):
            with self.subTest(name=name):
                files = {k: v for k, v in self.SIBLINGS.items() if k != name}
                self.assert_error(self.run_doctor(files), name, "file không có")
                self.assert_error(self.run_doctor({**self.SIBLINGS, name: broken}), name, "lỗi cú pháp")

    def test_hidden_and_path_siblings(self):
        cases = [
            (".guard.py", ".guard.py"),
            ("./guard.py", "guard.py"),
            (".//guard.py", "guard.py"),
            ("/guard.py", "guard.py"),
            ("nested/guard.py", "nested/guard.py"),
            ("nested//guard.py", "nested/guard.py"),
            ("../guard.py", "../guard.py"),
        ]
        for path, file in cases:
            with self.subTest(path=path):
                self.assertEqual(self.run_doctor({"entry.sh": self.hook(path), file: self.PRINT}), [])
                self.assert_error(self.run_doctor({"entry.sh": self.hook(path)}), path, "file không có")
                found = self.run_doctor({"entry.sh": self.hook(path), file: self.BROKEN_PY})
                self.assert_error(found, path, "lỗi cú pháp")

    def test_trailing_slash_is_not_the_file(self):
        for path in ("guard.py/", "guard.py/."):
            with self.subTest(path=path):
                found = self.run_doctor({"entry.sh": self.hook(path), "guard.py": self.PRINT})
                self.assert_error(found, path, "file không có")

    def test_parent_hops_need_real_intermediate_dirs(self):
        found = self.run_doctor({"entry.sh": self.hook("missing/../guard.py"), "guard.py": self.PRINT})
        self.assert_error(found, "missing/../guard.py", "file không có")
        ok = {"entry.sh": self.hook("nested/../guard.py"), "guard.py": self.PRINT}
        self.assertEqual(self.run_doctor(ok, ("nested",)), [])
        broken = {"entry.sh": self.hook("nested/../guard.py"), "guard.py": self.BROKEN_PY}
        self.assert_error(self.run_doctor(broken, ("nested",)), "nested/../guard.py", "lỗi cú pháp")
        self.assert_error(self.run_doctor({"entry.sh": self.hook("missing/..")}), "missing/..", "file không có")

    def test_direct_settings_hook_missing_or_broken(self):
        self.assert_error(self.run_doctor({}), "entry.sh", "file không có")
        self.assert_error(self.run_doctor({"entry.sh": self.BROKEN_SH}), "entry.sh", "lỗi cú pháp")


if __name__ == "__main__":
    unittest.main()
