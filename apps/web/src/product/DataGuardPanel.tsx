import { useQuery } from "@tanstack/react-query";
import { api, currentUser } from "../api";

type GuardItem = { state: "ok" | "remedying" | "attention" | "waiting" | "skipped"; detail?: string; status?: string };
type GuardPersona = GuardItem & { persona_id: number; name: string; setup?: GuardItem & { kind: string } };
type GuardSource = GuardItem & { source_id: number; name: string; last_success_at: string | null };
type Guard = { checked_at?: string; personas?: GuardPersona[]; sources?: GuardSource[]; remedies_today?: number; attention: number };

const STATE: Record<GuardItem["state"], [string, string]> = {
  ok: ["达标", "text-emerald-700"], remedying: ["补救中", "text-amber-700"], attention: ["需要你处理", "text-rose-700"],
  waiting: ["未到时间", "text-slate-500"], skipped: ["未运行", "text-slate-500"],
};

function time(value?: string | null) {
  return value ? new Date(/(?:Z|[+-]\d{2}:\d{2})$/i.test(value) ? value : `${value}Z`).toLocaleString("zh-CN", { hour12: false }) : "从未";
}

function Badge({ item }: { item: GuardItem }) {
  const [label, color] = STATE[item.state];
  return <span className={`shrink-0 font-medium ${color}`}>{label}</span>;
}

// The guard only checks outcomes: each source collected in time, each persona's daily topics done in time.
export function DataGuardPanel() {
  const guard = useQuery({ queryKey: ["discovery-guard", currentUser()], refetchInterval: 60_000,
    queryFn: () => api.get<Guard>("/content-opportunities/discovery/guard") });
  const data = guard.data;
  if (!data?.checked_at) return null;
  const problems = [
    ...(data.personas || []).flatMap(p => [p.state === "attention" ? `${p.name}：${p.detail}` : null, p.setup?.state === "attention" ? `${p.name}（找信息源）：${p.setup.detail}` : null]),
    ...(data.sources || []).map(s => s.state === "attention" ? `信息源 ${s.name}：${s.detail}` : null),
  ].filter((text): text is string => !!text);
  const sources = data.sources || [];
  const late = sources.filter(s => s.state !== "ok");
  return <section aria-label="数据保障" className="space-y-3">
    {problems.length > 0 && <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-900"><p className="font-semibold">数据保障：有 {problems.length} 项需要你处理</p><ul className="mt-2 list-disc space-y-1 pl-5">{problems.map(text => <li key={text} className="break-words">{text}</li>)}</ul></div>}
    <details className="rounded-xl border border-slate-200 bg-white p-4 text-sm">
      <summary className="cursor-pointer font-semibold">数据保障 · {problems.length ? `${problems.length} 项需要处理` : "全部正常"} · 今天自动补救 {data.remedies_today || 0} 次 · 上次巡检 {time(data.checked_at)}</summary>
      <h4 className="mt-3 font-medium">角色今天的选题</h4>
      <ul className="mt-1 divide-y divide-slate-100">{(data.personas || []).map(p => <li key={p.persona_id} className="flex flex-wrap items-start justify-between gap-2 py-2"><span className="min-w-0 break-words">{p.name}{p.detail ? <span className="text-slate-500"> · {p.detail}</span> : null}{p.setup && p.setup.state !== "ok" ? <span className="block text-xs text-slate-500">找信息源：{STATE[p.setup.state][0]} · {p.setup.detail}</span> : null}</span><Badge item={p} /></li>)}</ul>
      <h4 className="mt-3 font-medium">信息源（{sources.length - late.length}/{sources.length} 按时抓到）</h4>
      {late.length === 0 ? <p className="mt-1 text-slate-500">所有启用的信息源都在时限内抓到了。</p> :
        <ul className="mt-1 divide-y divide-slate-100">{late.map(s => <li key={s.source_id} className="flex flex-wrap items-start justify-between gap-2 py-2"><span className="min-w-0 break-words">{s.name}<span className="text-slate-500"> · {s.detail} · 最近成功 {time(s.last_success_at)}</span></span><Badge item={s} /></li>)}</ul>}
    </details>
  </section>;
}
