import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { api, ApiError, currentUser } from "../api";
import { Button, FloatingAlert } from "../components/ui";
import { MATERIAL_DRAG, type DraggedMaterial } from "./MaterialLibraryFloat";

type TimelineItem = { start_ms: number; end_ms: number; speech: string; picture: string; overlays: string; purpose: string };
type Shoot = { shot_id?: string; what: string; who?: string; framing?: string; camera?: string; seconds?: number; notes?: string };
type Reference = {
  status: "none" | "running" | "done" | "failed";
  source?: { kind: "upload"; filename: string } | { kind: "library"; material_revision_id: number };
  summary?: { duration_ms: number; cuts: number; average_shot_ms: number; loudness: { integrated_lufs: number } | null; transcript: string;
    transcript_engine: string | null; transcript_reason?: string | null; folder: string; files: { grids: string[] } } | null;
  error?: { message: string } | null;
  breakdown?: { analysis: string; timeline: TimelineItem[]; brand_material: string[] } | null;
  shot_list: Shoot[];
};

function errorText(error: unknown) {
  const detail = error instanceof ApiError ? error.detail as { message?: string } | string | undefined : undefined;
  return (typeof detail === "string" ? detail : detail?.message) || (error instanceof Error ? error.message : "操作失败");
}

function clock(ms: number) { return `${String(Math.floor(ms / 60000)).padStart(2, "0")}:${((ms % 60000) / 1000).toFixed(1).padStart(4, "0")}`; }

// Grid images need the user header, so they are shown from a local object URL.
function Grid({ base, name }: { base: string; name: string }) {
  const [url, setUrl] = useState("");
  useEffect(() => {
    let objectUrl = "";
    let alive = true;
    fetch(`/api/v1${base}/grids/${name}`, { headers: { "X-Studio-User": currentUser() } }).then(async response => {
      if (!response.ok) return;
      objectUrl = URL.createObjectURL(await response.blob());
      if (alive) setUrl(objectUrl);
    }).catch(() => {});
    return () => { alive = false; if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [base, name]);
  return url ? <img src={url} alt={`关键帧拼图 ${name}`} className="w-full max-w-xs rounded-lg border border-slate-200" /> : <p className="text-xs text-slate-500">读取拼图…</p>;
}

// 导演稿 step: attach a reference video, run the free local breakdown, and see what the third-party model made of it.
export default function ReferenceVideoPanel({ projectId, unitId, readOnly }: { projectId: number; unitId: number; readOnly: boolean }) {
  const client = useQueryClient();
  const base = `/content-projects/${projectId}/units/${unitId}/video-chain/reference`;
  const query = useQuery({ queryKey: ["reference-video", currentUser(), projectId, unitId], retry: false, queryFn: () => api.get<Reference>(base),
    refetchInterval: value => value.state.data?.status === "running" ? 4000 : false });
  const [busy, setBusy] = useState(false);
  const [over, setOver] = useState(false);
  const [issue, setIssue] = useState("");
  const [notice, setNotice] = useState("");
  const data = query.data;
  async function run(action: () => Promise<unknown>, done?: string) {
    setBusy(true); setIssue("");
    try { await action(); await client.invalidateQueries({ queryKey: ["reference-video"] }); if (done) setNotice(done); }
    catch (cause) { setIssue(errorText(cause)); }
    finally { setBusy(false); }
  }
  async function exportList() {
    await run(async () => { const result = await api.post<{ path: string }>(`${base}/shot-list/export`, {}); setNotice(`拍摄清单已导出到 ${result.path}`); });
  }
  const running = data?.status === "running";
  const locked = readOnly || busy || running;
  const summary = data?.summary;
  const timeline: TimelineItem[] = data?.breakdown?.timeline || [];
  return <section aria-label="参考视频" className="rounded-xl border border-slate-200 bg-white p-4 text-sm">
    <div className="flex flex-wrap items-baseline justify-between gap-2">
      <h3 className="font-semibold">参考视频（可选）</h3>
      <p className="text-xs text-slate-500">要复刻一条爆款时用。平台在本机拆：转写、切点、关键帧拼图、响度，不花钱；参考视频不会进成片。</p>
    </div>
    <div className="mt-3 flex flex-wrap items-center gap-2">
      <label className={`inline-flex cursor-pointer items-center rounded-lg border border-slate-300 bg-white px-3 py-1 text-sm ${locked ? "pointer-events-none opacity-50" : ""}`}>上传参考视频
        <input type="file" accept="video/mp4,video/quicktime,video/webm" className="hidden" disabled={locked} onChange={event => {
          const file = event.target.files?.[0]; event.target.value = "";
          if (!file) return;
          const form = new FormData(); form.append("file", file);
          void run(() => api.upload(`${base}/upload`, form), "开始拆参考视频了，几十秒到几分钟");
        }} /></label>
      <div aria-label="从素材库拖入参考视频" className={`rounded-lg border-2 border-dashed px-3 py-1 text-xs ${over ? "border-sky-400 bg-sky-50" : "border-slate-200 text-slate-500"}`}
        onDragOver={event => { if (!locked && event.dataTransfer.types.includes(MATERIAL_DRAG)) { event.preventDefault(); setOver(true); } }}
        onDragLeave={() => setOver(false)}
        onDrop={event => {
          const raw = event.dataTransfer.getData(MATERIAL_DRAG); setOver(false);
          if (!raw || locked) return;
          event.preventDefault();
          const item = JSON.parse(raw) as DraggedMaterial;
          void run(() => api.post(base, { material_revision_id: item.material_revision_id }), `开始拆「${item.title}」`);
        }}>或从右下角「素材库」拖一条视频到这里</div>
      {data?.status !== "running" && data?.source?.kind === "library" && <Button size="sm" variant="secondary" disabled={locked} onClick={() => { const source = data.source; if (source?.kind === "library") void run(() => api.post(base, { material_revision_id: source.material_revision_id }), "重新拆解中"); }}>重新拆解</Button>}
    </div>
    {running && <p className="mt-3 text-slate-600">正在拆参考视频…</p>}
    {data?.status === "failed" && <p className="mt-3 text-rose-700">没拆成：{data.error?.message || "原因不明"}</p>}
    {summary && <div className="mt-4 space-y-3">
      <p className="text-slate-700">{data?.source?.kind === "upload" ? `上传的「${data.source.filename}」` : data?.source?.kind === "library" ? `素材 #${data.source.material_revision_id}` : "参考视频"}：
        {(summary.duration_ms / 1000).toFixed(1)} 秒，{summary.cuts} 个切点，平均 {(summary.average_shot_ms / 1000).toFixed(1)} 秒一镜{summary.loudness ? `，响度 ${summary.loudness.integrated_lufs} LUFS` : "，没有声音"}。
        <span className="text-xs text-slate-500"> 结果在 {summary.folder}</span></p>
      {!summary.transcript_engine && <p className="text-xs text-amber-800">没转写出口播：{summary.transcript_reason || "原因不明"}</p>}
      {summary.transcript && <details><summary className="cursor-pointer text-slate-600">口播转写</summary><p className="mt-2 whitespace-pre-wrap rounded bg-slate-50 p-2 text-xs text-slate-700">{summary.transcript}</p></details>}
      <details><summary className="cursor-pointer text-slate-600">关键帧拼图（每行一段：首、中、尾三帧）</summary>
        <div className="mt-2 flex flex-wrap gap-3">{summary.files.grids.map(path => <Grid key={path} base={base} name={path.split("/").pop() || ""} />)}</div></details>
      {data?.breakdown ? <div className="space-y-2">
        <h4 className="font-medium">整体分析</h4>
        <p className="whitespace-pre-wrap text-slate-700">{data.breakdown.analysis}</p>
        {data.breakdown.brand_material.length > 0 && <p className="rounded bg-amber-50 p-2 text-xs text-amber-900">需要品牌真实资料（不照抄、不生成）：{data.breakdown.brand_material.join("；")}</p>}
        <h4 className="font-medium">时间线</h4>
        <div className="overflow-x-auto"><table className="w-full min-w-[40rem] text-left text-xs">
          <thead className="text-slate-500"><tr><th className="py-1 pr-2">时间</th><th className="pr-2">口播</th><th className="pr-2">画面</th><th className="pr-2">叠加</th><th>作用</th></tr></thead>
          <tbody>{timeline.map((item, index) => <tr key={index} className="border-t border-slate-100 align-top"><td className="whitespace-nowrap py-1 pr-2 tabular-nums">{clock(item.start_ms)}–{clock(item.end_ms)}</td><td className="pr-2">{item.speech}</td><td className="pr-2">{item.picture}</td><td className="pr-2">{item.overlays}</td><td>{item.purpose}</td></tr>)}</tbody>
        </table></div>
      </div> : data?.status === "done" && <p className="text-xs text-slate-500">本机拆解好了。回到第三方模型那边说「按参考视频写导演稿」，它会写整体分析、时间线和拍摄清单。</p>}
    </div>}
    {data && data.shot_list.length > 0 && <div className="mt-4 space-y-2">
      <div className="flex flex-wrap items-center justify-between gap-2"><h4 className="font-medium">拍摄清单 · {data.shot_list.length} 个镜头要实拍</h4>
        <Button size="sm" variant="secondary" disabled={busy} onClick={() => void exportList()}>导出到项目「导演稿」文件夹</Button></div>
      <div className="overflow-x-auto"><table className="w-full min-w-[40rem] text-left text-xs">
        <thead className="text-slate-500"><tr><th className="py-1 pr-2">#</th><th className="pr-2">拍什么</th><th className="pr-2">谁出镜</th><th className="pr-2">景别</th><th className="pr-2">机位 / 运镜</th><th className="pr-2">秒</th><th>注意</th></tr></thead>
        <tbody>{data.shot_list.map((shot, index) => <tr key={index} className="border-t border-slate-100 align-top"><td className="py-1 pr-2">{index + 1}</td><td className="pr-2">{shot.what}</td><td className="pr-2">{shot.who}</td><td className="pr-2">{shot.framing}</td><td className="pr-2">{shot.camera}</td><td className="pr-2 tabular-nums">{shot.seconds || ""}</td><td>{shot.notes}</td></tr>)}</tbody>
      </table></div>
    </div>}
    {issue && <FloatingAlert message={issue} onClose={() => setIssue("")} />}
    {notice && <FloatingAlert tone="info" message={notice} onClose={() => setNotice("")} />}
  </section>;
}
