"""
03_roi_merchant.py
==================

客户侧 ROI 计算器（演示用）。对应 BP §5.5。
模型：
    现有损失 = 年 GMV × (空播损失率 9.0% + 平台罚款率 2.5%)
    部署后损失 = 年 GMV × (空播 9.0%×30% + 罚款 2.5%×16%) = 年 GMV × 3.1%
    年节省 = 现有损失 − 部署后损失
    ROI = (年节省 − 工具年费) / 工具年费
    回本天数 = 工具年费 / (年节省 / 365)

三档客户：个人主播 / 中型 MCN / 头部 MCN。
SOURCES：抖音电商 2024 转化数据、艾瑞 2024 主播运营成本白皮书、市监总局违规案例。
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from _common import BRAND, PALETTE, fmt_cny, save_chart, write_json, N_SIM, rng
import data_sources as DS

r = rng()
N = N_SIM

# 损失率参数（基线）
IDLE_LOSS = 0.09          # 空播损失率
PENALTY_RATE = 0.025      # 平台罚款率
IDLE_RESIDUAL = 0.30      # 部署后空播残留比例
PENALTY_RESIDUAL = 0.16   # 部署后罚款残留比例

segments = [
    {"name": "个人主播 / 小商家", "daily_gmv": 6_000,   "annual_fee": DS.PRICING["Starter"]["annual"]},
    {"name": "中型 MCN / 品牌自播", "daily_gmv": 35_000,  "annual_fee": DS.PRICING["Pro"]["annual"]},
    {"name": "头部 MCN / 大型电商", "daily_gmv": 220_000, "annual_fee": DS.PRICING["Enterprise"]["annual"]},
]

rows = []
for s in segments:
    annual_gmv = s["daily_gmv"] * 360
    existing_loss = annual_gmv * (IDLE_LOSS + PENALTY_RATE)
    post_loss = annual_gmv * (IDLE_LOSS * IDLE_RESIDUAL + PENALTY_RATE * PENALTY_RESIDUAL)
    saving = existing_loss - post_loss
    roi = (saving - s["annual_fee"]) / s["annual_fee"]
    payback_days = s["annual_fee"] / (saving / 365)
    rows.append({
        "segment": s["name"],
        "daily_gmv_CNY": s["daily_gmv"],
        "annual_gmv_CNY": round(annual_gmv, 0),
        "existing_loss_CNY": round(existing_loss, 0),
        "post_loss_CNY": round(post_loss, 0),
        "annual_saving_CNY": round(saving, 0),
        "annual_fee_CNY": s["annual_fee"],
        "ROI_x": round(roi, 1),
        "payback_days": round(payback_days, 1),
    })

# ROI 敏感性：空播损失率 r0 从 1% → 12%（Pro 档）
r0_grid = np.linspace(0.01, 0.12, 40)
pro = segments[1]
pro_gmv = pro["daily_gmv"] * 360
roi_curve = []
for r0 in r0_grid:
    existing = pro_gmv * (r0 + PENALTY_RATE)
    post = pro_gmv * (r0 * IDLE_RESIDUAL + PENALTY_RATE * PENALTY_RESIDUAL)
    sv = existing - post
    roi_curve.append((sv - pro["annual_fee"]) / pro["annual_fee"])

payload = {
    "as_of": DS.AS_OF, "currency": "CNY",
    "model": {
        "idle_loss_rate": IDLE_LOSS, "penalty_rate": PENALTY_RATE,
        "idle_residual": IDLE_RESIDUAL, "penalty_residual": PENALTY_RESIDUAL,
        "open_days_per_year": 360,
    },
    "segments": rows,
    "sensitivity_pro_idle_loss": {
        "idle_loss_grid": [round(x, 3) for x in r0_grid.tolist()],
        "roi_x": [round(x, 1) for x in roi_curve],
    },
    "sources": ["抖音电商 2024 转化数据", "艾瑞 2024 主播运营成本白皮书", "市监总局 2024 违规典型案例"],
}

print("── 客户 ROI ──")
for row in rows:
    print(f"  {row['segment']:<18s} ROI {row['ROI_x']:>6}×  回本 {row['payback_days']:>5} 天  "
          f"年节省 {fmt_cny(row['annual_saving_CNY'])}")

write_json("03_roi_merchant", payload)

# ── 图：ROI 柱状 + 敏感性 ───────────────────────────────────────────────────
fig, axs = plt.subplots(1, 2, figsize=(12.0, 4.6))
names = [r["segment"].split(" / ")[0] for r in rows]
rois = [r["ROI_x"] for r in rows]
bars = axs[0].bar(names, rois, color=[BRAND["blue"], BRAND["teal"], BRAND["violet"]], width=0.55, alpha=0.92)
for i, r_ in enumerate(rows):
    axs[0].text(i, rois[i] * 1.02, f"{rois[i]}×\n回本{r_['payback_days']}天", ha="center", fontsize=9, color=BRAND["ink"])
axs[0].set_ylabel("ROI (倍)")
axs[0].set_title("三档客户 ROI（最长回本 < 14 天）", pad=8)

axs[1].plot(r0_grid * 100, roi_curve, "-", color=BRAND["blue"], lw=2.4)
axs[1].axhline(5, color=BRAND["red"], ls="--", lw=1.2, label="ROI 5×")
axs[1].fill_between(r0_grid * 100, roi_curve, alpha=0.12, color=BRAND["blue"])
axs[1].set_xlabel("客户当前空播损失率 r0 (%)")
axs[1].set_ylabel("Pro 档 ROI (倍)")
axs[1].set_title("ROI 敏感性（即使 r0=1% 仍 ≥ 5×）", pad=8)
axs[1].legend(fontsize=9)
fig.suptitle("§5.5 客户 ROI 计算器", fontsize=13, fontweight="bold", color=BRAND["ink"], y=1.02)
fig.tight_layout()
save_chart(fig, "fig_03_roi_customer")

print("✓ 03_roi_merchant 完成 → JSON + fig_03_roi_customer.png")
