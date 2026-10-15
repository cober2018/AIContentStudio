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
  return <div className="space-y-2">{url && actor === currentUser() && <><img className="max-h-72 max-w-full" src={url} alt={`起始图片版本 ${asset.material_revision_id}`} onLoad={onViewed} /><Button size="sm" variant="secondary" disabled={downloading} onClick={() => void downloadImage()}>下载这张精确图片</Button></>}{issue && <p role="alert" className="text-sm text-rose-700">{issue}</p>}</div>;
}

export default function VideoShotMaterialPanel({ projectId, unitId, masterId, dirty, draft, assets, readOnly, onChange, onRefreshAssets }: Props) {
  const base = `/content-projects/${projectId}/units/${unitId}`;
  const navigate = useNavigate();
  const [actor] = useState(currentUser);
  const alive = useRef(true);
  const lock = useRef(false);
  const latestDraft = useRef(draft);
  latestDraft.current = draft;
  const [busy, setBusy] = useState(false);
  const [issue, setIssue] = useState("");
  const [notice, setNotice] = useState("");
  const [instructions, setInstructions] = useState("");
  const [tasks, setTasks] = useState<Task[]>([]);
  const [page, setPage] = useState(0);
  const [imageChoices, setImageChoices] = useState<Record<string, number>>({});
  const [viewedImages, setViewedImages] = useState<Record<string, string>>({});
  const [savedImages, setSavedImages] = useState<Record<string, string>>({});
  const [selected, setSelected] = useState<Record<string, number>>({});
  const [feedbackTime, setFeedbackTime] = useState(0);
  const [feedbackNote, setFeedbackNote] = useState("");
  const [edits, setEdits] = useState<{ output: Output; execution: Execution }[]>([]);
  const safe = () => alive.current && actor === currentUser();
  const disabled = readOnly || busy || !safe();
  const ready = !disabled && !dirty && !!masterId;
  const post: VideoPostproduction = draft.payload.postproduction || { schema: "video.postproduction.v1", phase: "rough_cut", fps: 30, resolution: draft.payload.aspect_ratio[0] >= draft.payload.aspect_ratio[1] ? [1920, 1080] : [1080, 1920], ae_shot_ids: [], feedback: [] };
  useEffect(() => { if (!dirty && masterId) setSavedImages(Object.fromEntries(draft.assetRefs.filter(ref => ref.role === "shot_reference").map(ref => [ref.slot_key, `${ref.material_revision_id}:${ref.content_hash}`]))); }, [dirty, masterId, draft]);
  useEffect(() => { alive.current = true; return () => { alive.current = false; }; }, []);
  async function refresh() {
    const [web, executions] = await Promise.all([api.get<{ items: Task[] }>(`${base}/web-video-executions?limit=20&offset=${page * 20}`), api.get<{ items: Execution[] }>(`${base}/creative-executions?limit=100&offset=0`)]);
    if (!safe()) return;
    setTasks(web.items);
    const details = await Promise.all(executions.items.filter(execution => execution.state === "accepted" && execution.executor_key === "codex-video-production").slice(0, 20).map(execution => api.get<Execution>(`${base}/creative-executions/${execution.id}`)));
    if (!safe()) return;
    setEdits(details.flatMap(execution => (execution.outputs || []).filter(output => output.state === "accepted" && output.role_id === "rough_cut").map(output => ({ execution, output }))));
    onRefreshAssets();
  }
  useEffect(() => { void refresh().catch(cause => { if (safe()) setIssue(cause instanceof Error ? cause.message : "读取任务失败"); }); }, [projectId, unitId, page]);
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
    if (file.size > 512 * 1024 * 1024) { setIssue("视频超过本任务512MiB上限"); return; }
    await action(async () => {
      const data = new FormData(); data.append("file", file); data.append("expected_revision", String(task.execution.revision_no)); data.append("role_id", "clip"); data.append("output_index", "1"); data.append("mime_type", "video/mp4"); data.append("metadata_json", JSON.stringify({ web_provider: task.web_video.provider, summary: "人工回传网页原始视频；未声明不可见型号" }));
      await api.upload(`${base}/creative-executions/${task.execution.id}/uploads`, data);
      if (safe()) { setNotice("视频已暂存，请打开任务预览并明确接受。"); await refresh(); }
    });
  }
  async function applySelected() {
    await action(async () => {
      const current = await api.get<Asset[]>(`/content-projects/${projectId}/shared-assets`);
      if (!safe()) return;
      const currentDraft = latestDraft.current;
      let next = currentDraft;
      for (const [shotId, revisionId] of Object.entries(selected)) {
        if (!currentDraft.payload.shots.some(shot => shot.id === shotId)) throw new Error("所选素材的分镜已变化");
        const asset = current.find(item => item.material_revision_id === revisionId);
        if (!asset) throw new Error("所选素材不再可用，请刷新核对");
        next = bindShotSource(next, shotId, asset);
      }
      onChange(next); setSelected({}); setNotice("选定素材已放入本地主稿草稿；请点击保存内容 Master，才会正式绑定。");
    });
  }
  function updatePost(patch: Partial<VideoPostproduction>, parent?: Asset | null) {
    if (disabled) return;
    try { onChange(setVideoPostproduction(draft, { ...post, ...patch }, parent)); }
    catch (cause) { setIssue(cause instanceof Error ? cause.message : "后期设置无效"); }
  }
  return <section aria-label="分镜素材制作与剪辑交接" className="space-y-4 rounded-xl border border-indigo-200 bg-indigo-50 p-4">
    <div className="flex flex-wrap items-center justify-between gap-2"><h3 className="font-semibold">分镜素材制作与剪辑交接</h3><Button size="sm" variant="secondary" disabled={disabled} onClick={() => void action(refresh)}>刷新任务与素材</Button></div>
    <p className="text-xs">每段素材对应一个镜头。先保存分镜制作设置再准备任务；接受素材后可统一应用，另行保存主稿。网页生成和API图片使用各自的执行流程。</p>
    {dirty && <p className="text-sm text-amber-800">有未保存的主稿修改，请先保存后准备任务；已有任务不会自动重发。</p>}
    {draft.payload.shots.map(shot => {
      const prod = shot.production || defaultProduction();
      const image = assets.find(asset => asset.material_revision_id === (imageChoices[shot.id] ?? prod.reference_material_revision_id) && asset.kind === "image" && asset.model_use_allowed);
      const reference = draft.assetRefs.find(ref => ref.role === "shot_reference" && ref.slot_key === shot.id && ref.material_revision_id === prod.reference_material_revision_id);
      const imageKey = image ? `${image.material_revision_id}:${image.content_hash}` : "";
      const confirmedImageKey = reference ? `${reference.material_revision_id}:${reference.content_hash}` : "";
      const imageSaved = !!confirmedImageKey && savedImages[shot.id] === confirmedImageKey && imageKey === confirmedImageKey;
      const promptCurrent = prod.schema === "video.shot-production.v2" && !!reference && !!prod.prompt?.trim() && prod.prompt_reference?.revision_id === reference.material_revision_id && prod.prompt_reference?.content_hash === reference.content_hash;
      return <fieldset key={shot.id} className="space-y-2 rounded bg-white p-3" disabled={disabled}><legend className="text-sm font-medium">{shot.order + 1}. {shot.label || shot.id} · 使用 {shot.duration_ms / 1000} 秒</legend>
        <div className="grid gap-2 sm:grid-cols-2"><Field label="素材来源"><select className={inputClass} value={prod.source_mode} onChange={event => changeProduction(shot.id, event.target.value === "web_video" ? defaultProduction() : { source_mode: event.target.value as VideoShotProduction["source_mode"] })}><option value="existing">已有素材</option><option value="api_image">API生成图片</option><option value="web_video">网页生成视频</option><option value="ae">AE动效合成</option></select></Field>
        {prod.source_mode === "web_video" && <Field label="生成网站"><select className={inputClass} value={prod.web_provider || "grok"} onChange={event => changeProduction(shot.id, { web_provider: event.target.value as "grok" | "gemini" })}><option value="grok">Grok网页</option><option value="gemini">Gemini网页</option></select></Field>}</div>
        {prod.source_mode !== "existing" && prod.source_mode !== "web_video" && <Field label="图片描述 / 动效要求"><textarea aria-label={`镜头${shot.order + 1}图片描述`} className={inputClass} maxLength={2000} value={prod.prompt || ""} onChange={event => changeProduction(shot.id, { prompt: event.target.value })} /></Field>}
        {prod.source_mode === "web_video" && <>
          <Field label="1. 制作或选择起始图片"><select className={inputClass} value={imageChoices[shot.id] ?? prod.reference_material_revision_id ?? ""} onChange={event => setImageChoices(previous => ({ ...previous, [shot.id]: Number(event.target.value) }))}><option value="">选择已入库且允许模型使用的图片</option>{assets.filter(asset => asset.kind === "image" && asset.model_use_allowed).map(asset => <option key={asset.material_revision_id} value={asset.material_revision_id}>{asset.title || "图片"} #{asset.material_revision_id}</option>)}</select></Field>
          <p className="text-xs">先通过已有素材上传或本页API图片入口制作图片；入库后仍需在此预览并明确选定镜头。</p>
          <ReferenceImage base={base} asset={image} onViewed={() => setViewedImages(previous => previous[shot.id] === imageKey ? previous : { ...previous, [shot.id]: imageKey })} />
          <Button size="sm" variant="secondary" disabled={!image || viewedImages[shot.id] !== imageKey} onClick={() => { changeProduction(shot.id, {}, image); setNotice("已确认本镜头图片，请保存内容 Master；保存后查看此图并编写视频动作提示词。"); }}>确认这张图用于本镜头，再保存主稿</Button>
          <Field label="2. 查看已保存图片后编写视频动作 / 运镜提示词"><textarea aria-label={`镜头${shot.order + 1}视频动作提示词`} className={inputClass} disabled={!imageSaved} maxLength={2000} value={prod.prompt || ""} onChange={event => changeProduction(shot.id, { prompt: event.target.value })} /></Field>
          <p className="text-xs">{!imageSaved ? "请先确认并保存镜头图片。" : promptCurrent ? "视频提示词已对应当前图片；准备任务前请保存主稿。" : "视频提示词尚未确认或图片已变化；查看当前图片，核对保留元素、动作、运镜与节奏后明确确认。"} 生图描述与视频动作提示词分开填写。</p>
          <Button size="sm" variant="secondary" disabled={!imageSaved || !prod.prompt?.trim() || viewedImages[shot.id] !== imageKey} onClick={() => { try { onChange(confirmShotVideoPrompt(draft, shot.id)); setNotice("图片与视频提示词已明确对应，请保存主稿后准备人工图生视频任务。"); } catch (cause) { setIssue(cause instanceof Error ? cause.message : "提示词确认失败"); } }}>已查看图片，确认视频提示词</Button>
          <div className="grid gap-2 sm:grid-cols-2"><Field label="期望生成时长（秒）"><input className={inputClass} type="number" min={1} max={15} value={(prod.requested_generation_duration_ms || 6000) / 1000} onChange={event => changeProduction(shot.id, { requested_generation_duration_ms: Math.round(Number(event.target.value) * 1000) })} /></Field><Field label="原片声音"><select className={inputClass} value={prod.audio_intent || "mute"} onChange={event => changeProduction(shot.id, { audio_intent: event.target.value as "keep" | "mute" })}><option value="mute">剪辑时静音，使用统一旁白</option><option value="keep">保留并审阅原片声音</option></select></Field></div>
          <Button size="sm" disabled={!ready || !promptCurrent} onClick={() => void prepare(shot.id)}>准备此镜头人工图生视频任务</Button></>}
        {prod.source_mode === "api_image" && <p className="text-xs">使用本页“生成素材预览与接受”的图片API；接受后在镜头素材中选择精确版本。</p>}
        {prod.source_mode === "ae" && <p className="text-xs">在下方勾选对应AE分镜，随导演包交给Codex制作并回到达芬奇。</p>}
      </fieldset>;
    })}
    <p className="text-xs">网页视频由你人工生成并回传。平台提供冻结文案和参数；Codex通过MCP或命令行操作平台，负责后续达芬奇与AE制作。</p>
    {instructions && <div className="rounded bg-white p-3"><p className="whitespace-pre-wrap break-all text-xs">{instructions}</p><Button size="sm" variant="secondary" onClick={() => void navigator.clipboard.writeText(instructions).then(() => setNotice("任务说明已复制。"), () => setIssue("复制失败，可选择上方说明复制"))}>复制任务说明</Button></div>}
    <div className="space-y-2"><h4 className="text-sm font-semibold">网页素材任务与回传</h4>{tasks.map(task => <div key={task.execution.id} className="space-y-2 rounded border border-slate-200 bg-white p-3"><p className="text-sm">任务 #{task.execution.id} · {task.web_video.provider} · 镜头 {task.web_video.shot_id} · {STATES[task.execution.state] || task.execution.state}{!task.is_current && " · 来源已过期"}</p><details><summary className="text-xs">冻结文案、提示词与生成参数</summary><p className="whitespace-pre-wrap break-all text-xs">{task.instructions}</p></details><div className="flex flex-wrap gap-2"><ReferenceImage base={base} packageId={task.package_id} asset={assets.find(asset => asset.material_revision_id === task.web_video.reference_material_revision_id && asset.content_hash === task.web_video.reference_assets?.find(ref => ref.material_revision_id === asset.material_revision_id)?.content_hash && asset.model_use_allowed)} /><Button size="sm" variant="secondary" onClick={() => void navigator.clipboard.writeText(task.instructions).then(() => setNotice("此任务的冻结文案和参数已复制，请人工生成后回传原片。"), () => setIssue("复制失败，可展开任务说明复制"))}>复制文案 / 提示词 / 参数</Button><a className="text-sm text-indigo-700 underline" href={task.web_video.website} target="_blank" rel="noreferrer">打开生成网站</a><Button size="sm" variant="secondary" disabled={disabled} onClick={() => navigate(`?panel=execution&execution=${task.execution.id}`)}>查看、预览与接受</Button></div>
      {task.execution.executor_kind === "agent" && task.is_current && task.execution.dispatch_certainty === "not_dispatched" && ["prepared", "claimed", "blocked"].includes(task.execution.state) && <Button size="sm" variant="secondary" disabled={disabled} onClick={() => void action(async () => { await api.post(`${base}/creative-executions/${task.execution.id}/manual-takeover`, { expected_revision: task.execution.revision_no, idempotency_key: crypto.randomUUID() }); if (safe()) { setNotice("原执行已保留，新人工执行沿用冻结输入；请核对网页后回传。"); await refresh(); } })}>明确改为人工操作</Button>}
      {task.execution.executor_kind === "human" && task.is_current && !["accepted", "unknown", "cancelled", "superseded", "rejected"].includes(task.execution.state) && <Field label="回传网页原片"><input aria-label={`任务${task.execution.id}上传视频`} type="file" accept="video/mp4" disabled={disabled} onChange={event => { const file = event.target.files?.[0]; if (file) void upload(task, file); event.target.value = ""; }} /></Field>}
      {task.execution.outputs?.filter(output => output.state === "accepted" && output.material_revision_id).map(output => <Button key={output.id} size="sm" variant="secondary" disabled={disabled || !draft.payload.shots.some(shot => shot.id === task.web_video.shot_id)} onClick={() => setSelected(previous => ({ ...previous, [task.web_video.shot_id]: output.material_revision_id! }))}>{selected[task.web_video.shot_id] === output.material_revision_id ? "已选择" : "选用此候选"} · 素材 #{output.material_revision_id}</Button>)}
    </div>)}{tasks.length === 0 && <p className="text-xs">尚无网页任务。保存分镜制作设置后即可准备。</p>}<div className="flex gap-2"><Button size="sm" variant="secondary" disabled={disabled || page === 0} onClick={() => setPage(value => value - 1)}>上一页</Button><Button size="sm" variant="secondary" disabled={disabled || tasks.length < 20} onClick={() => setPage(value => value + 1)}>下一页</Button><Button size="sm" disabled={disabled || Object.keys(selected).length === 0} onClick={() => void applySelected()}>应用所选素材到主稿草稿</Button></div></div>
    <fieldset className="space-y-2 rounded border border-indigo-200 bg-white p-3" disabled={disabled}><legend className="font-semibold">达芬奇主剪 / AE按需制作</legend><div className="grid gap-2 sm:grid-cols-4"><Field label="制作阶段"><select className={inputClass} value={post.phase} onChange={event => updatePost({ phase: event.target.value as VideoPostproduction["phase"] })}><option value="rough_cut">粗剪</option><option value="refinement">修改 / 精剪</option><option value="final">最终导出</option></select></Field><Field label="帧率"><input className={inputClass} type="number" min={1} max={60} value={post.fps} onChange={event => updatePost({ fps: Number(event.target.value) })} /></Field><Field label="输出宽"><input className={inputClass} type="number" min={16} max={8192} value={post.resolution[0]} onChange={event => updatePost({ resolution: [Number(event.target.value), post.resolution[1]] })} /></Field><Field label="输出高"><input className={inputClass} type="number" min={16} max={8192} value={post.resolution[1]} onChange={event => updatePost({ resolution: [post.resolution[0], Number(event.target.value)] })} /></Field></div>
      <div className="flex flex-wrap gap-3">{draft.payload.shots.map(shot => <label key={shot.id} className="flex items-center gap-1 text-xs"><input type="checkbox" checked={post.ae_shot_ids.includes(shot.id)} onChange={event => updatePost({ ae_shot_ids: event.target.checked ? [...post.ae_shot_ids, shot.id] : post.ae_shot_ids.filter(id => id !== shot.id) })} />AE制作：{shot.label || shot.order + 1}</label>)}</div>
      {(post.ae_compositions || []).map(comp => <div key={comp.shot_id} className="grid gap-2 rounded border p-2 sm:grid-cols-5"><span className="text-xs">合成 {comp.shot_id}</span><Field label="合成时长（秒）"><input className={inputClass} type="number" min={0.001} max={draft.payload.timeline.duration_ms / 1000} value={comp.duration_ms / 1000} onChange={event => updatePost({ ae_compositions: post.ae_compositions!.map(item => item.shot_id === comp.shot_id ? { ...item, duration_ms: Math.round(Number(event.target.value) * 1000) } : item) })} /></Field><Field label="合成宽×高"><input className={inputClass} value={comp.resolution.join("x")} onChange={event => { const parts = event.target.value.split("x").map(Number); if (parts.length === 2 && parts.every(n => Number.isInteger(n) && n >= 16 && n <= 8192)) updatePost({ ae_compositions: post.ae_compositions!.map(item => item.shot_id === comp.shot_id ? { ...item, resolution: [parts[0], parts[1]] } : item) }); }} /></Field><Field label="合成帧率"><input className={inputClass} type="number" min={1} max={60} value={comp.fps} onChange={event => updatePost({ ae_compositions: post.ae_compositions!.map(item => item.shot_id === comp.shot_id ? { ...item, fps: Number(event.target.value) } : item) })} /></Field><label className="text-xs"><input type="checkbox" checked={comp.alpha_required} onChange={event => updatePost({ ae_compositions: post.ae_compositions!.map(item => item.shot_id === comp.shot_id ? { ...item, alpha_required: event.target.checked } : item) })} />需要透明通道（MOV）</label></div>)}
      {post.phase !== "rough_cut" && <><Field label="已接受的父粗剪"><select className={inputClass} value={post.parent_output_id || ""} onChange={event => { const found = edits.find(item => item.output.id === Number(event.target.value)); const asset = assets.find(item => item.material_revision_id === found?.output.material_revision_id); if (found && asset) updatePost({ parent_output_id: found.output.id, parent_output_hash: found.output.content_hash, feedback: [] }, asset); else if (!event.target.value) updatePost({}, null); else setIssue("请先将该粗剪接受并引用到项目，再刷新素材"); }}><option value="">选择确切粗剪版本</option>{edits.map(item => <option key={item.output.id} value={item.output.id}>执行 #{item.execution.id} / 输出 #{item.output.id} · {item.output.content_hash.slice(0, 12)}</option>)}</select></Field><div className="grid gap-2 sm:grid-cols-3"><Field label="反馈时间（秒）"><input className={inputClass} type="number" min={0} max={draft.payload.timeline.duration_ms / 1000} value={feedbackTime} onChange={event => setFeedbackTime(Number(event.target.value))} /></Field><Field label="修改意见"><input className={inputClass} value={feedbackNote} maxLength={2000} onChange={event => setFeedbackNote(event.target.value)} /></Field><Button size="sm" variant="secondary" disabled={!post.parent_output_id || !feedbackNote.trim()} onClick={() => { updatePost({ feedback: [...post.feedback, { time_ms: Math.round(feedbackTime * 1000), note: feedbackNote.trim() }] }); setFeedbackNote(""); }}>添加时间码反馈</Button></div>{post.feedback.map((item, index) => <p key={index} className="text-xs">{item.time_ms / 1000}s：{item.note}</p>)}</>}
      <p className="text-xs">先保存后期设置和精确素材，再准备导演包；接受后的粗剪修改会成为新执行。成片与工程回传后仍需明确审阅。</p><Button size="sm" variant="secondary" onClick={() => updatePost({})}>应用后期设置到草稿</Button><Button size="sm" disabled={!ready || !draft.payload.postproduction || draft.payload.shots.some(shot => !shot.source_material_revision_id)} onClick={() => void prepare()}>准备剪辑任务 / 交给Codex</Button>
    </fieldset>
    {notice && <p role="status" className="text-sm text-emerald-800">{notice}</p>}{issue && <p role="alert" className="text-sm text-rose-700">{issue}</p>}
  </section>;
}
