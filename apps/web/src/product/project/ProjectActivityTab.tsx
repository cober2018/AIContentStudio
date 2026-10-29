import { useEffect, useState } from "react";
import { api, ApiError } from "../../api";
import { Button, EmptyState, ErrorBanner, Spinner } from "../../components/ui";
import type { Activity } from "./types";

type Page = { items: Activity[]; next_before_id: number | null };
const LABELS: Record<string, string> = {
  "project.created": "创建项目", "project.updated": "更新项目", "project.archived": "归档项目",
  "brief.revision_created": "保存任务书版本", "source.attached": "引用来源", "source.detached": "解除来源引用",
  "fact_boundary.bound": "绑定事实边界", "fact_boundary.draft_cloned": "克隆事实草稿", "fact_boundary.frozen_bound": "冻结并更新事实边界",
  "unit.created": "创建作品", "unit.updated": "更新作品", "unit.replaced": "替换作品", "unit.archived": "归档作品", "unit.deleted": "删除无历史作品",
  "workflow.override_saved": "保存项目工作流", "workflow.role_default_saved": "另存角色默认工作流",
  "data.snapshot_created": "创建数据快照", "data.snapshot_changed": "刷新数据快照",
  "asset.attached": "关联项目素材", "asset.detached": "解除项目素材引用", "asset.workflow_generated": "生成工作流素材",
  "draft.generated": "生成草稿", "candidate.associated": "关联候选成品",
};

export function ProjectActivityTab({ projectId }: { projectId: number }) {
  const [items, setItems] = useState<Activity[]>([]);
  const [cursor, setCursor] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function load(before?: number) { const page = await api.get<Page>(`/content-projects/${projectId}/activity?limit=30${before ? `&before_id=${before}` : ""}`); setItems((previous) => before ? [...previous, ...page.items] : page.items); setCursor(page.next_before_id); }
  useEffect(() => { setLoading(true); load().catch((err) => setError(err instanceof ApiError ? err.message : "活动读取失败")).finally(() => setLoading(false)); }, [projectId]);
  if (error) return <ErrorBanner message={error} />;
  if (loading) return <Spinner label="读取项目活动…" />;
  return <section className="rounded-xl border border-slate-200 bg-white p-6"><h2 className="font-semibold">项目活动</h2>{items.length ? <ol className="mt-4 space-y-2">{items.map((item) => <li key={item.id} className="rounded-lg border p-3 text-sm"><p className="font-medium">{LABELS[item.event_type] || item.event_type}</p><p className="mt-1 text-xs text-slate-500">{item.created_at || "时间未知"}{item.actor ? ` · ${item.actor}` : ""}{item.entity_id ? ` · ${item.entity_type || "资源"} #${item.entity_id}` : ""}</p></li>)}</ol> : <div className="mt-4"><EmptyState title="暂无项目活动" /></div>}{cursor && <Button className="mt-4" variant="secondary" disabled={busy} onClick={async () => { setBusy(true); try { await load(cursor); } catch (err) { setError(err instanceof Error ? err.message : "加载失败"); } finally { setBusy(false); } }}>加载更多</Button>}</section>;
}
