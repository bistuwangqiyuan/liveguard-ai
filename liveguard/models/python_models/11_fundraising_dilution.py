"""
11_fundraising_dilution.py
==========================

Pre-Angel + 5 轮融资 Cap Table 演进 + 稀释 + 投资人 IRR/MOIC。对应 BP §9.1 / §12。

顺序：创立 → PreAngel（王启源 500 万）→ Angel → Seed → A → B → C
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from _common import BRAND, PALETTE, fmt_cny, save_chart, write_json
import data_sources as DS

ROUND_ORDER = DS.ROUND_ORDER
pct = {"Founders": 1.0}
cap_history = {"创立": dict(pct)}

# Pre-Angel：王启源自投
pa = DS.PRE_ANGEL
new_pa = pa["amount"] / pa["post_money"]
for k in pct:
    pct[k] *= (1 - new_pa)
pct["PreAngel"] = new_pa
cap_history["PreAngel"] = dict(pct)

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
rounds_summary = [{
    "round": "PreAngel",
    "timing": pa["date"],
    "investor": pa["investor"],
    "amount_CNY": pa["amount"],
    "amount_disp": fmt_cny(pa["amount"]),
    "pre_money_CNY": pa["post_money"] - pa["amount"],
    "post_money_CNY": pa["post_money"],
    "post_money_disp": fmt_cny(pa["post_money"]),
    "new_investor_pct": round(new_pa * 100, 1),
}]
total_raised = pa["amount"]
for rname in ROUND_ORDER:
    r = DS.ROUNDS[rname]
    total_raised += r["amount"]
    rounds_summary.append({
        "round": rname, "timing": r["date"],
        "amount_CNY": r["amount"], "amount_disp": fmt_cny(r["amount"]),
        "pre_money_CNY": r["post_money"] - r["amount"],
        "post_money_CNY": r["post_money"], "post_money_disp": fmt_cny(r["post_money"]),
        "new_investor_pct": round(r["amount"] / r["post_money"] * 100, 1),
    })

final = cap_history["C"]
holders = ["Founders", "PreAngel", "ESOP", "Angel", "Seed", "A", "B", "C"]

final_stakes = {r: final.get(r, 0) for r in ROUND_ORDER}
angel_stake_path = {stage: cap_history[stage].get("Angel", 0) for stage in cap_history}
# 王启源合计经济股比（Founders + PreAngel，单人创始团队）
wang_combined_path = {
    stage: cap_history[stage].get("Founders", 0) + cap_history[stage].get("PreAngel", 0)
    for stage in cap_history
}
founders_stake_path = {stage: cap_history[stage].get("Founders", 0) for stage in cap_history}

payload = {
    "as_of": DS.AS_OF, "currency": "CNY", "version": DS.VERSION,
    "pre_angel_round": {
        "investor": pa["investor"],
        "amount_CNY": pa["amount"],
        "post_money_CNY": pa["post_money"],
        "wang_pre_angel_stake_pct": round(final.get("PreAngel", 0) * 100, 2),
    },
    "rounds": rounds_summary,
    "total_raised_CNY": total_raised, "total_raised_disp": fmt_cny(total_raised),
    "cap_table_pct": {
        stage: {h: round(cap_history[stage].get(h, 0) * 100, 1) for h in holders}
        for stage in cap_history
    },
    "founders_after_C_pct": round(final["Founders"] * 100, 1),
    "wang_combined_after_C_pct": round(wang_combined_path["C"] * 100, 2),
    "esop_after_C_pct": round(final.get("ESOP", 0) * 100, 1),
    "institutions_after_C_pct": round(sum(final.get(r, 0) for r in ROUND_ORDER) * 100, 1),
    "final_stakes_pct": {r: round(final_stakes[r] * 100, 2) for r in ROUND_ORDER},
    "angel_final_stake_pct": round(final_stakes["Angel"] * 100, 2),
    "angel_stake_path_pct": {k: round(v * 100, 2) for k, v in angel_stake_path.items()},
    "founders_stake_path_pct": {k: round(v * 100, 2) for k, v in founders_stake_path.items()},
    "wang_combined_stake_path_pct": {k: round(v * 100, 2) for k, v in wang_combined_path.items()},
    "angel_invest_CNY": DS.ANGEL_INVEST_CNY,
    "sources": ["公司融资规划", "Pre-Angel + 标准优先股 + ESOP 增补稀释模型"],
}

print("── Cap Table 演进（%）──")
print("  阶段      " + "  ".join(f"{h:>8s}" for h in holders))
for stage in cap_history:
    print(f"  {stage:<8s}  " + "  ".join(f"{cap_history[stage].get(h,0)*100:>7.1f}%" for h in holders))
print(f"  累计融资 {fmt_cny(total_raised)} · 创始 Founders C 轮后 {final['Founders']*100:.1f}%")
print(f"  王启源合计（Founders+PreAngel）C 轮后 {wang_combined_path['C']*100:.1f}% · 天使 {final_stakes['Angel']*100:.2f}%")

write_json("11_fundraising_dilution", payload)

fig, axs = plt.subplots(1, 2, figsize=(12.4, 4.8))
stages = list(cap_history.keys())
colors = {
    "Founders": BRAND["blue"], "PreAngel": "#5B8DEF", "ESOP": BRAND["teal"],
    "Angel": BRAND["amber"], "Seed": BRAND["violet"], "A": BRAND["red"],
    "B": BRAND["grey"], "C": "#3CC8FF",
}
bottom = np.zeros(len(stages))
for h in holders:
    vals = np.array([cap_history[s].get(h, 0) * 100 for s in stages])
    axs[0].bar(stages, vals, bottom=bottom, color=colors[h], label=h, width=0.7)
    bottom += vals
axs[0].set_ylabel("股权占比 (%)")
axs[0].set_title(
    "Cap Table 演进（王启源合计 {:.0f}% · Founders {:.0f}%）".format(
        wang_combined_path["C"] * 100, final["Founders"] * 100
    ),
    pad=8,
)
axs[0].legend(fontsize=7, ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.14))
axs[0].set_ylim(0, 100)

names = ["PreAngel"] + ROUND_ORDER
posts = [pa["post_money"] / 1e8] + [DS.ROUNDS[r]["post_money"] / 1e8 for r in ROUND_ORDER]
axs[1].plot(names, posts, "o-", color=BRAND["blue"], lw=2.4, markersize=10)
for i, v in enumerate(posts):
    axs[1].annotate(f"¥{v:.2f}亿", (i, v), xytext=(6, 6), textcoords="offset points", fontsize=9, fontweight="bold", color=BRAND["ink"])
axs[1].set_yscale("log")
axs[1].set_ylabel("Post-money 估值 (¥ 亿 · log)")
axs[1].set_title("融资轨迹 PreAngel→C（Post-money）", pad=8)
fig.suptitle("§12 融资节奏与股权结构（v4.0 Pre-Angel）", fontsize=13, fontweight="bold", color=BRAND["ink"], y=1.02)
fig.tight_layout()
save_chart(fig, "fig_11_cap_table")

print("✓ 11_fundraising_dilution 完成 → JSON + fig_11_cap_table.png")
