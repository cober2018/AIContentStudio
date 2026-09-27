import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api, ApiError, currentUser } from "../api";
import { Button, EmptyState, ErrorBanner, Field, Spinner, StatusBadge, inputClass } from "../components/ui";

type Summary = "blocked" | "stale" | "waiting_review" | "ready" | "approved" | "delivery_ready" | "unknown" | "delivered";
type ReviewTarget = { id: number; status: string; action: string; account_ref: string; content_account_id: number | null; attempts: { id: number; status: string; remote_id: string | null; error: string | null }[]; receipts: { id: number; status: string; evidence_ref: string | null; note: string | null }[] };
type CandidateRef = { id: number; hash: string; status: string; title: string };
type ReviewUnit = { unit_id: number; project_id: number; title: string; modality: string; unit_status: string; persona_id: number; account_id: number | null; channel_id: string | null; summary: Summary; dimensions: Record<string, { status: string; reasons: string[] }>; current_candidate: CandidateRef | null; history: CandidateRef[]; reviews: { id: number; decision: string; comment: string | null }[]; targets: ReviewTarget[] };
type ReviewProject = { project_id: number; title: string; status: string; units: ReviewUnit[] };
type Candidate = { id: number; candidate_hash: string; status: string; manifest: Record<string, unknown> };
type Output = { id: number; output_kind: string; run_id: number; entity_id: number };
type Diff = { from_candidate_id: number | null; changed_sections: Record<string, { changed: boolean }>; text: { before_chars: number; after_chars: number; similarity: number } };
type Tab = "preview" | "changes" | "checks" | "publish";

const STATUS_NAMES: Record<Summary, string> = { blocked: "受阻", stale: "已过期", waiting_review: "待审核", ready: "就绪", approved: "已批准", delivery_ready: "待交付", unknown: "待核对", delivered: "已回填" };
const DIMENSION_NAMES: Record<string, string> = { content: "内容", evidence: "证据", identity: "身份", media: "素材权限", checks: "检查", candidate: "候选", approval: "内容审批", delivery: "交付授权" };
const TAB_NAMES: Record<Tab, string> = { preview: "预览", changes: "变更", checks: "检查", publish: "交付" };
function errorText(error: unknown) { return error instanceof ApiError ? `${error.status} · ${error.message}` : "后端请求失败，请重试。"; }

export default function ProjectReviewCenter() {
  const [query, setQuery] = useSearchParams();
  const [projects, setProjects] = useState<ReviewProject[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [filter, setFilter] = useState<Summary | "all">("all");
  const [tab, setTab] = useState<Tab>("preview");
  const [candidate, setCandidate] = useState<Candidate | null>(null);
  const [diff, setDiff] = useState<Diff | null>(null);
  const [outputs, setOutputs] = useState<Output[]>([]);
  const [outputId, setOutputId] = useState("");
  const [comment, setComment] = useState("");
  const [accountRef, setAccountRef] = useState("");
  const [accounts, setAccounts] = useState<{ id: number; name: string; status: string }[]>([]);
  const [accountId, setAccountId] = useState("");
  const [action, setAction] = useState("copy_package");
  const [authVersion, setAuthVersion] = useState("v1");
  const [receiptEvidence, setReceiptEvidence] = useState("");
  const [reconcileNote, setReconcileNote] = useState("");

  const projectId = Number(query.get("project"));
  const unitId = Number(query.get("unit"));
  const project = projects.find((row) => row.project_id === projectId) || null;
  const unit = project?.units.find((row) => row.unit_id === unitId) || null;
  const base = unit ? `/content-projects/${unit.project_id}/units/${unit.unit_id}` : "";

  async function reload() {
    const rows = await api.get<ReviewProject[]>("/review-center/projects");
    setProjects(rows);
    const requestedProject = Number(query.get("project"));
    const requestedUnit = Number(query.get("unit"));
    const selectedProject = rows.find((row) => row.project_id === requestedProject) || rows[0];
    const selectedUnit = selectedProject?.units.find((row) => row.unit_id === requestedUnit) || selectedProject?.units[0];
    if (selectedProject && selectedUnit && (requestedProject !== selectedProject.project_id || requestedUnit !== selectedUnit.unit_id)) {
      setQuery({ project: String(selectedProject.project_id), unit: String(selectedUnit.unit_id) }, { replace: true });
    }
  }
  useEffect(() => { setLoading(true); reload().catch((cause) => setError(errorText(cause))).finally(() => setLoading(false)); }, []);
  useEffect(() => {
    if (!unit) { setCandidate(null); setOutputs([]); return; }
    setCandidate(null); setDiff(null); setOutputId(""); setAccountId(String(unit.account_id || ""));
    const chosenId = Number(query.get("candidate")) || unit.current_candidate?.id;
    Promise.all([
      api.get<Output[]>(`${base}/outputs`),
      api.get<{ id: number; name: string; status: string }[]>(`/content-personas/${unit.persona_id}/accounts`),
      chosenId ? api.get<Candidate>(`/review-center/projects/${unit.project_id}/units/${unit.unit_id}/candidates/${chosenId}`) : Promise.resolve(null),
      chosenId ? api.get<Diff>(`/review-center/projects/${unit.project_id}/units/${unit.unit_id}/candidates/${chosenId}/diff`) : Promise.resolve(null),
    ]).then(([nextOutputs, nextAccounts, nextCandidate, nextDiff]) => {
      setOutputs(nextOutputs); setOutputId(String(nextOutputs.find((item) => item.output_kind === "draft")?.id || ""));
      setAccounts(nextAccounts); setCandidate(nextCandidate); setDiff(nextDiff);
    }).catch((cause) => setError(errorText(cause)));
  }, [unit?.project_id, unit?.unit_id, unit?.current_candidate?.id, query.get("candidate")]);

  async function change(actionCall: () => Promise<unknown>, success: string) {
    setBusy(true); setError(""); setNotice("");
    try {
      await actionCall(); setNotice(success); await reload();
      if (unit && candidate) {
        setCandidate(await api.get<Candidate>(`/review-center/projects/${unit.project_id}/units/${unit.unit_id}/candidates/${candidate.id}`));
      }
    }
    catch (cause) { setError(errorText(cause)); }
    finally { setBusy(false); }
  }
  function selectUnit(project: ReviewProject, next: ReviewUnit) { setQuery({ project: String(project.project_id), unit: String(next.unit_id) }); setTab("preview"); }
  function selectCandidate(id: number) { if (unit) setQuery({ project: String(unit.project_id), unit: String(unit.unit_id), candidate: String(id) }); }
  const currentCandidate = unit?.current_candidate?.id === candidate?.id;
  const archived = project?.status === "archived" || unit?.unit_status === "archived";
  const manifest = candidate?.manifest || {};
  const content = (manifest.content || {}) as Record<string, unknown>;
  const canApprove = currentCandidate && candidate?.status === "frozen" && !archived && unit?.summary !== "blocked" && unit?.summary !== "stale";
  const canAuthorize = currentCandidate && candidate?.status === "approved" && !archived;

  async function download(target: ReviewTarget) {
    setBusy(true); setError("");
    try {
      const response = await fetch(`/api/v1/delivery-targets/${target.id}/package.zip`, { headers: { "X-Studio-User": currentUser() } });
      if (!response.ok) throw new Error(`成品包下载失败 (${response.status})`);
      const url = URL.createObjectURL(await response.blob());
      const anchor = document.createElement("a"); anchor.href = url; anchor.download = `delivery-target-${target.id}.zip`; anchor.click();
      URL.revokeObjectURL(url);
      setNotice("已生成本地成品包；人工发布后再回填，不能视为平台已发布。"); await reload();
    } catch (cause) { setError(errorText(cause)); }
    finally { setBusy(false); }
  }

  return <div className="mx-auto max-w-7xl px-6 py-9">
    <div className="mb-7"><p className="text-xs font-semibold uppercase tracking-widest text-indigo-600">Project-first Review</p><h1 className="mt-2 text-3xl font-semibold">审阅与发布</h1><p className="mt-2 text-sm text-slate-500">按项目查看真实候选、审批与交付状态。旧 Topic 工作区仍在 <Link className="text-indigo-700 underline" to="/review-publish">旧审核与发布</Link>。</p></div>
    {error && <div className="mb-4"><ErrorBanner message={error} /></div>}
    {notice && <p className="mb-4 rounded-lg bg-emerald-50 p-3 text-sm text-emerald-800">{notice}</p>}
    {loading ? <Spinner label="读取项目审核…" /> : projects.length === 0 ? <EmptyState title="还没有可审阅的项目" hint="先在内容项目中创建项目和内容单元。" /> :
      <div className="grid gap-5 lg:grid-cols-[19rem_1fr]">
        <aside className="space-y-4"><Field label="状态筛选"><select className={inputClass} value={filter} onChange={(event) => setFilter(event.target.value as Summary | "all")}><option value="all">全部</option>{(Object.keys(STATUS_NAMES) as Summary[]).map((status) => <option key={status} value={status}>{STATUS_NAMES[status]}</option>)}</select></Field>
          {projects.map((row) => <section key={row.project_id} className="rounded-xl border border-slate-200 bg-white p-3"><Link className="font-semibold text-slate-900 hover:text-indigo-700" to={`/projects/${row.project_id}`}>{row.title}</Link><p className="mb-3 text-xs text-slate-500">项目 #{row.project_id}</p><div className="space-y-1">{row.units.filter((item) => filter === "all" || item.summary === filter).map((item) => <button key={item.unit_id} type="button" onClick={() => selectUnit(row, item)} className={`flex w-full items-center justify-between gap-2 rounded-lg px-3 py-2 text-left text-sm ${unit?.unit_id === item.unit_id && project?.project_id === row.project_id ? "bg-indigo-50 text-indigo-800" : "hover:bg-slate-50"}`}><span className="truncate">{item.title}</span><StatusBadge status={item.summary} /></button>)}</div></section>)}
        </aside>
        <main className="min-w-0 space-y-4">{!unit ? <EmptyState title="选择内容单元" hint="从左侧项目列表选择需要审阅的内容。" /> : <>
          <section className="rounded-xl border border-slate-200 bg-white p-5"><div className="flex flex-wrap items-center justify-between gap-3"><div><h2 className="text-xl font-semibold">{unit.title}</h2><p className="mt-1 text-xs text-slate-500">{project?.title} · {unit.modality} · {unit.channel_id || "未设渠道"}</p></div><StatusBadge status={unit.summary} /></div>
            {archived && <p className="mt-3 text-sm text-amber-800">项目或单元已归档，只能查看历史。</p>}
            {unit.summary === "unknown" && <p className="mt-3 rounded-lg bg-violet-50 p-3 text-sm text-violet-800">交付结果尚未确认，必须先对账；这里没有自动重发按钮。</p>}
            <div className="mt-4 grid gap-2 sm:grid-cols-2 xl:grid-cols-4">{Object.entries(unit.dimensions).map(([key, value]) => <div key={key} className="rounded-lg bg-slate-50 p-3"><p className="text-xs text-slate-500">{DIMENSION_NAMES[key] || key}</p><div className="mt-1"><StatusBadge status={value.status} /></div>{value.reasons.length > 0 && <p className="mt-1 break-all text-xs text-rose-700">{value.reasons.join("、")}</p>}</div>)}</div>
          </section>
          <section className="rounded-xl border border-slate-200 bg-white p-5"><h3 className="font-semibold">冻结 Candidate</h3><p className="mt-1 text-xs text-slate-500">只接受本单元可追溯的 Draft 工作流输出；纯素材或未连通来源不会假装冻结成功。</p><div className="mt-3 flex flex-wrap gap-2"><select className={inputClass} value={outputId} onChange={(event) => setOutputId(event.target.value)}><option value="">选择 Draft 输出</option>{outputs.filter((item) => item.output_kind === "draft").map((item) => <option key={item.id} value={item.id}>输出 #{item.id} · Run #{item.run_id} · Draft #{item.entity_id}</option>)}</select><Button disabled={busy || archived || !outputId} onClick={() => change(() => api.post(`${base}/candidates/freeze`, { project_output_id: Number(outputId) }), "候选已冻结；内容审批尚未发生。")}>冻结 Candidate</Button></div></section>
          <section className="rounded-xl border border-slate-200 bg-white p-5"><div className="flex flex-wrap items-center justify-between gap-3"><h3 className="font-semibold">候选历史</h3>{unit.current_candidate && <span className="text-xs text-slate-500">当前候选 #{unit.current_candidate.id}</span>}</div><div className="mt-3 flex flex-wrap gap-2">{[unit.current_candidate, ...unit.history].filter((item): item is CandidateRef => item !== null).map((item) => <Button key={item.id} size="sm" variant={candidate?.id === item.id ? "primary" : "secondary"} onClick={() => selectCandidate(item.id)}>#{item.id} · {item.title}</Button>)}</div>{!unit.current_candidate && <p className="mt-3 text-sm text-slate-500">还没有冻结候选。</p>}</section>
          {candidate && <section className="rounded-xl border border-slate-200 bg-white p-5"><div className="flex flex-wrap items-center justify-between gap-3"><div><h3 className="font-semibold">Candidate #{candidate.id}</h3><p className="mt-1 break-all text-xs text-slate-500">冻结哈希 {candidate.candidate_hash}</p></div><StatusBadge status={candidate.status} /></div><div role="tablist" className="mt-5 flex gap-2 border-b border-slate-200">{(Object.keys(TAB_NAMES) as Tab[]).map((key) => <button key={key} role="tab" aria-selected={tab === key} onClick={() => setTab(key)} className={`px-3 py-2 text-sm ${tab === key ? "border-b-2 border-indigo-600 font-semibold text-indigo-700" : "text-slate-500"}`}>{TAB_NAMES[key]}</button>)}</div>
            {tab === "preview" && <div className="mt-4 space-y-3"><h4 className="text-lg font-semibold">{String(content.title || "未命名")}</h4><pre className="max-h-96 overflow-auto whitespace-pre-wrap rounded-lg bg-slate-50 p-4 text-sm">{String(content.body_markdown || "无正文")}</pre><p className="text-xs text-slate-500">清单版本 {String(manifest.schema_version || "?")} · 身份、证据、Run 与渲染均来自冻结清单。</p></div>}
            {tab === "changes" && <div className="mt-4"><p className="text-sm text-slate-600">{diff?.from_candidate_id ? `相对于 Candidate #${diff.from_candidate_id}` : "首个 Candidate，没有前序版本"}</p><div className="mt-3 flex flex-wrap gap-2">{Object.entries(diff?.changed_sections || {}).map(([key, value]) => <span key={key} className={`rounded px-2 py-1 text-xs ${value.changed ? "bg-amber-100 text-amber-800" : "bg-slate-100 text-slate-500"}`}>{key}: {value.changed ? "有变化" : "未变"}</span>)}</div>{diff && <p className="mt-3 text-xs text-slate-500">正文长度 {diff.text.before_chars} → {diff.text.after_chars}；相似度 {Math.round(diff.text.similarity * 100)}%</p>}</div>}
            {tab === "checks" && <div className="mt-4 space-y-3"><p className="text-sm">冻结检查：{Array.isArray(manifest.checks) ? manifest.checks.length : 0} 项</p><pre className="max-h-64 overflow-auto rounded-lg bg-slate-50 p-3 text-xs">{JSON.stringify({ evidence: manifest.evidence, identity: manifest.identity, production: manifest.production, checks: manifest.checks, media: manifest.media, render: manifest.render }, null, 2)}</pre></div>}
            {tab === "publish" && !currentCandidate && <p className="mt-4 rounded-lg bg-slate-50 p-3 text-sm text-slate-600">这是历史 Candidate；交付操作只针对当前候选。历史清单仍可在预览、变更和检查中查看。</p>}
            {tab === "publish" && currentCandidate && <div className="mt-4 space-y-5"><section><h4 className="font-semibold">1. 内容审批</h4><p className="mt-1 text-xs text-slate-500">审批锁定当前 Candidate ID 与哈希；冻结本身不等于批准。</p><textarea className={`${inputClass} mt-2`} value={comment} onChange={(event) => setComment(event.target.value)} placeholder="审核意见（退改时建议填写）" /><div className="mt-2 flex gap-2"><Button disabled={busy || !canApprove} onClick={() => change(() => api.post(`${base}/candidates/${candidate.id}/approve`, { candidate_hash: candidate.candidate_hash, comment }), "内容审批已记录。")}>批准内容</Button><Button variant="secondary" disabled={busy || archived || !currentCandidate} onClick={() => change(() => api.post(`${base}/candidates/${candidate.id}/request-changes`, { candidate_hash: candidate.candidate_hash, comment }), "退改意见已记录，冻结清单保持不变。")}>要求修改</Button></div></section>
              <section className="border-t border-slate-200 pt-4"><h4 className="font-semibold">2. 交付授权</h4><p className="mt-1 text-xs text-slate-500">只提供人工包/复制包；当前 ContentAccount 没有已验证的远端发布映射，不开放自动草稿。</p><div className="mt-3 grid gap-3 sm:grid-cols-2"><Field label="内容账号"><select className={inputClass} value={accountId} onChange={(event) => setAccountId(event.target.value)}><option value="">不绑定稳定账号（保留人工账号引用）</option>{accounts.filter((row) => row.status === "active").map((row) => <option key={row.id} value={row.id}>{row.name}</option>)}</select></Field><Field label="账号引用"><input className={inputClass} value={accountRef} onChange={(event) => setAccountRef(event.target.value)} placeholder="人工发布账号标识" /></Field><Field label="动作"><select className={inputClass} value={action} onChange={(event) => setAction(event.target.value)}><option value="copy_package">复制成品包</option><option value="manual_handoff">人工交付包</option></select></Field><Field label="授权版本"><input className={inputClass} value={authVersion} onChange={(event) => setAuthVersion(event.target.value)} /></Field></div><Button className="mt-3" disabled={busy || !canAuthorize || !accountRef.trim() || !unit.channel_id} onClick={() => change(() => api.post(`${base}/candidates/${candidate.id}/delivery-authorizations`, { channel: unit.channel_id, content_form: String(manifest.content_form || "article"), account_ref: accountRef.trim(), content_account_id: accountId ? Number(accountId) : null, authorization_version: authVersion.trim(), action }), "交付目标已授权；尚未发布。")}>授权交付目标</Button></section>
              <section className="border-t border-slate-200 pt-4"><h4 className="font-semibold">3. 交付与回填</h4>{unit.targets.length === 0 ? <p className="mt-2 text-sm text-slate-500">当前候选暂无交付目标。</p> : unit.targets.map((target) => <div key={target.id} className="mt-3 rounded-lg border border-slate-200 p-4"><div className="flex flex-wrap items-center justify-between gap-2"><p className="font-medium">目标 #{target.id} · {target.account_ref}</p><StatusBadge status={target.status} /></div><p className="mt-1 text-xs text-slate-500">{target.action} · {target.content_account_id ? `ContentAccount #${target.content_account_id}` : "账号映射未验证"}</p><div className="mt-3 flex flex-wrap gap-2"><Button variant="secondary" disabled={busy || archived || target.status === "reconciliation_needed" || target.status === "blocked"} onClick={() => download(target)}>下载成品包 ZIP</Button></div>{target.attempts.map((attempt) => <p key={attempt.id} className="mt-2 text-xs text-slate-600">Attempt #{attempt.id} · {attempt.status}{attempt.remote_id ? ` · 远端 ${attempt.remote_id}` : ""}{attempt.error ? ` · ${attempt.error}` : ""}</p>)}{target.receipts.map((receipt) => <p key={receipt.id} className="mt-2 text-xs text-slate-600">Receipt #{receipt.id} · {receipt.status}{receipt.evidence_ref ? ` · ${receipt.evidence_ref}` : ""}</p>)}{target.status === "reconciliation_needed" ? <div className="mt-3 space-y-2"><input className={inputClass} value={reconcileNote} onChange={(event) => setReconcileNote(event.target.value)} placeholder="对账说明" /><div className="flex gap-2"><Button disabled={busy || archived} onClick={() => change(() => api.post(`/delivery-targets/${target.id}/reconcile`, { resolution: "delivered", note: reconcileNote }), "已人工确认交付结果。")}>确认已交付</Button><Button variant="secondary" disabled={busy || archived} onClick={() => change(() => api.post(`/delivery-targets/${target.id}/reconcile`, { resolution: "not_delivered", note: reconcileNote }), "已确认未交付；如需再次执行，请明确重新操作。")}>确认未交付</Button></div></div> : <div className="mt-3 flex flex-wrap gap-2"><input className={inputClass} value={receiptEvidence} onChange={(event) => setReceiptEvidence(event.target.value)} placeholder="回执链接或证据引用" /><Button disabled={busy || archived || !["awaiting_manual_receipt", "failed"].includes(target.status)} onClick={() => change(() => api.post(`/delivery-targets/${target.id}/receipt`, { status: "human_confirmed", evidence_ref: receiptEvidence || null }), "人工回填已保存；这不是平台自动验证。")}>回填人工发布</Button></div>}</div>)}</section>
            </div>}
          </section>}</>}</main>
      </div>}
  </div>;
}
