"""公共工具：JSON 输出、置信区间、蒙特卡洛采样。"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import numpy as np

# Windows GBK 终端对 ¥ 等字符不友好 — 统一切到 utf-8。
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

OUT_DIR = Path(__file__).parent / "outputs"
OUT_DIR.mkdir(exist_ok=True, parents=True)


def write_json(name: str, data: dict[str, Any]) -> Path:
    p = OUT_DIR / f"{name}.json"
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=_default), encoding="utf-8")
    return p


def _default(o: Any) -> Any:
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(type(o))


def ci(samples: np.ndarray, level: float = 0.9) -> tuple[float, float, float]:
    """返回 (median, lower, upper) 的百分位。"""
    lo = (1 - level) / 2 * 100
    hi = 100 - lo
    return float(np.median(samples)), float(np.percentile(samples, lo)), float(np.percentile(samples, hi))


def fmt_cny(x: float) -> str:
    if x >= 1e9:
        return f"¥{x/1e9:.2f} B"
    if x >= 1e6:
        return f"¥{x/1e6:.2f} M"
    if x >= 1e3:
        return f"¥{x/1e3:.2f} K"
    return f"¥{x:.2f}"
