import { useEffect, useRef, useState } from "react";
import { api, currentUser } from "../api";
import { Button, ErrorBanner, Field, inputClass } from "../components/ui";
import { previewByteHash } from "./previewByteHash";

export type VoicePresetOption = {
  id: string; label: string; provider_key: string; provider_version: string;
  model_id: string; profile_id: string; voice_id: string; language?: string;
  tags?: string[]; favorite?: boolean; verified?: boolean; rate?: number; preview_ref?: string | null;
};

export default function VoicePresetPicker({ voices, selectedId, disabled = false, onSelect }: {
  voices: VoicePresetOption[]; selectedId: string; disabled?: boolean;
  onSelect: (voice: VoicePresetOption) => void;
}) {
  const [search, setSearch] = useState("");
  const [language, setLanguage] = useState("");
  const [favorites, setFavorites] = useState(false);
  const [url, setUrl] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const selected = voices.find(item => item.id === selectedId);
  const request = useRef(0);
  const objectUrl = useRef("");
  useEffect(() => {
    request.current += 1; setBusy(false); setError(""); setUrl("");
    if (objectUrl.current) URL.revokeObjectURL(objectUrl.current);
    objectUrl.current = "";
    return () => { request.current += 1; if (objectUrl.current) URL.revokeObjectURL(objectUrl.current); objectUrl.current = ""; };
  }, [selectedId, selected?.preview_ref]);
  const filtered = voices.filter(item => (!favorites || item.favorite) && (!language || item.language === language)
    && `${item.label} ${item.voice_id} ${item.model_id} ${(item.tags || []).join(" ")}`.toLocaleLowerCase().includes(search.toLocaleLowerCase()))
    .sort((a, b) => Number(b.favorite) - Number(a.favorite) || a.label.localeCompare(b.label));
  const shown = filtered.slice(0, 100);
  if (selected && !shown.some(item => item.id === selected.id)) shown.unshift(selected);
  async function preview() {
    const match = /^material_revision:([1-9][0-9]*):([1-9][0-9]*)$/.exec(selected?.preview_ref || "");
    if (!match || busy || disabled) return;
    const serial = ++request.current;
    const identity = currentUser();
    const isCurrent = () => request.current === serial && currentUser() === identity;
    setBusy(true); setError("");
    try {
      const revisions = await api.get<{ id: number; status: string; content_hash: string; mime_type: string }[]>(`/materials/${match[1]}/revisions`);
      const revision = revisions.find(row => row.id === Number(match[2]));
      if (!revision || !["candidate", "usable", "active"].includes(revision.status)
        || !/^audio\/(wav|x-wav|mpeg|ogg|mp4)$/.test(revision.mime_type)) throw new Error("试听素材不可用，不会重新生成。");
      const response = await fetch(`/api/v1/materials/${match[1]}/revisions/${match[2]}/raw`, {
        headers: { "X-Studio-User": identity }, cache: "no-store",
      });
      if (!response.ok) throw new Error("试听素材不可读。");
      const bytes = await response.arrayBuffer();
      if (await previewByteHash(bytes) !== revision.content_hash) throw new Error("试听素材哈希不一致。");
      if (!isCurrent()) return;
      if (objectUrl.current) URL.revokeObjectURL(objectUrl.current);
      objectUrl.current = URL.createObjectURL(new Blob([bytes], { type: revision.mime_type })); setUrl(objectUrl.current);
    } catch (caught) { if (isCurrent()) setError(caught instanceof Error ? caught.message : "试听失败。"); }
    finally { if (isCurrent()) setBusy(false); }
  }
  return <div className="space-y-2" aria-label="音色选择器">
    <div className="grid gap-2 sm:grid-cols-2">
      <Field label="搜索音色"><input className={inputClass} value={search} onChange={event => setSearch(event.target.value)} placeholder="名称、Voice ID、风格或模型" /></Field>
      <Field label="音色语言"><select className={inputClass} value={language} onChange={event => setLanguage(event.target.value)}><option value="">全部语言</option>{[...new Set(voices.map(item => item.language).filter(Boolean))].sort().map(item => <option key={item} value={item}>{item}</option>)}</select></Field>
    </div>
    <label className="text-xs"><input type="checkbox" checked={favorites} onChange={event => setFavorites(event.target.checked)} /> 只看收藏音色</label>
    <Field label="音色预设"><select className={inputClass} value={selectedId} disabled={disabled} onChange={event => {
      const choice = voices.find(item => item.id === event.target.value); if (choice) onSelect(choice);
    }}><option value="">请选择已登记音色</option>{shown.map(item => <option key={item.id} value={item.id}>{item.favorite ? "★ " : ""}{item.label} · {item.model_id} · {item.voice_id}</option>)}</select></Field>
    <p className="text-xs text-slate-500">匹配 {filtered.length} 项，最多展示 100 项；可搜索全部目录。试听只读现有素材，不生成、不扣费。</p>
    {selected?.preview_ref?.startsWith("material_revision:") && <Button variant="secondary" disabled={disabled || busy} onClick={() => void preview()}>{busy ? "读取试听…" : "试听已保存音频"}</Button>}
    {url && <audio src={url} controls />}
    {error && <ErrorBanner message={error} />}
  </div>;
}
