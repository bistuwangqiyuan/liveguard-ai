"""
18_angel_returns.py  ·  v5.0（本轮 Seed 投资人·条件于成功退出）
==============================================================

本轮（Seed）投资人回报——【条件于公司成功走到退出】的情景表。对应 BP §12。

读取：
  * 11_fundraising_dilution.json → Seed 全稀释最终股比（Seed→A→B→C）
  * 14_monte_carlo_valuation.json → 加权综合 EV 与 MC 分位

口径：Seed ¥2,000 万 @ Post ¥1.0 亿（入场 20%），全稀释后 C 轮约 11%。
  * 退出锚点用 2026 压缩倍数（加权 EV），显著低于历史泡沫水平。
  * MOIC = 退出回报 / 投入；IRR = MOIC^(1/持有年限) − 1（持有 6 年）。

注：本表均为【条件于成功退出】；纳入失败概率后的多口径期望/中位/全损概率见 §12（19 模型）。
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

lead_invest = DS.LEAD_INVEST_CNY
lead_post = DS.ROUNDS[DS.LEAD_ROUND]["post_money"]
lead_entry_pct = lead_invest / lead_post
lead_final_pct = fund["lead_final_stake_pct"] / 100.0
hold = DS.HOLD_YEARS

weighted_ev = val["weighted_EV_yi"] * 1e8
mc = val["mc_quantiles_yi"]
c_post = DS.ROUNDS["C"]["post_money"]


def moic_irr(exit_ev, stake, invest, years):
    payout = exit_ev * stake
    moic = payout / invest
    irr = moic ** (1 / years) - 1
    return payout, moic, irr


# 纸面 mark（按 C 轮 Post-money 计，未退出的账面 mark）
paper_payout, paper_moic, paper_irr = moic_irr(c_post, lead_final_pct, lead_invest, hold)

# 四档"条件于成功退出"情景（2026 压缩倍数锚定）
scenarios = {
    "保守 (战略并购, MC P25)":  mc["P25"] * 1e8,
    "中性 (加权综合 EV)":        weighted_ev,
    "乐观 (IPO, MC P75)":        mc["P75"] * 1e8,
    "极乐观 (头部 IPO, MC P90)": mc["P90"] * 1e8,
}
exit_table = {}
for label, ev in scenarios.items():
    payout, moic, irr = moic_irr(ev, lead_final_pct, lead_invest, hold)
    exit_table[label] = {
        "exit_EV_yi": round(ev / 1e8, 1),
        "lead_payout_yi": round(payout / 1e8, 2),
        "MOIC": round(moic, 1),
        "IRR_pct": round(irr * 100, 0),
    }

payload = {
    "as_of": DS.AS_OF, "currency": "CNY", "version": DS.VERSION,
    "lead_round": DS.LEAD_ROUND,
    "lead_invest_CNY": lead_invest, "lead_invest_disp": fmt_cny(lead_invest),
    "lead_post_money_CNY": lead_post, "lead_post_money_disp": fmt_cny(lead_post),
    "lead_entry_stake_pct": round(lead_entry_pct * 100, 1),
    "lead_final_stake_pct": round(lead_final_pct * 100, 2),
    "dilution_path_pct": fund["lead_stake_path_pct"],
    "hold_years": hold,
    "paper_mark_at_C": {
        "basis": "C 轮 Post-money", "EV_yi": round(c_post / 1e8, 1),
        "lead_value_yi": round(paper_payout / 1e8, 2),
        "MOIC": round(paper_moic, 1), "IRR_pct": round(paper_irr * 100, 0),
    },
    "exit_scenarios_conditional": exit_table,
    "note": "四档为条件于成功退出；概率加权期望/中位/全损概率见 19_success_probability（§12）。",
    "sources": ["11_fundraising_dilution (全稀释)", "14_monte_carlo_valuation (加权 EV / MC 分位)"],
}

print("── 本轮 Seed 投资人回报（条件于成功退出）──")
print(f"  入场: {fmt_cny(lead_invest)} @ Post {fmt_cny(lead_post)} = {lead_entry_pct*100:.0f}%  → 全稀释后 {lead_final_pct*100:.2f}%")
print(f"  {hold} 年纸面 mark（C 轮 Post {fmt_cny(c_post)}）: {fmt_cny(paper_payout)} · MOIC {paper_moic:.1f}× · IRR {paper_irr*100:.0f}%")
for label, d in exit_table.items():
    print(f"  {label:<24s} EV ¥{d['exit_EV_yi']:.0f}亿 → 回报 ¥{d['lead_payout_yi']:.1f}亿 · MOIC {d['MOIC']:.1f}× · IRR {d['IRR_pct']:.0f}%")

write_json("18_angel_returns", payload)

# ── 图：稀释路径 + 退出 MOIC/IRR ────────────────────────────────────────────
fig, axs = plt.subplots(1, 2, figsize=(12.6, 4.8))

stages = list(fund["lead_stake_path_pct"].keys())
stake_vals = list(fund["lead_stake_path_pct"].values())
axs[0].plot(stages, stake_vals, "o-", color=BRAND["amber"], lw=2.6, markersize=9)
for i, v in enumerate(stake_vals):
    if v > 0:
        axs[0].annotate(f"{v:.1f}%", (i, v), xytext=(0, 8), textcoords="offset points", ha="center", fontsize=9, fontweight="bold", color=BRAND["ink"])
axs[0].set_ylabel("Seed 持股 (%)")
axs[0].set_title(f"Seed 股权稀释路径（{lead_entry_pct*100:.0f}% → {lead_final_pct*100:.1f}%）", pad=8)
axs[0].set_ylim(0, max(stake_vals) * 1.25)

labels = list(exit_table.keys())
moics = [exit_table[k]["MOIC"] for k in labels]
irrs = [exit_table[k]["IRR_pct"] for k in labels]
colors = [BRAND["grey"], BRAND["blue"], BRAND["teal"], BRAND["violet"]]
axs[1].bar(range(len(labels)), moics, color=colors, alpha=0.9, width=0.6)
for i, (m_, r_) in enumerate(zip(moics, irrs)):
    axs[1].text(i, m_ + max(moics) * 0.02, f"{m_:.0f}×\nIRR {r_:.0f}%", ha="center", fontsize=9, fontweight="bold", color=BRAND["ink"])
axs[1].set_xticks(range(len(labels)), [l.replace(" (", "\n(") for l in labels], fontsize=8.5)
axs[1].set_ylabel("MOIC (×)")
axs[1].set_title("条件于成功退出的 Seed MOIC / IRR", pad=8)
fig.suptitle("§12 本轮 Seed 投资人回报（条件于成功；多口径期望见 19 模型）",
             fontsize=12.5, fontweight="bold", color=BRAND["ink"], y=1.02)
fig.tight_layout()
save_chart(fig, "fig_18_angel_returns")

print("✓ 18_angel_returns 完成 → JSON + fig_18_angel_returns.png")
