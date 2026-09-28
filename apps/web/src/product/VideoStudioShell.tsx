import { Field, inputClass } from "../components/ui";
import type { StudioShellProps } from "./ModalityWorkspace";

export default function VideoStudioShell({ value, onChange, readOnly }: StudioShellProps) {
  return <Field label="Video Master 内容 JSON"><textarea aria-label="Video Master 内容 JSON" className={`${inputClass} font-mono`} rows={12} value={value} onChange={(event) => onChange(event.target.value)} readOnly={readOnly} /><p className="mt-2 text-xs text-slate-500">保存 script / shots / timeline；最终 render_asset_ref 必须引用真实视频版本。本阶段不包含时间线编辑器、合成器或自动视频生成。</p></Field>;
}
