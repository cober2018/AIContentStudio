import { ErrorBanner, inputClass } from "../components/ui";

type Payload = Record<string, unknown>;
type TextField = { key: string; label: string; limit: number; required?: boolean; collection?: string; index?: number; locationId?: string; locked?: boolean };
const normalize = (text: string) => text.replace(/\r\n?/g, "\n").normalize("NFC");

function fieldsFor(schema: string, payload: Payload): TextField[] {
  const fields: TextField[] = [];
  function rows(collection: string, build: (row: Payload, index: number) => TextField[]) {
    for (const [index, row] of (payload[collection] as Payload[]).entries()) {
      fields.push(...build(row, index).map(field => ({ ...field, collection, index })));
    }
  }
  if (schema === "wechat.article.v1") {
    fields.push({ key: "title", label: "公众号标题", limit: 200, required: true });
    rows("blocks", row => [
      { key: "text", label: `${row.kind === "image" ? "图片图注" : "公众号正文"} · ${row.id}`, limit: row.kind === "image" ? 2000 : 10000, required: row.kind !== "image", locationId: String(row.id), locked: "html_template" in payload },
      ...(row.kind === "image" ? [{ key: "alt_text", label: `图片替代文字 · ${row.id}`, limit: 2000, locked: "html_template" in payload }] : []),
    ]);
    if ("html_template" in payload) fields.push(
      { key: "digest", label: "公众号摘要", limit: 120 },
      { key: "author", label: "公众号署名", limit: 16 },
    );
  } else if (schema === "x.thread.v1") {
    rows("posts", row => [{ key: "text", label: `X 推串正文 · ${row.id}`, limit: 280, required: true, locationId: String(row.id) }]);
  } else if (schema === "x.single.v1") {
    fields.push({ key: "text", label: "X 单条正文", limit: 280, required: true, locationId: "single" });
  } else if (schema === "xiaohongshu.image_note.v1") {
    fields.push({ key: "title", label: "小红书标题", limit: 200, required: true });
    rows("cards", row => [{ key: "caption", label: `小红书图文文案 · ${row.id}`, limit: 500, locationId: String(row.id) }]);
  } else if (schema === "douyin.spoken_script.v1") {
    rows("scenes", row => [
      { key: "script", label: `口播脚本 · ${row.id}`, limit: 10000, required: true, locationId: String(row.id) },
      { key: "voice_text", label: `配音文字 · ${row.id}`, limit: 10000, required: true },
    ]);
    if ("estimated_srt" in payload) fields.push({ key: "text", label: "估算字幕 SRT", limit: 20000, collection: "estimated_srt" });
  }
  return fields;
}

function fieldValue(payload: Payload, field: TextField): string {
  if (!field.collection) return payload[field.key] as string;
  const container = field.index === undefined ? payload[field.collection] as Payload : (payload[field.collection] as Payload[])[field.index];
  return container[field.key] as string;
}

export function variantBodyIssue(schema: string, payload: Payload): string {
  const fields = fieldsFor(schema, payload);
  if (!fields.length) return "此正文版本暂不支持编辑。";
  const locations = new Map<string, string>();
  for (const field of fields) {
    const raw = fieldValue(payload, field);
    if (typeof raw !== "string") return `${field.label}须为文字。`;
    const text = normalize(raw);
    const characters = Array.from(text);
    if (characters.length > field.limit || field.required && !text.trim()) return `${field.label}${field.required ? "须填写，" : ""}最多 ${field.limit} 字。`;
    if (/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/.test(text) || characters.some(character => {
      const point = character.codePointAt(0)!;
      return point >= 0xd800 && point <= 0xdfff;
    })) return `${field.label}含无效字符，请修改后保存。`;
    if (field.locationId) locations.set(field.locationId, text);
  }
  for (const citation of (payload.citations || []) as Payload[]) {
    const locator = citation.locator as { start: number; end: number };
    const text = locations.get(citation.location_id as string);
    if (text === undefined || locator.end > Array.from(text).length) return `引用 ${citation.id} 的文字范围已超出正文；请恢复足够长度的正文，引用位置不会自动改变。`;
  }
  if (new TextEncoder().encode(JSON.stringify(payload)).length > 2_000_000) return "正文总大小不能超过 2 MB。";
  return "";
}

export default function ChannelVariantForm({ schema, value, readOnly, onChange }: {
  schema: string; value: Payload; readOnly: boolean; onChange: (value: Payload) => void;
}) {
  const fields = fieldsFor(schema, value);
  const issue = variantBodyIssue(schema, value);
  function update(field: TextField, text: string) {
    if (readOnly || field.locked) return;
    if (!field.collection) onChange({ ...value, [field.key]: text });
    else if (field.index === undefined) onChange({ ...value, [field.collection]: { ...value[field.collection] as Payload, [field.key]: text } });
    else onChange({ ...value, [field.collection]: (value[field.collection] as Payload[]).map((row, index) => index === field.index ? { ...row, [field.key]: text } : row) });
  }
  return <section aria-label="Variant 正文编辑" className="space-y-3 rounded-lg border border-slate-200 p-4">
    <h3 className="font-medium">渠道正文</h3>
    <p className="text-xs text-slate-500">编辑文字后明确保存为新修订；段落、卡片和镜头的 ID、顺序、素材槽、引用与声明随修订保留。</p>
    {"html_template" in value && <p className="text-xs text-amber-700">此文章保留原始 HTML，正文块与模板须一致，因此正文块只读；标题、摘要和署名仍可编辑。</p>}
    {issue && <ErrorBanner message={issue} />}
    {fields.map(field => {
      const text = fieldValue(value, field);
      const row = field.collection && field.index !== undefined ? (value[field.collection] as Payload[])[field.index] : null;
      return <label key={`${field.collection || "root"}.${field.index ?? ""}.${field.key}`} className="block text-sm">
        {field.label}<span className="ml-2 text-xs text-slate-500">{Array.from(normalize(text)).length}/{field.limit} 字{field.required ? " · 必填" : ""}</span>
        <textarea aria-label={field.label} className={`${inputClass} mt-1 min-h-24`} value={text} readOnly={readOnly || field.locked} onChange={event => update(field, event.target.value)} />
        {row && <span className="mt-1 block text-xs text-slate-500">顺序 {String(row.order) + " · ID " + String(row.id)}{row.image_ref_key ? ` · 图片槽 ${row.image_ref_key}` : ""}{Array.isArray(row.b_roll_ref_keys) ? ` · B-roll ${(row.b_roll_ref_keys as string[]).join("、") || "无"}` : ""}</span>}
      </label>;
    })}
    <details className="text-xs text-slate-600"><summary className="cursor-pointer">保留的引用与声明（只读）</summary>
      {((value.citations || []) as Payload[]).map(citation => <p key={String(citation.id)} className="mt-2">引用 {String(citation.id)} · {String(citation.location_id)} · FactPackItem #{String(citation.fact_pack_item_id)} · 范围 {JSON.stringify(citation.locator)}</p>)}
      {((value.declarations || []) as Payload[]).map(declaration => <p key={String(declaration.id)} className="mt-2 whitespace-pre-wrap">{String(declaration.kind)} · {String(declaration.text)}</p>)}
    </details>
  </section>;
}
