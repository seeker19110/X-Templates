#!/usr/bin/env python3
"""install.py — cài khung X-Templates vào một dự án đích (mọi hệ điều hành, chỉ cần Python >= 3.11).

Kết quả trong dự án đích:
  .xtemplates/framework/        bản sao thư viện yêu cầu (chỉ đọc; cập nhật bằng cách chạy lại install)
  .xtemplates/research/         bản nghiên cứu nền mà module trích dẫn
  .xtemplates/scripts/xt.py     công cụ compose / blueprint-status / loop
  .xtemplates/scripts/dev-task.sh
  .xtemplates/VERSION           SHA/nhãn phiên bản khung đã cài
  .xtemplates/manifest.json     hash file harness/gốc/GitHub + rule do khung đặt (chỉ gỡ `ask` có trong đây) + chính sách (REC-09)
                                — hash dạng `sha256:<hex>` (cả `harness.sha256.json`); đọc nhận cả hex trần của bản cũ
  .claude/settings.json, hooks/, skills/, agents/   harness (COPY-IF-ABSENT: không đè file đã có; bản mới ghi .xtemplates-new)
  .github/rulesets/main.json, pull_request_template.md, dependabot.yml,
  .github/workflows/{ci,secret-scan,merge-gate,pr-steward}.yml   chỉ khi --with-github (copy-if-absent, hash vào manifest)
  AGENTS.md, CLAUDE.md, PROGRESS.md, xt.yaml       từ framework/templates (copy-if-absent, bỏ frontmatter YAML; mẫu bọc ```markdown thì lấy phần trong)

File đã có mà khác bản khung (mọi nhóm): còn đúng hash lần cài trước → cập nhật tại chỗ; dự án đã sửa mà mẫu không đổi từ lần
cài trước → `kept-own` (im lặng); dự án đã sửa và mẫu đổi (hoặc chưa biết hash) → `.xtemplates-new`, ghi hash mẫu MỚI nên chỉ
gộp tay một lần mỗi lần mẫu đổi (D-114). File gốc: hash là mẫu đã bỏ frontmatter, TRƯỚC khi thay SHA HEAD (PROGRESS.md); cài
từ bản chưa có hash file gốc → suy từ `.xtemplates/framework/templates/` cũ; `xt.yaml` của dự án nhận khoá mới của mẫu dạng
chú thích. Nâng bản (`.xtemplates/VERSION` cũ đọc được X.Y.Z) → in mệnh đề "Dự án đích …" của CHANGELOG khung từ bản đó.

Dự án đã cài bản ≤ 2.x (`.xstored/`, `xs.py`, `xs.yaml`, `XS_*`): chạy lại install là chuyển sang tên mới (ADR-0007) —
  giữ manifest hash, đổi `xs.yaml` → `xt.yaml`, xoá bản sao `.xstored/`; file người dùng còn nhắc tên cũ được liệt kê để sửa tay.

Dùng:
  python3 scripts/install.py <thư-mục-dự-án> [--force-harness] [--no-harness] [--with-github] [--label v1.0.0] [--plan]
  --plan: in JSON kế hoạch (quyền thêm/bớt, hook thêm/đổi matcher, file đè/giữ), không ghi gì (REC-09)
  (chạy từ bản clone của X-Templates; hoặc: python3 -c "$(curl ...)" KHÔNG được khuyến khích — tải về, kiểm checksum rồi chạy)
Thoát 0 = ổn; 2 = lỗi tham số.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import unicodedata
from collections import Counter
from collections.abc import Callable
from typing import Any
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent
HARNESS_FILES = ["settings.json"]
HARNESS_DIRS = ["hooks", "skills", "agents"]
ROOT_TEMPLATES = {
    "AGENTS.md": "AGENTS.md",
    "CLAUDE.md": "CLAUDE.md",
    "PROGRESS.md": "PROGRESS.md",
    "xt.yaml": "xt.yaml",
}
# Tên trước 3.0.0 (ADR-0007): dự án đã cài bản ≤ 2.x được chuyển tự động khi chạy lại install.
LEGACY_DIR = ".xstored"
LEGACY_YAML = "xs.yaml"
LEGACY_RE = re.compile(r"\.xstored\b|\bxs\.(?:py|yaml)\b|\bXS_[A-Z]")
# --with-github: hàng rào GitHub mẫu (copy-if-absent), đích → nguồn trong khung. Mọi workflow ở đây KHÔNG phụ thuộc stack
# (AUD-CI-003): `ci.yml` mẫu chạy lệnh của xt.yaml qua `.xtemplates/scripts/dev-task.sh` (job song song + `quality` tổng
# hợp + `protection-guard`, WF-CI-024), `secret-scan.yml` (`gitleaks`), `merge-gate.yml` (ADR-0023) và `pr-steward.yml`
# (ADR-0027) chỉ cần python3 + gh. `dep-audit` phụ thuộc ngôn ngữ — dự án tự viết (cảnh báo khi cài). Mẫu PR, Dependabot,
# CI, quét bí mật lấy từ framework/templates: bản ở `.github/` của khung là của riêng repo khung (module/hồ sơ, pip).
GITHUB_FILES = {
    ".github/rulesets/main.json": ".github/rulesets/main.json",
    ".github/pull_request_template.md": "framework/templates/PULL-REQUEST.md",
    ".github/dependabot.yml": "framework/templates/dependabot.yml",
    ".github/workflows/ci.yml": "framework/templates/ci.yml",
    ".github/workflows/secret-scan.yml": "framework/templates/secret-scan.yml",
    ".github/workflows/merge-gate.yml": ".github/workflows/merge-gate.yml",
    ".github/workflows/pr-steward.yml": ".github/workflows/pr-steward.yml",
}
# Job cấp 1 của workflow (thụt 2) và `name:` của nó (thụt 4) — cùng cách đọc với job `protection-guard`.
WORKFLOW_JOBS_RE = re.compile(r"^jobs:\n(.*)", re.S | re.M)
WORKFLOW_JOB_RE = re.compile(r"^  ([A-Za-z0-9_-]+):\n((?:    .*\n|\n)*)", re.M)
WORKFLOW_NAME_RE = re.compile(r"^    name:\s*(.+?)\s*$", re.M)


def log(msg: str) -> None:
    print(f"[install] {msg}", file=sys.stderr)


def strip_frontmatter(text: str) -> str:
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                return "\n".join(lines[i + 1 :]).lstrip("\n") + "\n"
    return text


def template_body(text: str) -> str:
    """Bỏ frontmatter; mẫu bọc nội dung trong khối ```markdown (PROGRESS.md) thì chỉ lấy phần trong khối."""
    text = strip_frontmatter(text)
    lines = text.splitlines()
    start = next((i for i, ln in enumerate(lines) if ln.strip() == "```markdown"), None)
    if start is None:
        return text
    end = next((i for i in range(start + 1, len(lines)) if lines[i].strip() == "```"), len(lines))
    return "\n".join(lines[start + 1 : end]).strip("\n") + "\n"


def copy_tree_replace(src: Path, dst: Path) -> None:
    """Copy vào thư mục tạm rồi mới thay: lỗi giữa chừng không để dst mất/dở."""
    tmp = dst.with_name(dst.name + ".tmp")
    shutil.rmtree(tmp, ignore_errors=True)
    shutil.copytree(src, tmp, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    if dst.exists():
        shutil.rmtree(dst)
    tmp.rename(dst)


MANIFEST = ".xtemplates/harness.sha256.json"
MANIFEST_V2 = ".xtemplates/manifest.json"  # REC-09: hash file + rule do khung đặt + chính sách


def write_atomic(path: Path, text: str) -> None:
    """Ghi qua tệp tạm cùng thư mục rồi đổi tên — lỗi giữa chừng không để settings/manifest dở (BASE-DATA-009)."""
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# Hash trong manifest ghi dạng `sha256:<hex>`: hex trần sau khoá như `".github/workflows/secret-scan.yml"` khớp rule
# `generic-api-key` của gitleaks (token `[\w.=-]{10,150}` ngay sau dấu phân cách) — `:` không thuộc lớp đó nên tiền tố
# chặn khớp. Trong install.py hash là hex trần; đổi dạng ở ranh giới file: `load_manifest` (nhận cả hex trần của
# manifest cũ) và `write_manifests`; `classify_copy` cũng nhận cả hai dạng.
HASH_PREFIX = "sha256:"


def manifest_hash(value: str) -> str:
    """Hex của một hash trong manifest: bỏ tiền tố `sha256:` nếu có; hex trần (manifest cũ) giữ nguyên. Dùng ở mọi chỗ
    so hash với manifest."""
    return value.removeprefix(HASH_PREFIX)


def hash_label(digest: str) -> str:
    """Dạng ghi vào manifest: `sha256:<hex>` — giá trị đã có tiền tố không bị nhân đôi."""
    return HASH_PREFIX + manifest_hash(digest)


def load_manifest(target: Path) -> dict[str, str]:
    """Đường dẫn → hash hex theo `harness.sha256.json`: `sha256:<hex>` hay hex trần đều về hex (`manifest_hash`); giá
    trị không phải chuỗi bỏ qua như chưa biết hash; file thiếu/hỏng/không phải object → rỗng."""
    try:
        data = json.loads((target / MANIFEST).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {rel: manifest_hash(value) for rel, value in data.items() if isinstance(value, str)}


def load_rules(target: Path) -> dict[str, list[str]]:
    """Rule do khung đặt theo `.xtemplates/manifest.json` (rỗng nếu thiếu/hỏng — khi đó không gỡ `ask` nào, REC-09)."""
    try:
        rules = json.loads((target / MANIFEST_V2).read_text(encoding="utf-8")).get("rules", {})
        return {k: [r for r in rules.get(k, []) if isinstance(r, str)] for k in RULE_KEYS}
    except (OSError, ValueError, AttributeError, TypeError):
        return {k: [] for k in RULE_KEYS}


def source_bytes(src: Path, transform: Callable[[str], str] | None = None) -> bytes:
    """Nội dung file khung sẽ ghi vào dự án (sau biến đổi) — cũng là nội dung được băm vào manifest."""
    data = src.read_bytes()
    return transform(data.decode("utf-8")).encode("utf-8") if transform else data


# Trạng thái ghi hash mẫu vừa đưa vào manifest (harness, file gốc, GitHub): `updated-new` cũng ghi hash mẫu MỚI để lần cài
# sau với mẫu không đổi im lặng (`kept-own`) thay vì gộp tay lại (D-114); `kept-own` giữ hash cũ (= hash mẫu), symlink giữ cũ.
HASHED = ("copied", "updated", "kept", "updated-new")


def classify_copy(
    src: Path,
    dst: Path,
    force: bool = False,
    transform: Callable[[str], str] | None = None,
    installed_hash: str | None = None,
    template_hash: str | None = None,
) -> tuple[str, bytes]:
    """Quyết định (không ghi gì) cho một file khung: ('copied' | 'kept' | 'updated' | 'kept-own' | 'updated-new' |
    'skipped-symlink', nội dung bản khung). `installed_hash` = hash bản khung ghi ở lần cài trước: file còn đúng hash đó
    → `updated`; file dự án đã sửa mà mẫu vẫn đúng hash đó (mẫu không đổi) → `kept-own`, không có gì mới để đưa; mẫu đổi
    hoặc chưa biết hash → `updated-new`. `template_hash` = hash nhận diện mẫu (mặc định hash nội dung sẽ ghi; PROGRESS.md:
    mẫu trước khi thay SHA HEAD); cả hai nhận `sha256:<hex>` lẫn hex trần (`manifest_hash`). Dùng chung cho
    `copy_if_absent` và `--plan` để kế hoạch không lệch hành vi thật."""
    data = source_bytes(src, transform)
    if dst.is_symlink() or dst.with_name(dst.name + ".xtemplates-new").is_symlink():
        return "skipped-symlink", data
    if not dst.exists() or force:
        return "copied", data
    current = dst.read_bytes()
    if current == data:
        return "kept", data
    if installed_hash is None:
        return "updated-new", data
    installed = manifest_hash(installed_hash)
    if sha256(current) == installed:
        return "updated", data
    return ("kept-own" if manifest_hash(template_hash or sha256(data)) == installed else "updated-new"), data


def write_copy(src: Path, dst: Path, status: str, data: bytes) -> None:
    """Thực hiện quyết định của `classify_copy`: `copied`/`updated` ghi bản khung (giữ bit chạy cho `.sh`), `updated-new`
    ghi `<file>.xtemplates-new`, `kept`/`kept-own` không ghi gì; symlink → bỏ qua, không đi theo (AUD-HAR-010)."""
    if status == "skipped-symlink":
        log(f"  ⚠ bỏ qua symlink {dst} (không ghi qua liên kết)")
    elif status == "updated-new":
        dst.with_name(dst.name + ".xtemplates-new").write_bytes(data)
    elif status in ("copied", "updated"):
        dst.write_bytes(data)
        if src.suffix == ".sh":
            dst.chmod(dst.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP)


def copy_if_absent(
    src: Path,
    dst: Path,
    force: bool = False,
    transform: Callable[[str], str] | None = None,
    installed_hash: str | None = None,
) -> str:
    """Trả 'copied' | 'kept' | 'updated' | 'kept-own' | 'updated-new' | 'skipped-symlink'.

    Không bao giờ đè file người dùng đã sửa (trừ force). File còn đúng hash bản khung đã cài lần trước
    (`installed_hash`, người dùng chưa sửa) thì cập nhật tại chỗ — bản sửa hook tới được dự án đã cài (AUD-HAR-004).
    Đích là symlink → bỏ qua, không đi theo (AUD-HAR-010).
    """
    dst.parent.mkdir(parents=True, exist_ok=True)
    status, data = classify_copy(src, dst, force, transform, installed_hash)
    write_copy(src, dst, status, data)
    return status


# Luật `ask` mặc định của khung cũ (≤ ADR-0017); ADR-0018 bỏ hỏi người. REC-09: chỉ gỡ khi manifest.json chứng minh khung
# đã đặt; chuỗi trùng mà không có nguồn gốc là rule của dự án → giữ và báo (danh sách này chỉ dùng để báo).
OLD_FRAMEWORK_ASK = {"Bash(git merge *)", "Bash(git rebase *)", "Bash(gh release *)", "Bash(npm publish*)"}
OLD_FRAMEWORK_ASK |= {"Bash(docker push *)"}
RULE_KEYS = ("allow", "ask", "deny")


def merge_permissions(
    ours: dict[str, Any], theirs: dict[str, Any], prov: dict[str, list[str]] | None = None
) -> dict[str, list[str]]:
    """ADR-0018: `allow` có `Bash`, thêm `deny` của khung còn thiếu; gỡ `ask` mà manifest (`prov`) chứng minh do khung đặt
    và khung không còn đặt. Trả báo cáo `allow_add`/`deny_add`/`ask_remove`/`ask_unproven` (tổng độ dài = số thay đổi)."""
    src, perms = ours.get("permissions", {}), theirs.setdefault("permissions", {})
    report: dict[str, list[str]] = {"allow_add": [], "deny_add": [], "ask_remove": [], "ask_unproven": []}
    for key in ("allow", "deny"):
        rules = perms.setdefault(key, [])
        missing = [r for r in src.get(key, []) if r not in rules and (key == "deny" or r == "Bash")]
        rules.extend(missing)
        report[f"{key}_add"] = missing
    ask = perms.get("ask", [])
    now = set(src.get("ask", []))
    proven = set((prov or {}).get("ask", [])) - now
    report["ask_remove"] = [r for r in ask if r in proven]
    report["ask_unproven"] = [r for r in ask if r in OLD_FRAMEWORK_ASK and r not in proven and r not in now]
    if report["ask_remove"]:
        perms["ask"] = [r for r in ask if r not in proven]
    return report


def _sync_matcher(theirs: list[dict[str, Any]], entry: dict[str, Any], cmds: set[object]) -> list[dict[str, Any]]:
    """Hook của khung đã đăng ký mà matcher cũ (vd pre-mcp-guard thêm tool ghi PR — D-057): cập nhật matcher của mục
    CHỈ gồm lệnh của khung; mục dự án gộp thêm lệnh riêng thì giữ nguyên (gộp tay). Trả danh sách mục đã đổi."""
    changed = []
    for e in theirs:
        mine = {h.get("command") for h in e.get("hooks", [])}
        if mine and mine <= cmds and "matcher" in entry and e.get("matcher") != entry["matcher"]:
            changed.append({"matcher_from": e.get("matcher"), "matcher_to": entry["matcher"]})
            e["matcher"] = entry["matcher"]
    return changed


def _sync_on_failure(theirs: list[dict[str, Any]], entry: dict[str, Any]) -> list[dict[str, Any]]:
    """`onFailure` khung đặt cho handler (LOOP-DESIGN-010: guard PreToolUse lỗi/hết giờ thì chặn — T-1514) mà handler
    cùng lệnh ở dự án chưa có → thêm; giá trị dự án đã tự đặt giữ nguyên. Trả danh sách handler đã đổi."""
    want = {h.get("command"): h["onFailure"] for h in entry.get("hooks", []) if "onFailure" in h}
    changed = []
    for h in (h for e in theirs for h in e.get("hooks", [])):
        if h.get("command") in want and "onFailure" not in h:
            h["onFailure"] = want[h["command"]]
            changed.append({"command": h["command"], "onFailure": h["onFailure"]})
    return changed


def _merge_hook_events(
    ours: dict[str, Any], theirs: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Gộp `hooks` của khung vào `theirs` (giữ hook riêng); trả (mục thêm, mục đổi matcher/`onFailure`), mỗi mục kèm
    `event`."""
    hooks = theirs.setdefault("hooks", {})
    added: list[dict[str, Any]] = []
    synced: list[dict[str, Any]] = []
    for event, entries in ours.get("hooks", {}).items():
        have = {h.get("command") for e in hooks.get(event, []) for h in e.get("hooks", [])}
        for entry in entries:
            cmds = [h.get("command") for h in entry.get("hooks", [])]
            if not any(c in have for c in cmds):
                hooks.setdefault(event, []).append(entry)
                added.append({"event": event, "matcher": entry.get("matcher"), "commands": cmds})
            else:
                synced += [
                    {"event": event, "commands": cmds, **m}
                    for m in _sync_matcher(hooks.get(event, []), entry, set(cmds))
                    + _sync_on_failure(hooks.get(event, []), entry)
                ]
    return added, synced


def settings_changes(ours: dict[str, Any], theirs: dict[str, Any], prov: dict[str, list[str]]) -> dict[str, Any]:
    """Gộp `ours` vào `theirs` tại chỗ (bộ nhớ) và trả báo cáo: `permissions`, `hooks_added`, `hooks_matcher_updated`,
    `changes` (tổng số thay đổi; 0 = không cần ghi)."""
    added, synced = _merge_hook_events(ours, theirs)
    perms = merge_permissions(ours, theirs, prov)
    total = len(added) + len(synced) + sum(len(perms[k]) for k in ("allow_add", "deny_add", "ask_remove"))
    return {"permissions": perms, "hooks_added": added, "hooks_matcher_updated": synced, "changes": total}


def read_settings_pair(src: Path, dst: Path) -> tuple[dict[str, Any], dict[str, Any]] | str:
    """(settings khung, settings dự án) hoặc 'skipped-symlink' | 'invalid-json' (đã log lý do)."""
    if dst.is_symlink():
        log(f"  ⚠ bỏ qua symlink {dst}")
        return "skipped-symlink"
    try:
        return json.loads(src.read_text(encoding="utf-8")), json.loads(dst.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        log(
            f"  ⚠ {dst}: không đọc được JSON ({exc}) — HOOK CHƯA ĐĂNG KÝ, gộp tay từ .claude/settings.json.xtemplates-new"
        )
        return "invalid-json"


def merge_hooks(
    src: Path, dst: Path, prov: dict[str, list[str]] | None = None, report: dict[str, Any] | None = None
) -> str:
    """settings.json của dự án đã có: thêm khoá `hooks` của khung còn thiếu (giữ hook riêng) và gộp quyền theo
    ADR-0018 (`merge_permissions`; quyền riêng của dự án giữ nguyên). `prov` = rule khung đã đặt (manifest.json);
    `report` (nếu truyền) được điền báo cáo `settings_changes`.

    Trước đây file có sẵn chỉ sinh `.xtemplates-new` nên hook đã copy mà không chạy (AUD-HAR-003).
    """
    pair = read_settings_pair(src, dst)
    if isinstance(pair, str):
        return pair
    ours, theirs = pair
    rep = settings_changes(ours, theirs, prov or {})
    if report is not None:
        report.update(rep)
    if not rep["changes"]:
        return "kept"
    write_atomic(dst, json.dumps(theirs, ensure_ascii=False, indent=2) + "\n")
    return "merged-hooks"


def source_version() -> str:
    """Nội dung `VERSION` của bản khung đang cài ('unknown' nếu thiếu)."""
    return (SRC / "VERSION").read_text(encoding="utf-8").strip() if (SRC / "VERSION").exists() else "unknown"


def framework_label(explicit: str | None) -> str:
    """Nhãn ghi vào .xtemplates/VERSION: --label, hoặc '<VERSION> (<git sha>)' của bản khung đang cài."""
    if explicit:
        return explicit
    version = source_version()
    try:
        r = subprocess.run(
            ["git", "-C", str(SRC), "rev-parse", "--short", "HEAD"], capture_output=True, text=True, timeout=10
        )
        if r.returncode == 0 and r.stdout.strip():
            return f"{version} ({r.stdout.strip()})"
    except (OSError, subprocess.TimeoutExpired):
        pass
    return version


def target_error(target: Path) -> str | None:
    """Lý do không cài được vào `target` (None nếu hợp lệ)."""
    if not target.is_dir():
        return f"✗ không phải thư mục: {target}"
    if target == SRC:
        return "✗ không cài khung vào chính repo khung"
    return None


def install_framework(xt_dir: Path, label: str | None) -> str:
    """Bước 1: framework + research + scripts + VERSION + README vào .xtemplates/ — thay thế toàn bộ (bản chỉ đọc).
    Trả nhãn đã ghi vào VERSION."""
    copy_tree_replace(SRC / "framework", xt_dir / "framework")
    # research/ đi kèm vì module trong framework/ trỏ tới nguồn nghiên cứu bằng đường dẫn tương đối.
    if (SRC / "research").is_dir():
        copy_tree_replace(SRC / "research", xt_dir / "research")
    (xt_dir / "scripts").mkdir(exist_ok=True)
    for f in ("xt.py", "dev-task.sh", "check-links.py"):
        shutil.copy2(SRC / "scripts" / f, xt_dir / "scripts" / f)
    (xt_dir / "scripts" / "dev-task.sh").chmod(0o755)
    version = framework_label(label)
    (xt_dir / "VERSION").write_text(version + "\n", encoding="utf-8")
    (xt_dir / "README.md").write_text(
        "# .xtemplates/\n\nBản sao khung X-Templates (chỉ đọc). Cập nhật: chạy lại `install.py` từ bản khung mới.\n"
        "Ghép blueprint: `python3 .xtemplates/scripts/xt.py compose --profile <p> --scale <S|M|L> --out BLUEPRINT.md`.\n",
        encoding="utf-8",
    )
    log(f"✓ .xtemplates/framework + scripts (phiên bản {version})")
    return version


def our_rules() -> dict[str, list[str]]:
    """Rule `permissions` của settings.json khung (allow/ask/deny)."""
    perms = json.loads((SRC / ".claude" / "settings.json").read_text(encoding="utf-8")).get("permissions", {})
    return {k: list(perms.get(k, [])) for k in RULE_KEYS}


def update_provenance(prov: dict[str, list[str]], report: dict[str, Any]) -> dict[str, list[str]]:
    """Rule do khung đặt sau lần gộp: cũ + vừa thêm (`allow_add`/`deny_add`), bớt `ask` vừa gỡ. Rule người dùng đã có
    sẵn (không do khung thêm) không bao giờ vào danh sách này. Khử trùng giữ thứ tự: rule bị gỡ rồi khung thêm lại ở lần
    cài sau không làm danh sách phình (PR #173)."""
    perms = report.get("permissions", {})
    out = {k: list(dict.fromkeys([*prov.get(k, []), *perms.get(f"{k}_add", [])])) for k in RULE_KEYS}
    out["ask"] = [r for r in out["ask"] if r not in perms.get("ask_remove", [])]
    return out


def install_settings(
    target: Path, force_harness: bool, stats: Counter[str], prov: dict[str, list[str]]
) -> dict[str, list[str]]:
    """settings.json của harness: dự án đã có (không --force-harness) thì gộp khoá hooks, chưa có thì copy.
    Trả rule do khung đặt (ghi vào manifest.json)."""
    settings = target / ".claude" / "settings.json"
    if settings.exists() and not force_harness:
        report: dict[str, Any] = {}
        r = merge_hooks(SRC / ".claude" / "settings.json", settings, prov, report)
        stats[r] += 1
        if r == "merged-hooks":
            log(
                "  .claude/settings.json: đã gộp hooks + quyền của khung (allow Bash, deny, gỡ ask do khung đặt — ADR-0018)"
            )
        unproven = report.get("permissions", {}).get("ask_unproven", [])
        if unproven:
            log(f"  ⚠ giữ `ask` trùng chuỗi rule cũ của khung nhưng manifest không chứng minh khung đặt: {unproven}")
        return update_provenance(prov, report)
    r = copy_if_absent(SRC / ".claude" / "settings.json", settings, force_harness)
    stats[r] += 1
    return our_rules() if r == "copied" else prov


def harness_sources() -> list[Path]:
    """File harness của khung cần copy ngoài settings.json: HARNESS_FILES khác settings + mọi file trong HARNESS_DIRS."""
    sources = [SRC / ".claude" / f for f in HARNESS_FILES if f != "settings.json"]
    for d in HARNESS_DIRS:
        sources += [p for p in sorted((SRC / ".claude" / d).rglob("*")) if p.is_file() and "__pycache__" not in p.parts]
    return sources


def copy_harness_files(
    target: Path, force_harness: bool, manifest: dict[str, str], stats: Counter[str]
) -> dict[str, str]:
    """Copy-if-absent từng file harness; trả manifest mới: hash bản khung vừa đưa (`HASHED`, kể cả `.xtemplates-new`),
    giữ hash cũ khi `kept-own`/symlink."""
    new_manifest: dict[str, str] = {}
    for src in harness_sources():
        rel = src.relative_to(SRC).as_posix()
        r = copy_if_absent(src, target / rel, force_harness, installed_hash=manifest.get(rel))
        stats[r] += 1
        if r in HASHED:
            new_manifest[rel] = sha256(src.read_bytes())
        elif rel in manifest:
            new_manifest[rel] = manifest[rel]
    return new_manifest


def write_manifests(target: Path, files: dict[str, str], rules: dict[str, list[str]]) -> None:
    """Ghi `harness.sha256.json` (hash file) và `manifest.json` (hash file + rule khung đặt + chính sách, REC-09); mọi
    hash ghi dạng `sha256:<hex>` (`hash_label`), kể cả hash hex trần giữ lại từ manifest cũ."""
    labelled = {rel: hash_label(digest) for rel, digest in files.items()}
    write_atomic(target / MANIFEST, json.dumps(labelled, indent=2, sort_keys=True) + "\n")
    doc = {"schema": 1, "files": labelled, "rules": rules, "policy": {"ask_removal": "manifest-only"}}
    write_atomic(target / MANIFEST_V2, json.dumps(doc, indent=2, sort_keys=True) + "\n")


def install_harness(target: Path, force_harness: bool) -> None:
    """Bước 2: harness .claude/ — copy-if-absent, ghi manifest hash (+ manifest.json có rule khung), báo thống kê."""
    stats: Counter[str] = Counter()
    manifest = load_manifest(target)
    rules = install_settings(target, force_harness, stats, load_rules(target))
    new_manifest = copy_harness_files(target, force_harness, manifest, stats)
    # Hash file `.github/` (--with-github) và file gốc (bước sau ghi lại) giữ qua bước này: lần sau file chưa sửa vẫn
    # được cập nhật tại chỗ.
    new_manifest.update({k: v for k, v in manifest.items() if k in GITHUB_FILES or k in ROOT_TEMPLATES})
    write_manifests(target, new_manifest, rules)
    log("✓ .claude/: " + " · ".join(f"{k} {v}" for k, v in sorted(stats.items())))
    if stats.get("updated-new"):
        log(
            "  ⚠ có file .xtemplates-new: file sẵn có của dự án khác bản khung — so sánh và gộp tay; hook/settings chưa "
            "gộp thì hàng rào của khung có thể không chạy (`xt.py doctor` báo lỗi)"
        )


def root_template_jobs(target: Path) -> list[tuple[str, Path, Callable[[str], str]]]:
    """(tên, mẫu nguồn, hàm biến đổi) của file gốc từ framework/templates có mặt trong khung."""
    jobs: list[tuple[str, Path, Callable[[str], str]]] = []
    for name, tmpl in ROOT_TEMPLATES.items():
        tsrc = SRC / "framework" / "templates" / tmpl
        if tsrc.exists():
            body = template_body if name != "PROGRESS.md" else lambda t: progress_with_head(template_body(t), target)
            jobs.append((name, tsrc, body))
    return jobs


def root_template_hash(tmpl: Path) -> str:
    """Hash nhận diện mẫu file gốc (ghi vào manifest): mẫu đã bỏ frontmatter, TRƯỚC khi thay SHA HEAD — PROGRESS.md mang
    SHA đổi theo HEAD của dự án, không được làm mẫu "đổi" (D-114)."""
    return sha256(source_bytes(tmpl, template_body))


def infer_root_hashes(target: Path) -> dict[str, str]:
    """Hash mẫu file gốc của bản khung ĐÃ cài, suy từ `.xtemplates/framework/templates/` cũ — gọi trước `install_framework`.
    Chỉ dùng để phân loại file gốc mà manifest chưa có hash (cài từ trước khi có hash file gốc), không ghi vào manifest.
    Mẫu cũ thiếu/symlink/không đọc được → bỏ qua (coi như chưa biết hash)."""
    old = target / ".xtemplates" / "framework" / "templates"
    out: dict[str, str] = {}
    for name, tmpl in ROOT_TEMPLATES.items():
        p = old / tmpl
        if p.is_file() and not p.is_symlink():
            try:
                out[name] = root_template_hash(p)
            except (OSError, UnicodeDecodeError):
                pass  # không suy được → phân loại như chưa biết hash (`.xtemplates-new` khi khác mẫu)
    return out


YAML_MERGE = ("kept-own", "updated-new")  # xt.yaml của dự án: nối khoá mới của mẫu dạng chú thích
ROOT_MESSAGES = {
    # AUD-HAR-052: file của dự án (không phải bản khung cũ) — chỉ nói điều đúng
    "updated-new": "giữ file của dự án; mẫu khung ở {name}.xtemplates-new — gộp phần của khung vào",
    "kept-own": "kept-own — file của dự án, mẫu khung không đổi từ lần cài trước (không có gì mới để gộp)",
}
YAML_KEY_RE = re.compile(r"^([A-Za-z_][\w-]*):")  # dòng khoá cấp 1 của mẫu xt.yaml (cùng dạng `YAML_KEY_RE` của xt.py)
YAML_HAS_KEY_RE = re.compile(r"^(?:#[ \t]*)?([A-Za-z_][\w-]*):", re.M)  # dự án đã có: `khoá:` hoặc `# khoá:`
YAML_MARKER = '# Khoá mới của khung (bản {label}) — bật bằng cách bỏ "# "; vắng khoá = hành vi cũ'


def install_root_templates(target: Path, label: str, inferred: dict[str, str] | None = None) -> None:
    """Bước 3: file gốc từ framework/templates — copy-if-absent, bỏ frontmatter; hash mẫu (`root_template_hash`) vào
    CÙNG map `files` của manifest với harness: chưa sửa → cập nhật tại chỗ; đã sửa mà mẫu không đổi → `kept-own` (im
    lặng); đã sửa và mẫu đổi → `.xtemplates-new` một lần. Manifest chưa có hash file gốc → dùng hash suy từ mẫu cũ
    (`inferred`, chỉ để phân loại). `xt.yaml` của dự án nhận khoá mới của mẫu dạng chú thích (`label`)."""
    manifest = load_manifest(target)
    hints = inferred or {}
    for name, tsrc, body in root_template_jobs(target):
        th = root_template_hash(tsrc)
        r, data = classify_copy(tsrc, target / name, False, body, manifest.get(name, hints.get(name)), th)
        write_copy(tsrc, target / name, r, data)
        log(f"  {name}: " + ROOT_MESSAGES.get(r, r).format(name=name))
        if r != "skipped-symlink":  # `HASHED` ghi hash mẫu mới; `kept-own`: hash mẫu = hash đã cài, ghi lại như giữ
            manifest[name] = th
        if name == "xt.yaml" and r in YAML_MERGE:
            append_yaml_keys(target / name, data.decode("utf-8"), label)
    write_manifests(target, manifest, load_rules(target))


def missing_yaml_keys(template: str, own: str) -> list[tuple[str, str]]:
    """(khoá, dòng mẫu) của khoá cấp 1 trong mẫu xt.yaml mà file của dự án chưa có — không có `khoá:` lẫn `# khoá:`
    (khoá đã nối dạng chú thích ở lần cài trước hay dự án cố ý tắt không nối lại)."""
    have = set(YAML_HAS_KEY_RE.findall(own))
    lines: dict[str, str] = {}
    for line in template.splitlines():
        m = YAML_KEY_RE.match(line)
        if m and m[1] not in have:
            lines.setdefault(m[1], line)
    return list(lines.items())


def read_own_yaml(path: Path) -> str | None:
    """xt.yaml của dự án (UTF-8, bỏ BOM, giữ nguyên xuống dòng); không đọc được → None, đã log (fail-open)."""
    try:
        return path.read_bytes().decode("utf-8-sig")
    except (OSError, UnicodeDecodeError) as exc:
        log(f"  ⚠ xt.yaml: không đọc được ({exc}) — bỏ qua nối khoá mới của khung")
        return None


def yaml_block(own: str, lines: list[str], label: str) -> str:
    """Khối nối cuối xt.yaml: dòng trống ngăn cách, MỘT dòng đánh dấu, rồi `# <dòng mẫu>`; cùng kiểu xuống dòng với file."""
    nl = "\r\n" if "\r\n" in own else "\n"
    lead = "" if not own else nl if own.endswith("\n") else nl + nl
    return lead + nl.join([YAML_MARKER.format(label=label), *(f"# {ln}" for ln in lines)]) + nl


def append_yaml_keys(path: Path, template: str, label: str) -> None:
    """xt.yaml của dự án (`kept-own`/`updated-new`): nối vào cuối khoá có trong mẫu mà dự án chưa có, dạng chú thích —
    vắng khoá = hành vi cũ nên không đổi hành vi; không sửa dòng đã có (ghi nối byte); idempotent (khoá đã nối dạng
    `# khoá:` không nối lại)."""
    own = read_own_yaml(path)
    if own is None:
        return
    missing = missing_yaml_keys(template, own)
    if not missing:
        return
    try:
        with path.open("ab") as fh:
            fh.write(yaml_block(own, [ln for _, ln in missing], label).encode("utf-8"))
    except OSError as exc:
        log(f"  ⚠ xt.yaml: không nối được khoá mới của khung ({exc})")
        return
    keys = ", ".join(k for k, _ in missing)
    log(f'  xt.yaml: nối {len(missing)} khoá mới của khung dạng chú thích ({keys}) — bỏ "# " để bật; vắng = hành vi cũ')


def progress_with_head(text: str, target: Path) -> str:
    """PROGRESS mới cài ghi SHA HEAD thật của dự án (AUD-HAR-053) để `xt.py progress-check` xanh ngay — chỉ khi đích là
    GỐC repo git riêng và đang ở nhánh chính (mẫu cấm SHA của nhánh PR; dự án lồng trong repo cha không lấy HEAD của
    cha — review #97); không thì giữ chỗ trống của mẫu."""
    cmd = ["git", "-C", str(target), "rev-parse", "--show-toplevel", "HEAD", "--abbrev-ref", "HEAD"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10, check=False)
    except (OSError, subprocess.SubprocessError):
        return text
    out = r.stdout.split("\n")
    top, head, branch = (out + ["", "", ""])[:3]
    ok = r.returncode == 0 and Path(top).resolve() == target.resolve() and branch in ("main", "master")
    return text.replace("<SHA đầy đủ>", head) if ok and re.fullmatch(r"[0-9a-f]{40}", head) else text


def ruleset_required_checks() -> list[str]:
    """Tên các required status check trong ruleset mẫu (rỗng nếu không đọc/không có)."""
    try:
        rules = json.loads((SRC / ".github/rulesets/main.json").read_text(encoding="utf-8"))["rules"]
        return [
            c["context"]
            for r in rules
            if r["type"] == "required_status_checks"
            for c in r["parameters"]["required_status_checks"]
        ]
    except (OSError, ValueError, KeyError):
        return []


def workflow_job_names(text: str) -> set[str]:
    """Tên check của các job trong một workflow: `name:` của job, không có thì khoá job (như `protection-guard`)."""
    m = WORKFLOW_JOBS_RE.search(text)
    names: set[str] = set()
    for jm in WORKFLOW_JOB_RE.finditer(m.group(1) if m else ""):
        nm = WORKFLOW_NAME_RE.search(jm.group(2))
        names.add(nm.group(1).strip("\"'") if nm else jm.group(1))
    return names


def provided_checks() -> set[str]:
    """Tên job mà các workflow `--with-github` cung cấp (đọc từ nguồn trong khung)."""
    names: set[str] = set()
    for gh, src in GITHUB_FILES.items():
        if gh.startswith(".github/workflows/"):
            names |= workflow_job_names((SRC / src).read_text(encoding="utf-8"))
    return names


def github_template(src: str) -> Callable[[str], str] | None:
    """Biến đổi mẫu GitHub: mẫu `.md` bỏ frontmatter/lấy khối ```markdown; file khác giữ nguyên."""
    return template_body if src.endswith(".md") else None


def install_github(target: Path) -> None:
    """Bước 3b (--with-github): ruleset mẫu + PR template + Dependabot + workflow CI/quét bí mật/`merge-gate`/
    `pr-steward` (copy-if-absent; file chưa sửa so với lần cài trước thì cập nhật tại chỗ), ghi hash vào manifest, cảnh
    báo required check chưa có job."""
    manifest = load_manifest(target)
    for gh, src in GITHUB_FILES.items():
        tf = github_template(src)
        dst, data = target / gh, source_bytes(SRC / src, tf)
        r = copy_if_absent(SRC / src, dst, False, transform=tf, installed_hash=manifest.get(gh))
        log(f"  {gh}: {r}")
        # Hash ghi luôn là hash MẪU (không bao giờ hash file của người dùng — nếu không lần cài sau coi file đó là "chưa
        # sửa" và đè nó): bản khung thật sự nằm ở đích (`copied`/`updated`/`kept`), hoặc mẫu vừa ra `.xtemplates-new` —
        # lần sau mẫu không đổi thì `kept-own`, không gộp tay lại (D-114).
        if r == "updated-new" or (r in HASHED and dst.read_bytes() == data):
            manifest[gh] = sha256(data)
    write_manifests(target, manifest, load_rules(target))
    # AUD-CI-003: import ruleset khi còn required check chưa có job → mọi PR treo chờ check (và `protection-guard` đỏ)
    checks = [c for c in ruleset_required_checks() if c not in provided_checks()]
    if checks:
        log(
            f"  ⚠ ruleset mẫu đòi required check chưa có job: {', '.join(checks)} — viết job ĐÚNG tên (vd `dep-audit`: "
            "quét lỗ hổng phụ thuộc theo ngôn ngữ của dự án) trước khi import ruleset, hoặc bỏ khỏi "
            ".github/rulesets/main.json; tới lúc đó `protection-guard` đỏ và PR treo chờ check"
        )


def ensure_gitignore(target: Path) -> None:
    """Bước 4: .gitignore thêm `.autopilot/` nếu thiếu (tạo mới nếu chưa có file)."""
    gi = target / ".gitignore"
    line = ".autopilot/"
    if gi.exists():
        if line not in gi.read_text(encoding="utf-8").splitlines():
            with gi.open("a", encoding="utf-8") as fh:
                fh.write(f"\n# X-Templates: trạng thái autopilot cục bộ\n{line}\n")
            log("  .gitignore: thêm .autopilot/")
    else:
        gi.write_text(f"# X-Templates: trạng thái autopilot cục bộ\n{line}\n", encoding="utf-8")
        log("  .gitignore: tạo mới")


def migrate_legacy(target: Path) -> None:
    """Bước 0 (bản ≤ 2.x): giữ manifest hash để hook chưa sửa vẫn cập nhật tại chỗ, xoá bản sao chỉ đọc `.xstored/`
    (cài lại được), đổi `xs.yaml` → `xt.yaml` — dev-task.sh chỉ đọc tên mới, để nguyên thì cổng thành no-op."""
    legacy = target / LEGACY_DIR
    if legacy.is_dir() and not legacy.is_symlink():
        old_manifest = legacy / "harness.sha256.json"
        if old_manifest.is_file() and not (target / MANIFEST).exists():
            shutil.copy2(old_manifest, target / MANIFEST)
        shutil.rmtree(legacy)
        log(f"  {LEGACY_DIR}/ → .xtemplates/ (đã xoá bản sao cũ, giữ manifest hash)")
    old_yaml, new_yaml = target / LEGACY_YAML, target / "xt.yaml"
    if old_yaml.is_file() and not new_yaml.exists():
        old_yaml.rename(new_yaml)
        log(f"  {LEGACY_YAML} → xt.yaml")
    elif old_yaml.is_file():
        log(f"  ⚠ có cả {LEGACY_YAML} và xt.yaml — dev-task.sh chỉ đọc xt.yaml; gộp tay rồi xoá {LEGACY_YAML}")


def legacy_refs(target: Path) -> list[str]:
    """File của dự án còn nhắc tên trước 3.0.0 — copy-if-absent không đè file người dùng nên chỉ báo để sửa tay."""
    candidates = [*target.glob("*.md"), target / "xt.yaml", *(target / ".claude").rglob("*")]
    candidates += (target / ".github" / "workflows").glob("*")
    hits = []
    for p in candidates:
        if not p.is_file():
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if LEGACY_RE.search(text):
            hits.append(p.relative_to(target).as_posix())
    return sorted(hits)


VERSION_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)")  # nhãn VERSION dạng "3.7.1 (9433792)" → (3, 7, 1)
CHANGELOG_HEAD_RE = re.compile(r"^## \[(Unreleased|v?\d+\.\d+\.\d+)\]")
TARGET_STEP = unicodedata.normalize("NFC", "Dự án đích")  # so trên NFC: CHANGELOG gõ dạng tổ hợp (NFD) vẫn khớp


def installed_label(xt_dir: Path) -> str | None:
    """Nhãn `.xtemplates/VERSION` có TRƯỚC lần cài này (None: cài mới hoặc không đọc được)."""
    try:
        return (xt_dir / "VERSION").read_text(encoding="utf-8").strip()
    except (OSError, UnicodeDecodeError):
        return None


def parse_version(label: str | None) -> tuple[int, int, int] | None:
    m = VERSION_RE.match((label or "").strip())
    return (int(m[1]), int(m[2]), int(m[3])) if m else None


def changelog_sections(text: str) -> list[tuple[str, list[str]]]:
    """(tên mục — `Unreleased` hoặc `X.Y.Z`, rỗng với tiêu đề `## ` khác — và các dòng của mục) theo thứ tự CHANGELOG."""
    out: list[tuple[str, list[str]]] = []
    for line in text.splitlines():
        if line.startswith("## "):
            m = CHANGELOG_HEAD_RE.match(line)
            out.append((m[1] if m else "", []))
        elif out:
            out[-1][1].append(line)
    return out


def _block_kind(line: str) -> str:
    """Loại dòng Markdown: `bullet` (`- `), `quote` (`>`), `cont` (thụt lề), `para`; rỗng = dòng trống/tiêu đề (hết khối)."""
    if not line.strip() or line.startswith("#"):
        return ""
    if line.startswith("- "):
        return "bullet"
    if line.startswith(">"):
        return "quote"
    return "cont" if line[:1] in (" ", "\t") else "para"


def text_blocks(lines: list[str]) -> list[list[str]]:
    """Khối của một mục: gạch đầu dòng cùng dòng nối tiếp thụt lề của nó, khối trích dẫn `>` liền nhau, đoạn văn."""
    blocks: list[list[str]] = []
    cur = ""  # loại dòng mở khối đang đọc ("" = không có khối mở)
    for line in lines:
        kind = _block_kind(line)
        if not kind:
            cur = ""
        elif cur and (kind == "cont" or (kind == cur and kind != "bullet")):
            blocks[-1].append(line)
        else:
            blocks.append([line])
            cur = kind
    return blocks


LINE_PREFIX_RE = re.compile(r"^\s*(?:>\s*)*")  # thụt lề + dấu trích dẫn `>` đầu dòng — bỏ khi gộp khối thành một dòng
SENTENCE_END_RE = re.compile(r"\.(?=\s|$)")
QUOTES = "\"'“”‘’«»"  # "Dự án đích" đứng sau dấu nháy là nhắc tên (vd mô tả tính năng này), không phải bước làm tay


def _unbold(text: str) -> str:
    """Bỏ `**` (đậm Markdown) ngoài mã `…`: mệnh đề cắt giữa cặp `**` nên dấu còn lại lẻ; trong mã (glob `**/`) giữ."""
    parts = text.split("`")
    return "`".join(p if i % 2 else p.replace("**", "") for i, p in enumerate(parts))


def _sentence_end(text: str, start: int) -> int:
    """Chỉ số ngay sau dấu chấm hết câu đầu tiên từ `start`: dấu chấm rồi khoảng trắng hoặc hết khối; số thứ tự danh sách
    (`1.`) không phải hết câu; không có → hết khối."""
    for m in SENTENCE_END_RE.finditer(text, start):
        before = text[start : m.start()].split()
        if not (before and before[-1].isdigit()):
            return m.end()
    return len(text)


def step_clauses(block: list[str]) -> list[str]:
    """Mệnh đề bước làm tay của một khối: gộp các dòng thành một (bỏ thụt lề và `>`), rồi lấy từ mỗi "Dự án đích" tới hết
    câu (so trên NFC); lần nhắc tên trong ngoặc (`"Dự án đích"`) bỏ qua."""
    text = unicodedata.normalize("NFC", " ".join(LINE_PREFIX_RE.sub("", ln).strip() for ln in block))
    out: list[str] = []
    i = text.find(TARGET_STEP)
    while i >= 0:
        if i and text[i - 1] in QUOTES:
            i = text.find(TARGET_STEP, i + len(TARGET_STEP))
            continue
        j = _sentence_end(text, i)
        out.append(_unbold(text[i:j]).strip())
        i = text.find(TARGET_STEP, j)
    return out


def upgrade_steps(text: str, since: tuple[int, int, int]) -> list[tuple[str, list[str]]]:
    """(tên mục, mệnh đề "Dự án đích …") của mục `[Unreleased]` và mọi mục `[X.Y.Z]` có bản > `since`, thứ tự CHANGELOG;
    mệnh đề trùng hệt trong cùng mục in một lần."""
    out: list[tuple[str, list[str]]] = []
    for name, lines in changelog_sections(text):
        version = parse_version(name)
        if name != "Unreleased" and (version is None or version <= since):
            continue
        clauses = list(dict.fromkeys(c for block in text_blocks(lines) for c in step_clauses(block)))
        if clauses:
            out.append((name, clauses))
    return out


def report_upgrade_steps(previous: str | None, label: str) -> None:
    """Nâng bản (`previous` = nhãn VERSION trước khi cài, đọc được X.Y.Z): in các bước "Dự án đích" của CHANGELOG khung
    từ bản đó. Cài mới/nhãn lạ → bỏ qua; hạ bản → một dòng; CHANGELOG không đọc được → một dòng, không lỗi (fail-open)."""
    since = parse_version(previous)
    if since is None:
        return
    title = f"Bước làm tay từ CHANGELOG ({previous} → {label}):"
    now = parse_version(source_version())
    if now is not None and now < since:
        log(f"{title} bỏ qua — bản khung {'.'.join(map(str, now))} cũ hơn bản đã cài (hạ bản)")
        return
    try:
        text = (SRC / "CHANGELOG.md").read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        log(f"{title} không đọc được CHANGELOG.md của khung ({exc}) — xem mục 'Dự án đích' ở CHANGELOG bản mới")
        return
    steps = upgrade_steps(text, since)
    if not steps and now == since:  # cài lại cùng bản: im lặng (review #191)
        return
    log(title if steps else f"{title} không có")
    for name, clauses in steps:
        log(f"  [{name}]")
        for clause in clauses:
            log(f"  - {clause}")


def plan_settings(target: Path, force_harness: bool, prov: dict[str, list[str]]) -> dict[str, Any]:
    """Kế hoạch cho .claude/settings.json: quyền thêm/bớt, hook thêm/đổi matcher (không ghi gì)."""
    src, dst = SRC / ".claude" / "settings.json", target / ".claude" / "settings.json"
    if dst.exists() and not force_harness:
        pair = read_settings_pair(src, dst)
        if isinstance(pair, str):
            return {"action": pair}
        rep = settings_changes(pair[0], pair[1], prov)
        action = "merged-hooks" if rep.pop("changes") else "kept"
        return {"action": action, **rep}
    return {"action": classify_copy(src, dst, force_harness)[0]}


PlanJob = tuple[Path, str, bool, Callable[[str], str] | None, str | None]  # nguồn, đích, force, biến đổi, hash mẫu


def plan_entry(target: Path, job: PlanJob, installed_hash: str | None) -> dict[str, Any]:
    """Một file của kế hoạch: {path, action}; `xt.yaml` của dự án (`kept-own`/`updated-new`) kèm `keys_add` — khoá mới
    của mẫu sẽ được nối dạng chú thích (chỉ báo, không ghi)."""
    src, rel, force, tf, template_hash = job
    action, data = classify_copy(src, target / rel, force, tf, installed_hash, template_hash)
    entry: dict[str, Any] = {"path": rel, "action": action}
    if rel == "xt.yaml" and action in YAML_MERGE:
        own = read_own_yaml(target / rel)
        entry["keys_add"] = [k for k, _ in missing_yaml_keys(data.decode("utf-8"), own)] if own is not None else []
    return entry


def plan_files(target: Path, force_harness: bool, no_harness: bool, with_github: bool) -> list[dict[str, Any]]:
    """Hành động dự kiến cho từng file harness/gốc/GitHub: copied | kept | updated | kept-own | updated-new |
    skipped-symlink. Cùng hash như cài thật: manifest, file gốc chưa có hash thì suy từ mẫu cũ (`infer_root_hashes`)."""
    hashes = {**infer_root_hashes(target), **load_manifest(target)}  # manifest thắng hash suy
    jobs: list[PlanJob] = []
    if not no_harness:
        jobs += [(src, src.relative_to(SRC).as_posix(), force_harness, None, None) for src in harness_sources()]
    jobs += [(tsrc, name, False, body, root_template_hash(tsrc)) for name, tsrc, body in root_template_jobs(target)]
    if with_github:
        jobs += [(SRC / gsrc, gh, False, github_template(gsrc), None) for gh, gsrc in GITHUB_FILES.items()]
    return [plan_entry(target, job, hashes.get(job[1])) for job in jobs]


def install_plan(target: Path, force_harness: bool, no_harness: bool, with_github: bool = False) -> int:
    """`--plan`: in JSON kế hoạch (quyền/hook/file) ra stdout, KHÔNG ghi gì vào dự án. Thoát 0; 2 nếu đích không hợp lệ."""
    target = target.resolve()
    error = target_error(target)
    if error:
        log(error)
        return 2
    plan: dict[str, Any] = {
        "schema": 1,
        "target": str(target),
        "framework": {"action": "replace", "path": ".xtemplates/framework"},
        "legacy_migration": (target / LEGACY_DIR).is_dir() or (target / LEGACY_YAML).is_file(),
        "settings": {"action": "skipped"} if no_harness else plan_settings(target, force_harness, load_rules(target)),
        "files": plan_files(target, force_harness, no_harness, with_github),
        "manifest": {
            "path": MANIFEST_V2,
            "present": (target / MANIFEST_V2).is_file(),
            "policy": {"ask_removal": "manifest-only"},
        },
    }
    print(json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def install(target: Path, force_harness: bool, no_harness: bool, label: str | None, with_github: bool = False) -> int:
    target = target.resolve()
    error = target_error(target)
    if error:
        log(error)
        return 2
    xt_dir = target / ".xtemplates"
    previous = installed_label(xt_dir)  # đọc trước khi install_framework ghi nhãn mới
    xt_dir.mkdir(exist_ok=True)

    migrate_legacy(target)
    inferred = infer_root_hashes(target)  # mẫu cũ trong .xtemplates/framework/ — trước khi install_framework thay
    version = install_framework(xt_dir, label)
    if not no_harness:
        install_harness(target, force_harness)
    install_root_templates(target, version, inferred)
    if with_github:
        install_github(target)
    ensure_gitignore(target)
    stale = legacy_refs(target)
    if stale:
        log(
            "  ⚠ còn nhắc tên cũ (.xstored/xs.py/xs.yaml/XS_*) — đổi tay sang .xtemplates/xt.py/xt.yaml/XT_*: "
            + ", ".join(stale)
        )
    report_upgrade_steps(previous, version)

    log(
        "Xong. Bước tiếp: `python3 .xtemplates/scripts/xt.py doctor` (audit khung vừa cài), đọc AGENTS.md, điền xt.yaml, "
        "rồi `python3 .xtemplates/scripts/xt.py list profiles` → compose BLUEPRINT.md."
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Cài khung X-Templates vào dự án đích")
    p.add_argument("target", help="thư mục gốc dự án đích")
    p.add_argument("--force-harness", action="store_true", help="đè .claude/ của dự án bằng bản khung")
    p.add_argument("--no-harness", action="store_true", help="không copy .claude/")
    p.add_argument("--label", help="nhãn phiên bản ghi vào .xtemplates/VERSION (mặc định: git SHA)")
    p.add_argument(
        "--with-github",
        action="store_true",
        help="copy ruleset mẫu, PR template, Dependabot, workflow ci + secret-scan + merge-gate + pr-steward vào .github/ "
        "(không đè)",
    )
    p.add_argument("--plan", action="store_true", help="in JSON kế hoạch (quyền/hook/file) ra stdout, không ghi gì")
    a = p.parse_args(argv)
    if a.plan:
        return install_plan(Path(a.target), a.force_harness, a.no_harness, a.with_github)
    return install(Path(a.target), a.force_harness, a.no_harness, a.label, a.with_github)


if __name__ == "__main__":
    sys.exit(main())
