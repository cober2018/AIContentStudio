import { useQuery } from "@tanstack/react-query";
import { api, currentUser } from "../api";
import { ErrorBanner, Spinner } from "../components/ui";

type Guidance = { kind: string; label: string; setup: string; execution_status: string;
  adapters: { key: string; version: string; saved_configuration: boolean; configuration_status: string; verified: false }[] };

export default function ProviderGuidancePanel() {
  const inventory = useQuery({ queryKey: ["capabilities", currentUser()], queryFn: () => api.get<{ provider_guidance: Guidance[] }>("/settings/capabilities") });
  return <section className="min-w-0 space-y-3 text-slate-700" aria-label="Provider 配置指引">
    <h3 className="text-sm font-semibold text-slate-900">素材与音视频接入说明</h3>
    <p className="text-xs leading-5 text-slate-500">这里只读展示协议与保存记录，不读取密钥、不探测网络、不调用供应商。配置记录与协议加载都不证明某项能力可执行或已通过真实验证。</p>
    {inventory.isPending && <Spinner label="读取 Provider 指引…" />}
    {inventory.error && <ErrorBanner message={inventory.error instanceof Error ? inventory.error.message : "配置指引读取失败"} />}
    {inventory.data?.provider_guidance.map((row) => <details key={row.kind} className="min-w-0 rounded-lg border border-slate-200 bg-white p-3">
      <summary className="cursor-pointer text-sm font-medium focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-slate-500">{row.label} <span className="font-normal text-slate-500">· {row.adapters.some(adapter => adapter.saved_configuration) ? "有保存记录" : "无保存记录"}</span></summary>
      <div className="mt-3 space-y-2">
        <p className="text-xs text-slate-500">{row.execution_status === "unavailable" ? "此类别暂无可用实现；不代表其他类别或厂商连接失败。" : "此类别协议已加载；实际配置、执行和验证状态需按对应能力另行检查。"}</p>
        <p className="break-words text-sm leading-6">{row.setup}</p>
        {row.adapters.map((adapter) => <p className="break-all text-xs text-slate-500" key={`${adapter.key}:${adapter.version}`}>{adapter.key} / {adapter.version} · {adapter.saved_configuration ? "有配置记录，当前配置未检查" : "无持久配置记录"} · 本指引不提供真实验证结果</p>)}
      </div>
    </details>)}
  </section>;
}
