import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api, ApiError, currentUser } from "../api";
import { ErrorBanner, Field, inputClass } from "../components/ui";

export type ChromeProfiles = { available: boolean; profiles: { dir: string; name: string }[]; personas: Record<string, string> };

export function useChromeProfiles() {
  return useQuery({ queryKey: ["chrome-profiles", currentUser()], retry: false, queryFn: () => api.get<ChromeProfiles>("/settings/chrome-profiles") });
}

export function chromeProfileName(data: ChromeProfiles | undefined, personaId: number | null | undefined) {
  const dir = personaId != null ? data?.personas[String(personaId)] : undefined;
  return dir ? data?.profiles.find(item => item.dir === dir)?.name || dir : null;
}

// Each Chrome profile keeps its own logins, so a persona's accounts stay logged in without the studio holding cookies.
export default function PersonaChromeProfile({ personaId, disabled }: { personaId: number; disabled: boolean }) {
  const client = useQueryClient();
  const query = useChromeProfiles();
  const [busy, setBusy] = useState(false);
  const [issue, setIssue] = useState("");
  if (!query.data) return null;
  const data = query.data;
  const chosen = data.personas[String(personaId)] || "";
  const takenBy = new Set(Object.entries(data.personas).filter(([key]) => key !== String(personaId)).map(([, dir]) => dir));
  async function pick(dir: string) {
    setBusy(true); setIssue("");
    try {
      await api.put(`/content-personas/${personaId}/chrome-profile`, { profile_dir: dir || null });
      await client.invalidateQueries({ queryKey: ["chrome-profiles"] });
    } catch (cause) { setIssue(cause instanceof ApiError ? (cause.detail as { message?: string } | undefined)?.message || cause.message : "保存失败"); }
    finally { setBusy(false); }
  }
  if (!data.available) return <p className="text-sm text-ink-500">本机没有找到 Google Chrome。</p>;
  return <div className="space-y-2">
    <Field label="用哪个 Chrome 个人资料打开平台" hint="账号页的「去发布」等按钮会用这个个人资料打开 Chrome；各平台在里面登录一次即可。个人资料在 Chrome 右上角头像里新建。">
      <select aria-label="Chrome 个人资料" className={inputClass} value={chosen} disabled={disabled || busy} onChange={event => void pick(event.target.value)}>
        <option value="">不指定（在当前浏览器打开）</option>
        {data.profiles.map(item => <option key={item.dir} value={item.dir} disabled={takenBy.has(item.dir)}>{item.name}{data.profiles.filter(other => other.name === item.name).length > 1 ? `（${item.dir}）` : ""}{takenBy.has(item.dir) ? "（已被其他角色使用）" : ""}</option>)}
      </select>
    </Field>
    {issue && <ErrorBanner message={issue} />}
  </div>;
}
