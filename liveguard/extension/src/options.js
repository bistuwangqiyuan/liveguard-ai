const FIELDS = ["backendUrl", "tenantId", "streamId", "token"];

async function load() {
  const cfg = await chrome.storage.sync.get({
    backendUrl: "http://localhost:8080",
    tenantId: "t_demo",
    streamId: "",
    token: "",
    privacyMode: true,
  });
  for (const k of FIELDS) document.getElementById(k).value = cfg[k] ?? "";
  document.getElementById("privacyMode").checked = !!cfg.privacyMode;
}

async function save() {
  const payload = {};
  for (const k of FIELDS) payload[k] = document.getElementById(k).value.trim();
  payload.privacyMode = document.getElementById("privacyMode").checked;
  await chrome.storage.sync.set(payload);
  const s = document.getElementById("saved");
  s.hidden = false;
  setTimeout(() => (s.hidden = true), 1500);
}

document.getElementById("save").addEventListener("click", save);
load();
