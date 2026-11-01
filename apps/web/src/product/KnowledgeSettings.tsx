import { FormEvent, useEffect, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api, ApiError, currentUser } from "../api";
import { Button, ErrorBanner, Field, Spinner, inputClass } from "../components/ui";

type Connection = { configured: boolean; enabled: boolean; revision: number; vault_name: string; folders: string[]; root_path?: string; is_admin: boolean };

const messageOf = (error: unknown, fallback: string) => error instanceof Error ? error.message : fallback;

// One vault serves both persona speaking style and project knowledge, so it is set once here rather than inside a project.
export default function KnowledgeSettings() {
  const queryClient = useQueryClient();
  // Shares the project page's cache key so a save here is what the project page shows next.
  const key = ["obsidian-connection", currentUser()];
  const connection = useQuery({ queryKey: key, queryFn: () => api.get<Connection>("/obsidian/connection"), retry: false, staleTime: Infinity, refetchOnWindowFocus: false, refetchOnReconnect: false });
  const [rootPath, setRootPath] = useState("");
  const [folders, setFolders] = useState("");
  const [enabled, setEnabled] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const data = connection.data;
  useEffect(() => {
    if (!data) return;
    setRootPath(data.root_path ?? ""); setFolders(data.folders.join("\n")); setEnabled(data.enabled);
  }, [data]);

  async function save(event: FormEvent) {
    event.preventDefault();
    if (!data || busy) return;
    setBusy(true); setError(""); setNotice("");
    try {
      const next = await api.put<Connection>("/obsidian/connection", { root_path: rootPath.trim(), folders: folders.split("\n").map(folder => folder.trim()).filter(Boolean), enabled, expected_revision: data.revision });
      queryClient.setQueryData(key, next); setNotice("知识库连接已保存。");
    } catch (cause) { setError(cause instanceof ApiError && cause.status === 409 ? "连接设置已被其他操作更新，请重新读取后再修改。" : messageOf(cause, "保存连接失败")); }
    finally { setBusy(false); }
  }

  if (connection.isLoading) return <Spinner label="读取知识库连接…" />;
  if (connection.isError || !data) return <ErrorBanner message={messageOf(connection.error, "无法读取知识库连接")} />;
  const editable = data.is_admin;
  return <section className="rounded-xl border border-slate-200 bg-white p-6 space-y-4" aria-label="知识库">
    <div className="space-y-1">
      <h2 className="font-semibold">Obsidian 知识库</h2>
      <p className="text-sm text-slate-600">同一个知识库有两种用途：角色页填的逐字稿文件夹用来学说话方式，可以是库里任意文件夹；项目「来源与证据」里检索选用笔记，只在下面允许的子目录里找。</p>
      <p className="text-xs text-slate-500">只读本机目录里的 Markdown，不改动知识库。</p>
    </div>
    {error && <div role="alert"><ErrorBanner message={error} /></div>}
    {notice && <p role="status" className="text-sm text-emerald-700">{notice}</p>}
    {!editable && <p className="text-sm text-slate-500">只有管理员可以修改。</p>}
    <form onSubmit={save} className="space-y-3">
      <Field label="知识库根目录（绝对路径）"><input className={inputClass} required value={rootPath} disabled={!editable || busy} onChange={event => setRootPath(event.target.value)} /></Field>
      <Field label="项目可检索的子目录（每行一个）" hint="相对根目录的路径；留空表示整个知识库。只限制项目里的笔记检索，不限制角色的逐字稿文件夹。"><textarea className={inputClass} rows={3} value={folders} disabled={!editable || busy} onChange={event => setFolders(event.target.value)} /></Field>
      <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={enabled} disabled={!editable || busy} onChange={event => setEnabled(event.target.checked)} />启用知识库连接</label>
      {editable && <div className="flex flex-wrap gap-2"><Button type="submit" disabled={busy}>{busy ? "保存中…" : "保存"}</Button><Button variant="secondary" disabled={busy} onClick={() => { setNotice(""); void connection.refetch(); }}>重新读取</Button></div>}
    </form>
  </section>;
}
