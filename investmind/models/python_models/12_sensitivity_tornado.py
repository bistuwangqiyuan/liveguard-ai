"""
12_sensitivity_tornado.py
=========================

Y5 ARR 与 C 轮估值对 12 个核心假设的敏感性 Tornado。

每个假设：
   - low / high 用各模型 ASSUMPTIONS 的 [p5, p95] 区间端点
   - 其余假设取中位
   - 计算「对 Y5 ARR」与「对 Y5 估值」的影响幅度

绘图按影响幅度从大到小排序（典型 Tornado）。
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from _common import BRAND, fmt_cny, save_chart, write_json


def y5_arr_under(assumption_overrides):
    base = {
        "willing_ratio":  0.11,
        "arpu_blended":   4400,
        "monthly_retention_blended": 0.969,
        "monthly_new_y5":  9000,
        "platform_takerate": 0.020,
        "value_add_per_user": 1500,
        "data_api_y5_revenue": 110_000_000,
        "subscription_growth": 1.0,
        "gross_margin": 0.74,
        "wacc": 0.14,
        "exit_PS": 18.0,
        "target_irr": 0.40,
    }
    a = {**base, **assumption_overrides}

    months_active_y5 = 12
    base_users_y5 = 129_364
    user_factor = (
        (a["willing_ratio"] / 0.11) ** 0.5
        * (a["monthly_retention_blended"] / 0.969) ** 24
        * (a["monthly_new_y5"] / 9000) ** 0.4
    )
    users = base_users_y5 * user_factor
    sub_arr = users * a["arpu_blended"] * a["subscription_growth"]

    api_arr = a["data_api_y5_revenue"]
    platform_arr = users * 50 * 1500 * a["platform_takerate"]
    value_arr = users * a["value_add_per_user"]

    total_arr = sub_arr + api_arr + platform_arr + value_arr
    valuation = a["exit_PS"] * total_arr * (1 + a["target_irr"]) ** -3 * 0.75

    return total_arr, valuation


SENS = [
    ("胜率提升 (β)",        "willing_ratio",         0.07,  0.16),
    ("加权 ARPU",            "arpu_blended",          3200,  6500),
    ("月留存（混合）",        "monthly_retention_blended", 0.94, 0.985),
    ("月新付费 Y5",           "monthly_new_y5",        5500, 12000),
    ("撮合 take-rate",       "platform_takerate",     0.012, 0.030),
    ("增值服务/用户/年",      "value_add_per_user",    600,   3500),
    ("数据 API Y5 收入",      "data_api_y5_revenue",   60_000_000, 180_000_000),
    ("订阅增速因子",          "subscription_growth",   0.7,   1.4),
    ("综合毛利率",            "gross_margin",          0.66,  0.80),
    ("WACC",                 "wacc",                  0.11,  0.18),
    ("退出 PS 倍数",          "exit_PS",               12.0,  26.0),
    ("目标 IRR",              "target_irr",            0.30,  0.55),
]

base_arr, base_val = y5_arr_under({})

print(f"── 基线 Y5 ARR = {fmt_cny(base_arr)}, 估值 = {fmt_cny(base_val)} ──")

rows = []
for label, key, lo, hi in SENS:
    arr_lo, val_lo = y5_arr_under({key: lo})
    arr_hi, val_hi = y5_arr_under({key: hi})
    arr_swing_pct = (max(arr_hi, arr_lo) - min(arr_hi, arr_lo)) / base_arr * 100
    val_swing_pct = (max(val_hi, val_lo) - min(val_hi, val_lo)) / base_val * 100
    rows.append({
        "label": label, "key": key, "low": lo, "high": hi,
        "arr_low": arr_lo, "arr_high": arr_hi,
        "val_low": val_lo, "val_high": val_hi,
        "arr_swing_pct": arr_swing_pct,
        "val_swing_pct": val_swing_pct,
    })

rows_arr = sorted(rows, key=lambda x: -x["arr_swing_pct"])
rows_val = sorted(rows, key=lambda x: -x["val_swing_pct"])

result = {
    "as_of": "2026-04-30",
    "base_y5_arr_CNY": float(base_arr),
    "base_y5_valuation_CNY": float(base_val),
    "sensitivities": rows_arr,
    "ranked_by_arr": [r["label"] for r in rows_arr],
    "ranked_by_val": [r["label"] for r in rows_val],
}

write_json("12_sensitivity_tornado", result)

fig, axs = plt.subplots(1, 2, figsize=(13.5, 5.6))

for ax, rows_target, base, title in [
    (axs[0], rows_arr, base_arr, "Y5 ARR 敏感性"),
    (axs[1], rows_val, base_val, "Y5 估值 敏感性"),
]:
    labels = [x["label"] for x in rows_target]
    if title.startswith("Y5 ARR"):
        lows = [x["arr_low"]  for x in rows_target]
        highs = [x["arr_high"] for x in rows_target]
    else:
        lows = [x["val_low"]  for x in rows_target]
        highs = [x["val_high"] for x in rows_target]

    ys = np.arange(len(labels))
    for i, (lo, hi) in enumerate(zip(lows, highs)):
        left = (min(lo, hi) - base) / base * 100
        right = (max(lo, hi) - base) / base * 100
        ax.barh(ys[i], right - left, left=left,
                color=BRAND["red"] if right < 0 else BRAND["teal"],
                alpha=0.85, edgecolor="white", height=0.62)
        ax.text(right + 0.5, ys[i], f"+{right:.0f}%", va="center",
                fontsize=8, color=BRAND["teal"])
        ax.text(left - 0.5, ys[i], f"{left:.0f}%", va="center", ha="right",
                fontsize=8, color=BRAND["red"])

    ax.invert_yaxis()
    ax.set_yticks(ys, labels, fontsize=10)
    ax.axvline(0, color=BRAND["ink"], lw=1)
    ax.set_xlabel(f"相对基线 {fmt_cny(base)} 的偏离 %")
    ax.set_title(title, pad=8)

fig.suptitle("§8.5 InvestMind 敏感性 Tornado · 12 项核心假设",
             fontsize=13, fontweight="bold", y=1.02, color=BRAND["ink"])
fig.tight_layout()
save_chart(fig, "fig_12_sensitivity")

print("✓ 12_sensitivity_tornado 完成")
