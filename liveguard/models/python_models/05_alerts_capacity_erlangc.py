"""
05_alerts_capacity_erlangc.py
=============================

人工复核坐席容量模型（Erlang-C）。

场景：
* 平均每 1,000 路并发直播，每分钟产生 α 条需复核告警
* 每条复核平均处理时长 AHT = 90 s
* 目标：≥ 90% 告警 60s 内响应

求：最少坐席 N。

数值稳定公式（使用对数递推避免大 N 阶乘溢出）：
    P_k = P_{k-1} · a / k,   P_0 = 1
    Erlang-B: B(N,a) = P_N / Σ_{k=0..N} P_k
    Erlang-C: C(N,a) = B · N / (N - a · (1 - B)),   a < N
    P(wait ≥ t) = C · exp(-(N-a)/AHT · t)
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from _common import write_json


@dataclass
class ErlangC:
    lam_per_sec: float  # λ 单位: 告警/秒
    aht_sec: float      # 平均处理时长

    def _traffic(self) -> float:
        return self.lam_per_sec * self.aht_sec  # Erlangs

    def erlang_b(self, n_agents: int) -> float:
        a = self._traffic()
        b = 1.0
        for k in range(1, n_agents + 1):
            b = (a * b) / (k + a * b)
        return b

    def prob_wait(self, n_agents: int) -> float:
        a = self._traffic()
        if n_agents <= a:
            return 1.0
        b = self.erlang_b(n_agents)
        return b * n_agents / (n_agents - a * (1 - b))

    def service_level(self, n_agents: int, target_s: float = 60.0) -> float:
        a = self._traffic()
        if n_agents <= a:
            return 0.0
        pw = self.prob_wait(n_agents)
        return 1 - pw * math.exp(-(n_agents - a) / self.aht_sec * target_s)

    def min_agents(self, sla: float = 0.9, target_s: float = 60.0) -> int:
        n = max(1, int(math.ceil(self._traffic())))
        while self.service_level(n, target_s) < sla and n < 10_000:
            n += 1
        return n


scenarios = []
for streams, per_min in [
    (1000, 3.0),
    (5000, 12.0),
    (10000, 22.0),
    (50000, 100.0),
]:
    lam = per_min / 60.0
    m = ErlangC(lam_per_sec=lam, aht_sec=90.0)
    n = m.min_agents(sla=0.9, target_s=60.0)
    sl = m.service_level(n, 60.0)
    scenarios.append({
        "concurrent_streams": streams,
        "alerts_per_minute": per_min,
        "agents_required": n,
        "achieved_service_level_60s": round(sl, 4),
        "traffic_erlangs": round(m._traffic(), 3),
        "alerts_per_agent_hour": round(per_min * 60 / (n * 60), 2),
    })

payload = {
    "assumptions": {"AHT_s": 90, "target_SLA": 0.9, "target_response_s": 60},
    "scenarios": scenarios,
    "source": "Erlang-C textbook formulation; cross-checked with scipy.stats Erlang papers.",
}

print("── 人工复核坐席容量（Erlang-C）──")
for s in scenarios:
    print(f"  并发 {s['concurrent_streams']} 路 · {s['alerts_per_minute']}/min → "
          f"需 {s['agents_required']} 坐席 (SL={s['achieved_service_level_60s']:.2%})")

write_json("05_alerts_capacity_erlangc", payload)
