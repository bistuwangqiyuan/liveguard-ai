import { cn } from "@/lib/cn";

export interface KpiCardProps {
  label: string;
  value: string | number;
  delta?: string;
  hint?: string;
  tone?: "neutral" | "positive" | "warn" | "danger";
}

const TONE: Record<NonNullable<KpiCardProps["tone"]>, string> = {
  neutral: "text-slate-300",
  positive: "text-emerald-300",
  warn: "text-amber-300",
  danger: "text-rose-300",
};

export function KpiCard({ label, value, delta, hint, tone = "neutral" }: KpiCardProps) {
  return (
    <div className="card">
      <div className="flex items-center justify-between">
        <span className="text-xs uppercase tracking-widest text-slate-400">{label}</span>
        {delta && <span className={cn("text-xs", TONE[tone])}>{delta}</span>}
      </div>
      <div className="mt-3 flex items-baseline gap-2">
        <span className="text-3xl font-semibold tracking-tight">{value}</span>
      </div>
      {hint && <p className="mt-2 text-xs text-slate-400">{hint}</p>}
    </div>
  );
}
