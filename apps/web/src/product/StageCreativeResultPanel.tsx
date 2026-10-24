import { useEffect, useRef, useState, type ReactNode } from "react";
import { api, ApiError, currentUser } from "../api";
import { stageErrorText } from "./stageErrors";
import { Button, ErrorBanner, Field, inputClass } from "../components/ui";
import type { StageResult } from "./stageProposalState";

type CreativeCandidate = { id: string; candidate_hash: string; summary: string; content: Record<string, unknown>;
  references: { kind: string; id: number; checksum: string }[]; warnings: string[] };
export type CreativeAcceptance = { accepted_target: StageResult["accepted_target"]; feedback_event_id: number; replayed: boolean;
  continuation?: { status: string; node_id?: string; code?: string } };
type AcceptanceRequest = { run_id: number; attempt_id: number; expected_output_hash: string; expected_resolution_hash: string;
  expected_context_hash: string; candidate_id: string; candidate_hash: string; acceptance_key: string; note: string };
const labels: Record<string, string> = { title: "标题", sections: "结构", heading: "段落", points: "要点", body: "内容",
  facts: "事实", unknowns: "未知", risks: "风险", angles: "角度", cards: "卡片", script: "口语稿", voice: "声音方向",
  shots: "镜头", notes: "说明", evidence: "证据", observations: "观察", summary: "概述", content: "内容",
  angle: "角度", reader_stake: "读者为什么关心", known: "用到的事实", statement: "事实", purpose: "作用", open_questions: "待确认" };

function contentView(value: unknown, depth = 0): ReactNode {
  if (depth > 6) return <p className="text-slate-500">更多细节已保存在原始尝试中。</p>;
  if (value === null || value === undefined) return null;
  if (Array.isArray(value)) return <ul className="space-y-2">{value.map((item, index) => <li key={index} className="border-l-2 border-slate-200 pl-3">{contentView(item, depth + 1)}</li>)}</ul>;
  if (typeof value === "object") return <div className="space-y-3">{Object.entries(value).filter(([key]) => !["id", "schema", "stage_schema"].includes(key)).map(([key, item]) => <div key={key}><p className="mb-1 text-xs font-medium text-slate-500">{labels[key] || key}</p>{contentView(item, depth + 1)}</div>)}</div>;
  return <p className="whitespace-pre-wrap break-words text-sm">{String(value)}</p>;
}

export default function StageCreativeResultPanel({ base, result, readOnly, onBusy, onAccepted }: {
  base: string; result: StageResult; readOnly: boolean; onBusy: (busy: boolean) => void;
  onAccepted: (value: CreativeAcceptance) => Promise<void>;
}) {
  const output = result.output as unknown as { schema: string; candidates?: CreativeCandidate[] };
  const candidates = output.candidates || [];
  const [selectedId, setSelectedId] = useState(candidates[0]?.id || "");
  const [note, setNote] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const [pending, setPending] = useState<AcceptanceRequest | null>(null);
  const [busy, setBusy] = useState(false);
  const [saved, setSaved] = useState<CreativeAcceptance | null>(null);
  const [error, setError] = useState("");
  const mounted = useRef(true);
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);
  const selected = candidates.find(item => item.id === selectedId);
  const accepted = Boolean(saved || result.accepted_target);
  const locked = readOnly || busy || accepted || !result.is_current || Boolean(pending);

  async function accept() {
    if (readOnly || busy || !pending && (!selected || !confirmed || accepted || !result.is_current)) return;
    const actor = currentUser();
    const request = pending || { run_id: result.run_id, attempt_id: result.attempt_id,
      expected_output_hash: result.receipt.output_hash, expected_resolution_hash: result.receipt.resolution_hash,
      expected_context_hash: result.expected_context_hash, candidate_id: selected!.id, candidate_hash: selected!.candidate_hash,
      acceptance_key: `creative:${crypto.randomUUID()}`, note };
    setPending(request); setBusy(true); onBusy(true); setError("");
    try {
      const value = await api.post<CreativeAcceptance>(`${base}/creation-recipe/stages/${encodeURIComponent(result.node_id)}/accept-creative`, request);
      if (!mounted.current || currentUser() !== actor) return;
      setSaved(value); setPending(null);
      try { await onAccepted(value); } catch { setError("接受已保存，阶段回读暂时失败。请回读原尝试，不要重新生成。"); }
    } catch (cause) {
      if (!mounted.current || currentUser() !== actor) return;
      if (cause instanceof ApiError && cause.status >= 400 && cause.status < 500) setPending(null);
      setError(cause instanceof ApiError ? stageErrorText(cause) : "接受结果未知，请重试同一接受请求或回读原尝试。");
    } finally { if (mounted.current) { setBusy(false); onBusy(false); } }
  }

  return <section className="mt-3 rounded-xl border border-slate-200 bg-white p-4">
    <h4 className="font-medium">中间创作结果</h4><p className="mt-1 text-xs text-slate-500">{output.schema} · 接受后供下游阶段使用，并继续到下一处人工审阅，不创建 Master 或素材。</p>
    <div className="mt-3 flex flex-wrap gap-2">{candidates.map((item, index) => <Button key={item.id} variant={item.id === selectedId ? "primary" : "secondary"} disabled={locked} onClick={() => { setSelectedId(item.id); setConfirmed(false); }}>候选 {index + 1}</Button>)}</div>
    {selected && <div className="mt-3 rounded-lg bg-slate-50 p-4"><p className="mb-3 text-sm font-medium">{selected.summary}</p>{contentView(selected.content)}
      {selected.warnings.length > 0 && <div className="mt-3 text-xs text-amber-700">{selected.warnings.map((item, index) => <p key={index}>{item}</p>)}</div>}
      <p className="mt-3 break-all text-xs text-slate-400">候选 hash：{selected.candidate_hash}</p>
      {selected.references.map((item, index) => <p key={index} className="mt-1 text-xs text-slate-500">精确引用：{item.kind} #{item.id} · {item.checksum}</p>)}
    </div>}
    {accepted ? <p className="mt-3 text-sm text-emerald-700">已接受本次中间候选，原尝试保持不变。</p> : <div className="mt-3 space-y-3">
      <Field label="接受说明（可选）"><textarea className={inputClass} maxLength={2000} value={note} disabled={locked} onChange={event => setNote(event.target.value)} /></Field>
      <label className="flex gap-2 text-sm"><input type="checkbox" checked={confirmed} disabled={locked} onChange={event => setConfirmed(event.target.checked)} />我已核对内容，明确选择此候选供下游使用。</label>
      <Button disabled={readOnly || busy || !pending && (!confirmed || !selected || accepted || !result.is_current)} onClick={accept}>{pending ? "重试原接受请求" : "接受并继续下一阶段"}</Button>
    </div>}
    {saved?.continuation && <p className="mt-3 text-xs text-slate-600">下一阶段：{saved.continuation.node_id || "无"} · {saved.continuation.status}，新结果仍须明确接受。</p>}
    {error && <div className="mt-3"><ErrorBanner message={error} /></div>}
  </section>;
}
