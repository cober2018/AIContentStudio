import { useEffect, useState } from "react";
import { api, ApiError } from "../api";
import { Button, ErrorBanner, inputClass } from "../components/ui";

export const SPEECH_HINT = "选填。Obsidian 库里放这个角色真人口播逐字稿的文件夹，例如 逐字稿/角色名。写视频逐字稿时照它学说话方式，最近改过的优先，最多读 6000 字。";

function errorText(cause: unknown) {
  const detail = cause instanceof ApiError ? cause.detail as { message?: string } | string | undefined : undefined;
  return typeof detail === "object" && detail?.message ? detail.message : typeof detail === "string" ? detail : cause instanceof Error ? cause.message : "保存失败";
}

// 编辑资料: the folder saves as a new revision of the persona profile, like the portraits.
export function SpeechSampleFolderEditor({ personaId, revision, readOnly, onSaved }: {
  personaId: number; revision: { revision_no: number; profile: Record<string, unknown> } | undefined; readOnly: boolean; onSaved: () => Promise<void>;
}) {
  const saved = typeof revision?.profile?.speech_sample_folder === "string" ? revision.profile.speech_sample_folder as string : "";
  const [folder, setFolder] = useState(saved);
  const [busy, setBusy] = useState(false);
  const [issue, setIssue] = useState("");
  useEffect(() => { setFolder(saved); }, [saved]);
  async function save() {
    setBusy(true); setIssue("");
    try {
      const profile = { ...(revision?.profile || {}) };
      if (folder.trim()) profile.speech_sample_folder = folder.trim(); else delete profile.speech_sample_folder;
      await api.post(`/content-personas/${personaId}/revisions`, { expected_revision: revision?.revision_no ?? 0, profile });
      await onSaved();
    } catch (cause) { setIssue(errorText(cause)); } finally { setBusy(false); }
  }
  const off = readOnly || busy;
  return <div className="space-y-2">
    <div className="flex gap-2">
      <input className={inputClass} value={folder} placeholder="逐字稿/角色名" disabled={off} onChange={event => setFolder(event.target.value)} />
      <Button type="button" disabled={off || folder.trim() === saved} onClick={() => void save()}>{busy ? "保存中…" : "保存"}</Button>
    </div>
    <p className="text-[12px] text-ink-500">{SPEECH_HINT}</p>
    {issue && <ErrorBanner message={issue} />}
  </div>;
}
