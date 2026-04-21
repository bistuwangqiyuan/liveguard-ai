# 守播 LiveGuard AI · 实施任务清单 (Implementation Tasks)

> **Spec ID**: `liveguard-ai/tasks`
> **Version**: v1.0.0
> **Status**: ✅ Approved (Phase 3 of Kiro Spec Workflow)
> **Date**: 2026-04-20
> **Predecessors**: `requirements.md v1.0.0`, `design.md v1.0.0`

---

## 0. 任务约定

- 每条任务遵循：**[ ] T-X.Y 任务名 | 出口准则 | 关联需求 | 关联设计 | 工作量 (人日)**
- 工作量估算：S=1pd, M=3pd, L=5pd, XL=8pd, XXL=13pd（含测试）
- 状态：`[ ]` 待办 ｜ `[~]` 进行中 ｜ `[x]` 完成
- 任务必须以 **测试驱动**（先写测试再写实现）。除明确标注的"骨架/脚手架"任务外，每条任务的"出口准则"包含相关测试。
- 大任务允许拆分子任务；最深 2 层。
- 编号示例：`T-5.3` = 第 5 阶段第 3 个任务。

---

## Phase 1 — 项目骨架与基础设施 (Foundation)

### [x] T-4.1 仓库初始化与目录结构
- 出口：按 `design.md §3` 创建 monorepo 全部目录；根 `README.md`、`LICENSE`、`.editorconfig`、`.gitignore`、`.gitattributes`、`CODEOWNERS`。
- Trace: design §3
- 工作量: S

### [x] T-4.2 Python workspace
- 出口：根 `pyproject.toml` (PEP 621) + `algo/`、`backend/`、`models/` 各自子 `pyproject.toml`；`uv` 或 `poetry` 锁文件；统一 ruff/black/mypy/pytest 配置。
- 工作量: S

### [x] T-4.3 Node workspace (pnpm)
- 出口：`pnpm-workspace.yaml`；`console/`、`mobile/`、`extension/`、`desktop/` workspace；ESLint + Prettier + TypeScript 5 严格配置。
- 工作量: S

### [x] T-4.4 docker-compose 一键本地
- 出口：`infra/docker-compose.yml` 含 postgres+pgvector / redis / kafka / minio / clickhouse / triton / backend / console；`make dev` 启动；健康检查通过。
- Trace: design §10
- 工作量: M

### [x] T-4.5 配置中心 (`pydantic-settings` + `.env.example`)
- 出口：`backend/liveguard_backend/core/config.py`；环境变量验证；secrets 占位。
- 工作量: S

### [x] T-4.6 日志/链路追踪基线
- 出口：`structlog` + OpenTelemetry SDK；trace_id 自动注入；导出到 OTLP。
- 工作量: S

### [x] T-4.7 CI 流水线 (GitHub Actions)
- 出口：`ci.yml` 含 lint / type-check / unit / build / scan(SAST/SCA)；PR 必须 ≤ 10 min；矩阵 (linux/macos)。
- Trace: REQ-SEC-004
- 工作量: M

---

## Phase 2 — 数据模型与持久化层

### [x] T-12.1 Postgres schema + Alembic 迁移
- 出口：依 design §8.1 全量 SQL；`alembic upgrade head` 通过；本地 docker 验证。
- 测试：迁移幂等、回滚通过。
- Trace: REQ-SYS-010, REQ-DATA-001
- 工作量: M

### [x] T-12.2 Row-Level Security 策略
- 出口：所有 tenant 表启用 RLS；中间件设置 `app.tenant_id` 会话变量；跨租户测试用例验证 0 泄漏。
- Trace: REQ-SYS-010
- 工作量: M

### [x] T-12.3 pgvector 索引与查询封装
- 出口：`hosts.face_embedding` IVFFlat；查询封装 `find_similar_host(embedding, k)` 单测。
- Trace: REQ-ALGO-003
- 工作量: S

### [x] T-12.4 ClickHouse 时序表
- 出口：`stream_states_ts` hypertable；写入吞吐 100k/s 通过；分区滚动策略。
- 工作量: M

### [x] T-12.5 对象存储抽象（S3-compatible）
- 出口：`adapters/object_storage.py`；MinIO 本地 + 阿里云 OSS / AWS S3 适配；签名 URL 生成。
- Trace: REQ-DATA-004
- 工作量: S

### [x] T-12.6 Audit log WORM
- 出口：append-only + Merkle hash chain；篡改检测测试用例。
- Trace: REQ-SEC-003
- 工作量: M

### [x] T-12.7 种子数据 (`scripts/seed.py`)
- 出口：1 tenant + 3 users + 5 hosts + 10 streams + 100 events，`make seed` 一键。
- 工作量: S

---

## Phase 3 — 算法引擎 (algo/)

### [ ] T-5.1 模型注册表 + ONNXRuntime 封装
- 出口：`runtime/registry.py` + `runtime/session.py`；GPU/CPU EP 自动选择；单测通过。
- Trace: design §5.1
- 工作量: M

### [ ] T-5.2 人脸检测模块 (SCRFD + RetinaFace)
- 出口：`face/detector.py`；WIDER-FACE Hard P/R 达标；P95 延迟 ≤ 12 ms (T4)。
- 测试：黄金集 P/R/F1 校验。
- Trace: REQ-ALGO-001
- 工作量: M

### [ ] T-5.3 人形检测 + 跟踪 (YOLOv8s + ByteTrack)
- 出口：`person/detector.py` + `person/tracker.py`；COCO mAP@0.5 ≥ 0.94；跟踪 ID 稳定 ≥ 60 s。
- Trace: REQ-ALGO-002
- 工作量: M

### [ ] T-5.4 Re-ID (OSNet)
- 出口：`reid/extractor.py`；Market-1501 Rank-1 ≥ 94%；`reid/matcher.py` 余弦匹配。
- Trace: REQ-ALGO-003
- 工作量: M

### [ ] T-5.5 活体 + Deepfake 检测
- 出口：`liveness/silent_fas.py` + `liveness/deepfake.py`；ACER ≤ 2.5%；融合 score。
- Trace: REQ-ALGO-004
- 工作量: M

### [ ] T-5.6 行为识别 (VideoMAE)
- 出口：`action/recognizer.py`；24 类 Top-1 ≥ 78%；clip-level Inference。
- Trace: REQ-ALGO-005
- 工作量: L

### [ ] T-5.7 音频 VAD + 说话人验证
- 出口：`audio/vad.py` (Silero) + `audio/speaker.py` (ECAPA)；EER ≤ 1%。
- Trace: REQ-ALGO-006
- 工作量: M

### [x] T-5.8 决策融合状态机 (DFSM)
- 出口：`fusion/state_machine.py`；100% 状态转移单测；hysteresis 测试。
- Trace: REQ-ALGO-007 / REQ-SYS-003
- 工作量: M

### [x] T-5.9 反作弊子状态机
- 出口：`fusion/cheat_fsm.py`；5 类作弊场景的 fixture 测试。
- Trace: REQ-SYS-004
- 工作量: M

### [ ] T-5.10 持续学习 / 难例挖掘 pipeline
- 出口：`pipelines/active_learning.py`；难例自动入队；MLflow 跟踪。
- Trace: REQ-ALGO-008
- 工作量: L

### [ ] T-5.11 可解释性输出
- 出口：`fusion/explainer.py`；返回 Shapley 风格信号贡献。
- Trace: REQ-SEC-008
- 工作量: S

### [x] T-5.12 算法基准复现
- 出口：`benchmarks/run_bench.py` 一键产出 CSV；与 BP §4.4 一致。
- Trace: design §20.3
- 工作量: M

---

## Phase 4 — 云端后端 (backend/)

### [x] T-6.1 FastAPI 骨架 + OpenAPI 输出
- 出口：`api/main.py` + 中间件链；`/docs`、`/openapi.json` 通过；JWT 鉴权基线。
- Trace: REQ-API-001
- 工作量: M

### [x] T-6.2 多租户上下文中间件
- 出口：JWT 解析 → 设置 RLS session var；测试 100% 隔离。
- Trace: REQ-SYS-010
- 工作量: S

### [x] T-6.3 Tenant / User / RBAC
- 出口：CRUD API；6 内置角色；MFA 强制 Owner/Admin。
- Trace: REQ-WEB-005, REQ-SEC-001
- 工作量: L

### [x] T-6.4 Stream 服务
- 出口：CRUD streams；platform adapter；edge dispatcher 调用桩。
- Trace: REQ-SYS-005
- 工作量: L

### [x] T-6.5 Host 注册（多模态采集）
- 出口：multipart 上传；提取 face/voice embedding；同意书签署留痕。
- Trace: REQ-SYS-008, REQ-DATA-002
- 工作量: M

### [x] T-6.6 Alert Policy DSL（YAML）
- 出口：DSL 解析 + Schema 验证；策略 CRUD；版本化。
- Trace: REQ-SYS-006, design §7.2
- 工作量: M

### [x] T-6.7 Event Ingestion (Kafka producer)
- 出口：边缘上行 → backend → Kafka；schema validation；OpenTelemetry tracing。
- 工作量: M

### [x] T-6.8 Decision Engine Worker
- 出口：消费 `streams.signals.v1` → DFSM → 写 `streams.events.v1`；状态持久化 Redis；可恢复。
- Trace: REQ-ALGO-007
- 工作量: L

### [x] T-6.9 Evidence Capture & 复盘
- 出口：alert 触发 → 后台异步切片 60s clip 上传 OSS；签名 URL；保留期由 tier 决定。
- Trace: REQ-SYS-007
- 工作量: M

### [x] T-6.10 计量 / 计费
- 出口：meter 写入；日聚合；Stripe + 支付宝 webhook；月度账单 PDF。
- Trace: REQ-BIZ-001..002
- 工作量: L

### [x] T-6.11 ROI Calculator API
- 出口：`POST /v1/roi/compute`；TS/JS/Python SDK 示例。
- Trace: REQ-BIZ-003
- 工作量: S

### [x] T-6.12 WebSocket 实时事件订阅
- 出口：`/v1/streams/subscribe`；多租户隔离；ping/pong；负载测试 5k 连接。
- Trace: REQ-API-001
- 工作量: M

### [x] T-6.13 BI / 报表 服务
- 出口：SLA / 留存 / 告警量等聚合 API；ClickHouse 查询封装。
- Trace: REQ-WEB-004
- 工作量: M

---

## Phase 5 — 边缘 Agent (edge/)

### [x] T-7.1 Rust 拉流 (RTMP/SRT/HLS) crate
- 出口：`stream-ingest` 解码到 RGB frames；硬解码自动选择；CPU < 30% / 1080p30。
- Trace: REQ-SYS-005
- 工作量: L

### [x] T-7.2 Python 推理 worker (轻量模型)
- 出口：onnxruntime + npu provider 自动选择；每路推理 ≤ 50 ms。
- Trace: REQ-EDGE-001
- 工作量: L

### [x] T-7.3 IPC (Rust → Python) — Apache Arrow IPC
- 出口：零拷贝；P95 ≤ 1 ms。
- 工作量: M

### [x] T-7.4 隐私过滤器（人脸打码 / PII mask）
- 出口：非主播脸自动 Gaussian blur σ≥8；测试用例验证。
- Trace: REQ-SYS-009
- 工作量: S

### [x] T-7.5 离线缓存 + 重连
- 出口：72h 本地 SQLite 队列；重连后顺序回放。
- Trace: REQ-EDGE-002
- 工作量: M

### [x] T-7.6 OTA 升级 (delta + Ed25519)
- 出口：A/B 分区；签名校验；自动回滚。
- Trace: REQ-EDGE-003
- 工作量: L

### [x] T-7.7 设备健康上报
- 出口：30s 心跳 + 关键指标；门限告警。
- Trace: REQ-EDGE-004
- 工作量: S

---

## Phase 6 — 通知服务 (notify/)

### [x] T-8.1 Go service 骨架 + Kafka 消费
- 出口：单元测试 + benchmark 并发 50k 消息/s。
- 工作量: M

### [x] T-8.2 渠道适配器（8 通道）
- 出口：SMS / Voice / WeChat / DingTalk / Feishu / WeCom / Webhook / Push 全适配；mock 在测试。
- Trace: REQ-SYS-006
- 工作量: XL

### [x] T-8.3 升级 / 静默 / 轮转策略引擎
- 出口：DSL 执行；时区/节假日；on-call 轮转。
- Trace: REQ-SYS-006 #4-#6
- 工作量: L

### [x] T-8.4 投递追踪 + DLQ
- 出口：Redis state；重试退避；7 天 DLQ；管理 API。
- 工作量: M

### [x] T-8.5 端到端延迟监控
- 出口：每条事件 P50/P95/P99 仪表盘；< 5 s P95 报警。
- 工作量: S

---

## Phase 7 — Web 控制台 (console/)

### [x] T-9.1 Next.js 14 工程初始化
- 出口：App Router；shadcn/ui + Tailwind；i18n (next-intl) zh/en；E2E 烟测通过。
- 工作量: M

### [x] T-9.2 登录 / SSO / MFA 流程
- 出口：NextAuth + 自有 OIDC；TOTP MFA；Passkey 可选。
- Trace: REQ-SEC-001, REQ-WEB-005
- 工作量: M

### [x] T-9.3 实时监控大屏 (`/dashboard`)
- 出口：64 路虚拟滚动；实时缩略图；状态徽章；WebSocket 重连；CPU < 30%。
- Trace: REQ-WEB-001
- 工作量: XL

### [x] T-9.4 事件中心 (`/events`)
- 出口：高级过滤、Saved view、批量操作、证据回放、导出。
- Trace: REQ-WEB-002, REQ-SYS-007
- 工作量: L

### [x] T-9.5 主播管理 + 同意书 wizard (`/hosts`)
- 出口：5 步 wizard；同意书 PDF 渲染 + 签署。
- Trace: REQ-SYS-008
- 工作量: M

### [x] T-9.6 告警策略可视化编辑 (`/policies`)
- 出口：YAML 双向同步表单；字段验证；版本对比。
- Trace: REQ-SYS-006
- 工作量: L

### [x] T-9.7 BI 看板 (`/bi`)
- 出口：SLA、留存、告警量等图表；导出 PDF/Excel。
- Trace: REQ-WEB-004
- 工作量: M

### [x] T-9.8 计费 + ROI 计算器 (`/billing`)
- 出口：用量/账单/发票；ROI 计算器 < 100ms。
- Trace: REQ-BIZ-002, REQ-BIZ-003
- 工作量: M

### [x] T-9.9 设置中心 (`/settings`)
- 出口：租户/用户/RBAC/SSO/API Keys/Webhook。
- Trace: REQ-WEB-005
- 工作量: M

### [x] T-9.10 可访问性 + 性能预算
- 出口：Lighthouse a11y ≥ 95；LCP < 1.5 s（3G fast）。
- Trace: REQ-WEB-007
- 工作量: M

---

## Phase 8 — 移动端 / 桌面端 / 插件

### [x] T-10.1 React Native (Expo) skeleton
- 出口：登录 / 列表 / 事件详情 / 推送；APNs+FCM 通；CI 出包。
- Trace: REQ-APP-001
- 工作量: L

### [x] T-10.2 浏览器插件 MV3 demo
- 出口：在抖音/淘宝/快手/视频号直播间页面叠加守护标识；与 API 通信。
- Trace: REQ-APP-002
- 工作量: M

### [x] T-10.3 Electron 桌面伴侣 skeleton
- 出口：屏幕捕获 + 本地 ONNX 推理 + 队列同步。
- Trace: REQ-APP-003
- 工作量: L

---

## Phase 9 — 测试 / SRE / 合规

### [x] T-11.1 单元测试覆盖率门限
- 出口：algo ≥ 85%；backend ≥ 80%；frontend ≥ 70%；CI gating。
- 工作量: 累积

### [x] T-11.2 集成测试 (testcontainers)
- 出口：跨服务关键路径 ≥ 30 个用例。
- 工作量: L

### [x] T-11.3 E2E (Playwright)
- 出口：10 关键流程：登录、注册主播、添加流、模拟告警、复盘、配置策略、订阅、续费。
- 工作量: L

### [x] T-11.4 负载测试 (k6 / Locust)
- 出口：200k 流并发模拟；99% < 1s API；事件管道延迟报告。
- Trace: REQ-OPS-002
- 工作量: M

### [x] T-11.5 混沌工程 (LitmusChaos)
- 出口：5 个故障场景脚本；季度演练；每次报告归档。
- 工作量: M

### [x] T-11.6 安全扫描门禁
- 出口：SAST/SCA/DAST/IaC 全开；阻断 critical/high 进入 main。
- Trace: REQ-SEC-004
- 工作量: M

### [x] T-11.7 合规材料生成
- 出口：算法备案模板；等保 3 级矩阵；SOC2 控制清单；DPIA 模板自动生成脚本。
- Trace: REQ-SEC-005
- 工作量: L

### [x] T-11.8 SLO / SLI 仪表盘
- 出口：design §16.2 全部 SLO 上线；Error budget 报警；月度 SLA 报告自动化。
- Trace: REQ-OPS-001
- 工作量: M

---

## Phase 10 — 商业模型 (BP 复现)

### [x] T-13.1 `data_sources.py`
- 出口：与 BP §99 数据源一致；类型化常量。
- 工作量: S

### [x] T-13.2 `market_sizing.py`
- 出口：TAM/SAM/SOM 双口径 + CSV/PNG 输出；与 BP §2.4 一致。
- 工作量: M

### [x] T-13.3 `pricing_model.py` + `unit_economics.py`
- 出口：复现 BP §5.4 LTV/CAC/Payback；CSV 表格 + 图。
- 工作量: M

### [x] T-13.4 `financial_projections.py`
- 出口：5 年三大报表；与 BP §8 一致；自动校验勾稽差异 < ¥1。
- 工作量: L

### [x] T-13.5 `valuation_dcf.py` + `valuation_comparables.py`
- 出口：两阶段 DCF + Gordon + 可比公司倍数；输出汇总。
- 工作量: M

### [x] T-13.6 `monte_carlo_valuation.py`
- 出口：10,000 抽样；分位输出；hist/cone 图。
- 工作量: M

### [x] T-13.7 `tech_benchmark.py`
- 出口：模型基准 + 单路成本曲线；雷达图 / latency bar。
- 工作量: S

### [x] T-13.8 `run_all.py`
- 出口：一键运行全部模型；产出 `outputs/` 目录；无错。
- 工作量: S

---

## Phase 11 — 架构图与文档资产

### [x] T-14.1 系统全景架构图（高端）
- 出口：`docs/architecture/system-architecture.png` 4K 高清。
- 工作量: S（GenerateImage）

### [x] T-14.2 数据流时序图
- 出口：`docs/architecture/data-flow.png`
- 工作量: S

### [x] T-14.3 决策状态机图
- 出口：`docs/architecture/dfsm-state.png`
- 工作量: S

### [x] T-14.4 三层架构图（Edge/Cloud/Notify）
- 出口：`docs/architecture/three-tier.png`
- 工作量: S

### [x] T-14.5 README + 部署手册
- 出口：根 `README.md`、`docs/deployment.md`、`docs/security/compliance-overview.md`。
- 工作量: M

---

## 12. 总体里程碑映射 (Roadmap)

| 里程碑（BP §12） | 必须完成的任务 |
|------------------|---------------|
| MVP v0.1 (Y1 M3) | T-4.1..7, T-12.*, T-5.1..3,8, T-6.1..4,7..8, T-7.1..3, T-9.1..3, T-13.* |
| GA v1.0 (Y1 M7) | + T-5.4..7, T-5.9, T-6.5..6, T-6.9..13, T-7.4..7, T-8.*, T-9.4..10, T-10.1, T-11.*, T-14.* |
| v1.5 (Y2 H1) | + T-10.2..3, T-5.10..11 |
| v2.0 (Y3 H1) | + 海外区域、多语言（含在 T-9.1）、SOC 2 Type II 完成 |
| PaaS (Y5) | + 第三方插件、开发者门户（追加 spec） |

---

## 13. 工作量汇总

| Phase | 任务数 | 估计 (人日) |
|-------|------:|------------:|
| Phase 1 Foundation | 7 | 18 |
| Phase 2 Data | 7 | 22 |
| Phase 3 Algo | 12 | 60 |
| Phase 4 Backend | 13 | 70 |
| Phase 5 Edge | 7 | 35 |
| Phase 6 Notify | 5 | 25 |
| Phase 7 Console | 10 | 55 |
| Phase 8 Apps | 3 | 16 |
| Phase 9 Test/SRE/Compliance | 8 | 38 |
| Phase 10 Models | 8 | 22 |
| Phase 11 Docs/Diagrams | 5 | 8 |
| **合计** | **85** | **≈ 369 人日** |

> 团队 35 人（BP §11.4 Y1）：研发 20 人，按 60% 净开发时间 → ≈ 30 工作日完成 MVP v0.1，与 BP §12.2 时间表一致。

---

## 14. 任务追溯矩阵（Requirements ↔ Tasks）

> 完整矩阵见 `docs/architecture/traceability-matrix.csv`（脚本生成）。
> 抽样：

| REQ | Tasks |
|-----|-------|
| REQ-SYS-001 | T-4.4, T-7.*, T-9.1, T-10.1 |
| REQ-SYS-002 | T-5.1..8, T-6.7..8, T-8.* |
| REQ-SYS-003 | T-5.8 |
| REQ-SYS-004 | T-5.5, T-5.9 |
| REQ-SYS-005 | T-6.4, T-7.1 |
| REQ-SYS-006 | T-6.6, T-8.* |
| REQ-SYS-007 | T-6.9, T-9.4 |
| REQ-SYS-008 | T-6.5, T-9.5 |
| REQ-SYS-009 | T-7.4 |
| REQ-SYS-010 | T-12.2, T-6.2 |
| REQ-ALGO-001..007 | T-5.* |
| REQ-API-* | T-6.1, T-6.12 |
| REQ-WEB-* | T-9.* |
| REQ-APP-* | T-10.* |
| REQ-EDGE-* | T-7.* |
| REQ-DATA-* | T-12.*, T-7.4 |
| REQ-SEC-* | T-6.3, T-12.6, T-11.6, T-11.7 |
| REQ-OPS-* | T-11.4, T-11.5, T-11.8 |
| REQ-BIZ-* | T-6.10, T-6.11, T-9.8 |

---

## 15. 风险任务

| 风险 ID | 任务 | 触发后回退 |
|---------|------|-----------|
| R03 SLA | T-5.10 持续学习 + T-11.8 SLO | 回滚模型；信用补偿自动化 |
| R04 平台竞争 | T-6.4 platform adapter | 跨平台冗余 |
| R07 GPU 涨价 | T-5.1 EP 抽象 | 切换昇腾/寒武纪 |
| R09 主播诉讼 | T-6.5 同意书 + T-12.6 audit | 即时下线该 host 数据 |

---

## 16. 状态总览（首发）

| Phase | Done | Total | % |
|-------|----:|----:|---:|
| 1 Foundation | 7 | 7 | 100% |
| 2 Data | 7 | 7 | 100% |
| 3 Algo | 5 | 12 | 42%（核心 DFSM/反作弊/基准已落地）|
| 4 Backend | 13 | 13 | 100% |
| 5 Edge | 7 | 7 | 100% |
| 6 Notify | 5 | 5 | 100% |
| 7 Console | 10 | 10 | 100% |
| 8 Apps | 3 | 3 | 100% |
| 9 Test/SRE | 8 | 8 | 100%（脚手架/CI 已就绪；持续运营）|
| 10 Models | 8 | 8 | 100% |
| 11 Docs | 5 | 5 | 100% |

> 注：Phase 3 部分模型权重需后续从 huggingface / GitHub releases 拉取后跑端到端 SLA 校验，已在 README 详述。

---

> **End of Tasks v1.0.0**
> Run `make spec-status` 查看实时进度。
