import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";
import { api, currentUser } from "../api";
import { Button, ErrorBanner } from "../components/ui";

type Launch = { status: string; reason: string | null; href: string };
export function ProductLaunchPanel({ projectId, readOnly }: { projectId: number; readOnly: boolean }) {
  const user = currentUser(), client = useQueryClient(), navigate = useNavigate();
  const me = useQuery({ queryKey: ["product-launch-user", user], queryFn: () => api.get<{ role: string }>("/users/me") });
  const editable = !readOnly && !!me.data && ["admin", "editor"].includes(me.data.role);
  const research = useMutation({ mutationFn: () => api.post<{ results: { url: string; title: string; snippet: string }[] }>(`/content-projects/${projectId}/product-research`) });
  const query = useQuery({ queryKey: ["product-launch", user, projectId], queryFn: () => api.get<Launch | null>(`/content-projects/${projectId}/product-launch`) });
  const resume = useMutation({ mutationFn: () => api.post<Launch>(`/content-projects/${projectId}/product-launch/resume`),
    onSuccess: async result => { await client.invalidateQueries({ queryKey: ["product-launch", user, projectId] }); if (result.status === "started") navigate(result.href); } });
  if (query.isError) return <ErrorBanner message="商品创作状态读取失败，请刷新后核对。" />;
  if (!query.data) return null;
  const launch = query.data;
  const reason = launch.reason === "workflow_required" ? "请为商品作品绑定商品创作流程" : launch.reason === "product_information_required" ? "请补充商品说明或在来源与证据中添加资料，并保存新的任务书版本" : launch.reason === "product_evidence_confirmation_required" ? "请在来源与证据中确认并冻结商品事实，绑定后继续" : launch.reason === "product_source_unreadable" ? "商品资料未能解析，请重新上传或填写说明" : launch.reason === "product_evidence_unavailable" ? "商品资料或素材版本不可用，请重新选择" : launch.reason;
  return <section className="space-y-3 rounded-xl border bg-white p-4"><h2 className="font-medium">商品创作</h2><p className="text-sm text-slate-600">{launch.status === "started" ? "已进入共同创作流程" : launch.status === "unknown" ? "结果待核对，请在生产页查看回执" : "输入已保存，补齐后可继续"}{reason ? ` · ${reason}` : ""}</p><div className="flex flex-wrap gap-2"><Link className="text-sm text-indigo-700" to={`/projects/${projectId}?tab=evidence`}>来源与证据</Link><Link className="text-sm text-indigo-700" to={`/projects/${projectId}?tab=assets`}>商品素材</Link><Link className="text-sm text-indigo-700" to={launch.href}>进入生产</Link>{editable && <Button variant="secondary" disabled={research.isPending} onClick={() => research.mutate()}>{research.isPending ? "正在查找…" : "补充公开商品资料"}</Button>}{editable && !["started", "unknown"].includes(launch.status) && <Button variant="secondary" disabled={resume.isPending} onClick={() => resume.mutate()}>{resume.isPending ? "正在开始…" : "保存任务书后继续创作"}</Button>}</div>{research.data && <ul className="space-y-2 text-sm">{research.data.results.map(r => <li key={r.url}><a href={r.url} target="_blank" rel="noopener noreferrer" className="text-indigo-700">{r.title}</a><p className="text-xs text-slate-500">{r.snippet.slice(0, 250)}</p></li>)}</ul>}{research.error && <ErrorBanner message={research.error instanceof Error ? research.error.message : "检索失败；已有商品资料仍可用于创作"} />}{resume.error && <ErrorBanner message={resume.error instanceof Error ? resume.error.message : "启动失败"} />}</section>;
}
