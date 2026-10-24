import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api, ApiError } from "../api";
import { Button, ErrorBanner, Field, Spinner, inputClass } from "../components/ui";

type Persona = { id: number; name: string; status: string };
type Channel = { channel: string; label: string };
type Account = {
  id: number;
  name: string;
  persona_id: number | null;
  status: string;
  platform_channel: string | null;
  platform_account_id: string | null;
  platform_binding_state: string;
};

function failureText(error: unknown): string {
  if (!(error instanceof ApiError)) return "登记失败，请重试。";
  if (error.status === 403) return "只有管理员可以登记平台账号。";
  if (error.status === 409 && error.message === "platform_identity_conflict") return "这个平台标识已经登记过。归档也不会把同一个真实账号让给别的角色。";
  if (error.message === "platform_account_public_id_invalid") return "公开标识不合格。不要填写密码、AppSecret 或 token。公众号请填 wx 开头的 AppID，其他平台填账号名或 @handle。";
  return error.message || "登记失败，请重试。";
}

export default function AccountDesk() {
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [channels, setChannels] = useState<Channel[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [role, setRole] = useState<string | null>(null);
  const [personaId, setPersonaId] = useState<number | null>(null);
  const [channel, setChannel] = useState("");
  const [name, setName] = useState("");
  const [handle, setHandle] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const admin = role === "admin";
  const activePersonas = personas.filter(row => row.status !== "archived");
  const channelLabel = useMemo(() => Object.fromEntries(channels.map(row => [row.channel, row.label])), [channels]);

  async function load() {
    const [nextChannels, me] = await Promise.all([
      api.get<Channel[]>("/channels"),
      api.get<{ role: string }>("/users/me"),
    ]);
    const nextAccounts = await api.get<Account[]>("/content-accounts");
    setChannels(nextChannels);
    setAccounts(nextAccounts);
    setRole(me.role);
    setChannel(current => current || nextChannels[0]?.channel || "");
  }

  useEffect(() => {
    load().catch(err => setError(failureText(err))).finally(() => setLoading(false));
  }, []);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!admin || busy) return;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await api.post(personaId == null ? "/content-accounts/channel-accounts" : `/content-personas/${personaId}/channel-accounts`, {
        name: name.trim(),
        platform_channel: channel,
        platform_account_id: handle.trim(),
      });
      setName("");
      setHandle("");
      setNotice("已登记公开账号。这还不是登录，也不是发布。");
      await load();
    } catch (err) {
      setError(failureText(err));
    } finally {
      setBusy(false);
    }
  }

  const personaName = Object.fromEntries(personas.map(row => [row.id, row.name]));

  return <div className="mx-auto w-full max-w-[1240px] px-5 pb-20 pt-8 sm:px-8 md:pt-12 lg:px-12">
    <p className="eyebrow">账号工作台</p>
    <h1 className="mt-3 text-[34px] leading-[1.1] text-ink-900 sm:text-[40px]">账号管理</h1>
    <p className="mt-2 max-w-3xl text-sm leading-relaxed text-slate-600">在这里给每个可选渠道填公开账号名，方便之后对上号。不要填写密码、AppSecret、token 或带登录信息的网址。浏览器发布时用你自己已经登录的会话。登记成功只表示平台知道这是哪个号，不是已经授权，也不是已经发出去。</p>
    {error && <div className="mt-4"><ErrorBanner message={error} /></div>}
    {notice && <p className="mt-4 rounded-lg bg-indigo-50 p-3 text-sm text-indigo-700">{notice}</p>}
    {loading ? <Spinner label="读取账号…" /> : <>
      {<form onSubmit={submit} className="mt-6 space-y-4 rounded-2xl border border-slate-200 bg-white p-5">
        <div className="grid gap-4 md:grid-cols-2">
          <Field label="所属角色（可选）">
            <select aria-label="所属角色" className={inputClass} value={personaId ?? ""} disabled={!admin || busy} onChange={event => setPersonaId(event.target.value ? Number(event.target.value) : null)}>
              <option value="">独立账号 · 商品制作可直接使用</option>
              {activePersonas.map(row => <option key={row.id} value={row.id}>{row.name}</option>)}
            </select>
            {!personas.length && <Button size="sm" variant="secondary" disabled={busy} onClick={() => { api.get<Persona[]>("/content-personas").then(setPersonas).catch(err => setError(failureText(err))); }}>选择关联角色（可选）</Button>}
          </Field>
          <Field label="平台">
            <select aria-label="平台" className={inputClass} value={channel} disabled={!admin || busy} onChange={event => setChannel(event.target.value)}>
              {channels.map(row => <option key={row.channel} value={row.channel}>{row.label}</option>)}
            </select>
          </Field>
          <Field label="显示名称" hint="给你自己看的名字，例如「小红书主号」。">
            <input aria-label="显示名称" className={inputClass} value={name} required maxLength={200} disabled={!admin || busy} onChange={event => setName(event.target.value)} />
          </Field>
          <Field label="公开标识" hint={channel === "wechat" ? "公众号填 wx 开头的 AppID。不要填 AppSecret。已有公众号不用重复登记。" : "填平台上的账号名或 @handle，不要填密码。"}>
            <input aria-label="公开标识" className={inputClass} name="public-handle" autoComplete="off" spellCheck={false} value={handle} required maxLength={64} disabled={!admin || busy} onChange={event => setHandle(event.target.value)} />
          </Field>
        </div>
        <Button type="submit" disabled={!admin || busy}>{busy ? "登记中…" : "登记这个账号"}</Button>
        {!admin && <p className="text-xs text-slate-500">当前身份只读。登记平台账号只限管理员。</p>}
        <p className="text-xs leading-relaxed text-slate-500">公众号官方草稿的凭据版本仍在 <Link className="text-indigo-700" to="/identities">内容身份</Link> 里配置，那里也不输入 AppSecret。已下线的历史渠道不会出现在这个列表里。</p>
      </form>}
      <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-5">
        <h2 className="text-sm font-semibold">各平台登记情况</h2>
        <ul className="mt-3 divide-y divide-slate-100">
          {channels.map(row => {
            const bound = accounts.filter(account => account.platform_channel === row.channel);
            return <li key={row.channel} className="flex flex-wrap items-center justify-between gap-3 py-3">
              <div>
                <p className="text-sm font-medium">{row.label}</p>
                <p className="mt-1 text-xs text-slate-500">{bound.length === 0 ? "还没有登记" : bound.map(account => `${account.name}${account.status === "archived" ? "（已归档，标识仍被占用）" : ""}`).join("、")}</p>
              </div>
              <Button variant="secondary" size="sm" disabled={!admin} onClick={() => { setChannel(row.channel); setNotice(""); }}>填写</Button>
            </li>;
          })}
        </ul>
      </section>
      <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-5">
        <h2 className="text-sm font-semibold">已有账号</h2>
        {accounts.length === 0 ? <p className="mt-3 text-sm text-slate-500">还没有账号。</p> : <ul className="mt-3 space-y-2">
          {accounts.map(account => <li key={account.id} className="rounded-lg border border-slate-100 px-3 py-3 text-sm">
            <p className="font-medium">{account.name}<span className="ml-2 text-xs font-normal text-slate-500">{account.persona_id == null ? "独立账号" : personaName[account.persona_id] || `角色 #${account.persona_id}`} · {account.status === "archived" ? "已归档" : "使用中"}</span></p>
            <p className="mt-1 break-all text-xs text-slate-600">{account.platform_channel ? `${channelLabel[account.platform_channel] || account.platform_channel} · ${account.platform_account_id}` : "尚未绑定平台"} · {account.platform_binding_state === "bound_unverified" ? "已登记，未验证" : "未绑定"}</p>
          </li>)}
        </ul>}
      </section>
    </>}
  </div>;
}
