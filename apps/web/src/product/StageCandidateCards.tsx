import { useEffect, useState } from "react";
import { currentUser } from "../api";

type Canvas = { id: string; order: number };
type Target = { projectId: number; unitId: number; nodeId: string; runId: number; attemptId: number; candidateId: string };

const images = new Map<string, Promise<string>>();

// Rendering is heavy, so cards load one after another and stay cached as object URLs for the session.
function cardUrl(target: Target, canvasId: string, width?: number) {
  const query = new URLSearchParams({ run_id: String(target.runId), attempt_id: String(target.attemptId), candidate_id: target.candidateId, canvas_id: canvasId, ...(width ? { width: String(width) } : {}) });
  const path = `/api/v1/content-projects/${target.projectId}/units/${target.unitId}/creation-recipe/stages/${encodeURIComponent(target.nodeId)}/candidate-previews?${query}`;
  const key = `${currentUser()}:${path}`;
  let promise = images.get(key);
  if (!promise) {
    promise = fetch(path, { headers: { "X-Studio-User": currentUser() } })
      .then(async response => {
        if (!response.ok) throw new Error(response.status === 422 ? "unavailable" : String(response.status));
        return URL.createObjectURL(await response.blob());
      });
    promise.catch(() => images.delete(key));
    images.set(key, promise);
  }
  return promise;
}

export default function StageCandidateCards({ target, canvases, edited }: { target: Target; canvases: Canvas[]; edited: boolean }) {
  const ordered = [...canvases].sort((left, right) => left.order - right.order);
  const [urls, setUrls] = useState<Record<string, string>>({});
  const [state, setState] = useState<"loading" | "done" | "unavailable" | "failed">("loading");
  const [open, setOpen] = useState<{ id: string; url?: string } | null>(null);
  const key = `${target.attemptId}:${target.candidateId}`;
  useEffect(() => {
    let active = true;
    setUrls({}); setState("loading");
    (async () => {
      for (const canvas of ordered) {
        try {
          const url = await cardUrl(target, canvas.id, 480);
          if (!active) return;
          setUrls(current => ({ ...current, [canvas.id]: url }));
        } catch (error) {
          if (active) setState(error instanceof Error && error.message === "unavailable" ? "unavailable" : "failed");
          return;
        }
      }
      if (active) setState("done");
    })();
    return () => { active = false; };
    // The candidate identity fully determines the images.
  }, [key]);
  const enlarge = (id: string) => {
    setOpen({ id });
    cardUrl(target, id).then(url => setOpen(current => current?.id === id ? { id, url } : current)).catch(() => setOpen(null));
  };
  if (state === "unavailable") return <p className="mt-3 rounded-lg bg-slate-50 p-3 text-xs text-slate-600">预览不可用：本机渲染器未配置。仍可在下方按文字结构审阅并接受。</p>;
  return <div className="mt-4">
    <div className="flex flex-wrap items-baseline justify-between gap-2">
      <p className="text-sm font-medium text-slate-800">卡片预览（{ordered.length} 张）</p>
      <p className="text-xs text-slate-500">平台渲染器出的预览图，不算定稿。{edited ? "这是原候选的样子，你在下方的修改接受后再渲染。" : "点开看大图。"}</p>
    </div>
    <div className="mt-2 grid grid-cols-3 gap-2 sm:grid-cols-4 lg:grid-cols-7">
      {ordered.map((canvas, index) => <button key={canvas.id} type="button" onClick={() => urls[canvas.id] && enlarge(canvas.id)}
        className="relative overflow-hidden rounded-lg border border-slate-200 bg-slate-100 text-left" aria-label={`查看第 ${index + 1} 张大图`}>
        {urls[canvas.id] ? <img src={urls[canvas.id]} alt={`第 ${index + 1} 张`} className="block w-full" /> : <div className="aspect-[3/4] animate-pulse" />}
        <span className="absolute left-1 top-1 rounded bg-black/55 px-1.5 text-[11px] text-white">{index === 0 ? "封面" : index + 1}</span>
      </button>)}
    </div>
    {state === "failed" && <p className="mt-2 text-xs text-amber-700">有卡片没渲染出来，刷新再试；接受不受影响。</p>}
    {open && <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4" onClick={() => setOpen(null)} role="dialog" aria-label="卡片大图">
      {open.url ? <img src={open.url} alt="卡片大图" className="max-h-full max-w-full rounded-lg shadow-2xl" /> : <p className="text-sm text-white">加载大图…</p>}
    </div>}
  </div>;
}
