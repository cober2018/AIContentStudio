import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, ApiError } from "../api";
import { Button, EmptyState, ErrorBanner, Field, Modal, Spinner, StatusBadge, inputClass } from "../components/ui";
import { ProductCreationDialog } from "./ProductCreationDialog";
import type { Project } from "./project/projectTypes";

function message(error: unknown) { return error instanceof ApiError ? error.message : "连接后端失败，请检查 API 服务。"; }

export function PersistentProjectsPage() {
  const [editable, setEditable] = useState(false);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [title, setTitle] = useState("");
  const [productCreating, setProductCreating] = useState(false);
  const [creating, setCreating] = useState(false);
  const navigate = useNavigate();
  useEffect(() => { api.get<{ role: string }>("/users/me").then(user => setEditable(["admin", "editor"].includes(user.role))).catch(() => setEditable(false)); }, []);
  useEffect(() => { api.get<Project[]>("/content-projects").then(setProjects).catch((err) => setError(message(err))).finally(() => setLoading(false)); }, []);

  async function create(event: FormEvent) {
    event.preventDefault();
    try {
      const project = await api.post<Project>("/content-projects", { title: title.trim(), objective: "" });
      navigate(`/projects/${project.id}`);
    } catch (err) { setError(message(err)); }
  }

  return <div className="mx-auto max-w-7xl px-6 py-9">
    <div className="mb-7 flex flex-wrap items-start justify-between gap-3"><div><p className="text-xs font-semibold uppercase tracking-widest text-indigo-600">Content Projects</p><h1 className="mt-2 text-3xl font-semibold">内容项目</h1><p className="mt-2 text-sm text-slate-500">真实项目保存在后端；演示样本与真实数据分离。</p></div><div className="flex gap-2"><Link className="rounded-lg border border-slate-300 px-4 py-2 text-sm" to="/projects/demo">查看本地演示</Link>{editable && <Button variant="secondary" onClick={() => setProductCreating(true)}>从商品创作</Button>}<Button onClick={() => setCreating(true)}>新建项目</Button></div></div>
    {error && <ErrorBanner message={error} />}
    {loading ? <Spinner label="读取后端项目…" /> : projects.length === 0 ? <EmptyState title="还没有真实项目" hint="创建项目后可以添加角色、内容单元与持久化工作流。" action={<Button onClick={() => setCreating(true)}>新建项目</Button>} /> : <div className="grid gap-4 lg:grid-cols-2">{projects.map((project) => <Link key={project.id} to={`/projects/${project.id}`} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm hover:border-indigo-300"><div className="flex items-center justify-between gap-3"><h2 className="text-lg font-semibold">{project.title}</h2><StatusBadge status={project.status} /></div><p className="mt-3 text-sm text-slate-600">{project.objective || "待填写项目目标"}</p><p className="mt-4 text-xs text-slate-500">{project.units.length} 个内容单元 · 后端持久化</p></Link>)}</div>}
    {productCreating && <ProductCreationDialog onClose={() => setProductCreating(false)} />}
    {creating && <Modal title="新建内容项目" onClose={() => setCreating(false)}><form onSubmit={create} className="space-y-4"><Field label="项目名称"><input autoFocus required className={inputClass} value={title} onChange={(event) => setTitle(event.target.value)} /></Field><div className="flex justify-end gap-2"><Button variant="secondary" onClick={() => setCreating(false)}>取消</Button><Button type="submit">创建</Button></div></form></Modal>}
  </div>;
}
