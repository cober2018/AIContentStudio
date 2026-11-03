import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api, ApiError, currentUser } from "../../api";
import { ErrorBanner } from "../../components/ui";

type Template = { id: string; name: string; need_source: string[]; sources: string[]; not_sources: string[]; freshness: string; red_lines: string[]; opinion_only: string[] };
type FactItem = { id: number; kind: "fact" | "event" | "quote" | "opinion"; statement: string; excerpt: string | null; attribution: string | null; source_url: string | null; source_date: string | null; labels: string[] };
type Current = { revision_no: number; fact_pack_id: number; items: FactItem[]; labelled: number };
type View = { templates: Template[]; chosen: string[]; suggested: string[]; current: Current | null; stale_works: { unit_id: number; title: string }[] };

const KIND: Record<FactItem["kind"], string> = { fact: "事实", event: "事件", quote: "引语", opinion: "专家观点" };

function useView(projectId: number) {
  return useQuery({ queryKey: ["fact-templates", currentUser(), projectId], queryFn: () => api.get<View>(`/content-projects/${projectId}/fact-templates`), retry: false });
}

function errorText(error: unknown) {
  const detail = error instanceof ApiError ? error.detail as { message?: string } | string | undefined : undefined;
  return (typeof detail === "string" ? detail : detail?.message) || (error instanceof Error ? error.message : "操作失败");
}

// Which topic templates this project's fact boundary follows; the model drafts by them.
export function FactTemplatePicker({ projectId, readOnly }: { projectId: number; readOnly: boolean }) {
  const client = useQueryClient();
  const query = useView(projectId);
  const [busy, setBusy] = useState(false);
  const [issue, setIssue] = useState("");
  const data = query.data;
  if (!data) return query.isError ? <ErrorBanner message="题材模板读取失败" /> : null;
  async function toggle(id: string) {
    const next = data!.chosen.includes(id) ? data!.chosen.filter(item => item !== id) : [...data!.chosen, id];
    setBusy(true); setIssue("");
    try { await api.put(`/content-projects/${projectId}/fact-templates`, { templates: next }); await client.invalidateQueries({ queryKey: ["fact-templates"] }); }
    catch (error) { setIssue(errorText(error)); } finally { setBusy(false); }
  }
  const picked = data.templates.filter(item => data.chosen.includes(item.id));
  return <section className="space-y-3 rounded-xl border border-slate-200 bg-white p-4" aria-label="题材模板">
    <div><h3 className="text-sm font-semibold">题材模板</h3><p className="text-xs text-slate-500">决定这条内容哪些话要有出处、认哪些来源、有哪些红线。第三方模型会按选题自己选，选错了在这里改；标「建议」的是按选题和角色定位推荐的。</p></div>
    {issue && <ErrorBanner message={issue} />}
    <div className="flex flex-wrap gap-2">{data.templates.map(item => <label key={item.id} className={`flex items-center gap-1 rounded-lg border px-2 py-1 text-sm ${data.chosen.includes(item.id) ? "border-indigo-400 bg-indigo-50" : "border-slate-200"}`}>
      <input type="checkbox" checked={data.chosen.includes(item.id)} disabled={readOnly || busy} onChange={() => void toggle(item.id)} />{item.name}
      {data.suggested.includes(item.id) && <span className="rounded bg-amber-100 px-1 text-xs text-amber-800">建议</span>}
    </label>)}</div>
    {!picked.length && <p className="text-xs text-slate-500">还没选，第三方模型交事实时会按选题选上。</p>}
    {picked.map(item => <div key={item.id} className="rounded-lg bg-slate-50 p-2 text-xs text-slate-600">
      <p className="font-medium text-slate-800">{item.name}</p>
      <p>要有出处的话：{item.need_source.join("、")}</p>
      <p>认的来源：{item.sources.join("、")}；不认：{item.not_sources.join("、")}</p>
      <p>时效：{item.freshness}</p>
      <p>红线：{item.red_lines.join("；")}</p>
      <p>只能当个人经历或观点说：{item.opinion_only.join("、")}</p>
    </div>)}
    {data.stale_works.length > 0 && <p className="rounded-lg bg-amber-50 p-2 text-xs text-amber-800">事实边界已更新：{data.stale_works.map(item => `「${item.title}」`).join("")}的稿子是按旧的事实边界存的，要让第三方模型按新事实重新保存一版。</p>}
  </section>;
}

function FactList({ items }: { items: FactItem[] }) {
  return <ul className="space-y-2">{items.map((item, index) => <li key={item.id} className="rounded-lg border border-slate-200 p-3 text-sm">
    <p className="font-medium">{index + 1}. {item.statement}</p>
    <p className="mt-1 text-xs text-slate-500">{KIND[item.kind] || item.kind}{item.attribution ? ` · ${item.attribution}` : ""}{item.source_date ? ` · ${item.source_date}` : ""}</p>
    {item.excerpt && <p className="mt-1 text-xs text-slate-600">原文：「{item.excerpt}」</p>}
    {item.source_url && <a className="mt-1 block break-all text-xs text-indigo-700 underline" href={item.source_url} target="_blank" rel="noreferrer">{item.source_url}</a>}
    {item.labels.length > 0 && <p className="mt-1 flex flex-wrap gap-1">{item.labels.map(label => <span key={label} className="rounded bg-amber-100 px-1.5 text-xs text-amber-800">{label}</span>)}</p>}
  </li>)}</ul>;
}

// The frozen boundary, read-only: the model submitted it and the platform checked every source.
export function FactBoundaryView({ projectId }: { projectId: number }) {
  const data = useView(projectId).data;
  if (!data) return null;
  const current = data.current;
  return <section className="space-y-3 rounded-xl border border-slate-200 bg-white p-6" aria-label="当前事实边界">
    <div><h2 className="font-semibold">当前事实边界</h2><p className="text-xs text-slate-500">第三方模型按题材模板交上来、平台逐条打开来源核对过的事实；打不开、原文对不上的已退回，没收进来。只读。</p></div>
    {current ? <><p className="text-sm">第 {current.revision_no} 版 · {current.items.length} 条{current.labelled ? ` · ${current.labelled} 条带标注` : ""}</p><FactList items={current.items} /></>
      : <p className="text-sm text-slate-500">还没有。第三方模型写导演稿或文章前会按模板交事实，核对通过后自动出现在这里。</p>}
  </section>;
}

// One line under the draft being reviewed; nothing to operate, the list opens on demand.
export function FactSummary({ projectId }: { projectId: number }) {
  const data = useView(projectId).data;
  const [open, setOpen] = useState(false);
  if (!data) return null;
  const current = data.current;
  if (!current) return <p className="rounded-lg bg-slate-50 p-2 text-xs text-slate-500">本稿用到的事实：还没有核对过出处的事实。</p>;
  return <div className="rounded-lg bg-slate-50 p-2 text-xs text-slate-600">
    <button type="button" className="text-left" onClick={() => setOpen(value => !value)}>本稿用到的事实：{current.items.length} 条已核对出处{current.labelled ? `（${current.labelled} 条来源不在常见权威网站或可能过期）` : ""}<span className="ml-1 text-indigo-700 underline">{open ? "收起" : "看来源"}</span></button>
    {data.stale_works.length > 0 && <p className="mt-1 text-amber-800">事实边界更新过：{data.stale_works.map(item => `「${item.title}」`).join("")}的稿子是按旧事实存的，要让第三方模型重存一版。</p>}
    {open && <div className="mt-2"><FactList items={current.items} /></div>}
  </div>;
}
