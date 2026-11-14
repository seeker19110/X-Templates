"""S-111, S-118 (ADR-0077): chỉ loại sổ khỏi fingerprint nếu bật triển khai."""

import json
import os
import sys
import unittest.mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_xt_cli import TmpRepoCase, run_main

LEDGER = "docs/ops/DEPLOYS.json"
EMPTY_LEDGER = '{"schema":1,"envs":{},"events":[]}'


class DeployReleaseFingerprintTest(TmpRepoCase):
    def release_content(self):
        rc, out, err = run_main("release-check", "--json")
        self.assertIn(rc, (0, 1), err)
        fingerprint = json.loads(out)["subject"]["content"]
        self.assertRegex(fingerprint, r"^[0-9a-f]{64}$")
        return fingerprint

    def test_only_exact_ledger_path_is_excluded_from_release_content(self):
        self.init_repo()
        self.commit_files({"app/xt.yaml": 'deploy_envs: "dev prod" # opt-in\n', "app/src.py": "pass\n"}, 1_750_000_000)
        self.enterContext(unittest.mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(self.repo / "app")}))
        baseline = self.release_content()
        path = self.repo / "app" / LEDGER
        path.parent.mkdir(parents=True)
        path.write_text(EMPTY_LEDGER, encoding="utf-8")
        self.assertEqual(self.release_content(), baseline)
        self.commit_files({f"app/{LEDGER}": EMPTY_LEDGER}, 1_750_000_001)
        path.write_text(EMPTY_LEDGER + "\n", encoding="utf-8")
        self.assertEqual(self.release_content(), baseline)
        self.commit_files({f"app/{LEDGER}": path.read_text(encoding="utf-8")}, 1_750_000_002)
        self.assertEqual(self.release_content(), baseline)
        for relative in ("docs/ops/DEPLOYS.json.bak", "src/DEPLOYS.json", f"{LEDGER}/src.py"):
            with self.subTest(relative=relative):
                if path.is_file():
                    path.unlink()
                neighbor = self.repo / "app" / relative
                neighbor.parent.mkdir(parents=True, exist_ok=True)
                neighbor.write_text("pass\n", encoding="utf-8")
                self.assertNotEqual(self.release_content(), baseline)
                neighbor.unlink()
                self.assertEqual(self.release_content(), baseline)

    def test_receipt_path_counts_as_project_content_without_opt_in(self):
        self.init_repo()
        self.commit_files({"src.py": "pass\n"}, 1_750_000_000)
        self.enterContext(unittest.mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(self.repo)}))
        path = self.repo / LEDGER
        path.parent.mkdir(parents=True)
        config = self.repo / "xt.yaml"
        for value in (None, b"# deploy_envs: dev\n", b'deploy_envs: "" # disabled\n', b"\xff"):
            with self.subTest(config=value):
                if value is not None:
                    config.write_bytes(value)
                baseline = self.release_content()
                path.write_text('{"inventory":["ordinary project data"]}', encoding="utf-8")
                with_ledger = self.release_content()
                path.unlink()
                self.assertNotEqual(with_ledger, baseline)
                self.assertEqual(self.release_content(), baseline)
        config.write_text("deploy_envs: # disabled\n", encoding="utf-8")
        baseline = self.release_content()
        self.commit_files({LEDGER: '{"inventory":["ordinary project data"]}'}, 1_750_000_001)
        committed = self.release_content()
        self.assertNotEqual(committed, baseline)
        path.write_text('{"inventory":["new data"]}', encoding="utf-8")
        self.assertNotEqual(self.release_content(), committed)
