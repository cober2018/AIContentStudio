export type ProductMaterialRef = { material_revision_id: number; content_hash: string; categories?: string[] };
export type ProductOffer = { text: string; checked_at: string | null; valid_until: string | null; currency: string | null; original_price: string | null; sale_price: string | null; source_id: number | null; conditions: string | null; timezone: string | null; [key: string]: unknown };
export type ProductSalesSetup = {
  production_stages?: import("../ProductionStageControls").ProductionStages | null; category?: string; style_ref?: { artifact_id: number; revision_id: number; content_hash: string } | null;
  buyer_situation?: string; purchase_reason_evidence?: string;
  purchase_reason_source_ids?: number[]; purchase_reason_material_revision_ids?: number[];
  main_objection?: string; objection_answer?: string; unsuitable_for?: string; seller_advantage?: string;
  target_duration_seconds?: number | null; expression_test?: "scene" | "demo" | "compare" | "faq" | "selection" | null;
};
export type ProductContext = ProductSalesSetup & {
  name: string; variant: string; description: string; url: string | null; selling_points: string[]; excluded_claims: string[];
  source_refs?: { source_id: number; checksum: string }[]; material_refs?: ProductMaterialRef[]; offer?: ProductOffer | null;
  [key: string]: unknown;
};
export type ProductCosts = {
  currency: string | null; basis: "per_order" | "total" | null; order_count: number | null;
  purchase: string | null; packaging: string | null; shipping: string | null; platform: string | null;
  promotion: string | null; production: string | null; returns_service: string | null;
};
export type ProductCostsView = { costs: ProductCosts | null; estimated_contribution: string | null };

export type Brief = {
  id: number; revision_no: number; checksum: string; objective: string;
  primary_audience: string | null; core_message: string | null; angle: string | null;
  required_evidence: string[]; content_constraints: string[]; identity_scope: (number | Record<string, number | null>)[];
  modality_scope: string[]; channel_scope: string[]; cta: string | null;
  product_context?: ProductContext | null;
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
  review: { units: { unit_id: number; title: string; summary: string; current_candidate: { id: number } | null }[] };
};

export type SharedAsset = {
  key: string; id: number; source_type: "project_upload" | "system_reference" | "workflow" | "project_folder_import";
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
  payloadHash?: string; contextHash?: string; payloadSchema?: string; identitySnapshotId?: number | null;
  briefRevisionId?: number | null; boundaryRevisionId?: number | null; workflowRunId?: number | null; projectOutputId?: number | null;
};
export type Versions = Record<"brief" | "factBoundary" | "contentUnits" | "contentMasters" | "identitySnapshots" | "identityStates" | "workflows" | "runs" | "materials" | "contentOutputs" | "candidates" | "approvals" | "deliveryTargets", VersionItem[]>;
export type Activity = { id: number; event_type: string; entity_type: string | null; entity_id: string | null; actor: string | null; payload: Record<string, unknown>; created_at: string | null };
