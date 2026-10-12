import { lazy, Suspense, useRef, useState, type FormEvent, type ReactNode } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useSearchParams } from "react-router-dom";
import { api, ApiError, currentUser } from "../api";
import { Button, ErrorBanner, Field, Spinner, StatusBadge, inputClass } from "../components/ui";
import { categories, evidenceTypes, frozenEvidenceCount, insightReferences, memoryTypes, operationUUID, pageData, promotableClaim, queryString, scopeTypes } from "./learningTypes";
import type { Analysis as AnalysisData, Coverage, Insight, LearningCandidate, MemoryEntry, MemoryRevision, Observation, Page, PromotableClaim, PublishedContent, ScopeType } from "./learningTypes";

const CapabilityMemoryPanel = lazy(() => import("./CapabilityMemoryPanel"));

const box = "space-y-4 rounded-xl border border-slate-200 bg-white p-5";
const labels: Record<string, string> = { history: "历史回收", analysis: "长期分析", candidates: "学习候选", memory: "内容记忆" };
type Values = Record<string, unknown>;
type FormField = { name: string; label: string; type?: "text" | "number" | "datetime-local" | "url" | "textarea" | "json"; options?: string[]; value?: string; required?: boolean; hint?: string; maxLength?: number; readOnly?: boolean };
const json = (name: string, label: string, value = "{}"): FormField => ({ name, label, type: "json", value, hint: "高级 JSON；保留证据、范围和限制的原始结构。" });
const text = (name: string, label: string, required = false): FormField => ({ name, label, required });
const number = (name: string, label: string, required = false): FormField => ({ name, label, type: "number", required });
const select = (name: string, label: string, options: string[]): FormField => ({ name, label, options, value: options[0] });
const date = (name: string, label: string, required = false): FormField => ({ name, label, type: "datetime-local", required, hint: "按浏览器本地时区输入，提交为 ISO 时间。" });

function errorText(error: unknown) { return error instanceof Error ? error.message : "请求失败，请重试。"; }
function useRead<T>(path: string) {
  return useQuery({ queryKey: ["learning", currentUser(), path], queryFn: () => api.get<T>(path), retry: false });
}
function Read<T>({ path, children }: { path: string; children: (data: T) => ReactNode }) {
  const query = useRead<T>(path);
  if (query.isPending) return <Spinner label="读取真实记录…" />;
  if (query.isError) return <div role="alert" className="space-y-2"><ErrorBanner message={errorText(query.error)} /><Button variant="secondary" onClick={() => void query.refetch()}>重试读取</Button></div>;
  return <>{children(query.data)}</>;
}
export function DataView({ data, title = "来源与详细记录" }: { data: unknown; title?: string }) {
  return <details className="rounded-lg border border-slate-200 p-3 text-sm"><summary className="cursor-pointer text-slate-600">{title}</summary><pre className="mt-3 max-h-96 overflow-auto whitespace-pre-wrap break-words text-xs">{data == null ? "未返回 / 未知" : JSON.stringify(data, null, 2)}</pre></details>;
}

function ActionForm({ title, fields = [], submit = "保存", action, prepare, disabled = false, confirm, renderResult }: {
  title: string; fields?: FormField[]; submit?: string; disabled?: boolean; confirm?: string;
  action: (values: Values, key: string) => Promise<unknown>; prepare?: (values: Values) => Values;
  renderResult?: (result: unknown) => ReactNode;
}) {
  const client = useQueryClient();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<unknown>();
  const [saved, setSaved] = useState(false);
  const [conflict, setConflict] = useState(false);
  const operation = useRef<{ payload: string; key: string }>();
  async function send(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy || conflict || disabled || (confirm && !window.confirm(confirm))) return;
    setError(""); setSaved(false); setBusy(true);
    try {
      const form = new FormData(event.currentTarget);
      const raw: Values = {};
      for (const field of fields) {
        if (field.readOnly) continue;
        const value = String(form.get(field.name) ?? "").trim();
        if (!value) continue;
        if (field.type === "json") raw[field.name] = JSON.parse(value);
        else if (field.type === "number") {
          const parsed = Number(value); if (!Number.isFinite(parsed)) throw new Error(`${field.label}必须是有效数字。`);
          raw[field.name] = parsed;
        } else if (field.type === "datetime-local") raw[field.name] = new Date(value).toISOString();
        else raw[field.name] = value;
      }
      const values = prepare ? prepare(raw) : raw;
      const payload = JSON.stringify(values);
      // Keep one key for the same payload after network failures; changed input is a new operation.
      if (operation.current?.payload !== payload) operation.current = { payload, key: operationUUID() };
      const response = await action(values, operation.current.key);
      setResult(response); setSaved(true); operation.current = undefined;
      await Promise.all([client.invalidateQueries({ queryKey: ["learning"] }), client.invalidateQueries({ queryKey: ["home"] })]);
    } catch (cause) { setError(errorText(cause)); setConflict(cause instanceof ApiError && cause.status === 409); }
    finally { setBusy(false); }
  }
  return <form className={box} onSubmit={send}><h3 className="font-semibold">{title}</h3><div className="grid gap-3 sm:grid-cols-2">{fields.map((field) => <Field key={field.name} label={field.label} hint={field.hint}>{field.options ? <select name={field.name} className={inputClass} defaultValue={field.value} disabled={busy || disabled}>{field.options.map((option) => <option key={option}>{option}</option>)}</select> : ["textarea", "json"].includes(field.type ?? "") ? <textarea name={field.name} className={`${inputClass} min-h-24 ${field.type === "json" ? "font-mono text-xs" : ""}`} defaultValue={field.value} required={field.required} readOnly={field.readOnly} disabled={busy || disabled} /> : <input name={field.name} type={field.type ?? "text"} step={field.type === "number" ? "any" : undefined} className={inputClass} defaultValue={field.value} required={field.required} maxLength={field.maxLength} readOnly={field.readOnly} disabled={busy || disabled} />}</Field>)}</div>
    {error && <div role="alert"><ErrorBanner message={error} /></div>}{conflict && <p className="text-sm text-amber-800">版本或请求发生冲突。请刷新记录并核对最新状态，再重新操作；不会自动重试写入。</p>}
    <Button type="submit" disabled={busy || disabled || conflict}>{busy ? "提交中…" : submit}</Button>{conflict && <Button variant="secondary" onClick={() => { setConflict(false); void client.invalidateQueries({ queryKey: ["learning"] }); }}>刷新并重新核对</Button>}
    {saved && <div role="status" className="text-sm text-emerald-700">后端已确认操作。{renderResult?.(result)}<DataView data={result} title="查看后端结果" /></div>}
  </form>;
}

function Paged<T>({ path, render }: { path: string; render: (row: T) => ReactNode }) {
  const [offset, setOffset] = useState(0);
  const separator = path.includes("?") ? "&" : "?";
  const url = `${path}${separator}limit=20&offset=${offset}`;
  const query = useQuery({ queryKey: ["learning", currentUser(), url], queryFn: async () => pageData(await api.get<Page<T>>(url)), retry: false });
  if (query.isPending) return <Spinner label="读取本页记录…" />;
  if (query.isError) return <div className="space-y-2" role="alert"><ErrorBanner message={errorText(query.error)} /><Button onClick={() => void query.refetch()}>重试</Button></div>;
  const page = query.data;
  return <div className="space-y-3"><p className="text-xs text-slate-500">共 {page.total} 条 · 每页最多 {page.limit} 条</p>{page.items.length ? page.items.map(render) : <p className="text-sm text-slate-500">本页暂无记录。</p>}<div className="flex gap-3"><Button variant="secondary" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - 20))}>上一页</Button><Button variant="secondary" disabled={page.offset + page.items.length >= page.total} onClick={() => setOffset(offset + 20)}>下一页</Button><Button variant="secondary" onClick={() => void query.refetch()}>刷新</Button></div></div>;
}

function Filters({ fields, onChange }: { fields: FormField[]; onChange: (values: Record<string, string>) => void }) {
  return <form className={box} onSubmit={(event) => {
    event.preventDefault(); const values = Object.fromEntries(new FormData(event.currentTarget).entries()) as Record<string, string>;
    for (const field of fields) if (field.type === "datetime-local" && values[field.name]) values[field.name] = new Date(values[field.name]).toISOString();
    onChange(values);
  }}><h3 className="font-semibold">筛选范围</h3><div className="grid gap-3 sm:grid-cols-3">{fields.map((field) => <Field key={field.name} label={field.label}>{field.options ? <select className={inputClass} name={field.name}><option value="">{field.name === "status" ? "默认（当前有效记录）" : "全部"}</option>{field.options.map((value) => <option key={value}>{value}</option>)}</select> : <input className={inputClass} name={field.name} type={field.type ?? "text"} />}</Field>)}</div><Button type="submit">应用筛选</Button></form>;
}
const cohortFields = [text("channel", "渠道代码"), number("content_account_id", "内容账号 ID"), text("content_form", "内容形态"), date("date_from", "发布日期起"), date("date_to", "发布日期止（不含）")];

function CoverageView({ data }: { data: Coverage }) {
  const display = (value: number | undefined) => value === undefined ? "未知" : value;
  return <div className="space-y-3 text-sm"><p>内容数：{display(data.record_count)} · 样本数：{display(data.sample_count)}{data.observation_count !== undefined && ` · 观察数：${data.observation_count}`}{data.missing_date_count !== undefined && ` · 日期缺失：${data.missing_date_count}`}</p>
    {data.incomplete && <p role="alert" className="rounded-lg bg-amber-50 p-3 text-amber-900">结果已到查询上限，样本不完整；请缩小时间或账号范围。</p>}
    {data.coverage ? <div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead><tr><th className="p-2">字段覆盖</th><th>已知</th><th>缺失</th><th>未知</th></tr></thead><tbody>{Object.entries(data.coverage).map(([key, counts]) => <tr key={key} className="border-t"><td className="p-2">{key}</td><td>{display(counts.known)}</td><td>{display(counts.missing)}</td><td>{display(counts.unknown)}</td></tr>)}</tbody></table></div> : <ErrorBanner message="覆盖信息未返回，不能确认样本完整性。" />}
    {data.limitations?.map((item, index) => <p className="text-amber-800" key={`${item}:${index}`}>{item}</p>)}<DataView data={data} title="查看完整覆盖与年份分布" />
  </div>;
}

function SyncStudio({ onRecover }: { onRecover: (id: number) => void }) {
  const [offset, setOffset] = useState(0);
  return <ActionForm key={offset} title={`同步 Studio 已确认发布（起点 ${offset}，最多 50 条）`} submit="同步这一批确认记录" action={() => api.post(`/published-content/sync-studio?limit=50&offset=${offset}`, {})} renderResult={(result) => {
    const data = result as { processed?: number; next_offset?: number; missing_confirmation_target_ids?: number[] };
    return <div className="mt-3 space-y-2 text-slate-700"><p>本批处理：{data.processed ?? "未知"} 条；同步只回收已确认记录。</p>{data.missing_confirmation_target_ids?.length ? <div className="space-y-2"><p className="text-amber-800">以下目标缺少发布回执（本次最多显示 50 个），需要独立核实实际发布：</p><div className="flex flex-wrap gap-2">{data.missing_confirmation_target_ids.map((id) => <Button key={id} variant="secondary" onClick={() => onRecover(id)}>目标 #{id} · 补充发布声明</Button>)}</div></div> : null}{data.processed === 50 && typeof data.next_offset === "number" && <Button variant="secondary" onClick={() => setOffset(data.next_offset!)}>继续下一批</Button>}{data.processed !== undefined && data.processed < 50 && <p>该范围的回执扫描已完成；缺少回执的目标仍须单独处理。</p>}</div>;
  }} />;
}

function History({ selected, choose }: { selected: string | null; choose: (id: number) => void }) {
  const [filters, setFilters] = useState<Record<string, string>>({});
  const [recoveryTarget, setRecoveryTarget] = useState<number>();
  const suffix = queryString(filters);
  return <div className="space-y-5"><p className="text-sm text-slate-600">发布确认时间不等于实际发布时间。没有日期、指标或反馈的记录显示为缺失，不当作零。</p>
    <Filters fields={cohortFields} onChange={setFilters} />
    <section className={box}><h2 className="font-semibold">历史覆盖与缺失</h2><Read<Coverage> path={`/learning/coverage?${suffix}`} children={(data) => <CoverageView data={data} />} /></section>
    <SyncStudio onRecover={(id) => { setRecoveryTarget(id); document.getElementById("publication-recovery")?.scrollIntoView({ behavior: "smooth" }); }} />
    <div id="publication-recovery"><ActionForm key={`recovery:${recoveryTarget ?? "manual"}`} title="补充已核对目标的真实发布声明" submit="确认实际发布并恢复历史" confirm="确认该目标实际已在平台发布？核对完成或草稿成功本身不代表已发布。" fields={[{ ...number("target_id", "交付目标 ID", true), value: recoveryTarget?.toString() }, { ...text("publication_attestation", "实际发布声明", true), type: "textarea" }, date("published_at", "经核实的发布时间（可留空）"), text("evidence_ref", "发布证据引用")]} action={(values, key) => api.post("/published-content/confirm-reconciled", { ...values, idempotency_key: key })} /></div>
    <ActionForm title="导入外部已发布内容" submit="导入外部记录" fields={[text("external_key", "外部唯一编号", true), text("channel", "渠道代码", true), text("title", "标题"), text("content_form", "内容形态"), { ...text("canonical_url", "原文地址"), type: "url" }, date("published_at", "实际发布时间（未知则留空）"), number("content_account_id", "内容账号 ID"), { ...text("body", "正文"), type: "textarea" }, { ...text("subtitles", "字幕"), type: "textarea" }, json("media", "媒体引用列表", "[]")]} prepare={(values) => { const { body, subtitles, media, ...record } = values; return { records: [{ ...record, content_snapshot: { body, subtitles, media } }] }; }} action={(values) => api.post("/published-content/import", values)} />
    <details className={box}><summary>批量导入（高级）</summary><ActionForm title="规范化记录批量导入" fields={[json("records", "记录列表", "[]")]} action={(values) => api.post("/published-content/import", values)} /></details>
    <section className={box}><h2 className="font-semibold">已发布内容</h2><Paged<PublishedContent> key={suffix} path={`/published-content?${suffix}`} render={(row) => <button key={row.id} className="block w-full rounded-lg border p-3 text-left text-sm" onClick={() => choose(row.id)}><span className="font-medium">{row.title ?? "标题缺失"} · #{row.id}</span><p className="mt-1 text-slate-500">{row.channel} · {row.origin} · {row.published_at ?? "发布时间缺失"}</p></button>} /></section>
    {selected && <PublishedDetail key={selected} id={selected} />}
  </div>;
}

function PublishedDetail({ id }: { id: string }) {
  const base = `/published-content/${id}`;
  return <section className={box}><h2 className="font-semibold">发布记录 #{id}</h2><Read<PublishedContent> path={base} children={(row) => <DataView data={row} title="不可变内容、来源与覆盖" />} />
    <h3 className="font-semibold">表现与反馈观察</h3><Paged<Observation> key={base} path={`${base}/observations`} render={(row) => <article className="rounded-lg border p-3 text-sm" key={row.id}><p>#{row.id} · {row.observation_kind} · {row.metric_namespace ?? "无指标命名空间"}.{row.metric_key ?? "无指标"}</p><p>{row.numeric_value == null ? "数值未采集" : row.numeric_value} {row.unit ?? "单位未知"} · {row.text_value ?? "无文字反馈"}</p><p className="text-xs text-slate-500">{row.observed_at} {row.supersedes_id != null && `· 更正 #${row.supersedes_id}`}</p><DataView data={row} title="窗口、来源与测量方式" /></article>} />
    <ActionForm title="追加观察 / 更正（历史不覆盖）" fields={[select("observation_kind", "观察类型", ["metric", "feedback", "editorial", "correction"]), text("metric_namespace", "指标命名空间"), text("metric_key", "指标名称"), number("numeric_value", "数值（未采集则留空）"), text("unit", "单位"), date("observed_at", "采集时间", true), select("measurement_mode", "测量方式", ["snapshot", "interval"]), { name: "granularity", label: "测量粒度", value: "lifetime", maxLength: 50, hint: "默认 lifetime；最多 50 字符，留空沿用后端默认。" }, { ...date("cutoff", "指标截至时间（as of）"), hint: "按浏览器本地时区输入，提交为 ISO；留空使用采集时间，不得晚于采集时间。这是本条观察的测量口径。" }, date("period_start", "区间起点"), date("period_end", "区间终点"), { ...text("text_value", "反馈 / 编辑说明"), type: "textarea" }, number("supersedes_id", "被更正观察 ID")]} action={(values) => api.post(`${base}/observations`, values)} />
  </section>;
}

function Analysis() {
  const [filters, setFilters] = useState<Record<string, string>>({});
  const [insightId, setInsightId] = useState<number>();
  const suffix = queryString(filters);
  return <div className="space-y-5"><p className="text-sm text-slate-600">只在相同指标、单位和测量窗口内比较。累计快照不相加；未知值不补零。自动分析能力尚未验证，请使用人工 Insight。</p>
    <Filters fields={[...cohortFields, select("identity_scope_type", "身份范围", scopeTypes.filter((type) => type !== "owner")), number("identity_scope_id", "身份 ID"), text("metric_namespace", "指标命名空间"), text("metric_key", "指标名称"), text("unit", "单位"), date("cutoff", "采集截止时间")]} onChange={setFilters} />
    <section className={box}><h2 className="font-semibold">同口径分析</h2><Read<AnalysisData> path={`/learning/analysis?${suffix}`} children={(data) => <><CoverageView data={data} />{!Array.isArray(data.groups) ? <ErrorBanner message="指标分组未返回，不能确认分析结果。" /> : data.groups.length === 0 ? <p className="text-sm text-slate-500">当前范围没有可比较的同口径指标。</p> : data.groups.map((group, index) => <article key={index} className="space-y-2 rounded-lg border p-3 text-sm"><h3 className="font-semibold">{group.metric_namespace}.{group.metric_key} · {group.unit ?? "单位未知"} · {group.measurement_mode}</h3><p>窗口：{group.period_start ?? "未指定"} → {group.period_end ?? "未指定"}</p><p>独立发布样本 {group.sample_count ?? "未知"} · 最小 {group.min ?? "未知"} · 最大 {group.max ?? "未知"} · 平均 {group.average ?? "未知"} · 中位 {group.median ?? "未知"}</p>{group.trend && <div className="max-h-64 overflow-auto"><table className="w-full text-left"><thead><tr><th>采集时间</th><th>发布记录</th><th>数值</th></tr></thead><tbody>{group.trend.map((point, i) => <tr className="border-t" key={`${point.published_content_id}:${point.observed_at}:${i}`}><td className="py-2">{point.observed_at}</td><td>#{point.published_content_id}</td><td>{point.value ?? "未采集"}</td></tr>)}</tbody></table></div>}</article>)}</>} /></section>
    <ActionForm key={`insight:${suffix}`} title="保存人工 Insight" fields={[{ ...text("statement", "结论", true), type: "textarea" }, select("insight_type", "结论类型", [...categories, "general"]), json("scope", "适用范围"), json("cohort", "样本定义", JSON.stringify(filters)), json("supporting_refs", "支持证据引用（type + id）", "[]"), json("contradicting_refs", "反例引用（type + id）", "[]"), json("limitations", "局限说明", "[]"), number("confidence", "置信度（未知则留空）"), number("supersedes_id", "被更正 Insight ID（保留旧记录）")]} prepare={(values) => {
      const supporting_refs = insightReferences(values.supporting_refs ?? []);
      const contradicting_refs = insightReferences(values.contradicting_refs ?? []);
      if (!supporting_refs.length && !contradicting_refs.length) throw new Error("请至少引用一条真实证据，再保存结论。");
      return { ...values, supporting_refs, contradicting_refs };
    }} action={(values) => api.post("/learning/insights", values)} />
    <section className={box}><h2 className="font-semibold">已保存 Insights</h2><Paged<Insight> path="/learning/insights" render={(row) => <button key={row.id} className="block w-full rounded-lg border p-3 text-left text-sm" onClick={() => setInsightId(row.id)}>#{row.id} · {row.insight_type} · {row.statement}</button>} />{insightId && <Read<Insight> path={`/learning/insights/${insightId}`} children={(row) => <DataView data={row} title="样本、支持 / 反对证据、限制及分析来源" />} />}</section>
  </div>;
}

function Candidates({ selected, choose }: { selected: string | null; choose: (id: number) => void }) {
  const [filters, setFilters] = useState<Record<string, string>>({});
  const suffix = queryString(filters);
  return <div className="space-y-5"><p className="text-sm text-slate-600">候选 → 补充支持与反例 → 提交审核 → 人工验证 → 单独提升为记忆。单篇或多次采集不自动构成多样本验证。</p>
    <Filters fields={[select("status", "状态", ["collecting", "ready_for_review", "accepted", "rejected", "archived"]), select("category", "类别", categories)]} onChange={setFilters} />
    <ActionForm title="新建学习候选" fields={[text("title", "标题", true), select("category", "类别", categories), { ...text("proposition", "待验证命题", true), type: "textarea" }, { ...text("rationale", "提出理由", true), type: "textarea" }, json("scope", "适用范围"), number("created_from_insight_id", "来源 Insight ID")]} action={(values) => api.post("/learning-candidates", values)} />
    <section className={box}><h2 className="font-semibold">候选列表</h2><Paged<LearningCandidate> key={suffix} path={`/learning-candidates?${suffix}`} render={(row) => <button key={row.id} className="block w-full rounded-lg border p-3 text-left text-sm" onClick={() => choose(row.id)}><span>#{row.id} · {row.title} · </span><StatusBadge status={row.status} /><p className="mt-2 text-slate-600">{row.proposition}</p></button>} /></section>
    {selected && <Read<LearningCandidate> path={`/learning-candidates/${selected}`} children={(row) => <CandidateDetail key={row.id} candidate={row} />} />}
  </div>;
}

function CandidateDetail({ candidate: row }: { candidate: LearningCandidate }) {
  const [bridgeOpened, setBridgeOpened] = useState(false);
  const [showBridge, setShowBridge] = useState(false);
  const base = `/learning-candidates/${row.id}`;
  const revision = row.revision_no;
  const claim = promotableClaim(row);
  return <section className={box}><h2 className="font-semibold">#{row.id} · {row.title} · 修订 {revision ?? "未知"}</h2><StatusBadge status={row.status} /><p className="text-sm">{row.proposition}</p><p className="text-sm text-slate-500">{row.rationale}</p><DataView data={row} title="完整证据、反例、冻结决定与来源" />
    {row.evidence?.map((item) => <p key={item.id} className="rounded-lg border p-3 text-sm">{item.role} · {item.evidence_type} #{item.entity_id} · {item.note ?? "无附注"}</p>)}
    {row.status === "collecting" && <><ActionForm title="编辑尚在收集证据的候选" disabled={!Number.isInteger(revision)} fields={[{ ...text("title", "标题", true), value: row.title }, { ...text("proposition", "待验证命题", true), type: "textarea", value: row.proposition }, { ...text("rationale", "提出理由"), type: "textarea", value: row.rationale }, json("scope", "范围", JSON.stringify(row.scope ?? {}))]} action={(values) => api.patch(base, { ...values, expected_revision: revision })} /><ActionForm title="补充支持 / 反对 / 背景证据" disabled={!Number.isInteger(revision)} fields={[select("evidence_type", "证据类型", evidenceTypes), number("entity_id", "证据 ID", true), select("role", "证据作用", ["support", "contradict", "context"]), text("note", "附注")]} action={(values) => api.post(`${base}/evidence`, { ...values, expected_revision: revision })} /><ActionForm title="提交人工审核" submit="提交审核" disabled={!Number.isInteger(revision)} action={() => api.post(`${base}/submit-review`, { expected_revision: revision })} /></>}
    {row.status === "ready_for_review" && <ActionForm title="人工验证（不宣称自动实验或多样本）" submit="记录验证决定" disabled={!Number.isInteger(revision)} fields={[select("decision", "决定", ["accepted", "rejected", "collecting"]), { ...text("rationale", "验证依据、样本独立性与限制", true), type: "textarea" }]} action={(values) => api.post(`${base}/validate`, { expected_revision: revision, decision: values.decision, validation_method: "human", validation_summary: { rationale: values.rationale } })} />}
    {row.status === "accepted" && (claim ? <><p className="text-sm text-slate-600">记忆声明、适用条件和局限来自冻结验证记录，只能查看。不同声明须先建立并接受匹配的新候选。</p><ActionForm title="显式提升为内容记忆" submit="提升为记忆" confirm="确认把这条已接受候选的冻结声明提升为指定范围的内容记忆？" fields={[select("scope_type", "目标范围", scopeTypes), number("scope_id", "目标身份 ID（owner 留空）"), select("memory_type", "记忆类型", memoryTypes), ...claimFields(claim)]} prepare={(values) => { if (values.scope_type !== "owner" && !values.scope_id) throw new Error("请选择目标身份 ID。"); return { ...values, ...claim }; }} action={(values, key) => api.post(`${base}/promote-to-memory`, { ...values, idempotency_key: key })} /></> : <ErrorBanner message="后端未返回完整的冻结可提升声明，暂不能提升。请刷新记录或先完成匹配候选的验证。" />)}
    {row.status === "accepted" && <section className="space-y-3 rounded-lg border border-slate-200 p-4"><h3 className="font-semibold">独立保留为创作方法</h3><p className="text-sm text-slate-600">学习接受只保留原决定。另行填写可复用方法，后端核对并冻结支持证据，才会创建方法候选；原有内容记忆流程保持独立。</p><Button variant="secondary" disabled={!Number.isSafeInteger(revision) || revision < 1} onClick={() => { setBridgeOpened(true); setShowBridge(previous => !previous); }}>{showBridge ? "收起方法候选表单" : "明确创建方法候选"}</Button>{bridgeOpened && <div hidden={!showBridge}><Suspense fallback={<Spinner label="按需加载学习方法桥接…" />}><CapabilityMemoryPanel learningCandidate={{ id: row.id, revision_no: revision }} /></Suspense></div>}</section>}
    {["accepted", "rejected"].includes(row.status) && <ActionForm title="归档候选（保留决定与证据）" submit="归档" disabled={!Number.isInteger(revision)} confirm="归档此候选？" action={() => api.del(`${base}?expected_revision=${revision}`)} />}
  </section>;
}

function claimFields(claim: PromotableClaim): FormField[] {
  return [
    { ...text("statement", "已验证记忆声明"), type: "textarea", value: claim.statement, readOnly: true },
    { ...json("applicability", "冻结适用条件", JSON.stringify(claim.applicability, null, 2)), readOnly: true },
    { ...json("limitations", "冻结局限", JSON.stringify(claim.limitations, null, 2)), readOnly: true },
  ];
}

function MemoryRevisionForm({ base, revision }: { base: string; revision: number | undefined }) {
  const [sourceId, setSourceId] = useState<number>();
  return <section className={box}><h3 className="font-semibold">追加记忆修订</h3><p className="text-sm text-slate-600">选择已接受的匹配候选，读取其冻结声明与条件。新声明须有匹配的新接受候选；后端仍会核对此前适用限制。</p>
    <form className="flex flex-wrap items-end gap-3" onSubmit={(event) => { event.preventDefault(); const id = Number(new FormData(event.currentTarget).get("candidate")); if (Number.isInteger(id) && id > 0) setSourceId(id); }}><Field label="已接受来源候选 ID"><input className={inputClass} type="number" min="1" step="1" name="candidate" required /></Field><Button type="submit" variant="secondary">读取冻结验证记录</Button></form>
    {sourceId && <Read<LearningCandidate> path={`/learning-candidates/${sourceId}`} children={(source) => { const claim = promotableClaim(source); return claim ? <ActionForm key={`${source.id}:${source.revision_no}:${revision}`} title={`使用候选 #${source.id} 的已验证声明`} submit="追加冻结声明修订" disabled={!Number.isInteger(revision)} fields={claimFields(claim)} prepare={(values) => ({ ...values, ...claim, expected_revision: revision, source_learning_candidate_id: source.id })} action={(values) => api.post(`${base}/revisions`, values)} /> : <ErrorBanner message="此候选未接受或缺少完整冻结声明，不能作为记忆修订来源。" />; }} />}
  </section>;
}

export function MemoryPanel({ scopeType, scopeId }: { scopeType?: ScopeType; scopeId?: number }) {
  const [filters, setFilters] = useState<Record<string, string>>({ scope_type: scopeType ?? "", scope_id: scopeId?.toString() ?? "", status: "active" });
  const [selected, setSelected] = useState<number>();
  const suffix = queryString({ ...filters, ...(scopeType ? { scope_type: scopeType, scope_id: scopeId } : {}), include_ancestors: true });
  return <div className="space-y-5"><p className="text-sm text-slate-600">记忆按来源范围并列展示，可查看祖先范围；不会覆盖身份字段或自动注入生产提示词。</p>
    <Filters fields={[...(scopeType ? [] : [select("scope_type", "范围", scopeTypes), number("scope_id", "身份 ID")]), select("status", "状态", ["active", "archived"])]} onChange={(values) => { setSelected(undefined); setFilters(values); }} />
    <section className={box}><h2 className="font-semibold">适用的内容记忆</h2><Paged<MemoryEntry> key={suffix} path={`/content-memory?${suffix}`} render={(row) => { const latest = typeof row.current_revision === "object" ? row.current_revision : row.latest_revision; const origin = typeof row.scope_origin === "object" ? row.scope_origin : undefined; return <article key={row.id} className="space-y-2 rounded-lg border p-3 text-sm"><button className="text-left font-medium text-indigo-700" onClick={() => setSelected(row.id)}>#{row.id} · {row.memory_type} · {row.scope_type} {row.scope_id != null && `#${row.scope_id}`} · {row.status} →</button><p>{latest?.statement ?? "点击读取当前修订"}</p><p className="text-xs text-slate-500">来源范围：{origin?.label ?? row.scope_type} · {origin?.relationship === "ancestor" ? "上级范围" : origin?.relationship === "exact" ? "当前范围" : "来源关系未知"} · 修订 {typeof row.current_revision === "number" ? row.current_revision : row.current_revision?.revision_no ?? "未知"}</p>{latest && <MemoryProvenance revision={latest} />}</article>; }} /></section>
    {selected && <Read<MemoryEntry> path={`/content-memory/${selected}`} children={(row) => <MemoryDetail key={row.id} entry={row} />} />}
  </div>;
}

function MemoryProvenance({ revision }: { revision: MemoryRevision }) {
  const snapshot = revision.evidence_snapshot ?? revision.evidence_snapshot_json;
  const evidenceCount = frozenEvidenceCount(snapshot);
  const applicability = revision.applicability ?? revision.applicability_json;
  const limitations = revision.limitations ?? revision.limitations_json;
  return <div className="space-y-1 text-xs text-slate-600"><p>来源候选：{revision.source_learning_candidate_id == null ? "未知" : <Link className="text-indigo-700" to={`/learning?tab=candidates&candidate=${revision.source_learning_candidate_id}`}>#{revision.source_learning_candidate_id} →</Link>} · 冻结证据数：{evidenceCount ?? "未知"}</p><p>适用条件：{applicability == null ? "未返回" : JSON.stringify(applicability)}</p><p>局限：{limitations == null ? "未返回" : JSON.stringify(limitations)}</p></div>;
}

function MemoryDetail({ entry: row }: { entry: MemoryEntry }) {
  const base = `/content-memory/${row.id}`;
  const revision = typeof row.current_revision === "number" ? row.current_revision : row.current_revision?.revision_no;
  const latest = typeof row.current_revision === "object" ? row.current_revision : row.latest_revision;
  return <section className={box}><h2 className="font-semibold">记忆 #{row.id} · {row.status}</h2><p className="text-sm">{latest?.statement ?? "当前内容请见详细记录"}</p>{latest && <MemoryProvenance revision={latest} />}<DataView data={row} title="来源范围、证据、适用条件与限制" />
    <h3 className="font-semibold">追加式修订历史</h3><Paged<MemoryRevision> key={base} path={`${base}/revisions`} render={(item) => <article key={item.id} className="rounded-lg border p-3 text-sm"><p>v{item.revision_no} · {item.statement}</p><MemoryProvenance revision={item} /><DataView data={item} title="冻结证据与限制" /></article>} />
    {row.status === "active" && <><MemoryRevisionForm base={base} revision={revision} /><ActionForm title="归档记忆" submit="归档" confirm="归档记忆并保留历史？" action={() => api.del(base)} /></>}
  </section>;
}

export default function LearningWorkspace() {
  const [params, setParams] = useSearchParams();
  const requested = params.get("tab") ?? "history";
  const tab = requested in labels ? requested : "history";
  const choose = (key: string, id: number) => setParams((old) => { const next = new URLSearchParams(old); next.set(key, String(id)); return next; });
  const candidate = params.get("candidate");
  const published = params.get("published");
  return <div className="mx-auto max-w-7xl space-y-6 px-6 py-9"><header><p className="text-xs font-semibold tracking-widest text-indigo-600">Learning Workspace</p><h1 className="mt-2 text-3xl font-semibold">效果与学习</h1><p className="mt-2 text-sm text-slate-500">收回历史 → 保留观察 → 验证候选 → 显式积累内容记忆。</p></header><nav role="tablist" aria-label="学习分区" className="flex gap-2 overflow-x-auto border-b">{Object.entries(labels).map(([key, label]) => <Link role="tab" aria-selected={tab === key} className={`whitespace-nowrap border-b-2 px-4 py-3 text-sm ${tab === key ? "border-indigo-600 text-indigo-700" : "border-transparent text-slate-500"}`} key={key} to={`/learning?tab=${key}`}>{label}</Link>)}</nav>
    <div role="tabpanel">{tab === "history" && <History selected={published && /^\d+$/.test(published) ? published : null} choose={(id) => choose("published", id)} />}{tab === "analysis" && <Analysis />}{tab === "candidates" && <Candidates selected={candidate && /^\d+$/.test(candidate) ? candidate : null} choose={(id) => choose("candidate", id)} />}{tab === "memory" && <MemoryPanel />}</div>
  </div>;
}
