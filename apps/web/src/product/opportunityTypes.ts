export type OpportunityStatus = "new" | "watching" | "qualified" | "dismissed" | "converted" | "archived";
export interface Assessment {
  what_happened: string;
  why_now: string;
  brand_relevance: string;
  audience_fit: string;
  suggested_angle: string | null;
  time_sensitivity: "high" | "medium" | "low" | "timeless";
  recommended_identity_refs: Record<string, unknown>[];
  recommended_modalities: string[];
  recommended_channels: string[];
  evidence_signal_ids: number[];
  evidence_summary: string[];
  risk_flags: string[];
  similarity_state: "unknown" | "none" | "possible";
  similar_content_refs: unknown[];
  confidence: number | null;
}
export interface AssessmentRevision {
  id: number;
  revision_no: number;
  assessment: Partial<Assessment>;
  checksum: string;
  analysis_source?: string | null;
  analysis_provider_key?: string | null;
  analysis_provider_version?: string | null;
  created_by?: string;
  created_at?: string;
}
export interface Opportunity {
  persona_id?: number | null;
  research_run_id?: number | null;
  business_date?: string | null;
  id: number;
  title: string;
  summary: string;
  status: OpportunityStatus;
  priority: "high" | "normal" | "low";
  relevant_until: string | null;
  updated_at?: string;
  signal_types: string[];
  signal_count: number;
  latest_assessment: AssessmentRevision | null;
}
export interface OpportunitySignal {
  id: number;
  signal_type: string;
  source_entity_id: number | null;
  external_ref: string | null;
  label: string;
  annotation: Record<string, unknown>;
  source_version?: string | null;
  source_checksum?: string | null;
  observed_at?: string | null;
  status?: string;
}
export interface Conversion { project_id: number; assessment_revision_id?: number }
