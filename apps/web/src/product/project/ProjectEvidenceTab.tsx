import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, ApiError } from "../../api";
import { Button, EmptyState, ErrorBanner, Field, Spinner, inputClass } from "../../components/ui";

type Source = { id: number; title: string; source_type: string; parse_status: string; is_archived?: boolean; facts?: { id: number; statement: string; status: string }[] };
type SourceBinding = { id: number; source_document_id: number; title: string; source_type: string; parse_status: string };
type Pack = { id: number; name: string; status: string; version: number; checksum: string | null; parent_id: number | null };
type EvidenceItem = { item_id: number; ref: string; evidence_kind: string; statement: string | null; snapshot: { excerpt?: string; statement?: string; source_title?: string; source_url?: string; source_locator?: string } | null; source_document_id: number | null; public_use_allowed: boolean };
type PackDetail = Pack & { items: EvidenceItem[] };
type Boundary = { id: number; revision_no: number; fact_pack_id: number; fact_pack_version: number; fact_pack_checksum: string };

export function ProjectEvidenceTab({ projectId, readOnly = false }: { projectId: number; readOnly?: boolean }) {
  const base = `/content-projects/${projectId}`;
  const [sources, setSources] = useState<SourceBinding[]>([]);
  const [library, setLibrary] = useState<Source[]>([]);
  const [packs, setPacks] = useState<Pack[]>([]);
  const [boundary, setBoundary] = useState<Boundary | null>(null);
  const [evidencePack, setEvidencePack] = useState<PackDetail | null>(null);
  const [history, setHistory] = useState<Boundary[]>([]);
  const [selectedSource, setSelectedSource] = useState<Source | null>(null);
  const [sourceId, setSourceId] = useState("");
  const [sourceTitle, setSourceTitle] = useState("");
  const [sourceText, setSourceText] = useState("");
  const [sourceUrl, setSourceUrl] = useState("");
  const [packId, setPackId] = useState("");
  const [draftId, setDraftId] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  async function reload() {
    const [nextSources, nextLibrary, nextPacks, nextBoundary, nextHistory] = await Promise.all([
      api.get<SourceBinding[]>(`${base}/sources`), api.get<Source[]>("/sources"), api.get<Pack[]>("/fact-packs"),
      api.get<Boundary | null>(`${base}/fact-boundary`), api.get<Boundary[]>(`${base}/fact-boundary/revisions`),
    ]);
    setSources(nextSources); setLibrary(nextLibrary); setPacks(nextPacks); setBoundary(nextBoundary); setHistory(nextHistory);
    setEvidencePack(nextBoundary ? await api.get<PackDetail>(`/fact-packs/${nextBoundary.fact_pack_id}`) : null);
    setDraftId(nextBoundary ? nextPacks.filter((pack) => pack.status === "draft" && pack.parent_id === nextBoundary.fact_pack_id).sort((a, b) => b.id - a.id)[0]?.id ?? null : null);
  }
  useEffect(() => { setLoading(true); reload().catch((err) => setError(err instanceof ApiError ? err.message : "无法读取项目证据")).finally(() => setLoading(false)); }, [projectId]);
  async function action(work: () => Promise<unknown>) { setBusy(true); setError(""); try { await work(); await reload(); } catch (err) { setError(err instanceof Error ? err.message : "操作失败"); } finally { setBusy(false); } }
  async function attach(id: number) { await api.post(`${base}/sources`, { source_document_id: id }); setSourceId(""); }
  async function ensureWritable() { const project = await api.get<{ status: string }>(base); if (readOnly || project.status === "archived") throw new Error("项目已归档，不能从项目创建来源"); }
  async function createText(event: FormEvent) { event.preventDefault(); await action(async () => { await ensureWritable(); const source = await api.post<Source>("/sources/text", { title: sourceTitle, content: sourceText }); await attach(source.id); setSourceTitle(""); setSourceText(""); }); }
  async function createUrl(event: FormEvent) { event.preventDefault(); await action(async () => { await ensureWritable(); const source = await api.post<Source>("/sources/url", { url: sourceUrl }); await attach(source.id); setSourceUrl(""); }); }
  async function upload(file: File | null) { if (!file) return; await action(async () => { await ensureWritable(); const form = new FormData(); form.append("file", file); const source = await api.upload<Source>("/sources/upload", form); await attach(source.id); }); }
  async function inspect(id: number) { try { setSelectedSource(await api.get<Source>(`/sources/${id}`)); } catch (err) { setError(err instanceof Error ? err.message : "读取来源失败"); } }
  async function clone() { await action(async () => { const draft = await api.post<Pack>(`${base}/fact-boundary/clone`); setDraftId(draft.id); }); }
  if (loading) return <Spinner label="读取来源与事实边界…" />;
  return <section className="space-y-5">
    {error && <ErrorBanner message={error} />}
    <div className="rounded-xl border border-slate-200 bg-white p-6 space-y-4"><h2 className="font-semibold">项目来源</h2><p className="text-xs text-slate-500">引用现有 Source；从项目解除引用不会更改历史冻结事实边界。</p>
      {sources.length ? <ul className="space-y-2">{sources.map((item) => <li key={item.id} className="flex flex-wrap items-center justify-between gap-2 rounded-lg border p-3 text-sm"><span>{item.title} · {item.source_type} · {item.parse_status}</span><div className="flex gap-2"><Button size="sm" variant="secondary" onClick={() => inspect(item.source_document_id)}>查看事实</Button>{!readOnly && <Button size="sm" variant="danger" disabled={busy} onClick={() => action(() => api.del(`${base}/sources/${item.source_document_id}`))}>解除引用</Button>}</div></li>)}</ul> : <EmptyState title="项目尚无来源引用" />}
      {!readOnly && <><div className="flex gap-2"><select className={inputClass} value={sourceId} onChange={(event) => setSourceId(event.target.value)}><option value="">选择已有 Source</option>{library.filter((item) => !sources.some((bound) => bound.source_document_id === item.id)).map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}</select><Button disabled={!sourceId || busy} onClick={() => action(() => attach(Number(sourceId)))}>引用</Button></div>
      <div className="grid gap-4 md:grid-cols-2"><form onSubmit={createText} className="space-y-2"><Field label="创建文本 Source"><input className={inputClass} required value={sourceTitle} onChange={(event) => setSourceTitle(event.target.value)} placeholder="标题" /></Field><textarea className={inputClass} required rows={3} value={sourceText} onChange={(event) => setSourceText(event.target.value)} placeholder="原文" /><Button type="submit" disabled={busy}>创建并引用</Button></form><div className="space-y-2"><form onSubmit={createUrl} className="space-y-2"><Field label="创建 URL Source"><input className={inputClass} required type="url" value={sourceUrl} onChange={(event) => setSourceUrl(event.target.value)} /></Field><Button type="submit" disabled={busy}>抓取并引用</Button></form><Field label="上传 Source 文件"><input type="file" className={inputClass} onChange={(event) => upload(event.target.files?.[0] || null)} /></Field></div></div></>}
      {selectedSource && <div className="rounded-lg bg-slate-50 p-4 text-sm"><h3 className="font-medium">{selectedSource.title} · 已抽取事实</h3>{selectedSource.facts?.length ? <ul className="mt-2 list-disc pl-5">{selectedSource.facts.map((fact) => <li key={fact.id}>{fact.statement} · {fact.status}</li>)}</ul> : <p className="mt-2 text-slate-500">暂无事实；可从 <Link className="text-indigo-700" to="/sources">来源库</Link>抽取和确认。</p>}</div>}
    </div>
    <div className="rounded-xl border border-slate-200 bg-white p-6 space-y-4"><h2 className="font-semibold">项目证据</h2><p className="text-xs text-slate-500">以下条目来自当前冻结 FactPack；Source 引用变化不会改写这些历史快照。</p>{evidencePack?.items.length ? <ul className="space-y-2">{evidencePack.items.map((item) => <li key={item.item_id} className="rounded-lg border p-3 text-sm"><p className="font-medium">{item.ref} · {item.statement || item.snapshot?.excerpt || "未命名证据"}</p><p className="mt-1 text-xs text-slate-500">{item.evidence_kind} · {item.snapshot?.source_title || (item.source_document_id ? `Source #${item.source_document_id}` : "来源待核对")} · {item.snapshot?.source_locator || "定位待核对"} · {item.public_use_allowed ? "允许公开" : "未获公开许可"}</p></li>)}</ul> : <EmptyState title={boundary ? "当前事实边界没有证据条目" : "先绑定冻结事实包，再查看项目证据"} />}</div>
    <div className="rounded-xl border border-slate-200 bg-white p-6 space-y-4"><h2 className="font-semibold">事实边界</h2>{boundary ? <p className="text-sm">第 {boundary.revision_no} 版 · FactPack #{boundary.fact_pack_id} v{boundary.fact_pack_version} · {boundary.fact_pack_checksum.slice(0, 12)}…</p> : <EmptyState title="尚未建立项目事实边界" />}
      {!readOnly && <div className="flex gap-2"><select className={inputClass} value={packId} onChange={(event) => setPackId(event.target.value)}><option value="">选择已冻结 FactPack</option>{packs.filter((pack) => pack.status === "frozen" && pack.checksum).map((pack) => <option key={pack.id} value={pack.id}>{pack.name} v{pack.version}</option>)}</select><Button disabled={!packId || busy} onClick={() => action(() => api.post(`${base}/fact-boundary`, { fact_pack_id: Number(packId), expected_revision: boundary?.revision_no || 0 }))}>绑定为新版本</Button></div>}
      {!readOnly && boundary && <div className="flex flex-wrap gap-2"><Button variant="secondary" disabled={busy} onClick={clone}>克隆当前边界为草稿</Button>{draftId && <><Link className="rounded-md border px-3 py-2 text-sm text-indigo-700" to={`/fact-packs/${draftId}`}>编辑草稿 FactPack #{draftId}</Link><Button disabled={busy} onClick={() => action(() => api.post(`${base}/fact-boundary/${draftId}/freeze-and-bind`, { expected_revision: boundary.revision_no }))}>冻结并绑定草稿</Button></>}</div>}
      <div><h3 className="text-sm font-medium">历史边界</h3><ul className="mt-2 space-y-1 text-sm text-slate-600">{history.map((item) => <li key={item.id}>第 {item.revision_no} 版 · FactPack #{item.fact_pack_id} v{item.fact_pack_version}</li>)}</ul></div>
    </div>
  </section>;
}
