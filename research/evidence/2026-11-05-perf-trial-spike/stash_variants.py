"""Spike T-3551 phụ: biến thể `git stash push --include-untracked` để thu hồi candidate, ghi exit + trạng thái cây sau."""

import json
import os
import shutil
import subprocess
from pathlib import Path

S = Path(__file__).resolve().parent / "lab-stash"
ENV = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
ENV.update(
    GIT_AUTHOR_NAME="s", GIT_AUTHOR_EMAIL="s@e.invalid", GIT_COMMITTER_NAME="s", GIT_COMMITTER_EMAIL="s@e.invalid"
)


def sh(cwd, *cmd):
    r = subprocess.run(list(cmd), cwd=cwd, capture_output=True, text=True, env=ENV)
    return r.returncode, (r.stdout + r.stderr).strip()


def repo(name, ignore_autopilot):
    d = S / name
    d.mkdir(parents=True)
    sh(d, "git", "init", "-q")
    (d / "a.py").write_text("x = 1\n")
    (d / ".gitignore").write_text((".autopilot/\n" if ignore_autopilot else "") + ".cache/\n")
    sh(d, "git", "add", "-A")
    sh(d, "git", "commit", "-qm", "base")
    (d / ".autopilot").mkdir()
    (d / ".autopilot/state.json").write_text("{}\n")
    (d / "a.py").write_text("x = 2\n")
    (d / "new.py").write_text("y = 1\n")
    (d / ".cache").mkdir()
    (d / ".cache/c.bin").write_text("cache\n")
    return d


CASES = {
    "V1 ignored + exclude pathspec": (True, ["--", ".", ":(exclude).autopilot"]),
    "V2 ignored + no pathspec": (True, []),
    "V3 not-ignored + exclude pathspec": (False, ["--", ".", ":(exclude).autopilot"]),
    "V4 ignored + explicit file list": (True, ["--", "a.py", "new.py"]),
    "V5 not-ignored + explicit file list": (False, ["--", "a.py", "new.py"]),
}
if S.exists():
    shutil.rmtree(S)
out = {}
for i, (name, (ign, spec)) in enumerate(CASES.items()):
    d = repo(f"r{i}", ign)
    code, msg = sh(d, "git", "stash", "push", "--include-untracked", "-m", "xt-perf-trial", *spec)
    _, status = sh(d, "git", "status", "--porcelain", "--untracked-files=all")
    out[name] = {
        "exit": code,
        "msg": msg.splitlines()[-1][:90] if msg else "",
        "status_after": status.splitlines(),
        "a.py": (d / "a.py").read_text().strip(),
        "autopilot_kept": (d / ".autopilot/state.json").exists(),
        "cache_kept": (d / ".cache/c.bin").exists(),
        "stash_list": sh(d, "git", "stash", "list")[1],
    }
print(json.dumps(out, ensure_ascii=False, indent=1))
