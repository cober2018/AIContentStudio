import { FormEvent, lazy, Suspense, useEffect, useMemo, useRef, useState } from "react";
import { api, ApiError } from "../api";
import { Button, EmptyState, ErrorBanner, Field, Spinner, inputClass } from "../components/ui";
import { MemoryPanel } from "./LearningWorkspace";
import AccountPublisherPanel from "./AccountPublisherPanel";
import StarterPersonaGallery from "./StarterGallery";

const PersonaCreativeConfig = lazy(() => import("./PersonaCreativeConfig"));

type Kind = "brand" | "persona" | "account" | "series";
type Entity = { kind: Kind; id: number; name: string; status: string; brand_id?: number | null; persona_id?: number; account_id?: number; scope?: string; platform_channel?: string | null; current_revision: number };
type Channel = { channel: string; label: string; content_forms: { content_form: string; label: string }[] };
type SeriesTarget = { id: number; series_id: number; account_id: number; account_name: string | null; platform_channel: string | null; content_form: string; enabled: boolean; version: number };
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
  ["creative", "创作配置"], ["accounts", "账号与栏目"], ["workflow", "工作流偏好"], ["memory", "内容记忆"],
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
  const [channels, setChannels] = useState<Channel[]>([]);
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
  const [role, setRole] = useState<string | null>(null);
  const [loadedIdentityKey, setLoadedIdentityKey] = useState<string | null>(null);
  const [loadedBindingKey, setLoadedBindingKey] = useState<string | null>(null);
  const creativeDirty = useRef(false);
  const [creativeVisitedKey, setCreativeVisitedKey] = useState<string | null>(null);
  const identityKey = selected ? `${selected.kind}:${selected.id}` : null;
  const selectedIdentity = useRef(identityKey);
  selectedIdentity.current = identityKey;
  const detailGeneration = useRef(0);
  const selectionGeneration = useRef(0);
  const selectionEpoch = selectionGeneration.current;
  const bindingGeneration = useRef(0);

  const entities = useMemo(() => [...brands, ...personas, ...accounts, ...series], [brands, personas, accounts, series]);
  const current = selected ? entities.find((item) => item.kind === selected.kind && item.id === selected.id) : null;
  const editorialSeries = current?.kind === "series" && current.scope === "persona_editorial";
  const persona = current?.kind === "persona" ? current
    : current?.kind === "account" ? personas.find((row) => row.id === current.persona_id)
    : current?.kind === "series" ? (editorialSeries ? personas.find((row) => row.id === current.persona_id) : personas.find((row) => row.id === accounts.find((account) => account.id === current.account_id)?.persona_id))
    : null;
  const account = current?.kind === "account" ? current : current?.kind === "series" && !editorialSeries ? accounts.find((row) => row.id === current.account_id) : null;
  const brand = current?.kind === "brand" ? current : brands.find(row => row.id === persona?.brand_id);
  const seriesId = current?.kind === "series" ? current.id : null;
  const effectiveQuery = persona ? `persona_id=${persona.id}${account ? `&account_id=${account.id}` : ""}${seriesId ? `&series_id=${seriesId}` : ""}` : null;
  const selectedUrl = current ? `/${ROOT[current.kind]}/${current.id}` : null;
  const bindingKey = `${identityKey}:${modality}`;
  const selectedBinding = useRef(bindingKey);
  selectedBinding.current = bindingKey;
  const detailReady = loadedIdentityKey === identityKey;
  const creativeReadOnly = !["editor", "admin"].includes(role ?? "") || !detailReady || detailLoading
    || [current, brand, persona, account].some(row => row?.status === "archived");

  function selectIdentity(next: { kind: Kind; id: number } | null) {
    const nextKey = next ? `${next.kind}:${next.id}` : null;
    if (nextKey !== selectedIdentity.current && creativeDirty.current
        && !window.confirm("当前角色有未保存的创作配置。确认丢弃这些草稿并切换身份？")) return false;
    if (nextKey !== selectedIdentity.current) {
      selectionGeneration.current++;
      detailGeneration.current++;
      bindingGeneration.current++;
      selectedIdentity.current = nextKey;
      creativeDirty.current = false;
    }
    setSelected(next); setNotice("");
    return true;
  }

  async function refreshIdentity(url: string, query: string | null, key: string, epoch: number, resetDraft = false) {
    if (selectedIdentity.current !== key || selectionGeneration.current !== epoch) return;
    const generation = ++detailGeneration.current;
    const [nextRevisions, nextEffective] = await Promise.all([
      api.get<Revision[]>(`${url}/revisions`),
      query ? api.get<Effective>(`/content-identities/effective?${query}`) : Promise.resolve(null),
    ]);
    if (selectedIdentity.current !== key || selectionGeneration.current !== epoch || detailGeneration.current !== generation) return;
    setRevisions(nextRevisions); setEffective(nextEffective); setLoadedIdentityKey(key);
    if (resetDraft) setDraft(draftFrom(nextRevisions[0]?.profile || {}));
    return nextRevisions;
  }

  async function loadTree(selectInitial = false) {
    const [nextBrands, nextPersonas, nextVoices, me, nextChannels] = await Promise.all([
      api.get<Omit<Entity, "kind">[]>("/content-brands"), api.get<Omit<Entity, "kind">[]>("/content-personas"),
      api.get<{ id: number; name: string; version: number }[]>("/content-identities/brand-voices"),
      api.get<{ role: string }>("/users/me"),
      api.get<Channel[]>("/channels"),
    ]);
    const nextAccounts = (await Promise.all(nextPersonas.map((row) => api.get<Omit<Entity, "kind">[]>(`/content-personas/${row.id}/accounts`)))).flat();
    const [nextSeries, nextEditorial] = await Promise.all([
      Promise.all(nextAccounts.map((row) => api.get<Omit<Entity, "kind">[]>(`/content-accounts/${row.id}/series`))).then((rows) => rows.flat()),
      Promise.all(nextPersonas.map((row) => api.get<Omit<Entity, "kind">[]>(`/content-personas/${row.id}/series`))).then((rows) => rows.flat()),
    ]);
    setBrands(nextBrands.map((row) => ({ ...row, kind: "brand" })));
    setPersonas(nextPersonas.map((row) => ({ ...row, kind: "persona" })));
    setAccounts(nextAccounts.map((row) => ({ ...row, kind: "account" })));
    setSeries([...nextSeries.map((row) => ({ ...row, kind: "series" as Kind, scope: "account_legacy" })), ...nextEditorial.map((row) => ({ ...row, kind: "series" as Kind, scope: "persona_editorial" }))]);
    setChannels(nextChannels);
    setVoices(nextVoices);
    setRole(me.role);
    if (selectInitial && selectedIdentity.current === null && selectionGeneration.current === 0 && (nextBrands[0] || nextPersonas[0])) selectIdentity(nextBrands[0] ? { kind: "brand", id: nextBrands[0].id } : { kind: "persona", id: nextPersonas[0].id });
  }
  useEffect(() => { setLoading(true); loadTree(true).catch((error) => setError(errText(error))).finally(() => setLoading(false)); }, []);
  useEffect(() => {
    if (!selectedUrl || !identityKey) return;
    const key = identityKey;
    const generation = ++detailGeneration.current;
    const epoch = selectionEpoch;
    let active = true;
    const ownsRequest = () => active && selectedIdentity.current === key
      && selectionGeneration.current === epoch && detailGeneration.current === generation;
    setLoadedIdentityKey(null);
    setDetailLoading(true); setError(""); setRevisionConflict(false);
    Promise.all([
      api.get<Revision[]>(`${selectedUrl}/revisions`),
      effectiveQuery ? api.get<Effective>(`/content-identities/effective?${effectiveQuery}`) : Promise.resolve(null),
    ]).then(([nextRevisions, nextEffective]) => {
      if (!ownsRequest()) return;
      setRevisions(nextRevisions); setEffective(nextEffective); setDraft(draftFrom(nextRevisions[0]?.profile || {}));
      setLoadedIdentityKey(key);
    }).catch((error) => { if (ownsRequest()) setError(errText(error)); })
      .finally(() => { if (ownsRequest()) setDetailLoading(false); });
    return () => { active = false; };
  }, [selectedUrl, effectiveQuery, selectionEpoch]);
  useEffect(() => {
    let active = true;
    const key = bindingKey;
    const epoch = selectionEpoch;
    const generation = ++bindingGeneration.current;
    const ownsRequest = () => active && selectedBinding.current === key
      && selectionGeneration.current === epoch && bindingGeneration.current === generation;
    setLoadedBindingKey(null);
    if (!current || current.kind === "brand" || !effectiveQuery) { setBinding(null); setResolvedBinding(null); return; }
    Promise.all([
      api.get<Binding>(`${selectedUrl}/default-workflows/${modality}`),
      api.get<Binding>(`/content-identities/effective-workflow?${effectiveQuery}&modality=${modality}`),
    ]).then(([direct, resolved]) => {
      if (!ownsRequest()) return;
      setBinding(direct); setResolvedBinding(resolved); setDefinitionText(JSON.stringify(direct.workflow_id ? direct.definition : EMPTY_DEFINITION, null, 2));
      setLoadedBindingKey(key);
    }).catch((error) => { if (ownsRequest()) setError(errText(error)); });
    return () => { active = false; };
  }, [selectedUrl, effectiveQuery, modality, selectionEpoch]);
  useEffect(() => { if (tab === "creative" && identityKey) setCreativeVisitedKey(identityKey); }, [tab, identityKey]);

  async function createEntity(event: FormEvent) {
    event.preventDefault();
    const path = !current ? "/content-brands" : current.kind === "brand" ? `${selectedUrl}/personas` : current.kind === "persona" ? `${selectedUrl}/accounts` : current.kind === "account" ? `${selectedUrl}/series` : "";
    if (!path) return;
    try {
      const created = await api.post<{ id: number }>(path, { name: name.trim() });
      const kind: Kind = !current ? "brand" : current.kind === "brand" ? "persona" : current.kind === "persona" ? "account" : "series";
      await loadTree();
      if (selectionGeneration.current !== selectionEpoch) return;
      selectIdentity({ kind, id: created.id }); setName(""); setNotice(`${KIND_NAME[kind]}已创建。`);
    } catch (error) { if (selectionGeneration.current === selectionEpoch) setError(errText(error)); }
  }
  async function archive() {
    if (!current || !selectedUrl || !window.confirm(`归档「${current.name}」？历史版本与生产快照仍可查看。`)) return;
    try { await api.del(selectedUrl); await loadTree(); if (selectionGeneration.current === selectionEpoch) setNotice("已归档，历史记录仍可读取。"); }
    catch (error) { if (selectionGeneration.current === selectionEpoch) setError(errText(error)); }
  }
  async function saveRevision() {
    if (!current || !selectedUrl || !identityKey || !detailReady || detailLoading || revisionConflict
        || (revisions[0]?.revision_no ?? 0) !== current.current_revision) return;
    const key = identityKey;
    const epoch = selectionEpoch;
    try {
      const profile: Record<string, unknown> = { ...(revisions[0]?.profile || {}) };
      for (const { key, shape } of FIELDS) {
        delete profile[key];
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
      const next = await refreshIdentity(selectedUrl, effectiveQuery, key, epoch, true);
      if (next && selectedIdentity.current === key && selectionGeneration.current === epoch) setNotice(`修订 v${next[0]?.revision_no} 已保存，旧快照不会改变。`);
    } catch (error) {
      if (selectedIdentity.current !== key || selectionGeneration.current !== epoch) return;
      setError(error instanceof SyntaxError ? "JSON 格式不正确，请检查后再保存。" : errText(error));
      if (error instanceof ApiError && error.status === 409) {
        setRevisionConflict(true);
        await loadTree();
        const next = await refreshIdentity(selectedUrl, effectiveQuery, key, epoch);
        if (next && selectedIdentity.current === key && selectionGeneration.current === epoch) setNotice("版本已被其他人更新。当前表单仍是旧草稿；请核对最新修订后显式加载，才可再次保存。");
      }
    }
  }
  async function saveDefault() {
    if (!selectedUrl || !binding || !current || current.kind === "brand" || loadedBindingKey !== bindingKey) return;
    const key = bindingKey;
    const epoch = selectionEpoch;
    const generation = bindingGeneration.current;
    try {
      const definition = JSON.parse(definitionText);
      const next = await api.post<Binding>(`${selectedUrl}/default-workflows/${modality}`, { expected_revision: binding.revision, definition });
      if (selectedBinding.current !== key || selectionGeneration.current !== epoch || bindingGeneration.current !== generation) return;
      setBinding(next); setResolvedBinding({ ...next, source: current.kind }); setNotice("默认工作流已保存为新版本；已有内容单元不会自动重绑。");
    } catch (error) { if (selectedBinding.current === key && selectionGeneration.current === epoch && bindingGeneration.current === generation) setError(error instanceof SyntaxError ? "工作流定义 JSON 格式不正确。" : errText(error)); }
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
    return <button key={`${entity.kind}-${entity.id}`} onClick={() => selectIdentity({ kind: entity.kind, id: entity.id })} className={`block w-full rounded-lg px-3 py-2 text-left text-sm ${current?.kind === entity.kind && current.id === entity.id ? "bg-indigo-50 font-semibold text-indigo-700" : "hover:bg-slate-50"}`} style={{ paddingLeft: 12 + depth * 16 }}><span className="mr-2 text-xs text-slate-400">{KIND_NAME[entity.kind]}</span>{entity.name}{entity.status === "archived" && <span className="ml-1 text-xs text-slate-400">已归档</span>}</button>;
  }
  const brandless = personas.filter((row) => row.brand_id == null);

  return <div className="mx-auto max-w-7xl px-6 py-9"><div className="mb-6"><p className="text-xs font-semibold uppercase tracking-widest text-indigo-600">Identity Workspace</p><h1 className="mt-2 text-3xl font-semibold">内容身份</h1><p className="mt-2 text-sm text-slate-500">品牌 → 角色 → 账号 → 栏目；修订长期保存，生产时固定快照。</p></div>
    {error && <div className="mb-4"><ErrorBanner message={error} /></div>}{notice && <p className="mb-4 rounded-lg bg-indigo-50 p-3 text-sm text-indigo-700">{notice}</p>}
    <StarterPersonaGallery personaId={persona?.id} accountId={account?.id} seriesId={seriesId} refreshRevision={current?.current_revision} readOnly={!["editor", "admin"].includes(role ?? "")} onInitialized={async personaId => { await loadTree(); if (selectionGeneration.current !== selectionEpoch || !selectIdentity({ kind: "persona", id: personaId })) return; setTab("creative"); setNotice("已保存独立角色与默认流程；配置状态见就绪卡片，不代表真实成品质量已验收。已有记录和人工修改未覆盖。"); }} />
    {loading ? <Spinner label="读取身份树…" /> : <div className="grid gap-5 lg:grid-cols-[280px_1fr]"><aside className="rounded-2xl border border-slate-200 bg-white p-3"><h2 className="px-3 py-2 text-sm font-semibold">身份层级</h2>{brands.length + personas.length === 0 && <EmptyState title="还没有内容身份" hint="先创建品牌，或使用既有无品牌角色。" />}{brands.map((brand) => <div key={brand.id}>{entityButton(brand, 0)}{personas.filter((row) => row.brand_id === brand.id).map((p) => <div key={p.id}>{entityButton(p, 1)}{series.filter((row) => row.scope === "persona_editorial" && row.persona_id === p.id).map((s) => entityButton(s, 2))}{accounts.filter((row) => row.persona_id === p.id).map((a) => <div key={a.id}>{entityButton(a, 2)}{series.filter((row) => row.account_id === a.id).map((s) => entityButton(s, 3))}</div>)}</div>)}</div>)}{brandless.length > 0 && <div className="mt-3 border-t pt-3"><p className="px-3 text-xs text-slate-500">历史无品牌角色</p>{brandless.map((p) => <div key={p.id}>{entityButton(p, 1)}{series.filter((row) => row.scope === "persona_editorial" && row.persona_id === p.id).map((s) => entityButton(s, 2))}{accounts.filter((row) => row.persona_id === p.id).map((a) => <div key={a.id}>{entityButton(a, 2)}{series.filter((row) => row.account_id === a.id).map((s) => entityButton(s, 3))}</div>)}</div>)}</div>}
      <form onSubmit={createEntity} className="mt-4 space-y-2 border-t px-2 pt-4"><label className="text-xs text-slate-600">{!current ? "新建品牌" : current.kind === "series" ? "请选择上级创建子项" : `在${KIND_NAME[current.kind]}下新增${KIND_NAME[current.kind === "brand" ? "persona" : current.kind === "persona" ? "account" : "series"]}`}</label><input className={inputClass} value={name} onChange={(event) => setName(event.target.value)} placeholder="名称" required /><Button type="submit" disabled={current?.kind === "series" || current?.status === "archived"}>新增</Button><button type="button" className="ml-2 text-xs text-indigo-700" onClick={() => selectIdentity(null)}>新建根品牌</button></form></aside>
      <main className="min-w-0">{!current ? <EmptyState title="选择左侧身份或创建品牌" /> : <><div className="rounded-2xl border border-slate-200 bg-white p-5"><div className="flex flex-wrap items-center justify-between gap-3"><div><p className="text-xs text-slate-500">{KIND_NAME[current.kind]} · #{current.id}</p><h2 className="mt-1 text-xl font-semibold">{current.name}</h2><p className="mt-1 text-xs text-slate-500">{current.status === "archived" ? "已归档，只能查看历史" : `当前修订 v${current.current_revision}`}</p></div>{current.status !== "archived" && <Button variant="danger" onClick={archive}>归档</Button>}</div></div>
      <div role="tablist" className="mt-5 flex gap-1 overflow-x-auto border-b">{TABS.map(([key, label]) => <button key={key} role="tab" aria-selected={tab === key} onClick={() => setTab(key)} className={`whitespace-nowrap border-b-2 px-3 py-3 text-sm ${tab === key ? "border-indigo-600 text-indigo-700" : "border-transparent text-slate-500"}`}>{label}</button>)}</div>
      {detailLoading || !detailReady ? <Spinner label="读取修订…" /> : <div className="mt-5 space-y-4">{["identity", "expression", "boundaries"].includes(tab) && <>{revisionConflict && <div className="rounded-xl border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900"><p>最新修订为 v{revisions[0]?.revision_no ?? "未知"}；当前表单来自旧版本，已停止保存。请先复制需要保留的改动，再加载最新修订。</p><Button variant="secondary" onClick={() => { setDraft(draftFrom(revisions[0]?.profile || {})); setRevisionConflict(false); setError(""); setNotice("已加载最新修订，请重新核对后保存。"); }}>加载最新修订（覆盖当前表单）</Button></div>}<div className="grid gap-3 xl:grid-cols-2">{FIELDS.filter((field) => field.tab === tab).map(({ key, label, shape }) => fieldEditor(key, label, shape))}</div><Button onClick={saveRevision} disabled={current.status === "archived" || revisionConflict}>保存新修订 v{current.current_revision + 1}</Button><section className="rounded-xl border bg-white p-4"><h3 className="font-medium">修订历史</h3>{revisions.length ? <ul className="mt-2 space-y-2 text-xs">{revisions.map((revision) => <li key={revision.id} className="rounded border p-2">v{revision.revision_no} · #{revision.id} · {revision.created_at || ""}<pre className="mt-1 overflow-x-auto whitespace-pre-wrap text-slate-500">{JSON.stringify(revision.profile, null, 2)}</pre></li>)}</ul> : <p className="mt-2 text-xs text-slate-500">尚未提交身份画像修订。</p>}</section></>}
      {persona && (tab === "creative" || creativeVisitedKey === identityKey) && <div hidden={tab !== "creative"}><Suspense fallback={<Spinner label="读取创作配置…" />}><PersonaCreativeConfig key={`${identityKey}:${selectionEpoch}`} current={current} persona={persona} readOnly={creativeReadOnly} accountId={account?.id || null} seriesId={seriesId} revisions={revisions} effective={effective} onSaved={async () => { const key = identityKey!; if (selectedIdentity.current !== key || selectionGeneration.current !== selectionEpoch) return; await loadTree(); return refreshIdentity(selectedUrl!, effectiveQuery, key, selectionEpoch); }} onNotice={value => { if (selectedIdentity.current === identityKey && selectionGeneration.current === selectionEpoch) setNotice(value); }} onDirtyChange={value => { if (selectedIdentity.current === identityKey && selectionGeneration.current === selectionEpoch) creativeDirty.current = value; }} /></Suspense></div>}
      {tab === "accounts" && <section className="rounded-xl border bg-white p-5"><h3 className="font-medium">持久化层级</h3><p className="mt-2 text-sm text-slate-500">选择品牌、角色或账号，可创建直属子级；归档不会删除历史快照。各平台的公开账号名在这里登记（不要填写密码或 AppSecret）；登记公开标识不等于平台已登录，也不等于可以自动发布。</p>{persona && <p className="mt-3 text-sm">角色：{persona.name} · 账号 {accounts.filter((row) => row.persona_id === persona.id).length} 个 · 跨平台栏目 {series.filter((row) => row.scope === "persona_editorial" && row.persona_id === persona.id).length} 档</p>}{account && <p className="mt-1 text-sm">账号：{account.name} · 栏目 {series.filter((row) => row.account_id === account.id).length} 个</p>}{current.kind !== "series" && <form onSubmit={createEntity} className="mt-4 flex flex-wrap gap-2"><input aria-label="新子级名称" className={inputClass} required value={name} onChange={(event) => setName(event.target.value)} placeholder={`新建${KIND_NAME[current.kind === "brand" ? "persona" : current.kind === "persona" ? "account" : "series"]}名称`} /><Button type="submit" disabled={current.status === "archived"}>创建子级</Button></form>}{current.status !== "archived" && <div className="mt-4"><Button variant="danger" onClick={archive}>归档当前{KIND_NAME[current.kind]}</Button></div>}</section>}
      {tab === "accounts" && persona && current.status !== "archived" && <div className="grid gap-4 lg:grid-cols-2">
        <EditorialSeriesCreate personaId={persona.id} onDone={async (created) => { await loadTree(); if (selectionGeneration.current === selectionEpoch) selectIdentity({ kind: "series", id: created }); }} onError={setError} />
        <ChannelAccountRegister personaId={persona.id} channels={channels} role={role} onDone={loadTree} onError={setError} />
      </div>}
      {tab === "accounts" && current.kind === "series" && current.scope === "persona_editorial" && <SeriesTargetsPanel key={current.id} seriesId={current.id} personaId={persona?.id ?? null} archived={current.status === "archived"} accounts={accounts.filter((row) => row.persona_id === persona?.id)} channels={channels} readOnly={!["editor", "admin"].includes(role ?? "")} onChanged={loadTree} onNotice={setNotice} onError={setError} />}
      {tab === "workflow" && <section className="rounded-xl border bg-white p-5"><h3 className="font-medium">角色 / 账号 / 栏目 × 内容形态</h3>{current.kind === "brand" ? <p className="mt-2 text-sm text-slate-500">请选择角色、账号或栏目查看默认工作流。</p> : <><Field label="内容形态"><select className={inputClass} value={modality} onChange={(event) => setModality(event.target.value)}><option value="text">文字</option><option value="graphic">图文</option><option value="video">视频</option></select></Field><p className="mt-3 text-sm">本级：{binding?.workflow_id ? `v${binding.workflow_version} · Workflow #${binding.workflow_id}` : "未设置"}；当前生效：{resolvedBinding?.source || "未绑定"}{resolvedBinding?.workflow_id ? ` · Workflow #${resolvedBinding.workflow_id}` : ""}</p><p className="mt-2 text-xs text-slate-500">保存新版本不会自动修改已有内容单元。定义使用现有 Workflow schema；服务端检查可移植性和执行能力。</p><Field label="新默认工作流定义 JSON"><textarea className={`${inputClass} mt-2 min-h-44 font-mono text-xs`} value={definitionText} disabled={current.status === "archived"} onChange={(event) => setDefinitionText(event.target.value)} /></Field><Button onClick={saveDefault} disabled={current.status === "archived" || !binding}>另存为本级默认新版本</Button></>}</section>}
      {tab === "accounts" && account && <AccountPublisherPanel key={account.id} accountId={account.id} archived={current.status === "archived"} />}
      {tab === "memory" && <MemoryPanel key={`${current.kind}:${current.id}`} scopeType={current.kind} scopeId={current.id} />}</div>}</>}</main></div>}
  </div>;
}

function registerFailure(error: unknown): string {
  if (!(error instanceof ApiError)) return "登记失败，请重试。";
  if (error.status === 403) return "只有管理员可以登记平台账号。";
  if (error.status === 409 && error.message === "platform_identity_conflict") return "这个平台标识已经登记过。归档也不会把同一个真实账号让给别的角色。";
  if (error.message === "platform_account_public_id_invalid") return "公开标识不合格。不要填写密码、AppSecret 或 token。公众号请填 wx 开头的 AppID，其他平台填账号名或 @handle。";
  return error.message || "登记失败，请重试。";
}

function EditorialSeriesCreate({ personaId, onDone, onError }: {
  personaId: number; onDone: (seriesId: number) => Promise<void>; onError: (message: string) => void;
}) {
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  return <form onSubmit={async (event: FormEvent) => {
    event.preventDefault();
    if (busy || !name.trim()) return;
    setBusy(true);
    try {
      const created = await api.post<{ id: number }>(`/content-personas/${personaId}/series`, { name: name.trim() });
      setName("");
      await onDone(created.id);
    } catch (error) { onError(error instanceof ApiError ? `${error.status} · ${error.message}` : "创建失败，请重试。"); }
    finally { setBusy(false); }
  }} className="rounded-xl border border-slate-200 bg-white p-4">
    <h4 className="text-sm font-medium">新建跨平台栏目</h4>
    <p className="mt-1 text-xs text-slate-500">属于角色的编辑栏目，可稍后绑定多个渠道账号。同名栏目不会自动合并。</p>
    <div className="mt-2 flex gap-2"><input aria-label="栏目名称" className={inputClass} required maxLength={200} value={name} onChange={(event) => setName(event.target.value)} placeholder="例如「技术拆解」" /><Button type="submit" disabled={busy}>{busy ? "创建中…" : "创建栏目"}</Button></div>
  </form>;
}

function ChannelAccountRegister({ personaId, channels, role, onDone, onError }: {
  personaId: number; channels: Channel[]; role: string | null; onDone: () => Promise<void>; onError: (message: string) => void;
}) {
  const [channel, setChannel] = useState(channels[0]?.channel || "");
  const [name, setName] = useState("");
  const [handle, setHandle] = useState("");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const admin = role === "admin";
  const effectiveChannel = channels.some((row) => row.channel === channel) ? channel : channels[0]?.channel || "";
  return <form onSubmit={async (event: FormEvent) => {
    event.preventDefault();
    if (!admin || busy || !effectiveChannel) return;
    setBusy(true); setNotice("");
    try {
      await api.post(`/content-personas/${personaId}/channel-accounts`, { name: name.trim(), platform_channel: effectiveChannel, platform_account_id: handle.trim() });
      setName(""); setHandle(""); setNotice("已登记公开账号。这还不是登录，也不是发布。");
      await onDone();
    } catch (error) { onError(registerFailure(error)); }
    finally { setBusy(false); }
  }} className="rounded-xl border border-slate-200 bg-white p-4">
    <h4 className="text-sm font-medium">登记平台公开身份</h4>
    <p className="mt-1 text-xs text-slate-500">{admin ? "只填公开名称与标识；不要填密码、AppSecret、token 或带登录信息的网址。" : "登记平台账号只限管理员。"}</p>
    <div className="mt-2 grid gap-2 sm:grid-cols-3">
      <select aria-label="平台" className={inputClass} value={effectiveChannel} disabled={!admin || busy} onChange={(event) => setChannel(event.target.value)}>
        {channels.map((row) => <option key={row.channel} value={row.channel}>{row.label}</option>)}
      </select>
      <input aria-label="显示名称" className={inputClass} required maxLength={200} disabled={!admin || busy} value={name} onChange={(event) => setName(event.target.value)} placeholder="显示名称" />
      <input aria-label="公开标识" className={inputClass} name="public-handle" autoComplete="off" spellCheck={false} required maxLength={64} disabled={!admin || busy} value={handle} onChange={(event) => setHandle(event.target.value)} placeholder={effectiveChannel === "wechat" ? "wx 开头 AppID" : "账号名 / @handle"} />
    </div>
    <div className="mt-2 flex items-center gap-3"><Button type="submit" disabled={!admin || busy}>{busy ? "登记中…" : "登记账号"}</Button>{notice && <span className="text-xs text-indigo-700">{notice}</span>}</div>
  </form>;
}

function SeriesTargetsPanel({ seriesId, personaId, archived, accounts, channels, readOnly, onChanged, onNotice, onError }: {
  seriesId: number; personaId: number | null; archived: boolean;
  accounts: Entity[]; channels: Channel[]; readOnly: boolean;
  onChanged: () => Promise<void>; onNotice: (message: string) => void; onError: (message: string) => void;
}) {
  const [targets, setTargets] = useState<SeriesTarget[]>([]);
  const [loading, setLoading] = useState(true);
  const [accountId, setAccountId] = useState<number | null>(accounts[0]?.id ?? null);
  const [form, setForm] = useState("");
  const [busy, setBusy] = useState(false);
  const boundAccounts = new Set(targets.map((row) => row.account_id));
  const eligible = accounts.filter((row) => !boundAccounts.has(row.id) && row.platform_channel);
  const platformChannels = new Map(accounts.filter((row) => row.platform_channel).map((row) => [row.id, row.platform_channel as string]));
  const forms = platformChannels.get(accountId ?? -1) ? channels.find((row) => row.channel === platformChannels.get(accountId ?? -1))?.content_forms ?? [] : [];

  async function load() {
    try { setTargets(await api.get<SeriesTarget[]>(`/content-series/${seriesId}/targets`)); }
    catch (error) { onError(errText(error)); }
    finally { setLoading(false); }
  }
  useEffect(() => { setLoading(true); load(); }, [seriesId]);

  async function mutate(action: () => Promise<unknown>, notice: string) {
    if (busy) return;
    setBusy(true);
    try { await action(); await load(); await onChanged(); onNotice(notice); }
    catch (error) { onError(errText(error)); }
    finally { setBusy(false); }
  }

  return <section className="rounded-xl border bg-white p-5">
    <h3 className="font-medium">投放绑定（栏目 × 账号 × 内容形态）</h3>
    <p className="mt-1 text-xs text-slate-500">绑定只是默认投放目标，不是授权：不绕过内容审核、交付授权或平台能力验证。同平台的不同账号是不同目标。</p>
    {loading ? <Spinner label="读取投放绑定…" /> : <>
      {targets.length === 0 ? <p className="mt-3 text-sm text-slate-500">还没有投放绑定。</p> : <ul className="mt-3 space-y-2">
        {targets.map((row) => <li key={row.id} className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-slate-100 px-3 py-2 text-sm">
          <span>{row.account_name || `账号 #${row.account_id}`} · {channels.find((c) => c.channel === row.platform_channel)?.label || row.platform_channel} / {row.content_form}</span>
          <span className="flex items-center gap-2 text-xs">
            <span className={row.enabled ? "text-emerald-700" : "text-slate-500"}>{row.enabled ? "启用中" : "已停用"} · v{row.version}</span>
            {!readOnly && !archived && <Button size="sm" variant="secondary" disabled={busy} onClick={() => mutate(() => api.patch(`/content-series/${seriesId}/targets/${row.id}`, { enabled: !row.enabled, expected_version: row.version }), row.enabled ? "绑定已停用；新的投放授权会被阻断。" : "绑定已重新启用。")}>{row.enabled ? "停用" : "启用"}</Button>}
            {!readOnly && !archived && <Button size="sm" variant="danger" disabled={busy} onClick={() => { if (window.confirm("解除这条投放绑定？历史交付记录不受影响。")) mutate(() => api.del(`/content-series/${seriesId}/targets/${row.id}`), "绑定已解除。"); }}>解除</Button>}
          </span>
        </li>)}
      </ul>}
      {!readOnly && !archived && <form onSubmit={(event) => {
        event.preventDefault();
        if (accountId == null || !form) return;
        mutate(() => api.post(`/content-series/${seriesId}/targets`, { account_id: accountId, content_form: form }), "已绑定投放目标。可选择性默认已建立，不代表已审核或已发布。");
      }} className="mt-4 flex flex-wrap items-end gap-2">
        <label className="text-xs text-slate-600">目标账号
          <select aria-label="目标账号" className={`${inputClass} mt-1`} value={accountId ?? ""} onChange={(event) => { setAccountId(Number(event.target.value) || null); setForm(""); }}>
            <option value="">选择账号</option>
            {eligible.map((row) => <option key={row.id} value={row.id}>{row.name}{row.status === "archived" ? "（已归档）" : ""}</option>)}
          </select>
        </label>
        <label className="text-xs text-slate-600">内容形态
          <select aria-label="内容形态" className={`${inputClass} mt-1`} value={form} onChange={(event) => setForm(event.target.value)}>
            <option value="">选择形态</option>
            {forms.map((row) => <option key={row.content_form} value={row.content_form}>{row.label || row.content_form}</option>)}
          </select>
        </label>
        <Button type="submit" disabled={busy || accountId == null || !form}>{busy ? "绑定中…" : "绑定投放目标"}</Button>
        {personaId == null && <span className="text-xs text-slate-500">先选择所属角色。</span>}
      </form>}
      {!readOnly && !archived && eligible.length === 0 && <p className="mt-2 text-xs text-slate-500">没有可绑定的账号：先在本角色下登记带平台身份的账号。</p>}
    </>}
  </section>;
}
