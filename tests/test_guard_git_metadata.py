"""AUD-SEC-445/446: Git có thể đọc metadata nằm ngoài thư mục .git."""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".claude" / "hooks"))
import guard


class GitMetadataTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.tmp = Path(temp.name)
        self.root = self.tmp / "project"
        self.root.mkdir()
        self.bare = self.tmp / "bare"
        self.git_init(self.root)
        self.git_init(self.bare, "--bare")

    def git_init(self, path, *args):
        subprocess.run(["git", "init", "-q", *args, str(path)], check=True, capture_output=True)

    def policy(self, cmd):
        with patch.dict(
            os.environ, {"CLAUDE_PROJECT_DIR": str(self.root), "XT_GUARD_POLICY": "", "XT_GUARD_PHASE": "harden"}
        ):
            return guard.apply_policy(guard.bash_decision(cmd, str(self.root)))

    def assert_code(self, cmd, code):
        decision = self.policy(cmd)
        self.assertEqual(decision["code"], code, (cmd, decision))

    def test_separate_git_dir(self):
        for cmd in (
            f"git init --separate-git-dir={self.tmp / 'meta'}",
            f"git init --sep {self.tmp / 'meta'}",
            f"git clone --separate-git-dir {self.tmp / 'meta'} {self.root} clone",
        ):
            self.assert_code(cmd, "HOOK_BYPASS")
        self.assert_code("git init -- --separate-git-dir", "NONE")
        self.assert_code("git init other", "NONE")

        meta = self.tmp / "meta"
        self.git_init(self.root, f"--separate-git-dir={meta}")
        self.assert_code(f"printf x >> {meta / 'config'}", "HOOK_BYPASS")
        self.assert_code(f"cat {meta / 'config'}", "NONE")
        self.assert_code(f"printf x >> {meta / 'notes'}", "NONE")

    def test_bare_git_metadata(self):
        self.assert_code(f"printf x >> {self.bare / 'config'}", "HOOK_BYPASS")
        self.assert_code(f"printf x >> {self.bare / 'config.worktree'}", "HOOK_BYPASS")
        self.assert_code(f"printf x >> {self.bare / 'hooks' / 'pre-commit'}", "HOOK_BYPASS")
        self.assert_code(f"printf x >> {self.bare / 'worktrees' / 'w' / 'config.worktree'}", "HOOK_BYPASS")
        self.assert_code("printf x >> config", "NONE")
        self.assert_code("printf x >> hooks/pre-commit", "NONE")

        worktree = self.tmp / "worktree"
        worktree.mkdir()
        (worktree / "HEAD").write_text("ref: refs/heads/main\n")
        (worktree / "commondir").write_text(f"{self.bare}\n")
        self.assert_code(f"printf x >> {worktree / 'config.worktree'}", "HOOK_BYPASS")
        self.assert_code(f"printf x >> {worktree / 'commondir'}", "HOOK_BYPASS")

    def test_bare_git_rejects_preexisting_exec_config(self):
        config = self.bare / "config"
        self.assert_code("git rev-parse HEAD", "NONE")
        self.assert_code(f"git -C {self.bare} rev-parse --is-bare-repository", "NONE")
        with config.open("a") as f:
            f.write("[core]\n\tpager = cat\n")
        self.assert_code(f"git -C {self.bare} rev-parse --is-bare-repository", "NONE")
        with config.open("a") as f:
            f.write("[diff]\n\texternal = /tmp/driver\n")
        self.assert_code(f"git -C {self.bare} diff HEAD^ HEAD", "HOOK_BYPASS")
        self.assert_code(f"cd {self.bare} && git diff HEAD^ HEAD", "HOOK_BYPASS")
        objects = self.bare / "objects"
        self.assert_code(f"git -C {objects} diff --ext-diff HEAD^ HEAD -- :/", "HOOK_BYPASS")
        self.assert_code(f"git -C {self.tmp} rev-parse HEAD", "NONE")
        self.assert_code(f"GIT_CEILING_DIRECTORIES={self.bare} git -C {objects} rev-parse HEAD", "NONE")
        self.assert_code(f"GIT_CEILING_DIRECTORIES={self.bare}; git -C {objects} rev-parse HEAD", "HOOK_BYPASS")
        self.assert_code(
            f"GIT_CEILING_DIRECTORIES={self.bare} env -u GIT_CEILING_DIRECTORIES git -C {objects} rev-parse HEAD",
            "HOOK_BYPASS",
        )
        with patch.object(guard.os.path, "ismount", side_effect=lambda path: path == str(objects)):
            self.assert_code(f"git -C {objects} rev-parse HEAD", "NONE")
            self.assert_code(f"GIT_DISCOVERY_ACROSS_FILESYSTEM=true git -C {objects} rev-parse HEAD", "HOOK_BYPASS")
        nested = objects / "nested"
        self.git_init(nested)
        self.assert_code(f"git -C {nested} rev-parse HEAD", "NONE")
        self.assert_code(f"git -C {self.bare} config --get diff.external", "NONE")
        config.write_text(f"[include]\n\tpath = {config}\n")
        self.assertIn("include.path", self.policy(f"git -C {self.bare} rev-parse HEAD")["reason"])
        config.write_text("[core]\n\thooksPath = /dev/null\n")
        self.assert_code(f"git -C {self.bare} rev-parse HEAD", "HOOK_BYPASS")
        config.write_text("[invalid\n")
        self.assert_code(f"git -C {self.bare} rev-parse HEAD", "HOOK_BYPASS")
        config.unlink()
        self.assert_code(f"git -C {self.bare} rev-parse HEAD", "NONE")

    def test_bare_git_creation_with_metadata_write(self):
        future = self.tmp / "future"
        for create in (
            f"git init --bare {future}",
            f"git --bare init {future}",
            f"git clone --mirror {self.root} {future}",
        ):
            self.assert_code(f"{create} && printf x >> {future / 'config'}", "HOOK_BYPASS")
            self.assert_code(f"{create} && cat {future / 'config'}", "NONE")
            self.assert_code(f"{create} && printf x > note.txt", "NONE")
        self.assert_code(f"git init -- --bare && printf x > {future / 'config'}", "NONE")
        self.assert_code(f'''git init --bare {future} && python3 -c "open('{future / "config"}','w')"''', "HOOK_BYPASS")
        self.assert_code(
            f'''git init --bare {future} && python3 -c "print(open('{future / "config"}').read())"''', "NONE"
        )

    def test_bare_git_alternate_object_store(self):
        store = self.tmp / "store"
        (self.bare / "objects").rename(store)
        with (self.bare / "config").open("a") as f:
            f.write("[diff]\n\texternal = /tmp/driver\n")
        self.assert_code(f"GIT_OBJECT_DIRECTORY={store} git -C {self.bare} diff HEAD^ HEAD", "BUDGET")
        self.assert_code(f"export GIT_OBJECT_DIRECTORY={store}; git -C {self.bare} diff HEAD^ HEAD", "BUDGET")


if __name__ == "__main__":
    unittest.main()
