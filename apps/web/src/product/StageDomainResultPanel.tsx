import { useEffect, useRef, useState } from "react";
import { api, ApiError, currentUser } from "../api";
import { stageErrorText } from "./stageErrors";
import { Button, ErrorBanner, Field, StatusBadge, inputClass } from "../components/ui";
import ChannelVariantForm, { variantBodyIssue } from "./ChannelVariantForm";
import { stageValue } from "./creationRecipeState";
import { previewByteHash } from "./previewByteHash";
import type { StageAcceptedEntity, StageResult } from "./stageProposalState";

type Task = { task_id: string; state: string; revision: number; content_hash: string | null; mime_type: string | null;
  model_id?: string; execution_profile?: string; reason?: string; material_revision_id?: number;
  candidates?: { index: number; content_hash: string; mime_type: string; size: number }[];
  selected_candidate_index?: number | null };
type Domain = { domain: "media" | "audio_asr" | "variant" | "professional" | "checks" | "human"; result_hash: string | null;
  result: { task_id?: string; payload_schema?: string; payload?: Record<string, unknown>; asset_refs?: Record<string, unknown>[];
    evidence_refs?: Record<string, unknown>[]; expected_revision?: number; channel_id?: string; content_form?: string;
    variant_key?: string; package_id?: number; execution_id?: number | null; package_schema?: string;
    checks?: { id: number; check_kind: string; input_hash: string; status: string; report?: unknown }[]; instruction?: string; [key: string]: unknown };
  live?: Task | { package?: { id: number; is_current: boolean; reasons?: string[] }; execution?: { id: number; state: string;
    revision_no: number; safe_reason?: string; checkpoint?: unknown; recovery?: unknown;
    outputs?: { id: number; role_id: string; state: string; material_revision_id?: number }[] } | null } | null };
export type StageDomainAcceptance = { accepted_target: StageResult["accepted_target"]; accepted_entity: StageAcceptedEntity;
  feedback_event_id?: number; decision: string; continuation?: { status: string; node_id?: string; code?: string } };

function SubtitleExport({ subtitles, materialRevisionId, contentHash }: {
  subtitles: unknown; materialRevisionId?: number; contentHash?: string;
}) {
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const mounted = useRef(false);
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);
  if (!subtitles || typeof subtitles !== "object") return null;
  const value = subtitles as { schema?: string; srt?: string; srt_hash?: string; mode?: string;
    estimated?: boolean; label?: string; material_revision_id?: number; content_hash?: string; cue_count?: number };
  async function download() {
    const actor = currentUser(); setBusy(true); setError("");
    try {
      if (value.schema !== "studio.audio.subtitles.v1" || typeof value.srt !== "string"
        || !["asr", "estimated"].includes(value.mode || "") || value.estimated !== (value.mode === "estimated")
        || value.material_revision_id !== materialRevisionId || value.content_hash !== contentHash) throw new Error("字幕与本报告的精确音频来源不一致。");
      const bytes = new TextEncoder().encode(value.srt);
      if (bytes.byteLength > 24 * 1024 || await previewByteHash(bytes.buffer) !== value.srt_hash) throw new Error("字幕内容与冻结报告哈希不一致，不能导出。");
      if (!mounted.current || actor !== currentUser()) return;
      const url = URL.createObjectURL(new Blob([bytes], { type: "text/plain;charset=utf-8" }));
      try {
        const anchor = document.createElement("a"); anchor.href = url;
        anchor.download = value.mode === "estimated" ? "audio-estimated.srt" : "audio-asr.srt";
        anchor.click();
      } finally { URL.revokeObjectURL(url); }
    } catch (cause) { if (mounted.current && actor === currentUser()) setError(cause instanceof Error ? cause.message : "字幕导出失败。"); }
    finally { if (mounted.current) setBusy(false); }
  }
  return <div className="space-y-2 rounded-lg border border-slate-200 p-3"><p>{value.mode === "estimated" ? "估算字幕（非 ASR 时轴）" : "已接受 ASR 分段时轴（非逐词对齐）"} · {value.cue_count ?? "未核对"} 条</p><p className="text-slate-500">只导出此冻结报告，不调用识别、不接受素材、不写 Master；历史报告不代表当前素材仍可用。</p><Button size="sm" variant="secondary" disabled={busy} onClick={() => void download()}>{busy ? "核对字幕哈希…" : "校验哈希并下载 SRT"}</Button>{error && <ErrorBanner message={error} />}</div>;
}

function CheckReport({ report }: { report: unknown }) {
  if (!report || typeof report !== "object" || (report as Record<string, unknown>).schema !== "studio.audio.qc.v1") return <p className="mt-2 whitespace-pre-wrap text-xs">{stageValue(report)}</p>;
  const audio = report as { material_revision_id?: number; content_hash?: string; quality_profile_ref?: string;
    measured?: Record<string, unknown>; coverage?: Record<string, unknown>; issues?: { severity: string; code: string }[]; subtitles?: unknown; alignment?: { difference_ratio?: number; timing_alignment?: string } };
  const metrics: Record<string, string> = { duration_ms: "时长（毫秒）", rms_dbfs: "平均响度（dBFS，非 LUFS）", clipping_ratio: "削波比例", silence_ratio: "静音比例", leading_silence_ms: "开头静音（毫秒）", trailing_silence_ms: "结尾静音（毫秒）" };
  const coverage: Record<string, string> = { bytes_hash: "原文件与哈希", mime_duration: "真实格式与时长", waveform: "波形检测", accepted_task: "已接受任务回执", provider_model: "供应商与模型", voice_rate: "实际声音与语速", asr_alignment: "语音识别对稿" };
  return <div className="mt-2 space-y-3 text-xs"><p>音频素材版本 #{audio.material_revision_id ?? "未核对"} · {audio.quality_profile_ref}</p><dl className="grid gap-2 sm:grid-cols-2">{Object.entries(metrics).map(([key, label]) => <div key={key}><dt className="text-slate-500">{label}</dt><dd>{audio.measured?.[key] == null ? "未测得，不补零" : stageValue(audio.measured[key])}</dd></div>)}</dl><details><summary>本次检查覆盖范围</summary><dl className="mt-2 space-y-1">{Object.entries(coverage).map(([key, label]) => <div key={key}><dt>{label}</dt><dd className="text-slate-500">{stageValue(audio.coverage?.[key] ?? "not_run")}</dd></div>)}</dl></details>{audio.alignment && <p>对稿差异比例：{audio.alignment.difference_ratio ?? "未测得"} · {audio.alignment.timing_alignment || "未证明时间对齐"}</p>}<SubtitleExport subtitles={audio.subtitles} materialRevisionId={audio.material_revision_id} contentHash={audio.content_hash} />{audio.issues?.length ? <ul className="space-y-1">{audio.issues.map((issue, index) => <li key={`${issue.code}:${index}`}>{issue.severity} · {issue.code}</li>)}</ul> : null}<p className="text-slate-500">确定性检查不能代替试听。自然度、可懂度及角色声音是否合适，仍需人工确认；读取本报告不会调用 ASR。</p><details><summary>精确检查回执</summary><p className="mt-2 whitespace-pre-wrap break-words">{stageValue(report)}</p></details></div>;
}

function AudioASRResult({ value, status }: { value: Domain["result"]; status: string }) {
  const snapshot = value.asr_snapshot as { material_revision_id?: number; content_hash?: string; script?: string } | undefined;
  const provider = value.provider as { key?: string; version?: string; runtime_fingerprint?: string } | undefined;
  const cues = value.cues as { id: string; text: string; start_ms: number; end_ms: number }[] | undefined;
  const complete = value.audio_asr === true && ["waiting_input", "succeeded"].includes(status)
    && typeof value.duration_ms === "number" && Number.isFinite(value.duration_ms) && value.duration_ms > 0
    && Array.isArray(cues) && cues.length > 0 && typeof value.transcript === "string"
    && typeof value.output_hash === "string" && /^[a-f0-9]{64}$/.test(value.output_hash)
    && typeof snapshot?.material_revision_id === "number" && typeof snapshot.content_hash === "string";
  if (!complete) return <div className="mt-3 rounded-lg bg-amber-50 p-3 text-sm"><p>原识别尝试状态：{status}；尚无可确认的识别正文或分段时轴。</p><p className="mt-2 text-xs">保留原 Attempt，先回读或核对未知结果；这里不会自动重发识别，也不补零、估算或宣称已有真实字幕。</p></div>;
  return <div className="mt-3 space-y-3 text-sm"><p>音频素材版本 #{snapshot?.material_revision_id ?? "未核对"} · {Number(value.duration_ms) / 1000} 秒 · {cues?.length ?? 0} 段</p><p className="text-xs text-slate-500">本机 {provider?.key}@{provider?.version}。这是真实分段时轴，不是逐词对齐；识别结果不自动写 Master 或创建素材。</p><div className="grid gap-3 sm:grid-cols-2"><div><h4 className="font-medium">已接受口语稿</h4><p className="mt-2 max-h-64 overflow-auto whitespace-pre-wrap">{snapshot?.script}</p></div><div><h4 className="font-medium">识别正文</h4><p className="mt-2 max-h-64 overflow-auto whitespace-pre-wrap">{typeof value.transcript === "string" ? value.transcript : "未核对"}</p></div></div><details><summary>查看分段时轴</summary><ol className="mt-2 max-h-64 space-y-2 overflow-auto">{cues?.map(cue => <li key={cue.id}><span className="text-xs text-slate-500">{cue.start_ms}–{cue.end_ms} ms</span><p>{cue.text}</p></li>)}</ol></details><p className="text-xs text-amber-700">请核对后明确接受。后续 QC 才能使用此精确回执对稿和导出字幕；读取本结果不会再次识别。</p><details className="text-xs"><summary>来源与结果哈希</summary><p className="mt-2 break-all">来源 {snapshot?.content_hash} · runtime {provider?.runtime_fingerprint} · 输出 {String(value.output_hash || "未核对")}</p></details></div>;
}

export default function StageDomainResultPanel({ base, result, readOnly, onBusy, onAccepted }: {
  base: string; result: StageResult; readOnly: boolean; onBusy: (busy: boolean) => void;
  onAccepted: (value: StageDomainAcceptance) => Promise<void>;
}) {
  const domain = result.domain_output as Domain | null | undefined;
  const [payload, setPayload] = useState<Record<string, unknown> | null>(domain?.result.payload ? structuredClone(domain.result.payload) : null);
  const [note, setNote] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const [warningDispositions, setWarningDispositions] = useState<Record<string, string>>({});
  const [rights, setRights] = useState({ public_use_allowed: false, model_use_allowed: false, commercial_use_allowed: false });
  const [title, setTitle] = useState("");
  const [license, setLicense] = useState("provider_terms");
  const [licenseHash, setLicenseHash] = useState("");
  const [attribution, setAttribution] = useState("");
  const [url, setUrl] = useState("");
  const [reading, setReading] = useState(false);
  const [candidateIndex, setCandidateIndex] = useState(0);
  const [busy, setBusy] = useState(false);
  const [pending, setPending] = useState<Record<string, unknown> | null>(null);
  const [saved, setSaved] = useState<StageDomainAcceptance | null>(null);
  const [error, setError] = useState("");
  const mounted = useRef(true);
  const objectUrl = useRef("");
  const previewController = useRef<AbortController | null>(null);
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; previewController.current?.abort(); if (objectUrl.current) URL.revokeObjectURL(objectUrl.current); }; }, []);
  const task = domain?.domain === "media" ? domain.live as Task | null : null;
  useEffect(() => {
    previewController.current?.abort();
    if (objectUrl.current) { URL.revokeObjectURL(objectUrl.current); objectUrl.current = ""; }
    setUrl(""); setReading(false); setConfirmed(false);
    setCandidateIndex(task?.selected_candidate_index ?? 0);
  }, [task?.task_id, task?.content_hash, task?.revision]);
  useEffect(() => {
    previewController.current?.abort();
    if (objectUrl.current) { URL.revokeObjectURL(objectUrl.current); objectUrl.current = ""; }
    setUrl(""); setReading(false); setConfirmed(false);
  }, [candidateIndex]);
  const professional = domain?.domain === "professional" ? domain.live as Exclude<Domain["live"], Task> : null;
  const adopted = Boolean(saved || result.accepted_target || result.accepted_entity);
  const locked = readOnly || adopted || !result.is_current || busy || Boolean(pending);
  const edited = payload && JSON.stringify(payload) !== JSON.stringify(domain?.result.payload);
  const checkWarnings = domain?.domain === "checks" ? domain.result.checks?.filter(check => check.status === "warning") || [] : [];
  let bodyIssue = "";
  if (domain?.domain === "variant" && payload && domain.result.payload_schema) {
    try { bodyIssue = variantBodyIssue(domain.result.payload_schema, payload); }
    catch { bodyIssue = "此渠道正文暂不可编辑，请保留原结果并核对内容格式。"; }
  }
  const selectedCandidate = task?.candidates?.find(item => item.index === candidateIndex);
  const selectedContentHash = selectedCandidate?.content_hash ?? task?.content_hash;
  const canAccept = Boolean(domain && result.is_current && !adopted && domain.result_hash
    && (domain.domain !== "media" || task?.state === "result_ready" && url && selectedContentHash && title.trim() && /^[a-f0-9]{64}$/.test(licenseHash.trim()))
    && (domain.domain !== "professional" || !professional?.execution || professional.execution.state === "prepared")
    && (domain.domain !== "checks" || (domain.result.checks_pass === true || domain.result.checks_reviewable === true)
      && checkWarnings.every(check => warningDispositions[`${check.id}:${check.input_hash}`]?.trim()))
    && (domain.domain !== "variant" || payload && !bodyIssue));

  async function previewMedia() {
    const candidate = task?.candidates?.find(item => item.index === candidateIndex);
    const contentHash = candidate?.content_hash ?? task?.content_hash;
    const mimeType = candidate?.mime_type ?? task?.mime_type;
    if (!task || !contentHash || !mimeType || reading) return;
    const actor = currentUser();
    const controller = new AbortController(); previewController.current?.abort(); previewController.current = controller;
    setReading(true); setError(""); setConfirmed(false);
    try {
      const query = candidate ? `?candidate_index=${candidate.index}` : "";
      const response = await fetch(`/api/v1/generation-tasks/${encodeURIComponent(task.task_id)}/raw${query}`, { headers: { "X-Studio-User": actor }, cache: "no-store", signal: controller.signal });
      if (!response.ok) throw new Error("结果字节暂不可读。");
      const bytes = await response.arrayBuffer();
      if (await previewByteHash(bytes) !== contentHash) throw new Error("结果字节与当前任务哈希不一致。");
      if (!/^(image\/(png|jpeg|webp|gif)|audio\/(wav|x-wav|mpeg|ogg|mp4)|video\/(mp4|webm))$/.test(mimeType)) throw new Error("此媒体格式暂不可预览。");
      if (!mounted.current || actor !== currentUser() || controller.signal.aborted) return;
      if (objectUrl.current) URL.revokeObjectURL(objectUrl.current);
      objectUrl.current = URL.createObjectURL(new Blob([bytes], { type: mimeType })); setUrl(objectUrl.current);
    } catch (cause) { if (mounted.current && !controller.signal.aborted) setError(cause instanceof Error ? cause.message : "媒体结果暂不可读。"); }
    finally { if (mounted.current && !controller.signal.aborted) setReading(false); }
  }

  async function accept() {
    if (!domain || readOnly || busy || !pending && (!canAccept || !confirmed)) return;
    let request = pending;
    if (!request) {
      if (![result.receipt?.output_hash, result.receipt?.resolution_hash, result.expected_context_hash].every(hash => typeof hash === "string" && /^[a-f0-9]{64}$/.test(hash))) { setError("原尝试回执不完整，请先回读结果。"); return; }
      request = { run_id: result.run_id, attempt_id: result.attempt_id, domain: domain.domain,
        expected_output_hash: result.receipt.output_hash, expected_resolution_hash: result.receipt.resolution_hash,
        expected_context_hash: result.expected_context_hash, expected_revision: domain.result.expected_revision ?? 0,
        adoption_key: `adopt:${crypto.randomUUID()}`, decision: edited ? "accepted_with_edits" : "accepted", note, reason_tags: [] };
      if (domain.domain === "checks") request.warning_dispositions = Object.fromEntries(checkWarnings.map(check => [
        `${check.id}:${check.input_hash}`, warningDispositions[`${check.id}:${check.input_hash}`].trim()]));
      if (domain.domain === "media" && task) Object.assign(request, { task_id: task.task_id, candidate_index: candidateIndex, expected_revision: task.revision,
        expected_result_hash: selectedContentHash, decision: "accepted", rights: { ...rights, confirmed,
          title: title.trim(), license_code: license, license_evidence_hash: licenseHash.trim(), attribution_text: attribution.trim() || null } });
      if (domain.domain === "variant") Object.assign(request, { payload, asset_refs: domain.result.asset_refs || [], evidence_refs: domain.result.evidence_refs || [] });
      if (domain.domain === "professional") Object.assign(request, { package_id: domain.result.package_id, execution_id: domain.result.execution_id ?? null });
      request = structuredClone(request);
    }
    setPending(request); setBusy(true); onBusy(true); setError("");
    let uncertain = false;
    try {
      const value = await api.post<StageDomainAcceptance>(`${base}/creation-recipe/stages/${encodeURIComponent(result.node_id)}/accept-result`, request);
      setSaved(value); setPending(null);
      try { await onAccepted(value); } catch { setError("接受已提交，阶段回读暂时失败，请刷新状态后继续。"); }
    } catch (cause) {
      uncertain = !(cause instanceof ApiError && cause.status < 500);
      if (!uncertain) setPending(null);
      setError(uncertain ? "接受结果尚未确认。保留完整原请求，重试仅回放这次接受。" : `${stageErrorText(cause)}本地编辑仍保留。`);
    } finally { setBusy(false); onBusy(uncertain); }
  }

  if (!domain) return null;
  const accepted = saved?.accepted_entity || result.accepted_entity;
  const names = { media: "生成媒体素材", audio_asr: "本机 ASR 对稿", variant: "渠道版本", professional: "专业执行准备", checks: "检查结果", human: "人工确认" };
  return <section className="mt-4 rounded-xl border border-indigo-200 bg-white p-4" aria-label="阶段领域结果"><h3 className="font-semibold">{names[domain.domain]} · Attempt #{result.attempt_id}</h3><p className="mt-1 text-xs text-slate-500">结果来自原尝试与现有领域记录；明确接受后才记录本阶段决定。</p>
    {domain.domain === "media" && task?.candidates && task.candidates.length > 1 && <div className="mb-3 grid gap-2 sm:grid-cols-2">{task.candidates.map(candidate => <button key={candidate.index} type="button" className={`rounded border p-2 text-left text-xs ${candidate.index === candidateIndex ? "border-indigo-500 bg-indigo-50" : "border-slate-200"}`} disabled={locked} onClick={() => { setCandidateIndex(candidate.index); setUrl(""); setConfirmed(false); }}>{`候选 ${candidate.index + 1} · ${candidate.mime_type} · ${candidate.content_hash.slice(0, 12)}…`}</button>)}</div>}
    {domain.domain === "media" && task && <div className="mt-3 space-y-3"><p className="text-sm">生成任务 {task.task_id} · <StatusBadge status={task.state} /></p><p className="text-xs text-slate-500">执行配置：{task.execution_profile} · {task.model_id}。配置可用性与真实生成验证分别记录。</p>{task.reason && <p className="text-xs text-amber-700">{task.reason}</p>}{["unknown", "submitting", "submitted", "running", "pending"].includes(task.state) && <p className="text-xs text-amber-700">原任务尚未确认，保留原任务；请回读当前状态或在媒体任务面板核对。</p>}{["result_ready", "accepted"].includes(task.state) && <Button size="sm" variant="secondary" disabled={reading} onClick={previewMedia}>{reading ? "读取原结果…" : "查看并校验原媒体结果"}</Button>}{url && (task.mime_type?.startsWith("image/") ? <img src={url} alt="本次生成的待接受结果" className="max-h-96 max-w-full rounded-lg" /> : task.mime_type?.startsWith("audio/") ? <audio controls src={url} /> : <video controls src={url} className="max-h-96 max-w-full rounded-lg" />)}{!adopted && <><Field label="素材名称"><input className={inputClass} maxLength={300} value={title} disabled={locked} onChange={event => { setTitle(event.target.value); setConfirmed(false); }} /></Field><div className="grid gap-3 sm:grid-cols-2"><Field label="许可"><select className={inputClass} value={license} disabled={locked} onChange={event => { setLicense(event.target.value); setConfirmed(false); }}><option value="provider_terms">供应商条款</option><option value="self_owned">自有权利</option><option value="CC-BY-4.0">CC-BY-4.0</option></select></Field><Field label="已核对许可的证据摘要（SHA-256）"><input className={inputClass} value={licenseHash} disabled={locked} maxLength={64} onChange={event => { setLicenseHash(event.target.value); setConfirmed(false); }} /></Field></div><Field label="署名（许可要求时填写）"><input className={inputClass} maxLength={2000} value={attribution} disabled={locked} onChange={event => { setAttribution(event.target.value); setConfirmed(false); }} /></Field><fieldset className="flex flex-wrap gap-3" disabled={locked}>{([{ key: "public_use_allowed", label: "允许公开使用" }, { key: "model_use_allowed", label: "允许模型使用" }, { key: "commercial_use_allowed", label: "允许商业使用" }] as const).map(item => <label key={item.key} className="flex items-center gap-1 text-xs"><input type="checkbox" checked={rights[item.key]} onChange={event => { setRights(current => ({ ...current, [item.key]: event.target.checked })); setConfirmed(false); }} />{item.label}</label>)}</fieldset></>}<p className="text-xs text-slate-500">{task.mime_type?.startsWith("audio/") ? "接受会创建精确音频素材版本；请继续音频质量阶段，并在项目素材库试听。不会修改 Text Master；以后用于 Video 配音时再明确引用并保存。" : "接受会创建精确素材版本。进入下方内容编辑器选择它，再明确保存 Master。"}</p></div>}
    {domain.domain === "audio_asr" && <AudioASRResult value={domain.result} status={result.status} />}
    {domain.domain === "variant" && payload && domain.result.payload_schema && <div className="mt-3"><p className="mb-3 text-xs">{domain.result.channel_id} / {domain.result.content_form} · {domain.result.variant_key}</p><ChannelVariantForm schema={domain.result.payload_schema} value={payload} readOnly={locked} onChange={value => { setPayload(value); setConfirmed(false); }} /><p className="mt-2 text-xs text-slate-500">{edited ? "内容已在本地修改，接受会追加渠道修订并保留原结果。" : "接受会追加此精确渠道版本。"}</p>{bodyIssue && <ErrorBanner message={bodyIssue} />}</div>}
    {domain.domain === "professional" && <div className="mt-3 space-y-2 text-sm"><p>交接包 #{domain.result.package_id} · {domain.result.package_schema}</p><p>执行 #{domain.result.execution_id || "未准备执行记录"} · <StatusBadge status={professional?.execution?.state || "not_dispatched"} /></p>{professional?.execution?.safe_reason && <p className="text-xs text-amber-700">{professional.execution.safe_reason}</p>}<p className="text-xs text-slate-500">这里确认准备好的交接包；实际 Agent / 工具执行在下方“创意执行与成果”中明确操作。返回成果接受为素材后，仍需进入内容编辑器明确保存。</p>{professional?.execution?.outputs?.map(output => <p key={output.id} className="text-xs">输出 #{output.id} · {output.role_id} · {output.state} · 素材版本 #{output.material_revision_id || "尚未接受"}</p>)}{professional?.execution?.checkpoint != null && <details className="text-xs"><summary>检查点与恢复记录</summary><p className="mt-2 whitespace-pre-wrap">{stageValue(professional.execution.checkpoint)}</p><p className="mt-2 whitespace-pre-wrap">{stageValue(professional.execution.recovery)}</p></details>}</div>}
    {domain.domain === "checks" && <div className="mt-3 space-y-3">{domain.result.checks?.map(check => <div key={check.id} className="rounded-lg bg-slate-50 p-3"><p className="text-sm">{check.check_kind === "audio_quality" ? "音频质量" : check.check_kind} · <StatusBadge status={check.status} /></p><CheckReport report={check.report} />{check.status === "warning" && !adopted && <Field label="此提醒的处理说明（必填）"><textarea className={inputClass} maxLength={2000} disabled={locked} value={warningDispositions[`${check.id}:${check.input_hash}`] || ""} onChange={event => { setWarningDispositions(current => ({ ...current, [`${check.id}:${check.input_hash}`]: event.target.value })); setConfirmed(false); }} /></Field>}</div>)}<p className="text-xs text-slate-500">提醒必须逐项确认，原检查不会被改成通过；阻断、缺失和过期仍禁止继续。最终 Candidate 审核独立进行。</p></div>}
    {domain.domain === "human" && <div className="mt-3 rounded-lg bg-slate-50 p-3"><p className="whitespace-pre-wrap text-sm">{domain.result.instruction}</p><p className="mt-2 text-xs text-slate-500">确认此创作阶段的事项；最终 Candidate 审核与交付继续分别确认。</p></div>}
    {adopted ? <p className="mt-3 rounded-lg bg-emerald-50 p-3 text-sm text-emerald-800">已接受：{accepted?.kind || result.accepted_target?.output_kind} #{accepted?.id || result.accepted_target?.entity_id} · 版本 {accepted?.revision_no ?? "记录已保留"}</p> : <div className="mt-4 space-y-3"><Field label="接受说明（可选）"><textarea className={inputClass} maxLength={2000} value={note} disabled={locked} onChange={event => { setNote(event.target.value); setConfirmed(false); }} /></Field><label className="flex items-start gap-2 text-sm"><input type="checkbox" checked={confirmed} disabled={locked || !canAccept} onChange={event => setConfirmed(event.target.checked)} /><span>{domain.domain === "media" ? "已查看结果并核对许可及以上使用范围。" : domain.domain === "professional" ? "确认此交接包和执行记录已准备好，保留明确的工具执行步骤。" : "已查看当前结果，确认接受这次阶段决定。"}</span></label><Button disabled={readOnly || busy || !pending && (!canAccept || !confirmed)} onClick={accept}>{pending ? "重试原接受请求" : domain.domain === "media" ? "接受为素材版本" : domain.domain === "variant" ? "接受为新渠道修订" : "确认接受本阶段结果"}</Button></div>}
    {saved?.continuation && <p className="mt-2 text-xs text-slate-600">下一阶段：{saved.continuation.node_id || "无"} · {saved.continuation.status}。后续结果仍需明确接受。</p>}{error && <div className="mt-3"><ErrorBanner message={error} /></div>}
  </section>;
}
