import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { api, currentUser } from "../api";
import { Button, ErrorBanner, Field, inputClass } from "../components/ui";
import { errorText, type Copy, type View } from "./ShotWork";

const EMPTY: Copy = { channel: "", title: "", hashtags: [], cover_text: "", interaction: "", description: "" };

// The cover is read as a blob because identity travels in a request header.
function CoverImage({ cover }: { cover: { material_id: number; material_revision_id: number } }) {
  const [url, setUrl] = useState("");
  useEffect(() => {
    let alive = true, made = "";
    fetch(`/api/v1/materials/${cover.material_id}/revisions/${cover.material_revision_id}/raw`, { headers: { "X-Studio-User": currentUser() } })
      .then(response => response.ok ? response.blob() : null)
      .then(blob => { if (alive && blob) { made = URL.createObjectURL(blob); setUrl(made); } });
    return () => { alive = false; if (made) URL.revokeObjectURL(made); };
  }, [cover.material_id, cover.material_revision_id]);
  return url ? <img src={url} alt="封面" className="max-h-[40vh] w-auto rounded-lg border border-slate-200" /> : <p className="text-xs text-slate-400">加载中…</p>;
}

// Product works: the publish copy is finished on the 交付 step, beside the cover it has to match.
export default function ProductPublishCopy({ projectId, unitId, readOnly }: { projectId: number; unitId: number; readOnly: boolean }) {
  const client = useQueryClient();
  const base = `/content-projects/${projectId}/units/${unitId}/product-video`;
  const query = useQuery({ queryKey: ["product-video", currentUser(), projectId, unitId], queryFn: () => api.get<View>(base), retry: false });
  const [copy, setCopy] = useState<Copy | null>(null);
  const [busy, setBusy] = useState(false);
  const [issue, setIssue] = useState("");
  const data = query.data;
  if (!data?.product) return null;
  const draft = copy || data.publish_copy || EMPTY;
  async function save() {
    setBusy(true); setIssue("");
    try { await api.put(`${base}/publish-copy`, draft); setCopy(null); await client.invalidateQueries({ queryKey: ["product-video"] }); }
    catch (error) { setIssue(errorText(error)); } finally { setBusy(false); }
  }
  return <section aria-label="发布文案" className="rounded-xl border border-slate-200 bg-white p-4">
    <h3 className="mb-3 font-semibold">发布文案</h3>
    <div className="flex flex-wrap gap-5">
      <div className="min-w-[16rem] flex-1 space-y-2">
        <div className="grid gap-2 sm:grid-cols-2">
          <Field label="标题（≤15 字）"><input className={inputClass} maxLength={15} disabled={readOnly} value={draft.title} onChange={event => setCopy({ ...draft, title: event.target.value })} /></Field>
          <Field label="封面字（≤8 字）"><input className={inputClass} maxLength={8} disabled={readOnly} value={draft.cover_text} onChange={event => setCopy({ ...draft, cover_text: event.target.value })} /></Field>
          <Field label="话题（3–5 个，用空格分开）"><input className={inputClass} disabled={readOnly} value={draft.hashtags.join(" ")} onChange={event => setCopy({ ...draft, hashtags: event.target.value.split(/\s+/).filter(Boolean).slice(0, 5) })} /></Field>
          <Field label="互动引导"><input className={inputClass} maxLength={60} disabled={readOnly} value={draft.interaction} onChange={event => setCopy({ ...draft, interaction: event.target.value })} /></Field>
          <Field label="简介（≤50 字）"><input className={inputClass} maxLength={50} disabled={readOnly} value={draft.description} onChange={event => setCopy({ ...draft, description: event.target.value })} /></Field>
        </div>
        {!data.publish_copy && !copy && <p className="text-xs text-slate-500">模型定稿后会写一版，你也可以先自己填。</p>}
        <Button size="sm" disabled={readOnly || busy || !copy} onClick={() => void save()}>{busy ? "保存中…" : "保存发布文案"}</Button>
        {issue && <ErrorBanner message={issue} />}
      </div>
      <div className="w-48 shrink-0"><p className="mb-1 text-xs text-slate-600">封面</p>{data.cover ? <CoverImage cover={data.cover} /> : <p className="text-xs text-slate-400">还没有封面</p>}</div>
    </div>
  </section>;
}
