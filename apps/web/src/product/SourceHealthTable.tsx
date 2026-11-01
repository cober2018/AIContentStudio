import { useQuery } from "@tanstack/react-query";
import { api, currentUser } from "../api";
import { ErrorBanner, Spinner } from "../components/ui";
import { discoveryLabel } from "./DiscoveryPanel";

type SourceHealth = { id: number; name: string; aggregate: boolean; radar: boolean; state: "ok" | "error" | "paused"; reason: string | null; last_success_at: string | null; next_due_at: string | null; unscheduled_reason: string | null; daily_new: number[]; latest_item_at: string | null };

// Backend times are naive UTC; without the suffix the browser would read them as local time.
const time = (value: string | null) => !value ? "尚无" : new Date(/Z$|[+-]\d{2}:\d{2}$/.test(value) ? value : `${value}Z`).toLocaleString([], { month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit" });
// A source that polls fine but brings nothing new for days is how a stalled upstream shows up.
const stale = (s: SourceHealth) => s.daily_new.slice(-3).every(n => n === 0);
const problem = (s: SourceHealth) => s.state !== "ok" || !!s.unscheduled_reason || stale(s);

export function SourceHealthTable() {
  const user = currentUser();
  const health = useQuery({ queryKey: ["discovery-source-health", user], queryFn: () => api.get<{ days: string[]; sources: SourceHealth[] }>("/content-opportunities/discovery/source-health"), refetchInterval: 60000 });
  const rows = [...(health.data?.sources || [])].sort((a, b) => Number(problem(b)) - Number(problem(a)));
  const count = (test: (s: SourceHealth) => boolean) => rows.filter(test).length;
  return <details open className="rounded-xl border border-slate-200 bg-white p-4 text-sm">
    <summary className="cursor-pointer font-medium text-ink-900">数据源运行情况{health.data && <span className="ml-2 font-normal text-slate-600">共 {rows.length} 个 · 正常 {count(s => s.state === "ok")} · 报错 {count(s => s.state === "error")} · 已暂停 {count(s => s.state === "paused")} · 未被安排 {count(s => !!s.unscheduled_reason)} · 近 3 天无新内容 {count(stale)}</span>}</summary>
    {health.isPending ? <Spinner /> : health.isError ? <ErrorBanner message="数据源运行情况读取失败，请刷新重试。" /> : <div className="mt-3 max-h-96 overflow-auto"><table className="w-full text-left text-xs">
      <thead className="sticky top-0 bg-white"><tr className="border-b text-slate-500"><th className="p-2">名称</th><th className="p-2">状态</th><th className="p-2">最近成功抓取</th><th className="p-2">下次抓取</th><th className="p-2" title={health.data.days.join(" ~ ")}>近 7 天新内容（{health.data.days[0].slice(5)} ~ 今天）</th><th className="p-2">最近一条新内容</th></tr></thead>
      <tbody>{rows.map(s => <tr key={s.id} className={`border-b ${problem(s) ? "bg-amber-50/60" : ""}`}>
        <td className="p-2">{s.name}{s.aggregate && <span className="ml-1 text-slate-500">（聚合站）</span>}{s.radar && <span className="ml-1 text-slate-500">（新词雷达）</span>}</td>
        <td className={`p-2 ${s.state === "error" ? "text-red-700" : s.state === "paused" ? "text-slate-500" : "text-teal-800"}`}>{s.state === "ok" ? "正常" : s.state === "paused" ? "已暂停" : `报错：${discoveryLabel(s.reason)}`}</td>
        <td className="whitespace-nowrap p-2">{time(s.last_success_at)}</td>
        <td className="p-2">{s.unscheduled_reason ? <span className="text-amber-800">未被安排：{discoveryLabel(s.unscheduled_reason)}</span> : <span className="whitespace-nowrap">{time(s.next_due_at)}</span>}</td>
        <td className="whitespace-nowrap p-2 font-mono">{s.daily_new.map((n, i) => <span key={health.data.days[i]} title={health.data.days[i]} className={`mr-1 inline-block w-6 text-right ${n === 0 ? "text-slate-400" : "text-ink-900"}`}>{n}</span>)}</td>
        <td className={`whitespace-nowrap p-2 ${stale(s) ? "text-amber-800" : ""}`}>{time(s.latest_item_at)}</td>
      </tr>)}</tbody>
    </table></div>}
  </details>;
}
