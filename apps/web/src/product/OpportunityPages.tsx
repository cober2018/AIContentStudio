import { useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, ApiError, currentUser } from "../api";
import { Button, EmptyState, ErrorBanner, Field, Modal, Spinner, inputClass } from "../components/ui";
import type { Assessment, AssessmentRevision, Conversion, Opportunity, OpportunitySignal, OpportunityStatus } from "./opportunityTypes";

const base = "/content-opportunities";
const card = "rounded-xl border border-slate-200 bg-white p-6 space-y-4";
const statuses: Record<OpportunityStatus, string> = { new: "待判断", watching: "观察中", qualified: "可转项目", dismissed: "已暂缓", converted: "已转项目", archived: "已归档" };
const priorities = { high: "高", normal: "普通", low: "低" };
const triage: OpportunityStatus[] = ["new", "watching", "qualified", "dismissed"];
const signalNames: Record<string, string> = { manual: "人工观察", source_document: "来源文档", data_snapshot: "数据快照", delivery_feedback: "交付反馈", external_ref: "外部引用" };
function errorMessage(error: unknown) { return error instanceof Error ? error.message : "读取后端失败，请重试。"; }
function utcDate(value: string) { return /(?:Z|[+-]\d{2}:\d{2})$/i.test(value) ? value : `${value}Z`; }
function expired(item: Opportunity) { return !!item.relevant_until && Date.parse(utcDate(item.relevant_until)) < Date.now(); }

function OpportunityFields({ initial, busy, submit }: { initial?: Opportunity; busy: boolean; submit: (body: unknown) => void }) {
  const [title, setTitle] = useState(initial?.title ?? "");
  const [summary, setSummary] = useState(initial?.summary ?? "");
  const [priority, setPriority] = useState(initial?.priority ?? "normal");
  const [until, setUntil] = useState(initial?.relevant_until ? utcDate(initial.relevant_until) : "");
  const [error, setError] = useState("");
  function save(event: FormEvent) {
    event.preventDefault();
    if (until && (!/(?:Z|[+-]\d{2}:\d{2})$/i.test(until) || Number.isNaN(Date.parse(until)))) { setError("有效期请输入完整日期时间，例如 2026-10-01T18:00:00+08:00。"); return; }
    submit({ title: title.trim(), summary, priority, relevant_until: until ? new Date(until).toISOString() : null });
  }
  return <form onSubmit={save} className="space-y-4">
    {error && <ErrorBanner message={error} />}
    <Field label="机会名称"><input required maxLength={300} className={inputClass} value={title} onChange={(e) => setTitle(e.target.value)} /></Field>
    <Field label="概述"><textarea className={inputClass} value={summary} onChange={(e) => setSummary(e.target.value)} /></Field>
    <Field label="优先级"><select className={inputClass} value={priority} onChange={(e) => setPriority(e.target.value as Opportunity["priority"])}>{Object.entries(priorities).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></Field>
    <Field label="有效期（可选，含时区）"><input className={inputClass} value={until} onChange={(e) => setUntil(e.target.value)} /></Field>
    <Button type="submit" disabled={busy || !title.trim()}>{busy ? "保存中…" : "保存机会"}</Button>
  </form>;
}

export function OpportunitiesPage() {
  const navigate = useNavigate();
  const user = currentUser();
  const [status, setStatus] = useState("");
  const [priority, setPriority] = useState("");
  const [offset, setOffset] = useState(0);
  const [creating, setCreating] = useState(false);
  const query = useQuery({ queryKey: ["opportunities", user, status, priority, offset], queryFn: () => api.get<{ items: Opportunity[]; offset: number; limit: number; has_more: boolean }>(`${base}?${new URLSearchParams({ status, priority, offset: String(offset), limit: "30" })}`) });
  const create = useMutation({ mutationFn: (body: unknown) => api.post<Opportunity>(base, body), onSuccess: (item) => navigate(`/opportunities/${item.id}`) });
  return <div className="mx-auto max-w-7xl space-y-6 px-6 py-9">
    <header className="flex items-start justify-between gap-4"><div><p className="text-xs font-semibold tracking-widest text-indigo-600">Content Opportunities</p><h1 className="mt-2 text-3xl font-semibold">内容机会</h1><p className="mt-2 text-sm text-slate-500">先判断为什么现在做，再明确创建项目。人工评估是主要入口。</p></div><Button onClick={() => { create.reset(); setCreating(true); }}>新建机会</Button></header>
    <div className="flex gap-3"><Field label="状态"><select className={inputClass} value={status} onChange={(e) => { setStatus(e.target.value); setOffset(0); }}><option value="">全部状态</option>{Object.entries(statuses).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></Field><Field label="优先级"><select className={inputClass} value={priority} onChange={(e) => { setPriority(e.target.value); setOffset(0); }}><option value="">全部优先级</option>{Object.entries(priorities).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></Field><Button variant="secondary" onClick={() => void query.refetch()}>刷新</Button></div>
    {query.isPending ? <Spinner /> : query.isError ? <ErrorBanner message={errorMessage(query.error)} /> : <>
      {query.data.items.length === 0 ? <EmptyState title="没有符合条件的内容机会" /> : <div className="grid gap-4 lg:grid-cols-2">{query.data.items.map((item) => <Link className={card} key={item.id} to={`/opportunities/${item.id}`}><div className="flex justify-between gap-3"><h2 className="font-semibold">{item.title}</h2><span className="text-xs text-indigo-700">{statuses[item.status]}</span></div><p className="text-sm text-slate-600">{item.summary || "暂无概述"}</p><p className="text-xs text-slate-500">优先级：{priorities[item.priority]} · {item.signal_count} 条信号 · {item.latest_assessment ? `评估 v${item.latest_assessment.revision_no}` : "尚未评估"}{expired(item) ? " · 已超过有效期" : ""}</p><p className="text-sm">为什么现在：{item.latest_assessment?.assessment.why_now || "尚未判断"}</p><p className="text-xs text-slate-500">信号来源：{item.signal_types.map((type) => signalNames[type] || type).join("、") || "未添加"}</p></Link>)}</div>}
      <div className="flex items-center gap-3"><Button variant="secondary" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - 30))}>上一页</Button><span className="text-sm">第 {Math.floor(offset / 30) + 1} 页</span><Button variant="secondary" disabled={!query.data.has_more} onClick={() => setOffset(offset + 30)}>下一页</Button></div>
    </>}
    {creating && <Modal title="新建内容机会" onClose={() => { if (!create.isPending) setCreating(false); }}>{create.isError && <ErrorBanner message={errorMessage(create.error)} />}<OpportunityFields busy={create.isPending} submit={(body) => create.mutate(body)} /></Modal>}
  </div>;
}

export function OpportunityDetailPage() {
  const { id } = useParams();
  return id && /^\d+$/.test(id) ? <OpportunityDetail key={id} id={Number(id)} /> : <ErrorBanner message="内容机会编号无效。" />;
}

function OpportunityDetail({ id }: { id: number }) {
  const user = currentUser();
  const client = useQueryClient();
  const path = `${base}/${id}`;
  const [editing, setEditing] = useState(false);
  const [revisionId, setRevisionId] = useState<number | null>(null);
  const detail = useQuery({ queryKey: ["opportunity", user, id], queryFn: () => api.get<Opportunity>(path) });
  const signals = useQuery({ queryKey: ["opportunity-signals", user, id], queryFn: () => api.get<OpportunitySignal[]>(`${path}/signals`) });
  const revisions = useQuery({ queryKey: ["opportunity-assessments", user, id], queryFn: () => api.get<AssessmentRevision[]>(`${path}/assessments`) });
  const conversion = useQuery({ queryKey: ["opportunity-conversion", user, id], queryFn: () => api.get<Conversion | null>(`${path}/conversion`) });
  const historical = useQuery({ queryKey: ["opportunity-revision", user, id, revisionId], queryFn: () => api.get<AssessmentRevision>(`${path}/assessments/${revisionId}`), enabled: revisionId !== null });
  async function refresh() {
    await Promise.all(["opportunity", "opportunity-signals", "opportunity-assessments", "opportunity-conversion", "opportunities", "home"].map((key) => client.invalidateQueries({ queryKey: [key] })));
  }
  const change = useMutation({ mutationFn: (body: unknown) => api.patch<Opportunity>(path, body), onSuccess: async () => { setEditing(false); await refresh(); } });
  const archive = useMutation({ mutationFn: () => api.del(path), onSuccess: refresh });
  if (detail.isPending) return <Spinner />;
  if (detail.isError) return <div className="p-6"><ErrorBanner message={errorMessage(detail.error)} /><Button onClick={() => void detail.refetch()}>重试</Button></div>;
  const item = detail.data;
  const readonly = item.status === "converted" || item.status === "archived";
  const busy = change.isPending || archive.isPending;
  return <div className="mx-auto max-w-6xl space-y-6 px-6 py-9">
    <Link className="text-sm text-indigo-700" to="/opportunities">← 内容机会</Link>
    <header><h1 className="text-3xl font-semibold">{item.title}</h1><p className="mt-3 text-slate-600">{item.summary}</p><p className="mt-2 text-sm">{statuses[item.status]} · 优先级 {priorities[item.priority]}{expired(item) ? " · 已超过有效期" : ""}{readonly ? " · 只读" : ""}</p></header>
    {(change.isError || archive.isError) && <ErrorBanner message={errorMessage(change.error || archive.error)} />}
    <div className="flex flex-wrap gap-2">{!readonly && <><Button variant="secondary" disabled={busy} onClick={() => { change.reset(); setEditing(true); }}>编辑机会</Button>{triage.filter((status) => status !== item.status).map((status) => <Button key={status} variant="secondary" disabled={busy} onClick={() => change.mutate({ status })}>{statuses[status]}</Button>)}</>}{item.status !== "archived" && <Button variant="danger" disabled={busy} onClick={() => { if (window.confirm("归档这个内容机会？历史评估和项目关系将保留。")) archive.mutate(); }}>归档</Button>}<Button variant="secondary" disabled={busy} onClick={() => void refresh()}>刷新</Button></div>
    <section className={card}><h2 className="font-semibold">来源信号</h2><p className="text-xs text-slate-500">信号与来源是评估输入，尚未成为已批准的项目证据。</p>{signals.isPending ? <Spinner /> : signals.isError ? <ErrorBanner message={errorMessage(signals.error)} /> : <><SignalList signals={signals.data} path={readonly ? undefined : path} saved={refresh} />{!readonly && <SignalForm path={path} saved={refresh} />}</>}</section>
    <section className={card}><div className="flex items-center justify-between"><h2 className="font-semibold">评估与修订历史</h2><span className="text-xs text-slate-500">自动分析不可用 · 请人工评估</span></div>
      {revisions.isPending ? <Spinner /> : revisions.isError ? <ErrorBanner message={errorMessage(revisions.error)} /> : <Field label="查看不可变评估版本"><select className={inputClass} value={revisionId ?? ""} onChange={(e) => setRevisionId(e.target.value ? Number(e.target.value) : null)}><option value="">当前评估</option>{revisions.data.map((rev) => <option key={rev.id} value={rev.id}>v{rev.revision_no} · {rev.created_by || "作者未知"} · {rev.created_at || "时间未知"}</option>)}</select></Field>}
      {revisionId !== null ? historical.isPending ? <Spinner /> : historical.isError ? <ErrorBanner message={errorMessage(historical.error)} /> : <AssessmentView revision={historical.data} /> : <><AssessmentView revision={item.latest_assessment} />{!readonly && signals.isSuccess && <AssessmentForm key={item.latest_assessment?.id ?? 0} path={path} current={item.latest_assessment} signals={signals.data} saved={refresh} />}</>}
    </section>
    <section className={card}><h2 className="font-semibold">创建内容项目</h2>{conversion.isPending ? <Spinner /> : conversion.isError ? <ErrorBanner message={errorMessage(conversion.error)} /> : conversion.data ? <><Link className="text-indigo-700" to={`/projects/${conversion.data.project_id}`}>打开已创建项目 #{conversion.data.project_id} →</Link><Link className="block text-sm text-indigo-700" to={`/projects/${conversion.data.project_id}?tab=evidence`}>查看项目来源与事实边界 →</Link></> : item.status === "qualified" && item.latest_assessment && signals.isSuccess ? <ConversionForm key={item.latest_assessment.id} item={item} signals={signals.data} saved={refresh} /> : <p className="text-sm text-slate-500">{item.status === "converted" ? "转换关系缺失，请刷新核对；不要重复创建项目。" : "先保存人工评估并将机会标记为可转项目。"}</p>}</section>
    {editing && <Modal title="编辑内容机会" onClose={() => { if (!busy) setEditing(false); }}>{change.isError && <ErrorBanner message={errorMessage(change.error)} />}<OpportunityFields initial={item} busy={busy} submit={(body) => change.mutate(body)} /></Modal>}
  </div>;
}

function SignalList({ signals, path, saved }: { signals: OpportunitySignal[]; path?: string; saved: () => Promise<void> }) {
  const detach = useMutation({ mutationFn: (signalId: number) => api.del(`${path}/signals/${signalId}`), onSuccess: saved });
  return <div className="space-y-3">
    {detach.isError && <ErrorBanner message={errorMessage(detach.error)} />}
    {signals.length === 0 ? <p className="text-sm text-slate-500">尚无信号。</p> : <ul className="space-y-3">{signals.map((signal) => <li key={signal.id} className="rounded-lg border border-slate-200 p-3 text-sm">
      <p>#{signal.id} · {signalNames[signal.signal_type] || signal.signal_type} · {signal.label}{signal.status === "detached" ? " · 已解除引用" : ""}</p>
      <p className="mt-1 text-xs text-slate-500">来源 ID：{signal.source_entity_id ?? "无外部实体血缘"} · 版本：{signal.source_version ?? "未知"} · checksum：{signal.source_checksum ?? "未知"} · 观察时间：{signal.observed_at ?? "未知"}</p>
      {signal.external_ref && <p className="break-all text-xs">外部引用：{signal.external_ref}</p>}
      <pre className="mt-2 whitespace-pre-wrap break-all text-xs">{JSON.stringify(signal.annotation, null, 2)}</pre>
      {signal.signal_type === "source_document" && signal.source_entity_id && <Link className="text-indigo-700" to="/sources">打开来源库 · 手动查找 Source #{signal.source_entity_id} →</Link>}
      {path && signal.status !== "detached" && <Button className="mt-2" variant="secondary" size="sm" disabled={detach.isPending} onClick={() => { if (window.confirm(`解除信号 #${signal.id} 的当前引用？历史评估与原始来源将保留。`)) detach.mutate(signal.id); }}>解除信号引用</Button>}
    </li>)}</ul>}
  </div>;
}

function SignalForm({ path, saved }: { path: string; saved: () => Promise<void> }) {
  const [type, setType] = useState("manual");
  const [entityId, setEntityId] = useState("");
  const [label, setLabel] = useState("");
  const [external, setExternal] = useState("");
  const [annotation, setAnnotation] = useState("");
  const add = useMutation({ mutationFn: () => api.post(`${path}/signals`, { signal_type: type, source_entity_id: ["manual", "external_ref"].includes(type) ? null : Number(entityId), external_ref: type === "external_ref" ? external : null, label, annotation: { note: annotation } }), onSuccess: async () => { setLabel(""); setAnnotation(""); await saved(); } });
  return <form className="grid gap-3 sm:grid-cols-2" onSubmit={(e) => { e.preventDefault(); add.mutate(); }}><Field label="信号类型"><select className={inputClass} value={type} onChange={(e) => setType(e.target.value)}>{Object.entries(signalNames).map(([value, name]) => <option key={value} value={value}>{name}</option>)}</select></Field>{!["manual", "external_ref"].includes(type) && <Field label="已存在的来源实体 ID"><input required type="number" min={1} step={1} className={inputClass} value={entityId} onChange={(e) => setEntityId(e.target.value)} /></Field>}<Field label="标签（可选，留空使用后端来源名称）"><input maxLength={300} className={inputClass} value={label} onChange={(e) => setLabel(e.target.value)} /></Field>{type === "external_ref" && <Field label="外部引用"><input required maxLength={1000} className={inputClass} value={external} onChange={(e) => setExternal(e.target.value)} /></Field>}<Field label="观察备注"><textarea maxLength={4000} className={inputClass} value={annotation} onChange={(e) => setAnnotation(e.target.value)} /></Field><div className="sm:col-span-2">{add.isError && <ErrorBanner message={errorMessage(add.error)} />}<Button type="submit" disabled={add.isPending}>追加信号</Button></div></form>;
}

const textFields = { what_happened: "发生了什么", why_now: "为什么现在做", brand_relevance: "品牌相关性", audience_fit: "受众匹配", suggested_angle: "建议切入角度（suggested）" } as const;
function AssessmentView({ revision }: { revision: AssessmentRevision | null }) {
  if (!revision) return <p className="text-sm text-slate-500">尚未评估，不代表没有风险或没有相似内容。</p>;
  const data = revision.assessment;
  return <div className="space-y-2 text-sm">
    <p className="text-xs text-slate-500">v{revision.revision_no} · {revision.created_by || "作者未知"} · {revision.created_at || "时间未知"} · checksum {revision.checksum}</p>
    {Object.entries(textFields).map(([key, label]) => <p key={key}><span className="text-slate-500">{label}：</span>{data[key as keyof typeof textFields] || "未记录"}</p>)}
    <p className="whitespace-pre-wrap">证据概述：{data.evidence_summary?.join("\n") || "未记录"}</p>
    <p>时效性：{data.time_sensitivity ? { high: "高", medium: "中", low: "低", timeless: "长期有效" }[data.time_sensitivity] : "未知"}</p>
    <p>置信度：{data.confidence == null ? "未知" : `${Math.round(data.confidence * 100)}%`} · 风险：{data.risk_flags?.length ? data.risk_flags.join("、") : "未记录风险，不能视为无风险"}</p>
    <p>相似历史：{data.similarity_state === "none" ? "评估记录为无相似内容" : data.similarity_state === "possible" ? "可能相似，需人工核对" : "unknown · 未知／未核对"}</p>
    <p>建议身份 / 形态 / 渠道（suggested，未批准）：</p>
    <pre className="whitespace-pre-wrap break-all text-xs">{JSON.stringify({ recommended_identity_refs: data.recommended_identity_refs ?? [], recommended_modalities: data.recommended_modalities ?? [], recommended_channels: data.recommended_channels ?? [], evidence_signal_ids: data.evidence_signal_ids ?? [], similar_content_refs: data.similar_content_refs ?? [] }, null, 2)}</pre>
  </div>;
}

function AssessmentForm({ path, current, signals, saved }: { path: string; current: AssessmentRevision | null; signals: OpportunitySignal[]; saved: () => Promise<void> }) {
  const [draft, setDraft] = useState<Assessment>({ what_happened: "", why_now: "", brand_relevance: "", audience_fit: "", suggested_angle: "", time_sensitivity: "timeless", recommended_identity_refs: [], recommended_modalities: [], recommended_channels: [], evidence_signal_ids: [], evidence_summary: [], risk_flags: [], similarity_state: "unknown", similar_content_refs: [], confidence: null, ...current?.assessment });
  const [identities, setIdentities] = useState(JSON.stringify(draft.recommended_identity_refs));
  const [similar, setSimilar] = useState(JSON.stringify(draft.similar_content_refs));
  const [error, setError] = useState("");
  const save = useMutation({ mutationFn: (assessment: Assessment) => api.post(`${path}/assessments`, { expected_revision: current?.revision_no ?? 0, assessment }), onSuccess: saved });
  function submit(event: FormEvent) {
    event.preventDefault(); setError("");
    try {
      const refs: unknown = JSON.parse(identities); const history: unknown = JSON.parse(similar);
      if (!Array.isArray(refs) || refs.some((ref) => !ref || typeof ref !== "object" || Array.isArray(ref)) || !Array.isArray(history)) throw new Error("身份建议需为对象数组，相似内容引用需为 JSON 数组。");
      if (history.some((ref) => !ref || typeof ref !== "object" || Array.isArray(ref) || Object.keys(ref).length !== 1 || !Number.isInteger(ref.project_id) || ref.project_id < 1)) throw new Error("相似内容引用需为仅包含正整数 project_id 的对象数组。");
      save.mutate({ ...draft, recommended_identity_refs: refs as Record<string, unknown>[], similar_content_refs: history });
    } catch (err) { setError(errorMessage(err)); }
  }
  return <form onSubmit={submit} className="space-y-4 border-t border-slate-200 pt-4"><h3 className="font-medium">追加人工评估 · 基于 v{current?.revision_no ?? 0}</h3><fieldset disabled={save.isPending} className="grid gap-3 sm:grid-cols-2">
    {Object.entries(textFields).map(([key, label]) => <Field key={key} label={label}><textarea required={key === "why_now"} maxLength={5000} className={inputClass} value={draft[key as keyof typeof textFields] ?? ""} onChange={(e) => setDraft({ ...draft, [key]: e.target.value })} /></Field>)}
    <Field label="证据概述（每行一条，最多 30 条）"><textarea className={inputClass} defaultValue={draft.evidence_summary.join("\n")} onChange={(e) => setDraft({ ...draft, evidence_summary: e.target.value.split("\n").map((line) => line.trim()).filter(Boolean) })} /></Field>
    <Field label="时效性"><select className={inputClass} value={draft.time_sensitivity} onChange={(e) => setDraft({ ...draft, time_sensitivity: e.target.value as Assessment["time_sensitivity"] })}>{Object.entries({ high: "高", medium: "中", low: "低", timeless: "长期有效" }).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></Field>
    <Field label="相似历史判断"><select className={inputClass} value={draft.similarity_state} onChange={(e) => setDraft({ ...draft, similarity_state: e.target.value as Assessment["similarity_state"] })}><option value="unknown">未知／未核对</option><option value="none">人工确认无相似内容</option><option value="possible">可能相似</option></select></Field>
    <Field label="置信度（0–1，可留空表示未知）"><input className={inputClass} type="number" min={0} max={1} step="any" value={draft.confidence ?? ""} onChange={(e) => setDraft({ ...draft, confidence: e.target.value === "" ? null : Number(e.target.value) })} /></Field>
    {(["recommended_modalities", "recommended_channels", "risk_flags"] as const).map((key) => <Field key={key} label={{ recommended_modalities: "建议形态（suggested，逗号分隔）", recommended_channels: "建议渠道（suggested，逗号分隔）", risk_flags: "风险标记（逗号分隔）" }[key]}><input className={inputClass} defaultValue={draft[key].join(", ")} onChange={(e) => setDraft({ ...draft, [key]: e.target.value.split(/[,，]/).map((text) => text.trim()).filter(Boolean) })} /></Field>)}
    <Field label="建议身份引用（suggested，JSON 数组）" hint="使用已有 brand_id / persona_id / account_id / series_id；服务端校验可见层级。"><textarea className={inputClass} value={identities} onChange={(e) => setIdentities(e.target.value)} /></Field><Field label="相似内容引用（JSON 数组）"><textarea className={inputClass} value={similar} onChange={(e) => setSimilar(e.target.value)} /></Field>
    <div className="sm:col-span-2"><p className="mb-2 text-xs text-slate-500">评估引用信号（不自动绑定项目来源）</p>{signals.map((signal) => <label key={signal.id} className="mr-4 inline-flex items-center gap-2 text-sm"><input type="checkbox" checked={draft.evidence_signal_ids.includes(signal.id)} onChange={(e) => setDraft({ ...draft, evidence_signal_ids: e.target.checked ? [...draft.evidence_signal_ids, signal.id] : draft.evidence_signal_ids.filter((id) => id !== signal.id) })} />#{signal.id} {signal.label}</label>)}</div>
  </fieldset>{(error || save.isError) && <ErrorBanner message={error || (save.error instanceof ApiError && save.error.status === 409 ? "评估版本已变化。请先复制当前输入，再刷新并基于最新版本保存；本次输入仍保留。" : errorMessage(save.error))} />}<Button type="submit" disabled={save.isPending}>保存新评估版本</Button></form>;
}

function conversionIdempotencyKey(storageKey: string): string {
  const previous = sessionStorage.getItem(storageKey);
  if (previous) return previous;
  let value: string;
  if (typeof crypto.randomUUID === "function") {
    value = crypto.randomUUID();
  } else {
    // HTTP LAN origins lack randomUUID; getRandomValues remains available there.
    const bytes = crypto.getRandomValues(new Uint8Array(16));
    bytes[6] = (bytes[6] & 0x0f) | 0x40;
    bytes[8] = (bytes[8] & 0x3f) | 0x80;
    const hex = Array.from(bytes, (byte) => byte.toString(16).padStart(2, "0")).join("");
    value = `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
  }
  sessionStorage.setItem(storageKey, value);
  return value;
}

function ConversionForm({ item, signals, saved }: { item: Opportunity; signals: OpportunitySignal[]; saved: () => Promise<void> }) {
  const navigate = useNavigate();
  const [title, setTitle] = useState(item.title);
  const [objective, setObjective] = useState(item.summary);
  const [selected, setSelected] = useState<number[]>([]);
  const [key] = useState(() => {
    const storageKey = `opportunity-conversion:${currentUser()}:${item.id}:${item.latest_assessment!.revision_no}`;
    return conversionIdempotencyKey(storageKey);
  });
  const convert = useMutation({ mutationFn: () => api.post<Conversion>(`${base}/${item.id}/convert-to-project`, { expected_assessment_revision: item.latest_assessment!.revision_no, idempotency_key: key, title: title.trim() || undefined, objective: objective.trim() || undefined, selected_signal_ids: selected }), onSuccess: async (result) => { await saved(); navigate(`/projects/${result.project_id}`); } });
  const eligible = signals.filter((signal) => signal.signal_type === "source_document" && signal.source_entity_id !== null && signal.status !== "detached");
  return <form className="space-y-4" onSubmit={(e) => { e.preventDefault(); if (window.confirm(`使用当前评估 v${item.latest_assessment!.revision_no} 创建内容项目，并仅绑定选中的 ${selected.length} 条来源信号？`)) convert.mutate(); }}><p className="text-sm text-slate-600">使用评估 v{item.latest_assessment!.revision_no}。身份、形态、渠道与来源推荐均为 suggested；仅选中的来源会被绑定。事实边界需在项目证据页另行确认。</p><Field label="项目名称"><input maxLength={300} className={inputClass} value={title} onChange={(e) => setTitle(e.target.value)} /></Field><Field label="项目目标"><textarea className={inputClass} value={objective} onChange={(e) => setObjective(e.target.value)} /></Field><p className="text-sm">建议来源（suggested）· 默认不选</p>{eligible.length === 0 ? <p className="text-xs text-slate-500">没有可绑定的 SourceDocument 信号；可创建无来源绑定的项目。</p> : eligible.map((signal) => <label key={signal.id} className="flex items-center gap-2 text-sm"><input disabled={convert.isPending} type="checkbox" checked={selected.includes(signal.id)} onChange={(e) => setSelected(e.target.checked ? [...selected, signal.id] : selected.filter((id) => id !== signal.id))} />#{signal.id} {signal.label} · Source #{signal.source_entity_id}</label>)}{convert.isError && <ErrorBanner message={convert.error instanceof ApiError && convert.error.status === 409 ? "转换冲突：请刷新核对当前评估和已有项目关系。" : errorMessage(convert.error)} />}<Button type="submit" disabled={convert.isPending}>{convert.isPending ? "创建中…" : "确认创建内容项目"}</Button></form>;
}
