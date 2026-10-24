import { lazy, Suspense, useEffect, useState } from "react";
import { api, ApiError } from "../api";
import { Button, ErrorBanner, Field, Spinner, StatusBadge, inputClass } from "../components/ui";
import { stageValue, type StageContract } from "./creationRecipeState";
import { stageFeedback, type FeedbackTarget, type FeedbackLocation, type StageFeedbackDecision, type StageFeedbackRequest, type StageResult } from "./stageProposalState";

const StageProposalReview = lazy(() => import("./StageProposalReview"));
const StageDomainResultPanel = lazy(() => import("./StageDomainResultPanel"));
type FeedbackChoice = { target: FeedbackTarget; label: string; location: FeedbackLocation; duration_ms?: number };
export type StageFeedbackEvent = { id: number; decision?: string; attempt_id?: number; note?: string; reason_tags?: string[]; created_at?: string; payload?: { decision?: string; attempt_id?: number; note?: string; reason_tags?: string[]; accepted_hash?: string } };
export type StageHistory = { run_id?: number; node_id?: string; items: { attempt_id: number; attempt_no: number; status: string; output_hash?: string; receipt?: Record<string, unknown>; feedback: StageFeedbackEvent[] }[] };

export default function StageHistoryPanel({ base, nodeId, runId, result, contract, readOnly, epoch, onBusy, onFeedback, locatedEnabled = false }: {
  locatedEnabled?: boolean; base: string; nodeId: string; runId: number; result: StageResult | null; contract: StageContract;
  readOnly: boolean; epoch: number; onBusy: (busy: boolean) => void;
  onFeedback: (decision: StageFeedbackDecision) => Promise<void>;
}) {
  const [history, setHistory] = useState<StageHistory | null>(null);
  const [historical, setHistorical] = useState<StageResult | null>(null);
  const [refresh, setRefresh] = useState(0);
  const [loading, setLoading] = useState(true);
  const [reading, setReading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [pending, setPending] = useState<StageFeedbackRequest | null>(null);
  const [note, setNote] = useState("");
  const [choices, setChoices] = useState<FeedbackChoice[]>([]);
  const [choiceId, setChoiceId] = useState("");
  const [location, setLocation] = useState<FeedbackLocation | null>(null);
  const [targetAttempt, setTargetAttempt] = useState<number | null>(null);
  const [targetError, setTargetError] = useState("");
  useEffect(() => {
    let alive = true;
    setChoices([]); setChoiceId(""); setLocation(null); setTargetAttempt(null); setTargetError("");
    if (locatedEnabled && result) api.get<{ items: { target: FeedbackTarget; locations: Omit<FeedbackChoice, "target">[] }[] }>(`${base}/creation-recipe/stages/${encodeURIComponent(nodeId)}/feedback-targets?run_id=${runId}&attempt_id=${result.attempt_id}`).then(value => {
      if (alive) { setChoices(value.items.flatMap(item => item.locations.map(entry => ({ ...entry, target: item.target })))); setTargetAttempt(result.attempt_id); }
    }).catch(() => { if (alive) setTargetError("定位信息暂不可读；刷新历史后重试。可保留本作品意见。"); });
    return () => { alive = false; };
  }, [base, nodeId, runId, result?.attempt_id, result?.accepted_target?.accepted_hash, locatedEnabled, refresh]);
  const [tags, setTags] = useState<string[]>([]);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const stageBase = `${base}/creation-recipe/stages/${encodeURIComponent(nodeId)}`;
  useEffect(() => {
    let alive = true;
    setLoading(true); setError("");
    api.get<StageHistory>(`${stageBase}/history?run_id=${runId}`).then(value => {
      if (value.run_id !== undefined && value.run_id !== runId || value.node_id !== undefined && value.node_id !== nodeId
          || !Array.isArray(value.items)) throw new Error("历史记录身份不匹配。");
      if (alive) setHistory(value);
    }).catch(() => { if (alive) setError("阶段历史暂不可读，请刷新历史。"); }).finally(() => { if (alive) setLoading(false); });
    return () => { alive = false; };
  }, [stageBase, runId, nodeId, epoch, refresh]);

  async function inspect(attemptId: number) {
    setReading(true); setError("");
    try {
      const value = await api.get<StageResult>(`${stageBase}/result?run_id=${runId}&attempt_id=${attemptId}`);
      if (value.run_id !== runId || value.node_id !== nodeId || value.attempt_id !== attemptId) throw new Error("历史结果身份不匹配。");
      setHistorical(value);
    } catch { setError("此历史尝试暂不可回读。当前候选和本地编辑保留。"); }
    finally { setReading(false); }
  }

  async function send(decision: StageFeedbackDecision) {
    if (!result || readOnly || busy || pending && pending.decision !== decision) return;
    if (!pending && decision === "rerun_requested" && !result.allowed_decisions?.includes(decision)) return;
    let request: StageFeedbackRequest;
    try {
      if (choiceId && (!location || targetAttempt !== result.attempt_id || !choices[Number(choiceId)])) throw new Error("定位已变化，请重新选择当前片段。");
      const located = choiceId && location ? { target: choices[Number(choiceId)].target, location } : undefined;
      request = pending || stageFeedback(result, decision, `feedback:${crypto.randomUUID()}`, tags, note, located);
    }
    catch (cause) { setError(cause instanceof Error ? cause.message : "无法核对反馈来源。"); return; }
    setPending(request); setBusy(true); onBusy(true); setError(""); setNotice("");
    let uncertain = false;
    try {
      await api.post(`${stageBase}/feedback`, request);
      setPending(null); setNotice("本次决定已记录；保存的流程没有被反馈自动修改。");
      setRefresh(value => value + 1);
      try { await onFeedback(decision); } catch { setError("反馈已记录，阶段回读暂时失败。请刷新历史和阶段状态。"); }
    } catch (cause) {
      uncertain = !(cause instanceof ApiError && cause.status < 500);
      if (!uncertain) setPending(null);
      setError(uncertain ? "反馈尚未确认。保留原决定、哈希和请求，重试仅回放这次反馈。" : `${cause instanceof ApiError ? cause.status : ""} · 反馈未保存，请刷新当前尝试后再操作。`);
    } finally { setBusy(false); onBusy(uncertain); }
  }

  const adopted = Boolean(result?.accepted_target || result?.accepted_entity);
  const mutable = Boolean(result?.is_current && !adopted && !["running", "unknown"].includes(result.status));
  const canRerun = result?.allowed_decisions?.includes("rerun_requested") === true;
  const canSkip = result?.allowed_decisions?.includes("skipped_when_allowed") === true
    || contract.output_contract?.allow_skip === true
    || Array.isArray(contract.output_contract?.allowed_decisions) && contract.output_contract.allowed_decisions.includes("skipped_when_allowed");
  const reasons = [{ key: "instruction_mismatch", label: "不符合指令" }, { key: "fact_issue", label: "事实有问题" }, { key: "style", label: "风格不合适" }, { key: "quality", label: "质量未达预期" }];
  return <section className="mt-4 rounded-xl border border-slate-200 bg-white p-4" aria-label="阶段反馈与历史">
    <div className="flex items-center justify-between gap-2"><h3 className="font-semibold">反馈与尝试历史</h3><Button size="sm" variant="secondary" disabled={loading} onClick={() => setRefresh(value => value + 1)}>刷新历史</Button></div>
    {result && <div className="mt-3 space-y-3"><p className="text-xs text-slate-500">反馈固定到 Run #{result.run_id} / Attempt #{result.attempt_id}。接受反馈由保存结果时一并记录。</p><fieldset disabled={readOnly || busy || Boolean(pending)} className="flex flex-wrap gap-3"><legend className="mb-2 text-xs text-slate-600">原因（可选）</legend>{reasons.map(reason => <label key={reason.key} className="flex items-center gap-1 text-xs"><input type="checkbox" checked={tags.includes(reason.key)} onChange={event => setTags(current => event.target.checked ? [...current, reason.key] : current.filter(tag => tag !== reason.key))} />{reason.label}</label>)}</fieldset>{locatedEnabled && <div className="space-y-2 rounded-lg border border-indigo-100 p-3"><p className="text-xs text-slate-600">默认仅记录本作品。选择当前段落、图文页/元素或音视频时间段，精确版本随反馈保存。</p><Field label="反馈位置"><select className={inputClass} disabled={readOnly || busy || Boolean(pending)} value={choiceId} onChange={event => { setChoiceId(event.target.value); setLocation(event.target.value ? structuredClone(choices[Number(event.target.value)].location) : null); }}><option value="">本作品整体意见</option>{choices.map((choice, index) => <option key={index} value={String(index)}>{choice.target.candidate_id ? `${choice.target.candidate_id} / ` : ""}{choice.label}</option>)}</select></Field>{location?.kind === "text" && <Field label="选中片段（须与当前段落原文一致）"><textarea className={inputClass} maxLength={2000} disabled={readOnly || busy || Boolean(pending)} value={location.quote} onChange={event => setLocation({ ...location, quote: event.target.value })} /></Field>}{location?.kind === "time" && <div className="grid gap-2 sm:grid-cols-2">{(["start_ms", "end_ms"] as const).map(key => <Field key={key} label={key === "start_ms" ? "起点（毫秒）" : "终点（毫秒）"}><input type="number" min="0" max={choices[Number(choiceId)]?.duration_ms} className={inputClass} disabled={readOnly || busy || Boolean(pending)} value={location[key]} onChange={event => setLocation({ ...location, [key]: Number(event.target.value) })} /></Field>)}</div>}{targetError && <p role="alert" className="text-xs text-amber-700">{targetError}</p>}{location && <p className="text-xs text-amber-800">可先在主稿编辑器修改该段落或页元素。请求本阶段重做会重新生成整个阶段产物；位置和意见会随请求带入，独立分支不会自动重跑。接受前核对其它部分。</p>}</div>}<Field label="反馈说明（可选）"><textarea className={inputClass} maxLength={2000} value={note} disabled={readOnly || busy || Boolean(pending)} onChange={event => setNote(event.target.value)} /></Field><div className="flex flex-wrap gap-2">{pending ? <Button disabled={readOnly || busy} onClick={() => send(pending.decision)}>重试原反馈请求</Button> : <>{locatedEnabled && <Button size="sm" variant="secondary" disabled={readOnly || busy || !result.is_current || ["running", "unknown"].includes(result.status) || !note.trim()} onClick={() => send("commented")}>保存本作品意见</Button>}<Button size="sm" variant="secondary" disabled={readOnly || busy || !mutable} onClick={() => send("rejected")}>拒绝这次结果</Button><Button size="sm" variant="secondary" disabled={readOnly || busy || !result.is_current || ["running", "unknown"].includes(result.status) || !canRerun} onClick={() => send("rerun_requested")}>{location ? "确认整阶段重做范围，记录原因" : "记录重跑原因，重新调节"}</Button>{canSkip && <Button size="sm" variant="secondary" disabled={readOnly || busy || !mutable} onClick={() => send("skipped_when_allowed")}>跳过这个允许跳过的阶段</Button>}</>}</div></div>}
    {notice && <p className="mt-3 text-xs text-emerald-700" role="status">{notice}</p>}
    {loading ? <Spinner label="加载阶段历史…" /> : history && <div className="mt-4 overflow-x-auto"><table className="w-full text-left text-xs"><caption className="mb-2 text-left text-slate-500">原 Run #{runId} 的不可变尝试</caption><thead><tr><th className="p-2">尝试</th><th>执行状态</th><th>决定与反馈</th><th>查看</th></tr></thead><tbody>{history.items.map(attempt => { const id = attempt.attempt_id; const events = attempt.feedback || []; return <tr key={id} className="border-t"><td className="p-2">#{attempt.attempt_no} · {id}</td><td><StatusBadge status={attempt.status} /></td><td className="max-w-md py-2">{events.length ? events.map(event => <p key={event.id} className="whitespace-pre-wrap">{event.decision || event.payload?.decision} · {stageValue(event.reason_tags || event.payload?.reason_tags)}{event.note || event.payload?.note ? ` · ${event.note || event.payload?.note}` : ""}</p>) : "尚无反馈"}</td><td><Button size="sm" variant="secondary" disabled={reading || !id} onClick={() => inspect(id)}>只读查看</Button></td></tr>; })}</tbody></table>{history.items.length === 0 && <p className="text-xs text-slate-500">尚无执行尝试。</p>}</div>}
    {historical && <div className="mt-3 rounded-lg bg-slate-50 p-3"><div className="flex justify-between gap-2"><p className="text-xs">历史 Attempt #{historical.attempt_id} · 只读查看</p><Button variant="secondary" size="sm" onClick={() => setHistorical(null)}>关闭历史结果</Button></div><details className="mt-2 text-xs"><summary>这次尝试的实际指令与参数</summary><p className="mt-2 whitespace-pre-wrap">{stageValue(historical.resolved_stage?.effective_config)}</p><p className="mt-2 whitespace-pre-wrap">{historical.resolved_stage?.effective_prompt}</p></details>{historical.output?.schema === "stage.master.proposal.v1" ? <Suspense fallback={<Spinner />}><StageProposalReview key={historical.attempt_id} projectId={Number(base.split("/")[2])} unitId={Number(base.split("/")[4])} result={historical} readOnly onBusy={() => {}} onAccepted={async () => {}} /></Suspense> : historical.domain_output && <Suspense fallback={<Spinner />}><StageDomainResultPanel result={historical} base={base} readOnly onBusy={() => {}} onAccepted={async () => {}} /></Suspense>}</div>}
    {error && <div className="mt-3"><ErrorBanner message={error} /></div>}
  </section>;
}
