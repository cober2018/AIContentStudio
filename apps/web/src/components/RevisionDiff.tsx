/**
 * Revision Diff 视图：行级 LCS 对比「上一版 → 当前版」。
 * 行级而非字符级：中文长文按段落对比最直观，且 O(n·m) 可控。
 */
import { useMemo } from "react";

type Row = { type: "same" | "add" | "del"; text: string };

/** LCS 逐行对比：a 为旧版（del），b 为新版（add）。 */
export function diffLines(a: string, b: string): Row[] {
  const A = a.split("\n");
  const B = b.split("\n");
  const n = A.length;
  const m = B.length;
  // dp[i][j] = A[i:] 与 B[j:] 的 LCS 长度
  const dp: number[][] = Array.from({ length: n + 1 }, () => new Array(m + 1).fill(0));
  for (let i = n - 1; i >= 0; i--) {
    for (let j = m - 1; j >= 0; j--) {
      dp[i][j] = A[i] === B[j] ? dp[i + 1][j + 1] + 1 : Math.max(dp[i + 1][j], dp[i][j + 1]);
    }
  }
  const rows: Row[] = [];
  let i = 0;
  let j = 0;
  while (i < n && j < m) {
    if (A[i] === B[j]) {
      rows.push({ type: "same", text: A[i] });
      i++;
      j++;
    } else if (dp[i + 1][j] >= dp[i][j + 1]) {
      rows.push({ type: "del", text: A[i++] });
    } else {
      rows.push({ type: "add", text: B[j++] });
    }
  }
  while (i < n) rows.push({ type: "del", text: A[i++] });
  while (j < m) rows.push({ type: "add", text: B[j++] });
  return rows;
}

const ROW_STYLE: Record<Row["type"], string> = {
  same: "",
  add: "bg-emerald-50 text-emerald-900",
  del: "bg-rose-50 text-rose-700 line-through",
};
const ROW_MARK: Record<Row["type"], string> = { same: " ", add: "+", del: "−" };

export function RevisionDiff({ oldBody, newBody, oldLabel, newLabel }: {
  oldBody: string;
  newBody: string;
  oldLabel: string;
  newLabel: string;
}) {
  const rows = useMemo(() => diffLines(oldBody, newBody), [oldBody, newBody]);
  const changed = rows.filter((r) => r.type !== "same").length;

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="flex items-center gap-3 border-b border-slate-100 bg-slate-50 px-4 py-1.5 text-xs text-slate-500">
        <span>
          {oldLabel} → {newLabel}
        </span>
        <span className="text-emerald-600">+{rows.filter((r) => r.type === "add").length}</span>
        <span className="text-rose-600">−{rows.filter((r) => r.type === "del").length}</span>
        <span>（{changed} 处变动行）</span>
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto p-4 font-mono text-xs leading-relaxed">
        {rows.map((r, idx) => (
          <div key={idx} className={`flex gap-2 whitespace-pre-wrap rounded px-1 ${ROW_STYLE[r.type]}`}>
            <span className="select-none text-slate-400">{ROW_MARK[r.type]}</span>
            <span className="flex-1">{r.text || " "}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
