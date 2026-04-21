import "./globals.css";

import type { Metadata } from "next";
import Link from "next/link";

import {
  Activity,
  AlertTriangle,
  LayoutDashboard,
  Settings,
  Users2,
  Video,
} from "lucide-react";

import { cn } from "@/lib/cn";

export const metadata: Metadata = {
  title: "LiveGuard AI · 守播直播监控",
  description:
    "多模态 AI 直播监控平台 — 主播离岗、反作弊、合规回溯 · 一站式管理",
  icons: { icon: "/favicon.svg" },
};

const NAV = [
  { href: "/", label: "总览", Icon: LayoutDashboard },
  { href: "/streams", label: "直播流", Icon: Video },
  { href: "/alerts", label: "告警中心", Icon: AlertTriangle },
  { href: "/hosts", label: "主播", Icon: Users2 },
  { href: "/realtime", label: "实时大屏", Icon: Activity },
  { href: "/settings", label: "设置", Icon: Settings },
];

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN" className="dark">
      <body className="min-h-screen bg-surface-base text-slate-100 antialiased">
        <div className="flex min-h-screen">
          <aside className="w-60 border-r border-surface-border bg-surface-elev1 px-4 py-6">
            <div className="mb-10 flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-500/20 shadow-glow">
                <span className="text-xl font-bold text-brand-300">守</span>
              </div>
              <div>
                <div className="text-sm font-semibold tracking-wide">LiveGuard AI</div>
                <div className="text-[11px] text-slate-400">守播 · v1.0</div>
              </div>
            </div>
            <nav className="space-y-1">
              {NAV.map(({ href, label, Icon }) => (
                <Link
                  key={href}
                  href={href}
                  className={cn(
                    "flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-slate-300 transition",
                    "hover:bg-surface-elev2 hover:text-white"
                  )}
                >
                  <Icon className="h-4 w-4" />
                  {label}
                </Link>
              ))}
            </nav>
            <div className="mt-10 rounded-xl border border-surface-border bg-surface-elev2 p-3 text-xs text-slate-400">
              <div className="text-slate-200">Demo · 不含生产数据</div>
              <div className="mt-1">租户: t_demo · 环境: sandbox</div>
            </div>
          </aside>
          <main className="flex-1 min-w-0">{children}</main>
        </div>
      </body>
    </html>
  );
}
