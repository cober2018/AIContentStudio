export type WorkStatus = "draft" | "running" | "waiting_human" | "blocked" | "stale" | "ready" | "unknown" | "approved";
export type Modality = "text" | "image" | "video";
export type ProjectTab = "overview" | "brief" | "evidence" | "assets" | "matrix" | "versions" | "activity";

export interface ContentUnitView {
  id: string;
  title: string;
  identityId: string;
  modality: Modality;
  channelId: string;
  workflowName: string;
  status: WorkStatus;
  updatedAt: string;
}

export interface ProjectAssetView {
  id: string;
  title: string;
  type: "image" | "video" | "document" | "chart" | "screenshot";
  sourceType: "upload" | "system_library" | "workflow";
  revision: number;
  rightsStatus: "public_ok" | "internal" | "unknown";
  usedBy: string[];
}

export interface ContentProjectView {
  id: string;
  title: string;
  objective: string;
  status: WorkStatus;
  stage: string;
  identities: { id: string; name: string }[];
  brief: { objective: string; audience: string; message: string; angle: string; constraints: string[]; channels: string[] };
  evidence: { id: string; title: string; kind: "来源" | "证据" | "事实边界"; status: WorkStatus }[];
  assets: ProjectAssetView[];
  contentUnits: ContentUnitView[];
  risks: string[];
  versions: { label: string; value: string; status: WorkStatus }[];
  activity: { at: string; text: string }[];
  updatedAt: string;
}

const today = "2026-09-27";
const sampleProjects: ContentProjectView[] = [
  {
    id: "launch-ai-studio", title: "AI Content Studio 产品发布", objective: "把产品能力和真实使用方式讲清楚，形成多身份、多形态内容。", status: "ready", stage: "多形态制作",
    identities: [{ id: "brand", name: "品牌官方" }, { id: "founder", name: "创始人" }, { id: "expert", name: "产品专家" }],
    brief: { objective: "让目标用户理解内容项目的工作方式", audience: "内容团队与产品负责人", message: "同一组可信证据可以支撑不同身份和内容形态", angle: "从一个真实生产案例切入", constraints: ["不夸大自动发布能力", "保留来源和人工批准"], channels: ["公众号", "小红书", "B站", "X"] },
    evidence: [{ id: "s1", title: "产品能力说明与演示记录", kind: "来源", status: "ready" }, { id: "e1", title: "功能边界已核对", kind: "证据", status: "ready" }, { id: "f1", title: "产品事实边界 v3", kind: "事实边界", status: "approved" }],
    assets: [
      { id: "a1", title: "产品界面截图", type: "screenshot", sourceType: "upload", revision: 4, rightsStatus: "internal", usedBy: ["u1", "u2"] },
      { id: "a2", title: "品牌标题卡", type: "image", sourceType: "system_library", revision: 2, rightsStatus: "public_ok", usedBy: ["u2"] },
      { id: "a3", title: "执行链路图", type: "chart", sourceType: "workflow", revision: 2, rightsStatus: "public_ok", usedBy: ["u1", "u2"] },
      { id: "a4", title: "演示视频片段", type: "video", sourceType: "workflow", revision: 1, rightsStatus: "internal", usedBy: ["u3"] },
      ...Array.from({ length: 18 }, (_, index): ProjectAssetView => ({
        id: `a${index + 5}`, title: `项目素材 ${String(index + 1).padStart(2, "0")}`,
        type: index % 3 === 0 ? "image" : index % 3 === 1 ? "chart" : "document",
        sourceType: index % 3 === 0 ? "upload" : index % 3 === 1 ? "workflow" : "system_library",
        revision: 1, rightsStatus: index % 3 === 0 ? "internal" : "public_ok", usedBy: [],
      })),
    ],
    contentUnits: [
      { id: "u1", title: "产品发布长文", identityId: "brand", modality: "text", channelId: "公众号", workflowName: "品牌长文默认流程 v2", status: "ready", updatedAt: today },
      { id: "u2", title: "一图看懂内容生产", identityId: "brand", modality: "image", channelId: "小红书", workflowName: "品牌图卡流程 v1", status: "waiting_human", updatedAt: today },
      { id: "u3", title: "产品功能演示", identityId: "expert", modality: "video", channelId: "B站", workflowName: "专家视频流程 v1", status: "running", updatedAt: today },
      { id: "u4", title: "创始人观点", identityId: "founder", modality: "text", channelId: "X", workflowName: "创始人短帖流程 v1", status: "ready", updatedAt: today },
    ],
    risks: [],
    versions: [{ label: "创作任务书", value: "v3", status: "ready" }, { label: "身份快照", value: "v2", status: "ready" }, { label: "证据边界", value: "v3", status: "approved" }],
    activity: [{ at: "今天 10:42", text: "小红书图卡等待人工确认" }, { at: "今天 09:30", text: "产品事实边界冻结为 v3" }], updatedAt: today,
  },
  {
    id: "market-review", title: "市场复盘与观点解读", objective: "用可追溯的数据制作复盘内容。", status: "blocked", stage: "证据核对",
    identities: [{ id: "analyst", name: "研究员" }, { id: "brand", name: "品牌官方" }],
    brief: { objective: "复盘本周市场变化", audience: "关注市场趋势的读者", message: "让数字与结论一一对应", angle: "先列证据，再给观点", constraints: ["未确认数字不得使用"], channels: ["公众号", "微博", "小红书"] },
    evidence: [{ id: "s2", title: "外部市场数据", kind: "来源", status: "unknown" }, { id: "e2", title: "研究结论已过期", kind: "证据", status: "stale" }, { id: "f2", title: "事实边界待补充", kind: "事实边界", status: "blocked" }],
    assets: [{ id: "a5", title: "行情数据卡", type: "chart", sourceType: "workflow", revision: 1, rightsStatus: "unknown", usedBy: ["u5"] }, { id: "a6", title: "复盘参考图", type: "image", sourceType: "system_library", revision: 1, rightsStatus: "public_ok", usedBy: [] }],
    contentUnits: [
      { id: "u5", title: "本周市场长文", identityId: "analyst", modality: "text", channelId: "公众号", workflowName: "研究长文流程 v1", status: "blocked", updatedAt: today },
      { id: "u6", title: "市场数据图卡", identityId: "brand", modality: "image", channelId: "小红书", workflowName: "图卡流程 v1", status: "stale", updatedAt: today },
      { id: "u7", title: "短评", identityId: "analyst", modality: "text", channelId: "微博", workflowName: "短帖流程 v1", status: "unknown", updatedAt: today },
    ],
    risks: ["外部数据结果待核对", "图卡引用旧版数据", "部分素材公开使用权限未知"],
    versions: [{ label: "创作任务书", value: "v1", status: "ready" }, { label: "证据边界", value: "待补充", status: "blocked" }, { label: "数据快照", value: "v1（已过期）", status: "stale" }],
    activity: [{ at: "今天 11:10", text: "数据刷新结果未知，需人工核对" }, { at: "今天 10:05", text: "图卡因上游数据变化变为已过期" }], updatedAt: today,
  },
];

const STORAGE_KEY = "aicontentstudio.fe-f0-f1.projects.v1";

export function listMockProjects(): ContentProjectView[] {
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (stored) {
      const parsed: unknown = JSON.parse(stored);
      if (Array.isArray(parsed) && parsed.every((item) => item && typeof item === "object" && "id" in item && "contentUnits" in item)) return parsed as ContentProjectView[];
    }
  } catch { /* local storage can be unavailable in a private session */ }
  return structuredClone(sampleProjects);
}

export async function loadMockProjects(): Promise<ContentProjectView[]> {
  return listMockProjects();
}

export function saveMockProjects(projects: ContentProjectView[]): void {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(projects));
}

export function resetMockProjects(): ContentProjectView[] {
  window.localStorage.removeItem(STORAGE_KEY);
  return structuredClone(sampleProjects);
}
