# 投智云 InvestMind AI · 早期股权投资可行性研究与决策辅助平台

> **A SaaS website that auto-generates investment feasibility reports, ranks
> opportunities by win-rate × profit-loss ratio, and recommends
> profile-driven action plans for individual angel / PE investors in China.**

本仓库收录商业计划书所需的全部 **可复现 Python 模型**、**数据图表**、
**品牌视觉资产** 与 **文档生成管道**。

---

## 仓库结构

| 目录 | 内容 |
| --- | --- |
| `models/python_models/` | 12 套蒙特卡洛/解析模型，输出 `outputs/*.json` 供 BP 引用 |
| `docs/images/` | 4 张 AI 生成品牌大图 + Python 渲染数据图表 |
| `build/` | DOCX / PDF 生成管道脚本 + reference.docx + style.css |

---

## 一键运行

```bash
cd investmind
make models      # 运行 12 个 Python 模型，输出 JSON + 图表
make brand       # 引用预生成的品牌大图（已存放于 docs/images/）
make docx        # 渲染 DOCX
make pdf         # 渲染 PDF（Chrome headless）
make all         # 三件套全部产出
```

---

## 品牌主题

| 用途 | HEX |
| --- | --- |
| 主色（深空蓝） | `#0B0F1A` |
| 高亮（电光蓝） | `#1F6FFF` |
| 强调（翠绿） | `#00D4AA` |
| 警示（琥珀） | `#FFB020` |
| 风险（朱红） | `#FF4D4F` |

中文字体：思源黑 / 文泉驿微米黑（DOCX/PDF/图表全链路一致）。

---

## 数据可复现性约定

每个 Python 模型在文件头部声明：

1. **ASSUMPTIONS** — 关键假设（含三角分布的下界/众数/上界）
2. **SOURCES** — 公开数据源 / 行业报告 / 监管口径
3. 随机种子固定为 `42`，N=200,000 蒙特卡洛
4. 输出文件：`outputs/<model_id>.json` + `outputs/<model_id>.png`

任何读者都可以重跑得到相同数字。
