import { notFound } from "next/navigation";

import { StateDot } from "@/components/StateDot";
import { fetchStreams } from "@/lib/api";

export const dynamic = "force-dynamic";

interface Props {
  params: { id: string };
}

export default async function StreamDetailPage({ params }: Props) {
  const streams = await fetchStreams();
  const s = streams.find((x) => x.id === params.id);
  if (!s) return notFound();

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-8">
      <header>
        <div className="text-xs uppercase tracking-widest text-slate-400">Stream</div>
        <h1 className="font-mono text-2xl font-semibold">{s.id}</h1>
        <div className="mt-2 flex flex-wrap items-center gap-3 text-sm text-slate-300">
          <span className="chip">{s.platform}</span>
          <span className="chip">
            <StateDot state={s.last_state} />
            <span className="ml-1">{s.last_state}</span>
          </span>
          <span className="chip">host: {s.host_id ?? "—"}</span>
          <span className="chip">租户: {s.tenant_id}</span>
        </div>
      </header>

      <section className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <div className="card">
          <div className="text-xs uppercase tracking-widest text-slate-400">融合得分</div>
          <div className="mt-2 text-3xl font-semibold">{s.last_fusion_score.toFixed(3)}</div>
          <div className="mt-2 text-xs text-slate-500">阈值: ≥0.65 触发 ON_DUTY</div>
        </div>
        <div className="card">
          <div className="text-xs uppercase tracking-widest text-slate-400">最近心跳</div>
          <div className="mt-2 text-lg">
            {s.last_heartbeat_at
              ? new Date(s.last_heartbeat_at).toLocaleString("zh-CN")
              : "—"}
          </div>
        </div>
        <div className="card">
          <div className="text-xs uppercase tracking-widest text-slate-400">RTMP</div>
          <div className="mt-2 break-all font-mono text-xs text-slate-300">
            {s.rtmp_url ?? "未配置"}
          </div>
        </div>
      </section>

      <section className="card">
        <h2 className="text-lg font-semibold">实时视频预览（Mock）</h2>
        <p className="mt-1 text-xs text-slate-400">
          上线后接入 WHEP (low-latency WebRTC) / HLS 预览流 · 仅 Role ≥ OPS 可见
        </p>
        <div className="mt-4 flex aspect-video items-center justify-center rounded-xl border border-dashed border-surface-border bg-surface-elev2 text-sm text-slate-500">
          实时预览占位 · 待接入 WebRTC
        </div>
      </section>

      <section className="card">
        <h2 className="text-lg font-semibold">最近状态迁移</h2>
        <p className="mt-1 text-xs text-slate-400">StreamFSM 审计轨迹（示意 · 待接入 WS）</p>
        <ol className="mt-4 space-y-2 text-sm">
          {["IDLE → ON_DUTY", "ON_DUTY → BRIEF_AWAY", "BRIEF_AWAY → ON_DUTY"].map((t, i) => (
            <li
              key={i}
              className="flex items-center justify-between rounded-lg border border-surface-border bg-surface-elev2 px-3 py-2 font-mono text-xs"
            >
              <span>{t}</span>
              <span className="text-slate-500">{i * 47 + 12}s 前</span>
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}
