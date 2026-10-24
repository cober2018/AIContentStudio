import { useInfiniteQuery, useQuery } from "@tanstack/react-query";
import { AudioLines, Film, HardDrive, Image as ImageIcon, Search } from "lucide-react";
import { lazy, Suspense, useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api, currentUser } from "../api";
import { Button, Chip, EmptyState, ErrorBanner, Page, PageHeader, Segmented, Spinner, Tabs, inputClass } from "../components/ui";
import { readableTime } from "./HomePage";
import {
  Collection, DRIVE_STATUS, KIND_LABELS, LibraryMaterial, LibraryPage, SOURCE_LABELS,
  duration, mediaKind, rightsSummary, usePreview,
} from "./materialLibraryModel";

const MaterialDetailDrawer = lazy(() => import("./MaterialDetailDrawer"));
const MaterialDriveFolders = lazy(() => import("./MaterialDriveFolders"));
const MaterialCollections = lazy(() => import("./MaterialCollections"));
const MaterialScriptMatch = lazy(() => import("./MaterialScriptMatch"));
const PAGE = 48;
const TABS = [["all", "全部素材"], ["match", "按文案找素材"], ["drive", "硬盘文件夹"], ["collections", "合集"]] as const;
type Tab = typeof TABS[number][0];

function errorText(error: unknown) { return error instanceof Error ? error.message : "读取失败"; }

function Thumb({ item, large }: { item: LibraryMaterial; large?: boolean }) {
  const kind = mediaKind(item);
  const revision = item.latest_revision;
  const offline = item.drive && item.drive.status !== "available";
  const [hover, setHover] = useState<number | null>(null);
  const thumb = usePreview(item.id, revision?.id, "thumb", !!kind && !offline);
  const strip = usePreview(item.id, revision?.id, "strip", kind === "video" && hover !== null && !offline);
  const Icon = kind === "video" ? Film : kind === "audio" ? AudioLines : ImageIcon;
  return <div ref={thumb.ref}
    className={`relative overflow-hidden bg-ink-100 ${large ? "aspect-[4/3]" : "aspect-[4/3] rounded-[12px]"} ${kind === "audio" ? "!bg-accent-50/60" : ""}`}
    onMouseMove={kind === "video" ? event => { const box = event.currentTarget.getBoundingClientRect(); setHover(Math.min(7, Math.max(0, Math.floor((event.clientX - box.left) / box.width * 8)))); } : undefined}
    onMouseLeave={() => setHover(null)}>
    {thumb.url && <img src={thumb.url} alt="" loading="lazy" decoding="async"
      className={`absolute inset-0 h-full w-full ${kind === "audio" ? "object-contain px-3" : "object-cover"} transition-opacity duration-300 ${hover !== null && strip.url ? "opacity-0" : "opacity-100"}`} />}
    {hover !== null && strip.url && <div aria-hidden className="absolute inset-0 bg-no-repeat"
      style={{ backgroundImage: `url(${strip.url})`, backgroundSize: "800% 100%", backgroundPosition: `${hover / 7 * 100}% 0` }} />}
    {(!thumb.url || offline) && <div className="absolute inset-0 grid place-items-center text-ink-400">
      <div className="flex flex-col items-center gap-2 text-[12px]"><Icon size={22} strokeWidth={1.4} />{offline ? DRIVE_STATUS[item.drive?.status ?? "unavailable"] : thumb.failed ? "无法生成预览" : null}</div>
    </div>}
    {kind === "video" && hover !== null && <div aria-hidden className="absolute inset-x-2 bottom-2 flex gap-0.5">{Array.from({ length: 8 }, (_, index) =>
      <span key={index} className={`h-[3px] flex-1 rounded-full ${index === hover ? "bg-surface" : "bg-surface/40"}`} />)}</div>}
    {revision?.duration_ms && hover === null ? <span className="absolute bottom-2 right-2 rounded-md bg-ink-950/70 px-1.5 py-0.5 font-mono text-[11px] tabular-nums text-white/95">{duration(revision.duration_ms)}</span> : null}
    {kind === "audio" && <span className="absolute left-2 top-2 inline-flex items-center gap-1 rounded-md bg-surface/90 px-1.5 py-0.5 text-[11px] text-accent-700"><AudioLines size={11} />音频</span>}
    {item.drive && <span title={item.drive.label ?? undefined} className="absolute right-2 top-2 inline-flex items-center gap-1 rounded-md bg-ink-950/65 px-1.5 py-0.5 text-[11px] text-white/95"><HardDrive size={11} />硬盘</span>}
  </div>;
}

function Card({ item, open }: { item: LibraryMaterial; open: () => void }) {
  const rights = rightsSummary(item);
  return <button type="button" onClick={open} className="group block w-full min-w-0 animate-rise text-left">
    <div className="transition-transform duration-300 ease-studio group-hover:-translate-y-0.5"><Thumb item={item} /></div>
    <p className="mt-2.5 line-clamp-2 text-[13.5px] leading-snug text-ink-900 group-hover:text-accent-700">{item.title}</p>
    <p className="mt-1 flex items-center gap-1.5 text-[12px] text-ink-500">
      <span aria-hidden className={`h-1.5 w-1.5 shrink-0 rounded-full ${rights.tone === "good" ? "bg-emerald-500" : rights.tone === "warn" ? "bg-amber-500" : rights.tone === "bad" ? "bg-rose-500" : "bg-ink-300"}`} />
      <span className="truncate">{rights.label} · {item.drive ? "硬盘文件夹" : SOURCE_LABELS[item.provenance.source_kind ?? ""] ?? "其他来源"}</span>
    </p>
  </button>;
}

function Row({ item, open }: { item: LibraryMaterial; open: () => void }) {
  const rights = rightsSummary(item);
  const revision = item.latest_revision;
  return <button type="button" onClick={open} className="grid w-full grid-cols-[88px_minmax(0,1fr)] items-center gap-4 px-4 py-3 text-left transition-colors hover:bg-ink-50 sm:grid-cols-[88px_minmax(0,1fr)_120px_120px_110px]">
    <div className="w-[88px]"><Thumb item={item} /></div>
    <div className="min-w-0"><p className="truncate text-[14px] text-ink-900">{item.title}</p><p className="mt-0.5 truncate text-[12px] text-ink-500">{KIND_LABELS[item.kind] ?? item.kind}{revision?.width ? ` · ${revision.width}×${revision.height}` : ""}{revision?.duration_ms ? ` · ${duration(revision.duration_ms)}` : ""} · v{revision?.revision_no ?? "—"}</p></div>
    <span className="hidden text-[12.5px] text-ink-600 sm:block">{item.drive ? "硬盘文件夹" : SOURCE_LABELS[item.provenance.source_kind ?? ""] ?? "其他来源"}</span>
    <span className="hidden sm:block"><Chip tone={rights.tone}>{rights.label}</Chip></span>
    <span className="hidden text-right text-[12px] text-ink-500 sm:block">{readableTime(item.created_at)}</span>
  </button>;
}

function PlaceProject({ value, onChange }: { value: string; onChange: (value: string) => void }) {
  const tree = useQuery({ queryKey: ["material-float", currentUser()], retry: false,
    queryFn: () => api.get<{ projects: { project_id: number; name: string }[] }>("/material-folders") });
  return <select aria-label="项目" className={`${inputClass} !w-auto !py-1.5 text-[13px]`} value={value} onChange={event => onChange(event.target.value)}>
    <option value="">全部项目</option>{(tree.data?.projects ?? []).map(item => <option key={item.project_id} value={item.project_id}>{item.name}</option>)}
  </select>;
}

function Filters({ params, set, collections }: { params: URLSearchParams; set: (key: string, value: string) => void; collections: Collection[] }) {
  const [q, setQ] = useState(params.get("q") ?? "");
  useEffect(() => setQ(params.get("q") ?? ""), [params]);
  const select = (key: string, label: string, options: [string, string][]) => <label className="min-w-0">
    <span className="sr-only">{label}</span>
    <select aria-label={label} className={`${inputClass} !w-auto !py-1.5 text-[13px]`} value={params.get(key) ?? ""} onChange={event => set(key, event.target.value)}>
      <option value="">{label}</option>{options.map(([value, text]) => <option key={value} value={value}>{text}</option>)}
    </select>
  </label>;
  return <div className="space-y-4">
    <div className="flex flex-wrap items-center gap-3">
      <form className="relative min-w-[220px] flex-1" onSubmit={event => { event.preventDefault(); set("q", q.trim()); }}>
        <Search aria-hidden size={15} className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-ink-400" />
        <input aria-label="搜索素材标题" placeholder="搜索标题，回车确认" className={`${inputClass} !pl-9`} value={q} onChange={event => setQ(event.target.value)} />
      </form>
      <Segmented label="存放位置" value={params.get("place") ?? ""} onChange={value => { set("place", value); if (value !== "project") set("place_project", ""); }}
        items={[["", "全部位置"], ["external", "外部素材库"], ["common", "通用素材库"], ["project", "项目素材库"]]} />
      {params.get("place") === "project" && <PlaceProject value={params.get("place_project") ?? ""} onChange={value => set("place_project", value)} />}
      <Segmented label="素材类型" value={params.get("kind") ?? ""} onChange={value => set("kind", value)}
        items={[["", "全部"], ["image", "图片"], ["video", "视频"], ["audio", "音频"], ["screenshot", "截图"]]} />
    </div>
    <div className="-mx-5 flex items-center gap-2 overflow-x-auto px-5 [scrollbar-width:none] sm:mx-0 sm:flex-wrap sm:overflow-visible sm:px-0 [&::-webkit-scrollbar]:hidden [&>*]:shrink-0">
      {select("source", "全部来源", Object.entries(SOURCE_LABELS).filter(([key]) => !["upstream", "legacy", "chart"].includes(key)))}
      {select("public", "公开使用", [["allowed", "可公开"], ["denied", "不可公开"], ["unknown", "未确认"], ["revoked", "已撤销"]])}
      {select("model", "AI 使用", [["allowed", "允许 AI 使用"], ["denied", "不允许"], ["unknown", "未确认"]])}
      {collections.length > 0 && select("collection", "全部合集", collections.map(item => [String(item.id), item.name]))}
      <span className="ml-auto hidden sm:block" />
      {select("order", "最新在前", [["oldest", "最早在前"]])}
      <Segmented label="显示方式" value={params.get("view") ?? "grid"} onChange={value => set("view", value === "grid" ? "" : value)}
        items={[["grid", "网格"], ["list", "列表"]]} />
    </div>
  </div>;
}

function Library({ params, set, collections }: { params: URLSearchParams; set: (key: string, value: string) => void; collections: Collection[] }) {
  const query = new URLSearchParams({ type: "material", status: "active", order: params.get("order") === "oldest" ? "oldest" : "newest", limit: String(PAGE) });
  const map: [string, string][] = [["q", "q"], ["kind", "material_kind"], ["source", "material_source_kind"], ["public", "rights"], ["model", "model_use"], ["collection", "material_collection_id"], ["folder", "material_source_id"], ["place", "place"], ["place_project", "place_project_id"]];
  for (const [from, to] of map) if (params.get(from)) query.set(to, params.get(from)!);
  const base = query.toString();
  const list = useInfiniteQuery({
    queryKey: ["material-library", currentUser(), base],
    queryFn: ({ pageParam }) => api.get<LibraryPage>(`/system-library?${base}&offset=${pageParam}`),
    initialPageParam: 0,
    getNextPageParam: last => last.offset + last.items.length < last.total ? last.offset + last.items.length : undefined,
    retry: false,
  });
  const items = list.data?.pages.flatMap(page => page.items) ?? [];
  const total = list.data?.pages[0]?.total ?? 0;
  const open = (id: number) => set("material", String(id));
  const filtered = map.some(([from]) => params.get(from));
  return <div className="space-y-6">
    <Filters params={params} set={set} collections={collections} />
    {params.get("folder") && <p className="text-[13px] text-ink-600">只看硬盘文件夹 #{params.get("folder")} 中已链接的素材 · <button className="underline" onClick={() => set("folder", "")}>取消</button></p>}
    {list.isPending ? <Spinner label="读取素材…" /> : list.isError ? <ErrorBanner message={errorText(list.error)} /> : !items.length
      ? <EmptyState title={filtered ? "没有符合条件的素材" : "素材库还是空的"} hint={filtered ? "换个筛选条件试试。" : "上传素材，或在「硬盘文件夹」里把移动硬盘中的文件链接进来。"} />
      : <>
        <p className="text-[12.5px] text-ink-500">共 <span className="tabular-nums text-ink-800">{total}</span> 个素材</p>
        {(params.get("view") ?? "grid") === "grid"
          ? <div className="grid grid-cols-2 gap-x-5 gap-y-7 sm:grid-cols-3 lg:grid-cols-4">{items.map(item => <Card key={item.id} item={item} open={() => open(item.id)} />)}</div>
          : <div className="card divide-y divide-ink-200/70 overflow-hidden">{items.map(item => <Row key={item.id} item={item} open={() => open(item.id)} />)}</div>}
        {list.hasNextPage && <div className="flex justify-center"><Button variant="secondary" disabled={list.isFetchingNextPage} onClick={() => void list.fetchNextPage()}>{list.isFetchingNextPage ? "读取中…" : `再看 ${Math.min(PAGE, total - items.length)} 个`}</Button></div>}
      </>}
  </div>;
}

export default function MaterialLibraryPage() {
  const [params, setParams] = useSearchParams();
  const tab = (TABS.some(([key]) => key === params.get("tab")) ? params.get("tab") : "all") as Tab;
  const set = (key: string, value: string) => setParams(current => {
    const next = new URLSearchParams(current);
    if (value) next.set(key, value); else next.delete(key);
    return next;
  });
  const changeTab = (value: Tab) => setParams(value === "all" ? {} : { tab: value });
  const collections = useQuery({ queryKey: ["material-collections", currentUser()], queryFn: () => api.get<{ items: Collection[] }>("/material-collections"), retry: false });
  const materialId = Number(params.get("material")) || null;
  return <><Page>
    <PageHeader eyebrow="资料 · 素材" title="素材库" lead="所有图片、视频和音频都在这里：先看画面和权利，再用到项目里。移动硬盘里的文件原地链接，不占电脑空间。"
      actions={<Button variant="secondary" onClick={() => changeTab("drive")}><HardDrive size={15} className="mr-1.5" />链接硬盘素材</Button>}>
      <Tabs label="素材库分区" value={tab} onChange={changeTab} items={TABS} />
    </PageHeader>
    <Suspense fallback={<Spinner />}>
      {tab === "all" && <Library params={params} set={set} collections={collections.data?.items ?? []} />}
      {tab === "match" && <MaterialScriptMatch runId={Number(params.get("run")) || null} projectId={Number(params.get("project")) || null} unitId={Number(params.get("unit")) || null}
        openRun={id => setParams(current => { const next = new URLSearchParams({ tab: "match" }); for (const key of ["project", "unit"]) { const value = current.get(key); if (value) next.set(key, value); } if (id) next.set("run", String(id)); return next; })}
        scopeTo={(project, unit) => setParams(project ? { tab: "match", project: String(project), ...(unit ? { unit: String(unit) } : {}) } : { tab: "match" })} />}
      {tab === "drive" && <MaterialDriveFolders showLinked={id => setParams({ folder: String(id) })} />}
      {tab === "collections" && <MaterialCollections collections={collections} open={id => setParams({ collection: String(id) })} />}
    </Suspense>
  </Page>{materialId && <Suspense fallback={null}><MaterialDetailDrawer materialId={materialId} collections={collections.data?.items ?? []} onClose={() => set("material", "")} /></Suspense>}</>;
}

