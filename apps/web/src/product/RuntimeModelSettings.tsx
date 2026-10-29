import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ReactNode, useEffect, useMemo, useState } from "react";
import { api } from "../api";
import { Button, ErrorBanner, inputClass, StatusBadge } from "../components/ui";

// 技能与 MCP：本机技能目录、启用集与 MCP 登记。模型厂商、密钥和用途只在 厂商与模型 / 用途路由 配置。

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
}

interface SettingsView {
  plugins: PluginsView;
}

interface Me {
  id: number;
  email: string;
  name: string;
  role: string;
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

function PluginsPanel({ settings, isAdmin }: { settings: SettingsView; isAdmin: boolean }) {
  const queryClient = useQueryClient();
  const plugins = settings.plugins;
  const [filter, setFilter] = useState("");
  const [enabled, setEnabled] = useState<string[]>(plugins.skills_enabled);
  const [mcp, setMcp] = useState<McpEntry[]>(plugins.mcp);
  const [skillDirs, setSkillDirs] = useState<string[]>(plugins.skill_dirs);
  const [newDir, setNewDir] = useState("");
  const [newMcp, setNewMcp] = useState({ name: "", url: "" });
  const [error, setError] = useState("");

  useEffect(() => {
    setEnabled(plugins.skills_enabled);
    setMcp(plugins.mcp);
    setSkillDirs(plugins.skill_dirs);
  }, [plugins]);

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

  function toggleSkill(name: string) {
    setEnabled(enabled.includes(name) ? enabled.filter((n) => n !== name) : [...enabled, name]);
  }

  return (
    <div className="space-y-4">
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

export default function RuntimeModelSettings() {
  const { data: settings } = useQuery({ queryKey: ["settings"], queryFn: () => api.get<SettingsView>("/settings") });
  const { data: me } = useQuery({ queryKey: ["me"], queryFn: () => api.get<Me>("/users/me") });
  if (!settings) return <div className="rounded-lg border border-slate-200 bg-white p-5 text-sm text-slate-400">加载配置中…</div>;
  return <PluginsPanel settings={settings} isAdmin={me?.role === "admin"} />;
}
