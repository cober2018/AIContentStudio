import { lazy, Suspense, useEffect, useLayoutEffect, useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate, useSearchParams } from "react-router-dom";
import { api, currentUser, setCurrentUser } from "../api";
import { Button, ErrorBanner, Field, Modal, Spinner, inputClass } from "../components/ui";

const RuntimeModelSettings = lazy(() => import("./RuntimeModelSettings"));
const ConnectorSettings = lazy(() => import("./ConnectorSettings"));
const TemplateSettings = lazy(() => import("./TemplateSettings"));
const CapabilitySettings = lazy(() => import("./CapabilitySettings"));
const ChannelPluginPanel = lazy(() => import("./ChannelPluginPanel"));
const ProviderGuidancePanel = lazy(() => import("./ProviderGuidancePanel"));
const ModelRoutingSettings = lazy(() => import("./ModelRoutingSettings"));
const ModelRegistrationSettings = lazy(() => import("./ModelRegistrationSettings"));
const CapabilityMemoryPanel = lazy(() => import("./CapabilityMemoryPanel"));
const StudioCreativeInventory = lazy(() => import("./StudioCreativeInventory"));
const McpSettings = lazy(() => import("./McpSettings"));
const StorageSettings = lazy(() => import("./StorageSettings"));
const StockSourceSettings = lazy(() => import("./StockSourceSettings"));
const AeTemplateLibrary = lazy(() => import("./AeTemplateLibrary"));
const ProductCategories = lazy(() => import("./ProductCategories"));
const EditAgentSettings = lazy(() => import("./EditAgentSettings"));
const VoiceSettings = lazy(() => import("./VoiceSettings"));
type Editability = "editable" | "read_only" | "unavailable";
type Section = { key: string; label: string; editability: Editability; reason?: string | null; data?: unknown };
type Inventory = { sections: Section[] };
type PageInfo = { total: number; limit: number; offset: number };
const labels: Record<Editability, string> = { editable: "可配置", read_only: "只读", unavailable: "不可用" };
const sections = [
  ["models", "模型与 AI"], ["data_sources", "数据源"], ["channels", "渠道"],
  ["rules", "规则与模板"], ["team", "团队与权限"], ["mcp", "MCP 接入"], ["storage", "存储位置"], ["stock_sources", "素材数据源"], ["ae_templates", "AE 模板库"], ["product_categories", "商品品类"], ["edit_agent", "自动剪辑"], ["voice", "配音"], ["methods", "能力方法库"],
] as const;

const modelViews = [
  { key: "providers", label: "厂商与模型", hint: "连接服务，登记可用模型", icon: "01" },
  { key: "routes", label: "用途路由", hint: "为各个功能选择模型", icon: "02" },
  { key: "capabilities", label: "生成能力与插件", hint: "配置媒体能力与回退", icon: "03" },
  { key: "runtime", label: "技能与 MCP", hint: "本机技能目录与 MCP 登记", icon: "04" },
] as const;
type ModelView = typeof modelViews[number]["key"];

function ModelSettingsWorkspace({ editable, onDirtyChange }: { editable: boolean; onDirtyChange: (dirty: boolean) => void }) {
  const [view, setView] = useState<ModelView>("providers");
  const [capabilitiesOpened, setCapabilitiesOpened] = useState(false);
  const [registrationDirty, setRegistrationDirty] = useState(false);
  const [capabilityDirty, setCapabilityDirty] = useState(false);
  const [showGuidance, setShowGuidance] = useState(false);
  const [runtimeOpened, setRuntimeOpened] = useState(false);
  useEffect(() => { onDirtyChange(registrationDirty || capabilityDirty); }, [registrationDirty, capabilityDirty, onDirtyChange]);
  useEffect(() => () => onDirtyChange(false), [onDirtyChange]);
  return <div className="grid min-w-0 gap-6 lg:grid-cols-[11rem_minmax(0,1fr)]">
    <nav aria-label="模型配置分区" className="flex gap-1 overflow-x-auto rounded-lg bg-slate-50 p-1.5 lg:sticky lg:top-6 lg:block lg:self-start">
      {modelViews.map(item => <button key={item.key} type="button" aria-current={view === item.key ? "page" : undefined}
        className={`flex shrink-0 items-start gap-2.5 rounded-md px-3 py-3 text-left transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-slate-700 lg:w-full ${view === item.key ? "bg-white text-slate-900 shadow-sm ring-1 ring-slate-200" : "text-slate-500 hover:bg-white/70 hover:text-slate-800"}`}
        onClick={() => { setView(item.key); if (item.key === "capabilities") setCapabilitiesOpened(true); if (item.key === "runtime") setRuntimeOpened(true); }}>
        <span className="mt-0.5 text-[10px] font-semibold tabular-nums text-slate-400">{item.icon}</span>
        <span className="text-sm font-medium">{item.label}<span className="mt-1 hidden text-[11px] font-normal leading-relaxed text-slate-500 lg:block">{item.hint}</span></span>
      </button>)}
    </nav>
    <div className="min-w-0">
      <div hidden={view === "capabilities" || view === "runtime"}>
        <Suspense fallback={<Spinner label="读取厂商与模型…" />}><ModelRegistrationSettings view={view === "routes" ? "routes" : "providers"} editable={editable} onDirtyChange={setRegistrationDirty} /></Suspense>
      </div>
      {capabilitiesOpened && <div hidden={view !== "capabilities"} className="space-y-5">
        <Suspense fallback={<Spinner label="读取生成能力…" />}><ModelRoutingSettings editable={editable} onDirtyChange={setCapabilityDirty} /></Suspense>
        <details className="rounded-lg border border-slate-200 bg-slate-50/60" onToggle={event => setShowGuidance(event.currentTarget.open)}>
          <summary className="cursor-pointer px-4 py-3 text-sm text-slate-600 focus-visible:outline focus-visible:outline-2">技术说明</summary>
          {showGuidance && <div className="space-y-4 border-t border-slate-200 p-4">
            <Suspense fallback={<Spinner label="读取协议说明…" />}><ProviderGuidancePanel /></Suspense>
          </div>}
        </details>
      </div>}
      {runtimeOpened && <div hidden={view !== "runtime"}><Suspense fallback={<Spinner label="读取技能与 MCP…" />}><RuntimeModelSettings /></Suspense></div>}
    </div>
  </div>;
}

function Metadata({ value }: { value: unknown }) {
  if (value === null || value === undefined) return <span className="text-slate-400">未知 / 未提供</span>;
  if (Array.isArray(value)) return value.length ? <div className="space-y-3">{value.map((item, index) => <div className="rounded-lg border border-slate-200 p-3" key={index}><Metadata value={item} /></div>)}</div> : <p className="text-slate-500">暂无记录。</p>;
  if (typeof value === "object") return <dl className="space-y-2">{Object.entries(value).map(([key, item]) => <div key={key} className="grid gap-1 border-b border-slate-100 pb-2 sm:grid-cols-[11rem_1fr]"><dt className="break-all text-xs text-slate-500">{key}</dt><dd className="min-w-0 break-words text-sm"><Metadata value={item} /></dd></div>)}</dl>;
  if (typeof value === "boolean") return <span>{value ? "是" : "否"}</span>;
  const text = String(value);
  return <span className="whitespace-pre-wrap">{Object.prototype.hasOwnProperty.call(labels, text) ? labels[text as Editability] : text || "未配置"}</span>;
}

function TeamIdentity() {
  const client = useQueryClient();
  const [email, setEmail] = useState(currentUser());
  return <form className="space-y-3 rounded-xl border border-amber-200 bg-amber-50 p-4" onSubmit={(event) => {
    event.preventDefault();
    if (!email.trim()) return;
    setCurrentUser(email.trim().toLowerCase()); client.clear(); window.location.reload();
  }}><p className="text-sm text-amber-900">当前是开发 Header 身份，可在本机切换；这不是生产登录、组织成员管理或 SSO。请勿据此对外部署。</p><Field label="开发身份邮箱"><input type="email" required value={email} onChange={(event) => setEmail(event.target.value)} className={inputClass} /></Field><Button type="submit" variant="secondary">切换本机开发身份</Button></form>;
}

function SectionActions({ section, onDirtyChange }: { section: Section; onDirtyChange: (dirty: boolean) => void }) {
  const [modelDirty, setModelDirty] = useState(false);
  useEffect(() => { if (section.key === "models") onDirtyChange(modelDirty); }, [section.key, modelDirty, onDirtyChange]);
  const [showOperations, setShowOperations] = useState(false);
  const me = useQuery({ queryKey: ["product-settings-user", currentUser()], queryFn: () => api.get<{ role: string }>("/users/me"), retry: false });
  const editable = section.editability === "editable" && me.isSuccess && me.data.role === "admin";
  if (section.key === "models") return <><ModelSettingsWorkspace editable={editable} onDirtyChange={setModelDirty} /></>;
  if (section.key === "team") {
    const data = section.data && typeof section.data === "object" ? section.data as Record<string, unknown> : {};
    const production = data.auth_mode === "production/jwt_hs256";
    return production ? <p className="text-sm text-emerald-800">生产身份由已验证的 issuer + subject 映射到现有用户；本页面不提供 Header 身份切换或组织/SSO 管理。</p> : <TeamIdentity />;
  }
  return <div className="space-y-4">
    {section.key === "data_sources" && <div className="space-y-2"><p className="text-sm text-slate-600">Generic Connector 配置不代表 Data Source Plugin 已可执行。此清单读取不会自动拉取或测试连接；数据拉取是独立的有副作用动作。</p><Button variant="secondary" disabled={!me.isSuccess} onClick={() => setShowOperations(!showOperations)}>{showOperations ? "收起接入操作" : "管理数据接入与显式拉取"}</Button>{showOperations && me.isSuccess && <Suspense fallback={<Spinner label="加载数据接入操作…" />}><ConnectorSettings readOnly={!editable || me.data.role !== "admin"} allowPull={["admin", "editor"].includes(me.data.role)} /></Suspense>}</div>}
    {section.key === "channels" && <div className="space-y-3"><Suspense fallback={<Spinner label="读取渠道方法…" />}><ChannelPluginPanel /></Suspense><p className="text-sm text-slate-600">渠道注册信息仍是只读真源。配置了 workflow / publisher 引用不代表已经验证可执行或可发布。插拔只停用或恢复已安装的渠道方法，不提供虚假的保存或发布按钮。</p></div>}
    {(section.key === "channels" || section.key === "data_sources") && <Suspense fallback={<Spinner label="加载能力验证…" />}><CapabilitySettings mode={section.key} /></Suspense>}
    {section.key === "rules" && <div className="space-y-2"><p className="text-sm text-slate-600">确定性 Rule 仍为只读。管理员可打开既有版本化模板工具；单项操作由对应 API 校验，不因当前清单没有可编辑项而隐藏入口。</p>{me.data?.role === "admin" && <Button variant="secondary" onClick={() => setShowOperations(!showOperations)}>{showOperations ? "收起版本化模板" : "管理版本化模板"}</Button>}{showOperations && me.data?.role === "admin" && <Suspense fallback={<Spinner label="加载模板操作…" />}><TemplateSettings /></Suspense>}</div>}
    {section.key === "rules" && <Suspense fallback={<Spinner label="读取内置创作资源…" />}><StudioCreativeInventory /></Suspense>}
  </div>;
}

function pageInfo(section: Section): PageInfo | undefined {
  if (!section.data || typeof section.data !== "object") return undefined;
  const data = section.data as Record<string, unknown>;
  const raw = section.key === "rules" ? data.templates : data;
  if (!raw || typeof raw !== "object") return undefined;
  const page = raw as Record<string, unknown>;
  if (typeof page.total !== "number" || typeof page.limit !== "number" || typeof page.offset !== "number") return undefined;
  return { total: page.total, limit: page.limit, offset: page.offset };
}

export default function ProductSettingsPage() {
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();
  const requested = params.get("section");
  const active = sections.some(([key]) => key === requested) ? requested! : "";
  const rawOffset = Number(params.get("offset") ?? 0);
  const offset = Number.isSafeInteger(rawOffset) && rawOffset >= 0 ? rawOffset : 0;
  const changeLocation = (section: string, nextOffset = 0) => {
    const leave = () => { setDirty(false); setParams(old => { const next = new URLSearchParams(old); if (section) next.set("section", section); else next.delete("section"); next.delete("view"); if (nextOffset) next.set("offset", String(nextOffset)); else next.delete("offset"); return next; }); };
    if (dirty) setLeaveAction(() => leave); else leave();
  };
  const setOffset = (value: number) => changeLocation(active, value);
  const [dirty, setDirty] = useState(false);
  const [leaveAction, setLeaveAction] = useState<(() => void) | null>(null);
  const leaveDialog = useRef<HTMLDivElement>(null);
  const allowHistoryExit = useRef(false);
  const allowDocumentExit = useRef(false);
  useEffect(() => {
    if (!leaveAction) return;
    const previousFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    leaveDialog.current?.querySelector<HTMLButtonElement>("button")?.focus();
    return () => { if (previousFocus?.isConnected) previousFocus.focus(); };
  }, [leaveAction]);
  useLayoutEffect(() => {
    if (!dirty) return;
    let retainedState = window.history.state;
    let retainedUrl = window.location.href;
    let restoringHistory = false;
    let restoredLeaveAction: (() => void) | null = null;
    const navigation = (window as Window & { navigation?: EventTarget & { traverseTo: (key: string) => { finished: Promise<unknown> } } }).navigation;
    const warnTraverse = (event: Event) => {
      const change = event as Event & { navigationType: string; destination: { url: string; key: string; sameDocument: boolean } };
      if (change.navigationType !== "traverse" || !event.cancelable || !change.destination.sameDocument || allowHistoryExit.current) return;
      const destination = new URL(change.destination.url);
      if (destination.pathname === window.location.pathname && destination.search === window.location.search) return;
      // popstate at window can reach BrowserRouter before a later listener; stop traversal before it commits.
      event.preventDefault();
      setLeaveAction(() => () => {
        if (navigation) {
          allowHistoryExit.current = true;
          void navigation.traverseTo(change.destination.key).finished.catch(() => { allowHistoryExit.current = false; });
        }
        else navigate(destination.pathname + destination.search + destination.hash);
      });
    };
    const warn = (event: BeforeUnloadEvent) => { if (!allowDocumentExit.current) { event.preventDefault(); event.returnValue = ""; } };
    const warnHistory = (event: PopStateEvent) => {
      // BrowserRouter 的同文档后退不可取消，先恢复原位置，再让用户明确决定是否离开。
      if (restoringHistory) {
        event.stopImmediatePropagation();
        if (typeof retainedState?.idx === "number" && typeof event.state?.idx === "number" && retainedState.idx !== event.state.idx) {
          window.history.go(retainedState.idx - event.state.idx); return;
        }
        restoringHistory = false;
        if (restoredLeaveAction) setLeaveAction(() => restoredLeaveAction);
        return;
      }
      if (allowHistoryExit.current) { allowHistoryExit.current = false; return; }
      const retained = new URL(retainedUrl);
      if (window.location.pathname === retained.pathname && window.location.search === retained.search) {
        retainedState = window.history.state; retainedUrl = window.location.href; return;
      }
      event.stopImmediatePropagation();
      const destination = window.location.pathname + window.location.search + window.location.hash;
      const oldIndex = retainedState?.idx;
      const nextIndex = event.state?.idx;
      if (typeof oldIndex === "number" && typeof nextIndex === "number" && oldIndex !== nextIndex) {
        restoredLeaveAction = () => { allowHistoryExit.current = true; window.history.go(nextIndex - oldIndex); };
        restoringHistory = true; window.history.go(oldIndex - nextIndex);
      } else {
        window.history.pushState(retainedState, "", retainedUrl);
        setLeaveAction(() => () => navigate(destination));
      }
    };
    const warnNavigation = (event: MouseEvent) => {
      if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      const link = event.target instanceof Element ? event.target.closest<HTMLAnchorElement>("a[href]") : null;
      if (!link || (link.target && link.target !== "_self") || link.hasAttribute("download")) return;
      const destination = new URL(link.href, window.location.href);
      if (destination.pathname === window.location.pathname && destination.search === window.location.search) return;
      event.preventDefault(); event.stopPropagation();
      setLeaveAction(() => () => {
        if (destination.origin === window.location.origin) navigate(destination.pathname + destination.search + destination.hash);
        else { allowDocumentExit.current = true; window.location.assign(destination.href); }
      });
    };
    window.addEventListener("beforeunload", warn);
    window.addEventListener("popstate", warnHistory, true);
    navigation?.addEventListener("navigate", warnTraverse);
    document.addEventListener("click", warnNavigation, true);
    return () => { window.removeEventListener("beforeunload", warn); window.removeEventListener("popstate", warnHistory, true); navigation?.removeEventListener("navigate", warnTraverse); document.removeEventListener("click", warnNavigation, true); };
  }, [dirty, navigate]);
  const query = useQuery({ queryKey: ["product-settings", currentUser()], queryFn: () => api.get<Inventory>("/settings/product"), retry: false });
  const paginated = active === "rules" || active === "data_sources";
  const path = active === "rules" ? "rules" : "data-sources";
  const page = useQuery({ queryKey: ["product-settings-page", currentUser(), active, offset], queryFn: () => api.get<Section>(`/settings/${path}?limit=50&offset=${offset}`), enabled: paginated, retry: false });
  const selected = active === "mcp" || active === "storage" || active === "stock_sources" || active === "ae_templates" || active === "product_categories" || active === "edit_agent" || active === "voice" || active === "methods" ? undefined : paginated ? page.data : query.data?.sections.find((item) => item.key === active);
  const paging = selected ? pageInfo(selected) : undefined;
  // MCP has its own endpoint; the product inventory does not describe it.
  const ownPage = active === "mcp" || active === "storage" || active === "stock_sources" || active === "ae_templates" || active === "product_categories" || active === "edit_agent" || active === "voice" || active === "methods";
  const pending = ownPage ? false : paginated ? page.isPending : query.isPending;
  const error = ownPage ? null : paginated ? page.error : query.error;
  const refresh = () => paginated ? page.refetch() : query.refetch();
  return <div className="mx-auto w-full max-w-[1240px] space-y-8 px-5 pb-20 pt-8 sm:px-8 md:pt-12 lg:px-12"><header className="border-b border-ink-200/80 pb-7"><p className="eyebrow">工作空间</p><h1 className="mt-3 text-[34px] leading-[1.1] text-ink-900 sm:text-[40px]">设置</h1><p className="mt-3 text-[15px] text-ink-600">模型、数据源、渠道、模板与权限都在这里配置。</p></header>
    {!active && !requested && <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{sections.map(([key, label]) => <button key={key} className="rounded-xl border border-slate-200 bg-white p-5 text-left hover:border-indigo-300 focus-visible:outline focus-visible:outline-2 focus-visible:outline-indigo-600" onClick={() => changeLocation(key)}><h2 className="font-semibold text-slate-900">{label}</h2><p className="mt-2 text-sm text-slate-500">{{ models: "连接厂商、登记模型与选择功能用途", data_sources: "管理来源接入与明确拉取", channels: "查看渠道与配置渠道方法", rules: "查看创作资源与管理版本化模板", team: "核对当前身份与权限边界", mcp: "大模型如何连接平台、能做什么", storage: "素材库与本地工作文件夹放在哪里", stock_sources: "免费素材库的 Key、启用与测试", ae_templates: "看看有哪些 AE 效果、动画预览和要填的内容", product_categories: "每个品类的脚本风格、开头、光线和运镜；图生视频默认方式", edit_agent: "准备好剪辑后自动交给本机助手剪粗剪", voice: "MiniMax 配音的音色、情绪和音频参数", methods: "可复用的创作方法与偏好，按项目和作品选用" }[key]}</p><span className="mt-4 inline-block text-sm text-indigo-700">进入配置 →</span></button>)}</div>}
    {requested && !active && <div role="alert"><ErrorBanner message="未找到这个设置分区，请返回设置目录。" /><Button variant="secondary" onClick={() => changeLocation("")}>返回设置目录</Button></div>}
    {active && <><nav className="flex flex-wrap gap-2" aria-label="设置分区"><Button variant="secondary" onClick={() => changeLocation("")}>返回设置目录</Button>{sections.map(([key, label]) => <Button key={key} variant={active === key ? "primary" : "secondary"} onClick={() => { if (key !== active) changeLocation(key); }}>{label}</Button>)}</nav>
    {pending && <Spinner label="读取安全产品设置…" />}
    {error && <div className="space-y-3" role="alert"><ErrorBanner message={error instanceof Error ? error.message : "设置读取失败"} /><Button onClick={() => void refresh()}>重试</Button></div>}
    {active === "mcp" && <Suspense fallback={<Spinner label="读取 MCP 接入…" />}><McpSettings onDirtyChange={setDirty} /></Suspense>}
    {active === "voice" && <Suspense fallback={<Spinner label="读取配音设置…" />}><VoiceSettings /></Suspense>}
    {active === "edit_agent" && <Suspense fallback={<Spinner label="读取自动剪辑…" />}><EditAgentSettings /></Suspense>}
    {active === "storage" && <Suspense fallback={<Spinner label="读取存储位置…" />}><StorageSettings editable /></Suspense>}
    {active === "stock_sources" && <Suspense fallback={<Spinner label="读取素材数据源…" />}><StockSourceSettings editable /></Suspense>}
    {active === "ae_templates" && <Suspense fallback={<Spinner label="读取模板库…" />}><AeTemplateLibrary /></Suspense>}
    {active === "product_categories" && <Suspense fallback={<Spinner label="读取商品品类…" />}><ProductCategories /></Suspense>}
    {active === "methods" && <Suspense fallback={<Spinner label="读取能力方法库…" />}><CapabilityMemoryPanel onDirtyChange={setDirty} /></Suspense>}
    {!ownPage && !pending && !error && !selected && <ErrorBanner message="后端尚未返回这个分区，不能确认其能力。" />}
    {selected && <section className="space-y-5 rounded-xl border border-slate-200 bg-white p-5"><div className="flex items-center justify-between"><h2 className="text-lg font-semibold">{selected.label}</h2><span className="rounded-full bg-slate-100 px-3 py-1 text-xs">{labels[selected.editability] ?? "能力未核对"}</span></div>{selected.reason && <p className="text-sm text-amber-800">{selected.reason}</p>}{selected.key !== "models" && <details className="rounded-lg border border-slate-200 p-3"><summary className="cursor-pointer text-sm text-slate-600">查看原始配置与来源</summary><div className="mt-4"><Metadata value={selected.data} /></div></details>}{paging && <div className="flex items-center gap-3"><span className="text-xs text-slate-500">共 {paging.total} 条，当前起点 {paging.offset}</span><Button variant="secondary" disabled={paging.offset === 0} onClick={() => setOffset(Math.max(0, paging.offset - paging.limit))}>上一页</Button><Button variant="secondary" disabled={paging.offset + paging.limit >= paging.total} onClick={() => setOffset(paging.offset + paging.limit)}>下一页</Button></div>}<SectionActions key={`${currentUser()}:${selected.key}`} section={selected} onDirtyChange={setDirty} />{selected.key !== "models" && <Button variant="secondary" onClick={() => void refresh()}>刷新真实配置</Button>}</section>}
    </>}
    {leaveAction && <div ref={leaveDialog} className="fixed inset-0 z-40" role="dialog" aria-modal="true" aria-label="未保存的编辑" onKeyDown={event => {
      if (event.key === "Escape") { event.preventDefault(); setLeaveAction(null); }
      if (event.key !== "Tab") return;
      const buttons = leaveDialog.current?.querySelectorAll<HTMLButtonElement>("button");
      if (!buttons?.length) return;
      if (event.shiftKey && document.activeElement === buttons[0]) { event.preventDefault(); buttons[buttons.length - 1].focus(); }
      else if (!event.shiftKey && document.activeElement === buttons[buttons.length - 1]) { event.preventDefault(); buttons[0].focus(); }
    }}><Modal title="保留未保存的编辑？" onClose={() => setLeaveAction(null)}><p className="text-sm leading-6 text-slate-600">当前设置或能力方法有未保存的编辑。离开会丢弃这些本地草稿，已保存的内容不受影响。</p><div className="mt-5 flex flex-wrap justify-end gap-2"><Button variant="secondary" onClick={() => setLeaveAction(null)}>继续编辑</Button><Button variant="danger" onClick={() => { const leave = leaveAction; setLeaveAction(null); leave(); }}>丢弃并离开</Button></div></Modal></div>}
  </div>;
}
