import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api, ApiError } from "../api";
import { Button, Drawer, EmptyState, ErrorBanner, Field, Spinner, StatusBadge, inputClass } from "../components/ui";
import type { Definition, Persona, Project, SharedAsset, Unit, WorkflowBinding, WorkflowNode } from "./PersistentProjectPages";

type Step = { id: number; node_id: string; node_type: string; label: string; status: string; params: Record<string, unknown>; output: Record<string, unknown>; error: string | null; stale_reason: string | null; attempt_no: number };
type Run = { id: number; status: string; workflow_id: number; workflow_version: number | null; definition_checksum: string | null; definition: Definition; steps: Step[]; error: string | null };
type Attempt = { attempt_no: number; status: string; input_hash: string | null; output_hash: string | null; output_json: Record<string, unknown>; error: string | null };
type DataPlugin = { key: string; name: string; category: string; available: boolean; reason: string | null; config_schema: Record<string, unknown> };
type ExecutionOption = { provider: string; model: string; available: boolean; reason: string | null };
type UnitOutput = { id: number; output_kind: "draft" | "candidate" | "material_revision"; entity_id: number; run_id: number; node_id: string; attempt_id: number | null; provenance: Record<string, unknown> };

const KINDS: WorkflowNode["kind"][] = ["Data", "AI", "Tool", "Rule", "Human", "System"];
const DEFAULT_PLUGINS: Record<WorkflowNode["kind"], string> = {
  Data: "data.source", AI: "builtin.generate", Tool: "builtin.export", Rule: "builtin.fact_check", Human: "builtin.approve", System: "system.constant",
};
const PLUGIN_CHOICES: Record<WorkflowNode["kind"], string[]> = {
  Data: ["data.source"],
  AI: ["builtin.generate", "builtin.humanize", "builtin.generate_cover", "node.skill"],
  Tool: ["builtin.connector_pull", "builtin.extract_facts", "builtin.factpack_freeze", "builtin.topic_suggest", "builtin.export"],
  Rule: ["builtin.fact_check", "builtin.content_censor", "builtin.discoverability_post"],
  Human: ["builtin.approve", "builtin.confirm_facts", "builtin.adopt_topic"],
  System: ["system.constant"],
};
const MODALITY_NAMES: Record<string, string> = { text: "文字生产", graphic: "图文生产", video: "视频生产" };
const EMPTY: Definition = { nodes: [], edges: [], visual_order: [] };

function problem(error: unknown) { return error instanceof ApiError ? `${error.status} · ${error.message}` : "请求失败，请检查后端服务。"; }
function pretty(value: unknown) { return JSON.stringify(value ?? {}, null, 2); }

export function ProductionDesigner({ projectId, unitId }: { projectId: number; unitId: number }) {
  const base = `/content-projects/${projectId}/units/${unitId}`;
  const [project, setProject] = useState<Project | null>(null);
  const [unit, setUnit] = useState<Unit | null>(null);
  const [persona, setPersona] = useState<Persona | null>(null);
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
  const sourcePlugin = plugins.find((item) => item.key === selectedNode?.config.data_source_plugin_key);
  const executor = selectedNode?.kind === "AI" ? executionOptions[selectedNode.plugin] : null;

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
    ]).then(async ([nextProject, nextUnit, personas, nextBinding, nextEffective, nextPlugins, nextExecutors, nextRuns, nextAssets, nextOutputs]) => {
      const nextDefault = await api.get<WorkflowBinding>(`/content-personas/${nextUnit.persona_id}/default-workflows/${nextUnit.modality}`);
      setProject(nextProject); setUnit(nextUnit); setPersona(personas.find((item) => item.id === nextUnit.persona_id) || null);
      setBinding(nextBinding); setDefaultBinding(nextDefault); setDefinition(structuredClone(nextEffective.workflow_id ? nextEffective.definition : EMPTY));
      setPlugins(nextPlugins); setExecutionOptions(nextExecutors.ai); setRuns(nextRuns); setAssets(nextAssets); setOutputs(nextOutputs);
      if (nextRuns[0]) setRun(await api.get<Run>(`${base}/runs/${nextRuns[0].id}`));
    }).catch((err) => setError(problem(err))).finally(() => setLoading(false));
  }, [projectId, unitId]);

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

  function change(next: Definition) { setDefinition(next); setDirty(true); setNotice(""); }
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
    if (unit?.status === "archived") { setError("已归档单元只可查看历史。" ); return; }
    setBusy(true); setError("");
    try {
      const saved = await api.post<WorkflowBinding>(`${base}/workflow-override`, { expected_revision: binding.revision, definition });
      setBinding(saved); setUnit((current) => current ? { ...current, pinned_workflow_id: saved.workflow_id } : current); setDirty(false); setNotice(`项目覆盖已保存为 v${saved.workflow_version}。`);
    } catch (err) { setError(problem(err)); } finally { setBusy(false); }
  }
  async function saveDefault() {
    if (unit?.status === "archived") { setError("已归档单元只可查看历史。" ); return; }
    if (!unit || !defaultBinding || !window.confirm(`将当前流程另存为「${persona?.name || "当前身份"} × ${unit.modality}」的新默认版本？现有内容单元不会自动改绑。`)) return;
    setBusy(true); setError("");
    try {
      const saved = await api.post<WorkflowBinding>(`/content-personas/${unit.persona_id}/default-workflows/${unit.modality}`, { expected_revision: defaultBinding.revision, definition, source_project_id: projectId, source_unit_id: unitId });
      setDefaultBinding(saved); setNotice(`角色默认已另存为 v${saved.workflow_version}；当前单元绑定保持不变。`);
    } catch (err) { setError(problem(err)); } finally { setBusy(false); }
  }
  async function startRun() {
    if (unit?.status === "archived") { setError("已归档单元只可查看历史。" ); return; }
    if (dirty) { setError("请先保存项目覆盖，再运行。" ); return; }
    setBusy(true); setError("");
    try { const started = await api.post<Run>(`${base}/runs`, { params: runSourceRef.trim() ? { source_ref: runSourceRef.trim() } : {} }); setRun(started); setRuns([{ id: started.id, status: started.status }, ...runs]); setOutputs(await api.get<UnitOutput[]>(`${base}/outputs`)); setAssets(await api.get<SharedAsset[]>(`/content-projects/${projectId}/shared-assets`)); setNotice(`Run #${started.id} 已真实执行并保存。`); }
    catch (err) { setError(problem(err)); } finally { setBusy(false); }
  }
  async function runAction(action: "rerun" | "rerun-from-here" | "complete", payload: Record<string, unknown> = {}) {
    if (unit?.status === "archived") { setError("已归档单元只可查看历史。" ); return; }
    if (!run || !selected) return;
    setBusy(true); setError("");
    try { const updated = await api.post<Run>(`${base}/runs/${run.id}/nodes/${selected}/${action}`, action === "complete" ? { payload } : undefined); setRun(updated); setOutputs(await api.get<UnitOutput[]>(`${base}/outputs`)); setAssets(await api.get<SharedAsset[]>(`/content-projects/${projectId}/shared-assets`)); setNotice(`节点 ${selected} 已由后端处理。`); }
    catch (err) { setError(problem(err)); } finally { setBusy(false); }
  }

  if (loading) return <div className="p-9"><Spinner label="加载生产工作台…" /></div>;
  if (!project || !unit) return <div className="p-9"><ErrorBanner message={error || "内容单元不存在或无权访问。"} /></div>;
  return <div className="mx-auto max-w-7xl px-6 py-9">
    <Link to={`/projects/${project.id}?tab=matrix`} className="text-sm text-slate-500">← {project.title} / 内容矩阵</Link>
    <div className="mt-5 mb-5 flex flex-wrap items-start justify-between gap-4"><div><p className="text-xs font-semibold uppercase tracking-widest text-indigo-600">{MODALITY_NAMES[unit.modality] || "生产工作台"}</p><h1 className="mt-2 text-3xl font-semibold">{unit.title}</h1><p className="mt-2 text-sm text-slate-500">{persona?.name || `身份 #${unit.persona_id}`} · {unit.channel_id || "未选渠道"} · 固定工作流 #{unit.pinned_workflow_id || "未设置"}</p></div><Button variant="secondary" onClick={() => setAssetsOpen(!assetsOpen)}>项目共享素材 · {assets.length}</Button></div>
    {unit.status === "archived" && <p className="mb-4 rounded-lg bg-amber-50 px-4 py-3 text-sm text-amber-800">此内容单元已归档，仅供查看历史运行、尝试和产物；不能保存或重新执行。</p>}
    {error && <div className="mb-4"><ErrorBanner message={error} /></div>}{notice && <p className="mb-4 rounded-lg bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{notice}</p>}
    {assetsOpen && <Drawer title="项目共享素材（仅真实版本）" onClose={() => setAssetsOpen(false)}>{assets.length ? <ul className="space-y-3 text-sm">{assets.map((asset) => <li key={asset.id} className="rounded-lg border border-slate-200 p-3">Revision #{asset.material_revision_id} · {asset.kind || "素材"} · Run #{asset.run_id} / {asset.node_id} · {asset.rights_status || "权利待核对"}</li>)}</ul> : <p className="text-sm text-slate-500">暂无关联素材。</p>}</Drawer>}
    <ModalityShell modality={unit.modality} outputs={outputs} assets={assets.filter((asset) => asset.unit_id === unit.id)} />
    {selectedNode?.kind === "AI" && <section className="mb-5 rounded-xl border border-slate-200 bg-white p-4 text-sm"><h2 className="font-semibold">AI 节点执行路由 · {selectedNode.id}</h2><p className={`mt-2 text-xs ${executor?.available ? "text-emerald-700" : "text-amber-700"}`}>{executor?.available ? "后端当前路由可用" : `不可执行：${executor?.reason || "尚无已验证执行器"}`}。这里只能绑定后端实际配置的组合；运行前会再次校验。</p>{design && executor?.available && <div className="mt-3 grid gap-3 sm:grid-cols-2"><Field label="Provider"><select className={inputClass} value={String(selectedNode.config.provider || "")} onChange={(event) => editNode({ config: { ...selectedNode.config, provider: event.target.value || undefined } })}><option value="">沿用当前路由</option><option value={executor.provider}>{executor.provider}</option></select></Field><Field label="Model"><select className={inputClass} value={String(selectedNode.config.model || "")} onChange={(event) => editNode({ config: { ...selectedNode.config, model: event.target.value || undefined } })}><option value="">沿用当前路由</option><option value={executor.model}>{executor.model}</option></select></Field></div>}</section>}
    <div className="mb-5 flex flex-wrap items-center gap-2 rounded-xl border border-slate-200 bg-white p-4"><Button variant={design ? "secondary" : "primary"} onClick={() => { setDesign(!design); setSelected(null); }}>{design ? "退出设计模式" : "进入设计模式"}</Button><Button disabled={busy || !dirty} onClick={saveOverride}>保存项目覆盖</Button><Button variant="secondary" disabled={busy || definition.nodes.length === 0} onClick={saveDefault}>另存为角色默认新版本</Button>{definition.nodes.some((node) => node.kind === "Data") && <input aria-label="运行时来源 ID" className={`${inputClass} max-w-40`} placeholder="来源 ID（角色默认）" value={runSourceRef} onChange={(event) => setRunSourceRef(event.target.value)} />}<Button disabled={busy || dirty || !unit.pinned_workflow_id} onClick={startRun}>启动真实 Run</Button><span className={`text-xs ${dirty ? "text-amber-700" : "text-slate-500"}`}>{dirty ? "有未保存修改" : `项目修订 ${binding?.revision || 0} · 角色默认修订 ${defaultBinding?.revision || 0}`}</span></div>
    <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_360px]"><section className="rounded-2xl border border-slate-200 bg-white p-5"><div className="mb-4 flex items-center justify-between"><h2 className="font-semibold">单条流程小画布</h2><span className="text-xs text-slate-500">{!design && run ? `历史 Run #${run.id} · ${run.definition_checksum?.slice(0, 12) || "未知定义"}` : "项目工作流草稿"} · 顺序与依赖独立 · {canvasDefinition.nodes.length} 节点</span></div>
      {design && <div className="mb-4 flex flex-wrap gap-2"><select aria-label="新增节点类型" className={inputClass} value={newKind} onChange={(event) => setNewKind(event.target.value as WorkflowNode["kind"])}>{KINDS.map((kind) => <option key={kind}>{kind}</option>)}</select><Button onClick={addNode}>新增节点</Button></div>}
      {canvasDefinition.visual_order.length ? <div className="space-y-3">{canvasDefinition.visual_order.map((id, index) => { const node = canvasDefinition.nodes.find((item) => item.id === id); if (!node) return null; const step = !design ? run?.steps.find((item) => item.node_id === id) : null; return <article key={id} draggable={design} onDragStart={() => setDragging(id)} onDragOver={(event) => { if (design) event.preventDefault(); }} onDrop={() => { if (dragging) moveNode(dragging, id); setDragging(null); }} className={`rounded-xl border p-4 ${selected === id ? "border-indigo-400 bg-indigo-50" : "border-slate-200"}`}><div className="flex flex-wrap items-center justify-between gap-3"><button className="text-left" onClick={() => setSelected(id)}><span className="text-xs text-slate-500">{index + 1} · {node.kind}</span><p className="font-medium">{node.label || id}</p><p className="text-xs text-slate-500">{node.plugin}</p></button><div className="flex items-center gap-2">{step ? <StatusBadge status={step.status} /> : <span className="text-xs text-slate-400">未运行</span>}{design && <><button title="上移" aria-label={`${id} 上移`} onClick={() => moveBy(id, -1)} className="px-2 text-sm">↑</button><button title="下移" aria-label={`${id} 下移`} onClick={() => moveBy(id, 1)} className="px-2 text-sm">↓</button></>}</div></div></article>; })}</div> : <EmptyState title="还没有流程节点" hint="进入设计模式，添加 Data、AI、Tool、Rule、Human 或 System 节点。" />}
      <p className="mt-4 text-xs text-slate-500">依赖边：{canvasDefinition.edges.map((edge) => `${edge.from} → ${edge.to}`).join("；") || "无"}。拖拽只调整视觉顺序，不修改依赖。</p>
    </section><aside className="space-y-5"><section className="rounded-2xl border border-slate-200 bg-white p-5"><h2 className="font-semibold">节点 Inspector</h2>{!selectedNode ? <p className="mt-3 text-sm text-slate-500">选择一个节点查看配置、输入、输出与执行历史。</p> : <div className="mt-4 space-y-3"><p className="text-xs text-slate-500">{selectedNode.id} · {selectedNode.kind}</p>{design && <><Field label="节点名称"><input className={inputClass} value={selectedNode.label || ""} onChange={(event) => editNode({ label: event.target.value })} /></Field><Field label="执行插件"><select className={inputClass} value={selectedNode.plugin} onChange={(event) => editNode({ plugin: event.target.value })}>{PLUGIN_CHOICES[selectedNode.kind].map((plugin) => <option key={plugin}>{plugin}</option>)}</select></Field>{selectedNode.kind === "Data" && <Field label="数据来源插件"><select className={inputClass} value={String(selectedNode.config.data_source_plugin_key || "studio.source")} onChange={(event) => editNode({ config: { ...selectedNode.config, data_source_plugin_key: event.target.value } })}>{plugins.map((plugin) => <option key={plugin.key} value={plugin.key}>{plugin.name}{plugin.available ? "" : " · 未连接"}</option>)}</select></Field>}{selectedNode.kind === "Data" && sourcePlugin && <p className={`text-xs ${sourcePlugin.available ? "text-emerald-700" : "text-amber-700"}`}>{sourcePlugin.available ? "已验证只读执行" : `不可执行：${sourcePlugin.reason}`}</p>}<Field label="节点配置 JSON"><textarea className={inputClass} rows={5} value={configText} onChange={(event) => setConfigText(event.target.value)} /></Field><Field label="输入映射 JSON"><textarea className={inputClass} rows={3} value={inputText} onChange={(event) => setInputText(event.target.value)} /></Field><Field label="输出映射 JSON"><textarea className={inputClass} rows={3} value={outputText} onChange={(event) => setOutputText(event.target.value)} /></Field><Field label="依赖节点 ID（逗号分隔）"><input className={inputClass} value={depsText} onChange={(event) => setDepsText(event.target.value)} /></Field><Field label="执行条件 JSON"><textarea className={inputClass} rows={2} value={conditionText} onChange={(event) => setConditionText(event.target.value)} /></Field><Field label="失败策略"><select className={inputClass} value={selectedNode.failure_policy || "stop"} onChange={(event) => editNode({ failure_policy: event.target.value })}><option value="stop">停止流程</option><option value="skip">跳过节点</option><option value="wait_human">等待人工</option></select></Field><label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={selectedNode.enabled !== false} onChange={(event) => editNode({ enabled: event.target.checked })} />启用节点</label><div className="flex gap-2"><Button size="sm" onClick={applyInspector}>应用配置与映射</Button><Button size="sm" variant="danger" onClick={removeNode}>删除节点</Button></div></>}
      {selectedStep && <><p className="border-t pt-3 text-xs text-slate-500">当前状态：{selectedStep.status} · Attempt {selectedStep.attempt_no}</p>{selectedStep.error && <p className="text-xs text-rose-700">{selectedStep.error}</p>}{selectedStep.stale_reason && <p className="text-xs text-amber-700">{selectedStep.stale_reason}</p>}<details><summary className="cursor-pointer text-xs">实际输入</summary><pre className="mt-2 max-h-40 overflow-auto bg-slate-50 p-2 text-xs">{pretty(selectedStep.params)}</pre></details><details><summary className="cursor-pointer text-xs">实际输出</summary><pre className="mt-2 max-h-40 overflow-auto bg-slate-50 p-2 text-xs">{pretty(selectedStep.output)}</pre></details><p className="text-xs text-slate-500">历史尝试：{attempts.length}</p><div className="flex flex-wrap gap-2"><Button size="sm" disabled={busy || dirty} onClick={() => runAction("rerun")}>运行此节点 / 刷新数据</Button><Button size="sm" variant="secondary" disabled={busy || dirty} onClick={() => runAction("rerun-from-here")}>从这里重跑</Button>{selectedStep.status === "waiting_input" && (selectedStep.error ? <><Button size="sm" disabled={busy || dirty} onClick={() => runAction("complete", { action: "retry" })}>人工确认后重试</Button><Button size="sm" variant="secondary" disabled={busy || dirty} onClick={() => runAction("complete", { action: "skip" })}>跳过失败节点</Button></> : <Button size="sm" disabled={busy || dirty} onClick={() => runAction("complete")}>完成人工节点</Button>)}</div></>}
      </div>}</section><section className="rounded-2xl border border-slate-200 bg-white p-5"><h2 className="font-semibold">运行历史</h2><p className="mt-2 text-xs text-slate-500">{run ? `当前 Run #${run.id} · ${run.status} · 定义 ${run.definition_checksum?.slice(0, 12) || "未知"}` : "尚无真实 Run"}</p><div className="mt-3 flex flex-wrap gap-2">{runs.map((item) => <Button key={item.id} size="sm" variant="secondary" onClick={() => api.get<Run>(`${base}/runs/${item.id}`).then(setRun).catch((err) => setError(problem(err)))}>#{item.id}</Button>)}</div>{run?.error && <p className="mt-2 text-xs text-rose-700">{run.error}</p>}</section></aside></div>
  </div>;
}

function ModalityShell({ modality, outputs, assets }: { modality: Unit["modality"]; outputs: UnitOutput[]; assets: SharedAsset[] }) {
  if (modality === "text") {
    const textOutputs = outputs.filter((output) => output.output_kind === "draft" || output.output_kind === "candidate");
    return <section className="mb-5 rounded-2xl border border-slate-200 bg-white p-5"><h2 className="font-semibold">文字成品区</h2><p className="mt-2 text-xs text-slate-500">仅列出真实 Run 关联的 Draft 与已批准 Candidate；正文仍由现有稿件与审阅功能管理。</p>{textOutputs.length ? <ul className="mt-3 space-y-2 text-sm">{textOutputs.map((output) => <li key={output.id} className="rounded-lg bg-slate-50 p-3">{output.output_kind === "draft" ? "稿件 Draft" : "已批准 Candidate"} #{output.entity_id} · Run #{output.run_id} / Attempt #{output.attempt_id}</li>)}</ul> : <p className="mt-3 text-sm text-slate-500">尚无工作流产出的文字版本。</p>}</section>;
  }
  if (modality === "graphic") {
    const visuals = assets.filter((asset) => ["image", "chart", "screenshot"].includes(asset.kind || ""));
    return <section className="mb-5 rounded-2xl border border-slate-200 bg-white p-5"><h2 className="font-semibold">图文素材区</h2><p className="mt-2 text-xs text-slate-500">图片、图表和截图只在真实生成版本存在时展示，公开使用前仍需核对权利。</p>{visuals.length ? <ul className="mt-3 space-y-2 text-sm">{visuals.map((asset) => <li key={asset.id} className="rounded-lg bg-slate-50 p-3">{asset.kind} Revision #{asset.material_revision_id} · {asset.rights_status || "权利待核对"} · Run #{asset.run_id}</li>)}</ul> : <p className="mt-3 text-sm text-slate-500">尚无已生成的图文素材版本。</p>}</section>;
  }
  const clips = assets.filter((asset) => asset.kind === "video");
  const scripts = outputs.filter((output) => output.output_kind === "draft");
  return <section className="mb-5 rounded-2xl border border-slate-200 bg-white p-5"><h2 className="font-semibold">视频脚本与片段区</h2><p className="mt-2 text-xs text-slate-500">视频脚本沿用 Draft 版本；没有验证过的视频生成器时不展示假片段。</p><div className="mt-3 grid gap-3 sm:grid-cols-2"><div className="rounded-lg bg-slate-50 p-3 text-sm"><h3 className="font-medium">脚本版本</h3>{scripts.length ? scripts.map((item) => <p key={item.id} className="mt-2">Draft #{item.entity_id} · Run #{item.run_id}</p>) : <p className="mt-2 text-slate-500">暂无真实脚本</p>}</div><div className="rounded-lg bg-slate-50 p-3 text-sm"><h3 className="font-medium">视频片段</h3>{clips.length ? clips.map((asset) => <p key={asset.id} className="mt-2">Revision #{asset.material_revision_id} · {asset.rights_status || "权利待核对"}</p>) : <p className="mt-2 text-slate-500">尚无已生成片段</p>}</div></div></section>;
}
