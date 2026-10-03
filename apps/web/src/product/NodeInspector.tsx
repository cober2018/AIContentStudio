import { lazy, Suspense, useEffect, useState } from "react";
import { api } from "../api";
import { Button, Field, inputClass } from "../components/ui";
import { PLUGIN_CHOICES, pretty } from "./useProductionWorkflow";
import type { useProductionWorkflow } from "./useProductionWorkflow";
const ProviderMediaPanel = lazy(() => import("./ProviderMediaPanel"));

function GenerationInspector({ workflow, design }: { workflow: ReturnType<typeof useProductionWorkflow>; design: boolean }) {
  const [profiles, setProfiles] = useState<string[]>([]);
  const [error, setError] = useState("");
  const [open, setOpen] = useState(false);
  useEffect(() => {
    let active = true;
    if (design) void api.get<{ profiles: Record<string, { enabled: boolean }> }>("/settings/model-capabilities")
      .then((result) => { if (active) setProfiles(Object.entries(result.profiles).filter(([, item]) => item.enabled).map(([id]) => id)); })
      .catch(() => { if (active) setError("无法读取模型配置，请先检查设置。"); });
    return () => { active = false; };
  }, [design]);
  const { busy, readOnly, dirty, configText, setConfigText, selectedStep, runAction } = workflow;
  let config: Record<string, unknown> = {};
  try { const parsed = JSON.parse(configText); if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) config = parsed; } catch { /* Invalid JSON stays visible in the existing editor. */ }
  function change(patch: Record<string, unknown>) { setConfigText(pretty({ ...config, ...patch })); }
  const taskId = selectedStep?.output.generation_task_id;
  const locked = busy || readOnly || dirty;
  return <div className="space-y-3 rounded-lg border border-amber-200 p-3">
    <p className="text-sm">持久媒体生成：保存的工作流开始执行时会提交一次，可能消耗额度。等待、查询、接受结果都沿用原任务；不能通用重跑或跳过。</p>
    {error && <p role="alert" className="text-sm text-rose-700">{error}</p>}
    {design && <>
      <Field label="生成能力"><select className={inputClass} value={String(config.capability ?? "")} onChange={(event) => change({ capability: event.target.value, parameters: { items: 1 } })}><option value="">请选择</option><option value="image_generation">生图</option><option value="video_generation">生视频</option><option value="tts">语音</option></select></Field>
      <Field label="所选模型配置"><select className={inputClass} value={String(config.selected_profile ?? "")} onChange={(event) => change({ selected_profile: event.target.value })}><option value="">请选择</option>{Boolean(config.selected_profile) && !profiles.includes(String(config.selected_profile)) && <option value={String(config.selected_profile)}>当前模型未连接 / 不可用</option>}{profiles.map((id) => <option key={id} value={id}>{id}</option>)}</select></Field>
      <Field label="生成提示词"><textarea className={inputClass} maxLength={2000} value={String(config.prompt ?? "")} onChange={(event) => change({ prompt: event.target.value })} /></Field>
      <Field label={config.capability === "image_generation" ? "单张图片像素上限" : "单份视频 / 语音秒数上限"}><input className={inputClass} type="number" min={1} step={1} value={String((config.parameters as Record<string, unknown> | undefined)?.[config.capability === "image_generation" ? "pixels" : "seconds"] ?? "")} onChange={(event) => change({ parameters: { items: 1, [config.capability === "image_generation" ? "pixels" : "seconds"]: Number(event.target.value) } })} /></Field>
      <p className="text-xs text-slate-600">设置后点击“应用配置与映射”，再保存项目工作流。服务端检查能力、插件路由与上限；模型已登记不代表该能力可执行。来源精确版本和显式插件仍可在配置 JSON 中设置。</p>
    </>}
    {!design && selectedStep && <>
      <p className="text-sm">任务状态：{String(selectedStep.output.generation_state ?? selectedStep.status)} · 发送前记录 #{String(selectedStep.output.generation_started_attempt_id ?? "等待准备")}</p>
      <Button size="sm" disabled={locked} onClick={() => void runAction("complete", { action: "refresh" })}>刷新原结果 / 接受后推进</Button>
      <Button size="sm" variant="secondary" disabled={locked || selectedStep.status === "succeeded"} onClick={() => void runAction("complete", { action: "recover" })}>查询原任务（不重新提交）</Button>
      {!taskId && selectedStep.status === "running" && <Button size="sm" disabled={locked} onClick={() => void runAction("complete", { action: "submit_prepared" })}>继续原准备（可能发送一次）</Button>}
      {selectedStep.output.generation_state === "prepared" && <Button size="sm" disabled={locked} onClick={() => void runAction("complete", { action: "submit_prepared" })}>执行原准备一次</Button>}
      {typeof taskId === "string" && <><Button size="sm" variant="secondary" onClick={() => setOpen(!open)}>{open ? "关闭原任务" : "查看原任务 / 独立接受素材"}</Button>{open && <Suspense fallback={<p>读取原任务…</p>}><ProviderMediaPanel key={taskId} initialTaskId={taskId} unavailable={locked} onAccepted={async () => { await runAction("complete", { action: "refresh" }); }} /></Suspense>}</>}
    </>}
  </div>;
}
export function NodeInspector({ workflow }: { workflow: ReturnType<typeof useProductionWorkflow> }) {
  const { readOnly, dirty, design: workflowDesign, attempts, plugins, busy, configText, setConfigText, inputText, setInputText, outputText, setOutputText, conditionText, setConditionText, depsText, setDepsText, selectedNode, selectedStep, sourcePlugin, editNode, removeNode, applyInspector, runAction } = workflow;
  const design = workflowDesign && !readOnly;
  if (!workflow.project || !workflow.unit) return null;
  return <><section className="rounded-2xl border border-slate-200 bg-white p-5"><h2 className="font-semibold">节点 Inspector</h2>{!selectedNode ? <p className="mt-3 text-sm text-slate-500">选择一个节点查看配置、输入、输出与执行历史。</p> : <div className="mt-4 space-y-3"><p className="text-xs text-slate-500">{selectedNode.id} · {selectedNode.kind}</p>{design && <><Field label="节点名称"><input className={inputClass} value={selectedNode.label || ""} onChange={(event) => editNode({ label: event.target.value })} /></Field><Field label="执行插件"><select className={inputClass} value={selectedNode.plugin} onChange={(event) => editNode({ plugin: event.target.value })}>{PLUGIN_CHOICES[selectedNode.kind].map((plugin) => <option key={plugin}>{plugin}</option>)}</select></Field>{selectedNode.kind === "Data" && <Field label="数据来源插件"><select className={inputClass} value={String(selectedNode.config.data_source_plugin_key || "studio.source")} onChange={(event) => editNode({ config: { ...selectedNode.config, data_source_plugin_key: event.target.value } })}>{plugins.map((plugin) => <option key={plugin.key} value={plugin.key}>{plugin.name}{plugin.available ? "" : " · 未连接"}</option>)}</select></Field>}{selectedNode.kind === "Data" && sourcePlugin && <p className={`text-xs ${sourcePlugin.available ? "text-emerald-700" : "text-amber-700"}`}>{sourcePlugin.available ? "已验证只读执行" : `不可执行：${sourcePlugin.reason}`}</p>}<Field label="节点配置 JSON"><textarea className={inputClass} rows={5} value={configText} onChange={(event) => setConfigText(event.target.value)} /></Field><Field label="输入映射 JSON"><textarea className={inputClass} rows={3} value={inputText} onChange={(event) => setInputText(event.target.value)} /></Field><Field label="输出映射 JSON"><textarea className={inputClass} rows={3} value={outputText} onChange={(event) => setOutputText(event.target.value)} /></Field><Field label="依赖节点 ID（逗号分隔）"><input className={inputClass} value={depsText} onChange={(event) => setDepsText(event.target.value)} /></Field><Field label="执行条件 JSON"><textarea className={inputClass} rows={2} value={conditionText} onChange={(event) => setConditionText(event.target.value)} /></Field><Field label="失败策略"><select className={inputClass} value={selectedNode.failure_policy || "stop"} onChange={(event) => editNode({ failure_policy: event.target.value })}><option value="stop">停止流程</option><option value="skip">跳过节点</option><option value="wait_human">等待人工</option></select></Field><label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={selectedNode.enabled !== false} onChange={(event) => editNode({ enabled: event.target.checked })} />启用节点</label><div className="flex gap-2"><Button size="sm" onClick={applyInspector}>应用配置与映射</Button><Button size="sm" variant="danger" onClick={removeNode}>删除节点</Button></div></>}
      {design && selectedNode.kind === "Data" && <Field label="API 数据连接版本"><select className={inputClass}
        value={selectedNode.config.data_source_plugin_key === "api" ? String(selectedNode.config.source_ref ?? "") : ""}
        onChange={(event) => { const profile = workflow.dataCapabilities.find((item) => item.source_ref === event.target.value);
          if (profile) editNode({ config: { ...selectedNode.config, data_source_plugin_key: profile.plugin_key, source_ref: profile.source_ref } }); }}>
        <option value="">选择已有 API 连接版本</option>
        {selectedNode.config.data_source_plugin_key === "api" && Boolean(selectedNode.config.source_ref) && !workflow.sourceCapability && <option value={String(selectedNode.config.source_ref)}>当前固定连接不可用</option>}
        {workflow.dataCapabilities.map((item) => <option key={item.id} value={item.source_ref}>{item.key} · v{item.version} · {item.executable ? "已验证" : "不可执行"}</option>)}
      </select><p className="mt-1 text-xs text-slate-500">选择后固定该连接版本；保存项目工作流后才能运行。连接的配置与验证在设置页完成。</p></Field>}
      {selectedNode.plugin === "media.generate" && <GenerationInspector key={selectedNode.id} workflow={workflow} design={design} />}
      {selectedStep && <><p className="border-t pt-3 text-xs text-slate-500">当前状态：{selectedStep.status} · Attempt {selectedStep.attempt_no}</p>{selectedStep.error && <p className="text-xs text-rose-700">{selectedStep.error}</p>}{selectedStep.stale_reason && <p className="text-xs text-amber-700">{selectedStep.stale_reason}</p>}<details><summary className="cursor-pointer text-xs">实际输入</summary><pre className="mt-2 max-h-40 overflow-auto bg-slate-50 p-2 text-xs">{pretty(selectedStep.params)}</pre></details><details><summary className="cursor-pointer text-xs">实际输出</summary><pre className="mt-2 max-h-40 overflow-auto bg-slate-50 p-2 text-xs">{pretty(selectedStep.output)}</pre></details><p className="text-xs text-slate-500">历史尝试：{attempts.length}</p>{selectedNode.plugin !== "media.generate" && <div className="flex flex-wrap gap-2"><Button size="sm" disabled={readOnly || busy || dirty} onClick={() => runAction("rerun")}>运行此节点 / 刷新数据</Button><Button size="sm" variant="secondary" disabled={readOnly || busy || dirty} onClick={() => runAction("rerun-from-here")}>从这里重跑</Button>{selectedStep.status === "waiting_input" && (selectedStep.error ? <><Button size="sm" disabled={readOnly || busy || dirty} onClick={() => runAction("complete", { action: "retry" })}>人工确认后重试</Button><Button size="sm" variant="secondary" disabled={readOnly || busy || dirty} onClick={() => runAction("complete", { action: "skip" })}>跳过失败节点</Button></> : <Button size="sm" disabled={readOnly || busy || dirty} onClick={() => runAction("complete")}>完成人工节点</Button>)}</div>}</>}
      </div>}</section></>;
}
