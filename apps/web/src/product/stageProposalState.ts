import type { TextDraft, TextPayload, AssetRef, EvidenceRef } from "./TextStudioModel";
import type { GraphicDraft, GraphicPayload, GraphicAssetRef, GraphicEvidenceRef } from "./GraphicStudioModel";
import type { VideoDraft, VideoPayload, VideoAssetRef, VideoEvidenceRef } from "./VideoStudioModel";

type Candidate<P, A, E, S extends string> = { candidate_id: string; candidate_hash: string; payload_schema: S; payload: P; asset_refs: A[]; evidence_refs: E[] };
export type StageCandidate = Candidate<TextPayload, AssetRef, EvidenceRef, "text.master.v2">
  | Candidate<GraphicPayload, GraphicAssetRef, GraphicEvidenceRef, "graphic.master.v2">
  | Candidate<VideoPayload, VideoAssetRef, VideoEvidenceRef, "video.master.v2">;
export type StageDraft = TextDraft | GraphicDraft | VideoDraft;
export type StageMaster = { id: number; revision_no: number; payload_hash: string; payload_schema?: string; payload: TextPayload | GraphicPayload | VideoPayload };
export type StageAcceptedEntity = { entity_id?: number; id?: number; output_kind?: string; kind?: string; revision_no?: number; accepted_hash?: string; payload_hash?: string; content_hash?: string; decision?: string; entity?: Record<string, unknown> };
export type StageResult = {
  run_id: number; node_id: string; attempt_id: number; status: string; is_current: boolean;
  receipt: { output_hash: string; resolution_hash: string; prompt_hash?: string; config_hash?: string; base_config_hash?: string; request_mode?: string; invocation_key?: string; abandoned?: { by_user_id: number; at: string } };
  expected_context_hash: string; expected_revision: number;
  output: { schema?: string; candidates?: StageCandidate[]; [key: string]: unknown };
  resolved_stage?: { effective_prompt?: string; system_prompt?: string; override?: Record<string, unknown>; base_config?: Record<string, unknown>; effective_config?: Record<string, unknown>; context?: { identity?: { id: number } | null; boundary?: { id: number } | null; modality?: string } };
  accepted_target: (StageAcceptedEntity & { entity_id: number; accepted_hash: string; decision: string; feedback_event_id?: number }) | null;
  accepted_master?: StageMaster | null;
  accepted_entity?: StageAcceptedEntity | null;
  domain_output?: Record<string, unknown> | null;
  feedback_event_id?: number;
  allowed_decisions?: string[];
};

export function proposalDraft(candidate: StageCandidate): StageDraft {
  if (candidate.payload_schema === "text.master.v2" && candidate.payload.document?.schema === "studio.text.document.v1") {
    return { payloadSchema: candidate.payload_schema, payload: structuredClone(candidate.payload), assetRefs: structuredClone(candidate.asset_refs), evidenceRefs: structuredClone(candidate.evidence_refs), aiEdits: [], invalidatedCitationIds: [] };
  }
  if (candidate.payload_schema === "graphic.master.v2" && candidate.payload.canvases?.length) {
    return { payloadSchema: candidate.payload_schema, payload: structuredClone(candidate.payload), assetRefs: structuredClone(candidate.asset_refs), evidenceRefs: structuredClone(candidate.evidence_refs) };
  }
  if (candidate.payload_schema === "video.master.v2" && Array.isArray(candidate.payload.script?.blocks) && Array.isArray(candidate.payload.shots)) {
    return { payloadSchema: candidate.payload_schema, payload: structuredClone(candidate.payload), assetRefs: structuredClone(candidate.asset_refs), evidenceRefs: structuredClone(candidate.evidence_refs) };
  }
  throw new Error("此候选的内容格式无法使用当前编辑器审阅。");
}

function normalized(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(normalized);
  if (value && typeof value === "object") return Object.fromEntries(Object.entries(value).sort(([a], [b]) => a.localeCompare(b)).map(([key, item]) => [key, normalized(item)]));
  return value;
}

export function proposalEdited(candidate: StageCandidate, draft: StageDraft): boolean {
  return candidate.payload_schema !== draft.payloadSchema || JSON.stringify(normalized([candidate.payload, candidate.asset_refs, candidate.evidence_refs])) !== JSON.stringify(normalized([draft.payload, draft.assetRefs, draft.evidenceRefs]));
}

export function stageAdoption(result: StageResult, candidate: StageCandidate, draft: StageDraft, key: string, note: string) {
  if (!result.is_current || result.accepted_target || result.status !== "waiting_input") throw new Error("stage_result_not_adoptable");
  if (!result.output.candidates?.some(item => item.candidate_id === candidate.candidate_id && item.candidate_hash === candidate.candidate_hash)) throw new Error("stage_candidate_not_found");
  if (![result.receipt.output_hash, result.receipt.resolution_hash, result.expected_context_hash, candidate.candidate_hash].every(hash => /^[a-f0-9]{64}$/.test(hash))) throw new Error("stage_result_receipt_invalid");
  if (candidate.payload_schema !== draft.payloadSchema) throw new Error("stage_proposal_schema_unsupported");
  return structuredClone({ run_id: result.run_id, attempt_id: result.attempt_id, expected_output_hash: result.receipt.output_hash,
    expected_resolution_hash: result.receipt.resolution_hash, expected_context_hash: result.expected_context_hash,
    candidate_id: candidate.candidate_id, candidate_hash: candidate.candidate_hash, expected_revision: result.expected_revision,
    adoption_key: key, payload_schema: draft.payloadSchema, payload: draft.payload, asset_refs: draft.assetRefs, evidence_refs: draft.evidenceRefs,
    decision: proposalEdited(candidate, draft) ? "accepted_with_edits" : "accepted", note });
}

export type StageAdoption = ReturnType<typeof stageAdoption>;

export type FeedbackTarget = { kind: "attempt" | "master" | "material"; revision_id: number; content_hash: string; candidate_id?: string };
export type FeedbackLocation = { kind: "text"; block_id: string; list_item_id?: string; quote: string } | { kind: "graphic"; canvas_id: string; layer_id?: string } | { kind: "time"; start_ms: number; end_ms: number };
export type StageFeedbackDecision = "rejected" | "rerun_requested" | "skipped_when_allowed" | "commented";
export function stageFeedback(result: StageResult, decision: StageFeedbackDecision, key: string, reasonTags: string[], note: string, located?: { target: FeedbackTarget; location: FeedbackLocation }) {
  if (!result.receipt || ![result.receipt.output_hash, result.receipt.resolution_hash].every(hash => /^[a-f0-9]{64}$/.test(hash))) throw new Error("当前尝试缺少可核对的结果回执，请先回读。");
  return { run_id: result.run_id, attempt_id: result.attempt_id, decision, reason_tags: reasonTags, note,
    ...located, feedback_key: key, expected_output_hash: result.receipt.output_hash, expected_resolution_hash: result.receipt.resolution_hash };
}
export type StageFeedbackRequest = ReturnType<typeof stageFeedback>;
