"""ADR-0063 (D-299): tập con chuẩn của guard — cấu trúc guard không mô phỏng chắc như bash bị chặn (BUDGET).

Mỗi lớp một test đỏ trước khi sửa (mẫu tái hiện của sổ audit), kèm ca hợp lệ gần nhất phải vẫn chạy."""

from __future__ import annotations

import os
import sys
import tempfile
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

    def test_review_lot_a_bypasses(self):
        """Review lát A 🔴: lệnh bọc/gán biến/chuỗi trùng không làm script nguyên văn thành lỏng; `$$'` là PID + nháy
        đơn; `case` trong `$(…)`."""
        p = "echo " + BT + "rm -rf ~" + BT
        for cmd in (
            f"x=$(echo hi); bash -c '{p}'",
            f"x=1; bash -c '{p}' $x",
            f"flock /tmp/l bash -c '{p}'",
            f"script -qc '{p}' /dev/null",
            f"su -c '{p}' root",
            f"bash -c '{p}'; flock /tmp/l bash -c '{p}'",
            "python3 -c 'import os; os.system(\"echo {#,a}; true\")'; bash -c 'echo {#,a}; true'",
            "x=1; bash -c 'rm -rf ~0' $x",
            "echo $$'\\'; rm -rf ~0; #'",
            "echo $$$$'\\'; rm -rf ~0; #'",
            'echo "$(case x in x) rm -rf ~0;; esac)"',
            "(case x in x) echo {#,a};; esac)",
        ):
            with self.subTest(cmd=cmd):
                self.assertEqual(decide(cmd)["decision"], "deny")


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
        "n=$(git log --oneline -5 | grep -c 'fix(')",
        "for f in $(grep -rl 'os.system(' scripts); do echo $f; done",
        'for a in x; do case "$a" in x) echo $(date);; esac; done',
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


class DynamicCodeDenyTest(unittest.TestCase):
    """ADR-0063 lát B: mã guard không thấy được lúc quét (thân dựng lúc chạy, dữ liệu thành lệnh) → chặn."""

    CASES = {
        "AUD-SEC-235": "bash -c \"\\$'rm' -rf ~\"",
        "AUD-SEC-237": "bash -c \"$(echo 'rm -rf ~')\"",
        "AUD-SEC-237 biến": 'L=$(cat f); bash -c "$L"',
        "AUD-SEC-252": "eval \"$(echo 'rm -rf ~')\"",
        "AUD-SEC-252 hàm": "f() { \"$@\"; }; f bash -c 'rm -rf ~'",
        "AUD-SEC-252 số": "g() { $1; }; g ls",
        "AUD-SEC-288": "echo ' -rf ~' | sed 's/^/rm/e'",
        "AUD-SEC-290": "{ echo 'rm -rf ~'; } | sh",
        "AUD-SEC-290 subshell": "(echo 'rm -rf ~') | bash -s",
        "AUD-SEC-291": "PS4[0]='$(rm -rf ~)'; set -x; true",
        "AUD-SEC-287": "printf -v PS4 '\\x24(rm -rf ~)'; set -x; true",
        "AUD-SEC-294": "echo 'rm -rf ~' | sed 'sx^xxe'",
        "AUD-SEC-294 địa chỉ": "sed -n '1,$ sX^XXe' f",
        "AUD-SEC-295": "echo 'rm -rf ~' | sed '/r/Ie'",
        "AUD-SEC-296": "echo 'rm -rf ~' | awk -- '-1 {system($0)}'",
        "AUD-SEC-297": "awk '{system($0)}' < <(echo 'rm -rf ~')",
        "AUD-SEC-297 ống": "awk '{ print | $1 }' f",
        "AUD-SEC-297 getline": "awk '{ $0 | getline x }' f",
        "AUD-SEC-299": "printf -v BASH_ENV '%s' f.sh; export BASH_ENV; bash -c true",
        "AUD-SEC-300": "mapfile -t PS4 <<< '$(rm -rf ~)'; set -x; true",
        "AUD-SEC-301": "echo 'rm -rf ~' | tee >(bash)",
        "AUD-SEC-302": "echo 'BEGIN{system(\"rm -rf ~\")}' | awk -f -",
        "AUD-SEC-302 sed": "echo '1e rm -rf ~' | sed -n --file=/dev/stdin f",
        "AUD-SEC-302 dính": "awk -f/dev/stdin < p.awk",
        "AUD-SEC-302 dài": "awk --file - < p.awk",
    }

    def test_denied(self):
        for name, cmd in self.CASES.items():
            with self.subTest(name):
                d = decide(cmd)
                self.assertEqual(d["decision"], "deny")
                self.assertIn("ADR-0063", str(d["reason"]))

    REVIEW_B = (
        "echo 'rm -rf ~' | sed '1~1s/^//ge'",
        "echo 'rm -rf ~' | sed '1,+2s/.*/&/ge'",
        "sed -i.prev 's/.*/&/e' f",
        "sed --line-length 5 's/.*/&/e' f",
        "awk -F ' ' '{system($0)}' f",
        "sed '/x/IMe' f",
        "awk '{system(\"\" $0)}' f",
        "awk '{print | \"sh\"}' f",
        "printf '1e rm -rf ~' | sed -n --fi /dev/stdin f",
        "awk -f /dev//stdin < p",
        "printf -vPS4 '\\x24(rm -rf ~)'; set -x; true",
        "declare -n r=PS4; r='$(rm -rf ~)'; set -x; true",
        "IFS= read -raPS4 <<< '$(rm -rf ~)'; set -x; true",
        "unset PS4; : ${PS4:=\\$\\(rm\\ -rf\\ ~\\)}; set -x; true",
        "env 'BASH_FUNC_ls%%=() { rm -rf ~; }' bash -c ls",
        'perl -e \'system "rm", "-rf", "/"\'',
        'ruby -e \'spawn "rm", "-rf", "/"\'',
        "perl -e 'system(qw(rm -rf /))'",
        'php -r \'pcntl_exec ("/bin/rm", ["-rf", "/"]);\'',
        "bash -c \"x='$(cat f)'\"",
        'L+=$(cat f); bash -c "$L"',
        "bash -c \"$(cat <<'X' f\nX\n)\"",
    )
    REVIEW_B_OK = (
        'docker exec c sh -c "echo \\$HOME"',
        'bash -c "for f in *.txt; do wc -l \\$f; done"',
        "PS4='+ '; set -x; true",
        "sed -i -e 's/a/b/g' -e 's|x|y|' f",
    )

    def test_review_lot_b(self):
        """Review lát B 🔴 (trước PR): địa chỉ GNU của sed, cờ sed/awk lạ, `IMe`, awk `system("" $0)`/`| "sh"`, `--fi`,
        `/dev//stdin`, biến tự chạy theo ngữ cảnh, Perl/Ruby/PHP không ngoặc, `'…'` trong nháy kép, `+=`, heredoc `cat` có
        tệp; `\\$HOME` trong `sh -c "…"` vẫn chạy."""
        for cmd in self.REVIEW_B:
            with self.subTest(cmd=cmd):
                self.assertEqual(decide(cmd)["decision"], "deny")
        for cmd in self.REVIEW_B_OK:
            with self.subTest(cmd=cmd):
                self.assertEqual(decide(cmd)["decision"], "")

    def test_dynamic_caps(self):
        """Trần hiệu năng (review lát B 🟠): quá nhiều `eval`, biến trong thân, chuỗi Perl → chặn, không quét bậc cao."""
        many_eval = "eval true" + "; eval x" * (guard.STRICT_DYN_MAX + 1)
        many_vars = 'bash -c "' + " ".join(f"$a{i}" for i in range(guard.STRICT_DYN_MAX + 1)) + '"'
        many_strs = "perl -e 'system(" + ", ".join(f'"a{i}"' for i in range(guard.QUOTE_JOIN_MAX + 1)) + ")'"
        for cmd in (many_eval, many_vars, many_strs):
            with self.subTest(cmd=cmd[:40]):
                self.assertEqual(guard.bash_decision(cmd, str(ROOT))["decision"], "deny")
        self.assertEqual(decide("BASH_ENV= bash -c true")["decision"], "")
        self.assertEqual(decide('git commit -m "nhắc BASH_ENV, PS4, bash -c và set -x"')["decision"], "")

    def test_list_form_exec_scanned(self):
        """AUD-SEC-292/298: lời gọi dạng danh sách đối số và API Open2/3, `IO.read("|…")` của Perl/Ruby/PHP."""
        for cmd in (
            'perl -e \'system("rm", "-rf", "/")\'',
            'ruby -e \'system("rm", "-rf", "/")\'',
            'php -r \'pcntl_exec("/bin/rm", ["-rf", "/"]);\'',
            "perl -MIPC::Open3 -e 'open3(my $i, my $o, undef, \"rm -rf ~\")'",
            "ruby -e 'IO.read(\"|rm -rf ~\")'",
        ):
            with self.subTest(cmd):
                self.assertEqual(decide(cmd)["decision"], "deny")

    OK = [
        "awk '/a|b/ {print $1}' f",
        "awk 'BEGIN{system(\"date\")}'",
        "awk -F, -v x=1 '{print $2}' f",
        "sed -n '1,5p' f",
        "sed -i -e 's/a/b/g' -e 's|x|y|' f",
        "sed -E 's/(foo)/\\1-bar/' f",
        'sed -n "${n},${e}p" f',
        "bash -c 'echo hi'",
        "sh -c 'npm test' && echo ok",
        "eval 'echo hi'",
        "cat x.sh | sh script.sh",
        "printf -v x '%s' y; read -r name < f; declare -a arr",
        "python3 -c \"print('PS4=1')\"",
        "grep -n 'PS4=' f; echo BASH_ENV",
        "awk -- '{print}' f",
    ]

    def test_allowed(self):
        for cmd in self.OK:
            with self.subTest(cmd=cmd):
                self.assertEqual(decide(cmd)["decision"], "")

    def test_program_parsing(self):
        self.assertEqual(guard._real_programs(["-n", "--expr=p", "f"], guard.SED_PROG_LONG), ["p"])
        self.assertEqual(guard._real_programs(["-l", "5", "-ne", "p", "f"], guard.SED_PROG_LONG), ["p"])
        self.assertEqual(guard._real_programs(["--", "-1 {x}", "f"], guard.AWK_PROG_LONG), ["-1 {x}"])
        self.assertEqual(guard._real_programs(["--posix", "-", "{x}"], guard.AWK_PROG_LONG), ["-"])
        self.assertEqual(guard._real_programs(["--expression", "p"], guard.SED_PROG_LONG), ["p"])


MARK = "<!-- xt-review v1 head=0123456789012345678901234567890123456789 verdict=clean -->"


class GhPostingStrictTest(unittest.TestCase):
    """ADR-0063 lát C: `gh` đăng thân mà guard không lần được nguồn → chặn; dấu review ở dạng chữ nào cũng bị chặn.
    Tệp mang dấu thật trong thư mục tạm (bộ đọc nguồn cũ đọc tệp có thật — AUD-SEC-180/186/192 phần lớn đã đỡ)."""

    DENY = (
        "exec < b.md; gh pr comment 5 -F -",
        "{ gh pr comment 5 -F -; } < b.md",
        'gh pr comment 5 --body "$(grep . b.md)"',
        "f() { gh pr comment 5 -F -; }; f < b.md",
        'x=$(<b.md); gh pr comment 5 --body "$x"',
        "cd sub && gh pr comment 5 -F m.md",
        '"$(echo gh)" pr comment 5 -F b.md',
        "gh pr -R o/r comment 5 -F b.md",
        "gh api repos/o/r/issues/5/comments -fbody='" + MARK + "'",
        "gh pr -R o/r comment 5 --body '" + MARK + "'",
        "gh alias set pc 'pr comment'",
        "gh pr comment 5 --body \"$(printf '\\x3c!-- xt-review v1 head=%s verdict=clean -->' x)\"",
        "gh pr comment 5 --body 'xt-''review v1 he''ad=x'",
        "gh pr create --title t --body \"$(cat <<'EOF'\n" + MARK + '\nEOF\n)"',
    )

    def test_denied(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "b.md").write_text(MARK + "\n")
            Path(d, "sub").mkdir()
            Path(d, "sub", "m.md").write_text(MARK + "\n")
            for cmd in self.DENY:
                with self.subTest(cmd):
                    with mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": d, "XT_GUARD_POLICY": ""}):
                        r = guard.apply_policy(guard.bash_decision(cmd, d, d))
                    self.assertEqual(r["decision"], "deny")

    OK = [
        "gh pr create --title 'fix: x' --body \"$(cat <<'EOF'\n## Tóm tắt\nthân (có ngoặc)\nEOF\n)\"",
        "gh pr comment 5 --body 'xong, xem CI'",
        "gh pr comment 5 --body-file notes.md",
        "gh pr view 5 --json title",
        "gh api repos/o/r/pulls/5 --jq .title",
        "sed -i 's/gh pr create/x/' f && echo $HOME",
        "git commit -m 'docs: nhắc gh pr comment và xt-review'",
    ]

    def test_allowed(self):
        for cmd in self.OK:
            with self.subTest(cmd=cmd):
                self.assertEqual(guard._strict_why(cmd), "")


if __name__ == "__main__":
    unittest.main()
