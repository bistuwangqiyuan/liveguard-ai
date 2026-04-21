"use client";

import { useEffect, useState } from "react";

import { StateDot } from "@/components/StateDot";

interface TickSample {
  t: number;
  score: number;
  state: string;
}

const STATES = ["IDLE", "ON_DUTY", "BRIEF_AWAY", "LONG_AWAY", "ON_DUTY", "COOLDOWN"];

export default function RealtimePage() {
  const [samples, setSamples] = useState<TickSample[]>([]);
  const [state, setState] = useState("ON_DUTY");

  useEffect(() => {
    const id = setInterval(() => {
      setSamples((prev) => {
        const t = Date.now();
        const score =
          0.6 + 0.35 * Math.sin(t / 2500) + (Math.random() - 0.5) * 0.12;
        const next = [...prev, { t, score: Math.max(0, Math.min(1, score)), state }];
        return next.slice(-80);
      });
      if (Math.random() > 0.93) setState(STATES[Math.floor(Math.random() * STATES.length)]);
    }, 300);
    return () => clearInterval(id);
  }, [state]);

  const last = samples[samples.length - 1]?.score ?? 0;

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-8">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-semibold">实时大屏</h1>
          <p className="mt-1 text-sm text-slate-400">
            WebSocket + Canvas · 演示：融合得分时序 · 当前 FSM 状态
          </p>
        </div>
        <div className="chip">
          <StateDot state={state} />
          <span className="ml-1">{state}</span>
        </div>
      </div>

      <div className="card">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">融合得分</h2>
          <span className="font-mono text-2xl text-brand-300">{last.toFixed(3)}</span>
        </div>
        <svg viewBox="0 0 800 240" className="mt-4 h-64 w-full">
          <defs>
            <linearGradient id="g" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stopColor="#4d95ff" stopOpacity="0.5" />
              <stop offset="100%" stopColor="#4d95ff" stopOpacity="0" />
            </linearGradient>
          </defs>
          <g stroke="#1F2B4C" strokeWidth="1">
            {[0.25, 0.5, 0.65, 0.85].map((y, i) => (
              <line key={i} x1="0" x2="800" y1={240 - y * 240} y2={240 - y * 240} />
            ))}
          </g>
          <line
            x1="0"
            x2="800"
            y1={240 - 0.65 * 240}
            y2={240 - 0.65 * 240}
            stroke="#10B981"
            strokeDasharray="4 4"
            strokeWidth="1"
          />
          <polyline
            fill="none"
            stroke="#4d95ff"
            strokeWidth="2"
            points={samples
              .map(
                (s, i) =>
                  `${(i / Math.max(1, samples.length - 1)) * 800},${240 - s.score * 240}`
              )
              .join(" ")}
          />
          <polygon
            fill="url(#g)"
            points={[
              "0,240",
              ...samples.map(
                (s, i) =>
                  `${(i / Math.max(1, samples.length - 1)) * 800},${240 - s.score * 240}`
              ),
              "800,240",
            ].join(" ")}
          />
        </svg>
        <div className="mt-2 text-xs text-slate-500">
          虚线 = ON_DUTY 阈值 0.65 · 曲线 = 每 300ms 抽样 · 演示环境仅模拟数据
        </div>
      </div>
    </div>
  );
}
