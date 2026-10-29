import { Component, lazy, Suspense, type ReactNode } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Link, NavLink, Navigate, Route, Routes, useLocation, useParams } from "react-router-dom";
import { CheckCircle2, Clapperboard, FolderOpen, Images, Library, LineChart, PenLine, Settings2, Sparkles, Sun, UserRound, type LucideIcon } from "lucide-react";
import { useProductionWorkbench } from "./product/taskNavigation";

const MaterialLibraryFloat = lazy(() => import("./product/MaterialLibraryFloat"));
const ProductionQueuePage = lazy(() => import("./product/ProductionQueuePage"));
const WorkbenchEntry = lazy(() => import("./product/WorkbenchEntry"));
const IdentityWorkspace = lazy(() => import("./product/IdentityWorkspace"));
const LearningWorkspace = lazy(() => import("./product/LearningWorkspace"));
const SystemAssetsKnowledgePage = lazy(() => import("./product/SystemAssetsKnowledgePage"));
const MaterialLibraryPage = lazy(() => import("./product/MaterialLibraryPage"));
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

const NAV_GROUPS: { label: string; items: { to: string; label: string; icon: LucideIcon }[] }[] = [
  { label: "今日", items: [
    { to: "/home", label: "今日工作台", icon: Sun },
  ] },
  { label: "创作", items: [
    { to: "/opportunities", label: "内容机会", icon: Sparkles },
    { to: "/projects", label: "内容项目", icon: FolderOpen },
    { to: "/production?workspace=persona", label: "角色内容工作台", icon: PenLine },
    { to: "/production?workspace=product", label: "商品视频工作台", icon: Clapperboard },
  ] },
  { label: "发布与增长", items: [
    { to: "/review", label: "审阅与交付", icon: CheckCircle2 },
    { to: "/learning", label: "效果复盘", icon: LineChart },
  ] },
  { label: "资料", items: [
    { to: "/identities", label: "角色与账号", icon: UserRound },
    { to: "/materials", label: "素材库", icon: Images },
    { to: "/assets", label: "素材与知识", icon: Library },
  ] },
];

function NavItem({ to, label, icon: Icon }: { to: string; label: string; icon: LucideIcon }) {
  const location = useLocation();
  const workbench = useProductionWorkbench();
  const production = /^\/projects\/\d+\/units\/\d+\/production$/.test(location.pathname);
  // Two workbenches share /production; only the query tells them apart. A production page counts as its workbench.
  const activeFor = (isActive: boolean) => production ? !!workbench && to === `/production?workspace=${workbench}` : to.includes("?") ? location.pathname === "/production" && location.search.includes(to.split("?")[1]) : isActive;
  return <NavLink
    to={to}
    className={({ isActive }) => {
      const active = activeFor(isActive);
      return `group relative flex shrink-0 items-center gap-3 whitespace-nowrap rounded-[10px] px-3 py-2 text-[14px] transition-colors duration-200 ${active ? "bg-surface font-medium text-ink-900 shadow-card" : "text-ink-600 hover:bg-ink-100/70 hover:text-ink-900"}`;
    }}
  >
    {({ isActive }) => {
      const active = activeFor(isActive);
      return <>
        <Icon aria-hidden size={17} strokeWidth={1.6} className={active ? "text-accent-500" : "text-ink-400 transition-colors group-hover:text-ink-700"} />
        {label}
      </>;
    }}
  </NavLink>;
}

function RouteLoading() {
  return <div className="flex items-center gap-3 px-10 py-12 text-sm text-ink-500" role="status" aria-live="polite"><span className="h-1.5 w-1.5 animate-pulse rounded-full bg-accent-500" />正在加载页面…</div>;
}

class RouteFailureBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };

  static getDerivedStateFromError() { return { failed: true }; }

  render() {
    if (this.state.failed) {
      return <div className="px-10 py-12" role="alert"><p className="font-serif text-lg text-ink-900">页面加载失败</p><p className="mt-1 text-sm text-ink-500">请检查连接后重试。</p><button className="mt-4 rounded-pill border border-ink-300 bg-surface px-4 py-2 text-sm text-ink-800 hover:border-ink-500" onClick={() => window.location.reload()}>重新加载</button></div>;
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
  return (
        <div className="flex min-h-screen flex-col bg-paper md:flex-row">
          <a href="#main-content" className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-pill focus:bg-ink-900 focus:px-4 focus:py-2 focus:text-sm focus:text-paper">跳到正文</a>
          <aside className="relative z-10 flex w-full shrink-0 flex-col border-b border-ink-200/80 bg-paper md:sticky md:top-0 md:h-screen md:w-[248px] md:border-b-0 md:border-r">
            <div className="flex items-center justify-between px-5 pb-3 pt-5 md:block md:px-6 md:pb-6 md:pt-8">
              <Link to="/home" className="group flex items-center gap-3" aria-label="AI Content Studio 首页">
                <span aria-hidden className="grid h-8 w-8 place-items-center rounded-[9px] bg-accent-500 font-display text-[15px] leading-none text-paper shadow-[inset_0_-2px_0_rgb(0_0_0/0.18)]">文</span>
                <span className="leading-tight">
                  <span className="block font-display text-[19px] tracking-tight text-ink-900">Content Studio</span>
                  <span className="block text-[11px] text-ink-500">角色 · 内容 · 增长</span>
                </span>
              </Link>
            </div>
            <nav className="flex flex-1 gap-1 overflow-x-auto px-3 pb-3 [scrollbar-width:none] md:block md:overflow-y-auto md:px-4 md:pb-6 [&::-webkit-scrollbar]:hidden" aria-label="主导航">
              {NAV_GROUPS.map((group) => <div key={group.label} className="flex shrink-0 gap-1 md:mb-6 md:block">
                <p className="eyebrow hidden px-3 pb-2 md:block">{group.label}</p>
                <div className="flex gap-1 md:block md:space-y-0.5">
                  {group.items.map((item) => <NavItem key={item.to} {...item} />)}
                </div>
              </div>)}
              <div className="flex shrink-0 md:hidden"><NavItem to="/settings" label="设置" icon={Settings2} /></div>
            </nav>
            <div className="hidden border-t border-ink-200/80 px-4 py-4 md:block">
              <NavItem to="/settings" label="设置" icon={Settings2} />
              <p className="mt-3 px-3 text-[11px] leading-relaxed text-ink-500">本机工作台 · 项目与素材持久保存</p>
            </div>
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
              <Route path="/production" element={<WorkbenchEntry queue={ProductionQueuePage} />} />
              <Route path="/review" element={<ProjectReviewCenter />} />
              <Route path="/identities" element={<IdentityWorkspace />} />
              <Route path="/accounts" element={<Navigate to="/identities?directory=account" replace />} />
              <Route path="/assets" element={<SystemAssetsKnowledgePage />} />
              <Route path="/learning" element={<LearningWorkspace />} />
              <Route path="/materials" element={<MaterialLibraryPage />} />
              <Route path="/settings" element={<ProductSettingsPage />} />
              <Route path="*" element={<Navigate to="/home" replace />} />
                </Routes>
              </Suspense>
            </RouteFailureBoundary>
          </main>
          <Suspense fallback={null}><MaterialLibraryFloat /></Suspense>
        </div>
  );
}

function ProjectRoute() {
  const { projectId } = useParams();
  return projectId && /^\d+$/.test(projectId) ? <><ProjectOriginLink projectId={Number(projectId)} /><PersistentProjectPage /></> : <ProjectPage />;
}

function ProductionRoute() {
  const { projectId } = useParams();
  return projectId && /^\d+$/.test(projectId) ? <PersistentProductionPage /> : <ProductionShellPage />;
}
