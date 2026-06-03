"""
assemble_md.py  ·  守播 LiveGuard v5.0
======================================

把 bp_build/bp5_section_*.md 17 个分章节拼装为仓库根目录的
`守播LiveGuard_商业计划书_v5.0.md`。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).parent.parent.parent
BUILD = ROOT / "liveguard" / "bp_build"
OUT = ROOT / "守播LiveGuard_商业计划书_v5.0.md"

SECTIONS = [
    "bp5_section_00_executive.md",
    "bp5_section_01_company_product.md",
    "bp5_section_02_market.md",
    "bp5_section_03_competition.md",
    "bp5_section_04_product_tech.md",
    "bp5_section_05_business_model.md",
    "bp5_section_06_gtm.md",
    "bp5_section_07_operations.md",
    "bp5_section_08_unit_economics.md",
    "bp5_section_09_finance.md",
    "bp5_section_10_funding.md",
    "bp5_section_11_valuation.md",
    "bp5_section_12_success_returns.md",
    "bp5_section_13_risk.md",
    "bp5_section_14_team.md",
    "bp5_section_15_roadmap.md",
    "bp5_section_99_appendix.md",
]

HEADER = """# 守播 LiveGuard AI · 直播间 AI 实时合规监控 SaaS
## 商业计划书 (Business Plan) · v5.0 — 机构标准版（完全重构）
**编制日期**：2026 年 06 月 01 日

---

> **重要提示**：本文档为公司机密，面向机构投资人。v5.0 回归"AI 直播监控本体"，采用 2026 实时调研数据、
> 2026 压缩估值倍数与真实阶段晋级率。全部数字由 `liveguard/models/python_models/` 下 **19 个 Python 模型**可复现
>（seed=42，N=200,000）；运行 `python run_all.py` 一键重现，详见附录 B。资产负债表勾稽差异 = 0 元。
>
> **早期股权投资具有高风险**：主案 P(本金全损)≈77.9%。回报以多口径（中位/期望/条件于成功/逐路径 IRR 分位）披露，
> 均为情景建模结果，**不构成回报承诺或投资建议**。

---

## 目录 (Table of Contents)

- 00 执行摘要
- 01 公司与产品概述
- 02 行业与市场分析
- 03 竞争分析与差异化定位
- 04 产品与技术
- 05 商业模式与定价
- 06 进入市场策略 (GTM)
- 07 运营、组织与创立资源
- 08 单位经济
- 09 财务预测
- 10 融资与 Cap Table
- 11 估值（2026 压缩倍数）
- 12 成功概率与投资回报（多口径）
- 13 风险分析
- 14 团队与组织
- 15 路线图
- 99 附录（数据源 / 模型 / 方法学）

---

"""


def check_images(text: str) -> int:
    """Return count of missing image paths."""
    root = ROOT
    missing = 0
    for m in re.finditer(r"!\[[^\]]*\]\(([^)]+)\)", text):
        p = m.group(1).split("?")[0]
        if not (root / p).exists():
            print(f"  !! 缺失图片: {p}")
            missing += 1
    return missing


def main() -> None:
    parts = [HEADER]
    for s in SECTIONS:
        text = (BUILD / s).read_text(encoding="utf-8").strip()
        parts.append(text)
        parts.append("\n\n---\n\n")
    body = "\n".join(parts)
    OUT.write_text(body, encoding="utf-8")
    kb = OUT.stat().st_size / 1024
    miss = check_images(body)
    print(f"✓ 拼装完成 → {OUT}  ({kb:.1f} KB, {len(SECTIONS)} 章, 缺失图片 {miss})")
    if miss:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
