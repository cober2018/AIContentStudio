import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api, currentUser } from "../api";
import { Button, ErrorBanner, Spinner } from "../components/ui";
import ChannelIcon from "./ChannelIcon";

type Counts = { topics: number; topics_adopted: number; topics_pending: number; topics_dropped: number; in_progress: number; finalized: number; published: number; posts: number; posts_studio: number; posts_with_metrics: number; views: number; engagements: number; followers_gained: number };
type PersonaRow = Counts & { persona_id: number | null; persona_name: string };
type ChannelRow = { channel: string; channel_label: string; posts: number; views: number; engagements: number; followers_gained: number };
type Work = { id: number; title: string; channel: string; channel_label: string; persona_name: string | null; origin: string; published_at: string | null; views: number | null; engagements: number | null; followers_gained: number | null; has_metrics: boolean };
type Funnel = { days: number; totals: Counts; domains: Record<"persona" | "product", Counts>; personas: PersonaRow[]; channels: ChannelRow[]; top_works: Work[]; posts_without_metrics: number; last_observed_at: string | null };

const ranges = [[7, "近 7 天"], [30, "近 30 天"], [90, "近 90 天"], [0, "全部"]] as const;
const textLink = "text-sm font-medium text-accent-600 hover:underline";
const num = (value: number | null | undefined) => value == null ? "—" : value >= 10000 ? `${(value / 10000).toFixed(1)} 万` : Math.round(value).toLocaleString("zh-CN");
const parse = (value: string) => Date.parse(/(?:Z|[+-]\d{2}:\d{2})$/i.test(value) ? value : `${value}Z`);
const day = (value: string | null) => value ? new Date(parse(value)).toLocaleDateString("zh-CN", { timeZone: "Asia/Shanghai", month: "numeric", day: "numeric" }) : "日期未知";

function Step({ label, value, hint, to }: { label: string; value: number; hint: string; to?: string }) {
  const body = <><p className="eyebrow">{label}</p><p className="mt-2 font-serif text-[28px] font-semibold leading-none tabular-nums text-ink-900">{num(value)}</p><p className="mt-2 text-[12.5px] text-ink-500">{hint}</p></>;
  return to ? <Link to={to} className="block min-w-0 rounded-[14px] border border-ink-200/90 p-4 hover:border-accent-300">{body}</Link> : <div className="min-w-0 rounded-[14px] border border-ink-200/90 p-4">{body}</div>;
}

export default function HomeFunnel() {
  const [days, setDays] = useState(30);
  const query = useQuery({ queryKey: ["home-funnel", currentUser(), days], queryFn: () => api.get<Funnel>(`/home/funnel?days=${days}`), placeholderData: previous => previous });
  const data = query.data;
  const staleDays = data?.last_observed_at ? Math.floor((Date.now() - parse(data.last_observed_at)) / 86400000) : null;
  const maxViews = Math.max(1, ...(data?.channels ?? []).map(c => c.views));
  return <section className="card p-6 sm:p-7" aria-label="内容漏斗">
    <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
      <h2 className="font-serif text-[22px] font-semibold text-ink-900">内容漏斗与效果</h2>
      <div className="flex flex-wrap items-center gap-2" role="group" aria-label="时间范围">{ranges.map(([value, label]) => <Button key={value} size="sm" variant={days === value ? undefined : "secondary"} aria-pressed={days === value} onClick={() => setDays(value)}>{label}</Button>)}</div>
    </div>
    {query.isPending && <Spinner label="读取选题、作品和复盘数据…" />}
    {query.isError && <div className="space-y-2"><ErrorBanner message={`漏斗数据读取失败，不能当作没有数据。${query.error instanceof Error ? query.error.message : ""}`} /><Button size="sm" variant="secondary" onClick={() => void query.refetch()}>重试</Button></div>}
    {data && <div className={`space-y-7 ${query.isFetching ? "opacity-60" : ""}`}>
      <p className="text-[12.5px] text-ink-500">选题和作品按创建时间、发布按发布时间统计；效果取效果复盘里每条作品最新一次录入的数值，没录过的不算 0。{data.last_observed_at ? ` 效果数据最近录入：${day(data.last_observed_at)}。` : " 还没有录入过效果数据。"}{staleDays != null && staleDays >= 3 && <span className="text-amber-800"> 已 {staleDays} 天没更新，可让第三方模型按 craft-review 重新读取各平台后台。</span>} <Link className={textLink} to="/learning?tab=history">效果复盘 →</Link></p>
      <ol className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        <li><Step label="① 选题" value={data.totals.topics} hint={`待判断 ${data.totals.topics_pending} · 采纳 ${data.totals.topics_adopted} · 放弃 ${data.totals.topics_dropped}`} to="/opportunities" /></li>
        <li><Step label="② 制作中" value={data.totals.in_progress} hint={`角色 ${data.domains.persona.in_progress} · 商品 ${data.domains.product.in_progress}`} to="/production?workspace=persona" /></li>
        <li><Step label="③ 已成稿待发布" value={data.totals.finalized} hint={`角色 ${data.domains.persona.finalized} · 商品 ${data.domains.product.finalized}`} to="/review" /></li>
        <li><Step label="④ 平台作品" value={data.totals.posts} hint={`本平台做的 ${data.totals.posts_studio} · 平台导入 ${data.totals.posts - data.totals.posts_studio}`} to="/learning?tab=history" /></li>
        <li><Step label="⑤ 播放 / 阅读" value={data.totals.views} hint={`互动 ${num(data.totals.engagements)} · 涨粉 ${num(data.totals.followers_gained)}`} to="/learning?tab=analysis" /></li>
      </ol>
      {data.posts_without_metrics > 0 && <p className="text-sm text-amber-800">{data.posts_without_metrics} 条平台作品还没有效果数据。</p>}
      <div className="grid gap-7 lg:grid-cols-2">
        <div><h3 className="mb-3 font-medium text-ink-900">各平台播放 / 阅读</h3>{data.channels.length === 0 ? <p className="text-sm text-ink-500">这段时间没有发布记录。</p> : <ul className="space-y-2.5">{data.channels.map(c => <li key={c.channel} className="grid grid-cols-[6.5rem_1fr_4.5rem] items-center gap-3 text-sm" title={`${c.channel_label}：${c.posts} 条作品 · 播放/阅读 ${num(c.views)} · 互动 ${num(c.engagements)} · 涨粉 ${num(c.followers_gained)}`}><span className="truncate text-ink-700"><ChannelIcon channel={c.channel} className="mr-1" />{c.channel_label}</span><span className="h-3 rounded-r bg-ink-100"><span className="block h-3 rounded-r bg-accent-500" style={{ width: `${Math.max(c.views ? 1 : 0, c.views / maxViews * 100)}%` }} /></span><span className="text-right tabular-nums text-ink-700">{num(c.views)}</span></li>)}</ul>}<p className="mt-2 text-xs text-ink-500">各平台口径不同：抖音、视频号、B站是播放，公众号是阅读，小红书是观看。悬停看条数、互动和涨粉。</p></div>
        <div><h3 className="mb-3 font-medium text-ink-900">表现最好的作品</h3>{data.top_works.length === 0 ? <p className="text-sm text-ink-500">这段时间没有发布记录。</p> : <ol className="space-y-2">{data.top_works.map((w, i) => <li key={w.id}><Link to={`/learning?tab=history&published=${w.id}`} className="flex items-center gap-3 rounded-lg px-2 py-1.5 text-sm hover:bg-ink-50"><span className="w-4 shrink-0 text-xs tabular-nums text-ink-500">{i + 1}</span><span className="min-w-0 flex-1"><span className="block truncate text-ink-900">{w.title}</span><span className="text-xs text-ink-500"><ChannelIcon channel={w.channel} className="mr-1" />{w.channel_label} · {w.persona_name || "未关联角色"} · {day(w.published_at)}{w.origin === "external_import" ? " · 平台导入" : ""}</span></span><span className="shrink-0 text-right tabular-nums"><span className="block text-ink-900">{num(w.views)}</span><span className="text-xs text-ink-500">互动 {num(w.engagements)}</span></span></Link></li>)}</ol>}</div>
      </div>
      <div><h3 className="mb-3 font-medium text-ink-900">按角色</h3><div className="overflow-x-auto"><table className="w-full min-w-[720px] text-sm"><thead><tr className="border-b border-ink-200 text-left text-xs text-ink-500">{["角色", "选题", "待判断", "制作中", "待发布", "已发布", "平台作品", "播放/阅读", "互动", "涨粉"].map(h => <th key={h} className={`py-2 font-normal ${h === "角色" ? "" : "text-right"}`}>{h}</th>)}</tr></thead><tbody>{data.personas.map(p => <tr key={p.persona_id ?? "none"} className="border-b border-ink-100 last:border-0"><td className="py-2 text-ink-900">{p.persona_id ? <Link className="hover:text-accent-600" to={`/production?workspace=persona&persona=${p.persona_id}`}>{p.persona_name}</Link> : p.persona_name}</td>{[p.topics, p.topics_pending, p.in_progress, p.finalized, p.published, p.posts, p.views, p.engagements, p.followers_gained].map((v, i) => <td key={i} className="py-2 text-right tabular-nums text-ink-700">{num(v)}</td>)}</tr>)}</tbody></table></div><p className="mt-2 text-xs text-ink-500">「已发布」是本平台做完并发布的作品；「平台作品」还包括从平台后台导入的历史作品。商品视频没选角色时记在「未关联角色」。</p></div>
    </div>}
  </section>;
}
