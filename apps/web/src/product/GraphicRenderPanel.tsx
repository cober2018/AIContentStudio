import { lazy, Suspense, useEffect, useRef, useState } from "react";
import { api, currentUser } from "../api";
import { Button, ErrorBanner, Spinner } from "../components/ui";
import type { Accepted, Preview } from "./ProviderMediaPanel";

const ProviderMediaPanel = lazy(() => import("./ProviderMediaPanel"));
export type RenderAsset = { material_revision_id: number; content_hash: string; kind: string; public_use_allowed: boolean };
export type GraphicRenderSource = { id: number; payload_hash: string; context_hash: string };
type Descriptor = { renderer_key: string; renderer_version: string; payload_schema: string; can_probe: boolean;
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
  function live(token: number) { return active.current && generation.current === token && !blocked.current && currentUser() === identity; }
  async function probe() {
    if (unavailable || busy || preview || !descriptor?.can_probe) return;
    const token = ++generation.current;
    setBusy(true); setError("");
    try {
      const result = await api.post<Preview>(`/content-projects/${projectId}/units/${unitId}/master-revisions/${source.id}/media-render-previews`, {
        renderer_key: descriptor.renderer_key, renderer_version: descriptor.renderer_version,
        expected_payload_hash: source.payload_hash, expected_context_hash: source.context_hash, canvas_id: canvasId,
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
  return <section aria-label="图文渲染预览" className="space-y-3 rounded-xl border border-indigo-200 p-3">
    <h3 className="font-medium">真实画布渲染（管理员预览）</h3>
    <p className="text-xs text-slate-600">Master #{source.id} · 画布 {canvasId}。运行环境未探测；可尝试不等于已配置或已验证。当前仅支持显式配置字体的普通文字；缺字/样式会拒绝。</p>
    <p className="text-xs">渲染 → 明确接受素材 → 绑定到本地画布 → 单独保存 Master / 人工确认。不会自动入库、改稿、验证能力或发布。</p>
    {unavailable && <p role="status" className="text-amber-800 text-sm">当前有未保存修改，或版本/上下文只读；先保存当前稿或切回当前版本。</p>}
    {!descriptor?.can_probe && <p className="text-xs text-slate-500">仅管理员可探测已加载且支持当前渠道/形态的 Renderer；普通执行尚未验证。</p>}
    <Button variant="secondary" disabled={unavailable || busy || !!preview || !descriptor?.can_probe} onClick={() => void probe()}>{busy && !preview ? "真实渲染中…" : "渲染当前已保存画布"}</Button>
    {preview && <Suspense fallback={<Spinner label="读取渲染预览…" />}><ProviderMediaPanel key={preview.stage_id} initialPreview={preview}
      mediaOrigin="renderer" unavailable={unavailable} onAccepted={onAccepted}
      onDismiss={() => { generation.current += 1; setPreview(undefined); setAccepted(undefined); setAsset(undefined); setError(""); }} /></Suspense>}
    {accepted && !asset && <Button variant="secondary" disabled={unavailable || busy} onClick={() => void refresh(accepted)}>重新读取已接受的项目素材（不重复接受）</Button>}
    {asset && <Button variant="secondary" disabled={unavailable || busy} onClick={() => { if (!blocked.current) onBind(asset); }}>将接受的图片绑定到当前画布（仅本地）</Button>}
    {error && <ErrorBanner message={error} />}
  </section>;
}
