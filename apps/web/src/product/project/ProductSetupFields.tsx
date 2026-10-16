import { Field, inputClass } from "../../components/ui";
import type { ProductCosts, ProductMaterialRef, ProductOffer, ProductSalesSetup } from "./types";

type Reference = { id: number; title: string };
const salesFields = [
  ["buyer_situation", "具体使用场景：在哪里、遇到什么问题"],
  ["purchase_reason_evidence", "这个购买理由的依据（缺资料写待确认）"],
  ["main_objection", "买家最大的顾虑"], ["objection_answer", "有依据的回答"],
  ["unsuitable_for", "不适用的人或条件"], ["seller_advantage", "为什么向这家买（仅填写有依据的优势）"],
] as const;

export function ProductSalesFields({ value, onChange, sources, materials }: {
  value: ProductSalesSetup; onChange: (next: ProductSalesSetup) => void; sources: Reference[]; materials: Reference[];
}) {
  return <fieldset className="grid gap-3 md:grid-cols-2"><legend className="mb-3 font-medium">本条视频的销售思路</legend>
    {salesFields.map(([key, label]) => <Field key={key} label={label}><textarea data-ai-field={key} rows={2} maxLength={2000} className={inputClass} value={value[key] || ""} onChange={event => onChange({ ...value, [key]: event.target.value })} /></Field>)}
    <Field label="购买理由引用的资料（可多选）"><select multiple className={inputClass} value={(value.purchase_reason_source_ids || []).map(String)} onChange={event => onChange({ ...value, purchase_reason_source_ids: Array.from(event.target.selectedOptions, option => Number(option.value)) })}>{sources.map(source => <option key={source.id} value={source.id}>{source.title}</option>)}</select></Field>
    <Field label="购买理由引用的素材版本（可多选）"><select multiple className={inputClass} value={(value.purchase_reason_material_revision_ids || []).map(String)} onChange={event => onChange({ ...value, purchase_reason_material_revision_ids: Array.from(event.target.selectedOptions, option => Number(option.value)) })}>{materials.map(material => <option key={material.id} value={material.id}>{material.title}</option>)}</select></Field>
    <Field label="目标时长（秒，可调整）"><input data-ai-field="target_duration_seconds" type="number" min={1} max={3600} step={1} className={inputClass} value={value.target_duration_seconds ?? ""} onChange={event => onChange({ ...value, target_duration_seconds: event.target.value ? Number(event.target.value) : null })} /></Field>
    <Field label="表达小测试（可选，只选一个变化因素）"><select data-ai-field="expression_test" className={inputClass} value={value.expression_test || ""} onChange={event => onChange({ ...value, expression_test: (event.target.value || null) as ProductSalesSetup["expression_test"] })}><option value="">不做小测试</option><option value="scene">场景</option><option value="demo">演示</option><option value="compare">对比</option><option value="faq">答疑</option><option value="selection">选购</option></select></Field>
    <p className="text-xs text-slate-500 md:col-span-2">引用只关联已选资料和精确素材版本，不代表事实已核实。AI情境图不能证明实测表现、真实反馈或尺寸。</p>
  </fieldset>;
}

const categories = [["front", "正面"], ["side", "侧面"], ["back", "背面"], ["detail", "细节"], ["dimensions", "尺寸"], ["real_product", "真实产品图"], ["real_demo", "真实操作"], ["measurement", "实测"], ["comparison", "同条件对比"], ["specification", "参数文件"], ["authorized_feedback", "授权反馈"], ["ai_scene", "AI情境"]];
export function ProductMaterialCategories({ value, materials, onChange }: { value: ProductMaterialRef[]; materials: Reference[]; onChange: (next: ProductMaterialRef[]) => void }) {
  return <div className="space-y-3">{value.map(ref => <fieldset key={ref.material_revision_id} className="rounded-lg border p-3"><legend className="px-1 text-sm">{materials.find(item => item.id === ref.material_revision_id)?.title || `素材版本 ${ref.material_revision_id}`} · 用途分类</legend><div className="flex flex-wrap gap-3">{categories.map(([key, label]) => <label key={key} className="flex items-center gap-1 text-xs"><input type="checkbox" checked={(ref.categories || []).includes(key)} onChange={event => onChange(value.map(item => item.material_revision_id === ref.material_revision_id ? { ...item, categories: event.target.checked ? [...(item.categories || []), key] : (item.categories || []).filter(category => category !== key) } : item))} />{label}</label>)}</div></fieldset>)}{value.length > 0 && <p className="text-xs text-slate-500">分类可多选、更正；分类不会授予真实性或使用权限。</p>}</div>;
}

export const emptyProductCosts = (): ProductCosts => ({ currency: null, basis: null, order_count: null, purchase: null, packaging: null, shipping: null, platform: null, promotion: null, production: null, returns_service: null });
export function ProductCostFields({ value, onChange, estimate }: { value: ProductCosts; onChange: (next: ProductCosts) => void; estimate?: string | null }) {
  return <details className="rounded-lg border p-3"><summary className="cursor-pointer font-medium">内部经营估算（可选）</summary><p className="my-3 text-xs text-slate-500">仅内部保存，不进入创作输入或公开导出。未知项留空；明确没有费用才填0。所有费用使用同一币种与口径。</p><div className="grid gap-3 md:grid-cols-2">
    <Field label="费用币种"><input maxLength={3} className={inputClass} placeholder="CNY" value={value.currency || ""} onChange={event => onChange({ ...value, currency: event.target.value.toUpperCase() || null })} /></Field>
    <Field label="费用口径"><select className={inputClass} value={value.basis || ""} onChange={event => onChange({ ...value, basis: (event.target.value || null) as ProductCosts["basis"] })}><option value="">待确认</option><option value="per_order">单笔订单</option><option value="total">全部订单总额</option></select></Field>
    {value.basis === "total" && <Field label="总额对应订单数"><input type="number" min={1} step={1} className={inputClass} value={value.order_count ?? ""} onChange={event => onChange({ ...value, order_count: event.target.value ? Number(event.target.value) : null })} /></Field>}
    {([["purchase", "进货"], ["packaging", "包装"], ["shipping", "运费"], ["platform", "平台费用"], ["promotion", "推广"], ["production", "制作分摊"], ["returns_service", "退货售后预估"]] as const).map(([key, label]) => <Field key={key} label={label}><input type="number" min={0} step="any" className={inputClass} placeholder="未知" value={value[key] ?? ""} onChange={event => onChange({ ...value, [key]: event.target.value || null })} /></Field>)}
  </div>{estimate !== undefined && <p className="mt-3 text-sm">{estimate === null ? "估算贡献待确认：需补齐同币种售价、全部费用及订单口径。" : `估算贡献：${estimate} ${value.currency || ""}（${value.basis === "total" ? "总额" : "单笔"}，按已保存售价和费用估算，不是净利润）`}</p>}</details>;
}

export function ProductOfferFields({ value, onChange, sources }: { value: ProductOffer | null; onChange: (next: ProductOffer | null) => void; sources: Reference[] }) {
  return <details className="rounded-lg border p-3"><summary className="cursor-pointer font-medium">价格与服务（可选）</summary><label className="my-3 flex gap-2 text-sm"><input type="checkbox" checked={value !== null} onChange={event => onChange(event.target.checked ? { text: "", checked_at: null, valid_until: null, currency: null, original_price: null, sale_price: null, source_id: null, conditions: null, timezone: null } : null)} />本次需要价格或优惠展示</label>{value && <div className="grid gap-3 md:grid-cols-2">
    {([["text", "优惠说明"], ["currency", "币种（如 CNY）"], ["original_price", "原价（未知留空）"], ["sale_price", "售价"], ["conditions", "适用条件／已核实服务"], ["checked_at", "核对时间（ISO 8601，含时区）"], ["valid_until", "截止时间（ISO 8601，未知留空）"], ["timezone", "截止时区（如 Asia/Taipei）"]] as const).map(([key, label]) => <Field key={key} label={label}><input data-ai-field={`offer.${key}`} className={inputClass} value={value[key] || ""} onChange={event => onChange({ ...value, [key]: key === "currency" ? event.target.value.toUpperCase() || null : event.target.value || (key === "text" ? "" : null) })} /></Field>)}
    <Field label="价格资料来源"><select className={inputClass} value={value.source_id || ""} onChange={event => onChange({ ...value, source_id: event.target.value ? Number(event.target.value) : null })}><option value="">选择已附资料</option>{sources.map(source => <option key={source.id} value={source.id}>{source.title}</option>)}</select></Field>
    <p className="text-xs text-slate-500 md:col-span-2">仅根据资料填写款式、规格、价格和服务；缺少价格证据时不生成价格动效。</p>
  </div>}</details>;
}
