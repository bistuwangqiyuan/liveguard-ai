"""
assemble_md.py  ·  守播 LiveGuard v4.0
======================================

把 bp_build/bp4_section_*.md 17 个分章节拼装为仓库根目录的
`守播LiveGuard_商业计划书_v4.0.md`。
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
OUT = ROOT / "守播LiveGuard_商业计划书_v4.0.md"

SECTIONS = [
    "bp4_section_00_executive.md",
    "bp4_section_01_business_model.md",
    "bp4_section_02_market.md",
    "bp4_section_03_competition.md",
    "bp4_section_04_product.md",
    "bp4_section_05_pricing_unit.md",
    "bp4_section_06_gtm.md",
    "bp4_section_07_ops.md",
    "bp4_section_08_resources.md",
    "bp4_section_09_finance.md",
    "bp4_section_10_valuation.md",
    "bp4_section_11_success_probability.md",
    "bp4_section_12_funding.md",
    "bp4_section_13_risk.md",
    "bp4_section_14_team.md",
    "bp4_section_15_roadmap.md",
    "bp4_section_99_appendix.md",
]

HEADER = """# 守播 LiveGuard AI · 直播经济实时可信与风控中台
## 商业计划书 (Business Plan) · v4.0 — 创始人凯利仓位 + 天使 IRR
**编制日期**：2026 年 06 月 01 日

---

> **重要提示**：本文档为公司机密。v4.0 以**创始人王启源个人决策**（胜率 × 盈亏比 × 凯利仓位）为第一屏，
> 第二屏保留天使 IRR。全部数字由 `liveguard/models/python_models/` 下 **21 个 Python 模型**可复现
>（seed=42，N=200,000）；运行 `python run_all.py` 一键重现，详见附录 B。
>
> **早期创业/股权投资具有高风险**：创始人课余情景 P(全损)≈72.1%、天使 P(全损)≈69.5%。
> 期望收益为概率加权模型结果，不构成回报承诺。

---

## 目录 (Table of Contents)

- 00 执行摘要（王启源凯利仓位 + 天使 IRR 双视角）
- 01 商业模式与价值链机会
- 02 行业与市场分析
- 03 竞争分析
- 04 产品与技术
- 05 定价与单位经济
- 06 GTM
- 07 运营与组织
- 08 创立所需资源（个人 vs 公司资本）
- 09 财务预测
- 10 估值
- 11 成功概率与预期收益（天使 + §11b 创始人凯利）
- 12 融资与 Cap Table（含 Pre-Angel）
- 13 风险分析
- 14 团队（王启源）
- 15 路线图
- 99 附录

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
