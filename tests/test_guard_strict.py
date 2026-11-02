"""ADR-0063 (D-299): tập con chuẩn của guard — cấu trúc guard không mô phỏng chắc như bash bị chặn (BUDGET).

Mỗi lớp một test đỏ trước khi sửa (mẫu tái hiện của sổ audit), kèm ca hợp lệ gần nhất phải vẫn chạy."""

from __future__ import annotations

import os
import sys
import unittest
import unittest.mock as mock
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.environ.setdefault("XT_GUARD_PHASE", "harden")
sys.path.insert(0, str(ROOT / ".claude" / "hooks"))
import guard

BT = "`"


def decide(cmd: str) -> dict:
    with mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(ROOT), "XT_GUARD_POLICY": ""}):
        return guard.apply_policy(guard.bash_decision(cmd, str(ROOT)))


class StrictSubsetDenyTest(unittest.TestCase):
    """Mẫu tái hiện các 🔴/🟠 lớp từ vựng: guard cũ cho chạy, bash chạy tải."""

    CASES = {
        "AUD-SEC-196": "cat <<X\nit's $(rm -rf ~)\nX",
        "AUD-SEC-202": 'echo "$(echo ")"; rm -rf ~)"',
        "AUD-SEC-202 nháy đơn": "echo \"$(echo ')'; rm -rf ~)\"",
        "AUD-SEC-214": "echo hi\nrm -rf ~\n'",
        "AUD-SEC-214 nháy kép": 'echo "hi',
        "AUD-SEC-214 ansi": "echo $'hi",
        "AUD-SEC-231": "echo " + BT + "echo '" + BT + "\nrm -rf ~\n# '",
        "AUD-SEC-232": "echo $IFS#; rm -rf ~",
        "AUD-SEC-233": "echo {#,a}; rm -rf {~,x}",
        "AUD-SEC-233 cuối": "echo {a,#}; true",
        "AUD-SEC-234": "echo $'\\'' ' #' ; rm -rf {~,x}",
        "AUD-SEC-238": "rm${IFS-}-rf${IFS-}~",
        "AUD-SEC-240": "rm -rf ~0",
        "AUD-SEC-240 trừ số": "ls ~-1/x",
        "AUD-SEC-242": "a=(1)# rm -rf ~",
        "AUD-SEC-243": "echo \"$$( '$(rm -rf ~)' )\"",
        "AUD-SEC-245": 'echo "' + BT + 'rm -rf \\"$HOME\\"' + BT + '"',
        "AUD-SEC-246": 'bash -c "${x:-"rm -rf ~/"}"',
        "AUD-SEC-249": "x='y[$(rm -rf ~)]'; echo $((x))",
    }

    def test_denied_as_budget(self):
        for name, cmd in self.CASES.items():
            with self.subTest(name):
                d = guard.bash_decision(cmd, str(ROOT))
                self.assertEqual(d["decision"], "deny")
                self.assertEqual(d.get("code"), guard.BUDGET)
                self.assertIn("ADR-0063", str(d["reason"]))
                self.assertIn(name.split()[0][-3:], str(d["reason"]))

    def test_nested_shell_script_strict(self):
        """Script `bash -c '…'` là chữ bash đọc: tập con áp cả ở lệnh lồng."""
        for cmd in ("bash -c 'echo $IFS#; rm -rf ~'", "bash -c 'echo {#,a}; true'", "sh -c 'ls ~1'"):
            with self.subTest(cmd=cmd):
                self.assertIn("ADR-0063", str(decide(cmd)["reason"]))


class StrictSubsetAllowTest(unittest.TestCase):
    """Lệnh hợp lệ gần các lớp trên vẫn chạy (đo 2026-11-01 trên 1567 lệnh thật: chỉ backtick lỗi bị chặn thêm)."""

    OK = [
        "timeout 9 python3 -m unittest -q $(ls tests | grep -E '^test_(guard|hook).*[.]py$' | sed 's/[.]py$//')",
        'echo "$(date +%s)" "${x:-def}" "${x:-$y}" "${#a[@]}" a#b',
        "IFS=$'\\t' read -r a b <<< \"$(printf 'x\\ty')\"",
        "echo ~/x ~ {a,b} \"~0\" '~+' \\~0",
        "cat <<'EOF'\nit's " + BT + "x" + BT + " $(y) {#,a}\nEOF",
        "cat <<EOF\nhello $(date) ${HOME}\nEOF",
        "# chú thích thường\nls\n# cuối",
        'x=$(echo "(a)"); echo "$x" $((1+2)) $\'a\\tb\'',
        "git commit -q -m 'fix: dùng `x`' -m \"thân (có ngoặc) không backtick\"",
        "sed -i '70s/S-001; exec: deep)/S-001; topo: parallel; exec: deep)/' docs/x.md",
        "L=docs/x.md; python3 - <<'EOF'\nprint('$(a)', \"it's\")\nEOF",
        "echo )",
    ]

    def test_allowed(self):
        for cmd in self.OK:
            with self.subTest(cmd=cmd):
                self.assertEqual(guard._strict_why(cmd), "")
                self.assertEqual(decide(cmd)["decision"], "")

    def test_loose_text_skips_subset(self):
        """Chữ trích chiều chặt (sed `e`, lời gọi thực thi) không qua tập con; luật nguy hiểm vẫn áp."""
        budget = guard.ScanBudget()
        budget.loose.add("echo " + BT + "x" + BT)
        self.assertEqual(guard.bash_decision("echo " + BT + "x" + BT, str(ROOT), None, 1, budget)["decision"], "")
        budget.loose.add("rm -rf ~")
        self.assertEqual(guard.bash_decision("rm -rf ~", str(ROOT), None, 1, budget)["decision"], "deny")
        budget.loose.add("x=$(true)# rm -rf ~")  # luật `)#` cũ (AUD-SEC-195) vẫn đỡ chữ lỏng
        self.assertEqual(guard.bash_decision("x=$(true)# rm -rf ~", str(ROOT), None, 1, budget)["code"], guard.BUDGET)

    def test_nested_sources_without_budget(self):
        """`_nested_sources` gọi không ngân sách (đường cũ) vẫn trả nguồn, không ghi tập lỏng."""
        cmd = "bash -c 'echo hi'"
        rewritten, nested, _ = guard._nested_sources(cmd, guard.tokenize(cmd), str(ROOT), str(ROOT))
        self.assertIn("echo hi", [s for s, _ in nested])


if __name__ == "__main__":
    unittest.main()
