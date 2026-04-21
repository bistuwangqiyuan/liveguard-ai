export const dynamic = "force-dynamic";

const DEMO_HOSTS = [
  { id: "h_alice", name: "Alice", on_duty_h: 152.4, violations: 0, score: 4.9 },
  { id: "h_bob", name: "Bob", on_duty_h: 98.1, violations: 3, score: 4.1 },
  { id: "h_cathy", name: "Cathy", on_duty_h: 201.9, violations: 1, score: 4.7 },
];

export default function HostsPage() {
  return (
    <div className="mx-auto max-w-7xl space-y-6 p-8">
      <div>
        <h1 className="text-2xl font-semibold">主播管理</h1>
        <p className="mt-1 text-sm text-slate-400">
          主播画像 · 在岗时长 / 违规记录 / 综合评分 · RBAC: ADMIN / OPS
        </p>
      </div>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {DEMO_HOSTS.map((h) => (
          <div key={h.id} className="card">
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-brand-500/20 text-lg font-semibold text-brand-200">
                {h.name[0]}
              </div>
              <div>
                <div className="font-semibold">{h.name}</div>
                <div className="font-mono text-xs text-slate-500">{h.id}</div>
              </div>
            </div>
            <dl className="mt-4 grid grid-cols-3 gap-3 text-sm">
              <div>
                <dt className="text-xs text-slate-500">在岗</dt>
                <dd className="mt-1 font-semibold">{h.on_duty_h}h</dd>
              </div>
              <div>
                <dt className="text-xs text-slate-500">违规</dt>
                <dd className="mt-1 font-semibold text-rose-300">{h.violations}</dd>
              </div>
              <div>
                <dt className="text-xs text-slate-500">评分</dt>
                <dd className="mt-1 font-semibold text-emerald-300">{h.score}</dd>
              </div>
            </dl>
          </div>
        ))}
      </div>
    </div>
  );
}
