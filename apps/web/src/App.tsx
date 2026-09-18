import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Link, Navigate, Route, Routes, useLocation } from "react-router-dom";
import Assets from "./pages/Assets";
import Connectors from "./pages/Connectors";
import Dashboard from "./pages/Dashboard";
import Landing from "./pages/Landing";
import FactPacks from "./pages/FactPacks";
import Review from "./pages/Review";
import Settings from "./pages/Settings";
import Sources from "./pages/Sources";
import Templates from "./pages/Templates";
import Topics from "./pages/Topics";
import Workflows from "./pages/Workflows";
import Workspace from "./pages/Workspace";

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } },
});

const NAV = [
  { to: "/dashboard", label: "总览", icon: "◧" },
  { to: "/sources", label: "来源库", icon: "▤" },
  { to: "/connectors", label: "数据接入", icon: "⇄" },
  { to: "/fact-packs", label: "FactPack", icon: "▣" },
  { to: "/topics", label: "选题中心", icon: "✎" },
  { to: "/workspace", label: "内容任务", icon: "✍" },
  { to: "/review", label: "审核中心", icon: "✓" },
  { to: "/assets", label: "内容资产", icon: "◫" },
  { to: "/workflows", label: "工作流", icon: "◴" },
  { to: "/templates", label: "模板", icon: "⚙" },
  { to: "/settings", label: "设置", icon: "☰" },
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
        <div className="flex min-h-screen">
          <aside className="flex w-52 shrink-0 flex-col border-r border-slate-200 bg-white">
            <div className="px-5 py-5">
              <div className="text-base font-bold tracking-tight">AI Content Studio</div>
              <div className="mt-0.5 text-[11px] text-slate-400">事实驱动内容生产</div>
            </div>
            <nav className="flex-1 space-y-0.5 px-3">
              {NAV.map((item) => (
                <Link
                  key={item.to}
                  to={item.to}
                  className="flex items-center gap-2.5 rounded-md px-3 py-2 text-sm text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                >
                  <span className="w-4 text-center text-xs text-slate-400">{item.icon}</span>
                  {item.label}
                </Link>
              ))}
            </nav>
            <div className="px-5 py-4 text-[11px] leading-relaxed text-slate-400">
              Source → Fact → FactPack
              <br />
              → Topic → Draft → Check
              <br />
              → Review → Asset → Export
            </div>
          </aside>
          <main className="min-w-0 flex-1">
            <Routes>
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/sources" element={<Sources />} />
              <Route path="/connectors" element={<Connectors />} />
              <Route path="/fact-packs" element={<FactPacks />} />
              <Route path="/fact-packs/:id" element={<FactPacks />} />
              <Route path="/topics" element={<Topics />} />
              <Route path="/workspace" element={<Workspace />} />
              <Route path="/workspace/:topicId" element={<Workspace />} />
              <Route path="/review" element={<Review />} />
              <Route path="/assets" element={<Assets />} />
              <Route path="/workflows" element={<Workflows />} />
              <Route path="/templates" element={<Templates />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </main>
        </div>
  );
}
