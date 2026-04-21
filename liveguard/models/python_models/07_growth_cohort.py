"""
07_growth_cohort.py
===================

5 年 Cohort 留存 + ARR 预测（自下而上）。

* Month 1 新签：120（Y1 Q1） → 随月按 T2D3 节奏增长
* Logo churn 3.5%/月；NRR = 112%
* 以 Month 36 为目标 ARR 输出
"""

from __future__ import annotations

import numpy as np

from _common import fmt_cny, write_json

rng = np.random.default_rng(13)

MONTHS = 60
N_SIM = 10_000

arr_at = np.zeros((N_SIM, MONTHS))

for s in range(N_SIM):
    # 新签序列：T2D3 曲线近似（月度新签量，复合年增长）
    base_month_1 = 120  # Y1 M1 月新签数
    new_logos = []
    compounded = 1.0
    for m in range(MONTHS):
        year = m // 12
        # 每年 YoY 增长率
        growth_yoy = 2.0 if year == 0 else (1.85 if year == 1 else (1.55 if year == 2 else 1.28))
        # 年内月度 ramp（Q4 季节性较强）
        ramp = 1.0 + 0.06 * (m % 12)
        noise = rng.normal(1.0, 0.12)
        # year=0 → compounded=1；year=1 → compounded=2.0；year=2 → 3.7；...
        new_logos.append(max(1, base_month_1 * compounded * ramp * noise))
        if (m + 1) % 12 == 0:
            compounded *= growth_yoy
    new_logos_arr = np.array(new_logos)

    arpu_m = rng.triangular(280, 349, 520)
    monthly_churn = rng.triangular(0.022, 0.035, 0.055)
    nrr_monthly = rng.triangular(1.0045, 1.0095, 1.0165)  # ~NRR 112% 年化

    logos = np.zeros(MONTHS)
    for m in range(MONTHS):
        # 上月留存 × (1 - churn) × NRR 扩张 + 本月新签
        if m == 0:
            logos[m] = new_logos_arr[0]
        else:
            logos[m] = logos[m - 1] * (1 - monthly_churn) * nrr_monthly + new_logos_arr[m]
        arr_at[s, m] = logos[m] * arpu_m * 12

milestones = {
    "M12": float(np.median(arr_at[:, 11])),
    "M24": float(np.median(arr_at[:, 23])),
    "M36": float(np.median(arr_at[:, 35])),
    "M48": float(np.median(arr_at[:, 47])),
    "M60": float(np.median(arr_at[:, 59])),
    "M36_p10": float(np.percentile(arr_at[:, 35], 10)),
    "M36_p90": float(np.percentile(arr_at[:, 35], 90)),
    "M60_p10": float(np.percentile(arr_at[:, 59], 10)),
    "M60_p90": float(np.percentile(arr_at[:, 59], 90)),
}

payload = {
    "n_sim": N_SIM,
    "milestones_CNY": {k: fmt_cny(v) for k, v in milestones.items()},
    "assumptions": {
        "monthly_churn_pct": 3.5,
        "nrr_annual_pct": 112,
        "arpu_m_CNY_triangular": [280, 349, 520],
        "new_logos_M1": 120,
        "growth_schedule": "T2 year1, 1.85x year2, 1.55x year3, 1.28x year4+",
    },
}

print("── 5 年 ARR Cohort 预测（中位数） ──")
for k, v in payload["milestones_CNY"].items():
    print(f"  {k}: {v}")

write_json("07_growth_cohort", payload)
