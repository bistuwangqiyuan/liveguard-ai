# 部署指南 · LiveGuard AI

> 覆盖本地开发、Docker Compose 全栈、Kubernetes Helm 路径、可观测与灾备。

## 1. 环境矩阵

| 场景 | 方案 | 适用 |
| --- | --- | --- |
| 开发机 / 演示 | `make dev` (docker-compose) | 单机 · 全部组件拉齐 |
| 预发 | Kubernetes + 托管 DB/Redis/Kafka | 灰度小流量 |
| 生产 | K8s + RDS + Redis Cluster + Kafka + 多可用区 + CDN | 大规模 SaaS |

## 2. 本地 Docker Compose

```bash
cp liveguard/.env.example .env          # 如有
docker compose -f infra/docker-compose.yml up -d
# 等待健康：
docker compose -f infra/docker-compose.yml ps
```

组件：

- `postgres` (Timescale + pgvector 扩展) :5432
- `redis` 7 :6379
- `kafka` (Bitnami) :29092 (host)
- `minio` (S3) :9000 · 控制台 :9001
- `prometheus` :9090 · `grafana` :3001 (admin/liveguard)
- `backend` :8080 · `notify` :8081 · `console` :3000

## 3. Kubernetes（推荐生产）

### 3.1 依赖的云资源

| 资源 | 推荐 | 备注 |
| --- | --- | --- |
| Postgres | AWS RDS / 阿里云 RDS PG / 腾讯 TDSQL-C PG 16 | 启用 pgvector + Timescale |
| Redis | ElastiCache / Tair | ≥ 6.0 集群模式 |
| Kafka | MSK / 阿里云 MQ Kafka / 腾讯 CKafka | ≥ 3 broker + 3 副本 |
| 对象存储 | S3 / OSS / COS | 证据链 7 年冷归档 |
| 观测 | 云厂商 APM + 自建 Grafana | OTel + Prom + Loki |

### 3.2 环境变量（Backend）

```dotenv
LVG_ENV=prod
LVG_HTTP_HOST=0.0.0.0
LVG_HTTP_PORT=8080
LVG_DATABASE_URL=postgresql+asyncpg://liveguard:***@<rds>:5432/liveguard
LVG_REDIS_URL=rediss://:***@<redis>:6379/0
LVG_KAFKA_BOOTSTRAP=<kafka>:9092
LVG_JWT_SECRET=<高熵 32+ 字节>
LVG_CORS_ORIGINS=https://console.liveguard.ai
LVG_TRUSTED_HOSTS=console.liveguard.ai,api.liveguard.ai
LVG_LOG_LEVEL=info
```

### 3.3 健康检查 & Readiness

- **Liveness**: `GET /healthz` → 200
- **Readiness**: `GET /readyz` → 200（验证 DB/Redis/Kafka 连接）
- **Prometheus**: `GET /metrics`

Kubernetes 建议：

```yaml
livenessProbe:  { httpGet: { path: /healthz, port: 8080 }, periodSeconds: 15, timeoutSeconds: 3 }
readinessProbe: { httpGet: { path: /readyz,  port: 8080 }, periodSeconds: 10, timeoutSeconds: 3 }
resources:
  requests: { cpu: 200m, memory: 512Mi }
  limits:   { cpu: 1,    memory: 2Gi   }
```

### 3.4 HPA 基线

| 服务 | 扩缩比例 | 指标 |
| --- | --- | --- |
| backend | min 3 / max 20 | CPU 60% + P95 latency 200ms |
| notify | min 2 / max 10 | Kafka consumer lag |
| console | min 2 / max 6 | RPS p95 |

## 4. Alembic 迁移

```bash
# 生产部署前在 CI release 流水线执行
cd backend
LVG_DATABASE_URL=<prod_url> alembic upgrade head
```

> **RLS** 行级安全 + **events** 按月分区已在 `20260420_0002_postgres_enhancements.py` 迁移中启用；跨集群复制请启用 Postgres 逻辑复制 + pg_partman 预建分区。

## 5. 边缘 Agent 分发

- 建议打包 **PyInstaller** 单文件二进制（Windows / macOS / Linux）
- 生产环境默认 `privacy_mode=true` — 仅上传特征向量
- TLS + 客户端证书（mTLS），建议使用阿里云 / AWS 自有 CA

## 6. 密钥与 Secrets

| 类型 | 建议 |
| --- | --- |
| JWT/Service key | Hashicorp Vault / AWS Secrets Manager / 阿里云 KMS |
| 第三方渠道 | 厂商级 CA 签署 · 旋转周期 ≤ 90 天 |
| 边缘 client_cert | 设备注册 → short-lived JWT 换发 |

## 7. 灾备 / RTO / RPO

| 场景 | RTO | RPO | 策略 |
| --- | --- | --- | --- |
| 单 AZ 故障 | < 5min | 0 | K8s 多 AZ + RDS 主备 + Kafka 3 broker |
| Region 故障 | < 1h | < 15min | 跨 Region 冷备快照 + S3 跨区复制 |
| 算法模型回滚 | < 10min | - | `ModelRegistry` 多版本共存 · Canary 5% → 全量 |

## 8. 回滚

- Helm：`helm rollback liveguard-backend <rev>`
- DB：Alembic downgrade **only** 与应用 image 同步；生产禁止单独 downgrade
- Model：Registry 标签 `prod` 指向上一 tag · 10 分钟完成

## 9. 附：docker-compose 变量覆写

可在 `infra/docker-compose.yml` 同级 `.env` 中覆盖 `LVG_*`，也可在 `docker compose --env-file ./.env.prod up` 指定：

```dotenv
LVG_JWT_SECRET=xxxxxx
LVG_CORS_ORIGINS=https://console.example.com
```
