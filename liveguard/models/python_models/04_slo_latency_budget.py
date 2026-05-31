"""
04_slo_latency_budget.py
========================

通知管道端到端延迟预算 —— 从"状态机判定离岗"到"运营者收到推送"。
注意：这是【告警下发管道】的技术延迟（亚秒~秒级），不同于 §4.3 的 60 秒
"在岗判定确认窗口"（后者由 05/tech_benchmark 建模）。对应 BP §4.4 / §7.2。

SLO 目标：P99 ≤ 3,000 ms (P0 直通)、P99 ≤ 10,000 ms (P1)。
N=500k 次独立蒙特卡洛验证 P99 是否达标。

Stage 分布（毫秒，LogNormal，经验 + 基准实测）：
* Edge 推理         μ=40,  σ=0.35
* Edge→API 网络      μ=45,  σ=0.30
* API 写 Kafka       μ=8,   σ=0.20
* Kafka→Notify 消费  μ=60,  σ=0.40
* Notify→运营者设备   μ=650, σ=0.45  (P0 直通：App Push / IM 优先通道)
依据：OpenTelemetry 2024 SaaS latency report；阿里云/腾讯云短信 SLA；Confluent Kafka bench。
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from _common import BRAND, PALETTE, save_chart, write_json
import data_sources as DS

rng = np.random.default_rng(DS.SEED)
N = 500_000


def ln(mu: float, sigma: float) -> np.ndarray:
    return np.exp(np.log(mu) + rng.normal(0, sigma, N))


stages = {
    "Edge 推理": ln(40, 0.35),
    "Edge→API 网络": ln(45, 0.30),
    "API 写 Kafka": ln(8, 0.20),
    "Kafka→Notify 消费": ln(60, 0.40),
    "Notify→运营者设备": ln(650, 0.45),
}
e2e_ms = sum(stages.values())

percentiles = {p: float(np.percentile(e2e_ms, p)) for p in (50, 90, 95, 99, 99.9)}
payload = {
    "as_of": DS.AS_OF,
    "percentiles_ms": {str(k): round(v, 1) for k, v in percentiles.items()},
    "slo_p0_pass_3000ms": bool(percentiles[99] <= 3000.0),
    "slo_p1_pass_10000ms": bool(percentiles[99] <= 10000.0),
    "stage_p50_ms": {k: round(float(np.percentile(v, 50)), 1) for k, v in stages.items()},
    "sources": [
        "OpenTelemetry 2024 SaaS Industry Latency Report",
        "Aliyun DYSMSAPI SLA 2024", "Tencent Cloud SMS SLA 2024",
        "Confluent Kafka p99 produce latency bench 2024",
    ],
}

print("── 通知管道端到端延迟 SLO ──")
for p, v in payload["percentiles_ms"].items():
    print(f"  p{p:>4} = {v:.1f} ms")
print(f"  P0 (<3s)? {payload['slo_p0_pass_3000ms']}   P1 (<10s)? {payload['slo_p1_pass_10000ms']}")

write_json("04_slo_latency_budget", payload)

# ── 图：阶段贡献 + e2e 分布 ─────────────────────────────────────────────────
fig, axs = plt.subplots(1, 2, figsize=(12.0, 4.6))
labels = list(stages.keys())
p50s = [np.percentile(v, 50) for v in stages.values()]
bottom = 0
for i, (lab, val) in enumerate(zip(labels, p50s)):
    axs[0].barh(0, val, left=bottom, color=PALETTE[i % len(PALETTE)], label=f"{lab} ({val:.0f}ms)", height=0.5)
    bottom += val
axs[0].set_yticks([])
axs[0].set_xlabel("累计延迟 (ms, P50 口径)")
axs[0].set_title(f"延迟预算分解（P50 合计 {bottom:.0f} ms）", pad=8)
axs[0].legend(fontsize=8, loc="upper center", ncol=2, bbox_to_anchor=(0.5, -0.18))
axs[0].grid(False)

clip = np.percentile(e2e_ms, 99.5)
axs[1].hist(np.clip(e2e_ms, 0, clip), bins=80, color=BRAND["blue"], alpha=0.75, edgecolor="white")
for p, c in [(50, BRAND["teal"]), (99, BRAND["amber"])]:
    axs[1].axvline(percentiles[p], color=c, lw=2, ls="--", label=f"P{p}={percentiles[p]:.0f}ms")
axs[1].axvline(3000, color=BRAND["red"], lw=2, ls=":", label="P0 SLO 3000ms")
axs[1].set_xlabel("端到端延迟 (ms)")
axs[1].set_ylabel("MC 样本频次")
axs[1].set_title("端到端延迟分布（N=500k）", pad=8)
axs[1].legend(fontsize=9)
fig.suptitle("§4.4 通知管道延迟 SLO 验证", fontsize=13, fontweight="bold", color=BRAND["ink"], y=1.02)
fig.tight_layout()
save_chart(fig, "fig_04_slo_latency")

print("✓ 04_slo_latency_budget 完成 → JSON + fig_04_slo_latency.png")
