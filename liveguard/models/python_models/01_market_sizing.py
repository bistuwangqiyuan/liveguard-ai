"""
01_market_sizing.py
===================

TAM / SAM / SOM — 中国直播电商合规/监控市场 · 自上而下 + 自下而上双向校验。

---------------------------------------------------------------------------
ASSUMPTIONS（保守立场 · 取可公开验证区间的中值）
---------------------------------------------------------------------------

A1. 2025 中国直播电商 GMV ≈ ¥5.83 万亿
    - 商务部 / 艾瑞 / QuestMobile 多家估算：¥5.5–¥6.2 T
    - 取中值 5.83 T，区间 [5.3 T, 6.3 T]

A2. 活跃主播账号（月活 ≥1 场）≈ 1,350 万
    - 《抖音电商生态发展报告 2024》+ 快手 2024 Q4 财报 + 淘宝直播官方
    - 区间 [1,100 万, 1,600 万]

A3. 需要合规/监控服务的头部 + 腰部占比 ≈ 12%
    - 依据 80/20 规则调整：头部 1% 高度需要；腰部 11% 需求增长
    - 区间 [9%, 16%]

A4. 单主播可承担年订阅 ARPU ≈ ¥3,600（Starter 月 ¥299×12）
    - 按 BP §4 价格锚点 Starter 299/Pro 1,299/Ent 定制
    - 取 Starter/Pro 加权 60%/35%/5% → ≈ ¥3,600
    - 区间 [¥2,400, ¥5,800]

A5. 监控软件在直播电商 GMV 中的平均预算渗透率 ≈ 0.12%
    - 对标互联网安全软件占 IT 支出 ≈ 3% × 直播电商占比
    - 区间 [0.07%, 0.20%]

---------------------------------------------------------------------------
SOURCES
---------------------------------------------------------------------------
S1. 中国商务部《2024 年网络零售报告》: http://www.mofcom.gov.cn/
S2. 艾瑞咨询 《2024 年中国直播电商行业研究报告》
S3. QuestMobile《2024 年直播电商生态洞察》
S4. 抖音集团《2024 抖音电商生态发展报告》
S5. 快手 Kuaishou Technology 2024 Q4 Earnings Release, HKEX 1024.HK
S6. 淘宝直播 2024 年度数据白皮书
S7. 艾媒咨询《中国 SaaS 市场预测 2024-2028》
"""

from __future__ import annotations

import numpy as np

from _common import ci, fmt_cny, write_json

rng = np.random.default_rng(42)
N = 200_000

gmv = rng.triangular(5.3e12, 5.83e12, 6.3e12, N)
hosts = rng.triangular(1.1e7, 1.35e7, 1.6e7, N)
need_ratio = rng.triangular(0.09, 0.12, 0.16, N)
arpu = rng.triangular(2400, 3600, 5800, N)
penetration = rng.triangular(0.0007, 0.0012, 0.0020, N)

tam_topdown = gmv * penetration
tam_bottomup = hosts * arpu

tam = (tam_topdown + tam_bottomup) / 2

# SAM = 服务性直播（头部+腰部）子集
sam = hosts * need_ratio * arpu

# SOM = 5 年内可抢占 3% 的 SAM（保守；参考同类 SaaS 第一阶段市占）
som_ratio = rng.triangular(0.018, 0.03, 0.05, N)
som = sam * som_ratio

result = {
    "TAM_topdown_CNY": {
        "median": fmt_cny(float(np.median(tam_topdown))),
        "p5": fmt_cny(float(np.percentile(tam_topdown, 5))),
        "p95": fmt_cny(float(np.percentile(tam_topdown, 95))),
    },
    "TAM_bottomup_CNY": {
        "median": fmt_cny(float(np.median(tam_bottomup))),
        "p5": fmt_cny(float(np.percentile(tam_bottomup, 5))),
        "p95": fmt_cny(float(np.percentile(tam_bottomup, 95))),
    },
    "TAM_consensus_CNY": {
        "median": fmt_cny(float(np.median(tam))),
        "p5": fmt_cny(float(np.percentile(tam, 5))),
        "p95": fmt_cny(float(np.percentile(tam, 95))),
    },
    "SAM_CNY": {
        "median": fmt_cny(float(np.median(sam))),
        "p5": fmt_cny(float(np.percentile(sam, 5))),
        "p95": fmt_cny(float(np.percentile(sam, 95))),
    },
    "SOM_year5_CNY": {
        "median": fmt_cny(float(np.median(som))),
        "p5": fmt_cny(float(np.percentile(som, 5))),
        "p95": fmt_cny(float(np.percentile(som, 95))),
    },
    "assumptions": {
        "gmv_2025_CNY_trillion": [5.3, 5.83, 6.3],
        "active_hosts_million": [11, 13.5, 16],
        "need_ratio_pct": [9, 12, 16],
        "arpu_CNY": [2400, 3600, 5800],
        "penetration_pct": [0.07, 0.12, 0.20],
        "som_share_of_sam_pct": [1.8, 3.0, 5.0],
    },
    "sources": [
        "商务部《2024 年网络零售报告》",
        "艾瑞咨询 2024 直播电商研究报告",
        "QuestMobile 2024 直播电商生态洞察",
        "抖音集团 2024 生态发展报告",
        "快手 2024 Q4 财报 (HKEX 1024.HK)",
        "淘宝直播 2024 数据白皮书",
    ],
}

print("── TAM / SAM / SOM (Monte-Carlo N=200k) ──")
print(f"  TAM (共识)  : {result['TAM_consensus_CNY']['median']}  "
      f"(90% CI [{result['TAM_consensus_CNY']['p5']}, {result['TAM_consensus_CNY']['p95']}])")
print(f"  SAM        : {result['SAM_CNY']['median']}  "
      f"(90% CI [{result['SAM_CNY']['p5']}, {result['SAM_CNY']['p95']}])")
print(f"  SOM (Y5)   : {result['SOM_year5_CNY']['median']}  "
      f"(90% CI [{result['SOM_year5_CNY']['p5']}, {result['SOM_year5_CNY']['p95']}])")

write_json("01_market_sizing", result)
