import { useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { api, currentUser } from "../api";
import { Button, ErrorBanner, Field, inputClass } from "../components/ui";

export interface Preview {
  stage_id: string;
  content_hash: string;
  mime_type: string;
  kind: string;
  provider_key: string;
  provider_version: string;
  expires_in_seconds: number;
  input_hash?: string;
}
export interface Accepted { material_id: number; material_revision_id: number; content_hash: string }
const reasons: Record<string, string> = {
  capability_unavailable: "当前生图能力未配置或不可执行，请先在设置中配置真实 Provider。",
  provider_preview_unavailable_or_expired: "预览已过期或不属于当前用户，请明确重新生成。",
  provider_outcome_unknown: "生成结果未知。未入库，请先核对 Provider，不会自动重试。",
  provider_runtime_changed: "Provider 配置已变化，此预览不能接受，请重新生成。",
  provider_output_decode_failed: "Provider 返回的媒体不能真实解码，未保存任何素材。",
  provider_attribution_required: "此许可要求填写作者及署名。",
};

export interface ObservedLicense {
  title: string;
  license_code: string;
  license_evidence_hash: string;
  attribution_text: string | null;
}

export default function ProviderMediaPanel({ initialPreview, observedLicense, onDismiss, mediaOrigin, unavailable = false, onAccepted }: { initialPreview?: Preview; observedLicense?: ObservedLicense; onDismiss?: () => void; mediaOrigin?: "renderer"; unavailable?: boolean; onAccepted?: (accepted: Accepted) => void | Promise<void> }) {
  const queryClient = useQueryClient();
  const [prompt, setPrompt] = useState("");
  const [title, setTitle] = useState(observedLicense?.title ?? "");
  const [preview, setPreview] = useState<Preview | undefined>(initialPreview);
  const [accepted, setAccepted] = useState<Accepted>();
  const [url, setUrl] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [license, setLicense] = useState(observedLicense?.license_code ?? "provider_terms");
  const [licenseHash, setLicenseHash] = useState(observedLicense?.license_evidence_hash ?? "");
  const [attribution, setAttribution] = useState(observedLicense?.attribution_text ?? "");
  const [confirmed, setConfirmed] = useState(false);
  const [rights, setRights] = useState({ public: false, model: false, commercial: false });
  const objectUrl = useRef("");
  const mounted = useRef(true);
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; if (objectUrl.current) URL.revokeObjectURL(objectUrl.current); }; }, []);
  useEffect(() => {
    if (!initialPreview) return;
    const controller = new AbortController();
    setBusy(true);
    void (async () => {
      try {
        const response = await fetch(`/api/v1/provider-media/${initialPreview.stage_id}/raw`, { signal: controller.signal, headers: { "X-Studio-User": currentUser() }, cache: "no-store" });
        if (!response.ok) throw new Error("预览不可用或已过期，请重新明确选择候选。");
        const blob = await response.blob();
        if (controller.signal.aborted) return;
        objectUrl.current = URL.createObjectURL(blob); setUrl(objectUrl.current);
      } catch (cause) { if (!controller.signal.aborted) report(cause); }
      finally { if (!controller.signal.aborted) setBusy(false); }
    })();
    return () => controller.abort();
  }, [initialPreview]);
  function report(cause: unknown) {
    const reason = cause instanceof Error ? cause.message : "请求失败";
    setError(reasons[reason] ?? reason);
  }
  function reset() {
    if (onDismiss) { onDismiss(); return; }
    if (objectUrl.current) URL.revokeObjectURL(objectUrl.current);
    objectUrl.current = ""; setUrl(""); setPreview(undefined); setAccepted(undefined);
    setConfirmed(false); setRights({ public: false, model: false, commercial: false }); setError("");
  }
  async function generate() {
    setBusy(true); setError("");
    try {
      const result = await api.post<Preview>("/materials/generate", { prompt });
      if (!mounted.current) return;
      setPreview(result);
      const response = await fetch(`/api/v1/provider-media/${result.stage_id}/raw`, { headers: { "X-Studio-User": currentUser() }, cache: "no-store" });
      if (!response.ok) throw new Error("预览读取失败；没有入库，请重新生成预览。");
      const blob = await response.blob();
      if (!mounted.current) return;
      objectUrl.current = URL.createObjectURL(blob); setUrl(objectUrl.current);
    } catch (cause) { if (mounted.current) report(cause); }
    finally { if (mounted.current) setBusy(false); }
  }
  async function accept() {
    if (!preview || unavailable || busy || accepted) return;
    setBusy(true); setError("");
    try {
      const saved = await api.post<Accepted>(`/provider-media/${preview.stage_id}/accept`, {
        confirmed, title: title.trim(), license_code: license, license_evidence_hash: licenseHash.trim(),
        public_use_allowed: rights.public, model_use_allowed: rights.model, commercial_use_allowed: rights.commercial,
        attribution_text: attribution.trim() || null,
      });
      if (!mounted.current) return;
      setAccepted(saved);
      await onAccepted?.(saved);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["system-library"] }),
        queryClient.invalidateQueries({ queryKey: ["materials"] }),
      ]);
    } catch (cause) { if (mounted.current) report(cause); }
    finally { if (mounted.current) setBusy(false); }
  }
  const disabled = unavailable || busy || accepted !== undefined;
  return <section aria-label={mediaOrigin === "renderer" ? "渲染预览与接受" : observedLicense ? "素材预览与接受" : "生成预览与接受"} className="space-y-4 rounded-xl border bg-white p-5">
    <h2 className="font-semibold">{mediaOrigin === "renderer" ? "渲染图片：先预览，再接受" : observedLicense ? "搜索素材：核对许可后接受" : "AI 素材：先预览，再接受"}</h2>
    <p className="text-sm text-slate-600">{mediaOrigin === "renderer" ? "这是已保存画布的真实渲染结果，不会调用生图模型，也没有自动授予素材权利。" : observedLicense ? "已下载临时预览，尚未入库。下列来源许可摘要已固定，不能将它改成另一种许可；请在原始来源核对署名和使用义务。" : "会调用已配置的真实生图 Provider，可能产生费用。"}预览不表示已验证或可公开发布；约 15 分钟有效，服务重启后失效。</p>
    {!observedLicense && !mediaOrigin && <Field label="生成描述"><textarea className={`${inputClass} h-24`} maxLength={2000} value={prompt} disabled={busy || !!preview} onChange={(event) => setPrompt(event.target.value)} /></Field>}
    {!preview && <Button disabled={busy || !prompt.trim()} onClick={() => void generate()}>{busy ? "生成中…" : "调用 Provider 生成预览"}</Button>}
    {preview && <>
      {url && (/^image\/(png|jpeg|webp)$/.test(preview.mime_type) ? <img src={url} alt={mediaOrigin === "renderer" ? "未入库的渲染预览" : "未入库的生成预览"} className="max-h-80 rounded-lg object-contain" /> : preview.kind === "audio" ? <audio src={url} controls /> : <video src={url} controls className="max-h-80" />)}
      <p className="break-all text-xs text-slate-500">{preview.provider_key}@{preview.provider_version} · SHA256 {preview.content_hash}</p>
      <Field label="素材标题"><input className={inputClass} maxLength={200} value={title} disabled={disabled} onChange={(event) => setTitle(event.target.value)} /></Field>
      <Field label="你已核对的许可"><select aria-label="你已核对的许可" className={inputClass} value={license} disabled={disabled || !!observedLicense} onChange={(event) => { setLicense(event.target.value); setConfirmed(false); }}><option value="provider_terms">Provider 许可条款</option><option value="owned">本人拥有权利</option><option value="CC0">CC0</option><option value="CC-BY-4.0">CC BY 4.0</option></select></Field>
      <Field label="许可依据文件 SHA256（不上传原文或秘密）"><input className={inputClass} value={licenseHash} maxLength={64} disabled={disabled} readOnly={!!observedLicense} onChange={(event) => { setLicenseHash(event.target.value); setConfirmed(false); }} placeholder="已核对条款/权利依据的 64 位哈希" /></Field>
      <Field label="署名 / 来源说明（CC BY 必填）"><input className={inputClass} maxLength={1000} value={attribution} disabled={disabled} readOnly={!!observedLicense} onChange={(event) => { setAttribution(event.target.value); setConfirmed(false); }} /></Field>
      <div className="flex flex-wrap gap-4 text-sm">{([['public', '允许公开使用'], ['model', '允许模型使用'], ['commercial', '允许商业使用']] as const).map(([key, label]) => <label key={key}><input type="checkbox" className="mr-2" checked={rights[key]} disabled={disabled} onChange={(event) => { setRights((previous) => ({ ...previous, [key]: event.target.checked })); setConfirmed(false); }} />{label}</label>)}</div>
      <label className="block text-sm"><input type="checkbox" className="mr-2" checked={confirmed} disabled={disabled} onChange={(event) => setConfirmed(event.target.checked)} />我已看过媒体并核对上述许可、署名与使用权；这是人工确认，不是系统验证。</label>
      {!accepted && <Button disabled={unavailable || busy || !url || !confirmed || !title.trim() || !/^[0-9a-f]{64}$/.test(licenseHash.trim()) || (license === "CC-BY-4.0" && !attribution.trim())} onClick={() => void accept()}>{busy ? "保存中…" : "明确接受并保存素材版本"}</Button>}
      {accepted && <p role="status" className="text-sm text-emerald-700">已保存精确素材版本 #{accepted.material_revision_id}，素材 #{accepted.material_id}。未修改 Master、身份或发布状态。</p>}
      <Button variant="secondary" disabled={busy} onClick={reset}>{accepted ? mediaOrigin === "renderer" ? "关闭此渲染结果" : "生成下一份素材" : "放弃此预览"}</Button>
    </>}
    {error && <ErrorBanner message={error} />}
  </section>;
}
