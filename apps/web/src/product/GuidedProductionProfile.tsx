import { useEffect, useState } from "react";
import FormAssistancePanel from "./FormAssistancePanel";
import type { AssistanceField } from "./formAssistanceTypes";
import { api, ApiError } from "../api";
import { Button, ErrorBanner, Field, inputClass } from "../components/ui";

export type Settings = {
  shared_references?: { material_revision_id: number; content_hash: string; role: "product" | "person" | "scene" }[];
  work_type?: "showcase" | "scene" | "ugc"; creation_mode?: "original" | "reference";
  speech_mode?: "voiceover" | "lip_sync" | "none" | "mixed"; reference_notes?: string; comparison_notes?: string;
  visual_style?: string; continuity_notes?: string; dialogue?: string; dialogue_language?: string;
  music_direction?: string; ae_packaging?: boolean; target_duration_seconds?: number | null; estimated_voice_duration_seconds?: number | null;
  feedback?: { location: string; note: string; scope: "work" | "sku" | "category" | "style" | "general" } | null;
  script_style?: string | null; hook_pinned?: string; hook_versions?: number; reference_structure?: string;
  material_mode?: "photo_only" | "user_footage" | "mixed"; i2v_mode?: "default" | "manual" | "auto";
};
type Profile = { revision: number; settings: Settings; sku_id?: number | null };
export default function GuidedProductionProfile({ projectId, unitId, view, readOnly, onDirty, onSavedSettings, assistantVisible = false, onAssistanceFocus }: { projectId: number; unitId: number; view: string; readOnly: boolean; onDirty: (dirty: boolean) => void; onSavedSettings?: (settings: Settings) => void; assistantVisible?: boolean; onAssistanceFocus?: () => void }) {
  const base = `/content-projects/${projectId}/units/${unitId}/production-profile`;
  const [assets, setAssets] = useState<{ material_revision_id: number; content_hash: string; title?: string; kind: string; model_use_allowed: boolean }[]>([]);
  const [assetIssue, setAssetIssue] = useState("");
  const [profile, setProfile] = useState<Profile | null>(null);
  const [draft, setDraft] = useState<Settings>({});
  const [dirty, setDirty] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  async function load() {
    setBusy(true); setError("");
    try { const value = await api.get<Profile>(base); setProfile(value); setDraft(value.settings); setDirty(false); onSavedSettings?.(value.settings); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "制作设置读取失败"); }
    finally { setBusy(false); }
  }
  useEffect(() => { void load(); }, [base]);
  useEffect(() => { let active = true; api.get<typeof assets>(`/content-projects/${projectId}/shared-assets`).then(value => { if (active) { setAssets(value); setAssetIssue(""); } }).catch(() => { if (active) setAssetIssue("共同参考素材读取失败，已保存引用保留；请重新进入作品后重试。"); }); return () => { active = false; }; }, [projectId]);
  useEffect(() => { onDirty(dirty); }, [dirty, onDirty]);
  useEffect(() => {
    if (!dirty) return;
    const warn = (event: BeforeUnloadEvent) => { event.preventDefault(); event.returnValue = ""; };
    const guard = (event: MouseEvent) => {
      if (event.defaultPrevented || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      const anchor = (event.target as Element | null)?.closest?.("a[href]") as HTMLAnchorElement | null;
      if (!anchor || anchor.target === "_blank") return;
      const target = new URL(anchor.href);
      if (target.origin === window.location.origin && target.pathname === window.location.pathname && target.search === window.location.search) return;
      if (!window.confirm("离开会丢弃未保存的制作设置，继续？")) { event.preventDefault(); event.stopPropagation(); }
    };
    window.addEventListener("beforeunload", warn); document.addEventListener("click", guard, true);
    return () => { window.removeEventListener("beforeunload", warn); document.removeEventListener("click", guard, true); };
  }, [dirty]);
  function update(patch: Partial<Settings>) { setDraft(value => ({ ...value, ...patch })); setDirty(true); setNotice(""); }
  async function save() {
    if (!profile || busy || readOnly) return;
    setBusy(true); setError("");
    try { const value = await api.put<Profile>(base, { expected_revision: profile.revision, settings: draft }); setProfile(previous => ({ ...previous, ...value })); setDraft(value.settings); setDirty(false); onSavedSettings?.(value.settings); setNotice("制作设置已保存为独立版本；不代表方案、素材或成片已接受。"); }
    catch (cause) { setError(cause instanceof ApiError && cause.status === 409 ? "制作设置已有新版本，当前草稿保留。请核对后重新载入。" : cause instanceof Error ? cause.message : "保存失败，草稿保留"); }
    finally { setBusy(false); }
  }
  const visible = ["goal", "plan", "style", "edit", "review"].includes(view);
  const disabled = readOnly || busy || !profile;
  const text = (key: "comparison_notes" | "reference_notes" | "visual_style" | "continuity_notes" | "dialogue" | "dialogue_language" | "music_direction", label: string) => <Field label={label}><textarea data-ai-field={key} aria-label={label} className={inputClass} rows={key === "dialogue" ? 4 : 2} value={draft[key] || ""} disabled={disabled} onChange={event => update({ [key]: event.target.value })} /></Field>;
  const profileLabels = { comparison_notes: "本次对照只改变什么", reference_notes: "参考二创说明", visual_style: "共同视觉定样", continuity_notes: "跨镜头衔接说明", dialogue: "台词 / 口语稿", dialogue_language: "台词语言", music_direction: "环境声与配乐方向" } as const;
  const textKeys: (keyof typeof profileLabels)[] = view === "plan" ? ["reference_notes", "comparison_notes"] : view === "style" ? ["reference_notes", "visual_style", "continuity_notes", "dialogue", "dialogue_language", "music_direction"] : [];
  const assistanceFields: AssistanceField[] = textKeys.filter(key => !(key === "reference_notes" && draft.creation_mode !== "reference") && !(draft.speech_mode === "none" && (key === "dialogue" || key === "dialogue_language"))).map(key => ({ key, label: profileLabels[key], value: draft[key] || "", apply: value => update({ [key]: String(value ?? "") }) }));
  if (view === "review") assistanceFields.push(
    { key: "feedback.location", label: "成片反馈位置", protected: true, value: draft.feedback?.location || "", apply: value => update({ feedback: { location: String(value ?? ""), note: draft.feedback?.note || "", scope: draft.feedback?.scope || "work" } }) },
    { key: "feedback.note", label: "具体反馈", value: draft.feedback?.note || "", apply: value => update({ feedback: { location: draft.feedback?.location || "", note: String(value ?? ""), scope: draft.feedback?.scope || "work" } }) },
  );
  return <FormAssistancePanel surface="production_profile" context={{ work_type: draft.work_type || null, creation_mode: draft.creation_mode || null, speech_mode: draft.speech_mode || null }} projectId={projectId} unitId={unitId} fields={assistanceFields} versionKey={JSON.stringify([profile?.revision, draft.work_type, draft.creation_mode, draft.speech_mode, draft.shared_references, draft.target_duration_seconds, draft.estimated_voice_duration_seconds, draft.feedback?.scope])} readOnly={disabled} assistantVisible={visible && assistantVisible && assistanceFields.length > 0} onFieldFocus={onAssistanceFocus}>{visible && <section className="mb-5 space-y-4 rounded-2xl border border-slate-200 bg-white p-5" aria-label="本作品制作设置">
    <div className="flex items-center justify-between gap-3"><h3 className="font-semibold">本作品制作设置</h3><span className="text-xs text-slate-500">{dirty ? "有未保存设置" : profile ? `已保存 v${profile.revision}` : "尚未读取"}</span></div>
    {profile?.sku_id === null && <p className="text-sm text-amber-800">旧作品待关联SKU；保留现有商品资料，不根据名称自动匹配。</p>}
    {error && <ErrorBanner message={error} />}
    {!profile && <Button variant="secondary" disabled={busy} onClick={() => void load()}>重新读取制作设置</Button>}
    {(view === "goal" || view === "plan") && <div className="grid gap-4 sm:grid-cols-2"><Field label="作品类型"><select className={inputClass} value={draft.work_type || ""} disabled={disabled} onChange={event => update({ work_type: event.target.value as Settings["work_type"] })}><option value="" disabled>待选择</option><option value="showcase">商品展示</option><option value="scene">品牌 / 使用场景</option><option value="ugc">人物 UGC</option></select></Field><Field label="创作方式"><select className={inputClass} value={draft.creation_mode || ""} disabled={disabled} onChange={event => update({ creation_mode: event.target.value as Settings["creation_mode"] })}><option value="" disabled>待选择</option><option value="original">原创</option><option value="reference">参考二创</option></select></Field>{view === "plan" && draft.creation_mode === "reference" && text("reference_notes", "参考出处、保留和改写范围")}<Field label="目标时长（秒，未知可留空）"><input type="number" min={1} className={inputClass} value={draft.target_duration_seconds ?? ""} disabled={disabled} onChange={event => update({ target_duration_seconds: event.target.value ? Number(event.target.value) : null })} /></Field></div>}
    {(view === "goal" || view === "plan") && <SalesDirection draft={draft} disabled={disabled} update={update} />}
    {view === "plan" && <div>{text("comparison_notes", "本次对照只改变什么（可选）")}<p className="mt-1 text-xs text-slate-500">对照制作可从同一SKU、同一方案新建独立作品，只改一个因素，其余条件保持；这是可选记录，不限制正常编辑。</p></div>}
    {(view === "plan" || view === "style") && <><Field label="讲话方式"><select className={inputClass} value={draft.speech_mode || ""} disabled={disabled} onChange={event => update({ speech_mode: event.target.value as Settings["speech_mode"] })}><option value="" disabled>待选择</option><option value="voiceover">旁白</option><option value="lip_sync">人物对白 / 口型同步</option><option value="none">无讲话</option><option value="mixed">混合声音</option></select></Field>{(draft.speech_mode === "lip_sync" || draft.speech_mode === "mixed") && <p className="text-sm text-amber-800">人物同步能力待真实样本验证；请先确认网站支持所需台词或声音输入，回传后检查原声与口型。</p>}</>}
    {view === "style" && <div className="grid gap-4 sm:grid-cols-2">{draft.creation_mode === "reference" && text("reference_notes", "参考出处、保留和改写范围")}{text("visual_style", "共同视觉定样：商品、人物、场景、光线")}{text("continuity_notes", "跨镜头参考与动作衔接")}{draft.speech_mode !== "none" && <>{text("dialogue", "本条台词 / 口语稿")}{text("dialogue_language", "台词语言")}<Field label="预计旁白时长（秒，可留空）"><input type="number" min={0.01} max={3600} step="any" className={inputClass} value={draft.estimated_voice_duration_seconds ?? ""} disabled={disabled} onChange={event => update({ estimated_voice_duration_seconds: event.target.value ? Number(event.target.value) : null })} /><p className="mt-1 text-xs text-slate-500">规划值，非已生成音频时长；实际时长以精确音频素材为准。</p></Field></>}{text("music_direction", "环境声与配乐方向（可明确不使用配乐）")}</div>}
    {view === "style" && <div className="space-y-3 rounded-xl border border-slate-200 p-4"><h4 className="font-medium">共同视觉参考 · 精确素材版本</h4><p className="text-xs text-slate-500">从已入项目且允许模型使用的真实图片选取；保存引用不代表已批准，也不代表网站已收到这些输入。</p>{assetIssue && <ErrorBanner message={assetIssue} />}{([ ["product", "商品参考"], ["person", "人物参考"], ["scene", "场景参考"] ] as const).map(([role, label]) => {
      const selected = draft.shared_references?.find(item => item.role === role);
      const available = assets.filter(item => item.kind === "image" && item.model_use_allowed);
      return <Field key={role} label={label}><select aria-label={label} className={inputClass} value={selected?.material_revision_id || ""} disabled={disabled || !!assetIssue} onChange={event => { const asset = available.find(item => item.material_revision_id === Number(event.target.value)); update({ shared_references: [...(draft.shared_references || []).filter(item => item.role !== role), ...(asset ? [{ role, material_revision_id: asset.material_revision_id, content_hash: asset.content_hash }] : [])] }); }}><option value="">未选择</option>{selected && !available.some(item => item.material_revision_id === selected.material_revision_id && item.content_hash === selected.content_hash) && <option value={selected.material_revision_id}>已存 #{selected.material_revision_id}（当前不可用，需核对）</option>}{available.map(item => <option key={item.material_revision_id} value={item.material_revision_id}>{item.title || "图片"} · #{item.material_revision_id}</option>)}</select>{selected && <p className="mt-1 break-all text-xs text-slate-500">版本 #{selected.material_revision_id} · {selected.content_hash}</p>}</Field>;
    })}</div>}
    {view === "edit" && <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={draft.ae_packaging || false} disabled={disabled} onChange={event => update({ ae_packaging: event.target.checked })} />本作品需要 AE 包装（未勾选则按需跳过）</label>}
    {view === "review" && <div className="grid gap-3 sm:grid-cols-2"><Field label="成片反馈位置"><input data-ai-field="feedback.location" className={inputClass} value={draft.feedback?.location || ""} disabled={disabled} onChange={event => update({ feedback: { location: event.target.value, note: draft.feedback?.note || "", scope: draft.feedback?.scope || "work" } })} /></Field><Field label="反馈范围（保存不自动采用到其他作品）"><select className={inputClass} value={draft.feedback?.scope || "work"} disabled={disabled} onChange={event => update({ feedback: { location: draft.feedback?.location || "", note: draft.feedback?.note || "", scope: event.target.value as NonNullable<Settings["feedback"]>["scope"] } })}><option value="work">本作品</option><option value="sku">此SKU</option><option value="category">品类</option><option value="style">风格</option><option value="general">通用方法候选</option></select></Field><Field label="具体反馈"><textarea data-ai-field="feedback.note" className={inputClass} rows={3} value={draft.feedback?.note || ""} disabled={disabled} onChange={event => update({ feedback: { location: draft.feedback?.location || "", scope: draft.feedback?.scope || "work", note: event.target.value } })} /></Field></div>}
    <div className="flex flex-wrap items-center gap-3"><Button disabled={disabled || !dirty} onClick={() => void save()}>保存制作设置</Button><Button variant="secondary" disabled={busy} onClick={() => { if (!dirty || window.confirm("放弃本地制作设置草稿并载入已保存版本？")) void load(); }}>重新载入</Button><span className="text-xs text-slate-500">主稿与制作设置分别保存。打开步骤不会生成内容。</span></div>{notice && <p role="status" className="text-sm text-emerald-700">{notice}</p>}
  </section>}</FormAssistancePanel>;
}

// Names match studio.video.product-script references/hooks.md.
const HOOKS = ["画面冲击", "悬念提问", "反差对比", "痛点直击", "前后对比", "声音开头", "质疑实测", "身份共鸣", "数字利益", "反常识", "自曝转折", "先认缺点", "淘汰式", "成本拆账", "回应质疑", "跟风确认"];

// Script style, hook and how footage is gathered; the category's own defaults apply to whatever stays on "按品类".
function SalesDirection({ draft, disabled, update }: { draft: Settings; disabled: boolean; update: (patch: Partial<Settings>) => void }) {
  const [styles, setStyles] = useState<{ id: string; name: string; form: string }[]>([]);
  useEffect(() => { let active = true; api.get<{ styles: typeof styles }>("/product-categories").then(value => { if (active) setStyles(value.styles); }).catch(() => undefined); return () => { active = false; }; }, []);
  return <div className="space-y-3 rounded-xl border border-slate-200 p-4"><h4 className="font-medium">带货脚本与出片</h4>
    <div className="grid gap-4 sm:grid-cols-2">
      <Field label="脚本风格"><select aria-label="脚本风格" className={inputClass} value={draft.script_style || ""} disabled={disabled} onChange={event => update({ script_style: event.target.value || null })}><option value="">按品类推荐</option>{styles.map(style => <option key={style.id} value={style.id}>{style.form} · {style.name}</option>)}</select></Field>
      <Field label="开头"><select aria-label="开头" className={inputClass} value={draft.hook_pinned || ""} disabled={disabled} onChange={event => update({ hook_pinned: event.target.value })}><option value="">按品类和素材选</option>{HOOKS.map(hook => <option key={hook} value={hook}>{hook}</option>)}</select></Field>
      <Field label="开头出几个版本"><select aria-label="开头出几个版本" className={inputClass} value={draft.hook_versions || 1} disabled={disabled} onChange={event => update({ hook_versions: Number(event.target.value) })}>{[1, 2, 3].map(count => <option key={count} value={count}>{count} 个</option>)}</select></Field>
      <Field label="出片方式"><select aria-label="出片方式" className={inputClass} value={draft.material_mode || "mixed"} disabled={disabled} onChange={event => update({ material_mode: event.target.value as Settings["material_mode"] })}><option value="mixed">混合补齐：我的素材 → 免费素材 → 图生视频 → AE 模板</option><option value="photo_only">一张图出整片：全部靠图生视频</option><option value="user_footage">给素材剪：只用我的素材</option></select></Field>
      <Field label="图生视频"><select aria-label="图生视频" className={inputClass} value={draft.i2v_mode || "default"} disabled={disabled} onChange={event => update({ i2v_mode: event.target.value as Settings["i2v_mode"] })}><option value="default">跟随设置里的默认</option><option value="manual">手动：我去网页生成</option><option value="auto">自动：MiniMax 生成（按条计费）</option></select></Field>
    </div>
    <Field label="参考爆款结构（可选，只学结构不抄原话）"><textarea aria-label="参考爆款结构" className={inputClass} rows={2} maxLength={4000} value={draft.reference_structure || ""} disabled={disabled} onChange={event => update({ reference_structure: event.target.value })} /></Field>
  </div>;
}

