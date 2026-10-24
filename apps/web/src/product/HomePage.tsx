import { useTaskLink, taskReturn } from "./taskNavigation";
import { useQuery } from "@tanstack/react-query";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { api, ApiError, currentUser } from "../api";
import { Button, ErrorBanner, Page, PageHeader, Spinner, Stat, Tabs } from "../components/ui";
import { discoveryLabel, type DiscoveryStatus } from "./DiscoveryPanel";
import type { Opportunity } from "./opportunityTypes";
import type { Overview } from "./project/types";

interface Decision { code: string; project_id: number | null; unit_id?: number | null; node_id?: string; learning_candidate_id?: number | null; creative_execution_id?: number | null; entity_kind?: string; entity_id?: number | null; href: string; label: string }
interface Origin { opportunity_id: number; assessment_revision_id?: number }
interface HomeProject { id: number; title: string; overview: Omit<Overview, "review">; origin?: Origin | null; updated_at: string | null }
interface RecentActivity { id: number; project_id: number; event_type: string; created_at: string | null }
interface HomeData {
  opportunities: Opportunity[];
  decisions: Decision[];
  recipe_stages?: Decision[];
  projects: HomeProject[];
  identity_alerts: Decision[];
  recent_activity: RecentActivity[];
  upcoming: unknown[];
  discovery_status?: DiscoveryStatus | null;
  capabilities: { schedule: boolean; opportunity_analysis: boolean; daily_discovery?: boolean };
  generated_at: string;
  incomplete: boolean;
  section_errors: (string | { section?: string; code?: string; message?: string })[];
}
const box = "card p-6 sm:p-7";
const textLink = "text-sm font-medium text-accent-600 hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4";
const stages: Record<string, string> = { brief_needed: "待完善任务书", evidence_needed: "待建立事实边界", matrix_needed: "待添加内容单元", production: "生产中", attention_required: "需要处理风险", waiting_human: "等待人工", review_ready: "可进入审核" };
function homeRiskLabel(code: string) {
  const labels: Record<string, string> = { master_incomplete: "主稿待完善", master_render_unready: "成片待核验" };
  if (labels[code]) return labels[code];
  if (/unknown|reconcil/.test(code)) return "结果待核对";
  if (/stale/.test(code)) return "资料版本需核对";
  if (/block|failed/.test(code)) return "任务受阻，需处理";
  if (/waiting_human|waiting_input/.test(code)) return "等待人工补充";
  if (/approval|waiting_review/.test(code)) return "等待审阅确认";
  if (/identity|authoriz/.test(code)) return "角色或账号需确认";
  if (/render/.test(code)) return "成片待核验";
  return "需核对状态";
}
export function readableTime(value: string | null | undefined) {
  const time = timestamp(value);
  if (!time) return "时间未知";
  const minutes = Math.round((Date.now() - time) / 60000);
  if (minutes >= 0 && minutes < 1) return "刚刚";
  if (minutes >= 0 && minutes < 60) return `${minutes} 分钟前`;
  if (minutes >= 0 && minutes < 24 * 60) return `${Math.round(minutes / 60)} 小时前`;
  return new Date(time).toLocaleString("zh-CN", { month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit", hour12: false });
}
function timestamp(value: string | null | undefined) {
  if (!value) return 0;
  return Date.parse(/(?:Z|[+-]\d{2}:\d{2})$/i.test(value) ? value : `${value}Z`);
}
function todayDiscoveryLabel(persona: DiscoveryStatus["personas"][number]) {
  const run = persona.today_run;
  const currentState = ["paused", "persona_paused", "waiting_collection"].includes(persona.status) ? discoveryLabel(persona.status) : "";
  let result = "今日无运行记录";
  if (run) result = !persona.business_date || run.business_date !== persona.business_date ? "今日运行日期未核实" : discoveryLabel(run.status);
  else if (persona.today_run === undefined) result = "今日运行状态未返回";
  return currentState ? `${currentState} · ${result}` : result;
}
function rank(code: string) {
  if (code === "recipe_stage") return 8;
  if (code === "learning_validation") return 7;
  if (/unknown|reconcil/.test(code)) return 0;
  if (/block|failed/.test(code)) return 1;
  if (/stale/.test(code)) return 2;
  if (/waiting_human|waiting_input/.test(code)) return 3;
  if (/approval|waiting_review/.test(code)) return 4;
  if (/authoriz|delivery_ready/.test(code)) return 5;
  return 6;
}
function decisionKey(item: Decision) {
  return `${item.code}:${item.project_id ?? "none"}:${item.unit_id ?? "none"}:${item.entity_kind ?? "business"}:${item.learning_candidate_id ?? item.entity_id ?? (item.project_id != null ? "project" : item.href)}`;
}
function decisionLabel(item: Decision) {
  if (item.creative_execution_id) return `${item.label} · 执行 #${item.creative_execution_id}`;
  if (item.node_id) return item.label;
  if (/unknown|reconcil/.test(item.code)) return item.label || "结果未知 · 需要核对";
  if (/block/.test(item.code)) return "受阻 · 需要解决阻断";
  if (/stale/.test(item.code)) return "已过期 · 需要重新确认";
  if (/identity_unready/.test(item.code)) return "内容身份未就绪";
  return item.label || item.code;
}

function projectNextAction(projectId: number, overview: Pick<Overview, "nextAction" | "risks">, recipeStages: Decision[], decisions: Decision[] = []) {
  const next = overview.nextAction;
  const stage = recipeStages.find(item => item.project_id === projectId);
  if (next && /unknown|reconcil/.test(next.code)) return next;
  const uncertain = decisions.find(item => item.project_id === projectId && /unknown|reconcil/.test(item.code));
  if (uncertain) return uncertain;
  if (!stage) return next;
  if (overview.risks.some(risk => /unknown|reconcil/.test(risk.code)) && stage.code !== "unknown") return next;
  return stage.code === "unknown" || !next || ["production.continue", "production.complete_human", "production.resolve_risk"].includes(next.code) ? stage : next;
}

function ProjectActionLink({ action }: { action: { href: string; label: string } | null }) {
  const taskLink = useTaskLink();
  return action ? <Link className="block text-sm font-medium text-indigo-700" to={taskLink(action.href)}>{action.label} →</Link> : null;
}

export function ProjectNextStageLink({ projectId, overview }: { projectId: number; overview: Pick<Overview, "nextAction" | "risks"> }) {
  const query = useQuery({ queryKey: ["home", currentUser()], queryFn: () => api.get<HomeData>("/home") });
  return <ProjectActionLink action={projectNextAction(projectId, overview, query.data?.recipe_stages || [], query.data?.decisions || [])} />;
}

export default function HomePage() {
  const taskLink = useTaskLink();
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();
  const personaFilter = params.get("persona_id") || "";
  const view = params.get("view") || "today";
  const views: Record<string, string> = { today: "今日工作台", decisions: "全部待处理", projects: "继续创作", opportunities: "内容机会", activity: "最近项目活动", identities: "内容身份提醒" };
  const homeHref = (nextView: string) => {
    const next = new URLSearchParams(params);
    if (nextView === "today") next.delete("view"); else next.set("view", nextView);
    return `/home${next.size ? `?${next}` : ""}`;
  };
  const query = useQuery({ queryKey: ["home", currentUser()], queryFn: () => api.get<HomeData>("/home") });
  if (query.isPending) return <Spinner label="读取今日工作台…" />;
  if (query.isError) return <div className="space-y-3 p-9"><ErrorBanner message={query.error instanceof Error ? query.error.message : "工作台读取失败"} /><Button onClick={() => void query.refetch()}>重试</Button></div>;
  const data = query.data;
  const errors = data.section_errors ?? [];
  const missing = ["decisions", "projects", "opportunities", "identity_alerts", "recent_activity"].filter(key => !Array.isArray(data[key as keyof HomeData]));
  const incomplete = data.incomplete || errors.length > 0 || missing.length > 0;
  const decisions = [...new Map((data.decisions || []).map((item) => [decisionKey(item), item])).values()].sort((a, b) => rank(a.code) - rank(b.code) || (a.project_id ?? 0) - (b.project_id ?? 0) || (a.unit_id ?? 0) - (b.unit_id ?? 0) || (a.learning_candidate_id ?? a.entity_id ?? 0) - (b.learning_candidate_id ?? b.entity_id ?? 0) || a.code.localeCompare(b.code));
  const projects = [...(data.projects || [])].sort((a, b) => timestamp(b.updated_at) - timestamp(a.updated_at) || a.id - b.id);
  const opportunities = (data.opportunities || []).filter((item) => (!personaFilter || String(item.persona_id) === personaFilter) && ["new", "watching", "qualified"].includes(item.status) && (!item.relevant_until || timestamp(item.relevant_until) >= Date.now())).sort((a, b) => {
    const priorities = { high: 0, normal: 1, low: 2 }; const times = { high: 0, medium: 1, low: 2, timeless: 3 };
    return priorities[a.priority] - priorities[b.priority] || times[a.latest_assessment?.assessment.time_sensitivity ?? "timeless"] - times[b.latest_assessment?.assessment.time_sensitivity ?? "timeless"] || (a.relevant_until ? timestamp(a.relevant_until) : Infinity) - (b.relevant_until ? timestamp(b.relevant_until) : Infinity) || timestamp(b.updated_at) - timestamp(a.updated_at) || a.id - b.id;
  });
  const identityAlerts = data.identity_alerts || [];
  const hiddenRiskProjects = projects.slice(4).filter(project => project.overview.risks.length > 0);
  const visiblePersonas = (data.discovery_status?.personas || []).filter(p => !personaFilter || String(p.persona_id) === personaFilter);
  const personas = data.discovery_status?.personas || [];
  const roleOptions = [...new Map([...personas.map(p => [String(p.persona_id), p.name] as const), ...(data.opportunities || []).filter(item => item.persona_id != null).map(item => [String(item.persona_id), personas.find(p => p.persona_id === item.persona_id)?.name || `角色 #${item.persona_id}`] as const), ...(personaFilter ? [[personaFilter, personas.find(p => String(p.persona_id) === personaFilter)?.name || `角色 #${personaFilter}`] as const] : [])]).entries()];
  const preview = <T,>(items: T[]) => view === "today" ? items.slice(0, 4) : items;
  const empty = (message: string) => <p className={`text-sm ${incomplete ? "text-rose-700" : "text-slate-500"}`}>{incomplete ? "投影不完整，暂不能确认本区是否为空。" : message}</p>;
  const projectTitle = (id: number | null | undefined) => projects.find(project => project.id === id)?.title;
  const sectionHeading = (title: string, count: number, nextView: string) => <div className="mb-5 flex flex-wrap items-center justify-between gap-3"><h2 className="font-serif text-[22px] font-semibold text-ink-900">{title} <span className="ml-2 font-sans text-sm font-normal text-ink-500">{missing.includes(nextView === "identities" ? "identity_alerts" : nextView) ? "数量未知" : `${count} 项`}</span></h2>{view === "today" && <Link className={textLink} to={homeHref(nextView)}>查看全部 →</Link>}</div>;
  const pendingSummary = decisions.filter(item => rank(item.code) <= 2);
  const today = new Date().toLocaleDateString("zh-CN", { month: "long", day: "numeric", weekday: "long" });
  return <Page>
    {view !== "today" && <Link to={homeHref("today")} className="-mb-2 inline-block text-[13px] text-ink-500 hover:text-ink-900">← 今日工作台</Link>}
    <PageHeader eyebrow={view === "today" ? today : "今日工作台"} title={views[view] || "页面未找到"} lead={view === "today" ? "先处理需要你决定的事，再继续手中的创作。" : "查看当前业务记录，进入对应任务继续处理。"}
      actions={<><span className="text-[12.5px] text-ink-500">更新于 {readableTime(data.generated_at)}</span><Button variant="secondary" size="sm" onClick={() => void query.refetch()}>刷新</Button></>}>
      <Tabs label="工作台记录" value={view} onChange={key => navigate(homeHref(key))} items={(["today", "decisions", "projects", "opportunities", "activity", "identities"] as const).map(key => [key, `${views[key]}${key === "identities" ? ` ${missing.includes("identity_alerts") ? "?" : identityAlerts.length}` : ""}`] as const)} />
    </PageHeader>
    {incomplete && <div role="alert"><ErrorBanner message={`工作台数据不完整，请重试。${errors.map(error => typeof error === "string" ? error : `${error.section || error.code || "未知分区"}：${error.message || "读取失败"}`).join("；")}${missing.length ? ` 未返回：${missing.map(key => ({ decisions: "待处理", projects: "项目", opportunities: "机会", identity_alerts: "身份提醒", recent_activity: "活动记录" })[key]).join("、")}` : ""}`} /></div>}
    {view === "today" && <section aria-label="今日概况" className="card grid grid-cols-2 gap-x-6 gap-y-7 p-6 sm:p-7 lg:grid-cols-4">
      <Stat label="待我处理" value={decisions.length} hint={pendingSummary.length ? `${pendingSummary.length} 项需要先处理` : "没有紧急事项"} />
      <Stat label="进行中项目" value={projects.length} hint={hiddenRiskProjects.length || projects.some(project => project.overview.risks.length) ? `${projects.filter(project => project.overview.risks.length).length} 个有风险提醒` : "状态正常"} />
      <Stat label="待判断机会" value={opportunities.length} hint="有效期内" />
      <Stat label="身份提醒" value={missing.includes("identity_alerts") ? "—" : identityAlerts.length} hint="角色与账号" />
    </section>}
    {!views[view] && <ErrorBanner message="此工作台页面不存在，请返回今日工作台。" />}
    {(view === "today" || view === "decisions") && <section className={box}>
      {sectionHeading("待我处理", decisions.length, "decisions")}
      {pendingSummary.length > 0 && <p className="mb-4 text-sm text-amber-800">{pendingSummary.length} 项结果待核对、受阻或已过期，需要先处理。{view === "today" && decisions.length > 4 ? "其余事项可在全部待处理中查看。" : ""}</p>}
      {decisions.length === 0 ? empty("暂无待处理事项，可以继续创作。") : <ul className="space-y-3">{preview(decisions).map((item, index) => <li key={decisionKey(item)} className={`rounded-[14px] border p-4 transition-colors ${index === 0 ? "border-accent-200 bg-accent-50/70 sm:p-5" : "border-ink-200/90 hover:border-ink-300"}`}><div className="flex flex-wrap items-center justify-between gap-3"><div>{index === 0 && <p className="mb-2 text-xs font-medium text-accent-600">下一步</p>}<h3 className="font-medium">{decisionLabel(item)}</h3><p className="mt-2 text-[12.5px] text-ink-500">{item.code === "learning_validation" ? `学习候选 #${item.learning_candidate_id ?? item.entity_id ?? "未知"}` : item.project_id != null ? `${projectTitle(item.project_id) || `项目 #${item.project_id}`}${item.unit_id ? ` · 单元 #${item.unit_id}` : ""}` : "内容身份"}</p></div><Link className={index === 0 ? "inline-flex h-9 items-center rounded-pill bg-ink-900 px-4 text-[13.5px] font-medium text-paper hover:bg-ink-800" : textLink} to={taskLink(item.href)}>进入处理 →</Link></div></li>)}</ul>}
    </section>}
    {(view === "today" || view === "projects") && <section className={box}>
      {sectionHeading("继续创作", projects.length, "projects")}
      {projects.length === 0 ? empty("暂无进行中的项目。") : <div className="grid gap-4 lg:grid-cols-2">{preview(projects).map(project => <article className="space-y-3 rounded-[14px] border border-ink-200/90 p-5 text-sm transition-colors hover:border-ink-300" key={project.id}><Link className="block font-serif text-[18px] font-semibold leading-snug text-ink-900 hover:text-accent-600" to={taskLink(`/projects/${project.id}`)}>{project.title}</Link><p>{stages[project.overview.stage] || project.overview.stage} · {project.overview.activeUnitCount} 个当前单元</p><p className="text-xs text-slate-500">文字 {project.overview.modalityCounts.text || 0} · 图文 {project.overview.modalityCounts.graphic || 0} · 视频 {project.overview.modalityCounts.video || 0}</p><div className="flex flex-wrap gap-2">{[...new Set(project.overview.risks.map(risk => risk.code))].map(code => <span key={code} className="rounded-md bg-amber-50 px-2 py-1 text-xs text-amber-800">{homeRiskLabel(code)}</span>)}</div><ProjectActionLink action={projectNextAction(project.id, project.overview, data.recipe_stages || [], data.decisions || [])} />{project.origin?.opportunity_id && <Link className={textLink} to={taskLink(`/opportunities/${project.origin.opportunity_id}`)}>来源机会 #{project.origin.opportunity_id} →</Link>}<p className="text-xs text-slate-500">更新于 {readableTime(project.updated_at)}</p></article>)}</div>}
      {view === "today" && projects.length > 4 && <p className="mt-4 text-sm text-slate-500">另有 {projects.length - 4} 个项目{hiddenRiskProjects.length > 0 ? `，其中 ${hiddenRiskProjects.length} 个带有风险提醒` : ""}，进入全部创作查看状态与风险。</p>}
    </section>}
    {(view === "today" || view === "opportunities") && <section className={box}>
      {sectionHeading("内容机会", opportunities.length, "opportunities")}
      <div className="mb-5 space-y-3"><div className="flex flex-wrap items-center justify-between gap-3"><label className="flex flex-wrap items-center gap-3 text-sm">按角色查看<select aria-label="按角色筛选今日机会" className="rounded-lg border border-ink-300 bg-white px-3 py-2" value={personaFilter} onChange={event => { const next = new URLSearchParams(params); if (event.target.value) next.set("persona_id", event.target.value); else next.delete("persona_id"); setParams(next); }}><option value="">全部角色</option>{roleOptions.map(([id, name]) => <option key={id} value={id}>{name}</option>)}</select></label><Link className={textLink} to={taskLink(`/opportunities${personaFilter ? `?persona_id=${encodeURIComponent(personaFilter)}` : ""}`)}>进入机会工作台 →</Link></div><div className="flex flex-wrap gap-x-5 gap-y-2 text-xs text-slate-500">{data.discovery_status ? visiblePersonas.length ? visiblePersonas.map(p => <p key={p.persona_id}>{p.name} · 今日选题：{todayDiscoveryLabel(p)}</p>) : <p>角色每日选题状态未记录。</p> : <p>角色每日选题状态未返回，当前状态未知。</p>}</div></div>
      {opportunities.length === 0 ? empty("暂无有效期内待判断的机会。") : <div className="grid gap-3 md:grid-cols-2">{preview(opportunities).map(item => <Link className="rounded-xl border border-ink-200 p-4 hover:border-accent-300 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4" key={item.id} to={taskLink(`/opportunities/${item.id}`)}><p className="text-xs text-accent-600">{item.persona_id ? personas.find(p => p.persona_id === item.persona_id)?.name || `角色 #${item.persona_id}` : "人工机会"} · {{ high: "优先关注", normal: "常规", low: "低优先" }[item.priority]}</p><h3 className="mt-2 font-medium">{item.title}</h3><p className="mt-2 line-clamp-3 text-sm text-slate-600"><span className="font-medium text-accent-600">建议方向：</span>{item.latest_assessment?.assessment.suggested_angle || item.latest_assessment?.assessment.brand_relevance || item.summary || "尚无方向建议"}</p><p className="mt-3 text-xs text-slate-500">{item.signal_count} 条参考资料 · {item.latest_assessment ? `已有评估 v${item.latest_assessment.revision_no}` : "尚无评估记录"}</p></Link>)}</div>}
    </section>}
    {view === "identities" && <section className={box}>{sectionHeading("内容身份提醒", identityAlerts.length, "identities")}{identityAlerts.length === 0 ? empty("暂无内容身份提醒。") : <ul className="space-y-3">{identityAlerts.map((alert, index) => <li key={`${decisionKey(alert)}:${index}`}><Link className={`block rounded-xl border border-ink-200 p-4 ${textLink}`} to={alert.href || "/identities"}>{alert.label || "内容身份未就绪"} →</Link></li>)}</ul>}<Link className={`mt-5 inline-block ${textLink}`} to="/identities">管理角色与账号 →</Link></section>}
    {view === "activity" && <section className={box}><h2 className="mb-5 text-lg font-semibold">最近项目活动</h2>{!Array.isArray(data.recent_activity) ? <ErrorBanner message="项目活动未返回，暂不能确认活动记录。" /> : data.recent_activity.length === 0 ? empty("暂无项目活动记录。") : <ul className="space-y-3">{data.recent_activity.map(event => <li key={event.id} className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-ink-200 p-4 text-sm"><Link className={textLink} to={taskLink(`/projects/${event.project_id}?tab=activity`)}>{projectTitle(event.project_id) || `项目 #${event.project_id}`} · {event.event_type} →</Link><span className="text-xs text-slate-500">{readableTime(event.created_at)}</span></li>)}</ul>}<p className="mt-4 text-xs text-slate-500">这里展示工作台返回的已记录事件，完整记录请进入对应项目活动页。</p><p className="mt-2 text-xs text-slate-500">{data.capabilities?.schedule === false && data.upcoming?.length === 0 ? "排期尚未实现；项目更新时间不代表计划发布时间。" : "排期契约尚未确认，暂不展示计划。"}</p></section>}
  </Page>;
}

export function ProjectOriginLink({ projectId }: { projectId: number }) {
  const [params] = useSearchParams();
  const query = useQuery({ queryKey: ["project-origin", currentUser(), projectId], queryFn: () => api.get<Origin | null>(`/content-projects/${projectId}/origin`), retry: false });
  if (query.isPending) return <p className="px-6 pt-4 text-xs text-slate-500">读取项目来源…</p>;
  if (query.isError) return <div className="px-6 pt-4 text-xs text-slate-500">{query.error instanceof ApiError && query.error.status === 404 ? "项目来源接口暂不可用，来源状态未知。" : "项目来源读取失败，来源状态未知。"}<button className="ml-2 text-indigo-700" onClick={() => void query.refetch()}>重试</button></div>;
  if (!query.data) return null;
  const origin = `/opportunities/${query.data.opportunity_id}`;
  const previous = taskReturn(params.get("return_to"));
  return <Link className="block px-6 pt-4 text-sm text-indigo-700" to={previous && new URL(previous, "https://studio.local").pathname === origin ? previous : origin}>来自内容机会 #{query.data.opportunity_id} · 查看原始评估与信号 →</Link>;
}
