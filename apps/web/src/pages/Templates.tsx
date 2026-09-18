import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../api";
import { Button, EmptyState, Spinner, StatusBadge } from "../components/ui";

interface BrandVoice {
  id: number;
  name: string;
  version: number;
  description: string | null;
  tone_rules: string[];
  preferred_words: string[];
  forbidden_words: string[];
  status: string;
}

interface ChannelTemplate {
  id: number;
  channel: string;
  name: string;
  version: number;
  structure: string[];
  length_guidance: Record<string, string>;
  status: string;
}

interface PromptVersion {
  id: number;
  channel: string;
  name: string;
  version: number;
  status: string;
  template_text: string;
}

const TABS = [
  ["brand-voice", "Brand Voice"],
  ["templates", "渠道模板"],
  ["prompts", "Prompt 版本"],
] as const;

function TemplatesTab() {
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ["channel-templates"],
    queryFn: () => api.get<ChannelTemplate[]>("/templates/channel-templates"),
  });

  const setStatus = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) =>
      api.post(`/templates/channel-templates/${id}/status`, { status }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["channel-templates"] }),
    onError: (e) => alert(e instanceof Error ? e.message : "操作失败"),
  });
  const clone = useMutation({
    mutationFn: (id: number) => api.post(`/templates/channel-templates/clone?source_id=${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["channel-templates"] }),
    onError: (e) => alert(e instanceof Error ? e.message : "克隆失败"),
  });
  const del = useMutation({
    mutationFn: (t: ChannelTemplate) =>
      api.del(`/templates/channel-templates/${t.id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["channel-templates"] }),
    onError: (e) => alert(e instanceof Error ? e.message : "删除失败"),
  });

  function remove(t: ChannelTemplate) {
    if (window.confirm(`确定删除模板「${t.name}」v${t.version}？删除后不可恢复。`)) {
      del.mutate(t);
    }
  }

  if (isLoading) return <Spinner />;
  if (!data?.length) return <EmptyState title="暂无模板" />;

  return (
    <div className="grid grid-cols-3 gap-4">
      {data.map((t) => (
        <div key={t.id} className="rounded-lg border border-slate-200 bg-white p-4">
          <div className="flex items-center justify-between">
            <span className="font-medium">{t.name}</span>
            <StatusBadge status={t.status} />
          </div>
          <div className="mt-1 text-xs text-slate-400">
            {t.channel} · v{t.version}
          </div>
          <ul className="mt-3 space-y-1 text-xs text-slate-600">
            {t.structure.map((s, i) => (
              <li key={i}>· {s}</li>
            ))}
          </ul>
          <div className="mt-3 flex gap-2">
            {t.status !== "published" && (
              <Button size="sm" onClick={() => setStatus.mutate({ id: t.id, status: "published" })}>
                发布
              </Button>
            )}
            <Button size="sm" variant="secondary" onClick={() => clone.mutate(t.id)}>
              Clone
            </Button>
            {t.status !== "published" && (
              <Button size="sm" variant="ghost" onClick={() => setStatus.mutate({ id: t.id, status: "archived" })}>
                归档
              </Button>
            )}
            <Button size="sm" variant="danger" className="ml-auto" onClick={() => remove(t)}>
              删除
            </Button>
          </div>
        </div>
      ))}
    </div>
  );
}

function BrandVoiceTab() {
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ["brand-voices"],
    queryFn: () => api.get<BrandVoice[]>("/templates/brand-voices"),
  });
  const setStatus = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) =>
      api.post(`/templates/brand-voices/${id}/status`, { status }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["brand-voices"] }),
    onError: (e) => alert(e instanceof Error ? e.message : "操作失败"),
  });
  const clone = useMutation({
    mutationFn: (id: number) => api.post(`/templates/brand-voices/clone?source_id=${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["brand-voices"] }),
    onError: (e) => alert(e instanceof Error ? e.message : "克隆失败"),
  });
  const del = useMutation({
    mutationFn: (bv: BrandVoice) => api.del(`/templates/brand-voices/${bv.id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["brand-voices"] }),
    onError: (e) => alert(e instanceof Error ? e.message : "删除失败"),
  });

  function remove(bv: BrandVoice) {
    if (window.confirm(`确定删除 Brand Voice「${bv.name}」v${bv.version}？删除后不可恢复。`)) {
      del.mutate(bv);
    }
  }

  if (isLoading) return <Spinner />;
  if (!data?.length) return <EmptyState title="暂无 Brand Voice" />;

  return (
    <div className="grid grid-cols-2 gap-4">
      {data.map((bv) => (
        <div key={bv.id} className="rounded-lg border border-slate-200 bg-white p-4">
          <div className="flex items-center justify-between">
            <span className="font-medium">
              {bv.name} <span className="text-xs font-normal text-slate-400">v{bv.version}</span>
            </span>
            <StatusBadge status={bv.status} />
          </div>
          {bv.description && <p className="mt-1 text-xs text-slate-500">{bv.description}</p>}
          <div className="mt-3 space-y-2 text-xs">
            {bv.tone_rules.length > 0 && (
              <div>
                <span className="text-slate-400">语气规则：</span>
                {bv.tone_rules.join("；")}
              </div>
            )}
            {bv.preferred_words.length > 0 && (
              <div>
                <span className="text-slate-400">偏好用词：</span>
                {bv.preferred_words.join("、")}
              </div>
            )}
            {bv.forbidden_words.length > 0 && (
              <div className="text-rose-600">
                <span className="text-slate-400">禁用词：</span>
                {bv.forbidden_words.join("、")}
              </div>
            )}
          </div>
          <div className="mt-3 flex gap-2">
            {bv.status !== "published" && (
              <Button size="sm" onClick={() => setStatus.mutate({ id: bv.id, status: "published" })}>
                发布
              </Button>
            )}
            <Button size="sm" variant="secondary" onClick={() => clone.mutate(bv.id)}>
              Clone
            </Button>
            <Button size="sm" variant="danger" className="ml-auto" onClick={() => remove(bv)}>
              删除
            </Button>
          </div>
        </div>
      ))}
    </div>
  );
}

function PromptsTab() {
  const queryClient = useQueryClient();
  const [expanded, setExpanded] = useState<number | null>(null);
  const { data, isLoading } = useQuery({
    queryKey: ["prompts"],
    queryFn: () => api.get<PromptVersion[]>("/templates/prompts"),
  });
  const del = useMutation({
    mutationFn: (p: PromptVersion) => api.del(`/templates/prompts/${p.id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["prompts"] }),
    onError: (e) => alert(e instanceof Error ? e.message : "删除失败"),
  });

  function remove(p: PromptVersion) {
    if (window.confirm(`确定删除 Prompt「${p.name}」v${p.version}？删除后不可恢复。`)) {
      del.mutate(p);
    }
  }

  if (isLoading) return <Spinner />;
  if (!data?.length) return <EmptyState title="暂无 Prompt 版本" />;

  return (
    <div className="space-y-3">
      {data.map((p) => (
        <div key={p.id} className="rounded-lg border border-slate-200 bg-white p-4">
          <div className="flex items-center justify-between">
            <div>
              <span className="font-medium">{p.name}</span>
              <span className="ml-2 text-xs text-slate-400">
                {p.channel} · v{p.version}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <StatusBadge status={p.status} />
              <Button size="sm" variant="ghost" onClick={() => setExpanded(expanded === p.id ? null : p.id)}>
                {expanded === p.id ? "收起" : "查看"}
              </Button>
              {p.status !== "published" && (
                <Button size="sm" variant="danger" onClick={() => remove(p)}>
                  删除
                </Button>
              )}
            </div>
          </div>
          {expanded === p.id && (
            <pre className="mt-3 max-h-72 overflow-y-auto whitespace-pre-wrap rounded bg-slate-50 p-3 font-mono text-xs leading-relaxed">
              {p.template_text}
            </pre>
          )}
        </div>
      ))}
    </div>
  );
}

export default function Templates() {
  const [tab, setTab] = useState<(typeof TABS)[number][0]>("brand-voice");

  return (
    <div className="mx-auto max-w-6xl space-y-4 p-8">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">模板中心</h1>
        <span className="text-xs text-slate-400">
          内容一律不可编辑（含克隆草稿），变更 = Clone 新版本发布；同渠道仅最新发布版本生效，发布自动下线旧版本
        </span>
      </div>
      <div className="flex gap-1 rounded-md bg-slate-100 p-0.5 text-sm w-fit">
        {TABS.map(([key, label]) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={`rounded px-4 py-1.5 ${tab === key ? "bg-white font-medium shadow-sm" : "text-slate-500"}`}
          >
            {label}
          </button>
        ))}
      </div>
      {tab === "brand-voice" && <BrandVoiceTab />}
      {tab === "templates" && <TemplatesTab />}
      {tab === "prompts" && <PromptsTab />}
    </div>
  );
}
