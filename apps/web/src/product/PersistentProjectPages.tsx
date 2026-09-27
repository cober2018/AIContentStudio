import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { api, ApiError } from "../api";
import { Button, EmptyState, ErrorBanner, Field, Modal, Spinner, StatusBadge, inputClass } from "../components/ui";
import { ProductionDesigner } from "./ProductionDesigner";
import { ProjectOverviewTab } from "./project/ProjectOverviewTab";
import { ProjectBriefTab } from "./project/ProjectBriefTab";
import { ProjectEvidenceTab } from "./project/ProjectEvidenceTab";
import { ProjectAssetsTab } from "./project/ProjectAssetsTab";
import { ProjectVersionsTab } from "./project/ProjectVersionsTab";
import { ProjectActivityTab } from "./project/ProjectActivityTab";
import { ProjectMatrixTab } from "./project/ProjectMatrixTab";
import type { SharedAsset } from "./project/types";
export type { SharedAsset } from "./project/types";

export type Modality = "text" | "graphic" | "video";
export type Definition = { nodes: WorkflowNode[]; edges: { from: string; to: string }[]; visual_order: string[] };
export type WorkflowNode = {
  id: string; kind: "Data" | "AI" | "Tool" | "Rule" | "Human" | "System";
  plugin: string; plugin_version?: string; label?: string; config: Record<string, unknown>;
  input_mapping?: Record<string, unknown>; output_mapping?: Record<string, unknown>;
  condition?: Record<string, unknown> | string; failure_policy?: string; enabled?: boolean;
};
export type WorkflowBinding = { revision: number; workflow_id: number | null; workflow_version: number | null; definition_checksum: string | null; definition: Definition; source?: string };
export type Persona = { id: number; name: string; brand_id?: number | null; status?: string };
export type Unit = { id: number; project_id: number; persona_id: number; account_id: number | null; series_id: number | null; identity_snapshot_id: number | null; identity_state: string; modality: Modality; channel_id: string | null; title: string; status: string; pinned_workflow_id: number | null };
type IdentityChild = { id: number; name: string; status: string; persona_id?: number; account_id?: number };
export type Project = { id: number; title: string; objective: string; status: string; units: Unit[] };

const TABS = ["overview", "brief", "evidence", "assets", "matrix", "versions", "activity"] as const;
const TAB_NAMES = ["总览", "创作任务书", "来源与证据", "项目素材", "内容矩阵", "版本", "活动"];
const MODALITY_NAMES: Record<Modality, string> = { text: "文字", graphic: "图文", video: "视频" };

function message(error: unknown) { return error instanceof ApiError ? error.message : "连接后端失败，请检查 API 服务。"; }

export function PersistentProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [title, setTitle] = useState("");
  const [creating, setCreating] = useState(false);
  const navigate = useNavigate();
  useEffect(() => { api.get<Project[]>("/content-projects").then(setProjects).catch((err) => setError(message(err))).finally(() => setLoading(false)); }, []);

  async function create(event: FormEvent) {
    event.preventDefault();
    try {
      const project = await api.post<Project>("/content-projects", { title: title.trim(), objective: "" });
      navigate(`/projects/${project.id}`);
    } catch (err) { setError(message(err)); }
  }

  return <div className="mx-auto max-w-7xl px-6 py-9">
    <div className="mb-7 flex flex-wrap items-start justify-between gap-3"><div><p className="text-xs font-semibold uppercase tracking-widest text-indigo-600">Content Projects</p><h1 className="mt-2 text-3xl font-semibold">内容项目</h1><p className="mt-2 text-sm text-slate-500">真实项目保存在后端；演示样本与真实数据分离。</p></div><div className="flex gap-2"><Link className="rounded-lg border border-slate-300 px-4 py-2 text-sm" to="/projects/demo">查看本地演示</Link><Button onClick={() => setCreating(true)}>新建项目</Button></div></div>
    {error && <ErrorBanner message={error} />}
    {loading ? <Spinner label="读取后端项目…" /> : projects.length === 0 ? <EmptyState title="还没有真实项目" hint="创建项目后可以添加角色、内容单元与持久化工作流。" action={<Button onClick={() => setCreating(true)}>新建项目</Button>} /> : <div className="grid gap-4 lg:grid-cols-2">{projects.map((project) => <Link key={project.id} to={`/projects/${project.id}`} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm hover:border-indigo-300"><div className="flex items-center justify-between gap-3"><h2 className="text-lg font-semibold">{project.title}</h2><StatusBadge status={project.status} /></div><p className="mt-3 text-sm text-slate-600">{project.objective || "待填写项目目标"}</p><p className="mt-4 text-xs text-slate-500">{project.units.length} 个内容单元 · 后端持久化</p></Link>)}</div>}
    {creating && <Modal title="新建内容项目" onClose={() => setCreating(false)}><form onSubmit={create} className="space-y-4"><Field label="项目名称"><input autoFocus required className={inputClass} value={title} onChange={(event) => setTitle(event.target.value)} /></Field><div className="flex justify-end gap-2"><Button variant="secondary" onClick={() => setCreating(false)}>取消</Button><Button type="submit">创建</Button></div></form></Modal>}
  </div>;
}

export function PersistentProjectPage() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [project, setProject] = useState<Project | null>(null);
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [assets, setAssets] = useState<SharedAsset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [unitModal, setUnitModal] = useState(false);
  const [editingUnit, setEditingUnit] = useState<Unit | null>(null);
  const [projectModal, setProjectModal] = useState(false);
  const [personaModal, setPersonaModal] = useState(false);
  const [assetsOpen, setAssetsOpen] = useState(false);
  const [unitTitle, setUnitTitle] = useState("");
  const [personaName, setPersonaName] = useState("");
  const [personaId, setPersonaId] = useState<number | null>(null);
  const [accountId, setAccountId] = useState<number | null>(null);
  const [seriesId, setSeriesId] = useState<number | null>(null);
  const [accounts, setAccounts] = useState<IdentityChild[]>([]);
  const [series, setSeries] = useState<IdentityChild[]>([]);
  const [modality, setModality] = useState<Modality>("text");
  const [channel, setChannel] = useState("wechat");
  const [projectTitle, setProjectTitle] = useState("");
  const [defaultBinding, setDefaultBinding] = useState<WorkflowBinding | null>(null);
  const [rebindDefault, setRebindDefault] = useState(false);
  const [rebindIdentity, setRebindIdentity] = useState(false);
  const tab = TABS.includes(searchParams.get("tab") as typeof TABS[number]) ? searchParams.get("tab")! : "overview";

  async function reload() {
    if (!projectId) return;
    const [nextProject, nextPersonas, nextAssets] = await Promise.all([
      api.get<Project>(`/content-projects/${projectId}`), api.get<Persona[]>("/content-personas"), api.get<SharedAsset[]>(`/content-projects/${projectId}/shared-assets`),
    ]);
    setProject(nextProject); setPersonas(nextPersonas); setAssets(nextAssets);
  }
  useEffect(() => { setLoading(true); reload().catch((err) => setError(message(err))).finally(() => setLoading(false)); }, [projectId]);
  useEffect(() => {
    if (!personaId) { setDefaultBinding(null); setAccounts([]); return; }
    api.get<IdentityChild[]>(`/content-personas/${personaId}/accounts`).then(setAccounts).catch((err) => setError(message(err)));
  }, [personaId]);
  useEffect(() => {
    if (!accountId) { setSeries([]); return; }
    api.get<IdentityChild[]>(`/content-accounts/${accountId}/series`).then(setSeries).catch((err) => setError(message(err)));
  }, [accountId]);
  useEffect(() => {
    if (!personaId) { setDefaultBinding(null); return; }
    const query = `persona_id=${personaId}${accountId ? `&account_id=${accountId}` : ""}${seriesId ? `&series_id=${seriesId}` : ""}&modality=${modality}`;
    api.get<WorkflowBinding>(`/content-identities/effective-workflow?${query}`).then(setDefaultBinding).catch((err) => setError(message(err)));
  }, [personaId, accountId, seriesId, modality]);

  async function createPersona(event: FormEvent) {
    event.preventDefault();
    try { const created = await api.post<Persona>("/content-personas", { name: personaName.trim() }); setPersonas([...personas, created]); setPersonaId(created.id); setPersonaModal(false); setPersonaName(""); }
    catch (err) { setError(message(err)); }
  }
  async function createUnit(event: FormEvent) {
    event.preventDefault();
    if (!project || !personaId) { setError("先选择一个内容身份。" ); return; }
    try { await api.post<Unit>(`/content-projects/${project.id}/units`, { title: unitTitle.trim(), persona_id: personaId, account_id: accountId, series_id: seriesId, modality, channel_id: channel }); await reload(); setUnitModal(false); setUnitTitle(""); setError(""); }
    catch (err) { setError(message(err)); }
  }
  async function deleteUnit(unit: Unit) {
    if (!project || !window.confirm(`移除「${unit.title}」？若已有运行历史，将归档并保留历史记录。`)) return;
    try { await api.del<void>(`/content-projects/${project.id}/units/${unit.id}`); await reload(); }
    catch (err) { setError(message(err)); }
  }
  async function editUnit(event: FormEvent) {
    event.preventDefault();
    if (!project || !editingUnit) return;
    try {
      const saved = await api.patch<Unit>(`/content-projects/${project.id}/units/${editingUnit.id}`, { title: unitTitle.trim(), channel_id: channel, persona_id: personaId, account_id: accountId, series_id: seriesId, modality, rebind_identity: rebindIdentity, rebind_default: rebindDefault });
      await reload(); setEditingUnit(null); setError("");
      if (saved.id !== editingUnit.id) window.alert(`已有执行历史：已创建新单元 #${saved.id}，旧单元已归档，原运行历史仍可读取。`);
    }
    catch (err) { setError(message(err)); }
  }
  async function editProject(event: FormEvent) {
    event.preventDefault();
    if (!project) return;
    try { await api.patch<Project>(`/content-projects/${project.id}`, { title: projectTitle.trim() }); await reload(); setProjectModal(false); setError(""); }
    catch (err) { setError(message(err)); }
  }
  async function deleteProject() {
    if (!project || !window.confirm(`归档项目「${project.title}」？历史任务书、运行和产物仍可查看，归档后不能继续修改。`)) return;
    try { await api.del<void>(`/content-projects/${project.id}`); navigate("/projects"); }
    catch (err) { setError(message(err)); }
  }

  const identityFields = <>
    <Field label="内容身份"><select className={inputClass} value={personaId ?? ""} onChange={(event) => { setPersonaId(Number(event.target.value) || null); setAccountId(null); setSeriesId(null); }}><option value="">请选择</option>{personas.filter((item) => item.status !== "archived" || item.id === editingUnit?.persona_id).map((item) => <option key={item.id} value={item.id}>{item.name}{item.status === "archived" ? " · 已归档" : ""}</option>)}</select></Field>
    <Field label="账号（可选）"><select className={inputClass} value={accountId ?? ""} onChange={(event) => { setAccountId(Number(event.target.value) || null); setSeriesId(null); }}><option value="">不绑定账号</option>{accounts.filter((item) => item.status !== "archived" || item.id === editingUnit?.account_id).map((item) => <option key={item.id} value={item.id}>{item.name}{item.status === "archived" ? " · 已归档" : ""}</option>)}</select></Field>
    <Field label="栏目（可选）"><select className={inputClass} value={seriesId ?? ""} onChange={(event) => setSeriesId(Number(event.target.value) || null)}><option value="">不绑定栏目</option>{series.filter((item) => item.status !== "archived" || item.id === editingUnit?.series_id).map((item) => <option key={item.id} value={item.id}>{item.name}{item.status === "archived" ? " · 已归档" : ""}</option>)}</select></Field>
  </>;

  if (loading) return <div className="p-9"><Spinner label="读取项目…" /></div>;
  if (!project) return <div className="p-9"><ErrorBanner message={error || "项目不存在或无权访问。"} /></div>;
  return <div className="mx-auto max-w-7xl px-6 py-9">
    <Link to="/projects" className="text-sm text-slate-500">← 内容项目</Link>
    <div className="mt-4 mb-6 flex flex-wrap items-start justify-between gap-4"><div><p className="text-xs font-semibold uppercase tracking-widest text-indigo-600">Content Project</p><h1 className="mt-2 text-3xl font-semibold">{project.title}</h1><p className="mt-2 text-sm text-slate-500">{project.objective || "项目目标待填写"}</p></div><div className="flex flex-wrap gap-2">{project.status !== "archived" && <Button variant="secondary" onClick={() => { setProjectTitle(project.title); setProjectModal(true); }}>编辑项目</Button>}<Button variant="secondary" onClick={() => setAssetsOpen(true)}>项目共享素材 · {assets.length}</Button>{project.status !== "archived" && <Button variant="danger" onClick={deleteProject}>归档项目</Button>}</div></div>
    {project.status === "archived" && <p className="mb-4 rounded-lg bg-slate-100 p-3 text-sm text-slate-600">项目已归档，仅可查看历史；所有项目级保存和运行操作均被服务端拒绝。</p>}
    {error && <div className="mb-4"><ErrorBanner message={error} /></div>}
    <div role="tablist" aria-label="项目工作区" className="mb-6 flex gap-1 overflow-x-auto border-b border-slate-200">{TABS.map((item, index) => <button key={item} role="tab" aria-selected={tab === item} onClick={() => setSearchParams({ tab: item })} className={`whitespace-nowrap border-b-2 px-4 py-3 text-sm ${tab === item ? "border-indigo-600 font-semibold text-indigo-700" : "border-transparent text-slate-500"}`}>{TAB_NAMES[index]}</button>)}</div>
    {tab === "overview" && <ProjectOverviewTab projectId={project.id} />}
    {tab === "brief" && <ProjectBriefTab projectId={project.id} readOnly={project.status === "archived"} onSaved={() => { reload().catch((err) => setError(message(err))); }} />}
    {tab === "evidence" && <ProjectEvidenceTab projectId={project.id} readOnly={project.status === "archived"} />}
    {tab === "matrix" && <ProjectMatrixTab project={project} personas={personas} onAddPersona={() => setPersonaModal(true)} onAddUnit={() => { setPersonaId(personas[0]?.id ?? null); setAccountId(null); setSeriesId(null); setUnitModal(true); }} onEditUnit={(unit) => { setEditingUnit(unit); setUnitTitle(unit.title); setPersonaId(unit.persona_id); setAccountId(unit.account_id); setSeriesId(unit.series_id); setModality(unit.modality); setChannel(unit.channel_id || ""); setRebindDefault(false); setRebindIdentity(false); }} onDeleteUnit={deleteUnit} />}
    {tab === "assets" && <ProjectAssetsTab projectId={project.id} readOnly={project.status === "archived"} onChanged={() => { reload().catch((err) => setError(message(err))); }} />}
    {tab === "versions" && <ProjectVersionsTab projectId={project.id} />}
    {tab === "activity" && <ProjectActivityTab projectId={project.id} />}
    {assetsOpen && <Modal title={`项目共享素材 · ${assets.length}`} onClose={() => setAssetsOpen(false)} wide><ProjectAssetsTab projectId={project.id} readOnly={project.status === "archived"} onChanged={() => { reload().catch((err) => setError(message(err))); }} /></Modal>}
    {projectModal && <Modal title="编辑项目" onClose={() => setProjectModal(false)}><form onSubmit={editProject} className="space-y-4"><Field label="项目名称"><input required className={inputClass} value={projectTitle} onChange={(event) => setProjectTitle(event.target.value)} /></Field><p className="text-xs text-slate-500">项目目标请在「创作任务书」中保存为新版本。</p><Button type="submit">保存项目</Button></form></Modal>}
    {editingUnit && <Modal title="编辑内容单元" onClose={() => setEditingUnit(null)}><form onSubmit={editUnit} className="space-y-4"><Field label="内容名称"><input required className={inputClass} value={unitTitle} onChange={(event) => setUnitTitle(event.target.value)} /></Field>{identityFields}<Field label="内容形态"><select className={inputClass} value={modality} onChange={(event) => setModality(event.target.value as Modality)}>{Object.entries(MODALITY_NAMES).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></Field><Field label="渠道"><input className={inputClass} value={channel} onChange={(event) => setChannel(event.target.value)} /></Field><label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={rebindIdentity} onChange={(event) => setRebindIdentity(event.target.checked)} />显式刷新当前身份快照</label><label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={rebindDefault} onChange={(event) => setRebindDefault(event.target.checked)} />重新绑定当前有效默认工作流{defaultBinding?.workflow_id ? `（${defaultBinding.source || "身份"} · 版本 ${defaultBinding.workflow_version}）` : "（尚无默认版本）"}</label><p className="text-xs text-slate-500">更换身份、账号或栏目会生成新快照，并重新解析默认工作流。若有执行历史，保存将创建替代单元并归档旧单元。</p><Button type="submit">保存单元</Button></form></Modal>}
    {personaModal && <Modal title="新增内容身份" onClose={() => setPersonaModal(false)}><form onSubmit={createPersona} className="space-y-4"><Field label="身份名称"><input required autoFocus className={inputClass} value={personaName} onChange={(event) => setPersonaName(event.target.value)} /></Field><Button type="submit">保存身份</Button></form></Modal>}
    {unitModal && <Modal title="新增内容单元" onClose={() => setUnitModal(false)}><form onSubmit={createUnit} className="space-y-4"><Field label="名称"><input required className={inputClass} value={unitTitle} onChange={(event) => setUnitTitle(event.target.value)} /></Field>{identityFields}<Field label="内容形态"><select className={inputClass} value={modality} onChange={(event) => setModality(event.target.value as Modality)}>{Object.entries(MODALITY_NAMES).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></Field><Field label="渠道"><input className={inputClass} value={channel} onChange={(event) => setChannel(event.target.value)} /></Field><p className="text-xs text-slate-500">当前有效默认：{defaultBinding?.workflow_id ? `${defaultBinding.source || "身份"} · 版本 ${defaultBinding.workflow_version}（创建时固定）` : "尚未设置，可进入生产工作台创建项目覆盖"}</p><Button type="submit">保存内容单元</Button></form></Modal>}
  </div>;
}

export function PersistentProductionPage() {
  const { projectId, unitId } = useParams();
  if (!projectId || !unitId) return <ErrorBanner message="缺少项目或内容单元。" />;
  return <ProductionDesigner projectId={Number(projectId)} unitId={Number(unitId)} />;
}
