import { useQuery, useQueryClient } from "@tanstack/react-query";
import { lazy, Suspense, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, ApiError, currentUser } from "../api";
import { Button, ErrorBanner, inputClass } from "../components/ui";
import FileLocationActions from "./FileLocationActions";
import { PlatformSkillsSwitch } from "./ArticleChainPanel";
import type { VideoDraft, VideoPayload } from "./VideoStudioModel";

const StoryboardTable = lazy(() => import("./StoryboardTable"));

type Note = { time_ms: number | null; note: string };
type Cut = { execution_id: number; cut_output_id: number | null };
type Chain = {
  state: string; label: string; detail?: string; notes?: Note[]; execution_id?: number; cut_output_id?: number | null; draft_revision_no?: number;
  phase?: string; locked?: boolean; sample?: Cut;
  master: { id: number; revision_no: number; payload: VideoPayload } | null;
};
type Step = "draft" | "sample" | "final";
const STEPS = [["导演稿", ["draft_review", "draft_changes"]], ["小样", ["making", "sample_review", "sample_changes"]], ["成片", ["finishing", "final_review", "final_changes", "done"]]] as const;
const ORDER: Step[] = ["draft", "sample", "final"];

function errorText(error: unknown) {
  const detail = error instanceof ApiError ? error.detail as { message?: string } | undefined : undefined;
  return detail?.message || (error instanceof Error ? error.message : "操作失败");
}

// The video is made by the external model over MCP; this page only shows where it is and takes the user's answer.
// Each step page passes `step` and sees only its own stop; earlier stops are view-only.
export default function VideoChainPanel({ projectId, unitId, step, showDraft }: { projectId: number; unitId: number; step: Step; showDraft?: boolean }) {
  const client = useQueryClient();
  const navigate = useNavigate();
  const chain = useQuery({ queryKey: ["video-chain", currentUser(), projectId, unitId], retry: false,
    queryFn: () => api.get<Chain>(`/content-projects/${projectId}/units/${unitId}/video-chain`),
    refetchInterval: query => ["making", "finishing", "draft_changes", "sample_changes", "final_changes", "not_started"].includes(query.state.data?.state || "") ? 15000 : false });
  const [notes, setNotes] = useState<Note[]>([]);
  const [time, setTime] = useState("");
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [issue, setIssue] = useState("");
  const [player, setPlayer] = useState<{ url: string; key: string; output: number } | null>(null);
  const data = chain.data;
  if (chain.isPending) return null;
  if (chain.error || !data) return <ErrorBanner message={errorText(chain.error)} />;
  const current = STEPS.findIndex(([, states]) => (states as readonly string[]).includes(data.state));
  const here = ORDER.indexOf(step);
  const live = current === here;
  // Before the 成片 is final, the 导演稿 can be sent back from any later stop.
  const backToDraft = step === "draft" && current > 0 && !data.locked;
  const reviewing = live && (data.state.endsWith("_review") || data.state.endsWith("_changes")) || backToDraft;
  const timed = step !== "draft";
  // Once the 成片 task exists, the 小样 lives on as its own earlier task.
  const cut: Cut | null = step === "sample" ? data.sample || (data.phase === "rough_cut" && data.execution_id ? { execution_id: data.execution_id, cut_output_id: data.cut_output_id ?? null } : null)
    : step === "final" && data.phase === "final" && data.execution_id ? { execution_id: data.execution_id, cut_output_id: data.cut_output_id ?? null } : null;
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
      {reviewing && <div className="mt-3 space-y-2">
        <div className="flex flex-wrap items-end gap-2">
          {timed && <input aria-label="时间（秒）" className={`${inputClass} !w-24`} inputMode="decimal" placeholder="秒" value={time} onChange={event => setTime(event.target.value)} />}
          <input aria-label="修改意见" className={`${inputClass} min-w-[14rem] flex-1`} maxLength={2000} placeholder={timed ? "这一秒要改什么" : "要改的地方，例如：第 3 镜换成实拍"} value={text} onChange={event => setText(event.target.value)} />
          <Button size="sm" variant="secondary" disabled={!text.trim()} onClick={() => { setNotes(current => [...current, { time_ms: timed && time ? Math.round(Number(time) * 1000) : null, note: text.trim() }]); setText(""); setTime(""); }}>再加一条</Button>
        </div>
        {notes.length > 0 && <ul className="list-disc pl-5 text-xs text-slate-600">{notes.map((item, index) => <li key={index}>{item.time_ms != null ? `${item.time_ms / 1000}s：` : ""}{item.note}</li>)}</ul>}
        <div className="flex flex-wrap gap-2">
          {!backToDraft && <Button disabled={busy} onClick={() => void send("approve")}>{step === "draft" ? "采用导演稿" : step === "sample" ? "小样通过，开始排版" : "成片通过"}</Button>}
          <Button variant="secondary" disabled={busy || (!notes.length && !text.trim())} onClick={() => void send("changes")}>{backToDraft ? "退回导演稿" : "按意见修改"}</Button>
        </div>
        <p className="text-xs text-slate-500">{backToDraft ? "画面内容要改就写在这里，流程会回到导演稿，后面的素材、小样按新导演稿重做。" : step === "draft" ? "有素材的话，先放进素材库（外部素材库或本项目）再采用。" : step === "final" ? "通过后前面的步骤会锁定。" : "意见会交给第三方模型改出下一版。"}回到第三方模型那边说一声「继续」，它会读到你的决定。</p>
      </div>}
      {step === "final" && data.locked && <div className="mt-3 flex flex-wrap items-center gap-3 rounded-lg bg-white/70 p-3 text-xs text-slate-600"><span>成片已定稿，这一条不能再改。要调整就复制一份，在副本里从导演稿开始。</span><Button size="sm" variant="secondary" disabled={busy} onClick={() => void copy()}>复制一份</Button></div>}
      {issue && <p role="alert" className="mt-2 text-xs text-rose-700">{issue}</p>}
    </section>
    {showDraft && draft && draft.payload.shots.some(shot => shot.board) && <Suspense fallback={null}><StoryboardTable projectId={projectId} unitId={unitId} draft={draft} readOnly paged onChange={() => {}} /></Suspense>}
  </div>;
}
