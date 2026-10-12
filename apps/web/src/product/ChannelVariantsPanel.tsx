import { useEffect, useRef, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { api, ApiError } from "../api";
import { Button, ErrorBanner, StatusBadge, Spinner, inputClass } from "../components/ui";
import type { Unit } from "./project/projectTypes";
import type { SharedAsset } from "./project/types";
import CreativeIntentEditor, { creativeIntentIssue, type CreativeIntent } from "./CreativeIntentEditor";
import ChannelVariantForm, { variantBodyIssue } from "./ChannelVariantForm";

type Master = { id: number; revision_no: number; payload_schema: string; payload_hash: string; context_hash: string; readiness: { state: string; reasons: string[] } };
type Ref = Record<string, unknown>;
type Preview = { source_master_revision_id: number; source_payload_hash: string; source_context_hash: string; channel_id: string; content_form: string; payload_schema: string; payload: Record<string, unknown>; payload_hash: string; profile_hash: string; adapter_key: string; adapter_version: string; asset_refs: Ref[]; evidence_refs: Ref[]; verified_remote: false };
type Variant = { id: number; project_id: number; content_unit_id: number; variant_key: string; revision_no: number; source_master_revision_id: number; source_master_payload_hash: string; source_master_context_hash: string; channel_id: string; content_form: string; payload_schema: string; payload: Record<string, unknown>; payload_hash: string; adapter_key: string; adapter_version: string; profile_template_version_id: number; profile_hash: string; creative_intent?: CreativeIntent | null; assets: Ref[]; evidence: Ref[]; checks: { id: number; check_kind: string; status: string }[]; created_at: string | null };
type CheckProjection = { ready: boolean; drift_reasons: string[]; source_gate: { status: string; reasons: string[] }; items: { id: number | null; check_kind: string; status: string; is_current: boolean; report: { reasons?: string[] } }[] };
type VariantDiff = { from_revision_id: number | null; changed_sections: Record<string, { changed: boolean }>; structured: { id: string; changes: string[] }[] | null };
type Capability = { channel: string; content_form: string; payload_schema: string; capability: { configured: boolean; executable: boolean; verified: boolean; reason?: string; profile_version_id?: number; profile_hash?: string; adapter_key?: string; adapter_version?: string; artifact_kind?: string } };
type Target = { channel: string; form: string; label: string; source: string };
const TARGETS: Record<string, Target[]> = {
  text: [{ channel: "wechat", form: "article", label: "公众号文章", source: "text.master.v2" }, { channel: "x", form: "thread", label: "X 推串", source: "text.master.v2" }, { channel: "x", form: "single", label: "X 单条", source: "text.master.v2" }],
  graphic: [{ channel: "xiaohongshu", form: "image_note", label: "小红书图文", source: "graphic.master.v2" }],
  video: [{ channel: "douyin", form: "spoken_script", label: "抖音口播脚本", source: "video.master.v2" }],
};
function message(cause: unknown) { return cause instanceof ApiError ? cause.status === 409 ? "409 · 版本、来源或上下文已变化；本地正文、意图和预览已保留，请核对后重新读取。" : `${cause.status} · ${cause.message}` : cause instanceof Error ? cause.message : "请求失败，请重试。"; }
function keyOf(target: Target) { return `${target.channel}.${target.form}.primary`; }
function contentRows(variant: { payload_schema: string; payload: Record<string, unknown> }) {
  const payload = variant.payload;
  if (variant.payload_schema === "x.single.v1") return [{ id: "single", text: String(payload.text || "") }];
  const key = variant.payload_schema === "wechat.article.v1" ? "blocks" : variant.payload_schema === "x.thread.v1" ? "posts" : variant.payload_schema === "xiaohongshu.image_note.v1" ? "cards" : "scenes";
  return ((payload[key] as Ref[] | undefined) || []).map((row) => ({ id: String(row.id), text: row.kind === "image"
    ? `正文图片 · Block ${String(row.id)} · Slot ${String(row.image_ref_key)} · 图注：${String(row.text || "未指定")} · Alt：${String(row.alt_text || "未指定")}`
    : String(row.text || row.caption || row.script || "") }));
}

export default function ChannelVariantsPanel({ projectId, unit, readOnly: workspaceReadOnly, workflowDirty }: { projectId: number; unit: Unit; readOnly: boolean; workflowDirty: boolean }) {
  const [serverArchived, setServerArchived] = useState(false);
  const readOnly = workspaceReadOnly || unit.status === "archived" || serverArchived;
  const location = useLocation();
  const base = `/content-projects/${projectId}/units/${unit.id}`;
  const requestScope = useRef(base);
  requestScope.current = base;
  const targets = TARGETS[unit.modality] || [];
  const [targetKey, setTargetKey] = useState(keyOf(targets[0]));
  const target = targets.find((item) => keyOf(item) === targetKey) || targets[0];
  const [master, setMaster] = useState<Master | null>(null);
  const [capabilities, setCapabilities] = useState<Capability[]>([]);
  const [sharedAssets, setSharedAssets] = useState<SharedAsset[]>([]);
  const [coverId, setCoverId] = useState("");
  const [history, setHistory] = useState<Variant[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [preview, setPreview] = useState<Preview | null>(null);
  const [previewIntent, setPreviewIntent] = useState<CreativeIntent | null>(null);
  const [previewIntentDirty, setPreviewIntentDirty] = useState(false);
  const [intentDraft, setIntentDraft] = useState<CreativeIntent | null>(null);
  const [intentDirty, setIntentDirty] = useState(false);
  const [bodyDraft, setBodyDraft] = useState<Record<string, unknown> | null>(null);
  const [bodyDirty, setBodyDirty] = useState(false);
  const [conflict, setConflict] = useState(false);
  const [checks, setChecks] = useState<CheckProjection | null>(null);
  const [diff, setDiff] = useState<VariantDiff | null>(null);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const selected = history.find((row) => row.id === selectedId) || null;
  const current = history.filter((row) => row.variant_key === targetKey).sort((a, b) => b.revision_no - a.revision_no)[0] || null;
  const historical = !!selected && selected.id !== current?.id;
  const sourceReady = !!master && master.payload_schema === target.source && master.readiness.state === "current";
  const capability = capabilities.find((row) => row.channel === target.channel && row.content_form === target.form)?.capability;
  const dirty = bodyDirty || intentDirty || !!preview;
  const bodyIssue = selected && bodyDraft ? variantBodyIssue(selected.payload_schema, bodyDraft) : "";
  const intentIssue = intentDirty ? creativeIntentIssue(intentDraft) : "";
  const previewIntentIssue = previewIntentDirty ? creativeIntentIssue(previewIntent) : "";
  const exactSource = !!selected && !!master && selected.source_master_revision_id === master.id
    && selected.project_id === projectId && selected.content_unit_id === unit.id
    && selected.channel_id === target.channel && selected.content_form === target.form
    && selected.source_master_payload_hash === master.payload_hash && selected.source_master_context_hash === master.context_hash;
  function matchesProfile(variant: Variant, available: Capability[]) {
    const row = available.find((item) => item.channel === variant.channel_id && item.content_form === variant.content_form);
    return !!row?.capability.executable && row.payload_schema === variant.payload_schema
      && row.capability.profile_version_id === variant.profile_template_version_id && row.capability.profile_hash === variant.profile_hash
      && row.capability.adapter_key === variant.adapter_key && row.capability.adapter_version === variant.adapter_version;
  }
  const intentReadOnly = readOnly || busy || conflict || historical || !!preview || !sourceReady || !exactSource
    || !selected || !matchesProfile(selected, capabilities) || !checks || checks.drift_reasons.length > 0;
  function discardAllowed() { return !dirty || window.confirm("继续会丢弃未保存的渠道正文、创作意图或预览，继续？"); }
  function selectVariant(variant: Variant | null, resetDraft = false) {
    if (variant && variant.id === selectedId && !resetDraft) return;
    setSelectedId(variant?.id ?? null); setIntentDraft(variant?.creative_intent ?? null); setIntentDirty(false);
    setBodyDraft(variant?.payload ?? null); setBodyDirty(false); setConflict(false);
    if (!variant || variant.id !== selectedId) { setChecks(null); setDiff(null); }
  }
  function discardPreview() { setPreview(null); setPreviewIntent(null); setPreviewIntentDirty(false); setCoverId(""); }
  useEffect(() => {
    if (!dirty) return;
    const warn = (event: BeforeUnloadEvent) => { event.preventDefault(); event.returnValue = ""; };
    const guardLink = (event: MouseEvent) => {
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      const anchor = (event.target as Element | null)?.closest?.("a[href]");
      if (!anchor || anchor.getAttribute("target") === "_blank") return;
      const next = new URL((anchor as HTMLAnchorElement).href);
      if (next.origin === window.location.origin && next.pathname === window.location.pathname && next.search === window.location.search) return;
      if (!window.confirm("离开会丢弃未保存的渠道正文、创作意图或预览，继续？")) { event.preventDefault(); event.stopPropagation(); }
    };
    const navigation = (window as Window & { navigation?: EventTarget }).navigation;
    const guardHistory = (raw: Event) => {
      const event = raw as Event & { navigationType: string; destination: { sameDocument: boolean; url: string } };
      if (event.navigationType !== "traverse" || !event.destination.sameDocument || !event.cancelable) return;
      const next = new URL(event.destination.url);
      if (next.pathname === window.location.pathname && next.search === window.location.search) return;
      // popstate fires after the router has discarded the draft; cancel before traversal.
      if (!window.confirm("离开会丢弃未保存的渠道正文、创作意图或预览，继续？")) event.preventDefault();
    };
    window.addEventListener("beforeunload", warn); document.addEventListener("click", guardLink, true); navigation?.addEventListener("navigate", guardHistory);
    return () => { window.removeEventListener("beforeunload", warn); document.removeEventListener("click", guardLink, true); navigation?.removeEventListener("navigate", guardHistory); };
  }, [dirty, location.key]);

  async function reload() {
    const [masters, variants, available, assets] = await Promise.all([
      api.get<{ items: Master[] }>(`${base}/master-revisions`),
      api.get<{ items: Variant[] }>(`${base}/channel-variants?limit=100`),
      api.get<{ items: Capability[]; archived: boolean }>(`${base}/channel-variants/capabilities`),
      api.get<SharedAsset[]>(`/content-projects/${projectId}/shared-assets`),
    ]);
    if (requestScope.current === base) {
      setMaster(masters.items[0] || null); setHistory(variants.items); setCapabilities(available.items); setSharedAssets(assets); setServerArchived(available.archived);
    }
    return variants.items;
  }
  useEffect(() => {
    let active = true;
    setLoading(true);
    reload().catch((cause) => { if (active) setError(message(cause)); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [base]);
  useEffect(() => { discardPreview(); selectVariant(null); setNotice(""); setError(""); setBusy(false); }, [base, targetKey]);
  useEffect(() => {
    if (!selected) { setChecks(null); setDiff(null); return; }
    let active = true;
    api.get<CheckProjection>(`${base}/channel-variants/${selected.id}/checks`).then((next) => { if (active) setChecks(next); }).catch((cause) => { if (active) setError(message(cause)); });
    api.get<VariantDiff>(`${base}/channel-variants/${selected.id}/diff`).then((next) => { if (active) setDiff(next); }).catch((cause) => { if (active) setError(message(cause)); });
    return () => { active = false; };
  }, [base, selectedId, history]);
  async function run(action: () => Promise<void>) {
    setBusy(true); setError(""); setNotice("");
    try { await action(); }
    catch (cause) { if (requestScope.current === base) { if (cause instanceof ApiError && cause.status === 409) setConflict(true); setError(message(cause)); } }
    finally { if (requestScope.current === base) setBusy(false); }
  }
  async function adapt() {
    if (readOnly || busy || historical || !master || !target || !discardAllowed()) return;
    await run(async () => {
      const next = await api.post<Preview>(`${base}/channel-variants/adapt-preview`, {
        source_master_revision_id: master.id, expected_source_payload_hash: master.payload_hash,
        expected_source_context_hash: master.context_hash, channel_id: target.channel, content_form: target.form,
      });
      if (requestScope.current !== base) return;
      setPreview(next); setCoverId(""); setIntentDraft(selected?.creative_intent ?? null); setIntentDirty(false);
      setBodyDraft(selected?.payload ?? null); setBodyDirty(false); setConflict(false);
      setPreviewIntent(current?.creative_intent ?? null); setPreviewIntentDirty(false);
      setNotice("仅生成预览，尚未保存渠道变体，也没有远端发布。");
    });
  }
  async function save() {
    if (readOnly || busy || conflict || historical || !sourceReady || !capability?.executable || !preview || !target) return;
    await run(async () => {
      if (previewIntentIssue) throw new Error(previewIntentIssue);
      const cover = sharedAssets.find((asset) => String(asset.material_revision_id) === coverId);
      const assetRefs = target.channel === "wechat" && target.form === "article" && !preview.asset_refs.some((row) => row.role === "cover") && cover
        ? [{ material_revision_id: cover.material_revision_id, content_hash_snapshot: cover.content_hash, role: "cover", slot_key: "cover", sort_order: 0, placement: { usage: "cover" } }, ...preview.asset_refs.map((ref, index) => ({ ...ref, sort_order: index + 1 }))]
        : preview.asset_refs;
      const saved = await api.post<Variant>(`${base}/channel-variants`, {
        variant_key: keyOf(target), expected_revision: current?.revision_no || 0,
        source_master_revision_id: preview.source_master_revision_id,
        expected_source_payload_hash: preview.source_payload_hash,
        expected_source_context_hash: preview.source_context_hash,
        expected_profile_hash: preview.profile_hash,
        channel_id: target.channel, content_form: target.form,
        idempotency_key: crypto.randomUUID(), source_kind: "deterministic_adapt",
        payload: preview.payload, asset_refs: assetRefs, evidence_refs: preview.evidence_refs,
        ...(previewIntentDirty ? { creative_intent: previewIntent } : {}),
      });
      if (requestScope.current !== base) return;
      setHistory(rows => [saved, ...rows.filter(row => row.id !== saved.id)]); selectVariant(saved, true); discardPreview();
      try { await reload(); } catch (cause) { setError(`新修订已保存，重新读取失败：${message(cause)}`); }
      setNotice("已追加保存 Variant 修订；来源 Master 和 Workflow 草稿均未修改。");
    });
  }
  async function saveEdit() {
    if (intentReadOnly || !selected || !bodyDraft || !(bodyDirty || intentDirty) || bodyIssue || intentIssue) return;
    await run(async () => {
      const [freshChecks, freshCapabilities] = await Promise.all([
        api.get<CheckProjection>(`${base}/channel-variants/${selected.id}/checks`),
        api.get<{ items: Capability[]; archived: boolean }>(`${base}/channel-variants/capabilities`),
      ]);
      if (requestScope.current !== base) return;
      setChecks(freshChecks); setCapabilities(freshCapabilities.items); setServerArchived(freshCapabilities.archived);
      if (freshCapabilities.archived || freshChecks.drift_reasons.length || !matchesProfile(selected, freshCapabilities.items)) throw new ApiError(409, "Variant 来源或 Profile 已变化");
      const saved = await api.post<Variant>(`${base}/channel-variants`, {
        variant_key: selected.variant_key, expected_revision: selected.revision_no,
        source_master_revision_id: selected.source_master_revision_id,
        expected_source_payload_hash: selected.source_master_payload_hash,
        expected_source_context_hash: selected.source_master_context_hash,
        expected_profile_hash: selected.profile_hash,
        channel_id: selected.channel_id, content_form: selected.content_form,
        idempotency_key: crypto.randomUUID(), source_kind: "manual_edit",
        payload: bodyDraft, creative_intent: intentDraft,
        asset_refs: selected.assets.map((ref) => ({ material_revision_id: ref.material_revision_id, content_hash_snapshot: ref.content_hash, role: ref.role, slot_key: ref.slot_key, sort_order: ref.sort_order, placement: ref.placement })),
        evidence_refs: selected.evidence.map((ref) => ({ fact_pack_item_id: ref.fact_pack_item_id, snapshot_checksum: ref.snapshot_checksum, role: ref.role, content_locator_json: ref.locator, sort_order: ref.sort_order })),
      });
      if (requestScope.current !== base) return;
      setHistory(rows => [saved, ...rows.filter(row => row.id !== saved.id)]); selectVariant(saved, true);
      try { await reload(); } catch (cause) { setError(`新修订已保存，重新读取失败：${message(cause)}`); }
      setNotice("已将渠道正文与创作意图一起保存为新修订；来源 Master、其他渠道和精确引用均保留。");
    });
  }
  async function check() {
    if (readOnly || busy || historical || dirty || !selected) return;
    await run(async () => {
      setChecks(await api.post<CheckProjection>(`${base}/channel-variants/${selected.id}/checks`, {}));
      setNotice("已保存当前检查；历史检查没有被覆盖。");
    });
  }
  async function freeze() {
    if (readOnly || busy || historical || dirty || !selected) return;
    if (workflowDirty) { setError("请先保存或放弃未保存的 Workflow 草稿，再冻结并进入审核。"); return; }
    await run(async () => {
      const candidate = await api.post<{ id: number }>(`${base}/candidates/freeze`, {
        channel_variant_revision_id: selected.id, expected_payload_hash: selected.payload_hash,
      });
      setNotice(`已冻结 Candidate v5 #${candidate.id}，尚未审批。`);
      window.location.assign(`/review?project=${projectId}&unit=${unit.id}&candidate=${candidate.id}`);
    });
  }
  return <section className="mb-5 rounded-2xl border border-slate-200 bg-white p-5" aria-label="Channel Variants">
    <div className="flex flex-wrap items-center justify-between gap-3"><div><h2 className="text-lg font-semibold">渠道变体</h2><p className="mt-1 text-xs text-slate-500">仅从已保存的当前 Master 适配；预览不写入，保存追加新版本，远端发布未验证。{dirty ? " · 有未保存修改" : ""}</p></div><Button size="sm" variant="secondary" disabled={busy} onClick={() => { if (discardAllowed()) run(async () => { const rows = await reload(); discardPreview(); selectVariant(rows.filter((row) => row.variant_key === targetKey).sort((a, b) => b.revision_no - a.revision_no)[0] || null, true); setNotice("已重新读取当前 Master 和 Variant。"); }); }}>重新读取</Button></div>
    {loading ? <div className="mt-4"><Spinner label="读取渠道变体…" /></div> : <div className="mt-4 space-y-4">
      {error && <ErrorBanner message={error} />}{notice && <p role="status" className="rounded-lg bg-emerald-50 p-3 text-sm text-emerald-800">{notice}</p>}
      <div className="grid gap-3 sm:grid-cols-2"><label className="text-sm">目标渠道与形态<select className={`${inputClass} mt-1`} value={targetKey} disabled={busy} onChange={(event) => { if (discardAllowed()) setTargetKey(event.target.value); }}>{targets.map((item) => <option key={keyOf(item)} value={keyOf(item)}>{item.label} · {item.channel}/{item.form}</option>)}</select></label><div className="rounded-lg bg-slate-50 p-3 text-xs">来源 Master：{master ? `#${master.id} · v${master.revision_no} · ${master.payload_schema}` : "尚无 Master"}<br />{sourceReady ? "当前 v2 来源可请求适配预览" : `不可适配：${master?.readiness.reasons.join("、") || "须先保存来源 v2 Master；历史 v1 要显式升级"}`}</div></div>
      <p className={`rounded-lg p-3 text-xs ${capability?.executable ? "bg-emerald-50 text-emerald-800" : "bg-amber-50 text-amber-800"}`}>目标能力：{capability?.executable ? "本地适配可执行" : `不可执行 · ${capability?.reason || "未验证"}`} · Profile #{capability?.profile_version_id ?? "未发布"} · Adapter {capability?.adapter_key || "未注册"}@{capability?.adapter_version || "-"} · 远端发布未验证</p>
      <div className="flex flex-wrap gap-2"><Button disabled={readOnly || busy || historical || !sourceReady || !capability?.executable} onClick={adapt}>生成确定性预览</Button>{preview && <Button disabled={readOnly || busy || conflict || historical || !!previewIntentIssue || !sourceReady || !capability?.executable} onClick={save}>明确接受并保存新 Variant</Button>}{preview && <Button variant="secondary" disabled={busy} onClick={() => { if (discardAllowed()) discardPreview(); }}>丢弃预览</Button>}</div>
      {preview && <div className="rounded-lg border border-indigo-200 p-4"><h3 className="font-semibold">未保存预览 · {preview.payload_schema}</h3><p className="mt-1 break-all text-xs text-slate-500">来源 #{preview.source_master_revision_id} · Adapter {preview.adapter_key}@{preview.adapter_version} · Profile {preview.profile_hash.slice(0, 12)} · 素材 {preview.asset_refs.length} · 证据 {preview.evidence_refs.length}</p><div className="mt-3 space-y-2">{contentRows(preview).map((row) => <p key={row.id} className="whitespace-pre-wrap rounded bg-slate-50 p-2 text-sm">{row.text}</p>)}</div>{preview.payload_schema === "wechat.article.v1" && !preview.asset_refs.some((row) => row.role === "cover") && <label className="mt-3 block text-sm">公众号封面素材版本<select className={`${inputClass} mt-1`} value={coverId} onChange={(event) => setCoverId(event.target.value)} disabled={readOnly || busy}><option value="">选择当前项目中允许公开的图片版本</option>{sharedAssets.filter((asset) => asset.kind === "image" && asset.public_use_allowed).map((asset) => <option key={asset.key} value={asset.material_revision_id}>{asset.title || "项目图片"} · Revision #{asset.material_revision_id}</option>)}</select><span className="mt-1 block text-xs text-slate-500">仅绑定精确 MaterialRevision；保存时服务端重新验证项目可见性、字节哈希及公开权利。</span></label>}<p className="mt-2 text-xs text-amber-700">预览不会更新 Master、不会自动冻结 Candidate，也不等于平台已发布。</p></div>}
      {preview && <CreativeIntentEditor label="Variant 预览创作意图" value={previewIntent} readOnly={readOnly || busy} onChange={(value) => { setPreviewIntent(value); setPreviewIntentDirty(true); setNotice(""); }} />}
      {preview?.payload_schema === "wechat.article.v1" && !preview.asset_refs.some(ref => ref.role === "cover") && <Button size="sm" variant="secondary" disabled={busy} onClick={() => run(async () => {
        const assets = await api.get<SharedAsset[]>(`/content-projects/${projectId}/shared-assets`);
        if (requestScope.current !== base) return;
        setSharedAssets(assets); setNotice("已刷新项目素材；请明确选择封面版本后保存，现有引用和本地草稿均保留。");
      })}>刷新项目素材</Button>}
      <div><h3 className="font-semibold">不可变版本历史</h3><div className="mt-2 flex flex-wrap gap-2">{history.filter((row) => row.variant_key === targetKey).map((row) => <Button key={row.id} size="sm" disabled={busy} variant={selectedId === row.id ? "primary" : "secondary"} onClick={() => { if (discardAllowed()) { discardPreview(); selectVariant(row, true); setNotice(""); } }}>#{row.id} · v{row.revision_no}{row.id === current?.id ? " · 当前" : " · 历史"}</Button>)}</div>{!current && <p className="mt-2 text-sm text-slate-500">此目标尚未保存 Variant。</p>}</div>
      {selected && <div className="space-y-3 rounded-lg border border-slate-200 p-4"><div className="flex flex-wrap items-center justify-between gap-2"><h3 className="font-semibold">Variant #{selected.id} · {selected.payload_schema}</h3><StatusBadge status={historical ? "stale" : checks?.ready ? "ready" : checks?.drift_reasons.length ? "stale" : "blocked"} /></div><p className="break-all text-xs text-slate-500">来源 Master #{selected.source_master_revision_id} · Payload {selected.payload_hash} · Profile {selected.profile_hash} · Adapter {selected.adapter_key}@{selected.adapter_version}</p><div className="space-y-2">{contentRows(selected).map((row) => <p key={row.id} className="whitespace-pre-wrap rounded bg-slate-50 p-2 text-sm">{row.text}</p>)}</div><details className="text-xs text-slate-600"><summary className="cursor-pointer">精确素材 {selected.assets.length} · 证据 {selected.evidence.length} · 渲染检查</summary><div className="mt-2 space-y-1">{selected.assets.map((row, index) => <p key={index}>MaterialRevision #{String(row.material_revision_id)} · {String(row.role)} / {String(row.slot_key || "-")} · {String(row.content_hash)}</p>)}{selected.evidence.map((row, index) => <p key={index}>FactPackItem #{String(row.fact_pack_item_id)} · checksum {String(row.snapshot_checksum)} · locator {JSON.stringify(row.locator)}</p>)}<p>render：{checks?.items.find((row) => row.check_kind === "variant_render")?.status || "本形态不要求单独渲染检查"}</p></div></details>{historical && <p className="text-sm text-amber-800">历史 Variant 只读；不能重跑检查或冻结。</p>}
        {checks && <div><p className="text-sm">来源：{checks.source_gate.status} · {checks.source_gate.reasons.join("、") || "无异常"}</p>{checks.drift_reasons.length > 0 && <p className="text-xs text-amber-700">漂移：{checks.drift_reasons.join("、")}</p>}<div className="mt-2 flex flex-wrap gap-2">{checks.items.map((row) => <span key={row.check_kind} className="rounded bg-slate-50 p-2 text-xs">{row.check_kind} · {row.status}{row.id ? ` #${row.id}` : " · 未运行"}</span>)}</div></div>}
        {diff && <div className="text-xs text-slate-600"><p>相对版本：{diff.from_revision_id ? `#${diff.from_revision_id}` : "首次修订"}</p><p>变化区段：{Object.entries(diff.changed_sections).filter(([, value]) => value.changed).map(([key]) => key).join("、") || "无"}</p>{diff.structured?.map((row) => <p key={row.id}>{row.id} · {row.changes.join("/")}</p>)}</div>}
        {bodyDraft && <ChannelVariantForm schema={selected.payload_schema} value={bodyDraft} readOnly={intentReadOnly} onChange={value => { setBodyDraft(value); setBodyDirty(true); setNotice(""); }} />}
        <CreativeIntentEditor label="Variant 创作意图" value={intentDraft} onChange={(value) => { setIntentDraft(value); setIntentDirty(true); setNotice(""); }} readOnly={intentReadOnly} />
        <Button disabled={intentReadOnly || !(bodyDirty || intentDirty) || !!bodyIssue || !!intentIssue} onClick={saveEdit}>保存渠道正文与创作意图为新修订</Button>
        {(bodyDirty || intentDirty) && <p className="text-xs text-amber-700">渠道正文或创作意图尚未保存；保存会原子追加当前 Variant 子修订。</p>}
        {intentReadOnly && !busy && !preview && !historical && <p className="text-xs text-amber-700">当前正文与创作意图只读：请核对权限、来源、Profile 和当前版本；本地未保存修改会保留。</p>}
        {workflowDirty && <p className="text-sm text-amber-800">Workflow 有未保存修改；先保存或放弃后才能冻结跳转，渠道预览仍只读取已保存 Master。</p>}
        <div className="flex flex-wrap gap-2"><Button variant="secondary" disabled={readOnly || busy || historical || dirty || !sourceReady} onClick={check}>运行 Variant 检查</Button><Button disabled={readOnly || busy || historical || dirty || workflowDirty || !checks?.ready} onClick={freeze}>冻结 Candidate v5</Button>{workflowDirty ? <span className="self-center text-sm text-slate-500">保存 Workflow 后可进入审核</span> : <Link className="self-center text-sm text-indigo-700 underline" to={`/review?project=${projectId}&unit=${unit.id}`}>进入审核</Link>}</div>
      </div>}
    </div>}
  </section>;
}
