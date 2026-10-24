import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { Button, EmptyState, ErrorBanner, Field, Modal, Spinner, StatusBadge, inputClass } from "../components/ui";
import ProjectAssetsDrawer from "./ProjectAssetsDrawer";
import { ContentProjectView, ContentUnitView, listMockProjects, loadMockProjects, Modality, ProjectTab, saveMockProjects, WorkStatus } from "./mockProjects";

const TABS: { key: ProjectTab; label: string }[] = [
  { key: "overview", label: "总览" }, { key: "brief", label: "创作任务书" }, { key: "evidence", label: "来源与证据" },
  { key: "assets", label: "项目素材" }, { key: "matrix", label: "内容矩阵" }, { key: "versions", label: "版本" }, { key: "activity", label: "活动" },
];
const MODALITIES: Record<Modality, string> = { text: "文字", image: "图 / 图片", video: "视频" };
const STATUS_EXPLANATION: Partial<Record<WorkStatus, string>> = {
  blocked: "缺少必需证据、权限或人工决策，当前不能继续交付。",
  stale: "上游内容或数据有变化，需要重新检查。",
  unknown: "结果尚不确定，不能当作成功或失败。",
  ready: "当前内容已满足这一阶段的准备条件。",
  waiting_human: "下一步需要人工确认或处理。",
};

function PageHead({ eyebrow, title, description, action }: { eyebrow: string; title: string; description: string; action?: React.ReactNode }) {
  return <div className="mb-7 flex flex-wrap items-start justify-between gap-4"><div><p className="text-xs font-semibold uppercase tracking-[0.18em] text-indigo-600">{eyebrow}</p><h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-900">{title}</h1><p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500">{description}</p></div>{action}</div>;
}

function StatusLegend() {
  const statuses: WorkStatus[] = ["blocked", "stale", "unknown", "waiting_human", "ready"];
  return <section aria-label="状态说明" className="mb-6 rounded-xl border border-slate-200 bg-white px-5 py-4">
    <h2 className="text-sm font-semibold text-slate-900">状态说明</h2>
    <ul className="mt-3 grid gap-3 text-xs leading-5 text-slate-600 sm:grid-cols-2 xl:grid-cols-3">
      {statuses.map((status) => <li key={status} className="flex items-start gap-2"><StatusBadge status={status} /><span>{STATUS_EXPLANATION[status]}</span></li>)}
    </ul>
  </section>;
}

export function ProjectsPage() {
  const [projects, setProjects] = useState(listMockProjects);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [title, setTitle] = useState("");
  const [creating, setCreating] = useState(false);
  const navigate = useNavigate();

  useEffect(() => { loadMockProjects().then(setProjects).catch(() => setError("项目列表读取失败。" )).finally(() => setLoading(false)); }, []);

  function createProject(event: FormEvent) {
    event.preventDefault();
    const value = title.trim();
    if (!value) return;
    const project: ContentProjectView = {
      id: `project-${crypto.randomUUID()}`, title: value, objective: "", status: "draft", stage: "创作任务书", identities: [],
      brief: { objective: "", audience: "", message: "", angle: "", constraints: [], channels: [] }, evidence: [], assets: [], contentUnits: [], risks: [], versions: [],
      activity: [{ at: "刚刚", text: "创建内容项目" }], updatedAt: new Date().toISOString().slice(0, 10),
    };
    try { saveMockProjects([project, ...projects]); setProjects([project, ...projects]); setCreating(false); navigate(`/projects/${project.id}`); }
    catch { setError("浏览器未允许保存本地演示数据，请检查存储权限。"); }
  }

  return <div className="mx-auto w-full max-w-[1240px] px-5 pb-20 pt-8 sm:px-8 md:pt-12 lg:px-12">
    <PageHead eyebrow="Content Projects" title="内容项目" description="围绕一件事组织身份、证据、图文视频、素材与交付。这里使用本地演示数据。" action={<Button onClick={() => setCreating(true)}>新建项目</Button>} />
    {error && <div className="mb-4"><ErrorBanner message={error} /></div>}
    {loading ? <Spinner label="正在读取项目…" /> : projects.length === 0 ? <EmptyState title="还没有内容项目" hint="新建项目后可添加内容单元。" action={<Button onClick={() => setCreating(true)}>新建项目</Button>} /> :
      <div className="grid gap-4 lg:grid-cols-2">{projects.map((project) => <Link key={project.id} to={`/projects/${project.id}`} className="group rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition hover:border-indigo-300 hover:shadow-md">
        <div className="flex items-start justify-between gap-3"><div><h2 className="text-lg font-semibold text-slate-900 group-hover:text-indigo-700">{project.title}</h2><p className="mt-1 text-xs text-slate-500">{project.stage} · 更新于 {project.updatedAt}</p></div><StatusBadge status={project.status} /></div>
        <p className="mt-4 line-clamp-2 text-sm leading-6 text-slate-600">{project.objective || "等待填写项目目标"}</p>
        <div className="mt-5 flex flex-wrap gap-2 text-xs text-slate-500"><span className="rounded-md bg-slate-50 px-2 py-1">{project.contentUnits.length} 个内容单元</span><span className="rounded-md bg-slate-50 px-2 py-1">{project.identities.length} 个身份</span><span className="rounded-md bg-slate-50 px-2 py-1">{project.assets.length} 份素材</span></div>
        {project.risks.length > 0 && <p className="mt-4 rounded-lg bg-rose-50 px-3 py-2 text-xs text-rose-700">{project.risks.length} 项待处理 · {project.risks[0]}</p>}
      </Link>)}</div>}
    {creating && <Modal title="新建内容项目" onClose={() => setCreating(false)}><form onSubmit={createProject} className="space-y-4"><Field label="项目名称"><input autoFocus className={inputClass} value={title} onChange={(event) => setTitle(event.target.value)} placeholder="例如：新产品发布" required /></Field><p className="text-xs text-slate-500">先建立项目，再在内容矩阵中安排文字、图片和视频。</p><div className="flex justify-end gap-2"><Button variant="secondary" onClick={() => setCreating(false)}>取消</Button><Button type="submit">创建项目</Button></div></form></Modal>}
  </div>;
}

export function ProjectPage() {
  const { projectId } = useParams();
  const [projects, setProjects] = useState(listMockProjects);
  const [loading, setLoading] = useState(true);
  const [searchParams, setSearchParams] = useSearchParams();
  const [assetsOpen, setAssetsOpen] = useState(false);
  const [editing, setEditing] = useState<ContentUnitView | "new" | null>(null);
  const [deleting, setDeleting] = useState<ContentUnitView | null>(null);
  const [error, setError] = useState("");
  const project = projects.find((item) => item.id === projectId);
  const current = searchParams.get("tab");
  const tab = TABS.find((item) => item.key === current)?.key || "overview";

  useEffect(() => { loadMockProjects().then(setProjects).catch(() => setError("项目读取失败。" )).finally(() => setLoading(false)); }, []);

  function updateProject(next: ContentProjectView) {
    const updated = projects.map((item) => item.id === next.id ? next : item);
    try { saveMockProjects(updated); setProjects(updated); setError(""); }
    catch { setError("本地演示数据未能保存，请检查浏览器存储权限。"); }
  }

  if (loading) return <Spinner label="正在读取项目…" />;
  if (!project) return <div className="mx-auto w-full max-w-[1240px] px-5 pb-20 pt-8 sm:px-8 md:pt-12 lg:px-12"><ErrorBanner message={error || "找不到该内容项目。"} /><Link className="mt-4 inline-block text-sm text-indigo-600" to="/projects">返回项目列表</Link></div>;
  const showStatusLegend = [project.status, ...project.contentUnits.map((unit) => unit.status)].some((status) => status === "blocked" || status === "stale" || status === "unknown");

  function saveUnit(input: Omit<ContentUnitView, "id" | "updatedAt">) {
    if (!project) return;
    const now = new Date().toISOString().slice(0, 10);
    const isNew = editing === "new";
    const unit: ContentUnitView = { ...input, id: isNew ? `unit-${crypto.randomUUID()}` : (editing as ContentUnitView).id, updatedAt: now };
    updateProject({ ...project, contentUnits: isNew ? [...project.contentUnits, unit] : project.contentUnits.map((item) => item.id === unit.id ? unit : item), activity: [{ at: "刚刚", text: `${isNew ? "新增" : "编辑"}内容单元：${unit.title}` }, ...project.activity], updatedAt: now });
    setEditing(null);
  }

  function deleteUnit(unit: ContentUnitView) {
    if (!project) return;
    updateProject({ ...project, contentUnits: project.contentUnits.filter((item) => item.id !== unit.id), activity: [{ at: "刚刚", text: `删除内容单元：${unit.title}` }, ...project.activity] });
    setDeleting(null);
  }

  return <div className="mx-auto w-full max-w-[1240px] px-5 pb-20 pt-8 sm:px-8 md:pt-12 lg:px-12">
    <Link to="/projects" className="text-sm text-slate-500 hover:text-indigo-700">← 内容项目</Link>
    <div className="mt-4"><PageHead eyebrow="Content Project" title={project.title} description={project.objective || "请在创作任务书中补充项目目标。"} action={<div className="flex items-center gap-3"><StatusBadge status={project.status} /><Button variant="secondary" onClick={() => setAssetsOpen(true)}>项目共享素材 · {project.assets.length}</Button></div>} /></div>
    {error && <div className="mb-4"><ErrorBanner message={error} /></div>}
    <div role="tablist" aria-label="项目工作区" className="mb-6 flex gap-1 overflow-x-auto border-b border-slate-200">
      {TABS.map((item) => <button key={item.key} type="button" role="tab" aria-selected={tab === item.key} onClick={() => setSearchParams({ tab: item.key })} className={`whitespace-nowrap border-b-2 px-4 py-3 text-sm ${tab === item.key ? "border-indigo-600 font-semibold text-indigo-700" : "border-transparent text-slate-500 hover:text-slate-900"}`}>{item.label}</button>)}
    </div>
    {showStatusLegend && (tab === "overview" || tab === "matrix") && <StatusLegend />}
    {tab === "overview" && <div className="space-y-5"><div className="grid gap-3 sm:grid-cols-4">{[["阶段", project.stage], ["内容单元", String(project.contentUnits.length)], ["身份", String(project.identities.length)], ["项目素材", String(project.assets.length)]].map(([label, value]) => <div key={label} className="rounded-xl border border-slate-200 bg-white p-4"><p className="text-xs text-slate-500">{label}</p><p className="mt-2 text-lg font-semibold">{value}</p></div>)}</div><section className="rounded-xl border border-slate-200 bg-white p-6"><h2 className="font-semibold">项目目标</h2><p className="mt-2 text-sm leading-6 text-slate-600">{project.objective || "待填写"}</p><h3 className="mt-5 text-sm font-medium">参与身份</h3><p className="mt-2 text-sm text-slate-600">{project.identities.map((identity) => identity.name).join("、") || "待选择"}</p></section><section className="rounded-xl border border-slate-200 bg-white p-6"><h2 className="font-semibold">当前风险与下一步</h2>{project.risks.length ? <ul className="mt-3 list-inside list-disc space-y-2 text-sm text-rose-700">{project.risks.map((risk) => <li key={risk}>{risk}</li>)}</ul> : <p className="mt-2 text-sm text-slate-500">目前没有记录到阻断项。</p>}<button className="mt-4 text-sm font-medium text-indigo-700" onClick={() => setSearchParams({ tab: "matrix" })}>打开内容矩阵 →</button></section></div>}
    {tab === "brief" && <div className="rounded-xl border border-slate-200 bg-white p-6"><h2 className="font-semibold">创作任务书 · 项目公共目标</h2><dl className="mt-4 grid gap-5 sm:grid-cols-2">{[["目标", project.brief.objective], ["受众", project.brief.audience], ["核心信息", project.brief.message], ["角度", project.brief.angle], ["目标渠道", project.brief.channels.join("、")], ["约束", project.brief.constraints.join("；")]].map(([label, value]) => <div key={label}><dt className="text-xs text-slate-500">{label}</dt><dd className="mt-1 text-sm text-slate-800">{value || "待填写"}</dd></div>)}</dl><p className="mt-6 text-xs text-slate-500">此切片展示演示任务书；内容单元可以在矩阵中独立安排。</p></div>}
    {tab === "evidence" && <div className="space-y-3">{project.evidence.length ? project.evidence.map((item) => <div key={item.id} className="flex items-center justify-between rounded-xl border border-slate-200 bg-white p-4"><div><p className="text-xs text-slate-500">{item.kind}</p><p className="mt-1 font-medium">{item.title}</p></div><StatusBadge status={item.status} /></div>) : <EmptyState title="还没有来源与证据" hint="后续接入真实证据流；此处仅演示项目结构。" />}</div>}
    {tab === "assets" && <div className="rounded-xl border border-slate-200 bg-white p-6"><h2 className="font-semibold">项目素材</h2><p className="mt-2 text-sm text-slate-500">{project.assets.length} 个素材版本，包含上传、系统引用和生产流程生成。</p><Button className="mt-4" onClick={() => setAssetsOpen(true)}>打开项目共享素材</Button></div>}
    {tab === "matrix" && <section className="rounded-xl border border-slate-200 bg-white p-5"><div className="mb-5 flex items-center justify-between gap-3"><div><h2 className="font-semibold">内容矩阵</h2><p className="mt-1 text-xs text-slate-500">身份 × 内容形态 × 渠道；每个内容单元关联自己的生产流程。</p></div><Button onClick={() => setEditing("new")}>新增内容单元</Button></div>{project.contentUnits.length ? <div className="space-y-3">{project.contentUnits.map((unit) => <article key={unit.id} className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-slate-200 p-4"><div className="min-w-0 flex-1"><div className="flex flex-wrap items-center gap-2"><h3 className="font-semibold text-slate-900">{unit.title}</h3><StatusBadge status={unit.status} /></div><p className="mt-1 text-xs text-slate-500">{project.identities.find((identity) => identity.id === unit.identityId)?.name || unit.identityId} · {MODALITIES[unit.modality]} · {unit.channelId}</p><p className="mt-1 text-xs text-slate-500">生产流程：{unit.workflowName}</p></div><div className="flex flex-wrap gap-2"><Link to={`/projects/${project.id}/units/${unit.id}/production`} className="rounded-md bg-indigo-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-indigo-700">进入生产</Link><Button size="sm" variant="secondary" onClick={() => setEditing(unit)}>编辑</Button><Button size="sm" variant="danger" onClick={() => setDeleting(unit)}>删除</Button></div></article>)}</div> : <EmptyState title="内容矩阵还没有单元" hint="新增第一个文字、图片或视频内容单元。" action={<Button onClick={() => setEditing("new")}>新增内容单元</Button>} />}</section>}
    {tab === "versions" && <div className="space-y-3">{project.versions.length ? project.versions.map((item) => <div key={item.label} className="flex items-center justify-between rounded-xl border border-slate-200 bg-white p-4"><div><p className="text-xs text-slate-500">{item.label}</p><p className="mt-1 font-medium">{item.value}</p></div><StatusBadge status={item.status} /></div>) : <EmptyState title="还没有版本记录" hint="保存任务书或内容后，这里会出现版本。" />}</div>}
    {tab === "activity" && <div className="space-y-3">{project.activity.length ? project.activity.map((item, index) => <div key={`${item.at}-${index}`} className="rounded-xl border border-slate-200 bg-white p-4"><p className="text-xs text-slate-500">{item.at}</p><p className="mt-1 text-sm">{item.text}</p></div>) : <EmptyState title="还没有项目活动" />}</div>}
    {assetsOpen && <ProjectAssetsDrawer project={project} onClose={() => setAssetsOpen(false)} />}
    {editing && <ContentUnitDialog key={editing === "new" ? "new" : editing.id} project={project} unit={editing === "new" ? undefined : editing} onClose={() => setEditing(null)} onSave={saveUnit} />}
    {deleting && <Modal title="删除内容单元" onClose={() => setDeleting(null)}><p className="text-sm text-slate-600">确定删除「{deleting.title}」吗？此操作只修改本地演示数据。</p><div className="mt-6 flex justify-end gap-2"><Button variant="secondary" onClick={() => setDeleting(null)}>取消</Button><Button variant="danger" onClick={() => deleteUnit(deleting)}>确认删除</Button></div></Modal>}
  </div>;
}

function ContentUnitDialog({ project, unit, onClose, onSave }: { project: ContentProjectView; unit?: ContentUnitView; onClose: () => void; onSave: (input: Omit<ContentUnitView, "id" | "updatedAt">) => void }) {
  const [title, setTitle] = useState(unit?.title || "");
  const [identityId, setIdentityId] = useState(unit?.identityId || project.identities[0]?.id || "new-identity");
  const [modality, setModality] = useState<Modality>(unit?.modality || "text");
  const [channelId, setChannelId] = useState(unit?.channelId || "公众号");
  const [workflowName, setWorkflowName] = useState(unit?.workflowName || "默认生产流程 v1");
  const [status, setStatus] = useState<WorkStatus>(unit?.status || "draft");
  function submit(event: FormEvent) { event.preventDefault(); if (title.trim()) onSave({ title: title.trim(), identityId, modality, channelId: channelId.trim(), workflowName: workflowName.trim(), status }); }
  return <Modal title={unit ? "编辑内容单元" : "新增内容单元"} onClose={onClose}><form onSubmit={submit} className="space-y-4"><Field label="内容名称"><input autoFocus required className={inputClass} value={title} onChange={(event) => setTitle(event.target.value)} /></Field><div className="grid gap-3 sm:grid-cols-2"><Field label="表达身份"><select className={inputClass} value={identityId} onChange={(event) => setIdentityId(event.target.value)}>{project.identities.length ? project.identities.map((identity) => <option key={identity.id} value={identity.id}>{identity.name}</option>) : <option value="new-identity">待设置身份</option>}</select></Field><Field label="内容形态"><select className={inputClass} value={modality} onChange={(event) => setModality(event.target.value as Modality)}>{Object.entries(MODALITIES).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></Field></div><div className="grid gap-3 sm:grid-cols-2"><Field label="渠道"><input required className={inputClass} value={channelId} onChange={(event) => setChannelId(event.target.value)} /></Field><Field label="当前状态"><select className={inputClass} value={status} onChange={(event) => setStatus(event.target.value as WorkStatus)}>{(["draft", "running", "waiting_human", "blocked", "stale", "ready", "unknown"] as WorkStatus[]).map((key) => <option key={key} value={key}>{({ draft: "草稿", running: "进行中", waiting_human: "等待人工", blocked: "受阻", stale: "已过期", ready: "就绪", unknown: "待核对" } as Record<string, string>)[key]}</option>)}</select></Field></div><Field label="生产流程"><input required className={inputClass} value={workflowName} onChange={(event) => setWorkflowName(event.target.value)} /></Field><div className="flex justify-end gap-2"><Button variant="secondary" onClick={onClose}>取消</Button><Button type="submit">保存内容单元</Button></div></form></Modal>;
}

export function ProductionShellPage() {
  const { projectId, unitId } = useParams();
  const [assetsOpen, setAssetsOpen] = useState(false);
  const project = listMockProjects().find((item) => item.id === projectId);
  const unit = project?.contentUnits.find((item) => item.id === unitId);
  if (!project || !unit) return <div className="mx-auto w-full max-w-[1240px] px-5 pb-20 pt-8 sm:px-8 md:pt-12 lg:px-12"><ErrorBanner message="找不到这个内容单元。" /><Link className="mt-4 inline-block text-sm text-indigo-600" to="/projects">返回项目列表</Link></div>;
  return <div className="mx-auto w-full max-w-[1240px] px-5 pb-20 pt-8 sm:px-8 md:pt-12 lg:px-12"><Link to={`/projects/${project.id}?tab=matrix`} className="text-sm text-slate-500 hover:text-indigo-700">← {project.title} / 内容矩阵</Link><div className="mt-4"><PageHead eyebrow="Production Workspace" title={unit.title} description={`${project.identities.find((identity) => identity.id === unit.identityId)?.name || unit.identityId} · ${MODALITIES[unit.modality]} · ${unit.channelId}`} action={<Button variant="secondary" onClick={() => setAssetsOpen(true)}>项目共享素材 · {project.assets.length}</Button>} /></div><div className="grid gap-5 lg:grid-cols-[1fr_270px]"><section className="rounded-2xl border border-slate-200 bg-white p-6"><div className="flex items-center justify-between"><h2 className="font-semibold">当前生产单元</h2><StatusBadge status={unit.status} /></div><p className="mt-3 text-sm text-slate-600">使用「{unit.workflowName}」。内容编辑与流程调试将在 FE-F2 接入。</p><div className="mt-6 rounded-xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center text-sm text-slate-500">{MODALITIES[unit.modality]}生产工作区入口</div></section><aside className="rounded-2xl border border-slate-200 bg-white p-5"><h2 className="font-semibold">项目上下文</h2><p className="mt-3 text-sm text-slate-600">{project.brief.message || project.objective || "尚未填写核心信息"}</p><p className="mt-5 text-xs text-slate-500">{STATUS_EXPLANATION[unit.status] || "当前状态由项目模拟数据展示。"}</p><Button variant="secondary" className="mt-5 w-full" onClick={() => setAssetsOpen(true)}>查看共享素材</Button></aside></div>{assetsOpen && <ProjectAssetsDrawer project={project} onClose={() => setAssetsOpen(false)} />}</div>;
}
