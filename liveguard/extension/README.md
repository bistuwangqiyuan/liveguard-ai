# LiveGuard Browser Extension · 守播浏览器插件 (MV3)

> 为 抖音 / 快手 / 淘宝直播 / 视频号 网页主播助手提供 **本地监听 + 云端上报** 能力。无需机顶盒、无需采集卡——打开后台即守护。

## 能力

- **站点自动识别**：注入 `content script` 到 `live.douyin.com`、`live.kuaishou.com`、`liveplatform.taobao.com`、`channels.weixin.qq.com`。
- **音视频轻量探测**：通过 `<video>` 元素 + `MediaStreamTrack` 抓取关键帧 / 音频缓冲（仅在本地处理 / 或按需上报特征向量）。
- **隐私模式**：默认仅上传**信号特征**（融合得分、人形/人脸置信度），绝不上传原始画面；用户可显式授权截帧诊断模式。
- **实时状态徽章**：Toolbar icon 根据 `last_state` 染色（绿=ON_DUTY / 橙=BRIEF_AWAY / 红=LONG_AWAY / 闪红=CHEAT_FLAGGED）。
- **告警转发**：从 backend SSE / WebSocket 拉取，推送为浏览器原生通知。

## 安装 (Chromium)

```bash
# 1. 将 extension 目录加载为未打包扩展
Chrome → chrome://extensions → 打开「开发者模式」→ 「加载已解压的扩展程序」→ 选择 liveguard/extension

# 2. 配置后端地址（options 页面）
# 3. 登录并绑定 stream_id → tenant_id
```

## 目录

```
extension/
├── manifest.json           # MV3 manifest
├── src/
│   ├── background.ts       # Service worker：消息路由 / SSE 订阅 / 通知派发
│   ├── content.ts          # 注入到直播后台，抓取 <video> 特征
│   ├── popup.html / popup.ts
│   └── options.html / options.ts
├── icons/ (16/32/48/128)
└── README.md
```

本阶段仅提供 **骨架**（manifest + background + content + popup），接入真实后端以 `LVG_BACKEND_URL` 为准。
