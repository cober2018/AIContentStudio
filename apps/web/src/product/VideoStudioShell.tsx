import { lazy, Suspense, useEffect, useId, useState } from "react";
import CreativeIntentEditor, { type CreativeIntent } from "./CreativeIntentEditor";
import FormAssistancePanel from "./FormAssistancePanel";
import type { VideoProductionSummary } from "./VideoShotMaterialPanel";
import type { AssistanceField } from "./formAssistanceTypes";
import { setShotProduction, setShotFilming, setCapturePlan, type VideoFilming } from "./VideoStudioModel";
import { api, currentUser } from "../api";
import { Button, Field, inputClass } from "../components/ui";
import { addOverlay, addScriptBlock, addShot, addSubtitleCue, addTrack, addTimelineItem, bindFinalRender, canUseFinalRender, bindShotSource, importSubtitleSrt, removeOverlay, removeShot, removeSubtitleCue, removeTimelineItem, removeTrack, reorderShots, setCover, setMusic, setVoice, updateAspectRatio, updateOverlay, updateScriptBlock, updateShot, updateSubtitleCue, updateTimelineDuration, updateTimelineItem, updateVideoTitle, type VideoDraft, type VideoTimelineItem, type VideoTrack } from "./VideoStudioModel";

type ProjectAsset = { key: string; material_id: number; material_revision_id: number; content_hash: string; kind: string; mime_type: string | null; title: string | null; rights_status: string | null; public_use_allowed: boolean; model_use_allowed: boolean; local_final_use_allowed?: boolean; source_type: string; provenance?: { source_kind?: string | null; provider_key?: string | null } };
type Capability = { configured: boolean; executable: boolean; verified: boolean; reason: string };
type VideoCapabilities = { video_generation: Capability; tts: Capability; asr: Capability };
const AsrSuggestionPanel = lazy(() => import("./AsrSuggestionPanel"));
const VideoShotMaterialPanel = lazy(() => import("./VideoShotMaterialPanel"));
const StoryboardTable = lazy(() => import("./StoryboardTable"));
const ShotMaterialFinder = lazy(() => import("./ShotMaterialFinder"));
const ProviderMediaPanel = lazy(() => import("./ProviderMediaPanel"));
export type VideoStudioView = "goal" | "plan" | "style" | "materials" | "edit" | "review" | "none" | "simple";
export type VideoStudioProps = { isProduct?: boolean; onProductionSummary?: (summary: VideoProductionSummary) => void; view?: VideoStudioView; assistantVisible?: boolean; onAssistanceFocus?: () => void; speechMode?: string; productionSettingsDirty?: boolean; creativeIntent?: CreativeIntent | null; onIntentChange?: (value: CreativeIntent) => void; projectId: number; unitId?: number; masterId?: number | null; masterHash?: string | null; savedSourceIds?: number[]; dirty?: boolean; draft: VideoDraft | null; legacyPayload?: Record<string, unknown>; upgradeMode?: boolean; onChange: (draft: VideoDraft) => void; onOpenExecution?: () => void; readOnly: boolean; more?: boolean };

const filmingFields = [
  ["subject", "拍摄主体"], ["action", "画面动作"], ["camera_position", "手机放在哪里"],
  ["angle", "拍摄角度"], ["focus", "必须看清的重点"], ["evidence_requirement", "需要什么真实证据"], ["audio_note", "收音说明（可后期配音）"],
] as const;

export default function VideoStudioShell({ isProduct = false, more = false, view, onProductionSummary, assistantVisible = true, onAssistanceFocus, speechMode, productionSettingsDirty, creativeIntent, onIntentChange, projectId, unitId, masterId = null, masterHash = null, savedSourceIds = [], dirty = false, draft, legacyPayload, upgradeMode = false, onChange, onOpenExecution, readOnly }: VideoStudioProps) {
  const simple = view === "simple";
  // The simple view keeps every section mounted; only the main ones are visible until 更多 is opened.
  const folded = simple && !more;
  const show = (...views: VideoStudioView[]) => !view || views.includes(view) || simple && views.some(item => item !== "goal");
  const main = (order: number) => simple ? { "data-main": true, style: { order } } : {};
  const sectionPrefix = useId();
  const sectionId = (name: string) => `${sectionPrefix}-${name}`;
  const [issue, setIssue] = useState("");
  const [planView, setPlanView] = useState<"script" | "shots">("script");
  useEffect(() => setPlanView("script"), [projectId, unitId]);
  const [productContext, setProductContext] = useState<{category?: string; style_ref?: {artifact_id:number;revision_id:number;content_hash:string}; production_stages?: import("./ProductionStageControls").ProductionStages} | null>(null);
  useEffect(() => { let active = true; void api.get<{product_context?: typeof productContext}>(`/content-projects/${projectId}/brief`).then(value=>{if(active)setProductContext(value.product_context || null);}).catch(()=>{if(active)setIssue("商品品类和风格读取失败，保存相关偏好前请重试。");});return()=>{active=false;};}, [projectId]);
  const [captureState, setCaptureState] = useState<{ masterId: number; script: { state: string; content_hash: string }; task: { state: string; content_hash: string }; production_profile_revision_id: number | null; ready_to_shoot: boolean; adoptions?: Record<string, string> } | null>(null);
  const [captureIssue, setCaptureIssue] = useState("");
  useEffect(() => {
    let active = true;
    setCaptureState(null); setCaptureIssue("");
    if (!unitId || !masterId || !draft?.payload.capture_plan) return () => { active = false; };
    void api.get<{ id: number; capture_status?: Omit<NonNullable<typeof captureState>, "masterId"> }>(`/content-projects/${projectId}/units/${unitId}/master-revisions/${masterId}`).then(value => {
      if (active && value.capture_status) setCaptureState({ ...value.capture_status, masterId: value.id });
    }).catch(error => { if (active) setCaptureIssue(error instanceof Error ? error.message : "确认状态读取失败"); });
    return () => { active = false; };
  }, [projectId, unitId, masterId, masterHash, productionSettingsDirty, !!draft?.payload.capture_plan]);
  const [newTrackKind, setNewTrackKind] = useState<VideoTrack["kind"]>("video");
  const [voiceMode, setVoiceMode] = useState<"recorded" | "tts">("recorded");
  const [ratioWidth, setRatioWidth] = useState(draft?.payload.aspect_ratio[0] ?? 9);
  const [ratioHeight, setRatioHeight] = useState(draft?.payload.aspect_ratio[1] ?? 16);
  const [assets, setAssets] = useState<ProjectAsset[]>([]);
  const [assetIssue, setAssetIssue] = useState("");
  const [assetRefresh, setAssetRefresh] = useState(0);
  const [assetLoading, setAssetLoading] = useState(true);
  const [assetsVersion, setAssetsVersion] = useState(-1);
  // A picked search result reaches the shot only after the project asset list that contains it has been reloaded.
  const [pendingBind, setPendingBind] = useState<{ shotId: string; revisionId: number; after: number } | null>(null);
  const [assetNotice, setAssetNotice] = useState("");
  const [generationOpened, setGenerationOpened] = useState(false);
  const [generationOpen, setGenerationOpen] = useState(false);
  const [capabilities, setCapabilities] = useState<VideoCapabilities | null>(null);
  const [capabilityIssue, setCapabilityIssue] = useState("");
  const [showFinalPreview, setShowFinalPreview] = useState(false);
  const [finalToolsOpen, setFinalToolsOpen] = useState(false);
  useEffect(() => { setAssets([]); setAssetNotice(""); }, [projectId]);
  useEffect(() => {
    let active = true;
    setAssetLoading(true); setAssetIssue(""); setAssetNotice("");
    api.get<ProjectAsset[]>(`/content-projects/${projectId}/shared-assets`).then((items) => {
      if (active) { setAssets(items); setAssetsVersion(assetRefresh); setAssetIssue(""); setAssetNotice("项目素材已刷新；选择精确版本后，另行保存内容 Master。"); }
    }).catch((cause) => { if (active) setAssetIssue(cause instanceof Error ? cause.message : "项目素材不可用"); }).finally(() => { if (active) setAssetLoading(false); });
    return () => { active = false; };
  }, [projectId, assetRefresh]);
  useEffect(() => {
    let active = true;
    setCapabilities(null); setCapabilityIssue("");
    api.get<VideoCapabilities>(`/content-projects/${projectId}/video-capabilities`).then((state) => { if (active) { setCapabilities(state); setCapabilityIssue(""); } }).catch((cause) => { if (active) setCapabilityIssue(cause instanceof Error ? cause.message : "能力状态不可用"); });
    return () => { active = false; };
  }, [projectId]);
  useEffect(() => { if (draft?.payload.voice.mode === "recorded" || draft?.payload.voice.mode === "tts") setVoiceMode(draft.payload.voice.mode); }, [draft?.payload.voice.mode]);
  useEffect(() => { if (draft) { setRatioWidth(draft.payload.aspect_ratio[0]); setRatioHeight(draft.payload.aspect_ratio[1]); } }, [draft?.payload.aspect_ratio[0], draft?.payload.aspect_ratio[1]]);
  useEffect(() => setShowFinalPreview(false), [draft?.payload.render_asset_ref?.material_revision_id]);
  useEffect(() => {
    if (!pendingBind || !draft || assetsVersion < pendingBind.after) return;
    const asset = assets.find(item => item.material_revision_id === pendingBind.revisionId);
    if (asset) edit(() => bindShotSource(draft, pendingBind.shotId, asset));
    else setIssue("素材已入库，但项目素材列表里还没有它，请刷新后在镜头里手动选择。");
    setPendingBind(null);
  }, [assetsVersion, pendingBind]);
  function edit(action: () => VideoDraft) {
    try { onChange(action()); setIssue(""); } catch (cause) { setIssue(cause instanceof Error ? cause.message : "视频内容无效"); }
  }
  async function downloadCaptureSheet() {
    if (!unitId || !masterId || dirty) return;
    try {
      const saved = await api.get<{ id: number; revision_no: number; payload_hash: string; payload: VideoDraft["payload"]; capture_status?: { ready_to_shoot: boolean } }>(`/content-projects/${projectId}/units/${unitId}/master-revisions/${masterId}`);
      const rows = [...saved.payload.shots].sort((a, b) => (a.filming?.filming_order ?? a.order) - (b.filming?.filming_order ?? b.order));
      const lines = [saved.payload.title || "商品拍摄任务书", `路线：${saved.payload.capture_plan?.route || "旧路线"}`, `主稿 #${saved.id} v${saved.revision_no} · ${saved.payload_hash}`, saved.capture_status?.ready_to_shoot ? "已确认可拍" : "草稿 / 待复核，不是已确认拍摄版本", "", saved.payload.capture_plan?.script_structure || "", ""];
      for (const shot of rows) {
        lines.push(`素材来源：${shot.production?.source_mode || "existing"}`, `景别：${shot.framing || "待填写"}`, `镜头 ${shot.id} · ${shot.label} · 成片顺序 ${shot.order + 1}`, `目的：${shot.purpose || "待填写"}`, `场景：${shot.filming?.scene_id || "待填写"}`, `拍摄顺序：${(shot.filming?.filming_order ?? shot.order) + 1}`, `计划剪入：${shot.duration_ms / 1000}秒；建议原片：${shot.filming?.raw_duration_ms ? shot.filming.raw_duration_ms / 1000 + "秒" : "待填写"}`);
        if (shot.production && shot.production.source_mode !== "existing") { lines.push("此镜头采用AI/动效路线，按该镜头制作说明执行，不列入实拍清单。", ""); continue; }
        for (const [key, label] of filmingFields) lines.push(`${label}：${shot.filming?.[key] || "待填写"}`);
        lines.push("");
      }
      const url = URL.createObjectURL(new Blob([lines.join("\n")], { type: "text/plain;charset=utf-8" }));
      const link = document.createElement("a"); link.href = url; link.download = `filming-master-${saved.id}-v${saved.revision_no}.txt`; link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (error) { setCaptureIssue(error instanceof Error ? error.message : "下载任务书失败"); }
  }
  if (!draft && view === "none") return null;
  if (!draft) return <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900"><p>历史 Video Master v1 仅供查看。需要显式预览并追加 v2 修订后才能在专业工作台编辑。</p>{legacyPayload && <pre className="mt-2 max-h-40 overflow-auto text-xs">{JSON.stringify(legacyPayload, null, 2)}</pre>}</div>;
  const sourceAssets = assets.filter((item) => (item.kind === "image" || item.kind === "video") && (item.public_use_allowed || item.model_use_allowed));
  const audioAssets = assets.filter((item) => item.kind === "audio" && (item.public_use_allowed || item.model_use_allowed));
  const coverAssets = assets.filter((item) => item.kind === "image" && (item.public_use_allowed || item.model_use_allowed));
  const finalAssets = assets.filter((item) => item.mime_type === "video/mp4" && canUseFinalRender(item));
  const assetSelectionDisabled = readOnly || assetLoading || !!assetIssue;
  const capturePlan = draft.payload.capture_plan;
  const captureEnabled = !!capturePlan && capturePlan.route !== "ai";
  const captureShots = draft.payload.shots.filter(shot => captureEnabled && (capturePlan.route === "real" || !shot.production || shot.production.source_mode === "existing"));
  const captureStatus = captureIssue ? "error" : dirty || productionSettingsDirty || !masterId ? "draft" : !captureState ? "loading" : captureState.ready_to_shoot ? "ready" : "draft";
  const assistanceFields: AssistanceField[] = [
    ...(capturePlan ? [{ key: "capture_plan.script_structure", label: "销售思路与脚本结构", value: capturePlan.script_structure, apply: (value: import("./formAssistanceTypes").AssistanceValue) => edit(() => setCapturePlan(draft, { ...capturePlan, script_structure: String(value ?? "") })) }] : []),
    ...(captureEnabled ? captureShots.flatMap(shot => (["scene_id", "filming_order", "raw_duration_ms"] as const).map(key => ({ key: `shots.${shot.id}.filming.${key}`, label: `镜头${shot.order + 1} ${key === "scene_id" ? "所属场景" : key === "filming_order" ? "拍摄顺序（从0记录）" : "原片建议时长（毫秒）"}`, value: shot.filming?.[key] ?? null, kind: key === "scene_id" ? "text" as const : "number" as const, apply: (value: import("./formAssistanceTypes").AssistanceValue) => edit(() => setShotFilming(draft, shot.id, { [key]: key === "scene_id" ? String(value ?? "") : value == null ? undefined : Number(value) })) }))) : []),
    ...(captureEnabled ? captureShots.flatMap(shot => filmingFields.map(([key, label]) => ({ key: `shots.${shot.id}.filming.${key}`, label: `镜头${shot.order + 1} ${label}`, value: shot.filming?.[key] || "", apply: (value: import("./formAssistanceTypes").AssistanceValue) => edit(() => setShotFilming(draft, shot.id, { [key]: String(value ?? "") })) }))) : []),
    ...(["must_keep", "must_avoid"] as const).map(key => ({ key: `intent.${key}`, label: key === "must_keep" ? "意图必须保留" : "意图必须避免", value: creativeIntent?.[key] || [], protected: true, kind: "list" as const, apply: (value: import("./formAssistanceTypes").AssistanceValue) => onIntentChange?.({ ...(creativeIntent || { schema: "creative.intent.v1" }), [key]: Array.isArray(value) ? value : String(value ?? "").split("\n").filter(Boolean) }) })),
    ...(["objective", "why_now", "audience", "creative_freedom", "narrative_intent", "visual_intent", "audio_intent"] as const).map(key => ({ key: `intent.${key}`, label: `创作意图 · ${key}`, value: creativeIntent?.[key] || "", protected: true, apply: (value: import("./formAssistanceTypes").AssistanceValue) => onIntentChange?.({ ...(creativeIntent || { schema: "creative.intent.v1" }), [key]: String(value ?? "") }) })),
    { key: "title", label: "视频标题", value: draft.payload.title, apply: value => edit(() => updateVideoTitle(draft, String(value ?? ""))) },
    ...draft.payload.script.blocks.map(block => ({ key: `script.${block.id}.text`, label: `脚本段落 ${block.order + 1}`, value: block.text, apply: (value: import("./formAssistanceTypes").AssistanceValue) => edit(() => updateScriptBlock(draft, block.id, String(value ?? ""))) })),
    ...draft.payload.shots.flatMap(shot => [
      ...(["label", "purpose", "duration_ms", "framing", "transition"] as const).map(key => ({ key: `shots.${shot.id}.${key}`, label: `镜头${shot.order + 1} ${key === "label" ? "名称" : key === "purpose" ? "用途" : key === "duration_ms" ? "时长" : key === "framing" ? "景别" : "转场"}`, value: shot[key] ?? null, kind: key === "duration_ms" ? "number" as const : "text" as const, apply: (value: import("./formAssistanceTypes").AssistanceValue) => edit(() => updateShot(draft, shot.id, { [key]: value })) })),
      ...(captureShots.some(item => item.id === shot.id) ? [] : [{ key: `shots.${shot.id}.production.prompt`, label: `镜头${shot.order + 1} ${shot.production?.source_mode === "web_video" ? "据图动态提示词" : "素材描述"}`, value: shot.production?.prompt || "", apply: (value: import("./formAssistanceTypes").AssistanceValue) => edit(() => setShotProduction(draft, shot.id, { ...(shot.production || { schema: "video.shot-production.v2", source_mode: "web_video", web_provider: "grok", requested_generation_duration_ms: 6000, audio_intent: "mute" }), prompt: String(value ?? "") })) }]),
    ]),
    ...draft.payload.subtitles.cues.map(cue => ({ key: `subtitles.${cue.id}.text`, label: `字幕${cue.order + 1}`, value: cue.text, apply: (value: import("./formAssistanceTypes").AssistanceValue) => edit(() => updateSubtitleCue(draft, cue.id, { text: String(value ?? "") })) })),
    ...draft.payload.overlays.map(overlay => ({ key: `overlays.${overlay.id}.text`, label: `叠字${overlay.order + 1}`, value: overlay.text, apply: (value: import("./formAssistanceTypes").AssistanceValue) => edit(() => updateOverlay(draft, overlay.id, { text: String(value ?? "") })) })),
  ];
  return <FormAssistancePanel assistantVisible={assistantVisible} onFieldFocus={onAssistanceFocus} key={`${projectId}:${unitId}`} versionKey={JSON.stringify([masterId, masterHash, draft.assetRefs, creativeIntent, productContext])} surface="video" context={{category:productContext?.category || null,style_revision_id:productContext?.style_ref?.revision_id || null}} methodRefs={productContext?.style_ref ? [productContext.style_ref] : []} productionStages={productContext?.production_stages} projectId={projectId} unitId={unitId} fields={assistanceFields} readOnly={readOnly || upgradeMode} tools={unitId && !upgradeMode && show("plan", "materials") ? focusKey => <Suspense fallback={null}><ShotMaterialFinder projectId={projectId} unitId={unitId} focusKey={focusKey} aspect={draft.payload.aspect_ratio} readOnly={readOnly}
      shots={draft.payload.shots.filter(shot => !captureShots.some(item => item.id === shot.id)).map(shot => ({ id: shot.id, label: shot.label || `镜头 ${shot.order + 1}`, bound: !!shot.source_material_revision_id,
        text: [shot.purpose, draft.payload.script.blocks.find(block => block.id === shot.script_block_id)?.text, shot.production?.prompt].filter(Boolean).join("；") }))}
      onPicked={(shotId, revisionId) => { setPendingBind({ shotId, revisionId, after: assetRefresh + 1 }); setAssetRefresh(value => value + 1); }} /></Suspense> : undefined}><div className={folded ? "flex flex-col gap-4 [&>*:not([data-main])]:hidden" : simple ? "flex flex-col gap-4" : "space-y-4"} aria-label="Video Studio">{show("goal") && onIntentChange && <CreativeIntentEditor label="Master 创作意图" value={creativeIntent || null} onChange={onIntentChange} readOnly={readOnly || upgradeMode} />}
    {show("goal", "plan") && isProduct && <section aria-label="素材路线与脚本结构" className="rounded-xl border border-slate-200 p-4">
      <Field label="本条作品的素材路线"><select className={inputClass} disabled={readOnly || upgradeMode} value={capturePlan?.route || ""} onChange={event => { if (event.target.value) edit(() => setCapturePlan(draft, { schema: "video.capture-plan.v1", route: event.target.value as "real" | "ai" | "mixed", script_structure: capturePlan?.script_structure || "" })); }}><option value="" disabled>沿用旧镜头设置 · 请选择新路线</option><option value="real">实拍</option><option value="ai">AI生成</option><option value="mixed">实拍与AI混合</option></select></Field>
      {captureEnabled && (view !== "plan" || planView === "script") && <><p className="my-2 text-sm text-slate-600">切换实拍会将本草稿镜头改为真实素材来源，旧版本保留。先讲清购买理由，再拆成可拍的镜头。旁白可以后期制作。{captureStatus === "ready" ? "当前脚本与拍摄任务书已确认，可按任务书拍摄。" : captureStatus === "loading" ? "正在读取已保存版本的确认状态。" : captureStatus === "error" ? "确认状态读取失败，请重试后核对。" : "当前内容为草稿或待复核，修改后请保存并核对确认状态。"}</p><Field label="销售思路与脚本结构"><textarea data-ai-field="capture_plan.script_structure" className={inputClass} rows={4} maxLength={10000} disabled={readOnly || upgradeMode} value={capturePlan.script_structure || ""} onChange={event => edit(() => setCapturePlan(draft, { ...capturePlan, script_structure: event.target.value }))} placeholder="目标买家和场景 → 一个购买理由 → 如何展示或证明 → 回答顾虑 → 下一步" /></Field></>}
    </section>}
    {show("plan") && captureEnabled && <div role="group" aria-label="导演方案内容" className="flex flex-wrap gap-2"><Button variant={planView === "script" ? "primary" : "secondary"} ariaPressed={planView === "script"} onClick={() => setPlanView("script")}>销售思路与脚本</Button><Button variant={planView === "shots" ? "primary" : "secondary"} ariaPressed={planView === "shots"} onClick={() => setPlanView("shots")}>分镜与拍摄任务书</Button></div>}
    {show("plan") && captureEnabled && <section className="rounded-xl border border-slate-200 p-4" aria-label="拍摄版本确认">
      <h3 className="font-semibold">确认脚本与任务书</h3><p className="mt-2 text-sm">{captureStatus === "ready" ? "已确认可拍" : captureStatus === "loading" ? "正在读取当前版本的确认状态。" : captureStatus === "error" ? "确认状态读取失败，请重新读取后核对。" : "草稿或待复核：保存后核对当前版本，再确认。旁白可以后补。"}</p>
      <p className="mt-2 text-xs" role="status">脚本：{captureStatus === "loading" ? "正在读取" : captureStatus === "error" ? "读取失败，状态未知" : dirty ? "有未保存修改" : captureState?.script.state === "confirmed" ? "已确认" : captureState?.script.state === "needs_review" ? "待复核" : "草稿 / 待确认"} · 任务书：{captureStatus === "loading" ? "正在读取" : captureStatus === "error" ? "读取失败，状态未知" : dirty || productionSettingsDirty ? "有未保存修改" : captureState?.task.state === "confirmed" ? "已确认" : captureState?.task.state === "needs_review" ? "待复核" : "草稿 / 待确认"}</p>
      {Object.values(captureState?.adoptions || {}).some(value => value === "needs_review") && <p role="status" className="text-sm text-amber-800">已采用原片的任务或选段已变化，须复核后再准备剪辑。旧原片和历史版本保留。</p>}
      {captureIssue && <p role="alert" className="text-sm text-rose-700">{captureIssue}</p>}
      <div className="mt-3 flex flex-wrap gap-2">{planView === "script" && <Button variant="secondary" size="sm" disabled={readOnly || upgradeMode || captureStatus === "loading" || captureStatus === "error" || dirty || !captureState || captureState.script.state === "confirmed" || !(capturePlan.script_structure || "").trim()} onClick={() => edit(() => setCapturePlan(draft, { ...capturePlan, script_confirmation: { source_master_revision_id: captureState!.masterId, content_hash: captureState!.script.content_hash } }))}>确认此版脚本结构（再保存生效）</Button>}
      {planView === "shots" && <><Button variant="secondary" size="sm" disabled={readOnly || upgradeMode || captureStatus === "loading" || captureStatus === "error" || dirty || productionSettingsDirty || !captureState?.production_profile_revision_id || captureState.script.state !== "confirmed" || captureState.task.state === "confirmed"} onClick={() => edit(() => setCapturePlan(draft, { ...capturePlan, task_confirmation: { source_master_revision_id: captureState!.masterId, content_hash: captureState!.task.content_hash, production_profile_revision_id: captureState!.production_profile_revision_id! } }))}>确认此版拍摄任务书（再保存生效）</Button><Button size="sm" variant="secondary" disabled={dirty || !masterId} onClick={() => void downloadCaptureSheet()}>下载已保存任务书</Button></>}</div>
    </section>}
    {show("plan") && <div className="rounded-xl border border-slate-200 bg-slate-50 p-4"><h3 className="font-semibold">视频主稿 · 导演工作台</h3><p className="text-xs text-slate-500">{captureEnabled ? "先确认销售思路与脚本结构，再确认拍摄任务书并拍摄；原片审阅采用后进入剪辑，旁白、字幕和封面可在后期补充。" : "先确定脚本、镜头意图、素材、配音、字幕和封面，再准备导演包。"}编辑只改变本地草稿；点击“保存内容 Master”才会创建不可变修订。</p>
      <div className="mt-3 grid gap-3 sm:grid-cols-2"><Field label="标题"><input data-ai-field="title" aria-label="视频标题" className={inputClass} value={draft.payload.title} disabled={readOnly} onChange={(event) => edit(() => updateVideoTitle(draft, event.target.value))} /></Field><div className="flex flex-wrap items-end gap-2"><Field label="画幅宽比例"><input aria-label="画幅宽比例" className={inputClass} type="number" min="1" max="8192" value={ratioWidth} disabled={readOnly} onChange={(event) => setRatioWidth(Number(event.target.value))} /></Field><Field label="画幅高比例"><input aria-label="画幅高比例" className={inputClass} type="number" min="1" max="8192" value={ratioHeight} disabled={readOnly} onChange={(event) => setRatioHeight(Number(event.target.value))} /></Field><Button variant="secondary" size="sm" disabled={readOnly} onClick={() => edit(() => updateAspectRatio(draft, ratioWidth, ratioHeight))}>应用画幅</Button></div></div>
      <p className="mt-1 text-xs text-slate-500">常见约分比例：9:16、16:9、1:1。{upgradeMode ? "当前值只是升级编辑起点，请亲自核对画幅、时间线和每个镜头时长。" : "改变画幅会令既有最终成片绑定失效。"}</p>
      <div className="mt-3"><Field label="目标时长（毫秒）"><input aria-label="导演目标时长" className={inputClass} type="number" min="0" max="28800000" value={draft.payload.timeline.duration_ms} disabled={readOnly} onChange={(event) => edit(() => updateTimelineDuration(draft, Number(event.target.value)))} /></Field><p className="mt-1 text-xs text-slate-500">字幕时间码按此时长校验；详细轨道和成片绑定在下方“高级与兼容工具”。结构预览不是已渲染视频。</p></div>
    </div>}
    {unitId && !upgradeMode && <div id={sectionId("video-materials")} className="scroll-mt-4" tabIndex={-1}><Suspense fallback={<p className="text-sm">加载分镜素材制作…</p>}><VideoShotMaterialPanel captureStatus={captureEnabled ? captureStatus : undefined} captureTaskHash={captureState?.task.content_hash} captureReady={!!captureState?.ready_to_shoot && !dirty && !productionSettingsDirty} captureAdoptions={captureState?.adoptions} assetLoading={assetLoading} assetIssue={assetIssue} onSummary={onProductionSummary} speechMode={speechMode} productionSettingsDirty={productionSettingsDirty} key={`${projectId}:${unitId}`} view={view && !simple ? show("materials") ? "materials" : show("edit") ? "edit" : show("review") ? "review" : "none" : undefined} projectId={projectId} unitId={unitId} masterId={masterId} dirty={dirty} draft={draft} assets={assets} readOnly={readOnly} onChange={onChange} onRefreshAssets={() => setAssetRefresh(value => value + 1)} /></Suspense></div>}
    {show("edit") && <section {...main(-1)} id={sectionId("video-execution")} tabIndex={-1} aria-label="导演包与外部执行" className="rounded-xl border border-indigo-200 bg-indigo-50 p-4"><div className="flex flex-wrap items-center justify-between gap-3"><h3 className="font-semibold">导演包与外部执行</h3><Button variant="secondary" size="sm" disabled={!onOpenExecution || upgradeMode} onClick={onOpenExecution}>打开导演包与外部执行</Button></div><p className="mt-2 text-xs text-slate-600">从已保存的视频主稿准备导演包，无需先绑定最终 MP4。外部成果经人工接受并引用到本项目后，刷新项目素材，再明确绑定并保存主稿；冻结 Candidate 仍需通过现有成片检查。</p>{dirty && <p className="mt-2 text-xs text-amber-800">当前有未保存的修改。打开执行工作区会保留本地草稿；导演包读取已保存的版本，请先保存要交给执行者的内容。</p>}{!onOpenExecution && <p className="mt-2 text-xs text-slate-500">可从本工作台“创意执行与成果”入口查看导演包。</p>}{upgradeMode && <p className="mt-2 text-xs text-amber-800">请先核对并保存 v2 升级修订，再准备导演包。</p>}</section>}
    {show("plan") && <div {...main(-4)}><Suspense fallback={null}><StoryboardTable projectId={projectId} unitId={unitId} draft={draft} readOnly={readOnly || upgradeMode} onChange={onChange} /></Suspense></div>}
    {show("plan") && <>{(!captureEnabled || planView === "script") && <section id={sectionId("video-script")} tabIndex={-1} className="scroll-mt-4 rounded-xl border border-slate-200 p-4"><div className="flex items-center justify-between"><h3 className="font-semibold">{captureEnabled ? "旁白 / 对白段落" : "脚本"}</h3><Button variant="secondary" size="sm" disabled={readOnly || upgradeMode} onClick={() => edit(() => addScriptBlock(draft))}>添加脚本段落</Button></div>
      <div className="mt-3 space-y-3">{draft.payload.script.blocks.map((block) => <Field key={block.id} label={`段落 ${block.order + 1} · ${block.id.slice(0, 8)}`}><textarea data-ai-field={`script.${block.id}.text`} aria-label={`脚本段落 ${block.order + 1}`} className={inputClass} rows={3} value={block.text} readOnly={readOnly || upgradeMode} onChange={(event) => edit(() => updateScriptBlock(draft, block.id, event.target.value))} /></Field>)}{draft.payload.script.blocks.length === 0 && <p className="text-sm text-slate-500">{captureEnabled ? "尚未填写旁白 / 对白段落；上方脚本结构用于拍摄确认，旁白可在后期补充。选择现场对白时请补齐相应台词。" : "尚无脚本段落。"}</p>}</div>
    </section>}
    {(!captureEnabled || planView === "shots") && <section className="rounded-xl border border-slate-200 p-4"><div className="flex items-center justify-between"><h3 className="font-semibold">镜头</h3><Button variant="secondary" size="sm" disabled={readOnly || upgradeMode} onClick={() => edit(() => addShot(draft))}>添加镜头</Button></div><p className="mt-1 text-xs text-slate-500">镜头 ID 保持稳定；上移/下移调整成片顺序；拍摄顺序独立填写，时间线片段另行编辑。</p>
      <div className="mt-3 space-y-3">{draft.payload.shots.map((shot, index) => <div key={shot.id} className="rounded-lg border border-slate-200 p-3"><div className="flex flex-wrap items-center justify-between gap-2"><strong className="text-sm">镜头 {index + 1} · {shot.id.slice(0, 8)}</strong><div className="flex gap-1"><Button variant="secondary" size="sm" disabled={readOnly || upgradeMode || index === 0} onClick={() => edit(() => reorderShots(draft, shot.id, index - 1))}>上移</Button><Button variant="secondary" size="sm" disabled={readOnly || upgradeMode || index === draft.payload.shots.length - 1} onClick={() => edit(() => reorderShots(draft, shot.id, index + 1))}>下移</Button><Button variant="secondary" size="sm" disabled={readOnly || upgradeMode} onClick={() => edit(() => removeShot(draft, shot.id))}>删除</Button></div></div>
        <div className="mt-3 grid gap-3 sm:grid-cols-2"><Field label="镜头名称"><input data-ai-field={`shots.${shot.id}.label`} aria-label={`镜头 ${index + 1} 名称`} className={inputClass} value={shot.label} disabled={readOnly} onChange={(event) => edit(() => updateShot(draft, shot.id, { label: event.target.value }))} /></Field><Field label="时长（毫秒）"><input data-ai-field={`shots.${shot.id}.duration_ms`} aria-label={`镜头 ${index + 1} 时长`} className={inputClass} type="number" min="1" max="28800000" value={shot.duration_ms} disabled={readOnly} onChange={(event) => edit(() => updateShot(draft, shot.id, { duration_ms: Number(event.target.value) }))} /></Field>
          <Field label="关联脚本"><select aria-label={`镜头 ${index + 1} 关联脚本`} className={inputClass} value={shot.script_block_id || ""} disabled={readOnly} onChange={(event) => edit(() => updateShot(draft, shot.id, { script_block_id: event.target.value || undefined }))}><option value="">未关联</option>{draft.payload.script.blocks.map((block) => <option key={block.id} value={block.id}>段落 {block.order + 1} · {block.text.slice(0, 32)}</option>)}</select></Field>
          <Field label="景别"><select data-ai-field={`shots.${shot.id}.framing`} aria-label={`镜头 ${index + 1} 景别`} className={inputClass} value={shot.framing || ""} disabled={readOnly} onChange={(event) => edit(() => updateShot(draft, shot.id, { framing: event.target.value ? event.target.value as "wide" | "medium" | "close" | "custom" : undefined }))}><option value="">未指定</option><option value="wide">远景</option><option value="medium">中景</option><option value="close">近景</option><option value="custom">自定义</option></select></Field>
          <Field label="转场"><select data-ai-field={`shots.${shot.id}.transition`} aria-label={`镜头 ${index + 1} 转场`} className={inputClass} value={shot.transition || ""} disabled={readOnly} onChange={(event) => edit(() => updateShot(draft, shot.id, { transition: event.target.value ? event.target.value as "cut" | "fade" | "dissolve" : undefined }))}><option value="">未指定</option><option value="cut">切换</option><option value="fade">淡入淡出</option><option value="dissolve">叠化</option></select></Field>
          <Field label="镜头素材（精确版本）"><select aria-label={`镜头 ${index + 1} 素材`} className={inputClass} value={shot.source_material_revision_id || ""} disabled={assetSelectionDisabled || captureShots.some(item => item.id === shot.id)} onChange={(event) => edit(() => bindShotSource(draft, shot.id, assets.find((item) => item.material_revision_id === Number(event.target.value)) || null))}><option value="">未绑定</option>{shot.source_material_revision_id && !sourceAssets.some((item) => item.material_revision_id === shot.source_material_revision_id) && <option value={shot.source_material_revision_id}>已存版本 #{shot.source_material_revision_id}（当前项目库不可用）</option>}{sourceAssets.map((item) => <option key={item.key} value={item.material_revision_id}>{item.title || "未命名"} · {item.kind} #{item.material_revision_id}</option>)}</select></Field>
        </div><Field label="镜头用途"><input data-ai-field={`shots.${shot.id}.purpose`} aria-label={`镜头 ${index + 1} 用途`} className={inputClass} value={shot.purpose || ""} disabled={readOnly} onChange={(event) => edit(() => updateShot(draft, shot.id, { purpose: event.target.value }))} /></Field>
        {captureShots.some(item => item.id === shot.id) && <details className="mt-3 rounded border border-slate-200 p-3"><summary className="cursor-pointer font-medium">拍摄任务书 · 动作、机位与重点</summary><div className="mt-3 grid gap-3 sm:grid-cols-2">
          <Field label="所属场景"><input data-ai-field={`shots.${shot.id}.filming.scene_id`} className={inputClass} maxLength={100} disabled={readOnly || upgradeMode} value={shot.filming?.scene_id || ""} onChange={event => edit(() => setShotFilming(draft, shot.id, { scene_id: event.target.value }))} /></Field>
          <Field label="拍摄顺序（从1开始，独立于成片顺序）"><input data-ai-field={`shots.${shot.id}.filming.filming_order`} className={inputClass} type="number" min={1} max={300} disabled={readOnly || upgradeMode} value={shot.filming?.filming_order === undefined ? "" : shot.filming.filming_order + 1} onChange={event => edit(() => setShotFilming(draft, shot.id, { filming_order: event.target.value === "" ? undefined : Number(event.target.value) - 1 }))} /></Field>
          <Field label="建议拍摄原片时长（毫秒，含动作前后余量）"><input data-ai-field={`shots.${shot.id}.filming.raw_duration_ms`} className={inputClass} type="number" min={1} max={28800000} disabled={readOnly || upgradeMode} value={shot.filming?.raw_duration_ms ?? ""} onChange={event => edit(() => setShotFilming(draft, shot.id, { raw_duration_ms: event.target.value === "" ? undefined : Number(event.target.value) }))} /></Field>
          {filmingFields.map(([key, label]) => <Field key={key} label={label}><textarea data-ai-field={`shots.${shot.id}.filming.${key}`} aria-label={`镜头${index + 1} ${label}`} rows={2} maxLength={2000} className={inputClass} disabled={readOnly || upgradeMode} value={shot.filming?.[key as keyof VideoFilming] ?? ""} onChange={event => edit(() => setShotFilming(draft, shot.id, { [key]: event.target.value }))} /></Field>)}
        </div></details>}
      </div>)}{draft.payload.shots.length === 0 && <p className="text-sm text-slate-500">尚无镜头。</p>}</div>
    </section>}
    </>}
    {show("style", "materials", "edit", "review") && <section aria-label="视频项目素材" className="rounded-xl border border-slate-200 p-4"><div className="flex flex-wrap items-center justify-between gap-3"><h3 className="font-semibold">项目共享素材 · 精确版本</h3><div className="flex flex-wrap gap-2"><Button variant="secondary" size="sm" disabled={assetLoading} onClick={() => setAssetRefresh((value) => value + 1)}>{assetLoading ? "读取项目素材…" : "刷新项目素材"}</Button><Button variant="secondary" size="sm" disabled={readOnly || upgradeMode} onClick={() => { setGenerationOpened(true); setGenerationOpen((value) => !value); }}>{generationOpen ? "收起原生生图 / TTS" : "打开原生生图 / TTS"}</Button></div></div><p className="mt-2 text-xs text-slate-500">新接受的图片、音频或 MP4 需先引用到本项目，再刷新此列表。刷新只读取素材，保留未保存的主稿和现有绑定；选择素材只改本地草稿。</p>{assetIssue && <p role="alert" className="mt-2 text-sm text-rose-700">{assetIssue}。本地草稿仍保留，可重新刷新素材。</p>}{assetNotice && <p role="status" className="mt-2 text-xs text-slate-600">{assetNotice}</p>}

      <details className="mt-3 rounded border border-slate-200 p-3"><summary className="cursor-pointer text-sm">查看素材版本、来源与权利</summary><div className="mt-3 space-y-2">{assets.filter((item) => ["image", "video", "audio"].includes(item.kind)).map((item) => <div key={item.key} className="rounded border border-slate-200 p-2 text-xs"><p>{item.title || "未命名"} · {item.kind} / {item.mime_type || "类型未知"} · Revision #{item.material_revision_id}</p><p>来源：{item.source_type} / {item.provenance?.source_kind || "未知"} · Provider：{item.provenance?.provider_key || "无"}</p><p>公开使用：{item.public_use_allowed ? "允许" : "不允许"} · 模型使用：{item.model_use_allowed ? "允许" : "不允许"} · 权利：{item.rights_status || "未知"}</p><p className="break-all">Hash {item.content_hash}</p></div>)}{assets.length === 0 && !assetIssue && !assetLoading && <p className="text-sm text-slate-500">当前项目没有可见素材。</p>}</div></details>
    </section>}
      {generationOpened && <div hidden={!generationOpen || !show("style", "materials", "edit", "review")} className="mt-3"><Suspense fallback={<p className="text-xs">读取原生生成面板…</p>}><ProviderMediaPanel key={`${projectId}:${unitId}`} projectId={projectId} unitId={unitId} unavailable={readOnly || upgradeMode} onAccepted={() => setAssetRefresh((value) => value + 1)} /></Suspense></div>}
    {show("style", "edit") && <section {...main(-2)} id={sectionId("video-sound")} tabIndex={-1} className="scroll-mt-4 rounded-xl border border-slate-200 p-4"><h3 className="font-semibold">配音、音乐与封面</h3><p className="mt-1 text-xs text-slate-500">这里只引用已进入项目的精确素材；选择 TTS 模式不代表系统已连接或执行语音生成。</p><div className="mt-3 grid gap-3 sm:grid-cols-2">
      <Field label="配音来源类型"><select aria-label="配音来源类型" className={inputClass} value={voiceMode} disabled={assetSelectionDisabled} onChange={(event) => { const mode = event.target.value as "recorded" | "tts"; setVoiceMode(mode); const revision = draft.payload.voice.material_revision_id; const asset = assets.find((item) => item.material_revision_id === revision); if (asset) edit(() => setVoice(draft, mode, asset)); }}><option value="recorded">录音素材</option><option value="tts">已导入 TTS 音频</option></select></Field>
      <Field label="精确配音素材"><select aria-label="精确配音素材" className={inputClass} value={draft.payload.voice.material_revision_id || ""} disabled={assetSelectionDisabled} onChange={(event) => edit(() => setVoice(draft, event.target.value ? voiceMode : "none", assets.find((item) => item.material_revision_id === Number(event.target.value)) || null))}><option value="">无</option>{draft.payload.voice.material_revision_id && !audioAssets.some((item) => item.material_revision_id === draft.payload.voice.material_revision_id) && <option value={draft.payload.voice.material_revision_id}>已存音频 #{draft.payload.voice.material_revision_id}（当前项目库不可用）</option>}{audioAssets.map((item) => <option key={item.key} value={item.material_revision_id}>{item.title || "未命名音频"} #{item.material_revision_id}</option>)}</select></Field>
      <Field label="整片音乐"><select aria-label="整片音乐" className={inputClass} value={draft.payload.music.material_revision_id || ""} disabled={assetSelectionDisabled} onChange={(event) => edit(() => setMusic(draft, assets.find((item) => item.material_revision_id === Number(event.target.value)) || null))}><option value="">无</option>{draft.payload.music.material_revision_id && !audioAssets.some((item) => item.material_revision_id === draft.payload.music.material_revision_id) && <option value={draft.payload.music.material_revision_id}>已存音频 #{draft.payload.music.material_revision_id}（当前项目库不可用）</option>}{audioAssets.map((item) => <option key={item.key} value={item.material_revision_id}>{item.title || "未命名音频"} #{item.material_revision_id}</option>)}</select></Field>
      <Field label="封面图片"><select aria-label="封面图片" className={inputClass} value={draft.payload.cover.material_revision_id || ""} disabled={assetSelectionDisabled} onChange={(event) => edit(() => setCover(draft, assets.find((item) => item.material_revision_id === Number(event.target.value)) || null))}><option value="">无</option>{draft.payload.cover.material_revision_id && !coverAssets.some((item) => item.material_revision_id === draft.payload.cover.material_revision_id) && <option value={draft.payload.cover.material_revision_id}>已存图片 #{draft.payload.cover.material_revision_id}（当前项目库不可用）</option>}{coverAssets.map((item) => <option key={item.key} value={item.material_revision_id}>{item.title || "未命名图片"} #{item.material_revision_id}</option>)}</select></Field>
    </div></section>}
    {show("edit") && unitId && !upgradeMode && <Suspense fallback={<p className="text-xs">读取 ASR 面板…</p>}><AsrSuggestionPanel projectId={projectId} unitId={unitId} masterId={masterId} masterHash={masterHash} savedSourceIds={savedSourceIds} draft={draft} readOnly={readOnly} dirty={dirty} onChange={onChange} /></Suspense>}
    {show("edit") && <SubtitleEditor draft={draft} readOnly={readOnly} edit={edit} />}
    {show("edit", "review") && <details id={sectionId("video-final")} open={finalToolsOpen} onToggle={event => setFinalToolsOpen(event.currentTarget.open)} aria-label="视频高级与兼容工具" className="rounded-xl border border-slate-200 p-4"><summary className="cursor-pointer font-semibold">高级与兼容工具 · 时间线、叠字、最终成片</summary><p className="mt-2 text-xs text-slate-500">保留既有 v2 轨道、裁剪、音量、叠字与精确 MP4 绑定。可先保存脚本与镜头，再准备导演包；这些工具用于细调和最终成片核对。</p><div className="mt-4 space-y-4">
    {show("edit") && <><section className="rounded-xl border border-slate-200 p-4"><h3 className="font-semibold">时间线</h3><p className="mt-1 text-xs text-slate-500">时间用毫秒记录；拖动预览不等于真实视频合成。已放置片段超出时长时保存会被阻断。</p>
      <div className="mt-3 flex flex-wrap items-end gap-2"><Field label="总时长（毫秒）"><input aria-label="视频时间线总时长" className={inputClass} type="number" min="0" max="28800000" value={draft.payload.timeline.duration_ms} disabled={readOnly} onChange={(event) => edit(() => updateTimelineDuration(draft, Number(event.target.value)))} /></Field><Field label="新轨道类型"><select aria-label="新视频轨道类型" className={inputClass} value={newTrackKind} disabled={readOnly} onChange={(event) => setNewTrackKind(event.target.value as VideoTrack["kind"])}><option value="video">画面</option><option value="audio">配音/音效</option><option value="subtitle">字幕</option><option value="overlay">叠层</option><option value="music">音乐</option></select></Field><Button variant="secondary" size="sm" disabled={readOnly} onClick={() => edit(() => addTrack(draft, newTrackKind))}>添加轨道</Button></div>
      <div className="mt-3 space-y-3">{draft.payload.timeline.tracks.map((track) => <TimelineTrackEditor key={track.id} draft={draft} track={track} assets={assets} readOnly={readOnly} edit={edit} />)}{draft.payload.timeline.tracks.length === 0 && <p className="text-sm text-slate-500">尚无轨道。可以先保存脚本/镜头草稿；未完成时间线不会显示成品就绪。</p>}</div>
    </section>
    <OverlayEditor draft={draft} readOnly={readOnly} edit={edit} /></>}
    {show("review") && <section className="rounded-xl border border-amber-200 bg-amber-50 p-4"><h3 className="font-semibold">最终 MP4 与能力状态</h3><p className="mt-1 text-xs">脚本/时间线是本地结构声明，绝不是已渲染视频。最终成片必须从项目可见的真实 MP4 Revision 选择，保存 Master 后再按当前输入哈希明确确认。</p>
      <Field label="真实最终 MP4（精确版本）"><select aria-label="最终 MP4 素材" className={`${inputClass} mt-2`} value={draft.payload.render_asset_ref?.material_revision_id || ""} disabled={assetSelectionDisabled || upgradeMode} onChange={(event) => edit(() => bindFinalRender(draft, assets.find((item) => item.material_revision_id === Number(event.target.value)) || null))}><option value="">{upgradeMode ? "升级首修订禁止继承或绑定成片" : "尚未绑定；不可冻结"}</option>{draft.payload.render_asset_ref && !finalAssets.some((item) => item.material_revision_id === draft.payload.render_asset_ref?.material_revision_id) && <option value={draft.payload.render_asset_ref.material_revision_id}>已存 MP4 #{draft.payload.render_asset_ref.material_revision_id}（当前项目库不可用）</option>}{finalAssets.map((item) => <option key={item.key} value={item.material_revision_id}>{item.title || "未命名 MP4"} · Revision #{item.material_revision_id}{!item.public_use_allowed ? " · 仅本地使用" : ""}</option>)}</select></Field>
      {draft.payload.render_asset_ref && <p className="mt-1 break-all text-xs">当前绑定 #{draft.payload.render_asset_ref.material_revision_id} · Hash {draft.assetRefs.find((ref) => ref.role === "render_output")?.content_hash || "未知"}。绑定本身不生成 render attestation。</p>}
      <p className="mt-2 text-xs text-amber-800">受限已接受成片仅本地使用；公开交付仍需授权。绑定和私有预览不改变素材权利，冻结 Candidate 仍需公开使用授权。</p>
      <div className="mt-2"><Button variant="secondary" size="sm" disabled={!draft.payload.render_asset_ref || !assets.some((item) => item.material_revision_id === draft.payload.render_asset_ref?.material_revision_id && item.mime_type === "video/mp4" && canUseFinalRender(item))} onClick={() => setShowFinalPreview((value) => !value)}>{showFinalPreview ? "关闭精确 MP4 预览" : "验证字节并预览已绑定 MP4"}</Button>{showFinalPreview && <ExactMp4Preview asset={assets.find((item) => item.material_revision_id === draft.payload.render_asset_ref?.material_revision_id)} />}</div>
      <div className="mt-3 grid gap-2 sm:grid-cols-3">{(["video_generation", "tts", "asr"] as const).map((key) => <div key={key} className="rounded bg-white p-2 text-xs"><strong>{key}</strong><p>{capabilities?.[key].verified ? "已验证" : "未验证/不可执行"}</p><p>原因：{capabilities?.[key].reason || capabilityIssue || "状态读取中"}</p></div>)}</div>
    </section>}
    <details className="rounded-xl border border-slate-200 p-3"><summary className="cursor-pointer font-medium">本地结构预览（非成片）</summary><p className="mt-2 text-xs text-amber-800">仅按当前草稿列出可知的脚本、镜头与时间线；不能播放尚未真正合成的画面。</p><ol className="mt-2 list-decimal space-y-1 pl-5 text-sm">{draft.payload.shots.map((shot) => <li key={shot.id}>{shot.label || "未命名镜头"} · {shot.duration_ms} ms · {shot.source_material_revision_id ? `素材 #${shot.source_material_revision_id}` : "无视觉素材"} · {shot.script_block_id ? draft.payload.script.blocks.find((block) => block.id === shot.script_block_id)?.text || "脚本缺失" : "未关联脚本"}</li>)}</ol><p className="mt-2 text-xs">轨道 {draft.payload.timeline.tracks.length} · 片段 {draft.payload.timeline.tracks.reduce((sum, track) => sum + track.items.length, 0)} · 字幕 {draft.payload.subtitles.cues.length} · 叠字 {draft.payload.overlays.length}</p></details>
    </div></details>}
    {view !== "none" && <p className="text-xs text-slate-500">时间线 {draft.payload.timeline.duration_ms} ms · {draft.payload.timeline.tracks.length} 条轨道 · {draft.payload.subtitles.cues.length} 条字幕。未绑定最终成片时不能冻结 Candidate。</p>}
    {issue && <p {...main(0)} role="alert" className="text-sm text-rose-700">{issue}</p>}
  </div></FormAssistancePanel>;
}

function ExactMp4Preview({ asset }: { asset: ProjectAsset | undefined }) {
  const [url, setUrl] = useState("");
  const [issue, setIssue] = useState("");
  useEffect(() => {
    let active = true;
    let objectUrl = "";
    setUrl(""); setIssue("");
    if (!asset || !canUseFinalRender(asset) || asset.mime_type !== "video/mp4") { setIssue("最终 MP4 不可见或已撤权"); return () => { active = false; }; }
    const controller = new AbortController();
    if (asset.provenance?.source_kind === "external_execution") {
      const path = `/api/v1/materials/${asset.material_id}/revisions/${asset.material_revision_id}/preview`;
      fetch(`${path}-session`, { method: "POST", headers: { "X-Studio-User": currentUser() }, signal: controller.signal }).then(async (response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const session = await response.json() as { url: string };
        if (session.url !== path) throw new Error("MP4 预览地址不匹配");
        if (active) setUrl(session.url);
      }).catch((cause) => { if (active && cause?.name !== "AbortError") setIssue(cause instanceof Error ? cause.message : "MP4 不可预览"); });
      return () => { active = false; controller.abort(); };
    }
    fetch(`/api/v1/materials/${asset.material_id}/revisions/${asset.material_revision_id}/raw`, { headers: { "X-Studio-User": currentUser() }, signal: controller.signal }).then(async (response) => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const length = Number(response.headers.get("Content-Length"));
      if (Number.isFinite(length) && length > 100_000_000) throw new Error("MP4 超过本地预览上限；仍可由服务端验证成品包");
      const mime = response.headers.get("Content-Type") || "";
      if (!/^video\/mp4(;|$)/i.test(mime)) throw new Error("素材不是 MP4");
      const bytes = await response.arrayBuffer();
      if (bytes.byteLength > 100_000_000) throw new Error("MP4 超过本地预览上限");
      const digest = Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256", bytes))).map((value) => value.toString(16).padStart(2, "0")).join("");
      if (digest !== asset.content_hash) throw new Error("MP4 字节哈希不匹配");
      if (!active) return;
      objectUrl = URL.createObjectURL(new Blob([bytes], { type: "video/mp4" }));
      setUrl(objectUrl); setIssue("");
    }).catch((cause) => { if (active && cause?.name !== "AbortError") setIssue(cause instanceof Error ? cause.message : "MP4 不可预览"); });
    return () => { active = false; controller.abort(); if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [asset?.material_id, asset?.material_revision_id, asset?.content_hash, asset?.public_use_allowed, asset?.model_use_allowed, asset?.local_final_use_allowed, asset?.mime_type, asset?.provenance?.source_kind]);
  if (issue) return <p role="alert" className="mt-2 text-xs text-rose-800">{issue}</p>;
  if (!url) return <p className="mt-2 text-xs">正在验证精确 MP4 字节并建立预览…</p>;
  return <div className="mt-2"><video controls preload="metadata" className="max-h-96 w-full rounded bg-black" src={url} /><p className="text-xs text-slate-600">已验证所选素材字节与存储 hash 一致；这不证明其与当前 Master 输入匹配，仍需单独确认。</p></div>;
}

function TimelineTrackEditor({ draft, track, assets, readOnly, edit }: { draft: VideoDraft; track: VideoTrack; assets: ProjectAsset[]; readOnly: boolean; edit: (action: () => VideoDraft) => void }) {
  const [start, setStart] = useState(0);
  const [end, setEnd] = useState(1000);
  const [shotId, setShotId] = useState("");
  const [assetId, setAssetId] = useState("");
  const allowedKinds = track.kind === "video" ? ["image", "video"] : track.kind === "audio" || track.kind === "music" ? ["audio"] : [];
  const options = assets.filter((asset) => allowedKinds.includes(asset.kind) && (asset.model_use_allowed || asset.public_use_allowed));
  return <div className="rounded-lg border border-slate-200 p-3"><div className="flex items-center justify-between"><strong className="text-sm">{track.kind} 轨 · {track.order + 1}</strong><Button variant="secondary" size="sm" disabled={readOnly} onClick={() => edit(() => removeTrack(draft, track.id))}>删除轨道</Button></div>
    <div className="mt-2 space-y-2">{track.items.map((item) => <TimelineItemEditor key={item.id} draft={draft} track={track} item={item} readOnly={readOnly} edit={edit} />)}</div>
    <div className="mt-3 flex flex-wrap items-end gap-2"><Field label="新片段开始 ms"><input aria-label={`${track.id} 新片段开始`} className={inputClass} type="number" min="0" value={start} disabled={readOnly} onChange={(event) => setStart(Number(event.target.value))} /></Field><Field label="结束 ms"><input aria-label={`${track.id} 新片段结束`} className={inputClass} type="number" min="1" value={end} disabled={readOnly} onChange={(event) => setEnd(Number(event.target.value))} /></Field>
      {track.kind === "video" && <Field label="镜头"><select aria-label={`${track.id} 新片段镜头`} className={inputClass} value={shotId} disabled={readOnly} onChange={(event) => setShotId(event.target.value)}><option value="">无</option>{draft.payload.shots.map((shot) => <option key={shot.id} value={shot.id}>{shot.label || `镜头 ${shot.order + 1}`}</option>)}</select></Field>}
      {allowedKinds.length > 0 && <Field label="精确素材"><select aria-label={`${track.id} 新片段素材`} className={inputClass} value={assetId} disabled={readOnly} onChange={(event) => setAssetId(event.target.value)}><option value="">无</option>{options.map((asset) => <option key={asset.key} value={asset.material_revision_id}>{asset.title || "未命名"} · {asset.kind} #{asset.material_revision_id}</option>)}</select></Field>}
      <Button variant="secondary" size="sm" disabled={readOnly || draft.payload.timeline.duration_ms === 0} onClick={() => edit(() => addTimelineItem(draft, track.id, { start_ms: start, end_ms: end, ...(shotId ? { shot_id: shotId } : {}), ...(assetId ? { asset: options.find((asset) => asset.material_revision_id === Number(assetId)) } : {}) }))}>添加片段</Button>
    </div>
  </div>;
}

function TimelineItemEditor({ draft, track, item, readOnly, edit }: { draft: VideoDraft; track: VideoTrack; item: VideoTimelineItem; readOnly: boolean; edit: (action: () => VideoDraft) => void }) {
  const [trimStart, setTrimStart] = useState(item.trim_start_ms ?? 0);
  const [trimEnd, setTrimEnd] = useState(item.trim_end_ms ?? item.end_ms - item.start_ms);
  return <div className="rounded bg-slate-50 p-2"><div className="flex flex-wrap items-end gap-2"><span className="text-xs">片段 {item.order + 1} · {item.shot_id ? `镜头 ${item.shot_id.slice(0, 8)}` : ""}{item.material_revision_id ? `素材 #${item.material_revision_id}` : ""}</span><Field label="开始 ms"><input aria-label={`片段 ${item.id} 开始`} className={inputClass} type="number" min="0" value={item.start_ms} disabled={readOnly} onChange={(event) => edit(() => updateTimelineItem(draft, track.id, item.id, { start_ms: Number(event.target.value) }))} /></Field><Field label="结束 ms"><input aria-label={`片段 ${item.id} 结束`} className={inputClass} type="number" min="1" value={item.end_ms} disabled={readOnly} onChange={(event) => edit(() => updateTimelineItem(draft, track.id, item.id, { end_ms: Number(event.target.value) }))} /></Field><Button variant="secondary" size="sm" disabled={readOnly} onClick={() => edit(() => removeTimelineItem(draft, track.id, item.id))}>移除片段</Button></div>
    {item.material_revision_id && <details className="mt-2"><summary className="cursor-pointer text-xs">素材裁剪与音量</summary><div className="mt-2 flex flex-wrap items-end gap-2"><Field label="裁剪开始 ms"><input aria-label={`片段 ${item.id} 裁剪开始`} className={inputClass} type="number" min="0" value={trimStart} disabled={readOnly} onChange={(event) => setTrimStart(Number(event.target.value))} /></Field><Field label="裁剪结束 ms"><input aria-label={`片段 ${item.id} 裁剪结束`} className={inputClass} type="number" min="1" value={trimEnd} disabled={readOnly} onChange={(event) => setTrimEnd(Number(event.target.value))} /></Field><Button variant="secondary" size="sm" disabled={readOnly} onClick={() => edit(() => updateTimelineItem(draft, track.id, item.id, { trim_start_ms: trimStart, trim_end_ms: trimEnd }))}>应用裁剪</Button>{(track.kind === "audio" || track.kind === "music") && <Field label="音量（0–2）"><input aria-label={`片段 ${item.id} 音量`} className={inputClass} type="number" min="0" max="2" step="0.1" value={item.volume ?? 1} disabled={readOnly} onChange={(event) => edit(() => updateTimelineItem(draft, track.id, item.id, { volume: Number(event.target.value) }))} /></Field>}</div></details>}
  </div>;
}

function SubtitleEditor({ draft, readOnly, edit }: { draft: VideoDraft; readOnly: boolean; edit: (action: () => VideoDraft) => void }) {
  const [text, setText] = useState("");
  const [start, setStart] = useState(0);
  const [end, setEnd] = useState(1000);
  const [srt, setSrt] = useState("");
  return <section className="rounded-xl border border-slate-200 p-4"><h3 className="font-semibold">字幕</h3><p className="mt-1 text-xs text-slate-500">时间码使用毫秒；重叠、越界和非连续排序会被拒绝。字幕只是内容声明，不是 ASR 已执行证明。</p>
    <div className="mt-3 space-y-2">{draft.payload.subtitles.cues.map((cue) => <div key={cue.id} className="grid gap-2 rounded bg-slate-50 p-2 sm:grid-cols-[1fr_110px_110px_auto]"><input aria-label={`字幕 ${cue.order + 1} 内容`} className={inputClass} data-ai-field={`subtitles.${cue.id}.text`} value={cue.text} disabled={readOnly} onChange={(event) => edit(() => updateSubtitleCue(draft, cue.id, { text: event.target.value }))} /><input aria-label={`字幕 ${cue.order + 1} 开始`} className={inputClass} type="number" min="0" value={cue.start_ms} disabled={readOnly} onChange={(event) => edit(() => updateSubtitleCue(draft, cue.id, { start_ms: Number(event.target.value) }))} /><input aria-label={`字幕 ${cue.order + 1} 结束`} className={inputClass} type="number" min="1" value={cue.end_ms} disabled={readOnly} onChange={(event) => edit(() => updateSubtitleCue(draft, cue.id, { end_ms: Number(event.target.value) }))} /><Button variant="secondary" size="sm" disabled={readOnly} onClick={() => edit(() => removeSubtitleCue(draft, cue.id))}>删除</Button></div>)}</div>
    <div className="mt-3 flex flex-wrap items-end gap-2"><Field label="字幕文本"><input aria-label="新字幕内容" className={inputClass} value={text} disabled={readOnly} onChange={(event) => setText(event.target.value)} /></Field><Field label="开始 ms"><input aria-label="新字幕开始" className={inputClass} type="number" min="0" value={start} disabled={readOnly} onChange={(event) => setStart(Number(event.target.value))} /></Field><Field label="结束 ms"><input aria-label="新字幕结束" className={inputClass} type="number" min="1" value={end} disabled={readOnly} onChange={(event) => setEnd(Number(event.target.value))} /></Field><Button variant="secondary" size="sm" disabled={readOnly || draft.payload.timeline.duration_ms === 0} onClick={() => edit(() => addSubtitleCue(draft, { text, start_ms: start, end_ms: end }))}>添加字幕</Button></div>
    <details className="mt-3 rounded border border-slate-200 p-2"><summary className="cursor-pointer text-sm">导入 SRT 字幕</summary><p className="mt-1 text-xs text-amber-800">导入会替换当前本地字幕列表；不会直接保存 Master，也不代表 ASR 已执行。时间码必须不重叠且在总时长内。</p><textarea aria-label="SRT 字幕内容" className={`${inputClass} mt-2 font-mono`} rows={5} value={srt} readOnly={readOnly} onChange={(event) => setSrt(event.target.value)} /><Button variant="secondary" size="sm" disabled={readOnly || !srt.trim() || draft.payload.timeline.duration_ms === 0} onClick={() => { if (draft.payload.subtitles.cues.length && !window.confirm("替换当前本地字幕列表？未保存的字幕修改会丢失。")) return; edit(() => importSubtitleSrt(draft, srt)); }}>验证并导入到本地草稿</Button></details>
  </section>;
}

function OverlayEditor({ draft, readOnly, edit }: { draft: VideoDraft; readOnly: boolean; edit: (action: () => VideoDraft) => void }) {
  const [text, setText] = useState("");
  const [start, setStart] = useState(0);
  const [end, setEnd] = useState(1000);
  return <section className="rounded-xl border border-slate-200 p-4"><h3 className="font-semibold">画面叠字</h3><p className="mt-1 text-xs text-slate-500">位置 x/y 使用 0–1 归一化坐标；本地结构预览不代替真实渲染。</p><div className="mt-3 space-y-2">{draft.payload.overlays.map((overlay) => <div key={overlay.id} className="rounded bg-slate-50 p-2"><div className="flex flex-wrap items-end gap-2"><Field label="文字"><input aria-label={`叠字 ${overlay.order + 1} 文字`} className={inputClass} data-ai-field={`overlays.${overlay.id}.text`} value={overlay.text} disabled={readOnly} onChange={(event) => edit(() => updateOverlay(draft, overlay.id, { text: event.target.value }))} /></Field>{(["start_ms", "end_ms", "x", "y"] as const).map((field) => <Field key={field} label={field}><input aria-label={`叠字 ${overlay.order + 1} ${field}`} className={inputClass} type="number" min="0" max={field === "x" || field === "y" ? "1" : "28800000"} step={field === "x" || field === "y" ? "0.05" : "1"} value={overlay[field]} disabled={readOnly} onChange={(event) => edit(() => updateOverlay(draft, overlay.id, { [field]: Number(event.target.value) }))} /></Field>)}<Button variant="secondary" size="sm" disabled={readOnly} onClick={() => edit(() => removeOverlay(draft, overlay.id))}>删除</Button></div></div>)}</div>
    <div className="mt-3 flex flex-wrap items-end gap-2"><Field label="新叠字"><input aria-label="新叠字内容" className={inputClass} value={text} disabled={readOnly} onChange={(event) => setText(event.target.value)} /></Field><Field label="开始 ms"><input aria-label="新叠字开始" className={inputClass} type="number" min="0" value={start} disabled={readOnly} onChange={(event) => setStart(Number(event.target.value))} /></Field><Field label="结束 ms"><input aria-label="新叠字结束" className={inputClass} type="number" min="1" value={end} disabled={readOnly} onChange={(event) => setEnd(Number(event.target.value))} /></Field><Button variant="secondary" size="sm" disabled={readOnly || draft.payload.timeline.duration_ms === 0 || !text.trim()} onClick={() => edit(() => addOverlay(draft, { text, start_ms: start, end_ms: end, x: 0.5, y: 0.5 }))}>添加叠字</Button></div>
  </section>;
}
