import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Link, NavLink, Navigate, Route, Routes, useLocation } from "react-router-dom";
import Assets from "./pages/Assets";
import Connectors from "./pages/Connectors";
import Dashboard from "./pages/Dashboard";
import Landing from "./pages/Landing";
import FactPacks from "./pages/FactPacks";
import Handoff from "./pages/Handoff";
import Review from "./pages/Review";
import Settings from "./pages/Settings";
import Sources from "./pages/Sources";
import Templates from "./pages/Templates";
import Topics from "./pages/Topics";
import Workflows from "./pages/Workflows";
import Workspace from "./pages/Workspace";
import ProductPlaceholder from "./product/ProductPlaceholders";
import { ProductionShellPage, ProjectPage, ProjectsPage } from "./product/ProjectPages";

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } },
});

const NAV = [
  { to: "/home", label: "今日工作台", icon: "◧" },
  { to: "/opportunities", label: "内容机会", icon: "✧" },
  { to: "/projects", label: "内容项目", icon: "▤" },
  { to: "/production", label: "生产工作台", icon: "✍" },
  { to: "/review", label: "审阅与发布", icon: "✓" },
  { to: "/identities", label: "内容身份", icon: "◉" },
  { to: "/assets", label: "素材与知识", icon: "▦" },
  { to: "/learning", label: "效果与学习", icon: "▥" },
  { to: "/settings", label: "设置", icon: "⚙" },
];

const LEGACY_NAV = [
  { to: "/dashboard", label: "旧总览" }, { to: "/sources", label: "来源与证据" },
  { to: "/connectors", label: "数据接入" }, { to: "/fact-packs", label: "FactPack" },
  { to: "/topics", label: "选题中心" }, { to: "/workspace", label: "旧生产页" },
  { to: "/legacy/review", label: "旧审核中心" }, { to: "/legacy/assets", label: "旧内容资产" },
  { to: "/handoff", label: "文章交付" }, { to: "/workflows", label: "旧工作流" },
  { to: "/templates", label: "模板与规则" },
];

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
  const isLanding = location.pathname === "/";
  if (isLanding) {
    return (
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
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
              <details className="mt-7 hidden border-t border-slate-700/70 pt-4 md:block">
                <summary className="cursor-pointer px-3 text-xs text-slate-400">现有功能入口</summary>
                <div className="mt-3 space-y-0.5">{LEGACY_NAV.map((item) => <Link key={item.to} to={item.to} className="block rounded-lg px-3 py-1.5 text-xs text-slate-400 hover:bg-[#252936] hover:text-white">{item.label}</Link>)}</div>
              </details>
            </nav>
            <div className="hidden border-t border-slate-700/70 px-5 py-4 text-[11px] text-slate-400 md:block">FE-F0-F1 · 本地演示数据</div>
          </aside>
          <main className="min-w-0 flex-1" id="main-content">
            <Routes>
              <Route path="/home" element={<ProductPlaceholder kind="home" />} />
              <Route path="/opportunities" element={<ProductPlaceholder kind="opportunities" />} />
              <Route path="/projects" element={<ProjectsPage />} />
              <Route path="/projects/:projectId" element={<ProjectPage />} />
              <Route path="/projects/:projectId/units/:unitId/production" element={<ProductionShellPage />} />
              <Route path="/production" element={<ProductPlaceholder kind="production" />} />
              <Route path="/review" element={<ProductPlaceholder kind="review" />} />
              <Route path="/identities" element={<ProductPlaceholder kind="identities" />} />
              <Route path="/assets" element={<ProductPlaceholder kind="assets" />} />
              <Route path="/learning" element={<ProductPlaceholder kind="learning" />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/sources" element={<Sources />} />
              <Route path="/connectors" element={<Connectors />} />
              <Route path="/fact-packs" element={<FactPacks />} />
              <Route path="/fact-packs/:id" element={<FactPacks />} />
              <Route path="/topics" element={<Topics />} />
              <Route path="/workspace" element={<Workspace />} />
              <Route path="/workspace/:topicId" element={<Workspace />} />
              <Route path="/legacy/review" element={<Review />} />
              <Route path="/legacy/assets" element={<Assets />} />
              <Route path="/handoff" element={<Handoff />} />
              <Route path="/workflows" element={<Workflows />} />
              <Route path="/templates" element={<Templates />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="*" element={<Navigate to="/home" replace />} />
            </Routes>
          </main>
        </div>
  );
}
