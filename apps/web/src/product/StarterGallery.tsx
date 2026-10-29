import { useEffect, useState } from "react";
import { api, ApiError, currentUser } from "../api";
import { Button, ErrorBanner, Field, inputClass } from "../components/ui";

type Catalog = { starter_personas: { key: string; name: string }[] };
type CreativeProfile = { mode: "auto" | "custom" | "composed"; skill_ref: string; style_preset_ref: string;
  quality_profile_ref: string; model_binding?: unknown; model_chain?: unknown[]; capability_memory_revision_ids?: number[] };
type Readiness = { persona_id: number; creative_root: { scope: string; id: number }; readiness_hash: string;
  modalities: Record<string, { status: "ready" | "partial" | "blocked"; reasons: string[];
    profile: CreativeProfile | null; profile_source: string | null; profile_revision_id: number | null;
    selected_binding: unknown; declared_chain: unknown; fallback_reason: string | null;
    recipe: { source: string; workflow_id?: number; workflow_version?: number; binding_revision?: number; checksum: string } | null }> };
const MODALITIES = { text: "文字", graphic: "图文", video: "视频" };
const MODES = { auto: "Auto", custom: "Custom", composed: "Custom Composition" };
const STATES = { ready: "配置可开始", partial: "部分就绪", blocked: "阻断" };
const REASONS: Record<string, string> = {
  creative_profile_missing: "本级无有效创作配置（含显式清空）。",
  default_recipe_unavailable: "没有可用的精确默认流程。",
  identity_archived: "所选身份或祖先已归档，只能查看。",
  graphic_render_scope_requires_project_master: "真实图文渲染需项目 Master 和精确 renderer scope。",
  external_video_execution_required: "视频默认流程只准备导演包，最终成片需外部执行。",
  planning_chat_unavailable: "视觉规划的独立 Chat 配置不可用。",
  mock_provider_contract_only: "Mock 只证明合同，不代表真实模型就绪。",
};

export function PersonaReadinessPanel({ personaId, accountId, seriesId, refreshRevision }: {
  personaId: number; accountId?: number | null; seriesId?: number | null; refreshRevision?: number;
}) {
  const [value, setValue] = useState<Readiness | null>(null);
  const [error, setError] = useState("");
  const actor = currentUser();
  useEffect(() => {
    let alive = true; setValue(null); setError("");
    const params = new URLSearchParams({ persona_id: String(personaId) });
    if (accountId) params.set("account_id", String(accountId));
    if (seriesId) params.set("series_id", String(seriesId));
    api.get<Readiness>(`/content-identities/starter-readiness?${params}`)
      .then(result => { if (alive && currentUser() === actor) setValue(result); })
      .catch(cause => { if (alive && currentUser() === actor) setError(errorText(cause)); });
    return () => { alive = false; };
  }, [personaId, accountId, seriesId, refreshRevision, actor]);
  return <section aria-label="角色创作就绪状态" className="mt-4 rounded-xl border border-slate-200 p-4">
    <h3 className="font-medium">角色创作就绪状态</h3>
    <p className="mt-1 text-xs text-slate-500">只读配置投影，不调用 Provider，不代表成品或人工质量验收。</p>
    {error ? <ErrorBanner message={error} /> : !value ? <p className="mt-2 text-sm">读取中…</p> : <>
      <p className="mt-2 text-sm">创作根：{value.creative_root.scope} #{value.creative_root.id}</p>
      <div className="mt-3 grid gap-3 md:grid-cols-2">{Object.entries(value.modalities).map(([key, item]) => <div key={key} className="rounded-lg bg-slate-50 p-3">
        <p className="font-medium">{MODALITIES[key as keyof typeof MODALITIES] || key} · {STATES[item.status]}</p>
        <p className="mt-1 text-xs">来源：{item.profile_source || "未设置"} · Revision #{item.profile_revision_id ?? "无"} · {item.profile ? MODES[item.profile.mode] : "无有效配置"}</p>
        {item.profile && <><p className="mt-2 break-all text-xs">Skill：{item.profile.skill_ref}<br />Preset：{item.profile.style_preset_ref}<br />Quality：{item.profile.quality_profile_ref}</p>
          <p className="mt-2 text-xs">有序方法 revisions：{JSON.stringify(item.profile.capability_memory_revision_ids || [])}</p></>}
        <p className="mt-2 break-all text-xs">实际 binding：{JSON.stringify(item.selected_binding)}<br />声明 chain：{JSON.stringify(item.declared_chain)}<br />fallback：{item.fallback_reason || "无"}</p>
        <p className="mt-2 break-all text-xs">默认流程：{item.recipe ? `${item.recipe.source} · Workflow #${item.recipe.workflow_id ?? "未绑定"} @${item.recipe.workflow_version ?? "内置"} · ${item.recipe.checksum}` : "无"}</p>
        {item.reasons.length > 0 && <ul className="mt-2 space-y-1 text-xs">{item.reasons.map(reason => <li key={reason}>{REASONS[reason] || "此配置尚不可用。"} <code>{reason}</code></li>)}</ul>}
      </div>)}</div>
    </>}
  </section>;
}

function errorText(error: unknown) {
  return error instanceof ApiError ? `${error.status} · ${error.message}` : "创作配置读取失败。";
}

export default function StarterPersonaGallery({ onInitialized, personaId, accountId, seriesId, refreshRevision, readOnly = false }: {
  onInitialized: (personaId: number) => Promise<void>; personaId?: number | null;
  accountId?: number | null; seriesId?: number | null; refreshRevision?: number; readOnly?: boolean;
}) {
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [preview, setPreview] = useState<any>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [forkName, setForkName] = useState("");
  const [forkConfirmed, setForkConfirmed] = useState(false);
  const [createdPersonaId, setCreatedPersonaId] = useState<number | null>(null);
  const readinessPersonaId = personaId === undefined ? createdPersonaId : personaId;
  useEffect(() => { let alive = true; api.get<Catalog>("/content-identities/creative-catalog")
    .then(value => { if (alive) setCatalog(value); }).catch(cause => { if (alive) setError(errorText(cause)); });
    return () => { alive = false; }; }, []);
  async function showPreview(key: string) {
    setBusy(true); setError(""); setPreview(null); setForkName(""); setForkConfirmed(false);
    try { setPreview(await api.post("/content-identities/starter-preview", { blueprint_key: key })); }
    catch (cause) { setError(errorText(cause)); } finally { setBusy(false); }
  }
  async function initialize(fork = false) {
    if (!preview || busy || readOnly || (fork && (!forkConfirmed || !forkName.trim() || forkName.trim() === preview.name))) return;
    setBusy(true); setError("");
    try {
      const result = await api.post<{ persona_id: number }>(fork ? "/content-identities/starter-fork" : "/content-identities/starter-apply", {
        blueprint_key: preview.blueprint, ...(fork ? { name: forkName.trim(), expected_profile_checksum: preview.profile_checksum } : {}),
      });
      setCreatedPersonaId(result.persona_id); setPreview(null); await onInitialized(result.persona_id);
    } catch (cause) { setError(errorText(cause)); } finally { setBusy(false); }
  }
  return <section aria-label="内置创作角色" className="mb-5 rounded-2xl border border-indigo-100 bg-white p-5">
    <h2 className="font-semibold">从内置创作角色开始</h2><p className="mt-1 text-sm text-slate-500">预览不写入。初始化保持幂等；明确 Fork 才创建自定义命名的新角色，不修改原角色。配置就绪与真实成品质量验收分开。</p>
    <div className="mt-3 grid gap-3 md:grid-cols-2">{catalog?.starter_personas.map(item => <div key={item.key} className="rounded-xl bg-slate-50 p-4">
      <p className="font-medium">{item.name}</p><p className="mt-1 text-xs text-slate-500">{item.key}</p>
      <Button className="mt-3" variant="secondary" disabled={busy} onClick={() => showPreview(item.key)}>预览{item.name}</Button>
    </div>)}</div>
    {preview && <div className="mt-4 rounded-xl border border-indigo-200 p-4"><p className="font-medium">{preview.name} · 蓝图预览</p>
      <p className="mt-2 text-sm text-slate-600">{preview.profile.positioning}</p><p className="mt-2 text-xs text-slate-500">文字默认流程：证据 → 角度 → 大纲 → 初稿 → 检查 → 精修 → 标题 → 最终稿。其他形态配置不代表已验收。</p>
      <p className="mt-2 break-all text-xs">蓝图 {preview.blueprint} @{preview.version} · checksum {preview.profile_checksum}</p>
      <div className="mt-2 grid gap-2 md:grid-cols-2">{Object.entries(MODALITIES).map(([key, label]) => {
        const profile = preview.profile[`${key}_creative_profile`] as CreativeProfile;
        return <p key={key} className="break-all text-xs">{label} · 创作根 Persona · {MODES[profile.mode]}<br />{profile.skill_ref}<br />{profile.style_preset_ref}<br />{profile.quality_profile_ref}</p>;
      })}</div>
      <div className="mt-3 flex gap-2"><Button disabled={busy || readOnly} onClick={() => initialize()}>{busy ? "处理中…" : "确认初始化此角色"}</Button><Button variant="secondary" disabled={busy} onClick={() => setPreview(null)}>取消</Button></div>
      <div className="mt-4 border-t border-slate-200 pt-3"><Field label="Fork 为新角色（不覆盖原角色）"><input className={inputClass} maxLength={200} value={forkName} disabled={busy || readOnly} onChange={event => { setForkName(event.target.value); setForkConfirmed(false); }} /></Field>
        <label className="mt-2 flex gap-2 text-xs"><input type="checkbox" checked={forkConfirmed} disabled={busy || readOnly} onChange={event => setForkConfirmed(event.target.checked)} />确认将此 exact 蓝图完整复制为当前用户的新 Persona 及独立默认流程。</label>
        <Button className="mt-2" variant="secondary" disabled={busy || readOnly || !forkConfirmed || !forkName.trim() || forkName.trim() === preview.name} onClick={() => initialize(true)}>明确 Fork 新角色</Button></div>
    </div>}{error && <div className="mt-3"><ErrorBanner message={error} /></div>}
    {readinessPersonaId && <PersonaReadinessPanel key={`${readinessPersonaId}:${accountId || ""}:${seriesId || ""}`} personaId={readinessPersonaId} accountId={personaId ? accountId : null} seriesId={personaId ? seriesId : null} refreshRevision={refreshRevision} />}
  </section>;
}
