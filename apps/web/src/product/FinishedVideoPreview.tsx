import { useState } from "react";
import { api } from "../api";
import { CoverImage } from "./WorkCovers";

type File = { role: "final" | "cover" | "cover_43" | "cover_vertical"; material_id: number | null; material_revision_id: number; mime_type: string; width: number | null; height: number | null; duration_ms: number | null };
type Copy = { title?: string; lead?: string; hashtags?: string[]; cover_text?: string; interaction?: string; description?: string };
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
  const label = (file: File) => file.role === "cover_vertical" ? "竖封面 3:4" : file.role === "cover_43" ? "横封面 4:3" : covers.length > 1 ? "横封面 16:9" : "封面";
  const copy = preview.publish_copy;
  return <div className="mt-4 space-y-4">
    <h4 className="text-lg font-semibold">{preview.title || "未命名"}</h4>
    <p className="text-sm text-slate-600">成片交付版本 · 渠道：{preview.target?.channel || "授权时选择"}</p>
    {cut && <section><p className="mb-1 text-xs text-slate-600">成片{cut.width && cut.height ? ` · ${cut.width}×${cut.height}` : ""}{cut.duration_ms ? ` · ${(cut.duration_ms / 1000).toFixed(1)} 秒` : ""}</p><Cut file={cut} /></section>}
    <div className="flex flex-wrap items-start gap-4">{covers.map(file => <div key={file.role} className="w-56"><p className="mb-1 text-xs text-slate-600">{label(file)}</p>{file.material_id ? <CoverImage cover={{ material_id: file.material_id, material_revision_id: file.material_revision_id }} label={label(file)} /> : <p className="text-xs text-slate-400">读取不到</p>}</div>)}</div>
    {copy && <section className="space-y-1 rounded-lg border border-slate-200 p-3 text-sm"><p className="font-medium">发布文案</p><p>标题：{copy.title}</p>{copy.lead !== undefined && <p>导语：{copy.lead}</p>}<p>话题：{(copy.hashtags || []).join(" ")}</p>{copy.cover_text !== undefined && <p>封面字：{copy.cover_text}</p>}<p>互动引导：{copy.interaction}</p>{copy.description && <p className="whitespace-pre-wrap">{copy.description}</p>}</section>}
    {preview.delivery_notice && <p className="text-xs text-slate-500">{preview.delivery_notice}</p>}
  </div>;
}

type Account = { id: number; name: string; status: string; platform_channel?: string | null };
export type Platform = { channel: string; account: Account | null };

// One tick per platform; the persona's account bound to that platform goes with it.
export function FinishedPlatforms({ channels, accounts, disabled, onAuthorize }: { channels: Record<string, string>; accounts: Account[]; disabled: boolean; onAuthorize: (picked: Platform[]) => void }) {
  const [picked, setPicked] = useState<string[]>([]);
  const accountOf = (channel: string) => accounts.find(row => row.status === "active" && row.platform_channel === channel) || null;
  return <div className="mt-3 space-y-3">
    <p className="text-sm font-medium">发布平台（可多选，每个平台各生成一个交付目标）</p>
    <div className="grid gap-2 sm:grid-cols-3">{Object.entries(channels).map(([key, name]) => { const account = accountOf(key); return <label key={key} className="flex items-center gap-2 rounded border border-slate-200 px-3 py-2 text-sm">
      <input type="checkbox" checked={picked.includes(key)} disabled={disabled} onChange={event => setPicked(event.target.checked ? [...picked, key] : picked.filter(item => item !== key))} />
      <span>{name}</span><span className="text-xs text-slate-500">{account ? `账号：${account.name}` : "未绑账号"}</span></label>; })}</div>
    <button type="button" className="rounded bg-slate-900 px-4 py-2 text-sm text-white disabled:opacity-40" disabled={disabled || !picked.length} onClick={() => onAuthorize(picked.map(channel => ({ channel, account: accountOf(channel) })))}>授权所选平台（{picked.length}）</button>
  </div>;
}

// Opens the platform's upload page in the persona's Chrome profile; without one it opens here.
export function GoPublish({ name, url, accountId }: { name: string; url: string | null | undefined; accountId: number | null }) {
  const [issue, setIssue] = useState("");
  if (!url) return null;
  return <span className="inline-flex items-center gap-2"><button type="button" className="rounded border border-indigo-300 px-3 py-1 text-sm text-indigo-700" onClick={() => {
    setIssue("");
    if (accountId == null) { window.open(url, "_blank", "noopener"); return; }
    api.post(`/content-accounts/${accountId}/open-link`, { url }).catch(() => { window.open(url, "_blank", "noopener"); setIssue("没用角色的 Chrome 打开，已在当前浏览器打开"); });
  }}>去{name}发布</button>{issue && <span className="text-xs text-slate-500">{issue}</span>}</span>;
}
