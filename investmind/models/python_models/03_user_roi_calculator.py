"""
03_user_roi_calculator.py
=========================

个人投资者使用 InvestMind 后年化 IRR 提升 + 决策时间节省 + 综合 ROI。

---------------------------------------------------------------------------
ASSUMPTIONS
---------------------------------------------------------------------------

A. 个人投资者基线（baseline · 不使用 InvestMind）
   - 早期股权年化 IRR 中位数：8% （区间 [-5%, 22%]，长右尾）
   - 决策时间：每项目 18 小时尽调 + 评估
   - 1 年项目数：6 个（Pro 用户）

B. 使用 InvestMind 后（treated）
   - 排序引擎过滤掉负收益项目 → 胜率提升 8 → 12pp（详细见模型 04）
   - 盈亏比改进 1.6× → 2.4× 中位
   - 用 IRR 增量分布：使用 lognormal 增量 4-9pp
   - 决策时间：每项目 4 小时（自动报告 + 排序）→ 节省 14 小时/项目

C. 综合 ROI
   - 时间机会成本 ¥600/h（专业人士平均）
   - 订阅费按 Pro 档 ¥4,988/yr
   - 增量年化收益：增量 IRR × 平均资金量

---------------------------------------------------------------------------
SOURCES
---------------------------------------------------------------------------
S1. AngelList 2024 Letter：合格投资人 IRR 分布
S2. CB Insights Angel Investing Returns Study 2024
S3. 中国证券业协会《个人投资人决策行为调查 2024》
S4. 中欧国际工商学院 私人银行年报 2024
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from _common import BRAND, PALETTE, ci, fmt_cny, fmt_pct, save_chart, write_json, N_SIM, rng

r = rng()
N = N_SIM

baseline_irr = r.normal(0.08, 0.10, N)
baseline_irr = np.clip(baseline_irr, -0.30, 0.50)

irr_uplift = r.lognormal(np.log(0.06), 0.40, N)
treated_irr = baseline_irr + irr_uplift

baseline_decision_h = r.triangular(12, 18, 28, N)
treated_decision_h = r.triangular(2.5, 4.0, 6.5, N)
time_saved_h = baseline_decision_h - treated_decision_h

projects_per_year = r.triangular(3, 6, 12, N).astype(int)
hourly_rate = r.triangular(400, 600, 1200, N)

avg_capital_per_project = r.lognormal(np.log(120_000), 0.55, N)
total_capital = avg_capital_per_project * projects_per_year

irr_dollar_uplift = total_capital * irr_uplift
time_dollar_savings = time_saved_h * projects_per_year * hourly_rate

annual_subscription = 4988

net_benefit = irr_dollar_uplift + time_dollar_savings - annual_subscription
roi_multiple = net_benefit / annual_subscription

def st(s):
    m, lo, hi = ci(s)
    return {"median": float(m), "p5": float(lo), "p95": float(hi)}

result = {
    "as_of": "2026-04-30",
    "currency": "CNY",
    "monte_carlo_n": int(N_SIM),
    "annual_subscription_CNY": annual_subscription,
    "baseline_irr": st(baseline_irr),
    "treated_irr":  st(treated_irr),
    "irr_uplift":   st(irr_uplift),
    "decision_hours_baseline":   st(baseline_decision_h),
    "decision_hours_treated":    st(treated_decision_h),
    "time_saved_hours_per_project": st(time_saved_h),
    "projects_per_year": st(projects_per_year),
    "avg_capital_per_project_CNY": st(avg_capital_per_project),
    "total_capital_per_year_CNY": st(total_capital),
    "irr_dollar_uplift_CNY": st(irr_dollar_uplift),
    "time_dollar_savings_CNY": st(time_dollar_savings),
    "net_benefit_CNY": st(net_benefit),
    "roi_multiple_x": st(roi_multiple),
    "prob_roi_gt_5x": float(np.mean(roi_multiple > 5)),
    "prob_roi_gt_10x": float(np.mean(roi_multiple > 10)),
    "assumptions": {
        "baseline_irr_mean_pct":  8,
        "irr_uplift_mode_pct":    6,
        "decision_hours_baseline_mode": 18,
        "decision_hours_treated_mode":  4,
        "annual_subscription_CNY": annual_subscription,
    },
    "sources": [
        "AngelList 2024 Letter",
        "CB Insights Angel Investing Returns 2024",
        "中国证券业协会个人投资人决策行为调查 2024",
        "中欧国际工商学院 私人银行年报 2024",
    ],
}

print("── 个人投资者 ROI 计算（Pro 档 · MC N=200k）──")
print(f"  基线 IRR  : {fmt_pct(result['baseline_irr']['median'])}  "
      f"(90% CI [{fmt_pct(result['baseline_irr']['p5'])}, {fmt_pct(result['baseline_irr']['p95'])}])")
print(f"  Treated   : {fmt_pct(result['treated_irr']['median'])}  "
      f"(90% CI [{fmt_pct(result['treated_irr']['p5'])}, {fmt_pct(result['treated_irr']['p95'])}])")
print(f"  IRR 增量 : {fmt_pct(result['irr_uplift']['median'])}")
print(f"  时间节省 : {result['time_saved_hours_per_project']['median']:.1f} h/项目, "
      f"年总节省 ≈ {result['time_dollar_savings_CNY']['median']/1e4:.1f} 万元")
print(f"  IRR 增量金额: {fmt_cny(result['irr_dollar_uplift_CNY']['median'])}/年")
print(f"  ROI 倍数  : {result['roi_multiple_x']['median']:.1f}× (90% CI "
      f"[{result['roi_multiple_x']['p5']:.1f}×, {result['roi_multiple_x']['p95']:.1f}×])")
print(f"  P(ROI > 5×) : {result['prob_roi_gt_5x']*100:.1f}%, "
      f"P(ROI > 10×) : {result['prob_roi_gt_10x']*100:.1f}%")

write_json("03_user_roi_calculator", result)

fig, axs = plt.subplots(1, 2, figsize=(12.0, 4.6))

bins = np.linspace(-0.30, 0.50, 60)
axs[0].hist(baseline_irr, bins=bins, color=BRAND["amber"], alpha=0.7,
            edgecolor="white", label=f"Baseline 中位 {fmt_pct(np.median(baseline_irr))}")
axs[0].hist(treated_irr,  bins=bins, color=BRAND["teal"], alpha=0.7,
            edgecolor="white", label=f"Treated  中位 {fmt_pct(np.median(treated_irr))}")
axs[0].axvline(np.median(baseline_irr), color=BRAND["amber"], ls="--", lw=1.4)
axs[0].axvline(np.median(treated_irr),  color=BRAND["teal"],  ls="--", lw=1.4)
axs[0].set_xlabel("年化 IRR")
axs[0].set_ylabel("MC 频次")
axs[0].set_title("个人投资者 IRR 分布迁移", pad=8)
axs[0].xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v*100:.0f}%"))
axs[0].legend()

categories = ["基线\n年化 IRR\n金额", "+ IRR 增量\n金额", "+ 时间节省\n机会成本", "− 订阅费", "= 净收益"]
base = np.median(baseline_irr) * np.median(total_capital)
items = [
    base,
    np.median(irr_dollar_uplift),
    np.median(time_dollar_savings),
    -annual_subscription,
    np.median(net_benefit) + base,
]
running = np.cumsum([items[0], items[1], items[2], items[3]])
running = np.concatenate([[items[0]], running])

heights = [base, items[1], items[2], items[3], items[4]]
positions = np.arange(len(categories))
colors = [BRAND["grey"], BRAND["teal"], BRAND["blue"], BRAND["red"], BRAND["amber"]]

cumulative_bottom = [
    0,
    base,
    base + items[1],
    base + items[1] + items[2],
    0,
]
cumulative_height = [
    base,
    items[1],
    items[2],
    items[3],
    items[4],
]

for i, (b, h, c) in enumerate(zip(cumulative_bottom, cumulative_height, colors)):
    axs[1].bar(positions[i], h, bottom=b, color=c, alpha=0.92, edgecolor="white")
    axs[1].text(positions[i], b + h + (max(items[4], 1) * 0.02),
                fmt_cny(abs(h)), ha="center", fontsize=9, color=BRAND["ink"])

axs[1].set_xticks(positions, categories, fontsize=9)
axs[1].set_ylabel("金额 (¥)")
axs[1].set_title("年度 ROI 瀑布（中位口径）", pad=8)
axs[1].axhline(0, color=BRAND["line"], lw=0.6)

fig.suptitle("§5.5 InvestMind 个人投资者 ROI 计算（Pro 档）",
             fontsize=13, fontweight="bold", y=1.02, color=BRAND["ink"])
fig.tight_layout()
save_chart(fig, "fig_03_user_roi")

print("✓ 03_user_roi_calculator 完成")
