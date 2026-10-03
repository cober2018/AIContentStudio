import { useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { api, currentUser } from "../api";
import { Button, ErrorBanner, Field, inputClass } from "../components/ui";

export interface Preview {
  stage_id: string;
  content_hash: string;
  mime_type: string;
  kind: string;
  provider_key: string;
  provider_version: string;
  expires_in_seconds: number;
  input_hash?: string;
}
export interface Accepted { material_id: number; material_revision_id: number; content_hash: string }
interface GenerationTask {
  task_id: string; state: string; revision: number; provider_key: string; provider_version: string;
  model_id: string; reason: string | null; has_original_job: boolean;
  content_hash: string | null; mime_type: string | null; material_revision_id: number | null;
  capability: GenerationCapability; selected_profile: string; execution_profile: string;
  plugin_id: string | null; route_reason?: string; frozen_parameters: Record<string, number>;
}
type GenerationCapability = "image_generation" | "video_generation" | "tts";
interface GenerationConfiguration {
  revision: number;
  profiles: Record<string, { enabled: boolean }>;
  policies: { limits: Partial<Record<GenerationCapability, { max_pixels?: number; max_seconds?: number; timeout_seconds: number }>> };
}
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

export default function ProviderMediaPanel({ initialPreview, initialTaskId, observedLicense, onDismiss, mediaOrigin, unavailable = false, onAccepted }: { initialPreview?: Preview; initialTaskId?: string; observedLicense?: ObservedLicense; onDismiss?: () => void; mediaOrigin?: "renderer"; unavailable?: boolean; onAccepted?: (accepted: Accepted) => void | Promise<void> }) {
  const queryClient = useQueryClient();
  const [prompt, setPrompt] = useState("");
  const [title, setTitle] = useState(observedLicense?.title ?? "");
  const [preview, setPreview] = useState<Preview | undefined>(initialPreview);
  const [accepted, setAccepted] = useState<Accepted>();
  const [url, setUrl] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [tasks, setTasks] = useState<GenerationTask[]>([]);
  const [task, setTask] = useState<GenerationTask>();
  const [configuration, setConfiguration] = useState<GenerationConfiguration>();
  const [selectedProfile, setSelectedProfile] = useState("");
  const [capability, setCapability] = useState<GenerationCapability>("image_generation");
  const [outputLimit, setOutputLimit] = useState("");
  const [prepared, setPrepared] = useState<GenerationTask>();
  const [sendConfirmed, setSendConfirmed] = useState(false);
  const preparation = useRef<{ input: string; key: string }>();
  const [license, setLicense] = useState(observedLicense?.license_code ?? "provider_terms");
  const [licenseHash, setLicenseHash] = useState(observedLicense?.license_evidence_hash ?? "");
  const [attribution, setAttribution] = useState(observedLicense?.attribution_text ?? "");
  const [confirmed, setConfirmed] = useState(false);
  const [rights, setRights] = useState({ public: false, model: false, commercial: false });
  const objectUrl = useRef("");
  const previewRead = useRef(0);
  const mounted = useRef(true);
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; if (objectUrl.current) URL.revokeObjectURL(objectUrl.current); }; }, []);
  useEffect(() => {
    if (initialTaskId) void openTask({ task_id: initialTaskId } as GenerationTask);
  }, [initialTaskId]);
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
    objectUrl.current = ""; setUrl(""); setPreview(undefined); setAccepted(undefined); setTask(undefined);
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
    if (!selectedProfile || !configuration || prepared) return;
    const actor = currentUser();
    const request = { capability, selected_profile: selectedProfile, prompt: prompt.trim(),
      parameters: { items: 1, [capability === "image_generation" ? "pixels" : "seconds"]: Number(outputLimit) } };
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
  async function executePrepared() {
    if (!prepared || prepared.state !== "prepared" || prepared.reason || !sendConfirmed) return;
    const actor = currentUser();
    setBusy(true); setError(""); setSendConfirmed(false);
    try {
      const result = await api.post<GenerationTask>(`/generation-tasks/${prepared.task_id}/execute`, { expected_revision: prepared.revision });
      if (!mounted.current || actor !== currentUser()) return;
      setPrepared(result);
      setTasks((old) => old.map((item) => item.task_id === result.task_id ? result : item));
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
    if (objectUrl.current) URL.revokeObjectURL(objectUrl.current);
    objectUrl.current = ""; setUrl(""); setPreview(undefined); setTask(undefined); setAccepted(undefined);
    setConfirmed(false); setRights({ public: false, model: false, commercial: false });
    setTitle(""); setLicense("provider_terms"); setLicenseHash(""); setAttribution("");
    setBusy(true); setError("");
    try {
      const result = recover
        ? await api.post<GenerationTask>(`/generation-tasks/${selected.task_id}/recover`, { expected_revision: selected.revision })
        : await api.get<GenerationTask>(`/generation-tasks/${selected.task_id}`);
      if (!mounted.current || actor !== currentUser() || readId !== previewRead.current) return;
      setTasks((old) => old.map((item) => item.task_id === result.task_id ? result : item));
      setPrepared((old) => old?.task_id === result.task_id ? result : old);
      setTask(result);
      if (result.state !== "result_ready" || !result.content_hash || !result.mime_type) {
        if (objectUrl.current) URL.revokeObjectURL(objectUrl.current);
        objectUrl.current = ""; setUrl(""); setPreview(undefined);
        if (result.reason) setError(reasons[result.reason] ?? result.reason);
        return;
      }
      const response = await fetch(`/api/v1/generation-tasks/${result.task_id}/raw`, { headers: { "X-Studio-User": actor }, cache: "no-store" });
      if (!response.ok) throw new Error("持久结果校验失败。保留原任务，不自动重新生成。");
      const blob = await response.blob();
      if (!mounted.current || actor !== currentUser() || readId !== previewRead.current) return;
      if (objectUrl.current) URL.revokeObjectURL(objectUrl.current);
      objectUrl.current = URL.createObjectURL(blob); setUrl(objectUrl.current);
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
    if (!preview || unavailable || busy || accepted) return;
    if (task && (task.task_id !== preview.stage_id || task.content_hash !== preview.content_hash || task.state !== "result_ready")) return;
    setBusy(true); setError("");
    try {
      const saved = await api.post<Accepted>(task ? `/generation-tasks/${task.task_id}/accept` : `/provider-media/${preview.stage_id}/accept`, {
        ...(task ? { expected_revision: task.revision } : {}),
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
  const disabled = unavailable || busy || accepted !== undefined;
  const configuredLimit = configuration?.policies.limits[capability];
  const maximum = capability === "image_generation" ? configuredLimit?.max_pixels : configuredLimit?.max_seconds;
  const validLimit = Number.isSafeInteger(Number(outputLimit)) && Number(outputLimit) > 0 && maximum !== undefined && Number(outputLimit) <= maximum;
  return <section aria-label={mediaOrigin === "renderer" ? "渲染预览与接受" : observedLicense ? "素材预览与接受" : "生成预览与接受"} className="space-y-4 rounded-xl border bg-white p-5">
    <h2 className="font-semibold">{mediaOrigin === "renderer" ? "渲染图片：先预览，再接受" : observedLicense ? "搜索素材：核对许可后接受" : "AI 素材：先预览，再接受"}</h2>
    {!initialPreview && !initialTaskId && !observedLicense && !mediaOrigin && <div className="space-y-2">
      <Button variant="secondary" disabled={busy || unavailable} onClick={() => void readConfiguration()}>读取已登记模型与生成限额（不生成）</Button>
      {configuration && <div className="space-y-2 rounded border p-3">
        <Field label="本次所选模型配置"><select className={inputClass} value={selectedProfile} disabled={busy || !!prepared} onChange={(event) => { setSelectedProfile(event.target.value); setSendConfirmed(false); }}><option value="">请选择，不修改默认模型</option>{Object.entries(configuration.profiles).filter(([, profile]) => profile.enabled).map(([id]) => <option key={id} value={id}>{id}</option>)}</select></Field>
        <Field label="所需生成能力"><select className={inputClass} value={capability} disabled={busy || !!prepared} onChange={(event) => { setCapability(event.target.value as GenerationCapability); setOutputLimit(""); setSendConfirmed(false); }}><option value="image_generation">生图</option><option value="video_generation">生视频</option><option value="tts">语音生成</option></select></Field>
        <Field label={capability === "image_generation" ? "本次图片像素上限" : "本次视频 / 语音秒数上限"}><input type="number" min={1} max={maximum} step={1} className={inputClass} value={outputLimit} disabled={busy || !!prepared} onChange={(event) => { setOutputLimit(event.target.value); setSendConfirmed(false); }} /></Field>
        <p className="text-xs text-slate-600">当前配置版本 {configuration.revision}；单份输出，上限 {maximum ?? "尚未配置"}。服务端决定模型 / 插件路由；这里不是账号能力验证或累计费用保证。</p>
        {!prepared && <Button disabled={busy || unavailable || !!preview || !selectedProfile || !prompt.trim() || !validLimit} onClick={() => void prepareTask()}>仅保存准备任务（不发送、不扣费）</Button>}
        {prepared && <>
          <p role="status" className="text-sm">任务 {prepared.task_id} · {prepared.model_id} · {prepared.state}；{prepared.reason ? reasons[prepared.reason] ?? prepared.reason : "执行前仍需服务端检查"}</p>
          <p className="text-xs text-slate-600">此任务冻结路由：{prepared.selected_profile} → {prepared.plugin_id ? `能力插件 ${prepared.plugin_id} → ` : "模型自身 → "}{prepared.execution_profile}（{routeLabels[prepared.route_reason ?? ""] ?? "执行路径待核对"}）；单份输出，{prepared.capability === "image_generation" ? `${prepared.frozen_parameters.pixels} 像素` : `${prepared.frozen_parameters.seconds} 秒`}上限。上面的当前配置不能重写原任务。</p>
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
        {["running", "unknown", "submitting"].includes(item.state) && <Button variant="secondary" disabled={busy} onClick={() => void openTask(item, true)}>{item.has_original_job ? "查询原任务" : "确认原任务状态（不重发）"}</Button>}
      </div>)}
    </div>}
    <p className="text-sm text-slate-600">{task ? "读取的是原任务的持久结果；重启后仍需校验字节、签名、权限和权利。" : mediaOrigin === "renderer" ? "这是已保存画布的真实渲染结果，不会调用生图模型，也没有自动授予素材权利。" : observedLicense ? "已下载临时预览，尚未入库。下列来源许可摘要已固定，不能将它改成另一种许可；请在原始来源核对署名和使用义务。" : "会调用已配置的真实生图 Provider，可能产生费用。"}预览不表示已验证或可公开发布；{task ? "只有明确接受后才入库。" : "临时预览约 15 分钟有效，服务重启后失效。"}</p>
    {initialTaskId && <p className="text-sm">原工作流任务：{task?.state ?? "读取中"}。此处仅查看并独立接受该任务的结果，不提交新的生成。</p>}
    {!initialTaskId && !observedLicense && !mediaOrigin && <Field label="生成描述"><textarea className={`${inputClass} h-24`} maxLength={2000} value={prompt} disabled={busy || !!preview || !!prepared} onChange={(event) => { setPrompt(event.target.value); setSendConfirmed(false); }} /></Field>}
    {!initialTaskId && !preview && !configuration && !prepared && <Button disabled={busy || unavailable || !prompt.trim()} onClick={() => void generate()}>{busy ? "生成中…" : "调用旧生图 Provider 生成临时预览"}</Button>}
    {preview && <>
      {url && (/^image\/(png|jpeg|webp)$/.test(preview.mime_type) ? <img src={url} alt={mediaOrigin === "renderer" ? "未入库的渲染预览" : "未入库的生成预览"} className="max-h-80 rounded-lg object-contain" /> : preview.kind === "audio" ? <audio src={url} controls /> : <video src={url} controls className="max-h-80" />)}
      <p className="break-all text-xs text-slate-500">{preview.provider_key}@{preview.provider_version} · SHA256 {preview.content_hash}</p>
      <Field label="素材标题"><input className={inputClass} maxLength={200} value={title} disabled={disabled} onChange={(event) => setTitle(event.target.value)} /></Field>
      <Field label="你已核对的许可"><select aria-label="你已核对的许可" className={inputClass} value={license} disabled={disabled || !!observedLicense} onChange={(event) => { setLicense(event.target.value); setConfirmed(false); }}><option value="provider_terms">Provider 许可条款</option><option value="owned">本人拥有权利</option><option value="CC0">CC0</option><option value="CC-BY-4.0">CC BY 4.0</option></select></Field>
      <Field label="许可依据文件 SHA256（不上传原文或秘密）"><input className={inputClass} value={licenseHash} maxLength={64} disabled={disabled} readOnly={!!observedLicense} onChange={(event) => { setLicenseHash(event.target.value); setConfirmed(false); }} placeholder="已核对条款/权利依据的 64 位哈希" /></Field>
      <Field label="署名 / 来源说明（CC BY 必填）"><input className={inputClass} maxLength={1000} value={attribution} disabled={disabled} readOnly={!!observedLicense} onChange={(event) => { setAttribution(event.target.value); setConfirmed(false); }} /></Field>
      <div className="flex flex-wrap gap-4 text-sm">{([['public', '允许公开使用'], ['model', '允许模型使用'], ['commercial', '允许商业使用']] as const).map(([key, label]) => <label key={key}><input type="checkbox" className="mr-2" checked={rights[key]} disabled={disabled} onChange={(event) => { setRights((previous) => ({ ...previous, [key]: event.target.checked })); setConfirmed(false); }} />{label}</label>)}</div>
      <label className="block text-sm"><input type="checkbox" className="mr-2" checked={confirmed} disabled={disabled} onChange={(event) => setConfirmed(event.target.checked)} />我已看过媒体并核对上述许可、署名与使用权；这是人工确认，不是系统验证。</label>
      {!accepted && <Button disabled={unavailable || busy || !url || !confirmed || !title.trim() || !/^[0-9a-f]{64}$/.test(licenseHash.trim()) || (license === "CC-BY-4.0" && !attribution.trim())} onClick={() => void accept()}>{busy ? "保存中…" : "明确接受并保存素材版本"}</Button>}
      {accepted && <p role="status" className="text-sm text-emerald-700">已保存精确素材版本 #{accepted.material_revision_id}，素材 #{accepted.material_id}。未修改 Master、身份或发布状态。</p>}
      <Button variant="secondary" disabled={busy} onClick={reset}>{accepted ? mediaOrigin === "renderer" ? "关闭此渲染结果" : "生成下一份素材" : "放弃此预览"}</Button>
    </>}
    {error && <ErrorBanner message={error} />}
  </section>;
}
