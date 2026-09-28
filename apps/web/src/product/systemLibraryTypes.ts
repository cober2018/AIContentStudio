export type LibraryType = "material" | "source" | "fact_pack" | "knowledge_collection";
export type LibraryTab = "all" | LibraryType;
export interface LibraryPage<T> { items: T[]; total: number; offset: number; limit: number }
export interface LibraryUser { id: number; email: string; role: string }
export interface MaterialRevision {
  id: number; material_id?: number; revision_no: number; status: string;
  mime_type?: string | null; content_hash?: string; checksum?: string | null; source_kind?: string;
  rights_status?: string | null; public_use_allowed?: boolean | null;
  model_use_allowed?: boolean | null; commercial_use_allowed?: boolean | null;
  attribution_text?: string | null; source_url?: string | null; provider_key?: string | null;
  attribution_present?: boolean; rights?: Record<string, unknown>; provenance?: Record<string, unknown>;
}
export interface LibraryItem {
  type: LibraryType; id: number; title: string; status: string; scope: "system_shared";
  kind?: string; source_type?: string; version?: number; checksum?: string | null;
  latest_revision?: MaterialRevision | null;
  rights?: Record<string, unknown> | string | null;
  provenance?: Record<string, unknown> | null;
  created_at?: string | null;
}
export interface KnowledgeCollection {
  id: number; name: string; description: string | null; status: "active" | "archived"; revision: number;
}
export interface CollectionItem {
  collection_revision: number;
  id: number; item_type: "source_document" | "fact_pack";
  source_document_id: number | null; fact_pack_id: number | null;
  sort_order: number; note: string | null; status: "active" | "detached";
  title?: string; resource?: LibraryItem | null; resource_status?: string;
}
export interface CollectionPage extends LibraryPage<CollectionItem> { collection_revision: number }
export function collectionSnapshotRevision(page?: CollectionPage): number | undefined {
  const revision = page?.collection_revision;
  if (!revision || !Number.isSafeInteger(revision) || revision < 1
      || !page?.items.every((item) => item.collection_revision === revision)) return undefined;
  return revision;
}
export interface UsageReference { category: string; id: number; title: string; href?: string }
export interface LibraryUsage extends LibraryPage<UsageReference> {
  counts: Record<string, number>; coverage: Record<string, string>;
}
export interface ProjectSummary { id: number; title: string; status: string }
export interface FactBoundary { revision_no: number; fact_pack_id: number; fact_pack_version: number; fact_pack_checksum: string }
export interface SourceDetail {
  id: number; title: string; source_type: string; parse_status: string; is_archived: boolean;
  raw_text?: string | null; as_of?: string | null; trust_level?: number; sha256?: string | null;
  facts?: { id: number; statement: string; status: string }[];
}
export interface FactPackDetail {
  id: number; name: string; status: string; version: number; checksum: string | null;
  items?: { id?: number; item_id?: number; statement?: string | null; evidence_kind?: string; public_use_allowed?: boolean | null }[];
}

export const libraryLabels: Record<LibraryTab, string> = {
  all: "全部", material: "素材", source: "文档与网页", fact_pack: "Evidence Packs", knowledge_collection: "知识集合",
};
export const libraryTabs = Object.keys(libraryLabels) as LibraryTab[];
export const materialKinds = ["image", "video", "audio", "chart", "screenshot", "brand", "other"];

export function libraryQuery(values: Record<string, string | number | undefined>): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(values)) if (value !== undefined && value !== "") params.set(key, String(value));
  return params.toString();
}
export function checkedPage<T>(value: LibraryPage<T>): LibraryPage<T> {
  if (!value || !Array.isArray(value.items) || !Number.isSafeInteger(value.total) || value.total < 0
      || !Number.isSafeInteger(value.offset) || value.offset < 0 || !Number.isSafeInteger(value.limit) || value.limit < 1) {
    throw new Error("列表响应缺少分页信息，暂不能确认是否为空。请刷新或检查接口。");
  }
  return value;
}
export function positiveNumber(value: string, label = "ID"): number {
  if (!/^\d+$/.test(value) || !Number.isSafeInteger(Number(value)) || Number(value) < 1) throw new Error(`${label}必须是正整数。`);
  return Number(value);
}
export function collectionResource(item: CollectionItem): { type: "source" | "fact_pack"; id: number } {
  const type = item.item_type === "source_document" ? "source" : "fact_pack";
  const id = type === "source" ? item.source_document_id : item.fact_pack_id;
  if (!Number.isSafeInteger(id) || !id || id < 1) throw new Error("集合成员引用不完整，请刷新集合。");
  return { type, id };
}
export function membershipPayload(type: "source" | "fact_pack", id: number) {
  return { item_type: type === "source" ? "source_document" : "fact_pack", [type === "source" ? "source_document_id" : "fact_pack_id"]: id };
}
export function internalLibraryLink(value?: string): string | null {
  if (!value || !/^\/(projects|opportunities|workflows|learning|sources|fact-packs|materials)([/?#]|$)/.test(value)) return null;
  return value;
}
export function libraryError(error: unknown): string { return error instanceof Error ? error.message : "请求失败，请重试读取。"; }
export function readableValue(value: unknown): string {
  if (value === true) return "允许";
  if (value === false) return "不允许";
  if (value == null || value === "") return "未知";
  if (typeof value === "object") return JSON.stringify(value);
  const labels: Record<string, string> = { allowed: "允许", denied: "不允许", unknown: "未知", revoked: "已撤销", not_decided_at_source_level: "来源层尚未决定", system_shared: "系统共享" };
  return labels[String(value)] ?? String(value);
}
