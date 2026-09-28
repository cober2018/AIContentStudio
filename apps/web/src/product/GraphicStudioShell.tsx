import { Field, inputClass } from "../components/ui";
import type { StudioShellProps } from "./ModalityWorkspace";

export default function GraphicStudioShell({ value, onChange, readOnly }: StudioShellProps) {
  return <Field label="Graphic Master 内容 JSON"><textarea aria-label="Graphic Master 内容 JSON" className={`${inputClass} font-mono`} rows={12} value={value} onChange={(event) => onChange(event.target.value)} readOnly={readOnly} /><p className="mt-2 text-xs text-slate-500">canvases 使用稳定 id/order；render_asset_ref 必须覆盖每个画布，并绑定项目可见的真实 render_output 素材。不包含画布编辑器或图片生成器。</p></Field>;
}
