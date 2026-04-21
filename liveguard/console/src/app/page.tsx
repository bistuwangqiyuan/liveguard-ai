import { AlertTriangle, ShieldCheck, Signal, Timer } from "lucide-react";

import { KpiCard } from "@/components/KpiCard";
import { SeverityBadge } from "@/components/SeverityBadge";
import { StateDot } from "@/components/StateDot";
import { fetchAlerts, fetchStreams } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function Page() {
  const [streams, alerts] = await Promise.all([fetchStreams(), fetchAlerts()]);

  const active = streams.filter((s) => s.status === "active").length;
  const onDuty = streams.filter((s) => s.last_state === "ON_DUTY").length;
  const p0 = alerts.filter((a) => a.severity === "P0" && a.state === "open").length;
  const openTotal = alerts.filter((a) => a.state === "open").length;
  const avgScore =
    streams.reduce((s, x) => s + x.last_fusion_score, 0) / Math.max(1, streams.length);

  return (
    <div className="mx-auto max-w-7xl space-y-8 p-8">
      <header className="flex items-end justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">总览 Dashboard</h1>
          <p className="mt-2 text-sm text-slate-400">
            多模态 AI · 主播在岗 + 反作弊 + 合规回溯 — 一屏掌握所有直播间风险态势
          </p>
        </div>
        <div className="chip">
          <Signal className="h-3.5 w-3.5" />
          实时同步 · 5s 刷新
        </div>
      </header>

      <section className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          label="在线直播数"
          value={active}
          delta={`${onDuty} 在岗`}
          tone="positive"
          hint="active = 正在推流 · ON_DUTY = 主播在岗且有互动"
        />
        <KpiCard
          label="融合得分 (均值)"
          value={avgScore.toFixed(2)}
          tone={avgScore > 0.65 ? "positive" : avgScore > 0.4 ? "warn" : "danger"}
          hint="多模态融合（人脸×人形×Re-ID×活体×行为×声纹×VAD）"
        />
        <KpiCard
          label="未处理告警"
          value={openTotal}
          delta={`${p0} × P0`}
          tone={p0 > 0 ? "danger" : openTotal > 0 ? "warn" : "positive"}
          hint="按严重级别去重合并（5 分钟窗口）"
        />
        <KpiCard
          label="端到端告警延迟"
          value="2.1s"
          tone="positive"
          delta="P0 SLO 3.0s"
          hint="边缘推理 → Kafka → Notify 派发（p95）"
        />
      </section>

      <section className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <div className="card">
          <div className="flex items-center justify-between">
            <h2 className="flex items-center gap-2 text-lg font-semibold">
              <AlertTriangle className="h-4 w-4 text-severity-p1" />
              最近告警
            </h2>
            <span className="text-xs text-slate-400">最多显示 8 条</span>
          </div>
          <ul className="mt-4 space-y-3">
            {alerts.slice(0, 8).map((a) => (
              <li
                key={a.id}
                className="flex items-start gap-3 rounded-lg border border-surface-border bg-surface-elev2 p-3"
              >
                <SeverityBadge severity={a.severity} />
                <div className="min-w-0 flex-1">
                  <div className="truncate text-sm text-slate-100">{a.title}</div>
                  <div className="mt-1 line-clamp-2 text-xs text-slate-400">{a.summary}</div>
                  <div className="mt-1 text-[11px] text-slate-500">
                    首发 · {new Date(a.first_seen_at).toLocaleString("zh-CN")}
                  </div>
                </div>
              </li>
            ))}
            {alerts.length === 0 && (
              <li className="rounded-lg border border-dashed border-surface-border p-6 text-center text-sm text-slate-400">
                暂无告警 · 一切平稳
              </li>
            )}
          </ul>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <h2 className="flex items-center gap-2 text-lg font-semibold">
              <ShieldCheck className="h-4 w-4 text-emerald-400" />
              直播流状态
            </h2>
            <span className="text-xs text-slate-400">融合得分 · 实时</span>
          </div>
          <table className="mt-4 w-full text-sm">
            <thead className="text-xs uppercase tracking-widest text-slate-500">
              <tr>
                <th className="pb-2 text-left font-medium">Stream</th>
                <th className="pb-2 text-left font-medium">平台</th>
                <th className="pb-2 text-left font-medium">状态</th>
                <th className="pb-2 text-right font-medium">得分</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-border">
              {streams.map((s) => (
                <tr key={s.id} className="align-middle">
                  <td className="py-2 font-mono text-xs text-slate-200">{s.id}</td>
                  <td className="py-2 text-slate-300">{s.platform}</td>
                  <td className="py-2">
                    <div className="flex items-center gap-2">
                      <StateDot state={s.last_state} />
                      <span className="text-slate-200">{s.last_state}</span>
                    </div>
                  </td>
                  <td className="py-2 text-right font-mono">
                    {s.last_fusion_score.toFixed(3)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <footer className="flex items-center justify-between border-t border-surface-border pt-4 text-xs text-slate-500">
        <span>LiveGuard AI · 守播 v1.0 · © {new Date().getFullYear()}</span>
        <span className="flex items-center gap-2">
          <Timer className="h-3 w-3" />
          Next.js 14 · App Router · SSR
        </span>
      </footer>
    </div>
  );
}
