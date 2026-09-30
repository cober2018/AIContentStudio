import { useEffect, useMemo, useState } from "react";
import { api, ApiError } from "../api";
import type { Definition, Persona, Project, SharedAsset, Unit, WorkflowBinding, WorkflowNode } from "./project/projectTypes";

export type Step = { id: number; node_id: string; node_type: string; label: string; status: string; params: Record<string, unknown>; output: Record<string, unknown>; error: string | null; stale_reason: string | null; attempt_no: number };
export type Run = { id: number; status: string; workflow_id: number; workflow_version: number | null; definition_checksum: string | null; identity_snapshot_id: number | null; identity_state: string; definition: Definition; steps: Step[]; error: string | null };
export type IdentitySnapshot = { id: number; brand_id: number | null; persona_id: number; account_id: number | null; series_id: number | null; revision_ids?: Record<string, number | null>; brand_revision_id: number | null; persona_revision_id: number | null; account_revision_id: number | null; series_revision_id: number | null; brand_voice_version_id: number | null; effective_profile: Record<string, unknown>; field_origins: Record<string, string>; checksum: string };
export type Attempt = { attempt_no: number; status: string; input_hash: string | null; output_hash: string | null; output_json: Record<string, unknown>; error: string | null };
export type DataPlugin = { key: string; name: string; category: string; available: boolean; reason: string | null; config_schema: Record<string, unknown> };
export type DataCapability = { id: number; key: string; version: string; plugin_key: string; source_ref: string; executable: boolean; verified: boolean };
export type ExecutionOption = { provider: string; model: string; available: boolean; reason: string | null };
export type UnitOutput = { id: number; output_kind: "draft" | "candidate" | "material_revision" | "content_master_revision"; entity_id: number; run_id: number; node_id: string; attempt_id: number | null; provenance: Record<string, unknown> };

export const KINDS: WorkflowNode["kind"][] = ["Data", "AI", "Tool", "Rule", "Human", "System"];
const DEFAULT_PLUGINS: Record<WorkflowNode["kind"], string> = {
  Data: "data.source", AI: "builtin.generate", Tool: "builtin.export", Rule: "builtin.fact_check", Human: "builtin.approve", System: "system.constant",
};
export const PLUGIN_CHOICES: Record<WorkflowNode["kind"], string[]> = {
  Data: ["data.source"],
  AI: ["builtin.generate", "builtin.humanize", "builtin.generate_cover", "node.skill"],
  Tool: ["builtin.connector_pull", "builtin.extract_facts", "builtin.factpack_freeze", "builtin.topic_suggest", "builtin.export"],
  Rule: ["builtin.fact_check", "builtin.content_censor", "builtin.discoverability_post"],
  Human: ["builtin.approve", "builtin.confirm_facts", "builtin.adopt_topic"],
  System: ["system.constant"],
};
export const MODALITY_NAMES: Record<string, string> = { text: "文字生产", graphic: "图文生产", video: "视频生产" };
const EMPTY: Definition = { nodes: [], edges: [], visual_order: [] };

export function problem(error: unknown) { return error instanceof ApiError ? `${error.status} · ${error.message}` : "请求失败，请检查后端服务。"; }
export function pretty(value: unknown) { return JSON.stringify(value ?? {}, null, 2); }

export function useProductionWorkflow(projectId: number, unitId: number) {
  const base = `/content-projects/${projectId}/units/${unitId}`;
  const [project, setProject] = useState<Project | null>(null);
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
  const readOnly = project?.status === "archived" || unit?.status === "archived";

  useEffect(() => {
    setLoading(true);
    Promise.all([
      api.get<Project>(`/content-projects/${projectId}`),
      api.get<Unit>(base),
      api.get<Persona[]>("/content-personas"),
      api.get<WorkflowBinding>(`${base}/workflow-override`),
      api.get<WorkflowBinding>(`${base}/effective-workflow`),
      api.get<DataPlugin[]>("/data-source-plugins"),
      api.get<{ ai: Record<string, ExecutionOption> }>("/workflow-execution-options"),
      api.get<{ id: number; status: string }[]>(`${base}/runs`),
      api.get<SharedAsset[]>(`/content-projects/${projectId}/shared-assets`),
      api.get<UnitOutput[]>(`${base}/outputs`),
      api.get<DataCapability[]>("/data-source-capabilities"),
    ]).then(async ([nextProject, nextUnit, personas, nextBinding, nextEffective, nextPlugins, nextExecutors, nextRuns, nextAssets, nextOutputs, nextCapabilities]) => {
      const nextDefault = await api.get<WorkflowBinding>(`/content-personas/${nextUnit.persona_id}/default-workflows/${nextUnit.modality}`);
      setProject(nextProject); setUnit(nextUnit); setPersona(personas.find((item) => item.id === nextUnit.persona_id) || null);
      setBinding(nextBinding); setDefaultBinding(nextDefault); setDefinition(structuredClone(nextEffective.workflow_id ? nextEffective.definition : EMPTY));
      setPlugins(nextPlugins); setExecutionOptions(nextExecutors.ai); setRuns(nextRuns); setAssets(nextAssets); setOutputs(nextOutputs);
      setDataCapabilities(nextCapabilities);
      if (nextRuns[0]) setRun(await api.get<Run>(`${base}/runs/${nextRuns[0].id}`));
    }).catch((err) => setError(problem(err))).finally(() => setLoading(false));
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
  const displayedSnapshotId = !design && run ? run.identity_snapshot_id : unit?.identity_snapshot_id;
  useEffect(() => {
    setSnapshot(null);
    if (!displayedSnapshotId) return;
    let active = true;
    api.get<IdentitySnapshot>(`/identity-snapshots/${displayedSnapshotId}`).then((value) => { if (active) setSnapshot(value); }).catch((err) => { if (active) setError(problem(err)); });
    return () => { active = false; };
  }, [displayedSnapshotId]);

  useEffect(() => {
    const node = canvasDefinition.nodes.find((item) => item.id === selected);
    setConfigText(pretty(node?.config)); setInputText(pretty(node?.input_mapping)); setOutputText(pretty(node?.output_mapping)); setConditionText(pretty(node?.condition));
    setDepsText(canvasDefinition.edges.filter((edge) => edge.to === selected).map((edge) => edge.from).join(", "));
  }, [selected, canvasDefinition]);

  useEffect(() => {
    if (!run || !selected) { setAttempts([]); return; }
    api.get<Attempt[]>(`${base}/runs/${run.id}/nodes/${selected}/attempts`).then(setAttempts).catch(() => setAttempts([]));
  }, [run?.id, run?.steps, selected]);

  useEffect(() => {
    if (!run || !(["running", "waiting_input"] as string[]).includes(run.status)) return;
    let polls = 0;
    const timer = window.setInterval(() => {
      if (++polls > 20) { window.clearInterval(timer); return; }
      api.get<Run>(`${base}/runs/${run.id}`).then(setRun).catch((err) => { setError(problem(err)); window.clearInterval(timer); });
    }, 3000);
    return () => window.clearInterval(timer);
  }, [base, run?.id, run?.status]);

  function change(next: Definition) { if (readOnly) return; setDefinition(next); setDirty(true); setNotice(""); }
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
    setBusy(true); setError("");
    try {
      const saved = await api.post<WorkflowBinding>(`${base}/workflow-override`, { expected_revision: binding.revision, definition });
      setBinding(saved); setUnit((current) => current ? { ...current, pinned_workflow_id: saved.workflow_id } : current); setDirty(false); setNotice(`项目覆盖已保存为 v${saved.workflow_version}。`);
    } catch (err) { setError(problem(err)); } finally { setBusy(false); }
  }
  async function saveDefault() {
    if (readOnly) { setError("已归档单元只可查看历史。" ); return; }
    if (!unit || !defaultBinding || !window.confirm(`将当前流程另存为「${persona?.name || "当前身份"} × ${unit.modality}」的新默认版本？现有内容单元不会自动改绑。`)) return;
    setBusy(true); setError("");
    try {
      const saved = await api.post<WorkflowBinding>(`/content-personas/${unit.persona_id}/default-workflows/${unit.modality}`, { expected_revision: defaultBinding.revision, definition, source_project_id: projectId, source_unit_id: unitId });
      setDefaultBinding(saved); setNotice(`角色默认已另存为 v${saved.workflow_version}；当前单元绑定保持不变。`);
    } catch (err) { setError(problem(err)); } finally { setBusy(false); }
  }
  async function startRun() {
    if (readOnly) { setError("已归档单元只可查看历史。" ); return; }
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

  return { readOnly, base, project, unit, persona, brandName, accountName, seriesName, snapshot, binding, defaultBinding, definition, dirty, design, setDesign, selected, setSelected, runs, run, setRun, attempts, plugins, dataCapabilities, executionOptions, assets, outputs, assetsOpen, setAssetsOpen, loading, busy, error, setError, notice, configText, setConfigText, inputText, setInputText, outputText, setOutputText, conditionText, setConditionText, depsText, setDepsText, dragging, setDragging, newKind, setNewKind, runSourceRef, setRunSourceRef, canvasDefinition, selectedNode, selectedStep, sourcePlugin, sourceCapability, executor, change, editNode, addNode, removeNode, moveNode, moveBy, applyInspector, saveOverride, saveDefault, startRun, runAction };
}
