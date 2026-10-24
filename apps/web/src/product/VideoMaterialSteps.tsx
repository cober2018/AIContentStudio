import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { api, ApiError, currentUser } from "../api";
import { Button, ErrorBanner } from "../components/ui";
import { MATERIAL_DRAG, type DraggedMaterial } from "./MaterialLibraryFloat";
import type { VideoPayload } from "./VideoStudioModel";

type Asset = { material_id: number; material_revision_id: number; kind: string; title: string | null; mime_type: string | null };
type Chain = { state: string; locked?: boolean; master: { payload: VideoPayload } | null };

function errorText(error: unknown) {
  const detail = error instanceof ApiError ? error.detail as { message?: string } | string | undefined : undefined;
  return (typeof detail === "string" ? detail : detail?.message) || (error instanceof Error ? error.message : "操作失败");
}

function clock(ms: number) { return `${String(Math.floor(ms / 60000)).padStart(2, "0")}:${((ms % 60000) / 1000).toFixed(1).padStart(4, "0")}`; }

function useVideoChain(projectId: number, unitId: number) {
  return useQuery({ queryKey: ["video-chain", currentUser(), projectId, unitId], retry: false,
    queryFn: () => api.get<Chain>(`/content-projects/${projectId}/units/${unitId}/video-chain`) });
}

function useAssets(projectId: number) {
  return useQuery({ queryKey: ["shared-assets", currentUser(), projectId, "materials"], retry: false,
    queryFn: () => api.get<Asset[]>(`/content-projects/${projectId}/shared-assets?exclude_outputs=true`) });
}

// Raw bytes need the user header, so previews go through a local object URL.
function Preview({ asset }: { asset: Asset }) {
  const [url, setUrl] = useState("");
  const [failed, setFailed] = useState("");
  useEffect(() => {
    let objectUrl = "";
    let alive = true;
    setUrl(""); setFailed("");
    fetch(`/api/v1/materials/${asset.material_id}/revisions/${asset.material_revision_id}/raw`, { headers: { "X-Studio-User": currentUser() } }).then(async response => {
      if (!response.ok) {
        const body = await response.json().catch(() => null) as { detail?: { message?: string } | string } | null;
        if (alive) setFailed((typeof body?.detail === "string" ? body.detail : body?.detail?.message) || "预览读取失败");
        return;
      }
      objectUrl = URL.createObjectURL(await response.blob());
      if (alive) setUrl(objectUrl);
    }).catch(() => { if (alive) setFailed("预览读取失败"); });
    return () => { alive = false; if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [asset.material_id, asset.material_revision_id]);
  if (failed) return <p className="text-xs text-rose-700">{failed}</p>;
  if (!url) return <p className="text-xs text-slate-500">读取预览…</p>;
  if (asset.kind === "video") return <video src={url} controls playsInline className="max-h-[50vh] w-auto max-w-full rounded-lg bg-black" />;
  if (asset.kind === "image") return <img src={url} alt={asset.title || ""} className="max-h-[50vh] w-auto max-w-full rounded-lg" />;
  if (asset.kind === "audio") return <audio src={url} controls className="w-full" />;
  return <p className="text-xs text-slate-500">{asset.title}</p>;
}

// Dropping from the floating 素材库 is the same write the video model makes over MCP.
function useDropTo(projectId: number, unitId: number, readOnly: boolean) {
  const client = useQueryClient();
  const [over, setOver] = useState(false);
  const [busy, setBusy] = useState(false);
  const [issue, setIssue] = useState("");
  function zone(body: (revisionId: number) => { picks?: Record<string, number>; music?: number }) {
    return readOnly ? {} : {
      onDragOver: (event: React.DragEvent) => { if (event.dataTransfer.types.includes(MATERIAL_DRAG)) { event.preventDefault(); setOver(true); } },
      onDragLeave: () => setOver(false),
      onDrop: async (event: React.DragEvent) => {
        const raw = event.dataTransfer.getData(MATERIAL_DRAG);
        setOver(false);
        if (!raw) return;
        event.preventDefault();
        setBusy(true); setIssue("");
        try {
          const item = JSON.parse(raw) as DraggedMaterial;
          await api.post(`/content-projects/${projectId}/units/${unitId}/video-chain/materials`, { picks: {}, ...body(item.material_revision_id) });
          await client.invalidateQueries({ queryKey: ["video-chain"] });
          await client.invalidateQueries({ queryKey: ["shared-assets"] });
        } catch (cause) { setIssue(errorText(cause)); }
        finally { setBusy(false); }
      },
    };
  }
  return { over, busy, issue, zone };
}

export function ShotMaterialPages({ projectId, unitId, readOnly }: { projectId: number; unitId: number; readOnly: boolean }) {
  const chain = useVideoChain(projectId, unitId);
  const assets = useAssets(projectId);
  const [index, setIndex] = useState(0);
  const locked = readOnly || !!chain.data?.locked;
  const drop = useDropTo(projectId, unitId, locked);
  if (chain.isPending) return null;
  if (chain.error || !chain.data?.master) return <ErrorBanner message={chain.error ? errorText(chain.error) : "还没有导演稿"} />;
  const payload = chain.data.master.payload;
  const shots = [...payload.shots].sort((a, b) => a.order - b.order);
  if (!shots.length) return <p className="text-sm text-slate-500">导演稿里还没有镜头。</p>;
  const at = Math.min(index, shots.length - 1);
  const shot = shots[at];
  const start = shots.slice(0, at).reduce((sum, item) => sum + item.duration_ms, 0);
  const byRevision = new Map((assets.data || []).map(item => [item.material_revision_id, item]));
  const bound = shot.source_material_revision_id ? byRevision.get(shot.source_material_revision_id) : undefined;
  const missing = shots.filter(item => !item.source_material_revision_id).length;
  return <section aria-label="逐镜素材" className="rounded-xl border border-slate-200 bg-white p-4 text-sm">
    <div className="flex flex-wrap items-baseline justify-between gap-2"><h3 className="font-semibold">素材 · 镜头 {at + 1} / {shots.length}</h3><p className="text-xs text-slate-500">{missing ? `还缺 ${missing} 个镜头的素材` : "每个镜头都有素材了"}</p></div>
    <div className="mt-3 flex flex-wrap gap-1">{shots.map((item, position) => <button key={item.id} type="button" aria-current={position === at ? "step" : undefined} onClick={() => setIndex(position)} title={item.source_material_revision_id ? "有素材" : "缺素材"} className={`h-7 min-w-[2.25rem] rounded-md px-1.5 text-xs tabular-nums ${position === at ? "bg-ink-900 text-paper" : item.source_material_revision_id ? "border border-slate-200 text-slate-600 hover:bg-slate-50" : "border border-rose-200 bg-rose-50 text-rose-700"}`}>L{String(item.order + 1).padStart(2, "0")}</button>)}</div>
    <div className="mt-4 grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
      <div className="space-y-2 rounded-lg bg-slate-50 p-4">
        <p className="text-xs text-slate-500">{clock(start)}–{clock(start + shot.duration_ms)}</p>
        <p><span className="text-xs text-slate-500">画面　</span>{shot.board?.visual || shot.label}</p>
        {shot.board?.material_request && <p className="whitespace-pre-wrap text-amber-800"><span className="text-xs text-slate-500">素材需求　</span>{shot.board.material_request}</p>}
      </div>
      <div {...drop.zone(revision => ({ picks: { [shot.id]: revision } }))} className={`rounded-lg border-2 border-dashed p-4 ${drop.over ? "border-sky-400 bg-sky-50" : "border-slate-200"}`}>
        {bound ? <><p className="mb-2 text-xs text-slate-600">用的素材：{bound.title || `#${bound.material_revision_id}`}</p><Preview asset={bound} /></>
          : shot.source_material_revision_id ? <p className="text-xs text-slate-600">用的素材 #{shot.source_material_revision_id}（不在本项目素材里，无法预览）</p>
          : <p className="text-sm text-rose-700">这个镜头还没有素材。</p>}
        <p className="mt-2 text-xs text-slate-400">{locked ? "已定稿，只能看。" : drop.busy ? "放入中…" : "要换就从右下角「素材库」拖一条到这里；不拖的话由第三方模型去找或做。"}</p>
        {drop.issue && <p role="alert" className="mt-1 text-xs text-rose-700">{drop.issue}</p>}
      </div>
    </div>
    <div className="mt-3 flex justify-between"><Button size="sm" variant="secondary" disabled={at === 0} onClick={() => setIndex(at - 1)}>上一镜</Button><Button size="sm" variant="secondary" disabled={at === shots.length - 1} onClick={() => setIndex(at + 1)}>下一镜</Button></div>
  </section>;
}

export function MusicPanel({ projectId, unitId, readOnly }: { projectId: number; unitId: number; readOnly: boolean }) {
  const chain = useVideoChain(projectId, unitId);
  const assets = useAssets(projectId);
  const locked = readOnly || !!chain.data?.locked;
  const drop = useDropTo(projectId, unitId, locked);
  const music = (chain.data?.master?.payload as { music?: { material_revision_id?: number } } | undefined)?.music?.material_revision_id;
  const asset = music ? (assets.data || []).find(item => item.material_revision_id === music) : undefined;
  return <section aria-label="背景音乐" className="rounded-xl border border-slate-200 bg-white p-4 text-sm">
    <h3 className="font-semibold">② 背景音乐</h3>
    <div {...drop.zone(revision => ({ music: revision }))} className={`mt-3 rounded-lg border-2 border-dashed p-4 ${drop.over ? "border-sky-400 bg-sky-50" : "border-slate-200"}`}>
      {asset ? <><p className="mb-2 text-xs text-slate-600">现在用的：{asset.title || `#${asset.material_revision_id}`}</p><Preview asset={asset} /></> : music ? <p className="text-xs text-slate-600">现在用的音乐 #{music}</p> : <p className="text-xs text-slate-600">还没选背景音乐。</p>}
      <p className="mt-2 text-xs text-slate-400">{locked ? "已定稿，只能看。" : drop.busy ? "放入中…" : "要换就从「素材库」拖一首音频到这里；不拖的话由第三方模型来选。"}</p>
      {drop.issue && <p role="alert" className="mt-1 text-xs text-rose-700">{drop.issue}</p>}
    </div>
  </section>;
}
