"""
14_monte_carlo_valuation.py
===========================

蒙特卡洛估值（N=200,000）+ 多模型加权综合 EV。对应 BP §9.4.3 / §9.4.4。
读取 12_valuation_dcf.json 与 13_valuation_comparables.json。

参数分布：
* Y5 收入：截断正态 N(基准, σ=18%)，[0.5x, 1.8x]
* Y5 营业利润率：截断正态 N(18%, 8pct)，[-15%, 45%]
* EV/Sales：三角 (3, 7, 14)
* WACC：N(14%, 2%)；g：N(3%, 1%)
* EV = 0.5×DCF(简化) + 0.5×EV/Sales
"""

from __future__ import annotations

import json
import numpy as np
import matplotlib.pyplot as plt

from _common import BRAND, PALETTE, fmt_cny, save_chart, write_json, OUT_DIR, N_SIM, rng
import data_sources as DS

with open(OUT_DIR / "10_financial_projections.json", encoding="utf-8") as f:
    fin = json.load(f)
with open(OUT_DIR / "12_valuation_dcf.json", encoding="utf-8") as f:
    dcf = json.load(f)
with open(OUT_DIR / "13_valuation_comparables.json", encoding="utf-8") as f:
    comp = json.load(f)

r = rng()
N = N_SIM
rev_base = fin["revenue_CNY"][-1]


def trunc_normal(mean, sd, lo, hi, n):
    x = r.normal(mean, sd, n)
    return np.clip(x, lo, hi)


rev_y5 = trunc_normal(rev_base, rev_base * 0.18, rev_base * 0.5, rev_base * 1.8, N)
op_margin = trunc_normal(0.18, 0.08, -0.15, 0.45, N)
evs = r.triangular(3.0, 7.0, 14.0, N)
wacc = trunc_normal(0.14, 0.02, 0.09, 0.20, N)
g = trunc_normal(0.03, 0.01, 0.005, 0.05, N)

# 简化 DCF：从 Y5 收入按 10 年 taper 增长，FCF=收入×营业利润率×0.75，终值 Gordon
def dcf_simplified():
    rev = rev_y5.copy()
    pv = np.zeros(N)
    growth = np.array([0.30, 0.27, 0.24, 0.21, 0.18])
    for t in range(5):
        rev = rev * (1 + growth[t])
        fcf = rev * op_margin * 0.75
        pv += fcf / (1 + wacc) ** (t + 1)
    terminal_fcf = rev * op_margin * 0.75 * (1 + g)
    tv = terminal_fcf / (wacc - g)
    pv += tv / (1 + wacc) ** 5
    return pv


dcf_samples = dcf_simplified()
evs_value = evs * rev_y5
ev_combined = 0.5 * dcf_samples + 0.5 * evs_value

qs = [5, 10, 25, 50, 75, 90, 95]
quantiles = {f"P{q}": round(float(np.percentile(ev_combined, q)) / 1e8, 1) for q in qs}
mc_mean_yi = round(float(np.mean(ev_combined)) / 1e8, 1)
mc_p50 = float(np.percentile(ev_combined, 50))

# ── 多模型加权综合（§9.4.4）─────────────────────────────────────────────────
methods = {
    "DCF(两阶段+退出)": {"weight": 0.25, "ev_yi": dcf["EV_two_stage_yi"]},
    "DCF(Gordon对照)": {"weight": 0.10, "ev_yi": dcf["EV_gordon_yi"]},
    "EV/Sales(中位)": {"weight": 0.20, "ev_yi": comp["EV_Sales_valuation_yi"]["median"]},
    "EV/EBITDA(中位)": {"weight": 0.15, "ev_yi": comp["EV_EBITDA_valuation_yi"]["median"]},
    "蒙特卡洛(P50)": {"weight": 0.30, "ev_yi": round(mc_p50 / 1e8, 1)},
}
weighted_ev_yi = round(sum(m["weight"] * m["ev_yi"] for m in methods.values()), 1)

payload = {
    "as_of": DS.AS_OF, "currency": "CNY", "monte_carlo_n": int(N),
    "mc_quantiles_yi": quantiles, "mc_mean_yi": mc_mean_yi,
    "weighted_methods": methods, "weighted_EV_yi": weighted_ev_yi,
    "investor_range_yi": [110, 160],
    "c_round_post_money_yi": round(DS.ROUNDS["C"]["post_money"] / 1e8, 0),
    "sources": ["蒙特卡洛 N=200k seed=42", "DCF + 可比综合加权"],
}

print("── 蒙特卡洛估值（N=200k）──")
for k, v in quantiles.items():
    print(f"  {k}: ¥{v}亿")
print(f"  均值: ¥{mc_mean_yi}亿")
print(f"  加权综合 EV = ¥{weighted_ev_yi}亿 （投资人区间 110-160 亿；C 轮 Post 80 亿留上行空间）")

write_json("14_monte_carlo_valuation", payload)

# ── 图：MC 直方图 + 加权对比 ───────────────────────────────────────────────
fig, axs = plt.subplots(1, 2, figsize=(12.4, 4.8))
clip = np.percentile(ev_combined, 99)
axs[0].hist(np.clip(ev_combined, 0, clip) / 1e8, bins=80, color=BRAND["blue"], alpha=0.75, edgecolor="white")
for q, c in [(10, BRAND["amber"]), (50, BRAND["red"]), (90, BRAND["teal"])]:
    v = np.percentile(ev_combined, q) / 1e8
    axs[0].axvline(v, color=c, lw=2, ls="--", label=f"P{q}=¥{v:.0f}亿")
axs[0].set_xlabel("企业价值 EV (¥ 亿)")
axs[0].set_ylabel("MC 样本频次")
axs[0].set_title("蒙特卡洛 EV 分布 (N=200k)", pad=8)
axs[0].legend(fontsize=9)

mnames = list(methods.keys()) + ["加权综合"]
mvals = [methods[k]["ev_yi"] for k in methods] + [weighted_ev_yi]
mcolors = [BRAND["amber"], BRAND["grey"], BRAND["teal"], BRAND["violet"], BRAND["blue"], BRAND["red"]]
axs[1].barh(mnames, mvals, color=mcolors, alpha=0.9)
for i, v in enumerate(mvals):
    axs[1].text(v + 2, i, f"¥{v:.0f}亿", va="center", fontsize=9, color=BRAND["ink"])
axs[1].axvline(80, color=BRAND["ink"], ls=":", lw=1.5, label="C 轮 Post ¥80亿")
axs[1].set_xlabel("EV (¥ 亿)")
axs[1].set_title(f"多模型加权 → ¥{weighted_ev_yi:.0f}亿", pad=8)
axs[1].legend(fontsize=9)
axs[1].invert_yaxis()
fig.suptitle("§9.4 多模型加权估值", fontsize=13, fontweight="bold", color=BRAND["ink"], y=1.02)
fig.tight_layout()
save_chart(fig, "fig_14_valuation_montecarlo")

print("✓ 14_monte_carlo_valuation 完成 → JSON + fig_14_valuation_montecarlo.png")
