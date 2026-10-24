import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api, ApiError, currentUser } from "../api";
import { Button, ErrorBanner, Field, Spinner, inputClass } from "../components/ui";

type Voice = { model_id: string; voice_id: string; emotion: string; rate: number; volume: number; pitch: number; format: string; sample_rate: number; bitrate: number; channels: number; latex_read: boolean; text_normalization: boolean };

export default function VoiceSettings() {
  const query = useQuery({ queryKey: ["voice-settings", currentUser()], retry: false, queryFn: () => api.get<{ settings: Voice; emotions: Record<string, string> }>("/settings/voice") });
  const [draft, setDraft] = useState<Voice | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  if (query.isPending) return <Spinner label="读取配音设置…" />;
  if (query.error) return <ErrorBanner message={query.error instanceof Error ? query.error.message : "读取失败"} />;
  const value = draft || query.data!.settings;
  const set = (patch: Partial<Voice>) => { setDraft({ ...value, ...patch }); setNotice(""); };
  async function save() {
    setBusy(true); setError("");
    try { await api.put("/settings/voice", value); setDraft(null); setNotice("已保存，之后生成配音都用这套参数。"); await query.refetch(); }
    catch (cause) { setError(cause instanceof ApiError ? (cause.detail as { message?: string } | undefined)?.message || cause.message : "保存失败"); } finally { setBusy(false); }
  }
  const num = (key: keyof Voice, step: string) => <input className={inputClass} type="number" step={step} value={value[key] as number} disabled={busy} onChange={event => set({ [key]: Number(event.target.value) } as Partial<Voice>)} />;
  return <section aria-label="配音" className="space-y-4 rounded-xl border border-slate-200 bg-white p-5">
    <h2 className="text-lg font-semibold">配音（MiniMax）</h2>
    <p className="text-sm text-slate-600">制作内容页「生成配音」按这里的参数调用 MiniMax，每一项都原样传过去。</p>
    {error && <ErrorBanner message={error} />}{notice && <p role="status" className="text-sm text-emerald-700">{notice}</p>}
    <div className="grid gap-3 sm:grid-cols-2">
      <Field label="模型"><select className={inputClass} value={value.model_id} disabled={busy} onChange={event => set({ model_id: event.target.value })}>{["speech-2.8-hd", "speech-2.8-turbo", "speech-2.6-hd", "speech-2.6-turbo"].map(item => <option key={item}>{item}</option>)}</select></Field>
      <Field label="音色（voice_id）"><input className={inputClass} value={value.voice_id} disabled={busy} onChange={event => set({ voice_id: event.target.value.trim() })} /></Field>
      <Field label="情绪"><select className={inputClass} value={value.emotion} disabled={busy} onChange={event => set({ emotion: event.target.value })}>{Object.entries(query.data!.emotions).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></Field>
      <Field label="语速（0.5–2）">{num("rate", "0.1")}</Field>
      <Field label="音量">{num("volume", "0.1")}</Field>
      <Field label="音调（−12–12）">{num("pitch", "1")}</Field>
      <Field label="格式"><select className={inputClass} value={value.format} disabled={busy} onChange={event => set({ format: event.target.value })}>{["mp3", "wav", "flac"].map(item => <option key={item} value={item}>{item.toUpperCase()}</option>)}</select></Field>
      <Field label="采样率"><select className={inputClass} value={value.sample_rate} disabled={busy} onChange={event => set({ sample_rate: Number(event.target.value) })}>{[16000, 24000, 32000, 44100].map(item => <option key={item} value={item}>{item} Hz</option>)}</select></Field>
      <Field label="比特率"><select className={inputClass} value={value.bitrate} disabled={busy} onChange={event => set({ bitrate: Number(event.target.value) })}>{[64000, 128000, 256000].map(item => <option key={item} value={item}>{item / 1000} kbps</option>)}</select></Field>
      <Field label="声道"><select className={inputClass} value={value.channels} disabled={busy} onChange={event => set({ channels: Number(event.target.value) })}><option value={1}>单声道</option><option value={2}>双声道</option></select></Field>
    </div>
    <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={value.latex_read} disabled={busy} onChange={event => set({ latex_read: event.target.checked })} />LaTeX 公式朗读</label>
    <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={value.text_normalization} disabled={busy} onChange={event => set({ text_normalization: event.target.checked })} />中英文本规范化</label>
    <Button disabled={busy || !draft} onClick={() => void save()}>保存</Button>
  </section>;
}
