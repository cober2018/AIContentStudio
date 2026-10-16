import { FormEvent, useEffect, useState } from "react";
import { api, ApiError } from "../../api";
import { Button, EmptyState, ErrorBanner, Field, Spinner, inputClass } from "../../components/ui";
import ProductStyleFields from "../ProductStyleFields";
import FormAssistancePanel from "../FormAssistancePanel";
import { productAssistanceFields, offerAssistanceFields } from "../productAssistanceFields";
import type { AssistanceField, AssistanceValue } from "../formAssistanceTypes";
import type { Brief, ProductContext, ProductCosts, ProductCostsView } from "./types";
import { emptyProductCosts, ProductCostFields, ProductMaterialCategories, ProductOfferFields, ProductSalesFields } from "./ProductSetupFields";

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
  const [product, setProduct] = useState<ProductContext | null>(null);
  const [costs, setCosts] = useState<ProductCosts>(emptyProductCosts);
  const [costEstimate, setCostEstimate] = useState<string | null>(null);
  const [costChanged, setCostChanged] = useState(false);
  const [costBusy, setCostBusy] = useState(false);
  const [costError, setCostError] = useState("");
  const [costLoaded, setCostLoaded] = useState(false);
  const [costReloadKey, setCostReloadKey] = useState(0);
  const [costSaved, setCostSaved] = useState(false);
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
    setProduct(current?.product_context || null); setProductChanged(false);
    setBrief(current); setHistory(revisions); setForm(next); setBaseline(JSON.stringify(next)); setConflict(false);
  }
  useEffect(() => { setLoading(true); reload().catch((err) => setError(err instanceof ApiError ? err.message : "无法读取任务书")).finally(() => setLoading(false)); }, [projectId]);
  useEffect(() => {
    if (!brief?.product_context) return;
    let active = true;
    setCostLoaded(false); setCostError(""); setCostSaved(false);
    api.get<ProductCostsView>(`/content-projects/${projectId}/product-costs`).then(view => {
      if (!active) return;
      setCosts(view.costs || emptyProductCosts()); setCostEstimate(view.estimated_contribution); setCostChanged(false); setCostLoaded(true);
    }).catch(error => { if (active) setCostError(error instanceof Error ? error.message : "内部经营资料读取失败"); });
    return () => { active = false; };
  }, [projectId, Boolean(brief?.product_context), costReloadKey]);
  function updateProduct(next: Partial<ProductContext>) {
    setProduct(previous => previous ? { ...previous, ...next } : previous);
    setProductChanged(true);
  }
  async function saveCosts() {
    setCostBusy(true); setCostError(""); setCostSaved(false);
    try {
      const view = await api.put<ProductCostsView>(`/content-projects/${projectId}/product-costs`, costs);
      setCosts(view.costs || emptyProductCosts()); setCostEstimate(view.estimated_contribution); setCostChanged(false); setCostSaved(true);
    } catch (error) { setCostError(error instanceof Error ? error.message : "内部经营资料保存失败"); }
    finally { setCostBusy(false); }
  }
  function field(key: keyof Form, label: string, rows = 1) {
    return <Field label={label}>{rows > 1 ? <textarea data-ai-field={key} className={inputClass} rows={rows} value={form[key]} onChange={(event) => setForm({ ...form, [key]: event.target.value })} /> : <input data-ai-field={key} className={inputClass} value={form[key]} onChange={(event) => setForm({ ...form, [key]: event.target.value })} />}</Field>;
  }
  async function save(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError("");
    try {
      const references = JSON.parse(form.references);
      if (!Array.isArray(references)) throw new Error("引用必须是 JSON 数组");
      const identityScope: unknown = form.identity_scope.trim() ? JSON.parse(form.identity_scope) : [];
      if (!Array.isArray(identityScope) || identityScope.some((entry) => entry === null || (typeof entry !== "object" && (!Number.isInteger(entry) || entry <= 0)) || Array.isArray(entry))) throw new Error("身份范围必须是正整数或身份引用对象组成的 JSON 数组");
      await api.post<Brief>(`${base}/revisions`, { expected_revision: brief?.revision_no || 0, objective: form.objective.trim(), primary_audience: form.primary_audience || null, core_message: form.core_message || null, angle: form.angle || null, required_evidence: lines(form.required_evidence), content_constraints: lines(form.content_constraints), identity_scope: identityScope, modality_scope: commas(form.modality_scope), channel_scope: commas(form.channel_scope), cta: form.cta || null, references, product_context: product ? { ...product, selling_points: product.selling_points.map(item => item.trim()).filter(Boolean), excluded_claims: product.excluded_claims.map(item => item.trim()).filter(Boolean), source_refs: productSources.filter(s => sourceIds.includes(s.source_document_id)).map(s => ({ source_id: s.source_document_id, checksum: s.sha256 })), material_refs: productMaterials.filter(m => materialIds.includes(m.material_revision_id)).map(m => ({ material_revision_id: m.material_revision_id, content_hash: m.content_hash, categories: product.material_refs?.find(ref => ref.material_revision_id === m.material_revision_id)?.categories || [] })), purchase_reason_source_ids: (product.purchase_reason_source_ids || []).filter(id => sourceIds.includes(id)), purchase_reason_material_revision_ids: (product.purchase_reason_material_revision_ids || []).filter(id => materialIds.includes(id)) } : null });
      await reload(); onSaved();
      if (product && !costChanged) {
        try {
          const view = await api.get<ProductCostsView>(`/content-projects/${projectId}/product-costs`);
          setCostEstimate(view.estimated_contribution);
        } catch (error) { setCostEstimate(null); setCostError(error instanceof Error ? error.message : "任务书已保存，内部估算刷新失败"); }
      }
    } catch (err) { setConflict(err instanceof ApiError && err.status === 409); setError(err instanceof Error ? err.message : "保存失败"); }
    finally { setBusy(false); }
  }
  if (loading) return <Spinner label="读取创作任务书…" />;
  const formKeys = ["objective", "primary_audience", "core_message", "angle", "required_evidence", "content_constraints", "cta"] as const;
  const assistanceFields: AssistanceField[] = [
    ...formKeys.map(key => ({ key, label: ({ objective: "创作目标", primary_audience: "面向谁", core_message: "核心购买理由", angle: "内容角度", required_evidence: "必需证据", content_constraints: "内容约束", cta: "行动引导" })[key], value: ["required_evidence", "content_constraints"].includes(key) ? lines(form[key]) : form[key], kind: ["required_evidence", "content_constraints"].includes(key) ? "list" as const : "text" as const, protected: ["objective", "primary_audience"].includes(key), apply: (value: AssistanceValue) => setForm(previous => ({ ...previous, [key]: Array.isArray(value) ? value.join("\n") : String(value ?? "") })) })),
    ...(product ? productAssistanceFields(product, updateProduct) : []), ...(product ? offerAssistanceFields(product.offer || null, offer => updateProduct({ offer })) : []), ];
  return <FormAssistancePanel key={projectId} versionKey={JSON.stringify([brief?.id,sourceIds,materialIds,product?.production_stages])} surface="product_brief" productionStages={product?.production_stages} projectId={projectId} fields={assistanceFields} sourceRefs={productSources.filter(source=>sourceIds.includes(source.source_document_id)).map(source=>({source_id:source.source_document_id,checksum:source.sha256}))} methodRefs={product?.style_ref ? [product.style_ref] : []} readOnly={readOnly || busy} context={{ category: product?.category || null, style_revision_id: product?.style_ref?.revision_id || null }}><section className="space-y-5"><div className="rounded-xl border border-slate-200 bg-white p-6"><div className="flex items-center justify-between"><h2 className="font-semibold">创作任务书</h2><span className="text-xs text-slate-500">{brief ? `当前第 ${brief.revision_no} 版` : "尚无版本"}</span></div><p className="mt-2 text-xs text-slate-500">每次保存创建新版本；旧版本不会被覆盖。</p>
    {error && <div className="mt-4"><ErrorBanner message={error} /></div>}{conflict && <Button className="mt-2" variant="secondary" onClick={() => reload().catch(() => setError("刷新失败"))}>重新读取最新版本</Button>}
    {!readOnly && <form onSubmit={save} className="mt-5 grid gap-4 md:grid-cols-2">{field("objective", "项目目标", 3)}{field("primary_audience", product ? "具体买家（主要受众）" : "主要受众", 3)}{field("core_message", product ? "一个核心购买理由（核心信息）" : "核心信息", 3)}{field("angle", "内容角度", 3)}{field("required_evidence", "必需证据（每行一项）", 3)}{field("content_constraints", "内容约束（每行一项）", 3)}{field("identity_scope", "身份范围 JSON（ID 或层级引用，suggested）", 3)}{field("modality_scope", "内容形态（逗号分隔）")}{field("channel_scope", "渠道（逗号分隔）")}{field("cta", "行动引导")}{field("references", "引用 JSON", 3)}{product && <fieldset className="space-y-3 md:col-span-2"><legend className="font-medium">商品资料</legend>
      <Field label="商品名称"><input required maxLength={300} className={inputClass} data-ai-field="name" value={product.name} onChange={event => updateProduct({ name: event.target.value })} /></Field>
      <Field label="型号／准确规格"><input maxLength={1000} className={inputClass} data-ai-field="variant" value={product.variant} onChange={event => updateProduct({ variant: event.target.value })} /></Field>
      <Field label="商品／购买链接"><input type="url" maxLength={1000} className={inputClass} data-ai-field="url" value={product.url || ""} onChange={event => updateProduct({ url: event.target.value || null })} /></Field>
      <Field label="商品说明"><textarea rows={4} maxLength={12000} className={inputClass} data-ai-field="description" value={product.description} onChange={event => updateProduct({ description: event.target.value })} /></Field>
      <Field label="补充卖点（每行一项，需资料支持）"><textarea className={inputClass} data-ai-field="selling_points" value={product.selling_points.join("\n")} onChange={event => updateProduct({ selling_points: event.target.value.split("\n") })} /></Field>
      <Field label="不使用的说法（每行一项）"><textarea className={inputClass} data-ai-field="excluded_claims" value={product.excluded_claims.join("\n")} onChange={event => updateProduct({ excluded_claims: event.target.value.split("\n") })} /></Field>
      <Field label="本版使用的商品来源（可多选）"><select multiple className={inputClass} value={sourceIds.map(String)} onChange={event => { setSourceIds(Array.from(event.target.selectedOptions, option => Number(option.value))); setProductChanged(true); }}>{productSources.map(source => <option key={source.source_document_id} value={source.source_document_id}>{source.title}</option>)}</select></Field>
      <Field label="本版使用的商品素材（可多选）"><select multiple className={inputClass} value={materialIds.map(String)} onChange={event => { setMaterialIds(Array.from(event.target.selectedOptions, option => Number(option.value))); setProductChanged(true); }}>{productMaterials.map(material => <option key={material.material_revision_id} value={material.material_revision_id}>{material.title}</option>)}</select></Field>
      <ProductMaterialCategories value={productMaterials.filter(material => materialIds.includes(material.material_revision_id)).map(material => ({ material_revision_id: material.material_revision_id, content_hash: material.content_hash, categories: product.material_refs?.find(ref => ref.material_revision_id === material.material_revision_id)?.categories || [] }))} materials={productMaterials.map(material => ({ id: material.material_revision_id, title: material.title }))} onChange={refs => updateProduct({ material_refs: refs })} />
      <ProductStyleFields projectId={projectId} category={product.category || ""} styleRef={product.style_ref} stages={product.production_stages} onChange={(category,style_ref)=>updateProduct({category,style_ref})} onStages={production_stages=>updateProduct({production_stages})} />
      <ProductSalesFields value={product} onChange={updateProduct} sources={productSources.filter(source => sourceIds.includes(source.source_document_id)).map(source => ({ id: source.source_document_id, title: source.title }))} materials={productMaterials.filter(material => materialIds.includes(material.material_revision_id)).map(material => ({ id: material.material_revision_id, title: material.title }))} />
      <ProductOfferFields value={product.offer || null} onChange={offer => updateProduct({ offer })} sources={productSources.filter(source => sourceIds.includes(source.source_document_id)).map(source => ({ id: source.source_document_id, title: source.title }))} />
    </fieldset>}<div className="flex items-end"><Button type="submit" disabled={busy || !form.objective.trim() || (JSON.stringify(form) === baseline && !productChanged)}>{busy ? "保存中…" : "保存新版本"}</Button></div></form>}
  </div>{product && !readOnly && <section className="space-y-3 rounded-xl border border-slate-200 bg-white p-6">{costError && <ErrorBanner message={costError} />}{costError && !costLoaded && <Button variant="secondary" onClick={() => setCostReloadKey(key => key + 1)}>重新读取内部经营资料</Button>}<fieldset disabled={!costLoaded || costBusy}><ProductCostFields value={costs} onChange={next => { setCosts(next); setCostChanged(true); setCostSaved(false); }} estimate={costChanged ? undefined : costEstimate} /></fieldset><Button variant="secondary" disabled={!costLoaded || !costChanged || costBusy || busy} onClick={() => void saveCosts()}>{costBusy ? "保存中…" : "单独保存内部经营资料"}</Button>{costSaved && <p role="status" className="text-sm">内部经营资料已保存。</p>}</section>}<div className="rounded-xl border border-slate-200 bg-white p-6"><h3 className="font-semibold">历史版本</h3>{history.length ? <ul className="mt-3 space-y-2">{history.map((item) => <li key={item.id} className="rounded-lg border p-3 text-sm"><details><summary className="cursor-pointer">第 {item.revision_no} 版 · {item.objective}</summary><div className="mt-3 grid gap-2 text-xs text-slate-600 sm:grid-cols-2"><p>主要受众：{item.primary_audience || "未填写"}</p><p>核心信息：{item.core_message || "未填写"}</p><p>内容角度：{item.angle || "未填写"}</p><p>行动引导：{item.cta || "未填写"}</p><p>必需证据：{item.required_evidence.join("；") || "无"}</p><p>内容约束：{item.content_constraints.join("；") || "无"}</p><p>身份 ID：{item.identity_scope.map((entry) => typeof entry === "number" ? String(entry) : JSON.stringify(entry)).join("、") || "无"}</p><p>内容形态：{item.modality_scope.join("、") || "无"}</p><p>渠道：{item.channel_scope.join("、") || "无"}</p><p className="sm:col-span-2">引用：{JSON.stringify(item.references)}</p></div></details><p className="mt-1 break-all text-xs text-slate-500">{item.checksum}</p></li>)}</ul> : <EmptyState title="还没有已保存的任务书" />}</div></section></FormAssistancePanel>;
}
