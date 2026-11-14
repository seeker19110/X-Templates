"""Áp và kiểm ca sai cố ý của gói sản phẩm (ADR-0068 §Xác nhận B) — CI `pack-web-api.yml` dùng, test ở `test_packs.py`.

  python3 tests/pack_mutants.py list <pack>                    in id các ca (mỗi dòng một id)
  python3 tests/pack_mutants.py apply <pack> <id> <project>    sửa đúng một chỗ (chuỗi `find` phải xuất hiện đúng 1 lần)
  python3 tests/pack_mutants.py check <pack> <id> <junit.xml>  exit 0 khi ca bị bắt: ≥ 1 test đỏ và có test đỏ mang tên
                                                               chứa `expect_fail` (đỏ vì lý do khác không tính là bắt)
  python3 tests/pack_mutants.py promotion <release.json>       `release-check --json` của repo sạch: artifacts PASS,
                                                               có digest, promotion chưa `approved` khi chưa ký
Thoát 1 = ca sống sót / không áp được; 2 = tham số sai.
"""

from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


def load(pack: Path) -> dict[str, dict[str, Any]]:
    data = json.loads((pack / "mutants.json").read_text(encoding="utf-8"))
    return {m["id"]: m for m in data["mutants"]}


def apply(pack: Path, mid: str, project: Path) -> str:
    """Sửa file của ca `mid` trong `project`; trả "" khi xong, hoặc lý do không áp được."""
    m = load(pack)[mid]
    target = project / m["file"]
    text = target.read_text(encoding="utf-8")
    count = text.count(m["find"])
    if count != 1:
        return f"{m['file']}: chuỗi find xuất hiện {count} lần (cần 1) — mã gói đổi, cập nhật mutants.json"
    target.write_text(text.replace(m["find"], m["replace"]), encoding="utf-8")
    return ""


def failed_tests(junit: Path) -> list[str] | None:
    """Tên test có failure, hoặc None khi reporter ghi lỗi ngoài test."""
    root = ET.parse(junit).getroot()
    if next(root.iter("error"), None) is not None:
        return None
    return [case.get("name", "") for case in root.iter("testcase") if case.find("failure") is not None]


def check(pack: Path, mid: str, junit: Path) -> str:
    want = load(pack)[mid]["expect_fail"]
    failed = failed_tests(junit)
    if failed is None:
        return f"ca {mid}: JUnit có lỗi ngoài test, chưa chứng minh mutant bị bắt"
    if not failed:
        return f"ca {mid} SỐNG SÓT: không test nào đỏ"
    if not any(want in name for name in failed):
        return f"ca {mid}: đỏ nhưng không ở test mong đợi ({want!r}); đỏ: {failed[:5]}"
    return ""


def promotion(report: Path) -> str:
    """Repo sạch vừa build: hàng `artifacts` PASS (digest khớp sidecar) và promotion KHÔNG `approved` (chưa ai ký)."""
    data = json.loads(report.read_text(encoding="utf-8"))
    rows = {r["id"]: r["result"] for r in data.get("rows", [])}
    if rows.get("artifacts") != "PASS":
        return f"hàng artifacts = {rows.get('artifacts')!r} (cần PASS)"
    if not data.get("subject", {}).get("digest"):
        return "subject.digest trống"
    state = data.get("promotion", {}).get("state")
    return "" if state in ("pending_human", "blocked") else f"promotion = {state!r} khi chưa có chữ ký"


def main(argv: list[str]) -> int:
    if len(argv) == 2 and argv[0] == "list":
        print("\n".join(load(Path(argv[1]))))
        return 0
    if len(argv) == 2 and argv[0] == "promotion":
        problem = promotion(Path(argv[1]))
        print(f"✗ {problem}" if problem else "✓ promotion")
        return 1 if problem else 0
    if len(argv) != 4 or argv[0] not in ("apply", "check"):
        print(__doc__, file=sys.stderr)
        return 2
    cmd, pack, mid, path = argv[0], Path(argv[1]), argv[2], Path(argv[3])
    if mid not in load(pack):
        print(f"✗ không có ca {mid}", file=sys.stderr)
        return 2
    problem = apply(pack, mid, path) if cmd == "apply" else check(pack, mid, path)
    print(f"✗ {problem}" if problem else f"✓ {cmd} {mid}")
    return 1 if problem else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
