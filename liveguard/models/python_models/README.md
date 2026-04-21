# LiveGuard · 业务建模脚本

所有数据均可复现、可追溯到源头。每个脚本顶部列出 **ASSUMPTIONS** 与 **SOURCES**，
并打印出带置信区间的最终数字。脚本均使用纯 Python + NumPy，可离线运行。

| # | 脚本 | 目的 |
|---|------|------|
| 01 | `market_sizing.py` | TAM / SAM / SOM（中国直播电商监控） |
| 02 | `unit_economics.py` | LTV / CAC / payback |
| 03 | `roi_merchant.py` | 商家侧 ROI（合规损失 + GMV 提升 - 订阅） |
| 04 | `slo_latency_budget.py` | 端到端延迟预算（Edge→Kafka→API→Notify） |
| 05 | `alerts_capacity_erlangc.py` | 人工审核坐席 Erlang-C 容量模型 |
| 06 | `dedup_suppression_sim.py` | 告警去重/抑制 蒙特卡洛模拟 |
| 07 | `growth_cohort.py` | 多月队列留存 / 净收入 / 预测 ARR |

## 运行
```powershell
cd liveguard/models/python_models
python 01_market_sizing.py
...
python 07_growth_cohort.py
```

所有脚本都会把关键输出写到 `./outputs/*.json`，便于商业计划书 / 控制台数据看板引用。
