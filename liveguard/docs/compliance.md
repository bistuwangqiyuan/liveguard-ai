# 合规 & 隐私附录 · LiveGuard AI

> 世界级企业 SaaS 的合规是**代码级承诺** — 本附录提供可审计、可落地的实施清单。适用于中国大陆、欧盟 GDPR、美国 CCPA 三地框架。

## 0. 合规矩阵（一图看全）

| 框架 | 适用 | LiveGuard 对应措施 |
| --- | --- | --- |
| 《网络安全法》 | 中国大陆 | 数据本地化 · 等保三级 · 日志 6 月 |
| 《数据安全法》 | 中国大陆 | 数据分级 · 跨境评估 |
| 《个人信息保护法》(PIPL) | 中国大陆 | 最小必要 · 主体权利 · DPO |
| GDPR | 欧盟 | DPA · 数据可携 · 被遗忘权 |
| CCPA / CPRA | 美国加州 | 销售可选退出 · 敏感信息披露 |
| ISO 27001 / SOC 2 Type II | 全球 | 控制目标映射（见 §6） |
| 等保 2.0 三级 | 中国 | 物理 → 应用 → 数据 分层控制 |

## 1. 数据分类

| 类型 | 举例 | 处理原则 |
| --- | --- | --- |
| **一般数据** | 系统日志、匿名统计 | 聚合 · 去标识 |
| **个人信息** | 主播姓名、手机号（用于告警） | 单独同意 + 可撤回 |
| **敏感个人信息** | 人脸向量、声纹向量 | AES-256 存储 · 端到端加密传输 · 仅用于身份识别 |
| **商业机密** | 直播间 GMV、合作佣金 | 租户隔离 · RLS · Vault |

## 2. 最小化采集（隐私模式 Privacy Mode）

- 默认仅上传**特征向量**：面部关键点 / 融合得分 / 状态 hint / 置信度
- 原始视频**永不出边缘**；仅在用户显式授权的"诊断模式"中以临时 URL 存档 S3（24h TTL 自动删除）
- 边缘端支持**离线人脸库** — 主播比对在本地完成，服务端仅收到 yes/no + 置信度

## 3. 主体权利（Data Subject Rights）

| 权利 | 实现路径 | SLA |
| --- | --- | --- |
| 知情权 | `/privacy/policy` · 首次录入主播时同意流 | 即时 |
| 查询 / 访问 | 自助 → 导出 JSON · 包含所有向量 hash | ≤ 15 天 |
| 更正 | 控制台"主播管理" / API `PATCH /v1/hosts/{id}` | ≤ 7 天 |
| 删除 / 被遗忘 | 异步作业 — 清理 DB + 对象存储 + Kafka key level tombstone | ≤ 30 天 |
| 可携带 | 导出 SQL 行 + S3 对象 manifest (RFC 8949 CBOR) | ≤ 15 天 |
| 同意撤回 | `/v1/consent/withdraw` · 立刻停止上报 | 即时 |

## 4. 跨境 & 本地化

- 默认**区域感知路由**：`region=cn-east-1` 的租户数据不会跨境
- 跨境传输需走 **PIPL 第 38 条** 安全评估 / 标准合同；系统支持 tenant 级开关
- GDPR EEA 出境：采用欧盟标准合同条款 SCC + 补充措施 TIAs

## 5. 安全控制

| 层 | 控制 | 工具 |
| --- | --- | --- |
| 身份 | MFA · SSO (OIDC / SAML) · FIDO2 | Auth0 / 自建 |
| 传输 | TLS 1.3 · HSTS · 客户端 mTLS (边缘) | ACM / Let's Encrypt |
| 存储 | AES-256 静态加密 · KMS 轮换 | RDS TDE + S3 SSE-KMS |
| 密钥 | Vault / KMS · 90 天轮换 | Hashicorp Vault |
| 秘密 | 禁止明文 · CI 扫描 gitleaks | pre-commit + GH Actions |
| 网络 | VPC 分段 · 安全组白名单 · WAF | Nginx/Envoy + Cloudflare/WAF |
| 漏洞 | SCA · SAST · DAST · 月度渗透 | pip-audit + npm audit + Trivy |
| 日志 | 不可篡改 · 6 月热 + 7 年冷 | Loki / Elastic + S3 Object Lock |

## 6. 控制映射（ISO 27001 / SOC 2）

| Control ID | 描述 | 实现 |
| --- | --- | --- |
| A.5.1 | 信息安全策略 | `docs/security-policy.md`（待发） |
| A.6.1 | 职责分离 | RBAC (`backend/security/rbac.py`) |
| A.8.2 | 数据分类 | §1 本文 |
| A.8.3 | 访问控制 | JWT + API Key + 行级 RLS |
| A.10.1 | 加密策略 | TLS 1.3 · AES-256 · KMS |
| A.12.4 | 日志 & 监控 | Prometheus + Loki + 审计表 |
| A.16.1 | 事件响应 | On-Call + Runbook (`docs/runbooks/`) |
| CC 6.1 (SOC 2) | 合乎逻辑的访问 | RBAC + RLS + MFA |
| CC 7.2 (SOC 2) | 变更检测 | GitOps + 信号告警 |

## 7. 第三方厂商

| 类别 | 厂商 | 合规 |
| --- | --- | --- |
| IaaS | AWS / 阿里云 / 腾讯云 | ISO 27001 · SOC 2 · 等保三级 |
| 通信 | 阿里云短信 · 腾讯云 · 钉钉开放平台 | MIIT 许可 · 数据在境内 |
| 邮件 | Mailgun / 阿里云邮件 | GDPR DPA · 已签 |
| 对象存储 | S3 / OSS / MinIO | 加密 + 不可变存储 |

所有第三方须签订 **DPA（数据处理协议）** 并纳入 `docs/vendors/`（生产版）。

## 8. 审计日志 Schema

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `ts` | datetime | UTC · 精度 μs |
| `actor_id` | string | user / service id |
| `actor_role` | string | `admin/ops/analyst/service` |
| `tenant_id` | string | 租户 |
| `action` | string | `LOGIN / CREATE / UPDATE / DELETE / ACK / RESOLVE` |
| `resource` | string | `alert:al_xxx` |
| `ip` | string | 源 IP · 隐去末 8 位可选 |
| `ua` | string | User-Agent |
| `trace_id` | string | OTel traceparent |
| `diff` | jsonb | 变更差异（脱敏） |

保留：**180 天热 + 7 年冷（对象存储）**。不可篡改：S3 Object Lock（Compliance 模式）。

## 9. 未成年人保护

- 平台仅服务合法注册商家 / MCN — 主播年龄 ≥ 16 岁（中国）或 ≥ 18 岁（跨境）
- 不对未成年人直接收集任何数据；若检测到疑似未成年出镜，系统将触发 `P0 · UNDERAGE_SUSPECT` 告警并冻结该流

## 10. 伦理 AI

- **透明度**：每一条告警均附 `Explainer` 人类可读理由；误报可一键反馈
- **公平性**：人脸 / 声纹模型定期按性别、肤色、地域分布做 equal error rate 公平性评估
- **可追溯**：`ModelRegistry` 记录每个版本的训练集、评估集、指标、签名
- **持续监督**：`HardExampleMiner` 收集难例 → 人工复核 → 回灌训练，形成闭环

## 11. 投诉与联系

- 数据保护官（DPO）邮箱：`dpo@liveguard.ai`（生产）
- 安全漏洞披露：`security@liveguard.ai` · PGP 公钥见 `.well-known/security.txt`
- SLA：P0 = 1h · P1 = 8h · P2 = 48h

---

> 本附录由 LiveGuard AI 团队与外部律所 / 合规顾问共同维护。若与法律法规存在冲突，以最新法规为准。
