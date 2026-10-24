import { useQuery } from "@tanstack/react-query";
import { api, currentUser } from "../api";

export type Brief = { query_zh?: string; queries_en?: string[]; keywords_en?: string[]; t2v_prompt?: string; frame_prompt?: string; prompt?: string; gen_mode?: "text" | "frame"; footage?: "real" | "motion"; must_show?: string; run_id: number; segment_id: string };
export type AutoSource = { source: "stock" | "ae_template" | "ai_image"; score?: number | null; template?: string; version?: string; reason?: string };
export type Pick = { material_revision_id: number; title: string | null; provider_label: string | null; media_type: string | null; uploaded: boolean; run_id: number; auto?: AutoSource };
export type AutofillRow = { outcome: "stock" | "ae_template" | "ai_image" | "gap" | "kept"; source?: string | null; score?: number | null; reason?: string };
export type Slot = {
  id: string; order: number; label: string; narration: string; visual: string; purpose: string; requirements: string[]; duration_ms: number | null;
  bound_revision_id: number | null; brief: Brief | null; latest: { run_id: number; segment_id: string; status: string } | null;
  picks: Pick[]; candidate_count: number; brief_stale: boolean; status: "missing" | "candidates" | "chosen"; autofill: AutofillRow | null;
};
export type ShotSlotsView = { source: "plan" | "draft"; counts: Record<Slot["status"], number>; shots: Slot[] };

export function useShotSlots(projectId: number, unitId: number) {
  return useQuery({
    queryKey: ["shot-slots", currentUser(), projectId, unitId], retry: false,
    queryFn: () => api.get<ShotSlotsView>(`/content-projects/${projectId}/units/${unitId}/shot-slots`),
    // Searches run in the background; keep polling only while one is going.
    refetchInterval: query => query.state.data?.shots.some(slot => slot.latest && ["queued", "running"].includes(slot.latest.status)) ? 4000 : false,
  });
}
