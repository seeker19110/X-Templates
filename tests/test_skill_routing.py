"""Test kích hoạt skill tất định (XC-DOCAI-025): câu người dùng hay nói → skill mong đợi đứng đầu theo so khớp từ vựng
với `description` (TF-IDF, không gọi model); hai `description` gần trùng bị báo. Tầng hành vi (gọi model, `claude plugin
eval`) để ở eval riêng — đây chỉ bắt hai lỗi thường gặp: description thiếu từ người dùng hay nói, và hai skill giành nhau.

Thêm skill mới → thêm ≥ 2 câu vào PROMPTS (test đỏ nếu thiếu). Đổi `description` làm test đỏ → sửa description, không sửa câu
cho khớp; thay đổi bị loại ghi vào `.out-of-scope/` (XC-DOCAI-025)."""

from __future__ import annotations

import collections
import math
import re
import unicodedata
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / ".claude" / "skills"
MIN_RANK1 = 0.95  # tỉ lệ câu mà skill mong đợi đứng đầu; đo 2026-10-31: 32/32 (16 skill), 20/20 (10 skill)
MAX_PAIR_COSINE = 0.5  # hai description giống nhau hơn mức này là giành nhau; đo 2026-10-31: cao nhất 0,24
STOP = set(
    "và khi cho của là có không một các những được theo trong với để thì hoặc người dùng gõ này đó từ ra vào lên sau"
    " trước rồi mới nếu như cả mọi đã sẽ đang bị nhưng vì do tới về hay hơn nhất chỉ còn".split()
)
PROMPTS = {
    "adr": ["ghi lại quyết định kiến trúc chọn PostgreSQL", "tạo ADR cho việc đổi framework"],
    "audit": ["audit toàn diện dự án về bảo mật và chất lượng mã", "rà soát CI/CD, phụ thuộc, tài liệu của cả repo"],
    "autopilot": ["chạy tự động làm hết các task trong kế hoạch", "tự làm vòng lặp build đến khi hết việc"],
    "blueprint": ["dự án còn thiếu gì", "ghép blueprint cho web app thương mại điện tử"],
    "complete": ["hoàn thiện dự án để phát hành", "harden trước khi release, trả nợ review"],
    "gate": ["kiểm tra trước khi đẩy", "chạy lint typecheck test trước khi mở PR"],
    "handover": ["bàn giao, dừng ở đây", "wind-down cập nhật PROGRESS"],
    "optimize": ["tối ưu vì release-check báo perf FAIL", "ngân sách hiệu năng đang đỏ, cần profile"],
    "research": ["nên dùng thư viện nào cho xác thực", "xác minh chuẩn và luật từ nguồn sống"],
    "review": ["có bug không trong diff này", "rà nhanh diff PR"],
    "debug": ["test đỏ không rõ vì sao", "sao cái này hỏng, fix bug giúp"],
    "tdd": ["viết test trước rồi mới code", "làm TDD cho parser tính tiền"],
    "ui-verify": ["xem thử trên trình duyệt có vỡ layout không", "kiểm giao diện trang đăng nhập"],
    "upgrade": ["nâng cấp dependencies lên bản mới nhất", "update dependencies vì runtime sắp hết hỗ trợ"],
    "migrate-db": ["đổi tên cột trong bảng users", "viết migration thêm index cho bảng lớn"],
    "incident": ["production sập, xử lý sự cố", "viết post-mortem cho sự cố hôm qua"],
}


def tokens(text: str) -> list[str]:
    text = unicodedata.normalize("NFC", text).lower()  # chữ Việt dạng NFD (dấu tách rời) không bị cắt vụn
    return [w for w in re.findall(r"[^\W\d_]+", text) if len(w) > 1 and w not in STOP]


def skill_docs() -> dict[str, list[str]]:
    out = {}
    for p in sorted(SKILLS.glob("*/SKILL.md")):
        m = re.search(r"^description:\s*(.*)$", p.read_text(encoding="utf-8"), re.M)
        out[p.parent.name] = tokens(p.parent.name.replace("-", " ") + " " + (m.group(1) if m else ""))
    return out


def tfidf(docs: dict[str, list[str]]) -> tuple[dict[str, float], dict[str, dict[str, float]]]:
    df = collections.Counter(w for d in docs.values() for w in set(d))
    idf = {w: math.log((len(docs) + 1) / (c + 0.5)) for w, c in df.items()}
    vecs = {}
    for name, d in docs.items():
        v = {w: (1 + math.log(c)) * idf[w] for w, c in collections.Counter(d).items()}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        vecs[name] = {w: x / norm for w, x in v.items()}
    return idf, vecs


def ranked(query: str, idf: dict[str, float], vecs: dict[str, dict[str, float]]) -> list[str]:
    q = set(tokens(query))
    return sorted(vecs, key=lambda k: (-sum(idf.get(w, 0.0) * vecs[k].get(w, 0.0) for w in q), k))


class SkillRoutingTest(unittest.TestCase):
    def setUp(self) -> None:
        self.docs = skill_docs()
        self.idf, self.vecs = tfidf(self.docs)

    def test_every_skill_has_prompts(self) -> None:
        missing = sorted(k for k in self.docs if len(PROMPTS.get(k, [])) < 2)
        self.assertEqual(missing, [], "skill thiếu ≥ 2 câu mẫu trong PROMPTS")

    def test_expected_skill_ranks_first(self) -> None:
        misses, total = [], 0
        for skill, prompts in PROMPTS.items():
            if skill not in self.docs:  # skill chưa có trong bản này (vd nhánh cũ) — bỏ qua câu của nó
                continue
            for q in prompts:
                total += 1
                top = ranked(q, self.idf, self.vecs)[:3]
                if top[0] != skill:
                    misses.append(f"{skill}: {q!r} → {top}")
        self.assertGreater(total, 0)
        self.assertGreaterEqual((total - len(misses)) / total, MIN_RANK1, "\n".join(misses))

    def test_tokens_ignore_unicode_form(self) -> None:
        nfc = "kiểm giao diện"
        self.assertEqual(tokens(unicodedata.normalize("NFD", nfc)), tokens(nfc))

    def test_descriptions_do_not_collide(self) -> None:
        names = sorted(self.vecs)
        close = [
            f"{a} ~ {b}: {cos:.2f}"
            for i, a in enumerate(names)
            for b in names[i + 1 :]
            if (cos := sum(x * self.vecs[b].get(w, 0.0) for w, x in self.vecs[a].items())) >= MAX_PAIR_COSINE
        ]
        self.assertEqual(close, [], "hai description quá giống nhau — skill sẽ giành nhau")


if __name__ == "__main__":
    unittest.main()
