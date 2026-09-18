import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../api";
import { Button, ChannelBadge, EmptyState, Spinner, StatusBadge } from "../components/ui";

interface QueueItem {
  draft_id: number;
  revision_no: number;
  title: string;
  topic_title: string;
  channel: string;
  status: string;
  submitter: string | null;
  fact_check_result: string | null;
  fact_check_stats: { blockers: number; warnings: number } | null;
  fact_check_issues:
    | { severity: string; category: string; span: string; reason: string; suggestion: string | null }[]
    | null;
  reviewer: string | null;
}

interface DraftDetail {
  id: number;
  title: string;
  body: string;
  revision_no: number;
  status: string;
}

export default function Review() {
  const queryClient = useQueryClient();
  const [activeId, setActiveId] = useState<number | null>(null);
  const [comment, setComment] = useState("");
  const [message, setMessage] = useState("");
  const [tab, setTab] = useState<"queue" | "history">("queue");

  const queueQuery = useQuery({
    queryKey: ["reviews", tab],
    queryFn: () => api.get<QueueItem[]>(`/reviews/${tab === "queue" ? "queue" : "history"}`),
    refetchInterval: 15000,
  });

  const draftQuery = useQuery({
    queryKey: ["review-draft", activeId],
    queryFn: () => api.get<DraftDetail>(`/drafts/${activeId}`),
    enabled: !!activeId,
  });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["reviews"] });
    queryClient.invalidateQueries({ queryKey: ["review-draft", activeId] });
  };

  const approve = useMutation({
    mutationFn: () => api.post(`/reviews/drafts/${activeId}/approve`, comment ? { comment } : {}),
    onSuccess: () => {
      invalidate();
      setMessage("已批准，资产已生成");
      setComment("");
    },
    onError: (e) => setMessage(e instanceof Error ? e.message : "批准失败"),
  });
  const requestChanges = useMutation({
    mutationFn: () => api.post(`/reviews/drafts/${activeId}/request-changes`, { comment }),
    onSuccess: () => {
      invalidate();
      setMessage("已退回修改");
      setComment("");
    },
    onError: (e) => setMessage(e instanceof Error ? e.message : "退回失败"),
  });

  const items = queueQuery.data || [];
  const active = items.find((i) => i.draft_id === activeId);

  return (
    <div className="flex h-screen">
      <div className="flex w-[420px] shrink-0 flex-col border-r border-slate-200 bg-white">
        <div className="border-b border-slate-100 px-5 py-4">
          <h1 className="text-lg font-semibold">审核中心</h1>
          <div className="mt-2 flex gap-1 rounded-md bg-slate-100 p-0.5 text-sm">
            {(
              [
                ["queue", "待审核"],
                ["history", "已批准"],
              ] as const
            ).map(([key, label]) => (
              <button
                key={key}
                onClick={() => setTab(key)}
                className={`flex-1 rounded px-3 py-1 ${tab === key ? "bg-white font-medium shadow-sm" : "text-slate-500"}`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto">
          {queueQuery.isLoading ? (
            <Spinner />
          ) : items.length === 0 ? (
            <div className="p-5 text-sm text-slate-400">{tab === "queue" ? "队列为空" : "暂无记录"}</div>
          ) : (
            items.map((item) => (
              <button
                key={item.draft_id}
                onClick={() => setActiveId(item.draft_id)}
                className={`block w-full border-b border-slate-50 px-5 py-3 text-left hover:bg-slate-50 ${
                  activeId === item.draft_id ? "bg-gray-100/60" : ""
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="truncate text-sm font-medium">{item.title}</span>
                  <StatusBadge status={item.status} />
                </div>
                <div className="mt-1 flex items-center gap-2 text-xs text-slate-400">
                  <ChannelBadge channel={item.channel} />
                  <span>{item.topic_title}</span>
                  <span>r{item.revision_no}</span>
                </div>
              </button>
            ))
          )}
        </div>
      </div>

      <div className="min-w-0 flex-1 overflow-y-auto p-6">
        {!activeId || !active ? (
          <EmptyState title="选择左侧稿件进行审核" />
        ) : (
          <div className="grid grid-cols-[1fr_340px] gap-6">
            <div>
              <div className="mb-3 flex items-center gap-2">
                <h2 className="text-base font-semibold">{active.title}</h2>
                <StatusBadge status={active.status} />
              </div>
              {draftQuery.isLoading ? (
                <Spinner />
              ) : (
                <pre className="whitespace-pre-wrap rounded-lg border border-slate-200 bg-white p-5 font-mono text-sm leading-relaxed">
                  {draftQuery.data?.body}
                </pre>
              )}
            </div>

            <div className="space-y-4">
              <div className="rounded-lg border border-slate-200 bg-white p-4">
                <h3 className="mb-2 flex items-center justify-between text-sm font-medium">
                  检查结果
                  {active.fact_check_result && <StatusBadge status={active.fact_check_result} />}
                </h3>
                {active.fact_check_stats && (
                  <div className="text-xs text-slate-500">
                    blocker {active.fact_check_stats.blockers} · warning {active.fact_check_stats.warnings}
                  </div>
                )}
                <div className="mt-2 space-y-2">
                  {(active.fact_check_issues || []).map((issue, i) => (
                    <div
                      key={i}
                      className={`rounded p-2 text-xs ${
                        issue.severity === "blocker" ? "bg-rose-50 text-rose-700" : "bg-amber-50 text-amber-700"
                      }`}
                    >
                      [{issue.category}] {issue.reason}
                      <div className="mt-1 opacity-70">位置：{issue.span}</div>
                      {issue.suggestion && <div className="mt-0.5 opacity-70">建议：{issue.suggestion}</div>}
                    </div>
                  ))}
                  {(!active.fact_check_issues || active.fact_check_issues.length === 0) && (
                    <p className="text-xs text-slate-400">无问题</p>
                  )}
                </div>
              </div>

              {message && <div className="rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-800">{message}</div>}

              {tab === "queue" && (
                <div className="space-y-2 rounded-lg border border-slate-200 bg-white p-4">
                  <textarea
                    className="w-full rounded border border-slate-300 p-2 text-sm"
                    rows={3}
                    placeholder="审核意见（退回时必填）"
                    value={comment}
                    onChange={(e) => setComment(e.target.value)}
                  />
                  <div className="flex gap-2">
                    <Button
                      variant="danger"
                      onClick={() => requestChanges.mutate()}
                      disabled={requestChanges.isPending || !comment}
                    >
                      退回修改
                    </Button>
                    <Button
                      onClick={() => approve.mutate()}
                      disabled={approve.isPending || active.fact_check_result === "blocker"}
                    >
                      批准
                    </Button>
                  </div>
                  {active.fact_check_result === "blocker" && (
                    <p className="text-xs text-rose-600">存在 blocker，未解决不能批准</p>
                  )}
                </div>
              )}

              <div className="rounded-lg border border-slate-200 bg-white p-4 text-xs text-slate-500">
                <div>提交人：{active.submitter || "-"}</div>
                <div>审核人：{active.reviewer || "-"}</div>
                <div>revision：r{active.revision_no}</div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
