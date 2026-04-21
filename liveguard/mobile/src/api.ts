import Constants from "expo-constants";

const extra = (Constants.expoConfig?.extra ?? {}) as Record<string, string | undefined>;
const BACKEND = extra.LVG_BACKEND_URL || "http://localhost:8080";
const TOKEN = extra.LVG_MOBILE_TOKEN || "";

export interface AlertItem {
  id: string;
  tenant_id: string;
  stream_id: string;
  severity: "INFO" | "P2" | "P1" | "P0";
  state: string;
  title: string;
  summary: string;
  first_seen_at: string;
}

export async function fetchAlerts(): Promise<AlertItem[]> {
  try {
    const res = await fetch(`${BACKEND}/v1/alerts`, {
      headers: TOKEN ? { Authorization: `Bearer ${TOKEN}` } : {},
    });
    if (!res.ok) throw new Error(`status ${res.status}`);
    return await res.json();
  } catch {
    return MOCK;
  }
}

const MOCK: AlertItem[] = [
  {
    id: "alt_mock_p0",
    tenant_id: "t_demo",
    stream_id: "str_demo_custom",
    severity: "P0",
    state: "open",
    title: "反作弊告警 · DEEPFAKE_AVATAR",
    summary: "检测到 Deepfake 替换（置信度 0.87），请立即人工介入",
    first_seen_at: new Date(Date.now() - 5 * 60_000).toISOString(),
  },
  {
    id: "alt_mock_p1",
    tenant_id: "t_demo",
    stream_id: "str_demo_ks",
    severity: "P1",
    state: "open",
    title: "主播离岗 ≥ 60s",
    summary: "融合得分 0.21，累计离开 65s",
    first_seen_at: new Date(Date.now() - 30 * 60_000).toISOString(),
  },
];
