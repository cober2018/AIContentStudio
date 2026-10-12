import { useEffect, useLayoutEffect, useRef, useState, type FormEvent } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api, ApiError, currentUser } from "../api";
import { Button, ErrorBanner, Field, Spinner, inputClass } from "../components/ui";
import { capabilityApi, checkedPage, checkedPreferenceEdits, contextQuery, emptyArgsSchema, kindLabels, parseArgsSchema, parseObject, preferenceEditReference, queryString, scopeFromFields, scopeLabels, scopeText, statusLabels } from "./capabilityMemoryTypes";
import type { ArgumentProperty, CapabilityArtifact, CapabilityContext, CapabilityDefinition, CapabilityKind, CapabilityOutcome, CapabilityRevision, CapabilityScopeType, CapabilityStatus, CapabilityUseResult, JsonObject, SavedPreferenceEdit } from "./capabilityMemoryTypes";

export interface CapabilityMemoryPanelProps extends CapabilityContext {
  readOnly?: boolean;
  learningCandidate?: { id: number; revision_no: number };
  onDirtyChange?: (dirty: boolean) => void;
}
const box = "space-y-4 rounded-xl border border-slate-200 bg-white p-5";
const discardMessage = "能力方法有未保存的编辑。离开会丢弃本地草稿，确认离开？";
function useDraftDirty(dirty: boolean, onDirtyChange?: (dirty: boolean) => void) {
  useLayoutEffect(() => { onDirtyChange?.(dirty); }, [dirty, onDirtyChange]);
  useLayoutEffect(() => () => onDirtyChange?.(false), [onDirtyChange]);
}
function useMemoryNavigationGuard(dirty: boolean, managed: boolean) {
  useLayoutEffect(() => {
    if (!dirty || managed) return;
    let retainedState = window.history.state;
    let retainedUrl = window.location.href;
    let restoringHistory = false;
    let allowDocumentExit = false;
    let allowHistoryExit = false;
    const navigation = (window as Window & { navigation?: EventTarget }).navigation;
    const warnTraverse = (event: Event) => {
      const change = event as Event & { navigationType: string; destination: { url: string; sameDocument: boolean } };
      if (change.navigationType !== "traverse" || !event.cancelable || !change.destination.sameDocument) return;
      const destination = new URL(change.destination.url);
      if (destination.pathname === window.location.pathname && destination.search === window.location.search) return;
      // Confirm before BrowserRouter receives the committed popstate and unmounts the editor.
      if (!window.confirm(discardMessage)) event.preventDefault();
      else allowHistoryExit = true;
    };
    const warn = (event: BeforeUnloadEvent) => { if (!allowDocumentExit) { event.preventDefault(); event.returnValue = ""; } };
    const warnNavigation = (event: MouseEvent) => {
      if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      const link = event.target instanceof Element ? event.target.closest<HTMLAnchorElement>("a[href]") : null;
      if (!link || (link.target && link.target !== "_self") || link.hasAttribute("download")) return;
      const destination = new URL(link.href, window.location.href);
      if (destination.origin === window.location.origin && destination.pathname === window.location.pathname && destination.search === window.location.search) return;
      if (!window.confirm(discardMessage)) { event.preventDefault(); event.stopPropagation(); }
      else if (destination.origin !== window.location.origin) allowDocumentExit = true;
    };
    const warnHistory = (event: PopStateEvent) => {
      if (allowHistoryExit) { allowHistoryExit = false; return; }
      // Restore cancelled history before BrowserRouter can unmount the draft.
      if (restoringHistory) {
        event.stopImmediatePropagation();
        if (typeof retainedState?.idx === "number" && typeof event.state?.idx === "number" && retainedState.idx !== event.state.idx) {
          window.history.go(retainedState.idx - event.state.idx); return;
        }
        restoringHistory = false; return;
      }
      const retained = new URL(retainedUrl);
      if ((window.location.pathname === retained.pathname && window.location.search === retained.search) || window.confirm(discardMessage)) {
        retainedState = window.history.state; retainedUrl = window.location.href; return;
      }
      event.stopImmediatePropagation();
      const oldIndex = retainedState?.idx, nextIndex = event.state?.idx;
      if (typeof oldIndex === "number" && typeof nextIndex === "number" && oldIndex !== nextIndex) {
        restoringHistory = true; window.history.go(oldIndex - nextIndex);
      } else window.history.pushState(retainedState, "", retainedUrl);
    };
    window.addEventListener("beforeunload", warn);
    window.addEventListener("popstate", warnHistory, true);
    navigation?.addEventListener("navigate", warnTraverse);
    document.addEventListener("click", warnNavigation, true);
    return () => { window.removeEventListener("beforeunload", warn); window.removeEventListener("popstate", warnHistory, true); navigation?.removeEventListener("navigate", warnTraverse); document.removeEventListener("click", warnNavigation, true); };
  }, [dirty, managed]);
}
function errorText(error: unknown) {
  if (error instanceof ApiError && error.message === "[object Object]") {
    return ({ 401: "当前身份未通过验证，请重新核对身份。", 403: "当前用户没有此操作权限。", 404: "记录不存在或不适用于当前范围。", 409: "版本、范围或来源条件已变化，请核对最新记录。", 422: "内容或参数未通过后端校验，请核对大小、参数定义、来源与安全限制。", 503: "能力方法服务暂不可用，不能确认操作成功。" } as Record<number, string>)[error.status] ?? `请求失败（HTTP ${error.status}）。`;
  }
  return error instanceof Error ? error.message : "请求失败，请重试。";
}
function RecordView({ value, label }: { value: unknown; label: string }) {
  return <details className="rounded-lg border border-slate-200 p-3 text-sm"><summary className="cursor-pointer text-slate-600">{label}</summary><pre className="mt-3 max-h-80 overflow-auto whitespace-pre-wrap break-all text-xs">{value == null ? "未返回" : JSON.stringify(value, null, 2)}</pre></details>;
}
function useWrite() {
  const client = useQueryClient();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [conflict, setConflict] = useState(false);
  const [notice, setNotice] = useState("");
  async function run<T>(action: () => Promise<T>, done?: (result: T) => void) {
    if (busy || conflict) return;
    setBusy(true); setError(""); setNotice("");
    try {
      const result = await action();
      done?.(result); setNotice("后端已确认操作。");
      await client.invalidateQueries({ queryKey: ["capability-memory", currentUser()] });
    } catch (cause) {
      setError(errorText(cause)); setConflict(cause instanceof ApiError && cause.status === 409);
    } finally { setBusy(false); }
  }
  return { busy, error, conflict, notice, run, setError, setConflict };
}
type WriteState = ReturnType<typeof useWrite>;
function WriteStatus({ state }: { state: WriteState }) {
  return <>{state.error && <div role="alert"><ErrorBanner message={state.error} /></div>}{state.conflict && <p role="alert" className="text-sm text-amber-800">记录已变化或当前操作条件不满足。本地内容和参数已保留；不会自动重试写入。</p>}{state.notice && <p role="status" className="text-sm text-emerald-700">{state.notice}</p>}</>;
}
function ConflictReview({ id, state, onAdopt }: { id: number; state: WriteState; onAdopt: (artifact: CapabilityArtifact) => void }) {
  const [remote, setRemote] = useState<CapabilityArtifact>();
  const [reading, setReading] = useState(false);
  if (!state.conflict) return null;
  return <div className="space-y-3 rounded-lg border border-amber-200 bg-amber-50 p-3">
    <Button variant="secondary" disabled={reading} onClick={() => {
      setReading(true); setRemote(undefined);
      void capabilityApi.detail(id).then(setRemote).catch(cause => state.setError(errorText(cause))).finally(() => setReading(false));
    }}>{reading ? "读取中…" : "读取最新版本（保留本地编辑）"}</Button>
    {remote && <><p className="text-sm">服务端 v{remote.current_revision.revision_no} · {statusLabels[remote.status]} · {scopeText(remote.scope_type, remote.scope)}</p><RecordView value={remote.current_revision} label="核对最新服务端内容、参数与来源" /><Button variant="secondary" onClick={() => {
      if (!window.confirm(`已核对服务端 v${remote.current_revision.revision_no}？保留本地编辑，下一次提交将基于此版本；服务端仍会检查冲突。`)) return;
      onAdopt(remote); state.setConflict(false); state.setError(""); setRemote(undefined);
    }}>已核对，保留本地编辑继续</Button></>}
  </div>;
}

interface DefinitionDraft { kind: CapabilityKind; name: string; text: string; tags: string; args: string }
function newDraft(kind: CapabilityKind = "prompt_skill"): DefinitionDraft {
  return { kind, name: "", text: "", tags: "", args: JSON.stringify(emptyArgsSchema, null, 2) };
}
function DefinitionFields({ draft, change, disabled, identity = true }: { draft: DefinitionDraft; change: (patch: Partial<DefinitionDraft>) => void; disabled: boolean; identity?: boolean }) {
  return <div className="space-y-3">
    {identity && <div className="grid gap-3 sm:grid-cols-2"><Field label="方法类型"><select className={inputClass} disabled={disabled} value={draft.kind} onChange={event => change({ kind: event.target.value as CapabilityKind })}>{Object.entries(kindLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></Field><Field label="方法名称"><input className={inputClass} required maxLength={200} disabled={disabled} value={draft.name} onChange={event => change({ name: event.target.value })} /></Field></div>}
    <Field label="方法正文" hint="最多 8192 UTF-8 字节（中文通常每字 3 字节）；参数占位符使用 {{参数名}}。工具仅为定义，不在后端执行。"><textarea className={`${inputClass} min-h-36`} required maxLength={8192} disabled={disabled} value={draft.text} onChange={event => change({ text: event.target.value })} /></Field>
    <Field label="标签" hint="用逗号分隔。"><input className={inputClass} maxLength={2000} disabled={disabled} value={draft.tags} onChange={event => change({ tags: event.target.value })} /></Field>
    <details className="rounded-lg border border-slate-200 p-3"><summary className="cursor-pointer text-sm text-slate-600">高级：参数定义（JSON Schema）</summary><Field label="参数 schema" hint="仅支持 object 中的 string、number、integer、boolean、required 和有限 enum。"><textarea className={`${inputClass} mt-3 min-h-36 font-mono text-xs`} disabled={disabled} value={draft.args} onChange={event => change({ args: event.target.value })} /></Field></details>
  </div>;
}
function definition(draft: DefinitionDraft, previous: JsonObject = {}): CapabilityDefinition {
  if (!draft.text.trim() || !draft.name.trim()) throw new Error("请填写方法名称与正文。");
  const text = draft.text.normalize("NFC");
  if (new TextEncoder().encode(text).length > 8192) throw new Error("方法正文超过 8192 UTF-8 字节；中文通常每字 3 字节，请缩短正文。");
  const tags = [...new Set(draft.tags.split(/[,，]/).map(tag => tag.trim()).filter(Boolean))];
  if (tags.length > 30 || tags.some(tag => new TextEncoder().encode(tag).length > 100)) throw new Error("最多 30 个标签，每个标签最多 100 UTF-8 字节。");
  return {
    kind: draft.kind, name: draft.name.trim(),
    content: { ...previous, text, tags },
    args_schema: parseArgsSchema(draft.args),
  };
}
function CaptureForm({ editable, context, learningCandidate, execution = false, onCreated, onDirtyChange }: {
  editable: boolean; context: CapabilityContext; learningCandidate?: CapabilityMemoryPanelProps["learningCandidate"]; execution?: boolean; onCreated: (id: number) => void; onDirtyChange: (dirty: boolean) => void;
}) {
  const [draft, setDraft] = useState(() => newDraft(learningCandidate ? "creative_pattern" : "prompt_skill"));
  const [executionId, setExecutionId] = useState(context.executionId?.toString() ?? "");
  const [learningSource, setLearningSource] = useState(learningCandidate);
  const [refreshedSource, setRefreshedSource] = useState<{ id: number; revision_no: number; status: string }>();
  const [readingSource, setReadingSource] = useState(false);
  const [created, setCreated] = useState<CapabilityArtifact>();
  const state = useWrite();
  const initial = useRef({ draft, executionId });
  useDraftDirty(!created && (state.busy || state.conflict || JSON.stringify({ draft, executionId }) !== JSON.stringify(initial.current)), onDirtyChange);
  const title = learningCandidate ? `从学习候选 #${learningCandidate.id} 创建方法候选` : execution ? "从已接受的执行保留方法" : "新建方法候选";
  function send(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!editable || state.busy || state.conflict || created) return;
    void state.run(async () => {
      const body = definition(draft);
      if (learningSource) return capabilityApi.captureLearning({ ...body, learning_candidate_id: learningSource.id, expected_learning_revision: learningSource.revision_no });
      if (execution) {
        const id = Number(executionId);
        if (!Number.isSafeInteger(id) || id < 1) throw new Error("执行 ID 必须是正整数。");
        return capabilityApi.captureExecution({ ...body, execution_id: id });
      }
      return capabilityApi.create({ ...body, scope_type: context.projectId ? "project" : "owner", scope: context.projectId ? { id: context.projectId } : {} });
    }, result => { setCreated(result); onCreated(result.id); });
  }
  return <form className={box} onSubmit={send}><h3 className="font-semibold">{title}</h3>
    <p className="text-sm text-slate-600">{learningSource ? `冻结来源修订 v${learningSource.revision_no}；后端核对已接受决定及支持证据并冻结安全引用。接受学习候选本身不会创建方法，也不改变内容记忆。` : execution ? "必须整单执行已接受并满足冻结的必需成果合同；只接受一个成果不够。后端冻结来源并去重；捕获失败不改变成果接受状态。" : `仅创建候选，范围为${context.projectId ? `项目 #${context.projectId}` : "本人"}；保存或固定须另行确认。`}</p>
    {execution && <Field label="整单已接受的执行 ID"><input className={inputClass} type="number" required min="1" step="1" disabled={!editable || state.busy} value={executionId} onChange={event => { setExecutionId(event.target.value); setCreated(undefined); }} /></Field>}
    <DefinitionFields draft={draft} disabled={!editable || state.busy} change={patch => { setDraft(previous => ({ ...previous, ...patch })); setCreated(undefined); }} />
    <WriteStatus state={state} />
    {state.conflict && (learningSource ? <div className="space-y-3"><Button variant="secondary" disabled={readingSource} onClick={() => {
      setReadingSource(true); setRefreshedSource(undefined);
      void api.get<{ id: number; revision_no: number; status: string }>(`/learning-candidates/${learningSource.id}`).then(setRefreshedSource).catch(cause => state.setError(errorText(cause))).finally(() => setReadingSource(false));
    }}>读取最新学习来源（保留方法表单）</Button>{refreshedSource && <><RecordView value={refreshedSource} label="核对最新决定与冻结证据" /><Button variant="secondary" disabled={refreshedSource.status !== "accepted" || !Number.isSafeInteger(refreshedSource.revision_no)} onClick={() => {
      if (!window.confirm(`已核对学习候选 #${refreshedSource.id} 的已接受修订 v${refreshedSource.revision_no}？保留方法表单，并明确使用这个来源版本。`)) return;
      setLearningSource({ id: refreshedSource.id, revision_no: refreshedSource.revision_no }); state.setConflict(false); state.setError(""); setRefreshedSource(undefined);
    }}>确认最新来源，保留方法继续</Button></>}</div> : <Button variant="secondary" onClick={() => { state.setConflict(false); state.setError(""); }}>已核对来源条件，保留表单重新提交</Button>)}
    <Button type="submit" disabled={!editable || state.busy || state.conflict || !!created}>{state.busy ? "创建中…" : "明确创建方法候选"}</Button>
    {created && <p role="status" className="text-sm text-emerald-700">方法 #{created.id} · {statusLabels[created.status]} · v{created.current_revision.revision_no}。请另行审阅和提升。</p>}
  </form>;
}

function PreferenceCaptureForm({ editable, context, onCreated, onDirtyChange }: { editable: boolean; context: CapabilityContext; onCreated: (id: number) => void; onDirtyChange: (dirty: boolean) => void }) {
  const [project, setProject] = useState(context.projectId?.toString() ?? "");
  const [unit, setUnit] = useState(context.unitId?.toString() ?? "");
  const [name, setName] = useState("");
  const [preference, setPreference] = useState("");
  const [choices, setChoices] = useState<SavedPreferenceEdit[]>([]);
  const [selected, setSelected] = useState<SavedPreferenceEdit[]>([]);
  const [nextOffset, setNextOffset] = useState<number | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [reading, setReading] = useState(false);
  const [created, setCreated] = useState<CapabilityArtifact>();
  const requestEpoch = useRef(0);
  const state = useWrite();
  const initial = useRef({ project, unit, name, preference, selected });
  useDraftDirty(!created && (state.busy || state.conflict || JSON.stringify({ project, unit, name, preference, selected }) !== JSON.stringify(initial.current)), onDirtyChange);
  useEffect(() => () => { requestEpoch.current++; }, []);
  function clearSources() {
    requestEpoch.current++; setChoices([]); setSelected([]); setLoaded(false); setNextOffset(null); setCreated(undefined);
    state.setConflict(false); state.setError("");
  }
  async function readSources(offset = 0) {
    const projectId = Number(project), unitId = Number(unit);
    if (![projectId, unitId].every(id => Number.isSafeInteger(id) && id > 0)) { state.setError("请指定同一项目与内容单元的有效 ID。"); return; }
    const epoch = ++requestEpoch.current;
    setReading(true); state.setError("");
    try {
      const page = checkedPreferenceEdits(await capabilityApi.preferenceEdits(projectId, unitId, offset));
      if (epoch !== requestEpoch.current) return;
      setChoices(previous => offset === 0 ? page.items : [...previous.filter(edit => !page.items.some(item => item.master_revision_id === edit.master_revision_id)), ...page.items]);
      setLoaded(true); setNextOffset(page.next_offset); state.setConflict(false);
    } catch (cause) { if (epoch === requestEpoch.current) state.setError(errorText(cause)); }
    finally { if (epoch === requestEpoch.current) setReading(false); }
  }
  const staleSelection = selected.some(edit => !choices.some(item => JSON.stringify(preferenceEditReference(item)) === JSON.stringify(preferenceEditReference(edit))));
  const displayed = [...choices, ...selected.filter(edit => !choices.some(item => item.master_revision_id === edit.master_revision_id))];
  return <form aria-label="重复保存编辑偏好候选" className={box} onSubmit={event => {
    event.preventDefault(); if (!editable || state.busy || state.conflict || reading || created || staleSelection || selected.length < 2) return;
    void state.run(async () => {
      const content = preference.normalize("NFC").trim(), title = name.normalize("NFC").trim();
      if (!content || !title || new TextEncoder().encode(content).length > 2048 || new TextEncoder().encode(title).length > 255) throw new Error("请填写有界的名称与偏好正文（正文最多 2048 UTF-8 字节）。");
      const result = await capabilityApi.capturePreference({ project_id: Number(project), unit_id: Number(unit), name: title,
        preference: content, edits: selected.map(preferenceEditReference) });
      if (result.kind !== "preference" || result.status !== "candidate" || result.scope_type !== "project" || result.scope.id !== Number(project)) throw new Error("服务端未确认项目范围的偏好候选，请核对记录。");
      return result;
    }, result => { setCreated(result); onCreated(result.id); });
  }}><h3 className="font-semibold">从重复保存编辑保留偏好候选</h3><p className="text-sm text-slate-600">选择同一项目、同一内容单元至少两次由你明确保存且实际改变内容的编辑，再写下你想保留的偏好。首稿、升级、工作流种子、仅上下文/意图/成片确认变化和未保存 AI 修改不计入；只冻结修订、父修订与哈希，不复制正文。</p>
    <div className="grid gap-3 sm:grid-cols-2"><Field label="偏好来源项目 ID"><input aria-label="偏好来源项目 ID" className={inputClass} type="number" min="1" required value={project} disabled={!editable || state.busy || reading || context.projectId !== undefined} onChange={event => { setProject(event.target.value); clearSources(); }} /></Field><Field label="偏好来源单元 ID"><input aria-label="偏好来源单元 ID" className={inputClass} type="number" min="1" required value={unit} disabled={!editable || state.busy || reading || context.unitId !== undefined} onChange={event => { setUnit(event.target.value); clearSources(); }} /></Field></div>
    <div className="flex flex-wrap gap-2"><Button variant="secondary" disabled={!editable || reading || state.busy} onClick={() => void readSources()}>{reading ? "读取保存编辑中…" : "读取已保存的人工编辑"}</Button>{nextOffset !== null && <Button variant="secondary" disabled={!editable || reading || state.busy} onClick={() => void readSources(nextOffset)}>读取下一批历史编辑</Button>}</div>
    {loaded && <p className="text-xs text-slate-500">已读 {choices.length} 次可选编辑 · 已选 {selected.length} 次（最多 20 次）。读取和刷新不创建候选，保留偏好正文与原选择。</p>}
    {loaded && !displayed.length && <p className="text-sm text-slate-500">当前读取的历史没有符合条件的人工内容编辑。</p>}
    <fieldset disabled={!editable || reading || state.busy || !!created} className="space-y-2">{displayed.map(edit => <label key={edit.master_revision_id} className="block space-y-1 rounded-lg border border-slate-200 p-3 text-xs"><span className="flex items-center gap-2"><input aria-label={`选择已保存编辑 #${edit.master_revision_id}`} type="checkbox" checked={selected.some(item => item.master_revision_id === edit.master_revision_id)} disabled={selected.length >= 20 && !selected.some(item => item.master_revision_id === edit.master_revision_id)} onChange={event => { setSelected(previous => event.target.checked ? [...previous, edit] : previous.filter(item => item.master_revision_id !== edit.master_revision_id)); setCreated(undefined); }} />Master #{edit.master_revision_id} · v{edit.revision_no} · 父修订 #{edit.parent_revision_id} · {edit.payload_schema}</span><span className="block break-all">内容 hash {edit.payload_hash} · 上下文 hash {edit.context_hash}</span><span className="block break-all">父内容 hash {edit.parent_payload_hash} · 保存时间 {edit.created_at}</span></label>)}</fieldset>
    {staleSelection && <p role="alert" className="text-sm text-amber-800">所选来源已变化或不再出现在清单。本地偏好与原选择仍保留；请取消该选择并明确选择最新来源。</p>}
    <Field label="偏好候选名称"><input aria-label="偏好候选名称" className={inputClass} required maxLength={255} disabled={!editable || state.busy || !!created} value={name} onChange={event => setName(event.target.value)} /></Field><Field label="要保留的人工偏好" hint="最多 2048 UTF-8 字节；中文通常每字 3 字节。"><textarea aria-label="要保留的人工偏好" className={`${inputClass} min-h-28`} required maxLength={2048} disabled={!editable || state.busy || !!created} value={preference} onChange={event => setPreference(event.target.value)} /></Field>
    <WriteStatus state={state} /><Button type="submit" disabled={!editable || reading || state.busy || state.conflict || !!created || staleSelection || selected.length < 2 || !name.trim() || !preference.trim()}>{state.busy ? "捕获中…" : "明确创建项目偏好候选"}</Button><p className="text-xs text-slate-500">候选不会自动应用或扩大范围，也不改正文、角色、事实、工作流或内容记忆。保存、固定或改变范围须在候选详情中另行明确操作。</p>{created && <p role="status" className="text-sm text-emerald-700">已创建偏好候选 #{created.id} · 项目 #{project}。请另行审阅后保存或固定。</p>}
  </form>;
}

function RevisionEditor({ artifact, editable, close, onDirtyChange }: { artifact: CapabilityArtifact; editable: boolean; close: () => void; onDirtyChange: (dirty: boolean) => void }) {
  const [source, setSource] = useState(artifact.current_revision);
  const [expected, setExpected] = useState(source.revision_no);
  const [draft, setDraft] = useState<DefinitionDraft>(() => ({ ...newDraft(artifact.kind), name: artifact.name, text: typeof source.content.text === "string" ? source.content.text : "", tags: Array.isArray(source.content.tags) ? source.content.tags.join(", ") : "", args: JSON.stringify(source.args_schema ?? emptyArgsSchema, null, 2) }));
  const state = useWrite();
  const initial = useRef(draft);
  useDraftDirty(state.busy || state.conflict || JSON.stringify(draft) !== JSON.stringify(initial.current), onDirtyChange);
  return <form className={box} onSubmit={event => {
    event.preventDefault(); if (!editable) return;
    void state.run(() => { const body = definition(draft, source.content); return capabilityApi.revise(artifact.id, { expected_revision: expected, content: body.content, args_schema: body.args_schema ?? emptyArgsSchema }); }, close);
  }}><h3 className="font-semibold">追加方法修订 · 基于 v{expected}</h3><p className="text-sm text-slate-600">保存会追加新版本，原内容、hash 和来源保持可读；不会改变任何正文。原有扩展内容字段保留。</p>
    <DefinitionFields draft={draft} change={patch => setDraft(previous => ({ ...previous, ...patch }))} disabled={!editable || state.busy} identity={false} />
    <WriteStatus state={state} /><ConflictReview id={artifact.id} state={state} onAdopt={remote => { setExpected(remote.current_revision.revision_no); setSource(remote.current_revision); }} />
    <div className="flex gap-2"><Button type="submit" disabled={!editable || state.busy || state.conflict}>保存为新修订</Button><Button variant="secondary" disabled={state.busy} onClick={() => { if (window.confirm("放弃这份本地编辑？")) close(); }}>取消编辑</Button></div>
  </form>;
}
function LifecycleEditor({ artifact, editable, close, onDirtyChange }: { artifact: CapabilityArtifact; editable: boolean; close: () => void; onDirtyChange: (dirty: boolean) => void }) {
  const [baseline, setBaseline] = useState(artifact);
  const [status, setStatus] = useState<CapabilityStatus>(artifact.status);
  const [scopeType, setScopeType] = useState<CapabilityScopeType>(artifact.scope_type);
  const [fields, setFields] = useState<Record<string, string>>(() => Object.fromEntries(Object.entries(artifact.scope).map(([key, value]) => [key, String(value)])));
  const [reviewedChange, setReviewedChange] = useState<string>();
  const state = useWrite();
  const initial = useRef({ status, scopeType, fields });
  useDraftDirty(state.busy || state.conflict || JSON.stringify({ status, scopeType, fields }) !== JSON.stringify(initial.current), onDirtyChange);
  function changeField(key: string, value: string) { setFields(previous => ({ ...previous, [key]: value })); setReviewedChange(undefined); }
  let nextScope: JsonObject | undefined;
  try { nextScope = scopeType === "owner" && baseline.scope_type === "owner" ? baseline.scope : scopeFromFields(scopeType, fields); } catch { nextScope = undefined; }
  const scopeChanged = scopeType !== baseline.scope_type || !nextScope || Object.keys(nextScope).length !== Object.keys(baseline.scope).length || Object.entries(nextScope).some(([key, value]) => baseline.scope[key] !== value);
  const changeFingerprint = JSON.stringify({ artifact_id: artifact.id, revision_id: baseline.current_revision.id,
    revision_no: baseline.current_revision.revision_no, content_hash: baseline.current_revision.content_hash,
    before: { status: baseline.status, scope_type: baseline.scope_type, scope: baseline.scope },
    after: { status, scope_type: scopeType, scope: nextScope } });
  const confirmed = reviewedChange === changeFingerprint;
  return <form className={box} onSubmit={event => {
    event.preventDefault(); if (!editable || state.busy || state.conflict) return;
    if (!window.confirm(`确认将方法 #${artifact.id} · v${baseline.current_revision.revision_no} 调整为「${statusLabels[status]}」${scopeChanged ? `，范围由 ${scopeText(baseline.scope_type, baseline.scope)} 改为 ${nextScope ? scopeText(scopeType, nextScope) : "未填写完整"}` : ""}？正文及参数保持这份精确修订，不会自动修改其他角色的配置。`)) return;
    void state.run(() => {
      const scope = scopeFromFields(scopeType, fields);
      if (scopeChanged && !confirmed) throw new Error("改变范围需要单独明确确认。");
      return capabilityApi.lifecycle(artifact.id, { expected_revision: baseline.current_revision.revision_no, status, ...(scopeChanged ? { scope_type: scopeType, scope, confirm_scope_broadening: true } : {}) });
    }, close);
  }}><h3 className="font-semibold">明确调整保存状态与范围</h3><p className="text-sm text-slate-600">当前范围：{scopeText(baseline.scope_type, baseline.scope)}。范围变化由后端校验所属关系并冻结新修订；归档或停用保留历史引用。</p>
    <fieldset disabled={!editable || state.busy} className="space-y-3"><div className="grid gap-3 sm:grid-cols-2"><Field label="目标状态"><select className={inputClass} value={status} onChange={event => { setStatus(event.target.value as CapabilityStatus); setReviewedChange(undefined); }}>{Object.entries(statusLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></Field><Field label="适用范围"><select className={inputClass} value={scopeType} onChange={event => { setScopeType(event.target.value as CapabilityScopeType); setReviewedChange(undefined); }}>{Object.entries(scopeLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></Field></div>
      {["persona", "account", "series", "project"].includes(scopeType) && <Field label={`${scopeLabels[scopeType]} ID`}><input className={inputClass} type="number" min="1" step="1" required value={fields.id ?? ""} onChange={event => changeField("id", event.target.value)} /></Field>}
      {scopeType === "channel" && <Field label="渠道代码"><input className={inputClass} required value={fields.channel_id ?? ""} onChange={event => changeField("channel_id", event.target.value)} /></Field>}
      {scopeType === "executor" && <div className="grid gap-3 sm:grid-cols-3">{["executor_kind", "executor_key", "executor_version"].map((key, index) => <Field key={key} label={["执行者种类", "执行者 key", "执行者版本"][index]}><input className={inputClass} required value={fields[key] ?? ""} onChange={event => changeField(key, event.target.value)} /></Field>)}</div>}
      {scopeChanged && <div className="space-y-2 rounded-lg bg-amber-50 p-3 text-sm text-amber-900"><p>审阅方法 #{baseline.id} · v{baseline.current_revision.revision_no} · revision #{baseline.current_revision.id}</p><p className="break-all text-xs">正文 hash：{baseline.current_revision.content_hash}；本次不改正文或参数。</p><p>状态差异：{statusLabels[baseline.status]} → {statusLabels[status]}</p><p>范围差异：{scopeText(baseline.scope_type, baseline.scope)} → {nextScope ? scopeText(scopeType, nextScope) : "目标范围尚未填写完整"}。</p><p>扩大为“本人”会让其他角色可明确选择此方法，但不会自动应用，也不会更改其他角色的 Skill、风格或流程。再次修改状态、目标范围或基准版本后必须重新确认。</p><label className="flex items-start gap-2"><input type="checkbox" checked={confirmed} disabled={!nextScope} onChange={event => setReviewedChange(event.target.checked ? changeFingerprint : undefined)} />我已核对上述精确版本与差异，明确确认改变适用范围。</label></div>}
    </fieldset><WriteStatus state={state} /><ConflictReview id={artifact.id} state={state} onAdopt={remote => { setBaseline(remote); setReviewedChange(undefined); }} />
    <div className="flex gap-2"><Button type="submit" disabled={!editable || state.busy || state.conflict || (scopeChanged && !confirmed)}>确认状态与范围</Button><Button variant="secondary" disabled={state.busy} onClick={() => { if (window.confirm("放弃本地状态与范围选择？")) close(); }}>取消调整</Button></div>
  </form>;
}

function RevisionView({ revision }: { revision: CapabilityRevision }) {
  return <div className="space-y-3 text-sm"><p>v{revision.revision_no} · revision #{revision.id}</p><p className="break-all text-xs text-slate-500">hash: {revision.content_hash}</p>
    {typeof revision.content.text === "string" && <p className="whitespace-pre-wrap rounded-lg bg-slate-50 p-3">{revision.content.text}</p>}
    <p className="text-xs text-slate-600">来源执行：{revision.source_execution_id == null ? "无" : `#${revision.source_execution_id}`} · 来源学习候选：{revision.source_learning_candidate_id == null ? "无" : `#${revision.source_learning_candidate_id}`} · {revision.created_by ?? "创建人未返回"} · {revision.created_at ?? "时间未返回"}</p>
    <RecordView value={revision.metadata} label="冻结范围与来源 metadata" /><RecordView value={{ content: revision.content, args_schema: revision.args_schema }} label="精确存储内容与参数定义" />
  </div>;
}
function argumentValue(property: ArgumentProperty, raw: string): string | number | boolean {
  if (property.enum) {
    const value: unknown = JSON.parse(raw);
    if (!property.enum.some(item => item === value)) throw new Error("参数不在允许的选项内。");
    return value as string | number | boolean;
  }
  if (property.type === "boolean") return raw === "true";
  if (property.type === "string") return raw;
  const value = Number(raw);
  if (!Number.isFinite(value) || (property.type === "integer" && !Number.isSafeInteger(value))) throw new Error("请输入有效数字或整数。");
  return value;
}
function UseForm({ artifact, revision, context, editable, eligible, optedOut, override }: { artifact: CapabilityArtifact; revision: CapabilityRevision; context: CapabilityContext; editable: boolean; eligible: boolean; optedOut: boolean; override: string }) {
  const [values, setValues] = useState<Record<string, string>>({});
  const [result, setResult] = useState<CapabilityUseResult>();
  const [outcome, setOutcome] = useState<CapabilityOutcome>("used");
  const [recordedOutcome, setRecordedOutcome] = useState<CapabilityOutcome>("used");
  const [outcomeNotice, setOutcomeNotice] = useState("");
  const [latestReceipt, setLatestReceipt] = useState<{ use_id: number; artifact_revision_id: number; outcome: CapabilityOutcome }>();
  const [readingUse, setReadingUse] = useState(false);
  const state = useWrite();
  const outcomeState = useWrite();
  const schema = revision.args_schema ?? emptyArgsSchema;
  // Retirement blocks new reuse, not observation of a use already recorded.
  const canUse = editable && eligible;
  const latestOutcome = latestReceipt?.use_id === result?.use_id && latestReceipt?.artifact_revision_id === result?.artifact_revision_id ? latestReceipt?.outcome : undefined;
  return <section className={box}><h3 className="font-semibold">已明确选择 {artifact.name} · v{revision.revision_no}</h3><p className="text-xs text-slate-600">{scopeText(artifact.scope_type, artifact.scope)} · revision #{revision.id}</p><p className="break-all text-xs text-slate-500">hash: {revision.content_hash}</p>
    {optedOut && <p className="text-sm text-amber-800">本任务已选择不采用此方法。可取消不采用后再明确请求渲染。</p>}
    {override.trim() && <p className="whitespace-pre-wrap rounded-lg bg-amber-50 p-3 text-sm">本任务人工覆盖说明：{override}。此说明仅保留在当前页面，不改方法，不追加到渲染内容。</p>}
    <form className="space-y-3" onSubmit={event => {
      event.preventDefault(); if (!canUse || optedOut || outcomeState.busy || readingUse) return;
      void state.run(() => {
        const args: JsonObject = {};
        Object.entries(schema.properties ?? {}).forEach(([name, property]) => {
          const value = values[name] ?? "";
          if (value === "") { if (schema.required?.includes(name)) throw new Error(`请填写参数 ${name}。`); return; }
          Object.defineProperty(args, name, { value: argumentValue(property, value), enumerable: true, writable: true, configurable: true });
        });
        return capabilityApi.use(artifact.id, { artifact_revision_id: revision.id, arguments: args, ...contextQuery(context) });
      }, value => { setResult(value); setRecordedOutcome(value.outcome ?? "used"); setOutcome(value.outcome ?? "used"); setOutcomeNotice(""); setLatestReceipt(undefined); outcomeState.setConflict(false); outcomeState.setError(""); });
    }}>
      {Object.entries(schema.properties ?? {}).map(([name, property]) => <Field key={name} label={`${name}${schema.required?.includes(name) ? "（必填）" : ""}`} hint={property.description}>{property.enum || property.type === "boolean" ? <select className={inputClass} required={schema.required?.includes(name)} disabled={!canUse || state.busy || optedOut} value={values[name] ?? ""} onChange={event => setValues(previous => ({ ...previous, [name]: event.target.value }))}><option value="">请选择</option>{(property.enum ?? [true, false]).map(item => <option key={JSON.stringify(item)} value={JSON.stringify(item)}>{String(item)}</option>)}</select> : <input className={inputClass} type={property.type === "string" ? "text" : "number"} step={property.type === "integer" ? "1" : "any"} required={schema.required?.includes(name)} disabled={!canUse || state.busy || optedOut} value={values[name] ?? ""} onChange={event => setValues(previous => ({ ...previous, [name]: event.target.value }))} />}</Field>)}
      <WriteStatus state={state} />{state.conflict && <Button variant="secondary" onClick={() => { state.setConflict(false); state.setError(""); }}>已核对当前范围，保留参数继续</Button>}
      <Button type="submit" disabled={!canUse || state.busy || outcomeState.busy || state.conflict || optedOut || readingUse}>{state.busy ? "渲染中…" : "渲染所选版本并记录使用"}</Button>
    </form>
    {result && <div className="space-y-3" role="status"><p className="text-sm">使用 #{result.use_id} · 精确 revision #{result.artifact_revision_id}</p><p className="break-all text-xs">内容 hash: {result.content_hash}<br />参数 hash: {result.rendered_arguments_hash}</p>
      {typeof result.rendered_content === "object" && result.rendered_content && !Array.isArray(result.rendered_content) && typeof result.rendered_content.text === "string" ? <p className="whitespace-pre-wrap rounded-lg bg-slate-50 p-3 text-sm">{result.rendered_content.text}</p> : typeof result.rendered_content === "string" ? <p className="whitespace-pre-wrap rounded-lg bg-slate-50 p-3 text-sm">{result.rendered_content}</p> : null}
      <RecordView value={result.rendered_content} label="完整渲染结果" /><p className="text-xs text-slate-500">结果供人工查看或交给 Agent。方法没有应用到保存正文，也没有注入模型提示；使用次数和结果不是发布表现证据。</p>
      <p className="text-xs text-slate-500">当前已记录结果：{recordedOutcome}；下一次明确修改以此结果进行 CAS 核对。</p>
      <form className="flex flex-wrap items-end gap-3" onSubmit={event => { event.preventDefault(); if (!editable || state.busy) return; void outcomeState.run(() => capabilityApi.outcome(result.use_id, outcome, recordedOutcome), () => { setRecordedOutcome(outcome); setOutcomeNotice(`使用结果已记录为 ${outcome}。`); }); }}><Field label="这次方法使用的结果"><select className={inputClass} disabled={!editable || outcomeState.busy || state.busy} value={outcome} onChange={event => setOutcome(event.target.value as CapabilityOutcome)}>{["used", "accepted", "rejected", "unknown"].map(value => <option key={value}>{value}</option>)}</select></Field><Button type="submit" variant="secondary" disabled={!editable || state.busy || outcomeState.busy || outcomeState.conflict}>明确记录使用结果</Button></form><WriteStatus state={outcomeState} />{outcomeNotice && <p className="text-sm text-emerald-700">{outcomeNotice}</p>}
      {outcomeState.conflict && <div className="space-y-3 rounded-lg border border-amber-200 bg-amber-50 p-3">
        <Button variant="secondary" disabled={!editable || readingUse} onClick={() => {
          setReadingUse(true); setLatestReceipt(undefined);
          void capabilityApi.readUse(result.use_id).then(receipt => {
            if (receipt.use_id !== result.use_id || receipt.artifact_revision_id !== result.artifact_revision_id || !["used", "accepted", "rejected", "unknown"].includes(receipt.outcome)) throw new Error("使用记录响应不匹配，不能继续回填。");
            setLatestReceipt(receipt);
          }).catch(cause => outcomeState.setError(errorText(cause))).finally(() => setReadingUse(false));
        }}>{readingUse ? "读取中…" : "读取这次使用的最新结果"}</Button>
        {latestOutcome && <><p className="text-sm">同一使用 #{result.use_id} 的服务端结果：{latestOutcome}。本地选择仍保留为 {outcome}。</p><Button variant="secondary" disabled={!editable} onClick={() => {
          if (!window.confirm(`已核对使用 #${result.use_id} 当前为 ${latestOutcome}？保留本地选择并以此结果继续 CAS 回填。`)) return;
          setRecordedOutcome(latestOutcome); setLatestReceipt(undefined); outcomeState.setConflict(false); outcomeState.setError("");
        }}>已核对最新结果，保留本地选择继续</Button></>}
      </div>}
    </div>}
  </section>;
}

function ArtifactDetail({ id, context, editable, optedOut, override, onDirtyChange }: { id: number; context: CapabilityContext; editable: boolean; optedOut: boolean; override: string; onDirtyChange: (dirty: boolean) => void }) {
  const query = useQuery({ queryKey: ["capability-memory", currentUser(), "detail", id], queryFn: () => capabilityApi.detail(id), retry: false, refetchOnWindowFocus: false });
  const history = useQuery({ queryKey: ["capability-memory", currentUser(), "history", id], queryFn: async () => { const value = await capabilityApi.history(id); if (!Array.isArray(value?.items)) throw new Error("历史响应不完整。"); return value.items; }, retry: false, refetchOnWindowFocus: false });
  const [editor, setEditor] = useState<"revision" | "lifecycle">();
  const [useRevision, setUseRevision] = useState<CapabilityRevision>();
  const [exportState, setExportState] = useState({ busy: false, error: "" });
  if (query.isPending && !query.data) return <Spinner label="读取方法详情…" />;
  if (!query.data) return <div className={box}><ErrorBanner message={errorText(query.error)} /><Button onClick={() => void query.refetch()}>重试详情</Button></div>;
  const artifact = query.data;
  async function exportFile() {
    if (exportState.busy) return;
    setExportState({ busy: true, error: "" });
    try {
      const document = await capabilityApi.export(id);
      const url = URL.createObjectURL(new Blob([JSON.stringify(document, null, 2)], { type: "application/json" }));
      const link = window.document.createElement("a"); link.href = url; link.download = `capability-${id}.json`; link.click(); URL.revokeObjectURL(url);
    } catch (cause) { setExportState({ busy: false, error: errorText(cause) }); return; }
    setExportState({ busy: false, error: "" });
  }
  return <section className={box}><h3 className="font-semibold">{artifact.name} · #{artifact.id} · {statusLabels[artifact.status]}</h3><p className="text-sm">{kindLabels[artifact.kind]} · {scopeText(artifact.scope_type, artifact.scope)}</p><p className="text-xs text-slate-500">来源：{artifact.source_kind} · 稳定 ID：capability_memory:{artifact.id} · 使用 {artifact.usage?.use_count ?? "未知"} 次 · 最近 {artifact.usage?.last_used ?? "未使用 / 未返回"}</p>
    {artifact.matched_scope && <RecordView value={artifact.matched_scope} label="本任务匹配范围" />}
    <RevisionView revision={artifact.current_revision} />
    <div className="flex flex-wrap gap-2"><Button variant="secondary" disabled={!editable || !!editor} onClick={() => setEditor("revision")}>编辑为新修订</Button><Button variant="secondary" disabled={!editable || !!editor} onClick={() => setEditor("lifecycle")}>保存 / 固定 / 归档 / 范围</Button><Button variant="secondary" disabled={exportState.busy} onClick={() => void exportFile()}>导出安全方法文件</Button><Button variant="secondary" onClick={() => { void query.refetch(); void history.refetch(); }}>刷新详情与历史</Button></div>
    {query.isError && <ErrorBanner message={`详情刷新失败，本地编辑已保留。${errorText(query.error)}`} />}
    {exportState.error && <ErrorBanner message={exportState.error} />}
    {editor === "revision" && <RevisionEditor artifact={artifact} editable={editable} close={() => setEditor(undefined)} onDirtyChange={onDirtyChange} />}
    {editor === "lifecycle" && <LifecycleEditor artifact={artifact} editable={editable} close={() => setEditor(undefined)} onDirtyChange={onDirtyChange} />}
    <div className="space-y-3"><h4 className="font-semibold">追加式版本历史</h4>{history.isPending ? <Spinner label="读取精确历史…" /> : history.isError ? <><ErrorBanner message={errorText(history.error)} /><Button variant="secondary" onClick={() => void history.refetch()}>重试历史</Button></> : history.data.map(revision => <article key={revision.id} className="space-y-3 rounded-lg border p-3"><RevisionView revision={revision} />{revision.id === artifact.current_revision.id ? <Button variant="secondary" disabled={!editable || optedOut || !["saved", "pinned"].includes(artifact.status)} onClick={() => setUseRevision(revision)}>明确选择 v{revision.revision_no} 并填写参数</Button> : <p className="text-xs text-slate-500">历史版本仅查看；新使用请选择当前修订。</p>}</article>)}</div>
    {useRevision && <UseForm key={useRevision.id} artifact={artifact} revision={useRevision} context={context} editable={editable} eligible={useRevision.id === artifact.current_revision.id && ["saved", "pinned"].includes(artifact.status)} optedOut={optedOut} override={override} />}
  </section>;
}

function FileImport({ editable, onCreated }: { editable: boolean; onCreated: (id: number) => void }) {
  const [document, setDocument] = useState<JsonObject>();
  const [filename, setFilename] = useState("");
  const [reading, setReading] = useState(false);
  const [imported, setImported] = useState<number>();
  const state = useWrite();
  return <form className={box} onSubmit={event => {
    event.preventDefault(); if (!editable || !document || reading || imported) return;
    if (!window.confirm("将这个方法文件导入为新的本地候选？后端重新扫描与鉴权，不复制原 owner、状态或来源 provenance。")) return;
    void state.run(() => capabilityApi.import(document), result => { setImported(result.id); onCreated(result.id); });
  }}><h3 className="font-semibold">导入方法文件</h3><p className="text-sm text-slate-600">仅接受已导出的版本化 JSON 文件。导入产生新本地 ID 与候选状态，需再审阅；Installed Skills 不通过此入口安装或提升。</p><Field label="选择方法 JSON 文件"><input className={inputClass} type="file" accept="application/json,.json" disabled={!editable || state.busy || reading} onChange={event => {
    const file = event.target.files?.[0]; setDocument(undefined); setImported(undefined); setFilename(file?.name ?? ""); state.setError(""); state.setConflict(false);
    if (!file) return; if (file.size > 65536) { state.setError("文件过大，请使用有界方法文档。"); return; }
    setReading(true); void file.text().then(text => setDocument(parseObject(text))).catch(cause => state.setError(errorText(cause))).finally(() => setReading(false));
  }} /></Field>{filename && <p className="text-xs text-slate-600">{filename}{reading ? " · 读取中" : document ? " · 已读取" : " · 待核对"}</p>}<WriteStatus state={state} /><Button type="submit" disabled={!editable || !document || state.busy || state.conflict || reading || !!imported}>明确导入为新候选</Button>{imported && <p className="text-sm text-emerald-700">已创建本地方法 #{imported}。</p>}</form>;
}
function InstalledSkills() {
  const query = useQuery({ queryKey: ["installed-skills", currentUser()], queryFn: capabilityApi.installedSkills, enabled: false, retry: false, refetchOnWindowFocus: false, refetchOnReconnect: false });
  return <section className={box}><h3 className="font-semibold">Installed Agent Skills · 独立外部清单</h3><p className="text-sm text-slate-600">点击后才读取配置目录清单；与能力方法库有独立来源和稳定 ID，同名不表示替换。此处只读，不安装、启用或提升技能。</p><Button variant="secondary" disabled={query.isFetching} onClick={() => void query.refetch()}>{query.isFetching ? "读取中…" : "明确读取 Installed Skills 清单"}</Button>
    {query.isError && <ErrorBanner message={errorText(query.error)} />}
    {query.data && (Array.isArray(query.data.items) ? <div className="space-y-3">{query.data.items.length ? query.data.items.map(skill => <article key={`${skill.source_kind}:${skill.id}`} className="rounded-lg border p-3 text-sm"><p className="font-medium">{skill.name}</p><p className="break-all text-xs text-slate-500">来源：{skill.source_kind} · 稳定 ID：{skill.id}</p>{skill.description && <p>{skill.description}</p>}</article>) : <p className="text-sm text-slate-500">本次读取没有返回已安装技能。</p>}</div> : <ErrorBanner message="Installed Skills 响应不完整，不能确认技能清单。" />)}
  </section>;
}

function CapabilityWorkspace({ projectId, unitId, executionId, readOnly = false, learningCandidate, onDirtyChange }: CapabilityMemoryPanelProps) {
  const context = { projectId, unitId, executionId };
  const inContext = projectId !== undefined || unitId !== undefined;
  const validContext = !inContext || (Number.isSafeInteger(projectId) && Number(projectId) > 0 && Number.isSafeInteger(unitId) && Number(unitId) > 0);
  const me = useQuery({ queryKey: ["capability-memory-user", currentUser()], queryFn: () => api.get<{ role: string }>("/users/me"), retry: false, refetchOnWindowFocus: false });
  const editable = validContext && !readOnly && me.isSuccess && !me.isFetching && ["admin", "editor"].includes(me.data.role);
  const [tab, setTab] = useState<"candidate" | "saved" | "pinned" | "archived">("candidate");
  const [retired, setRetired] = useState<"archived" | "deprecated">("archived");
  const [filters, setFilters] = useState({ kind: "", scope_type: "", q: "", tag: "" });
  const [offset, setOffset] = useState(0);
  const [selected, setSelected] = useState<number>();
  const [detailDirty, setDetailDirty] = useState(false);
  const [createDirty, setCreateDirty] = useState(false);
  const [captureDirty, setCaptureDirty] = useState(false);
  const [learningDirty, setLearningDirty] = useState(false);
  const [preferenceDirty, setPreferenceDirty] = useState(false);
  const dirty = detailDirty || createDirty || captureDirty || learningDirty || preferenceDirty;
  useDraftDirty(dirty, onDirtyChange);
  useMemoryNavigationGuard(dirty, !!onDirtyChange);
  function choose(id: number) {
    if (id === selected || (detailDirty && !window.confirm(discardMessage))) return;
    setSelected(id);
  }
  const [opened, setOpened] = useState({ create: false, capture: false, import: false, preference: false });
  const [visible, setVisible] = useState({ create: false, capture: false, import: false, preference: false });
  const [optOut, setOptOut] = useState(false);
  const [override, setOverride] = useState("");
  const status = tab === "archived" ? retired : tab;
  const query = useQuery({ queryKey: ["capability-memory", currentUser(), inContext ? "discover" : "list", projectId, unitId, executionId, status, filters, offset], queryFn: async () => {
    const params = queryString({ ...filters, limit: 20, offset, ...(inContext ? contextQuery(context) : { status }) });
    return checkedPage(await (inContext ? capabilityApi.discover(params) : capabilityApi.list(params)));
  }, enabled: validContext && me.isSuccess && !learningCandidate && ["admin", "editor", "viewer"].includes(me.data.role), retry: false, refetchOnWindowFocus: false });
  function toggle(key: keyof typeof opened) { setOpened(previous => ({ ...previous, [key]: true })); setVisible(previous => ({ ...previous, [key]: !previous[key] })); }
  const detail = selected && <ArtifactDetail key={selected} id={selected} context={context} editable={editable} optedOut={optOut} override={override} onDirtyChange={setDetailDirty} />;
  return <section aria-label={learningCandidate ? "学习到方法候选" : "能力方法库"} className="mb-5 space-y-4"><header><h2 className="text-lg font-semibold">{learningCandidate ? "将已接受学习转为方法候选" : inContext ? "本任务适用方法与偏好" : "能力方法库"}</h2><p className="mt-1 text-sm text-slate-600">{inContext ? `项目 #${projectId ?? "未指定"} / 单元 #${unitId ?? "未指定"} · 返回所有适用的已保存或固定方法，排序没有优先覆盖含义。` : "可复用的创作方法、偏好与工具定义；与内容记忆、事实、角色和已安装技能分别保留。"}</p></header>
    {me.isPending ? <Spinner label="核对当前用户权限…" /> : me.isError ? <div className="space-y-2" role="alert"><ErrorBanner message="无法核对 /users/me，方法操作保持只读。" /><Button variant="secondary" onClick={() => void me.refetch()}>重试核对权限</Button></div> : !editable && <p className="rounded-lg bg-amber-50 p-3 text-sm text-amber-800">当前只读。可以查看历史，不记录使用、不创建、不修改方法。</p>}
    {!validContext && <ErrorBanner message="适用方法发现需要同时指定有效项目 ID 与单元 ID；未发送不完整范围请求。" />}
    {learningCandidate ? <><CaptureForm editable={editable} context={context} learningCandidate={learningCandidate} onCreated={choose} onDirtyChange={setLearningDirty} />{detail}</> : <>
      {inContext && <div className={box}><label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={optOut} onChange={event => setOptOut(event.target.checked)} />本任务不采用能力库方法或偏好</label><Field label="本任务人工覆盖说明（可选）" hint="仅保留当前页面说明；不会保存到正文或注入提示。"><textarea className={inputClass} value={override} onChange={event => setOverride(event.target.value)} maxLength={4000} /></Field><p className="text-xs text-slate-500">所有偏好和创作模式都需人工选择具体版本，再明确渲染；没有默认采用的方法。</p></div>}
      {!inContext && <nav className="flex flex-wrap gap-2" aria-label="方法状态">{(["candidate", "saved", "pinned", "archived"] as const).map(value => <Button key={value} variant={tab === value ? "primary" : "secondary"} ariaPressed={tab === value} onClick={() => { setTab(value); setOffset(0); }}>{statusLabels[value]}</Button>)}{tab === "archived" && <Field label="归档清单"><select className={inputClass} value={retired} onChange={event => { setRetired(event.target.value as "archived" | "deprecated"); setOffset(0); }}><option value="archived">已归档</option><option value="deprecated">已停用</option></select></Field>}</nav>}
      <form className="flex flex-wrap items-end gap-3" onSubmit={event => { event.preventDefault(); const form = new FormData(event.currentTarget); setFilters({ kind: String(form.get("kind") ?? ""), scope_type: String(form.get("scope_type") ?? ""), q: String(form.get("q") ?? ""), tag: String(form.get("tag") ?? "") }); setOffset(0); }}><Field label="类型"><select className={inputClass} name="kind"><option value="">所有类型（含偏好与模式）</option>{Object.entries(kindLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></Field><Field label="范围类型"><select className={inputClass} name="scope_type"><option value="">所有适用范围</option>{Object.entries(scopeLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></Field><Field label="名称 / 正文搜索"><input className={inputClass} name="q" maxLength={500} /></Field><Field label="标签"><input className={inputClass} name="tag" maxLength={100} /></Field><Button type="submit" variant="secondary">明确查询</Button></form>
      {query.isFetching && <Spinner label={inContext ? "读取所有适用方法…" : "读取方法库…"} />}{query.isError && <div className="space-y-2" role="alert"><ErrorBanner message={errorText(query.error)} /><Button variant="secondary" onClick={() => void query.refetch()}>重试读取</Button></div>}
      {query.data && <div className="space-y-3"><p className="text-xs text-slate-500">共 {query.data.total} 条 · 当前起点 {query.data.offset} · 每页 {query.data.limit} 条</p>{query.data.items.length ? query.data.items.map(artifact => <button type="button" key={artifact.id} className={`block w-full space-y-1 rounded-lg border p-3 text-left text-sm ${selected === artifact.id ? "border-indigo-400 bg-indigo-50" : "border-slate-200 bg-white"}`} onClick={() => choose(artifact.id)}><p className="font-medium">{artifact.name} · #{artifact.id} · {kindLabels[artifact.kind]} · {statusLabels[artifact.status]}</p><p>{scopeText(artifact.scope_type, artifact.scope)} · v{artifact.current_revision.revision_no} / revision #{artifact.current_revision.id}</p><p className="break-all text-xs text-slate-500">hash: {artifact.current_revision.content_hash}</p><p className="text-xs text-slate-500">来源：{artifact.source_kind} · 执行 {artifact.current_revision.source_execution_id ?? "无"} / 学习 {artifact.current_revision.source_learning_candidate_id ?? "无"} · 使用 {artifact.usage?.use_count ?? "未知"} 次 · 最近 {artifact.usage?.last_used ?? "未使用 / 未返回"}</p>{artifact.matched_scope && <p className="break-all text-xs text-slate-500">匹配：{JSON.stringify(artifact.matched_scope)}</p>}</button>) : <p className="text-sm text-slate-500">当前范围没有返回方法。</p>}<div className="flex gap-2"><Button variant="secondary" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - query.data!.limit))}>上一页</Button><Button variant="secondary" disabled={query.data.offset + query.data.limit >= query.data.total} onClick={() => setOffset(offset + query.data!.limit)}>下一页</Button><Button variant="secondary" onClick={() => void query.refetch()}>刷新清单</Button></div></div>}
      {detail}
      <div className="flex flex-wrap gap-2"><Button variant="secondary" disabled={!editable} onClick={() => toggle("create")}>{visible.create ? "收起新建表单" : "新建方法候选"}</Button><Button variant="secondary" disabled={!editable} onClick={() => toggle("capture")}>{visible.capture ? "收起捕获表单" : "从已接受执行保留方法"}</Button><Button variant="secondary" disabled={!editable} onClick={() => toggle("preference")}>{visible.preference ? "收起偏好候选表单" : "从重复保存编辑保留偏好"}</Button>{!inContext && <Button variant="secondary" disabled={!editable} onClick={() => toggle("import")}>{visible.import ? "收起导入表单" : "导入方法文件"}</Button>}</div>
      {opened.create && <div hidden={!visible.create}><CaptureForm editable={editable} context={context} onCreated={choose} onDirtyChange={setCreateDirty} /></div>}{opened.capture && <div hidden={!visible.capture}><CaptureForm editable={editable} context={context} execution onCreated={choose} onDirtyChange={setCaptureDirty} /></div>}{opened.import && <div hidden={!visible.import}><FileImport editable={editable} onCreated={choose} /></div>}
      {opened.preference && <div hidden={!visible.preference}><PreferenceCaptureForm editable={editable} context={context} onCreated={choose} onDirtyChange={setPreferenceDirty} /></div>}
      {!inContext && <InstalledSkills />}
    </>}
  </section>;
}
export default function CapabilityMemoryPanel(props: CapabilityMemoryPanelProps) {
  // A different owner/source/context must never inherit an unsent decision from this view.
  return <CapabilityWorkspace key={`${currentUser()}:${props.projectId ?? "library"}:${props.unitId ?? ""}:${props.executionId ?? ""}:${props.learningCandidate?.id ?? ""}`} {...props} />;
}
