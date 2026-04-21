# LiveGuard Backend · FastAPI 云端控制平面

## 职责
1. 多租户 REST + WebSocket API（OpenAPI 3.1）
2. 统一 AuthN/AuthZ（OIDC + API Key + JWT）
3. 事件摄取 / 告警持久化 / SLA 计算
4. 业务规则编排（升级、抑制、闭环）
5. 对接 Notify Service、边缘 Agent、控制台

## 架构
```
HTTP/WS  →  FastAPI  →  UseCase  →  Domain  →  Repository (SQLAlchemy / Redis)
                                  ↘        ↘
                                 Kafka    Algo Core (liveguard-algo)
```

## 本地开发
```powershell
pip install -e ".[dev]"
alembic upgrade head
uvicorn liveguard_backend.main:app --reload --port 8080
```

## 关键路由

| 路径 | 方法 | 说明 |
|------|------|------|
| `/healthz` | GET | 存活检查 |
| `/readyz` | GET | 依赖就绪 |
| `/metrics` | GET | Prometheus |
| `/v1/auth/token` | POST | OAuth2 Password flow（demo） |
| `/v1/streams` | GET/POST | 直播流管理 |
| `/v1/streams/{id}/events` | GET | 事件流（分页） |
| `/v1/alerts` | GET | 告警列表 |
| `/v1/alerts/{id}/ack` | POST | 确认告警 |
| `/v1/tenants` | GET/POST | 租户 |
| `/v1/hosts` | GET/POST | 主播档案 |
| `/v1/billing/usage` | GET | 计量 |
| `/v1/ingest/signals` | POST | 边缘上行（信号帧） |
| `/ws/v1/streams/{id}` | WS | 实时状态推送 |
