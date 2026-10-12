import { useState } from "react";
import { api, ApiError } from "../api";
import { Button, ErrorBanner, Field, inputClass } from "../components/ui";
import { ModalityWorkspace } from "./ModalityWorkspace";
import { proposalDraft, proposalEdited, stageAdoption, type StageAdoption, type StageDraft, type StageMaster, type StageResult } from "./stageProposalState";

export type StageAcceptance = { master: StageMaster; decision: string; feedback_event_id?: number; continuation?: { status: string; node_id?: string; code?: string } };

export default function StageProposalReview({ projectId, unitId, result, readOnly, onBusy, onAccepted }: {
  projectId: number; unitId: number; result: StageResult; readOnly: boolean;
  onBusy: (busy: boolean) => void; onAccepted: (value: StageAcceptance) => Promise<void>;
}) {
  const candidates = result.output.candidates || [];
  const [selectedId, setSelectedId] = useState(candidates[0]?.candidate_id || "");
  const [drafts, setDrafts] = useState<Record<string, StageDraft>>({});
  const [pending, setPending] = useState<StageAdoption | null>(null);
  const [saved, setSaved] = useState<StageAcceptance | null>(null);
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [issue, setIssue] = useState("");
  const [error, setError] = useState("");
  const selected = candidates.find(item => item.candidate_id === selectedId);
  let draft: StageDraft | null = null;
  let formatIssue = "";
  try { draft = selected ? drafts[selectedId] || proposalDraft(selected) : null; }
  catch (cause) { formatIssue = cause instanceof Error ? cause.message : "候选格式暂不可编辑。"; }
  const adopted = Boolean(saved || result.accepted_target);
  const acceptedMaster = saved?.master || result.accepted_master;
  const locked = readOnly || !result.is_current || adopted || busy || Boolean(pending);

  async function accept() {
    if (!selected || !draft || readOnly || busy || adopted || issue || !pending && !result.is_current) return;
    let request: StageAdoption;
    try { request = pending || stageAdoption(result, selected, draft, `adopt:${crypto.randomUUID()}`, note); }
    catch { setError("候选或回执暂不可核对，请先回读原尝试。本地编辑保留。"); return; }
    setBusy(true); onBusy(true); setError("");
    let uncertain = false;
    try {
      setPending(request);
      const value = await api.post<StageAcceptance>(`/content-projects/${projectId}/units/${unitId}/creation-recipe/stages/${encodeURIComponent(result.node_id)}/accept-master`, request);
      setSaved(value); setPending(null);
      try { await onAccepted(value); }
      catch { setError("采用已提交，阶段回读暂时失败。请刷新阶段状态；本地编辑仍保留。"); }
    } catch (cause) {
      if (cause instanceof ApiError && cause.status < 500) setPending(null);
      else uncertain = true;
      setError(cause instanceof ApiError ? `${cause.status} · ${cause.message}。本地编辑保留，请重新查看上下文或生成新候选。` : "接受结果尚未确认。保留原请求与本地编辑；重试只回放这次精确采用，不改投其他候选。");
    } finally { setBusy(false); onBusy(uncertain); }
  }

  if (formatIssue) return <div className="mt-4"><ErrorBanner message={formatIssue} /></div>;
  if (!selected || !draft) return null;
  return <div className="mt-4 rounded-xl border border-indigo-200 bg-white p-4" aria-label="阶段候选审阅">
    <div className="flex flex-wrap items-center justify-between gap-2"><div><h3 className="font-semibold">查看候选，决定是否采用</h3><p className="mt-1 text-xs text-slate-500">Attempt #{result.attempt_id} · {result.receipt.request_mode === "automatic" ? "接受后自动执行" : "手动执行"}。修改只在本地；明确接受才创建 Master。</p></div><span className="text-xs text-slate-500">{candidates.length} 个候选</span></div>
    <div className="mt-3 flex flex-wrap gap-2" role="group" aria-label="选择候选">{candidates.map((candidate, index) => <Button key={candidate.candidate_id} size="sm" variant={selectedId === candidate.candidate_id ? "primary" : "secondary"} disabled={busy || Boolean(pending)} onClick={() => { setSelectedId(candidate.candidate_id); setIssue(""); setError(""); }}>候选 {index + 1} · {candidate.payload.title}</Button>)}</div>
    {adopted && <p className="mt-3 rounded-lg bg-emerald-50 p-3 text-sm text-emerald-800">已接受为 Master #{saved?.master.id || result.accepted_target?.entity_id}。下方内容母版有独立编辑状态；请用“重新加载 Master”查看新版本，未保存编辑不会被覆盖。</p>}
    {acceptedMaster && <details className="mt-3 rounded-lg bg-emerald-50 p-3 text-sm"><summary>已提交 Master v{acceptedMaster.revision_no} · {acceptedMaster.payload.title}</summary><p className="mt-2 break-all text-xs">精确 hash：{acceptedMaster.payload_hash}</p>{"document" in acceptedMaster.payload ? acceptedMaster.payload.document.blocks.map(block => <p key={block.id} className="mt-2 whitespace-pre-wrap">{"content" in block ? block.content.map(run => run.text).join("") : "items" in block ? block.items.map(item => item.content.map(run => run.text).join("")).join("\n") : block.type === "code" ? block.code : block.type === "image" || block.type === "chart" ? `${block.type} · 精确素材 #${block.material_revision_id}` : "—"}</p>) : "canvases" in acceptedMaster.payload ? acceptedMaster.payload.canvases.map(canvas => <p key={canvas.id} className="mt-2">画布 {canvas.order + 1} · {canvas.width} × {canvas.height} · {canvas.layers.length} 个图层</p>) : acceptedMaster.payload.script.blocks.map(block => <p key={block.id} className="mt-2 whitespace-pre-wrap">{block.text}</p>)}</details>}
    {saved?.continuation && <p className="mt-2 text-xs text-slate-600">接续阶段：{saved.continuation.node_id || "无"} · {saved.continuation.status}{saved.continuation.code ? ` · ${saved.continuation.code}` : ""}。新结果仍需人工接受。</p>}
    <div className="mt-4">{draft.payloadSchema === "text.master.v2" ? <ModalityWorkspace modality="text" projectId={projectId} unitId={unitId} masterId={null} masterHash={null} savedAssetIds={[]} savedCitationIds={[]} identitySnapshotId={result.resolved_stage?.context?.identity?.id || null} boundaryRevisionId={result.resolved_stage?.context?.boundary?.id || null} draft={draft} readOnly={locked} epoch={candidates.findIndex(item => item.candidate_id === selectedId)} onIssue={setIssue} onChange={value => setDrafts(current => ({ ...current, [selectedId]: value }))} /> : draft.payloadSchema === "graphic.master.v2" ? <ModalityWorkspace key={selectedId} modality="graphic" projectId={projectId} unitId={unitId} renderSource={null} renderUnavailable boundaryRevisionId={result.resolved_stage?.context?.boundary?.id || null} draft={draft} readOnly={locked} onChange={value => setDrafts(current => ({ ...current, [selectedId]: value }))} /> : <ModalityWorkspace key={selectedId} modality="video" projectId={projectId} unitId={unitId} masterId={null} masterHash={null} savedSourceIds={[]} dirty draft={draft} readOnly={locked} onChange={value => setDrafts(current => ({ ...current, [selectedId]: value }))} />}</div>
    {!adopted && <div className="mt-4 space-y-2"><Field label="采用说明（可选）"><textarea className={inputClass} value={note} maxLength={2000} disabled={locked} onChange={event => setNote(event.target.value)} /></Field><p className="text-xs text-slate-500">{proposalEdited(selected, draft) ? "接受后修改：保留原候选与最终 Master 的两个 hash。" : "采用原候选，不改写历史 Proposal。"} 保存仍校验原上下文和 Master 版本，冲突不会自动覆盖。</p><Button disabled={readOnly || !pending && !result.is_current || busy || Boolean(issue)} onClick={accept}>{pending ? "重试原采用请求" : busy ? "采用中…" : "接受为 Content Master"}</Button></div>}
    {issue && <div className="mt-3"><ErrorBanner message={issue} /></div>}{error && <div className="mt-3"><ErrorBanner message={error} /></div>}
  </div>;
}
