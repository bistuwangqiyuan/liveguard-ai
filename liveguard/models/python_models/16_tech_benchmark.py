"""
16_tech_benchmark.py
====================

技术基准：算法栈延迟、端到端 KPI 雷达、单路推理成本下降曲线、反作弊能力评分。
对应 BP §4.3 / §4.4 / §4.5 / §4.8。常量来自 data_sources.TECH_MODELS / SYSTEM_KPI。
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from _common import BRAND, PALETTE, save_chart, write_json
import data_sources as DS

K = DS.SYSTEM_KPI

# 单路推理成本曲线（年降 28%）
cost = [DS.UNIT_INFER_COST_Y1]
for _ in range(4):
    cost.append(round(cost[-1] * (1 - DS.UNIT_INFER_COST_YOY_DROP), 0))

# 反作弊能力评分（0-100）
anticheat = {
    "主播离开(无人)": {"通用CV": 85, "规则脚本": 80, "守播": 98},
    "照片/静帧": {"通用CV": 45, "规则脚本": 10, "守播": 95},
    "循环视频回放": {"通用CV": 20, "规则脚本": 5, "守播": 92},
    "AI 数字人替播": {"通用CV": 15, "规则脚本": 5, "守播": 90},
    "换人代播": {"通用CV": 25, "规则脚本": 5, "守播": 94},
}
anticheat_avg = {k: round(np.mean([anticheat[s][k] for s in anticheat]), 0) for k in ("通用CV", "规则脚本", "守播")}

payload = {
    "as_of": DS.AS_OF,
    "algo_stack": DS.TECH_MODELS,
    "system_kpi": K,
    "unit_infer_cost_curve_CNY": {f"Y{i+1}": c for i, c in enumerate(cost)},
    "anti_cheat_scores": anticheat,
    "anti_cheat_avg": anticheat_avg,
    "sources": [DS.SOURCES[k] for k in ("S-030", "S-031", "S-032", "S-033", "S-034", "S-035", "S-036", "S-094")],
}

print("── 技术基准 ──")
print(f"  端到端 F1={K['f1']*100:.2f}%  FAR={K['far']*100:.1f}%  FNR={K['fnr']*100:.1f}%")
print(f"  告警 P50/P90/P99 = {K['alert_p50_s']}/{K['alert_p90_s']}/{K['alert_p99_s']} s")
print(f"  单路推理成本曲线: {cost}")
print(f"  反作弊均分: {anticheat_avg}")

write_json("16_tech_benchmark", payload)

# ── 图 1：延迟柱 + KPI 雷达 ────────────────────────────────────────────────
fig = plt.figure(figsize=(12.4, 4.8))
ax1 = fig.add_subplot(1, 2, 1)
mods = [m["module"] for m in DS.TECH_MODELS]
lat = [m["latency_ms"] for m in DS.TECH_MODELS]
ax1.barh(mods[::-1], lat[::-1], color=BRAND["blue"], alpha=0.85)
for i, v in enumerate(lat[::-1]):
    ax1.text(v + 0.5, i, f"{v}ms", va="center", fontsize=8, color=BRAND["ink"])
ax1.set_xlabel("单帧延迟 (ms)")
ax1.set_title("算法栈单帧延迟", pad=8)

ax2 = fig.add_subplot(1, 2, 2, polar=True)
metrics = ["Precision", "Recall", "F1", "1−FAR", "1−FNR", "可用性"]
ours = [K["precision"], K["recall"], K["f1"], 1 - K["far"], 1 - K["fnr"], K["availability"]]
baseline = [0.90, 0.87, 0.89, 0.93, 0.88, 0.99]
angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
ours += ours[:1]; baseline += baseline[:1]; angles += angles[:1]
ax2.plot(angles, [x * 100 for x in ours], "-", color=BRAND["blue"], lw=2.2, label="守播")
ax2.fill(angles, [x * 100 for x in ours], color=BRAND["blue"], alpha=0.18)
ax2.plot(angles, [x * 100 for x in baseline], "--", color=BRAND["grey"], lw=1.8, label="通用 CV 基线")
ax2.set_xticks(angles[:-1], metrics, fontsize=9)
ax2.set_ylim(80, 101)
ax2.set_title("端到端 KPI 雷达 (%)", pad=18)
ax2.legend(loc="lower right", fontsize=8, bbox_to_anchor=(1.15, -0.05))
fig.suptitle("§4.3-4.4 算法栈延迟与端到端 KPI", fontsize=13, fontweight="bold", color=BRAND["ink"], y=1.03)
fig.tight_layout()
save_chart(fig, "fig_16_tech_kpi")

# ── 图 2：成本曲线 + 反作弊对比 ────────────────────────────────────────────
fig2, axs = plt.subplots(1, 2, figsize=(12.2, 4.6))
yrs = [f"Y{i+1}" for i in range(5)]
axs[0].plot(yrs, cost, "o-", color=BRAND["teal"], lw=2.4, markersize=9)
axs[0].fill_between(yrs, cost, alpha=0.12, color=BRAND["teal"])
for i, c in enumerate(cost):
    axs[0].text(i, c + 6, f"¥{c:.0f}", ha="center", fontsize=9, color=BRAND["ink"])
axs[0].set_ylabel("单路推理成本 (¥/年)")
axs[0].set_title("单路推理成本曲线（年降 28%）", pad=8)

scenarios = list(anticheat.keys())
x = np.arange(len(scenarios))
w = 0.25
for i, (sys, col) in enumerate([("规则脚本", BRAND["grey"]), ("通用CV", BRAND["amber"]), ("守播", BRAND["blue"])]):
    vals = [anticheat[s][sys] for s in scenarios]
    axs[1].bar(x + (i - 1) * w, vals, w, color=col, alpha=0.9, label=sys)
axs[1].set_xticks(x, [s.replace("(", "\n(") for s in scenarios], fontsize=7.5)
axs[1].set_ylabel("能力评分 (0-100)")
axs[1].set_title("反作弊能力对比（守播独占领先）", pad=8)
axs[1].legend(fontsize=9)
fig2.suptitle("§4.5-4.8 反作弊能力与推理成本", fontsize=13, fontweight="bold", color=BRAND["ink"], y=1.02)
fig2.tight_layout()
save_chart(fig2, "fig_16_cost_anticheat")

print("✓ 16_tech_benchmark 完成 → JSON + fig_16_*.png (2 张)")
