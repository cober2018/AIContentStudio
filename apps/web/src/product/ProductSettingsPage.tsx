import { lazy, Suspense, useEffect, useLayoutEffect, useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";
import { api, currentUser, setCurrentUser } from "../api";
import { Button, ErrorBanner, Field, Modal, Spinner, inputClass } from "../components/ui";

const RuntimeSettings = lazy(() => import("../pages/Settings"));
const ConnectorOperations = lazy(() => import("../pages/Connectors"));
const TemplateOperations = lazy(() => import("../pages/Templates"));
const CapabilitySettings = lazy(() => import("./CapabilitySettings"));
const ProviderGuidancePanel = lazy(() => import("./ProviderGuidancePanel"));
const ModelRoutingSettings = lazy(() => import("./ModelRoutingSettings"));
const ModelRegistrationSettings = lazy(() => import("./ModelRegistrationSettings"));
const CapabilityMemoryPanel = lazy(() => import("./CapabilityMemoryPanel"));
const StudioCreativeInventory = lazy(() => import("./StudioCreativeInventory"));
type Editability = "editable" | "read_only" | "unavailable";
type Section = { key: string; label: string; editability: Editability; reason?: string | null; data?: unknown };
type Inventory = { sections: Section[] };
type PageInfo = { total: number; limit: number; offset: number };
const labels: Record<Editability, string> = { editable: "可配置", read_only: "只读", unavailable: "不可用" };
const sections = [
  ["models", "模型与 AI"], ["data_sources", "数据源"], ["channels", "渠道"],
  ["rules", "规则与模板"], ["team", "团队与权限"], ["advanced", "高级运行环境"],
] as const;
const compatibilityTools = [
  ["/topics", "旧选题", "原 Topic、生产输入与建议"],
  ["/workspace", "旧稿件工作台", "原 Draft 编辑、检查与生成历史"],
  ["/review-publish", "旧审核与发布", "原候选、检查与交付目标"],
  ["/legacy/review", "旧审核", "原 Draft 审批记录"],
  ["/handoff", "旧母稿交接", "原 MotherRevision 和适配稿"],
  ["/legacy/assets", "旧内容资产", "原候选、交付包、回执与反馈"],
  ["/workflows", "独立工作流", "定义、Run、Attempt 与高级调试"],
  ["/sources", "来源兼容页", "原 Source / Fact 操作"],
  ["/fact-packs", "证据包兼容页", "原 ID、版本与冻结快照"],
  ["/materials", "素材兼容页", "原素材版本与旧 Draft 挂载"],
  ["/connectors", "数据接入兼容页", "原端点配置与明确拉取"],
  ["/templates", "模板兼容页", "原模板、Brand Voice 与 Prompt"],
  ["/dashboard", "旧概览", "原概览读取"],
  ["/legacy/landing", "旧首页", "原入口保留"],
] as const;

const modelViews = [
  { key: "providers", label: "厂商与模型", hint: "连接服务，登记可用模型", icon: "01" },
  { key: "routes", label: "用途路由", hint: "为各个功能选择模型", icon: "02" },
  { key: "capabilities", label: "生成能力与插件", hint: "配置媒体能力与回退", icon: "03" },
] as const;
type ModelView = typeof modelViews[number]["key"];

function ModelSettingsWorkspace({ editable, onDirtyChange }: { editable: boolean; onDirtyChange: (dirty: boolean) => void }) {
  const [view, setView] = useState<ModelView>("providers");
  const [capabilitiesOpened, setCapabilitiesOpened] = useState(false);
  const [registrationDirty, setRegistrationDirty] = useState(false);
  const [capabilityDirty, setCapabilityDirty] = useState(false);
  const [showGuidance, setShowGuidance] = useState(false);
  useEffect(() => { onDirtyChange(registrationDirty || capabilityDirty); }, [registrationDirty, capabilityDirty, onDirtyChange]);
  useEffect(() => () => onDirtyChange(false), [onDirtyChange]);
  return <div className="grid min-w-0 gap-6 lg:grid-cols-[11rem_minmax(0,1fr)]">
    <nav aria-label="模型配置分区" className="flex gap-1 overflow-x-auto rounded-lg bg-slate-50 p-1.5 lg:sticky lg:top-6 lg:block lg:self-start">
      {modelViews.map(item => <button key={item.key} type="button" aria-current={view === item.key ? "page" : undefined}
        className={`flex shrink-0 items-start gap-2.5 rounded-md px-3 py-3 text-left transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-slate-700 lg:w-full ${view === item.key ? "bg-white text-slate-900 shadow-sm ring-1 ring-slate-200" : "text-slate-500 hover:bg-white/70 hover:text-slate-800"}`}
        onClick={() => { setView(item.key); if (item.key === "capabilities") setCapabilitiesOpened(true); }}>
        <span className="mt-0.5 text-[10px] font-semibold tabular-nums text-slate-400">{item.icon}</span>
        <span className="text-sm font-medium">{item.label}<span className="mt-1 hidden text-[11px] font-normal leading-relaxed text-slate-500 lg:block">{item.hint}</span></span>
      </button>)}
    </nav>
    <div className="min-w-0">
      <div hidden={view === "capabilities"}>
        <Suspense fallback={<Spinner label="读取厂商与模型…" />}><ModelRegistrationSettings view={view === "routes" ? "routes" : "providers"} editable={editable} onDirtyChange={setRegistrationDirty} /></Suspense>
      </div>
      {capabilitiesOpened && <div hidden={view !== "capabilities"} className="space-y-5">
        <Suspense fallback={<Spinner label="读取生成能力…" />}><ModelRoutingSettings editable={editable} onDirtyChange={setCapabilityDirty} /></Suspense>
        <details className="rounded-lg border border-slate-200 bg-slate-50/60" onToggle={event => setShowGuidance(event.currentTarget.open)}>
          <summary className="cursor-pointer px-4 py-3 text-sm text-slate-600 focus-visible:outline focus-visible:outline-2">技术说明与旧版兼容工具</summary>
          {showGuidance && <div className="space-y-4 border-t border-slate-200 p-4">
            <Suspense fallback={<Spinner label="读取协议说明…" />}><ProviderGuidancePanel /></Suspense>
            <p className="text-xs leading-relaxed text-slate-500">旧版保留图片、技能和运行环境配置；新版模型配置使用此页的版本化保存。</p>
            <Link className="inline-flex text-sm font-medium text-slate-700 underline underline-offset-4" to="/legacy/settings" target="_blank" rel="noopener noreferrer">打开原管理员配置工具 ↗</Link>
          </div>}
        </details>
      </div>}
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

const runtimeChecks = [
  ["db", "数据库"], ["schema", "迁移版本"], ["auth", "身份配置"],
  ["storage", "素材存储"], ["queue", "任务队列"], ["worker", "执行进程"], ["secrets", "密钥策略"],
] as const;
type RuntimeCheck = typeof runtimeChecks[number][0];
type RuntimeStatus = { ready: boolean; checks: Record<RuntimeCheck, boolean> };

function OperationalStatus() {
  const query = useQuery<RuntimeStatus>({
    queryKey: ["runtime-readiness", currentUser()], enabled: false, retry: false,
    refetchOnWindowFocus: false, refetchOnReconnect: false,
    queryFn: async ({ signal }) => {
      const response = await fetch("/api/v1/health/ready", { signal: AbortSignal.any([signal, AbortSignal.timeout(15000)]), cache: "no-store" });
      if (![200, 503].includes(response.status)) throw new Error("暂时无法读取运行状态，请稍后重试。");
      const result: unknown = await response.json();
      if (!result || typeof result !== "object") throw new Error("运行状态响应不完整，请稍后重试。");
      const data = result as Record<string, unknown>;
      if (typeof data.ready !== "boolean" || (response.status === 200) !== data.ready
        || runtimeChecks.some(([key]) => typeof data[key] !== "boolean")
        || (data.ready && runtimeChecks.some(([key]) => data[key] !== true))) {
        throw new Error("运行状态响应不完整，请稍后重试。");
      }
      return { ready: data.ready, checks: Object.fromEntries(runtimeChecks.map(([key]) => [key, data[key]])) as Record<RuntimeCheck, boolean> };
    },
  });
  return <section aria-label="运行状态" className="space-y-3 rounded-lg border border-slate-200 bg-slate-50 p-4">
    <div className="flex flex-wrap items-center justify-between gap-3"><h2 className="text-sm font-semibold text-slate-900">运行状态</h2><Button variant="secondary" disabled={query.isFetching} onClick={() => void query.refetch()}>{query.isFetching ? "检查中…" : "查询运行状态"}</Button></div>
    <p className="text-xs leading-relaxed text-slate-500">仅在点击时检查基础设施；不调用模型、不发送内容，也不改变配置。队列关闭时，队列与执行进程检查不阻断本机同步运行。</p>
    {query.isFetching ? <Spinner label="检查必要运行条件…" /> : query.isError ? <p role="alert" className="text-sm text-amber-800">暂时无法读取运行状态；这不代表检查通过。</p> : query.data ? <div aria-live="polite" className="space-y-3">
      <p className={`text-sm font-medium ${query.data.ready ? "text-emerald-800" : "text-amber-800"}`}>{query.data.ready ? "基础运行条件已就绪（不代表外部能力已验收）" : "基础运行条件未就绪"}</p>
      <dl className="grid gap-2 sm:grid-cols-2">{runtimeChecks.map(([key, label]) => <div key={key} className="flex justify-between gap-3 text-sm"><dt className="text-slate-600">{label}</dt><dd className={query.data!.checks[key] ? "text-emerald-700" : "text-amber-800"}>{query.data!.checks[key] ? "满足当前运行要求" : "未通过"}</dd></div>)}</dl>
    </div> : <p className="text-sm text-slate-500">尚未检查。配置存在不代表服务可用。</p>}
  </section>;
}

function SectionActions({ section, onDirtyChange }: { section: Section; onDirtyChange: (dirty: boolean) => void }) {
  const [showRuntime, setShowRuntime] = useState(false);
  const [showOperations, setShowOperations] = useState(false);
  const [memoryOpened, setMemoryOpened] = useState(false);
  const [showMemory, setShowMemory] = useState(false);
  const me = useQuery({ queryKey: ["product-settings-user", currentUser()], queryFn: () => api.get<{ role: string }>("/users/me"), retry: false });
  const editable = section.editability === "editable";
  if (section.key === "models") return <ModelSettingsWorkspace editable={editable} onDirtyChange={onDirtyChange} />;
  if (section.key === "team") {
    const data = section.data && typeof section.data === "object" ? section.data as Record<string, unknown> : {};
    const production = data.auth_mode === "production/jwt_hs256";
    return production ? <p className="text-sm text-emerald-800">生产身份由已验证的 issuer + subject 映射到现有用户；本页面不提供 Header 身份切换或组织/SSO 管理。</p> : <TeamIdentity />;
  }
  return <div className="space-y-4">
    {section.key === "data_sources" && <div className="space-y-2"><p className="text-sm text-slate-600">Generic Connector 配置不代表 Data Source Plugin 已可执行。此清单读取不会自动拉取或测试连接；数据拉取是独立的有副作用动作。</p><Button variant="secondary" disabled={!me.isSuccess} onClick={() => setShowOperations(!showOperations)}>{showOperations ? "收起接入操作" : "管理数据接入与显式拉取"}</Button>{showOperations && me.isSuccess && <Suspense fallback={<Spinner label="加载数据接入操作…" />}><ConnectorOperations embedded readOnly={!editable || me.data.role !== "admin"} allowPull={["admin", "editor"].includes(me.data.role)} /></Suspense>}</div>}
    {section.key === "channels" && <p className="text-sm text-slate-600">渠道注册信息为只读真源。配置了 workflow / publisher 引用不代表已经验证可执行或可发布，不提供虚假的保存按钮。</p>}
    {(section.key === "channels" || section.key === "data_sources") && <Suspense fallback={<Spinner label="加载能力验证…" />}><CapabilitySettings mode={section.key} /></Suspense>}
    {section.key === "rules" && <div className="space-y-2"><p className="text-sm text-slate-600">确定性 Rule 仍为只读。管理员可打开既有版本化模板工具；单项操作由对应 API 校验，不因当前清单没有可编辑项而隐藏入口。</p>{me.data?.role === "admin" && <Button variant="secondary" onClick={() => setShowOperations(!showOperations)}>{showOperations ? "收起版本化模板" : "管理版本化模板"}</Button>}{showOperations && me.data?.role === "admin" && <Suspense fallback={<Spinner label="加载模板操作…" />}><TemplateOperations /></Suspense>}</div>}
    {section.key === "rules" && <Suspense fallback={<Spinner label="读取内置创作资源…" />}><StudioCreativeInventory /></Suspense>}
    {section.key === "advanced" && <div className="space-y-2"><p className="text-sm text-amber-800">高级工具包含本机路径、技能、MCP、dsh 与基础设施配置。不会在读取此清单时扫描目录、写文件或探测外部服务。</p>{editable && <OperationalStatus />}<Button disabled={!editable} onClick={() => setShowRuntime(!showRuntime)}>{showRuntime ? "收起高级工具" : "明确打开本机运行配置工具"}</Button></div>}
    {section.key === "advanced" && <section aria-label="旧数据与兼容工具" className="space-y-3 rounded-lg border border-slate-200 p-4"><h2 className="font-semibold">旧数据与兼容工具</h2><p className="text-sm text-slate-600">保留原记录与操作，不自动转换为项目、Master 或外部执行。打开目录不执行生成、拉取、审批或发布；各工具仍按原权限校验，写入须在对应页面明确操作。</p><div className="grid gap-3 sm:grid-cols-2">{compatibilityTools.map(([path, label, detail]) => <div key={path}><Link to={path} target="_blank" rel="noopener noreferrer" className="text-sm text-indigo-700 underline underline-offset-4">{label} ↗</Link><p className="mt-1 text-xs text-slate-500">{detail}</p></div>)}</div>{me.data?.role === "admin" && <Link to="/legacy/settings" target="_blank" rel="noopener noreferrer" className="inline-block text-sm text-indigo-700 underline underline-offset-4">原管理员运行配置 ↗</Link>}</section>}
    {section.key === "advanced" && <section className="space-y-3 rounded-lg border border-slate-200 p-4"><h2 className="font-semibold">能力方法库</h2><p className="text-sm text-slate-600">独立管理可复用方法与偏好。编辑者和管理员可操作，查看者只读；入口与本机管理员配置权限分开。</p><Button variant="secondary" onClick={() => { setMemoryOpened(true); setShowMemory(previous => !previous); }}>{showMemory ? "收起能力方法库" : "明确打开能力方法库"}</Button>{memoryOpened && <div hidden={!showMemory}><Suspense fallback={<Spinner label="按需加载能力方法库…" />}><CapabilityMemoryPanel onDirtyChange={onDirtyChange} /></Suspense></div>}</section>}
    {showRuntime && editable && <section className="rounded-xl border border-amber-200 bg-white"><p className="p-4 text-sm text-amber-800">下面是原有管理员配置工具；其保存、连接测试和本机写入操作均需单独确认操作。</p><Suspense fallback={<Spinner label="按需加载原有配置工具…" />}><RuntimeSettings /></Suspense></section>}
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
  const [active, setActive] = useState<string>("models");
  const [offset, setOffset] = useState(0);
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
  const selected = paginated ? page.data : query.data?.sections.find((item) => item.key === active);
  const paging = selected ? pageInfo(selected) : undefined;
  const pending = paginated ? page.isPending : query.isPending;
  const error = paginated ? page.error : query.error;
  const refresh = () => paginated ? page.refetch() : query.refetch();
  return <div className="space-y-6 p-6 lg:p-9"><header><p className="text-xs font-semibold uppercase tracking-widest text-indigo-600">System configuration</p><h1 className="mt-2 text-2xl font-bold">设置</h1><p className="mt-2 text-sm text-slate-600">统一产品入口，读取既有 Registry 与安全配置投影；不建立第二套配置真源。</p></header>
    <nav className="flex flex-wrap gap-2" aria-label="设置分区">{sections.map(([key, label]) => <Button key={key} variant={active === key ? "primary" : "secondary"} onClick={() => { if (key === active) return; const leave = () => { setActive(key); setOffset(0); }; if (dirty) setLeaveAction(() => leave); else leave(); }}>{label}</Button>)}</nav>
    {pending && <Spinner label="读取安全产品设置…" />}
    {error && <div className="space-y-3" role="alert"><ErrorBanner message={error instanceof Error ? error.message : "设置读取失败"} /><Button onClick={() => void refresh()}>重试</Button></div>}
    {!pending && !error && !selected && <ErrorBanner message="后端尚未返回这个分区，不能确认其能力。" />}
    {selected && <section className="space-y-5 rounded-xl border border-slate-200 bg-white p-5"><div className="flex items-center justify-between"><h2 className="text-lg font-semibold">{selected.label}</h2><span className="rounded-full bg-slate-100 px-3 py-1 text-xs">{labels[selected.editability] ?? "能力未核对"}</span></div>{selected.reason && <p className="text-sm text-amber-800">{selected.reason}</p>}{selected.key !== "models" && <Metadata value={selected.data} />}{paging && <div className="flex items-center gap-3"><span className="text-xs text-slate-500">共 {paging.total} 条，当前起点 {paging.offset}</span><Button variant="secondary" disabled={paging.offset === 0} onClick={() => setOffset(Math.max(0, paging.offset - paging.limit))}>上一页</Button><Button variant="secondary" disabled={paging.offset + paging.limit >= paging.total} onClick={() => setOffset(paging.offset + paging.limit)}>下一页</Button></div>}<SectionActions key={`${currentUser()}:${selected.key}`} section={selected} onDirtyChange={setDirty} />{selected.key !== "models" && <Button variant="secondary" onClick={() => void refresh()}>刷新真实配置</Button>}</section>}
    {leaveAction && <div ref={leaveDialog} role="dialog" aria-modal="true" aria-label="未保存的编辑" onKeyDown={event => {
      if (event.key === "Escape") { event.preventDefault(); setLeaveAction(null); }
      if (event.key !== "Tab") return;
      const buttons = leaveDialog.current?.querySelectorAll<HTMLButtonElement>("button");
      if (!buttons?.length) return;
      if (event.shiftKey && document.activeElement === buttons[0]) { event.preventDefault(); buttons[buttons.length - 1].focus(); }
      else if (!event.shiftKey && document.activeElement === buttons[buttons.length - 1]) { event.preventDefault(); buttons[0].focus(); }
    }}><Modal title="保留未保存的编辑？" onClose={() => setLeaveAction(null)}><p className="text-sm leading-6 text-slate-600">当前设置或能力方法有未保存的编辑。离开会丢弃这些本地草稿，已保存的内容不受影响。</p><div className="mt-5 flex flex-wrap justify-end gap-2"><Button variant="secondary" onClick={() => setLeaveAction(null)}>继续编辑</Button><Button variant="danger" onClick={() => { const leave = leaveAction; setLeaveAction(null); leave(); }}>丢弃并离开</Button></div></Modal></div>}
  </div>;
}
