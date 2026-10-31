"""Fuzz bất biến cho guard (T-1811, research 2026-10-21 CL-2): chỉ stdlib, tất định (seed cố định).

Biến thể sinh từ ca nhóm `guard` của corpus `autonomy-bench` (tests/fixtures/autonomy/guard.json) và chạy qua ĐÚNG đường
của bench — `xt.BenchEnv` + `xt._bench_guard` (bộ luật, `_failure_decision` khi guard ném lỗi, `apply_policy`/`strict`).
Ba bất biến:
1. **deny đơn điệu** — ca `allowed: false` bọc trong lệnh giữ nguyên ngữ nghĩa vẫn bị chặn;
2. **không ngoại lệ** — `_rule_decision` không ném (ngoại lệ = fail-open với lệnh không phải merge, AUD-SEC-077/091);
3. **allow giữ** — ca `allowed: true` bọc vô hại vẫn được cho chạy (không chặn oan).

Lưới bậc 1 (mỗi ca × mỗi bộ bọc áp được) luôn chạy; thêm `XT_FUZZ_ROUNDS` biến thể ghép 2–3 bộ bọc chọn bằng
`random.Random(SEED)` (mặc định nhỏ, vài giây). Biến thể đỏ đã biết nằm ở `KNOWN_RED` (kèm lý do + ID sổ audit) và trong
tests/fixtures/autonomy/pending/guard.json (schema ca của bench) — test đòi hai nơi khớp nhau và mỗi ca còn tái hiện đỏ;
biến thể đỏ mới làm test đỏ.
"""

from __future__ import annotations

import ast
import io
import json
import keyword
import os
import random
import re
import shlex
import sys
import tempfile
import tokenize
import unicodedata
import unittest
import unittest.mock
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import xt

# Luật guard được test ở pha harden; pha build nới hành động cục bộ (ADR-0040) — test riêng ở BuildPhaseGuardTest.
os.environ.setdefault("XT_GUARD_PHASE", "harden")

CORPUS = ROOT / "tests" / "fixtures" / "autonomy"
PENDING = CORPUS / "pending" / "guard.json"
SEED = 1811
ROUNDS = int(os.environ.get("XT_FUZZ_ROUNDS") or "150")

# Từ đầu lệnh làm bộ bọc kiểu exec (`nice`/`timeout`/`command`/gán env) đổi nghĩa: builtin đổi trạng thái shell, từ khoá,
# gán biến, chuyển hướng đứng đầu. Bọc chúng không còn chạy cùng lệnh → không đòi bất biến.
SHELL_WORDS = {
    *"cd pushd popd exec source . read export eval set unset trap alias declare local readonly shopt".split(),
    *"for while until if case function time ! { ( [[ coproc select".split(),
}
REDIRECT_HEAD = re.compile(r"^\d*[<>]")

Wrap = Callable[[str], Optional[str]]


def _head_word(cmd: str) -> str:
    try:
        words = shlex.split(cmd, comments=False)
    except ValueError:
        return ""
    return words[0] if words else ""


def _exec_wrap(prefix: str) -> Wrap:
    """Bọc kiểu exec: chỉ áp khi từ đầu là chương trình thường (không builtin/từ khoá/gán/chuyển hướng)."""

    def wrap(cmd: str) -> Optional[str]:
        head = _head_word(cmd)
        if not head or head in SHELL_WORDS or "=" in head or REDIRECT_HEAD.match(head) or head.startswith("("):
            return None
        return f"{prefix} {cmd}"

    return wrap


def _python_c_script(cmd: str) -> Optional[str]:
    try:
        words = shlex.split(cmd)
    except ValueError:
        return None
    ok = len(words) == 3 and words[0] in ("python3", "python") and words[1] == "-c"
    return words[2] if ok else None


def _nfkc_names(script: str) -> Optional[str]:
    """Tên (không phải từ khoá) trong script Python: chữ ASCII đầu → chữ toàn độ rộng. Python chuẩn hoá NFKC định danh
    (PEP 3131) nên AST không đổi — kiểm bằng `ast.dump`; không đổi được tên nào → None."""
    try:
        toks = list(tokenize.generate_tokens(io.StringIO(script).readline))
        before = ast.dump(ast.parse(script))
    except (SyntaxError, tokenize.TokenError):
        return None
    lines = script.splitlines(keepends=True)
    changed = False
    for t in reversed(toks):
        if (
            t.type == tokenize.NAME
            and not keyword.iskeyword(t.string)
            and t.string[0].isascii()
            and t.string[0].isalpha()
        ):
            row, col = t.start
            line = lines[row - 1]
            lines[row - 1] = line[:col] + chr(ord(t.string[0]) + 0xFEE0) + line[col + 1 :]
            changed = True
    out = "".join(lines)
    if not changed or unicodedata.normalize("NFKC", out) == out or ast.dump(ast.parse(out)) != before:
        return None
    return out


def _nfkc_wrap(cmd: str) -> Optional[str]:
    """NFKC: chỉ nơi trình thông dịch tự chuẩn hoá (định danh `python3 -c`); shell không chuẩn hoá NFKC."""
    script = _python_c_script(cmd)
    variant = _nfkc_names(script) if script is not None else None
    return None if variant is None else shlex.join(["python3", "-c", variant])


WRAPS: Dict[str, Wrap] = {
    "env": _exec_wrap("XT_FUZZ=1"),
    "command": _exec_wrap("command"),
    "nice": _exec_wrap("nice -n 5"),
    "timeout": _exec_wrap("timeout 60"),
    "bash-c": lambda c: f"bash -c {shlex.quote(c)}",
    "subst": lambda c: f'echo "$({c}\n)"',
    "seq": lambda c: f"true; {c}",
    "and": lambda c: f"true && {c}",
    "nfkc": _nfkc_wrap,
    "cd-tmp": lambda c: f"cd /tmp && {c}",
}
# Bọc vô hại với ca allow: không đổi thư mục, không thêm tầng phân tích lồng nhau.
HARMLESS = ("env", "command", "nice", "timeout", "seq", "and")

# Biến thể đỏ đã biết: id biến thể → lý do (ID sổ audit). Phải khớp tests/fixtures/autonomy/pending/guard.json.
KNOWN_RED: Dict[str, str] = {}  # biến thể AUD-SEC-202 cũ nay bị chặn bởi luật D-275 (`` `# ``/nháy lẻ trước `$'`)

# Loại trừ có lý do (không phải lỗ của guard): ca gốc chặn vì ĐÍCH TƯƠNG ĐỐI theo thư mục dự án (`.autopilot/…`,
# `tests/…`, `.claude/hooks` viết không `/` đầu, `~+` = `$PWD`). Sau `cd /tmp &&` lệnh ghi vào `/tmp/…`, không chạm dự
# án — guard cho chạy là đúng, nên bất biến deny đơn điệu không áp cho biến thể có bộ bọc `cd-tmp` của các ca này.
# Ca chặn vì đích tuyệt đối/`~`/mạng (`rm -rf ~`, push main, merge…) vẫn bị đòi deny sau `cd /tmp`.
CWD_RELATIVE: Dict[str, str] = {
    "guard-audit1020c-cd-autopilot-script": "cd .autopilot → /tmp/.autopilot",
    "guard-audit1020c-tilde-plus-evidence": "~+ là $PWD = /tmp sau cd",
    "guard-har024-bash-state": ".autopilot/state.json tương đối",
    "guard-har026-git-rm-test": "tests/test_a.py tương đối (file của ca nằm ở thư mục ca)",
    "guard-har026-sed-assert": "tests/test_a.py tương đối (file của ca nằm ở thư mục ca)",
    "guard-review186-os-path-os-chain": ".claude/hooks tương đối → /tmp/.claude/hooks",
    "guard-sec084-var-evidence": ".autopilot/verified.json tương đối",
    "guard-sec085-cd-autopilot-evidence": "cd .autopilot → /tmp/.autopilot",
    "guard-sec087-cd-autopilot-pipe-sh": "cd .autopilot → /tmp/.autopilot",
    "guard-sec089-sqlite-evidence": ".autopilot/x.db tương đối",
    "guard-advrev-rm-fence-dir": ".claude tương đối → /tmp/.claude",
    "guard-advrev-chmod-dirglob-guard": ".claude/*/guard.py tương đối → /tmp/.claude",
    "guard-advrev-truncate-dirglob-guard": ".claude/*/guard.py tương đối → /tmp/.claude",
    "guard-rev361b-dd-ap": ".autopilot/state.json tương đối",
    "guard-rev361b-dddd-ap": ".autopilot/state.json tương đối",
    "guard-rev361b-arith-semi-ap": ".autopilot/state.json tương đối",
    "guard-rev361b-trail-sp-ap": ".autopilot/state.json tương đối",
    "guard-rev361b-dd-stage": "docs/autopilot/STAGE.json tương đối",
    "guard-rev361b-dddd-stage": "docs/autopilot/STAGE.json tương đối",
    "guard-rev361b-arith-semi-stage": "docs/autopilot/STAGE.json tương đối",
    "guard-rev361b-trail-sp-stage": "docs/autopilot/STAGE.json tương đối",
    "guard-rev361b-oldarith-ap": ".autopilot/state.json tương đối",
    "guard-rev361c-dq-body-ap": ".autopilot/state.json tương đối",
    "guard-rev361c-dq-body-stage": "docs/autopilot/STAGE.json tương đối",
    "guard-har154-rm-ledger-dir": "docs/autopilot tương đối → /tmp/docs/autopilot",
    "guard-har154-git-mv-ledger-dir": "docs/autopilot tương đối → /tmp/docs/autopilot",
    "guard-har154-cp-into-ledger-dir": "docs/autopilot/ tương đối → /tmp/docs/autopilot",
    "guard-har154-git-C-rm-ledger-dir": "git -C docs tương đối → /tmp/docs/autopilot",
    "guard-har154-git-worktree-mv-ledger-dir": "--work-tree=docs tương đối → /tmp/docs/autopilot",
    "guard-sec188-pr-create-combined-title": "`ai_attribution: forbid` ở xt.yaml của repo ca; /tmp không khai",
    "guard-sec188-pr-create-combined-body": "`ai_attribution: forbid` ở xt.yaml của repo ca; /tmp không khai",
}


def excused(vid: str, red: Dict[str, Any]) -> bool:
    """Biến thể đỏ được loại trừ theo `CWD_RELATIVE`: deny mất đi chỉ vì `cd /tmp` đổi đích tương đối."""
    return red["invariant"] == "deny-monotone" and "cd-tmp" in vid.split("--")[1] and red["case"]["id"] in CWD_RELATIVE


def _cases() -> List[Dict[str, Any]]:
    cases, _ = xt.autonomy_corpus(CORPUS)
    return [c for c in cases if c["group"] == "guard" and c["input"].get("tool", "bash") == "bash"]


def _variants(case: Dict[str, Any], names: Tuple[str, ...]) -> Optional[Tuple[str, str]]:
    cmd: Optional[str] = str(case["input"]["command"])
    for n in names:
        cmd = WRAPS[n](cmd) if cmd is not None else None
    return None if cmd is None else (f"fuzz-{case['id']}--{'+'.join(names)}", cmd)


def _grid(cases: List[Dict[str, Any]]) -> List[Tuple[Dict[str, Any], str, str]]:
    out: List[Tuple[Dict[str, Any], str, str]] = []
    for c in cases:
        allowed = c["expect"]["allowed"]
        for n in WRAPS if not allowed else HARMLESS:
            v = _variants(c, (n,))
            if v is not None:
                out.append((c, *v))
    return out


def _random(cases: List[Dict[str, Any]], rounds: int, seed: int) -> List[Tuple[Dict[str, Any], str, str]]:
    rng = random.Random(seed)
    out: List[Tuple[Dict[str, Any], str, str]] = []
    deny = [c for c in cases if not c["expect"]["allowed"]]
    allow = [c for c in cases if c["expect"]["allowed"]]
    for i in range(rounds):
        c = rng.choice(deny if i % 3 else allow)
        pool = list(WRAPS) if not c["expect"]["allowed"] else list(HARMLESS)
        v = _variants(c, tuple(rng.choice(pool) for _ in range(rng.randint(2, 3))))
        if v is not None:
            out.append((c, *v))
    return out


class _Runner:
    """Gọi guard như `autonomy-bench`; ghi ngoại lệ của `_rule_decision` (bench nuốt chúng vào `_failure_decision`)."""

    def __init__(self, env: xt.BenchEnv) -> None:
        self.env = env
        guard = env.module("guard")
        real = guard._rule_decision
        self.raised: List[str] = []

        def spy(*a: Any) -> Any:
            try:
                return real(*a)
            except Exception as exc:
                self.raised.append(f"{type(exc).__name__}: {exc}")
                raise

        guard._rule_decision = spy

    def run(self, case: Dict[str, Any], cmd: str) -> Tuple[bool, str]:
        """(allowed, lỗi) — lỗi rỗng khi guard không ném."""
        self.raised.clear()
        got = xt._bench_guard({**case["input"], "command": cmd}, self.env)
        return bool(got["allowed"]), "; ".join(self.raised)


def fuzz(rounds: int = ROUNDS, seed: int = SEED) -> Dict[str, Any]:
    """Chạy lưới bậc 1 + `rounds` biến thể ghép; trả số biến thể và các biến thể vi phạm bất biến."""
    cases = _cases()
    variants = _grid(cases) + _random(cases, rounds, seed)
    red: Dict[str, Dict[str, Any]] = {}
    with tempfile.TemporaryDirectory(prefix="xt-fuzz-") as tmp:
        runner = _Runner(xt.BenchEnv(Path(tmp).resolve()))
        for case, vid, cmd in variants:
            allowed, err = runner.run(case, cmd)
            want = bool(case["expect"]["allowed"])
            if err or allowed != want:
                why = "exception" if err else ("deny-monotone" if not want else "allow-kept")
                red[vid] = {"case": case, "command": cmd, "invariant": why, "error": err, "allowed": allowed}
    return {"variants": len(variants), "red": red}


def pending_cases() -> List[Dict[str, Any]]:
    if not PENDING.is_file():
        return []
    data = json.loads(PENDING.read_text(encoding="utf-8"))
    return list(data["cases"])


class GuardFuzzTest(unittest.TestCase):
    """Ba bất biến trên lưới bậc 1 + biến thể ghép tất định."""

    result: Dict[str, Any]

    @classmethod
    def setUpClass(cls) -> None:
        cls.result = fuzz()

    def test_guard_fuzz_variants_generated(self) -> None:
        cases = _cases()
        self.assertGreater(self.result["variants"], len(cases) * 3)
        self.assertTrue(any(not c["expect"]["allowed"] for c in cases))
        self.assertTrue(any(c["expect"]["allowed"] for c in cases))

    def test_guard_fuzz_invariants_hold(self) -> None:
        red = self.result["red"]
        new = {
            k: (v["invariant"], v["command"], v["error"])
            for k, v in red.items()
            if k not in KNOWN_RED and not excused(k, v)
        }
        self.assertEqual(new, {}, f"{len(new)} biến thể đỏ mới / {self.result['variants']} — ghi pending + sổ audit")

    def test_guard_fuzz_known_red_still_red_and_pending(self) -> None:
        """Loại trừ có lý do: mỗi biến thể trong KNOWN_RED còn đỏ (sửa xong thì gỡ, chuyển ca sang guard.json) và có ca
        trong pending/guard.json cùng lệnh, kỳ vọng như ca gốc, refs gồm ID sổ audit ghi trong lý do."""
        pend = {c["id"]: c for c in pending_cases()}
        self.assertEqual(sorted(pend), sorted(KNOWN_RED))
        for vid, why in KNOWN_RED.items():
            with self.subTest(vid):
                self.assertIn(vid, self.result["red"])
                got = self.result["red"][vid]
                self.assertEqual(pend[vid]["input"]["command"], got["command"])
                self.assertEqual(pend[vid]["expect"], {"allowed": got["case"]["expect"]["allowed"]})
                self.assertTrue(pend[vid]["refs"] and all(r in why for r in pend[vid]["refs"]))

    def test_guard_fuzz_cwd_relative_exclusions_still_needed(self) -> None:
        """Loại trừ `CWD_RELATIVE` còn đúng: mỗi ca vẫn đỏ ở lưới `cd-tmp` (guard đổi thì gỡ khỏi danh sách) và ca gốc
        (không bọc) vẫn bị chặn."""
        red = self.result["red"]
        self.assertEqual(sorted(i for i in CWD_RELATIVE if f"fuzz-{i}--cd-tmp" in red), sorted(CWD_RELATIVE))
        cases = {c["id"]: c for c in _cases()}
        self.assertTrue(all(cases[i]["expect"]["allowed"] is False for i in CWD_RELATIVE))
        self.assertFalse(
            excused("fuzz-x--seq", {"invariant": "deny-monotone", "case": {"id": next(iter(CWD_RELATIVE))}})
        )


class GuardFuzzWrapTest(unittest.TestCase):
    """Bộ bọc: áp đúng chỗ, từ chối chỗ đổi nghĩa; tất định theo seed."""

    def test_guard_fuzz_exec_wrap_skips_shell_words(self) -> None:
        nice = WRAPS["nice"]
        self.assertEqual(nice("rm -rf ~"), "nice -n 5 rm -rf ~")
        for cmd in (
            "cd .claude && x",
            "B=main; git push",
            "2>/dev/null cd x",
            "for i in 1; do x; done",
            "(x)",
            "",
            "'",
        ):
            self.assertIsNone(nice(cmd), cmd)

    def test_guard_fuzz_nfkc_only_python_identifiers(self) -> None:
        v = WRAPS["nfkc"]("python3 -c \"import os; os.remove('.env')\"")
        self.assertIsNotNone(v)
        script = shlex.split(str(v))[2]
        self.assertIn("'.env'", script)  # chuỗi không đổi
        self.assertNotEqual(script, unicodedata.normalize("NFKC", script))
        self.assertEqual(ast.dump(ast.parse(script)), ast.dump(ast.parse(unicodedata.normalize("NFKC", script))))
        for cmd in ("rm -rf ~", "python3 -c 'if'", "python3 -c '1'", "python3 -c \"'", "python3 -Ic 'x'"):
            self.assertIsNone(WRAPS["nfkc"](cmd), cmd)

    def test_guard_fuzz_deterministic(self) -> None:
        cases = _cases()
        a = [v[1:] for v in _random(cases, 20, SEED)]
        self.assertEqual(a, [v[1:] for v in _random(cases, 20, SEED)])
        self.assertNotEqual(a, [v[1:] for v in _random(cases, 20, SEED + 1)])

    def test_guard_fuzz_detects_wrapper_regression(self) -> None:
        """Fuzz có răng: guard giả bỏ qua lệnh bọc `nice` (deny mất) và chặn oan lệnh bọc `timeout` → đỏ đúng bất biến."""
        real = xt.BenchEnv.module

        def broken(env: xt.BenchEnv, name: str) -> Any:
            mod = real(env, name)
            if getattr(mod, "fuzz_fake", False):  # module được cache theo env: bọc một lần
                return mod
            mod.fuzz_fake = True
            inner = mod.bash_decision

            def decide(cmd: str, *a: Any, **kw: Any) -> Any:
                out = inner(cmd, *a, **kw)
                if kw.get("depth", a[2] if len(a) > 2 else 0):  # chỉ lệnh ngoài cùng
                    return out
                if cmd.startswith("nice "):
                    return {**out, "decision": ""}
                if cmd.startswith("timeout "):
                    return {**out, "decision": "deny", "reason": "giả"}
                return out

            mod.bash_decision = decide
            return mod

        with unittest.mock.patch.object(xt.BenchEnv, "module", broken):
            red = fuzz(rounds=0)["red"]
        kinds = {(k.split("--")[1], v["invariant"]) for k, v in red.items() if not excused(k, v)}
        self.assertEqual(kinds, {("nice", "deny-monotone"), ("timeout", "allow-kept")})

    def test_guard_fuzz_runner_records_exception(self) -> None:
        """Ngoại lệ trong `_rule_decision` được ghi (bất biến 2) dù bench chuyển nó thành `_failure_decision`."""
        with tempfile.TemporaryDirectory() as tmp:
            env = xt.BenchEnv(Path(tmp).resolve())
            env.module("guard").bash_decision = None  # gọi None → TypeError giữa chừng
            runner = _Runner(env)
            allowed, err = runner.run({"input": {"tool": "bash", "policy": "default"}}, "ls")
        self.assertTrue(err)
        self.assertTrue(allowed)  # fail-open với lệnh không phải merge: đúng lý do bất biến 2 tồn tại


if __name__ == "__main__":
    unittest.main()
