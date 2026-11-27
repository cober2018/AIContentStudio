import { useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, ApiError, currentUser } from "../../api";
import { Button, ErrorBanner, Field, inputClass } from "../../components/ui";
import type { Persona } from "./projectTypes";

// 一份本体、四种形态：本体是全文，长文就是本体本身；图卡、横版、竖版各是一条作品，从本体派生。
export type FormKey = "long_article" | "graphic_cards" | "video_landscape" | "video_portrait";
export const FORMS: { key: FormKey; label: string; hint: string }[] = [
  { key: "long_article", label: "长文", hint: "就是本体本身，定稿后出公众号等平台版本" },
  { key: "graphic_cards", label: "图卡", hint: "3～6 张 3:4，问题、结果表、结论" },
  { key: "video_landscape", label: "横版视频", hint: "16:9，3～5 分钟，讲完整过程" },
  { key: "video_portrait", label: "竖版视频", hint: "9:16，约 1 分钟，只追一个点" },
];
const LABEL = Object.fromEntries(FORMS.map(item => [item.key, item.label])) as Record<FormKey, string>;

type Stale = { from_revision_no: number | null; to_revision_no: number; changed_sections: string[] };
type Work = { unit_id: number; title: string; form: FormKey; state: string | null; label: string | null; started: boolean; body_revision_no: number | null; stale: Stale | null; redone_by?: number | null };
export type FormsView = {
  planned: boolean; forms: FormKey[]; body_source?: "new" | "published_article"; writer?: string; persona_id?: number; started?: boolean;
  import?: { title: string; url: string | null; images: { alt: string; src: string }[] } | null;
  long_article?: { state: "ready" | "failed"; variant_id?: number; reason?: string } | null;
  body?: { unit_id: number; title: string; state: string | null; label: string | null; final_master_id: number | null; final_revision_no: number | null; review_url: string } | null;
  works?: Work[];
};
export type PlanValue = { persona_id: number | null; forms: FormKey[]; body_source: "new" | "published_article"; writer: "external" | "platform";
  article: { title: string; url: string; text: string } };

function errorText(error: unknown) {
  const detail = error instanceof ApiError ? error.detail as { message?: string } | string | undefined : undefined;
  return (typeof detail === "string" ? detail : detail?.message) || (error instanceof Error ? error.message : "操作失败");
}

export function useForms(projectId: number) {
  return useQuery({ queryKey: ["topic-forms", currentUser(), projectId], retry: false, queryFn: () => api.get<FormsView>(`/content-projects/${projectId}/forms`) });
}

export function FormTicks({ value, onChange, disabled, locked = [] }: { value: FormKey[]; onChange: (next: FormKey[]) => void; disabled?: boolean; locked?: FormKey[] }) {
  return <fieldset className="grid gap-2 sm:grid-cols-2" aria-label="要做哪几种">
    {FORMS.map(item => {
      const checked = value.includes(item.key);
      const fixed = locked.includes(item.key);
      return <label key={item.key} className={`flex cursor-pointer items-start gap-2 rounded-lg border p-3 text-sm ${checked ? "border-indigo-300 bg-indigo-50/60" : "border-slate-200 bg-white"} ${disabled || fixed ? "cursor-not-allowed opacity-70" : ""}`}>
        <input type="checkbox" className="mt-0.5" checked={checked} disabled={disabled || fixed}
          onChange={event => onChange(event.target.checked ? [...value, item.key] : value.filter(key => key !== item.key))} />
        <span><span className="font-medium">{item.label}</span><span className="block text-xs text-slate-500">{fixed ? "已经开始做了，不能取消" : item.hint}</span></span>
      </label>;
    })}
  </fieldset>;
}

export function emptyPlan(personaId: number | null = null): PlanValue {
  return { persona_id: personaId, forms: ["long_article"], body_source: "new", writer: "external", article: { title: "", url: "", text: "" } };
}

export function planPayload(plan: PlanValue) {
  return { persona_id: plan.persona_id, forms: plan.forms, body_source: plan.body_source, writer: plan.writer,
    ...(plan.body_source === "published_article" ? { article: { title: plan.article.title.trim(), url: plan.article.url.trim() || null, text: plan.article.text } } : {}) };
}

export function planIssue(plan: PlanValue): string {
  if (!plan.persona_id) return "先选一个角色";
  if (!plan.forms.length) return "至少勾一种";
  if (plan.body_source === "published_article" && !plan.article.text.trim()) return "把已发表文章的正文贴进来";
  if (plan.article.url.trim() && !/^https?:\/\//.test(plan.article.url.trim())) return "发表链接要以 http 开头";
  return "";
}

// 「要做哪几种」：角色、四个勾选框（按角色默认预勾）、本体来源和写作方。
export function FormPlanFields({ value, onChange, personas, disabled }: { value: PlanValue; onChange: (next: PlanValue) => void; personas: Persona[]; disabled?: boolean }) {
  const defaults = useQuery({ queryKey: ["persona-default-forms", currentUser(), value.persona_id], enabled: !!value.persona_id, retry: false,
    queryFn: () => api.get<{ forms: FormKey[] }>(`/content-personas/${value.persona_id}/default-forms`) });
  const [touched, setTouched] = useState(false);
  useEffect(() => {
    if (defaults.data && !touched) onChange({ ...value, forms: defaults.data.forms });
    // Pre-tick once per persona; after the user changes a box their ticks win.
  }, [defaults.data, value.persona_id]); // eslint-disable-line react-hooks/exhaustive-deps
  return <div className="space-y-4">
    <Field label="角色"><select className={inputClass} disabled={disabled} value={value.persona_id ?? ""} onChange={event => { setTouched(false); onChange({ ...value, persona_id: Number(event.target.value) || null }); }}>
      <option value="">请选择</option>{personas.filter(item => item.status !== "archived").map(item => <option key={item.id} value={item.id}>{item.name}</option>)}
    </select></Field>
    <div><p className="mb-1.5 text-[12.5px] font-medium">要做哪几种</p>
      <FormTicks value={value.forms} disabled={disabled} onChange={forms => { setTouched(true); onChange({ ...value, forms }); }} />
      <p className="mt-1.5 text-xs text-slate-500">按角色默认勾好了，可以改。新写的本体在「本体待你看」时还能再改一次，比如读完全文再决定要不要竖版。</p></div>
    <Field label="本体从哪来"><div className="flex flex-wrap gap-4 text-sm">
      <label className="flex items-center gap-2"><input type="radio" disabled={disabled} checked={value.body_source === "new"} onChange={() => onChange({ ...value, body_source: "new" })} />新写（写好后停一次给你定稿）</label>
      <label className="flex items-center gap-2"><input type="radio" disabled={disabled} checked={value.body_source === "published_article"} onChange={() => onChange({ ...value, body_source: "published_article" })} />用已发表的文章（直接算定稿）</label>
    </div></Field>
    {value.body_source === "new" ? <Field label="谁写本体"><div className="flex flex-wrap gap-4 text-sm">
      <label className="flex items-center gap-2"><input type="radio" disabled={disabled} checked={value.writer === "external"} onChange={() => onChange({ ...value, writer: "external" })} />第三方模型</label>
      <label className="flex items-center gap-2"><input type="radio" disabled={disabled} checked={value.writer === "platform"} onChange={() => onChange({ ...value, writer: "platform" })} />平台模型（只写文字）</label>
    </div></Field> : <div className="space-y-3 rounded-lg border border-slate-200 p-3">
      <Field label="文章标题"><input className={inputClass} disabled={disabled} maxLength={500} value={value.article.title} onChange={event => onChange({ ...value, article: { ...value.article, title: event.target.value } })} /></Field>
      <Field label="发表链接（可选）"><input className={inputClass} disabled={disabled} maxLength={2000} placeholder="https://mp.weixin.qq.com/s/…" value={value.article.url} onChange={event => onChange({ ...value, article: { ...value.article, url: event.target.value } })} /></Field>
      <Field label="正文" hint="Markdown 或纯文本都行；图片链接会登记成原图出处"><textarea rows={8} className={inputClass} disabled={disabled} value={value.article.text} onChange={event => onChange({ ...value, article: { ...value.article, text: event.target.value } })} /></Field>
    </div>}
  </div>;
}

// 空项目页：一步定好本体和形态。
export function FormPlanSetup({ projectId, personas, onDone }: { projectId: number; personas: Persona[]; onDone: () => void }) {
  const [plan, setPlan] = useState<PlanValue>(() => emptyPlan(personas[0]?.id ?? null));
  const [busy, setBusy] = useState(false);
  const [issue, setIssue] = useState("");
  async function submit(event: FormEvent) {
    event.preventDefault();
    const problem = planIssue(plan);
    if (problem) { setIssue(problem); return; }
    setBusy(true); setIssue("");
    try { await api.post(`/content-projects/${projectId}/forms`, planPayload(plan)); onDone(); }
    catch (cause) { setIssue(errorText(cause)); }
    finally { setBusy(false); }
  }
  return <form onSubmit={submit} className="space-y-4">
    <FormPlanFields value={plan} onChange={setPlan} personas={personas} disabled={busy} />
    {issue && <p role="alert" className="text-sm text-rose-700">{issue}</p>}
    <Button type="submit" disabled={busy}>{busy ? "建立中…" : "建本体和这几种作品"}</Button>
  </form>;
}

function stateText(work: Work, started: boolean) {
  if (!started) return "等本体定稿";
  return work.label || "等第三方模型";
}

// 项目页的本体卡片：本体状态、勾选（定稿前随便改，定稿后补勾 / 取消未开始的）、各形态用的本体版本和「本体已更新」。
export function BodyCard({ projectId, readOnly }: { projectId: number; readOnly: boolean }) {
  const client = useQueryClient();
  const view = useForms(projectId);
  const [busy, setBusy] = useState(false);
  const [issue, setIssue] = useState("");
  const data = view.data;
  if (view.isPending || !data?.planned) return null;
  if (view.error) return <ErrorBanner message={errorText(view.error)} />;
  const works = data.works || [];
  const locked = FORMS.map(item => item.key).filter(key => works.some(work => work.form === key && work.started));
  async function act(run: () => Promise<unknown>) {
    setBusy(true); setIssue("");
    try { await run(); await client.invalidateQueries({ queryKey: ["topic-forms"] }); await client.invalidateQueries({ queryKey: ["project"] }); }
    catch (cause) { setIssue(errorText(cause)); }
    finally { setBusy(false); }
  }
  const body = data.body;
  return <section aria-label="本体与形态" className="mb-5 space-y-4 rounded-xl border border-indigo-200 bg-white p-5 text-sm">
    <div className="flex flex-wrap items-start justify-between gap-3">
      <div>
        <p className="eyebrow">本体（全文）</p>
        <h2 className="mt-1 text-lg font-semibold">{body?.title}</h2>
        <p className="mt-1 text-slate-600">
          {data.body_source === "published_article" ? "已发表文章导入 · " : ""}
          {body?.final_revision_no ? `已定稿第 ${body.final_revision_no} 版` : "还没定稿"}
          {body?.label && !(body.state === "done") ? ` · ${body.label}` : ""}
        </p>
        {data.import?.url && <p className="mt-1 text-xs"><a className="text-indigo-700 underline" href={data.import.url} target="_blank" rel="noreferrer">原文发表链接</a>{data.import.images?.length ? ` · 原图 ${data.import.images.length} 张已登记出处` : ""}</p>}
      </div>
      {body && <Link className="rounded-md bg-indigo-600 px-4 py-2 text-sm text-white" to={body.review_url}>{body.state === "draft_review" ? "本体待你看" : "打开本体"}</Link>}
    </div>
    <div>
      <p className="mb-1.5 font-medium">要做哪几种</p>
      <FormTicks value={data.forms} locked={locked} disabled={readOnly || busy} onChange={forms => { if (forms.length) void act(() => api.put(`/content-projects/${projectId}/forms`, { forms })); else setIssue("至少留一种"); }} />
      <p className="mt-1.5 text-xs text-slate-500">{data.started ? "本体已定稿：补勾的形态从当前定稿本体派生、马上开工；已开始的不能取消。" : "本体定稿时以这里的勾选为准开工；在那之前随便改。"}</p>
    </div>
    {data.forms.includes("long_article") && data.started && <p className="text-xs text-slate-600">长文：{data.long_article?.state === "ready" ? "公众号版本已出，在本体作品的渠道变体里看。" : data.long_article?.state === "failed" ? `公众号版本没出成（${data.long_article.reason}），可在本体作品的渠道变体里手动出。` : "出平台版本中…"}</p>}
    {works.length > 0 && <ul className="divide-y divide-slate-100 rounded-lg border border-slate-200">{works.map(work => <li key={work.unit_id} className="flex flex-wrap items-center gap-2 p-3">
      <span className="rounded-pill bg-slate-100 px-2 py-0.5 text-xs">{LABEL[work.form]}</span>
      <Link className="font-medium text-indigo-700 underline" to={`/projects/${projectId}/units/${work.unit_id}/production?workstep=plan`}>{work.title}</Link>
      <span className="text-xs text-slate-500">{stateText(work, !!data.started)}</span>
      {work.body_revision_no && body && <Link className="text-xs text-indigo-700 underline" to={`${body.review_url}#versions`} title="打开本体，在「版本」里看这一版">用本体第 {work.body_revision_no} 版</Link>}
      {work.stale && <span className="ml-auto flex flex-wrap items-center gap-2 text-xs text-amber-800">
        <span className="rounded-pill bg-amber-50 px-2 py-0.5">本体已更新到第 {work.stale.to_revision_no} 版 · 改了：{work.stale.changed_sections.join("、") || "措辞"}</span>
        {work.redone_by ? <Link className="underline" to={`/projects/${projectId}/units/${work.redone_by}/production?workstep=plan`}>已按新本体重做 →</Link>
          : !readOnly && <Button size="sm" variant="secondary" disabled={busy} onClick={() => { if (window.confirm(`按本体第 ${work.stale!.to_revision_no} 版新开一条${LABEL[work.form]}？这一条保留不动。`)) void act(() => api.post(`/content-projects/${projectId}/units/${work.unit_id}/form-redo`, {})); }}>按新本体重做</Button>}
      </span>}
    </li>)}</ul>}
    {issue && <p role="alert" className="text-xs text-rose-700">{issue}</p>}
  </section>;
}

// 本体作品页上：定稿前在全文旁边改勾选；定稿后可以写意见重开本体。
export function BodyReviewForms({ projectId, unitId, readOnly, state }: { projectId: number; unitId: number; readOnly: boolean; state: string }) {
  const client = useQueryClient();
  const view = useForms(projectId);
  const [busy, setBusy] = useState(false);
  const [issue, setIssue] = useState("");
  const [note, setNote] = useState("");
  const data = view.data;
  if (!data?.planned || data.body?.unit_id !== unitId) return null;
  const locked = FORMS.map(item => item.key).filter(key => (data.works || []).some(work => work.form === key && work.started));
  async function act(run: () => Promise<unknown>) {
    setBusy(true); setIssue("");
    try { await run(); await client.invalidateQueries({ queryKey: ["topic-forms"] }); await client.invalidateQueries({ queryKey: ["article-chain"] }); }
    catch (cause) { setIssue(errorText(cause)); }
    finally { setBusy(false); }
  }
  return <section aria-label="本体的形态" className="rounded-xl border border-indigo-200 bg-indigo-50/40 p-4 text-sm">
    <h3 className="font-semibold">这是本体（全文）</h3>
    <p className="mt-1 text-xs text-slate-600">{data.started ? `已定稿第 ${data.body?.final_revision_no} 版，勾选的形态已开工。` : "读完全文再定要做哪几种，点「采用并定稿」时以这里的勾选为准开工。"}</p>
    <div className="mt-3"><FormTicks value={data.forms} locked={locked} disabled={readOnly || busy}
      onChange={forms => { if (forms.length) void act(() => api.put(`/content-projects/${projectId}/forms`, { forms })); else setIssue("至少留一种"); }} /></div>
    {state === "done" && !readOnly && <div className="mt-3 flex flex-wrap items-end gap-2">
      <input aria-label="改本体的意见" className={`${inputClass} min-w-[14rem] flex-1`} maxLength={2000} placeholder="要改本体的地方，例如：结果表加上 2026 年" value={note} onChange={event => setNote(event.target.value)} />
      <Button size="sm" variant="secondary" disabled={busy || !note.trim()} onClick={() => void act(async () => { await api.post(`/content-projects/${projectId}/units/${unitId}/article-chain/decision`, { decision: "changes", notes: [{ note: note.trim() }] }); setNote(""); })}>改本体</Button>
      <p className="w-full text-xs text-slate-500">改完再定稿后，已派生的作品只会提示「本体已更新」，要不要重做由你在项目页决定。</p>
    </div>}
    {issue && <p role="alert" className="mt-2 text-xs text-rose-700">{issue}</p>}
  </section>;
}

// 角色设置里的默认勾选：定选题时预先勾好，每个项目都还能改。
export function PersonaDefaultForms({ personaId, disabled }: { personaId: number; disabled?: boolean }) {
  const client = useQueryClient();
  const defaults = useQuery({ queryKey: ["persona-default-forms", currentUser(), personaId], retry: false,
    queryFn: () => api.get<{ forms: FormKey[] }>(`/content-personas/${personaId}/default-forms`) });
  const [issue, setIssue] = useState("");
  const [busy, setBusy] = useState(false);
  if (!defaults.data) return null;
  return <div className="space-y-2">
    <FormTicks value={defaults.data.forms} disabled={disabled || busy} onChange={forms => {
      if (!forms.length) { setIssue("至少留一种"); return; }
      setBusy(true); setIssue("");
      api.put(`/content-personas/${personaId}/default-forms`, { forms }).then(() => client.invalidateQueries({ queryKey: ["persona-default-forms"] }))
        .catch(cause => setIssue(errorText(cause))).finally(() => setBusy(false));
    }} />
    {issue && <p role="alert" className="text-xs text-rose-700">{issue}</p>}
  </div>;
}
