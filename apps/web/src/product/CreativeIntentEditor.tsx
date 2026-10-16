import { Button, ErrorBanner, Field, inputClass } from "../components/ui";

export type CreativeIntent = Record<string, unknown> & {
  schema: "creative.intent.v1";
  objective?: string;
  why_now?: string;
  audience?: string;
  must_keep?: string[];
  must_avoid?: string[];
  creative_freedom?: string;
  narrative_intent?: string;
  visual_intent?: string;
  audio_intent?: string;
  rationales?: { stable_id: string; reason: string }[];
  human_confirmed_decisions?: { id: string; decision: string }[];
};

const TEXT_FIELDS = ["objective", "why_now", "audience", "creative_freedom", "narrative_intent", "visual_intent", "audio_intent"] as const;
const CONSTRAINT_FIELDS = ["must_keep", "must_avoid"] as const;
const ENTRY_FIELDS = ["rationales", "human_confirmed_decisions"] as const;
const ALLOWED_FIELDS = new Set<string>(["schema", ...TEXT_FIELDS, ...CONSTRAINT_FIELDS, ...ENTRY_FIELDS]);
const STABLE_ID = /^[A-Za-z0-9][A-Za-z0-9_.:-]{0,99}(?![\s\S])/;
const textLength = (value: string) => Array.from(value).length;
const validText = (value: unknown, limit: number, required = false): value is string => typeof value === "string"
  && textLength(value) <= limit && textLength(value.normalize("NFC")) <= limit
  && (!required || !!value.trim()) && !/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/.test(value);

export function creativeIntentIssue(value: CreativeIntent | null): string {
  if (value === null) return "";
  if (!value || typeof value !== "object" || Array.isArray(value) || value.schema !== "creative.intent.v1") return "此创作意图版本暂不支持编辑；已有内容会保留。";
  if (Object.keys(value).some((key) => !ALLOWED_FIELDS.has(key))) return "创作意图含当前服务不支持的扩展字段；已保留，请先核对服务契约。";
  const canonical: Record<string, unknown> = { schema: value.schema };
  for (const field of TEXT_FIELDS) {
    const text = value[field] === undefined ? "" : value[field];
    if (!validText(text, 2000)) return "每项意图文字限 2000 字，不能包含无效控制字符。";
    canonical[field] = text.normalize("NFC").trim();
  }
  for (const field of CONSTRAINT_FIELDS) {
    const items = value[field] === undefined ? [] : value[field];
    if (!Array.isArray(items) || items.length > 40 || items.some((item) => !validText(item, 500, true))) return "必须保留和必须避免各限 40 项，每项须填写且不超过 500 字。";
    canonical[field] = items.map((item) => item.normalize("NFC").trim());
  }
  for (const field of ENTRY_FIELDS) {
    const entries = value[field] === undefined ? [] : value[field];
    const idKey = field === "rationales" ? "stable_id" : "id";
    const textKey = field === "rationales" ? "reason" : "decision";
    if (!Array.isArray(entries) || entries.length > (field === "rationales" ? 100 : 50)) return "创作理由限 100 项，人工确认决定限 50 项。";
    const seen = new Set<string>();
    const normalized = [];
    for (const item of entries) {
      const entry = item as Record<string, unknown>;
      if (!entry || typeof entry !== "object" || Array.isArray(entry) || Object.keys(entry).length !== 2
        || !Object.prototype.hasOwnProperty.call(entry, idKey) || !Object.prototype.hasOwnProperty.call(entry, textKey)
        || !validText(entry[idKey], 100, true) || !STABLE_ID.test(entry[idKey] as string)
        || !validText(entry[textKey], 1000, true)) return "理由须填写稳定 ID 和文字：ID 限 100 个字母、数字或 _ . : -，首位须为字母或数字；文字限 1000 字。";
      const id = entry[idKey] as string;
      if (seen.has(id)) return "同一组创作理由或人工确认决定中的稳定 ID 不能重复。";
      seen.add(id);
      normalized.push({ [idKey]: id, [textKey]: (entry[textKey] as string).normalize("NFC").trim() });
    }
    canonical[field] = normalized;
  }
  if (new TextEncoder().encode(JSON.stringify(canonical)).length > 64 * 1024) return "创作意图总大小不能超过 64 KiB，请缩短文字。";
  return "";
}

export default function CreativeIntentEditor({ value, onChange, readOnly, label = "创作意图" }: {
  value: CreativeIntent | null;
  onChange: (value: CreativeIntent) => void;
  readOnly: boolean;
  label?: string;
}) {
  const issue = creativeIntentIssue(value);
  const unsupported = !!value && (value.schema !== "creative.intent.v1" || Object.keys(value).some((key) => !ALLOWED_FIELDS.has(key)));
  const disabled = readOnly || unsupported;
  function update(patch: Partial<CreativeIntent>) {
    if (!disabled && value) onChange({ ...value, ...patch });
  }
  const preservedText = [
    ["why_now", "为何现在创作"], ["narrative_intent", "叙事意图"],
    ["visual_intent", "视觉意图"], ["audio_intent", "声音意图"],
  ] as const;
  return <section aria-label={label} className="space-y-3 rounded-lg border border-slate-200 p-4">
    <h3 className="font-medium">{label}</h3>
    <p className="text-xs text-slate-500">随内容明确保存为新修订。请记录创作决定，不填写密钥、原始模型输出或整份来源正文。</p>
    {!value ? <div className="space-y-2"><p className="text-sm text-slate-500">此版本未记录创作意图。</p>{!readOnly && <Button variant="secondary" size="sm" onClick={() => onChange({ schema: "creative.intent.v1" })}>记录创作意图</Button>}</div> : <>
      {issue && <ErrorBanner message={issue} />}
      <div className="grid gap-3 sm:grid-cols-2">{([["objective", "创作目标"], ["audience", "面向谁"], ["creative_freedom", "允许自由发挥的范围"]] as const).map(([field, title]) => <Field key={field} label={title} hint="最多 2000 字"><textarea data-ai-field={`intent.${field}`} aria-label={`${label} · ${title}`} className={inputClass} rows={3} maxLength={2000} value={typeof value[field] === "string" ? value[field] : ""} disabled={disabled} onChange={(event) => update({ [field]: event.target.value })} /></Field>)}</div>
      <div className="grid gap-4 sm:grid-cols-2">{CONSTRAINT_FIELDS.map((field) => {
        const title = field === "must_keep" ? "必须保留" : "必须避免";
        const items = Array.isArray(value[field]) ? value[field] : [];
        return <div key={field} className="space-y-2"><h4 className="text-sm font-medium">{title} · {items.length}/40</h4>{items.map((text, index) => <div key={index} className="flex items-start gap-2"><textarea aria-label={`${label} · ${title} ${index + 1}`} className={inputClass} rows={2} maxLength={500} value={text} disabled={disabled} onChange={(event) => update({ [field]: items.map((item, at) => at === index ? event.target.value : item) })} /><Button size="sm" variant="secondary" disabled={disabled} onClick={() => update({ [field]: items.filter((_, at) => at !== index) })}>移除第 {index + 1} 项</Button></div>)}<Button size="sm" variant="secondary" disabled={disabled || items.length >= 40} onClick={() => update({ [field]: [...items, ""] })}>添加{title}</Button><p className="text-xs text-slate-500">每项最多 500 字。</p></div>;
      })}</div>
      <div className="space-y-2"><h4 className="text-sm font-medium">创作理由 · {value.rationales?.length || 0}/100</h4><p className="text-xs text-slate-500">使用已有区块、场景、镜头或素材槽位的稳定 ID。</p>{(value.rationales || []).map((entry, index) => <div key={index} className="grid gap-2 rounded bg-slate-50 p-3 sm:grid-cols-[1fr_2fr_auto]"><Field label="稳定 ID"><input aria-label={`${label} · 理由 ${index + 1} 稳定 ID`} className={inputClass} maxLength={100} value={entry.stable_id} disabled={disabled} onChange={(event) => update({ rationales: value.rationales!.map((item, at) => at === index ? { ...item, stable_id: event.target.value } : item) })} /></Field><Field label="为什么这样处理"><textarea aria-label={`${label} · 理由 ${index + 1} 文字`} className={inputClass} rows={2} maxLength={1000} value={entry.reason} disabled={disabled} onChange={(event) => update({ rationales: value.rationales!.map((item, at) => at === index ? { ...item, reason: event.target.value } : item) })} /></Field><Button size="sm" variant="secondary" disabled={disabled} onClick={() => update({ rationales: value.rationales!.filter((_, at) => at !== index) })}>移除理由 {index + 1}</Button></div>)}<Button size="sm" variant="secondary" disabled={disabled || (value.rationales?.length || 0) >= 100} onClick={() => update({ rationales: [...(value.rationales || []), { stable_id: "", reason: "" }] })}>添加创作理由</Button></div>
      {(preservedText.some(([field]) => !!value[field]) || !!value.human_confirmed_decisions?.length) && <details className="text-sm text-slate-600"><summary className="cursor-pointer">已记录的其他意图（随修订保留）</summary><div className="mt-2 space-y-2">{preservedText.map(([field, title]) => value[field] ? <p key={field} className="whitespace-pre-wrap">{title}：{value[field]}</p> : null)}{value.human_confirmed_decisions?.map((entry) => <p key={entry.id} className="whitespace-pre-wrap">人工确认 · {entry.id}：{entry.decision}</p>)}</div></details>}
    </>}
  </section>;
}
