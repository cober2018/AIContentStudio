import { useEffect, useState } from "react";
import { currentUser } from "../api";
import { ErrorBanner } from "../components/ui";
import { OfficialArticlePreview, type OfficialArticleRender } from "./OfficialArticlePreview";

type RenderOutput = { material_revision_id: number; content_hash: string; mime_type: string; canvas_id: string | null };
export type FrozenPreview = { modality: string; title: string; target?: { channel: string; content_form: string; artifact_kind: string }; markdown?: string; truncated?: boolean; canvas_count?: number; canvases?: unknown[]; cards?: { id: string; order: number; image_ref_key: string; caption: string }[]; scenes?: { id: string; order: number; script: string; voice_text: string; b_roll_ref_keys: string[] }[]; estimated_srt?: { estimated: true; text: string }; finished_video?: boolean; script?: unknown; script_blocks?: { id: string; order: number; text: string }[]; shot_count?: number; shots?: unknown[]; timeline_present?: boolean; timeline?: { duration_ms: number; tracks: { id: string; order: number; kind: string; items: { id: string; start_ms: number; end_ms: number }[] }[] }; voice?: { mode: string; material_revision_id?: number }; subtitles?: { cues: { id: string; text: string; start_ms: number; end_ms: number }[] }; overlays?: { id: string; text: string; start_ms: number; end_ms: number }[]; music?: { material_revision_id?: number }; cover?: { material_revision_id?: number }; render: { status?: string; outputs?: RenderOutput[]; reasons?: string[] } };

function RenderPreview({ path, output }: { path: string; output: RenderOutput }) {
  const [url, setUrl] = useState("");
  const [error, setError] = useState("");
  useEffect(() => {
    const controller = new AbortController(); let objectUrl = "";
    setUrl(""); setError("");
    fetch(`/api/v1${path}/renders/${output.material_revision_id}`, { headers: { "X-Studio-User": currentUser() }, signal: controller.signal }).then(async (response) => {
      if (!response.ok) throw new Error(`冻结渲染不可预览 (${response.status})，请核对实时权利与版本。`);
      const blob = await response.blob();
      if (!controller.signal.aborted) { objectUrl = URL.createObjectURL(blob); setUrl(objectUrl); }
    }).catch((cause) => { if (!controller.signal.aborted) setError(cause instanceof Error ? cause.message : "渲染读取失败"); });
    return () => { controller.abort(); if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [path, output.material_revision_id]);
  return <figure className="rounded-lg border border-slate-200 p-3"><figcaption className="mb-2 break-all text-xs text-slate-500">{output.canvas_id || "最终视频"} · Revision #{output.material_revision_id} · {output.content_hash}</figcaption>{error ? <ErrorBanner message={error} /> : url ? output.mime_type.startsWith("video/") ? <video aria-label="冻结视频渲染" className="max-h-96 w-full" controls src={url} /> : <img alt={`冻结画布 ${output.canvas_id || output.material_revision_id}`} className="max-h-96 object-contain" src={url} /> : <p className="text-xs text-slate-500">读取真实渲染字节…</p>}</figure>;
}

type CandidatePreviewProps = { preview: FrozenPreview & { official_render?: OfficialArticleRender }; path: string; assets?: { material_revision_id: number; content_hash_snapshot: string; role: string; slot_key: string | null; mime_type?: string }[] };

export function CandidatePreview(props: CandidatePreviewProps) {
  const official = props.preview.official_render;
  return <>{official && <OfficialArticlePreview render={official} path={props.path} />}<ContentPreview {...props} /></>;
}

function ContentPreview({ preview, path, assets = [] }: CandidatePreviewProps) {
  const videoV2 = preview.modality === "video" && preview.script_blocks !== undefined && preview.timeline !== undefined;
  const structured = preview.modality === "graphic" ? preview.canvases : videoV2 ? { script_blocks: preview.script_blocks, shots: preview.shots, timeline: preview.timeline, voice: preview.voice, subtitles: preview.subtitles, overlays: preview.overlays, music: preview.music, cover: preview.cover } : { script: preview.script, shots: preview.shots };
  return <div className="mt-4 space-y-3"><h4 className="text-lg font-semibold">{preview.title || "未命名"}</h4>{preview.target && <p className="text-sm text-indigo-700">冻结目标：{preview.target.channel}/{preview.target.content_form} · {preview.target.artifact_kind}；本地包不等于远端发布。</p>}{preview.modality === "text" ? <><pre className="max-h-96 overflow-auto whitespace-pre-wrap rounded-lg bg-slate-50 p-4 text-sm">{preview.markdown || "无正文"}</pre>{preview.truncated && <p className="text-xs text-amber-700">预览已截断，完整内容保留在冻结清单与成品包中。</p>}</> : preview.target?.artifact_kind === "image" && preview.cards ? <><p className="text-sm text-slate-600">冻结图文卡片 {preview.cards.length} 张，顺序和素材版本不可变。</p>{preview.cards.map((card) => { const ref = assets.find((item) => item.slot_key === card.image_ref_key && item.role === "card_image"); return <div key={card.id} className="space-y-2"><p className="text-sm">{card.order + 1}. {card.caption || "无说明"}</p>{ref ? <RenderPreview path={path} output={{ material_revision_id: ref.material_revision_id, content_hash: ref.content_hash_snapshot, mime_type: ref.mime_type || "image/png", canvas_id: card.id }} /> : <p className="text-sm text-amber-700">卡片素材引用未找到，不能推断图片内容。</p>}</div>; })}</> : preview.target?.artifact_kind === "script" && preview.scenes ? <><p className="text-sm text-slate-600">冻结口播场景 {preview.scenes.length} 段；无已确认最终视频。</p>{preview.scenes.map((scene) => <div key={scene.id} className="rounded bg-slate-50 p-3 text-sm"><p>{scene.order + 1}. {scene.script}</p><p className="mt-1 text-xs text-slate-500">配音稿：{scene.voice_text} · B-roll 引用：{scene.b_roll_ref_keys.join("、") || "无"}</p></div>)}{preview.estimated_srt && <pre className="max-h-56 overflow-auto whitespace-pre-wrap rounded bg-amber-50 p-3 text-xs">估算 SRT（非真实 ASR）：{preview.estimated_srt.text}</pre>}</> : <><p className="text-sm text-slate-600">{preview.modality === "graphic" ? `画布 ${preview.canvas_count || 0}` : `镜头 ${preview.shot_count || 0} · 时间线 ${videoV2 || preview.timeline_present ? "有" : "未填写"}`}</p><pre aria-label={videoV2 ? "冻结 Video v2 结构" : undefined} className="max-h-64 overflow-auto whitespace-pre-wrap rounded-lg bg-slate-50 p-4 text-xs">{JSON.stringify(structured, null, 2)}</pre>{(preview.render.outputs || []).map((output) => <RenderPreview key={output.material_revision_id} path={path} output={output} />)}</>}<p className="text-xs text-slate-500">预览来自冻结清单，渲染读取仍校验实时权利；不读取可变的当前 Master。</p></div>;
}
