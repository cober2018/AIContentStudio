import { FormEvent, lazy, Suspense, useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api, ApiError, currentUser } from "../../api";
import { Button, EmptyState, ErrorBanner, Field, Spinner, inputClass } from "../../components/ui";

const SourceDrawer = lazy(() => import("../SourceTools").then(module => ({ default: module.SourceDrawer })));
const FactTemplatePicker = lazy(() => import("./FactTemplatePanel").then(module => ({ default: module.FactTemplatePicker })));
const FactBoundaryView = lazy(() => import("./FactTemplatePanel").then(module => ({ default: module.FactBoundaryView })));
const ObsidianKnowledgePanel = lazy(() => import("./ObsidianKnowledgePanel").then(module => ({ default: module.ObsidianKnowledgePanel })));

type Source = { id: number; title: string; source_type: string; parse_status: string; is_archived?: boolean; facts?: { id: number; statement: string; status: string }[] };
type SourceBinding = { id: number; source_document_id: number; title: string; source_type: string; parse_status: string };
type Boundary = { id: number; revision_no: number; fact_pack_id: number; fact_pack_version: number; fact_pack_checksum: string };

export function ProjectEvidenceTab({ projectId, readOnly: archived = false }: { projectId: number; readOnly?: boolean }) {
  const me = useQuery({ queryKey: ["project-operations-user", currentUser()], queryFn: () => api.get<{ role: string }>("/users/me"), retry: false });
  const readOnly = archived || !me.isSuccess || !["admin", "editor"].includes(me.data.role);
  const base = `/content-projects/${projectId}`;
  const [sources, setSources] = useState<SourceBinding[]>([]);
  const [library, setLibrary] = useState<Source[]>([]);
  const [history, setHistory] = useState<Boundary[]>([]);
  const [selectedSource, setSelectedSource] = useState<Source | null>(null);
  const [sourceId, setSourceId] = useState("");
  const [sourceTitle, setSourceTitle] = useState("");
  const [sourceText, setSourceText] = useState("");
  const [sourceUrl, setSourceUrl] = useState("");
  const [sourceDate, setSourceDate] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  async function reload() {
    const [nextSources, nextLibrary, nextHistory] = await Promise.all([
      api.get<SourceBinding[]>(`${base}/sources`), api.get<Source[]>("/sources"), api.get<Boundary[]>(`${base}/fact-boundary/revisions`),
    ]);
    setSources(nextSources); setLibrary(nextLibrary); setHistory(nextHistory);
  }
  useEffect(() => { setLoading(true); reload().catch((err) => setError(err instanceof ApiError ? err.message : "无法读取项目证据")).finally(() => setLoading(false)); }, [projectId]);
  async function action(work: () => Promise<unknown>) { setBusy(true); setError(""); try { await work(); await reload(); } catch (err) { setError(err instanceof Error ? err.message : "操作失败"); } finally { setBusy(false); } }
  async function attach(id: number) { await api.post(`${base}/sources`, { source_document_id: id }); setSourceId(""); }
  async function ensureWritable() { const project = await api.get<{ status: string }>(base); if (readOnly || project.status === "archived") throw new Error("项目已归档，不能从项目创建来源"); }
  async function createText(event: FormEvent) { event.preventDefault(); await action(async () => { await ensureWritable(); const source = await api.post<Source>("/sources/text", { title: sourceTitle, content: sourceText, as_of: sourceDate || null }); await attach(source.id); setSourceTitle(""); setSourceText(""); }); }
  async function createUrl(event: FormEvent) { event.preventDefault(); await action(async () => { await ensureWritable(); const source = await api.post<Source>("/sources/url", { url: sourceUrl, as_of: sourceDate || null }); await attach(source.id); setSourceUrl(""); }); }
  async function upload(file: File | null) { if (!file) return; await action(async () => { await ensureWritable(); const form = new FormData(); form.append("file", file); const source = await api.upload<Source>(`/sources/upload${sourceDate ? `?as_of=${encodeURIComponent(sourceDate)}` : ""}`, form); await attach(source.id); }); }
  async function inspect(id: number) { try { setSelectedSource(await api.get<Source>(`/sources/${id}`)); } catch (err) { setError(err instanceof Error ? err.message : "读取来源失败"); } }
  if (loading) return <Spinner label="读取来源与事实边界…" />;
  return <section className="space-y-5">
    {error && <ErrorBanner message={error} />}
    {me.isError && <ErrorBanner message="无法核对操作权限；当前仅可查看，不能修改证据。" />}
    <Suspense fallback={<Spinner label="读取事实边界…" />}><FactTemplatePicker projectId={projectId} readOnly={readOnly} /><div className="mt-5"><FactBoundaryView projectId={projectId} /></div></Suspense>
    <Suspense fallback={<Spinner label="读取知识参考…" />}><ObsidianKnowledgePanel projectId={projectId} readOnly={readOnly} onSaved={() => reload().catch(err => setError(messageOf(err)))} /></Suspense>
    <div className="rounded-xl border border-slate-200 bg-white p-6 space-y-4"><h2 className="font-semibold">项目来源</h2><p className="text-xs text-slate-500">引用现有 Source；从项目解除引用不会更改历史冻结事实边界。</p>
      {sources.length ? <ul className="space-y-2">{sources.map((item) => <li key={item.id} className="flex flex-wrap items-center justify-between gap-2 rounded-lg border p-3 text-sm"><span>{item.title} · {item.source_type} · {item.parse_status}</span><div className="flex gap-2"><Button size="sm" variant="secondary" onClick={() => inspect(item.source_document_id)}>查看事实</Button>{!readOnly && <Button size="sm" variant="danger" disabled={busy} onClick={() => action(() => api.del(`${base}/sources/${item.source_document_id}`))}>解除引用</Button>}</div></li>)}</ul> : <EmptyState title="项目尚无来源引用" />}
      {!readOnly && <><div className="flex gap-2"><select className={inputClass} value={sourceId} onChange={(event) => setSourceId(event.target.value)}><option value="">选择已有 Source</option>{library.filter((item) => !sources.some((bound) => bound.source_document_id === item.id)).map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}</select><Button disabled={!sourceId || busy} onClick={() => action(() => attach(Number(sourceId)))}>引用</Button></div>
      <Field label="项目导入资料日期 as_of（可选）"><input type="date" className={inputClass} disabled={busy} value={sourceDate} onChange={event => setSourceDate(event.target.value)} /></Field>
      <div className="grid gap-4 md:grid-cols-2"><form onSubmit={createText} className="space-y-2"><Field label="创建文本 Source"><input className={inputClass} required value={sourceTitle} onChange={(event) => setSourceTitle(event.target.value)} placeholder="标题" /></Field><textarea className={inputClass} required rows={3} value={sourceText} onChange={(event) => setSourceText(event.target.value)} placeholder="原文" /><Button type="submit" disabled={busy}>创建并引用</Button></form><div className="space-y-2"><form onSubmit={createUrl} className="space-y-2"><Field label="创建 URL Source"><input className={inputClass} required type="url" value={sourceUrl} onChange={(event) => setSourceUrl(event.target.value)} /></Field><Button type="submit" disabled={busy}>抓取并引用</Button></form><Field label="上传 Source 文件"><input type="file" className={inputClass} disabled={busy} onChange={(event) => upload(event.target.files?.[0] || null)} /></Field></div></div></>}
      {selectedSource && <Suspense fallback={<Spinner />}><SourceDrawer key={selectedSource.id} sourceId={selectedSource.id} readOnly={readOnly} onClose={() => { setSelectedSource(null); void reload().catch(err => setError(messageOf(err))); }} /></Suspense>}
    </div>
    {history.length > 0 && <div className="rounded-xl border border-slate-200 bg-white p-6"><h2 className="font-semibold">事实边界历史</h2><ul className="mt-2 space-y-1 text-sm text-slate-600">{history.map((item) => <li key={item.id}>第 {item.revision_no} 版 · FactPack #{item.fact_pack_id} v{item.fact_pack_version}</li>)}</ul></div>}
  </section>;
}

function messageOf(error: unknown) { return error instanceof Error ? error.message : "证据读取失败"; }
