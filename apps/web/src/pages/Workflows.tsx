import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  Background,
  Controls,
  ReactFlow,
  type Edge,
  type Node,
  type NodeMouseHandler,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { api } from "../api";
import { Button, EmptyState, Field, Modal, StatusBadge, inputClass } from "../components/ui";

// 工作流画布：节点 = 已有能力的编排壳；数据源一条线，生成后按渠道分叉；
// 点节点看配置与产物，人工节点（采纳/批准）在检查器里直接操作。

interface WfRow {
  id: number;
  name: string;
  description: string | null;
  template_key: string | null;
  node_count: number;
  runs: { id: number; status: string; error: string; started_at: string | null }[];
}

interface TemplateRow {
  key: string;
  name: string;
  description: string;
  params_schema: { key: string; label: string; type: string; default?: unknown }[];
}

interface StepRow {
  id: number;
  node_id: string;
  node_type: string;
  label: string;
  params: Record<string, unknown>;
  status: string;
  output: Record<string, unknown>;
  error: string | null;
  layout: { x: number; y: number };
  channel: string | null;
}

interface RunRow {
  id: number;
  workflow_id: number;
  workflow_name: string;
  status: string;
  error: string | null;
  params: Record<string, unknown>;
  context: Record<string, unknown>;
  started_at: string | null;
  finished_at: string | null;
  definition: { nodes: { id: string; type: string; label: string; params: Record<string, unknown>; layout: { x: number; y: number } }[]; edges: { from: string; to: string }[] };
  steps: StepRow[];
}

const STATUS_STYLE: Record<string, { bg: string; border: string; badge: string }> = {
  pending: { bg: "#ffffff", border: "#cbd5e1", badge: "待执行" },
  running: { bg: "#eff6ff", border: "#3b82f6", badge: "执行中" },
  waiting_input: { bg: "#fffbeb", border: "#f59e0b", badge: "等你操作" },
  succeeded: { bg: "#f0fdf4", border: "#22c55e", badge: "完成" },
  failed: { bg: "#fef2f2", border: "#ef4444", badge: "失败" },
  skipped: { bg: "#f8fafc", border: "#e2e8f0", badge: "跳过" },
};

const NODE_TYPE_LABEL: Record<string, string> = {
  connector_pull: "拉取数据",
  extract_facts: "抽取事实",
  factpack_freeze: "打包冻结",
  suggest_topics: "AI 荐题",
  adopt_topic: "人工采纳",
  generate: "生成",
  fact_check: "事实校验",
  approve: "人工批准",
  export: "导出",
  publish_wechat: "公众号草稿箱",
};

const CHANNEL_LABEL: Record<string, string> = { douyin: "抖音", xiaohongshu: "小红书", wechat: "公众号" };

// ---------- 荐题候选类型 ----------
interface Suggestion {
  title: string;
  audience: string;
  angle: string;
  core_thesis: string;
  must_include: string[];
  fact_pack_id: number;
}

// ---------- 新建工作流弹窗 ----------

function CreateWorkflowModal({ onClose }: { onClose: () => void }) {
  const queryClient = useQueryClient();
  const { data: templates } = useQuery({
    queryKey: ["wf-templates"],
    queryFn: () => api.get<TemplateRow[]>("/workflows/templates"),
  });
  const { data: connectors } = useQuery({
    queryKey: ["connectors"],
    queryFn: () => api.get<{ id: number; name: string; endpoints: { id: number; name: string }[] }[]>("/connectors"),
  });
  const [templateKey, setTemplateKey] = useState("");
  const [name, setName] = useState("");
  const [endpointId, setEndpointId] = useState(0);
  const [channels, setChannels] = useState<string[]>(["douyin", "xiaohongshu", "wechat"]);
  const [error, setError] = useState("");

  const endpoints = (connectors || []).flatMap((c) => (c.endpoints || []).map((e) => ({ ...e, connector: c.name })));
  const create = useMutation({
    mutationFn: () => {
      const params =
        templateKey === "daily_suggest"
          ? { endpoint_id: endpointId }
          : { channels, publish_wechat: channels.includes("wechat") };
      return api.post<WfRow>("/workflows", { template_key: templateKey, name: name || undefined, params });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workflows"] });
      onClose();
    },
    onError: (e) => setError(e instanceof Error ? e.message : "创建失败"),
  });

  return (
    <Modal title="新建工作流" onClose={onClose}>
      <div className="space-y-3">
        <Field label="模板">
          <select className={inputClass} value={templateKey} onChange={(e) => setTemplateKey(e.target.value)}>
            <option value="">请选择</option>
            {(templates || []).map((t) => (
              <option key={t.key} value={t.key}>
                {t.name}
              </option>
            ))}
          </select>
        </Field>
        {templateKey && <p className="text-xs leading-relaxed text-slate-400">{templates?.find((t) => t.key === templateKey)?.description}</p>}
        {templateKey === "daily_suggest" && (
          <Field label="监测数据端点（拉取节点用）">
            <select className={inputClass} value={endpointId} onChange={(e) => setEndpointId(Number(e.target.value))}>
              <option value={0}>请选择</option>
              {endpoints.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.name}（{e.connector}）
                </option>
              ))}
            </select>
          </Field>
        )}
        {templateKey === "gen_export" && (
          <Field label="渠道线（每条独立：生成→校验→批准→导出）">
            <div className="flex gap-2">
              {Object.entries(CHANNEL_LABEL).map(([key, label]) => (
                <button
                  key={key}
                  type="button"
                  onClick={() => setChannels(channels.includes(key) ? channels.filter((c) => c !== key) : [...channels, key])}
                  className={`rounded-md border px-3 py-1.5 text-sm ${
                    channels.includes(key) ? "border-gray-900 bg-gray-100 text-gray-900" : "border-slate-300 bg-white text-slate-600"
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </Field>
        )}
        <Field label="名称（可选）">
          <input className={inputClass} value={name} onChange={(e) => setName(e.target.value)} placeholder="默认用模板名" />
        </Field>
        {error && <div className="rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>}
      </div>
      <div className="mt-4 flex justify-end gap-2">
        <Button variant="secondary" onClick={onClose}>
          取消
        </Button>
        <Button disabled={!templateKey || create.isPending || (templateKey === "daily_suggest" && !endpointId)} onClick={() => create.mutate()}>
          创建
        </Button>
      </div>
    </Modal>
  );
}

// ---------- 检查器：节点配置 / 结果 / 人工操作 ----------

function Inspector({
  run,
  step,
  onDone,
}: {
  run: RunRow;
  step: StepRow;
  onDone: () => void;
}) {
  const queryClient = useQueryClient();
  const [error, setError] = useState("");
  const [adoptIndex, setAdoptIndex] = useState(0);
  const [adoptChannels, setAdoptChannels] = useState<string[]>(["douyin", "xiaohongshu", "wechat"]);
  const suggestions = (run.context.suggestions || []) as Suggestion[];
  const jobs = (run.context.jobs || {}) as Record<string, { job_id: number; draft_id: number }>;
  const draftId = jobs[step.channel || ""]?.draft_id;
  const checkStep = run.steps.find((s) => s.node_id === `check_${step.channel}`);

  const complete = useMutation({
    mutationFn: (payload: Record<string, unknown>) =>
      api.post<RunRow>(`/workflow-runs/${run.id}/nodes/${step.node_id}/complete`, { payload }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["wf-run", run.id] });
      queryClient.invalidateQueries({ queryKey: ["workflows"] });
      onDone();
    },
    onError: (e) => setError(e instanceof Error ? e.message : "操作失败"),
  });

  return (
    <div className="space-y-3">
      <div>
        <span className="text-sm font-semibold text-slate-800">{step.label}</span>
        <span className="ml-2 text-xs text-slate-400">{NODE_TYPE_LABEL[step.node_type] || step.node_type}</span>
        <div className="mt-1">
          <StatusBadge status={step.status === "waiting_input" ? "changes_requested" : step.status} />
        </div>
      </div>

      <div>
        <h4 className="mb-1 text-xs font-medium text-slate-500">配置</h4>
        <pre className="whitespace-pre-wrap rounded bg-slate-50 p-2 font-mono text-[11px] text-slate-600">
          {JSON.stringify(step.params, null, 1)}
        </pre>
      </div>

      {step.output && Object.keys(step.output).length > 0 && (
        <div>
          <h4 className="mb-1 text-xs font-medium text-slate-500">产物</h4>
          <pre className="whitespace-pre-wrap rounded bg-slate-50 p-2 font-mono text-[11px] text-slate-600">
            {JSON.stringify(step.output, null, 1)}
          </pre>
          {step.node_type === "connector_pull" && !!step.output.source_id && (
            <Link className="text-xs text-gray-900 hover:underline" to={`/sources`}>
              → 查看来源库
            </Link>
          )}
          {step.node_type === "generate" && !!step.output.draft_id && (
            <Link className="ml-2 text-xs text-gray-900 hover:underline" to={`/workspace/${run.context.topic_id}`}>
              → 打开工作台
            </Link>
          )}
          {step.node_type === "export" && !!step.output.asset_id && (
            <Link className="ml-2 text-xs text-gray-900 hover:underline" to="/assets">
              → 内容资产库
            </Link>
          )}
        </div>
      )}

      {step.error && <div className="rounded-md bg-rose-50 px-3 py-2 text-xs text-rose-700">{step.error}</div>}

      {/* 人工采纳 */}
      {step.node_type === "adopt_topic" && step.status === "waiting_input" && (
        <div className="space-y-2 rounded-md border border-amber-200 bg-amber-50 p-3">
          <h4 className="text-xs font-semibold text-amber-700">采纳一个选题候选</h4>
          <div className="max-h-64 space-y-1.5 overflow-y-auto">
            {suggestions.map((s, i) => (
              <label key={i} className="flex cursor-pointer items-start gap-2 rounded border border-slate-200 bg-white p-2 hover:bg-slate-50">
                <input type="radio" name="adopt" className="mt-0.5" checked={adoptIndex === i} onChange={() => setAdoptIndex(i)} />
                <span className="min-w-0">
                  <span className="block text-xs font-medium text-slate-800">{s.title}</span>
                  <span className="block truncate text-[11px] text-slate-400">{s.core_thesis}</span>
                </span>
              </label>
            ))}
          </div>
          <Field label="目标渠道">
            <div className="flex gap-1.5">
              {Object.entries(CHANNEL_LABEL).map(([key, label]) => (
                <button
                  key={key}
                  type="button"
                  onClick={() => setAdoptChannels(adoptChannels.includes(key) ? adoptChannels.filter((c) => c !== key) : [...adoptChannels, key])}
                  className={`rounded border px-2 py-1 text-xs ${
                    adoptChannels.includes(key) ? "border-gray-900 bg-gray-100 text-gray-900" : "border-slate-300 bg-white text-slate-600"
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </Field>
          <Button
            size="sm"
            disabled={complete.isPending || adoptChannels.length === 0}
            onClick={() => complete.mutate({ index: adoptIndex, channels: adoptChannels })}
          >
            {complete.isPending ? "创建中…" : "采纳并创建选题"}
          </Button>
        </div>
      )}

      {/* 人工批准 */}
      {step.node_type === "approve" && step.status === "waiting_input" && (
        <div className="space-y-2 rounded-md border border-amber-200 bg-amber-50 p-3">
          <h4 className="text-xs font-semibold text-amber-700">批准 {CHANNEL_LABEL[step.channel || ""] || step.channel} 草稿</h4>
          {checkStep && (
            <p className="text-[11px] text-slate-500">
              FactCheck：{String(checkStep.output.result ?? '-')} · blocker {String(checkStep.output.blockers ?? '-')} · warning {String(checkStep.output.warnings ?? '-')}
            </p>
          )}
          {draftId && (
            <Link className="block text-xs text-gray-900 hover:underline" to={`/workspace/${run.context.topic_id}`}>
              → 到工作台查看全文
            </Link>
          )}
          <Button size="sm" disabled={complete.isPending} onClick={() => complete.mutate({})}>
            {complete.isPending ? "批准中…" : "批准并进入导出"}
          </Button>
          <p className="text-[11px] text-slate-400">批准沿用既有闸门：无 blocker + 冻结包 + revision 未变。</p>
        </div>
      )}

      {error && <div className="rounded-md bg-rose-50 px-3 py-2 text-xs text-rose-700">{error}</div>}
    </div>
  );
}

// ---------- 画布 ----------

function statusOf(run: RunRow | null, nodeId: string): string {
  if (!run) return "pending";
  return run.steps.find((s) => s.node_id === nodeId)?.status || "pending";
}

export default function Workflows() {
  const queryClient = useQueryClient();
  const { data: workflows } = useQuery({
    queryKey: ["workflows"],
    queryFn: () => api.get<WfRow[]>("/workflows"),
  });
  const { data: topics } = useQuery({
    queryKey: ["topics"],
    queryFn: () => api.get<{ id: number; title: string }[]>("/topics"),
  });
  const [showCreate, setShowCreate] = useState(false);
  const [selectedWf, setSelectedWf] = useState<number | null>(null);
  const [runId, setRunId] = useState<number | null>(null);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [startTopicId, setStartTopicId] = useState(0);

  const wf = (workflows || []).find((w) => w.id === selectedWf) || null;
  const { data: run } = useQuery({
    queryKey: ["wf-run", runId],
    queryFn: () => api.get<RunRow>(`/workflow-runs/${runId}`),
    enabled: !!runId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "running" || status === "waiting_input" ? 3000 : false;
    },
  });

  const start = useMutation({
    mutationFn: () =>
      api.post<RunRow>("/workflow-runs", {
        workflow_id: wf?.id,
        params: wf?.template_key === "gen_export" ? { topic_id: startTopicId } : {},
      }),
    onSuccess: (r) => {
      setRunId(r.id);
      setSelectedNode(null);
      queryClient.invalidateQueries({ queryKey: ["workflows"] });
    },
    onError: (e) => alert(e instanceof Error ? e.message : "启动失败"),
  });

  const [flowNodes, flowEdges] = useMemo(() => {
    const definition = run?.definition;
    if (!definition) return [[], []] as [Node[], Edge[]];
    const nodes: Node[] = definition.nodes.map((n: (typeof definition.nodes)[number]) => {
      const status = statusOf(run, n.id);
      const style = STATUS_STYLE[status] || STATUS_STYLE.pending;
      const channelKey = n.params.channel ? String(n.params.channel) : "";
      const channelLabel = channelKey ? ` · ${CHANNEL_LABEL[channelKey] || channelKey}` : "";
      return {
        id: n.id,
        position: { x: n.layout.x, y: n.layout.y },
        data: {
          label: (
            <div className="text-left">
              <div className="text-[10px] text-slate-400">{NODE_TYPE_LABEL[n.type] || n.type}{channelLabel}</div>
              <div className="text-xs font-semibold text-slate-800">{n.label}</div>
              <div className="mt-0.5 text-[10px] font-medium" style={{ color: style.border }}>
                {style.badge}
              </div>
            </div>
          ),
        },
        style: {
          background: style.bg,
          border: `2px solid ${style.border}`,
          borderRadius: 10,
          width: 190,
          padding: 6,
        },
      };
    });
    const edges: Edge[] = definition.edges.map((e: (typeof definition.edges)[number], i: number) => {
      const from = statusOf(run, e.from);
      const to = statusOf(run, e.to);
      const flowing = from === "succeeded" && (to === "running" || to === "waiting_input");
      return {
        id: `e${i}`,
        source: e.from,
        target: e.to,
        animated: flowing,
        style: { stroke: from === "succeeded" ? "#22c55e" : "#cbd5e1", strokeWidth: 2 },
      };
    });
    return [nodes, edges];
  }, [run]);

  const onNodeClick: NodeMouseHandler = useCallback((_, node) => setSelectedNode(node.id), []);
  const selectedStep = run?.steps.find((s) => s.node_id === selectedNode) || null;
  const active = run && (run.status === "running" || run.status === "waiting_input");

  useEffect(() => {
    if (workflows && workflows.length && selectedWf === null) setSelectedWf(workflows[0].id);
  }, [workflows, selectedWf]);

  return (
    <div className="flex h-screen flex-col">
      <div className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-3">
        <h1 className="text-lg font-semibold">工作流画布</h1>
        <div className="flex items-center gap-2">
          {wf && (
            <>
              <select
                className={`${inputClass} w-64`}
                value={selectedWf ?? ""}
                onChange={(e) => {
                  setSelectedWf(Number(e.target.value));
                  setRunId(null);
                  setSelectedNode(null);
                }}
              >
                {(workflows || []).map((w) => (
                  <option key={w.id} value={w.id}>
                    {w.name}
                  </option>
                ))}
              </select>
              {wf.template_key === "gen_export" && (
                <select className={`${inputClass} w-56`} value={startTopicId} onChange={(e) => setStartTopicId(Number(e.target.value))}>
                  <option value={0}>选择选题（启动参数）</option>
                  {(topics || []).map((t) => (
                    <option key={t.id} value={t.id}>
                      #{t.id} {t.title.slice(0, 24)}
                    </option>
                  ))}
                </select>
              )}
              <Button
                disabled={!!active || start.isPending || (wf.template_key === "gen_export" && !startTopicId)}
                onClick={() => start.mutate()}
              >
                {active ? "执行中…" : "▶ 启动运行"}
              </Button>
              {runId && (
                <select className={`${inputClass} w-28`} value={runId} onChange={(e) => setRunId(Number(e.target.value))}>
                  {wf.runs.map((r) => (
                    <option key={r.id} value={r.id}>
                      #{r.id} {r.status}
                    </option>
                  ))}
                </select>
              )}
            </>
          )}
          <Button variant="secondary" onClick={() => setShowCreate(true)}>
            从模板新建
          </Button>
        </div>
      </div>

      {run?.status === "waiting_input" && (
        <div className="bg-amber-50 px-6 py-2 text-sm text-amber-700">
          ⏸ 流程暂停：有节点等你操作（画布上黄色节点），完成后自动继续。
        </div>
      )}
      {run?.status === "failed" && (
        <div className="flex items-center justify-between bg-rose-50 px-6 py-2 text-sm text-rose-700">
          <span>✕ {run.error}</span>
          <Button
            size="sm"
            variant="secondary"
            onClick={async () => {
              const r = await api.post<RunRow>(`/workflow-runs/${run.id}/retry`);
              setRunId(r.id);
              queryClient.invalidateQueries({ queryKey: ["wf-run", run.id] });
            }}
          >
            从失败节点重试
          </Button>
        </div>
      )}

      <div className="flex min-h-0 flex-1">
        <div className="min-w-0 flex-1">
          {!run ? (
            <EmptyState title="选择或启动一次运行" hint="画布会展示执行状态，点节点查看配置与产物" />
          ) : (
            <ReactFlow
              nodes={flowNodes}
              edges={flowEdges}
              onNodeClick={onNodeClick}
              fitView
              nodesDraggable={false}
              nodesConnectable={false}
              proOptions={{ hideAttribution: true }}
            >
              <Background gap={18} />
              <Controls showInteractive={false} />
            </ReactFlow>
          )}
        </div>
        {selectedStep && run && (
          <aside className="w-96 shrink-0 overflow-y-auto border-l border-slate-200 bg-white p-4">
            <Inspector run={run} step={selectedStep} onDone={() => setSelectedNode(null)} />
          </aside>
        )}
      </div>

      {showCreate && <CreateWorkflowModal onClose={() => setShowCreate(false)} />}
    </div>
  );
}
