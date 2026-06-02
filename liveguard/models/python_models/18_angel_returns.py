"""
18_angel_returns.py
===================

天使投资人 5 年回报（守播 LiveGuard v3 全篇头条指标）。对应 BP §12。

读取：
  * 11_fundraising_dilution.json → 天使全稀释最终股比（Angel→Seed→A→B→C）
  * 14_monte_carlo_valuation.json → 加权综合 EV 与 MC 分位

口径：天使 ¥1,000 万 @ Post ¥5,000 万（持股 20%），全稀释后 C 轮 ≈ 8.8%。
  * 5 年纸面市值（按 C 轮 Post-money 计）
  * 四档"条件于成功退出"情景（保守 M&A / 中性=加权 EV / 乐观 IPO / 极乐观）
  * MOIC = 退出回报 / 投入；IRR_5y = MOIC^(1/5) − 1

注：四档情景均为【条件于公司成功走到退出】；纳入失败概率后的"概率加权期望收益"见 §11（19 模型）。
"""

from __future__ import annotations

import json
import numpy as np
import matplotlib.pyplot as plt

from _common import BRAND, PALETTE, fmt_cny, save_chart, write_json, OUT_DIR
import data_sources as DS

with open(OUT_DIR / "11_fundraising_dilution.json", encoding="utf-8") as f:
    fund = json.load(f)
with open(OUT_DIR / "14_monte_carlo_valuation.json", encoding="utf-8") as f:
    val = json.load(f)

angel_invest = DS.ANGEL_INVEST_CNY
angel_post = DS.ROUNDS["Angel"]["post_money"]
angel_entry_pct = angel_invest / angel_post
angel_final_pct = fund["angel_final_stake_pct"] / 100.0
hold = DS.ANGEL_HOLD_YEARS

weighted_ev = val["weighted_EV_yi"] * 1e8
mc = val["mc_quantiles_yi"]
c_post = DS.ROUNDS["C"]["post_money"]


def moic_irr(exit_ev, stake, invest, years):
    payout = exit_ev * stake
    moic = payout / invest
    irr = moic ** (1 / years) - 1
    return payout, moic, irr


# 5 年纸面市值（按 C 轮 Post-money 计，未退出的账面 mark）
paper_payout, paper_moic, paper_irr = moic_irr(c_post, angel_final_pct, angel_invest, hold)

# 四档"条件于成功退出"情景
scenarios = {
    "保守 (战略并购)":       130e8,                 # 略高于 C 轮 Post 的并购
    "中性 (加权综合 EV)":    weighted_ev,           # ≈ ¥222 亿
    "乐观 (IPO, MC P90)":    mc["P90"] * 1e8,       # ≈ ¥352 亿
    "极乐观 (头部 IPO)":     500e8,
}
exit_table = {}
for label, ev in scenarios.items():
    payout, moic, irr = moic_irr(ev, angel_final_pct, angel_invest, hold)
    exit_table[label] = {
        "exit_EV_yi": round(ev / 1e8, 0),
        "angel_payout_yi": round(payout / 1e8, 2),
        "MOIC": round(moic, 1),
        "IRR_5y_pct": round(irr * 100, 0),
    }

payload = {
    "as_of": DS.AS_OF, "currency": "CNY", "version": DS.VERSION,
    "angel_invest_CNY": angel_invest, "angel_invest_disp": fmt_cny(angel_invest),
    "angel_post_money_CNY": angel_post, "angel_post_money_disp": fmt_cny(angel_post),
    "angel_entry_stake_pct": round(angel_entry_pct * 100, 1),
    "angel_final_stake_pct": round(angel_final_pct * 100, 2),
    "dilution_path_pct": fund["angel_stake_path_pct"],
    "hold_years": hold,
    "paper_mark_at_C": {
        "basis": "C 轮 Post-money", "EV_yi": round(c_post / 1e8, 0),
        "angel_value_yi": round(paper_payout / 1e8, 2),
        "MOIC": round(paper_moic, 1), "IRR_5y_pct": round(paper_irr * 100, 0),
    },
    "exit_scenarios_conditional": exit_table,
    "note": "四档为条件于成功退出；概率加权期望收益见 19_success_probability（§11）。",
    "sources": ["11_fundraising_dilution (全稀释)", "14_monte_carlo_valuation (加权 EV / MC 分位)"],
}

print("── 天使 5 年回报（条件于成功退出）──")
print(f"  入场: {fmt_cny(angel_invest)} @ Post {fmt_cny(angel_post)} = {angel_entry_pct*100:.0f}%  → 全稀释后 {angel_final_pct*100:.2f}%")
print(f"  5 年纸面 mark（C 轮 Post {fmt_cny(c_post)}）: {fmt_cny(paper_payout)} · MOIC {paper_moic:.0f}× · IRR {paper_irr*100:.0f}%")
for label, d in exit_table.items():
    print(f"  {label:<20s} EV ¥{d['exit_EV_yi']:.0f}亿 → 回报 ¥{d['angel_payout_yi']:.1f}亿 · MOIC {d['MOIC']:.0f}× · IRR {d['IRR_5y_pct']:.0f}%")

write_json("18_angel_returns", payload)

# ── 图：稀释路径 + 退出 MOIC/IRR ────────────────────────────────────────────
fig, axs = plt.subplots(1, 2, figsize=(12.6, 4.8))

stages = list(fund["angel_stake_path_pct"].keys())
stake_vals = list(fund["angel_stake_path_pct"].values())
axs[0].plot(stages, stake_vals, "o-", color=BRAND["amber"], lw=2.6, markersize=9)
for i, v in enumerate(stake_vals):
    if v > 0:
        axs[0].annotate(f"{v:.1f}%", (i, v), xytext=(0, 8), textcoords="offset points", ha="center", fontsize=9, fontweight="bold", color=BRAND["ink"])
axs[0].set_ylabel("天使持股 (%)")
axs[0].set_title(f"天使股权稀释路径（20% → {angel_final_pct*100:.1f}%）", pad=8)
axs[0].set_ylim(0, max(stake_vals) * 1.25)

labels = list(exit_table.keys())
moics = [exit_table[k]["MOIC"] for k in labels]
irrs = [exit_table[k]["IRR_5y_pct"] for k in labels]
colors = [BRAND["grey"], BRAND["blue"], BRAND["teal"], BRAND["violet"]]
bars = axs[1].bar(range(len(labels)), moics, color=colors, alpha=0.9, width=0.6)
for i, (m_, r_) in enumerate(zip(moics, irrs)):
    axs[1].text(i, m_ + max(moics) * 0.02, f"{m_:.0f}×\nIRR {r_:.0f}%", ha="center", fontsize=9, fontweight="bold", color=BRAND["ink"])
axs[1].set_xticks(range(len(labels)), [l.replace(" (", "\n(") for l in labels], fontsize=8.5)
axs[1].set_ylabel("MOIC (×)")
axs[1].set_title("条件于成功退出的天使 MOIC / 5年 IRR", pad=8)
fig.suptitle("§12 天使投资人 5 年回报（条件于成功；期望值见 §11）",
             fontsize=12.5, fontweight="bold", color=BRAND["ink"], y=1.02)
fig.tight_layout()
save_chart(fig, "fig_18_angel_returns")

print("✓ 18_angel_returns 完成 → JSON + fig_18_angel_returns.png")
