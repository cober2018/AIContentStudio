import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api, currentUser } from "../api";
import { Button, ErrorBanner, Spinner } from "../components/ui";

type Plugin = {
  key: string;
  label: string;
  plugged: boolean;
  selectable: boolean;
  historical_only: boolean;
  methods: string[];
};
type Catalog = { items: Plugin[]; note: string };

export default function ChannelPluginPanel() {
  const client = useQueryClient();
  const me = useQuery({ queryKey: ["product-settings-user", currentUser()], queryFn: () => api.get<{ role: string }>("/users/me"), retry: false });
  const plugins = useQuery({ queryKey: ["channel-plugins", currentUser()], queryFn: () => api.get<Catalog>("/channels/plugins"), retry: false });
  const [pending, setPending] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const admin = me.data?.role === "admin";

  async function toggle(item: Plugin) {
    setPending(item.key);
    setError(null);
    try {
      await api.post(`/channels/plugins/${item.key}/${item.plugged ? "unplug" : "plug"}`);
      await client.invalidateQueries({ queryKey: ["channel-plugins"] });
      await client.invalidateQueries({ queryKey: ["channels"] });
    } catch (err) {
      setError(err instanceof Error ? err.message : "插拔失败");
    } finally {
      setPending(null);
    }
  }

  return <section aria-label="渠道方法插件" className="space-y-3 rounded-lg border border-slate-200 p-4">
    <div className="flex flex-wrap items-center justify-between gap-3">
      <h2 className="text-sm font-semibold text-slate-900">渠道方法</h2>
      <Button variant="secondary" disabled={plugins.isFetching} onClick={() => void plugins.refetch()}>{plugins.isFetching ? "刷新中…" : "刷新插拔状态"}</Button>
    </div>
    <p className="text-sm leading-relaxed text-slate-600">每个渠道的专用方法可以单独拔出。拔出后它不再出现在新选题里，已有稿件还在，其他渠道和主程序继续运行。更新好之后再插上，立即生效，不用重启，也不用改主程序。这里不能上传代码。</p>
    {plugins.isPending && <Spinner label="读取渠道方法…" />}
    {plugins.isError && <ErrorBanner message={plugins.error instanceof Error ? plugins.error.message : "渠道方法读取失败"} />}
    {error && <ErrorBanner message={error} />}
    {plugins.data && <ul className="space-y-2">
      {plugins.data.items.map(item => <li key={item.key} className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-slate-100 px-3 py-3">
        <div className="min-w-0">
          <p className="text-sm font-medium text-slate-900">{item.label}<span className="ml-2 text-xs font-normal text-slate-500">{item.key}</span></p>
          <p className="mt-1 text-xs leading-relaxed text-slate-500">{item.methods.join("、") || "通用方法"}{item.historical_only ? "。插上也不会回到可选渠道。" : ""}</p>
        </div>
        <div className="flex items-center gap-2">
          <span className={`text-xs ${item.plugged ? "text-emerald-700" : "text-amber-800"}`}>{item.plugged ? "已插上" : "已拔出"}</span>
          <Button variant={item.plugged ? "danger" : "primary"} size="sm" disabled={!admin || pending !== null} onClick={() => void toggle(item)}>{pending === item.key ? "处理中…" : item.plugged ? "拔出" : "插上"}</Button>
        </div>
      </li>)}
    </ul>}
    {plugins.data && <p className="text-xs leading-relaxed text-slate-500">{plugins.data.note}{admin ? "" : " 只有管理员可以插拔。"}</p>}
  </section>;
}
