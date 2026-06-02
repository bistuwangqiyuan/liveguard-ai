"""
20_business_model_layers.py
===========================

四层货币化收入结构（守播 LiveGuard v3 商业模式重构核心）。对应 BP §1 商业模式重构 / §5。

把"离岗监控"从一个功能升级为有网络效应 + 数据护城河的公司，四层叠加货币化：
  ① 核心监控 SaaS      —— 离岗/替身/合规实时监控（监管刚需，低 CAC 快速获客）
  ② 风控 OS 加购        —— 话术/极限词/价格/商品/刷单造假风控（ACV 跃升、更黏）
  ③ 可信数据网络 / API  —— 可信主播认证 + 欺诈名单 + 基准数据 + 平台/ISV API 调用（双边网络效应）
  ④ 合规履约保险分润 / RegTech —— 与保险公司联合承保"合规直播"+ 监管/平台治理（高毛利附加）

收入口径完全来自 data_sources.py（REVENUE_LAYER_CNY / REVENUE_BY_YEAR_CNY），
与 10_financial_projections.py 共用同一总收入 → 跨模型一致、可复现。
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from _common import BRAND, PALETTE, fmt_cny, fmt_pct, save_chart, write_json
import data_sources as DS

Y = DS.YEARS
n = len(Y)
LAYERS = list(DS.REVENUE_LAYER_RATIO.keys())   # 含"核心监控SaaS"基准层
layer_rev = {k: np.array(DS.REVENUE_LAYER_CNY[k]) for k in LAYERS}
total = np.array(DS.REVENUE_BY_YEAR_CNY)

# 各层占总收入比例（结构演进）
layer_mix = {k: layer_rev[k] / total for k in LAYERS}

# 各层 5 年 CAGR（从首个非零年到 Y5）
def cagr(arr):
    a = np.array(arr, dtype=float)
    nz = np.where(a > 0)[0]
    if len(nz) < 1 or a[nz[0]] <= 0:
        return None
    span = (n - 1) - nz[0]
    if span <= 0:
        return None
    return (a[-1] / a[nz[0]]) ** (1 / span) - 1

# Y5 各层毛利贡献
y5_gross = {k: layer_rev[k][-1] * DS.LAYER_GROSS_MARGIN[k] for k in LAYERS}
y5_gross_total = sum(y5_gross.values())

payload = {
    "as_of": DS.AS_OF, "currency": "CNY", "version": DS.VERSION,
    "years": Y,
    "layers": LAYERS,
    "layer_revenue_yi": {k: [round(float(x) / 1e8, 3) for x in layer_rev[k]] for k in LAYERS},
    "total_revenue_yi": [round(float(x) / 1e8, 3) for x in total],
    "revenue_multiplier": [round(float(x), 3) for x in DS.REVENUE_MULTIPLIER],
    "layer_mix_pct": {k: [round(float(x) * 100, 1) for x in layer_mix[k]] for k in LAYERS},
    "layer_gross_margin": DS.LAYER_GROSS_MARGIN,
    "blended_gross_margin_pct": [round(float(x) * 100, 1) for x in DS.GROSS_MARGIN],
    "layer_cagr_pct": {k: (None if cagr(DS.REVENUE_LAYER_CNY[k]) is None else round(cagr(DS.REVENUE_LAYER_CNY[k]) * 100, 0)) for k in LAYERS},
    "y5_gross_contrib_yi": {k: round(v / 1e8, 2) for k, v in y5_gross.items()},
    "headline": {
        "Y5_total_revenue_yi": round(float(total[-1]) / 1e8, 2),
        "Y5_core_saas_yi": round(float(layer_rev["核心监控SaaS"][-1]) / 1e8, 2),
        "Y5_expansion_layers_yi": round(float(total[-1] - layer_rev["核心监控SaaS"][-1]) / 1e8, 2),
        "Y5_expansion_share_pct": round(float(1 - layer_rev["核心监控SaaS"][-1] / total[-1]) * 100, 1),
        "Y5_blended_gross_margin_pct": round(float(DS.GROSS_MARGIN[-1]) * 100, 1),
    },
    "sources": ["data_sources.py (canonical 四层收入结构)", "land-and-expand 多层货币化"],
}

print("── 四层货币化收入（¥亿）──")
print("  年份            " + "  ".join(f"{y:>8s}" for y in Y))
for k in LAYERS:
    print(f"  {k:<14s}" + "  ".join(f"{layer_rev[k][t]/1e8:>8.2f}" for t in range(n)))
print(f"  {'总收入':<14s}" + "  ".join(f"{total[t]/1e8:>8.2f}" for t in range(n)))
print(f"  Y5 总收入 {fmt_cny(total[-1])} · 扩展层占比 {payload['headline']['Y5_expansion_share_pct']}% · 混合毛利 {payload['headline']['Y5_blended_gross_margin_pct']}%")

write_json("20_business_model_layers", payload)

# ── 图 1：四层收入堆叠 + 混合毛利率 ─────────────────────────────────────────
fig, axs = plt.subplots(1, 2, figsize=(12.4, 4.8))
layer_colors = {
    "核心监控SaaS": BRAND["blue"],
    "风控OS加购": BRAND["teal"],
    "数据网络/API": BRAND["violet"],
    "保险分润/RegTech": BRAND["amber"],
}
bottom = np.zeros(n)
for k in LAYERS:
    vals = layer_rev[k] / 1e8
    axs[0].bar(Y, vals, bottom=bottom, color=layer_colors[k], label=k, width=0.62)
    bottom += vals
for t in range(n):
    axs[0].text(t, total[t] / 1e8 + 1.0, f"¥{total[t]/1e8:.1f}亿", ha="center", fontsize=8.5, fontweight="bold", color=BRAND["ink"])
axs[0].set_ylabel("收入 (¥ 亿)")
axs[0].set_title("四层货币化收入堆叠（Y5 ¥{:.0f}亿）".format(total[-1] / 1e8), pad=8)
axs[0].legend(fontsize=8.5, loc="upper left")

ax2 = axs[1]
bottom = np.zeros(n)
for k in LAYERS:
    vals = layer_mix[k] * 100
    ax2.bar(Y, vals, bottom=bottom, color=layer_colors[k], width=0.62)
    bottom += vals
ax2b = ax2.twinx()
ax2b.plot(Y, np.array(DS.GROSS_MARGIN) * 100, "o-", color=BRAND["red"], lw=2.4, label="混合毛利率")
ax2b.set_ylabel("混合毛利率 (%)")
ax2b.set_ylim(50, 95)
ax2.set_ylabel("收入结构占比 (%)")
ax2.set_ylim(0, 100)
ax2.set_title("收入结构演进 + 毛利率抬升", pad=8)
ax2b.legend(loc="lower right", fontsize=9)
fig.suptitle("§1/§5 守播 LiveGuard 四层货币化（监控 → 风控OS → 数据网络 → 保险/RegTech）",
             fontsize=12.5, fontweight="bold", color=BRAND["ink"], y=1.02)
fig.tight_layout()
save_chart(fig, "fig_20_business_layers")

print("✓ 20_business_model_layers 完成 → JSON + fig_20_business_layers.png")
