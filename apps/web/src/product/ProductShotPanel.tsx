import { useQuery, useQueryClient } from "@tanstack/react-query";
import { lazy, Suspense, useState } from "react";
import { api, currentUser } from "../api";
import { Button, ErrorBanner, Field, inputClass } from "../components/ui";
import ShotWork, { errorText, NO_PORTRAIT_NOTE, type Copy, type Item, type View } from "./ShotWork";
import type { VideoPayload } from "./VideoStudioModel";

const StoryboardGridDialog = lazy(() => import("./StoryboardGridDialog"));
type Motion = { camera_presets?: string[]; look?: string; intensity?: "subtle" | "normal" | "strong"; chain_from_previous?: boolean };

const MODES: Record<string, string> = { photo_only: "一张图出整片", user_footage: "给素材剪", mixed: "混合补齐" };
const EMPTY: Copy = { channel: "", title: "", hashtags: [], cover_text: "", interaction: "", description: "" };

// Product works: per-shot camera / look / strength (view "draft") and the publish copy.
// Product and persona works (view "materials"): how each shot without the user's footage gets its clip; a consistency group of the 导演稿 is drawn in the storyboard-grid dialog.
export default function ProductShotPanel({ projectId, unitId, payload, locked, view, shotId }: { projectId: number; unitId: number; payload: VideoPayload | null; locked: boolean; view: "draft" | "materials"; shotId?: string }) {
  const client = useQueryClient();
  const base = `/content-projects/${projectId}/units/${unitId}/product-video`;
  const query = useQuery({ queryKey: ["product-video", currentUser(), projectId, unitId], queryFn: () => api.get<View>(base), retry: false,
    refetchInterval: value => value.state.data?.grid_run?.status === "running" ? 4000 : Object.values(value.state.data?.jobs || {}).some(job => job.state === "running") ? 20000 : false });
  const [busy, setBusy] = useState(false);
  const [issue, setIssue] = useState("");
  const [copy, setCopy] = useState<Copy | null>(null);
  const [openGroup, setOpenGroup] = useState<string | null>(null);
  const data = query.data;
  if (!data || !payload || !(data.product || data.persona && view === "materials")) return null;
  const persona = !data.product;
  const refresh = () => Promise.all([client.invalidateQueries({ queryKey: ["product-video"] }), client.invalidateQueries({ queryKey: ["video-chain"] })]);
  async function run(action: () => Promise<unknown>) {
    setBusy(true); setIssue("");
    try { await action(); await refresh(); } catch (error) { setIssue(errorText(error)); } finally { setBusy(false); }
  }
  const draftCopy = copy || data.publish_copy || EMPTY;
  const shots = [...payload.shots].sort((a, b) => a.order - b.order);
  const covered = (id: string) => { const used = data.used?.[id]; return !!used && !used.i2v; };
  const missing = shots.filter(shot => !data.used?.[shot.id]).length;
  const filled = shots.filter(shot => data.used?.[shot.id]?.i2v).length;
  const options = (items: Item[]) => [...new Set(items.map(item => item.group))].map(group =>
    <optgroup key={group} label={group}>{items.filter(item => item.group === group).map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</optgroup>);
  const groups = data.groups || [];
  const groupOf = (id: string) => groups.find(group => group.shot_ids.includes(id));
  const opened = groups.find(group => group.id === openGroup);
  const timing = data.resolution && `，现在按${data.resolution.phase === "final" ? "成片" : "小样"}档 ${data.resolution.current.toUpperCase()} 生成（小样 ${data.resolution.sample.toUpperCase()} / 成片 ${data.resolution.final.toUpperCase()}）`;
  return <section className="space-y-4 rounded-xl border border-slate-200 bg-white p-4">
    {persona ? <div><h3 className="font-semibold">补充镜头</h3><p className="text-sm text-slate-500">没有你素材的镜头：自动生成，或手动——拿文生视频提示词，或拿首帧和图生视频提示词，到网页工具生成后上传。默认{data.default_mode === "auto" ? "自动" : "手动"}{timing}。</p></div>
      : <div><h3 className="font-semibold">商品镜头</h3><p className="text-sm text-slate-500">{data.direction?.category?.name || "未选品类"} · {data.direction?.style?.name || "按品类推荐风格"} · {MODES[data.direction?.material_mode || "mixed"]} · 图生视频默认{data.default_mode === "auto" ? "自动" : "手动"}{timing}。改运镜会存成新一版导演稿。</p></div>}
    {view === "materials" && <p className="rounded-lg bg-slate-50 p-2 text-sm">共 {shots.length} 镜：{shots.length - missing - filled} 镜用你的素材{filled ? ` · ${filled} 镜已补` : ""} · <span className={missing ? "font-medium text-rose-700" : ""}>{missing} 镜缺画面</span>{missing ? (shotId ? "，下面是上面选中的这一镜。" : "，下面只列缺画面的镜头，选手动或自动生成。") : "，不用生成。"}</p>}
    {view === "materials" && persona && missing > 0 && data.references && !data.references.person.length && <p className="rounded-lg bg-amber-50 p-2 text-sm text-amber-800">{NO_PORTRAIT_NOTE}</p>}
    {issue && <ErrorBanner message={issue} />}
    <div className="space-y-3">{shots.map((shot, index) => {
      if (view === "materials" && shotId && shot.id !== shotId) return null;
      if (view === "materials" && covered(shot.id)) return shotId ? <p key={shot.id} className="text-sm text-slate-600">镜头 {index + 1} 已有素材，不用补。</p> : null;
      if (view === "materials") {
        const group = groupOf(shot.id);
        // Shots that must share a person or place are made together from one storyboard sheet, in the dialog.
        return group ? <article key={shot.id} className="flex flex-wrap items-center gap-2 rounded-lg border border-slate-100 p-3 text-sm">
          <span className="font-medium">镜头 {index + 1}</span><span className="min-w-0 flex-1 text-slate-500">{shot.board?.visual || shot.label}</span>
          <span className="rounded bg-indigo-50 px-1.5 text-xs text-indigo-700">九宫格组 {group.id}</span>
          <Button size="sm" variant="secondary" onClick={() => setOpenGroup(group.id)}>打开九宫格</Button>
        </article> : <ShotWork key={shot.id} shot={shot} label={`镜头 ${index + 1}`} data={data} base={base} busy={busy} locked={locked} run={action => void run(action)} onIssue={setIssue} />;
      }
      const board = (shot.board || {}) as Motion;
      const presets = board.camera_presets || [];
      const save = (value: Motion) => void run(() => api.put(`${base}/shots/${shot.id}/motion`, { camera_presets: presets, look: board.look ?? null, intensity: board.intensity ?? null, chain_from_previous: !!board.chain_from_previous, ...value }));
      return <article key={shot.id} className="rounded-lg border border-slate-100 p-3">
        <p className="text-sm font-medium">镜头 {index + 1}<span className="ml-2 font-normal text-slate-500">{shot.board?.visual || shot.label}</span></p>
        <div className="mt-2 grid gap-2 sm:grid-cols-5">
          {[0, 1].map(slot => <select key={slot} aria-label={`镜头 ${index + 1} 运镜 ${slot + 1}`} className={inputClass} value={presets[slot] || ""} disabled={busy || locked || !shot.board || (slot === 1 && !presets[0])}
            onChange={event => { const next = [...presets]; if (event.target.value) next[slot] = event.target.value; else next.splice(slot); save({ camera_presets: next.filter(Boolean) }); }}>
            <option value="">{slot === 0 ? "运镜：按品类" : "叠加第二个（可选）"}</option>{options(data.motion?.camera || [])}</select>)}
          <select aria-label={`镜头 ${index + 1} 光线`} className={inputClass} value={board.look || ""} disabled={busy || locked || !shot.board} onChange={event => save({ look: event.target.value || undefined })}>
            <option value="">光线：按品类</option>{options((data.motion?.looks || []).map(look => ({ ...look, group: look.group === "real" ? "机位质感" : "光线色调" })))}</select>
          <select aria-label={`镜头 ${index + 1} 强度`} className={inputClass} value={board.intensity || ""} disabled={busy || locked || !shot.board} onChange={event => save({ intensity: (event.target.value || undefined) as Motion["intensity"] })}>
            <option value="">强度：中</option><option value="subtle">轻</option><option value="normal">中</option><option value="strong">强</option></select>
          <label className="flex items-center gap-1 text-sm"><input type="checkbox" checked={!!board.chain_from_previous} disabled={busy || locked || !shot.board || index === 0} onChange={event => save({ chain_from_previous: event.target.checked })} />接上一镜</label>
        </div>
      </article>;
    })}</div>
    {view === "draft" && <div className="space-y-2 rounded-lg border border-slate-100 p-3"><h4 className="font-medium">发布文案</h4>
      <div className="grid gap-2 sm:grid-cols-2">
        <Field label="标题（≤15 字）"><input className={inputClass} maxLength={15} value={draftCopy.title} onChange={event => setCopy({ ...draftCopy, title: event.target.value })} /></Field>
        <Field label="封面字（≤8 字）"><input className={inputClass} maxLength={8} value={draftCopy.cover_text} onChange={event => setCopy({ ...draftCopy, cover_text: event.target.value })} /></Field>
        <Field label="话题（3–5 个，用空格分开）"><input className={inputClass} value={draftCopy.hashtags.join(" ")} onChange={event => setCopy({ ...draftCopy, hashtags: event.target.value.split(/\s+/).filter(Boolean).slice(0, 5) })} /></Field>
        <Field label="互动引导"><input className={inputClass} maxLength={60} value={draftCopy.interaction} onChange={event => setCopy({ ...draftCopy, interaction: event.target.value })} /></Field>
        <Field label="简介（≤50 字）"><input className={inputClass} maxLength={50} value={draftCopy.description} onChange={event => setCopy({ ...draftCopy, description: event.target.value })} /></Field>
      </div>
      {!data.publish_copy && !copy && <p className="text-xs text-slate-500">模型定稿前会写一版，你也可以先自己填。</p>}
      <Button size="sm" disabled={busy || !copy} onClick={() => void run(async () => { await api.put(`${base}/publish-copy`, draftCopy); setCopy(null); })}>保存发布文案</Button>
    </div>}
    {opened && <Suspense fallback={null}><StoryboardGridDialog projectId={projectId} unitId={unitId} group={opened} shots={shots} data={data} locked={locked} onClose={() => setOpenGroup(null)} /></Suspense>}
  </section>;
}
