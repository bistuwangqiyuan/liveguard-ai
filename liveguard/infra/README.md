# infra/ · 基础设施 & 部署

本目录汇集 LiveGuard 所需的一切基础设施资源：

```
infra/
├── docker-compose.yml        # 本地全栈（postgres + redis + kafka + minio + prometheus + grafana + backend/notify/console）
├── prometheus/               # prometheus 抓取配置
├── db/init/                  # postgres 启动时执行的初始化 SQL（扩展 / 角色）
└── README.md
```

## 本地开发流程

```bash
# 1. 启动基础设施
docker compose -f infra/docker-compose.yml up -d postgres redis kafka minio prometheus grafana

# 2. 跑 Alembic 迁移（首次）
cd backend && alembic upgrade head

# 3. 填种子
python scripts/seed.py

# 4. 启动 backend / notify / console（或继续用 compose 的 backend/notify/console 服务）
make dev

# 5. 打开控制台
open http://localhost:3000
```

## 观测端点

| 组件 | URL |
| --- | --- |
| Backend Swagger | http://localhost:8080/docs |
| Backend Metrics | http://localhost:8080/metrics |
| Notify Metrics | http://localhost:8081/metrics |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3001 (admin / liveguard) |
| MinIO Console | http://localhost:9001 (liveguard / liveguardminio) |

## 生产部署

请前往 `infra/helm/`（规划中）获取 Kubernetes Helm Chart。对于公有云托管：

- AWS：EKS + RDS Postgres + ElastiCache Redis + MSK Kafka + S3
- 阿里云：ACK + RDS PG + Tair + MSK + OSS
- 腾讯云：TKE + TDSQL-C PG + Redis + CKafka + COS
