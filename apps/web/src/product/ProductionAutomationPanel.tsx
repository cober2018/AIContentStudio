import { api } from "../api";
import { Button, Field, inputClass } from "../components/ui";
import { NodeInspector } from "./NodeInspector";
import { WorkflowMiniCanvas } from "./WorkflowMiniCanvas";
import { problem, type Run, useProductionWorkflow } from "./useProductionWorkflow";

export default function ProductionAutomationPanel({ workflow }: { workflow: ReturnType<typeof useProductionWorkflow> }) {
  const { readOnly, base, unit, binding, defaultBinding, definition, dirty, design, setDesign, setSelected, runs, run, setRun, busy, setError, runSourceRef, setRunSourceRef, selectedNode, executor, editNode, saveOverride, saveDefault, startRun } = workflow;
  return <section className="space-y-5" aria-label="高级自动化工作流">
    <p className="rounded-lg bg-slate-100 p-3 text-sm text-slate-600">工作流用于辅助内容生产。工作流修改与正文修改分别保存；启动 Run 不会自动替换 Content Master。</p>
    {selectedNode?.kind === "AI" && <section className="space-y-3 rounded-xl border border-slate-200 bg-white p-4 text-sm">
      <h2 className="font-semibold">AI 节点执行路由 · {selectedNode.id}</h2>
      <p className="text-xs text-slate-500">当前功能路由：{executor?.provider} / {executor?.model}。已配置不等于远端验证成功；运行前会重新校验。</p>
      {executor?.profiles && <Field label="此节点使用的注册模型"><select className={inputClass} disabled={!design || readOnly || busy} value={String(selectedNode.config.model_profile_id || "")} onChange={event => {
        const chosen = executor.profiles?.find(p => p.profile_id === event.target.value);
        editNode({ config: { ...selectedNode.config, model_profile_id: chosen?.profile_id, provider: chosen?.provider, model: chosen?.model } });
      }}><option value="">继承功能路由 / 全局默认</option>{executor.profiles.map(p => <option key={p.profile_id} value={p.profile_id}>{p.model} · {p.provider}</option>)}</select></Field>}
      {!executor?.available && <p className="text-xs text-amber-700">{executor?.reason || "尚无可执行配置"}</p>}
    </section>}
    <div className="flex flex-wrap items-center gap-2 rounded-xl border border-slate-200 bg-white p-4"><Button disabled={readOnly} variant={design ? "secondary" : "primary"} onClick={() => { setDesign(!design); setSelected(null); }}>{design ? "退出设计模式" : "进入设计模式"}</Button><Button disabled={readOnly || busy || !dirty} onClick={saveOverride}>保存项目覆盖</Button><Button variant="secondary" disabled={readOnly || busy || definition.nodes.length === 0} onClick={saveDefault}>另存为角色默认新版本</Button>{definition.nodes.some(node => node.kind === "Data") && <input disabled={readOnly} aria-label="运行时来源 ID" className={`${inputClass} max-w-40`} placeholder="来源 ID（角色默认）" value={runSourceRef} onChange={event => setRunSourceRef(event.target.value)} />}<Button disabled={readOnly || busy || dirty || !unit?.pinned_workflow_id} onClick={startRun}>启动真实 Run</Button><span className={`text-xs ${dirty ? "text-amber-700" : "text-slate-500"}`}>{dirty ? "有未保存修改" : `项目修订 ${binding?.revision || 0} · 角色默认修订 ${defaultBinding?.revision || 0}`}</span></div>
    <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_360px]"><WorkflowMiniCanvas workflow={workflow} /><aside className="space-y-5"><NodeInspector workflow={workflow} /><section className="rounded-2xl border border-slate-200 bg-white p-5"><h2 className="font-semibold">运行历史</h2><p className="mt-2 text-xs text-slate-500">{run ? `当前 Run #${run.id} · ${run.status} · 定义 ${run.definition_checksum?.slice(0, 12) || "未知"}` : "尚无真实 Run"}</p><div className="mt-3 flex flex-wrap gap-2">{runs.map(item => <Button key={item.id} size="sm" variant="secondary" onClick={() => api.get<Run>(`${base}/runs/${item.id}`).then(setRun).catch(err => setError(problem(err)))}>#{item.id}</Button>)}</div>{run?.error && <p className="mt-2 text-xs text-rose-700">{run.error}</p>}</section></aside></div>
  </section>;
}
