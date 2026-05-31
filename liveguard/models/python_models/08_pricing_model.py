"""
08_pricing_model.py
===================

三档 SaaS 定价 + 价格弹性 + 加权 ARPU。对应 BP §5.2 / §5.3。

* 档位：Starter ¥199/月、Pro ¥599/月、Enterprise ¥250,000/年
* 客户结构：70 / 25 / 5 → 加权年 ARPU = ¥15,969
* 价格弹性（恒弹性 q = q0·p^-e）：Starter 1.5 / Pro 0.8 / Enterprise 0.4
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from _common import BRAND, PALETTE, fmt_cny, save_chart, write_json
import data_sources as DS

tiers = {}
for name, p in DS.PRICING.items():
    tiers[name] = {
        "monthly_CNY": p["monthly"],
        "annual_CNY": p["annual"],
        "customer_mix_pct": round(p["mix"] * 100, 0),
        "monthly_churn_pct": round(p["monthly_churn"] * 100, 1),
        "price_elasticity": DS.PRICE_ELASTICITY[name],
        "arpu_contribution_CNY": round(p["annual"] * p["mix"], 1),
    }

arpu_blend = DS.BLENDED_ARPU_ANNUAL

payload = {
    "as_of": DS.AS_OF, "currency": "CNY",
    "tiers": tiers,
    "blended_arpu_annual_CNY": round(arpu_blend, 1),
    "blended_arpu_monthly_CNY": round(arpu_blend / 12, 1),
    "revenue_mix_y1_y3_y5": {
        "SaaS订阅": [0.88, 0.76, 0.68],
        "按量付费/加路": [0.05, 0.12, 0.14],
        "平台分润/API": [0.03, 0.08, 0.13],
        "硬件/私有化": [0.04, 0.04, 0.05],
    },
    "sources": ["公司定价（对标微盟/有赞 + 价值定价）", "KA 客户访谈"],
}

print("── 三档定价与加权 ARPU ──")
for n, t in tiers.items():
    print(f"  {n:<11s} ¥{t['monthly_CNY']:>8,.0f}/月  年 {fmt_cny(t['annual_CNY'])}  占比 {t['customer_mix_pct']:.0f}%  e={t['price_elasticity']}")
print(f"  加权年 ARPU = {fmt_cny(arpu_blend)} (≈ ¥{arpu_blend/12:.0f}/月)")

write_json("08_pricing_model", payload)

# ── 图：ARPU 贡献分解 + 价格弹性曲线 ────────────────────────────────────────
fig, axs = plt.subplots(1, 2, figsize=(12.0, 4.6))
names = list(tiers.keys())
contrib = [tiers[n]["arpu_contribution_CNY"] for n in names]
bottom = 0
for i, n in enumerate(names):
    axs[0].bar("加权 ARPU", contrib[i], bottom=bottom, color=PALETTE[i], width=0.5,
               label=f"{n} ¥{contrib[i]:,.0f} ({tiers[n]['customer_mix_pct']:.0f}%)")
    axs[0].text(0, bottom + contrib[i] / 2, f"¥{contrib[i]:,.0f}", ha="center", va="center", fontsize=9, color="white", fontweight="bold")
    bottom += contrib[i]
axs[0].text(0, bottom * 1.03, f"合计 {fmt_cny(arpu_blend)}", ha="center", fontsize=10, fontweight="bold", color=BRAND["ink"])
axs[0].set_ylabel("年 ARPU 贡献 (¥)")
axs[0].set_title("加权 ARPU 分解（长尾驱动：5% Ent 贡献 78%）", pad=8)
axs[0].legend(fontsize=8, loc="upper right")

p_rel = np.linspace(0.6, 1.4, 60)
for i, n in enumerate(names):
    e = DS.PRICE_ELASTICITY[n]
    q_rel = p_rel ** (-e)
    axs[1].plot(p_rel * 100, q_rel * 100, "-", color=PALETTE[i], lw=2.2, label=f"{n} (e={e})")
axs[1].axvline(100, color=BRAND["grey"], ls=":", lw=1)
axs[1].set_xlabel("相对价格 (% of 基准)")
axs[1].set_ylabel("相对需求量 (%)")
axs[1].set_title("价格弹性曲线（Ent 低弹性 → 提价空间）", pad=8)
axs[1].legend(fontsize=9)
fig.suptitle("§5.2-5.3 定价与价格弹性", fontsize=13, fontweight="bold", color=BRAND["ink"], y=1.02)
fig.tight_layout()
save_chart(fig, "fig_08_pricing")

print("✓ 08_pricing_model 完成 → JSON + fig_08_pricing.png")
