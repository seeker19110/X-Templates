"""Contract của gói sản phẩm so với nhánh gốc của PR (AUD-SEC-502, D-377) — CI `pack-web-api.yml` dùng, test ở `test_packs.py`.

  python3 tests/pack_baseline.py check <pack> <base-ref>

`starter/contract/baseline.json` là mốc mà bộ nghiệm thu (`contract.test.ts`) so `openapi.json` với nó; sửa được trong
cùng PR thì đổi không tương thích kèm chép đè baseline lọt. Luật: baseline ở cây làm việc phải CÙNG nội dung JSON với
bản ở `<base-ref>` (nên test contract thực chất so với baseline của nhánh gốc), trừ khi phiên bản gói TĂNG so với
`<base-ref>`. Phiên bản gói = `VERSION` của khung ở gốc repo (ADR-0068 quyết định 1, semver `X.Y.Z`). Gói chưa có
baseline ở gốc (gói mới) → qua.
Thoát 0 = đạt; 1 = baseline đổi không tăng phiên bản / file hỏng; 2 = tham số sai hay `<base-ref>` không đọc được.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

BASELINE = "starter/contract/baseline.json"
SEMVER = re.compile(r"(\d+)\.(\d+)\.(\d+)")


class RefError(Exception):
    """`<base-ref>` không có trong repo."""


def _git(pack: Path, *args: str) -> str | None:
    r = subprocess.run(["git", "-C", str(pack), *args], capture_output=True, text=True, check=False)
    return r.stdout if r.returncode == 0 else None


def at_base(pack: Path, ref: str, path: str) -> str | None:
    """Nội dung `path` (`./x` = tương đối thư mục gói, `x` = từ gốc repo) ở `ref`; không có file → None; `ref` không
    có → RefError."""
    if _git(pack, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}") is None:
        raise RefError(ref)
    return _git(pack, "show", f"{ref}:{path}")


def version(text: str | None) -> tuple[int, ...] | None:
    """Phiên bản semver từ nội dung `VERSION`; sai dạng/thiếu → None."""
    m = SEMVER.fullmatch(text.strip()) if text is not None else None
    return tuple(int(x) for x in m.groups()) if m else None


def check(pack: Path, ref: str) -> str:
    """Lý do baseline đổi không hợp lệ ("" = đạt)."""
    base = at_base(pack, ref, f"./{BASELINE}")
    try:
        head = json.loads((pack / BASELINE).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return f"{BASELINE} không đọc được ({exc})"
    if base is None or json.loads(base) == head:
        return ""
    top = Path((_git(pack, "rev-parse", "--show-toplevel") or ".").strip()) / "VERSION"
    new = version(top.read_text(encoding="utf-8") if top.is_file() else None)
    old = version(at_base(pack, ref, "VERSION"))
    if new is None or old is None or new <= old:
        return (
            f"{BASELINE} đổi so với {ref} mà phiên bản gói (`VERSION`, ADR-0068) không tăng ({old} → {new}) — đổi"
            " contract phải đi cùng PR tăng phiên bản (AUD-SEC-502)"
        )
    return ""


def main(argv: list[str]) -> int:
    if len(argv) != 3 or argv[0] != "check":
        print(__doc__, file=sys.stderr)
        return 2
    pack, ref = Path(argv[1]), argv[2]
    try:
        problem = check(pack, ref)
    except RefError:
        print(f"✗ không đọc được {ref} — cần lịch sử nhánh gốc (checkout fetch-depth: 0)", file=sys.stderr)
        return 2
    print(f"✗ {problem}" if problem else f"✓ baseline khớp {ref} hoặc phiên bản gói đã tăng")
    return 1 if problem else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
