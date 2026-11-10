import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { api, ApiError, currentUser } from "../api";
import { Button, Chip, EmptyState, ErrorBanner, Field, inputClass, Notice, Page, PageHeader, Section, Spinner, Tabs, RatioSuffix, WorkCode } from "../components/ui";

type Category = { id: number; top_key: string; top_name: string; name: string; status: "active" | "disabled" };
type Top = { key: string; name: string; categories: Category[] };
type Fact = { text: string; source: string; url?: string; excerpt?: string; status?: "sourced" | "needs_source" | "needs_manual"; checked_by_person?: boolean };
type Revision = {
  revision_id: number; revision_no: number; status: "draft" | "confirmed"; origin: "human" | "ai"; name: string; category_id: number | null;
  proposed_category: { top_key: string; name: string } | null; category_top: string; category_name: string; audiences: string[]; brand: string; url: string;
  description: string; facts: Fact[]; brand_statement: string; banned_words: string[];
};
type SubjectRow = { id: number; status: string; name: string; category_name: string; draft: Revision | null; confirmed: Revision | null; needs_confirmation: boolean };
type Question = { id: string; text: string; intent: string; priority: number; source_url: string; source_kind: "search" | "inferred"; coverage: "none" | "in_progress" | "done" };
type Library = { revision_no: number; origin: string; keywords: { primary: string[]; long_tail: string[]; brand: string[] }; questions: Question[] };
type ProjectRow = { id: number; title: string; question: string; settings: { forms: string[]; tone: string; reader_level: string; genre: string; writer: string; platforms?: string[]; cover?: { material_revision_id: number }; cover_error?: string }; state: string; pending_review: number; href: string };
type Subject = SubjectRow & { library: Library | null; projects: ProjectRow[]; hints: { common_questions: string[]; writing_focus: string[] }; genres: { key: string; name: string; for: string }[] };
type Version = { variant_id: number; channel: string; content_form: string; revision_no: number; title: string | null; candidate: { id: number; status: string } | null; review: { decision: string; comment: string | null } | null };
type ProjectUnit = { unit_id: number; title: string; aspect_ratio?: string | null; role: "core" | "derived"; modality: string; state: string; label: string; writer: string; versions: Version[]; href: string };
type SearchProject = ProjectRow & { subject: { id: number; name: string; revision_no: number }; genre_name: string; units: ProjectUnit[] };
type ReviewItem = { candidate_id: number; candidate_hash: string; channel: string; content_form: string; title: string; body: string | null };
type ReviewGroup = { project_id: number; title: string; question: string; items: ReviewItem[] };
type RunStep = { step: string; status: "done" | "failed" | "retry" | "skipped"; detail: string; model: string | null; project_id: number | null; at: string };
type Run = { id: number; kind: string; kind_name: string; status: "queued" | "running" | "done" | "failed" | "interrupted"; subject_id: number | null; project_id: number | null; steps: RunStep[]; error: string | null; created_at: string };
type Delivered = { delivery_target_id: number; project_title: string; channel: string; title: string; body: string | null; package_url: string };

const BASE = "/search-promotion";
const AUDIENCES = [["individual", "个人"], ["business", "企业"], ["government", "政府"]] as const;
const FORMS = [["text", "文章"], ["graphic", "图文"], ["video", "视频"]] as const;
const FORM_NAMES: Record<string, string> = Object.fromEntries(FORMS);
const PLATFORMS = [["wechat", "公众号"], ["zhihu", "知乎"], ["toutiao", "今日头条"], ["baijia", "百家号"], ["penguin", "企鹅号"], ["netease", "网易号"], ["bilibili", "B站专栏"]] as const;
const RUN_STATUS = { queued: ["排队中", "neutral"], running: ["进行中", "info"], done: ["完成", "good"], failed: ["有失败", "bad"], interrupted: ["中断", "warn"] } as const;
const STEP_STATUS = { done: ["完成", "good"], failed: ["失败", "bad"], retry: ["重写中", "warn"], skipped: ["跳过", "neutral"] } as const;
const COVERAGE = { none: ["没做", "neutral"], in_progress: ["在做", "warn"], done: ["已有成稿", "good"] } as const;
const FACT_STATUS = { sourced: ["有出处", "good"], needs_source: ["待补出处", "warn"], needs_manual: ["需人工核对", "bad"] } as const;

function message(error: unknown): string {
  if (error instanceof ApiError) {
    const detail = error.detail as { message?: string } | { msg?: string }[] | undefined;
    if (Array.isArray(detail)) return detail.map(item => item.msg).filter(Boolean).join("；") || "填写的内容格式不对";
    return detail?.message || error.message;
  }
  return error instanceof Error ? error.message : "操作失败";
}

const words = (value: string) => value.split(/[\n,，、]/).map(item => item.trim()).filter(Boolean);

export default function SearchPromotionWorkbench() {
  const { projectId, subjectId } = useParams();
  if (projectId) return <ProjectPage projectId={Number(projectId)} />;
  if (subjectId) return <SubjectPage subjectId={subjectId === "new" ? null : Number(subjectId)} />;
  return <Home />;
}

function Home() {
  const [params, setParams] = useSearchParams();
  const tab = (params.get("tab") || "todo") as "todo" | "review" | "subjects" | "delivered" | "categories";
  return <Page>
    <PageHeader eyebrow="创作" title="搜索推广工作台" lead="让用户在搜索和问 AI 时看到并引用你的内容。你只把两道关：开头确认基础资料，最后审成稿；问题库、写作、各平台改写都由 AI 完成。" />
    <Tabs label="搜索推广" value={tab} onChange={next => setParams(next === "todo" ? {} : { tab: next })}
      items={[["todo", "待确认资料"], ["review", "待审成稿"], ["subjects", "推广对象"], ["delivered", "已交付"], ["categories", "分类"]] as const} />
    <div className="mt-6">{tab === "todo" ? <Todo /> : tab === "review" ? <ReviewQueue /> : tab === "subjects" ? <Subjects /> : tab === "delivered" ? <DeliveredList /> : <Categories />}</div>
  </Page>;
}

function useSubjects(includeArchived = false) {
  return useQuery({ queryKey: ["search-subjects", currentUser(), includeArchived], queryFn: () => api.get<SubjectRow[]>(`${BASE}/subjects?include_archived=${includeArchived}`) });
}

function Todo() {
  const subjects = useSubjects();
  const waiting = (subjects.data || []).filter(row => row.needs_confirmation);
  return <div className="space-y-6">
    <Notice>开始方式：新建推广对象自己填资料；或只给名称和资料链接，对第三方模型说「起草 XX 的推广对象资料」。资料确认后，对它说「做 XX 的搜索推广」，它会生成问题库、开项目、写稿、出各平台版本，最后整批送到「待审成稿」。</Notice>
    <Section title="待确认的资料" aside={<Link to={`${BASE}/subjects/new`}><Button>新建推广对象</Button></Link>}>
      {subjects.isPending && <Spinner />}
      {subjects.isError && <ErrorBanner message={message(subjects.error)} />}
      {subjects.data && !waiting.length && <EmptyState title="没有等你确认的资料" />}
      <div className="space-y-2">{waiting.map(row => <Link key={row.id} to={`${BASE}/subjects/${row.id}`} className="flex flex-wrap items-center justify-between gap-3 rounded-xl border bg-white p-4 hover:border-ink-400">
        <div><p className="font-medium text-ink-900">{row.name}</p><p className="text-sm text-ink-500">第 {row.draft?.revision_no} 版草稿 · {row.draft?.origin === "ai" ? "AI 起草" : "人工录入"}</p></div>
        {row.draft?.facts.some(f => f.status === "needs_manual") && <Chip tone="bad">有事实需人工核对</Chip>}
      </Link>)}</div>
    </Section>
  </div>;
}

function Subjects() {
  const [archived, setArchived] = useState(false);
  const subjects = useSubjects(archived);
  return <Section title="推广对象" aside={<div className="flex items-center gap-3">
    <label className="flex items-center gap-1 text-sm text-ink-600"><input type="checkbox" checked={archived} onChange={event => setArchived(event.target.checked)} />显示已归档</label>
    <Link to={`${BASE}/subjects/new`}><Button>新建推广对象</Button></Link>
  </div>}>
    {subjects.isPending && <Spinner />}
    {subjects.isError && <ErrorBanner message={message(subjects.error)} />}
    {subjects.data && !subjects.data.length && <EmptyState title="还没有推广对象" hint="APP、数据接口、网站、服务、设备、原材料、品牌或公司都可以。" />}
    <div className="space-y-2">{subjects.data?.map(row => <Link key={row.id} to={`${BASE}/subjects/${row.id}`} className="flex flex-wrap items-center justify-between gap-3 rounded-xl border bg-white p-4 hover:border-ink-400">
      <div><p className="font-medium text-ink-900">{row.name}</p><p className="text-sm text-ink-500">{row.category_name}{row.confirmed ? ` · 已确认第 ${row.confirmed.revision_no} 版` : " · 资料未确认"}</p></div>
      <div className="flex gap-2">{row.needs_confirmation && <Chip tone="warn">有草稿待确认</Chip>}{row.status === "archived" && <Chip>已归档</Chip>}</div>
    </Link>)}</div>
  </Section>;
}

function useCategories() {
  return useQuery({ queryKey: ["search-categories", currentUser()], queryFn: () => api.get<{ tops: Top[] }>(`${BASE}/categories`) });
}

type Form = { name: string; category_id: number | null; proposed_category: { top_key: string; name: string } | null; audiences: string[]; brand: string; url: string; description: string; facts: Fact[]; brand_statement: string; banned_words: string };

function toForm(revision: Revision | null | undefined): Form {
  return revision ? { name: revision.name, category_id: revision.category_id, proposed_category: revision.proposed_category, audiences: revision.audiences, brand: revision.brand,
    url: revision.url, description: revision.description, facts: revision.facts.map(f => ({ ...f })), brand_statement: revision.brand_statement, banned_words: revision.banned_words.join("、") }
    : { name: "", category_id: null, proposed_category: null, audiences: [], brand: "", url: "", description: "", facts: [], brand_statement: "", banned_words: "" };
}

function SubjectPage({ subjectId }: { subjectId: number | null }) {
  const client = useQueryClient();
  const navigate = useNavigate();
  const subject = useQuery({ queryKey: ["search-subject", currentUser(), subjectId], enabled: subjectId !== null, queryFn: () => api.get<Subject>(`${BASE}/subjects/${subjectId}`) });
  const [editing, setEditing] = useState(subjectId === null);
  const refresh = () => { client.invalidateQueries({ queryKey: ["search-subject"] }); client.invalidateQueries({ queryKey: ["search-subjects"] }); };
  const confirm = useMutation({ mutationFn: () => api.post(`${BASE}/subjects/${subjectId}/confirm`, { revision_no: subject.data!.draft!.revision_no }), onSuccess: refresh });
  const status = useMutation({ mutationFn: (next: string) => api.post(`${BASE}/subjects/${subjectId}/status`, { status: next }), onSuccess: refresh });
  if (subjectId !== null && subject.isPending) return <Page><Spinner /></Page>;
  if (subject.isError) return <Page><ErrorBanner message={message(subject.error)} /></Page>;
  const data = subject.data;
  const shown = data?.draft || data?.confirmed;
  return <Page>
    <Link to={BASE} className="text-sm text-ink-500">← 搜索推广工作台</Link>
    <PageHeader title={subjectId === null ? "新建推广对象" : data!.name} lead={subjectId === null ? "自己录入基础资料，保存后确认即可使用；也可以只给名称和链接，让第三方模型起草。" : data!.confirmed ? `已确认第 ${data!.confirmed.revision_no} 版。改资料会生成新草稿，确认后新开的项目才用它。` : "资料还没确认；确认后才能做问题库和开项目。"} />
    {subjectId === null && <AiDraft />}
    {editing ? <SubjectEditor subjectId={subjectId} base={data?.draft || data?.confirmed || null} head={shown?.revision_no ?? 0}
      onDone={id => { setEditing(false); refresh(); if (subjectId === null) navigate(`${BASE}/subjects/${id}`, { replace: true }); }} onCancel={subjectId === null ? undefined : () => setEditing(false)} /> : <>
      {data!.draft && <Section title={`第 ${data!.draft.revision_no} 版草稿 · ${data!.draft.origin === "ai" ? "AI 起草" : "人工录入"} · 待你确认`} eyebrow="第 1 关">
        <SubjectView revision={data!.draft} />
        {confirm.isError && <div className="mt-3"><ErrorBanner message={message(confirm.error)} /></div>}
        <div className="mt-4 flex flex-wrap gap-3">
          <Button disabled={confirm.isPending || !data!.draft.name || (!data!.draft.category_id && !data!.draft.proposed_category)} onClick={() => confirm.mutate()}>确认资料</Button>
          <Button variant="secondary" onClick={() => setEditing(true)}>修改</Button>
        </div>
        {data!.draft.facts.some(f => f.status === "needs_manual") && <p className="mt-2 text-sm text-ink-500">标「需人工核对」的事实：链接平台打不开，请你自己核对。不对的先「修改」删掉；确认资料就表示你核对过了。</p>}
      </Section>}
      {!data!.draft && data!.confirmed && <Section title={`已确认 · 第 ${data!.confirmed.revision_no} 版`} aside={<Button variant="secondary" onClick={() => setEditing(true)}>修改</Button>}><SubjectView revision={data!.confirmed} /></Section>}
      {data!.confirmed && <StartPanel subjectId={data!.id} />}
      <Runs query={`subject_id=${data!.id}`} />
      {data!.confirmed && <LibrarySection subject={data!} />}
      {data!.projects.length > 0 && <Section title="推广项目">
        <div className="space-y-2">{data!.projects.map(row => <ProjectLink key={row.id} row={row} />)}</div>
      </Section>}
      {status.isError && <ErrorBanner message={message(status.error)} />}
      <Button variant="ghost" disabled={status.isPending} onClick={() => status.mutate(data!.status === "archived" ? "active" : "archived")}>{data!.status === "archived" ? "恢复使用" : "归档推广对象"}</Button>
    </>}
  </Page>;
}

function SubjectView({ revision }: { revision: Revision }) {
  const audience = Object.fromEntries(AUDIENCES) as Record<string, string>;
  return <div className="space-y-3 text-[14px] text-ink-800">
    <p><span className="text-ink-500">分类：</span>{revision.category_name}{revision.proposed_category && <Chip tone="warn">AI 提议的新小类，确认时一并新增</Chip>}</p>
    <p><span className="text-ink-500">面向：</span>{revision.audiences.map(a => audience[a]).join("、") || "未填"} · <span className="text-ink-500">品牌/公司：</span>{revision.brand || "未填"} · <span className="text-ink-500">链接：</span>{revision.url ? <a className="underline" href={revision.url} target="_blank" rel="noreferrer">{revision.url}</a> : "未填"}</p>
    <p><span className="text-ink-500">统一品牌说法：</span>{revision.brand_statement || "未填"}</p>
    <p><span className="text-ink-500">禁用词：</span>{revision.banned_words.join("、") || "无"}</p>
    {revision.description && <p className="whitespace-pre-wrap rounded-lg bg-ink-50 p-3">{revision.description}</p>}
    <div><p className="text-ink-500">核心事实（写作只能引用「有出处」的）</p>
      <ul className="mt-1 space-y-1">{revision.facts.map((fact, index) => {
        const [label, tone] = FACT_STATUS[fact.status || "needs_source"];
        return <li key={index} className="flex flex-wrap items-center gap-2"><Chip tone={tone}>{fact.checked_by_person ? "人工核对过" : label}</Chip><span>{fact.text}</span>
          <span className="text-ink-500">— {fact.url ? <a className="underline" href={fact.url} target="_blank" rel="noreferrer">{fact.source || fact.url}</a> : fact.source || "无出处"}</span></li>;
      })}{!revision.facts.length && <li className="text-ink-500">还没有事实</li>}</ul>
    </div>
  </div>;
}

function SubjectEditor({ subjectId, base, head, onDone, onCancel }: { subjectId: number | null; base: Revision | null; head: number; onDone: (id: number) => void; onCancel?: () => void }) {
  const categories = useCategories();
  const [form, setForm] = useState<Form>(() => toForm(base));
  const update = (patch: Partial<Form>) => setForm({ ...form, ...patch });
  const save = useMutation({
    mutationFn: () => {
      const body = { name: form.name, category_id: form.category_id, proposed_category: form.category_id ? null : form.proposed_category, audiences: form.audiences, brand: form.brand,
        url: form.url, description: form.description, brand_statement: form.brand_statement, banned_words: words(form.banned_words),
        facts: form.facts.filter(f => f.text.trim()).map(f => ({ text: f.text, source: f.source, url: f.url || "", excerpt: f.excerpt || "", status: f.status === "needs_manual" ? "needs_manual" : "" })) };
      return subjectId === null ? api.post<SubjectRow>(`${BASE}/subjects`, body) : api.put<SubjectRow>(`${BASE}/subjects/${subjectId}`, { ...body, expected_revision: head });
    },
    onSuccess: saved => onDone(saved.id),
  });
  if (categories.isPending) return <Spinner />;
  return <Section title={subjectId === null ? "基础资料" : "修改资料（保存为新草稿）"}>
    <div className="space-y-5">
      <Field label="名称"><input className={inputClass} value={form.name} onChange={event => update({ name: event.target.value })} /></Field>
      <Field label="分类" hint={form.proposed_category && !form.category_id ? `AI 提议新小类：${form.proposed_category.name}，确认资料时新增；也可以改选已有小类` : "大类固定，小类可以在「分类」页增加、改名、停用"}>
        <select aria-label="分类" className={inputClass} value={form.category_id || ""} onChange={event => update({ category_id: Number(event.target.value) || null })}>
          <option value="">{form.proposed_category ? `（AI 提议）${form.proposed_category.name}` : "选择分类"}</option>
          {categories.data?.tops.map(top => <optgroup key={top.key} label={top.name}>{top.categories.filter(item => item.status === "active").map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</optgroup>)}
        </select>
      </Field>
      <Field label="面向谁"><div className="flex gap-4">{AUDIENCES.map(([key, label]) => <label key={key} className="flex items-center gap-1 text-sm">
        <input type="checkbox" checked={form.audiences.includes(key)} onChange={event => update({ audiences: event.target.checked ? [...form.audiences, key] : form.audiences.filter(item => item !== key) })} />{label}</label>)}</div></Field>
      <Field label="所属品牌或公司"><input className={inputClass} value={form.brand} onChange={event => update({ brand: event.target.value })} /></Field>
      <Field label="官网或链接"><input className={inputClass} value={form.url} placeholder="https://" onChange={event => update({ url: event.target.value })} /></Field>
      <Field label="描述" hint="怎么写都行：是什么、解决什么问题、给谁用、和同类有什么不同"><textarea className={`${inputClass} min-h-[180px]`} value={form.description} onChange={event => update({ description: event.target.value })} /></Field>
      <Field label="统一品牌说法" hint="所有项目、所有平台都用这一种说法"><input className={inputClass} value={form.brand_statement} onChange={event => update({ brand_statement: event.target.value })} /></Field>
      <Field label="禁用词" hint="用顿号隔开；留空就用默认的绝对化用词清单"><input className={inputClass} value={form.banned_words} onChange={event => update({ banned_words: event.target.value })} /></Field>
      <Field label="核心事实" hint="一条一句话，写清出处；没写出处的标为「待补出处」，写作不能引用">
        <div className="space-y-2">
          {form.facts.map((fact, index) => <div key={index} className="flex flex-wrap items-center gap-2">
            <input aria-label={`事实 ${index + 1}`} className={`${inputClass} min-w-[260px] flex-1`} value={fact.text} placeholder="如：脱硝效率 95%" onChange={event => update({ facts: form.facts.map((item, i) => i === index ? { ...item, text: event.target.value } : item) })} />
            <input aria-label={`出处 ${index + 1}`} className={`${inputClass} w-56`} value={fact.source} placeholder="出处，如：第三方检测报告 2025" onChange={event => update({ facts: form.facts.map((item, i) => i === index ? { ...item, source: event.target.value } : item) })} />
            {fact.status === "needs_manual" && <Chip tone="bad">需人工核对</Chip>}
            <Button variant="ghost" size="sm" onClick={() => update({ facts: form.facts.filter((_, i) => i !== index) })}>删除</Button>
          </div>)}
          <Button variant="secondary" size="sm" onClick={() => update({ facts: [...form.facts, { text: "", source: "" }] })}>加一条事实</Button>
        </div>
      </Field>
      {save.isError && <ErrorBanner message={message(save.error)} />}
      <div className="flex gap-3">
        <Button disabled={!form.name.trim() || (!form.category_id && !form.proposed_category) || save.isPending} onClick={() => save.mutate()}>保存为草稿</Button>
        {onCancel && <Button variant="ghost" onClick={onCancel}>取消</Button>}
      </div>
    </div>
  </Section>;
}

function LibrarySection({ subject }: { subject: Subject }) {
  const client = useQueryClient();
  const library = subject.library;
  const [picked, setPicked] = useState<Record<string, { forms: string[]; genre: string; tone: string; reader_level: string; writer: string }>>({});
  const [editing, setEditing] = useState(false);
  const refresh = () => client.invalidateQueries({ queryKey: ["search-subject"] });
  const open = useMutation({
    mutationFn: () => api.post<{ opened: { project_id: number }[]; skipped: { question_id: string; reason: string }[] }>(`${BASE}/subjects/${subject.id}/projects`, {
      items: Object.entries(picked).map(([question_id, item]) => ({ question_id, ...item })) }),
    onSuccess: () => { setPicked({}); refresh(); },
  });
  const count = Object.keys(picked).length;
  return <Section title="问题库" eyebrow="AI 生成，可修改" aside={library && <Button size="sm" variant="secondary" onClick={() => setEditing(!editing)}>{editing ? "收起修改" : "修改问题库"}</Button>}>
    {!library ? <Notice>还没有问题库。对第三方模型说「做 {subject.name} 的搜索推广」，它会查搜索信号生成问题库并开项目；也可以先自己写几个问题。</Notice> : <>
      <p className="mb-3 text-sm text-ink-500">第 {library.revision_no} 版 · {library.origin === "ai" ? "AI 生成" : "人工修改"} · 主词：{library.keywords.primary.join("、") || "未定"}{library.keywords.long_tail.length ? ` · 长尾词：${library.keywords.long_tail.join("、")}` : ""}</p>
      <div className="space-y-2">{library.questions.map(question => {
        const [label, tone] = COVERAGE[question.coverage];
        const choice = picked[question.id];
        return <div key={question.id} className="rounded-lg border p-3">
          <div className="flex flex-wrap items-center gap-2">
            <input type="checkbox" aria-label={`选中 ${question.text}`} disabled={question.coverage !== "none" || (!choice && count >= 5)} checked={!!choice}
              onChange={event => { const next = { ...picked }; if (event.target.checked) next[question.id] = { forms: ["text"], genre: "buying-guide", tone: "专业中立科普", reader_level: "小白", writer: "external" }; else delete next[question.id]; setPicked(next); }} />
            <span className="font-medium">{question.text}</span><Chip tone={tone}>{label}</Chip><Chip>优先级 {question.priority}</Chip>
            {question.source_kind === "search" ? <a className="text-sm underline" href={question.source_url} target="_blank" rel="noreferrer">来源</a> : <Chip>模型推断</Chip>}
          </div>
          {question.intent && <p className="mt-1 text-sm text-ink-500">{question.intent}</p>}
          {choice && <div className="mt-2 flex flex-wrap items-end gap-3">
            <Field label="形式"><div className="flex gap-3">{FORMS.map(([key, name]) => <label key={key} className="flex items-center gap-1 text-sm"><input type="checkbox" checked={choice.forms.includes(key)}
              onChange={event => setPicked({ ...picked, [question.id]: { ...choice, forms: event.target.checked ? [...choice.forms, key] : choice.forms.filter(f => f !== key) } })} />{name}</label>)}</div></Field>
            <Field label="体裁"><select className={inputClass} value={choice.genre} onChange={event => setPicked({ ...picked, [question.id]: { ...choice, genre: event.target.value } })}>{subject.genres.map(g => <option key={g.key} value={g.key}>{g.name}（{g.for}）</option>)}</select></Field>
            <Field label="基调"><input className={inputClass} value={choice.tone} onChange={event => setPicked({ ...picked, [question.id]: { ...choice, tone: event.target.value } })} /></Field>
            <Field label="读者"><select className={inputClass} value={choice.reader_level} onChange={event => setPicked({ ...picked, [question.id]: { ...choice, reader_level: event.target.value } })}><option>小白</option><option>行业内行</option></select></Field>
            <Field label="谁来写"><select className={inputClass} value={choice.writer} onChange={event => setPicked({ ...picked, [question.id]: { ...choice, writer: event.target.value } })}><option value="external">第三方模型</option><option value="platform">平台模型</option></select></Field>
          </div>}
        </div>;
      })}</div>
      {open.isError && <div className="mt-3"><ErrorBanner message={message(open.error)} /></div>}
      {open.data?.skipped.length ? <Notice tone="warn">跳过：{open.data.skipped.map(s => s.reason).join("；")}</Notice> : null}
      <div className="mt-3 flex items-center gap-3">
        <Button disabled={!count || open.isPending || Object.values(picked).some(item => !item.forms.length)} onClick={() => open.mutate()}>开 {count || ""} 个项目</Button>
        <span className="text-sm text-ink-500">一次最多 5 个。开出后对第三方模型说「做这几个项目」；也可以直接让它按优先级自己开。</span>
      </div>
      {editing && <LibraryEditor subject={subject} onDone={() => { setEditing(false); refresh(); }} />}
    </>}
    {!library && <LibraryEditor subject={subject} onDone={refresh} />}
  </Section>;
}

function LibraryEditor({ subject, onDone }: { subject: Subject; onDone: () => void }) {
  const library = subject.library;
  const [questions, setQuestions] = useState(() => (library?.questions || []).map(q => ({ id: q.id, text: q.text, intent: q.intent, priority: q.priority, source_url: q.source_url })));
  const [primary, setPrimary] = useState((library?.keywords.primary || []).join("、"));
  const [longTail, setLongTail] = useState((library?.keywords.long_tail || []).join("、"));
  const [brand, setBrand] = useState((library?.keywords.brand || []).join("、"));
  const save = useMutation({
    mutationFn: () => api.put(`${BASE}/subjects/${subject.id}/library`, { questions: questions.filter(q => q.text.trim()), keywords: { primary: words(primary), long_tail: words(longTail), brand: words(brand) } }),
    onSuccess: onDone,
  });
  return <div className="mt-4 space-y-3 rounded-lg border border-dashed p-4">
    <p className="text-sm text-ink-500">这类东西用户常问：{subject.hints.common_questions.join("、")}</p>
    {questions.map((question, index) => <div key={question.id || `new-${index}`} className="flex flex-wrap gap-2">
      <input aria-label={`问题 ${index + 1}`} className={`${inputClass} min-w-[240px] flex-1`} value={question.text} onChange={event => setQuestions(questions.map((q, i) => i === index ? { ...q, text: event.target.value } : q))} />
      <select aria-label="优先级" className={inputClass} value={question.priority} onChange={event => setQuestions(questions.map((q, i) => i === index ? { ...q, priority: Number(event.target.value) } : q))}><option value={1}>优先级 1</option><option value={2}>优先级 2</option><option value={3}>优先级 3</option></select>
      <Button variant="ghost" size="sm" onClick={() => setQuestions(questions.filter((_, i) => i !== index))}>删除</Button>
    </div>)}
    <Button variant="secondary" size="sm" onClick={() => setQuestions([...questions, { id: "", text: "", intent: "", priority: 2, source_url: "" }])}>加一个问题</Button>
    <Field label="主词"><input className={inputClass} value={primary} onChange={event => setPrimary(event.target.value)} /></Field>
    <Field label="长尾词"><input className={inputClass} value={longTail} onChange={event => setLongTail(event.target.value)} /></Field>
    <Field label="品牌词"><input className={inputClass} value={brand} onChange={event => setBrand(event.target.value)} /></Field>
    {save.isError && <ErrorBanner message={message(save.error)} />}
    <Button disabled={save.isPending} onClick={() => save.mutate()}>保存为新版本</Button>
  </div>;
}

function ProjectLink({ row }: { row: ProjectRow }) {
  return <Link to={row.href} className="flex flex-wrap items-center justify-between gap-3 rounded-xl border bg-white p-4 hover:border-ink-400">
    <div><p className="font-medium text-ink-900">{row.title}</p><p className="text-sm text-ink-500">{row.settings.forms.map(f => FORM_NAMES[f]).join("、")} · {row.settings.tone} · {row.settings.writer === "platform" ? "平台模型" : "第三方模型"}</p></div>
    <div className="flex gap-2">{row.pending_review > 0 && <Chip tone="warn">{row.pending_review} 个版本待审</Chip>}<Chip tone={row.state === "done" ? "good" : "neutral"}>{row.state === "done" ? "已有成稿" : "在做"}</Chip></div>
  </Link>;
}

function ProjectPage({ projectId }: { projectId: number }) {
  const project = useQuery({ queryKey: ["search-project", currentUser(), projectId], queryFn: () => api.get<SearchProject>(`${BASE}/projects/${projectId}`) });
  if (project.isPending) return <Page><Spinner /></Page>;
  if (project.isError) return <Page><ErrorBanner message={message(project.error)} /></Page>;
  const data = project.data;
  const decision = (version: Version) => version.review?.decision === "approved" ? ["已通过", "good"] as const : version.review?.decision === "changes_requested" ? ["已写意见，AI 修改中", "warn"] as const
    : version.candidate?.status === "frozen" ? ["待你审", "warn"] as const : ["AI 改写中", "neutral"] as const;
  return <Page>
    <Link to={`${BASE}/subjects/${data.subject.id}`} className="text-sm text-ink-500">← {data.subject.name}</Link>
    <PageHeader title={data.title} lead={<>回答：{data.question} · 体裁：{data.genre_name} · 基调：{data.settings.tone} · 读者：{data.settings.reader_level} · 资料第 {data.subject.revision_no} 版</>} />
    {data.settings.cover_error && <Notice tone="warn">公众号封面没生成出来：{data.settings.cover_error}。下次存核心稿时会再试；检查「设置 → 模型」里的封面生图。</Notice>}
    <Notice>中间步骤都由 AI 完成，这里只看进度。要审的平台版本在「待审成稿」{data.pending_review ? `（${data.pending_review} 个）` : ""}；视频的导演稿、小样、成片在作品页由你看。</Notice>
    <div className="mt-4 space-y-3">{data.units.map(unit => <Section key={unit.unit_id} title={<><WorkCode id={unit.unit_id} /><Link className="underline" to={unit.href}>{unit.title}</Link><RatioSuffix ratio={unit.aspect_ratio} /></>} aside={<Chip>{unit.role === "core" ? "核心稿" : "衍生"} · {FORM_NAMES[unit.modality] || unit.modality}</Chip>}>
      <p className="text-sm text-ink-600">{unit.label} · {unit.writer === "platform" ? "平台模型" : "第三方模型"}</p>
      {unit.versions.length > 0 && <div className="mt-2 space-y-1">{unit.versions.map(version => {
        const [label, tone] = decision(version);
        return <div key={version.variant_id} className="flex flex-wrap items-center gap-2 text-sm"><Chip>{version.channel}</Chip><span>{version.title}</span><Chip tone={tone}>{label}</Chip>
          {version.review?.comment && <span className="text-ink-500">意见：{version.review.comment}</span>}</div>;
      })}</div>}
    </Section>)}</div>
    <Runs query={`project_id=${projectId}`} projectId={projectId} />
    <div className="mt-4"><Link to={`${BASE}?tab=review`}><Button variant="secondary">去审成稿</Button></Link></div>
  </Page>;
}

function AiDraft() {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [links, setLinks] = useState("");
  const [note, setNote] = useState("");
  const [runId, setRunId] = useState<number | null>(null);
  const start = useMutation({ mutationFn: () => api.post<Run>(`${BASE}/drafts`, { name, links: links.split("\n").map(l => l.trim()).filter(Boolean), note }), onSuccess: run => setRunId(run.id) });
  const run = useQuery({ queryKey: ["search-run", currentUser(), runId], enabled: runId !== null,
    queryFn: async () => (await api.get<Run[]>(`${BASE}/runs`)).find(r => r.id === runId) || null,
    refetchInterval: query => { const data = query.state.data as Run | null | undefined; return data && ["queued", "running"].includes(data.status) ? 2000 : false; } });
  return <Section title="让平台模型起草" eyebrow="可选">
    <p className="mb-3 text-sm text-ink-500">只填名称和资料链接，平台会搜索、读原文、起草资料；每条事实都附原文链接并核对。起草完是草稿，等你确认。用第三方模型起草的话，直接对它说「起草 XX 的推广对象资料」。</p>
    <div className="space-y-3">
      <Field label="名称"><input className={inputClass} value={name} onChange={event => setName(event.target.value)} /></Field>
      <Field label="资料链接" hint="一行一个：官网、产品页、检测报告等"><textarea className={`${inputClass} min-h-[80px]`} value={links} onChange={event => setLinks(event.target.value)} /></Field>
      <Field label="补充说明"><input className={inputClass} value={note} onChange={event => setNote(event.target.value)} /></Field>
      {start.isError && <ErrorBanner message={message(start.error)} />}
      <Button disabled={!name.trim() || start.isPending || (!!run.data && ["queued", "running"].includes(run.data.status))} onClick={() => start.mutate()}>开始起草</Button>
      {run.data && <RunCard run={run.data} />}
      {run.data?.status === "done" && run.data.subject_id && <Button variant="secondary" onClick={() => navigate(`${BASE}/subjects/${run.data!.subject_id}`)}>去确认资料</Button>}
    </div>
  </Section>;
}

function StartPanel({ subjectId }: { subjectId: number }) {
  const client = useQueryClient();
  const [count, setCount] = useState(3);
  const [forms, setForms] = useState<string[]>(["text"]);
  const [tone, setTone] = useState("专业中立科普");
  const [reader, setReader] = useState("小白");
  const [platforms, setPlatforms] = useState<string[]>(["wechat", "zhihu", "toutiao"]);
  const start = useMutation({ mutationFn: () => api.post<Run>(`${BASE}/subjects/${subjectId}/start`, { count, forms, tone, reader_level: reader, platforms }),
    onSuccess: () => client.invalidateQueries({ queryKey: ["search-runs"] }) });
  const toggle = (list: string[], key: string, on: boolean) => on ? [...list, key] : list.filter(item => item !== key);
  return <Section title="开始（平台模型自动做）" eyebrow="用第三方模型时，直接对它说「做这个推广对象的搜索推广」">
    <p className="mb-3 text-sm text-ink-500">平台按「设置 → 模型」里各用途的模型自动生成问题库、开项目、写稿自查、出各平台版本，最后整批送到「待审成稿」。本期平台模型只做文章；选了图文、视频的作品会等第三方模型接手。</p>
    <div className="flex flex-wrap items-end gap-4">
      <Field label="这次做几个项目"><select className={inputClass} value={count} onChange={event => setCount(Number(event.target.value))}>{[1, 2, 3, 4, 5].map(n => <option key={n} value={n}>{n}</option>)}</select></Field>
      <Field label="形式"><div className="flex gap-3">{FORMS.map(([key, name]) => <label key={key} className="flex items-center gap-1 text-sm"><input type="checkbox" checked={forms.includes(key)} onChange={event => setForms(toggle(forms, key, event.target.checked))} />{name}</label>)}</div></Field>
      <Field label="基调"><input className={inputClass} value={tone} onChange={event => setTone(event.target.value)} /></Field>
      <Field label="读者"><select className={inputClass} value={reader} onChange={event => setReader(event.target.value)}><option>小白</option><option>行业内行</option></select></Field>
    </div>
    <Field label="发布平台"><div className="flex flex-wrap gap-3">{PLATFORMS.map(([key, name]) => <label key={key} className="flex items-center gap-1 text-sm"><input type="checkbox" checked={platforms.includes(key)} onChange={event => setPlatforms(toggle(platforms, key, event.target.checked))} />{name}</label>)}</div></Field>
    {start.isError && <div className="mt-2"><ErrorBanner message={message(start.error)} /></div>}
    <Button className="mt-3" disabled={start.isPending || !forms.length || !platforms.length} onClick={() => start.mutate()}>开始</Button>
  </Section>;
}

function Runs({ query, projectId }: { query: string; projectId?: number }) {
  const client = useQueryClient();
  const runs = useQuery({ queryKey: ["search-runs", currentUser(), query], queryFn: () => api.get<Run[]>(`${BASE}/runs?${query}`),
    refetchInterval: q => ((q.state.data as Run[] | undefined) || []).some(r => ["queued", "running"].includes(r.status)) ? 2500 : false });
  const refresh = () => { client.invalidateQueries({ queryKey: ["search-runs"] }); client.invalidateQueries({ queryKey: ["search-subject"] }); client.invalidateQueries({ queryKey: ["search-project"] }); };
  const retry = useMutation({ mutationFn: (id: number) => api.post(`${BASE}/runs/${id}/retry`), onSuccess: refresh });
  const resume = useMutation({ mutationFn: () => api.post(`${BASE}/projects/${projectId}/continue`), onSuccess: refresh });
  if (!runs.data?.length) return null;
  return <Section title="平台模型执行记录">
    {(retry.isError || resume.isError) && <ErrorBanner message={message(retry.error || resume.error)} />}
    <div className="space-y-3">{runs.data.slice(0, 5).map(run => <div key={run.id}>
      <RunCard run={projectId ? { ...run, steps: run.steps.filter(s => !s.project_id || s.project_id === projectId) } : run} />
      {["failed", "interrupted"].includes(run.status) && <Button size="sm" variant="secondary" className="mt-2" disabled={retry.isPending} onClick={() => retry.mutate(run.id)}>重试</Button>}
    </div>)}</div>
    {projectId && <Button size="sm" variant="ghost" className="mt-2" disabled={resume.isPending} onClick={() => resume.mutate()}>从当前进度继续</Button>}
  </Section>;
}

function RunCard({ run }: { run: Run }) {
  const [label, tone] = RUN_STATUS[run.status];
  return <div className="rounded-lg border p-3 text-sm">
    <div className="flex flex-wrap items-center gap-2"><span className="font-medium">{run.kind_name}</span><Chip tone={tone}>{label}</Chip><span className="text-ink-500">{new Date(run.created_at).toLocaleString()}</span></div>
    {run.error && <p className="mt-1 text-rose-700">{run.error}</p>}
    <ul className="mt-2 space-y-1">{run.steps.map((step, index) => {
      const [stepLabel, stepTone] = STEP_STATUS[step.status] || ["", "neutral"];
      return <li key={index} className="flex flex-wrap items-center gap-2"><Chip tone={stepTone}>{stepLabel}</Chip><span>{step.step}</span>
        {step.project_id && <Link className="underline" to={`${BASE}/projects/${step.project_id}`}>项目 #{step.project_id}</Link>}
        <span className="text-ink-500">{step.detail}</span>{step.model && <span className="text-ink-400">· {step.model}</span>}</li>;
    })}</ul>
  </div>;
}

function ReviewQueue() {
  const client = useQueryClient();
  const queue = useQuery({ queryKey: ["search-review", currentUser()], queryFn: () => api.get<ReviewGroup[]>(`${BASE}/review`) });
  const [notes, setNotes] = useState<Record<number, string>>({});
  const [done, setDone] = useState<Record<number, string>>({});
  const refresh = () => { client.invalidateQueries({ queryKey: ["search-review"] }); client.invalidateQueries({ queryKey: ["search-delivered"] }); };
  const approve = useMutation({ mutationFn: (item: ReviewItem) => api.post<{ package_url: string }>(`${BASE}/candidates/${item.candidate_id}/approve`, { candidate_hash: item.candidate_hash }),
    onSuccess: (result, item) => { setDone({ ...done, [item.candidate_id]: result.package_url }); refresh(); } });
  const changes = useMutation({ mutationFn: (item: ReviewItem) => api.post(`${BASE}/candidates/${item.candidate_id}/request-changes`, { candidate_hash: item.candidate_hash, comment: notes[item.candidate_id] || "" }),
    onSuccess: refresh });
  if (queue.isPending) return <Spinner />;
  if (queue.isError) return <ErrorBanner message={message(queue.error)} />;
  return <div className="space-y-6">
    <Notice>第 2 关：逐篇看各平台版本。通过的立即可以复制文案、下载稿件包；写了意见的回到 AI 修改，改好后会再送过来。视频的成片在作品页审。</Notice>
    {(approve.isError || changes.isError) && <ErrorBanner message={message(approve.error || changes.error)} />}
    {!queue.data.length && <EmptyState title="没有待审的成稿" />}
    {queue.data.map(group => <Section key={group.project_id} title={<Link className="underline" to={`${BASE}/projects/${group.project_id}`}>{group.title}</Link>} eyebrow={`回答：${group.question}`}>
      <div className="space-y-4">{group.items.map(item => <article key={item.candidate_id} className="rounded-xl border p-4">
        <div className="flex flex-wrap items-center gap-2"><Chip tone="info">{item.channel}</Chip><h3 className="font-medium text-ink-900">{item.title}</h3></div>
        {item.body && <div className="mt-3 max-h-[420px] overflow-y-auto whitespace-pre-wrap rounded-lg bg-ink-50 p-3 text-[14px] leading-relaxed">{item.body}</div>}
        <textarea aria-label="意见" className={`${inputClass} mt-3 min-h-[60px] w-full`} placeholder="要改的地方写在这里，再点「写意见」" value={notes[item.candidate_id] || ""} onChange={event => setNotes({ ...notes, [item.candidate_id]: event.target.value })} />
        <div className="mt-2 flex flex-wrap gap-3">
          <Button disabled={approve.isPending} onClick={() => approve.mutate(item)}>通过</Button>
          <Button variant="secondary" disabled={changes.isPending || !(notes[item.candidate_id] || "").trim()} onClick={() => changes.mutate(item)}>写意见</Button>
          {done[item.candidate_id] && <a className="text-sm underline" href={done[item.candidate_id]}>下载稿件包</a>}
        </div>
      </article>)}</div>
    </Section>)}
  </div>;
}

function DeliveredList() {
  const rows = useQuery({ queryKey: ["search-delivered", currentUser()], queryFn: () => api.get<Delivered[]>(`${BASE}/delivered`) });
  const [copied, setCopied] = useState<number | null>(null);
  if (rows.isPending) return <Spinner />;
  if (rows.isError) return <ErrorBanner message={message(rows.error)} />;
  return <Section title="已交付的稿件">
    <p className="mb-3 text-sm text-ink-500">可以自己发，也可以转给别人发；平台不跟踪发表。如属付费推广，按规定标明「广告」。</p>
    {!rows.data.length && <EmptyState title="还没有通过的稿件" />}
    <div className="space-y-2">{rows.data.map(row => <div key={row.delivery_target_id} className="flex flex-wrap items-center justify-between gap-3 rounded-xl border bg-white p-4">
      <div><p className="font-medium text-ink-900">{row.title}</p><p className="text-sm text-ink-500">{row.project_title} · {row.channel}</p></div>
      <div className="flex gap-2">
        {row.body && <Button size="sm" variant="secondary" onClick={() => { void navigator.clipboard.writeText(`${row.title}\n\n${row.body}`); setCopied(row.delivery_target_id); }}>{copied === row.delivery_target_id ? "已复制" : "复制文案"}</Button>}
        <a href={row.package_url}><Button size="sm">下载稿件包</Button></a>
      </div>
    </div>)}</div>
  </Section>;
}

function Categories() {
  const client = useQueryClient();
  const categories = useCategories();
  const [names, setNames] = useState<Record<string, string>>({});
  const [editing, setEditing] = useState<{ id: number; name: string } | null>(null);
  const refresh = () => client.invalidateQueries({ queryKey: ["search-categories"] });
  const create = useMutation({ mutationFn: (top: string) => api.post(`${BASE}/categories`, { top_key: top, name: names[top] || "" }), onSuccess: (_, top) => { setNames({ ...names, [top]: "" }); refresh(); } });
  const patch = useMutation({ mutationFn: (body: { id: number; name?: string; status?: string }) => api.patch(`${BASE}/categories/${body.id}`, { name: body.name, status: body.status }), onSuccess: () => { setEditing(null); refresh(); } });
  if (categories.isPending) return <Spinner />;
  if (categories.isError) return <ErrorBanner message={message(categories.error)} />;
  return <div className="space-y-4">
    {(create.isError || patch.isError) && <ErrorBanner message={message(create.error || patch.error)} />}
    {categories.data.tops.map(top => <Section key={top.key} title={top.name}>
      <div className="space-y-2">{top.categories.map(item => <div key={item.id} className="flex flex-wrap items-center gap-2">
        {editing?.id === item.id ? <>
          <input aria-label="小类名称" className={inputClass} value={editing.name} onChange={event => setEditing({ id: item.id, name: event.target.value })} />
          <Button size="sm" onClick={() => patch.mutate({ id: item.id, name: editing.name })}>保存</Button>
          <Button size="sm" variant="ghost" onClick={() => setEditing(null)}>取消</Button>
        </> : <>
          <span className={item.status === "active" ? "text-ink-900" : "text-ink-400 line-through"}>{item.name}</span>
          {item.status !== "active" && <Chip>已停用</Chip>}
          <Button size="sm" variant="ghost" onClick={() => setEditing({ id: item.id, name: item.name })}>改名</Button>
          <Button size="sm" variant="ghost" onClick={() => patch.mutate({ id: item.id, status: item.status === "active" ? "disabled" : "active" })}>{item.status === "active" ? "停用" : "启用"}</Button>
        </>}
      </div>)}</div>
      <div className="mt-3 flex gap-2">
        <input aria-label={`${top.name}新小类`} className={inputClass} placeholder="新小类名称" value={names[top.key] || ""} onChange={event => setNames({ ...names, [top.key]: event.target.value })} />
        <Button size="sm" variant="secondary" disabled={!(names[top.key] || "").trim() || create.isPending} onClick={() => create.mutate(top.key)}>增加</Button>
      </div>
    </Section>)}
  </div>;
}
