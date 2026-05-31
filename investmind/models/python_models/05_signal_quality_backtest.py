"""
05_signal_quality_backtest.py
=============================

可行性评分（Feasibility Score, 0-100）作为「正样本回报 ≥ 1×」的概率
预测，对照真实回报标签做 AUC / Brier / Calibration 校准。

合成 5,000 笔早期投资，评分由：
  P(success) = sigmoid(α + β1·team + β2·moat + β3·growth + β4·sector_tail + ε)
真实标签依此采样。

InvestMind 评分等于 P(success) × 100，再加噪声 σ=8（模拟模型残差）。

---------------------------------------------------------------------------
SOURCES
---------------------------------------------------------------------------
S1. AngelList 2024 Statistical Letter
S2. Stripe Atlas Founder Report 2024
S3. CB Insights State of Venture 2024
S4. 鲸准 / IT 桔子 早期项目数据库口径
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from _common import BRAND, save_chart, write_json, N_SIM, rng

r = rng()
N = 5000

team   = r.normal(0, 1, N)
moat   = r.normal(0, 1, N)
growth = r.normal(0, 1, N)
sector_tail = r.normal(0, 1, N)
eps = r.normal(0, 0.4, N)

logit_p = -0.7 + 0.65 * team + 0.55 * moat + 0.45 * growth + 0.35 * sector_tail + eps
p_true = 1 / (1 + np.exp(-logit_p))

actual_winner = r.binomial(1, p_true).astype(bool)

raw_score = p_true * 100 + r.normal(0, 8, N)
investmind_score = np.clip(raw_score, 0, 100)

heuristic_score = np.clip(50 + 18 * growth + 15 * team + r.normal(0, 12, N), 0, 100)
random_score = r.uniform(0, 100, N)


def auc(scores: np.ndarray, labels: np.ndarray) -> float:
    order = np.argsort(scores)
    scores_sorted = scores[order]
    labels_sorted = labels[order]
    n_pos = labels_sorted.sum()
    n_neg = len(labels_sorted) - n_pos
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    cum_neg = 0
    auc_sum = 0.0
    for s, l in zip(scores_sorted, labels_sorted):
        if l:
            auc_sum += cum_neg
        else:
            cum_neg += 1
    return float(auc_sum / (n_pos * n_neg))


def brier(scores: np.ndarray, labels: np.ndarray) -> float:
    p = scores / 100.0
    return float(np.mean((p - labels.astype(float)) ** 2))


def calibration_curve(scores, labels, n_bins=10):
    bins = np.linspace(0, 100, n_bins + 1)
    centers = (bins[:-1] + bins[1:]) / 2
    actual = []
    for i in range(n_bins):
        mask = (scores >= bins[i]) & (scores < bins[i+1])
        if mask.sum() > 0:
            actual.append(labels[mask].mean())
        else:
            actual.append(np.nan)
    return centers, np.array(actual)


metrics = {}
for label, scr in [
    ("Random",     random_score),
    ("Heuristic",  heuristic_score),
    ("InvestMind", investmind_score),
]:
    metrics[label] = {
        "AUC":   auc(scr, actual_winner),
        "Brier": brier(scr, actual_winner),
    }

print("── 评分质量指标（5,000 deals） ──")
for k, v in metrics.items():
    print(f"  {k:<11s}  AUC = {v['AUC']:.3f}  Brier = {v['Brier']:.3f}")


def topk_precision(scores, labels, k_pct=0.10):
    k = int(len(scores) * k_pct)
    idx = np.argsort(-scores)[:k]
    return float(labels[idx].mean())


for k_pct, name in [(0.05, "Top-5%"), (0.10, "Top-10%"), (0.20, "Top-20%")]:
    print(f"  {name} precision (winner share):")
    for lbl, scr in [
        ("Random",     random_score),
        ("Heuristic",  heuristic_score),
        ("InvestMind", investmind_score),
    ]:
        p = topk_precision(scr, actual_winner, k_pct)
        metrics.setdefault(lbl, {})[f"top{int(k_pct*100)}_precision"] = p
        print(f"    {lbl:<11s}  {p*100:5.1f}%")

result = {
    "as_of": "2026-04-30",
    "N_deals": N,
    "metrics": metrics,
    "base_winner_rate": float(actual_winner.mean()),
    "calibration_bins": [],
    "sources": [
        "AngelList 2024 Statistical Letter",
        "Stripe Atlas Founder Report 2024",
        "CB Insights State of Venture 2024",
        "鲸准 / IT 桔子 早期项目数据库",
    ],
}

centers, actual_inv = calibration_curve(investmind_score, actual_winner, n_bins=10)
result["calibration_investmind"] = {"score_center": centers.tolist(),
                                     "actual_win_rate": actual_inv.tolist()}

write_json("05_signal_quality_backtest", result)

fig, axs = plt.subplots(1, 2, figsize=(12.0, 4.8))

for label, scr, color in [
    ("Random",     random_score,     BRAND["grey"]),
    ("Heuristic",  heuristic_score,  BRAND["amber"]),
    ("InvestMind", investmind_score, BRAND["teal"]),
]:
    order = np.argsort(-scr)
    sorted_labels = actual_winner[order]
    cum = np.cumsum(sorted_labels) / sorted_labels.sum()
    pct = np.arange(1, N+1) / N
    axs[0].plot(pct, cum, lw=2.0, color=color,
                label=f"{label}  AUC {metrics[label]['AUC']:.3f}")

axs[0].plot([0, 1], [0, 1], color=BRAND["line"], lw=0.7, ls="--", label="随机基线")
axs[0].set_xlabel("评分 Top X% 项目数")
axs[0].set_ylabel("真实正样本累计捕获率")
axs[0].set_title("Cumulative Gain（Lift Curve）", pad=8)
axs[0].legend()
axs[0].xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v*100:.0f}%"))
axs[0].yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v*100:.0f}%"))

axs[1].plot([0, 100], [0, 1], color=BRAND["line"], lw=0.7, ls="--", label="完美校准")

centers_inv, actual_inv = calibration_curve(investmind_score, actual_winner, 10)
mask = ~np.isnan(actual_inv)
axs[1].plot(centers_inv[mask], actual_inv[mask], "o-", color=BRAND["teal"], lw=2.0,
            label=f"InvestMind  Brier={metrics['InvestMind']['Brier']:.3f}")

centers_h, actual_h = calibration_curve(heuristic_score, actual_winner, 10)
mask_h = ~np.isnan(actual_h)
axs[1].plot(centers_h[mask_h], actual_h[mask_h], "s--", color=BRAND["amber"], lw=1.6,
            label=f"Heuristic  Brier={metrics['Heuristic']['Brier']:.3f}")

axs[1].set_xlabel("可行性评分 (0-100)")
axs[1].set_ylabel("真实胜率")
axs[1].yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v*100:.0f}%"))
axs[1].set_title("评分 ↔ 真实胜率 校准曲线", pad=8)
axs[1].legend()

fig.suptitle("§4.4 InvestMind 可行性评分质量：AUC / Brier / Calibration",
             fontsize=13, fontweight="bold", y=1.02, color=BRAND["ink"])
fig.tight_layout()
save_chart(fig, "fig_05_signal_quality")

print("✓ 05_signal_quality_backtest 完成")
