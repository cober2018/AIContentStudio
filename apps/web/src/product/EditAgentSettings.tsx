import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api, currentUser } from "../api";
import { Button, ErrorBanner, Field, Spinner, inputClass } from "../components/ui";

type Settings = { enabled: boolean; assistant: "claude" | "codex"; assistants: Record<string, string>; dispatcher_seen_at: string | null };

export default function EditAgentSettings() {
  const query = useQuery({ queryKey: ["edit-agent-settings", currentUser()], queryFn: () => api.get<Settings>("/settings/edit-agent"), retry: false });
  const [draft, setDraft] = useState<{ enabled: boolean; assistant: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  if (query.isPending) return <Spinner label="读取自动剪辑设置…" />;
  if (query.error) return <ErrorBanner message={query.error instanceof Error ? query.error.message : "读取失败"} />;
  const data = query.data!;
  const value = draft || { enabled: data.enabled, assistant: data.assistant };
  const seen = data.dispatcher_seen_at ? (Date.now() - new Date(data.dispatcher_seen_at).getTime()) / 1000 : null;
  async function save() {
    setBusy(true); setError("");
    try { await api.put("/settings/edit-agent", value); setDraft(null); await query.refetch(); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "保存失败"); } finally { setBusy(false); }
  }
  return <section aria-label="自动剪辑" className="space-y-4 rounded-xl border border-slate-200 bg-white p-5">
    <h2 className="text-lg font-semibold">自动剪辑</h2>
    <p className="text-sm text-slate-600">准备剪辑完成后，本机后台会自动启动助手：领取剪辑任务，在达芬奇里剪辑调色，标了 AE 的镜头用 AE 做特效，渲染粗剪交回平台，等你审片。助手不会替你接受结果；同一时间只剪一条；出错不会自动重来。</p>
    {error && <ErrorBanner message={error} />}
    <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={value.enabled} disabled={busy} onChange={event => setDraft({ ...value, enabled: event.target.checked })} />准备好剪辑后自动开始</label>
    <Field label="用哪个助手剪"><select className={inputClass} value={value.assistant} disabled={busy} onChange={event => setDraft({ ...value, assistant: event.target.value })}>{Object.entries(data.assistants).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></Field>
    <p className={`text-sm ${seen !== null && seen < 180 ? "text-emerald-700" : "text-amber-800"}`}>{seen === null ? "本机后台还没连上。在终端运行 apps/api/scripts/install_edit_dispatcher.sh 安装一次即可。" : seen < 180 ? "本机后台在运行。" : `本机后台 ${Math.round(seen / 60)} 分钟没有响应，可能已停止。`}</p>
    <p className="text-xs text-slate-500">日志在 ~/AIContentStudio/edit-logs/，每个剪辑任务一个文件。每次剪辑用一次你自己的 Claude（或 Codex）账号。</p>
    <Button disabled={busy || !draft} onClick={() => void save()}>保存</Button>
  </section>;
}
