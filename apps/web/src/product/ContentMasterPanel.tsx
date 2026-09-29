import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, ApiError } from "../api";
import { Button, ErrorBanner, Field, Spinner, StatusBadge, inputClass } from "../components/ui";
import { ModalityWorkspace } from "./ModalityWorkspace";
import { createTextDraft, draftFromMaster, type TextDraft } from "./TextStudioModel";
import type { Unit } from "./project/projectTypes";
import type { UnitOutput } from "./useProductionWorkflow";

type Master = { id: number; revision_no: number; payload: Record<string, unknown>; payload_hash: string; context_hash: string; payload_schema: string; content_form: string | null; identity_snapshot_id: number | null; creative_brief_revision_id: number | null; fact_boundary_revision_id: number | null; assets: Record<string, unknown>[]; evidence: Record<string, unknown>[]; readiness: { state: string; reasons: string[] }; source_kind: string; edit_summary?: Record<string, unknown>; created_by?: string; created_at?: string };
type Readiness = { render_input_hash: string; context: { state: string; reasons: string[] }; render: Record<string, unknown>; preview: Record<string, unknown>; checks: { id: number | null; check_kind: string; status: string; is_current: boolean; report: Record<string, unknown> }[]; candidate_freeze_available: boolean; adapter_availability: { available: boolean; reasons: string[] } };
type UpgradePreview = { payload: Record<string, unknown>; warnings: { code: string }[]; source_master_id: number; source_revision_no: number; source_payload_hash: string; current_context_hash: string };
type MasterDiff = { title: { changed: boolean; before: string; after: string }; blocks: { kind: string; changes?: string[]; block_id?: string; block?: { id: string; type: string }; from_index?: number; to_index?: number }[]; assets: { changed: boolean }; evidence: { changed: boolean }; citations: { changed: boolean }; ai_provenance: { changed: boolean }; context: { changed: boolean } };
type CheckHistory = { id: number; check_kind: string; input_hash: string; status: string; report: Record<string, unknown>; created_at: string | null };
const pretty = (value: unknown) => JSON.stringify(value, null, 2);
function initial(modality: Unit["modality"]) { return modality === "graphic" ? { title: "", canvases: [] } : { title: "", script: "", shots: [], timeline: {} }; }
function object(text: string): Record<string, unknown> { const value: unknown = JSON.parse(text); if (!value || typeof value !== "object" || Array.isArray(value)) throw new Error("内容必须是 JSON 对象"); return value as Record<string, unknown>; }
function list(text: string): Record<string, unknown>[] { const value: unknown = JSON.parse(text); if (!Array.isArray(value) || value.some((row) => !row || typeof row !== "object" || Array.isArray(row))) throw new Error("引用必须是 JSON 对象数组"); return value as Record<string, unknown>[]; }
function message(cause: unknown) { return cause instanceof ApiError ? cause.status === 409 ? "409 · 内容版本或上下文已变化；请核对后重新加载，当前本地修改尚未保存。" : `${cause.status} · ${cause.message}` : cause instanceof Error ? cause.message : "请求失败"; }
function checkProvenance(report: Record<string, unknown>) {
  const requirement = (report.requirement || {}) as Record<string, unknown>;
  const semantic = (requirement.semantic || {}) as Record<string, unknown>;
  const profile = (requirement.profile || {}) as Record<string, unknown>;
  return `Profile: ${String(report.profile_id || profile.id || requirement.schema || "未指定")} · Provider: ${String(semantic.provider || "未配置/不适用")} / ${String(semantic.model || "未配置/不适用")}`;
}

export function ContentMasterPanel({ projectId, unit, readOnly, outputs }: { projectId: number; unit: Unit; readOnly: boolean; outputs: UnitOutput[] }) {
  const base = `/content-projects/${projectId}/units/${unit.id}`;
  const [history, setHistory] = useState<Master[]>([]);
  const [selected, setSelected] = useState<Master | null>(null);
  const [readiness, setReadiness] = useState<Readiness | null>(null);
  const [checkHistory, setCheckHistory] = useState<CheckHistory[]>([]);
  const [payload, setPayload] = useState(pretty(initial(unit.modality)));
  const [textDraft, setTextDraft] = useState<TextDraft | null>(() => unit.modality === "text" ? createTextDraft() : null);
  const [textEpoch, setTextEpoch] = useState(0);
  const [editorIssue, setEditorIssue] = useState("");
  const [assets, setAssets] = useState("[]");
  const [evidence, setEvidence] = useState("[]");
  const [form, setForm] = useState("");
  const [dirty, setDirty] = useState(false);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [acceptContext, setAcceptContext] = useState(false);
  const [outputId, setOutputId] = useState("");
  const [candidateId, setCandidateId] = useState<number | null>(null);
  const [upgradePreview, setUpgradePreview] = useState<UpgradePreview | null>(null);
  const [compareToId, setCompareToId] = useState("");
  const [revisionDiff, setRevisionDiff] = useState<MasterDiff | null>(null);
  const current = history[0] || null;
  const historical = !!selected && selected.id !== current?.id;
  const disabled = readOnly || historical || busy;
  useEffect(() => {
    if (!dirty) return;
    const warn = (event: BeforeUnloadEvent) => { event.preventDefault(); event.returnValue = ""; };
    const guardLink = (event: MouseEvent) => {
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      const anchor = (event.target as Element | null)?.closest?.("a[href]");
      if (!anchor || anchor.getAttribute("target") === "_blank") return;
      const target = new URL((anchor as HTMLAnchorElement).href);
      if (target.origin !== window.location.origin || target.pathname === window.location.pathname && target.search === window.location.search) return;
      if (!window.confirm("离开会丢弃未保存的 Content Master 修改，继续？")) { event.preventDefault(); event.stopPropagation(); }
    };
    window.addEventListener("beforeunload", warn);
    document.addEventListener("click", guardLink, true);
    return () => { window.removeEventListener("beforeunload", warn); document.removeEventListener("click", guardLink, true); };
  }, [dirty]);

  async function select(master: Master | null) {
    setSelected(master); setReadiness(null); setCheckHistory([]); setDirty(false); setAcceptContext(false);
    setUpgradePreview(null); setRevisionDiff(null);
    setTextDraft(unit.modality !== "text" ? null : !master ? createTextDraft() : master.payload_schema === "text.master.v2" ? draftFromMaster(master) : null);
    setTextEpoch((value) => value + 1); setEditorIssue("");
    setPayload(pretty(master?.payload || initial(unit.modality)));
    setAssets(pretty((master?.assets || []).map((row) => ({ material_revision_id: row.material_revision_id, content_hash: row.content_hash, role: row.role, slot_key: row.slot_key, sort_order: row.sort_order, placement: row.placement }))));
    setEvidence(pretty((master?.evidence || []).map((row) => ({ fact_pack_item_id: row.fact_pack_item_id, snapshot_checksum: row.snapshot_checksum, role: row.role, sort_order: row.sort_order, locator: row.locator }))));
    setForm(master?.content_form || "");
    if (master) {
      const [nextReadiness, nextChecks] = await Promise.all([api.get<Readiness>(`${base}/master-revisions/${master.id}/readiness`), unit.modality === "text" ? api.get<{ items: CheckHistory[] }>(`${base}/master-revisions/${master.id}/checks`) : Promise.resolve({ items: [] })]);
      setReadiness(nextReadiness); setCheckHistory(nextChecks.items);
    }
  }
  async function reload() {
    const result = await api.get<{ items: Master[] }>(`${base}/master-revisions`);
    setHistory(result.items); await select(result.items[0] || null);
  }
  useEffect(() => { reload().catch((cause) => setError(message(cause))).finally(() => setLoading(false)); }, [base]);
  function change(set: (value: string) => void, value: string) { set(value); setDirty(true); setNotice(""); }
  function changeText(value: TextDraft) { setTextDraft(value); setDirty(true); setNotice(""); }
  async function execute(action: () => Promise<void>) { setBusy(true); setError(""); setNotice(""); try { await action(); } catch (cause) { setError(message(cause)); } finally { setBusy(false); } }
  async function save(attest = false) {
    await execute(async () => {
      if (unit.modality === "text" && (!textDraft || editorIssue)) throw new Error(editorIssue || "旧版 Text Master 需先显式升级");
      await api.post(`${base}/master-revisions`, { expected_revision: current?.revision_no || 0, expected_context_hash: current && !acceptContext ? current.context_hash : undefined, idempotency_key: crypto.randomUUID(), parent_revision_id: current?.id, payload_schema: unit.modality === "text" ? "text.master.v2" : undefined, payload: unit.modality === "text" ? textDraft!.payload : object(payload), content_form: form || null, asset_refs: unit.modality === "text" ? textDraft!.assetRefs : list(assets), evidence_refs: unit.modality === "text" ? textDraft!.evidenceRefs : list(evidence), edit_summary: unit.modality === "text" && textDraft!.aiEdits.length ? { ai_edits: textDraft!.aiEdits } : {}, render_attestation: attest && readiness ? { confirmed: true, render_input_hash: readiness.render_input_hash } : undefined });
      await reload(); setNotice("已保存新的不可变 Master 修订；Workflow 草稿未修改。");
    });
  }
  return <section className="mb-5 rounded-2xl border border-slate-200 bg-white p-5" aria-label="Content Master">
    <div className="flex flex-wrap items-center justify-between gap-3"><h2 className="text-lg font-semibold">Content Master · {unit.modality}</h2><span className="text-xs text-slate-500">{dirty ? "内容有未保存修改" : "内容已同步"} · 与 Workflow 保存独立</span></div>
    {loading ? <Spinner label="读取 Master…" /> : <div className="mt-4 space-y-4">
      {error && <ErrorBanner message={error} />}{notice && <p role="status" className="text-sm text-emerald-700">{notice}</p>}
      <div className="flex flex-wrap gap-2"><Button variant="secondary" disabled={busy} onClick={() => { if (!dirty || window.confirm("重新加载会丢弃未保存的内容编辑，继续？")) execute(reload); }}>重新加载 Master</Button>{history.map((row) => <Button key={row.id} variant={selected?.id === row.id ? "primary" : "secondary"} size="sm" disabled={busy} onClick={() => { if (!dirty || window.confirm("切换版本会丢弃未保存的内容编辑，继续？")) execute(() => select(row)); }}>Master v{row.revision_no}{row.id === current?.id ? " · 当前" : " · 历史"}</Button>)}</div>
      {unit.modality === "text" && history.length > 0 && <details><summary className="cursor-pointer text-xs">不可变修订历史</summary><ul className="mt-2 space-y-1 text-xs">{history.map((row) => <li key={row.id}>v{row.revision_no} · {row.id === current?.id ? "当前" : "历史"} · {row.payload_schema} · {row.source_kind} · {row.created_by || "作者未知"} · {row.created_at || "时间未知"} · {row.readiness.state} · AI {Array.isArray((row.edit_summary?.ai_provenance as { edits?: unknown[] } | undefined)?.edits) ? (row.edit_summary?.ai_provenance as { edits: unknown[] }).edits.length : 0} 次</li>)}</ul></details>}
      {selected && <div className="rounded-lg bg-slate-50 p-3 text-xs text-slate-600"><p>Master #{selected.id} · {selected.payload_schema} · {selected.source_kind} · {selected.created_by || "作者未知"} · {selected.created_at || "时间未知"}</p><p className="break-all">Payload {selected.payload_hash} / Context {selected.context_hash}</p><p>Identity #{selected.identity_snapshot_id ?? "缺失"} · Brief #{selected.creative_brief_revision_id ?? "缺失"} · Boundary #{selected.fact_boundary_revision_id ?? "缺失"} · AI 编辑 {Array.isArray((selected.edit_summary?.ai_provenance as { edits?: unknown[] } | undefined)?.edits) ? (selected.edit_summary?.ai_provenance as { edits: unknown[] }).edits.length : 0}</p><StatusBadge status={selected.readiness.state} />{selected.readiness.reasons.length > 0 && <p>{selected.readiness.reasons.join("、")}</p>}</div>}
      {historical && <p className="text-sm text-amber-800">历史 Master 只读；选择当前版本后再创建新修订。</p>}
      {unit.modality === "text" ? <ModalityWorkspace modality="text" projectId={projectId} unitId={unit.id} masterId={selected?.payload_schema === "text.master.v2" ? selected.id : null} masterHash={selected?.payload_schema === "text.master.v2" ? selected.payload_hash : null} savedAssetIds={(selected?.assets || []).map((row) => Number(row.material_revision_id))} savedCitationIds={(selected?.evidence || []).map((row) => String((row.locator as { citation_id?: string } | undefined)?.citation_id || ""))} identitySnapshotId={selected?.identity_snapshot_id || unit.identity_snapshot_id} boundaryRevisionId={selected?.fact_boundary_revision_id || null} draft={textDraft} legacyPayload={selected?.payload} onChange={changeText} readOnly={disabled || (!!selected && selected.payload_schema !== "text.master.v2")} epoch={textEpoch} onIssue={setEditorIssue} /> : <ModalityWorkspace modality={unit.modality} value={payload} onChange={(value) => change(setPayload, value)} readOnly={disabled} />}
      {editorIssue && <ErrorBanner message={editorIssue} />}
      <div className="grid gap-3 sm:grid-cols-2"><Field label="渠道内容形态（留空由 Registry 解析）"><input aria-label="Master 内容形态" className={inputClass} value={form} disabled={disabled || (unit.modality === "text" && !!selected && selected.payload_schema !== "text.master.v2")} onChange={(event) => change(setForm, event.target.value)} /></Field><p className="self-center text-xs text-slate-500">渠道：{unit.channel_id || "未选择，不能冻结"}。素材来自项目共享素材，可跨 Unit 引用；不复制字节。</p></div>
      {unit.modality === "text" && selected && <div className="space-y-3 rounded-lg border border-slate-200 p-3"><h3 className="font-medium">Text Master 版本</h3>
        {selected.payload_schema === "text.master.v1" && selected.id === current?.id && <div className="space-y-2"><Button variant="secondary" disabled={disabled || dirty} onClick={() => execute(async () => setUpgradePreview(await api.get<UpgradePreview>(`${base}/master-revisions/${selected.id}/text-v2-upgrade-preview`)))}>预览 v1 → v2 升级</Button>{upgradePreview?.source_master_id === selected.id && <div className="rounded bg-amber-50 p-3 text-sm"><p>将从 v{upgradePreview.source_revision_no} 追加一个 v2 修订；原 v1 不变。</p><p>区块数：{((upgradePreview.payload.document as { blocks?: unknown[] } | undefined)?.blocks || []).length}；转换提示：{upgradePreview.warnings.length}</p><ul className="list-disc pl-5">{upgradePreview.warnings.map((warning, index) => <li key={index}>{warning.code}</li>)}</ul><Button disabled={disabled || dirty || selected.readiness.state === "stale"} onClick={() => execute(async () => { await api.post(`${base}/master-revisions/${selected.id}/text-v2-upgrade`, { expected_revision: selected.revision_no, expected_payload_hash: upgradePreview.source_payload_hash, expected_context_hash: upgradePreview.current_context_hash, idempotency_key: crypto.randomUUID() }); await reload(); setNotice("已显式追加 v2 修订；原 v1 保留只读。"); })}>确认升级并创建新版本</Button></div>}</div>}
        {history.length > 1 && <div className="flex flex-wrap gap-2"><select aria-label="对比 Master 版本" className={inputClass} value={compareToId} onChange={(event) => setCompareToId(event.target.value)}><option value="">选择对比版本</option>{history.filter((row) => row.id !== selected.id).map((row) => <option key={row.id} value={row.id}>v{row.revision_no} · {row.payload_schema}</option>)}</select><Button variant="secondary" disabled={!compareToId || busy} onClick={() => execute(async () => setRevisionDiff(await api.get<MasterDiff>(`${base}/master-revisions/${selected.id}/diff?compare_to_id=${compareToId}`)))}>查看结构化差异</Button></div>}
        {revisionDiff && <div className="text-sm"><p>标题{revisionDiff.title.changed ? `：${revisionDiff.title.before} → ${revisionDiff.title.after}` : "：未变"}</p><ul className="list-disc pl-5">{revisionDiff.blocks.map((row, index) => <li key={index}>{row.changes?.join(" / ") || row.kind} · {row.block_id || row.block?.id} · {row.block?.type || "区块"} · {row.from_index ?? "新"} → {row.to_index ?? "已移除"}</li>)}</ul><p>素材：{revisionDiff.assets.changed ? "有变化" : "未变"} · 证据：{revisionDiff.evidence.changed ? "有变化" : "未变"} · 引用：{revisionDiff.citations.changed ? "有变化" : "未变"} · AI 血缘：{revisionDiff.ai_provenance.changed ? "有变化" : "未变"} · 上下文：{revisionDiff.context.changed ? "有变化" : "未变"}</p></div>}
        {selected.source_kind === "workflow_seed" && <div className="text-xs text-slate-600"><p>本版本来自经验证的 Draft WorkflowOutput；未能证明的映射不会自动变成事实引用。</p><p>执行血缘：{pretty(selected.edit_summary?.workflow_source || "未知")}</p><p>未映射素材：{pretty(selected.edit_summary?.unmapped_media_ids || [])}；未映射 claim：{pretty(selected.edit_summary?.unmapped_claims || [])}</p></div>}
        {Array.isArray(selected.edit_summary?.conversion_warnings) && selected.edit_summary.conversion_warnings.length > 0 && <ul className="list-disc pl-5 text-xs text-amber-800">{selected.edit_summary.conversion_warnings.map((warning, index) => <li key={index}>{typeof warning === "object" && warning ? String((warning as { code?: string }).code || "转换需核对") : String(warning)}</li>)}</ul>}
      </div>}
      {unit.modality !== "text" && <details><summary className="cursor-pointer text-sm">精确素材与证据引用</summary><div className="mt-3 grid gap-3 sm:grid-cols-2"><Field label="Master 素材引用 JSON"><textarea aria-label="Master 素材引用 JSON" className={inputClass} rows={6} value={assets} readOnly={disabled} onChange={(event) => change(setAssets, event.target.value)} /></Field><Field label="Master 证据引用 JSON"><textarea aria-label="Master 证据引用 JSON" className={inputClass} rows={6} value={evidence} readOnly={disabled} onChange={(event) => change(setEvidence, event.target.value)} /></Field></div></details>}
      {selected?.readiness.state === "stale" && <label className="flex items-center gap-2 text-sm text-amber-800"><input type="checkbox" disabled={disabled} checked={acceptContext} onChange={(event) => setAcceptContext(event.target.checked)} />明确接纳最新项目上下文，保存为新修订（历史不改写）</label>}
      <div className="flex flex-wrap gap-2"><Button disabled={disabled || !!editorIssue || (unit.modality === "text" && !textDraft) || (selected?.readiness.state === "stale" && !acceptContext)} onClick={() => save()}>保存内容 Master</Button><Button variant="secondary" disabled={disabled || dirty || !selected || selected.readiness.state === "stale"} onClick={() => execute(async () => { await api.post(`${base}/master-revisions/${selected!.id}/checks`); await reload(); setNotice("Master 检查已持久化；旧检查不覆盖。"); })}>运行 Master 检查</Button><Button disabled={disabled || dirty || !readiness?.candidate_freeze_available || !selected} onClick={() => execute(async () => { const frozen = await api.post<{ id: number }>(`${base}/candidates/freeze`, { content_master_revision_id: selected!.id, expected_payload_hash: selected!.payload_hash }); setCandidateId(frozen.id); setNotice(`已冻结 Candidate v4 #${frozen.id}，尚未审批。`); })}>冻结 Master Candidate v4</Button>{candidateId && <Link className="self-center text-sm text-indigo-700 underline" to={`/review?project=${projectId}&unit=${unit.id}&candidate=${candidateId}`}>审阅 Candidate #{candidateId}</Link>}</div>
      {unit.modality !== "text" && <Button variant="secondary" disabled={disabled || dirty || !selected || !readiness || selected.readiness.state !== "current"} onClick={() => { if (window.confirm("确认当前 render_output 的真实字节是此 Master 的最终渲染？确认会保存带输入哈希证明的新修订。")) save(true); }}>确认当前渲染并保存新修订</Button>}
      {unit.modality === "text" && <div className="flex flex-wrap gap-2"><select aria-label="Draft seed 输出" className={inputClass} disabled={disabled || dirty} value={outputId} onChange={(event) => setOutputId(event.target.value)}><option value="">选择真实 Draft 输出</option>{outputs.filter((row) => row.output_kind === "draft").map((row) => <option key={row.id} value={row.id}>输出 #{row.id} · Draft #{row.entity_id} · Run #{row.run_id}</option>)}</select><Button variant="secondary" disabled={disabled || dirty || !outputId} onClick={() => execute(async () => { await api.post(`${base}/master-revisions/from-output`, { expected_revision: current?.revision_no || 0, idempotency_key: crypto.randomUUID(), project_output_id: Number(outputId) }); await reload(); setNotice("已从可验证 Draft 执行输出创建 text.master.v2；未证明的映射仍保持 incomplete，可在修订血缘中核对。"); })}>从 Draft 创建 Text Master</Button></div>}
      {readiness && <div><h3 className="font-medium">Master 当前检查与渲染</h3><p className="mt-1 text-xs text-slate-500">{readiness.candidate_freeze_available ? "可冻结" : "不可冻结"} · {readiness.adapter_availability.reasons.join("、")}</p>{unit.modality === "text" ? <div className="mt-2 space-y-2">{readiness.checks.map((row) => <div key={row.check_kind} className="rounded border border-slate-200 p-2 text-xs"><div className="flex flex-wrap items-center gap-2"><strong>{row.check_kind}</strong><StatusBadge status={row.status} /><span>{row.is_current ? "输入仍是当前版本" : "已过期，需重跑"}</span><span>检查 #{row.id ?? "未运行"}</span></div><p>覆盖：{pretty(row.report.coverage || "未知")}</p><p>{checkProvenance(row.report)}</p>{Array.isArray(row.report.reasons) && row.report.reasons.length > 0 && <p>原因：{row.report.reasons.join("、")}</p>}{Array.isArray(row.report.issues) && row.report.issues.length > 0 && <p>问题：{row.report.issues.map((issue) => typeof issue === "object" && issue ? String((issue as { reason?: string; code?: string }).reason || (issue as { code?: string }).code || "需核对") : String(issue)).join("、")}</p>}</div>)}<details><summary className="cursor-pointer text-xs">历史检查（不覆盖旧结果）</summary><ul className="mt-2 space-y-1 text-xs">{checkHistory.map((row) => <li key={row.id}>#{row.id} · {row.check_kind} · {row.status} · {row.created_at || "时间未知"} · {row.input_hash.slice(0, 12)}…</li>)}</ul></details><p className="text-xs">渲染：{String(readiness.render.status || "未知")}。需要处置 warning 时进入冻结后的 Review，不在此处把 warning 改写为 pass。</p></div> : <><div className="mt-2 flex flex-wrap gap-2">{readiness.checks.map((row) => <span key={row.check_kind} className="text-xs">{row.check_kind}: <StatusBadge status={row.status} /></span>)}</div><pre className="mt-3 max-h-56 overflow-auto rounded bg-slate-50 p-3 text-xs">{pretty({ preview: readiness.preview, render: readiness.render, checks: readiness.checks })}</pre></>}</div>}
    </div>}
  </section>;
}
