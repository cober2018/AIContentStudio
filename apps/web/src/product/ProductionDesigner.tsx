import { ProductionWorkspace } from "./ProductionWorkspace";

export function ProductionDesigner({ projectId, unitId }: { projectId: number; unitId: number }) {
  return <ProductionWorkspace key={`${projectId}:${unitId}`} projectId={projectId} unitId={unitId} />;
}
