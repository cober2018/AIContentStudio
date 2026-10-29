import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { api, ApiError, currentUser } from "../api";
import { Button } from "../components/ui";

type Check = { status: "ok" | "warning"; items: { key: string; name: string; pass: boolean; detail: string }[] };
type Status = { voice: { mode: string; material_revision_id?: number; material_id?: number; duration_ms?: number | null; quality?: Check | null }; settings: { voice_id: string; emotion: string; rate: number; model_id: string }; emotions: Record<string, string> };

function failure(cause: unknown) {
  const detail = cause instanceof ApiError ? cause.detail as { message?: string } | undefined : undefined;
  return detail?.message || (cause instanceof Error ? cause.message : "配音没生成好");
}

export default function VoiceoverPanel({ projectId, unitId, readOnly, onSaved }: { projectId: number; unitId: number; readOnly?: boolean; onSaved?: () => void }) {
  const base = `/content-projects/${projectId}/units/${unitId}`;
  const status = useQuery({ queryKey: ["voiceover", currentUser(), projectId, unitId], retry: false, queryFn: () => api.get<Status>(`${base}/voiceover`) });
  const [busy, setBusy] = useState(false);
  const [issue, setIssue] = useState("");
  const [url, setUrl] = useState("");
  const revision = status.data?.voice.material_revision_id;
  useEffect(() => {
    let objectUrl = "";
    let alive = true;
    setUrl("");
    if (!revision) return;
    // Audio bytes need the user header, so the player gets a local object URL.
    const materialId = status.data?.voice.material_id;
    if (!materialId) return;
    fetch(`/api/v1/materials/${materialId}/revisions/${revision}/raw`, { headers: { "X-Studio-User": currentUser() } }).then(async response => {
      if (!response.ok) return;
      objectUrl = URL.createObjectURL(await response.blob());
      if (alive) setUrl(objectUrl);
    }).catch(() => {});
    return () => { alive = false; if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [revision, status.data?.voice.material_id]);
  async function generate() {
    setBusy(true); setIssue("");
    try { await api.post(`${base}/voiceover`, {}); await status.refetch(); onSaved?.(); }
    catch (cause) { setIssue(failure(cause)); } finally { setBusy(false); }
  }
  const settings = status.data?.settings;
  return <section aria-label="配音" className="rounded-xl border border-slate-200 bg-white p-4 text-sm">
    <div className="flex flex-wrap items-center justify-between gap-2">
      <div><h3 className="font-semibold">① 配音</h3><p className="mt-1 text-xs text-slate-500">{settings ? `按台词列生成 · ${settings.voice_id} · ${status.data?.emotions[settings.emotion] || settings.emotion} · 语速 ${settings.rate} · ${settings.model_id}（设置 → 配音 可改）` : "读取配音设置…"}</p></div>
      <Button size="sm" variant={revision ? "secondary" : "primary"} disabled={readOnly || busy || status.isPending} onClick={() => void generate()}>{busy ? "生成中，约一分钟…" : revision ? "重新生成配音" : "生成配音"}</Button>
    </div>
    {revision ? (url ? <audio className="mt-3 w-full" controls src={url} /> : <p className="mt-2 text-xs text-slate-500">配音已放进主稿（素材 #{revision}）。</p>) : <p className="mt-2 text-xs text-amber-700">还没有配音。剪辑要跟着配音走，先生成配音。</p>}
    {status.data?.voice.quality && <ul className="mt-2 space-y-1 text-xs">{status.data.voice.quality.items.map(item =>
      <li key={item.key} className={item.pass ? "text-slate-500" : "text-amber-800"}>{item.pass ? "✓" : "!"} {item.name}：{item.detail}</li>)}</ul>}
    {issue && <p role="alert" className="mt-2 text-xs text-rose-700">{issue}</p>}
  </section>;
}
