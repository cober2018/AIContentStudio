import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { api, ApiError } from "../api";
import { Button, ErrorBanner, Field, Spinner, inputClass } from "../components/ui";
import FormAssistancePanel from "./FormAssistancePanel";
import type { AssistanceField, AssistanceValue } from "./formAssistanceTypes";
import type { ProductionMethod, ProductionStages } from "./ProductionStageControls";
import type { Brief } from "./project/types";

type GoalDraft = { objective: string; primary_audience: string; core_message: string; buyer_situation: string; main_objection: string; cta: string };
const labels: Record<keyof GoalDraft, string> = { objective: "本条创作目标", primary_audience: "面向谁", core_message: "核心购买理由 / 表达", buyer_situation: "使用情境", main_objection: "主要顾虑", cta: "行动引导" };
const goalFieldLabels: Record<string, string> = { objective: "本条创作目标", primary_audience: "面向谁", core_message: "核心购买理由 / 表达", cta: "行动引导" };
function fromBrief(value: Brief | null): GoalDraft {
  return { objective: value?.objective || "", primary_audience: value?.primary_audience || "", core_message: value?.core_message || "", buyer_situation: value?.product_context?.buyer_situation || "", main_objection: value?.product_context?.main_objection || "", cta: value?.cta || "" };
}
type ProductMethod = { ref: string; key: string; version: string; name: string; purpose: string; applicable_fields: string[]; package_hash: string; selected: boolean; enabled: boolean | null };
type ProductMethods = { unit_id: number; script_stage: { configured: boolean; enabled: boolean | null }; effective_stages: ProductionStages; methods: ProductMethod[] };
const METHOD_REFS = ["studio.product.audience-need@1", "studio.product.purchase-reason@1"];

export default function GuidedProductionGoal({ projectId, unitId, isProduct = false, active, readOnly, onSaved, onDirty }: { projectId: number; unitId?: number; isProduct?: boolean; active: boolean; readOnly: boolean; onSaved: () => void; onDirty: (dirty: boolean) => void }) {
  const base = `/content-projects/${projectId}/brief`;
  const productUnit = Boolean(unitId && isProduct);
  const [brief, setBrief] = useState<Brief | null>(null);
  const [draft, setDraft] = useState<GoalDraft>(() => fromBrief(null));
  const [dirty, setDirty] = useState(false);
  const [loading, setLoading] = useState(true);
  const [loaded, setLoaded] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [productMethods, setProductMethods] = useState<ProductMethods | null>(null);
  // 商品方法组状态：未配置不自动启用；显式启用后两项默认开；切换不生成、不保存
  const [methodGroupOn, setMethodGroupOn] = useState(false);
  const [methodSwitches, setMethodSwitches] = useState<Record<string, boolean>>({});
  const [methodBusy, setMethodBusy] = useState(false);
  const [methodError, setMethodError] = useState("");
  const [methodNotice, setMethodNotice] = useState("");
  const [focusField, setFocusField] = useState("");
  const lock = useRef(false);
  async function reload() {
    if (lock.current) return;
    lock.current = true; setLoading(true); setError("");
    try { const value = await api.get<Brief | null>(base); setBrief(value); setDraft(fromBrief(value)); setDirty(false); setLoaded(true); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "任务书读取失败，草稿保留"); }
    finally { lock.current = false; setLoading(false); }
  }
  useEffect(() => { void reload(); }, [base]);
  useEffect(() => { onDirty(dirty); }, [dirty, onDirty]);
  const methodsQuery = productUnit ? `/form-assistance/product-methods?project_id=${projectId}&unit_id=${unitId}` : null;
  useEffect(() => {
    if (!methodsQuery) { setProductMethods(null); setMethodGroupOn(false); return; }
    let activeRequest = true;
    api.get<ProductMethods>(methodsQuery).then(value => {
      if (!activeRequest) return;
      setProductMethods(value);
      // 组开关＝任一方法实际生效（R3：已配置全关保存后重新载入显示一致）
      setMethodGroupOn(value.methods.some(method => method.selected && Boolean(method.enabled)));
      setMethodSwitches(Object.fromEntries(value.methods.map(method => [method.ref, method.selected ? Boolean(method.enabled) : true])));
      setMethodError(""); setMethodNotice("");
    }).catch(() => { if (activeRequest) setMethodError("商品方法状态暂未读取，仍可使用普通AI辅助。"); });
    return () => { activeRequest = false; };
  }, [methodsQuery]);
  function update(key: keyof GoalDraft, value: AssistanceValue) { setDraft(previous => ({ ...previous, [key]: String(value ?? "") })); setDirty(true); setNotice(""); }
  async function save() {
    if (!loaded || readOnly || lock.current || !draft.objective.trim()) return;
    lock.current = true; setBusy(true); setError("");
    try {
      const saved = await api.post<Brief>(`${base}/revisions`, {
        expected_revision: brief?.revision_no || 0,
        objective: draft.objective.trim(), primary_audience: draft.primary_audience || null,
        core_message: draft.core_message || null, cta: draft.cta || null,
        angle: brief?.angle ?? null, required_evidence: brief?.required_evidence ?? [],
        content_constraints: brief?.content_constraints ?? [], identity_scope: brief?.identity_scope ?? [],
        modality_scope: brief?.modality_scope ?? [], channel_scope: brief?.channel_scope ?? [],
        references: brief?.references ?? [],
        product_context: brief?.product_context ? { ...brief.product_context, buyer_situation: draft.buyer_situation, main_objection: draft.main_objection } : null,
      });
      setBrief(saved); setDraft(fromBrief(saved)); setDirty(false);
      setNotice("目标与受众已保存；商品规格、证据和已有引用保留。上游任务书变化后，已有方案与成片需核对。");
      onSaved();
    } catch (cause) { setError(cause instanceof ApiError && cause.status === 409 ? "任务书已有新版本，当前草稿保留。请核对后重新载入，再保存。" : cause instanceof Error ? cause.message : "保存失败，草稿保留"); }
    finally { lock.current = false; setBusy(false); }
  }
  // 已配置＝作品级（含 brief/SKU 合并后的有效 stages）存在任一方法条目；用于组开关本地关闭时仍显式传 disabled
  const anyMethodSelected = (productMethods?.methods || []).some(method => method.selected);
  // 商品方法组激活（或已配置但本次关闭）时的合并显式 stages：script stage 内 upsert 两项方法、保留其他方法，其余 stage 原样。
  // 组关闭但已配置时两项显式 disabled：否则请求不带 stages，已存方法会经 project_snapshot.production_methods 背景回退执行。
  const mergedStages = useMemo<ProductionStages | null>(() => {
    if (!productUnit || !productMethods || !(methodGroupOn || anyMethodSelected)) return null;
    const stages: ProductionStages = JSON.parse(JSON.stringify(productMethods.effective_stages || {}));
    const script = stages.script || { enabled: true, methods: [] as ProductionMethod[] };
    const existing = script.methods || [];
    const kept = existing.filter(method => !METHOD_REFS.includes(String(method.skill_ref)));
    const entries: ProductionMethod[] = METHOD_REFS.map(ref => {
      const previous = existing.find(method => method.skill_ref === ref);
      return { ...(previous || {}), id: String(previous?.id || ref.split("@")[0]), source_kind: "studio_builtin" as const, skill_ref: ref, enabled: methodGroupOn && methodSwitches[ref] !== false, parameters: previous?.parameters || {} };
    });
    stages.script = { ...script, enabled: script.enabled !== false, methods: [...kept, ...entries] };
    return stages;
  }, [productUnit, methodGroupOn, anyMethodSelected, productMethods, methodSwitches]);
  // R3：方法选择脏状态——进入离开提醒，避免静默丢弃
  const savedGroupOn = (productMethods?.methods || []).some(method => method.selected && Boolean(method.enabled));
  const savedSwitches = Object.fromEntries((productMethods?.methods || []).map(method => [method.ref, method.selected ? Boolean(method.enabled) : true]));
  const methodDirty = mergedStages != null && (methodGroupOn !== savedGroupOn
    || METHOD_REFS.some(ref => Boolean(methodSwitches[ref]) !== Boolean(savedSwitches[ref])));
  useEffect(() => {
    if (!dirty && !methodDirty) return;
    const warn = (event: BeforeUnloadEvent) => { event.preventDefault(); event.returnValue = ""; };
    const guard = (event: MouseEvent) => {
      if (event.defaultPrevented || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      const anchor = (event.target as Element | null)?.closest?.("a[href]") as HTMLAnchorElement | null;
      if (!anchor || anchor.target === "_blank") return;
      const target = new URL(anchor.href);
      if (target.origin === window.location.origin && target.pathname === window.location.pathname && target.search === window.location.search) return;
      if (!window.confirm("离开会丢弃未保存的目标与受众草稿或商品方法选择，继续？")) { event.preventDefault(); event.stopPropagation(); }
    };
    window.addEventListener("beforeunload", warn); document.addEventListener("click", guard, true);
    return () => { window.removeEventListener("beforeunload", warn); document.removeEventListener("click", guard, true); };
  }, [dirty, methodDirty]);
  async function saveMethodSwitches() {
    if (!productUnit || !unitId || !mergedStages || methodBusy) return;
    setMethodBusy(true); setMethodError(""); setMethodNotice("");
    try {
      // 先取得版本，再读含继承的方法；两次读取间发生作品写入时，旧版本使 PUT 返回 409。
      // 单用作品覆盖层会丢掉任务书继承的方法，保存时必须在有效配置上合并。
      const current = await api.get<{ revision: number; settings: Record<string, unknown> }>(`/content-projects/${projectId}/units/${unitId}/production-profile`);
      const fresh = await api.get<ProductMethods>(methodsQuery!);
      const base: ProductionStages = JSON.parse(JSON.stringify(fresh.effective_stages || {}));
      // R4：仅提交用户实际修改的开关，未修改项保留最新版本状态（含其他入口的更改）。
      // 组开关切换视为对两项的明确整体修改：启用＝两项默认开，关闭＝两项全关。
      const groupToggled = methodGroupOn !== savedGroupOn;
      const modifiedRefs = METHOD_REFS.filter(ref => groupToggled || Boolean(methodSwitches[ref]) !== Boolean(savedSwitches[ref]));
      if (modifiedRefs.length) {
        const script = base.script || { enabled: true, methods: [] as ProductionMethod[] };
        const existing = script.methods || [];
        const entries = modifiedRefs.map(ref => {
          const previous = existing.find(method => method.skill_ref === ref);
          return { ...(previous || {}), id: String(previous?.id || ref.split("@")[0]), source_kind: "studio_builtin" as const, skill_ref: ref, enabled: methodGroupOn && methodSwitches[ref] !== false, parameters: previous?.parameters || {} };
        });
        const kept = existing.filter(method => !modifiedRefs.includes(String(method.skill_ref)));
        base.script = { ...script, enabled: script.enabled !== false, methods: [...kept, ...entries] };
        await api.put(`/content-projects/${projectId}/units/${unitId}/production-profile`, {
          expected_revision: current.revision,
          settings: { ...current.settings, production_stages: base },
        });
      }
      const value = await api.get<ProductMethods>(methodsQuery!);
      setProductMethods(value);
      setMethodGroupOn(value.methods.some(method => method.selected && Boolean(method.enabled)));
      setMethodSwitches(Object.fromEntries(value.methods.map(method => [method.ref, method.selected ? Boolean(method.enabled) : true])));
      setMethodNotice(modifiedRefs.length
        ? "商品方法选择已保存到本作品制作设置；仅写入本次修改的开关，其他入口的阶段与方法配置保留。切换后需重新生成再采用建议。"
        : "没有需要保存的方法修改，已读取最新配置。");
    } catch (cause) { setMethodError(cause instanceof ApiError && cause.status === 409 ? "制作配置已有新版本，请重新保存方法选择。" : cause instanceof Error ? cause.message : "方法选择保存失败"); }
    finally { setMethodBusy(false); }
  }
  if (loading && !loaded) return <div hidden={!active}><Spinner label="读取目标与受众…" /></div>;
  const keys: (keyof GoalDraft)[] = brief?.product_context ? ["objective", "primary_audience", "core_message", "buyer_situation", "main_objection", "cta"] : ["objective", "primary_audience", "core_message", "cta"];
  // 仅商品作品的空 objective / primary_audience 开放补齐建议；非空与其他字段保护不放宽
  const suggestable = (key: keyof GoalDraft) => productUnit && (key === "objective" || key === "primary_audience") && !draft[key].trim();
  const fields: AssistanceField[] = keys.map(key => ({ key, label: labels[key], value: draft[key], protected: (key === "objective" || key === "primary_audience") && !suggestable(key), kind: "text", apply: value => update(key, value) }));
  const product = brief?.product_context;
  const stagesForRequest = mergedStages ?? product?.production_stages ?? undefined;
  const methodArea: ReactNode = productUnit && productMethods ? (
    <details className="rounded-lg border border-indigo-100 bg-indigo-50/40 p-2" data-ai-product-methods>
      <summary className="cursor-pointer text-xs font-medium">商品方法（{methodGroupOn ? `${METHOD_REFS.filter(ref => methodSwitches[ref] !== false).length}/2 启用` : anyMethodSelected ? "已配置·全关" : "未启用"}）</summary>
      <div className="space-y-2 p-2">
        <p className="text-xs text-slate-500">两项自有方法作用于目标与受众字段；补齐和润色共用此选择。启用不自动生成、不自动保存；聚焦字段时适用方法会标注；取消整组后本次请求两项不执行；阶段总开关关闭时方法不执行。</p>
        <label className="flex items-center gap-2 text-xs"><input type="checkbox" checked={methodGroupOn} disabled={methodBusy || readOnly} onChange={event => {
          setMethodGroupOn(event.target.checked);
          if (event.target.checked) setMethodSwitches(previous => Object.fromEntries(Object.keys(previous).map(ref => [ref, true])));
        }} />启用商品方法辅助（显式启用后两项默认开）</label>
        {methodGroupOn && productMethods.methods.map(method => {
          const applies = Boolean(focusField) && method.applicable_fields.includes(focusField);
          return (
          <label key={method.ref} className={`flex items-start gap-2 rounded border p-2 text-xs ${applies ? "border-indigo-300 bg-indigo-50/60 ring-1 ring-indigo-200" : "border-slate-100 bg-white"}`}>
            <input type="checkbox" className="mt-0.5" checked={methodSwitches[method.ref] !== false} disabled={methodBusy || readOnly} onChange={event => setMethodSwitches(previous => ({ ...previous, [method.ref]: event.target.checked }))} />
            <span>{method.name} · v{method.version}{applies && <span className="ml-1 rounded bg-indigo-100 px-1 py-0.5 text-[10px] text-indigo-700">适用当前字段</span>}<span className="block text-slate-500">适用：{method.applicable_fields.map(field => goalFieldLabels[field] || field).join("、")}</span></span>
          </label>
          );
        })}
        <div className="flex items-center gap-2">
          <Button size="sm" disabled={!mergedStages || methodBusy || readOnly} onClick={() => void saveMethodSwitches()}>保存方法选择到本作品</Button>
          {methodDirty && <span className="text-xs text-amber-700">有未保存的方法修改</span>}
          {methodNotice && <span role="status" className="text-xs text-emerald-700">{methodNotice}</span>}
        </div>
        {methodError && <p role="alert" className="text-xs text-rose-700">{methodError}</p>}
      </div>
    </details>
  ) : null;
  return <div hidden={!active}><FormAssistancePanel assistantVisible={active} versionKey={JSON.stringify([brief?.id, product?.source_refs, product?.material_refs])} surface="product_brief" productionStages={stagesForRequest} projectId={projectId} unitId={unitId} fields={fields} sourceRefs={(product?.source_refs || []).map(ref => ({ source_id: ref.source_id, checksum: ref.checksum }))} methodRefs={product?.style_ref ? [product.style_ref] : []} readOnly={readOnly || busy || loading || !loaded} methodArea={methodArea} context={{ category: product?.category || null, style_revision_id: product?.style_ref?.revision_id || null }}>
    <section className="mb-5 space-y-4 rounded-2xl border border-slate-200 bg-white p-5" aria-label="目标与受众编辑">
      <div className="flex items-center justify-between gap-3"><h3 className="font-semibold">目标与受众</h3><span className="text-xs text-slate-500">{dirty ? "有未保存修改" : brief ? `任务书 v${brief.revision_no}` : "尚无任务书"}</span></div>
      <p className="text-xs text-slate-500">保存在项目任务书；同项目作品共享这些资料。单作品的表现方式与声音另存制作设置。</p>
      {error && <ErrorBanner message={error} />}
      <div className="grid gap-4 sm:grid-cols-2">{keys.map(key => <Field key={key} label={labels[key]}><textarea aria-label={labels[key]} data-ai-field={key} className={inputClass} rows={key === "objective" || key === "core_message" ? 3 : 2} value={draft[key]} disabled={readOnly || busy || loading || !loaded} onFocus={() => setFocusField(key)} onChange={event => update(key, event.target.value)} /></Field>)}</div>
      <div className="flex flex-wrap items-center gap-3"><Button disabled={readOnly || busy || loading || !loaded || !dirty || !draft.objective.trim()} onClick={() => void save()}>保存目标与受众</Button><Button variant="secondary" disabled={busy || loading} onClick={() => { if (!dirty || window.confirm("放弃目标与受众的本地草稿并读取已保存任务书？")) void reload(); }}>重新载入</Button><span className="text-xs text-slate-500">切换步骤保留草稿；AI建议须逐项采用并保存。</span></div>
      {notice && <p role="status" className="text-sm text-emerald-700">{notice}</p>}
    </section>
  </FormAssistancePanel></div>;
}
