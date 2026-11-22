import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { api, currentUser } from "../api";
import { Button, ErrorBanner, Spinner } from "../components/ui";
import ChannelIcon from "./ChannelIcon";

type Event = { type: string; label: string; tone: "good" | "bad" | "info"; detail: string; at: string | null };
type Work = { id: number; title: string; channel: string; channel_label: string; account_name: string; origin: string; published_at: string | null; views: number | null; likes: number | null; comments: number | null; shares: number | null; favorites: number | null; followers_gained: number | null; engagements: number | null; engagement_rate: number | null; observations: number; events: Event[] };
type FeedEvent = Event & { work_id: number; title: string; channel: string; channel_label: string };
type Channel = { channel: string; channel_label: string; posts: number; with_data: number; views: number; engagements: number; followers_gained: number; median_views: number | null };
type FollowerAccount = { account_id: number; account_name: string; channel: string; channel_label: string; followers: number | null; observed_on: string | null; change: number | null; since: string | null; history: { observed_on: string; followers: number }[] };
type Followers = { total: number | null; accounts: FollowerAccount[]; recorded: number; missing: number; last_observed_on: string | null; trend: { observed_on: string; followers: number }[] };
type Timeline = { followers: Followers; persona_id: number; persona_name: string | null; works: Work[]; events: FeedEvent[]; event_types: { type: string; label: string; description: string; tone: Event["tone"] }[]; channels: Channel[]; totals: { posts: number; with_data: number; views: number; engagements: number; followers_gained: number }; last_observed_at: string | null };

// 颜色跟着平台走，不跟排名走；顺序固定（已过色盲校验）。
const CHANNEL_COLORS: Record<string, string> = { douyin: "#2a78d6", xiaohongshu: "#eb6834", wechat: "#1baf7a", wechat_channels: "#eda100", bilibili: "#e87ba4", toutiao: "#008300", baijia: "#6250d6" };
const colorOf = (channel: string) => CHANNEL_COLORS[channel] ?? "#e34948";
const TONE = { good: { glyph: "▲", cls: "text-emerald-700" }, bad: { glyph: "▼", cls: "text-amber-700" }, info: { glyph: "◆", cls: "text-ink-500" } } as const;
const ranges = [[30, "近 30 天"], [90, "近 90 天"], [180, "近半年"], [0, "全部"]] as const;
const metrics = {
  relative: { label: "相对平常", hint: "播放/阅读 ÷ 该平台这个角色的中位数；1× 就是平常水平，各平台可以放在一起比" },
  views: { label: "播放/阅读", hint: "各平台口径不同，建议按平台筛选后看" },
  engagements: { label: "互动", hint: "点赞 + 评论 + 分享 + 收藏" },
  comments: { label: "评论", hint: "" },
  followers_gained: { label: "涨粉", hint: "" },
  engagement_rate: { label: "互动率", hint: "互动 ÷ 播放/阅读" },
} as const;
type Metric = keyof typeof metrics;
const num = (v: number | null | undefined) => v == null ? "—" : v >= 10000 ? `${(v / 10000).toFixed(1)} 万` : Math.round(v).toLocaleString("zh-CN");
const fmt = (metric: Metric, v: number) => metric === "relative" ? `${v.toFixed(1)}×` : metric === "engagement_rate" ? `${(v * 100).toFixed(1)}%` : num(v);
const parse = (v: string) => Date.parse(/(?:Z|[+-]\d{2}:\d{2})$/i.test(v) ? v : `${v}Z`);
const day = (v: string | null) => v ? new Date(parse(v)).toLocaleDateString("zh-CN", { timeZone: "Asia/Shanghai", month: "numeric", day: "numeric" }) : "日期未知";
const detailHref = (id: number) => `/learning?tab=history&published=${id}`;

function Chart({ works, metric, medians, highlight }: { works: Work[]; metric: Metric; medians: Record<string, number | null>; highlight: string }) {
  const navigate = useNavigate();
  const [hover, setHover] = useState<number | null>(null);
  const value = (w: Work) => metric === "relative" ? (w.views != null && medians[w.channel] ? w.views / medians[w.channel]! : null) : w[metric];
  const points = works.map((w, i) => ({ w, i, v: value(w) }));
  const plotted = points.filter(p => p.v != null) as { w: Work; i: number; v: number }[];
  const W = 1000, H = 320, L = 52, R = 16, T = 26, B = 34;
  // 个别爆款会把其他点压成一条线：超过 90 分位 1.5 倍的点钉在顶部，标出真实数值。
  const sorted = plotted.map(p => p.v).sort((a, b) => a - b);
  const top = sorted[sorted.length - 1], p90 = sorted[Math.floor((sorted.length - 1) * 0.9)];
  const max = Math.max(metric === "relative" ? 2 : 0, top > p90 * 3 && p90 > 0 ? p90 * 1.5 : top) || 1;
  const x = (i: number) => L + (works.length <= 1 ? (W - L - R) / 2 : i * (W - L - R) / (works.length - 1));
  const y = (v: number) => T + (H - T - B) * (1 - Math.min(v, max) / max);
  const ticks = [0, max / 2, max];
  const series = [...new Set(plotted.map(p => p.w.channel))];
  const labelEvery = Math.max(1, Math.ceil(works.length / 8));
  const hovered = hover != null ? points[hover] : null;
  // 相邻两个超出图顶的点挨得太近时只标前一个，免得数字叠在一起（悬停仍能看到实际值）。
  const labelled = new Set<number>();
  let lastLabel = -Infinity;
  for (const p of plotted) if (p.v > max && x(p.i) - lastLabel > 60) { labelled.add(p.i); lastLabel = x(p.i); }
  if (!plotted.length) return <p className="rounded-xl border border-dashed p-8 text-center text-sm text-ink-500">这段时间、这个筛选下没有可画的数值。{metric === "relative" ? "相对平常需要同平台至少 5 条有数据的作品。" : ""}</p>;
  return <div className="relative">
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label={`按发布顺序的${metrics[metric].label}`} onMouseLeave={() => setHover(null)}>
      {ticks.map(t => <g key={t}><line x1={L} x2={W - R} y1={y(t)} y2={y(t)} stroke="currentColor" className="text-ink-200" strokeWidth={1} /><text x={L - 8} y={y(t) + 4} textAnchor="end" className="fill-ink-500 text-[11px]">{fmt(metric, t)}</text></g>)}
      {metric === "relative" && <g><line x1={L} x2={W - R} y1={y(1)} y2={y(1)} stroke="currentColor" className="text-ink-500" strokeDasharray="4 4" strokeWidth={1} /><text x={W - R} y={y(1) - 5} textAnchor="end" className="fill-ink-500 text-[11px]">平常 1×</text></g>}
      {series.map(c => { const pts = plotted.filter(p => p.w.channel === c); return pts.length > 1 ? <polyline key={c} points={pts.map(p => `${x(p.i)},${y(p.v)}`).join(" ")} fill="none" stroke={colorOf(c)} strokeWidth={2} strokeOpacity={highlight ? 0.25 : 0.55} strokeLinejoin="round" /> : null; })}
      {points.map(({ w, i }) => i % labelEvery === 0 && <text key={`d${w.id}`} x={x(i)} y={H - 10} textAnchor="middle" className="fill-ink-500 text-[11px]">{day(w.published_at)}</text>)}
      {plotted.map(({ w, i, v }) => { const marked = !highlight || w.events.some(e => e.type === highlight); const tone = w.events.find(e => !highlight || e.type === highlight)?.tone; return <g key={w.id} opacity={marked ? 1 : 0.2} className="cursor-pointer" onMouseEnter={() => setHover(i)} onClick={() => navigate(detailHref(w.id))}>
        <rect x={x(i) - 8} y={T - 20} width={16} height={H - T - B + 20} fill="transparent" />
        <circle cx={x(i)} cy={y(v)} r={hover === i ? 6 : 4.5} fill={colorOf(w.channel)} stroke="rgb(var(--surface))" strokeWidth={2} />
        {labelled.has(i) && <text x={x(i) + 8} y={y(v) + 4} className="fill-ink-700 text-[11px]">↑{fmt(metric, v)}</text>}
        {tone && <text x={x(i)} y={y(v) - 10} textAnchor="middle" className={`text-[10px] ${TONE[tone].cls}`} fill="currentColor">{TONE[tone].glyph}</text>}
      </g>; })}
    </svg>
    {hovered && <div className="pointer-events-none absolute z-10 w-72 rounded-xl border border-ink-200 bg-surface p-3 text-xs shadow-lg" style={{ left: `${Math.min(70, Math.max(0, x(hovered.i) / W * 100 - 12))}%`, top: 0 }}>
      <p className="font-medium text-ink-900">{hovered.w.title}</p>
      <p className="mt-1 text-ink-500"><ChannelIcon channel={hovered.w.channel} className="mr-1" />{hovered.w.channel_label} · {day(hovered.w.published_at)}{hovered.w.origin === "external_import" ? " · 平台导入" : ""}</p>
      <p className="mt-2 tabular-nums text-ink-700">播放/阅读 {num(hovered.w.views)}{medians[hovered.w.channel] && hovered.w.views != null ? `（平常的 ${(hovered.w.views / medians[hovered.w.channel]!).toFixed(1)}×）` : ""} · 互动 {num(hovered.w.engagements)} · 评论 {num(hovered.w.comments)} · 涨粉 {num(hovered.w.followers_gained)}</p>
      {hovered.w.events.length > 0 && <ul className="mt-2 space-y-0.5">{hovered.w.events.map((e, k) => <li key={k}><span className={TONE[e.tone].cls}>{TONE[e.tone].glyph} {e.label}</span> <span className="text-ink-500">{e.detail}</span></li>)}</ul>}
      <p className="mt-2 text-accent-600">点击看这条作品的详细数据 →</p>
    </div>}
    <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-ink-600">{series.map(c => <span key={c} className="inline-flex items-center gap-1.5"><span className="inline-block h-2.5 w-2.5 rounded-full" style={{ background: colorOf(c) }} />{works.find(w => w.channel === c)?.channel_label}</span>)}{top > max && <span className="text-ink-500">↑ 超出图顶的点标了实际数值 ·</span>}<span className="text-ink-500"><span className={TONE.good.cls}>▲</span> 好事件 · <span className={TONE.bad.cls}>▼</span> 要注意 · <span className={TONE.info.cls}>◆</span> 节点</span></div>
  </div>;
}

function FollowerCard({ data }: { data: Followers }) {
  const recorded = data.accounts.filter(a => a.followers != null);
  const missing = data.accounts.filter(a => a.followers == null);
  const max = Math.max(1, ...recorded.map(a => a.followers!));
  const trend = data.trend;
  const delta = trend.length > 1 ? trend[trend.length - 1].followers - trend[0].followers : null;
  return <section className="card grid gap-6 p-6 lg:grid-cols-[16rem_1fr]">
    <div><p className="eyebrow">全网粉丝</p><p className="mt-2 font-serif text-[40px] font-semibold leading-none tabular-nums text-ink-900">{data.total == null ? "—" : num(data.total)}</p>
      <p className="mt-2 text-[12.5px] text-ink-500">{data.recorded} / {data.accounts.length} 个账号已录{data.last_observed_on ? ` · 最近 ${data.last_observed_on.slice(5).replace("-", "/")}` : ""}</p>
      {delta != null && <p className={`mt-1 text-[12.5px] ${delta >= 0 ? "text-emerald-700" : "text-amber-700"}`}>{delta >= 0 ? "▲" : "▼"} {num(Math.abs(delta))}（{trend[0].observed_on.slice(5).replace("-", "/")} 起）</p>}
      {trend.length > 1 && <svg viewBox="0 0 160 40" className="mt-3 h-10 w-40" role="img" aria-label="全网粉丝走势"><polyline fill="none" stroke="#2a78d6" strokeWidth={2} points={trend.map((t, i) => { const lo = Math.min(...trend.map(x => x.followers)), hi = Math.max(...trend.map(x => x.followers)); return `${i * 160 / (trend.length - 1)},${36 - (hi === lo ? 16 : (t.followers - lo) / (hi - lo) * 32)}`; }).join(" ")} /></svg>}
      {data.total == null && <p className="mt-2 text-xs text-ink-500">还没录过粉丝数。让第三方模型按 craft-review 读各平台后台，用 record_account_followers 记下。</p>}
    </div>
    <div className="space-y-2">{recorded.map(a => <div key={a.account_id} className="grid grid-cols-[7rem_1fr_5rem] items-center gap-3 text-sm" title={`${a.account_name} · ${a.observed_on} 录入${a.change != null ? ` · ${a.since} 起 ${a.change >= 0 ? "+" : ""}${a.change}` : ""}`}><span className="truncate text-ink-700"><ChannelIcon channel={a.channel} className="mr-1" />{a.channel_label}</span><span className="h-3 rounded-r bg-ink-100"><span className="block h-3 rounded-r" style={{ width: `${Math.max(1, a.followers! / max * 100)}%`, background: colorOf(a.channel) }} /></span><span className="text-right tabular-nums text-ink-900">{num(a.followers)}{a.change != null && <span className={`ml-1 text-xs ${a.change >= 0 ? "text-emerald-700" : "text-amber-700"}`}>{a.change >= 0 ? "+" : ""}{a.change}</span>}</span></div>)}
      {missing.length > 0 && <p className="pt-1 text-xs text-ink-500">未录入（不计入合计）：{missing.map(a => a.channel_label).join("、")}</p>}
    </div>
  </section>;
}

export default function PersonaPerformance() {
  const [params, setParams] = useSearchParams();
  const set = (key: string, value: string) => setParams(old => { const next = new URLSearchParams(old); if (value) next.set(key, value); else next.delete(key); return next; });
  const personas = useQuery({ queryKey: ["learning-personas", currentUser()], queryFn: () => api.get<{ items: { persona_id: number; name: string; posts: number }[] }>("/learning/personas") });
  const personaId = Number(params.get("persona")) || personas.data?.items[0]?.persona_id || 0;
  const days = Number(params.get("days") ?? 90);
  const metric = (params.get("metric") ?? "relative") as Metric;
  const channel = params.get("ch") ?? "";
  const highlight = params.get("ev") ?? "";
  const query = useQuery({ queryKey: ["persona-timeline", currentUser(), personaId, days], queryFn: () => api.get<Timeline>(`/learning/personas/${personaId}/timeline?days=${days}`), enabled: !!personaId, placeholderData: previous => previous });
  const data = query.data;
  const medians = useMemo(() => Object.fromEntries((data?.channels ?? []).map(c => [c.channel, c.median_views])), [data]);
  const works = (data?.works ?? []).filter(w => !channel || w.channel === channel);
  const events = (data?.events ?? []).filter(e => (!channel || e.channel === channel) && (!highlight || e.type === highlight));
  const eventCounts = (data?.events ?? []).filter(e => !channel || e.channel === channel).reduce<Record<string, number>>((acc, e) => ({ ...acc, [e.type]: (acc[e.type] ?? 0) + 1 }), {});
  const [showAll, setShowAll] = useState(false);
  if (personas.isPending) return <Spinner label="读取角色…" />;
  if (personas.isError) return <ErrorBanner message="角色读取失败。" />;
  const chip = (active: boolean) => `rounded-pill border px-3 py-1.5 text-[13px] ${active ? "border-ink-900 bg-ink-900 text-paper" : "border-ink-300 bg-surface text-ink-700 hover:border-ink-500"}`;
  return <div className="space-y-6">
    <div className="flex flex-wrap gap-2" role="group" aria-label="角色">{personas.data.items.map(p => <button key={p.persona_id} className={chip(p.persona_id === personaId)} onClick={() => setParams(old => { const next = new URLSearchParams(old); next.set("persona", String(p.persona_id)); next.delete("ch"); next.delete("ev"); return next; })}>{p.name} <span className="opacity-70">{p.posts}</span></button>)}</div>
    <div className="flex flex-wrap items-center gap-2">{ranges.map(([value, label]) => <Button key={value} size="sm" variant={days === value ? undefined : "secondary"} onClick={() => set("days", String(value))}>{label}</Button>)}<span className="mx-2 h-5 w-px bg-ink-200" /><select aria-label="平台" className="rounded-lg border border-ink-300 bg-surface px-3 py-1.5 text-sm" value={channel} onChange={e => set("ch", e.target.value)}><option value="">全部平台</option>{(data?.channels ?? []).map(c => <option key={c.channel} value={c.channel}>{c.channel_label}（{c.posts}）</option>)}</select><select aria-label="指标" className="rounded-lg border border-ink-300 bg-surface px-3 py-1.5 text-sm" value={metric} onChange={e => set("metric", e.target.value)}>{Object.entries(metrics).map(([k, m]) => <option key={k} value={k}>{m.label}</option>)}</select><Link className="ml-auto text-sm font-medium text-accent-600 hover:underline" to={`/learning?tab=history&view=list&filter_persona_id=${personaId}${channel ? `&filter_channel=${channel}` : ""}`}>这个角色的作品清单 →</Link></div>
    {query.isPending && <Spinner label="读取作品和效果数据…" />}
    {query.isError && <ErrorBanner message={`角色表现读取失败，不能当作没有数据。${query.error instanceof Error ? query.error.message : ""}`} />}
    {data && <div className={`space-y-6 ${query.isFetching ? "opacity-60" : ""}`}>
      <FollowerCard data={data.followers} />
      <section className="card grid grid-cols-2 gap-x-6 gap-y-5 p-6 lg:grid-cols-5">{([["作品", data.totals.posts, `${data.totals.with_data} 条有效果数据`], ["播放 / 阅读", data.totals.views, "各平台相加"], ["互动", data.totals.engagements, "点赞评论分享收藏"], ["涨粉", data.totals.followers_gained, "作品带来的关注"], ["事件", data.events.length, `好事件 ${data.events.filter(e => e.tone === "good").length} · 要注意 ${data.events.filter(e => e.tone === "bad").length}`]] as const).map(([label, value, hint]) => <div key={label}><p className="eyebrow">{label}</p><p className="mt-2 font-serif text-[26px] font-semibold leading-none tabular-nums text-ink-900">{num(value)}</p><p className="mt-2 text-[12.5px] text-ink-500">{hint}</p></div>)}</section>
      <section className="card space-y-4 p-6">
        <div className="flex flex-wrap items-baseline justify-between gap-2"><h2 className="font-serif text-[20px] font-semibold text-ink-900">按发布顺序看表现</h2><p className="text-xs text-ink-500">横轴是一条条作品（按发布先后），纵轴是{metrics[metric].label}{metrics[metric].hint ? `：${metrics[metric].hint}` : ""}。效果数据最近录入 {day(data.last_observed_at)}。</p></div>
        <Chart works={works} metric={metric} medians={medians} highlight={highlight} />
      </section>
      <div className="grid gap-6 lg:grid-cols-[1fr_22rem]">
        <section className="card space-y-4 p-6"><h2 className="font-serif text-[20px] font-semibold text-ink-900">关键事件</h2>
          <div className="flex flex-wrap gap-2"><button className={chip(!highlight)} onClick={() => set("ev", "")}>全部 {Object.values(eventCounts).reduce((a, b) => a + b, 0)}</button>{data.event_types.filter(t => eventCounts[t.type]).map(t => <button key={t.type} title={t.description} className={chip(highlight === t.type)} onClick={() => set("ev", highlight === t.type ? "" : t.type)}><span className={highlight === t.type ? "" : TONE[t.tone].cls}>{TONE[t.tone].glyph}</span> {t.label} {eventCounts[t.type]}</button>)}</div>
          {highlight && <p className="text-xs text-ink-500">{data.event_types.find(t => t.type === highlight)?.description}。图上只亮出有这个事件的作品。</p>}
          {events.length === 0 ? <p className="text-sm text-ink-500">这段时间没有识别到事件。</p> : <ol className="divide-y divide-ink-100">{(showAll ? events : events.slice(0, 12)).map((e, k) => <li key={k}><Link to={detailHref(e.work_id)} className="flex items-start gap-3 py-2.5 text-sm hover:bg-ink-50"><span className="w-12 shrink-0 text-xs tabular-nums text-ink-500">{day(e.at)}</span><span className={`w-24 shrink-0 ${TONE[e.tone].cls}`}>{TONE[e.tone].glyph} {e.label}</span><span className="min-w-0 flex-1"><span className="block truncate text-ink-900">{e.title}</span><span className="text-xs text-ink-500"><ChannelIcon channel={e.channel} className="mr-1" />{e.channel_label} · {e.detail}</span></span></Link></li>)}</ol>}
          {events.length > 12 && <Button size="sm" variant="secondary" onClick={() => setShowAll(!showAll)}>{showAll ? "收起" : `展开全部 ${events.length} 个事件`}</Button>}
        </section>
        <section className="card space-y-3 p-6"><h2 className="font-serif text-[20px] font-semibold text-ink-900">各平台</h2><table className="w-full text-sm"><thead><tr className="text-left text-xs text-ink-500"><th className="py-1.5 font-normal">平台</th><th className="py-1.5 text-right font-normal">作品</th><th className="py-1.5 text-right font-normal">播放/阅读</th><th className="py-1.5 text-right font-normal">平常</th></tr></thead><tbody>{data.channels.map(c => <tr key={c.channel} className="cursor-pointer border-t border-ink-100 hover:bg-ink-50" onClick={() => set("ch", channel === c.channel ? "" : c.channel)} title={`互动 ${num(c.engagements)} · 涨粉 ${num(c.followers_gained)} · ${c.with_data}/${c.posts} 条有数据`}><td className="py-2"><span className="mr-1.5 inline-block h-2.5 w-2.5 rounded-full" style={{ background: colorOf(c.channel) }} />{c.channel_label}</td><td className="py-2 text-right tabular-nums">{c.posts}</td><td className="py-2 text-right tabular-nums">{num(c.views)}</td><td className="py-2 text-right tabular-nums text-ink-500">{num(c.median_views)}</td></tr>)}</tbody></table><p className="text-xs text-ink-500">「平常」是这个角色在该平台所有作品播放/阅读的中位数，少于 5 条有数据时不算。点一行只看该平台。</p></section>
      </div>
    </div>}
  </div>;
}
