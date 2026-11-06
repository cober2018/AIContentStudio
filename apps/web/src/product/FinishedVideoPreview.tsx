import { useState } from "react";
import { api } from "../api";
import { CoverImage } from "./WorkCovers";

type File = { role: "final" | "cover" | "cover_vertical"; material_id: number | null; material_revision_id: number; mime_type: string; width: number | null; height: number | null; duration_ms: number | null };
type Copy = { title?: string; hashtags?: string[]; cover_text?: string; interaction?: string; description?: string };
export type FinishedPreview = { finished_video: true; title?: string; files: File[]; publish_copy?: Copy | null; delivery_notice?: string; target?: { channel: string | null } };

// The 成片 plays through the library's signed stream rather than a full download.
function Cut({ file }: { file: File }) {
  const [url, setUrl] = useState("");
  const [issue, setIssue] = useState("");
  if (url) return <video src={url} controls playsInline className="max-h-[60vh] w-full rounded-lg bg-black" />;
  return <div className="space-y-1"><button type="button" className="rounded border px-3 py-1 text-sm" disabled={!file.material_id} onClick={() => {
    api.post<{ url: string }>(`/materials/${file.material_id}/revisions/${file.material_revision_id}/stream-session`).then(session => setUrl(session.url)).catch(cause => setIssue(cause instanceof Error ? cause.message : "成片读取失败"));
  }}>播放成片</button>{issue && <p className="text-xs text-rose-700">{issue}</p>}</div>;
}

export function FinishedVideoPreview({ preview }: { preview: FinishedPreview }) {
  const cut = preview.files.find(file => file.role === "final");
  const covers = preview.files.filter(file => file.role !== "final");
  const label = (file: File) => file.role === "cover_vertical" ? "竖封面 3:4" : covers.length > 1 ? "横封面 16:9" : "封面";
  const copy = preview.publish_copy;
  return <div className="mt-4 space-y-4">
    <h4 className="text-lg font-semibold">{preview.title || "未命名"}</h4>
    <p className="text-sm text-slate-600">成片交付版本 · 渠道：{preview.target?.channel || "授权时选择"}</p>
    {cut && <section><p className="mb-1 text-xs text-slate-600">成片{cut.width && cut.height ? ` · ${cut.width}×${cut.height}` : ""}{cut.duration_ms ? ` · ${(cut.duration_ms / 1000).toFixed(1)} 秒` : ""}</p><Cut file={cut} /></section>}
    <div className="flex flex-wrap items-start gap-4">{covers.map(file => <div key={file.role} className="w-56"><p className="mb-1 text-xs text-slate-600">{label(file)}</p>{file.material_id ? <CoverImage cover={{ material_id: file.material_id, material_revision_id: file.material_revision_id }} label={label(file)} /> : <p className="text-xs text-slate-400">读取不到</p>}</div>)}</div>
    {copy && <section className="space-y-1 rounded-lg border border-slate-200 p-3 text-sm"><p className="font-medium">发布文案</p><p>标题：{copy.title}</p><p>话题：{(copy.hashtags || []).join(" ")}</p><p>封面字：{copy.cover_text}</p><p>互动引导：{copy.interaction}</p><p className="whitespace-pre-wrap">{copy.description}</p></section>}
    {preview.delivery_notice && <p className="text-xs text-slate-500">{preview.delivery_notice}</p>}
  </div>;
}
