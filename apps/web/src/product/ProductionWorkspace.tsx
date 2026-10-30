import { useTaskLink, setProductionWorkbench } from "./taskNavigation";
import SkuWorkRetention from "./SkuWorkRetention";
import { lazy, Suspense, useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api, currentUser } from "../api";
import GuidedProductionGoal from "./GuidedProductionGoal";
import GuidedProductionProfile from "./GuidedProductionProfile";
import type { VideoProductionSummary } from "./VideoShotMaterialPanel";
import type { VideoStudioView } from "./VideoStudioShell";
import { Button, ErrorBanner, Spinner } from "../components/ui";
import { useProductionWorkflow } from "./useProductionWorkflow";
import { ProductionContextHeader } from "./ProductionContextHeader";
import { ProductionAssetDrawer } from "./ProductionAssetDrawer";
import { ContentMasterPanel } from "./ContentMasterPanel";
import { StageSubSteps } from "./StageSubSteps";
import type { RecipeSummary } from "./CreationRecipePanel";

const ChannelVariantsPanel = lazy(() => import("./ChannelVariantsPanel"));
const CreativeExecutionPanel = lazy(() => import("./CreativeExecutionPanel"));
const CapabilityMemoryPanel = lazy(() => import("./CapabilityMemoryPanel"));
const CreationRecipePanel = lazy(() => import("./CreationRecipePanel"));
const VideoChainPanel = lazy(() => import("./VideoChainPanel"));
const ArticleChainPanel = lazy(() => import("./ArticleChainPanel"));
const VoiceoverPanel = lazy(() => import("./VoiceoverPanel"));
const ShotMaterialPages = lazy(() => import("./VideoMaterialSteps").then(module => ({ default: module.ShotMaterialPages })));
const MusicPanel = lazy(() => import("./VideoMaterialSteps").then(module => ({ default: module.MusicPanel })));
const ProductShotGeneration = lazy(() => import("./VideoMaterialSteps").then(module => ({ default: module.ProductShotGeneration })));
const ReferenceVideoPanel = lazy(() => import("./ReferenceVideoPanel"));
const StoryboardGridPanel = lazy(() => import("./StoryboardGridPanel"));
// Persona video steps in order; the chain decides how far the user may go.
const VIDEO_ORDER = ["goal", "plan", "materials", "voice", "sample", "final", "delivery"];

export function ProductionWorkspace({ projectId, unitId }: { projectId: number; unitId: number }) {
  const taskLink = useTaskLink();
  const [params, setParams] = useSearchParams();
  const [brief, setBrief] = useState<{ core_message?: string; audience?: string; product_context?: Record<string, unknown> | null } | null>(null);
  const [briefIssue, setBriefIssue] = useState("");
  const [briefPending, setBriefPending] = useState(true);
  const briefOwner = useRef<number | null>(null);
  const [savedSettings, setSavedSettings] = useState<import("./GuidedProductionProfile").Settings>({});
  const [briefReload, setBriefReload] = useState(0);
  const [assistantFocus, setAssistantFocus] = useState<{ step: string; owner: "profile" | "master" }>({ step: "", owner: "master" });
  const [goalDirty, setGoalDirty] = useState(false);
  const [profileDirty, setProfileDirty] = useState(false);
  const [productionSummary, setProductionSummary] = useState<VideoProductionSummary | null>(null);
  const [recipeSummary, setRecipeSummary] = useState<RecipeSummary & { knowledge?: { revision_no: number; items: { title: string; purposes: string[] }[] } | null } | null>(null);
  const [selectedKnowledge, setSelectedKnowledge] = useState<{ revision_no: number; items: { title: string; purposes: string[]; modalities?: string[]; persona_id?: number; unit_id?: number; model_use_allowed: boolean }[] } | null>(null);
  const [factBoundary, setFactBoundary] = useState<{ revision_no: number; fact_pack_id: number; fact_pack_version: number } | null | undefined>(undefined);
  const [factBoundaryIssue, setFactBoundaryIssue] = useState("");
  const [knowledgeIssue, setKnowledgeIssue] = useState("");
  const [masterState, setMasterState] = useState({ dirty: false, hasMaster: false, hasRender: false, readiness: "incomplete" });
  useEffect(() => { let active = true; if (briefOwner.current !== projectId) { setBrief(null); setBriefPending(true); } api.get<typeof brief>(`/content-projects/${projectId}/brief`).then(value => { if (active) {setBrief(value);setBriefIssue("");} }).catch(() => { if (active) setBriefIssue("任务书暂时无法读取，请重试；作品归属保持不变。"); }).finally(() => { if (active) { briefOwner.current = projectId; setBriefPending(false); } }); return () => { active = false; }; }, [projectId, briefReload]);

  const [variantsOpen, setVariantsOpen] = useState(params.get("panel") === "variants");
  const [executionOpen, setExecutionOpen] = useState(params.get("panel") === "execution");
  const [memoryOpen, setMemoryOpen] = useState(params.get("panel") === "capability-memory");
  const [opened, setOpened] = useState({ variants: variantsOpen, execution: executionOpen, memory: memoryOpen });
  const [masterReloadRequest, setMasterReloadRequest] = useState(0);
  const masterRegion = useRef<HTMLDivElement>(null);
  function openMaster() {
    setMasterReloadRequest(value => value + 1);
    goStep(product || simpleVideo ? "plan" : "make");
    masterRegion.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    masterRegion.current?.focus({ preventScroll: true });
  }
  function toggle(panel: "variants" | "execution" | "memory") {
    // Collapsing a lazy panel must not discard its unsaved local decisions.
    setOpened(previous => ({ ...previous, [panel]: true }));
    if (panel === "variants") setVariantsOpen(previous => !previous);
    else if (panel === "execution") setExecutionOpen(previous => !previous);
    else setMemoryOpen(previous => !previous);
  }
  useEffect(() => {
    if (params.get("panel") === "execution") {
      setOpened(previous => ({ ...previous, execution: true })); setExecutionOpen(true);
    }
  }, [params]);
  const executionId = Number(params.get("execution")) || undefined;
  const workflow = useProductionWorkflow(projectId, unitId);
  const { readOnly, project, unit, dirty, loading, error, notice, workflowRevision, refreshWorkflowFromRecipe } = workflow;
  const product = unit?.production_domain === "product";
  const simpleVideo = unit?.modality === "video";
  // Shares the panel's cache key so the step pages and the panel always agree on where the video is.
  const chain = useQuery({ queryKey: ["video-chain", currentUser(), projectId, unitId], enabled: simpleVideo, retry: false,
    queryFn: () => api.get<{ state: string; label: string; locked?: boolean }>(`/content-projects/${projectId}/units/${unitId}/video-chain`) });
  const chainState = chain.data?.state || "";
  const chainReach = chainState.startsWith("draft") || chainState === "not_started" ? 1 : chainState === "making" ? 3 : chainState.startsWith("sample") ? 4 : chainState === "done" ? 6 : chainState ? 5 : 0;
  const chainHome = ["plan", "plan", "plan", "materials", "sample", "final", "final"][chainReach];
  const chainLocked = simpleVideo && !!chain.data?.locked;
  const articleUnit = !product && (unit?.modality === "text" || unit?.modality === "graphic");
  useEffect(() => {
    if (!unit) return;
    setProductionWorkbench(product ? "product" : "persona");
    return () => setProductionWorkbench(null);
  }, [unit, product]);
  const skuId = useQuery({ queryKey: ["production-sku", currentUser(), projectId, unitId], enabled: product,
    queryFn: async () => (await api.get<{ sku_id: number | null }>(`/content-projects/${projectId}/units/${unitId}/production-profile`)).sku_id }).data;
  const article = useQuery({ queryKey: ["article-chain", currentUser(), projectId, unitId], enabled: articleUnit, retry: false,
    queryFn: () => api.get<{ writer: string; locked?: boolean }>(`/content-projects/${projectId}/units/${unitId}/article-chain`) });
  // With a third-party writer the platform stages stay out of the way; the piece is written over MCP and reviewed here.
  const externalWriter = articleUnit && article.data?.writer === "external";
  const articleLocked = articleUnit && !!article.data?.locked;
  useEffect(() => {
    let alive = true;
    setSelectedKnowledge(null); setFactBoundary(undefined); setFactBoundaryIssue(""); setKnowledgeIssue("");
    if (unit && !product) {
      api.get<NonNullable<typeof selectedKnowledge>>(`/content-projects/${projectId}/knowledge`).then(value => { if (alive) setSelectedKnowledge(value); }).catch(() => { if (alive) setKnowledgeIssue("已选知识暂不可读，请在来源与事实边界页核对。"); });
      api.get<NonNullable<typeof factBoundary>>(`/content-projects/${projectId}/fact-boundary`).then(value => { if (alive) setFactBoundary(value); }).catch(() => { if (alive) setFactBoundaryIssue("事实边界读取失败，当前状态未知。请重试或到来源与事实边界页核对。"); });
    }
    return () => { alive = false; };
  }, [projectId, unitId, unit?.persona_id, product, briefReload]);
  const captureRoute = productionSummary?.route;
  const captureEnabled = captureRoute === "real" || captureRoute === "mixed";
  const steps: { id: VideoStudioView | "delivery" | "make" | "sample" | "final" | "voice" | "advanced"; label: string; hint: string }[] = simpleVideo ? [
    product ? { id: "goal", label: "商品与本条目标", hint: "复用商品事实，填写这一条作品要表达的购买理由。" } : { id: "goal", label: "选题与资料", hint: "核对选题、受众、事实与来源，填写本条创作目标。" },
    { id: "plan", label: "导演稿", hint: "逐镜看分镜和素材需求；采用或写修改意见。" },
    { id: "materials", label: "素材", hint: "逐镜看每个镜头用的素材；缺的可以从素材库拖进来。" },
    { id: "voice", label: "配音与音乐", hint: "生成并试听配音；看背景音乐，要换就拖一首进来。" },
    { id: "sample", label: "小样", hint: "看小样、按秒写意见；通过后开始排版。" },
    { id: "final", label: "成片", hint: "看成片、写意见或通过；通过即定稿，不能再改。" },
    { id: "delivery", label: "交付", hint: "基于已保存主稿进行渠道适配，进入既有审核与交付。" },
  ] : product ? [
    { id: "goal", label: "商品与本条目标", hint: "复用商品事实，填写这一条作品要表达的购买理由。" },
    { id: "plan", label: "导演方案", hint: "选择真实创作流程，起草并审阅脚本、动作链与粗分镜。" },
    { id: "style", label: "视觉与声音定样", hint: captureEnabled ? "核对场地、出镜范围、光线与手机拍摄条件；旁白可在后期制作。" : "先确定共同视觉参考、讲话方式与配乐方向，再制作镜头。" },
    { id: "materials", label: "逐镜素材", hint: captureRoute === "real" ? "按已确认任务书拍摄原片，逐镜上传、审阅选段，再明确采用。旁白可后期补充。" : captureRoute === "mixed" ? "实拍镜头按任务书拍摄回传；AI镜头确认图片与提示词后生成。逐镜审阅并采用。" : "选定精确图片，准备据图提示词，人工网页生成并回传审阅。" },
    { id: "edit", label: "剪辑包装", hint: captureEnabled ? "保存已审阅采用的原片与选段，后期补充旁白和配乐，交接达芬奇主剪与按需AE包装。" : "保存已采用素材与声音，交接达芬奇主剪和按需AE包装。" },
    { id: "review", label: "成片与反馈", hint: "核对真实成片与主稿版本，保存定位反馈并进入既有审核交付。" },
  ] : [
    { id: "goal", label: "选题与资料", hint: "核对选题、受众、事实与来源，填写本条创作目标。" },
    { id: "plan", label: "内容方案", hint: "选择创作流程，起草并审阅内容方案。" },
    { id: "make", label: "制作内容", hint: "按文字、图文或视频形态制作，音频沿用已接受文字派生。" },
    { id: "review", label: "审阅修改", hint: "查看真实结果与检查，明确修改或接受。" },
    { id: "delivery", label: "交付", hint: "基于已保存主稿进行渠道适配，进入既有审核与交付。" },
  ];
  const legacy = params.get("stage") ? "plan" : params.get("execution") || params.get("panel") === "execution" ? product ? "edit" : "make" : params.get("panel") === "variants" ? product ? "review" : "delivery" : "goal";
  const asked = params.get("workstep");
  // Old links (制作内容 / 审阅修改, the former product steps) and a video opened without a step land where the chain is.
  const requestedStep = simpleVideo ? asked === "make" ? "materials" : asked === "review" ? "final" : asked && (asked === "advanced" || steps.some(item => item.id === asked)) ? asked : params.get("execution") ? "advanced" : chainHome : asked || legacy;
  // 高级 holds what belongs to no step; it sits outside the numbered flow.
  const advanced = simpleVideo && requestedStep === "advanced";
  const step = advanced ? { id: "advanced" as const, label: "高级", hint: "主稿编辑器、版本与检查、创作流程、创意执行、方法与自动化。日常制作不用进来。" } : steps.find(item => item.id === requestedStep) || steps[0];
  const stepIndex = steps.indexOf(step);
  const assistantOwner = assistantFocus.step === step.id ? assistantFocus.owner : product && (step.id === "style" || step.id === "review") ? "profile" : "master";
  function stepStatus(id: string) {
    if (id === "plan" && product && captureEnabled && !simpleVideo) return productionSummary?.captureStatus === "ready" ? "脚本与任务书已确认 · 可拍摄" : productionSummary?.captureStatus === "loading" ? "正在读取拍摄确认状态" : productionSummary?.captureStatus === "error" ? "拍摄确认状态读取失败" : "脚本 / 任务书待确认或复核";
    if (simpleVideo && id !== "goal") {
      const at = VIDEO_ORDER.indexOf(id);
      if (!chainReach) return "读取中";
      if (at > chainReach) return "还没到";
      if (id === chainHome) return chain.data?.label || "";
      if (id === "plan") return "导演稿已采用";
      if (id === "materials" || id === "voice") return chainLocked ? "已定稿" : chainReach === 3 ? "可调整" : "已用于小样";
      if (id === "sample") return "小样已通过";
    }
    if (!product) {
      if (id === "goal") return brief?.core_message ? "已有已保存创作目标 · 资料需核对" : "待填写本条目标";
      if (id === "plan") return recipeSummary ? `已接受 ${recipeSummary.accepted}/${recipeSummary.total} 阶段${recipeSummary.issues ? ` · ${recipeSummary.issues} 项需处理` : ""}` : "流程状态读取中";
      if (id === "make") return recipeSummary?.running ? `执行中 ${recipeSummary.running} 阶段` : masterState.hasMaster ? masterState.dirty ? "已有主稿 · 草稿待保存" : "已有已保存主稿" : "待生成 / 接受产物";
      if (id === "review") return recipeSummary?.waiting ? `待审阅 ${recipeSummary.waiting} 阶段` : masterState.hasMaster ? `主稿检查状态：${masterState.readiness} · 仍需内容审阅` : "待产物";
      return masterState.hasMaster ? "已有主稿 · 待渠道检查与交付" : "待已保存主稿";
    }
    if (id === "plan") return masterState.hasMaster ? "已有主稿 · 方案接受另行核对" : "待起草 / 审阅";
    if (id !== "materials" && id !== "edit" && id !== "review") return "可进入准备";
    const summary = productionSummary;
    if (!summary || summary.state === "loading") return "正在读取素材任务";
    if (summary.state === "error") return "任务暂时无法读取";
    if (id === "materials") {
      if (!summary.total) return "待分镜与资料";
      if (summary.needsAttention) return `需核对 ${summary.needsAttention} 镜`;
      if (summary.reviewable) return `待审阅 ${summary.reviewable} 镜`;
      if (summary.waitingReturn) return `待人工回传 ${summary.waitingReturn} 镜`;
      if (summary.working) return `制作中 ${summary.working} 镜`;
      if (summary.waitingAdoption) return `待采用 / 保存 ${summary.waitingAdoption} 镜`;
      if (summary.missing) return captureRoute === "real" ? `待拍摄 ${summary.missing} 镜` : captureRoute === "mixed" ? `待拍摄 ${summary.captureMissing || 0} 镜 · 其他待准备 ${summary.missing - (summary.captureMissing || 0)} 镜` : `待资料 / 准备 ${summary.missing} 镜`;
      return `已保存采用 ${summary.savedAdopted}/${summary.total} 镜`;
    }
    if (id === "review") {
      if (masterState.hasRender) return masterState.dirty ? "草稿已引用成片 · 待保存" : "已引用成片 · 待核对";
      if (summary.editState === "result_ready") return `最近后期 #${summary.editExecutionId} 回片待审阅，核对版本`;
      return "等成片";
    }
    if (!summary.total || summary.savedAdopted < summary.total) return "待后期素材";
    if (!summary.editState) return "待后期";
    const labels: Record<string, string> = { prepared: "待领取", claimed: "已领取", in_progress: "制作中", result_ready: "回片待审阅", accepted: "已接受，需核对版本", blocked: "待处理", unknown: "结果待核对", rejected: "需修改", cancelled: "已取消", superseded: "已替代", failed_before_dispatch: "提交前失败" };
    return `最近后期 #${summary.editExecutionId} · ${labels[summary.editState] || summary.editState}`;
  }
  function goStep(id: string) { setParams(previous => { const next = new URLSearchParams(previous); next.set("workstep", id); return next; }, { replace: true }); }
  if (loading || briefPending) return <div className="p-9"><Spinner label="加载生产工作台…" /></div>;
  if (!project || !unit) return <div className="p-9"><ErrorBanner message={error || "内容单元不存在或无权访问。"} /></div>;
  return <div className="mx-auto w-full max-w-[1240px] px-5 pb-20 pt-8 sm:px-8 md:pt-12 lg:px-12">
    <Link to={product ? `/production?workspace=product${skuId ? `&sku=${skuId}` : ""}` : "/production?workspace=persona"} className="text-sm text-slate-500">← {product ? "商品视频工作台" : "角色内容工作台"} / {product ? unit.title : project.title}</Link>
    <ProductionContextHeader workflow={workflow} productContext={brief?.product_context} slim={simpleVideo && !advanced} />
    {workflow.needsProductContext && <div className="mb-4 space-y-2 rounded-lg border border-amber-200 bg-amber-50 p-4"><p className="text-sm">此旧作品仍保留历史角色快照。新制作前，明确切换为商品配置；历史运行保持原样。</p><Button disabled={readOnly || workflow.busy || dirty || profileDirty || masterState.dirty || goalDirty} onClick={() => void workflow.continueProduct()}>按商品流程继续</Button></div>}
    {readOnly && <p className="mb-4 rounded-lg bg-amber-50 px-4 py-3 text-sm text-amber-800">当前工作台为只读：项目或内容单元已归档，或当前账号无编辑权限；不能保存或重新执行。</p>}
    {product && !simpleVideo && masterState.hasMaster && ["incomplete_context", "stale"].includes(masterState.readiness) && <p role="status" className="mb-4 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">{captureEnabled ? "商品资料或事实边界仍需核对。拍摄以当前脚本与任务书的确认状态为准；后期与公开交付仍须通过资料、事实和素材检查。" : masterState.readiness === "stale" ? "资料已变化，请核对并保存新的主稿版本，再准备素材或后期任务。" : "主稿的资料或事实边界尚未齐全，可以继续整理方案；准备素材或后期任务前请先补齐。"} <Link className="underline" to={taskLink(`/projects/${projectId}?tab=evidence`)}>来源与事实边界</Link></p>}
    {error && <div className="mb-4"><ErrorBanner message={error} /></div>}{notice && <p className="mb-4 rounded-lg bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{notice}</p>}
    {briefIssue && <div className="mb-5"><ErrorBanner message={briefIssue} /><div className="mt-2 flex gap-2"><Button variant="secondary" onClick={() => setBriefReload(value => value + 1)}>重新读取任务书</Button></div></div>}
    <div className="mb-5 grid items-start gap-5 lg:grid-cols-[210px_minmax(0,1fr)]">
      <nav aria-label={simpleVideo ? product ? "商品视频七步" : "角色视频七步" : product ? "商品六步制作" : "角色五步制作"} className="card relative p-2 lg:sticky lg:top-4"><ol className="relative">{steps.map((item, index) => { const active = step.id === item.id; return <li key={item.id} className="relative">{index < steps.length - 1 && <span aria-hidden className="absolute left-[27px] top-[42px] h-[calc(100%-26px)] w-px bg-ink-200" />}<button type="button" aria-current={active ? "step" : undefined} onClick={() => goStep(item.id)} className={`relative flex w-full items-start gap-3 rounded-xl px-3 py-3 text-left transition-colors ${active ? "bg-ink-50" : "hover:bg-ink-50/70"}`}><span className={`relative z-10 mt-0.5 grid h-7 w-7 shrink-0 place-items-center rounded-full font-serif text-[13px] tabular-nums ${active ? "bg-ink-900 text-paper" : "border border-ink-300 bg-surface text-ink-600"}`}>{index + 1}</span><span className="min-w-0"><span className={`block text-[14px] ${active ? "font-semibold text-ink-900" : "font-medium text-ink-800"}`}>{item.label}</span><span className="mt-0.5 block text-[12px] leading-snug text-ink-500">{stepStatus(item.id)}</span></span></button>{item.id === "plan" && recipeSummary && !simpleVideo && <StageSubSteps summary={recipeSummary} />}</li>; })}</ol>{simpleVideo && <button type="button" aria-current={advanced ? "step" : undefined} onClick={() => goStep("advanced")} className={`mt-1 w-full rounded-xl border-t border-ink-200/70 px-3 py-2.5 text-left text-[13px] ${advanced ? "bg-ink-50 font-semibold text-ink-900" : "text-ink-500 hover:bg-ink-50/70"}`}>高级</button>}</nav>
      <main className="min-w-0" aria-label="当前制作步骤">
        <header className="mb-6 flex flex-wrap items-end justify-between gap-x-6 gap-y-3 border-b border-ink-200/80 pb-5"><div className="min-w-0"><p className="eyebrow">{product ? "商品视频" : "角色创作"} · {advanced ? "不在流程里" : `第 ${stepIndex + 1} / ${steps.length} 步`}</p><h2 className="mt-2 text-[28px] leading-tight text-ink-900">{step.label}</h2><p className="mt-2 text-[14px] text-ink-600">{step.hint}</p></div><p role="status" className={`text-[12.5px] ${masterState.dirty || profileDirty || goalDirty || dirty ? "text-amber-700" : "text-ink-500"}`}>{masterState.dirty || profileDirty || goalDirty || dirty ? "● 有未保存草稿，切换步骤会保留" : "没有未保存草稿"}</p></header>
        {(step.id === "delivery" || step.id === "review") && <p className="mb-5"><Link className="text-sm text-indigo-700 underline" to={taskLink(`/review?project=${projectId}&unit=${unitId}`)}>下一步：审阅与交付当前作品 →</Link></p>}
        <GuidedProductionGoal key={`goal:${projectId}`} projectId={projectId} unitId={unitId} isProduct={product} active={step.id === "goal"} readOnly={readOnly} onDirty={setGoalDirty} onSaved={() => setBriefReload(value => value + 1)} />
        {step.id === "goal" && <div className="mb-5 flex flex-wrap items-center gap-3"><Link className="text-sm text-indigo-700 underline" to={taskLink(`/projects/${projectId}?tab=brief`)}>{product ? "详细商品资料" : "详细创作任务书"}</Link><Link className="text-sm text-indigo-700 underline" to={taskLink(`/projects/${projectId}?tab=evidence`)}>来源与事实边界</Link>{!product && <Link className="text-sm text-indigo-700 underline" to={`/identities?persona=${unit.persona_id}`}>角色身份与声音配置</Link>}<Button size="sm" variant="secondary" onClick={() => workflow.setAssetsOpen(true)}>查看共享资料</Button></div>}
        {!product && (step.id === "goal" || step.id === "plan" && !simpleVideo) && <section className="mb-5 rounded-xl border border-slate-200 bg-white p-4" aria-label="本条资料与风格用途"><h3 className="text-sm font-semibold">资料选择与本次运行依据</h3><p className="mt-2 text-xs text-slate-500">已核实事实沿用来源与事实边界；专业参考帮助理解，风格样本只影响表达。旧资料不自动成为本条事实。</p>{knowledgeIssue && <ErrorBanner message={knowledgeIssue} />}<p className="mt-2 text-xs text-slate-600">{factBoundaryIssue || (factBoundary === undefined ? "正在读取已核实事实边界…" : factBoundary ? `已核实事实：事实边界修订 ${factBoundary.revision_no} · FactPack #${factBoundary.fact_pack_id} v${factBoundary.fact_pack_version}。条目只在来源页查看，风格样本里的数字不会升格。` : "尚未绑定已核实事实边界。")}</p>{factBoundaryIssue && <Button variant="secondary" size="sm" onClick={() => setBriefReload(value => value + 1)}>重新读取资料状态</Button>}{recipeSummary?.runId && <div className="mt-3 rounded-lg bg-indigo-50 p-3 text-xs"><p>当前运行 #{recipeSummary.runId} 固定的知识：{recipeSummary.knowledge ? `修订 ${recipeSummary.knowledge.revision_no}` : "未选择"}</p>{recipeSummary.knowledge?.items.map((item, index) => <p key={index} className="mt-1">{item.title} · {item.purposes.map(purpose => purpose === "professional" ? "专业参考" : "风格样本").join("、")}</p>)}<p className="mt-1">实际阶段按用途与当前授权裁剪；展开“预览实际请求”核对最终输入。新选择不会替换本次冻结版本。</p></div>}{selectedKnowledge && <p className="mt-3 text-xs text-slate-500">下次新运行的选择 · 项目知识修订 {selectedKnowledge.revision_no}</p>}{selectedKnowledge && <div className="mt-3 grid gap-3 sm:grid-cols-2">{[["professional", "专业参考"], ["style", "个人风格样本"]].map(([purpose, label]) => { const selected = selectedKnowledge.items.filter(item => item.purposes.includes(purpose) && (!item.persona_id || item.persona_id === unit.persona_id) && (!item.unit_id || item.unit_id === unitId)); return <div key={purpose}><h4 className="text-xs font-medium">{label}</h4>{selected.length ? selected.map((item, index) => <p key={index} className="mt-1 text-xs text-slate-600">{item.title} · {item.model_use_allowed && (item.modalities ?? ["text"]).includes(unit.modality) ? "已授权当前形态，按阶段用途裁剪" : "不进入当前模型输入"}</p>) : <p className="mt-1 text-xs text-slate-500">尚未选择</p>}</div>; })}</div>}<p className="mt-3 text-xs"><Link className="text-indigo-700 underline" to={taskLink(`/projects/${projectId}?tab=evidence`)}>核对所选片段、授权和已核实事实</Link> · <Link className="text-indigo-700 underline" to={`/identities?persona=${unit.persona_id}`}>查看角色分形态参考与方法</Link></p></section>}
        {articleUnit && step.id === "plan" && <Suspense fallback={<Spinner />}><ArticleChainPanel projectId={projectId} unitId={unitId} readOnly={readOnly} /></Suspense>}
        {(!simpleVideo || advanced) && !externalWriter && <div id="production-planning" tabIndex={-1}><Suspense fallback={<Spinner label="加载创作流程…" />}><CreationRecipePanel persona={!product} onDone={() => goStep("make")} onSummary={setRecipeSummary} active={advanced || step.id === "plan" || !product && (step.id === "make" || step.id === "review")} key={`${projectId}:${unitId}`} projectId={projectId} unitId={unitId} readOnly={readOnly || workflow.needsProductContext} modality={unit.modality} onOpenMaster={openMaster} workflowRevision={workflowRevision} onRecipeChanged={() => refreshWorkflowFromRecipe()} /></Suspense></div>}
        {product && (!simpleVideo || step.id === "goal") && <GuidedProductionProfile key={`${projectId}:${unitId}`} projectId={projectId} unitId={unitId} view={step.id} readOnly={readOnly} onDirty={setProfileDirty} onSavedSettings={setSavedSettings} assistantVisible={assistantOwner === "profile"} onAssistanceFocus={() => setAssistantFocus({ step: step.id, owner: "profile" })} />}
        <div ref={masterRegion} hidden={simpleVideo ? !advanced : step.id === "goal" || step.id === "delivery"} tabIndex={-1} aria-label="作品主稿编辑"><ContentMasterPanel key={`${projectId}:${unitId}`} projectId={projectId} unit={unit} readOnly={readOnly || chainLocked || articleLocked} reloadRequest={masterReloadRequest} active={simpleVideo ? advanced : step.id !== "goal" && step.id !== "delivery"} view={product ? step.id as VideoStudioView : simpleVideo || step.id === "make" ? undefined : step.id as VideoStudioView} assistantVisible={!product || assistantOwner === "master"} onAssistanceFocus={() => setAssistantFocus({ step: step.id, owner: "master" })} speechMode={savedSettings.speech_mode} productionSettingsDirty={profileDirty} onStateChange={setMasterState} onProductionSummary={setProductionSummary} onOpenExecution={() => { setOpened(previous => ({ ...previous, execution: true })); setExecutionOpen(true); }} /></div>
        {simpleVideo && !advanced && step.id !== "goal" && <Suspense fallback={<Spinner />}>{chainReach && VIDEO_ORDER.indexOf(step.id) > chainReach
          ? <p className="mb-5 rounded-xl border border-slate-200 bg-white p-4 text-sm text-slate-600">还没到这一步。视频现在：{chain.data?.label}。<button type="button" className="ml-2 text-indigo-700 underline" onClick={() => goStep(chainHome)}>去当前步骤</button></p>
          : <div className="mb-5 space-y-4">
            {step.id === "plan" && <><ReferenceVideoPanel projectId={projectId} unitId={unitId} readOnly={readOnly || chainLocked} /><VideoChainPanel projectId={projectId} unitId={unitId} step="draft" showDraft /></>}
            {step.id === "materials" && <><ShotMaterialPages projectId={projectId} unitId={unitId} readOnly={readOnly} />{product && <ProductShotGeneration projectId={projectId} unitId={unitId} readOnly={readOnly} />}<StoryboardGridPanel projectId={projectId} unitId={unitId} readOnly={readOnly} /></>}
            {step.id === "voice" && <><VoiceoverPanel projectId={projectId} unitId={unitId} readOnly={readOnly || chainLocked} onSaved={() => setMasterReloadRequest(value => value + 1)} /><MusicPanel projectId={projectId} unitId={unitId} readOnly={readOnly} /></>}
            {(step.id === "sample" || step.id === "final") && <VideoChainPanel projectId={projectId} unitId={unitId} step={step.id} />}
            {step.id === "delivery" && <ChannelVariantsPanel projectId={projectId} unit={unit} readOnly={readOnly} workflowDirty={dirty} />}
          </div>}</Suspense>}
        {product && <div hidden={step.id !== (simpleVideo ? "final" : "review")}><SkuWorkRetention projectId={projectId} unitId={unitId} readOnly={readOnly} /></div>}
        {!advanced && <footer className="mb-5 flex items-center justify-between gap-3 rounded-xl border border-slate-200 bg-white p-4"><Button variant="secondary" disabled={stepIndex === 0} onClick={() => goStep(steps[stepIndex - 1].id)}>上一步</Button><Button variant="secondary" disabled={stepIndex === steps.length - 1} onClick={() => goStep(steps[stepIndex + 1].id)}>前往{steps[stepIndex + 1]?.label || "下一步"}</Button></footer>}
      </main>
    </div>
    <ProductionAssetDrawer workflow={workflow} />
    {(!simpleVideo || advanced) && <details open={advanced || step.id === "delivery" || executionOpen || variantsOpen || memoryOpen} className="rounded-2xl border border-slate-200 bg-slate-50 p-4"><summary className="mb-4 cursor-pointer font-medium">渠道、执行、方法与高级工作流</summary><section className="mb-5 rounded-xl border border-slate-200 bg-white p-4"><div className="flex items-center justify-between gap-3"><div><h2 className="font-semibold">渠道适配</h2><p className="text-xs text-slate-500">基于已保存的 Content Master 创建渠道专属变体；不修改 Master 或 Workflow 草稿。</p></div><Button variant="secondary" onClick={() => toggle("variants")}>{variantsOpen ? "收起变体" : "打开渠道变体"}</Button></div></section>
    {opened.variants && <div hidden={!variantsOpen}><Suspense fallback={<Spinner label="加载渠道变体…" />}><ChannelVariantsPanel projectId={projectId} unit={unit} readOnly={readOnly} workflowDirty={dirty} /></Suspense></div>}
    <section className="mb-5 rounded-xl border border-slate-200 bg-white p-4"><div className="flex items-center justify-between gap-3"><div><h2 className="font-semibold">创意执行与成果</h2><p className="text-xs text-slate-500">从已保存的内容生成执行包，交给外部 Agent 或工具；成果经人工接受后进入素材库。</p></div><Button variant="secondary" onClick={() => toggle("execution")}>{executionOpen ? "收起创意执行" : "打开创意执行"}</Button></div></section>
    {opened.execution && <div hidden={!executionOpen}><Suspense fallback={<Spinner label="加载创意执行…" />}><CreativeExecutionPanel projectId={projectId} unitId={unitId} readOnly={readOnly} executionId={executionId} /></Suspense></div>}
    <section className="mb-5 rounded-xl border border-slate-200 bg-white p-4"><div className="flex items-center justify-between gap-3"><div><h2 className="font-semibold">适用方法与创作偏好</h2><p className="text-xs text-slate-500">按项目与内容单元查看所有适用方法；明确选择版本、填写参数后查看渲染结果，可不采用或写下本任务覆盖说明。</p></div><Button variant="secondary" onClick={() => toggle("memory")}>{memoryOpen ? "收起适用方法" : "查看适用方法"}</Button></div></section>
    {opened.memory && <div hidden={!memoryOpen}><Suspense fallback={<Spinner label="按需加载适用方法…" />}><CapabilityMemoryPanel projectId={projectId} unitId={unitId} executionId={executionId} readOnly={readOnly} /></Suspense></div>}
    </details>}
  </div>;
}
