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

    def test_bare_git_rejects_preexisting_worktree_config(self):
        future = self.tmp / "future"
        future.mkdir()
        config = future / "config.worktree"
        config.write_text("[core]\n\tpager = cat\n")
        self.git_init(future, "--bare")
        subprocess.run(["git", "-C", str(future), "config", "extensions.worktreeConfig", "true"], check=True)
        self.assert_code(f"git -C {future} rev-parse --is-bare-repository", "NONE")
        config.write_text("[diff]\n\texternal = /tmp/driver\n")
        effective = subprocess.check_output(["git", "-C", str(future), "config", "--get", "diff.external"], text=True)
        self.assertEqual(effective.strip(), "/tmp/driver")
        self.assert_code(f"git -C {future} diff HEAD^ HEAD", "HOOK_BYPASS")

    def test_bare_git_rejects_preexisting_common_config(self):
        gitdir = self.tmp / "metadata"
        gitdir.mkdir()
        (gitdir / "HEAD").write_text("ref: refs/heads/main\n")
        (gitdir / "commondir").write_text("../bare\n")
        with (self.bare / "config").open("a") as f:
            f.write("[diff]\n\texternal = /tmp/driver\n")
        effective = subprocess.check_output(["git", "-C", str(gitdir), "config", "--get", "diff.external"], text=True)
        self.assertEqual(effective.strip(), "/tmp/driver")
        self.assert_code(f"git -C {gitdir} diff HEAD^ HEAD", "HOOK_BYPASS")

    def test_bare_flag_uses_cwd_at_flag_position(self):
        self.git_init(self.bare)
        with (self.bare / "config").open("a") as config:
            config.write("[diff]\n\texternal = /tmp/driver\n")
        self.assert_code(f"git -C {self.bare} diff HEAD^ HEAD", "NONE")
        self.assert_code(f"git -C {self.bare} --bare diff HEAD^ HEAD", "HOOK_BYPASS")
        self.assert_code(f"git --bare -C {self.bare} diff HEAD^ HEAD", "NONE")

    def test_bare_git_objects_as_executable_file(self):
        """Review #435 R1 🔴: git nhận Git dir khi `objects` chỉ cần `access(X_OK)` — tệp thường có bit chạy cũng qua."""
        fake = self.tmp / "fake"
        (fake / "refs").mkdir(parents=True)
        (fake / "HEAD").write_text("ref: refs/heads/main\n")
        (fake / "objects").write_text("")
        (fake / "objects").chmod(0o755)
        bare = subprocess.run(
            ["git", "-C", str(fake), "rev-parse", "--is-bare-repository"], capture_output=True, text=True
        )
        self.assertEqual(bare.stdout.strip(), "true")
        self.assert_code(f"printf '[core]\\n\\tsshCommand = touch /tmp/pwn\\n' > {fake / 'config'}", "HOOK_BYPASS")
        self.assert_code(f"printf 'exit 0' > {fake / 'hooks' / 'pre-push'}", "HOOK_BYPASS")
        (fake / "config").write_text("[diff]\n\texternal = /tmp/driver\n")
        self.assert_code(f"git -C {fake} diff HEAD^ HEAD", "HOOK_BYPASS")

    def test_bare_git_alternate_object_store(self):
        store = self.tmp / "store"
        (self.bare / "objects").rename(store)
        with (self.bare / "config").open("a") as f:
            f.write("[diff]\n\texternal = /tmp/driver\n")
        self.assert_code(f"GIT_OBJECT_DIRECTORY={store} git -C {self.bare} diff HEAD^ HEAD", "BUDGET")
        self.assert_code(f"export GIT_OBJECT_DIRECTORY={store}; git -C {self.bare} diff HEAD^ HEAD", "BUDGET")


class ReviewDebt435Test(unittest.TestCase):
    """T-3670: nợ review #435 — AUD-SEC-449 (đầu đọc/ghi repo trần lọt), 450 (repo cha), 452 (chặn oan)."""

    git_init = GitMetadataTest.git_init
    policy = GitMetadataTest.policy
    assert_code = GitMetadataTest.assert_code

    def setUp(self):
        GitMetadataTest.setUp(self)
        with (self.bare / "config").open("a") as f:
            f.write("[core]\n\tsshCommand = touch /tmp/pwn\n")

    def test_449_cd_back_resolves_to_known_dir(self):
        """`cd -`/`cd -- -` là thư mục không biết (None, D-106) — AUD-SEC-466 (T-3672) bỏ việc tự theo dõi OLDPWD của
        T-3670: bash đổi OLDPWD qua `OLDPWD=X cd -`, `PWD=X`, `false && cd -`; phía đọc thử mọi thư mục đã biết."""
        a, b = str(self.bare), str(self.tmp)
        cmds = guard._commands_with_cwd(guard.tokenize(f"cd {a}; cd {b}; cd - && git ls-remote"), str(self.root))
        self.assertEqual([h for _, h in cmds], [a, b, None, None])
        cmds = guard._commands_with_cwd(guard.tokenize(f"cd {a}; cd -- -; pwd"), str(self.root))
        self.assertEqual([h for _, h in cmds], [a, None, None])  # không phải `<cwd>/-`
        for cmd in (
            f"cd {a}; cd {self.tmp / 'nope'}; cd -; pwd",  # cd hỏng giữ OLDPWD cũ → không đoán
            f"cd {a} | cat; cd -; pwd",  # cd trong ống chạy ở shell con
            f"(cd {a}; cd {b}); cd -; pwd",
            f"cd {a}; OLDPWD={b}; cd -; pwd",
            f'cd {a}; cd "$X"; cd -; pwd',
            "cd -; pwd",
        ):
            self.assertIsNone(guard._commands_with_cwd(guard.tokenize(cmd), str(self.root))[-1][1], cmd)

    def test_449_bare_config_read_with_cd_back_or_unknown_dir(self):
        for cmd in (
            f"cd {self.bare}; cd {self.tmp}; cd - && git ls-remote origin",
            f"cd {self.bare}; cd {self.tmp}; cd -- - && git ls-remote origin",
            f'cd {self.bare}; cd "$X" && git ls-remote origin',  # thư mục không biết: thử mọi thư mục đã biết
            f'cd {self.bare}; cd {self.tmp}; git -C "$X" ls-remote origin',
            f"cd {self.bare}; cd {self.tmp}; cd - && sh -c 'git ls-remote origin'",
            f'cd {self.bare}; cd "$X" && sh -c "git ls-remote origin"',
        ):
            self.assert_code(cmd, "HOOK_BYPASS")
        for cmd in ('cd "$X" && git status', 'git -C "$X" status', "cd - && git status", "popd; git log -1"):
            self.assert_code(cmd, "NONE")  # gốc dự án có `.git`: không chặn oan
        # D-347: `cd …;` ngoài tiền tố `&&` → hợp mọi đích, repo trần là một ứng viên (chặt hơn T-3672)
        self.assert_code(f"cd {self.bare}; cd {self.root}; cd {self.tmp} && git status", "HOOK_BYPASS")
        self.assert_code(f"cd {self.root} && cd {self.tmp} && git status", "NONE")

    def test_449_pending_bare_into_nested_shell(self):
        future = self.tmp / "future"
        for cmd in (
            f"git init --bare {future} && sh -c 'printf x > {future}/config'",
            f"git init --bare {future} && bash -c 'printf x > {future}/hooks/pre-commit'",
            f"git init --bare {future} && bash -c \"sh -c 'printf x >> {future}/config'\"",
            f"git clone --mirror {self.root} {future} && sh -c 'printf x > {future}/config'",
        ):
            self.assert_code(cmd, "HOOK_BYPASS")
        self.assert_code(f"git init --bare {future} && sh -c 'cat {future}/config'", "NONE")

    def test_449_writer_into_git_dir_directory(self):
        bare = self.bare
        for cmd in (
            f"cp f {bare}/",
            f"cp f {bare}",
            f"cp -r d/. {bare}",
            f"tar -xf a.tar -C {bare}",
            f"rsync -a d/ {bare}/",
            f"unzip a.zip -d {bare}",
            f"mv f {bare}/",
            f"cd {bare} && cp f .",
        ):
            self.assert_code(cmd, "HOOK_BYPASS")
        for cmd in (f"cp f {self.tmp}/", f"tar -xf a.tar -C {self.tmp}", f"cp f {bare}/objects/", "cp f ."):
            self.assert_code(cmd, "NONE")

    def test_450_project_inside_parent_repo_hardlink(self):
        """Dự án `mono/apps/web` (gốc dự án), `.git` ở `mono/`: link cứng tới hook/config của repo cha bị chặn."""
        for separate in (False, True):
            with self.subTest(separate=separate):
                mono = self.tmp / f"mono{int(separate)}"
                meta = self.tmp / f"meta{int(separate)}"
                self.git_init(mono, *([f"--separate-git-dir={meta}"] if separate else []))
                gitdir = meta if separate else mono / ".git"
                web = mono / "apps" / "web"
                web.mkdir(parents=True)
                (gitdir / "hooks" / "pre-commit").write_text("#!/bin/sh\nexit 1\n")
                os.link(gitdir / "hooks" / "pre-commit", web / "hk")
                os.link(gitdir / "config", web / "cfglink")
                (web / "plain").write_text("x")
                os.link(web / "plain", web / "plain2")
                env = {"CLAUDE_PROJECT_DIR": str(web), "XT_GUARD_POLICY": "", "XT_GUARD_PHASE": "harden"}
                with patch.dict(os.environ, env):
                    for cmd in ("printf 'exit 0' > hk", f"printf 'exit 0' > {web / 'hk'}", "printf x >> cfglink"):
                        code = guard.apply_policy(guard.bash_decision(cmd, str(web)))["code"]
                        self.assertEqual(code, "HOOK_BYPASS", cmd)
                    self.assertEqual(
                        guard.apply_policy(guard.bash_decision("printf x > plain2", str(web)))["code"], "NONE"
                    )
                    for name in ("hk", "cfglink"):
                        self.assertEqual(guard.edit_decision(str(web / name), str(web), {"content": "x"})[0], "deny")
                    self.assertEqual(guard.edit_decision(str(web / "plain2"), str(web), {"content": "x"})[0], "")

    def test_450_project_dotgit_none_up_to_root(self):
        """Không có `.git` nào từ gốc dự án lên `/` → giữ `$ROOT/.git` như trước (nhánh cuối của `_project_dotgit`)."""
        with patch.object(guard.os.path, "lexists", return_value=False):
            self.assertEqual(guard._project_dotgit(str(self.root)), os.path.join(str(self.root), ".git"))

    def test_449_bare_created_unknown_place(self):
        """Tạo repo trần mà không biết chắc chỗ (`GIT_DIR`, `--git-dir`, thư mục chạy không biết) → '' (khớp mọi đuôi
        metadata như #435), không phải None."""
        for argv in (
            ["GIT_DIR=x", "git", "init", "--bare", "y"],
            ["git", "--git-dir=x", "init", "--bare", "y"],
        ):
            with self.subTest(argv=argv):
                self.assertEqual(guard._bare_git_created(argv, str(self.root)), "")
        self.assertEqual(guard._bare_git_created(["git", "init", "--bare", "y"], None), "")
        self.assertIsNone(guard._bare_git_created(["git", "status"], str(self.root)))
        # `--` kết thúc tuỳ chọn: thư mục sau `--` vẫn là chỗ tạo repo trần
        made = guard._bare_git_created(["git", "init", "--bare", "--", "y"], str(self.root))
        self.assertEqual(os.path.normpath(made or ""), os.path.join(str(self.root), "y"))
        self.assert_code(
            f"git init --bare -- {self.tmp / 'z'} && printf x > {self.tmp / 'z' / 'config'}", "HOOK_BYPASS"
        )

    def test_452_own_git_dir_trailing_slash(self):
        for cmd in (
            f"GIT_DIR={self.root}/.git/ git status",
            "GIT_DIR=.git/ git status",
            f"git --git-dir={self.root}//.git status",
        ):
            self.assert_code(cmd, "NONE")
        for cmd in (
            f"GIT_DIR={self.root}/x/../.git git status",  # `..` không chuẩn hoá theo chữ (symlink)
            f"GIT_DIR={self.bare}/ git status",
            f"GIT_COMMON_DIR={self.bare}/ git status",
        ):
            self.assert_code(cmd, "BUDGET")

    def test_452_config_file_on_bare_like_dash_c(self):
        config = self.bare / "config"
        for form in (f"--file {config}", f"-f {config}", f"--file={config}"):
            self.assert_code(f"git config {form} user.name T", "NONE")
            self.assert_code(f"git -C {self.bare} config user.name T", "NONE")
            for key in ("core.sshCommand x", "core.hooksPath /dev/null", "include.path /tmp/x", "alias.x '!sh'"):
                self.assert_code(f"git config {form} {key}", "HOOK_BYPASS")
            self.assert_code(f"git config {form} --add core.fsmonitor x", "HOOK_BYPASS")
        for cmd in (
            f"git config --file {config} --edit",
            f"git config --file {config} -e",
            f"git config --file {config} edit",
            f"git config --file {self.bare / 'hooks' / 'pre-commit'} user.name T",
            f"git config --file {self.bare / 'commondir'} user.name T",
            "git config --file .git/config user.name T",  # `.git` của dự án: luật cũ giữ nguyên
        ):
            self.assert_code(cmd, "HOOK_BYPASS")

    def test_452_pending_bare_matches_created_dir(self):
        future = self.tmp / "future"
        (self.root / "src").mkdir()
        for cmd in (
            f"git init --bare {future} && printf x > src/config",
            f"git init --bare {future} && printf x > {self.tmp / 'other'}/config",
            f"git init --bare -b main {future} && printf x > src/hooks/pre-commit",
            f"git clone --mirror {self.root} {future} && printf x > src/config",
        ):
            self.assert_code(cmd, "NONE")
        for cmd in (
            f"git init --bare {future} && printf x > {future}/config",
            f"git init --bare {future} && cd {future} && printf x > config",
            f"git init --bare {future} && cd {self.tmp} && printf x > future/hooks/pre-commit",
            f"git -C {self.tmp} init --bare future && printf x > {future}/config",
            f"cd {self.tmp} && git init --bare && printf x > config",
            f"git clone --bare {self.root} && printf x > src/config",  # thư mục mặc định: không đoán
            "git init --bare $F && printf x > src/config",
            f"git init --bare --initial-br main {future} && printf x > src/config",  # viết tắt: cờ lạ
            f"git init --bare {future} && ln -s {future} l && printf x > l/config",
            f"git init --bare {future} && sh -c 'printf x > src/config'",
            f'git init --bare {future} && cd "$X" && printf x > future/config',
            f"GIT_DIR={future} git init --bare && printf x > src/config",
        ):
            self.assert_code(cmd, "HOOK_BYPASS")


class Preexisting3671Test(unittest.TestCase):
    """T-3671: sáu lỗ có từ trước T-3670 phát hiện (AUD-SEC-453…458) — mỗi ca đỏ ở 5657a14."""

    git_init = GitMetadataTest.git_init
    policy = GitMetadataTest.policy
    assert_code = GitMetadataTest.assert_code

    def setUp(self):
        GitMetadataTest.setUp(self)
        (self.root / "src").mkdir()
        self.fut = self.tmp / "fut"

    def test_453_bare_created_in_nested_shell_reported_outward(self):
        fut = self.fut
        for cmd in (
            f"sh -c 'git init --bare {fut}' && printf x > {fut}/config",
            "sh -c 'git init --bare fut' && printf x > fut/config",
            f'bash -c "git init --bare {fut}"; printf x > {fut}/hooks/pre-commit',
            f"sh -c 'git clone --mirror {self.root} {fut}' && printf x >> {fut}/config",
            f"sh -c 'git init --bare {fut}' && sh -c 'printf x > {fut}/config'",
            f"bash -c \"sh -c 'git init --bare {fut}'\" && printf x > {fut}/config",
        ):
            self.assert_code(cmd, "HOOK_BYPASS")
        for cmd in (
            f"sh -c 'git init --bare {fut}' && printf x > src/notes",
            f"sh -c 'git init --bare {fut}' && cat {fut}/config",
            f"sh -c 'git init {fut}' && git status",
        ):
            self.assert_code(cmd, "NONE")

    def test_454_fake_git_dir_built_in_same_command(self):
        d = self.tmp / "d"
        for cmd in (
            "mkdir -p d/objects && echo 'ref: refs/heads/main' > d/HEAD && printf '[core]\\n\\tsshCommand = x\\n' > d/config",
            f"mkdir -p {d}/objects && printf x > {d}/hooks/pre-commit",
            "echo 'ref: refs/heads/main' > d/HEAD && printf x > d/config",
            "printf x > d/config && echo 'ref: refs/heads/main' > d/HEAD",  # thứ tự đảo vẫn thành Git dir
            "mkdir -p d/objects/pack; printf x >> d/config.worktree",
            "echo x | tee d/HEAD d/config",
            "mkdir -p d/objects && sh -c 'printf x > d/config'",
        ):
            self.assert_code(cmd, "HOOK_BYPASS")
        for cmd in (
            "mkdir -p d/objects && printf x > other/config",
            "echo x > d/HEAD.txt && printf x > d/config",
            "mkdir -p d/objects && printf x > d/notes",
            "mkdir -p build/objects && touch build/out.o",
        ):
            self.assert_code(cmd, "NONE")

    def test_455_config_edit_any_repo(self):
        bare = self.bare
        for cmd in (
            f"git -C {bare} config --edit",
            f"git -C {bare} config -e",
            f"git -C {bare} config --ed",
            f"cd {bare} && git config --edit",
            f"GIT_EDITOR=true git -C {bare} config edit",
            "git config --edit",
            "git config -e",
            "git config --global --edit",
            "git config --local -e",
        ):
            self.assert_code(cmd, "HOOK_BYPASS")
        for cmd in (
            f"git -C {bare} config user.name T",
            f"git -C {bare} config --get core.bare",
            "git config --get core.editor",
            "git config -l",
            "git config core.editor vim",
        ):
            self.assert_code(cmd, "NONE")

    def test_456_config_section_ops_on_protected_keys(self):
        bare = self.bare
        for cmd in (
            "git config --remove-section core",
            "git config --remove-sec core",
            "git config --remove-section Core",
            "git config --global --remove-section core",
            f"git -C {bare} config --remove-section core",
            f"git config --file {bare}/config --remove-section core",
            f"cd {bare} && git config --remove-section core",
            "git config remove-section core",
            "git config --remove-section include",
            "git config --remove-section 'includeIf.gitdir:/x/'",
            "git config --remove-section alias",
            'git config --remove-section "$S"',
            "git config --rename-section core x",
            "git config rename-section core x",
            "git config --rename-section x core",
            "git config --rename-section x alias",
            "git config --rename-section x filter.lfs",  # khoá chạy lệnh theo mẫu `*.clean`/`*.smudge`
            "git config --rename-section x credential",
            "git config --unset include.path",
            "git config --unset-all includeIf.gitdir:/x/.path",
            # luật cũ (đã chặn ở base) giữ nguyên
            "git config --unset core.hooksPath",
            "git config --unset-all core.hooksPath",
            "git config --replace-all core.hooksPath /dev/null",
            "git config --replace-all core.sshCommand x",
        ):
            self.assert_code(cmd, "HOOK_BYPASS")
        for cmd in (
            "git config --remove-section user",
            "git config --remove-section submodule.lib",
            "git config --global --remove-section user",
            "git config --rename-section user author",
            "git config --unset user.email",
            "git config --unset core.fsmonitor",  # gỡ khoá chạy lệnh không bỏ hook
        ):
            self.assert_code(cmd, "NONE")

    def test_457_failed_cd_then_semicolon_is_unknown_dir(self):
        root = str(self.root)

        # T-3672 thay nhánh `cd` hỏng (None) bằng tập ứng viên: thư mục cũ thay cho "không biết"
        def dirs(cmd):
            return [list(c) for _, c in guard._commands_with_cwds(guard.tokenize(cmd), root)]

        def first(cmd):  # nhánh cd thành công
            return [h for _, h in guard._commands_with_cwd(guard.tokenize(cmd), root)]

        # D-347 (T-3674): ngoài tiền tố `cd … &&` là hợp mọi đích — chặt hơn T-3672 (`cd` chắc thành công vẫn giữ cũ)
        self.assertEqual(dirs("cd /khong-co; echo x > a"), [["/khong-co", root], ["/khong-co", root]])
        self.assertEqual(first("cd /khong-co; echo x > a"), ["/khong-co", "/khong-co"])
        self.assertEqual(dirs("cd /khong-co && echo x > a"), [["/khong-co"], ["/khong-co"]])
        self.assertEqual(dirs("cd /khong-co && (echo a; echo b)"), [["/khong-co"]] * 2 + [["/khong-co", root]])
        tmp = str(self.tmp)
        self.assertEqual(dirs(f"cd {tmp}; echo x > a"), [[tmp, root], [tmp, root]])
        self.assertEqual(dirs("(cd /khong-co); echo x > a"), [["/khong-co", root], [root]])  # subshell: bỏ khi ra
        for cmd in (
            "cd /khong-co; echo x > .autopilot/state.json",
            "cd /khong-co\necho x > .autopilot/state.json",
            "cd khong-co; echo x > .autopilot/state.json",
            "cd /khong-co || echo x > .autopilot/state.json",
            "cd /khong-co && true; echo x > .autopilot/state.json",
            "pushd /khong-co; echo x > .autopilot/state.json",
            "mkdir .autopilot; cd .autopilot; echo x > state.json",  # nhánh cd thành công vẫn xét (thư mục tạo trước)
            f"cd {self.tmp}; echo x > .autopilot/state.json",  # D-347: thư mục đầu là ứng viên (trước: NONE)
        ):
            self.assert_code(cmd, "EVIDENCE_HANDWRITE")
        self.assert_code("cd /khong-co; printf x > .git/hooks/pre-commit", "HOOK_BYPASS")
        self.assert_code("cd /khong-co; echo x > .env", "SECRET_WRITE")  # luật cũ (tên `.env` ở mọi nơi)
        at_root = self.policy("echo x > xt.yaml")
        self.assertNotEqual(at_root["code"], "NONE")
        self.assert_code("cd /khong-co; echo x > xt.yaml", at_root["code"])
        for cmd in (
            "cd /khong-co && echo x > .autopilot/state.json",  # cd hỏng thì vế sau không chạy
            "(cd /khong-co); echo x > a.txt",
            "cd src; echo x > a.txt",
            "cd /khong-co; git status",
            "cd /khong-co; git log -1",
            "cd src; git diff",
            "git status; git log -1; git diff",
            "git commit -m x",
            "git push origin feature",
        ):
            self.assert_code(cmd, "NONE")

    def test_458_extract_into_current_git_dir(self):
        bare = self.bare
        for cmd in (
            f"cd {bare} && tar -xf a.tar",
            f"cd {bare}; tar xf a.tar",
            f"cd {bare} && gtar -xzf a.tgz",
            f"cd {bare} && unzip a.zip",
            "cd .git && tar -xf a.tar",
            "cd .git/hooks && tar -xf a.tar",
            "cd .git && unzip -o a.zip",
        ):
            self.assert_code(cmd, "HOOK_BYPASS")
        for cmd in (
            "tar -xf a.tar",
            "cd src && tar -xf a.tar",
            f"cd {self.tmp} && tar -xf a.tar",
            f"cd {bare} && tar -tf a.tar",
            f"cd {bare} && tar -cf /tmp/a.tar .",
            f"cd {bare} && tar -xOf a.tar",
            f"cd {bare} && tar -xf a.tar -C {self.root / 'src'}",
            f"cd {bare} && unzip -l a.zip",
            f"cd {bare} && unzip a.zip -d {self.root / 'src'}",
            "unzip a.zip",
        ):
            self.assert_code(cmd, "NONE")


class CwdCandidates3672Test(unittest.TestCase):
    """T-3672 (review #438): thư mục chạy là TẬP ỨNG VIÊN như bash — `cd` có thể hỏng thì lệnh sau chạy ở thư mục cũ
    lẫn đích; `cd` trong ống/nền không dời thư mục; khoá git chạy lệnh; cờ giải nén. Mỗi ca chặn đỏ ở a27cf57."""

    git_init = GitMetadataTest.git_init
    policy = GitMetadataTest.policy
    assert_code = GitMetadataTest.assert_code

    def setUp(self):
        GitMetadataTest.setUp(self)
        (self.root / "src").mkdir()
        self.gone = self.root / "w"  # có lúc kiểm, trong dự án (xoá đệ quy ngoài dự án bị chặn riêng)
        self.gone.mkdir()

    def cands(self, cmd):
        return [list(c) for _, c in guard._commands_with_cwds(guard.tokenize(cmd), str(self.root))]

    def test_459_cd_may_fail_keeps_old_dir(self):
        d, ev = self.gone, "echo x > .autopilot/state.json"
        for cmd in (
            f"cd /khong-co/..; {ev}",  # bash kiểm `/khong-co` trước `..`: hỏng, PWD giữ nguyên
            f"cd khong-co/..; {ev}",
            f"! cd /khong-co && {ev}",  # `!` đảo: vế sau chạy khi `cd` hỏng
            f"if ! cd /khong-co; then {ev}; fi",
            f"rm -rf {d}; cd {d}; {ev}",  # đích có lúc kiểm, bị xoá trước `cd`
            f"rmdir {d}; cd {d}; {ev}",
            f"mv {d} {self.tmp}/e; cd {d}; {ev}",
            f"unlink {d}; cd {d}; {ev}",
            f"find {d} -delete; cd {d}; {ev}",
            f"rm -rf w; cd {d}; {ev}",
            f"rm -rf ./w/ && cd w; {ev}",
            f"rm -f $X; cd {d}; {ev}",
            f"cd /khong-co && cd {d}; {ev}",
            f"cd /khong-co || true; {ev}",
            f"cd /khong-co && true || {ev}",
            'cd /khong-co; python3 -c \'open(".autopilot/state.json","w")\'',
            'cd /khong-co | true; cd /khong-co; true | python3 -c \'open(".autopilot/state.json","w")\'',
        ):
            self.assert_code(cmd, "EVIDENCE_HANDWRITE")
        for cmd in (
            "shopt -s cdable_vars; cd khong-co; printf x > config",  # `cd` hỏng → `cd "$khong_co"`: không biết
            "cd /khong-co; cd .git; printf x > config",
        ):
            self.assert_code(cmd, "HOOK_BYPASS")
        root, tmp = str(self.root), str(self.tmp)
        k = "/khong-co"
        self.assertEqual(self.cands("cd /khong-co; echo")[1], [k, root])
        self.assertEqual(self.cands("cd /khong-co && echo")[1], [k])
        # D-347 (T-3674): bỏ miễn `|| exit|return` (AUD-SEC-480); ngoài tiền tố `&&` là hợp mọi đích (chặt hơn)
        self.assertEqual(self.cands("cd /khong-co || exit 1; echo")[2], [k, root])
        self.assertEqual(self.cands("cd /khong-co || return; echo")[2], [k, root])
        self.assertEqual(self.cands(f"cd {tmp}; echo")[1], [tmp, root])
        self.assertEqual(self.cands(f"cd {tmp} && echo")[1], [tmp])  # tiền tố chính xác, chắc thành công
        self.assertEqual(self.cands("cd /khong-co && (echo a; echo b); echo c")[1:], [[k], [k, root], [k, root]])
        self.assertEqual(self.cands("{ cd /khong-co && echo a\n}; echo b")[1:], [[k, root]] * 3)
        self.assertEqual(self.cands("cd $X; echo")[1], [None, root])
        self.assertEqual(self.cands(f"cd {tmp}; cd /khong-co; cd -; echo")[3], [None, root, tmp, k])
        self.assertEqual(self.cands(f"cd {tmp}; cd {root}/src; cd -; echo")[3], [None, root, tmp, f"{root}/src"])
        # `)` lẻ: không biết như cũ, cộng các thư mục biết (gỡ "chỉ None" — ứng viên là thư mục biết, AUD-SEC-463)
        self.assertEqual(self.cands("case x in a) cd src;; esac; echo")[-1], [None, root, f"{root}/src"])
        # chặn oan của nhánh `cd` hỏng T-3671 (AUD-SEC-463) — đích được tạo trước trong lệnh, hay `|| exit`
        for cmd in (
            "mkdir -p out; cd out; tar -xf ../a.tar",
            f"mkdir -p {self.tmp}/w; cd {self.tmp}/w; printf x > config",
            "mkdir -p dist; cd dist; unzip ../a.zip",
            "cd /khong-co || exit 1; printf x > config",
            "cd /khong-co && echo x > .autopilot/state.json",
            "git status",
            "cd src && git commit -m x",
            "mkdir build; cd build; cmake ..; make",
            f"cd {d} && echo x > .autopilot/state.json",
            "cd /khong-co; git status",
        ):
            self.assert_code(cmd, "NONE")
        for cmd in (  # D-347: thư mục đầu (gốc) là ứng viên ngoài tiền tố `&&` — trước T-3674: NONE
            f"cd {d}; echo x > .autopilot/state.json",
            f"rm -rf {d}/x; cd {d}; echo x > .autopilot/state.json",
            f"cd {d} || true; echo x > .autopilot/state.json",
        ):
            self.assert_code(cmd, "EVIDENCE_HANDWRITE")

    def test_460_cd_in_pipe_or_background_does_not_move(self):
        tmp, ev = self.tmp, "echo x > .autopilot/state.json"
        for cmd in (
            f"cd {tmp} | true; {ev}",
            f"cd {tmp} |& true; {ev}",
            f"true | cd {tmp}; {ev}",
            f"cd {tmp} & {ev}",
            f"cd {tmp} &\n{ev}",
            f"cd {tmp} && true & {ev}",
            f"{{ cd {tmp}; }} | cat; {ev}",
            f"true | {{ true; cd {tmp}; }}; {ev}",
            f"(cd {tmp}) | cat; {ev}",
            f"true; {{ cd {tmp}; }} & {ev}",
            f'cd {tmp} | true; python3 -c \'open(".autopilot/state.json","w")\'',
        ):
            self.assert_code(cmd, "EVIDENCE_HANDWRITE")
        root = str(self.root)
        self.assertEqual(self.cands(f"cd {tmp} | true; echo")[2], [root, str(tmp)])  # D-347: hợp (trước: [root])
        self.assertEqual(self.cands(f"cd {tmp} && echo a | cat; echo")[3], [str(tmp)])
        for cmd in (
            f"cd {tmp} && echo x | cat > .autopilot/state.json",  # `&&` thấp hơn `|`: ống chạy sau `cd`
            f"cd {tmp} && {ev} | cat",
            f"cd {tmp} && {ev} &",
            f"cd {tmp} | true; echo x > a.txt",
        ):
            self.assert_code(cmd, "NONE")
        for cmd in (f"cd {tmp}; {ev} | cat", f"{{ cd {tmp}; }}; {ev}"):  # D-347: gốc là ứng viên (trước: NONE)
            self.assert_code(cmd, "EVIDENCE_HANDWRITE")

    def test_461_git_exec_keys(self):
        for cmd in (
            "git config gc.recentObjectsHook 'sh -c x'",
            "git config interactive.diffFilter 'sh -c x'",
            "git config imap.tunnel 'sh -c x'",
            "git config instaweb.httpd 'sh -c x'",
            "git -c interactive.diffFilter='sh -c x' add -p",
            "git config --rename-section x gc",
            "git config rename-section x GC",
        ):
            self.assert_code(cmd, "HOOK_BYPASS")
        for cmd in (
            "git config gc.auto 0",
            "git config --rename-section x pack",
            "git config --get imap.tunnel",
        ):
            self.assert_code(cmd, "NONE")

    def test_462_extract_flags_and_implicit_dest(self):
        bare, src = self.bare, self.root / "src"
        for cmd in (
            f"tar -xC {bare} -f a.tar",
            f"cd {bare} && tar -xC . -f a.tar",
            f"cd {bare} && tar -xfO a.tar",  # `O` là giá trị của `f` (tên archive), không phải ra stdout
            f"cd {bare} && tar -x -f -O",
            f"cd {bare} && tar xfC a.tar .",  # kiểu cũ: giá trị theo thứ tự chữ
            f"cd {bare} && unzip -P -d a.zip",  # `-d` là mật khẩu
            f"cd {bare} && unzip -Pc a.zip",
            f"cd {bare} && 7z x a.7z",
            f"7z x a.7z -o{bare}",
            f"cd {bare} && cpio -i < a.cpio",
            f"cd {bare} && cpio -idv < a.cpio",
            f"cd {bare} && jar xf a.jar",
            f"cd {bare} && pax -r < a.pax",
            f"cd {bare} && pax -rv -f a.pax",
            f"pax -r -w x {bare}",
            "cd .git && 7z x a.7z",
            "cd .git && cpio -i < a.cpio",
        ):
            self.assert_code(cmd, "HOOK_BYPASS")
        for cmd in (
            f"cd {bare} && tar -xOf a.tar",
            f"cd {bare} && tar -x --to-stdout -f a.tar",
            f"cd {bare} && tar xfO a.tar",  # kiểu cũ: `f` ăn `a.tar`, `O` là ra stdout
            f"cd {bare} && tar -x --to-command cat -f a.tar",
            f"cd {bare} && tar -xf a.tar -C {src}",
            f"cd {bare} && tar -xC {src} -f a.tar",
            f"cd {bare} && unzip -l a.zip",
            f"cd {bare} && unzip -qd {src} a.zip",
            f"cd {bare} && 7z l a.7z",
            f"cd {bare} && 7z x a.7z -o{src}",
            f"cd {bare} && cpio -it < a.cpio",
            f"cd {bare} && jar tf a.jar",
            f"cd {bare} && pax < a.pax",
            f"cd {bare} && pax -w -f /tmp/a.pax .",
            "tar -xf a.tar",
            "pax -r < a.pax",
            "7z x a.7z",
            f"cd {bare} && ar t a.a",
            "ar x a.a",
            f"cd {bare} && python3 -m tarfile -l a.tar",
        ):
            self.assert_code(cmd, "NONE")

    def test_462_more_extractors(self):
        bare = self.bare
        for cmd in (
            f"cd {bare} && cpio -idm < a.cpio",
            f"cd {bare} && python3 -m tarfile -e a.tar",
            f"python3 -m tarfile -e a.tar {bare}",
            f"python3 -m zipfile -e a.zip {bare}",
            f"cd {bare} && ar x a.a",
            f"cd {bare} && ar -xv a.a",
            f"ar x a.a --output {bare}",
            f"cd {bare} && bsdtar -xf a.tar",
            f"bsdtar -xC {bare} -f a.tar",
            "cd .git/hooks && 7z x a.7z",
        ):
            self.assert_code(cmd, "HOOK_BYPASS")

    def test_466_cd_back_is_unknown_dir(self):
        """Hồi quy của T-3670 (9c03257 chặn, a27cf57 qua): OLDPWD đổi theo cách guard không theo dõi."""
        a, b, root = self.tmp / "a", self.tmp / "b", self.root
        a.mkdir()
        b.mkdir()
        (root / "docs" / "autopilot").mkdir(parents=True)
        for cmd, code in (
            (f"cd {a} && cd {b} && OLDPWD={root} cd - && echo x > .autopilot/state.json", "EVIDENCE_HANDWRITE"),
            (f"cd {a}; PWD={root}; cd {b}; cd -; echo '{{}}' > docs/autopilot/STAGE.json", "EVIDENCE_HANDWRITE"),
            (f"cd {a}; false && cd {b}; cd -; echo x > .autopilot/state.json", "EVIDENCE_HANDWRITE"),
            (f"cd {a}; cd {b}; cd -- -; echo x > .autopilot/state.json", "EVIDENCE_HANDWRITE"),
        ):
            self.assert_code(cmd, code)
        self.assert_code(f"cd {a} && cd {b} && cd - && git status", "NONE")

    def test_467_pending_bare_physical_path(self):
        """Hồi quy của T-3670: đường khác chữ cùng thư mục vật lý (symlink rồi `..`, hoa/thường)."""
        t = self.tmp
        (t / "deep" / "sub").mkdir(parents=True)
        (t / "lnk").symlink_to(t / "deep" / "sub")
        for cmd in (
            f"git init --bare {t}/deep/F && printf x > {t}/lnk/../F/config",
            f"git -C {t}/lnk init --bare ../F && printf x > {t}/deep/F/config",
            f"git init --bare {t}/Fq && printf x > {t}/fq/config",
            f"git init --bare {t}/deep/F && printf x > {t}/nope/../deep/F/hooks/pre-commit",
            f"mkdir -p {t}/lnk/../G/objects && printf x > {t}/deep/G/config",
            f"git -C {t}/lnk init --bare ../H; printf x > {t}/deep/H/config",
            f"git init --bare {t}/nope/../X && printf x > {t}/X/config",  # `..` sau phần chưa có: không chắc
        ):
            self.assert_code(cmd, "HOOK_BYPASS")
        for cmd in (
            f"git init --bare {t}/deep/F && printf x > {t}/other/config",
            f"git init --bare {t}/deep/F && cat {t}/lnk/../F/config",
            f"git init --bare {t}/deep/F && printf x > {t}/deep/notes",
        ):
            self.assert_code(cmd, "NONE")

    def test_review438_paths_and_files(self):
        t, bare = self.tmp, self.bare
        (t / "deep" / "sub").mkdir(parents=True)
        (t / "lnk").symlink_to(t / "deep" / "sub")
        with (bare / "config").open("a") as f:
            f.write("[core]\n\tsshCommand = touch /tmp/pwn\n")
        at_git = self.policy("git config --file .git/config user.name T")["code"]
        for cmd, code in (
            (f"cp f {t}/lnk/../../bare/", "HOOK_BYPASS"),  # `_git_dir_target` theo realpath
            (f'git -C "$X" -C {bare} ls-remote origin', "HOOK_BYPASS"),  # `-C` tuyệt đối đặt lại thư mục
            (f"git config --file {bare}/config --file .git/config user.name T", at_git),  # `--file` cuối thắng
        ):
            self.assert_code(cmd, code)
        self.assertEqual(guard._git_dir(["git", "-C", "$X", "-C", "/abs", "status"], None), "/abs")
        self.assertEqual(guard._git_config_file(["git", "config", "-f", "a", "--file=b", "x.y", "1"]), "b")
        self.assertEqual(guard._git_config_file(["git", "config", "-f"]), "")
        self.assert_code(f"cp f {t}/lnk/../sub/", "NONE")

    def test_464_alias_defined_in_same_command(self):
        for cmd in (
            "git config alias.u 'config --unset core.hooksPath' && git u",
            "git config alias.r 'config --remove-section core' && git r",
            "git config --global alias.u 'config --unset core.hooksPath'; git u",
            "git config alias.u 'config --unset core.hooksPath' && git config alias.v u && git v",
            "git config alias.s '!sh -c x' && git s",
        ):
            self.assert_code(cmd, "HOOK_BYPASS")
        for cmd in (
            "git config alias.st status && git st",
            "git config alias.u 'config --unset core.hooksPath'",  # đặt mà không gọi: thân là lệnh git thường
            "git u; git config alias.u 'config --unset user.name'",
        ):
            self.assertNotEqual(self.policy(cmd)["code"], "HOOK_BYPASS", cmd)

    def test_465_git_dir_built_by_copy(self):
        bare, d = self.bare, self.tmp / "cp"
        for cmd in (
            "cp -r .git d && printf x > d/config",
            f"cp -a {bare} {d} && printf x > {d}/config",
            f"cp -a {bare} {d}; printf x > {d}/bare/hooks/pre-commit",
            "rsync -a .git/ d/ && printf x > d/hooks/pre-commit",
            f"scp -r {bare} {d} && printf x >> {d}/config",
            f"cp -r -t {d} {bare} && printf x > {d}/bare/config",
            'cp -r .git "$D" && printf x > /tmp/elsewhere/config',  # đích là biến: mọi đuôi metadata
        ):
            self.assert_code(cmd, "HOOK_BYPASS")
        for cmd in (
            "cp -r src d && printf x > d/config",  # nguồn không phải Git dir
            "cp -r .git d && printf x > d/notes",
            f"cp -a {bare} {d} && cat {d}/config",
        ):
            self.assert_code(cmd, "NONE")

    def test_449_scp_into_git_dir(self):
        bare = self.bare
        for cmd in (f"scp f {bare}/", f"scp -P 22 f {bare}/hooks/pre-commit", "scp f .git/hooks/pre-commit"):
            self.assert_code(cmd, "HOOK_BYPASS")
        for cmd in (f"scp f host:{bare}/", "scp host:f src/", "scp -i k f src/"):
            self.assertNotEqual(self.policy(cmd)["decision"], "deny", cmd)  # gửi ra máy khác: hỏi-cho-qua như cũ


class OptionParse3673Test(unittest.TestCase):
    """T-3673 (audit delta 2026-11-04): cờ của từng lệnh đọc như getopt/argp/argparse/popt (`_getopt`) — cụm cờ, giá
    trị dính liền, tên dài viết tắt, `--`; đích ghi ngầm của chép/giải nén/tạo archive. Mỗi ca chặn đỏ ở f47c8c9."""

    git_init = GitMetadataTest.git_init
    policy = GitMetadataTest.policy
    assert_code = GitMetadataTest.assert_code

    def setUp(self):
        GitMetadataTest.setUp(self)
        for d in ("src", "dist", "build", ".claude/hooks", ".autopilot", "docs/autopilot"):
            (self.root / d).mkdir(parents=True)

    def assert_codes(self, code, *cmds):
        for cmd in cmds:
            self.assert_code(cmd, code)

    def test_468_cpio_value_letters_are_not_flags(self):
        bare = self.bare
        self.assert_codes(
            "EVIDENCE_HANDWRITE",
            "cd docs/autopilot && cpio -idHtar < /tmp/a.tar",
            "cd docs/autopilot && cpio -idRroot < a.cpio",
            "cd docs/autopilot && cpio -iFat",
            "cd docs/autopilot && cpio -id -H tar < a.tar",  # đối chứng base
        )
        self.assert_codes("HOOK_BYPASS", f"cd {bare} && cpio -idHtar < a.tar", "cd .claude/hooks && cpio -idHtar < a")
        self.assert_codes(
            "NONE", "cpio -it < a.cpio", "cd docs/autopilot && cpio -itv < a.cpio", "cd .claude/hooks && cpio -itHtar"
        )
        self.assertEqual(guard._unpack_dirs("cpio", ["-idHtar"]), ["."])
        self.assertEqual(guard._unpack_dirs("cpio", ["-it"]), [])

    def test_469_copy_target_directory_cluster_attached_abbrev(self):
        self.assert_codes(
            "HOOK_BYPASS",
            "cp -ft .claude/hooks /tmp/guard.py",
            "install -Dt .claude/hooks /tmp/guard.py",
            "ln -sft .claude/hooks /tmp/guard.py",
            "cp --target=.claude/hooks /tmp/guard.py",
            "cp --t .claude/hooks /tmp/guard.py",
            "cp -t.claude/hooks /tmp/guard.py",
            "cp -rt .claude /tmp/evil/hooks",
            "mv --targ .claude/hooks /tmp/guard.py",
            "install -m 755 -t.claude/hooks /tmp/guard.py",
            "cp -ft .git/hooks /tmp/pre-commit",
        )
        self.assert_codes(
            "EVIDENCE_HANDWRITE", "cp -ft .autopilot /tmp/state.json", "cp -ft docs/autopilot /x/STAGE.json"
        )
        self.assert_codes(
            "NONE",
            "cp -ft dist a b",
            "cp -r src dist",
            "cp -St .claude/hooks x",  # `-S` ăn `t`: toán hạng `.claude/hooks` là nguồn, đích là `x`
            "install -m 644 -t dist a",
            "cp --suffix .claude/hooks a b",
        )
        self.assertEqual(guard._copy_targets("cp", ["-ft", "D", "a"]), ["D/a"])
        self.assertEqual(guard._copy_targets("mv", ["--t=D", "a"]), ["D/a", "a"])
        self.assertEqual(guard._removed_targets(["mv", "-ftD", "a", "b"]), ["a", "b"])

    def test_470_copy_dir_into_parent_with_same_name(self):
        root = self.root
        self.assert_codes("HOOK_BYPASS", "cp -r /tmp/evil/.claude .", "cp -r /tmp/evil/.git .", "rsync -a /x/.git ./")
        self.assert_codes("EVIDENCE_HANDWRITE", f"cp -a /tmp/evil/.autopilot {root}/", "cp -r /tmp/evil/docs .")
        self.assert_codes("NONE", "cp -r /tmp/evil/src .", "cp -r src dist", "cp a.txt dist/", "mv build/x .")

    def test_471_tar_members_double_dash_abbrev(self):
        self.assert_codes(
            "HOOK_BYPASS",
            "cd .claude/hooks && tar -xf /tmp/a.tar guard.py -C /tmp",
            "cd .claude/hooks && tar -x --exclude -O -f /tmp/a.tar",
            "cd .claude/hooks && tar -xf /tmp/a.tar -- -O guard.py",
            "cd .claude/hooks && tar -x --exclude=x --strip-components 1 -f /tmp/a.tar",
            "tar --ge -f /tmp/a.tar -C .claude/hooks",
            "tar -x --file=/tmp/a.tar --dir=.claude/hooks",
        )
        self.assert_codes(
            "NONE",
            "tar -xf a.tar",
            "cd .claude/hooks && tar -xOf /tmp/a.tar",
            "cd .claude/hooks && tar -x --to-s -f /tmp/a.tar",
            "cd .claude/hooks && tar -xf /tmp/a.tar -C /tmp guard.py",
            "cd .claude/hooks && tar -tf /tmp/a.tar -- -O",
            "tar -czf build/out.tgz src",
        )
        self.assertEqual(guard._tar_extract_dirs(["-xf", "a", "m", "-C", "d"]), [".", "./d"])
        self.assertEqual(guard._tar_extract_dirs(["-xf", "a", "-C", "d", "m"]), ["./d"])

    def test_472_python_archive_modules_argparse(self):
        self.assert_codes(
            "HOOK_BYPASS",
            "python3 -Im tarfile -e /tmp/a.tar .claude/hooks",
            "python3 -IBm zipfile -e /tmp/a.zip .claude/hooks",
            "python3 -m zipfile --e /tmp/a.zip .claude/hooks",
            "cd .claude/hooks && python3 -m tarfile -ea.tar",
            "cd .git && python3 -m tarfile -e /tmp/a.tar --filter data",
            "python3 -mtarfile -ve /tmp/a.tar .claude/hooks",
        )
        self.assert_codes("EVIDENCE_HANDWRITE", "cd .autopilot && python3 -m tarfile --extract=/tmp/a.tar")
        self.assert_codes(
            "NONE",
            "python3 -m zipfile -l a.zip",
            "python3 -m tarfile -e /tmp/a.tar build",
            "cd .claude/hooks && python3 -m tarfile -l /tmp/a.tar",
            "cd .claude/hooks && python3 -m tarfile -t /tmp/a.tar",
            "python3 -m tarfile -e /tmp/a.tar build --filter data",
            "python3 -c pass -m tarfile -e /tmp/a.tar",
        )

    def test_473_jar_ar_unzip_flags(self):
        self.assert_codes(
            "HOOK_BYPASS",
            "cd .claude/hooks && jar --verbose -x --file /tmp/a.jar",
            "cd .claude/hooks && jar -v -x -f /tmp/a.jar",
            "cd .claude/hooks && ar --target elf64-x86-64 x /tmp/a.a",
            "cd .claude/hooks && ar --plugin /p.so x /tmp/a.a",
            "ar x /tmp/a.a --o=.claude/hooks",
            "ar x /tmp/a.a --outp .claude/hooks",
            "ar -v -x /tmp/a.a --output=.claude/hooks",
            "cd .claude/hooks && unzip -l --l /tmp/a.zip",
            "cd .claude/hooks && unzip -l- -l /tmp/a.zip",
            "cd .claude/hooks && unzip --- -l /tmp/a.zip",
            "cd .claude/hooks && unzip -Ol /tmp/a.zip",
            "cd .claude/hooks && unzip -Il /tmp/a.zip",
        )
        self.assert_codes(
            "NONE",
            "cd .claude/hooks && jar -tf /tmp/a.jar",
            "cd .claude/hooks && jar --list --file /tmp/a.jar",
            "cd .claude/hooks && ar t /tmp/a.a",
            "cd .claude/hooks && ar --target elf64-x86-64 t /tmp/a.a",
            "unzip -l a.zip",
            "cd .claude/hooks && unzip -qql /tmp/a.zip",
            "cd .claude/hooks && unzip -l- /tmp/a.zip",
            "cd .claude/hooks && unzip -O cp437 -l /tmp/a.zip",
        )

    def test_474_options_from_environment(self):
        bare = self.bare
        self.assert_codes(
            "HOOK_BYPASS",
            "TAR_OPTIONS=-C.claude/hooks tar -xf /tmp/a.tar",
            f"export TAR_OPTIONS=-C{bare}; tar -xf a.tar",
            "TAR_OPTIONS='-C .claude/hooks' tar xf /tmp/a.tar",
            "env TAR_OPTIONS=-C.claude/hooks tar -xf /tmp/a.tar",
            "UNZIP=-d.claude/hooks unzip /tmp/a.zip",
            "UNZIPOPT='-d .claude/hooks' unzip /tmp/a.zip",
            "export UNZIP=-l-; cd .claude/hooks && unzip -l /tmp/a.zip",  # `-` cuối phủ định `-l` của argv (đo)
        )
        self.assert_codes(
            "NONE",
            "TAR_OPTIONS=-v tar -xf a.tar -C build",
            "cd .claude/hooks && TAR_OPTIONS=-O tar -xf /tmp/a.tar",
            "cd .claude/hooks && UNZIP=-l unzip /tmp/a.zip",
            "cd .claude/hooks && UNZIP=--l unzip -l /tmp/a.zip",  # `--l` tự phủ định trong biến; `-l` argv vẫn liệt kê
            "TAR_OPTIONS=-C.claude/hooks tar -cf build/a.tar src",
        )

    def test_475_created_archive_is_write_target(self):
        self.assert_codes(
            "HOOK_BYPASS",
            "tar -cf .claude/hooks/guard.py /tmp/src",
            "cd .git/hooks && tar -cf pre-commit /tmp/payload",
            "tar --create --file=.git/hooks/pre-commit src",
            "tar cf .claude/hooks/guard.py src",
            "python3 -m zipfile -c .git/hooks/pre-commit /tmp/src",
            "python3 -m tarfile --create .claude/hooks/guard.py src",
            "zip -q .claude/hooks/x.zip src",
            "ar rc .claude/hooks/x.a a.o",
            "jar cf .claude/hooks/x.jar src",
            "cpio -o -F .claude/hooks/x.cpio < list",
            "pax -w -f .claude/hooks/x.pax src",
            "7z a .claude/hooks/x.7z src",
        )
        self.assert_codes("EVIDENCE_HANDWRITE", "tar -czf .autopilot/state.json /tmp/src")
        self.assert_codes(
            "NONE",
            "tar -czf build/out.tgz src",
            "python3 -m zipfile -c build/a.zip src",
            "zip -r build/a.zip src",
            "tar -cf - src > build/x.tar",
            "ar t .claude/hooks/x.a",
            "jar tf .claude/hooks/x.jar",
            "tar -tf .claude/hooks/x.tar",
        )

    def test_476_rsync_own_option_table(self):
        self.assert_codes(
            "HOOK_BYPASS",
            "rsync -P /tmp/guard.py .claude/hooks/",
            "rsync -av -P /tmp/evil/ .claude/",
            "rsync -r -l /tmp/guard.py .claude/hooks/",
            "rsync -a -p /tmp/evil/hooks .claude/",
            "rsync -a -o -i /tmp/guard.py .claude/hooks/",
        )
        self.assert_codes("EVIDENCE_HANDWRITE", "rsync -av -P /tmp/state.json .autopilot/")
        self.assert_codes(
            "NONE", "rsync -av src/ build/", "rsync -av --exclude .claude src/ build/", "rsync -a -e ssh src/ build/"
        )

    def test_477_cpio_directory_cluster_abbrev(self):
        bare = self.bare
        self.assert_codes(
            "HOOK_BYPASS",
            "cpio -iD .claude/hooks < /tmp/a.cpio",
            f"cpio -idD{bare} < a.cpio",
            f"cpio -i --dir={bare} < a.cpio",
            f"cd {bare} && cpio --ext < a.cpio",
            "cpio --extract --directory .claude/hooks < a.cpio",
        )
        self.assert_codes("NONE", "cpio -i -D build < a.cpio", "cpio -it -D .claude/hooks < a", "cpio -o > b.cpio")

    def test_shared_reader_edges(self):
        cp = guard.COPY_OPT_TABLES["cp"]
        self.assertEqual(
            guard._getopt(["--t", "D", "-fS~", "a", "--", "-x"], cp)[:3],
            [("target-directory", "D"), ("f", None), ("S", "~")],
        )
        self.assertEqual(guard._operands(guard._getopt(["--t", "D", "-fS~", "a", "--", "-x"], cp)), ["a", "-x"])
        self.assertEqual(
            guard._getopt(["--p", "--=x", "-t"], cp), [("p", None), ("-", "x"), ("t", None)]
        )  # mơ hồ, rỗng
        self.assertEqual(guard._getopt(["--exc"], guard.RSYNC_OPTS), [("exc", None)])  # popt không nhận viết tắt
        self.assertEqual(guard._old_style(["xfC", "a"], guard.TAR_SHORT_VALUE), ["-x", "-f", "a", "-C"])
        self.assertEqual(
            guard._py_module(["--check-hash-based-pycs", "always", "--help", "-X", "dev", "-mzipfile"]), ("zipfile", [])
        )
        self.assertEqual(guard._py_module(["-Wignore", "-I"]), ("", []))
        self.assertEqual(guard._py_module(["--", "-m", "x"]), ("", []))
        table = guard.PY_ARCHIVE_OPTS["tarfile"]
        self.assertEqual(guard._argparse(["--zz", "-q", "-e", "a", "--", "b"], table), {"extract": ["a"], "": ["b"]})
        self.assertEqual(guard._argparse(["-e=a", "--fil=x"], table), {"extract": ["a"], "filter": ["x"]})
        self.assertEqual(guard._py_archive(["-m", "zipfile", "-e", "a.zip"]), ([], []))  # nargs=2 thiếu: lỗi, không ghi
        self.assertEqual(guard._unzip_parse(["a.zip", "-d"]), ([], False))
        self.assertEqual(guard._unzip_parse(["-qd", "x", "a.zip", "-l", "-dy"]), (["x", "y"], False))
        self.assertEqual(guard._ar_parse(["--plugin", "p", "rc", "a.a", "o"])[:2], ("rc", ["a.a", "o"]))
        self.assertEqual(guard._ar_archive(["rb", "m", "a.a", "o"]), ["a.a"])
        self.assertEqual(guard._ar_archive(["t", "a.a"]), [])
        self.assertEqual(guard._cpio_dirs(["-pdm", "dest"]), ["dest"])
        self.assertEqual(
            guard._archive_outputs("zip", ["-b", "/tmp", "-r", "o.zip", "src", "--out", "n.zip"]), ["o.zip", "n.zip"]
        )
        self.assertEqual(guard._archive_outputs("jar", ["--create", "--file=x.jar", "a"]), ["x.jar"])
        self.assertEqual(guard._archive_outputs("pax", ["-r", "-f", "x"]), [])
        self.assertEqual(guard._archive_outputs("gzip", ["x"]), [])
        self.assertEqual(
            guard._with_env_opts(["tar", "xf", "a"], ["TAR_OPTIONS=-v", "tar", "xf", "a"], None),
            ["tar", "-v", "-x", "-f", "a"],
        )
        self.assertEqual(
            guard._with_env_opts(["tar", "xf", "a"], ["tar", "xf", "a"], {"TAR_OPTIONS": ""}), ["tar", "xf", "a"]
        )
        self.assertEqual(guard._copy_into_positionals(["mv", "-t", "D", "a"]), ["a", "D"])
        self.assertEqual(guard._copied_into(["rsync", "a", "host:d/"], str(self.root), str(self.root)), [])
        self.assertTrue(guard._keeps_path(["rsync", "-aR", "a", "d/"]))
        self.assertFalse(guard._keeps_path(["cp", "--p", "a", "d/"]))  # `--p` mơ hồ (parents/preserve)

    def test_green_scp_sink_and_7z_case(self):
        self.assert_codes("HOOK_BYPASS", "scp -t .claude/hooks", "cd .claude/hooks && 7z X /tmp/a.7z")
        self.assert_codes("HOOK_BYPASS", "7z x /tmp/a.7z -O.claude/hooks")
        self.assert_codes("NONE", "scp -f src", "7z l /tmp/a.7z", "7z x /tmp/a.7z -obuild")


class CwdUnion3674Test(unittest.TestCase):
    """T-3674 (D-347, audit delta 2026-11-04): thư mục chạy là HỢP MỌI ĐÍCH `cd` — không mô phỏng if/while/hàm/ống/
    `exit`; mọi luật theo thư mục (repo trần đang chờ, Git dir giả, cổng commit) xét đủ mọi ứng viên. Mỗi ca chặn đỏ
    ở 97ea666 (bash 5.2 xác nhận `pwd`)."""

    git_init = GitMetadataTest.git_init
    policy = GitMetadataTest.policy
    assert_code = GitMetadataTest.assert_code
    assert_codes = OptionParse3673Test.assert_codes

    def setUp(self):
        GitMetadataTest.setUp(self)
        r = self.root
        for d in ("sub/deep", "sub2", "src", ".autopilot", "docs/autopilot"):
            (r / d).mkdir(parents=True)
        (r / "sub" / "up").symlink_to(r / "sub2")
        (self.tmp / "rl").symlink_to(r)

    def cands(self, cmd):
        return [list(c) for _, c in guard._commands_with_cwds(guard.tokenize(cmd), str(self.root))]

    def test_478_pending_bare_and_fake_git_dir_every_candidate(self):
        r = self.root
        self.assert_codes(
            "HOOK_BYPASS",
            "git init --bare X; cd nonexist; printf x > X/config",
            f"cd nonexist; git init --bare X; printf x > {r}/X/config",
            "git init --bare X; false && cd sub; printf x > X/config",
            "git init --bare X; true || cd sub; printf x > X/config",
            "git init --bare sub/X; cd -P sub/up/..; printf x > sub/X/config",
            f"cd nonexist; mkdir -p D/objects D/refs; printf m > D/HEAD; printf x > {r}/D/config",
            f"cd nonexist; cp -r {r}/.git D; printf x > {r}/D/config",
        )
        self.assert_codes(
            "NONE",
            "git init --bare X; cd sub; printf x > notes",
            "cd nonexist; mkdir -p D/objects; printf x > other/notes",
            # tiền tố `cd … &&`: `git init` chỉ chạy khi `cd` thành công — repo trần ở `nonexist/X`, không ở gốc
            f"cd nonexist && git init --bare X; printf x > {r}/X/config",
        )

    def test_479_lastpipe_cd_in_last_pipe_element(self):
        self.assert_codes(
            "EVIDENCE_HANDWRITE",
            "shopt -s lastpipe; true | cd sub; printf x > ../.autopilot/x",
            "shopt -s lastpipe; true | { cd sub; }; printf x > ../.autopilot/x",
            "set +m; shopt -s lastpipe\ntrue | cd sub\nprintf x > ../.autopilot/x",
        )

    def test_480_or_exit_return_does_not_drop_old_dir(self):
        self.assert_codes(
            "EVIDENCE_HANDWRITE",
            "bash -c 'cd /khong-co || return; printf x > .autopilot/x'",
            "cd /khong-co || exit | cat; printf x > .autopilot/x",
            "cd /khong-co || exit 2>/nonexistent/x; printf x > .autopilot/x",
            "exit() { :; }; cd /khong-co || exit; printf x > .autopilot/x",
            "enable -n exit; cd /khong-co || exit; printf x > .autopilot/x",
            "cd /khong-co || return 0; printf x > docs/autopilot/STAGE.json",
        )
        root = str(self.root)
        self.assertEqual(self.cands("cd /khong-co || exit 1; echo")[2], ["/khong-co", root])

    def test_481_alias_defined_reaches_nested_shell_and_eval(self):
        self.assert_codes(
            "HOOK_BYPASS",
            "git config alias.u 'config --unset core.hooksPath' && bash -c \"git u\"",
            "git config alias.u 'config --unset core.hooksPath' && eval git u",
            "git config alias.u 'config --unset core.hooksPath'; sh -c 'sh -c \"git u\"'",
            "git config --global alias.r 'config --remove-section core'; eval 'git r'",
        )
        self.assertNotEqual(self.policy("git config alias.st status && bash -c 'git st'")["code"], "HOOK_BYPASS")

    def test_482_cd_skipped_by_control_flow_keeps_old_dir(self):
        r = self.root
        self.assert_codes(
            "EVIDENCE_HANDWRITE",
            "false && cd sub; printf x > .autopilot/x",
            "true || cd sub; printf x > .autopilot/x",
            "[ -d nonexist ] && cd sub; printf x > .autopilot/x",
            "if false; then cd sub; fi; printf x > .autopilot/x",
            "while false; do cd sub; done; printf x > .autopilot/x",
            "for i in; do cd sub; done; printf x > .autopilot/x",
            "f() { cd sub; }; printf x > .autopilot/x",
            f"case a in (b) cd {r}/sub;; esac; printf x > .autopilot/x",
            "cd sub/deep; for i in 1 2; do cd ..; done; printf x > .autopilot/x",
            # vòng lặp: lệnh đứng TRƯỚC `cd` trong thân chạy lại sau nó; thân hàm chạy lúc gọi
            "for i in 1 2; do printf x > ../.autopilot/x; cd sub; done",
            "f() { printf x > ../.autopilot/x; }; cd sub; f",
            "trap 'printf x > ../.autopilot/x' EXIT; cd sub",
            # đồng thời: `cd` ở nền không dời shell này
            "cd sub & wait; printf x > .autopilot/x",
        )
        root, sub = str(r), str(r / "sub")
        self.assertEqual(self.cands("false && cd sub; echo")[2], [sub, root])
        # `cd` tương đối trong vòng lặp: bao đóng (`..` tới `/`), `cd sub` lặp vượt giới hạn → None
        self.assertIn(root, self.cands("cd sub/deep; for i in 1 2; do cd ..; done; echo")[-1])
        self.assertIn(None, self.cands("while true; do cd sub; done; echo")[-1])
        self.assertIn(f"{sub}/sub", self.cands("while true; do cd sub; done; echo")[-1])

    def test_483_physical_cd_resolves_symlink_first(self):
        self.assert_codes(
            "EVIDENCE_HANDWRITE",
            "cd -P sub/up/.. && printf x > .autopilot/x",
            "set -P; cd sub/up/..; printf x > .autopilot/x",
            "set -o physical; cd sub/up/.. && printf x > .autopilot/x",
            "cd sub/up; printf x > ../.autopilot/x",  # `..` của đích ghi do kernel giải theo đường vật lý
        )

    def test_484_eval_cd(self):
        self.assert_codes(
            "EVIDENCE_HANDWRITE",
            "eval cd sub; printf x > ../.autopilot/x",
            "eval 'cd sub'; printf x > ../.autopilot/x",
            "eval eval cd sub; printf x > ../.autopilot/x",
        )
        self.assertIn(None, self.cands("eval cd sub; echo")[1])

    def test_485_sendemail_identity_command_keys(self):
        bare = self.bare
        self.assert_codes(
            "HOOK_BYPASS",
            "git config sendemail.x.sendmailCmd 'sh -c id'",
            f"git config --file {bare}/config sendemail.x.smtpServer /tmp/x.sh",
            "git config sendemail.a.b.toCmd 'sh -c id'",
            "git -c sendemail.x.ccCmd='sh -c id' send-email a.patch",
        )
        self.assert_codes("NONE", "git config sendemail.x.smtpUser me", "git config sendemail.x.to a@b.c")

    def test_486_gone_dir_compared_physically(self):
        t = self.tmp
        self.assert_codes(
            "EVIDENCE_HANDWRITE",
            "rm -rf sub2; cd sub/up; printf x > .autopilot/x",
            f"rm -rf {t}/rl/sub2; cd sub2; printf x > .autopilot/x",
        )

    def test_commit_dir_every_candidate(self):
        other = self.tmp / "other"
        self.git_init(other)
        root, bare = str(self.root), str(self.bare)
        for cmd, want in (
            ("cd src && git commit -m x", f"{root}/src"),
            ("cd src; git commit -m x", f"{root}/src"),  # cùng repo: ứng viên đầu
            (f"cd {other}; git commit -m x", str(other)),  # repo khác dự án: chặt (hook hỏi ở strict)
            (f"false && cd {other}; git commit -m x", str(other)),
            (f"cd {bare}; git commit -m x", ""),  # không biết repo nào
            ("cd $X; git commit -m x", ""),
            ("git commit -m x", root),
        ):
            with patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": root}):
                res = guard.bash_decision(cmd, root)
            self.assertTrue(res["commit"], cmd)
            self.assertEqual(res["commit_dir"], want, cmd)

    def test_fake_git_dir_project_root_with_dotgit(self):
        self.assert_codes("NONE", "mkdir -p objects refs && touch HEAD config", "printf x > HEAD; printf y > config")
        self.assert_codes("HOOK_BYPASS", "mkdir -p d/objects && touch d/HEAD d/config")

    def test_union_walk_edges(self):
        root, sub = str(self.root), str(self.root / "sub")
        # vòng lồng: lệnh trong vòng ngoài nhận tập ở cuối vòng ngoài; vòng chưa đóng: tới cuối lệnh
        nested = self.cands("for a in 1; do printf x; for b in 2; do cd /tmp; done; done; echo")
        self.assertIn("/tmp", nested[1])
        self.assertIn("/tmp", self.cands("while true; do printf x; cd /tmp")[1])
        # `cdable_vars` từ môi trường: `cd` chưa chắc thành công không thuộc tiền tố chính xác
        with patch.dict(os.environ, {"BASHOPTS": "cdable_vars"}):
            self.assertEqual(self.cands("cd khong-co && echo")[1], [f"{root}/khong-co", root, None])
        with patch.dict(os.environ, {"SHELLOPTS": "braceexpand:physical"}):
            self.assertEqual(self.cands("cd sub && echo")[1], [sub, root])
        self.assertEqual(self.cands("eval echo hi; echo")[1], [root])
        self.assertEqual(self.cands("popd; echo")[1], [None, root])
        self.assertEqual(guard._cwd_picks([]), 1)
        self.assert_code("eval 'c''d sub'; printf x > ../.autopilot/x", "EVIDENCE_HANDWRITE")  # nháy trong thân eval
        # alias đặt ở tầng ngoài, lệnh có `cd` (nhiều lượt `pick`): không nhân đôi bảng
        self.assert_code("git config alias.u 'config --unset core.hooksPath'; cd sub; git u", "HOOK_BYPASS")
        self.assertEqual(guard._strict_commit_dir(["", ""], root), "")
        self.assertEqual(guard._repo_top("/"), "")
        # subshell `( … )` luôn là tiến trình con: đích `cd` trong đó bỏ khi ra; thân hàm/trap vẫn thấy chúng
        self.assertEqual(self.cands("(cd sub && ls); echo")[-1], [root])
        self.assertEqual(self.cands("cd /khong-co && (cd sub; echo a); echo b")[-1], ["/khong-co", root])
        self.assert_code("f() { (cd sub; printf x > ../.autopilot/x); }; f", "EVIDENCE_HANDWRITE")
        self.assert_code("for i in 1; do (cd sub; printf x > ../.autopilot/x); done", "EVIDENCE_HANDWRITE")

    def test_false_positives_stay_clear(self):
        """Gỡ chặn oan AUD-SEC-463 giữ nguyên: ứng viên là thư mục biết, không phải None."""
        self.assert_codes(
            "NONE",
            "mkdir -p out; cd out; tar -xf ../a.tar",
            f"mkdir -p {self.tmp}/w; cd {self.tmp}/w; printf x > config",
            "mkdir -p dist; cd dist; unzip ../a.zip",
            "cd /khong-co || exit 1; printf x > config",
            "cd src && git commit -m x",
            "mkdir build; cd build; cmake ..; make",
            "git status",
            "pushd src; ls; popd",
            "cd src && make && cd ..; git status",
            "cd sub && cd deep && printf x > ../../.autopilot/../notes",
            "for d in a b; do (cd /tmp && ls); done",
        )
        root = str(self.root)
        self.assertEqual(self.cands("cd src && cd ../sub && echo"), [[f"{root}/src"], [f"{root}/sub"], [f"{root}/sub"]])
        self.assertEqual(self.cands("git status"), [[root]])


if __name__ == "__main__":
    unittest.main()
