// LiveGuard content script — 注入到直播后台页面，抓取 <video> 轻量特征。
// 隐私默认：仅抽取 "亮度 / 运动量 / 音频 RMS" 等特征向量，绝不上传原始帧。

(function () {
  "use strict";

  const SAMPLE_INTERVAL_MS = 2000;
  const FRAME_W = 48;
  const FRAME_H = 27;

  let prevGray = null;

  function findVideoEl() {
    const vids = Array.from(document.querySelectorAll("video"));
    return vids.find((v) => v.readyState >= 2 && v.videoWidth > 0) || null;
  }

  function grabFeatures(video) {
    const canvas = document.createElement("canvas");
    canvas.width = FRAME_W;
    canvas.height = FRAME_H;
    const ctx = canvas.getContext("2d", { willReadFrequently: true });
    if (!ctx) return null;
    try {
      ctx.drawImage(video, 0, 0, FRAME_W, FRAME_H);
    } catch (_) {
      return null; // CORS / security errors 直接跳过
    }
    const { data } = ctx.getImageData(0, 0, FRAME_W, FRAME_H);

    const n = FRAME_W * FRAME_H;
    const gray = new Float32Array(n);
    let sum = 0;
    let sq = 0;
    for (let i = 0; i < n; i++) {
      const r = data[i * 4],
        g = data[i * 4 + 1],
        b = data[i * 4 + 2];
      const y = 0.299 * r + 0.587 * g + 0.114 * b;
      gray[i] = y;
      sum += y;
      sq += y * y;
    }
    const mean = sum / n;
    const variance = sq / n - mean * mean;

    let motion = 0;
    if (prevGray) {
      for (let i = 0; i < n; i++) motion += Math.abs(gray[i] - prevGray[i]);
      motion /= n;
    }
    prevGray = gray;

    return {
      brightness: mean / 255,
      contrast: Math.sqrt(Math.max(0, variance)) / 255,
      motion: motion / 255,
      resolution: `${video.videoWidth}x${video.videoHeight}`,
      paused: video.paused,
      muted: video.muted,
    };
  }

  function classifyState(feat) {
    if (!feat) return "IDLE";
    if (feat.paused) return "IDLE";
    if (feat.motion < 0.003) return "BRIEF_AWAY";
    if (feat.brightness < 0.03) return "LONG_AWAY";
    return "ON_DUTY";
  }

  async function tick() {
    const video = findVideoEl();
    if (!video) return;
    const feat = grabFeatures(video);
    if (!feat) return;
    const state = classifyState(feat);

    chrome.runtime.sendMessage({ type: "LG_STATE", state });
    chrome.runtime.sendMessage({
      type: "LG_SIGNAL",
      data: {
        streamId: location.hostname + location.pathname,
        features: { ...feat, state_hint: state },
      },
    });
  }

  setInterval(tick, SAMPLE_INTERVAL_MS);
  console.log("[LiveGuard] content script mounted on", location.hostname);
})();
