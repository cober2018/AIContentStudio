import { useParams } from "react-router-dom";
import { ErrorBanner } from "../components/ui";
import { ProductionDesigner } from "./ProductionDesigner";

export function PersistentProductionPage() {
  const { projectId, unitId } = useParams();
  if (!projectId || !unitId) return <ErrorBanner message="缺少项目或内容单元。" />;
  return <ProductionDesigner projectId={Number(projectId)} unitId={Number(unitId)} />;
}
