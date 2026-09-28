import { lazy, Suspense } from "react";
import { Spinner } from "../components/ui";
import type { Modality } from "./project/projectTypes";

const TextStudioShell = lazy(() => import("./TextStudioShell"));
const GraphicStudioShell = lazy(() => import("./GraphicStudioShell"));
const VideoStudioShell = lazy(() => import("./VideoStudioShell"));

export type StudioShellProps = { value: string; onChange: (value: string) => void; readOnly: boolean };
export function ModalityWorkspace({ modality, ...props }: StudioShellProps & { modality: Modality }) {
  const Shell = modality === "text" ? TextStudioShell : modality === "graphic" ? GraphicStudioShell : VideoStudioShell;
  return <Suspense fallback={<Spinner label="加载内容形态…" />}><Shell {...props} /></Suspense>;
}
