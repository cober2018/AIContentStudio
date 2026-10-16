import { FormEvent, useEffect, useState } from "react";
import { api, ApiError } from "../../api";
import { Button, EmptyState, ErrorBanner, Field, Spinner, inputClass } from "../../components/ui";
import type { Brief } from "./types";

type Form = {
  objective: string; primary_audience: string; core_message: string; angle: string;
  required_evidence: string; content_constraints: string; identity_scope: string;
  modality_scope: string; channel_scope: string; cta: string; references: string;
};
const EMPTY: Form = { objective: "", primary_audience: "", core_message: "", angle: "", required_evidence: "", content_constraints: "", identity_scope: "", modality_scope: "", channel_scope: "", cta: "", references: "[]" };
const lines = (value: string) => value.split("\n").map((item) => item.trim()).filter(Boolean);
const commas = (value: string) => value.split(",").map((item) => item.trim()).filter(Boolean);

function toForm(brief: Brief | null): Form {
  if (!brief) return { ...EMPTY };
  return { objective: brief.objective, primary_audience: brief.primary_audience || "", core_message: brief.core_message || "", angle: brief.angle || "", required_evidence: brief.required_evidence.join("\n"), content_constraints: brief.content_constraints.join("\n"), identity_scope: JSON.stringify(brief.identity_scope, null, 2), modality_scope: brief.modality_scope.join(","), channel_scope: brief.channel_scope.join(","), cta: brief.cta || "", references: JSON.stringify(brief.references, null, 2) };
}

export function ProjectBriefTab({ projectId, onSaved, readOnly = false }: { projectId: number; onSaved: () => void; readOnly?: boolean }) {
  const base = `/content-projects/${projectId}/brief`;
  const [brief, setBrief] = useState<Brief | null>(null);
  const [productName, setProductName] = useState("");
  const [productVariant, setProductVariant] = useState("");
  const [productDescription, setProductDescription] = useState("");
  const [productSources, setProductSources] = useState<{ source_document_id: number; title: string; sha256: string }[]>([]);
  const [productMaterials, setProductMaterials] = useState<{ material_revision_id: number; title: string; content_hash: string }[]>([]);
  const [sourceIds, setSourceIds] = useState<number[]>([]);
  const [materialIds, setMaterialIds] = useState<number[]>([]);
  const [productChanged, setProductChanged] = useState(false);
  const [history, setHistory] = useState<Brief[]>([]);
  const [form, setForm] = useState<Form>({ ...EMPTY });
  const [baseline, setBaseline] = useState(JSON.stringify(EMPTY));
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [conflict, setConflict] = useState(false);
  async function reload() {
    const [current, revisions] = await Promise.all([api.get<Brief | null>(base), api.get<Brief[]>(`${base}/revisions`)]);
    if (current?.product_context) {
      const [sources, materials] = await Promise.all([
        api.get<{ source_document_id: number; title: string; sha256: string }[]>(`/content-projects/${projectId}/sources`),
        api.get<{ material_revision_id: number; title: string; content_hash: string }[]>(`/content-projects/${projectId}/shared-assets`),
      ]);
      setProductSources(sources); setProductMaterials(materials);
      setSourceIds((current.product_context.source_refs || []).map(r => r.source_id));
      setMaterialIds((current.product_context.material_refs || []).map(r => r.material_revision_id));
    }
    const next = toForm(current);
    setProductName(current?.product_context?.name || ""); setProductVariant(current?.product_context?.variant || ""); setProductDescription(current?.product_context?.description || ""); setProductChanged(false);
    setBrief(current); setHistory(revisions); setForm(next); setBaseline(JSON.stringify(next)); setConflict(false);
  }
  useEffect(() => { setLoading(true); reload().catch((err) => setError(err instanceof ApiError ? err.message : "无法读取任务书")).finally(() => setLoading(false)); }, [projectId]);
  function field(key: keyof Form, label: string, rows = 1) {
    return <Field label={label}>{rows > 1 ? <textarea className={inputClass} rows={rows} value={form[key]} onChange={(event) => setForm({ ...form, [key]: event.target.value })} /> : <input className={inputClass} value={form[key]} onChange={(event) => setForm({ ...form, [key]: event.target.value })} />}</Field>;
  }
  async function save(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError("");
    try {
      const references = JSON.parse(form.references);
      if (!Array.isArray(references)) throw new Error("引用必须是 JSON 数组");
      const identityScope: unknown = form.identity_scope.trim() ? JSON.parse(form.identity_scope) : [];
      if (!Array.isArray(identityScope) || identityScope.some((entry) => entry === null || (typeof entry !== "object" && (!Number.isInteger(entry) || entry <= 0)) || Array.isArray(entry))) throw new Error("身份范围必须是正整数或身份引用对象组成的 JSON 数组");
      await api.post<Brief>(`${base}/revisions`, { expected_revision: brief?.revision_no || 0, objective: form.objective.trim(), primary_audience: form.primary_audience || null, core_message: form.core_message || null, angle: form.angle || null, required_evidence: lines(form.required_evidence), content_constraints: lines(form.content_constraints), identity_scope: identityScope, modality_scope: commas(form.modality_scope), channel_scope: commas(form.channel_scope), cta: form.cta || null, references, product_context: brief?.product_context ? { ...brief.product_context, name: productName, variant: productVariant, description: productDescription, source_refs: productSources.filter(s => sourceIds.includes(s.source_document_id)).map(s => ({ source_id: s.source_document_id, checksum: s.sha256 })), material_refs: productMaterials.filter(m => materialIds.includes(m.material_revision_id)).map(m => ({ material_revision_id: m.material_revision_id, content_hash: m.content_hash })) } : null });
      await reload(); onSaved();
    } catch (err) { setConflict(err instanceof ApiError && err.status === 409); setError(err instanceof Error ? err.message : "保存失败"); }
    finally { setBusy(false); }
  }
  if (loading) return <Spinner label="读取创作任务书…" />;
  return <section className="space-y-5"><div className="rounded-xl border border-slate-200 bg-white p-6"><div className="flex items-center justify-between"><h2 className="font-semibold">创作任务书</h2><span className="text-xs text-slate-500">{brief ? `当前第 ${brief.revision_no} 版` : "尚无版本"}</span></div><p className="mt-2 text-xs text-slate-500">每次保存创建新版本；旧版本不会被覆盖。</p>
    {error && <div className="mt-4"><ErrorBanner message={error} /></div>}{conflict && <Button className="mt-2" variant="secondary" onClick={() => reload().catch(() => setError("刷新失败"))}>重新读取最新版本</Button>}
    {!readOnly && <form onSubmit={save} className="mt-5 grid gap-4 md:grid-cols-2">{field("objective", "项目目标", 3)}{field("primary_audience", "主要受众", 3)}{field("core_message", "核心信息", 3)}{field("angle", "内容角度", 3)}{field("required_evidence", "必需证据（每行一项）", 3)}{field("content_constraints", "内容约束（每行一项）", 3)}{field("identity_scope", "身份范围 JSON（ID 或层级引用，suggested）", 3)}{field("modality_scope", "内容形态（逗号分隔）")}{field("channel_scope", "渠道（逗号分隔）")}{field("cta", "行动引导")}{field("references", "引用 JSON", 3)}{brief?.product_context && <fieldset className="space-y-3 md:col-span-2"><legend className="font-medium">商品资料</legend><Field label="商品名称"><input required className={inputClass} value={productName} onChange={e => { setProductName(e.target.value); setProductChanged(true); }} /></Field><Field label="型号／规格"><input className={inputClass} value={productVariant} onChange={e => { setProductVariant(e.target.value); setProductChanged(true); }} /></Field><Field label="商品说明"><textarea rows={4} className={inputClass} value={productDescription} onChange={e => { setProductDescription(e.target.value); setProductChanged(true); }} /></Field><Field label="本版使用的商品来源（可多选）"><select multiple className={inputClass} value={sourceIds.map(String)} onChange={e => { setSourceIds(Array.from(e.target.selectedOptions, o => Number(o.value))); setProductChanged(true); }}>{productSources.map(s => <option key={s.source_document_id} value={s.source_document_id}>{s.title}</option>)}</select></Field><Field label="本版使用的商品素材（可多选）"><select multiple className={inputClass} value={materialIds.map(String)} onChange={e => { setMaterialIds(Array.from(e.target.selectedOptions, o => Number(o.value))); setProductChanged(true); }}>{productMaterials.map(m => <option key={m.material_revision_id} value={m.material_revision_id}>{m.title}</option>)}</select></Field></fieldset>}<div className="flex items-end"><Button type="submit" disabled={busy || !form.objective.trim() || (JSON.stringify(form) === baseline && !productChanged)}>{busy ? "保存中…" : "保存新版本"}</Button></div></form>}
  </div><div className="rounded-xl border border-slate-200 bg-white p-6"><h3 className="font-semibold">历史版本</h3>{history.length ? <ul className="mt-3 space-y-2">{history.map((item) => <li key={item.id} className="rounded-lg border p-3 text-sm"><details><summary className="cursor-pointer">第 {item.revision_no} 版 · {item.objective}</summary><div className="mt-3 grid gap-2 text-xs text-slate-600 sm:grid-cols-2"><p>主要受众：{item.primary_audience || "未填写"}</p><p>核心信息：{item.core_message || "未填写"}</p><p>内容角度：{item.angle || "未填写"}</p><p>行动引导：{item.cta || "未填写"}</p><p>必需证据：{item.required_evidence.join("；") || "无"}</p><p>内容约束：{item.content_constraints.join("；") || "无"}</p><p>身份 ID：{item.identity_scope.map((entry) => typeof entry === "number" ? String(entry) : JSON.stringify(entry)).join("、") || "无"}</p><p>内容形态：{item.modality_scope.join("、") || "无"}</p><p>渠道：{item.channel_scope.join("、") || "无"}</p><p className="sm:col-span-2">引用：{JSON.stringify(item.references)}</p></div></details><p className="mt-1 break-all text-xs text-slate-500">{item.checksum}</p></li>)}</ul> : <EmptyState title="还没有已保存的任务书" />}</div></section>;
}
