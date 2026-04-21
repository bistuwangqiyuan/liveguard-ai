# LiveGuard Edge · 边缘 Agent

## 职责
1. **拉流**：RTMP / SRT / WHEP / RTSP 多协议拉流（FFmpeg/AV）
2. **轻量推理**：运行 algo 的 mock 或量化版本，抽取 6 路信号（face/person/reid/liveness/action/audio）
3. **上行**：批量 gzip + HTTP(S) 上传到 `/v1/ingest/signals`，失败指数退避重试
4. **隐私模式**：默认不上传原始视频，仅上传数值特征

## 用法
```powershell
pip install -e ".[dev,cv]"
liveguard-edge run --stream-id demo1 --rtmp rtmp://push.example.com/live/demo1 \
  --backend https://api.liveguard.ai --token $env:LVG_EDGE_TOKEN
```

不装 opencv 时回退到 **synthetic source** — 生成彩色棋盘+噪声图像，方便
CI 与无相机环境。
