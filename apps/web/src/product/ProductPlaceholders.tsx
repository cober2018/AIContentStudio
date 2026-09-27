import { Link } from "react-router-dom";
import { EmptyState } from "../components/ui";

const descriptions: Record<string, { title: string; lead: string; next: string }> = {
  home: { title: "今日工作台", lead: "今天的机会、待决策事项与进行中项目会汇集在这里。", next: "先浏览内容项目" },
  opportunities: { title: "内容机会", lead: "将外部趋势、内部信号和内容缺口整理成可判断的机会。", next: "查看项目" },
  production: { title: "生产工作台", lead: "从内容项目中选择一个内容单元，进入对应的文字、图片或视频生产空间。", next: "选择项目" },
  review: { title: "审阅与发布", lead: "后续将以项目 → 内容单元 → 候选稿组织审阅，区分内容批准和交付授权。", next: "查看项目" },
  identities: { title: "内容身份", lead: "品牌、角色、账号与栏目会构成长期使用的内容身份。", next: "查看项目" },
  assets: { title: "素材与知识", lead: "跨项目复用的素材与知识将在此管理；项目素材可从项目页打开。", next: "查看项目" },
  learning: { title: "效果与学习", lead: "回收历史内容表现，整理可供人工判断的学习候选。", next: "查看项目" },
};

export default function ProductPlaceholder({ kind }: { kind: keyof typeof descriptions }) {
  const item = descriptions[kind];
  return (
    <div className="mx-auto max-w-6xl px-6 py-9">
      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-indigo-600">AI Content Studio</p>
      <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-900">{item.title}</h1>
      <p className="mt-2 text-sm text-slate-500">{item.lead}</p>
      <div className="mt-8"><EmptyState title="此工作区正在建设" hint="FE-F0-F1 先提供清晰入口；业务操作将在后续切片接入。" action={<Link to="/projects" className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700">{item.next}</Link>} /></div>
    </div>
  );
}
