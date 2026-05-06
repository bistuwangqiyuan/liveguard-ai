<!-- ===== File: 99-附录.md ===== -->

# §99 附录 (Appendix)

---

## A. 关键假设清单（与 §8.6 一致）

| # | 假设 | 中位 | 90% CI | 来源 / 模型 |
|---|------|------|------|----------|
| 1 | HNWI 配置意愿率 | 11% | [7%, 16%] | 招商银行 PWR 2024 / 01_market_sizing |
| 2 | 加权 ARPU | ¥4,400 | [¥3,200, ¥6,500] | 三档加权 / 02_unit_economics |
| 3 | 月留存（混合） | 96.9% | [94.0%, 98.5%] | SaaS Capital 2024 / 02_unit_economics |
| 4 | Y5 月新付费 | 9,000 | [5,500, 12,000] | 06_growth_cohort |
| 5 | 撮合 take-rate | 2.0% | [1.2%, 3.0%] | AngelList Letter / 11_revenue_buildup |
| 6 | 增值服务 ARPU | ¥1,500/年 | [¥600, ¥3,500] | 客户访谈 / 11_revenue_buildup |
| 7 | 数据 API Y5 收入 | ¥1.10 亿 | [¥6,000 万, ¥1.8 亿] | 11_revenue_buildup |
| 8 | 综合毛利率 | 73.9% | [66%, 80%] | 11_revenue_buildup |
| 9 | WACC | 14% | [11%, 18%] | DCF + Damodaran / 07_valuation_multimodel |
| 10 | 退出 PS 倍数 | 18× | [12×, 26×] | Bessemer Cloud / 07_valuation_multimodel |
| 11 | 目标 IRR | 40% | [30%, 55%] | VC method / 07_valuation_multimodel |
| 12 | 永续增长 g | 3.5% | [2.5%, 4.5%] | 07_valuation_multimodel |

---

## B. 12 套 Python 模型清单与运行说明

```bash
cd investmind/models/python_models
pip install -r requirements.txt    # numpy / scipy / pandas / matplotlib
python 01_market_sizing.py         # TAM/SAM/SOM
python 02_unit_economics.py        # LTV/CAC/Payback
python 03_user_roi_calculator.py   # 用户 ROI 22.5×
python 04_winrate_pnl_engine.py    # 排序引擎回测
python 05_signal_quality_backtest.py # 评分质量 AUC
python 06_growth_cohort.py         # 5 年增长 / Cohort
python 07_valuation_multimodel.py  # 多模型估值
python 08_funding_runway.py        # 现金 Runway / 三场景
python 09_user_profile_kelly.py    # Kelly + 三画像
python 10_compliance_risk_mc.py    # 合规风险 MC
python 11_revenue_buildup.py       # 5 年收入分层
python 12_sensitivity_tornado.py   # 敏感性 Tornado
```

每脚本输出：

* `outputs/<model_id>.json` — 关键数值（BP 文档 inline 引用）
* `outputs/<chart_name>.png` 与 `docs/images/charts/<chart_name>.png` — 图表

随机种子固定 `42`，N=200,000 蒙特卡洛 → 跨机可完全复现。

---

## C. 模型核心输出快照（截至 2026-04-30）

```
01_market_sizing
   TAM 共识中位     ¥57.27 亿  (90% CI [¥42.84 亿, ¥74.25 亿])
   SAM             ¥30.05 亿
   SOM Y5          ¥1.28 亿  (4.0% × SAM)

02_unit_economics
   Lite   LTV/CAC = 3.3×, Payback 7.4 mo
   Pro    LTV/CAC = 3.2×, Payback 10.5 mo
   Family LTV/CAC = 3.0×, Payback 18.1 mo
   加权   LTV/CAC = 3.2×, Payback 12.8 mo

03_user_roi_calculator
   ROI 倍数中位 22.5× (90% CI [9.9×, 49.3×])
   P(ROI > 5×) = 99.9%, P(ROI > 10×) = 94.8%
   IRR 增量金额 ≈ ¥4.5 万/年

04_winrate_pnl_engine
   InvestMind: MOIC 2.45×, IRR +22.0%, Win 75%, P/L 2.67
   vs Random:  +31.2pp IRR, +50pp Win, +1.56 P/L

05_signal_quality_backtest
   AUC 0.741, Brier 0.194, Top-5% 精度 77.2%

06_growth_cohort
   Y5 期末付费 129,364 用户, ARR ¥9.51 亿, 总营收 ¥10.88 亿(含其他)

07_valuation_multimodel
   DCF       ¥189.85 亿  (90% CI [¥115.85 亿, ¥313.07 亿])
   Comp      ¥142.62 亿  (90% CI [¥97.24 亿, ¥188.26 亿])
   VC method ¥215.98 亿  (90% CI [¥147.93 亿, ¥308.83 亿])
   加权 (DCF/Comp/VC = 30/40/30) = ¥178.80 亿

08_funding_runway
   Base   场景：M21 盈亏平衡, Y5 期末现金 ¥23.31 亿
   Bull   场景：M17 盈亏平衡, Y5 期末现金 ¥27.24 亿
   Stress 场景：M31 盈亏平衡, Y5 期末现金 ¥11.08 亿（无破产）

09_user_profile_kelly
   保守画像：18/200 可行机会, 平均仓位 5.0%
   平衡画像：74/200 可行机会, 平均仓位 10.9%
   进取画像：119/200 可行机会, 平均仓位 14.4%

10_compliance_risk_mc
   三大红色风险合并 ARR 受损中位 9.74%
   P(损失>15%) = 12.7%, P(损失>25%) = 0.2%

11_revenue_buildup
   Y5 总营收 ¥10.88 亿 (订阅 52% / 撮合 20% / API 10% / 增值 10% / 研报 8%)
   Y5 综合毛利率 73.9%

12_sensitivity_tornado
   Y5 ARR 最大杠杆：月留存 ±58%, 月新付费 ±42%, ARPU ±36%
   Y5 估值最大杠杆：退出 PS 倍数 ±63%, 月留存 ±58%
```

---

## D. 术语表 (Glossary)

| 缩写 | 全称 / 解释 |
|------|----------|
| ARR | Annual Recurring Revenue / 年化经常性收入 |
| MRR | Monthly Recurring Revenue / 月化经常性收入 |
| LTV | Lifetime Value / 客户终身价值 |
| CAC | Customer Acquisition Cost / 客户获取成本 |
| Payback | 回收期 = CAC / (ARPU × Gross Margin) |
| NRR | Net Revenue Retention / 净收入留存 |
| GRR | Gross Revenue Retention / 总收入留存 |
| MOIC | Multiple on Invested Capital / 投资资本倍数 |
| IRR | Internal Rate of Return / 内部收益率 |
| Sharpe | (E[r] - r_f) / σ |
| Sortino | (E[r] - r_f) / 下行 σ |
| TAM | Total Addressable Market / 总潜在市场 |
| SAM | Serviceable Available Market / 可服务市场 |
| SOM | Serviceable Obtainable Market / 可获得市场 |
| HNWI | High-Net-Worth Individual / 高净值个人（≥¥600 万可投资金融资产）|
| FA | Financial Advisor / 财务顾问 |
| AMAC | China Securities Investment Fund Industry Association / 中国证券投资基金业协会 |
| AUM | Assets Under Management / 管理资产 |
| PIPL | 个人信息保护法 |
| DSL | 数据安全法 |
| KG | Knowledge Graph / 知识图谱 |
| LLM | Large Language Model / 大语言模型 |
| RAG | Retrieval-Augmented Generation |
| OCR | Optical Character Recognition |
| MC | Monte Carlo / 蒙特卡洛仿真 |
| AUC | Area Under ROC Curve / 受试者特征曲线下面积 |
| Brier | Brier Score / 概率预测均方误差 |
| Kelly | Kelly Criterion / 凯利准则 |

---

## E. 参考文献 (References)

### 公开数据 / 监管文件

1. 招商银行 / 贝恩《2023 中国私人财富报告》（PWR 2024）
2. 麦肯锡《2024 中国财富管理报告》
3. 中国证券投资基金业协会 (AMAC) 私募登记季报 2025Q1
4. 清科研究 / Zero2IPO《2024 中国股权投资市场年报》
5. 艾瑞咨询《2024 中国 FinTech / WealthTech 行业研究》
6. 中国商务部《2024 年网络零售报告》
7. 《私募投资基金登记备案办法》2023-05
8. 《生成式人工智能服务管理暂行办法》2023-08
9. 《个人信息保护法》2021-11
10. 《证券投资咨询业务管理暂行办法》

### 行业 / 学术

11. AngelList Letters 2020-2024
12. CB Insights State of Venture 2024
13. Pitchbook NVCA Yearbook 2024
14. SaaS Capital 2024 Benchmark Report
15. ChartMogul SaaS Benchmark 2024
16. KeyBanc Capital Markets SaaS Survey 2024
17. Bessemer Cloud Index 2024
18. Damodaran NYU Stern Equity Risk Premium 2024
19. Stripe Atlas Founder Report 2024
20. Edward Thorp, "Beat the Market" (Kelly Criterion 早期实证)

### 上市公司 / 财报

21. Wind 信息 (300386.SZ) 财报 2023-2024
22. 同花顺 (300033.SZ) 财报 2023-2024
23. Topsoft (300624.SZ) 财报 2023-2024
24. 快手 (1024.HK) 2024 Q4 财报

### 数据合作伙伴

25. IT 桔子 / 鲸准 / 烯牛数据 / 36Kr 数据 公开口径

---

## F. 附件清单

| 附件 | 文件 | 用途 |
|------|------|------|
| A1 | `models/python_models/*.py` | 12 套可复现模型源码 |
| A2 | `models/python_models/outputs/*.json` | 12 个 JSON 输出 |
| A3 | `docs/images/charts/*.png` | 14 张数据图表 PNG（300 DPI）|
| A4 | `docs/images/investmind_*.png` | 4 张品牌大图（1792×1024）|
| A5 | 客户访谈纪要 | 内部资料，路演单独提供 |
| A6 | 主要合规材料 | 内部资料 |
| A7 | 顾问 LOI 与意向函 | 内部资料 |

---

## 文档结尾

**编制人**：CEO 林岚 · CFO 苏珊 · CTO 周轶恒

**审阅**：CCO 吕谨（合规）· CRO 孟一（投研）

**版本**：v1.0  ·  **日期**：2026-04-30

**机密标识**：`CONFIDENTIAL · 仅授权对象阅读`

---

> "**最好的预测早期投资的方式，是把它做成可复现的工程问题。**"
> —— 投智云 InvestMind AI · 2026
