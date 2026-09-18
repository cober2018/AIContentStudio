import { ReactNode } from "react";

// 小型 UI 组件集：按钮/徽标/弹层/抽屉/空态，风格统一为内容工作台

export function Button({
  children,
  onClick,
  variant = "primary",
  size = "md",
  disabled,
  type = "button",
  className = "",
}: {
  children: ReactNode;
  onClick?: () => void;
  variant?: "primary" | "secondary" | "danger" | "ghost";
  size?: "sm" | "md";
  disabled?: boolean;
  type?: "button" | "submit";
  className?: string;
}) {
  const variants = {
    primary: "bg-gray-900 text-white hover:bg-black disabled:bg-gray-300",
    secondary: "bg-white text-slate-700 border border-slate-300 hover:bg-slate-50 disabled:text-slate-400",
    danger: "bg-rose-600 text-white hover:bg-rose-700",
    ghost: "text-slate-600 hover:bg-slate-100",
  };
  const sizes = { sm: "px-2.5 py-1 text-xs", md: "px-3.5 py-1.5 text-sm" };
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`rounded-md font-medium transition-colors disabled:cursor-not-allowed ${variants[variant]} ${sizes[size]} ${className}`}
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
  archived: "bg-slate-100 text-slate-400",
  exported: "bg-teal-100 text-teal-700",
  active: "bg-emerald-100 text-emerald-700",
};

export function StatusBadge({ status }: { status: string }) {
  const style = STATUS_STYLES[status] || "bg-slate-100 text-slate-600";
  return <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${style}`}>{status}</span>;
}

export function ChannelBadge({ channel }: { channel: string }) {
  const names: Record<string, string> = { douyin: "抖音", xiaohongshu: "小红书", wechat: "公众号" };
  return (
    <span className="inline-flex rounded border border-slate-200 bg-white px-1.5 py-0.5 text-xs text-slate-600">
      {names[channel] || channel}
    </span>
  );
}

export function Modal({
  title,
  children,
  onClose,
  wide,
}: {
  title: string;
  children: ReactNode;
  onClose: () => void;
  wide?: boolean;
}) {
  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-slate-900/40" onClick={onClose}>
      <div
        className={`max-h-[85vh] w-full ${wide ? "max-w-3xl" : "max-w-lg"} overflow-y-auto rounded-lg bg-white p-6 shadow-xl`}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold">{title}</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            ✕
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}

export function Drawer({ title, children, onClose }: { title: string; children: ReactNode; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-slate-900/30" onClick={onClose}>
      <div
        className="h-full w-full max-w-2xl overflow-y-auto bg-white shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sticky top-0 flex items-center justify-between border-b border-slate-200 bg-white px-6 py-4">
          <h2 className="text-lg font-semibold">{title}</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            ✕
          </button>
        </div>
        <div className="p-6">{children}</div>
      </div>
    </div>
  );
}

export function EmptyState({ title, hint, action }: { title: string; hint?: string; action?: ReactNode }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-slate-300 bg-white py-16">
      <p className="text-sm font-medium text-slate-500">{title}</p>
      {hint && <p className="mt-1 text-xs text-slate-400">{hint}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

export function ErrorBanner({ message }: { message: string }) {
  return <div className="rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{message}</div>;
}

export function Field({ label, hint, children }: { label: string; hint?: string; children: ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-medium text-slate-500">{label}</span>
      {children}
      {hint && <span className="mt-1 block text-[11px] text-slate-400">{hint}</span>}
    </label>
  );
}

export const inputClass =
  "w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-gray-900 focus:outline-none";

export function Spinner({ label = "加载中…" }: { label?: string }) {
  return (
    <div className="flex items-center justify-center py-16 text-sm text-slate-400">
      <span className="mr-2 inline-block h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-gray-900" />
      {label}
    </div>
  );
}
