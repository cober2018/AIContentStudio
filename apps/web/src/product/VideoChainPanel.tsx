import { useQuery, useQueryClient } from "@tanstack/react-query";
import { lazy, Suspense, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, ApiError, currentUser } from "../api";
import { Button, ErrorBanner, inputClass } from "../components/ui";
import FileLocationActions from "./FileLocationActions";
import { PlatformSkillsSwitch } from "./ArticleChainPanel";
import type { VideoDraft, VideoPayload } from "./VideoStudioModel";

const StoryboardTable = lazy(() => import("./StoryboardTable"));
const ProductShotPanel = lazy(() => import("./ProductShotPanel"));

type Note = { time_ms: number | null; note: string };
type ShotWarning = { code: "shot_overexposed" | "shot_brightness_jump" | "dialogue_level_uneven"; shot_id: string | null; order: number; luma?: number; clipped?: number;
  from_shot_id?: string | null; from_order?: number; from_luma?: number; lufs?: number; median_lufs?: number; diff_lu?: number }
  | { code: "color_tags_not_srgb"; color_primaries: string; color_transfer: string; color_space: string }
  | { code: "cover_color_mismatch"; at_ms: number; mean: number; rgb: [number, number, number]; threshold: number }
  | { code: "cover_template_missing" } | { code: "cover_template_mismatch" }
  | { code: "source_brightness_diff"; shot_id: string | null; order: number; luma: number; source_luma: number; diff: number; source_basis?: "manifest" | "reported" | "estimated" }
  | { code: "source_highlight_diff"; shot_id: string | null; order: number; luma_p90: number; source_p90: number; diff: number; source_basis?: "manifest" | "reported" | "estimated" }
  | { code: "source_brightness"; shot_id: string | null; order: number; luma?: number; source_luma?: number; diff?: number; luma_p90?: number; source_p90?: number; diff_p90?: number; source_basis?: "manifest" | "reported" | "estimated" };
type ShotChecks = { status: string; basis: string; truncated?: boolean; warnings: ShotWarning[];
  thresholds: { overexposed_mean_luma: number; overexposed_clipped_percent: number; brightness_jump_luma: number; dialogue_spread_lu: number; source_brightness_diff?: number; source_highlight_diff?: number } };
type Cut = { execution_id: number; cut_output_id: number | null; cover_output_id?: number | null; shot_checks?: ShotChecks | null };
type Chain = {
  state: string; label: string; detail?: string; notes?: Note[]; execution_id?: number; cut_output_id?: number | null; cover_output_id?: number | null; shot_checks?: ShotChecks | null; draft_revision_no?: number;
  phase?: string; locked?: boolean; sample?: Cut; cover_redo?: { note: string; at: string };
  master: { id: number; revision_no: number; payload: VideoPayload } | null;
};
type Step = "draft" | "sample" | "final";
const STEPS = [["导演稿", ["not_started", "draft_review", "draft_changes"]], ["小样", ["making", "sample_review", "sample_changes"]], ["成片", ["finishing", "final_review", "final_changes", "done"]]] as const;
const ORDER: Step[] = ["draft", "sample", "final"];

function errorText(error: unknown) {
  const detail = error instanceof ApiError ? error.detail as { message?: string } | undefined : undefined;
  return detail?.message || (error instanceof Error ? error.message : "操作失败");
}

function shotName(id: string | null | undefined, order: number, basis: string) {
  return basis === "fixed" || !id ? `第 ${order * 3}–${order * 3 + 3} 秒` : `第 ${order + 1} 镜（${id}）`;
}

function warningText(item: ShotWarning, checks: ShotChecks) {
  if (item.code === "color_tags_not_srgb") return `成片颜色标记不是 sRGB（现在是 原色 ${item.color_primaries}、传输 ${item.color_transfer}、矩阵 ${item.color_space}；应为 bt709 / iec61966-2-1 / bt709）`;
  if (item.code === "cover_template_missing") return "封面没用角色的封面模板（交封面时没附模板渲染回执）";
  if (item.code === "cover_template_mismatch") return "封面用错了模板：附的渲染不是这个角色的封面模板";
  if (item.code === "cover_color_mismatch") return `封面与成片颜色不一致：平均差 ${item.mean}（R/G/B ${item.rgb.join(" / ")}，提示线 ${item.threshold}），最接近的是第 ${(item.at_ms / 1000).toFixed(1)} 秒那一帧`;
  const limits = checks.thresholds;
  const name = shotName(item.shot_id, item.order, checks.basis);
  if (item.code === "source_brightness") {
    const parts = [
      item.diff !== undefined ? `平均${item.diff < 0 ? "暗" : "亮"} ${Math.abs(item.diff)} 级（成片 ${item.luma}，原片 ${item.source_luma}，提示线 ${limits.source_brightness_diff ?? 8}）` : "",
      item.diff_p90 !== undefined ? `亮部${item.diff_p90 < 0 ? "暗" : "亮"} ${Math.abs(item.diff_p90)} 级（成片 ${item.luma_p90}，原片 ${item.source_p90}，提示线 ${limits.source_highlight_diff ?? 5}）` : "",
    ].filter(Boolean);
    return `第 ${item.order + 1} 镜和原片比：${parts.join("、")}；${{ manifest: "按剪辑清单的截取点", reported: "按交付时报的截取点", estimated: "按估计位置比，可能不准" }[item.source_basis || "estimated"]}`;
  }
  if (item.code === "source_highlight_diff") return `第 ${item.order + 1} 镜亮部比原片${item.diff < 0 ? "暗" : "亮"} ${Math.abs(item.diff)} 级（成片 ${item.luma_p90}，原片 ${item.source_p90}，提示线 ${limits.source_highlight_diff ?? 5}；${{ manifest: "按剪辑清单的截取点", reported: "按交付时报的截取点", estimated: "按估计位置比，可能不准" }[item.source_basis || "estimated"]}）`;
  if (item.code === "source_brightness_diff") return `第 ${item.order + 1} 镜成片比原片${item.diff < 0 ? "暗" : "亮"} ${Math.abs(item.diff)} 级（成片 ${item.luma}，原片 ${item.source_luma}，提示线 ${limits.source_brightness_diff ?? 8}）${item.source_basis === "estimated" ? "（按估计位置比，可能不准）" : ""}`;
  if (item.code === "shot_overexposed") return `${name}偏亮：平均亮度 ${item.luma}（提示线 ${limits.overexposed_mean_luma}），贴顶高光占 ${item.clipped}%（提示线 ${limits.overexposed_clipped_percent}%）`;
  if (item.code === "shot_brightness_jump") return `${shotName(item.from_shot_id, item.from_order ?? item.order - 1, checks.basis)} → ${name}亮度跳变：${item.from_luma} → ${item.luma}，差 ${Math.abs((item.luma ?? 0) - (item.from_luma ?? 0)).toFixed(1)}（提示线 ${limits.brightness_jump_luma}）`;
  return `${name}对白${(item.diff_lu ?? 0) > 0 ? "偏响" : "偏轻"}：${item.lufs} LUFS，和各段中间值 ${item.median_lufs} 差 ${Math.abs(item.diff_lu ?? 0)} LU（提示线 ${limits.dialogue_spread_lu} LU）`;
}

// Platform readings per 导演稿 shot; hints for the reviewer, the delivery is never held back by them.
function ShotCheckList({ checks }: { checks: ShotChecks }) {
  if (!checks.warnings.length) return <p className="mt-2 text-xs text-slate-500">交付检查：逐镜头亮度和对白音量没发现问题{checks.status === "partial" ? "（镜头太多，只查了前面一部分）" : ""}。</p>;
  return <div className="mt-2 rounded-lg bg-amber-50 p-3 text-xs text-amber-900" role="note" aria-label="交付检查">
    <p className="font-medium">交付检查提示（只是提醒，不影响交付）</p>
    <ul className="mt-1 list-disc space-y-0.5 pl-5">{checks.warnings.map((item, index) => <li key={index}>{warningText(item, checks)}</li>)}</ul>
    {(checks.status === "partial" || checks.truncated) && <p className="mt-1 text-amber-700">镜头太多，只列出了一部分。</p>}
  </div>;
}

// The cover is an image output of the same task, shown through the same signed preview as the cut.
function CoverPreview({ projectId, unitId, executionId, outputId }: { projectId: number; unitId: number; executionId: number; outputId: number }) {
  const [url, setUrl] = useState("");
  const [issue, setIssue] = useState("");
  useEffect(() => {
    let alive = true;
    setUrl(""); setIssue("");
    api.post<{ url: string }>(`/content-projects/${projectId}/units/${unitId}/creative-executions/${executionId}/outputs/${outputId}/preview-session`, {})
      .then(session => { if (alive) setUrl(`${session.url}?t=${Date.now()}`); }).catch(cause => { if (alive) setIssue(errorText(cause)); });
    return () => { alive = false; };
  }, [projectId, unitId, executionId, outputId]);
  return <div className="mt-3">
    <p className="mb-1 text-xs text-slate-600">封面</p>
    {url ? <img src={url} alt="封面" className="max-h-[50vh] w-auto rounded-lg border border-slate-200" /> : issue ? <p className="text-xs text-rose-700">{issue}</p> : <p className="text-xs text-slate-400">加载中…</p>}
  </div>;
}

// Only the cover goes back to the model; the cut itself keeps waiting for the user's answer.
function CoverRedo({ projectId, unitId, pending }: { projectId: number; unitId: number; pending?: { note: string } }) {
  const client = useQueryClient();
  const [open, setOpen] = useState(false);
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [issue, setIssue] = useState("");
  if (pending) return <p className="mt-2 text-xs text-amber-800">封面重做中{pending.note ? `：${pending.note}` : ""}。新封面交上来前，成片不能通过。</p>;
  async function send() {
    setBusy(true); setIssue("");
    try {
      await api.post(`/content-projects/${projectId}/units/${unitId}/video-chain/cover-redo`, { note: note.trim() });
      setOpen(false); setNote("");
      await client.invalidateQueries({ queryKey: ["video-chain"] });
    } catch (cause) { setIssue(errorText(cause)); } finally { setBusy(false); }
  }
  return <div className="mt-2 space-y-2">
    {!open ? <Button size="sm" variant="secondary" onClick={() => setOpen(true)}>重做封面</Button>
      : <div className="flex flex-wrap items-end gap-2">
        <input aria-label="封面备注" className={`${inputClass} min-w-[14rem] flex-1`} maxLength={2000} placeholder="要怎么改（可不写），例如：卖点字再大一点" value={note} onChange={event => setNote(event.target.value)} />
        <Button size="sm" disabled={busy} onClick={() => void send()}>{busy ? "提交中…" : "只重做封面"}</Button>
        <Button size="sm" variant="secondary" disabled={busy} onClick={() => setOpen(false)}>取消</Button>
      </div>}
    {issue && <p role="alert" className="text-xs text-rose-700">{issue}</p>}
  </div>;
}

// The video is made by the external model over MCP; this page only shows where it is and takes the user's answer.
// Each step page passes `step` and sees only its own stop; earlier stops are view-only.
export default function VideoChainPanel({ projectId, unitId, step, showDraft }: { projectId: number; unitId: number; step: Step; showDraft?: boolean }) {
  const client = useQueryClient();
  const navigate = useNavigate();
  const chain = useQuery({ queryKey: ["video-chain", currentUser(), projectId, unitId], retry: false,
    queryFn: () => api.get<Chain>(`/content-projects/${projectId}/units/${unitId}/video-chain`),
    refetchInterval: query => query.state.data?.state === "approving" ? 3000
      : ["making", "finishing", "draft_changes", "sample_changes", "final_changes", "not_started"].includes(query.state.data?.state || "") ? 15000 : false });
  const [notes, setNotes] = useState<Note[]>([]);
  const [time, setTime] = useState("");
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [issue, setIssue] = useState("");
  const [player, setPlayer] = useState<{ url: string; key: string; output: number } | null>(null);
  const data = chain.data;
  if (chain.isPending) return null;
  if (chain.error || !data) return <ErrorBanner message={errorText(chain.error)} />;
  // An approval being written belongs to the stop it was given at: the 小样 for a rough cut, else the 成片.
  const current = data.state === "approving" ? (data.phase === "rough_cut" ? 1 : 2) : STEPS.findIndex(([, states]) => (states as readonly string[]).includes(data.state));
  const here = ORDER.indexOf(step);
  const live = current === here;
  // Before the 成片 is final, the 导演稿 can be sent back from any later stop.
  const backToDraft = step === "draft" && current > 0 && !data.locked;
  const reviewing = live && (data.state.endsWith("_review") || data.state.endsWith("_changes")) || backToDraft;
  const timed = step !== "draft";
  // Once the 成片 task exists, the 小样 lives on as its own earlier task.
  const cut: Cut | null = step === "sample" ? data.sample || (data.phase === "rough_cut" && data.execution_id ? { execution_id: data.execution_id, cut_output_id: data.cut_output_id ?? null, cover_output_id: data.cover_output_id, shot_checks: data.shot_checks } : null)
    : step === "final" && data.phase === "final" && data.execution_id ? { execution_id: data.execution_id, cut_output_id: data.cut_output_id ?? null, cover_output_id: data.cover_output_id, shot_checks: data.shot_checks } : null;
  async function send(decision: "approve" | "changes") {
    const pending = text.trim() ? [...notes, { time_ms: timed && time ? Math.round(Number(time) * 1000) : null, note: text.trim() }] : notes;
    setBusy(true); setIssue("");
    try {
      await api.post(`/content-projects/${projectId}/units/${unitId}/video-chain/decision`, { stage: step, decision, notes: decision === "changes" ? pending : [] });
      setNotes([]); setText(""); setTime("");
      await client.invalidateQueries({ queryKey: ["video-chain"] });
    } catch (cause) { setIssue(errorText(cause)); }
    finally { setBusy(false); }
  }
  async function copy() {
    setBusy(true); setIssue("");
    try {
      const unit = await api.post<{ id: number }>(`/content-projects/${projectId}/units/${unitId}/copy`, {});
      navigate(`/projects/${projectId}/units/${unit.id}/production?workstep=plan`);
    } catch (cause) { setIssue(errorText(cause)); }
    finally { setBusy(false); }
  }
  async function play() {
    if (!cut?.cut_output_id) return;
    setIssue("");
    try {
      // A short-lived signed cookie lets the <video> element stream the file without exposing a token in the URL.
      const session = await api.post<{ url: string }>(`/content-projects/${projectId}/units/${unitId}/creative-executions/${cut.execution_id}/outputs/${cut.cut_output_id}/preview-session`, {});
      setPlayer({ url: session.url, key: `${cut.execution_id}:${Date.now()}`, output: cut.cut_output_id });
    } catch (cause) { setIssue(errorText(cause)); }
  }
  const status = live ? data.label : step === "draft" ? `导演稿${data.draft_revision_no ? ` v${data.draft_revision_no}` : ""} 已采用` : "小样已通过";
  const draft: VideoDraft | null = data.master ? { payloadSchema: "video.master.v2", payload: data.master.payload, assetRefs: [], evidenceRefs: [] } : null;
  return <div className="space-y-4">
    {step === "draft" && <PlatformSkillsSwitch projectId={projectId} unitId={unitId} readOnly={!!data.locked} />}
    <section aria-label="视频进度" className="rounded-xl border border-indigo-100 bg-indigo-50/60 p-4 text-sm">
      <div className="flex flex-wrap items-center gap-2 text-xs">{STEPS.map(([label], index) => <span key={label} className={`rounded-pill px-2.5 py-0.5 ${data.state === "done" || index < current ? "bg-emerald-100 text-emerald-800" : index === current ? "bg-indigo-600 text-white" : "bg-white text-slate-500"}`}>{index + 1} {label}</span>)}</div>
      <p className="mt-2"><span className="font-semibold">{status}</span>{live && data.draft_revision_no && step === "draft" ? ` · 导演稿 v${data.draft_revision_no}` : ""}{live && data.detail ? ` · ${data.detail}` : ""}</p>
      {live && data.notes?.length ? <ul className="mt-1 list-disc pl-5 text-xs text-slate-600">{data.notes.map((item, index) => <li key={index}>{item.time_ms != null ? `${(item.time_ms / 1000).toFixed(1)}s：` : ""}{item.note}</li>)}</ul> : null}
      {data.locked && step !== "final" && <p className="mt-2 text-xs text-slate-600">成片已完成，这一步只能看。</p>}
      {cut?.cut_output_id && <div className="mt-2">
        <Button size="sm" variant="secondary" onClick={() => void (player ? setPlayer(null) : play())}>{player ? "收起播放器" : step === "sample" ? "看小样" : "看成片"}</Button>
        {player && <div className="relative mt-3 w-fit max-w-full">
          <video key={player.key} src={player.url} controls autoPlay playsInline className="max-h-[75vh] w-auto max-w-full rounded-lg bg-black" onError={() => setIssue("播放链接已过期，点「收起播放器」后再点一次")} />
          <FileLocationActions base={`/content-projects/${projectId}/units/${unitId}/video-chain/cuts/${player.output}`} />
        </div>}
      </div>}
      {cut?.shot_checks && <ShotCheckList checks={cut.shot_checks} />}
      {cut?.cover_output_id && <CoverPreview projectId={projectId} unitId={unitId} executionId={cut.execution_id} outputId={cut.cover_output_id} />}
      {cut?.cover_output_id && live && data.state.endsWith("_review") && cut.execution_id === data.execution_id && <CoverRedo projectId={projectId} unitId={unitId} pending={data.cover_redo} />}
      {reviewing && <div className="mt-3 space-y-2">
        <div className="flex flex-wrap items-end gap-2">
          {timed && <input aria-label="时间（秒）" className={`${inputClass} !w-24`} inputMode="decimal" placeholder="秒" value={time} onChange={event => setTime(event.target.value)} />}
          <input aria-label="修改意见" className={`${inputClass} min-w-[14rem] flex-1`} maxLength={2000} placeholder={timed ? "这一秒要改什么" : "要改的地方，例如：第 3 镜换成实拍"} value={text} onChange={event => setText(event.target.value)} />
          <Button size="sm" variant="secondary" disabled={!text.trim()} onClick={() => { setNotes(current => [...current, { time_ms: timed && time ? Math.round(Number(time) * 1000) : null, note: text.trim() }]); setText(""); setTime(""); }}>再加一条</Button>
        </div>
        {notes.length > 0 && <ul className="list-disc pl-5 text-xs text-slate-600">{notes.map((item, index) => <li key={index}>{item.time_ms != null ? `${item.time_ms / 1000}s：` : ""}{item.note}</li>)}</ul>}
        <div className="flex flex-wrap gap-2">
          {!backToDraft && <Button disabled={busy || (step === "final" && !!data.cover_redo)} onClick={() => void send("approve")}>{busy && step !== "draft" ? "正在通过…" : step === "draft" ? "采用导演稿" : step === "sample" ? "小样通过，开始排版" : "成片通过"}</Button>}
          <Button variant="secondary" disabled={busy || (!notes.length && !text.trim())} onClick={() => void send("changes")}>{backToDraft ? "退回导演稿" : "按意见修改"}</Button>
        </div>
        <p className="text-xs text-slate-500">{backToDraft ? "画面内容要改就写在这里，流程会回到导演稿，后面的素材、小样按新导演稿重做。" : step === "draft" ? "有素材的话，先放进素材库（外部素材库或本项目）再采用。" : step === "final" ? "通过后前面的步骤会锁定。" : "意见会交给第三方模型改出下一版。"}回到第三方模型那边说一声「继续」，它会读到你的决定。</p>
      </div>}
      {step === "final" && data.locked && <div className="mt-3 flex flex-wrap items-center gap-3 rounded-lg bg-white/70 p-3 text-xs text-slate-600"><span>成片已定稿，这一条不能再改。要调整就复制一份，在副本里从导演稿开始。</span><Button size="sm" variant="secondary" disabled={busy} onClick={() => void copy()}>复制一份</Button></div>}
      {issue && <p role="alert" className="mt-2 text-xs text-rose-700">{issue}</p>}
    </section>
    {showDraft && draft && draft.payload.shots.some(shot => shot.board) && <Suspense fallback={null}><StoryboardTable projectId={projectId} unitId={unitId} draft={draft} readOnly paged onChange={() => {}} /></Suspense>}
    {showDraft && !!draft?.payload.consistency_groups?.length && <section aria-label="九宫格分组" className="rounded-xl border border-slate-200 bg-white p-4 text-sm">
      <h3 className="font-semibold">九宫格分组</h3>
      <p className="text-xs text-slate-500">这些镜头要保持同一个人物或同一个场景，导演稿采用后每组一起出一张九宫格；没分组的镜头各自单独生成。</p>
      <ul className="mt-2 space-y-1">{draft.payload.consistency_groups.map(group => <li key={group.id}>{group.id}：{group.shot_ids.map(id => `镜头 ${(draft.payload.shots.find(shot => shot.id === id)?.order ?? 0) + 1}`).join("、")}{group.setting ? ` · 场景：${group.setting}` : ""}{group.person ? ` · 人物：${group.person}` : ""}</li>)}</ul>
    </section>}
    {showDraft && <Suspense fallback={null}><ProductShotPanel projectId={projectId} unitId={unitId} payload={data.master?.payload || null} locked={!!data.locked} view="draft" /></Suspense>}
  </div>;
}
