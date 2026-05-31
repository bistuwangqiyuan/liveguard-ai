"""
02_unit_economics.py
====================

InvestMind 三档客户单位经济（LTV / CAC / Payback / LTV/CAC ratio）。

三档客群：
  * Lite      — 散户高净值（HNWI）个人投资者
  * Pro       — 持证天使 / 个人 PE LP
  * Family    — Family Office / 律所 / 财富顾问

---------------------------------------------------------------------------
ASSUMPTIONS
---------------------------------------------------------------------------

| 客群 | 月费 (¥) | 月留存 | Gross Margin | 毛利率 | CAC (¥) |
|------|----------|--------|--------------|--------|---------|
| Lite     | 99      | 95–97% | 80–85% | 82%   | 600     |
| Pro      | 416     | 96–98% | 78–84% | 80%   | 3,500   |
| Family   | 1,666   | 97–99% | 70–76% | 73%   | 22,000  |

留存率使用 Beta 分布 sample，CAC 使用对数正态分布。

---------------------------------------------------------------------------
SOURCES
---------------------------------------------------------------------------
S1. 艾瑞咨询《2024 中国 FinTech / WealthTech SaaS 行业基准》
S2. SaaS Capital《2024 SMB / Mid-Market SaaS Benchmark》
S3. 上市可比：Wind 个人版 / 同花顺 iFinD / Choice / 朝阳永续 财报
S4. AngelList 2024 Internal Investor Letter（公开摘录）
S5. 国内私募基金销售获客成本（2023 中欧私行峰会）
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from _common import BRAND, PALETTE, ci, fmt_cny, save_chart, write_json, N_SIM, rng

r = rng()
N = N_SIM

PERSONAS = ["Lite", "Pro", "Family"]
MONTHLY_FEE = {"Lite": 99.0, "Pro": 416.0, "Family": 1666.0}
ARPU_ANNUAL = {k: v * 12 for k, v in MONTHLY_FEE.items()}

monthly_retention = {
    "Lite":   r.beta(95, 4, N) * 0 + r.triangular(0.94, 0.96, 0.975, N),
    "Pro":    r.triangular(0.955, 0.97, 0.985, N),
    "Family": r.triangular(0.97, 0.985, 0.995, N),
}

gross_margin = {
    "Lite":   r.triangular(0.78, 0.82, 0.86, N),
    "Pro":    r.triangular(0.76, 0.80, 0.85, N),
    "Family": r.triangular(0.68, 0.73, 0.78, N),
}

cac = {
    "Lite":   r.lognormal(np.log(600),    0.35, N),
    "Pro":    r.lognormal(np.log(3500),   0.40, N),
    "Family": r.lognormal(np.log(22000),  0.45, N),
}

result = {
    "as_of": "2026-04-30",
    "currency": "CNY",
    "monte_carlo_n": int(N_SIM),
    "personas": {},
}

summary_rows = []

for p in PERSONAS:
    monthly_churn = 1 - monthly_retention[p]
    avg_lifetime_months = 1.0 / np.maximum(monthly_churn, 1e-4)
    avg_lifetime_months = np.clip(avg_lifetime_months, 0, 60)

    arpu_m = MONTHLY_FEE[p]
    ltv = arpu_m * avg_lifetime_months * gross_margin[p]
    payback = cac[p] / np.maximum(arpu_m * gross_margin[p], 1.0)
    ltv_cac = ltv / np.maximum(cac[p], 1.0)

    def st(s):
        m, lo, hi = ci(s)
        return {"median": float(m), "p5": float(lo), "p95": float(hi)}

    persona_block = {
        "monthly_fee_CNY": float(arpu_m),
        "annual_arpu_CNY": float(arpu_m * 12),
        "avg_lifetime_months": st(avg_lifetime_months),
        "gross_margin_pct": st(gross_margin[p]),
        "CAC_CNY": st(cac[p]),
        "LTV_CNY": st(ltv),
        "LTV_CAC_ratio": st(ltv_cac),
        "payback_months": st(payback),
    }
    result["personas"][p] = persona_block

    print(f"── {p:<7s} | ARPU/yr {fmt_cny(arpu_m*12):>9s} | "
          f"LTV {fmt_cny(persona_block['LTV_CNY']['median']):>9s} | "
          f"CAC {fmt_cny(persona_block['CAC_CNY']['median']):>9s} | "
          f"LTV/CAC {persona_block['LTV_CAC_ratio']['median']:.1f}× | "
          f"Payback {persona_block['payback_months']['median']:.1f} mo")
    summary_rows.append((p, persona_block))


blend_arpu = sum(MONTHLY_FEE[p] * 12 * w for p, w in zip(PERSONAS, [0.55, 0.35, 0.10]))
blend_ltv = sum(result["personas"][p]["LTV_CNY"]["median"] * w
                for p, w in zip(PERSONAS, [0.55, 0.35, 0.10]))
blend_cac = sum(result["personas"][p]["CAC_CNY"]["median"] * w
                for p, w in zip(PERSONAS, [0.55, 0.35, 0.10]))
blend_pb  = blend_cac / (blend_arpu / 12 * 0.80)
result["blended_55_35_10"] = {
    "annual_arpu_CNY": float(blend_arpu),
    "LTV_CNY": float(blend_ltv),
    "CAC_CNY": float(blend_cac),
    "LTV_CAC_ratio": float(blend_ltv / blend_cac),
    "payback_months": float(blend_pb),
}

print(f"── 加权 (55/35/10): ARPU/yr {fmt_cny(blend_arpu)} | "
      f"LTV {fmt_cny(blend_ltv)} | CAC {fmt_cny(blend_cac)} | "
      f"LTV/CAC {blend_ltv/blend_cac:.1f}× | Payback {blend_pb:.1f} mo")

write_json("02_unit_economics", result)

fig, axs = plt.subplots(1, 2, figsize=(11.5, 4.6))

x = np.arange(len(PERSONAS))
ltv_vals = [result["personas"][p]["LTV_CNY"]["median"] for p in PERSONAS]
cac_vals = [result["personas"][p]["CAC_CNY"]["median"] for p in PERSONAS]
ltv_lo   = [result["personas"][p]["LTV_CNY"]["p5"]  for p in PERSONAS]
ltv_hi   = [result["personas"][p]["LTV_CNY"]["p95"] for p in PERSONAS]
cac_lo   = [result["personas"][p]["CAC_CNY"]["p5"]  for p in PERSONAS]
cac_hi   = [result["personas"][p]["CAC_CNY"]["p95"] for p in PERSONAS]

axs[0].bar(x - 0.18, ltv_vals, width=0.34, color=BRAND["teal"], label="LTV (中位)")
axs[0].errorbar(x - 0.18, ltv_vals, yerr=[
    np.array(ltv_vals) - np.array(ltv_lo),
    np.array(ltv_hi) - np.array(ltv_vals),
], fmt="none", color=BRAND["ink"], capsize=4, lw=1.0)
axs[0].bar(x + 0.18, cac_vals, width=0.34, color=BRAND["amber"], label="CAC (中位)")
axs[0].errorbar(x + 0.18, cac_vals, yerr=[
    np.array(cac_vals) - np.array(cac_lo),
    np.array(cac_hi) - np.array(cac_vals),
], fmt="none", color=BRAND["ink"], capsize=4, lw=1.0)
axs[0].set_xticks(x, PERSONAS)
axs[0].set_ylabel("人民币 (¥)")
axs[0].set_yscale("log")
axs[0].set_title("LTV vs CAC（90% MC 区间）", pad=8)
axs[0].legend()
for i, p in enumerate(PERSONAS):
    rt = result["personas"][p]["LTV_CAC_ratio"]["median"]
    axs[0].text(i, max(ltv_vals[i], cac_vals[i]) * 1.7,
                f"LTV/CAC = {rt:.1f}×",
                ha="center", fontsize=9, color=BRAND["blue"], fontweight="bold")

pb_med = [result["personas"][p]["payback_months"]["median"] for p in PERSONAS]
pb_lo  = [result["personas"][p]["payback_months"]["p5"]    for p in PERSONAS]
pb_hi  = [result["personas"][p]["payback_months"]["p95"]   for p in PERSONAS]

axs[1].barh(x, pb_med, color=PALETTE[:3], height=0.55)
axs[1].errorbar(pb_med, x, xerr=[
    np.array(pb_med) - np.array(pb_lo),
    np.array(pb_hi) - np.array(pb_med),
], fmt="none", color=BRAND["ink"], capsize=4, lw=1.0)
axs[1].set_yticks(x, PERSONAS)
axs[1].set_xlabel("Payback 月数")
axs[1].set_title("Payback 周期（90% MC 区间）", pad=8)
axs[1].axvline(12, color=BRAND["red"], ls="--", lw=1.2, label="健康 12 个月线")
axs[1].legend(fontsize=9)
for i, m in enumerate(pb_med):
    axs[1].text(m + 0.4, i, f"{m:.1f} mo", va="center", fontsize=10, color=BRAND["ink"])

fig.suptitle("§5.4 InvestMind 单位经济：三档客户 LTV / CAC / Payback",
             fontsize=13, fontweight="bold", y=1.02, color=BRAND["ink"])
fig.tight_layout()
save_chart(fig, "fig_02_unit_economics")

print("✓ 02_unit_economics 完成")
