import { z } from "zod";

const BACKEND = process.env.LVG_BACKEND_URL || "http://localhost:8080";
const TOKEN = process.env.LVG_CONSOLE_TOKEN || "";

export const StreamSchema = z.object({
  id: z.string(),
  tenant_id: z.string(),
  host_id: z.string().nullable(),
  platform: z.string(),
  rtmp_url: z.string().nullable().optional(),
  status: z.string(),
  last_state: z.string(),
  last_fusion_score: z.number(),
  last_heartbeat_at: z.string().nullable().optional(),
});
export type Stream = z.infer<typeof StreamSchema>;

export const AlertSchema = z.object({
  id: z.string(),
  tenant_id: z.string(),
  stream_id: z.string(),
  host_id: z.string().nullable(),
  severity: z.enum(["INFO", "P2", "P1", "P0"]),
  state: z.string(),
  title: z.string(),
  summary: z.string(),
  first_seen_at: z.string(),
  ack_at: z.string().nullable(),
});
export type AlertItem = z.infer<typeof AlertSchema>;

async function get<T>(path: string, schema: z.ZodType<T>, tag: string): Promise<T> {
  const res = await fetch(`${BACKEND}${path}`, {
    headers: TOKEN ? { Authorization: `Bearer ${TOKEN}` } : {},
    next: { revalidate: 5, tags: [tag] },
  });
  if (!res.ok) throw new Error(`[api] ${path} → ${res.status}`);
  const data = await res.json();
  return schema.parse(data);
}

export async function fetchStreams(): Promise<Stream[]> {
  return get("/v1/streams", z.array(StreamSchema), "streams").catch(() => MOCK_STREAMS);
}

export async function fetchAlerts(): Promise<AlertItem[]> {
  return get("/v1/alerts", z.array(AlertSchema), "alerts").catch(() => MOCK_ALERTS);
}

// ---------------------------------------------------------------------------
// 开发/离线模拟数据
// ---------------------------------------------------------------------------

const MOCK_STREAMS: Stream[] = [
  {
    id: "str_demo_douyin",
    tenant_id: "t_demo",
    host_id: "h_alice",
    platform: "douyin",
    rtmp_url: "rtmp://push.douyin.com/live/demoAlice",
    status: "active",
    last_state: "ON_DUTY",
    last_fusion_score: 0.84,
    last_heartbeat_at: new Date().toISOString(),
  },
  {
    id: "str_demo_ks",
    tenant_id: "t_demo",
    host_id: "h_bob",
    platform: "kuaishou",
    status: "active",
    last_state: "LONG_AWAY",
    last_fusion_score: 0.21,
    last_heartbeat_at: new Date().toISOString(),
  },
  {
    id: "str_demo_custom",
    tenant_id: "t_demo",
    host_id: "h_cathy",
    platform: "custom",
    status: "active",
    last_state: "CHEAT_FLAGGED",
    last_fusion_score: 0.61,
    last_heartbeat_at: new Date().toISOString(),
  },
];

const MOCK_ALERTS: AlertItem[] = [
  {
    id: "alt_mock_p1",
    tenant_id: "t_demo",
    stream_id: "str_demo_ks",
    host_id: "h_bob",
    severity: "P1",
    state: "open",
    title: "主播离岗 ≥ 60s · str_demo_ks",
    summary: "状态: BRIEF_AWAY → LONG_AWAY ｜ 融合得分: 0.210 ｜ 累计离开: 65.0s",
    first_seen_at: new Date(Date.now() - 45 * 60_000).toISOString(),
    ack_at: null,
  },
  {
    id: "alt_mock_p0",
    tenant_id: "t_demo",
    stream_id: "str_demo_custom",
    host_id: "h_cathy",
    severity: "P0",
    state: "open",
    title: "反作弊告警 · DEEPFAKE_AVATAR",
    summary: "检测到 Deepfake 替换迹象（置信度 0.87），立即人工介入。",
    first_seen_at: new Date(Date.now() - 10 * 60_000).toISOString(),
    ack_at: null,
  },
];
