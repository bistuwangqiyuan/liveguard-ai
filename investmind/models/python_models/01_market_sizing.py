"""
01_market_sizing.py
===================

TAM / SAM / SOM —— 中国「早期股权投资可行性研究 SaaS」市场容量
（自上而下 + 自下而上双向校验，蒙特卡洛 N=200,000）。

---------------------------------------------------------------------------
ASSUMPTIONS（保守立场 · 取可公开验证区间的中值）
---------------------------------------------------------------------------

A1. 中国 HNWI 个人投资者总数（可投资金融资产 ≥ ¥600 万）
    ≈ 1,070 万人  (区间 [950 万, 1,200 万])
    - 招商银行 / 贝恩《2023 中国私人财富报告》：316 万 ≥ ¥1,000 万；推算
      ¥600 万门槛覆盖人群 ~ 3.4×
    - 麦肯锡 2024：HNWI 增速 12% CAGR

A2. 持证或活跃的天使 / 个人 PE LP 数量
    ≈ 9.5 万人 (区间 [6 万, 15 万])
    - 中国证券投资基金业协会（AMAC）登记 GP 自然人 / 合格 LP 自然人统计
      + IT 桔子 / 鲸准非登记活跃天使估算

A3. 早期股权投资意愿渗透率（HNWI 中愿意"系统化"评估早期项目者）
    ≈ 11% (区间 [7%, 16%])
    - 招商银行 PWR 2024：12% HNWI 已配置或计划配置 PE/VC

A4. 单用户年订阅 ARPU（人民币）
    ≈ ¥3,800 (区间 [¥2,400, ¥6,000])
    - 三档定价加权：Lite ¥1,188×0.55 + Pro ¥4,988×0.35 + Family ¥19,988×0.10
    - 行业可比：Wind 个人版 ¥4,800、Choice 个人版 ¥3,600、AngelList Pro $499

A5. 自上而下：早期股权投资 AUM 中 SaaS 工具 / 数据预算渗透率
    ≈ 0.18% (区间 [0.10%, 0.30%])
    - 对标二级市场金融数据软件 ≈ 0.4% AUM 渗透；早期市场低成熟度折半
    - 中国早期股权 AUM 2025E ≈ ¥3.2 万亿（清科 / Zero2IPO）

A6. 5 年 SOM 占 SAM 比例
    ≈ 4.0% (区间 [2.5%, 6.5%])
    - 同类型工具 SaaS 在中国 5 年市占常见 3-7%（Wind / Choice / 朝阳永续）

---------------------------------------------------------------------------
SOURCES
---------------------------------------------------------------------------
S1. 招商银行 / 贝恩《2023 中国私人财富报告》
S2. 麦肯锡《2024 中国财富管理报告》
S3. 中国证券投资基金业协会 (AMAC) 私募登记季报 2025Q1
S4. 清科研究 / Zero2IPO《2024 中国股权投资市场年报》
S5. 艾瑞咨询《2024 中国 FinTech / WealthTech 行业研究》
S6. AngelList / Republic 公开融资数据
S7. Wind / 同花顺 / Choice 财报与个人版价格表
S8. IT 桔子 / 鲸准 2024 早期投资数据库口径
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from _common import (
    BRAND, PALETTE, ci, fmt_cny, save_chart, write_json, N_SIM, rng,
)

r = rng()

hnwi_total       = r.triangular(9.5e6,  1.07e7, 1.20e7, N_SIM)
licensed_angels  = r.triangular(6.0e4,  9.5e4,  1.50e5, N_SIM)
willing_ratio    = r.triangular(0.07,   0.11,   0.16,   N_SIM)
arpu             = r.triangular(2_400,  3_800,  6_000,  N_SIM)

aum_early_stage  = r.triangular(2.6e12, 3.2e12, 3.8e12, N_SIM)
penetration_aum  = r.triangular(0.0010, 0.0018, 0.0030, N_SIM)

som_share        = r.triangular(0.025,  0.040,  0.065,  N_SIM)

addressable_users_bottomup = (
    hnwi_total * willing_ratio + licensed_angels
)
tam_bottomup = addressable_users_bottomup * arpu

tam_topdown  = aum_early_stage * penetration_aum

tam_consensus = (tam_bottomup + tam_topdown) / 2.0

sam = (
    hnwi_total * willing_ratio * 0.55 + licensed_angels * 0.85
) * arpu

som_y5 = sam * som_share

def stat(s):
    m, lo, hi = ci(s)
    return {"median": float(m), "p5": float(lo), "p95": float(hi)}


result = {
    "as_of": "2026-04-30",
    "currency": "CNY",
    "monte_carlo_n": int(N_SIM),
    "TAM_topdown_CNY":   stat(tam_topdown),
    "TAM_bottomup_CNY":  stat(tam_bottomup),
    "TAM_consensus_CNY": stat(tam_consensus),
    "SAM_CNY":           stat(sam),
    "SOM_year5_CNY":     stat(som_y5),
    "addressable_users_bottomup": stat(addressable_users_bottomup),
    "assumptions": {
        "hnwi_total_million": [9.5, 10.7, 12.0],
        "licensed_angels_thousand": [60, 95, 150],
        "willing_ratio_pct": [7, 11, 16],
        "arpu_CNY": [2400, 3800, 6000],
        "aum_early_stage_CNY_trillion": [2.6, 3.2, 3.8],
        "penetration_aum_pct": [0.10, 0.18, 0.30],
        "som_share_of_sam_pct": [2.5, 4.0, 6.5],
    },
    "sources": [
        "招商银行/贝恩《2023中国私人财富报告》",
        "麦肯锡《2024中国财富管理报告》",
        "AMAC 2025Q1 私募登记季报",
        "清科研究《2024中国股权投资市场年报》",
        "艾瑞咨询《2024 FinTech/WealthTech行业研究》",
    ],
}

print("── InvestMind · TAM / SAM / SOM (Monte-Carlo N=200k, seed=42) ──")
print(f"  TAM (共识)  : {fmt_cny(result['TAM_consensus_CNY']['median'])}  "
      f"(90% CI [{fmt_cny(result['TAM_consensus_CNY']['p5'])}, "
      f"{fmt_cny(result['TAM_consensus_CNY']['p95'])}])")
print(f"  TAM (自上而下): {fmt_cny(result['TAM_topdown_CNY']['median'])}")
print(f"  TAM (自下而上): {fmt_cny(result['TAM_bottomup_CNY']['median'])}")
print(f"  SAM        : {fmt_cny(result['SAM_CNY']['median'])}")
print(f"  SOM (Y5)   : {fmt_cny(result['SOM_year5_CNY']['median'])}")

write_json("01_market_sizing", result)

fig, ax = plt.subplots(figsize=(8.6, 5.0))

levels = [
    ("TAM\n(共识)",   tam_consensus),
    ("SAM",           sam),
    ("SOM (Y5)",      som_y5),
]
medians = np.array([np.median(s) for s in (tam_consensus, sam, som_y5)])
p5s     = np.array([np.percentile(s, 5)  for s in (tam_consensus, sam, som_y5)])
p95s    = np.array([np.percentile(s, 95) for s in (tam_consensus, sam, som_y5)])

bar_widths = medians / medians.max()
y = np.arange(len(levels))
for i, (label, _) in enumerate(levels):
    ax.barh(y[i], bar_widths[i], color=PALETTE[i], alpha=0.92, height=0.6)
    ax.text(bar_widths[i] + 0.01, y[i], f"{fmt_cny(medians[i])}\n90%CI [{fmt_cny(p5s[i])}, {fmt_cny(p95s[i])}]",
            va="center", fontsize=10, color=BRAND["ink"])

ax.set_yticks(y, [lv[0] for lv in levels], fontsize=11, color=BRAND["ink"])
ax.invert_yaxis()
ax.set_xlim(0, 1.55)
ax.set_xticks([])
ax.spines["bottom"].set_visible(False)
ax.set_title("InvestMind · TAM / SAM / SOM 漏斗（蒙特卡洛 90% 区间）", pad=14)
ax.grid(False)
fig.text(0.99, 0.01, "Source: BP §2.4 · MC N=200k seed=42",
         ha="right", fontsize=8, color=BRAND["grey"])
save_chart(fig, "fig_01_tam_sam_som_funnel")

fig2, axs = plt.subplots(1, 2, figsize=(11.5, 4.4))

bins = np.linspace(0, np.percentile(np.concatenate([tam_topdown, tam_bottomup]), 99.5), 70)
axs[0].hist(tam_topdown / 1e8, bins=bins / 1e8, alpha=0.65, label="自上而下 (AUM × 渗透率)",
            color=BRAND["blue"], edgecolor="white")
axs[0].hist(tam_bottomup / 1e8, bins=bins / 1e8, alpha=0.65, label="自下而上 (用户 × ARPU)",
            color=BRAND["teal"], edgecolor="white")
axs[0].axvline(np.median(tam_consensus) / 1e8, color=BRAND["red"], lw=2, ls="--",
               label=f"共识中位 {fmt_cny(np.median(tam_consensus))}")
axs[0].set_xlabel("市场规模 (¥ 亿)")
axs[0].set_ylabel("MC 样本频次")
axs[0].set_title("TAM 双向校验：分布对比", pad=10)
axs[0].legend(loc="upper right", fontsize=9)

shares = [
    np.percentile(tam_consensus, 50) - np.percentile(sam, 50),
    np.percentile(sam, 50) - np.percentile(som_y5, 50),
    np.percentile(som_y5, 50),
]
labels = ["TAM 不可服务部分", "SAM 5 年外可达", "SOM Y5 可拿"]
axs[1].pie(
    shares,
    labels=labels,
    colors=[BRAND["grey"], BRAND["amber"], BRAND["teal"]],
    autopct=lambda p: f"{p:.1f}%",
    startangle=90,
    wedgeprops=dict(width=0.45, edgecolor="white"),
    textprops=dict(color=BRAND["ink"], fontsize=10),
)
axs[1].set_title("市场分层结构（中位数口径）", pad=10)

fig2.suptitle("§2.4 中国早期股权投资可行性研究 SaaS 市场量化", fontsize=13,
              fontweight="bold", color=BRAND["ink"], y=1.02)
fig2.tight_layout()
save_chart(fig2, "fig_01_tam_validation")

print("✓ 01_market_sizing 完成 → outputs/01_market_sizing.json")
print("✓ 图表已保存到 docs/images/charts/fig_01_*.png")
