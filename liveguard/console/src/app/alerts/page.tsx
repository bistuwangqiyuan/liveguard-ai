import { SeverityBadge } from "@/components/SeverityBadge";
import { fetchAlerts } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function AlertsPage() {
  const alerts = await fetchAlerts();
  return (
    <div className="mx-auto max-w-7xl space-y-6 p-8">
      <div>
        <h1 className="text-2xl font-semibold">告警中心</h1>
        <p className="mt-1 text-sm text-slate-400">
          按 5 分钟窗口去重合并 · 支持 ACK / RESOLVE · 审计日志完整留存
        </p>
      </div>
      <div className="grid grid-cols-1 gap-4">
        {alerts.map((a) => (
          <article
            key={a.id}
            className="card flex flex-col gap-3 md:flex-row md:items-center md:justify-between"
          >
            <div className="flex items-start gap-4">
              <SeverityBadge severity={a.severity} />
              <div>
                <h3 className="text-base font-semibold">{a.title}</h3>
                <p className="mt-1 max-w-2xl text-sm text-slate-400">{a.summary}</p>
                <p className="mt-2 text-xs text-slate-500">
                  {a.stream_id} · 首发 {new Date(a.first_seen_at).toLocaleString("zh-CN")}
                </p>
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <span className="chip">{a.state.toUpperCase()}</span>
              <button className="rounded-lg border border-brand-500/50 bg-brand-500/10 px-3 py-1.5 text-xs font-medium text-brand-200 transition hover:bg-brand-500/20">
                确认 ACK
              </button>
              <button className="rounded-lg border border-emerald-500/40 bg-emerald-500/10 px-3 py-1.5 text-xs font-medium text-emerald-200 transition hover:bg-emerald-500/20">
                处理 RESOLVE
              </button>
            </div>
          </article>
        ))}
        {alerts.length === 0 && (
          <div className="card text-center text-sm text-slate-400">
            当前无未处理告警 · 系统平稳运行
          </div>
        )}
      </div>
    </div>
  );
}
