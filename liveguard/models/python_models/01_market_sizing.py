"""
01_market_sizing.py  ·  v5.0
============================

TAM / SAM / SOM —— 中国直播电商「离岗/合规监控」SaaS 市场容量（单层监控为主口径）。
自上而下（GMV × 工具支出比 × 监控占比）+ 自下而上（可触达账号 × ARPU）双向校验，
蒙特卡洛 N=200,000，seed=42。对应 BP §2。所有常量来自 data_sources.py（唯一可信源）。

口径（保守，2026 实时调研）：
A1. 2025 直播电商 GMV 主案 ≈ ¥5.92 万亿（华经 5.26 与白皮书>5 之上、网经社 6.95 之下）[S-101][S-102][S-103]
A2. 直播工具/SaaS 支出占 GMV = 1.1%（区间 [0.9%, 1.3%]）[S-109]
A3. 监控/合规类占工具支出 = 22%（令117号后上行，区间 [18%, 28%]）[内部测算]
A4. 可触达付费监控账号 = 260 万（核心职业主播过半 + 商家自播间）[S-105][S-101]
A5. 市场层平均年 ARPU = ¥6,600（监控单品锚点，区间 [4,500, 8,500]）

注：四层货币化（风控OS/数据网络/保险）作为"增长期上行情景"附注（UPSIDE_TAM_MULTIPLIER），不进主口径。
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from _common import BRAND, PALETTE, ci, fmt_cny, save_chart, write_json, N_SIM, rng
import data_sources as DS

r = rng()
N = N_SIM

gmv_2025 = DS.CHINA_LIVE_GMV_TRILLION[2025] * 1e12     # 主案 5.92 万亿

# ── 自上而下 ────────────────────────────────────────────────────────────────
gmv = r.triangular(5.26e12, gmv_2025, 6.95e12, N)       # 下沿华经、上沿网经社
tool_ratio = r.triangular(0.009, DS.TOOL_SPEND_RATIO_OF_GMV, 0.013, N)
monitor_share = r.triangular(0.18, DS.MONITOR_SHARE_OF_TOOL_SPEND, 0.28, N)
tam_topdown = gmv * tool_ratio * monitor_share
sam_topdown = tam_topdown * r.triangular(0.78, DS.SAM_SHARE_OF_TAM, 0.90, N)

# ── 自下而上 ────────────────────────────────────────────────────────────────
accounts = r.triangular(2.1e6, DS.ADDRESSABLE_ACCOUNTS_MILLION * 1e6, 3.2e6, N)
arpu = r.triangular(4500.0, DS.MARKET_ARPU_ANCHOR_CNY, 8500.0, N)
tam_bottomup = accounts * arpu
sam_bottomup = tam_bottomup * r.triangular(0.78, DS.SAM_SHARE_OF_TAM, 0.90, N)

tam_consensus = (tam_topdown + tam_bottomup) / 2.0
sam_consensus = (sam_topdown + sam_bottomup) / 2.0

# ── 上行情景：四层货币化 TAM（仅附注，不作主口径）──────────────────────────────
tam_upside = tam_consensus * DS.UPSIDE_TAM_MULTIPLIER
sam_upside = sam_consensus * DS.UPSIDE_TAM_MULTIPLIER

# ── SOM 5 年路径（= 财务模型监控 SaaS 收入 REVENUE_BY_YEAR）──────────────────────
som_by_year = {y: DS.REVENUE_BY_YEAR_CNY[i] for i, y in enumerate(DS.YEARS)}
som_y5 = som_by_year["Y5"]


def stat(s):
    m, lo, hi = ci(s)
    return {"median": float(m), "p5": float(lo), "p95": float(hi)}


diff_tam = abs(np.median(tam_topdown) - np.median(tam_bottomup)) / np.median(tam_consensus)

result = {
    "as_of": DS.AS_OF, "currency": "CNY", "version": DS.VERSION, "monte_carlo_n": int(N),
    "TAM_topdown_CNY": stat(tam_topdown),
    "TAM_bottomup_CNY": stat(tam_bottomup),
    "TAM_consensus_CNY": stat(tam_consensus),
    "SAM_consensus_CNY": stat(sam_consensus),
    "TAM_upside_layered_CNY": stat(tam_upside),
    "SAM_upside_layered_CNY": stat(sam_upside),
    "upside_multiplier": DS.UPSIDE_TAM_MULTIPLIER,
    "upside_layers": DS.UPSIDE_EXPANSION_LAYERS,
    "SOM_by_year_CNY": som_by_year,
    "SOM_year5_CNY": float(som_y5),
    "som_y5_share_of_monitor_sam_pct": round(som_y5 / float(np.median(sam_consensus)) * 100, 1),
    "topdown_vs_bottomup_diff_pct": round(float(diff_tam) * 100, 1),
    "blended_arpu_annual_CNY": round(DS.BLENDED_ARPU_ANNUAL, 1),
    "assumptions": {
        "gmv_2025_trillion": [5.26, round(gmv_2025 / 1e12, 2), 6.95],
        "tool_spend_ratio_pct": [0.9, DS.TOOL_SPEND_RATIO_OF_GMV * 100, 1.3],
        "monitor_share_pct": [18, DS.MONITOR_SHARE_OF_TOOL_SPEND * 100, 28],
        "addressable_accounts_million": [2.1, DS.ADDRESSABLE_ACCOUNTS_MILLION, 3.2],
        "market_arpu_CNY": [4500, DS.MARKET_ARPU_ANCHOR_CNY, 8500],
    },
    "sources": [DS.SOURCES[k] for k in ("S-101", "S-102", "S-103", "S-105", "S-109")],
}

print("── 守播 LiveGuard · TAM / SAM / SOM (单层监控, MC N=200k, seed=42) ──")
print(f"  TAM 自上而下 : {fmt_cny(result['TAM_topdown_CNY']['median'])}")
print(f"  TAM 自下而上 : {fmt_cny(result['TAM_bottomup_CNY']['median'])}")
print(f"  TAM 共识(监控): {fmt_cny(result['TAM_consensus_CNY']['median'])}  双向差异 {result['topdown_vs_bottomup_diff_pct']}%")
print(f"  SAM 共识(监控): {fmt_cny(result['SAM_consensus_CNY']['median'])}")
print(f"  TAM 上行(四层): {fmt_cny(result['TAM_upside_layered_CNY']['median'])}  (×{DS.UPSIDE_TAM_MULTIPLIER} 仅情景)")
print(f"  SOM Y5       : {fmt_cny(som_y5)}  (= 监控SAM {result['som_y5_share_of_monitor_sam_pct']}%)")

write_json("01_market_sizing", result)

# ── 图 1a：TAM/SAM/SOM 漏斗 ─────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(8.6, 5.0))
medians = [np.median(tam_consensus), np.median(sam_consensus), som_y5]
p5s = [np.percentile(tam_consensus, 5), np.percentile(sam_consensus, 5), som_y5]
p95s = [np.percentile(tam_consensus, 95), np.percentile(sam_consensus, 95), som_y5]
labels = ["TAM (监控共识)", "SAM (监控共识)", "SOM (Y5)"]
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
ax.set_title("守播 LiveGuard · 监控 SaaS TAM/SAM/SOM 漏斗（MC 90% 区间）", pad=14)
fig.text(0.99, 0.01, "Source: BP §2 · MC N=200k seed=42", ha="right", fontsize=8, color=BRAND["grey"])
save_chart(fig, "fig_01_tam_sam_som_funnel")

# ── 图 1b：双向校验分布 + SOM 路径 ──────────────────────────────────────────
fig2, axs = plt.subplots(1, 2, figsize=(11.8, 4.4))
bins = np.linspace(0, np.percentile(np.concatenate([tam_topdown, tam_bottomup]), 99.5), 70)
axs[0].hist(tam_topdown / 1e8, bins=bins / 1e8, alpha=0.6, label="自上而下 (GMV×比例×占比)", color=BRAND["blue"], edgecolor="white")
axs[0].hist(tam_bottomup / 1e8, bins=bins / 1e8, alpha=0.6, label="自下而上 (账号×ARPU)", color=BRAND["teal"], edgecolor="white")
axs[0].axvline(np.median(tam_consensus) / 1e8, color=BRAND["red"], lw=2, ls="--", label=f"共识中位 {fmt_cny(np.median(tam_consensus))}")
axs[0].set_xlabel("市场规模 (¥ 亿)")
axs[0].set_ylabel("MC 样本频次")
axs[0].set_title(f"监控 TAM 双向校验（差异 {result['topdown_vs_bottomup_diff_pct']}% < 25%）", pad=10)
axs[0].legend(loc="upper right", fontsize=9)

som_vals = [som_by_year[yy] / 1e8 for yy in DS.YEARS]
axs[1].bar(DS.YEARS, som_vals, color=BRAND["teal"], alpha=0.85, width=0.6)
for i, v in enumerate(som_vals):
    axs[1].text(i, v * 1.02, f"¥{v:.2f}亿", ha="center", fontsize=9, color=BRAND["ink"])
axs[1].set_ylabel("SOM 收入 (¥ 亿)")
axs[1].set_title("SOM 5 年路径（付费账号 × 加权 ARPU）", pad=10)
fig2.suptitle("§2 中国直播在岗/合规监控 SaaS 市场量化（2026 调研）", fontsize=13, fontweight="bold", color=BRAND["ink"], y=1.02)
fig2.tight_layout()
save_chart(fig2, "fig_01_tam_validation")

print("✓ 01_market_sizing 完成 → JSON + fig_01_*.png")
