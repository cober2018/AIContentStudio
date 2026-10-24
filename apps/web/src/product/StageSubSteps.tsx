import { useSearchParams } from "react-router-dom";
import type { RecipeSummary } from "./CreationRecipePanel";

function statusText(stage: RecipeSummary["stages"][number], isNext: boolean) {
  if (stage.accepted) return "已采用";
  if (stage.status === "skipped") return "已跳过";
  if (stage.status === "running") return "AI 正在做";
  if (stage.status === "waiting_input") return "等你确认";
  if (["blocked", "failed", "stale", "unknown"].includes(stage.status)) return "需要处理";
  return isNext ? "可以开始" : "等前一步";
}

// The workflow stages are what actually gate the work, so they sit in the nav and the one needing the user stands out.
export function StageSubSteps({ summary }: { summary: RecipeSummary }) {
  const [params, setParams] = useSearchParams();
  const nextId = summary.next.kind === "done" ? null : summary.next.nodeId;
  const current = params.get("workstep") === "plan" ? params.get("stage") : null;
  function go(nodeId: string, open: boolean) {
    setParams(previous => {
      const next = new URLSearchParams(previous);
      next.set("workstep", "plan"); next.set("stage", nodeId);
      if (open) next.set("open", "result"); else next.delete("open");
      return next;
    }, { replace: true });
    document.getElementById("production-planning")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }
  return <ol className="mb-1 ml-[42px] mr-1 space-y-0.5" aria-label="内容方案阶段">{summary.stages.map(stage => {
    const isNext = stage.nodeId === nextId;
    const text = statusText(stage, isNext);
    const mark = stage.accepted || stage.status === "skipped" ? "✓" : isNext ? "●" : "○";
    const urgent = isNext && (stage.status === "waiting_input" || text === "需要处理");
    return <li key={stage.nodeId}><button type="button" aria-current={current === stage.nodeId ? "step" : undefined}
      onClick={() => go(stage.nodeId, stage.status === "waiting_input")}
      className={`flex w-full items-baseline gap-2 rounded-lg px-2 py-1.5 text-left text-[12.5px] ${isNext ? "bg-rose-50 ring-1 ring-rose-200" : current === stage.nodeId ? "bg-ink-50" : "hover:bg-ink-50/70"}`}>
      <span aria-hidden className={`w-3 shrink-0 ${stage.accepted ? "text-emerald-600" : isNext ? "text-rose-600" : "text-ink-300"}`}>{mark}</span>
      <span className="min-w-0 flex-1"><span className={`block ${isNext ? "font-semibold text-ink-900" : "text-ink-700"}`}>{stage.label}</span>
        <span className={`block text-[11.5px] ${urgent ? "font-semibold text-rose-700" : "text-ink-500"}`}>{text}</span></span>
    </button></li>;
  })}</ol>;
}
