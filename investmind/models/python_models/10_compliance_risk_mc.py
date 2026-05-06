"""
10_compliance_risk_mc.py
========================

合规 / 监管 / 信息披露风险蒙特卡洛 + 24 项风险登记册（Risk Register）。

按 (likelihood × impact) 给出风险热力分；以蒙特卡洛量化关键三大红色风险
对 Y5 ARR / 估值的潜在影响。

---------------------------------------------------------------------------
风险大类 / 关键风险（汇总）
---------------------------------------------------------------------------
1. 合规：投顾资格 / 私募登记 / 广告法 / 信披义务
2. 数据：PIPL / 数据出境 / 数据合作伙伴稳定性
3. 模型：算法歧视、可解释性、生成式 AI 管理办法
4. 商业：竞品低价、平台依赖（流量来源）、客户集中度
5. 运营：人才争夺、关键岗位流失、IT 安全
6. 财务：融资市场冷却、汇率、应收账款
7. 治理：股权分散、员工持股、公司化障碍
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

from _common import BRAND, save_chart, write_json, ci, N_SIM, rng


REGISTER = [
    # (id, name, likelihood 1-5, impact 1-5, owner, mitigation)
    ("R01", "投顾业务无证经营", 2, 5, "CCO",   "申请《证券投资咨询业务资格》；在此之前严格守住「研究/教育」边界"),
    ("R02", "私募基金推介触红线", 2, 5, "CCO",   "禁止推介；只展示评估，落地由用户自行决策"),
    ("R03", "广告法合规", 2, 4, "Legal", "禁止「绝对化」「保证收益」表述；样品库审核"),
    ("R04", "信披与免责声明不全", 2, 4, "Legal", "T+0 报告页底标准免责声明 + 风险等级标"),
    ("R05", "PIPL / 数据安全法", 3, 4, "DPO",   "数据本地化、最小必要、加密存储、季度审计"),
    ("R06", "数据出境受限", 2, 4, "DPO",   "国内独立备份；海外用户单独站点"),
    ("R07", "数据合作伙伴稳定性", 3, 3, "BD",    "至少 5 家数据合作；SLA 触发自动切换"),
    ("R08", "生成式 AI 管理办法", 3, 4, "CCO",   "完成大模型备案；输出二审 + 留存"),
    ("R09", "算法可解释性 / 用户投诉", 3, 3, "PM",    "评估卡可下钻；建立投诉处理流程"),
    ("R10", "竞品低价烧钱", 4, 3, "CFO",   "垂直深度防守；用户 NPS > 60 + 排序引擎护城河"),
    ("R11", "平台依赖（流量来源）", 4, 3, "CMO",   "私域沉淀 + 5 大公域分散"),
    ("R12", "客户集中度（Family）", 3, 3, "CRO",   "Family 客户单一占比 ≤ 10%"),
    ("R13", "人才争夺（量化 + AI 工程）", 4, 4, "VP-People", "ESOP + 两地办公 + 学术合作"),
    ("R14", "关键岗位流失", 3, 4, "VP-People", "Key-person 保险 + 双备份机制"),
    ("R15", "IT 安全 / 渗透", 2, 5, "CISO",  "ISO 27001 / 27701 + 渗透测试"),
    ("R16", "融资市场冷却", 3, 4, "CFO",   "保持 24 个月 Runway；备用债务额度"),
    ("R17", "汇率（美元成本）", 2, 2, "CFO",   "对冲；多元货币付费"),
    ("R18", "应收账款", 2, 2, "CFO",   "Family 预收 + 法务催收"),
    ("R19", "股权分散 / 治理", 2, 3, "Board", "AB 股 / 一致行动协议"),
    ("R20", "员工持股 ESOP 设计", 2, 3, "VP-People", "10-15% 池 + 分批 vest"),
    ("R21", "公司化与海外架构", 2, 3, "CFO",   "VIE 结构预留；境外结构 Cayman"),
    ("R22", "用户投资亏损 / 集体投诉", 3, 4, "Legal", "免责声明 + 风险评级 + 仅作工具"),
    ("R23", "误标 / 评分错误", 2, 4, "PM",    "三审制 + 误标赔付资金池"),
    ("R24", "技术依赖（云 / LLM）", 3, 3, "CTO",   "多云多模型；私有化备份"),
]

risks = [{"id": x[0], "name": x[1], "likelihood": x[2], "impact": x[3],
          "owner": x[4], "mitigation": x[5], "score": x[2] * x[3]}
         for x in REGISTER]
risks_sorted = sorted(risks, key=lambda x: -x["score"])

print(f"── 风险登记册 共 {len(risks)} 项 · Top-5 ──")
for x in risks_sorted[:5]:
    print(f"  [{x['id']}] {x['name']}  L={x['likelihood']}/I={x['impact']}/score={x['score']}")


r = rng()
N = N_SIM

p_no_advisory_license = r.beta(2, 8, N)
p_data_breach = r.beta(1.5, 9, N)
p_genai_filing_delay = r.beta(2, 5, N)

arr_loss_advisory = p_no_advisory_license * r.triangular(0.10, 0.20, 0.40, N)
arr_loss_breach   = p_data_breach * r.triangular(0.05, 0.15, 0.35, N)
arr_loss_genai    = p_genai_filing_delay * r.triangular(0.05, 0.10, 0.20, N)

total_arr_at_risk = 1 - (1 - arr_loss_advisory) * (1 - arr_loss_breach) * (1 - arr_loss_genai)


def stat(s):
    m, lo, hi = ci(s)
    return {"median": float(m), "p5": float(lo), "p95": float(hi)}


result = {
    "as_of": "2026-04-30",
    "register_count": len(risks),
    "register_top10": risks_sorted[:10],
    "register_full": risks,
    "monte_carlo_n": int(N),
    "scenarios": {
        "advisory_license_risk":  stat(arr_loss_advisory),
        "data_breach_risk":       stat(arr_loss_breach),
        "genai_filing_delay":     stat(arr_loss_genai),
        "combined_arr_at_risk":   stat(total_arr_at_risk),
    },
    "p_total_arr_loss_gt_15pct": float(np.mean(total_arr_at_risk > 0.15)),
    "p_total_arr_loss_gt_25pct": float(np.mean(total_arr_at_risk > 0.25)),
}

print("── 三大红色风险蒙特卡洛 → ARR 损失 ──")
print(f"  无证经营触发     : 中位 {result['scenarios']['advisory_license_risk']['median']*100:.1f}%")
print(f"  数据泄露         : 中位 {result['scenarios']['data_breach_risk']['median']*100:.2f}%")
print(f"  生成式 AI 备案延期: 中位 {result['scenarios']['genai_filing_delay']['median']*100:.2f}%")
print(f"  合并 ARR 受损     : 中位 {result['scenarios']['combined_arr_at_risk']['median']*100:.2f}%")
print(f"  P(损失 > 15%)    : {result['p_total_arr_loss_gt_15pct']*100:.1f}%")
print(f"  P(损失 > 25%)    : {result['p_total_arr_loss_gt_25pct']*100:.1f}%")

write_json("10_compliance_risk_mc", result)


fig, axs = plt.subplots(1, 2, figsize=(13.0, 5.4))

heat = np.zeros((5, 5))
for x in risks:
    heat[x["impact"] - 1, x["likelihood"] - 1] += 1

cmap = LinearSegmentedColormap.from_list(
    "rht", ["#F0F4FA", BRAND["amber"], BRAND["red"]]
)
im = axs[0].imshow(heat[::-1], cmap=cmap, aspect="auto", vmin=0, vmax=heat.max())
axs[0].set_xticks(range(5), ["很低", "低", "中", "高", "极高"])
axs[0].set_yticks(range(5), ["极高", "高", "中", "低", "很低"])
axs[0].set_xlabel("发生概率 (Likelihood)")
axs[0].set_ylabel("影响（Impact）")
axs[0].set_title("24 项风险登记册热力图（5 × 5 矩阵）", pad=8)
for i in range(5):
    for j in range(5):
        v = int(heat[4 - i, j])
        if v > 0:
            color = "white" if v >= heat.max() * 0.6 else BRAND["ink"]
            axs[0].text(j, i, str(v), ha="center", va="center",
                        fontsize=11, color=color, fontweight="bold")
plt.colorbar(im, ax=axs[0], label="风险数量")

scenarios = ["投顾资格", "数据泄露", "生成式 AI", "合并损失"]
data = [arr_loss_advisory, arr_loss_breach, arr_loss_genai, total_arr_at_risk]
bp = axs[1].boxplot([d * 100 for d in data], showfliers=False, patch_artist=True,
                     widths=0.55)
for patch, c in zip(bp["boxes"], [BRAND["amber"], BRAND["red"], BRAND["violet"], BRAND["blue"]]):
    patch.set_facecolor(c)
    patch.set_alpha(0.7)

axs[1].set_xticks(range(1, 5), scenarios)
axs[1].set_ylabel("Y5 ARR 受损 %")
axs[1].set_title("三大红色风险 + 合并损失分布（MC）", pad=8)
axs[1].axhline(15, color=BRAND["amber"], lw=1, ls="--", label="15% 警戒线")
axs[1].axhline(25, color=BRAND["red"], lw=1, ls="--", label="25% 应急线")
axs[1].legend(fontsize=9)

fig.suptitle("§10 InvestMind 风险全景图与三大红色风险蒙特卡洛",
             fontsize=13, fontweight="bold", y=1.02, color=BRAND["ink"])
fig.tight_layout()
save_chart(fig, "fig_10_risk")

print("✓ 10_compliance_risk_mc 完成")
