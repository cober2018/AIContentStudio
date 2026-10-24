import { useTaskLink, taskReturn } from "./taskNavigation";
import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api, ApiError, currentUser } from "../api";
import { Button, EmptyState, ErrorBanner, Field, Page, PageHeader, Spinner, StatusBadge, Tabs, inputClass } from "../components/ui";
import { CandidatePreview } from "./CandidatePreview";
import type { FrozenPreview } from "./CandidatePreview";

type Summary = "blocked" | "stale" | "waiting_review" | "ready" | "approved" | "delivery_ready" | "unknown" | "delivered";
type ReviewTarget = { id: number; status: string; action: string; publisher_key?: string; publisher_version?: string; account_ref: string; content_account_id: number | null; attempts: { id: number; status: string; remote_id: string | null; error: string | null }[]; receipts: { id: number; status: string; evidence_ref: string | null; note: string | null }[] };
type CandidateRef = { id: number; hash: string; status: string; title: string };
type ReviewUnit = { unit_id: number; project_id: number; title: string; modality: string; unit_status: string; persona_id: number | null; production_domain?: "product" | "persona"; account_id: number | null; channel_id: string | null; summary: Summary; dimensions: Record<string, { status: string; reasons: string[] }>; current_candidate: CandidateRef | null; legacy_current_candidate: CandidateRef | null; variantSeries?: { variantKey: string; candidateId: number; candidateHash: string; status: string; channel: string; contentForm: string; targetStatuses: string[] }[]; history: CandidateRef[]; reviews: { id: number; decision: string; comment: string | null }[]; targets: ReviewTarget[] };
type ReviewProject = { project_id: number; title: string; status: string; units: ReviewUnit[] };
type Candidate = { id: number; candidate_hash: string; status: string; manifest: Record<string, unknown>; preview: FrozenPreview };
type Output = { id: number; output_kind: string; run_id: number; entity_id: number };
type Diff = { from_candidate_id: number | null; changed_sections: Record<string, { changed: boolean }>; structured?: { id?: string; block_id?: string; kind?: string; changes?: string[] }[] | Record<string, unknown> | null; text: { before_chars: number; after_chars: number; similarity: number } | null };
type Tab = "preview" | "issues" | "authorization" | "delivery" | "history";
type Account = { id: number; name: string; status: string; platform_channel?: string | null };
type Draft = { outputId: string; comment: string; warningDispositions: Record<string, string>; accountRef: string; accountId: string; action: string; authVersion: string; receipts: Record<string, string>; reconciliations: Record<string, string> };
const EMPTY_DRAFT: Draft = { outputId: "", comment: "", warningDispositions: {}, accountRef: "", accountId: "", action: "copy_package", authVersion: "v1", receipts: {}, reconciliations: {} };
function readDraft(key: string): Draft { try { return { ...EMPTY_DRAFT, ...JSON.parse(sessionStorage.getItem(key) || "null") }; } catch { return { ...EMPTY_DRAFT }; } }

const STATUS_NAMES: Record<Summary, string> = { blocked: "受阻", stale: "已过期", waiting_review: "待审核", ready: "就绪", approved: "已批准", delivery_ready: "待交付", unknown: "待核对", delivered: "已回填" };
const DIMENSION_NAMES: Record<string, string> = { content: "内容", evidence: "证据", identity: "身份", media: "素材权限", checks: "检查", candidate: "候选", approval: "内容审批", delivery: "交付授权" };
const TAB_NAMES: Record<Tab, string> = { preview: "核对作品", issues: "问题与审批", authorization: "账号与授权", delivery: "交付与回填", history: "历史与变更" };
function errorText(error: unknown) { return error instanceof ApiError ? `${error.status} · ${error.message}` : error instanceof Error ? error.message : "后端请求失败，请重试。"; }
function latestAttempt(target: ReviewTarget) { return target.attempts.reduce<ReviewTarget["attempts"][number] | null>((head, item) => !head || item.id > head.id ? item : head, null); }
function officialDraft(target: ReviewTarget) { return target.publisher_key === "publisher.wechat.official" && target.publisher_version === "1" && target.action === "auto_draft"; }
function needsReconciliation(target: ReviewTarget) { return target.status === "reconciliation_needed" || officialDraft(target) && target.status === "target_authorized" && ["prepared", "running"].includes(latestAttempt(target)?.status || ""); }

const REASON_NAMES: Record<string, string> = {
  candidate_missing: "还没有冻结作品", freeze_required: "需要在制作工作台冻结作品", identity_unready: "角色身份尚未就绪",
  product_context_missing: "商品资料尚未就绪", product_configuration_unavailable: "商品配置暂时不可用", evidence_unready: "证据资料尚未就绪",
  project_boundary_changed: "项目证据范围已变更，需要重新核对并冻结", fact_pack_changed: "事实包已变更，需要重新核对并冻结",
  evidence_rights_unready: "证据使用权限尚未确认", media_rights_unready: "素材使用权限尚未确认", candidate_integrity_unready: "冻结版本完整性尚未核实",
  newer_draft_revision: "已有更新稿件，请回制作工作台核对", approval_pending: "此渠道候选尚待内容审批", authorization_missing: "此渠道尚未授权交付目标",
  stale_master: "源作品已更新，需要重新检查和冻结", historical_candidate: "当前查看的是历史候选", readiness_blocked: "制作检查尚未通过",
};
function reasonText(reason: string) { const [key, ...detail] = reason.split(":"); const name = REASON_NAMES[key]; return name ? `${name}${detail.length ? `（${detail.join(":")}）` : ""}` : "需核对检查说明"; }

export default function ProjectReviewCenter() {
  const [query, setQuery] = useSearchParams();
  const user = currentUser();
  const [data, setData] = useState<{ user: string; projects: ReviewProject[] }>({ user: "", projects: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [access, setAccess] = useState<{ user: string; role: string; error: string }>({ user: "", role: "", error: "" });
  const [busy, setBusy] = useState(false);
  const lock = useRef(false);
  const request = useRef(0);
  const alive = useRef(true);
  useEffect(() => { alive.current = true; return () => { alive.current = false; request.current++; }; }, []);
  const projects = data.user === user ? data.projects : [];
  const role = access.user === user ? access.role : "";
  const scope = `${user}:${query.get("project")}:${query.get("unit")}:${query.get("candidate")}`;
  async function reload() {
    const version = ++request.current;
    setLoading(true); setError("");
    try {
      const rows = await api.get<ReviewProject[]>("/review-center/projects");
      if (alive.current && currentUser() === user && request.current === version) setData({ user, projects: rows });
    } catch (cause) {
      if (alive.current && currentUser() === user && request.current === version) setError(errorText(cause));
      throw cause;
    } finally { if (alive.current && currentUser() === user && request.current === version) setLoading(false); }
  }
  useEffect(() => {
    void reload().catch(() => {});
    let active = true;
    setAccess({user, role: "", error: ""});
    api.get<{ role: string }>("/users/me").then(next => { if (active && currentUser() === user) setAccess({ user, role: next.role, error: "" }); })
      .catch(cause => { if (active && currentUser() === user) setAccess({ user, role: "", error: `权限读取失败，当前只读：${errorText(cause)}` }); });
    return () => { active = false; request.current++; };
  }, [user]);
  async function mutate(call: () => Promise<unknown>) {
    if (lock.current || currentUser() !== user) return false;
    lock.current = true; setBusy(true);
    try { await call(); return true; }
    finally { lock.current = false; if (alive.current) setBusy(false); }
  }
  function update(values: Record<string, string | null>) {
    const next = new URLSearchParams(query);
    Object.entries(values).forEach(([key, value]) => value === null || value === "" ? next.delete(key) : next.set(key, value));
    setQuery(next);
  }
  const detail = query.has("project") || query.has("unit");
  const project = projects.find(row => row.project_id === Number(query.get("project"))) || null;
  const unit = project?.units.find(row => row.unit_id === Number(query.get("unit"))) || null;
  const filter = query.get("status") || "all";
  const search = query.get("q") || "";
  const rows = projects.flatMap(project => project.units.map(unit => ({ project, unit })))
    .filter(row => (filter === "all" || row.unit.summary === filter) && `${row.project.title} ${row.unit.title}`.toLowerCase().includes(search.toLowerCase()))
    .sort((a, b) => Number(b.unit.summary === "unknown") - Number(a.unit.summary === "unknown"));
  const pages = Math.max(1, Math.ceil(rows.length / 20));
  const rawPage = Number(query.get("page") || 1);
  const page = Math.min(pages, Number.isSafeInteger(rawPage) && rawPage > 0 ? rawPage : 1);
  const returnQuery = new URLSearchParams(query); ["project", "unit", "candidate", "step"].forEach(key => returnQuery.delete(key));
  const back = `/review${returnQuery.size ? `?${returnQuery}` : ""}`;
  const MODALITY: Record<string, string> = { text: "文字", graphic: "图文", video: "视频", audio: "音频" };
  const pageRows = rows.slice((page - 1) * 20, page * 20);
  const groups = pageRows.reduce<{ project: (typeof pageRows)[number]["project"]; items: typeof pageRows }[]>((all, row) => { const last = all[all.length - 1]; if (last && last.project.project_id === row.project.project_id) last.items.push(row); else all.push({ project: row.project, items: [row] }); return all; }, []);
  return <Page>
    {!detail && <PageHeader eyebrow="发布与增长" title="审阅与交付" lead="核对冻结的作品，处理问题，再分别确认账号授权与交付。只浏览不会批准或交付任何作品。" />}
    {access.user === user && access.error && <ErrorBanner message={access.error} />}
    {error && <ErrorBanner message={`作品清单读取失败：${error}`} />}
    {error && <Button variant="secondary" disabled={loading || busy} onClick={() => void reload().catch(() => {})}>重新读取作品清单</Button>}
    {detail ? <><Link className="-mb-2 inline-block text-[13px] text-ink-500 hover:text-ink-900" to={back}>← 审阅与交付</Link>
      {!unit || !project ? loading ? <Spinner label="读取作品…" /> : error ? <p className="text-sm text-slate-600">作品尚未核实，请重新读取清单后再核对链接。</p> : <EmptyState title="无法找到指定作品" hint="请核对项目与作品链接，或返回作品列表选择；不会自动打开其他作品。" /> :
        <ReviewDetail key={`${scope}:${unit.current_candidate?.id || 0}`} user={user} project={project} unit={unit} role={role} busy={busy} verified={!error && !loading} query={query} update={update} mutate={mutate} reload={reload} />}
    </> : <>
      <div className="flex flex-wrap items-center gap-3"><div className="relative min-w-[220px] flex-1 sm:max-w-sm"><input aria-label="搜索项目或作品" className={`${inputClass} pl-9`} value={search} onChange={event => update({q: event.target.value, page: null})} placeholder="搜索项目或作品" /><span aria-hidden className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-ink-400">⌕</span></div>
        <select aria-label="状态筛选" className={`${inputClass} !w-auto`} value={filter} onChange={event => update({status: event.target.value === "all" ? null : event.target.value, page: null})}><option value="all">全部状态</option>{Object.entries(STATUS_NAMES).map(([value, name]) => <option key={value} value={value}>{name}</option>)}</select>{!loading && !error && <span className="ml-auto text-[13px] text-ink-500">{rows.length} 个作品</span>}</div>
      {loading ? <Spinner label="读取审阅作品…" /> : !error && <>
        {!rows.length ? <EmptyState title="没有符合条件的作品" hint="可调整搜索或状态，或先在原制作工作台完成作品并冻结。" /> : <div className="space-y-8">{groups.map(group => <section key={group.project.project_id} aria-label={group.project.title}>
          <h2 className="mb-3 flex items-baseline gap-3 font-serif text-[18px] font-semibold text-ink-900"><span className="min-w-0 truncate">{group.project.title}</span><span className="shrink-0 font-sans text-[12.5px] font-normal text-ink-500">{group.items.length} 个作品</span></h2>
          <ul className="card divide-y divide-ink-200/80 overflow-hidden">{group.items.map(({project, unit}) => <li key={`${project.project_id}:${unit.unit_id}`}><button type="button" onClick={() => update({project: String(project.project_id), unit: String(unit.unit_id), candidate: null, step: null})} className="group flex w-full flex-wrap items-center justify-between gap-3 px-5 py-4 text-left transition-colors hover:bg-ink-50"><span className="flex min-w-0 items-center gap-3"><span className="shrink-0 rounded-pill bg-ink-100 px-2 py-0.5 text-[11.5px] text-ink-600">{MODALITY[unit.modality] || unit.modality}</span><span className="min-w-0 truncate text-[14.5px] text-ink-900">{unit.title}</span></span><span className="flex items-center gap-4"><StatusBadge status={unit.summary} /><span className="text-[13px] font-medium text-ink-500 transition-colors group-hover:text-accent-600">核对 →</span></span></button></li>)}</ul>
        </section>)}</div>}
        {pages > 1 && <div className="flex items-center justify-center gap-3"><Button size="sm" variant="secondary" disabled={page <= 1} onClick={() => update({page: String(page - 1)})}>上一页</Button><span className="text-[13px] text-ink-500">第 {page} / {pages} 页</span><Button size="sm" variant="secondary" disabled={page >= pages} onClick={() => update({page: String(page + 1)})}>下一页</Button></div>}
      </>}
    </>}
    <details className="text-sm text-slate-500"><summary className="cursor-pointer">兼容入口</summary><Link className="mt-2 inline-block text-indigo-700 underline" to="/review-publish">旧 Topic 审核与发布</Link></details>
  </Page>;
}

function ReviewDetail({ user, project, unit, role, busy, verified, query, update, mutate, reload }: {
  user: string; project: ReviewProject; unit: ReviewUnit; role: string; busy: boolean; verified: boolean; query: URLSearchParams;
  update: (values: Record<string, string | null>) => void; mutate: (call: () => Promise<unknown>) => Promise<boolean>; reload: () => Promise<void>;
}) {
  const taskLink = useTaskLink();
  const rawId = query.get("candidate");
  const selectedCandidateId = rawId === null ? unit.current_candidate?.id || null : Number.isSafeInteger(Number(rawId)) && Number(rawId) > 0 ? Number(rawId) : null;
  const selectionKey = `${user}:${unit.project_id}:${unit.unit_id}:${rawId ?? selectedCandidateId ?? "none"}`;
  const draftKey = `studio-review:${selectionKey}`;
  const [draft, setDraft] = useState<Draft>(() => readDraft(draftKey));
  function patchDraft(values: Partial<Draft>) { setDraft(previous => { const next = { ...previous, ...values }; try { sessionStorage.setItem(draftKey, JSON.stringify(next)); } catch { /* Browser storage must not block explicit decisions. */ } return next; }); }
  const { outputId, comment, warningDispositions, accountRef, accountId, action, authVersion } = draft;
  const setOutputId = (value: string) => patchDraft({outputId: value});
  const setComment = (value: string) => patchDraft({comment: value});
  const setWarningDispositions = (value: Record<string, string>) => patchDraft({warningDispositions: value});
  const setAccountRef = (value: string) => patchDraft({accountRef: value});
  const setAccountId = (value: string) => patchDraft({accountId: value});
  const setAction = (value: string) => patchDraft({action: value});
  const setAuthVersion = (value: string) => patchDraft({authVersion: value});
  const [candidate, setCandidate] = useState<Candidate | null>(null);
  const [candidateTargets, setCandidateTargets] = useState<ReviewTarget[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [outputs, setOutputs] = useState<Output[]>([]);
  const [diff, setDiff] = useState<Diff | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [loaded, setLoaded] = useState<Record<string, boolean>>({});
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [revision, setRevision] = useState(0);
  const active = useRef(true);
  const readVersion = useRef(0);
  useEffect(() => { active.current = true; return () => { active.current = false; readVersion.current++; }; }, []);
  const base = `/content-projects/${unit.project_id}/units/${unit.unit_id}`;
  const candidatePath = selectedCandidateId ? `/review-center/projects/${unit.project_id}/units/${unit.unit_id}/candidates/${selectedCandidateId}` : "";
  const domain = unit.production_domain || (unit.persona_id == null ? "product" : "persona");
  const tab = (Object.keys(TAB_NAMES).includes(query.get("step") || "") ? query.get("step") : "preview") as Tab;
  const setTab = (step: Tab) => update({step: step === "preview" ? null : step});
  useEffect(() => {
    let live = true;
    const version = ++readVersion.current;
    const valid = () => live && active.current && currentUser() === user && version === readVersion.current;
    setCandidate(null); setCandidateTargets([]); setAccounts([]); setOutputs([]); setDiff(null); setLoaded({}); setErrors({});
    async function read<T>(key: string, path: string, apply: (value: T) => void) {
      try { const next = await api.get<T>(path); if (valid()) { apply(next); setLoaded(state => ({...state, [key]: true})); } }
      catch (cause) { if (valid()) setErrors(state => ({...state, [key]: errorText(cause)})); }
    }
    void read<Output[]>("outputs", `${base}/outputs`, setOutputs);
    if (domain === "product") void read<Account[]>("accounts", "/content-accounts", setAccounts);
    else if (unit.persona_id && unit.persona_id > 0) void read<Account[]>("accounts", `/content-personas/${unit.persona_id}/accounts`, setAccounts);
    else setErrors(state => ({...state, accounts: "角色标识无效，无法读取账号。"}));
    if (candidatePath) {
      void read<Candidate>("candidate", candidatePath, next => { if (next.id !== selectedCandidateId) throw new Error("候选响应与指定版本不一致，请重新读取。"); setCandidate(next); });
      void read<Diff>("diff", `${candidatePath}/diff`, setDiff);
      void read<ReviewTarget[]>("targets", `/assets/${selectedCandidateId}/delivery-targets`, setCandidateTargets);
    }
    return () => { live = false; };
  }, [selectionKey, domain, unit.persona_id, revision]);
  const candidateMatchesSelection = !!candidate && candidate.id === selectedCandidateId;
  const manifest = candidateMatchesSelection ? candidate.manifest : {};
  const isV5 = manifest.schema_version === 5;
  const frozenTarget = (manifest.target || {}) as { channel?: string; content_form?: string; artifact_kind?: string; account?: { content_account_id: number; platform_channel: string } };
  const currentCandidate = candidateMatchesSelection && (isV5 ? !!unit.variantSeries?.some(row => row.candidateId === candidate.id && row.candidateHash === candidate.candidate_hash) : unit.legacy_current_candidate?.id === candidate.id && unit.legacy_current_candidate.hash === candidate.candidate_hash);
  const archived = project.status === "archived" || unit.unit_status === "archived";
  const canEdit = ["admin", "editor"].includes(role) && !archived && verified;
  const canReview = ["admin", "editor", "reviewer"].includes(role) && !archived && verified;
  const sourceWarnings = ((manifest.source_master as { warning_checks?: { id: number; input_hash: string; status: string; kind: string; report?: unknown }[] } | undefined)?.warning_checks) || [];
  const warnings = isV5 ? sourceWarnings : ((manifest.checks || []) as { id: number; input_hash: string; status: string; kind: string; report?: unknown }[]).filter(row => row.status === "warning");
  const canApprove = currentCandidate && candidate?.status === "frozen" && canReview;
  const frozenAccountId = isV5 ? frozenTarget.account?.content_account_id : undefined;
  const deliveryAccountId = frozenAccountId ? String(frozenAccountId) : accountId;
  const deliveryAccounts = accounts.filter(row => row.status === "active" && (!isV5 || row.platform_channel === frozenTarget.channel) && (!frozenAccountId || row.id === frozenAccountId));
  const accountCompatible = frozenAccountId ? deliveryAccounts.some(row => String(row.id) === deliveryAccountId) : !deliveryAccountId || deliveryAccounts.some(row => String(row.id) === deliveryAccountId);
  const canAuthorize = currentCandidate && candidate?.status === "approved" && canEdit && loaded.accounts && loaded.targets && accountCompatible;
  async function change(actionCall: () => Promise<unknown>, success: string, allowed = canEdit && currentCandidate) {
    if (!allowed || busy || !active.current || currentUser() !== user) return;
    setError(""); setNotice("");
    try {
      const done = await mutate(actionCall);
      if (!done || !active.current || currentUser() !== user) return;
      setNotice(success); setRevision(value => value + 1);
      await reload();
    } catch (cause) { if (active.current && currentUser() === user) setError(errorText(cause)); }
  }
  function selectCandidate(id: number) { update({candidate: String(id)}); }
  async function reconcileTarget(target: ReviewTarget, resolution: "delivered" | "not_delivered") {
    const evidence = (draft.reconciliations[target.id] || "").trim();
    if (!canEdit || !currentCandidate || !loaded.targets || !evidence || busy || !window.confirm(resolution === "delivered" ? "已在平台核对这个账号的交付结果？只保存人工回执，不代表平台验证或公开发布。" : "已核对平台确实没有本次交付结果？不会自动重发。")) return;
    const latest = latestAttempt(target);
    await change(async () => {
      const bytes = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(evidence));
      if (!active.current || currentUser() !== user) return;
      const hash = Array.from(new Uint8Array(bytes), byte => byte.toString(16).padStart(2, "0")).join("");
      return api.post(`/delivery-targets/${target.id}/reconcile`, { resolution, evidence_ref: `sha256:${hash}`, expected_attempt_id: latest?.id ?? null });
    }, resolution === "delivered" ? "人工核验回执已保存；不是平台自动验证或公开发布。" : "未交付证据已保存，不会自动重发。");
  }
  async function readbackTarget(target: ReviewTarget) {
    const latest = latestAttempt(target);
    if (!canEdit || !currentCandidate || !loaded.targets || busy || !officialDraft(target) || target.status !== "reconciliation_needed" || latest?.status !== "unknown" || !latest.remote_id || !window.confirm(`只回读目标 #${target.id} 的已知草稿（Attempt #${latest.id}），不会创建新草稿；是否继续？`)) return;
    await change(() => api.post(`/delivery-targets/${target.id}/official-readback`, {expected_attempt_id: latest.id}), "已请求精确草稿回读；未创建新草稿，也不代表公开发布。");
  }
  async function download(target: ReviewTarget) {
    if (!canEdit || !currentCandidate || !loaded.targets || needsReconciliation(target) || target.status === "blocked") return;
    await change(async () => {
      const response = await fetch(`/api/v1/delivery-targets/${target.id}/package.zip`, {headers: {"X-Studio-User": user}});
      if (!response.ok) throw new Error(`成品包下载失败 (${response.status})`);
      const blob = await response.blob();
      if (!active.current || currentUser() !== user) return;
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a"); anchor.href = url; anchor.download = `delivery-target-${target.id}.zip`; anchor.click(); URL.revokeObjectURL(url);
    }, "已生成本地成品包；人工发布后再回填，不能视为平台已发布。");
  }
  return <main className="min-w-0 space-y-4">
    {error && <ErrorBanner message={error} />}
    {notice && <p role="status" className="rounded-lg bg-emerald-50 p-3 text-sm text-emerald-800">{notice}</p>}
    {Object.entries(errors).map(([key, message]) => <ErrorBanner key={key} message={`${({candidate: "候选", accounts: "账号", outputs: "旧输出", diff: "版本比较", targets: "交付记录"} as Record<string, string>)[key] || key}读取失败：${message}`} />)}
    {!!Object.keys(errors).length && <Button variant="secondary" disabled={busy} onClick={() => setRevision(value => value + 1)}>重新读取作品详情</Button>}
          <section className="rounded-xl border border-slate-200 bg-white p-5"><div className="flex flex-wrap items-center justify-between gap-3"><div><h2 className="text-xl font-semibold">{unit.title}</h2><p className="mt-1 text-xs text-slate-500">{project?.title} · {unit.modality} · {unit.channel_id || "未设渠道"}</p></div><StatusBadge status={unit.summary} /></div>
            {archived && <p className="mt-3 text-sm text-amber-800">项目或单元已归档，只能查看历史。</p>}
            {unit.summary === "unknown" && <p className="mt-3 rounded-lg bg-violet-50 p-3 text-sm text-violet-800">交付结果尚未确认，必须先对账；这里没有自动重发按钮。</p>}
            <ul aria-label="当前需处理的问题" className="mt-3 space-y-1 text-xs leading-relaxed text-amber-900">{Object.entries(unit.dimensions).filter(([, value]) => !["ready", "pass", "approved", "delivered"].includes(value.status) || value.reasons.length > 0).map(([key, value]) => <li key={key} className="break-words"><span className="font-medium">{DIMENSION_NAMES[key] || key}：</span>{value.reasons.length ? value.reasons.map(reasonText).join("；") : STATUS_NAMES[value.status as Summary] || "需要核对当前状态"}</li>)}{warnings.length > 0 && <li>当前候选有 {warnings.length} 项检查提醒，需在问题与审批页逐项核对：{warnings.map(row => row.kind).join("、")}</li>}</ul>
            <details className="mt-3 text-xs text-slate-600"><summary className="cursor-pointer">全部核对状态与检查原文</summary><ul className="mt-2 space-y-2">{Object.entries(unit.dimensions).map(([key, value]) => <li key={key}><div className="flex flex-wrap items-center gap-2"><span>{DIMENSION_NAMES[key] || key}</span><StatusBadge status={value.status} /></div>{value.reasons.length > 0 && <p className="mt-1 break-all text-slate-500">{value.reasons.join("、")}</p>}</li>)}</ul></details>
          </section>

    {!canReview && <p className="text-sm text-slate-600">当前只读；审批、授权和交付需要相应角色权限。</p>}
    {tab === "delivery" && <p className="text-sm text-slate-600">实际公开发布后，再同步发布记录与表现数据；ZIP和人工交付回执不等于公开发布。 <Link className="text-indigo-700 underline" to={taskLink("/learning?tab=history&view=sync")}>下一步：发布后效果复盘 →</Link></p>}
    <Tabs label="审阅与交付步骤" value={tab} onChange={key => setTab(key as Tab)} items={Object.entries(TAB_NAMES) as [Tab, string][]} />
    <section className="flex flex-wrap items-center justify-between gap-3 rounded-xl bg-indigo-50 p-4" aria-label="当前下一步">
      <p className="text-sm text-slate-700">{selectedCandidateId && !loaded.candidate ? errors.candidate ? "候选读取失败，请重新读取；当前不能审批或交付。" : "正在核对指定冻结版本，请等待读取完成。" : !candidateMatchesSelection ? "先在制作工作台完成作品并冻结，再开始审阅。" : !currentCandidate ? "历史版本仅供核对；请在历史页选择当前渠道候选。" : tab === "preview" ? "先核对冻结正文和当前问题，再处理内容审批。" : tab === "issues" ? candidate?.status === "approved" ? "内容已经批准，下一步单独确认账号和交付授权。" : "逐项核对当前问题并填写提醒处置说明，再明确批准或要求修改。" : tab === "authorization" ? !loaded.targets ? "交付目标尚未核实，请等待或明确重新读取。" : candidateTargets.length ? "已有交付目标，下一步检查目标状态并交付或对账。" : "先批准当前内容，再确认账号并显式授权交付目标。" : tab === "delivery" ? "核对每个目标的状态；未知结果须先对账，ZIP和人工回执不等于公开发布。" : "按渠道核对候选和版本变化；选择历史版本不会改变当前作品。"}</p>
      {tab === "preview" && <Button disabled={!candidateMatchesSelection} onClick={() => setTab("issues")}>下一步：处理问题与审批</Button>}
      {tab === "issues" && <Button variant="secondary" disabled={!currentCandidate || candidate?.status !== "approved"} onClick={() => setTab("authorization")}>下一步：账号与授权</Button>}
      {tab === "authorization" && <Button variant="secondary" disabled={!currentCandidate || !loaded.targets || !candidateTargets.length} onClick={() => setTab("delivery")}>下一步：交付与回填</Button>}
    </section>
    {taskReturn(query.get("return_to")) && <Link className="block text-sm text-indigo-700 underline" to={taskReturn(query.get("return_to"))}>返回来源页面</Link>}
    <Link className="inline-block text-sm text-indigo-700 underline" to={taskLink(`/projects/${unit.project_id}/units/${unit.unit_id}/production?workstep=${domain === "product" ? "review" : "delivery"}`)}>返回制作工作台修改内容</Link>
    {tab === "preview" && <details className="rounded-xl border border-slate-200 bg-white p-4"><summary className="cursor-pointer text-sm text-slate-600">旧 Draft 冻结兼容入口</summary>          <section className="rounded-xl border border-slate-200 bg-white p-5"><h3 className="font-semibold">冻结 Candidate</h3><p className="mt-1 text-xs text-slate-500">旧 Draft 输出保持 v3 冻结；Content Master v4 在生产工作台完成检查后显式冻结。</p><div className="mt-3 flex flex-wrap gap-2"><select className={inputClass} value={outputId} onChange={(event) => setOutputId(event.target.value)}><option value="">选择 Draft 输出</option>{outputs.filter((item) => item.output_kind === "draft").map((item) => <option key={item.id} value={item.id}>输出 #{item.id} · Run #{item.run_id} · Draft #{item.entity_id}</option>)}</select><Button disabled={busy || !canEdit || !loaded.outputs || !outputs.some(row => row.id === Number(outputId) && row.output_kind === "draft")} onClick={() => change(() => api.post(`${base}/candidates/freeze`, { project_output_id: Number(outputId) }), "候选已冻结；内容审批尚未发生。", canEdit && !!loaded.outputs)}>冻结 Candidate</Button></div></section>
</details>}
    {tab === "history" && <>          <section className="rounded-xl border border-slate-200 bg-white p-5"><div className="flex flex-wrap items-center justify-between gap-3"><h3 className="font-semibold">候选历史</h3>{unit.current_candidate && <span className="text-xs text-slate-500">最近候选 #{unit.current_candidate.id}；v5 按渠道系列独立判断当前性</span>}</div>{!!unit.variantSeries?.length && <div className="mt-3 flex flex-wrap gap-2">{unit.variantSeries.map((series) => <Button key={series.variantKey} size="sm" variant={candidate?.id === series.candidateId ? "primary" : "secondary"} onClick={() => selectCandidate(series.candidateId)}>{series.channel}/{series.contentForm} · #{series.candidateId} · {series.status}</Button>)}</div>}<div className="mt-3 flex flex-wrap gap-2">{[unit.current_candidate, ...unit.history].filter((item): item is CandidateRef => item !== null).map((item) => <Button key={item.id} size="sm" variant={candidate?.id === item.id ? "primary" : "secondary"} onClick={() => selectCandidate(item.id)}>#{item.id} · {item.title}</Button>)}</div>{!unit.current_candidate && <p className="mt-3 text-sm text-slate-500">还没有冻结候选。</p>}</section>
{unit.current_candidate && unit.reviews.length > 0 && <section className="rounded-xl border border-slate-200 bg-white p-4"><h3 className="font-semibold">最近候选 #{unit.current_candidate.id} 的审批记录</h3>{selectedCandidateId !== unit.current_candidate.id && <p className="mt-2 text-sm text-amber-800">这些记录属于最近候选，不代表当前选中候选的审批结果。</p>}{unit.reviews.map(row => <p key={row.id} className="mt-2 break-words text-sm text-slate-600">{row.decision}{row.comment ? ` · ${row.comment}` : ""}</p>)}</section>}</>}
    {!selectedCandidateId && <EmptyState title={rawId !== null ? "指定候选标识无效" : "还没有冻结候选"} hint={rawId !== null ? "请核对原链接或在历史页明确选择候选；不会替换为其他候选。" : "请先返回制作工作台完成检查并显式冻结，再来核对作品。"} />}
    {selectedCandidateId && !loaded.candidate && !errors.candidate && <Spinner label="读取冻结候选…" />}
    {candidateMatchesSelection && candidate && <section className="rounded-xl border border-slate-200 bg-white p-4 sm:p-5">
      <div className="flex flex-wrap items-center justify-between gap-3"><h3 className="font-semibold">{candidate.preview.title || unit.title} · 候选 #{candidate.id}</h3><StatusBadge status={candidate.status} /></div>
      {!currentCandidate && <p className="mt-3 rounded-lg bg-amber-50 p-3 text-sm text-amber-800">这是历史候选，只有阅读权限；请在历史页明确选择当前渠道候选后操作。</p>}
      <details className="mt-3 text-xs text-slate-500"><summary className="cursor-pointer">冻结版本技术信息</summary><p className="mt-2 break-all">冻结哈希 {candidate.candidate_hash}</p><pre className="mt-2 max-h-64 overflow-auto whitespace-pre-wrap break-all">{JSON.stringify(manifest, null, 2)}</pre></details>
            {tab === "preview" && <CandidatePreview preview={candidate.preview} path={`/review-center/projects/${unit.project_id}/units/${unit.unit_id}/candidates/${candidate.id}`} assets={isV5 && Array.isArray(manifest.assets) ? manifest.assets as { material_revision_id: number; content_hash_snapshot: string; role: string; slot_key: string | null; mime_type?: string }[] : []} />}
            {tab === "history" && <div className="mt-4">{!loaded.diff && !errors.diff && <Spinner label="读取变更比较…" />}{loaded.diff && <><p className="text-sm text-slate-600">{diff?.from_candidate_id ? `相对于 Candidate #${diff.from_candidate_id}` : "此系列首个 Candidate，没有前序版本"}</p><div className="mt-3 flex flex-wrap gap-2">{Object.entries(diff?.changed_sections || {}).map(([key, value]) => <span key={key} className={`rounded px-2 py-1 text-xs ${value.changed ? "bg-amber-100 text-amber-800" : "bg-slate-100 text-slate-500"}`}>{key}: {value.changed ? "有变化" : "未变"}</span>)}</div>{Array.isArray(diff?.structured) && diff.structured.length > 0 && <ul className="mt-3 space-y-1 text-xs text-slate-600">{diff.structured.map((row, index) => <li key={`${row.id || row.block_id}-${index}`}>{row.id || row.block_id || "区段"} · {row.changes?.join("/") || row.kind || "已变化"}</li>)}</ul>}{diff?.text ? <p className="mt-3 text-xs text-slate-500">正文长度 {diff.text.before_chars} → {diff.text.after_chars}；相似度 {Math.round(diff.text.similarity * 100)}%</p> : <p className="mt-3 text-xs text-slate-500">图文/视频按结构化区段比较，不计算文本相似度。</p>}</>}</div>}
            {tab === "issues" && <div className="mt-4 space-y-3"><p className="text-sm">冻结检查：{Array.isArray(manifest.checks) ? manifest.checks.length : 0} 项；来源 Master 提醒：{sourceWarnings.length} 项</p><details><summary className="cursor-pointer text-sm text-slate-600">技术检查报告与冻结清单</summary><pre className="max-h-64 overflow-auto rounded-lg bg-slate-50 p-3 text-xs">{JSON.stringify({ evidence: manifest.evidence, identity: manifest.identity, production: manifest.production, source_warnings: sourceWarnings, checks: manifest.checks, media: manifest.media, render: manifest.render }, null, 2)}</pre></details></div>}

      {tab === "issues" && <div className="mt-4 space-y-4"><section><h4 className="font-semibold">1. 内容审批</h4><p className="mt-1 text-xs text-slate-500">审批锁定当前 Candidate ID 与哈希；冻结本身不等于批准。</p><textarea aria-label="审核意见" className={`${inputClass} mt-2`} value={comment} onChange={(event) => setComment(event.target.value)} placeholder="审核意见（退改时建议填写）" />{warnings.map((row) => <Field key={row.id} label={`检查提醒 #${row.id}`}><p className="mb-2 text-xs text-amber-800">{row.kind} · 冻结检查的具体覆盖与原因：</p><details><summary className="cursor-pointer text-xs text-slate-500">查看检查证据</summary><pre className="mb-2 max-h-40 overflow-auto rounded bg-amber-50 p-2 text-xs">{JSON.stringify(row.report || {}, null, 2)}</pre></details><textarea aria-label={`Warning #${row.id} 处置说明`} className={inputClass} value={warningDispositions[`${row.id}:${row.input_hash}`] || ""} onChange={(event) => setWarningDispositions({ ...warningDispositions, [`${row.id}:${row.input_hash}`]: event.target.value })} placeholder="明确接受/处理此检查提醒的理由；不会把warning改成pass" /></Field>)}<div className="mt-2 flex gap-2"><Button disabled={busy || !canApprove || warnings.some((row) => !warningDispositions[`${row.id}:${row.input_hash}`]?.trim())} onClick={() => change(() => api.post(`${base}/candidates/${candidate.id}/approve`, { candidate_hash: candidate.candidate_hash, comment, warning_dispositions: warningDispositions }), "内容审批已记录。", canApprove)}>批准内容</Button><Button variant="secondary" disabled={busy || !canReview || !currentCandidate} onClick={() => change(() => api.post(`${base}/candidates/${candidate.id}/request-changes`, { candidate_hash: candidate.candidate_hash, comment }), "退改意见已记录，冻结清单保持不变。", canReview && currentCandidate)}>要求修改</Button></div></section>
</div>}
      {tab === "authorization" && <div className="mt-4 space-y-4">{!loaded.accounts && !errors.accounts && <Spinner label="读取交付账号…" /> }<p className="text-sm text-slate-500">{domain === "product" ? "商品作品使用自有账号目录。" : "角色作品沿用原角色账号目录。"}冻结账号保持不变，最终资格由服务核验。</p>              <section className="border-t border-slate-200 pt-4"><h4 className="font-semibold">2. 交付授权</h4><p className="mt-1 text-xs text-slate-500">{isV5 ? `冻结目标 ${frozenTarget.channel}/${frozenTarget.content_form}；` : ""}只提供人工包/复制包；当前 ContentAccount 没有已验证的远端发布映射，不开放自动草稿。</p><div className="mt-3 grid gap-3 sm:grid-cols-2"><Field label="内容账号"><select aria-label="冻结候选交付账号" className={inputClass} value={deliveryAccountId} disabled={!!frozenAccountId || !loaded.accounts || !canEdit || !currentCandidate} onChange={(event) => setAccountId(event.target.value)}>{!frozenAccountId && <option value="">{loaded.accounts ? "不绑定稳定账号（保留人工账号引用）" : "账号目录尚未核实"}</option>}{deliveryAccountId && !deliveryAccounts.some(row => String(row.id) === deliveryAccountId) && <option value={deliveryAccountId} disabled>{loaded.accounts ? "账号已失效或不属于冻结目标平台" : "冻结账号目录尚未核实"}</option>}{deliveryAccounts.map(row => <option key={row.id} value={row.id}>{row.name} · #{row.id}</option>)}</select>{frozenAccountId && <p className="mt-1 text-xs text-slate-500">冻结账号 #{frozenAccountId}；其他账号须独立适配、冻结与审批。</p>}</Field><Field label="账号引用"><input className={inputClass} value={accountRef} onChange={(event) => setAccountRef(event.target.value)} placeholder="人工发布账号标识" /></Field><Field label="动作"><select className={inputClass} value={action} onChange={(event) => setAction(event.target.value)}><option value="copy_package">复制成品包</option><option value="manual_handoff">人工交付包</option></select></Field><Field label="授权版本"><input className={inputClass} value={authVersion} onChange={(event) => setAuthVersion(event.target.value)} /></Field></div><Button className="mt-3" disabled={busy || !canAuthorize || !accountRef.trim() || !authVersion.trim() || !(isV5 ? frozenTarget.channel : unit.channel_id)} onClick={() => change(() => api.post(`${base}/candidates/${candidate.id}/delivery-authorizations`, { channel: isV5 ? frozenTarget.channel : unit.channel_id, content_form: isV5 ? frozenTarget.content_form : String(manifest.content_form || "article"), account_ref: accountRef.trim(), content_account_id: deliveryAccountId ? Number(deliveryAccountId) : null, authorization_version: authVersion.trim(), action }), "交付目标已授权；尚未发布。")}>授权交付目标</Button></section>
</div>}
      {tab === "delivery" && <div className="mt-4 space-y-4">{isV5 && <HandoffGuide channel={frozenTarget.channel} form={frozenTarget.content_form} />}              <section className="border-t border-slate-200 pt-4"><h4 className="font-semibold">3. 交付与回填</h4>{!loaded.targets ? errors.targets ? <p className="mt-2 text-sm text-rose-700">交付记录未核实，相关操作不可用。</p> : <Spinner label="读取交付记录…" /> : candidateTargets.length === 0 ? <p className="mt-2 text-sm text-slate-500">当前候选暂无交付目标。</p> : candidateTargets.map((target) => <div key={target.id} className="mt-3 rounded-lg border border-slate-200 p-4"><div className="flex flex-wrap items-center justify-between gap-2"><p className="font-medium">目标 #{target.id} · {target.account_ref}</p><StatusBadge status={target.status} /></div><p className="mt-1 text-xs text-slate-500">{target.action} · {target.content_account_id ? `ContentAccount #${target.content_account_id}` : "账号映射未验证"}</p><div className="mt-3 flex flex-wrap gap-2"><Button variant="secondary" disabled={busy || !canEdit || !currentCandidate || !loaded.targets || needsReconciliation(target) || target.status === "blocked"} onClick={() => download(target)}>下载成品包 ZIP</Button></div>{target.attempts.map((attempt) => <p key={attempt.id} className="mt-2 text-xs text-slate-600">Attempt #{attempt.id} · {attempt.status}{attempt.remote_id ? ` · 远端 ${attempt.remote_id}` : ""}{attempt.error ? ` · ${attempt.error}` : ""}</p>)}{target.receipts.map((receipt) => <p key={receipt.id} className="mt-2 text-xs text-slate-600">Receipt #{receipt.id} · {receipt.status}{receipt.evidence_ref ? ` · ${receipt.evidence_ref}` : ""}</p>)}{officialDraft(target) && target.status === "reconciliation_needed" && latestAttempt(target)?.status === "unknown" && latestAttempt(target)?.remote_id && <Button variant="secondary" disabled={busy || !canEdit || !currentCandidate || !loaded.targets} onClick={() => readbackTarget(target)}>回读已知草稿（不重建）</Button>}{needsReconciliation(target) ? <div className="mt-3 space-y-2"><input className={inputClass} aria-label={`目标 #${target.id} 对账依据`} value={draft.reconciliations[target.id] || ""} onChange={(event) => patchDraft({reconciliations: {...draft.reconciliations, [target.id]: event.target.value}})} maxLength={2000} placeholder="平台核验依据（仅提交本地 SHA-256 摘要，不上传原文）" /><div className="flex gap-2"><Button disabled={busy || !canEdit || !currentCandidate || !loaded.targets || !(draft.reconciliations[target.id] || "").trim()} onClick={() => reconcileTarget(target, "delivered")}>确认已交付</Button><Button variant="secondary" disabled={busy || !canEdit || !currentCandidate || !loaded.targets || !(draft.reconciliations[target.id] || "").trim()} onClick={() => reconcileTarget(target, "not_delivered")}>确认未交付</Button></div></div> : <div className="mt-3 flex flex-wrap gap-2"><input className={inputClass} aria-label={`目标 #${target.id} 回执证据`} value={draft.receipts[target.id] || ""} onChange={(event) => patchDraft({receipts: {...draft.receipts, [target.id]: event.target.value}})} placeholder="回执链接或证据引用" /><Button disabled={busy || !canEdit || !currentCandidate || !loaded.targets || !["awaiting_manual_receipt", "failed"].includes(target.status)} onClick={() => change(() => api.post(`/delivery-targets/${target.id}/receipt`, { status: "human_confirmed", evidence_ref: draft.receipts[target.id] || null }), "人工回填已保存；这不是平台自动验证。")}>{officialDraft(target) ? "确认草稿交付（非公开发布）" : "回填人工回执"}</Button></div>}</div>)}</section>
</div>}
    </section>}
  </main>;
}

function HandoffGuide({ channel, form }: { channel?: string; form?: string }) {
  const content = form === "spoken_script" ? "使用脚本、口播与明确标为估算的 SRT；包内 B-roll 为精确素材版本。脚本包没有最终 MP4。"
    : form === "image_note" ? "按冻结图卡顺序上传真实成品图片，粘贴标题、图说与说明；保留引用与声明。"
    : form === "thread" ? "按冻结推串顺序逐条复制正文；保留每条对应的引用与声明。"
    : form === "long_post" ? "将冻结长正文交给 X 长帖编辑器；这是长帖形态。账号是否支持该形态需在平台核对。"
    : form === "articles" ? "将冻结标题、概要与嵌套正文交给 X Articles 编辑器；按 manifest 配置图片和引用。账号资格需在平台核对。"
    : form === "answer" ? "核对冻结的已确认问题、链接与背景，在对应问题下使用首段直接回答和后续正文。"
    : form === "single" ? "复制冻结单条正文，按 manifest 上传配图；保留标签、引用与声明。"
    : "使用包内安全 HTML/结构化正文，按 manifest 的顺序与位置插入精确图片，保留来源与声明。";
  return <section aria-label="本形态交付说明" className="rounded-lg bg-indigo-50 p-4 text-xs text-slate-700"><h4 className="font-semibold">{channel}/{form} · 本地人工交接</h4><p className="mt-2">{content}</p><p className="mt-2">下载 ZIP 只生成本地包；请在对应平台人工发布并回填回执。</p>{channel === "wechat" && <p className="mt-2">公众号自动草稿是另一个经过授权与能力验证的动作；本地 ZIP 不会调用草稿箱，草稿交付也不等于公开发布。</p>}</section>;
}
