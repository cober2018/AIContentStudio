import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../api";
import {
  EditorContent,
  EditorToolbar,
  getMarkdown,
  loadContent,
  replaceSelection,
  selectionContext,
  useMarkdownEditor,
  type SelectionRange,
} from "../components/editor";
import { RevisionDiff } from "../components/RevisionDiff";
import { Button, EmptyState, Spinner, StatusBadge } from "../components/ui";

interface TopicDetail {
  id: number;
  title: string;
  core_thesis: string | null;
  channels: string[];
  fact_pack: { id: number; name: string; version: number; fact_count: number; checksum: string | null };
  content_jobs: {
    id: number;
    channel: string;
    status: string;
    error: string | null;
    fact_pack_snapshot: { version: number; checksum: string | null } | null;
    draft_count: number;
    latest_draft_id: number | null;
  }[];
}

interface DraftDetail {
  id: number;
  revision_no: number;
  title: string;
  body: string;
  status: string;
  channel: string;
  fact_check: { result: string; stats: { blockers: number; warnings: number }; issues: IssueRow[] } | null;
  structured: Record<string, unknown> | null;
}

interface JobDetail {
  id: number;
  drafts: { id: number; revision_no: number; title: string; status: string }[];
}

interface IssueRow {
  severity: string;
  category: string;
  span: string;
  reason: string;
  suggestion: string | null;
}

const CHANNEL_NAMES: Record<string, string> = { douyin: "抖音", xiaohongshu: "小红书", wechat: "公众号" };

function TopicPicker() {
  const navigate = useNavigate();
  const { data } = useQuery({ queryKey: ["topics"], queryFn: () => api.get<{ id: number; title: string }[]>("/topics") });
  return (
    <div className="mx-auto max-w-6xl space-y-4 p-8">
      <h1 className="text-xl font-semibold">内容任务</h1>
      {data && data.length > 0 ? (
        <div className="space-y-2">
          {data.map((t) => (
            <div
              key={t.id}
              onClick={() => navigate(`/workspace/${t.id}`)}
              className="cursor-pointer rounded-lg border border-slate-200 bg-white p-4 hover:border-indigo-300"
            >
              {t.title}
            </div>
          ))}
        </div>
      ) : (
        <EmptyState title="暂无选题" hint="先到选题中心创建" />
      )}
    </div>
  );
}

export default function Workspace() {
  const { topicId } = useParams();
  if (!topicId) return <TopicPicker />;
  return <WorkspaceInner key={topicId} topicId={Number(topicId)} />;
}

function WorkspaceInner({ topicId }: { topicId: number }) {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [activeChannel, setActiveChannel] = useState<string | null>(null);
  const [body, setBody] = useState("");
  const [dirty, setDirty] = useState(false);
  const [sel, setSel] = useState<SelectionRange | null>(null);
  const [showDiff, setShowDiff] = useState(false);
  const [rewriteInstruction, setRewriteInstruction] = useState("");
  const [message, setMessage] = useState("");

  const topicQuery = useQuery({
    queryKey: ["topic", topicId],
    queryFn: () => api.get<TopicDetail>(`/topics/${topicId}`),
  });
  const topic = topicQuery.data;

  const jobs = topic?.content_jobs || [];
  const currentJob = useMemo(
    () => jobs.find((j) => j.channel === activeChannel) || jobs[0],
    [jobs, activeChannel],
  );

  const draftQuery = useQuery({
    queryKey: ["draft", currentJob?.latest_draft_id],
    queryFn: () => api.get<DraftDetail>(`/drafts/${currentJob!.latest_draft_id}`),
    enabled: !!currentJob?.latest_draft_id,
  });
  const draft = draftQuery.data;
  const draftId = draft?.id;

  // 全部 revisions（用于「对比上一版」）
  const jobQuery = useQuery({
    queryKey: ["content-job", currentJob?.id],
    queryFn: () => api.get<JobDetail>(`/content-jobs/${currentJob!.id}`),
    enabled: !!currentJob,
  });
  const prevRevision = useMemo(() => {
    const drafts = (jobQuery.data?.drafts || []).filter((d) => d.revision_no < (draft?.revision_no ?? 0));
    return drafts.length > 0 ? drafts[drafts.length - 1] : null;
  }, [jobQuery.data, draft?.revision_no]);

  const prevDraftQuery = useQuery({
    queryKey: ["draft", prevRevision?.id],
    queryFn: () => api.get<DraftDetail>(`/drafts/${prevRevision!.id}`),
    enabled: showDiff && !!prevRevision,
  });

  const editor = useMarkdownEditor("", {
    onChange: (md) => {
      setBody(md);
      setDirty(true);
    },
    onSelectionChange: setSel,
  });

  // 切换稿件：重置编辑态
  useEffect(() => {
    setDirty(false);
    setSel(null);
    setShowDiff(false);
  }, [draftId]);
  // 未编辑时同步服务端内容到编辑器与字数
  useEffect(() => {
    if (!editor || !draft || dirty) return;
    if (getMarkdown(editor) !== draft.body) loadContent(editor, draft.body);
    setBody(draft.body);
  }, [editor, draft, dirty]);

  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ["topic", topicId] });
    if (currentJob?.latest_draft_id) {
      queryClient.invalidateQueries({ queryKey: ["draft", currentJob.latest_draft_id] });
    }
  };

  const generate = useMutation({
    mutationFn: () => api.post(`/topics/${topicId}/generate`, {}),
    onSuccess: refresh,
    onError: (e) => setMessage(e instanceof Error ? e.message : "生成失败"),
  });
  const regenerate = useMutation({
    mutationFn: () => api.post(`/content-jobs/${currentJob!.id}/regenerate`),
    onSuccess: refresh,
    onError: (e) => setMessage(e instanceof Error ? e.message : "重新生成失败"),
  });
  const factCheck = useMutation({
    mutationFn: () => api.post(`/drafts/${draft!.id}/fact-check`),
    onSuccess: refresh,
    onError: (e) => setMessage(e instanceof Error ? e.message : "FactCheck 失败"),
  });
  const save = useMutation({
    mutationFn: () => api.patch(`/drafts/${draft!.id}`, { body }),
    onSuccess: () => {
      setDirty(false);
      refresh();
      setMessage("已保存为新 revision");
    },
    onError: (e) => setMessage(e instanceof Error ? e.message : "保存失败"),
  });
  const submitReview = useMutation({
    mutationFn: () => api.post(`/drafts/${draft!.id}/submit-review`),
    onSuccess: () => {
      refresh();
      setMessage("已提交审核");
    },
    onError: (e) => setMessage(e instanceof Error ? e.message : "提交失败"),
  });
  const rewrite = useMutation({
    mutationFn: (payload: { selected_text: string; instruction: string; context_before: string; context_after: string }) =>
      api.post<{ rewritten_text: string }>(`/drafts/${draft!.id}/rewrite-selection`, payload),
    onSuccess: (result) => {
      // 按记录的位置精确替换选区；onChange 回调自动更新 body 并置 dirty
      if (editor && sel) replaceSelection(editor, sel, result.rewritten_text);
      setSel(null);
      setRewriteInstruction("");
    },
    onError: (e) => setMessage(e instanceof Error ? e.message : "改写失败"),
  });

  if (topicQuery.isLoading) return <Spinner />;
  if (!topic) return <EmptyState title="选题不存在" action={<Button onClick={() => navigate("/topics")}>返回选题中心</Button>} />;

  const factCheckStats = draft?.fact_check?.stats;
  const citations = extractCitations(draft?.structured ?? null);

  return (
    <div className="flex h-screen flex-col">
      {/* 顶栏 */}
      <div className="flex flex-wrap items-center gap-3 border-b border-slate-200 bg-white px-6 py-3">
        <Button variant="ghost" size="sm" onClick={() => navigate("/workspace")}>
          ←
        </Button>
        <div className="min-w-0">
          <div className="truncate text-sm font-semibold">{topic.title}</div>
          <div className="text-xs text-slate-400">
            FactPack {topic.fact_pack.name} v{topic.fact_pack.version}（{topic.fact_pack.fact_count} 条）
          </div>
        </div>
        <div className="ml-auto flex items-center gap-2">
          {jobs.length < topic.channels.length && (
            <Button variant="secondary" onClick={() => generate.mutate()} disabled={generate.isPending}>
              {generate.isPending ? "生成中…" : `生成全部（${topic.channels.length} 渠道）`}
            </Button>
          )}
          {jobs.length > 0 && (
            <Button variant="secondary" onClick={() => generate.mutate()} disabled={generate.isPending}>
              追加生成
            </Button>
          )}
        </div>
      </div>

      {message && (
        <div className="flex items-center justify-between bg-amber-50 px-6 py-2 text-sm text-amber-800">
          {message}
          <button onClick={() => setMessage("")}>✕</button>
        </div>
      )}

      <div className="grid min-h-0 flex-1 grid-cols-[180px_1fr_320px]">
        {/* 左：渠道 */}
        <div className="border-r border-slate-200 bg-white py-3">
          <div className="px-4 pb-2 text-xs font-medium text-slate-400">渠道</div>
          {topic.channels.map((channel) => {
            const job = jobs.find((j) => j.channel === channel);
            const isActive = (activeChannel || jobs[0]?.channel) === channel;
            return (
              <button
                key={channel}
                onClick={() => setActiveChannel(channel)}
                className={`flex w-full items-center justify-between px-4 py-2.5 text-left text-sm ${
                  isActive ? "bg-indigo-50 font-medium text-indigo-700" : "text-slate-600 hover:bg-slate-50"
                }`}
              >
                <span>{CHANNEL_NAMES[channel]}</span>
                {job ? <StatusBadge status={job.status} /> : <span className="text-xs text-slate-300">未生成</span>}
              </button>
            );
          })}
        </div>

        {/* 中：编辑器 */}
        <div className="flex min-w-0 flex-col">
          {draftQuery.isLoading && <Spinner label="加载稿件…" />}
          {!currentJob ? (
            <EmptyState title="该渠道尚未生成" action={<Button onClick={() => generate.mutate()}>生成</Button>} />
          ) : !draft ? (
            <EmptyState
              title={currentJob.status === "failed" ? `生成失败：${currentJob.error}` : "暂无稿件"}
              action={
                <Button onClick={() => regenerate.mutate()} disabled={regenerate.isPending}>
                  {regenerate.isPending ? "生成中…" : "生成"}
                </Button>
              }
            />
          ) : (
            <>
              <div className="flex items-center gap-2 border-b border-slate-100 bg-white px-4 py-2 text-xs text-slate-500">
                <span className="font-medium text-slate-700">{draft.title}</span>
                <StatusBadge status={draft.status} />
                <span>r{draft.revision_no}</span>
                <span>{body.length} 字</span>
                {dirty && <span className="text-amber-600">未保存</span>}
                <div className="ml-auto flex gap-2">
                  {prevRevision && (
                    <Button
                      size="sm"
                      variant={showDiff ? "primary" : "secondary"}
                      onClick={() => setShowDiff((v) => !v)}
                    >
                      {showDiff ? "退出对比" : `对比上一版（r${prevRevision.revision_no}）`}
                    </Button>
                  )}
                  <Button size="sm" variant="secondary" onClick={() => regenerate.mutate()} disabled={regenerate.isPending}>
                    重新生成
                  </Button>
                  <Button size="sm" variant="secondary" onClick={() => save.mutate()} disabled={!dirty || save.isPending}>
                    保存（新 revision）
                  </Button>
                  <Button
                    size="sm"
                    onClick={() => submitReview.mutate()}
                    disabled={submitReview.isPending || draft.status !== "draft"}
                  >
                    进入审核
                  </Button>
                </div>
              </div>
              {showDiff && prevDraftQuery.data ? (
                <RevisionDiff
                  oldBody={prevDraftQuery.data.body}
                  newBody={body}
                  oldLabel={`r${prevRevision!.revision_no}`}
                  newLabel={`r${draft.revision_no}（当前）`}
                />
              ) : showDiff && prevDraftQuery.isLoading ? (
                <Spinner label="加载上一版…" />
              ) : (
                <>
                  <EditorToolbar editor={editor!} />
                  <div className="min-h-0 flex-1 overflow-y-auto">
                    <div className="mx-auto max-w-3xl px-6 py-4">
                      <EditorContent editor={editor!} />
                    </div>
                  </div>
                  {sel && sel.text.length > 4 && (
                    <div className="flex items-center gap-2 border-t border-slate-100 bg-white px-4 py-2">
                      <span className="max-w-[200px] truncate text-xs text-slate-500">选中：{sel.text}</span>
                      <input
                        className="flex-1 rounded border border-slate-300 px-2 py-1 text-xs"
                        placeholder="改写要求，如：更口语化"
                        value={rewriteInstruction}
                        onChange={(e) => setRewriteInstruction(e.target.value)}
                      />
                      <Button
                        size="sm"
                        variant="secondary"
                        disabled={!rewriteInstruction || rewrite.isPending}
                        onClick={() => {
                          if (!editor || !sel) return;
                          rewrite.mutate({
                            selected_text: sel.text,
                            instruction: rewriteInstruction,
                            ...selectionContext(editor, sel),
                          });
                        }}
                      >
                        AI 改写选中
                      </Button>
                    </div>
                  )}
                </>
              )}
            </>
          )}
        </div>

        {/* 右：引用与检查 */}
        <div className="overflow-y-auto border-l border-slate-200 bg-white p-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium">Fact / Citations</h3>
            {draft && (
              <Button size="sm" variant="secondary" onClick={() => factCheck.mutate()} disabled={factCheck.isPending}>
                {factCheck.isPending ? "检查中…" : "FactCheck"}
              </Button>
            )}
          </div>

          {draft?.fact_check ? (
            <div className="mt-3 space-y-3">
              <div className="flex items-center gap-2 text-xs">
                <StatusBadge status={draft.fact_check.result} />
                <span className="text-slate-500">
                  blocker {factCheckStats?.blockers ?? 0} · warning {factCheckStats?.warnings ?? 0}
                </span>
              </div>
              {(draft.fact_check.issues || []).map((issue, i) => (
                <div
                  key={i}
                  className={`rounded-md border p-2.5 text-xs ${
                    issue.severity === "blocker" ? "border-rose-200 bg-rose-50" : "border-amber-200 bg-amber-50"
                  }`}
                >
                  <div className="flex items-center gap-1.5 font-medium">
                    <span className={issue.severity === "blocker" ? "text-rose-700" : "text-amber-700"}>
                      [{issue.severity}/{issue.category}]
                    </span>
                  </div>
                  <div className="mt-1 text-slate-700">{issue.reason}</div>
                  <div className="mt-1 text-slate-500">位置：{issue.span}</div>
                  {issue.suggestion && <div className="mt-1 text-slate-500">建议：{issue.suggestion}</div>}
                </div>
              ))}
            </div>
          ) : (
            <p className="mt-3 text-xs text-slate-400">尚未执行 FactCheck</p>
          )}

          <h3 className="mt-6 text-sm font-medium">引用的事实</h3>
          <div className="mt-2 space-y-1.5">
            {citations.length === 0 ? (
              <p className="text-xs text-slate-400">无</p>
            ) : (
              citations.map((c, i) => (
                <div key={i} className="rounded border border-slate-100 p-2 text-xs">
                  <div className="font-mono text-indigo-600">{c.factIds.join(", ")}</div>
                  <div className="mt-0.5 line-clamp-2 text-slate-600">{c.text}</div>
                </div>
              ))
            )}
          </div>

          {currentJob?.fact_pack_snapshot && (
            <div className="mt-6 rounded-md bg-slate-50 p-3 text-[11px] text-slate-500">
              生成时快照：FactPack v{currentJob.fact_pack_snapshot.version}
              <br />
              checksum {currentJob.fact_pack_snapshot.checksum?.slice(0, 16)}…
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function extractCitations(structured: Record<string, unknown> | null): { factIds: string[]; text: string }[] {
  if (!structured) return [];
  const result: { factIds: string[]; text: string }[] = [];
  const claimMap = structured["claim_fact_map"];
  if (Array.isArray(claimMap)) {
    for (const claim of claimMap) {
      if (claim && typeof claim === "object") {
        const c = claim as { text?: string; fact_ids?: string[] };
        if (c.fact_ids?.length) result.push({ factIds: c.fact_ids, text: c.text || "" });
      }
    }
  }
  const scenes = structured["scenes"];
  if (Array.isArray(scenes)) {
    for (const scene of scenes) {
      if (scene && typeof scene === "object") {
        const s = scene as { script?: string; fact_ids?: string[] };
        if (s.fact_ids?.length) result.push({ factIds: s.fact_ids, text: s.script || "" });
      }
    }
  }
  return result;
}
