#!/usr/bin/env python3
"""install.py — cài khung X-Templates vào một dự án đích (mọi hệ điều hành, chỉ cần Python >= 3.11).

Kết quả trong dự án đích:
  .xtemplates/framework/        bản sao thư viện yêu cầu (chỉ đọc; cập nhật bằng cách chạy lại install)
  .xtemplates/research/         bản nghiên cứu nền mà module trỏ tới (chỉ file được trỏ)
  .xtemplates/scripts/xt.py     công cụ compose / blueprint-status / loop
  .xtemplates/scripts/dev-task.sh
  .xtemplates/scripts/{xt_app,app}/  app cục bộ `xt.py app` (ADR-0038)
  .xtemplates/VERSION           SHA/nhãn phiên bản khung đã cài
  .xtemplates/manifest.json     hash file harness/gốc/GitHub + rule do khung đặt (chỉ gỡ `ask` có trong đây) + chính sách (REC-09)
                                — hash dạng `sha256:<hex>` (cả `harness.sha256.json`); đọc nhận cả hex trần của bản cũ
  .claude/settings.json, hooks/, skills/, agents/   harness (COPY-IF-ABSENT: không đè file đã có; bản mới ghi .xtemplates-new)
  <starter/, managed/ của gói>  chỉ khi --pack <id> (framework/templates/packs/<id>/, ADR-0068): starter chỉ vào repo sạch
                                (chưa có package.json, manifest chưa ghi gói; sau đó là của dự án); managed nâng theo hash
                                manifest như harness; khoá xt.yaml của gói chỉ đặt khi chép starter (còn lại: gợi ý trong
                                --plan); lùi bản = cài lại bằng bản khung cũ
  .github/rulesets/main.json, pull_request_template.md, dependabot.yml,
  .github/workflows/{ci,secret-scan,pr-title,merge-gate,pr-steward}.yml   chỉ khi --with-github (copy-if-absent, hash vào manifest;
                                merge-gate.yml là stub tạm D-122)
  AGENTS.md, CLAUDE.md, PROGRESS.md, xt.yaml       từ framework/templates (copy-if-absent, bỏ frontmatter YAML; mẫu bọc ```markdown thì lấy phần trong)

File đã có mà khác bản khung (mọi nhóm): còn đúng hash lần cài trước → cập nhật tại chỗ; dự án đã sửa mà mẫu không đổi từ lần
cài trước → `kept-own` (im lặng); dự án đã sửa và mẫu đổi (hoặc chưa biết hash) → `.xtemplates-new`, ghi hash mẫu MỚI nên chỉ
gộp tay một lần mỗi lần mẫu đổi (D-114). File gốc: hash là mẫu đã bỏ frontmatter, TRƯỚC khi thay SHA HEAD (PROGRESS.md); cài
từ bản chưa có hash file gốc → suy từ `.xtemplates/framework/templates/` cũ; `xt.yaml` của dự án nhận khoá mới của mẫu dạng
chú thích. Nâng bản (`.xtemplates/VERSION` cũ đọc được X.Y.Z) → in mệnh đề "Dự án đích …" của CHANGELOG khung từ bản đó.

Dự án đã cài bản ≤ 2.x (`.xstored/`, `xs.py`, `xs.yaml`, `XS_*`): chạy lại install là chuyển sang tên mới (ADR-0007) —
  giữ manifest hash, đổi `xs.yaml` → `xt.yaml`, xoá bản sao `.xstored/`; file người dùng còn nhắc tên cũ được liệt kê để sửa tay.

Dùng:
  python3 scripts/install.py <thư-mục-dự-án> [--force-harness] [--no-harness] [--no-git-hooks] [--harness codex,…] [--with-github] [--preset safe|autonomous] [--stage-init] [--pack <id>] [--label v1.0.0] [--plan]
  --plan: in JSON kế hoạch (quyền thêm/bớt, hook thêm/đổi matcher, file đè/giữ, git hook, adapter; gói và drift file
          managed khi có --pack), không ghi gì (REC-09)
  --no-git-hooks: không cài git hook sàn chung (`pre-commit`/`commit-msg`/`pre-push`); git hook + adapter khung đã ghi
                  được liệt kê trong manifest.json (`git_hooks`, `adapters`) — AUD-HAR-204
  --preset: chính sách merge/review cho xt.yaml mới; cài lại giữ lựa chọn dự án (không cấu hình sandbox).
  --stage-init: dự án mới — tạo sổ giai đoạn sản phẩm docs/autopilot/STAGE.json (giai đoạn 1, ADR-0058) khi chưa có; không
                cờ thì không tạo. Sau cài luôn kiểm sổ bằng `xt.py stage status` (sổ có sẵn giữ nguyên).
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
from typing import Any, TypeGuard
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
INSTALL_PRESETS = {
    "safe": {"merge_autonomy": "L1", "merge_hard_exceptions": "human", "delivery_phase": "harden"},
    "autonomous": {"merge_autonomy": "L3", "merge_hard_exceptions": "auto", "delivery_phase": "build"},
}
YAML_POLICY_KEYS = frozenset(key.encode("ascii") for key in INSTALL_PRESETS["safe"])
# Tên trước 3.0.0 (ADR-0007): dự án đã cài bản ≤ 2.x được chuyển tự động khi chạy lại install.
LEGACY_DIR = ".xstored"
LEGACY_YAML = "xs.yaml"
LEGACY_RE = re.compile(r"\.xstored\b|\bxs\.(?:py|yaml)\b|\bXS_[A-Z]")
# --with-github: hàng rào GitHub mẫu (copy-if-absent), đích → nguồn trong khung. Mọi workflow ở đây KHÔNG phụ thuộc stack
# (AUD-CI-003): `ci.yml` mẫu chạy lệnh của xt.yaml qua `.xtemplates/scripts/dev-task.sh` (3 job `gate` · `e2e` · `quality`
# tổng hợp, ADR-0039, WF-CI-025), `secret-scan.yml` (`gitleaks`), `pr-title.yml` (tiêu đề PR) và `pr-steward.yml` (ADR-0027) chỉ cần python3 + gh. Ruleset
# mẫu (D-116, D-117, D-122) chỉ đòi `quality` · `gitleaks` và không đòi "up to date" (PR merge song song); `protection-guard`
# là bước của `quality`, `dep-audit` (theo ngôn ngữ, dự án viết) là bước của `gate`. `merge-gate.yml` là STUB TẠM (D-122, ADR-0036):
# job `merge-gate` luôn xanh, chỉ giữ context cũ còn trong ruleset sống của dự án — vẫn phát để bản cũ (gọi lệnh
# `xt.py merge-gate` đã gỡ) được cập nhật tại chỗ thay vì làm đỏ mọi PR; bỏ khỏi danh sách này khi ruleset sống đã gỡ
# context (T-1834). Mẫu PR, ruleset, Dependabot, CI, quét bí mật lấy từ framework/templates: bản ở `.github/` của khung là
# của riêng repo khung.
GITHUB_FILES = {
    ".github/rulesets/main.json": "framework/templates/ruleset-main.json",
    ".github/pull_request_template.md": "framework/templates/PULL-REQUEST.md",
    ".github/dependabot.yml": "framework/templates/dependabot.yml",
    ".github/workflows/ci.yml": "framework/templates/ci.yml",
    ".github/workflows/secret-scan.yml": "framework/templates/secret-scan.yml",
    ".github/workflows/pr-title.yml": "framework/templates/pr-title.yml",
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


def drop_symlink(path: Path) -> None:
    """`.xtemplates/` là bản chỉ đọc của khung: đích là symlink → gỡ liên kết (không đụng file nó trỏ tới) rồi ghi file
    thật — không bao giờ ghi xuyên symlink ra ngoài dự án (AUD-CFG-003, như AUD-HAR-010 cho harness)."""
    if path.is_symlink():
        log(f"  ⚠ {path} là symlink — gỡ liên kết, ghi bản khung tại chỗ (không ghi qua liên kết)")
        path.unlink()


BYTECODE = shutil.ignore_patterns("__pycache__", "*.pyc")
PACK_PAYLOADS = ("starter", "managed")


def framework_ignore(dirpath: str, names: list[str]) -> set[str]:
    """Bỏ bytecode và cây nội dung của gói sản phẩm (`templates/packs/<id>/starter|managed`) khỏi `.xtemplates/framework`:
    installer đọc gói từ khung nguồn; chép vào dự án đích thì test `*.test.ts`/`package.json` của gói bị công cụ của dự
    án (vitest, pnpm workspace…) nhặt nhầm (review lát B 🔴)."""
    skip = set(BYTECODE(dirpath, names))
    here = Path(dirpath)
    if here.parent.name == "packs" and here.parent.parent.name == "templates":
        skip |= {n for n in names if n in PACK_PAYLOADS}
    return skip


def copy_tree_replace(src: Path, dst: Path, ignore: Callable[[str, list[str]], set[str]] = BYTECODE) -> None:
    """Copy vào thư mục tạm rồi mới thay: lỗi giữa chừng không để dst mất/dở."""
    tmp = dst.with_name(dst.name + ".tmp")
    drop_symlink(tmp)
    shutil.rmtree(tmp, ignore_errors=True)
    shutil.copytree(src, tmp, ignore=ignore)
    drop_symlink(dst)
    if dst.exists():
        shutil.rmtree(dst)
    tmp.rename(dst)


# Đích liên kết như `LINK_RE` của check-links: `<…>` (cho phép khoảng trắng) hoặc không khoảng trắng (AUD-CODE-044).
MD_LINK_RE = re.compile(r"\]\((<[^>]+>|[^)#\s]+)")
# Trích dẫn trong backtick: `research/x.md` (từ gốc repo khung) hay `../../research/x.md` (từ file) — AUD-XFEAT-047.
TICK_RESEARCH_RE = re.compile(r"`((?:\.\./)*research/[^`#\s]+)")


def _research_refs(md: Path, src: Path) -> list[Path]:
    """Đích có thể của mọi tham chiếu trong `md`: liên kết Markdown (từ thư mục của file), trích dẫn backtick (từ thư mục
    của file, rồi từ gốc `src`)."""
    text = md.read_text(encoding="utf-8")
    refs = [md.parent / link.strip("<>").split("#")[0] for link in MD_LINK_RE.findall(text)]
    return refs + [base / tick for tick in TICK_RESEARCH_RE.findall(text) for base in (md.parent, src)]


def linked_research(src: Path) -> list[Path]:
    """Đường dẫn (tương đối từ `research/`) của mọi FILE trong `src/research` mà tài liệu ở `src/framework` trỏ tới bằng
    liên kết Markdown tương đối hoặc trích dẫn backtick — kể cả gián tiếp (file research trỏ sang file research khác);
    liên kết tới thư mục, URL hay ra ngoài `research/` bị bỏ qua."""
    root = (src / "research").resolve()
    found: set[Path] = set()
    todo = sorted((src / "framework").rglob("*.md"))
    while todo:
        md = todo.pop()
        for ref in _research_refs(md, src):
            target = ref.resolve()
            rel = target.relative_to(root) if target.is_file() and target.is_relative_to(root) else None
            if rel is not None and rel not in found:
                found.add(rel)
                todo += [target] if target.suffix == ".md" else []
    return sorted(found)


def copy_files_replace(src: Path, rels: list[Path], dst: Path) -> None:
    """Như `copy_tree_replace` nhưng chỉ các file `rels` (tương đối từ `src`): dựng ở thư mục tạm rồi mới thay."""
    tmp = dst.with_name(dst.name + ".tmp")
    drop_symlink(tmp)
    shutil.rmtree(tmp, ignore_errors=True)
    for rel in rels:
        (tmp / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src / rel, tmp / rel)
    tmp.mkdir(exist_ok=True)
    drop_symlink(dst)
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


def installed_preset(target: Path) -> str | None:
    """Preset đã áp dụng khi tạo xt.yaml; thiếu/hỏng/không biết → hành vi mẫu cũ, không suy từ cấu hình dự án."""
    try:
        value = json.loads((target / MANIFEST_V2).read_text(encoding="utf-8")).get("policy", {}).get("install_preset")
    except (OSError, ValueError, AttributeError):
        return None
    return value if isinstance(value, str) and value in INSTALL_PRESETS else None


def has_project_yaml(target: Path) -> bool:
    """Có cấu hình hiện hữu (kể cả legacy/symlink hỏng): --preset không được thay lựa chọn của dự án."""
    return any(p.exists() or p.is_symlink() for p in (target / "xt.yaml", target / LEGACY_YAML))


def select_preset(target: Path, requested: str | None) -> str | None:
    """Chỉ chọn preset mới khi tạo xt.yaml; cài lại dùng preset đã lưu, không nâng/hạ quyền ngầm."""
    saved = installed_preset(target)
    return saved if has_project_yaml(target) else requested or saved


def yaml_with_preset(text: str, preset: str | None) -> str:
    """Thay đúng ba khoá chính sách của mẫu; không sửa nội dung dự án hay cấu hình quyền/sandbox."""
    if preset is None:
        return text
    for key, value in INSTALL_PRESETS[preset].items():
        text = re.sub(rf"^{key}:.*$", f"{key}: {value}", text, flags=re.M)
    return text


def manifest_policy(target: Path, preset: str | None = None) -> dict[str, str]:
    """Chính sách manifest: chỉ ghi preset đã áp dụng thật, hoặc giữ lựa chọn hợp lệ của lần cài trước."""
    policy = {"ask_removal": "manifest-only"}
    selected = preset or installed_preset(target)
    if selected is not None:
        policy["install_preset"] = selected
    return policy


def yaml_policy_unchanged(current: bytes, replacement: bytes, preserve: bool) -> bool:
    """Khi cập nhật xt.yaml, chỉ tự ghi nếu ba dòng chính sách giữ nguyên; không suy preset từ file dự án."""
    if not preserve:
        return True

    def policy(data: bytes) -> list[bytes]:
        return [line for line in data.splitlines() if line.partition(b":")[0] in YAML_POLICY_KEYS]

    return policy(current) == policy(replacement)


def yaml_keep_policy(template: bytes, own: bytes) -> bytes:
    """`xt.yaml.xtemplates-new` giữ ba dòng chính sách của file dự án (AUD-HAR-123): khoá dự án có → lấy dòng của dự án;
    dự án không khai (= hành vi mặc định) → dòng của mẫu thành chú thích. Gộp tay không vô tình nâng quyền theo mẫu."""
    mine = {k: line for line in own.splitlines() if (k := line.partition(b":")[0]) in YAML_POLICY_KEYS}
    out = []
    for line in template.splitlines(keepends=True):
        key, body = line.partition(b":")[0], line.rstrip(b"\r\n")
        if key in YAML_POLICY_KEYS:
            line = mine.get(key, b"# " + body) + line[len(body) :]
        out.append(line)
    return b"".join(out)


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
    preserve_yaml_policy: bool = False,
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
        return ("updated" if yaml_policy_unchanged(current, data, preserve_yaml_policy) else "updated-new"), data
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
    """ADR-0018: `allow` có `Bash`, thêm `deny` của khung còn thiếu; gỡ `ask`/`deny` mà manifest (`prov`) chứng minh do
    khung đặt và khung không còn đặt (ADR-0040: deny tĩnh của hành động cục bộ chuyển cho guard quyết theo pha). Trả báo
    cáo `allow_add`/`deny_add`/`ask_remove`/`deny_remove`/`ask_unproven` (tổng độ dài = số thay đổi)."""
    src, perms = ours.get("permissions", {}), theirs.setdefault("permissions", {})
    report: dict[str, list[str]] = {"allow_add": [], "deny_add": [], "ask_remove": [], "deny_remove": []}
    for key in ("allow", "deny"):
        rules = perms.setdefault(key, [])
        missing = [r for r in src.get(key, []) if r not in rules and (key == "deny" or r == "Bash")]
        rules.extend(missing)
        report[f"{key}_add"] = missing
    for key in ("ask", "deny"):
        rules, now = perms.get(key, []), set(src.get(key, []))
        proven = set((prov or {}).get(key, [])) - now
        report[f"{key}_remove"] = [r for r in rules if r in proven]
        if report[f"{key}_remove"]:
            perms[key] = [r for r in rules if r not in proven]
    ask, now = perms.get("ask", []), set(src.get("ask", []))
    report["ask_unproven"] = [r for r in ask if r in OLD_FRAMEWORK_ASK and r not in now]
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


def _seconds(value: object) -> TypeGuard[int | float]:
    """`timeout` là số giây (int/float, không phải bool — `true < 1200` đúng trong Python, AUD-HAR-303 🟢)."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _sync_timeout(theirs: list[dict[str, Any]], entry: dict[str, Any]) -> list[dict[str, Any]]:
    """`timeout` của handler khung lớn hơn handler cùng lệnh ở dự án → nâng lên (khung nâng hạn chờ hook guard 600 →
    1200 s, D-382 — giữ hạn cũ thì hook hết giờ chặn commit chạy đủ bộ test); dự án đặt lớn hơn hoặc không đặt thì giữ —
    không bao giờ hạ. Trả danh sách handler đã đổi."""
    want = {h.get("command"): h["timeout"] for h in entry.get("hooks", []) if _seconds(h.get("timeout"))}
    changed = []
    for h in (h for e in theirs for h in e.get("hooks", [])):
        have = h.get("timeout")
        if h.get("command") in want and _seconds(have) and have < want[h["command"]]:
            h["timeout"] = want[h["command"]]
            changed.append({"command": h["command"], "timeout_from": have, "timeout_to": h["timeout"]})
    return changed


PROJECT_DIR_PREFIX = re.compile(r'"?\$\{?CLAUDE_PROJECT_DIR\}?/')


def _hook_key(cmd: object) -> object:
    """Khoá so lệnh hook: bỏ `${CLAUDE_PROJECT_DIR}/` và dấu nháy — khung 2.x đăng ký dạng tương đối
    (`bash .claude/hooks/x.sh`), cùng hook với dạng hiện tại (`bash "${CLAUDE_PROJECT_DIR}/.claude/hooks/x.sh"`)."""
    return PROJECT_DIR_PREFIX.sub("", cmd).replace('"', "") if isinstance(cmd, str) else cmd


def _upgrade_legacy_commands(theirs: list[dict[str, Any]], entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Handler dự án cùng khoá với lệnh khung nhưng khác chữ (dạng tương đối của khung 2.x — sai đường khi cwd không phải
    gốc dự án) → đổi sang lệnh khung; lệnh khung lặp lại sau khi đổi thì gỡ bản sau (mục chỉ còn rỗng vì vậy bỏ luôn) —
    không đăng ký hook hai lần. Trả danh sách thay đổi."""
    want = {_hook_key(h.get("command")): h.get("command") for e in entries for h in e.get("hooks", [])}
    framework, seen = set(want.values()), set[object]()
    changed: list[dict[str, Any]] = []
    for e in theirs:
        kept = []
        for h in e.get("hooks", []):
            cmd = want.get(_hook_key(h.get("command")), h.get("command"))
            if cmd != h.get("command"):
                changed.append({"command_from": h.get("command"), "command_to": cmd})
                h["command"] = cmd
            if cmd in framework and cmd in seen:
                changed.append({"duplicate_removed": cmd})
                continue
            seen.add(cmd)
            kept.append(h)
        if len(kept) < len(e.get("hooks", [])):
            e["hooks"] = kept
    theirs[:] = [e for e in theirs if e.get("hooks") != []]
    return changed


def _merge_hook_events(
    ours: dict[str, Any], theirs: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Gộp `hooks` của khung vào `theirs` (giữ hook riêng); trả (mục thêm, mục đổi lệnh/matcher/`onFailure`/`timeout`),
    mỗi mục kèm `event`."""
    hooks = theirs.setdefault("hooks", {})
    added: list[dict[str, Any]] = []
    synced: list[dict[str, Any]] = []
    for event, entries in ours.get("hooks", {}).items():
        synced += [{"event": event, **c} for c in _upgrade_legacy_commands(hooks.get(event, []), entries)]
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
                    + _sync_timeout(hooks.get(event, []), entry)
                ]
    return added, synced


HOOK_FORM_LABEL = {  # log của `install_settings` (AUD-HAR-306: trước luôn in "dạng tương đối", kể cả khi giữ tuyệt đối)
    "relative": "dạng tương đối",
    "absolute": "giữ dạng ${CLAUDE_PROJECT_DIR} của dự án",
    "framework": "dạng của khung",
}
OWN_PERMISSIONS_RE = re.compile(r"""^harness_permissions:[ \t]*["']?own["']?[ \t]*(?:#.*)?$""", re.M)
NO_PERMISSION_CHANGES = ("allow_add", "deny_add", "ask_remove", "deny_remove", "ask_unproven")


def own_permissions(target: Path) -> bool:
    """`harness_permissions: own` trong xt.yaml của dự án: dự án giữ mô hình quyền riêng (dhcb cấm `allow: Bash` trùm —
    chủ repo 2026-10-22); lệnh hook khung theo dạng dự án đang dùng — tuyệt đối nếu đã có lệnh khung dạng `${CLAUDE_PROJECT_DIR}`, không thì
    tương đối `bash .claude/hooks/x.sh` (`_absolute_form`, `_relative_hooks`; ADR-0073). Thiếu/không đọc được → False."""
    try:
        return bool(OWN_PERMISSIONS_RE.search((target / "xt.yaml").read_text(encoding="utf-8-sig")))
    except (OSError, UnicodeDecodeError):
        return False


def _absolute_form(ours: dict[str, Any], theirs: dict[str, Any]) -> bool:
    """Dự án đang ghi lệnh hook KHUNG (cùng khoá `_hook_key` với lệnh của `ours`; hook riêng của dự án không tính) dạng
    `${CLAUDE_PROJECT_DIR}/…` (ADR-0073, AUD-HAR-301): `own` giữ dạng đó — dạng tương đối không chạy khi phiên mở ngoài
    gốc repo. Chưa có lệnh hook khung nào → dạng tương đối."""
    keys = {
        _hook_key(h.get("command")) for es in ours.get("hooks", {}).values() for e in es for h in e.get("hooks", [])
    }
    cmds = [h.get("command") for es in theirs.get("hooks", {}).values() for e in es for h in e.get("hooks", [])]
    return any(isinstance(c, str) and PROJECT_DIR_PREFIX.search(c) is not None and _hook_key(c) in keys for c in cmds)


def _relative_hooks(ours: dict[str, Any]) -> dict[str, Any]:
    """Bản sao settings khung với lệnh hook dạng tương đối của dự án (`bash .claude/hooks/x.sh`, bỏ
    `${CLAUDE_PROJECT_DIR}/` và dấu nháy — `_hook_key`)."""
    copy: dict[str, Any] = json.loads(json.dumps(ours))
    for h in (h for entries in copy.get("hooks", {}).values() for e in entries for h in e.get("hooks", [])):
        h["command"] = _hook_key(h.get("command"))
    return copy


def settings_changes(
    ours: dict[str, Any], theirs: dict[str, Any], prov: dict[str, list[str]], own: bool = False
) -> dict[str, Any]:
    """Gộp `ours` vào `theirs` tại chỗ (bộ nhớ) và trả báo cáo: `permissions`, `hooks_added`, `hooks_matcher_updated`,
    `changes` (tổng số thay đổi; 0 = không cần ghi). `own` (`harness_permissions: own`): không đụng quyền, lệnh hook
    của khung ghi dạng tương đối như dự án."""
    added, synced = _merge_hook_events(
        _relative_hooks(ours) if own and not _absolute_form(ours, theirs) else ours, theirs
    )
    perms = dict.fromkeys(NO_PERMISSION_CHANGES, []) if own else merge_permissions(ours, theirs, prov)
    total = (
        len(added) + len(synced) + sum(len(perms[k]) for k in ("allow_add", "deny_add", "ask_remove", "deny_remove"))
    )
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
    src: Path,
    dst: Path,
    prov: dict[str, list[str]] | None = None,
    report: dict[str, Any] | None = None,
    own: bool = False,
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
    form = ("absolute" if _absolute_form(ours, theirs) else "relative") if own else "framework"
    rep = settings_changes(ours, theirs, prov or {}, own)
    if report is not None:
        report.update(rep, hook_form=form)
    if not rep["changes"]:
        return "kept"
    write_atomic(dst, json_preserving(dst.read_text(encoding="utf-8"), theirs) + "\n")
    return "merged-hooks"


JSON_INDENT = re.compile(r"\n([ \t]+)\S")
JsonPath = tuple[str | int, ...]


class _JsonSpans:
    """Vị trí văn bản (đầu, cuối) của mọi giá trị trong một JSON hợp lệ, theo đường dẫn khoá/chỉ số."""

    def __init__(self, text: str) -> None:
        self.text, self.spans = text, dict[JsonPath, tuple[int, int]]()
        self.value(0, ())

    def skip(self, i: int) -> int:
        while self.text[i] in " \t\r\n":  # chỉ gọi trong object/mảng: sau khoảng trắng luôn còn ký tự
            i += 1
        return i

    def value(self, i: int, path: JsonPath) -> int:
        i = self.skip(i)
        opener = self.text[i]
        end = self.members(i, path) if opener in "{[" else json.JSONDecoder().raw_decode(self.text, i)[1]
        self.spans[path] = (i, end)
        return end

    def members(self, i: int, path: JsonPath) -> int:
        """Duyệt object/mảng mở ở `i`; trả vị trí sau dấu đóng."""
        is_obj, n = self.text[i] == "{", 0
        i = self.skip(i + 1)
        while self.text[i] not in "}]":
            key: str | int = n
            if is_obj:
                key, i = json.JSONDecoder().raw_decode(self.text, i)
                i = self.skip(i) + 1  # bỏ `:`
            i = self.skip(self.value(i, (*path, key)))
            i = self.skip(i + 1) if self.text[i] == "," else i
            n += 1
        return i + 1


def json_preserving(src: str, value: Any) -> str:
    """`value` dạng JSON, giữ nguyên văn bản của `src` cho mọi nút không đổi (cùng đường dẫn, cùng giá trị) — dự án định
    dạng `settings.json` theo Prettier (dhcb: object một dòng `{ "type": … }`) thì gộp vài hook không viết lại cả file
    (dhcb #1481: diff 95 dòng cho 2 giá trị, AUD-HAR-305). Nút đổi: object/mảng gốc nằm một dòng thì giữ một dòng (cùng
    kiểu khoảng trắng trong ngoặc), còn lại nhiều dòng theo thụt lề của file (mặc định 2 dấu cách)."""
    found = JSON_INDENT.search(src)
    return _render(value, (), _JsonSpans(src), found[1] if found else "  ", 0)


def _same_json(a: Any, b: Any) -> bool:
    """Bằng nhau theo JSON (`1`, `1.0`, `true` khác nhau — `==` của Python coi là bằng)."""
    return json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def _render(value: Any, path: JsonPath, src: _JsonSpans, unit: str, depth: int) -> str:
    span = src.spans.get(path)
    old = src.text[span[0] : span[1]] if span else ""
    was = json.loads(old) if old else None
    if old and _same_json(was, value):
        return old
    if not isinstance(value, (dict, list)) or not value:
        return json.dumps(value, ensure_ascii=False)
    pairs = value.items() if isinstance(value, dict) else enumerate(value)
    parts = [
        (json.dumps(k, ensure_ascii=False) + ": " if isinstance(value, dict) else "")
        + _render(v, (*path, k), src, unit, depth + 1)
        for k, v in pairs
    ]
    open_, close = "{}" if isinstance(value, dict) else "[]"
    if was and old[0] == open_ and "\n" not in old:  # gốc rỗng (`[]`): chưa rõ kiểu — nhiều dòng như `indent=2`
        pad = " " if old[1:2] == " " else ""
        return f"{open_}{pad}{', '.join(parts)}{pad}{close}"
    inner = unit * (depth + 1)
    return f"{open_}\n{inner}" + f",\n{inner}".join(parts) + f"\n{unit * depth}{close}"


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


def target_error(target: Path, with_github: bool = False) -> str | None:
    """Lý do không cài được vào `target` (None nếu hợp lệ)."""
    if not target.is_dir():
        return f"✗ không phải thư mục: {target}"
    if target == SRC:
        return "✗ không cài khung vào chính repo khung"
    if (target / ".xtemplates").is_symlink():
        return f"✗ {target / '.xtemplates'} là symlink — khung không ghi xuyên liên kết (AUD-CFG-003); gỡ liên kết rồi cài lại"
    return github_root_error(target) if with_github else None


GIT_LOCATION_ENV = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR", "GIT_OBJECT_DIRECTORY")


def git_subdir_of(target: Path) -> Path | None:
    """Gốc repo git khi `target` là thư mục CON của nó (monorepo `apps/web`); gốc repo, không phải repo git hay git lỗi → None
    (chưa có gốc để so). Bỏ `GIT_DIR`… của môi trường (hook, tự động hoá): gốc là của `target`, như `xt.py` thấy."""
    env = {k: v for k, v in os.environ.items() if k not in GIT_LOCATION_ENV}
    try:
        r = subprocess.run(
            ["git", "-C", str(target), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=10,
            env=env,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    top = Path(r.stdout.strip()).resolve() if r.returncode == 0 and r.stdout.strip() else None
    return None if top is None or top == target else top


def github_root_error(target: Path) -> str | None:
    """`--with-github` vào thư mục con của repo git: GitHub chỉ chạy workflow ở `.github/workflows` của GỐC repo — ghi vào
    thư mục con là CI không bao giờ chạy mà không ai biết (AUD-CI-012)."""
    top = git_subdir_of(target)
    if top is None:
        return None
    return (
        f"✗ --with-github: {target} không phải gốc repo git ({top}) — GitHub chỉ chạy workflow ở {top / '.github'}; "
        "cài không kèm --with-github ở thư mục con, rồi chép/gộp workflow vào gốc repo và đặt `working-directory`"
    )


def pack_root_error(target: Path, pack: dict[str, Any] | None) -> str | None:
    """`--pack` có file managed dưới `.github/` vào thư mục con của repo git: như `--with-github` (AUD-CI-012), workflow
    ghi ở đó không bao giờ chạy (AUD-HAR-227) → từ chối trước khi ghi."""
    if pack is None or not any(rel.startswith(".github/") for rel, _src in pack_tree(pack["id"], "managed")):
        return None
    top = git_subdir_of(target)
    if top is None:
        return None
    return (
        f"✗ --pack {pack['id']}: {target} không phải gốc repo git ({top}) — gói ghi .github/ mà GitHub chỉ chạy workflow "
        f"ở {top / '.github'}; cài gói ở gốc repo, hoặc chép/gộp workflow vào gốc và đặt `working-directory`"
    )


def install_framework(xt_dir: Path, label: str | None) -> str:
    """Bước 1: framework + research + scripts + VERSION + README vào .xtemplates/ — thay thế toàn bộ (bản chỉ đọc).
    Trả nhãn đã ghi vào VERSION."""
    copy_tree_replace(SRC / "framework", xt_dir / "framework", framework_ignore)
    # research/: chỉ file module trong framework/ trỏ tới bằng đường dẫn tương đối (AUD-XFEAT-046) — nhật ký nghiên cứu
    # khác của repo khung không phải của dự án đích.
    if (SRC / "research").is_dir():
        copy_files_replace(SRC / "research", linked_research(SRC), xt_dir / "research")
    drop_symlink(xt_dir / "scripts")
    (xt_dir / "scripts").mkdir(exist_ok=True)
    for f in ("xt.py", "dev-task.sh", "check-links.py", "xt_adapter.py"):
        drop_symlink(xt_dir / "scripts" / f)
        if f == "xt_adapter.py" and not (SRC / "scripts" / f).is_file():  # khung tối giản/bản cũ: không có adapter
            continue
        shutil.copy2(SRC / "scripts" / f, xt_dir / "scripts" / f)
    (xt_dir / "scripts" / "dev-task.sh").chmod(0o755)
    # App cục bộ `xt.py app` (ADR-0038): gói máy chủ + giao diện tĩnh cạnh xt.py, luôn thay như xt.py.
    for d in ("xt_app", "app"):
        if (SRC / "scripts" / d).is_dir():  # khung tối giản (test, bản cũ) không có app: bỏ qua, `doctor` báo ⚠
            copy_tree_replace(SRC / "scripts" / d, xt_dir / "scripts" / d)
    version = framework_label(label)
    for f in ("VERSION", "README.md"):
        drop_symlink(xt_dir / f)
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
    """Rule do khung đặt sau lần gộp: cũ + vừa thêm (`allow_add`/`deny_add`), bớt `ask`/`deny` vừa gỡ. Rule người dùng đã có
    sẵn (không do khung thêm) không bao giờ vào danh sách này. Khử trùng giữ thứ tự: rule bị gỡ rồi khung thêm lại ở lần
    cài sau không làm danh sách phình (PR #173)."""
    perms = report.get("permissions", {})
    out = {k: list(dict.fromkeys([*prov.get(k, []), *perms.get(f"{k}_add", [])])) for k in RULE_KEYS}
    for key in ("ask", "deny"):
        out[key] = [r for r in out[key] if r not in perms.get(f"{key}_remove", [])]
    return out


def install_settings(
    target: Path, force_harness: bool, stats: Counter[str], prov: dict[str, list[str]]
) -> dict[str, list[str]]:
    """settings.json của harness: dự án đã có (không --force-harness) thì gộp khoá hooks, chưa có thì copy.
    Trả rule do khung đặt (ghi vào manifest.json)."""
    settings = target / ".claude" / "settings.json"
    if settings.exists() and not force_harness:
        report: dict[str, Any] = {}
        own = own_permissions(target)
        r = merge_hooks(SRC / ".claude" / "settings.json", settings, prov, report, own)
        stats[r] += 1
        if r == "merged-hooks" and own:
            log(
                f"  .claude/settings.json: đã gộp hooks của khung ({HOOK_FORM_LABEL[report['hook_form']]}); quyền giữ"
                " nguyên — harness_permissions: own"
            )
        elif r == "merged-hooks":
            log(
                "  .claude/settings.json: đã gộp hooks + quyền của khung (allow Bash, deny, gỡ ask do khung đặt — ADR-0018)"
            )
        unproven = report.get("permissions", {}).get("ask_unproven", [])
        if unproven:
            log(f"  ⚠ giữ `ask` trùng chuỗi rule cũ của khung nhưng manifest không chứng minh khung đặt: {unproven}")
        return update_provenance(prov, report)
    own = own_permissions(target)
    r = copy_if_absent(SRC / ".claude" / "settings.json", settings, force_harness, own_settings if own else None)
    stats[r] += 1
    if r != "copied":
        return prov
    return dict.fromkeys(RULE_KEYS, []) if own else our_rules()


def own_settings(text: str) -> str:
    """settings.json khung cho dự án `harness_permissions: own` khi chép mới/`--force-harness`: bỏ `permissions` (dự án tự
    khai), lệnh hook dạng tương đối (`_relative_hooks`)."""
    data = _relative_hooks(json.loads(text))
    data.pop("permissions", None)
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def shadowed_skills(target: Path) -> list[str]:
    """Skill khung trùng tên lệnh riêng của dự án (`.claude/commands/<tên>.md`): không cài — lệnh dự án thắng (chủ repo
    2026-10-22; dhcb có `/gate`, `/review`, `/adr` riêng); `doctor` nhận lệnh đó thay skill."""
    commands = target / ".claude" / "commands"
    return sorted(d.name for d in (SRC / ".claude" / "skills").iterdir() if (commands / f"{d.name}.md").is_file())


def registered_hooks() -> set[str]:
    """Tên file trong `.claude/hooks/` mà settings.json của khung đăng ký, cộng file chúng nạp cạnh (`_lib.sh`,
    `guard.py`). Hook khung chưa đăng ký không chép sang dự án đích:
    file hook không ai gọi là mồ côi (xboss `tests/claude-hooks.test.ts` bắt)."""
    hooks = SRC / ".claude" / "hooks"
    named = set(
        re.findall(r"\.claude/hooks/([\w.-]+)", (SRC / ".claude" / "settings.json").read_text(encoding="utf-8"))
    )
    sources = [hooks / n for n in named if (hooks / n).is_file()]
    return named | {s for p in sources for s in re.findall(r'\$\(dirname "\$0"\)/([\w.-]+)', p.read_text("utf-8"))}


def harness_sources(target: Path) -> list[Path]:
    """File harness của khung cần copy ngoài settings.json: HARNESS_FILES khác settings + mọi file trong HARNESS_DIRS,
    trừ skill bị lệnh dự án che (`shadowed_skills`) và hook khung chưa đăng ký (`registered_hooks`)."""
    sources = [SRC / ".claude" / f for f in HARNESS_FILES if f != "settings.json"]
    skip = {SRC / ".claude" / "skills" / name for name in shadowed_skills(target)}
    hooks = SRC / ".claude" / "hooks"
    registered = registered_hooks()
    skip |= {p for p in hooks.iterdir() if p.is_file() and p.name not in registered}
    for d in HARNESS_DIRS:
        sources += [
            p
            for p in sorted((SRC / ".claude" / d).rglob("*"))
            if p.is_file() and "__pycache__" not in p.parts and p not in skip and not skip.intersection(p.parents)
        ]
    return sources


def copy_harness_files(
    target: Path, force_harness: bool, manifest: dict[str, str], stats: Counter[str]
) -> dict[str, str]:
    """Copy-if-absent từng file harness; trả manifest mới: hash bản khung vừa đưa (`HASHED`, kể cả `.xtemplates-new`),
    giữ hash cũ khi `kept-own`/symlink."""
    new_manifest: dict[str, str] = {}
    for src in harness_sources(target):
        rel = src.relative_to(SRC).as_posix()
        r = copy_if_absent(src, target / rel, force_harness, installed_hash=manifest.get(rel))
        stats[r] += 1
        if r in HASHED:
            new_manifest[rel] = sha256(src.read_bytes())
        elif rel in manifest:
            new_manifest[rel] = manifest[rel]
    return new_manifest


def write_manifests(
    target: Path, files: dict[str, str], rules: dict[str, list[str]], preset: str | None = None
) -> None:
    """Ghi `harness.sha256.json` (hash file) và `manifest.json` (hash file + rule khung đặt + chính sách, REC-09); mọi
    hash ghi dạng `sha256:<hex>` (`hash_label`), kể cả hash hex trần giữ lại từ manifest cũ."""
    labelled = {rel: hash_label(digest) for rel, digest in files.items()}
    write_atomic(target / MANIFEST, json.dumps(labelled, indent=2, sort_keys=True) + "\n")
    doc = {"schema": 1, "files": labelled, "rules": rules, "policy": manifest_policy(target, preset)}
    doc.update({k: v for k, v in load_manifest_doc(target).items() if k in MANIFEST_PATH_LISTS})
    write_atomic(target / MANIFEST_V2, json.dumps(doc, indent=2, sort_keys=True) + "\n")


MANIFEST_PATH_LISTS = (
    "git_hooks",
    "adapters",
    "packs",
)  # file khung ghi ngoài `files` (AUD-HAR-204) + gói đã cài (`packs`, object) — giữ qua `write_manifests`


def load_manifest_doc(target: Path) -> dict[str, Any]:
    """manifest.json dạng object (thiếu/hỏng → {})."""
    try:
        doc = json.loads((target / MANIFEST_V2).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return doc if isinstance(doc, dict) else {}


def record_manifest_paths(target: Path, key: str, paths: list[str]) -> None:
    """Ghi danh sách đường dẫn khung đã ghi (`git_hooks`/`adapters`) vào manifest.json, giữ mọi khoá khác."""
    doc = load_manifest_doc(target)
    doc[key] = sorted(set(paths))
    (target / MANIFEST_V2).parent.mkdir(parents=True, exist_ok=True)
    write_atomic(target / MANIFEST_V2, json.dumps(doc, indent=2, sort_keys=True) + "\n")


def install_harness(target: Path, force_harness: bool) -> None:
    """Bước 2: harness .claude/ — copy-if-absent, ghi manifest hash (+ manifest.json có rule khung), báo thống kê."""
    stats: Counter[str] = Counter()
    manifest = load_manifest(target)
    rules = install_settings(target, force_harness, stats, load_rules(target))
    new_manifest = copy_harness_files(target, force_harness, manifest, stats)
    # Hash file `.github/` (--with-github) và file gốc (bước sau ghi lại) giữ qua bước này: lần sau file chưa sửa vẫn
    # được cập nhật tại chỗ.
    # File managed của gói (`--pack`) cũng vậy.
    packed = pack_managed_paths(target)
    new_manifest.update({k: v for k, v in manifest.items() if k in GITHUB_FILES or k in ROOT_TEMPLATES or k in packed})
    write_manifests(target, new_manifest, rules)
    log("✓ .claude/: " + " · ".join(f"{k} {v}" for k, v in sorted(stats.items())))
    shadowed = shadowed_skills(target)
    if shadowed:
        log(f"  không cài skill khung trùng lệnh riêng của dự án (.claude/commands/): {', '.join(shadowed)}")
    if stats.get("updated-new"):
        log(
            "  ⚠ có file .xtemplates-new: file sẵn có của dự án khác bản khung — so sánh và gộp tay; hook/settings chưa "
            "gộp thì hàng rào của khung có thể không chạy (`xt.py doctor` báo lỗi)"
        )


def root_template_jobs(target: Path, preset: str | None = None) -> list[tuple[str, Path, Callable[[str], str]]]:
    """(tên, mẫu nguồn, hàm biến đổi) của file gốc từ framework/templates có mặt trong khung."""
    jobs: list[tuple[str, Path, Callable[[str], str]]] = []
    for name, tmpl in ROOT_TEMPLATES.items():
        tsrc = SRC / "framework" / "templates" / tmpl
        if tsrc.exists():
            body = template_body if name != "PROGRESS.md" else lambda t: progress_with_head(template_body(t), target)
            if name == "xt.yaml":
                body = lambda t: yaml_with_preset(template_body(t), preset)
            jobs.append((name, tsrc, body))
    return jobs


def root_template_hash(tmpl: Path, preset: str | None = None) -> str:
    """Hash nhận diện mẫu file gốc (ghi vào manifest): mẫu đã bỏ frontmatter, TRƯỚC khi thay SHA HEAD — PROGRESS.md mang
    SHA đổi theo HEAD của dự án, không được làm mẫu "đổi" (D-114)."""
    body = source_bytes(tmpl, template_body).decode("utf-8")
    return sha256((yaml_with_preset(body, preset) if tmpl.name == "xt.yaml" else body).encode("utf-8"))


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


GIT_HOOKS = ("pre-commit", "commit-msg", "pre-push")
GIT_HOOK_MARK = "# xtemplates-git-hook"  # dòng 2 của hook khung — hook không có dấu là của dự án, không đè


def git_hooks_dir(target: Path) -> Path | None:
    """Thư mục hook git của repo chứa `target` (`git rev-parse --git-path hooks` — theo `core.hooksPath`); không phải
    repo git hay không chạy được git → None."""
    try:
        r = subprocess.run(
            ["git", "-C", str(target), "rev-parse", "--git-path", "hooks"], capture_output=True, text=True, timeout=10
        )
    except (OSError, subprocess.SubprocessError):
        return None
    out = r.stdout.strip()
    if r.returncode != 0 or not out:
        return None
    return Path(out) if Path(out).is_absolute() else target / out


def git_hook_action(dst: Path) -> str:
    """Quyết định (không ghi) cho một git hook: 'copied' (chưa có) | 'updated' (hook khung, khác bản mới) | 'kept' (hook
    khung, giống bản mới) | 'kept-own' (hook không mang dấu khung — của dự án, husky, pre-commit… — hay symlink)."""
    if dst.is_symlink():
        return "kept-own"
    if not dst.exists():
        return "copied"
    if GIT_HOOK_MARK not in dst.read_text(encoding="utf-8", errors="replace"):
        return "kept-own"
    return (
        "kept"
        if dst.read_bytes() == (SRC / "framework" / "templates" / "git-hooks" / dst.name).read_bytes()
        else "updated"
    )


def shown_path(target: Path, path: Path) -> str:
    """Đường dẫn để báo/ghi manifest: tương đối `target` khi nằm trong dự án, ngược lại tuyệt đối (worktree, hooksPath
    ngoài dự án)."""
    full = path.resolve()
    return full.relative_to(target).as_posix() if full.is_relative_to(target) else full.as_posix()


def git_hooks_plan(target: Path, no_harness: bool, no_git_hooks: bool) -> dict[str, Any]:
    """Kế hoạch git hook (AUD-HAR-204): thư mục hook thật (`core.hooksPath` có thể là thư mục được track như `.husky/` —
    `in_tree`: commit sẽ mang hook) và hành động từng hook; bỏ qua kèm lý do."""
    reason = "--no-harness" if no_harness else "--no-git-hooks" if no_git_hooks else None
    hooks = None if reason else git_hooks_dir(target)
    if hooks is None:
        return {"action": "skipped", "reason": reason or "không phải repo git"}
    where = shown_path(target, hooks)
    rows = [{"name": n, "path": shown_path(target, hooks / n), "action": git_hook_action(hooks / n)} for n in GIT_HOOKS]
    in_tree = not Path(where).is_absolute() and ".git" not in Path(where).parts
    return {"action": "install", "dir": where, "in_tree": in_tree, "hooks": rows}


def install_git_hooks(target: Path) -> None:
    """Sàn chung không phụ thuộc hook của công cụ (ADR-0064 lát C): `pre-commit` (cổng commit), `commit-msg` (subject,
    ghi công AI), `pre-push` (nhánh chính, force). Hook đã có mà không mang dấu khung (của dự án, husky, pre-commit…)
    giữ nguyên và báo để gộp tay; hook của khung thì cập nhật. Hook khung có mặt sau cài ghi vào manifest.json
    (`git_hooks`, AUD-HAR-204)."""
    hooks = git_hooks_dir(target)
    if hooks is None:
        log("  git hook: không phải repo git — bỏ qua (chạy lại install.py sau `git init`)")
        return
    hooks.mkdir(parents=True, exist_ok=True)
    ours: list[str] = []
    for name in GIT_HOOKS:
        dst = hooks / name
        if git_hook_action(dst) == "kept-own":
            log(
                f"  git hook {name}: dự án đã có hook riêng — giữ nguyên; gộp tay `.xtemplates/framework/templates/git-hooks/{name}`"
            )
            continue
        shutil.copy2(SRC / "framework" / "templates" / "git-hooks" / name, dst)
        dst.chmod(0o755)
        ours.append(shown_path(target, dst))
        log(f"  git hook {name}: cài ({dst})")
    record_manifest_paths(target, "git_hooks", ours)


# Adapter hook cho công cụ agent khác (ADR-0064 lát B): host → (mẫu trong framework/templates/harness/, đích ở dự án).
ADAPTERS = {
    "codex": ("codex-hooks.json", ".codex/hooks.json"),
    "gemini": ("gemini-settings.json", ".gemini/settings.json"),
    "cursor": ("cursor-hooks.json", ".cursor/hooks.json"),
    "copilot": ("copilot-xt.json", ".github/hooks/xt.json"),
    "grok": ("grok-xt.json", ".grok/hooks/xt.json"),
    "opencode": ("opencode-xt.ts", ".opencode/plugins/xt.ts"),
}
GEMINI_HOOK_NAME = "xt-guard"


def gemini_merged(dst: Path, src: Path) -> dict[str, Any] | None:
    """Nội dung `.gemini/settings.json` sau khi gộp hook `BeforeTool` của khung (tên `xt-guard`) — giữ mọi khoá khác,
    thay bản cũ của khung; file không đọc được dạng object JSON → None (giữ nguyên). Không ghi gì."""
    ours = json.loads(src.read_text(encoding="utf-8"))["hooks"]["BeforeTool"]
    try:
        data = json.loads(dst.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = None
    hooks = data.get("hooks") if isinstance(data, dict) else None
    if not isinstance(data, dict) or not isinstance(hooks, (dict, type(None))):
        return None
    entries = (hooks or {}).get("BeforeTool")
    # `BeforeTool` dạng lạ của dự án (không phải danh sách): giữ nguyên file, không thay im lặng (AUD-HAR-207)
    if entries is not None and not isinstance(entries, list):
        return None
    keep = [e for e in entries if GEMINI_HOOK_NAME not in json.dumps(e)] if entries else []
    data["hooks"] = {**(hooks or {}), "BeforeTool": keep + ours}
    return data


def merge_gemini_settings(dst: Path, src: Path) -> str:
    """Ghi bản gộp của `gemini_merged` vào `.gemini/settings.json` có sẵn. Trả 'merged' | 'kept' (không đọc được/dạng lạ)
    | 'skipped-symlink' (không ghi xuyên liên kết ra ngoài dự án — AUD-HAR-207, như AUD-HAR-010)."""
    if dst.is_symlink():
        return "skipped-symlink"
    data = gemini_merged(dst, src)
    if data is None:
        return "kept"
    dst.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return "merged"


ADAPTER_OURS = ("copied", "kept", "updated")  # đích sau cài là bản khung → ghi manifest `adapters`


def adapter_src(host: str) -> Path:
    return SRC / "framework" / "templates" / "harness" / ADAPTERS[host][0]


def adapter_action(target: Path, host: str) -> str:
    """Quyết định (không ghi) cho adapter của `host`: Gemini có sẵn (không phải symlink) → 'merged' | 'kept'; còn lại như
    `classify_copy` (symlink → 'skipped-symlink')."""
    dst = target / ADAPTERS[host][1]
    if host == "gemini" and dst.is_file() and not dst.is_symlink():
        return "merged" if gemini_merged(dst, adapter_src(host)) is not None else "kept"
    return classify_copy(adapter_src(host), dst)[0]


def adapters_plan(target: Path, hosts: list[str]) -> list[dict[str, str]]:
    """Kế hoạch adapter (`--harness`, AUD-HAR-204): host, đường dẫn đích, hành động."""
    return [{"host": h, "path": ADAPTERS[h][1], "action": adapter_action(target, h)} for h in hosts]


def install_adapters(target: Path, hosts: list[str]) -> None:
    """Chép cấu hình hook của từng host (copy-if-absent; Gemini gộp vào settings có sẵn). Adapter gọi guard của harness
    `.claude/` — không có harness thì hook của host cho qua (báo ở đây để người biết). Adapter là bản khung sau cài ghi
    vào manifest.json (`adapters`, gộp với lần cài trước — AUD-HAR-204)."""
    if not hosts:
        return
    if not (target / ".claude" / "hooks" / "guard.py").is_file():
        log("  ⚠ adapter cần harness `.claude/hooks/guard.py` (cài không `--no-harness`) — chưa có thì hook cho qua")
    recorded = load_manifest_doc(target).get("adapters")
    ours = [p for p in recorded if isinstance(p, str)] if isinstance(recorded, list) else []
    for host in hosts:
        rel = ADAPTERS[host][1]
        dst = target / rel
        if host == "gemini" and dst.is_file():
            status = merge_gemini_settings(dst, adapter_src(host))
            mine = status == "merged"  # `kept` ở đây = không đọc được, giữ file của dự án
        else:
            status = copy_if_absent(adapter_src(host), dst)
            mine = status in ADAPTER_OURS
        if mine:
            ours.append(rel)
        log(
            f"  adapter {host}: {rel} ({status}) — công cụ cần tin cậy hook dự án một lần (xem templates/harness/README.md)"
        )
    record_manifest_paths(target, "adapters", ours)


# Gói sản phẩm (`--pack <id>`, ADR-0068 lát B/C): `framework/templates/packs/<id>/` gồm `pack.json` (schema 1, `id` = tên
# thư mục, owner, hạn hỗ trợ, compat, profile, control ID, khoá `xt_yaml`), `starter/` (mã khởi đầu — chỉ chép vào repo
# SẠCH: chưa có `package.json` và manifest chưa ghi gói; copy-if-absent; sau lần đầu là của dự án: không cập nhật, không
# băm) và `managed/` (file gói sở hữu — như harness: hash trong `files` của manifest; chưa sửa → cập nhật, đã sửa →
# `.xtemplates-new`). Lùi bản = cài lại từ bản khung cũ: file managed còn đúng hash bản mới được đưa về bản cũ.
PACKS_DIR = Path("framework") / "templates" / "packs"
PACK_ID_RE = re.compile(r"[a-z0-9][a-z0-9-]*")  # tên thư mục gói — không `/`, `..`: không đọc ra ngoài packs/
PACK_YAML_KEY_RE = re.compile(r"[A-Za-z_][\w-]*")  # khoá cấp 1 của xt.yaml (cùng dạng `YAML_KEY_RE`)
PACK_BROWNFIELD = "package.json"  # dự án đã có mã (stack của gói đầu: Node) → không chép starter
PACK_MODES = {
    "fresh": "repo sạch — chép starter, đặt khoá xt.yaml của gói",
    "brownfield": f"dự án đã có {PACK_BROWNFIELD} — không chép starter; khoá xt.yaml chỉ gợi ý",
    "upgrade": "gói đã cài — starter là của dự án; file managed nâng theo hash manifest",
}
STARTER_SKIP = {"upgrade": "owned-by-project", "brownfield": "skipped-brownfield"}


def available_packs() -> list[str]:
    """Id các gói có `pack.json` trong bản khung đang cài."""
    root = SRC / PACKS_DIR
    return sorted(d.name for d in root.iterdir() if (d / "pack.json").is_file()) if root.is_dir() else []


def _pack_yaml_pair(key: object, value: object) -> bool:
    """Một khoá `xt_yaml` hợp lệ: khoá YAML cấp 1, giá trị chuỗi MỘT dòng — không chen được dòng lạ vào xt.yaml."""
    if not isinstance(key, str) or not isinstance(value, str):
        return False
    # `yaml_set_keys` ghi nháy JSON; `yaml_get` (dev-task.sh)/`yaml_scalar` (xt.py) không giải escape → chỉ nhận giá trị
    # mà nháy JSON giữ nguyên chữ: in được, không `"`, không `\` (AUD-HAR-227).
    return PACK_YAML_KEY_RE.fullmatch(key) is not None and value.isprintable() and not set(value) & {'"', "\\"}


def pack_problem(pack_id: str, doc: object) -> str | None:
    """Lý do `pack.json` không hợp lệ (None nếu hợp lệ): object, `schema` = 1, `id` = tên thư mục, `xt_yaml` là
    {khoá cấp 1: lệnh một dòng}."""
    if not isinstance(doc, dict):
        return "không phải object JSON"
    schema = doc.get("schema")
    if schema != 1 or isinstance(schema, bool):
        return f"schema {schema!r} — chỉ hỗ trợ 1"
    if doc.get("id") != pack_id:
        return f"id {doc.get('id')!r} khác tên thư mục {pack_id!r}"
    keys = doc.get("xt_yaml")
    if not isinstance(keys, dict) or not all(_pack_yaml_pair(k, v) for k, v in keys.items()):
        return "xt_yaml phải là object {khoá cấp 1: lệnh một dòng}"
    return None


def load_pack(pack_id: str) -> dict[str, Any]:
    """`pack.json` đã kiểm của gói `pack_id`; id lạ/thiếu gói/`pack.json` hỏng → ValueError (lý do để báo)."""
    root = SRC / PACKS_DIR / pack_id
    if PACK_ID_RE.fullmatch(pack_id) is None or not (root / "pack.json").is_file():
        raise ValueError(f"không biết gói {pack_id!r} — có: {', '.join(available_packs()) or 'chưa có gói nào'}")
    try:
        doc = json.loads((root / "pack.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError(f"{pack_id}/pack.json không đọc được ({exc})") from exc
    problem = pack_problem(pack_id, doc)
    if problem:
        raise ValueError(f"{pack_id}/pack.json: {problem}")
    pack: dict[str, Any] = doc
    return pack


def pack_tree(pack_id: str, part: str) -> list[tuple[str, Path]]:
    """(đường dẫn đích POSIX tương đối gốc dự án, file nguồn) của `starter/` hoặc `managed/`; thiếu thư mục → rỗng."""
    root = SRC / PACKS_DIR / pack_id / part
    if not root.is_dir():
        return []
    files = (p for p in sorted(root.rglob("*")) if p.is_file() and "__pycache__" not in p.parts)
    return [(p.relative_to(root).as_posix(), p) for p in files]


def _str_list(value: object) -> list[str]:
    return [v for v in value if isinstance(v, str)] if isinstance(value, list) else []


def recorded_packs(target: Path) -> dict[str, Any]:
    """`packs` của manifest.json (thiếu/hỏng → {})."""
    packs = load_manifest_doc(target).get("packs")
    return packs if isinstance(packs, dict) else {}


def pack_managed_paths(target: Path) -> set[str]:
    """Đường dẫn managed của mọi gói đã ghi trong manifest — bước harness giữ hash của chúng (như file gốc/GitHub)."""
    return {
        p for rec in recorded_packs(target).values() if isinstance(rec, dict) for p in _str_list(rec.get("managed"))
    }


def pack_mode(target: Path, pack_id: str) -> str:
    """`upgrade` (manifest đã ghi gói) | `brownfield` (có `package.json`, kể cả symlink) | `fresh`."""
    if pack_id in recorded_packs(target):
        return "upgrade"
    marker = target / PACK_BROWNFIELD
    return "brownfield" if marker.exists() or marker.is_symlink() else "fresh"


def under_symlink(target: Path, rel: str) -> bool:
    """Đích hoặc một thư mục giữa gốc dự án và đích là symlink — không ghi xuyên liên kết ra ngoài dự án (AUD-HAR-010)."""
    path = target / rel
    return any(p.is_symlink() for p in (path, *path.parents) if p != target and p.is_relative_to(target))


def starter_action(target: Path, rel: str, src: Path, mode: str) -> str:
    """Quyết định (không ghi) cho một file starter: repo sạch → 'copied' | 'kept' (giống hệt) | 'kept-own' (file của dự
    án) | 'skipped-symlink'; brownfield → 'skipped-brownfield'; gói đã cài → 'owned-by-project'."""
    if mode in STARTER_SKIP:
        return STARTER_SKIP[mode]
    dst = target / rel
    if under_symlink(target, rel):
        return "skipped-symlink"
    if not dst.exists():
        return "copied"
    if dst.is_file() and dst.read_bytes() == src.read_bytes():
        return "kept"
    return "merged" if rel == ".gitignore" and gitignore_missing(dst, src) else "kept-own"


def gitignore_missing(dst: Path, src: Path) -> list[str]:
    """Dòng ignore của starter mà `.gitignore` sẵn có của dự án chưa có (`node_modules/`, `.env`…) — file của dự án giữ
    nguyên, chỉ nối thêm (review lát B 🟢); không đọc được → rỗng (giữ file, không nối)."""
    try:
        have = set(dst.read_text(encoding="utf-8").splitlines())
    except (OSError, UnicodeDecodeError):
        return []
    return [line for line in src.read_text(encoding="utf-8").splitlines() if line and line not in have]


def merge_gitignore(dst: Path, src: Path) -> None:
    text = dst.read_text(encoding="utf-8")
    lead = "" if not text or text.endswith("\n") else "\n"
    dst.write_text(text + lead + "\n".join(gitignore_missing(dst, src)) + "\n", encoding="utf-8")


def managed_action(target: Path, rel: str, src: Path, files: dict[str, str], mode: str) -> tuple[str, bytes]:
    """Quyết định (không ghi) cho một file managed: như harness (`classify_copy` với hash manifest). File chưa có ở dự
    án brownfield — hoặc dự án chưa nhận đề xuất trước (`.xtemplates-new` còn đó) — chỉ thành đề xuất `updated-new`:
    thêm workflow/script vào dự án đang chạy là đổi hành vi (hotel-manager đòi mọi job PR là required check — lát C)."""
    if under_symlink(target, rel):
        return "skipped-symlink", b""
    dst = target / rel
    if not dst.exists() and (mode == "brownfield" or dst.with_name(dst.name + ".xtemplates-new").exists()):
        return "updated-new", source_bytes(src)
    return classify_copy(src, dst, installed_hash=files.get(rel))


def pack_plan(target: Path, pack: dict[str, Any]) -> dict[str, Any]:
    """Kế hoạch gói cho `--plan` — cùng hàm quyết định với lần cài thật, không ghi gì."""
    pid, files = pack["id"], load_manifest(target)
    mode = pack_mode(target, pid)
    starter = [{"path": r, "action": starter_action(target, r, s, mode)} for r, s in pack_tree(pid, "starter")]
    managed = [
        {"path": r, "action": managed_action(target, r, s, files, mode)[0]} for r, s in pack_tree(pid, "managed")
    ]
    return {
        "id": pid,
        "mode": mode,
        "starter": starter,
        "managed": managed,
        "xt_yaml": pack_yaml_plan(target, mode, dict(pack["xt_yaml"])),
    }


def _action_counts(actions: Counter[str]) -> str:
    return " · ".join(f"{k} {v}" for k, v in sorted(actions.items())) or "không có file"


def install_pack_starter(target: Path, pid: str, mode: str) -> list[str]:
    """Chép starter (chỉ repo sạch, copy-if-absent); trả đường dẫn đã chép."""
    actions: Counter[str] = Counter()
    copied: list[str] = []
    for rel, src in pack_tree(pid, "starter"):
        action = starter_action(target, rel, src, mode)
        actions[action] += 1
        if action == "copied":
            (target / rel).parent.mkdir(parents=True, exist_ok=True)
            copied.append(rel)
        if action == "merged":
            merge_gitignore(target / rel, src)
        write_copy(src, target / rel, action, src.read_bytes())
    log(f"  gói {pid}/starter: {_action_counts(actions)}")
    return copied


def install_pack_managed(target: Path, pid: str, mode: str) -> list[str]:
    """File managed như harness: cập nhật theo hash, `.xtemplates-new` khi dự án đã sửa (hoặc file mới ở brownfield);
    hash mẫu vào `files` của manifest (`HASHED`), `kept-own`/symlink giữ hash cũ. Trả mọi đường dẫn managed của gói."""
    files = load_manifest(target)
    actions: Counter[str] = Counter()
    rels: list[str] = []
    for rel, src in pack_tree(pid, "managed"):
        status, data = managed_action(target, rel, src, files, mode)
        if status in ("copied", "updated-new"):
            (target / rel).parent.mkdir(parents=True, exist_ok=True)
        write_copy(src, target / rel, status, data)
        actions[status] += 1
        rels.append(rel)
        if status in HASHED:
            files[rel] = sha256(data)
    write_manifests(target, files, load_rules(target))
    log(f"  gói {pid}/managed: {_action_counts(actions)}")
    if actions["updated-new"]:
        log(
            f"  ⚠ gói {pid}: bản gói ở <file>.xtemplates-new (dự án đã sửa file, hoặc file mới ở dự án đang chạy) — "
            "so sánh rồi đổi tên/gộp tay để nhận"
        )
    return rels


def yaml_set_keys(text: str, values: dict[str, str]) -> str:
    """Đặt giá trị khoá cấp 1 (nháy JSON như các dòng khác): thay dòng `khoá:` đã có, chưa có thì nối cuối; giữ kiểu
    xuống dòng của file."""
    nl = "\r\n" if "\r\n" in text else "\n"
    for key, value in values.items():
        line = f"{key}: {json.dumps(value, ensure_ascii=False)}"
        pattern = re.compile(rf"^{re.escape(key)}:[^\r\n]*", re.M)
        if pattern.search(text):
            text = pattern.sub(lambda _m: line, text)
        else:
            text += ("" if not text or text.endswith("\n") else nl) + line + nl
    return text


YAML_EMPTY_RE = re.compile(r"""^(?:""|'')?[ \t]*(?:#.*)?$""")


def yaml_own_value(text: str, key: str) -> str | None:
    """Giá trị thô (bỏ chú thích cuối dòng) của khoá cấp 1 trong xt.yaml của dự án; vắng → None, rỗng (`""`, `''`,
    không ghi gì) → ""."""
    m = re.search(rf"^{re.escape(key)}:[ \t]*([^\r\n]*)", text, re.M)
    if m is None:
        return None
    raw = m[1]
    return "" if YAML_EMPTY_RE.match(raw) else raw.split(" #", 1)[0].strip()


def pack_yaml_split(own: str, values: dict[str, str]) -> tuple[dict[str, str], dict[str, dict[str, str]]]:
    """(khoá sẽ đặt: vắng/rỗng/đã đúng giá trị gói, khoá giữ của dự án: {khoá: {own, pack}}) — repo sạch vẫn có thể đã
    điền lệnh riêng (Python, Go…): không ghi đè lệnh của dự án (review lát B 🟠)."""
    apply: dict[str, str] = {}
    kept: dict[str, dict[str, str]] = {}
    for key, value in values.items():
        cur = yaml_own_value(own, key)
        if cur in (None, "", json.dumps(value, ensure_ascii=False)):
            apply[key] = value
        else:
            kept[key] = {"own": str(cur), "pack": value}
    return apply, kept


def pack_yaml_plan(target: Path, mode: str, values: dict[str, str]) -> dict[str, Any]:
    """Phần `xt_yaml` của `--plan`: repo sạch → `apply` (+ `kept` khi dự án đã điền khoá); còn lại → `suggested`."""
    if mode != "fresh":
        return {"suggested": dict(values)}
    path = target / "xt.yaml"
    own = (read_own_yaml(path) or "") if path.is_file() and not path.is_symlink() else ""
    apply, kept = pack_yaml_split(own, values)
    return {"apply": apply, **({"kept": kept} if kept else {})}


def install_pack_yaml(target: Path, pid: str, mode: str, values: dict[str, str]) -> None:
    """Khoá `xt_yaml` của gói: chỉ ghi khi chép starter lần này (repo sạch), và chỉ khoá vắng/rỗng — khoá dự án đã điền
    giữ nguyên, báo kèm giá trị của gói; dự án đã có cấu hình (brownfield/nâng bản) → chỉ gợi ý."""
    if not values:
        return
    names = ", ".join(values)
    if mode != "fresh":
        log(f"  gói {pid}/xt.yaml: gợi ý khoá {names} — không ghi (dự án đã có cấu hình; giá trị ở `--plan`)")
        return
    path = target / "xt.yaml"
    if path.is_symlink():
        log(f"  ⚠ bỏ qua symlink {path} — tự đặt khoá {names} của gói")
        return
    own = read_own_yaml(path) if path.exists() else ""
    if own is None:
        return
    apply, kept = pack_yaml_split(own, values)
    path.write_bytes(yaml_set_keys(own, apply).encode("utf-8"))
    log(f"  gói {pid}/xt.yaml: đặt {len(apply)} khoá ({', '.join(apply) or 'không có'})")
    for key, pair in kept.items():
        log(f"  ⚠ gói {pid}/xt.yaml: giữ `{key}: {pair['own']}` của dự án — gói đề nghị {json.dumps(pair['pack'])}")


def record_pack(target: Path, pid: str, entry: dict[str, Any]) -> None:
    """Ghi `packs.<id>` vào manifest.json, giữ gói khác và mọi khoá khác."""
    doc = load_manifest_doc(target)
    doc["packs"] = {**recorded_packs(target), pid: entry}
    write_atomic(target / MANIFEST_V2, json.dumps(doc, indent=2, sort_keys=True) + "\n")


def install_pack(target: Path, pack: dict[str, Any], version: str) -> None:
    """Bước 3c (`--pack`): starter (repo sạch) → managed (theo hash) → manifest `packs` → khoá xt.yaml."""
    pid = pack["id"]
    mode = pack_mode(target, pid)
    log(f"  gói {pid}: {mode} — {PACK_MODES[mode]}")
    prior = recorded_packs(target).get(pid)
    starter = install_pack_starter(target, pid, mode)
    if mode == "upgrade":
        starter = _str_list(prior.get("starter")) if isinstance(prior, dict) else []
    managed = install_pack_managed(target, pid, mode)
    record_pack(target, pid, {"version": version, "starter": starter, "managed": managed})
    install_pack_yaml(target, pid, mode, pack["xt_yaml"])


def install_root_templates(
    target: Path, label: str, inferred: dict[str, str] | None = None, preset: str | None = None
) -> None:
    """Bước 3: file gốc từ framework/templates — copy-if-absent, bỏ frontmatter; hash mẫu (`root_template_hash`) vào
    CÙNG map `files` của manifest với harness: chưa sửa → cập nhật tại chỗ; đã sửa mà mẫu không đổi → `kept-own` (im
    lặng); đã sửa và mẫu đổi → `.xtemplates-new` một lần. Manifest chưa có hash file gốc → dùng hash suy từ mẫu cũ
    (`inferred`, chỉ để phân loại). `xt.yaml` của dự án nhận khoá mới của mẫu dạng chú thích (`label`)."""
    manifest = load_manifest(target)
    hints = inferred or {}
    applied = None
    for name, tsrc, body in root_template_jobs(target, preset):
        th = root_template_hash(tsrc, preset)
        r, data = classify_copy(
            tsrc,
            target / name,
            False,
            body,
            manifest.get(name, hints.get(name)),
            th,
            preserve_yaml_policy=name == "xt.yaml",
        )
        new = yaml_keep_policy(data, (target / name).read_bytes()) if name == "xt.yaml" and r == "updated-new" else data
        write_copy(tsrc, target / name, r, new)  # nối khoá (dưới) vẫn so với mẫu gốc
        log(f"  {name}: " + ROOT_MESSAGES.get(r, r).format(name=name))
        if r != "skipped-symlink":  # `HASHED` ghi hash mẫu mới; `kept-own`: hash mẫu = hash đã cài, ghi lại như giữ
            manifest[name] = th
        if name == "xt.yaml" and r in YAML_MERGE:
            append_yaml_keys(target / name, data.decode("utf-8"), label)
        if name == "xt.yaml" and r == "copied":
            applied = preset
    write_manifests(target, manifest, load_rules(target), applied)


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


YAML_QUOTED_RE = re.compile(r""""(?:[^"\\]|\\.)*"|'[^']*'""")  # chuỗi trích dẫn — `#` bên trong không phải chú thích


def yaml_gap(own: str) -> int:
    """Số dòng trống trước khối nối, theo Prettier (3.9.10, đo 2026-11-06): một dòng; HAI khi dòng nội dung cuối mang
    chú thích cuối dòng (`perf: x # y`) — Prettier dồn khối chú thích cuối file xuống thêm một dòng, một dòng thì
    `prettier --check` của dự án đỏ (X-Company #98, AUD-HAR-304)."""
    last = next((ln for ln in reversed(own.splitlines()) if ln.strip()), "#")
    inline = not last.lstrip().startswith("#") and re.search(r"\s#", YAML_QUOTED_RE.sub("", last)) is not None
    return 2 if inline else 1


def yaml_block(own: str, lines: list[str], label: str) -> str:
    """Khối nối cuối xt.yaml: dòng trống ngăn cách (`yaml_gap`; dòng trống sẵn có ở cuối file được tính, không xoá),
    MỘT dòng đánh dấu, rồi `# <dòng mẫu>`; cùng kiểu xuống dòng với file."""
    nl = "\r\n" if "\r\n" in own else "\n"
    trailing = own[len(own.rstrip("\r\n")) :].count("\n")
    lead = nl * max(yaml_gap(own) + 1 - trailing, 0) if own else ""
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
        rules = json.loads((SRC / GITHUB_FILES[".github/rulesets/main.json"]).read_text(encoding="utf-8"))["rules"]
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
    """Bước 3b (--with-github): ruleset mẫu + PR template + Dependabot + workflow CI/quét bí mật/`pr-steward` + stub
    `merge-gate` tạm (D-122) (copy-if-absent; file chưa sửa so với lần cài trước thì cập nhật tại chỗ), ghi hash vào
    manifest, cảnh báo required check chưa có job."""
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
            f"  ⚠ ruleset mẫu đòi required check chưa có job: {', '.join(checks)} — viết job ĐÚNG tên trước khi import "
            "ruleset, hoặc bỏ khỏi "
            ".github/rulesets/main.json; tới lúc đó `protection-guard` đỏ và PR treo chờ check"
        )


GITIGNORE_LINES = (
    ".autopilot/",
    ".claude/settings.local.json",
)  # trạng thái autopilot; quyền/đường dẫn máy cá nhân (LOOP-HARNESS-032)
# Dòng tương đương đã có thì không thêm (cùng tập với `AUTOPILOT_IGNORES`/`SETTINGS_LOCAL_IGNORES` của xt.py — review #381)
GITIGNORE_EQUIV = {
    ".autopilot/": (".autopilot/", ".autopilot", "/.autopilot/", "/.autopilot"),
    ".claude/settings.local.json": (
        ".claude/settings.local.json",
        "/.claude/settings.local.json",
        "**/.claude/settings.local.json",
        "settings.local.json",
        "**/settings.local.json",
        ".claude/*.local.json",
        "*.local.json",
    ),
}


GITIGNORE_PROBE = {".autopilot/": ".autopilot/state.json", ".claude/settings.local.json": ".claude/settings.local.json"}


def gitignore_blocks(target: Path, rel: str) -> bool | None:
    """`rel` có bị một file `.gitignore` chặn không, theo `git check-ignore` (mọi mẫu git thật — `.claude/`, `.claude/*`,
    `*.local.*`, BOM, `!` phủ định; AUD-HAR-179; cùng luật `gitignore_blocks` của xt.py). Chỉ tính `.gitignore` trong cây
    (đường tương đối; exclude toàn cục kể cả `~/.gitignore`, `.git/info/exclude` chỉ có ở máy này). Không có git/không
    phải repo → None."""
    hits = gitignore_hits(target, [rel])
    return None if hits is None else bool(hits)


def gitignore_hits(target: Path, rels: list[str], no_index: bool = True) -> list[tuple[str, str]] | None:
    """(đường, mẫu) của các `rels` bị một `.gitignore` TRONG CÂY của dự án chặn (mẫu `!` phủ định không tính;
    `.gitignore` nằm trong `.xtemplates/` là của khung, không tính), một lần gọi `git check-ignore -v -z --stdin`.
    `no_index=False`: file đã track không tính (git không bỏ qua file đã track). Không có git/không phải repo → None."""
    if not rels:
        return []
    cmd = ["git", "-C", str(target), "check-ignore", "-v", "-z", "--stdin", *(["--no-index"] if no_index else [])]
    try:
        r = subprocess.run(cmd, input="\0".join(rels) + "\0", capture_output=True, text=True, timeout=30, check=False)
    except (OSError, subprocess.SubprocessError):
        return None
    if r.returncode not in (0, 1):
        return None
    f = r.stdout.split("\0")
    # Mỗi bản ghi: nguồn, số dòng, mẫu, đường. `.gitignore` trong cây: git in đường tương đối; exclude toàn cục (vd
    # `~/.gitignore`) in đường tuyệt đối.
    recs = [f[i : i + 4] for i in range(0, len(f) - 3, 4)]
    return [
        (path, pattern)
        for src, _, pattern, path in recs
        if not os.path.isabs(src)
        and Path(src).name == ".gitignore"
        and not src.startswith(".xtemplates/")
        and not pattern.startswith("!")
    ]


def warn_ignored_framework(target: Path) -> None:
    """AUD-HAR-300: `.gitignore` của dự án che file khung trong `.xtemplates/` (vd mẫu tên trần `PLAN.md` che
    `templates/PLAN.md`) → clone sạch thiếu file. Chỉ báo — thêm `!.xtemplates/**` sẽ kéo cả file dự án cố ý bỏ qua."""
    xt_dir = target / ".xtemplates"
    rels = sorted(
        p.relative_to(target).as_posix() for p in xt_dir.rglob("*") if p.is_file() and "__pycache__" not in p.parts
    )
    hits = gitignore_hits(target, rels, no_index=False) or []  # file khung đã track: clone sạch vẫn có
    if hits:
        shown = ", ".join(f"{path} (mẫu `{pattern}`)" for path, pattern in hits[:5])
        more = f" và {len(hits) - 5} file khác" if len(hits) > 5 else ""
        log(
            f"  ⚠ .gitignore của dự án che {len(hits)} file khung trong .xtemplates/ — clone sạch sẽ thiếu: {shown}{more};"
            " sửa mẫu cho hẹp lại (vd `/PLAN.md`) hoặc thêm dòng `!<đường>`"
        )


def _gitignore_has(target: Path, line: str, have: set[str]) -> bool:
    """Dòng `line` của khung đã có hiệu lực: git nói đã chặn, hoặc (không hỏi được git) có dòng tương đương."""
    blocked = gitignore_blocks(target, GITIGNORE_PROBE[line])
    return bool(have & set(GITIGNORE_EQUIV[line])) if blocked is None else blocked


def ensure_gitignore(target: Path) -> None:
    """Bước 4: .gitignore thêm `.autopilot/` và `.claude/settings.local.json` nếu thiếu (tạo mới nếu chưa có file)."""
    gi = target / ".gitignore"
    if gi.is_symlink():  # file của dự án (không phải bản khung): không ghi qua liên kết, không gỡ (AUD-CFG-003)
        log(f"  ⚠ bỏ qua symlink {gi} — tự thêm dòng `{'`, `'.join(GITIGNORE_LINES)}` vào file thật")
        return
    if gi.exists():
        have = {ln.strip() for ln in gi.read_text(encoding="utf-8", errors="replace").splitlines()}  # AUD-HAR-180
        missing = [ln for ln in GITIGNORE_LINES if not _gitignore_has(target, ln, have)]
        if missing:
            with gi.open("a", encoding="utf-8") as fh:
                fh.write(
                    "\n# X-Templates: trạng thái autopilot cục bộ, settings cá nhân\n"
                    + "".join(f"{ln}\n" for ln in missing)
                )
            log("  .gitignore: thêm " + ", ".join(missing))
    else:
        body = "".join(f"{ln}\n" for ln in GITIGNORE_LINES)
        gi.write_text(f"# X-Templates: trạng thái autopilot cục bộ, settings cá nhân\n{body}", encoding="utf-8")
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
    mệnh đề trùng hệt in một lần — giữ lần đầu theo thứ tự CHANGELOG (bản mới nhất), mục hết mệnh đề thì bỏ (D-159)."""
    out: list[tuple[str, list[str]]] = []
    seen: set[str] = set()
    for name, lines in changelog_sections(text):
        version = parse_version(name)
        if name != "Unreleased" and (version is None or version <= since):
            continue
        clauses = [
            c for c in dict.fromkeys(c for block in text_blocks(lines) for c in step_clauses(block)) if c not in seen
        ]
        seen.update(clauses)
        if clauses:
            out.append((name, clauses))
    return out


CHANGELOG_ARCHIVE = "CHANGELOG-ARCHIVE.md"  # T-3651: bản < 3.20.0 dời khỏi CHANGELOG.md, cùng định dạng


def read_changelog(src: Path) -> str:
    """CHANGELOG.md của khung nối tiếp các mục `## ` của CHANGELOG-ARCHIVE.md (bản cũ hơn, nếu có) — thứ tự mới → cũ như
    một file; phần đầu file lưu trữ (trước mục đầu) bỏ, không dính vào mục cuối của CHANGELOG. Ném
    OSError/UnicodeDecodeError khi không đọc được."""
    text = (src / "CHANGELOG.md").read_text(encoding="utf-8")
    archive = src / CHANGELOG_ARCHIVE
    if not archive.is_file():
        return text
    old = archive.read_text(encoding="utf-8")
    first = re.search(r"^## ", old, re.M)
    return text + "\n" + (old[first.start() :] if first else "")


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
        text = read_changelog(SRC)
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


STAGE_LEDGER = "docs/autopilot/STAGE.json"  # sổ giai đoạn sản phẩm (ADR-0058) — file của dự án, installer không ghi tay


def run_stage(target: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """`xt.py stage …` của bản VỪA CÀI, gốc = dự án đích (bỏ CLAUDE_PROJECT_DIR của phiên đang chạy installer và GIT_DIR…
    của môi trường — lịch sử sổ phải là của dự án đích, review #339)."""
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR" and k not in GIT_LOCATION_ENV}
    cmd = [sys.executable, str(target / ".xtemplates" / "scripts" / "xt.py"), "stage", *args]
    return subprocess.run(cmd, cwd=target, env=env, capture_output=True, text=True, timeout=120)


def report_stage(target: Path, stage_init: bool) -> None:
    """Giai đoạn sản phẩm sau cài (ADR-0058 lát E, D-249): không đoán giai đoạn — chỉ `--stage-init` (dự án mới) tạo sổ;
    sổ có sẵn không bị chạm, nhưng được kiểm bằng xt.py mới (sổ không hợp lệ với bản mới lộ ngay lúc nâng). Không kiểm
    được (xt.py thiếu/lỗi) → một dòng ⚠, không làm hỏng lần cài (fail-open như `report_upgrade_steps`). Thư mục con của
    repo git (monorepo `apps/web`): sổ ở chính thư mục dự án — `xt.py stage` và `release-check` cùng gốc (`loop_root`)."""
    created, warned = False, None
    try:
        if stage_init and not (target / STAGE_LEDGER).exists():
            r = run_stage(target, "init")
            created = r.returncode == 0
            if not created:
                warned = r.stderr.strip()
                log(
                    f"⚠ --stage-init không tạo được sổ: {warned or f'`xt.py stage init` thoát {r.returncode} không kèm lý do'}"
                )
        r = run_stage(target, "status", "--json")
        led = json.loads(r.stdout)["stage"] if r.returncode == 0 else None
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError) as exc:
        log(f"⚠ không kiểm được sổ giai đoạn ({exc!r}) — chạy `python3 .xtemplates/scripts/xt.py stage status`")
        return
    if r.returncode:
        if warned is None or r.stderr.strip() != warned:  # cùng lý do với lần `init` vừa báo: không lặp (review #339)
            why = r.stderr.strip() or f"`xt.py stage status` thoát {r.returncode} không kèm lý do"
            log(f"⚠ sổ giai đoạn: {why} — sửa trước khi chạy vòng (ADR-0058)")
    elif led is None:
        log(
            "Giai đoạn sản phẩm (ADR-0058): chưa dùng — dự án mới: `python3 .xtemplates/scripts/xt.py stage init`"
            " (hoặc cài lại với --stage-init); đã chạy/production: người chạy `stage init --adopt 2|3 --evidence …`"
            " ở terminal ngoài phiên agent"
        )
    else:
        how = "vừa tạo — commit + push" if created else "giữ nguyên"
        log(
            f"✓ giai đoạn sản phẩm: {led['cycle']} · giai đoạn {led['stage']} · {led['status']} ({STAGE_LEDGER}, {how})"
        )


def plan_settings(target: Path, force_harness: bool, prov: dict[str, list[str]]) -> dict[str, Any]:
    """Kế hoạch cho .claude/settings.json: quyền thêm/bớt, hook thêm/đổi lệnh/matcher/`onFailure`/`timeout` (không ghi
    gì)."""
    src, dst = SRC / ".claude" / "settings.json", target / ".claude" / "settings.json"
    if dst.exists() and not force_harness:
        pair = read_settings_pair(src, dst)
        if isinstance(pair, str):
            return {"action": pair}
        rep = settings_changes(pair[0], pair[1], prov, own_permissions(target))
        action = "merged-hooks" if rep.pop("changes") else "kept"
        return {"action": action, **rep}
    return {"action": classify_copy(src, dst, force_harness, own_settings if own_permissions(target) else None)[0]}


PlanJob = tuple[Path, str, bool, Callable[[str], str] | None, str | None]  # nguồn, đích, force, biến đổi, hash mẫu


def plan_entry(target: Path, job: PlanJob, installed_hash: str | None) -> dict[str, Any]:
    """Một file của kế hoạch: {path, action}; `xt.yaml` của dự án (`kept-own`/`updated-new`) kèm `keys_add` — khoá mới
    của mẫu sẽ được nối dạng chú thích (chỉ báo, không ghi)."""
    src, rel, force, tf, template_hash = job
    action, data = classify_copy(
        src, target / rel, force, tf, installed_hash, template_hash, preserve_yaml_policy=rel == "xt.yaml"
    )
    entry: dict[str, Any] = {"path": rel, "action": action}
    if rel == "xt.yaml" and action in YAML_MERGE:
        own = read_own_yaml(target / rel)
        entry["keys_add"] = [k for k, _ in missing_yaml_keys(data.decode("utf-8"), own)] if own is not None else []
    return entry


def plan_files(
    target: Path, force_harness: bool, no_harness: bool, with_github: bool, preset: str | None = None
) -> list[dict[str, Any]]:
    """Hành động dự kiến cho từng file harness/gốc/GitHub: copied | kept | updated | kept-own | updated-new |
    skipped-symlink. Cùng hash như cài thật: manifest, file gốc chưa có hash thì suy từ mẫu cũ (`infer_root_hashes`)."""
    hashes = {**infer_root_hashes(target), **load_manifest(target)}  # manifest thắng hash suy
    jobs: list[PlanJob] = []
    if not no_harness:
        jobs += [(src, src.relative_to(SRC).as_posix(), force_harness, None, None) for src in harness_sources(target)]
    jobs += [
        (tsrc, name, False, body, root_template_hash(tsrc, preset))
        for name, tsrc, body in root_template_jobs(target, preset)
    ]
    if with_github:
        jobs += [(SRC / gsrc, gh, False, github_template(gsrc), None) for gh, gsrc in GITHUB_FILES.items()]
    return [plan_entry(target, job, hashes.get(job[1])) for job in jobs]


def install_plan(
    target: Path,
    force_harness: bool,
    no_harness: bool,
    with_github: bool = False,
    preset: str | None = None,
    stage_init: bool = False,
    adapters: list[str] | None = None,
    no_git_hooks: bool = False,
    pack: dict[str, Any] | None = None,
) -> int:
    """`--plan`: in JSON kế hoạch (quyền/hook/file/git hook/adapter; gói khi `--pack`) ra stdout, KHÔNG ghi gì vào dự án.
    Thoát 0; 2 nếu đích không hợp lệ."""
    target = target.resolve()
    error = target_error(target, with_github) or pack_root_error(target, pack)
    if error:
        log(error)
        return 2
    selected = select_preset(target, preset)
    files = plan_files(target, force_harness, no_harness, with_github, selected)
    creates_yaml = any(f["path"] == "xt.yaml" and f["action"] == "copied" for f in files)
    plan: dict[str, Any] = {
        "schema": 1,
        "target": str(target),
        "framework": {"action": "replace", "path": ".xtemplates/framework"},
        "skills_shadowed": [] if no_harness else shadowed_skills(target),
        "legacy_migration": (target / LEGACY_DIR).is_dir() or (target / LEGACY_YAML).is_file(),
        "settings": {"action": "skipped"} if no_harness else plan_settings(target, force_harness, load_rules(target)),
        "files": files,
        "git_hooks": git_hooks_plan(target, no_harness, no_git_hooks),
        "adapters": adapters_plan(target, adapters or []),
        "preset": {
            "requested": preset,
            "template": selected or "autonomous",
            "existing_yaml": has_project_yaml(target),
            "applied": creates_yaml and selected is not None,
        },
        "manifest": {
            "path": MANIFEST_V2,
            "present": (target / MANIFEST_V2).is_file(),
            "policy": manifest_policy(target, selected if creates_yaml else None),
        },
        "stage": {  # sổ giai đoạn: chỉ `--stage-init` tạo, sổ có sẵn không bị chạm (D-249)
            "path": STAGE_LEDGER,
            "present": (target / STAGE_LEDGER).exists(),
            # sẽ THỬ `stage init` (sổ ở ref khác → xt.py từ chối lúc cài)
            "init": stage_init and not (target / STAGE_LEDGER).exists(),
        },
    }
    if pack is not None:  # không `--pack` → kế hoạch y như trước (không có khoá `pack`)
        plan["pack"] = pack_plan(target, pack)
    print(json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def install(
    target: Path,
    force_harness: bool,
    no_harness: bool,
    label: str | None,
    with_github: bool = False,
    preset: str | None = None,
    stage_init: bool = False,
    adapters: list[str] | None = None,
    no_git_hooks: bool = False,
    pack: dict[str, Any] | None = None,
) -> int:
    target = target.resolve()
    error = target_error(target, with_github) or pack_root_error(target, pack)
    if error:
        log(error)
        return 2
    selected = select_preset(target, preset)
    if preset is not None and has_project_yaml(target):
        log("  --preset chỉ áp dụng khi tạo xt.yaml mới — giữ chính sách và lựa chọn hiện có của dự án")
    xt_dir = target / ".xtemplates"
    previous = installed_label(xt_dir)  # đọc trước khi install_framework ghi nhãn mới
    xt_dir.mkdir(exist_ok=True)

    migrate_legacy(target)
    inferred = infer_root_hashes(target)  # mẫu cũ trong .xtemplates/framework/ — trước khi install_framework thay
    version = install_framework(xt_dir, label)
    if not no_harness:
        install_harness(target, force_harness)
        if not no_git_hooks:
            install_git_hooks(target)
    install_adapters(target, adapters or [])
    install_root_templates(target, version, inferred, selected)
    if with_github:
        install_github(target)
    if pack is not None:
        install_pack(target, pack, version)
    ensure_gitignore(target)
    warn_ignored_framework(target)
    stale = legacy_refs(target)
    if stale:
        log(
            "  ⚠ còn nhắc tên cũ (.xstored/xs.py/xs.yaml/XS_*) — đổi tay sang .xtemplates/xt.py/xt.yaml/XT_*: "
            + ", ".join(stale)
        )
    report_stage(target, stage_init)
    report_upgrade_steps(previous, version)  # cuối: khối bước làm tay đứng ngay trước "Xong."

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
        help="copy ruleset mẫu, PR template, Dependabot, workflow ci + secret-scan + pr-title + pr-steward (+ stub merge-gate tạm, "
        "D-122) vào .github/ (không đè)",
    )
    p.add_argument(
        "--plan",
        action="store_true",
        help="in JSON kế hoạch (quyền/hook/file/git hook/adapter) ra stdout, không ghi gì",
    )
    p.add_argument(
        "--no-git-hooks",
        action="store_true",
        help="không cài git hook sàn chung pre-commit/commit-msg/pre-push (ADR-0064 lát C)",
    )
    p.add_argument(
        "--preset",
        choices=INSTALL_PRESETS,
        help="chính sách merge/review cho xt.yaml mới: safe hoặc autonomous; cài lại giữ lựa chọn cũ",
    )
    p.add_argument(
        "--stage-init",
        action="store_true",
        help="dự án mới: tạo sổ giai đoạn sản phẩm ở giai đoạn 1 (ADR-0058) khi chưa có; dự án đã chạy dùng `stage init --adopt`",
    )
    p.add_argument(
        "--harness",
        default="",
        help=f"adapter hook cho công cụ khác, cách nhau dấu phẩy: {','.join(ADAPTERS)} (ADR-0064 lát B)",
    )
    p.add_argument(
        "--pack",
        help="gói sản phẩm framework/templates/packs/<id>: starter chỉ vào repo sạch, managed nâng theo hash (ADR-0068)",
    )
    a = p.parse_args(argv)
    hosts = [h for h in a.harness.split(",") if h]
    bad = [h for h in hosts if h not in ADAPTERS]
    if bad:
        log(f"✗ --harness: không biết {', '.join(bad)} — chọn trong {', '.join(ADAPTERS)}")
        return 2
    try:
        pack = load_pack(a.pack) if a.pack else None
    except ValueError as exc:
        log(f"✗ --pack: {exc}")
        return 2
    if a.plan:
        return install_plan(
            Path(a.target),
            a.force_harness,
            a.no_harness,
            a.with_github,
            a.preset,
            a.stage_init,
            hosts,
            a.no_git_hooks,
            pack,
        )
    return install(
        Path(a.target),
        a.force_harness,
        a.no_harness,
        a.label,
        a.with_github,
        a.preset,
        a.stage_init,
        hosts,
        a.no_git_hooks,
        pack,
    )


if __name__ == "__main__":
    sys.exit(main())
