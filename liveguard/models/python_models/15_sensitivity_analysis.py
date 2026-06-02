"""
15_sensitivity_analysis.py
==========================

龙卷风敏感性：Y5 收入 + 企业价值 EV。对应 BP §8.5。
通过逐参数扰动重算（而非线性近似）测度影响。读取 10/12 JSON。
"""

from __future__ import annotations

import json
import numpy as np
import matplotlib.pyplot as plt

from _common import BRAND, PALETTE, save_chart, write_json, OUT_DIR
import data_sources as DS

with open(OUT_DIR / "10_financial_projections.json", encoding="utf-8") as f:
    fin = json.load(f)
with open(OUT_DIR / "12_valuation_dcf.json", encoding="utf-8") as f:
    dcf = json.load(f)

# ── 收入敏感性：通过 ARPU 组成扰动 ─────────────────────────────────────────
P = DS.PRICING
cust_y5 = DS.CUSTOMERS_EOY[-1]


def arpu(prices, mixes):
    return sum(prices[s] * mixes[s] for s in P)


base_prices = {s: P[s]["annual"] for s in P}
base_mixes = {s: P[s]["mix"] for s in P}
base_arpu = arpu(base_prices, base_mixes)
base_rev = cust_y5 * base_arpu


def rev_with(prices=None, mixes=None):
    pr = dict(base_prices); mx = dict(base_mixes)
    if prices:
        pr.update(prices)
    if mixes:
        mx.update(mixes)
    return cust_y5 * arpu(pr, mx)


rev_drivers = []
for label, lo_kw, hi_kw in [
    ("Enterprise 单价 ±20%", {"prices": {"Enterprise": base_prices["Enterprise"] * 0.8}}, {"prices": {"Enterprise": base_prices["Enterprise"] * 1.2}}),
    ("Pro 价格 ±20%", {"prices": {"Pro": base_prices["Pro"] * 0.8}}, {"prices": {"Pro": base_prices["Pro"] * 1.2}}),
    ("Starter 价格 ±20%", {"prices": {"Starter": base_prices["Starter"] * 0.8}}, {"prices": {"Starter": base_prices["Starter"] * 1.2}}),
    ("Enterprise 占比 ±2pct", {"mixes": {"Enterprise": 0.03, "Starter": 0.72}}, {"mixes": {"Enterprise": 0.07, "Starter": 0.68}}),
    ("Pro 占比 ±5pct", {"mixes": {"Pro": 0.20, "Starter": 0.75}}, {"mixes": {"Pro": 0.30, "Starter": 0.65}}),
]:
    lo = rev_with(**lo_kw); hi = rev_with(**hi_kw)
    rev_drivers.append({
        "param": label,
        "low_pct": round((lo - base_rev) / base_rev * 100, 1),
        "high_pct": round((hi - base_rev) / base_rev * 100, 1),
        "range_pp": round(abs(hi - lo) / base_rev * 100, 1),
    })
rev_drivers.sort(key=lambda d: d["range_pp"], reverse=True)

# ── EV 敏感性：扰动 DCF 输入 ───────────────────────────────────────────────
base_ev = dcf["EV_two_stage_CNY"]
pv_exp = dcf["pv_explicit_CNY"]
pv_trans = dcf["pv_transition_CNY"]
term_ebitda = dcf["terminal_ebitda_y10_yi"] * 1e8
WACC = DS.WACC
EXIT = DS.EXIT_EV_EBITDA


def ev_with(exit_mult=EXIT, wacc=WACC, ebitda=term_ebitda, fcf_scale=1.0):
    tv = exit_mult * ebitda
    pv_term = tv / (1 + wacc) ** 10
    # pv_explicit + pv_transition 随 wacc/fcf 近似缩放
    scale = ((1 + WACC) / (1 + wacc)) ** 7  # 过渡期平均贴现年限近似
    return (pv_exp + pv_trans * scale) * fcf_scale + pv_term


ev_drivers = []
for label, lo_kw, hi_kw in [
    ("Y10 EBITDA ±25%", {"ebitda": term_ebitda * 0.75}, {"ebitda": term_ebitda * 1.25}),
    ("退出倍数 ±5×", {"exit_mult": EXIT - 5}, {"exit_mult": EXIT + 5}),
    ("FCF ±20%", {"fcf_scale": 0.8}, {"fcf_scale": 1.2}),
    ("WACC ±2pct", {"wacc": WACC + 0.02}, {"wacc": WACC - 0.02}),
]:
    lo = ev_with(**lo_kw); hi = ev_with(**hi_kw)
    ev_drivers.append({
        "param": label,
        "low_pct": round((lo - base_ev) / base_ev * 100, 1),
        "high_pct": round((hi - base_ev) / base_ev * 100, 1),
        "range_pp": round(abs(hi - lo) / base_ev * 100, 1),
    })
ev_drivers.sort(key=lambda d: d["range_pp"], reverse=True)

payload = {
    "as_of": DS.AS_OF,
    "base_y5_core_saas_revenue_yi": round(base_rev / 1e8, 2),
    "base_y5_total_revenue_yi": round(DS.REVENUE_BY_YEAR_CNY[-1] / 1e8, 2),
    "base_ev_yi": round(base_ev / 1e8, 1),
    "revenue_tornado_note": "收入龙卷风针对【核心监控 SaaS 层】定价/结构驱动；扩展层见 20_business_model_layers。",
    "revenue_tornado": rev_drivers,
    "ev_tornado": ev_drivers,
    "sources": ["逐参数重算敏感性", "BP §10"],
}

print("── Y5 收入敏感性 ──")
for d in rev_drivers:
    print(f"  {d['param']:<22s} [{d['low_pct']:+.1f}%, {d['high_pct']:+.1f}%]  幅度 {d['range_pp']}pp")
print("── EV 敏感性 ──")
for d in ev_drivers:
    print(f"  {d['param']:<22s} [{d['low_pct']:+.1f}%, {d['high_pct']:+.1f}%]  幅度 {d['range_pp']}pp")

write_json("15_sensitivity_analysis", payload)


def tornado(ax, drivers, title):
    labels = [d["param"] for d in drivers][::-1]
    lows = [d["low_pct"] for d in drivers][::-1]
    highs = [d["high_pct"] for d in drivers][::-1]
    y = np.arange(len(labels))
    for i in range(len(labels)):
        ax.barh(y[i], highs[i], color=BRAND["teal"], alpha=0.85)
        ax.barh(y[i], lows[i], color=BRAND["red"], alpha=0.85)
        ax.text(highs[i] + 0.4, y[i], f"{highs[i]:+.0f}%", va="center", fontsize=8, color=BRAND["ink"])
        ax.text(lows[i] - 0.4, y[i], f"{lows[i]:+.0f}%", va="center", ha="right", fontsize=8, color=BRAND["ink"])
    ax.set_yticks(y, labels, fontsize=9)
    ax.axvline(0, color=BRAND["ink"], lw=1)
    ax.set_xlabel("相对基准变化 (%)")
    ax.set_title(title, pad=8)
    ax.grid(axis="y", visible=False)


fig, axs = plt.subplots(1, 2, figsize=(13.0, 4.8))
tornado(axs[0], rev_drivers, f"核心 SaaS 收入敏感性（基准 ¥{base_rev/1e8:.1f}亿）")
tornado(axs[1], ev_drivers, f"企业价值 EV 敏感性（基准 ¥{base_ev/1e8:.0f}亿）")
fig.suptitle("§10 龙卷风敏感性分析", fontsize=13, fontweight="bold", color=BRAND["ink"], y=1.02)
fig.tight_layout()
save_chart(fig, "fig_15_sensitivity_tornado")

print("✓ 15_sensitivity_analysis 完成 → JSON + fig_15_sensitivity_tornado.png")
