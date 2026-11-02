import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api, ApiError, currentUser } from "../api";
import { ErrorBanner, Field, inputClass } from "../components/ui";

type Persona = { id: number; name: string; status: string };

// The persona drives the product video's voice, portrait and way of talking, so it is required and can change at any time.
export default function ProductPersonaPicker({ base, personaId, readOnly, onSaved }: {
  base: string; personaId: number | null; readOnly: boolean; onSaved: (unit: unknown) => void;
}) {
  const personas = useQuery({ queryKey: ["content-personas", currentUser()], retry: false, queryFn: () => api.get<Persona[]>("/content-personas") });
  const [busy, setBusy] = useState(false);
  const [issue, setIssue] = useState("");
  const [changed, setChanged] = useState(false);
  async function pick(value: string) {
    if (!value || Number(value) === personaId) return;
    setBusy(true); setIssue("");
    try { onSaved(await api.patch(base, { persona_id: Number(value) })); setChanged(personaId !== null); }
    catch (cause) { setIssue(cause instanceof ApiError ? (cause.detail as { message?: string } | undefined)?.message || cause.message : "保存失败"); }
    finally { setBusy(false); }
  }
  const active = (personas.data || []).filter(row => row.status === "active" || row.id === personaId);
  return <section className={`mb-5 rounded-xl border p-4 ${personaId === null ? "border-amber-300 bg-amber-50" : "border-slate-200 bg-white"}`} aria-label="作品角色">
    {personaId === null && <p className="mb-3 text-sm font-medium text-amber-900">这条商品视频还没选角色。先选好角色：配音、形象照和说话方式都按角色来，选好之前不能生成任务书、画面和配音。</p>}
    <Field label="角色" hint="这条视频按这个角色生成：声音、形象照、用词口吻、发布文案。随时可以换。">
      <select aria-label="作品角色" className={inputClass} value={personaId ?? ""} disabled={readOnly || busy} onChange={event => void pick(event.target.value)}>
        <option value="" disabled>选择角色</option>
        {active.map(row => <option key={row.id} value={row.id}>{row.name}</option>)}
      </select>
    </Field>
    {changed && <p className="mt-2 text-xs text-slate-600">已换角色。之后生成的画面和配音按新角色；已有的导演稿是按原角色写的，要按新角色说话就让模型重写导演稿。</p>}
    {issue && <div className="mt-2"><ErrorBanner message={issue} /></div>}
  </section>;
}
