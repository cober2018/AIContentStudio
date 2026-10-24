import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, currentUser } from "../api";
import { Button, Chip, EmptyState, ErrorBanner, Field, Segmented, Spinner, inputClass } from "../components/ui";
import { readableTime } from "./HomePage";
import { MatchRun, RunStatus, SegmentResult, errorText, ownerLabel, ownerLink, useMatchRun } from "./MaterialMatchView";

type Provider = { key: string; label: string; media_types: string[]; configured: boolean };
type RunSummary = Omit<MatchRun, "segments"> & { segment_count: number; gap_count: number };
const ASPECTS = [["9:16", "竖屏 9:16"], ["3:4", "3:4"], ["1:1", "1:1"], ["16:9", "横屏 16:9"]] as const;

type MasterText = { payload: { document?: { blocks: { content?: { text: string }[]; items?: { content: { text: string }[] }[] }[] };
  canvases?: { layers: { type: string; runs?: { text: string }[] }[] }[]; script?: { blocks: { text: string }[] } } };

// The piece's own words are the natural script to search with; each modality keeps them in a different shape.
function pieceText(master: MasterText) {
  const payload = master.payload;
  if (payload.document) return payload.document.blocks.map(block => block.content ? block.content.map(run => run.text).join("") : (block.items ?? []).map(item => item.content.map(run => run.text).join("")).join("\n")).filter(Boolean).join("\n\n");
  if (payload.canvases) return payload.canvases.map(canvas => canvas.layers.filter(layer => layer.type === "text").map(layer => (layer.runs ?? []).map(run => run.text).join("")).join("\n")).join("\n\n");
  return (payload.script?.blocks ?? []).map(block => block.text).join("\n\n");
}

export default function MaterialScriptMatch({ runId, openRun, projectId, unitId, scopeTo }: {
  runId: number | null; openRun: (id: number | null) => void; projectId: number | null; unitId: number | null; scopeTo: (projectId: number | null, unitId?: number | null) => void;
}) {
  const client = useQueryClient();
  const providers = useQuery({ queryKey: ["material-match-providers", currentUser()], queryFn: () => api.get<{ items: Provider[] }>("/material-match/providers"), retry: false });
  const projects = useQuery({ queryKey: ["projects", currentUser()], queryFn: () => api.get<{ id: number; title: string }[]>("/content-projects"), retry: false });
  const filter = new URLSearchParams({ limit: "30", ...(projectId ? { project_id: String(projectId) } : {}), ...(unitId ? { unit_id: String(unitId) } : {}) }).toString();
  const history = useQuery({ queryKey: ["material-match-runs", currentUser(), "all", filter], queryFn: () => api.get<{ items: RunSummary[] }>(`/material-match-runs?${filter}`), retry: false });
  const run = useMatchRun(runId);
  const [form, setForm] = useState({ text: "", projectId: projectId ? String(projectId) : "", aspect: "9:16", minShortSide: "720" });
  useEffect(() => { setForm(current => ({ ...current, projectId: projectId ? String(projectId) : current.projectId })); }, [projectId]);
  const [loadingPiece, setLoadingPiece] = useState(false);
  const fillFromPiece = async () => {
    if (!projectId || !unitId) return;
    setLoadingPiece(true); setState({});
    try {
      const list = await api.get<{ items: { id: number }[] }>(`/content-projects/${projectId}/units/${unitId}/master-revisions`);
      if (!list.items.length) throw new Error("这件作品还没有保存的主稿，先在作品里保存一版。");
      const master = await api.get<MasterText>(`/content-projects/${projectId}/units/${unitId}/master-revisions/${list.items[0].id}`);
      setForm(current => ({ ...current, text: pieceText(master).slice(0, 20000) }));
    } catch (error) { setState({ error: errorText(error) }); }
    finally { setLoadingPiece(false); }
  };
  const [state, setState] = useState<{ busy?: boolean; error?: string }>({});
  const start = async () => {
    setState({ busy: true });
    try {
      const created = await api.post<MatchRun>("/material-match-runs", { scope: "script", text: form.text.trim(), aspect: form.aspect,
        min_short_side: Number(form.minShortSide), ...(form.projectId ? { project_id: Number(form.projectId) } : {}),
        ...(unitId && form.projectId === String(projectId) ? { unit_id: unitId } : {}) });
      setState({});
      void client.invalidateQueries({ queryKey: ["material-match-runs"] });
      openRun(created.id);
    } catch (error) { setState({ error: errorText(error) }); }
  };
  const act = async (path: string) => {
    setState({ busy: true });
    try { await api.post(path); await run.refetch(); setState({}); } catch (error) { setState({ error: errorText(error) }); }
  };
  if (runId !== null) {
    const data = run.data;
    return <div className="space-y-6">
      <button className="text-[13px] text-ink-600 hover:text-ink-900" onClick={() => openRun(null)}>← 返回</button>
      {run.isPending ? <Spinner /> : run.isError || !data ? <ErrorBanner message={errorText(run.error)} /> : <>
        <div className="card space-y-4 p-6">
          <div className="flex flex-wrap items-baseline justify-between gap-3">
            <div><h2 className="font-serif text-[20px] font-semibold text-ink-900">{data.title}</h2>
              {ownerLabel(data) && <p className="mt-1 text-[13px] text-ink-600">属于 <Link className="text-accent-700 underline" to={ownerLink(data)!}>{ownerLabel(data)}</Link></p>}</div>
            <span className="text-[12.5px] text-ink-500">{data.settings.aspect} · 短边 ≥ {data.settings.min_short_side}px · {readableTime(data.created_at ?? "")}</span>
          </div>
          <RunStatus run={data} busy={state.busy} onCancel={() => void act(`/material-match-runs/${data.id}/cancel`)} onResume={() => void act(`/material-match-runs/${data.id}/resume`)} />
          {state.error && <ErrorBanner message={state.error} />}
        </div>
        {data.segments.length > 0 && <div className="card p-6 sm:p-7">{data.segments.map(segment => <SegmentResult key={segment.id} run={data} segment={segment} onChanged={() => void run.refetch()} />)}</div>}
      </>}
    </div>;
  }
  const off = (providers.data?.items ?? []).filter(item => !item.configured);
  return <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_320px]">
    <section className="card space-y-5 p-6 sm:p-7">
      <div>
        <h2 className="font-serif text-[20px] font-semibold text-ink-900">把一段文案变成素材方案</h2>
        <p className="mt-1.5 text-[13.5px] leading-relaxed text-ink-600">AI 先按画面需要拆段，再优先搜你自己的素材库，然后搜免费图库，并真的看每张候选图打分。只有你点「用这个」才会下载入库。</p>
      </div>
      {projectId && unitId && <div className="flex flex-wrap items-center gap-2"><Button size="sm" variant="secondary" disabled={loadingPiece} onClick={() => void fillFromPiece()}>{loadingPiece ? "读取中…" : "填入这件作品的内容"}</Button><span className="text-[12px] text-ink-500">读作品最新保存的主稿，可再修改。</span></div>}
      <Field label="文案或口播稿"><textarea className={inputClass} rows={9} maxLength={20000} value={form.text} placeholder="粘贴整段脚本……" onChange={event => setForm({ ...form, text: event.target.value })} /></Field>
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="画幅"><Segmented label="画幅" value={form.aspect} onChange={value => setForm({ ...form, aspect: value })} items={ASPECTS} /></Field>
        <Field label="最低清晰度（短边）"><select className={inputClass} value={form.minShortSide} onChange={event => setForm({ ...form, minShortSide: event.target.value })}>
          <option value="540">540p</option><option value="720">720p</option><option value="1080">1080p</option></select></Field>
      </div>
      <Field label="关联项目（可选）" hint="关联后，采用的素材会自动加入这个项目，并注明对应段落。"><select className={inputClass} value={form.projectId} onChange={event => setForm({ ...form, projectId: event.target.value })}>
        <option value="">不关联</option>{(projects.data ?? []).map(project => <option key={project.id} value={project.id}>{project.title}</option>)}</select></Field>
      <div className="flex flex-wrap items-center gap-2">
        {(providers.data?.items ?? []).map(item => <Chip key={item.key} tone={item.configured ? "good" : "neutral"}>{item.label}{item.configured ? "" : " · 未配置"}</Chip>)}
      </div>
      {off.length > 0 && <p className="text-[12px] leading-relaxed text-ink-500">{off.map(item => item.label).join("、")} 需要免费 API 密钥：填入 <code className="font-mono">apps/api/scripts/startup/runtime.env</code>（{off.map(item => item.key === "stock.pexels" ? "PEXELS_API_KEY" : item.key === "stock.pixabay" ? "PIXABAY_API_KEY" : item.key).join("、")}），重启服务后生效。</p>}
      {state.error && <ErrorBanner message={state.error} />}
      <div className="flex items-center justify-between gap-3">
        <span className="text-[12px] text-ink-500">每段约 1 次拆段 + 3 次看图评分</span>
        <Button disabled={state.busy || form.text.trim().length < 10} onClick={() => void start()}>开始找素材</Button>
      </div>
    </section>
    <aside className="space-y-3">
      <p className="eyebrow">最近的素材方案</p>
      {projectId ? <div className="flex flex-wrap items-center gap-2 text-[12.5px] text-ink-600"><span>只看 {history.data?.items[0] ? ownerLabel(unitId ? history.data.items[0] : { project: history.data.items[0].project }) ?? `项目 #${projectId}` : `项目 #${projectId}`}</span><button className="text-accent-700 underline" onClick={() => scopeTo(null)}>看全部</button></div> : null}
      {history.isPending ? <Spinner /> : !history.data?.items.length ? <EmptyState title="还没有素材方案" /> : history.data.items.map(item =>
        <button key={item.id} onClick={() => openRun(item.id)} className="card block w-full p-4 text-left transition-transform hover:-translate-y-0.5">
          <p className="line-clamp-2 text-[13.5px] text-ink-900">{item.title}</p>
          {ownerLabel(item) && <p className="mt-1 text-[12px] text-accent-700">{ownerLabel(item)}</p>}
          <p className="mt-1.5 text-[12px] text-ink-500">{item.status === "queued" || item.status === "running" ? "进行中" : item.status === "completed" ? `${item.segment_count} 段 · ${item.gap_count} 段缺素材` : item.status === "cancelled" ? "已取消" : "未完成"} · {readableTime(item.created_at ?? "")}</p>
        </button>)}
    </aside>
  </div>;
}
