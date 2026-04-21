(async () => {
  const cfg = await chrome.storage.sync.get({ backendUrl: "http://localhost:8080" });
  document.getElementById("backend").textContent = cfg.backendUrl;

  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (tab?.url) {
    try {
      document.getElementById("host").textContent = new URL(tab.url).hostname;
    } catch {
      /* ignore */
    }
  }

  // 监听来自 content script 的状态更新
  chrome.runtime.onMessage.addListener((msg) => {
    if (msg?.type === "LG_STATE") {
      const el = document.getElementById("state");
      el.textContent = msg.state;
      el.className = `state-${msg.state}`;
    } else if (msg?.type === "LG_SIGNAL" && msg.data?.features) {
      const f = msg.data.features;
      document.getElementById("brightness").textContent = f.brightness?.toFixed(3) ?? "—";
      document.getElementById("motion").textContent = f.motion?.toFixed(4) ?? "—";
    }
  });
})();
