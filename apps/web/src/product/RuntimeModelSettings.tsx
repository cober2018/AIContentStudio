import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ReactNode, useEffect, useMemo, useState } from "react";
import { api } from "../api";
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
  base_url_redacted?: boolean;
  model: string;
  api_key: SecretView;
  mock_inject_unfact_number: boolean;
  overridden: boolean;
}

interface ModelProfileView {
  provider: string;
  base_url: string;
  base_url_redacted?: boolean;
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
  dsh: { url: string; reachable: boolean; status_code: number | null; status?: "not_probed" };
}

interface DshSnapshot {
  configured: boolean;
  settings_path: string;
  providers: Record<string, { api: string | null; base_url: string | null; api_key_env: string | null; models: string[] }>;
  default_model: { provider: string | null; model: string | null };
  env_keys: Record<string, boolean>;
}

interface ImageView {
  enabled: boolean;
  provider: string;
  model: string;
  base_url: string;
  base_url_redacted?: boolean;
  size: string;
  api_key: SecretView;
  providers_available: string[];
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
  image: ImageView;
  app: { version: string };
}

interface Me {
  id: number;
  email: string;
  name: string;
  role: string;
}

interface TestResult {
  ok: boolean;
  provider: string;
  model?: string;
  latency_ms?: number;
  reply?: string;
  error?: string;
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

function ImagePanel({ settings, isAdmin }: { settings: SettingsView; isAdmin: boolean }) {
  const queryClient = useQueryClient();
  const img = settings.image;
  const [form, setForm] = useState({
    enabled: img.enabled,
    provider: img.provider,
    model: img.model,
    base_url: img.base_url,
    api_key: "",
    size: img.size,
  });
  const [msg, setMsg] = useState("");
  useEffect(() => setForm({
    enabled: img.enabled, provider: img.provider, model: img.model,
    base_url: img.base_url, api_key: "", size: img.size,
  }), [img]);

  const save = useMutation({
    mutationFn: () => {
      if (img.base_url_redacted && !form.base_url.trim()) throw new Error("敏感地址已隐藏，请明确重新输入地址后再保存；旧配置未更改。");
      return api.put<ImageView>("/settings/image", form);
    },
    onSuccess: () => {
      setMsg(form.enabled ? "已保存并同步 wewrite 生图配置（cover 节点将真实出图）" : "已保存（生图关闭，cover 节点自动跳过）");
      queryClient.invalidateQueries({ queryKey: ["settings"] });
    },
    onError: (e) => setMsg(e instanceof Error ? e.message : "保存失败"),
  });

  return (
    <Panel title="AI 生图" desc="封面节点用；provider 可随时切换（Gemini 反带接入后在此切换即可），保存即同步 wewrite CLI 配置。">
      <div className="mb-3 flex items-center gap-2">
        {img.enabled ? <StatusBadge status="active" /> : <StatusBadge status="draft" />}
        <span className="text-xs text-slate-400">
          {img.enabled ? "已启用" : "未启用（cover 节点自动跳过）"} | Key {img.api_key.configured ? img.api_key.masked : "未配置"}
        </span>
      </div>
      <div className="grid grid-cols-2 gap-2.5">
        <Field label="Provider">
          <select className={inputClass} value={form.provider} disabled={!isAdmin}
            onChange={(e) => setForm({ ...form, provider: e.target.value })}>
            {img.providers_available.map((p) => (
              <option key={p} value={p}>{p}{p === "gemini" ? "（nano-banana 图像原生）" : p === "minimax" ? "（image-01）" : ""}</option>
            ))}
          </select>
        </Field>
        <Field label="模型" hint={form.provider === "minimax" ? "默认 image-01" : form.provider === "gemini" ? "如 gemini-3.1-flash-image-preview" : ""}>
          <input className={inputClass} value={form.model} disabled={!isAdmin}
            onChange={(e) => setForm({ ...form, model: e.target.value })} />
        </Field>
        {((form.provider !== "minimax" && form.provider !== "gemini") || img.base_url_redacted) && (
          <Field label="Base URL">
            <input className={inputClass} value={form.base_url} disabled={!isAdmin}
              onChange={(e) => setForm({ ...form, base_url: e.target.value })} />
          </Field>
        )}
        <Field label="尺寸" hint="宽x高，封面建议 1344x768（16:9）">
          <input className={inputClass} value={form.size} disabled={!isAdmin}
            onChange={(e) => setForm({ ...form, size: e.target.value })} />
        </Field>
        <Field label="API Key" hint={img.api_key.configured ? `已配置（${img.api_key.masked}），留空保持不变` : "对应平台的图像 API Key"}>
          <input className={inputClass} type="password" value={form.api_key} disabled={!isAdmin}
            placeholder={img.api_key.configured ? "留空保持不变" : "粘贴 Key"}
            onChange={(e) => setForm({ ...form, api_key: e.target.value })} />
        </Field>
        <label className="flex items-end gap-2 pb-1 text-sm text-slate-600">
          <input type="checkbox" checked={form.enabled} disabled={!isAdmin}
            onChange={(e) => setForm({ ...form, enabled: e.target.checked })} />
          启用生图
        </label>
      </div>
      {msg && <div className="mt-2 rounded-md bg-slate-50 px-3 py-2 text-xs text-slate-600">{msg}</div>}
      {img.base_url_redacted && !form.base_url.trim() && <p role="alert" className="mt-2 text-sm text-amber-800">地址含敏感信息，已隐藏；明确重新输入地址后才能保存。</p>}
      <Button className="mt-3" disabled={!isAdmin || save.isPending} onClick={() => save.mutate()}>
        {save.isPending ? "保存中…" : "保存生图配置"}
      </Button>
    </Panel>
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
    mutationFn: () => {
      if (llm.base_url_redacted && !form.base_url.trim()) throw new Error("敏感地址已隐藏，请明确重新输入地址后再保存；旧配置未更改。");
      return api.put<LLMView>("/settings/llm", form);
    },
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
      {
      if (llm.base_url_redacted && (!editing || !form.base_url.trim())) throw new Error("敏感地址已隐藏，请进入编辑并明确重新输入地址后再测试。");
      return api.post<TestResult>("/settings/llm/test", {
        provider: form.provider,
        base_url: form.base_url,
        model: form.model,
        api_key: editing && form.api_key ? form.api_key : undefined,
      });
      },
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
      {llm.base_url_redacted && <p role="alert" className="mb-3 text-sm text-amber-800">连接地址含敏感信息，已隐藏；保存或测试前须明确重新输入。</p>}
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
            {(form.provider === "openai_compatible" || llm.base_url_redacted) && (
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
            label={`dsh :3080 ${plugins.dsh.status === "not_probed" ? "尚未探测（读取配置不检测连接）" : plugins.dsh.reachable ? `在线（HTTP ${plugins.dsh.status_code}，token 鉴权）` : "未启动"}`}
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

// Still read at runtime: the default model behind every route, the image provider, dsh and skill folders.
export default function RuntimeModelSettings() {
  const { data: settings } = useQuery({ queryKey: ["settings"], queryFn: () => api.get<SettingsView>("/settings") });
  const { data: me } = useQuery({ queryKey: ["me"], queryFn: () => api.get<Me>("/users/me") });
  if (!settings) return <div className="rounded-lg border border-slate-200 bg-white p-5 text-sm text-slate-400">加载配置中…</div>;
  const isAdmin = me?.role === "admin";
  return <div className="space-y-4">
    <DefaultLLMPanel settings={settings} isAdmin={isAdmin} />
    <ImagePanel settings={settings} isAdmin={isAdmin} />
    <PluginsPanel settings={settings} isAdmin={isAdmin} />
  </div>;
}
