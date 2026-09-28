export type ScopeType = "owner" | "brand" | "persona" | "account" | "series";
export type EvidenceType = "published_content" | "performance_observation" | "insight" | "delivery_feedback";
export interface Page<T> { items: T[]; total: number; limit: number; offset: number }
export interface PublishedContent {
  id: number; title: string | null; channel: string; origin: string; status: string;
  published_at: string | null; content_account_id: number | null; content_form?: string | null;
  coverage?: Record<string, unknown>; coverage_json?: Record<string, unknown>;
  [key: string]: unknown;
}
export interface Observation {
  id: number; observation_kind: string; metric_namespace: string | null; metric_key: string | null;
  numeric_value: number | null; text_value: string | null; unit: string | null; observed_at: string;
  supersedes_id: number | null; granularity?: string; cutoff?: string; [key: string]: unknown;
}
export interface Insight { id: number; statement: string; insight_type: string; [key: string]: unknown }
export interface Evidence { id: number; evidence_type: EvidenceType; entity_id: number; role: string; note?: string | null; [key: string]: unknown }
export interface LearningCandidate {
  id: number; title: string; proposition: string; rationale: string; category: string;
  status: "collecting" | "ready_for_review" | "accepted" | "rejected" | "archived";
  revision_no: number; evidence?: Evidence[]; [key: string]: unknown;
}
export interface PromotableClaim {
  statement: string; applicability: Record<string, unknown>; limitations: string[];
}
export interface MemoryRevision {
  id: number; revision_no: number; statement: string; source_learning_candidate_id: number | null;
  applicability?: unknown; applicability_json?: unknown; limitations?: unknown; limitations_json?: unknown;
  evidence_snapshot?: unknown; evidence_snapshot_json?: unknown; [key: string]: unknown;
}
export interface MemoryEntry {
  id: number; scope_type: ScopeType; scope_id?: number | null; status: string; memory_type: string;
  current_revision: number | MemoryRevision | null; latest_revision?: MemoryRevision | null;
  origin?: unknown; scope_origin?: { scope_type?: ScopeType; scope_id?: number; label?: string; relationship?: string } | string; source_learning_candidate_id?: number | null;
  [key: string]: unknown;
}
export interface Coverage {
  record_count?: number; sample_count?: number; observation_count?: number; missing_date_count?: number;
  coverage?: Record<string, { known?: number; missing?: number; unknown?: number }>;
  years?: Record<string, number>; limitations?: string[]; incomplete?: boolean;
}
export interface MetricGroup {
  metric_namespace: string; metric_key: string; unit: string | null; measurement_mode: string;
  period_start?: string | null; period_end?: string | null; sample_count?: number;
  sum?: number | null; min?: number | null; max?: number | null; average?: number | null; median?: number | null;
  trend?: { observed_at: string; published_content_id: number; value: number | null }[];
}
export interface Analysis extends Coverage { groups?: MetricGroup[] }

export const scopeTypes = ["owner", "brand", "persona", "account", "series"];
export const evidenceTypes = ["published_content", "performance_observation", "insight", "delivery_feedback"];
export const categories = ["identity", "audience", "channel", "format", "topic", "workflow"];
export const memoryTypes = ["historical_viewpoint", "audience_learning", "channel_experience", "editorial_preference", "validated_strategy", "workflow_learning", "topic_learning"];

export function operationUUID(): string {
  const crypto = globalThis.crypto;
  if (typeof crypto?.randomUUID === "function") return crypto.randomUUID();
  if (typeof crypto?.getRandomValues !== "function") throw new Error("当前浏览器无法生成安全操作编号，请使用支持 Web Crypto 的浏览器。");
  const bytes = crypto.getRandomValues(new Uint8Array(16));
  bytes[6] = (bytes[6] & 15) | 64;
  bytes[8] = (bytes[8] & 63) | 128;
  const hex = Array.from(bytes, (value) => value.toString(16).padStart(2, "0")).join("");
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}

export function pageData<T>(value: Page<T>): Page<T> {
  if (!value || !Array.isArray(value.items) || !Number.isInteger(value.total) || value.total < 0 || !Number.isInteger(value.limit) || value.limit <= 0 || !Number.isInteger(value.offset) || value.offset < 0) {
    throw new Error("列表响应不完整，暂不能确认是否为空。");
  }
  return value;
}

export function queryString(values: Record<string, string | number | boolean | null | undefined>): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(values)) if (value !== undefined && value !== null && value !== "") params.set(key, String(value));
  return params.toString();
}

export function insightReferences(value: unknown): { evidence_type: EvidenceType; entity_id: number }[] {
  if (!Array.isArray(value)) throw new Error("证据引用必须为列表。");
  return value.map((item) => {
    if (!item || typeof item !== "object") throw new Error("证据引用必须含 type 与 id。");
    const evidence_type = item.type ?? item.evidence_type;
    const entity_id = item.id ?? item.entity_id;
    if (!evidenceTypes.includes(evidence_type) || !Number.isInteger(entity_id) || entity_id <= 0) throw new Error("证据类型无效或 ID 不是正整数。");
    return { evidence_type, entity_id };
  });
}

export function frozenEvidenceCount(snapshot: unknown): number | undefined {
  if (!snapshot || typeof snapshot !== "object" || !("candidate" in snapshot)) return undefined;
  const candidate = snapshot.candidate;
  if (!candidate || typeof candidate !== "object" || !("evidence" in candidate)) return undefined;
  return Array.isArray(candidate.evidence) ? candidate.evidence.length : undefined;
}

export function promotableClaim(candidate: LearningCandidate): PromotableClaim | null {
  if (candidate.status !== "accepted") return null;
  const summary = candidate.validation_summary;
  if (!summary || typeof summary !== "object" || !("promotable_claim" in summary)) return null;
  const claim = summary.promotable_claim;
  if (!claim || typeof claim !== "object" || !("statement" in claim) || !("applicability" in claim) || !("limitations" in claim)) return null;
  if (typeof claim.statement !== "string" || !claim.statement.trim() || !claim.applicability || typeof claim.applicability !== "object" || Array.isArray(claim.applicability) || !Array.isArray(claim.limitations) || claim.limitations.some((item) => typeof item !== "string")) return null;
  return { statement: claim.statement, applicability: claim.applicability as Record<string, unknown>, limitations: claim.limitations };
}
