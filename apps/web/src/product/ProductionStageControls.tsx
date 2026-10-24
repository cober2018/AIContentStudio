import { useEffect, useState } from "react";
import { currentUser } from "../api";
import { Button, Field, inputClass } from "../components/ui";
import { refName } from "./IdentityProfileView";
import { TypedStageField } from "./StageContractControls";
import { capabilityApi, type CapabilityArtifact, type CapabilityRevision } from "./capabilityMemoryTypes";

export type ProductionMethod = {
  id: string; source_kind: "studio_builtin" | "capability_memory" | "installed_agent_skill";
  enabled: boolean; parameters: Record<string, unknown>;
  skill_ref?: string; artifact_id?: number; revision_id?: number; skill_id?: string; version?: string;
};
export type ProductionStages = Record<string, { enabled: boolean; methods: ProductionMethod[] }>;
export type ProductionCatalog = { production_stages?: { id: string; title: string; order: number; modalities: string[] }[]; skills: any[] };

const ORIGINS: Record<string, string> = { persona: "角色", account: "账号", series: "栏目", brand: "品牌" };

export default function ProductionStageControls({ value, catalog, methods = [], disabled, origin, onChange }: {
  value?: ProductionStages; catalog: ProductionCatalog | null; methods?: CapabilityArtifact[];
  disabled: boolean; origin: string; onChange: (value: ProductionStages) => void;
}) {
  const owner = currentUser();
  const [exactRevisions, setExactRevisions] = useState<Record<string, CapabilityRevision>>({});
  const [revisionErrors, setRevisionErrors] = useState<Record<string, string>>({});
  const [retry, setRetry] = useState(0);
  const selections = JSON.stringify(Object.values(value || {}).flatMap(stage => stage.methods)
    .filter(item => item.source_kind === "capability_memory").map(item => [item.artifact_id, item.revision_id]));
  const inventoryRevisions = JSON.stringify(methods.map(item => [item.id, item.current_revision.id]));
  const revisionKey = (artifactId?: number, revisionId?: number) => `${owner}:${artifactId}:${revisionId}`;
  useEffect(() => {
    let active = true;
    const selected = JSON.parse(selections) as [number, number][];
    const missing = selected.filter(([artifactId, revisionId]) => !methods.some(item => item.id === artifactId && item.current_revision.id === revisionId));
    for (const artifactId of new Set(missing.map(([id]) => id))) {
      const requested = missing.filter(([id]) => id === artifactId);
      void capabilityApi.history(artifactId).then(page => {
        if (!active) return;
        for (const [, revisionId] of requested) {
          const key = revisionKey(artifactId, revisionId);
          const revision = page.items.find(item => item.id === revisionId);
          if (revision) { setExactRevisions(previous => ({ ...previous, [key]: revision })); setRevisionErrors(previous => ({ ...previous, [key]: "" })); }
          else setRevisionErrors(previous => ({ ...previous, [key]: "所选精确修订不可读取；参数与版本已保留。" }));
        }
      }).catch(() => {
        if (active) setRevisionErrors(previous => ({ ...previous, ...Object.fromEntries(requested.map(([, id]) => [revisionKey(artifactId, id), "历史参数合同读取失败；参数与版本已保留。另请检查当前身份权限。"])) }));
      });
    }
    return () => { active = false; };
  }, [selections, inventoryRevisions, owner, retry]);

  function updateStage(key: string, patch: Partial<ProductionStages[string]>) {
    onChange({ ...(value || {}), [key]: { enabled: true, methods: [], ...value?.[key], ...patch } });
  }
  return <div className="space-y-4" aria-label="十阶段方法配置">
    <div className="flex flex-wrap items-start justify-between gap-3">
      <p className="max-w-xl text-[12.5px] leading-relaxed text-ink-500">来源：{ORIGINS[origin] || origin}。没设置的步骤沿用默认流程；设置了但没有启用方法时，按角色、知识与任务生成。关闭会保留所选方法。</p>
      {!disabled && <Button size="sm" variant="ghost" disabled={!catalog?.production_stages?.length} onClick={() => onChange(Object.fromEntries((catalog?.production_stages || []).map(stage => [stage.id, { enabled: false, methods: value?.[stage.id]?.methods || [] }])))}>全部关闭（保留选择）</Button>}
    </div>
    <ol className="divide-y divide-ink-200/80 overflow-hidden rounded-[14px] border border-ink-200/90 bg-surface">
    {(catalog?.production_stages || []).map(stage => {
      const selection = value?.[stage.id];
      const items = selection?.methods || [];
      const updateMethod = (index: number, patch: Partial<ProductionMethod>) => updateStage(stage.id, { methods: items.map((item, at) => at === index ? { ...item, ...patch } : item) });
      const enabledNames = items.filter(item => item.enabled).map(item => catalog?.skills.find(skill => skill.ref === item.skill_ref)?.purpose || methods.find(method => method.id === item.artifact_id)?.name || refName(item.skill_ref) || `方法 #${item.artifact_id}`);
      return <li key={stage.id}><details className="group">
        <summary className="flex cursor-pointer list-none items-start gap-4 px-4 py-3.5 transition-colors hover:bg-ink-50">
          <span className="mt-0.5 w-6 shrink-0 font-serif text-[13px] tabular-nums text-ink-400">{String(stage.order + 1).padStart(2, "0")}</span>
          <span className="min-w-0 flex-1">
            <span className="block text-[14px] font-medium text-ink-900">{stage.title}</span>
            <span className="mt-0.5 block truncate text-[12.5px] text-ink-500">{!selection ? "沿用默认流程" : !selection.enabled ? "已关闭" : enabledNames.length ? enabledNames.join(" · ") : "已启用，未选方法"}</span>
          </span>
          <span className={`mt-1 shrink-0 rounded-pill px-2 py-0.5 text-[11px] ${!selection ? "bg-ink-100 text-ink-500" : !selection.enabled ? "bg-ink-100 text-ink-400" : "bg-accent-50 text-accent-700"}`}>{!selection ? "默认" : !selection.enabled ? "关闭" : `${enabledNames.length} 项`}</span>
          <span aria-hidden className="mt-1 text-ink-400 transition-transform group-open:rotate-90">›</span>
        </summary>
        <div className="space-y-3 border-t border-ink-200/70 bg-ink-50/50 px-4 py-4 pl-14">
          <label className="flex items-center gap-2 text-[13.5px] text-ink-800"><input type="checkbox" className="accent-accent-500" disabled={disabled} checked={selection?.enabled ?? false} onChange={event => updateStage(stage.id, { enabled: event.target.checked })} />启用这一步的所选方法</label>
          {!selection && <Button size="sm" variant="secondary" disabled={disabled} onClick={() => updateStage(stage.id, { enabled: false })}>明确关闭本阶段方法</Button>}
          {selection && <Button size="sm" variant="ghost" disabled={disabled} onClick={() => { const next = { ...value }; delete next[stage.id]; onChange(next); }}>恢复原流程</Button>}
          {items.map((item, index) => {
            const builtin = catalog?.skills.find(skill => skill.ref === item.skill_ref);
            const saved = methods.find(method => method.id === item.artifact_id && method.current_revision.id === item.revision_id);
            const revision = saved?.current_revision || exactRevisions[revisionKey(item.artifact_id, item.revision_id)];
            const revisionError = revisionErrors[revisionKey(item.artifact_id, item.revision_id)];
            const schema = builtin?.parameter_schema || revision?.args_schema;
            return <div key={item.id} className="space-y-2 rounded-xl border border-ink-200/80 bg-surface p-3.5">
              <div className="flex flex-wrap items-center gap-2"><label className="flex flex-1 gap-2 text-[13.5px] text-ink-900"><input type="checkbox" className="accent-accent-500" disabled={disabled} checked={item.enabled} onChange={event => updateMethod(index, { enabled: event.target.checked })} />{index + 1}. {builtin?.purpose || saved?.name || refName(item.skill_ref) || `方法 #${item.artifact_id} / 修订 #${item.revision_id}`}</label><Button size="sm" variant="ghost" disabled={disabled || index === 0} onClick={() => { const next = [...items]; [next[index - 1], next[index]] = [next[index], next[index - 1]]; updateStage(stage.id, { methods: next }); }}>上移</Button><Button size="sm" variant="ghost" disabled={disabled} onClick={() => updateStage(stage.id, { methods: items.filter((_, at) => at !== index) })}>移除</Button></div>
              <p className="pl-6 text-[12px] text-ink-500">{item.source_kind === "studio_builtin" ? `内置方法 · ${refName(item.skill_ref)}` : item.source_kind === "capability_memory" ? `方法库 · 修订 #${item.revision_id}` : "外部 Skill"} · {selection?.enabled && item.enabled ? "运行时载入" : "不载入"}</p>
              {schema && <TypedStageField label="方法参数" schema={schema} value={item.parameters} disabled={disabled} onChange={parameters => updateMethod(index, { parameters: parameters as Record<string, unknown> })} />}
              {item.source_kind === "capability_memory" && !saved && <p className="text-xs text-slate-500">{revisionError || (revision ? "正在使用所选历史修订的参数合同。" : "读取所选历史修订的参数合同…")}{revisionError && <Button size="sm" variant="ghost" onClick={() => setRetry(count => count + 1)}>重试读取</Button>}</p>}
              {!schema && Object.keys(item.parameters).length > 0 && <p className="break-all text-xs">固定参数：{JSON.stringify(item.parameters)}</p>}
            </div>;
          })}
          <Field label="添加方法"><select className={inputClass} value="" disabled={disabled || items.length >= 12} onChange={event => {
            const ref = event.target.value;
            if (!ref) return;
            const saved = ref.startsWith("memory:") ? methods.find(item => item.id === Number(ref.slice(7))) : null;
            const method: ProductionMethod = { id: `method-${crypto.randomUUID()}`, enabled: true, parameters: {}, ...(saved ? { source_kind: "capability_memory", artifact_id: saved.id, revision_id: saved.current_revision.id } : { source_kind: "studio_builtin", skill_ref: ref }) };
            updateStage(stage.id, { methods: [...items, method] });
          }}><option value="">选择要加入的方法</option><optgroup label="内置方法">{catalog?.skills.filter(item => item.kind === "skill").map(item => <option key={item.ref} value={item.ref}>{item.purpose}（{refName(item.ref)}）</option>)}</optgroup><optgroup label="我的方法库">{methods.filter(item => ["saved", "pinned"].includes(item.status) && ["prompt_skill", "recipe"].includes(item.kind)).map(item => <option key={item.id} value={`memory:${item.id}`}>{item.name} · 修订 #{item.current_revision.id}</option>)}</optgroup></select></Field>
        </div>
      </details></li>;
    })}
    </ol>
    <p className="text-[12px] text-ink-500">外部安装的 Skill 只是库存，没有适配前不能选作方法。</p>
  </div>;
}
