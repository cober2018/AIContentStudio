import { Drawer } from "../components/ui";
import type { useProductionWorkflow } from "./useProductionWorkflow";
export function ProductionAssetDrawer({ workflow }: { workflow: ReturnType<typeof useProductionWorkflow> }) {
  const { assets, assetsOpen, setAssetsOpen } = workflow;
  if (!workflow.project || !workflow.unit) return null;
  return <>{assetsOpen && <Drawer title="项目共享素材（仅真实版本）" onClose={() => setAssetsOpen(false)}>{assets.length ? <ul className="space-y-3 text-sm">{assets.map((asset) => <li key={asset.key} className="rounded-lg border border-slate-200 p-3">Revision #{asset.material_revision_id} · {asset.kind || "素材"} · {asset.source_type === "workflow" ? `工作流 Run #${asset.run_id} / ${asset.node_id}` : asset.source_type === "project_upload" ? "项目上传" : "系统素材引用"} · {asset.rights_status || "权利待核对"}</li>)}</ul> : <p className="text-sm text-slate-500">暂无关联素材。</p>}</Drawer>}</>;
}
