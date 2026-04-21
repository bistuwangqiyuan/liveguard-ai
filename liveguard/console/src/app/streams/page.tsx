import Link from "next/link";

import { StateDot } from "@/components/StateDot";
import { fetchStreams } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function StreamsPage() {
  const streams = await fetchStreams();
  return (
    <div className="mx-auto max-w-7xl space-y-6 p-8">
      <div>
        <h1 className="text-2xl font-semibold">直播流</h1>
        <p className="mt-1 text-sm text-slate-400">所有已接入的直播间 · 实时融合得分与状态</p>
      </div>
      <div className="card overflow-hidden p-0">
        <table className="w-full text-sm">
          <thead className="bg-surface-elev2 text-xs uppercase tracking-widest text-slate-400">
            <tr>
              <th className="px-4 py-3 text-left">Stream ID</th>
              <th className="px-4 py-3 text-left">平台</th>
              <th className="px-4 py-3 text-left">主播</th>
              <th className="px-4 py-3 text-left">状态</th>
              <th className="px-4 py-3 text-right">融合得分</th>
              <th className="px-4 py-3 text-right">操作</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-surface-border">
            {streams.map((s) => (
              <tr key={s.id} className="hover:bg-surface-elev2/60">
                <td className="px-4 py-3 font-mono text-xs text-slate-200">{s.id}</td>
                <td className="px-4 py-3">{s.platform}</td>
                <td className="px-4 py-3 text-slate-300">{s.host_id ?? "—"}</td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <StateDot state={s.last_state} />
                    <span>{s.last_state}</span>
                  </div>
                </td>
                <td className="px-4 py-3 text-right font-mono">
                  {s.last_fusion_score.toFixed(3)}
                </td>
                <td className="px-4 py-3 text-right">
                  <Link
                    className="text-brand-300 hover:text-brand-200"
                    href={`/streams/${s.id}`}
                  >
                    详情 →
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
