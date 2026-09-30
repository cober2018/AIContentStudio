import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, currentUser } from "../api";
import { Button, ErrorBanner, Field, Spinner, inputClass } from "../components/ui";
import type { RendererCapability } from "./RendererVerificationPanel";

type DataCapability = { id: number; key: string; version: string; source_ref: string; configured: boolean; executable: boolean; verified: boolean; last_verification: { result: string; verified_at: string; expires_at: string | null } | null };
type PublisherScope = { channel: string; content_form: string; action: string; content_account_id: number; account_ref: string; publisher_key: string; publisher_version: string };
type Publisher = { scope: PublisherScope; configured: boolean; executable: boolean; verified: boolean; reason: string | null; last_verification: { result: string; verified_at: string; expires_at: string | null } };
type Inventory = { publishers: Publisher[]; renderers: RendererCapability[]; can_verify: boolean; publisher_verification_available: boolean };
type Endpoint = { id: number; connector_name: string; name: string; method: string };
type Account = { id: number; name: string };

export default function CapabilitySettings({ mode }: { mode: "data_sources" | "channels" }) {
  const cache = useQueryClient();
  const identity = currentUser();
  const [endpointId, setEndpointId] = useState("");
  const [version, setVersion] = useState("1");
  const [accountId, setAccountId] = useState("");
  const [accountRef, setAccountRef] = useState("");
  const [evidence, setEvidence] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const [notice, setNotice] = useState("");
  const inventory = useQuery({ queryKey: ["capabilities", identity], queryFn: () => api.get<Inventory>("/settings/capabilities") });
  const data = useQuery({ queryKey: ["data-capabilities", identity], queryFn: () => api.get<DataCapability[]>("/data-source-capabilities"), enabled: mode === "data_sources" });
  const endpoints = useQuery({ queryKey: ["capability-endpoints", identity], queryFn: () => api.get<{ data: { endpoint_options: Endpoint[] } }>("/settings/data-sources"), enabled: mode === "data_sources" && !!inventory.data?.can_verify });
  const accounts = useQuery({ queryKey: ["capability-accounts", identity], enabled: mode === "channels" && !!inventory.data?.can_verify, queryFn: async () => {
    const personas = await api.get<{ id: number; name: string }[]>("/content-personas");
    const groups = await Promise.all(personas.map(async (persona) => (await api.get<Account[]>(`/content-personas/${persona.id}/accounts`)).map((account) => ({ ...account, name: `${persona.name} / ${account.name}` }))));
    return groups.flat();
  } });
  const action = useMutation({ mutationFn: async ({ path, body, message }: { path: string; body?: unknown; message: string }) => {
    const result = await api.post(path, body); setNotice(message); return result;
  }, onSuccess: async () => { await Promise.all([cache.invalidateQueries({ queryKey: ["capabilities", identity] }), cache.invalidateQueries({ queryKey: ["data-capabilities", identity] })]); } });
  const error = action.error ?? inventory.error ?? data.error ?? endpoints.error ?? accounts.error;
  const busy = action.isPending;
  async function verify() {
    const bytes = new TextEncoder().encode(evidence);
    const hash = Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256", bytes))).map((byte) => byte.toString(16).padStart(2, "0")).join("");
    action.mutate({ path: "/settings/publisher-verifications", body: {
      channel: "wechat", content_form: "article", action: "auto_draft", content_account_id: Number(accountId), account_ref: accountRef,
      publisher_key: "publisher.wechat.wewrite", publisher_version: "1", result: "verified", reference_hash: hash, confirm_readback: confirmed,
    }, message: "已记录准确账号与动作的人工回看证据；有效期为 24 小时。" });
  }
  return <section className="space-y-4 rounded-xl border border-indigo-100 bg-indigo-50/30 p-4" aria-label="能力验证">
    <h3 className="font-semibold">{mode === "data_sources" ? "数据源连接与验证" : "公众号交付账号验证"}</h3>
    <p className="text-sm text-slate-600">此列表只读取已保存记录。配置变化、验证过期或撤销后，执行入口会重新检查。</p>
    {inventory.isPending && <Spinner label="读取能力状态…" />}
    {error && <ErrorBanner message={error instanceof Error ? error.message : "能力请求失败"} />}
    {notice && <p role="status" className="text-sm text-emerald-700">{notice}</p>}
    {mode === "data_sources" && <>
      {data.data?.map((item) => <article key={item.id} className="space-y-2 rounded-lg border bg-white p-3"><p className="font-medium">{item.key} · 版本 {item.version}</p><p className="text-sm">{item.verified ? "已验证，可执行" : item.configured ? "已配置，尚不可执行" : "已停用"}</p><p className="text-xs text-slate-500">{item.last_verification ? `最近结果：${item.last_verification.result} · ${item.last_verification.verified_at}` : "暂无验证"}</p>{inventory.data?.can_verify && <Button size="sm" disabled={busy} onClick={() => action.mutate({ path: `/data-source-capabilities/${item.id}/probe`, message: "已完成真实读取与映射验证。" })}>执行读取并验证</Button>}</article>)}
      {inventory.data?.can_verify && <form className="grid gap-3 sm:grid-cols-2" onSubmit={(event) => { event.preventDefault(); action.mutate({ path: "/data-source-capabilities", body: { key: `api.endpoint.${endpointId}`, version, plugin_key: "api", endpoint_id: Number(endpointId) }, message: "连接配置已保存，请显式读取并验证。" }); }}>
        <Field label="已有只读数据接口"><select required className={inputClass} value={endpointId} onChange={(event) => setEndpointId(event.target.value)}><option value="">选择接口</option>{endpoints.data?.data.endpoint_options.filter((endpoint) => endpoint.method === "GET").map((endpoint) => <option key={endpoint.id} value={endpoint.id}>{endpoint.connector_name} / {endpoint.name}</option>)}</select></Field>
        <Field label="连接版本"><input required className={inputClass} pattern="[1-9][0-9]*" value={version} onChange={(event) => setVersion(event.target.value)} /></Field>
        <p className="text-xs text-slate-600">验证会读取外部接口，并保存 Source / Fact；配置修改后请创建新的连接版本。</p><Button type="submit" disabled={busy || !endpointId}>保存连接配置</Button>
      </form>}
    </>}
    {mode === "channels" && <>
      <h4 className="font-medium">渲染能力（只读清单）</h4>
      <p className="text-xs text-slate-600">管理员在文字生产工作台对已保存 Master 显式验证。图片/视频人工成片不等于自动 Renderer 已验证。</p>
      {inventory.data?.renderers.map((item) => <article key={`${item.renderer_key}:${item.renderer_version}:${JSON.stringify(item.scope || {})}`} className="rounded-lg border bg-white p-3 text-sm"><p>{item.renderer_key} / {item.renderer_version} · {item.payload_schema}</p><p>{item.mode === "manual" ? "人工成片；自动渲染不可用" : item.verified ? "精确范围已验证" : "精确范围尚未验证 / 已失效"}</p><p className="text-xs text-slate-500">{item.scope ? `${item.scope.channel} / ${item.scope.content_form} → ${item.scope.output_mime}` : item.output_mimes.join(" / ")}{item.last_verification ? ` · ${item.last_verification.result} · ${item.last_verification.expires_at || "已撤销"}` : " · 无验证记录"}</p></article>)}
      {inventory.data && !inventory.data.publisher_verification_available && <p className="text-sm text-amber-800">当前 WeWrite 尚不能证明实际执行账号与批准正文保持一致，远端交付未开放。请使用审核后的人工成品包。</p>}
      {inventory.data?.publishers.length === 0 && <p className="text-sm text-slate-500">当前身份尚无账号发布验证。人工成品包仍按候选审批与素材权利提供。</p>}
      {inventory.data?.publishers.map((item) => <article key={JSON.stringify(item.scope)} className="space-y-2 rounded-lg border bg-white p-3"><p className="font-medium">{item.scope.account_ref} · 公众号文章 → 草稿箱</p><p className="text-sm">{item.verified ? "账号范围已验证" : "当前范围未验证 / 已失效"}</p><p className="text-xs text-slate-500">最近结果：{item.last_verification.result} · 有效期：{item.last_verification.expires_at ?? "已撤销"}</p>{inventory.data.can_verify && <Button size="sm" variant="danger" disabled={busy || !item.verified} onClick={() => { if (window.confirm("撤销该账号的草稿箱执行验证？")) action.mutate({ path: "/settings/publisher-verifications", body: { ...item.scope, result: "revoked", reference_hash: "0".repeat(64), confirm_readback: true }, message: "验证已撤销；历史记录仍可查看。" }); }}>撤销验证</Button>}</article>)}
      {inventory.data?.can_verify && inventory.data.publisher_verification_available && <form className="space-y-3" onSubmit={(event) => { event.preventDefault(); void verify(); }}>
        <Field label="内容身份账号"><select required className={inputClass} value={accountId} onChange={(event) => setAccountId(event.target.value)}><option value="">选择账号</option>{accounts.data?.map((account) => <option key={account.id} value={account.id}>{account.name}</option>)}</select></Field>
        <Field label="平台账号标识"><input required className={inputClass} pattern="[A-Za-z0-9_.:@-]{1,150}" value={accountRef} onChange={(event) => setAccountRef(event.target.value)} /></Field>
        <Field label="平台回看记录（仅在本机计算摘要，原文不上传）"><textarea required className={inputClass} value={evidence} onChange={(event) => setEvidence(event.target.value)} /></Field>
        <label className="flex gap-2 text-sm"><input type="checkbox" required checked={confirmed} onChange={(event) => setConfirmed(event.target.checked)} />我已在平台回看并确认该账号的草稿结果；此次仅记录核验，不发起发布。</label>
        <Button type="submit" disabled={busy || !accountId || !confirmed || !evidence.trim()}>记录账号核验</Button>
      </form>}
    </>}
  </section>;
}
