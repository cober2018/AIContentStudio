import { ReactNode, useEffect } from "react";

// 工作室共享组件：所有页面经由这里取得同一套版式、节奏与状态语言。

export function Button({
  children,
  onClick,
  variant = "primary",
  size = "md",
  disabled,
  type = "button",
  className = "",
  ariaPressed,
}: {
  children: ReactNode;
  onClick?: () => void;
  variant?: "primary" | "secondary" | "danger" | "ghost";
  size?: "sm" | "md";
  disabled?: boolean;
  type?: "button" | "submit";
  className?: string;
  ariaPressed?: boolean;
}) {
  const variants = {
    primary: "bg-ink-900 text-paper shadow-[inset_0_-1px_0_rgb(0_0_0/0.25)] hover:bg-ink-800 disabled:bg-ink-300 disabled:text-ink-100 disabled:shadow-none",
    secondary: "bg-surface text-ink-800 border border-ink-300/90 hover:border-ink-500 hover:text-ink-900 disabled:border-ink-200 disabled:text-ink-400",
    danger: "bg-surface text-rose-600 border border-rose-200 hover:border-rose-400 hover:bg-rose-50 disabled:text-rose-300",
    ghost: "text-ink-600 hover:bg-ink-100 hover:text-ink-900 disabled:text-ink-300",
  };
  const sizes = { sm: "h-7 px-3 text-xs", md: "h-9 px-4 text-[13.5px]" };
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      aria-pressed={ariaPressed}
      className={`inline-flex items-center justify-center gap-1.5 whitespace-nowrap rounded-pill font-medium transition-[background-color,border-color,color,transform] duration-200 ease-studio active:translate-y-px disabled:cursor-not-allowed disabled:active:translate-y-0 ${variants[variant]} ${sizes[size]} ${className}`}
    >
      {children}
    </button>
  );
}

const STATUS_STYLES: Record<string, string> = {
  // 通用状态
  draft: "bg-slate-100 text-slate-600",
  pending: "bg-slate-100 text-slate-600",
  queued: "bg-slate-100 text-slate-600",
  parsing: "bg-amber-100 text-amber-700",
  running: "bg-amber-100 text-amber-700",
  candidate: "bg-amber-100 text-amber-700",
  done: "bg-emerald-100 text-emerald-700",
  succeeded: "bg-emerald-100 text-emerald-700",
  confirmed: "bg-emerald-100 text-emerald-700",
  pass: "bg-emerald-100 text-emerald-700",
  approved: "bg-emerald-100 text-emerald-700",
  frozen: "bg-sky-100 text-sky-700",
  published: "bg-sky-100 text-sky-700",
  ready_for_review: "bg-violet-100 text-violet-700",
  changes_requested: "bg-amber-100 text-amber-700",
  fact_check_failed: "bg-rose-100 text-rose-700",
  failed: "bg-rose-100 text-rose-700",
  conflict: "bg-rose-100 text-rose-700",
  blocker: "bg-rose-100 text-rose-700",
  warning: "bg-amber-100 text-amber-700",
  rejected: "bg-rose-100 text-rose-600",
  stale: "bg-amber-100 text-amber-700",
  blocked: "bg-rose-100 text-rose-800 ring-1 ring-rose-200",
  unknown: "bg-violet-100 text-violet-800 ring-1 ring-violet-200",
  ready: "bg-emerald-100 text-emerald-800 ring-1 ring-emerald-200",
  waiting_review: "bg-violet-100 text-violet-800",
  delivery_ready: "bg-sky-100 text-sky-800",
  delivered: "bg-emerald-100 text-emerald-800",
  waiting_human: "bg-sky-100 text-sky-800 ring-1 ring-sky-200",
  archived: "bg-slate-100 text-slate-400",
  exported: "bg-teal-100 text-teal-700",
  incomplete: "bg-amber-100 text-amber-700",
  target_authorized: "bg-sky-100 text-sky-700",
  awaiting_manual_receipt: "bg-violet-100 text-violet-700",
  human_confirmed: "bg-emerald-100 text-emerald-700",
  reconciliation_needed: "bg-amber-100 text-amber-700",
  active: "bg-emerald-100 text-emerald-700",
};

export function StatusBadge({ status }: { status: string }) {
  const style = STATUS_STYLES[status] || "bg-slate-100 text-slate-600";
  const labels: Record<string, string> = {
    blocked: "受阻", stale: "已过期", unknown: "待核对", ready: "就绪", waiting_review: "待审核", delivery_ready: "待交付", delivered: "已回填", waiting_human: "等待人工", running: "进行中", draft: "草稿", approved: "已批准",
    active: "使用中", frozen: "已冻结", candidate: "候选", usable: "可用", revoked: "已撤销", archived: "已归档", pending: "等待中", queued: "排队中", parsing: "解析中",
    done: "完成", succeeded: "成功", failed: "失败", confirmed: "已确认", pass: "通过", published: "已发布", ready_for_review: "待审阅", changes_requested: "需修改",
    rejected: "已退回", exported: "已导出", incomplete: "不完整", conflict: "冲突", warning: "注意", blocker: "阻断", fact_check_failed: "事实核查未过",
    target_authorized: "已授权", awaiting_manual_receipt: "待人工回执", human_confirmed: "人工已确认", reconciliation_needed: "需核对", saved: "已保存", pinned: "已固定",
    accepted: "已采纳", result_ready: "结果待审", in_progress: "进行中", prepared: "已准备", cancelled: "已取消", superseded: "已替代", completed: "已完成", waiting_input: "等待输入",
  };
  return <span className={`inline-flex items-center gap-1.5 rounded-pill px-2.5 py-0.5 text-[11.5px] font-medium ${style}`} title={status}><span aria-hidden className="h-1.5 w-1.5 rounded-full bg-current opacity-70" />{labels[status] || status}</span>;
}

export function ChannelBadge({ channel }: { channel: string }) {
  const names: Record<string, string> = { douyin: "抖音", xiaohongshu: "小红书", wechat: "公众号", x: "X", x_thread: "X Thread（已下线）" };
  return (
    <span className="inline-flex rounded-pill border border-ink-200 bg-surface px-2 py-0.5 text-[11.5px] text-ink-600">
      {names[channel] || channel}
    </span>
  );
}

export function Modal({
  title,
  children,
  onClose,
  wide,
  closeOnBackdrop = true,
}: {
  title: string;
  children: ReactNode;
  onClose: () => void;
  wide?: boolean;
  // Upload windows stay open on outside clicks: dragging a file in often ends with a click beside the dialog.
  closeOnBackdrop?: boolean;
}) {
  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-ink-950/35 p-4 backdrop-blur-[2px]" onClick={closeOnBackdrop ? onClose : undefined}>
      <EscapeToClose onClose={onClose} />
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className={`max-h-[86vh] w-full animate-rise ${wide ? "max-w-3xl" : "max-w-lg"} overflow-y-auto rounded-card border border-ink-200 bg-surface p-7 shadow-lift`}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-5 flex items-start justify-between gap-4">
          <h2 className="text-[22px] leading-tight text-ink-900">{title}</h2>
          <CloseButton onClose={onClose} />
        </div>
        {children}
      </div>
    </div>
  );
}

export function Drawer({ title, children, onClose }: { title: string; children: ReactNode; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-ink-950/30 backdrop-blur-[2px]" onClick={onClose}>
      <EscapeToClose onClose={onClose} />
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className="h-full w-full max-w-2xl overflow-y-auto border-l border-ink-200 bg-surface shadow-lift"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sticky top-0 z-10 flex items-center justify-between border-b border-ink-200/80 bg-surface/95 px-7 py-5 backdrop-blur">
          <h2 className="text-[22px] leading-tight text-ink-900">{title}</h2>
          <CloseButton onClose={onClose} />
        </div>
        <div className="p-7">{children}</div>
      </div>
    </div>
  );
}

export function EmptyState({ title, hint, action }: { title: string; hint?: string; action?: ReactNode }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-card border border-dashed border-ink-300 bg-surface/60 px-6 py-16 text-center">
      <span aria-hidden className="mb-4 font-display text-3xl leading-none text-ink-300">○</span>
      <p className="font-serif text-[17px] text-ink-800">{title}</p>
      {hint && <p className="mt-1.5 max-w-sm text-[13px] leading-relaxed text-ink-500">{hint}</p>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

export function ErrorBanner({ message }: { message: string }) {
  return <div role="alert" className="flex items-start gap-2.5 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-[13.5px] leading-relaxed text-rose-700"><span aria-hidden className="mt-[7px] h-1.5 w-1.5 shrink-0 rounded-full bg-rose-500" />{message}</div>;
}

// Alerts float at the side instead of pushing the page down; success notes fade out on their own, warnings stay until closed.
export function FloatingAlert({ message, tone = "error", onClose }: { message: string; tone?: "error" | "info"; onClose: () => void }) {
  useEffect(() => {
    if (tone !== "info") return;
    const timer = window.setTimeout(onClose, 5000);
    return () => window.clearTimeout(timer);
  }, [message, tone, onClose]);
  const colors = tone === "error" ? "border-rose-200 bg-rose-50 text-rose-700" : "border-emerald-200 bg-emerald-50 text-emerald-800";
  return <div role={tone === "error" ? "alert" : "status"} className={`fixed bottom-6 right-6 z-50 flex max-w-sm items-start gap-3 rounded-xl border px-4 py-3 text-[13.5px] leading-relaxed shadow-lg ${colors}`}>
    <span className="min-w-0 flex-1">{message}</span>
    <button type="button" aria-label="关闭" className="shrink-0 text-[16px] leading-none opacity-60 hover:opacity-100" onClick={onClose}>×</button>
  </div>;
}

export function Field({ label, hint, children }: { label: string; hint?: string; children: ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-[12.5px] font-medium text-ink-700">{label}</span>
      {children}
      {hint && <span className="mt-1.5 block text-[12px] leading-relaxed text-ink-500">{hint}</span>}
    </label>
  );
}

export const inputClass =
  "w-full rounded-[10px] border border-ink-300/90 bg-surface px-3.5 py-2 text-[14px] text-ink-900 placeholder:text-ink-400 transition-colors hover:border-ink-400 focus:border-ink-800 focus:outline-none focus:ring-4 focus:ring-ink-200/60 disabled:bg-ink-50 disabled:text-ink-500";

export function Spinner({ label = "加载中…" }: { label?: string }) {
  return (
    <div role="status" className="flex items-center justify-center gap-3 py-16 text-[13px] text-ink-500">
      <span className="inline-block h-4 w-4 animate-spin rounded-full border-[1.5px] border-ink-200 border-t-accent-500" />
      {label}
    </div>
  );
}

function EscapeToClose({ onClose }: { onClose: () => void }) {
  useEffect(() => {
    const key = (event: KeyboardEvent) => { if (event.key === "Escape") onClose(); };
    window.addEventListener("keydown", key);
    return () => window.removeEventListener("keydown", key);
  }, [onClose]);
  return null;
}

function CloseButton({ onClose }: { onClose: () => void }) {
  return <button onClick={onClose} aria-label="关闭" className="grid h-8 w-8 shrink-0 place-items-center rounded-full text-ink-500 transition-colors hover:bg-ink-100 hover:text-ink-900">
    <svg aria-hidden width="14" height="14" viewBox="0 0 14 14"><path d="M2 2l10 10M12 2L2 12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" /></svg>
  </button>;
}

export function PageHeader({ eyebrow, title, lead, actions, children }: { eyebrow?: ReactNode; title: ReactNode; lead?: ReactNode; actions?: ReactNode; children?: ReactNode }) {
  return <header className={`animate-rise ${children ? "" : "border-b border-ink-200/80 pb-7"}`}>
    <div className="flex flex-wrap items-end justify-between gap-x-8 gap-y-4">
      <div className="min-w-0 max-w-3xl">
        {eyebrow && <p className="eyebrow mb-3">{eyebrow}</p>}
        <h1 className="break-words text-[34px] leading-[1.1] text-ink-900 sm:text-[42px]">{title}</h1>
        {lead && <p className="mt-3 max-w-2xl text-[15px] leading-relaxed text-ink-600">{lead}</p>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </div>
    {children && <div className="mt-7">{children}</div>}
  </header>;
}

export function Page({ children, width = "wide" }: { children: ReactNode; width?: "wide" | "narrow" }) {
  return <div className={`mx-auto w-full ${width === "wide" ? "max-w-[1240px]" : "max-w-[920px]"} space-y-8 px-5 pb-20 pt-8 sm:px-8 md:pt-12 lg:px-12`}>{children}</div>;
}

export function Section({ title, eyebrow, aside, children, className = "" }: { title?: ReactNode; eyebrow?: ReactNode; aside?: ReactNode; children: ReactNode; className?: string }) {
  return <section className={`card p-6 sm:p-7 ${className}`}>
    {(title || eyebrow || aside) && <div className="mb-5 flex flex-wrap items-start justify-between gap-3">
      <div className="min-w-0">
        {eyebrow && <p className="eyebrow mb-1.5">{eyebrow}</p>}
        {title && <h2 className="font-serif text-[20px] font-semibold leading-snug text-ink-900">{title}</h2>}
      </div>
      {aside && <div className="flex flex-wrap items-center gap-2 text-[13px] text-ink-500">{aside}</div>}
    </div>}
    {children}
  </section>;
}

export function Tabs<T extends string>({ items, value, onChange, label, disabled }: { items: readonly (readonly [T, string])[]; value: string; onChange: (value: T) => void; label: string; disabled?: boolean }) {
  return <nav aria-label={label} className="-mx-1 flex gap-1 overflow-x-auto overflow-y-hidden border-b border-ink-200/80 px-1 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
    {items.map(([key, text]) => {
      const active = key === value;
      return <button key={key} type="button" disabled={disabled} aria-current={active ? "page" : undefined} onClick={() => onChange(key)}
        className={`relative shrink-0 whitespace-nowrap px-3 pb-3 pt-1 text-[14px] transition-colors disabled:cursor-not-allowed disabled:opacity-60 ${active ? "font-medium text-ink-900" : "text-ink-500 hover:text-ink-900"}`}>
        {text}
        <span aria-hidden className={`absolute inset-x-3 -bottom-px h-[2px] rounded-full transition-colors ${active ? "bg-accent-500" : "bg-transparent"}`} />
      </button>;
    })}
  </nav>;
}

export function Segmented<T extends string>({ items, value, onChange, label }: { items: readonly (readonly [T, string])[]; value: string; onChange: (value: T) => void; label: string }) {
  return <div role="group" aria-label={label} className="inline-flex flex-wrap gap-1 rounded-pill border border-ink-200 bg-ink-100/60 p-1">
    {items.map(([key, text]) => <button key={key} type="button" aria-pressed={key === value} onClick={() => onChange(key)}
      className={`rounded-pill px-3.5 py-1.5 text-[13px] transition-colors ${key === value ? "bg-surface font-medium text-ink-900 shadow-card" : "text-ink-600 hover:text-ink-900"}`}>{text}</button>)}
  </div>;
}

export function Chip({ children, tone = "neutral" }: { children: ReactNode; tone?: "neutral" | "accent" | "good" | "warn" | "bad" | "info" }) {
  const tones = {
    neutral: "border-ink-200 bg-ink-50 text-ink-700",
    accent: "border-accent-200 bg-accent-50 text-accent-700",
    good: "border-emerald-200 bg-emerald-50 text-emerald-700",
    warn: "border-amber-200 bg-amber-50 text-amber-800",
    bad: "border-rose-200 bg-rose-50 text-rose-700",
    info: "border-sky-200 bg-sky-50 text-sky-700",
  };
  return <span className={`inline-flex max-w-full items-center rounded-pill border px-2.5 py-0.5 text-[12.5px] leading-5 ${tones[tone]}`}><span className="truncate">{children}</span></span>;
}

export function Notice({ children, tone = "info" }: { children: ReactNode; tone?: "info" | "warn" | "good" }) {
  const tones = { info: "border-ink-200 bg-surface text-ink-700", warn: "border-amber-200 bg-amber-50 text-amber-800", good: "border-emerald-200 bg-emerald-50 text-emerald-800" };
  const dot = { info: "bg-accent-500", warn: "bg-amber-500", good: "bg-emerald-500" };
  return <div role="status" className={`flex items-start gap-2.5 rounded-xl border px-4 py-3 text-[13.5px] leading-relaxed ${tones[tone]}`}><span aria-hidden className={`mt-[7px] h-1.5 w-1.5 shrink-0 rounded-full ${dot[tone]}`} /><div className="min-w-0">{children}</div></div>;
}

export function Stat({ label, value, hint }: { label: ReactNode; value: ReactNode; hint?: ReactNode }) {
  return <div className="min-w-0">
    <p className="eyebrow">{label}</p>
    <p className="mt-2 font-serif text-[30px] font-semibold leading-none tabular-nums text-ink-900">{value}</p>
    {hint && <p className="mt-2 text-[12.5px] text-ink-500">{hint}</p>}
  </div>;
}
