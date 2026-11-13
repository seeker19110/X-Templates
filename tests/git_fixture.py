"""Git fixture: cô lập routing/config, không chạy hook/template/chữ ký của người gọi."""

from __future__ import annotations

import contextlib
import os
import subprocess
from collections.abc import Iterator
from pathlib import Path
from unittest import mock


@contextlib.contextmanager
def isolated_git_environment() -> Iterator[None]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull, GIT_CONFIG_NOSYSTEM="1")
    with mock.patch.dict(os.environ, env, clear=True):
        yield


def fixture_git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "git",
            "-c",
            "core.hooksPath=" + os.devnull,
            "-c",
            "init.templateDir=",
            "-c",
            "commit.gpgsign=false",
            "-c",
            "tag.gpgsign=false",
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "-C",
            str(root),
            *args,
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=15,
    )


def init_git_fixture(root: Path) -> None:
    fixture_git(root, "init", "--template=", "-q", "-b", "main")
    for key, value in (("core.hooksPath", os.devnull), ("commit.gpgsign", "false"), ("init.templateDir", "")):
        fixture_git(root, "config", key, value)
