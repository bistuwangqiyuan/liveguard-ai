# 守播 LiveGuard · 可复现业务模型库 (v4.0)

商业计划书（`守播LiveGuard_商业计划书_v4.0.*`）中的**全部数字**均由本目录下 **21 个 Python 模型**计算，
可复现、可追溯到源头。随机种子固定 `seed=42`，蒙特卡洛 `N=200,000`。

v4.0 在 v3.0 基础上新增：**创始人王启源个人凯利仓位**（`21`）、**Pre-Angel Cap Table**、课余创始生存折扣。

- **唯一可信源**：`data_sources.py`（含 `FOUNDER`、`PRE_ANGEL`、`STAGE_GATES_FOUNDER`、`KELLY_*`）
- **公共工具**：`_common.py`

| # | 脚本 | 目的 | 图表 |
|---|------|------|------|
| 01–16 | （同 v3） | 市场/财务/估值/技术 | `fig_01`–`fig_16` |
| 17 | `17_resource_requirements.py` | 自底向上资源 → 倒推天使轮 | `fig_17_*` |
| 18 | `18_angel_returns.py` | 天使条件回报四档 | `fig_18_*` |
| 19 | `19_success_probability.py` | 天使阶段闸门 + 期望收益 | `fig_19_*` |
| 20 | `20_business_model_layers.py` | 四层货币化收入 | `fig_20_*` |
| **21** | **`21_personal_kelly_founder.py`** | **王启源胜率/盈亏比/凯利仓位** | **`fig_21_*`** |

## 一键运行

```powershell
cd liveguard/models/python_models
pip install -r requirements.txt
python run_all.py
```

## 关键 headline（v4.0 · summary.json）

| 指标 | 值 |
|------|----|
| **胜率 p / 盈亏比 b** | 27.9% / 129.3 |
| **凯利建议仓位** | 6.8%（≈ ¥68 万）|
| **创始人 P(成功) / P(全损)** | 2.6% / 72.1% |
| 天使期望 MOIC / IRR | 19.7× / 82% |
| 天使 P(成功) / P(全损) | 7.1% / 69.5% |
| 王启源 C 轮后合计股比 | 35.37% |
| Y5 收入 / 加权 EV | ¥45.27 亿 / ¥222 亿 |

## 文档生成（仅 DOCX）

```powershell
cd liveguard
./build.ps1
```

产出：`守播LiveGuard_商业计划书_v4.0.{md,docx}`
