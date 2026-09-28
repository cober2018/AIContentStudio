import { lazy, Suspense, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api, currentUser, setCurrentUser } from "../api";
import { Button, ErrorBanner, Field, Spinner, inputClass } from "../components/ui";

const RuntimeSettings = lazy(() => import("../pages/Settings"));
type Editability = "editable" | "read_only" | "unavailable";
type Section = { key: string; label: string; editability: Editability; reason?: string | null; data?: unknown };
type Inventory = { sections: Section[] };
type PageInfo = { total: number; limit: number; offset: number };
const labels: Record<Editability, string> = { editable: "可配置", read_only: "只读", unavailable: "不可用" };
const sections = [
  ["models", "模型与 AI"], ["data_sources", "数据源"], ["channels", "渠道"],
  ["rules", "规则与模板"], ["team", "团队与权限"], ["advanced", "高级运行环境"],
] as const;

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

function SectionActions({ section }: { section: Section }) {
  const [showRuntime, setShowRuntime] = useState(false);
  const me = useQuery({ queryKey: ["product-settings-user", currentUser()], queryFn: () => api.get<{ role: string }>("/users/me"), retry: false });
  const editable = section.editability === "editable";
  if (section.key === "team") return <TeamIdentity />;
  return <div className="space-y-4">
    {section.key === "models" && <div className="space-y-2"><p className="text-sm text-slate-600">模型配置沿用现有持久化与完整 Profiles / 路由保存契约。密钥留空表示保留，显示掩码不会被重新提交。连接测试会发起真实网络请求；图片配置保存可能写入本机 CLI 配置，必须由你明确操作。</p><Button disabled={!editable} onClick={() => setShowRuntime(!showRuntime)}>{showRuntime ? "收起配置工具" : "打开模型与图片配置工具"}</Button></div>}
    {section.key === "data_sources" && <div className="space-y-2"><p className="text-sm text-slate-600">Generic Connector 配置不代表 Data Source Plugin 已可执行。此清单读取不会自动拉取或测试连接；数据拉取是独立的有副作用动作。</p>{["admin", "editor"].includes(me.data?.role ?? "") && <Link className="text-sm text-indigo-700 underline" to="/connectors">{editable ? "管理 Generic Connectors / 显式拉取" : "打开已有 Connectors（配置只读，可显式拉取）"}</Link>}</div>}
    {section.key === "channels" && <p className="text-sm text-slate-600">渠道注册信息为只读真源。配置了 workflow / publisher 引用不代表已经验证可执行或可发布，不提供虚假的保存按钮。</p>}
    {section.key === "rules" && <div className="space-y-2"><p className="text-sm text-slate-600">确定性 Rule、Prompt、Channel Template 与 Discoverability Profile 分开列出。版本操作以每项实际支持的 actions 和状态为准。</p>{editable && <Link className="text-sm text-indigo-700 underline" to="/templates">打开现有版本化模板工具</Link>}</div>}
    {section.key === "advanced" && <div className="space-y-2"><p className="text-sm text-amber-800">高级工具包含本机路径、技能、MCP、dsh 与基础设施配置。不会在读取此清单时扫描目录、写文件或探测外部服务。</p><Button disabled={!editable} onClick={() => setShowRuntime(!showRuntime)}>{showRuntime ? "收起高级工具" : "明确打开本机运行配置工具"}</Button></div>}
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
  const [active, setActive] = useState<string>("models");
  const [offset, setOffset] = useState(0);
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
    <nav className="flex flex-wrap gap-2" aria-label="设置分区">{sections.map(([key, label]) => <Button key={key} variant={active === key ? "primary" : "secondary"} onClick={() => { setActive(key); setOffset(0); }}>{label}</Button>)}</nav>
    {pending && <Spinner label="读取安全产品设置…" />}
    {error && <div className="space-y-3" role="alert"><ErrorBanner message={error instanceof Error ? error.message : "设置读取失败"} /><Button onClick={() => void refresh()}>重试</Button></div>}
    {!pending && !error && !selected && <ErrorBanner message="后端尚未返回这个分区，不能确认其能力。" />}
    {selected && <section className="space-y-5 rounded-xl border border-slate-200 bg-white p-5"><div className="flex items-center justify-between"><h2 className="text-lg font-semibold">{selected.label}</h2><span className="rounded-full bg-slate-100 px-3 py-1 text-xs">{labels[selected.editability] ?? "能力未核对"}</span></div>{selected.reason && <p className="text-sm text-amber-800">{selected.reason}</p>}<Metadata value={selected.data} />{paging && <div className="flex items-center gap-3"><span className="text-xs text-slate-500">共 {paging.total} 条，当前起点 {paging.offset}</span><Button variant="secondary" disabled={paging.offset === 0} onClick={() => setOffset(Math.max(0, paging.offset - paging.limit))}>上一页</Button><Button variant="secondary" disabled={paging.offset + paging.limit >= paging.total} onClick={() => setOffset(paging.offset + paging.limit)}>下一页</Button></div>}<SectionActions key={`${currentUser()}:${selected.key}`} section={selected} /><Button variant="secondary" onClick={() => void refresh()}>刷新真实配置</Button></section>}
  </div>;
}
