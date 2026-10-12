import { api } from "../api";

export type JsonValue = string | number | boolean | null | JsonValue[] | { [key: string]: JsonValue };
export type JsonObject = { [key: string]: JsonValue };
export type CapabilityKind = "prompt_skill" | "recipe" | "creative_pattern" | "preference" | "execution_template" | "tool";
export type CapabilityStatus = "candidate" | "saved" | "pinned" | "archived" | "deprecated";
export type CapabilityScopeType = "owner" | "persona" | "account" | "series" | "project" | "channel" | "executor";
export type CapabilityOutcome = "used" | "accepted" | "rejected" | "unknown";
export interface ArgumentProperty {
  type: "string" | "number" | "integer" | "boolean";
  description?: string;
  enum?: (string | number | boolean)[];
  minLength?: number;
  maxLength?: number;
  minimum?: number;
  maximum?: number;
}
export interface ArgumentSchema {
  type?: "object";
  properties?: Record<string, ArgumentProperty>;
  required?: string[];
  additionalProperties?: false;
  description?: string;
}
export interface CapabilityRevision {
  id: number;
  revision_no: number;
  content: JsonObject;
  args_schema: ArgumentSchema | null;
  content_hash: string;
  metadata: JsonObject;
  source_execution_id: number | null;
  source_learning_candidate_id: number | null;
  created_by?: string;
  created_at?: string;
}
export interface CapabilityArtifact {
  id: number;
  kind: CapabilityKind;
  name: string;
  status: CapabilityStatus;
  scope_type: CapabilityScopeType;
  scope: JsonObject;
  source_kind: "capability_memory";
  current_revision: CapabilityRevision;
  usage: { use_count: number; last_used: string | null };
  matched_scope?: JsonObject;
}
export interface CapabilityPage { items: CapabilityArtifact[]; total: number; limit: number; offset: number }
export interface CapabilityContext { projectId?: number; unitId?: number; executionId?: number }
export interface CapabilityUseResult {
  use_id: number;
  artifact_revision_id: number;
  content_hash: string;
  rendered_content: JsonValue;
  rendered_arguments_hash: string;
  outcome: CapabilityOutcome;
}
export interface CapabilityUseReceipt {
  use_id: number;
  artifact_revision_id: number;
  outcome: CapabilityOutcome;
}
export interface CapabilityDefinition { kind: CapabilityKind; name: string; content: JsonObject; args_schema?: ArgumentSchema }
export interface PreferenceEditReference {
  master_revision_id: number;
  revision_no: number;
  payload_hash: string;
  context_hash: string;
  parent_revision_id: number;
  parent_payload_hash: string;
  parent_context_hash: string;
}
export interface SavedPreferenceEdit extends PreferenceEditReference {
  actor_user_id: number;
  payload_schema: string;
  created_at: string;
}
export interface PreferenceEditPage { items: SavedPreferenceEdit[]; limit: number; offset: number; next_offset: number | null }
export interface InstalledSkill {
  id: string;
  name: string;
  source_kind: string;
  description?: string;
}

export const kindLabels: Record<CapabilityKind, string> = {
  prompt_skill: "提示方法", recipe: "操作配方", creative_pattern: "创作模式",
  preference: "创作偏好", execution_template: "执行模板", tool: "外部工具定义",
};
export const statusLabels: Record<CapabilityStatus, string> = {
  candidate: "候选", saved: "已保存", pinned: "已固定", archived: "已归档", deprecated: "已停用",
};
export const scopeLabels: Record<CapabilityScopeType, string> = {
  owner: "本人", persona: "角色", account: "账号", series: "系列", project: "项目", channel: "渠道", executor: "执行者",
};
export const emptyArgsSchema: ArgumentSchema = { type: "object", properties: {}, required: [], additionalProperties: false };
const prefix = "/capability-memory";
export const capabilityApi = {
  list: (query: string) => api.get<CapabilityPage>(`${prefix}/?${query}`),
  discover: (query: string) => api.get<CapabilityPage>(`${prefix}/discover?${query}`),
  detail: (id: number) => api.get<CapabilityArtifact>(`${prefix}/${id}`),
  history: (id: number) => api.get<{ items: CapabilityRevision[] }>(`${prefix}/${id}/revisions`),
  create: (body: CapabilityDefinition & { scope_type?: CapabilityScopeType; scope?: JsonObject }) => api.post<CapabilityArtifact>(`${prefix}/`, body),
  revise: (id: number, body: { expected_revision: number; content: JsonObject; args_schema: ArgumentSchema }) => api.post<CapabilityArtifact>(`${prefix}/${id}/revisions`, body),
  lifecycle: (id: number, body: { expected_revision: number; status: CapabilityStatus; scope_type?: CapabilityScopeType; scope?: JsonObject; confirm_scope_broadening?: boolean }) => api.post<CapabilityArtifact>(`${prefix}/${id}/lifecycle`, body),
  use: (id: number, body: { artifact_revision_id: number; arguments: JsonObject; project_id?: number; unit_id?: number; execution_id?: number }) => api.post<CapabilityUseResult>(`${prefix}/${id}/use`, body),
  outcome: (id: number, outcome: CapabilityOutcome, expectedOutcome: CapabilityOutcome) => api.post(`${prefix}/uses/${id}/outcome`, { outcome, expected_outcome: expectedOutcome }),
  readUse: (id: number) => api.get<CapabilityUseReceipt>(`${prefix}/uses/${id}`),
  captureExecution: (body: CapabilityDefinition & { execution_id: number }) => api.post<CapabilityArtifact>(`${prefix}/capture-execution`, body),
  captureLearning: (body: CapabilityDefinition & { learning_candidate_id: number; expected_learning_revision: number }) => api.post<CapabilityArtifact>(`${prefix}/capture-learning`, body),
  preferenceEdits: (projectId: number, unitId: number, offset = 0) => api.get<PreferenceEditPage>(`${prefix}/preference-edits?${queryString({ project_id: projectId, unit_id: unitId, limit: 50, offset })}`),
  capturePreference: (body: { project_id: number; unit_id: number; name: string; preference: string; edits: PreferenceEditReference[] }) => api.post<CapabilityArtifact>(`${prefix}/capture-preference`, body),
  export: (id: number) => api.get<JsonObject>(`${prefix}/${id}/export`),
  import: (body: JsonObject) => api.post<CapabilityArtifact>(`${prefix}/import`, body),
  installedSkills: () => api.get<{ items: InstalledSkill[] }>(`${prefix}/installed-skills`),
};

export function contextQuery(context: CapabilityContext): Record<string, number> {
  return Object.fromEntries(Object.entries({ project_id: context.projectId, unit_id: context.unitId, execution_id: context.executionId }).filter(([, value]) => value !== undefined)) as Record<string, number>;
}
export function queryString(values: Record<string, string | number | undefined>): string {
  const params = new URLSearchParams();
  Object.entries(values).forEach(([key, value]) => { if (value !== undefined && value !== "") params.set(key, String(value)); });
  return params.toString();
}
export function checkedPage(page: CapabilityPage): CapabilityPage {
  if (!page || !Array.isArray(page.items) || !Number.isInteger(page.total) || page.total < 0 || !Number.isInteger(page.limit) || page.limit < 1 || !Number.isInteger(page.offset) || page.offset < 0) throw new Error("能力列表响应不完整，无法确认可用方法。");
  return page;
}
export function preferenceEditReference(edit: PreferenceEditReference): PreferenceEditReference {
  return { master_revision_id: edit.master_revision_id, revision_no: edit.revision_no,
    payload_hash: edit.payload_hash, context_hash: edit.context_hash, parent_revision_id: edit.parent_revision_id,
    parent_payload_hash: edit.parent_payload_hash, parent_context_hash: edit.parent_context_hash };
}
export function checkedPreferenceEdits(page: PreferenceEditPage): PreferenceEditPage {
  if (!page || !Array.isArray(page.items) || page.items.length > 100 || !Number.isSafeInteger(page.limit) || page.limit < 1 || page.limit > 100 || !Number.isSafeInteger(page.offset) || page.offset < 0 || (page.next_offset !== null && (!Number.isSafeInteger(page.next_offset) || page.next_offset <= page.offset))) throw new Error("保存编辑清单响应不完整。");
  for (const edit of page.items) {
    if (!edit || ![edit.master_revision_id, edit.revision_no, edit.parent_revision_id, edit.actor_user_id].every(id => Number.isSafeInteger(id) && id > 0) || edit.revision_no < 2 || ![edit.payload_hash, edit.context_hash, edit.parent_payload_hash, edit.parent_context_hash].every(hash => typeof hash === "string" && /^[0-9a-f]{64}$/.test(hash)) || typeof edit.payload_schema !== "string" || typeof edit.created_at !== "string") throw new Error("保存编辑的精确来源不完整。");
  }
  return page;
}
export function parseObject(text: string): JsonObject {
  if (new TextEncoder().encode(text).length > 65536) throw new Error("JSON 超过 64 KiB，请缩小内容。");
  const parsed: unknown = JSON.parse(text);
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) throw new Error("请输入 JSON 对象。");
  const pending: { value: unknown; depth: number }[] = [{ value: parsed, depth: 0 }];
  let count = 0;
  while (pending.length) {
    const { value, depth } = pending.pop()!;
    if (++count > 4000 || depth > 12) throw new Error("JSON 结构过大或嵌套过深。");
    if (typeof value === "number" && (!Number.isFinite(value) || Math.abs(value) > 2 ** 53)) throw new Error("JSON 含非有限或越界数字，不能保存。");
    if (value && typeof value === "object") {
      const children = Object.values(value);
      if (children.length > 100) throw new Error("JSON 单个对象或数组项数过多。");
      children.forEach(child => pending.push({ value: child, depth: depth + 1 }));
    }
  }
  return parsed as JsonObject;
}
export function parseArgsSchema(text: string): ArgumentSchema {
  const schema = parseObject(text.trim() || JSON.stringify(emptyArgsSchema));
  const allowed = ["type", "properties", "required", "additionalProperties", "description"];
  if (Object.keys(schema).some(key => !allowed.includes(key)) || (schema.type !== undefined && schema.type !== "object") || (schema.additionalProperties !== undefined && schema.additionalProperties !== false)) throw new Error("参数只支持受限的 object schema，不支持引用或动态执行。");
  if (schema.properties !== undefined && (!schema.properties || typeof schema.properties !== "object" || Array.isArray(schema.properties))) throw new Error("properties 必须为对象。");
  const properties = (schema.properties ?? {}) as Record<string, JsonValue>;
  for (const [name, value] of Object.entries(properties)) {
    if (!value || typeof value !== "object" || Array.isArray(value) || !["string", "number", "integer", "boolean"].includes(String(value.type)) || Object.keys(value).some(key => !["type", "description", "enum", "minLength", "maxLength", "minimum", "maximum"].includes(key))) throw new Error(`参数 ${name} 只能使用字符串、数字、整数或布尔类型及有限 enum。`);
    if (value.enum !== undefined && (!Array.isArray(value.enum) || !value.enum.length || value.enum.some(item => typeof item !== (value.type === "integer" ? "number" : value.type) || (typeof item === "number" && (!Number.isFinite(item) || (value.type === "integer" && !Number.isInteger(item))))))) throw new Error(`参数 ${name} 的 enum 与类型不匹配。`);
  }
  if (schema.required !== undefined && (!Array.isArray(schema.required) || schema.required.some(name => typeof name !== "string" || !Object.prototype.hasOwnProperty.call(properties, name)))) throw new Error("required 必须引用已定义参数。");
  return schema as unknown as ArgumentSchema;
}
export function scopeText(type: CapabilityScopeType, scope: JsonObject): string {
  return `${scopeLabels[type]} · ${JSON.stringify(scope)}`;
}
export function scopeFromFields(type: CapabilityScopeType, fields: Record<string, string>): JsonObject {
  if (type === "owner") return {};
  if (type === "channel") {
    if (!fields.channel_id?.trim()) throw new Error("请输入渠道代码。");
    return { channel_id: fields.channel_id.trim() };
  }
  if (type === "executor") {
    if (!["executor_kind", "executor_key", "executor_version"].every(key => fields[key]?.trim())) throw new Error("请输入完整执行者身份和版本。");
    return { executor_kind: fields.executor_kind.trim(), executor_key: fields.executor_key.trim(), executor_version: fields.executor_version.trim() };
  }
  const id = Number(fields.id);
  if (!Number.isSafeInteger(id) || id < 1) throw new Error("范围 ID 必须是正整数。");
  return { id };
}
