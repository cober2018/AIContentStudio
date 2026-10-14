import type { ChannelFormDescriptor, ChannelFormField } from "../api";

export type Payload = Record<string, unknown>;
export type FieldPath = (string | number)[];
export const normalizeText = (text: string) => text.replace(/\r\n?/g, "\n").normalize("NFC");
export const fieldName = (field: ChannelFormField) => field.path.split(".").slice(-1)[0].replace(/\[\]$/, "");
export const pathLabel = (path: FieldPath) => path.reduce<string>((result, part) => typeof part === "number" ? `${result}[${part}]` : `${result}${result ? "." : ""}${part}`, "");
export const isObject = (value: unknown): value is Payload => !!value && typeof value === "object" && !Array.isArray(value);

export function fieldsForObject(field: ChannelFormField, value: Payload): ChannelFormField[] {
  if (!field.discriminator) return field.fields || [];
  return Object.values(field.variants?.[String(value[field.discriminator])] || {});
}
export function valueAtPath(value: unknown, path: FieldPath): unknown {
  for (const part of path) value = (value as Record<string | number, unknown> | undefined)?.[part];
  return value;
}
export function setAtPath<T>(value: T, path: FieldPath, next: unknown): T {
  if (!path.length) return next as T;
  const [first, ...rest] = path;
  if (Array.isArray(value)) return value.map((item, index) => index === first ? setAtPath(item, rest, next) : item) as T;
  return { ...value, [first]: setAtPath((value as Payload)?.[first], rest, next) };
}

function locations(value: unknown, result = new Map<string, string>()): Map<string, string> {
  if (Array.isArray(value)) value.forEach(item => locations(item, result));
  else if (isObject(value)) {
    if (typeof value.id === "string") {
      const text = [value.text, value.caption, value.script].find(item => typeof item === "string");
      if (typeof text === "string") result.set(value.id, normalizeText(text));
    }
    Object.entries(value).filter(([key]) => key !== "citations").forEach(([, item]) => locations(item, result));
  }
  return result;
}

export function descriptorIssue(descriptor: ChannelFormDescriptor | undefined | null, payload: Payload, original?: Payload): string {
  if (!descriptor || descriptor.descriptor_version !== 1 || !Array.isArray(descriptor.fields)) return "缺少受支持的服务端字段描述，正文只读，不能保存。";
  const globalIds = new Set<string>();
  function objectIssue(field: ChannelFormField, value: Payload, path: FieldPath): string {
    if (field.discriminator && !field.variants?.[String(value[field.discriminator])]) return `${pathLabel([...path, field.discriminator])}：不支持的内容类型。`;
    const fields = fieldsForObject(field, value);
    if (field.additional_fields !== true) {
      const known = new Set(fields.map(fieldName));
      const unknown = Object.keys(value).find(key => !known.has(key));
      if (unknown) return `${pathLabel([...path, unknown])}：含不支持的字段，原值已保留，不能保存。`;
    }
    for (const child of fields) {
      const issue = visit(child, value[fieldName(child)], [...path, fieldName(child)]);
      if (issue) return issue;
    }
    return "";
  }
  function visit(field: ChannelFormField, value: unknown, path: FieldPath): string {
    const label = pathLabel(path);
    if (!["string", "integer", "boolean", "object", "list", "media_ref"].includes(field.type)) return `${label}：不支持的字段类型，原值已保留，不能保存。`;
    if (value === undefined || value === null && field.default === null && !field.required) return field.required ? `${label}：必填。` : "";
    if (field.type === "object") return isObject(value) ? objectIssue(field, value, path) : `${label}：须为结构对象。`;
    if (field.type === "list") {
      if (!Array.isArray(value) || !field.item) return `${label}：须为受支持的列表。`;
      if (value.length < (field.min_items ?? 0) || value.length > (field.max_items ?? Infinity)) return `${label}：列表数量不符合限制。`;
      if (field.unique_values && new Set(value.map(item => JSON.stringify(item))).size !== value.length) return `${label}：列表值不能重复。`;
      const ids = new Set<string>();
      for (const [index, item] of value.entries()) {
        if (isObject(item)) {
          if (field.ordered && item.order !== index) return `${label}[${index}].order：顺序须从零连续排列。`;
          if (field.unique_ids && typeof item.id === "string") {
            if (ids.has(item.id) || field.item.global_unique_ids && globalIds.has(item.id)) return `${label}[${index}].id：稳定标识重复。`;
            ids.add(item.id); if (field.item.global_unique_ids || label.startsWith("blocks")) globalIds.add(item.id);
          }
        }
        const issue = visit(field.item, item, [...path, index]);
        if (issue) return issue;
      }
      if (field.first_kind && (!isObject(value[0]) || value[0].kind !== field.first_kind)) return `${label}[0].kind：首段须为 ${field.first_kind}。`;
      for (const [kind, count] of Object.entries(field.kind_counts || {})) {
        const length = value.filter(item => isObject(item) && item.kind === kind).length;
        if (length < (count.min ?? 0) || length > (count.max ?? Infinity)) return `${label}：${kind} 数量不符合限制。`;
      }
      return "";
    }
    if (field.type === "integer") {
      if (!Number.isInteger(value)) return `${label}：须为整数。`;
      if ((value as number) < (field.minimum ?? -Infinity) || (value as number) > (field.maximum ?? Infinity)) return `${label}：数值超出允许范围。`;
    } else if (field.type === "boolean") {
      if (typeof value !== "boolean") return `${label}：须为是或否。`;
    } else {
      if (typeof value !== "string") return `${label}：须为文字。`;
      const text = normalizeText(value), size = Array.from(text).length;
      if (field.required && !text.trim() || size < (field.min_length ?? 0) || size > (field.max_length ?? Infinity)) return `${label}：${field.required ? "须填写，" : ""}文字长度不符合限制${field.max_length ? `（最多 ${field.max_length} 字）` : ""}。`;
      if (/[\u0000-\u0008\u000b\u000c\u000e-\u001f\ud800-\udfff]/u.test(text)) return `${label}：含无效字符。`;
      if (field.pattern) {
        try { if (!new RegExp(field.pattern).test(text)) return `${label}：格式不正确。`; }
        catch { return `${label}：字段约束暂不支持，不能保存。`; }
      }
    }
    if (field.enum && !field.enum.some(item => item === value)) return `${label}：不在允许的值内。`;
    return "";
  }
  const issue = objectIssue({ path: "", type: "object", fields: descriptor.fields, additional_fields: descriptor.additional_fields }, payload, []);
  if (issue) return issue;
  const texts = locations(payload), previous = original ? locations(original) : undefined;
  if (typeof payload.text === "string") texts.set("single", normalizeText(payload.text));
  if (previous && typeof original?.text === "string") previous.set("single", normalizeText(original.text));
  for (const [index, citation] of (Array.isArray(payload.citations) ? payload.citations : []).entries()) {
    if (!isObject(citation) || !isObject(citation.locator)) return `citations[${index}]：引用结构不完整。`;
    const { start, end } = citation.locator;
    const text = texts.get(String(citation.location_id));
    if (!Number.isInteger(start) || !Number.isInteger(end) || (start as number) < 0 || (end as number) <= (start as number) || text === undefined || (end as number) > Array.from(text).length) return `citations[${index}]：引用范围超出正文；位置不会自动改变。`;
    const old = previous?.get(String(citation.location_id));
    if (old !== undefined && Array.from(old).slice(start as number, end as number).join("") !== Array.from(text).slice(start as number, end as number).join("")) return `citations[${index}]：引用文字已变化；请恢复引用文字，精确事实链接不会自动重绑。`;
  }
  if (new TextEncoder().encode(JSON.stringify(payload)).length > (descriptor.technical_limits?.canonical_bytes ?? 2_000_000)) return "payload：正文超过技术大小限制。";
  return "";
}

function containsMedia(value: unknown): boolean {
  if (Array.isArray(value)) return value.some(containsMedia);
  return isObject(value) && Object.entries(value).some(([key, item]) => /(?:image_ref_key|b_roll_ref_keys)$/.test(key) && (Array.isArray(item) ? item.length > 0 : !!item) || containsMedia(item));
}
function collectIds(value: unknown, ids = new Set<string>()): Set<string> {
  if (Array.isArray(value)) value.forEach(item => collectIds(item, ids));
  else if (isObject(value)) { if (typeof value.id === "string") ids.add(value.id); Object.values(value).forEach(item => collectIds(item, ids)); }
  return ids;
}
export function descriptorHasExactMedia(field: ChannelFormField, kind?: string): boolean {
  if (field.type === "media_ref") return true;
  if (field.type === "list") return !!field.item && descriptorHasExactMedia(field.item, kind);
  if (field.type !== "object") return false;
  const seed = field.discriminator ? { [field.discriminator]: kind || Object.keys(field.variants || {})[0] } : {};
  return fieldsForObject(field, seed).some(child => descriptorHasExactMedia(child));
}
export function newListItem(field: ChannelFormField, kind?: string): unknown {
  const item = field.item;
  if (!item) throw new Error("缺少列表字段描述。");
  function make(node: ChannelFormField, selectedKind?: string): unknown {
    if (fieldName(node) === "id") return `item-${crypto.randomUUID()}`;
    if (fieldName(node) === "order") return 0;
    if (node.type === "object") {
      const seed = node.discriminator ? { [node.discriminator]: selectedKind || Object.keys(node.variants || {})[0] } : {};
      return Object.fromEntries(fieldsForObject(node, seed).map(child => [fieldName(child), make(child)]));
    }
    if (node.type === "list") return Array.from({ length: node.min_items || 0 }, (_, index) => {
      const row = make(node.item!); return isObject(row) && node.ordered ? { ...row, order: index } : row;
    });
    return node.default ?? (node.type === "boolean" ? false : node.type === "integer" ? node.minimum ?? 0 : "");
  }
  return make(item, kind);
}
export function changeList(payload: Payload, path: FieldPath, field: ChannelFormField, action: "add" | "remove" | "move", index = 0, destination = 0, kind?: string): Payload {
  if (field.readonly || field.exact_evidence_ref || path[0] === "citations") throw new Error("精确引用列表只读，不能自动修改事实链接。");
  const currentList = valueAtPath(payload, path);
  const list = currentList === undefined ? [] : currentList;
  if (!Array.isArray(list)) throw new Error("列表结构不可编辑。");
  const next = [...list];
  if (action === "add") {
    if (descriptorHasExactMedia(field, kind)) throw new Error("含精确素材引用的列表只读，新增须先绑定精确素材版本。");
    if (list.length >= (field.max_items ?? Infinity)) throw new Error("列表已达到数量上限。");
    const item = newListItem(field, kind);
    if (containsMedia(item)) throw new Error("新增素材须先绑定精确素材版本。");
    next.push(item);
  } else {
    if (index < 0 || index >= list.length) throw new Error("列表位置已变化。");
    if (containsMedia(list)) throw new Error("含精确素材映射的列表不可删除或重排；素材链接保持原样。");
    if (action === "remove") {
      const ids = collectIds(list[index]);
      if ((Array.isArray(payload.citations) ? payload.citations : []).some(citation => isObject(citation) && ids.has(String(citation.location_id)))) throw new Error("此条目仍有精确引用，不能删除。");
      if (list.length <= (field.min_items ?? 0)) throw new Error("须保留最少数量的条目。");
      next.splice(index, 1);
    } else {
      if (destination < 0 || destination >= list.length) return payload;
      const [item] = next.splice(index, 1); next.splice(destination, 0, item);
    }
  }
  if (field.first_kind && (!isObject(next[0]) || next[0].kind !== field.first_kind)) throw new Error("首段直接回答必须保留在第一位。");
  const ordered = field.ordered ? next.map((item, order) => isObject(item) ? { ...item, order } : item) : next;
  return setAtPath(payload, path, ordered);
}
