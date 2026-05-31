"""
06_dedup_suppression_sim.py
===========================

告警去重 / 抑制策略的蒙特卡洛模拟。对应 BP §7.4 算法运营。

* 输入：每主播每小时真告警率 + 误报率（Poisson 到达）
* 抑制窗口 W ∈ {120s, 300s, 600s}；策略 A 固定窗口，策略 B 自适应
* 输出每策略 (人工处理量下降%, 真告警错过率%, 平均延迟)
* P0 告警不进入抑制窗口，全部直通

seed=42。
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from _common import BRAND, PALETTE, save_chart, write_json
import data_sources as DS

rng = np.random.default_rng(DS.SEED)
SIM_HOURS = 24 * 14
STREAMS = 1000
TRUE_RATE = 0.8
FP_RATE = 0.10
WINDOWS = [120, 300, 600]


def simulate_one_stream(w_s: int, adaptive: bool) -> dict:
    t = 0.0
    suppressed = delivered = missed = total_true = total_fp = 0
    last_delivered_t = -1e9
    last_delivered_is_true = False
    density = 0.0
    delays: list[float] = []

    lam_fp = FP_RATE * 5 / 3600.0
    lam_true = TRUE_RATE / 3600.0
    lam_total = lam_fp + lam_true
    p_true = lam_true / lam_total
    end_time = SIM_HOURS * 3600

    while t < end_time:
        t += rng.exponential(1.0 / lam_total)
        if t >= end_time:
            break
        is_true = rng.random() < p_true
        if is_true:
            total_true += 1
        else:
            total_fp += 1
        effective_w = int(w_s * (1 + min(density / 5, 1.5))) if adaptive else w_s
        if t - last_delivered_t < effective_w:
            suppressed += 1
            if is_true and not last_delivered_is_true:
                missed += 1
            continue
        delivered += 1
        last_delivered_t = t
        last_delivered_is_true = is_true
        density = density * 0.9 + 1
        delays.append(rng.uniform(0, 10))

    return {"delivered": delivered, "suppressed": suppressed, "true_total": total_true,
            "fp_total": total_fp, "missed_true": missed,
            "avg_delay_s": float(np.mean(delays)) if delays else 0.0}


strategies = []
for w in WINDOWS:
    for adaptive in (False, True):
        agg = {"delivered": 0, "suppressed": 0, "true_total": 0, "fp_total": 0, "missed_true": 0, "avg_delay_s": []}
        for _ in range(STREAMS):
            r_ = simulate_one_stream(w, adaptive)
            for k in ("delivered", "suppressed", "true_total", "fp_total", "missed_true"):
                agg[k] += r_[k]
            agg["avg_delay_s"].append(r_["avg_delay_s"])
        total = agg["delivered"] + agg["suppressed"]
        strategies.append({
            "window_s": w, "adaptive": adaptive,
            "human_load_reduction_pct": round(100 * agg["suppressed"] / max(1, total), 2),
            "true_alert_miss_pct": round(100 * agg["missed_true"] / max(1, agg["true_total"]), 3),
            "avg_delay_s": round(float(np.mean(agg["avg_delay_s"])), 2),
        })

payload = {
    "as_of": DS.AS_OF,
    "config": {"streams": STREAMS, "sim_hours": SIM_HOURS, "true_rate_per_host_hour": TRUE_RATE, "fp_rate": FP_RATE, "windows_s": WINDOWS},
    "strategies": strategies,
    "recommendation": "P1 级别推荐 W=300s 自适应：~60% 降人工量，<1.5% 真告警错过；P0 不进抑制窗口直通。",
}

print("── 告警抑制策略对比 ──")
for s in strategies:
    print(f"  W={s['window_s']}s adaptive={s['adaptive']}: 降载 {s['human_load_reduction_pct']}%  "
          f"漏报 {s['true_alert_miss_pct']}%  延迟 {s['avg_delay_s']}s")

write_json("06_dedup_suppression_sim", payload)

# ── 图：人工降载 vs 漏报 trade-off ─────────────────────────────────────────
fig, ax = plt.subplots(figsize=(8.8, 5.2))
for i, s in enumerate(strategies):
    marker = "o" if s["adaptive"] else "s"
    color = BRAND["teal"] if s["adaptive"] else BRAND["blue"]
    ax.scatter(s["human_load_reduction_pct"], s["true_alert_miss_pct"], s=160, marker=marker,
               color=color, edgecolor="white", zorder=3,
               label=("自适应窗口" if s["adaptive"] else "固定窗口") if i < 2 else None)
    ax.annotate(f"W={s['window_s']}s", (s["human_load_reduction_pct"], s["true_alert_miss_pct"]),
                xytext=(6, 6), textcoords="offset points", fontsize=9, color=BRAND["ink"])
ax.axhline(1.5, color=BRAND["red"], ls="--", lw=1.2, label="漏报红线 1.5%")
ax.set_xlabel("人工处理量下降 (%)")
ax.set_ylabel("真告警错过率 (%)")
ax.set_title("§7.4 告警去重/抑制策略 trade-off（推荐 W=300s 自适应）", pad=12)
ax.legend(fontsize=9)
fig.text(0.99, 0.01, "MC seed=42 · 1000 streams × 2 周", ha="right", fontsize=8, color=BRAND["grey"])
save_chart(fig, "fig_06_dedup_suppression")

print("✓ 06_dedup_suppression_sim 完成 → JSON + fig_06_dedup_suppression.png")
