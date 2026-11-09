import { useTaskLink } from "./taskNavigation";
import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api, ApiError } from "../api";
import { Button, ErrorBanner, Field, Spinner, StatusBadge, inputClass } from "../components/ui";
import { ModalityWorkspace } from "./ModalityWorkspace";
import { creativeIntentIssue, type CreativeIntent } from "./CreativeIntentEditor";
import type { VideoProductionSummary } from "./VideoShotMaterialPanel";
import type { VideoStudioView } from "./VideoStudioShell";
import type { VideoDraft } from "./VideoStudioModel";
import type { Unit } from "./project/projectTypes";
import ChannelIcon from "./ChannelIcon";

type Master = { id: number; revision_no: number; payload: Record<string, unknown>; payload_hash: string; context_hash: string; payload_schema: string; channel_id: string | null; content_form: string | null; identity_snapshot_id: number | null; creative_brief_revision_id: number | null; fact_boundary_revision_id: number | null; creative_intent?: CreativeIntent | null; assets: Record<string, unknown>[]; evidence: Record<string, unknown>[]; readiness: { state: string; reasons: string[] }; source_kind: string; edit_summary?: Record<string, unknown>; created_by?: string; created_at?: string };
type Readiness = { render_input_hash: string; context: { state: string; reasons: string[] }; render: Record<string, unknown>; preview: Record<string, unknown>; checks: { id: number | null; check_kind: string; status: string; is_current: boolean; report: Record<string, unknown> }[]; candidate_freeze_available: boolean; adapter_availability: { available: boolean; reasons: string[] } };
type VideoUpgradePreview = { payload: null; source_fields: { title: string | null; script: string | null; shots: { id: string; order: number }[] }; warnings: string[]; source_master_id: number; source_revision_no: number; source_payload_hash: string; current_context_hash: string };
type VideoDiffRow = { id: string; kind: string; changes?: string[]; track_id?: string };
type VideoDiff = { from_schema: string; to_schema: string; title: { changed: boolean }; aspect_ratio: { changed: boolean }; timeline_duration_ms: { changed: boolean }; script: VideoDiffRow[]; shots: VideoDiffRow[]; timeline_tracks: VideoDiffRow[]; timeline_items: VideoDiffRow[]; voice: { changed: boolean }; subtitles: VideoDiffRow[]; overlays: VideoDiffRow[]; music: { changed: boolean }; cover: { changed: boolean }; render_asset_ref: { changed: boolean }; assets: { changed: boolean }; evidence: { changed: boolean }; render: { changed: boolean }; context: { changed: boolean } };
const pretty = (value: unknown) => JSON.stringify(value, null, 2);
function message(cause: unknown) { return cause instanceof ApiError ? cause.status === 409 ? "409 · 内容版本或上下文已变化；请核对后重新加载，当前本地修改尚未保存。" : `${cause.status} · ${cause.message}` : cause instanceof Error ? cause.message : "请求失败"; }

export function ContentMasterPanel({ projectId, unit, readOnly: workspaceReadOnly, onOpenExecution, reloadRequest = 0, view, active = true, onStateChange, speechMode, productionSettingsDirty, assistantVisible = true, onAssistanceFocus, onProductionSummary }: { projectId: number; unit: Unit; readOnly: boolean; onOpenExecution?: () => void; reloadRequest?: number; view?: VideoStudioView; speechMode?: string; productionSettingsDirty?: boolean; assistantVisible?: boolean; onAssistanceFocus?: () => void; onProductionSummary?: (summary: VideoProductionSummary) => void; active?: boolean; onStateChange?: (state: { dirty: boolean; hasMaster: boolean; hasRender: boolean; readiness: string }) => void }) {
  const taskLink = useTaskLink();
  const readOnly = workspaceReadOnly || unit.status === "archived";
  const base = `/content-projects/${projectId}/units/${unit.id}`;
  const [params] = useSearchParams();
  const initialMasterSelection = useRef({ base, master: params.get("master") });
  const simple = view === "simple";
  const [more, setMore] = useState(false);
  const folded = simple && !more;
  const [initialMasterIssue, setInitialMasterIssue] = useState("");
  const [history, setHistory] = useState<Master[]>([]);
  const [selected, setSelected] = useState<Master | null>(null);
  const [readiness, setReadiness] = useState<Readiness | null>(null);
  const [videoDraft, setVideoDraft] = useState<VideoDraft | null>(null);
  const [videoUpgradeDraft, setVideoUpgradeDraft] = useState<VideoDraft | null>(null);
  const [videoUpgradePreview, setVideoUpgradePreview] = useState<VideoUpgradePreview | null>(null);
  const [videoUpgradeConfirmed, setVideoUpgradeConfirmed] = useState(false);
  const [form, setForm] = useState("");
  const [dirty, setDirty] = useState(false);
  const [contentDirty, setContentDirty] = useState(false);
  const [intentDraft, setIntentDraft] = useState<CreativeIntent | null>(null);
  const [intentDirty, setIntentDirty] = useState(false);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [acceptContext, setAcceptContext] = useState(false);
  const [candidateId, setCandidateId] = useState<number | null>(null);
  const [compareToId, setCompareToId] = useState("");
  const [videoDiff, setVideoDiff] = useState<VideoDiff | null>(null);
  const seenReloadRequest = useRef(reloadRequest);
  const current = history[0] || null;
  useEffect(() => { onStateChange?.({ dirty, hasMaster: !!current, hasRender: !!videoDraft?.payload.render_asset_ref, readiness: current?.readiness.state || "incomplete" }); }, [dirty, current?.id, current?.readiness.state, videoDraft?.payload.render_asset_ref, onStateChange]);
  const historical = !!selected && selected.id !== current?.id;
  const intentOnly = !!selected && intentDirty && !contentDirty && !videoUpgradeDraft;
  const intentIssue = intentDirty ? creativeIntentIssue(intentDraft) : "";
  const disabled = readOnly || historical || busy || !!initialMasterIssue || (!!selected && selected.payload_schema !== "video.master.v2");
  useEffect(() => {
    if (!dirty) return;
    const warn = (event: BeforeUnloadEvent) => { event.preventDefault(); event.returnValue = ""; };
    const guardLink = (event: MouseEvent) => {
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      const anchor = (event.target as Element | null)?.closest?.("a[href]");
      if (!anchor || anchor.getAttribute("target") === "_blank") return;
      const target = new URL((anchor as HTMLAnchorElement).href);
      if (target.origin !== window.location.origin || target.pathname === window.location.pathname && target.search === window.location.search) return;
      if (!window.confirm("离开会丢弃未保存的 Content Master 修改，继续？")) { event.preventDefault(); event.stopPropagation(); }
    };
    window.addEventListener("beforeunload", warn);
    document.addEventListener("click", guardLink, true);
    return () => { window.removeEventListener("beforeunload", warn); document.removeEventListener("click", guardLink, true); };
  }, [dirty]);

  async function select(master: Master | null) {
    setInitialMasterIssue("");
    setSelected(master); setReadiness(null); setDirty(false); setContentDirty(false); setAcceptContext(false);
    setIntentDraft(master?.creative_intent ?? null); setIntentDirty(false);
    setVideoDiff(null); setCompareToId("");
    setVideoUpgradeDraft(null); setVideoUpgradePreview(null); setVideoUpgradeConfirmed(false);
    setVideoDraft(null);
    const { createVideoDraft, videoDraftFromMaster } = await import("./VideoStudioModel");
    setVideoDraft(!master ? createVideoDraft() : master.payload_schema === "video.master.v2" ? videoDraftFromMaster(master) : null);
    setForm(master?.content_form || "");
    if (master) {
      setReadiness(await api.get<Readiness>(`${base}/master-revisions/${master.id}/readiness`));
    }
  }
  async function reload(initial = false) {
    const result = await api.get<{ items: Master[] }>(`${base}/master-revisions`);
    setHistory(result.items);
    const requested = initial ? initialMasterSelection.current.master : null;
    if (requested !== null) {
      const id = /^[1-9][0-9]*$/.test(requested) ? Number(requested) : NaN;
      const exact = Number.isSafeInteger(id) ? result.items.find(master => master.id === id) : undefined;
      if (!exact) {
        await select(null);
        setInitialMasterIssue("参考作品指定的主稿版本无效、不属于本作品或当前不可见。没有自动切换到最新版；请在版本历史中明确选择可见版本。");
        return;
      }
      await select(exact);
      return;
    }
    await select(result.items[0] || null);
  }
  useEffect(() => {
    if (initialMasterSelection.current.base !== base) initialMasterSelection.current = { base, master: params.get("master") };
    reload(true).catch((cause) => setError(message(cause))).finally(() => setLoading(false));
  }, [base]);
  useEffect(() => {
    if (seenReloadRequest.current === reloadRequest) return;
    seenReloadRequest.current = reloadRequest;
    if (dirty || busy || loading) {
      setNotice("已前往内容编辑器，保留当前本地修改；保存或明确重新加载后再读取 Recipe 接受的新版本。");
      return;
    }
    void execute(reload);
  }, [reloadRequest, dirty, busy, loading]);
  function change(set: (value: string) => void, value: string) { set(value); setDirty(true); setContentDirty(true); setNotice(""); }
  function changeVideo(value: VideoDraft) { if (value === (videoUpgradeDraft || videoDraft)) return; if (videoUpgradeDraft) setVideoUpgradeDraft(value); else setVideoDraft(value); setDirty(true); setContentDirty(true); setNotice(""); }
  function changeIntent(value: CreativeIntent) { setIntentDraft(value); setIntentDirty(true); setDirty(true); setNotice(""); }
  async function execute(action: () => Promise<void>) { setBusy(true); setError(""); setNotice(""); try { await action(); } catch (cause) { setError(message(cause)); } finally { setBusy(false); } }
  async function save(attest = false) {
    await execute(async () => {
      if (readOnly || historical || busy) return;
      if (intentIssue) throw new Error(intentIssue);
      if (!intentOnly && !videoDraft) throw new Error("旧版 Video Master 需先显式升级");
      const draft = intentOnly ? {
        payloadSchema: selected!.payload_schema, payload: selected!.payload,
        assetRefs: selected!.assets.map((row) => ({ material_revision_id: row.material_revision_id, content_hash: row.content_hash, role: row.role, slot_key: row.slot_key, sort_order: row.sort_order, placement: row.placement })),
        evidenceRefs: selected!.evidence.map((row) => ({ fact_pack_item_id: row.fact_pack_item_id, snapshot_checksum: row.snapshot_checksum, role: row.role, locator: row.locator, sort_order: row.sort_order })),
      } : videoDraft!;
      await api.post(`${base}/master-revisions`, {
        expected_revision: current?.revision_no || 0,
        expected_context_hash: current && !acceptContext ? current.context_hash : undefined,
        idempotency_key: crypto.randomUUID(), parent_revision_id: current?.id,
        payload_schema: draft.payloadSchema, payload: draft.payload, content_form: form || null,
        asset_refs: draft.assetRefs, evidence_refs: draft.evidenceRefs,
        ...(intentDirty ? { creative_intent: intentDraft } : {}),
        edit_summary: !intentOnly && videoDraft?.asrReceiptId ? { asr_receipt_id: videoDraft.asrReceiptId } : {},
        render_attestation: attest && readiness ? { confirmed: true, render_input_hash: readiness.render_input_hash } : undefined,
      });
      await reload(); setNotice("已保存新的不可变 Master 修订；Workflow 草稿未修改。");
    });
  }
  return <section className={active ? "mb-5 rounded-2xl border border-slate-200 bg-white p-5" : ""} aria-label="Content Master">
    {active && <div className="flex flex-wrap items-center justify-between gap-3"><h2 className="text-lg font-semibold">{view === "goal" ? "本条创作目标" : "作品主稿"}</h2><span className="text-xs text-slate-500">{dirty ? "内容有未保存修改" : "内容已同步"} · 与 Workflow 保存独立</span></div>}
    {loading ? <Spinner label="读取 Master…" /> : <div className={`mt-4 space-y-4${folded ? " [&>*:not([data-main])]:hidden" : ""}`}>
      <div data-main className="space-y-2 empty:hidden">{initialMasterIssue && <ErrorBanner message={initialMasterIssue} />}{error && <ErrorBanner message={error} />}{notice && <p role="status" className="text-sm text-emerald-700">{notice}</p>}</div>
      {active && <details><summary className="cursor-pointer text-sm text-slate-600">主稿版本与历史（历史版本只读）</summary><div className="mt-2 flex flex-wrap gap-2"><Button variant="secondary" disabled={busy} onClick={() => { if (!dirty || window.confirm("重新加载会丢弃未保存的内容编辑，继续？")) execute(reload); }}>重新加载 Master</Button>{history.map((row) => <Button key={row.id} variant={selected?.id === row.id ? "primary" : "secondary"} size="sm" disabled={busy} onClick={() => { if (!dirty || window.confirm("切换版本会丢弃未保存的内容编辑，继续？")) execute(() => select(row)); }}>Master v{row.revision_no}{row.id === current?.id ? " · 当前" : " · 历史"}</Button>)}</div></details>}
      {active && selected && <details className="rounded-lg bg-slate-50 p-3 text-xs text-slate-600"><summary className="cursor-pointer">已保存主稿的精确版本与来源</summary><div><p>Master #{selected.id} · {selected.payload_schema} · {selected.source_kind} · {selected.created_by || "作者未知"} · {selected.created_at || "时间未知"}</p><p className="break-all">Payload {selected.payload_hash} / Context {selected.context_hash}</p><p>Identity #{selected.identity_snapshot_id ?? "缺失"} · Brief #{selected.creative_brief_revision_id ?? "缺失"} · Boundary #{selected.fact_boundary_revision_id ?? "缺失"} · AI 编辑 {Array.isArray((selected.edit_summary?.ai_provenance as { edits?: unknown[] } | undefined)?.edits) ? (selected.edit_summary?.ai_provenance as { edits: unknown[] }).edits.length : 0}</p><StatusBadge status={selected.readiness.state} />{selected.readiness.reasons.length > 0 && <p>{selected.readiness.reasons.join("、")}</p>}</div></details>}
      {historical && <p className="text-sm text-amber-800">历史 Master 只读；选择当前版本后再创建新修订。</p>}
<div data-main={simple ? undefined : true}><ModalityWorkspace modality="video" isProduct={unit.production_domain === "product"} onProductionSummary={onProductionSummary} assistantVisible={assistantVisible} onAssistanceFocus={onAssistanceFocus} speechMode={speechMode} productionSettingsDirty={productionSettingsDirty} view={active ? view : "none"} more={more} creativeIntent={intentDraft} onIntentChange={changeIntent} onOpenExecution={onOpenExecution} projectId={projectId} unitId={unit.id} masterId={selected?.payload_schema === "video.master.v2" ? selected.id : null} masterHash={selected?.payload_schema === "video.master.v2" ? selected.payload_hash : null} savedSourceIds={Array.from(new Set((selected?.assets || []).filter((row) => ["voice_audio", "music_audio", "timeline_media", "shot_source"].includes(String(row.role))).map((row) => Number(row.material_revision_id))))} dirty={dirty} draft={videoUpgradeDraft || videoDraft} legacyPayload={selected?.payload} upgradeMode={!!videoUpgradeDraft} onChange={changeVideo} readOnly={videoUpgradeDraft ? readOnly || historical || busy : disabled} /></div>
      {active && <><details><summary className="cursor-pointer text-sm text-slate-600">版本详情与高级检查</summary><div className="mt-3 space-y-4"><div className="grid gap-3 sm:grid-cols-2"><Field label="渠道内容形态（留空由 Registry 解析）"><input aria-label="Master 内容形态" className={inputClass} value={form} disabled={disabled} onChange={(event) => change(setForm, event.target.value)} /></Field><p className="self-center text-xs text-slate-500">渠道：<ChannelIcon channel={unit.channel_id} className="mr-1" />{unit.channel_id || "未选择，不能冻结"}。素材来自项目共享素材，可跨 Unit 引用；不复制字节。</p></div>
      {selected?.payload_schema === "video.master.v2" && <div className="space-y-3 rounded-lg border border-slate-200 p-3"><h3 className="font-medium">Video Master 不可变版本与差异</h3><p className="text-xs">比较稳定脚本/镜头/轨道/片段/字幕/叠字 ID，不计算整片视频的伪文字相似度。</p><div className="flex flex-wrap gap-2"><select aria-label="对比 Video Master 版本" className={inputClass} value={compareToId} onChange={(event) => setCompareToId(event.target.value)}><option value="">选择另一个 Video v2 版本</option>{history.filter((row) => row.id !== selected.id && row.payload_schema === "video.master.v2").map((row) => <option key={row.id} value={row.id}>v{row.revision_no} · {row.source_kind}</option>)}</select><Button variant="secondary" disabled={!compareToId || busy} onClick={() => execute(async () => setVideoDiff(await api.get<VideoDiff>(`${base}/master-revisions/${selected.id}/diff?compare_to_id=${compareToId}`)))}>查看结构化差异</Button></div>{videoDiff && <div className="space-y-1 text-xs"><p>标题：{videoDiff.title.changed ? "变化" : "未变"} · 画幅：{videoDiff.aspect_ratio.changed ? "变化" : "未变"} · 总时长：{videoDiff.timeline_duration_ms.changed ? "变化" : "未变"}</p>{(["script", "shots", "timeline_tracks", "timeline_items", "subtitles", "overlays"] as const).map((field) => <div key={field}><strong>{field}：{videoDiff[field].length} 处</strong>{videoDiff[field].length > 0 && <ul className="list-disc pl-5">{videoDiff[field].map((row, index) => <li key={`${row.id}-${index}`}>{row.id} · {row.kind} · {row.changes?.join("/") || ""}{row.track_id ? ` · 轨道 ${row.track_id}` : ""}</li>)}</ul>}</div>)}<p>配音：{videoDiff.voice.changed ? "变化" : "未变"} · 音乐：{videoDiff.music.changed ? "变化" : "未变"} · 封面：{videoDiff.cover.changed ? "变化" : "未变"} · 最终成片：{videoDiff.render_asset_ref.changed ? "变化" : "未变"}</p><p>素材：{videoDiff.assets.changed ? "变化" : "未变"} · 证据：{videoDiff.evidence.changed ? "变化" : "未变"} · 渲染证明：{videoDiff.render.changed ? "变化" : "未变"} · 上下文：{videoDiff.context.changed ? "变化" : "未变"}</p></div>}</div>}
      {selected?.payload_schema === "video.master.v1" && selected.id === current?.id && <div className="space-y-3 rounded-lg border border-amber-200 bg-amber-50 p-3"><h3 className="font-medium">Video v1 → v2 显式升级</h3><p className="text-sm">旧脚本和镜头 ID/顺序保留；旧稿无法证明画幅、镜头时长和时间线。预览不会自动生成可冻结的 v2，也不会继承旧最终成片。</p>
        <Button variant="secondary" disabled={readOnly || historical || busy || dirty} onClick={() => execute(async () => { const preview = await api.get<VideoUpgradePreview>(`${base}/master-revisions/${selected.id}/video-v2-upgrade-preview`); const { videoUpgradeDraftFromPreview } = await import("./VideoStudioModel"); setVideoUpgradePreview(preview); setVideoUpgradeDraft(videoUpgradeDraftFromPreview(preview.source_fields)); setVideoUpgradeConfirmed(false); })}>预览 Video v1 → v2</Button>
        {videoUpgradePreview?.source_master_id === selected.id && <div className="space-y-2 text-sm"><p>来源 v{videoUpgradePreview.source_revision_no} · {videoUpgradePreview.source_fields.shots.length} 个已存镜头。上方编辑器中的画幅、每镜头 1000 ms 和时间线仅是填写起点，须亲自核对。</p><ul className="list-disc pl-5">{videoUpgradePreview.warnings.map((warning) => <li key={warning}>{warning}</li>)}</ul><label className="flex items-start gap-2"><input type="checkbox" checked={videoUpgradeConfirmed} disabled={readOnly || busy} onChange={(event) => setVideoUpgradeConfirmed(event.target.checked)} /><span>我已核对并提交完整画幅、镜头时长、时间线和精确引用，接受上述不可推断信息及全部转换警告；旧 Master/旧 Candidate 保持不变。</span></label><Button disabled={readOnly || historical || busy || !videoUpgradeConfirmed || !videoUpgradeDraft || selected.readiness.state === "stale"} onClick={() => execute(async () => { await api.post(`${base}/master-revisions/${selected.id}/video-v2-upgrade`, { expected_revision: selected.revision_no, expected_payload_hash: videoUpgradePreview.source_payload_hash, expected_context_hash: videoUpgradePreview.current_context_hash, idempotency_key: crypto.randomUUID(), payload: videoUpgradeDraft!.payload, asset_refs: videoUpgradeDraft!.assetRefs, evidence_refs: videoUpgradeDraft!.evidenceRefs, acknowledged_warnings: videoUpgradePreview.warnings }); await reload(); setNotice("已显式追加 Video v2 修订；旧 v1 及历史 Candidate 保持只读。"); })}>确认升级并追加 Video v2 修订</Button></div>}
      </div>}
      </div></details>
      {selected?.readiness.state === "stale" && <label className="flex items-center gap-2 text-sm text-amber-800"><input type="checkbox" disabled={readOnly || historical || busy || (!intentOnly && disabled)} checked={acceptContext} onChange={(event) => setAcceptContext(event.target.checked)} />明确接纳最新项目上下文，保存为新修订（历史不改写）</label>}
      <div data-main={simple ? undefined : true} className="flex flex-wrap gap-2"><Button disabled={!dirty || readOnly || historical || busy || !!intentIssue || (!intentOnly && (disabled || !videoDraft)) || (selected?.readiness.state === "stale" && !acceptContext)} onClick={() => save()}>保存当前主稿</Button>{!folded && <><Button variant="secondary" disabled={disabled || dirty || !selected || selected.readiness.state === "stale"} onClick={() => execute(async () => { await api.post(`${base}/master-revisions/${selected!.id}/checks`); await reload(); setNotice("Master 检查已持久化；旧检查不覆盖。"); })}>运行 Master 检查</Button><Button disabled={disabled || dirty || !readiness?.candidate_freeze_available || !selected} onClick={() => execute(async () => { const frozen = await api.post<{ id: number }>(`${base}/candidates/freeze`, { content_master_revision_id: selected!.id, expected_payload_hash: selected!.payload_hash }); setCandidateId(frozen.id); setNotice(`已冻结 Candidate v4 #${frozen.id}，尚未审批。`); })}>冻结 Master Candidate v4</Button>{candidateId && <Link className="self-center text-sm text-indigo-700 underline" to={taskLink(`/review?project=${projectId}&unit=${unit.id}&candidate=${candidateId}`)}>审阅 Candidate #{candidateId}</Link>}</>}</div>
      <Button variant="secondary" disabled={disabled || dirty || !selected || !readiness || selected.readiness.state !== "current" || !videoDraft?.payload.render_asset_ref} onClick={() => { if (window.confirm("确认当前 render_output 的真实字节是此 Master 的最终渲染？确认会保存带输入哈希证明的新修订。")) save(true); }}>确认真实 MP4 与当前输入一致并保存新修订</Button>
      {readiness && <details className="rounded-lg border border-slate-200 p-3"><summary className="cursor-pointer text-sm font-medium">Master 当前检查与渲染 · {readiness.candidate_freeze_available ? "可冻结" : "不可冻结"}{readiness.adapter_availability.reasons.length > 0 ? ` · ${readiness.adapter_availability.reasons[0]}` : ""}</summary><p className="mt-2 text-xs text-slate-500">{readiness.adapter_availability.reasons.join("、")}</p><div className="mt-2 flex flex-wrap gap-2">{readiness.checks.map((row) => <span key={row.check_kind} className="text-xs">{row.check_kind}: <StatusBadge status={row.status} /></span>)}</div><pre className="mt-3 max-h-56 overflow-auto rounded bg-slate-50 p-3 text-xs">{pretty({ preview: readiness.preview, render: readiness.render, checks: readiness.checks })}</pre></details>}
      </>}
      {simple && active && <button data-main type="button" aria-expanded={more} className="w-full rounded-xl border border-slate-200 bg-white/70 p-3 text-left text-sm text-slate-600 hover:border-slate-300" onClick={() => setMore(value => !value)}>{more ? "▾ 收起更多" : "▸ 更多：编辑主稿、逐镜素材、导演包、版本与检查、字幕、时间线、ASR"}</button>}
    </div>}
  </section>;
}
