"""
21_personal_kelly_founder.py
============================

创始人王启源个人决策：胜率、盈亏比、凯利最优仓位（守播 LiveGuard v4.0 核心交付物）。

经济账户：500 万现金 + 5×100 万时间机会成本 = 1000 万 bankroll。
阶段闸门：STAGE_GATES_FOUNDER（课余轻量创始 p_advance ×0.82）。
股比：王启源合计（Founders + PreAngel）全稀释路径（11 模型）。

Kelly：f* = max(0, (p×(b+1)−1)/b)；建议仓位 = min(f*×0.25, 0.35, 现金上限 50%)。
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
bankroll = DS.FOUNDER["economic_bankroll_CNY"]
cash_cap = DS.FOUNDER["cash_capital_CNY"]
time_horizon = DS.FOUNDER["time_horizon_years"]
time_cost_yr = DS.FOUNDER["time_opportunity_cost_per_year_CNY"]
full_cost = cash_cap + time_horizon * time_cost_yr

weighted_ev = val["weighted_EV_yi"] * 1e8
sigma = DS.EXIT_EV_SIGMA
gates = DS.STAGE_GATES_FOUNDER

path = fund["wang_combined_stake_path_pct"]
stake_before = [
    path["Angel"] / 100, path["Seed"] / 100, path["A"] / 100,
    path["B"] / 100, path["C"] / 100,
]
ref_premoney = [DS.STAGE_REF_PREMONEY_CNY[g[0]] for g in gates]

p_adv = [g[2] for g in gates]
reach = []
acc = 1.0
for p in p_adv:
    acc *= p
    reach.append(acc)
p_success = reach[-1]


def run_mc(gates_list, stake_path_pct):
    sb = [
        stake_path_pct["Angel"] / 100, stake_path_pct["Seed"] / 100,
        stake_path_pct["A"] / 100, stake_path_pct["B"] / 100,
        stake_path_pct["C"] / 100,
    ]
    payout = np.zeros(N)
    year = np.zeros(N)
    exit_kind = np.zeros(N, dtype=int)
    active = np.ones(N, dtype=bool)

    for i, (name, gyear, padv, ppart, prec) in enumerate(gates_list):
        u = r.random(N)
        advance = active & (u < padv)
        fail = active & (~advance)
        up = r.random(N)
        partial = fail & (up < ppart)
        death = fail & (~partial)

        rec_ev = ref_premoney[i] * prec
        payout[partial] = sb[i] * rec_ev
        year[partial] = gyear
        exit_kind[partial] = 1
        year[death] = gyear
        exit_kind[death] = 0

        if i == len(gates_list) - 1:
            exit_ev = r.lognormal(np.log(weighted_ev), sigma, N)
            exit_ev = np.clip(exit_ev, 0.30 * weighted_ev, 4.0 * weighted_ev)
            succ = advance
            payout[succ] = sb[i] * exit_ev[succ]
            year[succ] = gyear
            exit_kind[succ] = 2
        active = advance

    return payout, year, exit_kind


payout, year, exit_kind = run_mc(gates, path)
net_return = payout - full_cost
moic_personal = np.where(full_cost > 0, payout / full_cost, 0.0)

win_mask = net_return > 0
loss_mask = ~win_mask
p_win = float(np.mean(win_mask))
p_total_loss = float(np.mean(payout <= 0))
p_success_mc = float(np.mean(exit_kind == 2))
p_partial = float(np.mean(exit_kind == 1))

mean_win = float(np.mean(net_return[win_mask])) if win_mask.any() else 0.0
mean_loss = float(np.mean(net_return[loss_mask])) if loss_mask.any() else 0.0
pnl_ratio_b = mean_win / abs(mean_loss) if mean_loss < 0 else 0.0

def kelly_fraction(p, b):
    if b <= 0 or p <= 0:
        return 0.0
    f = (p * (b + 1) - 1) / b
    return max(0.0, f)


f_kelly_full = kelly_fraction(p_win, pnl_ratio_b)
f_recommended = min(
    f_kelly_full * DS.KELLY_FRACTIONAL,
    DS.KELLY_MAX_POSITION_OF_BANKROLL,
    cash_cap / bankroll,
)
recommended_commitment = f_recommended * bankroll
recommended_cash = min(cash_cap, recommended_commitment * DS.KELLY_CASH_SHARE_OF_COMMITMENT)
recommended_time_wan = (recommended_commitment - recommended_cash) / 1e4  # 万元

E_net = float(np.mean(net_return))
median_moic = float(np.median(moic_personal))
E_moic = float(np.mean(moic_personal))
p_moic_ge_1 = float(np.mean(moic_personal >= 1.0))

succ_mask = exit_kind == 2
cond_payout = float(np.mean(payout[succ_mask])) if succ_mask.any() else 0.0
cond_moic = cond_payout / full_cost if full_cost > 0 else 0.0

# 行动标签
if f_recommended < 0.05:
    action_label = "观望 / 不全职 all-in"
elif f_recommended < 0.15:
    action_label = "轻仓试探 + 必须补全职技术负责人"
elif f_recommended >= 0.15 and E_net > 0:
    action_label = "可按建议仓位投入，仍须预留 ≥65% bankroll 抗风险"
else:
    action_label = "轻仓试探 + 必须补全职技术负责人"

# 敏感性：课余折扣系数
sensitivity = {}
for mult in (0.78, 0.82, 0.86):
    gates_s = [
        (g[0], g[1], round(DS.STAGE_GATES[i][2] * mult, 4),
         min(0.95, DS.STAGE_GATES[i][3] + DS.FOUNDER_PARTIAL_EXIT_BUMP), g[4])
        for i, g in enumerate(DS.STAGE_GATES)
    ]
    ps = np.prod([g[2] for g in gates_s])
    sensitivity[str(mult)] = {"p_success_exit_pct": round(ps * 100, 2)}

# 仓位情景 EV
E_payout = float(np.mean(payout))
scenario_order = [
    ("不投入", 0.0),
    (f"建议 {f_recommended * 100:.0f}%", f_recommended),
    ("全投入 100%", 1.0),
]
scenarios = {}
for label, f in scenario_order:
    net = E_payout - f * bankroll
    scenarios[label] = {
        "f": f,
        "expected_net_CNY": round(net),
        "expected_net_wan": round(net / 1e4, 1),
    }

# 天使基准 P(成功) 对比
angel_p_success = float(np.prod([g[2] for g in DS.STAGE_GATES]))

payload = {
    "as_of": DS.AS_OF, "version": DS.VERSION, "monte_carlo_n": int(N),
    "founder": DS.FOUNDER,
    "economic_bankroll_CNY": bankroll,
    "full_commitment_cost_CNY": full_cost,
    "wang_combined_after_C_pct": fund["wang_combined_after_C_pct"],
    "stage_gates_founder": [
        {"gate": g[0], "year": g[1], "p_advance": g[2],
         "cum_reach_pct": round(reach[i] * 100, 1)} for i, g in enumerate(gates)
    ],
    "p_success_exit_pct": round(p_success * 100, 1),
    "p_success_mc_pct": round(p_success_mc * 100, 1),
    "p_partial_exit_pct": round(p_partial * 100, 1),
    "p_total_loss_pct": round(p_total_loss * 100, 1),
    "angel_baseline_p_success_exit_pct": round(angel_p_success * 100, 1),
    "win_rate_p_pct": round(p_win * 100, 1),
    "pnl_ratio_b": round(pnl_ratio_b, 2),
    "kelly_full_f": round(f_kelly_full, 4),
    "kelly_fractional": DS.KELLY_FRACTIONAL,
    "kelly_recommended_f": round(f_recommended, 4),
    "recommended_commitment_CNY": round(recommended_commitment),
    "recommended_commitment_wan": round(recommended_commitment / 1e4, 1),
    "recommended_cash_wan": round(recommended_cash / 1e4, 1),
    "recommended_time_equiv_wan": round(recommended_time_wan, 1),
    "expected_net_return_CNY": round(E_net),
    "expected_net_return_wan": round(E_net / 1e4, 1),
    "expected_MOIC": round(E_moic, 2),
    "median_MOIC": round(median_moic, 2),
    "p_moic_ge_1x_pct": round(p_moic_ge_1 * 100, 1),
    "conditional_success_payout_CNY": round(cond_payout),
    "conditional_success_MOIC": round(cond_moic, 1),
    "mean_win_CNY": round(mean_win),
    "mean_loss_CNY": round(mean_loss),
    "action_label": action_label,
    "position_scenarios": scenarios,
    "part_time_sensitivity": sensitivity,
    "methodology": (
        "STAGE_GATES_FOUNDER + MC(N=200k, seed=42)；"
        "胜率=P(净回报>0)；盈亏比=E[赢]/|E[输]|；"
        "Kelly f*=(p(b+1)-1)/b；建议=1/4 Kelly capped"
    ),
    "sources": [DS.SOURCES["S-040"], DS.SOURCES["S-041"], DS.SOURCES["S-042"], "11/14 模型输出"],
}

print("── 王启源个人决策（课余轻量创始 · STAGE_GATES_FOUNDER）──")
print(f"  经济 bankroll = {fmt_cny(bankroll)}（现金 {fmt_cny(cash_cap)} + 时间 {time_horizon}×{fmt_cny(time_cost_yr)}）")
print(f"  P(成功退出) = {p_success*100:.1f}%（天使基准 {angel_p_success*100:.1f}%）")
print(f"  胜率 p = {p_win*100:.1f}%   盈亏比 b = {pnl_ratio_b:.2f}")
print(f"  Kelly 全量 f* = {f_kelly_full:.3f}   建议仓位（1/4 Kelly）= {f_recommended*100:.1f}% = {fmt_cny(recommended_commitment)}")
print(f"  期望净回报 = {fmt_cny(E_net)}   中位 MOIC = {median_moic:.2f}×   P(全损) = {p_total_loss*100:.1f}%")
print(f"  行动建议：{action_label}")

write_json("21_personal_kelly_founder", payload)

fig, axs = plt.subplots(1, 3, figsize=(15.6, 4.6))

# (1) 创始人 vs 天使 成功概率漏斗
stage_labels = ["PreAngel\n入场"] + [g[0] for g in gates]
reach_full = [1.0] + reach
angel_reach = [1.0]
acc_a = 1.0
for g in DS.STAGE_GATES:
    acc_a *= g[2]
    angel_reach.append(acc_a)
x = np.arange(len(reach_full))
w = 0.35
axs[0].bar(x - w / 2, [v * 100 for v in reach_full], w, color=BRAND["blue"], label="创始人(课余)", alpha=0.9)
axs[0].bar(x + w / 2, [v * 100 for v in angel_reach[: len(reach_full)]], w, color=BRAND["grey"], label="天使基准", alpha=0.7)
axs[0].set_xticks(x, stage_labels, fontsize=7.5)
axs[0].set_ylabel("累计到达概率 (%)")
axs[0].set_title(f"生存漏斗对比（创始人 P成功={p_success*100:.1f}%）", pad=8)
axs[0].legend(fontsize=8)

# (2) Kelly 仓位与情景 EV
labels = list(scenarios.keys())
evs = [scenarios[k]["expected_net_wan"] for k in labels]
cols = [BRAND["grey"], BRAND["teal"], BRAND["amber"]]
bars = axs[1].bar(labels, evs, color=cols, alpha=0.9, width=0.55)
for bar, v in zip(bars, evs):
    axs[1].text(bar.get_x() + bar.get_width() / 2, v + (5 if v >= 0 else -15),
                f"{v:+.0f}万", ha="center", fontsize=9, fontweight="bold", color=BRAND["ink"])
axs[1].axhline(0, color=BRAND["ink"], lw=1)
axs[1].set_ylabel("期望净回报 (万元)")
axs[1].set_title(f"凯利仓位情景（f*={f_kelly_full:.2f} → 建议 {f_recommended*100:.0f}%）", pad=8)

# (3) 个人 MOIC 分布
pos = moic_personal[moic_personal > 0]
if len(pos) > 0:
    clip = np.percentile(pos, 99.5)
    axs[2].hist(np.clip(pos, 1e-3, clip), bins=40, color=BRAND["teal"], alpha=0.8, edgecolor="white")
axs[2].axvline(1.0, color=BRAND["grey"], ls=":", lw=1.5, label="盈亏平衡 1×")
axs[2].axvline(E_moic, color=BRAND["red"], ls="--", lw=2, label=f"期望 {E_moic:.1f}×")
axs[2].set_xlabel("个人 MOIC（全投入 1000 万口径）")
axs[2].set_ylabel("MC 样本频次")
axs[2].set_title(f"个人 MOIC（中位 {median_moic:.2f}× · 胜率 {p_win*100:.0f}%）", pad=8)
axs[2].legend(fontsize=8)

fig.suptitle(
    "§11b 王启源个人凯利仓位（胜率×盈亏比×1/4 Kelly · N=200k）",
    fontsize=12.5, fontweight="bold", color=BRAND["ink"], y=1.03,
)
fig.tight_layout()
save_chart(fig, "fig_21_kelly_position")

print("✓ 21_personal_kelly_founder 完成 → JSON + fig_21_kelly_position.png")
