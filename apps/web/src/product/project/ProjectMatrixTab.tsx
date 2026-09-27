import { Link } from "react-router-dom";
import { Button, EmptyState, StatusBadge } from "../../components/ui";
import type { Persona, Project, Unit } from "../PersistentProjectPages";

const MODALITY_NAMES = { text: "文字", graphic: "图文", video: "视频" };

export function ProjectMatrixTab({ project, personas, onAddPersona, onAddUnit, onEditUnit, onDeleteUnit }: {
  project: Project; personas: Persona[]; onAddPersona: () => void; onAddUnit: () => void;
  onEditUnit: (unit: Unit) => void; onDeleteUnit: (unit: Unit) => void;
}) {
  const active = project.units.filter((unit) => unit.status !== "archived");
  const archived = project.units.filter((unit) => unit.status === "archived");
  const writable = project.status !== "archived";
  return <section className="rounded-xl border border-slate-200 bg-white p-5">
    <div className="mb-4 flex items-center justify-between"><h2 className="font-semibold">内容矩阵</h2>{writable && <div className="flex gap-2"><Button variant="secondary" onClick={onAddPersona}>新增身份</Button><Button onClick={onAddUnit}>新增内容单元</Button></div>}</div>
    {active.length ? <div className="space-y-3">{active.map((unit) => <article key={unit.id} className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-200 p-4"><div><div className="flex gap-2"><h3 className="font-semibold">{unit.title}</h3><StatusBadge status={unit.status} /></div><p className="mt-1 text-xs text-slate-500">{personas.find((persona) => persona.id === unit.persona_id)?.name || `身份 #${unit.persona_id}`} · {unit.account_id ? `账号 #${unit.account_id}` : "无账号"} · {unit.series_id ? `栏目 #${unit.series_id}` : "无栏目"} · {MODALITY_NAMES[unit.modality]} · {unit.channel_id || "未选择渠道"}</p><p className="mt-1 text-xs text-slate-500">身份：{unit.identity_snapshot_id ? `快照 #${unit.identity_snapshot_id}` : "Legacy / 未冻结身份"} · 固定工作流：{unit.pinned_workflow_id ? `#${unit.pinned_workflow_id}` : "未设置"}</p></div><div className="flex gap-2"><Link to={`/projects/${project.id}/units/${unit.id}/production`} className="rounded-md bg-indigo-600 px-3 py-2 text-xs text-white">进入生产</Link>{writable && <><Button size="sm" variant="secondary" onClick={() => onEditUnit(unit)}>编辑</Button><Button size="sm" variant="danger" onClick={() => onDeleteUnit(unit)}>删除</Button></>}</div></article>)}</div> : <EmptyState title="还没有内容单元" hint={writable ? "先创建身份，再添加文字、图文或视频单元。" : "此项目已归档，仅可查看历史。"} />}
    {archived.length > 0 && <details className="mt-5 border-t pt-4"><summary className="cursor-pointer text-sm text-slate-600">已归档单元（{archived.length}）</summary><div className="mt-3 space-y-2">{archived.map((unit) => <div key={unit.id} className="flex items-center justify-between rounded-lg bg-slate-50 p-3 text-sm"><span>{unit.title} · #{unit.id} · {MODALITY_NAMES[unit.modality]}</span><Link className="text-indigo-600" to={`/projects/${project.id}/units/${unit.id}/production`}>查看历史</Link></div>)}</div></details>}
  </section>;
}
