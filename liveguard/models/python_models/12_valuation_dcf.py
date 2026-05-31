"""
12_valuation_dcf.py
===================

两阶段 DCF 估值 + Gordon 永续对照。对应 BP §9.4.1。
读取 10_financial_projections.json 的显性期 FCF。

* 显性期 Y1–Y5：直接取模型 FCF（= CFO + CFI）
* 过渡期 Y6–Y10：收入按 TRANSITION_GROWTH 递减增长；FCF = 收入 × 营业利润率 × (1−税率)
* 终值（Y10）：退出 EV/EBITDA = 18×（EBITDA = 收入 ×(营业利润率+6% 折旧率)）
* WACC = 14%
* Gordon 对照：终值 = FCF_Y10×(1+g)/(WACC−g)
"""

from __future__ import annotations

import json
import numpy as np
import matplotlib.pyplot as plt

from _common import BRAND, PALETTE, fmt_cny, save_chart, write_json, OUT_DIR
import data_sources as DS

with open(OUT_DIR / "10_financial_projections.json", encoding="utf-8") as f:
    fin = json.load(f)

WACC = DS.WACC
G = DS.TERMINAL_G
EXIT = DS.EXIT_EV_EBITDA
TAX = DS.TAX_RATE

fcf_explicit = np.array(fin["fcf_CNY"])          # Y1-Y5
rev_y5 = fin["revenue_CNY"][-1]

# 过渡期 Y6-Y10
rev = rev_y5
trans_rev, trans_fcf, trans_ebitda = [], [], []
for t in range(5):
    rev = rev * (1 + DS.TRANSITION_GROWTH[t])
    om = DS.TRANSITION_OPMARGIN[t]
    fcf = rev * om * (1 - TAX)
    ebitda = rev * (om + 0.06)
    trans_rev.append(rev)
    trans_fcf.append(fcf)
    trans_ebitda.append(ebitda)

# 折现
pv_explicit = sum(fcf_explicit[t] / (1 + WACC) ** (t + 1) for t in range(5))
pv_transition = sum(trans_fcf[t] / (1 + WACC) ** (6 + t) for t in range(5))

terminal_ebitda = trans_ebitda[-1]
tv_exit = EXIT * terminal_ebitda
pv_terminal_exit = tv_exit / (1 + WACC) ** 10
ev_two_stage = pv_explicit + pv_transition + pv_terminal_exit

# Gordon 对照
tv_gordon = trans_fcf[-1] * (1 + G) / (WACC - G)
pv_terminal_gordon = tv_gordon / (1 + WACC) ** 10
ev_gordon = pv_explicit + pv_transition + pv_terminal_gordon

payload = {
    "as_of": DS.AS_OF, "currency": "CNY",
    "wacc": WACC, "terminal_g": G, "exit_ev_ebitda": EXIT,
    "pv_explicit_CNY": round(pv_explicit, 0), "pv_explicit_yi": round(pv_explicit / 1e8, 1),
    "pv_transition_CNY": round(pv_transition, 0), "pv_transition_yi": round(pv_transition / 1e8, 1),
    "terminal_ebitda_y10_yi": round(terminal_ebitda / 1e8, 1),
    "pv_terminal_exit_yi": round(pv_terminal_exit / 1e8, 1),
    "EV_two_stage_CNY": round(ev_two_stage, 0), "EV_two_stage_yi": round(ev_two_stage / 1e8, 1),
    "EV_gordon_CNY": round(ev_gordon, 0), "EV_gordon_yi": round(ev_gordon / 1e8, 1),
    "transition_revenue_yi": [round(x / 1e8, 1) for x in trans_rev],
    "transition_fcf_yi": [round(x / 1e8, 1) for x in trans_fcf],
    "sources": ["两阶段 DCF + 退出倍数法", "Salesforce/Datadog 历史 EV/EBITDA 中位"],
}

print("── 两阶段 DCF 估值 ──")
print(f"  PV(显性 Y1-Y5)  = {fmt_cny(pv_explicit)}")
print(f"  PV(过渡 Y6-Y10) = {fmt_cny(pv_transition)}")
print(f"  PV(终值 @18×)   = {fmt_cny(pv_terminal_exit)}")
print(f"  EV(两阶段)      = {fmt_cny(ev_two_stage)}")
print(f"  EV(Gordon g=3%) = {fmt_cny(ev_gordon)}")

write_json("12_valuation_dcf", payload)

# ── 图：DCF 价值桥 + FCF 曲线 ──────────────────────────────────────────────
fig, axs = plt.subplots(1, 2, figsize=(12.2, 4.6))
labels = ["PV显性\nY1-Y5", "PV过渡\nY6-Y10", "PV终值\n@18×", "EV合计"]
vals = [pv_explicit / 1e8, pv_transition / 1e8, pv_terminal_exit / 1e8, ev_two_stage / 1e8]
cum = 0
for i in range(3):
    axs[0].bar(i, vals[i], bottom=cum if vals[i] > 0 else cum + vals[i], color=PALETTE[i], alpha=0.9, width=0.6)
    axs[0].text(i, cum + vals[i] / 2, f"¥{vals[i]:.0f}亿", ha="center", fontsize=9, color=BRAND["ink"])
    cum += vals[i]
axs[0].bar(3, vals[3], color=BRAND["blue"], alpha=0.95, width=0.6)
axs[0].text(3, vals[3] + 3, f"¥{vals[3]:.0f}亿", ha="center", fontsize=10, fontweight="bold", color=BRAND["ink"])
axs[0].set_xticks(range(4), labels, fontsize=9)
axs[0].set_ylabel("¥ 亿")
axs[0].set_title("两阶段 DCF 价值桥", pad=8)

all_years = [f"Y{i}" for i in range(1, 11)]
all_fcf = [x / 1e8 for x in fcf_explicit] + [x / 1e8 for x in trans_fcf]
axs[1].bar(all_years, all_fcf, color=[BRAND["red"] if v < 0 else BRAND["teal"] for v in all_fcf], alpha=0.85, width=0.6)
axs[1].axhline(0, color=BRAND["grey"], lw=1)
axs[1].set_ylabel("FCF (¥ 亿)")
axs[1].set_title("10 年自由现金流（显性 + 过渡）", pad=8)
fig.suptitle(f"§9.4.1 两阶段 DCF：EV ≈ ¥{ev_two_stage/1e8:.0f}亿（Gordon 对照 ¥{ev_gordon/1e8:.0f}亿）",
             fontsize=12.5, fontweight="bold", color=BRAND["ink"], y=1.02)
fig.tight_layout()
save_chart(fig, "fig_12_valuation_dcf")

print("✓ 12_valuation_dcf 完成 → JSON + fig_12_valuation_dcf.png")
