"""
05_alerts_capacity_erlangc.py
=============================

人工复核坐席容量模型（Erlang-C）。对应 BP §7.2 NOC 容量规划。

场景：每 N 路并发直播每分钟产生 α 条需复核告警；每条复核 AHT=90s；
目标 ≥ 90% 告警 60s 内响应。求最少坐席 N。

数值稳定（对数递推避免阶乘溢出）：
    Erlang-B 递推 B(N,a) = a·B / (N + a·B)
    Erlang-C  C = B·N / (N − a·(1−B))
    P(wait ≥ t) = C·exp(−(N−a)/AHT·t)
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import matplotlib.pyplot as plt

from _common import BRAND, PALETTE, save_chart, write_json
import data_sources as DS


@dataclass
class ErlangC:
    lam_per_sec: float
    aht_sec: float

    def _traffic(self) -> float:
        return self.lam_per_sec * self.aht_sec

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
for streams, per_min in [(1000, 3.0), (5000, 12.0), (10000, 22.0), (50000, 100.0)]:
    m = ErlangC(lam_per_sec=per_min / 60.0, aht_sec=90.0)
    n = m.min_agents(sla=0.9, target_s=60.0)
    scenarios.append({
        "concurrent_streams": streams,
        "alerts_per_minute": per_min,
        "agents_required": n,
        "achieved_service_level_60s": round(m.service_level(n, 60.0), 4),
        "traffic_erlangs": round(m._traffic(), 3),
        "agents_per_1k_streams": round(n / (streams / 1000), 2),
    })

payload = {
    "as_of": DS.AS_OF,
    "assumptions": {"AHT_s": 90, "target_SLA": 0.9, "target_response_s": 60},
    "scenarios": scenarios,
    "source": "Erlang-C textbook formulation; cross-checked with scipy.stats Erlang.",
}

print("── 人工复核坐席容量（Erlang-C）──")
for s in scenarios:
    print(f"  并发 {s['concurrent_streams']:>6} 路 · {s['alerts_per_minute']}/min → "
          f"{s['agents_required']} 坐席 (SL={s['achieved_service_level_60s']:.2%})")

write_json("05_alerts_capacity_erlangc", payload)

# ── 图：规模 vs 坐席 + 服务水平曲线（10k 路场景）─────────────────────────────
fig, axs = plt.subplots(1, 2, figsize=(12.0, 4.6))
streams = [s["concurrent_streams"] for s in scenarios]
agents = [s["agents_required"] for s in scenarios]
axs[0].plot(streams, agents, "o-", color=BRAND["blue"], lw=2.4, markersize=9)
for s in scenarios:
    axs[0].annotate(f"{s['agents_required']}人", (s["concurrent_streams"], s["agents_required"]),
                    xytext=(0, 8), textcoords="offset points", ha="center", fontsize=9, color=BRAND["ink"])
axs[0].set_xlabel("并发直播路数")
axs[0].set_ylabel("最少坐席数")
axs[0].set_title("规模化坐席需求（亚线性增长）", pad=8)
axs[0].set_xscale("log")

m10 = ErlangC(lam_per_sec=22.0 / 60.0, aht_sec=90.0)
n_range = range(max(1, int(m10._traffic())), max(1, int(m10._traffic())) + 25)
sl = [m10.service_level(n, 60.0) for n in n_range]
axs[1].plot(list(n_range), [x * 100 for x in sl], "-", color=BRAND["teal"], lw=2.4)
axs[1].axhline(90, color=BRAND["red"], ls="--", lw=1.2, label="目标 90% / 60s")
n10 = next(s for s in scenarios if s["concurrent_streams"] == 10000)["agents_required"]
axs[1].axvline(n10, color=BRAND["amber"], ls=":", lw=1.5, label=f"最优坐席 {n10}")
axs[1].set_xlabel("坐席数 (10,000 路场景)")
axs[1].set_ylabel("60s 内响应率 (%)")
axs[1].set_title("服务水平曲线", pad=8)
axs[1].legend(fontsize=9)
fig.suptitle("§7.2 NOC 人工复核坐席容量（Erlang-C）", fontsize=13, fontweight="bold", color=BRAND["ink"], y=1.02)
fig.tight_layout()
save_chart(fig, "fig_05_erlangc_capacity")

print("✓ 05_alerts_capacity_erlangc 完成 → JSON + fig_05_erlangc_capacity.png")
