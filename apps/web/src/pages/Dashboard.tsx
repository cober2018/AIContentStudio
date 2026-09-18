import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../api";
import { ChannelBadge, EmptyState, Spinner, StatusBadge } from "../components/ui";

interface DashboardData {
  stats: {
    week_drafts: number;
    pending_review: number;
    fact_conflicts: number;
    exported_count: number;
    topics: number;
    assets: number;
  };
  today_flow: {
    job_id: number;
    topic_id: number;
    topic_title: string;
    channel: string;
    status: string;
    draft_status: string | null;
    updated_at: string | null;
  }[];
  recent_fact_packs: { id: number; name: string; version: number; status: string; fact_count: number }[];
  recent_exports: { id: number; asset_id: number; fmt: string; created_at: string }[];
  failed_jobs: { id: number; topic: string; channel: string; error: string | null }[];
}

function StatCard({ label, value, warn }: { label: string; value: number; warn?: boolean }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <div className="text-xs text-slate-500">{label}</div>
      <div className={`mt-1 text-2xl font-semibold ${warn && value > 0 ? "text-rose-600" : "text-slate-900"}`}>
        {value}
      </div>
    </div>
  );
}

export default function Dashboard() {
  const { data, isLoading } = useQuery({
    queryKey: ["dashboard"],
    queryFn: () => api.get<DashboardData>("/dashboard"),
    refetchInterval: 10000,
  });

  if (isLoading) return <Spinner />;
  if (!data) return <EmptyState title="无法加载总览数据" />;

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-8">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">总览</h1>
        <div className="flex gap-2">
          <Link
            to="/topics"
            className="rounded-md bg-gray-900 px-3.5 py-1.5 text-sm font-medium text-white hover:bg-black"
          >
            新建选题
          </Link>
          <Link
            to="/sources"
            className="rounded-md border border-slate-300 bg-white px-3.5 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            导入来源
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <StatCard label="本周内容" value={data.stats.week_drafts} />
        <StatCard label="待审核" value={data.stats.pending_review} />
        <StatCard label="Fact 异常" value={data.stats.fact_conflicts} warn />
        <StatCard label="已导出" value={data.stats.exported_count} />
      </div>

      <div className="rounded-lg border border-slate-200 bg-white">
        <div className="border-b border-slate-100 px-5 py-3 text-sm font-medium">今日工作流</div>
        {data.today_flow.length === 0 ? (
          <div className="px-5 py-10 text-center text-sm text-slate-400">
            暂无内容任务，先到 <Link to="/sources" className="text-gray-900">来源库</Link> 导入数据
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100 text-left text-xs text-slate-400">
                <th className="px-5 py-2 font-medium">选题</th>
                <th className="px-5 py-2 font-medium">渠道</th>
                <th className="px-5 py-2 font-medium">状态</th>
                <th className="px-5 py-2 font-medium">最后更新</th>
              </tr>
            </thead>
            <tbody>
              {data.today_flow.map((row) => (
                <tr key={row.job_id} className="border-b border-slate-50 last:border-0">
                  <td className="px-5 py-2.5">
                    <Link to={`/workspace/${row.topic_id}`} className="text-gray-900 hover:underline">
                      {row.topic_title}
                    </Link>
                  </td>
                  <td className="px-5 py-2.5">
                    <ChannelBadge channel={row.channel} />
                  </td>
                  <td className="px-5 py-2.5">
                    <StatusBadge status={row.draft_status || row.status} />
                  </td>
                  <td className="px-5 py-2.5 text-slate-500">
                    {row.updated_at ? new Date(row.updated_at).toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" }) : "-"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="rounded-lg border border-slate-200 bg-white p-4">
          <div className="mb-2 text-sm font-medium">最近 FactPack</div>
          {data.recent_fact_packs.length === 0 ? (
            <div className="text-xs text-slate-400">暂无</div>
          ) : (
            data.recent_fact_packs.map((p) => (
              <div key={p.id} className="flex items-center justify-between py-1.5 text-sm">
                <Link to={`/fact-packs/${p.id}`} className="truncate text-slate-700 hover:text-gray-900">
                  {p.name} v{p.version}
                </Link>
                <StatusBadge status={p.status} />
              </div>
            ))
          )}
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-4">
          <div className="mb-2 text-sm font-medium">最近导出</div>
          {data.recent_exports.length === 0 ? (
            <div className="text-xs text-slate-400">暂无</div>
          ) : (
            data.recent_exports.map((e) => (
              <div key={e.id} className="py-1.5 text-sm text-slate-600">
                Asset #{e.asset_id} · {e.fmt.toUpperCase()}
              </div>
            ))
          )}
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-4">
          <div className="mb-2 text-sm font-medium">失败任务</div>
          {data.failed_jobs.length === 0 ? (
            <div className="text-xs text-slate-400">无失败任务</div>
          ) : (
            data.failed_jobs.map((j) => (
              <div key={j.id} className="py-1.5 text-sm text-rose-600" title={j.error || ""}>
                {j.topic} · {j.channel}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
