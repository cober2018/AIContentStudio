import { useTaskLink } from "../taskNavigation";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, ApiError } from "../../api";
import { Button, EmptyState, ErrorBanner, StatusBadge } from "../../components/ui";
import type { Persona, Project, Unit } from "./projectTypes";

const MODALITY_NAMES = { text: "文字", graphic: "图文", video: "视频" };
type Suggestion = { personaId: number; accountId: number | null; seriesId: number | null; modality: keyof typeof MODALITY_NAMES; channel: string; contentForm: string; reason: string; estimatedCost: string; estimatedValue: string; confidence: string; historyCoverage: string; capability: { executable: boolean; reason?: string }; unknowns: string[] };

export function ProjectMatrixTab({ project, personas, onAddPersona, onAddUnit, onEditUnit, onDeleteUnit, onConfirmSuggestions, readOnly = false }: {
  project: Project; personas: Persona[]; readOnly?: boolean; onAddPersona: () => void; onAddUnit: () => void;
  onEditUnit: (unit: Unit) => void; onDeleteUnit: (unit: Unit) => void; onConfirmSuggestions: (rows: Suggestion[]) => Promise<void>;
}) {
  const taskLink = useTaskLink();
  const navigate = useNavigate();
  const [copyIssue, setCopyIssue] = useState("");
  // A finished piece stays as it is; adjustments are made on a copy in the same project.
  async function copyUnit(unit: Unit) {
    setCopyIssue("");
    try {
      const copy = await api.post<{ id: number }>(`/content-projects/${project.id}/units/${unit.id}/copy`, {});
      navigate(taskLink(`/projects/${project.id}/units/${copy.id}/production?workstep=plan`));
    } catch (cause) { setCopyIssue(cause instanceof ApiError ? String((cause.detail as { message?: string } | undefined)?.message || cause.message) : "复制失败"); }
  }
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [selected, setSelected] = useState<number[]>([]);
  const [suggestionsOpen, setSuggestionsOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const active = project.units.filter((unit) => unit.status !== "archived" && unit.lifecycle !== "archived" && unit.lifecycle !== "deleted");
  const archived = project.units.filter((unit) => (unit.status === "archived" || unit.lifecycle === "archived") && unit.lifecycle !== "deleted");
  const writable = !readOnly && project.status !== "archived";
  async function loadSuggestions() {
    setBusy(true); setError("");
    try {
      const result = await api.get<{ persisted: boolean; items: Suggestion[] }>(`/content-projects/${project.id}/matrix/suggestions?limit=20`);
      setSuggestions(result.items); setSelected([]); setSuggestionsOpen(true);
    } catch (cause) { setError(cause instanceof ApiError ? cause.message : "读取建议失败，请重试。"); }
    finally { setBusy(false); }
  }
  async function confirmSelected() {
    if (!writable || !selected.length || !window.confirm(`只创建选中的 ${selected.length} 个内容单元？未选中的建议不会保存。`)) return;
    setBusy(true); setError("");
    try { await onConfirmSuggestions(selected.map((index) => suggestions[index])); setSuggestionsOpen(false); setSelected([]); }
    catch (cause) { setSuggestionsOpen(false); setSelected([]); setError(cause instanceof Error ? cause.message : "创建内容单元失败，请检查已创建项目后重试。"); }
    finally { setBusy(false); }
  }
  return <section className="rounded-xl border border-slate-200 bg-white p-5">
    <div className="mb-4 flex flex-wrap items-center justify-between gap-3"><h2 className="font-semibold">内容矩阵</h2>{writable && <div className="flex flex-wrap gap-2"><Button variant="secondary" disabled={busy} onClick={loadSuggestions}>查看矩阵建议</Button><Button variant="secondary" onClick={onAddPersona}>新增身份</Button><Button onClick={onAddUnit}>新增内容单元</Button><Link to={`/production?workspace=product&project=${project.id}`} className="rounded-md border border-slate-300 px-3 py-2 text-xs">加商品视频</Link></div>}</div>
    {error && <div className="mb-4"><ErrorBanner message={error} /></div>}
    {suggestionsOpen && <div className="mb-5 rounded-xl border border-indigo-100 bg-indigo-50 p-4"><div className="flex items-center justify-between"><h3 className="font-semibold">仅供选择的建议 · {suggestions.length}</h3><Button size="sm" variant="secondary" onClick={() => setSuggestionsOpen(false)}>关闭</Button></div><p className="mt-1 text-xs text-slate-600">建议本身不会创建单元或交付目标；成本、价值与可信度未知时不做排序承诺。</p>{suggestions.length === 0 ? <p className="mt-3 text-sm text-slate-500">当前项目范围内没有可用的新建议。</p> : <div className="mt-3 space-y-2">{suggestions.map((item, index) => <label key={`${item.personaId}-${item.accountId}-${item.seriesId}-${item.channel}-${item.contentForm}`} className="flex gap-3 rounded-lg border border-slate-200 bg-white p-3"><input type="checkbox" disabled={!writable || busy || !item.capability.executable} checked={selected.includes(index)} onChange={(event) => setSelected(event.target.checked ? [...selected, index] : selected.filter((row) => row !== index))} /><span className="text-sm"><strong>{personas.find((persona) => persona.id === item.personaId)?.name || `身份 #${item.personaId}`}</strong> · {MODALITY_NAMES[item.modality]} · {item.channel}/{item.contentForm}<span className="block text-xs text-slate-500">{item.reason} · 历史覆盖：{item.historyCoverage} · 成本/价值/可信度：{item.estimatedCost}/{item.estimatedValue}/{item.confidence}</span>{!item.capability.executable && <span className="block text-xs text-amber-700">当前不可执行：{item.capability.reason || "能力未验证"}</span>}</span></label>)}</div>}<Button className="mt-3" disabled={busy || !writable || !selected.length} onClick={confirmSelected}>仅确认所选 {selected.length} 项</Button></div>}
    {copyIssue && <ErrorBanner message={copyIssue} />}
    {active.length ? <div className="space-y-3">{active.map((unit) => <article key={unit.id} className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-200 p-4"><div><div className="flex gap-2"><h3 className="font-semibold">{unit.title}</h3><StatusBadge status={unit.status} /></div><p className="mt-1 text-xs text-slate-500">{unit.production_domain === "product" ? `商品视频 / SKU · ${unit.title}` : `${personas.find((persona) => persona.id === unit.persona_id)?.name || `身份 #${unit.persona_id}`} · ${unit.account_id ? `账号 #${unit.account_id}` : "无账号"} · ${unit.series_id ? `栏目 #${unit.series_id}` : "无栏目"} · ${MODALITY_NAMES[unit.modality]}`} · {unit.channel_id || "未选择渠道"}</p><p className="mt-1 text-xs text-slate-500">{unit.production_domain === "product" ? "独立商品配置" : `身份：${unit.identity_snapshot_id ? `快照 #${unit.identity_snapshot_id}` : "Legacy / 未冻结身份"}`} · 固定工作流：{unit.pinned_workflow_id ? `#${unit.pinned_workflow_id}` : "未设置"}</p></div><div className="flex gap-2"><Link to={taskLink(`/projects/${project.id}/units/${unit.id}/production`)} className="rounded-md bg-indigo-600 px-3 py-2 text-xs text-white">进入生产</Link>{writable && <><Button size="sm" variant="secondary" onClick={() => onEditUnit(unit)}>{unit.production_domain === "product" ? "商品制作设置" : "编辑"}</Button>{unit.production_domain !== "product" && <Button size="sm" variant="secondary" onClick={() => void copyUnit(unit)}>复制一份</Button>}<Button size="sm" variant="danger" onClick={() => onDeleteUnit(unit)}>删除</Button></>}</div></article>)}</div> : <EmptyState title="还没有内容单元" hint={writable ? "先创建身份，再添加文字、图文或视频单元。" : "当前项目只读，可查看已有作品和历史。"} />}
    {archived.length > 0 && <details className="mt-5 border-t pt-4"><summary className="cursor-pointer text-sm text-slate-600">已归档单元（{archived.length}）</summary><div className="mt-3 space-y-2">{archived.map((unit) => <div key={unit.id} className="flex items-center justify-between rounded-lg bg-slate-50 p-3 text-sm"><span>{unit.title} · #{unit.id} · {MODALITY_NAMES[unit.modality]}</span><Link className="text-indigo-600" to={taskLink(`/projects/${project.id}/units/${unit.id}/production`)}>查看历史</Link></div>)}</div></details>}
  </section>;
}
