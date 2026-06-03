"""
19_success_probability.py  ·  v5.0（成功概率 + 多口径回报，合并重写）
=====================================================================

项目成功概率 + 本轮（Seed）投资人回报的【多口径披露】。对应 BP §12。

方法学（保守，2026 真实晋级率）：
  1) 阶段闸门生存模型：Seed → A → B → C → 成功退出，逐级"前进概率"相乘
     得到累计到达各里程碑/成功退出的概率（Seed→A 2026≈22%，A→B/B→C≈50–55% [S-110][S-114]）。
  2) 蒙特卡洛（N=200,000，seed=42）：每条路径在某个闸门"前进 / 部分退出(并购) / 归零"，
     计算 Seed 投资人在该结局下的回报（全稀释股比 × 退出/回收 EV），逐路径得到 MOIC 与 IRR。
  3) 回报【多口径并列】，杜绝单点夸大：
       - 中位（≈ 本金全损）
       - 概率加权期望 MOIC / 期望 IRR
       - 条件于成功退出的 MOIC / IRR
       - 逐路径 IRR 的期望与分位（P25/P50/P75/P90）—— 不用 E[MOIC]^(1/n)−1 替代

诚实披露：早期股权为单笔高方差投资——中位结局为本金全损，期望值由右尾（成功退出）驱动；
所有数字均为情景建模，非回报承诺。读取 11（全稀释股比路径）与 14（加权 EV）。
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
invest = DS.LEAD_INVEST_CNY
hold = DS.HOLD_YEARS
weighted_ev = val["weighted_EV_yi"] * 1e8
sigma = DS.EXIT_EV_SIGMA

gates = DS.STAGE_GATES                       # 4 闸门：Seed→A, A→B, B→C, C→退出
path = fund["lead_stake_path_pct"]
# 进入各闸门时 Seed 投资人持股（attempting 该闸门时已完成的最近一轮股比）
stake_before = [path["Seed"] / 100, path["A"] / 100, path["B"] / 100, path["C"] / 100]
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
        exit_ev = r.lognormal(np.log(weighted_ev), sigma, N)
        exit_ev = np.clip(exit_ev, 0.30 * weighted_ev, 4.0 * weighted_ev)
        succ = advance
        payout[succ] = stake_before[i] * exit_ev[succ]
        year[succ] = gyear
        exit_kind[succ] = 2
    active = advance

moic = payout / invest
yr = np.maximum(year, 0.5)
# 逐路径 IRR：全损 = -100%
irr_path = np.where(payout > 0, np.power(np.maximum(moic, 1e-9), 1.0 / yr) - 1.0, -1.0)

# ── 汇总（多口径）────────────────────────────────────────────────────────────
p_total_loss = float(np.mean(payout <= 0))
p_partial = float(np.mean(exit_kind == 1))
p_success_mc = float(np.mean(exit_kind == 2))
E_moic = float(np.mean(moic))
median_moic = float(np.median(moic))
E_irr_annualized = E_moic ** (1.0 / hold) - 1.0     # 期望 MOIC 年化（仅作对照口径）
E_irr_path = float(np.mean(irr_path))               # 逐路径 IRR 期望（主口径）
p_moic_ge_1 = float(np.mean(moic >= 1.0))
p_moic_ge_3 = float(np.mean(moic >= 3.0))
p_moic_ge_10 = float(np.mean(moic >= 10.0))

succ_mask = exit_kind == 2
cond_moic = float(np.mean(moic[succ_mask])) if succ_mask.any() else 0.0
cond_irr = cond_moic ** (1.0 / hold) - 1.0
cond_irr_path = float(np.mean(irr_path[succ_mask])) if succ_mask.any() else 0.0

qs = [10, 25, 50, 75, 90, 95, 99]
moic_quantiles = {f"P{q}": round(float(np.percentile(moic, q)), 2) for q in qs}
irr_quantiles = {f"P{q}": round(float(np.percentile(irr_path, q)) * 100, 0) for q in [25, 50, 75, 90, 95, 99]}

# ── 期望 MOIC 对阶段闸门概率的敏感性（±7pp 关键闸门）─────────────────────────
def expected_moic_with(padv_override):
    reach_acc = 1.0
    em = 0.0
    for i, (name, gyear, padv, ppart, prec) in enumerate(gates):
        p = padv_override[i]
        p_fail = reach_acc * (1 - p)
        rec_ev = ref_premoney[i] * prec
        em += p_fail * ppart * (stake_before[i] * rec_ev / invest)
        reach_acc *= p
    em += reach_acc * cond_moic
    return em


base = list(p_adv)
dpp = DS.STAGE_GATE_SENS_PP
sens = {}
for idx, gname in [(0, "Seed→A"), (1, "A→B"), (3, "C→成功退出")]:
    hi = base.copy(); hi[idx] = min(0.95, base[idx] + dpp)
    lo = base.copy(); lo[idx] = max(0.05, base[idx] - dpp)
    em_hi = expected_moic_with(hi); em_lo = expected_moic_with(lo)
    sens[gname] = {
        "expected_MOIC_at_+pp": round(em_hi, 2),
        "expected_MOIC_at_-pp": round(em_lo, 2),
    }

payload = {
    "as_of": DS.AS_OF, "currency": "CNY", "version": DS.VERSION, "monte_carlo_n": int(N),
    "lead_round": DS.LEAD_ROUND, "lead_invest_CNY": invest, "lead_invest_disp": fmt_cny(invest),
    "hold_years": hold,
    "stage_gates": [{"gate": g[0], "year": g[1], "p_advance": g[2],
                     "cum_reach_pct": round(reach[i] * 100, 2)} for i, g in enumerate(gates)],
    "p_reach_C_pct": round(p_reach_C * 100, 2),
    "p_success_exit_pct": round(p_success * 100, 2),
    "p_success_mc_pct": round(p_success_mc * 100, 2),
    "p_partial_exit_pct": round(p_partial * 100, 1),
    "p_total_loss_pct": round(p_total_loss * 100, 1),
    # ── 多口径回报 ──
    "median_MOIC": round(median_moic, 2),
    "expected_MOIC": round(E_moic, 2),
    "expected_IRR_annualized_pct": round(E_irr_annualized * 100, 0),
    "expected_IRR_path_pct": round(E_irr_path * 100, 0),
    "conditional_success_MOIC": round(cond_moic, 1),
    "conditional_success_IRR_pct": round(cond_irr * 100, 0),
    "conditional_success_IRR_path_pct": round(cond_irr_path * 100, 0),
    "moic_quantiles": moic_quantiles,
    "irr_path_quantiles_pct": irr_quantiles,
    "p_moic_ge_1x_pct": round(p_moic_ge_1 * 100, 1),
    "p_moic_ge_3x_pct": round(p_moic_ge_3 * 100, 1),
    "p_moic_ge_10x_pct": round(p_moic_ge_10 * 100, 1),
    "expected_moic_sensitivity_to_gates": sens,
    "weighted_EV_used_yi": val["weighted_EV_yi"],
    "methodology": "阶段闸门生存(2026真实晋级率) + 蒙特卡洛(N=200k, seed=42)；"
                   "回报多口径并列：中位/期望/条件于成功/逐路径IRR分位；非回报承诺。",
    "sources": [DS.SOURCES["S-110"], DS.SOURCES["S-114"], "11/14 模型输出"],
}

print("── 阶段闸门生存（累计到达概率）──")
for i, g in enumerate(gates):
    print(f"  {g[0]:<14s} 前进 {g[2]*100:.0f}%  累计到达 {reach[i]*100:.2f}%")
print("── Seed 投资人回报（多口径）──")
print(f"  P(成功退出) = {p_success*100:.2f}%   P(到达C轮) = {p_reach_C*100:.2f}%")
print(f"  P(本金全损) = {p_total_loss*100:.1f}%   P(部分退出) = {p_partial*100:.1f}%")
print(f"  中位 MOIC = {median_moic:.2f}×（中位=本金全损）")
print(f"  期望 MOIC ≈ {E_moic:.2f}× · 期望逐路径 IRR ≈ {E_irr_path*100:.0f}%（年化对照 {E_irr_annualized*100:.0f}%）")
print(f"  条件于成功：MOIC ≈ {cond_moic:.0f}× · IRR ≈ {cond_irr*100:.0f}%")
print(f"  逐路径 IRR 分位 P50/P75/P90 = {irr_quantiles['P50']}/{irr_quantiles['P75']}/{irr_quantiles['P90']}%")
print(f"  P(MOIC≥1×)={p_moic_ge_1*100:.0f}%  P(≥3×)={p_moic_ge_3*100:.0f}%  P(≥10×)={p_moic_ge_10*100:.0f}%")

write_json("19_success_probability", payload)

# ── 图：生存漏斗 + MOIC 分布 + IRR 分位 ────────────────────────────────────
fig, axs = plt.subplots(1, 3, figsize=(15.6, 4.6))

stage_labels = ["Seed\n入场"] + [g[0] for g in gates]
reach_full = [1.0] + reach
axs[0].bar(range(len(reach_full)), [x * 100 for x in reach_full],
           color=[BRAND["blue"]] + PALETTE[1:1 + len(gates)], alpha=0.9, width=0.66)
for i, v in enumerate(reach_full):
    axs[0].text(i, v * 100 + 1.5, f"{v*100:.1f}%", ha="center", fontsize=8.5, fontweight="bold", color=BRAND["ink"])
axs[0].set_xticks(range(len(reach_full)), stage_labels, fontsize=8)
axs[0].set_ylabel("累计到达概率 (%)")
axs[0].set_ylim(0, 108)
axs[0].set_title(f"阶段闸门生存漏斗（P成功={p_success*100:.1f}%）", pad=8)

pos = moic[moic > 0]
if pos.size > 0:
    clip = np.percentile(pos, 99.5)
    axs[1].hist(np.clip(pos, 1e-3, clip), bins=np.logspace(np.log10(1e-2), np.log10(max(clip, 1.0)), 60),
                color=BRAND["teal"], alpha=0.8, edgecolor="white")
    axs[1].set_xscale("log")
axs[1].axvline(1.0, color=BRAND["grey"], ls=":", lw=1.5, label="本金线 1×")
axs[1].axvline(max(E_moic, 1e-3), color=BRAND["red"], ls="--", lw=2, label=f"期望 {E_moic:.1f}×")
axs[1].set_xlabel("Seed MOIC (×, log；不含 {:.0f}% 全损)".format(p_total_loss * 100))
axs[1].set_ylabel("MC 样本频次")
axs[1].set_title(f"Seed MOIC 分布（中位=全损，期望由右尾驱动）", pad=8)
axs[1].legend(fontsize=8.5)

# (3) 逐路径 IRR 分位
qlabels = ["P50", "P75", "P90", "P95"]
qvals = [irr_quantiles["P50"], irr_quantiles["P75"], irr_quantiles["P90"], irr_quantiles["P95"]]
bcolors = [BRAND["grey"], BRAND["amber"], BRAND["teal"], BRAND["blue"]]
axs[2].bar(qlabels, qvals, color=bcolors, alpha=0.9, width=0.62)
for i, v in enumerate(qvals):
    axs[2].text(i, v + (3 if v >= 0 else -8), f"{v:.0f}%", ha="center", fontsize=9, fontweight="bold", color=BRAND["ink"])
axs[2].axhline(0, color=BRAND["ink"], lw=1)
axs[2].set_ylabel("逐路径 IRR (%)")
axs[2].set_title(f"逐路径 IRR 分位（期望 {E_irr_path*100:.0f}%）", pad=8)
fig.suptitle("§12 成功概率与投资回报（多口径 · 阶段闸门生存 + 蒙特卡洛 N=200k）",
             fontsize=12.5, fontweight="bold", color=BRAND["ink"], y=1.03)
fig.tight_layout()
save_chart(fig, "fig_19_success_probability")

print("✓ 19_success_probability 完成 → JSON + fig_19_success_probability.png")
