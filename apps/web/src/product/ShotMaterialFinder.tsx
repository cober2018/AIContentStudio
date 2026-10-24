import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Search } from "lucide-react";
import { useEffect, useState } from "react";
import { api, currentUser } from "../api";
import { Button, ErrorBanner } from "../components/ui";
import { Accepted, MatchRun, RunStatus, SegmentResult, errorText, useMatchRun } from "./MaterialMatchView";

export type FinderShot = { id: string; label: string; text: string; bound: boolean };

function nearestAspect(width: number, height: number) {
  const ratio = width / height;
  const options: [string, number][] = [["9:16", 9 / 16], ["3:4", 3 / 4], ["1:1", 1], ["4:3", 4 / 3], ["16:9", 16 / 9]];
  return options.reduce((best, item) => Math.abs(item[1] - ratio) < Math.abs(best[1] - ratio) ? item : best)[0];
}

export default function ShotMaterialFinder({ projectId, unitId, shots, focusKey, aspect, readOnly, onPicked }: {
  projectId: number; unitId: number; shots: FinderShot[]; focusKey: string; aspect: [number, number]; readOnly?: boolean;
  onPicked: (shotId: string, materialRevisionId: number) => void;
}) {
  const client = useQueryClient();
  const focused = shots.find(shot => focusKey.startsWith(`shots.${shot.id}.`));
  const missing = shots.filter(shot => !shot.bound);
  const latest = useQuery({ queryKey: ["material-match-runs", currentUser(), "shots", unitId], retry: false,
    queryFn: () => api.get<{ items: { id: number }[] }>(`/material-match-runs?scope=shots&unit_id=${unitId}&limit=1`) });
  const [runId, setRunId] = useState<number | null>(null);
  useEffect(() => { if (runId === null && latest.data?.items[0]) setRunId(latest.data.items[0].id); }, [latest.data, runId]);
  const run = useMatchRun(runId);
  const [state, setState] = useState<{ busy?: boolean; error?: string; notice?: string }>({});
  const start = async (targets: FinderShot[]) => {
    setState({ busy: true });
    try {
      const created = await api.post<MatchRun>("/material-match-runs", {
        scope: "shots", project_id: projectId, unit_id: unitId, aspect: nearestAspect(aspect[0], aspect[1]),
        title: targets.length === 1 ? `镜头找素材 · ${targets[0].label}` : `镜头找素材 · ${targets.length} 个镜头`,
        shots: targets.map(shot => ({ id: shot.id, label: shot.label, text: shot.text })),
      });
      setRunId(created.id);
      setState({});
      void client.invalidateQueries({ queryKey: ["material-match-runs"] });
    } catch (error) { setState({ error: errorText(error) }); }
  };
  const act = async (path: string) => {
    setState({ busy: true });
    try { await api.post(path); await run.refetch(); setState({}); } catch (error) { setState({ error: errorText(error) }); }
  };
  const picked = (value: Accepted) => {
    onPicked(value.segment_id, value.material_revision_id);
    setState({ notice: "已入库并关联项目，正在填入这个镜头的素材位；保存分镜后生效。" });
  };
  const usable = (target: FinderShot | undefined) => !!target && target.text.trim().length >= 4;
  const data = run.data;
  return <div className="space-y-3">
    <div className="flex items-center gap-2 text-[13.5px] font-medium text-ink-900"><Search size={14} />为镜头找素材</div>
    <p className="text-[12px] leading-relaxed text-ink-500">按镜头的画面描述、用途和口播，先搜你的素材库，再搜免费图库，并看图打分。</p>
    <div className="flex flex-wrap gap-2">
      <Button size="sm" disabled={readOnly || state.busy || !usable(focused)} onClick={() => focused && void start([focused])}>{focused ? `找「${focused.label}」的素材` : "先点进一个镜头"}</Button>
      <Button size="sm" variant="secondary" disabled={readOnly || state.busy || !missing.filter(usable).length} onClick={() => void start(missing.filter(usable))}>找所有缺素材的镜头（{missing.filter(usable).length}）</Button>
    </div>
    {focused && !usable(focused) && <p className="text-[12px] text-amber-800">这个镜头还没有画面描述或用途，先补上再找。</p>}
    {state.error && <ErrorBanner message={state.error} />}
    {state.notice && <p className="text-[12px] text-emerald-700">{state.notice}</p>}
    {data && <div className="space-y-4 rounded-xl bg-paper/70 p-3">
      <RunStatus run={data} busy={state.busy} onCancel={() => void act(`/material-match-runs/${data.id}/cancel`)} onResume={() => void act(`/material-match-runs/${data.id}/resume`)} />
      {data.segments.map(segment => <SegmentResult key={segment.id} run={data} segment={segment} compact onAccepted={picked} onChanged={() => void run.refetch()} />)}
    </div>}
  </div>;
}
