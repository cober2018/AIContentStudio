import { useTaskLink, taskReturn } from "./taskNavigation";
import { useEffect, useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { DiscoveryPanel, discoveryLabel, useDiscoveryStatus } from "./DiscoveryPanel";
import { api, ApiError, currentUser } from "../api";
import { Button, EmptyState, ErrorBanner, Field, Modal, Spinner, inputClass } from "../components/ui";
import type { Assessment, AssessmentRevision, Conversion, Opportunity, OpportunitySignal, OpportunityStatus } from "./opportunityTypes";

const base = "/content-opportunities";
const card = "card min-w-0 break-words p-6 space-y-4 transition-[transform,box-shadow,border-color] duration-300 ease-studio hover:border-ink-300";
const shell = "mx-auto min-h-screen max-w-6xl space-y-6 bg-paper px-4 py-9 sm:px-8";
function useOpportunityPermission() {
  const me = useQuery({ queryKey: ["opportunity-user", currentUser()], queryFn: () => api.get<{ role: string }>("/users/me"), retry: false });
  return { editable: !!me.data && ["admin", "editor"].includes(me.data.role), error: me.isError };
}
function safeUrl(value: unknown): string | undefined {
  if (typeof value !== "string") return undefined;
  try { const url = new URL(value); return ["http:", "https:"].includes(url.protocol) ? url.href : undefined; } catch { return undefined; }
}
function provenance(revision: AssessmentRevision | null) {
  if (!revision) return "尚未评估";
  const provider = revision.analysis_provider_key;
  if (revision.analysis_source === "manual") return "人工评估";
  if (revision.analysis_source === "system" && provider?.includes("correction")) return "系统修订";
  if (revision.analysis_source === "system" && provider === "daily-discovery") return "每日自动选题评估";
  if (revision.analysis_source === "system") return "系统评估";
  if (revision.analysis_source === "model") return "模型评估";
  return "评估来源未记录";
}
const statuses: Record<OpportunityStatus, string> = { new: "待判断", watching: "备选 / 观察中", qualified: "可转项目", dismissed: "已暂缓", converted: "已转项目", archived: "已归档" };
const priorities = { high: "高", normal: "普通", low: "低" };
const triage: OpportunityStatus[] = ["new", "watching", "qualified", "dismissed"];
const signalNames: Record<string, string> = { manual: "人工观察", source_document: "来源文档", data_snapshot: "数据快照", delivery_feedback: "交付反馈", external_ref: "外部引用" };
function errorMessage(error: unknown) { return error instanceof Error ? error.message : "读取后端失败，请重试。"; }
function utcDate(value: string) { return /(?:Z|[+-]\d{2}:\d{2})$/i.test(value) ? value : `${value}Z`; }
function readableTiming(value: string) {
  return value.replace(/\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:\d{2})?)?/g, timestamp => {
    if (!timestamp.includes("T")) { const [year, month, day] = timestamp.split("-"); return `${year}年${Number(month)}月${Number(day)}日`; }
    const time = new Date(utcDate(timestamp));
    return Number.isNaN(time.getTime()) ? timestamp : `${time.toLocaleString("zh-CN", { timeZone: "Asia/Taipei", year: "numeric", month: "long", day: "numeric", hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false })}（台北时间）`;
  });
}
function expired(item: Opportunity) { return !!item.relevant_until && Date.parse(utcDate(item.relevant_until)) < Date.now(); }
function opportunityKind(item: Opportunity, technology: boolean) {
  const assessment = item.latest_assessment?.assessment;
  if (assessment?.time_sensitivity === "timeless" || /^(常青|深度常青)/.test(assessment?.why_now || "")) return technology ? "深度常青" : "常青";
  if (/^(热点|最新动态)/.test(assessment?.why_now || "")) return technology ? "最新动态" : "热点";
  if (/^(近期报道|近期进展)/.test(assessment?.why_now || "")) return technology ? "近期进展" : "近期报道";
  return "类型未记录";
}

function OpportunityFields({ initial, busy, submit }: { initial?: Opportunity; busy: boolean; submit: (body: unknown) => void }) {
  const [title, setTitle] = useState(initial?.title ?? "");
  const [summary, setSummary] = useState(initial?.summary ?? "");
  const [priority, setPriority] = useState(initial?.priority ?? "normal");
  const [until, setUntil] = useState(initial?.relevant_until ? utcDate(initial.relevant_until) : "");
  const [error, setError] = useState("");
  function save(event: FormEvent) {
    event.preventDefault();
    if (until && (!/(?:Z|[+-]\d{2}:\d{2})$/i.test(until) || Number.isNaN(Date.parse(until)))) { setError("有效期请输入完整日期时间，例如 2026-10-01T18:00:00+08:00。"); return; }
    submit({ title: title.trim(), summary, priority, relevant_until: until ? new Date(until).toISOString() : null });
  }
  return <form onSubmit={save} className="space-y-4">
    {error && <ErrorBanner message={error} />}
    <Field label="机会名称"><input required maxLength={300} className={inputClass} value={title} onChange={(e) => setTitle(e.target.value)} /></Field>
    <Field label="概述"><textarea className={inputClass} value={summary} onChange={(e) => setSummary(e.target.value)} /></Field>
    <Field label="优先级"><select className={inputClass} value={priority} onChange={(e) => setPriority(e.target.value as Opportunity["priority"])}>{Object.entries(priorities).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></Field>
    <Field label="有效期（可选，含时区）"><input className={inputClass} value={until} onChange={(e) => setUntil(e.target.value)} /></Field>
    <Button type="submit" disabled={busy || !title.trim()}>{busy ? "保存中…" : "保存机会"}</Button>
  </form>;
}

export function OpportunitiesPage() {
  const navigate = useNavigate();
  const taskLink = useTaskLink();
  const user = currentUser();
  const [params, setParams] = useSearchParams();
  const permission = useOpportunityPermission();
  const personaId = params.get("persona_id") ?? params.get("role") ?? "";
  const dateSelection = params.has("date") ? params.get("date")! : null;
  const keyword = params.get("keyword") || "";
  function filters(patch: Record<string, string | null>) {
    const next = new URLSearchParams(params); next.delete("page");
    Object.entries(patch).forEach(([key, value]) => value === null ? next.delete(key) : next.set(key, value));
    setParams(next);
  }
  const setPersonaId = (value: string) => filters({ persona_id: value, role: null });
  const setDateSelection = (value: string | null) => filters({ date: value });
  const roles = useQuery({ queryKey: ["opportunity-personas", user], queryFn: () => api.get<{ id: number; name: string }[]>("/content-personas") });
  const discovery = useDiscoveryStatus();
  const persona = discovery.data?.personas.find(p => String(p.persona_id) === personaId);
  const technology = persona?.opportunity_policy === "technology.v1";
  const status = params.get("status") ?? "recommended";
  const priority = params.get("priority") || "";
  const requestedPage = Number(params.get("page"));
  const page = Number.isSafeInteger(requestedPage) && requestedPage > 0 ? requestedPage : 1;
  const offset = (page - 1) * 30;
  const setStatus = (value: string) => filters({ status: value, date: null });
  const setPriority = (value: string) => filters({ priority: value });
  const setOffset = (value: number) => { if (value === 0) return; const next = new URLSearchParams(params); next.set("page", String(Math.floor(value / 30) + 1)); setParams(next); };
  const [creating, setCreating] = useState(false);
  const today = persona?.business_date || new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Taipei", year: "numeric", month: "2-digit", day: "2-digit" }).format(new Date());
  const businessDate = dateSelection ?? (status === "recommended" && !technology ? today : "");
  const actionable = technology && status === "recommended";
  const policyRequired = !!personaId && status === "recommended";
  const policyReady = !policyRequired || !!persona?.opportunity_policy;
  const query = useQuery({ queryKey: ["opportunities", user, status, priority, offset, personaId, businessDate, actionable, keyword], enabled: policyReady,
    queryFn: () => api.get<{ items: Opportunity[]; offset: number; limit: number; has_more: boolean }>(`${base}?${new URLSearchParams({ ...(status === "recommended" ? { recommended_only: "true" } : { status }), ...(actionable ? { actionable_only: "true" } : {}), priority, ...(keyword.trim() ? { q: keyword.trim() } : {}), offset: String(offset), limit: "30", ...(personaId ? { persona_id: personaId } : {}), ...(businessDate ? { business_date: businessDate } : {}) })}`) });
  const create = useMutation({ mutationFn: (body: unknown) => api.post<Opportunity>(base, body), onSuccess: (item) => navigate(taskLink(`/opportunities/${item.id}`)) });
  if (params.get("view") === "automation") return <div className={shell}><Link className="text-sm text-teal-800" to={`/opportunities?${new URLSearchParams([...params].filter(([key]) => key !== "view"))}`}>← 返回内容机会</Link><h1 className="text-[34px] leading-[1.1] text-ink-900 sm:text-[40px]">自动选题运行</h1><p className="text-sm text-slate-600">查看实际运行、来源与调度配置。刷新仅重新读取状态。</p><DiscoveryPanel personaId={personaId} /></div>;
  return <div className={shell}>
    {taskReturn(params.get("return_to")) && <Link className="text-sm text-teal-800" to={taskReturn(params.get("return_to"))}>{["/", "/home"].includes(taskReturn(params.get("return_to")).split("?")[0]) ? "返回今日工作台" : "返回来源页面"}</Link>}
    <header className="flex items-start justify-between gap-4"><div><p className="eyebrow">创作 · 选题</p><h1 className="mt-3 text-[34px] leading-[1.1] text-ink-900 sm:text-[40px]">内容机会</h1><p className="mt-2 text-sm text-slate-500">先判断为什么现在做，再明确创建项目。每日建议按角色自动生成，也可保留人工机会。</p></div>{permission.editable && <Button onClick={() => { create.reset(); setCreating(true); }}>新建机会</Button>}</header>
    <section className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-teal-900/10 bg-teal-50/60 p-4 text-sm"><p>{discovery.isError ? "自动选题状态读取失败" : discovery.isPending ? "正在读取运行状态…" : persona ? `${persona.name} · ${discoveryLabel(persona.status)}${persona.today_run ? ` · 今日${discoveryLabel(persona.today_run.status)}${persona.today_run.summary?.count != null ? `，保存 ${persona.today_run.summary.count} 条` : "，保存数未记录"}` : " · 今日运行未记录"}` : "选择角色查看对应运行状态；全部角色不合并计算运行结果。"}</p><Link className="font-medium text-teal-800" to={`?${new URLSearchParams({ ...Object.fromEntries(params), view: "automation" })}`}>查看运行与来源 →</Link></section>
    {permission.error && <ErrorBanner message="用户权限读取失败，当前保持只读。" />}
    <div className="flex flex-wrap gap-3">
      <Field label="关键词"><input className={inputClass} value={keyword} onChange={e => filters({ keyword: e.target.value })} placeholder="搜索机会标题" /></Field>
      <Field label="角色"><select className={inputClass} value={personaId} onChange={e => { setPersonaId(e.target.value); setOffset(0); }}><option value="">全部角色与人工机会</option>{roles.data?.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}</select></Field>
      <Field label="生成日期"><input type="date" className={inputClass} value={businessDate} onChange={e => { setDateSelection(e.target.value); setOffset(0); }} /></Field>
      <Field label="状态"><select className={inputClass} value={status} onChange={e => { setStatus(e.target.value); }}><option value="recommended">当前建议（不含备选）</option><option value="">全部状态（含备选和历史）</option>{Object.entries(statuses).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></Field>
      <Field label="优先级"><select className={inputClass} value={priority} onChange={e => { setPriority(e.target.value); setOffset(0); }}><option value="">全部优先级</option>{Object.entries(priorities).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></Field>
      <Button variant="secondary" onClick={() => { setDateSelection(today); setOffset(0); }}>今天新生成</Button>
      <Button variant="secondary" onClick={() => { filters({ date: null, status: "recommended", priority: "", page: null }); }}>默认建议</Button>
      <Button variant="secondary" disabled={query.isFetching || discovery.isFetching} onClick={() => { void discovery.refetch(); if (policyReady) void query.refetch(); }}>刷新</Button>
    </div>
    <p className="text-xs text-slate-600">{personaId ? persona?.name || roles.data?.find(p => String(p.id) === personaId)?.name || `角色 ${personaId}` : "全部角色与人工机会"} · 生成日期：{businessDate || "不限"}{actionable ? " · 仅待判断 / 可转项目且有效期未到的建议" : ""}。全部状态可查看已处理、过期和有效期未记录的历史。</p>
    {roles.isError && <ErrorBanner message="角色列表读取失败，请刷新重试。" />}
    {!policyReady && discovery.isError ? <ErrorBanner message="角色选题策略读取失败，暂时无法加载默认建议。请刷新重试。" /> : !policyReady && !discovery.isPending ? <ErrorBanner message="该角色的选题策略未记录，暂时无法加载默认建议；可切换全部状态查看历史。" /> : query.isPending ? <Spinner /> : query.isError ? <ErrorBanner message={errorMessage(query.error)} /> : <>
      {query.data.items.length === 0 ? <div className="space-y-2" role="status"><EmptyState title="当前筛选下没有内容机会" /><p className="text-center text-sm text-slate-600">请核对角色、生成日期、状态和优先级；列表为空不代表今日运行完成或生成了 0 条。今日是否运行、是否失败和实际保存数请查看运行与来源。</p></div> : <div className="grid gap-4 lg:grid-cols-2">{query.data.items.map((item) => <Link className={card} key={item.id} to={taskLink(`/opportunities/${item.id}?${params}`)}><div className="flex items-start justify-between gap-3"><h2 className="min-w-0 font-serif text-[18px] font-semibold leading-snug text-ink-900">{item.title}</h2><span className="shrink-0 whitespace-nowrap rounded-pill bg-sky-50 px-2.5 py-0.5 text-[11.5px] text-sky-700">{statuses[item.status]}</span></div><p className="line-clamp-4 text-[14px] leading-relaxed text-ink-600">{item.summary || "暂无概述"}</p><p className="text-xs text-slate-500">{item.persona_id ? `${roles.data?.find(p => p.id === item.persona_id)?.name || `角色 ${item.persona_id}`} · ` : "人工机会 · "}{item.research_run_id ? `${opportunityKind(item, discovery.data?.personas.find(p => p.persona_id === item.persona_id)?.opportunity_policy === "technology.v1")} · ` : ""}优先级：{priorities[item.priority]} · {item.signal_count} 条参考资料 · {item.latest_assessment ? `评估 v${item.latest_assessment.revision_no}` : "尚未评估"}{expired(item) ? " · 已超过有效期" : ""}</p><p className="text-xs text-slate-500">生成日期：{item.business_date || "未记录"} · {item.relevant_until ? `有效期至：${new Date(utcDate(item.relevant_until)).toLocaleString("zh-CN", { timeZone: "Asia/Taipei" })}（台北时间）` : "有效期未记录"}</p><p className="text-sm">推荐理由：{item.latest_assessment?.assessment.brand_relevance || "尚未记录"}</p><p className="text-xs text-slate-500">资料类型：{item.signal_types.map((type) => signalNames[type] || type).join("、") || "未添加"}</p></Link>)}</div>}
      <div className="flex items-center gap-3"><Button variant="secondary" disabled={offset === 0} onClick={() => setParams(previous => { const next = new URLSearchParams(previous); next.set("page", String(Math.max(1, page - 1))); return next; })}>上一页</Button><span className="text-sm">第 {Math.floor(offset / 30) + 1} 页</span><Button variant="secondary" disabled={!query.data.has_more} onClick={() => setOffset(offset + 30)}>下一页</Button></div>
    </>}
    {creating && permission.editable && <Modal title="新建内容机会" onClose={() => { if (!create.isPending) setCreating(false); }}>{create.isError && <ErrorBanner message={errorMessage(create.error)} />}<OpportunityFields busy={create.isPending} submit={(body) => create.mutate(body)} /></Modal>}
  </div>;
}

export function OpportunityDetailPage() {
  const { id } = useParams();
  return id && /^\d+$/.test(id) ? <OpportunityDetail key={`${currentUser()}:${id}`} id={Number(id)} /> : <ErrorBanner message="内容机会编号无效。" />;
}

function OpportunityDetail({ id }: { id: number }) {
  const taskLink = useTaskLink();
  const user = currentUser();
  const client = useQueryClient();
  const [params, setParams] = useSearchParams();
  const view = params.get("view") || "detail";
  const permission = useOpportunityPermission();
  const path = `${base}/${id}`;
  const [editing, setEditing] = useState(false);
  const [revisionId, setRevisionId] = useState<number | null>(null);
  const detail = useQuery({ queryKey: ["opportunity", user, id], queryFn: () => api.get<Opportunity>(path) });
  const signals = useQuery({ queryKey: ["opportunity-signals", user, id], queryFn: () => api.get<OpportunitySignal[]>(`${path}/signals`) });
  const revisions = useQuery({ queryKey: ["opportunity-assessments", user, id], queryFn: () => api.get<AssessmentRevision[]>(`${path}/assessments`), enabled: view === "history" });
  const conversion = useQuery({ queryKey: ["opportunity-conversion", user, id], queryFn: () => api.get<Conversion | null>(`${path}/conversion`) });
  const historical = useQuery({ queryKey: ["opportunity-revision", user, id, revisionId], queryFn: () => api.get<AssessmentRevision>(`${path}/assessments/${revisionId}`), enabled: view === "history" && revisionId !== null });
  async function refresh() {
    await Promise.all(["opportunity", "opportunity-signals", "opportunity-assessments", "opportunity-conversion", "opportunities", "home"].map((key) => client.invalidateQueries({ queryKey: [key] })));
  }
  const change = useMutation({ mutationFn: (body: unknown) => api.patch<Opportunity>(path, body), onSuccess: async () => { setEditing(false); await refresh(); } });
  const archive = useMutation({ mutationFn: () => api.del(path), onSuccess: refresh });
  const navigateView = (value: string) => { const next = new URLSearchParams(params); next.set("view", value); setParams(next); };
  const listParams = new URLSearchParams(params); listParams.delete("view");
  const viewLink = (value: string) => { const next = new URLSearchParams(params); next.set("view", value); return `?${next}`; };
  if (detail.isPending) return <Spinner />;
  if (detail.isError) return <div className="p-6"><ErrorBanner message={errorMessage(detail.error)} /><Button onClick={() => void detail.refetch()}>重试</Button></div>;
  const item = detail.data;
  const readonly = !permission.editable || item.status === "converted" || item.status === "archived";
  const busy = change.isPending || archive.isPending;
  const assessment = item.latest_assessment?.assessment;
  const activeSignals = signals.data?.filter(signal => signal.status !== "detached") || [];
  const canCreate = !readonly && ["new", "watching", "qualified"].includes(item.status) && !!item.latest_assessment;
  return <div className={shell}>
    <Link className="text-sm text-teal-800" to={taskReturn(params.get("return_to"), `/opportunities?${listParams}`)}>← 返回机会来源</Link>
    <header className="space-y-3"><p className="eyebrow">{view === "direction" ? "02 / 确认创作方向" : view === "sources" ? "03 / 阅读资料与确认创建" : view === "history" ? "评估历史" : view === "advanced" ? "高级维护" : "01 / 判断选题价值"}</p><h1 className="text-[34px] leading-[1.1] text-ink-900 sm:text-[40px]">{item.title}</h1><p className="text-slate-600">{item.summary || "概述未记录"}</p><p className="text-sm text-slate-500">{statuses[item.status]} · 优先级 {priorities[item.priority]}{expired(item) ? " · 已超过有效期" : ""}{readonly ? " · 只读" : ""}</p></header>
    <nav className="flex flex-wrap gap-5 border-b border-slate-200 pb-4 text-sm">{[["detail", "推荐详情"], ["direction", "创作方向"], ["sources", "阅读与选择资料"], ["history", "评估历史"], ["advanced", "高级维护"]].map(([key, label]) => <Link key={key} aria-current={view === key ? "page" : undefined} className={view === key ? "font-semibold text-teal-800" : "text-slate-500"} to={viewLink(key)}>{label}</Link>)}</nav>
    {permission.error && <ErrorBanner message="用户权限读取失败，当前保持只读。" />}
    {(change.isError || archive.isError) && <ErrorBanner message={errorMessage(change.error || archive.error)} />}
    {conversion.isError && <ErrorBanner message="已有项目关系读取失败，请刷新核对后再创建。" />}
    {conversion.data && <section className={card}><h2 className="font-semibold">已创建内容项目</h2><Link className="text-teal-800" to={taskLink(`/projects/${conversion.data.project_id}`)}>打开已有项目 →</Link><p className="text-sm text-slate-500">下一步：进入角色创作流程，确认任务书与来源事实。</p></section>}
    {item.status === "converted" && conversion.isSuccess && !conversion.data && <ErrorBanner message="转换关系缺失，请刷新核对；不要重复创建项目。" />}
    {view === "detail" && <>
      <section className={card}><p className="text-xs text-teal-800">{provenance(item.latest_assessment)}{item.latest_assessment ? ` · v${item.latest_assessment.revision_no}` : ""} · {opportunityKind(item, /^(最新动态|近期进展|深度常青)/.test(assessment?.why_now || ""))}</p><h2 className="text-xl font-semibold">为什么推荐</h2><p className="whitespace-pre-wrap text-slate-700">{assessment?.brand_relevance || "角色相关性未记录。"}</p><p className="whitespace-pre-wrap text-sm">受众：{assessment?.audience_fit || "未记录"}</p>{assessment?.what_happened && assessment.what_happened.trim() !== item.summary.trim() && <p className="whitespace-pre-wrap text-sm text-slate-500">{assessment.what_happened}</p>}<details className="border-t border-slate-100 pt-3 text-sm"><summary className="cursor-pointer text-teal-800">查看时效依据</summary><p className="mt-3 whitespace-pre-wrap text-slate-600">{assessment?.why_now ? readableTiming(assessment.why_now) : "时效依据未记录。"}</p></details></section>
      <section className={card}><h2 className="text-xl font-semibold">建议怎么做</h2><p className="whitespace-pre-wrap">{assessment?.suggested_angle || "创作角度未记录"}</p>{canCreate && !conversion.data && conversion.isSuccess && <Button onClick={() => navigateView("direction")}>确认创作方向 →</Button>}{item.status === "dismissed" && <p className="text-sm text-amber-800">该机会已暂缓；继续前请到高级维护明确恢复。</p>}</section>
      <section className={card}><h2 className="text-xl font-semibold">参考资料与缺口</h2>{signals.isPending ? <Spinner /> : signals.isError ? <ErrorBanner message={errorMessage(signals.error)} /> : <><p className="text-sm">{activeSignals.length ? `已关联 ${activeSignals.length} 条参考资料；正文是否完整需逐条阅读。` : "尚无参考资料；缺少资料不代表事实已核实。"}</p>{activeSignals.slice(0, 4).map(signal => <p key={signal.id} className="text-sm text-slate-600">{signal.label || signalNames[signal.signal_type] || "未命名参考"}</p>)}</>}{assessment?.risk_flags?.length ? <ul className="list-disc space-y-2 pl-5 text-sm text-amber-800">{assessment.risk_flags.map((risk, index) => <li key={index} className="whitespace-pre-wrap">{risk}</li>)}</ul> : <p className="text-sm text-amber-800">风险信息未记录，仍需核对事实与使用许可。</p>}<Link className="text-teal-800" to={viewLink("sources")}>阅读参考资料 →</Link></section>
    </>}
    {view === "sources" && !item.latest_assessment ? <section className={card}><h2 className="text-xl font-semibold">阅读参考资料</h2><p className="text-sm text-slate-600">尚无已保存的评估，暂不能创建项目；仍可阅读参考资料与原文，资料不等于已核实事实或使用许可。</p>{signals.isPending ? <Spinner /> : signals.isError ? <ErrorBanner message={errorMessage(signals.error)} /> : signals.data.length ? signals.data.map(signal => <ReferencePreview key={signal.id} signal={signal} />) : <EmptyState title="尚无参考资料" />}</section> : (view === "direction" || view === "sources") && <>{signals.isPending ? <Spinner /> : signals.isError ? <ErrorBanner message={errorMessage(signals.error)} /> : item.latest_assessment ? <ConversionForm key={`${user}:${item.id}`} item={item} signals={signals.data} saved={refresh} view={view} navigateView={navigateView} editable={canCreate && conversion.isSuccess && !conversion.data} /> : <EmptyState title="尚无评估，暂不能创建项目" />}</>}
    {view === "history" && <section className={card}><h2 className="text-xl font-semibold">不可变评估历史</h2>{revisions.isPending ? <Spinner /> : revisions.isError ? <ErrorBanner message={errorMessage(revisions.error)} /> : <Field label="查看版本"><select className={inputClass} value={revisionId ?? ""} onChange={e => setRevisionId(e.target.value ? Number(e.target.value) : null)}><option value="">当前评估</option>{revisions.data.map(rev => <option key={rev.id} value={rev.id}>v{rev.revision_no} · {provenance(rev)} · {rev.created_at || "时间未记录"}</option>)}</select></Field>}{revisionId !== null ? historical.isPending ? <Spinner /> : historical.isError ? <ErrorBanner message={errorMessage(historical.error)} /> : <AssessmentView revision={historical.data} /> : <AssessmentView revision={item.latest_assessment} />}</section>}
    {view === "advanced" && <>
      <section className={card}><h2 className="font-semibold">机会维护</h2><div className="flex flex-wrap gap-2">{!readonly && <><Button variant="secondary" disabled={busy} onClick={() => { change.reset(); setEditing(true); }}>编辑机会</Button>{triage.filter(status => status !== item.status).map(status => <Button key={status} variant="secondary" disabled={busy} onClick={() => change.mutate({ status })}>{item.status === "dismissed" ? `恢复为${statuses[status]}` : statuses[status]}</Button>)}</>}{permission.editable && item.status !== "archived" && <Button variant="danger" disabled={busy} onClick={() => { if (window.confirm("归档这个内容机会？历史评估和项目关系将保留。")) archive.mutate(); }}>归档</Button>}<Button variant="secondary" onClick={() => void refresh()}>刷新</Button></div></section>
      <section className={card}><h2 className="font-semibold">来源信号维护</h2><p className="text-xs text-slate-500">参考信号不等于批准事实或使用许可。</p>{signals.isPending ? <Spinner /> : signals.isError ? <ErrorBanner message={errorMessage(signals.error)} /> : <><SignalList signals={signals.data} path={readonly ? undefined : path} saved={refresh} />{!readonly && <SignalForm path={path} saved={refresh} />}</>}</section>
      <section className={card}><h2 className="font-semibold">当前评估与人工修订</h2><AssessmentView revision={item.latest_assessment} technical />{!readonly && signals.isSuccess && <AssessmentForm key={item.latest_assessment?.id ?? 0} path={path} current={item.latest_assessment} signals={signals.data} saved={refresh} />}</section>
    </>}
    {editing && !readonly && <Modal title="编辑内容机会" onClose={() => { if (!busy) setEditing(false); }}>{change.isError && <ErrorBanner message={errorMessage(change.error)} />}<OpportunityFields initial={item} busy={busy} submit={body => change.mutate(body)} /></Modal>}
  </div>;
}

function SignalList({ signals, path, saved }: { signals: OpportunitySignal[]; path?: string; saved: () => Promise<void> }) {
  const detach = useMutation({ mutationFn: (signalId: number) => api.del(`${path}/signals/${signalId}`), onSuccess: saved });
  return <div className="space-y-3">
    {detach.isError && <ErrorBanner message={errorMessage(detach.error)} />}
    {signals.length === 0 ? <p className="text-sm text-slate-500">尚无信号。</p> : <ul className="space-y-3">{signals.map((signal) => <li key={signal.id} className="rounded-lg border border-slate-200 p-3 text-sm">
      <p>#{signal.id} · {signalNames[signal.signal_type] || signal.signal_type} · {signal.label}{signal.status === "detached" ? " · 已解除引用" : ""}</p>
      <p className="mt-1 text-xs text-slate-500">来源 ID：{signal.source_entity_id ?? "无外部实体血缘"} · 版本：{signal.source_version ?? "未知"} · checksum：{signal.source_checksum ?? "未知"} · 观察时间：{signal.observed_at ?? "未知"}</p>
      {signal.external_ref && <p className="break-all text-xs">外部引用：{signal.external_ref}</p>}
      <pre className="mt-2 whitespace-pre-wrap break-all text-xs">{JSON.stringify(signal.annotation, null, 2)}</pre>
      {signal.signal_type === "source_document" && signal.source_entity_id && <Link className="text-teal-700" to="/assets">打开素材与知识 · 手动查找 Source #{signal.source_entity_id} →</Link>}
      {path && signal.status !== "detached" && <Button className="mt-2" variant="secondary" size="sm" disabled={detach.isPending} onClick={() => { if (window.confirm(`解除信号 #${signal.id} 的当前引用？历史评估与原始来源将保留。`)) detach.mutate(signal.id); }}>解除信号引用</Button>}
    </li>)}</ul>}
  </div>;
}

function SignalForm({ path, saved }: { path: string; saved: () => Promise<void> }) {
  const [type, setType] = useState("manual");
  const [entityId, setEntityId] = useState("");
  const [label, setLabel] = useState("");
  const [external, setExternal] = useState("");
  const [annotation, setAnnotation] = useState("");
  const add = useMutation({ mutationFn: () => api.post(`${path}/signals`, { signal_type: type, source_entity_id: ["manual", "external_ref"].includes(type) ? null : Number(entityId), external_ref: type === "external_ref" ? external : null, label, annotation: { note: annotation } }), onSuccess: async () => { setLabel(""); setAnnotation(""); await saved(); } });
  return <form className="grid gap-3 sm:grid-cols-2" onSubmit={(e) => { e.preventDefault(); add.mutate(); }}><Field label="信号类型"><select className={inputClass} value={type} onChange={(e) => setType(e.target.value)}>{Object.entries(signalNames).map(([value, name]) => <option key={value} value={value}>{name}</option>)}</select></Field>{!["manual", "external_ref"].includes(type) && <Field label="已存在的来源实体 ID"><input required type="number" min={1} step={1} className={inputClass} value={entityId} onChange={(e) => setEntityId(e.target.value)} /></Field>}<Field label="标签（可选，留空使用后端来源名称）"><input maxLength={300} className={inputClass} value={label} onChange={(e) => setLabel(e.target.value)} /></Field>{type === "external_ref" && <Field label="外部引用"><input required maxLength={1000} className={inputClass} value={external} onChange={(e) => setExternal(e.target.value)} /></Field>}<Field label="观察备注"><textarea maxLength={4000} className={inputClass} value={annotation} onChange={(e) => setAnnotation(e.target.value)} /></Field><div className="sm:col-span-2">{add.isError && <ErrorBanner message={errorMessage(add.error)} />}<Button type="submit" disabled={add.isPending}>追加信号</Button></div></form>;
}

const textFields = { what_happened: "发生了什么", why_now: "为什么现在做", brand_relevance: "品牌相关性", audience_fit: "受众匹配", suggested_angle: "建议切入角度（suggested）" } as const;
function AssessmentView({ revision, technical = false }: { revision: AssessmentRevision | null; technical?: boolean }) {
  if (!revision) return <p className="text-sm text-slate-500">尚未评估，不代表没有风险或没有相似内容。</p>;
  const data = revision.assessment;
  return <div className="space-y-2 text-sm">
    <p className="break-all text-xs text-slate-500">{provenance(revision)} · v{revision.revision_no} · {revision.analysis_provider_key || "提供方未记录"} · {revision.analysis_provider_version || "提供方版本未记录"} · {revision.created_by || "作者未知"} · {revision.created_at || "时间未知"}{technical ? ` · checksum ${revision.checksum}` : ""}</p>
    {Object.entries(textFields).map(([key, label]) => <p key={key}><span className="text-slate-500">{label}：</span>{data[key as keyof typeof textFields] || "未记录"}</p>)}
    <p className="whitespace-pre-wrap">证据概述：{data.evidence_summary?.join("\n") || "未记录"}</p>
    <p>选题类型 / 时效：{data.time_sensitivity ? { high: "近期事件或报道（见时间依据）", medium: "中", low: "低", timeless: "常青" }[data.time_sensitivity] : "未知"}</p>
    <p>置信度：{data.confidence == null ? "未知" : `${Math.round(data.confidence * 100)}%`} · 风险：{data.risk_flags?.length ? data.risk_flags.join("、") : "未记录风险，不能视为无风险"}</p>
    <p>相似历史：{data.similarity_state === "none" ? "评估记录为无相似内容" : data.similarity_state === "possible" ? "可能相似，需人工核对" : "unknown · 未知／未核对"}</p>
    <p>建议身份 / 形态 / 渠道（suggested，未批准）：</p>
    {technical ? <pre className="whitespace-pre-wrap break-all text-xs">{JSON.stringify({ recommended_identity_refs: data.recommended_identity_refs ?? [], recommended_modalities: data.recommended_modalities ?? [], recommended_channels: data.recommended_channels ?? [], evidence_signal_ids: data.evidence_signal_ids ?? [], similar_content_refs: data.similar_content_refs ?? [] }, null, 2)}</pre> : <p>形态：{data.recommended_modalities?.join("、") || "未记录"} · 渠道：{data.recommended_channels?.join("、") || "未记录"} · 身份建议{data.recommended_identity_refs?.length ? "已记录，进入项目后确认" : "未记录"}</p>}
  </div>;
}

function AssessmentForm({ path, current, signals, saved }: { path: string; current: AssessmentRevision | null; signals: OpportunitySignal[]; saved: () => Promise<void> }) {
  const [draft, setDraft] = useState<Assessment>({ what_happened: "", why_now: "", brand_relevance: "", audience_fit: "", suggested_angle: "", time_sensitivity: "timeless", recommended_identity_refs: [], recommended_modalities: [], recommended_channels: [], evidence_signal_ids: [], evidence_summary: [], risk_flags: [], similarity_state: "unknown", similar_content_refs: [], confidence: null, ...current?.assessment });
  const [identities, setIdentities] = useState(JSON.stringify(draft.recommended_identity_refs));
  const [similar, setSimilar] = useState(JSON.stringify(draft.similar_content_refs));
  const [error, setError] = useState("");
  const save = useMutation({ mutationFn: (assessment: Assessment) => api.post(`${path}/assessments`, { expected_revision: current?.revision_no ?? 0, assessment }), onSuccess: saved });
  function submit(event: FormEvent) {
    event.preventDefault(); setError("");
    try {
      const refs: unknown = JSON.parse(identities); const history: unknown = JSON.parse(similar);
      if (!Array.isArray(refs) || refs.some((ref) => !ref || typeof ref !== "object" || Array.isArray(ref)) || !Array.isArray(history)) throw new Error("身份建议需为对象数组，相似内容引用需为 JSON 数组。");
      if (history.some((ref) => !ref || typeof ref !== "object" || Array.isArray(ref) || Object.keys(ref).length !== 1 || !Number.isInteger(ref.project_id) || ref.project_id < 1)) throw new Error("相似内容引用需为仅包含正整数 project_id 的对象数组。");
      save.mutate({ ...draft, recommended_identity_refs: refs as Record<string, unknown>[], similar_content_refs: history });
    } catch (err) { setError(errorMessage(err)); }
  }
  return <form onSubmit={submit} className="space-y-4 border-t border-slate-200 pt-4"><h3 className="font-medium">追加人工评估 · 基于 v{current?.revision_no ?? 0}</h3><fieldset disabled={save.isPending} className="grid gap-3 sm:grid-cols-2">
    {Object.entries(textFields).map(([key, label]) => <Field key={key} label={label}><textarea required={key === "why_now"} maxLength={5000} className={inputClass} value={draft[key as keyof typeof textFields] ?? ""} onChange={(e) => setDraft({ ...draft, [key]: e.target.value })} /></Field>)}
    <Field label="证据概述（每行一条，最多 30 条）"><textarea className={inputClass} defaultValue={draft.evidence_summary.join("\n")} onChange={(e) => setDraft({ ...draft, evidence_summary: e.target.value.split("\n").map((line) => line.trim()).filter(Boolean) })} /></Field>
    <Field label="时效性"><select className={inputClass} value={draft.time_sensitivity} onChange={(e) => setDraft({ ...draft, time_sensitivity: e.target.value as Assessment["time_sensitivity"] })}>{Object.entries({ high: "高", medium: "中", low: "低", timeless: "长期有效" }).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></Field>
    <Field label="相似历史判断"><select className={inputClass} value={draft.similarity_state} onChange={(e) => setDraft({ ...draft, similarity_state: e.target.value as Assessment["similarity_state"] })}><option value="unknown">未知／未核对</option><option value="none">人工确认无相似内容</option><option value="possible">可能相似</option></select></Field>
    <Field label="置信度（0–1，可留空表示未知）"><input className={inputClass} type="number" min={0} max={1} step="any" value={draft.confidence ?? ""} onChange={(e) => setDraft({ ...draft, confidence: e.target.value === "" ? null : Number(e.target.value) })} /></Field>
    {(["recommended_modalities", "recommended_channels", "risk_flags"] as const).map((key) => <Field key={key} label={{ recommended_modalities: "建议形态（suggested，逗号分隔）", recommended_channels: "建议渠道（suggested，逗号分隔）", risk_flags: "风险标记（逗号分隔）" }[key]}><input className={inputClass} defaultValue={draft[key].join(", ")} onChange={(e) => setDraft({ ...draft, [key]: e.target.value.split(/[,，]/).map((text) => text.trim()).filter(Boolean) })} /></Field>)}
    <Field label="建议身份引用（suggested，JSON 数组）" hint="使用已有 brand_id / persona_id / account_id / series_id；服务端校验可见层级。"><textarea className={inputClass} value={identities} onChange={(e) => setIdentities(e.target.value)} /></Field><Field label="相似内容引用（JSON 数组）"><textarea className={inputClass} value={similar} onChange={(e) => setSimilar(e.target.value)} /></Field>
    <div className="sm:col-span-2"><p className="mb-2 text-xs text-slate-500">评估引用信号（不自动绑定项目来源）</p>{signals.map((signal) => <label key={signal.id} className="mr-4 inline-flex items-center gap-2 text-sm"><input type="checkbox" checked={draft.evidence_signal_ids.includes(signal.id)} onChange={(e) => setDraft({ ...draft, evidence_signal_ids: e.target.checked ? [...draft.evidence_signal_ids, signal.id] : draft.evidence_signal_ids.filter((id) => id !== signal.id) })} />#{signal.id} {signal.label}</label>)}</div>
  </fieldset>{(error || save.isError) && <ErrorBanner message={error || (save.error instanceof ApiError && save.error.status === 409 ? "评估版本已变化。请先复制当前输入，再刷新并基于最新版本保存；本次输入仍保留。" : errorMessage(save.error))} />}<Button type="submit" disabled={save.isPending}>保存新评估版本</Button></form>;
}

function conversionIdempotencyKey(storageKey: string): string {
  const previous = sessionStorage.getItem(storageKey);
  if (previous) return previous;
  let value: string;
  if (typeof crypto.randomUUID === "function") {
    value = crypto.randomUUID();
  } else {
    // HTTP LAN origins lack randomUUID; getRandomValues remains available there.
    const bytes = crypto.getRandomValues(new Uint8Array(16));
    bytes[6] = (bytes[6] & 0x0f) | 0x40;
    bytes[8] = (bytes[8] & 0x3f) | 0x80;
    const hex = Array.from(bytes, (byte) => byte.toString(16).padStart(2, "0")).join("");
    value = `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
  }
  sessionStorage.setItem(storageKey, value);
  return value;
}

interface DirectionDraft { revision: number; title: string; objective: string; selected: number[] }
function readDirectionDraft(scope: string, item: Opportunity): DirectionDraft {
  const revision = item.latest_assessment!.revision_no;
  try {
    const active = sessionStorage.getItem(`${scope}:active`);
    const raw = sessionStorage.getItem(`${scope}:${active || revision}`);
    if (raw) {
      const parsed: unknown = JSON.parse(raw);
      if (parsed && typeof parsed === "object") {
        const value = parsed as DirectionDraft;
        if (Number.isSafeInteger(value.revision) && value.revision > 0 && typeof value.title === "string" && typeof value.objective === "string" && Array.isArray(value.selected) && value.selected.every(Number.isSafeInteger)) return value;
      }
    }
  } catch { /* A disabled browser store must not prevent reading the opportunity. */ }
  return { revision, title: item.title, objective: item.latest_assessment?.assessment.suggested_angle || item.latest_assessment?.assessment.what_happened || item.summary, selected: [] };
}

function ReferencePreview({ signal }: { signal: OpportunitySignal }) {
  const [reading, setReading] = useState(false);
  const document = signal.signal_type === "source_document" && signal.source_entity_id !== null;
  const source = useQuery({ queryKey: ["opportunity-source", currentUser(), signal.source_entity_id], queryFn: () => api.get<{ raw_text?: string | null; title?: string }>(`/sources/${signal.source_entity_id}`), enabled: reading && document });
  const url = safeUrl(signal.external_ref) || safeUrl(signal.annotation.url) || safeUrl(signal.annotation.source_url);
  const note = [signal.annotation.note, signal.annotation.summary].filter(value => typeof value === "string" && value.trim()).join("\n");
  return <article className="space-y-3 rounded-xl border border-slate-200 p-4">
    <h3 className="font-medium">{signal.label || signalNames[signal.signal_type] || "未命名参考"}</h3>
    <p className="text-xs text-slate-500">{signalNames[signal.signal_type] || "其他参考"}{signal.status === "detached" ? " · 已解除引用" : ""}</p>
    {url ? <a className="text-sm text-teal-800" href={url} target="_blank" rel="noopener noreferrer">阅读原文 ↗</a> : <p className="text-xs text-slate-500">原文链接未记录或不是安全的网页链接。</p>}
    {note && <div className="text-sm"><p className="mb-1 text-xs text-slate-500">人工备注 / 摘要（不代替原文）</p><p className="whitespace-pre-wrap">{note}</p></div>}
    {document ? <><Button variant="secondary" size="sm" onClick={() => setReading(!reading)}>{reading ? "收起资料正文" : "阅读已保存正文"}</Button>{reading && (source.isPending ? <Spinner /> : source.isError ? <div className="space-y-2"><ErrorBanner message="资料正文读取失败；参考关系仍保留。" /><Button variant="secondary" size="sm" onClick={() => void source.refetch()}>重试读取正文</Button></div> : <div className="max-h-80 overflow-auto whitespace-pre-wrap rounded-lg bg-slate-50 p-4 text-sm">{source.data.raw_text?.trim() || "该来源尚无可阅读的正文。"}</div>)}</> : <p className="text-xs text-slate-500">{signal.signal_type === "manual" ? "这是人工观察，未关联文档正文。" : "此参考不是来源文档；请从原文链接阅读，当前不能直接绑定为项目来源。"}</p>}
  </article>;
}

function ConversionForm({ item, signals, saved, view, navigateView, editable }: { item: Opportunity; signals: OpportunitySignal[]; saved: () => Promise<void>; view: string; navigateView: (value: string) => void; editable: boolean }) {
  const navigate = useNavigate();
  const taskLink = useTaskLink();
  const scope = `opportunity-direction:${currentUser()}:${item.id}`;
  const [draft, setDraft] = useState<DirectionDraft>(() => readDirectionDraft(scope, item));
  const [storageError, setStorageError] = useState("");
  const [stage, setStage] = useState("");
  const [createdProject, setCreatedProject] = useState<number | null>(null);
  useEffect(() => {
    try { sessionStorage.setItem(`${scope}:${draft.revision}`, JSON.stringify(draft)); sessionStorage.setItem(`${scope}:active`, String(draft.revision)); setStorageError(""); }
    catch { setStorageError("浏览器暂存不可用；本页输入仍保留，刷新后可能丢失。"); }
  }, [scope, draft]);
  const eligible = signals.filter(signal => signal.signal_type === "source_document" && signal.source_entity_id !== null && signal.status !== "detached");
  const selected = draft.selected.filter(id => eligible.some(signal => signal.id === id));
  const stale = draft.revision !== item.latest_assessment!.revision_no;
  const assessment = item.latest_assessment!.assessment;
  const personas = useQuery({ queryKey: ["opportunity-personas", currentUser()], queryFn: () => api.get<{ id: number; name: string }[]>("/content-personas") });
  const suggestedRoles = assessment.recommended_identity_refs?.flatMap(ref => typeof ref.persona_id === "number" ? [personas.data?.find(persona => persona.id === ref.persona_id)?.name || "角色名称未读取"] : []) || [];
  const convert = useMutation({ mutationFn: async () => {
    if (!editable) throw new Error("当前机会或用户权限不允许创建项目。");
    if (stale) throw new Error("评估版本已变化，请先核对最新评估；草稿仍保留。");
    const key = conversionIdempotencyKey(`opportunity-conversion:${currentUser()}:${item.id}:${draft.revision}`);
    if (item.status === "new" || item.status === "watching") {
      setStage("正在将机会确认为可转项目…");
      await api.patch(`${base}/${item.id}`, { status: "qualified" });
      setStage("机会已确认为可转项目；正在创建项目…");
    } else setStage("正在创建项目…");
    return api.post<Conversion>(`${base}/${item.id}/convert-to-project`, { expected_assessment_revision: draft.revision, idempotency_key: key, title: draft.title.trim() || undefined, objective: draft.objective.trim() || undefined, selected_signal_ids: selected });
  }, onSuccess: async result => {
    setCreatedProject(result.project_id);
    setStage("项目已创建。下一步：在项目总览进入角色创作，确认任务书与来源事实。");
    try { await saved(); } finally { navigate(taskLink(`/projects/${result.project_id}?from=opportunity&next=creation`)); }
  }, onError: () => { setStage(previous => previous.includes("机会已确认") ? "机会已确认为可转项目，项目创建未完成；输入仍保留，请核对后再继续。" : "本次创建未完成；输入仍保留。请刷新核对机会状态与已有项目。"); } });
  const locked = !editable || convert.isPending || createdProject !== null;
  return <div className="space-y-5">
    {storageError && <ErrorBanner message={storageError} />}
    {stale && <section className="space-y-3 rounded-xl border border-amber-200 bg-amber-50 p-4"><p className="text-sm text-amber-900">评估已从草稿的 v{draft.revision} 变为 v{item.latest_assessment!.revision_no}。旧草稿仍保留；请先核对推荐详情，再明确采用最新版本。</p><Button variant="secondary" disabled={locked} onClick={() => setDraft({ ...draft, revision: item.latest_assessment!.revision_no })}>保留输入，采用最新评估版本</Button></section>}
    {!editable && <p className="text-sm text-slate-600">当前只读或已有项目，不能创建新项目。可阅读参考资料。</p>}
    {view === "direction" ? <section className={card}><h2 className="text-xl font-semibold">这次准备做什么</h2><p className="text-sm text-slate-500">以下是本次项目草稿，修改不会覆盖原推荐评估。输入暂存在当前浏览器标签页。</p><fieldset disabled={locked} className="space-y-4"><Field label="项目名称"><input maxLength={300} className={inputClass} value={draft.title} onChange={e => setDraft({ ...draft, title: e.target.value })} /></Field><Field label="创作目标"><textarea rows={5} className={inputClass} value={draft.objective} onChange={e => setDraft({ ...draft, objective: e.target.value })} /></Field></fieldset><p className="text-sm">角色建议：{suggestedRoles.length ? `${suggestedRoles.join("、")}；进入项目后确认身份。` : "未记录角色建议；进入项目后确认身份。"}</p><p className="text-sm">形态建议：{assessment.recommended_modalities?.join("、") || "未记录"} · 渠道建议：{assessment.recommended_channels?.join("、") || "未记录"}</p><p className="text-xs text-slate-500">这些建议未批准，不会自动建立创作单元或绑定账号。</p><Button disabled={convert.isPending} onClick={() => navigateView("sources")}>继续阅读与选择资料 →</Button></section> : <>
      <section className={card}><h2 className="text-xl font-semibold">阅读与选择参考资料</h2><p className="text-sm text-slate-500">来源默认不选。勾选仅建立项目来源关系，事实与使用许可仍需分别确认。</p>{signals.length === 0 ? <EmptyState title="尚无参考资料" /> : signals.map(signal => <div key={signal.id} className="space-y-2">{eligible.some(source => source.id === signal.id) && <label className="flex items-center gap-2 text-sm"><input type="checkbox" disabled={locked} checked={selected.includes(signal.id)} onChange={e => setDraft({ ...draft, selected: e.target.checked ? [...selected, signal.id] : selected.filter(id => id !== signal.id) })} />作为项目来源</label>}<ReferencePreview signal={signal} /></div>)}</section>
      <form className={card} onSubmit={event => { event.preventDefault(); if (!locked && !stale) convert.mutate(); }}><h2 className="text-xl font-semibold">确认选题</h2><p className="font-medium">{draft.title.trim() || item.title}</p><p className="whitespace-pre-wrap text-sm text-slate-600">{draft.objective || "未填写项目目标"}</p><p className="text-sm">基于评估 v{draft.revision} · 已选择 {selected.length} 条项目来源。</p>{draft.selected.length !== selected.length && <p className="text-sm text-amber-800">部分之前选择的来源已不可用，将不传入项目。</p>}{selected.length === 0 && <p className="text-sm text-amber-800">本次将创建无来源绑定的项目，之后需补充资料并核对事实。</p>}<p className="text-xs text-slate-500">{["new", "watching"].includes(item.status) ? "确认后将机会标记为可转项目，再创建项目和初始任务书。" : "确认后创建项目和初始任务书。"}下一步进入角色创作流程确认内容与身份。</p>{stage && <p role="status" className="text-sm text-teal-800">{stage}</p>}{convert.isError && <ErrorBanner message={convert.error instanceof ApiError && convert.error.status === 409 ? "转换冲突：请刷新核对最新评估和已有项目关系。草稿输入已保留，不会自动重试。" : errorMessage(convert.error)} />}{createdProject ? <Link className="text-teal-800" to={taskLink(`/projects/${createdProject}`)}>打开已创建项目 →</Link> : <div className="flex flex-wrap gap-3"><Button variant="secondary" disabled={convert.isPending} onClick={() => navigateView("direction")}>返回调整方向</Button><Button type="submit" disabled={locked || stale}>{convert.isPending ? "创建中…" : "确认选题并创建项目"}</Button></div>}</form>
    </>}
  </div>;
}
