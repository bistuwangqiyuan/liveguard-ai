"""
01_market_sizing.py
===================

TAM / SAM / SOM —— 中国直播电商「合规 / 在岗监控」SaaS 市场容量。
自上而下（GMV × 工具支出比 × 监控占比）+ 自下而上（可触达账号 × ARPU）双向校验，
蒙特卡洛 N=200,000，seed=42。

对应 BP §2.4。所有常量来自 data_sources.py（唯一可信源）。

---------------------------------------------------------------------------
ASSUMPTIONS（保守立场 · 取可公开验证区间中值）
---------------------------------------------------------------------------
A1. 2024 中国直播电商 GMV = ¥5.30 万亿（区间 [5.0, 5.6]）[S-001][S-002]
A2. 工具支出占 GMV = 1.2%（区间 [1.0%, 1.4%]）[S-015]
A3. 监控/合规类占工具支出 = 25%（区间 [20%, 30%]）[内部 30+ MCN 采购清单中位]
A4. 可触达账号 = 249 万（50%×178 万职业主播 + 160 万商家自播）[S-005][S-002]
A5. 市场平均年 ARPU = ¥7,188（Pro 档锚点；区间 [5,000, 9,000]）

---------------------------------------------------------------------------
SOURCES：见 data_sources.SOURCES（S-001/002/005/008/015）
---------------------------------------------------------------------------
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from _common import BRAND, PALETTE, ci, fmt_cny, save_chart, write_json, N_SIM, rng
import data_sources as DS

r = rng()
N = N_SIM

# ── 自上而下 ────────────────────────────────────────────────────────────────
gmv = r.triangular(5.0e12, 5.30e12, 5.6e12, N)
tool_ratio = r.triangular(0.010, 0.012, 0.014, N)
monitor_share = r.triangular(0.20, 0.25, 0.30, N)
tam_topdown = gmv * tool_ratio * monitor_share
sam_topdown = tam_topdown * r.triangular(0.80, 0.86, 0.92, N)

# ── 自下而上 ────────────────────────────────────────────────────────────────
accounts = r.triangular(2.1e6, 2.49e6, 2.9e6, N)
arpu = r.triangular(5000.0, 7188.0, 9000.0, N)
tam_bottomup = accounts * arpu
sam_bottomup = tam_bottomup * r.triangular(0.78, 0.86, 0.92, N)

tam_consensus = (tam_topdown + tam_bottomup) / 2.0
sam_consensus = (sam_topdown + sam_bottomup) / 2.0

# ── v3：多层货币化 TAM 放大（核心监控 + 风控 OS + 数据网络/API + 保险/RegTech）──────
LAYER_MULT_TOTAL = sum(DS.TAM_LAYER_MULTIPLIER.values())   # ≈ 3.80×
tam_layered = tam_consensus * LAYER_MULT_TOTAL
sam_layered = sam_consensus * LAYER_MULT_TOTAL

# ── SOM 5 年路径（与财务模型一致：四层货币化总收入 REVENUE_BY_YEAR）──────────────
arpu_blend = DS.BLENDED_ARPU_ANNUAL
som_by_year = {y: DS.REVENUE_BY_YEAR_CNY[i] for i, y in enumerate(DS.YEARS)}
som_y5 = som_by_year["Y5"]


def stat(s):
    m, lo, hi = ci(s)
    return {"median": float(m), "p5": float(lo), "p95": float(hi)}


diff_tam = abs(np.median(tam_topdown) - np.median(tam_bottomup)) / np.median(tam_consensus)

result = {
    "as_of": DS.AS_OF, "currency": "CNY", "monte_carlo_n": int(N),
    "TAM_topdown_CNY": stat(tam_topdown),
    "TAM_bottomup_CNY": stat(tam_bottomup),
    "TAM_consensus_CNY": stat(tam_consensus),
    "SAM_consensus_CNY": stat(sam_consensus),
    "TAM_layered_total_CNY": stat(tam_layered),
    "SAM_layered_total_CNY": stat(sam_layered),
    "layer_multiplier_total": round(LAYER_MULT_TOTAL, 2),
    "layer_multiplier_detail": DS.TAM_LAYER_MULTIPLIER,
    "SOM_by_year_CNY": som_by_year,
    "SOM_year5_CNY": float(som_y5),
    "som_y5_share_of_monitor_sam_pct": round(som_y5 / float(np.median(sam_consensus)) * 100, 1),
    "som_y5_share_of_layered_sam_pct": round(som_y5 / float(np.median(sam_layered)) * 100, 1),
    "topdown_vs_bottomup_diff_pct": round(float(diff_tam) * 100, 1),
    "blended_arpu_annual_CNY": round(arpu_blend, 1),
    "assumptions": {
        "gmv_2024_trillion": [5.0, 5.30, 5.6],
        "tool_spend_ratio_pct": [1.0, 1.2, 1.4],
        "monitor_share_pct": [20, 25, 30],
        "addressable_accounts_million": [2.1, 2.49, 2.9],
        "market_arpu_CNY": [5000, 7188, 9000],
    },
    "sources": [DS.SOURCES[k] for k in ("S-001", "S-002", "S-005", "S-008", "S-015")],
}

print("── 守播 LiveGuard · TAM / SAM / SOM (MC N=200k, seed=42) ──")
print(f"  TAM 自上而下 : {fmt_cny(result['TAM_topdown_CNY']['median'])}")
print(f"  TAM 自下而上 : {fmt_cny(result['TAM_bottomup_CNY']['median'])}")
print(f"  TAM 共识(监控): {fmt_cny(result['TAM_consensus_CNY']['median'])}  双向差异 {result['topdown_vs_bottomup_diff_pct']}%")
print(f"  SAM 共识(监控): {fmt_cny(result['SAM_consensus_CNY']['median'])}")
print(f"  TAM 多层放大 : {fmt_cny(result['TAM_layered_total_CNY']['median'])}  (×{LAYER_MULT_TOTAL:.2f} 四层货币化)")
print(f"  SAM 多层放大 : {fmt_cny(result['SAM_layered_total_CNY']['median'])}")
print(f"  SOM Y5       : {fmt_cny(som_y5)}  (= 监控SAM {result['som_y5_share_of_monitor_sam_pct']}% / 多层SAM {result['som_y5_share_of_layered_sam_pct']}%)")

write_json("01_market_sizing", result)

# ── 图 1a：TAM/SAM/SOM 漏斗 ─────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(8.6, 5.0))
levels = [("TAM\n(共识)", tam_consensus), ("SAM\n(共识)", sam_consensus)]
medians = [np.median(tam_consensus), np.median(sam_consensus), som_y5]
p5s = [np.percentile(tam_consensus, 5), np.percentile(sam_consensus, 5), som_y5]
p95s = [np.percentile(tam_consensus, 95), np.percentile(sam_consensus, 95), som_y5]
labels = ["TAM (共识)", "SAM (共识)", "SOM (Y5)"]
widths = np.array(medians) / max(medians)
y = np.arange(3)
for i in range(3):
    ax.barh(y[i], widths[i], color=PALETTE[i], alpha=0.92, height=0.6)
    txt = fmt_cny(medians[i])
    if i < 2:
        txt += f"\n90%CI [{fmt_cny(p5s[i])}, {fmt_cny(p95s[i])}]"
    ax.text(widths[i] + 0.01, y[i], txt, va="center", fontsize=10, color=BRAND["ink"])
ax.set_yticks(y, labels, fontsize=11, color=BRAND["ink"])
ax.invert_yaxis()
ax.set_xlim(0, 1.55)
ax.set_xticks([])
ax.spines["bottom"].set_visible(False)
ax.grid(False)
ax.set_title("守播 LiveGuard · TAM / SAM / SOM 漏斗（蒙特卡洛 90% 区间）", pad=14)
fig.text(0.99, 0.01, "Source: BP §2.4 · MC N=200k seed=42", ha="right", fontsize=8, color=BRAND["grey"])
save_chart(fig, "fig_01_tam_sam_som_funnel")

# ── 图 1b：双向校验分布 + SOM 路径 ──────────────────────────────────────────
fig2, axs = plt.subplots(1, 2, figsize=(11.8, 4.4))
bins = np.linspace(0, np.percentile(np.concatenate([tam_topdown, tam_bottomup]), 99.5), 70)
axs[0].hist(tam_topdown / 1e8, bins=bins / 1e8, alpha=0.6, label="自上而下 (GMV×比例×占比)", color=BRAND["blue"], edgecolor="white")
axs[0].hist(tam_bottomup / 1e8, bins=bins / 1e8, alpha=0.6, label="自下而上 (账号×ARPU)", color=BRAND["teal"], edgecolor="white")
axs[0].axvline(np.median(tam_consensus) / 1e8, color=BRAND["red"], lw=2, ls="--", label=f"共识中位 {fmt_cny(np.median(tam_consensus))}")
axs[0].set_xlabel("市场规模 (¥ 亿)")
axs[0].set_ylabel("MC 样本频次")
axs[0].set_title(f"TAM 双向校验（差异 {result['topdown_vs_bottomup_diff_pct']}% < 25%）", pad=10)
axs[0].legend(loc="upper right", fontsize=9)

som_vals = [som_by_year[y] / 1e8 for y in DS.YEARS]
axs[1].bar(DS.YEARS, som_vals, color=BRAND["teal"], alpha=0.85, width=0.6)
for i, v in enumerate(som_vals):
    axs[1].text(i, v * 1.02, f"¥{v:.2f}亿", ha="center", fontsize=9, color=BRAND["ink"])
axs[1].set_ylabel("SOM 收入 (¥ 亿)")
axs[1].set_title("SOM 5 年路径（客户数 × 加权 ARPU）", pad=10)
fig2.suptitle("§2.4 中国直播在岗监控 SaaS 市场量化", fontsize=13, fontweight="bold", color=BRAND["ink"], y=1.02)
fig2.tight_layout()
save_chart(fig2, "fig_01_tam_validation")

print("✓ 01_market_sizing 完成 → JSON + fig_01_*.png")
