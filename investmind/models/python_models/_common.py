"""
investmind / models / _common.py
=================================

公共工具：
  * 输出目录管理（outputs/）
  * JSON 序列化（处理 numpy 标量 / 数组）
  * 蒙特卡洛置信区间
  * 中文 / 货币格式化
  * matplotlib 主题（统一品牌色 + 中文字体）

任何模型脚本都必须 `from _common import ...`，
确保数字、配色、字体跨 12 个脚本完全一致。
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

OUT_DIR = Path(__file__).parent / "outputs"
OUT_DIR.mkdir(exist_ok=True, parents=True)

CHART_DIR = Path(__file__).parent.parent.parent / "docs" / "images" / "charts"
CHART_DIR.mkdir(exist_ok=True, parents=True)

BRAND = {
    "ink":     "#0B0F1A",
    "blue":    "#1F6FFF",
    "teal":    "#00D4AA",
    "amber":   "#FFB020",
    "red":     "#FF4D4F",
    "violet":  "#7C5CFF",
    "grey":    "#8A93A6",
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


def setup_matplotlib() -> None:
    """统一主题：白底 + 品牌色 + 中文字体（Noto / 文泉驿 / 系统级 fallback）。"""
    mpl.rcParams.update({
        "font.sans-serif": [
            "Noto Sans CJK SC",
            "Noto Sans CJK JP",
            "WenQuanYi Micro Hei",
            "WenQuanYi Zen Hei",
            "Source Han Sans SC",
            "DejaVu Sans",
        ],
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
    """中文金额简写：B / M / K → 亿 / 百万 / 千。"""
    if x >= 1e8:
        return f"¥{x/1e8:.2f} 亿"
    if x >= 1e4:
        return f"¥{x/1e4:.1f} 万"
    return f"¥{x:,.0f}"


def fmt_pct(x: float, digits: int = 1) -> str:
    return f"{x*100:.{digits}f}%"


def save_chart(fig: plt.Figure, name: str) -> Path:
    """保存到 docs/images/charts/<name>.png + outputs/<name>.png 双份。"""
    p1 = CHART_DIR / f"{name}.png"
    fig.savefig(p1)
    p2 = OUT_DIR / f"{name}.png"
    fig.savefig(p2)
    plt.close(fig)
    return p1


SEED = 42
N_SIM = 200_000


def rng() -> np.random.Generator:
    return np.random.default_rng(SEED)
