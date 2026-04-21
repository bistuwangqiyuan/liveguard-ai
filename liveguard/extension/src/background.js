// LiveGuard Service Worker (MV3)
// 负责：心跳、接收 content script 特征、向后端上报、订阅后端告警事件流并展示通知。

const DEFAULTS = {
  backendUrl: "http://localhost:8080",
  tenantId: "t_demo",
  token: "",
  streamId: "",
  privacyMode: true,
};

async function getConfig() {
  const saved = await chrome.storage.sync.get(DEFAULTS);
  return { ...DEFAULTS, ...saved };
}

async function postSignal(payload) {
  const cfg = await getConfig();
  try {
    const res = await fetch(`${cfg.backendUrl}/v1/ingest/signals`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(cfg.token ? { Authorization: `Bearer ${cfg.token}` } : {}),
      },
      body: JSON.stringify({
        stream_id: cfg.streamId || payload.streamId || "extension-default",
        features: payload.features,
        timestamp_s: Date.now() / 1000,
        source: "extension",
        privacy_mode: cfg.privacyMode,
      }),
    });
    return res.ok;
  } catch {
    return false;
  }
}

function colorFromState(state) {
  switch (state) {
    case "ON_DUTY":
      return "#10B981";
    case "BRIEF_AWAY":
      return "#F59E0B";
    case "LONG_AWAY":
      return "#F97316";
    case "CHEAT_FLAGGED":
      return "#E4000F";
    default:
      return "#64748B";
  }
}

async function updateBadge(state) {
  await chrome.action.setBadgeBackgroundColor({ color: colorFromState(state) });
  await chrome.action.setBadgeText({ text: state ? state.slice(0, 2) : "" });
}

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  (async () => {
    if (msg?.type === "LG_SIGNAL") {
      const ok = await postSignal(msg.data);
      sendResponse({ ok });
    } else if (msg?.type === "LG_STATE") {
      await updateBadge(msg.state);
      sendResponse({ ok: true });
    } else if (msg?.type === "LG_ALERT") {
      await chrome.notifications.create(`lg-${Date.now()}`, {
        type: "basic",
        iconUrl: "../icons/icon-128.png",
        title: `${msg.severity} · ${msg.title}`,
        message: msg.summary || "",
        priority: msg.severity === "P0" ? 2 : 1,
      });
      sendResponse({ ok: true });
    } else {
      sendResponse({ ok: false, error: "unknown_type" });
    }
  })();
  return true; // 异步响应
});

chrome.alarms.create("lg-heartbeat", { periodInMinutes: 1 });
chrome.alarms.onAlarm.addListener(async (a) => {
  if (a.name !== "lg-heartbeat") return;
  const cfg = await getConfig();
  if (!cfg.backendUrl) return;
  try {
    await fetch(`${cfg.backendUrl}/healthz`);
  } catch {
    /* offline */
  }
});

chrome.runtime.onInstalled.addListener(() => {
  console.log("[LiveGuard] extension installed · v1.0.0");
});
