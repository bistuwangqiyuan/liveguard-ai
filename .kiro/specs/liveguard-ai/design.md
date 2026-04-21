# 守播 LiveGuard AI · 系统设计说明书 (Design Document)

> **Spec ID**: `liveguard-ai/design`
> **Version**: v1.0.0
> **Status**: ✅ Approved (Phase 2 of Kiro Spec Workflow)
> **Date**: 2026-04-20
> **Predecessor**: `requirements.md v1.0.0`
> **Successor**: `tasks.md v1.0.0`

---

## 0. 阅读指南

本文档为 `requirements.md` 的工程实现蓝图。每节通过 `Trace` 反向锚定需求 ID。

| 章 | 主题 | 主要 Trace |
|----|------|-----------|
| §1 | 设计原则与约束 | — |
| §2 | 总体架构 (C4 Context/Container) | REQ-SYS-001..010 |
| §3 | 模块分解（monorepo 结构） | 全部 |
| §4 | 数据流 / 时序 / 事件模型 | REQ-SYS-002..006 |
| §5 | 算法子系统 | REQ-ALGO-001..008 |
| §6 | 决策融合状态机详细设计 | REQ-ALGO-007 |
| §7 | 通知子系统 | REQ-SYS-006 |
| §8 | 数据模型与持久化 | REQ-DATA-001..004 |
| §9 | API 设计（OpenAPI 3.1 摘要） | REQ-API-001..003 |
| §10 | 部署、扩缩容、可用性 | REQ-OPS-001..004 |
| §11 | 安全与隐私 | REQ-SEC-001..008 |
| §12 | Web 控制台 | REQ-WEB-001..007 |
| §13 | 移动端 / 桌面端 | REQ-APP-001..003 |
| §14 | 边缘智能盒子 | REQ-EDGE-001..004 |
| §15 | 计费与商业 | REQ-BIZ-001..003 |
| §16 | 可观测性、SRE、混沌工程 | REQ-OPS-* |
| §17 | 测试策略 | DoD §15 |
| §18 | 风险与回退方案 | BP §10 |
| §19 | 决策记录 (ADR Index) | — |

---

## 1. 设计原则 (Design Principles)

### 1.1 核心原则
1. **Privacy by Default**：边缘推理优先；原始视频默认不出客户网络。
2. **Latency First**：P95 端到端 ≤ 60 s；为此采用流式推理 + 事件驱动架构。
3. **Reliability over Cleverness**：决策融合采用确定性 DFSM（非端到端黑盒模型），可解释、可回滚、可审计。
4. **Cost-aware ML**：模型蒸馏 + INT8 量化 + 多任务复用；单卡服 80–120 路 1080p。
5. **Composable Multi-tenant SaaS**：单一控制平面 + 多区域数据平面 + 私有化包同源代码。
6. **Observability is Product**：每条事件可追溯到 model_version、data_snapshot、commit hash。
7. **Compliance as Code**：合规要求体现在 schema、CI 检查、ADR 中，而非仅文档。

### 1.2 工程约束
- **语言**：Python 3.11（算法/后端）｜ TypeScript 5.x（前端/Node 服务）｜ Rust 1.79（边缘高性能模块）｜ Go 1.22（网关/控制器）
- **CI/CD**：GitHub Actions + ArgoCD｜每提交 ≤ 10 min 完成 build+lint+test
- **代码标准**：trunk-based development；feature flag；commit 格式 conventional commits

---

## 2. 总体架构

### 2.1 C4 — System Context（Level 1）

```
                        ┌──────────────────────┐
                        │   监管/审计/合规机构   │
                        └─────────▲────────────┘
                                  │ 报送、审查
   主播 / 直播平台                │
   ┌────────────┐                 │
   │ Live Stream│ ───── RTMP/SRT ─┼────────────► ┌────────────────────────┐
   │ (抖/淘/快/视频号/TikTok/自建)│                │  守播 LiveGuard AI    │ ◄─── B 端用户（MCN/品牌/教培/政务）
   └────────────┘                 │                │  (SaaS + APP + Edge)  │       Web Console / App / API
                                  │                └────────────────────────┘
   消费者 / 观众                   │                       │
   ┌────────────┐                 │     告警/事件         ▼
   │  观众       │ ◄── 直播流 ────┘     ┌────────────────────────┐
   └────────────┘                       │ 通知通道:             │
                                        │ 短信/语音/IM/Webhook/Push │
                                        └────────────────────────┘
```

### 2.2 C4 — Containers（Level 2）

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│                              守播 LiveGuard AI Platform                             │
│                                                                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Web Console  │  │ Mobile App   │  │ Browser Ext. │  │ Desktop Companion    │  │
│  │ (Next.js 14) │  │ (iOS/Android)│  │ (MV3)        │  │ (Electron)           │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────────────┘  │
│         └─────────────────┴──────┬──────────┴──────────────────┘                  │
│                                  │ HTTPS / WSS                                    │
│  ┌───────────────────────────────▼──────────────────────────────────────────────┐ │
│  │                        API Gateway (Envoy + JWT/RBAC)                        │ │
│  └───┬─────────┬─────────┬─────────┬──────────┬─────────┬─────────┬───────────┘ │
│      │         │         │         │          │         │         │             │
│   ┌──▼──┐  ┌───▼───┐  ┌──▼──┐  ┌───▼───┐  ┌───▼───┐  ┌──▼──┐  ┌──▼──┐          │
│   │Auth │  │Tenant │  │Stream│ │Alert  │  │Billing│  │BI   │  │Audit│          │
│   │ svc │  │svc    │  │svc   │ │svc    │  │svc    │  │svc  │  │svc  │          │
│   └──┬──┘  └───┬───┘  └──┬──┘  └───┬───┘  └───┬───┘  └──┬──┘  └──┬──┘          │
│      └─────────┴─────────┴─────────┴──────────┴─────────┴────────┘              │
│                              │                                                    │
│                  ┌───────────┼───────────┐                                       │
│                  ▼           ▼           ▼                                       │
│            ┌─────────┐ ┌──────────┐ ┌──────────┐                                │
│            │PostgreSQL│ │Redis    │ │Kafka     │   (data plane)                 │
│            │+ pgvector│ │(stream  │ │(events)  │                                │
│            │+ RLS    │ │  cache) │ │          │                                │
│            └─────────┘ └──────────┘ └──────────┘                                │
│                                  │                                               │
│  ┌───────────────────────────────▼──────────────────────────────────────────┐   │
│  │  Inference Plane (GPU Cluster)                                           │   │
│  │   Triton Inference Server × N                                            │   │
│  │   ├ Face (SCRFD)                                                         │   │
│  │   ├ Person (YOLOv8s)                                                     │   │
│  │   ├ Re-ID (OSNet)                                                        │   │
│  │   ├ Liveness (Silent-FAS + Deepfake-Detector)                            │   │
│  │   ├ Action (VideoMAE-B)                                                  │   │
│  │   └ Speaker (ECAPA-TDNN) + VAD (Silero)                                  │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                  │                                               │
│  ┌───────────────────────────────▼──────────────────────────────────────────┐   │
│  │  Decision Engine (Stateful, Fault-tolerant)                              │   │
│  │   Per-stream DFSM → emit events → Kafka topic `alerts.v1`                │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                  │                                               │
│  ┌───────────────────────────────▼──────────────────────────────────────────┐   │
│  │  Notification Dispatcher (Workflow engine + retry + escalation)          │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                                                                    │
└────────────────────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ (cross-data plane)
                                  ▼
┌────────────────────────────────────────────────────────────────────────────────────┐
│                       Edge Plane (Customer Premise)                                │
│                                                                                    │
│  ┌──────────────────────────────────────────────────────────────────────────────┐ │
│  │  Edge Agent (Rust + Python ONNXRuntime)                                       │ │
│  │   ├ RTMP/SRT/HLS Ingestor                                                     │ │
│  │   ├ Lightweight Inference (Face + Person + Liveness)                          │ │
│  │   ├ Privacy Filter (face blur, PII masking)                                   │ │
│  │   └ Uplink: only features + events (≤ 1KB/min/stream)                         │ │
│  └──────────────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────────────┘
```

> 上图图形版见 `docs/architecture/system-architecture.png`（GenerateImage 输出）。

### 2.3 C4 — Components（Level 3）— 仅 Stream Service 详细分解

```
                            stream-svc (Python FastAPI)
       ┌───────────────────────────────────────────────────────────────┐
       │  REST handlers (CRUD streams)                                 │
       │     │                                                         │
       │     ▼                                                         │
       │  StreamProvisioner ──► Edge dispatcher ──► Edge agent         │
       │     │                                                         │
       │     ▼                                                         │
       │  StreamMetadataRepo (Postgres)                                │
       │     │                                                         │
       │     ▼                                                         │
       │  EventConsumer (Kafka) ──► StreamStateProjector (Redis)       │
       │     │                                                         │
       │     ▼                                                         │
       │  WSPubSub (broadcast to console / app)                        │
       └───────────────────────────────────────────────────────────────┘
```

---

## 3. 模块分解（Monorepo 结构）

```
liveguard-ai/                              # 仓库根
├── .github/                               # CI/CD workflows
│   └── workflows/{ci.yml, release.yml, codeql.yml}
├── .kiro/specs/liveguard-ai/              # Kiro spec: requirements / design / tasks
├── docs/                                  # 文档
│   ├── architecture/                      # C4 图、ADR
│   ├── runbooks/                          # SRE runbooks
│   └── security/                          # 合规材料
├── algo/                                  # 算法引擎（Python）
│   ├── liveguard_algo/
│   │   ├── face/                          # SCRFD / RetinaFace
│   │   ├── person/                        # YOLOv8 + ByteTrack
│   │   ├── reid/                          # OSNet / TransReID
│   │   ├── liveness/                      # Silent-FAS + Deepfake
│   │   ├── action/                        # VideoMAE
│   │   ├── audio/                         # Silero VAD + ECAPA-TDNN
│   │   ├── fusion/                        # 决策融合 DFSM
│   │   ├── runtime/                       # ONNXRuntime / TensorRT 包装
│   │   ├── pipelines/                     # 端到端 pipeline 编排
│   │   ├── benchmarks/                    # 基准复现
│   │   └── tests/
│   └── pyproject.toml
├── backend/                               # 云端后端（Python FastAPI）
│   ├── liveguard_backend/
│   │   ├── api/                           # REST + WS handlers
│   │   ├── core/                          # 配置、依赖注入
│   │   ├── domain/                        # DDD：tenant/stream/host/alert/billing
│   │   ├── adapters/                      # Postgres / Redis / Kafka / S3
│   │   ├── services/                      # 业务服务
│   │   ├── workers/                       # Celery / Faust 事件消费者
│   │   └── tests/
│   ├── alembic/                           # DB migrations
│   └── pyproject.toml
├── notify/                                # 通知服务（Go）
│   ├── cmd/notify/
│   ├── internal/{channel, escalation, queue, audit}
│   └── go.mod
├── edge/                                  # 边缘 Agent（Rust + Python）
│   ├── crates/                            # Rust：拉流 + 编解码 + IPC
│   │   ├── stream-ingest/
│   │   ├── ipc/
│   │   └── ota/
│   ├── python/                            # 推理 + 上行
│   │   └── liveguard_edge/
│   └── Dockerfile.edge
├── console/                               # Web 控制台（Next.js 14）
│   ├── app/                               # App Router
│   │   ├── (dashboard)/dashboard/
│   │   ├── events/
│   │   ├── settings/
│   │   └── api/                           # BFF
│   ├── components/
│   ├── lib/
│   └── package.json
├── mobile/                                # React Native (Expo)
│   ├── app/
│   └── package.json
├── extension/                             # 浏览器插件（MV3）
│   ├── src/
│   └── manifest.json
├── desktop/                               # Electron 桌面伴侣
├── infra/
│   ├── helm/                              # K8s Helm charts
│   ├── terraform/                         # Aliyun / AWS modules
│   ├── docker-compose.yml                 # 一键本地
│   └── argocd/
├── models/                                # 财务/市场 BP 模型
│   ├── data_sources.py
│   ├── market_sizing.py
│   ├── pricing_model.py
│   ├── unit_economics.py
│   ├── financial_projections.py
│   ├── valuation_dcf.py
│   ├── monte_carlo_valuation.py
│   ├── tech_benchmark.py
│   └── run_all.py
├── tools/                                 # CLI 工具
├── examples/                              # 示例代码、SDK demo
├── package.json                           # workspaces 根
├── pnpm-workspace.yaml
├── pyproject.toml                         # 根（共享 dev deps）
├── README.md
└── LICENSE
```

---

## 4. 数据流与时序

### 4.1 端到端数据流（Edge-Cloud 模式）

```
1. Edge Agent (T0)
   ├ Pull RTMP stream
   ├ Decode (FFmpeg)
   ├ Sample @ 5 fps
   ├ Run light models: Face / Person / Liveness
   ├ Privacy filter (face blur)
   └ Emit Feature Frame (1 KB) every 200 ms
       │
       ▼ HTTPS/MQTT (compressed)
2. Backend gRPC Ingestor (T0 + 50 ms)
   └ Push to Kafka topic `streams.features.v1`
       │
       ▼
3. Inference Plane Workers (T0 + 80 ms)
   ├ Re-ID / Action / Speaker (heavy models)
   └ Push to Kafka topic `streams.signals.v1`
       │
       ▼
4. Decision Engine (T0 + 110 ms)
   ├ Per-stream DFSM
   ├ Apply hysteresis
   └ Emit transition events to `streams.events.v1`
       │
       ▼
5. Notification Dispatcher (T0 + 200 ms)
   ├ Lookup alert policy
   ├ Resolve on-call roster
   ├ Fan-out to channels
   └ Track acknowledgement
       │
       ▼
6. Console / App (T0 + 600 ms WS push)
```

> 端到端从"主播离开镜头"到"通知落地"目标 ≤ 60 s（含 60 s 状态机阈值）；技术延迟 ≤ 1 s。

### 4.2 关键时序图（UML）

#### 4.2.1 主播离岗告警链路

```
Host  Edge   Cloud-Inf  Cloud-Decision  Notify  WS-Console  Operator
 │     │         │          │              │       │           │
 │ leaves seat                                                   │
 │────►│ T+0s   no-face                                          │
 │     │ no-face / no-person                                     │
 │     │────►│  speaker silent                                   │
 │     │     │────►│  fusion score 0.20                          │
 │     │     │     │  state: BRIEF_AWAY                          │
 │     │     │     │  (T+5s, no alert yet)                       │
 │     │     │────►│  ... 60s elapsed ...                        │
 │     │     │     │  state: LONG_AWAY                           │
 │     │     │     │  emit ALERT P1 ───►│                        │
 │     │     │     │                    │ resolve policy         │
 │     │     │     │                    │ send IM bot ───────────►ack
 │     │     │     │                    │ (no ack 60s)           │
 │     │     │     │                    │ escalate SMS+Phone     │
 │     │     │     │                    │                        │
 │     │     │     │  state: ALERT_ESC. │                        │
 │     │     │     │  emit ALERT P0 ───►│                        │
 │     │     │     │                    │  push WS ─────────────►Console blink
```

### 4.3 事件模型（Event Schema v1）

CloudEvents 1.0 + 守播扩展。

```jsonc
{
  "specversion": "1.0",
  "id": "evt_01HV8X9Y2J6Z3K1A4B5C6D7E8F",          // ULID
  "source": "lvg://tenant/{tenant_id}/stream/{stream_id}",
  "type": "lvg.alert.host_offline.v1",                // 事件类型
  "subject": "stream/{stream_id}",
  "time": "2026-04-20T14:30:12.345Z",
  "datacontenttype": "application/json",
  "data": {
    "tenant_id": "t_001",
    "stream_id": "s_abc",
    "host_id": "h_zhang",
    "platform": "douyin",
    "severity": "P1",
    "state_transition": { "from": "BRIEF_AWAY", "to": "LONG_AWAY" },
    "duration_offline_s": 60,
    "fusion_score": 0.18,
    "signal_breakdown": {
      "face": 0.05, "person": 0.10, "reid": 0.0,
      "liveness": 0.0, "action": 0.40, "audio": 0.20
    },
    "model_versions": {
      "face": "scrfd-2.5g@v1.4",
      "person": "yolov8s@v3.0",
      "reid": "osnet-x1.0@v2.1",
      "liveness": "silent-fas@v1.2",
      "action": "videomae-b@v1.0",
      "speaker": "ecapa-tdnn@v1.5"
    },
    "evidence": {
      "clip_uri": "s3://lvg-evidence/t_001/s_abc/2026-04-20/14-30-12.mp4",
      "thumbnail_uri": "s3://...",
      "expires_at": "2026-05-20T14:30:12Z"
    }
  },
  "extensions": {
    "lvgsignature": "sha256=...",                     // HMAC for downstream
    "traceid": "00-4bf92f...",
    "spanid": "00f067aa..."
  }
}
```

事件类型清单：
| Type | 含义 | 严重级 |
|------|------|--------|
| `lvg.host.online.v1` | 主播上线 | INFO |
| `lvg.host.offline.v1` | 主播离开（首次进入 BRIEF_AWAY）| INFO |
| `lvg.alert.host_offline.v1` | 升级到 LONG_AWAY | P1 |
| `lvg.alert.host_offline_escalated.v1` | 升级到 ALERT_ESCALATED | P0 |
| `lvg.alert.cheat_detected.v1` | 反作弊触发 | P0/P1（看类别）|
| `lvg.alert.drowsy.v1` | 主播打瞌睡 | P2 |
| `lvg.health.stream_lost.v1` | 流断 | P1 |
| `lvg.health.edge_offline.v1` | 边缘离线 | P1 |

---

## 5. 算法子系统设计

### 5.1 模型注册表 (Model Registry)

每个模型在 `algo/liveguard_algo/runtime/registry.py` 注册：

```python
@register_model(
  name="face.scrfd",
  version="2.5g-v1.4",
  framework="onnx",
  hash_sha256="ab12...",
  input_spec=(("image", (1,3,640,640), "f32"),),
  output_spec=(("bboxes", (-1,5), "f32"), ("landmarks", (-1,5,2), "f32")),
  inference_target=["edge:rk3588", "edge:j5", "cloud:t4"],
  benchmark={"latency_ms_p95": 12.1, "precision": 0.982, "recall": 0.975},
  license="Apache-2.0",
  data_lineage="datasets/widerface_v1.json"
)
class SCRFDFaceDetector(BaseDetector): ...
```

模型元数据自动写入 `model_registry` 表（Postgres），用于审计与回滚。

### 5.2 推理 Pipeline（Cloud）

```
Frame batch (16) ─► Triton (dynamic batching, INT8)
                      ├ face → landmarks
                      ├ person → keypoints + tracks
                      └ liveness (cropped face)
                  ─► RingBuffer (5s window)
                  ─► reid (per-track embeddings, every 1s)
                  ─► action (16-frame clip every 2s)
                  ─► audio worker (chunk 1s) → vad + speaker
                  ─► signal aggregator → SignalFrame (per stream, per 200ms)
                  ─► Decision Engine
```

### 5.3 推理 Pipeline（Edge）

```
RTMP/SRT input
  ├ FFmpeg decode (HW: rkmpp / nvdec / VPU)
  ├ Frame sampler (5 fps)
  ├ Face (SCRFD-2.5g INT8 on NPU)
  ├ Person (YOLOv8s INT8 on NPU)
  ├ Liveness (Silent-FAS INT8 on NPU)
  ├ Privacy filter (Gaussian blur non-host faces)
  └ Feature uplink (MQTT QoS 1, batched 5s)
```

### 5.4 模型部署形态对比

| 模型 | Edge (NPU) | Cloud (GPU) | Bandwidth Trade-off |
|------|-----------|-------------|---------------------|
| Face | ✅ INT8 | ✅ FP16 batch | 0 frames uploaded |
| Person | ✅ INT8 | ✅ | 0 |
| Re-ID | ⚠️ optional | ✅ | embeddings only |
| Liveness | ✅ INT8 | ✅ | 0 |
| Action | ❌ (heavy) | ✅ FP16 | clip features 16-frame embedding |
| Speaker | ⚠️ optional | ✅ | audio embedding |

> 决策：边缘默认跑 Face/Person/Liveness（隐私敏感），云端补全 Re-ID/Action/Speaker（性能敏感）。

---

## 6. 决策融合状态机详细设计

### 6.1 形式化定义

```
M = (Q, Σ, δ, q₀, F)

Q = {IDLE, ON_DUTY, BRIEF_AWAY, LONG_AWAY, ALERT_ESCALATED, CHEAT_FLAGGED}
Σ = SignalFrame ∈ ℝ⁶  (face, person, reid, liveness, action, audio) ∈ [0,1]⁶
q₀ = IDLE
F  = ∅ (终态：无；持续状态机)

S = w · Σ,  w = (0.30, 0.20, 0.20, 0.10, 0.10, 0.10), Σwᵢ = 1
```

### 6.2 状态转移表

| 当前 | Trigger | 下一 | Action |
|------|---------|------|--------|
| IDLE | stream first frame | ON_DUTY (if S≥0.65) | log online |
| ON_DUTY | S < 0.35 持续 5s | BRIEF_AWAY | start away timer |
| ON_DUTY | reid_diff < 0.55 持续 10s | CHEAT_FLAGGED | emit cheat |
| BRIEF_AWAY | S ≥ 0.65 持续 5s | ON_DUTY | clear timer |
| BRIEF_AWAY | timer ≥ 60s | LONG_AWAY | emit P1 |
| LONG_AWAY | S ≥ 0.65 持续 5s | ON_DUTY | resolve |
| LONG_AWAY | timer ≥ 120s (累计 180s 离开) | ALERT_ESCALATED | emit P0 |
| ALERT_ESCALATED | S ≥ 0.65 持续 10s | ON_DUTY | resolve, close ticket |
| CHEAT_FLAGGED | manual_clear by operator | ON_DUTY | log review |

### 6.3 反作弊子状态机

并发于主状态机，独立判定：
```
                 face_in_frame     no_motion        liveness_low
                     │                 │                 │
                     ▼                 ▼                 ▼
              SUSPECT_PHOTO    SUSPECT_LOOPED    SUSPECT_DEEPFAKE
                     │                 │                 │
                     └─────────┬───────┴────────┬────────┘
                               ▼                ▼
                        evidence collector → CHEAT_FLAGGED
```

### 6.4 抗抖动（Hysteresis）
- 边界缓冲：`upper=0.65`, `lower=0.35`，中间 [0.35, 0.65] 维持原状态。
- 时间常数：进入 ON_DUTY 需 5s 累积；进入 AWAY 需 5s 累积；防止瞬时遮挡误触发。
- 信号置信度过滤：单信号 confidence < 0.3 时该信号权重折半，重新归一。

### 6.5 可解释性
- 每次状态转移持久化 `state_transition_log`：`stream_id, from, to, ts, signals[6], score, model_versions, frame_uri`。
- API `/v1/streams/{id}/explain?event_id=...` 返回 SHAP 风格加权贡献。

### 6.6 实现要点（伪代码）
```python
class StreamFSM:
    def __init__(self, weights=DEFAULT_W, thresholds=DEFAULT_TH):
        self.state = "IDLE"
        self.timer = 0
        self.score_buf = RingBuf(size=25)  # 5s @ 5fps
        ...
    def feed(self, signals: SignalFrame, dt: float) -> Optional[Event]:
        score = sum(w*s for w,s in zip(self.weights, signals))
        self.score_buf.push(score)
        avg = self.score_buf.mean()
        return self._transition(avg, signals, dt)
```

---

## 7. 通知子系统

### 7.1 架构
```
events ─► Kafka ─► Notification Worker (Go)
                    ├ AlertPolicyResolver (per tenant)
                    ├ OnCallScheduler (rotation, holidays)
                    ├ ChannelAdapter
                    │   ├ TwilioSMS / 阿里云短信
                    │   ├ TwilioVoice / 腾讯云语音
                    │   ├ Feishu Bot / DingTalk Bot / WeCom
                    │   ├ APNs / FCM
                    │   └ Webhook (HMAC-signed)
                    └ DeliveryTracker (Redis + audit log)
```

### 7.2 通知策略 DSL（YAML）
```yaml
policy: default-pro
match:
  severity: [P1, P0]
  event_type: [lvg.alert.*]
escalation:
  - channels: [in_app, feishu_bot]
    wait: 60s
  - channels: [sms]
    wait: 120s
  - channels: [voice_call]
    repeat: 3
silent_window:
  - cron: "0 2-7 * * *"
    suppress_severity: [P1]
on_call:
  rotation: weekly
  members: [u_alice, u_bob, u_charlie]
```

### 7.3 可靠投递
- At-least-once：Kafka offset commit after delivery ack。
- Idempotency：HMAC-signed `X-LiveGuard-Event-Id` ULID。
- DLQ：3 次失败入死信队列；7 天内自动重试。

---

## 8. 数据模型与持久化

### 8.1 关键表（Postgres + RLS）

```sql
-- Tenant
CREATE TABLE tenants (
  id          UUID PRIMARY KEY,
  name        TEXT NOT NULL,
  tier        TEXT NOT NULL CHECK (tier IN ('starter','pro','enterprise')),
  region      TEXT NOT NULL DEFAULT 'cn-north',
  created_at  TIMESTAMPTZ DEFAULT now(),
  status      TEXT NOT NULL DEFAULT 'active'
);

-- User
CREATE TABLE users (
  id          UUID PRIMARY KEY,
  tenant_id   UUID NOT NULL REFERENCES tenants(id),
  email       CITEXT UNIQUE NOT NULL,
  password_hash TEXT,
  role        TEXT NOT NULL DEFAULT 'viewer',
  mfa_secret  TEXT,
  created_at  TIMESTAMPTZ DEFAULT now()
);
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
CREATE POLICY users_isolation ON users
  USING (tenant_id = current_setting('app.tenant_id')::uuid);

-- Host (主播)
CREATE TABLE hosts (
  id           UUID PRIMARY KEY,
  tenant_id    UUID NOT NULL REFERENCES tenants(id),
  display_name TEXT NOT NULL,
  face_embedding   vector(512),    -- pgvector
  voice_embedding  vector(192),
  consent_token    TEXT NOT NULL,  -- SHA256(consent doc)
  consent_at       TIMESTAMPTZ NOT NULL,
  status       TEXT DEFAULT 'active',
  created_at   TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX ON hosts USING ivfflat (face_embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX ON hosts USING ivfflat (voice_embedding vector_cosine_ops);

-- Stream
CREATE TABLE streams (
  id          UUID PRIMARY KEY,
  tenant_id   UUID NOT NULL REFERENCES tenants(id),
  host_id     UUID REFERENCES hosts(id),
  platform    TEXT NOT NULL,
  ingest_url  TEXT NOT NULL,
  ingest_protocol TEXT,
  edge_id     UUID REFERENCES edges(id),
  state       TEXT DEFAULT 'IDLE',
  policy_id   UUID REFERENCES alert_policies(id),
  metadata    JSONB,
  created_at  TIMESTAMPTZ DEFAULT now()
);

-- Event
CREATE TABLE events (
  id          UUID PRIMARY KEY,
  tenant_id   UUID NOT NULL REFERENCES tenants(id),
  stream_id   UUID NOT NULL REFERENCES streams(id),
  type        TEXT NOT NULL,
  severity    TEXT NOT NULL,
  payload     JSONB NOT NULL,
  evidence_uri TEXT,
  occurred_at TIMESTAMPTZ NOT NULL,
  created_at  TIMESTAMPTZ DEFAULT now()
) PARTITION BY RANGE (occurred_at);
-- 月分区：events_2026_04 ...
CREATE INDEX ON events (tenant_id, occurred_at DESC);
CREATE INDEX ON events USING gin (payload);

-- Alert Policy
CREATE TABLE alert_policies (
  id          UUID PRIMARY KEY,
  tenant_id   UUID NOT NULL REFERENCES tenants(id),
  name        TEXT,
  yaml_dsl    TEXT NOT NULL,
  enabled     BOOLEAN DEFAULT true
);

-- Edge
CREATE TABLE edges (
  id          UUID PRIMARY KEY,
  tenant_id   UUID NOT NULL REFERENCES tenants(id),
  serial_no   TEXT UNIQUE,
  hardware    TEXT,                 -- rk3588 / j5 / ascend310b
  firmware_version TEXT,
  last_heartbeat_at TIMESTAMPTZ,
  status      TEXT
);

-- Audit Log (WORM, append-only)
CREATE TABLE audit_logs (
  id          BIGSERIAL PRIMARY KEY,
  tenant_id   UUID,
  actor       TEXT,
  action      TEXT NOT NULL,
  resource    TEXT,
  payload     JSONB,
  hash        TEXT NOT NULL,           -- SHA256(prev_hash || row)
  created_at  TIMESTAMPTZ DEFAULT now()
);

-- Billing meter
CREATE TABLE meter_records (
  id           BIGSERIAL PRIMARY KEY,
  tenant_id    UUID NOT NULL,
  metric       TEXT NOT NULL,           -- stream_hours / alert_count / api_calls / ...
  qty          NUMERIC NOT NULL,
  occurred_at  TIMESTAMPTZ NOT NULL,
  created_at   TIMESTAMPTZ DEFAULT now()
);

-- Model Registry
CREATE TABLE model_versions (
  id            UUID PRIMARY KEY,
  name          TEXT NOT NULL,
  version       TEXT NOT NULL,
  framework     TEXT,
  artifact_uri  TEXT,
  metrics       JSONB,
  data_lineage  JSONB,
  released_at   TIMESTAMPTZ,
  UNIQUE(name, version)
);
```

### 8.2 时序数据
- 流状态时间序列：写入 ClickHouse / TimescaleDB（hypertable on `(tenant_id, stream_id, ts)`）。
- 用于实时大屏、报表、SLA 计算。

### 8.3 对象存储
- 证据（evidence clip）：S3-compatible（MinIO / OSS / S3）。
- 路径：`s3://lvg-evidence/{tenant_id}/{stream_id}/{yyyy}/{mm}/{dd}/{event_id}.mp4`
- TTL 默认 30 天（Pro）/ 365 天（Enterprise）；服务端加密 SSE-KMS。

### 8.4 缓存（Redis）
- Per-stream state cache: `stream:state:{id}` (TTL 60s)
- Tenant config cache: `tenant:cfg:{id}` (TTL 5 min, invalidate on update)
- Rate limiting: token bucket per tenant.

---

## 9. API 设计

### 9.1 OpenAPI 摘要

```yaml
openapi: 3.1.0
info:
  title: LiveGuard AI Public API
  version: 1.0.0
servers:
  - url: https://api.liveguard.ai/v1
security:
  - bearerAuth: []
paths:
  /auth/token:
    post: { summary: "Obtain JWT", security: [], requestBody: {$ref: '#/components/requestBodies/Login'} }
  /tenants/{tid}/streams:
    get:    { summary: "List streams" }
    post:   { summary: "Create stream", requestBody: {$ref: '#/components/requestBodies/StreamCreate'} }
  /tenants/{tid}/streams/{sid}:
    get:    { summary: "Get stream details" }
    delete: { summary: "Delete stream" }
  /tenants/{tid}/streams/{sid}/events:
    get:    { summary: "List events", parameters: [from, to, type, severity, page, size] }
  /tenants/{tid}/hosts:
    post:   { summary: "Enroll host (multipart: photos+audio)" }
  /tenants/{tid}/alert-policies:
    post:   { summary: "Create alert policy", requestBody: {$ref: '#/components/requestBodies/PolicyDSL'} }
  /tenants/{tid}/billing/usage:
    get:    { summary: "Get usage (meter records aggregated)" }
  /streams/{sid}/explain:
    get:    { summary: "Get fusion explanation for event" }
  /sdk/edge/heartbeat:
    post:   { summary: "Edge agent heartbeat (JWT issued by activation token)" }
  /webhook/admin:
    post:   { summary: "Admin webhook configuration" }
components:
  securitySchemes:
    bearerAuth: { type: http, scheme: bearer, bearerFormat: JWT }
```

完整 OpenAPI 规范在 `backend/liveguard_backend/api/openapi.yaml`。

### 9.2 WebSocket 协议
```
URL: wss://api.liveguard.ai/v1/streams/subscribe
Auth: ?token=<JWT>
Subscribe message:
  {"action":"subscribe","streams":["s_abc","s_def"]}
Server push:
  {"type":"event","payload": <CloudEvents JSON>}
Heartbeat: ping/pong every 20s; server disconnects after 45s no pong.
```

### 9.3 SDK 设计
- Python：`liveguard` (Apache-2.0) — 同步 + 异步 client、自动重试、type hints。
- TS/JS：`@liveguard/sdk` — Tree-shakable，浏览器/Node 同包。
- Go/Java/PHP：generated from OpenAPI via `openapi-generator-cli`。

---

## 10. 部署、扩缩容、可用性

### 10.1 拓扑
- **Region 1（华北 / Default）**：阿里云北京/张家口（GPU 大集群）。
- **Region 2（华东）**：阿里云杭州（控制平面备份 + 直播热点）。
- **Region 3（合规 / 政务）**：华为云乌兰察布（信创栈 + 国密）。
- **Region Overseas**：AWS Singapore（东南亚）、AWS Tokyo（日韩）。

### 10.2 K8s 资源规划（Y3 末参考）
| Component | Pods | CPU/Pod | RAM/Pod | GPU/Pod |
|-----------|----:|--------:|--------:|--------:|
| api-gateway (Envoy) | 12 | 2 | 4 GB | — |
| backend services | 60 (10 svc × 6) | 2 | 4 GB | — |
| inference workers | 200 | 8 | 32 GB | 1 × A10 |
| decision-engine | 40 | 4 | 8 GB | — |
| notify | 24 | 2 | 4 GB | — |
| stream-ingest | 80 | 4 | 8 GB | — |
| postgres (HA) | 3 (RDS managed) | 16 | 128 GB | — |
| redis-cluster | 6 | 8 | 32 GB | — |
| kafka | 9 | 8 | 32 GB | — |
| clickhouse | 6 | 16 | 64 GB | — |
| object-storage | OSS managed | — | — | — |

### 10.3 水平扩缩容
- HPA：基于 GPU utilization、Kafka lag、HTTP RPS。
- Inference Workers：自定义 metrics adapter（Prometheus → KEDA）。
- 预热：流量预测（每周日训练 LightGBM 预测 7×24 流量曲线）→ pre-scale 30 min ahead。

### 10.4 可用性
- 多 AZ：每个 region 至少 3 AZ。
- Postgres：主备 + 同步流复制 + 跨 region 异步复制。
- Kafka：3 副本 + min.insync.replicas=2。
- 蓝绿部署：API 网关支持金丝雀发布。

### 10.5 灾备演练
- 季度 DR drill：模拟 region 失效，目标 RTO < 60s（Enterprise tier）。
- 测试覆盖率：每年至少 4 次完整切换（含数据库故障转移、Kafka rebalance）。

---

## 11. 安全与隐私

### 11.1 网络安全
- WAF（阿里云 WAF / Cloudflare）+ 云盾 DDoS。
- 内部服务通信 mTLS（SPIFFE / SPIRE）。
- 零信任：所有内部 API 携带 service identity (workload SPIFFE ID) + tenant context.

### 11.2 密钥管理
- KMS：阿里云 KMS / AWS KMS / 自托管 Vault。
- 密钥层级：根密钥（HSM）→ Tenant KEK → DEK（per-record）。
- 旋转策略：DEK 90 天，KEK 365 天。

### 11.3 数据治理
- DPO 系统：自动数据 inventory；DPIA 模板；删除请求 SLA 24h（个人数据）。
- 可解释审计：每个推理可回溯 (model_version, dataset_snapshot, git_commit)。

### 11.4 算法伦理
- AI 伦理委员会季度评审：偏见审计报告、敏感场景使用审批。
- 公平性指标：FAR/FNR by gender/age/skin-tone group；阈值告警。

### 11.5 合规清单（与 §11 requirements 完整映射）
完整清单见 `docs/security/compliance-matrix.xlsx`。

---

## 12. Web 控制台设计

### 12.1 技术栈
- Next.js 14 (App Router) + React 18 + TypeScript 5.x
- UI: Tailwind CSS + shadcn/ui + Radix Primitives
- 状态：TanStack Query + Zustand
- 实时：原生 WebSocket（自封装 hooks）+ React Server Components 边缘流式
- 图表：Visx + ECharts（重场景）
- Auth：NextAuth.js + 自有 OIDC

### 12.2 关键页面
- `/dashboard`：实时 64 路监控墙（虚拟滚动 + WebGL Canvas 重绘减少抖动）
- `/streams`：流管理 CRUD
- `/events`：事件中心（Server-side 分页 + 高级过滤 + Saved view）
- `/hosts`：主播注册（多步 wizard，含同意书签署）
- `/policies`：告警策略可视化编辑（YAML + Schema-driven form）
- `/billing`：使用量、账单、ROI 计算器
- `/settings`：租户、用户、RBAC、SSO、API Keys

### 12.3 设计语言
- 12-列网格、4/8/16 px spacing、深色优先（监控场景）
- 配色：主 `#0EA5E9`（cyan-500）+ 警示 `#EF4444` + 成功 `#10B981`
- 响应式断点：`sm:640 / md:768 / lg:1024 / xl:1280 / 2xl:1536 / 4k:2560`

### 12.4 性能目标
- LCP < 1.5 s（3G fast）
- TTI < 3 s
- 64 路并行实时刷新 CPU 使用 < 30%（M1 Pro）

---

## 13. 移动端 / 桌面端

### 13.1 React Native (Expo) 跨平台
- 推送：APNs (iOS) / FCM (Android) / 极光（CN fallback）
- 离线：MMKV 本地缓存
- 视频：react-native-vlc-media-player（RTMP 拉流）

### 13.2 浏览器插件 (MV3)
- 内容脚本注入抖音/淘宝/快手/视频号直播间页面
- 仅请求 `activeTab` 权限，不收集用户数据
- 通过插件后台 Service Worker 与 LiveGuard API 通信

### 13.3 Electron 桌面伴侣
- 本地 ONNXRuntime（轻量模型）
- 屏幕录制：Win Graphics Capture API / macOS ScreenCaptureKit
- 跟随系统休眠唤醒；崩溃恢复

---

## 14. 边缘智能盒子

### 14.1 硬件抽象层（HAL）
```
       ┌──────────────────────────────┐
       │ Edge Agent (Rust core)        │
       └───────────┬───────────────────┘
                   │ ONNXRuntime EP API
       ┌───────────▼──────────────────┐
       │ EP Plugins                   │
       │  ├ ROCmEP (AMD)              │
       │  ├ TensorRT (Nvidia)         │
       │  ├ NPU-Ascend (Huawei)       │
       │  ├ NPU-Cambricon (MLU)       │
       │  ├ NPU-Horizon (J5)          │
       │  └ NPU-Rockchip (RK3588)     │
       └──────────────────────────────┘
```

### 14.2 OTA
- Mender / SWUpdate 两套备选；签名 Ed25519；A/B partition + 自动回滚。
- Bandwidth efficient: bsdiff delta packages.

### 14.3 安全启动
- TPM/TEE：保存设备身份与密钥。
- 启动校验链：bootloader → kernel → rootfs 全签名。

---

## 15. 计费与商业

### 15.1 计量
- 计量来源：Stream service 写入 `meter_records`；Notification service 写入 SMS/Voice 计量。
- 聚合：每日 cron → `daily_aggregates`；每月生成账单 PDF。

### 15.2 定价对接
- Stripe（国际）：subscription + usage-based add-on。
- 支付宝/微信支付：周期订阅；增值税专票通过财税服务商（百望/航信）。

### 15.3 ROI 计算器
公式（来自 BP §5.5）：
```python
def compute_roi(daily_gmv, offline_loss_rate=0.09, fine_rate=0.025,
                save_offline_pct=0.7, save_fine_pct=0.84,
                tool_annual_fee=7188, broadcast_days=300):
    annual_gmv = daily_gmv * broadcast_days
    current_loss = annual_gmv * (offline_loss_rate + fine_rate)
    after_loss   = annual_gmv * (offline_loss_rate*(1-save_offline_pct) +
                                 fine_rate*(1-save_fine_pct))
    annual_save  = current_loss - after_loss
    roi          = (annual_save - tool_annual_fee) / tool_annual_fee
    payback_days = tool_annual_fee / (annual_save / broadcast_days)
    return {"annual_save": annual_save, "roi": roi, "payback_days": payback_days}
```

---

## 16. 可观测性、SRE、混沌工程

### 16.1 三大支柱
- **Metrics**: Prometheus + VictoriaMetrics（长存储）+ Grafana
- **Logs**: ELK + Loki（结构化日志统一 traceid）
- **Traces**: OpenTelemetry → Tempo / Jaeger

### 16.2 SLO 板
| Service | SLO | Error Budget |
|---------|-----|-------------|
| API Gateway | 99.95% availability | 21.9 min/月 |
| Decision Engine | 99.9% availability + p95 latency < 200ms | 43.8 min/月 |
| Notification | 99.9% delivery within 5s | 43.8 min/月 |
| Inference Worker | 99.5% job success | 3.6 h/月 |

### 16.3 混沌工程
- LitmusChaos / ChaosMesh
- 季度演练：随机杀 Pod、网络分区、磁盘满、GPU OOM。

### 16.4 On-Call
- PagerDuty + 钉钉/飞书机器人；7×24 NOC（北京 + 杭州）。
- Runbook 强制：每个 P1+ alert 必须关联 runbook 链接。

---

## 17. 测试策略

### 17.1 测试金字塔
| 层 | 工具 | 占比 | 命中目标 |
|----|------|-----|---------|
| Unit | pytest / vitest | 70% | 单函数边界 |
| Component | pytest+httpx / @testing-library | 20% | 单服务 |
| Integration | testcontainers + docker-compose | 7% | 跨服务 |
| E2E | Playwright | 3% | 真实浏览器流程 |
| Load | k6 / Locust | — | 200k 流并发 |
| Chaos | LitmusChaos | — | 故障演练 |

### 17.2 算法专项测试
- 黄金集（10 万段标注视频）：每发布运行 P/R/F1/FAR/FNR
- A/B 在线：5%→25%→100% 灰度，监控 NRR、误报投诉率
- 难例集：人工 +主动学习贡献的 5,000 段持续扩充

### 17.3 安全测试
- SAST: Semgrep + ESLint security
- DAST: OWASP ZAP nightly
- SCA: Trivy + Snyk
- IaC: Checkov + tfsec
- Secrets: gitleaks pre-commit

### 17.4 合规测试
- DPIA 自动生成报告；`pytest-bdd` 编写合规场景：例如"撤销同意 → 24 小时内删除"

---

## 18. 风险与回退方案

### 18.1 算法回退
- 每模型双版本部署；客户级 model_version pin；一键回滚 < 5 min。
- Fallback 路径：Heavy 模型超时 → Light 版本 → 规则脚本（保底）

### 18.2 Vendor Lock-in 缓解
- 云抽象层：DB（Postgres）/ Cache（Redis 协议）/ Object（S3 协议）/ Queue（Kafka 协议）— 全部开放协议
- 多云：阿里云 + 华为云 + 腾讯云 + AWS

### 18.3 监管风险
- 私有化包同源代码，6 周可交付政务版本。
- 国密栈（SM2/SM3/SM4）作为可插拔 crypto provider。

---

## 19. ADR Index（Architecture Decision Records）

| ID | 标题 | 决策 | 理由 |
|----|------|------|------|
| ADR-001 | 边缘 vs 云端推理 | Hybrid | 隐私 + 成本 + 延迟综合最优 |
| ADR-002 | DFSM vs E2E ML 决策 | DFSM | 可解释、可审计、易回滚 |
| ADR-003 | Postgres + pgvector vs 专用向量库 | Postgres+pgvector | 简化栈，单库事务 |
| ADR-004 | 通知服务用 Go 而非 Python | Go | 高并发 + 低 GC 抖动 |
| ADR-005 | Edge Agent 用 Rust + Python | 双语言 | Rust 编解码/IPC，Python 推理生态 |
| ADR-006 | Frontend Next.js 14 App Router | Next.js | RSC + 流式 SSR + 边缘渲染 |
| ADR-007 | Multi-tenancy with Postgres RLS | RLS | 最小化运维，强保证 |
| ADR-008 | CloudEvents v1 schema | CloudEvents | 标准化事件，便于第三方对接 |
| ADR-009 | OIDC + SAML for SSO | 双协议 | 大客户兼容性 |
| ADR-010 | 国密支持作为 crypto provider plugin | 可插拔 | 政务/信创可选 |

每个 ADR 在 `docs/architecture/adr/ADR-XXX-*.md` 保留完整论证记录。

---

## 20. 附录

### 20.1 模型选型矩阵 vs 替代品
| Task | Chosen | Alternative | 选择理由 |
|------|--------|-------------|---------|
| Face | SCRFD-2.5g | RetinaFace, BlazeFace | 速度+精度平衡 |
| Person | YOLOv8s | YOLO-NAS, RT-DETR | 工业落地成熟 |
| Tracker | ByteTrack | BoT-SORT, DeepSORT | 简单 + 高 MOTA |
| Re-ID | OSNet | TransReID, FastReID | 轻量 + 准确 |
| Liveness | Silent-FAS | DeepPixBis | 推理快 |
| Deepfake | Xception+TempCNN | Face X-Ray | 平衡 |
| Action | VideoMAE-B | Video Swin, SlowFast | SOTA |
| Speaker | ECAPA-TDNN | x-vector | 行业标杆 |
| VAD | Silero VAD | WebRTC VAD | 噪声鲁棒 |

### 20.2 第三方依赖清单（许可证审查）
| Lib | License | Usage |
|-----|---------|-------|
| FastAPI | MIT | backend |
| ONNXRuntime | MIT | inference |
| PyTorch | BSD-3 | training only |
| Triton Inference Server | BSD-3 | cloud serve |
| Next.js | MIT | console |
| TanStack Query | MIT | console |
| Tailwind CSS | MIT | console |
| shadcn/ui | MIT | console |
| pgvector | PostgreSQL | DB |
| Kafka | Apache-2.0 | event bus |
| Redis | RSALv2/SSPLv1 (post-7.4) | cache — 评估替换 Valkey (BSD) |
| LitmusChaos | Apache-2.0 | chaos |

### 20.3 性能基准复现脚本
- `algo/liveguard_algo/benchmarks/run_bench.py` 一键复现 BP §4.4 全部 KPI
- 输出 `models/outputs/data/tech__models.csv` 与 `tech__system_kpi.csv`

---

> **End of Design v1.0.0**
> **Next**: 进入 Phase 3 → `tasks.md`
