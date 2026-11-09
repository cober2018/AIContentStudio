import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, ApiError, currentUser } from "../api";
import { Button, ErrorBanner, inputClass } from "../components/ui";

type Chain = { writer: "platform" | "external"; state: string; label: string; detail?: string; locked?: boolean; notes?: { note: string }[]; master_id: number | null;
  review?: { state: "not_sent" | "rendered" | "sent" | "failed"; message?: string; candidate_id?: number };
  renders?: { canvas_id: string; material_id: number | null; material_revision_id: number }[] };

function RenderImage({ item, index }: { item: { material_id: number | null; material_revision_id: number }; index: number }) {
  const [url, setUrl] = useState("");
  useEffect(() => {
    let objectUrl = "";
    let alive = true;
    if (item.material_id) fetch(`/api/v1/materials/${item.material_id}/revisions/${item.material_revision_id}/raw`, { headers: { "X-Studio-User": currentUser() } }).then(async response => {
      if (!response.ok) return;
      objectUrl = URL.createObjectURL(await response.blob());
      if (alive) setUrl(objectUrl);
    }).catch(() => {});
    return () => { alive = false; if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [item.material_id, item.material_revision_id]);
  return <figure className="space-y-1">
    {url ? <a href={url} target="_blank" rel="noreferrer"><img src={url} alt={`第 ${index + 1} 张成图`} className="w-full rounded border border-slate-200" /></a> : <div className="aspect-[3/4] w-full rounded bg-slate-100" />}
    <figcaption className="text-center text-[11px] text-slate-500">第 {index + 1} 张{index === 0 ? "（封面）" : ""}</figcaption>
  </figure>;
}
type Version = { id: number; revision_no: number; source: string; note: string; created_at: string | null; current: boolean; final: boolean; referenced: boolean; deletable: boolean };

function errorText(error: unknown) {
  const detail = error instanceof ApiError ? error.detail as { message?: string } | string | undefined : undefined;
  return (typeof detail === "string" ? detail : detail?.message) || (error instanceof Error ? error.message : "操作失败");
}

// The words of a text or graphic master, enough to tell versions apart without opening the editor.
function plainText(value: unknown, out: string[] = []): string[] {
  if (Array.isArray(value)) value.forEach(item => plainText(item, out));
  else if (value && typeof value === "object") {
    const record = value as Record<string, unknown>;
    if (typeof record.text === "string") out.push(record.text);
    for (const [key, item] of Object.entries(record)) if (key !== "text" && key !== "style") plainText(item, out);
  }
  return out;
}

export function Switch({ checked, disabled, onChange, left, right }: { checked: boolean; disabled?: boolean; onChange: (value: boolean) => void; left: string; right: string }) {
  return <div className="inline-flex items-center gap-3 text-sm">
    <span className={checked ? "text-slate-400" : "font-medium text-slate-900"}>{left}</span>
    <button type="button" role="switch" aria-checked={checked} aria-label={`${left} / ${right}`} disabled={disabled} onClick={() => onChange(!checked)}
      className={`relative h-[31px] w-[51px] shrink-0 rounded-full transition-colors duration-200 disabled:opacity-50 ${checked ? "bg-emerald-500" : "bg-slate-300"}`}>
      <span aria-hidden className={`absolute left-[2px] top-[2px] h-[27px] w-[27px] rounded-full bg-white shadow transition-transform duration-200 ${checked ? "translate-x-[20px]" : ""}`} />
    </button>
    <span className={checked ? "font-medium text-slate-900" : "text-slate-400"}>{right}</span>
  </div>;
}

// Writing skills (scripts, copy) follow this switch; editing and effects skills stay on for the model regardless.
export function PlatformSkillsSwitch({ projectId, unitId, readOnly }: { projectId: number; unitId: number; readOnly: boolean }) {
  const client = useQueryClient();
  const base = `/content-projects/${projectId}/units/${unitId}/platform-skills`;
  const state = useQuery({ queryKey: ["platform-skills", currentUser(), projectId, unitId], retry: false,
    queryFn: () => api.get<{ writing_skills: "on" | "off" }>(base) });
  const [busy, setBusy] = useState(false);
  const [issue, setIssue] = useState("");
  const on = state.data?.writing_skills !== "off";
  return <section aria-label="平台创作 skill" className="rounded-xl border border-slate-200 bg-white p-4 text-sm">
    <div className="flex flex-wrap items-center justify-between gap-3">
      <h3 className="font-semibold">平台创作 skill</h3>
      <Switch checked={on} disabled={readOnly || busy || !state.data} left="不用" right="可以用" onChange={value => {
        setBusy(true); setIssue("");
        api.put(base, { writing_skills: value }).then(() => client.invalidateQueries({ queryKey: ["platform-skills"] }))
          .catch(error => setIssue(errorText(error))).finally(() => setBusy(false));
      }} />
    </div>
    <p className="mt-2 text-xs text-slate-500">{on ? "第三方模型写文案、脚本、镜头规划时可以用平台沉淀的 skill。" : "第三方模型写文案、脚本、做镜头规划时不用平台 skill，靠自己来。"}剪辑和特效 skill（达芬奇、AE）一直可用。</p>
    {issue && <p className="mt-2 text-xs text-rose-700">{issue}</p>}
  </section>;
}

function Versions({ projectId, unitId, readOnly }: { projectId: number; unitId: number; readOnly: boolean }) {
  const client = useQueryClient();
  const base = `/content-projects/${projectId}/units/${unitId}`;
  const list = useQuery({ queryKey: ["article-versions", currentUser(), projectId, unitId], retry: false,
    queryFn: () => api.get<{ items: Version[]; locked: boolean }>(`${base}/article-chain/versions`) });
  const [open, setOpen] = useState<number | null>(null);
  const [preview, setPreview] = useState("");
  const [issue, setIssue] = useState("");
  const [busy, setBusy] = useState(false);
  async function show(id: number) {
    if (open === id) { setOpen(null); return; }
    setOpen(id); setPreview("读取中…");
    try {
      const master = await api.get<{ payload: unknown }>(`${base}/master-revisions/${id}`);
      setPreview(plainText(master.payload).join("\n\n"));
    } catch (cause) { setPreview(errorText(cause)); }
  }
  async function act(run: () => Promise<unknown>) {
    setBusy(true); setIssue("");
    try { await run(); await client.invalidateQueries({ queryKey: ["article-versions"] }); await client.invalidateQueries({ queryKey: ["article-chain"] }); }
    catch (cause) { setIssue(errorText(cause)); }
    finally { setBusy(false); }
  }
  const items = list.data?.items || [];
  const frozen = readOnly || !!list.data?.locked;
  return <section aria-label="版本" className="rounded-xl border border-slate-200 bg-white p-4 text-sm">
    <h3 className="font-semibold">版本 <span className="font-normal text-slate-500">· 共 {items.length} 个</span></h3>
    {issue && <p role="alert" className="mt-2 text-xs text-rose-700">{issue}</p>}
    {list.error && <ErrorBanner message={errorText(list.error)} />}
    <ul className="mt-3 divide-y divide-slate-100">{items.map(item => <li key={item.id} className="py-2">
      <div className="flex flex-wrap items-center gap-2">
        <span className="font-medium tabular-nums">v{item.revision_no}</span>
        <span className={`rounded-pill px-2 py-0.5 text-[11px] ${item.source === "第三方模型" ? "bg-indigo-50 text-indigo-700" : item.source === "平台模型" ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-600"}`}>{item.source}</span>
        {item.final ? <span className="text-[11px] text-emerald-700">已定稿</span> : item.current ? <span className="text-[11px] text-slate-700">当前</span> : null}
        <span className="text-xs text-slate-500">{item.created_at ? new Date(item.created_at).toLocaleString() : ""}{item.note ? ` · ${item.note}` : ""}</span>
        <span className="ml-auto flex gap-1">
          <Button size="sm" variant="secondary" onClick={() => void show(item.id)}>{open === item.id ? "收起" : "查看"}</Button>
          {!item.current && !frozen && <Button size="sm" variant="secondary" disabled={busy} onClick={() => void act(() => api.post(`${base}/article-chain/versions/${item.id}/restore`, {}))}>用这一版</Button>}
          {item.deletable && !frozen && <Button size="sm" variant="danger" disabled={busy} onClick={() => { if (window.confirm(`删除 v${item.revision_no}？删除后不能恢复。`)) void act(() => api.del(`${base}/article-chain/versions/${item.id}`)); }}>删除</Button>}
        </span>
      </div>
      {open === item.id && <pre className="mt-2 max-h-80 overflow-auto whitespace-pre-wrap rounded-lg bg-slate-50 p-3 font-sans text-[13px] leading-relaxed text-slate-700">{preview}</pre>}
    </li>)}</ul>
    {!items.length && !list.isPending && <p className="mt-2 text-xs text-slate-500">还没有版本。</p>}
  </section>;
}

export type ArticlePart = "draft" | "images" | "delivery";

// One writing chain shown across the work's steps: 稿子 (who writes, draft review, versions), 成图 (check the rendered images), 交付 (sending status).
export default function ArticleChainPanel({ projectId, unitId, readOnly, isGraphic = false, part }: { projectId: number; unitId: number; readOnly: boolean; isGraphic?: boolean; part: ArticlePart }) {
  const client = useQueryClient();
  const navigate = useNavigate();
  const base = `/content-projects/${projectId}/units/${unitId}`;
  const chain = useQuery({ queryKey: ["article-chain", currentUser(), projectId, unitId], retry: false,
    queryFn: () => api.get<Chain>(`${base}/article-chain`),
    refetchInterval: query => ["not_started", "draft_changes", "platform"].includes(query.state.data?.state || "") ? 15000 : false });
  const [notes, setNotes] = useState<string[]>([]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [issue, setIssue] = useState("");
  const data = chain.data;
  async function act(run: () => Promise<unknown>) {
    setBusy(true); setIssue("");
    try { await run(); await client.invalidateQueries({ queryKey: ["article-chain"] }); await client.invalidateQueries({ queryKey: ["article-versions"] }); }
    catch (cause) { setIssue(errorText(cause)); }
    finally { setBusy(false); }
  }
  async function copy() {
    setBusy(true); setIssue("");
    try {
      const unit = await api.post<{ id: number }>(`${base}/copy`, {});
      navigate(`/projects/${projectId}/units/${unit.id}/production?workstep=plan`);
    } catch (cause) { setIssue(errorText(cause)); }
    finally { setBusy(false); }
  }
  if (chain.isPending) return null;
  if (chain.error || !data) return <ErrorBanner message={errorText(chain.error)} />;
  const external = data.writer === "external";
  const reviewing = part === "draft" && (data.state === "draft_review" || data.state === "draft_changes");
  const checking = part === "images" && data.state === "final_review";
  const pending = text.trim() ? [...notes, text.trim()] : notes;
  const decisionControls = (reviewing || checking) && !readOnly && <div className="mt-3 space-y-2">
    <div className="flex flex-wrap items-end gap-2">
      <input aria-label="修改意见" className={`${inputClass} min-w-[14rem] flex-1`} maxLength={2000} placeholder={checking ? "成图要改的地方，例如：第2张背景换一张" : "要改的地方，例如：开头再短一点"} value={text} onChange={event => setText(event.target.value)} />
      <Button size="sm" variant="secondary" disabled={!text.trim()} onClick={() => { setNotes(current => [...current, text.trim()]); setText(""); }}>再加一条</Button>
    </div>
    {notes.length > 0 && <ul className="list-disc pl-5 text-xs text-slate-600">{notes.map((note, index) => <li key={index}>{note}</li>)}</ul>}
    <div className="flex flex-wrap gap-2">
      {checking
        ? <Button disabled={busy} onClick={() => { if (window.confirm("成图验收通过并定稿？定稿后不能再改，要调整只能复制一份。")) void act(() => api.post(`${base}/article-chain/decision`, { decision: "accept", notes: [] })); }}>{busy ? "送审中…" : "验收通过"}</Button>
        : <Button disabled={busy} onClick={() => { if (window.confirm(isGraphic ? "采用这版稿子？平台会接着出图，出好后到「成图」一步验收。" : "采用当前版本并定稿？定稿后不能再改，要调整只能复制一份。")) void act(() => api.post(`${base}/article-chain/decision`, { decision: "approve", notes: [] })); }}>{busy ? "出图中…" : isGraphic ? "采用" : "采用并定稿"}</Button>}
      <Button variant="secondary" disabled={busy || !pending.length} onClick={() => void act(async () => { await api.post(`${base}/article-chain/decision`, { decision: "changes", notes: pending.map(note => ({ note })) }); setNotes([]); setText(""); })}>按意见修改</Button>
    </div>
    <p className="text-xs text-slate-500">{external ? "回到第三方模型那边说一声「继续」，它会读到你的决定。" : "写了意见后，在下面的创作流程里重跑，采用的新稿会回到这里。"}</p>
  </div>;
  const status = <div className="rounded-lg bg-indigo-50/60 p-3 text-sm">
    <p><span className="font-semibold">{data.label}</span>{data.detail ? ` · ${data.detail}` : ""}</p>
    {data.notes?.length ? <ul className="mt-1 list-disc pl-5 text-xs text-slate-600">{data.notes.map((item, index) => <li key={index}>{item.note}</li>)}</ul> : null}
  </div>;
  const failure = issue && <p role="alert" className="mt-2 text-xs text-rose-700">{issue}</p>;
  if (part === "images") return <section aria-label="成图" className="mb-5 space-y-3 rounded-xl border border-slate-200 bg-white p-4 text-sm">
    {status}
    {checking && <>
      <p className="text-xs text-slate-600">平台按采用的稿子出好了成图。满意就验收通过（这时才定稿，并送进「审阅与交付」）；不满意写意见退回，出下一版。点图可看大图。</p>
      <div className="grid grid-cols-3 gap-2 sm:grid-cols-6">{(data.renders || []).map((item, index) => <RenderImage key={item.material_revision_id} item={item} index={index} />)}</div>
    </>}
    {data.state === "rendering" && data.review?.state === "failed" && <div className="flex flex-wrap items-center gap-3 text-xs">
      <span className="text-rose-700">出图没成功：{data.review.message || ""}</span>
      {!readOnly && <Button size="sm" disabled={busy} onClick={() => void act(() => api.post(`${base}/article-chain/send-to-review`, {}))}>{busy ? "出图中…" : "重新出图"}</Button>}
    </div>}
    {decisionControls}
    {failure}
  </section>;
  if (part === "delivery") return <section aria-label="送审" className="mb-5 space-y-3 rounded-xl border border-slate-200 bg-white p-4 text-sm">
    {data.review && <div className="flex flex-wrap items-center gap-3 text-xs text-slate-600">
      {data.review.state === "sent"
        ? <><span>已送进「审阅与交付」等你审批。</span><Button size="sm" variant="secondary" onClick={() => navigate("/review")}>去审阅与交付</Button></>
        : <><span className={data.review.state === "failed" ? "text-rose-700" : ""}>{data.review.state === "failed" ? `送审没成功：${data.review.message || ""}` : "还没送审。"}</span>
          {!readOnly && <Button size="sm" disabled={busy} onClick={() => void act(() => api.post(`${base}/article-chain/send-to-review`, {}))}>{busy ? "处理中…" : "重新送审"}</Button>}</>}
    </div>}
    {data.locked && <div className="flex flex-wrap items-center gap-3 text-xs text-slate-600"><span>已定稿，这一条不能再改。要调整就复制一份。</span><Button size="sm" variant="secondary" disabled={busy} onClick={() => void copy()}>复制一份</Button></div>}
    {failure}
  </section>;
  return <div className="mb-5 space-y-4">
    {external && <PlatformSkillsSwitch projectId={projectId} unitId={unitId} readOnly={readOnly || !!data.locked} />}
    <section aria-label="写作方式" className="rounded-xl border border-slate-200 bg-white p-4 text-sm">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h3 className="font-semibold">写作方式</h3>
        <Switch checked={external} disabled={readOnly || busy || !!data.locked} left="平台模型" right="第三方模型"
          onChange={value => void act(() => api.put(`${base}/article-chain/writer`, { writer: value ? "external" : "platform" }))} />
      </div>
      <p className="mt-2 text-xs text-slate-500">{external ? "由接了 MCP 的第三方模型写稿：在那边说「写这篇」，写好的每一版都会出现在下面，你在这里采用或写意见。" : "由平台里配置的模型按下面的创作流程逐步写；采用的稿子会回到这里等你看。"}</p>
      <div className="mt-3">{status}</div>
      {decisionControls}
      {failure}
    </section>
    <Versions projectId={projectId} unitId={unitId} readOnly={readOnly} />
  </div>;
}
