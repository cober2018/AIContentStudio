import { lazy, Suspense, useEffect, useState } from "react";
import { api, ApiError } from "../api";
import { Button, ErrorBanner, Field, Spinner, inputClass } from "../components/ui";
import StageContractControls from "./StageContractControls";
import { stageValue, type StageContract, type StageDestination, type StageDiff, type StageMethod, type StageMethods } from "./creationRecipeState";
import type { StageHistory } from "./StageHistoryPanel";
import type { StageResult } from "./stageProposalState";
import type { StageTuningPatch } from "./StageTuningPanel";

const StageTuningPanel = lazy(() => import("./StageTuningPanel"));

type Destination = { key: StageDestination; scope_id?: number };
type DefinitionDiff = { replaces_entire_default: boolean; previous_workflow_id: number | null; previous_checksum: string | null;
  nodes: { node_id: string; change: "added" | "removed" | "modified"; fields: StageDiff[] }[];
  edges: { before: unknown[]; after: unknown[] }; visual_order: { before: string[]; after: string[] } };
type ImprovementRequest = { run_id: number; attempt_id: number; feedback_event_id: number; destination: StageDestination; scope_id?: number } & Partial<StageTuningPatch>;
type ImprovementPreview = { run_id?: number; attempt_id?: number; node_id?: string; destination?: StageDestination;
  method_scope?: { scope_type: string; scope: { id: number } };
  config_patch: Record<string, unknown>; diff: StageDiff[]; has_config_change: boolean; content_only: boolean;
  patch_source?: "accepted_override" | "content_feedback_only" | "user_authored" | "model_suggestion"; executed_patch?: boolean;
  expected_revision: number; preview_hash: string; destinations: Destination[]; feedback_event_id?: number; definition_diff?: DefinitionDiff | null };
type MethodRequest = { artifact_id: number; revision_id: number; destination: StageDestination; scope_id?: number };
type MethodPreview = { artifact_id: number; revision_id: number; diff: StageDiff[]; preview_hash: string; expected_revision: number; destination: StageDestination; definition_diff?: DefinitionDiff | null };
type Pending = { endpoint: "save-adjustment" | "apply-method"; body: Record<string, unknown> };
const destinationNames: Record<StageDestination, string> = { project: "当前项目", persona: "当前角色默认", account: "当前账号默认", series: "当前系列默认", capability: "可复用方法候选" };
const impacts: Record<StageDestination, string> = { project: "创建本单元的新项目流程版本；旧运行仍固定原流程。", persona: "将当前项目的完整流程作为此角色的新默认模板，不是只改这一个阶段。已有单元与运行不自动重绑。", account: "将当前项目的完整流程作为此账号的新默认模板，不是只改这一个阶段。已有单元与运行不自动重绑。", series: "将当前项目的完整流程作为此系列的新默认模板，不是只改这一个阶段。已有单元与运行不自动重绑。", capability: "仅保存为方法候选；之后仍需明确保存、固定版本和应用。" };
const definitionLabels: Record<string, string> = { nodes: "阶段", added: "新增", removed: "删除", modified: "修改", change: "变更方式", changes: "精确变化", fields: "精确字段变化", field: "字段", visual_order: "阶段显示顺序", edges: "依赖连线", before: "原默认模板", after: "拟保存模板", node_id: "阶段标识", from: "来源", to: "目标", previous_workflow_id: "原默认流程", previous_checksum: "原默认模板摘要", replaces_entire_default: "替换完整默认模板" };

function DefinitionChanges({ value }: { value: unknown }) {
  if (Array.isArray(value)) return value.length ? <ol className="list-decimal space-y-2 pl-5">{value.map((item, index) => <li key={index}><DefinitionChanges value={item} /></li>)}</ol> : <p>无变化 / 空列表</p>;
  if (value && typeof value === "object") return <dl className="space-y-2">{Object.entries(value).map(([key, item]) => <div key={key} className="border-l border-indigo-200 pl-3"><dt className="font-medium">{definitionLabels[key] || key}</dt><dd className="mt-1"><DefinitionChanges value={item} /></dd></div>)}</dl>;
  return <p className="whitespace-pre-wrap break-words">{value === null ? "无" : stageValue(value)}</p>;
}

function DiffTable({ diff, contract }: { diff: StageDiff[]; contract: StageContract }) {
  return <div className="overflow-x-auto"><table className="mt-3 w-full text-left text-xs"><thead><tr><th className="p-2">参数</th><th>原配置</th><th>将保存</th></tr></thead><tbody>{diff.map((item, index) => <tr key={`${item.field}:${index}`} className="border-t"><td className="p-2">{contract.ui_schema?.[item.field || ""]?.label || item.field}</td><td className="max-w-sm whitespace-pre-wrap break-words p-2">{stageValue(item.before)}</td><td className="max-w-sm whitespace-pre-wrap break-words p-2">{stageValue(item.after)}</td></tr>)}</tbody></table></div>;
}

export default function StageLearningPanel({ base, nodeId, result, contract, readOnly, onBusy, onSaved }: {
  base: string; nodeId: string; result: StageResult | null; contract: StageContract; readOnly: boolean;
  onBusy: (busy: boolean) => void; onSaved: () => Promise<void>;
}) {
  const stageBase = `${base}/creation-recipe/stages/${encodeURIComponent(nodeId)}`;
  const [methods, setMethods] = useState<StageMethod[]>([]);
  const [feedbackId, setFeedbackId] = useState<number | null>(result?.feedback_event_id || result?.accepted_target?.feedback_event_id || null);
  const [destination, setDestination] = useState<StageDestination>("project");
  const [destinations, setDestinations] = useState<Destination[]>([{ key: "project" }, { key: "capability" }]);
  const [preview, setPreview] = useState<ImprovementPreview | null>(null);
  const [methodPreview, setMethodPreview] = useState<MethodPreview | null>(null);
  const [methodId, setMethodId] = useState("");
  const [name, setName] = useState("有效阶段调整");
  const [methodKind, setMethodKind] = useState<"recipe" | "prompt_skill">("recipe");
  const [confirmed, setConfirmed] = useState(false);
  const [pending, setPending] = useState<Pending | null>(null);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [refresh, setRefresh] = useState(0);
  const [tuningOpen, setTuningOpen] = useState(false);
  const [tuning, setTuning] = useState<StageTuningPatch | null>(null);
  const [tuningBusy, setTuningBusy] = useState(false);
  const [authoring, setAuthoring] = useState(false);
  const [authoredPatch, setAuthoredPatch] = useState<Record<string, unknown>>({});

  useEffect(() => {
    if (pending) return;
    setPreview(null); setMethodPreview(null); setConfirmed(false);
    setTuning(null); setTuningOpen(false); setAuthoring(false); setAuthoredPatch({});
  }, [base, nodeId, result?.run_id, result?.attempt_id, result?.feedback_event_id, result?.accepted_target?.feedback_event_id]);

  useEffect(() => {
    let alive = true;
    setLoading(true); setError("");
    const acceptedId = result?.feedback_event_id || result?.accepted_target?.feedback_event_id;
    setFeedbackId(acceptedId || null);
    const reads = [api.get<StageMethods>(`${base}/creation-recipe/methods`).then(value => {
      if (alive) setMethods(value.methods.filter(item => item.kind === "recipe" && item.selection?.source_kind === "capability_memory"));
    })];
    if (result && !acceptedId) reads.push(api.get<StageHistory>(`${stageBase}/history?run_id=${result.run_id}`).then(history => {
      const attempt = history.items.find(item => item.attempt_id === result.attempt_id);
      const feedback = attempt?.feedback.slice().reverse().find(event => ["accepted", "accepted_with_edits"].includes(event.decision || event.payload?.decision || ""));
      if (alive) setFeedbackId(feedback?.id || null);
    }));
    Promise.allSettled(reads).then(outcomes => { if (alive) { if (outcomes.some(item => item.status === "rejected")) setError("方法或接受反馈暂不可读，请刷新来源。"); setLoading(false); } });
    return () => { alive = false; };
  }, [base, stageBase, result?.run_id, result?.attempt_id, result?.feedback_event_id, result?.accepted_target?.feedback_event_id, refresh]);

  const target = destinations.find(item => item.key === destination);
  const scope = target?.scope_id === undefined ? {} : { scope_id: target.scope_id };
  const improvementRequest: ImprovementRequest | null = result && feedbackId ? { run_id: result.run_id, attempt_id: result.attempt_id, feedback_event_id: feedbackId, destination, ...scope, ...(authoring ? { config_patch: authoredPatch } : tuning) } : null;
  const chosen = methods.find(item => item.selection.source_kind === "capability_memory" && `${item.selection.artifact_id}:${item.selection.revision_id}` === methodId);
  const methodRequest: MethodRequest | null = chosen?.selection.source_kind === "capability_memory" && destination !== "capability" ? { artifact_id: chosen.selection.artifact_id, revision_id: chosen.selection.revision_id, destination, ...scope } : null;
  const locked = readOnly || busy || Boolean(pending) || tuningBusy;
  const authoredFields = (contract.tunable_fields || []).filter(field => ["instruction", "method"].includes(field));
  const allowedPatch = preview && Object.keys(preview.config_patch).every(field => contract.tunable_fields?.includes(field));
  const defaultDestination = ["persona", "account", "series"].includes(destination);
  const definitionDiff = (preview || methodPreview)?.definition_diff;
  const fullDiffAvailable = !defaultDestination || Boolean(definitionDiff?.replaces_entire_default
    && Array.isArray(definitionDiff.nodes) && Array.isArray(definitionDiff.edges?.before) && Array.isArray(definitionDiff.edges?.after)
    && Array.isArray(definitionDiff.visual_order?.before) && Array.isArray(definitionDiff.visual_order?.after));

  function invalidate() { setPreview(null); setMethodPreview(null); setConfirmed(false); setNotice(""); }
  async function inspect(kind: "adjustment" | "method") {
    const request = kind === "adjustment" ? improvementRequest : methodRequest;
    if (!request || busy || pending || tuningBusy) return;
    setBusy(true); setError(""); setConfirmed(false);
    try {
      if (kind === "adjustment") {
        const value = await api.post<ImprovementPreview>(`${stageBase}/improvement-preview`, request);
        if (value.attempt_id !== undefined && value.attempt_id !== result?.attempt_id || value.run_id !== undefined && value.run_id !== result?.run_id
            || value.destination !== undefined && value.destination !== destination
            || !/^[a-f0-9]{64}$/.test(value.preview_hash) || !Array.isArray(value.diff)) throw new Error("调整来源无法核对。");
        setPreview(value); setMethodPreview(null); setDestinations(value.destinations);
      } else {
        const value = await api.post<MethodPreview>(`${stageBase}/apply-method-preview`, request);
        if (!methodRequest || value.artifact_id !== methodRequest.artifact_id || value.revision_id !== methodRequest.revision_id || value.destination !== destination || !/^[a-f0-9]{64}$/.test(value.preview_hash)) throw new Error("方法版本无法核对。");
        setMethodPreview(value); setPreview(null);
      }
    } catch (cause) { invalidate(); setError(cause instanceof ApiError ? `${cause.status} · ${cause.message}。请核对来源、范围与当前流程版本。` : "差异预览不可用，请刷新来源后重试。"); }
    finally { setBusy(false); }
  }

  async function save() {
    if (readOnly || busy || tuningBusy || !pending && !confirmed) return;
    const snapshot = preview || methodPreview;
    const source = preview ? improvementRequest : methodRequest;
    if (!pending && (!snapshot || !source || !name.trim() || !fullDiffAvailable || preview && (!allowedPatch || !preview.has_config_change))) return;
    const request = pending || { endpoint: preview ? "save-adjustment" : "apply-method", body: {
      ...source, expected_preview_hash: snapshot!.preview_hash, expected_revision: snapshot!.expected_revision,
      idempotency_key: `save:${crypto.randomUUID()}`, name: name.trim(),
      ...(preview && destination === "capability" ? { method_kind: methodKind } : {}),
    } } as Pending;
    setPending(request); setBusy(true); onBusy(true); setError("");
    let uncertain = false;
    try {
      const value = await api.post<{ workflow_id?: number; revision?: number; status?: string; artifact?: { id: number } }>(`${stageBase}/${request.endpoint}`, request.body);
      setPending(null); setPreview(null); setMethodPreview(null); setConfirmed(false);
      setNotice(value.status === "candidate" ? `已保存为方法候选 #${value.artifact?.id || ""}，需在方法库明确保存后才能复用。` : `已创建流程 #${value.workflow_id} · 新版本 ${value.revision}。原运行仍保留原版本。`);
      try { await onSaved(); } catch { setError("保存已提交，最新流程回读暂时失败。请刷新流程后继续。"); }
    } catch (cause) {
      uncertain = !(cause instanceof ApiError && cause.status < 500);
      if (!uncertain) { setPending(null); invalidate(); }
      setError(uncertain ? "保存结果尚未确认。保留原预览、目标版本和请求；重试只回放这次保存。" : "来源或目标版本已变化，请重新预览差异再确认。");
    } finally { setBusy(false); onBusy(uncertain); }
  }

  return <section className="mt-4 rounded-xl border border-indigo-100 bg-white p-4" aria-label="保存有效调整与复用方法"><div className="flex items-center justify-between gap-2"><h3 className="font-semibold">保存有效调整 / 复用方法</h3><Button variant="secondary" size="sm" disabled={locked || loading} onClick={() => { invalidate(); setRefresh(value => value + 1); }}>刷新来源</Button></div>{loading && <Spinner label="读取接受反馈与方法…" />}
    <div className="mt-3 grid gap-3 sm:grid-cols-2"><Field label="保存或应用到"><select className={inputClass} disabled={locked} value={destination} onChange={event => { setDestination(event.target.value as StageDestination); invalidate(); }}>{destinations.map(item => <option key={item.key} value={item.key}>{destinationNames[item.key]}{item.scope_id ? ` #${item.scope_id}` : ""}</option>)}</select></Field><Field label="新版本 / 方法名称"><input className={inputClass} maxLength={200} value={name} disabled={locked} onChange={event => { setName(event.target.value); setConfirmed(false); }} /></Field></div><p className="mt-2 text-xs text-slate-600">{impacts[destination]}</p>
    <div className="mt-4 space-y-2"><p className="text-sm font-medium">保存这次调节</p><p className="text-xs text-slate-500">已执行的参数差异可以明确保存。正文修改只作为反馈证据，不会被自动推断为指令或方法。</p><Button variant="secondary" size="sm" disabled={locked || !improvementRequest || authoring && !Object.keys(authoredPatch).length} onClick={() => inspect("adjustment")}>{authoring ? "预览人工调整的差异" : "预览这次调节的差异"}</Button>{!feedbackId && !loading && <p className="text-xs text-slate-500">先明确接受一个结果，才能选择其接受反馈保存调整。</p>}{destination === "capability" && <Field label="方法类型"><select className={inputClass} value={methodKind} disabled={locked} onChange={event => { setMethodKind(event.target.value as "recipe" | "prompt_skill"); setConfirmed(false); }}><option value="recipe">阶段参数方法候选</option><option value="prompt_skill">提示词方法候选（需要指令差异）</option></select></Field>}</div>
    {(authoring || preview?.content_only && !tuning) && authoredFields.length > 0 && <div className="mt-3 space-y-2 rounded-lg border border-amber-200 p-3"><p className="text-sm font-medium">明确编写指令 / 选择方法</p><p className="text-xs text-amber-800">此调整由你明确提出，尚未通过运行验证；不会从正文修订自动生成，也不标为已成功使用。</p>{authoring ? <><StageContractControls base={base} nodeId={nodeId} contract={{ ...contract, tunable_fields: authoredFields }} baseConfig={result?.resolved_stage?.base_config || {}} override={authoredPatch} mode="authored" disabled={locked} onChange={(field, value) => { setAuthoredPatch(current => { const patch = { ...current }; if (value === undefined) delete patch[field]; else patch[field] = value; return patch; }); invalidate(); }} /><Button size="sm" variant="secondary" disabled={locked} onClick={() => { setAuthoring(false); setAuthoredPatch({}); invalidate(); }}>取消人工调整</Button></> : <Button size="sm" variant="secondary" disabled={locked} onClick={() => { setAuthoring(true); setTuning(null); setTuningOpen(false); invalidate(); }}>开始明确编写或选择</Button>}</div>}
    <div className="mt-4 space-y-2 border-t pt-4"><Field label="明确选择一个已保存的方法版本"><select className={inputClass} value={methodId} disabled={locked || destination === "capability"} onChange={event => { setMethodId(event.target.value); invalidate(); }}><option value="">请选择，不自动采用</option>{methods.map(item => item.selection.source_kind === "capability_memory" && <option key={`${item.selection.artifact_id}:${item.selection.revision_id}`} value={`${item.selection.artifact_id}:${item.selection.revision_id}`}>{item.name} · #{item.selection.artifact_id} / 版本 #{item.selection.revision_id} · {stageValue(item.matched_scope)}</option>)}</select></Field><Button variant="secondary" size="sm" disabled={locked || !methodRequest} onClick={() => inspect("method")}>预览方法应用差异</Button></div>
    {(preview || methodPreview) && <div className="mt-4 rounded-lg bg-indigo-50 p-3">{preview?.content_only || preview && !preview.has_config_change ? <p className="text-sm text-amber-800">这次没有可保存的参数差异。可以明确编写新的指令或选择方法，再预览保存；也可以先调节、重新运行并接受结果。</p> : <>{preview?.patch_source === "user_authored" && <p className="mb-2 text-xs text-amber-800">来源：人工明确调整，尚未实测。此次保存不证明它已经产生过好结果。</p>}{preview?.patch_source === "accepted_override" && <p className="mb-2 text-xs text-indigo-700">来源：本次已执行且结果已接受的参数差异。</p>}<DiffTable diff={(preview || methodPreview)!.diff} contract={contract} />{defaultDestination && <div className="mt-4 space-y-3 rounded-lg border border-amber-200 bg-white p-3 text-xs"><p className="font-medium text-amber-800">完整默认模板替换：{impacts[destination]}</p>{fullDiffAvailable ? <DefinitionChanges value={definitionDiff} /> : <p role="alert" className="text-rose-700">服务端尚未提供完整模板替换差异（definition_diff）；无法核对新增、删除、修改阶段及顺序、依赖连线，已禁止保存。</p>}</div>}<p className="mt-2 text-xs">目标：{destinationNames[destination]}{target?.scope_id ? ` #${target.scope_id}` : ""} · 当前版本 {(preview || methodPreview)!.expected_revision}</p><label className="mt-3 flex items-start gap-2 text-sm"><input type="checkbox" checked={confirmed} disabled={locked || !fullDiffAvailable} onChange={event => setConfirmed(event.target.checked)} /><span>{defaultDestination ? "我确认以上完整模板替换差异、所有阶段和依赖的变化及默认作用范围，创建新的默认版本。" : "我确认以上差异和影响范围，创建新的版本。"}</span></label></>}{preview && !allowedPatch && <p role="alert" className="text-xs text-rose-700">差异包含当前阶段不允许调节的字段，已禁止保存。</p>}</div>}
    {preview?.method_scope && destination === "capability" && <p className="mt-2 rounded-lg bg-indigo-50 p-3 text-xs">方法候选范围：{({ persona: "当前角色", account: "当前账号", series: "当前系列", project: "当前项目" } as Record<string, string>)[preview.method_scope.scope_type] || preview.method_scope.scope_type} #{preview.method_scope.scope.id}。不会自动推广到其他角色；扩大范围需要在方法库单独确认。</p>}
    <div className="mt-3 flex flex-wrap gap-2"><Button disabled={readOnly || busy || tuningBusy || !pending && (!confirmed || !fullDiffAvailable || !name.trim() || !preview && !methodPreview || Boolean(preview && (!preview.has_config_change || !allowedPatch || destination === "capability" && methodKind === "prompt_skill" && !preview.config_patch.instruction)))} onClick={save}>{pending ? "重试原保存请求" : "确认保存新版本 / 方法候选"}</Button><Button variant="secondary" disabled={locked || !feedbackId} onClick={() => setTuningOpen(true)}>明确请求 AI 调优建议</Button>{tuning && <Button variant="secondary" size="sm" disabled={locked} onClick={() => { setTuning(null); invalidate(); }}>恢复这次尝试的原调节差异</Button>}</div>
    {tuning && <p className="mt-2 text-xs text-indigo-700">已选用调优建议 #{tuning.tuning_suggestion_id} 的明确参数修改。请重新预览差异并确认保存。</p>}
    {tuningOpen && result && feedbackId && <Suspense fallback={<Spinner label="加载调优建议控件…" />}><StageTuningPanel base={base} nodeId={nodeId} runId={result.run_id} acceptedFeedbackId={feedbackId} contract={contract} readOnly={readOnly || busy || Boolean(pending)} onBusy={value => { setTuningBusy(value); onBusy(value); }} onPatch={patch => { setTuning(patch); setAuthoring(false); setAuthoredPatch({}); invalidate(); }} onInvalidate={() => { setTuning(null); invalidate(); }} /></Suspense>}
    {notice && <p className="mt-3 text-xs text-emerald-700" role="status">{notice}</p>}{error && <div className="mt-3"><ErrorBanner message={error} /></div>}
  </section>;
}
