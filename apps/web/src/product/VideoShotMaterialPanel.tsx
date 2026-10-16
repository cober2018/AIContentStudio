import { useAssistanceFields, useAssistanceFocus } from "./FormAssistancePanel";
import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, currentUser } from "../api";
import { Button, Field, inputClass } from "../components/ui";
import { bindShotSource, confirmShotVideoPrompt, setShotProduction, setVideoPostproduction, type VideoDraft, type VideoPostproduction, type VideoShotProduction } from "./VideoStudioModel";

type Asset = { material_id: number; material_revision_id: number; content_hash: string; kind: string; mime_type?: string | null; title?: string | null; public_use_allowed: boolean; model_use_allowed: boolean };
type Output = { id: number; state: string; material_revision_id: number | null; content_hash: string; role_id: string };
type Execution = { id: number; revision_no: number; state: string; executor_kind: string; executor_key: string; executor_version: string; dispatch_certainty?: string; outputs?: Output[] };
type Handoff = { shot_id: string; provider: string; prompt: string; website: string; source_master_revision_id: number; reference_material_revision_id?: number; reference_assets?: { material_revision_id: number; content_hash: string }[] };
type Task = { execution: Execution; web_video: Handoff; package_id: number; instructions: string; is_current: boolean };
type Prepared = { execution: Execution; instructions: string; website: string | null };
type Props = { projectId: number; unitId: number; masterId: number | null; dirty: boolean; draft: VideoDraft; assets: Asset[]; readOnly: boolean; onChange: (draft: VideoDraft) => void; onRefreshAssets: () => void };
const STATES: Record<string, string> = { prepared: "待人工网页制作", claimed: "已领取", in_progress: "制作中", blocked: "待处理或补交", unknown: "结果待核对，请勿重新生成", result_ready: "待素材审阅", accepted: "素材已接受，待明确绑定", cancelled: "已取消", superseded: "已替代", rejected: "已拒绝", failed_before_dispatch: "提交前失败" };
function defaultProduction(): VideoShotProduction { return { schema: "video.shot-production.v2", source_mode: "web_video", web_provider: "grok", prompt: "", requested_generation_duration_ms: 6000, audio_intent: "mute" }; }

function ReferenceImage({ asset, base, packageId, onViewed }: { asset: Asset | undefined; base: string; packageId?: number; onViewed?: () => void }) {
  const [url, setUrl] = useState("");
  const [issue, setIssue] = useState("");
  const [downloading, setDownloading] = useState(false);
  const [actor] = useState(currentUser);
  const mounted = useRef(true);
  const downloadController = useRef<AbortController>();
  const path = asset ? `/api/v1${base}/web-video-reference-images/${asset.material_revision_id}?content_hash=${asset.content_hash}${packageId ? `&package_id=${packageId}` : ""}` : "";
  const latestPath = useRef(path);
  latestPath.current = path;
  async function loadImage(signal: AbortSignal): Promise<Blob> {
    if (!asset || actor !== currentUser()) throw new Error("当前身份或图片已变化，请刷新");
    const response = await fetch(path, { headers: { "X-Studio-User": actor }, cache: "no-store", signal });
    if (!response.ok) throw new Error(`图片读取失败 HTTP ${response.status}`);
    const mime = response.headers.get("Content-Type") || "";
    if (!mime.startsWith("image/")) throw new Error("参考素材不是图片");
    if (Number(response.headers.get("Content-Length")) > 30 * 1024 * 1024) throw new Error("图片超过读取上限");
    const bytes = await response.arrayBuffer();
    if (bytes.byteLength > 30 * 1024 * 1024) throw new Error("图片超过读取上限");
    const hash = Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256", bytes))).map(value => value.toString(16).padStart(2, "0")).join("");
    if (hash !== asset.content_hash) throw new Error("图片版本哈希不匹配");
    return new Blob([bytes], { type: mime });
  }
  useEffect(() => {
    let active = true;
    let objectUrl = "";
    const controller = new AbortController();
    mounted.current = true;
    setUrl(""); setIssue(""); setDownloading(false);
    if (asset?.kind === "image" && asset.model_use_allowed) void loadImage(controller.signal).then(blob => {
      if (!active || actor !== currentUser()) return;
      objectUrl = URL.createObjectURL(blob); setUrl(objectUrl);
    }).catch(cause => { if (active && cause?.name !== "AbortError") setIssue(cause instanceof Error ? cause.message : "图片读取失败"); });
    return () => { active = false; mounted.current = false; controller.abort(); downloadController.current?.abort(); if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [path, asset?.kind, asset?.model_use_allowed, actor]);
  async function downloadImage() {
    if (!asset || downloading || actor !== currentUser()) return;
    const requestedPath = path;
    const controller = new AbortController(); downloadController.current = controller;
    setDownloading(true); setIssue("");
    try {
      const blob = await loadImage(controller.signal);
      if (!mounted.current || controller.signal.aborted || actor !== currentUser() || latestPath.current !== requestedPath) return;
      const objectUrl = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = objectUrl; link.download = `reference-${asset.material_revision_id}.${blob.type.startsWith("image/jpeg") ? "jpg" : blob.type.startsWith("image/webp") ? "webp" : "png"}`;
      link.click(); setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
    } catch (cause) { if (mounted.current && !controller.signal.aborted && latestPath.current === requestedPath) setIssue(cause instanceof Error ? cause.message : "图片下载失败"); }
    finally { if (mounted.current && latestPath.current === requestedPath) setDownloading(false); }
  }
  if (!asset) return null;
  return <div className="space-y-2">{url && actor === currentUser() && <><a className="block text-xs text-indigo-700 underline" href={url} target="_blank" rel="noreferrer">放大查看图片</a><img className="max-h-72 max-w-full" src={url} alt={`起始图片版本 ${asset.material_revision_id}`} onLoad={onViewed} /><Button size="sm" variant="secondary" disabled={downloading} onClick={() => void downloadImage()}>下载这张精确图片</Button></>}{issue && <p role="alert" className="text-sm text-rose-700">{issue}</p>}</div>;
}

export default function VideoShotMaterialPanel({ projectId, unitId, masterId, dirty, draft, assets, readOnly, onChange, onRefreshAssets }: Props) {
  const base = `/content-projects/${projectId}/units/${unitId}`;
  const navigate = useNavigate();
  const [actor] = useState(currentUser);
  const alive = useRef(true);
  const lock = useRef(false);
  const refreshVersion = useRef(0);
  const latestDraft = useRef(draft);
  latestDraft.current = draft;
  const [busy, setBusy] = useState(false);
  const [issue, setIssue] = useState("");
  const [notice, setNotice] = useState("");
  const [instructions, setInstructions] = useState("");
  const [tasks, setTasks] = useState<Task[]>([]);
  const [preview, setPreview] = useState<{ outputId: number; url: string } | null>(null);
  const [uploadingTask, setUploadingTask] = useState<number | null>(null);
  const [salesBrief, setSalesBrief] = useState<{ core_message?: string; product_context?: { buyer_situation?: string; main_objection?: string; target_duration_seconds?: number } } | null>(null);
  const [imageChoices, setImageChoices] = useState<Record<string, number>>({});
  const [viewedImages, setViewedImages] = useState<Record<string, string>>({});
  const [savedImages, setSavedImages] = useState<Record<string, string>>({});
  const [selected, setSelected] = useState<Record<string, number>>({});
  const [feedbackTime, setFeedbackTime] = useState(0);
  const [feedbackNote, setFeedbackNote] = useState("");
  useAssistanceFields("postproduction", [{ key: "postproduction.feedback_note", label: "后期修改意见", value: feedbackNote, apply: value => setFeedbackNote(String(value ?? "")) }]);
  const focusAssistance = useAssistanceFocus();
  const [edits, setEdits] = useState<{ output: Output; execution: Execution }[]>([]);
  const safe = () => alive.current && actor === currentUser();
  const disabled = readOnly || busy || !safe();
  const ready = !disabled && !dirty && !!masterId;
  const post: VideoPostproduction = draft.payload.postproduction || { schema: "video.postproduction.v1", phase: "rough_cut", fps: 30, resolution: draft.payload.aspect_ratio[0] >= draft.payload.aspect_ratio[1] ? [1920, 1080] : [1080, 1920], ae_shot_ids: [], feedback: [] };
  useEffect(() => { if (!dirty && masterId) setSavedImages(Object.fromEntries(draft.assetRefs.filter(ref => ref.role === "shot_reference").map(ref => [ref.slot_key, `${ref.material_revision_id}:${ref.content_hash}`]))); }, [dirty, masterId, draft]);
  useEffect(() => { alive.current = true; return () => { alive.current = false; }; }, []);
  const taskCurrent = (task: Task) => task.is_current && task.web_video.source_master_revision_id === masterId;
  async function refresh() {
    const version = ++refreshVersion.current;
    const refreshSafe = () => safe() && version === refreshVersion.current;
    const [web, executions] = await Promise.all([api.get<{ items: Task[] }>(`${base}/web-video-executions?limit=50&offset=0`), api.get<{ items: Execution[] }>(`${base}/creative-executions?limit=100&offset=0`)]);
    if (!refreshSafe()) return;
    const allTasks = [...web.items];
    for (let offset = 50; offset <= 10000 && allTasks.length === offset; offset += 50) {
      const older = await api.get<{ items: Task[] }>(`${base}/web-video-executions?limit=50&offset=${offset}`);
      if (!refreshSafe()) return;
      allTasks.push(...older.items);
      if (older.items.length < 50) break;
    }
    if (!refreshSafe()) return;
    setTasks(allTasks);
    const details = await Promise.all(executions.items.filter(execution => execution.state === "accepted" && execution.executor_key === "codex-video-production").slice(0, 20).map(execution => api.get<Execution>(`${base}/creative-executions/${execution.id}`)));
    if (!refreshSafe()) return;
    setEdits(details.flatMap(execution => (execution.outputs || []).filter(output => output.state === "accepted" && output.role_id === "rough_cut").map(output => ({ execution, output }))));
    onRefreshAssets();
  }
  useEffect(() => { void refresh().catch(cause => { if (safe()) setIssue(cause instanceof Error ? cause.message : "读取任务失败"); }); }, [projectId, unitId, masterId]);
  useEffect(() => { let active = true; void api.get<typeof salesBrief>(`/content-projects/${projectId}/brief`).then(value => { if (active && safe()) setSalesBrief(value); }).catch(() => { if (active && safe()) setIssue("商品任务书暂未读取，可刷新后核对销售目标。"); }); return () => { active = false; }; }, [projectId]);
  async function action(run: () => Promise<void>) {
    if (disabled || lock.current) return;
    lock.current = true; setBusy(true); setIssue("");
    try { await run(); } catch (cause) { if (safe()) setIssue(cause instanceof Error ? cause.message : "操作未完成，请核对原任务"); }
    finally { lock.current = false; if (safe()) setBusy(false); }
  }
  function changeProduction(shotId: string, patch: Partial<VideoShotProduction>, reference?: Asset | null) {
    if (disabled) return;
    try {
      const old = draft.payload.shots.find(shot => shot.id === shotId)?.production || defaultProduction();
      const next = { ...old, ...patch, schema: "video.shot-production.v2" as const };
      if (next.source_mode !== "web_video") { delete next.web_provider; delete next.requested_generation_duration_ms; delete next.audio_intent; delete next.prompt_reference; }
      onChange(setShotProduction(draft, shotId, next, reference));
    } catch (cause) { setIssue(cause instanceof Error ? cause.message : "素材设置无效"); }
  }
  async function prepare(shotId?: string) {
    if (!ready) return;
    await action(async () => {
      const identity = `video-prepare:${actor}:${projectId}:${unitId}:${masterId}:${shotId || "edit"}:${shotId ? "manual" : "codex"}`;
      let requestKey: string;
      try {
        requestKey = localStorage.getItem(identity) || crypto.randomUUID();
        localStorage.setItem(identity, requestKey);
        if (localStorage.getItem(identity) !== requestKey) throw new Error();
      } catch { throw new Error("无法保存任务请求标识，请启用浏览器本地存储后重试；尚未准备新任务。"); }
      const result = await api.post<Prepared>(`${base}/${shotId ? "web-video" : "video-edit"}-executions/prepare`, { source_master_revision_id: masterId, idempotency_key: requestKey, ...(shotId ? { shot_id: shotId, execution_mode: "manual" } : {}) });
      if (!safe()) return;
      setInstructions(result.instructions); setNotice(`任务 #${result.execution.id} 已准备；尚未开始外部操作。`);
      await refresh();
      if (!shotId) navigate(`?panel=execution&execution=${result.execution.id}`);
    });
  }
  async function upload(task: Task, file: File) {
    if (!taskCurrent(task) || task.execution.executor_kind !== "human" || ["accepted", "unknown", "cancelled", "superseded", "rejected"].includes(task.execution.state)) { setIssue("此任务当前不能回传，请刷新核对原任务。"); return; }
    if (!file.name.toLowerCase().endsWith(".mp4") || (file.type && file.type !== "video/mp4")) { setIssue("请选择网页下载的原始MP4。"); return; }
    if (file.size > 512 * 1024 * 1024) { setIssue("视频超过本任务512MiB上限"); return; }
    await action(async () => {
      const data = new FormData(); data.append("file", file); data.append("expected_revision", String(task.execution.revision_no)); data.append("role_id", "clip"); data.append("output_index", "1"); data.append("mime_type", "video/mp4"); data.append("metadata_json", JSON.stringify({ web_provider: task.web_video.provider, summary: "人工回传网页原始视频；未声明不可见型号" }));
      setUploadingTask(task.execution.id);
      try { await api.upload(`${base}/creative-executions/${task.execution.id}/uploads`, data); }
      finally { if (safe()) setUploadingTask(null); }
      if (safe()) { setNotice("视频已暂存，请打开任务预览并明确接受。"); await refresh(); }
    });
  }
  async function applySelected(onlyShotId?: string) {
    await action(async () => {
      const current = await api.get<Asset[]>(`/content-projects/${projectId}/shared-assets`);
      if (!safe()) return;
      const currentDraft = latestDraft.current;
      let next = currentDraft;
      for (const [shotId, revisionId] of Object.entries(selected)) {
        if (onlyShotId && shotId !== onlyShotId) continue;
        if (!currentDraft.payload.shots.some(shot => shot.id === shotId)) throw new Error("所选素材的分镜已变化");
        const asset = current.find(item => item.material_revision_id === revisionId);
        if (!asset) throw new Error("所选素材不再可用，请刷新核对");
        next = bindShotSource(next, shotId, asset);
      }
      onChange(next); setSelected(previous => onlyShotId ? Object.fromEntries(Object.entries(previous).filter(([key]) => key !== onlyShotId)) : {}); setNotice("选定素材已放入本地主稿草稿；请点击保存内容 Master，才会正式绑定。");
    });
  }
  function updatePost(patch: Partial<VideoPostproduction>, parent?: Asset | null) {
    if (disabled) return;
    try { onChange(setVideoPostproduction(draft, { ...post, ...patch }, parent)); }
    catch (cause) { setIssue(cause instanceof Error ? cause.message : "后期设置无效"); }
  }
  function renderReturnedTask(task: Task) {
    const canUpload = task.execution.executor_kind === "human" && taskCurrent(task) && !["accepted", "unknown", "cancelled", "superseded", "rejected"].includes(task.execution.state);
    return <div className="space-y-2 rounded-lg border border-slate-200 p-3">
      <p className="text-xs font-medium">任务 #{task.execution.id} · {task.web_video.provider} · {STATES[task.execution.state] || task.execution.state}{!taskCurrent(task) && " · 来源已变化"}</p>
      {canUpload && <div className="space-y-2 rounded border border-dashed border-indigo-300 bg-indigo-50 p-3" onDragOver={event => { if (!disabled) event.preventDefault(); }} onDrop={event => { event.preventDefault(); if (disabled) return; const file = event.dataTransfer.files[0]; if (file) void upload(task, file); }}>
        <Field label={`镜头${task.web_video.shot_id}回传原始MP4`}><input className="w-full text-xs" aria-label={`任务${task.execution.id}上传视频`} type="file" accept="video/mp4,.mp4" disabled={disabled} onChange={event => { const file = event.target.files?.[0]; if (file) void upload(task, file); event.target.value = ""; }} /></Field>
        <p className="text-xs">拖放或选择文件，仅回传到本镜头任务。</p>
        {uploadingTask === task.execution.id && <div role="status"><progress className="w-full" aria-label="视频正在上传" /><p className="text-xs">正在上传并校验，请勿重复提交…</p></div>}
      </div>}
      {task.execution.outputs?.filter(output => output.role_id === "clip").map(output => <div key={output.id} className="space-y-2 rounded bg-slate-50 p-2">
        <p className="text-xs">片段 #{output.id} · {output.state === "accepted" ? "已接受" : output.state === "rejected" ? "需重做" : "待检查"} · {output.content_hash.slice(0, 10)}</p>
        <Button size="sm" variant="secondary" disabled={disabled} onClick={() => void action(async () => {
          const value = await api.post<{ url: string }>(`${base}/creative-executions/${task.execution.id}/outputs/${output.id}/preview-session`, {});
          if (!value.url.startsWith(`/api/v1/content-projects/${projectId}/units/${unitId}/`)) throw new Error("预览地址不属于当前视频单元");
          if (safe()) setPreview({ outputId: output.id, url: value.url });
        })}>在此预览原片</Button>
        {preview?.outputId === output.id && safe() && <div><video className="max-h-72 w-full rounded" src={preview.url} controls preload="metadata" /><Button size="sm" variant="ghost" onClick={() => setPreview(null)}>关闭预览</Button></div>}
        {output.state === "accepted" && output.material_revision_id && <Button size="sm" variant="secondary" disabled={disabled || !draft.payload.shots.some(shot => shot.id === task.web_video.shot_id)} onClick={() => setSelected(previous => ({ ...previous, [task.web_video.shot_id]: output.material_revision_id! }))}>{selected[task.web_video.shot_id] === output.material_revision_id ? "已选择待采用" : "选择这个已接受片段"}</Button>}
      </div>)}
      <Button size="sm" variant="secondary" disabled={disabled || dirty} onClick={() => navigate(`?panel=execution&execution=${task.execution.id}`)}>审阅、接受或反馈重做</Button>
      {task.execution.executor_kind === "agent" && taskCurrent(task) && task.execution.dispatch_certainty === "not_dispatched" && ["prepared", "claimed", "blocked"].includes(task.execution.state) && <Button size="sm" variant="secondary" disabled={disabled} onClick={() => void action(async () => { await api.post(`${base}/creative-executions/${task.execution.id}/manual-takeover`, { expected_revision: task.execution.revision_no, idempotency_key: crypto.randomUUID() }); if (safe()) { setNotice("原执行已保留，人工执行沿用冻结输入。"); await refresh(); } })}>明确改为人工操作</Button>}
    </div>;
  }
  return <section aria-label="分镜素材制作与剪辑交接" className="space-y-4 rounded-xl border border-indigo-200 bg-indigo-50 p-4">
    <div className="flex flex-wrap items-center justify-between gap-2"><h3 className="font-semibold">分镜素材制作与剪辑交接</h3><Button size="sm" variant="secondary" disabled={disabled} onClick={() => void action(refresh)}>刷新任务与素材</Button></div>
    {salesBrief?.product_context && <div className="rounded-lg bg-white p-3 text-sm">
      <div className="flex flex-wrap items-center justify-between gap-2"><strong>这条视频的销售任务</strong><Button size="sm" variant="secondary" disabled={disabled || dirty} onClick={() => navigate(`/projects/${projectId}?tab=brief`)}>编辑商品资料</Button></div>
      <p>使用场景：{salesBrief.product_context.buyer_situation || "待补充"}</p><p>核心购买理由：{salesBrief.core_message || "待补充"}</p><p>主要顾虑：{salesBrief.product_context.main_objection || "待补充"}</p>
      {salesBrief.product_context.target_duration_seconds && <p>计划时长：约 {salesBrief.product_context.target_duration_seconds} 秒</p>}
    </div>}
    <p className="text-xs">按镜头逐行完成：确认并保存关键帧 → 复制提示词到Grok或Gemini网页生成 → 在右侧回传原始MP4 → 审阅接受后采用并保存主稿。上传不代表已接受。</p>
    <p className="text-xs" role="status">已保存选图 {draft.payload.shots.filter(shot => savedImages[shot.id]).length}/{draft.payload.shots.length} · 已回传 {draft.payload.shots.filter(shot => tasks.some(task => task.web_video.shot_id === shot.id && task.execution.outputs?.some(output => output.role_id === "clip"))).length}/{draft.payload.shots.length} · {dirty ? "草稿中已采用" : "已保存采用"} {draft.payload.shots.filter(shot => shot.source_material_revision_id).length}/{draft.payload.shots.length}</p>
    {dirty && <p className="text-sm text-amber-800">有未保存的主稿修改，请先保存后准备任务；已有任务不会自动重发。</p>}
    <div className="hidden grid-cols-[minmax(0,1fr)_minmax(0,1.15fr)_minmax(0,1fr)] gap-4 rounded-lg bg-slate-100 px-4 py-3 text-sm font-semibold lg:grid" aria-hidden="true"><span>镜头与关键帧</span><span>网页提示词 / 制作说明</span><span>回传视频与采用</span></div>
    {draft.payload.shots.map(shot => {
      const prod = shot.production || defaultProduction();
      const image = assets.find(asset => asset.material_revision_id === (imageChoices[shot.id] ?? prod.reference_material_revision_id) && asset.kind === "image" && asset.model_use_allowed);
      const reference = draft.assetRefs.find(ref => ref.role === "shot_reference" && ref.slot_key === shot.id && ref.material_revision_id === prod.reference_material_revision_id);
      const imageKey = image ? `${image.material_revision_id}:${image.content_hash}` : "";
      const confirmedImageKey = reference ? `${reference.material_revision_id}:${reference.content_hash}` : "";
      const imageSaved = !!confirmedImageKey && savedImages[shot.id] === confirmedImageKey && imageKey === confirmedImageKey;
      const promptCurrent = prod.schema === "video.shot-production.v2" && !!reference && !!prod.prompt?.trim() && prod.prompt_reference?.revision_id === reference.material_revision_id && prod.prompt_reference?.content_hash === reference.content_hash;
      const shotTasks = tasks.filter(task => task.web_video.shot_id === shot.id);
      const currentTask = shotTasks.find(taskCurrent) || shotTasks[0];
      const frozenImage = currentTask?.web_video.reference_assets?.[0];
      const imageMatchesTask = !!image && !!frozenImage && image.material_revision_id === frozenImage.material_revision_id && image.content_hash === frozenImage.content_hash;
      const canUseTask = !!currentTask && taskCurrent(currentTask) && imageMatchesTask && imageSaved;
      const narration = draft.payload.script.blocks.find(block => block.id === shot.script_block_id)?.text;
      const bound = assets.find(asset => asset.material_revision_id === shot.source_material_revision_id);
      const rowState = bound ? (dirty ? "素材已放入草稿，待保存" : "已采用素材") : currentTask ? STATES[currentTask.execution.state] || currentTask.execution.state : prod.source_mode !== "web_video" ? "待素材" : !imageSaved ? "待确认并保存关键帧" : !promptCurrent ? "待确认视频提示词" : dirty ? "待保存提示词" : "待准备网页任务";
      return <fieldset key={shot.id} className="min-w-0 rounded-xl border border-slate-200 bg-white p-4" disabled={disabled}>
        <legend className="px-2 text-sm font-semibold">{shot.order + 1}. {shot.label || shot.id} · 剪入 {shot.duration_ms / 1000} 秒 · {rowState}</legend>
        <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.15fr)_minmax(0,1fr)]">
          <section aria-label={`镜头${shot.order + 1}分镜与关键帧`} className="min-w-0 space-y-3">
            <p className="text-sm">{shot.purpose || "尚未填写镜头目的，可在上方分镜编辑中补充。"}</p>
            <details className="text-xs"><summary className="cursor-pointer">旁白与画面信息</summary><p className="mt-2 whitespace-pre-wrap">{narration || "未关联旁白"}</p><p>景别：{({ wide: "远景", medium: "中景", close: "近景", custom: "自定义" } as Record<string, string>)[shot.framing || ""] || "未设置"} · 画幅 {draft.payload.aspect_ratio.join(":")}</p></details>
            <Field label={`镜头${shot.order + 1}素材来源`}><select className={inputClass} value={prod.source_mode} onChange={event => changeProduction(shot.id, event.target.value === "web_video" ? defaultProduction() : { source_mode: event.target.value as VideoShotProduction["source_mode"] })}><option value="existing">真实资料 / 已有素材</option><option value="api_image">API生成图片</option><option value="web_video">网页生成视频</option><option value="ae">AE动效合成</option></select></Field>
            {prod.source_mode === "web_video" && <>
              <Field label={`镜头${shot.order + 1}起始图片`}><select className={inputClass} value={imageChoices[shot.id] ?? prod.reference_material_revision_id ?? ""} onChange={event => setImageChoices(previous => ({ ...previous, [shot.id]: Number(event.target.value) }))}><option value="">选择已入库且允许模型使用的图片</option>{assets.filter(asset => asset.kind === "image" && asset.model_use_allowed).map(asset => <option key={asset.material_revision_id} value={asset.material_revision_id}>{asset.title || "图片"} #{asset.material_revision_id}</option>)}</select></Field>
              <ReferenceImage base={base} asset={image} onViewed={() => setViewedImages(previous => previous[shot.id] === imageKey ? previous : { ...previous, [shot.id]: imageKey })} />
              <Button size="sm" variant="secondary" disabled={!image || viewedImages[shot.id] !== imageKey || imageSaved} onClick={() => { changeProduction(shot.id, {}, image); setNotice("已确认本镜头图片，请保存内容 Master；保存后再编写视频动作提示词。"); }}>{imageSaved ? "当前图片已确认并保存" : "确认这张图用于本镜头"}</Button>
              <p className="text-xs text-slate-500">图片入库不等于选定。换图后需重新核对视频提示词。</p>
            </>}
            {prod.source_mode !== "web_video" && <p className="text-xs text-slate-500">真实操作、实测和参数图直接使用已有素材；不需要网页提示词。</p>}
          </section>
          <section aria-label={`镜头${shot.order + 1}提示词与参数`} className="min-w-0 space-y-3 lg:border-x lg:border-slate-100 lg:px-4">
            {prod.source_mode === "web_video" ? <>
              <Field label={`镜头${shot.order + 1}生成网站`}><select className={inputClass} value={prod.web_provider || "grok"} onChange={event => changeProduction(shot.id, { web_provider: event.target.value as "grok" | "gemini" })}><option value="grok">Grok网页</option><option value="gemini">Gemini网页</option></select></Field>
              <Button size="sm" variant="secondary" disabled={!imageSaved} onClick={() => focusAssistance?.(`shots.${shot.id}.production.prompt`)}>选择此提示词交给AI助手</Button><Field label="基于已确认图片的视频动作 / 运镜提示词"><textarea data-ai-field={`shots.${shot.id}.production.prompt`} aria-label={`镜头${shot.order + 1}视频动作提示词`} className={inputClass} rows={7} disabled={!imageSaved} maxLength={2000} value={prod.prompt || ""} onChange={event => changeProduction(shot.id, { prompt: event.target.value })} /></Field>
              <p className="text-xs text-slate-500">{!imageSaved ? "先确认图片并保存主稿，再写视频提示词。" : promptCurrent ? "提示词对应当前图片；修改后需再次确认并保存。" : "核对要保留的商品细节、一个动作、景别、运镜、光线和节奏。"}</p>
              <Button size="sm" variant="secondary" disabled={!imageSaved || !prod.prompt?.trim() || viewedImages[shot.id] !== imageKey || promptCurrent} onClick={() => { try { onChange(confirmShotVideoPrompt(draft, shot.id)); setNotice("图片与视频提示词已对应，请保存主稿后准备人工任务。"); } catch (cause) { setIssue(cause instanceof Error ? cause.message : "提示词确认失败"); } }}>{promptCurrent ? "提示词已确认" : "确认视频提示词"}</Button>
              <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2"><Field label="期望生成时长（秒）"><input className={inputClass} type="number" min={1} max={15} value={(prod.requested_generation_duration_ms || 6000) / 1000} onChange={event => changeProduction(shot.id, { requested_generation_duration_ms: Math.round(Number(event.target.value) * 1000) })} /></Field><Field label="原片声音"><select className={inputClass} value={prod.audio_intent || "mute"} onChange={event => changeProduction(shot.id, { audio_intent: event.target.value as "keep" | "mute" })}><option value="mute">静音，使用统一旁白</option><option value="keep">保留并审阅</option></select></Field></div>
              <Button size="sm" disabled={!ready || !promptCurrent} onClick={() => void prepare(shot.id)}>准备本镜网页生成包</Button>
              {currentTask && <div className="space-y-2 rounded bg-slate-50 p-3">
                <p className="text-xs">冻结任务 #{currentTask.execution.id}{!taskCurrent(currentTask) && " · 旧版本，只供核对"}</p>
                <details><summary className="cursor-pointer text-xs">查看冻结提示词与完整参数</summary><p className="mt-2 whitespace-pre-wrap break-words text-xs">{currentTask.instructions}</p></details>
                <Button size="sm" variant="secondary" disabled={!ready || !canUseTask} onClick={() => void navigator.clipboard.writeText(currentTask.instructions).then(() => setNotice("已复制本镜生成包。左侧图片与此任务的精确版本一致，请下载并上传该图，再去网站生成。"), () => setIssue("复制失败，请展开生成包手动复制。"))}>复制本镜生成包</Button>
                {ready && canUseTask && <a className="block text-sm text-indigo-700 underline" href={currentTask.web_video.provider === "gemini" ? "https://gemini.google.com/app" : "https://grok.com/"} target="_blank" rel="noreferrer">打开 {currentTask.web_video.provider === "gemini" ? "Gemini" : "Grok"} 网页</a>}
                <p className="text-xs text-slate-500">{!imageMatchesTask ? "当前候选图片与冻结任务不同。请确认并保存选图、提示词后准备新任务；旧任务保留供核对。" : "网页由你操作；复制文字不会自动上传图片。"}</p>
              </div>}
            </> : <>
              <h4 className="text-sm font-medium">{prod.source_mode === "existing" ? "拍摄 / 核验说明" : "图片描述 / 动效要求"}</h4>
              {prod.source_mode !== "existing" && <textarea data-ai-field={`shots.${shot.id}.production.prompt`} aria-label={`镜头${shot.order + 1}图片描述`} rows={6} className={inputClass} maxLength={2000} value={prod.prompt || ""} onChange={event => changeProduction(shot.id, { prompt: event.target.value })} />}
              <p className="text-sm">{prod.source_mode === "existing" ? "使用同款商品的真实资料，核对结构、规格和操作。效果、测量与对比不得用AI情境冒充证明。" : prod.source_mode === "api_image" ? "使用本页原生生图入口制作，审阅并入库后选择精确素材。" : "在下方后期设置选定此镜头，由AE制作包装并回到达芬奇。"}</p>
            </>}
          </section>
          <section aria-label={`镜头${shot.order + 1}回传与采用`} className="min-w-0 space-y-3">
            {currentTask && renderReturnedTask(currentTask)}
            {!currentTask && prod.source_mode === "web_video" && <p className="rounded border border-dashed border-slate-300 p-4 text-sm text-slate-500">完成左侧选图和中间提示词后，本镜头会在这里接收网页原始MP4。</p>}
            {prod.source_mode !== "web_video" && <p className="text-xs">在项目素材库上传真实资料或实拍后，刷新并在这里选用。</p>}
            <Field label={`镜头${shot.order + 1}明确选用素材`}><select className={inputClass} value={selected[shot.id] ?? shot.source_material_revision_id ?? ""} onChange={event => { const revisionId = Number(event.target.value); setSelected(previous => { const next = { ...previous }; if (revisionId) next[shot.id] = revisionId; else delete next[shot.id]; return next; }); }}><option value="">选择本镜头可用素材</option>{assets.filter(asset => ["image", "video"].includes(asset.kind)).map(asset => <option key={asset.material_revision_id} value={asset.material_revision_id}>{asset.title || asset.kind} #{asset.material_revision_id}</option>)}</select></Field>
            <Button size="sm" variant="secondary" disabled={!selected[shot.id]} onClick={() => void applySelected(shot.id)}>采用到本镜头草稿</Button>
            {bound && <p className="text-xs text-emerald-800">{dirty ? "草稿素材" : "已保存素材"}：{bound.title || `#${bound.material_revision_id}`}；采用后需保存主稿。</p>}
            {shotTasks.length > 1 && <details><summary className="cursor-pointer text-xs">本镜头历史任务（{shotTasks.length - 1}）</summary><div className="mt-2 space-y-2">{shotTasks.filter(task => task !== currentTask).map(task => <div key={task.execution.id}>{renderReturnedTask(task)}</div>)}</div></details>}
          </section>
        </div>
      </fieldset>;
    })}
    {draft.payload.shots.length === 0 && <p className="rounded bg-white p-4 text-sm">先在上方保存静态分镜，再逐镜确认图片、准备提示词和回传素材。</p>}
    <p className="text-xs">网页生成由你手工完成；已上传不等于已接受或已采用。准备剪辑前保存已采用的精确素材、旁白与配乐。</p>
    {instructions && <details className="rounded bg-white p-3"><summary className="cursor-pointer text-sm">最近准备的任务说明</summary><p className="whitespace-pre-wrap break-words text-xs">{instructions}</p></details>}
    {tasks.some(task => !draft.payload.shots.some(shot => shot.id === task.web_video.shot_id)) && <details><summary className="cursor-pointer text-sm">已移除镜头的历史任务</summary>{tasks.filter(task => !draft.payload.shots.some(shot => shot.id === task.web_video.shot_id)).map(task => <div key={task.execution.id}>{renderReturnedTask(task)}</div>)}</details>}
    <fieldset className="space-y-2 rounded border border-indigo-200 bg-white p-3" disabled={disabled}><legend className="font-semibold">达芬奇主剪 / AE按需制作</legend><div className="grid gap-2 sm:grid-cols-4"><Field label="制作阶段"><select className={inputClass} value={post.phase} onChange={event => updatePost({ phase: event.target.value as VideoPostproduction["phase"] })}><option value="rough_cut">粗剪</option><option value="refinement">修改 / 精剪</option><option value="final">最终导出</option></select></Field><Field label="帧率"><input className={inputClass} type="number" min={1} max={60} value={post.fps} onChange={event => updatePost({ fps: Number(event.target.value) })} /></Field><Field label="输出宽"><input className={inputClass} type="number" min={16} max={8192} value={post.resolution[0]} onChange={event => updatePost({ resolution: [Number(event.target.value), post.resolution[1]] })} /></Field><Field label="输出高"><input className={inputClass} type="number" min={16} max={8192} value={post.resolution[1]} onChange={event => updatePost({ resolution: [post.resolution[0], Number(event.target.value)] })} /></Field></div>
      <div className="flex flex-wrap gap-3">{draft.payload.shots.map(shot => <label key={shot.id} className="flex items-center gap-1 text-xs"><input type="checkbox" checked={post.ae_shot_ids.includes(shot.id)} onChange={event => updatePost({ ae_shot_ids: event.target.checked ? [...post.ae_shot_ids, shot.id] : post.ae_shot_ids.filter(id => id !== shot.id) })} />AE制作：{shot.label || shot.order + 1}</label>)}</div>
      {(post.ae_compositions || []).map(comp => <div key={comp.shot_id} className="grid gap-2 rounded border p-2 sm:grid-cols-5"><span className="text-xs">合成 {comp.shot_id}</span><Field label="合成时长（秒）"><input className={inputClass} type="number" min={0.001} max={draft.payload.timeline.duration_ms / 1000} value={comp.duration_ms / 1000} onChange={event => updatePost({ ae_compositions: post.ae_compositions!.map(item => item.shot_id === comp.shot_id ? { ...item, duration_ms: Math.round(Number(event.target.value) * 1000) } : item) })} /></Field><Field label="合成宽×高"><input className={inputClass} value={comp.resolution.join("x")} onChange={event => { const parts = event.target.value.split("x").map(Number); if (parts.length === 2 && parts.every(n => Number.isInteger(n) && n >= 16 && n <= 8192)) updatePost({ ae_compositions: post.ae_compositions!.map(item => item.shot_id === comp.shot_id ? { ...item, resolution: [parts[0], parts[1]] } : item) }); }} /></Field><Field label="合成帧率"><input className={inputClass} type="number" min={1} max={60} value={comp.fps} onChange={event => updatePost({ ae_compositions: post.ae_compositions!.map(item => item.shot_id === comp.shot_id ? { ...item, fps: Number(event.target.value) } : item) })} /></Field><label className="text-xs"><input type="checkbox" checked={comp.alpha_required} onChange={event => updatePost({ ae_compositions: post.ae_compositions!.map(item => item.shot_id === comp.shot_id ? { ...item, alpha_required: event.target.checked } : item) })} />需要透明通道（MOV）</label></div>)}
      {post.phase !== "rough_cut" && <><Field label="已接受的父粗剪"><select className={inputClass} value={post.parent_output_id || ""} onChange={event => { const found = edits.find(item => item.output.id === Number(event.target.value)); const asset = assets.find(item => item.material_revision_id === found?.output.material_revision_id); if (found && asset) updatePost({ parent_output_id: found.output.id, parent_output_hash: found.output.content_hash, feedback: [] }, asset); else if (!event.target.value) updatePost({}, null); else setIssue("请先将该粗剪接受并引用到项目，再刷新素材"); }}><option value="">选择确切粗剪版本</option>{edits.map(item => <option key={item.output.id} value={item.output.id}>执行 #{item.execution.id} / 输出 #{item.output.id} · {item.output.content_hash.slice(0, 12)}</option>)}</select></Field><div className="grid gap-2 sm:grid-cols-3"><Field label="反馈时间（秒）"><input className={inputClass} type="number" min={0} max={draft.payload.timeline.duration_ms / 1000} value={feedbackTime} onChange={event => setFeedbackTime(Number(event.target.value))} /></Field><Field label="修改意见"><input data-ai-field="postproduction.feedback_note" className={inputClass} value={feedbackNote} maxLength={2000} onChange={event => setFeedbackNote(event.target.value)} /></Field><Button size="sm" variant="secondary" disabled={!post.parent_output_id || !feedbackNote.trim()} onClick={() => { updatePost({ feedback: [...post.feedback, { time_ms: Math.round(feedbackTime * 1000), note: feedbackNote.trim() }] }); setFeedbackNote(""); }}>添加时间码反馈</Button></div>{post.feedback.map((item, index) => <p key={index} className="text-xs">{item.time_ms / 1000}s：{item.note}</p>)}</>}
      <p className="text-xs">先保存后期设置和精确素材，再准备导演包；接受后的粗剪修改会成为新执行。成片与工程回传后仍需明确审阅。</p><Button size="sm" variant="secondary" onClick={() => updatePost({})}>应用后期设置到草稿</Button><Button size="sm" disabled={!ready || !draft.payload.postproduction || draft.payload.shots.some(shot => !shot.source_material_revision_id)} onClick={() => void prepare()}>准备剪辑任务 / 交给Codex</Button>
    </fieldset>
    {notice && <p role="status" className="text-sm text-emerald-800">{notice}</p>}{issue && <p role="alert" className="text-sm text-rose-700">{issue}</p>}
  </section>;
}
