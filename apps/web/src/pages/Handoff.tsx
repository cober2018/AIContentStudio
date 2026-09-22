import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { api } from "../api";
import { Button, ChannelBadge, EmptyState, Field, Spinner, StatusBadge, inputClass } from "../components/ui";

type Topic = { id: number; title: string; fact_pack: { id: number; status: string; checksum: string | null } };
type FactPackDetail = { items: { evidence_kind: string; public_use_allowed: boolean | null; public_use_revoked_at: string | null }[] };
type MotherRevision = { id: number; revision_no: number; title: string; body_markdown: string; evidence_checksum: string | null };
type Draft = {
  id: number; title: string; channel: string; status: string; candidate_readiness: string | null;
  fact_check: { result?: string; stats?: { warnings?: number; blockers?: number } } | null;
  thread_posts: { index: number; text: string }[] | null;
  media: { id: number; role: string; public_use_allowed: boolean | null; rights_status: string | null; public_use_revoked_at: string | null }[];
  asset_id: number | null; approved_candidate_hash: string | null;
};

export default function Handoff() {
  const queryClient = useQueryClient();
  const [topicId, setTopicId] = useState(0);
  const [selectedRevision, setSelectedRevision] = useState(0);
  const [mother, setMother] = useState({ title: "", body_markdown: "" });
  const [adaptation, setAdaptation] = useState({ channel: "wechat", title: "", body_markdown: "", thread_text: "" });
  const [warningNote, setWarningNote] = useState("");
  const [message, setMessage] = useState("");

  const topics = useQuery({ queryKey: ["topics"], queryFn: () => api.get<Topic[]>("/topics") });
  const selectedTopic = useMemo(() => (topics.data || []).find((topic) => topic.id === topicId), [topics.data, topicId]);
  const revisions = useQuery({
    queryKey: ["mother-revisions", topicId],
    queryFn: () => api.get<MotherRevision[]>(`/article-handoff/topics/${topicId}/mother-revisions`),
    enabled: !!topicId,
  });
  const factPack = useQuery({
    queryKey: ["handoff-fact-pack", selectedTopic?.fact_pack.id],
    queryFn: () => api.get<FactPackDetail>(`/fact-packs/${selectedTopic!.fact_pack.id}`),
    enabled: !!selectedTopic,
  });
  const revisionId = selectedRevision || revisions.data?.[revisions.data.length - 1]?.id || 0;
  const drafts = useQuery({
    queryKey: ["mother-drafts", revisionId],
    queryFn: () => api.get<Draft[]>(`/article-handoff/mother-revisions/${revisionId}/drafts`),
    enabled: !!revisionId,
  });
  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ["mother-revisions", topicId] });
    queryClient.invalidateQueries({ queryKey: ["mother-drafts", revisionId] });
    queryClient.invalidateQueries({ queryKey: ["assets"] });
  };
  const fail = (error: unknown) => setMessage(error instanceof Error ? error.message : "操作失败");

  const importMother = useMutation({
    mutationFn: () => api.post<MotherRevision>(`/article-handoff/topics/${topicId}/mother-revisions`, mother),
    onSuccess: (revision) => { setSelectedRevision(revision.id); setMother({ title: "", body_markdown: "" }); setMessage("母稿已按不可变版本导入"); refresh(); },
    onError: fail,
  });
  const createDraft = useMutation({
    mutationFn: () => api.post(`/article-handoff/mother-revisions/${revisionId}/drafts`, {
      channel: adaptation.channel,
      title: adaptation.title || undefined,
      body_markdown: adaptation.body_markdown || undefined,
      thread_posts: adaptation.channel === "x_thread"
        ? adaptation.thread_text.split(/\n+/).map((line) => line.trim()).filter(Boolean)
        : undefined,
    }),
    onSuccess: () => { setMessage("平台适配稿已创建；请完成检查、审核和交付授权"); setAdaptation({ channel: "wechat", title: "", body_markdown: "", thread_text: "" }); refresh(); },
    onError: fail,
  });
  const check = useMutation({ mutationFn: (id: number) => api.post(`/drafts/${id}/fact-check`), onSuccess: () => { setMessage("FactCheck 已完成"); refresh(); }, onError: fail });
  const submit = useMutation({ mutationFn: (id: number) => api.post(`/drafts/${id}/submit-review`), onSuccess: () => { setMessage("已提交审核"); refresh(); }, onError: fail });
  const approve = useMutation({
    mutationFn: (id: number) => api.post(`/reviews/drafts/${id}/approve`, warningNote ? { warning_dispositions: { reviewer_note: warningNote } } : {}),
    onSuccess: () => { setMessage("内容已批准；下一步在内容资产库创建人工交付目标"); setWarningNote(""); refresh(); },
    onError: fail,
  });
  const uploadCover = useMutation({
    mutationFn: ({ draftId, file }: { draftId: number; file: File }) => {
      const form = new FormData(); form.append("file", file);
      return api.upload(`/article-handoff/drafts/${draftId}/media?role=cover&rights_status=cleared&public_use_allowed=true`, form);
    },
    onSuccess: () => { setMessage("封面已加入候选素材，需重新检查后再批准"); refresh(); }, onError: fail,
  });
  const revokeMedia = useMutation({
    mutationFn: ({ draftId, mediaId }: { draftId: number; mediaId: number }) => api.post(`/article-handoff/drafts/${draftId}/media/${mediaId}/revoke-public-use`, { note: "编辑在交付工作台撤销公开使用权限" }),
    onSuccess: () => { setMessage("已撤销素材公开使用权限；相关未完成交付目标已停止"); refresh(); }, onError: fail,
  });

  return (
    <div className="mx-auto max-w-6xl space-y-5 p-8">
      <div>
        <h1 className="text-xl font-semibold">文章交付工作台</h1>
        <p className="mt-1 text-sm text-slate-500">只生成公众号和 X Thread 的本地成品包；不会自动写入草稿箱或发布。</p>
      </div>
      {message && <div className="rounded-md bg-sky-50 px-3 py-2 text-sm text-sky-800">{message}</div>}

      <section className="rounded-lg border border-slate-200 bg-white p-5">
        <Field label="1. 选择已绑定冻结 FactPack 的选题">
          <select className={inputClass} value={topicId} onChange={(event) => { setTopicId(Number(event.target.value)); setSelectedRevision(0); }}>
            <option value={0}>请选择选题</option>
            {(topics.data || []).map((topic) => <option key={topic.id} value={topic.id}>{topic.title} · {topic.fact_pack.status}</option>)}
          </select>
        </Field>
        {selectedTopic?.fact_pack.status !== "frozen" && topicId > 0 && <p className="mt-2 text-sm text-rose-700">该选题未绑定冻结 FactPack，不能进入 M1。</p>}
        {factPack.data && <p className="mt-2 text-xs text-slate-500">证据分类：{Object.entries(factPack.data.items.reduce<Record<string, number>>((counts, item) => ({ ...counts, [item.evidence_kind]: (counts[item.evidence_kind] || 0) + 1 }), {})).map(([kind, count]) => `${kind} ${count}`).join(" · ")}；公开可交付 {factPack.data.items.filter((item) => item.public_use_allowed && !item.public_use_revoked_at).length} 项</p>}
      </section>

      {topicId > 0 && selectedTopic?.fact_pack.status === "frozen" && <>
        <section className="rounded-lg border border-slate-200 bg-white p-5">
          <h2 className="text-base font-medium">2. 导入或选择母稿版本</h2>
          <p className="mt-1 text-xs text-slate-400">导入后母稿不可覆盖；每一次新导入都会形成新的版本和证据校验绑定。</p>
          {(revisions.data || []).length > 0 && <div className="mt-3 flex flex-wrap gap-2">
            {(revisions.data || []).map((revision) => <button key={revision.id} onClick={() => setSelectedRevision(revision.id)} className={`rounded border px-3 py-1.5 text-sm ${revisionId === revision.id ? "border-slate-900 bg-slate-900 text-white" : "border-slate-300 text-slate-600"}`}>v{revision.revision_no} · {revision.title}</button>)}
          </div>}
          <div className="mt-4 grid gap-3 md:grid-cols-[1fr_2fr_auto] md:items-end">
            <Field label="标题"><input className={inputClass} value={mother.title} onChange={(event) => setMother({ ...mother, title: event.target.value })} /></Field>
            <Field label="原始 Markdown 正文"><textarea rows={4} className={inputClass} value={mother.body_markdown} onChange={(event) => setMother({ ...mother, body_markdown: event.target.value })} /></Field>
            <Button disabled={!mother.title || !mother.body_markdown || importMother.isPending} onClick={() => importMother.mutate()}>{importMother.isPending ? "导入中…" : "导入母稿"}</Button>
          </div>
        </section>

        {revisionId > 0 && <section className="rounded-lg border border-slate-200 bg-white p-5">
          <h2 className="text-base font-medium">3. 创建平台适配稿</h2>
          <div className="mt-3 grid gap-3 md:grid-cols-2">
            <Field label="渠道"><select className={inputClass} value={adaptation.channel} onChange={(event) => setAdaptation({ ...adaptation, channel: event.target.value })}><option value="wechat">公众号文章</option><option value="x_thread">X Thread</option></select></Field>
            <Field label="适配标题（留空使用母稿标题）"><input className={inputClass} value={adaptation.title} onChange={(event) => setAdaptation({ ...adaptation, title: event.target.value })} /></Field>
          </div>
          {adaptation.channel === "x_thread" ? <Field label="X Thread（每行一帖，顺序即交付顺序）"><textarea rows={5} className={inputClass} value={adaptation.thread_text} onChange={(event) => setAdaptation({ ...adaptation, thread_text: event.target.value })} /></Field> : <Field label="公众号 Markdown（留空使用母稿正文）"><textarea rows={5} className={inputClass} value={adaptation.body_markdown} onChange={(event) => setAdaptation({ ...adaptation, body_markdown: event.target.value })} /></Field>}
          <div className="mt-3"><Button disabled={createDraft.isPending || (adaptation.channel === "x_thread" && !adaptation.thread_text.trim())} onClick={() => createDraft.mutate()}>{createDraft.isPending ? "创建中…" : "创建适配稿"}</Button></div>
        </section>}

        {revisionId > 0 && <section className="rounded-lg border border-slate-200 bg-white p-5">
          <h2 className="text-base font-medium">4. 候选检查与批准</h2>
          <p className="mt-1 text-xs text-slate-400">内容批准不等于平台发布。批准后请到「内容资产」建立对应账号的人工交付目标。</p>
          {drafts.isLoading ? <Spinner /> : (drafts.data || []).length === 0 ? <EmptyState title="还没有适配稿" hint="先从母稿创建公众号或 X Thread 版本" /> : <div className="mt-3 space-y-3">{(drafts.data || []).map((draft) => <div key={draft.id} className="rounded border border-slate-200 p-4">
            <div className="flex flex-wrap items-center gap-2"><span className="font-medium">{draft.title}</span><ChannelBadge channel={draft.channel} /><StatusBadge status={draft.status} />{draft.candidate_readiness && <StatusBadge status={draft.candidate_readiness} />}</div>
            <div className="mt-2 text-xs text-slate-500">FactCheck：{draft.fact_check?.result || "未执行"} · 素材：{draft.media.length} 项{draft.asset_id && <> · 已批准哈希 {draft.approved_candidate_hash?.slice(0, 12)}</>}</div>
            {draft.media.length > 0 && <div className="mt-2 flex flex-wrap gap-2 text-xs">{draft.media.map((media, index) => <span key={media.id} className="rounded bg-slate-50 px-2 py-1 text-slate-600">{index + 1}. {media.role} · {media.public_use_revoked_at ? "已撤销公开使用" : media.public_use_allowed && media.rights_status ? "公开可交付" : "权限未完成"}{media.public_use_allowed && !media.public_use_revoked_at && <button className="ml-2 text-rose-700" onClick={() => { if (window.confirm("撤销后，相关未完成交付目标会停止。是否继续？")) revokeMedia.mutate({ draftId: draft.id, mediaId: media.id }); }}>撤销</button>}</span>)}</div>}
            {draft.channel === "wechat" && !draft.media.some((media) => media.role === "cover" && media.public_use_allowed && media.rights_status) && <label className="mt-3 inline-flex cursor-pointer rounded border border-dashed border-slate-300 px-2.5 py-1 text-xs text-slate-600">上传有公开权限的封面<input className="hidden" type="file" accept="image/png,image/jpeg,image/webp" onChange={(event) => { const file = event.target.files?.[0]; if (file) uploadCover.mutate({ draftId: draft.id, file }); }} /></label>}
            {draft.status !== "approved" && <div className="mt-3 flex flex-wrap gap-2"><Button size="sm" variant="secondary" disabled={check.isPending} onClick={() => check.mutate(draft.id)}>执行检查</Button><Button size="sm" variant="secondary" disabled={!draft.fact_check || submit.isPending} onClick={() => submit.mutate(draft.id)}>提交审核</Button><Button size="sm" disabled={draft.status !== "ready_for_review" || approve.isPending} onClick={() => approve.mutate(draft.id)}>批准候选</Button></div>}
          </div>)}</div>}
          <div className="mt-4 max-w-xl"><Field label="如有 warning，记录处理说明"><input className={inputClass} value={warningNote} onChange={(event) => setWarningNote(event.target.value)} placeholder="无 warning 可留空" /></Field></div>
        </section>}
      </>}
    </div>
  );
}
