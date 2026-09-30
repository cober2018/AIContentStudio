import { useQuery } from "@tanstack/react-query";
import { api, currentUser } from "../api";
import { ErrorBanner, Spinner } from "../components/ui";

type Guidance = { kind: string; label: string; setup: string; execution_status: string;
  adapters: { key: string; version: string; saved_configuration: boolean; configuration_status: string; verified: false }[] };

export default function ProviderGuidancePanel() {
  const inventory = useQuery({ queryKey: ["capabilities", currentUser()], queryFn: () => api.get<{ provider_guidance: Guidance[] }>("/settings/capabilities") });
  return <section className="space-y-3 rounded-xl border border-indigo-100 p-4" aria-label="Provider 配置指引">
    <h3 className="font-semibold">素材与音视频 Provider 配置指引</h3>
    <p className="text-sm text-slate-600">这里只读加载协议和已保存配置记录，不读密钥、不探测网络、不调用 Provider。已加载 / 配置记录不代表执行可用或真实外部验证。</p>
    {inventory.isPending && <Spinner label="读取 Provider 指引…" />}
    {inventory.error && <ErrorBanner message={inventory.error instanceof Error ? inventory.error.message : "配置指引读取失败"} />}
    {inventory.data?.provider_guidance.map((row) => <article key={row.kind} className="space-y-2 rounded-lg border bg-white p-3">
      <h4 className="font-medium">{row.label}</h4>
      <p className="text-sm">{row.execution_status === "unavailable" ? "未接入可用实现" : "协议已加载；真实执行与配置待明确调用时检查，尚未外部验证"}</p>
      <p className="text-xs text-slate-600">{row.setup}</p>
      {row.adapters.map((adapter) => <p className="text-xs" key={`${adapter.key}:${adapter.version}`}>{adapter.key} / {adapter.version} · {adapter.saved_configuration ? "有配置记录，当前配置未检查" : "无持久配置记录"} · 未验证</p>)}
    </article>)}
  </section>;
}
