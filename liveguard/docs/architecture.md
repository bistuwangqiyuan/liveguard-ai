# 守播 LiveGuard AI · 架构图集

> 所有图使用 [Mermaid](https://mermaid.js.org/) 描述，GitHub / GitLab / Notion / VS Code 原生渲染。
> 配套高端渲染位图位于 `docs/images/`，可直接放入商业计划书 / 商务 PPT / 官网。

## 1. 业务上下文（Context）

```mermaid
flowchart LR
    M[商家 / MCN 运营] -->|Web 控制台| Console
    OPS[运维 / 合规专员] -->|移动 APP / 浏览器插件| MobileExt
    Host[主播 PC / 手机] -->|推流 RTMP/SRT| Stream
    Stream --> EdgeAgent
    Platform[抖音 / 快手 / 淘宝 / 视频号] -->|后台 Web| BrowserExt

    subgraph LiveGuard 守播平台
        EdgeAgent[边缘 Agent · 轻量推理]
        BackendAPI[后端 API · FastAPI]
        Algo[算法引擎 · 多模态融合]
        Notify[通知服务 · 7 通道]
        Console[Web 控制台 · Next.js]
        MobileExt[移动 APP + 浏览器插件]
        BrowserExt[浏览器插件 · MV3]
    end

    EdgeAgent --> BackendAPI
    BackendAPI --> Algo
    BackendAPI --> Notify
    Notify --> OPS
    BackendAPI --> Console
    BackendAPI --> MobileExt
    BrowserExt --> BackendAPI
```

## 2. 系统架构（Container）

```mermaid
flowchart TB
    classDef svc fill:#0f52db,stroke:#fff,color:#fff
    classDef data fill:#16a34a,stroke:#fff,color:#fff
    classDef bus fill:#f59e0b,stroke:#fff,color:#fff

    subgraph Edge["边缘侧"]
        E1[RTMP/SRT/WHEP<br/>拉流]
        E2[Algo 轻量推理<br/>ONNX · INT8]
        E3[特征上报<br/>httpx + tenacity]
        E1 --> E2 --> E3
    end

    subgraph Cloud["云端"]
        subgraph Gateway["网关层"]
            G1[Nginx / Envoy]
            G2[WAF + Rate Limit]
        end

        subgraph App["应用层"]
            B1[backend · FastAPI]:::svc
            B2[notify · FastAPI+Kafka consumer]:::svc
            B3[console · Next.js 14]:::svc
        end

        subgraph Algo["算法层"]
            A1[StreamFSM<br/>主播在岗状态机]
            A2[CheatFSM<br/>反作弊状态机]
            A3[多模态融合引擎<br/>Face·Person·Re-ID·Liveness·VAD·Voiceprint·Action]
            A4[难例挖掘<br/>持续学习]
            A1 --> A3
            A2 --> A3
            A3 --> A4
        end

        subgraph Data["数据层"]
            D1[(Postgres 16<br/>pgvector+TimescaleDB)]:::data
            D2[(Redis 7<br/>Cache+RateLimit)]:::data
            D3[(S3 / MinIO<br/>证据存档)]:::data
        end

        subgraph Bus["事件总线"]
            K1((Kafka<br/>events.v1))::: bus
            K2((Kafka<br/>notify.jobs.v1)):::bus
        end
    end

    E3 --> G1 --> G2 --> B1
    B1 --> A1 & A2
    B1 --> D1 & D2 & D3
    B1 --> K1 --> K2
    K2 --> B2
    B3 --> B1
    B2 -->|SMS/Voice/DingTalk/WeWork/Feishu/Webhook/Push| OPS[(运维 / 合规)]
```

## 3. 算法流水线（Algorithm Pipeline）

```mermaid
flowchart LR
    F[Frame<br/>图像+PCM] --> P1[Preprocess<br/>resize · normalize]
    P1 --> D1[FaceDetector]
    P1 --> D2[PersonDetector]
    P1 --> D3[LivenessScorer]
    P1 --> D4[ActionRecognizer]
    F --> V[VAD]
    F --> VP[VoicePrint]

    D1 --> R[Re-ID]
    D1 --> FS[FusionScore]
    D2 --> FS
    D3 --> FS
    R --> FS
    V --> FS
    VP --> FS
    D4 --> FS

    FS --> SF[StreamFSM<br/>IDLE→ON_DUTY→BRIEF_AWAY→LONG_AWAY→ALERT]
    FS --> CF[CheatFSM<br/>STATIC/LOOP/DEEPFAKE/IMPERSONATE/REPLAY]

    SF --> E[StateTransitionEvent]
    CF --> FL[CheatFlag]

    E --> EX[Explainer<br/>人类可读报告 + CloudEvents]
    FL --> EX

    FS --> HEM[HardExampleMiner<br/>低置信/冲突/反馈]
    HEM --> L[持续学习仓库]
```

## 4. 数据流（Sequence · 主播离岗告警）

```mermaid
sequenceDiagram
    participant H as 主播 (推流)
    participant EA as Edge Agent
    participant API as backend /v1/ingest
    participant FSM as StreamFSM
    participant AM as AlertManager
    participant K as Kafka (notify.jobs.v1)
    participant N as Notify 服务
    participant O as 运维 (DingTalk)

    loop 每 ~100ms
        H->>EA: 视频+音频帧
        EA->>EA: Algo 轻推理 → 特征
        EA->>API: POST /ingest/signals  (JWT + HMAC)
    end

    API->>FSM: feed(signal)
    FSM-->>API: StateTransitionEvent(ON_DUTY→BRIEF_AWAY)
    FSM-->>API: StateTransitionEvent(BRIEF_AWAY→LONG_AWAY)  [累计 60s]
    API->>AM: ingest(EventRecord, severity=P1)
    AM->>AM: 5 分钟窗口去重
    AM->>K: publish(notify.jobs.v1)
    K->>N: consume
    N->>N: 指数退避重试
    N->>O: DingTalk Markdown + @值班人
    N-->>API: ChannelResult(ok=True, attempts=1)
```

## 5. 反作弊检测（CheatFSM）

```mermaid
stateDiagram-v2
    [*] --> CLEAR
    CLEAR --> SUSPECTED_STATIC: 连续 N 秒帧内容熵 < τ₁
    CLEAR --> SUSPECTED_LOOP: 相似帧周期性重放置信度 ≥ τ₂
    CLEAR --> SUSPECTED_DEEPFAKE: Liveness < τ₃ AND 光流异常
    CLEAR --> SUSPECTED_IMPERSONATE: FaceID 与注册主播相似度 < τ₄
    CLEAR --> SUSPECTED_REPLAY: 音画不同步 >= Δ

    SUSPECTED_STATIC --> FLAGGED_STATIC: 证据累积满足阈值
    SUSPECTED_LOOP --> FLAGGED_LOOP
    SUSPECTED_DEEPFAKE --> FLAGGED_DEEPFAKE
    SUSPECTED_IMPERSONATE --> FLAGGED_IMPERSONATE
    SUSPECTED_REPLAY --> FLAGGED_REPLAY

    FLAGGED_STATIC --> CLEAR: 冷却 + 操作员复核 RESOLVE
    FLAGGED_LOOP --> CLEAR
    FLAGGED_DEEPFAKE --> CLEAR
    FLAGGED_IMPERSONATE --> CLEAR
    FLAGGED_REPLAY --> CLEAR
```

## 6. 部署拓扑（Production Kubernetes）

```mermaid
flowchart LR
    subgraph Region[cn-east-1]
        subgraph Ingress[Ingress / 7 层]
            LB[SLB + WAF]
            CDN[CDN 静态资源]
        end

        subgraph K8S[Kubernetes 集群]
            subgraph ns-api[namespace: liveguard-api]
                pod1[backend · HPA 3-20]
                pod2[notify · HPA 2-10]
                pod3[console · HPA 2-6]
            end

            subgraph ns-data[namespace: liveguard-data]
                pg[(RDS Postgres 16<br/>主备 + 只读)]
                rd[(Redis Cluster)]
                mq[(Kafka 3 broker)]
                s3[(OSS/S3)]
            end

            subgraph ns-obs[namespace: liveguard-obs]
                prom[Prometheus]
                graf[Grafana]
                tempo[Tempo / OTel]
                loki[Loki 日志]
            end
        end

        Edge[边缘 Agent · 客户侧 PC/NVR]
    end

    CDN --> LB
    LB --> pod3
    LB --> pod1
    Edge -->|TLS mTLS| LB
    pod1 --> pg & rd & mq & s3
    pod2 --> mq
    pod1 -.->|OTLP| tempo
    pod1 -.->|prom /metrics| prom
    pod1 -.->|JSON stdout| loki
```

## 7. 模块依赖（Monorepo）

```mermaid
flowchart TB
    algo[liveguard-algo<br/>算法引擎]
    backend[liveguard-backend<br/>FastAPI]
    notify[liveguard-notify<br/>Kafka Consumer]
    edge[liveguard-edge<br/>边缘 Agent]
    console[console · Next.js]
    mobile[mobile · RN/Expo]
    ext[extension · MV3]
    models[models/python_models]

    algo --> backend
    algo --> edge
    backend --> notify
    backend --> console
    backend --> mobile
    backend --> ext
    models -. 业务决策 .-> backend
```

## 8. 观测链路（Metrics → Alerts）

```mermaid
flowchart LR
    pod1[backend pod] -->|/metrics| prom[Prometheus]
    pod2[notify pod] -->|/metrics| prom
    pod3[edge agent] -->|pushgateway/OTLP| prom
    prom --> graf[Grafana Dashboards]
    prom --> alert[Alertmanager]
    alert -->|P0/P1| pd[PagerDuty]
    alert -->|SLO 告警| dt[DingTalk On-Call]
```

---

### 渲染导出

本目录已预置 `docs/images/` 以存放品牌图、海报图。将本文件任何 ```mermaid 块 复制到 [mermaid.live](https://mermaid.live) 即可一键导出 SVG/PDF/PNG，字体建议 Inter + Noto Sans SC。
