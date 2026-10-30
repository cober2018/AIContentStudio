import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api, ApiError, currentUser } from "../api";
import { Button, ErrorBanner, Field, Spinner, inputClass } from "../components/ui";

type Voice = { name: string; model_id: string; voice_id: string; emotion: string; rate: number; volume: number; pitch: number; format: string; sample_rate: number; bitrate: number; channels: number; latex_read: boolean; text_normalization: boolean;
  language_boost: string | null; voice_modify: { pitch: number; intensity: number; timbre: number } };
const LANGUAGES: [string, string][] = [["", "不设置"], ["auto", "自动识别"], ["Chinese", "中文"], ["Chinese,Yue", "粤语"], ["English", "英语"], ["Japanese", "日语"], ["Korean", "韩语"]];
const MODIFY: [keyof Voice["voice_modify"], string][] = [["pitch", "音调"], ["intensity", "强度"], ["timbre", "音色"]];
type Presets = { default: string; items: Record<string, Voice>; personas: Record<string, string>; emotions: Record<string, string> };

function errorText(cause: unknown) {
  return cause instanceof ApiError ? (cause.detail as { message?: string } | undefined)?.message || cause.message : "保存失败";
}

// Several named voice setups (男声、女声…); a persona picks one and its works use it, the default covers works without a persona.
export default function VoiceSettings() {
  const query = useQuery({ queryKey: ["voice-settings", currentUser()], retry: false, queryFn: () => api.get<Presets>("/settings/voice") });
  const catalog = useQuery({ queryKey: ["voice-catalog", currentUser()], retry: false,
    queryFn: () => api.get<{ voice_catalog: { voice_id: string }[] }>("/settings/model-capabilities").then(data => [...new Set(data.voice_catalog.map(item => item.voice_id))].sort()) });
  const [selected, setSelected] = useState<string | null>(null);
  const [draft, setDraft] = useState<Voice | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  if (query.isPending) return <Spinner label="读取配音设置…" />;
  if (query.error) return <ErrorBanner message={query.error instanceof Error ? query.error.message : "读取失败"} />;
  const data = query.data!;
  const id = selected && (selected === "new" || data.items[selected]) ? selected : data.default;
  const base = id === "new" ? { ...data.items[data.default], name: "" } : data.items[id];
  const value = draft || base;
  const usedBy = Object.values(data.personas).filter(preset => preset === id).length;
  const set = (patch: Partial<Voice>) => { setDraft({ ...value, ...patch }); setNotice(""); };
  async function run(action: () => Promise<unknown>, done: string) {
    setBusy(true); setError("");
    try { await action(); setDraft(null); setNotice(done); await query.refetch(); } catch (cause) { setError(errorText(cause)); } finally { setBusy(false); }
  }
  const { model_id: _model, ...body } = value;
  const num = (key: keyof Voice, step: string) => <input className={inputClass} type="number" step={step} value={value[key] as number} disabled={busy} onChange={event => set({ [key]: Number(event.target.value) } as Partial<Voice>)} />;
  return <section aria-label="配音" className="space-y-4 rounded-xl border border-slate-200 bg-white p-5">
    <h2 className="text-lg font-semibold">配音（MiniMax）</h2>
    <p className="text-sm text-slate-600">可以存多套声音配置（比如男声、女声）。每个角色定一套（一套可以给多个角色用），角色下的作品都用这套；没选角色的作品用默认这套。</p>
    {error && <ErrorBanner message={error} />}{notice && <p role="status" className="text-sm text-emerald-700">{notice}</p>}
    <div className="flex flex-wrap gap-2">{Object.entries(data.items).map(([key, item]) =>
      <Button key={key} size="sm" variant={id === key ? "primary" : "secondary"} disabled={busy} onClick={() => { setSelected(key); setDraft(null); setNotice(""); }}>{item.name}{key === data.default ? "（默认）" : ""}</Button>)}
      <Button size="sm" variant={id === "new" ? "primary" : "ghost"} disabled={busy} onClick={() => { setSelected("new"); setDraft(null); setNotice(""); }}>＋ 新建一套</Button></div>
    <div className="grid gap-3 sm:grid-cols-2">
      <Field label="名称"><input className={inputClass} maxLength={40} value={value.name} disabled={busy} onChange={event => set({ name: event.target.value })} /></Field>
      <Field label="模型" hint="在 设置 → AI 与模型 → 生成能力与插件 的语音生成里选"><p className="py-2 text-sm text-slate-700">{value.model_id}</p></Field>
      <Field label="音色（voice_id）" hint="填 MiniMax 的音色 ID，可以输入关键词搜索，比如 Gentle、female、Chinese；「温柔学姐」是 Chinese (Mandarin)_Gentle_Senior"><input className={inputClass} list="voice-ids" value={value.voice_id} disabled={busy} onChange={event => set({ voice_id: event.target.value.trim() })} />
        <datalist id="voice-ids">{(catalog.data || []).map(voice => <option key={voice} value={voice} />)}</datalist></Field>
      <Field label="情绪"><select className={inputClass} value={value.emotion} disabled={busy} onChange={event => set({ emotion: event.target.value })}>{Object.entries(data.emotions).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></Field>
      <Field label="语速（0.5–2）">{num("rate", "0.1")}</Field>
      <Field label="音量">{num("volume", "0.1")}</Field>
      <Field label="音调（−12–12）">{num("pitch", "1")}</Field>
      <Field label="格式"><select className={inputClass} value={value.format} disabled={busy} onChange={event => set({ format: event.target.value })}>{["mp3", "wav", "flac"].map(item => <option key={item} value={item}>{item.toUpperCase()}</option>)}</select></Field>
      <Field label="采样率"><select className={inputClass} value={value.sample_rate} disabled={busy} onChange={event => set({ sample_rate: Number(event.target.value) })}>{[16000, 24000, 32000, 44100].map(item => <option key={item} value={item}>{item} Hz</option>)}</select></Field>
      <Field label="比特率"><select className={inputClass} value={value.bitrate} disabled={busy} onChange={event => set({ bitrate: Number(event.target.value) })}>{[64000, 128000, 256000].map(item => <option key={item} value={item}>{item / 1000} kbps</option>)}</select></Field>
      <Field label="声道"><select className={inputClass} value={value.channels} disabled={busy} onChange={event => set({ channels: Number(event.target.value) })}><option value={1}>单声道</option><option value={2}>双声道</option></select></Field>
      <Field label="语言增强" hint="让模型按这种语言读，中文稿选「中文」"><select className={inputClass} value={value.language_boost || ""} disabled={busy} onChange={event => set({ language_boost: event.target.value || null })}>{LANGUAGES.map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></Field>
    </div>
    <div className="grid gap-3 sm:grid-cols-3">{MODIFY.map(([key, label]) => <Field key={key} label={`声音调整 · ${label}（−100–100）`} hint={key === "pitch" ? "0 是不调整" : undefined}>
      <input className={inputClass} type="number" min={-100} max={100} step={1} value={value.voice_modify?.[key] ?? 0} disabled={busy}
        onChange={event => set({ voice_modify: { ...(value.voice_modify ?? { pitch: 0, intensity: 0, timbre: 0 }), [key]: Math.round(Number(event.target.value)) } })} /></Field>)}</div>
    <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={value.latex_read} disabled={busy} onChange={event => set({ latex_read: event.target.checked })} />LaTeX 公式朗读</label>
    <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={value.text_normalization} disabled={busy} onChange={event => set({ text_normalization: event.target.checked })} />中英文本规范化</label>
    <div className="flex flex-wrap items-center gap-2">
      <Button disabled={busy || !draft || !value.name.trim()} onClick={() => void run(() => id === "new" ? api.post("/settings/voice/presets", body) : api.put(`/settings/voice/presets/${id}`, body), "已保存。")}>{id === "new" ? "新建这一套" : "保存"}</Button>
      {id !== "new" && id !== data.default && <Button variant="secondary" disabled={busy} onClick={() => void run(() => api.put(`/settings/voice/default/${id}`, {}), "已设为默认。")}>设为默认</Button>}
      {id !== "new" && id !== data.default && <Button variant="ghost" disabled={busy || usedBy > 0} onClick={() => { if (window.confirm(`删除「${value.name}」？`)) void run(async () => { await api.del(`/settings/voice/presets/${id}`); setSelected(null); }, "已删除。"); }}>删除</Button>}
      {usedBy > 0 && <span className="text-xs text-slate-500">有 {usedBy} 个角色在用这套</span>}
    </div>
  </section>;
}
