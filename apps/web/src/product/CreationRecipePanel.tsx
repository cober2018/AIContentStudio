import { lazy, Suspense, useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api, ApiError, currentUser } from "../api";
import { Button, ErrorBanner, Spinner, StatusBadge } from "../components/ui";
import { emptyStage, needsStageRecovery, nextActionableStage, prepareStageRequest, recoveredStage, stageRecoveryTarget, stageValue, tuneStage, type StageContract, type StageLocal, type StageRecovery, type StageRequest } from "./creationRecipeState";
import { stageFeedback, type StageFeedbackDecision, type StageFeedbackRequest, type StageResult } from "./stageProposalState";
import type { StageAcceptance } from "./StageProposalReview";
import type { StageDomainAcceptance } from "./StageDomainResultPanel";
import type { CreativeAcceptance } from "./StageCreativeResultPanel";

const StageProposalReview = lazy(() => import("./StageProposalReview"));
const StageContractControls = lazy(() => import("./StageContractControls"));
const StageDomainResultPanel = lazy(() => import("./StageDomainResultPanel"));
const StageHistoryPanel = lazy(() => import("./StageHistoryPanel"));
const StageLearningPanel = lazy(() => import("./StageLearningPanel"));
const StageRecipePicker = lazy(() => import("./StageRecipePicker"));
const StageCreativeResultPanel = lazy(() => import("./StageCreativeResultPanel"));
const GraphicRecipeReadiness = lazy(() => import("./GraphicRecipeReadiness"));
const ProjectAssetsTab = lazy(() => import("./project/ProjectAssetsTab").then(module => ({ default: module.ProjectAssetsTab })));

type Stage = {
  node_id: string;
  kind: string;
  plugin: string;
  plugin_version: string;
  label: string;
  mode: "stage" | "advanced_legacy";
  controls: StageContract | null;
  status: string;
  readiness: string;
  dependencies: string[];
  last_attempt: { id: number; attempt_no: number; status: string; input_hash: string | null; output_hash: string | null } | null;
  accepted_target: { output_kind: string; entity_id: number; decision: string; accepted_hash: string; payload_hash?: string; project_output_id: number } | null;
  blockers: string[];
  base_config: Record<string, unknown> | null;
};

type Recipe = {
  workflow_id: number | null;
  workflow_version?: number | null;
  definition_checksum?: string | null;
  source?: string;
  source_revision?: number | null;
  run_id: number | null;
  readonly: boolean;
  stages: Stage[];
  inherited_default?: { source: string; revision: number; workflow_id: number; checksum: string; diff: Record<string, unknown> } | null;
  history?: { workflow_id: number; version: number; checksum: string; diff: Record<string, unknown> }[];
};

type Preview = {
  ready: boolean;
  blockers: string[];
  resolution_hash: string | null;
  base_config?: Record<string, unknown>;
  effective_config: Record<string, unknown>;
  prompt_sections?: { key: string; text: string; hash: string }[];
  effective_prompt?: string;
  system_prompt?: string;
  prompt_hash?: string;
  model?: { provider?: string; model?: string; profile_id?: string; status?: string };
  method?: { source_kind?: string; key?: string; version?: string };
  upstream?: Record<string, unknown>;
};

function message(error: unknown) {
  return error instanceof ApiError ? `${error.status} · ${error.message}` : "请求失败，请检查后端服务。";
}

const layers: Record<string, string> = { method: "方法 / Skill", identity: "固定身份", stage_instruction: "阶段指令", execution_controls: "执行参数", brief: "创作任务", intent: "创作意图", evidence: "事实约束", upstream: "已接受的上游内容", task_override: "仅本次调整", persona_creative_configuration: "角色创作配置 / 风格 / 模型策略" };
const scopes: Record<string, string> = { series: "系列默认", account: "账号默认", persona: "角色默认", project_override: "项目覆盖" };

export default function CreationRecipePanel({ projectId, unitId, readOnly, onOpenAdvanced, workflowRevision = 0, onRecipeChanged, modality, onOpenMaster }: {
  projectId: number; unitId: number; readOnly: boolean; onOpenAdvanced: () => void;
  workflowRevision?: number; onRecipeChanged?: () => Promise<void>; modality?: string; onOpenMaster?: () => void;
}) {
  const [params, setParams] = useSearchParams();
  const base = `/content-projects/${projectId}/units/${unitId}`;
  const [recipe, setRecipe] = useState<Recipe | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [locals, setLocals] = useState<Record<string, StageLocal<Preview, Record<string, unknown>>>>({});
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [tab, setTab] = useState<"basic" | "advanced">("basic");
  const [opened, setOpened] = useState<Record<string, { result?: boolean; history?: boolean; learning?: boolean }>>({});
  const [pickerOpen, setPickerOpen] = useState(false);
  const [graphicAssetsOpen, setGraphicAssetsOpen] = useState(false);
  const [graphicAssetsOpened, setGraphicAssetsOpened] = useState(false);
  const [epoch, setEpoch] = useState(0);
  const [actionOwner, setActionOwner] = useState<string | null>(null);
  const [pendingReruns, setPendingReruns] = useState<Record<string, { request: StageRequest; feedback: StageFeedbackRequest }>>({});
  const seenWorkflowRevision = useRef(workflowRevision);
  const dispatchingStage = useRef<string | null>(null);

  function panelBusy(owner: string, value: boolean) { setBusy(value); setActionOwner(value ? owner : null); }
  function panelReadOnly(owner: string) { return locked || busy && actionOwner !== owner || Object.keys(pendingReruns).length > 0; }

  function selectStage(nodeId: string) {
    setSelectedId(nodeId); setError("");
    setParams(current => { const next = new URLSearchParams(current); next.set("stage", nodeId); return next; }, { replace: true });
  }
  function openPanel(kind: "result" | "history" | "learning") {
    if (selectedId) setOpened(current => ({ ...current, [selectedId]: { ...current[selectedId], [kind]: !current[selectedId]?.[kind] } }));
  }

  function graphicAssetsChanged() {
    // New exact refs change the effective request, never an already accepted plan.
    setLocals(current => Object.fromEntries(Object.entries(current).map(([id, state]) => [id, { ...state, preview: null }])));
  }

  async function reload() {
    const value = await api.get<Recipe>(`${base}/creation-recipe`);
    setRecipe(value);
    setSelectedId(current => current && value.stages.some(stage => stage.node_id === current) ? current : nextActionableStage(value.stages));
    setEpoch(current => current + 1);
    return value;
  }

  useEffect(() => {
    let alive = true;
    setLoading(true);
    setLocals({}); setOpened({}); setPendingReruns({}); setActionOwner(null); setBusy(false); setError("");
    api.get<Recipe>(`${base}/creation-recipe`).then(value => {
      if (alive) { setRecipe(value); const requested = params.get("stage"); setSelectedId(requested && value.stages.some(stage => stage.node_id === requested) ? requested : nextActionableStage(value.stages)); }
    }).catch(cause => { if (alive) setError(message(cause)); }).finally(() => { if (alive) setLoading(false); });
    return () => { alive = false; };
  }, [projectId, unitId]);

  useEffect(() => {
    if (seenWorkflowRevision.current === workflowRevision) return;
    seenWorkflowRevision.current = workflowRevision;
    let alive = true;
    setLocals(current => Object.fromEntries(Object.entries(current).map(([id, state]) => [id, { ...state, preview: null }])));
    api.get<Recipe>(`${base}/creation-recipe`).then(value => {
      if (!alive) return;
      setRecipe(value);
      setSelectedId(current => current && value.stages.some(stage => stage.node_id === current) ? current : nextActionableStage(value.stages));
      setEpoch(current => current + 1);
    }).catch(cause => { if (alive) setError(message(cause)); });
    return () => { alive = false; };
  }, [projectId, unitId, workflowRevision]);

  useEffect(() => {
    const requested = params.get("stage");
    if (requested && recipe?.stages.some(stage => stage.node_id === requested)) setSelectedId(requested);
  }, [params, recipe]);

  const selected = useMemo(() => recipe?.stages.find(stage => stage.node_id === selectedId) || null, [recipe, selectedId]);
  const directAudioASR = selected?.plugin === "stage.audio.qc"
    && selected.dependencies.some(nodeId => recipe?.stages.some(stage => stage.node_id === nodeId && stage.plugin === "stage.audio.asr"));
  const local = selectedId ? locals[selectedId] || emptyStage<Preview, Record<string, unknown>>() : emptyStage<Preview, Record<string, unknown>>();
  const { override: overrides, preview, result } = local;
  const locked = readOnly || Boolean(recipe?.readonly);
  const unsettled = busy || Object.keys(pendingReruns).length > 0;
  const unresolvedLocal = Object.values(locals).some(state => state.request
    || ["running", "unknown"].includes(String(state.result?.status)));
  const canPrepareRun = Boolean(recipe?.stages.length && recipe.stages.every(stage => stage.mode === "stage")
    && !unresolvedLocal && !Object.keys(pendingReruns).length
    && (!recipe.run_id || recipe.stages.every(stage => ["succeeded", "failed", "blocked", "stale", "skipped"].includes(stage.status)
      && !["running", "unknown"].includes(stage.last_attempt?.status || ""))));
  const recoveryTarget = stageRecoveryTarget(local, recipe?.run_id || null, selected?.last_attempt?.id || null);
  const recovering = needsStageRecovery(local, recoveryTarget);
  const pendingRerun = selectedId ? pendingReruns[selectedId] : undefined;
  const editable = !locked && !busy && !recovering && !pendingRerun && selected?.controls?.supports_run_override === true;
  function updateLocal(nodeId: string, update: (state: StageLocal<Preview, Record<string, unknown>>) => StageLocal<Preview, Record<string, unknown>>) {
    setLocals(current => ({ ...current, [nodeId]: update(current[nodeId] || emptyStage<Preview, Record<string, unknown>>()) }));
  }
  function change(field: string, value: unknown) {
    if (selectedId) updateLocal(selectedId, state => tuneStage(state, field, value));
  }

  async function readResult(nodeId: string, target: StageRecovery) {
    const query = new URLSearchParams({ run_id: String(target.run_id) });
    if (target.invocation_key !== undefined) query.set("invocation_key", target.invocation_key);
    else query.set("attempt_id", String(target.attempt_id));
    const value = await api.get<Record<string, unknown>>(`${base}/creation-recipe/stages/${encodeURIComponent(nodeId)}/result?${query}`);
    if (value.node_id !== nodeId) throw new Error("stage_recovery_node_mismatch");
    return value;
  }

  useEffect(() => {
    let alive = true;
    if (selected?.mode !== "stage" || !recoveryTarget) return;
    // The active request owns its response; its durable claim may not exist yet.
    if (local.request && dispatchingStage.current === selected.node_id) return;
    const nodeId = selected.node_id;
    const target = recoveryTarget;
    readResult(nodeId, target).then(value => {
      recoveredStage(local, target, value);
      if (alive) updateLocal(nodeId, state => recoveredStage(state, target, value));
    }).catch(cause => { if (alive) setError(message(cause)); });
    return () => { alive = false; };
  }, [projectId, unitId, selectedId, selected?.last_attempt?.id, recipe?.run_id, local.request?.invocation_key]);

  async function recoverStage() {
    if (!selected || !recoveryTarget || busy) return;
    const nodeId = selected.node_id;
    const target = recoveryTarget;
    setBusy(true); setError("");
    try {
      const value = await readResult(nodeId, target);
      recoveredStage(local, target, value);
      updateLocal(nodeId, state => recoveredStage(state, target, value));
      await reload();
    } catch (cause) { setError(message(cause)); } finally { setBusy(false); }
  }

  async function prepareRun() {
    if (locked || unsettled || !canPrepareRun) return;
    setBusy(true); setError("");
    try {
      await api.post(`${base}/runs`, { params: {} });
      await reload();
      setLocals(current => Object.fromEntries(Object.entries(current).map(([id, state]) => [id, {
        ...emptyStage<Preview, Record<string, unknown>>(), override: state.override,
      }])));
    }
    catch (cause) { setError(message(cause)); } finally { setBusy(false); }
  }

  async function previewStage() {
    if (!selected || selected.mode !== "stage" || selected.controls?.supports_preview !== true || recovering || busy || pendingRerun) return;
    const nodeId = selected.node_id;
    const revision = seenWorkflowRevision.current;
    setBusy(true); setError("");
    try {
      const value = await api.post<Preview>(`${base}/creation-recipe/stages/${encodeURIComponent(nodeId)}/preview`, { run_id: recipe?.run_id, stage_override: overrides });
      if (revision !== seenWorkflowRevision.current) return;
      updateLocal(nodeId, state => ({ ...state, preview: value }));
    } catch (cause) { setError(message(cause)); } finally { setBusy(false); }
  }

  async function runStage() {
    if (!selected || !recipe?.run_id || locked || busy || (!recovering && !pendingRerun && (!preview?.ready || !preview.resolution_hash))) return;
    const nodeId = selected.node_id;
    if (recovering) { await recoverStage(); return; }
    const request = pendingRerun?.request || prepareStageRequest(local, recipe.run_id, `manual:${crypto.randomUUID()}`);
    setBusy(true); setError("");
    let invoked = false;
    try {
      const previous = result as StageResult | null;
      if (pendingRerun || previous?.attempt_id && previous.receipt && local.rerunFeedbackAttemptId !== previous.attempt_id) {
        const feedback = pendingRerun?.feedback || stageFeedback(previous!, "rerun_requested", `rerun:${request.invocation_key}`, [], "明确执行新的阶段尝试");
        setPendingReruns(current => ({ ...current, [nodeId]: { request, feedback } }));
        await api.post(`${base}/creation-recipe/stages/${encodeURIComponent(nodeId)}/feedback`,
          feedback);
        setPendingReruns(current => { const next = { ...current }; delete next[nodeId]; return next; });
        updateLocal(nodeId, state => ({ ...state, rerunFeedbackAttemptId: feedback.attempt_id }));
      }
      invoked = true;
      dispatchingStage.current = nodeId;
      updateLocal(nodeId, state => ({ ...state, request }));
      const value = await api.post<Record<string, unknown>>(`${base}/creation-recipe/stages/${encodeURIComponent(nodeId)}/run`, request);
      updateLocal(nodeId, state => ({ ...state, result: value, request: ["running", "unknown"].includes(String(value.status)) ? request : null }));
      await reload();
    } catch (cause) {
      if (cause instanceof ApiError && cause.status < 500) {
        updateLocal(nodeId, state => ({ ...state, request: null, preview: null }));
        if (!invoked) setPendingReruns(current => { const next = { ...current }; delete next[nodeId]; return next; });
      }
      setError(message(cause));
      try { await reload(); } catch { /* Keep the original request when status cannot be read back. */ }
    } finally { dispatchingStage.current = null; setBusy(false); }
  }

  async function reconcileStage() {
    if (!selected?.last_attempt || !recipe?.run_id || locked || unsettled) return;
    const nodeId = selected.node_id;
    setBusy(true); setError("");
    try {
      const value = await api.post<Record<string, unknown>>(`${base}/creation-recipe/stages/${encodeURIComponent(nodeId)}/reconcile`, { run_id: recipe.run_id, attempt_id: selected.last_attempt.id });
      updateLocal(nodeId, state => ({ ...state, result: value }));
      await reload();
    } catch (cause) { setError(message(cause)); } finally { setBusy(false); }
  }

  async function acceptedStage(nodeId: string, value: StageAcceptance) {
    updateLocal(nodeId, state => ({ ...state, preview: null, result: { ...state.result, is_current: false,
      accepted_master: value.master, feedback_event_id: value.feedback_event_id,
      accepted_target: { entity_id: value.master.id, accepted_hash: value.master.payload_hash, decision: value.decision, feedback_event_id: value.feedback_event_id } } }));
    await reload();
  }

  async function acceptedDomain(nodeId: string, value: StageDomainAcceptance) {
    const current = locals[nodeId]?.result as StageResult | undefined;
    updateLocal(nodeId, state => ({ ...state, preview: null, result: { ...state.result, is_current: false,
      accepted_target: value.accepted_target, accepted_entity: value.accepted_entity, feedback_event_id: value.feedback_event_id } }));
    if (current) {
      const recovered = await readResult(nodeId, { run_id: current.run_id, attempt_id: current.attempt_id });
      updateLocal(nodeId, state => ({ ...state, preview: null, result: { ...recovered, feedback_event_id: value.feedback_event_id } }));
    }
    await reload();
  }
  async function acceptedCreative(nodeId: string, value: CreativeAcceptance) {
    const current = locals[nodeId]?.result as StageResult | undefined;
    updateLocal(nodeId, state => ({ ...state, preview: null, result: { ...state.result,
      accepted_target: value.accepted_target, feedback_event_id: value.feedback_event_id } }));
    if (current) {
      const recovered = await readResult(nodeId, { run_id: current.run_id, attempt_id: current.attempt_id });
      updateLocal(nodeId, state => ({ ...state, preview: null, result: recovered }));
    }
    await reload();
  }
  async function feedbackStage(nodeId: string, decision: StageFeedbackDecision) {
    const current = locals[nodeId]?.result as StageResult | undefined;
    if (current) {
      const recovered = await readResult(nodeId, { run_id: current.run_id, attempt_id: current.attempt_id });
      updateLocal(nodeId, state => ({ ...state, preview: null, result: recovered,
        ...(decision === "rerun_requested" ? { rerunFeedbackAttemptId: current.attempt_id } : {}) }));
    }
    await reload();
  }
  async function changedRecipe() {
    try {
      const value = await reload();
      if (value.definition_checksum !== recipe?.definition_checksum) {
        setLocals(current => Object.fromEntries(Object.entries(current).map(([id, state]) => [id, { ...state, preview: null }])));
      }
    } finally { await onRecipeChanged?.(); }
  }

  if (loading) return <section className="mb-5 rounded-xl border border-slate-200 bg-white"><Spinner label="加载 Creation Recipe…" /></section>;
  if (error && !recipe) return <section className="mb-5"><ErrorBanner message={error} /></section>;
  if (!recipe || recipe.stages.length === 0) return <section className="mb-5 rounded-xl border border-slate-200 bg-white p-5"><h2 className="font-semibold">Creation Recipe</h2><p className="mt-2 text-sm text-slate-500">先明确选择创作流程，再逐阶段调节和审阅。</p><Button className="mt-3" variant="secondary" disabled={busy} onClick={() => setPickerOpen(true)}>选择创作流程</Button>{pickerOpen && <Suspense fallback={<Spinner />}><StageRecipePicker base={base} readOnly={panelReadOnly("recipe") || !recipe} onBusy={value => panelBusy("recipe", value)} onAdopted={changedRecipe} /></Suspense>}</section>;

  return <section className="mb-5 rounded-2xl border border-indigo-100 bg-gradient-to-br from-indigo-50/70 to-white p-5" aria-label="Creation Recipe 创作流程">
    <div className="flex flex-wrap items-start justify-between gap-3">
      <div><p className="text-xs font-semibold uppercase tracking-widest text-indigo-600">Creation Recipe</p><h2 className="mt-1 text-xl font-semibold">按阶段完成内容生产</h2><p className="mt-1 text-sm text-slate-600">先查看阶段细节与实际请求，再执行；结果仍需人工接受，不会自动写入 Master。</p></div>
      <div className="flex flex-wrap gap-2"><Button variant="secondary" size="sm" disabled={unsettled} onClick={() => setPickerOpen(current => !current)}>选择创作流程</Button><Button variant="secondary" size="sm" disabled={unsettled} onClick={onOpenAdvanced}>高级工作流</Button></div>
    </div>
    <div className="mt-3 flex flex-wrap items-center gap-3 text-xs text-slate-600"><span>{scopes[recipe.source || ""] || recipe.source} · Workflow #{recipe.workflow_id} v{recipe.workflow_version} · 来源版本 {recipe.source_revision}</span><span className="break-all">checksum {recipe.definition_checksum}</span>{canPrepareRun && <Button size="sm" disabled={unsettled || locked} onClick={prepareRun}>{recipe.run_id ? "准备新的运行（不调用模型）" : "准备本次运行（不调用模型）"}</Button>}</div>
    <details className="mt-3 text-xs text-slate-600"><summary className="cursor-pointer">默认差异与流程历史</summary>{recipe.inherited_default && <p className="mt-2">继承 {scopes[recipe.inherited_default.source] || recipe.inherited_default.source} · Workflow #{recipe.inherited_default.workflow_id} · 版本 {recipe.inherited_default.revision} · {stageValue(recipe.inherited_default.diff)}</p>}<ul className="mt-2 space-y-1">{recipe.history?.map(item => <li key={item.workflow_id}>v{item.version} · #{item.workflow_id} · {item.checksum.slice(0, 16)} · {stageValue(item.diff)}</li>)}</ul></details>
    {pickerOpen && <Suspense fallback={<Spinner label="加载流程选择…" />}><StageRecipePicker base={base} readOnly={panelReadOnly("recipe")} onBusy={value => panelBusy("recipe", value)} onAdopted={changedRecipe} /></Suspense>}
    {nextActionableStage(recipe.stages) && nextActionableStage(recipe.stages) !== selectedId && <Button className="mt-3" size="sm" variant="secondary" disabled={unsettled} onClick={() => selectStage(nextActionableStage(recipe.stages)!)}>前往下一个可处理阶段</Button>}
    <div className="mt-4 flex gap-2 overflow-x-auto pb-1" role="tablist" aria-label="Creation Recipe 阶段">
      {recipe.stages.map((stage, index) => <button key={stage.node_id} type="button" role="tab" id={`recipe-${projectId}-${unitId}-${stage.node_id}`} aria-controls={`recipe-${projectId}-${unitId}-details`} tabIndex={stage.node_id === selectedId ? 0 : -1} aria-selected={stage.node_id === selectedId} disabled={unsettled} onClick={() => selectStage(stage.node_id)} onKeyDown={event => {
        if (!["ArrowRight", "ArrowLeft", "Home", "End"].includes(event.key) || unsettled) return;
        event.preventDefault();
        const next = event.key === "Home" ? 0 : event.key === "End" ? recipe.stages.length - 1 : (index + (event.key === "ArrowRight" ? 1 : -1) + recipe.stages.length) % recipe.stages.length;
        selectStage(recipe.stages[next].node_id);
        event.currentTarget.parentElement?.querySelectorAll<HTMLButtonElement>('[role="tab"]')[next]?.focus();
      }} className={`min-w-36 rounded-lg border px-3 py-2 text-left transition ${stage.node_id === selectedId ? "border-indigo-500 bg-white shadow-sm" : "border-slate-200 bg-white/60 hover:border-indigo-300"}`}>
        <span className="block text-[11px] text-slate-400">{index + 1} · {stage.kind}</span><span className="mt-1 block truncate text-sm font-medium">{stage.label}</span><span className="mt-1 flex items-center gap-1"><StatusBadge status={stage.status} />{stage.accepted_target && <span className="text-[11px] text-emerald-700">已接受</span>}{Object.keys(locals[stage.node_id]?.override || {}).length > 0 && <span className="text-[11px] text-indigo-700">本次调整</span>}</span>
      </button>)}
    </div>
    {selected && <div role="tabpanel" id={`recipe-${projectId}-${unitId}-details`} aria-labelledby={`recipe-${projectId}-${unitId}-${selected.node_id}`} className="mt-4 grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
      <div className="rounded-xl border border-slate-200 bg-white p-4">
        <div className="flex flex-wrap items-start justify-between gap-2"><div><h3 className="font-semibold">{selected.label}</h3><p className="mt-1 text-xs text-slate-500">{selected.plugin}@{selected.plugin_version} · {selected.mode === "stage" ? selected.controls?.stage_schema : "旧工作流节点"}</p></div><StatusBadge status={selected.status} /></div>
        {selected.dependencies.length > 0 && <p className="mt-3 text-xs text-slate-500">依赖阶段：{selected.dependencies.join("、")}</p>}
        {selected.accepted_target ? <div className="mt-3 rounded-lg bg-emerald-50 p-3 text-xs text-emerald-800"><p>已接受：{selected.accepted_target.output_kind} #{selected.accepted_target.entity_id} · {selected.accepted_target.decision}</p><p className="mt-1 break-all">accepted hash：{selected.accepted_target.accepted_hash}</p></div> : <p className="mt-3 rounded-lg bg-slate-50 p-3 text-xs text-slate-600">尚无已接受结果。生成成功不等于内容已进入 Master。</p>}
        {selected.last_attempt && <div className="mt-3 text-xs text-slate-500">最近尝试 #{selected.last_attempt.attempt_no} · {selected.last_attempt.status}{selected.last_attempt.output_hash ? ` · output ${selected.last_attempt.output_hash.slice(0, 12)}…` : ""}</div>}
        {selected.blockers.length > 0 && <p className="mt-3 text-xs text-amber-700">当前提示：{selected.blockers.join("、")}</p>}
        {selected.status === "running" && <details className="mt-3 rounded-lg bg-amber-50 p-3 text-xs"><summary>执行中断了？</summary><p className="mt-2">只在原进程已中断且结果无法确认时操作。此操作将原尝试标为未知，不重发请求。</p><Button size="sm" variant="secondary" disabled={locked || busy} onClick={reconcileStage}>确认中断，保留原尝试为未知</Button></details>}
      </div>
      <div className="rounded-xl border border-slate-200 bg-white p-4">
        {selected.mode !== "stage" || !selected.controls ? <><h3 className="font-semibold">高级节点</h3><p className="mt-2 text-sm text-slate-500">此节点没有 Creation Recipe Stage Contract。请在高级工作流中按原有语义编辑。</p></> : <>
          <div className="mb-3 flex gap-2" role="tablist" aria-label="阶段控制模式"><button type="button" role="tab" id={`stage-basic-${unitId}`} aria-controls={`stage-controls-${unitId}`} aria-selected={tab === "basic"} onClick={() => setTab("basic")} className={`rounded-md px-3 py-2 text-sm ${tab === "basic" ? "bg-indigo-100 text-indigo-800" : "text-slate-500"}`}>基本</button><button type="button" role="tab" id={`stage-advanced-${unitId}`} aria-controls={`stage-controls-${unitId}`} aria-selected={tab === "advanced"} onClick={() => setTab("advanced")} className={`rounded-md px-3 py-2 text-sm ${tab === "advanced" ? "bg-indigo-100 text-indigo-800" : "text-slate-500"}`}>高级</button></div>
          <div role="tabpanel" id={`stage-controls-${unitId}`} aria-labelledby={`stage-${tab}-${unitId}`}>
          {tab === "basic" ? <><div className="flex items-center justify-between gap-2"><h3 className="font-semibold">本次调整</h3><span className="text-xs text-slate-500">只影响本次 Run</span></div>{directAudioASR && <p className="mt-2 text-xs text-slate-500">对稿来源是此流程已接受的本机 ASR 阶段，不需要填写 Video Master 或手抄回执 ID。</p>}<Suspense fallback={<Spinner label="加载阶段控件…" />}><StageContractControls base={base} nodeId={selected.node_id} contract={selected.controls} baseConfig={selected.base_config || {}} override={overrides} disabled={!editable} hiddenFields={directAudioASR ? ["asr_master_revision_id", "asr_receipt_id", "asr_output_hash"] : []} onChange={change} /></Suspense></> : <div className="space-y-3 text-xs"><p>高级配置、输入输出映射和依赖关系使用原工作流工具。</p><Button variant="secondary" size="sm" onClick={onOpenAdvanced}>打开配置、映射与依赖编辑器</Button><p>本次调节与内容编辑各自保留；保存新流程需明确确认。</p>{result && <details><summary>精确执行回执</summary><pre className="mt-2 max-h-44 overflow-auto whitespace-pre-wrap">{JSON.stringify(result, null, 2)}</pre></details>}</div>}
          </div>
          {modality === "graphic" && selected.plugin === "stage.creative.method" && <div className="mt-3 space-y-2 rounded-lg border border-indigo-200 p-3 text-xs"><p className="font-medium">视觉素材准备 / 精确版本选择</p><p>缺照片或插图时，先明确上传、引用或生成并接受到项目素材。生成图不能冒充新闻照片或事实证据；权利未证明时仍不可使用。素材变化后重新预览，并明确生成/接受新的卡片计划，旧结果不会自动改写。</p><Button size="sm" variant="secondary" disabled={unsettled || recovering} onClick={() => { setGraphicAssetsOpened(true); setGraphicAssetsOpen(value => !value); }}>{graphicAssetsOpen ? "收起素材准备（保留本地填写）" : "准备 / 选择项目素材"}</Button></div>}
          {modality === "graphic" && selected.plugin === "stage.checks" && onOpenMaster && <Suspense fallback={<Spinner label="加载图文成品承接…" />}><GraphicRecipeReadiness base={base} readOnly={panelReadOnly("graphic-render")} onOpenMaster={onOpenMaster} /></Suspense>}
          <div className="mt-4 flex flex-wrap gap-2"><Button variant="secondary" disabled={unsettled || recovering || selected.controls.supports_preview !== true} onClick={previewStage}>预览实际请求</Button><Button disabled={busy || locked || (!recovering && !pendingRerun && !preview?.ready) || !recipe.run_id || selected.controls.supports_preview !== true} onClick={runStage}>{recovering ? "回读原尝试（不重发）" : pendingRerun ? "重试原重跑反馈并执行" : result ? "再次生成（新尝试）" : "执行本阶段"}</Button></div>
          {pendingRerun && <p className="mt-2 text-xs text-amber-700">原重跑反馈尚未确认，保留原参数和调用键；确认反馈后才执行该次新尝试。</p>}
          {recovering && <p className="mt-2 text-xs text-amber-700">先恢复原 Run 的结果；读取失败或尚未完成时，不允许新调用。</p>}
          <p className="mt-2 text-[11px] text-slate-500">Preview 只解析，不调用模型；执行会重新解析并校验 resolution hash。</p>
          {selected.plugin === "stage.audio.asr" && <p className="mt-2 text-xs text-amber-700">本机 ASR 不会自动执行。先预览，再明确点击执行；识别完成后核对并接受，下一步才做对稿／字幕 QC。</p>}
          {preview && <div className="mt-3 rounded-lg bg-slate-50 p-3 text-xs"><h4 className="font-medium">实际将发送给 AI / Agent 的内容</h4><p className="mt-2">{preview.ready ? "已准备，执行时仍会校验是否变化" : `不可执行：${preview.blockers.join("、") || "请先满足前置条件"}`}</p>{preview.model && <p className="mt-1">模型：{preview.model.provider} / {preview.model.model} · 配置 {preview.model.profile_id}</p>}<p className="mt-1">方法来源：{preview.method?.source_kind || "无"}</p><table className="mt-3 w-full table-fixed text-left"><thead><tr><th>参数</th><th>已保存</th><th>本次调整</th><th>实际采用</th></tr></thead><tbody>{Object.keys(preview.effective_config).map(field => <tr key={field}><td className="break-words border-t py-2">{selected.controls?.ui_schema?.[field]?.label || field}</td><td className="break-words border-t py-2">{stageValue(preview.base_config?.[field])}</td><td className="break-words border-t py-2">{stageValue(overrides[field])}</td><td className="break-words border-t py-2">{stageValue(preview.effective_config[field])}</td></tr>)}</tbody></table>{preview.prompt_sections?.map(section => <details key={section.key} className="mt-3"><summary className="cursor-pointer font-medium">{layers[section.key] || section.key}</summary><pre className="mt-1 max-h-60 overflow-auto whitespace-pre-wrap break-words">{section.text || "此层无内容"}</pre></details>)}<details className="mt-3"><summary className="cursor-pointer font-medium">完整 System / User Prompt 与精确哈希</summary><p className="mt-2 break-all">prompt {preview.prompt_hash} · resolution {preview.resolution_hash}</p><pre className="mt-2 max-h-96 overflow-auto whitespace-pre-wrap break-words">{`System:\n${preview.system_prompt || ""}\n\nUser:\n${preview.effective_prompt || ""}`}</pre></details></div>}
        </>}
      </div>
    </div>}
    {modality === "graphic" && graphicAssetsOpened && <div hidden={!graphicAssetsOpen} className="mt-4" aria-label="Recipe 项目视觉素材准备"><Suspense fallback={<Spinner label="加载现有项目素材工具…" />}><ProjectAssetsTab key={`${projectId}:${unitId}:${currentUser()}`} projectId={projectId} readOnly={locked} disabled={panelReadOnly("graphic-assets") || recovering} onChanged={graphicAssetsChanged} onBusy={value => panelBusy("graphic-assets", value)} /></Suspense></div>}
    {selected?.mode === "stage" && <div className="mt-4 flex flex-wrap gap-2"><Button size="sm" variant="secondary" disabled={busy || !result} onClick={() => openPanel("result")}>{opened[selected.node_id]?.result ? "收起结果" : "查看本次结果"}</Button><Button size="sm" variant="secondary" disabled={busy || !recipe.run_id} onClick={() => openPanel("history")}>{opened[selected.node_id]?.history ? "收起历史与反馈" : "历史与反馈"}</Button><Button size="sm" variant="secondary" disabled={busy} onClick={() => openPanel("learning")}>{opened[selected.node_id]?.learning ? "收起保存与复用" : "保存有效调整 / 复用方法"}</Button></div>}
    {recipe.stages.map(stage => {
      const value = locals[stage.node_id]?.result as StageResult | null | undefined;
      const panels = opened[stage.node_id];
      if (!panels || stage.mode !== "stage" || !stage.controls) return null;
      return <div key={stage.node_id} hidden={selectedId !== stage.node_id}>
        {panels.result !== undefined && value && <div hidden={!panels.result} key={`${value.run_id}:${value.attempt_id}`}><Suspense fallback={<Spinner label="加载结果审阅…" />}>
          {value.output?.schema === "stage.master.proposal.v1" && value.receipt && value.resolved_stage
            ? <StageProposalReview projectId={projectId} unitId={unitId} result={value} readOnly={panelReadOnly(`result:${stage.node_id}`) || value.run_id !== recipe.run_id} onBusy={active => panelBusy(`result:${stage.node_id}`, active)} onAccepted={accepted => acceptedStage(stage.node_id, accepted)} />
            : stage.plugin === "stage.creative.method" && Array.isArray(value.output?.candidates)
              ? <StageCreativeResultPanel base={base} result={value} readOnly={panelReadOnly(`result:${stage.node_id}`) || value.run_id !== recipe.run_id} onBusy={active => panelBusy(`result:${stage.node_id}`, active)} onAccepted={accepted => acceptedCreative(stage.node_id, accepted)} />
              : value.domain_output
                ? <StageDomainResultPanel base={base} result={value} readOnly={panelReadOnly(`result:${stage.node_id}`) || value.run_id !== recipe.run_id} onBusy={active => panelBusy(`result:${stage.node_id}`, active)} onAccepted={accepted => acceptedDomain(stage.node_id, accepted)} />
                : <p className="mt-3 rounded-lg bg-slate-50 p-3 text-sm">当前尝试：{String(value.status)}。尚无可审阅结果，请回读当前阶段状态。</p>}
        </Suspense></div>}
        {panels.history !== undefined && recipe.run_id && <div hidden={!panels.history}><Suspense fallback={<Spinner label="加载阶段历史…" />}><StageHistoryPanel key={`${recipe.run_id}:${stage.node_id}`} base={base} nodeId={stage.node_id} runId={recipe.run_id} result={value || null} contract={stage.controls} readOnly={panelReadOnly(`history:${stage.node_id}`) || Boolean(value && value.run_id !== recipe.run_id)} epoch={epoch} onBusy={active => panelBusy(`history:${stage.node_id}`, active)} onFeedback={decision => feedbackStage(stage.node_id, decision)} /></Suspense></div>}
        {panels.learning !== undefined && <div hidden={!panels.learning}><Suspense fallback={<Spinner label="加载有效调整…" />}><StageLearningPanel key={`${recipe.run_id}:${stage.node_id}:${value?.attempt_id || ""}`} base={base} nodeId={stage.node_id} result={value || null} contract={stage.controls} readOnly={panelReadOnly(`learning:${stage.node_id}`) || Boolean(value && value.run_id !== recipe.run_id)} onBusy={active => panelBusy(`learning:${stage.node_id}`, active)} onSaved={changedRecipe} /></Suspense></div>}
      </div>;
    })}
    {error && <div className="mt-3"><ErrorBanner message={error} /></div>}
  </section>;
}
