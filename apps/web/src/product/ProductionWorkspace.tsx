import { lazy, Suspense, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Button, ErrorBanner, Spinner } from "../components/ui";
import { useProductionWorkflow } from "./useProductionWorkflow";
import { ProductionContextHeader } from "./ProductionContextHeader";
import { ProductionAssetDrawer } from "./ProductionAssetDrawer";
import { ContentMasterPanel } from "./ContentMasterPanel";

const ChannelVariantsPanel = lazy(() => import("./ChannelVariantsPanel"));
const CreativeExecutionPanel = lazy(() => import("./CreativeExecutionPanel"));
const ProductionAutomationPanel = lazy(() => import("./ProductionAutomationPanel"));
const CapabilityMemoryPanel = lazy(() => import("./CapabilityMemoryPanel"));
const CreationRecipePanel = lazy(() => import("./CreationRecipePanel"));

export function ProductionWorkspace({ projectId, unitId }: { projectId: number; unitId: number }) {
  const [params] = useSearchParams();
  const [variantsOpen, setVariantsOpen] = useState(params.get("panel") === "variants");
  const [executionOpen, setExecutionOpen] = useState(params.get("panel") === "execution");
  const [automationOpen, setAutomationOpen] = useState(params.get("panel") === "automation");
  const [memoryOpen, setMemoryOpen] = useState(params.get("panel") === "capability-memory");
  const [opened, setOpened] = useState({ variants: variantsOpen, execution: executionOpen, automation: automationOpen, memory: memoryOpen });
  const [masterReloadRequest, setMasterReloadRequest] = useState(0);
  const masterRegion = useRef<HTMLDivElement>(null);
  function openMaster() {
    setMasterReloadRequest(value => value + 1);
    masterRegion.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    masterRegion.current?.focus({ preventScroll: true });
  }
  function toggle(panel: "variants" | "execution" | "automation" | "memory") {
    // Collapsing a lazy panel must not discard its unsaved local decisions.
    setOpened(previous => ({ ...previous, [panel]: true }));
    if (panel === "variants") setVariantsOpen(previous => !previous);
    else if (panel === "execution") setExecutionOpen(previous => !previous);
    else if (panel === "automation") setAutomationOpen(previous => !previous);
    else setMemoryOpen(previous => !previous);
  }
  const executionId = Number(params.get("execution")) || undefined;
  const workflow = useProductionWorkflow(projectId, unitId);
  const { readOnly, project, unit, dirty, outputs, loading, error, notice, workflowConflict, workflowRevision, refreshWorkflowFromRecipe } = workflow;
  if (loading) return <div className="p-9"><Spinner label="加载生产工作台…" /></div>;
  if (!project || !unit) return <div className="p-9"><ErrorBanner message={error || "内容单元不存在或无权访问。"} /></div>;
  return <div className="mx-auto max-w-7xl px-6 py-9">
    <Link to={`/projects/${project.id}?tab=matrix`} className="text-sm text-slate-500">← {project.title} / 内容矩阵</Link>
    <ProductionContextHeader workflow={workflow} />
    {readOnly && <p className="mb-4 rounded-lg bg-amber-50 px-4 py-3 text-sm text-amber-800">当前工作台为只读：项目或内容单元已归档，或当前账号无编辑权限；不能保存或重新执行。</p>}
    {error && <div className="mb-4"><ErrorBanner message={error} /></div>}{notice && <p className="mb-4 rounded-lg bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{notice}</p>}
    {workflowConflict && <div className="mb-4 space-y-2 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900" role="alert"><p>{workflowConflict}</p><div className="flex flex-wrap gap-2"><Button size="sm" variant="secondary" disabled={workflow.busy} onClick={() => { setOpened(previous => ({ ...previous, automation: true })); setAutomationOpen(true); }}>查看保留的高级流程草稿</Button><Button size="sm" variant="secondary" disabled={workflow.busy} onClick={() => { if (window.confirm("放弃高级工作流的未保存草稿并载入最新已保存流程？Content Master 的未保存编辑不会改变。")) void refreshWorkflowFromRecipe(true).catch(() => {}); }}>放弃高级流程草稿，载入已保存版本</Button></div></div>}
    <Suspense fallback={<div className="mb-5 rounded-xl border border-slate-200 bg-white p-5"><Spinner label="加载 Creation Recipe…" /></div>}><CreationRecipePanel key={`${projectId}:${unitId}`} projectId={projectId} unitId={unitId} readOnly={readOnly} modality={unit.modality} onOpenMaster={openMaster} workflowRevision={workflowRevision} onRecipeChanged={() => refreshWorkflowFromRecipe()} onOpenAdvanced={() => { setOpened(previous => ({ ...previous, automation: true })); setAutomationOpen(true); }} /></Suspense>
    <ProductionAssetDrawer workflow={workflow} />
    <div ref={masterRegion} tabIndex={-1} aria-label="Recipe 内容编辑承接"><ContentMasterPanel projectId={projectId} unit={unit} readOnly={readOnly} outputs={outputs} reloadRequest={masterReloadRequest} onOpenExecution={() => { setOpened(previous => ({ ...previous, execution: true })); setExecutionOpen(true); }} /></div>
    <section className="mb-5 rounded-xl border border-slate-200 bg-white p-4"><div className="flex items-center justify-between gap-3"><div><h2 className="font-semibold">渠道适配</h2><p className="text-xs text-slate-500">基于已保存的 Content Master 创建渠道专属变体；不修改 Master 或 Workflow 草稿。</p></div><Button variant="secondary" onClick={() => toggle("variants")}>{variantsOpen ? "收起变体" : "打开渠道变体"}</Button></div></section>
    {opened.variants && <div hidden={!variantsOpen}><Suspense fallback={<Spinner label="加载渠道变体…" />}><ChannelVariantsPanel projectId={projectId} unit={unit} readOnly={readOnly} workflowDirty={dirty} /></Suspense></div>}
    <section className="mb-5 rounded-xl border border-slate-200 bg-white p-4"><div className="flex items-center justify-between gap-3"><div><h2 className="font-semibold">创意执行与成果</h2><p className="text-xs text-slate-500">从已保存的内容生成执行包，交给外部 Agent 或工具；成果经人工接受后进入素材库。</p></div><Button variant="secondary" onClick={() => toggle("execution")}>{executionOpen ? "收起创意执行" : "打开创意执行"}</Button></div></section>
    {opened.execution && <div hidden={!executionOpen}><Suspense fallback={<Spinner label="加载创意执行…" />}><CreativeExecutionPanel projectId={projectId} unitId={unitId} readOnly={readOnly} executionId={executionId} /></Suspense></div>}
    <section className="mb-5 rounded-xl border border-slate-200 bg-white p-4"><div className="flex items-center justify-between gap-3"><div><h2 className="font-semibold">适用方法与创作偏好</h2><p className="text-xs text-slate-500">按项目与内容单元查看所有适用方法；明确选择版本、填写参数后查看渲染结果，可不采用或写下本任务覆盖说明。</p></div><Button variant="secondary" onClick={() => toggle("memory")}>{memoryOpen ? "收起适用方法" : "查看适用方法"}</Button></div></section>
    {opened.memory && <div hidden={!memoryOpen}><Suspense fallback={<Spinner label="按需加载适用方法…" />}><CapabilityMemoryPanel projectId={projectId} unitId={unitId} executionId={executionId} readOnly={readOnly} /></Suspense></div>}
    <section className="mb-5 rounded-xl border border-slate-200 bg-white p-4"><div className="flex items-center justify-between gap-3"><div><h2 className="font-semibold">高级自动化</h2><p className="text-xs text-slate-500">保留工作流设计器与真实运行调试；不作为日常内容创作的默认入口。</p></div><Button variant="secondary" onClick={() => toggle("automation")}>{automationOpen ? "收起高级自动化" : "打开高级自动化"}{dirty ? " · 未保存" : ""}</Button></div></section>
    {opened.automation && <div hidden={!automationOpen}><Suspense fallback={<Spinner label="加载高级自动化…" />}><ProductionAutomationPanel workflow={workflow} /></Suspense></div>}
  </div>;
}
