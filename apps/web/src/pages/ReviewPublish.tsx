import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api";
import { Button, EmptyState, Spinner, StatusBadge, inputClass } from "../components/ui";

// 审核与发布中心（V1 PRD 2.0 / unified-review-publish-center）
// projection：聚合每个目标（channel × content_form）的 draft/checks/SEO/媒体/candidate/delivery。

interface CheckRow {
  kind: string;
  status: string;
  profile: string | null;
}

interface DiscoReport {
  id: number;
  status: string;
  report: { title_suggestions?: string[]; issues?: unknown[] };
}

interface TargetView {
  channel: string;
  content_form: string | null;
  form_label: string | null;
  artifact_kind: string | null;
  workflow_run: { id: number | null; status: string; workflow_key: string | null; workflow_version: number | null; error: string | null };
  draft: { id: number; revision_no: number; title: string; status: string; candidate_readiness: string | null; artifact_kind: string | null } | null;
  checks: CheckRow[];
  discoverability: DiscoReport | null;
  materials: { draft_media_id: number; role: string; sort_order: number; material_revision_id: number | null; public_use_allowed: boolean | null; alt_text: string | null; caption: string | null }[];
  candidate: { asset_id: number; approved_candidate_hash: string; manifest_schema: number; approved_revision: number; reviewer: string | null } | null;
  delivery: { id: number; action: string; account_ref: string; status: string; publisher_key: string | null; capability: { verified?: boolean; available?: boolean; reason?: string } | null }[];
  readiness: { content: string; evidence: string; media: string; platform: string; delivery: string };
}

interface CenterData {
  topic: { id: number; title: string; status: string; fact_pack: { name: string; version: number; status: string; fact_count: number } };
  targets: TargetView[];
}

interface DocumentData {
  document: { blocks: { id: string; type: string; text?: string; alt?: string; caption?: string }[] };
}

const READINESS_LABEL: Record<string, string> = {
  ready: "就绪", in_progress: "进行中", incomplete: "未完成", missing: "缺稿",
  blocked: "受阻", none: "无素材", delivered: "已交付", authorized: "已授权",
  not_authorized: "未授权", awaiting_approval: "待批准",
};

function ReadinessChips({ readiness }: { readiness: TargetView["readiness"] }) {
  return (
    <div className="flex flex-wrap gap-1">
      {Object.entries(readiness).map(([k, v]) => (
        <span
          key={k}
          className={`rounded px-1.5 py-0.5 text-[10px] ${
            v === "ready" || v === "delivered"
              ? "bg-emerald-50 text-emerald-700"
              : v === "blocked"
                ? "bg-rose-50 text-rose-700"
                : v === "ready_ok" ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"
          }`}
        >
          {k}: {READINESS_LABEL[v] || v}
        </span>
      ))}
    </div>
  );
}

function TargetPane({ target, onSelect, selected }: { target: TargetView; onSelect: () => void; selected: boolean }) {
  return (
    <button
      onClick={onSelect}
      className={`w-full rounded-lg border p-3 text-left ${
        selected ? "border-gray-900 bg-gray-50" : "border-slate-200 bg-white hover:border-gray-400"
      }`}
    >
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-slate-800">
          {target.channel}
          {target.content_form ? ` · ${target.form_label || target.content_form}` : ""}
        </span>
        <StatusBadge status={target.draft?.status || "draft"} />
      </div>
      <div className="mt-1 truncate text-xs text-slate-500">{target.draft?.title || "尚未生成稿件"}</div>
      <div className="mt-2">
        <ReadinessChips readiness={target.readiness} />
      </div>
      <div className="mt-1.5 text-[10px] text-slate-400">
        Run: {target.workflow_run.status}
        {target.workflow_run.workflow_key ? ` · ${target.workflow_run.workflow_key} v${target.workflow_run.workflow_version ?? "-"}` : ""}
      </div>
    </button>
  );
}

function CenterPreview({ target }: { target: TargetView }) {
  const { data: doc } = useQuery({
    queryKey: ["draft-document", target.draft?.id],
    queryFn: () => api.get<DocumentData>(`/drafts/${target.draft?.id}/document`),
    enabled: !!target.draft,
  });
  if (!target.draft) return <EmptyState title="该目标还没有稿件" hint="在工作台或工作流中生成" />;
  const blocks = doc?.document?.blocks || [];
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-base font-semibold text-slate-800">{target.draft.title}</h3>
        <span className="text-xs text-slate-400">
          rev{target.draft.revision_no} · {target.artifact_kind || "text"}
        </span>
      </div>
      <div className="max-h-[42vh] space-y-2 overflow-y-auto rounded-lg border border-slate-200 bg-white p-4 text-sm leading-relaxed text-slate-700">
        {blocks.length === 0 && <p className="text-xs text-slate-400">（无 document，正文见工作台）</p>}
        {blocks.map((b) =>
          b.type === "image" ? (
            <div key={b.id} className="rounded border border-dashed border-slate-300 bg-slate-50 px-3 py-2 text-xs text-slate-500">
              🖼 {b.alt || b.caption || "图片位"}（placement 已入 candidate manifest）
            </div>
          ) : (
            <p key={b.id} className="whitespace-pre-wrap">{b.text}</p>
          ),
        )}
      </div>
      {target.materials.length > 0 && (
        <div className="rounded-lg border border-slate-200 bg-white p-3">
          <h4 className="mb-1 text-xs font-medium text-slate-500">素材（按序）</h4>
          {target.materials
            .slice()
            .sort((a, b) => a.sort_order - b.sort_order)
            .map((m) => (
              <div key={m.draft_media_id} className="flex items-center justify-between py-0.5 text-xs text-slate-600">
                <span>
                  #{m.sort_order} {m.role} · rev {m.material_revision_id ?? "legacy"}
                </span>
                <span>{m.public_use_allowed ? "公开✅" : "未公开⛔"}</span>
              </div>
            ))}
        </div>
      )}
    </div>
  );
}

function RightPane({ data, target }: { data: CenterData; target: TargetView }) {
  const queryClient = useQueryClient();
  const [msg, setMsg] = useState("");
  const draftId = target.draft?.id;

  const { data: discoReports } = useQuery({
    queryKey: ["disco", draftId],
    queryFn: () => api.get<DiscoReport[]>(`/drafts/${draftId}/discoverability`),
    enabled: !!draftId,
  });

  const runSeo = useMutation({
    mutationFn: () => api.post(`/drafts/${draftId}/discoverability/post`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["disco", draftId] });
      queryClient.invalidateQueries({ queryKey: ["review-center", data.topic.id] });
    },
    onError: (e) => setMsg(e instanceof Error ? e.message : "SEO 报告失败"),
  });
  const runPlatformCheck = useMutation({
    mutationFn: () => api.post(`/drafts/${draftId}/checks/platform`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["review-center", data.topic.id] }),
  });
  const execute = useMutation({
    mutationFn: (tid: number) => api.post(`/delivery-targets/${tid}/execute`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["review-center", data.topic.id] });
    },
    onError: (e) => setMsg(e instanceof Error ? e.message : "执行失败"),
  });

  return (
    <div className="space-y-3 text-xs">
      <div className="rounded-lg border border-slate-200 bg-white p-3">
        <h4 className="mb-1.5 font-medium text-slate-500">检查（DraftCheckRun）</h4>
        {target.checks.length === 0 && <p className="text-slate-400">未运行（批准时自动补跑确定性检查）</p>}
        {target.checks.map((c, i) => (
          <div key={i} className="flex items-center justify-between py-0.5">
            <span>{c.kind}</span>
            <StatusBadge status={c.status === "pass" ? "approved" : c.status === "blocker" ? "changes_requested" : "draft"} />
          </div>
        ))}
        {draftId && (
          <Button size="sm" variant="secondary" className="mt-2" disabled={runPlatformCheck.isPending} onClick={() => runPlatformCheck.mutate()}>
            运行平台规则
          </Button>
        )}
      </div>

      <div className="rounded-lg border border-slate-200 bg-white p-3">
        <h4 className="mb-1.5 font-medium text-slate-500">Discoverability（SEO 报告独立于写作）</h4>
        {(discoReports || []).length === 0 && <p className="text-slate-400">暂无报告</p>}
        {(discoReports || []).slice(0, 1).map((r) => (
          <div key={r.id} className="space-y-1">
            <div>
              状态：<StatusBadge status={r.status === "ready" ? "approved" : "draft"} />（incomplete 不是 pass）
            </div>
            {(r.report.title_suggestions || []).slice(0, 3).map((t, i) => (
              <div key={i} className="flex items-center justify-between gap-2 rounded bg-slate-50 px-2 py-1">
                <span className="truncate">{t}</span>
                <ApplyTitle draftId={draftId} reportId={r.id} index={i} onDone={() => queryClient.invalidateQueries({ queryKey: ["review-center", data.topic.id] })} />
              </div>
            ))}
          </div>
        ))}
        {draftId && (
          <Button size="sm" variant="secondary" className="mt-2" disabled={runSeo.isPending} onClick={() => runSeo.mutate()}>
            {runSeo.isPending ? "生成中…" : "生成 Post SEO 报告"}
          </Button>
        )}
      </div>

      <div className="rounded-lg border border-slate-200 bg-white p-3">
        <h4 className="mb-1.5 font-medium text-slate-500">交付（Delivery Router）</h4>
        {target.delivery.length === 0 && (
          <p className="text-slate-400">
            未授权。候选批准后可在资产页授权目标（copy_package 为通用兜底；未验证平台不显示 auto_publish）。
          </p>
        )}
        {target.delivery.map((d) => (
          <div key={d.id} className="space-y-1 rounded border border-slate-100 p-2">
            <div className="flex items-center justify-between">
              <span>
                {d.account_ref} · {d.action}
              </span>
              <StatusBadge status={d.status === "human_confirmed" ? "approved" : d.status === "failed" ? "changes_requested" : "draft"} />
            </div>
            <div className="text-[10px] text-slate-400">
              {d.publisher_key}
              {d.capability?.verified === false && <span className="ml-1 text-amber-600">unverified</span>}
            </div>
            <div className="flex gap-2">
              <a className="text-gray-900 hover:underline" href={`/api/v1/delivery-targets/${d.id}/package.zip`}>
                下载成品包
              </a>
              {d.action === "auto_draft" && d.status === "target_authorized" && (
                d.capability?.verified === false ? (
                  <span className="cursor-not-allowed text-slate-300" title="publisher 未真实验收，自动执行已禁用（设置 → 交付可显式放行）">
                    执行自动草稿（unverified 已禁用）
                  </span>
                ) : (
                  <button className="text-gray-900 hover:underline" onClick={() => execute.mutate(d.id)}>
                    执行自动草稿
                  </button>
                )
              )}
            </div>
          </div>
        ))}
      </div>

      {target.candidate && (
        <div className="rounded-lg border border-slate-200 bg-white p-3">
          <h4 className="mb-1 font-medium text-slate-500">批准候选</h4>
          <p className="font-mono text-[10px] text-slate-400">hash {target.candidate.approved_candidate_hash.slice(0, 20)}…</p>
          <p className="text-[10px] text-slate-400">
            schema v{target.candidate.manifest_schema} · rev{target.candidate.approved_revision} · by {target.candidate.reviewer}
          </p>
        </div>
      )}
      {msg && <div className="rounded bg-rose-50 px-2 py-1 text-rose-700">{msg}</div>}
    </div>
  );
}

function ApplyTitle({ draftId, reportId, index, onDone }: { draftId?: number; reportId: number; index: number; onDone: () => void }) {
  const [done, setDone] = useState(false);
  const apply = useMutation({
    mutationFn: () => api.post(`/drafts/${draftId}/discoverability/${reportId}/apply`, { title_index: index }),
    onSuccess: () => {
      setDone(true);
      onDone();
    },
  });
  if (draftId === undefined) return null;
  return (
    <button
      className="text-[10px] text-gray-900 hover:underline disabled:text-slate-300"
      disabled={done || apply.isPending}
      onClick={() => apply.mutate()}
    >
      {done ? "已应用（新 revision）" : "应用→新 revision"}
    </button>
  );
}

export default function ReviewPublish() {
  const { topicId } = useParams();
  const navigate = useNavigate();
  const [selectedTarget, setSelectedTarget] = useState(0);
  const { data: topics } = useQuery({
    queryKey: ["topics"],
    queryFn: () => api.get<{ id: number; title: string }[]>("/topics"),
  });
  const { data, isLoading } = useQuery({
    queryKey: ["review-center", topicId],
    queryFn: () => api.get<CenterData>(`/review-center/topics/${topicId}`),
    enabled: !!topicId,
  });

  useEffect(() => {
    if (!topicId && topics?.length) navigate(`/review-publish/${topics[0].id}`, { replace: true });
  }, [topicId, topics, navigate]);

  if (!topicId) return <Spinner />;
  if (isLoading) return <Spinner />;
  if (!data) return <EmptyState title="暂无选题" hint="先在选题中心创建选题" action={<Link to="/topics"><Button>去选题中心</Button></Link>} />;

  const target = data.targets[Math.min(selectedTarget, data.targets.length - 1)] || null;

  return (
    <div className="flex h-screen flex-col">
      <div className="flex items-center gap-3 border-b border-slate-200 bg-white px-6 py-3">
        <h1 className="text-lg font-semibold">审核与发布</h1>
        <select
          className={`${inputClass} w-72`}
          value={topicId}
          onChange={(e) => {
            navigate(`/review-publish/${e.target.value}`);
            setSelectedTarget(0);
          }}
        >
          {(topics || []).map((t) => (
            <option key={t.id} value={t.id}>
              #{t.id} {t.title.slice(0, 28)}
            </option>
          ))}
        </select>
        <span className="text-xs text-slate-400">
          {data.topic.fact_pack.name} v{data.topic.fact_pack.version} · <StatusBadge status={data.topic.fact_pack.status} />
        </span>
      </div>
      <div className="flex min-h-0 flex-1">
        <aside className="w-72 shrink-0 space-y-2 overflow-y-auto border-r border-slate-200 bg-slate-50 p-3">
          {data.targets.map((t, i) => (
            <TargetPane key={`${t.channel}.${t.content_form}`} target={t} selected={i === selectedTarget} onSelect={() => setSelectedTarget(i)} />
          ))}
        </aside>
        <main className="min-w-0 flex-1 overflow-y-auto bg-slate-50 p-6">
          {target ? <CenterPreview target={target} /> : <EmptyState title="无目标" />}
        </main>
        <aside className="w-96 shrink-0 overflow-y-auto border-l border-slate-200 bg-slate-50 p-4">
          {target ? <RightPane data={data} target={target} /> : null}
        </aside>
      </div>
    </div>
  );
}
