"""
19_success_probability.py
=========================

项目成功概率 + 天使预期投资收益（守播 LiveGuard v3 核心交付物）。对应 BP §11。

方法学：
  1) 阶段闸门生存模型：天使 → Seed → A → B → C → 成功退出，逐级"前进概率"相乘
     得到到达各里程碑 / 成功退出的累计概率（对标早期 AI SaaS 行业基准 [S-040][S-041]）。
  2) 蒙特卡洛（N=200,000，seed=42）：每条路径模拟公司在某个闸门"前进 / 部分退出(并购) / 归零"，
     据此计算天使在该结局下的回报（全稀释股比 × 退出/回收估值），汇总得到：
       - P(成功大额退出)、P(本金全损)
       - 天使 MOIC 分布、概率加权【期望 MOIC / 5 年期望 IRR】
       - 条件于成功的 MOIC / IRR

诚实披露：天使为单笔高方差投资——中位结局为本金全损，期望值由右尾（成功退出）驱动。
读取 11_fundraising_dilution.json（全稀释股比路径）与 14_monte_carlo_valuation.json（加权 EV）。
"""

from __future__ import annotations

import json
import numpy as np
import matplotlib.pyplot as plt

from _common import BRAND, PALETTE, fmt_cny, save_chart, write_json, OUT_DIR, N_SIM, rng
import data_sources as DS

with open(OUT_DIR / "11_fundraising_dilution.json", encoding="utf-8") as f:
    fund = json.load(f)
with open(OUT_DIR / "14_monte_carlo_valuation.json", encoding="utf-8") as f:
    val = json.load(f)

r = rng()
N = N_SIM
invest = DS.ANGEL_INVEST_CNY
weighted_ev = val["weighted_EV_yi"] * 1e8
sigma = DS.EXIT_EV_SIGMA

gates = DS.STAGE_GATES
path = fund["angel_stake_path_pct"]
# 进入各闸门时天使持股（attempting 该闸门时的股比）
stake_before = [path["Angel"] / 100, path["Seed"] / 100, path["A"] / 100, path["B"] / 100, path["C"] / 100]
ref_premoney = [DS.STAGE_REF_PREMONEY_CNY[g[0]] for g in gates]

# ── 阶段闸门累计概率（解析）─────────────────────────────────────────────────
p_adv = [g[2] for g in gates]
reach = []
acc = 1.0
for p in p_adv:
    acc *= p
    reach.append(acc)
p_success = reach[-1]                       # 成功退出
p_reach_C = reach[-2]                        # 到达 C 轮

# ── 蒙特卡洛 ────────────────────────────────────────────────────────────────
payout = np.zeros(N)
year = np.zeros(N)
exit_kind = np.zeros(N, dtype=int)           # 0=全损, 1=部分退出, 2=成功退出
active = np.ones(N, dtype=bool)

for i, (name, gyear, padv, ppart, prec) in enumerate(gates):
    u = r.random(N)
    advance = active & (u < padv)
    fail = active & (~advance)
    up = r.random(N)
    partial = fail & (up < ppart)
    death = fail & (~partial)

    rec_ev = ref_premoney[i] * prec
    payout[partial] = stake_before[i] * rec_ev
    year[partial] = gyear
    exit_kind[partial] = 1
    year[death] = gyear
    exit_kind[death] = 0

    if i == len(gates) - 1:
        # 通过最后闸门 = 成功退出
        exit_ev = r.lognormal(np.log(weighted_ev), sigma, N)
        exit_ev = np.clip(exit_ev, 0.30 * weighted_ev, 4.0 * weighted_ev)
        succ = advance
        payout[succ] = stake_before[i] * exit_ev[succ]
        year[succ] = gyear
        exit_kind[succ] = 2
    active = advance

moic = payout / invest
yr = np.maximum(year, 0.5)
irr = np.where(payout > 0, moic ** (1.0 / yr) - 1.0, -1.0)

# ── 汇总 ────────────────────────────────────────────────────────────────────
p_total_loss = float(np.mean(payout <= 0))
p_partial = float(np.mean(exit_kind == 1))
p_success_mc = float(np.mean(exit_kind == 2))
E_moic = float(np.mean(moic))
median_moic = float(np.median(moic))
E_irr_5y = E_moic ** (1.0 / DS.ANGEL_HOLD_YEARS) - 1.0     # 期望 5 年 IRR（按期望倍数年化）
p_moic_ge_1 = float(np.mean(moic >= 1.0))
p_moic_ge_3 = float(np.mean(moic >= 3.0))
p_moic_ge_10 = float(np.mean(moic >= 10.0))

succ_mask = exit_kind == 2
cond_moic = float(np.mean(moic[succ_mask])) if succ_mask.any() else 0.0
cond_irr = cond_moic ** (1.0 / DS.ANGEL_HOLD_YEARS) - 1.0
qs = [10, 25, 50, 75, 90, 95, 99]
moic_quantiles = {f"P{q}": round(float(np.percentile(moic, q)), 2) for q in qs}

# ── 期望 IRR 对阶段闸门概率的敏感性（±10pp 关键闸门）─────────────────────────
def expected_moic_with(padv_override):
    # 解析近似：用各结局期望倍数加权（与 MC 同口径，足够稳定用于敏感性）
    reach_acc = 1.0
    em = 0.0
    for i, (name, gyear, padv, ppart, prec) in enumerate(gates):
        p = padv_override[i]
        # 在该闸门失败的概率（条件于到达）
        p_fail = reach_acc * (1 - p)
        rec_ev = ref_premoney[i] * prec
        em += p_fail * ppart * (stake_before[i] * rec_ev / invest)   # 部分退出贡献
        reach_acc *= p
    # 成功退出贡献（用 MC 条件均值）
    em += reach_acc * cond_moic
    return em

base = list(p_adv)
sens = {}
for idx, gname in [(2, "A→B"), (3, "B→C"), (4, "C→成功退出")]:
    hi = base.copy(); hi[idx] = min(0.95, base[idx] + 0.10)
    lo = base.copy(); lo[idx] = max(0.05, base[idx] - 0.10)
    em_hi = expected_moic_with(hi); em_lo = expected_moic_with(lo)
    sens[gname] = {
        "IRR_at_+10pp_pct": round((em_hi ** (1 / 5) - 1) * 100, 0),
        "IRR_at_-10pp_pct": round((em_lo ** (1 / 5) - 1) * 100, 0),
    }

payload = {
    "as_of": DS.AS_OF, "currency": "CNY", "version": DS.VERSION, "monte_carlo_n": int(N),
    "stage_gates": [{"gate": g[0], "year": g[1], "p_advance": g[2],
                     "cum_reach_pct": round(reach[i] * 100, 1)} for i, g in enumerate(gates)],
    "p_reach_C_pct": round(p_reach_C * 100, 1),
    "p_success_exit_pct": round(p_success * 100, 1),
    "p_success_mc_pct": round(p_success_mc * 100, 1),
    "p_partial_exit_pct": round(p_partial * 100, 1),
    "p_total_loss_pct": round(p_total_loss * 100, 1),
    "expected_MOIC": round(E_moic, 1),
    "expected_IRR_5y_pct": round(E_irr_5y * 100, 0),
    "median_MOIC": round(median_moic, 2),
    "moic_quantiles": moic_quantiles,
    "p_moic_ge_1x_pct": round(p_moic_ge_1 * 100, 1),
    "p_moic_ge_3x_pct": round(p_moic_ge_3 * 100, 1),
    "p_moic_ge_10x_pct": round(p_moic_ge_10 * 100, 1),
    "conditional_success_MOIC": round(cond_moic, 0),
    "conditional_success_IRR_5y_pct": round(cond_irr * 100, 0),
    "irr_sensitivity_to_gates": sens,
    "weighted_EV_used_yi": val["weighted_EV_yi"],
    "methodology": "阶段闸门生存模型 + 蒙特卡洛(N=200k, seed=42)；期望IRR=期望MOIC^(1/5)-1",
    "sources": [DS.SOURCES["S-040"], DS.SOURCES["S-041"], "11/14 模型输出"],
    "cross_ref": "founder_personal 见 21_personal_kelly_founder.json",
}

print("── 阶段闸门生存（累计到达概率）──")
for i, g in enumerate(gates):
    print(f"  {g[0]:<14s} 前进 {g[2]*100:.0f}%  累计到达 {reach[i]*100:.1f}%")
print(f"── 天使预期收益（概率加权）──")
print(f"  P(成功大额退出) = {p_success*100:.1f}%   P(到达C轮) = {p_reach_C*100:.1f}%")
print(f"  P(本金全损)     = {p_total_loss*100:.1f}%   P(部分退出) = {p_partial*100:.1f}%")
print(f"  期望 MOIC ≈ {E_moic:.1f}×   期望 5 年 IRR ≈ {E_irr_5y*100:.0f}%")
print(f"  中位 MOIC = {median_moic:.2f}×（中位结局=本金全损，期望由右尾驱动）")
print(f"  P(MOIC≥1×)={p_moic_ge_1*100:.0f}%  P(≥3×)={p_moic_ge_3*100:.0f}%  P(≥10×)={p_moic_ge_10*100:.0f}%")
print(f"  条件于成功：MOIC ≈ {cond_moic:.0f}× · IRR ≈ {cond_irr*100:.0f}%")

write_json("19_success_probability", payload)

# ── 图：生存漏斗 + MOIC 分布 + IRR 敏感性 ──────────────────────────────────
fig, axs = plt.subplots(1, 3, figsize=(15.6, 4.6))

# (1) 阶段生存漏斗
stage_labels = ["天使\n入场"] + [g[0] for g in gates]
reach_full = [1.0] + reach
axs[0].bar(range(len(reach_full)), [x * 100 for x in reach_full],
           color=[BRAND["blue"]] + PALETTE[1:1 + len(gates)], alpha=0.9, width=0.66)
for i, v in enumerate(reach_full):
    axs[0].text(i, v * 100 + 1.5, f"{v*100:.1f}%", ha="center", fontsize=8.5, fontweight="bold", color=BRAND["ink"])
axs[0].set_xticks(range(len(reach_full)), stage_labels, fontsize=8)
axs[0].set_ylabel("累计到达概率 (%)")
axs[0].set_ylim(0, 108)
axs[0].set_title(f"阶段闸门生存漏斗（P成功={p_success*100:.1f}%）", pad=8)

# (2) MOIC 分布（log x，截断）
pos = moic[moic > 0]
clip = np.percentile(pos, 99.5)
axs[1].hist(np.clip(pos, 1e-3, clip), bins=np.logspace(np.log10(1e-2), np.log10(clip), 60),
            color=BRAND["teal"], alpha=0.8, edgecolor="white")
axs[1].set_xscale("log")
axs[1].axvline(1.0, color=BRAND["grey"], ls=":", lw=1.5, label="本金线 1×")
axs[1].axvline(E_moic, color=BRAND["red"], ls="--", lw=2, label=f"期望 {E_moic:.0f}×")
axs[1].set_xlabel("天使 MOIC (×, log；不含 {:.0f}% 全损)".format(p_total_loss * 100))
axs[1].set_ylabel("MC 样本频次")
axs[1].set_title(f"天使 MOIC 分布（期望 IRR≈{E_irr_5y*100:.0f}%）", pad=8)
axs[1].legend(fontsize=8.5)

# (3) 期望 IRR 对关键闸门 ±10pp 敏感性
gnames = list(sens.keys())
base_irr = E_irr_5y * 100
his = [sens[g]["IRR_at_+10pp_pct"] - base_irr for g in gnames]
los = [sens[g]["IRR_at_-10pp_pct"] - base_irr for g in gnames]
yy = np.arange(len(gnames))
axs[2].barh(yy, his, color=BRAND["teal"], alpha=0.9, label="+10pp")
axs[2].barh(yy, los, color=BRAND["red"], alpha=0.9, label="-10pp")
axs[2].axvline(0, color=BRAND["ink"], lw=1)
axs[2].set_yticks(yy, gnames, fontsize=9)
axs[2].set_xlabel("期望 5 年 IRR 变动 (pp)")
axs[2].set_title(f"期望 IRR 对闸门概率敏感性（基线 {base_irr:.0f}%）", pad=8)
axs[2].legend(fontsize=8.5)
fig.suptitle("§11 项目成功概率与天使预期收益（阶段闸门生存 + 蒙特卡洛 N=200k）",
             fontsize=12.5, fontweight="bold", color=BRAND["ink"], y=1.03)
fig.tight_layout()
save_chart(fig, "fig_19_success_probability")

print("✓ 19_success_probability 完成 → JSON + fig_19_success_probability.png")
