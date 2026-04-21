import { cn } from "@/lib/cn";

const LABEL: Record<string, string> = {
  P0: "P0 · 紧急",
  P1: "P1 · 高",
  P2: "P2 · 中",
  INFO: "INFO",
};

export function SeverityBadge({ severity }: { severity: string }) {
  const key = `severity-${severity.toLowerCase()}`;
  return (
    <span className={cn("chip", key)} aria-label={`严重级别 ${severity}`}>
      {LABEL[severity] ?? severity}
    </span>
  );
}
