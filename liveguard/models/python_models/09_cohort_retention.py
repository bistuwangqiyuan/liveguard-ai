"""
09_cohort_retention.py
======================

净/总收入留存（NRR / GRR）与留存瀑布。对应 BP §5.4.3 / §7.1.3。

NRR = (期初 ARR − 流失 − 收缩 + 扩张) / 期初 ARR
GRR = (期初 ARR − 流失 − 收缩) / 期初 ARR

分档月流失 → 年化 logo 流失；扩张来自 Starter→Pro 升级 + Pro/Ent 加路。
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from _common import BRAND, PALETTE, fmt_pct, save_chart, write_json
import data_sources as DS

# 分档年化金额流失（金额口径，含降档）
seg_annual_gross_churn = {
    "Starter": 1 - (1 - DS.PRICING["Starter"]["monthly_churn"]) ** 12,
    "Pro": 1 - (1 - DS.PRICING["Pro"]["monthly_churn"]) ** 12,
    "Enterprise": 1 - (1 - DS.PRICING["Enterprise"]["monthly_churn"]) ** 12,
}
# 金额加权 GRR（按各档年收入贡献加权）
rev_weight = {s: DS.PRICING[s]["annual"] * DS.PRICING[s]["mix"] for s in DS.PRICING}
total_w = sum(rev_weight.values())
blended_gross_churn = sum(rev_weight[s] / total_w * seg_annual_gross_churn[s] for s in DS.PRICING)
grr_amount = 1 - blended_gross_churn

# 净扩张（v3 四层货币化驱动：Pro/Ent 升级 + 加路 + 风控OS加购 + 数据/API + 保险/RegTech）
expansion_by_year = [0.12, 0.25, 0.40, 0.50, 0.60]
nrr_by_year = [round(grr_amount + e, 4) for e in expansion_by_year]
grr_by_year = [round(grr_amount, 4)] * 5

payload = {
    "as_of": DS.AS_OF,
    "segment_annual_gross_churn_pct": {s: round(v * 100, 1) for s, v in seg_annual_gross_churn.items()},
    "blended_amount_GRR_pct": round(grr_amount * 100, 1),
    "NRR_by_year_pct": [round(x * 100, 0) for x in nrr_by_year],
    "GRR_by_year_pct": [round(x * 100, 0) for x in grr_by_year],
    "expansion_by_year_pct": [round(x * 100, 0) for x in expansion_by_year],
    "note": "金额口径 GRR；NRR = GRR + 净扩张。Starter 重型导致 logo 口径偏高流失，金额口径稳健。",
    "sources": ["公司客户结构假设", "SaaS Capital 2024 NRR/GRR 基准"],
}

print("── NRR / GRR ──")
print(f"  金额 GRR(混合) = {fmt_pct(grr_amount)}")
for i, y in enumerate(DS.YEARS):
    print(f"  {y}: NRR {nrr_by_year[i]*100:.0f}%  GRR {grr_by_year[i]*100:.0f}%  扩张 +{expansion_by_year[i]*100:.0f}%")

write_json("09_cohort_retention", payload)

# ── 图：NRR/GRR 演进 + Y3 留存瀑布 ──────────────────────────────────────────
fig, axs = plt.subplots(1, 2, figsize=(12.0, 4.6))
axs[0].plot(DS.YEARS, [x * 100 for x in nrr_by_year], "o-", color=BRAND["teal"], lw=2.4, label="NRR")
axs[0].plot(DS.YEARS, [x * 100 for x in grr_by_year], "s--", color=BRAND["blue"], lw=2, label="GRR")
axs[0].axhline(100, color=BRAND["grey"], ls=":", lw=1)
for i, v in enumerate(nrr_by_year):
    axs[0].annotate(f"{v*100:.0f}%", (i, v * 100), xytext=(0, 8), textcoords="offset points", ha="center", fontsize=9, color=BRAND["ink"])
axs[0].set_ylabel("留存率 (%)")
axs[0].set_title("NRR / GRR 5 年演进", pad=8)
axs[0].legend(fontsize=9)

# Y3 瀑布：期初 100 → -流失 +扩张 → NRR
start = 100
churn = -blended_gross_churn * 100
expansion = expansion_by_year[2] * 100
steps = [("期初 ARR", start, BRAND["blue"]), ("金额流失", churn, BRAND["red"]),
         ("净扩张", expansion, BRAND["teal"]), ("期末 NRR", start + churn + expansion, BRAND["amber"])]
cum = 0
for i, (lab, val, col) in enumerate(steps):
    if lab in ("期初 ARR", "期末 NRR"):
        axs[1].bar(i, val, color=col, alpha=0.9, width=0.6)
        axs[1].text(i, val + 2, f"{val:.0f}", ha="center", fontsize=9, color=BRAND["ink"])
        cum = val
    else:
        axs[1].bar(i, val, bottom=cum if val > 0 else cum + val, color=col, alpha=0.9, width=0.6)
        axs[1].text(i, cum + val / 2, f"{val:+.0f}", ha="center", fontsize=9, color=BRAND["ink"])
        cum += val
axs[1].set_xticks(range(4), [s[0] for s in steps], fontsize=9)
axs[1].set_ylabel("ARR 指数 (期初=100)")
axs[1].set_title(f"Y3 留存瀑布（NRR={nrr_by_year[2]*100:.0f}%）", pad=8)
fig.suptitle("§5.4.3 净/总收入留存", fontsize=13, fontweight="bold", color=BRAND["ink"], y=1.02)
fig.tight_layout()
save_chart(fig, "fig_09_cohort_retention")

print("✓ 09_cohort_retention 完成 → JSON + fig_09_cohort_retention.png")
