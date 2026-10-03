import { lazy, Suspense, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { Button, ErrorBanner, Field, Spinner, inputClass } from "../components/ui";
import { useProductionWorkflow, problem } from "./useProductionWorkflow";
import type { Run } from "./useProductionWorkflow";
import { ProductionContextHeader } from "./ProductionContextHeader";
import { ProductionAssetDrawer } from "./ProductionAssetDrawer";
import { WorkflowMiniCanvas } from "./WorkflowMiniCanvas";
import { NodeInspector } from "./NodeInspector";
import { ContentMasterPanel } from "./ContentMasterPanel";

const ChannelVariantsPanel = lazy(() => import("./ChannelVariantsPanel"));

export function ProductionWorkspace({ projectId, unitId }: { projectId: number; unitId: number }) {
  const [variantsOpen, setVariantsOpen] = useState(false);
  const workflow = useProductionWorkflow(projectId, unitId);
  const { readOnly, base, project, unit, binding, defaultBinding, definition, dirty, design, setDesign, setSelected, runs, run, setRun, outputs, loading, busy, error, setError, notice, runSourceRef, setRunSourceRef, selectedNode, executor, editNode, saveOverride, saveDefault, startRun } = workflow;
  if (loading) return <div className="p-9"><Spinner label="加载生产工作台…" /></div>;
  if (!project || !unit) return <div className="p-9"><ErrorBanner message={error || "内容单元不存在或无权访问。"} /></div>;
  return <div className="mx-auto max-w-7xl px-6 py-9">
    <Link to={`/projects/${project.id}?tab=matrix`} className="text-sm text-slate-500">← {project.title} / 内容矩阵</Link>
    <ProductionContextHeader workflow={workflow} />
    {readOnly && <p className="mb-4 rounded-lg bg-amber-50 px-4 py-3 text-sm text-amber-800">此项目或内容单元已归档，仅供查看历史运行、尝试和产物；不能保存或重新执行。</p>}
    {error && <div className="mb-4"><ErrorBanner message={error} /></div>}{notice && <p className="mb-4 rounded-lg bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{notice}</p>}
    <ProductionAssetDrawer workflow={workflow} />
    <ContentMasterPanel projectId={projectId} unit={unit} readOnly={project.status === "archived" || unit.status === "archived"} outputs={outputs} />
    <section className="mb-5 rounded-xl border border-slate-200 bg-white p-4"><div className="flex items-center justify-between gap-3"><div><h2 className="font-semibold">渠道适配</h2><p className="text-xs text-slate-500">基于已保存的 Content Master 创建渠道专属变体；不修改 Master 或 Workflow 草稿。</p></div><Button variant="secondary" onClick={() => setVariantsOpen(!variantsOpen)}>{variantsOpen ? "收起变体" : "打开渠道变体"}</Button></div></section>
    {variantsOpen && <Suspense fallback={<Spinner label="加载渠道变体…" />}><ChannelVariantsPanel projectId={projectId} unit={unit} readOnly={readOnly} workflowDirty={dirty} /></Suspense>}
    {selectedNode?.kind === "AI" && <section className="mb-5 space-y-3 rounded-xl border border-slate-200 bg-white p-4 text-sm">
      <h2 className="font-semibold">AI 节点执行路由 · {selectedNode.id}</h2>
      <p className="text-xs text-slate-500">当前功能路由：{executor?.provider} / {executor?.model}。已配置不等于远端验证成功；运行前会重新校验。</p>
      {executor?.profiles && <Field label="此节点使用的注册模型"><select className={inputClass} disabled={!design || readOnly || busy} value={String(selectedNode.config.model_profile_id || "")} onChange={event => {
        const chosen = executor.profiles?.find(p => p.profile_id === event.target.value);
        editNode({ config: { ...selectedNode.config, model_profile_id: chosen?.profile_id, provider: chosen?.provider, model: chosen?.model } });
      }}><option value="">继承功能路由 / 全局默认</option>{executor.profiles.map(p => <option key={p.profile_id} value={p.profile_id}>{p.model} · {p.provider}</option>)}</select></Field>}
      {!executor?.available && <p className="text-xs text-amber-700">{executor?.reason || "尚无可执行配置"}</p>}
    </section>}
    <div className="mb-5 flex flex-wrap items-center gap-2 rounded-xl border border-slate-200 bg-white p-4"><Button disabled={readOnly} variant={design ? "secondary" : "primary"} onClick={() => { setDesign(!design); setSelected(null); }}>{design ? "退出设计模式" : "进入设计模式"}</Button><Button disabled={readOnly || busy || !dirty} onClick={saveOverride}>保存项目覆盖</Button><Button variant="secondary" disabled={readOnly || busy || definition.nodes.length === 0} onClick={saveDefault}>另存为角色默认新版本</Button>{definition.nodes.some((node) => node.kind === "Data") && <input disabled={readOnly} aria-label="运行时来源 ID" className={`${inputClass} max-w-40`} placeholder="来源 ID（角色默认）" value={runSourceRef} onChange={(event) => setRunSourceRef(event.target.value)} />}<Button disabled={readOnly || busy || dirty || !unit.pinned_workflow_id} onClick={startRun}>启动真实 Run</Button><span className={`text-xs ${dirty ? "text-amber-700" : "text-slate-500"}`}>{dirty ? "有未保存修改" : `项目修订 ${binding?.revision || 0} · 角色默认修订 ${defaultBinding?.revision || 0}`}</span></div>
    <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_360px]"><WorkflowMiniCanvas workflow={workflow} /><aside className="space-y-5"><NodeInspector workflow={workflow} /><section className="rounded-2xl border border-slate-200 bg-white p-5"><h2 className="font-semibold">运行历史</h2><p className="mt-2 text-xs text-slate-500">{run ? `当前 Run #${run.id} · ${run.status} · 定义 ${run.definition_checksum?.slice(0, 12) || "未知"}` : "尚无真实 Run"}</p><div className="mt-3 flex flex-wrap gap-2">{runs.map((item) => <Button key={item.id} size="sm" variant="secondary" onClick={() => api.get<Run>(`${base}/runs/${item.id}`).then(setRun).catch((err) => setError(problem(err)))}>#{item.id}</Button>)}</div>{run?.error && <p className="mt-2 text-xs text-rose-700">{run.error}</p>}</section></aside></div>
  </div>;
}
