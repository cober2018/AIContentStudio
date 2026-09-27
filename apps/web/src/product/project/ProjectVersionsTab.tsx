import { useEffect, useState } from "react";
import { api, ApiError } from "../../api";
import { EmptyState, ErrorBanner, Spinner, StatusBadge } from "../../components/ui";
import type { Versions } from "./types";

const GROUPS: { key: keyof Versions; label: string }[] = [
  { key: "brief", label: "创作任务书" }, { key: "factBoundary", label: "事实边界" },
  { key: "contentUnits", label: "内容单元" }, { key: "workflows", label: "工作流" },
  { key: "runs", label: "运行" }, { key: "materials", label: "素材版本" },
  { key: "contentOutputs", label: "内容产物" },
];

export function ProjectVersionsTab({ projectId }: { projectId: number }) {
  const [versions, setVersions] = useState<Versions | null>(null);
  const [error, setError] = useState("");
  useEffect(() => { api.get<Versions>(`/content-projects/${projectId}/versions`).then(setVersions).catch((err) => setError(err instanceof ApiError ? err.message : "版本读取失败")); }, [projectId]);
  if (error) return <ErrorBanner message={error} />;
  if (!versions) return <Spinner label="读取项目版本…" />;
  return <section className="space-y-4"><p className="text-xs text-slate-500">这里只汇总真实存在的版本资源；身份快照尚未纳入 FE-F3A。</p>{GROUPS.map(({ key, label }) => <div key={key} className="rounded-xl border border-slate-200 bg-white p-5"><h2 className="font-semibold">{label} · {versions[key]?.length || 0}</h2>{versions[key]?.length ? <ul className="mt-3 space-y-2">{versions[key].map((item, index) => <li key={`${item.kind}-${item.id}-${item.source || index}`} className="rounded-lg border p-3 text-sm"><div className="flex items-center gap-2"><span>#{item.id}{item.version !== null ? ` · v${item.version}` : ""}</span>{item.status && <StatusBadge status={item.status} />}{item.current && <span className="text-xs text-indigo-700">当前关联</span>}</div>{item.checksum && <p className="mt-1 break-all text-xs text-slate-500">校验和：{item.checksum}</p>}{item.unitId && <p className="mt-1 text-xs text-slate-500">单元 #{item.unitId} · {item.source || "项目"}</p>}</li>)}</ul> : <div className="mt-3"><EmptyState title={`暂无${label}版本`} /></div>}</div>)}</section>;
}
