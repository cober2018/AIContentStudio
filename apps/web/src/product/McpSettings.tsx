import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { api, ApiError, currentUser } from "../api";
import { Button, Chip, ErrorBanner, Field, Spinner, inputClass } from "../components/ui";

type Tool = { name: string; description: string; summary: string | null; read_only: boolean; group: string };
type External = { name: string; url: string; enabled: boolean };
type View = {
  server_name: string; enabled: boolean; token_configured: boolean; owner: { id: number; email: string; role: string; active: boolean } | null;
  endpoint: string; loopback_only: boolean; bridge: string; runtime_env: string; config_keys: string[];
  clients: { codex: string; claude_code: string }; groups: { key: string; label: string }[]; tools: Tool[]; cannot: string[]; loop: string[];
  external: { mcp: External[]; skill_dirs: string[]; skills_enabled: string[] };
};
type Check = { ok: boolean; checks: { key: string; label: string; ok: boolean; reason: string | null; count?: number }[] };

function Snippet({ title, text, hint }: { title: string; text: string; hint: string }) {
  const [copied, setCopied] = useState(false);
  return <div className="space-y-2">
    <div className="flex items-center justify-between gap-2"><p className="text-sm font-medium text-ink-800">{title}</p>
      <Button size="sm" variant="secondary" onClick={() => void navigator.clipboard.writeText(text).then(() => { setCopied(true); setTimeout(() => setCopied(false), 1500); })}>{copied ? "已复制" : "复制"}</Button></div>
    <pre className="overflow-x-auto whitespace-pre rounded-lg bg-slate-900 p-3 font-mono text-[12px] leading-relaxed text-slate-100">{text}</pre>
    <p className="text-xs text-ink-500">{hint}</p>
  </div>;
}

function ExternalServices({ initial, onDirtyChange, onSaved }: { initial: View["external"]; onDirtyChange: (dirty: boolean) => void; onSaved: () => void }) {
  const [rows, setRows] = useState<External[]>(initial.mcp);
  const [state, setState] = useState<{ busy?: boolean; error?: string; saved?: boolean }>({});
  const dirty = JSON.stringify(rows) !== JSON.stringify(initial.mcp);
  useEffect(() => { onDirtyChange(dirty); }, [dirty, onDirtyChange]);
  const update = (index: number, patch: Partial<External>) => setRows(current => current.map((row, i) => i === index ? { ...row, ...patch } : row));
  const save = async () => {
    setState({ busy: true });
    try {
      // The plugins endpoint replaces skills and MCP together, so the current skill settings are sent back unchanged.
      await api.put("/settings/plugins", { skill_dirs: initial.skill_dirs, skills_enabled: initial.skills_enabled, mcp: rows });
      setState({ saved: true }); onSaved();
    } catch (error) { setState({ error: error instanceof ApiError ? error.message : "保存失败" }); }
  };
  return <section className="space-y-3 rounded-xl border border-slate-200 bg-white p-5">
    <div><h2 className="font-semibold">平台调用的外部 MCP 服务</h2><p className="mt-1 text-sm text-slate-600">登记后工作流节点可以引用；这里只保存地址，不会自动连接或探测。与旧设置页是同一份数据。</p></div>
    {rows.length === 0 && <p className="text-sm text-slate-500">还没有登记外部 MCP 服务。</p>}
    {rows.map((row, index) => <div key={index} className="grid gap-2 sm:grid-cols-[minmax(0,1fr)_minmax(0,2fr)_auto_auto] sm:items-end">
      <Field label="名称"><input className={inputClass} value={row.name} maxLength={100} onChange={event => update(index, { name: event.target.value })} /></Field>
      <Field label="地址（http/https）"><input className={inputClass} value={row.url} maxLength={500} onChange={event => update(index, { url: event.target.value })} /></Field>
      <label className="flex items-center gap-1.5 pb-2 text-sm"><input type="checkbox" checked={row.enabled} onChange={event => update(index, { enabled: event.target.checked })} />启用</label>
      <Button size="sm" variant="ghost" onClick={() => setRows(current => current.filter((_, i) => i !== index))}>删除</Button>
    </div>)}
    {state.error && <ErrorBanner message={state.error} />}
    <div className="flex flex-wrap items-center gap-2">
      <Button size="sm" variant="secondary" onClick={() => setRows(current => [...current, { name: "", url: "", enabled: true }])}>新增服务</Button>
      <Button size="sm" disabled={!dirty || state.busy} onClick={() => void save()}>{state.busy ? "保存中…" : "保存"}</Button>
      {state.saved && !dirty && <span className="text-xs text-emerald-700">已保存</span>}
    </div>
  </section>;
}

export default function McpSettings({ onDirtyChange }: { onDirtyChange: (dirty: boolean) => void }) {
  const view = useQuery({ queryKey: ["mcp-settings", currentUser()], queryFn: () => api.get<View>("/settings/mcp"), retry: false });
  const [check, setCheck] = useState<{ busy?: boolean; result?: Check; error?: string }>({});
  const runCheck = async () => {
    setCheck({ busy: true });
    try { setCheck({ result: await api.post<Check>("/settings/mcp/check") }); }
    catch (error) { setCheck({ error: error instanceof ApiError ? error.message : "检测失败" }); }
  };
  if (view.isPending) return <Spinner label="读取 MCP 接入…" />;
  if (view.isError || !view.data) return <ErrorBanner message={view.error instanceof ApiError && view.error.status === 403 ? "只有管理员可以查看 MCP 接入。" : "MCP 接入读取失败。"} />;
  const data = view.data;
  return <div className="space-y-5">
    <section className="space-y-4 rounded-xl border border-slate-200 bg-white p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div><h2 className="font-semibold">平台 MCP · {data.server_name}</h2><p className="mt-1 text-sm text-slate-600">大模型（Claude Code、Codex）通过它操作平台：跑生产阶段、找素材、读你在平台上的决定。它不能替你做决定。</p></div>
        <Chip tone={data.enabled ? "good" : "warn"}>{data.enabled ? "已启用" : "未启用"}</Chip>
      </div>
      <dl className="space-y-1.5 text-sm">
        <div className="flex flex-col gap-0.5 sm:flex-row sm:gap-4"><dt className="shrink-0 text-slate-500 sm:w-28">代理账号</dt><dd className="min-w-0">{data.owner ? `${data.owner.email} · ${data.owner.role}${data.owner.active ? "" : " · 已停用"}` : "未配置"}</dd></div>
        <div className="flex flex-col gap-0.5 sm:flex-row sm:gap-4"><dt className="shrink-0 text-slate-500 sm:w-28">访问令牌</dt><dd className="min-w-0">{data.token_configured ? "已配置（不在页面显示）" : `未配置：在运行配置里设置 ${data.config_keys.join("、")}`}</dd></div>
        <div className="flex flex-col gap-0.5 sm:flex-row sm:gap-4"><dt className="shrink-0 text-slate-500 sm:w-28">接口</dt><dd className="min-w-0 font-mono text-[12.5px]">{data.endpoint}{data.loopback_only ? " · 仅本机" : ""}</dd></div>
        <div className="flex flex-col gap-0.5 sm:flex-row sm:gap-4"><dt className="shrink-0 text-slate-500 sm:w-28">本地连接脚本</dt><dd className="min-w-0 break-all font-mono text-[12.5px]">{data.bridge}</dd></div>
        <div className="flex flex-col gap-0.5 sm:flex-row sm:gap-4"><dt className="shrink-0 text-slate-500 sm:w-28">运行配置文件</dt><dd className="min-w-0 break-all font-mono text-[12.5px]">{data.runtime_env}</dd></div>
      </dl>
      <div className="flex flex-wrap items-center gap-3"><Button size="sm" disabled={check.busy} onClick={() => void runCheck()}>{check.busy ? "检测中…" : "检测连接"}</Button><span className="text-xs text-slate-500">只在本机核对配置、账号和工具清单，不联网，不显示令牌。</span></div>
      {check.error && <ErrorBanner message={check.error} />}
      {check.result && <ul className="space-y-1 text-sm">{check.result.checks.map(item => <li key={item.key} className={item.ok ? "text-emerald-800" : "text-rose-800"}>{item.ok ? "✓" : "✗"} {item.label}{item.count ? `（${item.count} 个工具）` : ""}{item.reason ? ` · ${item.reason}` : ""}</li>)}</ul>}
    </section>

    <section className="space-y-4 rounded-xl border border-slate-200 bg-white p-5">
      <h2 className="font-semibold">怎么连接</h2>
      <Snippet title="Claude Code" text={data.clients.claude_code} hint="在项目目录的终端里运行一次；之后新开会话或用 /mcp 重连即可使用。" />
      <Snippet title="Codex（~/.codex/config.toml）" text={data.clients.codex} hint="追加到 Codex 配置文件；阶段生成可能要几分钟，所以工具超时设为 360 秒。" />
    </section>

    <section className="space-y-4 rounded-xl border border-slate-200 bg-white p-5">
      <div><h2 className="font-semibold">能做什么（{data.tools.length} 个工具）</h2><p className="mt-1 text-sm text-slate-600">清单直接读平台注册表，新增工具会自动出现。</p></div>
      <div className="rounded-lg bg-slate-50 p-3 text-sm"><p className="font-medium text-slate-800">推荐流程</p><ol className="mt-1 list-decimal space-y-0.5 pl-5 text-slate-700">{data.loop.map(step => <li key={step}>{step}</li>)}</ol></div>
      {data.groups.map(group => {
        const tools = data.tools.filter(tool => tool.group === group.key);
        if (!tools.length) return null;
        return <div key={group.key}><p className="text-sm font-medium text-slate-800">{group.label}</p>
          <ul className="mt-2 divide-y divide-slate-100 rounded-lg border border-slate-200">{tools.map(tool => <li key={tool.name} className="flex flex-wrap items-start gap-x-3 gap-y-1 px-3 py-2">
            <code className="font-mono text-[12.5px] text-slate-900">{tool.name}</code>
            <Chip tone={tool.read_only ? "neutral" : "info"}>{tool.read_only ? "只读" : "会改动"}</Chip>
            <p className="w-full text-xs text-slate-600" title={tool.description}>{tool.summary ?? tool.description}</p>
          </li>)}</ul></div>;
      })}
      <div className="rounded-lg border border-rose-200 bg-rose-50/60 p-3 text-sm"><p className="font-medium text-rose-900">MCP 不能做的事（只能你在平台上操作）</p><ul className="mt-1 list-disc space-y-0.5 pl-5 text-rose-900">{data.cannot.map(item => <li key={item}>{item}</li>)}</ul></div>
    </section>

    <ExternalServices key={JSON.stringify(data.external.mcp)} initial={data.external} onDirtyChange={onDirtyChange} onSaved={() => void view.refetch()} />
  </div>;
}
