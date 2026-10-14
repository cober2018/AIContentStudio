import { Component, lazy, Suspense, type ReactNode } from "react";
import { QueryClient, QueryClientProvider, useQuery } from "@tanstack/react-query";
import { api, currentUser } from "./api";
import { BrowserRouter, Link, NavLink, Navigate, Route, Routes, useLocation, useParams } from "react-router-dom";

const Assets = lazy(() => import("./pages/Assets"));
const Connectors = lazy(() => import("./pages/Connectors"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const Landing = lazy(() => import("./pages/Landing"));
const FactPacks = lazy(() => import("./pages/FactPacks"));
const Handoff = lazy(() => import("./pages/Handoff"));
const Materials = lazy(() => import("./pages/Materials"));
const Review = lazy(() => import("./pages/Review"));
const ReviewPublish = lazy(() => import("./pages/ReviewPublish"));
const Settings = lazy(() => import("./pages/Settings"));
const Sources = lazy(() => import("./pages/Sources"));
const Templates = lazy(() => import("./pages/Templates"));
const Topics = lazy(() => import("./pages/Topics"));
const Workflows = lazy(() => import("./pages/Workflows"));
const Workspace = lazy(() => import("./pages/Workspace"));
const ProductionQueuePage = lazy(() => import("./product/ProductionQueuePage"));
const IdentityWorkspace = lazy(() => import("./product/IdentityWorkspace"));
const LearningWorkspace = lazy(() => import("./product/LearningWorkspace"));
const SystemAssetsKnowledgePage = lazy(() => import("./product/SystemAssetsKnowledgePage"));
const ProductSettingsPage = lazy(() => import("./product/ProductSettingsPage"));
const ProjectReviewCenter = lazy(() => import("./product/ProjectReviewCenter"));
const HomePage = lazy(() => import("./product/HomePage"));
const ProjectOriginLink = lazy(() => import("./product/HomePage").then((module) => ({ default: module.ProjectOriginLink })));
const OpportunitiesPage = lazy(() => import("./product/OpportunityPages").then((module) => ({ default: module.OpportunitiesPage })));
const OpportunityDetailPage = lazy(() => import("./product/OpportunityPages").then((module) => ({ default: module.OpportunityDetailPage })));
const ProjectsPage = lazy(() => import("./product/ProjectPages").then((module) => ({ default: module.ProjectsPage })));
const ProjectPage = lazy(() => import("./product/ProjectPages").then((module) => ({ default: module.ProjectPage })));
const ProductionShellPage = lazy(() => import("./product/ProjectPages").then((module) => ({ default: module.ProductionShellPage })));
const PersistentProjectsPage = lazy(() => import("./product/PersistentProjectsPage").then((module) => ({ default: module.PersistentProjectsPage })));
const PersistentProjectPage = lazy(() => import("./product/PersistentProjectPage").then((module) => ({ default: module.PersistentProjectPage })));
const PersistentProductionPage = lazy(() => import("./product/PersistentProductionPage").then((module) => ({ default: module.PersistentProductionPage })));

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } },
});

const NAV = [
  { to: "/home", label: "今日工作台", icon: "◧" },
  { to: "/opportunities", label: "内容机会", icon: "✧" },
  { to: "/projects", label: "内容项目", icon: "▤" },
  { to: "/production", label: "创作与执行", icon: "✍" },
  { to: "/review", label: "审阅与发布", icon: "✓" },
  { to: "/identities", label: "内容身份", icon: "◉" },
  { to: "/assets", label: "素材与知识", icon: "▦" },
  { to: "/learning", label: "效果与学习", icon: "▥" },
  { to: "/settings", label: "设置", icon: "⚙" },
];

function RouteLoading() {
  return <div className="p-9 text-sm text-slate-600" role="status" aria-live="polite">正在加载页面…</div>;
}

class RouteFailureBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };

  static getDerivedStateFromError() { return { failed: true }; }

  render() {
    if (this.state.failed) {
      return <div className="p-9" role="alert"><p className="text-sm text-rose-700">页面加载失败，请检查连接后重试。</p><button className="mt-3 rounded-lg border border-slate-300 px-4 py-2 text-sm" onClick={() => window.location.reload()}>重新加载</button></div>;
    }
    return this.props.children;
  }
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Shell />
      </BrowserRouter>
    </QueryClientProvider>
  );
}

function Shell() {
  const location = useLocation();
  const isLanding = location.pathname === "/legacy/landing";
  if (isLanding) {
    return (
      <RouteFailureBoundary key={location.pathname}>
        <Suspense fallback={<RouteLoading />}>
          <Routes>
            <Route path="/legacy/landing" element={<Landing />} />
            <Route path="*" element={<Navigate to="/home" replace />} />
          </Routes>
        </Suspense>
      </RouteFailureBoundary>
    );
  }
  return (
        <div className="flex min-h-screen flex-col bg-[#f4f6fb] md:flex-row">
          <aside className="relative flex w-full shrink-0 flex-col bg-[#11141b] text-white md:sticky md:top-0 md:h-screen md:w-60">
            <div className="px-5 py-4 md:py-6">
              <Link to="/home" className="text-base font-bold tracking-tight">AI Content Studio</Link>
              <div className="mt-1 text-[11px] text-slate-400">项目驱动 · 图文视频协作</div>
            </div>
            <nav className="flex flex-1 gap-1 overflow-x-auto px-3 pb-3 md:block md:space-y-0.5 md:overflow-y-auto md:pb-4" aria-label="主导航">
              <p className="hidden px-3 pb-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500 md:block">工作区</p>
              {NAV.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) => `flex shrink-0 items-center gap-2.5 whitespace-nowrap rounded-lg px-3 py-2.5 text-sm transition ${isActive ? "bg-[#2a2d42] font-medium text-white" : "text-slate-300 hover:bg-[#252936] hover:text-white"}`}
                >
                  <span className="w-4 text-center text-xs text-indigo-300">{item.icon}</span>
                  {item.label}
                </NavLink>
              ))}
            </nav>
            <div className="hidden border-t border-slate-700/70 px-5 py-4 text-[11px] text-slate-400 md:block">本机工作台 · 项目与素材持久保存</div>
          </aside>
          <main className="min-w-0 flex-1" id="main-content">
            <RouteFailureBoundary key={location.pathname}>
              <Suspense fallback={<RouteLoading />}>
                <Routes>
              <Route path="/" element={<Navigate to="/home" replace />} />
              <Route path="/home" element={<HomePage />} />
              <Route path="/opportunities" element={<OpportunitiesPage />} />
              <Route path="/opportunities/:id" element={<OpportunityDetailPage />} />
              <Route path="/projects" element={<PersistentProjectsPage />} />
              <Route path="/projects/demo" element={<ProjectsPage />} />
              <Route path="/projects/:projectId" element={<ProjectRoute />} />
              <Route path="/projects/:projectId/units/:unitId/production" element={<ProductionRoute />} />
              <Route path="/production" element={<ProductionQueuePage />} />
              <Route path="/review" element={<ProjectReviewCenter />} />
              <Route path="/identities" element={<IdentityWorkspace />} />
              <Route path="/accounts" element={<Navigate to="/identities" replace />} />
              <Route path="/assets" element={<SystemAssetsKnowledgePage />} />
              <Route path="/learning" element={<LearningWorkspace />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/sources" element={<Sources />} />
              <Route path="/connectors" element={<Connectors />} />
              <Route path="/fact-packs" element={<FactPacks />} />
              <Route path="/fact-packs/:id" element={<FactPacks />} />
              <Route path="/topics" element={<Topics />} />
              <Route path="/workspace" element={<Workspace />} />
              <Route path="/workspace/:topicId" element={<Workspace />} />
              <Route path="/materials" element={<Materials />} />
              <Route path="/review-publish" element={<ReviewPublish />} />
              <Route path="/review-publish/:topicId" element={<ReviewPublish />} />
              <Route path="/legacy/review" element={<Review />} />
              <Route path="/legacy/assets" element={<Assets />} />
              <Route path="/handoff" element={<Handoff />} />
              <Route path="/workflows" element={<Workflows />} />
              <Route path="/templates" element={<Templates />} />
              <Route path="/settings" element={<ProductSettingsPage />} />
              <Route path="/legacy/settings" element={<AdminSettingsRoute />} />
              <Route path="*" element={<Navigate to="/home" replace />} />
                </Routes>
              </Suspense>
            </RouteFailureBoundary>
          </main>
        </div>
  );
}

function ProjectRoute() {
  const { projectId } = useParams();
  return projectId && /^\d+$/.test(projectId) ? <><ProjectOriginLink projectId={Number(projectId)} /><PersistentProjectPage /></> : <ProjectPage />;
}

function AdminSettingsRoute() {
  const user = useQuery({ queryKey: ["settings-admin", currentUser()], queryFn: () => api.get<{ role: string }>("/users/me"), retry: false });
  if (user.isPending) return <RouteLoading />;
  if (user.error || user.data?.role !== "admin") return <div className="p-9" role="alert">本机运行配置仅限管理员访问。<Link to="/settings" className="ml-2 text-indigo-700 underline">返回安全产品设置</Link></div>;
  return <Settings />;
}

function ProductionRoute() {
  const { projectId } = useParams();
  return projectId && /^\d+$/.test(projectId) ? <PersistentProductionPage /> : <ProductionShellPage />;
}
