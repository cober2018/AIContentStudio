import { lazy, Suspense, useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { api, currentUser } from "../api";
import { Button, ErrorBanner, Field, inputClass } from "../components/ui";
import { previewByteHash } from "./previewByteHash";
import VoicePresetPicker, { type VoicePresetOption } from "./VoicePresetPicker";

const ManualChatGPTImagePanel = lazy(() => import("./ManualChatGPTImagePanel"));

export interface Preview {
  stage_id: string;
  content_hash: string;
  mime_type: string;
  kind: string;
  provider_key: string;
  provider_version: string;
  expires_in_seconds: number;
  input_hash?: string;
  candidate_index?: number;
}
export interface Accepted { material_id: number; material_revision_id: number; content_hash: string }
interface GenerationTask {
  task_id: string; state: string; revision: number; provider_key: string; provider_version: string;
  project_id: number | null;
  model_id: string; reason: string | null; has_original_job: boolean;
  content_hash: string | null; mime_type: string | null; material_revision_id: number | null;
  capability: GenerationCapability; selected_profile: string; execution_profile: string;
  plugin_id: string | null; route_reason?: string; frozen_parameters: Record<string, number | string>;
  candidate_count?: number; candidate_mode?: string;
  candidates?: Array<{ index: number; content_hash: string; mime_type: string; size: number }>;
  selected_candidate_index?: number | null;
}
type GenerationCapability = "image_generation" | "video_generation" | "tts";
interface GenerationConfiguration {
  revision: number;
  profiles: Record<string, { enabled: boolean; capability_bindings?: Record<string, { adapter_key: string; adapter_version: string; model_id: string }>; multimedia_controls?: Record<string, { supported_fields: string[]; candidate_counts: number[]; reference_images?: boolean }> }>;
  voice_catalog?: VoicePresetOption[];
  policies: { limits: Partial<Record<GenerationCapability, { max_pixels?: number; max_seconds?: number; timeout_seconds: number }>> };
}
interface BatchCandidate extends Preview { url: string }
const reasons: Record<string, string> = {
  generation_schema_unavailable: "本地任务表尚未迁移。此处不会自动升级数据库或提交生成。",
  generation_receipt_key_unavailable: "持久任务签名密钥尚未配置或已撤销，不能执行或接受。",
  credential_continuity_unverified: "无法证明仍是原认证上下文。保留原任务，不查询、不重发。",
  generation_original_job_unknown: "原任务编号未知，需人工核对供应商，不会重新提交。",
  generation_task_required: "MiniMax CLI 需通过持久任务入口，不能使用旧临时生成入口。",
  generation_query_interval_required: "查询过于频繁，请至少间隔 5 秒后再查询原任务。",
  generation_revision_conflict: "任务已更新。请刷新状态，不要重新生成。",
  generation_video_duration_unverified: "实际视频时长无法验证，结果不能作为有效素材接受。",
  generation_output_limit_exceeded: "实际输出超过本次授权上限，未入库。",
  generation_local_storage_required: "持久任务当前需要本地私有存储，不会改用网络存储。",
  durable_provider_dispatch_unavailable: "此 Provider 尚未接入持久任务执行，不会发送生成请求。",
  execution_plan_stale: "发送前配置已变化。原任务保留，不能自动改用新的执行计划。",
  capability_unavailable: "当前生图能力未配置或不可执行，请先在设置中配置真实 Provider。",
  capability_plugin_unavailable: "这项能力没有可用的模型或插件，请先在模型与 AI 设置中配置；没有发送请求或创建结果。",
  provider_preview_unavailable_or_expired: "预览已过期或不属于当前用户，请明确重新生成。",
  provider_outcome_unknown: "生成结果未知。未入库，请先核对 Provider，不会自动重试。",
  provider_runtime_changed: "Provider 配置已变化，此结果不能接受。保留原任务，不自动重新生成。",
  provider_output_decode_failed: "Provider 返回的媒体不能真实解码，未保存任何素材。",
  provider_attribution_required: "此许可要求填写作者及署名。",
  multimedia_batch_incomplete: "候选结果未完整返回，未接受任何图片。",
  multimedia_custom_batch_requires_declared_composition: "指定单一模型不允许隐式批量；请改用明确的组合配置。",
};
const routeLabels: Record<string, string> = {
  selected_model_binding: "所选模型自身",
  explicit_workflow_binding: "工作流显式模型",
  explicit_plugin_binding: "显式能力插件",
  authorized_plugin_fallback: "已授权自动插件路由",
};

export interface ObservedLicense {
  title: string;
  license_code: string;
  license_evidence_hash: string;
  attribution_text: string | null;
}

export default function ProviderMediaPanel({ initialPreview, initialTaskId, observedLicense, onDismiss, mediaOrigin, unavailable = false, onAccepted, projectId, unitId }: { initialPreview?: Preview; initialTaskId?: string; observedLicense?: ObservedLicense; onDismiss?: () => void; mediaOrigin?: "renderer"; unavailable?: boolean; onAccepted?: (accepted: Accepted) => void | Promise<void>; projectId?: number; unitId?: number }) {
  const queryClient = useQueryClient();
  const [prompt, setPrompt] = useState("");
  const [imageMode, setImageMode] = useState<"automatic" | "chatgpt_manual">("automatic");
  const [title, setTitle] = useState(observedLicense?.title ?? "");
  const [preview, setPreview] = useState<Preview | undefined>(initialPreview);
  const [batchCandidates, setBatchCandidates] = useState<BatchCandidate[]>([]);
  const [accepted, setAccepted] = useState<Accepted>();
  const [url, setUrl] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [tasks, setTasks] = useState<GenerationTask[]>([]);
  const [task, setTask] = useState<GenerationTask>();
  const [taskReadOnly, setTaskReadOnly] = useState(false);
  const [configuration, setConfiguration] = useState<GenerationConfiguration>();
  const [selectedProfile, setSelectedProfile] = useState("");
  const [capability, setCapability] = useState<GenerationCapability>("image_generation");
  const [outputLimit, setOutputLimit] = useState("");
  const [candidateCount, setCandidateCount] = useState(1);
  const [aspectRatio, setAspectRatio] = useState("1:1");
  const [voiceId, setVoiceId] = useState("");
  const [voiceRate, setVoiceRate] = useState(1);
  const [advanced, setAdvanced] = useState(false);
  const [configurationMode, setConfigurationMode] = useState<"auto" | "custom">("auto");
  const [prepared, setPrepared] = useState<GenerationTask>();
  const [sendConfirmed, setSendConfirmed] = useState(false);
  const preparation = useRef<{ input: string; key: string }>();
  const [license, setLicense] = useState(observedLicense?.license_code ?? "provider_terms");
  const [licenseHash, setLicenseHash] = useState(observedLicense?.license_evidence_hash ?? "");
  const [attribution, setAttribution] = useState(observedLicense?.attribution_text ?? "");
  const [confirmed, setConfirmed] = useState(false);
  const [rights, setRights] = useState({ public: false, model: false, commercial: false });
  const objectUrl = useRef("");
  const candidateUrls = useRef<string[]>([]);
  const previewRead = useRef(0);
  const mounted = useRef(true);
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; previewRead.current += 1; if (objectUrl.current) URL.revokeObjectURL(objectUrl.current); candidateUrls.current.forEach(URL.revokeObjectURL); }; }, []);
  useEffect(() => {
    if (initialTaskId) void openTask({ task_id: initialTaskId } as GenerationTask);
  }, [initialTaskId]);
  useEffect(() => {
    if (!configuration || prepared || outputLimit) return;
    const limit = configuration.policies.limits[capability];
    const ceiling = capability === "image_generation" ? limit?.max_pixels : limit?.max_seconds;
    if (ceiling) setOutputLimit(String(Math.min(ceiling, capability === "image_generation" ? 1024 * 1024 : 120)));
  }, [capability, configuration?.revision, prepared, outputLimit]);
  useEffect(() => {
    if (!initialPreview) return;
    const controller = new AbortController();
    setBusy(true);
    void (async () => {
      try {
        const response = await fetch(`/api/v1/provider-media/${initialPreview.stage_id}/raw`, { signal: controller.signal, headers: { "X-Studio-User": currentUser() }, cache: "no-store" });
        if (!response.ok) throw new Error("预览不可用或已过期，请重新明确选择候选。");
        const blob = await response.blob();
        if (controller.signal.aborted) return;
        objectUrl.current = URL.createObjectURL(blob); setUrl(objectUrl.current);
      } catch (cause) { if (!controller.signal.aborted) report(cause); }
      finally { if (!controller.signal.aborted) setBusy(false); }
    })();
    return () => controller.abort();
  }, [initialPreview]);
  function report(cause: unknown) {
    const reason = cause instanceof Error ? cause.message : "请求失败";
    setError(reasons[reason] ?? reason);
  }
  function reset() {
    previewRead.current += 1;
    if (onDismiss) { onDismiss(); return; }
    if (objectUrl.current) URL.revokeObjectURL(objectUrl.current);
    objectUrl.current = ""; setUrl(""); setPreview(undefined); setAccepted(undefined); setTask(undefined); setTaskReadOnly(false);
    clearCandidates();
    setConfirmed(false); setRights({ public: false, model: false, commercial: false }); setError("");
  }
  async function refreshTasks() {
    const actor = currentUser();
    setBusy(true); setError("");
    try {
      const result = await api.get<GenerationTask[]>("/generation-tasks");
      if (mounted.current && actor === currentUser()) {
        setTasks(result);
        setPrepared((old) => old ? result.find((item) => item.task_id === old.task_id) ?? old : old);
      }
    }
    catch (cause) { if (mounted.current && actor === currentUser()) report(cause); }
    finally { if (mounted.current) setBusy(false); }
  }
  async function readConfiguration() {
    const actor = currentUser();
    setBusy(true); setError("");
    try {
      const result = await api.get<GenerationConfiguration>("/settings/model-capabilities");
      if (mounted.current && actor === currentUser()) { setConfiguration(result); setSendConfirmed(false); }
    } catch (cause) { if (mounted.current && actor === currentUser()) report(cause); }
    finally { if (mounted.current) setBusy(false); }
  }
  async function prepareTask() {
    if (!selectedProfile || !configuration || prepared || !validControls) return;
    const actor = currentUser();
    const request = { capability, selected_profile: selectedProfile, prompt: prompt.trim(), configuration_mode: capability === "tts" ? "custom" : configurationMode, ...(projectId ? { project_id: projectId } : {}),
      parameters: { items: capability === "image_generation" ? candidateCount : 1, ...(capability === "image_generation"
        ? { pixels: Number(outputLimit), ...(controls?.supported_fields.includes("aspect_ratio") ? { aspect_ratio: aspectRatio } : {}) }
        : capability === "tts" ? { seconds: Number(outputLimit), ...(voiceControlsSupported ? { voice_id: voiceId, rate: voiceRate } : {}) }
        : { seconds: Number(outputLimit) }) } };
    const input = JSON.stringify({ actor, request });
    if (preparation.current?.input !== input) preparation.current = { input, key: crypto.randomUUID() };
    setBusy(true); setError("");
    try {
      const result = await api.post<GenerationTask>("/generation-tasks", { ...request, idempotency_key: preparation.current.key });
      if (!mounted.current || actor !== currentUser()) return;
      setPrepared(result); setSendConfirmed(false);
      setTasks((old) => [result, ...old.filter((item) => item.task_id !== result.task_id)]);
      if (result.reason) setError(reasons[result.reason] ?? result.reason);
    } catch (cause) { if (mounted.current && actor === currentUser()) report(cause); }
    finally { if (mounted.current) setBusy(false); }
  }
  function clearCandidates() {
    candidateUrls.current.forEach(URL.revokeObjectURL); candidateUrls.current = []; setBatchCandidates([]);
  }
  async function loadTaskCandidates(result: GenerationTask, actor: string, readId: number) {
    if (!result.candidates?.length) return false;
    const candidates: BatchCandidate[] = [];
    try {
      for (const item of result.candidates) {
        const response = await fetch(`/api/v1/generation-tasks/${encodeURIComponent(result.task_id)}/raw?candidate_index=${item.index}`, { headers: { "X-Studio-User": actor }, cache: "no-store" });
        if (!response.ok) throw new Error("候选预览读取失败；持久结果未通过校验。");
        const bytes = await response.arrayBuffer();
        if (bytes.byteLength !== item.size || await previewByteHash(bytes) !== item.content_hash || !/^image\/(png|jpeg|webp)$/.test(item.mime_type)) throw new Error("候选字节、格式或哈希不一致，不能选择。");
        if (!mounted.current || actor !== currentUser() || readId !== previewRead.current) return true;
        candidates.push({ stage_id: result.task_id, content_hash: item.content_hash, mime_type: item.mime_type, kind: "image", provider_key: result.provider_key, provider_version: result.provider_version, expires_in_seconds: 0, candidate_index: item.index, url: URL.createObjectURL(new Blob([bytes], { type: item.mime_type })) });
      }
      clearCandidates(); candidateUrls.current = candidates.map(item => item.url);
      setBatchCandidates([...candidates]); setPreview(undefined); setUrl("");
      candidates.length = 0;
    } finally { candidates.forEach(item => URL.revokeObjectURL(item.url)); }
    return true;
  }
  async function executePrepared() {
    if (!prepared || prepared.state !== "prepared" || prepared.reason || !sendConfirmed) return;
    const actor = currentUser();
    setBusy(true); setError(""); setSendConfirmed(false);
    try {
      const result = await api.post<GenerationTask>(`/generation-tasks/${prepared.task_id}/execute`, { expected_revision: prepared.revision });
      if (!mounted.current || actor !== currentUser()) return;
      setPrepared(result);
      setTasks((old) => old.map((item) => item.task_id === result.task_id ? result : item));
      if (result.state === "result_ready") await openTask(result);
      if (result.reason) setError(reasons[result.reason] ?? result.reason);
    } catch (cause) {
      if (mounted.current && actor === currentUser()) {
        setPrepared((old) => old ? { ...old, state: "unknown", reason: "provider_outcome_unknown" } : old);
        setTasks((old) => old.map((item) => item.task_id === prepared.task_id
          ? { ...item, state: "unknown", reason: "provider_outcome_unknown" } : item));
        report(cause);
        // An HTTP failure does not prove a send; only the durable task decides.
        try {
          const persisted = await api.get<GenerationTask>(`/generation-tasks/${prepared.task_id}`);
          if (!mounted.current || actor !== currentUser()) return;
          setPrepared((old) => old?.task_id === persisted.task_id ? persisted : old);
          setTasks((old) => old.map((item) => item.task_id === persisted.task_id ? persisted : item));
        } catch {
          // A failed read leaves the outcome unknown and never authorizes a send.
        }
      }
    }
    finally { if (mounted.current) setBusy(false); }
  }
  async function openTask(selected: GenerationTask, recover = false) {
    const actor = currentUser();
    const readId = ++previewRead.current;
    clearCandidates();
    if (objectUrl.current) URL.revokeObjectURL(objectUrl.current);
    objectUrl.current = ""; setUrl(""); setPreview(undefined); setTask(undefined); setAccepted(undefined); setTaskReadOnly(true);
    setConfirmed(false); setRights({ public: false, model: false, commercial: false });
    setTitle(""); setLicense("provider_terms"); setLicenseHash(""); setAttribution("");
    setBusy(true); setError("");
    try {
      let result = await api.get<GenerationTask>(`/generation-tasks/${selected.task_id}`);
      if (!mounted.current || actor !== currentUser() || readId !== previewRead.current) return;
      setTask(result);
      let readOnly = false;
      if (result.project_id != null) {
        const project = await api.get<{ status: string }>(`/content-projects/${result.project_id}`);
        readOnly = project.status === "archived";
      }
      if (!mounted.current || actor !== currentUser() || readId !== previewRead.current) return;
      setTaskReadOnly(readOnly);
      if (recover) {
        if (unavailable || readOnly) throw new Error("此任务仅供查看，不能查询供应商或接受新的结果。");
        result = await api.post<GenerationTask>(`/generation-tasks/${selected.task_id}/recover`, { expected_revision: result.revision });
        if (!mounted.current || actor !== currentUser() || readId !== previewRead.current) return;
      }
      setTasks((old) => old.map((item) => item.task_id === result.task_id ? result : item));
      setPrepared((old) => old?.task_id === result.task_id ? result : old);
      setTask(result);
      if (await loadTaskCandidates(result, actor, readId)) {
        if (!mounted.current || actor !== currentUser() || readId !== previewRead.current) return;
        setTask(result); setAccepted(undefined); setConfirmed(false); setRights({ public: false, model: false, commercial: false });
        return;
      }
      if (!["result_ready", "accepted"].includes(result.state) || !result.content_hash || !result.mime_type) {
        if (objectUrl.current) URL.revokeObjectURL(objectUrl.current);
        objectUrl.current = ""; setUrl(""); setPreview(undefined);
        if (result.reason) setError(reasons[result.reason] ?? result.reason);
        return;
      }
      const response = await fetch(`/api/v1/generation-tasks/${result.task_id}/raw`, { headers: { "X-Studio-User": actor }, cache: "no-store" });
      if (!response.ok) throw new Error("持久结果校验失败。保留原任务，不自动重新生成。");
      const bytes = await response.arrayBuffer();
      if (await previewByteHash(bytes) !== result.content_hash) throw new Error("持久结果字节与冻结哈希不一致。");
      if (!mounted.current || actor !== currentUser() || readId !== previewRead.current) return;
      if (objectUrl.current) URL.revokeObjectURL(objectUrl.current);
      objectUrl.current = URL.createObjectURL(new Blob([bytes], { type: result.mime_type })); setUrl(objectUrl.current);
      setTask(result); setAccepted(undefined); setConfirmed(false); setRights({ public: false, model: false, commercial: false });
      setPreview({ stage_id: result.task_id, content_hash: result.content_hash, mime_type: result.mime_type,
        kind: result.mime_type.startsWith("image/") ? "image" : result.mime_type.startsWith("audio/") ? "audio" : "video",
        provider_key: result.provider_key, provider_version: result.provider_version, expires_in_seconds: 0 });
    } catch (cause) { if (mounted.current && actor === currentUser() && readId === previewRead.current) report(cause); }
    finally { if (mounted.current && readId === previewRead.current) setBusy(false); }
  }
  async function generate() {
    setBusy(true); setError("");
    try {
      const result = await api.post<Preview>("/materials/generate", { prompt });
      if (!mounted.current) return;
      setPreview(result);
      const response = await fetch(`/api/v1/provider-media/${result.stage_id}/raw`, { headers: { "X-Studio-User": currentUser() }, cache: "no-store" });
      if (!response.ok) throw new Error("预览读取失败；没有入库，请重新生成预览。");
      const blob = await response.blob();
      if (!mounted.current) return;
      objectUrl.current = URL.createObjectURL(blob); setUrl(objectUrl.current);
    } catch (cause) { if (mounted.current) report(cause); }
    finally { if (mounted.current) setBusy(false); }
  }
  async function accept() {
    if (!preview || unavailable || taskReadOnly || busy || accepted) return;
    if (task && (task.task_id !== preview.stage_id || task.state !== "result_ready"
      || task.candidates?.length && !task.candidates.some(item => item.index === (preview.candidate_index ?? 0) && item.content_hash === preview.content_hash)
      || !task.candidates?.length && task.content_hash !== preview.content_hash)) return;
    setBusy(true); setError("");
    try {
      const saved = await api.post<Accepted>(task ? `/generation-tasks/${task.task_id}/accept` : `/provider-media/${preview.stage_id}/accept`, {
        ...(task ? { expected_revision: task.revision, candidate_index: preview.candidate_index ?? 0 } : {}),
        confirmed, title: title.trim(), license_code: license, license_evidence_hash: licenseHash.trim(),
        public_use_allowed: rights.public, model_use_allowed: rights.model, commercial_use_allowed: rights.commercial,
        attribution_text: attribution.trim() || null,
      });
      if (!mounted.current) return;
      setAccepted(saved);
      await onAccepted?.(saved);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["system-library"] }),
        queryClient.invalidateQueries({ queryKey: ["materials"] }),
      ]);
    } catch (cause) { if (mounted.current) report(cause); }
    finally { if (mounted.current) setBusy(false); }
  }
  const taskAlreadyAccepted = task?.state === "accepted";
  const previewIsAccepted = Boolean(accepted) || taskAlreadyAccepted
    && (!task?.candidates?.length || task.selected_candidate_index === preview?.candidate_index);
  const disabled = unavailable || taskReadOnly || busy || accepted !== undefined || taskAlreadyAccepted;
  const configuredLimit = configuration?.policies.limits[capability];
  const maximum = capability === "image_generation" ? configuredLimit?.max_pixels : configuredLimit?.max_seconds;
  const validLimit = Number.isSafeInteger(Number(outputLimit)) && Number(outputLimit) > 0 && maximum !== undefined && Number(outputLimit) <= maximum;
  const selectedBinding = configuration?.profiles[selectedProfile]?.capability_bindings?.[capability];
  const controls = configuration?.profiles[selectedProfile]?.multimedia_controls?.[capability];
  const candidateCounts = controls?.candidate_counts?.length ? controls.candidate_counts : [1];
  const voiceControlsSupported = !!controls?.supported_fields.includes("voice_id") && controls.supported_fields.includes("rate");
  const compatibleVoices = (configuration?.voice_catalog || []).filter(item => item.profile_id === selectedProfile
    && item.provider_key === selectedBinding?.adapter_key && item.provider_version === selectedBinding?.adapter_version
    && item.model_id === selectedBinding?.model_id).sort((a, b) => Number(b.favorite) - Number(a.favorite) || a.label.localeCompare(b.label));
  const validControls = capability === "image_generation" ? candidateCounts.includes(candidateCount)
    : capability === "tts" ? voiceControlsSupported && compatibleVoices.some(item => item.voice_id === voiceId) : true;
  const canChooseMode = !initialPreview && !initialTaskId && !observedLicense && !mediaOrigin;
  const modeSelector = <Field label="图片生成方式"><select className={inputClass} value={imageMode} disabled={busy || !!prepared || !!preview || !!batchCandidates.length} onChange={event => setImageMode(event.target.value as "automatic" | "chatgpt_manual")}><option value="automatic">已配置模型 / 插件（自动生成）</option><option value="chatgpt_manual">ChatGPT（手动生图）</option></select></Field>;
  if (canChooseMode && imageMode === "chatgpt_manual") return <section aria-label="生成预览与接受" className="space-y-4 rounded-xl border bg-white p-5"><h2 className="font-semibold">ChatGPT：手动生成，上传后选择</h2>{modeSelector}<Suspense fallback={<p className="text-sm">加载手动交接入口…</p>}><ManualChatGPTImagePanel projectId={projectId} unitId={unitId} readOnly={unavailable} onAccepted={onAccepted} /></Suspense></section>;
  return <section aria-label={mediaOrigin === "renderer" ? "渲染预览与接受" : observedLicense ? "素材预览与接受" : "生成预览与接受"} className="space-y-4 rounded-xl border bg-white p-5">
    <h2 className="font-semibold">{mediaOrigin === "renderer" ? "渲染图片：先预览，再接受" : observedLicense ? "搜索素材：核对许可后接受" : "AI 素材：先预览，再接受"}</h2>
    {canChooseMode && modeSelector}
    {!initialPreview && !initialTaskId && !observedLicense && !mediaOrigin && <div className="space-y-2">
      <Button variant="secondary" disabled={busy || unavailable} onClick={() => void readConfiguration()}>读取已登记模型与生成限额（不生成）</Button>
      {configuration && <div className="space-y-2 rounded border p-3">
        <Field label="本次所选模型配置"><select className={inputClass} value={selectedProfile} disabled={busy || !!prepared} onChange={(event) => { setSelectedProfile(event.target.value); setCandidateCount(1); setVoiceId(""); setSendConfirmed(false); }}><option value="">请选择，不修改默认模型</option>{Object.entries(configuration.profiles).filter(([, profile]) => profile.enabled).map(([id, profile]) => <option key={id} value={id}>{profile.capability_bindings?.[capability]?.model_id || id} · {id}</option>)}</select></Field>
        {capability !== "tts" && <Field label="模型选择方式"><select className={inputClass} disabled={busy || !!prepared} value={configurationMode} onChange={e => { setConfigurationMode(e.target.value as "auto" | "custom"); setSendConfirmed(false); }}><option value="auto">自动（仅已授权路由）</option><option value="custom">指定模型（不可用就停止）</option></select></Field>}
        <Button size="sm" variant="secondary" onClick={() => setAdvanced(value => !value)}>{advanced ? "收起高级设置" : "高级设置"}</Button>
        {advanced && <div className="space-y-2 rounded-lg bg-slate-50 p-3 text-xs"><p>精确绑定：{selectedBinding ? `${selectedBinding.adapter_key}@${selectedBinding.adapter_version} / ${selectedBinding.model_id} / ${selectedProfile}` : "此模型尚未登记当前生成能力"}</p><p>此适配器支持：{controls?.supported_fields.join("、") || "未声明，无法使用高级参数"}。未支持的参数不会显示或静默忽略。</p>{capability === "image_generation" && <p>参考图：{controls?.reference_images ? "支持精确素材引用" : "此适配器未接入，不发送参考图"}；具体像素受下方授权上限和画面比例共同约束。</p>}{capability === "tts" && controls?.supported_fields.includes("voice_id") && <Field label="精确 Voice ID（须与当前模型登记匹配）"><input className={inputClass} maxLength={150} disabled={busy || !!prepared} value={voiceId} onChange={e => setVoiceId(e.target.value)} /></Field>}</div>}
        <Field label="所需生成能力"><select className={inputClass} value={capability} disabled={busy || !!prepared} onChange={(event) => { setCapability(event.target.value as GenerationCapability); setCandidateCount(1); setOutputLimit(""); setVoiceId(""); setSendConfirmed(false); }}><option value="image_generation">生图</option><option value="video_generation">生视频</option><option value="tts">语音生成</option></select></Field>
        {(advanced || capability === "video_generation") && <Field label={capability === "image_generation" ? "本次图片像素上限" : "本次视频 / 语音秒数上限"}><input type="number" min={1} max={maximum} step={1} className={inputClass} value={outputLimit} disabled={busy || !!prepared} onChange={(event) => { setOutputLimit(event.target.value); setSendConfirmed(false); }} /></Field>}
        {capability === "image_generation" && controls?.supported_fields.includes("aspect_ratio") && <Field label="画面比例"><select className={inputClass} value={aspectRatio} disabled={busy || !!prepared} onChange={(event) => setAspectRatio(event.target.value)}><option value="1:1">1:1 方图</option><option value="4:3">4:3 横图</option><option value="16:9">16:9 横图</option><option value="3:4">3:4 竖图</option><option value="9:16">9:16 竖图</option></select></Field>}
        {capability === "tts" && voiceControlsSupported && <div className="space-y-3"><VoicePresetPicker voices={compatibleVoices} selectedId={compatibleVoices.find(item => item.voice_id === voiceId)?.id || ""} disabled={busy || !!prepared} onSelect={item => { setVoiceId(item.voice_id); setVoiceRate(item.rate ?? 1); }} /><Field label={`语速 ${voiceRate.toFixed(2)}×`}><input type="range" min="0.5" max="2" step="0.05" className="w-full" value={voiceRate} disabled={busy || !!prepared} onChange={event => setVoiceRate(Number(event.target.value))} /></Field></div>}
        {capability === "tts" && !voiceControlsSupported && <p className="text-xs text-amber-700">当前适配器未声明精确音色和语速配置，此处不能准备语音任务。</p>}
        {capability === "image_generation" && <Field label="候选图片数量（生成后只接受一张）"><select className={inputClass} value={candidateCount} disabled={busy || !!prepared} onChange={(event) => { setCandidateCount(Number(event.target.value)); setSendConfirmed(false); }}>{!candidateCounts.includes(candidateCount) && <option value={candidateCount} disabled>原选择 {candidateCount} 张已不支持，请重新选择</option>}{candidateCounts.map(count => <option key={count} value={count}>{count} 张</option>)}</select></Field>}
        {selectedProfile && !validControls && <p className="text-xs text-amber-700">当前配置不再支持原候选数量或精确音色；请重新选择，不会替换或提交旧配置。</p>}
        <p className="text-xs text-slate-600">当前配置版本 {configuration.revision}；图片最多生成 4 个候选，音频保持单份输出，上限 {maximum ?? "尚未配置"}。候选按顺序冻结，只有明确选中的一张可以接受入库。</p>
        {!prepared && <Button disabled={busy || unavailable || !!preview || !!batchCandidates.length || !selectedProfile || !prompt.trim() || !validLimit || !validControls} onClick={() => void prepareTask()}>仅保存准备任务（不发送、不扣费）</Button>}
        {prepared && <>
          <p role="status" className="text-sm">任务 {prepared.task_id} · {prepared.model_id} · {prepared.state}；{prepared.reason ? reasons[prepared.reason] ?? prepared.reason : "执行前仍需服务端检查"}</p>
          <p className="text-xs text-slate-600">此任务冻结路由：{prepared.selected_profile} → {prepared.plugin_id ? `能力插件 ${prepared.plugin_id} → ` : "模型自身 → "}{prepared.execution_profile}（{routeLabels[prepared.route_reason ?? ""] ?? "执行路径待核对"}）；{prepared.candidate_count ?? 1} 份候选，{prepared.candidate_mode === "native" ? "单次原生批量" : prepared.candidate_mode === "fan_out" ? "事先声明的分次生成" : "单次生成"}，{prepared.capability === "image_generation" ? `${prepared.frozen_parameters.pixels} 像素` : `${prepared.frozen_parameters.seconds} 秒`}上限。上面的当前配置不能重写原任务。</p>
          {prepared.state === "prepared" && !prepared.reason && <><label className="block text-sm"><input type="checkbox" checked={sendConfirmed} disabled={busy || unavailable} onChange={(event) => setSendConfirmed(event.target.checked)} />我授权这一个准备任务执行一次，可能消耗供应商额度；不确定结果不得重新提交。</label><Button disabled={busy || unavailable || !sendConfirmed} onClick={() => void executePrepared()}>执行此任务一次</Button></>}
          <Button variant="secondary" disabled={busy || ["unknown", "submitting", "running"].includes(prepared.state)} onClick={() => { setPrepared(undefined); setSendConfirmed(false); }}>结束本次准备（保留幂等键和原任务，不取消远端任务）</Button>
        </>}
      </div>}
      <Button variant="secondary" disabled={busy} onClick={() => void refreshTasks()}>读取我的持久生成任务</Button>
      <p className="text-xs text-slate-600">刷新只读状态；恢复只查询原任务。这里不重新提交、不自动生成或扣费。</p>
      {tasks.map((item) => <div key={item.task_id} className="flex flex-wrap items-center gap-2 rounded border p-2 text-sm">
        <span>{item.model_id} · {item.state} · 版本 {item.revision} · {routeLabels[item.route_reason ?? ""] ?? (item.plugin_id ? `插件 ${item.plugin_id}` : "执行路径待核对")}</span>
        {item.reason && <span>{reasons[item.reason] ?? item.reason}</span>}
        {item.material_revision_id && <span>已接受素材版本 #{item.material_revision_id}</span>}
        <Button variant="secondary" disabled={busy} onClick={() => void openTask(item)}>{item.state === "result_ready" ? "打开校验预览" : "刷新此任务"}</Button>
        {item.state === "prepared" && <Button variant="secondary" disabled={busy || unavailable} onClick={() => { setPrepared(item); setSendConfirmed(false); void readConfiguration(); }}>选择原准备任务（仍不执行）</Button>}
        {["running", "unknown", "submitting"].includes(item.state) && <Button variant="secondary" disabled={busy || unavailable} onClick={() => void openTask(item, true)}>{item.has_original_job ? "查询原任务" : "确认原任务状态（不重发）"}</Button>}
      </div>)}
    </div>}
    <p className="text-sm text-slate-600">{task ? "读取的是原任务的持久结果；重启后仍需校验字节、签名、权限和权利。" : mediaOrigin === "renderer" ? "这是已保存画布的真实渲染结果，不会调用生图模型，也没有自动授予素材权利。" : observedLicense ? "已下载临时预览，尚未入库。下列来源许可摘要已固定，不能将它改成另一种许可；请在原始来源核对署名和使用义务。" : "会调用已配置的真实生图 Provider，可能产生费用。"}预览不表示已验证或可公开发布；{task ? "只有明确接受后才入库。" : "临时预览约 15 分钟有效，服务重启后失效。"}</p>
    {initialTaskId && <div className="space-y-2">
      <p className="text-sm">原生成任务：{task?.state ?? "读取中"}。此处不提交新的生成。</p>
      <Button variant="secondary" disabled={busy} onClick={() => void openTask({ task_id: initialTaskId } as GenerationTask)}>刷新原任务状态（只读）</Button>
      {task && ["running", "unknown", "submitting"].includes(task.state) && <Button variant="secondary" disabled={busy || unavailable || taskReadOnly} onClick={() => void openTask(task, true)}>查询原供应商任务（不重发）</Button>}
    </div>}
    {task?.project_id != null && <p className="text-sm text-slate-600">此任务绑定项目 #{task.project_id}。明确接受会保存素材版本并同时建立该项目的素材引用，不会修改 Master。{taskReadOnly ? "项目已归档或状态未核实，此处只读。" : ""}</p>}
    {!initialTaskId && !observedLicense && !mediaOrigin && <Field label="生成描述"><textarea className={`${inputClass} h-24`} maxLength={2000} value={prompt} disabled={busy || !!preview || !!prepared} onChange={(event) => { setPrompt(event.target.value); setSendConfirmed(false); }} /></Field>}
    {!initialTaskId && !preview && !configuration && !prepared && <Button disabled={busy || unavailable || !prompt.trim()} onClick={() => void generate()}>{busy ? "生成中…" : "调用旧生图 Provider 生成临时预览"}</Button>}
    {batchCandidates.length > 0 && !preview && <div className="grid gap-3 sm:grid-cols-2">{batchCandidates.map(item => <button key={`${item.stage_id}:${item.candidate_index}`} type="button" disabled={busy} className="rounded-lg border p-2 text-left hover:border-indigo-500" onClick={() => { setPreview(item); setUrl(item.url); setConfirmed(false); }}><img src={item.url} alt={`候选图片 ${(item.candidate_index ?? 0) + 1}`} className="max-h-80 w-full rounded object-contain" /><p className="mt-1 text-xs text-slate-500">候选 {(item.candidate_index ?? 0) + 1} · SHA256 {item.content_hash.slice(0, 12)}…{taskAlreadyAccepted && task?.selected_candidate_index === item.candidate_index ? " · 已接受这一张" : ""}</p></button>)}</div>}
    {preview && <>
      {batchCandidates.length > 1 && !accepted && <Button variant="secondary" disabled={busy} onClick={() => { setPreview(undefined); setUrl(""); setConfirmed(false); }}>返回候选列表（保留任务）</Button>}
      {url && (/^image\/(png|jpeg|webp)$/.test(preview.mime_type) ? <img src={url} alt={previewIsAccepted ? "已接受的素材版本预览" : mediaOrigin === "renderer" ? "未入库的渲染预览" : "未入库的生成预览"} className="max-h-80 rounded-lg object-contain" /> : preview.kind === "audio" ? <audio src={url} controls /> : <video src={url} controls className="max-h-80" />)}
      {taskAlreadyAccepted && !previewIsAccepted && <p className="text-xs text-slate-500">这一张未被接受，仅供历史查看；该任务只将所选候选保存为素材。</p>}
      <p className="break-all text-xs text-slate-500">{preview.provider_key}@{preview.provider_version} · SHA256 {preview.content_hash}</p>
      {!taskAlreadyAccepted && <>
      <Field label="素材标题"><input className={inputClass} maxLength={200} value={title} disabled={disabled} onChange={(event) => setTitle(event.target.value)} /></Field>
      <Field label="你已核对的许可"><select aria-label="你已核对的许可" className={inputClass} value={license} disabled={disabled || !!observedLicense} onChange={(event) => { setLicense(event.target.value); setConfirmed(false); }}><option value="provider_terms">Provider 许可条款</option><option value="owned">本人拥有权利</option><option value="CC0">CC0</option><option value="CC-BY-4.0">CC BY 4.0</option></select></Field>
      <Field label="许可依据文件 SHA256（不上传原文或秘密）"><input className={inputClass} value={licenseHash} maxLength={64} disabled={disabled} readOnly={!!observedLicense} onChange={(event) => { setLicenseHash(event.target.value); setConfirmed(false); }} placeholder="已核对条款/权利依据的 64 位哈希" /></Field>
      <Field label="署名 / 来源说明（CC BY 必填）"><input className={inputClass} maxLength={1000} value={attribution} disabled={disabled} readOnly={!!observedLicense} onChange={(event) => { setAttribution(event.target.value); setConfirmed(false); }} /></Field>
      <div className="flex flex-wrap gap-4 text-sm">{([['public', '允许公开使用'], ['model', '允许模型使用'], ['commercial', '允许商业使用']] as const).map(([key, label]) => <label key={key}><input type="checkbox" className="mr-2" checked={rights[key]} disabled={disabled} onChange={(event) => { setRights((previous) => ({ ...previous, [key]: event.target.checked })); setConfirmed(false); }} />{label}</label>)}</div>
      <label className="block text-sm"><input type="checkbox" className="mr-2" checked={confirmed} disabled={disabled} onChange={(event) => setConfirmed(event.target.checked)} />我已看过媒体并核对上述许可、署名与使用权；这是人工确认，不是系统验证。</label>
      {!accepted && <Button disabled={disabled || !url || !confirmed || !title.trim() || !/^[0-9a-f]{64}$/.test(licenseHash.trim()) || (license === "CC-BY-4.0" && !attribution.trim())} onClick={() => void accept()}>{busy ? "保存中…" : task?.project_id != null ? `明确接受并引用到项目 #${task.project_id}` : "明确接受并保存素材版本"}</Button>}
      </>}
      {(accepted || taskAlreadyAccepted) && <p role="status" className="text-sm text-emerald-700">已保存精确素材版本 #{accepted?.material_revision_id ?? task?.material_revision_id}{accepted ? `，素材 #${accepted.material_id}` : ""}。{task?.project_id != null ? `已引用到项目 #${task.project_id}。` : ""}未修改 Master、身份或发布状态。</p>}
      <Button variant="secondary" disabled={busy} onClick={reset}>{initialTaskId || taskAlreadyAccepted ? "关闭此任务结果" : accepted ? mediaOrigin === "renderer" ? "关闭此渲染结果" : "生成下一份素材" : "放弃此预览"}</Button>
    </>}
    {error && <ErrorBanner message={error} />}
  </section>;
}
