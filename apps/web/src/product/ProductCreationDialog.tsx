import { FormEvent, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, ApiError, currentUser } from "../api";
import { Button, ErrorBanner, Field, Modal, inputClass } from "../components/ui";

import ProductStyleFields from "./ProductStyleFields";
import FormAssistancePanel from "./FormAssistancePanel";
import { productAssistanceFields, offerAssistanceFields } from "./productAssistanceFields";
import type { AssistanceField, AssistanceValue } from "./formAssistanceTypes";
import ProductionStageControls, { type ProductionCatalog, type ProductionStages } from "./ProductionStageControls";
import { capabilityApi, type CapabilityArtifact } from "./capabilityMemoryTypes";
import { emptyProductCosts, ProductCostFields, ProductMaterialCategories, ProductOfferFields, ProductSalesFields } from "./project/ProductSetupFields";
import type { ProductContext, ProductCosts, ProductMaterialRef, ProductOffer, ProductSalesSetup } from "./project/types";

type Persona = { id: number; name: string; status: string };
type Source = { id: number; title: string; sha256?: string };
type PendingRequest = { production_stages?: ProductionStages; launch_key: string; persona_id: number; title: string; objective: string; primary_audience?: string | null; core_message?: string | null; angle?: string | null; cta: string | null; channel: string; modality: string; source_ids: number[]; material_revision_ids: number[]; product_context: ProductContext; private_costs?: ProductCosts };
function requestKey() {
  if (typeof crypto.randomUUID === "function") return crypto.randomUUID();
  return Array.from(crypto.getRandomValues(new Uint8Array(16)), byte => byte.toString(16).padStart(2, "0")).join("");
}
function readPending(key: string): PendingRequest | null {
  try {
    const value = JSON.parse(sessionStorage.getItem(key) || "null");
    return value && typeof value.launch_key === "string" && value.product_context && typeof value.product_context.name === "string" ? value : null;
  } catch { return null; }
}
type Launch = { project_id: number; unit_id: number; status: string; reason: string | null; href: string };

export function ProductCreationDialog({ onClose }: { onClose: () => void }) {
  const navigate = useNavigate();
  const owner = useRef(currentUser());
  const storageKey = `product-creation.pending.${owner.current}`;
  const [pending, setPending] = useState<PendingRequest | null>(() => readPending(storageKey));
  const launchKey = useRef(pending?.launch_key || requestKey());
  const [channels, setChannels] = useState<{ channel: string; label: string }[]>([]);
  const [materials, setMaterials] = useState<{ title: string; latest_revision: { id: number; content_hash: string } | null }[]>([]);
  const [materialIds, setMaterialIds] = useState<number[]>([]);
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [sourceIds, setSourceIds] = useState<number[]>([]);
  const [persona, setPersona] = useState("");
  const [name, setName] = useState("");
  const [variant, setVariant] = useState("");
  const [url, setUrl] = useState("");
  const [description, setDescription] = useState("");
  const [sellingPoints, setSellingPoints] = useState("");
  const [excludedClaims, setExcludedClaims] = useState("");
  const [objective, setObjective] = useState("介绍商品的适用场景和有依据的卖点，帮助受众判断是否适合购买");
  const [cta, setCta] = useState("");
  const [audience, setAudience] = useState("");
  const [coreMessage, setCoreMessage] = useState("");
  const [angle, setAngle] = useState("");
  const [sales, setSales] = useState<ProductSalesSetup>({ target_duration_seconds: 30 });
  const [materialRefs, setMaterialRefs] = useState<ProductMaterialRef[]>([]);
  const [costs, setCosts] = useState<ProductCosts>(emptyProductCosts);
  const [offer, setOffer] = useState<ProductOffer | null>(null);
  const [channel, setChannel] = useState("xiaohongshu");
  const [modality, setModality] = useState("video");
  const [busy, setBusy] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [productionStages, setProductionStages] = useState<ProductionStages>({});
  const [catalog, setCatalog] = useState<ProductionCatalog | null>(null);
  const [methods, setMethods] = useState<CapabilityArtifact[]>([]);
  const [saved, setSaved] = useState<Launch | null>(null);
  useEffect(() => {
    api.get<{ channel: string; label: string }[]>("/channels").then(setChannels).catch(() => setError("无法读取平台列表"));
    api.get<{ title: string; latest_revision: { id: number; content_hash: string } | null }[]>("/materials").then(setMaterials).catch(() => setError("无法读取素材列表"));
    Promise.all([api.get<Persona[]>("/content-personas"), api.get<Source[]>("/sources")])
      .then(([roles, docs]) => { setPersonas(roles.filter(r => r.status === "active")); setSources(docs); })
      .catch(e => setError(e instanceof Error ? e.message : "无法读取角色与资料"));
  }, []);
  useEffect(() => {
    let active = true;
    api.get<ProductionCatalog>("/content-identities/creative-catalog").then(value => { if (active) setCatalog(value); })
      .catch(() => { if (active) setError("无法读取阶段方法，请稍后重试"); });
    async function loadMethods() {
      const items: CapabilityArtifact[] = [];
      for (let offset = 0; ; offset += 100) {
        const page = await capabilityApi.list(`limit=100&offset=${offset}`);
        items.push(...page.items);
        if (offset + page.items.length >= page.total || !page.items.length) break;
      }
      if (active) setMethods(items);
    }
    void loadMethods().catch(() => { if (active) setError("无法读取已保存方法，请稍后重试"); });
    return () => { active = false; };
  }, []);
  async function upload(file: File) {
    setUploading(true); setError("");
    try {
      const data = new FormData(); data.append("file", file);
      const source = await api.upload<Source>("/sources/upload", data);
      setSources(current => [source, ...current]); setSourceIds(current => [...current, source.id]);
    } catch (e) { setError(e instanceof Error ? e.message : "资料上传失败"); }
    finally { setUploading(false); }
  }
  function restoreForm(body: PendingRequest) {
    setPersona(String(body.persona_id)); setName(body.product_context.name); setVariant(body.product_context.variant);
    setUrl(body.product_context.url || ""); setDescription(body.product_context.description);
    setSellingPoints(body.product_context.selling_points.join("\n")); setExcludedClaims(body.product_context.excluded_claims.join("\n"));
    setObjective(body.objective); setCta(body.cta || ""); setChannel(body.channel); setModality(body.modality);
    setSourceIds(body.source_ids); setMaterialIds(body.material_revision_ids);
    setProductionStages(body.production_stages || {});
    setOffer(body.product_context.offer || null);
    setAudience(body.primary_audience || ""); setCoreMessage(body.core_message || ""); setAngle(body.angle || "");
    setSales(body.product_context); setMaterialRefs(body.product_context.material_refs || []);
    setCosts(body.private_costs || emptyProductCosts());
  }
  async function dispatch(body: PendingRequest) {
    setBusy(true); setError("");
    try {
      if (currentUser() !== owner.current) throw new Error("当前账号已切换，请关闭窗口后重新进入");
      sessionStorage.setItem(storageKey, JSON.stringify(body));
      setPending(body);
      const result = await api.post<Launch>("/content-projects/from-product", body);
      sessionStorage.removeItem(storageKey); setPending(null); setSaved(result);
      if (result.status === "started") navigate(result.href);
    } catch (e) {
      const detail = e instanceof ApiError && e.detail && typeof e.detail === "object" ? e.detail as { project_created?: boolean; message?: string; launch?: Launch } : null;
      if (detail?.project_created === false || (e instanceof ApiError && [400, 422].includes(e.status) && detail?.project_created !== true)) {
        sessionStorage.removeItem(storageKey); setPending(null); restoreForm(body);
      } else if (detail?.project_created && detail.launch) {
        sessionStorage.removeItem(storageKey); setPending(null); setSaved(detail.launch);
      }
      const firstValidationError = e instanceof ApiError && Array.isArray(e.detail)
        ? e.detail.find(item => item && typeof item === "object" && typeof item.msg === "string") as { loc?: unknown[]; msg: string; type?: string } | undefined : undefined;
      const fieldNames: Record<string, string> = { original_price: "原价", sale_price: "售价", currency: "币种", checked_at: "核对时间", valid_until: "截止时间", source_id: "价格资料来源", timezone: "截止时区" };
      const path = firstValidationError?.loc?.filter(part => typeof part === "string" && part !== "body") as string[] | undefined;
      const field = path?.length ? fieldNames[path[path.length - 1]] || path.join(".") : "输入";
      const reason = firstValidationError?.type?.startsWith("decimal_") ? "请输入有效金额"
        : firstValidationError?.type?.startsWith("datetime_") ? "请输入含时区的有效日期时间"
        : firstValidationError?.msg.slice(0, 300);
      setError(detail?.message || (firstValidationError ? `${field}：${reason}` : e instanceof Error ? e.message : "请求结果未确认，恢复时会使用同一请求核对"));
    } finally { setBusy(false); }
  }
  function submit(event: FormEvent) {
    event.preventDefault();
    const selectedRefs = materials.filter(material => material.latest_revision && materialIds.includes(material.latest_revision.id)).map(material => ({
      material_revision_id: material.latest_revision!.id, content_hash: material.latest_revision!.content_hash,
      categories: materialRefs.find(ref => ref.material_revision_id === material.latest_revision!.id)?.categories || [],
    }));
    void dispatch({ primary_audience: audience || null, core_message: coreMessage || null, angle: angle || null,
      ...(Object.values(costs).some(value => value !== null) ? { private_costs: costs } : {}), launch_key: launchKey.current, persona_id: Number(persona), title: name.trim(), objective,
      ...(Object.keys(productionStages).length ? { production_stages: productionStages } : {}), cta: cta || null, channel, modality, source_ids: sourceIds, material_revision_ids: materialIds,
      product_context: { ...sales, production_stages: Object.keys(productionStages).length ? productionStages : null, material_refs: selectedRefs, purchase_reason_source_ids: (sales.purchase_reason_source_ids || []).filter(id => sourceIds.includes(id)), purchase_reason_material_revision_ids: (sales.purchase_reason_material_revision_ids || []).filter(id => materialIds.includes(id)), name: name.trim(), variant, url: url || null, description,
        selling_points: sellingPoints.split("\n").map(v => v.trim()).filter(Boolean),
        excluded_claims: excludedClaims.split("\n").map(v => v.trim()).filter(Boolean), offer } });
  }
  const productDraft: Partial<ProductContext> = { ...sales, name, variant, url: url || null, description, selling_points: sellingPoints.split("\n").filter(Boolean), excluded_claims: excludedClaims.split("\n").filter(Boolean) };
  function applyProduct(patch: Partial<ProductContext>) {
    if (patch.name !== undefined) setName(patch.name); if (patch.variant !== undefined) setVariant(patch.variant);
    if (patch.url !== undefined) setUrl(patch.url || ""); if (patch.description !== undefined) setDescription(patch.description);
    if (patch.selling_points) setSellingPoints(patch.selling_points.join("\n")); if (patch.excluded_claims) setExcludedClaims(patch.excluded_claims.join("\n"));
    setSales(previous => ({ ...previous, ...patch }));
  }
  const assistanceFields: AssistanceField[] = [ ...productAssistanceFields(productDraft, applyProduct), ...offerAssistanceFields(offer, setOffer),
    ...([{ key: "objective", label: "创作目标", value: objective, set: setObjective, protected: true }, { key: "primary_audience", label: "面向谁", value: audience, set: setAudience, protected: true }, { key: "core_message", label: "核心购买理由", value: coreMessage, set: setCoreMessage }, { key: "angle", label: "内容角度", value: angle, set: setAngle }, { key: "cta", label: "行动引导", value: cta, set: setCta }]).map(row => ({ key: row.key, label: row.label, value: row.value, protected: row.protected, apply: (value: AssistanceValue) => row.set(String(value ?? "")) })), ];
  return <Modal title="从商品开始创作" closeOnBackdrop={false} onClose={() => { if (!busy && !uploading) onClose(); }}>
    {error && <ErrorBanner message={error} />}
    {saved ? <div className="space-y-4"><p>商品项目已保存。{saved.status === "unknown" ? "生成结果待核对，请勿重复发起。" : "请在项目中补齐资料或创作流程后继续。"}</p><p className="text-sm text-slate-600">{saved.reason === "workflow_required" ? "该角色尚未绑定对应创作流程。" : saved.reason === "product_information_required" ? "商品链接未能获取资料，请补充说明或上传文档。" : saved.reason}</p><Button onClick={() => navigate(`/projects/${saved.project_id}?tab=brief`)}>打开创作任务书</Button><Button variant="secondary" onClick={() => navigate(saved.href)}>进入共同创作流程</Button></div> : pending ? <div className="space-y-4"><p>正在核对或等待恢复「{pending.product_context.name}」的创作请求。输入和请求标识已保留，恢复会继续同一项目。</p><Button disabled={busy} onClick={() => void dispatch(pending)}>{busy ? "正在处理…" : "恢复上次创作请求"}</Button></div> : <FormAssistancePanel surface="product_creation" productionStages={productionStages} fields={assistanceFields} context={{ style_revision_id: sales.style_ref?.revision_id || null }} sourceRefs={sources.filter(source=>sourceIds.includes(source.id) && source.sha256).map(source=>({source_id:source.id,checksum:source.sha256!}))} versionKey={JSON.stringify([sourceIds,materialIds,productionStages])} methodRefs={sales.style_ref ? [sales.style_ref] : []} readOnly={busy || uploading}><form onSubmit={submit} className="space-y-4">
      <p className="text-sm text-slate-600">商品直接进入创作，无需先建立内容机会。提供说明、链接或资料后，按所选角色生成。</p>
      <Field label="商品名称"><input autoFocus required maxLength={300} className={inputClass} data-ai-field="name" value={name} onChange={e => setName(e.target.value)} /></Field>
      <Field label="型号／规格（需要区分时填写）"><input className={inputClass} data-ai-field="variant" value={variant} onChange={e => setVariant(e.target.value)} /></Field>
      <Field label="商品链接（可选）"><input type="url" className={inputClass} data-ai-field="url" value={url} onChange={e => setUrl(e.target.value)} /></Field>
      <Field label="商品说明"><textarea rows={4} maxLength={12000} className={inputClass} data-ai-field="description" value={description} onChange={e => setDescription(e.target.value)} /></Field>
      <Field label="上传商品资料"><input type="file" accept=".pdf,.txt,.md,.csv,.json" disabled={uploading || busy} onChange={e => { const file = e.target.files?.[0]; if (file) void upload(file); }} /></Field>
      <Field label="已有资料（可多选）"><select multiple className={inputClass} value={sourceIds.map(String)} onChange={e => setSourceIds(Array.from(e.target.selectedOptions, o => Number(o.value)))}>{sources.map(s => <option key={s.id} value={s.id}>{s.title}</option>)}</select></Field>
      <Field label="商品图片／实拍片段（已有素材，可多选）"><select multiple className={inputClass} value={materialIds.map(String)} onChange={e => setMaterialIds(Array.from(e.target.selectedOptions, o => Number(o.value)))}>{materials.filter(m => m.latest_revision).map(m => <option key={m.latest_revision!.id} value={m.latest_revision!.id}>{m.title}</option>)}</select></Field>
      <ProductMaterialCategories value={materials.filter(material => material.latest_revision && materialIds.includes(material.latest_revision.id)).map(material => ({ material_revision_id: material.latest_revision!.id, content_hash: material.latest_revision!.content_hash, categories: materialRefs.find(ref => ref.material_revision_id === material.latest_revision!.id)?.categories || [] }))} materials={materials.filter(material => material.latest_revision).map(material => ({ id: material.latest_revision!.id, title: material.title }))} onChange={setMaterialRefs} />
      <Field label="表达角色"><select required className={inputClass} value={persona} onChange={e => setPersona(e.target.value)}><option value="">选择角色</option>{personas.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}</select></Field>
      <div className="grid grid-cols-2 gap-3"><Field label="内容形态"><select className={inputClass} value={modality} onChange={e => setModality(e.target.value)}><option value="video">视频</option><option value="text">文字</option><option value="graphic">图文</option></select></Field><Field label="平台"><select className={inputClass} value={channel} onChange={e => setChannel(e.target.value)}>{channels.map(c => <option key={c.channel} value={c.channel}>{c.label}</option>)}</select></Field></div>
      <details className="rounded-lg border p-3"><summary className="cursor-pointer font-medium">本次商品创作的阶段方法</summary>
        <p className="my-3 text-sm text-slate-600">开始创作前选择并冻结本次方法；保留角色风格，不写回角色默认配置。商品方法需要明确添加。</p>
        <ProductionStageControls system="product" catalog={catalog} methods={methods.filter(method => method.scope_type === "owner" || (method.scope_type === "persona" && method.scope.id === Number(persona)) || (method.scope_type === "channel" && method.scope.channel_id === channel))} value={productionStages} disabled={busy || uploading} origin="本次商品任务" onChange={setProductionStages} />
      </details>
      <Field label="内容目标"><textarea required className={inputClass} data-ai-field="objective" value={objective} onChange={e => setObjective(e.target.value)} /></Field>
      <Field label="具体买家（主要受众）"><textarea maxLength={2000} className={inputClass} data-ai-field="primary_audience" value={audience} onChange={event => setAudience(event.target.value)} /></Field>
      <Field label="一个核心购买理由（核心信息）"><textarea maxLength={2000} className={inputClass} data-ai-field="core_message" value={coreMessage} onChange={event => setCoreMessage(event.target.value)} /></Field>
      <Field label="内容角度"><input maxLength={2000} className={inputClass} data-ai-field="angle" value={angle} onChange={event => setAngle(event.target.value)} /></Field>
      <ProductStyleFields category={sales.category || ""} styleRef={sales.style_ref} onChange={(category,style_ref)=>setSales(previous=>({...previous,category,style_ref}))} onStages={setProductionStages} />
      <ProductSalesFields value={sales} onChange={setSales} sources={sources.filter(source => sourceIds.includes(source.id))} materials={materials.filter(material => material.latest_revision && materialIds.includes(material.latest_revision.id)).map(material => ({ id: material.latest_revision!.id, title: material.title }))} />
      <Field label="希望表达的卖点（每行一项，仍需资料支持）"><textarea className={inputClass} data-ai-field="selling_points" value={sellingPoints} onChange={e => setSellingPoints(e.target.value)} /></Field>
      <Field label="不使用的说法（每行一项）"><textarea className={inputClass} data-ai-field="excluded_claims" value={excludedClaims} onChange={e => setExcludedClaims(e.target.value)} /></Field>
      <ProductOfferFields value={offer} onChange={setOffer} sources={sources.filter(source => sourceIds.includes(source.id))} />
      <ProductCostFields value={costs} onChange={setCosts} />
      <Field label="行动引导（可选）"><input className={inputClass} data-ai-field="cta" value={cta} onChange={e => setCta(e.target.value)} /></Field>
      <p className="text-xs text-slate-500">资料充分时直接启动第一个创作阶段；事实确认、素材权限和后续接受操作在同一项目完成。</p>
      <Button type="submit" disabled={busy || uploading || !persona || !name.trim() || (!url && !description.trim() && !sourceIds.length)}>{busy ? "正在准备并开始创作…" : "开始创作"}</Button>
    </form></FormAssistancePanel>}
  </Modal>;
}
