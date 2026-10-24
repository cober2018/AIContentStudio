import { useEffect, useState } from "react";
import { api } from "../api";
import { Button, Field, inputClass } from "../components/ui";
import { stageValue, type StageContract, type StageFieldSchema, type StageMethod, type StageMethods, type StageMethodSelection } from "./creationRecipeState";

// Stage contracts name parameters by machine key; readers need plain words.
const FIELD_LABELS: Record<string, string> = {
  instruction: "补充说明", length: "篇幅", candidate_count: "候选数量", tone: "语气", audience: "读者", angle: "角度", format: "格式",
  voice: "音色", rate: "语速", style: "风格", count: "数量", max_items: "最多条数", language: "语言", aspect: "画幅", duration_seconds: "时长（秒）",
  fact_mode: "事实模式", evidence_mode: "证据模式", shot_count: "镜头数", density: "信息密度", title: "标题", hook: "开头钩子",
};
export function fieldLabel(key: string) { return FIELD_LABELS[key] || key.replace(/_/g, " "); }

export function TypedStageField({ label, schema, value, disabled, onChange }: {
  label: string; schema: StageFieldSchema; value: unknown; disabled: boolean; onChange: (value: unknown) => void;
}) {
  const enumLabels: Record<string, string> = { grounded: "既有证据内创作", current: "当前事实（须有新来源）", reflection: "个人观察与感悟", speculation: "明确标注的推测", short: "短", medium: "中", long: "长" };
  if (schema.enum) return <Field label={label}><select className={inputClass} disabled={disabled} value={value == null ? "" : String(value)} onChange={event => onChange(schema.enum?.find(item => String(item) === event.target.value))}><option value="">请选择</option>{schema.enum.map(item => <option key={String(item)} value={item}>{enumLabels[String(item)] || item}</option>)}</select></Field>;
  if (schema.type === "boolean") return <Field label={label}><select className={inputClass} disabled={disabled} value={value === undefined ? "" : String(value)} onChange={event => onChange(event.target.value === "" ? undefined : event.target.value === "true")}><option value="">未设置</option><option value="true">开启</option><option value="false">关闭</option></select></Field>;
  if (schema.type === "integer" || schema.type === "number") return <Field label={label}><input className={inputClass} type="number" step={schema.type === "integer" ? 1 : "any"} min={schema.minimum} max={schema.maximum} disabled={disabled} value={value == null ? "" : String(value)} onChange={event => { const next = event.target.value === "" ? undefined : Number(event.target.value); if (next === undefined || Number.isFinite(next)) onChange(next); }} /></Field>;
  if (schema.type === "object") {
    const object = value && typeof value === "object" && !Array.isArray(value) ? value as Record<string, unknown> : {};
    return <fieldset className="space-y-3 rounded-[14px] border border-ink-200 p-4" disabled={disabled}><legend className="px-1.5 text-[13px] font-medium text-ink-800">{label}</legend>{Object.entries(schema.properties || {}).map(([key, child]) => <TypedStageField key={key} label={(child as { title?: string }).title || fieldLabel(key)} schema={child} value={object[key] ?? child.default} disabled={disabled} onChange={next => { const copy = { ...object }; if (next === undefined) delete copy[key]; else copy[key] = next; onChange(copy); }} />)}</fieldset>;
  }
  if (schema.type === "array" && schema.items) {
    const rows = Array.isArray(value) ? value : [];
    return <fieldset className="space-y-2 rounded-lg border p-3" disabled={disabled}><legend className="px-1 text-sm font-medium">{label}</legend>{rows.map((item, index) => <div key={index} className="flex items-end gap-2"><div className="min-w-0 flex-1"><TypedStageField label={`${label} ${index + 1}`} schema={schema.items!} value={item} disabled={disabled} onChange={next => onChange(rows.map((row, at) => at === index ? next : row))} /></div><Button size="sm" variant="secondary" disabled={disabled || rows.length <= (schema.minItems || 0)} onClick={() => onChange(rows.filter((_, at) => at !== index))}>移除</Button></div>)}<Button size="sm" variant="secondary" disabled={disabled || rows.length >= (schema.maxItems ?? 0)} onClick={() => onChange([...rows, schema.items?.default ?? (schema.items?.type === "object" ? {} : schema.items?.type === "string" ? "" : schema.items?.type === "boolean" ? false : schema.items?.minimum ?? 0)])}>添加一项</Button></fieldset>;
  }
  if (schema.type !== "string") return <p className="text-xs text-slate-500">{label} 当前由已保存的配置决定。</p>;
  return <Field label={label}><textarea className={`${inputClass} min-h-20`} minLength={schema.minLength} maxLength={schema.maxLength} disabled={disabled} value={value == null ? "" : String(value)} onChange={event => onChange(event.target.value)} /></Field>;
}

function methodKey(selection: StageMethodSelection) {
  return selection.source_kind === "capability_memory" ? `${selection.source_kind}:${selection.artifact_id}:${selection.revision_id}`
    : selection.source_kind === "installed_agent_skill" ? `${selection.source_kind}:${selection.skill_id}:${selection.version}:${selection.runtime_key}:${selection.runtime_version}`
    : `${selection.source_kind}:${selection.key}:${selection.version}`;
}

function methodConfig(selection: StageMethodSelection) {
  if (selection.source_kind !== "capability_memory") return selection;
  const { arguments: args, ...reference } = selection;
  return { ...reference, arguments_json: JSON.stringify(args || {}) };
}

export default function StageContractControls({ base, nodeId, contract, baseConfig, override, disabled, mode = "run", hiddenFields = [], onChange }: {
  base: string; nodeId: string; contract: StageContract; baseConfig: Record<string, unknown>;
  override: Record<string, unknown>; disabled: boolean; mode?: "run" | "authored"; hiddenFields?: string[]; onChange: (field: string, value: unknown) => void;
}) {
  const variantStage = contract.stage_schema === "stage.variant.adapt.v1";
  const [variantInventory, setVariantInventory] = useState<{ targets: { channel: string; content_form: string }[]; channels: { channel: string; label: string; content_forms: { content_form: string; label: string }[] }[]; accounts: { id: number; name: string; status: string; persona_id: number; platform_channel?: string | null }[]; bindings: { account_id: number; content_form: string; enabled: boolean }[] } | null>(null);
  const [variantError, setVariantError] = useState("");
  const [inventory, setInventory] = useState<StageMethods | null>(null);
  const [error, setError] = useState("");
  const [refresh, setRefresh] = useState(0);
  const fields = (contract.tunable_fields || []).filter(field => !hiddenFields.includes(field)
    || baseConfig[field] !== undefined || override[field] !== undefined);
  const needsInventory = fields.some(field => field === "model_profile_id" || field === "profile_id" || field === "selected_profile" || contract.ui_schema?.[field]?.control === "method");
  useEffect(() => {
    let alive = true;
    setInventory(null); setError("");
    if (!needsInventory) return;
    api.get<StageMethods>(`${base}/creation-recipe/methods`).then(value => {
      if (!Array.isArray(value.model_profiles) || !Array.isArray(value.methods)) throw new Error("方法清单格式不完整。");
      if (alive) setInventory(value);
    }).catch(() => { if (alive) setError("模型和方法清单暂不可用，请刷新清单后选择。"); });
    return () => { alive = false; };
  }, [base, needsInventory, refresh]);
  useEffect(() => {
    let alive = true;
    setVariantInventory(null); setVariantError("");
    if (!variantStage) return;
    Promise.all([
      api.get<{ persona_id: number; series_id: number | null }>(base),
      api.get<{ items: { channel: string; content_form: string }[] }>(`${base}/channel-variants/capabilities`),
      api.get<{ channel: string; label: string; content_forms: { content_form: string; label: string }[] }[]>("/channels"),
    ]).then(async ([unit, targets, channels]) => {
      const [accounts, bindings] = await Promise.all([
        api.get<{ id: number; name: string; status: string; persona_id: number; platform_channel?: string | null }[]>(`/content-personas/${unit.persona_id}/accounts`),
        unit.series_id ? api.get<{ account_id: number; content_form: string; enabled: boolean }[]>(`/content-series/${unit.series_id}/targets`) : Promise.resolve([]),
      ]);
      if (alive) setVariantInventory({ targets: targets.items, channels, accounts: accounts.filter(account => account.persona_id === unit.persona_id), bindings });
    }).catch(() => { if (alive) setVariantError("渠道形态和目标账号清单暂不可用，请刷新后选择；已保存的配置仍保留。"); });
    return () => { alive = false; };
  }, [base, variantStage, refresh]);
  const selectedChannel = String(override.channel_id ?? baseConfig.channel_id ?? "");
  const selectedForm = String(override.content_form ?? baseConfig.content_form ?? "");
  function variantKey(channel: string, form: string, account?: unknown) { return `${channel}.${form}.${account ? `account-${account}` : "primary"}`; }
  const methods: StageMethod[] = (inventory?.methods || []).filter(item => item.selection
    && contract.method_sources?.includes(item.source_kind)
    && (!item.applicable_node_ids || item.applicable_node_ids.includes(nodeId)));

  return <div className="mt-3 space-y-3">{fields.map(field => {
    const schema = contract.config_schema?.properties?.[field];
    if (!schema) return null;
    const label = contract.ui_schema?.[field]?.label || field;
    const current = override[field];
    const effective = current === undefined ? baseConfig[field] ?? schema.default : current;
    const hint = `已保存：${stageValue(baseConfig[field] ?? schema.default)} · ${current === undefined ? "当前继承" : mode === "authored" ? "人工拟保存，尚未实测" : "仅本次调整"}`;
    let control;
    if (variantStage && (field === "channel_id" || field === "content_form")) {
      const catalog = variantInventory?.targets || [];
      const values = field === "channel_id" ? Array.from(new Set(catalog.map(target => target.channel))) : catalog.filter(target => target.channel === selectedChannel).map(target => target.content_form);
      const chosen = String(effective ?? "");
      control = <Field label={label} hint={hint}><select aria-label={`阶段 ${label}`} className={inputClass} disabled={disabled || !variantInventory} value={chosen} onChange={event => {
        const next = event.target.value;
        onChange(field, next || undefined);
        onChange("target_account_id", 0);
        if (field === "channel_id") {
          const form = catalog.find(target => target.channel === next)?.content_form;
          onChange("content_form", form);
          if (next && form) onChange("variant_key", variantKey(next, form));
        } else if (next && selectedChannel) onChange("variant_key", variantKey(selectedChannel, next));
      }}><option value="">请选择</option>{chosen && !values.includes(chosen) && <option value={chosen} disabled>{chosen} · 当前目录不可用（保留原值）</option>}{values.map(value => { const channel = variantInventory?.channels.find(item => item.channel === (field === "channel_id" ? value : selectedChannel)); return <option key={value} value={value}>{field === "channel_id" ? channel?.label || value : channel?.content_forms.find(item => item.content_form === value)?.label || value} · {value}</option>; })}</select></Field>;
    } else if (variantStage && field === "target_account_id") {
      const accounts = variantInventory?.accounts.filter(account => account.status === "active" && account.platform_channel === selectedChannel) || [];
      const chosen = effective == null || effective === 0 ? "" : String(effective);
      control = <Field label="目标投放账号（与来源创作账号分别选择）" hint={hint}><select aria-label="阶段目标投放账号" className={inputClass} disabled={disabled || !variantInventory} value={chosen} onChange={event => {
        const next = Number(event.target.value) || 0;
        onChange(field, next);
        if (selectedChannel && selectedForm) onChange("variant_key", variantKey(selectedChannel, selectedForm, next));
      }}><option value="">仅渠道适配 · 未选目标账号</option>{chosen && !accounts.some(account => String(account.id) === chosen) && <option value={chosen} disabled>当前账号不属于此角色/平台（保留原值）</option>}{accounts.map(account => <option key={account.id} value={account.id} disabled={variantInventory?.bindings.some(binding => binding.account_id === account.id && binding.content_form === selectedForm && !binding.enabled)}>{account.name} · #{account.id}</option>)}</select><p className="mt-1 text-xs text-slate-500">按服务端角色与平台筛选。选择“仅渠道适配”会明确清除已保存的目标账号。选择账号后使用独立版本标识；接受与审核仍须明确确认。</p></Field>;
    } else if (field === "selected_profile") {
      const capability = String(override.capability ?? baseConfig.capability ?? "");
      const profiles = inventory?.media_profiles?.filter(profile => profile.capabilities?.[capability]?.declared) || [];
      control = <Field label={label} hint={`${hint} · 能力：${capability}`}><select className={inputClass} disabled={disabled || !inventory} value={current === undefined ? "" : String(current)} onChange={event => onChange(field, event.target.value || undefined)}><option value="">使用已保存的媒体配置</option>{current !== undefined && !profiles.some(profile => profile.id === current) && <option value={String(current)} disabled>当前媒体配置不支持所选能力</option>}{profiles.map(profile => { const state = profile.capabilities?.[capability]; return <option key={profile.id} value={profile.id} disabled={!profile.available || state?.configured !== true || state.executable !== true}>{profile.label} · {state?.provider || profile.provider || "未配置"} / {state?.model || profile.model || "未配置"} · {state?.state}{state?.reason ? ` · ${state.reason}` : ""}</option>; })}</select><p className="mt-1 text-xs text-slate-500">配置声明和可用性供选择参考，不代表真实生成已验收；实际执行路由以阶段预览为准。</p></Field>;
    } else if (field === "model_profile_id" || field === "profile_id") {
      control = <Field label={label} hint={hint}><select className={inputClass} disabled={disabled || !inventory} value={current === undefined ? "" : String(current)} onChange={event => onChange(field, event.target.value || undefined)}><option value="">使用已保存的模型配置</option>{inventory?.model_profiles.map(profile => { const id = profile.profile_id || profile.id; return id ? <option key={id} value={id} disabled={profile.available === false || profile.executable === false}>{profile.label || id}{profile.provider || profile.model ? ` · ${profile.provider || ""} / ${profile.model || ""}` : ""}{profile.reason ? ` · ${profile.reason}` : ""}</option> : null; })}</select></Field>;
    } else if (contract.ui_schema?.[field]?.control === "method") {
      const chosen = effective as (StageMethodSelection & { arguments_json?: string }) | undefined;
      const chosenKey = chosen?.source_kind ? methodKey(chosen) : "";
      const selected = methods.find(item => methodKey(item.selection) === chosenKey);
      const argsSchema = selected?.arguments_schema || selected?.args_schema;
      let argumentsValue: Record<string, unknown> = chosen?.source_kind === "capability_memory" ? chosen.arguments || {} : {};
      if (chosen?.arguments_json) {
        try { argumentsValue = JSON.parse(chosen.arguments_json); } catch { argumentsValue = {}; }
      }
      control = <div><Field label={label} hint={hint}><select className={inputClass} disabled={disabled || !inventory} value={current === undefined ? "" : chosenKey} onChange={event => { const method = methods.find(item => methodKey(item.selection) === event.target.value); onChange(field, method ? methodConfig(method.selection) : undefined); }}><option value="">使用已保存的方法</option>{current !== undefined && !selected && <option value={chosenKey} disabled>当前固定方法版本（不在可用清单中）</option>}{methods.map(item => <option key={methodKey(item.selection)} value={methodKey(item.selection)} disabled={item.available === false || item.executable === false}>{item.label || item.name || methodKey(item.selection)} · {item.source_kind} · {item.scope_type || "固定来源"}{item.reason ? ` · ${item.reason}` : ""}</option>)}</select></Field>{selected?.selection.source_kind === "capability_memory" && <p className="mt-1 text-xs text-slate-500">方法 #{selected.selection.artifact_id} · 精确版本 #{selected.selection.revision_id} · {stageValue(selected.matched_scope || selected.scope)}</p>}{selected?.selection.source_kind === "capability_memory" && argsSchema?.properties && Object.keys(argsSchema.properties).length > 0 && <div className="mt-2"><TypedStageField label={mode === "authored" ? "方法参数（拟保存）" : "方法参数（仅本次）"} schema={argsSchema} value={argumentsValue} disabled={disabled} onChange={value => onChange(field, { source_kind: "capability_memory", artifact_id: selected.selection.source_kind === "capability_memory" ? selected.selection.artifact_id : undefined, revision_id: selected.selection.source_kind === "capability_memory" ? selected.selection.revision_id : undefined, arguments_json: JSON.stringify(value) })} /></div>}</div>;
    } else control = <div><TypedStageField label={label} schema={schema} value={effective} disabled={disabled} onChange={value => onChange(field, value)} /><p className="mt-1 text-xs text-slate-500">{hint}</p></div>;
    return <div key={field}>{control}<button type="button" className="mt-1 text-xs text-indigo-600 disabled:text-slate-400" disabled={disabled || current === undefined} onClick={() => onChange(field, undefined)}>恢复已保存配置</button></div>;
  })}{variantError && <p className="rounded bg-amber-50 p-3 text-xs text-amber-800" role="status">{variantError}<Button size="sm" variant="secondary" onClick={() => setRefresh(value => value + 1)}>刷新渠道与账号</Button></p>}{inventory?.installed_skills?.length ? <details className="rounded-lg bg-slate-50 p-3 text-xs"><summary>已安装 Skills 库存（只读）</summary>{inventory.installed_skills.map(skill => <p key={`${skill.id}:${skill.version}`} className="mt-2">{skill.name || skill.id} · {skill.version} · {skill.reason || "库存不代表已验证的阶段执行绑定"}</p>)}</details> : null}{error && <div className="rounded-lg bg-amber-50 p-3 text-xs text-amber-800" role="status">{error}<Button size="sm" variant="secondary" onClick={() => setRefresh(value => value + 1)}>刷新模型与方法</Button></div>}{contract.supports_run_override !== true && <p className="text-xs text-slate-500">此阶段不支持本次调节；参数以固定流程版本为准。</p>}</div>;
}
