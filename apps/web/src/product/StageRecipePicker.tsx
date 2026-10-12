import { useEffect, useState } from "react";
import { api, ApiError } from "../api";
import { Button, ErrorBanner, Field, Spinner, inputClass } from "../components/ui";

type Option = { key: string; title: string; modality: string; definition_hash: string;
  definition: { nodes: { id: string; label?: string; plugin: string; config?: { instruction?: string } }[]; edges: { from: string; to: string }[]; visual_order: string[] } };
type Options = { items: Option[]; expected_revision: number; current_workflow_id: number | null; current_checksum: string | null };
type Adoption = { recipe_key: string; expected_definition_hash: string; expected_workflow_id: number | null; expected_revision: number; idempotency_key: string };

export default function StageRecipePicker({ base, readOnly, onBusy, onAdopted }: {
  base: string; readOnly: boolean; onBusy: (busy: boolean) => void; onAdopted: () => Promise<void>;
}) {
  const [options, setOptions] = useState<Options | null>(null);
  const [selectedKey, setSelectedKey] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const [pending, setPending] = useState<Adoption | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [refresh, setRefresh] = useState(0);
  useEffect(() => {
    let alive = true;
    setOptions(null); setConfirmed(false); setSelectedKey(""); setError("");
    api.get<Options>(`${base}/creation-recipe/options`).then(value => { if (alive) setOptions(value); })
      .catch(() => { if (alive) setError("可选流程暂不可读，请刷新清单。"); });
    return () => { alive = false; };
  }, [base, refresh]);
  const selected = options?.items.find(item => item.key === selectedKey);
  async function adopt() {
    if (readOnly || busy || !pending && (!selected || !options || !confirmed)) return;
    const request = pending || { recipe_key: selected!.key, expected_definition_hash: selected!.definition_hash,
      expected_workflow_id: options!.current_workflow_id, expected_revision: options!.expected_revision,
      idempotency_key: `recipe:${crypto.randomUUID()}` };
    setPending(request); setBusy(true); onBusy(true); setError("");
    let uncertain = false;
    try {
      const value = await api.post<{ workflow_id: number; revision: number }>(`${base}/creation-recipe/adopt-recipe`, request);
      setPending(null); setConfirmed(false); setNotice(`已选择流程 #${value.workflow_id} · 项目版本 ${value.revision}。`);
      try { await onAdopted(); } catch { setError("选择已提交，阶段回读暂时失败，请刷新流程。"); }
    } catch (cause) {
      uncertain = !(cause instanceof ApiError && cause.status < 500);
      if (!uncertain) { setPending(null); setConfirmed(false); }
      setError(uncertain ? "流程选择尚未确认。保留模板哈希、原目标版本和请求，只重试这次选择。" : "当前流程或模板版本已变化，请刷新清单并重新确认。");
    } finally { setBusy(false); onBusy(uncertain); }
  }
  return <section className="mt-4 rounded-xl border border-slate-200 bg-white p-4" aria-label="选择 Creation Recipe"><div className="flex justify-between gap-2"><h3 className="font-semibold">明确选择创作流程</h3><Button variant="secondary" size="sm" disabled={busy || Boolean(pending)} onClick={() => setRefresh(value => value + 1)}>刷新可选流程</Button></div>{!options && !error && <Spinner label="加载可选流程…" />}{options && <><Field label="选择模板"><select className={inputClass} disabled={readOnly || busy || Boolean(pending)} value={selectedKey} onChange={event => { setSelectedKey(event.target.value); setConfirmed(false); }}><option value="">请选择，不自动替换</option>{options.items.map(item => <option key={item.key} value={item.key}>{item.title} · {item.modality}</option>)}</select></Field>{selected && <div className="mt-3 rounded-lg bg-slate-50 p-3"><ol className="space-y-2 text-sm">{selected.definition.visual_order.map((id, index) => { const node = selected.definition.nodes.find(item => item.id === id); return <li key={id}>{index + 1}. {node?.label || id}<p className="mt-1 whitespace-pre-wrap text-xs text-slate-500">{node?.config?.instruction}</p></li>; })}</ol><p className="mt-3 text-xs text-slate-600">创建当前单元的新项目流程版本。已有运行保留原版本；独立的内容编辑和高级工作流草稿需各自明确保存。</p><label className="mt-3 flex items-start gap-2 text-sm"><input type="checkbox" checked={confirmed} disabled={readOnly || busy || Boolean(pending)} onChange={event => setConfirmed(event.target.checked)} /><span>确认选择“{selected.title}”，以当前项目版本 {options.expected_revision} 为基准创建新版本。</span></label></div>}</>}
    <Button className="mt-3" disabled={readOnly || busy || !pending && (!selected || !confirmed)} onClick={adopt}>{pending ? "重试原选择请求" : "确认选择此流程"}</Button>{notice && <p className="mt-3 text-xs text-emerald-700" role="status">{notice}</p>}{error && <div className="mt-3"><ErrorBanner message={error} /></div>}
  </section>;
}
