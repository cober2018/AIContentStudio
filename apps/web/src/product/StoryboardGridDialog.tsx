import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { api, currentUser } from "../api";
import { Button, FloatingAlert, Modal } from "../components/ui";
import ShotWork, { errorText, NO_PORTRAIT_NOTE, type View } from "./ShotWork";
import type { ConsistencyGroup, VideoShot } from "./VideoStudioModel";

const ORIGIN: Record<string, string> = { manual: "共同视觉参考里选的", sku_primary_image: "商品主图", persona_portrait: "角色形象照" };

function Picture({ path, alt }: { path: string; alt: string }) {
  const [url, setUrl] = useState("");
  useEffect(() => {
    let objectUrl = "";
    let alive = true;
    fetch(path, { headers: { "X-Studio-User": currentUser() } }).then(async response => {
      if (!response.ok) return;
      objectUrl = URL.createObjectURL(await response.blob());
      if (alive) setUrl(objectUrl);
    }).catch(() => {});
    return () => { alive = false; if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [path]);
  return url ? <a href={url} target="_blank" rel="noreferrer"><img src={url} alt={alt} className="h-72 w-auto rounded border border-slate-200" /></a> : <div className="h-72 w-40 rounded bg-slate-100" />;
}

// One consistency group of the 导演稿: one storyboard sheet keeps its people and place the same, then each shot is finished here.
export default function StoryboardGridDialog({ projectId, unitId, group, shots, data, locked, onClose }: {
  projectId: number; unitId: number; group: ConsistencyGroup; shots: VideoShot[]; data: View; locked: boolean; onClose: () => void;
}) {
  const client = useQueryClient();
  const base = `/content-projects/${projectId}/units/${unitId}/product-video`;
  const [busy, setBusy] = useState(false);
  const [issue, setIssue] = useState("");
  const [notice, setNotice] = useState("");
  const persona = !data.product;
  const members = shots.filter(shot => group.shot_ids.includes(shot.id));
  const refs = data.references;
  const run = data.grid_run;
  const running = run?.status === "running";
  const sheets = [...new Set([...members.map(shot => data.grid_sheets?.[shot.id]).filter((name): name is string => !!name),
    ...(run?.group_id === group.id ? run.sheets || [] : [])])];
  const notices = members.filter(shot => data.person_notices?.[shot.id]);
  function act(action: () => Promise<unknown>, done = "") {
    setBusy(true); setIssue("");
    void (async () => {
      try { await action(); await Promise.all([client.invalidateQueries({ queryKey: ["product-video"] }), client.invalidateQueries({ queryKey: ["video-chain"] })]); if (done) setNotice(done); }
      catch (cause) { setIssue(errorText(cause)); }
      finally { setBusy(false); }
    })();
  }
  return <Modal title={`九宫格分镜 · ${group.id}`} wide onClose={onClose}>
    <div className="space-y-3 text-sm">
      <p className="text-xs text-slate-500">这一组镜头要保持同一个人物或同一个场景：一次画在一张图里，再裁成每镜的首帧候选。{persona ? "" : "每格对照商品主图检查，不过关只重画那一格。"}按次计费。</p>
      <p className="text-xs text-slate-600">镜头：{members.map(shot => `镜头 ${shot.order + 1}`).join("、")}{group.setting ? ` · 场景：${group.setting}` : ""}{group.person ? ` · 人物：${group.person}` : ""}</p>
      {refs && <p className="text-xs text-slate-600">参考：{persona ? "" : `商品 ${refs.product.length ? `${ORIGIN[refs.origin.product] || "已选"}${refs.main_image ? `（第 ${refs.main_image.revision} 版${refs.main_image.followed_latest ? "，已跟随商品最新主图" : ""}）` : ""}` : "没有（不检查商品）"}；`}人物 {refs.person.length ? `${ORIGIN[refs.origin.person] || "已选"} ${refs.person.length} 张` : "没有形象照，生成画面里不出现人物"}{refs.scene.length ? `；场景 ${refs.scene.length} 张` : ""}</p>}
      {persona && refs && !refs.person.length && <p className="rounded-lg bg-amber-50 p-2 text-xs text-amber-800">{NO_PORTRAIT_NOTE}</p>}
      {!persona && notices.length > 0 && <ul className="space-y-1 rounded-lg bg-amber-50 p-2 text-xs text-amber-800">{notices.map(shot => <li key={shot.id}>镜头 {shot.order + 1}：{data.person_notices?.[shot.id]}。可以改成商品 / 场景镜头，或先给角色补形象照。</li>)}</ul>}
      <div className="flex flex-wrap items-center gap-2">
        <Button size="sm" disabled={locked || busy || running} onClick={() => { if (window.confirm("生成九宫格分镜会调用生图模型，按次计费。继续？")) act(() => api.post(`${base}/storyboard-grid`, { group_id: group.id }), "开始生成了，约 2–4 分钟，好了这里会自动更新"); }}>{running ? "生成中…" : sheets.length ? "重新生成九宫格" : "生成九宫格"}</Button>
        {running && run?.group_id && run.group_id !== group.id && <span className="text-xs text-slate-500">分组 {run.group_id} 正在生成，好了再点这一组</span>}
      </div>
      {running && run?.group_id === group.id && <p className="rounded-lg bg-indigo-50 p-2 text-xs text-indigo-800">正在生成九宫格：先画整张分镜图，再裁成每镜的候选{persona ? "" : "，逐格对照商品主图检查，不过关的格子会单独重画"}。约 2–4 分钟，页面会自动更新。</p>}
      {run?.status === "failed" && run.group_id === group.id && <p className="rounded-lg bg-rose-50 p-2 text-xs text-rose-800">上次生成失败：{run.error || "原因未知"}{run.sheets?.length ? "。整张分镜图已保留在下面。" : ""}</p>}
      {sheets.length > 0 && <div><p className="text-xs font-medium text-slate-600">整张分镜图（点开看大图；每镜的候选就是从这里按格裁出来的）</p>
        <div className="mt-2 flex flex-wrap gap-3">{sheets.map(name => <Picture key={name} path={`/api/v1${base}/storyboard-grid/sheets/${encodeURIComponent(name)}`} alt={`九宫格分镜 ${name}`} />)}</div></div>}
      <div className="space-y-3">{members.map(shot => <ShotWork key={shot.id} shot={shot} label={`镜头 ${shot.order + 1}`} data={data} base={base} busy={busy} locked={locked}
        run={action => act(action)} onIssue={setIssue} grid />)}</div>
    </div>
    {issue && <FloatingAlert message={issue} onClose={() => setIssue("")} />}
    {notice && <FloatingAlert tone="info" message={notice} onClose={() => setNotice("")} />}
  </Modal>;
}
