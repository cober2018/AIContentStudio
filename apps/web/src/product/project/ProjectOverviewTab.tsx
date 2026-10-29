import { useTaskLink } from "../taskNavigation";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, ApiError } from "../../api";
import { ErrorBanner, Spinner } from "../../components/ui";
import { ProjectNextStageLink } from "../HomePage";
import type { Unit } from "./projectTypes";
import type { Overview } from "./types";

const STAGES: Record<string, string> = { brief_needed: "待完成任务书", evidence_needed: "待建立事实边界", matrix_needed: "待添加作品", production: "生产中", attention_required: "需要处理风险", waiting_human: "等待人工", review_ready: "可进入审核" };
const STATE_NAMES: Record<string, string> = { identity_unready: "身份未就绪，请完善画像或显式重绑", blocked: "受阻", stale: "已过期", unknown: "待核对", failed: "执行失败", waiting_human: "等待人工", waiting_review: "待审核", ready: "就绪", approved: "已批准", delivery_ready: "待交付", delivered: "已回填" };
const MASTER_STATES: Record<string, string> = { master_incomplete: "原稿或必要检查尚未完成", master_stale: "原稿依据已变化，需要核对", master_check_blocked: "原稿检查发现问题", master_render_unready: "成品尚未完成渲染验证" };
function stateLabel(code: string) { if (MASTER_STATES[code]) return MASTER_STATES[code]; const state = STATE_NAMES[code] ? code : Object.keys(STATE_NAMES).find((item) => code.endsWith(item)); return state ? STATE_NAMES[state] : code; }

export function ProjectOverviewTab({ projectId, productUnitCount = 0, productOnly = false, units = [], search = "" }: { projectId: number; productUnitCount?: number; productOnly?: boolean; units?: Unit[]; search?: string }) {
  const taskLink = useTaskLink();
  const [data, setData] = useState<Overview | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    setData(null); setError("");
    api.get<Overview>(`/content-projects/${projectId}/overview`).then(value => { if (active) setData(value); }).catch(err => { if (active) setError(err instanceof ApiError ? err.message : "无法读取项目概况"); });
    return () => { active = false; };
  }, [projectId]);
  const activeUnits = units.filter(unit => unit.lifecycle !== "deleted" && unit.lifecycle !== "archived" && unit.status !== "archived");
  const projectTab = (tab: string) => { const params = new URLSearchParams(search); params.set("tab", tab); return `/projects/${projectId}?${params}`; };
  if (error) return <ErrorBanner message={error} />;
  if (!data) return <Spinner label="读取项目概况…" />;
  return <section className="rounded-xl border border-slate-200 bg-white p-6 space-y-5">
    <div><h2 className="font-semibold">下一步做什么</h2><p className="mt-2 text-sm text-slate-600">阶段：{STAGES[data.stage] || data.stage}</p></div>
    <ProjectNextStageLink projectId={projectId} overview={data} />
    {activeUnits.length > 0 ? <div className="space-y-3"><h3 className="text-sm font-medium">继续已有作品</h3>{activeUnits.slice(0, 3).map(unit => <Link key={unit.id} to={taskLink(`/projects/${projectId}/units/${unit.id}/production`)} className="group flex flex-wrap items-center justify-between gap-3 rounded-[14px] border border-ink-200/90 px-4 py-3.5 transition-colors hover:border-ink-400"><span className="flex min-w-0 items-center gap-3"><span className="shrink-0 rounded-pill bg-ink-100 px-2 py-0.5 text-[11.5px] text-ink-600">{({ text: "文字", graphic: "图文", video: "视频", audio: "音频" } as Record<string, string>)[unit.modality] || unit.modality}</span><span className="min-w-0 truncate text-[14.5px] text-ink-900">{unit.title}</span></span><span className="text-[13px] font-medium text-accent-600 transition-transform group-hover:translate-x-0.5">继续创作 →</span></Link>)}{activeUnits.length > 3 && <Link className="text-sm text-indigo-700 underline" to={projectTab("matrix")}>查看全部 {activeUnits.length} 个作品</Link>}</div> : <div className="rounded-lg bg-slate-50 p-4 text-sm text-slate-600"><p>尚无作品。先确认任务书与来源，再到作品页创建。</p><div className="mt-3 flex flex-wrap gap-4"><Link className="text-indigo-700 underline" to={projectTab("brief")}>核对任务书</Link><Link className="text-indigo-700 underline" to={projectTab("evidence")}>查看来源与证据</Link><Link className="text-indigo-700 underline" to={projectTab("matrix")}>进入作品页</Link></div></div>}
    <details className="border-t pt-4"><summary className="cursor-pointer text-sm font-medium">项目概况与依据</summary><div className="mt-4 space-y-4">
    <div className="grid gap-3 sm:grid-cols-3 text-sm"><p>当前单元 {data.activeUnitCount} · 归档 {data.archivedUnitCount}</p><p>文字 {data.modalityCounts.text || 0} · 图文 {data.modalityCounts.graphic || 0} · 视频 {data.modalityCounts.video || 0}</p><p>{productUnitCount > 0 || productOnly ? `商品作品 ${productUnitCount}` : ""}{!productOnly && <>{productUnitCount > 0 ? " · " : ""}身份：{data.personas.filter(item => item.id != null).map((item) => `${item.name} ${item.unitCount}`).join("、") || "暂无"}</>}</p></div>
    <p className="text-sm text-slate-600">任务书：{data.brief.ready ? `第 ${data.brief.revision} 版` : "未填写"} · 事实边界：{data.factBoundary.ready ? `第 ${data.factBoundary.revision} 版` : "未建立"}</p>
    </div></details>
    {data.risks.length > 0 && <div><h3 className="text-sm font-medium text-rose-700">需要关注</h3><ul className="mt-1 list-disc pl-5 text-sm text-slate-600">{data.risks.map((risk, index) => <li key={`${risk.code}-${index}`}>{stateLabel(risk.code)}{risk.unit_id ? ` · ${activeUnits.find(unit => unit.id === risk.unit_id)?.title || `单元 #${risk.unit_id}`}` : ""}</li>)}</ul></div>}
    {data.pendingDecisions.length > 0 && <div><h3 className="text-sm font-medium text-sky-700">等待人工处理</h3><ul className="mt-1 list-disc pl-5 text-sm text-slate-600">{data.pendingDecisions.map((item, index) => <li key={`${item.code}-${index}`}>{stateLabel(item.code)}{item.unit_id ? ` · ${activeUnits.find(unit => unit.id === item.unit_id)?.title || `单元 #${item.unit_id}`}` : ""}</li>)}</ul></div>}
    {data.review?.units.some((unit) => unit.current_candidate) && <div><h3 className="text-sm font-medium">候选与交付</h3><ul className="mt-2 space-y-1 text-sm">{data.review.units.filter((unit) => unit.current_candidate).map((unit) => <li key={unit.unit_id}><Link className="text-indigo-700 hover:underline" to={`/review?project=${projectId}&unit=${unit.unit_id}`}>{unit.title} · Candidate #{unit.current_candidate?.id} · {stateLabel(unit.summary)}</Link></li>)}</ul></div>}
  </section>;
}
