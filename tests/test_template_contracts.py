"""Mẫu tài liệu khớp lệnh Kiểm của mục MUST nó phục vụ (review #412): dự án chép mẫu nguyên văn phải qua được Kiểm máy
của mục đó, không đỏ ngay dòng mẫu."""

from __future__ import annotations

import fnmatch
import re
import shlex
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FW = ROOT / "framework"


def template_block(name: str, lang: str = "markdown") -> str:
    """Khối ````<lang> đầu tiên của mẫu — phần dự án chép sang."""
    text = (FW / "templates" / name).read_text(encoding="utf-8")
    m = re.search(rf"^````{lang}\n(.*?)^````$", text, re.M | re.S)
    assert m, f"{name}: không có khối ````{lang}"
    return m.group(1)


ISO_DURATION_RE = re.compile(r"P(?!$)(\d+Y)?(\d+M)?(\d+W)?(\d+D)?(T(?=\d)(\d+H)?(\d+M)?(\d+S)?)?")


def item_line(item_id: str) -> str:
    for p in FW.rglob("*.md"):
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.startswith(f"- [ ] `{item_id}` "):
                return line
    raise AssertionError(f"không thấy mục {item_id}")


class TemplateContractTest(unittest.TestCase):
    def test_risks_template_ids_match_pm_risk_001_check(self):
        """`PM-RISK-001` Kiểm `rg -n "^\\| RK-[0-9]{3}" docs/RISKS.md …`: mẫu từng dùng `R-001` (trùng không gian ID
        `R-NNN` của PROJECT.md) nên chép nguyên văn là đỏ MUST."""
        self.assertIn('"^\\| RK-[0-9]{3}"', item_line("PM-RISK-001"))
        rows = template_block("RISKS.md").splitlines()
        self.assertTrue([r for r in rows if re.match(r"^\| RK-[0-9]{3}", r)])
        self.assertFalse([r for r in rows if re.match(r"^\| R-[0-9]{3}", r)])

    def test_privacy_data_map_matches_cmp_priv_001_002(self):
        """AUD-DOC-218: `retention` của mẫu theo đúng lint `CMP-PRIV-002` (ISO 8601 duration hoặc `until-account-deleted`)
        và mẫu có trường "nơi sao chép" (`copies`) mà `CMP-PRIV-001` đòi."""
        self.assertIn("ISO 8601 duration hoặc `until-account-deleted`", item_line("CMP-PRIV-002"))
        self.assertIn("nơi sao chép", item_line("CMP-PRIV-001"))
        block = template_block("PRIVACY-DATA-MAP.md", "yaml")
        retention = re.findall(r"^\s*retention:\s*<([^>]*)>", block, re.M)
        self.assertTrue(retention, block)
        for value in retention:
            for choice in (c.strip() for c in value.split("|")):
                self.assertTrue(choice == "until-account-deleted" or ISO_DURATION_RE.fullmatch(choice), choice)
        self.assertRegex(block, r"(?m)^\s*copies:\s*\[")

    def test_slo_file_name_is_one(self):
        """AUD-DOC-217: một tên file SLO ở `OPS-SLO-001` (nhà), mẫu, chỉ mục mẫu và mục ngành — `slo.md` ≠ `SLO.md` trên
        Linux."""
        want = "`docs/ops/SLO.md`"
        for item in ("OPS-SLO-001", "IND-SAAS-013", "IND-GOV-018"):
            self.assertIn(want, item_line(item), item)
        self.assertIn("# Mẫu docs/ops/SLO.md\n", (FW / "templates" / "SLO.md").read_text(encoding="utf-8"))
        index = (FW / "templates" / "README.md").read_text(encoding="utf-8")
        self.assertIn(f"| [`SLO.md`](SLO.md) | {want} ", index)
        self.assertNotIn("docs/ops/slo.md", "\n".join(p.read_text(encoding="utf-8") for p in FW.rglob("*.md")))


def kiem_rg_cmds(item_id: str) -> list:
    """Các lệnh `rg …` (đoạn trong backtick) ở phần `→ Kiểm:` của mục — đúng chuỗi dự án chép vào CI."""
    kiem = item_line(item_id).split("→ Kiểm:", 1)[1].split(" · Nguồn:", 1)[0]
    return [c for c in re.findall(r"`([^`]+)`", kiem) if c.startswith("rg ")]


def rg_emulate(cmd: str, root: Path) -> list:
    """Chạy pipeline `rg … | rg …` bằng `re` của Python (CI không cài ripgrep; regex của các mục dùng cú pháp chung
    Rust/Python): khâu đầu đọc file khớp `-g` dưới đường dẫn, `-U` = khớp nhiều dòng (in mọi dòng của đoạn khớp), khâu
    sau lọc dòng của khâu trước (`-v` đảo). Khâu đầu thiếu đường dẫn → AssertionError (rg sẽ đọc stdin — treo ở CI/hook)."""
    lines: list = []
    for i, stage in enumerate(_stages(cmd)):
        assert stage[0] == "rg", stage
        flags, globs, rest = set(), [], []
        args = iter(stage[1:])
        for a in args:
            if a == "-g":
                globs.append(next(args))
            elif a.startswith("--"):
                flags.add(a)
            elif a.startswith("-") and not rest:
                flags.update(a[1:])
            else:
                rest.append(a)
        pat = re.compile(rest[0], re.I if "i" in flags else 0)
        if i:
            lines = [ln for ln in lines if bool(pat.search(ln)) != ("v" in flags)]
            continue
        assert rest[1:] == ["."], f"khâu đầu thiếu đường dẫn `.`: {stage}"
        for p in sorted(
            x for x in root.rglob("*") if x.is_file() and (not globs or any(fnmatch.fnmatch(x.name, g) for g in globs))
        ):
            text, rel = p.read_text(encoding="utf-8"), "./" + p.relative_to(root).as_posix()
            src = text.split("\n")
            if "U" in flags:
                for m in pat.finditer(text):
                    a, b = text.count("\n", 0, m.start()), text.count("\n", 0, max(m.end() - 1, m.start()))
                    lines += [f"{rel}:{k + 1}:{src[k]}" for k in range(a, b + 1)]
            else:
                lines += [f"{rel}:{k + 1}:{ln}" for k, ln in enumerate(src) if pat.search(ln)]
    return lines


def _stages(cmd: str) -> list:
    out: list = [[]]
    for tok in shlex.split(cmd):
        if tok == "|":
            out.append([])
        else:
            out[-1].append(tok)
    return out


class KiemRegexTest(unittest.TestCase):
    """Lệnh Kiểm dạng `rg` của mục MUST chạy trên fixture xấu (phải ra dòng) / tốt (không ra) — AUD-DOC-157/158/160."""

    def setUp(self) -> None:
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory()))

    def flagged(self, item_id: str) -> set:
        return {ln.split(":", 2)[2] for c in kiem_rg_cmds(item_id) for ln in rg_emulate(c, self.root)}

    def test_base_sec_010_catches_every_non_loopback_publish(self):
        (self.root / "docker-compose.yml").write_text(
            "services:\n  web:\n    ports:\n"
            '      - "127.0.0.1:8080:80"  # OK\n'
            '      - "[::1]:9000:9000"  # OK\n'
            '      - "192.168.1.5:8081:80"  # BAD ip\n'
            '      - "3000"  # BAD chỉ cổng container\n'
            "      - 8082:80  # BAD\n"
            '      - "0.0.0.0:5432:5432"  # BAD\n'
            '      - "[::]:6379:6379"  # BAD\n'
            "      - target: 80\n"
            "        published: 8083  # BAD long syntax\n"
            "    environment:\n      - KEY=1\n    depends_on:\n      - db\n",
            encoding="utf-8",
        )
        (self.root / "README.md").write_text(
            "docker run -p 127.0.0.1:8080:80 img OK\n"
            "docker run --publish published=8080,target=80,host_ip=127.0.0.1 img OK\n"
            "docker run --rm -v /a:/b --platform linux/amd64 img OK\n"
            "mkdir -p 1dir OK\n"
            "docker run -P img BAD\n"
            "docker run --publish-all img BAD\n"
            "docker container run -p 192.168.1.5:80:80 img BAD\n"
            "podman run -p 8084:80 img BAD\n"
            "docker run --publish published=8085,target=80 img BAD\n"
            "docker run -p8086:80 img BAD\n"
            "docker run \\\n  --rm \\\n  -p 9001:9001 --label BAD \\\n  img\n",
            encoding="utf-8",
        )
        got = self.flagged("BASE-SEC-010")
        self.assertTrue(got)
        self.assertEqual({ln for ln in got if "BAD" not in ln}, set())
        want = {ln for p in self.root.iterdir() for ln in p.read_text(encoding="utf-8").split("\n") if "BAD" in ln}
        self.assertEqual(got, want)

    def test_sec_supply_032_catches_dict_and_underscore_flag(self):
        (self.root / "load.py").write_text(
            "m = AutoModel.from_pretrained(x, trust_remote_code=True)\n"
            'kw = {"trust_remote_code": true}\n'
            "kw2 = {'trust_remote_code': 1}\n"
            "os.system('vllm serve m --trust-remote-code')\n"
            "os.system('run --trust_remote_code')\n"
            "trust_remote_code = False\n",
            encoding="utf-8",
        )
        cmds = kiem_rg_cmds("SEC-SUPPLY-032")
        self.assertEqual(len(cmds), 1)
        got = [ln.split(":", 2)[1] for ln in rg_emulate(cmds[0], self.root)]
        self.assertEqual(got, ["1", "2", "3", "4", "5"])


if __name__ == "__main__":
    unittest.main()
