import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { api, ApiError, currentUser } from "../api";
import { Button, FloatingAlert } from "../components/ui";
import type { VideoPayload } from "./VideoStudioModel";

type Candidate = { material_revision_id: number; material_id: number; consistency?: string | null };
type References = { product: number[]; person: number[]; scene: number[]; origin: Record<string, string> };
type Run = { status: "running" | "done" | "failed"; started_at?: number; finished_at?: number; sheets?: string[]; error?: string | null;
  skipped?: string[]; consistency_failed?: string[] };
type View = { product: boolean; grid?: Record<string, Candidate[]>; grid_run?: Run | null; frames?: Record<string, { material_revision_id: number }>;
  references?: References; person_notices?: Record<string, string> };

const ORIGIN: Record<string, string> = { manual: "共同视觉参考里选的", sku_primary_image: "商品主图", persona_portrait: "角色形象照" };
type Chain = { state: string; locked?: boolean; master: { payload: VideoPayload } | null };

function errorText(error: unknown) {
  const detail = error instanceof ApiError ? error.detail as { message?: string } | string | undefined : undefined;
  return (typeof detail === "string" ? detail : detail?.message) || (error instanceof Error ? error.message : "操作失败");
}

function Picture({ path, alt, className }: { path: string; alt: string; className: string }) {
  const [url, setUrl] = useState("");
  useEffect(() => {
    let objectUrl = "";
    let alive = true;
    fetch(path, { headers: { "X-Studio-User": currentUser() } }).then(async response => {
      if (!response.ok) return;
      objectUrl = URL.createObjectURL(await response.blob());
      if (alive) setUrl(objectUrl);
    }).catch(() => {});
    return () => { alive = false; if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [path]);
  return url ? <a href={url} target="_blank" rel="noreferrer"><img src={url} alt={alt} className={className} /></a> : <div className={`${className} bg-slate-100`} />;
}

function Thumb({ item }: { item: Candidate }) {
  const [url, setUrl] = useState("");
  useEffect(() => {
    let objectUrl = "";
    let alive = true;
    fetch(`/api/v1/materials/${item.material_id}/revisions/${item.material_revision_id}/raw`, { headers: { "X-Studio-User": currentUser() } }).then(async response => {
      if (!response.ok) return;
      objectUrl = URL.createObjectURL(await response.blob());
      if (alive) setUrl(objectUrl);
    }).catch(() => {});
    return () => { alive = false; if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [item.material_id, item.material_revision_id]);
  return url ? <img src={url} alt={`候选 #${item.material_revision_id}`} className="h-40 w-auto rounded border border-slate-200" /> : <div className="h-40 w-24 rounded bg-slate-100" />;
}

// 素材 step, product works: one 3×3 image keeps people and room the same across shots; each cell is only a first-frame candidate.
export default function StoryboardGridPanel({ projectId, unitId, readOnly }: { projectId: number; unitId: number; readOnly: boolean }) {
  const client = useQueryClient();
  const base = `/content-projects/${projectId}/units/${unitId}/product-video`;
  // While a sheet is being drawn (minutes), the panel re-reads the state instead of holding a request open.
  const view = useQuery({ queryKey: ["product-video", currentUser(), projectId, unitId], retry: false, queryFn: () => api.get<View>(base),
    refetchInterval: query => query.state.data?.grid_run?.status === "running" ? 4000 : false });
  const chain = useQuery({ queryKey: ["video-chain", currentUser(), projectId, unitId], retry: false,
    queryFn: () => api.get<Chain>(`/content-projects/${projectId}/units/${unitId}/video-chain`) });
  const [busy, setBusy] = useState("");
  const [issue, setIssue] = useState("");
  const [notice, setNotice] = useState("");
  if (!view.data?.product || !chain.data?.master) return null;
  const locked = readOnly || !!chain.data.locked || ["not_started", "draft_review", "draft_changes"].includes(chain.data.state);
  const shots = [...chain.data.master.payload.shots].sort((a, b) => a.order - b.order);
  const grid = view.data.grid || {};
  const refs = view.data.references;
  const notices = view.data.person_notices || {};
  const gridRun = view.data.grid_run;
  const running = gridRun?.status === "running";
  async function run(key: string, action: () => Promise<unknown>, done: string) {
    setBusy(key); setIssue("");
    try { await action(); await client.invalidateQueries({ queryKey: ["product-video"] }); setNotice(done); }
    catch (cause) { setIssue(errorText(cause)); }
    finally { setBusy(""); }
  }
  return <section aria-label="九宫格分镜" className="rounded-xl border border-slate-200 bg-white p-4 text-sm">
    <div className="flex flex-wrap items-center justify-between gap-2">
      <div><h3 className="font-semibold">九宫格分镜</h3>
        <p className="text-xs text-slate-500">一次把最多 9 个镜头画在一张图里，商品、人物、房间、光线一致，再裁成每镜的首帧候选；每格对照商品主图检查，不过关只重画那一格。商品纯特写单独生成更准。按次计费。</p>
        {refs && <p className="mt-1 text-xs text-slate-600">参考：商品 {refs.product.length ? ORIGIN[refs.origin.product] || "已选" : "没有（不检查商品）"}；人物 {refs.person.length ? `${ORIGIN[refs.origin.person] || "已选"} ${refs.person.length} 张` : "没有形象照，生成画面里不出现人物"}{refs.scene.length ? `；场景 ${refs.scene.length} 张` : ""}</p>}</div>
      <Button size="sm" disabled={locked || !!busy || running} onClick={() => { if (window.confirm("生成九宫格分镜会调用生图模型，按次计费。继续？")) void run("grid", () => api.post(`${base}/storyboard-grid`, {}), "开始生成了，约 2–4 分钟，可以先做别的，好了这里会自动更新"); }}>{running ? "生成中…" : "九宫格分镜"}</Button>
    </div>
    {locked && !chain.data.locked && <p className="mt-2 text-xs text-slate-500">导演稿采用后才能生成。</p>}
    {running && <p className="mt-2 rounded-lg bg-indigo-50 p-2 text-xs text-indigo-800">正在生成九宫格：先画整张分镜图，再逐格对照商品主图检查，不过关的格子会单独重画。约 2–4 分钟，页面会自动更新。</p>}
    {gridRun?.status === "failed" && <p className="mt-2 rounded-lg bg-rose-50 p-2 text-xs text-rose-800">上次生成失败：{gridRun.error || "原因未知"}{gridRun.sheets?.length ? "。整张分镜图已保留在下面，可以看看模型画成了什么样。" : ""}</p>}
    {!!gridRun?.sheets?.length && <div className="mt-3"><p className="text-xs font-medium text-slate-600">最近一次的整张分镜图（点开看大图；每镜的候选就是从这里按格裁出来的）</p>
      <div className="mt-2 flex flex-wrap gap-3">{gridRun.sheets.map(name => <Picture key={name} path={`/api/v1${base}/storyboard-grid/sheets/${encodeURIComponent(name)}`} alt={`九宫格分镜 ${name}`} className="h-72 w-auto rounded border border-slate-200" />)}</div></div>}
    {gridRun?.status === "done" && !!gridRun.skipped?.length && <p className="mt-2 text-xs text-slate-500">没进九宫格的镜头：{gridRun.skipped.map(id => `镜头 ${(shots.find(shot => shot.id === id)?.order ?? 0) + 1}`).join("、")}（商品亮相 / 下单引导用商品原图，模板和素材库镜头用已有素材，商品纯特写默认单独生成）。</p>}
    {Object.keys(notices).length > 0 && <ul className="mt-2 space-y-1 rounded-lg bg-amber-50 p-2 text-xs text-amber-800">{shots.filter(shot => notices[shot.id]).map(shot => <li key={shot.id}>镜头 {shot.order + 1}：{notices[shot.id]}。可以改成商品 / 场景镜头，或先给角色补形象照。</li>)}</ul>}
    {Object.keys(grid).length > 0 && <p className="mt-3 text-xs text-slate-500">每镜的候选按生成时间排，最新的在最前；旧的候选是以前生成的，留着备选。</p>}
    {Object.keys(grid).length > 0 && <div className="mt-3 space-y-3">{shots.filter(shot => grid[shot.id]?.length).map(shot => {
      const used = view.data?.frames?.[shot.id]?.material_revision_id;
      return <div key={shot.id} className="rounded-lg border border-slate-100 p-3">
        <div className="flex flex-wrap items-center justify-between gap-2"><p className="font-medium">镜头 {shot.order + 1}<span className="ml-2 font-normal text-slate-500">{shot.board?.visual || shot.label}</span></p>
          <Button size="sm" variant="ghost" disabled={locked || !!busy} onClick={() => { if (window.confirm("只重画这一镜，按次计费。继续？")) void run(`redraw-${shot.id}`, () => api.post(`${base}/shots/${shot.id}/grid-redraw`, {}), "这一镜重画好了，多了一张候选"); }}>{busy === `redraw-${shot.id}` ? "重画中…" : "只重画这一镜"}</Button></div>
        <div className="mt-2 flex flex-wrap gap-3">{grid[shot.id].map(item => <div key={item.material_revision_id} className="space-y-1">
          <Thumb item={item} />
          {item.consistency && <p className={`text-xs ${item.consistency === "通过" ? "text-slate-500" : "text-amber-700"}`}>商品对照：{item.consistency}</p>}
          {used === item.material_revision_id ? <p className="text-xs text-emerald-700">已用作首帧</p>
            : <Button size="sm" variant="secondary" disabled={locked || !!busy} onClick={() => void run(`use-${item.material_revision_id}`, () => api.put(`${base}/shots/${shot.id}/first-frame`, { material_revision_id: item.material_revision_id }), "已设为这一镜的首帧")}>用作首帧</Button>}
        </div>)}</div>
      </div>;
    })}</div>}
    {issue && <FloatingAlert message={issue} onClose={() => setIssue("")} />}
    {notice && <FloatingAlert tone="info" message={notice} onClose={() => setNotice("")} />}
  </section>;
}
