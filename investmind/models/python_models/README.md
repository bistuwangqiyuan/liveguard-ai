# InvestMind · 业务建模脚本（12 套全部可复现）

> 所有数字均可复现、可追溯到源头。每个脚本顶部列出 **ASSUMPTIONS** 与
> **SOURCES**，并打印带 90% 置信区间的最终数字。脚本均使用纯
> Python + NumPy/SciPy/pandas/matplotlib，可离线运行。

| # | 脚本 | 目的 |
|---|------|------|
| 01 | `01_market_sizing.py` | TAM / SAM / SOM —— 中国早期股权投资可行性研究 SaaS |
| 02 | `02_unit_economics.py` | LTV / CAC / Payback（散户 / 持证个人 / Family Office） |
| 03 | `03_user_roi_calculator.py` | 个人投资者年化 IRR 提升 + 决策时间节省 |
| 04 | `04_winrate_pnl_engine.py` | 1,000 笔早期投资蒙特卡洛回测 → 引擎 Sharpe 提升 |
| 05 | `05_signal_quality_backtest.py` | 可行性评分 vs 真实回报：AUC / Brier / Calibration |
| 06 | `06_growth_cohort.py` | Cohort 留存 / Net Revenue / 5 年 ARR |
| 07 | `07_valuation_multimodel.py` | DCF + Comparables + VC method 三模型加权估值 |
| 08 | `08_funding_runway.py` | 5 年融资节奏 + 现金 Runway + 敏感性 |
| 09 | `09_user_profile_kelly.py` | 三类画像 × Kelly 配比建议 |
| 10 | `10_compliance_risk_mc.py` | 监管 / 合规 / 信息披露风险蒙特卡洛 |
| 11 | `11_revenue_buildup.py` | 5 年收入分层（订阅 / API / 数据 / 平台分成） |
| 12 | `12_sensitivity_tornado.py` | 估值 / ARR 对 12 个核心假设的敏感性 |

## 运行

```bash
cd investmind/models/python_models
pip install -r requirements.txt
python 01_market_sizing.py
# ...
python 12_sensitivity_tornado.py
```

每个脚本会写入：

* `outputs/<id>.json` — 关键数值，BP 文档直接引用
* `outputs/<id>.png` 与 `docs/images/charts/<chart_name>.png` — 图表

## 共同约定

* 随机种子 `SEED = 42`，N=200,000
* 三角分布：`(low, mode, high)` 全部来自公开报告区间
* 货币单位：人民币 `¥`，美元仅作国际可比时转换
* 时间口径：BP 编制基准日 2026-04-30
