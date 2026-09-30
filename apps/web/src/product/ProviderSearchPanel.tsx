import { useState } from "react";
import { api } from "../api";
import { Button, ErrorBanner, Field, inputClass } from "../components/ui";
import ProviderMediaPanel, { type ObservedLicense, type Preview } from "./ProviderMediaPanel";

interface Candidate extends ObservedLicense { candidate_id: string; source_url: string | null; public_ready: false }
const reasons: Record<string, string> = {
  search_provider_failed: "公共搜索未能完成，可能是网络、来源限流或安全校验阻断。没有生成素材；可稍后明确重试。",
  search_license_unknown: "来源许可未知或当前不支持，不允许导入为可复用素材。",
  search_download_failed: "下载或文件版本校验失败，没有保存素材。请重新搜索核对来源。",
  search_runtime_changed: "搜索能力版本已变化，请重新搜索。",
  search_candidate_unavailable_or_expired: "候选已过期或不属于当前用户，请重新搜索。",
};

export default function ProviderSearchPanel() {
  const [query, setQuery] = useState("");
  const [projectId, setProjectId] = useState("");
  const [items, setItems] = useState<Candidate[]>([]);
  const [selected, setSelected] = useState<{ candidate: Candidate; preview: Preview }>();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  function report(cause: unknown) { const reason = cause instanceof Error ? cause.message : "请求失败"; setError(reasons[reason] ?? reason); }
  async function search() {
    setBusy(true); setError(""); setItems([]); setSelected(undefined);
    try { const result = await api.post<{ items: Candidate[] }>("/provider-search", { provider_key: "search.wikimedia.commons", provider_version: "1", query: query.trim(), limit: 10 }); setItems(result.items); }
    catch (cause) { report(cause); }
    finally { setBusy(false); }
  }
  async function choose(candidate: Candidate) {
    setBusy(true); setError("");
    try {
      const preview = await api.post<Preview>(`/provider-search/${candidate.candidate_id}/stage`, projectId ? { project_id: Number(projectId) } : {});
      setSelected({ candidate, preview });
    } catch (cause) { report(cause); }
    finally { setBusy(false); }
  }
  return <section aria-label="公共素材搜索" className="space-y-4 rounded-xl border bg-white p-5">
    <h2 className="font-semibold">Wikimedia 公共素材搜索</h2>
    <p className="text-sm text-slate-600">明确搜索才读取公共来源，最多 10 个候选；选择后才下载不超过 5 MB 的图片。来源许可不是你的使用授权，必须另行核对、确认。候选约 15 分钟有效。</p>
    <form className="flex flex-wrap items-end gap-3" onSubmit={(event) => { event.preventDefault(); void search(); }}>
      <Field label="公共素材关键词"><input className={inputClass} maxLength={300} value={query} disabled={busy || !!selected} onChange={(event) => setQuery(event.target.value)} /></Field>
      <Field label="同时引用到项目 ID（可选）"><input className={inputClass} type="number" min={1} step={1} value={projectId} disabled={busy || !!selected} onChange={(event) => setProjectId(event.target.value)} /></Field>
      <Button type="submit" disabled={busy || !!selected || !query.trim()}>{busy ? "读取中…" : "明确搜索公共素材"}</Button>
    </form>
    {error && <ErrorBanner message={error} />}
    {selected ? <ProviderMediaPanel key={selected.preview.stage_id} initialPreview={selected.preview} observedLicense={selected.candidate} onDismiss={() => setSelected(undefined)} /> : <ul className="space-y-3">{items.map((candidate) => <li key={candidate.candidate_id} className="space-y-2 rounded-lg border p-3">
      <h3 className="font-medium">{candidate.title}</h3><p className="text-sm">许可：{candidate.license_code === "unknown" ? "未知 / 当前不支持" : candidate.license_code} · 尚未入库，不具公开使用资格</p>
      {candidate.attribution_text && <p className="text-sm text-slate-600">署名：{candidate.attribution_text}</p>}
      {candidate.source_url && <a className="mr-3 text-sm text-indigo-700 underline" href={candidate.source_url} target="_blank" rel="noreferrer">打开公共来源核对许可</a>}
      <Button variant="secondary" disabled={busy || candidate.license_code === "unknown" || (projectId !== "" && (!Number.isSafeInteger(Number(projectId)) || Number(projectId) < 1))} onClick={() => void choose(candidate)}>下载临时预览</Button>
    </li>)}</ul>}
  </section>;
}
