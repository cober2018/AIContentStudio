import { useEffect, useState } from "react";
import { api, ApiError } from "../api";
import { ErrorBanner, Spinner } from "../components/ui";

type Resource = { ref: string; key: string; version: string; kind: string; source_kind: string;
  purpose?: string; provenance?: string; license?: string; compatible_stage_schemas?: string[];
  output_schemas?: string[]; tunable_fields?: string[];
  execution_support?: { status: string; reason?: string }; config?: Record<string, unknown> };
type Inventory = { skills: Resource[]; style_presets: Resource[]; quality_profiles: Resource[] };
const groups = [["skills", "产品内置 Skill", "怎么做"], ["style_presets", "风格预设", "如何表达"],
  ["quality_profiles", "质量门禁", "如何核对"]] as const;

export default function StudioCreativeInventory() {
  const [data, setData] = useState<Inventory | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    let alive = true;
    api.get<Inventory>("/content-identities/creative-catalog").then(value => {
      if (!groups.every(([key]) => Array.isArray(value[key]))) throw new Error("资源清单不完整。");
      if (alive) setData(value);
    }).catch(cause => { if (alive) setError(cause instanceof ApiError ? cause.message : "资源清单暂不可读。"); });
    return () => { alive = false; };
  }, []);
  return <section aria-label="Studio 内置创作资源" className="space-y-4 rounded-xl border border-slate-200 bg-white p-5">
    <div><h3 className="font-semibold">Studio 内置创作资源</h3><p className="mt-1 text-sm text-slate-500">只读、版本化产品资源。与角色保存的方法、外部安装 Skill 分开；读取不会生成内容或探测 Provider。</p></div>
    {error && <ErrorBanner message={error} />}{!data && !error && <Spinner label="读取内置资源…" />}
    {data && groups.map(([key, label, hint]) => <details key={key} className="rounded-lg border border-slate-200">
      <summary className="cursor-pointer px-4 py-3 text-sm font-medium">{label} · {data[key].length} 项 <span className="font-normal text-slate-500">{hint}</span></summary>
      <div className="grid gap-3 border-t border-slate-100 p-4 md:grid-cols-2">{data[key].map(item => <article key={item.ref} className="min-w-0 rounded-lg bg-slate-50 p-3 text-xs">
        <p className="break-all font-medium text-slate-800">{item.ref}</p><p className="mt-1 text-slate-600">{item.purpose || hint}</p>
        <p className="mt-2 text-slate-500">来源：{item.source_kind} · 版本：{item.version}</p>
        {item.execution_support && <p className="mt-1 text-amber-800">{item.execution_support.status === "connected_not_probed" ? "已接执行合同，尚非质量验收" : `部分接入 · ${item.execution_support.reason || "需要执行入口"}`}</p>}
        {!!item.compatible_stage_schemas?.length && <p className="mt-1 break-all text-slate-500">Stage：{item.compatible_stage_schemas.join(" / ")}</p>}
        {!!item.output_schemas?.length && <p className="mt-1 break-all text-slate-500">输出：{item.output_schemas.join(" / ")}</p>}
        {!!item.tunable_fields?.length && <p className="mt-1 text-slate-500">可调：{item.tunable_fields.join("、")}</p>}
        {item.provenance && <p className="mt-1 break-all text-slate-500">来源记录：{item.provenance} · License：{item.license || "未声明"}</p>}
      </article>)}</div>
    </details>)}
  </section>;
}
