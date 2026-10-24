import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api, currentUser } from "../api";
import type { HandoffStatus } from "./editHandoff";
import { Button } from "../components/ui";
import { stageErrorText } from "./stageErrors";
import { useShotSlots, type Slot } from "./shotSlots";
import { MATERIAL_DRAG, type DraggedMaterial } from "./MaterialLibraryFloat";
import { updateScriptBlock, updateShotBoard, type VideoBoard, type VideoDraft } from "./VideoStudioModel";

const cameras: [VideoBoard["camera"], string][] = [["fixed", "固定"], ["push_in", "推近"], ["pull_out", "拉远"], ["follow", "跟拍"], ["orbit", "环绕"], ["pan", "横移"]];
const speakers: [VideoBoard["speaker"], string][] = [["narration", "旁白"], ["presenter", "口播"], ["dialogue", "对白"], ["none", "无台词"]];
function materialText(slot: Slot | undefined, bound?: number) {
  if (bound) return <span className="text-emerald-700">已绑定 #{bound}</span>;
  const pick = slot?.picks[slot.picks.length - 1];
  if (pick?.auto) return <span className="text-emerald-700" title={pick.auto.reason || ""}>自动 · {pick.auto.source === "stock" ? `${pick.provider_label || "素材站"}${pick.auto.score != null ? ` ${pick.auto.score.toFixed(2)}` : ""}` : pick.provider_label}</span>;
  if (slot?.picks.length === 1) return <span className="text-emerald-700">已选 1 个</span>;
  if (slot?.picks.length) return <span className="text-amber-700">待你选（{slot.picks.length} 个候选）</span>;
  if (slot?.autofill?.outcome === "gap") return <span className="text-rose-700">缺口：{slot.autofill.reason}</span>;
  if (slot?.candidate_count) return <span className="text-amber-700">有候选</span>;
  return <span className="text-slate-400">待补</span>;
}

const cell = "w-full resize-y rounded border border-transparent bg-transparent p-1 text-[13px] leading-snug hover:border-slate-200 focus:border-sky-400 focus:outline-none disabled:resize-none";

function clock(ms: number) {
  const seconds = Math.round(ms / 100) / 10;
  return `${String(Math.floor(seconds / 60)).padStart(2, "0")}:${(seconds % 60).toFixed(1).padStart(4, "0")}`;
}

export default function StoryboardTable({ projectId, unitId, draft, readOnly, paged, onChange }: {
  projectId: number; unitId?: number; draft: VideoDraft; readOnly: boolean; paged?: boolean; onChange: (draft: VideoDraft) => void;
}) {
  const slots = useShotSlots(projectId, unitId || 0);
  const handoff = useQuery({ queryKey: ["edit-handoff", currentUser(), projectId, unitId], enabled: !!unitId && !readOnly, retry: false,
    queryFn: () => api.get<HandoffStatus>(`/content-projects/${projectId}/units/${unitId}/edit-handoff`) });
  const route = (shotId: string) => {
    const decided = draft.payload.postproduction ? draft.payload.postproduction.ae_shot_ids : handoff.data?.decided ? handoff.data.ae_shot_ids : null;
    if (!decided) return null;
    const reason = handoff.data?.ae[shotId];
    return decided.includes(shotId) ? <span className="mt-1 block text-[11px] text-indigo-700" title={reason || ""}>后期：达芬奇 + AE{reason ? `（${reason}）` : ""}</span> : <span className="mt-1 block text-[11px] text-slate-500">后期：达芬奇</span>;
  };
  const [fillIssue, setFillIssue] = useState("");
  const [dropTarget, setDropTarget] = useState("");
  const [index, setIndex] = useState(0);
  const shots = [...draft.payload.shots].sort((a, b) => a.order - b.order);
  if (!shots.some(shot => shot.board)) return null;
  const blocks = new Map(draft.payload.script.blocks.map(block => [block.id, block]));
  const slotById = new Map((unitId ? slots.data?.shots || [] : []).map(slot => [slot.id, slot]));
  const total = shots.reduce((sum, shot) => sum + shot.duration_ms, 0);
  // A material dropped from the floating library becomes this shot's pick, same as choosing it in the slot.
  async function dropMaterial(shotId: string, raw: string) {
    setDropTarget(""); setFillIssue("");
    try {
      const item = JSON.parse(raw) as DraggedMaterial;
      const target = await api.post<{ run_id: number; segment_id: string }>(`/content-projects/${projectId}/units/${unitId}/shot-slots/${encodeURIComponent(shotId)}/upload-target`);
      await api.post(`/material-match-runs/${target.run_id}/segments/${encodeURIComponent(target.segment_id)}/attach`, { material_revision_id: item.material_revision_id });
      await slots.refetch();
    } catch (cause) { setFillIssue(stageErrorText(cause, "素材没能放进这个镜头，请刷新后重试。")); }
  }
  function edit(next: () => VideoDraft) { try { onChange(next()); } catch { /* The field keeps its last valid value. */ } }
  if (paged) {
    // Review mode: one shot per page, like flipping a storyboard, instead of a wide table to scroll through.
    const at = Math.min(index, shots.length - 1);
    const shot = shots[at];
    const start = shots.slice(0, at).reduce((sum, item) => sum + item.duration_ms, 0);
    const board = shot.board;
    const block = shot.script_block_id ? blocks.get(shot.script_block_id) : undefined;
    const rows: [string, string | undefined][] = [["信息点", board?.message], ["画面", board?.visual || shot.label], ["运镜", cameras.find(([value]) => value === board?.camera)?.[1]],
      [speakers.find(([value]) => value === board?.speaker)?.[1] || "台词", block?.text], ["声音", board?.sound], ["备注", board?.notes], ["素材需求", board?.material_request]];
    return <section aria-label="分镜表" className="rounded-xl border border-slate-200 bg-white p-4">
      <div className="flex flex-wrap items-baseline justify-between gap-2"><h3 className="font-semibold">分镜 · 镜头 {at + 1} / {shots.length}</h3><p className="text-xs text-slate-500">估计总长 {clock(total)} · 时长是估计，最终以配音为准</p></div>
      <div className="mt-3 flex flex-wrap gap-1">{shots.map((item, position) => <button key={item.id} type="button" aria-current={position === at ? "step" : undefined} onClick={() => setIndex(position)} className={`h-7 min-w-[2.25rem] rounded-md px-1.5 text-xs tabular-nums ${position === at ? "bg-ink-900 text-paper" : "border border-slate-200 text-slate-600 hover:bg-slate-50"}`}>L{String(item.order + 1).padStart(2, "0")}</button>)}</div>
      <div className="mt-4 rounded-lg bg-slate-50 p-4">
        <p className="text-xs text-slate-500">{clock(start)}–{clock(start + shot.duration_ms)}</p>
        <dl className="mt-2 grid gap-x-4 gap-y-2 text-sm sm:grid-cols-[6rem_1fr]">{rows.filter(([, value]) => value).map(([label, value]) => <div key={label} className="contents"><dt className="text-xs text-slate-500 sm:pt-0.5">{label}</dt><dd className={`whitespace-pre-wrap ${label === "素材需求" ? "text-amber-800" : "text-slate-800"}`}>{value}</dd></div>)}</dl>
        <p className="mt-3 text-xs">{materialText(slotById.get(shot.id), shot.source_material_revision_id)}</p>{route(shot.id)}
      </div>
      <div className="mt-3 flex justify-between"><Button size="sm" variant="secondary" disabled={at === 0} onClick={() => setIndex(at - 1)}>上一镜</Button><Button size="sm" variant="secondary" disabled={at === shots.length - 1} onClick={() => setIndex(at + 1)}>下一镜</Button></div>
    </section>;
  }
  let cursor = 0;
  return <section aria-label="分镜表" className="rounded-xl border border-slate-200 p-4">
    <div className="flex flex-wrap items-baseline justify-between gap-2"><h3 className="font-semibold">分镜表</h3><div className="flex flex-wrap items-center gap-3"><p className="text-xs text-slate-500">{shots.length} 个镜头 · 估计总长 {clock(total)} · 时长是估计，最终以配音为准</p></div></div>
    {fillIssue && <p role="alert" className="mt-2 text-xs text-rose-700">{fillIssue}</p>}
    <p className="mt-1 text-xs text-slate-500">「素材需求」写的是每个镜头要什么画面。你有的素材放进素材库或拖到素材格；剩下的由第三方模型去找或做，每个镜头最后用哪条也由它定。</p>
    <div className="mt-3 overflow-x-auto"><table className="w-full min-w-[1100px] border-collapse text-left align-top">
      <thead><tr className="border-b border-slate-200 text-xs text-slate-500">{["镜头", "时长", "信息点", "画面", "运镜", "台词", "声音", "备注", "素材需求 / 素材"].map(label => <th key={label} className="px-1 py-2 font-medium">{label}</th>)}</tr></thead>
      <tbody>{shots.map(shot => {
        const start = cursor; cursor += shot.duration_ms;
        const board: VideoBoard = shot.board || { message: shot.purpose || "", visual: shot.label, camera: "fixed", speaker: shot.script_block_id ? "narration" : "none", sound: "", notes: "" };
        const block = shot.script_block_id ? blocks.get(shot.script_block_id) : undefined;
        const slot = slotById.get(shot.id);
        const locked = readOnly || !shot.board;
        const text = (key: "message" | "visual" | "sound" | "notes", rows = 2) => <textarea aria-label={`L${shot.order + 1} ${key}`} rows={rows} className={cell} disabled={locked} value={board[key]} onChange={event => edit(() => updateShotBoard(draft, shot.id, { [key]: event.target.value }))} />;
        return <tr key={shot.id} className="border-b border-slate-100 align-top">
          <td className="px-1 py-2 text-[13px] font-semibold">L{String(shot.order + 1).padStart(2, "0")}</td>
          <td className="whitespace-nowrap px-1 py-2 text-xs text-slate-600">{clock(start)}–{clock(start + shot.duration_ms)}</td>
          <td className="w-[13%] px-1 py-1">{text("message")}</td>
          <td className="w-[20%] px-1 py-1">{text("visual", 3)}</td>
          <td className="px-1 py-1"><select aria-label={`L${shot.order + 1} 运镜`} className={cell} disabled={locked} value={board.camera} onChange={event => edit(() => updateShotBoard(draft, shot.id, { camera: event.target.value as VideoBoard["camera"] }))}>{cameras.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></td>
          <td className="w-[20%] px-1 py-1"><span className="text-[11px] text-slate-500">{speakers.find(([value]) => value === board.speaker)?.[1]}</span>{block && <textarea aria-label={`L${shot.order + 1} 台词`} rows={3} className={cell} disabled={readOnly} value={block.text} onChange={event => edit(() => updateScriptBlock(draft, block.id, event.target.value))} />}</td>
          <td className="w-[12%] px-1 py-1">{text("sound")}</td>
          <td className="w-[12%] px-1 py-1">{text("notes")}</td>
          <td className={`max-w-[10rem] px-1 py-2 text-xs ${dropTarget === shot.id ? "rounded bg-sky-50 outline outline-2 outline-sky-400" : ""}`}
            onDragOver={unitId ? event => { if (event.dataTransfer.types.includes(MATERIAL_DRAG)) { event.preventDefault(); setDropTarget(shot.id); } } : undefined}
            onDragLeave={() => setDropTarget(current => current === shot.id ? "" : current)}
            onDrop={unitId ? event => { const raw = event.dataTransfer.getData(MATERIAL_DRAG); if (raw) { event.preventDefault(); void dropMaterial(shot.id, raw); } } : undefined}>{board.material_request && <span className="mb-1 block whitespace-pre-wrap text-[11.5px] text-amber-800">需求：{board.material_request}</span>}{materialText(slot, shot.source_material_revision_id)}{route(shot.id)}{unitId && !readOnly && <span className="mt-1 block text-[11px] text-slate-400">拖素材到这里</span>}</td>
        </tr>;
      })}</tbody>
    </table></div>
  </section>;
}
