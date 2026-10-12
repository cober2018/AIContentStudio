import { lazy, Suspense, useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api, ApiError, currentUser } from "../../api";
import { Button, EmptyState, ErrorBanner, Field, Spinner, inputClass } from "../../components/ui";
import type { SharedAsset } from "./types";

const ProviderMediaPanel = lazy(() => import("../ProviderMediaPanel"));
const ProviderSearchPanel = lazy(() => import("../ProviderSearchPanel"));

type Material = { id: number; title: string; kind: string };
type Revision = { id: number; revision_no: number; rights_status: string | null };
const SOURCES: Record<SharedAsset["source_type"], string> = { project_upload: "项目上传", system_reference: "系统素材引用", workflow: "工作流生成" };

export function ProjectAssetsTab({ projectId, onChanged, onBusy, disabled = false, readOnly: archived = false }: { projectId: number; onChanged?: () => void; onBusy?: (busy: boolean) => void; disabled?: boolean; readOnly?: boolean }) {
  const me = useQuery({ queryKey: ["project-operations-user", currentUser()], queryFn: () => api.get<{ role: string }>("/users/me"), retry: false });
  const readOnly = archived || !me.isSuccess || !["admin", "editor"].includes(me.data.role);
  const base = `/content-projects/${projectId}`;
  const [assets, setAssets] = useState<SharedAsset[]>([]);
  const [materials, setMaterials] = useState<Material[]>([]);
  const [revisions, setRevisions] = useState<Revision[]>([]);
  const [materialId, setMaterialId] = useState("");
  const [revisionId, setRevisionId] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [kind, setKind] = useState("image");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [generateOpen, setGenerateOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  async function reload() { setAssets(await api.get<SharedAsset[]>(`${base}/shared-assets`)); }
  useEffect(() => { setLoading(true); Promise.all([api.get<SharedAsset[]>(`${base}/shared-assets`), api.get<Material[]>("/materials")]).then(([nextAssets, nextMaterials]) => { setAssets(nextAssets); setMaterials(nextMaterials); }).catch((err) => setError(err instanceof ApiError ? err.message : "读取素材失败")).finally(() => setLoading(false)); }, [projectId]);
  useEffect(() => { if (!materialId) { setRevisions([]); return; } api.get<Revision[]>(`/materials/${materialId}/revisions`).then(setRevisions).catch(() => setRevisions([])); }, [materialId]);
  async function action(work: () => Promise<unknown>) { setBusy(true); onBusy?.(true); setError(""); try { await work(); onChanged?.(); await reload(); } catch (err) { setError(err instanceof Error ? err.message : "素材操作失败"); } finally { setBusy(false); onBusy?.(false); } }
  if (loading) return <Spinner label="读取项目素材…" />;
  return <section><fieldset disabled={disabled || busy} className="space-y-4"><div className="rounded-xl border border-slate-200 bg-white p-5"><h2 className="font-semibold">项目共享素材</h2><p className="mt-1 text-xs text-slate-500">项目只保存素材版本引用；权利状态与工作流来源保持可追溯。</p>{error && <div className="mt-3"><ErrorBanner message={error} /></div>}
    {assets.length ? <ul className="mt-4 space-y-2">{assets.map((asset) => <li key={asset.key || `${asset.source_type}-${asset.id}`} className="rounded-lg border p-3 text-sm"><div className="flex items-center justify-between gap-2"><p className="font-medium">{asset.title || asset.kind || "素材"} · Revision #{asset.material_revision_id}</p><span className="rounded bg-slate-100 px-2 py-1 text-xs">{SOURCES[asset.source_type] || asset.source_type}</span></div><p className="mt-1 text-xs text-slate-500">{asset.mime_type || "未知格式"} · 权利：{asset.rights_status || "待核对"} · {asset.public_use_allowed ? "允许公开" : "未获公开许可"}</p><p className="mt-1 text-xs text-slate-500">来源：{String(asset.provenance.source_kind || "待核对")}{asset.provenance.provider_key ? ` · ${String(asset.provenance.provider_key)}` : ""}</p>{asset.run_id && <p className="mt-1 text-xs text-slate-500">Run #{asset.run_id} · 节点 {asset.node_id} · Attempt #{asset.attempt_id || "?"}</p>}{asset.attribution_text && <p className="mt-1 text-xs text-slate-500">署名：{asset.attribution_text}</p>}{!readOnly && asset.reference_id && <Button className="mt-2" size="sm" variant="danger" disabled={busy} onClick={() => action(() => api.del(`${base}/materials/references/${asset.reference_id}`))}>解除项目引用</Button>}</li>)}</ul> : <div className="mt-4"><EmptyState title="项目暂无真实素材版本" /></div>}</div>
    {!readOnly && <div className="grid gap-4 md:grid-cols-2"><div className="rounded-xl border border-slate-200 bg-white p-5 space-y-3"><h3 className="font-semibold">上传到项目</h3><Field label="素材类型"><select className={inputClass} value={kind} onChange={(event) => setKind(event.target.value)}><option value="image">图片</option><option value="video">视频</option><option value="audio">音频</option><option value="other">其他文件</option></select></Field><input type="file" className={inputClass} onChange={(event) => setFile(event.target.files?.[0] || null)} /><Button disabled={!file || busy} onClick={() => action(async () => { if (!file) return; const form = new FormData(); form.append("file", file); await api.upload(`${base}/materials/upload?kind=${encodeURIComponent(kind)}&title=${encodeURIComponent(file.name)}`, form); setFile(null); })}>上传并引用</Button></div>
      <div className="rounded-xl border border-slate-200 bg-white p-5 space-y-3"><h3 className="font-semibold">引用系统素材</h3><Field label="素材"><select className={inputClass} value={materialId} onChange={(event) => { setMaterialId(event.target.value); setRevisionId(""); }}><option value="">选择素材</option>{materials.map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}</select></Field><Field label="版本"><select className={inputClass} value={revisionId} onChange={(event) => setRevisionId(event.target.value)}><option value="">选择版本</option>{revisions.map((item) => <option key={item.id} value={item.id}>#{item.id} · v{item.revision_no} · {item.rights_status || "待核对"}</option>)}</select></Field><Button disabled={!revisionId || busy} onClick={() => action(() => api.post(`${base}/materials/references`, { material_revision_id: Number(revisionId) }))}>引用版本</Button><p className="text-xs text-slate-500">也可前往 <Link to="/assets?tab=material" className="text-indigo-700">系统素材库</Link>查看完整权利信息。</p></div></div>}
    {me.isError && <ErrorBanner message="无法核对操作权限；当前仅可查看，不能修改项目素材。" />}
    {!readOnly && <div className="space-y-4 rounded-xl border bg-white p-5"><div className="flex flex-wrap gap-3"><Button variant="secondary" onClick={() => setGenerateOpen(!generateOpen)}>生成素材预览与接受</Button><Button variant="secondary" onClick={() => setSearchOpen(!searchOpen)}>公共素材搜索与导入</Button></div><p className="text-xs text-slate-500">绑定本项目的持久生成任务，接受时会同时入素材库并引用到本项目；旧临时预览只入素材库，需另行明确引用。两条路径都不自动修改 Master，仍需编辑并保存。</p>{generateOpen && <Suspense fallback={<Spinner />}><ProviderMediaPanel projectId={projectId} onAccepted={async () => { onChanged?.(); setMaterials(await api.get<Material[]>("/materials")); await reload(); }} /></Suspense>}{searchOpen && <Suspense fallback={<Spinner />}><ProviderSearchPanel /></Suspense>}</div>}
  </fieldset></section>;
}
