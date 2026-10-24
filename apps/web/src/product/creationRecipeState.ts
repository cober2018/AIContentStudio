export type StageRequest = { run_id: number; invocation_key: string; expected_resolution_hash: string; stage_override: Record<string, unknown> };
export type StageRecovery = { run_id: number; attempt_id?: number; invocation_key?: string };
export type StageLocal<P = { resolution_hash: string | null }, R = unknown> = {
  override: Record<string, unknown>;
  preview: P | null;
  result: R | null;
  request: StageRequest | null;
  rerunFeedbackAttemptId?: number;
};

export type StageFieldSchema = {
  type?: string; enum?: (string | number)[]; default?: unknown; minLength?: number; maxLength?: number;
  minimum?: number; maximum?: number; properties?: Record<string, StageFieldSchema>;
  items?: StageFieldSchema; minItems?: number; maxItems?: number; required?: string[];
};
export type StageContract = {
  stage_schema?: string; title?: string; category?: string;
  config_schema?: StageFieldSchema;
  ui_schema?: Record<string, { control?: string; label?: string }>;
  tunable_fields?: string[]; method_sources?: string[];
  supports_preview?: boolean; supports_run_override?: boolean; supports_candidates?: boolean;
  requires_human_acceptance?: boolean; output_contract?: Record<string, unknown>;
};
export type StageMethodSelection =
  | { source_kind: "capability_memory"; artifact_id: number; revision_id: number; arguments: Record<string, unknown> }
  | { source_kind: "installed_agent_skill"; skill_id: string; version: string; runtime_key: string; runtime_version: string }
  | { source_kind: "builtin"; key: string; version: string };
export type StageMethod = {
  name?: string; label?: string; source_kind: StageMethodSelection["source_kind"]; selection: StageMethodSelection;
  executable?: boolean; available?: boolean; reason?: string; scope_type?: string; scope?: Record<string, unknown>;
  args_schema?: StageFieldSchema; applicable_node_ids?: string[]; kind?: string;
  arguments_schema?: StageFieldSchema; matched_scope?: Record<string, unknown>;
};
export type StageMethods = {
  model_profiles: { id?: string; profile_id?: string; label?: string; provider?: string; model?: string;
    executable?: boolean; available?: boolean; reason?: string; capability?: string }[];
  methods: StageMethod[];
  media_profiles?: { id: string; label: string; model?: string; provider?: string; available: boolean;
    capabilities?: Record<string, { declared?: boolean; configured?: boolean; executable?: boolean;
      verified?: boolean; provider?: string; model?: string; state?: string; reason?: string }> }[];
  installed_skills?: { id: string; name?: string; version?: string; available: boolean; reason?: string }[];
};
export type StageDestination = "project" | "persona" | "account" | "series" | "capability";
export type StageDiff = { field?: string; node_id?: string; before?: unknown; after?: unknown };

export function stageValue(value: unknown): string {
  if (value === undefined || value === null) return "未设置";
  if (Array.isArray(value)) return value.map(stageValue).join("、");
  if (typeof value === "object") return Object.entries(value).map(([key, item]) => `${key}：${stageValue(item)}`).join("；");
  return String(value);
}

export function nextActionableStage(stages: { node_id: string; status: string; mode: string;
  accepted_target: unknown; dependencies: string[]; controls?: StageContract | null }[]): string | null {
  const review = stages.find(stage => stage.mode === "stage" && stage.status === "waiting_input" && !stage.accepted_target);
  if (review) return review.node_id;
  const next = stages.find(stage => stage.mode === "stage" && !stage.accepted_target
    && !["succeeded", "skipped", "running", "unknown"].includes(stage.status)
    && stage.dependencies.every(id => stages.some(upstream => upstream.node_id === id
      && (upstream.accepted_target || upstream.status === "skipped"
        || upstream.status === "succeeded" && upstream.controls?.requires_human_acceptance === false))));
  return next?.node_id || stages.find(stage => !stage.accepted_target)?.node_id || stages[0]?.node_id || null;
}

export function emptyStage<P, R>(): StageLocal<P, R> {
  return { override: {}, preview: null, result: null, request: null };
}

export function tuneStage<P, R>(state: StageLocal<P, R>, field: string, value: unknown): StageLocal<P, R> {
  // An unresolved request keeps its exact inputs until the original invocation is reconciled.
  if (state.request) return state;
  const override = { ...state.override };
  if (value === undefined) delete override[field];
  else override[field] = value;
  return { ...state, override, preview: null };
}

export function prepareStageRequest<P extends { resolution_hash: string | null }, R>(state: StageLocal<P, R>, runId: number, key: string): StageRequest {
  if (state.request) return state.request;
  if (!state.preview?.resolution_hash) throw new Error("stage_preview_required");
  return { run_id: runId, invocation_key: key, expected_resolution_hash: state.preview.resolution_hash, stage_override: { ...state.override } };
}

export function restoreStageRequest(result: { run_id?: unknown; status?: unknown; receipt?: Record<string, unknown>; resolved_stage?: { override?: Record<string, unknown> } }): StageRequest | null {
  if (!["running", "unknown"].includes(String(result.status)) || typeof result.run_id !== "number") return null;
  // An unknown attempt the user gave up is settled; keeping its request would hold the page in read-back mode.
  if (result.receipt?.abandoned) return null;
  const key = result.receipt?.invocation_key;
  const hash = result.receipt?.resolution_hash;
  if (typeof key !== "string" || typeof hash !== "string" || !/^[a-f0-9]{64}$/.test(hash)) return null;
  return { run_id: result.run_id, invocation_key: key, expected_resolution_hash: hash, stage_override: result.resolved_stage?.override || {} };
}

export function stageRecoveryTarget<P, R>(state: StageLocal<P, R>, runId: number | null, attemptId: number | null): StageRecovery | null {
  if (state.request) return { run_id: state.request.run_id, invocation_key: state.request.invocation_key };
  return runId && attemptId ? { run_id: runId, attempt_id: attemptId } : null;
}

export function needsStageRecovery<P>(state: StageLocal<P, Record<string, unknown>>, target: StageRecovery | null): boolean {
  return Boolean(state.request || target && (state.result?.run_id !== target.run_id || state.result?.attempt_id !== target.attempt_id));
}

export function recoveredStage<P>(state: StageLocal<P, Record<string, unknown>>, target: StageRecovery, value: Record<string, unknown>): StageLocal<P, Record<string, unknown>> {
  const receipt = value.receipt as Record<string, unknown> | undefined;
  if (value.run_id !== target.run_id || (target.attempt_id !== undefined && value.attempt_id !== target.attempt_id)
      || (target.invocation_key !== undefined && receipt?.invocation_key !== target.invocation_key)) {
    throw new Error("stage_recovery_identity_mismatch");
  }
  if (state.request && (state.request.run_id !== target.run_id || state.request.invocation_key !== receipt?.invocation_key)) return state;
  return { ...state, preview: null, result: value, request: restoreStageRequest(value) };
}
