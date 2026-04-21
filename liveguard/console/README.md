# LiveGuard Console · 守播 Web 控制台

Next.js 14 · App Router · Tailwind CSS · shadcn 风格 · SSR + Streaming

## 概览

- 多租户直播监控控制台 — 总览 / 直播流 / 告警中心 / 主播 / 实时大屏 / 设置
- 与 `liveguard-backend` 通过 REST + WebSocket 对接（通过 `next.config.mjs` rewrites 反向代理）
- 暗色系 + 品牌蓝 `brand-500 #1F6FFF` + 严重级别语义色（P0/P1/P2/INFO）
- 纯 SSR + 组件化卡片，支持零后端情况下的 fallback mock，方便演示

## 目录

```
console/
├── src/
│   ├── app/                # App Router pages (layout/page + route groups)
│   ├── components/         # UI atoms (KpiCard, SeverityBadge, StateDot)
│   └── lib/                # API client + utilities
├── public/                 # 静态资源 (favicon 等)
├── tailwind.config.ts
├── next.config.mjs
└── package.json
```

## 启动

```bash
# 1. 安装依赖（需要 Node.js ≥ 20 + pnpm / npm）
cd liveguard/console
npm install

# 2. 指向 backend（可选）
export LVG_BACKEND_URL=http://localhost:8080
export LVG_CONSOLE_TOKEN=<jwt_or_api_key>

# 3. 开发
npm run dev        # http://localhost:3000

# 4. 生产构建
npm run build && npm run start
```

后端不可达时，页面将自动回退到内置 mock 数据（`src/lib/api.ts`），用于离线演示 / 截图 / 设计评审。

## 关键环境变量

| 变量 | 说明 | 默认 |
| --- | --- | --- |
| `LVG_BACKEND_URL` | FastAPI 后端基础 URL | `http://localhost:8080` |
| `LVG_CONSOLE_TOKEN` | 控制台调用后端的 Bearer Token / API Key | 空 |

## 安全头

已在 `next.config.mjs` 预置 `X-Frame-Options=DENY`、`X-Content-Type-Options=nosniff`、`Referrer-Policy=strict-origin-when-cross-origin`、`Permissions-Policy=camera=(), microphone=(), geolocation=()`。

## 路线图

- [ ] 接入真实 WebSocket (`/ws/v1/streams/:id`) 做状态实时同步
- [ ] 内嵌 WHEP WebRTC 低延迟预览
- [ ] Saga Tracing 可视化 · 告警时间线对账
- [ ] 多语言（zh-CN / en-US）
