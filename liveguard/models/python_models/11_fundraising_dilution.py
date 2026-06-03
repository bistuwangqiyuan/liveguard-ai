"""
11_fundraising_dilution.py  ·  v5.0
===================================

标准机构融资 Cap Table 演进 + 稀释 + lead 投资人股比路径。对应 BP §10。

顺序：创立 → Seed（本轮）→ A → B → C
本轮 lead 投资人 = Seed；其全稀释后股比路径供 §12 回报模型使用。
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from _common import BRAND, PALETTE, fmt_cny, save_chart, write_json
import data_sources as DS

ROUND_ORDER = DS.ROUND_ORDER
LEAD = DS.LEAD_ROUND
pct = {"Founders": 1.0}
cap_history = {"创立": dict(pct)}

for rname in ROUND_ORDER:
    rinfo = DS.ROUNDS[rname]
    new = rinfo["amount"] / rinfo["post_money"]
    for k in pct:
        pct[k] *= (1 - new)
    pct[rname] = new
    topup = rinfo["esop_topup"]
    if topup > 0:
        for k in pct:
            pct[k] *= (1 - topup)
        pct["ESOP"] = pct.get("ESOP", 0.0) + topup
    cap_history[rname] = dict(pct)

# 轮次摘要
rounds_summary = []
total_raised = 0
for rname in ROUND_ORDER:
    r = DS.ROUNDS[rname]
    total_raised += r["amount"]
    rounds_summary.append({
        "round": rname, "timing": r["date"],
        "amount_CNY": r["amount"], "amount_disp": fmt_cny(r["amount"]),
        "pre_money_CNY": r["post_money"] - r["amount"],
        "post_money_CNY": r["post_money"], "post_money_disp": fmt_cny(r["post_money"]),
        "esop_topup_pct": round(r["esop_topup"] * 100, 1),
        "new_investor_pct": round(r["amount"] / r["post_money"] * 100, 1),
    })

final = cap_history["C"]
holders = ["Founders", "ESOP"] + ROUND_ORDER

final_stakes = {r: final.get(r, 0) for r in ROUND_ORDER}
lead_stake_path = {stage: cap_history[stage].get(LEAD, 0) for stage in cap_history}
founders_stake_path = {stage: cap_history[stage].get("Founders", 0) for stage in cap_history}

payload = {
    "as_of": DS.AS_OF, "currency": "CNY", "version": DS.VERSION,
    "lead_round": LEAD,
    "rounds": rounds_summary,
    "total_raised_CNY": total_raised, "total_raised_disp": fmt_cny(total_raised),
    "cap_table_pct": {
        stage: {h: round(cap_history[stage].get(h, 0) * 100, 1) for h in holders}
        for stage in cap_history
    },
    "founders_after_C_pct": round(final["Founders"] * 100, 1),
    "esop_after_C_pct": round(final.get("ESOP", 0) * 100, 1),
    "institutions_after_C_pct": round(sum(final.get(r, 0) for r in ROUND_ORDER) * 100, 1),
    "final_stakes_pct": {r: round(final_stakes[r] * 100, 2) for r in ROUND_ORDER},
    "lead_entry_pct": round(lead_stake_path[LEAD] * 100, 2),
    "lead_final_stake_pct": round(final_stakes[LEAD] * 100, 2),
    "lead_stake_path_pct": {k: round(v * 100, 2) for k, v in lead_stake_path.items()},
    "founders_stake_path_pct": {k: round(v * 100, 2) for k, v in founders_stake_path.items()},
    "lead_invest_CNY": DS.LEAD_INVEST_CNY,
    "sources": ["公司融资规划", "标准优先股 + ESOP 增补稀释模型"],
}

print("── Cap Table 演进（%）──")
print("  阶段      " + "  ".join(f"{h:>8s}" for h in holders))
for stage in cap_history:
    print(f"  {stage:<8s}  " + "  ".join(f"{cap_history[stage].get(h,0)*100:>7.1f}%" for h in holders))
print(f"  累计融资 {fmt_cny(total_raised)} · 创始 Founders C 轮后 {final['Founders']*100:.1f}%")
print(f"  本轮 {LEAD} 入场 {lead_stake_path[LEAD]*100:.1f}% → C 轮后全稀释 {final_stakes[LEAD]*100:.2f}%")

write_json("11_fundraising_dilution", payload)

fig, axs = plt.subplots(1, 2, figsize=(12.4, 4.8))
stages = list(cap_history.keys())
colors = {
    "Founders": BRAND["blue"], "ESOP": BRAND["teal"],
    "Seed": BRAND["amber"], "A": BRAND["violet"], "B": BRAND["red"], "C": "#3CC8FF",
}
bottom = np.zeros(len(stages))
for h in holders:
    vals = np.array([cap_history[s].get(h, 0) * 100 for s in stages])
    axs[0].bar(stages, vals, bottom=bottom, color=colors.get(h, BRAND["grey"]), label=h, width=0.7)
    bottom += vals
axs[0].set_ylabel("股权占比 (%)")
axs[0].set_title(
    "Cap Table 演进（Founders C 轮后 {:.0f}% · ESOP {:.0f}%）".format(
        final["Founders"] * 100, final.get("ESOP", 0) * 100
    ),
    pad=8,
)
axs[0].legend(fontsize=8, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.14))
axs[0].set_ylim(0, 100)

names = ROUND_ORDER
posts = [DS.ROUNDS[r]["post_money"] / 1e8 for r in ROUND_ORDER]
axs[1].plot(names, posts, "o-", color=BRAND["blue"], lw=2.4, markersize=10)
for i, v in enumerate(posts):
    axs[1].annotate(f"¥{v:.2f}亿", (i, v), xytext=(6, 6), textcoords="offset points", fontsize=9, fontweight="bold", color=BRAND["ink"])
axs[1].set_yscale("log")
axs[1].set_ylabel("Post-money 估值 (¥ 亿 · log)")
axs[1].set_title("融资轨迹 Seed→C（Post-money）", pad=8)
fig.suptitle("§10 融资节奏与股权结构（标准机构 Seed→C）", fontsize=13, fontweight="bold", color=BRAND["ink"], y=1.02)
fig.tight_layout()
save_chart(fig, "fig_11_cap_table")

print("✓ 11_fundraising_dilution 完成 → JSON + fig_11_cap_table.png")
