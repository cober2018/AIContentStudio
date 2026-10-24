import { useEffect, useRef, useState } from "react";
import { currentUser } from "../api";

export type Permission = "allowed" | "denied" | "unknown" | "revoked" | string | null;
export type LibraryMaterial = {
  type: "material"; id: number; title: string; status: string; kind: string; created_at: string;
  rights: { public_use: Permission; model_use: Permission; commercial_use?: Permission; rights_status?: string | null; attribution_present?: boolean };
  provenance: { source_kind?: string | null; source_url?: string | null; provider_key?: string | null; created_by?: string | null };
  drive: { source_id: number; status?: string; label?: string | null } | null;
  latest_revision: null | {
    id: number; revision_no: number; status: string; content_hash: string; mime_type: string | null;
    width: number | null; height: number | null; duration_ms: number | null;
  };
};
export type LibraryPage = { items: LibraryMaterial[]; total: number; limit: number; offset: number };
export type Collection = { id: number; name: string; description: string | null; status: string; revision: number; item_count: number; updated_at: string | null };
export type DriveSource = { id: number; label: string; root_path: string; status: "available" | "unavailable" | "different_volume"; created_at: string | null };

export const KIND_LABELS: Record<string, string> = { image: "图片", video: "视频", audio: "音频", screenshot: "截图", chart: "图表", brand: "品牌", other: "其他" };
export const SOURCE_LABELS: Record<string, string> = {
  upload: "上传", web_search: "网络素材", ai_generated: "AI 生成", chart: "图表", screenshot: "截图",
  upstream: "上游导入", legacy: "历史导入", external_execution: "剪辑产出", drive: "硬盘文件夹",
};
export const DRIVE_STATUS: Record<string, string> = { available: "已连接", unavailable: "硬盘未连接", different_volume: "不是登记的那块硬盘" };

export function mediaKind(item: LibraryMaterial): "image" | "video" | "audio" | null {
  const mime = item.latest_revision?.mime_type ?? "";
  return mime.startsWith("image/") ? "image" : mime.startsWith("video/") ? "video" : mime.startsWith("audio/") ? "audio" : null;
}

export function duration(ms: number | null | undefined) {
  if (!ms) return null;
  const seconds = Math.round(ms / 1000);
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;
}

export function rightsSummary(item: LibraryMaterial): { label: string; tone: "good" | "warn" | "bad" | "neutral" } {
  if (item.rights.public_use === "revoked") return { label: "已撤销", tone: "bad" };
  if (item.rights.public_use === "allowed") return { label: "可公开", tone: "good" };
  if (item.rights.model_use === "allowed") return { label: "仅本地使用", tone: "warn" };
  return { label: "权利未定", tone: "neutral" };
}

const previews = new Map<string, Promise<string>>();

// Thumbnails need the studio header, so they come through fetch and live as object URLs for the session.
export function previewUrl(materialId: number, revisionId: number, variant: "thumb" | "strip"): Promise<string> {
  const key = `${currentUser()}:${materialId}:${revisionId}:${variant}`;
  let promise = previews.get(key);
  if (!promise) {
    promise = fetch(`/api/v1/materials/${materialId}/revisions/${revisionId}/thumbnail?variant=${variant}`, { headers: { "X-Studio-User": currentUser() } })
      .then(response => { if (!response.ok) throw new Error(String(response.status)); return response.blob(); })
      .then(blob => URL.createObjectURL(blob));
    promise.catch(() => previews.delete(key));
    previews.set(key, promise);
  }
  return promise;
}

export function usePreview(materialId: number, revisionId: number | undefined, variant: "thumb" | "strip", enabled = true) {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);
  const [state, setState] = useState<{ url?: string; failed?: boolean }>({});
  useEffect(() => {
    const node = ref.current;
    if (!node || visible) return;
    const observer = new IntersectionObserver(entries => { if (entries.some(entry => entry.isIntersecting)) setVisible(true); }, { rootMargin: "240px" });
    observer.observe(node);
    return () => observer.disconnect();
  }, [visible]);
  useEffect(() => {
    if (!enabled || !visible || revisionId === undefined) return;
    let active = true;
    previewUrl(materialId, revisionId, variant).then(url => { if (active) setState({ url }); }).catch(() => { if (active) setState({ failed: true }); });
    return () => { active = false; };
  }, [enabled, visible, materialId, revisionId, variant]);
  return { ref, ...state };
}
