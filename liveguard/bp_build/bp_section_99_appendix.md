<!-- ===== File: 99-附录.md ===== -->

# 附录 (Appendix)

> 数据源、模型说明、术语表、引用清单与方法论披露。

---

## A. 数据源清单（Data Sources）

> 全部参数集中在 `liveguard/models/python_models/data_sources.py`；每条参数有明确出处，便于审计。

| 数据项 | 数值 | 来源 | 编号 |
|--------|-----|------|------|
| 中国直播电商 GMV 2024 | 5.30 万亿元 | 商务部 + 艾瑞咨询 | S-001/002 |
| 中国直播电商 GMV CAGR 2024–29 | 13% | 艾瑞 / 麦肯锡交叉验证 | S-002/020 |
| 全球直播电商 CAGR 2024–29 | 20.5% | Coresight / eMarketer | S-018/019 |
| 职业主播 | 178 万 | 人社部 2024 新职业名录 | S-005 |
| 商家自播账号 | 160 万 | 艾瑞咨询 | S-002 |
| MCN 机构数 | 4.2 万家 | 克劳锐白皮书 | S-008 |
| 工具支出占 GMV 比 | 1.2% | Frost & Sullivan | S-015 |
| 监控工具占工具支出比 | 25% | 行业访谈 + 公司测算 | — |
| AI 推理成本年降 | 28% | NVIDIA + 寒武纪/昇腾 | S-094 |
| 加权年 ARPU | ¥15,969 | 70/25/5 定价结构推导 | — |
| 稳态毛利率 | 78% | SaaS 行业 P75 + 公司目标 | — |
| WACC | 14% | CAPM + 早期 SaaS 风险溢价 | — |
| 退出 EV/EBITDA | 18× | Salesforce/Datadog 历史中位 | — |
| EV/Sales 中位 | 4.6× | 12 家可比公司中位 | — |

---

## B. Python 模型库说明（Models）

> 详见 `liveguard/models/python_models/README.md` 与各脚本头部 docstring。
> 全部模型种子固定 `seed=42`，蒙特卡洛 `N=200,000`。

| 文件 | 用途 | 关键输出 |
|------|------|---------|
| `_common.py` | 公共工具（品牌色、中文字体、图表保存、CNY 格式化）| — |
| `data_sources.py` | 集中参数与常量（唯一可信源）| — |
| `01_market_sizing.py` | TAM/SAM/SOM 双口径 | `fig_01_*.png` |
| `02_unit_economics.py` | 分客群 LTV/CAC/Payback | `fig_02_*.png` |
| `03_roi_merchant.py` | 客户 ROI 计算器 | `fig_03_*.png` |
| `04_slo_latency_budget.py` | 通知管道延迟 SLO | `fig_04_*.png` |
| `05_alerts_capacity_erlangc.py` | NOC 坐席 Erlang-C 容量 | `fig_05_*.png` |
| `06_dedup_suppression_sim.py` | 告警去重/抑制模拟 | `fig_06_*.png` |
| `07_growth_cohort.py` | 5 年客户/ARR 队列 | `fig_07_*.png` |
| `08_pricing_model.py` | 三档定价 + 价格弹性 | `fig_08_*.png` |
| `09_cohort_retention.py` | NRR/GRR 留存瀑布 | `fig_09_*.png` |
| `10_financial_projections.py` | 5 年三大报表 + SaaS 比率 | `fig_10_*.png` |
| `11_fundraising_dilution.py` | Cap Table 演进 + IRR | `fig_11_*.png` |
| `12_valuation_dcf.py` | 两阶段 DCF | `fig_12_*.png` |
| `13_valuation_comparables.py` | 可比公司估值 | `fig_13_*.png` |
| `14_monte_carlo_valuation.py` | 蒙特卡洛 + 加权估值 | `fig_14_*.png` |
| `15_sensitivity_analysis.py` | 龙卷风敏感性 | `fig_15_*.png` |
| `16_tech_benchmark.py` | 技术基准/延迟/成本 | `fig_16_*.png` |
| `run_all.py` | 一键全跑 | `summary.json` |

### 一键复现

```bash
cd liveguard/models/python_models
pip install -r requirements.txt
python run_all.py
# 输出 JSON 位于 outputs/；图表位于 ../../docs/images/charts/
```

修改 `data_sources.py` 中任一参数 → 重跑 `run_all.py` → 整个 BP 数字自动重算。

---

## C. 术语表（Glossary）

| 术语 | 全称 / 释义 |
|------|------------|
| ARR | Annual Recurring Revenue 年度循环收入 |
| ARPU | Average Revenue Per User 单客户平均收入 |
| CAC | Customer Acquisition Cost 获客成本 |
| CAGR | Compound Annual Growth Rate 复合年增长率 |
| DCF | Discounted Cash Flow 现金流折现 |
| EBITDA | 息税折旧摊销前利润 |
| ESOP | Employee Stock Option Pool 员工持股池 |
| EV | Enterprise Value 企业价值 |
| FAR / FNR | 误报率 / 漏报率 |
| GMV | Gross Merchandise Volume 商品交易总额 |
| GRR / NRR | 总收入留存 / 净收入留存 |
| LTV | Lifetime Value 客户终身价值 |
| MCN | Multi-Channel Network 直播机构 |
| NOC | Network Operations Center 网络运营中心 |
| PIPL | Personal Information Protection Law 个人信息保护法 |
| Re-ID | Re-Identification 重识别 |
| SaaS | Software as a Service |
| TAM/SAM/SOM | 总可达 / 可服务 / 可获得市场 |
| VAD | Voice Activity Detection 语音活动检测 |
| WACC | 加权平均资本成本 |

---

## D. 引用清单（References）

1. 中国互联网络信息中心（CNNIC），《第 53 次中国互联网络发展状况统计报告》，2024
2. 商务部，《2024 年中国电子商务报告》，2024
3. 艾瑞咨询，《2024 中国直播电商行业研究报告》，2024
4. 克劳锐，《2024 中国 MCN 行业发展白皮书》，2024
5. 中国信通院，《人工智能白皮书 2024》，2024
6. NVIDIA, GTC 2024 / 2025 Keynote on Inference Cost Reduction
7. Salesforce / Datadog, Annual Reports (FY24/FY25)
8. 商汤科技、旷视科技、依图科技 公开年报 / 招股书
9. 微盟集团、有赞，公开年报
10. Bessemer Cloud Index 2024；KeyBanc SaaS Survey 2024；OpenView SaaS Benchmarks 2024
11. PIPL 全文及配套司法解释，2021–2024
12. 国家互联网信息办公室，《生成式人工智能服务管理暂行办法》，2023.07
13. OSNet (ICCV 2019)、SlowFast (ICCV 2019)、VideoMAE (NeurIPS 2022)、ECAPA-TDNN (Interspeech 2020)

---

## E. 风险披露与免责声明

本商业计划书包含前瞻性陈述，基于公司当前对市场、技术、监管的理解与假设。实际经营结果可能受宏观经济、政策、技术演进、竞争等多种因素影响而显著偏离。本文档仅用于潜在投资人评估，不构成证券发行或投资建议；任何引用或转发需获得本公司书面同意。

---

## F. 联系方式

- **BD / 投资人**：bd@liveguard.ai ｜ **媒体**：pr@liveguard.ai ｜ **招聘**：hr@liveguard.ai
- **官网**：https://liveguard.ai（拟）｜ **地址**：北京海淀中关村 / 杭州滨江高新园

---

> **文档版本**：v2.0（2026-05-31）
> **数据可复现性**：所有数字均由 `liveguard/models/python_models/` 下 16 个 Python 模型计算，运行 `python run_all.py` 重现（seed=42, N=200,000）。
