import { FormEvent, useEffect, useRef, useState } from "react";
import { api, ApiError } from "../api";
import { Button, ErrorBanner, Spinner, inputClass } from "../components/ui";

type BoundAccount = { id: number; platform_channel: string | null; platform_account_id: string | null; status: string };
type Connection = { revision: number; enabled: boolean; credential_ref: string; credential_version: string | null; configured: boolean; verified: boolean; executable: boolean; read_only: boolean };
const localDrafts = new Map<string, { appid: string; version: string; enabled: boolean; revision: number }>();

export default function AccountPublisherPanel({ accountId, archived }: { accountId: number; archived: boolean }) {
  const [account, setAccount] = useState<BoundAccount | null>(null);
  const [connection, setConnection] = useState<Connection | null>(null);
  const [admin, setAdmin] = useState(false);
  const [appid, setAppid] = useState("");
  const [version, setVersion] = useState("");
  const [enabled, setEnabled] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [draftKey, setDraftKey] = useState("");
  const alive = useRef(true);
  const panel = useRef<HTMLElement>(null);
  const base = `/content-accounts/${accountId}`;

  useEffect(() => {
    let cancelled = false;
    alive.current = true;
    Promise.all([api.get<BoundAccount>(base), api.get<Connection>(`${base}/publisher-connection`), api.get<{ role: string; id?: number; email?: string }>("/users/me")])
      .then(([nextAccount, nextConnection, user]) => {
        if (cancelled) return;
        const key = user.id || user.email ? `${user.id ?? user.email}:${accountId}` : "";
        const cached = key ? localDrafts.get(key) : undefined;
        setDraftKey(key);
        setAccount(nextAccount); setConnection(cached ? { ...nextConnection, revision: cached.revision } : nextConnection); setAdmin(user.role === "admin");
        setAppid(cached?.appid ?? nextAccount.platform_account_id ?? ""); setVersion(cached?.version ?? nextConnection.credential_version ?? "");
        setEnabled(cached?.enabled ?? (nextConnection.configured ? nextConnection.enabled : true));
        if (cached) setNotice("已恢复此账号未保存的本地输入；请重读服务端版本并核对。");
      }).catch(() => { if (!cancelled) setError("账号连接读取失败，请刷新后重试。"); });
    return () => { cancelled = true; alive.current = false; };
  }, [base]);

  const dirty = !!account && !!connection && (appid !== (account.platform_account_id || "") || version !== (connection.credential_version || "") || enabled !== (connection.configured ? connection.enabled : true));
  useEffect(() => {
    if (!draftKey || !connection) return;
    if (dirty) localDrafts.set(draftKey, { appid, version, enabled, revision: connection.revision });
    else localDrafts.delete(draftKey);
  }, [draftKey, connection, dirty, appid, version, enabled]);
  useEffect(() => {
    if (!dirty && !busy) return;
    const leaving = (event: BeforeUnloadEvent) => { event.preventDefault(); event.returnValue = ""; };
    const navigating = (event: MouseEvent) => {
      const target = event.target instanceof Element ? event.target : null;
      if (!target?.closest("button, a") || panel.current?.contains(target)) return;
      if (!window.confirm("账号配置尚未保存或操作尚未结束，确定离开并放弃本地输入吗？")) {
        event.preventDefault(); event.stopPropagation();
      }
    };
    window.addEventListener("beforeunload", leaving);
    document.addEventListener("click", navigating, true);
    return () => { window.removeEventListener("beforeunload", leaving); document.removeEventListener("click", navigating, true); };
  }, [dirty, busy]);

  async function reloadConnection() {
    setBusy(true);
    try {
      const next = await api.get<Connection>(`${base}/publisher-connection`);
      if (alive.current) { setConnection(next); setError(""); setNotice("已重读服务端版本，本地输入未改变；请核对后再明确保存。"); }
    } catch { if (alive.current) setError("重读失败，本地输入未改变。"); }
    finally { if (alive.current) setBusy(false); }
  }

  async function save(event: FormEvent, bind: boolean) {
    event.preventDefault();
    if (!admin || archived || busy || !connection || connection.read_only !== false || !account) return;
    setBusy(true); setError(""); setNotice("");
    try {
      if (bind) {
        const next = await api.put<BoundAccount>(`${base}/platform-binding`, { platform_channel: "wechat", platform_account_id: appid });
        if (alive.current) { setAccount(next); setNotice("账号已绑定，尚未验证"); }
      } else {
        const next = await api.put<Connection>(`${base}/publisher-connection`, { expected_revision: connection.revision, enabled, credential_version: version });
        if (alive.current) { setConnection(next); setNotice("连接配置已保存；未调用微信接口。"); }
      }
    } catch (err) {
      if (alive.current) setError(err instanceof ApiError && err.status === 409 ? "配置冲突或账号不可修改；本地输入已保留，请重读服务端版本并核对。" : "账号操作失败，请检查管理员权限与输入。");
    } finally { if (alive.current) setBusy(false); }
  }

  const disabled = !admin || archived || busy || account?.status === "archived" || connection?.read_only !== false;
  return <section ref={panel} className="mt-5 space-y-3 border-t pt-4" aria-label="公众号账号连接">
    <h4 className="font-medium">微信公众号 · 独占账号绑定</h4>
    <p className="text-xs text-slate-500">一个角色可经营多个账号；同一真实账号只绑定一个角色，归档不释放占用。保存配置不会调用微信接口。</p>
    {error && <ErrorBanner message={error} />}
    {notice && <p role="status" className="text-sm text-indigo-700">{notice}</p>}
    {!account || !connection ? <Spinner label="读取账号连接…" /> : <>
      <form onSubmit={event => save(event, true)} className="flex flex-wrap items-end gap-2">
        <label className="text-sm">公众号 AppID<input aria-label="公众号 AppID" className={inputClass} value={appid} pattern="wx[0-9a-f]{16}" required disabled={disabled || !!account.platform_account_id} onChange={event => setAppid(event.target.value)} /></label>
        <Button type="submit" disabled={disabled || !!account.platform_account_id}>绑定真实账号</Button>
      </form>
      {account.platform_account_id && <p className="text-sm">已绑定 {account.platform_account_id} · 未验证，不能直接交付</p>}
      <form onSubmit={event => save(event, false)} className="space-y-3">
        <p className="text-xs text-slate-500">凭据仅通过部署环境引用：<code>{connection.credential_ref}</code>。不要在此输入 AppSecret。</p>
        <label className="block text-sm">凭据版本<input aria-label="凭据版本" className={inputClass} value={version} pattern="[A-Za-z0-9_.-]{1,64}" required disabled={disabled || !account.platform_account_id} onChange={event => setVersion(event.target.value)} /></label>
        <label className="flex gap-2 text-sm"><input type="checkbox" checked={enabled} disabled={disabled || !account.platform_account_id} onChange={event => setEnabled(event.target.checked)} />启用本地连接配置（不是远端授权）</label>
        <Button type="submit" disabled={disabled || !account.platform_account_id}>保存账号连接</Button>
        <Button type="button" disabled={busy} onClick={reloadConnection}>重读服务端版本（保留输入）</Button>
        <p className="text-xs text-slate-500">配置版本 {connection.revision} · {connection.configured ? "已配置" : "未配置"} · 未验证</p>
      </form>
      <p className="text-sm text-amber-700">远端不可执行：官方正文限制尚未核实</p>
      {!admin && <p className="text-xs text-slate-500">当前身份只读；绑定和配置仅限所属账号的管理员。</p>}
      {admin && connection.read_only && <p className="text-xs text-slate-500">账号或上级身份不可修改，仅供查看历史配置。</p>}
    </>}
  </section>;
}
