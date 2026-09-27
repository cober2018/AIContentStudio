export type Brief = {
  id: number; revision_no: number; checksum: string; objective: string;
  primary_audience: string | null; core_message: string | null; angle: string | null;
  required_evidence: string[]; content_constraints: string[]; identity_scope: number[];
  modality_scope: string[]; channel_scope: string[]; cta: string | null;
  references: { kind: string; id: number }[]; created_at: string | null;
};

export type Overview = {
  stage: string; activeUnitCount: number; archivedUnitCount: number;
  modalityCounts: Record<string, number>; personas: { id: number; name: string; unitCount: number }[];
  brief: { ready: boolean; revision: number | null };
  factBoundary: { ready: boolean; revision: number | null; factPackId: number | null; factPackVersion: number | null; checksum: string | null };
  risks: { code: string; unit_id?: number; run_id?: number }[];
  pendingDecisions: { code: string; unit_id?: number; run_id?: number }[];
  nextAction: { code: string; label: string; href: string } | null;
};

export type SharedAsset = {
  key: string; id: number; source_type: "project_upload" | "system_reference" | "workflow";
  reference_id: number | null; material_id: number; material_revision_id: number;
  revision_no: number; kind: string | null; title: string | null; mime_type: string | null;
  content_hash: string; rights_status: string | null; public_use_allowed: boolean | null;
  model_use_allowed: boolean | null; commercial_use_allowed: boolean | null;
  attribution_text: string | null; unit_id: number | null; run_id: number | null;
  node_id: string | null; attempt_id: number | null; provenance: Record<string, unknown>;
};

export type VersionItem = {
  kind: string; id: string; version: string | number | null; status: string | null;
  checksum: string | null; createdAt: string | null; current: boolean; unitId?: number; source?: string;
};
export type Versions = Record<"brief" | "factBoundary" | "contentUnits" | "identitySnapshots" | "identityStates" | "workflows" | "runs" | "materials" | "contentOutputs", VersionItem[]>;
export type Activity = { id: number; event_type: string; entity_type: string | null; entity_id: string | null; actor: string | null; payload: Record<string, unknown>; created_at: string | null };
