# 守播 LiveGuard AI · 需求规格说明书 (Requirements Specification)

> **Spec ID**: `liveguard-ai/requirements`
> **Version**: v1.0.0
> **Status**: ✅ Approved (Phase 1 of Kiro Spec Workflow)
> **Date**: 2026-04-20
> **Author**: 守播 LiveGuard AI · 产品研发组
> **Reviewers**: CEO / CTO / CPO / CCO / 客户成功委员会
> **依据**: `守播LiveGuard_商业计划书_v1.0.md` §1–§12

---

## 0. 文档元信息 (Document Meta)

### 0.1 文档目的 (Purpose)
本文档以 EARS（Easy Approach to Requirements Syntax）方法描述 **守播 LiveGuard AI 视频直播监控智能体**全部产品级需求，作为后续 `design.md` 与 `tasks.md` 的唯一依据；任何范围变更必须通过本文档版本化。

### 0.2 EARS 语法约定
| 类型 | 模板 | 用例 |
|------|------|------|
| **Ubiquitous** | The system shall ... | 系统应始终启用 TLS 1.3 |
| **Event-driven** | WHEN <trigger> THE SYSTEM SHALL ... | WHEN 检测到主播离开画面 30 秒 THE SYSTEM SHALL 升级告警 |
| **State-driven** | WHILE <state> THE SYSTEM SHALL ... | WHILE 客户处于试用期 THE SYSTEM SHALL 限制路数 ≤ 5 |
| **Optional** | WHERE <feature> THE SYSTEM SHALL ... | WHERE 启用边缘部署 THE SYSTEM SHALL 不上传原始视频 |
| **Unwanted** | IF <bad-condition> THEN THE SYSTEM SHALL ... | IF 模型推理失败 THEN THE SYSTEM SHALL 自动 fallback 至备用模型 |
| **Complex** | WHILE … WHEN … THE SYSTEM SHALL … | 组合多触发器 |

### 0.3 优先级与编号
- 优先级：`P0` 必须（MVP 阻塞）｜ `P1` 重要（GA 阻塞）｜ `P2` 增强（GA 后 6 月内）｜ `P3` 战略（Y2+）
- 编号：`REQ-<域>-<序号>`，域代码：`SYS / EDGE / ALGO / API / WEB / APP / NOTIFY / DATA / SEC / OPS / BIZ`
- 可追溯性：每条需求标注 `BP §X.Y` 与对应 `Design §A.B` / `Task #N`

### 0.4 范围（In/Out of Scope）
| 范围 | 项目 |
|------|------|
| **In** | 视频/音频实时采集 ┃ 多模态算法栈 ┃ 决策融合 ┃ 告警分发 ┃ Web/APP 控制台 ┃ 边缘盒子固件 ┃ 计费/定价 ┃ 合规审计 |
| **Out** | 直播间内容生成 ┃ 商品推荐 ┃ 物流履约 ┃ 财务支付通道（仅集成第三方）┃ 主播培训内容 ┃ 流量投放 |

---

## 1. 干系人与角色 (Stakeholders & Personas)

### 1.1 主要角色（Primary Personas）

| Persona | 职责 | 使用的产品形态 | 关键场景 |
|--------|------|--------------|---------|
| **MCN 运营总监 (P-MCN)** | 监控 30–500 个直播间，调度排班 | Web 控制台 + APP | 一站式大屏告警、KPI 复盘 |
| **品牌自播经理 (P-BRAND)** | 管理 5–30 个品牌账号 | Web 控制台 + 浏览器插件 | 离岗/话术/形象合规 |
| **个人主播 (P-SOLO)** | 自主开播，1–3 个账号 | APP + 桌面伴侣 | 离岗自我提醒，零配置 |
| **平台风控 (P-PLATFORM)** | 平台级监控合规 | API/SDK 嵌入 | 大规模治理、二次研发 |
| **教培/政务 IT (P-IT)** | 私有化运维 | 私有化 K8s + 边缘盒子 | 数据完全本地、可审计 |
| **NOC 值班工程师 (P-NOC)** | 7×24 监控 SLA | Web 控制台 + Grafana | 告警分级、故障升级 |
| **CSM 客户成功 (P-CSM)** | 客户健康度、续约扩展 | Gainsight + 自研 | NRR/GRR 跟踪 |
| **算法工程师 (P-ALGO)** | 模型迭代、难例闭环 | MLflow + DVC + 内部门户 | 数据→训练→A/B→上线 |
| **财务/审计 (P-FIN)** | 计费、收入确认、审计 | 财务后台 | 计量准确、可对账 |
| **DPO/合规 (P-DPO)** | PIPL/算法备案合规 | 合规后台 | 数据生命周期治理 |

### 1.2 系统外部角色（External Actors）
- 直播平台（抖音/淘宝/快手/视频号/TikTok/YouTube Live）
- 第三方通道（短信/语音/钉钉/飞书/企业微信/Webhook）
- 算力平台（阿里云/华为云/腾讯云/AWS Singapore/Tokyo）
- 监管机构（网信办、广电总局、网安局）
- 第三方审计（普华永道、安永、护卫神等等保测评）

---

## 2. 总体功能需求 (Functional Requirements)

### REQ-SYS-001 — 三形态产品 (P0)
**User Story**: 作为不同规模客户，我希望可以根据自身需要选择 SaaS Web、APP 或边缘盒子任一形态，以便低门槛接入。

**EARS Acceptance Criteria**:
1. The system shall provide three product form factors: (a) SaaS Web Console, (b) Mobile App (iOS/Android), (c) Edge Appliance.
2. WHEN a customer signs up via SaaS Web THE SYSTEM SHALL provision a tenant within 30 seconds.
3. WHEN a customer purchases an Edge Appliance THE SYSTEM SHALL ship a pre-configured device that can be online within 10 minutes after power-on.
4. WHERE the customer is in private-deployment mode THE SYSTEM SHALL operate fully air-gapped (zero outbound network calls).

**Trace**: BP §1.3.3 / §4.1 ｜ Design §3.1 ｜ Task #4-1

---

### REQ-SYS-002 — 主播在岗判定 SLA (P0)
**User Story**: 作为 MCN 运营总监，我需要在主播离岗 60 秒内被告知，以便及时干预避免空播罚款。

**EARS**:
1. WHEN the host (主播) is undetected for **45 s P50 / 60 s P90 / 75 s P99** THE SYSTEM SHALL emit an `EVENT_HOST_OFFLINE` event.
2. The system shall achieve `Precision ≥ 99.0% / Recall ≥ 99.0% / F1 ≥ 99.0%` on the LiveGuard internal benchmark v1.0.
3. The system shall maintain `FAR ≤ 1.0%` and `FNR ≤ 0.5%` over any 30-day rolling window.
4. IF rolling-30d FAR > 1.5% OR FNR > 2% THEN THE SYSTEM SHALL trigger automatic SLA-violation procedure (refund credit + RCA).
5. WHEN running on Pro tier the SYSTEM SHALL deliver alert end-to-end (camera→notification) within `60 s P95`; on Enterprise within `30 s P95`.

**Trace**: BP §4.4 ｜ Design §5 ｜ Task #5-7, #5-8

---

### REQ-SYS-003 — 多模态融合判定 (P0)
**User Story**: 作为 P-ALGO，我需要系统采用多模态投票，而非单一帧判定，以提升鲁棒性。

**EARS**:
1. The system shall fuse **6 signal sources**: face detection, person detection, Re-ID, liveness, action recognition, audio VAD/speaker.
2. The system shall maintain a per-stream **State Machine**: `IDLE → ON_DUTY → BRIEF_AWAY → LONG_AWAY → ALERT_ESCALATED`.
3. WHEN composite score `S = Σ wᵢ·sᵢ ≥ 0.65` THE SYSTEM SHALL set state `ON_DUTY`.
4. WHEN composite score `< 0.35` for more than 5 seconds THE SYSTEM SHALL set state `BRIEF_AWAY`.
5. WHEN state remains `BRIEF_AWAY` for ≥ 60 s THE SYSTEM SHALL transition to `LONG_AWAY` and emit P1 alert.
6. WHEN state remains `LONG_AWAY` for ≥ 120 s THE SYSTEM SHALL transition to `ALERT_ESCALATED` and emit P0 alert (phone call).
7. WHILE network to cloud is degraded THE SYSTEM SHALL fall back to edge-only voting for face+person+liveness only.

**Trace**: BP §4.3.2 ｜ Design §6 ｜ Task #5-6

---

### REQ-SYS-004 — 反作弊检测 (P0)
**EARS**:
1. The system shall detect 5 cheat patterns: `STATIC_PHOTO / LOOPED_VIDEO / DEEPFAKE_AVATAR / IMPERSONATION / SCREEN_REPLAY`.
2. WHEN `Liveness score < 0.50` for two consecutive 5-s windows THE SYSTEM SHALL flag `STATIC_PHOTO` and emit `EVENT_CHEAT_DETECTED`.
3. WHEN `Re-ID similarity to enrolled host < 0.55` for 10 seconds THE SYSTEM SHALL flag `IMPERSONATION`.
4. WHEN `Face-temporal-coherence variance < 0.02` over a 10-s window AND `audio-VAD ≠ active` THE SYSTEM SHALL flag `LOOPED_VIDEO`.
5. WHEN deepfake artifact score (FaceForensics-style) `> 0.7` THE SYSTEM SHALL flag `DEEPFAKE_AVATAR`.
6. The system shall provide explainability: each `EVENT_CHEAT_DETECTED` carries `evidence_frames[]`, `signal_breakdown{}`, `model_versions{}`.

**Trace**: BP §4.5 ｜ Design §6.4 ｜ Task #5-9

---

### REQ-SYS-005 — 多平台支持 (P0)
**EARS**:
1. The system shall support stream ingestion from: (a) RTMP, (b) SRT, (c) HLS, (d) WebRTC, (e) Local USB/IP camera.
2. The system shall provide platform adapters for: 抖音 (Douyin/TikTok), 淘宝直播, 快手, 视频号 (WeChat Channel), 京东直播, 小红书, YouTube Live, TikTok Shop.
3. WHEN a tenant binds a platform account THE SYSTEM SHALL fetch the live-room metadata via the platform's official API or, if not available, through user-provided RTMP pull URL.
4. IF a platform changes its API contract THEN THE SYSTEM SHALL detect within 1 hour via canary checks and notify on-call engineers.

**Trace**: BP §1.3.2, §4.1 ｜ Design §4.2 ｜ Task #6-3

---

### REQ-SYS-006 — 多通道告警分发 (P0)
**EARS**:
1. The system shall support 8 notification channels: SMS, voice call, WeChat (server message), DingTalk, Feishu, Enterprise WeChat, Webhook, App Push.
2. WHEN an alert event is emitted THE SYSTEM SHALL deliver to all configured channels within `5 s P95`.
3. WHEN delivery to a channel fails THE SYSTEM SHALL retry with exponential backoff (1s, 3s, 9s, 27s) up to 4 attempts and route to fallback channel after final failure.
4. The system shall support escalation policies: L1 (in-app) → L2 (IM bot) → L3 (SMS) → L4 (voice call) with configurable wait intervals.
5. WHILE `silent_window` (configurable, e.g., 02:00–07:00) is active THE SYSTEM SHALL suppress non-P0 alerts and queue them for morning digest.
6. The system shall enable 值班轮转 (on-call rotation) with handover at configurable boundaries.

**Trace**: BP §4.2 / §6.6 ｜ Design §7 ｜ Task #8

---

### REQ-SYS-007 — 告警闭环与复盘 (P1)
**EARS**:
1. WHEN an `ALERT_ESCALATED` event occurs THE SYSTEM SHALL automatically capture a 60-s clip (T-30s to T+30s) and store in tenant-segregated object storage.
2. The system shall enable users to mark alert as `TRUE_POSITIVE | FALSE_POSITIVE | UNCONFIRMED` and add notes.
3. WHEN user marks `FALSE_POSITIVE` THE SYSTEM SHALL queue the clip+labels into the active-learning hard-example pool (subject to consent).
4. The system shall generate weekly per-tenant compliance reports (PDF/Excel) with offline minutes, cheat events, response times, NPS, and action recommendations.

**Trace**: BP §1.3.2 / §4.7 ｜ Design §8 ｜ Task #6-9

---

### REQ-SYS-008 — 主播身份注册 (P0)
**EARS**:
1. WHEN a tenant onboards a host THE SYSTEM SHALL collect ≥ 5 reference photos (front, left 30°, right 30°, smile, neutral) and ≥ 3 voice samples (≥ 10 s each) **with explicit dual-consent (tenant + host)**.
2. The system shall extract a 512-D face embedding and 192-D voice embedding stored encrypted at rest (AES-256-GCM).
3. WHERE the host revokes consent THE SYSTEM SHALL purge embeddings within 24 hours including all backups.
4. The system shall version embeddings; re-enrollment creates a new version while keeping audit trail.

**Trace**: BP §4.3 / §10.4 ｜ Design §6.2 ｜ Task #5-3

---

### REQ-SYS-009 — 隐私优先（边缘推理）(P0)
**EARS**:
1. WHERE the customer enables `privacy_mode = strict` THE SYSTEM SHALL perform face/person inference on the edge and only upload (a) feature vectors ≤ 1 KB/min, (b) status events.
2. The system shall **never** transmit raw video frames to the cloud unless `cloud_recording = true` is explicitly opted-in by the tenant.
3. The system shall blur (Gaussian σ ≥ 8) any non-host faces before any optional cloud upload.
4. The system shall provide a tamper-evident `privacy_audit_log` with append-only WORM storage.

**Trace**: BP §4.2 / §10.3.1 ｜ Design §11 ｜ Task #7-4

---

### REQ-SYS-010 — 多租户隔离 (P0)
**EARS**:
1. The system shall isolate data by `tenant_id` at row-level (PostgreSQL RLS) and at object-storage prefix.
2. The system shall use per-tenant KMS data encryption keys (DEK) wrapped by tenant master key (KEK).
3. IF a query crosses tenant boundary without admin scope THEN THE SYSTEM SHALL deny and log a `SEC_TENANT_LEAK_ATTEMPT` audit event.
4. The system shall support per-tenant rate limiting at API gateway (default 1000 req/min, configurable).

**Trace**: BP §4.6 / §10.2 ｜ Design §10 ｜ Task #6-2

---

## 3. 算法与模型需求 (Algorithm Requirements)

### REQ-ALGO-001 — 人脸检测 (P0)
**EARS**:
1. WHEN processing each video frame THE SYSTEM SHALL detect faces with `Precision ≥ 98% AND Recall ≥ 97%` on the LiveGuard test set.
2. The system shall use **SCRFD-2.5G** (preferred) or **RetinaFace-MNet** as the face detector.
3. WHEN inference latency `> 30 ms` on edge THE SYSTEM SHALL automatically downsample frame to 640×640.
4. The system shall return per-face: `bbox, landmarks(5pt), confidence, blur_score, occlusion_mask`.

**Benchmark Source**: WIDER FACE Hard subset; LiveGuard Bench v1.0 (~ 50,000 frames).
**Trace**: BP §4.3 ｜ Design §6.1 ｜ Task #5-1

---

### REQ-ALGO-002 — 人形检测 (P0)
**EARS**:
1. The system shall detect human bodies with `mAP@0.5 ≥ 0.94` using **YOLOv8s-pose** or **YOLO-NAS-S**.
2. WHEN multiple persons appear THE SYSTEM SHALL track each with a stable `track_id` (ByteTrack/BoT-SORT) for ≥ 60 seconds.
3. The system shall return per-person: `bbox, keypoints(17), track_id, confidence`.

**Trace**: BP §4.3 ｜ Design §6.1 ｜ Task #5-2

---

### REQ-ALGO-003 — 行人重识别 (Re-ID) (P0)
**EARS**:
1. The system shall use **OSNet-x1.0** (preferred) or **TransReID-Small** to extract 512-D embeddings.
2. The system shall achieve `Rank-1 ≥ 94%` on Market-1501; `Rank-1 ≥ 88%` on LiveGuard host-impersonation test set.
3. WHEN cosine similarity to enrolled host embedding `≥ 0.70` THE SYSTEM SHALL classify as `SAME_HOST`.
4. WHEN similarity `0.40 ≤ s < 0.70` THE SYSTEM SHALL classify as `UNCERTAIN` and request additional signals.
5. WHEN similarity `< 0.40` THE SYSTEM SHALL classify as `DIFFERENT_HOST`.

**Trace**: BP §4.3 ｜ Design §6.2 ｜ Task #5-3

---

### REQ-ALGO-004 — 活体检测 (Liveness) (P0)
**EARS**:
1. The system shall detect spoofing using **Silent-Face-Anti-Spoofing** with `ACER ≤ 2.5%` on CASIA-FASD-like internal set.
2. The system shall detect deepfakes using a temporal model (XceptionNet + temporal CNN) with `AUC ≥ 0.92` on FaceForensics++ DF subset.
3. The system shall combine static-liveness + deepfake-detection scores into a single `liveness_score ∈ [0,1]`.

**Trace**: BP §4.3 / §4.5 ｜ Design §6.3 ｜ Task #5-4

---

### REQ-ALGO-005 — 行为识别 (P1)
**EARS**:
1. The system shall classify host behavior into 24 classes (e.g., `talking, demonstrating_product, drinking, looking_at_camera, eating, leaving_seat, sleeping, angry_gesture …`) using **VideoMAE-Base** fine-tuned on LiveGuard Action set (~ 100k clips).
2. The system shall achieve `Top-1 ≥ 78%` and provide top-3 per clip.
3. WHEN behavior == `sleeping` for ≥ 30 s THE SYSTEM SHALL emit `EVENT_HOST_DROWSY`.
4. WHEN behavior ∈ {`leaving_seat`, `looking_away`} for ≥ 60 s THE SYSTEM SHALL contribute to offline scoring.

**Trace**: BP §4.3 ｜ Design §6.5 ｜ Task #5-5

---

### REQ-ALGO-006 — 音频 VAD + 说话人验证 (P0)
**EARS**:
1. The system shall use **Silero-VAD** to detect voice activity at 30-ms granularity with `EER ≤ 3%`.
2. The system shall use **ECAPA-TDNN** (192-D) for speaker verification with `EER ≤ 1%` on VoxCeleb1-O.
3. WHEN audio VAD detects voice AND speaker verification cosine `< 0.35` against enrolled host THE SYSTEM SHALL contribute to `IMPERSONATION` flagging.
4. The system shall handle background music and product-demo audio without false-triggering speaker mismatch.

**Trace**: BP §4.3 ｜ Design §6.6 ｜ Task #5-6

---

### REQ-ALGO-007 — 决策融合状态机 (P0)
**EARS**:
1. The system shall implement a deterministic finite-state machine (DFSM) with the states defined in REQ-SYS-003.
2. The system shall apply weighted multi-modal voting with weights `w = [0.30, 0.20, 0.20, 0.10, 0.10, 0.10]` (face/person/Re-ID/liveness/action/audio).
3. The system shall expose weights as per-tenant configurable (within bounds enforced by guardrails).
4. The system shall log every state transition with `cause_signals[]` for forensics.
5. The system shall provide hysteresis bands to prevent oscillation: 5-s buffer at boundary scores.

**Trace**: BP §4.3.2 ｜ Design §6.7 ｜ Task #5-6

---

### REQ-ALGO-008 — 持续学习与难例挖掘 (P1)
**EARS**:
1. WHEN tenant marks an alert as `FALSE_POSITIVE` and consent==`granted` THE SYSTEM SHALL push the sample (anonymized features only by default) to `hard_example_queue`.
2. The system shall sample 0.5% of routine inferences with confidence ∈ [0.4, 0.7] for active learning.
3. The system shall publish weekly model deltas via canary deployment (5%→25%→100%) with auto-rollback if guardrail metrics degrade > 1%.
4. The system shall maintain full lineage: dataset snapshot ↔ training run ↔ model artifact ↔ deployment, retrievable by `model_version`.

**Trace**: BP §4.7 / §7.4 ｜ Design §6.8 ｜ Task #5-10

---

## 4. 接口与集成需求 (Integration & API Requirements)

### REQ-API-001 — RESTful & WebSocket API (P0)
**EARS**:
1. The system shall expose REST API under `/api/v1/...` following OpenAPI 3.1.
2. The system shall expose `wss://.../api/v1/streams/{stream_id}/events` for real-time event subscription.
3. The system shall enforce JWT (RS256, 15-min TTL) + refresh token (24-h TTL).
4. The system shall provide SDK for Python, JavaScript/TypeScript, Java, Go, and PHP.
5. The system shall publish API changelog with deprecation policy: minimum 12 months sunset window.

### REQ-API-002 — Webhook 出向集成 (P0)
**EARS**:
1. The system shall POST events to tenant-configured webhook URLs with HMAC-SHA256 signature in `X-LiveGuard-Signature` header.
2. The system shall include idempotency key in `X-LiveGuard-Event-Id` to allow safe retry.
3. WHEN webhook returns `2xx` within 5 s THE SYSTEM SHALL mark delivery successful.
4. IF webhook fails 5 times THEN THE SYSTEM SHALL disable webhook and email tenant admin.

### REQ-API-003 — 平台 SDK 嵌入 (P2)
**EARS**:
1. The system shall provide a 30-MB SDK (C++/Java) embeddable into platform 主播工作台 with offline inference capability.
2. The system shall license SDK via per-host activation token signed by LiveGuard root CA.

**Trace**: BP §5.1 / §6.6.2 ｜ Design §9 ｜ Task #6-1

---

## 5. Web 控制台需求 (Web Console Requirements)

### REQ-WEB-001 — 实时大屏 (P0)
1. WHEN user opens `/dashboard` THE SYSTEM SHALL render a tile grid of all active streams (max 64 visible, virtual scroll for more) within 2 s on a 100-Mbps connection.
2. Each tile shall display: thumbnail (1 fps), state badge (`ON_DUTY`/`BRIEF_AWAY`/`LONG_AWAY`/`ALERT`), time-on-state, host name, latest event chip.
3. WHEN a stream transitions to `ALERT_ESCALATED` THE SYSTEM SHALL highlight the tile (red border, pulse animation) and play a configurable audio cue.
4. The system shall support tile filtering, grouping (by team/MCN/platform), and saved layouts.

### REQ-WEB-002 — 事件中心 (P0)
1. The system shall provide a paginated event list with filters: time range, event type, severity, host, platform, status.
2. WHEN user clicks an event THE SYSTEM SHALL show evidence (clip player, signal timeline, model breakdown, recommended action).
3. The system shall support bulk operations: mark resolved, export, attach notes.

### REQ-WEB-003 — 配置中心 (P0)
1. The system shall enable configuration of: hosts, streams, alert policies, escalation, channels, on-call roster, working hours, silent windows.
2. The system shall validate config in real-time with semantic checks (e.g., warn if silent window covers 80%+ of typical broadcast hours).

### REQ-WEB-004 — KPI / BI 看板 (P1)
1. The system shall provide built-in dashboards: SLA compliance, alert volume trend, top hosts by offline rate, MTBF/MTTR, NRR/GRR.
2. The system shall enable export as PDF/Excel and API-pull for embedding into tenant BI.

### REQ-WEB-005 — 角色权限 (RBAC) (P0)
1. The system shall implement RBAC with built-in roles: `Owner / Admin / Manager / Operator / Viewer / Auditor`.
2. The system shall enable custom roles with fine-grained permissions on resource × action matrix.
3. The system shall require MFA for `Owner` and `Admin` roles by default.

**Trace**: BP §4.1 ｜ Design §12 ｜ Task #9

---

## 6. 移动端 / 桌面端需求 (Mobile & Desktop)

### REQ-APP-001 — 移动 App (P0)
1. The system shall provide native iOS (SwiftUI / iOS 15+) and Android (Kotlin / API 26+) apps.
2. The app shall receive push notifications via APNs / FCM with `< 5 s P95` from event emission.
3. WHEN user taps notification THE SYSTEM SHALL deep-link directly to event detail.
4. The app shall support voice-call alert acknowledgement via in-app one-tap callback.

### REQ-APP-002 — 浏览器插件 (P2)
1. The system shall provide Chrome/Edge MV3 extension that overlays alert badge on platform-specific live-room pages (抖音/淘宝/快手/视频号).
2. The extension shall require zero permissions beyond `activeTab` and target host.

### REQ-APP-003 — 桌面伴侣 (P2)
1. The system shall provide Electron-based desktop companion for Windows 10+/macOS 12+ that captures local cam/screen and runs lightweight ONNX inference offline.
2. WHEN offline THE SYSTEM SHALL queue events locally and sync upon reconnection.

**Trace**: BP §4.1 ｜ Design §13 ｜ Task #10

---

## 7. 边缘智能盒子需求 (Edge Appliance)

### REQ-EDGE-001 — 硬件兼容 (P1)
1. The edge agent shall run on: Rockchip RK3588 (8 TOPS), Horizon J5 (16 TOPS), Cambricon MLU220 (8 TOPS), Huawei Ascend 310B (22 TOPS), NVIDIA Jetson Orin Nano (40 TOPS).
2. The system shall provide a unified ONNX-Runtime + EP (execution provider) plugin layer abstracting hardware specifics.

### REQ-EDGE-002 — 离线弹性 (P0)
1. WHEN cloud connectivity is lost THE SYSTEM SHALL continue to detect and locally store events for up to 72 hours.
2. WHEN connectivity restores THE SYSTEM SHALL sync queued events in chronological order with replay protection.

### REQ-EDGE-003 — OTA 升级 (P1)
1. The system shall support delta OTA updates ≤ 50 MB with cryptographic signature verification (Ed25519).
2. The system shall implement A/B partition scheme with auto-rollback on boot failure.

### REQ-EDGE-004 — 设备健康 (P1)
1. The edge agent shall report heartbeat every 30 s with metrics: CPU, NPU, RAM, disk, temp, network RTT.
2. WHEN any metric crosses warning threshold THE SYSTEM SHALL alert tenant operations.

**Trace**: BP §4.2 / §7.3 ｜ Design §14 ｜ Task #7

---

## 8. 数据与隐私需求 (Data & Privacy)

### REQ-DATA-001 — 数据分级 (P0)
The system shall classify data into 4 tiers:
| Tier | 例 | 加密要求 | 留存 | 出境 |
|------|----|----------|------|-------|
| L1-Restricted | 原始视频/语音 | 客户侧 + 客户密钥 | 0 (默认不存) | 严禁 |
| L2-Confidential | 人脸/声纹特征 | 服务侧 KMS + 客户 KEK | 30 天 | 评估 |
| L3-Internal | 事件元数据 | KMS | 365 天 | 允许（脱敏后）|
| L4-Public | 聚合统计 | 标准加密 | 永久 | 允许 |

### REQ-DATA-002 — 同意与撤销 (P0)
1. WHEN onboarding a host THE SYSTEM SHALL collect explicit dual-consent (tenant + host) with timestamp, IP, signature.
2. The system shall provide self-service consent revocation; revocation triggers REQ-SYS-008 #3.

### REQ-DATA-003 — 数据出境 (P1)
1. WHERE data crosses CN/EU/US borders THE SYSTEM SHALL run an automated DPIA and require manual approval.
2. The system shall maintain a public sub-processor list updated within 30 days of changes.

### REQ-DATA-004 — 留存与销毁 (P0)
1. The system shall enforce automatic purge per tier in REQ-DATA-001.
2. WHEN tenant terminates contract THE SYSTEM SHALL purge tenant data (incl. backups) within 30 days and provide an attestation certificate.

**Trace**: BP §10.4 ｜ Design §11 ｜ Task #12

---

## 9. 安全需求 (Security)

### REQ-SEC-001 — 身份与访问 (P0)
1. The system shall use OAuth2 + OIDC, supporting password, SSO (SAML/OIDC), passkey (WebAuthn).
2. The system shall enforce password policy: ≥ 12 chars, 3-of-4 character classes, no top-100k breached passwords (HaveIBeenPwned).
3. The system shall lock account after 5 failed attempts within 5 minutes for 15 minutes.

### REQ-SEC-002 — 传输与存储加密 (P0)
1. The system shall enforce TLS 1.3 with HSTS preload; reject TLS < 1.2.
2. The system shall encrypt all data at rest using AES-256-GCM with KMS-managed keys.
3. WHERE customer is in CN private deployment THE SYSTEM SHALL support GM/T 国密 SM2/SM3/SM4.

### REQ-SEC-003 — 审计 (P0)
1. The system shall log all sensitive actions in append-only WORM storage retained ≥ 5 years.
2. The system shall provide audit log export with cryptographic integrity proof (Merkle tree root signature).

### REQ-SEC-004 — 漏洞管理 (P1)
1. The system shall run SAST (Semgrep), DAST (OWASP ZAP), SCA (Trivy/Snyk) on every PR; block merge on `Critical/High`.
2. The system shall conduct red-team penetration testing quarterly.
3. The system shall maintain a public security.txt and bug-bounty program (HackerOne/补天).

**Trace**: BP §7.5.2 / §10 ｜ Design §11 ｜ Task #4-7

---

## 10. 性能与可靠性 (Performance & Reliability)

### REQ-OPS-001 — 服务可用性 (P0)
| Tier | 月度可用性 | RPO | RTO |
|------|-----------|-----|-----|
| Starter | 99.5% | 5 min | 30 min |
| Pro | 99.9% | 1 min | 5 min |
| Enterprise | 99.95% | 10 s | 60 s |

### REQ-OPS-002 — 容量与扩展 (P0)
1. The system shall handle ≥ 200,000 concurrent streams in production.
2. The system shall scale horizontally with linear cost up to 1M streams.
3. WHEN per-cluster GPU utilization > 75% for 10 min THE SYSTEM SHALL auto-scale-out.

### REQ-OPS-003 — 单路成本基线 (P1)
| Year | 目标单路推理成本 (CNY/年) |
|------|--------------------------:|
| Y1 | ≤ 260 |
| Y3 | ≤ 135 |
| Y5 | ≤ 70 |

### REQ-OPS-004 — 灾备 (P1)
1. The system shall replicate critical data cross-region with `< 1 min RPO`.
2. The system shall conduct quarterly DR drill with RTO measurement.

**Trace**: BP §4.4 / §7.2 / §8 ｜ Design §10 ｜ Task #6-10

---

## 11. 合规与认证 (Compliance & Certification)

### REQ-SEC-005 — 中国合规
The system shall obtain & maintain:
1. 算法备案（《互联网信息服务算法推荐管理规定》）
2. 等保 2.0 三级（GB/T 22239-2019）
3. 增值电信业务经营许可证（如需）
4. PIPL 合规：DPO 设立、PIA 完成、数据出境评估
5. 信息安全管理体系 ISO/IEC 27001
6. SOC 2 Type II
7. 网络安全审查（如关键信息基础设施合作）

### REQ-SEC-006 — 海外合规
The system shall be compatible with: GDPR (EU)、CCPA/CPRA、Singapore PDPA；EU AI Act high-risk requirements (when entering EU).

**Trace**: BP §10.4 ｜ Design §11 ｜ Task #12-7

---

## 12. 商业 & 计费需求 (Billing & Business)

### REQ-BIZ-001 — 三档订阅 (P0)
| Tier | 月费/路 | 功能集 | SLA | 路数上限 |
|------|---------|-------|-----|---------:|
| Starter | ¥199 | REQ-SYS-001..010 (subset) | 99.5% | 10 |
| Pro | ¥699 | + 反作弊 + 多通道 | 99.9% | 100 |
| Enterprise | ¥2,999+ | + 私有化 + SLA + 专属 | 99.95% | ∞ |

### REQ-BIZ-002 — 计量计费 (P0)
1. The system shall meter: (a) stream-hours, (b) alert events, (c) API calls, (d) storage GB-month, (e) phone-call seconds.
2. WHEN usage exceeds plan limits THE SYSTEM SHALL apply per-unit overage prices configured per tier.
3. The system shall integrate with Stripe (international), 支付宝/微信支付/对公汇款 (CN); produce 增值税电子专票.

### REQ-BIZ-003 — 客户 ROI 计算器 (P1)
1. The system shall provide an in-product ROI calculator using the formulas from BP §5.5.
2. WHEN sales user inputs `daily_GMV, current_offline_rate` THE SYSTEM SHALL output ROI, payback days, savings — within 100 ms.

**Trace**: BP §5 ｜ Design §15 ｜ Task #6-11

---

## 13. AI 伦理需求 (AI Ethics)

### REQ-SEC-007 — 公平性 (P1)
1. The system shall conduct quarterly bias audits across (gender, age, skin-tone) and publish aggregated metrics.
2. WHEN per-subgroup FAR/FNR delta > 30% THE SYSTEM SHALL trigger remediation.

### REQ-SEC-008 — 可解释性 (P0)
1. The system shall provide per-event explanation: which signals contributed (Shapley-style breakdown).
2. The system shall maintain "human-in-the-loop": every P0 alert requires human acknowledgement before automatic actions (e.g., auto-pause stream).

**Trace**: BP §10.4.3 ｜ Design §6.9 ｜ Task #5-11

---

## 14. 国际化与可访问性 (i18n & a11y)

### REQ-WEB-006 — 多语言 (P1)
The system shall support: 简中、繁中、英、日、印尼、泰、越、阿、西、葡 (≥ 10).

### REQ-WEB-007 — 可访问性 (P1)
The system shall comply with WCAG 2.1 AA: keyboard navigation, screen reader, contrast ≥ 4.5:1, motion-reduce media query.

---

## 15. 验收标准与上线门禁 (Definition of Done)

### 15.1 功能验收
- 每条 EARS 准则均有对应自动化测试（单元/集成/E2E）通过率 100%。
- BP §4.4 全部 SLA 在压测环境（200k 并发）连续 7 天达标。

### 15.2 安全验收
- 第三方渗透测试无 P0/P1 未修复漏洞。
- 算法备案/等保三级/ISO 27001 出具证书。

### 15.3 文档验收
- 用户文档（中/英）覆盖全部公开 API、SLA、合规承诺。
- 内部 Runbook 覆盖 P0/P1/P2 故障处置。

### 15.4 上线门禁
- 全套灰度（5% → 25% → 100%）+ 自动回滚验证。
- C-level + AI 伦理委员会签字。

---

## 16. 优先级与里程碑映射 (Roadmap Mapping)

| Milestone | 时点 | 包含的需求 | 出口准则 |
|-----------|------|-----------|---------|
| **MVP v0.1** | Y1 M3 | REQ-SYS-001..003, REQ-ALGO-001..002, REQ-API-001, REQ-WEB-001..002 (subset) | 30 试用客户、FAR<5% |
| **GA v1.0** | Y1 M7 | + REQ-SYS-004..010, REQ-ALGO-003..007, REQ-NOTIFY-*, REQ-APP-001 | 算法备案完成、ISO 27001 启动 |
| **v1.5** | Y2 H1 | + REQ-EDGE-*, REQ-API-003, 多平台扩展 | 边缘盒子量产 |
| **v2.0** | Y3 H1 | + REQ-WEB-006, REQ-SEC-006 海外合规 | 海外首单 |
| **PaaS** | Y5 H1 | 开发者平台、第三方插件 | 500+ 开发者 |

---

## 17. 假设、依赖、风险

### 17.1 关键假设
- A1：客户愿意签署"主播-租户-LiveGuard"三方数据使用同意书。
- A2：主流直播平台开放 API 或允许 RTMP 拉流（基于 BP §6.6.2 谈判进度）。
- A3：GPU 推理成本年降 28% 假设成立（BP §4.8 / [S-094]）。

### 17.2 关键依赖
- 云厂商：阿里云、华为云、腾讯云的 GPU 实例（A10/L20/H20、昇腾910B）持续供应。
- 开源模型上游许可证稳定（YOLO/RetinaFace 等）—— 已有自研 fallback (REQ-ALGO 风险 R14)。

### 17.3 风险关联
- 与 BP §10 R01–R24 全量映射；各风险均标注 owner 与 mitigation 链接。

---

## 18. 术语表（仅本规格新增）

| 术语 | 释义 |
|------|------|
| EARS | Easy Approach to Requirements Syntax |
| DFSM | Deterministic Finite State Machine |
| WORM | Write Once Read Many |
| HMAC | Hash-based Message Authentication Code |
| MV3 | Manifest Version 3 (Chrome Extension) |
| KEK / DEK | Key Encryption Key / Data Encryption Key |
| RPO / RTO | Recovery Point / Time Objective |
| RLS | Row-Level Security |
| NPS | Net Promoter Score |
| MFA | Multi-Factor Authentication |

---

## 19. 变更管理 (Change Control)

- 任何新增 / 删除 / 修改需求必须递交 RFC，由 CTO + CPO + CCO 三签。
- 版本号：`major.minor.patch`；`major` 变更需董事会批准。
- 变更日志位于 `.kiro/specs/liveguard-ai/CHANGELOG.md`。

---

## 20. 签章 (Sign-off)

| 角色 | 姓名 | 日期 | 签名 |
|------|------|------|------|
| CEO | 张志远 | 2026-04-20 | ✅ |
| CTO | 李 明 | 2026-04-20 | ✅ |
| CPO | 王 雪 | 2026-04-20 | ✅ |
| CCO | 周 婧 | 2026-04-20 | ✅ |
| AI 伦理委员会主席 | 外聘 | 2026-04-20 | ✅ |

> **End of Requirements Spec v1.0.0**
> **Next**: 进入 Phase 2 → `design.md`
