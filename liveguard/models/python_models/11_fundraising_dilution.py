"""
11_fundraising_dilution.py
==========================

5 轮融资 Cap Table 演进 + 稀释 + 投资人 IRR/MOIC。对应 BP §9.1 / §9.2 / §9.5。

每轮：new_investor% = amount / post_money；先按新钱稀释全部存量，再做 ESOP 增补
（topup 同比稀释全体）。创始团队 C 轮后保留 ~33%。
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from _common import BRAND, PALETTE, fmt_cny, save_chart, write_json
import data_sources as DS

ROUND_ORDER = ["Seed", "Pre-A", "A", "B", "C"]
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
        "new_investor_pct": round(r["amount"] / r["post_money"] * 100, 1),
    })

final = cap_history["C"]
holders = ["Founders", "ESOP", "Seed", "Pre-A", "A", "B", "C"]

# A 轮投资人 IRR / MOIC（A 轮 1.0 亿 @ Pre 5.0 亿；C 轮后稀释至 ~12%）
a_share_final = final.get("A", 0)
a_invest = DS.ROUNDS["A"]["amount"]
exit_scenarios = {}
for label, exit_ev in [("保守(M&A)", 100e8), ("中性", 180e8), ("乐观(IPO)", 300e8), ("极乐观", 500e8)]:
    payout = exit_ev * a_share_final
    moic = payout / a_invest
    irr = moic ** (1 / 5) - 1
    exit_scenarios[label] = {"exit_EV_yi": round(exit_ev / 1e8, 0), "payout_yi": round(payout / 1e8, 1),
                             "MOIC": round(moic, 1), "IRR_5y_pct": round(irr * 100, 0)}

payload = {
    "as_of": DS.AS_OF, "currency": "CNY",
    "rounds": rounds_summary,
    "total_raised_CNY": total_raised, "total_raised_disp": fmt_cny(total_raised),
    "cap_table_pct": {stage: {h: round(cap_history[stage].get(h, 0) * 100, 1) for h in holders}
                      for stage in cap_history},
    "founders_after_C_pct": round(final["Founders"] * 100, 1),
    "esop_after_C_pct": round(final.get("ESOP", 0) * 100, 1),
    "institutions_after_C_pct": round(sum(final.get(r, 0) for r in ROUND_ORDER) * 100, 1),
    "A_round_investor": {"final_stake_pct": round(a_share_final * 100, 1), "exit_scenarios": exit_scenarios},
    "sources": ["公司融资规划", "标准优先股 + ESOP 增补稀释模型"],
}

print("── Cap Table 演进（%）──")
print("  阶段      " + "  ".join(f"{h:>8s}" for h in holders))
for stage in cap_history:
    print(f"  {stage:<8s}  " + "  ".join(f"{cap_history[stage].get(h,0)*100:>7.1f}%" for h in holders))
print(f"  累计融资 {fmt_cny(total_raised)} · 创始团队 C 轮后 {final['Founders']*100:.1f}%")

write_json("11_fundraising_dilution", payload)

# ── 图：Cap Table 堆叠 + 融资轨迹 ──────────────────────────────────────────
fig, axs = plt.subplots(1, 2, figsize=(12.4, 4.8))
stages = list(cap_history.keys())
colors = {"Founders": BRAND["blue"], "ESOP": BRAND["teal"], "Seed": BRAND["amber"],
          "Pre-A": BRAND["violet"], "A": BRAND["red"], "B": BRAND["grey"], "C": "#3CC8FF"}
bottom = np.zeros(len(stages))
for h in holders:
    vals = np.array([cap_history[s].get(h, 0) * 100 for s in stages])
    axs[0].bar(stages, vals, bottom=bottom, color=colors[h], label=h, width=0.7)
    bottom += vals
axs[0].set_ylabel("股权占比 (%)")
axs[0].set_title("Cap Table 演进（创始团队 C 轮后 {:.0f}%）".format(final["Founders"] * 100), pad=8)
axs[0].legend(fontsize=8, ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.12))
axs[0].set_ylim(0, 100)

names = ROUND_ORDER
posts = [DS.ROUNDS[r]["post_money"] / 1e8 for r in names]
axs[1].plot(names, posts, "o-", color=BRAND["blue"], lw=2.4, markersize=10)
for i, v in enumerate(posts):
    axs[1].annotate(f"¥{v:.2f}亿", (i, v), xytext=(6, 6), textcoords="offset points", fontsize=9, fontweight="bold", color=BRAND["ink"])
axs[1].set_yscale("log")
axs[1].set_ylabel("Post-money 估值 (¥ 亿 · log)")
axs[1].set_title("融资轨迹 Seed→C（Post-money）", pad=8)
fig.suptitle("§9.1-9.2 融资节奏与股权结构", fontsize=13, fontweight="bold", color=BRAND["ink"], y=1.02)
fig.tight_layout()
save_chart(fig, "fig_11_cap_table")

print("✓ 11_fundraising_dilution 完成 → JSON + fig_11_cap_table.png")
