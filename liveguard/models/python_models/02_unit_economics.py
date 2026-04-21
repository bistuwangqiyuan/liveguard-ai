"""
02_unit_economics.py
====================

LTV / CAC / Payback / Rule of 40 — 蒙特卡洛。

ASSUMPTIONS
-----------
* ARPU 月 = ¥ 349（Starter 299 / Pro 1,299 加权）
* Gross Margin = 72% (GPU/带宽/短信/电话成本按 BP §9 测算)
* Monthly churn = 3.5%（行业中小 B SaaS 中位数）
* Blended CAC:
    - 直销 ¥2,400 / 单
    - 自然/渠道 ¥480 / 单
    - 混合 50/50 → ¥1,440
* Expansion (NRR) = 1.12

SOURCES
-------
* SaaS Capital 2024 Benchmark Report (https://www.saascapital.com/)
* OpenView 2024 SaaS Benchmarks
* ChinaVenture 2024 中国 SaaS 调研报告
"""

from __future__ import annotations

import numpy as np

from _common import ci, fmt_cny, write_json

rng = np.random.default_rng(7)
N = 200_000

arpu_m = rng.triangular(280, 349, 520, N)       # CNY/月
gross_margin = rng.triangular(0.65, 0.72, 0.78, N)
monthly_churn = rng.triangular(0.022, 0.035, 0.055, N)
nrr = rng.triangular(1.05, 1.12, 1.22, N)
cac = rng.triangular(900, 1440, 2800, N)

# 简化 LTV：GM × ARPU_m / churn × NRR 上浮
ltv = gross_margin * arpu_m * nrr / monthly_churn
ltv_to_cac = ltv / cac
payback_months = cac / (arpu_m * gross_margin)

# Rule of 40：growth% + margin%
growth_pct = rng.triangular(0.55, 0.90, 1.30, N) * 100  # Y1→Y2 同比（BP 假设）
rule_of_40 = growth_pct + gross_margin * 100 - 20  # 扣 20% 为假定 OpEx 率

payload = {
    "ARPU_m_CNY": fmt_cny(float(np.median(arpu_m))),
    "gross_margin_%": round(float(np.median(gross_margin)) * 100, 1),
    "monthly_churn_%": round(float(np.median(monthly_churn)) * 100, 2),
    "NRR": round(float(np.median(nrr)), 2),
    "CAC_CNY": fmt_cny(float(np.median(cac))),
    "LTV_CNY": fmt_cny(float(np.median(ltv))),
    "LTV_to_CAC_median": round(float(np.median(ltv_to_cac)), 2),
    "payback_months_median": round(float(np.median(payback_months)), 1),
    "rule_of_40_median": round(float(np.median(rule_of_40)), 1),
    "confidence_intervals": {
        "LTV_90pct": [fmt_cny(x) for x in ci(ltv)[1:]],
        "LTV_to_CAC_90pct": list(ci(ltv_to_cac))[1:],
        "payback_months_90pct": list(ci(payback_months))[1:],
    },
}

print("── Unit economics ──")
print(f"  ARPU_m = {payload['ARPU_m_CNY']}  |  GM = {payload['gross_margin_%']}%  "
      f"|  monthly churn = {payload['monthly_churn_%']}%  |  NRR = {payload['NRR']}x")
print(f"  CAC  = {payload['CAC_CNY']}")
print(f"  LTV  = {payload['LTV_CNY']}   LTV:CAC = {payload['LTV_to_CAC_median']}x")
print(f"  Payback = {payload['payback_months_median']} months")
print(f"  Rule-of-40 = {payload['rule_of_40_median']}")

write_json("02_unit_economics", payload)
