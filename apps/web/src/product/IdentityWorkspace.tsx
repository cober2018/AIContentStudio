import { FormEvent, lazy, Suspense, useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api, ApiError, currentUser } from "../api";
import { Button, Chip, EmptyState, ErrorBanner, Field, Notice, Page, PageHeader, Section, Spinner, Tabs, inputClass } from "../components/ui";
import { ProfileOverview } from "./IdentityProfileView";
import { PersonaDiscoveryStatus } from "./DiscoveryPanel";
import { MemoryPanel } from "./LearningWorkspace";
import AccountPublisherPanel from "./AccountPublisherPanel";
import StarterPersonaGallery from "./StarterGallery";

const PersonaReferenceStylePanel = lazy(() => import("./CapabilityMemoryPanel").then(module => ({ default: module.PersonaReferenceStylePanel })));
const PersonaCreativeConfig = lazy(() => import("./PersonaCreativeConfig"));

type Kind = "brand" | "persona" | "account" | "series";
type Entity = { kind: Kind; id: number; name: string; status: string; brand_id?: number | null; persona_id?: number | null; account_id?: number; scope?: string; platform_channel?: string | null; current_revision: number };
type Channel = { channel: string; label: string; content_forms: { content_form: string; label: string }[] };
type SeriesTarget = { id: number; series_id: number; account_id: number; account_name: string | null; platform_channel: string | null; content_form: string; enabled: boolean; version: number };
type Revision = { id: number; revision_no: number; profile: Record<string, unknown>; checksum: string; created_at: string | null };
type Effective = { effective_profile: Record<string, unknown>; field_origins: Record<string, string>; revision_ids: Record<string, number | null> };
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
  ["summary", "概览"], ["edit", "编辑资料"], ["history", "修订历史"],
  ["creative", "创作配置"], ["accounts", "关联与管理"],
  ["memory", "内容记忆"], ["publisher", "平台连接"],
] as const;

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
  const [user, setUser] = useState(currentUser);
  useEffect(() => {
    const sync = () => setUser(currentUser());
    window.addEventListener("storage", sync); window.addEventListener("focus", sync);
    return () => { window.removeEventListener("storage", sync); window.removeEventListener("focus", sync); };
  }, []);
  return <IdentityWorkspaceForUser key={user} user={user} />;
}
function IdentityWorkspaceForUser({ user }: { user: string }) {
  const [params, setParams] = useSearchParams();
  const directory = (Object.keys(ROOT).includes(params.get("directory") || "") ? params.get("directory") : "persona") as Kind;
  const routeKind = params.get("kind") || (params.has("persona") ? "persona" : "");
  const routeId = params.get("id") || params.get("persona") || "";
  const routeSelection = Object.keys(ROOT).includes(routeKind) && /^[1-9]\d*$/.test(routeId) ? { kind: routeKind as Kind, id: Number(routeId) } : null;
  const invalidSelection = (params.has("kind") || params.has("id") || params.has("persona")) && !routeSelection;
  const routeView = params.get("view") || "summary";

  const [brands, setBrands] = useState<Entity[]>([]);
  const [personas, setPersonas] = useState<Entity[]>([]);
  const [accounts, setAccounts] = useState<Entity[]>([]);
  const [series, setSeries] = useState<Entity[]>([]);
  const [channels, setChannels] = useState<Channel[]>([]);
  const [selected, setSelected] = useState<{ kind: Kind; id: number } | null>(routeSelection);
  const [revisions, setRevisions] = useState<Revision[]>([]);
  const [effective, setEffective] = useState<Effective | null>(null);
  const [voices, setVoices] = useState<{ id: number; name: string; version: number }[]>([]);
  const [draft, setDraft] = useState<Record<FieldKey, DraftField>>(draftFrom({}));
  const draftRef = useRef(draft);
  draftRef.current = draft;
  const tab = routeView;
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(true);
  const [treeError, setTreeError] = useState("");
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [revisionConflict, setRevisionConflict] = useState(false);
  const [busy, setBusy] = useState(false);
  const pending = useRef(false);
  const baselineDraft = useRef(JSON.stringify(draftFrom({})));
  const profileDirty = useRef(false);
  profileDirty.current = JSON.stringify(draft) !== baselineDraft.current;
  const [role, setRole] = useState<string | null>(null);
  const [loadedIdentityKey, setLoadedIdentityKey] = useState<string | null>(null);
  const creativeDirty = useRef(false);
  const referenceStyleDirty = useRef(false);
  const [creativeVisitedKey, setCreativeVisitedKey] = useState<string | null>(null);
  const identityKey = selected ? `${selected.kind}:${selected.id}` : null;
  const selectedIdentity = useRef(identityKey);
  selectedIdentity.current = identityKey;
  const detailGeneration = useRef(0);
  const selectionGeneration = useRef(0);
  const selectionEpoch = selectionGeneration.current;

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
  const detailReady = loadedIdentityKey === identityKey;
  const missingAncestor = Boolean(current && (
    (current.kind === "persona" && current.brand_id != null && !brand)
    || (current.kind === "account" && current.persona_id != null && !persona)
    || (current.kind === "series" && (editorialSeries ? !persona : !account))
    || (persona?.brand_id != null && !brand)
  ));
  const creativeReadOnly = missingAncestor || !["editor", "admin"].includes(role ?? "") || !detailReady || detailLoading
    || [current, brand, persona, account].some(row => row?.status === "archived");

  const acceptedParams = useRef(params.toString());
  const acceptedHistoryIndex = useRef<number | null>(window.history.state?.idx ?? null);
  const restoringHistory = useRef(false);
  const acceptedPop = useRef(false);
  const canLeave = () => !pending.current && (!(profileDirty.current || creativeDirty.current || referenceStyleDirty.current) || window.confirm("有未保存的修改，确认离开并丢弃草稿？"));
  function navigate(next: URLSearchParams) {
    const nextKind = next.get("kind") || (next.has("persona") ? "persona" : "");
    const nextId = next.get("id") || next.get("persona");
    const sameObject = selectedIdentity.current === (nextKind && nextId ? `${nextKind}:${nextId}` : null);
    if (pending.current || (!sameObject && !canLeave())) return;
    acceptedParams.current = next.toString();
    setParams(next);
  }
  function changeView(view: string) {
    const next = new URLSearchParams(params); next.set("view", view); navigate(next);
  }
  useEffect(() => {
    const unload = (event: BeforeUnloadEvent) => {
      if (pending.current || profileDirty.current || creativeDirty.current || referenceStyleDirty.current) { event.preventDefault(); event.returnValue = ""; }
    };
    const click = (event: MouseEvent) => {
      const link = (event.target as Element | null)?.closest?.("a[href]") as HTMLAnchorElement | null;
      if (link && link.href !== window.location.href && !canLeave()) { event.preventDefault(); event.stopPropagation(); }
    };
    const pop = (event: PopStateEvent) => {
      if (restoringHistory.current) { restoringHistory.current = false; return; }
      const nextParams = new URLSearchParams(window.location.search);
      const nextKind = nextParams.get("kind") || (nextParams.has("persona") ? "persona" : "");
      const nextId = nextParams.get("id") || nextParams.get("persona");
      const sameObject = window.location.pathname === "/identities" && selectedIdentity.current === (nextKind && nextId ? `${nextKind}:${nextId}` : null);
      if ((!pending.current && sameObject) || canLeave()) { acceptedPop.current = true; return; }
      const nextIndex: unknown = event.state?.idx;
      if (typeof nextIndex === "number" && acceptedHistoryIndex.current != null) {
        event.stopImmediatePropagation();
        restoringHistory.current = true;
        window.history.go(acceptedHistoryIndex.current - nextIndex);
      }
    };
    window.addEventListener("beforeunload", unload); document.addEventListener("click", click, true); window.addEventListener("popstate", pop, true);
    return () => { window.removeEventListener("beforeunload", unload); document.removeEventListener("click", click, true); window.removeEventListener("popstate", pop, true); };
  }, []);
  useEffect(() => {
    const nextKey = routeSelection ? `${routeSelection.kind}:${routeSelection.id}` : null;
    if (nextKey === selectedIdentity.current) { acceptedParams.current = params.toString(); acceptedHistoryIndex.current = window.history.state?.idx ?? null; acceptedPop.current = false; return; }
    if (nextKey !== selectedIdentity.current && !acceptedPop.current && acceptedParams.current !== params.toString() && !canLeave()) { setParams(new URLSearchParams(acceptedParams.current), { replace: true }); return; }
    acceptedParams.current = params.toString(); acceptedHistoryIndex.current = window.history.state?.idx ?? null; acceptedPop.current = false;
    if (nextKey !== selectedIdentity.current) {
      selectionGeneration.current++; detailGeneration.current++;
      selectedIdentity.current = nextKey; setSelected(routeSelection);
      creativeDirty.current = false; referenceStyleDirty.current = false;
      setCreativeVisitedKey(null); setName("");
    }
    if (nextKey !== identityKey) {
      setDraft(draftFrom({})); baselineDraft.current = JSON.stringify(draftFrom({}));
    }
    setNotice("");
  }, [params.toString()]);
  function selectIdentity(next: { kind: Kind; id: number } | null) {
    const nextParams = new URLSearchParams(params);
    nextParams.delete("persona");
    if (next) { nextParams.set("kind", next.kind); nextParams.set("id", String(next.id)); }
    else { nextParams.delete("kind"); nextParams.delete("id"); }
    nextParams.set("view", "summary");
    const nextKey = next ? `${next.kind}:${next.id}` : null;
    if (pending.current || (nextKey !== selectedIdentity.current && !canLeave())) return false;
    acceptedParams.current = nextParams.toString(); setParams(nextParams); return true;
  }

  async function refreshIdentity(url: string, query: string | null, key: string, epoch: number, resetDraft = false) {
    if (selectedIdentity.current !== key || selectionGeneration.current !== epoch || currentUser() !== user) return;
    const generation = ++detailGeneration.current;
    const [nextRevisions, nextEffective] = await Promise.all([
      api.get<Revision[]>(`${url}/revisions`),
      query ? api.get<Effective>(`/content-identities/effective?${query}`) : Promise.resolve(null),
    ]);
    if (selectedIdentity.current !== key || selectionGeneration.current !== epoch || detailGeneration.current !== generation || currentUser() !== user) return;
    setRevisions(nextRevisions); setEffective(nextEffective); setLoadedIdentityKey(key);
    if (resetDraft) { setDraft(draftFrom(nextRevisions[0]?.profile || {})); baselineDraft.current = JSON.stringify(draftFrom(nextRevisions[0]?.profile || {})); }
    return nextRevisions;
  }

  const treeGeneration = useRef(0);
  async function loadTree() {
    const generation = ++treeGeneration.current;
    setRole(null); setTreeError("");
    try {
    const [nextBrands, nextPersonas, nextVoices, me, nextChannels] = await Promise.all([
      api.get<Omit<Entity, "kind">[]>("/content-brands"), api.get<Omit<Entity, "kind">[]>("/content-personas"),
      api.get<{ id: number; name: string; version: number }[]>("/content-identities/brand-voices"),
      api.get<{ role: string }>("/users/me").catch(error => { if (generation === treeGeneration.current && currentUser() === user) setError(`权限读取失败，当前仅可查看。${errText(error)}`); return null; }),
      api.get<Channel[]>("/channels"),
    ]);
    const nextAccounts = await api.get<Omit<Entity, "kind">[]>("/content-accounts");
    const [nextSeries, nextEditorial] = await Promise.all([
      Promise.all(nextAccounts.map((row) => api.get<Omit<Entity, "kind">[]>(`/content-accounts/${row.id}/series`))).then((rows) => rows.flat()),
      Promise.all(nextPersonas.map((row) => api.get<Omit<Entity, "kind">[]>(`/content-personas/${row.id}/series`))).then((rows) => rows.flat()),
    ]);
    if (generation !== treeGeneration.current || currentUser() !== user) return;
    setBrands(nextBrands.map((row) => ({ ...row, kind: "brand" })));
    setPersonas(nextPersonas.map((row) => ({ ...row, kind: "persona" })));
    setAccounts(nextAccounts.map((row) => ({ ...row, kind: "account" })));
    setSeries([...nextSeries.map((row) => ({ ...row, kind: "series" as Kind, scope: "account_legacy" })), ...nextEditorial.map((row) => ({ ...row, kind: "series" as Kind, scope: "persona_editorial" }))]);
    setChannels(nextChannels);
    setVoices(nextVoices);
    setRole(me?.role ?? null);
    } catch (error) {
      if (generation === treeGeneration.current && currentUser() === user) { setRole(null); setTreeError(errText(error)); }
      throw error;
    }
  }
  useEffect(() => { setLoading(true); loadTree().catch((error) => setError(errText(error))).finally(() => setLoading(false)); }, []);
  useEffect(() => {
    if (!selectedUrl || !identityKey) return;
    const key = identityKey;
    const generation = ++detailGeneration.current;
    const epoch = selectionEpoch;
    let active = true;
    const ownsRequest = () => active && selectedIdentity.current === key
      && selectionGeneration.current === epoch && detailGeneration.current === generation && currentUser() === user;
    setLoadedIdentityKey(null); setRevisions([]); setEffective(null);
    setDetailLoading(true); setError(""); setRevisionConflict(false);
    Promise.all([
      api.get<Revision[]>(`${selectedUrl}/revisions`),
      effectiveQuery ? api.get<Effective>(`/content-identities/effective?${effectiveQuery}`) : Promise.resolve(null),
    ]).then(([nextRevisions, nextEffective]) => {
      if (!ownsRequest()) return;
      setRevisions(nextRevisions); setEffective(nextEffective); setDraft(draftFrom(nextRevisions[0]?.profile || {}));
      baselineDraft.current = JSON.stringify(draftFrom(nextRevisions[0]?.profile || {}));
      setLoadedIdentityKey(key);
    }).catch((error) => { if (ownsRequest()) setError(errText(error)); })
      .finally(() => { if (ownsRequest()) setDetailLoading(false); });
    return () => { active = false; };
  }, [selectedUrl, effectiveQuery, selectionEpoch]);
  useEffect(() => { if (tab === "creative" && identityKey) setCreativeVisitedKey(identityKey); }, [tab, identityKey]);

  function scopedError(message: string) { if (selectedIdentity.current === identityKey && selectionGeneration.current === selectionEpoch && currentUser() === user) setError(message); }
  function scopedNotice(message: string) { if (selectedIdentity.current === identityKey && selectionGeneration.current === selectionEpoch && currentUser() === user) setNotice(message); }
  function beginChildMutation() {
    if (pending.current || currentUser() !== user) return false;
    pending.current = true; setBusy(true); return true;
  }
  function childBusy(value: boolean) { pending.current = value; setBusy(value); }
  async function seriesCreated(id: number) {
    const key = identityKey; const epoch = selectionEpoch;
    await loadTree();
    if (selectedIdentity.current !== key || selectionGeneration.current !== epoch || currentUser() !== user) return;
    childBusy(false); selectIdentity({ kind: "series", id });
  }
  async function createEntity(event: FormEvent) {
    event.preventDefault();
    const path = !current ? "/content-brands" : current.kind === "brand" ? `${selectedUrl}/personas` : current.kind === "persona" ? `${selectedUrl}/accounts` : current.kind === "account" ? `${selectedUrl}/series` : "";
    if (currentUser() !== user || !path || !name.trim() || pending.current || creativeReadOnly && current || !["editor", "admin"].includes(role ?? "")) return;
    pending.current = true; setBusy(true);
    try {
      const created = await api.post<{ id: number }>(path, { name: name.trim() });
      const kind: Kind = !current ? "brand" : current.kind === "brand" ? "persona" : current.kind === "persona" ? "account" : "series";
      await loadTree();
      if (selectionGeneration.current !== selectionEpoch || currentUser() !== user) return;
      pending.current = false; selectIdentity({ kind, id: created.id }); setName(""); setNotice(`${KIND_NAME[kind]}已创建。`);
    } catch (error) { if (selectionGeneration.current === selectionEpoch && currentUser() === user) setError(errText(error)); }
    finally { pending.current = false; setBusy(false); }
  }
  async function archive() {
    if (currentUser() !== user || pending.current || creativeReadOnly || !current || !selectedUrl || !window.confirm(`归档「${current.name}」？历史版本与生产快照仍可查看。`)) return;
    pending.current = true; setBusy(true);
    try { await api.del(selectedUrl); await loadTree(); if (selectionGeneration.current === selectionEpoch && currentUser() === user) setNotice("已归档，历史记录仍可读取。"); }
    catch (error) { if (selectionGeneration.current === selectionEpoch && currentUser() === user) setError(errText(error)); }
    finally { pending.current = false; setBusy(false); }
  }
  async function saveRevision() {
    if (currentUser() !== user || pending.current || creativeReadOnly || !current || !selectedUrl || !identityKey || !detailReady || detailLoading || revisionConflict
        || (revisions[0]?.revision_no ?? 0) !== current.current_revision) return;
    const key = identityKey;
    const epoch = selectionEpoch;
    pending.current = true; setBusy(true);
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
      if (selectedIdentity.current !== key || selectionGeneration.current !== epoch || currentUser() !== user) return;
      setError(error instanceof SyntaxError ? "JSON 格式不正确，请检查后再保存。" : errText(error));
      if (error instanceof ApiError && error.status === 409) {
        setRevisionConflict(true);
        try {
          await loadTree();
          const next = await refreshIdentity(selectedUrl, effectiveQuery, key, epoch);
          if (next && selectedIdentity.current === key && selectionGeneration.current === epoch) setNotice("版本已被其他人更新。当前表单仍是旧草稿；请核对最新修订后显式加载，才可再次保存。");
        } catch (reloadError) { if (currentUser() === user) setError(`草稿已保留，最新版本读取失败。${errText(reloadError)}`); }
      }
    } finally { pending.current = false; setBusy(false); }
  }
  function fieldEditor(key: FieldKey, label: string, shape: string) {
    const value = draft[key];
    const displayedProfile = effective?.effective_profile || revisions[0]?.profile || {};
    const origin = effective ? effective.field_origins[key] : key in displayedProfile ? current?.kind : undefined;
    return <div key={key} className="min-w-0 rounded-[16px] border border-ink-200/90 bg-surface p-5"><div className="flex flex-wrap items-baseline justify-between gap-2"><label className="font-serif text-[16px] font-semibold text-ink-900">{label.replace(" JSON", "")}</label><span className="text-[12px] text-ink-500">{origin ? `${KIND_NAME[origin as Kind] || origin} · ${displayedProfile[key] === null ? "显式清空" : origin === current?.kind ? "本级设置" : "继承上级"}` : "当前未设置"}</span></div>
      <select disabled={creativeReadOnly || busy} aria-label={`${label}模式`} className={`${inputClass} mt-3`} value={value.mode} onChange={(event) => setDraft({ ...draft, [key]: { ...value, mode: event.target.value as Mode } })}><option value="inherit">继承上级 / 不设置</option><option value="override">本级设置</option><option value="clear">显式清空</option></select>
      {value.mode === "override" && (shape === "voice" ? <select aria-label={label} disabled={creativeReadOnly || busy} className={`${inputClass} mt-2`} value={value.text} onChange={(event) => setDraft({ ...draft, [key]: { ...value, text: event.target.value } })}><option value="">请选择已发布版本</option>{voices.map((voice) => <option key={voice.id} value={voice.id}>{voice.name} · v{voice.version}</option>)}</select> : shape === "text" ? <input aria-label={label} disabled={creativeReadOnly || busy} className={`${inputClass} mt-2`} value={value.text} onChange={(event) => setDraft({ ...draft, [key]: { ...value, text: event.target.value } })} /> : <textarea aria-label={label} disabled={creativeReadOnly || busy} className={`${inputClass} mt-2 min-h-28 ${shape === "json" ? "font-mono text-[12.5px]" : ""}`} value={value.text} placeholder={shape === "json" ? "{}" : "每行一项"} onChange={(event) => setDraft({ ...draft, [key]: { ...value, text: event.target.value } })} />)}
      {shape === "json" && <p className="mt-2 text-[12px] text-ink-500">结构化设置，按 JSON 填写。</p>}
    </div>;
  }
  function entityButton(entity: Entity) {
    return <button key={`${entity.kind}:${entity.id}`} disabled={busy} className="group flex w-full items-center justify-between gap-3 rounded-xl border border-ink-200/80 bg-surface px-4 py-3 text-left transition-colors hover:border-ink-400" onClick={() => selectIdentity({ kind: entity.kind, id: entity.id })}><span className="min-w-0"><span className="block text-[11.5px] text-ink-500">{KIND_NAME[entity.kind]}{entity.platform_channel ? ` · ${channels.find(channel => channel.channel === entity.platform_channel)?.label || entity.platform_channel}` : ""}</span><span className="block truncate text-[14.5px] font-medium text-ink-900">{entity.name}</span></span><span aria-hidden className="text-ink-400 transition-transform group-hover:translate-x-0.5 group-hover:text-ink-800">→</span></button>;
  }
  function parentLabel(entity: Entity) {
    if (entity.kind === "brand") return "根品牌";
    if (entity.kind === "persona") return brands.find(row => row.id === entity.brand_id)?.name || "无品牌角色";
    if (entity.kind === "account") return personas.find(row => row.id === entity.persona_id)?.name || "独立自有账号";
    return entity.scope === "persona_editorial" ? `${personas.find(row => row.id === entity.persona_id)?.name || "角色"} · 跨平台栏目` : `${accounts.find(row => row.id === entity.account_id)?.name || "账号"} · 账号栏目`;
  }
  const search = params.get("q") || "";
  const status = params.get("status") || "all";
  const filtered = entities.filter(row => row.kind === directory && row.name.toLocaleLowerCase().includes(search.toLocaleLowerCase()) && (status === "all" || row.status === status));
  const pages = Math.max(1, Math.ceil(filtered.length / 20));
  const page = Math.min(pages, Math.max(1, Math.floor(Number(params.get("page"))) || 1));
  function listParam(key: string, value: string) {
    const next = new URLSearchParams(params); next.set(key, value); if (key !== "page") next.delete("page"); navigate(next);
  }
  const related = current ? entities.filter(row => current.kind === "brand" ? row.kind === "persona" && row.brand_id === current.id : current.kind === "persona" ? (row.kind === "account" || row.scope === "persona_editorial") && row.persona_id === current.id : current.kind === "account" ? row.kind === "series" && row.account_id === current.id : false) : [];
  const displayedProfile = effective?.effective_profile || revisions[0]?.profile || {};
  const editor = ["editor", "admin"].includes(role ?? "");
  const profileTabs = [["identity", "身份"], ["expression", "表达与视觉"], ["boundaries", "观点与边界"]];

  const counts = Object.fromEntries((["persona", "account", "series", "brand"] as Kind[]).map(kind => [kind, entities.filter(row => row.kind === kind).length])) as Record<Kind, number>;
  const channelLabel = (value?: string | null) => value ? channels.find(channel => channel.channel === value)?.label || value : null;
  const visibleTabs = TABS.filter(([key]) => key !== "publisher" || account).filter(([key]) => key !== "creative" || persona);

  return <Page>
    {error && <ErrorBanner message={error} />}{notice && <Notice>{notice}</Notice>}
    {loading ? <Spinner label="读取身份目录…" /> : treeError ? <div className="space-y-3"><ErrorBanner message={treeError} /><Button variant="secondary" onClick={() => { setLoading(true); loadTree().catch(error => setError(errText(error))).finally(() => setLoading(false)); }}>重试读取目录</Button></div> : invalidSelection ? <EmptyState title="身份链接无效" hint="请返回目录选择正确的对象。" /> : !selected ? <>
      <PageHeader eyebrow="资料 · 身份" title="角色与账号" lead="角色决定说什么、怎么说；账号是角色在各平台的落脚点；栏目是长期连载。"
        actions={tab === "summary" && editor ? <>{directory === "persona" && <Button variant="secondary" onClick={() => changeView("starter")}>从起步模板创建</Button>}<Button onClick={() => changeView("new")}>新建{KIND_NAME[directory]}</Button></> : undefined}>
        <Tabs label="资料目录" value={directory} onChange={kind => listParam("directory", kind)} items={(["persona", "account", "series", "brand"] as Kind[]).map(kind => [kind, `${KIND_NAME[kind]} ${counts[kind]}`] as const)} />
      </PageHeader>
      {tab === "starter" ? <div className="space-y-5"><button className="text-[13px] text-ink-500 hover:text-ink-900" onClick={() => changeView("summary")}>← 返回角色目录</button><StarterPersonaGallery readOnly={!editor} onInitialized={async id => { await loadTree(); selectIdentity({ kind: "persona", id }); }} /></div>
      : tab === "new" ? <Section eyebrow="新建" title={`新建${KIND_NAME[directory]}`} aside={<button className="text-[13px] text-ink-500 hover:text-ink-900" onClick={() => changeView("summary")}>← 返回目录</button>}>{directory === "account" ? <ChannelAccountRegister personaId={null} channels={channels} role={role} onBusyChange={childBusy} beginMutation={beginChildMutation} parentBusy={busy} onDone={loadTree} onError={scopedError} /> : directory === "brand" ? <form className="max-w-md space-y-4" onSubmit={createEntity}><Field label="品牌名称"><input className={inputClass} value={name} onChange={event => setName(event.target.value)} required /></Field><Button type="submit" disabled={!editor || busy}>新建品牌</Button></form> : <p className="text-[14px] leading-relaxed text-ink-600">{directory === "persona" ? "角色属于某个品牌：先打开品牌，在“关联与管理”里创建；或者用“从起步模板创建”。" : "栏目属于角色或账号：先打开对应角色，在“关联与管理”里创建。"}</p>}</Section>
      : <>
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative min-w-[220px] flex-1 sm:max-w-sm"><input aria-label="搜索名称" className={`${inputClass} pl-9`} value={search} placeholder={`搜索${KIND_NAME[directory]}名称`} onChange={event => listParam("q", event.target.value)} /><span aria-hidden className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-ink-400">⌕</span></div>
          <select aria-label="状态" className={`${inputClass} !w-auto`} value={status} onChange={event => listParam("status", event.target.value)}><option value="all">全部状态</option><option value="active">使用中</option><option value="archived">已归档</option></select>
          <span className="ml-auto text-[13px] text-ink-500">共 {filtered.length} 个{KIND_NAME[directory]}</span>
        </div>
        {filtered.length === 0 ? <EmptyState title={`没有匹配的${KIND_NAME[directory]}`} hint={search ? "换个关键词试试。" : undefined} /> : <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{filtered.slice((page - 1) * 20, page * 20).map((row, index) => <button key={`${row.kind}:${row.id}`} disabled={busy} onClick={() => selectIdentity({ kind: row.kind, id: row.id })} style={{ animationDelay: `${Math.min(index, 8) * 40}ms` }} className="card group flex min-h-[188px] animate-rise flex-col p-6 text-left transition-[transform,box-shadow,border-color] duration-300 ease-studio hover:-translate-y-0.5 hover:border-ink-300 hover:shadow-lift">
          <div className="flex items-start justify-between gap-3">
            <span aria-hidden className={`grid h-11 w-11 shrink-0 place-items-center rounded-full font-serif text-[18px] ${row.status === "archived" ? "bg-ink-100 text-ink-400" : "bg-accent-50 text-accent-600"}`}>{row.name.trim().charAt(0) || "·"}</span>
            {row.status === "archived" ? <Chip>已归档</Chip> : channelLabel(row.platform_channel) ? <Chip tone="info">{channelLabel(row.platform_channel)}</Chip> : null}
          </div>
          <h2 className="mt-5 line-clamp-2 break-words font-serif text-[21px] font-semibold leading-snug text-ink-900">{row.name}</h2>
          <p className="mt-1.5 truncate text-[13px] text-ink-500">{parentLabel(row)}</p>
          <div className="mt-auto flex items-center justify-between pt-5 text-[12.5px] text-ink-500"><span>修订 v{row.current_revision}</span><span aria-hidden className="text-ink-400 transition-transform group-hover:translate-x-0.5 group-hover:text-accent-500">打开 →</span></div>
        </button>)}</div>}
        {pages > 1 && <div className="flex items-center justify-center gap-3 pt-2"><Button variant="secondary" size="sm" disabled={page <= 1} onClick={() => listParam("page", String(page - 1))}>上一页</Button><span className="text-[13px] text-ink-500">第 {page} / {pages} 页</span><Button variant="secondary" size="sm" disabled={page >= pages} onClick={() => listParam("page", String(page + 1))}>下一页</Button></div>}
      </>}
    </> : !current ? <EmptyState title="找不到或无法读取这个身份" hint="不会自动切换到其他身份。请返回目录重选。" /> : <>
      <div>
        <button className="mb-6 text-[13px] text-ink-500 transition-colors hover:text-ink-900" onClick={() => selectIdentity(null)}>← {KIND_NAME[directory]}目录</button>
        <PageHeader eyebrow={<>{KIND_NAME[current.kind]} · {parentLabel(current)}</>} title={current.name}
          actions={tab === "summary" && !creativeReadOnly ? <Button onClick={() => changeView("edit")}>编辑资料</Button> : undefined}>
          <div className="mb-6 flex flex-wrap items-center gap-2">
            {current.status === "archived" ? <Chip tone="warn">已归档 · 只能查看</Chip> : <Chip tone="good">使用中</Chip>}
            <Chip>修订 v{current.current_revision}</Chip>
            {channelLabel(current.platform_channel) && <Chip tone="info">{channelLabel(current.platform_channel)}</Chip>}
            {current.kind === "persona" && <Chip>{related.filter(row => row.kind === "account").length} 个账号</Chip>}
            {creativeReadOnly && current.status !== "archived" && <span className="text-[12.5px] text-amber-700">只读：权限未确认、读取未完成或上级已归档</span>}
          </div>
          <Tabs label="身份页面" value={tab} disabled={busy} onChange={changeView} items={visibleTabs} />
        </PageHeader>
      </div>
      {detailLoading ? <Spinner label="读取修订…" /> : !detailReady ? <div className="space-y-3"><p className="text-[14px] text-ink-700">身份资料读取失败，暂不可修改。</p><Button variant="secondary" onClick={() => refreshIdentity(selectedUrl!, effectiveQuery, identityKey!, selectionEpoch, true).catch(error => setError(errText(error)))}>重试读取</Button></div> : <div className="space-y-6">
        {tab === "summary" && <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
          <Section>
            {current.kind !== "persona" && effective && persona && <div className="mb-7"><Notice>{(() => { const own = Object.values(effective.field_origins || {}).filter(origin => origin === current.kind).length; return own ? `这里是实际生效的资料：本${KIND_NAME[current.kind]}单独设置了 ${own} 项，其余继承自角色「${persona.name}」。` : `这个${KIND_NAME[current.kind]}还没有单独设置，以下资料全部继承自角色「${persona.name}」。需要不同的定位或语气时，在“编辑资料”里单独设置。`; })()}</Notice></div>}
            <ProfileOverview profile={displayedProfile} />
          </Section>
          <aside className="space-y-6 lg:sticky lg:top-8">
            <Section eyebrow="归属与关联" title={parentLabel(current)}>
              <div className="space-y-2">{[brand, persona, account].filter((row): row is Entity => Boolean(row) && row !== current).map(row => entityButton(row))}{related.map(row => entityButton(row))}</div>
              {!related.length && ![brand, persona, account].some(row => row && row !== current) && <p className="text-[13.5px] text-ink-500">暂无直属关联资料。</p>}
            </Section>
            {current.kind === "persona" && <PersonaDiscoveryStatus personaId={current.id} revision={current.current_revision} />}
          </aside>
        </div>}
        {tab === "edit" && <div className="space-y-8">{revisionConflict && <div className="space-y-3 rounded-xl border border-amber-300 bg-amber-50 p-5 text-[14px] text-amber-900"><p>最新修订为 v{revisions[0]?.revision_no ?? "未知"}。当前输入已保留，需先核对历史再显式加载，不能继续覆盖。</p><Button variant="secondary" onClick={() => { if (!window.confirm("加载最新修订将覆盖当前表单，确认继续？")) return; const next = draftFrom(revisions[0]?.profile || {}); setDraft(next); baselineDraft.current = JSON.stringify(next); setRevisionConflict(false); setError(""); }}>加载最新修订（覆盖当前表单）</Button></div>}
          {profileTabs.map(([group, label]) => <section key={group} className="min-w-0"><h3 className="mb-4 font-serif text-[20px] font-semibold text-ink-900">{label}</h3><div className="grid min-w-0 grid-cols-1 gap-4 xl:grid-cols-2">{FIELDS.filter(field => field.tab === group).map(({ key, label, shape }) => fieldEditor(key, label, shape))}</div></section>)}
          <div className="sticky bottom-4 z-10 flex items-center justify-between gap-4 rounded-pill border border-ink-200 bg-surface/95 py-2 pl-6 pr-2 shadow-lift backdrop-blur"><span className="text-[13px] text-ink-600">保存后生成新修订，旧作品的快照不会改变。</span><Button onClick={saveRevision} disabled={creativeReadOnly || busy || revisionConflict}>保存为 v{current.current_revision + 1}</Button></div>
        </div>}
        {tab === "history" && <Section eyebrow="只读" title="修订历史">{revisions.length ? <ol className="relative space-y-3 border-l border-ink-200 pl-6">{revisions.map((revision, index) => <li key={revision.id} className="relative"><span aria-hidden className={`absolute -left-[29px] top-5 h-2.5 w-2.5 rounded-full ring-4 ring-surface ${index === 0 ? "bg-accent-500" : "bg-ink-300"}`} /><details className="group rounded-[14px] border border-ink-200/80 bg-surface"><summary className="flex cursor-pointer list-none flex-wrap items-baseline gap-x-3 gap-y-1 px-5 py-4"><span className="font-serif text-[20px] font-semibold text-ink-900">v{revision.revision_no}</span>{index === 0 && <Chip tone="accent">当前</Chip>}<span className="text-[13px] text-ink-500">{revision.created_at ? new Date(revision.created_at).toLocaleString("zh-CN", { hour12: false }) : "时间未记录"}</span><span className="ml-auto text-[12.5px] text-ink-500 group-open:hidden">展开</span></summary><div className="border-t border-ink-200/80 p-5"><ProfileOverview profile={revision.profile} /><p className="mt-4 break-all font-mono text-[11.5px] text-ink-400">校验和 {revision.checksum}</p></div></details></li>)}</ol> : <p className="text-[14px] text-ink-500">尚无画像修订。</p>}</Section>}
      {persona && (tab === "creative" || creativeVisitedKey === identityKey) && <div hidden={tab !== "creative"} className="space-y-6"><Suspense fallback={<Spinner label="读取创作配置…" />}><PersonaCreativeConfig key={`${identityKey}:${selectionEpoch}`} current={current} persona={persona} readOnly={creativeReadOnly} accountId={account?.id || null} seriesId={seriesId} revisions={revisions} effective={effective} onSaved={async () => { const key = identityKey!; if (selectedIdentity.current !== key || selectionGeneration.current !== selectionEpoch) return; await loadTree(); return refreshIdentity(selectedUrl!, effectiveQuery, key, selectionEpoch); }} onNotice={value => { if (selectedIdentity.current === identityKey && selectionGeneration.current === selectionEpoch) setNotice(value); }} onDirtyChange={value => { if (selectedIdentity.current === identityKey && selectionGeneration.current === selectionEpoch) creativeDirty.current = value; }} /></Suspense>{current.kind === "persona" && <Suspense fallback={<Spinner label="读取参考风格…" />}><PersonaReferenceStylePanel key={`style:${identityKey}:${selectionEpoch}`} personaId={persona.id} readOnly={creativeReadOnly} identityRevision={revisions[0]} onIdentityRefresh={async () => {
        const key = identityKey!;
        if (selectedIdentity.current !== key || selectionGeneration.current !== selectionEpoch) return;
        const baseline = JSON.stringify(draftFrom(revisions[0]?.profile || {}));
        await loadTree();
        const next = await refreshIdentity(selectedUrl!, effectiveQuery, key, selectionEpoch);
        if (next) {
          if (JSON.stringify(draftRef.current) !== baseline) setRevisionConflict(true);
          else { setDraft(draftFrom(next[0]?.profile || {})); baselineDraft.current = JSON.stringify(draftFrom(next[0]?.profile || {})); }
        }
      }} onDirtyChange={value => { referenceStyleDirty.current = value; }} /></Suspense>}</div>}

        {tab === "accounts" && <div className="space-y-6"><Section eyebrow="关联与管理" title={parentLabel(current)} aside={!creativeReadOnly ? <Button variant="danger" size="sm" disabled={busy} onClick={archive}>归档{KIND_NAME[current.kind]}</Button> : undefined}>
          {related.length > 0 ? <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">{related.map(row => entityButton(row))}</div> : <p className="text-[14px] text-ink-500">还没有下级资料。</p>}
          {!creativeReadOnly && current.kind !== "series" && <form className="mt-6 flex flex-wrap gap-3 border-t border-ink-200/80 pt-6" onSubmit={createEntity}><input aria-label="新子级名称" className={`${inputClass} max-w-sm`} value={name} onChange={event => setName(event.target.value)} required placeholder={`新建${current.kind === "brand" ? "角色" : current.kind === "persona" ? "账号" : "栏目"}名称`} disabled={busy} /><Button type="submit" disabled={busy}>创建{current.kind === "brand" ? "角色" : current.kind === "persona" ? "账号" : "栏目"}</Button></form>}
          <p className="mt-4 text-[12.5px] leading-relaxed text-ink-500">公开账号登记只记录公开名称和标识；平台登录与发布授权在“平台连接”。归档会保留历史。</p>
        </Section>{!creativeReadOnly && persona && <div className="grid gap-6 lg:grid-cols-2"><EditorialSeriesCreate key={`series:${identityKey}`} personaId={persona.id} onBusyChange={childBusy} beginMutation={beginChildMutation} parentBusy={busy} onDone={seriesCreated} onError={scopedError} /><ChannelAccountRegister key={`register:${identityKey}`} personaId={persona.id} channels={channels} role={role} onBusyChange={childBusy} beginMutation={beginChildMutation} parentBusy={busy} onDone={loadTree} onError={scopedError} /></div>}{current.kind === "series" && current.scope === "persona_editorial" && <SeriesTargetsPanel key={identityKey} seriesId={current.id} personaId={persona?.id ?? null} archived={creativeReadOnly} accounts={accounts.filter(row => row.persona_id === persona?.id)} channels={channels} readOnly={creativeReadOnly} onBusyChange={childBusy} beginMutation={beginChildMutation} parentBusy={busy} onChanged={loadTree} onNotice={scopedNotice} onError={scopedError} />}</div>}
        {tab === "publisher" && account && <AccountPublisherPanel key={account.id} accountId={account.id} archived={creativeReadOnly} />}
        {tab === "memory" && <MemoryPanel key={identityKey} scopeType={current.kind} scopeId={current.id} readOnly={creativeReadOnly} />}
        {!TABS.some(([key]) => key === tab) && <EmptyState title="页面不存在" hint="请使用上方入口。" />}
      </div>}
    </>}
  </Page>;
}

function registerFailure(error: unknown): string {
  if (!(error instanceof ApiError)) return "登记失败，请重试。";
  if (error.status === 403) return "只有管理员可以登记平台账号。";
  if (error.status === 409 && error.message === "platform_identity_conflict") return "这个平台标识已经登记过。归档也不会把同一个真实账号让给别的角色。";
  if (error.message === "platform_account_public_id_invalid") return "公开标识不合格。不要填写密码、AppSecret 或 token。公众号请填 wx 开头的 AppID，其他平台填账号名或 @handle。";
  return error.message || "登记失败，请重试。";
}

function EditorialSeriesCreate({ personaId, onDone, onError, onBusyChange, beginMutation, parentBusy }: {
  personaId: number; onBusyChange: (value: boolean) => void; beginMutation: () => boolean; parentBusy: boolean; onDone: (seriesId: number) => Promise<void>; onError: (message: string) => void;
}) {
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const submitting = useRef(false);
  const owner = currentUser();
  return <form onSubmit={async (event: FormEvent) => {
    event.preventDefault();
    if (submitting.current || currentUser() !== owner || !name.trim()) return;
    if (!beginMutation()) return;
    submitting.current = true; setBusy(true);
    try {
      const created = await api.post<{ id: number }>(`/content-personas/${personaId}/series`, { name: name.trim() });
      setName("");
      if (currentUser() === owner) await onDone(created.id);
    } catch (error) { onError(error instanceof ApiError ? `${error.status} · ${error.message}` : "创建失败，请重试。"); }
    finally { submitting.current = false; onBusyChange(false); setBusy(false); }
  }} className="rounded-xl border border-slate-200 bg-white p-4">
    <h4 className="text-sm font-medium">新建跨平台栏目</h4>
    <p className="mt-1 text-xs text-slate-500">属于角色的编辑栏目，可稍后绑定多个渠道账号。同名栏目不会自动合并。</p>
    <div className="mt-2 flex gap-2"><input aria-label="栏目名称" className={inputClass} required maxLength={200} value={name} onChange={(event) => setName(event.target.value)} placeholder="例如「技术拆解」" /><Button type="submit" disabled={busy || parentBusy}>{busy ? "创建中…" : "创建栏目"}</Button></div>
  </form>;
}

function ChannelAccountRegister({ personaId, channels, role, onDone, onError, onBusyChange, beginMutation, parentBusy }: {
  personaId: number | null; channels: Channel[]; role: string | null; onBusyChange: (value: boolean) => void; beginMutation: () => boolean; parentBusy: boolean; onDone: () => Promise<void>; onError: (message: string) => void;
}) {
  const [channel, setChannel] = useState(channels[0]?.channel || "");
  const [name, setName] = useState("");
  const [handle, setHandle] = useState("");
  const [busy, setBusy] = useState(false);
  const submitting = useRef(false);
  const owner = currentUser();
  const [notice, setNotice] = useState("");
  const admin = role === "admin";
  const effectiveChannel = channels.some((row) => row.channel === channel) ? channel : channels[0]?.channel || "";
  return <form onSubmit={async (event: FormEvent) => {
    event.preventDefault();
    if (!admin || submitting.current || currentUser() !== owner || !effectiveChannel) return;
    if (!beginMutation()) return;
    submitting.current = true; setBusy(true); setNotice("");
    try {
      await api.post(personaId == null ? "/content-accounts/channel-accounts" : `/content-personas/${personaId}/channel-accounts`, { name: name.trim(), platform_channel: effectiveChannel, platform_account_id: handle.trim() });
      setName(""); setHandle(""); setNotice("已登记公开账号。这还不是登录，也不是发布。");
      if (currentUser() === owner) await onDone();
    } catch (error) { onError(registerFailure(error)); }
    finally { submitting.current = false; onBusyChange(false); setBusy(false); }
  }} className="rounded-xl border border-slate-200 bg-white p-4">
    <h4 className="text-sm font-medium">登记平台公开身份</h4>
    <p className="mt-1 text-xs text-slate-500">{admin ? "只填公开名称与标识；不要填密码、AppSecret、token 或带登录信息的网址。" : "登记平台账号只限管理员。"}</p>
    <div className="mt-2 grid gap-2 sm:grid-cols-3">
      <select aria-label="平台" className={inputClass} value={effectiveChannel} disabled={!admin || busy || parentBusy} onChange={(event) => setChannel(event.target.value)}>
        {channels.map((row) => <option key={row.channel} value={row.channel}>{row.label}</option>)}
      </select>
      <input aria-label="显示名称" className={inputClass} required maxLength={200} disabled={!admin || busy || parentBusy} value={name} onChange={(event) => setName(event.target.value)} placeholder="显示名称" />
      <input aria-label="公开标识" className={inputClass} name="public-handle" autoComplete="off" spellCheck={false} required maxLength={64} disabled={!admin || busy || parentBusy} value={handle} onChange={(event) => setHandle(event.target.value)} placeholder={effectiveChannel === "wechat" ? "wx 开头 AppID" : "账号名 / @handle"} />
    </div>
    <div className="mt-2 flex items-center gap-3"><Button type="submit" disabled={!admin || busy || parentBusy}>{busy ? "登记中…" : "登记账号"}</Button>{notice && <span className="text-xs text-indigo-700">{notice}</span>}</div>
  </form>;
}

function SeriesTargetsPanel({ seriesId, personaId, archived, accounts, channels, readOnly, onChanged, onNotice, onError, onBusyChange, beginMutation, parentBusy }: {
  seriesId: number; personaId: number | null; archived: boolean;
  accounts: Entity[]; channels: Channel[]; readOnly: boolean; onBusyChange: (value: boolean) => void; beginMutation: () => boolean; parentBusy: boolean;
  onChanged: () => Promise<void>; onNotice: (message: string) => void; onError: (message: string) => void;
}) {
  const [targets, setTargets] = useState<SeriesTarget[]>([]);
  const [loading, setLoading] = useState(true);
  const [accountId, setAccountId] = useState<number | null>(accounts[0]?.id ?? null);
  const [form, setForm] = useState("");
  const [busy, setBusy] = useState(false);
  const submitting = useRef(false);
  const owner = currentUser();
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
    if (submitting.current || readOnly || archived || currentUser() !== owner) return;
    if (!beginMutation()) return;
    submitting.current = true; setBusy(true);
    try { await action(); await load(); await onChanged(); onNotice(notice); }
    catch (error) { onError(errText(error)); }
    finally { submitting.current = false; onBusyChange(false); setBusy(false); }
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
            {!readOnly && !archived && <Button size="sm" variant="secondary" disabled={busy || parentBusy} onClick={() => mutate(() => api.patch(`/content-series/${seriesId}/targets/${row.id}`, { enabled: !row.enabled, expected_version: row.version }), row.enabled ? "绑定已停用；新的投放授权会被阻断。" : "绑定已重新启用。")}>{row.enabled ? "停用" : "启用"}</Button>}
            {!readOnly && !archived && <Button size="sm" variant="danger" disabled={busy || parentBusy} onClick={() => { if (window.confirm("解除这条投放绑定？历史交付记录不受影响。")) mutate(() => api.del(`/content-series/${seriesId}/targets/${row.id}`), "绑定已解除。"); }}>解除</Button>}
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
        <Button type="submit" disabled={busy || parentBusy || accountId == null || !form}>{busy ? "绑定中…" : "绑定投放目标"}</Button>
        {personaId == null && <span className="text-xs text-slate-500">先选择所属角色。</span>}
      </form>}
      {!readOnly && !archived && eligible.length === 0 && <p className="mt-2 text-xs text-slate-500">没有可绑定的账号：先在本角色下登记带平台身份的账号。</p>}
    </>}
  </section>;
}
