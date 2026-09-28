import { FormEvent, useEffect, useMemo, useState } from "react";
import { api, ApiError } from "../api";
import { Button, EmptyState, ErrorBanner, Field, Spinner, inputClass } from "../components/ui";
import { MemoryPanel } from "./LearningWorkspace";

type Kind = "brand" | "persona" | "account" | "series";
type Entity = { kind: Kind; id: number; name: string; status: string; brand_id?: number | null; persona_id?: number; account_id?: number; current_revision: number };
type Revision = { id: number; revision_no: number; profile: Record<string, unknown>; checksum: string; created_at: string | null };
type Effective = { effective_profile: Record<string, unknown>; field_origins: Record<string, string>; revision_ids: Record<string, number | null> };
type Binding = { revision: number; workflow_id: number | null; workflow_version: number | null; definition: Record<string, unknown>; source?: string };
type FieldKey = "positioning" | "target_audience" | "content_domains" | "expression_style" | "visual_language" | "long_term_views" | "value_propositions" | "content_boundaries" | "risk_boundaries" | "public_fact_policy" | "brand_voice_version_id";
type Mode = "inherit" | "override" | "clear";
type DraftField = { mode: Mode; text: string };

const ROOT: Record<Kind, string> = { brand: "content-brands", persona: "content-personas", account: "content-accounts", series: "content-series" };
const KIND_NAME: Record<Kind, string> = { brand: "品牌", persona: "角色", account: "账号", series: "栏目" };
const FIELDS: { key: FieldKey; label: string; shape: "text" | "lines" | "json" | "voice"; tab: string }[] = [
  { key: "positioning", label: "定位", shape: "text", tab: "identity" },
  { key: "target_audience", label: "目标受众", shape: "lines", tab: "identity" },
  { key: "content_domains", label: "内容领域", shape: "lines", tab: "identity" },
  { key: "brand_voice_version_id", label: "品牌语气版本", shape: "voice", tab: "expression" },
  { key: "expression_style", label: "表达风格 JSON", shape: "json", tab: "expression" },
  { key: "visual_language", label: "视觉语言 JSON", shape: "json", tab: "expression" },
  { key: "long_term_views", label: "长期观点 JSON", shape: "json", tab: "boundaries" },
  { key: "value_propositions", label: "价值主张", shape: "lines", tab: "boundaries" },
  { key: "content_boundaries", label: "内容边界", shape: "lines", tab: "boundaries" },
  { key: "risk_boundaries", label: "风险边界", shape: "lines", tab: "boundaries" },
  { key: "public_fact_policy", label: "公开事实规则 JSON", shape: "json", tab: "boundaries" },
];
const TABS = [
  ["identity", "身份"], ["expression", "表达与视觉"], ["boundaries", "观点与边界"],
  ["accounts", "账号与栏目"], ["workflow", "工作流偏好"], ["memory", "内容记忆"],
] as const;
const EMPTY_DEFINITION = { nodes: [], edges: [], visual_order: [] };

function errText(error: unknown) { return error instanceof ApiError ? `${error.status} · ${error.message}` : "后端读取失败，请重试。"; }
function fieldText(value: unknown, shape: string): string {
  if (value === undefined || value === null) return "";
  if (shape === "lines" && Array.isArray(value)) return value.map(String).join("\n");
  return shape === "json" ? JSON.stringify(value, null, 2) : String(value);
}
function draftFrom(profile: Record<string, unknown>): Record<FieldKey, DraftField> {
  return Object.fromEntries(FIELDS.map(({ key, shape }) => [key, { mode: !(key in profile) ? "inherit" : profile[key] === null ? "clear" : "override", text: fieldText(profile[key], shape) }])) as Record<FieldKey, DraftField>;
}

export default function IdentityWorkspace() {
  const [brands, setBrands] = useState<Entity[]>([]);
  const [personas, setPersonas] = useState<Entity[]>([]);
  const [accounts, setAccounts] = useState<Entity[]>([]);
  const [series, setSeries] = useState<Entity[]>([]);
  const [selected, setSelected] = useState<{ kind: Kind; id: number } | null>(null);
  const [revisions, setRevisions] = useState<Revision[]>([]);
  const [effective, setEffective] = useState<Effective | null>(null);
  const [voices, setVoices] = useState<{ id: number; name: string; version: number }[]>([]);
  const [draft, setDraft] = useState<Record<FieldKey, DraftField>>(draftFrom({}));
  const [tab, setTab] = useState<string>("identity");
  const [modality, setModality] = useState("text");
  const [binding, setBinding] = useState<Binding | null>(null);
  const [resolvedBinding, setResolvedBinding] = useState<Binding | null>(null);
  const [definitionText, setDefinitionText] = useState(JSON.stringify(EMPTY_DEFINITION, null, 2));
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [revisionConflict, setRevisionConflict] = useState(false);

  const entities = useMemo(() => [...brands, ...personas, ...accounts, ...series], [brands, personas, accounts, series]);
  const current = selected ? entities.find((item) => item.kind === selected.kind && item.id === selected.id) : null;
  const persona = current?.kind === "persona" ? current : current?.kind === "account" ? personas.find((row) => row.id === current.persona_id) : current?.kind === "series" ? personas.find((row) => row.id === accounts.find((account) => account.id === current.account_id)?.persona_id) : null;
  const account = current?.kind === "account" ? current : current?.kind === "series" ? accounts.find((row) => row.id === current.account_id) : null;
  const seriesId = current?.kind === "series" ? current.id : null;
  const effectiveQuery = persona ? `persona_id=${persona.id}${account ? `&account_id=${account.id}` : ""}${seriesId ? `&series_id=${seriesId}` : ""}` : null;
  const selectedUrl = current ? `/${ROOT[current.kind]}/${current.id}` : null;

  async function loadTree() {
    const [nextBrands, nextPersonas, nextVoices] = await Promise.all([
      api.get<Omit<Entity, "kind">[]>("/content-brands"), api.get<Omit<Entity, "kind">[]>("/content-personas"),
      api.get<{ id: number; name: string; version: number }[]>("/content-identities/brand-voices"),
    ]);
    const nextAccounts = (await Promise.all(nextPersonas.map((row) => api.get<Omit<Entity, "kind">[]>(`/content-personas/${row.id}/accounts`)))).flat();
    const nextSeries = (await Promise.all(nextAccounts.map((row) => api.get<Omit<Entity, "kind">[]>(`/content-accounts/${row.id}/series`)))).flat();
    setBrands(nextBrands.map((row) => ({ ...row, kind: "brand" })));
    setPersonas(nextPersonas.map((row) => ({ ...row, kind: "persona" })));
    setAccounts(nextAccounts.map((row) => ({ ...row, kind: "account" })));
    setSeries(nextSeries.map((row) => ({ ...row, kind: "series" })));
    setVoices(nextVoices);
    if (!selected && (nextBrands[0] || nextPersonas[0])) setSelected(nextBrands[0] ? { kind: "brand", id: nextBrands[0].id } : { kind: "persona", id: nextPersonas[0].id });
  }
  useEffect(() => { setLoading(true); loadTree().catch((error) => setError(errText(error))).finally(() => setLoading(false)); }, []);
  useEffect(() => {
    if (!selectedUrl) return;
    setDetailLoading(true); setError(""); setRevisionConflict(false);
    Promise.all([
      api.get<Revision[]>(`${selectedUrl}/revisions`),
      effectiveQuery ? api.get<Effective>(`/content-identities/effective?${effectiveQuery}`) : Promise.resolve(null),
    ]).then(([nextRevisions, nextEffective]) => {
      setRevisions(nextRevisions); setEffective(nextEffective); setDraft(draftFrom(nextRevisions[0]?.profile || {}));
    }).catch((error) => setError(errText(error))).finally(() => setDetailLoading(false));
  }, [selectedUrl, effectiveQuery]);
  useEffect(() => {
    if (!current || current.kind === "brand" || !effectiveQuery) { setBinding(null); setResolvedBinding(null); return; }
    Promise.all([
      api.get<Binding>(`${selectedUrl}/default-workflows/${modality}`),
      api.get<Binding>(`/content-identities/effective-workflow?${effectiveQuery}&modality=${modality}`),
    ]).then(([direct, resolved]) => { setBinding(direct); setResolvedBinding(resolved); setDefinitionText(JSON.stringify(direct.workflow_id ? direct.definition : EMPTY_DEFINITION, null, 2)); }).catch((error) => setError(errText(error)));
  }, [selectedUrl, effectiveQuery, modality]);

  async function createEntity(event: FormEvent) {
    event.preventDefault();
    const path = !current ? "/content-brands" : current.kind === "brand" ? `${selectedUrl}/personas` : current.kind === "persona" ? `${selectedUrl}/accounts` : current.kind === "account" ? `${selectedUrl}/series` : "";
    if (!path) return;
    try {
      const created = await api.post<{ id: number }>(path, { name: name.trim() });
      const kind: Kind = !current ? "brand" : current.kind === "brand" ? "persona" : current.kind === "persona" ? "account" : "series";
      await loadTree(); setSelected({ kind, id: created.id }); setName(""); setNotice(`${KIND_NAME[kind]}已创建。`);
    } catch (error) { setError(errText(error)); }
  }
  async function archive() {
    if (!current || !selectedUrl || !window.confirm(`归档「${current.name}」？历史版本与生产快照仍可查看。`)) return;
    try { await api.del(selectedUrl); await loadTree(); setNotice("已归档，历史记录仍可读取。"); }
    catch (error) { setError(errText(error)); }
  }
  async function saveRevision() {
    if (!current || !selectedUrl || revisionConflict) return;
    try {
      const profile: Record<string, unknown> = {};
      for (const { key, shape } of FIELDS) {
        const value = draft[key];
        if (value.mode === "inherit") continue;
        if (value.mode === "clear") { profile[key] = null; continue; }
        if (shape === "lines") profile[key] = value.text.split("\n").map((line) => line.trim()).filter(Boolean);
        else if (shape === "json") profile[key] = JSON.parse(value.text || (key === "long_term_views" ? "[]" : "{}"));
        else if (shape === "voice") profile[key] = Number(value.text);
        else profile[key] = value.text;
      }
      await api.post(`${selectedUrl}/revisions`, { expected_revision: current.current_revision, profile });
      await loadTree();
      const nextRevisions = await api.get<Revision[]>(`${selectedUrl}/revisions`);
      setRevisions(nextRevisions); setDraft(draftFrom(nextRevisions[0]?.profile || {}));
      if (effectiveQuery) setEffective(await api.get<Effective>(`/content-identities/effective?${effectiveQuery}`));
      setNotice(`修订 v${nextRevisions[0].revision_no} 已保存，旧快照不会改变。`);
    } catch (error) {
      setError(error instanceof SyntaxError ? "JSON 格式不正确，请检查后再保存。" : errText(error));
      if (error instanceof ApiError && error.status === 409) {
        setRevisionConflict(true);
        await loadTree();
        setRevisions(await api.get<Revision[]>(`${selectedUrl}/revisions`));
        setNotice("版本已被其他人更新。当前表单仍是旧草稿；请核对最新修订后显式加载，才可再次保存。");
      }
    }
  }
  async function saveDefault() {
    if (!selectedUrl || !binding || !current || current.kind === "brand") return;
    try {
      const definition = JSON.parse(definitionText);
      const next = await api.post<Binding>(`${selectedUrl}/default-workflows/${modality}`, { expected_revision: binding.revision, definition });
      setBinding(next); setResolvedBinding({ ...next, source: current.kind }); setNotice("默认工作流已保存为新版本；已有内容单元不会自动重绑。");
    } catch (error) { setError(error instanceof SyntaxError ? "工作流定义 JSON 格式不正确。" : errText(error)); }
  }
  function fieldEditor(key: FieldKey, label: string, shape: string) {
    const value = draft[key];
    const displayedProfile = current?.kind === "brand" ? revisions[0]?.profile || {} : effective?.effective_profile || {};
    const origin = current?.kind === "brand" ? key in displayedProfile ? "brand" : undefined : effective?.field_origins[key];
    return <div key={key} className="rounded-xl border border-slate-200 bg-white p-4"><div className="flex flex-wrap items-center justify-between gap-2"><label className="text-sm font-medium">{label}</label><span className="text-xs text-slate-500">{origin ? `当前生效：${KIND_NAME[origin as Kind] || origin}（${displayedProfile[key] === null ? "显式清空" : origin === current?.kind ? "本级覆盖" : "从上级继承"}）` : "当前未设置"}</span></div>
      <select disabled={current?.status === "archived"} aria-label={`${label}模式`} className={`${inputClass} mt-2`} value={value.mode} onChange={(event) => setDraft({ ...draft, [key]: { ...value, mode: event.target.value as Mode } })}><option value="inherit">继承上级 / 不设置</option><option value="override">本级覆盖</option><option value="clear">显式清空</option></select>
      {value.mode === "override" && (shape === "voice" ? <select disabled={current?.status === "archived"} className={`${inputClass} mt-2`} value={value.text} onChange={(event) => setDraft({ ...draft, [key]: { ...value, text: event.target.value } })}><option value="">请选择已发布版本</option>{voices.map((voice) => <option key={voice.id} value={voice.id}>{voice.name} · v{voice.version}</option>)}</select> : shape === "text" ? <input disabled={current?.status === "archived"} className={`${inputClass} mt-2`} value={value.text} onChange={(event) => setDraft({ ...draft, [key]: { ...value, text: event.target.value } })} /> : <textarea disabled={current?.status === "archived"} className={`${inputClass} mt-2 min-h-24 font-mono text-xs`} value={value.text} placeholder={shape === "json" ? "{}" : "每行一项"} onChange={(event) => setDraft({ ...draft, [key]: { ...value, text: event.target.value } })} />)}
      {key in displayedProfile && <p className="mt-2 break-words text-xs text-slate-500">生效值：{JSON.stringify(displayedProfile[key])}</p>}
    </div>;
  }
  function entityButton(entity: Entity, depth: number) {
    return <button key={`${entity.kind}-${entity.id}`} onClick={() => { setSelected({ kind: entity.kind, id: entity.id }); setNotice(""); }} className={`block w-full rounded-lg px-3 py-2 text-left text-sm ${current?.kind === entity.kind && current.id === entity.id ? "bg-indigo-50 font-semibold text-indigo-700" : "hover:bg-slate-50"}`} style={{ paddingLeft: 12 + depth * 16 }}><span className="mr-2 text-xs text-slate-400">{KIND_NAME[entity.kind]}</span>{entity.name}{entity.status === "archived" && <span className="ml-1 text-xs text-slate-400">已归档</span>}</button>;
  }
  const brandless = personas.filter((row) => row.brand_id == null);

  return <div className="mx-auto max-w-7xl px-6 py-9"><div className="mb-6"><p className="text-xs font-semibold uppercase tracking-widest text-indigo-600">Identity Workspace</p><h1 className="mt-2 text-3xl font-semibold">内容身份</h1><p className="mt-2 text-sm text-slate-500">品牌 → 角色 → 账号 → 栏目；修订长期保存，生产时固定快照。</p></div>
    {error && <div className="mb-4"><ErrorBanner message={error} /></div>}{notice && <p className="mb-4 rounded-lg bg-indigo-50 p-3 text-sm text-indigo-700">{notice}</p>}
    {loading ? <Spinner label="读取身份树…" /> : <div className="grid gap-5 lg:grid-cols-[280px_1fr]"><aside className="rounded-2xl border border-slate-200 bg-white p-3"><h2 className="px-3 py-2 text-sm font-semibold">身份层级</h2>{brands.length + personas.length === 0 && <EmptyState title="还没有内容身份" hint="先创建品牌，或使用既有无品牌角色。" />}{brands.map((brand) => <div key={brand.id}>{entityButton(brand, 0)}{personas.filter((row) => row.brand_id === brand.id).map((p) => <div key={p.id}>{entityButton(p, 1)}{accounts.filter((row) => row.persona_id === p.id).map((a) => <div key={a.id}>{entityButton(a, 2)}{series.filter((row) => row.account_id === a.id).map((s) => entityButton(s, 3))}</div>)}</div>)}</div>)}{brandless.length > 0 && <div className="mt-3 border-t pt-3"><p className="px-3 text-xs text-slate-500">历史无品牌角色</p>{brandless.map((p) => <div key={p.id}>{entityButton(p, 1)}{accounts.filter((row) => row.persona_id === p.id).map((a) => <div key={a.id}>{entityButton(a, 2)}{series.filter((row) => row.account_id === a.id).map((s) => entityButton(s, 3))}</div>)}</div>)}</div>}
      <form onSubmit={createEntity} className="mt-4 space-y-2 border-t px-2 pt-4"><label className="text-xs text-slate-600">{!current ? "新建品牌" : current.kind === "series" ? "请选择上级创建子项" : `在${KIND_NAME[current.kind]}下新增${KIND_NAME[current.kind === "brand" ? "persona" : current.kind === "persona" ? "account" : "series"]}`}</label><input className={inputClass} value={name} onChange={(event) => setName(event.target.value)} placeholder="名称" required /><Button type="submit" disabled={current?.kind === "series" || current?.status === "archived"}>新增</Button><button type="button" className="ml-2 text-xs text-indigo-700" onClick={() => setSelected(null)}>新建根品牌</button></form></aside>
      <main className="min-w-0">{!current ? <EmptyState title="选择左侧身份或创建品牌" /> : <><div className="rounded-2xl border border-slate-200 bg-white p-5"><div className="flex flex-wrap items-center justify-between gap-3"><div><p className="text-xs text-slate-500">{KIND_NAME[current.kind]} · #{current.id}</p><h2 className="mt-1 text-xl font-semibold">{current.name}</h2><p className="mt-1 text-xs text-slate-500">{current.status === "archived" ? "已归档，只能查看历史" : `当前修订 v${current.current_revision}`}</p></div>{current.status !== "archived" && <Button variant="danger" onClick={archive}>归档</Button>}</div></div>
      <div role="tablist" className="mt-5 flex gap-1 overflow-x-auto border-b">{TABS.map(([key, label]) => <button key={key} role="tab" aria-selected={tab === key} onClick={() => setTab(key)} className={`whitespace-nowrap border-b-2 px-3 py-3 text-sm ${tab === key ? "border-indigo-600 text-indigo-700" : "border-transparent text-slate-500"}`}>{label}</button>)}</div>
      {detailLoading ? <Spinner label="读取修订…" /> : <div className="mt-5 space-y-4">{["identity", "expression", "boundaries"].includes(tab) && <>{revisionConflict && <div className="rounded-xl border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900"><p>最新修订为 v{revisions[0]?.revision_no ?? "未知"}；当前表单来自旧版本，已停止保存。请先复制需要保留的改动，再加载最新修订。</p><Button variant="secondary" onClick={() => { setDraft(draftFrom(revisions[0]?.profile || {})); setRevisionConflict(false); setError(""); setNotice("已加载最新修订，请重新核对后保存。"); }}>加载最新修订（覆盖当前表单）</Button></div>}<div className="grid gap-3 xl:grid-cols-2">{FIELDS.filter((field) => field.tab === tab).map(({ key, label, shape }) => fieldEditor(key, label, shape))}</div><Button onClick={saveRevision} disabled={current.status === "archived" || revisionConflict}>保存新修订 v{current.current_revision + 1}</Button><section className="rounded-xl border bg-white p-4"><h3 className="font-medium">修订历史</h3>{revisions.length ? <ul className="mt-2 space-y-2 text-xs">{revisions.map((revision) => <li key={revision.id} className="rounded border p-2">v{revision.revision_no} · #{revision.id} · {revision.created_at || ""}<pre className="mt-1 overflow-x-auto whitespace-pre-wrap text-slate-500">{JSON.stringify(revision.profile, null, 2)}</pre></li>)}</ul> : <p className="mt-2 text-xs text-slate-500">尚未提交身份画像修订。</p>}</section></>}
      {tab === "accounts" && <section className="rounded-xl border bg-white p-5"><h3 className="font-medium">持久化层级</h3><p className="mt-2 text-sm text-slate-500">选择品牌、角色或账号，可创建直属子级；归档不会删除历史快照。</p>{persona && <p className="mt-3 text-sm">角色：{persona.name} · 账号 {accounts.filter((row) => row.persona_id === persona.id).length} 个</p>}{account && <p className="mt-1 text-sm">账号：{account.name} · 栏目 {series.filter((row) => row.account_id === account.id).length} 个</p>}{current.kind !== "series" && <form onSubmit={createEntity} className="mt-4 flex flex-wrap gap-2"><input aria-label="新子级名称" className={inputClass} required value={name} onChange={(event) => setName(event.target.value)} placeholder={`新建${KIND_NAME[current.kind === "brand" ? "persona" : current.kind === "persona" ? "account" : "series"]}名称`} /><Button type="submit" disabled={current.status === "archived"}>创建子级</Button></form>}{current.status !== "archived" && <div className="mt-4"><Button variant="danger" onClick={archive}>归档当前{KIND_NAME[current.kind]}</Button></div>}</section>}
      {tab === "workflow" && <section className="rounded-xl border bg-white p-5"><h3 className="font-medium">角色 / 账号 / 栏目 × 内容形态</h3>{current.kind === "brand" ? <p className="mt-2 text-sm text-slate-500">请选择角色、账号或栏目查看默认工作流。</p> : <><Field label="内容形态"><select className={inputClass} value={modality} onChange={(event) => setModality(event.target.value)}><option value="text">文字</option><option value="graphic">图文</option><option value="video">视频</option></select></Field><p className="mt-3 text-sm">本级：{binding?.workflow_id ? `v${binding.workflow_version} · Workflow #${binding.workflow_id}` : "未设置"}；当前生效：{resolvedBinding?.source || "未绑定"}{resolvedBinding?.workflow_id ? ` · Workflow #${resolvedBinding.workflow_id}` : ""}</p><p className="mt-2 text-xs text-slate-500">保存新版本不会自动修改已有内容单元。定义使用现有 Workflow schema；服务端检查可移植性和执行能力。</p><Field label="新默认工作流定义 JSON"><textarea className={`${inputClass} mt-2 min-h-44 font-mono text-xs`} value={definitionText} disabled={current.status === "archived"} onChange={(event) => setDefinitionText(event.target.value)} /></Field><Button onClick={saveDefault} disabled={current.status === "archived" || !binding}>另存为本级默认新版本</Button></>}</section>}
      {tab === "memory" && <MemoryPanel key={`${current.kind}:${current.id}`} scopeType={current.kind} scopeId={current.id} />}</div>}</>}</main></div>}
  </div>;
}
