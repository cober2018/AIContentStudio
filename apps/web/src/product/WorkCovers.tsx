import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { api, currentUser } from "../api";

export type CoverRef = { material_id: number; material_revision_id: number };

// The cover is read as a blob because identity travels in a request header; the same blob backs the download.
export function CoverImage({ cover, label = "封面", download }: { cover: CoverRef; label?: string; download?: string }) {
  const [url, setUrl] = useState("");
  useEffect(() => {
    let alive = true, made = "";
    fetch(`/api/v1/materials/${cover.material_id}/revisions/${cover.material_revision_id}/raw`, { headers: { "X-Studio-User": currentUser() } })
      .then(response => response.ok ? response.blob() : null)
      .then(blob => { if (alive && blob) { made = URL.createObjectURL(blob); setUrl(made); } });
    return () => { alive = false; if (made) URL.revokeObjectURL(made); };
  }, [cover.material_id, cover.material_revision_id]);
  if (!url) return <p className="text-xs text-slate-400">加载中…</p>;
  return <div className="space-y-1">
    <img src={url} alt={label} className="max-h-[40vh] w-auto rounded-lg border border-slate-200" />
    {download && <a className="text-xs text-indigo-700 underline" href={url} download={download}>下载</a>}
  </div>;
}

// A landscape work has a 16:9 cover and a 3:4 one for list pages that crop to 3:4.
export function LandscapeCovers({ cover, vertical }: { cover: CoverRef | null | undefined; vertical: CoverRef | null | undefined }) {
  return <div className="flex flex-wrap items-start gap-4">{([["横封面 16:9", cover, "横封面-16x9"], ["竖封面 3:4", vertical, "竖封面-3x4"]] as const).map(([label, ref, file]) =>
    <div key={label} className="w-56 shrink-0"><p className="mb-1 text-xs text-slate-600">{label}</p>{ref ? <CoverImage cover={ref} label={label} download={file} /> : <p className="text-xs text-slate-400">还没交</p>}</div>)}</div>;
}

// 交付 step of a work that is not a product video: only landscape works get their covers shown here.
export default function WorkCovers({ projectId, unitId }: { projectId: number; unitId: number }) {
  const covers = useQuery({ queryKey: ["work-covers", projectId, unitId, currentUser()], retry: false,
    queryFn: () => api.get<{ aspect: string; cover: CoverRef | null; cover_vertical: CoverRef | null }>(`/content-projects/${projectId}/units/${unitId}/video-chain/covers`) });
  if (covers.data?.aspect !== "16:9") return null;
  return <section className="mb-6 rounded-lg border border-slate-200 p-4"><h3 className="mb-3 font-semibold">作品封面</h3>
    <LandscapeCovers cover={covers.data.cover} vertical={covers.data.cover_vertical} /></section>;
}
