import { useEffect, useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api, ApiError, currentUser } from "../api";
import { retargetPlugin } from "./modelRoutingState";
import { Button, ErrorBanner, Field, Spinner, inputClass } from "../components/ui";

const capabilities = ["chat", "image_generation", "video_generation", "tts", "asr"] as const;
type Capability = typeof capabilities[number];
const labels: Record<Capability, string> = { chat: "聊天", image_generation: "生图", video_generation: "生视频", tts: "语音生成", asr: "语音识别" };
type Binding = { adapter_key: string; adapter_version: string; model_id: string; base_url: string; credential_ref: string };
type State = { declared: boolean; configured: boolean; executable: boolean; verified: boolean; reason: string };
type Profile = { enabled?: boolean; declared_capabilities: Capability[]; capability_bindings: Partial<Record<Capability, Binding>>; capabilities: Record<Capability, State> };
type Limit = { max_items: number; max_pixels?: number | null; max_seconds?: number | null; max_tokens?: number | null; timeout_seconds: number; max_cost?: number | null; currency?: "USD" | "CNY" | null };
type Configuration = { revision: number; profiles: Record<string, Profile>; media_plugins: Record<string, { enabled: boolean; capability: Capability; model_profile_id: string }>; capability_routes: Partial<Record<Capability, string[]>>; policies: { allow_automatic_fallback: boolean; limits: Partial<Record<Capability, Limit>> } };
type Catalog = { revision: number; providers: Record<string, { name: string }>; profiles: Record<string, { provider_id: string | null; model_id: string; chat: boolean }> };
type Preview = { status: string; reason: string; plugin_id?: string; execution_profile?: string };
type Props = { editable?: boolean; onDirtyChange?: (dirty: boolean) => void };
const disclosureClass = "cursor-pointer rounded-md text-sm font-medium text-slate-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-slate-500";

export default function ModelRoutingSettings(props: Props) {
  const identity = currentUser();
  return <ModelRoutingEditor key={identity} {...props} identity={identity} />;
}

function ModelRoutingEditor({ editable = false, onDirtyChange, identity }: Props & { identity: string }) {
  const queryClient = useQueryClient();
  const queryKey = ["model-capability-routing", identity];
  const query = useQuery({ queryKey, queryFn: async () => {
    const received = await api.get<Configuration>("/settings/model-capabilities");
    const cached = queryClient.getQueryData<Configuration>(queryKey);
    return cached && cached.revision > received.revision ? cached : received;
  }, retry: false });
  const catalogKey = ["model-registration", identity];
  const catalog = useQuery({ queryKey: catalogKey, queryFn: async () => {
    const received = await api.get<Catalog>("/settings/model-registration");
    const cached = queryClient.getQueryData<Catalog>(catalogKey);
    return cached && cached.revision > received.revision ? cached : received;
  }, retry: false });
  const [draft, setDraft] = useState<Configuration | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [name, setName] = useState("");
  const [pluginName, setPluginName] = useState("");
  const [preview, setPreview] = useState<(Preview & { selected_profile: string }) | null>(null);
  const [previewBusy, setPreviewBusy] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const mounted = useRef(false);
  const previewRequest = useRef(0);
  useEffect(() => {
    mounted.current = true;
    return () => { mounted.current = false; };
  }, []);
  const dirty = !!draft;
  const incompleteEntry = !!name.trim() || !!pluginName.trim();
  useEffect(() => {
    onDirtyChange?.(dirty || incompleteEntry);
    return () => { onDirtyChange?.(false); };
  }, [dirty, incompleteEntry, onDirtyChange]);
  const value = draft ?? query.data;
  const isCurrent = () => mounted.current && currentUser() === identity;
  const update = (next: Configuration) => {
    if (!editable || busy || !isCurrent()) return;
    setDraft(next); setPreview(null); setSaved(false);
    previewRequest.current += 1; setPreviewBusy(null);
  };
  async function save() {
    if (!value || !editable || busy || !draft || !isCurrent()) return;
    setBusy(true); setError("");
    setSaved(false); setPreview(null); previewRequest.current += 1; setPreviewBusy(null);
    try {
      const profiles = Object.fromEntries(Object.entries(value.profiles).map(([key, profile]) => [key, { enabled: profile.enabled ?? true, declared_capabilities: profile.declared_capabilities, capability_bindings: profile.capability_bindings }]));
      const routes = Object.fromEntries(Object.entries(value.capability_routes).map(([cap, ids]) => [cap, ids.filter(Boolean)]));
      const result = await api.put<Configuration>("/settings/model-capabilities", { expected_revision: value.revision, configuration: { profiles, media_plugins: value.media_plugins, capability_routes: routes, policies: value.policies } });
      if (!isCurrent()) return;
      if (result.revision <= value.revision) { setError("保存版本未推进，本地编辑仍保留；请核对当前配置。"); return; }
      await queryClient.cancelQueries({ queryKey, exact: true });
      if (!isCurrent()) return;
      queryClient.setQueryData(queryKey, result);
      await queryClient.invalidateQueries({ queryKey: ["model-registration", identity] });
      if (!isCurrent()) return;
      setDraft(null); setPreview(null);
      setSaved(true);
    } catch (caught) {
      if (isCurrent()) setError(caught instanceof ApiError && caught.status === 409
        ? "配置版本已变化，保存被拒绝；本地编辑仍保留。可核对草稿后选择重新读取，不会自动覆盖。"
        : `${caught instanceof Error ? caught.message : "保存失败"}；本地编辑仍保留。`);
    } finally { if (isCurrent()) setBusy(false); }
  }
  async function plan(id: string) {
    if (!editable || busy || draft || previewBusy || !isCurrent()) return;
    const request = ++previewRequest.current;
    setError(""); setPreview(null); setPreviewBusy(id);
    try {
      const result = await api.post<Preview>("/settings/model-capabilities/plan", { capability: "image_generation", selected_profile: id, parameters: {} });
      if (isCurrent() && request === previewRequest.current) setPreview({ ...result, selected_profile: id });
    } catch (caught) {
      if (isCurrent() && request === previewRequest.current) setError(caught instanceof Error ? caught.message : "规划失败");
    } finally { if (isCurrent() && request === previewRequest.current) setPreviewBusy(null); }
  }
  if (query.isPending) return <Spinner label="读取模型能力配置…" />;
  if (query.error) return <ErrorBanner message="模型能力编辑当前仅管理员可用，或配置读取失败。" />;
  if (!value) return null;
  const modelTitle = (id: string) => {
    const registered = catalog.data?.profiles[id];
    const providerName = registered?.provider_id ? catalog.data?.providers[registered.provider_id]?.name : undefined;
    const bindingModel = Object.values(value.profiles[id]?.capability_bindings ?? {}).find(binding => binding?.model_id)?.model_id;
    const title = registered?.model_id || bindingModel || id;
    return providerName ? `${title} · ${providerName}` : title;
  };
  const changedSections = draft && query.data ? [
    JSON.stringify(draft.profiles) !== JSON.stringify(query.data.profiles) ? "模型能力与绑定" : "",
    JSON.stringify(draft.media_plugins) !== JSON.stringify(query.data.media_plugins) ? "生成插件" : "",
    JSON.stringify(draft.capability_routes) !== JSON.stringify(query.data.capability_routes) ? "回退顺序" : "",
    JSON.stringify(draft.policies) !== JSON.stringify(query.data.policies) ? "回退开关与限额" : "",
  ].filter(Boolean) : [];
  return <section className="min-w-0 space-y-5 text-slate-700" aria-label="模型能力与生成配置">
    <header className="space-y-1">
      <h3 className="text-base font-semibold text-slate-900">生成能力与插件</h3>
      <p className="text-sm text-slate-500">先声明模型能力，再配置对应接口或插件。聊天登记与媒体能力分开判断；保存和路由预览不会请求供应商。</p>
    </header>
    {error && <ErrorBanner message={error} />}
    {!editable && <p className="text-sm text-slate-500">当前角色仅可查看安全配置，不能保存或启用能力。</p>}
    {catalog.error && <p className="text-xs text-slate-500">模型名称目录暂不可读，显示已有接口模型名或配置标识；不代表厂商连接失败。</p>}
    <fieldset disabled={busy || !editable} className="space-y-4">
    <div className="space-y-3">
    {Object.entries(value.profiles).map(([id, profile]) => <article key={id} className="min-w-0 space-y-3 rounded-lg border border-slate-200 bg-white p-3 sm:p-4">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <h4 className="break-words text-sm font-semibold text-slate-900">{modelTitle(id)}</h4>
          {catalog.data?.profiles[id]?.chat && <p className="mt-1 text-xs text-slate-500">聊天已登记；生图、视频和语音以各自接口状态为准。</p>}
        </div>
        <label className="flex items-center gap-2 text-xs"><input type="checkbox" checked={profile.enabled ?? true} onChange={(event) => update({ ...value, profiles: { ...value.profiles, [id]: { ...profile, enabled: event.target.checked } } })} /> 启用此配置</label>
      </div>
      <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-5">{capabilities.map((cap) => {
        const state = profile.capabilities[cap];
        return <div className="min-w-0 rounded-md bg-slate-50 p-2" key={cap}>
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={profile.declared_capabilities.includes(cap)} onChange={(event) => {
        const bindings = { ...profile.capability_bindings }; if (!event.target.checked) delete bindings[cap];
        update({ ...value, profiles: { ...value.profiles, [id]: { ...profile, declared_capabilities: event.target.checked ? [...profile.declared_capabilities, cap] : profile.declared_capabilities.filter((item) => item !== cap), capability_bindings: bindings } } });
      }} /> {labels[cap]}</label>
          <div className="mt-1 flex flex-wrap gap-x-1 text-xs leading-5 text-slate-500">{draft
            ? <><span className="whitespace-nowrap">{profile.capability_bindings[cap] ? "接口已填写" : "接口未填写"}</span><span className="whitespace-nowrap">· 未保存</span></>
            : state ? <><span className="whitespace-nowrap">{state.configured ? "已配置" : "未配置"}</span><span className="whitespace-nowrap">· {state.executable ? "可执行" : "不可执行"}</span><span className="whitespace-nowrap">· {state.verified ? "已验证" : "未验证"}</span></> : <span>该能力状态未提供</span>}</div>
        </div>;
      })}</div>
      {profile.declared_capabilities.map((cap) => {
        const binding = profile.capability_bindings[cap];
        const setBinding = (next?: Binding) => { const bindings = { ...profile.capability_bindings }; if (next) bindings[cap] = next; else delete bindings[cap]; update({ ...value, profiles: { ...value.profiles, [id]: { ...profile, capability_bindings: bindings } } }); };
        return <details className="border-t border-slate-100 pt-2" key={cap}>
          <summary className={disclosureClass}>{labels[cap]}接口绑定 <span className="font-normal text-slate-500">· {binding ? "已填写" : "未填写"}</span></summary>
          <div className="mt-3 space-y-3">
          <p className="break-words text-xs text-slate-500">{draft ? "本地草稿，执行与验证状态需保存后重新读取。" : profile.capabilities[cap]?.reason || "该能力暂无状态说明。"} {!binding && cap !== "chat" && "缺少此媒体绑定不代表厂商聊天连接失败。"}</p>
          <Button size="sm" variant="secondary" disabled={busy} onClick={() => setBinding(binding ? undefined : { adapter_key: "google.native", adapter_version: "1", model_id: "", base_url: "https://generativelanguage.googleapis.com", credential_ref: "" })}>{binding ? "移除该能力接口绑定" : "配置该能力接口"}</Button>
          {binding && <div className="grid gap-2 sm:grid-cols-2">
            <Field label="协议适配器"><select className={inputClass} value={binding.adapter_key} onChange={(event) => setBinding({ ...binding, adapter_key: event.target.value })}>{["openai.compatible", "google.native", "xai.native", "minimax.native", "minimax.cli"].map((adapter) => <option key={adapter}>{adapter}</option>)}</select></Field>
            <Field label="实际 API 模型标识"><input className={inputClass} value={binding.model_id} onChange={(event) => setBinding({ ...binding, model_id: event.target.value })} /></Field>
            <Field label={binding.adapter_key === "minimax.cli" ? "本地 CLI 地址（local://mmx）" : "HTTPS 接口根地址"}><input className={inputClass} value={binding.base_url} onChange={(event) => setBinding({ ...binding, base_url: event.target.value })} /></Field>
            <Field label={binding.adapter_key === "minimax.cli" ? "受控认证引用标识（不是密钥值或文件路径）" : "密钥环境变量名（不是密钥值）"}><input className={inputClass} autoComplete="off" value={binding.credential_ref} onChange={(event) => setBinding({ ...binding, credential_ref: event.target.value })} /></Field>
            <p className="text-xs text-slate-500 sm:col-span-2">协议版本：{binding.adapter_version}。仅填写引用，不输入密钥明文。</p>
          </div>}
          </div>
        </details>;
      })}
      <details className="border-t border-slate-100 pt-2">
        <summary className={disclosureClass}>技术标识与路由预览</summary>
        <div className="mt-3 space-y-2">
          <p className="break-all text-xs text-slate-500">模型配置 ID：{id}</p>
          <Button size="sm" variant="secondary" disabled={busy || !!draft || !!previewBusy} onClick={() => void plan(id)}>{previewBusy === id ? "正在读取路由规划…" : "预览生图路由（不生成、不收费）"}</Button>
        </div>
      </details>
    </article>)}
    {Object.keys(value.profiles).length === 0 && <p className="rounded-lg border border-dashed border-slate-200 p-4 text-sm text-slate-500">暂无模型能力配置。可先登记模型，或展开下方手动添加。</p>}
    <details className="rounded-lg border border-slate-200 bg-white p-3">
      <summary className={disclosureClass}>手动添加模型能力配置</summary>
      <div className="mt-3 flex flex-col gap-2 sm:flex-row sm:items-end"><div className="min-w-0 flex-1"><Field label="稳定模型配置 ID"><input className={inputClass} placeholder="如 writer" value={name} onChange={(event) => setName(event.target.value)} /></Field></div><Button disabled={busy || !/^[A-Za-z0-9_.-]{1,100}$/.test(name) || !!value.profiles[name]} onClick={() => { update({ ...value, profiles: { ...value.profiles, [name]: { declared_capabilities: [], capability_bindings: {}, capabilities: {} as Record<Capability, State> } } }); setName(""); }}>添加配置</Button></div>
    </details>
    </div>
    <details className="rounded-lg border border-slate-200 bg-white p-3 sm:p-4">
      <summary className={disclosureClass}>生成插件 <span className="font-normal text-slate-500">· {Object.keys(value.media_plugins).length} 项</span></summary>
      <div className="mt-3 space-y-3">
      <p className="text-xs text-slate-500">插件绑定已有模型能力，不安装脚本；加入回退顺序后才可能参与路由。</p>
      {Object.keys(value.media_plugins).length === 0 && <p className="text-sm text-slate-500">暂无生成插件。</p>}
      {Object.entries(value.media_plugins).map(([id, plugin]) => {
        const setPlugin = (next: typeof plugin) => update({ ...value, media_plugins: { ...value.media_plugins, [id]: next } });
        return <div key={id} className="grid min-w-0 gap-3 border-t border-slate-100 pt-3 sm:grid-cols-2">
          <label className="flex items-center gap-2 break-all text-sm sm:col-span-2"><input type="checkbox" checked={plugin.enabled} onChange={(event) => setPlugin({ ...plugin, enabled: event.target.checked })} /> {id} · 允许参与路由</label>
          <Field label="插件能力"><select className={inputClass} value={plugin.capability} onChange={(event) => setPlugin(retargetPlugin({ ...plugin, capability: event.target.value as Capability }, "", value.profiles))}>{capabilities.map((cap) => <option value={cap} key={cap}>{labels[cap]}</option>)}</select></Field>
          <Field label="执行模型配置"><select className={inputClass} value={plugin.model_profile_id} onChange={(event) => setPlugin(retargetPlugin(plugin, event.target.value, value.profiles))}><option value="">请选择已绑定该能力的模型</option>{plugin.model_profile_id && !value.profiles[plugin.model_profile_id]?.capability_bindings[plugin.capability] && <option value={plugin.model_profile_id}>{modelTitle(plugin.model_profile_id)} · 此能力缺少绑定</option>}{Object.entries(value.profiles).filter(([, profile]) => profile.capability_bindings[plugin.capability]).map(([id]) => <option key={id} value={id}>{modelTitle(id)}</option>)}</select></Field>
          <div className="sm:col-span-2"><Button size="sm" variant="secondary" onClick={() => { const plugins = { ...value.media_plugins }; delete plugins[id]; const routes = Object.fromEntries(Object.entries(value.capability_routes).map(([cap, ids]) => [cap, ids.filter((key) => key !== id)])); update({ ...value, media_plugins: plugins, capability_routes: routes }); }}>删除插件及路由引用</Button></div>
        </div>;
      })}
      <div className="flex flex-col gap-2 border-t border-slate-100 pt-3 sm:flex-row sm:items-end"><div className="min-w-0 flex-1"><Field label="稳定插件 ID"><input className={inputClass} placeholder="如 cover" value={pluginName} onChange={(event) => setPluginName(event.target.value)} /></Field></div><Button disabled={busy || !/^[A-Za-z0-9_.-]{1,100}$/.test(pluginName) || !!value.media_plugins[pluginName]} onClick={() => { update({ ...value, media_plugins: { ...value.media_plugins, [pluginName]: { enabled: false, capability: "image_generation", model_profile_id: "" } } }); setPluginName(""); }}>添加插件</Button></div>
      </div>
    </details>
    <details className="rounded-lg border border-slate-200 bg-white p-3 sm:p-4">
      <summary className={disclosureClass}>自动回退与顺序 <span className="font-normal text-slate-500">· {value.policies.allow_automatic_fallback ? "已允许" : "未开启"}</span></summary>
      <div className="mt-3 space-y-3">
        <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={value.policies.allow_automatic_fallback} onChange={(event) => update({ ...value, policies: { ...value.policies, allow_automatic_fallback: event.target.checked } })} /> 允许在保存的限额内自动调用配置插件</label>
        <p className="text-xs text-slate-500">模型缺能力时才选择插件。按逗号分隔的插件 ID 原顺序保存，不会自动排序或调用。</p>
        {capabilities.map((cap) => <Field key={cap} label={`${labels[cap]} · 按顺序回退的插件 ID`}><input className={inputClass} value={(value.capability_routes[cap] ?? []).join(",")} onChange={(event) => update({ ...value, capability_routes: { ...value.capability_routes, [cap]: event.target.value.split(",").map((id) => id.trim()) } })} /></Field>)}
      </div>
    </details>
    <details className="rounded-lg border border-slate-200 bg-white p-3 sm:p-4">
      <summary className={disclosureClass}>单次硬上限 <span className="font-normal text-slate-500">· {Object.keys(value.policies.limits).length} 项</span></summary>
      <div className="mt-3 space-y-3">
      <p className="text-xs text-slate-500">限额按单次请求生效，不是累计账本，也不证明接口可执行。金额上限缺少可验证价格时会阻塞。</p>
      {capabilities.map((cap) => {
        const limit = value.policies.limits[cap];
        const quantity: keyof Limit = cap === "chat" ? "max_tokens" : cap === "image_generation" ? "max_pixels" : "max_seconds";
        const setLimit = (next: Limit | undefined) => { const limits = { ...value.policies.limits }; if (next) limits[cap] = next; else delete limits[cap]; update({ ...value, policies: { ...value.policies, limits } }); };
        return <details className="border-t border-slate-100 pt-3" key={cap}>
          <summary className={disclosureClass}>{labels[cap]} <span className="font-normal text-slate-500">· {limit ? "已设置单次限额" : "未设置单次限额"}</span></summary>
          <div className="mt-3 space-y-3">
          <Button size="sm" variant="secondary" onClick={() => setLimit(limit ? undefined : { max_items: 1, timeout_seconds: 25 })}>{limit ? "移除该能力限额" : "设置单次限额"}</Button>
          {limit && <div className="grid gap-2 sm:grid-cols-3">
            {(["max_items", quantity, "timeout_seconds"] as const).map((key) => <Field key={key} label={key === "max_items" ? "最多结果数" : key === "timeout_seconds" ? "请求超时（秒，≤300）" : key === "max_pixels" ? "最多像素" : key === "max_tokens" ? "最多 Token" : "最多秒数"}><input type="number" min="1" step="1" className={inputClass} value={limit[key] ?? ""} onChange={(event) => setLimit({ ...limit, [key]: event.target.value === "" ? null : Number(event.target.value) })} /></Field>)}
            <Field label="金额上限（可选，无价格证明则阻塞）"><input type="number" min="0.01" step="0.01" className={inputClass} value={limit.max_cost ?? ""} onChange={(event) => setLimit({ ...limit, max_cost: event.target.value === "" ? null : Number(event.target.value) })} /></Field>
            <Field label="金额币种"><select className={inputClass} value={limit.currency ?? ""} onChange={(event) => setLimit({ ...limit, currency: event.target.value === "USD" || event.target.value === "CNY" ? event.target.value : null })}><option value="">未设置</option><option>USD</option><option>CNY</option></select></Field>
          </div>}
          </div>
        </details>;
      })}
      </div>
    </details>
    </fieldset>
    {preview && <div role="status" className="space-y-1 rounded-lg bg-slate-50 p-3 text-sm">
      <p className="break-words">{modelTitle(preview.selected_profile)} · 生图规划：{preview.status} · {preview.reason}{preview.plugin_id ? ` · 插件 ${preview.plugin_id} → ${preview.execution_profile ? modelTitle(preview.execution_profile) : "未指定执行模型"}` : ""}</p>
      <p className="text-xs text-slate-500">仅检查保存的路由配置，未执行生成或真实供应商验证。</p>
    </div>}
    <footer className="space-y-3 border-t border-slate-200 pt-4">
      <div className="space-y-1" role="status" aria-live="polite">
        <p className="text-sm font-medium">{busy ? "正在保存能力配置…" : error ? (dirty ? "操作失败，本地编辑仍保留" : "操作失败") : dirty ? `未保存：${changedSections.join("、") || "能力配置编辑"}` : saved ? "能力配置已保存" : "暂无未保存编辑"}</p>
        <p className="text-xs text-slate-500">保存范围：模型能力与接口绑定、生成插件、回退顺序和限额；厂商、密钥及用途选择由各自保存按钮提交。</p>
        {incompleteEntry && <p className="text-xs text-amber-700">正在输入的新条目需先点击添加，才会包含在保存中。</p>}
      </div>
      <div className="flex flex-wrap items-center gap-2"><Button disabled={busy || !draft || !editable} onClick={() => void save()}>{busy ? "保存中…" : "保存能力配置"}</Button><Button variant="secondary" disabled={busy || query.isFetching} onClick={() => {
        if (!isCurrent() || ((draft || incompleteEntry) && !window.confirm("丢弃未保存的能力编辑并重新读取？"))) return;
        previewRequest.current += 1; setPreviewBusy(null); setDraft(null); setName(""); setPluginName(""); setPreview(null); setError(""); setSaved(false);
        void query.refetch();
      }}>{query.isFetching ? "正在读取…" : "重新读取"}</Button><span className="text-xs text-slate-400">配置版本 {value.revision}</span></div>
      <details><summary className={disclosureClass}>保存兼容性说明</summary><p className="mt-2 text-xs text-slate-500">保存能力配置后，旧的无版本模型编辑器会拒绝覆盖；原生图配置和历史运行不会自动迁移。</p></details>
    </footer>
  </section>;
}
