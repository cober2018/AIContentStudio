import { useEffect, useState } from "react";
import { useQuery, useQueries } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api, currentUser } from "../api";
import { Button, EmptyState, ErrorBanner, Field, Spinner, StatusBadge, inputClass } from "../components/ui";
import type { Project } from "./project/projectTypes";

type NativeTask = { task_id: string; project_id: number | null; state: string; capability: string; model_id: string; reason: string | null };
type ExternalTask = { id: number; project_id: number; content_unit_id: number; state: string; safe_reason: string | null; executor_kind: string; executor_key: string; revision_no: number };
const modalityNames: Record<string, string> = { text: "文字", graphic: "图文", video: "视频" };
const capabilityNames: Record<string, string> = { image_generation: "生图", video_generation: "生视频", tts: "语音生成", asr: "语音识别" };
const priority: Record<string, number> = { unknown: 0, reconciliation_needed: 0, blocked: 1, failed: 1, stale: 2, waiting_human: 3, result_ready: 3 };
const pageSize = 20;

export default function ProductionQueuePage({ projectId }: { projectId?: number }) {
  const [q, setQ] = useState("");
  const [modality, setModality] = useState("");
  const [offset, setOffset] = useState(0);
  const [showArchived, setShowArchived] = useState(false);
  const projects = useQuery({ queryKey: ["production-queue", currentUser(), projectId ?? "all"], queryFn: async () => projectId ? [await api.get<Project>(`/content-projects/${projectId}`)] : api.get<Project[]>("/content-projects"), retry: false });
  const tasks = useQuery({ queryKey: ["generation-tasks", currentUser()], queryFn: () => api.get<NativeTask[]>("/generation-tasks"), retry: false });
  // 搜索词防抖：避免每敲一个字符就重算可见单元并触发外部执行重拉
  const [debouncedQ, setDebouncedQ] = useState("");
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQ(q), 300);
    return () => clearTimeout(timer);
  }, [q]);
  const rows = (projects.data ?? []).flatMap(project => project.units.map(unit => ({ project, unit })))
    .filter(({ project, unit }) => (showArchived || (project.status !== "archived" && unit.status !== "archived")) && (!modality || unit.modality === modality) && `${project.title} ${unit.title}`.toLowerCase().includes(debouncedQ.toLowerCase()))
    .sort((a, b) => (priority[a.unit.status] ?? 4) - (priority[b.unit.status] ?? 4) || b.project.id - a.project.id || a.unit.id - b.unit.id);
  const nativeTasks = (tasks.data ?? []).filter(task => !projectId || task.project_id === projectId)
    .sort((a, b) => (priority[a.state] ?? 4) - (priority[b.state] ?? 4));
  const visible = rows.slice(offset, offset + pageSize);
  // 每单元独立缓存：翻页/筛选命中缓存，只拉新增单元，替代整页拼接键的全量重发
  const externalQueries = useQueries({
    queries: visible.map(({ project, unit }) => ({
      queryKey: ["creative-executions", currentUser(), project.id, unit.id],
      queryFn: () => api.get<{ items: ExternalTask[] }>(`/content-projects/${project.id}/units/${unit.id}/creative-executions?limit=20`),
      retry: false,
      staleTime: 30_000,
    })),
  });
  const external = {
    isPending: externalQueries.length > 0 && externalQueries.some(query => query.isPending),
    done: externalQueries.length === 0 || externalQueries.every(query => !query.isPending),
    items: externalQueries.flatMap(query => query.data?.items ?? []).sort((a, b) => (priority[a.state] ?? 4) - (priority[b.state] ?? 4) || b.id - a.id),
    errors: externalQueries.flatMap((query, index) => {
      if (!query.error) return [];
      const { project, unit } = visible[index];
      return [`项目 #${project.id} / 内容单元 #${unit.id}：${query.error instanceof Error ? query.error.message : "读取失败"}`];
    }),
    refetch: () => { externalQueries.forEach(query => void query.refetch()); },
  };
  return <section className={projectId ? "space-y-6" : "mx-auto max-w-7xl space-y-6 px-6 py-9"}>
    <header><p className="text-xs font-semibold tracking-widest text-indigo-600">Creation & Execution</p><h1 className="mt-2 text-3xl font-semibold">创作与执行</h1><p className="mt-2 text-sm text-slate-500">从内容单元进入创作；生成任务读取既有记录。查看队列不会生成、重发或接受结果。</p></header>
    <div className="flex flex-wrap items-end gap-3 rounded-xl border bg-white p-4"><Field label="查找项目或内容"><input className={inputClass} value={q} onChange={event => { setQ(event.target.value); setOffset(0); }} /></Field><Field label="内容形态"><select className={inputClass} value={modality} onChange={event => { setModality(event.target.value); setOffset(0); }}><option value="">全部</option>{Object.entries(modalityNames).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></Field><label className="text-sm"><input type="checkbox" checked={showArchived} onChange={event => { setShowArchived(event.target.checked); setOffset(0); }} /> 包含归档历史</label><Button variant="secondary" onClick={() => { void projects.refetch(); void tasks.refetch(); void external.refetch(); }}>刷新</Button><Link to="/projects" className="text-sm text-indigo-700 underline">从想法创建项目</Link></div>
    <section className="space-y-3 rounded-xl border bg-white p-5"><h2 className="font-semibold">内容创作</h2>{projects.isPending && <Spinner label="读取项目与内容单元…" />}{projects.isError && <ErrorBanner message={`项目读取失败，不能当作没有待办。${projects.error.message}`} />}{projects.isSuccess && <>{visible.map(({ project, unit }) => <article key={`${project.id}:${unit.id}`} className="flex flex-wrap items-center justify-between gap-3 rounded-lg border p-4"><div><p className="text-xs text-slate-500">{project.title} · 项目 #{project.id}</p><h3 className="mt-1 font-medium">{unit.title}</h3><p className="mt-1 text-xs text-slate-500">{modalityNames[unit.modality] ?? unit.modality} · {unit.channel_id ?? "渠道未选"} · 内容单元 #{unit.id}{project.status === "archived" || unit.status === "archived" ? " · 归档只读" : ""}</p></div><div className="flex items-center gap-3"><StatusBadge status={unit.status} /><Link className="text-sm text-indigo-700 underline" to={`/projects/${project.id}/units/${unit.id}/production`}>{project.status === "archived" || unit.status === "archived" ? "查看历史" : "继续创作"}</Link></div></article>)}{!rows.length && <EmptyState title="当前筛选下没有内容单元" hint="到内容项目创建单元，或查看归档历史。" />}<div className="flex items-center gap-3 text-sm"><span>共 {rows.length} 条 · 每页 {pageSize} 条</span><Button variant="secondary" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - pageSize))}>上一页</Button><Button variant="secondary" disabled={offset + pageSize >= rows.length} onClick={() => setOffset(offset + pageSize)}>下一页</Button></div></>}</section>
    <section className="space-y-3 rounded-xl border bg-white p-5"><h2 className="font-semibold">原生生成任务</h2><p className="text-xs text-slate-500">读取当前用户最近最多 50 条记录{projectId ? "中的本项目任务" : ""}，并非全部历史。unknown 需核对原任务，不会自动重发。</p>{tasks.isPending && <Spinner label="读取原生任务…" />}{tasks.isError && <ErrorBanner message={`任务读取失败，不能推断为零任务。${tasks.error.message}`} />}{tasks.isSuccess && <>{nativeTasks.map(task => <article key={task.task_id} className="flex flex-wrap items-center justify-between gap-3 rounded-lg border p-3"><div><p className="text-sm font-medium">{capabilityNames[task.capability] ?? task.capability} · {task.model_id}</p><p className="mt-1 break-all text-xs text-slate-500">{task.task_id}{task.reason ? ` · ${task.reason}` : ""}</p></div><div className="flex items-center gap-3"><StatusBadge status={task.state} /><Link className="text-sm text-indigo-700 underline" to={`/assets?tab=material&task=${encodeURIComponent(task.task_id)}`}>查看原任务与结果</Link>{task.project_id && <Link className="text-sm text-slate-600 underline" to={`/projects/${task.project_id}?tab=execution`}>所属项目</Link>}</div></article>)}{!nativeTasks.length && <EmptyState title="本次读取范围内没有生成任务" />}</>}</section>
    <section className="space-y-3 rounded-xl border bg-white p-5"><h2 className="font-semibold">外部创意执行</h2><p className="text-xs text-slate-500">仅汇总本页最多 {pageSize} 个内容单元、每单元最近 20 条真实执行记录。Unknown 必须核对原执行，不会自动创建或重发任务。</p>{visible.length > 0 && external.isPending && <Spinner label="读取外部执行…" />}{external.errors.map(message => <ErrorBanner key={message} message={message} />)}{external.items.map(task => <article key={task.id} className="flex flex-wrap items-center justify-between gap-3 rounded-lg border p-3"><div><p className="text-sm font-medium">执行 #{task.id} · {task.executor_kind} / {task.executor_key}</p><p className="mt-1 text-xs text-slate-500">项目 #{task.project_id} / 内容单元 #{task.content_unit_id} · 修订 {task.revision_no}{task.safe_reason ? ` · ${task.safe_reason}` : ""}</p></div><div className="flex items-center gap-3"><StatusBadge status={task.state} /><Link className="text-sm text-indigo-700 underline" to={`/projects/${task.project_id}/units/${task.content_unit_id}/production?panel=execution&execution=${task.id}`}>查看执行与成果</Link></div></article>)}{(!visible.length || external.done && !external.items.length && !external.errors.length) && <EmptyState title="当前读取范围内没有外部执行" hint="在内容工作台保存 Master 后，可创建执行包；本队列不自动执行。" />}</section>
  </section>;
}
