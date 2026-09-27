import type { SharedAsset } from "./types";

export type { SharedAsset };
export type Modality = "text" | "graphic" | "video";
export type Definition = { nodes: WorkflowNode[]; edges: { from: string; to: string }[]; visual_order: string[] };
export type WorkflowNode = {
  id: string; kind: "Data" | "AI" | "Tool" | "Rule" | "Human" | "System";
  plugin: string; plugin_version?: string; label?: string; config: Record<string, unknown>;
  input_mapping?: Record<string, unknown>; output_mapping?: Record<string, unknown>;
  condition?: Record<string, unknown> | string; failure_policy?: string; enabled?: boolean;
};
export type WorkflowBinding = { revision: number; workflow_id: number | null; workflow_version: number | null; definition_checksum: string | null; definition: Definition; source?: string };
export type Persona = { id: number; name: string; brand_id?: number | null; status?: string };
export type Unit = { id: number; project_id: number; persona_id: number; account_id: number | null; series_id: number | null; identity_snapshot_id: number | null; identity_state: string; modality: Modality; channel_id: string | null; title: string; status: string; pinned_workflow_id: number | null };
export type Project = { id: number; title: string; objective: string; status: string; units: Unit[] };
