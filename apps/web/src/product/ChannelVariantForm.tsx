import { useState } from "react";
import { Button, ErrorBanner, inputClass } from "../components/ui";
import type { ChannelFormDescriptor, ChannelFormField } from "../api";
import { changeList, descriptorHasExactMedia, descriptorIssue, fieldName, fieldsForObject, isObject, normalizeText, newListItem, pathLabel, setAtPath, type FieldPath, type Payload } from "./ChannelVariantModel";

export function variantBodyIssue(schema: string, payload: Payload, descriptor?: ChannelFormDescriptor | null, original?: Payload): string {
  if (descriptor?.schema_id !== schema) return "服务端字段描述与正文版本不一致，正文只读，不能保存。";
  return descriptorIssue(descriptor, payload, original);
}

export default function ChannelVariantForm({ schema, descriptor, value, original, readOnly, onChange }: {
  schema: string; descriptor?: ChannelFormDescriptor | null; value: Payload; original?: Payload; readOnly: boolean; onChange: (value: Payload) => void;
}) {
  const [operationIssue, setOperationIssue] = useState("");
  const compatible = descriptor?.schema_id === schema && descriptor.descriptor_version === 1;
  const issue = variantBodyIssue(schema, value, descriptor, original);
  const locked = readOnly || !compatible;
  function update(path: FieldPath, next: unknown) {
    if (locked) return;
    setOperationIssue(""); onChange(setAtPath(value, path, next));
  }
  function editList(field: ChannelFormField, path: FieldPath, action: "add" | "remove" | "move", index?: number, destination?: number, kind?: string) {
    if (locked) return;
    try { const next = changeList(value, path, field, action, index, destination, kind); setOperationIssue(""); onChange(next); }
    catch (cause) { setOperationIssue(`${pathLabel(path)}：${cause instanceof Error ? cause.message : "列表不能安全修改。"}`); }
  }
  function objectFields(fields: ChannelFormField[], object: Payload, path: FieldPath, inheritedReadOnly: boolean) {
    const known = new Set(fields.map(fieldName));
    return <>{fields.map(field => renderField(field, object[fieldName(field)], [...path, fieldName(field)], inheritedReadOnly))}{Object.keys(object).filter(key => !known.has(key)).map(key => <div key={key} className="rounded border border-amber-300 p-2 text-xs"><p>{pathLabel([...path, key])} · 未知字段（只读，不能保存）</p><pre className="overflow-auto whitespace-pre-wrap">{JSON.stringify(object[key], null, 2)}</pre></div>)}</>;
  }
  function renderField(field: ChannelFormField, item: unknown, path: FieldPath, inheritedReadOnly: boolean): JSX.Element {
    const key = pathLabel(path), label = field.label || fieldName(field);
    const fieldLocked = locked || inheritedReadOnly || !!field.readonly || field.type === "media_ref" || path[0] === "citations" || path[0] === "blocks" && typeof value.html_template === "string";
    const fullLabel = `${label} · ${key}`;
    if (field.type === "object") {
      if (item === undefined && !field.required) return <div key={key} className="text-sm">{fullLabel} · 未启用{!fieldLocked && <Button className="ml-2" size="sm" variant="secondary" onClick={() => update(path, newListItem({ path: field.path, type: "list", item: field }))}>启用{label}</Button>}</div>;
      if (item !== undefined && !isObject(item)) return <div key={key} className="rounded border p-2 text-xs">{fullLabel} · 结构异常（只读）<pre>{JSON.stringify(item)}</pre></div>;
      const object = isObject(item) ? item : {};
      const fields = fieldsForObject(field, object);
      return <fieldset key={key} className="space-y-3 rounded-lg border border-slate-200 p-3"><legend className="px-1 text-sm">{label} · {key}</legend>{objectFields(fields, object, path, fieldLocked)}</fieldset>;
    }
    if (field.type === "list") {
      if (!field.item || item !== undefined && !Array.isArray(item)) return <div key={key} className="text-xs">{fullLabel} · 列表结构不支持编辑<pre>{JSON.stringify(item)}</pre></div>;
      const rows = Array.isArray(item) ? item : [];
      const kinds = (field.item.variants ? Object.keys(field.item.variants) : [undefined]).filter(kind => !descriptorHasExactMedia(field, kind));
      return <fieldset key={key} className="space-y-3 rounded-lg border border-slate-200 p-3"><legend className="px-1 text-sm">{label} · {key}（{rows.length}{field.max_items ? `/${field.max_items}` : ""}）</legend>{rows.map((row, index) => <div key={isObject(row) && typeof row.id === "string" ? row.id : index} className="space-y-2 border-b border-slate-100 pb-3">
        {renderField(field.item!, row, [...path, index], fieldLocked)}
        {!fieldLocked && <div className="flex flex-wrap gap-2"><Button size="sm" variant="secondary" disabled={rows.length <= (field.min_items ?? 0)} onClick={() => editList(field, path, "remove", index)}>删除条目 {index + 1}</Button>{field.ordered && <><Button size="sm" variant="secondary" disabled={index === 0} onClick={() => editList(field, path, "move", index, index - 1)}>上移条目 {index + 1}</Button><Button size="sm" variant="secondary" disabled={index === rows.length - 1} onClick={() => editList(field, path, "move", index, index + 1)}>下移条目 {index + 1}</Button></>}</div>}
      </div>)}{!fieldLocked && <div className="flex flex-wrap gap-2">{kinds.map(kind => <Button key={kind || "item"} size="sm" variant="secondary" disabled={rows.length >= (field.max_items ?? Infinity)} onClick={() => editList(field, path, "add", undefined, undefined, kind)}>新增{kind ? ` ${kind}` : "条目"}</Button>)}</div>}{path[0] === "citations" && <p className="text-xs text-slate-500">引用与精确事实链接只读；文字修改不自动迁移引用。</p>}</fieldset>;
    }
    if (!["string", "integer", "boolean", "media_ref"].includes(field.type)) return <div key={key} className="rounded border border-amber-300 p-2 text-xs">{fullLabel} · 不支持的字段（只读）<pre>{JSON.stringify(item, null, 2)}</pre></div>;
    if (field.type === "boolean") return <label key={key} className="flex items-center gap-2 text-sm"><input aria-label={fullLabel} type="checkbox" checked={item === true} disabled={fieldLocked} onChange={event => update(path, event.target.checked)} />{fullLabel}{field.required ? " · 必填" : ""}</label>;
    if (field.enum) return <label key={key} className="block text-sm">{fullLabel}<select aria-label={fullLabel} className={`${inputClass} mt-1`} value={item === undefined ? "" : String(item)} disabled={fieldLocked || field.enum.length === 1} onChange={event => update(path, field.type === "integer" ? Number(event.target.value) : event.target.value)}>{item === undefined && <option value="">请选择</option>}{field.enum.map(option => <option key={String(option)} value={String(option)}>{String(option)}</option>)}</select></label>;
    if (field.type === "integer") return <label key={key} className="block text-sm">{fullLabel}<input aria-label={fullLabel} className={`${inputClass} mt-1`} type="number" step="1" min={field.minimum} max={field.maximum} value={typeof item === "number" ? item : ""} readOnly={fieldLocked} onChange={event => update(path, event.target.value === "" ? undefined : Number(event.target.value))} /></label>;
    const text = typeof item === "string" ? item : "";
    return <label key={key} className="block text-sm">{fullLabel}<span className="ml-2 text-xs text-slate-500">{Array.from(normalizeText(text)).length}{field.max_length ? `/${field.max_length}` : ""} 字{field.required ? " · 必填" : ""}{fieldLocked ? " · 只读" : ""}</span><textarea aria-label={fullLabel} className={`${inputClass} mt-1 ${fieldLocked || field.type === "media_ref" ? "min-h-12" : "min-h-24"}`} value={text} readOnly={fieldLocked} onChange={event => update(path, event.target.value)} />{field.type === "media_ref" && <span className="mt-1 block text-xs text-slate-500">精确素材槽保持原样；素材版本与权利由服务端校验。</span>}</label>;
  }
  return <section aria-label="Variant 正文编辑" className="space-y-3 rounded-lg border border-slate-200 p-4"><h3 className="font-medium">渠道正文</h3><p className="text-xs text-slate-500">服务端字段描述：{schema} · v{descriptor?.descriptor_version ?? "未知"}。保存追加新修订；稳定 ID、精确素材和事实链接保留。</p>{typeof value.html_template === "string" && <p className="text-xs text-amber-700">公众号原版 HTML 与正文块须一致，因此正文块只读；标题、摘要和署名可编辑。</p>}{(operationIssue || issue) && <ErrorBanner message={operationIssue || issue} />}{compatible ? objectFields(descriptor.fields, value, [], false) : <pre className="max-h-96 overflow-auto whitespace-pre-wrap text-xs">{JSON.stringify(value, null, 2)}</pre>}</section>;
}
