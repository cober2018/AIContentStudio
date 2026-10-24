import { useEffect, useMemo, useRef, useState } from "react";
import { api, ApiError } from "../api";
import { Button, Chip, ErrorBanner, Field, Notice, Section, Segmented, Stat, inputClass } from "../components/ui";
import { CreativeProfile, refName, useNames } from "./IdentityProfileView";
import { capabilityApi, type CapabilityArtifact, type InstalledSkill } from "./capabilityMemoryTypes";
import { TypedStageField } from "./StageContractControls";
import ProductionStageControls from "./ProductionStageControls";
import VoicePresetPicker, { type VoicePresetOption } from "./VoicePresetPicker";

type Kind = "brand" | "persona" | "account" | "series";
type Entity = { kind: Kind; id: number; name: string; status: string; current_revision: number };
type Revision = { revision_no: number; profile: Record<string, any> };
type Effective = { effective_profile: Record<string, any>; creative_profile_origins?: Record<string, string>; revision_ids?: Record<string, number | null> };
type Catalog = { production_stages?: { id: string; title: string; order: number; modalities: string[] }[]; skills: any[]; style_presets: any[]; quality_profiles: any[]; starter_personas: any[] };
type VoicePreset = VoicePresetOption;
type Modality = "text" | "graphic" | "audio" | "video";
type Mode = "inherit" | "override" | "clear";
type SaveReceipt = { expectedRevision: number; profile: Record<string, any>; confirmed: boolean; modality: Modality; draft: any; editVersion: number };
const MODALITIES: { key: Modality; label: string }[] = [
  { key: "text", label: "文字" }, { key: "graphic", label: "图文" },
  { key: "audio", label: "音频" }, { key: "video", label: "视频" },
];
const FIELDS: Record<Modality, string> = {
  text: "text_creative_profile", graphic: "graphic_creative_profile",
  audio: "audio_creative_profile", video: "video_creative_profile",
};

function errorText(error: unknown) {
  return error instanceof ApiError ? `${error.status} · ${error.message}` : "创作配置读取失败。";
}

function stableJson(value: any): string {
  function sorted(item: any): any {
    if (Array.isArray(item)) return item.map(sorted);
    if (item && typeof item === "object") return Object.fromEntries(Object.keys(item).sort().map(key => [key, sorted(item[key])]));
    return item;
  }
  return JSON.stringify(sorted(value));
}

function rebaseDraft(before: any, draft: any, latest: any): any {
  if (stableJson(before) === stableJson(draft)) return structuredClone(latest);
  if (before && draft && latest && typeof before === "object" && typeof draft === "object" && typeof latest === "object"
      && !Array.isArray(before) && !Array.isArray(draft) && !Array.isArray(latest)) {
    const next = { ...latest };
    for (const key of new Set([...Object.keys(before), ...Object.keys(draft)])) {
      if (stableJson(before[key]) === stableJson(draft[key])) continue;
      if (!(key in draft)) delete next[key];
      else next[key] = rebaseDraft(before[key], draft[key], latest[key]);
    }
    return next;
  }
  return structuredClone(draft);
}

function initialDraft(modality: Modality, direct: Record<string, any>, effective: Record<string, any>) {
  const field = FIELDS[modality];
  const value = direct[field] ?? effective[field];
  return { mode: direct[field] === null ? "clear" as Mode : direct[field] ? "override" as Mode : "inherit" as Mode,
    profile: value ? JSON.parse(JSON.stringify(value)) : {
      schema: `persona.creative.${modality}.v1`, mode: "auto", skill_ref: "", style_preset_ref: "", quality_profile_ref: "",
      capability: modality === "graphic" ? "image_generation" : modality === "audio" ? "tts" : "chat",
      model_binding: null, model_chain: [], capability_memory_revision_ids: [], installed_skill_refs: [], parameters: {}, stage_instruction: null, provenance: {},
    } };
}

export default function PersonaCreativeConfig({ current, persona, readOnly, accountId, seriesId, revisions, effective, onSaved, onNotice, onDirtyChange }: {
  current: Entity; persona: Entity | null; accountId: number | null; seriesId: number | null;
  revisions: Revision[]; effective: Effective | null; onSaved: () => Promise<Revision[] | undefined>; onNotice: (value: string) => void;
  onDirtyChange: (value: boolean) => void;
  readOnly: boolean;
}) {
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [voiceCatalog, setVoiceCatalog] = useState<VoicePreset[]>([]);
  const names = useNames();
  const [audioAdvanced, setAudioAdvanced] = useState(false);
  const [modality, setModality] = useState<Modality>("text");
  const [drafts, setDrafts] = useState<Record<Modality, any>>({} as Record<Modality, any>);
  const [preview, setPreview] = useState<any>(null);
  const [previewFingerprint, setPreviewFingerprint] = useState("");
  const [confirmDiff, setConfirmDiff] = useState(false);
  const [methods, setMethods] = useState<CapabilityArtifact[]>([]);
  const [installed, setInstalled] = useState<InstalledSkill[]>([]);
  const [methodsLoaded, setMethodsLoaded] = useState(false);
  const [methodsBusy, setMethodsBusy] = useState(false);
  const [methodsTruncated, setMethodsTruncated] = useState(false);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [pendingSave, setPendingSave] = useState<SaveReceipt | null>(null);
  const baselines = useRef<Record<Modality, any>>({} as Record<Modality, any>);
  const editVersions = useRef<Record<Modality, number>>({ text: 0, graphic: 0, audio: 0, video: 0 });
  const rebasedVersions = useRef<Record<Modality, number>>({ text: 0, graphic: 0, audio: 0, video: 0 });
  const direct = revisions[0]?.profile || {};
  const effectiveProfile = effective?.effective_profile || {};
  const effectiveCreative = effectiveProfile[FIELDS[modality]];
  const effectiveOrigin = effective?.creative_profile_origins?.[FIELDS[modality]];
  const effectiveRevisionId = effectiveOrigin ? effective?.revision_ids?.[effectiveOrigin] : null;
  const readonly = readOnly || current.status === "archived";

  useEffect(() => {
    api.get<Catalog>("/content-identities/creative-catalog").then(setCatalog).catch((e) => setError(errorText(e)));
    api.get<{ voice_catalog?: VoicePreset[] }>("/settings/model-capabilities").then((value) => setVoiceCatalog(value.voice_catalog || [])).catch(() => setVoiceCatalog([]));
  }, []);
  useEffect(() => {
    if (!effective) return;
    const previousBaselines = baselines.current;
    const nextBaselines = Object.fromEntries(MODALITIES.map(({ key }) => [key, initialDraft(key, direct, effectiveProfile)])) as Record<Modality, any>;
    setDrafts(previous => Object.fromEntries(MODALITIES.map(({ key }) => [key,
      previous[key] && (editVersions.current[key] !== rebasedVersions.current[key]
        || stableJson(previous[key]) !== stableJson(previousBaselines[key]))
        ? rebaseDraft(previousBaselines[key], previous[key], nextBaselines[key]) : nextBaselines[key],
    ])) as Record<Modality, any>);
    baselines.current = nextBaselines;
  }, [revisions, effective]);
  const dirty = MODALITIES.some(({ key }) => drafts[key]
    && stableJson(drafts[key]) !== stableJson(baselines.current[key]));
  useEffect(() => { onDirtyChange(dirty || pendingSave !== null); }, [dirty, pendingSave, onDirtyChange]);

  const draft = drafts[modality] || initialDraft(modality, direct, effectiveProfile);
  const modalityDirty = stableJson(draft) !== stableJson(baselines.current[modality]);
  const fingerprint = JSON.stringify([current.kind, current.id, current.current_revision, modality, draft]);
  const currentFingerprint = useRef(fingerprint);
  currentFingerprint.current = fingerprint;
  const shownPreview = previewFingerprint === fingerprint ? preview : null;
  useEffect(() => { setConfirmDiff(false); }, [fingerprint]);
  const resourceOptions = useMemo(() => ({
    skills: (catalog?.skills || []).filter((item) => item.modality === modality),
    presets: (catalog?.style_presets || []).filter((item) => item.config?.modality === (modality === "video" ? "graphic" : modality)),
    quality: (catalog?.quality_profiles || []).filter((item) => item.ref?.includes(`quality.${modality === "graphic" ? "graphic" : modality === "audio" ? "audio" : "text"}.`)),
  }), [catalog, modality]);
  const selectedSkill = resourceOptions.skills.find(item => item.ref === draft.profile.skill_ref);
  const profileBefore = direct[FIELDS[modality]];
  const profileAfter = draft.mode === "inherit" ? undefined : draft.mode === "clear" ? null : draft.profile;
  const changedFields = draft.mode !== "override" ? [draft.mode === "clear" ? "显式清空" : "移除本级覆盖"]
    : Array.from(new Set([...Object.keys(profileBefore || {}), ...Object.keys(profileAfter || {})]))
      .filter(key => JSON.stringify(profileBefore?.[key]) !== JSON.stringify(profileAfter?.[key]));
  const matchingMethods = methods.filter(item => ["prompt_skill", "recipe"].includes(item.kind)
    && ["saved", "pinned"].includes(item.status)
    && (item.scope_type === "owner" || (item.scope_type === "persona" && item.scope.id === persona?.id)
      || (item.scope_type === "account" && item.scope.id === accountId)
      || (item.scope_type === "series" && item.scope.id === seriesId)));

  function markEdited() {
    if (readonly) return false;
    editVersions.current[modality] += 1;
    onDirtyChange(true);
    return true;
  }
  function updateProfile(key: string, value: any) {
    const parameterFields = key === "skill_ref" ? Object.keys(resourceOptions.skills.find(item => item.ref === value)?.parameter_schema?.properties || {}) : [];
    if (key === "skill_ref" && ["voice", "rate"].some(field => field in (draft.profile.parameters || {}) && !parameterFields.includes(field))) {
      setError("此方法不接收现有音色或语速参数。请在作品阶段试用口播/声音方向方法；原声音配置保留。");
      return;
    }
    if (!markEdited()) return;
    setPreview(null);
    const reset = key === "mode" && value !== "composed" ? { model_chain: [], capability_memory_revision_ids: [], installed_skill_refs: [] }
      : key === "skill_ref" ? { parameters: Object.fromEntries(Object.entries(draft.profile.parameters || {}).filter(([field]) => parameterFields.includes(field))) } : {};
    setDrafts(current => {
      const currentDraft = current[modality] || draft;
      return { ...current, [modality]: { ...currentDraft, profile: { ...currentDraft.profile, ...reset,
        ...(key === "mode" && value === "auto" ? { model_binding: null } : {}), [key]: value } } };
    });
  }
  function updateBinding(key: string, value: string) {
    updateProfile("model_binding", { ...(draft.profile.model_binding || { provider: "", model: "", profile: "" }), [key]: value });
  }
  function chooseVoice(preset: VoicePreset) {
    if (!markEdited()) return;
    setPreview(null);
    setDrafts(previous => ({ ...previous, audio: { ...(previous.audio || draft), profile: {
      ...(previous.audio || draft).profile, mode: "custom", skill_ref: "studio.audio.tts@1",
      capability: "tts", model_chain: [], capability_memory_revision_ids: [], installed_skill_refs: [],
      model_binding: { provider: preset.provider_key, model: preset.model_id, profile: preset.profile_id },
      parameters: { voice: preset.voice_id, rate: preset.rate ?? 1 },
    } } }));
  }
  const chosenVoice = voiceCatalog.find(item => item.provider_key === draft.profile.model_binding?.provider
    && item.model_id === draft.profile.model_binding?.model && item.profile_id === draft.profile.model_binding?.profile
    && item.voice_id === draft.profile.parameters?.voice);
  async function loadPreview() {
    if (!persona) return;
    const requestedFingerprint = fingerprint;
    try {
      setError("");
      const value = await api.post(`/content-identities/creative-preview`, {
        persona_id: persona.id,
        account_id: draft.mode === "inherit" && current.kind === "account" ? null : accountId,
        series_id: draft.mode === "inherit" && current.kind === "series" ? null : seriesId, modality,
        ...(draft.mode === "inherit" && current.kind !== "persona" ? {} : {
          profile_override: draft.mode === "override" ? draft.profile : null,
        }),
      });
      if (currentFingerprint.current === requestedFingerprint) {
        setPreview(value); setPreviewFingerprint(requestedFingerprint);
      }
    } catch (e) { if (currentFingerprint.current === requestedFingerprint) setError(errorText(e)); }
  }
  async function loadMethods() {
    if (methodsBusy) return;
    setMethodsBusy(true); setError("");
    try {
      const [page, external] = await Promise.all([capabilityApi.list("limit=100"), capabilityApi.installedSkills()]);
      setMethods(page.items); setInstalled(external.items); setMethodsTruncated(page.total > page.items.length); setMethodsLoaded(true);
    } catch (cause) { setError(errorText(cause)); }
    finally { setMethodsBusy(false); }
  }
  async function save() {
    if (!persona || readonly || !modalityDirty || saving || pendingSave || current.kind === "brand" || !shownPreview || !confirmDiff
        || (revisions[0]?.revision_no ?? 0) !== current.current_revision) return;
    const profile = { ...direct };
    if (draft.mode === "inherit") delete profile[FIELDS[modality]];
    else if (draft.mode === "clear") profile[FIELDS[modality]] = null;
    else profile[FIELDS[modality]] = { ...draft.profile, schema: `persona.creative.${modality}.v1` };
    let receipt: SaveReceipt = { expectedRevision: current.current_revision, profile, confirmed: false, modality,
      draft: JSON.parse(JSON.stringify(draft)), editVersion: editVersions.current[modality] };
    try {
      setSaving(true); setError(""); setPendingSave(receipt);
      const saved = await api.post<Revision>(`/${current.kind === "persona" ? "content-personas" : current.kind === "account" ? "content-accounts" : "content-series"}/${current.id}/revisions`, {
        expected_revision: current.current_revision, profile,
      });
      receipt = { ...receipt, confirmed: true, profile: saved.profile };
      setPendingSave(receipt);
      await reconcileSave(receipt);
    } catch (e) {
      if (!receipt.confirmed && e instanceof ApiError && e.status >= 400 && e.status < 500 && e.status !== 408) {
        setPendingSave(null); setError(errorText(e));
        if (e.status === 409) {
          setPreview(null); setConfirmDiff(false);
          try { await onSaved(); } catch { setError("版本冲突，草稿已保留；最新修订回读失败，请重新核对后保存。"); }
        }
      } else setError(receipt.confirmed ? "新修订已保存，但回读失败。草稿已保留，请先回读核对，不要重复保存。" : "保存结果尚未确认。草稿已保留，请先回读核对，不要重复保存。");
    } finally { setSaving(false); }
  }
  async function reconcileSave(receipt: SaveReceipt) {
    const readback = await onSaved();
    if (!readback) return;
    const exact = readback.find(item => item.revision_no === receipt.expectedRevision + 1
      && stableJson(item.profile) === stableJson(receipt.profile));
    if (exact) {
      rebasedVersions.current[receipt.modality] = receipt.editVersion;
      setDrafts(previous => {
        if (editVersions.current[receipt.modality] !== receipt.editVersion
            || stableJson(previous[receipt.modality]) !== stableJson(receipt.draft)) return previous;
        const next = { ...previous };
        delete next[receipt.modality];
        return next;
      });
      setPendingSave(null); setError(""); setPreview(null); setConfirmDiff(false);
      onNotice(`${MODALITIES.find(item => item.key === receipt.modality)?.label}创作配置已保存为新修订。`);
    } else if (!receipt.confirmed) {
      setPendingSave(null); setPreview(null); setConfirmDiff(false);
      setError((readback[0]?.revision_no ?? 0) === receipt.expectedRevision
        ? "回读未发现新修订。草稿已保留，请重新预览并确认后保存。"
        : "最新修订与本次草稿不同。草稿已保留，请重新预览并核对差异。不可把它当作本次保存成功。");
    } else throw new Error("creative_save_readback_mismatch");
  }
  async function readBackSave() {
    if (!pendingSave || saving) return;
    setSaving(true);
    try { await reconcileSave(pendingSave); }
    catch { setError("保存结果仍无法核对。草稿已保留，请恢复读取后再次回读，不要重复保存。"); }
    finally { setSaving(false); }
  }

  if (current.kind === "brand") return <Section eyebrow="创作配置" title="品牌不设创作方式"><p className="text-[14px] leading-relaxed text-ink-600">品牌只提供约束与语气，不决定用哪种方法、风格或质量标准。请到角色、账号或栏目里配置。</p></Section>;
  const label = MODALITIES.find(item => item.key === modality)?.label || modality;
  return <div className="space-y-6">
    {error && <ErrorBanner message={error} />}
    {pendingSave && <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-amber-200 bg-amber-50 px-5 py-4 text-[14px] text-amber-900"><p>{pendingSave.confirmed ? "新修订已写入，等待回读核对。" : "这次保存的结果还没确认，已暂停再次保存。"}</p><Button variant="secondary" size="sm" disabled={saving} onClick={readBackSave}>回读核对</Button></div>}
    <Section eyebrow="创作配置" title={`${label}内容怎么做`} aside={<><Chip tone={readonly ? "neutral" : "accent"}>{readonly ? "只读" : current.kind === "persona" ? "角色默认" : `${current.kind === "account" ? "账号" : "栏目"}单独设置`}</Chip></>}>
      <p className="-mt-2 mb-5 max-w-2xl text-[13.5px] leading-relaxed text-ink-500">角色是默认来源；账号和栏目可以整套替换某种形态的配置，不会悄悄混合两边。</p>
      <Segmented label="内容形态" value={modality} onChange={(key) => { setModality(key as Modality); setPreview(null); }} items={MODALITIES.map(item => [item.key, item.label] as const)} />
      {dirty && <div className="mt-4"><Notice tone="warn">有未保存的修改。保存当前形态不会丢掉其他形态的草稿；版本更新时保留你改过的字段，请重新预览差异。</Notice></div>}
      <div className="mt-6 grid items-start gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <div className="space-y-5">
          <Field label="配置方式"><select disabled={readonly} className={inputClass} value={draft.mode} onChange={(e) => { if (!markEdited()) return; setDrafts({ ...drafts, [modality]: { ...draft, mode: e.target.value as Mode } }); }}><option value="inherit">{current.kind === "persona" ? "不设置（不继承品牌风格）" : "继承角色 / 上级"}</option><option value="override">在这里完整设置</option><option value="clear">明确清空</option></select></Field>
          {draft.mode === "override" && <>
            <Field label="主方法"><select disabled={readonly} className={inputClass} value={draft.profile.skill_ref} onChange={(e) => updateProfile("skill_ref", e.target.value)}><option value="">请选择</option>{resourceOptions.skills.map((item) => <option key={item.ref} value={item.ref}>{item.purpose}（{refName(item.ref)}）</option>)}</select></Field>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="风格预设"><select disabled={readonly} className={inputClass} value={draft.profile.style_preset_ref} onChange={(e) => updateProfile("style_preset_ref", e.target.value)}><option value="">请选择</option>{resourceOptions.presets.map((item) => <option key={item.ref} value={item.ref}>{refName(item.ref)}</option>)}</select></Field>
              <Field label="质量标准"><select disabled={readonly} className={inputClass} value={draft.profile.quality_profile_ref} onChange={(e) => updateProfile("quality_profile_ref", e.target.value)}><option value="">请选择</option>{resourceOptions.quality.map((item) => <option key={item.ref} value={item.ref}>{refName(item.ref)}</option>)}</select></Field>
            </div>
            {modality === "audio" && selectedSkill?.ref === "studio.audio.tts@1" && <div className="space-y-4 rounded-[14px] border border-ink-200 bg-ink-50/60 p-4">
              <div className="flex items-start justify-between gap-3"><div><p className="text-[14px] font-medium text-ink-900">声音</p><p className="mt-0.5 text-[12.5px] text-ink-500">选定音色会固定对应的模型和声音；不可用时停下，不会自动换。</p></div><Button variant="ghost" size="sm" onClick={() => setAudioAdvanced(value => !value)}>{audioAdvanced ? "收起高级" : "高级设置"}</Button></div>
              <VoicePresetPicker voices={voiceCatalog} selectedId={chosenVoice?.id || ""} disabled={readonly} onSelect={chooseVoice} />
              <Field label={`语速 ${Number(draft.profile.parameters?.rate ?? 1).toFixed(2)}×`}><input type="range" className="w-full accent-accent-500" min="0.5" max="2" step="0.05" disabled={readonly} value={Number(draft.profile.parameters?.rate ?? 1)} onChange={e => updateProfile("parameters", { ...(draft.profile.parameters || {}), rate: Number(e.target.value) })} /></Field>
              {audioAdvanced && <Field label="精确音色 ID（含本人克隆音色）" hint="服务商、模型在下方“指定模型”里设置；只支持音色与语速。"><input disabled={readonly} className={inputClass} maxLength={150} value={draft.profile.parameters?.voice || ""} onChange={e => updateProfile("parameters", { ...(draft.profile.parameters || {}), voice: e.target.value })} /></Field>}
            </div>}
            {selectedSkill?.parameter_schema && <TypedStageField label="主方法参数" schema={selectedSkill.parameter_schema} value={draft.profile.parameters || {}} disabled={readonly} onChange={value => updateProfile("parameters", value)} />}
            <Field label="模型选择"><select disabled={readonly} className={inputClass} value={draft.profile.mode} onChange={(e) => updateProfile("mode", e.target.value)}><option value="auto">自动选择</option><option value="custom">指定模型</option><option value="composed">指定模型 + 后备</option></select></Field>
            {draft.profile.mode !== "auto" && <div className="rounded-[14px] border border-ink-200 p-4"><p className="text-[13px] font-medium text-ink-800">指定模型</p><div className="mt-3 grid gap-2 sm:grid-cols-3">{[["provider", "服务商"], ["model", "模型"], ["profile", "配置名"]].map(([key, text]) => <input key={key} aria-label={text} disabled={readonly} className={inputClass} placeholder={text} value={draft.profile.model_binding?.[key] || ""} onChange={(e) => updateBinding(key, e.target.value)} />)}</div></div>}
            {draft.profile.mode === "composed" && <div className="space-y-3 rounded-[14px] border border-ink-200 p-4">
              <p className="text-[13px] font-medium text-ink-800">后备模型（按顺序尝试）</p>
              {(draft.profile.model_chain || []).map((binding: Record<string, string>, index: number) => <div key={index} className="space-y-2 rounded-xl bg-ink-50 p-3">
                <div className="flex items-center justify-between"><p className="text-[12.5px] text-ink-500">后备 {index + 1}</p><Button variant="ghost" size="sm" disabled={readonly} onClick={() => updateProfile("model_chain", draft.profile.model_chain.filter((_: unknown, position: number) => position !== index))}>移除</Button></div>
                <div className="grid gap-2 sm:grid-cols-3">{[["provider", "服务商"], ["model", "模型"], ["profile", "配置名"]].map(([key, text]) => <input key={key} aria-label={text} className={inputClass} disabled={readonly} placeholder={text} value={binding[key] || ""} onChange={event => updateProfile("model_chain", draft.profile.model_chain.map((item: Record<string, string>, position: number) => position === index ? { ...item, [key]: event.target.value } : item))} />)}</div>
              </div>)}
              <Button variant="secondary" size="sm" disabled={readonly || (draft.profile.model_chain || []).length >= 8} onClick={() => updateProfile("model_chain", [...(draft.profile.model_chain || []), { provider: "", model: "", profile: "" }])}>添加后备模型</Button>
              <div className="border-t border-ink-200/80 pt-3">
                <p className="text-[13px] font-medium text-ink-800">附加方法</p><p className="mt-0.5 text-[12px] text-ink-500">顺序：主方法 → 下列方法 → 本级说明</p>
                <div className="mt-2 space-y-2">{(draft.profile.capability_memory_revision_ids || []).map((id: number, index: number) => {
                  const item = methods.find(value => value.current_revision.id === id);
                  return <div key={`${id}:${index}`} className="flex flex-wrap items-center gap-2 rounded-xl bg-ink-50 px-3 py-2 text-[13px]"><span className="min-w-0 flex-1 text-ink-800">{index + 1}. {item?.name || "固定方法"} <span className="text-ink-500">· 修订 #{id}</span></span><Button variant="ghost" size="sm" disabled={readonly || index === 0} onClick={() => {
                    const next = [...draft.profile.capability_memory_revision_ids]; [next[index - 1], next[index]] = [next[index], next[index - 1]]; updateProfile("capability_memory_revision_ids", next);
                  }}>上移</Button><Button variant="ghost" size="sm" disabled={readonly} onClick={() => updateProfile("capability_memory_revision_ids", draft.profile.capability_memory_revision_ids.filter((_: number, at: number) => at !== index))}>移除</Button></div>;
                })}</div>
                <div className="mt-3"><Button variant="secondary" size="sm" disabled={methodsBusy} onClick={loadMethods}>{methodsBusy ? "读取中…" : methodsLoaded ? "刷新方法库" : "读取方法库"}</Button></div>
                {methodsLoaded && <div className="mt-3"><Field label="加入方法"><select className={inputClass} value="" disabled={readonly || (draft.profile.capability_memory_revision_ids || []).length >= 8} onChange={event => {
                  if (event.target.value) updateProfile("capability_memory_revision_ids", [...(draft.profile.capability_memory_revision_ids || []), Number(event.target.value)]);
                }}><option value="">选择方法</option>{matchingMethods.filter(item => !(draft.profile.capability_memory_revision_ids || []).includes(item.current_revision.id)).map(item => <option key={item.id} value={item.current_revision.id}>{item.name} · 修订 #{item.current_revision.id}</option>)}</select></Field></div>}
                {methodsTruncated && <p className="mt-2 text-[12px] text-amber-700">只显示前 100 项，更多请到方法库查看。</p>}
                {(draft.profile.installed_skill_refs || []).map((id: string) => <div key={id} className="mt-2 flex items-center gap-2 text-[12.5px] text-ink-600"><span className="flex-1">外部 Skill：{id}（只是库存，不会执行）</span><Button variant="ghost" size="sm" disabled={readonly} onClick={() => updateProfile("installed_skill_refs", draft.profile.installed_skill_refs.filter((value: string) => value !== id))}>移除</Button></div>)}
                {methodsLoaded && installed.length > 0 && <p className="mt-2 text-[12px] text-ink-500">外部已安装 {installed.length} 个 Skill，未适配前不能选用。</p>}
              </div>
            </div>}
            <div>
              <div className="mb-3 flex items-center justify-between gap-3"><h4 className="text-[14px] font-medium text-ink-900">制作步骤与方法</h4><Button variant="ghost" size="sm" disabled={methodsBusy} onClick={loadMethods}>{methodsBusy ? "读取中…" : "读取方法库"}</Button></div>
              <ProductionStageControls catalog={catalog} methods={matchingMethods} value={draft.profile.production_stages} disabled={readonly} origin={current.kind} onChange={value => updateProfile("production_stages", value)} />
            </div>
            <Field label="本级补充说明" hint="只影响这里的创作配置。"><textarea disabled={readonly} className={`${inputClass} min-h-24`} value={draft.profile.stage_instruction || ""} onChange={(e) => updateProfile("stage_instruction", e.target.value || null)} placeholder="例如：每期结尾留一个开放问题" /></Field>
          </>}
        </div>
        <aside className="space-y-5 xl:sticky xl:top-6">
          <div>
            <div className="mb-3 flex items-baseline justify-between gap-3"><p className="eyebrow">当前实际生效</p><span className="text-[12px] text-ink-500">来源：{effectiveOrigin ? ({ persona: "角色", account: "账号", series: "栏目", brand: "品牌" } as Record<string, string>)[effectiveOrigin] || effectiveOrigin : "未设置"}{effectiveRevisionId != null && ` · 修订 #${effectiveRevisionId}`}</span></div>
            {effectiveCreative ? <CreativeProfile label={label} value={effectiveCreative} names={names} /> : <p className="rounded-[14px] border border-dashed border-ink-300 p-5 text-[13.5px] text-ink-500">{!effective ? "还没读取生效配置" : effectiveCreative === null ? "已明确清空" : "还没有设置"}</p>}
            {effectiveCreative?.capability_memory_revision_ids?.length > 0 && <p className="mt-2 text-[12.5px] text-ink-500">附加方法：{effectiveCreative.capability_memory_revision_ids.map((id: number) => methods.find(item => item.current_revision.id === id)?.name || `修订 #${id}`).join("、")}</p>}
          </div>
          <div className="rounded-[14px] border border-ink-200 bg-surface p-5">
            <p className="eyebrow">这次会改动</p>
            {changedFields.length === 0 ? <p className="mt-2 text-[13.5px] text-ink-500">还没有改动。</p> : <ul className="mt-3 space-y-3">{changedFields.map(key => <li key={key} className="min-w-0 text-[13px]"><p className="font-medium text-ink-900">{CHANGE_LABELS[key] || key}</p>{draft.mode === "override" && <div className="mt-1 grid gap-1"><p className="break-all text-ink-500"><span className="mr-1.5 rounded bg-ink-100 px-1 text-[11px]">原</span>{summarize(profileBefore?.[key])}</p><p className="break-all text-accent-700"><span className="mr-1.5 rounded bg-accent-50 px-1 text-[11px]">新</span>{summarize(profileAfter?.[key])}</p></div>}</li>)}</ul>}
          </div>
          {shownPreview && <div className={`rounded-[14px] border p-5 ${shownPreview.status === "ready" ? "border-emerald-200 bg-emerald-50/60" : "border-amber-200 bg-amber-50/60"}`}>
            <p className="eyebrow">预览结果</p>
            <p className={`mt-2 text-[14px] font-medium ${shownPreview.status === "ready" ? "text-emerald-800" : "text-amber-800"}`}>{shownPreview.status !== "ready" ? `暂不可用：${shownPreview.reason || "还需要配置"}` : selectedSkill?.execution_support?.status === "partial" || draft.profile.capability_memory_revision_ids?.length || draft.profile.installed_skill_refs?.length ? "部分就绪：还要在具体步骤里验证方法与输入" : "已就绪：配置可用（还不代表成品合格）"}</p>
            {shownPreview.selected_binding && <p className="mt-2 text-[13px] text-ink-700">实际使用：{shownPreview.selected_binding.model} · {shownPreview.selected_binding.provider}</p>}
            {shownPreview.declared_chain?.map((item: any, index: number) => <p key={index} className="mt-1 text-[12.5px] text-ink-600">后备 {index + 1}：{item.model} · {item.provider}</p>)}
            {shownPreview.fallback_reason && <p className="mt-1 text-[12.5px] text-amber-700">选择原因：{shownPreview.fallback_reason}</p>}
          </div>}
        </aside>
      </div>
      <div className="mt-7 flex flex-wrap items-center gap-3 border-t border-ink-200/80 pt-5">
        <Button variant="secondary" onClick={loadPreview} disabled={!persona}>预览生效结果</Button>
        {shownPreview && <label className="flex items-center gap-2 text-[13px] text-ink-600"><input type="checkbox" className="accent-accent-500" disabled={readonly} checked={confirmDiff} onChange={event => setConfirmDiff(event.target.checked)} />我已核对改动；保存会生成新修订，不影响历史作品和其他角色</label>}
        <Button className="ml-auto" onClick={save} disabled={readonly || saving || !!pendingSave || !shownPreview || !confirmDiff}>{saving ? "保存中…" : `保存${label}配置`}</Button>
      </div>
    </Section>
    <Section eyebrow="内置资源" title="平台自带的方法与标准" aside={<span>只读 · 不会自动调用模型</span>}>
      <div className="grid gap-6 sm:grid-cols-3">
        <Stat label="内置方法" value={catalog?.skills.length ?? "—"} />
        <Stat label="风格预设" value={catalog?.style_presets.length ?? "—"} />
        <Stat label="质量标准" value={catalog?.quality_profiles.length ?? "—"} />
      </div>
    </Section>
  </div>;
}

const CHANGE_LABELS: Record<string, string> = { mode: "模型选择", skill_ref: "主方法", style_preset_ref: "风格预设", quality_profile_ref: "质量标准", model_binding: "指定模型", model_chain: "后备模型", capability_memory_revision_ids: "附加方法", installed_skill_refs: "外部 Skill", production_stages: "制作步骤", parameters: "参数", stage_instruction: "补充说明" };
function summarize(value: unknown): string {
  if (value === undefined) return "继承 / 未设置";
  if (value === null) return "清空";
  if (typeof value === "string") return refName(value) || value;
  if (Array.isArray(value)) return value.length ? `${value.length} 项` : "无";
  if (typeof value === "object") return `${Object.keys(value as object).length} 项设置`;
  return String(value);
}
