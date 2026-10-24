import { useEffect, useState } from "react";
import { api, ApiError } from "../api";
import type { Definition, Persona, Project, SharedAsset, Unit, WorkflowBinding } from "./project/projectTypes";

export type Step = { id: number; node_id: string; node_type: string; label: string; status: string; params: Record<string, unknown>; output: Record<string, unknown>; error: string | null; stale_reason: string | null; attempt_no: number };
export type Run = { id: number; status: string; workflow_id: number; workflow_version: number | null; definition_checksum: string | null; identity_snapshot_id: number | null; identity_state: string; definition: Definition; steps: Step[]; error: string | null };
export type IdentitySnapshot = { id: number; brand_id: number | null; persona_id: number; account_id: number | null; series_id: number | null; revision_ids?: Record<string, number | null>; brand_revision_id: number | null; persona_revision_id: number | null; account_revision_id: number | null; series_revision_id: number | null; brand_voice_version_id: number | null; effective_profile: Record<string, unknown>; field_origins: Record<string, string>; checksum: string };
export type Attempt = { attempt_no: number; status: string; input_hash: string | null; output_hash: string | null; output_json: Record<string, unknown>; error: string | null };
export type DataPlugin = { key: string; name: string; category: string; available: boolean; reason: string | null; config_schema: Record<string, unknown> };
export type DataCapability = { id: number; key: string; version: string; plugin_key: string; source_ref: string; executable: boolean; verified: boolean };
export type ExecutionOption = { provider: string; model: string; available: boolean; reason: string | null; profiles?: { profile_id: string; provider: string; model: string; available: boolean }[] };
export type UnitOutput = { id: number; output_kind: "draft" | "candidate" | "material_revision" | "content_master_revision"; entity_id: number; run_id: number; node_id: string; attempt_id: number | null; provenance: Record<string, unknown> };

export const MODALITY_NAMES: Record<string, string> = { text: "文字生产", graphic: "图文生产", video: "视频生产" };

export function problem(error: unknown) { return error instanceof ApiError ? `${error.status} · ${error.message}` : "请求失败，请检查后端服务。"; }
export function pretty(value: unknown) { return JSON.stringify(value ?? {}, null, 2); }

// What the production page needs about a piece. Workflows run underneath platform-model writing; nobody edits them here.
export function useProductionWorkflow(projectId: number, unitId: number) {
  const base = `/content-projects/${projectId}/units/${unitId}`;
  const [project, setProject] = useState<Project | null>(null);
  const [role, setRole] = useState<string | null>(null);
  const [unit, setUnit] = useState<Unit | null>(null);
  const [persona, setPersona] = useState<Persona | null>(null);
  const [brandName, setBrandName] = useState<string | null>(null);
  const [accountName, setAccountName] = useState<string | null>(null);
  const [seriesName, setSeriesName] = useState<string | null>(null);
  const [snapshot, setSnapshot] = useState<IdentitySnapshot | null>(null);
  const [workflowSource, setWorkflowSource] = useState<string | null>(null);
  const [run, setRun] = useState<Run | null>(null);
  const [assets, setAssets] = useState<SharedAsset[]>([]);
  const [outputs, setOutputs] = useState<UnitOutput[]>([]);
  const [assetsOpen, setAssetsOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [workflowRevision, setWorkflowRevision] = useState(0);
  const readOnly = !["editor", "admin"].includes(role ?? "") || project?.status === "archived" || unit?.status === "archived" || unit?.lifecycle === "archived" || unit?.lifecycle === "deleted";

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setRole(null);
    Promise.all([
      api.get<{ role: string }>("/users/me", controller.signal),
      api.get<Project>(`/content-projects/${projectId}`, controller.signal),
      api.get<Unit>(base, controller.signal),
      api.get<WorkflowBinding>(`${base}/effective-workflow`, controller.signal),
      api.get<{ id: number; status: string }[]>(`${base}/runs`, controller.signal),
      api.get<SharedAsset[]>(`/content-projects/${projectId}/shared-assets`, controller.signal),
      api.get<UnitOutput[]>(`${base}/outputs`, controller.signal),
    ]).then(async ([me, nextProject, nextUnit, nextEffective, nextRuns, nextAssets, nextOutputs]) => {
      const product = nextUnit.production_domain === "product";
      const personas = product ? [] as Persona[] : await api.get<Persona[]>("/content-personas", controller.signal);
      setRole(me.role); setProject(nextProject); setUnit(nextUnit); setPersona(personas.find((item) => item.id === nextUnit.persona_id) || null);
      setWorkflowSource(nextEffective.source || null); setAssets(nextAssets); setOutputs(nextOutputs);
      if (nextRuns[0]) setRun(await api.get<Run>(`${base}/runs/${nextRuns[0].id}`, controller.signal));
    }).catch((err) => { if (!controller.signal.aborted) setError(problem(err)); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [projectId, unitId]);

  useEffect(() => {
    if (!unit) return;
    const personaBrand = persona?.brand_id;
    Promise.all([
      personaBrand ? api.get<{ name: string }>(`/content-brands/${personaBrand}`) : Promise.resolve(null),
      unit.account_id ? api.get<{ name: string }>(`/content-accounts/${unit.account_id}`) : Promise.resolve(null),
      unit.series_id ? api.get<{ name: string }>(`/content-series/${unit.series_id}`) : Promise.resolve(null),
    ]).then(([brand, account, series]) => { setBrandName(brand?.name || null); setAccountName(account?.name || null); setSeriesName(series?.name || null); }).catch((err) => setError(problem(err)));
  }, [unit?.id, persona?.brand_id]);
  const displayedSnapshotId = unit?.production_domain === "product" ? null : run ? run.identity_snapshot_id : unit?.identity_snapshot_id;
  useEffect(() => {
    setSnapshot(null);
    if (!displayedSnapshotId) return;
    let active = true;
    api.get<IdentitySnapshot>(`/identity-snapshots/${displayedSnapshotId}`).then((value) => { if (active) setSnapshot(value); }).catch((err) => { if (active) setError(problem(err)); });
    return () => { active = false; };
  }, [displayedSnapshotId]);

  // A recipe change re-binds the piece; read the unit and binding again so the page shows the current one.
  async function refreshWorkflowFromRecipe() {
    const [nextUnit, nextEffective] = await Promise.all([api.get<Unit>(base), api.get<WorkflowBinding>(`${base}/effective-workflow`)]);
    setUnit(nextUnit); setWorkflowSource(nextEffective.source || null);
  }
  const needsProductContext = unit?.production_domain === "product" && !!(unit.identity_snapshot_id || run?.identity_snapshot_id) && !["product_default", "project_override"].includes(workflowSource || "");
  async function continueProduct() {
    if (readOnly || busy) return;
    setBusy(true); setError("");
    try {
      setUnit(await api.post<Unit>(`${base}/product-context`));
      await refreshWorkflowFromRecipe();
      setWorkflowRevision(value => value + 1);
      setNotice("已切换为独立商品配置；历史运行与身份快照保留。");
    } catch (err) { setError(problem(err)); } finally { setBusy(false); }
  }
  return { readOnly, base, project, unit, persona, brandName, accountName, seriesName, snapshot, run, assets, outputs, assetsOpen, setAssetsOpen,
    loading, busy, error, setError, notice, dirty: false, design: false, workflowRevision, refreshWorkflowFromRecipe, continueProduct, needsProductContext };
}
