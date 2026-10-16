export type AssistanceValue = string | number | boolean | string[] | null;
export type AssistanceField = { key: string; label: string; value: AssistanceValue; apply: (value: AssistanceValue) => void; protected?: boolean; kind?: "text" | "number" | "list" | "fact" | "choice"; options?: string[]; unavailable?: string };
export const isUnfilled = (value: AssistanceValue) => value === null || (typeof value === "string" && !value.trim()) || (Array.isArray(value) && value.length === 0);
export const displayValue = (value: AssistanceValue) => Array.isArray(value) ? value.join("\n") : value === null ? "" : String(value);
export function editedValue(text: string, field: AssistanceField): AssistanceValue {
  if (field.kind === "number") { if (!text.trim()) return null; const value = Number(text); if (!Number.isFinite(value)) throw new Error("请输入有效数字"); return value; }
  if (field.kind === "list" || Array.isArray(field.value)) return text.split("\n").map(item => item.trim()).filter(Boolean);
  return text;
}
