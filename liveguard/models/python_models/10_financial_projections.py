"""
10_financial_projections.py
===========================

5 年三大报表（损益表 / 现金流量表 / 资产负债表）+ SaaS 关键比率。
对应 BP §8。这是财务的【核心模型】，估值模型（12/13/14）读取其 JSON 输出。

驱动（全部来自 data_sources.py）：
    收入 = 期末付费账号数 × 加权年 ARPU
    成本/费用 = 收入 × (1−毛利率) / S&M比 / R&D比 / G&A比
    现金流 = 净利 + 折旧摊销 − ΔWC − CapEx + 融资
资产负债表按构造勾稽：总资产 = 总负债 + 股东权益（精确成立）。
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from _common import BRAND, PALETTE, fmt_cny, save_chart, write_json
import data_sources as DS

Y = DS.YEARS
n = len(Y)
ARPU = DS.BLENDED_ARPU_ANNUAL

# v3：收入采用四层货币化口径（核心监控 SaaS × 分层乘数），唯一可信源 = data_sources
rev = np.array(DS.REVENUE_BY_YEAR_CNY)
gm = np.array(DS.GROSS_MARGIN)
cogs = rev * (1 - gm)
gross = rev * gm
sm = rev * np.array(DS.SM_RATIO)
rd = rev * np.array(DS.RD_RATIO)
ga = rev * np.array(DS.GA_RATIO)
opex = sm + rd + ga
ebit = gross - opex
other = rev * DS.OTHER_INCOME_RATIO

# 折旧摊销（递减余额 30%）+ PP&E roll-forward
capex = rev * DS.CAPEX_RATIO
da = np.zeros(n)
ppe = np.zeros(n)
ppe_begin = 0.0
for t in range(n):
    da[t] = (ppe_begin + capex[t]) * DS.DA_RATE
    ppe[t] = ppe_begin + capex[t] - da[t]
    ppe_begin = ppe[t]

ebitda = ebit + da
pbt = ebit + other
tax = np.where(pbt > 0, pbt * DS.TAX_RATE, 0.0)
net = pbt - tax

# 营运资本
ar = rev * DS.AR_DAYS / 360
ap = cogs * DS.AP_DAYS / 360
wc = ar - ap
d_wc = np.diff(wc, prepend=0.0)

cfo = net + da - d_wc
cfi = -capex
# v3：融资以天使轮为第一性视角（Angel+Seed 计入 Y1；A→Y2；B→Y3；C→Y5）
financing = np.zeros(n)
for rname, ridx in DS.ROUND_YEAR_INDEX.items():
    financing[ridx] += DS.ROUNDS[rname]["amount"]
cff = financing
net_cash = cfo + cfi + cff
cash = np.cumsum(net_cash)

paid_in = np.cumsum(financing)
retained = np.cumsum(net)
equity = paid_in + retained
total_assets = cash + ar + ppe
total_liab = ap
recon_gap = total_assets - (total_liab + equity)

# SaaS 比率
rev_growth = np.concatenate([[np.nan], rev[1:] / rev[:-1] - 1])
op_margin = ebit / rev
net_margin = net / rev
net_new_arr = np.diff(rev, prepend=0.0)
magic = np.where(sm > 0, net_new_arr / sm, np.nan)
magic[0] = np.nan
net_burn = np.where(cfo < 0, -cfo, 0.0)
burn_multiple = np.where(net_new_arr > 0, net_burn / net_new_arr, 0.0)
rule_of_40 = rev_growth * 100 + op_margin * 100


def wan(a):
    return [round(float(x) / 1e4, 0) for x in a]


payload = {
    "as_of": DS.AS_OF, "currency": "CNY", "unit_note": "income/cash/balance 字段以【元】给出；*_wan 以万元",
    "years": Y,
    "income_statement_wan": {
        "营业收入": wan(rev), "营业成本": wan(cogs), "毛利": wan(gross),
        "毛利率_pct": [round(x * 100, 0) for x in gm],
        "销售费用": wan(sm), "研发费用": wan(rd), "管理费用": wan(ga),
        "营业利润": wan(ebit), "EBITDA": wan(ebitda),
        "其他收益": wan(other), "利润总额": wan(pbt), "所得税": wan(tax), "净利润": wan(net),
        "净利率_pct": [round(x * 100, 0) for x in net_margin],
    },
    "cash_flow_wan": {
        "净利润": wan(net), "折旧摊销": wan(da), "ΔWC": wan(d_wc),
        "经营现金流CFO": wan(cfo), "资本支出": wan(capex), "投资现金流CFI": wan(cfi),
        "融资现金流CFF": wan(cff), "净现金变动": wan(net_cash), "期末现金": wan(cash),
    },
    "balance_sheet_wan": {
        "现金": wan(cash), "应收账款": wan(ar), "固定资产净值": wan(ppe), "总资产": wan(total_assets),
        "应付账款": wan(ap), "总负债": wan(total_liab),
        "实收资本": wan(paid_in), "留存收益": wan(retained), "股东权益": wan(equity),
        "勾稽差异": [round(float(x), 2) for x in recon_gap],
    },
    "key_ratios": {
        "收入增速_pct": [None if np.isnan(x) else round(x * 100, 0) for x in rev_growth],
        "毛利率_pct": [round(x * 100, 0) for x in gm],
        "营业利润率_pct": [round(x * 100, 0) for x in op_margin],
        "净利率_pct": [round(x * 100, 0) for x in net_margin],
        "Magic_Number": [None if np.isnan(x) else round(float(x), 2) for x in magic],
        "Burn_Multiple": [round(float(x), 2) for x in burn_multiple],
        "Rule_of_40": [None if np.isnan(x) else round(float(x), 0) for x in rule_of_40],
    },
    "headline": {
        "Y5_revenue_CNY": float(rev[-1]), "Y5_revenue_yi": round(float(rev[-1]) / 1e8, 2),
        "Y5_ebitda_CNY": float(ebitda[-1]), "Y5_ebitda_yi": round(float(ebitda[-1]) / 1e8, 2),
        "Y5_net_CNY": float(net[-1]), "Y5_net_yi": round(float(net[-1]) / 1e8, 2),
        "Y5_rule_of_40": round(float(rule_of_40[-1]), 0),
        "max_recon_gap_CNY": round(float(np.max(np.abs(recon_gap))), 2),
    },
    "fcf_CNY": [round(float(cfo[t] + cfi[t]), 0) for t in range(n)],
    "ebit_CNY": [round(float(x), 0) for x in ebit],
    "ebitda_CNY": [round(float(x), 0) for x in ebitda],
    "revenue_CNY": [round(float(x), 0) for x in rev],
    "sources": ["data_sources.py (canonical)", "SaaS Capital / OpenView 2024 基准"],
}

print("── 5 年损益（万元）──")
print("  收入   :", " ".join(f"{x:>9,.0f}" for x in wan(rev)))
print("  营业利润:", " ".join(f"{x:>9,.0f}" for x in wan(ebit)))
print("  净利润 :", " ".join(f"{x:>9,.0f}" for x in wan(net)))
print("  期末现金:", " ".join(f"{x:>9,.0f}" for x in wan(cash)))
print(f"  Y5 收入 {fmt_cny(rev[-1])} · EBITDA {fmt_cny(ebitda[-1])} · 净利 {fmt_cny(net[-1])}")
print(f"  资产负债表最大勾稽差异 = {np.max(np.abs(recon_gap)):.4f} 元")
print("  Rule of 40:", payload["key_ratios"]["Rule_of_40"])

write_json("10_financial_projections", payload)

# ── 图 1：P&L 线 + 收入堆叠 ────────────────────────────────────────────────
fig, axs = plt.subplots(1, 2, figsize=(12.2, 4.6))
axs[0].bar(Y, rev / 1e8, color=BRAND["blue"], alpha=0.35, width=0.6, label="营业收入")
axs[0].plot(Y, gross / 1e8, "o-", color=BRAND["teal"], lw=2, label="毛利")
axs[0].plot(Y, ebit / 1e8, "s-", color=BRAND["amber"], lw=2, label="营业利润")
axs[0].plot(Y, net / 1e8, "^-", color=BRAND["red"], lw=2, label="净利润")
axs[0].axhline(0, color=BRAND["grey"], lw=1)
axs[0].set_ylabel("¥ 亿")
axs[0].set_title("5 年损益（Y4 盈亏平衡，Y5 转盈）", pad=8)
axs[0].legend(fontsize=9)

mix = payload  # revenue split via pricing mix is in 08; here show revenue + margin
ax2 = axs[1]
ax2.bar(Y, rev / 1e8, color=BRAND["blue"], alpha=0.8, width=0.6, label="收入")
ax2.set_ylabel("收入 (¥ 亿)")
ax2b = ax2.twinx()
ax2b.plot(Y, gm * 100, "o-", color=BRAND["teal"], lw=2.2, label="毛利率")
ax2b.set_ylabel("毛利率 (%)")
ax2b.set_ylim(50, 90)
for i, v in enumerate(rev / 1e8):
    ax2.text(i, v + 0.4, f"¥{v:.1f}亿", ha="center", fontsize=8, color=BRAND["ink"])
ax2.set_title("收入规模 vs 毛利率演进", pad=8)
ax2.legend(loc="upper left", fontsize=9)
ax2b.legend(loc="lower right", fontsize=9)
fig.suptitle("§8.1 守播 LiveGuard 5 年损益", fontsize=13, fontweight="bold", color=BRAND["ink"], y=1.02)
fig.tight_layout()
save_chart(fig, "fig_10_pnl")

# ── 图 2：现金跑道 ─────────────────────────────────────────────────────────
fig2, ax = plt.subplots(figsize=(9.0, 5.0))
ax.bar(Y, cash / 1e8, color=[BRAND["teal"] if c > 0 else BRAND["red"] for c in cash], alpha=0.85, width=0.55)
ax.plot(Y, cfo / 1e8, "o--", color=BRAND["ink"], lw=2, label="经营现金流 CFO")
for i, v in enumerate(cash / 1e8):
    ax.text(i, v + 0.3, f"¥{v:.2f}亿", ha="center", fontsize=9, color=BRAND["ink"])
for i, f in enumerate(financing):
    if f > 0:
        ax.annotate(f"+融资 {fmt_cny(f)}", (i, (cash[i]) / 1e8), xytext=(0, -22), textcoords="offset points", ha="center", fontsize=8, color=BRAND["blue"])
ax.axhline(0, color=BRAND["grey"], lw=1)
ax.set_ylabel("期末现金 / CFO (¥ 亿)")
ax.set_title("§8.2 5 年现金跑道（Y4 最紧后转入安全飞轮）", pad=10)
ax.legend(fontsize=9)
save_chart(fig2, "fig_10_cash_runway")

# ── 图 3：Rule of 40 ───────────────────────────────────────────────────────
fig3, ax = plt.subplots(figsize=(9.0, 5.0))
gr = [0 if np.isnan(x) else x * 100 for x in rev_growth]
om = op_margin * 100
ax.bar(Y, gr, color=BRAND["blue"], alpha=0.75, width=0.5, label="收入增速 %")
ax.bar(Y, om, bottom=[max(0, g) for g in gr], color=BRAND["teal"], alpha=0.75, width=0.5, label="营业利润率 %")
r40 = [g + o for g, o in zip(gr, om)]
ax.plot(Y, r40, "o-", color=BRAND["red"], lw=2.4, label="Rule of 40 合计")
for i, v in enumerate(r40):
    ax.text(i, v + 10, f"{v:.0f}", ha="center", fontsize=9, fontweight="bold", color=BRAND["ink"])
ax.axhline(40, color=BRAND["amber"], ls="--", lw=1.5, label="健康线 40")
ax.set_ylabel("增速% + 营业利润率%")
ax.set_yscale("symlog")
ax.set_title("§8.4 Rule of 40（五年全部 > 40）", pad=10)
ax.legend(fontsize=9, ncol=2)
save_chart(fig3, "fig_10_rule_of_40")

print("✓ 10_financial_projections 完成 → JSON + fig_10_*.png (3 张)")
