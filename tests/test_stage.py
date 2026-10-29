"""Test cho giai đoạn sản phẩm (ADR-0058): sổ `docs/autopilot/STAGE.json`, lệnh `xt.py stage`, khoá ở `loop` và hàng
`stage` của `release-check`. Repo git tạm thật (bản trình duyệt gắn SHA của HEAD)."""

from __future__ import annotations

import contextlib
import io
import json
import os
import stat
import unicodedata
import subprocess
import sys
import unittest
import unittest.mock
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import xt
from test_xt_cli import TmpRepoCase, run_main

HUMAN = {k: "" for k in xt.STAGE_AGENT_ENV}  # ngoài phiên agent
SHA = "a" * 40
SHA2 = "b" * 40


def ev(kind, stage, cycle="C-001", **extra):
    return {"event": kind, "cycle": cycle, "stage": stage, **extra}


def approve(stage, sha=SHA, cycle="C-001"):
    """submit + approve hợp lệ của một giai đoạn."""
    return [ev("submit", stage, cycle, sha=sha), ev("approve", stage, cycle, sha=sha, by="p@x")]


def ledger(history=None, **over):
    led = {"schema": 1, "cycle": "C-001", "stage": 1, "status": "active", "submitted": None}
    led["history"] = history if history is not None else [ev("init", 1)]
    led.update(over)
    return led


def completed(cycle="C-001"):
    return ledger([ev("init", 1), *approve(1), *approve(2), *approve(3)], stage=3, status="completed", cycle=cycle)


class StageProblemTest(unittest.TestCase):
    def test_valid_and_shape_errors(self):
        self.assertEqual(xt.stage_problem(ledger()), "")
        cases = [
            ([], "schema"),
            (ledger(schema=2), "schema"),
            (ledger(cycle="X"), "C-NNN"),
            (ledger(stage=4), "`stage` phải"),
            (ledger(stage=[1]), "`stage` phải"),  # không băm được: sổ hỏng, không TypeError (review #338)
            (ledger(stage=True), "`stage` phải"),
            (ledger(status="locked"), "`stage` phải"),
            (ledger(status="completed"), "chỉ có ở giai đoạn 3"),
            (ledger(status="awaiting_approval"), "submitted.sha"),
            (ledger(submitted={"sha": SHA}), "submitted.sha"),
            (ledger(submitted="x"), "phải là object hoặc null"),
            (ledger(history=[]), "thiếu `history`"),
            (ledger(history="x"), "thiếu `history`"),
        ]
        for led, why in cases:
            with self.subTest(why=why):
                self.assertIn(why, xt.stage_problem(led))

    def test_valid_histories(self):
        ok = [
            ledger([ev("init", 1), *approve(1)], stage=2),
            ledger([ev("init", 1), ev("submit", 1, sha=SHA)], status="awaiting_approval", submitted={"sha": SHA}),
            ledger([ev("init", 1), ev("submit", 1, sha=SHA), ev("reopen", 1), *approve(1, SHA2)], stage=2),
            ledger([ev("adopt", 3, by="p", evidence="v1.0")], stage=3),
            ledger([ev("init", 1), *approve(1, "c" * 64)], stage=2),  # repo SHA-256
            completed(),
            ledger([*completed()["history"], ev("init", 1, "C-002")], cycle="C-002"),
        ]
        for led in ok:
            with self.subTest(led=led["history"][-1]):
                self.assertEqual(xt.stage_problem(led), "")

    def test_hand_edits_are_exposed(self):
        """Ca tái hiện của review #327 (B1–B4) và sửa tay `stage` 1 → 3."""
        bad = {
            "nhảy 1→3": (ledger(stage=3), "lịch sử dựng ra C-001/1/active, sổ ghi C-001/3/active"),
            "B1 adopt thay init": (ledger([ev("adopt", 3)], stage=3), "sự kiện đầu"),
            "adopt giai đoạn 1": (ledger([ev("adopt", 1, by="p", evidence="e")]), "sự kiện đầu"),
            "B2 adopt chu kỳ khác": (
                ledger([ev("init", 1), ev("adopt", 3, "C-002", by="p", evidence="e")], cycle="C-002", stage=3),
                "đang mở C-001/1",
            ),
            "B3 approve không submit": (
                ledger([ev("init", 1), ev("approve", 1, sha=SHA, by="p")], stage=2),
                "sai thứ tự",
            ),
            "approve khác sha": (
                ledger([ev("init", 1), ev("submit", 1, sha=SHA), ev("approve", 1, sha=SHA2, by="p")], stage=2),
                "sai thứ tự",
            ),
            "approve thiếu by": (
                ledger([ev("init", 1), ev("submit", 1, sha=SHA), ev("approve", 1, sha=SHA)], stage=2),
                "sai thứ tự",
            ),
            "approve sau reopen": (
                ledger([ev("init", 1), ev("submit", 1, sha=SHA), ev("reopen", 1), ev("approve", 1, sha=SHA, by="p")]),
                "sai thứ tự",
            ),
            "submit sha ngắn": (ledger([ev("init", 1), ev("submit", 1, sha="abc")]), "sai thứ tự"),
            "submit sha 50 hex": (ledger([ev("init", 1), ev("submit", 1, sha="a" * 50)]), "sai thứ tự"),
            "reopen khi active": (ledger([ev("init", 1), ev("reopen", 1)]), "sai thứ tự"),
            "sự kiện lạ": (ledger([ev("init", 1), ev("skip", 1)]), "sai thứ tự"),
            "B4 init chu kỳ khi chưa xong": (
                ledger([ev("init", 1), ev("init", 1, "C-002")], cycle="C-002"),
                "chưa xong",
            ),
            "init nhảy số chu kỳ": (
                ledger([*completed()["history"], ev("init", 1, "C-003")], cycle="C-003"),
                "không phải chu kỳ kế (C-002)",
            ),
            "submitted lệch lịch sử": (
                ledger([ev("init", 1), ev("submit", 1, sha=SHA)], status="awaiting_approval", submitted={"sha": SHA2}),
                "lịch sử dựng ra",
            ),
            "không phải object": (ledger(["x"]), "không phải object"),
            "cycle sai dạng": (ledger([ev("init", 1, "C-1")]), "không phải object"),
        }
        for name, (led, why) in bad.items():
            with self.subTest(name):
                self.assertIn(why, xt.stage_problem(led))

    def test_plan_stage_marker(self):
        self.assertEqual(xt.plan_stage("# P\n> Giai đoạn sản phẩm: 2 (C-004) · khác\n"), [(2, "C-004")])
        self.assertEqual(xt.plan_stage("> Giai đoạn: G4 → G6\n"), [])
        two = "> Giai đoạn sản phẩm: 1 (C-001)\n## Lát 2\n> Giai đoạn sản phẩm: 2 (C-001)\n"
        self.assertEqual(xt.plan_stage(two), [(1, "C-001"), (2, "C-001")])
        tilde = "> Giai đoạn sản phẩm: 1 (C-001)\n~~~\n> Giai đoạn sản phẩm: 2 (C-001)\n```\n~~~\n"
        self.assertEqual(xt.plan_stage(tilde), [(1, "C-001")])  # fence ~~~ (``` bên trong không đóng nó)
        inner = "~~~\n```\n> Giai đoạn sản phẩm: 2 (C-001)\n~~~\n> Giai đoạn sản phẩm: 1 (C-001)\n"
        self.assertEqual(
            xt.plan_stage(inner), [(1, "C-001")]
        )  # ~~~ đóng đúng fence, dòng sau đó vẫn tính (review #328)
        nfd = unicodedata.normalize("NFD", "> Giai đoạn sản phẩm: 2 (C-003)")
        self.assertEqual(xt.plan_stage(nfd), [(2, "C-003")])

    def test_agent_session(self):
        with unittest.mock.patch.dict(os.environ, HUMAN):
            self.assertFalse(xt.agent_session())
        with unittest.mock.patch.dict(os.environ, {**HUMAN, "CLAUDECODE": "1"}):
            self.assertTrue(xt.agent_session())


class StageCliTest(TmpRepoCase):
    def setUp(self):
        super().setUp()
        self.init_repo()
        self.git("config", "user.email", "chu@example.invalid")
        self.git(
            "config", "user.name", "chu"
        )  # smoke tự `git commit` không qua `self.git` — CI không có user.name toàn cục
        self.git("config", "commit.gpgsign", "false")
        self.enterContext(unittest.mock.patch.dict(os.environ, {**HUMAN, "CLAUDE_PROJECT_DIR": str(self.repo)}))
        self.commit("khởi tạo")

    def commit(self, msg):
        (self.repo / "f.txt").write_text(msg + "\n", encoding="utf-8")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", msg)
        return self.git("rev-parse", "HEAD").strip()

    def stage(self, *args, agent=False):
        env = {"CLAUDE_CODE_SESSION_ID": "s-1"} if agent else {}
        with unittest.mock.patch.dict(os.environ, env):
            return run_main("stage", *args)

    def led(self):
        return json.loads((self.repo / xt.STAGE_LEDGER).read_text(encoding="utf-8"))

    def submit(self):
        sha = self.commit(f"bản {len(self.led()['history'])}")
        rc, _, err = self.stage("submit", "--evidence", "chạy `make demo`", agent=True)
        self.assertEqual(rc, 0, err)
        return sha

    def test_full_cycle_one_two_three_then_new_cycle(self):
        self.assertIn("Chưa dùng", self.stage("status")[1])
        self.assertEqual(self.stage("init", agent=True)[0], 0)
        mode = stat.S_IMODE((self.repo / xt.STAGE_LEDGER).stat().st_mode)
        umask = os.umask(0)
        os.umask(umask)
        self.assertEqual(mode, 0o666 & ~umask)  # sổ theo git: quyền theo umask như file khác, không 0600 của mkstemp
        rc, _, err = self.stage("init")
        self.assertEqual(rc, 2)
        self.assertIn("đã có (C-001, giai đoạn 1)", err)
        self.assertIn("giai đoạn 2–3 khoá", self.stage("status")[1])
        for n in (1, 2, 3):
            with self.subTest(stage=n):
                sha = self.submit()
                out = self.stage("status")[1]
                self.assertIn(f"giai đoạn {n} ", out)
                self.assertIn(f"chờ người duyệt bản {sha[:12]}", out)
                rc, _, err = self.stage("approve", "--sha", sha, "--note", "ok", agent=True)
                self.assertEqual(rc, 2)
                self.assertIn("chỉ người duyệt", err)
                rc, out, err = self.stage("approve", "--sha", sha[:7].upper(), "--note", "ok")
                self.assertEqual(rc, 0, err)
                if n == 1:
                    self.assertIn("giai đoạn 3 khoá", out)
        led = self.led()
        self.assertEqual((led["stage"], led["status"]), (3, "completed"))
        self.assertEqual([e["by"] for e in led["history"] if e["event"] == "approve"], ["chu@example.invalid"] * 3)
        self.assertIn("completed", self.stage("status")[1])
        self.assertEqual(self.stage("new-cycle", "--reason", "module lớn", agent=True)[0], 0)
        self.assertEqual((self.led()["cycle"], self.led()["stage"], self.led()["status"]), ("C-002", 1, "active"))
        rc, out, _ = self.stage("status", "--json")
        self.assertEqual(json.loads(out)["stage"]["cycle"], "C-002")

    def test_refusals_leave_ledger_untouched(self):
        rc, _, err = self.stage("submit", "--evidence", "x")
        self.assertIn("chỉ trình duyệt khi giai đoạn đang `active`", err)
        self.stage("init")
        before = self.led()
        (self.repo / "dở.txt").write_text("x", encoding="utf-8")
        self.assertIn("chưa commit", self.stage("submit", "--evidence", "x")[2])
        self.git("config", "status.showUntrackedFiles", "no")  # cấu hình không giấu được file chưa track
        self.assertIn("chưa commit", self.stage("submit", "--evidence", "x")[2])
        (self.repo / "dở.txt").unlink()
        self.assertIn("chỉ mở lại giai đoạn đang chờ duyệt", self.stage("reopen", "--reason", "x")[2])
        self.assertIn("không có giai đoạn chờ duyệt", self.stage("approve", "--sha", "abcdef1", "--note", "x")[2])
        self.assertIn("chỉ mở sau khi chu kỳ", self.stage("new-cycle", "--reason", "x")[2])
        self.assertEqual(self.led(), before)
        sha = self.submit()
        self.assertIn("cần ≥ 7 ký tự", self.stage("approve", "--sha", sha[:6], "--note", "x")[2])
        self.assertIn("cần ≥ 7 ký tự", self.stage("approve", "--sha", "", "--note", "x")[2])
        self.assertIn("không phải bản đã trình", self.stage("approve", "--sha", "0" * 7, "--note", "x")[2])
        self.assertIn("chỉ trình duyệt", self.stage("submit", "--evidence", "x")[2])  # đã chờ duyệt
        self.assertEqual(self.stage("reopen", "--reason", "chủ dự án muốn sửa form", agent=True)[0], 0)
        led = self.led()
        self.assertEqual((led["stage"], led["status"], led["submitted"]), (1, "active", None))
        self.assertEqual([e["event"] for e in led["history"]], ["init", "submit", "reopen"])

    def test_commit_hint_and_status_timeout(self):
        out = self.stage("init")[1]
        self.assertIn(f"commit + push `{xt.STAGE_LEDGER}`", out)
        self.assertNotIn("commit + push", self.stage("status")[1])
        self.assertNotIn("commit + push", self.stage("reopen", "--reason", "x")[1])  # từ chối: không gợi ý
        real = subprocess.run

        def slow(cmd, *a, **k):
            if cmd[:2] == ["git", "status"]:
                raise subprocess.TimeoutExpired(cmd, 30)
            return real(cmd, *a, **k)

        with unittest.mock.patch.object(xt.subprocess, "run", side_effect=slow):
            self.assertIn("quá 30 s", self.stage("submit", "--evidence", "x")[2])

    def test_submit_needs_final_verify_and_records_preview(self):
        """ADR-0058 lát C: dự án chạy vòng → `submit` đòi kiểm lại cuối xanh trên cây này; ghi `preview` của xt.yaml."""
        (self.repo / "xt.yaml").write_text("preview: make demo\n", encoding="utf-8")
        self.commit("xt.yaml")
        self.stage("init")
        rc, out, _ = self.stage("submit", "--evidence", "x")
        self.assertEqual(rc, 0)
        sub = self.led()["submitted"]
        self.assertEqual(
            (sub["preview"], sub["verified"]),
            ("make demo", "không có `.autopilot/state.json` ở cây này — không có kiểm lại cuối"),
        )
        self.assertIn("chạy thử: make demo", self.stage("status")[1])
        self.stage("reopen", "--reason", "sửa")
        xt.write_state({"active": False, "plan": "P.md"}, self.repo)
        busy = {"verdict": "continue", "reason": "còn T-002", "task": "T-002"}
        with unittest.mock.patch.object(xt, "_batch_verdict", return_value=busy):  # PLAN còn task (review #330)
            rc, _, err = self.stage("submit", "--evidence", "x")
        self.assertEqual(rc, 2)
        self.assertIn("vòng chưa xong (continue: còn T-002)", err)
        self.assertNotIn("loop resume", err)
        self.assertNotIn("PLAN mất", err)  # vòng còn việc: không kèm lối ra của vòng dừng (review #334)
        stopped = {"verdict": "blocked", "reason": "vòng lặp đã kết thúc — stopped"}
        with unittest.mock.patch.object(xt, "_batch_verdict", return_value=stopped):  # lối ra từ helper chung (#332)
            self.assertIn("PLAN mất/rỗng → `loop init --plan <mới>`", self.stage("submit", "--evidence", "x")[2])
        (self.repo / "P.md").write_text("- [ ] `T-001` x — Gate: `true`\n", encoding="utf-8")
        live = {"active": True, "plan": "P.md"}
        self.assertEqual(xt._halted_loop_exit(live, self.repo), xt.EXIT_UNBLOCK)  # vòng còn bật, PLAN còn
        spent = {**live, "iterations": 50, "max_iterations": 50}
        self.assertEqual(xt._halted_loop_exit(spent, self.repo), xt.EXIT_BUDGET)  # như `doctor`
        (self.repo / "P.md").unlink()
        self.assertIn("`loop stop` rồi", xt._halted_loop_exit(live, self.repo))  # vòng bật + PLAN mất
        self.assertIn("PLAN mất/rỗng", xt._halted_loop_exit(spent, self.repo))  # PLAN trước ngân sách (#333)
        xt.write_state(live, self.repo)  # đầu-cuối, verdict thật `blocked`: vòng bật + PLAN mất (review #334)
        self.assertIn("`loop stop` rồi", self.stage("submit", "--evidence", "x")[2])
        (self.repo / "P.md").write_text("- [ ] `T-001` x — Gate: `true`\n", encoding="utf-8")
        self.commit("PLAN")
        xt.write_state(spent, self.repo)  # verdict thật `budget`: lối ra `loop init`, không `unblock` (#333)
        err = self.stage("submit", "--evidence", "x")[2]
        self.assertIn(f"(budget: đã chạm trần 50 vòng) — {xt.EXIT_BUDGET}", err)
        self.assertNotIn("loop unblock", err)
        done = unittest.mock.patch.object(xt, "_batch_verdict", return_value={"verdict": "done", "reason": "x"})
        with done, unittest.mock.patch.object(xt, "final_check", return_value="kiểm lại cuối ĐỎ (T-001)"):
            rc, _, err = self.stage("submit", "--evidence", "x")
        self.assertEqual(rc, 2)
        self.assertIn("chưa trình được — kiểm lại cuối ĐỎ (T-001)", err)
        with done, unittest.mock.patch.object(xt, "final_check", return_value=None):
            self.assertEqual(self.stage("submit", "--evidence", "x")[0], 0)
        self.stage("reopen", "--reason", "x")
        pend = {"verdict": xt.PENDING_HUMAN, "reason": "T-9 chờ người"}
        with unittest.mock.patch.object(xt, "_batch_verdict", return_value=pend):  # chờ người vẫn trình được
            with unittest.mock.patch.object(xt, "final_check", return_value=None):
                self.assertEqual(self.stage("submit", "--evidence", "x")[0], 0)
        self.assertEqual(self.led()["submitted"]["verified"], "loop verify --all xanh trên cây này")
        with unittest.mock.patch.object(xt, "_xt_keys", side_effect=ValueError("utf-8")):
            self.assertEqual(xt._stage_submit_proof(self.tmp)["preview"], "")

    def test_submit_runs_preview_smoke(self):
        """ADR-0058 lát C (D-247): `preview_smoke` chạy trên bản trình — đỏ hay để lại thay đổi trong cây → không trình;
        chưa khai → trình được, sổ ghi rõ "không có"; xt.yaml hỏng → không trình."""
        self.stage("init")
        self.assertEqual(self.stage("submit", "--evidence", "x")[0], 0)
        self.assertIn("chưa khai `preview_smoke`", self.led()["submitted"]["smoke"])
        self.assertIn("smoke: không có", self.stage("status")[1])
        self.stage("reopen", "--reason", "x")
        (self.repo / "xt.yaml").write_text("preview_smoke: echo hong; exit 3\n", encoding="utf-8")
        self.commit("smoke đỏ")
        rc, _, err = self.stage("submit", "--evidence", "x")
        self.assertEqual(rc, 2)
        self.assertIn("smoke `echo hong; exit 3` exit 3: hong", err)
        self.assertEqual(self.led()["status"], "active")  # không ghi sổ
        (self.repo / "xt.yaml").write_text("preview_smoke: touch smoke-out.txt\n", encoding="utf-8")
        self.commit("smoke bẩn cây")
        self.assertIn("để lại thay đổi trong cây", self.stage("submit", "--evidence", "x")[2])
        (self.repo / "smoke-out.txt").unlink()
        (self.repo / "xt.yaml").write_text("preview_smoke: test -f f.txt\n", encoding="utf-8")
        self.commit("smoke xanh")
        self.assertEqual(self.stage("submit", "--evidence", "x")[0], 0)
        self.assertEqual(self.led()["submitted"]["smoke"], "`test -f f.txt` exit 0")
        self.assertIn("smoke: `test -f f.txt` exit 0", self.stage("status")[1])
        self.stage("reopen", "--reason", "x")
        with unittest.mock.patch.object(xt, "_xt_keys", side_effect=ValueError("utf-8")):
            self.assertIn("không đọc được xt.yaml (utf-8)", self.stage("submit", "--evidence", "x")[2])
        led = self.led()
        led["submitted"] = {**led["history"][1], "sha": "c" * 40}  # bản trình trước D-247: không có trường smoke
        led["status"] = "awaiting_approval"
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            xt._stage_print(led, False)
        self.assertIn("smoke: (bản trình trước D-247)", out.getvalue())

    def test_preview_smoke_head_and_state(self):
        """Review #336: smoke tự commit → HEAD lệch bản trình → không trình; ghi vào thư mục `.gitignore` → trình được;
        sổ không `active` → từ chối TRƯỚC khi chạy smoke."""
        self.stage("init")
        (self.repo / "smoke.sh").write_text("echo moved >> f.txt; git commit -qam smoke-artefact\n", encoding="utf-8")
        (self.repo / "xt.yaml").write_text("preview_smoke: bash smoke.sh\n", encoding="utf-8")
        self.commit("smoke commit")
        rc, _, err = self.stage("submit", "--evidence", "x")
        self.assertEqual(rc, 2)
        self.assertIn("HEAD đổi trong lúc smoke `bash smoke.sh` chạy", err)
        self.assertEqual(self.led()["status"], "active")
        (self.repo / ".gitignore").write_text("out/\n", encoding="utf-8")
        (self.repo / "smoke.sh").write_text("mkdir -p out; date > out/report.txt\n", encoding="utf-8")
        self.commit("smoke ra thư mục bỏ qua")
        self.assertEqual(self.stage("submit", "--evidence", "x")[0], 0)
        mark = self.repo.parent / "smoke-ran.txt"
        (self.repo / "smoke.sh").write_text(f"date >> {mark}\n", encoding="utf-8")
        self.commit("smoke ghi dấu")  # sổ đang `awaiting_approval`
        self.assertIn("chỉ trình duyệt khi giai đoạn đang `active`", self.stage("submit", "--evidence", "x")[2])
        self.assertFalse(mark.exists())
        self.stage("reopen", "--reason", "x")
        xt.write_state({"active": False, "plan": "P.md"}, self.repo)
        busy = {"verdict": "continue", "reason": "còn T-002", "task": "T-002"}
        with unittest.mock.patch.object(xt, "_batch_verdict", return_value=busy):  # kiểm lại cuối trước smoke
            self.assertIn("vòng chưa xong", self.stage("submit", "--evidence", "x")[2])
        self.assertFalse(mark.exists())

    def test_gate_tail_redacts_then_cuts(self):
        """Review #336: che bí mật trên cả output rồi mới cắt đuôi; hết giờ giữ dòng `timeout:`."""
        pem = "-----BEGIN PRIVATE KEY-----\nQUJDREVGR0g=\nSUpLTE1OT1A=\n-----END PRIVATE KEY-----\nfail"
        self.assertEqual(
            xt._gate_tail(1, pem), "-----BEGIN PRIVATE KEY----- *** fail"
        )  # cắt trước → lộ thân; chữ sau giữ
        self.assertEqual(xt._gate_tail(1, "deploy --password\nhunter2-secret"), "deploy --password ***")
        self.assertEqual(xt._gate_tail(124, "timeout: quá 1 giây\na\nb\nc"), "timeout: quá 1 giây a b c")
        self.assertEqual(xt._gate_tail(124, "timeout: quá 1 giây\na"), "timeout: quá 1 giây a")
        self.assertEqual(xt._gate_tail(1, "x\na\nb\nc"), "a b c")

    def test_autopilot_dir_does_not_dirty_submit(self):
        self.git("rm", "-q", "--cached", "f.txt")  # repo không ignore .autopilot/: khoá state.lock nằm ở đó
        self.commit("lại")
        self.stage("init")
        self.assertTrue((self.repo / ".autopilot" / xt.STATE_LOCK_FILE).exists())
        self.assertEqual(self.stage("submit", "--evidence", "x")[0], 0)

    def test_adopt_needs_human_and_evidence(self):
        self.assertIn("cần `--evidence`", self.stage("init", "--adopt", "2")[2])
        self.assertIn("chỉ người duyệt", self.stage("init", "--adopt", "2", "--evidence", "v1.0", agent=True)[2])
        with self.assertRaises(SystemExit):  # viết tắt không được (`--ado`): guard so chữ đầy đủ
            run_main("stage", "init", "--ado", "2", "--evidence", "v")
        self.assertEqual(self.stage("init", "--adopt", "2", "--evidence", "tag v1.0 + GO-NO-GO")[0], 0)
        first = self.led()["history"][0]
        self.assertEqual((self.led()["stage"], first["event"], first["by"]), (2, "adopt", "chu@example.invalid"))

    def test_corrupt_or_removed_ledger_blocks(self):
        p = self.repo / xt.STAGE_LEDGER
        p.parent.mkdir(parents=True)
        p.write_text("{", encoding="utf-8")
        self.assertIn("không đọc được", self.stage("status")[2])
        p.write_text(json.dumps(ledger(stage=3)), encoding="utf-8")
        rc, _, err = self.stage("status")
        self.assertEqual(rc, 2)
        self.assertIn("hỏng: lịch sử dựng ra", err)
        p.unlink()
        self.stage("init")
        self.commit("sổ")
        self.git("mv", "docs/autopilot", "docs/plans")  # C2: dời thư mục không tắt được khoá
        rc, _, err = self.stage("status")
        self.assertEqual(rc, 2)
        self.assertIn("vắng nhưng có trong lịch sử git", err)

    def test_branch_before_ledger_still_locked(self):
        """C1 (review #327): nhánh tách trước commit sổ không thoát khoá."""
        self.git("branch", "cu")
        self.stage("init")
        self.commit("sổ")
        self.git("switch", "-q", "cu")
        rc, _, err = self.stage("status")
        self.assertEqual(rc, 2)
        self.assertIn("lịch sử git", err)
        self.assertEqual(xt._release_stage(self.repo)["result"], "FAIL")

    def test_no_commit_and_approver_fallback(self):
        self.stage("init")
        with unittest.mock.patch.object(xt, "_git_head", return_value=None):
            self.assertIn("không có commit", self.stage("submit", "--evidence", "x")[2])
        sha = self.submit()
        empty = subprocess.CompletedProcess([], 0, "", "")
        named = subprocess.CompletedProcess([], 0, "Chủ Dự Án\n", "")
        real = subprocess.run

        def faking(email, name):
            def fake(cmd, *a, **k):  # chỉ `git config user.*` giả; lệnh khác chạy thật
                hit = {"user.email": email, "user.name": name}.get(cmd[-1]) if cmd[:2] == ["git", "config"] else None
                if isinstance(hit, Exception):
                    raise hit
                return hit or real(cmd, *a, **k)

            return unittest.mock.patch.object(xt.subprocess, "run", side_effect=fake)

        with faking(OSError("x"), empty):
            self.assertIn("không biết người duyệt", self.stage("approve", "--sha", sha, "--note", "x")[2])
        with faking(empty, named):  # user.email trống → user.name
            self.assertEqual(self.stage("approve", "--sha", sha, "--note", "x")[0], 0)
        self.assertEqual(self.led()["history"][-1]["by"], "Chủ Dự Án")

    def test_update_holds_lock_and_refuses_invalid_result(self):
        held = []

        @contextlib.contextmanager
        def lock(base):
            held.append(True)
            yield
            held.append(False)

        with unittest.mock.patch.object(xt, "_state_lock", lock):
            xt.update_stage(self.repo, lambda led: (self.assertEqual(held, [True]), ledger())[1])
        self.assertEqual(held, [True, False])
        with self.assertRaises(xt.StageError):
            xt.update_stage(self.repo, lambda led: {"schema": 1})
        self.assertEqual(json.loads((self.repo / xt.STAGE_LEDGER).read_text(encoding="utf-8")), ledger())

    def test_failed_write_leaves_no_empty_ledger(self):
        with unittest.mock.patch.object(xt, "write_atomic", side_effect=OSError(28, "đầy đĩa")):
            self.assertIn("đầy đĩa", self.stage("init")[2])
        self.assertFalse((self.repo / xt.STAGE_LEDGER).exists())
        self.stage("init")
        with unittest.mock.patch.object(xt, "write_atomic", side_effect=OSError(28, "đầy đĩa")):
            with self.assertRaises(OSError):
                xt.update_stage(self.repo, lambda led: led)
        self.assertEqual(self.led()["history"][0]["event"], "init")  # sổ có sẵn không bị xoá khi ghi lỗi

    def test_stage_uses_worktree_root_and_no_abbrev(self):
        other = self.tmp / "khac"
        other.mkdir()
        with unittest.mock.patch.object(xt, "loop_root", return_value=other):
            self.assertEqual(self.stage("init")[0], 0)
        self.assertTrue((other / xt.STAGE_LEDGER).exists())
        self.assertFalse((self.repo / xt.STAGE_LEDGER).exists())
        with self.assertRaises(SystemExit):
            run_main("stage", "approve", "--sh", "abcdef1", "--note", "x")

    def test_seen_message_names_ref(self):
        self.git("switch", "-q", "-c", "thu")
        self.stage("init")
        self.commit("sổ ở nhánh thử")
        self.git("switch", "-q", "main")
        err = self.stage("status")[2]
        self.assertIn("refs/heads/thu", err)
        self.assertIn("người khôi phục sổ", err)

    def test_unknown_subcommand_is_read_only(self):
        args = unittest.mock.Mock(stage_cmd="khác")
        self.assertIsNone(xt._stage_dispatch(args, self.repo))


class StageLockTest(TmpRepoCase):
    """Giai đoạn sau khoá ở lối vào vòng (`loop init/next/record`; verdict không đọc khoá — D-241) và ở `release-check`."""

    PLAN = "docs/autopilot/PLAN.md"

    def setUp(self):
        super().setUp()
        self.init_repo()
        self.git("config", "user.email", "chu@example.invalid")
        self.enterContext(unittest.mock.patch.dict(os.environ, {**HUMAN, "CLAUDE_PROJECT_DIR": str(self.repo)}))
        self.enterContext(unittest.mock.patch.object(xt, "loop_root", lambda base: base))

    def plan(self, *markers, tasks=("T-001",)):
        p = self.repo / self.PLAN
        p.parent.mkdir(parents=True, exist_ok=True)
        lines = ["# PLAN", *markers, ""] + [f"- [ ] `{t}` việc — Gate: `true`" for t in tasks]
        p.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def write_ledger(self, led):
        p = self.repo / xt.STAGE_LEDGER
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(led), encoding="utf-8")

    def problem(self):
        return xt.stage_plan_problem(self.repo, self.PLAN)

    def test_plan_problem_cases(self):
        self.plan()
        self.assertEqual(self.problem(), "")  # không dùng sổ
        self.write_ledger(ledger())
        self.assertIn("phải khai đúng một dòng `Giai đoạn sản phẩm: 1 (C-001)` (đang có 0)", self.problem())
        self.plan("> Giai đoạn sản phẩm: 2 (C-001)")
        self.assertIn("khai giai đoạn 2 (C-001) nhưng đang mở giai đoạn 1", self.problem())
        self.plan("> Giai đoạn sản phẩm: 1 (C-002)")  # chu kỳ khác
        self.assertIn("khai giai đoạn 1 (C-002) nhưng đang mở giai đoạn 1 (C-001)", self.problem())
        self.plan("> Giai đoạn sản phẩm: 1 (C-001)", "## Lát 2", "> Giai đoạn sản phẩm: 2 (C-001)")  # ca D
        self.assertIn("(đang có 2)", self.problem())
        self.plan("> Giai đoạn sản phẩm: 1 (C-001)")
        self.assertEqual(self.problem(), "")
        self.assertIn("không đọc được", xt.stage_plan_problem(self.repo, "thiếu.md"))
        self.write_ledger(ledger([ev("init", 1), *approve(1)], stage=2))
        self.assertIn("giai đoạn 1 của C-001 đã được người duyệt — PLAN đợt mới khai", self.problem())
        self.write_ledger({"schema": 9})
        self.assertIn("hỏng", self.problem())
        self.write_ledger(completed())  # bảo trì/cải tiến chu kỳ đã phát hành vẫn chạy (review #327)
        self.plan("> Giai đoạn sản phẩm: 3 (C-001)")
        self.assertEqual(self.problem(), "")

    def test_skill_plans_need_their_stage(self):
        """D-246: PLAN của `/complete` (`PLAN-harden-*`) từ giai đoạn 2, của `/optimize` (`PLAN-opt-*`) chỉ giai đoạn 3."""
        cases = [  # (tên PLAN, giai đoạn mở, được chạy?)
            ("PLAN-harden-2026-10-29.md", 1, False),
            ("PLAN-harden.md", 1, False),
            ("PLAN-harden-x.md", 2, True),
            ("PLAN-opt-2026-10-29.md", 2, False),
            ("PLAN-opt-x.md", 3, True),
            ("PLAN-options.md", 1, True),  # chỉ đúng tiền tố skill đặt
            ("PLAN-hardening.md", 1, True),
            ("plan-Harden-x.md", 1, False),  # macOS/Windows: cùng file với PLAN-harden-x.md (review #338)
            ("PLAN-OPT-x.md", 2, False),
            ("PLAN-mvp.md", 1, True),
        ]
        hist = {1: [ev("init", 1)], 2: [ev("init", 1), *approve(1)], 3: [ev("init", 1), *approve(1), *approve(2)]}
        for name, stage, ok in cases:
            with self.subTest(name=name, stage=stage):
                self.PLAN = f"docs/autopilot/{name}"
                self.write_ledger(ledger(hist[stage], stage=stage))
                self.plan(f"> Giai đoạn sản phẩm: {stage} (C-001)")
                why = self.problem()
                self.assertEqual(why == "", ok, why)
                if not ok:
                    self.assertIn(f"đang mở giai đoạn {stage} (C-001)", why)
                    self.assertIn("/optimize" if "opt" in name.lower() else "/complete", why)
        self.PLAN = "docs/autopilot/PLAN-opt-y.md"  # giai đoạn 3 đã xong: bảo trì vẫn tối ưu được
        self.write_ledger(completed())
        self.plan("> Giai đoạn sản phẩm: 3 (C-001)")
        self.assertEqual(self.problem(), "")
        self.PLAN = "docs/autopilot/PLAN-harden-z.md"  # lối vào vòng thật từ chối, không ghi state
        self.write_ledger(ledger())
        self.plan("> Giai đoạn sản phẩm: 1 (C-001)")
        rc, _, err = run_main("loop", "init", "--plan", self.PLAN)
        self.assertEqual(rc, 2)
        self.assertIn("là PLAN của `/complete`", err)
        self.assertIsNone(xt.read_state(self.repo))

    def test_loop_entry_points_refuse_locked_stage(self):
        self.write_ledger(ledger())
        self.plan("> Giai đoạn sản phẩm: 2 (C-001)")
        rc, _, err = run_main("loop", "init", "--plan", self.PLAN)
        self.assertEqual(rc, 2)
        self.assertIn("giai đoạn sau khoá", err)
        self.assertIsNone(xt.read_state(self.repo))
        self.plan("> Giai đoạn sản phẩm: 1 (C-001)")
        self.assertEqual(run_main("loop", "init", "--plan", self.PLAN)[0], 0)
        self.assertEqual(run_main("loop", "next")[0], 0)
        self.assertEqual(xt.loop_verdict(self.repo)["verdict"], "continue")
        self.plan("> Giai đoạn sản phẩm: 2 (C-001)")  # sửa PLAN sau init
        rc, _, err = run_main("loop", "next")
        self.assertEqual(rc, 2)
        self.assertIn("đang mở giai đoạn 1", err)
        rc, _, err = run_main("loop", "record", "--task", "T-001", "--", "true")
        self.assertEqual(rc, 2)
        self.assertIn("đang mở giai đoạn 1", err)
        self.assertFalse((self.repo / ".autopilot" / "evidence" / "T-001.json").exists())

    def step(self):
        """`next-step` build trên dữ kiện thật của repo (sổ, vòng, kiểm lại cuối); sổ audit/MUST coi như sạch."""
        f = xt.next_step_facts(self.repo, xt.read_state(self.repo) or {}, "S.md", [])
        f.update(
            audit={
                **f["audit"],
                "exists": True,
                "sha256": "0" * 64,
                "scanned": ["b" * 40],
                "errors": [],
                "open": 0,
                "debt": {},
            },
            open_must=0,
        )
        return xt.next_step(f)

    def test_submit_then_commit_ledger_still_waits(self):
        """Review #330: verify xanh → `stage-submit`; trình → `wait-approval`; commit sổ (đổi HEAD) vẫn `wait-approval`,
        không bắt chạy lại mọi Gate. Đường nối thật `next_step_facts` → `stage_facts` (SHA bản trình)."""
        self.assertEqual(run_main("stage", "init")[0], 0)
        self.plan("> Giai đoạn sản phẩm: 1 (C-001)")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "khởi tạo")
        self.assertEqual(run_main("loop", "init", "--plan", self.PLAN)[0], 0)
        self.assertEqual(run_main("loop", "record", "--task", "T-001", "--", "true")[0], 0)
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "T-001")
        self.assertEqual(run_main("loop", "verify", "--all")[0], 0)
        self.assertEqual(self.step()["action"], "stage-submit")
        self.assertEqual(run_main("stage", "submit", "--evidence", "demo")[0], 0)
        sha = self.git("rev-parse", "HEAD").strip()
        out = self.step()
        self.assertEqual(out["action"], "wait-approval")
        self.assertIn(sha[:12], out["reason"])
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "sổ: trình MVP")
        self.assertEqual(self.step()["action"], "wait-approval")
        f = xt.next_step_facts(self.repo, xt.read_state(self.repo), "S.md", [])
        self.assertEqual(f["stage"]["sha"], sha)
        pending = xt.next_step(
            {
                **f,
                "audit": {
                    **f["audit"],
                    "exists": True,
                    "sha256": "0" * 64,
                    "scanned": ["b" * 40],
                    "errors": [],
                    "open": 0,
                    "debt": {},
                },
                "open_must": 0,
            }
            | {"stage": {**f["stage"], "status": "active", "sha": None}}
            | {"verdict": {"verdict": xt.PENDING_HUMAN, "reason": "T-009 chờ người duyệt pháp lý"}, "final_check": None}
        )
        self.assertIn("T-009 chờ người duyệt pháp lý", pending["reason"])  # không mất lý do chờ người (review #330)
        sub = json.loads((self.repo / xt.STAGE_LEDGER).read_text(encoding="utf-8"))["submitted"]
        with unittest.mock.patch.object(xt, "_changed_since", return_value=None):  # SHA mất (squash, clone mới)
            self.assertEqual(xt._stage_changed(self.repo, sub), [])  # vân tay nội dung khớp
            self.assertIsNone(xt._stage_changed(self.repo, {**sub, "tree": None}))  # bản trình cũ: không so được
            self.assertEqual(xt._stage_changed(self.repo, {**sub, "tree": "0" * 64}), [xt.STAGE_DIFF_UNKNOWN])
        self.assertEqual(xt._stage_changed(self.repo, {**sub, "tree": "0" * 64}), [xt.STAGE_DIFF_UNKNOWN])
        (self.repo / "moi.py").write_text("x = 1\n", encoding="utf-8")  # mã đổi sau bản trình → mở lại giai đoạn
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "mã mới")
        out = self.step()
        self.assertEqual(out["action"], "stage-reopen")
        self.assertIn("moi.py", out["reason"])

    def test_after_human_approval_switch_plan_with_force(self):
        """Ca W (review #327), D-241: người duyệt khi vòng giai đoạn 1 còn task → `record` từ chối kèm lối ra đúng; verdict và
        mọi lối ra của vòng giữ như cũ (không đọc khoá); đổi PLAN khi vòng còn bật bằng `--force` (LOOP-HARNESS-024)."""
        self.write_ledger(ledger())
        self.plan("> Giai đoạn sản phẩm: 1 (C-001)")
        self.assertEqual(run_main("loop", "init", "--plan", self.PLAN, "--single-session")[0], 0)
        self.write_ledger(ledger([ev("init", 1), *approve(1)], stage=2))
        rc, _, err = run_main("loop", "record", "--task", "T-001", "--", "true")
        self.assertEqual(rc, 2)
        self.assertIn("đã được người duyệt — PLAN đợt mới khai `Giai đoạn sản phẩm: 2 (C-001)` rồi", err)
        self.assertIn("vòng cũ còn bật: thêm `--force`", err)
        self.assertEqual(xt.loop_verdict(self.repo)["verdict"], "continue")  # verdict không đọc khoá (D-241)
        two = "docs/autopilot/PLAN-2.md"
        text = "# P\n> Giai đoạn sản phẩm: 2 (C-001)\n\n- [ ] `T-002` v — Gate: `true`\n"
        (self.repo / two).write_text(text, encoding="utf-8")
        rc, _, err = run_main("loop", "init", "--plan", two, "--single-session")
        self.assertEqual(rc, 2)  # vòng đang sống không bị ghi đè khi thiếu `--force`
        self.assertIn("`loop init --force`", err)
        self.assertEqual(run_main("loop", "init", "--plan", two, "--single-session", "--force")[0], 0)
        self.assertEqual(xt.read_state(self.repo)["plan"], two)

    def test_fenced_example_and_new_cycle_hint(self):
        self.write_ledger(ledger())
        self.plan("> Giai đoạn sản phẩm: 1 (C-001)", "```markdown", "> Giai đoạn sản phẩm: 2 (C-001)", "```")
        self.assertEqual(self.problem(), "")  # ví dụ trong code fence không tính
        self.write_ledger(completed())
        self.plan("> Giai đoạn sản phẩm: 1 (C-002)")
        self.assertIn("chu kỳ mới: `xt.py stage new-cycle", self.problem())
        fake = completed()
        fake["status"] = "active"  # lịch sử xong cả ba mà sổ ghi active (đột biến N10)
        self.assertIn("lịch sử dựng ra C-001/3/completed", xt.stage_problem(fake))

    def test_release_row(self):
        row = xt._release_stage(self.repo)
        self.assertEqual((row["result"], row["level"]), ("N/A", "SHOULD"))
        self.write_ledger(ledger())
        row = xt._release_stage(self.repo)
        self.assertEqual(row["result"], "FAIL")
        self.assertIn("MVP chưa mở Production", row["evidence"])
        waiting = ledger([ev("init", 1), ev("submit", 1, sha=SHA)], status="awaiting_approval", submitted={"sha": SHA})
        self.write_ledger(waiting)  # MVP chờ duyệt vẫn chưa phát hành được
        self.assertEqual(xt._release_stage(self.repo)["result"], "FAIL")
        self.write_ledger(ledger([ev("init", 1), *approve(1)], stage=2))
        self.assertEqual(xt._release_stage(self.repo)["result"], "PASS")
        self.write_ledger(completed())
        self.assertEqual(xt._release_stage(self.repo)["result"], "PASS")
        self.write_ledger({})
        self.assertEqual(xt._release_stage(self.repo)["result"], "FAIL")

    def test_git_unavailable_means_never_seen(self):
        with unittest.mock.patch.object(xt, "_git", side_effect=OSError("không có git")):
            self.assertEqual(xt._stage_git_seen(self.repo), "")

    def test_ledger_not_in_tree_fingerprint(self):
        self.plan()
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "c")
        before = xt.tree_fingerprint(self.repo)
        self.write_ledger(ledger())
        self.assertEqual(xt.tree_fingerprint(self.repo), before)


def _load_guard():
    sys.path.insert(0, str(ROOT / ".claude" / "hooks"))
    import guard as g

    return g


class StageGuardTest(unittest.TestCase):
    """Guard (lớp chặn nhầm, D-015): agent không duyệt giai đoạn, không ghi tay sổ (ADR-0058)."""

    def setUp(self):
        self.g = _load_guard()
        env = {"CLAUDE_PROJECT_DIR": str(ROOT), "XT_GUARD_POLICY": ""}
        self.enterContext(unittest.mock.patch.dict(os.environ, env))

    def decide(self, cmd):
        return dict(self.g.apply_policy(self.g.bash_decision(cmd, str(ROOT), None))).get("decision")

    def test_approve_and_adopt_denied(self):
        for cmd in (
            "python3 scripts/xt.py stage approve --sha abc1234 --note ok",
            "env A=1 python3 .xtemplates/scripts/xt.py stage init --adopt 2 --evidence v1",
            "cd . && python3 /x/xt.py stage init --adopt=3 --evidence v",
        ):
            with self.subTest(cmd=cmd):
                self.assertEqual(self.decide(cmd), "deny")

    def test_agent_steps_and_reads_allowed(self):
        for cmd in (
            "python3 scripts/xt.py stage status",
            "python3 scripts/xt.py stage submit --evidence demo",
            "python3 scripts/xt.py stage init",
            "python3 scripts/xt.py loop status",
            "grep approve scripts/xt.py",
            "cat docs/autopilot/STAGE.json",
        ):
            with self.subTest(cmd=cmd):
                self.assertNotEqual(self.decide(cmd), "deny")

    def test_handwrite_ledger_denied(self):
        self.assertEqual(self.g.classify_path(xt.STAGE_LEDGER), "evidence")
        self.assertEqual(self.g.STAGE_LEDGER, xt.STAGE_LEDGER)
        self.assertEqual(self.decide("sed -i s/1/3/ docs/autopilot/STAGE.json"), "deny")
        action, why = self.g.edit_decision(str(ROOT / xt.STAGE_LEDGER), str(ROOT))
        self.assertEqual(action, "ask")
        self.assertIn("xt.py stage", why)


if __name__ == "__main__":
    unittest.main()
