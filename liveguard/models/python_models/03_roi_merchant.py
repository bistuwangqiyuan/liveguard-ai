"""
03_roi_merchant.py
==================

商家侧 ROI — 订阅 LiveGuard vs 不订阅。

模型：
    净收益 = (避免的合规罚款 + 减少的 GMV 流失 + 节省的人工成本)
              - 订阅费

ASSUMPTIONS
-----------
* 典型商家月均直播 240 小时（每天 8h × 30d）
* 每次离岗/脱岗平均 GMV 流失 ≈ 1,400 元/次（抖音电商 2024 年直播电商 GMV 转化均值反推）
* 传统方案（人工看守 1:3 比例、每人 800 元/月）人工成本 × 被监控主播数
* LiveGuard 套餐 Pro 月 ¥1,299，覆盖 5 路并发

SOURCES
-------
* 抖音电商 2024 年直播电商转化数据
* 艾瑞 2024 年直播电商主播运营成本白皮书
* 国家市监总局 2024 年直播电商违规典型案例公告
"""

from __future__ import annotations

import numpy as np

from _common import fmt_cny, write_json

rng = np.random.default_rng(21)
N = 200_000

hours_monthly = rng.triangular(180, 240, 360, N)
offline_incidents_per_hour = rng.triangular(0.6, 1.1, 1.8, N) / 10  # 每 10 小时次数
gmv_loss_per_incident = rng.triangular(700, 1400, 2600, N)

# LiveGuard 拦截率（算法 + 人工复核）
interception_rate = rng.triangular(0.75, 0.88, 0.95, N)

# 合规罚款期望（每月罚款事件概率 × 罚款金额）
penalty_prob = rng.triangular(0.02, 0.05, 0.10, N)
penalty_amount = rng.triangular(5000, 20000, 80000, N)
expected_penalty_saving = penalty_prob * penalty_amount * rng.triangular(0.5, 0.8, 0.95, N)

# 传统看守成本：按 1:3 覆盖 5 路并发 → 5/3 ≈ 1.67 人
traditional_staff_cost = 1.67 * rng.triangular(600, 800, 1100, N)

# GMV 流失减少
incidents_monthly = hours_monthly * offline_incidents_per_hour
gmv_saving = incidents_monthly * gmv_loss_per_incident * interception_rate

# 订阅费
subscription_fee = rng.triangular(299, 1299, 4999, N)

net_benefit = gmv_saving + expected_penalty_saving + traditional_staff_cost - subscription_fee
roi_pct = net_benefit / subscription_fee * 100

payload = {
    "assumptions": {
        "hours_monthly": [180, 240, 360],
        "incidents_per_10h": [0.6, 1.1, 1.8],
        "gmv_loss_per_incident_CNY": [700, 1400, 2600],
        "interception_rate": [0.75, 0.88, 0.95],
        "subscription_fee_CNY": [299, 1299, 4999],
    },
    "monthly_gmv_saving_CNY_median": fmt_cny(float(np.median(gmv_saving))),
    "monthly_penalty_saving_CNY_median": fmt_cny(float(np.median(expected_penalty_saving))),
    "monthly_labor_saving_CNY_median": fmt_cny(float(np.median(traditional_staff_cost))),
    "monthly_net_benefit_CNY_median": fmt_cny(float(np.median(net_benefit))),
    "ROI_pct_median": round(float(np.median(roi_pct)), 1),
    "ROI_pct_p5_p95": [round(float(np.percentile(roi_pct, 5)), 1),
                       round(float(np.percentile(roi_pct, 95)), 1)],
    "payback_days_median": round(30 * float(np.median(subscription_fee)) /
                                 float(np.median(net_benefit + subscription_fee)), 1),
}

print("── 商家 ROI ──")
print(f"  月净收益 = {payload['monthly_net_benefit_CNY_median']}  "
      f"ROI = {payload['ROI_pct_median']}%  (90% CI {payload['ROI_pct_p5_p95']}%)")
print(f"  回本天数 ≈ {payload['payback_days_median']} 天")

write_json("03_roi_merchant", payload)
