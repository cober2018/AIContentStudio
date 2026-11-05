import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { api, ApiError, currentUser } from "../api";
import { Button, ErrorBanner, inputClass } from "../components/ui";
import { Preview, type Template } from "./AeTemplateLibrary";

type Chosen = { id: string; version: string };

function errorText(cause: unknown) {
  const detail = cause instanceof ApiError ? cause.detail as { message?: string } | string | undefined : undefined;
  return typeof detail === "object" && detail?.message ? detail.message : typeof detail === "string" ? detail : cause instanceof Error ? cause.message : "保存失败";
}

// 编辑资料: the chosen 封面 template saves as a new revision of the persona profile, like the portraits.
export function PersonaCoverTemplateEditor({ personaId, revision, readOnly, onSaved }: {
  personaId: number; revision: { revision_no: number; profile: Record<string, unknown> } | undefined; readOnly: boolean; onSaved: () => Promise<void>;
}) {
  const templates = useQuery({ queryKey: ["ae-templates", currentUser()], queryFn: () => api.get<{ items: Template[] }>("/settings/ae-templates"), retry: false });
  const saved = revision?.profile?.cover_template as Chosen | undefined;
  const savedKey = saved ? `${saved.id}@${saved.version}` : "";
  const [choice, setChoice] = useState(savedKey);
  const [busy, setBusy] = useState(false);
  const [issue, setIssue] = useState("");
  useEffect(() => { setChoice(savedKey); }, [savedKey]);
  const covers = (templates.data?.items || []).filter(item => item.category === "封面");
  const picked = covers.find(item => `${item.id}@${item.version}` === choice);
  async function save() {
    setBusy(true); setIssue("");
    try {
      const profile = { ...(revision?.profile || {}) };
      if (picked) profile.cover_template = { id: picked.id, version: picked.version }; else delete profile.cover_template;
      await api.post(`/content-personas/${personaId}/revisions`, { expected_revision: revision?.revision_no ?? 0, profile });
      await onSaved();
    } catch (cause) { setIssue(errorText(cause)); } finally { setBusy(false); }
  }
  const off = readOnly || busy;
  return <div className="space-y-2">
    <div className="flex gap-2">
      <select className={inputClass} aria-label="封面样式" value={choice} disabled={off || templates.isPending} onChange={event => setChoice(event.target.value)}>
        <option value="">不固定（第三方模型自己设计）</option>
        {covers.map(item => <option key={`${item.id}@${item.version}`} value={`${item.id}@${item.version}`}>{item.name} · {item.version}{item.status === "ready" ? "" : "（未验收）"}</option>)}
      </select>
      <Button type="button" disabled={off || choice === savedKey} onClick={() => void save()}>{busy ? "保存中…" : "保存"}</Button>
    </div>
    <p className="text-[12px] text-ink-500">选填。这个角色的视频封面都用这个 AE 封面模板出字（大标题、副标题、卖点），底图是成片开头的画面；只影响之后新开的剪辑任务。</p>
    {templates.isError && <ErrorBanner message={errorText(templates.error)} />}
    {picked && <Preview template={picked} aspect="9:16" />}
    {issue && <ErrorBanner message={issue} />}
  </div>;
}
