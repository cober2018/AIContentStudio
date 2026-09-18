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

interface Suggestion {
  title: string;
  audience: string;
  goal: string;
  angle: string;
  core_thesis: string;
  must_include: string[];
  forbidden: string[];
  cta: string;
  rationale: string;
  fact_pack_id: number;
}

function SuggestModal({
  onClose,
  onAdopt,
}: {
  onClose: () => void;
  onAdopt: (s: Suggestion) => void;
}) {
  const { data: packs } = useQuery({
    queryKey: ["fact-packs", "frozen"],
    queryFn: () => api.get<PackRow[]>("/fact-packs?status=frozen"),
  });
  const [packId, setPackId] = useState(0);
  const [count, setCount] = useState(3);
  const [suggestions, setSuggestions] = useState<Suggestion[] | null>(null);
  const [model, setModel] = useState<string>("");
  const [error, setError] = useState("");

  const suggest = useMutation({
    mutationFn: () =>
      api.post<{ suggestions: Suggestion[]; model: { provider: string; model: string } }>(
        `/topics/suggest?fact_pack_id=${packId}&count=${count}`,
      ),
    onSuccess: (d) => {
      setSuggestions(d.suggestions);
      setModel(`${d.model.provider} · ${d.model.model}`);
      setError("");
    },
    onError: (e) => setError(e instanceof Error ? e.message : "荐题失败"),
  });

  return (
    <Modal title="AI 荐题（基于冻结事实包）" onClose={onClose} wide>
      <p className="mb-3 text-xs leading-relaxed text-slate-400">
        模型只读取所选 FactPack 里已确认的事实来提出选题候选，不引入事实包外的数字；
        采纳后仍走完整的生成 → FactCheck → 审核链路。模型在「设置 → 模型服务 → 场景路由」的
        选题发现中配置。
      </p>
      <div className="flex items-end gap-2">
        <Field label="FactPack（仅 frozen）">
          <select className={inputClass} value={packId} onChange={(e) => setPackId(Number(e.target.value))}>
            <option value={0}>请选择</option>
            {(packs || []).map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} v{p.version}（{p.item_count} 条事实）
              </option>
            ))}
          </select>
        </Field>
        <Field label="候选数">
          <select className={inputClass} value={count} onChange={(e) => setCount(Number(e.target.value))}>
            {[2, 3, 4, 5].map((n) => (
              <option key={n} value={n}>{n}</option>
            ))}
          </select>
        </Field>
        <Button className="mb-0.5" disabled={!packId || suggest.isPending} onClick={() => suggest.mutate()}>
          {suggest.isPending ? "生成中…" : "生成候选"}
        </Button>
      </div>
      {model && <p className="mt-2 text-xs text-slate-400">本次荐题模型：{model}</p>}
      {error && <div className="mt-2 rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>}
      {suggestions && (
        <div className="mt-3 max-h-[46vh] space-y-3 overflow-y-auto">
          {suggestions.map((s, i) => (
            <div key={i} className="rounded-lg border border-slate-200 p-3">
              <div className="flex items-start justify-between gap-3">
                <h3 className="text-sm font-medium text-slate-800">{s.title}</h3>
                <Button size="sm" onClick={() => onAdopt(s)}>
                  采纳
                </Button>
              </div>
              <p className="mt-1 text-xs leading-relaxed text-slate-500">{s.core_thesis}</p>
              <div className="mt-1.5 flex flex-wrap gap-x-3 gap-y-1 text-[11px] text-slate-400">
                <span>受众：{s.audience || "-"}</span>
                <span>角度：{s.angle || "-"}</span>
                {s.must_include?.length > 0 && <span>必含：{s.must_include.join("、")}</span>}
              </div>
              {s.rationale && <p className="mt-1 text-[11px] text-slate-400">理由：{s.rationale}</p>}
            </div>
          ))}
        </div>
      )}
      <div className="mt-4 flex justify-end">
        <Button variant="secondary" onClick={onClose}>
          关闭
        </Button>
      </div>
    </Modal>
  );
}

function CreateTopicModal({
  onClose,
  initial,
}: {
  onClose: () => void;
  initial?: Partial<Suggestion> | null;
}) {
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
    title: initial?.title || "",
    audience: initial?.audience || "",
    goal: initial?.goal || "",
    angle: initial?.angle || "",
    core_thesis: initial?.core_thesis || "",
    must_include: (initial?.must_include || []).join("、"),
    forbidden: (initial?.forbidden || []).join("、"),
    cta: initial?.cta || "",
    fact_pack_id: initial?.fact_pack_id || 0,
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
                      ? "border-gray-900 bg-gray-100 text-gray-900"
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
  const [showSuggest, setShowSuggest] = useState(false);
  const [adopted, setAdopted] = useState<Suggestion | null>(null);
  const navigate = useNavigate();
  const { data, isLoading } = useQuery({
    queryKey: ["topics"],
    queryFn: () => api.get<TopicRow[]>("/topics"),
  });

  return (
    <div className="mx-auto max-w-6xl space-y-4 p-8">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">选题中心</h1>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={() => setShowSuggest(true)}>
            AI 荐题
          </Button>
          <Button onClick={() => setShowCreate(true)}>新建选题</Button>
        </div>
      </div>

      {isLoading ? (
        <Spinner />
      ) : !data || data.length === 0 ? (
        <EmptyState
          title="暂无选题"
          hint="选题绑定 frozen FactPack 后可多渠道生成"
          action={
            <div className="flex gap-2">
              <Button variant="secondary" onClick={() => setShowSuggest(true)}>
                AI 荐题
              </Button>
              <Button onClick={() => setShowCreate(true)}>新建选题</Button>
            </div>
          }
        />
      ) : (
        <div className="grid grid-cols-2 gap-4">
          {data.map((t) => (
            <div
              key={t.id}
              className="cursor-pointer rounded-lg border border-slate-200 bg-white p-4 hover:border-gray-400"
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

      {showSuggest && (
        <SuggestModal
          onClose={() => setShowSuggest(false)}
          onAdopt={(s) => {
            setAdopted(s);
            setShowSuggest(false);
            setShowCreate(true);
          }}
        />
      )}
      {showCreate && (
        <CreateTopicModal
          initial={adopted}
          onClose={() => {
            setShowCreate(false);
            setAdopted(null);
          }}
        />
      )}
    </div>
  );
}
