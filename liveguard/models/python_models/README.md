# 守播 LiveGuard · 可复现业务模型库

商业计划书（`守播LiveGuard_商业计划书_v2.0.*`）中的**全部数字**均由本目录下 **16 个 Python 模型**计算，
可复现、可追溯到源头。每个脚本顶部列出 **ASSUMPTIONS** 与 **SOURCES**，
随机种子固定 `seed=42`，蒙特卡洛 `N=200,000`。

- **唯一可信源**：`data_sources.py` 集中全部关键假设与常量。修改任一参数 → 重跑 `run_all.py` → 全部 JSON + 图表 + BP 数字自动重算。
- **公共工具**：`_common.py`（品牌色板、中文字体、图表保存、CNY 格式化）。

| # | 脚本 | 目的 | 图表 |
|---|------|------|------|
| 01 | `01_market_sizing.py` | TAM / SAM / SOM 双口径交叉验证 | `fig_01_*` |
| 02 | `02_unit_economics.py` | 分客群 LTV / CAC / Payback | `fig_02_*` |
| 03 | `03_roi_merchant.py` | 客户 ROI 计算器 + 敏感性 | `fig_03_*` |
| 04 | `04_slo_latency_budget.py` | 通知管道端到端延迟 SLO | `fig_04_*` |
| 05 | `05_alerts_capacity_erlangc.py` | NOC 人工复核坐席 Erlang-C 容量 | `fig_05_*` |
| 06 | `06_dedup_suppression_sim.py` | 告警去重 / 抑制策略蒙特卡洛 | `fig_06_*` |
| 07 | `07_growth_cohort.py` | 5 年客户 / ARR 队列 | `fig_07_*` |
| 08 | `08_pricing_model.py` | 三档定价 + 价格弹性 + 加权 ARPU | `fig_08_*` |
| 09 | `09_cohort_retention.py` | NRR / GRR 留存瀑布 | `fig_09_*` |
| 10 | `10_financial_projections.py` | 5 年三大报表 + SaaS 比率（核心）| `fig_10_*` |
| 11 | `11_fundraising_dilution.py` | Cap Table 演进 + 投资人 IRR/MOIC | `fig_11_*` |
| 12 | `12_valuation_dcf.py` | 两阶段 DCF + Gordon 对照 | `fig_12_*` |
| 13 | `13_valuation_comparables.py` | 可比公司 EV/Sales、EV/EBITDA | `fig_13_*` |
| 14 | `14_monte_carlo_valuation.py` | 蒙特卡洛 + 多模型加权估值 | `fig_14_*` |
| 15 | `15_sensitivity_analysis.py` | 收入 / EV 龙卷风敏感性 | `fig_15_*` |
| 16 | `16_tech_benchmark.py` | 算法栈延迟 / KPI 雷达 / 成本曲线 | `fig_16_*` |

> 依赖关系：12 / 13 / 14 / 15 读取 `10_financial_projections.json`，因此用 `run_all.py` 按序运行。

## 一键运行

```powershell
cd liveguard/models/python_models
pip install -r requirements.txt
python run_all.py
```

- JSON 输出：`./outputs/*.json`（+ `summary.json` 汇总 headline）
- 图表输出：`../../docs/images/charts/*.png`（同时供 BP 文档引用）

## 关键 headline（seed=42）

| 指标 | 值 |
|------|----|
| TAM / SAM 共识 | ¥167 亿 / ¥143 亿 |
| Y5 收入 / EBITDA / 净利 | ¥27.95 亿 / ¥5.74 亿 / ¥3.88 亿 |
| Y5 Rule of 40 | 142 |
| 资产负债表勾稽差异 | 0.00 元（精确成立）|
| 创始团队 C 轮后持股 | 33.7% |
| 加权综合估值 EV | ≈ ¥135 亿（C 轮 Post ¥80 亿）|

## 文档生成

```powershell
cd liveguard
./build.ps1        # 模型 → 拼装 Markdown → DOCX → PDF
```

产出位于仓库根目录：`守播LiveGuard_商业计划书_v2.0.{md,docx,pdf}`。
