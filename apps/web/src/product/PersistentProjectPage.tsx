import { useTaskLink, taskReturn } from "./taskNavigation";
import { FormEvent, lazy, Suspense, useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api, ApiError, currentUser } from "../api";
import { Button, ErrorBanner, Field, Modal, Spinner, inputClass } from "../components/ui";
import { ProjectOverviewTab } from "./project/ProjectOverviewTab";
import { ProductLaunchPanel } from "./ProductLaunchPanel";
import { ProjectBriefTab } from "./project/ProjectBriefTab";
import { ProjectEvidenceTab } from "./project/ProjectEvidenceTab";
import { ProjectAssetsTab } from "./project/ProjectAssetsTab";
import { ProjectVersionsTab } from "./project/ProjectVersionsTab";
import { ProjectActivityTab } from "./project/ProjectActivityTab";
import type { Modality, Persona, Project, SharedAsset, Unit, WorkflowBinding } from "./project/projectTypes";

const ProjectMatrixTab = lazy(() => import("./project/ProjectMatrixTab").then((module) => ({ default: module.ProjectMatrixTab })));
const ProductionQueuePage = lazy(() => import("./ProductionQueuePage"));

type IdentityChild = { id: number; name: string; status: string; persona_id?: number; account_id?: number };
type CatalogChannel = { channel: string; label: string; content_forms: { content_form: string; label: string; artifact_kind: string; status: "ready" | "planned"; display?: string }[] };
// A work's modality accepts channel forms of these output kinds.
const MODALITY_KINDS: Record<Modality, string[]> = { text: ["text"], graphic: ["image"], video: ["script", "video"] };
type MatrixSuggestion = { personaId: number; accountId: number | null; seriesId: number | null; modality: Modality; channel: string; contentForm: string };

const TABS = ["overview", "brief", "evidence", "assets", "matrix", "variants", "execution", "versions", "activity"] as const;
const TAB_NAMES: Record<string, string> = { overview: "总览", brief: "创作任务书", evidence: "来源与证据", assets: "项目素材", matrix: "作品与形态", variants: "渠道变体", execution: "执行记录", versions: "版本", activity: "活动" };
const TAB_GROUPS = [
  { label: "总览", tabs: ["overview"] },
  { label: "作品", tabs: ["matrix", "variants", "execution"] },
  { label: "项目资料", tabs: ["brief", "evidence", "assets"] },
  { label: "历史记录", tabs: ["versions", "activity"] },
];
const MODALITY_NAMES: Record<Modality, string> = { text: "文字", graphic: "图文", video: "视频" };

function message(error: unknown) { return error instanceof ApiError ? error.message : "连接后端失败，请检查 API 服务。"; }

export function PersistentProjectPage() {
  const taskLink = useTaskLink();
  const { projectId } = useParams();
  const navigate = useNavigate();
  const loadSequence = useRef(0);
  const currentProjectId = useRef(projectId);
  currentProjectId.current = projectId;
  const me = useQuery({ queryKey: ["me", currentUser()], queryFn: () => api.get<{ role: string }>("/users/me"), retry: false });
  const [searchParams, setSearchParams] = useSearchParams();
  const [project, setProject] = useState<Project | null>(null);
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [assets, setAssets] = useState<SharedAsset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [unitModal, setUnitModal] = useState(false);
  const [editingUnit, setEditingUnit] = useState<Unit | null>(null);
  const [projectModal, setProjectModal] = useState(false);
  const [assetsOpen, setAssetsOpen] = useState(false);
  const [unitTitle, setUnitTitle] = useState("");
  const [personaId, setPersonaId] = useState<number | null>(null);
  const [accountId, setAccountId] = useState<number | null>(null);
  const [seriesId, setSeriesId] = useState<number | null>(null);
  const [accounts, setAccounts] = useState<IdentityChild[]>([]);
  const [series, setSeries] = useState<IdentityChild[]>([]);
  const [editorialSeries, setEditorialSeries] = useState<IdentityChild[]>([]);
  const [modality, setModality] = useState<Modality>("text");
  const [channel, setChannel] = useState("");
  const catalog = useQuery({ queryKey: ["channel-catalog", currentUser()], queryFn: () => api.get<CatalogChannel[]>("/channels?catalog=true") });
  const [projectTitle, setProjectTitle] = useState("");
  const [defaultBinding, setDefaultBinding] = useState<WorkflowBinding | null>(null);
  const [rebindDefault, setRebindDefault] = useState(false);
  const [rebindIdentity, setRebindIdentity] = useState(false);
  const tab = TABS.includes(searchParams.get("tab") as typeof TABS[number]) ? searchParams.get("tab")! : "overview";

  const writable = !me.isPending && !me.isError && (me.data?.role === "admin" || me.data?.role === "editor") && project?.status !== "archived";
  const activeGroup = TAB_GROUPS.find(group => group.tabs.includes(tab))!;
  function goTab(nextTab: string) { const next = new URLSearchParams(searchParams); next.set("tab", nextTab); setSearchParams(next); }

  async function reload() {
    if (!projectId) return;
    const requestedProjectId = projectId;
    const sequence = ++loadSequence.current;
    const [nextProject, nextAssets] = await Promise.all([
      api.get<Project>(`/content-projects/${projectId}`), api.get<SharedAsset[]>(`/content-projects/${projectId}/shared-assets`),
    ]);
    const productOnly = nextProject.units.length > 0 && nextProject.units.every(unit => unit.production_domain === "product");
    const nextPersonas = productOnly ? [] : await api.get<Persona[]>("/content-personas");
    if (currentProjectId.current !== requestedProjectId || sequence !== loadSequence.current) return;
    setProject(nextProject); setPersonas(nextPersonas); setAssets(nextAssets);
  }
  useEffect(() => {
    let active = true;
    setLoading(true); setProject(null); setError(""); setAssets([]); setPersonas([]);
    setUnitModal(false); setEditingUnit(null); setProjectModal(false); setAssetsOpen(false);
    setPersonaId(null); setAccountId(null); setSeriesId(null);
    reload().catch((err) => { if (active) setError(message(err)); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; loadSequence.current += 1; };
  }, [projectId]);
  useEffect(() => {
    let active = true;
    setAccounts([]); setEditorialSeries([]);
    if (!personaId) { setDefaultBinding(null); return; }
    api.get<IdentityChild[]>(`/content-personas/${personaId}/accounts`).then(value => { if (active) setAccounts(value); }).catch(err => { if (active) setError(message(err)); });
    api.get<IdentityChild[]>(`/content-personas/${personaId}/series`).then(value => { if (active) setEditorialSeries(value); }).catch(err => { if (active) setError(message(err)); });
    return () => { active = false; };
  }, [personaId]);
  useEffect(() => {
    let active = true;
    setSeries([]);
    if (!accountId) return;
    api.get<IdentityChild[]>(`/content-accounts/${accountId}/series`).then(value => { if (active) setSeries(value); }).catch(err => { if (active) setError(message(err)); });
    return () => { active = false; };
  }, [accountId]);
  useEffect(() => {
    let active = true;
    setDefaultBinding(null);
    if (!personaId) return;
    const query = `persona_id=${personaId}${accountId ? `&account_id=${accountId}` : ""}${seriesId ? `&series_id=${seriesId}` : ""}&modality=${modality}`;
    api.get<WorkflowBinding>(`/content-identities/effective-workflow?${query}`).then(value => { if (active) setDefaultBinding(value); }).catch(err => { if (active) setError(message(err)); });
    return () => { active = false; };
  }, [personaId, accountId, seriesId, modality]);

  async function openRoleUnit() {
    if (!writable) return;
    const requestedProjectId = projectId;
    try {
      const available = personas.length ? personas : await api.get<Persona[]>("/content-personas");
      if (currentProjectId.current !== requestedProjectId) return;
      setPersonas(available); setPersonaId(available[0]?.id ?? null); setAccountId(null); setSeriesId(null); setChannel(""); setUnitModal(true);
    } catch (err) { setError(message(err)); }
  }
  async function createUnit(event: FormEvent) {
    event.preventDefault();
    if (!writable) return;
    if (!project || !personaId) { setError("先选择一个角色。"); return; }
    try { await api.post<Unit>(`/content-projects/${project.id}/units`, { title: unitTitle.trim(), persona_id: personaId, account_id: accountId, series_id: seriesId, modality, channel_id: channel || null }); await reload(); setUnitModal(false); setUnitTitle(""); setError(""); }
    catch (err) { setError(message(err)); }
  }
  async function confirmMatrixSuggestions(rows: MatrixSuggestion[]) {
    if (!project || !writable) throw new Error("当前项目只读，不能创建作品。");
    let created = 0;
    try {
      for (const row of rows) {
        await api.post<Unit>(`/content-projects/${project.id}/units`, {
          title: `${MODALITY_NAMES[row.modality]} · ${row.channel}/${row.contentForm}`,
          persona_id: row.personaId, account_id: row.accountId, series_id: row.seriesId,
          modality: row.modality, channel_id: row.channel,
        });
        created += 1;
      }
    } catch (cause) {
      throw new Error(`已创建 ${created}/${rows.length} 个所选作品；其余未创建。${message(cause)}`);
    } finally { await reload(); }
  }
  async function deleteUnit(unit: Unit) {
    if (!project || !writable || !window.confirm(`移除「${unit.title}」？若已有运行历史，将归档并保留历史记录。`)) return;
    try { await api.del<void>(`/content-projects/${project.id}/units/${unit.id}`); await reload(); }
    catch (err) { setError(message(err)); }
  }
  async function editUnit(event: FormEvent) {
    event.preventDefault();
    if (!writable) return;
    if (!project || !editingUnit) return;
    try {
      const saved = await api.patch<Unit>(`/content-projects/${project.id}/units/${editingUnit.id}`, { title: unitTitle.trim(), ...(channel !== (editingUnit.channel_id || "") ? { channel_id: channel || null } : {}), persona_id: personaId, account_id: accountId, series_id: seriesId, modality, rebind_identity: rebindIdentity, rebind_default: rebindDefault });
      await reload(); setEditingUnit(null); setError("");
      if (saved.id !== editingUnit.id) window.alert(`已有执行历史：已创建新作品 #${saved.id}，旧作品已归档，原运行历史仍可读取。`);
    }
    catch (err) { setError(message(err)); }
  }
  async function editProject(event: FormEvent) {
    event.preventDefault();
    if (!writable) return;
    if (!project) return;
    try { await api.patch<Project>(`/content-projects/${project.id}`, { title: projectTitle.trim() }); await reload(); setProjectModal(false); setError(""); }
    catch (err) { setError(message(err)); }
  }
  async function deleteProject() {
    if (!project || !writable || !window.confirm(`归档项目「${project.title}」？历史任务书、运行和产物仍可查看，归档后不能继续修改。`)) return;
    try { await api.del<void>(`/content-projects/${project.id}`); navigate("/projects"); }
    catch (err) { setError(message(err)); }
  }

  // A channel that also serves other modalities names the forms it offers here, e.g. B站专栏 under 图文 is its 图文笔记.
  const channelOptions = (catalog.data || []).flatMap(item => {
    const forms = item.content_forms.filter(form => MODALITY_KINDS[modality].includes(form.artifact_kind));
    const mixed = item.content_forms.some(form => form.status === "ready" && !MODALITY_KINDS[modality].includes(form.artifact_kind));
    const here = forms.filter(form => form.status === "ready").map(form => form.label).join("、");
    return forms.map(form => ({ ...form, channel: item.channel, name: mixed ? `${item.label} · ${here}` : item.label }));
  });
  const channelField = <Field label="渠道（可选）" hint="只列出支持当前形态的平台；灰色的是平台清单里还没接入的"><select className={inputClass} value={channel} onChange={(event) => setChannel(event.target.value)}>
    <option value="">不指定渠道</option>
    {channel && !channelOptions.some(form => form.channel === channel && form.status === "ready") && <option value={channel}>{channel}（当前值，不在可选清单里）</option>}
    {channelOptions.filter(form => form.status === "ready").filter((form, index, all) => all.findIndex(other => other.channel === form.channel) === index).map(form => <option key={form.channel} value={form.channel}>{form.name}</option>)}
    {channelOptions.filter(form => form.status === "planned").map(form => <option key={`${form.channel}-${form.content_form}`} value="" disabled>{form.display || form.name}（待接入）</option>)}
  </select></Field>;
  const identityFields = <>
    <Field label="角色"><select className={inputClass} value={personaId ?? ""} onChange={(event) => { setPersonaId(Number(event.target.value) || null); setAccountId(null); setSeriesId(null); }}><option value="">请选择</option>{personas.filter((item) => item.status !== "archived" || item.id === editingUnit?.persona_id).map((item) => <option key={item.id} value={item.id}>{item.name}{item.status === "archived" ? " · 已归档" : ""}</option>)}</select></Field><p className="-mt-2 text-xs"><Link className="text-indigo-700 underline" to="/identities">没有合适的角色？去新建角色</Link>（品牌和声音在那里一次定好）</p>
    <Field label="账号（可选）"><select className={inputClass} value={accountId ?? ""} onChange={(event) => { setAccountId(Number(event.target.value) || null); setSeriesId(null); }}><option value="">不绑定账号</option>{accounts.filter((item) => item.status !== "archived" || item.id === editingUnit?.account_id).map((item) => <option key={item.id} value={item.id}>{item.name}{item.status === "archived" ? " · 已归档" : ""}</option>)}</select></Field>
    <Field label="栏目（可选）"><select className={inputClass} value={seriesId ?? ""} onChange={(event) => { const next = Number(event.target.value) || null; setSeriesId(next); if (next && editorialSeries.some((row) => row.id === next)) { setAccountId(null); } }}><option value="">不绑定栏目</option>{editorialSeries.filter((item) => item.status !== "archived" || item.id === editingUnit?.series_id).map((item) => <option key={`e-${item.id}`} value={item.id}>{item.name} · 跨平台栏目{item.status === "archived" ? " · 已归档" : ""}</option>)}{series.filter((item) => item.status !== "archived" || item.id === editingUnit?.series_id).map((item) => <option key={item.id} value={item.id}>{item.name}{item.status === "archived" ? " · 已归档" : ""}</option>)}</select></Field>
  </>;

  if (loading) return <div className="p-9"><Spinner label="读取项目…" /></div>;
  if (!project) return <div className="p-9"><ErrorBanner message={error || "项目不存在或无权访问。"} /></div>;
  return <div className="mx-auto w-full max-w-[1240px] px-5 pb-20 pt-8 sm:px-8 md:pt-12 lg:px-12">
    <Link to={taskReturn(searchParams.get("return_to"), "/projects")} className="text-sm text-slate-500">← 返回项目来源</Link>
    <div className="mb-7 mt-5 flex flex-wrap items-end justify-between gap-x-8 gap-y-5"><div className="min-w-0 max-w-4xl"><p className="eyebrow">内容项目</p><h1 className="mt-3 break-words text-[32px] leading-[1.15] text-ink-900 sm:text-[38px]">{project.title}</h1><p className="mt-3 line-clamp-3 break-words text-[15px] leading-relaxed text-ink-600">{project.objective || "还没有写项目目标"}</p></div><div className="flex flex-wrap gap-2"><Button variant="secondary" size="sm" onClick={() => setAssetsOpen(true)}>共享素材 · {assets.length}</Button>{writable && <Button variant="secondary" size="sm" onClick={() => { setProjectTitle(project.title); setProjectModal(true); }}>编辑项目</Button>}{writable && <Button variant="danger" size="sm" onClick={deleteProject}>归档</Button>}</div></div>
    {project.status === "archived" ? <p className="mb-4 rounded-lg bg-slate-100 p-3 text-sm text-slate-600">项目已归档，仅可查看历史。</p> : !writable && <p className="mb-4 rounded-lg bg-slate-100 p-3 text-sm text-slate-600">{me.isPending ? "正在确认操作权限，当前仅可查看。" : me.isError ? "无法确认操作权限，当前仅可查看。" : "当前账号仅可查看项目。"}</p>}
    {error && <div className="mb-4"><ErrorBanner message={error} /></div>}
    {writable && project.units.length === 0 && <section className="mb-5 rounded-xl border border-indigo-200 bg-indigo-50 p-5"><h2 className="font-semibold">这个项目要做什么？</h2><p className="mt-1 text-sm text-slate-600">项目里还没有作品。选一种开始，项目已有的素材和资料都会保留。</p><div className="mt-3 flex flex-wrap gap-2"><Button onClick={() => void openRoleUnit()}>角色内容</Button><Link to={`/production?workspace=product&project=${project.id}`} className="rounded-md bg-indigo-600 px-4 py-2 text-sm text-white">商品视频</Link></div></section>}
    {searchParams.get("from") === "opportunity" && <p className="mb-5 rounded-xl bg-indigo-50 p-4 text-sm text-indigo-800">选题已建立项目与初始任务书，尚未生成内容。先核对项目资料，再到作品页继续创作。</p>}
    <div role="tablist" aria-label="项目工作区" className="mb-4 flex gap-1 overflow-x-auto border-b border-slate-200">{TAB_GROUPS.map(group => <button key={group.label} role="tab" aria-selected={activeGroup === group} onClick={() => goTab(group.tabs[0])} className={`whitespace-nowrap border-b-2 px-4 py-3 text-sm ${activeGroup === group ? "border-indigo-600 font-semibold text-indigo-700" : "border-transparent text-slate-500"}`}>{group.label}</button>)}</div>
    {activeGroup.tabs.length > 1 && <nav aria-label={`${activeGroup.label}子页`} className="mb-6 flex flex-wrap gap-2">{activeGroup.tabs.map(item => <button key={item} aria-current={tab === item ? "page" : undefined} onClick={() => goTab(item)} className={`rounded-lg px-3 py-2 text-sm ${tab === item ? "bg-indigo-50 font-medium text-indigo-700" : "text-slate-600 hover:bg-slate-100"}`}>{TAB_NAMES[item]}</button>)}</nav>}
    {tab === "brief" && <ProductLaunchPanel key={project.id} projectId={project.id} readOnly={!writable} />}
    {tab === "overview" && <ProjectOverviewTab key={project.id} units={project.units} search={searchParams.toString()} projectId={project.id} productUnitCount={project.units.filter(unit => unit.production_domain === "product" && unit.status !== "archived").length} productOnly={project.units.length > 0 && project.units.every(unit => unit.production_domain === "product")} />}
    {tab === "brief" && <ProjectBriefTab key={project.id} projectId={project.id} readOnly={!writable} onSaved={() => { reload().catch((err) => setError(message(err))); }} />}
    {tab === "evidence" && <ProjectEvidenceTab key={project.id} projectId={project.id} readOnly={!writable} />}
    {tab === "matrix" && <Suspense fallback={<Spinner label="加载内容矩阵…" />}><ProjectMatrixTab key={project.id} readOnly={!writable} project={project} personas={personas} onAddUnit={() => void openRoleUnit()} onEditUnit={(unit) => { if (!writable) return; if (unit.production_domain === "product") { navigate(taskLink(`/projects/${project.id}/units/${unit.id}/production?workstep=goal`)); return; } setEditingUnit(unit); setUnitTitle(unit.title); setPersonaId(unit.persona_id); setAccountId(unit.account_id); setSeriesId(unit.series_id); setModality(unit.modality); setChannel(unit.channel_id || ""); setRebindDefault(false); setRebindIdentity(false); }} onDeleteUnit={deleteUnit} onConfirmSuggestions={confirmMatrixSuggestions} /></Suspense>}
    {tab === "assets" && <ProjectAssetsTab key={project.id} projectId={project.id} readOnly={!writable} onChanged={() => { reload().catch((err) => setError(message(err))); }} />}
    {tab === "variants" && <section className="space-y-4 rounded-xl border bg-white p-5"><h2 className="font-semibold">按作品管理渠道变体</h2><p className="text-sm text-slate-500">进入作品后，基于已保存 Master 显式创建或查看渠道变体；不会在打开此页时执行适配。</p>{project.units.map(unit => <div key={unit.id} className="flex flex-wrap items-center justify-between gap-3 rounded-lg border p-3"><span>{unit.title} · {MODALITY_NAMES[unit.modality]}{unit.status === "archived" ? " · 归档只读" : ""}</span><Link className="text-sm text-indigo-700 underline" to={taskLink(`/projects/${project.id}/units/${unit.id}/production?panel=variants`)}>查看渠道变体</Link></div>)}{!project.units.length && <p className="text-sm text-slate-500">先在内容矩阵创建内容单元。</p>}</section>}
    {tab === "execution" && <Suspense fallback={<Spinner label="读取项目执行队列…" />}><ProductionQueuePage projectId={project.id} /></Suspense>}
    {tab === "versions" && <ProjectVersionsTab key={project.id} projectId={project.id} />}
    {tab === "activity" && <ProjectActivityTab key={project.id} projectId={project.id} />}
    {assetsOpen && <Modal title={`项目共享素材 · ${assets.length}`} onClose={() => setAssetsOpen(false)} wide><ProjectAssetsTab key={project.id} projectId={project.id} readOnly={!writable} onChanged={() => { reload().catch((err) => setError(message(err))); }} /></Modal>}
    {projectModal && writable && <Modal title="编辑项目" onClose={() => setProjectModal(false)}><form onSubmit={editProject} className="space-y-4"><Field label="项目名称"><input required className={inputClass} value={projectTitle} onChange={(event) => setProjectTitle(event.target.value)} /></Field><p className="text-xs text-slate-500">项目目标请在「创作任务书」中保存为新版本。</p><Button type="submit">保存项目</Button></form></Modal>}
    {editingUnit && writable && <Modal title="编辑作品" onClose={() => setEditingUnit(null)}><form onSubmit={editUnit} className="space-y-4"><Field label="作品名称"><input required className={inputClass} value={unitTitle} onChange={(event) => setUnitTitle(event.target.value)} /></Field>{identityFields}<Field label="内容形态"><select className={inputClass} value={modality} onChange={(event) => { setModality(event.target.value as Modality); setChannel(""); }}>{Object.entries(MODALITY_NAMES).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></Field>{channelField}<label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={rebindIdentity} onChange={(event) => setRebindIdentity(event.target.checked)} />重新读取角色最新资料</label><label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={rebindDefault} onChange={(event) => setRebindDefault(event.target.checked)} />重新绑定当前有效默认工作流{defaultBinding?.workflow_id ? `（${defaultBinding.source || "身份"} · 版本 ${defaultBinding.workflow_version}）` : "（尚无默认版本）"}</label><p className="text-xs text-slate-500">更换身份、账号或栏目会生成新快照，并重新解析默认工作流。若有执行历史，保存将创建替代单元并归档旧单元。</p><Button type="submit">保存单元</Button></form></Modal>}
    {unitModal && writable && <Modal title="新增作品" onClose={() => setUnitModal(false)}><form onSubmit={createUnit} className="space-y-4"><Field label="名称"><input required className={inputClass} value={unitTitle} onChange={(event) => setUnitTitle(event.target.value)} /></Field>{identityFields}<Field label="内容形态"><select className={inputClass} value={modality} onChange={(event) => { setModality(event.target.value as Modality); setChannel(""); }}>{Object.entries(MODALITY_NAMES).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></Field>{channelField}<p className="text-xs text-slate-500">当前有效默认：{defaultBinding?.workflow_id ? `${defaultBinding.source || "身份"} · 版本 ${defaultBinding.workflow_version}（创建时固定）` : "尚未设置，可进入生产工作台创建项目覆盖"}</p><Button type="submit">保存作品</Button></form></Modal>}
  </div>;
}
