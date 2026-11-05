"""Spike T-3551: môi trường đo cho `perf trial` — chạy: python3 spike.py <đường tới scripts/xt.py> --out <thư mục tạm>.

Mọi thứ ghi vào `--out` (thư mục mới hoặc rỗng, ngoài thư mục này): repo đồ chơi `lab/`, mọi lệnh (cwd, exit, giây, đuôi
output) vào `log.json`, số đo chính + giây theo bước vào `results.json`. Không đụng repo khung, không đè `results.json` đã
commit cạnh script (chép tay sau khi xem).
"""

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import files as F  # noqa: E402

HERE = Path(__file__).resolve().parent
if len(sys.argv) != 4 or sys.argv[2] != "--out":
    raise SystemExit("dùng: python3 spike.py <scripts/xt.py> --out <thư mục tạm>")
XT_SRC = Path(sys.argv[1]).resolve()
S = Path(sys.argv[3]).resolve()
if S == HERE or HERE in S.parents or (S.exists() and any(S.iterdir())):
    raise SystemExit(f"--out phải là thư mục mới/rỗng ngoài {HERE}")
S.mkdir(parents=True, exist_ok=True)
LAB = S / "lab"
LOG: list = []
R: dict = {}
ENV = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
ENV.update(
    GIT_AUTHOR_NAME="spike",
    GIT_AUTHOR_EMAIL="spike@example.invalid",
    GIT_COMMITTER_NAME="spike",
    GIT_COMMITTER_EMAIL="spike@example.invalid",
)
N = 200000


def run(step, cmd, cwd, check=True, env=None):
    t = time.perf_counter()
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env or ENV)
    dt = time.perf_counter() - t
    LOG.append(
        {
            "step": step,
            "cmd": " ".join(map(str, cmd)),
            "cwd": str(cwd).replace(str(S), "$S"),
            "exit": r.returncode,
            "secs": round(dt, 3),
            "tail": (r.stdout + r.stderr)[-400:],
        }
    )
    if check and r.returncode:
        raise SystemExit(f"[{step}] exit {r.returncode}: {cmd}\n{r.stdout}\n{r.stderr}")
    return r


def git(step, cwd, *a, check=True):
    return run(step, ["git", "-c", "protocol.file.allow=always", *a], cwd, check)


def w(p: Path, text: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def ref_value(lib_src: str, n: int) -> int:
    ns: dict = {}
    exec(lib_src, ns)
    return ns["work"](n)


# ---------- dựng repo ----------
def build():
    if LAB.exists():
        shutil.rmtree(LAB)
    sub, proj = LAB / "subrepo", LAB / "proj"
    sub.mkdir(parents=True)
    git("sub-init", sub, "init", "-q", "-b", "main")
    w(sub / "data.txt", "dữ liệu submodule v1\n")
    git("sub-commit", sub, "add", "-A")
    git("sub-commit", sub, "commit", "-qm", "sub v1")
    proj.mkdir()
    git("init", proj, "init", "-q", "-b", "main")
    w(proj / "pyproject.toml", F.PYPROJECT)
    w(proj / "src/fastlib/__init__.py", F.LIB_B)
    w(proj / "bench/run.py", F.BENCH)
    w(proj / "heldout/gen.py", F.HELDOUT_GEN)
    w(proj / "tests/equiv/test_equiv.py", F.EQUIV.replace("None  # điền lúc dựng", str(ref_value(F.LIB_B, 1000))))
    w(proj / ".gitignore", F.GITIGNORE)
    w(proj / "js/package.json", F.JS_PKG)
    w(proj / "jslib/package.json", F.JSLIB_PKG)
    w(proj / "jslib/index.js", F.JSLIB_INDEX)
    w(proj / "js/bench.js", F.JS_BENCH)
    (proj / "scripts").mkdir()
    shutil.copy2(XT_SRC, proj / "scripts/xt.py")
    r = run("npm-install-lock", ["npm", "install", "--no-audit", "--no-fund", "--offline"], proj / "js", check=False)
    R["npm_install_agent"] = {"exit": r.returncode, "secs": LOG[-1]["secs"]}
    git("submodule-add", proj, "submodule", "add", "-q", "../subrepo", "vendor/sub")
    git("commit-B", proj, "add", "-A")
    git("commit-B", proj, "commit", "-qm", "B: gốc")
    b = git("rev-B", proj, "rev-parse", "HEAD").stdout.strip()
    w(proj / "src/fastlib/__init__.py", F.LIB_K)
    git("commit-K", proj, "commit", "-qam", "K: giữ lần trước")
    k = git("rev-K", proj, "rev-parse", "HEAD").stdout.strip()
    git("origin-main", proj, "update-ref", "refs/remotes/origin/main", b)
    R["B"], R["K"] = b, k
    return proj, b, k


def setup_tree(tag, tree: Path):
    """Bước --setup (ghim từ commit gốc): submodule, venv + cài editable, node_modules — trong chính cây `tree`."""
    t0 = time.perf_counter()
    git(f"setup-{tag}-submodule", tree, "submodule", "update", "--init", "-q")
    run(f"setup-{tag}-venv", ["uv", "venv", "-q", ".venv"], tree)
    run(f"setup-{tag}-pip-e", ["uv", "pip", "install", "-q", "--python", ".venv/bin/python", "-e", "."], tree)
    ci = run(f"setup-{tag}-npm-ci", ["npm", "ci", "--no-audit", "--no-fund", "--offline"], tree / "js", check=False)
    R.setdefault("setup_secs", {})[tag] = round(time.perf_counter() - t0, 3)
    R.setdefault("npm_ci_exit", {})[tag] = ci.returncode
    return ci.returncode


def where(tag, tree: Path, python: Path):
    py = run(f"where-{tag}", [str(python), "bench/run.py", "where", "0"], tree).stdout.strip()
    js = run(f"where-js-{tag}", ["node", "bench.js"], tree / "js", check=False)
    sub = git(f"where-sub-{tag}", tree, "-C", "vendor/sub", "rev-parse", "HEAD", check=False).stdout.strip()
    link = git(f"gitlink-{tag}", tree, "rev-parse", "HEAD:vendor/sub", check=False).stdout.strip()
    return {
        "fastlib": py.replace(str(S), "$S"),
        "jslib": js.stdout.strip().replace(str(S), "$S") or f"exit {js.returncode}",
        "sub_ok": bool(sub) and sub == link,
    }


def instr(tag, tree: Path, n=N, python=None):
    py = str(python or tree / ".venv/bin/python")
    vals = [json.loads(run(f"instr-{tag}", [py, "bench/run.py", "instr", str(n)], tree).stdout) for _ in range(3)]
    return [v["instr"] for v in vals], vals[0]["result"]


def mem(tag, tree: Path):
    return [int(run(f"mem-{tag}", [".venv/bin/python", "bench/run.py", "mem", str(N)], tree).stdout) for _ in range(3)]


def sample(tag, tree: Path, xt: Path, out: Path):
    r = run(
        f"sample-{tag}",
        [
            "python3",
            "-I",
            str(xt),
            "perf",
            "sample",
            "--out",
            str(out),
            "--runs",
            "10",
            "--warmup",
            "2",
            "--harness",
            "bench/*",
            "--",
            ".venv/bin/python",
            "bench/run.py",
            "time",
            str(N),
        ],
        tree,
        check=False,
    )
    return r.returncode


def compare(tag, xt: Path, before: Path, after: Path, base=None, exact=False, cwd=None):
    cmd = ["python3", "-I", str(xt), "perf", "compare", "--json", str(before), str(after)]
    if base:
        cmd += ["--base", base]
    if exact:
        cmd.append("--exact")
    r = run(f"compare-{tag}", cmd, cwd or LAB / "proj", check=False)
    try:
        doc = json.loads(r.stdout)
    except ValueError:
        doc = {"stderr": r.stderr.strip()[-300:]}
    return {
        "exit": r.returncode,
        **{k: doc.get(k) for k in ("verdict", "change", "p", "unverified-manual", "stderr") if k in doc},
    }


def trial_list(tree: Path):
    """Danh sách file của lần thử: đổi so HEAD + chưa track (không ignored), trừ `.autopilot/` — pathspec tường minh cho stash."""
    r = run("trial-list", ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"], tree).stdout
    names = [e[3:] for e in r.split("\0") if len(e) > 3]
    return [n for n in names if not n.startswith(".autopilot/")]


def fp(xt_dir: Path, tree: Path):
    code = f"import sys; sys.path.insert(0, {str(xt_dir)!r}); import xt; from pathlib import Path; print(xt.tree_fingerprint(Path({str(tree)!r})))"
    return run("tree_fp", ["python3", "-I", "-c", code], tree).stdout.strip()


def main():
    proj, b, k = build()
    # 1. môi trường agent (cây candidate)
    setup_tree("agent", proj)
    # 2. công cụ chấm lấy từ commit gốc
    tool = LAB / "tool"
    tool.mkdir()
    blob = git("tool-show", proj, "show", f"{b}:scripts/xt.py").stdout
    (tool / "xt.py").write_text(blob, encoding="utf-8")
    xt = tool / "xt.py"
    R["tool_help_exit"] = run("tool-help", ["python3", "-I", str(xt), "perf", "--help"], LAB, check=False).returncode
    fp_start = fp(tool, proj)
    # 3. candidate chưa commit trên K
    w(proj / "src/fastlib/__init__.py", F.LIB_C)
    w(proj / "src/fastlib/_note.py", "# file mới chưa track của candidate\n")
    # 4. worktree tạm ngoài cây agent
    wts = LAB / "wts"
    wts.mkdir()
    wb, wk = wts / "base", wts / "start"
    git("wt-add-base", proj, "worktree", "add", "-q", "--detach", str(wb), b)
    git("wt-add-start", proj, "worktree", "add", "-q", "--detach", str(wk), k)
    R["wt_add_secs"] = [e["secs"] for e in LOG if e["step"].startswith("wt-add")]
    # 4a. hiểm hoạ: đo cây gốc bằng venv/node_modules của cây agent
    R["hazard_base_with_agent_venv"] = where("hazard", wb, proj / ".venv/bin/python")
    (wb / "js/node_modules").symlink_to(proj / "js/node_modules")
    R["hazard_base_node_modules_symlinked"] = (
        run("hazard-js", ["node", "bench.js"], wb / "js").stdout.strip().replace(str(S), "$S")
    )
    (wb / "js/node_modules").unlink()
    R["agent_venv_pth"] = sorted(
        p.name + ": " + p.read_text(encoding="utf-8").strip().replace(str(S), "$S")[:160]
        for p in (proj / ".venv").glob("lib/python*/site-packages/*.pth")
    )
    R["agent_jslib_link"] = os.readlink(proj / "js/node_modules/jslib")
    # 4b. setup ghim trong từng worktree
    setup_tree("base", wb)
    setup_tree("start", wk)
    R["where"] = {t: where(t, d, d / ".venv/bin/python") for t, d in (("base", wb), ("start", wk), ("candidate", proj))}
    # 4c. candidate dựng lại ở worktree riêng (phương án C2): start_head + diff + file chưa track, bộ đo từ gốc
    wc = wts / "cand"
    t0 = time.perf_counter()
    git("wt-add-cand", proj, "worktree", "add", "-q", "--detach", str(wc), k)
    patch = run("cand-diff", ["git", "diff", "--binary", "HEAD"], proj).stdout
    p = subprocess.run(["git", "apply", "--binary"], cwd=wc, input=patch, text=True, capture_output=True, env=ENV)
    LOG.append(
        {
            "step": "cand-apply",
            "cmd": "git apply --binary <diff>",
            "cwd": "$S/lab/wts/cand",
            "exit": p.returncode,
            "secs": 0,
            "tail": p.stderr[-200:],
        }
    )
    for name in run("cand-untracked", ["git", "ls-files", "--others", "--exclude-standard", "-z"], proj).stdout.split(
        "\0"
    ):
        if name:
            (wc / name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(proj / name, wc / name)
    git("cand-overlay", wc, "checkout", b, "--", "bench", "tests/equiv", "heldout")
    setup_tree("cand", wc)
    R["c2_build_secs"] = round(time.perf_counter() - t0, 3)
    R["where"]["cand_wt"] = where("cand_wt", wc, wc / ".venv/bin/python")
    R["c2_src_equal"] = (
        run("c2-diff", ["git", "diff", "--binary", "HEAD", "--", "src"], wc).stdout
        == run("ag-diff", ["git", "diff", "--binary", "HEAD", "--", "src"], proj).stdout
        and (wc / "src/fastlib/_note.py").exists()
    )
    # 5. đo cùng lượt: thời gian tường (perf sample của công cụ gốc) + đại lượng tất định
    out = LAB / "out"
    out.mkdir()
    t0 = time.perf_counter()
    R["sample_exit"] = {
        t: sample(t, d, xt, out / f"{t}.json")
        for t, d in (("base", wb), ("start", wk), ("cand", wc), ("cand_inplace", proj))
    }
    R["sample_round_secs"] = round(time.perf_counter() - t0, 3)
    R["sample_dirty"] = {
        t: json.loads((out / f"{t}.json").read_text())["dirty"] for t in ("base", "start", "cand", "cand_inplace")
    }
    R["cmp"] = {
        "base_vs_cand": compare("base-cand", xt, out / "base.json", out / "cand.json", base=b),
        "start_vs_cand": compare("start-cand", xt, out / "start.json", out / "cand.json", base=k),
        "base_vs_start": compare("base-start", xt, out / "base.json", out / "start.json", base=b),
    }
    # A/A: cùng cây gốc đo hai lần
    aa = []
    for i in range(3):
        sample(f"aa{i}", wb, xt, out / f"aa{i}.json")
        aa.append(compare(f"aa{i}", xt, out / "base.json", out / f"aa{i}.json", base=b))
    R["aa"] = aa
    R["wall_medians"] = {
        t: sorted(json.loads((out / f"{t}.json").read_text())["samples"])[5]
        for t in ("base", "start", "cand", "aa0", "aa1", "aa2")
    }
    t0 = time.perf_counter()
    R["instr"] = {t: instr(t, d) for t, d in (("base", wb), ("start", wk), ("cand", wc))}
    R["instr_secs"] = round(time.perf_counter() - t0, 3)
    R["mem"] = {t: mem(t, d) for t, d in (("base", wb), ("start", wk), ("cand", wc))}
    for t in ("base", "cand"):
        w(out / f"i-{t}.json", json.dumps(R["instr"][t][0]))
    R["cmp"]["instr_exact_raw"] = compare("instr-exact", xt, out / "i-base.json", out / "i-cand.json", exact=True)
    # 6. test tương đương (bộ của gốc) trên cây candidate
    R["equiv_cand"] = run(
        "equiv-cand",
        [".venv/bin/python", "-m", "unittest", "discover", "-q", "-s", "tests/equiv"],
        wc,
        check=False,
    ).returncode
    # 7. held-out: hạt giống sinh lúc finish, bộ sinh lấy từ gốc
    seed = int.from_bytes(os.urandom(8), "big")
    ns = run("heldout-gen", ["python3", "-I", "heldout/gen.py", str(seed)], wb).stdout.split()
    R["heldout_ns"] = ns
    R["heldout"] = {
        t: [instr(f"ho-{t}", d, int(n))[0][0] for n in ns] for t, d in (("base", wb), ("start", wk), ("cand", wc))
    }
    R["heldout_out_equal"] = (
        len(
            {tuple(instr(f"hoo-{t}", d, int(n))[1] for n in ns) for t, d in (("base", wb), ("start", wk), ("cand", wc))}
        )
        == 1
    )
    R["python_bench_vs_tool"] = [
        run(
            "pyver-bench", [str(wb / ".venv/bin/python"), "-c", "import sys; print(sys.version.split()[0])"], wb
        ).stdout.strip(),
        run("pyver-tool", ["python3", "-I", "-c", "import sys; print(sys.version.split()[0])"], wb).stdout.strip(),
    ]
    # 8. gian lận theo input: hard-code N của bộ đo
    short = F.LIB_SHORTCUT.replace("_KNOWN = None  # điền lúc dựng", f"_KNOWN = {ref_value(F.LIB_K, N)}")
    w(wc / "src/fastlib/__init__.py", short)
    R["shortcut"] = {"bench_n": instr("short", wc)[0][0], "heldout": [instr("ho-short", wc, int(n))[0][0] for n in ns]}
    w(wc / "src/fastlib/__init__.py", F.LIB_C)
    # 9. bộ chấm bị sửa — (a) file theo dõi trong cây agent
    w(
        proj / "bench/run.py",
        F.BENCH.replace("fastlib.work(n)\n        return", "fastlib.work(n // 10)\n        return", 1),
    )
    g = run(
        "guard-tamper",
        [
            "python3",
            "-I",
            str(xt),
            "perf",
            "guard",
            "--base",
            b,
            "--locked",
            "bench/*",
            "--locked",
            "tests/equiv/*",
            "--strict",
        ],
        proj,
        check=False,
    )
    R["tamper_tracked_guard_exit"] = g.returncode
    sample("cand_tamper", proj, xt, out / "cand_tamper.json")
    R["cmp"]["base_vs_tampered_inplace"] = compare("tamper", xt, out / "base.json", out / "cand_tamper.json", base=b)
    git("tamper-undo", proj, "checkout", "--", "bench/run.py")
    # (b) file bị bỏ qua (.pth trong .venv của agent) che fastlib bằng bản giả
    fake = proj / ".cache/fake/fastlib"
    w(
        fake / "__init__.py",
        "def work(n):\n    return %d if n == %d else 0\n__file__x = 'fake'\n" % (ref_value(F.LIB_K, N), N),
    )
    site = next((proj / ".venv").glob("lib/python*/site-packages"))
    fp_before_pth = fp(tool, proj)
    w(site / "aaa_spike.pth", f"import sys; sys.path.insert(0, {str(fake.parent)!r})\n")
    R["pth_cheat"] = {
        "tree_fp_unchanged": fp(tool, proj) == fp_before_pth,
        "guard_exit": run(
            "guard-pth",
            ["python3", "-I", str(xt), "perf", "guard", "--base", b, "--locked", "bench/*", "--strict"],
            proj,
            check=False,
        ).returncode,
        "inplace_instr": instr("pth-inplace", proj)[0][0],
        "c2_instr": instr("pth-c2", wc)[0][0],
    }
    # 10. baseline bị lái — (a) worktree gốc bị sửa trong lượt đo
    w(wb / "src/fastlib/__init__.py", F.LIB_B + "\nimport time as _t\n_t.sleep(0)\n")
    sample("base_tampered", wb, xt, out / "base_tampered.json")
    R["cmp"]["tampered_base"] = compare("base-tampered", xt, out / "base_tampered.json", out / "cand.json", base=b)
    git("wb-undo", wb, "checkout", "--", "src")
    # (b) ref dời sau start: SHA đã ghim không đổi
    git("ref-move", proj, "update-ref", "refs/remotes/origin/main", k)
    R["ref_moved"] = {
        "pinned": b[:12],
        "origin_main_now": git("ref-now", proj, "rev-parse", "origin/main").stdout.strip()[:12],
    }
    # 11. thu hồi: stash có phạm vi rồi kiểm vân tay
    w(proj / ".cache/ignored.txt", "file bị bỏ qua do candidate sinh\n")
    w(proj / ".autopilot/perf-trial.json", "{}\n")
    t0 = time.perf_counter()
    trial_files = trial_list(proj)
    R["trial_files"] = trial_files
    st = git(
        "stash",
        proj,
        "stash",
        "push",
        "--include-untracked",
        "-m",
        "xt-perf-trial T-1 #1",
        "--",
        *trial_files,
        check=False,
    )
    R["stash"] = {
        "exit": st.returncode,
        "secs": round(time.perf_counter() - t0, 3),
        "fp_back_to_start": fp(tool, proj) == fp_start,
        "ignored_left": (proj / ".cache/ignored.txt").exists(),
        "pth_left": (site / "aaa_spike.pth").exists(),
        "autopilot_left": (proj / ".autopilot/perf-trial.json").exists(),
        "list": git("stash-list", proj, "stash", "list").stdout.strip(),
    }
    (site / "aaa_spike.pth").unlink()
    # 11b. submodule bị sửa: stash -u không thu hồi
    w(proj / "vendor/sub/data.txt", "submodule bị sửa\n")
    sub_files = trial_list(proj)
    st_sub = git(
        "stash-sub",
        proj,
        "stash",
        "push",
        "--include-untracked",
        "-m",
        "xt-perf-trial sub",
        "--",
        *sub_files,
        check=False,
    )
    R["stash_submodule"] = {  # kết quả của chính lệnh stash, không LOG[-1] (fp() nối thêm một dòng log)
        "trial_files": sub_files,
        "exit": st_sub.returncode,
        "tail": (st_sub.stdout + st_sub.stderr)[-160:],
        "fp_back": fp(tool, proj) == fp_start,
    }
    git("sub-undo", proj, "-C", "vendor/sub", "checkout", "--", "data.txt")
    # 11c. .autopilot không bị ignore: stash không phạm vi cuốn theo sổ máy
    tiny = LAB / "tiny"
    tiny.mkdir()
    git("tiny", tiny, "init", "-q")
    w(tiny / "a.txt", "a\n")
    git("tiny", tiny, "add", "-A")
    git("tiny", tiny, "commit", "-qm", "a")
    w(tiny / ".autopilot/state.json", "{}\n")
    w(tiny / "a.txt", "b\n")
    git("tiny-stash-all", tiny, "stash", "push", "--include-untracked", "-q")
    R["stash_without_exclude_takes_autopilot"] = not (tiny / ".autopilot/state.json").exists()
    # 12. giữ: cây candidate (index tạm) = cây commit sau đó
    names = git("stash-list2", proj, "stash", "list", "--format=%gd %s").stdout.splitlines()
    ref = next(n.split()[0] for n in names if "T-1 #1" in n)
    git("stash-apply", proj, "stash", "apply", "-q", ref)
    tmpidx = LAB / "idx"
    env = {**ENV, "GIT_INDEX_FILE": str(tmpidx)}
    run("kept-read", ["git", "read-tree", "HEAD"], proj, env=env)
    kept_files = trial_list(proj)
    R["kept_files"] = kept_files
    run("kept-add", ["git", "add", "-A", "--", *kept_files], proj, env=env)
    kept_tree = run("kept-tree", ["git", "write-tree"], proj, env=env).stdout.strip()
    git("kept-commit", proj, "add", "-A", "--", *kept_files)
    git("kept-commit", proj, "commit", "-qm", "giữ candidate")
    R["kept_tree_equal"] = git("head-tree", proj, "rev-parse", "HEAD^{tree}").stdout.strip() == kept_tree
    # 13. commit giữa chừng: HEAD ≠ start_head
    R["head_moved"] = git("head", proj, "rev-parse", "HEAD").stdout.strip() != k
    # dọn worktree
    for d in (wb, wk, wc):
        git("wt-remove", proj, "worktree", "remove", "--force", str(d), check=False)
    R["wt_remove_secs"] = [e["secs"] for e in LOG if e["step"] == "wt-remove"]


def step_secs():
    """Giây theo bước (gộp lệnh cùng tên bước): số lần, tổng giây, exit — số trong nghiên cứu đối chiếu được không cần log."""
    agg: dict = {}
    for e in LOG:
        n, secs, exits = agg.get(e["step"], (0, 0.0, set()))
        agg[e["step"]] = (n + 1, secs + e["secs"], exits | {e["exit"]})
    return {k: f"{n}× {secs:.3f} s exit {','.join(map(str, sorted(ex)))}" for k, (n, secs, ex) in agg.items()}


R["loadavg_start"] = [round(x, 2) for x in os.getloadavg()]  # máy bận thì số giây không so được với lượt khác
try:
    main()
finally:
    R["loadavg_end"] = [round(x, 2) for x in os.getloadavg()]
    R["step_secs"] = step_secs()
    (S / "log.json").write_text(json.dumps(LOG, ensure_ascii=False, indent=1), encoding="utf-8")
    (S / "results.json").write_text(json.dumps(R, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(R, ensure_ascii=False, indent=1))
