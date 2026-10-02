import { useEffect, useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api, currentUser } from "../api";
import { Button, ErrorBanner, Field, Spinner, inputClass } from "../components/ui";

type Provider = { name: string; base_url: string; enabled: boolean; trusted_private_endpoint: string; api_key: { configured: boolean; masked: string } };
type Profile = { provider_id: string | null; model_id: string; enabled: boolean; chat: boolean };
type Catalog = { revision: number; providers: Record<string, Provider>; profiles: Record<string, Profile>; default_profile: string; routes: Record<string, string>; purposes: string[] };
const names: Record<string, string> = { generate: "内容生成", rewrite: "内容改写", fact_check: "事实核查", topic_discovery: "选题发现", discoverability: "可发现性分析", platform_adaptation: "渠道适配", text_master_edit: "文字工作台 AI 编辑" };

export default function ModelRegistrationSettings({ editable = false, view = "providers", onDirtyChange }: {
  editable?: boolean; view?: "providers" | "routes"; onDirtyChange?: (dirty: boolean) => void;
}) {
  const client = useQueryClient();
  const actor = currentUser();
  const key = ["model-registration", actor];
  const query = useQuery({ queryKey: key, queryFn: async () => {
    const received = await api.get<Catalog>("/settings/model-registration");
    const cached = client.getQueryData<Catalog>(key);
    return cached && cached.revision > received.revision ? cached : received;
  }, retry: false });
  const [draft, setDraft] = useState<Catalog | null>(null);
  const [secrets, setSecrets] = useState<Record<string, string>>({});
  const [clearKeys, setClearKeys] = useState<Record<string, boolean>>({});
  const [newId, setNewId] = useState("");
  const [providerId, setProviderId] = useState("");
  const [modelId, setModelId] = useState("");
  const [pendingModels, setPendingModels] = useState<{ provider_id: string; model_id: string }[]>([]);
  const [discovered, setDiscovered] = useState<Record<string, string[]>>({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);
  const [editingProvider, setEditingProvider] = useState<string | null>(null);
  const [showAdd, setShowAdd] = useState(false);
  const [showManual, setShowManual] = useState(false);
  const [changedAreas, setChangedAreas] = useState<string[]>([]);
  const mounted = useRef(true);
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);
  const value = draft ?? query.data;
  const dirty = !!draft || pendingModels.length > 0 || Object.values(secrets).some(Boolean) || Object.values(clearKeys).some(Boolean);
  const incompleteEntry = !!newId.trim() || !!modelId.trim();
  useEffect(() => { onDirtyChange?.(dirty || incompleteEntry); }, [dirty, incompleteEntry, onDirtyChange]);
  useEffect(() => () => onDirtyChange?.(false), [onDirtyChange]);
  function markChanged(area: string) { setSaved(false); setChangedAreas(areas => areas.includes(area) ? areas : [...areas, area]); }
  function updateProvider(id: string, patch: Partial<Provider>) {
    if (!value) return;
    markChanged("厂商与模型");
    setDraft({ ...value, providers: { ...value.providers, [id]: { ...value.providers[id], ...patch } } });
  }
  async function save() {
    if (!value || !editable) return;
    setBusy(true); setError(""); setSaved(false);
    try {
      const providers = Object.fromEntries(Object.entries(value.providers).map(([id, p]) => [id, { name: p.name, base_url: p.base_url, enabled: p.enabled, trusted_private_endpoint: p.trusted_private_endpoint, api_key: secrets[id] ?? "", clear_key: clearKeys[id] ?? false }]));
      const received = await api.put<Catalog>("/settings/model-registration", { expected_revision: value.revision, configuration: { providers, models: pendingModels, default_profile: value.default_profile, routes: value.routes } });
      if (!mounted.current || currentUser() !== actor) return;
      await client.cancelQueries({ queryKey: key, exact: true });
      if (!mounted.current || currentUser() !== actor) return;
      client.setQueryData(key, received);
      setDraft(null); setSecrets({}); setClearKeys({}); setPendingModels([]); setChangedAreas([]); setSaved(true);
      await client.invalidateQueries({ queryKey: ["model-capability-routing", actor] });
    } catch (caught) { if (mounted.current && currentUser() === actor) setError(caught instanceof Error ? caught.message : "保存失败，本地编辑保留"); }
    finally { if (mounted.current && currentUser() === actor) setBusy(false); }
  }
  async function discover(id: string) {
    setBusy(true); setError("");
    try {
      const result = await api.post<{ models: string[] }>(`/settings/model-registration/providers/${encodeURIComponent(id)}/models`);
      if (mounted.current && currentUser() === actor) setDiscovered(previous => ({ ...previous, [id]: result.models }));
    } catch (caught) { if (mounted.current && currentUser() === actor) setError(caught instanceof Error ? caught.message : "获取失败，可手动登记模型"); }
    finally { if (mounted.current && currentUser() === actor) setBusy(false); }
  }
  if (query.isPending) return <Spinner label="读取厂商与模型…" />;
  if (query.error || !value) return <ErrorBanner message="厂商配置读取失败" />;
  const options = Object.entries(value.profiles).filter(([, p]) => p.enabled && p.chat);
  const providerName = (id: string | null) => id ? value.providers[id]?.name || id : "原有配置";
  const modelName = (id: string) => value.profiles[id]?.model_id || id;
  const selector = (selected: string, change: (id: string) => void, defaultLabel: string, controlId?: string) => <select id={controlId} className={inputClass} value={selected} onChange={event => { markChanged("用途路由"); change(event.target.value); }}><option value="">{defaultLabel}</option>{selected && !options.some(([id]) => id === selected) && <option value={selected}>{modelName(selected)}（当前选择不可用）</option>}{options.map(([id, p]) => <option key={id} value={id}>{p.model_id || id} · {providerName(p.provider_id)}</option>)}</select>;
  const groups = [...new Set(Object.values(value.profiles).map(p => p.provider_id))];
  return <section className="min-w-0 space-y-5">
    <header className="flex flex-wrap items-start justify-between gap-3">
      <div><h3 className="text-base font-semibold text-slate-900">{view === "providers" ? "厂商与模型" : "用途路由"}</h3><p className="mt-1 text-sm text-slate-500">{view === "providers" ? "先连接厂商，再登记你要使用的模型。" : "设置默认模型，并为需要的功能单独指定模型。"}</p></div>
      {view === "providers" && <Button variant="secondary" disabled={!editable || busy} onClick={() => setShowAdd(!showAdd)}>{showAdd ? "收起添加" : "+ 添加厂商"}</Button>}
    </header>
    {!editable && <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-500">当前角色仅可查看配置。</p>}
    <fieldset disabled={busy || !editable} className="min-w-0 space-y-5">
      <div hidden={view !== "providers"} className="space-y-5">
        {showAdd && <div className="flex flex-wrap items-end gap-2 rounded-lg border border-slate-200 bg-slate-50 p-4">
          <div className="min-w-0 flex-1"><Field label="新厂商 ID" hint="用于稳定引用，如 cpa"><input className={inputClass} value={newId} onChange={e => setNewId(e.target.value)} /></Field></div>
          <Button disabled={!/^[A-Za-z0-9_.-]{1,100}$/.test(newId) || !!value.providers[newId]} onClick={() => { markChanged("厂商与模型"); setDraft({ ...value, providers: { ...value.providers, [newId]: { name: newId, base_url: "", enabled: true, trusted_private_endpoint: "", api_key: { configured: false, masked: "" } } } }); setEditingProvider(newId); setNewId(""); setShowAdd(false); }}>添加厂商</Button>
        </div>}
        <div className="overflow-hidden rounded-lg border border-slate-200">
          {Object.keys(value.providers).length === 0 && <p className="p-5 text-sm text-slate-500">尚未登记厂商。添加 API 地址和密钥后即可获取模型。</p>}
          {Object.entries(value.providers).map(([id, p]) => <article key={id} className="border-b border-slate-200 last:border-b-0">
            <div className="flex flex-wrap items-center justify-between gap-3 p-4">
              <div className="flex min-w-0 items-center gap-3"><span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-sm font-semibold text-slate-600">{(p.name || id).slice(0, 2).toUpperCase()}</span>
                <div className="min-w-0"><div className="flex flex-wrap items-center gap-2"><h4 className="text-sm font-semibold text-slate-800">{p.name || id}</h4><span className="rounded bg-slate-100 px-1.5 py-0.5 text-[11px] text-slate-500">{p.enabled ? "已启用" : "已停用"}</span></div>
                  <p className="mt-1 break-all text-xs text-slate-500">{p.base_url || "尚未填写 API 地址"}</p><p className="mt-1 text-xs text-slate-400">{p.api_key.configured ? "密钥已配置" : "密钥未配置"} · {Object.values(value.profiles).filter(m => m.provider_id === id).length} 个已登记模型</p>
                </div>
              </div>
              <div className="flex shrink-0 gap-2"><Button size="sm" variant="secondary" onClick={() => setEditingProvider(editingProvider === id ? null : id)}>{editingProvider === id ? "收起编辑" : "编辑"}</Button><Button size="sm" variant="ghost" disabled={dirty || !p.enabled || !p.api_key.configured} onClick={() => void discover(id)}>获取模型</Button></div>
            </div>
            {editingProvider === id && <div className="space-y-3 border-t border-slate-100 bg-slate-50/60 p-4">
              <div className="grid gap-3 sm:grid-cols-2"><Field label="厂商名称"><input className={inputClass} value={p.name} onChange={e => updateProvider(id, { name: e.target.value })} /></Field><Field label="API 根地址（含 /v1）"><input className={inputClass} value={p.base_url} onChange={e => { updateProvider(id, { base_url: e.target.value, trusted_private_endpoint: "" }); setDiscovered({}); }} /></Field></div>
              <Field label="API Key" hint={p.api_key.configured ? "密钥已配置，留空保持不变；不会回显明文。" : "填写厂商提供的访问密钥。"}><input type="password" autoComplete="new-password" className={inputClass} placeholder={p.api_key.configured ? "留空保留现有密钥" : "输入 API Key"} value={secrets[id] ?? ""} onChange={e => { markChanged("厂商与模型"); setSecrets({ ...secrets, [id]: e.target.value }); }} /></Field>
              <div className="flex flex-wrap gap-4"><label className="flex items-center gap-2 text-sm text-slate-600"><input type="checkbox" checked={p.enabled} onChange={e => updateProvider(id, { enabled: e.target.checked })} />启用厂商</label><label className="flex items-center gap-2 text-sm text-slate-600"><input type="checkbox" checked={clearKeys[id] ?? false} onChange={e => { markChanged("厂商与模型"); setClearKeys({ ...clearKeys, [id]: e.target.checked }); }} />明确清除此密钥</label></div>
              <details className="text-xs text-slate-500"><summary className="cursor-pointer py-1">连接安全与技术标识</summary><div className="mt-2 space-y-2"><p className="break-all">厂商 ID：{id} · OpenAI-compatible</p><label className="flex items-start gap-2 text-amber-800"><input className="mt-0.5" type="checkbox" checked={!!p.trusted_private_endpoint} onChange={e => updateProvider(id, { trusted_private_endpoint: e.target.checked ? p.base_url.replace(/\/+$/, "") : "" })} />此精确地址是我信任的局域网网关（HTTP 会明文传输密钥）</label></div></details>
            </div>}
            {discovered[id] && <div className="border-t border-slate-100 p-4"><p className="mb-2 text-xs text-slate-500">选中需要登记的模型，再点击下方保存。模型列表不代表能力已验证。</p><div className="max-h-64 space-y-2 overflow-y-auto">{discovered[id].map(model => <label className="flex items-start gap-2 text-sm" key={model}><input className="mt-1" type="checkbox" checked={pendingModels.some(m => m.provider_id === id && m.model_id === model) || Object.values(value.profiles).some(m => m.provider_id === id && m.model_id === model)} disabled={Object.values(value.profiles).some(m => m.provider_id === id && m.model_id === model)} onChange={e => { markChanged("厂商与模型"); setPendingModels(e.target.checked ? [...pendingModels, { provider_id: id, model_id: model }] : pendingModels.filter(m => !(m.provider_id === id && m.model_id === model))); }} /><span className="min-w-0 break-all">{model}</span></label>)}</div></div>}
          </article>)}
        </div>
        {dirty && <p className="text-xs text-slate-500">获取模型前，请先保存厂商与模型配置。</p>}
        <section className="space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-2"><h4 className="text-sm font-semibold text-slate-800">已登记模型 <span className="ml-1 font-normal text-slate-400">{Object.keys(value.profiles).length}</span></h4><Button size="sm" variant="ghost" onClick={() => setShowManual(!showManual)}>{showManual ? "收起补录" : "手动补录模型"}</Button></div>
          {showManual && <div className="grid items-end gap-3 rounded-lg border border-slate-200 bg-slate-50 p-4 sm:grid-cols-[1fr_2fr_auto]"><Field label="模型所属厂商"><select className={inputClass} value={providerId} onChange={e => setProviderId(e.target.value)}><option value="">选择厂商</option>{Object.entries(value.providers).map(([id, p]) => <option key={id} value={id}>{p.name || id}</option>)}</select></Field><Field label="准确模型 ID"><input className={inputClass} value={modelId} onChange={e => setModelId(e.target.value)} /></Field><Button disabled={!providerId || !/^[A-Za-z0-9_./:-]{1,160}$/.test(modelId)} onClick={() => { markChanged("厂商与模型"); setPendingModels([...pendingModels.filter(m => !(m.provider_id === providerId && m.model_id === modelId)), { provider_id: providerId, model_id: modelId }]); setModelId(""); }}>加入待保存</Button></div>}
          <div className="rounded-lg border border-slate-200">{groups.map(group => <div key={group ?? "legacy"} className="border-b border-slate-200 last:border-b-0"><p className="bg-slate-50/70 px-4 py-2 text-xs font-medium text-slate-500">{providerName(group)}</p>{Object.entries(value.profiles).filter(([, p]) => p.provider_id === group).map(([id, p]) => <div className="flex flex-wrap items-center justify-between gap-2 border-t border-slate-100 px-4 py-3" key={id}><div className="min-w-0"><p className="break-all text-sm font-medium text-slate-700">{p.model_id || id}</p><details className="mt-1 text-[11px] text-slate-400"><summary className="cursor-pointer">技术标识与声明</summary><p className="mt-1 break-all">{id} · {p.chat ? "聊天能力已声明" : "未声明聊天能力"} · 登记不代表调用已验证</p></details></div><div className="flex gap-2">{value.default_profile === id && <span className="rounded bg-slate-800 px-2 py-0.5 text-[11px] text-white">默认</span>}<span className="rounded bg-slate-100 px-2 py-0.5 text-[11px] text-slate-500">{p.enabled ? "启用" : "停用"}</span></div></div>)}</div>)}{groups.length === 0 && <p className="p-4 text-sm text-slate-500">还没有登记模型。</p>}</div>
          {pendingModels.length > 0 && <div className="rounded-md bg-amber-50 px-3 py-2 text-xs text-amber-800">待登记：{pendingModels.map(m => `${providerName(m.provider_id)} / ${m.model_id}`).join("、")}</div>}
        </section>
      </div>
      <div hidden={view !== "routes"} className="space-y-5">
        <div className="rounded-lg border border-slate-200 bg-slate-50/60 p-4"><Field label="全局默认模型" hint="没有单独选择模型的功能继承这个默认。">{selector(value.default_profile, id => setDraft({ ...value, default_profile: id }), "保留旧默认 / 环境配置")}</Field></div>
        <div className="divide-y divide-slate-100 rounded-lg border border-slate-200">{value.purposes.map(purpose => <div className="grid gap-2 px-4 py-4 sm:grid-cols-[minmax(0,1fr)_minmax(0,1.4fr)] sm:items-center" key={purpose}><label className="text-sm text-slate-700" htmlFor={`model-purpose-${purpose}`}>{names[purpose] ?? purpose}<span className="mt-1 block text-xs text-slate-400">{purpose === "text_master_edit" ? "未指定时继承内容改写，再继承默认" : "未指定时继承全局默认"}</span></label><div>{selector(value.routes[purpose] ?? "", id => setDraft({ ...value, routes: { ...value.routes, [purpose]: id } }), purpose === "text_master_edit" ? "继承改写选择 / 全局默认" : "继承全局默认", `model-purpose-${purpose}`)}</div></div>)}</div>
      </div>
    </fieldset>
    <footer className="space-y-3 border-t border-slate-200 pt-4">
      {error && <div role="alert"><ErrorBanner message={`${error}。本地编辑仍保留；可重新读取后再调整。`} /></div>}
      <div className="flex flex-wrap items-center justify-between gap-3"><div aria-live="polite" className="text-xs text-slate-500"><p className={dirty ? "font-medium text-amber-700" : saved ? "font-medium text-emerald-700" : ""}>{busy ? "正在处理…" : dirty ? `未保存 · ${changedAreas.join("、") || "厂商、模型与用途选择"}` : saved ? "配置已保存" : "与已保存配置一致"}</p><p className="mt-1">保存范围：厂商、登记模型、默认与用途路由 · 版本 {value.revision}</p>{incompleteEntry && <p className="mt-1 text-amber-700">正在输入的新条目需先点击添加，才会包含在保存中。</p>}</div>
        <div className="flex gap-2"><Button variant="ghost" disabled={busy} onClick={() => { if ((dirty || incompleteEntry) && !window.confirm("丢弃本地登记与用途草稿并重新读取？")) return; setDraft(null); setSecrets({}); setClearKeys({}); setPendingModels([]); setDiscovered({}); setChangedAreas([]); setNewId(""); setModelId(""); setSaved(false); setError(""); void query.refetch(); }}>重新读取</Button><Button disabled={busy || !editable || !dirty} onClick={() => void save()}>{busy ? "处理中…" : "保存模型设置"}</Button></div>
      </div>
    </footer>
  </section>;
}
