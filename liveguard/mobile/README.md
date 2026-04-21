# LiveGuard Mobile · 守播移动端

React Native · Expo SDK 51 · TypeScript · React Navigation 6

> 面向运维 / 商家一线巡检人员：收到 P0 告警 → 语音/震动 → 一键查看直播间实时画面 → 确认或升级。

## 功能规划

| 模块 | 说明 |
| --- | --- |
| 告警列表 | 按严重级别排序 · 支持下拉刷新 · APNs / FCM 推送深链接 |
| 直播详情 | 实时状态 + 融合得分 + WebRTC (WHEP) 预览 |
| 一键确认 | ACK / RESOLVE · 含生物识别确认（可选） |
| 值班设置 | On-Call 排班 · 勿扰时段 · 通道偏好 |
| 租户切换 | 多品牌 / 多租户角色 |

## 骨架

本阶段仅提供最小可运行骨架：`App.tsx` + 2 个占位屏幕 + API client stub。后续接入 `/v1/alerts` + 推送通道。

## 启动

```bash
cd liveguard/mobile
npm install
npx expo start            # 扫码在 Expo Go 预览
npx expo run:ios          # 需要 macOS + Xcode
npx expo run:android      # Android SDK
```

## 环境变量

使用 `app.config.ts` 的 `extra` 字段：

```bash
export LVG_BACKEND_URL=https://api.liveguard.ai
export LVG_MOBILE_TOKEN=<jwt>
```
