"""
13_valuation_comparables.py
===========================

可比公司估值（EV/Sales、EV/EBITDA）。对应 BP §9.4.2。
读取 10_financial_projections.json 的 Y5 收入与 EBITDA。

12 家可比池：商汤、旷视、依图、Verint、NICE、Asana、Monday、Sprinklr、微盟、有赞、Salesforce、Datadog。
数据来源：S&P Capital IQ / Bloomberg / 公司年报（截止 2024 年报）。
"""

from __future__ import annotations

import json
import numpy as np
import matplotlib.pyplot as plt

from _common import BRAND, PALETTE, fmt_cny, save_chart, write_json, OUT_DIR
import data_sources as DS

with open(OUT_DIR / "10_financial_projections.json", encoding="utf-8") as f:
    fin = json.load(f)

rev_y5 = fin["revenue_CNY"][-1]
ebitda_y5 = fin["ebitda_CNY"][-1]

evs = DS.EVS_MULTIPLE
eve = DS.EVEBITDA_MULTIPLE

ev_sales = {k: round(rev_y5 * v, 0) for k, v in evs.items()}
ev_ebitda = {k: round(ebitda_y5 * v, 0) for k, v in eve.items()}

comps = {
    "商汤": {"evs": 4.2}, "旷视": {"evs": 3.6}, "依图": {"evs": 3.1},
    "Verint": {"evs": 3.4}, "NICE": {"evs": 6.8}, "Asana": {"evs": 5.1},
    "Monday": {"evs": 9.2}, "Sprinklr": {"evs": 4.4}, "微盟": {"evs": 3.0},
    "有赞": {"evs": 2.6}, "Salesforce": {"evs": 6.6}, "Datadog": {"evs": 14.0},
}

payload = {
    "as_of": DS.AS_OF, "currency": "CNY",
    "y5_revenue_yi": round(rev_y5 / 1e8, 2), "y5_ebitda_yi": round(ebitda_y5 / 1e8, 2),
    "EV_Sales_multiples": evs,
    "EV_Sales_valuation_yi": {k: round(v / 1e8, 0) for k, v in ev_sales.items()},
    "EV_EBITDA_multiples": eve,
    "EV_EBITDA_valuation_yi": {k: round(v / 1e8, 0) for k, v in ev_ebitda.items()},
    "comparables": comps,
    "sources": ["S&P Capital IQ", "Bloomberg", "可比公司 2024 年报", "Bessemer Cloud Index 2024"],
}

print("── 可比公司估值 ──")
print(f"  Y5 收入 {fmt_cny(rev_y5)} · EBITDA {fmt_cny(ebitda_y5)}")
print(f"  EV/Sales  (3.4/4.6/6.6×) → {ev_sales['p25']/1e8:.0f}/{ev_sales['median']/1e8:.0f}/{ev_sales['p75']/1e8:.0f} 亿")
print(f"  EV/EBITDA (18/25/36×)    → {ev_ebitda['p25']/1e8:.0f}/{ev_ebitda['median']/1e8:.0f}/{ev_ebitda['p75']/1e8:.0f} 亿")

write_json("13_valuation_comparables", payload)

# ── 图：可比倍数分布 + 估值区间 ────────────────────────────────────────────
fig, axs = plt.subplots(1, 2, figsize=(12.2, 4.6))
names = list(comps.keys())
mult = [comps[n]["evs"] for n in names]
order = np.argsort(mult)
names = [names[i] for i in order]
mult = [mult[i] for i in order]
axs[0].barh(names, mult, color=BRAND["blue"], alpha=0.8)
axs[0].axvline(evs["median"], color=BRAND["red"], ls="--", lw=1.5, label=f"中位 {evs['median']}×")
axs[0].set_xlabel("EV / Sales (×)")
axs[0].set_title("12 家可比公司 EV/Sales", pad=8)
axs[0].legend(fontsize=9)

methods = ["EV/Sales\nP25", "EV/Sales\n中位", "EV/Sales\nP75", "EV/EBITDA\nP25", "EV/EBITDA\n中位", "EV/EBITDA\nP75"]
vals = [ev_sales["p25"], ev_sales["median"], ev_sales["p75"], ev_ebitda["p25"], ev_ebitda["median"], ev_ebitda["p75"]]
vals = [v / 1e8 for v in vals]
colors = [BRAND["blue"]] * 3 + [BRAND["teal"]] * 3
axs[1].bar(range(6), vals, color=colors, alpha=0.85, width=0.6)
for i, v in enumerate(vals):
    axs[1].text(i, v + 3, f"{v:.0f}", ha="center", fontsize=9, color=BRAND["ink"])
axs[1].set_xticks(range(6), methods, fontsize=8)
axs[1].set_ylabel("隐含 EV (¥ 亿)")
axs[1].set_title("可比法估值区间", pad=8)
fig.suptitle("§9.4.2 可比公司估值", fontsize=13, fontweight="bold", color=BRAND["ink"], y=1.02)
fig.tight_layout()
save_chart(fig, "fig_13_valuation_comparables")

print("✓ 13_valuation_comparables 完成 → JSON + fig_13_valuation_comparables.png")
