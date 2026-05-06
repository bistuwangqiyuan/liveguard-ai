"""
08_funding_runway.py
====================

5 年融资节奏 + 月度现金 Runway + 三档敏感性场景。

---------------------------------------------------------------------------
ASSUMPTIONS
---------------------------------------------------------------------------

A. 融资节奏（来自 07_valuation_multimodel.json）
    Seed   2025-08   ¥0.10 亿
    Pre-A  2026-06   ¥0.50 亿
    A      2027-09   ¥2.00 亿
    B      2029-03   ¥5.00 亿
    C      2030-09   ¥8.00 亿

B. 月度运营成本（含人力、研发、市场、IT）
    Y1: ¥150 万 / 月
    Y2: ¥320 万 / 月
    Y3: ¥720 万 / 月
    Y4: ¥1,400 万 / 月
    Y5: ¥2,200 万 / 月

C. 月度毛利（来自 06 / 11）
    Y1-Y5: 累积毛利 / 12

D. 月度净现金 = 毛利 - 运营成本 + 融资到账（轮次月点）

E. 三档场景：
   - Base    : 上面所有数字
   - Bull    : 收入 +25%, 成本 -10%
   - Stress  : 收入 -25%, 成本 +15%, 融资延迟 6 个月

---------------------------------------------------------------------------
SOURCES
---------------------------------------------------------------------------
S1. 自有 06 / 07 / 11 输出
S2. 国内 SaaS 公司 IPO 招股说明书（金融壹账通 / 慧择 / 微医）
"""

from __future__ import annotations

import json
import numpy as np
import matplotlib.pyplot as plt

from _common import BRAND, PALETTE, fmt_cny, save_chart, write_json, OUT_DIR

with open(OUT_DIR / "11_revenue_buildup.json", encoding="utf-8") as f:
    rev = json.load(f)
with open(OUT_DIR / "07_valuation_multimodel.json", encoding="utf-8") as f:
    val = json.load(f)

MONTHS = 60
years = ["Y1", "Y2", "Y3", "Y4", "Y5"]

annual_revenue = np.array(rev["total_revenue"])
gm_blended = np.array(rev["blended_gross_margin"])
annual_gp = annual_revenue * gm_blended

annual_opex_base = np.array([0.18, 0.38, 0.86, 1.68, 2.64]) * 1e8
annual_opex_base = annual_opex_base * 1.0

monthly_revenue = np.zeros(MONTHS)
monthly_gp = np.zeros(MONTHS)
monthly_opex = np.zeros(MONTHS)

for y in range(5):
    a = y * 12
    progress = np.linspace(0.5, 1.5, 12)
    progress = progress / progress.mean()
    monthly_revenue[a:a+12] = annual_revenue[y] / 12 * progress
    monthly_gp[a:a+12] = annual_gp[y] / 12 * progress
    monthly_opex[a:a+12] = annual_opex_base[y] / 12

funding_events = {
    11:  50_000_000,    # Pre-A 2026-06 (M12 of Y1 ~ M11 zero-indexed)
    23:  200_000_000,   # A     2027-06 (M24 ~ M23)
    41:  500_000_000,   # B     2029-06 (M42 ~ M41)
    59:  800_000_000,   # C     2030-09 → use M60 final point
}


def simulate(scenario: str = "base"):
    rev_mult = {"base": 1.0, "bull": 1.25, "stress": 0.75}[scenario]
    cost_mult = {"base": 1.0, "bull": 0.90, "stress": 1.15}[scenario]
    funding_delay = {"base": 0, "bull": 0, "stress": 6}[scenario]

    cash = 10_000_000
    cash_path = []
    monthly_burn = []
    monthly_cash_in = []
    for m in range(MONTHS):
        rev_in = monthly_revenue[m] * rev_mult
        gp_in = monthly_gp[m] * rev_mult
        op_out = monthly_opex[m] * cost_mult
        net = gp_in - op_out
        funding = 0
        for fm, amt in funding_events.items():
            if m == fm + funding_delay:
                funding = amt
        cash += net + funding
        cash_path.append(cash)
        monthly_burn.append(net)
        monthly_cash_in.append(funding)
    return np.array(cash_path), np.array(monthly_burn), np.array(monthly_cash_in)


cash_base, burn_base, fund_base = simulate("base")
cash_bull, burn_bull, fund_bull = simulate("bull")
cash_stress, burn_stress, fund_stress = simulate("stress")

months_to_cash_pos = {}
for label, burn in [("base", burn_base), ("bull", burn_bull), ("stress", burn_stress)]:
    above = np.where(burn > 0)[0]
    months_to_cash_pos[label] = int(above[0]) + 1 if len(above) > 0 else None

result = {
    "as_of": "2026-04-30",
    "horizon_months": MONTHS,
    "scenarios": {
        "base":    {"end_cash_CNY": float(cash_base[-1]),
                    "min_cash_CNY": float(cash_base.min()),
                    "months_to_breakeven": months_to_cash_pos["base"]},
        "bull":    {"end_cash_CNY": float(cash_bull[-1]),
                    "min_cash_CNY": float(cash_bull.min()),
                    "months_to_breakeven": months_to_cash_pos["bull"]},
        "stress":  {"end_cash_CNY": float(cash_stress[-1]),
                    "min_cash_CNY": float(cash_stress.min()),
                    "months_to_breakeven": months_to_cash_pos["stress"]},
    },
    "funding_events_CNY": {str(k): v for k, v in funding_events.items()},
    "monthly_runway_path_base": cash_base.tolist(),
}

write_json("08_funding_runway", result)

print("── 5 年现金 Runway ──")
for s in ["base", "bull", "stress"]:
    info = result["scenarios"][s]
    print(f"  {s:<7s}  最低现金 {fmt_cny(info['min_cash_CNY'])}  "
          f"期末 {fmt_cny(info['end_cash_CNY'])}  "
          f"盈亏平衡月份 = M{info['months_to_breakeven']}")


fig, axs = plt.subplots(1, 2, figsize=(12.0, 4.8))

m_idx = np.arange(1, MONTHS + 1)
axs[0].plot(m_idx, cash_base / 1e8, color=BRAND["blue"], lw=2.4, label="Base")
axs[0].plot(m_idx, cash_bull / 1e8, color=BRAND["teal"], lw=2.0, ls="--", label="Bull (+25%/-10%)")
axs[0].plot(m_idx, cash_stress / 1e8, color=BRAND["red"], lw=2.0, ls=":", label="Stress (-25%/+15%/+6mo)")
axs[0].axhline(0, color=BRAND["line"], lw=0.6)
for fm, amt in funding_events.items():
    axs[0].axvline(fm + 1, color=BRAND["amber"], lw=0.7, ls="--", alpha=0.5)
    axs[0].annotate(f"+{fmt_cny(amt)}",
                    (fm + 1, cash_base[fm] / 1e8),
                    xytext=(4, 8), textcoords="offset points",
                    fontsize=8, color=BRAND["amber"])
axs[0].set_xlabel("月份 (M1-M60)")
axs[0].set_ylabel("现金余额 (¥亿)")
axs[0].set_title("月度现金 Runway · 三档场景", pad=8)
axs[0].legend(loc="upper left", fontsize=9)

burn_yr = np.array([burn_base[y*12:(y+1)*12].sum() / 1e4 for y in range(5)])
axs[1].bar(years, burn_yr, color=[BRAND["red"] if v < 0 else BRAND["teal"] for v in burn_yr],
           width=0.55)
axs[1].axhline(0, color=BRAND["line"], lw=0.6)
axs[1].set_ylabel("年度净现金流（毛利 − 运营成本，万元）")
axs[1].set_title("年度净现金流（不含融资到账）", pad=8)
for i, v in enumerate(burn_yr):
    axs[1].text(i, v + (200 if v > 0 else -700), f"¥{v:.0f}万",
                ha="center", fontsize=10, color=BRAND["ink"])

fig.suptitle("§8.5 InvestMind 5 年融资节奏与现金 Runway",
             fontsize=13, fontweight="bold", y=1.02, color=BRAND["ink"])
fig.tight_layout()
save_chart(fig, "fig_08_runway")

print("✓ 08_funding_runway 完成")
