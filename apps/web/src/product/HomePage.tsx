import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api, ApiError, currentUser } from "../api";
import { Button, ErrorBanner, Spinner, StatusBadge } from "../components/ui";
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
  capabilities: { schedule: boolean; opportunity_analysis: boolean };
  generated_at: string;
  incomplete: boolean;
  section_errors: (string | { section?: string; code?: string; message?: string })[];
}
const box = "rounded-xl border border-slate-200 bg-white p-6";
const stages: Record<string, string> = { brief_needed: "待完善任务书", evidence_needed: "待建立事实边界", matrix_needed: "待添加内容单元", production: "生产中", attention_required: "需要处理风险", waiting_human: "等待人工", review_ready: "可进入审核" };
function timestamp(value: string | null | undefined) {
  if (!value) return 0;
  return Date.parse(/(?:Z|[+-]\d{2}:\d{2})$/i.test(value) ? value : `${value}Z`);
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
  return action ? <Link className="block text-sm font-medium text-indigo-700" to={action.href}>{action.label} →</Link> : null;
}

export function ProjectNextStageLink({ projectId, overview }: { projectId: number; overview: Pick<Overview, "nextAction" | "risks"> }) {
  const query = useQuery({ queryKey: ["home", currentUser()], queryFn: () => api.get<HomeData>("/home") });
  return <ProjectActionLink action={projectNextAction(projectId, overview, query.data?.recipe_stages || [], query.data?.decisions || [])} />;
}

export default function HomePage() {
  const query = useQuery({ queryKey: ["home", currentUser()], queryFn: () => api.get<HomeData>("/home") });
  if (query.isPending) return <Spinner label="读取今日工作台…" />;
  if (query.isError) return <div className="space-y-3 p-9"><ErrorBanner message={query.error instanceof Error ? query.error.message : "工作台读取失败"} /><Button onClick={() => void query.refetch()}>重试</Button></div>;
  const data = query.data;
  const errors = data.section_errors ?? [];
  // Missing core projections must never look like a successful empty queue.
  const incomplete = data.incomplete || errors.length > 0;
  const decisions = [...new Map(data.decisions.map((item) => [decisionKey(item), item])).values()].sort((a, b) => rank(a.code) - rank(b.code) || (a.project_id ?? 0) - (b.project_id ?? 0) || (a.unit_id ?? 0) - (b.unit_id ?? 0) || (a.learning_candidate_id ?? a.entity_id ?? 0) - (b.learning_candidate_id ?? b.entity_id ?? 0) || a.code.localeCompare(b.code));
  const opportunities = data.opportunities.filter((item) => ["new", "watching", "qualified"].includes(item.status) && (!item.relevant_until || timestamp(item.relevant_until) >= Date.now())).sort((a, b) => {
    const priorities = { high: 0, normal: 1, low: 2 }; const times = { high: 0, medium: 1, low: 2, timeless: 3 };
    return priorities[a.priority] - priorities[b.priority] || times[a.latest_assessment?.assessment.time_sensitivity ?? "timeless"] - times[b.latest_assessment?.assessment.time_sensitivity ?? "timeless"] || (a.relevant_until ? timestamp(a.relevant_until) : Infinity) - (b.relevant_until ? timestamp(b.relevant_until) : Infinity) || timestamp(b.updated_at) - timestamp(a.updated_at) || a.id - b.id;
  });
  const empty = (message: string) => <p className={`text-sm ${incomplete ? "text-rose-700" : "text-slate-500"}`}>{incomplete ? "投影不完整，暂不能确认本区是否为空。" : message}</p>;
  return <div className="mx-auto max-w-7xl space-y-6 px-6 py-9">
    <header className="flex items-start justify-between gap-3"><div><p className="text-xs font-semibold tracking-widest text-indigo-600">Home Workspace</p><h1 className="mt-2 text-3xl font-semibold">今日工作台</h1><p className="mt-2 text-sm text-slate-500">机会、项目和待处理事项，来自后端当前业务记录。</p><p className="mt-1 text-xs text-slate-400">生成时间：{data.generated_at || "未知"}</p></div><Button variant="secondary" onClick={() => void query.refetch()}>刷新</Button></header>
    {incomplete && <div role="alert"><ErrorBanner message={`工作台数据不完整，请重试。${errors.map((error) => typeof error === "string" ? error : `${error.section || error.code || "未知分区"}：${error.message || "读取失败"}`).join("；")}`} /></div>}
    <section className={box}><h2 className="mb-4 font-semibold">待我处理</h2>{decisions.length === 0 ? empty("暂无待处理事项。") : <ul className="space-y-3">{decisions.map((item) => <li key={decisionKey(item)}><Link className="flex flex-wrap justify-between gap-2 rounded-lg border border-slate-200 p-3 text-sm text-indigo-700" to={item.href}><span>{decisionLabel(item)}</span><span className="text-xs text-slate-500">{item.code === "learning_validation" ? `学习候选 #${item.learning_candidate_id ?? item.entity_id ?? "未知"}` : item.project_id != null ? `项目 #${item.project_id}${item.unit_id ? ` · 单元 #${item.unit_id}` : ""}` : "内容身份"} →</span></Link></li>)}</ul>}</section>
    <section className={box}><div className="mb-4 flex justify-between"><h2 className="font-semibold">今日内容机会</h2><Link className="text-sm text-indigo-700" to="/opportunities">全部机会 →</Link></div>{opportunities.length === 0 ? empty("暂无有效期内待判断的机会。") : <div className="grid gap-3 md:grid-cols-2">{opportunities.map((item) => <Link className="rounded-lg border border-slate-200 p-4" key={item.id} to={`/opportunities/${item.id}`}><h3 className="font-medium">{item.title}</h3><p className="mt-2 text-sm text-slate-600">{item.latest_assessment?.assessment.why_now || item.summary || "尚未评估"}</p><p className="mt-2 text-xs text-slate-500">{item.priority} · {item.signal_count} 条信号 · {item.latest_assessment ? `评估 v${item.latest_assessment.revision_no}` : "待人工评估"}</p></Link>)}</div>}</section>
    <section className={box}><h2 className="mb-4 font-semibold">进行中的内容项目</h2>{data.projects.length === 0 ? empty("暂无进行中的项目。") : <div className="grid gap-4 lg:grid-cols-2">{data.projects.map((project) => <article className="space-y-3 rounded-lg border border-slate-200 p-4 text-sm" key={project.id}><Link className="font-semibold text-indigo-700" to={`/projects/${project.id}`}>{project.title} →</Link><p>{stages[project.overview.stage] || project.overview.stage} · {project.overview.activeUnitCount} 个当前单元</p><p className="text-xs text-slate-500">文字 {project.overview.modalityCounts.text || 0} · 图文 {project.overview.modalityCounts.graphic || 0} · 视频 {project.overview.modalityCounts.video || 0}</p><div className="flex flex-wrap gap-2">{project.overview.risks.map((risk, index) => <StatusBadge key={`${risk.code}:${index}`} status={risk.code} />)}</div><ProjectActionLink action={projectNextAction(project.id, project.overview, data.recipe_stages || [], data.decisions)} />{project.origin?.opportunity_id && <Link className="block text-xs text-indigo-700" to={`/opportunities/${project.origin.opportunity_id}`}>来源机会 #{project.origin.opportunity_id} →</Link>}</article>)}</div>}</section>
    <section className={box}><h2 className="mb-4 font-semibold">内容身份提醒</h2>{data.identity_alerts.length === 0 ? empty("暂无内容身份提醒。") : <ul className="space-y-2">{data.identity_alerts.map((alert, index) => <li key={`${alert.project_id}:${alert.unit_id}:${alert.code}:${index}`}><Link className="text-sm text-indigo-700" to={alert.href || "/identities"}>{alert.label || "内容身份未就绪"} →</Link></li>)}</ul>}</section>
    <section className={box}>
      <h2 className="mb-4 font-semibold">最近项目活动</h2>
      {!Array.isArray(data.recent_activity) ? <ErrorBanner message="项目活动未返回，暂不能确认活动记录。" /> : data.recent_activity.length === 0 ? empty("暂无项目活动记录。") : <ul className="space-y-3">
        {data.recent_activity.slice(0, 20).map((event) => <li key={event.id} className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-slate-200 p-3 text-sm">
          <Link className="text-indigo-700" to={`/projects/${event.project_id}?tab=activity`}>项目 #{event.project_id} · {event.event_type} →</Link>
          <span className="text-xs text-slate-500">事件 #{event.id} · {event.created_at || "发生时间未知"}</span>
        </li>)}
      </ul>}
      <p className="mt-3 text-xs text-slate-500">最多展示 20 条已记录的项目事件；完整记录请进入项目活动页。</p>
    </section>
    <section className={box}><h2 className="mb-4 font-semibold">最近更新的项目</h2>{data.projects.length === 0 ? empty("暂无项目更新记录。") : <ul className="space-y-2">{[...data.projects].sort((a, b) => Date.parse(b.updated_at || "1970-01-01") - Date.parse(a.updated_at || "1970-01-01") || a.id - b.id).map((project) => <li className="flex justify-between gap-3 text-sm" key={project.id}><Link className="text-indigo-700" to={`/projects/${project.id}?tab=activity`}>{project.title} · 查看活动 →</Link><span className="text-xs text-slate-500">{project.updated_at || "更新时间未知"}</span></li>)}</ul>}<p className="mt-4 text-xs text-slate-500">{data.capabilities.schedule === false && data.upcoming.length === 0 ? "排期尚未实现；项目更新时间不代表计划发布时间。" : "排期契约尚未确认，暂不展示计划。"} {!data.capabilities.opportunity_analysis && "自动机会分析不可用，请使用人工评估。"}</p></section>
  </div>;
}

export function ProjectOriginLink({ projectId }: { projectId: number }) {
  const query = useQuery({ queryKey: ["project-origin", currentUser(), projectId], queryFn: () => api.get<Origin | null>(`/content-projects/${projectId}/origin`), retry: false });
  if (query.isPending) return <p className="px-6 pt-4 text-xs text-slate-500">读取项目来源…</p>;
  if (query.isError) return <div className="px-6 pt-4 text-xs text-slate-500">{query.error instanceof ApiError && query.error.status === 404 ? "项目来源接口暂不可用，来源状态未知。" : "项目来源读取失败，来源状态未知。"}<button className="ml-2 text-indigo-700" onClick={() => void query.refetch()}>重试</button></div>;
  if (!query.data) return null;
  return <Link className="block px-6 pt-4 text-sm text-indigo-700" to={`/opportunities/${query.data.opportunity_id}`}>来自内容机会 #{query.data.opportunity_id} · 查看原始评估与信号 →</Link>;
}
