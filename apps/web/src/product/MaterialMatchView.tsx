import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, Eye, EyeOff, Film, Image as ImageIcon, TriangleAlert } from "lucide-react";
import { useState } from "react";
import { api, currentUser } from "../api";
import { Button, Chip, ErrorBanner, Field, Modal, Notice, inputClass } from "../components/ui";
import { usePreview } from "./materialLibraryModel";

export type Candidate = {
  id: string; origin: "own" | "open"; provider: string; provider_label: string; title: string; media_type: "image" | "video";
  width: number | null; height: number | null; duration_ms: number | null; thumb_url?: string | null; page_url?: string | null;
  material_id?: number; material_revision_id?: number; creator?: string; attribution_text?: string | null;
  license: { code: string; name: string; url?: string | null; accept_code: string | null };
  score: number; seen?: boolean; seen_text?: string; reason?: string; conflicts?: string[]; visual_note?: string;
  eligible_main: boolean; needs_full_review: boolean; orientation_note?: string; accepted?: { material_id: number; material_revision_id: number }; uploaded?: boolean;
};
export type Segment = {
  id: string; order: number; label: string; text: string; role: "proof" | "explain" | "mood" | "data"; media_type: "video" | "image";
  must_show: string; status: "pending" | "matched" | "gap" | "motion"; footage?: "real" | "motion"; main_id: string | null; chosen_id?: string; picked_ids?: string[]; candidates: Candidate[];
  request?: { must_show: string; role: string; suggestion: string }; rejected?: { note: string; rejected_at: string };
};
export type RunOwner = { project?: { id: number; title: string } | null; unit?: { id: number; title: string; modality: string; label: string } | null };
export type MatchRun = RunOwner & {
  id: number; scope: "script" | "shots"; title: string; status: "queued" | "running" | "completed" | "failed" | "cancelled" | "interrupted";
  project_id: number | null; unit_id: number | null; progress: { stage?: string; done?: number; total?: number }; error_code: string | null;
  segments: Segment[]; providers: Record<string, { status: string; error?: string }>; visual?: "enabled" | "unavailable"; created_at: string | null;
  settings: { aspect: string; min_short_side: number };
};
export type Accepted = { material_id: number; material_revision_id: number; segment_id: string; candidate_id: string; project_id: number | null };

export const ROLE_LABELS: Record<string, string> = { proof: "证明画面", explain: "解释画面", mood: "氛围空镜", data: "数字 / 关键词" };
const STAGE_LABELS: Record<string, string> = { queued: "排队中", planning: "正在拆分段落与检索词", matching: "正在搜索并看图评分", done: "已完成" };
const PROVIDER_STATE: Record<string, string> = { off: "未配置密钥", failed: "本次连不上", ok: "可用" };
const ERRORS: Record<string, string> = {
  material_match_plan_failed: "拆分段落时模型调用失败，可以继续运行重试。", material_match_plan_invalid: "模型没有返回可用的段落，请换一段文案或重试。",
  material_match_interrupted: "运行中断了（服务重启），已完成的段落保留，可以继续。", material_match_failed: "运行出错，已完成的段落保留，可以继续。",
  material_match_still_running: "还在找素材，等这一轮结束再标记。", material_match_download_failed: "下载素材失败，可能是网络或来源暂时不可用。", material_match_download_unavailable: "这个素材没有满足分辨率要求的下载版本。",
  provider_output_decode_failed: "下载的文件无法解码或太大，换一个候选试试。", provider_preview_capacity: "同时待处理的素材太多，稍等再试。",
};

export function errorText(error: unknown) { const text = error instanceof Error ? error.message : "操作失败"; return ERRORS[text] ?? text; }
export function runActive(run?: MatchRun | null) { return !!run && (run.status === "queued" || run.status === "running"); }

export function useMatchRun(runId: number | null) {
  return useQuery({
    queryKey: ["material-match-run", currentUser(), runId], enabled: runId !== null, retry: false,
    queryFn: () => api.get<MatchRun>(`/material-match-runs/${runId}`),
    refetchInterval: query => runActive(query.state.data) ? 2500 : false,
  });
}

function rightsFor(code: string) {
  if (code === "own") return null;
  return { public: true, model: true, commercial: code !== "nasa" };
}

function Thumb({ candidate }: { candidate: Candidate }) {
  const own = usePreview(candidate.material_id ?? 0, candidate.material_revision_id, "thumb", candidate.origin === "own");
  const url = candidate.origin === "own" ? own.url : candidate.thumb_url ?? undefined;
  const Icon = candidate.media_type === "video" ? Film : ImageIcon;
  return <div ref={own.ref} className="relative aspect-[4/3] overflow-hidden rounded-[10px] bg-ink-100">
    {url ? <img src={url} alt="" loading="lazy" referrerPolicy="no-referrer" className="absolute inset-0 h-full w-full object-cover" />
      : <div className="absolute inset-0 grid place-items-center text-ink-400"><Icon size={20} strokeWidth={1.4} /></div>}
    {candidate.media_type === "video" && <span className="absolute left-1.5 top-1.5 inline-flex items-center gap-1 rounded-md bg-ink-950/65 px-1.5 py-0.5 text-[10.5px] text-white/95"><Film size={10} />视频</span>}
    {candidate.uploaded ? <span className="absolute bottom-1.5 left-1.5 rounded-md bg-emerald-600/90 px-1.5 py-0.5 text-[11px] text-white">你上传的</span>
      : <span className={`absolute right-1.5 top-1.5 rounded-md px-1.5 py-0.5 font-mono text-[11px] tabular-nums ${candidate.seen ? "bg-surface/95 text-ink-900" : "bg-ink-950/55 text-white/90"}`}>{Math.round(candidate.score * 100)}</span>}
  </div>;
}

function AcceptDialog({ run, segment, candidate, onClose, onDone }: { run: MatchRun; segment: Segment; candidate: Candidate; onClose: () => void; onDone: (value: Accepted) => void }) {
  const client = useQueryClient();
  const defaults = rightsFor(candidate.license.code) ?? { public: false, model: true, commercial: false };
  // Pixabay titles are long tag lists; maxLength does not trim a prefilled value, and the API rejects over 200.
  const [form, setForm] = useState({ title: candidate.title.slice(0, 200), ...defaults });
  const projects = useQuery({ queryKey: ["projects", currentUser()], queryFn: () => api.get<{ id: number; title: string }[]>("/content-projects"), retry: false, enabled: !run.project_id });
  const [projectId, setProjectId] = useState(run.project_id ? String(run.project_id) : "");
  const [state, setState] = useState<{ busy?: boolean; error?: string }>({});
  const submit = async () => {
    setState({ busy: true });
    try {
      const value = await api.post<Accepted>(`/material-match-runs/${run.id}/accept`, {
        segment_id: segment.id, candidate_id: candidate.id, title: form.title.trim() || undefined, project_id: projectId ? Number(projectId) : undefined,
        public_use_allowed: form.public, model_use_allowed: form.model, commercial_use_allowed: form.commercial,
      });
      await client.invalidateQueries({ queryKey: ["material-match-run", currentUser(), run.id] });
      void client.invalidateQueries({ queryKey: ["material-library"] });
      onDone(value);
    } catch (error) { setState({ error: errorText(error) }); }
  };
  const own = candidate.origin === "own";
  return <Modal title={own ? "使用素材库里的这个素材" : "下载并加入素材库"} onClose={onClose}>
    <div className="space-y-4">
      {!own && <Notice>{candidate.license.name}{candidate.attribution_text ? `。署名：${candidate.attribution_text}` : ""}。下载后成为素材库里的一个版本，来源网址、许可证和署名一并记录。</Notice>}
      {own && <p className="text-[13.5px] text-ink-700">它已在素材库中，不会重复下载；{run.project_id || projectId ? "会关联到项目，备注写明对应段落。" : "选择项目后会关联过去。"}</p>}
      {!own && <Field label="素材标题"><input className={inputClass} value={form.title} maxLength={200} onChange={event => setForm({ ...form, title: event.target.value })} /></Field>}
      {!run.project_id && <Field label="关联项目（可选）"><select className={inputClass} value={projectId} onChange={event => setProjectId(event.target.value)}>
        <option value="">不关联</option>{(projects.data ?? []).map(project => <option key={project.id} value={project.id}>{project.title}</option>)}</select></Field>}
      {!own && <div className="flex flex-wrap gap-5 text-[13.5px] text-ink-800">
        <label className="inline-flex items-center gap-2"><input type="checkbox" checked={form.public} onChange={event => setForm({ ...form, public: event.target.checked })} />允许公开发布</label>
        <label className="inline-flex items-center gap-2"><input type="checkbox" checked={form.model} onChange={event => setForm({ ...form, model: event.target.checked })} />允许 AI 剪辑</label>
        <label className="inline-flex items-center gap-2"><input type="checkbox" checked={form.commercial} onChange={event => setForm({ ...form, commercial: event.target.checked })} />允许商业使用</label>
      </div>}
      {candidate.needs_full_review && <p className="flex items-start gap-1.5 text-[12.5px] text-amber-800"><TriangleAlert size={14} className="mt-0.5 shrink-0" />只核对过封面帧，用之前请看完整片段。</p>}
      {state.error && <ErrorBanner message={state.error} />}
      <div className="flex justify-end gap-2"><Button variant="secondary" onClick={onClose}>取消</Button><Button disabled={state.busy} onClick={() => void submit()}>{state.busy ? (own ? "处理中…" : "下载中…") : own ? "使用" : "下载并入库"}</Button></div>
    </div>
  </Modal>;
}

function CandidateCard({ run, segment, candidate, compact, onAccepted, onChanged }: { run: MatchRun; segment: Segment; candidate: Candidate; compact?: boolean; onAccepted?: (value: Accepted) => void; onChanged?: () => void }) {
  const client = useQueryClient();
  const [open, setOpen] = useState(false);
  const [removing, setRemoving] = useState<{ busy?: boolean; error?: string }>({});
  const removeUpload = async () => {
    if (!window.confirm("取消这份上传？它会从这一段移除，文件仍留在素材库。")) return;
    setRemoving({ busy: true });
    try {
      await api.post(`/material-match-runs/${run.id}/segments/${encodeURIComponent(segment.id)}/detach`, { candidate_id: candidate.id });
      await client.invalidateQueries({ queryKey: ["material-match-run", currentUser(), run.id] });
      setRemoving({}); onChanged?.();
    } catch (error) { setRemoving({ error: errorText(error) }); }
  };
  const main = segment.main_id === candidate.id;
  const chosen = segment.chosen_id === candidate.id || !!segment.picked_ids?.includes(candidate.id);
  return <article className={`min-w-0 rounded-[12px] border p-2 transition-colors ${chosen ? "border-emerald-400 bg-emerald-50/50" : main ? "border-accent-300 bg-accent-50/40" : "border-ink-200 bg-surface"}`}>
    <div className="relative"><Thumb candidate={candidate} />
      {candidate.uploaded && <button type="button" aria-label="取消这份上传" title="取消这份上传" disabled={removing.busy} onClick={() => void removeUpload()}
        className="absolute right-1.5 top-1.5 grid h-6 w-6 place-items-center rounded-full bg-ink-950/70 text-[13px] leading-none text-white hover:bg-rose-600 disabled:opacity-50">×</button>}
    </div>
    {removing.error && <p className="mt-1 text-[11.5px] text-rose-700">{removing.error}</p>}
    <div className="px-0.5 pt-2">
      <div className="flex flex-wrap items-center gap-1.5 text-[11.5px]">
        {main && <span className="rounded-pill bg-accent-500 px-1.5 py-px text-paper">主选</span>}
        <span className="text-ink-500">{candidate.provider_label}</span>
        <span className="text-ink-400">·</span>
        <span className="truncate text-ink-500" title={candidate.license.name}>{candidate.license.name}</span>
      </div>
      <p className="mt-1 line-clamp-2 text-[12.5px] leading-snug text-ink-900" title={candidate.title}>{candidate.title}</p>
      {!compact && <p className="mt-1.5 flex items-start gap-1 text-[12px] leading-snug text-ink-600">
        {candidate.seen ? <Eye size={12} className="mt-[3px] shrink-0 text-ink-400" /> : <EyeOff size={12} className="mt-[3px] shrink-0 text-ink-400" />}
        <span className="line-clamp-3">{candidate.seen ? candidate.seen_text || candidate.reason : candidate.visual_note || "未看图，只按标题匹配，需人工确认"}</span>
      </p>}
      {candidate.orientation_note && <p className="mt-1 text-[11.5px] text-ink-500">{candidate.orientation_note}</p>}
      {(candidate.conflicts ?? []).length > 0 && <p className="mt-1 line-clamp-2 text-[11.5px] text-amber-800">⚠ {candidate.conflicts!.join("；")}</p>}
      <div className="mt-2 flex items-center gap-2">
        {candidate.accepted || chosen ? <span className="inline-flex items-center gap-1 text-[12px] text-emerald-700"><Check size={13} />已采用</span>
          : <Button size="sm" variant={main ? "primary" : "secondary"} onClick={() => setOpen(true)}>用这个</Button>}
        {candidate.page_url && <a href={candidate.page_url} target="_blank" rel="noreferrer" className="text-[12px] text-ink-500 underline">来源</a>}
      </div>
    </div>
    {open && <AcceptDialog run={run} segment={segment} candidate={candidate} onClose={() => setOpen(false)} onDone={value => { setOpen(false); onAccepted?.(value); }} />}
  </article>;
}

export function ownerLabel(run: RunOwner) {
  return run.project ? `${run.project.title}${run.unit ? ` · ${run.unit.label}` : ""}` : null;
}

export function ownerLink(run: RunOwner) {
  return run.project ? run.unit ? `/projects/${run.project.id}/units/${run.unit.id}/production` : `/projects/${run.project.id}` : null;
}

export function UploadOwn({ run, segment, onClose, onDone }: { run: MatchRun; segment: Segment; onClose: () => void; onDone: () => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [form, setForm] = useState({ title: segment.label, origin: "own", source: "", modelUse: true, publicUse: false });
  const [state, setState] = useState<{ busy?: boolean; error?: string }>({});
  const thirdParty = form.origin === "third_party";
  const ready = !!file && (!thirdParty || form.source.trim().length >= 3);
  const submit = async () => {
    if (!file) return;
    setState({ busy: true });
    try {
      const kind = file.type.startsWith("video/") ? "video" : "image";
      const query = new URLSearchParams({ kind, title: form.title.trim() || file.name, source_kind: "upload", rights_status: "cleared",
        public_use_allowed: String(form.publicUse), model_use_allowed: String(form.modelUse),
        attribution_text: thirdParty ? form.source.trim() : form.origin === "ai" ? "AI 生成 · 示意图，不是实拍" : "自己拍摄或制作", ...(thirdParty && /^https?:\/\//.test(form.source.trim()) ? { source_url: form.source.trim() } : {}) });
      const body = new FormData(); body.append("file", file);
      const material = await api.upload<{ revisions: { id: number }[] }>(`/materials/upload?${query}`, body);
      const revision = material.revisions[material.revisions.length - 1];
      await api.post(`/material-match-runs/${run.id}/segments/${encodeURIComponent(segment.id)}/attach`, { material_revision_id: revision.id });
      onDone();
    } catch (error) { setState({ error: errorText(error) }); }
  };
  return <Modal title={`上传自己的素材 · ${segment.label}`} onClose={onClose} closeOnBackdrop={false}>
    <div className="space-y-4">
      <Field label="图片或视频（30MB 以内）"><input type="file" accept="image/*,video/mp4,video/quicktime" className={inputClass} onChange={event => setFile(event.target.files?.[0] ?? null)} /></Field>
      <Field label="标题"><input className={inputClass} maxLength={200} value={form.title} onChange={event => setForm({ ...form, title: event.target.value })} /></Field>
      <Field label="来源"><select className={inputClass} value={form.origin} onChange={event => setForm({ ...form, origin: event.target.value })}>
        <option value="own">自己拍摄或制作</option><option value="ai">AI 生成（会标为示意图）</option><option value="third_party">别人的作品（已获授权或许可）</option></select></Field>
      {thirdParty && <Field label="来源与授权（链接或说明，会作为署名保存）"><input className={inputClass} maxLength={1000} value={form.source} placeholder="比如：SubCom 新闻图片库，仅限报道使用" onChange={event => setForm({ ...form, source: event.target.value })} /></Field>}
      <label className="flex items-center gap-2 text-[13px]"><input type="checkbox" checked={form.modelUse} onChange={event => setForm({ ...form, modelUse: event.target.checked })} />允许 AI 看和使用这份素材</label>
      <label className="flex items-center gap-2 text-[13px]"><input type="checkbox" checked={form.publicUse} onChange={event => setForm({ ...form, publicUse: event.target.checked })} />可以公开发布</label>
      {state.error && <ErrorBanner message={state.error} />}
      <div className="flex justify-end gap-2"><Button variant="ghost" disabled={state.busy} onClick={onClose}>取消</Button><Button disabled={!ready || state.busy} onClick={() => void submit()}>{state.busy ? "上传中…" : "上传并用在这一段"}</Button></div>
    </div>
  </Modal>;
}

function RejectSegment({ run, segment, onChanged }: { run: MatchRun; segment: Segment; onChanged?: () => void }) {
  const [open, setOpen] = useState(false);
  const [note, setNote] = useState("");
  const [state, setState] = useState<{ busy?: boolean; error?: string }>({});
  const [uploading, setUploading] = useState(false);
  const upload = <>
    {uploading && <UploadOwn run={run} segment={segment} onClose={() => setUploading(false)} onDone={() => { setUploading(false); onChanged?.(); }} />}
  </>;
  const canUpload = !runActive(run) && segment.status !== "pending";
  if (segment.rejected) return <>{upload}<p className="mt-3 rounded-xl bg-rose-50 px-4 py-2.5 text-[13px] text-rose-900">你标记了都不合适{segment.rejected.note ? `：${segment.rejected.note}` : ""}。AI 会按这条意见重新找，也可以<button className="underline" onClick={() => setUploading(true)}>上传自己的</button>。</p></>;
  // A chosen segment can still take more material (a cover may need a photo plus a detail shot).
  if (segment.chosen_id || runActive(run) || !["matched", "gap"].includes(segment.status)) return canUpload ? <>{upload}<div className="mt-2"><Button size="sm" variant="ghost" onClick={() => setUploading(true)}>{segment.chosen_id ? "再上传一份" : "上传自己的"}</Button></div></> : upload;
  const send = async () => {
    setState({ busy: true });
    try { await api.post(`/material-match-runs/${run.id}/segments/${encodeURIComponent(segment.id)}/reject`, { note: note.trim() }); setOpen(false); setState({}); onChanged?.(); }
    catch (error) { setState({ error: errorText(error) }); }
  };
  return open ? <div className="mt-3 space-y-2 rounded-xl border border-ink-200 p-3">
    <Field label="哪里不合适（可选，AI 会照这个重新找）"><textarea className={inputClass} rows={2} maxLength={500} value={note} placeholder="比如：要现代布缆船，不要老照片" onChange={event => setNote(event.target.value)} /></Field>
    {state.error && <ErrorBanner message={state.error} />}
    <div className="flex gap-2"><Button size="sm" disabled={state.busy} onClick={() => void send()}>确认都不合适</Button><Button size="sm" variant="ghost" disabled={state.busy} onClick={() => setOpen(false)}>取消</Button></div>
  </div> : <>{upload}<div className="mt-2 flex flex-wrap gap-2">{segment.candidates.length > 0 && <Button size="sm" variant="ghost" onClick={() => setOpen(true)}>都不合适</Button>}<Button size="sm" variant="ghost" onClick={() => setUploading(true)}>上传自己的</Button></div></>;
}

export function SegmentResult({ run, segment, compact, bare, onAccepted, onChanged }: { run: MatchRun; segment: Segment; compact?: boolean; bare?: boolean; onAccepted?: (value: Accepted) => void; onChanged?: () => void }) {
  return <section className={compact ? "space-y-2" : "border-t border-ink-200/80 py-6 first:border-t-0 first:pt-0"}>
    {!bare && <><div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
      <span className="font-serif text-[15px] font-semibold text-ink-900">{segment.label}</span>
      <Chip tone={segment.role === "proof" ? "accent" : "neutral"}>{ROLE_LABELS[segment.role]}</Chip>
      {segment.status === "gap" && <Chip tone="warn">缺素材</Chip>}
      {segment.status === "motion" && <Chip tone="info">动效制作</Chip>}
      {segment.status === "pending" && <span className="text-[12px] text-ink-400">等待中…</span>}
    </div>
    <p className={`text-[13.5px] leading-relaxed text-ink-700 ${compact ? "line-clamp-2" : "mt-1.5"}`}>{segment.text}</p></>}
    {!compact && segment.must_show && <p className="mt-1 text-[12.5px] text-ink-500">画面要出现：{segment.must_show}</p>}
    {segment.status !== "pending" && segment.candidates.length > 0 && <div className={`mt-3 grid gap-3 ${compact ? "grid-cols-2" : "grid-cols-2 sm:grid-cols-3 lg:grid-cols-5"}`}>
      {segment.candidates.slice(0, compact ? 4 : 5).map(candidate => <CandidateCard key={candidate.id} run={run} segment={segment} candidate={candidate} compact={compact} onAccepted={onAccepted} onChanged={onChanged} />)}
    </div>}
    <RejectSegment run={run} segment={segment} onChanged={onChanged} />
    {segment.status === "motion" && segment.request && <div className="mt-3 rounded-xl border border-sky-200 bg-sky-50/60 px-4 py-3 text-[13px] leading-relaxed text-sky-900">
      <p className="font-medium">不找素材 · {segment.request.suggestion}</p><p className="mt-0.5">要做出的画面：{segment.request.must_show}</p>
    </div>}
    {segment.status === "gap" && segment.request && <div className="mt-3 rounded-xl border border-dashed border-amber-300 bg-amber-50/60 px-4 py-3 text-[13px] leading-relaxed text-amber-900">
      <p className="font-medium">素材需求 · 建议{segment.request.suggestion}</p><p className="mt-0.5">画面要能看到：{segment.request.must_show}</p>
    </div>}
  </section>;
}

export function RunStatus({ run, onCancel, onResume, busy }: { run: MatchRun; onCancel?: () => void; onResume?: () => void; busy?: boolean }) {
  const done = run.progress.done ?? 0;
  const total = run.progress.total ?? 0;
  const providers = Object.entries(run.providers);
  return <div className="space-y-3">
    <div className="flex flex-wrap items-center gap-3">
      {runActive(run) ? <span className="text-[13px] text-ink-700">{STAGE_LABELS[run.progress.stage ?? "queued"] ?? "处理中"}{total ? ` · ${done}/${total}` : ""}</span>
        : <span className="text-[13px] text-ink-700">{run.status === "completed" ? `已完成 · ${run.segments.filter(item => item.status === "matched").length} 段有主选，${run.segments.filter(item => item.status === "gap").length} 段缺素材${run.segments.some(item => item.status === "motion") ? `，${run.segments.filter(item => item.status === "motion").length} 段做动效` : ""}`
          : run.status === "cancelled" ? "已取消" : errorText(new Error(run.error_code ?? "material_match_failed"))}</span>}
      <span className="ml-auto" />
      {runActive(run) && onCancel && <Button size="sm" variant="ghost" disabled={busy} onClick={onCancel}>取消</Button>}
      {["interrupted", "failed", "cancelled"].includes(run.status) && onResume && <Button size="sm" variant="secondary" disabled={busy} onClick={onResume}>继续运行</Button>}
    </div>
    {runActive(run) && <div className="h-1 overflow-hidden rounded-full bg-ink-100"><div className="h-full rounded-full bg-accent-500 transition-all duration-500" style={{ width: `${total ? Math.max(6, done / total * 100) : 8}%` }} /></div>}
    {(providers.length > 0 || run.visual === "unavailable") && <p className="text-[12px] leading-relaxed text-ink-500">
      {providers.map(([key, value]) => `${key.replace("stock.", "")}：${PROVIDER_STATE[value.status] ?? value.status}`).join(" · ")}
      {run.visual === "unavailable" && " · 未配置能看图的模型，不会自动选主选"}
    </p>}
  </div>;
}
