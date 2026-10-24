import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../api";
import { Button, Chip, ErrorBanner, Field, inputClass } from "../components/ui";
import { MatchRun, SegmentResult, UploadOwn, errorText, useMatchRun } from "./MaterialMatchView";

import { useShotSlots, type ShotSlotsView, type Slot } from "./shotSlots";

const STATUS: Record<Slot["status"], { label: string; tone: "warn" | "info" | "good" }> = {
  missing: { label: "缺素材", tone: "warn" }, candidates: { label: "有候选", tone: "info" }, chosen: { label: "已选定", tone: "good" },
};

function shotText(slot: Slot) {
  const seconds = Math.round((slot.duration_ms || 0) / 100) / 10;
  return [slot.narration && `口播：${slot.narration}`, slot.visual && `画面：${slot.visual}`, slot.purpose, ...slot.requirements, seconds ? `时长：${seconds} 秒` : ""].filter(Boolean).join("；").slice(0, 4000);
}

function Copy({ text }: { text: string }) {
  const [done, setDone] = useState(false);
  return <button type="button" className="text-[12px] text-accent-700 underline" onClick={() => void navigator.clipboard.writeText(text).then(() => { setDone(true); setTimeout(() => setDone(false), 1200); })}>{done ? "已复制" : "复制"}</button>;
}

function PromptBlock({ label, text }: { label: string; text?: string }) {
  if (!text) return null;
  return <div><div className="flex items-baseline gap-2"><dt className="text-ink-500">{label}</dt><Copy text={text} /></div>
    <dd className="mt-0.5 rounded-md bg-paper/80 px-2 py-1.5 font-mono text-[12px] leading-relaxed text-ink-800">{text}</dd></div>;
}

function BriefView({ slot, base, onSaved }: { slot: Slot; base: string; onSaved: () => void }) {
  const brief = slot.brief!;
  const [form, setForm] = useState<{ query_zh: string; queries_en: string; t2v_prompt: string; frame_prompt: string; prompt: string } | null>(null);
  const [state, setState] = useState<{ busy?: boolean; error?: string }>({});
  const mode = brief.gen_mode === "frame" || (!brief.t2v_prompt && brief.frame_prompt) ? "frame" : "text";
  const patch = async (body: Record<string, unknown>) => {
    setState({ busy: true });
    try { await api.patch(`${base}/shot-slots/${encodeURIComponent(slot.id)}/brief`, body); setForm(null); setState({}); onSaved(); }
    catch (error) { setState({ error: errorText(error) }); }
  };
  const save = () => form && void patch({
    query_zh: form.query_zh.trim(), t2v_prompt: form.t2v_prompt.trim(), frame_prompt: form.frame_prompt.trim(), prompt: form.prompt.trim(),
    queries_en: form.queries_en.split("\n").map(item => item.trim()).filter(Boolean).slice(0, 2) });
  if (form) return <div className="space-y-2 rounded-lg border border-ink-200 p-3">
    <Field label="中文搜索词"><input className={inputClass} maxLength={60} value={form.query_zh} onChange={event => setForm({ ...form, query_zh: event.target.value })} /></Field>
    <Field label="英文搜索词（一行一条，最多两条）"><textarea className={inputClass} rows={2} value={form.queries_en} onChange={event => setForm({ ...form, queries_en: event.target.value })} /></Field>
    <Field label="直接生成视频的提示词"><textarea className={inputClass} rows={4} maxLength={1500} value={form.t2v_prompt} onChange={event => setForm({ ...form, t2v_prompt: event.target.value })} /></Field>
    <Field label="① 首帧生图提示词"><textarea className={inputClass} rows={3} maxLength={1000} value={form.frame_prompt} onChange={event => setForm({ ...form, frame_prompt: event.target.value })} /></Field>
    <Field label="② 图生视频提示词（从首帧开始怎么动）"><textarea className={inputClass} rows={3} maxLength={1000} value={form.prompt} onChange={event => setForm({ ...form, prompt: event.target.value })} /></Field>
    {state.error && <ErrorBanner message={state.error} />}
    <div className="flex gap-2"><Button size="sm" disabled={state.busy} onClick={save}>保存</Button><Button size="sm" variant="ghost" disabled={state.busy} onClick={() => setForm(null)}>取消</Button></div>
  </div>;
  const english = (brief.queries_en || []).concat(brief.keywords_en || []);
  return <dl className="space-y-1.5 text-[13px]">
    <div className="flex flex-wrap items-baseline gap-x-2"><dt className="text-ink-500">建议</dt><dd>{brief.footage === "motion" ? <><strong className="font-semibold text-rose-700">后期做（动效、图解、数字卡）</strong>；想用实拍或生成的也可以上传</> : "先找素材，找不到再用提示词生成"}</dd></div>
    {brief.query_zh && <div className="flex flex-wrap items-baseline gap-x-2"><dt className="text-ink-500">搜索词</dt><dd className="min-w-0">{brief.query_zh}</dd><Copy text={brief.query_zh} /></div>}
    {english.length > 0 && <div className="flex flex-wrap items-baseline gap-x-2"><dt className="text-ink-500">英文</dt><dd className="min-w-0">{english.join(" / ")}</dd><Copy text={english.join("\n")} /></div>}
    <div className="flex flex-wrap items-center gap-2 pt-1"><dt className="text-ink-500">生成方式</dt>
      <div className="inline-flex overflow-hidden rounded-full border border-ink-200" role="radiogroup" aria-label="生成方式">
        {([["text", "直接生成视频"], ["frame", "先生成首帧，再生成视频"]] as const).map(([key, label]) => <button key={key} type="button" role="radio" aria-checked={mode === key}
          disabled={state.busy || mode === key} onClick={() => void patch({ gen_mode: key })}
          className={`px-3 py-1 text-[12.5px] ${mode === key ? "bg-ink-900 text-white" : "text-ink-700 hover:bg-ink-50"}`}>{label}</button>)}
      </div></div>
    {mode === "text" ? <PromptBlock label="视频提示词" text={brief.t2v_prompt || brief.prompt} />
      : <><PromptBlock label="① 首帧生图提示词" text={brief.frame_prompt} /><PromptBlock label="② 图生视频提示词（用上面的首帧）" text={brief.prompt} /></>}
    {state.error && <ErrorBanner message={state.error} />}
    <button type="button" className="text-[12px] text-ink-500 underline" onClick={() => setForm({ query_zh: brief.query_zh || "", queries_en: (brief.queries_en || []).join("\n"), t2v_prompt: brief.t2v_prompt || "", frame_prompt: brief.frame_prompt || "", prompt: brief.prompt || "" })}>改简报</button>
  </dl>;
}

function Candidates({ runId, segmentId, onChanged }: { runId: number; segmentId: string; onChanged: () => void }) {
  const run = useMatchRun(runId);
  const segment = run.data?.segments.find(item => item.id === segmentId);
  if (!run.data || !segment) return null;
  return <SegmentResult run={run.data} segment={segment} compact bare onAccepted={onChanged} onChanged={() => { void run.refetch(); onChanged(); }} />;
}

function DirectUpload({ base, slot, onDone }: { base: string; slot: Slot; onDone: () => void }) {
  const [target, setTarget] = useState<{ run_id: number; segment_id: string } | null>(null);
  const [error, setError] = useState("");
  const run = useMatchRun(target?.run_id ?? null);
  const segment = run.data?.segments.find(item => item.id === target?.segment_id);
  const open = async () => {
    try { setTarget(await api.post<{ run_id: number; segment_id: string }>(`${base}/shot-slots/${encodeURIComponent(slot.id)}/upload-target`)); }
    catch (cause) { setError(errorText(cause)); }
  };
  return <>
    <Button size="sm" variant="ghost" onClick={() => void open()}>直接上传</Button>
    {error && <ErrorBanner message={error} />}
    {run.data && segment && <UploadOwn run={run.data as MatchRun} segment={segment} onClose={() => setTarget(null)} onDone={() => { setTarget(null); onDone(); }} />}
  </>;
}

function SlotRow({ slot, base, source, busy, onSearch, onChanged }: { slot: Slot; base: string; source: ShotSlotsView["source"]; busy: boolean; onSearch: (slots: Slot[]) => void; onChanged: () => void }) {
  const status = STATUS[slot.status];
  const searching = !!slot.latest && ["queued", "running"].includes(slot.latest.status);
  return <details className="group rounded-xl border border-ink-200/90 bg-surface px-4 py-3" open={slot.status !== "chosen"}>
    <summary className="flex cursor-pointer list-none flex-wrap items-baseline gap-x-2 gap-y-1">
      <span className="font-serif text-[15px] font-semibold text-ink-900">{slot.label}</span>
      <Chip tone={status.tone}>{status.label}</Chip>
      {slot.brief?.footage === "motion" && <span className="text-[12.5px] font-semibold text-rose-700">后期做</span>}
      {searching && <span className="text-[12px] text-ink-500">正在找…</span>}
      <span className="w-full text-[13.5px] text-ink-700">{slot.narration || slot.visual}</span>
    </summary>
    <div className="mt-3 space-y-3">
      {slot.visual && <p className="text-[13px] text-ink-700"><span className="text-ink-500">画面：</span>{slot.visual}</p>}
      {slot.brief ? <BriefView slot={slot} base={base} onSaved={onChanged} />
        : <p className="text-[12.5px] text-ink-500">还没有简报。找一次素材会同时写出搜索词、首帧和视频提示词。</p>}
      {slot.picks.length > 0 && <div className="text-[13px]"><p className="text-ink-500">{slot.picks.every(pick => pick.auto) ? "AI 自动选的" : "你选的"}（{slot.picks.length}）</p><ul className="mt-1 space-y-0.5">{slot.picks.map(pick =>
        <li key={pick.material_revision_id} className="text-ink-800">{pick.title || `素材 #${pick.material_revision_id}`} · {pick.uploaded ? "你上传的" : pick.provider_label}{pick.media_type === "video" ? " · 视频" : ""}{pick.auto ? ` · 自动${pick.auto.score != null ? ` ${pick.auto.score.toFixed(2)}` : ""}` : ""}{pick.auto?.reason ? <span className="block text-[12px] text-ink-500">{pick.auto.reason}</span> : null}</li>)}</ul></div>}
      {slot.autofill?.outcome === "gap" && !slot.picks.length && <p className="text-[12.5px] text-rose-700">AI 补齐没找到：{slot.autofill.reason}</p>}
      {source === "draft" && (slot.bound_revision_id
        ? <p className="text-[12.5px] text-emerald-800">成片里用的是素材 #{slot.bound_revision_id}。</p>
        : slot.picks.length > 0 && <p className="text-[12.5px] text-ink-500">在视频工作台的素材步骤里选用并保存，才会进成片。</p>)}
      {slot.latest && <Candidates runId={slot.latest.run_id} segmentId={slot.latest.segment_id} onChanged={onChanged} />}
      <div className="flex flex-wrap gap-2">
        <Button size="sm" variant="secondary" disabled={busy || searching} onClick={() => onSearch([slot])}>{slot.brief ? "再找一次" : "写简报并找素材"}</Button>
        {!slot.latest && <DirectUpload base={base} slot={slot} onDone={onChanged} />}
      </div>
    </div>
  </details>;
}

export default function ShotSlotsBoard({ projectId, unitId }: { projectId: number; unitId: number }) {
  const client = useQueryClient();
  const base = `/content-projects/${projectId}/units/${unitId}`;
  const view = useShotSlots(projectId, unitId);
  const [filter, setFilter] = useState<Slot["status"] | "all">("all");
  const [state, setState] = useState<{ busy?: boolean; error?: string }>({});
  const refresh = () => { void view.refetch(); void client.invalidateQueries({ queryKey: ["material-match-runs"] }); };
  const search = async (targets: Slot[]) => {
    setState({ busy: true });
    try {
      await api.post("/material-match-runs", {
        scope: "shots", project_id: projectId, unit_id: unitId, aspect: "9:16",
        title: targets.length === 1 ? `镜头找素材 · ${targets[0].label}` : `镜头找素材 · ${targets.length} 个镜头`,
        shots: targets.map(slot => ({ id: slot.id, label: slot.label, text: shotText(slot) })) });
      setState({}); refresh();
    } catch (error) { setState({ error: errorText(error) }); }
  };
  if (view.isPending) return <p className="text-sm text-ink-500">读取镜头…</p>;
  if (view.isError || !view.data) return <ErrorBanner message={errorText(view.error)} />;
  const data = view.data;
  if (!data.shots.length) return <p className="text-sm text-ink-500">还没有镜头计划。先在下方生成镜头计划，每个镜头就会出现在这里。</p>;
  const noBrief = data.shots.filter(slot => !slot.brief && slot.status !== "chosen");
  const noPrompt = data.shots.filter(slot => slot.brief_stale);
  const writeBriefs = async () => {
    setState({ busy: true });
    try { await api.post(`${base}/shot-slots/briefs`); setState({}); refresh(); } catch (error) { setState({ error: errorText(error) }); }
  };
  const shown = data.shots.filter(slot => filter === "all" || slot.status === filter);
  return <section className="space-y-3">
    <div className="flex flex-wrap items-center gap-2">
      {(["all", "missing", "candidates", "chosen"] as const).map(key => <button key={key} type="button" onClick={() => setFilter(key)}
        className={`rounded-full border px-3 py-1 text-[12.5px] ${filter === key ? "border-ink-800 bg-ink-900 text-white" : "border-ink-200 text-ink-700"}`}>
        {key === "all" ? `全部 ${data.shots.length}` : `${STATUS[key].label} ${data.counts[key]}`}</button>)}
      <span className="ml-auto" />
      {noPrompt.length > 0 && <Button size="sm" variant="ghost" disabled={state.busy} onClick={() => void writeBriefs()}>{state.busy ? "处理中…" : `更新生成提示词（${noPrompt.length}）`}</Button>}
      {noBrief.length > 0 && <Button size="sm" variant="secondary" disabled={state.busy} onClick={() => void search(noBrief)}>给没简报的镜头写简报并找素材（{noBrief.length}）</Button>}
    </div>
    <p className="text-[12.5px] leading-relaxed text-ink-500">每个镜头是一个素材位：平台搜的、你上传的、生成的都能放进来，随时可以补；缺素材不影响写稿、配音和剪辑。{data.source === "plan" ? "现在按镜头计划显示，导演稿生成后会自动对上。" : ""}</p>
    {state.error && <ErrorBanner message={state.error} />}
    <div className="space-y-2">{shown.map(slot => <SlotRow key={slot.id} slot={slot} base={base} source={data.source} busy={!!state.busy} onSearch={targets => void search(targets)} onChanged={refresh} />)}</div>
  </section>;
}
