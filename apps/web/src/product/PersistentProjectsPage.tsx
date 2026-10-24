import { useTaskLink } from "./taskNavigation";
import { FormEvent, useEffect, useRef, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { api, ApiError, currentUser } from "../api";
import { Button, Chip, EmptyState, ErrorBanner, Field, Page, PageHeader, Spinner, StatusBadge, inputClass } from "../components/ui";
import type { Project } from "./project/projectTypes";

function message(error: unknown) { return error instanceof ApiError ? error.message : "连接后端失败，请检查 API 服务。"; }
const pageSize = 20;

export function PersistentProjectsPage() {
  const [editable, setEditable] = useState(false);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [listError, setListError] = useState("");
  const draftKey = `studio-project-draft:${currentUser()}`;
  const [draft, setDraft] = useState<{title: string; objective: string}>(() => {
    try { const saved = JSON.parse(sessionStorage.getItem(draftKey) ?? "null"); return {title: typeof saved?.title === "string" ? saved.title : "", objective: typeof saved?.objective === "string" ? saved.objective : ""}; }
    catch { return {title: "", objective: ""}; }
  });
  const [saving, setSaving] = useState(false);
  const savingRef = useRef(false);
  const taskLink = useTaskLink();
  const [params, setParams] = useSearchParams();
  const navigate = useNavigate();
  const creating = params.get("view") === "new";
  const q = params.get("q") ?? "";
  const status = params.get("status") ?? "";
  const requestedPage = Number(params.get("page") ?? "1");
  const page = Number.isSafeInteger(requestedPage) && requestedPage > 0 ? requestedPage : 1;
  function update(values: Record<string, string>, resetPage = true) {
    setParams(previous => { const next = new URLSearchParams(previous); if (resetPage) next.delete("page"); Object.entries(values).forEach(([key,value]) => value ? next.set(key,value) : next.delete(key)); return next; });
  }
  useEffect(() => { let active = true; api.get<{ role: string }>("/users/me").then(user => { if (active) setEditable(["admin", "editor"].includes(user.role)); }).catch(() => { if (active) setEditable(false); }); return () => { active = false; }; }, []);
  useEffect(() => { let active = true; api.get<Project[]>("/content-projects").then(items => { if (active) setProjects(items); }).catch(err => { if (active) setListError(message(err)); }).finally(() => { if (active) setLoading(false); }); return () => { active = false; }; }, []);
  useEffect(() => { try { sessionStorage.setItem(draftKey, JSON.stringify(draft)); } catch { /* Storage can be unavailable in private sessions. */ } }, [draft, draftKey]);

  async function create(event: FormEvent) {
    event.preventDefault();
    if (!editable || savingRef.current || !draft.title.trim()) return;
    savingRef.current = true; setSaving(true); setError("");
    try {
      const project = await api.post<Project>("/content-projects", { title: draft.title.trim(), objective: draft.objective.trim() });
      try { sessionStorage.removeItem(draftKey); } catch { /* Saving must not depend on browser storage. */ }
      setDraft({title: "", objective: ""});
      navigate(taskLink(`/projects/${project.id}?tab=overview`));
    } catch (err) { setError(message(err)); }
    finally { savingRef.current = false; setSaving(false); }
  }
  const filtered = projects.filter(project => (!status || (status === "active" ? project.status !== "archived" : project.status === status)) && `${project.title} ${project.objective}`.toLowerCase().includes(q.toLowerCase()));
  const lastPage = Math.max(1, Math.ceil(filtered.length / pageSize));
  const actualPage = Math.min(page, lastPage);
  const visible = filtered.slice((actualPage - 1) * pageSize, actualPage * pageSize);
  const modalityName: Record<string, string> = { text: "文字", graphic: "图文", video: "视频", audio: "音频" };
  return <Page>
    {creating && <button className="-mb-2 text-[13px] text-ink-500 hover:text-ink-900" onClick={() => { setError(""); update({view: ""}, false); }}>← 项目档案</button>}
    <PageHeader eyebrow={creating ? "新建" : "创作 · 项目"} title={creating ? "新建项目" : "内容项目"} lead={creating ? "先保存名称和目标，再整理资料与作品。创建项目不会自动生成内容。" : "一个项目是一件事：目标、参考资料，以及围绕它做出的文字、图文和视频。"}
      actions={creating ? undefined : <><Link className="inline-flex h-9 items-center rounded-pill border border-ink-300/90 bg-surface px-4 text-[13.5px] font-medium text-ink-800 hover:border-ink-500" to="/production?workspace=persona">角色内容工作台</Link>{editable && <Button onClick={() => { setError(""); update({view: "new"}, false); }}>新建项目</Button>}</>} />
    {error && <ErrorBanner message={error} />}
    {!creating && listError && <ErrorBanner message={listError} />}
    {creating ? editable ? <form onSubmit={create} className="card max-w-2xl space-y-5 p-7"><Field label="项目名称"><input autoFocus required maxLength={200} disabled={saving} className={inputClass} value={draft.title} onChange={event => setDraft({...draft,title:event.target.value})} /></Field><Field label="项目目标（选填）"><textarea disabled={saving} className={inputClass} rows={4} value={draft.objective} onChange={event => setDraft({...draft,objective:event.target.value})} /></Field><p className="text-xs text-slate-500">未提交内容仅在当前用户的浏览器标签页暂存。</p><Button type="submit" disabled={saving || !draft.title.trim()}>{saving ? "正在保存…" : "保存并进入项目"}</Button></form> : <EmptyState title="当前账号不能新建项目" hint="编辑权限确认后才能创建；已有项目可返回列表查看。" /> : <>
      <div className="flex flex-wrap items-center gap-3"><div className="relative min-w-[220px] flex-1 sm:max-w-sm"><input aria-label="搜索名称或目标" placeholder="搜索名称或目标" className={`${inputClass} pl-9`} value={q} onChange={event => update({q:event.target.value})} /><span aria-hidden className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-ink-400">⌕</span></div><select aria-label="项目状态" className={`${inputClass} !w-auto`} value={status} onChange={event => update({status:event.target.value})}><option value="">全部状态</option><option value="active">进行中</option><option value="archived">已归档</option></select>{!loading && !listError && <span className="ml-auto text-[13px] text-ink-500">共 {filtered.length} 个项目</span>}</div>
      {loading ? <Spinner label="读取项目…" /> : listError ? null : !visible.length ? <EmptyState title="当前筛选下没有项目" hint="调整搜索条件，或新建一个项目。" /> : <div className="grid gap-4 lg:grid-cols-2">{visible.map((project, index) => { const units = project.units.filter(unit => unit.lifecycle !== "deleted"); const counts = units.reduce<Record<string, number>>((all, unit) => ({ ...all, [unit.modality]: (all[unit.modality] || 0) + 1 }), {}); return <Link key={project.id} to={taskLink(`/projects/${project.id}?tab=overview`)} style={{ animationDelay: `${Math.min(index, 8) * 40}ms` }} className="card group flex min-w-0 animate-rise flex-col p-6 transition-[transform,box-shadow,border-color] duration-300 ease-studio hover:-translate-y-0.5 hover:border-ink-300 hover:shadow-lift"><div className="flex items-start justify-between gap-3"><h2 className="line-clamp-2 min-w-0 break-words font-serif text-[20px] font-semibold leading-snug text-ink-900">{project.title}</h2><StatusBadge status={project.status} /></div><p className="mt-3 line-clamp-3 break-words text-[14px] leading-relaxed text-ink-600">{project.objective || "还没有写项目目标"}</p><div className="mt-auto flex flex-wrap items-center gap-1.5 pt-5">{Object.entries(counts).map(([modality, count]) => <Chip key={modality}>{modalityName[modality] || modality} {count}</Chip>)}{!units.length && <span className="text-[12.5px] text-ink-500">还没有作品</span>}<span aria-hidden className="ml-auto text-[13px] text-ink-400 transition-transform group-hover:translate-x-0.5 group-hover:text-accent-500">打开 →</span></div></Link>; })}</div>}
      {!loading && !listError && lastPage > 1 && <div className="flex items-center justify-center gap-3"><Button variant="secondary" size="sm" disabled={actualPage <= 1} onClick={() => update({page:String(actualPage-1)})}>上一页</Button><span className="text-[13px] text-ink-500">第 {actualPage} / {lastPage} 页</span><Button variant="secondary" size="sm" disabled={actualPage >= lastPage} onClick={() => update({page:String(actualPage+1)})}>下一页</Button></div>}
    </>}
  </Page>;
}
