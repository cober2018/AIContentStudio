import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api, currentUser } from "../api";
import { Button, ErrorBanner, Field, inputClass } from "../components/ui";
import { errorText } from "./ShotWork";

type Copy = { title: string; hashtags: string[]; interaction: string; cover_text?: string; description?: string; lead?: string };
type View = { format: "video" | "graphic"; limits: Record<string, number>; copy: Copy | null };

// One general copy per work; video and graphic works have different fields.
export default function PublishCopy({ projectId, unitId, readOnly }: { projectId: number; unitId: number; readOnly: boolean }) {
  const client = useQueryClient();
  const path = `/content-projects/${projectId}/units/${unitId}/publish-copy`;
  const query = useQuery({ queryKey: ["publish-copy", projectId, unitId, currentUser()], retry: false, queryFn: () => api.get<View>(path) });
  const [edit, setEdit] = useState<Copy | null>(null);
  const [busy, setBusy] = useState(false);
  const [issue, setIssue] = useState("");
  if (query.isPending) return null;
  if (query.isError) return <ErrorBanner message={errorText(query.error)} />;
  const { format, limits, copy } = query.data;
  const empty: Copy = format === "graphic" ? { title: "", lead: "", hashtags: [], interaction: "" } : { title: "", hashtags: [], cover_text: "", interaction: "", description: "" };
  const draft = edit ?? { ...empty, ...(copy || {}) };
  const set = (key: keyof Copy, value: string) => setEdit({ ...draft, [key]: value });
  async function save() {
    setBusy(true); setIssue("");
    try {
      const { title, hashtags, interaction } = draft;
      await api.put(path, format === "graphic" ? { title, lead: draft.lead, hashtags, interaction } : { title, hashtags, cover_text: draft.cover_text, interaction, description: draft.description });
      setEdit(null); await client.invalidateQueries({ queryKey: ["publish-copy", projectId, unitId] });
    } catch (cause) { setIssue(errorText(cause)); } finally { setBusy(false); }
  }
  const text = (key: keyof Copy, label: string) => <Field label={`${label}（≤${limits[key]} 字）`}><input className={inputClass} maxLength={limits[key]} disabled={readOnly} value={String(draft[key] ?? "")} onChange={event => set(key, event.target.value)} /></Field>;
  return <section aria-label="发布文案" className="mb-6 rounded-xl border border-slate-200 bg-white p-4">
    <h3 className="mb-1 font-semibold">发布文案</h3>
    <p className="mb-3 text-xs text-slate-500">{format === "graphic" ? "图文文案" : "视频文案"}；每个平台都用这一份，成品包里带上。</p>
    <div className="grid gap-2 sm:grid-cols-2">
      {text("title", "标题")}
      {format === "video" && text("cover_text", "封面字")}
      <Field label="话题（3–5 个，用空格分开）"><input className={inputClass} disabled={readOnly} value={draft.hashtags.join(" ")} onChange={event => setEdit({ ...draft, hashtags: event.target.value.split(/\s+/).filter(Boolean).slice(0, 5) })} /></Field>
      {text("interaction", "互动引导")}
    </div>
    <div className="mt-2">{format === "graphic"
      ? <Field label={`导语（≤${limits.lead} 字，放在图前面）`}><textarea className={`${inputClass} min-h-[72px]`} maxLength={limits.lead} disabled={readOnly} value={draft.lead ?? ""} onChange={event => set("lead", event.target.value)} /></Field>
      : <Field label={`简介（≤${limits.description} 字）`}><textarea className={`${inputClass} min-h-[96px]`} maxLength={limits.description} disabled={readOnly} value={draft.description ?? ""} onChange={event => set("description", event.target.value)} /></Field>}</div>
    {!copy && !edit && <p className="mt-2 text-xs text-slate-500">第三方模型会写一版，你也可以先自己填。</p>}
    <div className="mt-3"><Button size="sm" disabled={readOnly || busy || !edit} onClick={() => void save()}>{busy ? "保存中…" : "保存发布文案"}</Button></div>
    {issue && <ErrorBanner message={issue} />}
  </section>;
}
