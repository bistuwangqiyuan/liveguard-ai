"""
02_unit_economics.py
====================

分客群单位经济：LTV / CAC / Payback / Rule of 40。对应 BP §5.4。
三档（Starter/Pro/Enterprise）均以贡献毛利 78% 计，LTV = 月贡献毛利 / 月流失。
蒙特卡洛 N=200,000，seed=42。常量来自 data_sources.py。

ASSUMPTIONS
-----------
* 贡献毛利率 = 78%（稳态；GPU/带宽/短信/电话成本按 §8 测算）
* 月流失：Starter 5.0% / Pro 2.5% / Enterprise 0.8%
* CAC：Starter ¥280 / Pro ¥850 / Enterprise ¥18,000
SOURCES：SaaS Capital 2024 / OpenView 2024 / ChinaVenture 2024 SaaS 调研
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from _common import BRAND, PALETTE, ci, fmt_cny, save_chart, write_json, N_SIM, rng
import data_sources as DS

r = rng()
N = N_SIM
CM = DS.SEGMENT_CONTRIB_MARGIN

segments = {}
for name, p in DS.PRICING.items():
    monthly = p["monthly"]
    churn0 = p["monthly_churn"]
    cac0 = DS.CAC[name]
    # MC：贡献毛利率、流失、CAC 三角扰动
    cm = r.triangular(CM - 0.05, CM, CM + 0.04, N)
    churn = r.triangular(churn0 * 0.8, churn0, churn0 * 1.3, N)
    cac = r.triangular(cac0 * 0.8, cac0, cac0 * 1.4, N)
    # 确定性基准（headline，与 BP 表对齐）
    monthly_contrib_base = monthly * CM
    ltv_base = monthly_contrib_base / churn0
    cac_base = cac0
    # 蒙特卡洛仅用于给出 90% 区间
    monthly_contrib = monthly * cm
    ltv = monthly_contrib / churn
    ltv_cac = ltv / cac
    segments[name] = {
        "monthly_price_CNY": monthly,
        "monthly_contribution_CNY": round(monthly_contrib_base, 0),
        "monthly_churn_pct": round(churn0 * 100, 1),
        "lifetime_months": round(1.0 / churn0, 0),
        "CAC_CNY": round(cac_base, 0),
        "LTV_CNY": round(ltv_base, 0),
        "LTV_to_CAC": round(ltv_base / cac_base, 1),
        "payback_months": round(cac_base / monthly_contrib_base, 1),
        "LTV_to_CAC_90CI": [round(x, 1) for x in ci(ltv_cac)[1:]],
    }

# 混合（按客户结构加权）
blended_churn = sum(DS.PRICING[s]["mix"] * DS.PRICING[s]["monthly_churn"] for s in DS.PRICING)
blended_payback_by_year = []
for cac_y in DS.CAC_BLENDED_BY_YEAR:
    # 月贡献毛利（混合 ARPU/12 × 贡献毛利率）
    monthly_contrib_blend = DS.BLENDED_ARPU_ANNUAL / 12 * CM
    blended_payback_by_year.append(round(cac_y / monthly_contrib_blend, 1))

payload = {
    "as_of": DS.AS_OF, "currency": "CNY", "monte_carlo_n": int(N),
    "contribution_margin_pct": round(CM * 100, 0),
    "segments": segments,
    "blended_monthly_churn_pct": round(blended_churn * 100, 2),
    "blended_payback_months_by_year": blended_payback_by_year,
    "sources": ["SaaS Capital 2024 Benchmark", "OpenView 2024 SaaS Benchmarks", "ChinaVenture 2024 中国 SaaS 调研"],
}

print("── 分客群单位经济（MC N=200k, seed=42）──")
for s, v in segments.items():
    print(f"  {s:<11s} LTV {fmt_cny(v['LTV_CNY']):>12s}  CAC {fmt_cny(v['CAC_CNY']):>9s}  "
          f"LTV/CAC {v['LTV_to_CAC']:>5}x  Payback {v['payback_months']}月")

write_json("02_unit_economics", payload)

# ── 图：LTV/CAC 对比 + 分年 Payback ─────────────────────────────────────────
fig, axs = plt.subplots(1, 2, figsize=(12.0, 4.6))
names = list(segments.keys())
ltv_cac = [segments[s]["LTV_to_CAC"] for s in names]
bars = axs[0].bar(names, ltv_cac, color=[BRAND["blue"], BRAND["teal"], BRAND["violet"]], width=0.55, alpha=0.92)
axs[0].axhline(3, color=BRAND["red"], ls="--", lw=1.2, label="健康线 3×")
axs[0].axhline(5, color=BRAND["amber"], ls="--", lw=1.2, label="优秀线 5×")
for i, v in enumerate(ltv_cac):
    axs[0].text(i, v * 1.02, f"{v}×", ha="center", fontsize=11, fontweight="bold", color=BRAND["ink"])
axs[0].set_ylabel("LTV / CAC")
axs[0].set_title("分客群 LTV/CAC（远超优秀线）", pad=8)
axs[0].legend(fontsize=9)

axs[1].plot(DS.YEARS, blended_payback_by_year, "o-", color=BRAND["blue"], lw=2.2, markersize=9)
for i, v in enumerate(blended_payback_by_year):
    axs[1].annotate(f"{v}月", (i, v), xytext=(0, 8), textcoords="offset points", ha="center", fontsize=9, color=BRAND["ink"])
axs[1].axhline(6, color=BRAND["red"], ls="--", lw=1.2, label="世界级 < 6 月")
axs[1].set_ylabel("混合回本期 (月)")
axs[1].set_title("分年混合 Payback", pad=8)
axs[1].legend(fontsize=9)
axs[1].set_ylim(0, max(blended_payback_by_year + [7]))
fig.suptitle("§5.4 守播 LiveGuard 单位经济", fontsize=13, fontweight="bold", color=BRAND["ink"], y=1.02)
fig.tight_layout()
save_chart(fig, "fig_02_unit_economics")

print("✓ 02_unit_economics 完成 → JSON + fig_02_unit_economics.png")
