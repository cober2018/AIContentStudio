import { useQuery, useQueryClient } from "@tanstack/react-query";
import { lazy, Suspense, useState } from "react";
import { api, ApiError, currentUser } from "../api";
import { Button, ErrorBanner, inputClass } from "../components/ui";
import FileLocationActions from "./FileLocationActions";
import type { VideoDraft, VideoPayload } from "./VideoStudioModel";

const StoryboardTable = lazy(() => import("./StoryboardTable"));

type Note = { time_ms: number | null; note: string };
type Chain = {
  state: string; label: string; detail?: string; notes?: Note[]; execution_id?: number; cut_output_id?: number | null; draft_revision_no?: number;
  master: { id: number; revision_no: number; payload: VideoPayload } | null;
};
const STEPS = [["导演稿", ["draft_review", "draft_changes"]], ["小样", ["making", "sample_review", "sample_changes"]], ["成片", ["finishing", "final_review", "final_changes", "done"]]] as const;

function errorText(error: unknown) {
  const detail = error instanceof ApiError ? error.detail as { message?: string } | undefined : undefined;
  return detail?.message || (error instanceof Error ? error.message : "操作失败");
}

// The video is made by the external model over MCP; this page only shows where it is and takes the user's answer.
export default function VideoChainPanel({ projectId, unitId, showDraft }: { projectId: number; unitId: number; showDraft?: boolean }) {
  const client = useQueryClient();
  const chain = useQuery({ queryKey: ["video-chain", currentUser(), projectId, unitId], retry: false,
    queryFn: () => api.get<Chain>(`/content-projects/${projectId}/units/${unitId}/video-chain`),
    refetchInterval: query => ["making", "finishing", "draft_changes", "sample_changes", "final_changes", "not_started"].includes(query.state.data?.state || "") ? 15000 : false });
  const [notes, setNotes] = useState<Note[]>([]);
  const [time, setTime] = useState("");
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [issue, setIssue] = useState("");
  const [player, setPlayer] = useState<{ url: string; key: string } | null>(null);
  const data = chain.data;
  if (chain.isPending) return null;
  if (chain.error || !data) return <ErrorBanner message={errorText(chain.error)} />;
  const stage = data.state.startsWith("draft") ? "draft" : data.state.startsWith("sample") ? "sample" : data.state.startsWith("final") ? "final" : null;
  const reviewing = data.state.endsWith("_review") || data.state.endsWith("_changes");
  const timed = stage !== "draft";
  async function send(decision: "approve" | "changes") {
    const pending = text.trim() ? [...notes, { time_ms: timed && time ? Math.round(Number(time) * 1000) : null, note: text.trim() }] : notes;
    setBusy(true); setIssue("");
    try {
      await api.post(`/content-projects/${projectId}/units/${unitId}/video-chain/decision`, { stage, decision, notes: decision === "changes" ? pending : [] });
      setNotes([]); setText(""); setTime("");
      await client.invalidateQueries({ queryKey: ["video-chain"] });
    } catch (cause) { setIssue(errorText(cause)); }
    finally { setBusy(false); }
  }
  async function play() {
    if (!data?.execution_id || !data.cut_output_id) return;
    setIssue("");
    try {
      // A short-lived signed cookie lets the <video> element stream the file without exposing a token in the URL.
      const session = await api.post<{ url: string }>(`/content-projects/${projectId}/units/${unitId}/creative-executions/${data.execution_id}/outputs/${data.cut_output_id}/preview-session`, {});
      setPlayer({ url: session.url, key: `${data.execution_id}:${Date.now()}` });
    } catch (cause) { setIssue(errorText(cause)); }
  }
  const current = STEPS.findIndex(([, states]) => (states as readonly string[]).includes(data.state));
  const draft: VideoDraft | null = data.master ? { payloadSchema: "video.master.v2", payload: data.master.payload, assetRefs: [], evidenceRefs: [] } : null;
  return <div className="space-y-4">
    <section aria-label="视频进度" className="rounded-xl border border-indigo-100 bg-indigo-50/60 p-4 text-sm">
      <div className="flex flex-wrap items-center gap-2 text-xs">{STEPS.map(([label], index) => <span key={label} className={`rounded-pill px-2.5 py-0.5 ${data.state === "done" || index < current ? "bg-emerald-100 text-emerald-800" : index === current ? "bg-indigo-600 text-white" : "bg-white text-slate-500"}`}>{index + 1} {label}</span>)}</div>
      <p className="mt-2"><span className="font-semibold">{data.label}</span>{data.draft_revision_no ? ` · 导演稿 v${data.draft_revision_no}` : ""}{data.detail ? ` · ${data.detail}` : ""}</p>
      {data.notes?.length ? <ul className="mt-1 list-disc pl-5 text-xs text-slate-600">{data.notes.map((item, index) => <li key={index}>{item.time_ms != null ? `${(item.time_ms / 1000).toFixed(1)}s：` : ""}{item.note}</li>)}</ul> : null}
      {data.execution_id && data.cut_output_id && (stage === "sample" || stage === "final" || data.state === "done") && <div className="mt-2">
        <Button size="sm" variant="secondary" onClick={() => void (player ? setPlayer(null) : play())}>{player ? "收起播放器" : stage === "sample" ? "看小样" : "看成片"}</Button>
        {player && <div className="relative mt-3 w-fit max-w-full">
          <video key={player.key} src={player.url} controls autoPlay playsInline className="max-h-[75vh] w-auto max-w-full rounded-lg bg-black" onError={() => setIssue("播放链接已过期，点「收起播放器」后再点一次")} />
          <FileLocationActions base={`/content-projects/${projectId}/units/${unitId}/video-chain/cuts/${data.cut_output_id}`} />
        </div>}
      </div>}
      {reviewing && stage && <div className="mt-3 space-y-2">
        <div className="flex flex-wrap items-end gap-2">
          {timed && <input aria-label="时间（秒）" className={`${inputClass} !w-24`} inputMode="decimal" placeholder="秒" value={time} onChange={event => setTime(event.target.value)} />}
          <input aria-label="修改意见" className={`${inputClass} min-w-[14rem] flex-1`} maxLength={2000} placeholder={timed ? "这一秒要改什么" : "要改的地方，例如：第 3 镜换成实拍"} value={text} onChange={event => setText(event.target.value)} />
          <Button size="sm" variant="secondary" disabled={!text.trim()} onClick={() => { setNotes(current => [...current, { time_ms: timed && time ? Math.round(Number(time) * 1000) : null, note: text.trim() }]); setText(""); setTime(""); }}>再加一条</Button>
        </div>
        {notes.length > 0 && <ul className="list-disc pl-5 text-xs text-slate-600">{notes.map((item, index) => <li key={index}>{item.time_ms != null ? `${item.time_ms / 1000}s：` : ""}{item.note}</li>)}</ul>}
        <div className="flex flex-wrap gap-2">
          <Button disabled={busy} onClick={() => void send("approve")}>{stage === "draft" ? "采用导演稿" : stage === "sample" ? "小样通过，开始排版" : "成片通过"}</Button>
          <Button variant="secondary" disabled={busy || (!notes.length && !text.trim())} onClick={() => void send("changes")}>按意见修改</Button>
        </div>
        <p className="text-xs text-slate-500">{stage === "draft" ? "有素材的话，先放进素材库（外部素材库或本项目）再采用。" : "意见会交给 Claude Code 改出下一版。"}回到 Claude Code 说一声「继续」，它会读到你的决定。</p>
      </div>}
      {issue && <p role="alert" className="mt-2 text-xs text-rose-700">{issue}</p>}
    </section>
    {showDraft && draft && draft.payload.shots.some(shot => shot.board) && <Suspense fallback={null}><StoryboardTable projectId={projectId} unitId={unitId} draft={draft} readOnly onChange={() => {}} /></Suspense>}
  </div>;
}
