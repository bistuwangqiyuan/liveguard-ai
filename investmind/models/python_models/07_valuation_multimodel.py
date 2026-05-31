"""
07_valuation_multimodel.py
==========================

InvestMind C 轮（Year 5 末）估值，三模型加权：
  M1. DCF（折现现金流）— 10 年期，5+5
  M2. Comparables（可比公司）— PS / PE / ARR multiple
  M3. VC method — 退出估值 ÷ (1 + IRR)^N × 稀释折扣

并对各轮（Seed / Pre-A / A / B / C）做估值轨迹。

---------------------------------------------------------------------------
ASSUMPTIONS
---------------------------------------------------------------------------

A. 5 年财务（来自 06_growth_cohort + 11_revenue_buildup + 8 损益）
B. 期末 ARR（Y5）= ¥9.51 亿；总营收 = ¥10.88 亿；毛利率 73.9%
C. 终值年（Y15）：营收 80 亿 / FCF margin 28%
D. WACC = 14% 中位 (区间 [11%, 18%])
E. 永续增长 g = 3.5%（中国宏观长期，CPI + 1.5%）
F. 可比 SaaS：
   - 中国 SaaS：PS 6-12× ARR (Wind 8×, 同花顺 7×, Topsoft 5×)
   - 全球 FinTech SaaS：PS 10-22× (Tiger 14×, Mobileye 18×)
   - InvestTech 偏溢价：PS 15× ARR (中位)
G. VC method 退出口径：
   - IPO 估值 = 18× ARR_Y8 (¥45 亿 ARR Y8 → ¥800 亿 / IPO post-money)

---------------------------------------------------------------------------
SOURCES
---------------------------------------------------------------------------
S1. Wind / 同花顺 / Topsoft 上市公司财报与估值
S2. Bessemer Cloud Index 2024
S3. SaaS Capital 2024 Benchmark
S4. Pitchbook PE Buyout Multiples 2024
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from _common import BRAND, PALETTE, fmt_cny, save_chart, write_json, ci, N_SIM, rng

r = rng()
N = N_SIM

revenue_y1_y5 = np.array([0.0595, 0.42, 1.75, 5.07, 10.88]) * 1e8
y5_arr = 9.51e8

revenue_growth_y6_y10 = r.triangular(0.45, 0.65, 0.85, N)
fcf_margin_y10 = r.triangular(0.20, 0.28, 0.36, N)
wacc = r.triangular(0.11, 0.14, 0.18, N)
terminal_g = r.triangular(0.025, 0.035, 0.045, N)


def dcf_value(rev_g, fcf_m, w, g):
    rev = revenue_y1_y5[-1]
    pv = 0.0
    for t in range(1, 6):
        rev *= 1 + rev_g * (0.95 ** (t-1))
        if t == 1:
            fcf = rev * (fcf_m * 0.4)
        elif t == 2:
            fcf = rev * (fcf_m * 0.65)
        elif t == 3:
            fcf = rev * (fcf_m * 0.80)
        else:
            fcf = rev * fcf_m
        pv += fcf / ((1 + w) ** t)
    terminal_fcf = rev * fcf_m * (1 + g)
    terminal_value = terminal_fcf / (w - g)
    pv += terminal_value / ((1 + w) ** 5)
    return pv

dcf_samples = np.array([
    dcf_value(revenue_growth_y6_y10[i], fcf_margin_y10[i], wacc[i], terminal_g[i])
    for i in range(min(20000, N))
])

ps_ratio = r.triangular(8.0, 15.0, 22.0, N)
arr_multiple_value = ps_ratio * y5_arr

vc_exit_arr = y5_arr * r.triangular(3.5, 4.7, 6.0, N)
vc_exit_ps = r.triangular(12.0, 18.0, 26.0, N)
exit_valuation = vc_exit_arr * vc_exit_ps
target_irr = r.triangular(0.30, 0.40, 0.55, N)
years_to_exit = 3
dilution = 1 - r.triangular(0.18, 0.25, 0.35, N)
vc_method_value = exit_valuation / ((1 + target_irr) ** years_to_exit) * dilution


def stat(s):
    m, lo, hi = ci(s)
    return {"median": float(m), "p5": float(lo), "p95": float(hi)}


valuations = {
    "DCF":          stat(dcf_samples),
    "Comparables":  stat(arr_multiple_value),
    "VC_method":    stat(vc_method_value),
}

weights = np.array([0.30, 0.40, 0.30])
weighted = (
    weights[0] * np.median(dcf_samples)
    + weights[1] * np.median(arr_multiple_value)
    + weights[2] * np.median(vc_method_value)
)

print(f"── InvestMind 估值（Y5 末，C 轮口径）──")
for k, v in valuations.items():
    print(f"  {k:<12s}  中位 {fmt_cny(v['median'])}  "
          f"(90% CI [{fmt_cny(v['p5'])}, {fmt_cny(v['p95'])}])")
print(f"  加权 (DCF/CMP/VC = 30/40/30): {fmt_cny(weighted)}")

round_track = {
    "Seed":  {"date": "2025-08", "amount":  10_000_000,  "post_money": 50_000_000},
    "Pre-A": {"date": "2026-06", "amount":  50_000_000,  "post_money": 250_000_000},
    "A":     {"date": "2027-09", "amount": 200_000_000,  "post_money": 1_000_000_000},
    "B":     {"date": "2029-03", "amount": 500_000_000,  "post_money": 3_500_000_000},
    "C":     {"date": "2030-09", "amount": 800_000_000,  "post_money": int(weighted)},
    "IPO_target_2032": {"date": "2032-Q4", "expected_post": 18_000_000_000},
}

result = {
    "as_of": "2026-04-30",
    "currency": "CNY",
    "y5_arr_CNY": float(y5_arr),
    "y5_total_revenue_CNY": float(revenue_y1_y5[-1]),
    "valuations_y5": valuations,
    "weighted_y5_CNY": float(weighted),
    "rounds": round_track,
    "weights": {"DCF": 0.30, "Comparables": 0.40, "VC": 0.30},
    "assumptions": {
        "revenue_growth_y6_y10": [0.45, 0.65, 0.85],
        "fcf_margin_y10": [0.20, 0.28, 0.36],
        "wacc": [0.11, 0.14, 0.18],
        "terminal_g": [0.025, 0.035, 0.045],
        "PS_ratio_comparables": [8.0, 15.0, 22.0],
        "exit_arr_multiple": [3.5, 4.7, 6.0],
        "exit_PS": [12.0, 18.0, 26.0],
        "target_irr": [0.30, 0.40, 0.55],
        "dilution": [0.18, 0.25, 0.35],
    },
    "sources": [
        "Wind/同花顺/Topsoft 财报",
        "Bessemer Cloud Index 2024",
        "SaaS Capital 2024",
        "Pitchbook PE Buyout Multiples 2024",
    ],
}

write_json("07_valuation_multimodel", result)


fig, axs = plt.subplots(1, 2, figsize=(12.0, 4.8))

methods = ["DCF", "Comparables", "VC Method", "加权"]
medians = [valuations["DCF"]["median"], valuations["Comparables"]["median"],
           valuations["VC_method"]["median"], weighted]
los = [valuations["DCF"]["p5"], valuations["Comparables"]["p5"],
       valuations["VC_method"]["p5"], 0]
his = [valuations["DCF"]["p95"], valuations["Comparables"]["p95"],
       valuations["VC_method"]["p95"], 0]

x = np.arange(len(methods))
colors = [BRAND["amber"], BRAND["teal"], BRAND["violet"], BRAND["blue"]]
axs[0].bar(x, medians, color=colors, alpha=0.92, width=0.55)
axs[0].errorbar(x[:3], medians[:3], yerr=[
    np.array(medians[:3]) - np.array(los[:3]),
    np.array(his[:3]) - np.array(medians[:3]),
], fmt="none", color=BRAND["ink"], capsize=4, lw=1.0)
for i, v in enumerate(medians):
    axs[0].text(i, v * 1.03, fmt_cny(v), ha="center", fontsize=9, color=BRAND["ink"])
axs[0].set_xticks(x, methods)
axs[0].set_ylabel("估值 (¥)")
axs[0].set_title("Y5 多模型估值对比（90% MC 区间）", pad=8)
axs[0].yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"¥{v/1e8:.0f}亿"))

names = ["Seed", "Pre-A", "A", "B", "C", "IPO\n2032"]
posts = [
    round_track["Seed"]["post_money"],
    round_track["Pre-A"]["post_money"],
    round_track["A"]["post_money"],
    round_track["B"]["post_money"],
    round_track["C"]["post_money"],
    round_track["IPO_target_2032"]["expected_post"],
]
axs[1].plot(names, posts, "o-", color=BRAND["blue"], lw=2.4, markersize=10)
for i, v in enumerate(posts):
    axs[1].annotate(fmt_cny(v), (i, v), xytext=(6, 6), textcoords="offset points",
                    fontsize=9, color=BRAND["ink"], fontweight="bold")
axs[1].set_yscale("log")
axs[1].set_ylabel("Post-money 估值 (¥ · log)")
axs[1].set_title("融资轨迹 · Seed → IPO（Post-money 估值演进）", pad=8)
axs[1].yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"¥{v/1e8:.0f}亿"))

fig.suptitle("§9.4 InvestMind 多模型加权估值与轮次轨迹",
             fontsize=13, fontweight="bold", y=1.02, color=BRAND["ink"])
fig.tight_layout()
save_chart(fig, "fig_07_valuation")

print("✓ 07_valuation_multimodel 完成")
