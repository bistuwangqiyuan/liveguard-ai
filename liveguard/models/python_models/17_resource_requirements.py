"""
17_resource_requirements.py
===========================

创立所需资源（自底向上）—— 取代"限定投入资金 + 创始人时间"评估模式。对应 BP §8 创立资源与里程碑。

思路：先穷举把公司做出来需要哪些资源（团队 / 算力 / 数据标注 / 资质牌照 / 平台合作 / 资本），
再由"天使覆盖期（精益跑到 Seed 里程碑）"的资源强度【自底向上倒推天使轮规模】，
而非预设一个投入上限。

输出：
  * 天使覆盖期资源拆解 → 倒推天使轮 ≈ ¥1,000 万（与 data_sources.ROUNDS["Angel"] 校验一致）
  * 5 年人力 / 算力 / 标注 / 资质资源总需求
  * 资金充足性：累计融资 vs 累计资源支出
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from _common import BRAND, PALETTE, fmt_cny, save_chart, write_json
import data_sources as DS

Y = DS.YEARS
n = len(Y)
WAN = 1e4

# ── A. 天使覆盖期（精益）资源 → 倒推天使轮规模 ──────────────────────────────
m = DS.ANGEL_RUNWAY_MONTHS
team_cost = DS.FOUNDING_TEAM_SIZE * DS.FOUNDING_AVG_SALARY_WAN * WAN * (m / 12)
annotation_cost = DS.ANGEL_ANNOTATION_HOURS * DS.ANNOTATION_PRICE_CNY_PER_HOUR
compute_cost = DS.ANGEL_GPU_NODES * DS.GPU_NODE_MONTHLY_CNY * m
license_cost = sum(DS.LICENSE_COSTS_CNY[k] for k in DS.ANGEL_INIT_LICENSE_KEYS)
office_cost = DS.ANGEL_OFFICE_LEGAL_MISC_WAN_PER_MONTH * WAN * m

angel_subtotal = team_cost + annotation_cost + compute_cost + license_cost + office_cost
angel_need = angel_subtotal * (1 + DS.ANGEL_BUFFER)
angel_round = DS.ROUNDS["Angel"]["amount"]

angel_breakdown = {
    "核心团队(12人×9月)": team_cost,
    "数据采集与标注(2.5万小时)": annotation_cost,
    "算力(6 GPU节点×9月)": compute_cost,
    "首程资质(算法备案+增值电信)": license_cost,
    "办公/法务/杂项": office_cost,
}

# ── B. 5 年人力资源与成本 ──────────────────────────────────────────────────
hc_by_dept = DS.HEADCOUNT_PLAN
hc_total = [sum(hc_by_dept[d][t] for d in hc_by_dept) for t in range(n)]
people_cost = [hc_total[t] * DS.AVG_SALARY_WAN[t] * WAN for t in range(n)]

# ── C. 5 年算力 / 标注 / 资质资源 ───────────────────────────────────────────
# 单路年化推理成本曲线（年降 28%）
unit_cost = [DS.UNIT_INFER_COST_Y1 * (1 - DS.UNIT_INFER_COST_YOY_DROP) ** t for t in range(n)]
# 监控路数 ≈ 付费账号 × 平均 3.2 路
avg_paths = 3.2
paths = [DS.CUSTOMERS_EOY[t] * avg_paths for t in range(n)]
compute_year = [paths[t] * unit_cost[t] for t in range(n)]

annot_cum = DS.ANNOTATION_CUM_HOURS
annot_incr = [annot_cum[0]] + [annot_cum[t] - annot_cum[t - 1] for t in range(1, n)]
annot_year = [annot_incr[t] * DS.ANNOTATION_PRICE_CNY_PER_HOUR for t in range(n)]

license_total = sum(DS.LICENSE_COSTS_CNY.values())

# ── D. 资金充足性：累计融资 vs 累计资源支出（人力+算力+标注） ─────────────────
resource_year = [people_cost[t] + compute_year[t] + annot_year[t] for t in range(n)]
cum_resource = np.cumsum(resource_year)
financing_year = np.zeros(n)
for rname, ridx in DS.ROUND_YEAR_INDEX.items():
    financing_year[ridx] += DS.ROUNDS[rname]["amount"]
cum_financing = np.cumsum(financing_year)

payload = {
    "as_of": DS.AS_OF, "currency": "CNY", "version": DS.VERSION,
    "angel_stage": {
        "runway_months": m,
        "breakdown_CNY": {k: round(v, 0) for k, v in angel_breakdown.items()},
        "breakdown_disp": {k: fmt_cny(v) for k, v in angel_breakdown.items()},
        "subtotal_CNY": round(angel_subtotal, 0),
        "buffer_pct": round(DS.ANGEL_BUFFER * 100, 0),
        "derived_angel_need_CNY": round(angel_need, 0),
        "derived_angel_need_disp": fmt_cny(angel_need),
        "angel_round_set_CNY": angel_round,
        "angel_round_set_disp": fmt_cny(angel_round),
        "consistent": bool(abs(angel_need - angel_round) / angel_round < 0.10),
    },
    "headcount_total": hc_total,
    "headcount_by_dept": hc_by_dept,
    "people_cost_yi": [round(x / 1e8, 2) for x in people_cost],
    "compute_unit_cost_CNY": [round(x, 0) for x in unit_cost],
    "monitored_paths": [int(round(x)) for x in paths],
    "compute_cost_yi": [round(x / 1e8, 2) for x in compute_year],
    "annotation_cum_hours": annot_cum,
    "annotation_cost_yi": [round(x / 1e8, 2) for x in annot_year],
    "license_total_CNY": license_total, "license_total_disp": fmt_cny(license_total),
    "license_items_CNY": DS.LICENSE_COSTS_CNY,
    "platform_bd_budget_CNY": DS.PLATFORM_BD_BUDGET_CNY,
    "cum_resource_yi": [round(float(x) / 1e8, 2) for x in cum_resource],
    "cum_financing_yi": [round(float(x) / 1e8, 2) for x in cum_financing],
    "sources": ["自底向上资源清单", "GPU 成本年降 [S-094]", "标注单价行业中位"],
}

print("── 天使覆盖期资源（精益 9 个月）倒推天使轮 ──")
for k, v in angel_breakdown.items():
    print(f"  {k:<26s}{fmt_cny(v)}")
print(f"  小计 {fmt_cny(angel_subtotal)} ×(1+{DS.ANGEL_BUFFER:.0%}) = 需求 {fmt_cny(angel_need)}  → 天使轮设定 {fmt_cny(angel_round)}  一致={payload['angel_stage']['consistent']}")
print("── 5 年资源 ──")
print("  团队人数  :", hc_total)
print("  人力(亿)  :", payload["people_cost_yi"])
print("  算力(亿)  :", payload["compute_cost_yi"])
print("  标注(亿)  :", payload["annotation_cost_yi"])
print(f"  资质合计 {fmt_cny(license_total)} · 平台 BD {fmt_cny(DS.PLATFORM_BD_BUDGET_CNY)}")

write_json("17_resource_requirements", payload)

# ── 图 1：天使资源拆解 + 5 年团队/资金充足性 ────────────────────────────────
fig, axs = plt.subplots(1, 2, figsize=(12.6, 4.8))

# 左：天使覆盖期资源条形
labels = list(angel_breakdown.keys())
vals = [angel_breakdown[k] / WAN for k in labels]
axs[0].barh(labels, vals, color=[BRAND["blue"], BRAND["teal"], BRAND["violet"], BRAND["amber"], BRAND["grey"]], alpha=0.92)
for i, v in enumerate(vals):
    axs[0].text(v + max(vals) * 0.01, i, f"¥{v:.0f}万", va="center", fontsize=9, color=BRAND["ink"])
axs[0].axvline(angel_round / WAN, color=BRAND["red"], ls="--", lw=1.8, label=f"天使轮 {fmt_cny(angel_round)}")
axs[0].set_xlabel("金额 (¥ 万)")
axs[0].set_title(f"天使覆盖期资源 → 倒推 {fmt_cny(angel_need)}", pad=8)
axs[0].legend(fontsize=9)
axs[0].invert_yaxis()

# 右：5 年累计融资 vs 累计资源支出 + 团队规模
ax = axs[1]
ax.bar(Y, [x / 1e8 for x in resource_year], color=BRAND["amber"], alpha=0.55, width=0.55, label="当年资源支出")
ax.plot(Y, payload["cum_resource_yi"], "o-", color=BRAND["red"], lw=2.2, label="累计资源支出")
ax.plot(Y, payload["cum_financing_yi"], "s-", color=BRAND["blue"], lw=2.2, label="累计融资")
ax.set_ylabel("¥ 亿")
axb = ax.twinx()
axb.plot(Y, hc_total, "^--", color=BRAND["teal"], lw=2, label="团队人数")
axb.set_ylabel("团队人数")
ax.set_title("5 年资源支出 vs 融资充足性 + 团队扩张", pad=8)
ax.legend(loc="upper left", fontsize=8.5)
axb.legend(loc="lower right", fontsize=8.5)
fig.suptitle("§8 创立所需资源（自底向上，倒推天使轮）", fontsize=12.5, fontweight="bold", color=BRAND["ink"], y=1.02)
fig.tight_layout()
save_chart(fig, "fig_17_resources")

print("✓ 17_resource_requirements 完成 → JSON + fig_17_resources.png")
