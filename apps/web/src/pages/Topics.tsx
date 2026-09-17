import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import { Button, ChannelBadge, EmptyState, Field, Modal, Spinner, StatusBadge, inputClass } from "../components/ui";

interface PackRow {
  id: number;
  name: string;
  version: number;
  status: string;
  item_count: number;
  created_at: string;
}

interface TopicRow {
  id: number;
  title: string;
  audience: string | null;
  core_thesis: string | null;
  channels: string[];
  status: string;
  fact_pack: { id: number; name: string; version: number; status: string; fact_count: number };
  content_jobs?: { id: number; channel: string; status: string }[];
}

const CHANNELS = [
  ["douyin", "抖音"],
  ["xiaohongshu", "小红书"],
  ["wechat", "公众号"],
] as const;

function CreateTopicModal({ onClose }: { onClose: () => void }) {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const { data: packs } = useQuery({
    queryKey: ["fact-packs", "frozen"],
    queryFn: () => api.get<PackRow[]>("/fact-packs?status=frozen"),
  });
  const { data: voices } = useQuery({
    queryKey: ["brand-voices"],
    queryFn: () => api.get<{ id: number; name: string; version: number; status: string }[]>("/templates/brand-voices"),
  });

  const [form, setForm] = useState({
    title: "",
    audience: "",
    goal: "",
    angle: "",
    core_thesis: "",
    must_include: "",
    forbidden: "",
    cta: "",
    fact_pack_id: 0,
    brand_voice_version_id: 0,
    channels: ["douyin"] as string[],
  });
  const [error, setError] = useState("");

  const selectedPack = (packs || []).find((p) => p.id === form.fact_pack_id);

  const create = useMutation({
    mutationFn: () =>
      api.post<{ id: number }>("/topics", {
        ...form,
        fact_pack_id: form.fact_pack_id,
        brand_voice_version_id: form.brand_voice_version_id || null,
        must_include: form.must_include.split(/[,，、\s]+/).filter(Boolean),
        forbidden: form.forbidden.split(/[,，、\s]+/).filter(Boolean),
      }),
    onSuccess: (topic) => {
      queryClient.invalidateQueries({ queryKey: ["topics"] });
      onClose();
      navigate(`/workspace/${topic.id}`);
    },
    onError: (e) => setError(e instanceof Error ? e.message : "创建失败"),
  });

  const set = (key: string, value: string | number | string[]) => setForm((f) => ({ ...f, [key]: value }));

  return (
    <Modal title="新建选题" onClose={onClose} wide>
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-3">
          <Field label="标题 *">
            <input className={inputClass} value={form.title} onChange={(e) => set("title", e.target.value)} />
          </Field>
          <Field label="目标受众">
            <input className={inputClass} value={form.audience} onChange={(e) => set("audience", e.target.value)} />
          </Field>
          <Field label="目标">
            <input className={inputClass} value={form.goal} onChange={(e) => set("goal", e.target.value)} />
          </Field>
          <Field label="内容角度">
            <input className={inputClass} value={form.angle} onChange={(e) => set("angle", e.target.value)} />
          </Field>
          <Field label="核心结论">
            <textarea
              className={`${inputClass} h-16`}
              value={form.core_thesis}
              onChange={(e) => set("core_thesis", e.target.value)}
            />
          </Field>
        </div>
        <div className="space-y-3">
          <Field label="必须包含（逗号分隔）">
            <input className={inputClass} value={form.must_include} onChange={(e) => set("must_include", e.target.value)} />
          </Field>
          <Field label="禁止出现（逗号分隔，FactCheck blocker）">
            <input className={inputClass} value={form.forbidden} onChange={(e) => set("forbidden", e.target.value)} />
          </Field>
          <Field label="CTA">
            <input className={inputClass} value={form.cta} onChange={(e) => set("cta", e.target.value)} />
          </Field>
          <Field label="Brand Voice">
            <select
              className={inputClass}
              value={form.brand_voice_version_id}
              onChange={(e) => set("brand_voice_version_id", Number(e.target.value))}
            >
              <option value={0}>默认</option>
              {(voices || [])
                .filter((v) => v.status === "published")
                .map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.name} v{v.version}
                  </option>
                ))}
            </select>
          </Field>
          <Field label="FactPack（仅 frozen）*">
            <select
              className={inputClass}
              value={form.fact_pack_id}
              onChange={(e) => set("fact_pack_id", Number(e.target.value))}
            >
              <option value={0}>请选择</option>
              {(packs || []).map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} v{p.version}（{p.item_count} 条事实）
                </option>
              ))}
            </select>
          </Field>
          <Field label="目标渠道 *">
            <div className="flex gap-2">
              {CHANNELS.map(([key, label]) => (
                <button
                  key={key}
                  type="button"
                  onClick={() =>
                    set(
                      "channels",
                      form.channels.includes(key)
                        ? form.channels.filter((c) => c !== key)
                        : [...form.channels, key],
                    )
                  }
                  className={`rounded-md border px-3 py-1.5 text-sm ${
                    form.channels.includes(key)
                      ? "border-indigo-500 bg-indigo-50 text-indigo-700"
                      : "border-slate-300 bg-white text-slate-600"
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </Field>
        </div>
      </div>

      {selectedPack && (
        <div className="mt-4 rounded-md bg-slate-50 px-4 py-3 text-xs text-slate-600">
          FactPack 概要：{selectedPack.name} v{selectedPack.version} · {selectedPack.item_count} 条事实 ·
          <StatusBadge status={selectedPack.status} />
        </div>
      )}
      {error && <div className="mt-3 rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>}

      <div className="mt-5 flex justify-end gap-2">
        <Button variant="secondary" onClick={onClose}>
          取消
        </Button>
        <Button
          disabled={!form.title || !form.fact_pack_id || form.channels.length === 0}
          onClick={() => create.mutate()}
        >
          创建并进入工作台
        </Button>
      </div>
    </Modal>
  );
}

export default function Topics() {
  const [showCreate, setShowCreate] = useState(false);
  const navigate = useNavigate();
  const { data, isLoading } = useQuery({
    queryKey: ["topics"],
    queryFn: () => api.get<TopicRow[]>("/topics"),
  });

  return (
    <div className="mx-auto max-w-6xl space-y-4 p-8">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">选题中心</h1>
        <Button onClick={() => setShowCreate(true)}>新建选题</Button>
      </div>

      {isLoading ? (
        <Spinner />
      ) : !data || data.length === 0 ? (
        <EmptyState
          title="暂无选题"
          hint="选题绑定 frozen FactPack 后可多渠道生成"
          action={<Button onClick={() => setShowCreate(true)}>新建选题</Button>}
        />
      ) : (
        <div className="grid grid-cols-2 gap-4">
          {data.map((t) => (
            <div
              key={t.id}
              className="cursor-pointer rounded-lg border border-slate-200 bg-white p-4 hover:border-indigo-300"
              onClick={() => navigate(`/workspace/${t.id}`)}
            >
              <div className="flex items-start justify-between">
                <h3 className="font-medium text-slate-800">{t.title}</h3>
                <StatusBadge status={t.status} />
              </div>
              {t.core_thesis && <p className="mt-1 line-clamp-2 text-sm text-slate-500">{t.core_thesis}</p>}
              <div className="mt-3 flex flex-wrap items-center gap-1.5 text-xs text-slate-400">
                {t.channels.map((c) => (
                  <ChannelBadge key={c} channel={c} />
                ))}
                <span>
                  · {t.fact_pack.name} v{t.fact_pack.version}（{t.fact_pack.fact_count} 事实）
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {showCreate && <CreateTopicModal onClose={() => setShowCreate(false)} />}
    </div>
  );
}
