import { Field, inputClass } from "../components/ui";
import type { StudioShellProps } from "./ModalityWorkspace";

export default function TextStudioShell({ value, onChange, readOnly }: StudioShellProps) {
  return <Field label="Text Master 内容 JSON"><textarea aria-label="Text Master 内容 JSON" className={`${inputClass} font-mono`} rows={12} value={value} onChange={(event) => onChange(event.target.value)} readOnly={readOnly} /><p className="mt-2 text-xs text-slate-500">最小内容壳：markdown 为正文，可保留 document / structured / citations；本阶段不包含专业富文本编辑器。</p></Field>;
}
