export default function SettingsPage() {
  return (
    <div className="mx-auto max-w-4xl space-y-6 p-8">
      <div>
        <h1 className="text-2xl font-semibold">设置</h1>
        <p className="mt-1 text-sm text-slate-400">
          租户策略 · 算法阈值 · 通知通道 · 隐私模式 · 合规审计
        </p>
      </div>

      <section className="card space-y-4">
        <h2 className="text-lg font-semibold">算法阈值</h2>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <Field label="ON_DUTY 阈值" value="0.65" hint="融合得分 ≥ 此值进入 ON_DUTY" />
          <Field label="BRIEF_AWAY 阈值" value="0.40" hint="低于此值进入短暂离岗" />
          <Field label="LONG_AWAY 时长" value="60s" hint="累计离岗超过此阈值触发 P1 告警" />
        </div>
      </section>

      <section className="card space-y-4">
        <h2 className="text-lg font-semibold">通知通道</h2>
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          {["SMS", "Voice", "DingTalk", "WeWork", "Feishu", "Webhook", "App Push"].map((c) => (
            <label
              key={c}
              className="flex cursor-pointer items-center justify-between rounded-lg border border-surface-border bg-surface-elev2 px-3 py-2 text-sm"
            >
              <span>{c}</span>
              <input type="checkbox" defaultChecked className="accent-brand-500" />
            </label>
          ))}
        </div>
      </section>

      <section className="card space-y-4">
        <h2 className="text-lg font-semibold">隐私 & 合规</h2>
        <div className="space-y-3 text-sm text-slate-300">
          <Toggle label="隐私模式（边缘端不上传原始视频）" defaultChecked />
          <Toggle label="主播人脸向量加密存储（AES-256）" defaultChecked />
          <Toggle label="审计日志 180 天保留 · 符合《网络安全法》要求" defaultChecked />
          <Toggle label="欧盟 GDPR 兼容（DPA 已签署）" />
        </div>
      </section>
    </div>
  );
}

function Field({ label, value, hint }: { label: string; value: string; hint: string }) {
  return (
    <div>
      <div className="text-xs uppercase tracking-widest text-slate-400">{label}</div>
      <div className="mt-2 rounded-lg border border-surface-border bg-surface-elev2 px-3 py-2 font-mono text-lg">
        {value}
      </div>
      <p className="mt-1 text-xs text-slate-500">{hint}</p>
    </div>
  );
}

function Toggle({ label, defaultChecked }: { label: string; defaultChecked?: boolean }) {
  return (
    <label className="flex cursor-pointer items-center justify-between rounded-lg border border-surface-border bg-surface-elev2 px-3 py-2">
      <span>{label}</span>
      <input type="checkbox" defaultChecked={defaultChecked} className="accent-brand-500" />
    </label>
  );
}
