<!-- ===== File: 99-附录.md ===== -->

# 附录 (Appendix)

> 数据源、模型说明、术语表、引用清单与方法论披露。

---

## A. 数据源清单（Data Sources）

> 全部参数集中在 `liveguard/models/python_models/data_sources.py`（唯一可信源）；每条有明确出处。

| 数据项 | 数值 | 来源 | 编号 |
|--------|-----|------|------|
| 中国直播电商 GMV 2024 | 5.30 万亿元 | 商务部 + 艾瑞 | S-001/002 |
| 中国直播电商 CAGR 2024–29 | 13% | 艾瑞 / 麦肯锡 | S-002/020 |
| 全球直播电商 CAGR | 20.5% | Coresight / eMarketer | S-018/019 |
| 职业主播 / 商家自播 | 178 万 / 160 万 | 人社部 / 艾瑞 | S-005/002 |
| 工具支出占 GMV / 监控占比 | 1.2% / 25% | Frost & Sullivan / 测算 | S-015 |
| 四层货币化 TAM 放大系数 | ×3.80 | 内部测算（监控+风控+数据+保险）| — |
| 加权年 ARPU（核心 SaaS）| ¥15,969 | 70/25/5 定价结构 | — |
| 稳态混合毛利率 | 80% | 四层结构内生 | — |
| AI 推理成本年降 | 28% | NVIDIA + 寒武纪/昇腾 | S-094 |
| WACC / 退出 EV/EBITDA / EV/Sales 中位 | 14% / 18× / 4.6× | CAPM / 可比中位 | — |
| 阶段晋级与早期回报分布 | — | CB Insights / 红杉 / Correlation Ventures | S-040/041 |
| 天使轮 / 入场估值 | ¥1,000 万 / Post ¥5,000 万 | §8 资源倒推 | — |

---

## B. Python 模型库说明（v3.0，共 20 模型）

> 详见 `liveguard/models/python_models/README.md` 与各脚本头部 docstring。
> 全部模型种子固定 `seed=42`，蒙特卡洛 `N=200,000`。

| 文件 | 用途 | 关键输出 |
|------|------|---------|
| `data_sources.py` | 集中参数与常量（唯一可信源）| — |
| `01_market_sizing.py` | TAM/SAM/SOM 双口径 + 四层放大 | `fig_01_*` |
| `02_unit_economics.py` | 分客群 LTV/CAC/Payback | `fig_02_*` |
| `03_roi_merchant.py` | 客户 ROI 计算器 | `fig_03_*` |
| `04_slo_latency_budget.py` | 通知管道延迟 SLO | `fig_04_*` |
| `05_alerts_capacity_erlangc.py` | NOC 坐席 Erlang-C | `fig_05_*` |
| `06_dedup_suppression_sim.py` | 告警去重/抑制 | `fig_06_*` |
| `07_growth_cohort.py` | 客户/ARR 队列 | `fig_07_*` |
| `08_pricing_model.py` | 三档定价 + 弹性 | `fig_08_*` |
| `09_cohort_retention.py` | NRR/GRR（升至 145%）| `fig_09_*` |
| `10_financial_projections.py` | 5 年三大报表（收入=四层）| `fig_10_*` |
| `11_fundraising_dilution.py` | Cap Table（Angel→C 全稀释）| `fig_11_*` |
| `12_valuation_dcf.py` | 两阶段 DCF | `fig_12_*` |
| `13_valuation_comparables.py` | 可比公司估值 | `fig_13_*` |
| `14_monte_carlo_valuation.py` | 蒙特卡洛 + 加权 EV | `fig_14_*` |
| `15_sensitivity_analysis.py` | 龙卷风敏感性 | `fig_15_*` |
| `16_tech_benchmark.py` | 技术基准/延迟/成本 | `fig_16_*` |
| **`17_resource_requirements.py`** | 自底向上资源 → 倒推天使轮 | `fig_17_*` |
| **`18_angel_returns.py`** | 天使条件回报四档 | `fig_18_*` |
| **`19_success_probability.py`** | 阶段闸门生存 + P(成功) + 期望收益 | `fig_19_*` |
| **`20_business_model_layers.py`** | 四层货币化收入 | `fig_20_*` |
| `run_all.py` | 一键全跑 | `summary.json` |

### 一键复现

```bash
cd liveguard/models/python_models
pip install -r requirements.txt
python run_all.py
# 输出 JSON 位于 outputs/；图表位于 ../../docs/images/charts/
```

> 修改 `data_sources.py` 任一参数 → 重跑 `run_all.py` → 整个 BP 数字自动重算。
> `summary.json` 头条 = 天使 5 年期望 IRR / P(成功) / 期望 MOIC。

---

## C. 关键结论速查（来自 `summary.json`）

| 指标 | 值 |
|------|---:|
| 天使投资 / 入场估值 | ¥1,000 万 / Post ¥5,000 万（20%）|
| 天使全稀释后股比 | 8.84% |
| 天使期望 MOIC / 5 年 IRR | 19.7× / 82% |
| P(成功退出) / P(本金全损) | 7.1% / 69.5% |
| 条件于成功 MOIC | 217× |
| 累计融资 / 创始团队 C 轮后 | ¥20.6 亿 / 35.4% |
| Y5 总收入 / 扩展层占比 | ¥45.27 亿 / 38.3% |
| Y5 EBITDA / 净利 / Rule of 40 | ¥10.20 亿 / ¥6.99 亿 / 164 |
| 资产负债表勾稽差异 | 0.00 元 |
| 加权综合 EV / C 轮 Post | ¥222 亿 / ¥120 亿 |

---

## D. 术语表（Glossary）

| 术语 | 释义 |
|------|------|
| ARR / ARPU | 年度循环收入 / 单客户平均收入 |
| CAC / LTV | 获客成本 / 客户终身价值 |
| MOIC / IRR | 投入资本回报倍数 / 内部收益率 |
| NRR / GRR | 净收入留存 / 总收入留存 |
| DCF / EV | 现金流折现 / 企业价值 |
| FAR / FNR | 误报率 / 漏报率 |
| ESOP | 员工持股池 |
| RegTech | 监管科技 |
| Re-ID | 行人重识别 |
| TAM/SAM/SOM | 总可达/可服务/可获得市场 |
| 阶段闸门生存模型 | Stage-gate survival：逐级晋级概率连乘估计成功率 |

---

## E. 引用清单（References）

1. CNNIC，《第 53 次中国互联网络发展状况统计报告》，2024
2. 商务部，《2024 年中国电子商务报告》，2024
3. 艾瑞咨询，《2024 中国直播电商行业研究报告》，2024
4. 克劳锐，《2024 中国 MCN 行业发展白皮书》，2024
5. NVIDIA, GTC 2024/2025 Keynote on Inference Cost Reduction
6. Salesforce / Datadog, Annual Reports (FY24/FY25)
7. 商汤、旷视、依图 公开年报/招股书；微盟、有赞 公开年报
8. Bessemer Cloud Index 2024；OpenView SaaS Benchmarks 2024
9. CB Insights, *Venture Capital Funnel / Stage Graduation Rates*, 2024
10. Correlation Ventures / AngelList, *Early-Stage Return Distribution Studies*
11. PIPL 全文及配套；《生成式人工智能服务管理暂行办法》，2023.07
12. OSNet (ICCV 2019)、SlowFast (ICCV 2019)、VideoMAE (NeurIPS 2022)、ECAPA-TDNN (Interspeech 2020)

---

## F. 风险披露与免责声明

本商业计划书包含前瞻性陈述，基于公司当前对市场、技术、监管的理解与假设。**早期股权投资具有高风险，本金可能全部损失**（本文已用阶段闸门生存模型量化为 P≈69.5%）。所述期望收益为概率加权模型结果，不构成任何回报承诺。本文档仅用于潜在投资人评估，不构成证券发行或投资建议；引用或转发需经本公司书面同意。

---

## G. 联系方式

- **BD / 投资人**：bd@liveguard.ai ｜ **媒体**：pr@liveguard.ai ｜ **招聘**：hr@liveguard.ai
- **官网**：https://liveguard.ai（拟）｜ **地址**：北京海淀中关村 / 杭州滨江高新园

---

> **文档版本**：v3.0（2026-06-01）
> **数据可复现性**：所有数字均由 `liveguard/models/python_models/` 下 **20 个 Python 模型**计算，运行 `python run_all.py` 重现（seed=42, N=200,000）。
