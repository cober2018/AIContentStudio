import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ExternalLink, HardDrive } from "lucide-react";
import { ReactNode, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, currentUser } from "../api";
import { Button, Chip, Drawer, ErrorBanner, Field, Notice, Spinner, inputClass } from "../components/ui";
import FileLocationActions from "./FileLocationActions";
import { readableTime } from "./HomePage";
import { Collection, DRIVE_STATUS, KIND_LABELS, LibraryMaterial, SOURCE_LABELS, duration, mediaKind, rightsSummary } from "./materialLibraryModel";

type Revision = {
  id: number; revision_no: number; status: string; source_kind: string; source_url: string | null; content_hash: string;
  mime_type: string | null; width: number | null; height: number | null; duration_ms: number | null;
  drive: { source_id: number; relative_path: string } | null; rights_status: string | null;
  public_use_allowed: boolean | null; model_use_allowed: boolean | null; commercial_use_allowed: boolean | null;
  attribution_text: string | null; provider_key: string | null; created_at: string | null;
  metadata: { tags?: string[] };
};
type Detail = { id: number; title: string; kind: string; tags: string[]; revisions: Revision[] };
type Usage = { items: { category: string; id: number; title: string; href: string }[]; total: number };
type Project = { id: number; title: string; status: string };

function errorText(error: unknown) { return error instanceof Error ? error.message : "操作失败"; }
const RIGHTS_STATUS: Record<string, string> = { restricted: "仅限本地审阅", cleared: "自有，权利清楚", licensed: "已获授权", unknown: "未确认" };
const allowed = (value: boolean | null) => value === true ? "允许" : value === false ? "不允许" : "未确认";

function Player({ item, revision }: { item: LibraryMaterial; revision: Revision }) {
  const kind = mediaKind(item);
  const [state, setState] = useState<{ url?: string; error?: string }>({});
  useEffect(() => {
    let active = true;
    setState({});
    if (kind) {
      api.post<{ url: string }>(`/materials/${item.id}/revisions/${revision.id}/stream-session`)
        .then(session => { if (active) setState({ url: session.url }); })
        .catch(error => { if (active) setState({ error: errorText(error) === "material_external_unavailable" ? "硬盘未连接，接上后即可播放。" : errorText(error) }); });
    }
    return () => { active = false; };
  }, [item.id, revision.id, kind]);
  if (!kind) return <Notice>这类文件不能直接预览。</Notice>;
  if (state.error) return <div className="grid aspect-video place-items-center rounded-card bg-ink-100 text-[13px] text-ink-500">{state.error}</div>;
  if (!state.url) return <div className="grid aspect-video place-items-center rounded-card bg-ink-100"><Spinner label="准备预览…" /></div>;
  if (kind === "image") return <img src={state.url} alt={item.title} className="max-h-[56vh] w-full rounded-card bg-ink-100 object-contain" />;
  if (kind === "audio") return <audio controls preload="metadata" src={state.url} className="w-full" />;
  return <div className="relative">
    <video controls preload="metadata" playsInline src={state.url} className="max-h-[56vh] w-full rounded-card bg-ink-950" />
    <FileLocationActions base={`/materials/${item.id}/revisions/${revision.id}`} />
  </div>;
}

function Facts({ rows }: { rows: [string, ReactNode][] }) {
  return <dl className="grid grid-cols-2 gap-x-6 gap-y-3.5">{rows.filter(([, value]) => value !== null && value !== undefined && value !== "").map(([label, value]) =>
    <div key={label} className="min-w-0"><dt className="text-[12px] text-ink-500">{label}</dt><dd className="mt-0.5 break-words text-[13.5px] text-ink-900">{value}</dd></div>)}</dl>;
}

function Block({ title, children }: { title: string; children: ReactNode }) {
  return <section className="border-t border-ink-200/80 pt-6"><h3 className="mb-4 font-serif text-[16px] font-semibold text-ink-900">{title}</h3>{children}</section>;
}

export default function MaterialDetailDrawer({ materialId, collections, onClose }: { materialId: number; collections: Collection[]; onClose: () => void }) {
  const client = useQueryClient();
  const key = ["material-detail", currentUser(), materialId];
  const summary = useQuery({ queryKey: [...key, "summary"], queryFn: () => api.get<LibraryMaterial>(`/system-library/material/${materialId}`), retry: false });
  const detail = useQuery({ queryKey: [...key, "detail"], queryFn: () => api.get<Detail>(`/materials/${materialId}`), retry: false });
  const usage = useQuery({ queryKey: [...key, "usage"], queryFn: () => api.get<Usage>(`/system-library/material/${materialId}/usage`), retry: false });
  const memberOf = useQuery({ queryKey: [...key, "collections"], queryFn: () => api.get<{ items: Collection[] }>(`/materials/${materialId}/collections`), retry: false });
  const projects = useQuery({ queryKey: ["projects", currentUser()], queryFn: () => api.get<Project[]>("/content-projects"), retry: false });
  const [projectId, setProjectId] = useState("");
  const [note, setNote] = useState("");
  const [collectionId, setCollectionId] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ ok?: string; error?: string }>({});
  const item = summary.data;
  const revisions = [...(detail.data?.revisions ?? [])].sort((a, b) => b.revision_no - a.revision_no);
  const revision = revisions[0];
  const run = async (action: () => Promise<unknown>, ok: string) => {
    setBusy(true); setMessage({});
    try { await action(); setMessage({ ok }); await client.invalidateQueries({ queryKey: key }); await client.invalidateQueries({ queryKey: ["material-collections"] }); }
    catch (error) { setMessage({ error: errorText(error) }); }
    finally { setBusy(false); }
  };
  const members = new Set((memberOf.data?.items ?? []).map(entry => entry.id));
  return <Drawer title={item?.title ?? "素材详情"} onClose={onClose}>
    {summary.isPending || detail.isPending ? <Spinner /> : summary.isError || detail.isError || !item || !revision
      ? <ErrorBanner message={errorText(summary.error ?? detail.error ?? new Error("素材不存在"))} /> : <div className="space-y-7">
        <Player item={item} revision={revision} />
        <div className="flex flex-wrap gap-2">
          <Chip tone={rightsSummary(item).tone}>{rightsSummary(item).label}</Chip>
          <Chip>{KIND_LABELS[item.kind] ?? item.kind}</Chip>
          {item.drive && <Chip tone={item.drive.status === "available" ? "info" : "warn"}>{DRIVE_STATUS[item.drive.status ?? "unavailable"]}</Chip>}
          {(detail.data?.tags ?? []).map(tag => <Chip key={tag}>#{tag}</Chip>)}
        </div>
        {message.ok && <Notice tone="good">{message.ok}</Notice>}
        {message.error && <ErrorBanner message={message.error} />}

        <Block title="用到项目里">
          <div className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto] sm:items-end">
            <Field label="项目"><select className={inputClass} value={projectId} onChange={event => setProjectId(event.target.value)}>
              <option value="">选择项目</option>{(projects.data ?? []).map(project => <option key={project.id} value={project.id}>{project.title}</option>)}
            </select></Field>
            <Field label="备注（可选）"><input className={inputClass} value={note} maxLength={500} placeholder="例如：第 3 段的证据画面" onChange={event => setNote(event.target.value)} /></Field>
            <Button disabled={busy || !projectId} onClick={() => void run(() => api.post(`/content-projects/${projectId}/materials/references`, { material_revision_id: revision.id, note: note.trim() || null }), `已把 v${revision.revision_no} 加入项目。`)}>加入项目</Button>
          </div>
          <p className="mt-2 text-[12px] text-ink-500">项目引用的是这个精确版本；之后素材有新版本，项目里的引用不会自动变。</p>
        </Block>

        <Block title="存放位置">
          <div className="flex flex-wrap items-center gap-2">
            <Button size="sm" variant="secondary" disabled={busy} onClick={() => void run(async () => { await api.post(`/materials/${materialId}/to-common`, {}); await client.invalidateQueries({ queryKey: ["material-float"] }); }, "已归入通用素材库。")}>归入通用素材库</Button>
            <p className="text-[12px] text-ink-500">通用素材库里的文件不会被项目移走，各项目直接引用。</p>
          </div>
        </Block>

        <Block title="合集">
          <div className="flex flex-wrap items-center gap-2">
            {(memberOf.data?.items ?? []).map(entry => <span key={entry.id} className="inline-flex items-center gap-1.5 rounded-pill border border-ink-200 bg-ink-50 py-0.5 pl-2.5 pr-1 text-[12.5px] text-ink-700">{entry.name}
              <button aria-label={`从合集「${entry.name}」移除`} disabled={busy} className="grid h-5 w-5 place-items-center rounded-full text-ink-500 hover:bg-ink-200 hover:text-ink-900"
                onClick={() => void run(() => api.del(`/material-collections/${entry.id}/items/${materialId}?expected_revision=${entry.revision}`), `已从「${entry.name}」移除。`)}>×</button></span>)}
            {collections.filter(entry => !members.has(entry.id)).length > 0 && <>
              <select aria-label="加入合集" className={`${inputClass} !w-auto !py-1.5 text-[13px]`} value={collectionId} onChange={event => setCollectionId(event.target.value)}>
                <option value="">加入合集…</option>{collections.filter(entry => !members.has(entry.id)).map(entry => <option key={entry.id} value={entry.id}>{entry.name}</option>)}
              </select>
              <Button size="sm" variant="secondary" disabled={busy || !collectionId} onClick={() => { const target = collections.find(entry => String(entry.id) === collectionId)!; setCollectionId(""); void run(() => api.post(`/material-collections/${target.id}/items`, { expected_revision: target.revision, material_id: materialId }), `已加入「${target.name}」。`); }}>加入</Button>
            </>}
            {!collections.length && <p className="text-[13px] text-ink-500">还没有合集，可在「合集」页新建。</p>}
          </div>
        </Block>

        <Block title="文件">
          <Facts rows={[
            ["格式", revision.mime_type],
            ["尺寸", revision.width ? `${revision.width} × ${revision.height}` : null],
            ["时长", duration(revision.duration_ms)],
            ["当前版本", `v${revision.revision_no}`],
            ["位置", revision.drive ? <span className="inline-flex items-start gap-1.5"><HardDrive size={14} className="mt-0.5 shrink-0" />{item.drive?.label ?? "硬盘文件夹"} / {revision.drive.relative_path}</span> : "平台素材存储"],
            ["加入时间", readableTime(revision.created_at ?? item.created_at)],
          ]} />
        </Block>

        <Block title="来源与权利">
          <Facts rows={[
            ["来源", item.drive ? "硬盘文件夹" : SOURCE_LABELS[revision.source_kind] ?? revision.source_kind],
            ["来源网址", revision.source_url ? <a href={revision.source_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 underline">{new URL(revision.source_url).hostname}<ExternalLink size={12} /></a> : null],
            ["公开发布", allowed(revision.public_use_allowed)],
            ["AI 使用", allowed(revision.model_use_allowed)],
            ["商业使用", allowed(revision.commercial_use_allowed)],
            ["权利状态", RIGHTS_STATUS[revision.rights_status ?? ""] ?? revision.rights_status],
          ]} />
          {revision.attribution_text && <div className="mt-4 rounded-xl bg-paper px-4 py-3 text-[13px] leading-relaxed text-ink-700"><p className="eyebrow mb-1">署名</p>{revision.attribution_text}</div>}
        </Block>

        <Block title={`用在哪里${usage.data ? ` · ${usage.data.total}` : ""}`}>
          {usage.isPending ? <Spinner /> : !usage.data?.items.length ? <p className="text-[13px] text-ink-500">还没有项目引用它。</p>
            : <ul className="space-y-2">{usage.data.items.map(entry => <li key={`${entry.category}-${entry.id}`}><Link to={entry.href} className="text-[13.5px] underline">{entry.title}</Link></li>)}</ul>}
        </Block>

        <Block title={`版本 · ${revisions.length}`}>
          <ol className="relative space-y-4 border-l border-ink-200 pl-5">{revisions.map(entry => <li key={entry.id} className="relative">
            <span aria-hidden className={`absolute -left-[25px] top-1.5 h-2 w-2 rounded-full ${entry.id === revision.id ? "bg-accent-500" : "bg-ink-300"}`} />
            <p className="text-[13.5px] text-ink-900">v{entry.revision_no}{entry.id === revision.id ? " · 当前" : ""}{entry.status === "revoked" ? " · 已撤销" : ""}</p>
            <p className="mt-0.5 text-[12px] text-ink-500">{readableTime(entry.created_at ?? "")} · {SOURCE_LABELS[entry.source_kind] ?? entry.source_kind} · {entry.content_hash.slice(0, 10)}</p>
          </li>)}</ol>
          <p className="mt-4 text-[12px] text-ink-500">撤销公开使用等权利操作在 <Link className="underline" to={`/assets?tab=material`}>素材与知识</Link> 中进行。</p>
        </Block>
      </div>}
  </Drawer>;
}
