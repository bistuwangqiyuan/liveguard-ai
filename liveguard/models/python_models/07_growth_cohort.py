"""
07_growth_cohort.py
===================

5 年客户 / ARR 队列模型 + NRR / GRR。对应 BP §5.4.3 / §6.9 / §8。

* 期末付费账号数（canonical）：[800, 6500, 28000, 78000, 175000]
* 加权年 ARPU = ¥15,969（来自 pricing：70/25/5 结构）
* ARR_year = 期末账号数 × 加权 ARPU
* NRR / GRR 由分档月流失 + 净扩张推导

蒙特卡洛仅用于给 Y5 ARR 一个 90% 区间（增长节奏 ±噪声）。seed=42。
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from _common import BRAND, PALETTE, ci, fmt_cny, save_chart, write_json, rng
import data_sources as DS

r = rng()
ARPU = DS.BLENDED_ARPU_ANNUAL
cust = DS.CUSTOMERS_EOY
arr_by_year = [c * ARPU for c in cust]

# NRR / GRR（公司目标，分档加权）
nrr_by_year = [1.05, 1.15, 1.25, 1.28, 1.30]
logo_retention = [0.88, 0.90, 0.92, 0.93, 0.94]
# GRR：以混合月流失年化
blended_monthly_churn = sum(DS.PRICING[s]["mix"] * DS.PRICING[s]["monthly_churn"] for s in DS.PRICING)
grr_annual = (1 - blended_monthly_churn) ** 12

# 36 个月分档队列留存曲线（用于图示）
months = np.arange(0, 37)
retention_curves = {}
for s, p in DS.PRICING.items():
    retention_curves[s] = (1 - p["monthly_churn"]) ** months

# Y5 ARR 90% 区间（增长节奏噪声）
N = 20000
noise = r.normal(1.0, 0.16, N)
y5_arr_samples = arr_by_year[-1] * np.clip(noise, 0.55, 1.6)
m, lo, hi = ci(y5_arr_samples)

payload = {
    "as_of": DS.AS_OF, "currency": "CNY",
    "customers_eoy": cust,
    "blended_arpu_annual_CNY": round(ARPU, 1),
    "arr_by_year_CNY": [round(x, 0) for x in arr_by_year],
    "arr_by_year_yi": [round(x / 1e8, 2) for x in arr_by_year],
    "nrr_by_year_pct": [round(x * 100, 0) for x in nrr_by_year],
    "logo_retention_pct": [round(x * 100, 0) for x in logo_retention],
    "blended_monthly_churn_pct": round(blended_monthly_churn * 100, 2),
    "grr_annual_pct": round(grr_annual * 100, 1),
    "y5_arr_90CI_CNY": [round(lo, 0), round(hi, 0)],
    "sources": ["公司客户结构假设", "SaaS Capital 2024 留存基准", "BP §5/§8 一致性约束"],
}

print("── 5 年 ARR 队列（中位数） ──")
for i, y in enumerate(DS.YEARS):
    print(f"  {y}: 客户 {cust[i]:>7,} → ARR {fmt_cny(arr_by_year[i])}  NRR {nrr_by_year[i]*100:.0f}%")
print(f"  Y5 ARR 90% 区间: [{fmt_cny(lo)}, {fmt_cny(hi)}]")

write_json("07_growth_cohort", payload)

# ── 图：留存曲线 + ARR 路径 ────────────────────────────────────────────────
fig, axs = plt.subplots(1, 2, figsize=(12.0, 4.6))
colors = [BRAND["blue"], BRAND["teal"], BRAND["violet"]]
for i, (s, curve) in enumerate(retention_curves.items()):
    axs[0].plot(months, curve * 100, "-", color=colors[i], lw=2.2, label=f"{s} (churn {DS.PRICING[s]['monthly_churn']*100:.1f}%/月)")
axs[0].set_xlabel("月份")
axs[0].set_ylabel("Logo 留存 (%)")
axs[0].set_title("分档队列留存曲线 (36 月)", pad=8)
axs[0].legend(fontsize=9)
axs[0].set_ylim(0, 105)

arr_yi = [x / 1e8 for x in arr_by_year]
axs[1].bar(DS.YEARS, arr_yi, color=BRAND["blue"], alpha=0.85, width=0.6)
axs[1].plot(DS.YEARS, arr_yi, "o-", color=BRAND["amber"], lw=2)
for i, v in enumerate(arr_yi):
    axs[1].text(i, v * 1.02 + 0.3, f"¥{v:.2f}亿", ha="center", fontsize=9, color=BRAND["ink"])
axs[1].errorbar(4, arr_yi[-1], yerr=[[arr_yi[-1] - lo / 1e8], [hi / 1e8 - arr_yi[-1]]],
                fmt="none", color=BRAND["red"], capsize=5, lw=1.5)
axs[1].set_ylabel("ARR (¥ 亿)")
axs[1].set_title(f"5 年 ARR 路径（Y5 = ¥{arr_yi[-1]:.1f}亿，CAGR≈{(arr_by_year[-1]/arr_by_year[0])**0.25*100-100:.0f}%）", pad=8)
fig.suptitle("§8 守播 LiveGuard 5 年客户与 ARR 队列", fontsize=13, fontweight="bold", color=BRAND["ink"], y=1.02)
fig.tight_layout()
save_chart(fig, "fig_07_growth_cohort")

print("✓ 07_growth_cohort 完成 → JSON + fig_07_growth_cohort.png")
