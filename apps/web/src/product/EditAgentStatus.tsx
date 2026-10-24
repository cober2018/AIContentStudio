import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";
import { api, ApiError, currentUser } from "../api";
import { Button } from "../components/ui";
import { handoffSummary, prepareEdit } from "./editHandoff";

type Status = { label: string | null; detail?: string; execution_id?: number; state?: string; log?: string | null; can_retry?: boolean };
const tone: Record<string, string> = { 出错: "border-rose-200 bg-rose-50 text-rose-800", "粗剪已回传，待你审片": "border-emerald-200 bg-emerald-50 text-emerald-800" };

export default function EditAgentStatus({ projectId, unitId }: { projectId: number; unitId: number }) {
  const status = useQuery({ queryKey: ["edit-agent", currentUser(), projectId, unitId], retry: false,
    queryFn: () => api.get<Status>(`/content-projects/${projectId}/units/${unitId}/edit-agent`),
    refetchInterval: query => ["排队中", "剪辑中"].includes(query.state.data?.label || "") ? 15000 : false });
  const [issue, setIssue] = useState("");
  const [starting, setStarting] = useState("");
  const data = status.data;
  // A 导演包 made before auto-edit existed has no edit task yet; this builds it (same steps as 准备剪辑).
  async function start() {
    setIssue("");
    try { setStarting(handoffSummary(await prepareEdit(projectId, unitId, setStarting))); await status.refetch(); }
    catch (cause) { setStarting(""); setIssue(cause instanceof Error ? cause.message : "没能建好剪辑任务"); }
  }
  if (status.isPending || status.error) return null;
  if (!data?.label) return <section aria-label="剪辑进度" className="rounded-xl border border-slate-200 bg-white p-4 text-sm">
    <div className="flex flex-wrap items-center justify-between gap-2"><p><span className="font-semibold">剪辑：还没开始</span>{starting ? ` · ${starting}` : " · 素材和导演包准备好后，点右边按钮交给本机助手剪粗剪。"}</p><Button size="sm" disabled={!!starting && !issue} onClick={() => void start()}>开始剪辑</Button></div>
    {issue && <p role="alert" className="mt-1 text-xs text-rose-700">{issue}</p>}
  </section>;
  async function retry() {
    setIssue("");
    try { await api.post(`/content-projects/${projectId}/units/${unitId}/edit-agent/retry`, {}); await status.refetch(); }
    catch (cause) { setIssue(cause instanceof ApiError ? (cause.detail as { message?: string } | undefined)?.message || cause.message : "重试没成功"); }
  }
  return <section aria-label="剪辑进度" className={`rounded-xl border p-4 text-sm ${tone[data.label] || "border-indigo-200 bg-indigo-50 text-indigo-900"}`}>
    <div className="flex flex-wrap items-center justify-between gap-2"><p><span className="font-semibold">剪辑：{data.label}</span>{data.detail ? ` · ${data.detail}` : ""}</p>
      <div className="flex flex-wrap gap-2">{data.can_retry && <Button size="sm" onClick={() => void retry()}>重试</Button>}{data.execution_id && <Link className="self-center underline" to={`?workstep=make&panel=execution&execution=${data.execution_id}`}>{data.label.startsWith("粗剪已回传") ? "去审片" : "打开剪辑任务"}</Link>}</div></div>
    {data.log && data.label === "出错" && <p className="mt-1 break-all text-xs opacity-80">日志：{data.log}</p>}
    {issue && <p role="alert" className="mt-1 text-xs text-rose-700">{issue}</p>}
  </section>;
}
