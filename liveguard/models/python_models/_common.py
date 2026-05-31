"""
liveguard / models / _common.py
================================

公共工具（与 investmind 模型库保持一致的工程约定）：

  * 输出目录管理（outputs/ + docs/images/charts/）
  * JSON 序列化（处理 numpy 标量 / 数组）
  * 蒙特卡洛置信区间
  * 中文 / 货币 / 百分比格式化（亿 / 万）
  * matplotlib 主题（统一品牌色 + 中文字体，Windows 友好）

所有模型脚本必须 `from _common import ...`，确保数字、配色、字体跨全部脚本完全一致。
随机种子固定为 SEED=42、蒙特卡洛 N_SIM=200,000，任何读者重跑得到相同数字。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

# Windows GBK 终端对 ¥ / 中文不友好 — 统一切到 utf-8。
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

OUT_DIR = Path(__file__).parent / "outputs"
OUT_DIR.mkdir(exist_ok=True, parents=True)

# 图表与 BP 文档共享同一目录，便于 markdown 直接引用。
CHART_DIR = Path(__file__).parent.parent.parent / "docs" / "images" / "charts"
CHART_DIR.mkdir(exist_ok=True, parents=True)

# ── 守播 LiveGuard 品牌色板 ───────────────────────────────────────────────
BRAND = {
    "ink":     "#0B0F1A",   # 深空蓝（正文 / 标题）
    "blue":    "#1F6FFF",   # 电光蓝（主色）
    "teal":    "#00D4AA",   # 翠绿（增长 / 正向）
    "amber":   "#FFB020",   # 琥珀（警示）
    "red":     "#FF4D4F",   # 朱红（风险 / 离岗）
    "violet":  "#7C5CFF",   # 紫（次强调）
    "grey":    "#8A93A6",   # 中性灰
    "paper":   "#F7F8FB",
    "line":    "#1F2A44",
}

PALETTE = [
    BRAND["blue"],
    BRAND["teal"],
    BRAND["amber"],
    BRAND["violet"],
    BRAND["red"],
    BRAND["grey"],
]

SEED = 42
N_SIM = 200_000


def _resolve_cjk_font() -> list[str]:
    """优先使用 Windows 自带中文字体，回退到 Noto / 文泉驿。"""
    candidates = [
        "Microsoft YaHei",       # Windows 默认（本机可用）
        "微软雅黑",
        "Noto Sans CJK SC",
        "Source Han Sans SC",
        "WenQuanYi Micro Hei",
        "WenQuanYi Zen Hei",
        "SimHei",
        "DejaVu Sans",
    ]
    try:
        from matplotlib import font_manager
        installed = {f.name for f in font_manager.fontManager.ttflist}
        ordered = [c for c in candidates if c in installed]
        ordered += [c for c in candidates if c not in ordered]
        return ordered
    except Exception:
        return candidates


def setup_matplotlib() -> None:
    """统一主题：白底 + 品牌色 + 中文字体。"""
    mpl.rcParams.update({
        "font.sans-serif": _resolve_cjk_font(),
        "axes.unicode_minus": False,
        "axes.facecolor": "white",
        "figure.facecolor": "white",
        "axes.edgecolor": BRAND["line"],
        "axes.labelcolor": BRAND["ink"],
        "xtick.color": BRAND["ink"],
        "ytick.color": BRAND["ink"],
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.titlecolor": BRAND["ink"],
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": "#E2E6EE",
        "grid.linestyle": "--",
        "grid.linewidth": 0.6,
        "legend.frameon": False,
        "axes.prop_cycle": mpl.cycler(color=PALETTE),
        "figure.dpi": 140,
        "savefig.dpi": 220,
        "savefig.bbox": "tight",
    })


setup_matplotlib()


def write_json(name: str, data: dict[str, Any]) -> Path:
    p = OUT_DIR / f"{name}.json"
    p.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, default=_default),
        encoding="utf-8",
    )
    return p


def _default(o: Any) -> Any:
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (set, tuple)):
        return list(o)
    raise TypeError(type(o))


def ci(samples: np.ndarray, level: float = 0.9) -> tuple[float, float, float]:
    """返回 (median, lower, upper) 的百分位。"""
    lo = (1 - level) / 2 * 100
    hi = 100 - lo
    return (
        float(np.median(samples)),
        float(np.percentile(samples, lo)),
        float(np.percentile(samples, hi)),
    )


def fmt_cny(x: float) -> str:
    """中文金额简写：亿 / 万 / 元。"""
    if x >= 1e8:
        return f"¥{x/1e8:.2f} 亿"
    if x >= 1e4:
        return f"¥{x/1e4:.1f} 万"
    return f"¥{x:,.0f}"


def fmt_pct(x: float, digits: int = 1) -> str:
    return f"{x*100:.{digits}f}%"


def save_chart(fig: "plt.Figure", name: str) -> Path:
    """保存到 docs/images/charts/<name>.png + outputs/<name>.png 双份。"""
    p1 = CHART_DIR / f"{name}.png"
    fig.savefig(p1)
    p2 = OUT_DIR / f"{name}.png"
    fig.savefig(p2)
    plt.close(fig)
    return p1


def rng() -> np.random.Generator:
    return np.random.default_rng(SEED)
