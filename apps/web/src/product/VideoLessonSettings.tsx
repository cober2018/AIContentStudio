import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api, currentUser } from "../api";
import { Button, ErrorBanner, Field, Spinner, inputClass } from "../components/ui";

type Source = { project_id: number; project_title: string; unit_id: number; unit_title: string };
type Lesson = { id: number; title: string; rule: string; scope: string; status: "proposed" | "active" | "rejected" | "retired"; occurrences: number; sources: Source[]; proposed_by: string | null; decided_at: string | null };
type ReworkRecord = { id: number; project_id: number; unit_id: number; unit_title: string | null; project_title: string | null; stage: "sample" | "final"; time_ms: number | null; note: string; lesson_id: number | null; created_at: string | null };
type Draft = { title: string; rule: string; scope: string };

const messageOf = (error: unknown, fallback: string) => error instanceof Error ? error.message : fallback;
const clock = (ms: number | null) => ms === null ? "" : `${Math.floor(ms / 60000)}:${String(Math.floor(ms / 1000) % 60).padStart(2, "0")}`;

function Sources({ sources }: { sources: Source[] }) {
  if (!sources.length) return <span className="text-slate-400">没有关联视频</span>;
  return <>{sources.map((item, index) => <span key={item.unit_id}>{index > 0 && "、"}<Link className="text-indigo-700 hover:underline" to={`/projects/${item.project_id}/units/${item.unit_id}/production`}>{item.project_title} · {item.unit_title}</Link></span>)}</>;
}

export default function VideoLessonSettings() {
  const queryClient = useQueryClient();
  const lessonsKey = ["video-lessons", currentUser()];
  const lessons = useQuery({ queryKey: lessonsKey, queryFn: () => api.get<{ items: Lesson[] }>("/settings/video-lessons"), retry: false });
  const [showRecords, setShowRecords] = useState(false);
  const records = useQuery({ queryKey: ["video-rework-records", currentUser()], queryFn: () => api.get<{ items: ReworkRecord[] }>("/settings/video-lessons/records?limit=50"), enabled: showRecords, retry: false });
  const me = useQuery({ queryKey: ["product-settings-user", currentUser()], queryFn: () => api.get<{ role: string }>("/users/me"), retry: false });
  const [editing, setEditing] = useState<number | null>(null);
  const [draft, setDraft] = useState<Draft>({ title: "", rule: "", scope: "" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function decide(id: number, body: Partial<Draft> & { action?: "approve" | "reject" | "retire" }) {
    if (busy) return;
    setBusy(true); setError("");
    try { await api.patch(`/settings/video-lessons/${id}`, body); setEditing(null); await queryClient.invalidateQueries({ queryKey: lessonsKey }); }
    catch (cause) { setError(messageOf(cause, "保存失败")); }
    finally { setBusy(false); }
  }

  if (lessons.isLoading) return <Spinner label="读取经验库…" />;
  if (lessons.isError || !lessons.data) return <ErrorBanner message={messageOf(lessons.error, "无法读取经验库")} />;
  const canDecide = me.data?.role === "admin" || me.data?.role === "editor";
  const pending = lessons.data.items.filter(item => item.status === "proposed");
  const active = lessons.data.items.filter(item => item.status === "active");
  const count = (item: Lesson) => <span className={item.occurrences >= 2 ? "font-medium text-red-600" : "text-slate-500"}>出现 {item.occurrences} 次{item.occurrences >= 2 && "（同一原因反复出现）"}</span>;

  return <section className="space-y-6 rounded-xl border border-slate-200 bg-white p-6" aria-label="经验库">
    <div className="space-y-1">
      <h2 className="font-semibold">经验库</h2>
      <p className="text-sm text-slate-600">小样、成片被退回后，剪辑模型把原因归纳成以后的做法交给你确认。你同意后，这条经验会随任务书带进之后每一条视频。</p>
    </div>
    {error && <div role="alert"><ErrorBanner message={error} /></div>}
    {!canDecide && <p className="text-sm text-slate-500">只有管理员和编辑可以同意、修改或停用经验。</p>}
    <div className="space-y-3">
      <h3 className="text-sm font-medium">待你确认（{pending.length}）</h3>
      {!pending.length && <p className="text-sm text-slate-500">没有待确认的经验。</p>}
      {pending.map(item => <div key={item.id} className="space-y-2 rounded-lg border border-amber-200 bg-amber-50/50 p-4">
        {editing === item.id ? <div className="space-y-3">
          <Field label="原因"><input className={inputClass} value={draft.title} maxLength={200} onChange={event => setDraft({ ...draft, title: event.target.value })} /></Field>
          <Field label="以后怎么做"><textarea className={inputClass} rows={3} value={draft.rule} maxLength={2000} onChange={event => setDraft({ ...draft, rule: event.target.value })} /></Field>
          <Field label="适用范围"><input className={inputClass} value={draft.scope} maxLength={200} onChange={event => setDraft({ ...draft, scope: event.target.value })} /></Field>
          <div className="flex flex-wrap gap-2"><Button size="sm" disabled={busy || !draft.title.trim() || !draft.rule.trim() || !draft.scope.trim()} onClick={() => void decide(item.id, { ...draft, action: "approve" })}>保存并同意</Button><Button size="sm" variant="secondary" disabled={busy} onClick={() => setEditing(null)}>取消</Button></div>
        </div> : <>
          <p className="font-medium text-slate-900">{item.title}</p>
          <p className="whitespace-pre-wrap text-sm text-slate-700">{item.rule}</p>
          <p className="text-xs text-slate-500">适用：{item.scope} · {count(item)} · 来自 <Sources sources={item.sources} /></p>
          {canDecide && <div className="flex flex-wrap gap-2"><Button size="sm" disabled={busy} onClick={() => void decide(item.id, { action: "approve" })}>同意</Button><Button size="sm" variant="secondary" disabled={busy} onClick={() => { setEditing(item.id); setDraft({ title: item.title, rule: item.rule, scope: item.scope }); }}>改后同意</Button><Button size="sm" variant="danger" disabled={busy} onClick={() => void decide(item.id, { action: "reject" })}>不同意</Button></div>}
        </>}
      </div>)}
    </div>
    <div className="space-y-3">
      <h3 className="text-sm font-medium">已生效（{active.length}）</h3>
      {!active.length && <p className="text-sm text-slate-500">还没有生效的经验。</p>}
      {active.map(item => <div key={item.id} className={`space-y-2 rounded-lg border p-4 ${item.occurrences >= 2 ? "border-red-200" : "border-slate-200"}`}>
        <div className="flex flex-wrap items-start justify-between gap-2"><p className="font-medium text-slate-900">{item.title}</p>{canDecide && <Button size="sm" variant="secondary" disabled={busy} onClick={() => void decide(item.id, { action: "retire" })}>停用</Button>}</div>
        <p className="whitespace-pre-wrap text-sm text-slate-700">{item.rule}</p>
        <p className="text-xs text-slate-500">适用：{item.scope} · {count(item)} · 来源视频：<Sources sources={item.sources} /></p>
      </div>)}
    </div>
    <details className="rounded-lg border border-slate-200" onToggle={event => setShowRecords(event.currentTarget.open)}>
      <summary className="cursor-pointer px-4 py-3 text-sm text-slate-600">最近的退回意见</summary>
      <div className="border-t border-slate-200 p-4">
        {records.isLoading && <Spinner label="读取退回意见…" />}
        {records.isError && <ErrorBanner message={messageOf(records.error, "无法读取退回意见")} />}
        {records.data && !records.data.items.length && <p className="text-sm text-slate-500">还没有退回意见。</p>}
        {records.data && records.data.items.length > 0 && <table className="w-full text-sm">
          <thead><tr className="border-b border-slate-200 text-left text-xs text-slate-500"><th className="py-2 font-normal">视频</th><th className="py-2 font-normal">阶段</th><th className="py-2 font-normal">意见</th><th className="py-2 font-normal">经验</th></tr></thead>
          <tbody>{records.data.items.map(item => <tr key={item.id} className="border-b border-slate-100 align-top">
            <td className="py-2 pr-3"><Link className="text-indigo-700 hover:underline" to={`/projects/${item.project_id}/units/${item.unit_id}/production`}>{item.project_title} · {item.unit_title}</Link><div className="text-xs text-slate-400">{item.created_at ? new Date(item.created_at).toLocaleString("zh-CN") : ""}</div></td>
            <td className="py-2 pr-3 whitespace-nowrap">{item.stage === "sample" ? "小样" : "成片"}{item.time_ms !== null && <span className="text-xs text-slate-500"> {clock(item.time_ms)}</span>}</td>
            <td className="py-2 pr-3 whitespace-pre-wrap">{item.note}</td>
            <td className="py-2 text-slate-500">{item.lesson_id ? `已归入 #${item.lesson_id}` : "还没归纳"}</td>
          </tr>)}</tbody>
        </table>}
      </div>
    </details>
  </section>;
}
