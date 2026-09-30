import { lazy, Suspense, useEffect, useRef, useState } from "react";
import { api, currentUser } from "../api";
import { Button, ErrorBanner, Spinner } from "../components/ui";
import type { Accepted, Preview } from "./ProviderMediaPanel";

const ProviderMediaPanel = lazy(() => import("./ProviderMediaPanel"));
export type RenderAsset = { material_revision_id: number; content_hash: string; kind: string; public_use_allowed: boolean };
export type GraphicRenderSource = { id: number; payload_hash: string; context_hash: string };
type Descriptor = { renderer_key: string; renderer_version: string; payload_schema: string; can_probe: boolean;
  can_request_execution: boolean; recorded_scopes: { verification_id: number; result: string; requestable: boolean;
    scope: { channel: string; content_form: string; output_mime: string } }[];
  supported_forms: { channel: string; content_form: string }[] };

export default function GraphicRenderPanel({ projectId, unitId, source, canvasId, channelId, contentForm, unavailable, onBind, onAssets }: {
  projectId: number; unitId: number; source: GraphicRenderSource; canvasId: string; channelId?: string | null; contentForm?: string | null;
  unavailable: boolean; onBind: (asset: RenderAsset) => void; onAssets: () => void;
}) {
  const [descriptors, setDescriptors] = useState<Descriptor[]>([]);
  const [preview, setPreview] = useState<Preview>();
  const [accepted, setAccepted] = useState<Accepted>();
  const [asset, setAsset] = useState<RenderAsset>();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [verification, setVerification] = useState<{ verification_id: number }>();
  const [verificationNotice, setVerificationNotice] = useState("");
  const active = useRef(true);
  const generation = useRef(0);
  const blocked = useRef(unavailable);
  blocked.current = unavailable;
  const identity = currentUser();
  useEffect(() => {
    active.current = true;
    void api.get<{ media_renderer_previews: Descriptor[] }>("/settings/capabilities")
      .then(result => { if (active.current) setDescriptors(result.media_renderer_previews); })
      .catch(() => { if (active.current) setError("渲染能力清单读取失败；不会调用未知实现。"); });
    return () => { active.current = false; generation.current += 1; };
  }, []);
  useEffect(() => {
    generation.current += 1;
    setPreview(undefined); setAccepted(undefined); setAsset(undefined); setBusy(false); setError("");
  }, [unavailable]);
  const descriptor = descriptors.find(item => item.payload_schema === "graphic.master.v2"
    && item.supported_forms.some(form => form.channel === channelId && form.content_form === contentForm));
  const recorded = descriptor?.recorded_scopes.find(row => row.scope.channel === channelId && row.scope.content_form === contentForm && row.scope.output_mime === "image/png");
  const canExecute = descriptor?.can_request_execution && recorded?.requestable;
  function live(token: number) { return active.current && generation.current === token && !blocked.current && currentUser() === identity; }
  async function probe() {
    if (unavailable || busy || preview || !descriptor || (!descriptor.can_probe && !canExecute)) return;
    const token = ++generation.current;
    setBusy(true); setError("");
    try {
      const result = await api.post<Preview>(`/content-projects/${projectId}/units/${unitId}/master-revisions/${source.id}/${descriptor.can_probe ? "media-render-previews" : "media-render-outputs"}`, {
        renderer_key: descriptor.renderer_key, renderer_version: descriptor.renderer_version,
        expected_payload_hash: source.payload_hash, expected_context_hash: source.context_hash, canvas_id: canvasId,
        ...(descriptor.can_probe ? {} : { output_mime: "image/png" }),
      });
      if (live(token)) setPreview(result);
    } catch (cause) { if (live(token)) setError(cause instanceof Error ? cause.message : "渲染失败；未保存素材，不会自动重试。"); }
    finally { if (live(token)) setBusy(false); }
  }
  async function refresh(saved: Accepted) {
    const token = generation.current;
    setBusy(true); setAsset(undefined); setError("");
    try {
      const items = await api.get<RenderAsset[]>(`/content-projects/${projectId}/shared-assets`);
      if (!live(token)) return;
      onAssets();
      const exact = items.find(item => item.material_revision_id === saved.material_revision_id && item.content_hash === saved.content_hash);
      if (!exact || exact.kind !== "image" || !exact.public_use_allowed) throw new Error("已接受图片当前不可公开使用或项目引用不匹配；保留素材，但不能绑定。");
      setAsset(exact);
    } catch (cause) { if (live(token)) setError(cause instanceof Error ? cause.message : "素材已接受，但刷新失败；不能绑定。可明确重读，不会重复接受。"); }
    finally { if (live(token)) setBusy(false); }
  }
  async function onAccepted(saved: Accepted) {
    if (!active.current || blocked.current || currentUser() !== identity) return;
    setAccepted(saved);
    await refresh(saved);
  }
  async function verifyScope() {
    if (!preview?.input_hash || !descriptor?.can_probe || unavailable || busy || !window.confirm("你已核对当前真实图片与此画布输入？仅验证此精确 Renderer/schema/channel/form/MIME 范围，不授予素材权利，也不改 Master。")) return;
    const token = generation.current;
    setBusy(true); setError("");
    try {
      const result = await api.post<{ verification_id: number }>("/settings/media-renderer-verifications", {
        stage_id: preview.stage_id, confirmed: true, expected_input_hash: preview.input_hash, expected_output_hash: preview.content_hash,
      });
      if (live(token)) { setVerification(result); setVerificationNotice("已记录此精确范围的验证，24 小时内请求仍由服务端检查当前运行环境。未改 Master/素材权利。"); }
    } catch (cause) { if (live(token)) setError(cause instanceof Error ? cause.message : "验证失败，未提升能力。"); }
    finally { if (live(token)) setBusy(false); }
  }
  async function revokeScope() {
    const id = verification?.verification_id ?? recorded?.verification_id;
    if (!id || !descriptor?.can_probe || unavailable || busy) return;
    const token = generation.current;
    setBusy(true); setError("");
    try {
      await api.post(`/settings/media-renderer-verifications/${id}/revoke`, {});
      if (live(token)) { setVerification(undefined); setVerificationNotice("已撤销此范围；历史验证和已保存素材不变。不会自动重新渲染。"); }
    } catch (cause) { if (live(token)) setError(cause instanceof Error ? cause.message : "撤销失败。"); }
    finally { if (live(token)) setBusy(false); }
  }
  return <section aria-label="图文渲染预览" className="space-y-3 rounded-xl border border-indigo-200 p-3">
    <h3 className="font-medium">真实画布渲染（管理员预览）</h3>
    <p className="text-xs text-slate-600">Master #{source.id} · 画布 {canvasId}。运行环境未探测；可尝试不等于已配置或已验证。当前仅支持显式配置字体的普通文字；缺字/样式会拒绝。</p>
    <p className="text-xs">渲染 → 明确接受素材 → 绑定到本地画布 → 单独保存 Master / 人工确认。不会自动入库、改稿、验证能力或发布。</p>
    {unavailable && <p role="status" className="text-amber-800 text-sm">当前有未保存修改，或版本/上下文只读；先保存当前稿或切回当前版本。</p>}
    {!descriptor?.can_probe && <p className="text-xs text-slate-500">仅管理员可探测；普通用户须有已记录的精确范围，请求时仍检查运行环境。</p>}
    <Button variant="secondary" disabled={unavailable || busy || !!preview || (!descriptor?.can_probe && !canExecute)} onClick={() => void probe()}>{busy && !preview ? "真实渲染中…" : descriptor?.can_probe ? "渲染当前已保存画布" : "按已记录范围请求渲染（服务端复核）"}</Button>
    {preview && descriptor?.can_probe && <Button variant="secondary" disabled={unavailable || busy || !preview.input_hash} onClick={() => void verifyScope()}>核对当前预览并验证此精确渲染范围（24 小时）</Button>}
    {descriptor?.can_probe && (verification || recorded) && <Button variant="secondary" disabled={unavailable || busy} onClick={() => void revokeScope()}>撤销此渲染范围验证</Button>}
    {verificationNotice && <p role="status" className="text-xs">{verificationNotice}</p>}
    {preview && <Suspense fallback={<Spinner label="读取渲染预览…" />}><ProviderMediaPanel key={preview.stage_id} initialPreview={preview}
      mediaOrigin="renderer" unavailable={unavailable} onAccepted={onAccepted}
      onDismiss={() => { generation.current += 1; setPreview(undefined); setAccepted(undefined); setAsset(undefined); setError(""); }} /></Suspense>}
    {accepted && !asset && <Button variant="secondary" disabled={unavailable || busy} onClick={() => void refresh(accepted)}>重新读取已接受的项目素材（不重复接受）</Button>}
    {asset && <Button variant="secondary" disabled={unavailable || busy} onClick={() => { if (!blocked.current) onBind(asset); }}>将接受的图片绑定到当前画布（仅本地）</Button>}
    {error && <ErrorBanner message={error} />}
  </section>;
}
