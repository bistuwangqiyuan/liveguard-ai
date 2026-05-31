"""
assemble_md.py
==============

把 bp_build/bp_section_*.md 14 个分章节按顺序拼装为仓库根目录的
`守播LiveGuard_商业计划书_v2.0.md`（含标题页元信息 + 目录占位）。

图片路径以仓库根为基准（liveguard/docs/images/...），pandoc 渲染时
--resource-path 指向仓库根即可解析。
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).parent.parent.parent
BUILD = ROOT / "liveguard" / "bp_build"
OUT = ROOT / "守播LiveGuard_商业计划书_v2.0.md"

SECTIONS = [
    "bp_section_00_executive.md",
    "bp_section_01_company.md",
    "bp_section_02_market.md",
    "bp_section_03_competition.md",
    "bp_section_04_product.md",
    "bp_section_05_business.md",
    "bp_section_06_gtm.md",
    "bp_section_07_ops.md",
    "bp_section_08_finance.md",
    "bp_section_09_funding.md",
    "bp_section_10_risk.md",
    "bp_section_11_team.md",
    "bp_section_12_roadmap.md",
    "bp_section_99_appendix.md",
]

HEADER = """# 守播 LiveGuard AI · 视频直播监控智能体
## 商业计划书 (Business Plan) · v2.0
**编制日期**：2026 年 05 月 31 日

---

> **重要提示**：本文档为公司机密，仅授权对象阅读。所有数字均由 `liveguard/models/python_models/`
> 下 **16 个 Python 模型**计算可复现（seed=42，蒙特卡洛 N=200,000）；运行
> `python run_all.py` 一键重现，详见附录 B。

---

## 目录 (Table of Contents)

- 00 执行摘要
- 01 公司与产品概述
- 02 行业与市场分析
- 03 竞争分析与差异化定位
- 04 产品与技术方案
- 05 商业模式与定价策略
- 06 市场进入与营销战略
- 07 运营与组织计划
- 08 财务预测与单位经济
- 09 融资计划与估值
- 10 风险分析与对策
- 11 团队与治理结构
- 12 发展路线图与里程碑
- 99 附录

---

"""


def main() -> None:
    parts = [HEADER]
    for s in SECTIONS:
        text = (BUILD / s).read_text(encoding="utf-8").strip()
        parts.append(text)
        parts.append("\n\n---\n\n")
    OUT.write_text("\n".join(parts), encoding="utf-8")
    kb = OUT.stat().st_size / 1024
    print(f"✓ 拼装完成 → {OUT}  ({kb:.1f} KB, {len(SECTIONS)} 章)")


if __name__ == "__main__":
    main()
