import { useEffect, useMemo, useRef, useState } from "react";
import { api, ApiError } from "../api";
import { Button, ErrorBanner, Field, inputClass } from "../components/ui";
import { capabilityApi, type CapabilityArtifact, type InstalledSkill } from "./capabilityMemoryTypes";
import { TypedStageField } from "./StageContractControls";
import VoicePresetPicker, { type VoicePresetOption } from "./VoicePresetPicker";

type Kind = "brand" | "persona" | "account" | "series";
type Entity = { kind: Kind; id: number; name: string; status: string; current_revision: number };
type Revision = { revision_no: number; profile: Record<string, any> };
type Effective = { effective_profile: Record<string, any>; creative_profile_origins?: Record<string, string>; revision_ids?: Record<string, number | null> };
type Catalog = { skills: any[]; style_presets: any[]; quality_profiles: any[]; starter_personas: any[] };
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
        ? previous[key] : nextBaselines[key],
    ])) as Record<Modality, any>);
    baselines.current = nextBaselines;
  }, [revisions, effective]);
  const dirty = MODALITIES.some(({ key }) => drafts[key]
    && stableJson(drafts[key]) !== stableJson(baselines.current[key]));
  useEffect(() => { onDirtyChange(dirty || pendingSave !== null); }, [dirty, pendingSave, onDirtyChange]);

  const draft = drafts[modality] || initialDraft(modality, direct, effectiveProfile);
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
    && ((item.scope_type === "persona" && item.scope.id === persona?.id)
      || (item.scope_type === "account" && item.scope.id === accountId)
      || (item.scope_type === "series" && item.scope.id === seriesId)));

  function markEdited() {
    if (readonly) return false;
    editVersions.current[modality] += 1;
    onDirtyChange(true);
    return true;
  }
  function updateProfile(key: string, value: any) {
    if (!markEdited()) return;
    setPreview(null);
    const reset = key === "mode" && value !== "composed" ? { model_chain: [], capability_memory_revision_ids: [], installed_skill_refs: [] }
      : key === "skill_ref" ? { parameters: {} } : {};
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
    if (!persona || readonly || saving || pendingSave || current.kind === "brand" || !shownPreview || !confirmDiff
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

  if (current.kind === "brand") return <section className="rounded-xl border bg-white p-5"><h3 className="font-medium">创作配置</h3><p className="mt-2 text-sm text-slate-600">Brand 只提供品牌约束上下文，不提供 Persona 的 Skill、风格、质量或 Recipe 默认值。请选择 Persona、账号或栏目配置创作方式。</p></section>;
  return <div className="space-y-4">
    {error && <ErrorBanner message={error} />}
    {pendingSave && <div className="rounded-xl border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900"><p>{pendingSave.confirmed ? "新修订写入已确认，等待回读核对。" : "本次保存结果尚未确认，已暂停再次保存。"}</p><Button variant="secondary" disabled={saving} onClick={readBackSave}>回读核对保存结果</Button></div>}
    <section className="rounded-xl border bg-white p-5">
      {dirty && <p className="mb-3 text-xs text-amber-700">有未保存的创作配置；保存当前形态不会丢弃其他形态的草稿。</p>}
      <div className="flex flex-wrap items-start justify-between gap-3"><div><h3 className="font-medium">创作配置</h3><p className="mt-1 text-sm text-slate-500">Persona 是创作根；账号和栏目只替换完整的形态配置，不做隐藏深合并。</p></div><span className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-600">{readonly ? "只读" : current.kind === "persona" ? "创作根" : "本级覆盖"}</span></div>
      <div className="mt-4 flex flex-wrap gap-2">{MODALITIES.map((item) => <button key={item.key} onClick={() => { setModality(item.key); setPreview(null); }} className={`rounded-lg px-3 py-2 text-sm ${modality === item.key ? "bg-indigo-600 text-white" : "bg-slate-100 text-slate-700"}`}>{item.label}</button>)}</div>
      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <div className="space-y-3">
          <Field label="配置方式"><select disabled={readonly} className={inputClass} value={draft.mode} onChange={(e) => { if (!markEdited()) return; setDrafts({ ...drafts, [modality]: { ...draft, mode: e.target.value as Mode } }); }}><option value="inherit">{current.kind === "persona" ? "移除本级创作配置（不继承 Brand 风格）" : "继承角色 / 上级"}</option><option value="override">本级完整覆盖</option><option value="clear">显式清空</option></select></Field>
          {draft.mode === "override" && <>
            <Field label="Studio Skill"><select disabled={readonly} className={inputClass} value={draft.profile.skill_ref} onChange={(e) => updateProfile("skill_ref", e.target.value)}><option value="">请选择 Skill</option>{resourceOptions.skills.map((item) => <option key={item.ref} value={item.ref}>{item.ref} · {item.purpose}</option>)}</select></Field>
            <Field label="Style Preset"><select disabled={readonly} className={inputClass} value={draft.profile.style_preset_ref} onChange={(e) => updateProfile("style_preset_ref", e.target.value)}><option value="">请选择风格</option>{resourceOptions.presets.map((item) => <option key={item.ref} value={item.ref}>{item.ref}</option>)}</select></Field>
            <Field label="Quality Profile"><select disabled={readonly} className={inputClass} value={draft.profile.quality_profile_ref} onChange={(e) => updateProfile("quality_profile_ref", e.target.value)}><option value="">请选择质量门禁</option>{resourceOptions.quality.map((item) => <option key={item.ref} value={item.ref}>{item.ref}</option>)}</select></Field>
            {modality === "audio" && selectedSkill?.ref === "studio.audio.tts@1" && <div className="space-y-3 rounded-lg border border-slate-200 p-3">
              <div className="flex items-center justify-between gap-3"><div><p className="text-sm font-medium">声音</p><p className="text-xs text-slate-500">选择音色会钉死对应的模型和声音；不可用就停止，不自动替换。</p></div><button type="button" className="text-xs text-indigo-700 underline" onClick={() => setAudioAdvanced(value => !value)}>{audioAdvanced ? "收起高级设置" : "展开高级设置"}</button></div>
              <VoicePresetPicker voices={voiceCatalog} selectedId={chosenVoice?.id || ""} disabled={readonly} onSelect={chooseVoice} />
              <Field label={`语速 ${Number(draft.profile.parameters?.rate ?? 1).toFixed(2)}×`}><input type="range" min="0.5" max="2" step="0.05" disabled={readonly} value={Number(draft.profile.parameters?.rate ?? 1)} onChange={e => updateProfile("parameters", { ...(draft.profile.parameters || {}), rate: Number(e.target.value) })} /></Field>
              {audioAdvanced && <div className="space-y-2"><p className="text-xs text-slate-500">供应商/模型/Profile 在下面的“指定模型”中设置。只支持此适配器声明的 voice 与 rate；不展示未实现的情绪、音调或暂停控制。</p><Field label="精确 voice ID（含本人克隆音色）"><input disabled={readonly} className={inputClass} maxLength={150} value={draft.profile.parameters?.voice || ""} onChange={e => updateProfile("parameters", { ...(draft.profile.parameters || {}), voice: e.target.value })} /></Field></div>}
            </div>}
            {selectedSkill?.parameter_schema && <TypedStageField label="默认阶段参数（受 Skill 合同限制）" schema={selectedSkill.parameter_schema} value={draft.profile.parameters || {}} disabled={readonly} onChange={value => updateProfile("parameters", value)} />}
            <Field label="模式"><select disabled={readonly} className={inputClass} value={draft.profile.mode} onChange={(e) => updateProfile("mode", e.target.value)}><option value="auto">自动选择</option><option value="custom">指定模型</option><option value="composed">自定义组合</option></select></Field>
            {draft.profile.mode !== "auto" && <div className="rounded-lg border border-slate-200 p-3"><p className="text-xs font-medium text-slate-600">精确模型绑定</p><div className="mt-2 grid gap-2 sm:grid-cols-3">{["provider", "model", "profile"].map((key) => <input key={key} disabled={readonly} className={inputClass} placeholder={key} value={draft.profile.model_binding?.[key] || ""} onChange={(e) => updateBinding(key, e.target.value)} />)}</div>{draft.profile.mode === "composed" && <p className="mt-2 text-xs text-slate-500">Custom Composition 只允许使用已保存的有序绑定链；未声明的 Provider 不会自动发现。</p>}</div>}
            {draft.profile.mode === "composed" && <div className="space-y-2 rounded-lg border p-3">
              <p className="text-xs font-medium text-slate-600">按顺序尝试的后备模型</p>
              {(draft.profile.model_chain || []).map((binding: Record<string, string>, index: number) => <div key={index} className="space-y-2 rounded-lg bg-slate-50 p-2">
                <p className="text-xs text-slate-500">后备 {index + 1}</p>
                <div className="grid gap-2 sm:grid-cols-3">{["provider", "model", "profile"].map(key => <input key={key} className={inputClass} disabled={readonly} placeholder={key} value={binding[key] || ""} onChange={event => updateProfile("model_chain", draft.profile.model_chain.map((item: Record<string, string>, position: number) => position === index ? { ...item, [key]: event.target.value } : item))} />)}</div>
                <Button variant="ghost" disabled={readonly} onClick={() => updateProfile("model_chain", draft.profile.model_chain.filter((_: unknown, position: number) => position !== index))}>移除此后备模型</Button>
              </div>)}
              <Button variant="secondary" disabled={readonly || (draft.profile.model_chain || []).length >= 8} onClick={() => updateProfile("model_chain", [...(draft.profile.model_chain || []), { provider: "", model: "", profile: "" }])}>添加后备模型</Button>
              <p className="pt-2 text-xs font-medium text-slate-600">方法组合顺序：内置 Skill → 下列精确方法修订 → Stage 说明</p>
              {(draft.profile.capability_memory_revision_ids || []).map((id: number, index: number) => {
                const item = methods.find(value => value.current_revision.id === id);
                return <div key={`${id}:${index}`} className="flex flex-wrap items-center gap-2 rounded-lg bg-slate-50 p-2 text-xs"><span className="min-w-0 flex-1">{index + 1}. {item?.name || "固定方法"} · Revision #{id}{item ? ` · ${item.scope_type} #${item.scope.id}` : "（回读后核对）"}</span><Button variant="ghost" size="sm" disabled={readonly || index === 0} onClick={() => {
                  const next = [...draft.profile.capability_memory_revision_ids]; [next[index - 1], next[index]] = [next[index], next[index - 1]]; updateProfile("capability_memory_revision_ids", next);
                }}>上移</Button><Button variant="ghost" size="sm" disabled={readonly} onClick={() => updateProfile("capability_memory_revision_ids", draft.profile.capability_memory_revision_ids.filter((_: number, at: number) => at !== index))}>移除</Button></div>;
              })}
              <Button variant="secondary" disabled={methodsBusy} onClick={loadMethods}>{methodsBusy ? "读取中…" : methodsLoaded ? "刷新方法 / 外部 Skill 库存" : "读取可选方法 / 外部 Skill 库存"}</Button>
              {methodsLoaded && <Field label="明确添加当前角色 / 账号 / 栏目的方法"><select className={inputClass} value="" disabled={readonly || (draft.profile.capability_memory_revision_ids || []).length >= 8} onChange={event => {
                if (event.target.value) updateProfile("capability_memory_revision_ids", [...(draft.profile.capability_memory_revision_ids || []), Number(event.target.value)]);
              }}><option value="">不自动选择方法</option>{matchingMethods.filter(item => !(draft.profile.capability_memory_revision_ids || []).includes(item.current_revision.id)).map(item => <option key={item.id} value={item.current_revision.id}>{item.name} · {item.scope_type} #{String(item.scope.id)} · Revision #{item.current_revision.id}</option>)}</select></Field>}
              {methodsTruncated && <p className="text-xs text-amber-700">当前只读前 100 项。更多方法请在能力方法库查看；不自动扩大角色范围。</p>}
              {(draft.profile.installed_skill_refs || []).map((id: string) => <div key={id} className="flex gap-2 text-xs"><span className="flex-1">外部 Skill：{id} · 库存不代表 Stage 可执行</span><Button variant="ghost" size="sm" disabled={readonly} onClick={() => updateProfile("installed_skill_refs", draft.profile.installed_skill_refs.filter((value: string) => value !== id))}>移除</Button></div>)}
              {methodsLoaded && installed.length > 0 && <Field label="外部 Installed Skill（当前无已验证 Stage 绑定）"><select className={inputClass} value="" disabled><option value="">不可执行，不能代替内置方法</option>{installed.map(item => <option key={item.id} value={item.id}>{item.name} · {item.id}</option>)}</select></Field>}
            </div>}
            <Field label="本级阶段说明"><textarea disabled={readonly} className={`${inputClass} min-h-20`} value={draft.profile.stage_instruction || ""} onChange={(e) => updateProfile("stage_instruction", e.target.value || null)} placeholder="只影响本级创作配置的说明" /></Field>
          </>}
        </div>
        <div className="rounded-xl bg-slate-50 p-4 text-sm">
          <section aria-label="当前生效创作配置">
            <p className="font-medium">当前生效创作配置（只读）</p>
            <p className="mt-2 text-slate-600">来源：{effectiveOrigin || "未设置"}{effectiveRevisionId != null && ` · 来源 Revision #${effectiveRevisionId}`}</p>
            <p className="mt-1 text-xs text-slate-500">当前身份修订 v{current.current_revision}；下方草稿和预览不会改写此摘要。</p>
            {effectiveCreative ? <div className="mt-3 space-y-2 break-all text-xs text-slate-600">
              <p>模式：{effectiveCreative.mode || "未设置"}</p>
              <p>Studio Skill：{effectiveCreative.skill_ref || "未设置"}</p>
              <p>Style Preset：{effectiveCreative.style_preset_ref || "未设置"}</p>
              <p>Quality Profile：{effectiveCreative.quality_profile_ref || "未设置"}</p>
              <p>声明的主绑定：{effectiveCreative.model_binding ? JSON.stringify(effectiveCreative.model_binding) : effectiveCreative.mode === "auto" ? "自动路由（实际绑定以 Effective Preview 为准）" : "未设置"}</p>
              <div><p>声明的后备绑定（按顺序）：</p>{effectiveCreative.model_chain?.length ? <ol className="ml-4 mt-1 list-decimal space-y-1">{effectiveCreative.model_chain.map((binding: Record<string, string>, index: number) => <li key={index}>{JSON.stringify(binding)}</li>)}</ol> : <p className="mt-1 text-slate-500">无声明的后备绑定</p>}</div>
              <div><p>Capability Memory 方法（按顺序）：</p>{effectiveCreative.capability_memory_revision_ids?.length ? <ol className="ml-4 mt-1 list-decimal space-y-1">{effectiveCreative.capability_memory_revision_ids.map((id: number, index: number) => <li key={`${id}:${index}`}>Revision #{id}</li>)}</ol> : <p className="mt-1 text-slate-500">无扩展方法</p>}</div>
              {effectiveCreative.installed_skill_refs?.length > 0 && <div><p>声明的 Installed Skill（不代表 Stage 可执行）：</p><ol className="ml-4 mt-1 list-decimal space-y-1">{effectiveCreative.installed_skill_refs.map((ref: string, index: number) => <li key={`${ref}:${index}`}>{ref}</li>)}</ol></div>}
            </div> : <p className="mt-3 text-xs text-slate-500">{!effective ? "尚未读取生效配置" : effectiveCreative === null ? "当前生效配置已显式清空" : "当前未设置创作配置"}</p>}
          </section>
          <div className="mt-4 border-t pt-3"><p className="font-medium">本次完整替换的差异</p><p className="mt-1 text-xs text-slate-500">未明确修改的上级字段只复制到草稿，不自动写回或深合并。</p>{changedFields.map(key => <div key={key} className="mt-2 min-w-0 text-xs"><p className="font-medium">{key}</p>{draft.mode === "override" && <><p className="break-all text-slate-500">原：{JSON.stringify(profileBefore?.[key]) ?? "继承 / 未设置"}</p><p className="break-all text-indigo-700">拟保存：{JSON.stringify(profileAfter?.[key]) ?? "移除"}</p></>}</div>)}{changedFields.length === 0 && <p className="mt-2 text-xs text-slate-500">配置未变化。</p>}</div>
          {shownPreview && <div className="mt-4 border-t pt-3"><p className="font-medium">Effective 配置路由预览</p><p className={`mt-1 ${shownPreview.status === "ready" ? "text-emerald-700" : "text-amber-700"}`}>{shownPreview.status !== "ready" ? `blocked · ${shownPreview.reason || "需要配置"}` : selectedSkill?.execution_support?.status === "partial" || draft.profile.capability_memory_revision_ids?.length || draft.profile.installed_skill_refs?.length ? "partial · 需在具体 Stage 验证方法与输入" : "ready · 配置路由已就绪，尚非成品验收"}</p><p className="mt-1 break-all text-xs text-slate-500">resolution: {shownPreview.resolution_hash || "无可执行配置"}</p>{shownPreview.selected_binding && <p className="mt-1 text-xs text-slate-600">实际绑定：{shownPreview.selected_binding.provider} / {shownPreview.selected_binding.model} / {shownPreview.selected_binding.profile}</p>}{shownPreview.declared_chain?.map((item: any, index: number) => <p key={index} className="mt-1 text-xs text-slate-600">声明顺序 {index + 1}：{item.provider} / {item.model} / {item.profile}</p>)}{shownPreview.fallback_reason && <p className="mt-1 text-xs text-amber-700">选择原因：{shownPreview.fallback_reason}</p>}</div>}
        </div>
      </div>
      <div className="mt-4 flex flex-wrap gap-2"><Button variant="secondary" onClick={loadPreview} disabled={!persona}>查看 Effective Preview</Button><Button onClick={save} disabled={readonly || saving || !!pendingSave || !shownPreview || !confirmDiff}>{saving ? "保存中…" : "保存本级创作配置"}</Button></div>
      {shownPreview && <label className="mt-3 flex gap-2 text-xs text-slate-600"><input type="checkbox" disabled={readonly} checked={confirmDiff} onChange={event => setConfirmDiff(event.target.checked)} />我已核对本级完整替换差异；保存创建新身份修订，不改历史 Snapshot 或其他角色。</label>}
    </section>
    <section className="rounded-xl border bg-white p-5"><h3 className="font-medium">Studio 内置资源</h3><p className="mt-1 text-sm text-slate-500">只读产品资源，不等于 Installed Agent Skill，也不会自动调用模型。</p><div className="mt-3 grid gap-3 sm:grid-cols-3"><div className="rounded-lg bg-slate-50 p-3"><p className="text-xs text-slate-500">Built-in Skills</p><p className="mt-1 text-xl font-semibold">{catalog?.skills.length ?? "—"}</p></div><div className="rounded-lg bg-slate-50 p-3"><p className="text-xs text-slate-500">Style Presets</p><p className="mt-1 text-xl font-semibold">{catalog?.style_presets.length ?? "—"}</p></div><div className="rounded-lg bg-slate-50 p-3"><p className="text-xs text-slate-500">Quality Profiles</p><p className="mt-1 text-xl font-semibold">{catalog?.quality_profiles.length ?? "—"}</p></div></div></section>
  </div>;
}
