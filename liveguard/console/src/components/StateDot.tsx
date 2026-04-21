import { cn } from "@/lib/cn";

const STATE_COLOR: Record<string, string> = {
  IDLE: "bg-slate-400",
  ON_DUTY: "bg-emerald-400 shadow-[0_0_12px_-1px_rgba(16,185,129,0.7)]",
  BRIEF_AWAY: "bg-amber-400",
  LONG_AWAY: "bg-orange-500",
  ALERT_ESCALATED: "bg-rose-500 animate-pulse",
  CHEAT_FLAGGED: "bg-red-500 animate-pulse",
  COOLDOWN: "bg-sky-400",
};

export function StateDot({ state }: { state: string }) {
  return (
    <span
      className={cn("inline-block h-2.5 w-2.5 rounded-full", STATE_COLOR[state] || "bg-slate-400")}
      aria-label={`流状态 ${state}`}
    />
  );
}
