import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from "react";
import { capabilityApi, type CapabilityArtifact } from "./capabilityMemoryTypes";
import { api, ApiError, currentUser } from "../api";
import { Button, inputClass } from "../components/ui";
import { displayValue, editedValue, isUnfilled, type AssistanceField, type AssistanceSurface, type AssistanceValue } from "./formAssistanceTypes";

type Item = { key: string; baseline: AssistanceValue; status: string; suggestion: AssistanceValue; note?: string; image_observation?: string; image_reference?: Record<string, unknown> };
type Pending = { requestKey: string; kind: "generate" | "feedback"; sessionId?: number };
type Session = { context: Record<string, unknown>; request_key: string; id: number; revision: number; context_hash: string; status: string; items: Item[]; attempts: { id: number; items: Item[]; model_receipt?: Record<string, unknown>; feedback?: unknown; project_snapshot?: { product_context?: { sku?: { sku_id: number } | null } } }[]; decisions?: unknown; feedback?: unknown };
type SourceRef = { source_id: number; checksum: string };
type MethodRef = { artifact_id: number; revision_id: number; content_hash: string };
type Props = { productionStages?: import("./ProductionStageControls").ProductionStages | null; versionKey?: string; surface: AssistanceSurface; assistantVisible?: boolean; onFieldFocus?: () => void; projectId?: number; unitId?: number; fields: AssistanceField[]; context?: Record<string, unknown>; sourceRefs?: SourceRef[]; methodRefs?: MethodRef[]; readOnly?: boolean; methodArea?: ReactNode; tools?: (focusKey: string) => ReactNode; children: ReactNode };
const AssistanceContext = createContext<{ focus: (key: string) => void; register: (scope: string, values: AssistanceField[]) => void; unregister: (scope: string) => void } | null>(null);
export function useAssistanceFields(scope: string, fields: AssistanceField[]) {
  const controller = useContext(AssistanceContext), latest = useRef(fields); latest.current = fields;
  const register = controller?.register, unregister = controller?.unregister;
  const signature = JSON.stringify(fields.map(({ key, value, label, kind, protected: guard }) => [key,value,label,kind,guard]));
  useEffect(() => { register?.(scope, latest.current.map(field => ({ ...field, apply: value => { const current = latest.current.find(row => row.key === field.key); if (!current) throw new Error("字段已变化"); current.apply(value); } }))); }, [scope, signature, register]);
  useEffect(() => () => unregister?.(scope), [scope, unregister]);
}
export function useAssistanceFocus() { return useContext(AssistanceContext)?.focus; }
const same = (a: unknown, b: unknown) => JSON.stringify(a) === JSON.stringify(b);

export default function FormAssistancePanel({ productionStages, versionKey = "", surface, projectId, unitId, fields: baseFields, context = {}, sourceRefs = [], methodRefs = [], readOnly = false, assistantVisible = true, onFieldFocus, methodArea, tools, children }: Props) {
  const [extra, setExtra] = useState<Record<string, AssistanceField[]>>({});
  const register = useCallback((scope: string, values: AssistanceField[]) => setExtra(previous => ({ ...previous, [scope]: values })), []);
  const unregister = useCallback((scope: string) => setExtra(previous => Object.fromEntries(Object.entries(previous).filter(([key]) => key !== scope))), []);
  const fields = [...baseFields, ...Object.values(extra).flat()];
  const [actor] = useState(currentUser);
  const [open, setOpen] = useState(false);
  const [focusKey, setFocusKey] = useState("");
  const selection = useRef<{ field_key: string; start: number; end: number; text: string } | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [index, setIndex] = useState(0);
  const [candidate, setCandidate] = useState("");
  const [reason, setReason] = useState("");
  const [correction, setCorrection] = useState("presentation_style");
  const [reuse, setReuse] = useState(false);
  const [rule, setRule] = useState("");
  const [reuseKind, setReuseKind] = useState("project");
  const [reuseStage, setReuseStage] = useState("");
  const [skipKeys, setSkipKeys] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [issue, setIssue] = useState("");
  const [notice, setNotice] = useState("");
  const [sessions, setSessions] = useState<Session[]>([]);
  const [chosen, setChosen] = useState("");
  const [preferences, setPreferences] = useState<CapabilityArtifact[]>([]);
  const [selectedPreferences, setSelectedPreferences] = useState<number[]>([]);
  const pendingStorageKey = `form-assistance.pending:${actor}:${surface}:${projectId || "new"}:${unitId || "none"}`;
  const [pending, setPending] = useState<Pending | null>(() => { try { return JSON.parse(sessionStorage.getItem(pendingStorageKey) || "null"); } catch { return null; } });
  useEffect(() => { try { if (pending) sessionStorage.setItem(pendingStorageKey,JSON.stringify(pending)); else sessionStorage.removeItem(pendingStorageKey); } catch { setIssue("请求恢复标识无法持久保存，请先保持页面打开并核对原批次。"); } }, [pending, pendingStorageKey]);
  const alive = useRef(true), locked = useRef(false), latest = useRef(fields);
  latest.current = fields;
  const generationVersion = useRef(versionKey), currentVersion = useRef(versionKey); currentVersion.current = versionKey;
  const generationBase = useRef<Record<string, unknown> | null>(null);
  const acceptedValues = useRef<Record<string, unknown>>({});
  const identity = `${actor}:${surface}:${projectId || "new"}:${unitId || "none"}`;
  const identityRef = useRef(identity); identityRef.current = identity;
  const focused = fields.find(field => field.key === focusKey);
  const item = session?.items[index];
  const currentSkuId = session?.attempts[session.attempts.length - 1]?.project_snapshot?.product_context?.sku?.sku_id;
  const target = fields.find(field => field.key === item?.key);
  const actorSafe = alive.current && currentUser() === actor;
  const disabled = busy || readOnly || !actorSafe || !assistantVisible;
  const snapshot = () => ({ ...context, ...Object.fromEntries(latest.current.map(field => [field.key, field.value])) });
  const latestSnapshot = useRef(snapshot()); latestSnapshot.current = snapshot();
  const chosenMethods = [...methodRefs, ...preferences.filter(row => selectedPreferences.includes(row.current_revision.id)).map(row => ({ artifact_id: row.id, revision_id: row.current_revision.id, content_hash: row.current_revision.content_hash }))];
  const methodIdentity = JSON.stringify([chosenMethods,productionStages,sourceRefs]);
  const currentMethods = useRef(methodIdentity), generationMethods = useRef(methodIdentity); currentMethods.current = methodIdentity;
  const available = fields.filter(field => !field.protected && !field.unavailable && isUnfilled(field.value) && !skipKeys.includes(field.key));
  useEffect(() => { alive.current = true; return () => { alive.current = false; }; }, []);
  useEffect(() => {
    setSession(null); setIndex(0); generationBase.current = null; acceptedValues.current = {}; setSessions([]); setFocusKey(""); selection.current = null;
    let active = true;
    setSelectedPreferences([]);
    void capabilityApi.list("kind=preference&status=saved&limit=100&offset=0").then(value => {
      if (!active || currentUser() !== actor) return;
      setPreferences(value.items.filter(row => row.scope_type === "owner" || (row.scope_type === "project" && row.scope.id === projectId)));
    }).catch(() => { if (active) setIssue("偏好列表暂未读取，仍可不选偏好生成。"); });
    const query = new URLSearchParams({ surface, ...(projectId ? { project_id: String(projectId) } : {}), ...(unitId ? { unit_id: String(unitId) } : {}) });
    void api.get<{ items: Session[] } | Session[]>(`/form-assistance?${query}`).then(value => {
      if (active && currentUser() === actor) setSessions(Array.isArray(value) ? value : value.items);
    }).catch(() => { if (active) setIssue("历史建议暂未读取，可重新打开面板后重试。"); });
    return () => { active = false; };
  }, [identity]);
  useEffect(() => { setCandidate(item && item.status === "suggested" ? displayValue(item.suggestion) : ""); }, [session?.id, session?.revision, index]);
  function focus(key: string) { if (fields.some(field => field.key === key)) { setFocusKey(key); onFieldFocus?.(); } }
  async function run(action: () => Promise<void>) {
    if (disabled || locked.current) return;
    locked.current = true; setBusy(true); setIssue(""); setNotice("");
    try { await action(); } catch (error) { if (alive.current) { if (error instanceof ApiError && [400,401,403,404,409,422].includes(error.status)) setPending(null); setIssue(error instanceof Error ? error.message : "操作未完成，请核对原请求"); } }
    finally { locked.current = false; if (alive.current) setBusy(false); }
  }
  function contextMatches() {
    if (!generationBase.current || generationVersion.current !== currentVersion.current || generationMethods.current !== currentMethods.current) return false;
    const expected = { ...generationBase.current, ...acceptedValues.current };
    return same(expected, latestSnapshot.current);
  }
  function receive(value: Session, base: Record<string, unknown>, requestIdentity: string) {
    if (!alive.current || currentUser() !== actor || identityRef.current !== requestIdentity) return;
    setSession(value); setIndex(0); generationBase.current = base; generationVersion.current = currentVersion.current; generationMethods.current = currentMethods.current; acceptedValues.current = {}; setPending(null);
    setSessions(previous => [value, ...previous.filter(row => row.id !== value.id)]);
  }
  async function generate(mode: "autofill" | "polish") {
    setOpen(true);
    const targets = mode === "autofill" ? available.map(field => field.key) : focused && !focused.unavailable ? [focused.key] : [];
    if (!targets.length) { setIssue(mode === "autofill" ? "当前没有可补齐的空白内容。已填项可聚焦后单独润色。" : focused?.unavailable || "先聚焦要处理的内容字段。"); return; }
    await run(async () => {
      const requestIdentity = identity, base = snapshot(), requestKey = crypto.randomUUID();
      const sentVersion = currentVersion.current, sentMethods = currentMethods.current;
      setPending({ requestKey, kind: "generate" });
      const result = await api.post<Session>("/form-assistance", { request_key: requestKey, surface, mode, project_id: projectId, unit_id: unitId, context: base, targets, skipped_keys: skipKeys, source_refs: sourceRefs, method_refs: chosenMethods, production_stages: productionStages, ...(mode === "polish" && selection.current?.field_key === focusKey ? { selection: selection.current } : {}) });
      receive(result, base, requestIdentity); generationVersion.current = sentVersion; generationMethods.current = sentMethods;
    });
  }
  async function decide(action: "adopt" | "edit" | "skip") {
    if (!session || !item || !target) return;
    await run(async () => {
      if (!contextMatches() || !same(target.value, item.baseline)) throw new Error("字段或相关上下文已变化，请重新生成，当前文字已保留。");
      if (action !== "skip" && item.status !== "suggested") throw new Error("这一项还需要资料或能力配置，不能当成有效建议采用。");
      const value = action === "skip" ? null : editedValue(candidate, target);
      const requestIdentity = identity;
      const result = await api.post<Session>(`/form-assistance/${session.id}/decisions`, { expected_revision: session.revision, context_hash: session.context_hash, decisions: [{ key: item.key, action, value, baseline: item.baseline }] });
      if (!alive.current || currentUser() !== actor || identityRef.current !== requestIdentity) return;
      if (!contextMatches()) { setSession(result); throw new Error("记录期间内容已变化，未写回草稿；请重新生成。"); }
      if (action !== "skip") {
        const current = latest.current.find(field => field.key === item.key);
        if (!current || !same(current.value, item.baseline)) throw new Error("原字段已变化，未写回草稿。");
        current.apply(value); acceptedValues.current[item.key] = value; setFocusKey(item.key);
      } else setSkipKeys(previous => [...new Set([...previous, item.key])]);
      setSession(result); setIndex(value => Math.min(value + 1, result.items.length - 1));
      setNotice(action === "skip" ? "已跳过本项。" : "已采用到页面草稿；如需继续润色，可点上方“润色当前项”。请使用原页面保存按钮保存。");
    });
  }
  async function feedback(batch: boolean) {
    if (!session || !reason.trim()) { setIssue("写一下这次希望如何修改。"); return; }
    await run(async () => {
      if (!contextMatches()) throw new Error("上下文已变化，请保留反馈文字并重新生成。");
      const keys = batch ? session.items.filter(row => { const field = latest.current.find(f => f.key === row.key); return field && !field.protected && isUnfilled(field.value) && !skipKeys.includes(row.key); }).map(row => row.key) : item ? [item.key] : [];
      if (!keys.length) throw new Error("没有仍待确认的空白项；已填内容可定点润色。");
      if (reuse && !rule.trim()) throw new Error("请写清以后要复用的规则。");
      const base = snapshot(), requestIdentity = identity, requestKey = crypto.randomUUID(), sentVersion = currentVersion.current, sentMethods = currentMethods.current;
      if (reuse && reuseKind === "sku" && !currentSkuId) throw new Error("当前作品尚未关联SKU，不能保存本SKU偏好。");
      if (reuse && reuseKind === "category" && !base.category) throw new Error("请先确认商品品类再保存此范围的偏好。");
      if (reuse && reuseKind === "style" && !base.style_revision_id) throw new Error("请先选定表现风格，再保存此风格的偏好。");
      setPending({ requestKey, kind: "feedback", sessionId: session.id });
      const result = await api.post<Session>(`/form-assistance/${session.id}/feedback`, { expected_revision: session.revision, request_key: requestKey, context: base, keys, reason, correction_target: correction, ...(reuse ? { reuse: { rule, name: rule.slice(0, 60), scope_type: projectId && reuseKind === "project" ? "project" : "owner", ...(reuseKind === "sku" ? { sku_id: currentSkuId } : {}), ...(reuseKind === "category" ? { category: base.category } : {}), ...(reuseKind === "style" ? { style_revision_id: base.style_revision_id } : {}), ...(reuseStage ? { stage: reuseStage } : {}) } } : {}) });
      receive(result, base, requestIdentity); generationVersion.current = sentVersion; generationMethods.current = sentMethods; setNotice(reuse ? "反馈已记录；复用规则仅保存为候选，请在方法库明确选择版本后使用。" : "已按本次反馈生成新建议，旧版本保留。");
    });
  }
  async function restore(id: number) {
    if (pending) { setIssue("先核对原请求终态，再切换历史建议。"); return; }
    await run(async () => {
      const requestIdentity = identity; const value = await api.get<Session>(`/form-assistance/${id}`);
      receive(value, value.context, requestIdentity);
      // Historical content cannot authenticate the current unsaved references or selected methods.
      generationBase.current = null;
      setNotice("已恢复历史结果供对照。当前来源、方法或未保存引用可能不同，请重新生成后再采用；历史采用记录不表示草稿已保存。");
    });
  }
  return <AssistanceContext.Provider value={{ focus, register, unregister }}><div onFocusCapture={event => {
    const input = event.target as HTMLInputElement | HTMLTextAreaElement;
    const key = input.dataset.aiField || input.closest<HTMLElement>("[data-ai-field]")?.dataset.aiField;
    if (!key) return;
    focus(key); selection.current = null;
  }} onSelectCapture={event => {
    const input = event.target as HTMLInputElement | HTMLTextAreaElement;
    const key = input.dataset.aiField || input.closest<HTMLElement>("[data-ai-field]")?.dataset.aiField;
    if (!key) return;
    if (typeof input.value !== "string" || input.selectionStart === null || input.selectionEnd === null || input.selectionStart === input.selectionEnd) { selection.current = null; return; }
    selection.current = { field_key: key, start: input.selectionStart, end: input.selectionEnd, text: input.value.slice(input.selectionStart, input.selectionEnd) };
  }}>{children}</div>
    {/* Collapsed, the assistant is a single pill so it never covers the form it helps with. */}
    {!open && assistantVisible && <button type="button" onClick={() => setOpen(true)} aria-label="展开 AI创作助手" className="fixed bottom-5 right-5 z-[70] inline-flex items-center gap-2 rounded-pill border border-ink-200 bg-surface/95 py-2 pl-3 pr-4 text-[13px] text-ink-800 shadow-lift backdrop-blur transition-transform hover:-translate-y-0.5"><span aria-hidden className="grid h-6 w-6 place-items-center rounded-full bg-accent-500 text-[12px] text-paper">✦</span>AI 创作助手{available.length > 0 && <span className="rounded-pill bg-ink-100 px-1.5 text-[11.5px] text-ink-600">{available.length} 项可补</span>}{pending && <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-amber-500" />}</button>}
    <aside hidden={!assistantVisible || !open} aria-label="AI创作助手" className="fixed bottom-5 right-5 z-[70] max-h-[80vh] w-[min(28rem,calc(100vw-2rem))] animate-rise overflow-auto rounded-card border border-ink-200 bg-surface p-5 shadow-lift">
      <div className="flex items-center justify-between gap-3"><strong className="flex items-center gap-2 text-[14px] text-ink-900"><span aria-hidden className="grid h-6 w-6 place-items-center rounded-full bg-accent-500 text-[12px] font-normal text-paper">✦</span>AI 创作助手</strong><Button size="sm" variant="ghost" onClick={() => setOpen(false)}>收起</Button></div>
      {tools && <div className="mt-4 border-b border-ink-200/80 pb-4">{tools(focusKey)}</div>}
      <p className="my-3 text-[12.5px] text-ink-600">当前字段：{focused?.label || "尚未选择"}{focused?.unavailable && ` · ${focused.unavailable}`}</p>
      <div className="flex flex-wrap gap-2"><Button size="sm" disabled={disabled || !!pending} onClick={() => void generate("autofill")}>补齐未填项（{available.length}）</Button><Button size="sm" variant="secondary" disabled={disabled || !!pending || !focused || !!focused.unavailable} onClick={() => void generate("polish")}>{focused && isUnfilled(focused.value) ? "生成当前项" : "润色当前项"}</Button></div>
      {<div className="mt-3 space-y-3 text-sm"><p className="text-xs text-slate-500">已填内容与创作意图不会被批量改写。待补字段：{available.map(field => field.label).join("、") || "无"}。建议采用后仍需保存原页面。</p>
        {methodArea}
        <p className="text-xs"><a className="text-indigo-700 underline" href="/settings?section=models">配置补齐／润色模型</a></p>
        {preferences.length > 0 && <details><summary className="cursor-pointer text-xs">本次明确选用的偏好版本（可不选）</summary><div className="space-y-2 py-2">{preferences.map(row => <label key={row.id} className="flex gap-2 text-xs"><input type="checkbox" checked={selectedPreferences.includes(row.current_revision.id)} onChange={event => setSelectedPreferences(previous => event.target.checked ? [...previous,row.current_revision.id] : previous.filter(id=>id!==row.current_revision.id))} /><span>{row.name} · v{row.current_revision.revision_no}<span className="block text-slate-500">{String(row.current_revision.content.text || "")}</span></span></label>)}</div></details>}
        {sessions.length > 0 && <label className="block text-xs">历史建议<select className={inputClass} value={chosen} disabled={disabled || !!pending} onChange={event => { setChosen(event.target.value); if (event.target.value) void restore(Number(event.target.value)); }}><option value="">选择历史批次</option>{sessions.map(row => <option key={row.id} value={row.id}>批次 #{row.id} · {row.status}</option>)}</select></label>}
        {pending && <div role="status" className="rounded bg-amber-50 p-2 text-xs">请求 {pending.requestKey.slice(0, 8)} 正在处理或结果待核对，请勿重复生成。<Button size="sm" variant="secondary" disabled={busy} onClick={() => void run(async () => { const query = new URLSearchParams({ surface, ...(projectId ? { project_id: String(projectId) } : {}), ...(unitId ? { unit_id: String(unitId) } : {}) }); const value = await api.get<{ items: Session[] } | Session[]>(`/form-assistance?${query}`); const rows = Array.isArray(value) ? value : value.items; setSessions(rows); const original = pending.sessionId ? await api.get<Session>(`/form-assistance/${pending.sessionId}`) : rows.find(row=>row.request_key===pending.requestKey); if (!original) { setNotice("尚未找到原请求回执，结果仍待核对，请勿重新生成。"); return; } if (original.status === "running") { setNotice("原批次仍在运行，请稍后读取，不能重复发起。"); return; } setPending(null); setSession(original); setIndex(0); generationBase.current=null; acceptedValues.current={}; setNotice("已找到原批次终态；历史建议可查看，采用前需核对当前草稿。"); })}>读取原批次</Button></div>}
        {session && <><p className="text-xs">批次 #{session.id} · {session.status} · 第 {index + 1}/{session.items.length} 项</p>
          {item && <div className="space-y-2 rounded-lg bg-indigo-50 p-3"><strong>{target?.label || item.key}</strong><p className="whitespace-pre-wrap text-xs">原值：{displayValue(item.baseline) || "空白"}</p><p className="text-xs">{item.note || item.status}</p>{item.image_observation && <p className="text-xs whitespace-pre-wrap">看图观察：{item.image_observation}</p>}{item.image_reference && <p className="break-all text-xs">图片依据：{JSON.stringify(item.image_reference)}</p>}<textarea aria-label="AI建议可修改内容" className={inputClass} rows={5} disabled={disabled || item.status !== "suggested"} value={candidate} onChange={event => setCandidate(event.target.value)} />
            <div className="flex flex-wrap gap-2"><Button size="sm" disabled={disabled || item.status !== "suggested" || !target || !contextMatches()} onClick={() => void decide(same(candidate, displayValue(item.suggestion)) ? "adopt" : "edit")}>采用到草稿并下一项</Button><Button size="sm" variant="secondary" disabled={disabled || !target || !contextMatches()} onClick={() => void decide("skip")}>跳过</Button></div>
            <div className="flex gap-2"><Button size="sm" variant="ghost" disabled={index === 0} onClick={() => setIndex(value => value - 1)}>上一项</Button><Button size="sm" variant="ghost" disabled={index >= session.items.length - 1} onClick={() => setIndex(value => value + 1)}>下一项</Button></div>
          </div>}
          <label className="block text-xs">这次希望如何改<textarea className={inputClass} maxLength={2000} rows={2} value={reason} onChange={event => setReason(event.target.value)} placeholder="例如：太空泛，请围绕具体场景讲清一个购买理由" /></label>
          <select aria-label="反馈改动类型" className={inputClass} value={correction} onChange={event => setCorrection(event.target.value)}><option value="product_fact">商品资料/事实</option><option value="category_method">品类展示方法</option><option value="presentation_style">表现风格</option><option value="stage_method">阶段技巧</option></select>
          <label className="flex gap-2 text-xs"><input type="checkbox" checked={reuse} onChange={event => setReuse(event.target.checked)} />以后也这样：保存一条偏好候选</label>
          {reuse && <div className="space-y-2"><textarea aria-label="长期复用规则" maxLength={2000} className={inputClass} value={rule} onChange={event => setRule(event.target.value)} placeholder="明确规则，不填写商品参数或私人费用" /><select aria-label="反馈适用范围" className={inputClass} value={reuseKind} onChange={event => setReuseKind(event.target.value)}><option value="project">{projectId ? "当前商品项目" : "我的方法库候选（需明确选择才使用）"}</option>{currentSkuId && <option value="sku">本SKU的作品</option>}<option value="category">此品类的作品</option><option value="style">所选表现风格</option><option value="general">商品通用方法候选</option></select><select aria-label="复用阶段" className={inputClass} value={reuseStage} onChange={event=>setReuseStage(event.target.value)}><option value="">不限阶段</option><option value="research">商品资料与依据</option><option value="script">文案与脚本</option><option value="storyboard">分镜与素材</option><option value="subtitle_color">字幕与校色</option><option value="packaging">后期包装</option><option value="review">质量评审</option></select><p className="text-xs">本SKU、品类和风格范围会保存到我的方法库，后续作品需明确选用已保存的版本；候选不会自动更改任何默认设置。</p></div>}
          <div className="flex gap-2"><Button size="sm" disabled={disabled || !!pending || !reason.trim()} onClick={() => void feedback(false)}>反馈并重写本项</Button><Button size="sm" variant="secondary" disabled={disabled || !!pending || !reason.trim()} onClick={() => void feedback(true)}>本批待确认项重写</Button></div>
          <details><summary className="cursor-pointer text-xs">查看历史结果和模型版本</summary>{session.attempts.map((attempt, n) => <div key={attempt.id || n} className="my-2 rounded border p-2 text-xs"><p>版本 {n + 1} · {JSON.stringify(attempt.model_receipt || {})}</p>{attempt.items.map(row => <p key={row.key} className="whitespace-pre-wrap">{row.key}：{displayValue(row.suggestion)} · {row.note}</p>)}{!!attempt.feedback && <p>{JSON.stringify(attempt.feedback)}</p>}</div>)}</details>
        </>}
      </div>}
      {notice && <p role="status" className="mt-2 text-xs text-emerald-800">{notice}</p>}{issue && <p role="alert" className="mt-2 text-xs text-rose-700">{issue}</p>}
    </aside>
  </AssistanceContext.Provider>;
}
