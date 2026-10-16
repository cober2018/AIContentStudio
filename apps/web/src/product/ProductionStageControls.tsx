import { useEffect, useState } from "react";
import { currentUser } from "../api";
import { Button, Field, inputClass } from "../components/ui";
import { TypedStageField } from "./StageContractControls";
import { capabilityApi, type CapabilityArtifact, type CapabilityRevision } from "./capabilityMemoryTypes";

export type ProductionMethod = {
  id: string; source_kind: "studio_builtin" | "capability_memory" | "installed_agent_skill";
  enabled: boolean; parameters: Record<string, unknown>;
  skill_ref?: string; artifact_id?: number; revision_id?: number; skill_id?: string; version?: string;
};
export type ProductionStages = Record<string, { enabled: boolean; methods: ProductionMethod[] }>;
export type ProductionCatalog = { production_stages?: { id: string; title: string; order: number; modalities: string[] }[]; skills: any[] };

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
  return <div className="space-y-3" aria-label="十阶段方法配置">
    <p className="text-xs text-slate-500">配置来源：{origin}。未设置的阶段沿用原流程；已设置且无启用方法时，依据角色、知识与任务生成。关闭保留选择，技术输出合同继续生效。</p>
    <Button size="sm" variant="secondary" disabled={disabled || !catalog?.production_stages?.length} onClick={() => onChange(Object.fromEntries((catalog?.production_stages || []).map(stage => [stage.id, { enabled: false, methods: value?.[stage.id]?.methods || [] }])))}>关闭全部阶段方法（保留选择）</Button>
    {(catalog?.production_stages || []).map(stage => {
      const selection = value?.[stage.id];
      const items = selection?.methods || [];
      const updateMethod = (index: number, patch: Partial<ProductionMethod>) => updateStage(stage.id, { methods: items.map((item, at) => at === index ? { ...item, ...patch } : item) });
      return <details key={stage.id} className="rounded-lg border border-slate-200 p-3">
        <summary className="cursor-pointer text-sm font-medium">{stage.order + 1}. {stage.title} · {!selection ? "沿用原流程" : !selection.enabled ? "方法已关闭" : `${items.filter(item => item.enabled).length} 项启用`}</summary>
        <div className="mt-3 space-y-3">
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" disabled={disabled} checked={selection?.enabled ?? false} onChange={event => updateStage(stage.id, { enabled: event.target.checked })} />启用本阶段所选方法</label>
          {!selection && <Button size="sm" variant="secondary" disabled={disabled} onClick={() => updateStage(stage.id, { enabled: false })}>明确关闭本阶段方法</Button>}
          {selection && <Button size="sm" variant="ghost" disabled={disabled} onClick={() => { const next = { ...value }; delete next[stage.id]; onChange(next); }}>恢复原流程</Button>}
          {items.map((item, index) => {
            const builtin = catalog?.skills.find(skill => skill.ref === item.skill_ref);
            const saved = methods.find(method => method.id === item.artifact_id && method.current_revision.id === item.revision_id);
            const revision = saved?.current_revision || exactRevisions[revisionKey(item.artifact_id, item.revision_id)];
            const revisionError = revisionErrors[revisionKey(item.artifact_id, item.revision_id)];
            const schema = builtin?.parameter_schema || revision?.args_schema;
            return <div key={item.id} className="space-y-2 rounded bg-slate-50 p-3">
              <div className="flex flex-wrap items-center gap-2"><label className="flex flex-1 gap-2 text-xs"><input type="checkbox" disabled={disabled} checked={item.enabled} onChange={event => updateMethod(index, { enabled: event.target.checked })} />{index + 1}. {builtin?.purpose || saved?.name || item.skill_ref || `方法 #${item.artifact_id} / 修订 #${item.revision_id}`}</label><Button size="sm" variant="ghost" disabled={disabled || index === 0} onClick={() => { const next = [...items]; [next[index - 1], next[index]] = [next[index], next[index - 1]]; updateStage(stage.id, { methods: next }); }}>上移</Button><Button size="sm" variant="ghost" disabled={disabled} onClick={() => updateStage(stage.id, { methods: items.filter((_, at) => at !== index) })}>移除</Button></div>
              <p className="text-xs text-slate-500">{item.source_kind} · {item.skill_ref || `Artifact #${item.artifact_id} · Revision #${item.revision_id}`} · {selection?.enabled && item.enabled ? "本次将冻结并载入" : "不注入指令"}</p>
              {schema && <TypedStageField label="方法参数" schema={schema} value={item.parameters} disabled={disabled} onChange={parameters => updateMethod(index, { parameters: parameters as Record<string, unknown> })} />}
              {item.source_kind === "capability_memory" && !saved && <p className="text-xs text-slate-500">{revisionError || (revision ? "正在使用所选历史修订的参数合同。" : "读取所选历史修订的参数合同…")}{revisionError && <Button size="sm" variant="ghost" onClick={() => setRetry(count => count + 1)}>重试读取</Button>}</p>}
              {!schema && Object.keys(item.parameters).length > 0 && <p className="break-all text-xs">固定参数：{JSON.stringify(item.parameters)}</p>}
            </div>;
          })}
          <Field label="添加方法（按当前顺序冻结版本）"><select className={inputClass} value="" disabled={disabled || items.length >= 12} onChange={event => {
            const ref = event.target.value;
            if (!ref) return;
            const saved = ref.startsWith("memory:") ? methods.find(item => item.id === Number(ref.slice(7))) : null;
            const method: ProductionMethod = { id: `method-${crypto.randomUUID()}`, enabled: true, parameters: {}, ...(saved ? { source_kind: "capability_memory", artifact_id: saved.id, revision_id: saved.current_revision.id } : { source_kind: "studio_builtin", skill_ref: ref }) };
            updateStage(stage.id, { methods: [...items, method] });
          }}><option value="">选择明确的方法，不自动添加</option><optgroup label="内置方法（执行时校验阶段兼容）">{catalog?.skills.filter(item => item.kind === "skill").map(item => <option key={item.ref} value={item.ref}>{item.ref} · {item.purpose}</option>)}</optgroup><optgroup label="已保存方法的精确修订">{methods.filter(item => ["saved", "pinned"].includes(item.status) && ["prompt_skill", "recipe"].includes(item.kind)).map(item => <option key={item.id} value={`memory:${item.id}`}>{item.name} · Revision #{item.current_revision.id}</option>)}</optgroup></select></Field>
        </div>
      </details>;
    })}
    <p className="text-xs text-slate-500">外部已安装 Skill 仅是库存；没有精确源码适配时不可选择为可执行方法。</p>
  </div>;
}
