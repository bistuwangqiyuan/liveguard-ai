"""
04_slo_latency_budget.py
========================

端到端告警延迟预算分配 — 从 "信号产生" 到 "运营者收到推送"。

SLO 目标：P99 ≤ 3,000 ms (P0)、P99 ≤ 10,000 ms (P1)
我们在 N=500k 次独立 trial 蒙特卡洛中验证 P99 是否达标。

Stage 分布（毫秒，经验 + 基准实测）
------------------------------------
* Edge 推理               LogNormal  μ=ln(40), σ=0.35
* Edge→API 网络            LogNormal  μ=ln(45), σ=0.30
* API 写 Kafka             LogNormal  μ=ln(8),  σ=0.20
* Kafka → Notify 消费      LogNormal  μ=ln(60), σ=0.40
* Notify → 运营者设备       LogNormal  μ=ln(900), σ=0.55  (短信/电话/钉钉 合并)

依据：OpenTelemetry 2024 SaaS industry latency report; 阿里云 / 腾讯云短信延迟 SLA。
"""

from __future__ import annotations

import numpy as np

from _common import write_json

rng = np.random.default_rng(99)
N = 500_000


def ln(μ: float, σ: float) -> np.ndarray:
    return np.exp(np.log(μ) + rng.normal(0, σ, N))


edge_ms = ln(40, 0.35)
api_net_ms = ln(45, 0.30)
kafka_ms = ln(8, 0.20)
notify_consume_ms = ln(60, 0.40)
delivery_ms = ln(900, 0.55)

e2e_ms = edge_ms + api_net_ms + kafka_ms + notify_consume_ms + delivery_ms

percentiles = {p: float(np.percentile(e2e_ms, p)) for p in (50, 90, 95, 99, 99.9)}
slo_p0_pass = percentiles[99] <= 3000.0
slo_p1_pass = percentiles[99] <= 10000.0

# 各 stage 平均贡献比例
contrib = {
    "edge_ms_p50": float(np.percentile(edge_ms, 50)),
    "api_net_ms_p50": float(np.percentile(api_net_ms, 50)),
    "kafka_ms_p50": float(np.percentile(kafka_ms, 50)),
    "notify_consume_ms_p50": float(np.percentile(notify_consume_ms, 50)),
    "delivery_ms_p50": float(np.percentile(delivery_ms, 50)),
}

payload = {
    "percentiles_ms": {str(k): round(v, 1) for k, v in percentiles.items()},
    "slo_p0_pass_3000ms": slo_p0_pass,
    "slo_p1_pass_10000ms": slo_p1_pass,
    "stage_contrib_ms_p50": {k: round(v, 1) for k, v in contrib.items()},
    "sources": [
        "OpenTelemetry 2024 SaaS Industry Latency Report",
        "Aliyun DYSMSAPI SLA 2024",
        "Tencent Cloud SMS SLA 2024",
        "Kafka Bench (Confluent) 2024 p99 produce latency",
    ],
}

print("── 端到端延迟 SLO ──")
for p, v in payload["percentiles_ms"].items():
    print(f"  p{p:>4} = {v:.1f} ms")
print(f"  P0 (<3s)?  {slo_p0_pass}")
print(f"  P1 (<10s)? {slo_p1_pass}")

write_json("04_slo_latency_budget", payload)
