import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ReactNode, useEffect, useMemo, useState } from "react";
import { api, currentUser, setCurrentUser } from "../api";
import { Button, ErrorBanner, Field, inputClass, StatusBadge } from "../components/ui";

// 系统配置管理页：仿桌面客户端设置页（左侧分区导航 + 右侧配置面板）。
// 模型服务 = 场景路由 + 多模型 Profiles + 默认(env)配置；技能与插件 = 本地 skills / MCP / dsh。

interface SecretView {
  configured: boolean;
  masked: string;
}

interface LLMView {
  provider: string;
  base_url: string;
  model: string;
  api_key: SecretView;
  mock_inject_unfact_number: boolean;
  overridden: boolean;
}

interface ModelProfileView {
  provider: string;
  base_url: string;
  model: string;
  api_key: SecretView;
  enabled: boolean;
}

interface ModelsView {
  profiles: Record<string, ModelProfileView>;
  routes: Record<string, string>;
}

interface SkillInfo {
  name: string;
  description: string;
  path: string;
  source: string;
}

interface McpEntry {
  name: string;
  url: string;
  enabled: boolean;
}

interface PluginsView {
  skill_dirs: string[];
  skills: SkillInfo[];
  skills_enabled: string[];
  mcp: McpEntry[];
  dsh: { url: string; reachable: boolean; status_code: number | null };
}

interface DshSnapshot {
  configured: boolean;
  settings_path: string;
  providers: Record<string, { api: string | null; base_url: string | null; api_key_env: string | null; models: string[] }>;
  default_model: { provider: string | null; model: string | null };
  env_keys: Record<string, boolean>;
}

interface DshView {
  config: {
    default_provider: string;
    default_model: string;
    fallback_provider: string;
    fallback_model: string;
    timeout_sec: number;
    max_retries: number;
    output_dir: string;
  };
  snapshot: DshSnapshot;
  last_apply?: Record<string, unknown>;
}

interface SettingsView {
  llm: LLMView;
  models: ModelsView;
  plugins: PluginsView;
  database: { url: string; driver: string };
  queue: { enabled: boolean; broker: string; queues: string[] };
  storage: {
    enabled: boolean;
    endpoint: string;
    bucket: string;
    secure: boolean;
    access_key: SecretView;
    url_expiry_hours: number;
  };
  security: {
    ssrf_allow_private: boolean;
    url_fetch_timeout_seconds: number;
    url_fetch_max_bytes: number;
    upload_max_bytes: number;
  };
  dsh: DshView;
  app: { version: string };
}

interface HealthView {
  status: string;
  db: boolean;
  provider: string;
  queue_enabled: boolean;
  version: string;
}

interface Me {
  id: number;
  email: string;
  name: string;
  role: string;
}

interface UserRow {
  id: number;
  email: string;
  name: string;
  role: string;
  is_active: boolean;
}

interface TestResult {
  ok: boolean;
  provider: string;
  model?: string;
  latency_ms?: number;
  reply?: string;
  error?: string;
}

const ROLE_DESC: Record<string, string> = {
  admin: "系统/模型/模板/品牌/用户，全部权限",
  editor: "Source、FactPack、生成、审核提交",
  reviewer: "审核与改稿",
  viewer: "只读",
};

type SectionId = "model" | "plugins" | "data" | "storage" | "security" | "identity" | "about";

const SECTIONS: { id: SectionId; label: string; icon: string; desc: string }[] = [
  { id: "model", label: "模型服务", icon: "✦", desc: "场景路由与多模型配置" },
  { id: "plugins", label: "技能与插件", icon: "⌘", desc: "Skills / MCP / dsh" },
  { id: "data", label: "数据与队列", icon: "▤", desc: "数据库与异步队列" },
  { id: "storage", label: "对象存储", icon: "◫", desc: "MinIO / S3 导出副本" },
  { id: "security", label: "安全", icon: "⛨", desc: "SSRF 防护与上传限制" },
  { id: "identity", label: "身份与权限", icon: "◉", desc: "开发模式身份切换" },
  { id: "about", label: "关于", icon: "☰", desc: "版本与链路" },
];

// 模型模板：新增 Profile 时预填（用户要求 DeepSeek 等能配的都给选项）
const PROVIDER_TEMPLATES: { label: string; provider: string; base_url: string; model: string }[] = [
  { label: "DeepSeek", provider: "openai_compatible", base_url: "https://api.deepseek.com/v1", model: "deepseek-chat" },
  { label: "MiniMax", provider: "openai_compatible", base_url: "https://api.minimaxi.com/v1", model: "MiniMax-Text-01" },
  { label: "OpenAI", provider: "openai_compatible", base_url: "https://api.openai.com/v1", model: "gpt-4o-mini" },
  { label: "自定义网关", provider: "openai_compatible", base_url: "", model: "" },
  { label: "Mock（离线）", provider: "mock", base_url: "", model: "" },
];

const ROUTE_LABELS: Record<string, string> = {
  generate: "内容生成（三渠道 / 整篇改写）",
  rewrite: "选区改写（编辑器 AI 润色）",
  fact_check: "事实校验与审核复核（LLM Reviewer）",
  topic_discovery: "选题发现（基于 FactPack AI 荐题）",
};

function bytesLabel(n: number): string {
  if (n >= 1024 * 1024) return `${Math.round(n / (1024 * 1024))} MB`;
  if (n >= 1024) return `${Math.round(n / 1024)} KB`;
  return `${n} B`;
}

function Panel({ title, desc, children }: { title: string; desc?: string; children: ReactNode }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5">
      <h2 className="text-sm font-semibold text-slate-800">{title}</h2>
      {desc && <p className="mt-1 text-xs text-slate-400">{desc}</p>}
      <div className="mt-3">{children}</div>
    </section>
  );
}

function Row({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-6 border-b border-slate-100 py-2.5 last:border-b-0">
      <span className="shrink-0 text-sm text-slate-500">{label}</span>
      <span className="break-all text-right font-mono text-xs text-slate-800">{children}</span>
    </div>
  );
}

function Dot({ ok, label }: { ok: boolean; label: string }) {
  return (
    <span className="inline-flex items-center gap-1.5 text-xs text-slate-600">
      <span className={`inline-block h-2 w-2 rounded-full ${ok ? "bg-emerald-500" : "bg-slate-300"}`} />
      {label}
    </span>
  );
}

function SourceBadge({ overridden }: { overridden: boolean }) {
  return (
    <span
      className={`inline-flex rounded border px-1.5 py-0.5 text-[11px] ${
        overridden ? "border-gray-300 bg-gray-100 text-gray-900" : "border-slate-200 bg-slate-50 text-slate-500"
      }`}
    >
      {overridden ? "页面覆盖" : "环境变量"}
    </span>
  );
}

function TestResultBar({ result }: { result: TestResult | null }) {
  if (!result) return null;
  return (
    <div
      className={`mt-3 rounded-md px-3 py-2 text-xs leading-relaxed ${
        result.ok ? "bg-emerald-50 text-emerald-700" : "bg-rose-50 text-rose-700"
      }`}
    >
      {result.ok
        ? `连接正常 · ${result.provider}${result.model ? ` · ${result.model}` : ""}${
            result.latency_ms ? ` · ${result.latency_ms}ms` : ""
          }${result.reply ? ` · 回复：${result.reply}` : ""}`
        : `连接失败：${result.error}`}
    </div>
  );
}

// ---------- 模型服务：场景路由 + Profiles + 默认配置 ----------

interface ProfileDraft {
  name: string;
  provider: string;
  base_url: string;
  model: string;
  api_key: string;
  enabled: boolean;
  isNew?: boolean;
}

function ModelsPanel({ settings, isAdmin }: { settings: SettingsView; isAdmin: boolean }) {
  const queryClient = useQueryClient();
  const models = settings.models;
  const [profiles, setProfiles] = useState<ProfileDraft[]>([]);
  const [routes, setRoutes] = useState<Record<string, string>>({});
  const [editingName, setEditingName] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [testResults, setTestResults] = useState<Record<string, TestResult>>({});

  useEffect(() => {
    setProfiles(
      Object.entries(models.profiles).map(([name, p]) => ({
        name,
        provider: p.provider,
        base_url: p.base_url,
        model: p.model,
        api_key: "",
        enabled: p.enabled,
      })),
    );
    setRoutes(models.routes);
  }, [models]);

  function startAdd(template?: (typeof PROVIDER_TEMPLATES)[number]) {
    const base: ProfileDraft = {
      name: "",
      provider: template?.provider ?? "openai_compatible",
      base_url: template?.base_url ?? "",
      model: template?.model ?? "",
      api_key: "",
      enabled: true,
      isNew: true,
    };
    setProfiles([...profiles, base]);
    setEditingName("");
  }

  function startEdit(p: ProfileDraft) {
    setEditingName(p.name);
  }

  function updateDraft(idx: number, patch: Partial<ProfileDraft>) {
    setProfiles(profiles.map((p, i) => (i === idx ? { ...p, ...patch } : p)));
  }

  const save = useMutation({
    mutationFn: () =>
      api.put<ModelsView>("/settings/models", {
        profiles: profiles.map((p) => ({
          name: p.name,
          provider: p.provider,
          base_url: p.base_url,
          model: p.model,
          api_key: p.api_key,
          enabled: p.enabled,
        })),
        routes,
      }),
    onSuccess: () => {
      setEditingName(null);
      setError("");
      setProfiles((prev) => prev.map((p) => ({ ...p, api_key: "", isNew: false })));
      queryClient.invalidateQueries({ queryKey: ["settings"] });
    },
    onError: (e) => setError(e instanceof Error ? e.message : "保存失败"),
  });

  function testProfile(p: ProfileDraft) {
    api
      .post<TestResult>("/settings/llm/test", {
        provider: p.provider,
        base_url: p.base_url,
        model: p.model,
        api_key: p.api_key || undefined,
      })
      .then((r) => setTestResults({ ...testResults, [p.name || String(profiles.indexOf(p))]: r }))
      .catch((e) =>
        setTestResults({ ...testResults, [p.name || String(profiles.indexOf(p))]: { ok: false, provider: p.provider, error: e instanceof Error ? e.message : "测试失败" } }),
      );
  }

  return (
    <div className="space-y-4">
      <Panel title="场景路由" desc="不同环节可用不同模型；指向的 Profile 停用或缺失时回落默认配置。">
        <div className="space-y-2.5">
          {Object.entries(ROUTE_LABELS).map(([key, label]) => (
            <div key={key} className="flex items-center gap-3">
              <span className="w-64 shrink-0 text-sm text-slate-600">{label}</span>
              <select
                className={`${inputClass} flex-1`}
                value={routes[key] || ""}
                onChange={(e) => setRoutes({ ...routes, [key]: e.target.value })}
              >
                <option value="">默认（下方环境变量 / 页面覆盖）</option>
                {profiles
                  .filter((p) => p.name)
                  .map((p) => (
                    <option key={p.name} value={p.name}>
                      {p.name} · {p.provider === "mock" ? "mock" : p.model || "未配模型"}
                      {p.enabled ? "" : "（已停用）"}
                    </option>
                  ))}
              </select>
            </div>
          ))}
        </div>
      </Panel>

      <Panel
        title="模型配置 Profiles"
        desc="可同时登记多个模型（DeepSeek / MiniMax / OpenAI / 任意兼容网关）；API Key 只回显掩码。"
      >
        {!isAdmin && <p className="mb-2 text-xs text-slate-400">需要 admin 角色才能修改。</p>}
        <div className="space-y-3">
          {profiles.map((p, idx) => {
            const stored = models.profiles[p.name];
            const editing = editingName === p.name || (p.isNew && editingName === "");
            const testKey = p.name || `new-${idx}`;
            return (
              <div key={testKey} className="rounded-lg border border-slate-200 p-3">
                {!editing ? (
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="text-sm font-medium">{p.name}</span>
                      <span className="ml-2 text-xs text-slate-400">
                        {p.provider === "mock" ? "mock" : `${p.model} @ ${p.base_url}`}
                      </span>
                      {stored && (
                        <span className="ml-2 text-xs text-slate-400">
                          Key {stored.api_key.configured ? stored.api_key.masked : "未配置"}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      {p.enabled ? <StatusBadge status="active" /> : <StatusBadge status="draft" />}
                      <Button size="sm" variant="secondary" disabled={!isAdmin} onClick={() => startEdit(p)}>
                        编辑
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        disabled={!isAdmin}
                        onClick={() => setProfiles(profiles.filter((_, i) => i !== idx))}
                      >
                        移除
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-2.5">
                    <div className="flex flex-wrap gap-1.5">
                      {PROVIDER_TEMPLATES.map((t) => (
                        <button
                          key={t.label}
                          onClick={() => updateDraft(idx, { provider: t.provider, base_url: t.base_url, model: t.model })}
                          className="rounded border border-slate-200 bg-slate-50 px-2 py-0.5 text-[11px] text-slate-600 hover:bg-slate-100"
                        >
                          {t.label}
                        </button>
                      ))}
                    </div>
                    <div className="grid grid-cols-2 gap-2.5">
                      <Field label="名称">
                        <input
                          className={inputClass}
                          value={p.name}
                          placeholder="如 deepseek / minimax"
                          onChange={(e) => updateDraft(idx, { name: e.target.value.trim() })}
                        />
                      </Field>
                      <Field label="Provider">
                        <select
                          className={inputClass}
                          value={p.provider}
                          onChange={(e) => updateDraft(idx, { provider: e.target.value })}
                        >
                          <option value="openai_compatible">openai_compatible</option>
                          <option value="mock">mock</option>
                        </select>
                      </Field>
                    </div>
                    {p.provider === "openai_compatible" && (
                      <div className="grid grid-cols-2 gap-2.5">
                        <Field label="Base URL">
                          <input
                            className={inputClass}
                            value={p.base_url}
                            placeholder="https://api.deepseek.com/v1"
                            onChange={(e) => updateDraft(idx, { base_url: e.target.value.trim() })}
                          />
                        </Field>
                        <Field label="模型名">
                          <input
                            className={inputClass}
                            value={p.model}
                            placeholder="deepseek-chat"
                            onChange={(e) => updateDraft(idx, { model: e.target.value.trim() })}
                          />
                        </Field>
                        <Field
                          label="API Key"
                          hint={stored?.api_key.configured ? `已配置（${stored.api_key.masked}），留空保持不变` : "只在服务端使用"}
                        >
                          <input
                            className={inputClass}
                            type="password"
                            value={p.api_key}
                            placeholder={stored?.api_key.configured ? "••••••（留空保持不变）" : "粘贴 API Key"}
                            onChange={(e) => updateDraft(idx, { api_key: e.target.value })}
                          />
                        </Field>
                        <label className="flex items-end gap-2 pb-1 text-sm text-slate-600">
                          <input
                            type="checkbox"
                            checked={p.enabled}
                            onChange={(e) => updateDraft(idx, { enabled: e.target.checked })}
                          />
                          启用
                        </label>
                      </div>
                    )}
                    <div className="flex gap-2">
                      <Button size="sm" variant="secondary" onClick={() => testProfile(p)}>
                        测试连接
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => {
                          if (p.isNew) setProfiles(profiles.filter((_, i) => i !== idx));
                          else setEditingName(null);
                        }}
                      >
                        取消
                      </Button>
                    </div>
                    <TestResultBar result={testResults[testKey] ?? null} />
                  </div>
                )}
              </div>
            );
          })}
        </div>
        {error && <div className="mt-3"><ErrorBanner message={error} /></div>}
        <div className="mt-3 flex flex-wrap items-center gap-2">
          {PROVIDER_TEMPLATES.map((t) => (
            <Button key={t.label} size="sm" variant="secondary" disabled={!isAdmin} onClick={() => startAdd(t)}>
              + {t.label}
            </Button>
          ))}
          <Button
            className="ml-auto"
            disabled={!isAdmin || save.isPending}
            onClick={() => save.mutate()}
          >
            {save.isPending ? "保存中…" : "保存模型配置"}
          </Button>
        </div>
      </Panel>

      <DefaultLLMPanel settings={settings} isAdmin={isAdmin} />
    </div>
  );
}

// ---------- 默认模型（env / 页面覆盖，场景路由的回落） ----------

function DefaultLLMPanel({ settings, isAdmin }: { settings: SettingsView; isAdmin: boolean }) {
  const queryClient = useQueryClient();
  const llm = settings.llm;
  const [editing, setEditing] = useState(false);
  const [testResult, setTestResult] = useState<TestResult | null>(null);
  const [formError, setFormError] = useState("");
  const [form, setForm] = useState({
    provider: llm.provider,
    base_url: llm.base_url,
    model: llm.model,
    api_key: "",
    mock_inject_unfact_number: llm.mock_inject_unfact_number,
  });

  function startEdit() {
    setForm({
      provider: llm.provider,
      base_url: llm.base_url,
      model: llm.model,
      api_key: "",
      mock_inject_unfact_number: llm.mock_inject_unfact_number,
    });
    setTestResult(null);
    setFormError("");
    setEditing(true);
  }

  const save = useMutation({
    mutationFn: () => api.put<LLMView>("/settings/llm", form),
    onSuccess: () => {
      setEditing(false);
      queryClient.invalidateQueries({ queryKey: ["settings"] });
      queryClient.invalidateQueries({ queryKey: ["health"] });
    },
    onError: (e) => setFormError(e instanceof Error ? e.message : "保存失败"),
  });

  const reset = useMutation({
    mutationFn: () => api.del<LLMView>("/settings/llm"),
    onSuccess: () => {
      setEditing(false);
      queryClient.invalidateQueries({ queryKey: ["settings"] });
      queryClient.invalidateQueries({ queryKey: ["health"] });
    },
    onError: (e) => setFormError(e instanceof Error ? e.message : "恢复默认失败"),
  });

  const test = useMutation({
    mutationFn: () =>
      api.post<TestResult>("/settings/llm/test", {
        provider: form.provider,
        base_url: form.base_url,
        model: form.model,
        api_key: editing && form.api_key ? form.api_key : undefined,
      }),
    onSuccess: (d) => setTestResult(d),
    onError: (e) => setTestResult({ ok: false, provider: form.provider, error: e instanceof Error ? e.message : "测试失败" }),
  });

  return (
    <Panel title="默认模型（场景路由的回落）" desc="场景未指定 Profile 时使用此配置；页面覆盖优先于 .env。">
      <div className="mb-2 flex items-center gap-2">
        <span className="inline-flex rounded bg-slate-800 px-2 py-0.5 text-xs font-medium text-white">
          {llm.provider === "mock" ? "Mock（离线演示）" : "OpenAI 兼容"}
        </span>
        <SourceBadge overridden={llm.overridden} />
      </div>
      <div className="divide-y divide-slate-100">
        <Row label="Provider">{llm.provider}</Row>
        <Row label="模型">{llm.provider === "mock" ? "mock-structured-v1（确定性输出）" : llm.model || "未配置"}</Row>
        <Row label="Base URL">{llm.base_url || "—"}</Row>
        <Row label="API Key">
          {llm.api_key.configured ? `${llm.api_key.masked}（已配置，明文不回显）` : <span className="text-slate-400">未配置</span>}
        </Row>
      </div>
      {!editing ? (
        <div className="mt-3 flex gap-2">
          <Button size="sm" onClick={startEdit} disabled={!isAdmin}>
            修改默认配置
          </Button>
          {llm.overridden && (
            <Button
              size="sm"
              variant="secondary"
              disabled={!isAdmin}
              onClick={() => {
                if (window.confirm("清除页面覆盖，回落到 .env 环境变量配置？")) reset.mutate();
              }}
            >
              恢复环境变量默认
            </Button>
          )}
          <Button size="sm" variant="secondary" disabled={!isAdmin} onClick={() => test.mutate()}>
            {test.isPending ? "测试中…" : "测试当前连接"}
          </Button>
        </div>
      ) : (
        <div className="mt-3 space-y-2.5">
          <div className="grid grid-cols-2 gap-2.5">
            <Field label="Provider">
              <select className={inputClass} value={form.provider} onChange={(e) => setForm({ ...form, provider: e.target.value })}>
                <option value="mock">mock（离线演示）</option>
                <option value="openai_compatible">openai_compatible</option>
              </select>
            </Field>
            {form.provider === "openai_compatible" && (
              <>
                <Field label="模型名">
                  <input className={inputClass} value={form.model} onChange={(e) => setForm({ ...form, model: e.target.value.trim() })} />
                </Field>
                <Field label="Base URL">
                  <input className={inputClass} value={form.base_url} onChange={(e) => setForm({ ...form, base_url: e.target.value.trim() })} />
                </Field>
                <Field label="API Key" hint={llm.api_key.configured ? `已配置（${llm.api_key.masked}），留空保持不变` : ""}>
                  <input
                    className={inputClass}
                    type="password"
                    value={form.api_key}
                    placeholder={llm.api_key.configured ? "留空保持不变" : "粘贴 API Key"}
                    onChange={(e) => setForm({ ...form, api_key: e.target.value })}
                  />
                </Field>
              </>
            )}
          </div>
          {formError && <ErrorBanner message={formError} />}
          <div className="flex gap-2">
            <Button size="sm" onClick={() => save.mutate()} disabled={save.isPending}>
              保存
            </Button>
            <Button size="sm" variant="secondary" onClick={() => test.mutate()} disabled={test.isPending}>
              测试连接
            </Button>
            <Button size="sm" variant="ghost" onClick={() => setEditing(false)}>
              取消
            </Button>
          </div>
        </div>
      )}
      <TestResultBar result={testResult} />
    </Panel>
  );
}

// ---------- 技能与插件 ----------

function PluginsPanel({ settings, isAdmin }: { settings: SettingsView; isAdmin: boolean }) {
  const queryClient = useQueryClient();
  const plugins = settings.plugins;
  const dsh = settings.dsh;
  const [filter, setFilter] = useState("");
  const [enabled, setEnabled] = useState<string[]>(plugins.skills_enabled);
  const [mcp, setMcp] = useState<McpEntry[]>(plugins.mcp);
  const [skillDirs, setSkillDirs] = useState<string[]>(plugins.skill_dirs);
  const [newDir, setNewDir] = useState("");
  const [newMcp, setNewMcp] = useState({ name: "", url: "" });
  const [error, setError] = useState("");
  const [dshForm, setDshForm] = useState(dsh.config);
  const [applyToDsh, setApplyToDsh] = useState(false);
  const [dshMsg, setDshMsg] = useState("");

  useEffect(() => {
    setEnabled(plugins.skills_enabled);
    setMcp(plugins.mcp);
    setSkillDirs(plugins.skill_dirs);
    setDshForm(dsh.config);
  }, [plugins, dsh]);

  const filtered = useMemo(() => {
    const kw = filter.trim().toLowerCase();
    const list = kw ? plugins.skills.filter((s) => (s.name + s.description).toLowerCase().includes(kw)) : plugins.skills;
    return list.slice(0, 40);
  }, [plugins.skills, filter]);

  const save = useMutation({
    mutationFn: () => api.put<PluginsView>("/settings/plugins", { skill_dirs: skillDirs, skills_enabled: enabled, mcp }),
    onSuccess: () => {
      setError("");
      queryClient.invalidateQueries({ queryKey: ["settings"] });
    },
    onError: (e) => setError(e instanceof Error ? e.message : "保存失败"),
  });

  const saveDsh = useMutation({
    mutationFn: () => api.put<DshView>("/settings/dsh", { ...dshForm, apply_to_dsh: applyToDsh }),
    onSuccess: () => {
      setDshMsg(applyToDsh ? "已保存并写回 dsh 默认模型（原文件已自动备份）" : "已保存 Studio 侧 dsh 协作配置");
      setApplyToDsh(false);
      queryClient.invalidateQueries({ queryKey: ["settings"] });
    },
    onError: (e) => setDshMsg(e instanceof Error ? e.message : "保存失败"),
  });

  function toggleSkill(name: string) {
    setEnabled(enabled.includes(name) ? enabled.filter((n) => n !== name) : [...enabled, name]);
  }

  return (
    <div className="space-y-4">
      <Panel
        title="dsh 执行层（DeepSeek Harness）"
        desc="dsh 用户设置只读快照 + Studio 侧稳定性协作配置；密钥状态只显示是否已配置，永不回显值。"
      >
        <div className="mb-3 flex items-center justify-between">
          <Dot
            ok={plugins.dsh.reachable}
            label={`dsh :3080 ${plugins.dsh.reachable ? `在线（HTTP ${plugins.dsh.status_code}，token 鉴权）` : "未启动"}`}
          />
          <span className="font-mono text-[11px] text-slate-400">{dsh.snapshot.settings_path}</span>
        </div>
        <div className="mb-3 rounded-md bg-slate-50 p-3">
          <div className="mb-1.5 text-xs font-medium text-slate-500">providers 与默认模型（快照）</div>
          <div className="space-y-1">
            {Object.entries(dsh.snapshot.providers).map(([name, p]) => (
              <div key={name} className="flex items-center gap-2 text-xs">
                <span className="w-20 font-mono text-gray-900">{name}</span>
                <span className="text-slate-500">{p.base_url}</span>
                <span className="text-slate-400">模型 {(p.models || []).join(" / ")}</span>
                <span
                  className={`ml-auto inline-flex items-center gap-1 ${
                    dsh.snapshot.env_keys[p.api_key_env || ""] ? "text-emerald-600" : "text-amber-600"
                  }`}
                >
                  <span className={`inline-block h-1.5 w-1.5 rounded-full ${dsh.snapshot.env_keys[p.api_key_env || ""] ? "bg-emerald-500" : "bg-amber-400"}`} />
                  {p.api_key_env} {dsh.snapshot.env_keys[p.api_key_env || ""] ? "已配置" : "未配置"}
                </span>
              </div>
            ))}
            <div className="border-t border-slate-200 pt-1.5 text-xs text-slate-600">
              当前默认路由：<span className="font-mono">{dsh.snapshot.default_model.provider || "-"} / {dsh.snapshot.default_model.model || "-"}</span>
            </div>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-2.5">
          <Field label="默认 Provider">
            <input className={inputClass} value={dshForm.default_provider} disabled={!isAdmin}
              onChange={(e) => setDshForm({ ...dshForm, default_provider: e.target.value })} />
          </Field>
          <Field label="默认模型">
            <input className={inputClass} value={dshForm.default_model} disabled={!isAdmin}
              onChange={(e) => setDshForm({ ...dshForm, default_model: e.target.value })} />
          </Field>
          <Field label="备选 Provider（容灾）">
            <input className={inputClass} value={dshForm.fallback_provider} disabled={!isAdmin}
              onChange={(e) => setDshForm({ ...dshForm, fallback_provider: e.target.value })} />
          </Field>
          <Field label="备选模型">
            <input className={inputClass} value={dshForm.fallback_model} disabled={!isAdmin}
              onChange={(e) => setDshForm({ ...dshForm, fallback_model: e.target.value })} />
          </Field>
          <Field label="超时（秒）">
            <input className={inputClass} type="number" value={dshForm.timeout_sec} disabled={!isAdmin}
              onChange={(e) => setDshForm({ ...dshForm, timeout_sec: Number(e.target.value) })} />
          </Field>
          <Field label="失败重试次数">
            <input className={inputClass} type="number" value={dshForm.max_retries} disabled={!isAdmin}
              onChange={(e) => setDshForm({ ...dshForm, max_retries: Number(e.target.value) })} />
          </Field>
          <Field label="产出目录（相对仓库根）" hint="dsh 产出沉淀位置，Connector/素材流程读取">
            <input className={inputClass} value={dshForm.output_dir} disabled={!isAdmin}
              onChange={(e) => setDshForm({ ...dshForm, output_dir: e.target.value })} />
          </Field>
        </div>
        <div className="mt-3 flex items-center gap-3">
          <label className="flex items-center gap-2 text-sm text-slate-600">
            <input type="checkbox" checked={applyToDsh} disabled={!isAdmin}
              onChange={(e) => setApplyToDsh(e.target.checked)} />
            同时写回 dsh 默认模型（自动备份原 settings.yaml）
          </label>
          <Button className="ml-auto" disabled={!isAdmin || saveDsh.isPending} onClick={() => saveDsh.mutate()}>
            {saveDsh.isPending ? "保存中…" : "保存 dsh 配置"}
          </Button>
        </div>
        {dshMsg && (
          <div className={`mt-2 rounded-md px-3 py-2 text-xs ${dshMsg.includes("失败") ? "bg-rose-50 text-rose-700" : "bg-emerald-50 text-emerald-700"}`}>
            {dshMsg}
          </div>
        )}
      </Panel>

      <Panel title="技能扫描目录" desc="留空使用默认（~/.agents/skills 与 ~/.zcode/skills）；配置后以自定义目录为准。">
        <div className="mb-2 space-y-1.5">
          {skillDirs.length === 0 && (
            <p className="text-xs text-slate-400">
              未配置 → 扫描默认目录，共发现 {plugins.skills.length} 个技能。
            </p>
          )}
          {skillDirs.map((d, i) => (
            <div key={d + i} className="flex items-center justify-between rounded-md border border-slate-200 px-3 py-1.5">
              <span className="break-all font-mono text-xs text-slate-700">{d}</span>
              <Button size="sm" variant="ghost" disabled={!isAdmin}
                onClick={() => setSkillDirs(skillDirs.filter((_, j) => j !== i))}>
                移除
              </Button>
            </div>
          ))}
        </div>
        <div className="flex gap-2">
          <input className={inputClass} placeholder="新增扫描目录（绝对路径，支持 ~）" value={newDir}
            onChange={(e) => setNewDir(e.target.value)} />
          <Button variant="secondary" disabled={!isAdmin || !newDir.trim()}
            onClick={() => {
              setSkillDirs([...skillDirs, newDir.trim()]);
              setNewDir("");
            }}>
            添加
          </Button>
        </div>
      </Panel>

      <Panel title="MCP 服务登记" desc="登记 MCP server 地址供工作流节点引用；连通性检测为 V2。">
        <div className="space-y-2">
          {mcp.length === 0 && <p className="text-xs text-slate-400">暂未登记 MCP 服务。</p>}
          {mcp.map((m, i) => (
            <div key={m.name + i} className="flex items-center justify-between rounded-md border border-slate-200 px-3 py-2">
              <div className="text-sm">
                <span className="font-medium">{m.name}</span>
                <span className="ml-2 font-mono text-xs text-slate-400">{m.url}</span>
              </div>
              <div className="flex items-center gap-2">
                {m.enabled ? <StatusBadge status="active" /> : <StatusBadge status="draft" />}
                <Button size="sm" variant="ghost" disabled={!isAdmin} onClick={() => setMcp(mcp.filter((_, j) => j !== i))}>
                  移除
                </Button>
              </div>
            </div>
          ))}
          <div className="flex gap-2">
            <input className={`${inputClass} w-40`} placeholder="名称，如 browser" value={newMcp.name}
              onChange={(e) => setNewMcp({ ...newMcp, name: e.target.value })} />
            <input className={inputClass} placeholder="http(s):// 地址" value={newMcp.url}
              onChange={(e) => setNewMcp({ ...newMcp, url: e.target.value.trim() })} />
            <Button variant="secondary" disabled={!isAdmin || !newMcp.name || !newMcp.url}
              onClick={() => {
                setMcp([...mcp, { name: newMcp.name.trim(), url: newMcp.url, enabled: true }]);
                setNewMcp({ name: "", url: "" });
              }}>
              添加
            </Button>
          </div>
        </div>
      </Panel>

      <Panel
        title={`本机技能库（当前发现 ${plugins.skills.length} 个）`}
        desc="勾选启用后可在内容任务工作流里引用；目录在上方可配置。"
      >
        <div className="mb-3 flex gap-2">
          <input className={inputClass} placeholder="搜索技能（wewrite / dbs / …）" value={filter}
            onChange={(e) => setFilter(e.target.value)} />
          <Button disabled={!isAdmin || save.isPending} onClick={() => save.mutate()}>
            {save.isPending ? "保存中…" : `保存（启用 ${enabled.length} / 目录 ${skillDirs.length || "默认"}）`}
          </Button>
        </div>
        {error && <ErrorBanner message={error} />}
        <div className="max-h-96 space-y-1 overflow-y-auto">
          {filtered.map((s) => (
            <label key={s.name} className="flex cursor-pointer items-start gap-2.5 rounded-md border border-slate-100 px-3 py-2 hover:bg-slate-50">
              <input type="checkbox" className="mt-1" checked={enabled.includes(s.name)} disabled={!isAdmin}
                onChange={() => toggleSkill(s.name)} />
              <span className="min-w-0">
                <span className="text-sm font-medium text-slate-800">{s.name}</span>
                <span className="block truncate text-xs text-slate-400">{s.description || s.path}</span>
              </span>
            </label>
          ))}
        </div>
      </Panel>
    </div>
  );
}

// ---------- 数据与队列 / 存储 / 安全 / 身份 / 关于（保持原有） ----------

function DataPanel({ settings, health }: { settings: SettingsView; health?: HealthView }) {
  const { database, queue } = settings;
  return (
    <div className="space-y-4">
      <Panel title="数据库" desc="默认 SQLite 零依赖；生产用 PostgreSQL（make migrate 建表）。">
        <div className="divide-y divide-slate-100">
          <Row label="连接串（已脱敏）">{database.url}</Row>
          <Row label="驱动">{database.driver}</Row>
        </div>
        <div className="mt-3 flex gap-4">
          <Dot ok={!!health?.db} label={`DB 探针${health ? (health.db ? " · 正常" : " · 异常") : ""}`} />
        </div>
      </Panel>
      <Panel title="异步队列（Celery）" desc=".env 设 TASK_QUEUE_ENABLED=true 后生成/拉取走队列，接口契约不变。">
        <div className="mb-3 flex items-center gap-2">
          <StatusBadge status={queue.enabled ? "active" : "draft"} />
          <span className="text-xs text-slate-400">{queue.enabled ? "已启用，worker 消费" : "未启用（同步执行）"}</span>
        </div>
        <div className="divide-y divide-slate-100">
          <Row label="Broker（已脱敏）">{queue.broker}</Row>
          <Row label="队列">
            <span className="flex flex-wrap justify-end gap-1.5">
              {queue.queues.map((q) => (
                <span key={q} className="rounded border border-slate-200 bg-slate-50 px-1.5 py-0.5">
                  {q}
                </span>
              ))}
            </span>
          </Row>
        </div>
      </Panel>
    </div>
  );
}

function StoragePanel({ settings }: { settings: SettingsView }) {
  const s = settings.storage;
  return (
    <Panel title="对象存储（MinIO / S3）" desc="默认关闭，导出内容内联返回；开启后导出产物另传存储并返回预签名 URL。">
      <div className="mb-3 flex items-center gap-2">
        <StatusBadge status={s.enabled ? "active" : "draft"} />
        <span className="text-xs text-slate-400">{s.enabled ? "已启用" : "未启用（可降级）"}</span>
      </div>
      <div className="divide-y divide-slate-100">
        <Row label="Endpoint">{s.endpoint}</Row>
        <Row label="Bucket">{s.bucket}</Row>
        <Row label="HTTPS">{s.secure ? "true" : "false（本机 MinIO）"}</Row>
        <Row label="Access Key">{s.access_key.configured ? s.access_key.masked : <span className="text-slate-400">未配置</span>}</Row>
        <Row label="预签名有效期">{s.url_expiry_hours} 小时</Row>
      </div>
    </Panel>
  );
}

function SecurityPanel({ settings }: { settings: SettingsView }) {
  const s = settings.security;
  return (
    <div className="space-y-4">
      <Panel title="SSRF 防护" desc="URL 抓取与 Connector 默认禁私网地址；LOCAL_DOCS_ALLOWLIST 控制本地文档数据源。">
        <div className="divide-y divide-slate-100">
          <Row label="私网放行">
            {s.ssrf_allow_private ? (
              <span className="inline-flex items-center gap-2">
                <StatusBadge status="warning" />
                <span className="text-amber-600">已开启 · 仅限本机开发，生产必须关闭</span>
              </span>
            ) : (
              <span className="text-emerald-600">关闭（生产推荐）</span>
            )}
          </Row>
          <Row label="抓取超时">{s.url_fetch_timeout_seconds} 秒</Row>
          <Row label="抓取大小上限">{bytesLabel(s.url_fetch_max_bytes)}</Row>
        </div>
      </Panel>
      <Panel title="上传限制">
        <div className="divide-y divide-slate-100">
          <Row label="单文件上限">{bytesLabel(s.upload_max_bytes)}</Row>
        </div>
      </Panel>
    </div>
  );
}

function IdentityPanel() {
  const { data: users } = useQuery({ queryKey: ["users"], queryFn: () => api.get<UserRow[]>("/users") });
  const { data: me } = useQuery({ queryKey: ["me"], queryFn: () => api.get<Me>("/users/me") });
  const [selected, setSelected] = useState(currentUser());

  useEffect(() => {
    if (me) setSelected(me.email);
  }, [me]);

  function switchUser(email: string) {
    setCurrentUser(email);
    setSelected(email);
    window.location.reload();
  }

  return (
    <div className="space-y-4">
      <Panel title="当前身份（开发模式）" desc="V1 使用 Header 身份便于演示 RBAC；生产部署替换为标准身份框架。">
        {me && (
          <div className="rounded-md bg-slate-50 px-3 py-2 text-sm">
            {me.name} · {me.email} · <span className="font-medium text-gray-900">{me.role}</span>
          </div>
        )}
        <div className="mt-3 flex flex-wrap gap-2">
          {(users || []).map((u) => (
            <button
              key={u.email}
              onClick={() => switchUser(u.email)}
              className={`rounded-md border px-3 py-1.5 text-xs ${
                selected === u.email
                  ? "border-gray-900 bg-gray-100 text-gray-900"
                  : "border-slate-300 bg-white text-slate-600 hover:bg-slate-50"
              }`}
            >
              {u.role} · {u.email}
            </button>
          ))}
        </div>
      </Panel>
      <Panel title="角色权限矩阵">
        <div className="space-y-2">
          {Object.entries(ROLE_DESC).map(([role, desc]) => (
            <div key={role} className="flex gap-3 text-sm">
              <span className="w-20 shrink-0 font-mono text-xs text-gray-900">{role}</span>
              <span className="text-slate-600">{desc}</span>
            </div>
          ))}
        </div>
      </Panel>
    </div>
  );
}

function AboutPanel({ settings }: { settings: SettingsView }) {
  return (
    <div className="space-y-4">
      <Panel title="关于 AI Content Studio">
        <div className="divide-y divide-slate-100">
          <Row label="版本">{settings.app.version}</Row>
          <Row label="定位">事实驱动的内容生产中心（汇聚 / 生产 / 审核 / 导出）</Row>
          <Row label="主链路">Source → Fact → FactPack(冻结) → Topic → 生成 → FactCheck → Review → Export</Row>
        </div>
      </Panel>
      <Panel title="文档">
        <div className="space-y-1.5 text-sm text-slate-600">
          <p>· README：启动 / 关键决策 / 运维（监控、备份、Golden 评测）</p>
          <p>· HANDOVER.md：项目交接与待办</p>
          <p>· docs/E2E_TEST_REPORT_2026-09-17.md：全量测试报告</p>
        </div>
      </Panel>
    </div>
  );
}

// ---------- 页面骨架 ----------

export default function Settings() {
  const { data: settings } = useQuery({ queryKey: ["settings"], queryFn: () => api.get<SettingsView>("/settings") });
  const { data: health } = useQuery({ queryKey: ["health"], queryFn: () => api.get<HealthView>("/health") });
  const { data: me } = useQuery({ queryKey: ["me"], queryFn: () => api.get<Me>("/users/me") });
  const [section, setSection] = useState<SectionId>("model");

  return (
    <div className="mx-auto max-w-5xl p-8">
      <h1 className="text-xl font-semibold">设置</h1>
      <div className="mt-6 flex items-start gap-8">
        <aside className="sticky top-8 w-52 shrink-0 space-y-1">
          {SECTIONS.map((s) => (
            <button
              key={s.id}
              onClick={() => setSection(s.id)}
              className={`flex w-full items-center gap-2.5 rounded-md px-3 py-2 text-left text-sm transition-colors ${
                section === s.id
                  ? "bg-gray-100 text-gray-900"
                  : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
              }`}
            >
              <span className="w-4 text-center text-xs text-slate-400">{s.icon}</span>
              <span className="flex-1">
                {s.label}
                <span className="block text-[11px] font-normal text-slate-400">{s.desc}</span>
              </span>
            </button>
          ))}
        </aside>
        <div className="min-w-0 max-w-2xl flex-1">
          {!settings ? (
            <div className="rounded-lg border border-slate-200 bg-white p-5 text-sm text-slate-400">加载配置中…</div>
          ) : (
            <>
              {section === "model" && <ModelsPanel settings={settings} isAdmin={me?.role === "admin"} />}
              {section === "plugins" && <PluginsPanel settings={settings} isAdmin={me?.role === "admin"} />}
              {section === "data" && <DataPanel settings={settings} health={health} />}
              {section === "storage" && <StoragePanel settings={settings} />}
              {section === "security" && <SecurityPanel settings={settings} />}
              {section === "identity" && <IdentityPanel />}
              {section === "about" && <AboutPanel settings={settings} />}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
