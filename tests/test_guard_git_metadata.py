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
        self.assert_code(f"cd {self.bare}; cd {self.root}; cd {self.tmp} && git status", "NONE")

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

        self.assertEqual(dirs("cd /khong-co; echo x > a"), [["/khong-co"], ["/khong-co", root]])
        self.assertEqual(first("cd /khong-co; echo x > a"), ["/khong-co", "/khong-co"])
        self.assertEqual(dirs("cd /khong-co && echo x > a"), [["/khong-co"], ["/khong-co"]])
        self.assertEqual(dirs("cd /khong-co && (echo a; echo b)"), [["/khong-co"]] * 3)
        self.assertEqual(dirs(f"cd {self.tmp}; echo x > a"), [[str(self.tmp)], [str(self.tmp)]])
        self.assertEqual(dirs("(cd /khong-co); echo x > a"), [["/khong-co"], [root]])
        for cmd in (
            "cd /khong-co; echo x > .autopilot/state.json",
            "cd /khong-co\necho x > .autopilot/state.json",
            "cd khong-co; echo x > .autopilot/state.json",
            "cd /khong-co || echo x > .autopilot/state.json",
            "cd /khong-co && true; echo x > .autopilot/state.json",
            "pushd /khong-co; echo x > .autopilot/state.json",
            "mkdir .autopilot; cd .autopilot; echo x > state.json",  # nhánh cd thành công vẫn xét (thư mục tạo trước)
        ):
            self.assert_code(cmd, "EVIDENCE_HANDWRITE")
        self.assert_code("cd /khong-co; printf x > .git/hooks/pre-commit", "HOOK_BYPASS")
        self.assert_code("cd /khong-co; echo x > .env", "SECRET_WRITE")  # luật cũ (tên `.env` ở mọi nơi)
        at_root = self.policy("echo x > xt.yaml")
        self.assertNotEqual(at_root["code"], "NONE")
        self.assert_code("cd /khong-co; echo x > xt.yaml", at_root["code"])
        for cmd in (
            "cd /khong-co && echo x > .autopilot/state.json",  # cd hỏng thì vế sau không chạy
            f"cd {self.tmp}; echo x > .autopilot/state.json",
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
        self.assertEqual(self.cands("cd /khong-co; echo")[1], ["/khong-co", root])
        self.assertEqual(self.cands("cd /khong-co && echo")[1], ["/khong-co"])
        self.assertEqual(self.cands("cd /khong-co || exit 1; echo")[2], ["/khong-co"])
        self.assertEqual(self.cands("cd /khong-co || return; echo")[2], ["/khong-co"])
        self.assertEqual(self.cands(f"cd {tmp}; echo")[1], [tmp])  # có lúc kiểm, không bị xoá: chắc
        self.assertEqual(
            self.cands("cd /khong-co && (echo a; echo b); echo c")[1:], [["/khong-co"]] * 2 + [["/khong-co", root]]
        )
        self.assertEqual(
            self.cands("{ cd /khong-co && echo a\n}; echo b")[1:],
            [["/khong-co"], ["/khong-co", root], ["/khong-co", root]],
        )
        self.assertEqual(self.cands("cd $X; echo")[1], [None])
        self.assertEqual(self.cands(f"cd {tmp}; cd /khong-co; cd -; echo")[3], [None])
        self.assertEqual(self.cands(f"cd {tmp}; cd {root}/src; cd -; echo")[3], [None])  # AUD-SEC-466
        self.assertEqual(self.cands("case x in a) cd src;; esac; echo")[-1], [None])  # `)` lẻ: không biết như cũ
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
            f"cd {d}; echo x > .autopilot/state.json",
            f"rm -rf {d}/x; cd {d}; echo x > .autopilot/state.json",  # xoá thư mục con, không phải đích
            f"cd {d} || true; echo x > .autopilot/state.json",
            "cd /khong-co; git status",
        ):
            self.assert_code(cmd, "NONE")

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
        self.assertEqual(self.cands(f"cd {tmp} | true; echo")[2], [root])
        self.assertEqual(self.cands(f"cd {tmp} && echo a | cat; echo")[3], [str(tmp)])
        for cmd in (
            f"cd {tmp} && echo x | cat > .autopilot/state.json",  # `&&` thấp hơn `|`: ống chạy sau `cd`
            f"cd {tmp}; {ev} | cat",
            f"cd {tmp} && {ev} &",
            f"{{ cd {tmp}; }}; {ev}",
            f"cd {tmp} | true; echo x > a.txt",
        ):
            self.assert_code(cmd, "NONE")

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


if __name__ == "__main__":
    unittest.main()
