import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, ApiError } from "../api";
import { Button, ErrorBanner, Field, Spinner, StatusBadge, inputClass } from "../components/ui";
import { ModalityWorkspace } from "./ModalityWorkspace";
import type { Unit } from "./project/projectTypes";
import type { UnitOutput } from "./useProductionWorkflow";

type Master = { id: number; revision_no: number; payload: Record<string, unknown>; payload_hash: string; context_hash: string; payload_schema: string; content_form: string | null; identity_snapshot_id: number | null; creative_brief_revision_id: number | null; fact_boundary_revision_id: number | null; assets: Record<string, unknown>[]; evidence: Record<string, unknown>[]; readiness: { state: string; reasons: string[] }; source_kind: string };
type Readiness = { render_input_hash: string; context: { state: string; reasons: string[] }; render: Record<string, unknown>; preview: Record<string, unknown>; checks: { id: number | null; check_kind: string; status: string; is_current: boolean; report: Record<string, unknown> }[]; candidate_freeze_available: boolean; adapter_availability: { available: boolean; reasons: string[] } };
const pretty = (value: unknown) => JSON.stringify(value, null, 2);
function initial(modality: Unit["modality"]) { return modality === "text" ? { title: "", markdown: "" } : modality === "graphic" ? { title: "", canvases: [] } : { title: "", script: "", shots: [], timeline: {} }; }
function object(text: string): Record<string, unknown> { const value: unknown = JSON.parse(text); if (!value || typeof value !== "object" || Array.isArray(value)) throw new Error("内容必须是 JSON 对象"); return value as Record<string, unknown>; }
function list(text: string): Record<string, unknown>[] { const value: unknown = JSON.parse(text); if (!Array.isArray(value) || value.some((row) => !row || typeof row !== "object" || Array.isArray(row))) throw new Error("引用必须是 JSON 对象数组"); return value as Record<string, unknown>[]; }
function message(cause: unknown) { return cause instanceof ApiError ? `${cause.status} · ${cause.message}` : cause instanceof Error ? cause.message : "请求失败"; }

export function ContentMasterPanel({ projectId, unit, readOnly, outputs }: { projectId: number; unit: Unit; readOnly: boolean; outputs: UnitOutput[] }) {
  const base = `/content-projects/${projectId}/units/${unit.id}`;
  const [history, setHistory] = useState<Master[]>([]);
  const [selected, setSelected] = useState<Master | null>(null);
  const [readiness, setReadiness] = useState<Readiness | null>(null);
  const [payload, setPayload] = useState(pretty(initial(unit.modality)));
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
  const current = history[0] || null;
  const historical = !!selected && selected.id !== current?.id;
  const disabled = readOnly || historical || busy;

  async function select(master: Master | null) {
    setSelected(master); setReadiness(null); setDirty(false); setAcceptContext(false);
    setPayload(pretty(master?.payload || initial(unit.modality)));
    setAssets(pretty((master?.assets || []).map((row) => ({ material_revision_id: row.material_revision_id, content_hash: row.content_hash, role: row.role, slot_key: row.slot_key, sort_order: row.sort_order, placement: row.placement }))));
    setEvidence(pretty((master?.evidence || []).map((row) => ({ fact_pack_item_id: row.fact_pack_item_id, snapshot_checksum: row.snapshot_checksum, role: row.role, sort_order: row.sort_order, locator: row.locator }))));
    setForm(master?.content_form || "");
    if (master) setReadiness(await api.get<Readiness>(`${base}/master-revisions/${master.id}/readiness`));
  }
  async function reload() {
    const result = await api.get<{ items: Master[] }>(`${base}/master-revisions`);
    setHistory(result.items); await select(result.items[0] || null);
  }
  useEffect(() => { reload().catch((cause) => setError(message(cause))).finally(() => setLoading(false)); }, [base]);
  function change(set: (value: string) => void, value: string) { set(value); setDirty(true); setNotice(""); }
  async function execute(action: () => Promise<void>) { setBusy(true); setError(""); setNotice(""); try { await action(); } catch (cause) { setError(message(cause)); } finally { setBusy(false); } }
  async function save(attest = false) {
    await execute(async () => {
      await api.post(`${base}/master-revisions`, { expected_revision: current?.revision_no || 0, expected_context_hash: current && !acceptContext ? current.context_hash : undefined, idempotency_key: crypto.randomUUID(), parent_revision_id: current?.id, payload: object(payload), content_form: form || null, asset_refs: list(assets), evidence_refs: list(evidence), render_attestation: attest && readiness ? { confirmed: true, render_input_hash: readiness.render_input_hash } : undefined });
      await reload(); setNotice("已保存新的不可变 Master 修订；Workflow 草稿未修改。");
    });
  }
  return <section className="mb-5 rounded-2xl border border-slate-200 bg-white p-5" aria-label="Content Master">
    <div className="flex flex-wrap items-center justify-between gap-3"><h2 className="text-lg font-semibold">Content Master · {unit.modality}</h2><span className="text-xs text-slate-500">{dirty ? "内容有未保存修改" : "内容已同步"} · 与 Workflow 保存独立</span></div>
    {loading ? <Spinner label="读取 Master…" /> : <div className="mt-4 space-y-4">
      {error && <ErrorBanner message={error} />}{notice && <p role="status" className="text-sm text-emerald-700">{notice}</p>}
      <div className="flex flex-wrap gap-2"><Button variant="secondary" disabled={busy} onClick={() => { if (!dirty || window.confirm("重新加载会丢弃未保存的内容编辑，继续？")) execute(reload); }}>重新加载 Master</Button>{history.map((row) => <Button key={row.id} variant={selected?.id === row.id ? "primary" : "secondary"} size="sm" disabled={busy} onClick={() => { if (!dirty || window.confirm("切换版本会丢弃未保存的内容编辑，继续？")) execute(() => select(row)); }}>Master v{row.revision_no}{row.id === current?.id ? " · 当前" : " · 历史"}</Button>)}</div>
      {selected && <div className="rounded-lg bg-slate-50 p-3 text-xs text-slate-600"><p>Master #{selected.id} · {selected.payload_schema} · {selected.source_kind}</p><p className="break-all">Payload {selected.payload_hash} / Context {selected.context_hash}</p><p>Identity #{selected.identity_snapshot_id ?? "缺失"} · Brief #{selected.creative_brief_revision_id ?? "缺失"} · Boundary #{selected.fact_boundary_revision_id ?? "缺失"}</p><StatusBadge status={selected.readiness.state} />{selected.readiness.reasons.length > 0 && <p>{selected.readiness.reasons.join("、")}</p>}</div>}
      {historical && <p className="text-sm text-amber-800">历史 Master 只读；选择当前版本后再创建新修订。</p>}
      <ModalityWorkspace modality={unit.modality} value={payload} onChange={(value) => change(setPayload, value)} readOnly={disabled} />
      <div className="grid gap-3 sm:grid-cols-2"><Field label="渠道内容形态（留空由 Registry 解析）"><input aria-label="Master 内容形态" className={inputClass} value={form} disabled={disabled} onChange={(event) => change(setForm, event.target.value)} /></Field><p className="self-center text-xs text-slate-500">渠道：{unit.channel_id || "未选择，不能冻结"}。素材来自项目共享素材，可跨 Unit 引用；不复制字节。</p></div>
      <details><summary className="cursor-pointer text-sm">精确素材与证据引用</summary><div className="mt-3 grid gap-3 sm:grid-cols-2"><Field label="Master 素材引用 JSON"><textarea aria-label="Master 素材引用 JSON" className={inputClass} rows={6} value={assets} readOnly={disabled} onChange={(event) => change(setAssets, event.target.value)} /></Field><Field label="Master 证据引用 JSON"><textarea aria-label="Master 证据引用 JSON" className={inputClass} rows={6} value={evidence} readOnly={disabled} onChange={(event) => change(setEvidence, event.target.value)} /></Field></div></details>
      {selected?.readiness.state === "stale" && <label className="flex items-center gap-2 text-sm text-amber-800"><input type="checkbox" disabled={disabled} checked={acceptContext} onChange={(event) => setAcceptContext(event.target.checked)} />明确接纳最新项目上下文，保存为新修订（历史不改写）</label>}
      <div className="flex flex-wrap gap-2"><Button disabled={disabled || (selected?.readiness.state === "stale" && !acceptContext)} onClick={() => save()}>保存内容 Master</Button><Button variant="secondary" disabled={disabled || dirty || !selected || selected.readiness.state === "stale"} onClick={() => execute(async () => { await api.post(`${base}/master-revisions/${selected!.id}/checks`); await reload(); setNotice("Master 检查已持久化；旧检查不覆盖。"); })}>运行 Master 检查</Button><Button disabled={disabled || dirty || !readiness?.candidate_freeze_available || !selected} onClick={() => execute(async () => { const frozen = await api.post<{ id: number }>(`${base}/candidates/freeze`, { content_master_revision_id: selected!.id, expected_payload_hash: selected!.payload_hash }); setCandidateId(frozen.id); setNotice(`已冻结 Candidate v4 #${frozen.id}，尚未审批。`); })}>冻结 Master Candidate v4</Button>{candidateId && <Link className="self-center text-sm text-indigo-700 underline" to={`/review?project=${projectId}&unit=${unit.id}&candidate=${candidateId}`}>审阅 Candidate #{candidateId}</Link>}</div>
      {unit.modality !== "text" && <Button variant="secondary" disabled={disabled || dirty || !selected || !readiness || selected.readiness.state !== "current"} onClick={() => { if (window.confirm("确认当前 render_output 的真实字节是此 Master 的最终渲染？确认会保存带输入哈希证明的新修订。")) save(true); }}>确认当前渲染并保存新修订</Button>}
      {unit.modality === "text" && <div className="flex flex-wrap gap-2"><select aria-label="Draft seed 输出" className={inputClass} disabled={disabled || dirty} value={outputId} onChange={(event) => setOutputId(event.target.value)}><option value="">选择真实 Draft 输出</option>{outputs.filter((row) => row.output_kind === "draft").map((row) => <option key={row.id} value={row.id}>输出 #{row.id} · Draft #{row.entity_id} · Run #{row.run_id}</option>)}</select><Button variant="secondary" disabled={disabled || dirty || !outputId} onClick={() => execute(async () => { await api.post(`${base}/master-revisions/from-output`, { expected_revision: current?.revision_no || 0, idempotency_key: crypto.randomUUID(), project_output_id: Number(outputId) }); await reload(); setNotice("已从可验证 Draft 执行输出创建新 Master；未证明的映射仍保持 incomplete。"); })}>从 Draft 创建 Text Master</Button></div>}
      {readiness && <div><h3 className="font-medium">Master 当前检查与渲染</h3><p className="mt-1 text-xs text-slate-500">{readiness.candidate_freeze_available ? "可冻结" : "不可冻结"} · {readiness.adapter_availability.reasons.join("、")}</p><div className="mt-2 flex flex-wrap gap-2">{readiness.checks.map((row) => <span key={row.check_kind} className="text-xs">{row.check_kind}: <StatusBadge status={row.status} /></span>)}</div><pre className="mt-3 max-h-56 overflow-auto rounded bg-slate-50 p-3 text-xs">{pretty({ preview: readiness.preview, render: readiness.render, checks: readiness.checks })}</pre></div>}
    </div>}
  </section>;
}
