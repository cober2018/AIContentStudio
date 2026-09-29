import { lazy, Suspense } from "react";
import { Spinner } from "../components/ui";
import type { Modality } from "./project/projectTypes";
import type { TextStudioProps } from "./TextStudioShell";

const TextStudioShell = lazy(() => import("./TextStudioShell"));
const GraphicStudioShell = lazy(() => import("./GraphicStudioShell"));
const VideoStudioShell = lazy(() => import("./VideoStudioShell"));

export type StudioShellProps = { value: string; onChange: (value: string) => void; readOnly: boolean };
export type ModalityWorkspaceProps = ({ modality: "text" } & TextStudioProps) | ({ modality: Exclude<Modality, "text"> } & StudioShellProps);
export function ModalityWorkspace(props: ModalityWorkspaceProps) {
  return <Suspense fallback={<Spinner label="加载内容形态…" />}>
    {props.modality === "text" ? <TextStudioShell {...props} /> : props.modality === "graphic" ? <GraphicStudioShell {...props} /> : <VideoStudioShell {...props} />}
  </Suspense>;
}
