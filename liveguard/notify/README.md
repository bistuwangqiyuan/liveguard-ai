# LiveGuard Notify · 多通道通知服务

## 职责
消费 `notify.jobs.v1` 主题里的发送任务；按通道（SMS / Voice / DingTalk /
WeWork / Feishu / Webhook / App Push）投递，并带指数退避重试。

## 通道矩阵
| Severity | 默认通道 |
|----------|----------|
| INFO | Webhook |
| P2 | Webhook + 钉钉 |
| P1 | Webhook + 钉钉 + 企业微信 + SMS |
| P0 | Webhook + 钉钉 + 企业微信 + SMS + Voice |

## 端点
* `POST /v1/send` — 同步发送（供 backend 直接调用）
* `POST /v1/webhooks/result` — 上游 callback（短信/电话回调结果）
* `GET /healthz`, `GET /metrics`

## 安全
* 每个通道的 AK/SK 走 Vault/KMS，不入源。
* `X-Signature: sha256=..` 对 webhook 调用做 HMAC 校验。
* 所有外部 HTTP 走带 TLS pinning 的 httpx client。
