import { useParams } from "react-router-dom";
import { ErrorBanner } from "../components/ui";
import { ProductionWorkspace } from "./ProductionWorkspace";

export function PersistentProductionPage() {
  const { projectId, unitId } = useParams();
  if (!projectId || !unitId) return <ErrorBanner message="缺少项目或内容单元。" />;
  return <ProductionWorkspace key={`${projectId}:${unitId}`} projectId={Number(projectId)} unitId={Number(unitId)} />;
}
