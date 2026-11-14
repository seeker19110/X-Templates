"""Lát đọc receipt triển khai (ADR-0077): CLI chỉ đọc và vân tay của ứng viên."""

import json
import os
import shlex
import sys
import unittest
import unittest.mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_xt_cli import TmpRepoCase, run_main

LEDGER = "docs/ops/DEPLOYS.json"
EMPTY = {"schema": 1, "envs": {}, "events": []}
EMPTY_STATUS = {**EMPTY, "metrics": {}}
HEAD = "a" * 40
DIGEST = "b" * 64
CONTENT = "c" * 64
AT = "2026-11-14T12:00:00+00:00"
STEP = {"cmd_sha256": "d" * 64, "exit_code": 0}
UNKNOWN = {"current": None, "previous": None, "unknown": True}
UNDEPLOYED = {**UNKNOWN, "unknown": False}


def receipt(env="dev", **changes):
    return {
        "env": env,
        "result": "deployed",
        "subject": {"head": HEAD, "content": CONTENT, "digest": DIGEST},
        "artifacts": [{"path": "dist/ứng-viên.tgz", "sha256": DIGEST}],
        "started": AT,
        "finished": AT,
        "deploy": STEP,
        "smoke": STEP,
        "served_digest": DIGEST,
        "rollback": None,
        "previous_digest": None,
        "url": "https://example.invalid/ứng-viên",
        "runner": {"kind": "local", "run_id": None, "run_url": None},
        "session": None,
        **changes,
    }


class DeployStatusTest(TmpRepoCase):
    def setUp(self):
        super().setUp()
        self.project = self.init_repo()
        self.enterContext(unittest.mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(self.project)}))
        self.config = self.project / "xt.yaml"
        self.unexpected = self.project / "unexpected"
        command = f"touch {shlex.quote(str(self.unexpected))}"
        self.config.write_text(
            "deploy_envs: dev prod empty a123456789012345\n"
            f"deploy_dev: {command}\nsmoke_dev: {command}\n"
            f"digest_dev: {command}\nrollback_dev: {command}\n",
            encoding="utf-8",
        )
        self.ledger = self.project / LEDGER

    def write_ledger(self, data):
        self.ledger.parent.mkdir(parents=True, exist_ok=True)
        self.ledger.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    def status_json(self, *args):
        rc, out, err = run_main("deploy", "status", "--json", *args)
        self.assertEqual((rc, err), (0, ""), out)
        return json.loads(out)

    def assert_error(self, expected, *args):
        rc, out, err = run_main("deploy", "status", "--json", *args)
        self.assertEqual((rc, out), (2, ""), err)
        self.assertIn(expected, err)
        self.assertEqual(len(err.splitlines()), 1, err)

    def test_missing_and_empty_ledgers_are_read_only(self):
        self.assertEqual(self.status_json(), EMPTY_STATUS)
        self.assertFalse(self.ledger.parent.exists())
        self.assertFalse((self.project / ".autopilot").exists())
        self.write_ledger(EMPTY)
        original = self.ledger.read_bytes()
        self.assertEqual(self.status_json("--env", "a123456789012345"), EMPTY_STATUS)
        rc, out, err = run_main("deploy", "status")
        self.assertEqual((rc, err), (0, ""))
        self.assertIn("Chưa có biên nhận", out)
        self.assertEqual(self.ledger.read_bytes(), original)

    def test_filter_limits_envs_and_events_without_executing_or_writing(self):
        dev = receipt()
        prod = receipt(
            "prod",
            result="rollback_failed",
            deploy={**STEP, "exit_code": 1},
            smoke=None,
            rollback={**STEP, "exit_code": -1},
            served_digest=None,
            previous_digest=CONTENT,
            url=None,
            runner={"kind": "ci", "run_id": 17, "run_url": "https://example.invalid/17"},
            session="phiên thử",
        )
        historic = receipt("old", runner={"kind": "ci", "run_id": "17", "run_url": None})
        envs = {
            "dev": {
                "current": dev,
                "previous": receipt(subject={**dev["subject"], "digest": CONTENT}, served_digest=CONTENT),
                "unknown": False,
            },
            "empty": UNDEPLOYED,
            "prod": UNKNOWN,
            "old": {**UNDEPLOYED, "current": historic},
        }
        data = {"schema": 1, "envs": envs, "events": [dev, prod, historic, dev]}
        self.write_ledger(data)
        original = self.ledger.read_bytes()
        original_mtime = self.ledger.stat().st_mtime_ns
        original_git = self.git("status", "--porcelain", "--untracked-files=all")
        status = self.status_json()
        self.assertEqual({key: status[key] for key in data}, data)
        self.assertEqual(set(status["metrics"]), set(envs))
        self.assertEqual(
            self.status_json("--env", "dev"),
            {
                "schema": 1,
                "envs": {"dev": envs["dev"]},
                "events": [dev, dev],
                "metrics": {"dev": status["metrics"]["dev"]},
            },
        )
        self.assertEqual(
            self.status_json("--env", "prod"),
            {"schema": 1, "envs": {"prod": UNKNOWN}, "events": [prod], "metrics": {"prod": status["metrics"]["prod"]}},
        )
        rc, out, err = run_main("deploy", "status")
        self.assertEqual((rc, err), (0, ""))
        self.assertIn(f"dev: deployed {DIGEST}", out)
        self.assertIn("empty: chưa có biên nhận", out)
        self.assertIn("prod: chưa rõ bản đang phục vụ", out)
        self.assertEqual(self.ledger.read_bytes(), original)
        self.assertEqual(self.ledger.stat().st_mtime_ns, original_mtime)
        self.assertEqual(self.git("status", "--porcelain", "--untracked-files=all"), original_git)
        self.assertFalse(self.unexpected.exists())
        self.assertFalse((self.project / ".autopilot").exists())

    def test_invalid_or_unconfigured_environment(self):
        for name in ("", "a123456789012345x", "Dev", "../x", "môi"):
            with self.subTest(name=name):
                self.assert_error("--env", "--env", name)
        self.assert_error("deploy_envs", "--env", "old")
        for content in ("", "deploy_envs:   \n", "deploy_envs: dev Prod\n"):
            with self.subTest(content=content):
                self.config.write_text(content, encoding="utf-8")
                self.assert_error("deploy_envs")
        self.config.unlink()
        self.assert_error("deploy_envs")

    def test_io_and_parse_errors_leave_ledger_in_place(self):
        self.ledger.mkdir(parents=True)
        self.assert_error(LEDGER)
        self.ledger.rmdir()
        for raw in (b"", b"{x", b"\xff", b"[" * 3000):
            with self.subTest(raw=raw[:10]):
                self.ledger.write_bytes(raw)
                self.assert_error(LEDGER)
                self.assertEqual(self.ledger.read_bytes(), raw)

    def test_config_read_errors_name_xt_yaml_even_with_debug(self):
        self.config.write_bytes(b"\xff")
        with unittest.mock.patch.dict(os.environ, {"XT_DEBUG": "1"}):
            self.assert_error("xt.yaml")
            with unittest.mock.patch.object(Path, "read_text", side_effect=PermissionError("I/O fixture")):
                self.assert_error("xt.yaml")

    def test_rejects_ledger_links_leaving_project(self):
        outside = self.tmp / "outside"
        outside.mkdir()
        outside_ledger = outside / self.ledger.name
        outside_ledger.write_text(json.dumps(EMPTY), encoding="utf-8")
        self.ledger.parent.mkdir(parents=True)
        self.ledger.symlink_to(outside_ledger)
        self.assert_error(LEDGER)
        self.ledger.unlink()
        self.ledger.parent.rmdir()
        self.ledger.parent.symlink_to(outside, target_is_directory=True)
        self.assert_error(LEDGER)
        self.ledger.parent.unlink()
        self.ledger.parent.mkdir()
        self.ledger.symlink_to(self.ledger.name)
        self.assert_error(LEDGER)

    def test_rejects_bad_ledger_shapes(self):
        for data in (
            None,
            [],
            {**EMPTY, "schema": 2},
            {**EMPTY, "schema": True},
            {**EMPTY, "schema": 1.0},
            {**EMPTY, "envs": []},
            {**EMPTY, "events": {}},
            {**EMPTY, "unexpected": "do not print"},
            {**EMPTY, "envs": {"../x": UNKNOWN}},
            {**EMPTY, "envs": {"dev": 0}},
            {**EMPTY, "envs": {"dev": {**UNKNOWN, "unknown": 0}}},
            {**EMPTY, "envs": {"dev": {**UNKNOWN, "current": receipt()}}},
            {**EMPTY, "envs": {"dev": {**UNDEPLOYED, "current": receipt("prod")}}},
            {**EMPTY, "envs": {"dev": {**UNKNOWN, "previous": 0}}},
            {**EMPTY, "envs": {"dev": {"unknown": True, "current": None}}},
            {**EMPTY, "events": [None]},
        ):
            with self.subTest(data=data):
                self.write_ledger(data)
                self.assert_error(LEDGER, "--env", "prod")

    def test_rejects_bad_receipt_shapes(self):
        dev = receipt()
        changes = (
            {"env": "Dev"},
            {"env": 0},
            {"result": []},
            {"result": "OK"},
            {"subject": None},
            {"subject": {**dev["subject"], "head": 0}},
            {"subject": {**dev["subject"], "head": "a"}},
            {"subject": {**dev["subject"], "content": 0}},
            {"subject": {**dev["subject"], "digest": "b"}},
            {"subject": {**dev["subject"], "tree": "do not print"}},
            {"artifacts": None},
            {"artifacts": [None]},
            {"artifacts": [{"path": "dist/app", "sha256": DIGEST, "stdout": "do not print"}]},
            {"artifacts": [{"path": 0, "sha256": DIGEST}]},
            {"artifacts": [{"path": "dist/app", "sha256": True}]},
            {"deploy": None},
            {"deploy": {**STEP, "cmd_sha256": None}},
            {"deploy": {**STEP, "exit_code": False}},
            {"smoke": {}},
            {"rollback": {**STEP, "stdout": "do not print"}},
            {"started": "ngày mai"},
            {"finished": "2026-11-14T12:00:00"},
            {"finished": "2026-11-14T12:00:00+07:00"},
            {"started": 0},
            {"served_digest": 0},
            {"previous_digest": "x"},
            {"url": []},
            {"runner": 1},
            {"runner": {**dev["runner"], "stderr": "do not print"}},
            {"runner": {**dev["runner"], "kind": "remote"}},
            {"runner": {**dev["runner"], "run_id": True}},
            {"runner": {**dev["runner"], "run_url": 0}},
            {"session": 0},
            {"stdout": "do not print"},
        )
        for fields in changes:
            with self.subTest(fields=fields):
                self.write_ledger({**EMPTY, "events": [receipt(**fields)]})
                self.assert_error(LEDGER)

    def test_rejects_receipt_with_impossible_success_or_timestamps(self):
        for fields, expected in (
            ({"served_digest": None}, "`served_digest`"),
            ({"served_digest": CONTENT}, "`served_digest`"),
            ({"deploy": {**STEP, "exit_code": 1}}, "`deploy`"),
            ({"smoke": None}, "`smoke`"),
            ({"smoke": {**STEP, "exit_code": 1}}, "`smoke`"),
            ({"rollback": STEP}, "`rollback`"),
            ({"finished": "2026-11-14T11:59:59Z"}, "`finished`"),
            ({"result": "rolled_back", "rollback": STEP, "previous_digest": CONTENT}, "`served_digest`"),
            ({"result": "rolled_back", "previous_digest": DIGEST}, "`rollback`"),
            ({"result": "rolled_back", "rollback": STEP}, "`previous_digest`"),
            ({"result": "rolled_back", "rollback": {**STEP, "exit_code": 1}, "previous_digest": DIGEST}, "`rollback`"),
            ({"result": "rollback_failed", "previous_digest": DIGEST}, "`rollback`"),
            ({"result": "failed", "previous_digest": DIGEST}, "`failed`"),
            ({"result": "failed", "rollback": STEP}, "`failed`"),
        ):
            with self.subTest(fields=fields):
                self.write_ledger({**EMPTY, "events": [receipt(**fields)]})
                self.assert_error(expected)

    def test_current_and_previous_must_be_confirmed_deployments(self):
        unconfirmed = receipt(result="failed", deploy={**STEP, "exit_code": 1}, served_digest=None)
        for field in ("current", "previous"):
            with self.subTest(field=field):
                self.write_ledger({**EMPTY, "envs": {"dev": {**UNDEPLOYED, field: unconfirmed}}})
                self.assert_error(f"envs.dev.{field}")

    def test_metrics_use_retained_events_grouped_by_environment(self):
        successful = receipt(finished="2026-11-14T12:00:02.500Z")
        rolled_back = receipt(
            result="rolled_back",
            deploy={**STEP, "exit_code": 1},
            rollback=STEP,
            previous_digest=CONTENT,
            served_digest=CONTENT,
            finished="2026-11-14T12:00:04+00:00",
        )
        self.write_ledger(
            {
                **EMPTY,
                "envs": {"dev": {**UNDEPLOYED, "current": successful}, "empty": UNDEPLOYED},
                "events": [successful, receipt("prod"), rolled_back],
            }
        )
        self.assertEqual(
            self.status_json()["metrics"],
            {
                "dev": {"runs": 2, "rollback_rate": 0.5, "durations_seconds": [2.5, 4.0]},
                "empty": {"runs": 0, "rollback_rate": 0.0, "durations_seconds": []},
                "prod": {"runs": 1, "rollback_rate": 0.0, "durations_seconds": [0.0]},
            },
        )
        self.assertEqual(
            self.status_json("--env", "dev")["metrics"],
            {
                "dev": {"runs": 2, "rollback_rate": 0.5, "durations_seconds": [2.5, 4.0]},
            },
        )
