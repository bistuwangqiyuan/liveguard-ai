<!-- ===== File: 99-附录.md · v5.0 ===== -->

# §99 附录

## 附录 A · 数据源清单（可溯源）

### 市场与监管（2026 实时调研）

| 编号 | 来源 |
|------|------|
| S-101 | 市场监管总局发展研究中心 + 社科院《2025 直播电商行业发展白皮书》(新华社, 2026-03)：2025 GMV>5 万亿、店播占比>50%、直播相关企业 256.96 万家 |
| S-102 | 华经产业研究院《2026 中国直播电商行业市场深度分析》：2025 GMV 5.26 万亿(+16.5%)、渗透率 32.92% |
| S-103 | 网经社「电数宝」《年度中国直播电商 2025 市场数据报告》(2026-05)：2025 GMV 6.95 万亿(+30.4%)、用户 6.6 亿 |
| S-104 | 广州市商务局 / 艾瑞：2024 GMV≈5.8 万亿、2024–26 CAGR≈18%；国家统计局 2024 网络零售 15.52 万亿 |
| S-105 | 《中国网络视听发展研究报告(2024)》：2024 职业主播 3880 万人 |
| S-106 | 《直播电商监督管理办法》(市监总局 + 网信办令第117号, 2025-12-18 公布, **2026-02-01 施行**) |
| S-107 | 《互联网信息内容多渠道分发服务管理规定》(**2026-09-01 施行**) |
| S-108 | 《生成式人工智能服务管理暂行办法》(2023-08-15) + 算法备案制度 |
| S-109 | Frost & Sullivan / 艾瑞 中国电商 SaaS 工具支出占 GMV 比例研究 |

### 估值与晋级率

| 编号 | 来源 |
|------|------|
| S-110 | Crunchbase《Seed Deals 2026》/ Carta：Seed→A 晋级率 2023 年 24%、2024 年 16%；时间拉长至 >2 年 |
| S-111 | Aventis Advisors《SaaS Valuation Multiples 2015–2026》：2026-03 公募 SaaS EV/Rev 中位 3.4× |
| S-112 | SaaS Capital Index / BVP Emerging Cloud：2026 Q1 中位 6.4× / 8.0×；垂直 SaaS 4–8× ARR |
| S-113 | QuantPillar《2025–2026 Private Market Valuation Multiples》：B2B 中速 EV/EBITDA 8–15×、垂直 SaaS 10–18× |
| S-114 | Chronograph / Incisive Ventures：A→B、B→C 晋级率约 55–60%；幂律 5–10% 项目贡献多数回报 |
| S-115 | NVIDIA GTC 2024/2025 + 寒武纪/昇腾国产替代成本曲线综合：推理成本年降≈28% |

### 技术

| 编号 | 来源 |
|------|------|
| S-130 | RetinaFace / SCRFD 论文与开源 README |
| S-131 | YOLOv8 Ultralytics 文档 |
| S-132 | OSNet (Zhou et al., ICCV 2019) |
| S-133 | SlowFast (Feichtenhofer et al., ICCV 2019) |
| S-134 | VideoMAE (Tong et al., NeurIPS 2022) |
| S-135 | ECAPA-TDNN (Desplanques et al., Interspeech 2020) |
| S-136 | Silent-Face-Anti-Spoofing (MiniVision 开源) |

---

## 附录 B · 模型清单与复现指引

全部数字由 `liveguard/models/python_models/` 下 **19 个 Python 模型**计算，`seed=42`、`N=200,000`，结果可复现。

```bash
cd liveguard/models/python_models
pip install -r requirements.txt   # numpy / scipy / matplotlib
python run_all.py                 # 一键运行，输出 outputs/*.json + 图表，并写 summary.json
```

| 模型 | 输出 | 对应章节 |
|------|------|---------|
| 01_market_sizing | TAM/SAM/SOM 双口径 | §2 |
| 02_unit_economics | LTV/CAC/回收期 | §8 |
| 03_roi_merchant | 客户 ROI | §8 |
| 04_slo_latency_budget | 告警时延 SLO | §4 |
| 05_alerts_capacity_erlangc | NOC 坐席容量 | §7 |
| 06_dedup_suppression_sim | 告警去重/抑制 | §7 |
| 07_growth_cohort | 客户/ARR 队列 | §6 |
| 08_pricing_model | 定价与弹性 | §5 |
| 09_cohort_retention | NRR/GRR | §8 |
| 10_financial_projections | 5 年三表（勾稽=0）| §9 |
| 11_fundraising_dilution | Cap Table（Seed→C）| §10 |
| 12_valuation_dcf | 两阶段 DCF | §11 |
| 13_valuation_comparables | 可比公司 | §11 |
| 14_monte_carlo_valuation | 加权 EV | §11 |
| 15_sensitivity_analysis | 龙卷风敏感性 | §9 |
| 16_tech_benchmark | 技术基准 | §4 |
| 17_resource_requirements | 创立资源倒推 | §7 |
| 18_angel_returns | Seed 条件回报 | §12 |
| 19_success_probability | 成功概率 + 多口径回报 | §12 |

---

## 附录 C · 回报口径与方法学说明

- **中位 MOIC/IRR**：蒙特卡洛全样本中位数（本项目 ≈ 全损），代表"最可能的单笔结局"。
- **概率加权期望 MOIC**：全样本均值，含 P(全损)；由右尾（成功退出）驱动。
- **期望逐路径 IRR**：对每条蒙特卡洛路径先按其退出年限年化 IRR（全损=−100%），再取期望——避免用 `E[MOIC]^(1/n)−1` 夸大。
- **条件于成功 MOIC/IRR**：仅在成功退出路径上的平均值（本项目 ≈20× / 65%）。
- **逐路径 IRR 分位**：P25/P50/P75/P90/P95/P99，完整刻画分布形状。

> **免责声明**：本文档全部回报数字为基于公开数据与明示假设的情景建模结果，**不构成任何回报承诺或投资建议**。
> 早期股权投资具有本金全损风险（本项目主案 P(全损)≈77.9%）。

---

**文档版本：v5.0（2026-06-01）** ｜ 复现：`python run_all.py` ｜ 联系：bd@liveguard.ai
