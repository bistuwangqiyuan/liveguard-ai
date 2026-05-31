"""
09_user_profile_kelly.py
========================

三类用户画像 × Kelly 公式 + 行动方案推荐器仿真。

---------------------------------------------------------------------------
用户画像
---------------------------------------------------------------------------

| 画像        | 风险偏好  | 流动性约束 | 投资经验 | Kelly 折扣 |
|-------------|-----------|-----------|----------|-----------|
| 保守 (C)    | 低        | 高        | 入门     | 0.25× Kelly |
| 平衡 (B)    | 中        | 中        | 进阶     | 0.50× Kelly |
| 进取 (A)    | 高        | 低        | 资深     | 0.75× Kelly |

---------------------------------------------------------------------------
Kelly 公式
---------------------------------------------------------------------------
对每笔机会：
    p = 胜率（来自模型 04 引擎）
    b = 盈亏比 = E[+] / E[-]
    f* = (p * (b+1) - 1) / b

实际推荐配比 = max(0, min(f* * personality_factor, position_cap))
position_cap：保守 5% / 平衡 12% / 进取 20%

---------------------------------------------------------------------------
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from _common import BRAND, PALETTE, save_chart, write_json, ci, rng


PERSONAS = {
    "C_保守": {"factor": 0.25, "cap": 0.05, "min_winrate": 0.50,
                "min_pnl_ratio": 3.0, "color": BRAND["blue"]},
    "B_平衡": {"factor": 0.50, "cap": 0.12, "min_winrate": 0.35,
                "min_pnl_ratio": 2.0, "color": BRAND["teal"]},
    "A_进取": {"factor": 0.75, "cap": 0.20, "min_winrate": 0.20,
                "min_pnl_ratio": 1.4, "color": BRAND["amber"]},
}

r = rng()
N = 200
opportunities = []
for i in range(N):
    p = float(np.clip(r.beta(2.5, 4), 0.0, 0.95))
    b = float(np.clip(r.lognormal(np.log(2.5), 0.55), 0.4, 14.0))
    sector = r.choice(["AI", "Biotech", "Consumer", "Climate", "Fintech"])
    opportunities.append({"p": p, "b": b, "sector": sector})


def kelly_fraction(p, b):
    if b <= 0 or p <= 0:
        return 0.0
    f = (p * (b + 1) - 1) / b
    return max(0.0, f)


recommendations = {name: [] for name in PERSONAS}

for opp in opportunities:
    f = kelly_fraction(opp["p"], opp["b"])
    for name, cfg in PERSONAS.items():
        if opp["p"] < cfg["min_winrate"] or opp["b"] < cfg["min_pnl_ratio"]:
            rec = 0.0
            action = "回避"
        else:
            rec = min(f * cfg["factor"], cfg["cap"])
            if rec < 0.005:
                action = "仅观察"
            elif rec < 0.03:
                action = "小仓位试水"
            elif rec < 0.10:
                action = "标准建仓"
            else:
                action = "重仓建立"
        recommendations[name].append({
            "p": opp["p"], "b": opp["b"], "sector": opp["sector"],
            "kelly_raw": f, "recommend_pct": rec, "action": action,
        })


summary = {}
for name in PERSONAS:
    recs = recommendations[name]
    nonzero = [r["recommend_pct"] for r in recs if r["recommend_pct"] > 0]
    actions_count = {}
    for x in recs:
        actions_count[x["action"]] = actions_count.get(x["action"], 0) + 1
    summary[name] = {
        "n_opportunities": len(recs),
        "n_actionable": int(sum(1 for r in recs if r["recommend_pct"] > 0)),
        "avg_recommend_pct": float(np.mean(nonzero)) if nonzero else 0.0,
        "max_recommend_pct": float(max(nonzero)) if nonzero else 0.0,
        "actions_distribution": actions_count,
    }


print("── Kelly × 画像 行动建议汇总 ──")
for name, info in summary.items():
    print(f"  {name}  可行机会 {info['n_actionable']}/{info['n_opportunities']}  "
          f"平均建议仓位 {info['avg_recommend_pct']*100:.1f}%  "
          f"最大 {info['max_recommend_pct']*100:.1f}%")
    print(f"    分布: {info['actions_distribution']}")

result = {
    "as_of": "2026-04-30",
    "n_opportunities": N,
    "personas": {k: {kk: vv for kk, vv in v.items() if kk != "color"}
                 for k, v in PERSONAS.items()},
    "summary": summary,
    "sample_recommendations_top5": {
        name: sorted(recs, key=lambda x: -x["recommend_pct"])[:5]
        for name, recs in recommendations.items()
    },
}

write_json("09_user_profile_kelly", result)


fig, axs = plt.subplots(1, 2, figsize=(12.0, 4.8))

p_grid = np.linspace(0.05, 0.95, 80)
b_grid = np.linspace(0.5, 8.0, 80)
P, B = np.meshgrid(p_grid, b_grid)
KEL = np.maximum(0, (P * (B + 1) - 1) / B)

cs = axs[0].contourf(P, B, KEL, levels=20, cmap="viridis", alpha=0.8)
contour_lines = axs[0].contour(P, B, KEL, levels=[0.01, 0.05, 0.10, 0.20, 0.40],
                                colors=BRAND["ink"], linewidths=0.8)
axs[0].clabel(contour_lines, inline=True, fontsize=8, fmt=lambda v: f"f*={v*100:.0f}%")

for name, cfg in PERSONAS.items():
    recs = recommendations[name]
    pts = [(r["p"], r["b"]) for r in recs if r["recommend_pct"] > 0.005]
    if pts:
        ps_x, bs_y = zip(*pts)
        axs[0].scatter(ps_x, bs_y, s=20, color=cfg["color"], alpha=0.7,
                       edgecolor="white", linewidths=0.5, label=name)

axs[0].set_xlabel("胜率 p")
axs[0].set_ylabel("盈亏比 b")
axs[0].set_title("Kelly 等高线 + 三画像可投机会散点", pad=8)
axs[0].legend(loc="upper right", fontsize=9)
plt.colorbar(cs, ax=axs[0], label="Kelly 仓位 f*")

names = list(summary.keys())
actionable = [summary[n]["n_actionable"] for n in names]
avg_pct = [summary[n]["avg_recommend_pct"] * 100 for n in names]

x = np.arange(len(names))
ax2 = axs[1].twinx()
b1 = axs[1].bar(x - 0.18, actionable, width=0.34, color=BRAND["blue"], label="可行机会数")
b2 = ax2.bar(x + 0.18, avg_pct, width=0.34, color=BRAND["teal"], label="平均仓位 %")
axs[1].set_xticks(x, names)
axs[1].set_ylabel("可行机会数（200 笔池）", color=BRAND["blue"])
ax2.set_ylabel("平均推荐仓位 %", color=BRAND["teal"])
axs[1].set_title("画像决策：可行机会 × 平均仓位", pad=8)
axs[1].legend(loc="upper left", fontsize=9)
ax2.legend(loc="upper right", fontsize=9)
for i, v in enumerate(actionable):
    axs[1].text(i - 0.18, v + 1, str(v), ha="center", fontsize=9, color=BRAND["blue"])
for i, v in enumerate(avg_pct):
    ax2.text(i + 0.18, v + 0.2, f"{v:.1f}%", ha="center", fontsize=9, color=BRAND["teal"])

fig.suptitle("§4.4 InvestMind 用户画像 × Kelly 行动建议引擎",
             fontsize=13, fontweight="bold", y=1.02, color=BRAND["ink"])
fig.tight_layout()
save_chart(fig, "fig_09_kelly_personas")

print("✓ 09_user_profile_kelly 完成")
