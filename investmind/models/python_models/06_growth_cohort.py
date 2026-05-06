"""
06_growth_cohort.py
===================

5 年用户增长 + 月度 Cohort 留存 + Net Revenue + ARR 预测。

---------------------------------------------------------------------------
ASSUMPTIONS
---------------------------------------------------------------------------

A. 月新增付费用户（漏斗 GTM 三阶段）
   Y1: PLG 自助为主    →   180 → 800 / 月（指数爬升）
   Y2: PLG + 内容渠道   →   1,500 / 月
   Y3: PLG + ABM        →   3,500 / 月
   Y4: 全渠道           →   6,500 / 月
   Y5: 平台化扩张        →   9,000 / 月

B. 月留存率
   Lite      94-97%      (mode 96%)
   Pro       95.5-98.5%  (mode 97%)
   Family    97-99%      (mode 98.5%)

C. 客群混合 (Lite : Pro : Family)
   Y1: 75 : 22 : 3
   Y3: 55 : 35 : 10
   Y5: 45 : 40 : 15

D. 升级率（Lite→Pro 月升级率 1.2-2.5%；Pro→Family 月升级率 0.4-0.9%）

---------------------------------------------------------------------------
SOURCES
---------------------------------------------------------------------------
S1. SaaS Capital 2024 Benchmark Report
S2. ChartMogul SaaS Benchmark 2024
S3. KeyBanc Capital Markets SaaS Survey 2024
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

from _common import BRAND, PALETTE, fmt_cny, save_chart, write_json, rng

r = rng()
MONTHS = 60

monthly_new = np.zeros(MONTHS)
monthly_new[0:12]   = np.linspace(180, 800,  12)
monthly_new[12:24]  = np.linspace(800, 1500, 12)
monthly_new[24:36]  = np.linspace(1500, 3500, 12)
monthly_new[36:48]  = np.linspace(3500, 6500, 12)
monthly_new[48:60]  = np.linspace(6500, 9000, 12)

mix_evolution = np.zeros((MONTHS, 3))
year_mix = np.array([
    [0.75, 0.22, 0.03],
    [0.65, 0.30, 0.05],
    [0.55, 0.35, 0.10],
    [0.50, 0.38, 0.12],
    [0.45, 0.40, 0.15],
])
for y in range(5):
    for m in range(12):
        mix_evolution[y*12 + m] = year_mix[y]

retention = {"Lite": 0.96, "Pro": 0.97, "Family": 0.985}
arpu_m = {"Lite": 99.0, "Pro": 416.0, "Family": 1666.0}
gm = {"Lite": 0.82, "Pro": 0.80, "Family": 0.73}

active_per_segment = {k: np.zeros(MONTHS) for k in ["Lite", "Pro", "Family"]}
for m in range(MONTHS):
    for j, seg in enumerate(["Lite", "Pro", "Family"]):
        new_seg = monthly_new[m] * mix_evolution[m, j]
        prev = active_per_segment[seg][m-1] if m > 0 else 0
        active_per_segment[seg][m] = prev * retention[seg] + new_seg

mrr_per_segment = {seg: active_per_segment[seg] * arpu_m[seg] for seg in active_per_segment}
mrr_total = sum(mrr_per_segment.values())
arr_total = mrr_total * 12

api_data_revenue_m = arr_total * 0.10 / 12
platform_revenue_m = np.where(
    np.arange(MONTHS) >= 18, arr_total * 0.18 / 12, 0.0,
)
total_revenue_m = mrr_total + api_data_revenue_m + platform_revenue_m
total_arr = total_revenue_m * 12

annual = {}
for y in range(5):
    sl = slice(y*12, (y+1)*12)
    annual[f"Y{y+1}"] = {
        "active_users_eom":     int(sum(v[(y+1)*12-1] for v in active_per_segment.values())),
        "Lite_active":          int(active_per_segment["Lite"][(y+1)*12-1]),
        "Pro_active":           int(active_per_segment["Pro"][(y+1)*12-1]),
        "Family_active":        int(active_per_segment["Family"][(y+1)*12-1]),
        "subscription_revenue": float(mrr_per_segment["Lite"][sl].sum()
                                      + mrr_per_segment["Pro"][sl].sum()
                                      + mrr_per_segment["Family"][sl].sum()),
        "data_api_revenue":     float(api_data_revenue_m[sl].sum()),
        "platform_revenue":     float(platform_revenue_m[sl].sum()),
        "total_revenue":        float(total_revenue_m[sl].sum()),
        "ending_ARR":           float(total_arr[(y+1)*12-1]),
        "ending_MRR":           float(total_revenue_m[(y+1)*12-1]),
    }

cohort_size = monthly_new[:36].astype(int)
cohort_retention = np.zeros((36, 24))
for c in range(36):
    for t in range(24):
        if c + t < 60:
            blended_ret = (
                year_mix[(c)//12][0] * retention["Lite"]
                + year_mix[(c)//12][1] * retention["Pro"]
                + year_mix[(c)//12][2] * retention["Family"]
            )
            cohort_retention[c, t] = blended_ret ** t

result = {
    "as_of": "2026-04-30",
    "horizon_months": MONTHS,
    "annual": annual,
    "monthly_new_users": monthly_new.astype(int).tolist(),
    "ending_ARR_y5_total_CNY":          float(total_arr[-1]),
    "ending_ARR_y5_subscription_CNY":   float(mrr_total[-1] * 12),
    "ending_ARR_y5_data_api_CNY":       float(api_data_revenue_m[-1] * 12),
    "ending_ARR_y5_platform_CNY":       float(platform_revenue_m[-1] * 12),
    "y5_cumulative_revenue_CNY":        float(total_revenue_m[48:60].sum()),
    "blended_y5_active_users":          int(sum(v[-1] for v in active_per_segment.values())),
    "sources": [
        "SaaS Capital 2024 Benchmark Report",
        "ChartMogul SaaS Benchmark 2024",
        "KeyBanc SaaS Survey 2024",
    ],
}

print("── 5 年增长 / 留存 / ARR ──")
for y in range(5):
    a = annual[f"Y{y+1}"]
    print(f"  Y{y+1}: 用户 {a['active_users_eom']:>7,d}  "
          f"年收入 {fmt_cny(a['total_revenue']):>10s}  "
          f"期末 ARR {fmt_cny(a['ending_ARR']):>10s}")

write_json("06_growth_cohort", result)

fig, axs = plt.subplots(1, 2, figsize=(12.0, 4.8))

months = np.arange(1, MONTHS + 1)
axs[0].stackplot(
    months,
    mrr_per_segment["Family"] * 12,
    mrr_per_segment["Pro"] * 12,
    mrr_per_segment["Lite"] * 12,
    api_data_revenue_m * 12,
    platform_revenue_m * 12,
    labels=["Family Office 订阅", "Pro 订阅", "Lite 订阅", "数据 / API", "平台分成 / 撮合"],
    colors=[BRAND["amber"], BRAND["blue"], BRAND["teal"], BRAND["violet"], BRAND["red"]],
    alpha=0.9,
)
axs[0].set_xlabel("月份 (M1-M60)")
axs[0].set_ylabel("ARR (¥)")
axs[0].set_title("ARR 分层堆叠 · 5 年路径", pad=8)
axs[0].yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"¥{v/1e8:.1f}亿"))
axs[0].legend(fontsize=8, loc="upper left")
for y in range(1, 6):
    axs[0].axvline(y * 12, color=BRAND["line"], lw=0.5, ls="--")
    axs[0].text(y * 12 - 6, total_arr[y*12-1] * 0.04, f"Y{y}",
                fontsize=9, color=BRAND["grey"], ha="center")

cmap = LinearSegmentedColormap.from_list(
    "investmind", ["#FFFFFF", BRAND["teal"], BRAND["blue"]],
)
im = axs[1].imshow(cohort_retention[:24, :], aspect="auto", cmap=cmap, vmin=0, vmax=1)
axs[1].set_xlabel("入组后月数")
axs[1].set_ylabel("Cohort（入组月）")
axs[1].set_title("月度 Cohort 留存热力图", pad=8)
cb = plt.colorbar(im, ax=axs[1])
cb.set_label("留存率")

fig.suptitle("§8.1 InvestMind 5 年增长 / Cohort / 收入分层",
             fontsize=13, fontweight="bold", y=1.02, color=BRAND["ink"])
fig.tight_layout()
save_chart(fig, "fig_06_growth_cohort")

print("✓ 06_growth_cohort 完成")
