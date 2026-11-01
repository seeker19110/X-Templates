"""Workflow mẫu cho dự án đích (`framework/templates/ci.yml`, `secret-scan.yml` — `install.py --with-github` chép vào
`.github/workflows/`) và các task CI của `dev-task.sh`: không phụ thuộc stack, 3 job `gate` · `e2e` · `quality` tổng hợp
(ADR-0039, WF-CI-001, WF-CI-024, WF-CI-025), qua được `xt.py ci-check`."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from typing import Dict

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import install
import xt
from test_ci import ci_jobs, flow_list, job_key, matrix_shards

TEMPLATES = ROOT / "framework" / "templates"
CI = TEMPLATES / "ci.yml"
SCAN = TEMPLATES / "secret-scan.yml"
PR_TITLE = TEMPLATES / "pr-title.yml"
DEV_TASK = "bash .xtemplates/scripts/dev-task.sh"  # đường dẫn ở dự án đích (install.py chép scripts vào .xtemplates/)
SETUP = f"run: {DEV_TASK} setup\n"
# Dòng YAML khối đơn giản mà mẫu dùng: comment, `khoá:`/`khoá: giá trị`, `- khoá: giá trị`, `- giá trị`.
YAML_LINE_RE = re.compile(r"^(?: {2})*(?:#.*|(?:- )?[A-Za-z0-9_.-]+:(?: .*)?|- \S.*)$")
BLOCK_RE = re.compile(r":\s*\|\s*$")


def heredoc_python(body: str) -> str:
    """Mã Python trong `python3 - <<'PY' … PY` cuối cùng của thân job (bỏ thụt lề YAML)."""
    found = re.findall(r"python3 - <<'PY'\n(.*?)\n\s*PY\n", body, re.S)
    assert found, "không thấy heredoc python"
    return textwrap.dedent(found[-1])


def step_run(body: str, name_prefix: str) -> str:
    """Script `run: |` của bước có `name:` bắt đầu bằng `name_prefix` (bỏ thụt lề YAML)."""
    m = re.search(
        rf"^      - name: {re.escape(name_prefix)}.*?^        run: \|\n(.*?)(?=^      - |\Z)", body, re.S | re.M
    )
    assert m, f"không thấy bước {name_prefix!r}"
    return textwrap.dedent(m.group(1))


def step_index(body: str, run: str) -> int:
    return body.index(f"run: {run}\n")


class CiTemplateTest(unittest.TestCase):
    """ADR-0039: mẫu CI dự án đích còn đúng 3 job — `gate` · `e2e` · `quality` (gom, kèm bước protection-guard)."""

    def setUp(self):
        self.text = CI.read_text(encoding="utf-8")
        self.jobs: Dict[str, str] = ci_jobs(self.text)

    def test_three_jobs_and_check_names(self):
        self.assertEqual(list(self.jobs), ["gate", "e2e", "quality"])
        # Gate của T-1851 đếm dòng `  khoá:` thụt 2 — `on:` viết dạng flow để chỉ job khớp.
        self.assertEqual(len(re.findall(r"(?m)^  [a-z0-9-]*:$", self.text)), 3)
        self.assertNotIn("deploy", self.text)  # CD không thuộc mẫu (D-117)
        for gone in ("build", "typecheck", "lint", "test", "coverage", "checks", "protection-guard", "test-plan"):
            with self.subTest(job=gone):
                self.assertNotIn(gone, self.jobs)
                self.assertNotRegex(self.text, rf"(?m)^  {re.escape(gone)}:")
        self.assertEqual(job_key(self.jobs["gate"], "name"), "gate")
        self.assertEqual(job_key(self.jobs["quality"], "name"), "quality")  # tên check = khoá job (khớp ruleset)
        self.assertEqual(job_key(self.jobs["e2e"], "name"), "e2e ${{ matrix.shard }}/${{ strategy.job-total }}")

    def test_quality_aggregates_every_job_always(self):
        q = self.jobs["quality"]
        self.assertEqual(flow_list(job_key(q, "needs")), ["gate", "e2e"])
        self.assertEqual(set(flow_list(job_key(q, "needs"))), set(self.jobs) - {"quality"})  # mọi job khác là job con
        cond = job_key(q, "if")
        self.assertIn("always()", cond)
        self.assertNotIn("cancelled()", cond)
        self.assertIn("RESULTS: ${{ toJSON(needs) }}", q)
        # Bước tổng hợp chạy cả khi bước protection-guard đỏ (log luôn nêu job con nào đỏ) và đứng cuối job.
        agg = q.index("- name: Mọi job con phải `success`")
        self.assertGreater(agg, q.index("protection-guard — ruleset trên nhánh"))
        self.assertIn("if: ${{ always() }}", q[agg:])
        for name in ("gate", "e2e"):
            self.assertEqual(job_key(self.jobs[name], "needs"), "")  # job con chạy cùng lúc, không chờ nhau
            self.assertEqual(job_key(self.jobs[name], "if"), "")  # job bị điều kiện bỏ qua = `skipped` → `quality` đỏ

    def test_quality_script_red_on_any_non_success(self):
        code = heredoc_python(self.jobs["quality"])
        for results, rc in (
            ({"gate": {"result": "success"}, "e2e": {"result": "success"}}, 0),
            ({"gate": {"result": "success"}, "e2e": {"result": "skipped"}}, 1),
            ({"gate": {"result": "cancelled"}}, 1),
            ({"gate": {"result": "failure"}, "e2e": {"result": "success"}}, 1),
            ({"gate": {}}, 1),
            ({}, 1),
        ):
            with self.subTest(results=results):
                env = dict(os.environ, RESULTS=json.dumps(results))
                r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env)
                self.assertEqual(r.returncode, rc, r.stdout + r.stderr)

    def test_gate_job_runs_gate_and_framework_checks_in_order(self):
        """`gate`: require (đỏ sớm, D-096) → setup → `dev-task.sh gate-par` (song song trong job, D-128) → sàn M/L `floor --run`
        → doctor → ci-check (tiêu đề PR đã chuyển sang `pr-title.yml`, T-2401)."""
        body = self.jobs["gate"]
        order = [
            body.index("actions/checkout@"),
            step_index(body, f"{DEV_TASK} require lint test"),
            body.index(SETUP),
            step_index(body, f"{DEV_TASK} gate-par"),
            step_index(body, "python3 .xtemplates/scripts/xt.py floor --run --skip e2e"),  # AUD-XFEAT-020
            step_index(body, "python3 .xtemplates/scripts/xt.py doctor"),
            step_index(body, "python3 .xtemplates/scripts/xt.py ci-check"),
        ]
        self.assertEqual(order, sorted(order))
        self.assertIn("fetch-depth: 0", body)  # doctor: SHA bàn giao là tổ tiên HEAD
        self.assertEqual(body.count(f"{DEV_TASK} gate"), 1)  # đúng một lần, là `gate-par`
        self.assertNotIn(f"run: {DEV_TASK} gate\n", self.text)
        # Coverage: ngưỡng nằm trong `test` mà `gate` chạy — không còn đường shard/combine/artefact trong mẫu.
        for gone in ("test-shard", "test-combine", "test-mode", "upload-artifact", "download-artifact", "XT_MIN_TESTS"):
            self.assertNotIn(gone, self.text)
        code = "\n".join(ln for ln in self.text.splitlines() if not ln.lstrip().startswith("#"))
        self.assertNotRegex(code, r"\b(npm|pip|pytest|go test|cargo|ruff|setup-(node|python|go))\b")  # không theo stack

    def test_pr_title_step(self):
        self.assertNotIn("pull_request.title", self.text)  # không còn ở CI nặng (T-2401)
        text = PR_TITLE.read_text(encoding="utf-8")
        body = ci_jobs(text)["title"]
        self.assertIn("TITLE: ${{ github.event.pull_request.title }}", body)  # qua env, không chèn thẳng vào shell
        self.assertNotIn('${{ github.event.pull_request.title }}"', body)
        self.assertIn("pr_title_check", body)
        self.assertIn("persist-credentials: false", body)
        script = step_run(body, "Tiêu đề PR")
        for title, author, rc in (
            ("feat(ci): gộp job ngắn vào gate", "dev", 0),
            ("fix!: đổi giao ước", "dev", 0),
            ("gộp job", "dev", 1),
            ("feat: " + "x" * 98, "dev", 1),
            ("bất kỳ", "dependabot[bot]", 0),
            ('Revert "feat: x"', "dev", 0),
        ):
            with self.subTest(title=title):
                env = dict(os.environ, TITLE=title, AUTHOR=author)
                r = subprocess.run(
                    ["bash", "-c", script], capture_output=True, text=True, env=env, cwd=tempfile.gettempdir()
                )
                self.assertEqual(r.returncode, rc, r.stdout + r.stderr)

    def test_e2e_single_shard_mode_driven(self):
        e2e = self.jobs["e2e"]
        self.assertEqual(matrix_shards(e2e), ["1"])
        self.assertIn("thêm shard", e2e.lower())
        self.assertIn(f'mode="$({DEV_TASK} e2e-mode)"\n', e2e)  # gán riêng: lỗi dev-task → bước đỏ (set -e)
        self.assertIn("set -euo pipefail", e2e)
        self.assertLess(e2e.index("e2e-mode"), e2e.index(SETUP))
        self.assertIn(f'run: {DEV_TASK} e2e "$SHARD" "$TOTAL"\n', e2e)
        self.assertIn("fail-fast: false", e2e)
        self.assertIn("steps.mode.outputs.mode == 'whole' && matrix.shard == 1", e2e)

    def test_hardening_kept(self):
        """Ghim SHA, quyền tối thiểu, timeout mỗi job, concurrency theo PR, persist-credentials: false, không
        continue-on-error."""
        self.assertRegex(self.text, r"(?m)^permissions:\n  contents: read\n")
        self.assertNotRegex(self.text, r"(?m)^    permissions:")  # không job nào nới quyền
        self.assertIn("group: ${{ github.workflow }}-${{ github.head_ref || github.run_id }}", self.text)
        self.assertIn("cancel-in-progress: ${{ github.event_name == 'pull_request' }}", self.text)
        self.assertNotIn("continue-on-error", self.text)
        for name, body in self.jobs.items():
            with self.subTest(job=name):
                self.assertRegex(job_key(body, "timeout-minutes"), r"^\d+$")
                n = body.count("actions/checkout@")
                self.assertEqual(n, 1)
                self.assertEqual(body.count("persist-credentials: false"), n)
        for ref in re.findall(r"uses: (\S+)", self.text):
            self.assertRegex(ref, r"@[0-9a-f]{40}$")

    def test_protection_guard_step_reads_ruleset(self):
        body = self.jobs["quality"]
        self.assertIn(".github/rulesets/main.json", body)
        self.assertIn("required_status_checks", body)
        self.assertIn('glob.glob(".github/workflows/*.yml")', body)
        self.assertIn("GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}", body)  # chỉ GITHUB_TOKEN (WF-CI-023)

    @unittest.skipIf(shutil.which("bash") is None, "cần bash")
    def test_protection_guard_step_allows_and_denies(self):
        """Chạy thật bước đối chiếu: ruleset mẫu ↔ workflow mẫu → xanh; context không có job → đỏ nêu tên; không có
        ruleset → cảnh báo, xanh."""
        script = step_run(self.jobs["quality"], "protection-guard — required check")
        repo = Path(self.enterContext(tempfile.TemporaryDirectory()))
        (repo / ".github" / "workflows").mkdir(parents=True)
        (repo / ".github" / "rulesets").mkdir()
        for src in (CI, SCAN):
            shutil.copy(src, repo / ".github" / "workflows" / src.name)

        def run() -> subprocess.CompletedProcess:
            return subprocess.run(["bash", "-c", script], capture_output=True, text=True, cwd=repo)

        r = run()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("Không có .github/rulesets/main.json", r.stdout)
        ruleset = repo / ".github" / "rulesets" / "main.json"
        shutil.copy(TEMPLATES / "ruleset-main.json", ruleset)
        r = run()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("OK — mọi required check đều là job có thật.", r.stdout)
        rs = json.loads(ruleset.read_text(encoding="utf-8"))
        status = next(x for x in rs["rules"] if x["type"] == "required_status_checks")["parameters"]
        status["required_status_checks"].append({"context": "checks"})  # job cũ đã gộp vào `gate` (ADR-0039)
        ruleset.write_text(json.dumps(rs), encoding="utf-8")
        r = run()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("::error::Required check 'checks' không khớp job nào", r.stdout)

    def test_ruleset_checks_are_all_provided(self):
        """D-116/D-117/D-122, ADR-0039: ruleset mẫu đòi đúng `quality` + `gitleaks`, cả hai là job có thật."""
        self.assertEqual(install.ruleset_required_checks(), ["quality", "gitleaks"])
        self.assertLessEqual(set(install.ruleset_required_checks()), install.provided_checks())
        self.assertLessEqual({"gate", "quality"}, install.provided_checks())
        self.assertEqual(xt.ci_check_text(SCAN.read_text(encoding="utf-8")), [])
        self.assertEqual(job_key(ci_jobs(SCAN.read_text(encoding="utf-8"))["gitleaks"], "name"), "gitleaks")

    def test_templates_pass_ci_check_and_are_block_yaml(self):
        for path in (CI, SCAN, PR_TITLE):
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                self.assertEqual(xt.ci_check_text(text), [])
                self.assertNotIn("\t", text)
                block = None
                for no, line in enumerate(text.splitlines(), 1):
                    indent = len(line) - len(line.lstrip(" "))
                    if block is not None and (not line.strip() or indent > block):
                        continue
                    block = None
                    if line.strip():
                        self.assertRegex(line, YAML_LINE_RE, f"dòng {no}")
                    if BLOCK_RE.search(line):
                        block = indent
                self.assertRegex(text, r"(?m)^permissions:\n  contents: read\n")
        self.assertIn("\non:\n  push: { branches: [main] }\n", self.text)
        self.assertRegex(
            self.text, r"(?m)^  pull_request: \{ branches: \[main\], types: \[opened, synchronize, reopened\] \}$"
        )

    def test_ci_no_edited_trigger(self):
        """T-2401: sửa tiêu đề/thân PR (`edited`) không chạy lại CI nặng cùng SHA; workflow tiêu đề riêng nghe `edited`."""
        ci_types = [CI, ROOT / ".github" / "workflows" / "ci.yml"]
        for path in ci_types:
            with self.subTest(path=str(path.relative_to(ROOT))):
                self.assertNotRegex(path.read_text(encoding="utf-8"), r"types:\s*\[[^\]]*\bedited\b")
        for path in (PR_TITLE, ROOT / ".github" / "workflows" / "pr-title.yml"):
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=str(path.relative_to(ROOT))):
                self.assertRegex(text, r"types:\s*\[opened, edited, synchronize, reopened\]")
                self.assertRegex(text, r'\[ "\$\{#TITLE\}" -(le|gt) 100 \]')
                self.assertRegex(text, r"(?m)^permissions:\n  contents: read\n")
                self.assertIn("cancel-in-progress: true", text)
                self.assertIn("github.event.pull_request.number", text)
                self.assertEqual(xt.ci_check_text(text), [])
        self.assertNotIn("pull_request.title", (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8"))


@unittest.skipIf(shutil.which("bash") is None, "cần bash")
class DevTaskSetupTest(unittest.TestCase):
    """`dev-task.sh setup`: chạy khoá `setup` của xt.yaml; vắng/rỗng → exit 0; guard cấm → 126; không tự dò."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        (self.tmp / "scripts").mkdir()
        shutil.copy(ROOT / "scripts" / "dev-task.sh", self.tmp / "scripts" / "dev-task.sh")

    def run_setup(self, yaml: str | None, **env: str) -> subprocess.CompletedProcess:
        if yaml is not None:
            (self.tmp / "xt.yaml").write_text(yaml, encoding="utf-8")
        full = dict(os.environ, CLAUDE_PROJECT_DIR=str(self.tmp), **env)
        cmd = ["bash", str(self.tmp / "scripts" / "dev-task.sh"), "setup"]
        return subprocess.run(cmd, capture_output=True, text=True, env=full, cwd="/")

    def test_missing_or_empty_is_skipped(self):
        (self.tmp / "package.json").write_text('{"scripts": {"setup": "touch tu-do"}}', encoding="utf-8")
        for yaml in (None, 'setup: ""\n', "lint: x\n"):
            with self.subTest(yaml=yaml):
                r = self.run_setup(yaml)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertIn("không khai setup", r.stderr)
        self.assertFalse((self.tmp / "tu-do").exists())  # không tự dò script `setup` của package.json

    def test_runs_declared_command_in_project_root(self):
        r = self.run_setup("setup: touch đã-cài && printf ok > đã-cài  # cài phụ thuộc\n")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual((self.tmp / "đã-cài").read_text(encoding="utf-8"), "ok")
        self.assertIn("run [setup]", r.stderr)
        self.assertEqual(self.run_setup("setup: exit 3\n").returncode, 3)
        self.assertNotEqual(self.run_setup("setup: false | cat\n").returncode, 0)  # pipefail

    def test_guard_blocks_setup(self):
        shutil.copy(ROOT / "scripts" / "xt.py", self.tmp / "scripts" / "xt.py")
        (self.tmp / ".claude" / "hooks").mkdir(parents=True)
        shutil.copy(ROOT / ".claude" / "hooks" / "guard.py", self.tmp / ".claude" / "hooks" / "guard.py")
        r = self.run_setup("setup: touch chay && git push origin main\n", XT_GUARD_POLICY="")
        self.assertEqual(r.returncode, 126, r.stderr)
        self.assertFalse((self.tmp / "chay").exists())

    def test_unknown_task_lists_setup(self):
        r = subprocess.run(["bash", str(self.tmp / "scripts" / "dev-task.sh"), "nope"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)
        self.assertIn("|require|setup)", r.stderr)


# (lệnh, là no-op?) — bảng chung cho `is_noop` của dev-task.sh và `xt.gate_noop` (không chứa `'` hay ` #`: nằm trong
# nháy đơn của xt.yaml).
NOOP_TABLE = (
    ("true", True),
    (":", True),
    ("exit", True),
    ("exit 0", True),
    ("echo", True),
    ("echo ok", True),
    ("printf x", True),
    ("echo $HOME", True),
    ("true && true", True),
    (": && :", True),
    ("true; true", True),
    ("true || :", True),
    (" true ;", True),
    ("echo a; exit 0", True),
    ("true&&:", True),
    ("echo go && echo done", True),
    ("echo go && pytest", False),
    ("echo go; pytest -q", False),
    ("printf x || make test", False),
    ("echo x | sh", False),
    ("echo $(pytest)", False),
    ("echo `pytest`", False),
    ("echo a & pytest", False),
    ("true && pytest -q", False),
    ("pytest -q; true", False),
    ("true | pytest", False),
    ("exit 1 && :", False),
    ("truex", False),
    ("echox", False),
    ("pytest -q", False),
)


@unittest.skipIf(shutil.which("bash") is None, "cần bash")
class DevTaskRequireEmptyGateTest(unittest.TestCase):
    """`dev-task.sh require lint test` (bước đầu job `gate` của CI mẫu, D-096): đỏ khi `lint`/`test` rỗng hoặc no-op,
    ở mọi `delivery_phase`; typecheck/build rỗng không chặn."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        (self.tmp / "scripts").mkdir()
        shutil.copy(ROOT / "scripts" / "dev-task.sh", self.tmp / "scripts" / "dev-task.sh")

    def require(self, yaml: str | None, *tasks: str, **env: str) -> subprocess.CompletedProcess:
        if yaml is not None:
            (self.tmp / "xt.yaml").write_text(yaml, encoding="utf-8")
        full = {k: v for k, v in os.environ.items() if k != "GITHUB_ACTIONS"}
        full.update(CLAUDE_PROJECT_DIR=str(self.tmp), **env)
        cmd = ["bash", str(self.tmp / "scripts" / "dev-task.sh"), "require", *tasks]
        return subprocess.run(cmd, capture_output=True, text=True, env=full, cwd="/")

    def test_empty_gate_template_yaml_is_red(self):
        """xt.yaml mẫu (mọi khoá cổng "") → đỏ cả `lint` lẫn `test`, kể cả `delivery_phase: build`."""
        yaml = (TEMPLATES / "xt.yaml").read_text(encoding="utf-8")
        self.assertIn("delivery_phase: build\n", yaml)
        r = self.require(yaml, "lint", "test", GITHUB_ACTIONS="true")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        errors = [ln for ln in r.stdout.splitlines() if ln.startswith("::error::")]
        self.assertEqual(len(errors), 2, r.stdout)
        self.assertIn("'lint:'", errors[0])
        self.assertIn("'test:'", errors[1])
        for stack in ("Node:", "Python:", "Go:"):
            self.assertIn(stack, errors[0])

    def test_empty_gate_lint_and_test_declared_is_green(self):
        r = self.require('lint: ruff check .\ntest: "pytest -q"  # đủ\ntypecheck: ""\nbuild: ""\n', "lint", "test")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("::error::", r.stdout + r.stderr)

    def test_empty_gate_only_lint_is_red(self):
        for yaml in ('lint: ruff check .\ntest: ""\n', "lint: ruff check .\n"):
            with self.subTest(yaml=yaml):
                r = self.require(yaml, "lint", "test", GITHUB_ACTIONS="true")
                self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
                self.assertIn("::error::xt.yaml chưa khai lệnh thật cho 'test'", r.stdout)
                self.assertNotIn("cho 'lint'", r.stdout)

    def test_empty_gate_noop_commands_are_red(self):
        for noop in ("true", ":", "exit 0", "echo ok", "printf x", "  "):
            with self.subTest(noop=noop):
                r = self.require(f"lint: ruff check .\ntest: {noop}\n", "lint", "test")
                self.assertEqual(r.returncode, 1, r.stderr)
                self.assertIn(
                    "ĐỎ: xt.yaml chưa khai lệnh thật cho 'test'", r.stderr
                )  # ngoài Actions: log, không ::error::
                self.assertNotIn("::error::", r.stdout)

    def test_empty_gate_chained_noop_commands_are_red(self):
        """Chuỗi toàn no-op nối bằng `&&`/`;`/`||` vẫn không kiểm gì."""
        for noop in ("true && true", ": && :", "true; true", "true || :", " true ;", "echo a; exit 0", "true&&:"):
            with self.subTest(noop=noop):
                r = self.require(f"lint: ruff check .\ntest: '{noop}'\n", "lint", "test")
                self.assertEqual(r.returncode, 1, r.stderr)
                self.assertIn("ĐỎ: xt.yaml chưa khai lệnh thật cho 'test'", r.stderr)

    def test_empty_gate_chain_with_real_command_is_green(self):
        for cmd in ("true && pytest -q", "pytest -q; true", ": || make test", "true | pytest", "exit 1 && :"):
            with self.subTest(cmd=cmd):
                r = self.require(f"lint: ruff check .\ntest: '{cmd}'\n", "lint", "test")
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertIn(f"require: 'test' = {cmd}", r.stderr)

    def test_noop_parity_with_xt(self):
        """`is_noop` (dev-task.sh) và `xt.gate_noop` cùng kết luận trên một bảng ca; hai chuỗi regex trùng nhau."""
        dev = (ROOT / "scripts" / "dev-task.sh").read_text(encoding="utf-8")
        self.assertIn(f"NOOP_RE='{xt.GATE_NOOP_SEG}'\n", dev)
        for cmd, noop in NOOP_TABLE:
            with self.subTest(cmd=cmd):
                self.assertEqual(xt.gate_noop(cmd), noop)
                r = self.require(f"lint: ruff check .\ntest: '{cmd}'\n", "lint", "test")
                self.assertEqual(r.returncode, 1 if noop else 0, r.stderr)

    def test_empty_gate_detected_command_counts(self):
        """Không có xt.yaml mà tự dò được (Makefile có target) → lệnh thật, xanh; không dò được → đỏ."""
        self.assertEqual(self.require(None, "lint", "test").returncode, 1)
        (self.tmp / "Makefile").write_text("lint:\n\ttrue\ntest:\n\ttrue\n", encoding="utf-8")
        r = self.require(None, "lint", "test")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("require: 'test' = make test", r.stderr)

    def test_empty_gate_needs_task(self):
        r = self.require("lint: x\n")
        self.assertEqual(r.returncode, 2)
        self.assertIn("cần ít nhất một task", r.stderr)


@unittest.skipIf(shutil.which("bash") is None, "cần bash")
class DevTaskCiModeTest(unittest.TestCase):
    """Task CI của dev-task.sh (D-115): test-mode · e2e-mode · e2e."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        (self.tmp / "scripts").mkdir()
        shutil.copy(ROOT / "scripts" / "dev-task.sh", self.tmp / "scripts" / "dev-task.sh")

    def dt(self, yaml: str | None, *args: str, **env: str) -> subprocess.CompletedProcess:
        if yaml is not None:
            (self.tmp / "xt.yaml").write_text(yaml, encoding="utf-8")
        full = {k: v for k, v in os.environ.items() if k not in ("GITHUB_ACTIONS", "XT_SHARD", "GITHUB_SHA")}
        full.update(CLAUDE_PROJECT_DIR=str(self.tmp), **env)
        cmd = ["bash", str(self.tmp / "scripts" / "dev-task.sh"), *args]
        return subprocess.run(cmd, capture_output=True, text=True, env=full, cwd="/")

    def test_test_mode(self):
        three = 'test_list: ls\ntest_unit: run "$1"\ntest_combine: comb  # gộp\n'
        for yaml, want in (
            (None, "whole"),
            (three, "shard"),
            (three.replace("ls", '""'), "whole"),
            (three.replace("comb", "true"), "whole"),
            ("test_list: ls\ntest_unit: x\n", "whole"),
        ):
            with self.subTest(yaml=yaml):
                (self.tmp / "xt.yaml").unlink(missing_ok=True)
                r = self.dt(yaml, "test-mode")
                self.assertEqual((r.returncode, r.stdout), (0, f"{want}\n"), r.stderr)

    def test_e2e_off(self):
        self.assertEqual(self.dt('e2e: ""\n', "e2e-mode").stdout, "off\n")
        self.assertEqual(self.dt("e2e: echo hi\n", "e2e-mode").stdout, "off\n")  # no-op không phải suite
        r = self.dt('e2e: ""\n', "e2e", "1", "2")
        self.assertEqual(r.returncode, 0)
        self.assertIn("e2e: chưa khai 'e2e'", r.stderr)

    def test_e2e_sharded(self):
        sharded = 'e2e_setup: touch cai-dat\ne2e: printf "%s;" "$XT_SHARD" >> chay\n'
        self.assertEqual(self.dt(sharded, "e2e-mode").stdout, "shard\n")
        for i in ("1", "2"):
            self.assertEqual(self.dt(sharded, "e2e", i, "2").returncode, 0)
        self.assertEqual(self.dt(sharded, "e2e").returncode, 0)  # agent chạy tay: cả suite
        self.assertEqual((self.tmp / "chay").read_text(encoding="utf-8"), "1/2;2/2;1/1;")
        self.assertTrue((self.tmp / "cai-dat").exists())
        for bad in (("3", "2"), ("0", "1"), ("a", "1")):
            with self.subTest(bad=bad):
                self.assertEqual(self.dt(sharded, "e2e", *bad).returncode, 2)

    def test_e2e_whole_runs_once(self):
        whole = "e2e: printf x | tee -a ca-suite\n"
        self.assertEqual(self.dt(whole, "e2e-mode").stdout, "whole\n")
        r = self.dt(whole, "e2e", "2", "2")
        self.assertEqual(r.returncode, 0)
        self.assertIn("shard này bỏ qua", r.stderr)
        self.assertEqual(self.dt(whole, "e2e", "1", "2").returncode, 0)
        self.assertEqual((self.tmp / "ca-suite").read_text(encoding="utf-8"), "x")  # không chạy trùng cả suite
        self.assertEqual(self.dt("e2e: exit 4\n", "e2e").returncode, 4)
        self.assertEqual(self.dt('e2e_setup: "false"\ne2e: touch x\n', "e2e").returncode, 1)
        self.assertFalse((self.tmp / "x").exists())

    def test_guard_blocks_e2e(self):
        """LOOP-STOP-027: lệnh `e2e` bị guard cấm → 126, không chạy cả `e2e_setup`."""
        shutil.copy(ROOT / "scripts" / "xt.py", self.tmp / "scripts" / "xt.py")
        (self.tmp / ".claude" / "hooks").mkdir(parents=True)
        shutil.copy(ROOT / ".claude" / "hooks" / "guard.py", self.tmp / ".claude" / "hooks" / "guard.py")
        yaml = "e2e_setup: touch cai\ne2e: touch d && git push origin main\n"
        r = self.dt(yaml, "e2e", XT_GUARD_POLICY="")
        self.assertEqual(r.returncode, 126, r.stderr)
        self.assertFalse((self.tmp / "cai").exists())
        self.assertFalse((self.tmp / "d").exists())


if __name__ == "__main__":
    unittest.main()
