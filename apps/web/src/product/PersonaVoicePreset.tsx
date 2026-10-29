import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api, ApiError, currentUser } from "../api";
import { ErrorBanner, Field, inputClass } from "../components/ui";

type Presets = { default: string; items: Record<string, { name: string; voice_id: string; rate: number }>; personas: Record<string, string> };

// One place for a persona's voice: the named voice setup its works speak with (设置 → 配音).
export default function PersonaVoicePreset({ personaId, disabled }: { personaId: number; disabled: boolean }) {
  const client = useQueryClient();
  const query = useQuery({ queryKey: ["voice-settings", currentUser()], retry: false, queryFn: () => api.get<Presets>("/settings/voice") });
  const [busy, setBusy] = useState(false);
  const [issue, setIssue] = useState("");
  if (!query.data) return null;
  const data = query.data;
  const chosen = data.personas[String(personaId)] || "";
  async function pick(preset: string) {
    if (!preset || !window.confirm(`声音定为「${data.items[preset]?.name}」？定了之后不能再改。`)) return;
    setBusy(true); setIssue("");
    try {
      await api.put(`/personas/${personaId}/voice-preset`, { preset_id: preset });
      await client.invalidateQueries({ queryKey: ["voice-settings"] });
    } catch (cause) { setIssue(cause instanceof ApiError ? (cause.detail as { message?: string } | undefined)?.message || cause.message : "保存失败"); }
    finally { setBusy(false); }
  }
  if (chosen) return <Field label="这个角色的声音" hint="角色的声音建好就定下，不能再改；这个角色下的作品都用这个声音。">
    <p className="py-2 text-sm text-ink-800">{data.items[chosen]?.name || chosen}（已锁定）</p></Field>;
  return <div className="space-y-2">
    <Field label="这个角色的声音" hint="只能选一次，选定后锁定。在 设置 → 配音 里管理各套声音；同一套声音可以给多个角色用。">
      <select aria-label="这个角色的声音" className={inputClass} value={chosen} disabled={disabled || busy} onChange={event => void pick(event.target.value)}>
        <option value="">请选择</option>
        {Object.entries(data.items).map(([key, item]) => <option key={key} value={key}>{item.name}</option>)}
      </select>
    </Field>
    {issue && <ErrorBanner message={issue} />}
  </div>;
}
