import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, currentUser } from "../api";
import { Button, ErrorBanner, Spinner } from "../components/ui";

export type RendererCapability = {
  renderer_key: string; renderer_version: string; modality: string; payload_schema: string;
  output_mimes: string[]; mode: "deterministic" | "manual"; verified: boolean; executable: boolean;
  scope?: { channel: string; content_form: string; output_mime: string };
  last_verification?: { result: string; expires_at: string | null };
};
type Inventory = { renderers: RendererCapability[]; can_verify: boolean };
type Master = { id: number; payload_schema: string; payload_hash: string; context_hash: string; channel_id: string | null; content_form: string | null };

export default function RendererVerificationPanel({ projectId, unitId, master, unavailable }: {
  projectId: number; unitId: number; master: Master; unavailable: boolean;
}) {
  const cache = useQueryClient();
  const identity = currentUser();
  const key = ["capabilities", identity];
  const inventory = useQuery({ queryKey: key, queryFn: () => api.get<Inventory>("/settings/capabilities") });
  const version = master.payload_schema === "text.master.v2" ? "2" : "1";
  const rendererKey = version === "2" ? "text.studio.document.v1" : "text.markdown.v1";
  const scope = inventory.data?.renderers.find((item) => item.renderer_key === rendererKey && item.renderer_version === version
    && item.scope?.channel === master.channel_id && item.scope?.content_form === master.content_form && item.scope?.output_mime === "text/markdown");
  const action = useMutation({ mutationFn: (result: "verified" | "revoked") => api.post("/settings/renderer-probes", {
    project_id: projectId, unit_id: unitId, master_id: master.id, renderer_key: rendererKey, renderer_version: version,
    expected_payload_hash: master.payload_hash, expected_context_hash: master.context_hash, result,
  }), onSuccess: () => cache.invalidateQueries({ queryKey: key }) });
  const error = action.error || inventory.error;
  const disabled = unavailable || action.isPending || !master.channel_id || !master.content_form;
  return <section aria-label="文字渲染验证" className="space-y-2 rounded-lg border border-indigo-100 bg-indigo-50/30 p-3">
    <h3 className="font-medium">文字渲染能力</h3>
    <p className="text-xs text-slate-600">{rendererKey} / {version} · {master.channel_id || "未选择渠道"} / {master.content_form || "未选择形态"} → Markdown</p>
    <p className="text-sm">{scope?.verified ? "当前精确范围已验证" : "当前精确范围尚未验证 / 已失效"}</p>
    <p className="text-xs text-slate-600">验证会实际渲染已保存的当前版本，只记录输入与输出摘要；不会保存 Master、批准内容或发布。它是能力验证，不代表此稿已通过审核。</p>
    {scope?.last_verification && <p className="text-xs">最近结果：{scope.last_verification.result} · 到期：{scope.last_verification.expires_at || "已撤销"}</p>}
    {inventory.isPending && <Spinner label="读取渲染状态…" />}
    {error && <ErrorBanner message={error instanceof Error ? error.message : "渲染验证失败"} />}
    <div className="flex flex-wrap gap-2">
      <Button size="sm" variant="secondary" disabled={inventory.isFetching || action.isPending} onClick={() => void inventory.refetch()}>刷新渲染状态</Button>
      {inventory.data?.can_verify && <>
        <Button size="sm" disabled={disabled} onClick={() => action.mutate("verified")}>实际渲染并验证</Button>
        <Button size="sm" variant="danger" disabled={disabled || !scope?.verified} onClick={() => { if (window.confirm("撤销当前范围的渲染验证？历史证据会保留。")) action.mutate("revoked"); }}>撤销渲染验证</Button>
      </>}
    </div>
    {unavailable && <p className="text-xs text-amber-800">请先保存当前内容；历史、归档、未保存或过期上下文不能发起验证。</p>}
    {inventory.data && !inventory.data.can_verify && <p className="text-xs text-slate-500">当前身份只读；管理员可明确发起验证。</p>}
  </section>;
}
