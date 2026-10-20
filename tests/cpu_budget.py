"""Kiểm "không bậc hai" bằng tỉ lệ đo trong cùng tiến trình, không bằng ngưỡng giây cứng (AUD-TEST-008).

Ngưỡng tuyệt đối (`assertLess(process_time() - t0, 2.0)`) đỏ ngẫu nhiên khi chạy dưới `coverage run` trên runner chung
(CI #170: 2,013 s ≥ 2,0 s). Ở đây đo cùng việc ở cỡ `n` và `4n`: tuyến tính tăng ~4 lần, bậc hai ~16 lần; ngưỡng
`10 × max(cost(n), FLOOR) + SLACK` nằm giữa. Máy chậm làm chậm cả hai lần đo như nhau nên tỉ lệ không đổi.

Độ nhạy: mã bậc hai bị bắt khi `cost(n) > SLACK / 6` (~0,08 s), tức `cost(4n)` > ~1,3 s — ngang ngưỡng tuyệt đối cũ
(1–3 s ở cỡ lớn). Vì vậy cỡ lớn `4n` ở mỗi test giữ đúng cỡ đầu vào của test cũ.
"""

from __future__ import annotations

import time
import unittest
from typing import Callable

FACTOR = 4  # cỡ lớn = FACTOR × cỡ nhỏ
RATIO = 10  # giữa FACTOR (tuyến tính) và FACTOR**2 (bậc hai)
FLOOR = 0.02  # giây: lần đo nhỏ quá ngắn thì nhiễu đồng hồ chiếm phần lớn
SLACK = 0.5  # giây: nhiễu tuyệt đối (GC, cache) của lần đo lớn


def cost(work: Callable[[int], object], n: int, clock: Callable[[], float] = time.process_time) -> float:
    t0 = clock()
    work(n)
    return clock() - t0


def assert_not_quadratic(
    tc: unittest.TestCase,
    work: Callable[[int], object],
    n: int,
    clock: Callable[[], float] = time.process_time,
    ratio: float = RATIO,
) -> None:
    """`work(FACTOR*n)` tốn CPU < `ratio` × `work(n)` (+ sàn/nhiễu) — đỏ khi `work` bậc hai trở lên theo `n`.

    Test chỉ canh hàm mũ (ngân sách quét) có thể nới `ratio` tới 40 (cho phép bậc hai, FACTOR**2 = 16 lần) — hàm mũ
    vẫn vượt xa."""
    small = max(cost(work, n, clock), FLOOR)
    big = cost(work, FACTOR * n, clock)
    tc.assertLess(big, small * ratio + SLACK, f"cỡ {FACTOR * n}: {big:.3f} s; cỡ {n}: {small:.3f} s — bậc hai?")
