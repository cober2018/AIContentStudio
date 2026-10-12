import { useEffect, useRef, useState } from "react";
import { api, currentUser } from "../api";
import { Button, ErrorBanner, Spinner } from "../components/ui";

type Master = { id: number; revision_no: number; payload_schema: string; payload_hash: string;
  payload: { canvases?: { id: string; width: number; height: number }[];
    render_asset_ref?: { canvas_id: string; material_revision_id: number }[] } };
type Readiness = { master_revision_id: number; context: { state: string; reasons: string[] };
  render: { status: string; canvas_dimensions_verified?: boolean; reasons?: string[]; outputs?: { canvas_id: string; material_revision_id: number; content_hash: string }[] };
  candidate_freeze_available: boolean };

export default function GraphicRecipeReadiness({ base, readOnly, onOpenMaster }: {
  base: string; readOnly: boolean; onOpenMaster: () => void;
}) {
  const [value, setValue] = useState<{ master: Master; readiness: Readiness } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const generation = useRef(0);
  const mounted = useRef(false);
  const actor = currentUser();
  async function refresh() {
    const token = ++generation.current;
    const live = () => mounted.current && generation.current === token && currentUser() === actor;
    setLoading(true); setError(""); setValue(null);
    try {
      const master = await api.get<Master | null>(`${base}/master-revisions/current`);
      if (!live()) return;
      if (!master) { setError("先明确接受排版候选为 Graphic Master，再渲染真实图片。"); return; }
      if (master.payload_schema !== "graphic.master.v2") throw new Error("当前不是 Graphic v2；先在内容编辑器显式升级，不会隐式迁移历史稿。");
      const readiness = await api.get<Readiness>(`${base}/master-revisions/${master.id}/readiness`);
      const latest = await api.get<Master | null>(`${base}/master-revisions/current`);
      if (!live()) return;
      if (!latest || latest.id !== master.id || latest.payload_hash !== master.payload_hash || readiness.master_revision_id !== master.id) {
        throw new Error("读取期间 Master 已变化；重新读取当前状态，不使用旧画布结果。");
      }
      setValue({ master, readiness });
    } catch (cause) { if (live()) setError(cause instanceof Error ? cause.message : "图文状态读取失败，不能认定渲染完成。"); }
    finally { if (live()) setLoading(false); }
  }
  useEffect(() => {
    mounted.current = true;
    void refresh();
    return () => { mounted.current = false; generation.current += 1; };
  }, [base, actor]);
  return <section className="mt-3 space-y-3 rounded-xl border border-indigo-200 bg-indigo-50/40 p-3" aria-label="Recipe 图文成品承接">
    <h4 className="text-sm font-medium">真实 PNG → 图文质量确认</h4>
    <p className="text-xs text-slate-600">排版候选只是内容。逐画布渲染、查看并接受真实素材、绑定到本地画布，明确保存 Master 后再确认当前渲染并运行本阶段质量检查。</p>
    <div className="flex flex-wrap gap-2"><Button size="sm" variant="secondary" disabled={loading || readOnly} onClick={onOpenMaster}>前往图文编辑器渲染 / 接受 / 保存</Button><Button size="sm" variant="secondary" disabled={loading} onClick={() => void refresh()}>读取当前成品状态（不渲染）</Button></div>
    {loading && <Spinner label="读取保存的画布与真实渲染…" />}
    {error && <ErrorBanner message={error} />}
    {value && <div className="space-y-2 text-xs"><p>Master #{value.master.id} v{value.master.revision_no} · 上下文 {value.readiness.context.state}</p>
      <p>{value.readiness.render.status === "ready" ? "服务端已验证全部画布的真实图片与当前输入绑定；仍不代表审美或用户验收通过。" : `尚未完成真实渲染：${value.readiness.render.reasons?.join("、") || "未就绪"}`}</p>
      {value.readiness.context.reasons.length > 0 && <p className="text-amber-800">{value.readiness.context.reasons.join("、")}</p>}
      <ul className="space-y-1">{value.master.payload.canvases?.map((canvas, index) => {
        const bound = value.master.payload.render_asset_ref?.find(ref => ref.canvas_id === canvas.id);
        const verified = value.readiness.render.status === "ready" && value.readiness.render.outputs?.find(ref => ref.canvas_id === canvas.id && ref.material_revision_id === bound?.material_revision_id);
        return <li key={canvas.id}>{index + 1}. {canvas.width}×{canvas.height} · {bound ? `素材版本 #${bound.material_revision_id}` : "未绑定真实图片"} · {verified ? value.readiness.render.canvas_dimensions_verified ? "字节 / 哈希 / 尺寸已验证" : "原渲染凭据已验证；未执行 Persona 尺寸检查" : "尚未验证当前渲染"}</li>;
      })}</ul>
      <p className="text-slate-500">只读投影；打开编辑器不会覆盖已有本地内容。画布或素材变化后重新 Preview / 运行检查，不复用旧结果。</p>
    </div>}
  </section>;
}
