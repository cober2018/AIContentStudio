import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Film, FolderInput, Image as ImageIcon, Minus, Music, Search, X } from "lucide-react";
import { useRef, useState, type DragEvent, type PointerEvent } from "react";
import { useLocation } from "react-router-dom";
import { api, ApiError, currentUser } from "../api";
import { usePreview } from "./materialLibraryModel";

export const MATERIAL_DRAG = "application/x-aics-material";
export type DraggedMaterial = { material_revision_id: number; title: string };
type Library = "external" | "common" | "project";
type FolderItem = { material_id: number; material_revision_id: number; title: string; kind: string; mime_type: string | null; library: Library; group: string; project_id: number | null; folder: string | null; used_by: number[] };
type FolderTree = { projects: { project_id: number; name: string; pending: number }[]; folders: string[]; items: FolderItem[] };
type SharedAsset = { material_id: number; material_revision_id: number; kind: string; mime_type: string | null; title: string | null };

function errorText(error: unknown) {
  const detail = error instanceof ApiError ? error.detail as { message?: string } | string | undefined : undefined;
  if (typeof detail === "object" && detail?.message) return detail.message;
  return error instanceof Error ? error.message : "操作失败";
}

function formatLabel(mime: string | null) {
  const sub = (mime || "").split("/")[1] || "";
  return ({ jpeg: "JPG", quicktime: "MOV", "svg+xml": "SVG" } as Record<string, string>)[sub] || sub.toUpperCase();
}

function Tile({ id, revisionId, title, mime, onCommon, origin }: { id: number; revisionId?: number; title: string; mime: string | null; onCommon?: () => void; origin?: string }) {
  const kind = mime?.startsWith("video/") ? "video" : mime?.startsWith("image/") ? "image" : null;
  const thumb = usePreview(id, revisionId, "thumb", !!kind);
  const Icon = kind === "video" ? Film : kind === "image" ? ImageIcon : Music;
  return <div ref={thumb.ref} draggable={!!revisionId && !!kind} title={`${title}（拖到分镜表的素材格）`}
    onDragStart={event => { if (!revisionId) return; event.dataTransfer.setData(MATERIAL_DRAG, JSON.stringify({ material_revision_id: revisionId, title } satisfies DraggedMaterial)); event.dataTransfer.effectAllowed = "copy"; }}
    className="group relative aspect-square cursor-grab overflow-hidden rounded-lg bg-ink-100 active:cursor-grabbing">
    {thumb.url ? <img src={thumb.url} alt="" draggable={false} className="absolute inset-0 h-full w-full object-cover" /> : <span className="absolute inset-0 grid place-items-center text-ink-400"><Icon size={18} strokeWidth={1.4} /></span>}
    <span className="absolute inset-x-0 top-0 truncate bg-ink-950/60 px-1 py-0.5 text-[10.5px] text-white opacity-0 group-hover:opacity-100">{title}</span>
    {onCommon && <button type="button" aria-label="归入通用素材库" title="归入通用素材库" onClick={onCommon} className="absolute left-1 top-1 hidden rounded bg-ink-950/60 p-0.5 text-white group-hover:block"><FolderInput size={12} /></button>}
    {origin && <span className="absolute bottom-1 left-1 max-w-[60%] truncate rounded bg-accent-600/85 px-1 py-px text-[10px] leading-tight text-white" title={origin}>{origin}</span>}
    {kind && <span className="absolute bottom-1 right-1 rounded bg-ink-950/55 px-1 py-px text-[10px] leading-tight text-white">{kind === "video" ? "视频" : "图片"} {formatLabel(mime)}</span>}
  </div>;
}

export default function MaterialLibraryFloat() {
  const location = useLocation();
  const projectId = Number(location.pathname.match(/^\/projects\/(\d+)/)?.[1]) || null;
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [tab, setTab] = useState<Library | "work">("external");
  const [folderProject, setFolderProject] = useState<number | null>(null);
  const [folder, setFolder] = useState<string | null>(null);
  const [moveError, setMoveError] = useState<string | null>(null);
  const [q, setQ] = useState("");
  const [position, setPosition] = useState<{ right: number; bottom: number }>({ right: 20, bottom: 76 });
  const drag = useRef<{ x: number; y: number; right: number; bottom: number } | null>(null);
  const [dropping, setDropping] = useState(false);
  const [upload, setUpload] = useState<{ done: number; total: number; errors: string[] } | null>(null);
  const storage = useQuery({ queryKey: ["storage-settings", currentUser()], enabled: open, retry: false,
    queryFn: () => api.get<{ library: { path: string | null; reachable: boolean } }>("/settings/storage") });
  const tree = useQuery({ queryKey: ["material-float", currentUser()], enabled: open && tab !== "work", retry: false,
    queryFn: () => api.get<FolderTree>("/material-folders") });
  const shared = useQuery({ queryKey: ["material-float-project", currentUser(), projectId], enabled: open && tab === "work" && !!projectId, retry: false,
    queryFn: () => api.get<SharedAsset[]>(`/content-projects/${projectId}/shared-assets?exclude_outputs=true`) });

  function startMove(event: PointerEvent<HTMLElement>) {
    if ((event.target as HTMLElement).closest("button,input")) return;
    drag.current = { x: event.clientX, y: event.clientY, ...position };
    event.currentTarget.setPointerCapture(event.pointerId);
  }
  function move(event: PointerEvent<HTMLElement>) {
    if (!drag.current) return;
    const right = Math.max(0, Math.min(window.innerWidth - 120, drag.current.right - (event.clientX - drag.current.x)));
    const bottom = Math.max(0, Math.min(window.innerHeight - 60, drag.current.bottom - (event.clientY - drag.current.y)));
    setPosition({ right, bottom });
  }

  async function dropFiles(event: DragEvent<HTMLElement>) {
    event.preventDefault(); setDropping(false);
    const files = Array.from(event.dataTransfer.files);
    if (!files.length) return;
    setUpload({ done: 0, total: files.length, errors: [] });
    for (const file of files) {
      const kind = file.type.startsWith("video/") ? "video" : file.type.startsWith("audio/") ? "audio" : "image";
      // Files dropped from the user's own disk are treated like 自己拍摄或制作 in the upload form.
      const params = new URLSearchParams({ kind, title: file.name, source_kind: "upload", rights_status: "cleared",
        public_use_allowed: "true", model_use_allowed: "true", attribution_text: "自己拍摄或制作" });
      const body = new FormData(); body.append("file", file);
      try { await api.upload(`/materials/upload?${params}`, body); }
      catch (error) { setUpload(current => current && { ...current, errors: [...current.errors, `${file.name}：${errorText(error)}`] }); }
      setUpload(current => current && { ...current, done: current.done + 1 });
    }
    setTab("external");
    await queryClient.invalidateQueries({ queryKey: ["material-float"] });
  }

  if (!open) return <button type="button" onClick={() => setOpen(true)} aria-label="打开素材库"
    className="fixed bottom-[76px] right-5 z-[69] inline-flex items-center gap-2 rounded-pill border border-ink-200 bg-surface/95 py-2 pl-3 pr-4 text-[13px] text-ink-800 shadow-lift backdrop-blur transition-transform hover:-translate-y-0.5">
    <ImageIcon size={15} className="text-accent-600" />素材库</button>;

  async function toCommon(materialId: number) {
    setMoveError(null);
    try { await api.post(`/materials/${materialId}/to-common`, {}); await queryClient.invalidateQueries({ queryKey: ["material-float"] }); }
    catch (error) { setMoveError(errorText(error)); }
  }

  const projects = tree.data?.projects || [];
  const activeProject = folderProject ?? (projects.find(item => item.project_id === projectId) || projects[0])?.project_id ?? null;
  const needle = q.trim().toLowerCase();
  const names = new Map(projects.map(item => [item.project_id, item.name]));
  // A project shows its own folder plus what it reuses: shortcuts to other projects' files and 通用素材库 files.
  const reused = (item: FolderItem) => tab === "project" && item.project_id !== activeProject && activeProject !== null && item.used_by.includes(activeProject) && !folder;
  const items: { id: number; revisionId?: number; title: string; mime: string | null; onCommon?: () => void; origin?: string }[] = tab === "work"
    ? (shared.data || []).filter(item => ["image", "video"].includes(item.kind)).map(item => ({ id: item.material_id, revisionId: item.material_revision_id, title: item.title || `素材 #${item.material_id}`, mime: item.mime_type }))
    : (tree.data?.items || []).filter(item => (reused(item) || (item.library === tab && (tab !== "project" || (item.project_id === activeProject && (!folder || item.folder === folder)))))
        && (!needle || item.title.toLowerCase().includes(needle)))
      .map(item => ({ id: item.material_id, revisionId: item.material_revision_id, title: item.title, mime: item.mime_type ?? (item.kind === "audio" ? "audio/" : null),
        onCommon: item.library === "common" ? undefined : () => void toCommon(item.material_id),
        origin: reused(item) ? (item.library === "common" ? "通用" : `来自 ${names.get(item.project_id ?? 0) ?? item.group}`) : undefined }));
  const loading = tab === "work" ? shared.isLoading : tree.isLoading;
  const loadError = tab === "work" ? shared.error : tree.error;
  return <aside aria-label="素材库浮窗" style={{ right: position.right, bottom: position.bottom }}
    onDragOver={event => { if (event.dataTransfer.types.includes("Files")) { event.preventDefault(); setDropping(true); } }}
    onDragLeave={event => { if (!event.currentTarget.contains(event.relatedTarget as Node)) setDropping(false); }}
    onDrop={event => void dropFiles(event)}
    className={`fixed z-[69] flex max-h-[70vh] w-[min(24rem,calc(100vw-2rem))] flex-col rounded-card border bg-surface shadow-lift ${dropping ? "border-accent-500 ring-2 ring-accent-200" : "border-ink-200"}`}>
    <header onPointerDown={startMove} onPointerMove={move} onPointerUp={() => { drag.current = null; }} className="flex cursor-move items-center justify-between gap-2 border-b border-ink-100 px-3 py-2">
      <span className="text-[13px] font-medium text-ink-800">素材库</span>
      <span className="flex gap-1"><button type="button" aria-label="收起素材库" className="rounded p-1 text-ink-500 hover:bg-ink-100" onClick={() => setOpen(false)}><Minus size={14} /></button><button type="button" aria-label="关闭素材库" className="rounded p-1 text-ink-500 hover:bg-ink-100" onClick={() => { setOpen(false); setPosition({ right: 20, bottom: 76 }); }}><X size={14} /></button></span>
    </header>
    <div className="space-y-2 px-3 pt-2">
      <div className="flex items-center gap-1 text-[12.5px]">{([["external", "外部"], ["common", "通用"], ["project", "项目"], ["work", "本作品"]] as const).map(([id, label]) => <button key={id} type="button" disabled={id === "work" && !projectId} onClick={() => setTab(id)} className={`rounded-pill px-3 py-1 ${tab === id ? "bg-ink-900 text-paper" : "text-ink-600 hover:bg-ink-100 disabled:opacity-40"}`}>{label}</button>)}</div>
      {tab === "project" && <div className="space-y-1.5 text-[12px]">
        <select aria-label="项目" value={activeProject ?? ""} onChange={event => { setFolderProject(Number(event.target.value) || null); setFolder(null); }} className="w-full rounded-lg border border-ink-200 bg-surface px-2 py-1">
          {projects.length ? projects.map(item => <option key={item.project_id} value={item.project_id}>{item.name}{item.pending ? `（${item.pending} 个待归档）` : ""}</option>) : <option value="">还没有项目素材</option>}
        </select>
        <div className="flex flex-wrap gap-1">{[null, ...(tree.data?.folders || [])].map(name => <button key={name ?? "all"} type="button" onClick={() => setFolder(name)} className={`rounded px-1.5 py-0.5 ${folder === name ? "bg-accent-100 text-accent-800" : "text-ink-600 hover:bg-ink-100"}`}>{name ?? "全部"}</button>)}</div>
      </div>}
      {tab !== "work" && <label className="flex items-center gap-2 rounded-lg border border-ink-200 px-2 py-1"><Search size={13} className="text-ink-400" /><input value={q} onChange={event => setQ(event.target.value)} placeholder="搜索标题或标签" className="w-full bg-transparent text-[13px] outline-none" /></label>}
      {moveError && <p role="alert" className="text-[12px] text-rose-700">{moveError}</p>}
      {storage.data && !storage.data.library.reachable && <p role="status" className="text-[12px] text-amber-700">素材库未连接：{storage.data.library.path || "还没设置"}。可在「设置 → 存储位置」修改。</p>}
    </div>
    <div className="min-h-[8rem] flex-1 overflow-y-auto p-3">
      {loading ? <p className="text-[12.5px] text-ink-500">读取中…</p> : loadError ? <p className="text-[12.5px] text-rose-700">{errorText(loadError)}</p>
        : items.length ? <div className="grid grid-cols-4 gap-1.5">{items.map(item => <Tile key={`${item.id}:${item.revisionId}`} {...item} />)}</div>
        : <p className="text-[12.5px] text-ink-500">{tab === "work" ? "本作品还没有图片或视频素材。" : tab === "project" ? "这个文件夹还没有素材。" : "没有找到素材。"}</p>}
    </div>
    <footer className="border-t border-ink-100 px-3 py-2 text-[11.5px] text-ink-500">
      {upload ? <span>{upload.done < upload.total ? `正在入库 ${upload.done}/${upload.total}…` : `已入库 ${upload.total - upload.errors.length}/${upload.total}`}{upload.errors.map(item => <span key={item} className="block text-rose-700">{item}</span>)}</span>
        : "把素材拖到分镜表的素材格就会用在那个镜头；从访达把文件拖进来就入库。"}
    </footer>
  </aside>;
}
