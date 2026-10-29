import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api, ApiError, currentUser } from "../api";
import { Button, ErrorBanner, Field, inputClass } from "../components/ui";
import type { VideoPayload } from "./VideoStudioModel";

type Item = { id: string; name: string; group: string };
type Copy = { channel: string; title: string; hashtags: string[]; cover_text: string; interaction: string; description: string };
type Job = { state: string; material_revision_id?: number | null; reason?: string | null; resolution?: string | null };
type View = { product: boolean; default_mode?: "manual" | "auto"; resolution?: { phase: "sample" | "final"; sample: string; final: string; current: string }; modes?: Record<string, "manual" | "auto">; jobs?: Record<string, Job>;
  used?: Record<string, { material_revision_id: number; source: string; i2v: boolean; title: string }>;
  frames?: Record<string, { material_revision_id: number; material_id: number; consistency: string | null; tries: number }>;
  publish_copy?: Copy | null; motion?: { camera: Item[]; looks: Item[] }; direction?: { material_mode: string; style: { name: string } | null; category: { name: string } | null } };
type Motion = { camera_presets?: string[]; look?: string; intensity?: "subtle" | "normal" | "strong"; chain_from_previous?: boolean };
type Prompt = { prompt: string; first_frame_revision_id: number | null; last_frame_revision_id: number | null; aspect_ratio: string; seconds: number; manual_note: string };

const MODES: Record<string, string> = { photo_only: "一张图出整片", user_footage: "给素材剪", mixed: "混合补齐" };
const EMPTY: Copy = { channel: "", title: "", hashtags: [], cover_text: "", interaction: "", description: "" };

function errorText(error: unknown) {
  const detail = error instanceof ApiError ? error.detail as { message?: string } | string | undefined : undefined;
  return typeof detail === "object" && detail?.message ? detail.message : error instanceof Error ? error.message : "操作失败";
}

// Product works only: per-shot camera / look / strength, how each shot's image-to-video is made, and the publish copy.
export default function ProductShotPanel({ projectId, unitId, payload, locked }: { projectId: number; unitId: number; payload: VideoPayload | null; locked: boolean }) {
  const client = useQueryClient();
  const base = `/content-projects/${projectId}/units/${unitId}/product-video`;
  const query = useQuery({ queryKey: ["product-video", currentUser(), projectId, unitId], queryFn: () => api.get<View>(base), retry: false,
    refetchInterval: value => Object.values(value.state.data?.jobs || {}).some(job => job.state === "running") ? 20000 : false });
  const [busy, setBusy] = useState(false);
  const [issue, setIssue] = useState("");
  const [prompt, setPrompt] = useState<Record<string, Prompt>>({});
  const [copy, setCopy] = useState<Copy | null>(null);
  const [stillPrompt, setStillPrompt] = useState<Record<string, string>>({});
  const data = query.data;
  if (!data?.product || !payload) return null;
  const refresh = () => Promise.all([client.invalidateQueries({ queryKey: ["product-video"] }), client.invalidateQueries({ queryKey: ["video-chain"] })]);
  async function run(action: () => Promise<unknown>) {
    setBusy(true); setIssue("");
    try { await action(); await refresh(); } catch (error) { setIssue(errorText(error)); } finally { setBusy(false); }
  }
  // The still is fetched with the identity header and saved from a local object URL.
  async function download(materialId: number, revisionId: number) {
    const resp = await fetch(`/api/v1/materials/${materialId}/revisions/${revisionId}/raw`, { headers: { "X-Studio-User": currentUser() } });
    if (!resp.ok) { setIssue(`首帧下载失败（${resp.status}）`); return; }
    const link = document.createElement("a");
    link.href = URL.createObjectURL(await resp.blob()); link.download = `shot-first-frame-${revisionId}.png`; link.click();
    URL.revokeObjectURL(link.href);
  }
  const draftCopy = copy || data.publish_copy || EMPTY;
  const shots = [...payload.shots].sort((a, b) => a.order - b.order);
  const options = (items: Item[]) => [...new Set(items.map(item => item.group))].map(group =>
    <optgroup key={group} label={group}>{items.filter(item => item.group === group).map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</optgroup>);
  return <section className="space-y-4 rounded-xl border border-slate-200 bg-white p-4">
    <div><h3 className="font-semibold">商品镜头</h3><p className="text-sm text-slate-500">{data.direction?.category?.name || "未选品类"} · {data.direction?.style?.name || "按品类推荐风格"} · {MODES[data.direction?.material_mode || "mixed"]} · 图生视频默认{data.default_mode === "auto" ? "自动" : "手动"}{data.resolution && `，现在按${data.resolution.phase === "final" ? "成片" : "小样"}档 ${data.resolution.current.toUpperCase()} 生成（小样 ${data.resolution.sample.toUpperCase()} / 成片 ${data.resolution.final.toUpperCase()}）`}。改运镜会存成新一版导演稿。</p></div>
    {issue && <ErrorBanner message={issue} />}
    <div className="space-y-3">{shots.map((shot, index) => {
      const board = (shot.board || {}) as Motion;
      const presets = board.camera_presets || [];
      const mode = data.modes?.[shot.id] || data.default_mode || "manual";
      const job = data.jobs?.[shot.id];
      const used = data.used?.[shot.id];
      // Shots built from the original product picture or AE are finished footage; only image-to-video shots get the generate controls.
      const generated = !used || used.i2v;
      const frame = data.frames?.[shot.id];
      const save = (value: Motion) => void run(() => api.put(`${base}/shots/${shot.id}/motion`, { camera_presets: presets, look: board.look ?? null, intensity: board.intensity ?? null, chain_from_previous: !!board.chain_from_previous, ...value }));
      return <article key={shot.id} className="rounded-lg border border-slate-100 p-3">
        <p className="text-sm font-medium">镜头 {index + 1}<span className="ml-2 font-normal text-slate-500">{shot.board?.visual || shot.label}</span></p>
        <div className="mt-2 grid gap-2 sm:grid-cols-5">
          {[0, 1].map(slot => <select key={slot} aria-label={`镜头 ${index + 1} 运镜 ${slot + 1}`} className={inputClass} value={presets[slot] || ""} disabled={busy || locked || !shot.board || (slot === 1 && !presets[0])}
            onChange={event => { const next = [...presets]; if (event.target.value) next[slot] = event.target.value; else next.splice(slot); save({ camera_presets: next.filter(Boolean) }); }}>
            <option value="">{slot === 0 ? "运镜：按品类" : "叠加第二个（可选）"}</option>{options(data.motion?.camera || [])}</select>)}
          <select aria-label={`镜头 ${index + 1} 光线`} className={inputClass} value={board.look || ""} disabled={busy || locked || !shot.board} onChange={event => save({ look: event.target.value || undefined })}>
            <option value="">光线：按品类</option>{options((data.motion?.looks || []).map(look => ({ ...look, group: look.group === "real" ? "机位质感" : "光线色调" })))}</select>
          <select aria-label={`镜头 ${index + 1} 强度`} className={inputClass} value={board.intensity || ""} disabled={busy || locked || !shot.board} onChange={event => save({ intensity: (event.target.value || undefined) as Motion["intensity"] })}>
            <option value="">强度：中</option><option value="subtle">轻</option><option value="normal">中</option><option value="strong">强</option></select>
          <label className="flex items-center gap-1 text-sm"><input type="checkbox" checked={!!board.chain_from_previous} disabled={busy || locked || !shot.board || index === 0} onChange={event => save({ chain_from_previous: event.target.checked })} />接上一镜</label>
        </div>
        {used && <p className="mt-2 text-sm text-slate-600">已用：素材 #{used.material_revision_id} · {used.source}{used.i2v && job?.resolution ? ` ${job.resolution.toUpperCase()}` : ""}{!used.i2v && "（用商品原图或现成素材做的，不走图生视频）"}</p>}
        {generated && <div className="mt-2 flex flex-wrap items-center gap-2 text-sm">
          <span className="text-slate-500">图生视频：</span>
          <Button size="sm" variant={mode === "manual" ? "primary" : "secondary"} disabled={busy || locked} onClick={() => void run(() => api.put(`${base}/shots/${shot.id}/mode`, { mode: "manual" }))}>手动</Button>
          <Button size="sm" variant={mode === "auto" ? "primary" : "secondary"} disabled={busy || locked} onClick={() => void run(() => api.put(`${base}/shots/${shot.id}/mode`, { mode: "auto" }))}>自动</Button>
          {mode === "auto" && <Button size="sm" variant="secondary" disabled={busy || locked || job?.state === "running"} onClick={() => { if (window.confirm("自动生成这一镜，按条计费。继续？")) void run(() => api.post(`${base}/shots/${shot.id}/generate`, {})); }}>{job ? "重新生成" : "自动生成"}</Button>}
          {job?.state === "running" && <Button size="sm" variant="ghost" disabled={busy} onClick={() => void run(() => api.get(`${base}/shots/${shot.id}/video`))}>查看进度</Button>}
          <Button size="sm" variant="ghost" disabled={busy} onClick={() => void run(async () => { const value = await api.get<Prompt>(`${base}/shots/${shot.id}/prompt`); setPrompt(current => ({ ...current, [shot.id]: value })); })}>看提示词</Button>
          {job && <span className={job.state === "failed" ? "text-amber-800" : "text-slate-500"}>{{ running: "生成中…", done: used?.material_revision_id === job.material_revision_id ? "已用进片" : `已生成${job.resolution ? ` ${job.resolution.toUpperCase()}` : ""}，素材 #${job.material_revision_id}（候选，选用后才进片）`, failed: `没成功：${job.reason || ""}，可改成手动` }[job.state] || job.state}</span>}
        </div>}
        {generated && <div className="mt-2 space-y-2 rounded bg-slate-50 p-2 text-sm">
          <p className="text-slate-600">首帧：{frame ? <>素材 #{frame.material_revision_id}（生成图，主体一致性{frame.consistency || "未检查"}{frame.tries > 1 ? `，重画 ${frame.tries - 1} 次` : ""}）
            <Button size="sm" variant="ghost" disabled={busy} onClick={() => void download(frame.material_id, frame.material_revision_id)}>下载首帧</Button>
            <Button size="sm" variant="ghost" disabled={busy || locked} onClick={() => void run(() => api.put(`${base}/shots/${shot.id}/first-frame`, { material_revision_id: null }))}>改回商品原图</Button></> : "商品原图（或导演稿关键帧）"}</p>
          <div className="flex flex-wrap gap-2"><input aria-label={`镜头 ${index + 1} 首帧画面`} className={`${inputClass} min-w-0 flex-1`} placeholder="要生成的首帧画面：场景、光线、角度（商品会保持原样）" value={stillPrompt[shot.id] || ""} onChange={event => setStillPrompt(current => ({ ...current, [shot.id]: event.target.value }))} />
            <Button size="sm" variant="secondary" disabled={busy || locked || !(stillPrompt[shot.id] || "").trim()} onClick={() => void run(async () => {
              const value = await api.post<{ consistency: string; used: boolean; next?: string }>(`${base}/shots/${shot.id}/image`, { prompt: stillPrompt[shot.id], as_first_frame: true });
              if (!value.used) throw new Error(value.next || `主体一致性${value.consistency}`);
            })}>生成首帧</Button>
            {mode === "manual" && <label className="inline-flex cursor-pointer items-center rounded-lg border border-slate-300 bg-white px-3 py-1 text-sm">上传做好的视频<input type="file" accept="video/mp4,video/quicktime" className="hidden" disabled={busy || locked} onChange={event => { const file = event.target.files?.[0]; if (!file) return; const form = new FormData(); form.append("file", file); void run(() => api.upload(`${base}/shots/${shot.id}/upload`, form)); event.target.value = ""; }} /></label>}
          </div>
        </div>}
        {prompt[shot.id] && <div className="mt-2 rounded bg-slate-50 p-2 text-xs text-slate-600"><p className="whitespace-pre-wrap">{prompt[shot.id].prompt}</p>
          <p className="mt-1">首帧：素材 #{prompt[shot.id].first_frame_revision_id ?? "无"}{prompt[shot.id].last_frame_revision_id ? `；尾帧：素材 #${prompt[shot.id].last_frame_revision_id}` : ""}；{prompt[shot.id].aspect_ratio}；{prompt[shot.id].seconds} 秒。{prompt[shot.id].manual_note}</p></div>}
      </article>;
    })}</div>
    <div className="space-y-2 rounded-lg border border-slate-100 p-3"><h4 className="font-medium">发布文案</h4>
      <div className="grid gap-2 sm:grid-cols-2">
        <Field label="标题（≤15 字）"><input className={inputClass} maxLength={15} value={draftCopy.title} onChange={event => setCopy({ ...draftCopy, title: event.target.value })} /></Field>
        <Field label="封面字（≤8 字）"><input className={inputClass} maxLength={8} value={draftCopy.cover_text} onChange={event => setCopy({ ...draftCopy, cover_text: event.target.value })} /></Field>
        <Field label="话题（3–5 个，用空格分开）"><input className={inputClass} value={draftCopy.hashtags.join(" ")} onChange={event => setCopy({ ...draftCopy, hashtags: event.target.value.split(/\s+/).filter(Boolean).slice(0, 5) })} /></Field>
        <Field label="互动引导"><input className={inputClass} maxLength={60} value={draftCopy.interaction} onChange={event => setCopy({ ...draftCopy, interaction: event.target.value })} /></Field>
        <Field label="简介（≤50 字）"><input className={inputClass} maxLength={50} value={draftCopy.description} onChange={event => setCopy({ ...draftCopy, description: event.target.value })} /></Field>
      </div>
      {!data.publish_copy && !copy && <p className="text-xs text-slate-500">模型定稿前会写一版，你也可以先自己填。</p>}
      <Button size="sm" disabled={busy || !copy} onClick={() => void run(async () => { await api.put(`${base}/publish-copy`, draftCopy); setCopy(null); })}>保存发布文案</Button>
    </div>
  </section>;
}
