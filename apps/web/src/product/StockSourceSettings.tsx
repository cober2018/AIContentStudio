import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api, ApiError, currentUser } from "../api";
import { Button, ErrorBanner, Spinner, inputClass } from "../components/ui";

type Source = {
  key: string; label: string; media_types: string[]; blurb?: string; license?: string; signup?: string;
  needs_key: "none" | "optional" | "required"; api_key: { configured: boolean; masked: string } | null;
  key_from: "page" | "env" | null; enabled: boolean; configured: boolean;
};
type Test = { ok: boolean; hits?: number; reason?: string; elapsed_ms?: number };

const mediaNames: Record<string, string> = { video: "视频", image: "图片", audio: "音频" };

function errorText(error: unknown) {
  const detail = error instanceof ApiError ? error.detail as { code?: string } | string | undefined : undefined;
  if (typeof detail === "object" && detail?.code) return detail.code;
  return error instanceof Error ? error.message : "操作失败";
}

function SourceCard({ source, editable, onSaved }: { source: Source; editable: boolean; onSaved: () => Promise<unknown> }) {
  const [key, setKey] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [test, setTest] = useState<Test | null>(null);

  async function save(change: { enabled?: boolean; api_key?: string }) {
    setBusy(true); setError(""); setTest(null);
    try { await api.put("/settings/open-media", { [source.key]: change }); setKey(""); await onSaved(); }
    catch (cause) { setError(errorText(cause)); } finally { setBusy(false); }
  }
  async function runTest() {
    setBusy(true); setError(""); setTest(null);
    try { setTest(await api.post<Test>(`/settings/open-media/${source.key}/test`, {})); }
    catch (cause) { setError(errorText(cause)); } finally { setBusy(false); }
  }

  const state = !source.enabled ? ["已关闭", "bg-slate-100 text-slate-600"]
    : source.configured ? ["可用", "bg-emerald-50 text-emerald-700"] : ["未配置 Key", "bg-amber-50 text-amber-800"];
  return <article className="space-y-3 rounded-xl border border-slate-200 bg-white p-4">
    <div className="flex flex-wrap items-center justify-between gap-2">
      <div className="flex items-center gap-2"><h3 className="font-semibold text-slate-900">{source.label}</h3>
        <span className="text-xs text-slate-500">{source.media_types.map(item => mediaNames[item] ?? item).join(" · ")}</span></div>
      <div className="flex items-center gap-3">
        <span className={`rounded-full px-2 py-0.5 text-xs ${state[1]}`}>{state[0]}</span>
        <label className="flex items-center gap-1.5 text-sm text-slate-600">
          <input type="checkbox" checked={source.enabled} disabled={!editable || busy} onChange={event => void save({ enabled: event.target.checked })} />启用
        </label>
      </div>
    </div>
    {source.blurb && <p className="text-sm text-slate-600">{source.blurb}</p>}
    {source.license && <p className="text-xs text-slate-500">许可：{source.license}</p>}
    {source.needs_key !== "none" && <div className="space-y-2">
      <p className="text-xs text-slate-500">
        {source.needs_key === "required" ? "需要 API Key。" : "可选令牌，不填也能用。"}
        {source.api_key?.configured ? ` 当前：${source.api_key.masked}（${source.key_from === "page" ? "本页保存" : "启动配置文件"}）` : " 当前未配置。"}
        {source.signup && <> <a className="text-indigo-700 underline" href={source.signup} target="_blank" rel="noreferrer">{source.signup.startsWith("mailto:") ? "发邮件申请" : "去申请"}</a></>}
      </p>
      {editable && <div className="flex flex-wrap items-center gap-2">
        <input aria-label={`${source.label} API Key`} type="password" autoComplete="off" className={`${inputClass} max-w-sm`} placeholder="粘贴新的 Key" value={key} disabled={busy} onChange={event => setKey(event.target.value)} />
        <Button disabled={busy || !key.trim()} onClick={() => void save({ api_key: key.trim() })}>保存 Key</Button>
        {source.api_key?.configured && <Button variant="secondary" disabled={busy} onClick={() => { if (window.confirm(`清除 ${source.label} 的 Key？清除后这个来源搜不到素材。`)) void save({ api_key: "" }); }}>清除</Button>}
      </div>}
    </div>}
    <div className="flex flex-wrap items-center gap-3">
      <Button variant="secondary" disabled={busy || !source.enabled} onClick={() => void runTest()}>测试</Button>
      {busy && <span className="text-xs text-slate-500">处理中…</span>}
      {test && <span role="status" className={`text-sm ${test.ok ? "text-emerald-700" : "text-amber-800"}`}>
        {test.ok ? `连接正常，搜到 ${test.hits} 条（${test.elapsed_ms} 毫秒）` : `测试失败：${test.reason}`}</span>}
    </div>
    {error && <ErrorBanner message={error} />}
  </article>;
}

export default function StockSourceSettings({ editable }: { editable: boolean }) {
  const sources = useQuery({ queryKey: ["open-media-settings", currentUser()], queryFn: () => api.get<{ items: Source[] }>("/settings/open-media"), retry: false });
  if (sources.isPending) return <Spinner label="读取素材数据源…" />;
  if (sources.error) return <ErrorBanner message={errorText(sources.error)} />;
  return <section aria-label="素材数据源" className="space-y-4 rounded-xl border border-slate-200 bg-white p-5">
    <div><h2 className="text-lg font-semibold">素材数据源</h2>
      <p className="mt-1 text-sm text-slate-500">给镜头找免费素材时搜索的素材库。关掉的来源不参与搜索；Key 只保存在后台，页面只显示掩码。测试只搜一条，不下载素材。</p></div>
    <div className="grid gap-3 lg:grid-cols-2">{sources.data!.items.map(source => <SourceCard key={source.key} source={source} editable={editable} onSaved={() => sources.refetch()} />)}</div>
  </section>;
}
