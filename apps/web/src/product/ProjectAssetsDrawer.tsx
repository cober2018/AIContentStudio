import { useState } from "react";
import { Drawer, EmptyState, StatusBadge } from "../components/ui";
import type { ContentProjectView, ProjectAssetView } from "./mockProjects";

const sourceNames: Record<ProjectAssetView["sourceType"], string> = {
  upload: "项目上传", system_library: "系统素材引用", workflow: "生产流程生成",
};
const rightNames: Record<ProjectAssetView["rightsStatus"], string> = {
  public_ok: "可公开使用", internal: "仅内部使用", unknown: "权限待核对",
};

export default function ProjectAssetsDrawer({ project, onClose }: { project: ContentProjectView; onClose: () => void }) {
  const [filter, setFilter] = useState<"all" | ProjectAssetView["sourceType"]>("all");
  const assets = project.assets.filter((asset) => filter === "all" || asset.sourceType === filter);
  return (
    <Drawer title={`项目共享素材 · ${project.assets.length}`} onClose={onClose}>
      <p className="mb-5 text-sm text-slate-500">素材归属「{project.title}」。此处展示项目引用与版本，生产页面只保留入口。</p>
      <div className="mb-5 flex flex-wrap gap-2" role="tablist" aria-label="素材来源">
        {(["all", "upload", "system_library", "workflow"] as const).map((key) => (
          <button key={key} type="button" role="tab" aria-selected={filter === key} onClick={() => setFilter(key)} className={`rounded-lg px-3 py-2 text-xs ${filter === key ? "bg-indigo-600 text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"}`}>
            {key === "all" ? "全部" : sourceNames[key]}
          </button>
        ))}
      </div>
      {assets.length === 0 ? <EmptyState title="当前筛选暂无素材" hint="切换素材来源查看其他版本。" /> : (
        <div className="grid gap-3 sm:grid-cols-2">
          {assets.map((asset) => (
            <article key={asset.id} className="rounded-xl border border-slate-200 bg-white p-4">
              <div className="mb-3 flex h-24 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-50 to-slate-100 text-xs text-indigo-500">{asset.type.toUpperCase()} · v{asset.revision}</div>
              <h3 className="font-semibold text-slate-900">{asset.title}</h3>
              <p className="mt-1 text-xs text-slate-500">{sourceNames[asset.sourceType]} · {rightNames[asset.rightsStatus]}</p>
              <p className="mt-2 text-xs text-slate-500">使用位置：{asset.usedBy.length ? asset.usedBy.map((id) => project.contentUnits.find((unit) => unit.id === id)?.title || id).join("、") : "尚未引用"}</p>
              {asset.rightsStatus === "unknown" && <div className="mt-2"><StatusBadge status="unknown" /></div>}
            </article>
          ))}
        </div>
      )}
    </Drawer>
  );
}
