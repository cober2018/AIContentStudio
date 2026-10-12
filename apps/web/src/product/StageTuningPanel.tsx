import { useEffect, useState } from "react";
import { api, ApiError } from "../api";
import { Button, ErrorBanner, Field, Spinner, inputClass } from "../components/ui";
import StageContractControls from "./StageContractControls";
import { stageValue, type StageContract, type StageMethods } from "./creationRecipeState";
import type { StageFeedbackEvent, StageHistory } from "./StageHistoryPanel";

export type StageTuningPatch = { tuning_suggestion_id: number; expected_suggestion_hash: string; config_patch: Record<string, unknown> };
type Suggestion = { llm_run_id: number; suggestion_hash: string; config_patch: Record<string, unknown>;
  base_config: Record<string, unknown>; effective_config: Record<string, unknown>; explanation: string };
type Request = { feedback_event_ids: number[]; model_profile_id?: string; invocation_key: string };

export default function StageTuningPanel({ base, nodeId, runId, acceptedFeedbackId, contract, readOnly, onBusy, onPatch, onInvalidate }: {
  base: string; nodeId: string; runId: number; acceptedFeedbackId: number; contract: StageContract;
  readOnly: boolean; onBusy: (busy: boolean) => void; onPatch: (value: StageTuningPatch) => void; onInvalidate: () => void;
}) {
  const [feedback, setFeedback] = useState<StageFeedbackEvent[]>([]);
  const [selected, setSelected] = useState<number[]>([acceptedFeedbackId]);
  const [profiles, setProfiles] = useState<StageMethods["model_profiles"]>([]);
  const [model, setModel] = useState("");
  const [suggestion, setSuggestion] = useState<Suggestion | null>(null);
  const [patch, setPatch] = useState<Record<string, unknown>>({});
  const [pending, setPending] = useState<Request | null>(null);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [unavailable, setUnavailable] = useState(false);
  const [error, setError] = useState("");
  const stageBase = `${base}/creation-recipe/stages/${encodeURIComponent(nodeId)}`;
  useEffect(() => {
    let alive = true;
    Promise.all([api.get<StageHistory>(`${stageBase}/history?run_id=${runId}`), api.get<StageMethods>(`${base}/creation-recipe/methods`)]).then(([history, inventory]) => {
      if (alive) { setFeedback(history.items.flatMap(attempt => attempt.feedback)); setProfiles(inventory.model_profiles); }
    }).catch(() => { if (alive) setError("反馈或模型清单暂不可读，不能请求建议。"); }).finally(() => { if (alive) setLoading(false); });
    return () => { alive = false; };
  }, [base, stageBase, runId]);
  async function suggest() {
    if (readOnly || busy || unavailable && !pending || !pending && (!selected.length || loading)) return;
    const request = pending || { feedback_event_ids: [...selected], ...(model ? { model_profile_id: model } : {}), invocation_key: `tune:${crypto.randomUUID()}` };
    if (!request.feedback_event_ids.includes(acceptedFeedbackId)
        || !pending && !feedback.some(event => event.id === acceptedFeedbackId && ["accepted", "accepted_with_edits"].includes(event.decision || event.payload?.decision || ""))) {
      setError("必须保留这次结果的接受反馈，才能请求调优建议。"); return;
    }
    onInvalidate(); setSuggestion(null); setPending(request); setBusy(true); onBusy(true); setError("");
    let uncertain = false;
    try {
      const value = await api.post<Suggestion>(`${stageBase}/tuning-suggestion`, request);
      if (!/^[a-f0-9]{64}$/.test(value.suggestion_hash) || !Number.isSafeInteger(value.llm_run_id) || !Object.keys(value.config_patch).every(field => contract.tunable_fields?.includes(field))) throw new Error("建议回执或允许字段不匹配。");
      setSuggestion(value); setPatch(structuredClone(value.config_patch)); setPending(null);
    } catch (cause) {
      const beforeDispatch = cause instanceof ApiError && [400, 403, 404, 422].includes(cause.status);
      uncertain = !beforeDispatch;
      if (beforeDispatch) setPending(null);
      if (cause instanceof ApiError && [404, 503].includes(cause.status)) setUnavailable(true);
      setError(beforeDispatch ? "调优建议当前不可用，请核对反馈与模型；已有调节保持原样。" : "原调优请求尚未确认，保留原反馈、模型与调用键；只能回读或重试同一请求。");
    } finally { setBusy(false); onBusy(uncertain); }
  }
  const locked = readOnly || busy || Boolean(pending);
  return <section className="mt-4 rounded-lg border border-indigo-200 p-4" aria-label="AI 调优建议"><h4 className="font-semibold">AI 调优建议</h4><p className="mt-1 text-xs text-slate-500">明确选择本阶段的反馈后调用一次模型。建议保留原模型回执；参数修改还需另行预览与确认保存。</p>{loading && <Spinner label="读取可选反馈…" />}<fieldset className="mt-3 space-y-2" disabled={locked || loading}><legend className="mb-2 text-sm">明确选择反馈（最多 20 条；当前接受反馈必选）</legend>{feedback.map(event => <label key={event.id} className="flex items-start gap-2 text-xs"><input type="checkbox" checked={event.id === acceptedFeedbackId || selected.includes(event.id)} disabled={event.id === acceptedFeedbackId || !selected.includes(event.id) && selected.length >= 20} onChange={input => { if (event.id === acceptedFeedbackId) return; setSelected(current => Array.from(new Set([acceptedFeedbackId, ...(input.target.checked ? [...current, event.id] : current.filter(id => id !== event.id))]))); setSuggestion(null); onInvalidate(); }} /><span>反馈 #{event.id} · Attempt #{event.attempt_id} · {event.decision} · {event.note || "无说明"}{event.id === acceptedFeedbackId ? " · 接受反馈（必选）" : ""}</span></label>)}</fieldset><div className="mt-3"><Field label="请求建议使用的模型"><select className={inputClass} value={model} disabled={locked || loading} onChange={event => { setModel(event.target.value); setSuggestion(null); onInvalidate(); }}><option value="">使用后端当前明确的默认路由</option>{profiles.map(profile => { const id = profile.id || profile.profile_id; return id && <option key={id} value={id} disabled={profile.available === false}>{profile.label || id}{profile.reason ? ` · ${profile.reason}` : ""}</option>; })}</select></Field></div><Button className="mt-3" disabled={readOnly || busy || unavailable && !pending || !pending && (loading || !selected.includes(acceptedFeedbackId) || !feedback.some(event => event.id === acceptedFeedbackId && ["accepted", "accepted_with_edits"].includes(event.decision || event.payload?.decision || "")))} onClick={suggest}>{pending ? "重试原调优请求" : "请求一次调优建议"}</Button>
    {suggestion && <div className="mt-4 space-y-3"><p className="whitespace-pre-wrap text-sm">{suggestion.explanation}</p><p className="break-all text-xs text-slate-500">模型调用 #{suggestion.llm_run_id} · 建议摘要 {suggestion.suggestion_hash}</p><StageContractControls base={base} nodeId={nodeId} contract={{ ...contract, supports_run_override: true, tunable_fields: Object.keys(patch) }} baseConfig={suggestion.base_config} override={patch} disabled={locked} onChange={(field, value) => { onInvalidate(); setPatch(current => { const next = { ...current }; if (value === undefined) delete next[field]; else next[field] = value; return next; }); }} /><table className="w-full text-left text-xs"><thead><tr><th className="p-2">参数</th><th>原配置</th><th>拟采用</th></tr></thead><tbody>{Object.entries(patch).map(([field, value]) => <tr className="border-t" key={field}><td className="p-2">{contract.ui_schema?.[field]?.label || field}</td><td className="max-w-xs whitespace-pre-wrap break-words p-2">{stageValue(suggestion.base_config[field])}</td><td className="max-w-xs whitespace-pre-wrap break-words p-2">{stageValue(value)}</td></tr>)}</tbody></table><Button variant="secondary" disabled={locked || !Object.keys(patch).length} onClick={() => onPatch({ tuning_suggestion_id: suggestion.llm_run_id, expected_suggestion_hash: suggestion.suggestion_hash, config_patch: structuredClone(patch) })}>选用以上参数，进入保存差异预览</Button></div>}{error && <div className="mt-3"><ErrorBanner message={error} /></div>}
  </section>;
}
