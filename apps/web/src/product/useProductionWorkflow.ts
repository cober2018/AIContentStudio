import { useEffect, useMemo, useRef, useState } from "react";
import { api, ApiError } from "../api";
import type { Definition, Persona, Project, SharedAsset, Unit, WorkflowBinding, WorkflowNode } from "./project/projectTypes";

export type Step = { id: number; node_id: string; node_type: string; label: string; status: string; params: Record<string, unknown>; output: Record<string, unknown>; error: string | null; stale_reason: string | null; attempt_no: number };
export type Run = { id: number; status: string; workflow_id: number; workflow_version: number | null; definition_checksum: string | null; identity_snapshot_id: number | null; identity_state: string; definition: Definition; steps: Step[]; error: string | null };
export type IdentitySnapshot = { id: number; brand_id: number | null; persona_id: number; account_id: number | null; series_id: number | null; revision_ids?: Record<string, number | null>; brand_revision_id: number | null; persona_revision_id: number | null; account_revision_id: number | null; series_revision_id: number | null; brand_voice_version_id: number | null; effective_profile: Record<string, unknown>; field_origins: Record<string, string>; checksum: string };
export type Attempt = { attempt_no: number; status: string; input_hash: string | null; output_hash: string | null; output_json: Record<string, unknown>; error: string | null };
export type DataPlugin = { key: string; name: string; category: string; available: boolean; reason: string | null; config_schema: Record<string, unknown> };
export type DataCapability = { id: number; key: string; version: string; plugin_key: string; source_ref: string; executable: boolean; verified: boolean };
export type ExecutionOption = { provider: string; model: string; available: boolean; reason: string | null; profiles?: { profile_id: string; provider: string; model: string; available: boolean }[] };
export type UnitOutput = { id: number; output_kind: "draft" | "candidate" | "material_revision" | "content_master_revision"; entity_id: number; run_id: number; node_id: string; attempt_id: number | null; provenance: Record<string, unknown> };

export const KINDS: WorkflowNode["kind"][] = ["Data", "AI", "Tool", "Rule", "Human", "System"];
const DEFAULT_PLUGINS: Record<WorkflowNode["kind"], string> = {
  Data: "data.source", AI: "builtin.generate", Tool: "builtin.export", Rule: "builtin.fact_check", Human: "builtin.approve", System: "system.constant",
};
export const PLUGIN_CHOICES: Record<WorkflowNode["kind"], string[]> = {
  Data: ["data.source"],
  AI: ["builtin.generate", "builtin.humanize", "builtin.generate_cover", "media.generate", "node.skill"],
  Tool: ["builtin.connector_pull", "builtin.extract_facts", "builtin.factpack_freeze", "builtin.topic_suggest", "builtin.export"],
  Rule: ["builtin.fact_check", "builtin.content_censor", "builtin.discoverability_post"],
  Human: ["builtin.approve", "builtin.confirm_facts", "builtin.adopt_topic"],
  System: ["system.constant"],
};
export const MODALITY_NAMES: Record<string, string> = { text: "文字生产", graphic: "图文生产", video: "视频生产" };
const EMPTY: Definition = { nodes: [], edges: [], visual_order: [] };

export function problem(error: unknown) { return error instanceof ApiError ? `${error.status} · ${error.message}` : "请求失败，请检查后端服务。"; }
export function pretty(value: unknown) { return JSON.stringify(value ?? {}, null, 2); }
function workflowStamp(binding: WorkflowBinding, effective: WorkflowBinding, defaults: WorkflowBinding) {
  return JSON.stringify([binding.workflow_id, binding.revision, effective.workflow_id, effective.definition_checksum,
    defaults.workflow_id, defaults.revision]);
}

export function useProductionWorkflow(projectId: number, unitId: number) {
  const base = `/content-projects/${projectId}/units/${unitId}`;
  const [project, setProject] = useState<Project | null>(null);
  const [role, setRole] = useState<string | null>(null);
  const [unit, setUnit] = useState<Unit | null>(null);
  const [persona, setPersona] = useState<Persona | null>(null);
  const [brandName, setBrandName] = useState<string | null>(null);
  const [accountName, setAccountName] = useState<string | null>(null);
  const [seriesName, setSeriesName] = useState<string | null>(null);
  const [snapshot, setSnapshot] = useState<IdentitySnapshot | null>(null);
  const [binding, setBinding] = useState<WorkflowBinding | null>(null);
  const [defaultBinding, setDefaultBinding] = useState<WorkflowBinding | null>(null);
  const [definition, setDefinition] = useState<Definition>(EMPTY);
  const [dirty, setDirty] = useState(false);
  const [design, setDesign] = useState(false);
  const [selected, setSelected] = useState<string | null>(null);
  const [runs, setRuns] = useState<{ id: number; status: string }[]>([]);
  const [run, setRun] = useState<Run | null>(null);
  const [attempts, setAttempts] = useState<Attempt[]>([]);
  const [plugins, setPlugins] = useState<DataPlugin[]>([]);
  const [dataCapabilities, setDataCapabilities] = useState<DataCapability[]>([]);
  const [executionOptions, setExecutionOptions] = useState<Record<string, ExecutionOption>>({});
  const [assets, setAssets] = useState<SharedAsset[]>([]);
  const [outputs, setOutputs] = useState<UnitOutput[]>([]);
  const [assetsOpen, setAssetsOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [workflowConflict, setWorkflowConflict] = useState("");
  const [workflowRevision, setWorkflowRevision] = useState(0);
  const savedWorkflowStamp = useRef<string | null>(null);
  const savedEffectiveWorkflow = useRef<WorkflowBinding | null>(null);
  const workflowRefresh = useRef(0);
  const [configText, setConfigText] = useState("{}");
  const [inputText, setInputText] = useState("{}");
  const [outputText, setOutputText] = useState("{}");
  const [conditionText, setConditionText] = useState("{}");
  const [depsText, setDepsText] = useState("");
  const [dragging, setDragging] = useState<string | null>(null);
  const [newKind, setNewKind] = useState<WorkflowNode["kind"]>("System");
  const [runSourceRef, setRunSourceRef] = useState("");
  const canvasDefinition = !design && run ? run.definition : definition;
  const selectedNode = useMemo(() => canvasDefinition.nodes.find((node) => node.id === selected) || null, [canvasDefinition, selected]);
  const selectedStep = !design ? run?.steps.find((step) => step.node_id === selected) || null : null;
  const sourceCapability = dataCapabilities.find((item) => item.source_ref === selectedNode?.config.source_ref
    && item.plugin_key === selectedNode?.config.data_source_plugin_key);
  const pluginDescriptor = plugins.find((item) => item.key === selectedNode?.config.data_source_plugin_key);
  const sourcePlugin = pluginDescriptor && sourceCapability ? { ...pluginDescriptor,
    available: sourceCapability.executable, reason: sourceCapability.executable ? null : "所选连接版本未验证或已失效",
  } : pluginDescriptor;
  const executor = selectedNode?.kind === "AI" ? executionOptions[selectedNode.plugin] : null;
  const readOnly = !["editor", "admin"].includes(role ?? "") || project?.status === "archived" || unit?.status === "archived" || unit?.lifecycle === "archived" || unit?.lifecycle === "deleted";
  const inspectorDirty = Boolean(design && selectedNode && (configText !== pretty(selectedNode.config)
    || inputText !== pretty(selectedNode.input_mapping) || outputText !== pretty(selectedNode.output_mapping)
    || conditionText !== pretty(selectedNode.condition)
    || depsText !== canvasDefinition.edges.filter(edge => edge.to === selected).map(edge => edge.from).join(", ")));
  const liveWorkflow = useRef({ base, dirty: dirty || inspectorDirty, busy, definition, configText, inputText, outputText, conditionText, depsText });
  liveWorkflow.current = { base, dirty: dirty || inspectorDirty, busy, definition, configText, inputText, outputText, conditionText, depsText };

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setRole(null);
    Promise.all([
      api.get<{ role: string }>("/users/me", controller.signal),
      api.get<Project>(`/content-projects/${projectId}`, controller.signal),
      api.get<Unit>(base, controller.signal),
      api.get<WorkflowBinding>(`${base}/workflow-override`, controller.signal),
      api.get<WorkflowBinding>(`${base}/effective-workflow`, controller.signal),
      api.get<DataPlugin[]>("/data-source-plugins", controller.signal),
      api.get<{ ai: Record<string, ExecutionOption> }>("/workflow-execution-options", controller.signal),
      api.get<{ id: number; status: string }[]>(`${base}/runs`, controller.signal),
      api.get<SharedAsset[]>(`/content-projects/${projectId}/shared-assets`, controller.signal),
      api.get<UnitOutput[]>(`${base}/outputs`, controller.signal),
      api.get<DataCapability[]>("/data-source-capabilities", controller.signal),
    ]).then(async ([me, nextProject, nextUnit, nextBinding, nextEffective, nextPlugins, nextExecutors, nextRuns, nextAssets, nextOutputs, nextCapabilities]) => {
      const product = nextUnit.production_domain === "product";
      const [personas, nextDefault] = await Promise.all([
        product ? Promise.resolve([] as Persona[]) : api.get<Persona[]>("/content-personas", controller.signal),
        product ? Promise.resolve(nextEffective) : api.get<WorkflowBinding>(`/content-personas/${nextUnit.persona_id}/default-workflows/${nextUnit.modality}`, controller.signal),
      ]);
      setRole(me.role); setProject(nextProject); setUnit(nextUnit); setPersona(personas.find((item) => item.id === nextUnit.persona_id) || null);
      setBinding(nextBinding); setDefaultBinding(nextDefault); setDefinition(structuredClone(nextEffective.workflow_id ? nextEffective.definition : EMPTY));
      savedWorkflowStamp.current = workflowStamp(nextBinding, nextEffective, nextDefault);
      savedEffectiveWorkflow.current = nextEffective;
      setWorkflowConflict("");
      setPlugins(nextPlugins); setExecutionOptions(nextExecutors.ai); setRuns(nextRuns); setAssets(nextAssets); setOutputs(nextOutputs);
      setDataCapabilities(nextCapabilities);
      if (nextRuns[0]) setRun(await api.get<Run>(`${base}/runs/${nextRuns[0].id}`, controller.signal));
    }).catch((err) => { if (!controller.signal.aborted) setError(problem(err)); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [projectId, unitId]);

  useEffect(() => {
    if (!unit) return;
    const personaBrand = persona?.brand_id;
    Promise.all([
      personaBrand ? api.get<{ name: string }>(`/content-brands/${personaBrand}`) : Promise.resolve(null),
      unit.account_id ? api.get<{ name: string }>(`/content-accounts/${unit.account_id}`) : Promise.resolve(null),
      unit.series_id ? api.get<{ name: string }>(`/content-series/${unit.series_id}`) : Promise.resolve(null),
    ]).then(([brand, account, series]) => { setBrandName(brand?.name || null); setAccountName(account?.name || null); setSeriesName(series?.name || null); }).catch((err) => setError(problem(err)));
  }, [unit?.id, persona?.brand_id]);
  const displayedSnapshotId = unit?.production_domain === "product" ? null : !design && run ? run.identity_snapshot_id : unit?.identity_snapshot_id;
  useEffect(() => {
    setSnapshot(null);
    if (!displayedSnapshotId) return;
    let active = true;
    api.get<IdentitySnapshot>(`/identity-snapshots/${displayedSnapshotId}`).then((value) => { if (active) setSnapshot(value); }).catch((err) => { if (active) setError(problem(err)); });
    return () => { active = false; };
  }, [displayedSnapshotId]);

  // 检查器只跟随「选中节点 + 内容签名」重置：轮询每 3 秒产生新的 run/definition
  // 对象引用，若直接依赖引用会持续覆盖用户正在输入的检查器文本
  const canvasRef = useRef(canvasDefinition);
  canvasRef.current = canvasDefinition;
  const nodeSignature = useMemo(() => {
    const node = canvasDefinition.nodes.find((item) => item.id === selected);
    return JSON.stringify([node?.config, node?.input_mapping, node?.output_mapping, node?.condition,
      canvasDefinition.edges.filter((edge) => edge.to === selected).map((edge) => edge.from)]);
  }, [canvasDefinition, selected]);
  useEffect(() => {
    const canvas = canvasRef.current;
    const node = canvas.nodes.find((item) => item.id === selected);
    setConfigText(pretty(node?.config)); setInputText(pretty(node?.input_mapping)); setOutputText(pretty(node?.output_mapping)); setConditionText(pretty(node?.condition));
    setDepsText(canvas.edges.filter((edge) => edge.to === selected).map((edge) => edge.from).join(", "));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selected, nodeSignature]);

  // attempts 只在所选节点的 attempt_no/status 实际变化时重拉，不跟随轮询的新数组引用
  const selectedStepKey = !design && run && selected
    ? `${run.steps.find((step) => step.node_id === selected)?.attempt_no ?? "-"}:${run.steps.find((step) => step.node_id === selected)?.status ?? "-"}`
    : null;
  useEffect(() => {
    if (!run || !selected) { setAttempts([]); return; }
    api.get<Attempt[]>(`${base}/runs/${run.id}/nodes/${selected}/attempts`).then(setAttempts).catch(() => setAttempts([]));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [base, run?.id, selected, selectedStepKey]);

  useEffect(() => {
    if (!run || !(["running", "waiting_input"] as string[]).includes(run.status)) return;
    let polls = 0;
    const timer = window.setInterval(() => {
      // 页面不可见时暂停轮询，回到前台自动恢复
      if (document.visibilityState === "hidden") return;
      // 200 次×3s=10 分钟，覆盖最长合法执行（媒体 305s/轮询等待 420s）；更久的由后端回收
      if (++polls > 200) { window.clearInterval(timer); return; }
      api.get<Run>(`${base}/runs/${run.id}`).then(setRun).catch((err) => { setError(problem(err)); window.clearInterval(timer); });
    }, 3000);
    return () => window.clearInterval(timer);
  }, [base, run?.id, run?.status]);

  async function refreshWorkflowFromRecipe(discardDraft = false) {
    if (!unit) return;
    const refresh = ++workflowRefresh.current;
    const draft = liveWorkflow.current;
    try {
      const nextUnit = await api.get<Unit>(base);
      const [nextBinding, nextEffective, nextDefault] = await Promise.all([
        api.get<WorkflowBinding>(`${base}/workflow-override`),
        api.get<WorkflowBinding>(`${base}/effective-workflow`),
        nextUnit.production_domain === "product" ? api.get<WorkflowBinding>(`${base}/effective-workflow`) : api.get<WorkflowBinding>(`/content-personas/${nextUnit.persona_id}/default-workflows/${nextUnit.modality}`),
      ]);
      if (refresh !== workflowRefresh.current || liveWorkflow.current.base !== base) return;
      const stamp = workflowStamp(nextBinding, nextEffective, nextDefault);
      if (!discardDraft && stamp === savedWorkflowStamp.current) return;
      const current = liveWorkflow.current;
      const changedWhileReading = current.definition !== draft.definition || current.configText !== draft.configText
        || current.inputText !== draft.inputText || current.outputText !== draft.outputText
        || current.conditionText !== draft.conditionText || current.depsText !== draft.depsText;
      if (current.busy || current.dirty && !discardDraft || discardDraft && changedWhileReading) {
        setWorkflowConflict("已保存的流程版本已更新；高级工作流的未保存草稿已保留，未自动覆盖。请先核对冲突，或明确放弃高级流程草稿后载入已保存版本。");
        return;
      }
      setBinding(nextBinding); setDefaultBinding(nextDefault);
      setDefinition(structuredClone(nextEffective.workflow_id ? nextEffective.definition : EMPTY));
      setUnit(nextUnit);
      setSelected(value => value && nextEffective.definition.nodes.some(node => node.id === value) ? value : null);
      setDirty(false); setWorkflowConflict(""); savedWorkflowStamp.current = stamp;
      savedEffectiveWorkflow.current = nextEffective;
    } catch (cause) {
      if (refresh === workflowRefresh.current && liveWorkflow.current.base === base) setWorkflowConflict("已保存流程的最新版本暂时无法回读。高级工作流草稿保持原样，请重试流程同步后再保存。");
      throw cause;
    }
  }

  function change(next: Definition) {
    if (readOnly) return;
    liveWorkflow.current = { ...liveWorkflow.current, dirty: true, definition: next };
    setDefinition(next); setDirty(true); setNotice("");
  }
  function editNode(patch: Partial<WorkflowNode>) {
    if (!selected) return;
    change({ ...definition, nodes: definition.nodes.map((node) => node.id === selected ? { ...node, ...patch } : node) });
  }
  function addNode() {
    const id = `${newKind.toLowerCase()}_${crypto.randomUUID().slice(0, 8)}`;
    const config = newKind === "System" ? { value: {} } : newKind === "Data" ? { data_source_plugin_key: "studio.source", source_ref: "" } : {};
    change({ ...definition, nodes: [...definition.nodes, { id, kind: newKind, plugin: DEFAULT_PLUGINS[newKind], label: `${newKind} 节点`, config }], visual_order: [...definition.visual_order, id] });
    setSelected(id);
  }
  function removeNode() {
    if (!selected) return;
    change({ nodes: definition.nodes.filter((node) => node.id !== selected), edges: definition.edges.filter((edge) => edge.from !== selected && edge.to !== selected), visual_order: definition.visual_order.filter((id) => id !== selected) });
    setSelected(null);
  }
  function moveNode(nodeId: string, targetId: string) {
    if (nodeId === targetId) return;
    const next = definition.visual_order.filter((id) => id !== nodeId);
    next.splice(next.indexOf(targetId), 0, nodeId);
    change({ ...definition, visual_order: next });
  }
  function moveBy(nodeId: string, offset: number) {
    const from = definition.visual_order.indexOf(nodeId);
    const to = from + offset;
    if (to < 0 || to >= definition.visual_order.length) return;
    const next = [...definition.visual_order]; [next[from], next[to]] = [next[to], next[from]];
    change({ ...definition, visual_order: next });
  }
  function parseObject(value: string, label: string): Record<string, unknown> {
    const parsed: unknown = JSON.parse(value);
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) throw new Error(`${label}必须是 JSON 对象`);
    return parsed as Record<string, unknown>;
  }
  function applyInspector() {
    try {
      const config = parseObject(configText, "配置"); const input_mapping = parseObject(inputText, "输入映射"); const output_mapping = parseObject(outputText, "输出映射"); const condition = parseObject(conditionText, "条件");
      const sources = depsText.split(",").map((item) => item.trim()).filter(Boolean);
      change({ ...definition, nodes: definition.nodes.map((node) => node.id === selected ? { ...node, config, input_mapping, output_mapping, condition } : node), edges: [...definition.edges.filter((edge) => edge.to !== selected), ...sources.map((from) => ({ from, to: selected! }))] });
      setError("");
    }
    catch (err) { setError(err instanceof Error ? err.message : "JSON 无效"); }
  }
  async function saveOverride() {
    if (!binding) return;
    if (readOnly) { setError("已归档单元只可查看历史。" ); return; }
    if (workflowConflict) { setError("流程版本有冲突，请先核对并同步；高级草稿仍保留。" ); return; }
    setBusy(true); setError("");
    try {
      const saved = await api.post<WorkflowBinding>(`${base}/workflow-override`, { expected_revision: binding.revision, definition });
      setBinding(saved); setUnit((current) => current ? { ...current, pinned_workflow_id: saved.workflow_id } : current); setDirty(false); setNotice(`项目覆盖已保存为 v${saved.workflow_version}。`);
      if (defaultBinding) savedWorkflowStamp.current = workflowStamp(saved, saved, defaultBinding);
      savedEffectiveWorkflow.current = saved;
      setWorkflowRevision(value => value + 1);
    } catch (err) { setError(problem(err)); } finally { setBusy(false); }
  }
  async function saveDefault() {
    if (unit?.production_domain === "product") return;
    if (readOnly) { setError("已归档单元只可查看历史。" ); return; }
    if (workflowConflict) { setError("流程版本有冲突，请先核对并同步；高级草稿仍保留。" ); return; }
    if (!unit || !defaultBinding || !window.confirm(`将当前流程另存为「${persona?.name || "当前身份"} × ${unit.modality}」的新默认版本？现有内容单元不会自动改绑。`)) return;
    setBusy(true); setError("");
    try {
      const saved = await api.post<WorkflowBinding>(`/content-personas/${unit.persona_id}/default-workflows/${unit.modality}`, { expected_revision: defaultBinding.revision, definition, source_project_id: projectId, source_unit_id: unitId });
      setDefaultBinding(saved); setNotice(`角色默认已另存为 v${saved.workflow_version}；当前单元绑定保持不变。`);
      savedWorkflowStamp.current = binding && savedEffectiveWorkflow.current ? workflowStamp(binding, savedEffectiveWorkflow.current, saved) : null;
      setWorkflowRevision(value => value + 1);
    } catch (err) { setError(problem(err)); } finally { setBusy(false); }
  }
  const needsProductContext = unit?.production_domain === "product" && !!(unit.identity_snapshot_id || run?.identity_snapshot_id) && !["product_default", "project_override"].includes(defaultBinding?.source || "");
  async function continueProduct() {
    if (readOnly || busy) return;
    setBusy(true); setError("");
    try {
      const nextUnit = await api.post<Unit>(`${base}/product-context`);
      setUnit(nextUnit);
      setBusy(false);
      liveWorkflow.current = { ...liveWorkflow.current, busy: false };
      await refreshWorkflowFromRecipe();
      setWorkflowRevision(value => value + 1);
      setNotice("已切换为独立商品配置；历史运行与身份快照保留。");
    } catch (err) { setError(problem(err)); } finally { setBusy(false); }
  }
  async function startRun() {
    if (needsProductContext) { setError("请先按商品流程继续，再准备新的运行。"); return; }
    if (readOnly) { setError("已归档单元只可查看历史。" ); return; }
    if (workflowConflict) { setError("请先解决流程版本冲突，再准备运行。" ); return; }
    if (dirty) { setError("请先保存项目覆盖，再运行。" ); return; }
    setBusy(true); setError("");
    try { const started = await api.post<Run>(`${base}/runs`, { params: runSourceRef.trim() ? { source_ref: runSourceRef.trim() } : {} }); setRun(started); setRuns([{ id: started.id, status: started.status }, ...runs]); setOutputs(await api.get<UnitOutput[]>(`${base}/outputs`)); setAssets(await api.get<SharedAsset[]>(`/content-projects/${projectId}/shared-assets`)); setNotice(`Run #${started.id} 已真实执行并保存。`); }
    catch (err) { setError(problem(err)); } finally { setBusy(false); }
  }
  async function runAction(action: "rerun" | "rerun-from-here" | "complete", payload: Record<string, unknown> = {}) {
    if (readOnly) { setError("已归档单元只可查看历史。" ); return; }
    if (!run || !selected) return;
    setBusy(true); setError("");
    try { const updated = await api.post<Run>(`${base}/runs/${run.id}/nodes/${selected}/${action}`, action === "complete" ? { payload } : undefined); setRun(updated); setOutputs(await api.get<UnitOutput[]>(`${base}/outputs`)); setAssets(await api.get<SharedAsset[]>(`/content-projects/${projectId}/shared-assets`)); setNotice(`节点 ${selected} 已由后端处理。`); }
    catch (err) { setError(problem(err)); } finally { setBusy(false); }
  }

  return { readOnly, base, project, unit, persona, brandName, accountName, seriesName, snapshot, binding, defaultBinding, definition, dirty, design, setDesign, selected, setSelected, runs, run, setRun, attempts, plugins, dataCapabilities, executionOptions, assets, outputs, assetsOpen, setAssetsOpen, loading, busy, error, setError, notice, workflowConflict, workflowRevision, refreshWorkflowFromRecipe, configText, setConfigText, inputText, setInputText, outputText, setOutputText, conditionText, setConditionText, depsText, setDepsText, dragging, setDragging, newKind, setNewKind, runSourceRef, setRunSourceRef, canvasDefinition, selectedNode, selectedStep, sourcePlugin, sourceCapability, executor, change, editNode, addNode, removeNode, moveNode, moveBy, applyInspector, saveOverride, saveDefault, continueProduct, needsProductContext, startRun, runAction };
}
