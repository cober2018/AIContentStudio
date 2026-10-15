import { FormEvent, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api, ApiError, currentUser } from "../../api";
import { Button, ErrorBanner, Field, Spinner, inputClass } from "../../components/ui";

type Purpose = "professional" | "style";
type Limits = { max_notes: number; max_excerpt_chars: number; max_total_chars: number };
type Connection = { configured: boolean; enabled: boolean; revision: number; vault_name: string; folders: string[]; root_path?: string; is_admin: boolean; limits: Limits };
type Selection = {
  source_document_id?: number; source_checksum?: string; connection_id?: string; connection_revision?: number; note_sha256: string; path: string; title: string; excerpt: string;
  purposes: Purpose[]; persona_id: number | null; unit_id: number | null; model_use_allowed: boolean;
};
type KnowledgeContext = { revision_no: number; checksum: string | null; items: Selection[]; limits: Limits };
type Unit = { id: number; title: string; persona_id: number; modality: string; status: string };
type SearchResult = { items: { path: string; title: string; snippet: string }[]; coverage: { scanned: number; skipped: number; truncated: boolean }; connection_revision: number };
type Note = { connection_id: string; connection_revision: number; path: string; title: string; note_sha256: string; text: string; char_count: number; byte_size: number; mtime_ns: number };

const DEFAULT_LIMITS: Limits = { max_notes: 5, max_excerpt_chars: 4000, max_total_chars: 6000 };
const purposeLabels: Record<Purpose, string> = { professional: "专业内容参考", style: "个人风格样本" };
const charCount = (value: string) => Array.from(value).length;
const messageOf = (error: unknown, fallback: string) => error instanceof Error ? error.message : fallback;

type PanelProps = { projectId: number; readOnly: boolean; onSaved?: () => Promise<void> };

export function ObsidianKnowledgePanel({ projectId, readOnly, onSaved }: PanelProps) {
  return <KnowledgePanel key={`${projectId}:${currentUser()}`} projectId={projectId} readOnly={readOnly} onSaved={onSaved} />;
}

function KnowledgePanel({ projectId, readOnly, onSaved }: PanelProps) {
  const queryClient = useQueryClient();
  const user = currentUser();
  const base = `/content-projects/${projectId}/knowledge`;
  const contextKey = ["project-knowledge", projectId, user];
  const connectionKey = ["obsidian-connection", user];
  const me = useQuery({ queryKey: ["project-operations-user", user], queryFn: () => api.get<{ role: string }>("/users/me"), retry: false });
  const writable = !readOnly && me.isSuccess && ["admin", "editor"].includes(me.data.role);
  const saved = useQuery({ queryKey: contextKey, queryFn: () => api.get<KnowledgeContext>(base), enabled: me.isSuccess, retry: false, staleTime: Infinity, refetchOnWindowFocus: false, refetchOnReconnect: false });
  const connection = useQuery({ queryKey: connectionKey, queryFn: () => api.get<Connection>("/obsidian/connection"), enabled: writable, retry: false, staleTime: Infinity, refetchOnWindowFocus: false, refetchOnReconnect: false });
  const units = useQuery({ queryKey: ["project-knowledge-units", projectId, user], queryFn: () => api.get<Unit[]>(`/content-projects/${projectId}/units`), enabled: writable, retry: false });
  const [draft, setDraft] = useState<Selection[] | null>(null);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult | null>(null);
  const [preview, setPreview] = useState<Note | null>(null);
  const [excerpt, setExcerpt] = useState("");
  const [choice, setChoice] = useState({ purposes: ["professional"] as Purpose[], persona_id: null as number | null, unit_id: null as number | null, model_use_allowed: false });
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const items = writable ? draft ?? saved.data?.items ?? [] : saved.data?.items ?? [];
  const limits = saved.data?.limits ?? connection.data?.limits ?? DEFAULT_LIMITS;
  const totalChars = items.reduce((total, item) => total + charCount(item.excerpt), 0);
  const excerptChars = charCount(excerpt);
  const excerptError = preview && (!excerpt.trim() ? "请选择非空原文片段。" : excerptChars > limits.max_excerpt_chars ? `片段最多 ${limits.max_excerpt_chars} 字，请缩短。` : !preview.text.includes(excerpt) ? "片段须完整保留原文中的连续内容，请勿改写。" : "");
  const canBrowse = writable && connection.data?.configured && connection.data.enabled;

  async function search(event: FormEvent) {
    event.preventDefault();
    if (!canBrowse || busy || !query.trim()) return;
    setBusy("正在检索已保存的笔记…"); setError(""); setNotice(""); setResults(null); setPreview(null);
    try { setResults(await api.get<SearchResult>(`${base}/notes?${new URLSearchParams({ q: query.trim(), limit: "20" })}`)); }
    catch (cause) { setError(messageOf(cause, "检索笔记失败")); }
    finally { setBusy(""); }
  }

  async function inspect(path: string) {
    if (!canBrowse || busy) return;
    setBusy("正在读取所选笔记…"); setError(""); setNotice(""); setPreview(null);
    try {
      const note = await api.get<Note>(`${base}/note?${new URLSearchParams({ path })}`);
      setPreview(note); setExcerpt(Array.from(note.text).slice(0, limits.max_excerpt_chars).join(""));
      setChoice({ purposes: ["professional"], persona_id: null, unit_id: null, model_use_allowed: false });
    } catch (cause) { setError(messageOf(cause, "读取笔记失败")); }
    finally { setBusy(""); }
  }

  function selectNote() {
    if (!writable || busy || !preview || excerptError || !choice.purposes.length) return;
    if (items.length >= limits.max_notes || totalChars + excerptChars > limits.max_total_chars) {
      setError(`每个版本最多 ${limits.max_notes} 篇笔记、合计 ${limits.max_total_chars} 字，请先移除或缩短已选内容。`); return;
    }
    setDraft([...items, { path: preview.path, title: preview.title, note_sha256: preview.note_sha256, connection_id: preview.connection_id, connection_revision: preview.connection_revision, excerpt, ...choice }]);
    setPreview(null); setError(""); setNotice("已加入待保存选择；保存后才会形成项目知识版本。");
  }

  async function save() {
    if (!writable || busy || draft === null || !saved.data) return;
    if (items.some(item => !item.purposes.length)) { setError("每篇笔记至少选择一种参考用途。"); return; }
    setBusy("正在保存知识选择…"); setError(""); setNotice("");
    try {
      const next = await api.put<KnowledgeContext>(base, {
        expected_revision: saved.data.revision_no,
        items: items.map(item => ({
          ...(item.source_document_id ? { source_document_id: item.source_document_id, source_checksum: item.source_checksum, note_sha256: item.note_sha256 } : { path: item.path, note_sha256: item.note_sha256, connection_id: item.connection_id, connection_revision: item.connection_revision, excerpt: item.excerpt }),
          purposes: item.purposes, persona_id: item.persona_id, unit_id: item.unit_id, model_use_allowed: item.model_use_allowed,
        })),
      });
      queryClient.setQueryData(contextKey, next); setDraft(null); setNotice(`已保存第 ${next.revision_no} 版，仅供新启动的创作使用。`);
      await onSaved?.();
    } catch (cause) {
      setError(cause instanceof ApiError && cause.status === 409 ? "保存未完成：知识版本、知识库连接或笔记内容已变化。可舍弃修改并重载，或移除待保存笔记后重新预览选用。" : messageOf(cause, "保存知识选择失败"));
    } finally { setBusy(""); }
  }

  async function reload() {
    if (busy) return;
    setBusy("正在重新读取已存版本…"); setError(""); setNotice("");
    try {
      const next = await api.get<KnowledgeContext>(base);
      queryClient.setQueryData(contextKey, next); setDraft(null); setPreview(null);
    } catch (cause) { setError(messageOf(cause, "重新读取失败")); }
    finally { setBusy(""); }
  }

  async function reloadConnection(): Promise<Connection | null> {
    if (!writable || busy) return null;
    setBusy("正在重新读取连接设置…"); setError(""); setNotice("");
    try {
      const next = await api.get<Connection>("/obsidian/connection");
      queryClient.setQueryData(connectionKey, next);
      setResults(null); setPreview(null);
      return next;
    } catch (cause) { setError(messageOf(cause, "重新读取连接设置失败")); return null; }
    finally { setBusy(""); }
  }

  return <section className="rounded-xl border border-slate-200 bg-white p-6 space-y-4" aria-label="Obsidian 知识参考">
    <div className="space-y-2">
      <h2 className="font-semibold">Obsidian 专业资料与个人风格</h2>
      <p className="text-sm text-slate-600">从已保存的笔记中选取专业内容或本人作品。参考资料不等于已核实的事实，需要作为证据的内容仍须确认并进入事实包。</p>
      <p className="text-xs text-slate-500">原笔记始终只读；明确选用并保存的片段会进入现有共享来源库。模型使用须单独勾选授权，更新仅作用于新启动的创作，历史稿件与已启动任务保留原版本。</p>
    </div>
    {me.isError && <ErrorBanner message="无法核对知识参考权限，请刷新重试。" />}
    {saved.isError && <><ErrorBanner message={messageOf(saved.error, "无法读取已存知识版本")} /><Button variant="secondary" disabled={!!busy} onClick={reload}>重新读取已存版本</Button></>}
    {error && <div role="alert"><ErrorBanner message={error} /></div>}
    <div role="status" aria-live="polite" className="text-sm text-slate-600">{busy || notice}</div>
    {(me.isPending || saved.isLoading) && <Spinner label="读取项目知识参考…" />}
    {saved.data && <>
      <div className="rounded-lg bg-slate-50 p-3 text-sm space-y-1">
        <p>已保存版本：{saved.data.revision_no ? `第 ${saved.data.revision_no} 版` : "尚未建立"}{draft !== null && writable ? " · 有未保存修改" : ""}</p>
        <p className="text-xs text-slate-500">当前选择 {items.length}/{limits.max_notes} 篇 · {totalChars}/{limits.max_total_chars} 字 · 每篇最多 {limits.max_excerpt_chars} 字</p>
        {saved.data.checksum && <details className="text-xs text-slate-500"><summary className="cursor-pointer">查看已存版本校验值</summary><p className="mt-1 break-all font-mono">{saved.data.checksum}</p></details>}
      </div>
      {items.length ? <ul className="space-y-3">{items.map((item, index) => <li key={`${item.source_document_id ?? "new"}:${item.path}:${index}`} className="rounded-lg border border-slate-200 p-4 space-y-3">
        <div className="flex flex-wrap justify-between gap-2"><div><h3 className="font-medium text-sm">{item.title}</h3><p className="break-all text-xs text-slate-500">{item.path} · {charCount(item.excerpt)} 字 · {item.source_document_id ? `来源 #${item.source_document_id}` : "待保存"}</p></div>{writable && <Button variant="danger" size="sm" disabled={!!busy} onClick={() => { setDraft(items.filter((_, itemIndex) => itemIndex !== index)); setNotice(""); }}>移除选择</Button>}</div>
        {writable ? <SelectionControls value={item} units={units.data ?? []} disabled={!!busy} onChange={value => { setDraft(items.map((row, itemIndex) => itemIndex === index ? { ...row, ...value } : row)); setNotice(""); }} /> : <p className="text-sm text-slate-600">{item.purposes.map(purpose => purposeLabels[purpose]).join("、")} · {scopeLabel(item, units.data ?? [])} · {item.model_use_allowed ? "允许模型使用" : "未允许模型使用"}</p>}
        <details><summary className="cursor-pointer text-sm text-slate-600">查看所选原文与来源版本</summary><pre className="mt-2 max-h-72 overflow-auto whitespace-pre-wrap break-words rounded bg-slate-50 p-3 text-sm font-sans">{item.excerpt}</pre><p className="mt-2 break-all text-xs text-slate-500">笔记版本：{item.note_sha256}</p>{item.source_checksum && <p className="break-all text-xs text-slate-500">所选片段校验值：{item.source_checksum}</p>}</details>
      </li>)}</ul> : <p className="text-sm text-slate-500">尚未选择知识参考或个人风格样本。</p>}
      {writable && <div className="flex flex-wrap gap-2"><Button disabled={!!busy || draft === null} onClick={save}>保存知识选择为新版本</Button><Button variant="secondary" disabled={!!busy} onClick={reload}>{draft !== null ? "舍弃修改并重载" : "重新读取已存版本"}</Button></div>}
    </>}
    {writable && <div className="border-t pt-4 space-y-4">
      {connection.isLoading && <p className="text-sm text-slate-500">读取知识库连接…</p>}
      {connection.isError && <><ErrorBanner message={messageOf(connection.error, "无法读取知识库连接")} /><Button variant="secondary" disabled={!!busy} onClick={() => { void connection.refetch(); }}>重试读取连接</Button></>}
      {connection.data && <>
        <p className="text-sm text-slate-600">{connection.data.configured ? `知识库：${connection.data.vault_name} · ${connection.data.enabled ? "已启用" : "已停用"}` : "尚未连接本地知识库，请管理员配置。"}{connection.data.configured && <span className="block mt-1 text-xs text-slate-500">检索范围：{connection.data.folders.length ? connection.data.folders.join("、") : "知识库内全部可读取的 Markdown 笔记"}</span>}</p>
        {me.isSuccess && me.data.role === "admin" && connection.data.is_admin && <ConnectionSettings key={connection.data.revision} connection={connection.data} disabled={!!busy} onBusy={setBusy} onReload={reloadConnection} onSaved={next => { queryClient.setQueryData(connectionKey, next); setResults(null); setPreview(null); setNotice("本地知识库连接已保存。"); }} />}
      </>}
      {units.isError && <ErrorBanner message="未能读取内容单元；目前可选择项目范围，已有角色或单元范围仍会保留。" />}
      <form onSubmit={search} className="flex flex-wrap items-end gap-2"><div className="min-w-0 flex-1"><Field label="搜索已保存的 Obsidian 笔记"><input className={inputClass} required value={query} disabled={!canBrowse || !!busy || !saved.data} onChange={event => setQuery(event.target.value)} placeholder="输入标题或正文关键词" /></Field></div><Button type="submit" disabled={!canBrowse || !!busy || !query.trim() || !saved.data}>检索笔记</Button></form>
      {results && <div className="space-y-3"><p className="text-xs text-slate-500">本次扫描 {results.coverage.scanned} 篇，跳过 {results.coverage.skipped} 项；返回 {results.items.length} 项（最多 20 项）。{results.coverage.truncated ? "已达到检索上限，结果未覆盖全部笔记，请缩小目录或关键词。" : "已完成本次可读取范围检索。"} · 连接版本 {results.connection_revision}</p>{results.items.length ? <ul className="space-y-2">{results.items.map(note => <li key={note.path} className="rounded-lg border p-3 space-y-2"><h3 className="font-medium text-sm">{note.title}</h3><p className="break-all text-xs text-slate-500">{note.path}</p><p className="whitespace-pre-wrap break-words text-sm text-slate-600">{note.snippet}</p><Button variant="secondary" size="sm" disabled={!!busy || !canBrowse} onClick={() => inspect(note.path)}>预览此笔记</Button></li>)}</ul> : <p className="text-sm text-slate-500">本次范围内未找到匹配笔记。</p>}</div>}
      {preview && canBrowse && <div className="rounded-lg border border-indigo-200 bg-indigo-50/40 p-4 space-y-3">
        <h3 className="font-medium">预览：{preview.title}</h3><p className="break-all text-xs text-slate-500">{preview.path} · 原文 {preview.char_count} 字</p>
        <details><summary className="cursor-pointer text-sm text-slate-600">查看完整已保存原文</summary><pre className="mt-2 max-h-80 overflow-auto whitespace-pre-wrap break-words rounded bg-white p-3 text-sm font-sans">{preview.text}</pre></details>
        <Field label="明确选用的原文片段" hint={`当前 ${excerptChars}/${limits.max_excerpt_chars} 字。须为原文中的连续片段，不在此处改写。`}><textarea className={inputClass} rows={7} value={excerpt} disabled={!!busy} onChange={event => setExcerpt(event.target.value)} /></Field>
        {preview.char_count > limits.max_excerpt_chars && <p className="text-xs text-amber-800">原文超出单篇上限，默认仅选取前 {limits.max_excerpt_chars} 字；可从完整原文复制替换为所需片段。</p>}
        {excerptError && <p role="alert" className="text-xs text-rose-700">{excerptError}</p>}
        <SelectionControls value={choice} units={units.data ?? []} disabled={!!busy} onChange={setChoice} />
        {!choice.purposes.length && <p className="text-xs text-rose-700">至少选择一种参考用途。</p>}
        <div className="flex flex-wrap gap-2"><Button disabled={!!busy || !!excerptError || !choice.purposes.length || items.length >= limits.max_notes || totalChars + excerptChars > limits.max_total_chars} onClick={selectNote}>明确选用笔记</Button><Button variant="secondary" disabled={!!busy} onClick={() => setPreview(null)}>关闭预览</Button></div>
      </div>}
    </div>}
  </section>;
}

type Choice = Pick<Selection, "purposes" | "persona_id" | "unit_id" | "model_use_allowed">;

function scopeLabel(choice: Choice, units: Unit[]) {
  if (choice.unit_id !== null) return `内容单元：${units.find(unit => unit.id === choice.unit_id)?.title ?? `#${choice.unit_id}`}`;
  if (choice.persona_id !== null) return `仅身份 #${choice.persona_id}`;
  return "项目内全部文字创作";
}

function SelectionControls({ value, units: allUnits, disabled, onChange }: { value: Choice; units: Unit[]; disabled: boolean; onChange: (value: Choice) => void }) {
  const units = allUnits.filter(unit => unit.modality === "text" && unit.status !== "archived");
  const scope = value.unit_id !== null ? `unit:${value.unit_id}` : value.persona_id !== null ? `persona:${value.persona_id}` : "project";
  const personaIds = [...new Set(units.map(unit => unit.persona_id))];
  return <fieldset disabled={disabled} className="space-y-3">
    <legend className="text-xs font-medium text-slate-500">参考用途与使用范围</legend>
    <div className="flex flex-wrap gap-4 text-sm">{(["professional", "style"] as Purpose[]).map(purpose => <label key={purpose} className="flex items-center gap-2"><input type="checkbox" checked={value.purposes.includes(purpose)} onChange={event => onChange({ ...value, purposes: event.target.checked ? [...value.purposes, purpose] : value.purposes.filter(item => item !== purpose) })} />{purposeLabels[purpose]}</label>)}</div>
    <Field label="用于哪些文字创作"><select className={inputClass} value={scope} onChange={event => { const [kind, id] = event.target.value.split(":"); onChange({ ...value, persona_id: kind === "persona" ? Number(id) : null, unit_id: kind === "unit" ? Number(id) : null }); }}><option value="project">项目内全部文字创作</option>{personaIds.map(id => <option key={`persona:${id}`} value={`persona:${id}`}>仅身份 #{id}</option>)}{value.persona_id !== null && value.unit_id === null && !personaIds.includes(value.persona_id) && <option value={scope}>仅身份 #{value.persona_id}（现有选择）</option>}{units.map(unit => <option key={`unit:${unit.id}`} value={`unit:${unit.id}`}>仅内容单元：{unit.title} · 身份 #{unit.persona_id}</option>)}{value.unit_id !== null && !units.some(unit => unit.id === value.unit_id) && <option value={scope}>仅内容单元 #{value.unit_id}（现有选择）</option>}</select></Field>
    <label className="flex items-start gap-2 text-sm"><input type="checkbox" className="mt-1" checked={value.model_use_allowed} onChange={event => onChange({ ...value, model_use_allowed: event.target.checked })} /><span>允许将此片段用于生成模型<span className="block text-xs text-slate-500">请确认作者与使用权限；未勾选时仅保存参考，不发送给生成模型。</span></span></label>
  </fieldset>;
}

function ConnectionSettings({ connection, disabled, onBusy, onReload, onSaved }: { connection: Connection; disabled: boolean; onBusy: (value: string) => void; onReload: () => Promise<Connection | null>; onSaved: (value: Connection) => void }) {
  const [rootPath, setRootPath] = useState(connection.root_path ?? "");
  const [folders, setFolders] = useState(connection.folders.join("\n"));
  const [enabled, setEnabled] = useState(connection.enabled);
  const [error, setError] = useState("");
  async function save(event: FormEvent) {
    event.preventDefault();
    if (disabled) return;
    onBusy("正在保存本地知识库连接…"); setError("");
    try { onSaved(await api.put<Connection>("/obsidian/connection", { root_path: rootPath.trim(), folders: folders.split("\n").map(folder => folder.trim()).filter(Boolean), enabled, expected_revision: connection.revision })); }
    catch (cause) { setError(cause instanceof ApiError && cause.status === 409 ? "连接设置已被其他操作更新，请重新读取连接设置后再修改。" : messageOf(cause, "保存连接失败")); }
    finally { onBusy(""); }
  }
  async function reload() {
    const next = await onReload();
    if (next) { setRootPath(next.root_path ?? ""); setFolders(next.folders.join("\n")); setEnabled(next.enabled); setError(""); }
  }
  return <details className="rounded-lg border border-slate-200 p-3"><summary className="cursor-pointer text-sm font-medium">管理员：本地知识库连接设置</summary><form onSubmit={save} className="mt-3 space-y-3"><p className="text-xs text-slate-500">仅连接本机目录，以已保存的 Markdown 为准。保存配置不会自动检索、导入笔记或修改 Vault。</p>{error && <div role="alert"><ErrorBanner message={error} /></div>}<Field label="知识库根目录（绝对路径）"><input className={inputClass} required value={rootPath} disabled={disabled} onChange={event => setRootPath(event.target.value)} /></Field><Field label="允许检索的子目录（每行一个）" hint="填写相对根目录的路径；留空表示知识库内全部可读取的 Markdown 笔记。"><textarea className={inputClass} rows={3} value={folders} disabled={disabled} onChange={event => setFolders(event.target.value)} /></Field><label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={enabled} disabled={disabled} onChange={event => setEnabled(event.target.checked)} />启用本地知识库连接</label><div className="flex flex-wrap gap-2"><Button type="submit" disabled={disabled}>保存连接设置</Button><Button variant="secondary" disabled={disabled} onClick={reload}>重新读取连接设置</Button></div></form></details>;
}
