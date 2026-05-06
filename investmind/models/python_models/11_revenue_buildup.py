"""
11_revenue_buildup.py
=====================

5 年收入分层展开（订阅 / API / 数据 / 平台撮合 / 增值服务）+ 毛利。

引用 06_growth_cohort 的用户与 ARR 输出，进一步展开为：
  * Lite / Pro / Family 三档订阅
  * 数据 API 调用费（按 Top-10 早期投资数据合作伙伴 + 银行/律所）
  * 第三方研报市场分成
  * 平台撮合（Y2 起，FA 服务费 1.5-3.0% × 平台撮合金额）
  * 增值服务（深度尽调 / 投后陪跑）

---------------------------------------------------------------------------
ASSUMPTIONS
---------------------------------------------------------------------------
A. 数据 API：Y2 上线，年合作客户 12→90，单合同 ¥80,000 → ¥350,000
B. 第三方研报：Y3 上线，UGC + PGC 报告交易 GMV 抽 25%
C. 平台撮合：Y3 上线，Family Office / 持证天使聚合，take-rate 2.0%
D. 增值服务：Y2 上线，对 Pro/Family 用户 ¥3,000-15,000/单

---------------------------------------------------------------------------
SOURCES
---------------------------------------------------------------------------
S1. AngelList 2024 Letter（撮合 take-rate 数据）
S2. Wind / 同花顺 / Choice 个人版 + 数据 API 财报
S3. Pitchbook Pricing Page（机构数据 API 区间）
S4. 中欧国际工商学院 私行年报 2024
"""

from __future__ import annotations

import json
import numpy as np
import matplotlib.pyplot as plt

from _common import BRAND, PALETTE, fmt_cny, save_chart, write_json, OUT_DIR

with open(OUT_DIR / "06_growth_cohort.json", encoding="utf-8") as f:
    cohort = json.load(f)

years = ["Y1", "Y2", "Y3", "Y4", "Y5"]

subscription = np.array([
    cohort["annual"][y]["subscription_revenue"] for y in years
])
data_api_baseline = np.array([0, 4_800_000, 21_000_000, 56_000_000, 110_000_000], dtype=float)
research_marketplace = np.array([0, 0, 8_000_000, 38_000_000, 85_000_000], dtype=float)
platform_matchmaking = np.array([0, 0, 26_000_000, 95_000_000, 220_000_000], dtype=float)
value_add_services = np.array([0, 6_000_000, 22_000_000, 55_000_000, 105_000_000], dtype=float)

stack = {
    "subscription":         subscription,
    "data_api":             data_api_baseline,
    "research_market":      research_marketplace,
    "platform_match":       platform_matchmaking,
    "value_add":            value_add_services,
}

total = sum(stack.values())

gm = {
    "subscription":   0.80,
    "data_api":       0.78,
    "research_market":0.55,
    "platform_match": 0.75,
    "value_add":      0.50,
}
gross_profit_per_line = {k: v * gm[k] for k, v in stack.items()}
gp_total = sum(gross_profit_per_line.values())

result = {
    "as_of": "2026-04-30",
    "currency": "CNY",
    "years": years,
    "revenue_lines": {k: v.tolist() for k, v in stack.items()},
    "gross_margin_per_line": gm,
    "total_revenue": total.tolist(),
    "total_gross_profit": gp_total.tolist(),
    "blended_gross_margin": (gp_total / np.maximum(total, 1)).tolist(),
    "y5_total_revenue_CNY": float(total[-1]),
    "y5_total_gross_profit_CNY": float(gp_total[-1]),
    "y5_blended_gm_pct": float(gp_total[-1] / total[-1] * 100),
    "sources": [
        "AngelList 2024 Letter",
        "Wind / 同花顺 / Choice 财报",
        "Pitchbook Pricing Page",
    ],
}

print("── 5 年收入分层（人民币 万元） ──")
print(f"  {'Line':<18s} | " + " | ".join(f"{y:>10s}" for y in years))
for k, v in stack.items():
    print(f"  {k:<18s} | " + " | ".join(f"{x/1e4:>10.1f}" for x in v))
print(f"  {'合计':<18s} | " + " | ".join(f"{x/1e4:>10.1f}" for x in total))
print(f"  {'毛利合计':<18s} | " + " | ".join(f"{x/1e4:>10.1f}" for x in gp_total))
print(f"  Y5 综合毛利率: {gp_total[-1]/total[-1]*100:.1f}%")

write_json("11_revenue_buildup", result)

fig, axs = plt.subplots(1, 2, figsize=(12.0, 4.8))

x = np.arange(len(years))
labels_zh = {
    "subscription":   "三档订阅",
    "data_api":       "数据 API",
    "research_market":"研报市场分成",
    "platform_match": "平台撮合 / FA",
    "value_add":      "增值服务",
}
colors = [BRAND["blue"], BRAND["teal"], BRAND["violet"], BRAND["amber"], BRAND["red"]]
bottom = np.zeros(len(years))
for i, (k, v) in enumerate(stack.items()):
    axs[0].bar(x, v, bottom=bottom, color=colors[i], label=labels_zh[k], width=0.6)
    bottom += v

axs[0].set_xticks(x, years)
axs[0].set_ylabel("收入 (¥)")
axs[0].set_title("5 年收入堆积（按业务线）", pad=8)
axs[0].yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"¥{v/1e8:.1f}亿"))
axs[0].legend(fontsize=8, loc="upper left")
for i, t in enumerate(total):
    axs[0].text(i, t * 1.02, fmt_cny(t), ha="center", fontsize=9, color=BRAND["ink"])

share = stack["subscription"] / np.maximum(total, 1) * 100
axs[1].bar(x, share, width=0.55, color=BRAND["blue"], alpha=0.8, label="订阅占比 %")
axs[1].plot(x, np.array(result["blended_gross_margin"]) * 100,
            "o-", color=BRAND["teal"], lw=2.0, label="综合毛利率 %")
axs[1].set_xticks(x, years)
axs[1].set_ylabel("百分比")
axs[1].set_title("收入结构 vs 毛利率演进", pad=8)
axs[1].yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%"))
axs[1].legend(fontsize=10)

fig.suptitle("§5.6 InvestMind 5 年收入分层与毛利演进",
             fontsize=13, fontweight="bold", y=1.02, color=BRAND["ink"])
fig.tight_layout()
save_chart(fig, "fig_11_revenue_buildup")

print("✓ 11_revenue_buildup 完成")
