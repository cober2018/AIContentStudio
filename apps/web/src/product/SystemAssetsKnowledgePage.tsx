import { lazy, Suspense, useEffect, useRef, useState, type FormEvent, type ReactNode } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useSearchParams } from "react-router-dom";
import { api, ApiError, currentUser } from "../api";
import { Button, EmptyState, ErrorBanner, Field, Spinner, StatusBadge, inputClass } from "../components/ui";
import {
  checkedPage, collectionResource, collectionSnapshotRevision, internalLibraryLink, libraryError, libraryLabels, libraryQuery,
  libraryTabs, materialKinds, membershipPayload, positiveNumber, readableValue,
} from "./systemLibraryTypes";
import type {
  CollectionItem, CollectionPage, FactBoundary, FactPackDetail, KnowledgeCollection, LibraryItem, LibraryPage,
  LibraryTab, LibraryUsage, LibraryUser, MaterialRevision, ProjectSummary, SourceDetail,
} from "./systemLibraryTypes";

const box = "space-y-4 rounded-xl border border-slate-200 bg-white p-5";
const linkClass = "text-sm text-indigo-700 underline underline-offset-4";
const PAGE_SIZE = 20;
const ProviderMediaPanel = lazy(() => import("./ProviderMediaPanel"));

function useLibraryRead<T>(path: string, enabled = true) {
  return useQuery({ queryKey: ["system-library", currentUser(), path], queryFn: () => api.get<T>(path), enabled, retry: false });
}
function Read<T>({ path, children }: { path: string; children: (data: T) => ReactNode }) {
  const query = useLibraryRead<T>(path);
  if (query.isPending) return <Spinner label="读取详细记录…" />;
  if (query.isError) return <ReadError error={query.error} retry={() => void query.refetch()} />;
  return <>{children(query.data)}</>;
}
function ReadError({ error, retry }: { error: unknown; retry: () => void }) {
  return <div role="alert" className="space-y-3"><ErrorBanner message={libraryError(error)} /><Button variant="secondary" onClick={retry}>重新读取</Button></div>;
}
function Metadata({ values }: { values: Record<string, unknown> }) {
  return <dl className="grid gap-2 text-sm sm:grid-cols-2">{Object.entries(values).map(([label, value]) => <div key={label} className="min-w-0 rounded-lg bg-slate-50 p-3"><dt className="text-xs text-slate-500">{label}</dt><dd className="mt-1 break-words">{readableValue(value)}</dd></div>)}</dl>;
}
function Pagination({ page, offset, change }: { page: LibraryPage<unknown>; offset: number; change: (offset: number) => void }) {
  return <div className="flex flex-wrap items-center gap-3 text-sm"><span className="text-slate-500">共 {page.total} 条 · 当前 {page.items.length} 条</span><Button variant="secondary" disabled={offset === 0} onClick={() => change(Math.max(0, offset - page.limit))}>上一页</Button><Button variant="secondary" disabled={page.offset + page.items.length >= page.total} onClick={() => change(offset + page.limit)}>下一页</Button></div>;
}

function useLibraryAction() {
  const client = useQueryClient();
  const [busy, setBusy] = useState(false);
  const pending = useRef(false);
  const [error, setError] = useState<unknown>();
  const [conflict, setConflict] = useState(false);
  const [message, setMessage] = useState("");
  async function refresh() {
    if (pending.current) return;
    pending.current = true;
    setBusy(true);
    try {
      await client.invalidateQueries({ queryKey: ["system-library", currentUser()] }, { throwOnError: true });
      setConflict(false); setError(undefined); setMessage("");
    } catch (cause) { setError(cause); }
    finally { pending.current = false; setBusy(false); }
  }
  async function run(work: () => Promise<unknown>, success: string) {
    if (pending.current || conflict) return false;
    pending.current = true;
    setBusy(true); setError(undefined); setMessage("");
    try {
      await work();
      setMessage(success);
      await client.invalidateQueries({ queryKey: ["system-library", currentUser()] }, { throwOnError: true });
      await client.invalidateQueries({ queryKey: ["projects"] });
      return true;
    } catch (cause) {
      setError(cause); setConflict(cause instanceof ApiError && cause.status === 409);
      return false;
    } finally { pending.current = false; setBusy(false); }
  }
  return { busy, error, conflict, message, run, refresh, disabled: busy || conflict };
}
type LibraryAction = ReturnType<typeof useLibraryAction>;
function ActionState({ action }: { action: LibraryAction }) {
  return <div aria-live="polite" className="space-y-2">{action.error !== undefined && <ErrorBanner message={libraryError(action.error)} />}{action.conflict && <div role="alert" className="space-y-2 rounded-lg bg-amber-50 p-3 text-sm text-amber-900"><p>版本或状态已变化。刷新后核对最新记录，再明确提交；不会自动重试写入。</p><Button variant="secondary" disabled={action.busy} onClick={() => void action.refresh()}>刷新并重新核对</Button></div>}{action.message && <p role="status" className="text-sm text-emerald-700">{action.message}{action.error !== undefined && "；回读失败，请重新读取确认最新界面。"}</p>}</div>;
}

function Rights({ item }: { item: LibraryItem }) {
  if (item.type === "source") return <p className="rounded-lg bg-amber-50 p-3 text-sm text-amber-900">来源层尚未决定公开或模型使用权利。解析成功、信任等级均不代表授权；依据以 FactPack 证据条目为准。</p>;
  if (item.type === "knowledge_collection") return <p className="text-sm text-slate-600">集合仅组织引用，不授予权利、不冻结证据，也不构成项目事实边界。</p>;
  return <div className="space-y-3">{item.type === "fact_pack" && <p className="text-sm text-amber-800">冻结状态不代表可公开使用；未知、空包和撤销项仍需核对。</p>}{item.rights && typeof item.rights === "object" ? <Metadata values={item.rights} /> : <p className="text-sm">权利：{readableValue(item.rights)}</p>}</div>;
}
function Usage({ item }: { item: LibraryItem }) {
  const [offset, setOffset] = useState(0);
  return <Read<LibraryUsage> path={`/system-library/${item.type}/${item.id}/usage?limit=${PAGE_SIZE}&offset=${offset}`}>{(data) => {
    if (!data?.coverage || !data.counts || !Array.isArray(data.items)) return <ErrorBanner message="使用覆盖信息缺失，不能推断为没有使用。" />;
    return <div className="space-y-3"><p className="text-xs text-slate-500">仅展示当前用户获授权的使用记录；未覆盖的类别不能当作零使用。</p>{Object.entries(data.coverage).map(([name, coverage]) => <section key={name} className="space-y-2 rounded-lg border p-3"><h4 className="text-sm font-semibold">{name} · {coverage === "supported" && data.counts[name] != null ? `${data.counts[name]} 条` : "不作零使用推断"}</h4><p className="text-xs text-slate-500">覆盖：{coverage === "supported" ? "已支持（仅授权范围）" : coverage === "not_applicable" ? "不适用" : "尚未覆盖"}</p>{data.items.filter((ref) => ref.category === name).map((ref) => {
      const href = internalLibraryLink(ref.href);
      return <p key={`${ref.category}:${ref.id}`} className="text-sm">{ref.title}{href && <> · <Link className={linkClass} to={href}>查看获授权记录</Link></>}</p>;
    })}</section>)}<Pagination page={data} offset={offset} change={setOffset} /></div>;
  }}</Read>;
}

function MaterialPreview({ item, revision }: { item: LibraryItem; revision: MaterialRevision }) {
  const [url, setUrl] = useState<string>();
  const [mime, setMime] = useState(revision.mime_type);
  const [error, setError] = useState<unknown>();
  const [busy, setBusy] = useState(false);
  const controller = useRef<AbortController>();
  const blobUrl = useRef<string>();
  useEffect(() => () => { controller.current?.abort(); if (blobUrl.current) URL.revokeObjectURL(blobUrl.current); }, []);
  async function preview() {
    controller.current?.abort();
    const request = new AbortController(); controller.current = request;
    setBusy(true); setError(undefined);
    try {
      const response = await fetch(`/api/v1/materials/${item.id}/revisions/${revision.id}/raw`, { signal: request.signal, headers: { "X-Studio-User": currentUser() } });
      if (!response.ok) throw new ApiError(response.status, `预览读取失败（${response.status}）`);
      const blob = await response.blob();
      if (request.signal.aborted) return;
      if (blobUrl.current) URL.revokeObjectURL(blobUrl.current);
      blobUrl.current = URL.createObjectURL(blob); setUrl(blobUrl.current); setMime(blob.type || revision.mime_type);
    } catch (cause) { if (!request.signal.aborted) setError(cause); }
    finally { if (!request.signal.aborted) setBusy(false); }
  }
  return <div className="space-y-3"><Button variant="secondary" disabled={busy} onClick={() => void preview()}>{busy ? "读取媒体…" : "加载此版本预览"}</Button>{error !== undefined && <ErrorBanner message={libraryError(error)} />}{url && (mime?.startsWith("image/") ? <img src={url} alt={item.title} className="max-h-72 rounded-lg object-contain" /> : mime?.startsWith("video/") ? <video src={url} controls className="max-h-72 w-full" /> : mime?.startsWith("audio/") ? <audio src={url} controls /> : <a href={url} download className={linkClass}>下载此版本文件</a>)}</div>;
}
function MaterialVersions({ item, onRevision }: { item: LibraryItem; onRevision: (revision: MaterialRevision) => void }) {
  const [offset, setOffset] = useState(0);
  const path = `/system-library/material/${item.id}/revisions?limit=${PAGE_SIZE}&offset=${offset}`;
  const query = useQuery({ queryKey: ["system-library", currentUser(), path], queryFn: async () => checkedPage(await api.get<LibraryPage<MaterialRevision>>(path)), retry: false });
  if (query.isPending) return <Spinner label="读取本页素材版本…" />;
  if (query.isError) return <ReadError error={query.error} retry={() => void query.refetch()} />;
  return <div className="space-y-3">{query.data.items.length ? query.data.items.map((revision) => <div key={revision.id} className="flex flex-wrap items-center justify-between gap-2 rounded-lg border p-3 text-sm"><span>v{revision.revision_no} · Revision #{revision.id} · {revision.rights_status ?? "权利未知"}</span><Button variant="secondary" size="sm" onClick={() => onRevision(revision)}>选择此精确版本</Button></div>) : <EmptyState title="本页没有素材版本" />}<Pagination page={query.data} offset={offset} change={setOffset} /></div>;
}

function ProjectReuse({ item, revision, canWrite }: { item: LibraryItem; revision?: MaterialRevision | null; canWrite: boolean }) {
  const [projectInput, setProjectInput] = useState("");
  const [projectId, setProjectId] = useState<number>();
  const [localError, setLocalError] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const action = useLibraryAction();
  const project = useLibraryRead<ProjectSummary>(`/content-projects/${projectId}`, projectId !== undefined);
  const boundary = useLibraryRead<FactBoundary | null>(`/content-projects/${projectId}/fact-boundary`, projectId !== undefined && item.type === "fact_pack");
  const pack = useLibraryRead<FactPackDetail>(`/fact-packs/${item.id}`, item.type === "fact_pack");
  const resourceArchived = item.status === "archived" || revision?.status === "revoked" || revision?.status === "archived";
  const packReady = item.type !== "fact_pack" || (pack.isSuccess && pack.data.status === "frozen" && !!pack.data.checksum && boundary.isSuccess);
  const writable = canWrite && (item.type !== "material" || !!revision) && !resourceArchived && project.isSuccess && project.data.status !== "archived" && packReady;
  function choose(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setLocalError(""); setConfirmed(false);
    try { setProjectId(positiveNumber(projectInput, "项目 ID")); } catch (cause) { setLocalError(libraryError(cause)); }
  }
  async function attach() {
    if (!writable || !projectId || !confirmed) return;
    await action.run(async () => {
      if (item.type === "material") {
        if (!revision) throw new Error("请先选择精确素材版本。");
        await api.post(`/content-projects/${projectId}/materials/references`, { material_revision_id: revision.id });
      } else if (item.type === "source") {
        await api.post(`/content-projects/${projectId}/sources`, { source_document_id: item.id });
      } else if (item.type === "fact_pack" && boundary.isSuccess) {
        await api.post(`/content-projects/${projectId}/fact-boundary`, { fact_pack_id: item.id, expected_revision: boundary.data?.revision_no ?? 0 });
      }
    }, item.type === "fact_pack" ? "后端已确认新的项目事实边界。" : "后端已确认项目引用；资源没有被复制。");
    setConfirmed(false);
  }
  return <section className={box}><h3 className="font-semibold">明确引用到项目</h3><p className="text-xs text-slate-500">选择自有项目；<Link to="/projects" className={linkClass}>查看项目 ID</Link>。归档项目不能新增引用。</p><form onSubmit={choose} className="flex items-end gap-2"><Field label="项目 ID"><input type="text" inputMode="numeric" className={inputClass} value={projectInput} onChange={(event) => { setProjectInput(event.target.value); setProjectId(undefined); setConfirmed(false); }} /></Field><Button type="submit" variant="secondary" disabled={!projectInput || action.busy}>读取并核对项目</Button></form>{localError && <ErrorBanner message={localError} />}{projectId && project.isPending && <Spinner label="验证项目访问权限…" />}{project.isError && <ReadError error={project.error} retry={() => void project.refetch()} />}{project.isSuccess && <><p className="text-sm">目标：{project.data.title} · #{project.data.id} · <StatusBadge status={project.data.status} /></p>{item.type === "material" && <p className="text-sm">引用固定 Revision #{revision?.id ?? "未选择"}，不会自动跟随最新版本。</p>}{item.type === "fact_pack" && <><p className="text-sm text-amber-800">此操作建立新的事实边界版本。集合、草稿包和无校验和包不能代替冻结证据。</p>{pack.isPending || boundary.isPending ? <Spinner label="读取冻结包与当前边界…" /> : null}{pack.isError && <ReadError error={pack.error} retry={() => void pack.refetch()} />}{boundary.isError && <ReadError error={boundary.error} retry={() => void boundary.refetch()} />}{pack.isSuccess && <p className="break-all text-xs">FactPack #{pack.data.id} v{pack.data.version} · {pack.data.status} · checksum: {pack.data.checksum ?? "缺失"}</p>}{boundary.isSuccess && <p className="text-xs">当前边界版本：{boundary.data?.revision_no ?? 0}{boundary.data && ` · FactPack #${boundary.data.fact_pack_id}`}</p>}</>}<label className="flex items-start gap-2 text-sm"><input type="checkbox" checked={confirmed} disabled={!writable || action.disabled} onChange={(event) => setConfirmed(event.target.checked)} />我已核对资源、精确版本和目标项目，确认{item.type === "fact_pack" ? "建立新的事实边界" : "添加引用"}。</label><Button disabled={!writable || !confirmed || action.disabled || (item.type === "material" && !revision)} onClick={() => void attach()}>{action.busy ? "保存中…" : item.type === "fact_pack" ? "确认绑定冻结 FactPack" : "确认添加项目引用"}</Button><Link to={`/projects/${projectId}?tab=${item.type === "material" ? "assets" : "evidence"}`} className={linkClass}>到项目回读</Link></>}{!canWrite && <p className="text-sm text-slate-500">当前角色只可查看。</p>}{resourceArchived && <p className="text-sm text-amber-800">资源或所选版本已归档 / 撤销，不能新增引用。</p>}<ActionState action={action} /></section>;
}

function ResourceDetail({ item, canWrite }: { item: LibraryItem; canWrite: boolean }) {
  const [panel, setPanel] = useState("summary");
  const [selectedRevisionId, setSelectedRevisionId] = useState(item.type === "material" ? item.latest_revision?.id : undefined);
  const selectedRevision = useLibraryRead<MaterialRevision>(`/system-library/material/${item.id}/revisions/${selectedRevisionId}`, item.type === "material" && selectedRevisionId !== undefined);
  const revision = selectedRevision.isSuccess && !selectedRevision.isFetching ? selectedRevision.data : undefined;
  const [reuse, setReuse] = useState(false);
  const action = useLibraryAction();
  const legacy = item.type === "material" ? "/materials" : item.type === "source" ? "/sources" : `/fact-packs/${item.id}`;
  return <section className={box}><div className="flex flex-wrap items-center justify-between gap-3"><div><p className="text-xs text-slate-500">{libraryLabels[item.type]} · #{item.id} · 系统共享</p><h2 className="mt-1 text-xl font-semibold">{item.title}</h2></div><StatusBadge status={item.status} /></div><nav className="flex flex-wrap gap-2" aria-label="资源详情"><Button variant={panel === "summary" ? "primary" : "secondary"} onClick={() => setPanel("summary")}>权利与来源</Button><Button variant={panel === "usage" ? "primary" : "secondary"} onClick={() => setPanel("usage")}>按需读取使用情况</Button>{item.type === "material" && <Button variant={panel === "revisions" ? "primary" : "secondary"} onClick={() => setPanel("revisions")}>按页查看版本</Button>}{item.type !== "material" && <Button variant={panel === "content" ? "primary" : "secondary"} onClick={() => setPanel("content")}>按需读取正文 / 证据</Button>}</nav>
    {item.type === "material" && selectedRevisionId !== undefined && selectedRevision.isPending && <Spinner label="读取所选精确版本…" />}{item.type === "material" && selectedRevision.isError && <ReadError error={selectedRevision.error} retry={() => void selectedRevision.refetch()} />}{panel === "summary" && <><Rights item={item} /><Metadata values={item.provenance ?? { 来源: null }} />{revision && <><h3 className="text-sm font-semibold">所选不可变素材版本 · v{revision.revision_no} · #{revision.id}</h3><Metadata values={{ 状态: revision.status, 内容哈希: revision.content_hash ?? revision.checksum, 权利状态: revision.rights_status, 公开使用: revision.status === "revoked" ? "revoked" : revision.rights?.public_use ?? revision.public_use_allowed, 模型使用: revision.status === "revoked" ? "revoked" : revision.rights?.model_use ?? revision.model_use_allowed, 商业使用: revision.status === "revoked" ? "revoked" : revision.rights?.commercial_use ?? revision.commercial_use_allowed, 署名要求存在: revision.attribution_present, 来源: revision.source_kind, 来源网址: revision.source_url, Provider: revision.provider_key }} /><MaterialPreview key={revision.id} item={item} revision={revision} /></>}</>}
    {panel === "usage" && <Usage item={item} />}{panel === "revisions" && <MaterialVersions item={item} onRevision={(value) => { setSelectedRevisionId(value.id); setReuse(false); setPanel("summary"); }} />}
    {panel === "content" && item.type === "source" && <Read<SourceDetail> path={`/sources/${item.id}`}>{(source) => <div className="space-y-3"><Metadata values={{ 解析: source.parse_status, 来源类型: source.source_type, 资料日期: source.as_of, 信任等级: source.trust_level, 校验和: source.sha256 }} /><pre className="max-h-72 overflow-auto whitespace-pre-wrap break-words rounded-lg bg-slate-50 p-3 text-sm">{source.raw_text ?? "正文缺失"}</pre><h3 className="text-sm font-semibold">提取事实 · {source.facts?.length ?? "数量未知"}</h3>{source.facts?.slice(0, 20).map((fact) => <p key={fact.id} className="text-sm">#{fact.id} · {fact.statement} · <StatusBadge status={fact.status} /></p>)}{(source.facts?.length ?? 0) > 20 && <p className="text-xs text-slate-500">这里仅展示前 20 条；更多事实请在来源管理中核对。</p>}</div>}</Read>}
    {panel === "content" && item.type === "fact_pack" && <Read<FactPackDetail> path={`/fact-packs/${item.id}`}>{(pack) => <Metadata values={{ 版本: pack.version, 状态: pack.status, 校验和: pack.checksum, 证据条数: pack.items?.length }} />}</Read>}
    <div className="flex flex-wrap gap-3"><Button variant="secondary" disabled={action.busy} onClick={() => void action.refresh()}>刷新详情与所选版本</Button><Link className={linkClass} to={legacy}>{item.type === "material" ? "打开素材上传 / 搜索 / 生成工具" : item.type === "source" ? "打开来源导入 / 事实管理" : "打开 FactPack 编辑器"}</Link><Button variant="secondary" disabled={item.status === "archived"} onClick={() => setReuse(!reuse)}>{reuse ? "收起项目引用" : "明确引用到项目"}</Button>{item.type === "source" && <Button variant="danger" disabled={!canWrite || item.status === "archived" || action.disabled} onClick={() => { if (window.confirm("确认归档此系统共享来源？历史证据与已有引用仍保留。")) void action.run(() => api.patch(`/sources/${item.id}`, { is_archived: true }), "后端已确认归档来源。"); }}>归档共享来源</Button>}</div>{reuse && <ProjectReuse key={`${item.type}:${item.id}:${JSON.stringify(revision ?? null)}`} item={item} revision={revision} canWrite={canWrite} />}<ActionState action={action} />
  </section>;
}

function CollectionForm({ collection, canWrite, action }: { collection: KnowledgeCollection; canWrite: boolean; action: LibraryAction }) {
  return <form className="space-y-3" onSubmit={(event) => {
    event.preventDefault(); if (!canWrite || collection.status === "archived" || action.disabled) return;
    const data = new FormData(event.currentTarget);
    void action.run(() => api.patch(`/knowledge-collections/${collection.id}`, { name: String(data.get("name")).trim(), description: String(data.get("description") ?? "").trim(), expected_revision: collection.revision }), "后端已确认集合信息。");
  }}><Field label="集合名称"><input name="name" defaultValue={collection.name} required maxLength={200} className={inputClass} disabled={!canWrite || collection.status === "archived" || action.disabled} /></Field><Field label="用途说明"><textarea name="description" defaultValue={collection.description ?? ""} maxLength={5000} className={inputClass} disabled={!canWrite || collection.status === "archived" || action.disabled} /></Field><Button type="submit" disabled={!canWrite || collection.status === "archived" || action.disabled}>保存集合信息</Button></form>;
}
function AddMember({ collection, action, disabled }: { collection: KnowledgeCollection; action: LibraryAction; disabled: boolean }) {
  const readCollection = useLibraryRead<KnowledgeCollection>(`/knowledge-collections/${collection.id}`);
  const [chosenRevision, setChosenRevision] = useState<number>();
  const [type, setType] = useState<"source" | "fact_pack">("source");
  const [search, setSearch] = useState("");
  const [q, setQ] = useState("");
  const [offset, setOffset] = useState(0);
  const [chosen, setChosen] = useState<LibraryItem>();
  const selectionDisabled = disabled || !readCollection.isSuccess || readCollection.isFetching || readCollection.data.revision !== collection.revision;
  const path = `/system-library?${libraryQuery({ type, q, offset, limit: 10 })}`;
  const query = useQuery({ queryKey: ["system-library", currentUser(), path], queryFn: async () => checkedPage(await api.get<LibraryPage<LibraryItem>>(path)), retry: false });
  return <div className="space-y-3 rounded-lg border p-4"><h3 className="text-sm font-semibold">添加来源 / 精确 FactPack 版本引用</h3><form onSubmit={(event) => { event.preventDefault(); setQ(search.trim()); setOffset(0); setChosen(undefined); }} className="flex flex-wrap gap-2"><select aria-label="成员资源类型" className={inputClass} value={type} onChange={(event) => { setType(event.target.value as "source" | "fact_pack"); setOffset(0); setChosen(undefined); }}><option value="source">文档与网页</option><option value="fact_pack">FactPack</option></select><input aria-label="搜索成员资源" className={inputClass} value={search} onChange={(event) => setSearch(event.target.value)} placeholder="搜索标题" /><Button type="submit" variant="secondary">搜索</Button></form>{query.isPending && <Spinner label="读取可引用资源…" />}{query.isError && <ReadError error={query.error} retry={() => void query.refetch()} />}{query.isSuccess && <><div className="space-y-2">{query.data.items.length ? query.data.items.map((resource) => <label key={`${resource.type}:${resource.id}`} className="flex items-center gap-2 rounded-lg border p-3 text-sm"><input type="radio" name={`collection-resource-${collection.id}`} checked={chosen?.id === resource.id && chosen.type === resource.type} disabled={selectionDisabled || resource.status === "archived"} onChange={() => { setChosen(resource); setChosenRevision(readCollection.data?.revision); }} />{resource.title} · #{resource.id}{resource.version ? ` v${resource.version}` : ""} · <StatusBadge status={resource.status} /></label>) : <EmptyState title="没有匹配的可引用资源" />}</div><Pagination page={query.data} offset={offset} change={(next) => { setOffset(next); setChosen(undefined); }} /></>}<Button disabled={selectionDisabled || !chosen || chosen.status === "archived" || chosenRevision !== readCollection.data?.revision} onClick={() => { if (!selectionDisabled && chosen && chosenRevision === readCollection.data?.revision) void action.run(() => api.post(`/knowledge-collections/${collection.id}/items`, { ...membershipPayload(type, chosen.id), expected_revision: chosenRevision }), "后端已确认集合成员引用。"); }}>添加所选资源</Button><p className="text-xs text-slate-500">只保存引用；添加 FactPack 不会冻结它或授权发布。</p></div>;
}
function MemberEditor({ item, collection, action, disabled: parentDisabled, inspect }: { item: CollectionItem; collection: KnowledgeCollection; action: LibraryAction; disabled: boolean; inspect: (type: "source" | "fact_pack", id: number) => void }) {
  const disabled = parentDisabled || !Number.isSafeInteger(item.collection_revision) || item.collection_revision !== collection.revision;
  const [note, setNote] = useState(item.note ?? "");
  const [sortOrder, setSortOrder] = useState(String(item.sort_order));
  // Collection revision and member values can arrive in separate query responses.
  useEffect(() => { setNote(item.note ?? ""); setSortOrder(String(item.sort_order)); }, [item.id, item.note, item.sort_order]);
  const resource = collectionResource(item);
  const summary = useLibraryRead<LibraryItem>(`/system-library/${resource.type}/${resource.id}`);
  const archived = summary.isSuccess && summary.data.status === "archived";
  return <article className="space-y-3 rounded-lg border p-4"><div className="flex flex-wrap items-center justify-between gap-2"><button type="button" className={linkClass} onClick={() => inspect(resource.type, resource.id)}>{summary.data?.title ?? item.title ?? item.resource?.title ?? `${libraryLabels[resource.type]} #${resource.id}`}</button><StatusBadge status={item.status} /></div>{summary.isPending && <p className="text-xs text-slate-500">读取成员真实标题与状态…</p>}{summary.isError && <ReadError error={summary.error} retry={() => void summary.refetch()} />}<p className="text-xs text-slate-500">集合条目 #{item.id} · {libraryLabels[resource.type]} #{resource.id} · 顺序 {item.sort_order}{archived ? " · 原资源已归档" : ""}</p><form className="space-y-2" onSubmit={(event) => {
    event.preventDefault(); if (disabled || item.status !== "active") return;
    const order = Number(sortOrder);
    if (!Number.isSafeInteger(order) || order < 0 || order > 1000000) return;
    void action.run(() => api.patch(`/knowledge-collections/${collection.id}/items/${item.id}`, { note: note.trim(), sort_order: order, expected_revision: item.collection_revision }), "后端已确认条目备注与顺序。");
  }}><Field label="条目备注"><textarea className={inputClass} name="note" value={note} onChange={(event) => setNote(event.target.value)} maxLength={5000} disabled={disabled || item.status !== "active"} /></Field><Field label="排序位置"><input className={inputClass} type="number" min={0} max={1000000} step={1} required name="sort_order" value={sortOrder} onChange={(event) => setSortOrder(event.target.value)} disabled={disabled || item.status !== "active"} /></Field><div className="flex gap-2"><Button type="submit" variant="secondary" size="sm" disabled={disabled || item.status !== "active"}>保存备注 / 顺序</Button>{item.status === "active" ? <Button variant="danger" size="sm" disabled={disabled} onClick={() => { if (window.confirm("只解除集合成员引用，保留原资源与历史，确认？")) void action.run(() => api.del(`/knowledge-collections/${collection.id}/items/${item.id}?expected_revision=${item.collection_revision}`), "后端已确认解除集合成员引用。"); }}>解除引用</Button> : <Button variant="secondary" size="sm" disabled={disabled || !summary.isSuccess || archived} onClick={() => void action.run(() => api.post(`/knowledge-collections/${collection.id}/items`, { ...membershipPayload(resource.type, resource.id), note: item.note, sort_order: item.sort_order, expected_revision: item.collection_revision }), "后端已确认重新启用原条目。")} >重新启用原引用</Button>}</div></form></article>;
}
function CollectionItems({ collection, canWrite, action, inspect }: { collection: KnowledgeCollection; canWrite: boolean; action: LibraryAction; inspect: (type: "source" | "fact_pack", id: number) => void }) {
  const [offset, setOffset] = useState(0);
  const [status, setStatus] = useState("active");
  const [adding, setAdding] = useState(false);
  const path = `/knowledge-collections/${collection.id}/items?${libraryQuery({ status, offset, limit: PAGE_SIZE })}`;
  const query = useQuery({ queryKey: ["system-library", currentUser(), path], queryFn: async () => {
    const page = await api.get<CollectionPage>(path); checkedPage(page); return page;
  }, retry: false });
  const snapshotRevision = collectionSnapshotRevision(query.data);
  const disabled = !canWrite || collection.status === "archived" || action.disabled || !query.isSuccess || query.isFetching || snapshotRevision !== collection.revision;
  async function move(index: number, direction: -1 | 1) {
    if (disabled || !snapshotRevision || !query.isSuccess || status !== "active" || offset !== 0 || query.data.items.length !== query.data.total || query.data.items.some((item) => item.status !== "active")) return;
    const item_ids = query.data.items.map((item) => item.id);
    const target = index + direction;
    if (target < 0 || target >= item_ids.length) return;
    [item_ids[index], item_ids[target]] = [item_ids[target], item_ids[index]];
    if (window.confirm(`确认保存全部 ${item_ids.length} 条有效成员的新顺序？`)) await action.run(() => api.post(`/knowledge-collections/${collection.id}/reorder`, { item_ids, expected_revision: snapshotRevision }), "后端已确认完整成员顺序。");
  }
  return <div className="space-y-4"><div className="flex flex-wrap gap-2"><select aria-label="成员状态" value={status} className={inputClass} onChange={(event) => { setStatus(event.target.value); setOffset(0); }}><option value="active">当前引用</option><option value="detached">已解除引用</option></select><Button variant="secondary" disabled={disabled} onClick={() => setAdding(!adding)}>添加资源引用</Button></div>{query.isSuccess && snapshotRevision !== collection.revision && <div className="space-y-2"><ErrorBanner message="成员快照与集合修订不一致，不能用旧成员值提交新修订号。" /><Button variant="secondary" disabled={action.busy} onClick={() => void action.refresh()}>重新读取集合与成员</Button></div>}{adding && <AddMember collection={collection} action={action} disabled={disabled} />}{query.isPending && <Spinner label="读取本页集合成员…" />}{query.isError && <ReadError error={query.error} retry={() => void query.refetch()} />}{query.isSuccess && <>{query.data.items.length ? query.data.items.map((item, index) => <div key={`${item.id}:${item.collection_revision}`} className="space-y-2"><MemberEditor item={item} collection={collection} action={action} disabled={disabled} inspect={inspect} />{status === "active" && offset === 0 && query.data.items.length === query.data.total && <div className="flex gap-2"><Button variant="secondary" size="sm" disabled={disabled || index === 0} onClick={() => void move(index, -1)}>上移并确认完整顺序</Button><Button variant="secondary" size="sm" disabled={disabled || index === query.data.items.length - 1} onClick={() => void move(index, 1)}>下移并确认完整顺序</Button></div>}</div>) : <EmptyState title="本页没有集合成员" />}<Pagination page={query.data} offset={offset} change={setOffset} />{status === "active" && <><p className="text-xs text-slate-500">完整重排要求一次确认全部有效成员；分页集合可逐条明确编辑排序位置。</p></>}</>}</div>;
}
function CollectionDetail({ id, canWrite, inspect }: { id: number; canWrite: boolean; inspect: (type: "source" | "fact_pack", id: number) => void }) {
  const query = useLibraryRead<KnowledgeCollection>(`/knowledge-collections/${id}`);
  const action = useLibraryAction();
  if (query.isPending) return <Spinner label="读取集合及当前修订…" />;
  if (query.isError) return <ReadError error={query.error} retry={() => void query.refetch()} />;
  const collection = query.data;
  if (!Number.isSafeInteger(collection.revision) || collection.revision < 1) return <ErrorBanner message="集合修订号缺失，不能安全保存。请刷新或检查接口。" />;
  return <section className={box}><div className="flex items-center justify-between gap-2"><div><p className="text-xs text-slate-500">知识集合 · 系统共享 · #{id} · 修订 {collection.revision}</p><h2 className="text-xl font-semibold">{collection.name}</h2></div><StatusBadge status={collection.status} /></div><p className="text-sm text-slate-600">集合只组织来源和精确 FactPack 引用。用于项目时，请打开具体成员并明确绑定；集合本身不能绑定为事实边界。</p><CollectionForm key={collection.revision} collection={collection} canWrite={canWrite} action={action} /><ActionState action={action} /><CollectionItems collection={collection} canWrite={canWrite} action={action} inspect={inspect} /><Button variant="danger" disabled={!canWrite || collection.status === "archived" || action.disabled} onClick={() => { if (window.confirm("确认归档此系统共享集合？归档后所有成员只可查看，原资源与历史仍保留。")) void action.run(() => api.del(`/knowledge-collections/${id}?expected_revision=${collection.revision}`), "后端已确认归档集合。"); }}>归档集合</Button>{collection.status === "archived" && <p className="text-sm text-amber-800">已归档集合只可查看；成员编辑、排序、解除和重新启用均已停用。</p>}</section>;
}
function NewCollection({ canWrite, created }: { canWrite: boolean; created: (id: number) => void }) {
  const action = useLibraryAction();
  return <form className={box} onSubmit={async (event) => {
    event.preventDefault(); if (!canWrite || action.disabled) return;
    const data = new FormData(event.currentTarget); let id: number | undefined;
    const saved = await action.run(async () => { const row = await api.post<KnowledgeCollection>("/knowledge-collections", { name: String(data.get("name")).trim(), description: String(data.get("description") ?? "").trim() }); id = row.id; }, "后端已确认创建集合。");
    if (saved && id) created(id);
  }}><h2 className="font-semibold">新建知识集合</h2><Field label="名称"><input name="name" required maxLength={200} className={inputClass} disabled={!canWrite || action.disabled} /></Field><Field label="用途说明"><textarea name="description" maxLength={5000} className={inputClass} disabled={!canWrite || action.disabled} /></Field><Button type="submit" disabled={!canWrite || action.disabled}>{action.busy ? "创建中…" : "创建引用集合"}</Button><ActionState action={action} /></form>;
}

function AssetsWorkspace() {
  const refreshAction = useLibraryAction();
  const [params, setParams] = useSearchParams();
  const requestedTab = params.get("tab") ?? "all";
  const tab: LibraryTab = libraryTabs.includes(requestedTab as LibraryTab) ? requestedTab as LibraryTab : "all";
  const [qInput, setQInput] = useState(params.get("q") ?? "");
  const [offset, setOffset] = useState(0);
  const [status, setStatus] = useState("");
  const [kind, setKind] = useState("");
  const [sourceType, setSourceType] = useState("");
  useEffect(() => { setQInput(params.get("q") ?? ""); }, [params]);
  const [rights, setRights] = useState("");
  const [newCollection, setNewCollection] = useState(false);
  const [showProvider, setShowProvider] = useState(false);
  const [selected, setSelected] = useState<LibraryItem>();
  const [selectedCollection, setSelectedCollection] = useState<number>();
  const [referenced, setReferenced] = useState<{ type: "source" | "fact_pack"; id: number }>();
  const me = useLibraryRead<LibraryUser>("/users/me");
  const canWrite = me.isSuccess && ["admin", "editor"].includes(me.data.role);
  const path = `/system-library?${libraryQuery({ type: tab === "all" ? undefined : tab, q: params.get("q") ?? "", status, source_type: tab === "source" ? sourceType : undefined, material_kind: tab === "material" ? kind : undefined, rights: tab === "material" || tab === "fact_pack" ? rights : undefined, limit: PAGE_SIZE, offset })}`;
  const list = useQuery({ queryKey: ["system-library", currentUser(), path], queryFn: async () => checkedPage(await api.get<LibraryPage<LibraryItem>>(path)), retry: false });
  function choose(item: LibraryItem) { setNewCollection(false); setSelected(item); setReferenced(undefined); setSelectedCollection(item.type === "knowledge_collection" ? item.id : undefined); }
  function changeTab(next: LibraryTab) { setParams({ tab: next, ...(params.get("q") ? { q: params.get("q")! } : {}) }); setOffset(0); setStatus(""); setKind(""); setSourceType(""); setRights(""); setReferenced(undefined); setSelected(undefined); setSelectedCollection(undefined); setNewCollection(false); }
  const latestSelection = selected ? list.data?.items.find((item) => item.type === selected.type && item.id === selected.id) ?? selected : undefined;
  async function inspect(type: "source" | "fact_pack", id: number) {
    setSelected(undefined); setReferenced({ type, id }); setSelectedCollection(undefined);
  }
  return <main className="mx-auto max-w-7xl space-y-6 px-6 py-9"><header><p className="text-xs font-semibold tracking-widest text-indigo-600">System Library</p><h1 className="mt-2 text-3xl font-semibold">素材与知识</h1><p className="mt-2 text-sm text-slate-500">系统共享资源 · 保留原始真源、精确版本与权利依据 · 项目只保存明确引用。</p></header><nav role="tablist" aria-label="素材与知识分区" className="flex gap-2 overflow-x-auto border-b">{libraryTabs.map((key) => <button type="button" role="tab" aria-selected={tab === key} key={key} className={`whitespace-nowrap border-b-2 px-4 py-3 text-sm ${tab === key ? "border-indigo-600 text-indigo-700" : "border-transparent text-slate-500"}`} onClick={() => changeTab(key)}>{libraryLabels[key]}</button>)}</nav>
    {me.isError && <ReadError error={me.error} retry={() => void me.refetch()} />}{me.isPending && <p className="text-xs text-slate-500">正在确认当前用户权限，写入暂不可用。</p>}{me.isSuccess && !canWrite && <p className="rounded-lg bg-slate-100 p-3 text-sm text-slate-600">当前角色 {me.data.role} 只可查看，不能修改共享资源或项目引用。</p>}
    <div className="flex flex-wrap gap-4">{(tab === "all" || tab === "material") && <Link className={linkClass} to="/materials">素材上传 / AI 生成 / 网络搜索</Link>}{(tab === "all" || tab === "source") && <Link className={linkClass} to="/sources">导入文档 / 网页 / 提取事实</Link>}{(tab === "all" || tab === "fact_pack") && <Link className={linkClass} to="/fact-packs">新建 / 编辑 / 冻结证据包</Link>}{(tab === "all" || tab === "knowledge_collection") && <Button disabled={!canWrite} variant="secondary" onClick={() => { setNewCollection(!newCollection); setReferenced(undefined); setSelected(undefined); setSelectedCollection(undefined); }}>新建知识集合</Button>}</div>
    <form className="flex flex-wrap items-end gap-3 rounded-xl border bg-white p-4" onSubmit={(event) => { event.preventDefault(); setParams({ tab, q: qInput.trim() }); setOffset(0); setReferenced(undefined); setSelected(undefined); setSelectedCollection(undefined); }}><Field label="搜索标题"><input className={inputClass} value={qInput} onChange={(event) => setQInput(event.target.value)} placeholder="按真实资源元数据搜索" /></Field><Field label="状态"><select className={inputClass} value={status} onChange={(event) => { setStatus(event.target.value); setOffset(0); }}><option value="">全部状态</option>{tab !== "fact_pack" && <option value="active">有效</option>}{(tab === "all" || tab === "fact_pack") && <><option value="draft">草稿</option><option value="frozen">已冻结</option></>}<option value="archived">已归档</option></select></Field>{tab === "material" && <Field label="素材类型"><select className={inputClass} value={kind} onChange={(event) => { setKind(event.target.value); setOffset(0); }}><option value="">全部类型</option>{materialKinds.map((value) => <option key={value}>{value}</option>)}</select></Field>}{tab === "source" && <Field label="来源类型"><select className={inputClass} value={sourceType} onChange={(event) => { setSourceType(event.target.value); setOffset(0); }}><option value="">全部类型</option>{["text", "markdown", "file", "url", "api"].map((value) => <option key={value}>{value}</option>)}</select></Field>}{(tab === "material" || tab === "fact_pack") && <Field label="公开使用权利"><select className={inputClass} value={rights} onChange={(event) => { setRights(event.target.value); setOffset(0); }}><option value="">所有权利状态</option><option value="allowed">允许</option><option value="denied">不允许</option><option value="unknown">未知</option><option value="revoked">已撤销</option></select></Field>}<Button type="submit" variant="secondary">搜索</Button><Button variant="secondary" disabled={refreshAction.busy} onClick={() => void refreshAction.refresh()}>刷新列表与详情</Button></form>
    {(tab === "all" || tab === "material") && <Button variant="secondary" disabled={!canWrite} onClick={() => setShowProvider(!showProvider)}>生成素材预览与接受</Button>}
    {showProvider && canWrite && <Suspense fallback={<Spinner label="加载素材能力…" />}><ProviderMediaPanel /></Suspense>}
    <ActionState action={refreshAction} /><div className="grid items-start gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)]"><section role="tabpanel" aria-label={libraryLabels[tab]} className={box}>{list.isPending && <Spinner label="读取本页共享资源…" />}{list.isError && <ReadError error={list.error} retry={() => void list.refetch()} />}{list.isSuccess && <>{list.data.items.length ? <ul className="space-y-3">{list.data.items.map((item) => <li key={`${item.type}:${item.id}`}><button type="button" onClick={() => choose(item)} className={`w-full rounded-xl border p-4 text-left transition-colors hover:border-indigo-400 ${selected?.type === item.type && selected.id === item.id ? "border-indigo-500 bg-indigo-50" : "border-slate-200"}`}><div className="flex items-center justify-between gap-2"><h2 className="font-semibold">{item.title}</h2><StatusBadge status={item.status} /></div><p className="mt-2 text-xs text-slate-500">{libraryLabels[item.type]} · #{item.id} · {item.scope === "system_shared" ? "系统共享" : "范围未确认"}{item.latest_revision ? ` · 最新 v${item.latest_revision.revision_no}` : item.version ? ` · v${item.version}` : ""}</p>{item.type === "source" && <p className="mt-2 text-xs text-amber-800">公开使用权利：来源层尚未决定</p>}</button></li>)}</ul> : <EmptyState title="没有匹配的共享资源" hint="调整搜索或筛选，或通过现有导入工具创建资源。" />}<Pagination page={list.data} offset={offset} change={setOffset} /></>}</section><div className="min-w-0 space-y-4">{newCollection && <NewCollection canWrite={canWrite} created={(id) => { setNewCollection(false); setSelectedCollection(id); }} />}{selectedCollection !== undefined ? <CollectionDetail key={selectedCollection} id={selectedCollection} canWrite={canWrite} inspect={(type, id) => void inspect(type, id)} /> : referenced ? <Read<LibraryItem> key={`${referenced.type}:${referenced.id}`} path={`/system-library/${referenced.type}/${referenced.id}`}>{(item) => <ResourceDetail item={item} canWrite={canWrite} />}</Read> : latestSelection && latestSelection.type !== "knowledge_collection" ? <Read<LibraryItem> key={`${latestSelection.type}:${latestSelection.id}`} path={`/system-library/${latestSelection.type}/${latestSelection.id}`}>{(item) => <ResourceDetail key={`${item.type}:${item.id}`} item={item} canWrite={canWrite} />}</Read> : !newCollection && <div className={box}><EmptyState title="选择资源查看详情" hint="正文、媒体、版本与使用记录只在明确操作后读取。" /></div>}</div></div>
  </main>;
}

export default function SystemAssetsKnowledgePage() { return <AssetsWorkspace key={currentUser()} />; }
