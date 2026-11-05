import { useEffect, useState } from "react";
import { api, ApiError, currentUser } from "../api";
import { Button, inputClass } from "../components/ui";
import type { ConsistencyGroup, VideoShot } from "./VideoStudioModel";

export type Item = { id: string; name: string; group: string };
export type Copy = { channel: string; title: string; hashtags: string[]; cover_text: string; interaction: string; description: string };
export type Job = { state: string; material_revision_id?: number | null; reason?: string | null; resolution?: string | null };
export type Candidate = { material_revision_id: number; material_id: number; consistency?: string | null };
export type References = { product: number[]; person: number[]; scene: number[]; origin: Record<string, string>; main_image?: { revision: number; followed_latest: boolean } | null };
export type GridRun = { status: "running" | "done" | "failed"; started_at?: number; finished_at?: number; sheets?: string[]; error?: string | null; group_id?: string; consistency_failed?: string[] };
export type View = { product: boolean; persona?: boolean; groups?: ConsistencyGroup[]; default_mode?: "manual" | "auto";
  resolution?: { phase: "sample" | "final"; sample: string; final: string; current: string }; modes?: Record<string, "manual" | "auto">; jobs?: Record<string, Job>;
  used?: Record<string, { material_revision_id: number; source: string; i2v: boolean; title: string }>;
  frames?: Record<string, { material_revision_id: number; material_id: number; consistency: string | null; tries: number }>;
  grid?: Record<string, Candidate[]>; grid_run?: GridRun | null; grid_sheets?: Record<string, string>; references?: References; person_notices?: Record<string, string>; other_people?: Record<string, string>;
  publish_copy?: Copy | null; cover?: { material_id: number; material_revision_id: number } | null; motion?: { camera: Item[]; looks: Item[] }; direction?: { material_mode: string; style: { name: string } | null; category: { name: string } | null } };
type Prompt = { prompt: string; prompt_en: string; still_prompt: string; t2v_prompt?: string; t2v_prompt_en?: string;
  first_frame_revision_id: number | null; last_frame_revision_id: number | null; aspect_ratio: string; seconds: number; manual_note: string };

export const NO_PORTRAIT_NOTE = "这个角色没有形象照：生成画面里不出现人物，只拍场景，拿东西只出现手部。";

export function errorText(error: unknown) {
  const detail = error instanceof ApiError ? error.detail as { message?: string } | string | undefined : undefined;
  return (typeof detail === "string" ? detail : detail?.message) || (error instanceof Error ? error.message : "操作失败");
}

function CopyText({ label, text }: { label: string; text: string }) {
  const [copied, setCopied] = useState(false);
  return <div className="rounded border border-slate-200 bg-white p-2">
    <div className="flex items-center justify-between gap-2"><span className="font-medium text-slate-700">{label}</span>
      <Button size="sm" variant="ghost" onClick={() => void navigator.clipboard.writeText(text).then(() => { setCopied(true); setTimeout(() => setCopied(false), 1500); })}>{copied ? "已复制" : "复制"}</Button></div>
    <p className="mt-1 whitespace-pre-wrap">{text}</p>
  </div>;
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

// One shot without the user's footage: how its clip is made (automatic, or by hand on a website and uploaded) and the picture it starts from.
// In the storyboard-grid dialog (grid) the picture comes from the group's sheet; outside it, from a single still.
export default function ShotWork({ shot, label, data, base, busy, locked, run, onIssue, grid }: {
  shot: VideoShot; label: string; data: View; base: string; busy: boolean; locked: boolean;
  run: (action: () => Promise<unknown>) => void; onIssue: (message: string) => void; grid?: boolean;
}) {
  const [prompt, setPrompt] = useState<Prompt | null>(null);
  const [stillPrompt, setStillPrompt] = useState("");
  const [over, setOver] = useState(false);
  const [note, setNote] = useState("");
  const persona = !data.product;
  const mode = data.modes?.[shot.id] || data.default_mode || "manual";
  const job = data.jobs?.[shot.id];
  const used = data.used?.[shot.id];
  const frame = data.frames?.[shot.id];
  const candidates = data.grid?.[shot.id] || [];
  // Shots built from the original product picture or AE are finished footage; only image-to-video shots get the generate controls.
  const generated = !used || used.i2v;
  async function download(materialId: number, revisionId: number) {
    const resp = await fetch(`/api/v1/materials/${materialId}/revisions/${revisionId}/raw`, { headers: { "X-Studio-User": currentUser() } });
    if (!resp.ok) { onIssue(`首帧下载失败（${resp.status}）`); return; }
    const link = document.createElement("a");
    link.href = URL.createObjectURL(await resp.blob()); link.download = `shot-first-frame-${revisionId}.png`; link.click();
    URL.revokeObjectURL(link.href);
  }
  const loadPrompt = () => run(async () => {
    const value = await api.get<Prompt>(`${base}/shots/${shot.id}/prompt`);
    setPrompt(value);
    // Persona shots start from the shot's own board, so the still box is filled with that wording to edit.
    if (persona && !stillPrompt.trim()) setStillPrompt(value.still_prompt);
  });
  const send = (files: FileList | null) => {
    const file = files?.[0];
    if (!file) return;
    if (!/\.(mp4|mov)$/i.test(file.name) && !["video/mp4", "video/quicktime"].includes(file.type)) { setNote("请拖 MP4 / MOV 视频"); return; }
    // The panel clears its error line when an upload starts, so this note lives next to the drop area.
    setNote(files.length > 1 ? "一镜只能放一条视频，只传了第一个" : "");
    const form = new FormData(); form.append("file", file);
    run(() => api.upload(`${base}/shots/${shot.id}/upload`, form));
  };
  const off = busy || locked;
  // Drag events are always taken here so a dropped file never makes the browser open it in place of the page.
  const upload = <label className={`flex flex-col items-center rounded-lg border border-dashed px-3 py-3 text-sm ${over ? "border-indigo-500 bg-indigo-50 text-indigo-700" : "border-slate-300 bg-white"} ${off ? "cursor-not-allowed opacity-60" : "cursor-pointer"}`}
    onDragOver={event => { event.preventDefault(); if (!off) { setOver(true); setNote(""); } }} onDragLeave={() => setOver(false)}
    onDrop={event => { event.preventDefault(); setOver(false); if (!off) send(event.dataTransfer.files); }}>
    {over ? "松手上传到这一镜" : "上传做好的视频：把视频拖到这里，或点击选择"}
    <input type="file" accept="video/mp4,video/quicktime" className="hidden" disabled={off} onChange={event => { send(event.target.files); event.target.value = ""; }} />
    {note && <span className="mt-1 text-xs text-amber-800">{note}</span>}
  </label>;
  const frameInfo = prompt && <p className="mt-1">首帧：素材 #{prompt.first_frame_revision_id ?? "无"}{prompt.last_frame_revision_id ? `；尾帧：素材 #${prompt.last_frame_revision_id}` : ""}；{prompt.aspect_ratio}；{prompt.seconds} 秒。{prompt.manual_note}</p>;
  return <article className="rounded-lg border border-slate-100 p-3">
    <p className="text-sm font-medium">{label}<span className="ml-2 font-normal text-slate-500">{shot.board?.visual || shot.label}</span></p>
    {persona && data.other_people?.[shot.id] && <p className="mt-1 text-xs text-amber-800">这一镜可以出现{data.other_people[shot.id]}（不露脸），不出现角色本人。</p>}
    {used && (used.i2v ? <p className="mt-2 rounded bg-emerald-50 p-2 text-sm font-medium text-emerald-800">{used.source === "手动图生视频" ? "已上传" : "已生成"}，已放进这一镜：素材 #{used.material_revision_id}{job?.resolution ? ` ${job.resolution.toUpperCase()}` : ""}。要换可以重新上传或生成。</p>
      : <p className="mt-2 text-sm text-slate-600">已用：素材 #{used.material_revision_id} · {used.source}（用商品原图或现成素材做的，不走图生视频）</p>)}
    {generated && <div className="mt-2 flex flex-wrap items-center gap-2 text-sm">
      <span className="text-slate-500">{persona ? "出视频：" : "图生视频："}</span>
      <Button size="sm" variant={mode === "manual" ? "primary" : "secondary"} disabled={busy || locked} onClick={() => run(() => api.put(`${base}/shots/${shot.id}/mode`, { mode: "manual" }))}>手动</Button>
      <Button size="sm" variant={mode === "auto" ? "primary" : "secondary"} disabled={busy || locked} onClick={() => run(() => api.put(`${base}/shots/${shot.id}/mode`, { mode: "auto" }))}>自动</Button>
      {mode === "auto" && <Button size="sm" variant="secondary" disabled={busy || locked || job?.state === "running"} onClick={() => { if (window.confirm("自动生成这一镜，按条计费。继续？")) run(() => api.post(`${base}/shots/${shot.id}/generate`, {})); }}>{job ? "重新生成" : "自动生成"}</Button>}
      {job?.state === "running" && <Button size="sm" variant="ghost" disabled={busy} onClick={() => run(() => api.get(`${base}/shots/${shot.id}/video`))}>查看进度</Button>}
      <Button size="sm" variant="ghost" disabled={busy} onClick={loadPrompt}>看提示词</Button>
      {job && <span className={job.state === "failed" ? "text-amber-800" : "text-slate-500"}>{{ running: "生成中…", done: used?.material_revision_id === job.material_revision_id ? "已用进片" : `已生成${job.resolution ? ` ${job.resolution.toUpperCase()}` : ""}，素材 #${job.material_revision_id}（候选，选用后才进片）`, failed: `没成功：${job.reason || ""}，可改成手动` }[job.state] || job.state}</span>}
    </div>}
    {generated && <div className="mt-2 space-y-2 rounded bg-slate-50 p-2 text-sm">
      <p className="text-slate-600">首帧：{frame ? <>素材 #{frame.material_revision_id}（{persona ? "生成图" : `生成图，主体一致性${frame.consistency || "未检查"}${frame.tries > 1 ? `，重画 ${frame.tries - 1} 次` : ""}`}）
        <Button size="sm" variant="ghost" disabled={busy} onClick={() => void download(frame.material_id, frame.material_revision_id)}>下载首帧</Button>
        <Button size="sm" variant="ghost" disabled={busy || locked} onClick={() => run(() => api.put(`${base}/shots/${shot.id}/first-frame`, { material_revision_id: null }))}>{persona ? "不用这张首帧" : "改回商品原图"}</Button></>
        : persona ? grid ? "还没有首帧，从下面的九宫格候选里挑一张" : "还没有首帧，自动图生视频要先生成一张" : "商品原图（或导演稿关键帧）"}</p>
      {grid && candidates.length > 0 && <div className="flex flex-wrap gap-3">{candidates.map(item => <div key={item.material_revision_id} className="space-y-1">
        <Thumb item={item} />
        {!persona && item.consistency && <p className={`text-xs ${item.consistency === "通过" ? "text-slate-500" : "text-amber-700"}`}>商品对照：{item.consistency}</p>}
        {frame?.material_revision_id === item.material_revision_id ? <p className="text-xs text-emerald-700">已用作首帧</p>
          : <Button size="sm" variant="secondary" disabled={locked || busy} onClick={() => run(() => api.put(`${base}/shots/${shot.id}/first-frame`, { material_revision_id: item.material_revision_id }))}>用作首帧</Button>}
      </div>)}</div>}
      {grid && candidates.length > 0 && <Button size="sm" variant="ghost" disabled={locked || busy} onClick={() => { if (window.confirm("只重画这一镜，按次计费。继续？")) run(() => api.post(`${base}/shots/${shot.id}/grid-redraw`, {})); }}>只重画这一镜</Button>}
      {!grid && <div className="flex flex-wrap gap-2"><input aria-label={`${label} 首帧画面`} className={`${inputClass} min-w-0 flex-1`} placeholder={persona ? "要生成的首帧画面；点「看提示词」会按分镜填好" : "要生成的首帧画面：场景、光线、角度（商品会保持原样）"} value={stillPrompt} onChange={event => setStillPrompt(event.target.value)} />
        <Button size="sm" variant="secondary" disabled={busy || locked || !stillPrompt.trim()} onClick={() => run(async () => {
          const value = await api.post<{ consistency: string | null; used: boolean; next?: string }>(`${base}/shots/${shot.id}/image`, { prompt: stillPrompt, as_first_frame: true });
          if (!value.used) throw new Error(value.next || `主体一致性${value.consistency}`);
        })}>生成首帧</Button>
        {!persona && mode === "manual" && upload}
      </div>}
      {(persona || grid) && mode === "manual" && <div>{upload}</div>}
    </div>}
    {prompt && (persona ? <div className={`mt-2 grid gap-2 text-xs text-slate-600 ${mode === "manual" && !grid ? "sm:grid-cols-2" : ""}`}>
      {mode === "manual" && !grid && prompt.t2v_prompt && <div className="space-y-2 rounded bg-slate-50 p-2"><p className="font-medium text-slate-800">文生视频：只用文字生成</p>
        <CopyText label="中文" text={prompt.t2v_prompt} />{prompt.t2v_prompt_en && <CopyText label="English" text={prompt.t2v_prompt_en} />}</div>}
      <div className="space-y-2 rounded bg-slate-50 p-2"><p className="font-medium text-slate-800">图生视频：带首帧生成</p>
        {!grid && <CopyText label="首帧图提示词" text={prompt.still_prompt} />}
        <CopyText label="中文" text={prompt.prompt} /><CopyText label="English" text={prompt.prompt_en} />{frameInfo}</div>
    </div> : <div className="mt-2 rounded bg-slate-50 p-2 text-xs text-slate-600"><p className="whitespace-pre-wrap">{prompt.prompt}</p>{frameInfo}</div>)}
  </article>;
}
