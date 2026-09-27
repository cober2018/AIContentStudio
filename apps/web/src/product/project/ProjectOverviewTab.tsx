import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, ApiError } from "../../api";
import { ErrorBanner, Spinner } from "../../components/ui";
import type { Overview } from "./types";

const STAGES: Record<string, string> = { brief_needed: "待完成任务书", evidence_needed: "待建立事实边界", matrix_needed: "待添加内容单元", production: "生产中", attention_required: "需要处理风险", waiting_human: "等待人工", review_ready: "可进入审核" };
const STATE_NAMES: Record<string, string> = { identity_unready: "身份未就绪，请完善画像或显式重绑", blocked: "受阻", stale: "已过期", unknown: "待核对", failed: "执行失败", waiting_human: "等待人工", waiting_review: "待审核", ready: "就绪", approved: "已批准", delivery_ready: "待交付", delivered: "已回填" };
function stateLabel(code: string) { const state = STATE_NAMES[code] ? code : Object.keys(STATE_NAMES).find((item) => code.endsWith(item)); return state ? STATE_NAMES[state] : code; }

export function ProjectOverviewTab({ projectId }: { projectId: number }) {
  const [data, setData] = useState<Overview | null>(null);
  const [error, setError] = useState("");
  useEffect(() => { api.get<Overview>(`/content-projects/${projectId}/overview`).then(setData).catch((err) => setError(err instanceof ApiError ? err.message : "无法读取项目概况")); }, [projectId]);
  if (error) return <ErrorBanner message={error} />;
  if (!data) return <Spinner label="读取项目概况…" />;
  return <section className="rounded-xl border border-slate-200 bg-white p-6 space-y-5">
    <div><h2 className="font-semibold">项目概况</h2><p className="mt-2 text-sm text-slate-600">阶段：{STAGES[data.stage] || data.stage}</p></div>
    <div className="grid gap-3 sm:grid-cols-3 text-sm"><p>当前单元 {data.activeUnitCount} · 归档 {data.archivedUnitCount}</p><p>文字 {data.modalityCounts.text || 0} · 图文 {data.modalityCounts.graphic || 0} · 视频 {data.modalityCounts.video || 0}</p><p>身份：{data.personas.map((item) => `${item.name} ${item.unitCount}`).join("、") || "暂无"}</p></div>
    <p className="text-sm text-slate-600">任务书：{data.brief.ready ? `第 ${data.brief.revision} 版` : "未填写"} · 事实边界：{data.factBoundary.ready ? `第 ${data.factBoundary.revision} 版` : "未建立"}</p>
    {data.risks.length > 0 && <div><h3 className="text-sm font-medium text-rose-700">需要关注</h3><ul className="mt-1 list-disc pl-5 text-sm text-slate-600">{data.risks.map((risk, index) => <li key={`${risk.code}-${index}`}>{stateLabel(risk.code)}{risk.unit_id ? ` · 单元 #${risk.unit_id}` : ""}</li>)}</ul></div>}
    {data.pendingDecisions.length > 0 && <div><h3 className="text-sm font-medium text-sky-700">等待人工处理</h3><ul className="mt-1 list-disc pl-5 text-sm text-slate-600">{data.pendingDecisions.map((item, index) => <li key={`${item.code}-${index}`}>{stateLabel(item.code)}{item.unit_id ? ` · 单元 #${item.unit_id}` : ""}</li>)}</ul></div>}
    {data.review?.units.some((unit) => unit.current_candidate) && <div><h3 className="text-sm font-medium">候选与交付</h3><ul className="mt-2 space-y-1 text-sm">{data.review.units.filter((unit) => unit.current_candidate).map((unit) => <li key={unit.unit_id}><Link className="text-indigo-700 hover:underline" to={`/review?project=${projectId}&unit=${unit.unit_id}`}>{unit.title} · Candidate #{unit.current_candidate?.id} · {stateLabel(unit.summary)}</Link></li>)}</ul></div>}
    {data.nextAction && <Link className="text-sm font-medium text-indigo-700" to={data.nextAction.href}>{data.nextAction.label} →</Link>}
  </section>;
}
