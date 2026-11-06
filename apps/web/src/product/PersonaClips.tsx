import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { api, currentUser } from "../api";
import { Button, ErrorBanner, inputClass } from "../components/ui";
import { errorText } from "./PersonaPortraits";
import type { LibraryPage } from "./materialLibraryModel";

export type Clip = { material_revision_id: number; material_id: number | null; title: string; duration_ms: number | null };
export type Aspect = "9:16" | "16:9";
export type Clips = Record<"intro_clip" | "outro_clip", Partial<Record<Aspect, Clip>>>;

const SLOTS = [
  { key: "outro_clip", label: "收尾片段", note: "接在每条成片最后。" },
  { key: "intro_clip", label: "进门片段", note: "放在成片最前面；可能影响完播率，暂不建议设。" },
] as const;
const ASPECTS: [Aspect, string][] = [["9:16", "竖版 9:16"], ["16:9", "横版 16:9"]];
const seconds = (ms: number | null) => ms == null ? "时长未知" : `${(ms / 1000).toFixed(1)} 秒`;

// version: anything that changes when the stored clips change, so a new revision refetches.
function usePersonaClips(personaId: number, version: unknown) {
  return useQuery({ queryKey: ["persona-clips", personaId, version, currentUser()], queryFn: () => api.get<Clips>(`/content-personas/${personaId}/clips`), retry: false });
}

// What the profile stores: only revision ids, per aspect; empty slots are left out.
function clipsForProfile(clips: Clips) {
  const out: Record<string, Record<string, number>> = {};
  for (const { key } of SLOTS) {
    const ids = Object.fromEntries(Object.entries(clips[key]).filter(([, clip]) => clip).map(([aspect, clip]) => [aspect, clip!.material_revision_id]));
    if (Object.keys(ids).length) out[key] = ids;
  }
  return out;
}

function Preview({ clip }: { clip: Clip }) {
  const [url, setUrl] = useState("");
  const [issue, setIssue] = useState("");
  if (!clip.material_id) return null;
  if (url) return <video src={url} controls autoPlay playsInline className="mt-2 max-h-56 w-auto rounded-lg bg-black" />;
  return <>
    <button type="button" className="text-[12px] text-ink-600 underline" onClick={() => {
      api.post<{ url: string }>(`/materials/${clip.material_id}/revisions/${clip.material_revision_id}/stream-session`).then(session => setUrl(session.url)).catch(cause => setIssue(errorText(cause)));
    }}>预览</button>
    {issue && <span className="ml-2 text-[12px] text-red-600">{issue}</span>}
  </>;
}

function Picker({ onPick, onCancel }: { onPick: (clip: Clip) => void; onCancel: () => void }) {
  const [q, setQ] = useState("");
  const [term, setTerm] = useState("");
  const params = new URLSearchParams({ type: "material", status: "active", material_kind: "video", order: "newest", limit: "20", ...(term ? { q: term } : {}) });
  const list = useQuery({ queryKey: ["brand-clip-pick", term, currentUser()], queryFn: () => api.get<LibraryPage>(`/system-library?${params}`), retry: false });
  return <div className="mt-2 space-y-2 rounded-lg border border-ink-200 p-3">
    <form className="flex gap-2" onSubmit={event => { event.preventDefault(); setTerm(q.trim()); }}>
      <input className={inputClass} placeholder="搜索素材库视频标题，回车" value={q} onChange={event => setQ(event.target.value)} />
      <Button type="button" variant="secondary" size="sm" onClick={onCancel}>取消</Button>
    </form>
    {list.isError && <ErrorBanner message={errorText(list.error)} />}
    <ul className="max-h-60 divide-y divide-ink-100 overflow-auto">{(list.data?.items || []).filter(item => item.latest_revision).map(item => {
      const revision = item.latest_revision!;
      const long = (revision.duration_ms ?? 0) > 5000;
      return <li key={item.id} className="flex items-center justify-between gap-3 py-1.5 text-[13px]">
        <span className="min-w-0 truncate">{item.title} <span className="text-ink-400">· {seconds(revision.duration_ms)}{long ? " · 超过 5 秒" : ""}</span></span>
        <Button type="button" size="sm" variant="secondary" disabled={long} onClick={() => onPick({ material_revision_id: revision.id, material_id: item.id, title: item.title, duration_ms: revision.duration_ms })}>选这条</Button>
      </li>;
    })}</ul>
    {list.data && !list.data.items.length && <p className="text-[12px] text-ink-400">没有找到视频。</p>}
  </div>;
}

// Logo animations every 成片 of this persona gets automatically; saved as a new revision of the persona profile, like the cover template.
export function PersonaClipsEditor({ personaId, revision, readOnly, onSaved }: {
  personaId: number; revision: { revision_no: number; profile: Record<string, unknown> } | undefined; readOnly: boolean; onSaved: () => Promise<void>;
}) {
  const revisionNo = revision?.revision_no ?? 0;
  const saved = usePersonaClips(personaId, revisionNo);
  const [clips, setClips] = useState<Clips | null>(null);
  const [busy, setBusy] = useState(false);
  const [issue, setIssue] = useState("");
  useEffect(() => { setClips(null); }, [personaId, revisionNo]);
  async function save() {
    if (!clips) return;
    setBusy(true); setIssue("");
    try {
      const profile = { ...(revision?.profile || {}) };
      delete profile.intro_clip; delete profile.outro_clip;
      await api.post(`/content-personas/${personaId}/revisions`, { expected_revision: revisionNo, profile: { ...profile, ...clipsForProfile(clips) } });
      await onSaved();
      setClips(null);
    } catch (cause) { setIssue(errorText(cause)); } finally { setBusy(false); }
  }
  const off = readOnly || busy || saved.isPending || saved.isError;
  return <div className="space-y-3">
    <ClipSlots value={clips ?? saved.data ?? { intro_clip: {}, outro_clip: {} }} onChange={setClips} disabled={off} />
    <div className="flex items-center gap-3"><Button type="button" disabled={off || !clips} onClick={() => void save()}>{busy ? "保存中…" : "保存片段"}</Button>
      <span className="text-[12px] text-ink-500">只影响之后新开的成片任务。</span></div>
    {saved.isError && <ErrorBanner message={errorText(saved.error)} />}
    {issue && <ErrorBanner message={issue} />}
  </div>;
}

function ClipSlots({ value, onChange, disabled }: { value: Clips; onChange: (next: Clips) => void; disabled: boolean }) {
  const [picking, setPicking] = useState<string | null>(null);
  return <div className="grid min-w-0 grid-cols-1 gap-4 xl:grid-cols-2">{SLOTS.map(slot => <div key={slot.key} className="min-w-0 rounded-[16px] border border-ink-200/90 bg-surface p-5">
    <p className="font-serif text-[16px] font-semibold text-ink-900">{slot.label}</p>
    <p className="mt-1 text-[12px] text-ink-500">{slot.note}只在成片里加，小样不加；视频要自己的、可公开使用、允许给模型用，最长 5 秒。</p>
    {ASPECTS.map(([aspect, label]) => {
      const clip = value[slot.key][aspect];
      const id = `${slot.key}:${aspect}`;
      return <div key={aspect} className="mt-3">
        <p className="text-[12.5px] font-medium text-ink-500">{label}</p>
        {clip ? <div className="mt-1 flex flex-wrap items-center gap-3 text-[13.5px] text-ink-800"><span>{clip.title}（{seconds(clip.duration_ms)}）</span><Preview key={clip.material_revision_id} clip={clip} />
          <button type="button" className="text-[12px] text-ink-500 hover:text-red-600" disabled={disabled} onClick={() => onChange({ ...value, [slot.key]: { ...value[slot.key], [aspect]: undefined } })}>清空</button></div>
          : <p className="mt-1 text-[13px] text-ink-400">未设置</p>}
        {picking === id ? <Picker onCancel={() => setPicking(null)} onPick={picked => { onChange({ ...value, [slot.key]: { ...value[slot.key], [aspect]: picked } }); setPicking(null); }} />
          : <button type="button" className="mt-1 text-[12.5px] text-accent-700 underline disabled:opacity-50" disabled={disabled} onClick={() => setPicking(id)}>{clip ? "换一条" : "从素材库选视频"}</button>}
      </div>;
    })}
  </div>)}</div>;
}

// Read-only profile page: each set clip as name and length.
export function PersonaClipsSummary({ personaId, profile }: { personaId: number; profile: Record<string, unknown> }) {
  const clips = usePersonaClips(personaId, JSON.stringify([profile.intro_clip, profile.outro_clip]));
  return <>{SLOTS.map(slot => {
    const set = ASPECTS.flatMap(([aspect, label]) => { const clip = clips.data?.[slot.key][aspect]; return clip ? [`${label}：${clip.title}（${seconds(clip.duration_ms)}）`] : []; });
    return <div key={slot.key} className="text-[14px]"><span className="text-ink-500">{slot.label}　</span>{set.length ? <span className="text-ink-800">{set.join("；")}</span> : <span className="text-ink-400">未设置</span>}</div>;
  })}</>;
}
