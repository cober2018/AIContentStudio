import { useQuery } from "@tanstack/react-query";
import { Suspense, lazy, useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useShotSlots } from "./shotSlots";
import { api, currentUser } from "../api";
import { Button } from "../components/ui";
import { MODALITY_NAMES, pretty } from "./useProductionWorkflow";
import type { useProductionWorkflow } from "./useProductionWorkflow";
// A piece's material searches live in the library; this keeps them reachable from the piece itself.
function MaterialSearchEntry({ projectId, unitId }: { projectId: number; unitId: number }) {
  const runs = useQuery({ queryKey: ["material-match-runs", currentUser(), "unit-count", unitId], retry: false,
    queryFn: () => api.get<{ items: unknown[] }>(`/material-match-runs?project_id=${projectId}&unit_id=${unitId}&limit=100`) });
  return <Link to={`/materials?tab=match&project=${projectId}&unit=${unitId}`} className="inline-flex items-center rounded-full border border-ink-200 bg-surface px-3 py-1.5 text-[13px] text-ink-800 hover:border-ink-400">找素材{runs.data ? ` · ${runs.data.items.length}` : ""}</Link>;
}

const ShotSlotsBoard = lazy(() => import("./ShotSlotsBoard"));

// Material is gathered while producing, shot by shot, so the slots sit on the piece's own page.
function ShotSlotsSection({ projectId, unitId }: { projectId: number; unitId: number }) {
  const [params] = useSearchParams();
  const [open, setOpen] = useState(params.get("panel") === "shots");
  useEffect(() => { if (params.get("panel") === "shots") setOpen(true); }, [params]);
  const slots = useShotSlots(projectId, unitId);
  const counts = slots.data?.counts;
  return <section id="shot-slots" className="mb-6 scroll-mt-4 rounded-[14px] border border-ink-200/90 bg-surface px-5 py-3.5">
    <button type="button" className="flex w-full items-center gap-2 text-left text-[13.5px] text-ink-800" onClick={() => setOpen(!open)}>
      <span aria-hidden className={`text-ink-400 transition-transform ${open ? "rotate-90" : ""}`}>›</span>镜头素材
      {slots.data && slots.data.shots.length > 0 && counts && <span className="ml-auto text-[12.5px] text-ink-500">已选 {counts.chosen}/{slots.data.shots.length} · 有候选 {counts.candidates} · 缺 {counts.missing}</span>}
    </button>
    {open && <div className="mt-3"><Suspense fallback={null}><ShotSlotsBoard projectId={projectId} unitId={unitId} /></Suspense></div>}
  </section>;
}

export function ProductionContextHeader({ workflow, productContext }: { workflow: ReturnType<typeof useProductionWorkflow>; productContext?: Record<string, unknown> | null }) {
  const { unit, persona, brandName, accountName, seriesName, snapshot, design, run, assets, assetsOpen, setAssetsOpen } = workflow;
  if (!workflow.project || !workflow.unit) return null;
  if (!unit) return null;
  if (unit.production_domain === "product") return <div className="my-5 flex flex-wrap items-start justify-between gap-4"><div><p className="text-xs font-semibold text-indigo-600">商品视频 · 独立制作配置</p><h1 className="mt-3 text-[34px] leading-[1.1] text-ink-900 sm:text-[40px]">{unit.title}</h1><p className="mt-2 text-sm text-slate-500">{typeof productContext?.name === "string" ? productContext.name : "商品资料待补充"}{typeof productContext?.variant === "string" && productContext.variant ? ` · ${productContext.variant}` : ""} · {unit.channel_id || "交付时再选渠道"}</p><p className="mt-1 text-xs text-slate-500">{!design && run ? `历史 Run #${run.id} · 工作流 #${run.workflow_id}` : `当前商品工作流 #${unit.pinned_workflow_id || "未设置"}`}{!design && run?.identity_snapshot_id ? " · 此历史运行保留原身份快照" : ""}</p></div><div className="flex flex-wrap items-center gap-2"><MaterialSearchEntry projectId={unit.project_id} unitId={unit.id} /><Button variant="secondary" onClick={() => setAssetsOpen(!assetsOpen)}>项目共享素材 · {assets.length}</Button></div></div>;
  const chain = [brandName, persona?.name || `角色 #${unit.persona_id}`, accountName, seriesName].filter(Boolean);
  return <><div className="mb-6 mt-5 flex flex-wrap items-end justify-between gap-x-8 gap-y-4"><div className="min-w-0"><p className="eyebrow">{MODALITY_NAMES[unit.modality] || "生产工作台"}</p><h1 className="mt-3 break-words text-[30px] leading-[1.15] text-ink-900 sm:text-[36px]">{unit.title}</h1><div className="mt-3 flex flex-wrap items-center gap-x-2 gap-y-1 text-[13.5px] text-ink-600">{chain.map((name, index) => <span key={`${name}-${index}`} className="flex items-center gap-2">{index > 0 && <span aria-hidden className="text-ink-300">/</span>}{name}</span>)}<span aria-hidden className="text-ink-300">·</span><span>{unit.channel_id || "未选渠道"}</span></div></div><div className="flex flex-wrap items-center gap-2"><MaterialSearchEntry projectId={unit.project_id} unitId={unit.id} /><Button variant="secondary" size="sm" onClick={() => setAssetsOpen(!assetsOpen)}>项目共享素材 · {assets.length}</Button></div></div>
    {unit.modality === "video" && <ShotSlotsSection projectId={unit.project_id} unitId={unit.id} />}
    <details className="group mb-6 rounded-[14px] border border-ink-200/90 bg-surface px-5 py-3.5 text-sm"><summary className="flex cursor-pointer list-none items-center gap-2 text-[13.5px] text-ink-700"><span aria-hidden className="text-ink-400 transition-transform group-open:rotate-90">›</span>身份快照与运行记录<span className="ml-auto text-[12.5px] text-ink-500">{snapshot ? `快照 #${snapshot.id}` : "未冻结身份"} · 工作流 #{!design && run ? run.workflow_id : unit.pinned_workflow_id || "未设置"}</span></summary>{!design && run && snapshot && <p className="mt-3 text-xs text-slate-600">历史运行 #{run.id} 固定的身份：品牌 #{snapshot.brand_id ?? "无"} → 角色 #{snapshot.persona_id} → 账号 #{snapshot.account_id ?? "无"} → 栏目 #{snapshot.series_id ?? "无"}；标题下方是当前名称，不代表运行时名称。</p>}{snapshot ? <div className="mt-3 space-y-2 text-xs text-slate-600"><p>快照 #{snapshot.id} · 校验和 {snapshot.checksum}</p><p>修订：品牌 {snapshot.brand_revision_id ?? "无"} / 角色 {snapshot.persona_revision_id ?? "无"} / 账号 {snapshot.account_revision_id ?? "无"} / 栏目 {snapshot.series_revision_id ?? "无"} · 品牌语气 {snapshot.brand_voice_version_id ?? "无"}</p><pre className="max-h-56 overflow-auto whitespace-pre-wrap rounded-xl bg-ink-900 p-4 font-mono text-[11.5px] text-ink-100">{pretty(snapshot.effective_profile)}</pre><p>字段来源：{pretty(snapshot.field_origins)}</p><p>身份当前修订变化不会回写此快照；如需更新，请在项目矩阵显式重绑。</p></div> : <p className="mt-2 text-xs text-amber-700">Legacy / 未冻结身份。不能宣称当前身份曾用于历史运行；如需新生产，请在项目矩阵显式重绑。</p>}</details></>;
}
