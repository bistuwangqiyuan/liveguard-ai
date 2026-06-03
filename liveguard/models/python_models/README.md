# 守播 LiveGuard · 可复现业务模型库 (v5.0)

商业计划书（`守播LiveGuard_商业计划书_v5.0.*`）中的**全部数字**均由本目录下 **19 个 Python 模型**计算，
可复现、可追溯到源头。随机种子固定 `seed=42`，蒙特卡洛 `N=200,000`。资产负债表勾稽差异 = 0 元。

v5.0 完全重构：**回归 AI 直播监控 SaaS 本体**，采用 2026 实时调研数据、2026 压缩估值倍数、真实阶段晋级率，
回报改为**多口径披露**（中位/期望/条件于成功/逐路径 IRR 分位）。已移除 v4 的创始人凯利与 Pre-Angel/四层货币化主口径。

- **唯一可信源**：`data_sources.py`（2026 市场 + 令117号 + 保守估值/闸门）
- **公共工具**：`_common.py`

| # | 脚本 | 目的 | 图表 |
|---|------|------|------|
| 01 | `01_market_sizing.py` | 监控 TAM/SAM/SOM 双口径 | `fig_01_*` |
| 02–03 | 单位经济 / 客户 ROI | LTV/CAC/回收期/ROI | `fig_02/03_*` |
| 04–06 | SLO / Erlang-C / 去重 | 技术与运营容量 | `fig_04/05/06_*` |
| 07–09 | 增长队列 / 定价 / 留存 | ARR/NRR/GRR | `fig_07/08/09_*` |
| 10 | `10_financial_projections.py` | 5 年三表（勾稽=0）| `fig_10_*` |
| 11 | `11_fundraising_dilution.py` | Cap Table（Seed→C）| `fig_11_*` |
| 12–14 | DCF / 可比 / 蒙特卡洛 | 估值（2026 压缩倍数）| `fig_12/13/14_*` |
| 15 | `15_sensitivity_analysis.py` | 龙卷风敏感性 | `fig_15_*` |
| 16 | `16_tech_benchmark.py` | 技术基准 | `fig_16_*` |
| 17 | `17_resource_requirements.py` | 自底向上资源 → 倒推 Seed 轮 | `fig_17_*` |
| 18 | `18_angel_returns.py` | Seed 条件回报四档 | `fig_18_*` |
| 19 | `19_success_probability.py` | 成功概率 + 多口径回报 | `fig_19_*` |

## 一键运行

```powershell
cd liveguard/models/python_models
pip install -r requirements.txt
python run_all.py
```

## 关键 headline（v5.0 · summary.json）

| 指标 | 值 |
|------|----|
| 监控 TAM / SAM | ¥160.8 亿 / ¥135.1 亿 |
| Y5 收入 / EBITDA / 净利 | ¥11.62 亿 / ¥1.12 亿 / ¥0.73 亿 |
| 累计融资 / 创始 C 轮后股比 | ¥6.5 亿 / 40.0% |
| 加权 EV / C 轮 Post | ¥34.3 亿 / ¥30 亿 |
| P(成功退出) / P(全损) | 2.72% / 77.9% |
| 中位 MOIC / 期望 MOIC | 0×（全损）/ 1.01× |
| 条件于成功 MOIC / IRR | 20.2× / 65% |
| 逐路径 IRR P90 | +17% |

## 文档生成（仅 DOCX）

```powershell
cd liveguard
./build.ps1
```

产出：`守播LiveGuard_商业计划书_v5.0.{md,docx}`
