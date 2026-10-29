import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState, type FormEvent } from "react";
import { api, ApiError, currentUser } from "../api";
import { Button, ErrorBanner, Field, Modal, Spinner, inputClass } from "../components/ui";

type CatchupReceipt = { id: number; source_id: number; name: string | null; persona_ids: number[]; start_at: string | null; end_at: string; status: string; reason: string | null; counts: { scanned?: number; new_versions?: number; requests?: number }; coverage: { complete?: boolean; unconfirmed_interval?: { start_at: string | null; end_at: string; missing_count: number | null } | null }; finished_at: string | null; earlier_gap?: CatchupReceipt | null };
type CollectionSnapshot = { status: string; frozen_at: string; target_at?: string; notice?: string; sources: CatchupReceipt[] };
export type DiscoveryStatus = { catchup?: CatchupReceipt[]; settings: { enabled: boolean; paused_persona_ids: number[]; search_provider: string; public_processing_allowed: boolean; search_configured: boolean; worker_enabled: boolean; daily_hour: number; daily_limit: number }; personas: { persona_id: number; business_date?: string; opportunity_policy?: "technology.v1" | "discovery.v2"; collection_mode?: string; name: string; status: string; reason: string | null; next_due_at: string | null; today_run?: Run | null; last_run: Run | null; radar?: Radar | null }[] };
type Source = { aggregate_mode_paused_for?: number[]; aggregate_sync?: { phase?: string; synced_at?: string; has_more?: boolean } | null; id: number; name: string; url: string; input_url: string; collector_url: string | null; kind: string; origin: string; status: string; reason: string | null; manually_paused: boolean; processing_allowed: boolean; last_success_at: string | null; persona_ids: number[]; personas: { id: number; name: string; state: string }[]; validation: { state?: string }; merged_into?: number | null; alias_notice?: { message: string } | null; catchup?: { latest: CatchupReceipt | null; last_gap: CatchupReceipt | null } };
type SourceDraft = { name?: string; kind?: string; persona_ids: number[]; manually_paused: boolean; processing_allowed: boolean; url?: string };
type Persona = { id: number; name: string; status: string };
const sourceBase = "/content-opportunities/discovery/sources";
const origins: Record<string, string> = { manual: "手动添加", automatic: "自动发现", both: "手动 + 自动", seed: "初始储备", unknown: "既有来源" };
type Radar = { status: string; source_id?: number | null; reason?: string | null };
type RadarConfig = { enabled?: boolean; auto_daily?: boolean; report_path?: string | null; producer_version?: string | null; producer_revision?: string | null };
type RadarSettings = Radar & { persona_id: number; config: RadarConfig; generation?: { business_date: string; status: string; reason?: string; finished_at?: string } | null; counts: Record<string, number> | null; issues: string[] | null; last_imported_at: string | null; report_hash: string | null; availability_checked: false };
const radarBase = "/content-opportunities/discovery/radar";
const isRadarSource = (source: Source) => source.kind === "local_report" || source.url.startsWith("radar://");
const diagnosticCounts = {
  eligible_items: "可参与选题的线索（项）", body_reads_succeeded: "正文读取成功（项）", body_reads_failed: "正文读取失败（项）",
  budget_unexamined_items: "受预算限制未分析（项）", proposed_candidates: "生成候选（个）", pre_score_rejected: "证据 / 类型未通过（个）",
  scored_candidates: "进入评分（个）", score_rejected: "评分未通过（个）", deduplicated_candidates: "重复候选排除（个）",
  source_cap_excluded: "来源主体上限排除（个）", daily_cap_excluded: "每日上限排除（个）", persisted_opportunities: "已保存机会（条）",
};
type Diagnostics = { version: string | null; policy_version: string | null; counts: Partial<Record<keyof typeof diagnosticCounts, number | null>>; rejections: { candidate_id: string | number; title: string; stage: string; reason: string }[] };
type Run = { diagnostics?: Diagnostics | null; radar?: Radar | null; collection_notice?: string | null; collection_snapshot?: CollectionSnapshot | null; collection_target_at?: string | null; id: number; persona_id: number; status: string; reason: string | null; business_date: string; kind: string; summary?: { count?: number } | null; finished_at: string | null };
const labels: Record<string, string> = { aggregate_retry_wait: "等待上游允许重试", aggregate_rate_limited: "上游限流，按指定时间等待", aggregate_evidence_withdrawn: "冻结证据已被上游撤选，停止新生成", aggregate_sync_incomplete: "聚合精选尚未同步完整，将继续补读", aggregate_snapshot_required: "增量需重建快照", waiting_collection: "正在补采，今日选题等待中", catchup_coverage_incomplete: "补采存在缺口", collection_entry_unverified: "尚未确认持续采集入口", pending_validation: "等待后台验证", pending: "等待后台验证", complete: "验证通过", ready: "可用于选题", selected: "已关联", persona_ineligible: "角色已归档或定位待完善", persona_paused: "角色或自动研究已暂停", source_paused: "来源已暂停", processing_not_allowed: "尚未允许模型分析", source_unvalidated: "等待来源验证", capacity_pending: "活跃来源已满，等待空位", no_usable_article_body: "暂无可用正文", no_grounded_candidates: "没有证据充分的选题", article_read_incomplete: "部分正文读取失败", daily_limit_reached: "本角色今日选题额度已完成", positioning_incomplete: "待完善角色定位", paused: "已暂停", search_unavailable: "搜索未就绪", worker_not_enabled: "后台任务尚未启用", public_processing_not_allowed: "尚未允许公开资料分析", not_yet_due: "尚未到执行时间", queued: "等待后台研究", running: "正在研究", succeeded: "已完成", partial: "部分来源不可用", failed: "研究失败", unknown: "调用结果待核对", blocked: "需要处理依赖", candidate: "待验证来源", active: "可持续采集", adapter_unavailable: "当前入口无法采集", source_validation_failed: "本次访问未通过", source_collection_failed: "本次采集失败", source_dates_unverified: "来源时间未核实", credential_required: "需要登录凭据", pending_revalidation: "等待重新核验", no_usable_source_evidence: "暂无可用来源证据", fewer_qualifying_topics: "合适选题不足目标数量", provider_outcome_unknown: "模型结果待核对" };
const reasonLabels: Record<string, string> = {
  no_suitable_events: "没有符合类型要求的事件", research_processing_failed: "研究处理失败，请查看批次状态后再处理",
  recovered_committed_outputs: "已恢复此前保存的结果", timeline_missing: "未提供可核对的时间依据",
  supporting_evidence_missing: "缺少可核对的正文引文", classification_invalid: "选题类型无效",
  recent_date_unverified_or_outside_window: "原文或事件日期未核实，或已超出该类型的时间范围",
  lasting_value_missing: "未说明持久技术价值", candidate_schema_invalid: "候选信息不完整或格式无效",
  future_source_date: "来源日期晚于本批评估时间", candidate_response_invalid: "候选生成结果格式无效",
  score_below_threshold_or_ungrounded: "评分未达门槛或正文证据未通过核验",
  duplicate_topic: "与已有选题重复", source_actor_limit: "已达同一来源主体上限",
  radar_unconfigured: "Radar 尚未配置", radar_source_unconfigured: "Radar 尚未配置",
  radar_producer_binding_invalid: "自动生成只支持已核验的本机Radar版本和report.json路径",
  radar_producer_not_installed: "本机Radar或Python3.12入口不可用", radar_producer_version_changed: "Radar代码版本变化，请重新核验",
  radar_generation_failed: "日报生成失败，今日不自动重试", radar_generation_sources_failed: "GitHub与HF采集均失败",
  radar_generation_timeout: "日报生成超时，结果未知，今日不自动重试", radar_generation_interrupted: "生成中断，结果未知，今日不自动重试",
  radar_generation_unknown: "日报生成结果未知", radar_generation_busy: "日报正在生成，请等待后台处理",
  radar_generated_report_changed: "日报与当天生成回执不一致，已停止使用",
  radar_absolute_json_path_required: "请输入服务所在机器上的 JSON 文件绝对路径",
  radar_regular_file_required: "日报路径必须指向普通文件", radar_report_unavailable: "无法读取日报，请检查文件路径和读取权限",
  radar_report_too_large: "日报文件超过允许大小", radar_report_invalid_json: "日报不是有效的 JSON",
  radar_daily_schema_invalid: "日报结构不符合要求", radar_lead_invalid: "日报线索字段不符合要求",
  radar_producer_version_required: "启用时请填写生成器版本", radar_producer_version_invalid: "版本仅支持字母、数字、下划线、点、加号和连字符，最长 80 字符",
  radar_producer_revision_invalid: "commit 必须是 40 位十六进制字符", radar_producer_confirmation_required: "生成器版本尚未确认，当前后端要求版本确认后才能启用",
  radar_technology_only: "Radar 仅支持科技角色", radar_persona_ineligible: "角色定位尚未就绪",
  radar_source_missing: "已配置的 Radar 来源不存在", radar_source_mismatch: "Radar 来源与当前角色不匹配",
  radar_processing_paused: "Radar 来源采集或分析已暂停", radar_source_disabled: "Radar 来源未启用",
  radar_subscription_ineligible: "Radar 角色订阅不可用", radar_partial: "日报存在未解析线索或部分来源缺口",
};
export const discoveryLabel = (value: string | null | undefined) => !value ? "未记录" :
  Object.prototype.hasOwnProperty.call(labels, value) ? labels[value] :
  Object.prototype.hasOwnProperty.call(reasonLabels, value) ? reasonLabels[value] : "未识别的状态或原因，请核对运行记录";

export function useDiscoveryStatus() {
  const user = currentUser();
  return useQuery({ queryKey: ["discovery-status", user], queryFn: () => api.get<DiscoveryStatus>("/content-opportunities/discovery/status"), refetchInterval: 30000 });
}

function RadarView({ radar }: { radar: Radar | null | undefined }) {
  const radarLabels: Record<string, string> = { unconfigured: "未配置", disabled: "未启用", unavailable: "不可用", ready: "已注册，等待后台读取", synced: "已同步", partial: "部分线索或来源有缺口" };
  return <p className="text-xs text-slate-600">Radar：{radar ? Object.prototype.hasOwnProperty.call(radarLabels, radar.status) ? radarLabels[radar.status] : discoveryLabel(radar.status) : "未记录"}{radar?.source_id != null ? ` · 来源 ${radar.source_id}` : ""}{radar?.reason ? ` · ${discoveryLabel(radar.reason)}` : ""}</p>;
}

function RadarConfiguration({ personaId, editable, initiallyOpen = false }: { personaId: number; editable: boolean; initiallyOpen?: boolean }) {
  const user = currentUser(), client = useQueryClient();
  const [open, setOpen] = useState(initiallyOpen);
  const [draft, setDraft] = useState<RadarConfig | null>(null);
  const [validationError, setValidationError] = useState("");
  const [notice, setNotice] = useState("");
  const [producerVerified, setProducerVerified] = useState(false);
  const key = ["discovery-radar", user, personaId];
  const query = useQuery({ queryKey: key, queryFn: ({ signal }) => api.get<RadarSettings>(`${radarBase}?persona_id=${personaId}`, signal), enabled: open });
  const config = draft ?? query.data?.config ?? {};
  const save = useMutation({ mutationFn: (body: { persona_id: number; enabled: boolean; auto_daily: boolean; report_path?: string; producer_version?: string; producer_revision?: string; producer_verified: boolean }) => api.put<RadarSettings>(radarBase, body),
    onSuccess: async result => {
      await client.cancelQueries({ queryKey: key });
      client.setQueryData(key, result);
      setDraft(null);
      setProducerVerified(false);
      setNotice(result.config.auto_daily ? "配置已保存。后台会在每日选题前生成免费Radar日报，再导入评估；保存本身不立即调用模型。" : "配置已保存，后台只读取日报，不运行Radar生成器。");
      await Promise.all(["discovery-radar", "discovery-status", "discovery-persona", "discovery-sources", "discovery-source-merges", "discovery-runs"].map(name => client.invalidateQueries({ queryKey: [name, user] })));
    } });
  function edit(value: Partial<RadarConfig>) {
    setDraft({ ...config, ...value });
    if ("report_path" in value || "producer_version" in value || "producer_revision" in value) setProducerVerified(false);
    setValidationError(""); setNotice(""); save.reset();
  }
  function submit(event: FormEvent) {
    event.preventDefault();
    if (!editable || save.isPending || !query.isSuccess) return;
    const path = config.report_path?.trim() || "", version = config.producer_version?.trim() || "", revision = config.producer_revision?.trim().toLowerCase() || "";
    if (config.enabled && (!path.startsWith("/") || !/\.json$/i.test(path))) { setValidationError(discoveryLabel("radar_absolute_json_path_required")); return; }
    if (config.enabled && !version) { setValidationError(discoveryLabel("radar_producer_version_required")); return; }
    if (version && !/^[A-Za-z0-9_.+-]{1,80}$/.test(version)) { setValidationError(discoveryLabel("radar_producer_version_invalid")); return; }
    if (revision && !/^[0-9a-f]{40}$/.test(revision)) { setValidationError(discoveryLabel("radar_producer_revision_invalid")); return; }
    if (config.enabled && !producerVerified) { setValidationError("请先核实并确认这份日报的生成器版本。"); return; }
    setValidationError(""); setNotice("");
    save.mutate({ persona_id: personaId, enabled: !!config.enabled, auto_daily: !!config.auto_daily, producer_verified: producerVerified, ...(path ? { report_path: path } : {}), ...(version ? { producer_version: version } : {}), ...(revision ? { producer_revision: revision } : {}) });
  }
  const saveError = save.error instanceof ApiError && save.error.status === 422 ? discoveryLabel(save.error.message) : "Radar 配置保存失败，请检查权限或连接后重试。";
  return <details open={open} onToggle={event => setOpen(event.currentTarget.open)} className="rounded border border-slate-200 p-3">
    <summary>配置 Radar 本地日报</summary>
    <div className="mt-3 space-y-3">
      <p className="text-xs text-slate-600">仅作为当前科技角色的补充来源。请使用服务所在机器可读取的本地日报 JSON 文件；GitHub 仓库链接不能作为日报 Feed。</p>
      {query.isPending ? <Spinner label="读取 Radar 配置…" /> : query.isError ? <><ErrorBanner message="Radar 配置读取失败，无法确认已保存的设置。" /><Button variant="secondary" onClick={() => void query.refetch()}>重试读取</Button></> : <>
        <RadarView radar={query.data} />
        {query.data.config.auto_daily && <p className="text-xs text-slate-600">每日自动生成：{query.data.generation ? `${query.data.generation.business_date} · ${discoveryLabel(query.data.generation.status)}${query.data.generation.reason ? ` · ${discoveryLabel(query.data.generation.reason)}` : ""}` : "等待当天选题时段（沿用角色调度）"}。仅GitHub/Hugging Face免费信号，同日失败或未知不自动重试。</p>}
        <p className="text-xs text-slate-600">最近导入：{localTime(query.data.last_imported_at)}（台北时间）。页面读取仅展示已记录状态，未检查文件当前是否可用。</p>
        <form onSubmit={submit} className="space-y-3">
          {validationError && <ErrorBanner message={validationError} />}
          {save.isError && <ErrorBanner message={saveError} />}
          <fieldset disabled={!editable || save.isPending} className="space-y-3">
            <Field label="本地日报 JSON 路径"><input className={inputClass} required={!!config.enabled} maxLength={2000} value={config.report_path ?? ""} onChange={event => edit({ report_path: event.target.value })} placeholder="本地文件的绝对路径" /></Field>
            <Field label="生成器版本（启用时必填）"><input className={inputClass} required={!!config.enabled} maxLength={80} value={config.producer_version ?? ""} onChange={event => edit({ producer_version: event.target.value })} /></Field>
            <Field label="生成器 commit（可选，40 位十六进制）"><input className={inputClass} maxLength={40} pattern="[0-9a-fA-F]{40}" value={config.producer_revision ?? ""} onChange={event => edit({ producer_revision: event.target.value })} /></Field>
            <p className="text-xs text-slate-500">可选字段留空会保留已有值；启用时必须填写路径和版本。</p>
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={!!config.enabled} onChange={event => edit({ enabled: event.target.checked })} />启用此补充来源</label>
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={!!config.auto_daily} onChange={event => edit({ auto_daily: event.target.checked })} />每天自动生成日报，再进入科技选题评估</label>
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" required={!!config.enabled} checked={producerVerified} onChange={event => { setDraft({ ...config }); setProducerVerified(event.target.checked); setValidationError(""); setNotice(""); save.reset(); }} />我已核实这份日报的生成器版本</label>
          </fieldset>
          <p className="text-xs text-slate-600">保存前请核实实际生成器版本。未勾选自动生成时只读取文件；勾选后由既有后台调度运行已安装的免费Radar，不启用付费信号或额外模型调用。</p>
          {!editable && <p className="text-xs text-slate-600">当前账号仅可查看配置。</p>}
          <Button type="submit" disabled={!editable || save.isPending}>{save.isPending ? "保存中…" : "保存 Radar 配置"}</Button>
          {notice && <p role="status" className="text-xs text-slate-600">{notice}</p>}
        </form>
      </>}
    </div>
  </details>;
}

function RunView({ run }: { run: Run }) {
  const count = run.diagnostics?.counts.persisted_opportunities ?? run.summary?.count;
  const stages: Record<string, string> = { evidence: "证据 / 类型核验", score: "评分", selection: "去重与名额筛选" };
  return <div className="min-w-0 space-y-2 text-sm">
    <p>{run.business_date || "日期未记录"} · 角色 {run.persona_id} · {discoveryLabel(run.status)}</p>
    <p className="text-xs text-slate-600">原因：{discoveryLabel(run.reason)} · 已保存机会：{count ?? "未记录"}{count != null ? " 条" : ""} · 完成时间：{localTime(run.finished_at)}</p>
    {run.status === "succeeded" && count === 0 && <p>本批已完成，保存了 0 条机会；具体覆盖与淘汰原因见下方记录。</p>}
    {run.status === "partial" && <p className="text-amber-800">本批仅部分完成，已有机会仍可使用；来源缺口不代表全部内容都已评估。</p>}
    <details className="rounded border border-slate-200 p-2 text-xs">
      <summary>选题过程与淘汰原因{run.diagnostics ? "" : "：未记录"}</summary>
      {run.diagnostics ? <div className="mt-2 space-y-3">
        <p>策略：{run.diagnostics.policy_version || "未记录"} · 诊断版本：{run.diagnostics.version || "未记录"}</p>
        <dl className="grid gap-2 sm:grid-cols-2">{Object.entries(diagnosticCounts).map(([key, label]) => <div key={key} className="flex justify-between gap-3"><dt>{label}</dt><dd>{run.diagnostics!.counts[key as keyof typeof diagnosticCounts] ?? "未记录"}</dd></div>)}</dl>
        <p>未分析的线索不等于不合格；不同阶段计数不能相加当作线索总数。</p>
        {run.diagnostics.rejections?.length ? <ul className="space-y-2">{run.diagnostics.rejections.map((rejection, index) => <li key={`${rejection.candidate_id}-${rejection.stage}-${index}`} className="break-words">{rejection.title || "未命名候选"} · {Object.prototype.hasOwnProperty.call(stages, rejection.stage) ? stages[rejection.stage] : "筛选阶段"}：{discoveryLabel(rejection.reason)}</li>)}</ul> : <p>未记录逐条淘汰原因。</p>}
      </div> : <p className="mt-2">此批次未记录分阶段诊断，无法推算为 0，也无法判断所有线索是否都已分析。</p>}
    </details>
    {run.radar && <RadarView radar={run.radar} />}
    {run.collection_notice && <p className="text-xs text-amber-800">{catchupLabel(run.collection_notice)}</p>}
    {run.collection_snapshot && <CollectionCoverage snapshot={run.collection_snapshot} />}
  </div>;
}


const catchupLabels: Record<string, string> = {
  radar_interval_unverified: "日报已读取，但无法证明停机区间的所有日报均已覆盖",
  radar_item_budget: "Radar 达到单次线索上限，仍有未分析项", radar_partial: "Radar 日报存在未解析线索或上游缺口",
  pending: "等待补采", running: "正在补采", covered: "公开入口区间已核对", partial: "补采结束，覆盖不完整", failed: "补采失败", excluded: "未参与本次补采",
  catchup_source_budget: "达到单来源补采上限", catchup_wait_budget: "达到本批补采等待上限",
  catchup_history_unavailable: "来源不支持可核实的历史回溯", catchup_initial_history_unknown: "首次收录，历史覆盖未知",
  catchup_dates_unknown: "日期或排序不明确，无法确认完整", catchup_pagination_loop: "历史分页重复，无法继续",
  catchup_hotlist_history_unknown: "关机期间已下榜内容无法确认", catchup_unchanged_unverified: "当前入口未变化，历史覆盖仍待确认",
  catchup_http_failed: "来源HTTP请求失败", catchup_timeout: "来源读取超时", catchup_network_failed: "网络读取失败", catchup_parse_failed: "来源内容解析失败", catchup_unsafe_url: "历史链接未通过安全检查",
  no_eligible_subscription: "没有有效角色订阅", source_merged: "来源已合并", catchup_not_in_frozen_run: "本次补采未纳入已开始的当天批次",
};
const catchupLabel = (value: string | null) => value ? catchupLabels[value] || discoveryLabel(value) : "";
const localTime = (value: string | null) => value ? new Date(value.endsWith("Z") || /[+-]\d{2}:\d{2}$/.test(value) ? value : `${value}Z`).toLocaleString("zh-CN", { timeZone: "Asia/Taipei" }) : "未记录";
function CatchupReceiptView({ receipt }: { receipt: CatchupReceipt }) {
  return <div className="space-y-1 text-xs text-slate-600">
    <p><strong>{receipt.name || `来源 ${receipt.source_id}`}</strong> · {catchupLabel(receipt.status)}</p>
    <p>补采检查区间：{localTime(receipt.start_at)} → {localTime(receipt.end_at)}</p>
    <p>扫描 {receipt.counts.scanned ?? "未记录"} 条 · 新增 {receipt.counts.new_versions ?? "未记录"} 个条目版本 · 请求 {receipt.counts.requests ?? "未记录"} 次（不等于已核验正文或选题数）</p>
    {receipt.reason && <p>{catchupLabel(receipt.reason)}</p>}
    {receipt.coverage.unconfirmed_interval && <p className="text-amber-800">未确认区间：{localTime(receipt.coverage.unconfirmed_interval.start_at)} → {localTime(receipt.coverage.unconfirmed_interval.end_at)}；具体缺失时段和数量未知。</p>}
    {receipt.earlier_gap && <details><summary>此前仍有未确认的历史区间</summary><CatchupReceiptView receipt={receipt.earlier_gap} /></details>}
  </div>;
}
function CollectionCoverage({ snapshot }: { snapshot: CollectionSnapshot }) {
  return <details className="mt-2 rounded border border-slate-200 p-2 text-xs">
    <summary>选题采用的补采快照：{snapshot.status === "covered" ? "公开入口区间已核对" : snapshot.status === "legacy_frozen" ? "沿用此前已冻结证据" : "部分来源有缺口"} · {localTime(snapshot.frozen_at)}</summary>
    {snapshot.notice && <p className="my-2 text-amber-800">{catchupLabel(snapshot.notice)}</p>}
    <div className="mt-2 space-y-3">{snapshot.sources.map(r => <CatchupReceiptView key={r.id} receipt={r} />)}</div>
  </details>;
}

export function PersonaDiscoveryStatus({ personaId, revision }: { personaId: number; revision: number }) {
  const user = currentUser();
  const status = useQuery({ queryKey: ["discovery-persona", user, personaId, revision],
    queryFn: () => api.get<DiscoveryStatus>("/content-opportunities/discovery/status"), refetchInterval: 30000 });
  const persona = status.data?.personas.find(p => p.persona_id === personaId);
  return <p className="mt-3 text-sm text-slate-600">自动研究：{status.isPending ? "正在读取…" : status.isError ? "状态读取失败" : persona ? discoveryLabel(persona.status) : "暂无有效定位"} · <a className="text-indigo-700" href="/opportunities">查看来源与每日选题</a></p>;
}

function SourceEditor({ source, personas, initialPersona, allowProcessing, busy, error, notice, save, close }: {
  source: Source | null; personas: Persona[]; initialPersona: string; allowProcessing: boolean; busy: boolean;
  error: unknown; notice: string; save: (body: SourceDraft) => void; close: () => void;
}) {
  const [name, setName] = useState(source?.name || "");
  const [url, setUrl] = useState("");
  const [kind, setKind] = useState(source?.kind || "website");
  const [ids, setIds] = useState<number[]>(source?.persona_ids || (initialPersona ? [Number(initialPersona)] : []));
  const [paused, setPaused] = useState(source?.manually_paused ?? false);
  const [processing, setProcessing] = useState(source?.processing_allowed ?? allowProcessing);
  function submit(event: FormEvent) {
    event.preventDefault();
    save({ name: name.trim() || undefined, ...(!source || kind !== source.kind ? { kind } : {}), persona_ids: ids, manually_paused: paused, processing_allowed: processing,
      ...(!source ? { url: url.trim() } : {}) });
  }
  return <Modal title={source ? "配置来源" : "添加来源"} onClose={() => { if (!busy) close(); }}>
    <form className="space-y-4" onSubmit={submit}>
      {notice && <p role="status" className="text-sm text-indigo-700">{notice}</p>}
      {!!error && <ErrorBanner message={error instanceof Error ? error.message : "保存失败，请重试"} />}
      <Field label="来源类型"><select className={inputClass} value={kind} onChange={e => setKind(e.target.value)}>{source && !["website", "rss", "creator"].includes(source.kind) && <option value={source.kind}>保留原类型（{({ official: "官方", media: "媒体", blog: "博客", community: "社区", hotlist: "热点聚合" } as Record<string, string>)[source.kind] || source.kind}）</option>}<option value="website">新闻网站</option><option value="rss">RSS / Atom</option><option value="creator">博主主页</option></select></Field>
      <Field label="公开链接"><input className={inputClass} type="url" required disabled={!!source} maxLength={1000} value={source?.input_url || source?.url || url} onChange={e => setUrl(e.target.value)} /></Field>
      <p className="text-xs text-slate-500">{source ? "更换链接请添加新来源，原有证据会保留。" : "支持公开网站、Feed和博主主页；保存后由后台验证可采集入口。"}</p>
      <Field label="显示名称（可选）"><input className={inputClass} maxLength={300} value={name} onChange={e => setName(e.target.value)} placeholder="未填写时使用域名" /></Field>
      <fieldset className="space-y-2"><legend className="mb-2 text-sm font-medium">关联角色（可多选）</legend>{personas.map(p => <label key={p.id} className="flex items-center gap-2 text-sm"><input type="checkbox" checked={ids.includes(p.id)} onChange={e => setIds(e.target.checked ? [...ids, p.id] : ids.filter(id => id !== p.id))} />{p.name}{p.status !== "active" ? "（当前不可用）" : ""}</label>)}<p className="text-xs text-slate-500">不选角色时仅储备来源。手动选择不会被自动研究更改，选题仍按角色定位筛选。</p></fieldset>
      <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={!paused} onChange={e => setPaused(!e.target.checked)} />允许后台采集</label>
      <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={processing} onChange={e => setProcessing(e.target.checked)} />允许模型分析公开资料的必要片段</label>
      <p className="text-xs text-slate-500">来源验证通过且角色有效后参与正常调度；添加来源不立即补充今日选题。</p>
      <Button type="submit" disabled={busy}>{busy ? "保存中…" : source ? "保存配置" : "保存并后台验证"}</Button>
    </form>
  </Modal>;
}

export function DiscoveryPanel({ personaId = "" }: { personaId?: string }) {
  const user = currentUser(), client = useQueryClient();
  const [tab, setTab] = useState("status");
  const [origin, setOrigin] = useState("");
  const [offset, setOffset] = useState(0);
  const [editing, setEditing] = useState<Source | null | undefined>(undefined);
  const [radarEditing, setRadarEditing] = useState<number | null>(null);
  const [notice, setNotice] = useState("");
  useEffect(() => setOffset(0), [personaId]);
  const personas = useQuery({ queryKey: ["discovery-role-options", user], queryFn: () => api.get<Persona[]>("/content-personas"), enabled: tab === "sources" });
  const me = useQuery({ queryKey: ["discovery-user", user], queryFn: () => api.get<{ role: string }>("/users/me") });
  const editable = !!me.data && ["admin", "editor"].includes(me.data.role);
  const status = useDiscoveryStatus();
  const suffix = personaId ? `?persona_id=${encodeURIComponent(personaId)}` : "";
  const sourceParams = new URLSearchParams({ limit: "31", offset: String(offset), ...(personaId ? { persona_id: personaId } : {}), ...(origin ? { origin } : {}) });
  const sources = useQuery({ queryKey: ["discovery-sources", user, personaId, origin, offset], queryFn: () => api.get<Source[]>(`${sourceBase}?${sourceParams}`), enabled: tab === "sources", refetchInterval: tab === "sources" ? 5000 : false });
  const merges = useQuery({ queryKey: ["discovery-source-merges", user], queryFn: () => api.get<Source[]>(`${sourceBase}?merged_only=true&limit=200`), enabled: tab === "sources", refetchInterval: tab === "sources" ? 5000 : false });
  const runs = useQuery({ queryKey: ["discovery-runs", user, personaId], queryFn: () => api.get<Run[]>(`/content-opportunities/discovery/runs${suffix}`), enabled: tab === "runs", refetchInterval: tab === "runs" ? 10000 : false });
  const refresh = () => Promise.all(["discovery-status", "discovery-radar", "discovery-sources", "discovery-source-merges", "discovery-runs", "opportunities", "home"].map(key => client.invalidateQueries({ queryKey: [key] })));
  function radarPersona(source: Source) {
    return status.data?.personas.find(p => p.opportunity_policy === "technology.v1" && (p.radar?.source_id === source.id || source.persona_ids.includes(p.persona_id)));
  }
  function editSource(source: Source) {
    if (isRadarSource(source)) {
      const persona = radarPersona(source);
      if (persona) { setEditing(undefined); setRadarEditing(persona.persona_id); }
      else setNotice("无法确认该 Radar 来源对应的科技角色，请刷新运行状态后重试。");
    } else setEditing(source);
  }
  const configure = useMutation({ mutationFn: () => api.put("/content-opportunities/discovery/settings", {
    enabled: !status.data?.settings.enabled, public_processing_allowed: true,
    daily_hour: status.data?.settings.daily_hour ?? 8, daily_limit: status.data?.settings.daily_limit ?? 5,
  }), onSuccess: refresh });
  const pausePersona = useMutation({ mutationFn: (id: number) => {
    const settings = status.data!.settings;
    const paused = settings.paused_persona_ids || [];
    return api.put("/content-opportunities/discovery/settings", {
      enabled: settings.enabled, public_processing_allowed: settings.public_processing_allowed,
      daily_hour: settings.daily_hour, daily_limit: settings.daily_limit,
      paused_persona_ids: paused.includes(id) ? paused.filter(value => value !== id) : [...paused, id],
    });
  }, onSuccess: refresh });
  const changeSource = useMutation({ mutationFn: ({ id, ...body }: { id: number; manually_paused?: boolean; processing_allowed?: boolean }) => api.patch(`/content-opportunities/discovery/sources/${id}`, body), onSuccess: refresh });
  const saveSource = useMutation({ mutationFn: (body: SourceDraft) => editing
    ? api.patch<Source>(`${sourceBase}/${editing.id}`, body).then(source => ({ source, created: true }))
    : api.post<{ source: Source; created: boolean }>(sourceBase, body), onSuccess: result => {
      void refresh();
      if (!result.created) { setNotice("该来源已存在。已打开原配置，请核对关联角色后保存。"); editSource(result.source); }
      else { setEditing(undefined); setNotice("来源配置已保存，后台会按实际验证状态和角色设置继续处理。"); }
    } });
  const openMerged = useMutation({ mutationFn: (id: number) => api.get<Source>(`${sourceBase}/${id}`), onSuccess: source => {
    saveSource.reset(); setNotice("新链接对应已有来源，新关联设置尚未应用。请核对后保存配置。"); editSource(source);
  } });
  const validate = useMutation({ mutationFn: (id: number) => api.post(`${sourceBase}/${id}/validate`), onSuccess: refresh });
  const retry = useMutation({ mutationFn: (id: number) => api.post(`/content-opportunities/discovery/runs/${id}/retry`), onSuccess: refresh });
  const error = status.error || sources.error || runs.error || configure.error || changeSource.error || pausePersona.error || retry.error || validate.error || personas.error || merges.error || openMerged.error;
  if (status.isPending) return <Spinner label="读取角色研究状态…" />;
  return <section className="space-y-4 rounded-xl border border-slate-200 bg-white p-5">
    <div className="flex flex-wrap justify-between gap-3"><h2 className="font-semibold">角色自动研究与每日选题</h2><div className="flex flex-wrap gap-2">{[ ["status", "运行状态"], ["sources", "信息源储备"], ["runs", "研究记录"] ].map(([key, label]) => <Button key={key} variant={tab === key ? "primary" : "secondary"} onClick={() => setTab(key)}>{label}</Button>)}<Button variant="secondary" disabled={status.isFetching} onClick={() => void refresh()}>刷新状态</Button></div></div>
    {error && <ErrorBanner message={error instanceof Error ? error.message : "读取研究状态失败"} />}
    {tab === "status" && status.data && !status.isError && <div className="space-y-3" aria-live="polite">
      <p className="text-sm text-slate-600">每日 {String(status.data.settings.daily_hour).padStart(2, "0")}:00（台北时间），每角色最多 {status.data.settings.daily_limit} 条；来源发现和选题由后台执行。</p>
      <p className="text-xs text-slate-500">搜索：{status.data.settings.search_provider || "未选择"}（在 设置 → AI 与模型 → 用途路由 里选）· {status.data.settings.search_configured ? "可用" : "不可用"} · {status.data.settings.worker_enabled ? "后台队列已启用" : "后台队列尚未启用"}</p>
      {!!status.data.catchup?.length && <details className="rounded-lg border p-3 text-sm"><summary>来源补采进度与缺口（公开入口覆盖，不保证全网历史完整）</summary><div className="mt-3 space-y-3">{status.data.catchup.filter(r => !personaId || r.persona_ids.includes(Number(personaId))).map(r => <CatchupReceiptView key={r.id} receipt={r} />)}</div></details>}
      {status.data.personas.filter(p => !personaId || String(p.persona_id) === personaId).map(p => <div key={p.persona_id} className="space-y-3 rounded-lg bg-slate-50 p-3 text-sm">
        <div><strong>{p.name}</strong> · {p.collection_mode === "aggregate" ? "聚合站同步选题" : "自动研究"} {p.status !== "positioning_incomplete" && <Button size="sm" variant="secondary" disabled={!editable || pausePersona.isPending} onClick={() => pausePersona.mutate(p.persona_id)}>{status.data.settings.paused_persona_ids?.includes(p.persona_id) ? "恢复此角色" : "暂停此角色"}</Button>}</div>
        {["positioning_incomplete", "paused", "search_unavailable", "worker_not_enabled", "public_processing_not_allowed"].includes(p.status) && <p className="text-amber-800">当前执行条件：{discoveryLabel(p.reason || p.status)}</p>}
        <p className="font-medium">今日批次（{p.business_date || "业务日期未记录"}）</p>
        {p.today_run ? <RunView run={p.today_run} /> : <p>{p.today_run === null ? "今日尚无研究批次，不能判断今日是否有合适选题。" : "今日批次状态未记录。"}</p>}
        {p.last_run && p.last_run.id !== p.today_run?.id && <details className="rounded border p-2"><summary>最近批次：{p.last_run.business_date || "日期未记录"} · {discoveryLabel(p.last_run.status)}（{p.last_run.business_date === p.business_date ? "其他研究批次" : "非今日结果"}）</summary><div className="mt-2"><RunView run={p.last_run} /></div></details>}
        <p className="text-xs text-slate-600">下次计划：{localTime(p.next_due_at)}（台北时间）</p>
        {p.opportunity_policy === "technology.v1" && <><RadarView radar={p.radar ?? p.today_run?.radar} /><RadarConfiguration key={`${user}-${p.persona_id}`} personaId={p.persona_id} editable={editable} /></>}
      </div>)}
      <div className="flex flex-wrap gap-2"><Button variant="secondary" disabled={!editable || configure.isPending} onClick={() => configure.mutate()}>{status.data.settings.enabled ? "暂停自动研究" : "启用自动研究"}</Button></div>
      <p className="text-xs text-slate-500">启用即允许系统分析所跟踪公开资料的必要片段；不会授予全文转载权限。正常运行无需手动生成或打开此页。刷新只读取状态，不触发采集、生成或重试。</p>
    </div>}
    {tab === "sources" && <div className="space-y-3">
      {merges.data?.map(s => <div key={s.id} role="status" className="rounded-lg bg-amber-50 p-3 text-sm"><p className="break-all">新增链接 {s.input_url || s.url} 的采集入口已存在，新的角色设置尚未应用。</p><Button size="sm" variant="secondary" disabled={!editable || !personas.isSuccess || openMerged.isPending} onClick={() => openMerged.mutate(s.id)}>打开已有来源配置</Button></div>)}
      <div className="flex flex-wrap items-end gap-3"><Field label="添加方式"><select className={inputClass} value={origin} onChange={e => { setOrigin(e.target.value); setOffset(0); }}><option value="">全部来源</option>{Object.entries(origins).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></Field><Button disabled={!editable || !personas.isSuccess} onClick={() => { saveSource.reset(); setNotice(""); setEditing(null); }}>添加来源</Button></div>
      {notice && editing === undefined && <p role="status" className="text-sm text-indigo-700">{notice}</p>}
      {sources.isPending ? <Spinner /> : <div className="space-y-2">{sources.data?.length === 0 && <p className="text-sm text-slate-500">没有符合条件的来源，可以添加或调整筛选。</p>}{sources.data?.slice(0, 30).map(s => isRadarSource(s) ? <div key={s.id} className="space-y-2 rounded-lg border p-3 text-sm"><strong>{s.name}</strong><p>本地 Radar 日报 · {radarPersona(s)?.name || "科技角色待核对"}</p><RadarView radar={radarPersona(s)?.radar} /><p className="text-xs text-slate-600">请使用专属配置管理路径、生成器版本和启用状态。</p><Button size="sm" variant="secondary" disabled={!radarPersona(s)} onClick={() => editSource(s)}>Radar 专属配置</Button>{!radarPersona(s) && <p className="text-xs text-amber-800">无法确认对应的科技角色，请刷新状态后重试。</p>}</div> : <div className="flex flex-wrap justify-between gap-3 rounded-lg border p-3 text-sm" key={s.id}><div className="min-w-0 flex-1 space-y-1"><a href={s.input_url || s.url} target="_blank" rel="noopener noreferrer" className="break-all text-indigo-700">{s.name}</a><p className="text-xs text-slate-500">{origins[s.origin] || "既有来源"} · {s.manually_paused ? "已暂停采集" : discoveryLabel(s.status)} · {s.processing_allowed ? "允许模型分析" : "已禁止模型分析"}</p><p className="text-xs text-slate-500">关联角色：{s.personas.map(p => `${p.name}（${discoveryLabel(p.state)}）`).join("、") || "未关联，仅储备"}</p><p className="break-all text-xs text-slate-500">原始链接：{s.input_url || s.url}</p>{!!s.aggregate_mode_paused_for?.length && <p className="text-xs text-slate-500">聚合模式已暂停这些角色的逐站采集：{s.aggregate_mode_paused_for.join("、")}；原配置保留。</p>}{s.aggregate_sync && <p className="text-xs text-slate-500">聚合同步：{s.aggregate_sync.phase === "snapshot" ? "初次快照" : "增量"} · {s.aggregate_sync.has_more ? "还有数据待补读" : "当前分页已完成"} · 最近结案：{localTime(s.aggregate_sync.synced_at || null)}</p>}{s.collector_url && <p className="break-all text-xs text-slate-500">采集入口：{s.collector_url}</p>}<p className="text-xs text-slate-500">验证：{s.validation.state ? discoveryLabel(s.validation.state) : "既有状态"} · 最近成功：{s.last_success_at ? new Date(s.last_success_at.endsWith("Z") || /[+-]\d{2}:\d{2}$/.test(s.last_success_at) ? s.last_success_at : `${s.last_success_at}Z`).toLocaleString() : "尚无"}{s.reason ? ` · ${discoveryLabel(s.reason)}` : ""}</p>{s.catchup?.latest && <details className="mt-2"><summary className="text-xs">补采：{catchupLabel(s.catchup.latest.status)}</summary><CatchupReceiptView receipt={s.catchup.latest} />{s.catchup.last_gap && s.catchup.last_gap.id !== s.catchup.latest.id && <div className="mt-2"><p className="text-xs text-amber-800">此前的未确认历史区间仍保留：</p><CatchupReceiptView receipt={s.catchup.last_gap} /></div>}</details>}{s.alias_notice && <p role="status" className="text-xs text-amber-700">{s.alias_notice.message}</p>}</div><div className="flex flex-wrap items-start gap-2"><Button size="sm" variant="secondary" disabled={!editable || !personas.isSuccess} onClick={() => { saveSource.reset(); setNotice(""); setEditing(s); }}>配置</Button><Button size="sm" variant="secondary" disabled={!editable || validate.isPending || ["pending", "running"].includes(s.validation.state || "")} onClick={() => validate.mutate(s.id)}>重新验证</Button><Button size="sm" variant="secondary" disabled={!editable || changeSource.isPending} onClick={() => changeSource.mutate({ id: s.id, manually_paused: !s.manually_paused })}>{s.manually_paused ? "恢复采集" : "暂停采集"}</Button><Button size="sm" variant="secondary" disabled={!editable || changeSource.isPending} onClick={() => changeSource.mutate({ id: s.id, processing_allowed: !s.processing_allowed })}>{s.processing_allowed ? "禁止模型分析" : "允许模型分析"}</Button></div></div>)}</div>}
      <div className="flex items-center gap-3"><Button variant="secondary" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - 30))}>上一页来源</Button><span className="text-sm">第 {Math.floor(offset / 30) + 1} 页</span><Button variant="secondary" disabled={!sources.data || sources.data.length <= 30} onClick={() => setOffset(offset + 30)}>下一页来源</Button></div>
    </div>}
    {radarEditing !== null && <Modal title={`Radar 专属配置 · ${status.data?.personas.find(p => p.persona_id === radarEditing)?.name || `角色 ${radarEditing}`}`} onClose={() => setRadarEditing(null)}><RadarConfiguration key={`${user}-${radarEditing}`} personaId={radarEditing} editable={editable} initiallyOpen /></Modal>}
    {editing !== undefined && (!editing || !isRadarSource(editing)) && <SourceEditor key={editing?.id ?? "new"} source={editing} personas={personas.data || []} initialPersona={personaId} allowProcessing={status.data?.settings.public_processing_allowed ?? false} busy={saveSource.isPending} error={saveSource.error} notice={notice} save={body => saveSource.mutate(body)} close={() => { setEditing(undefined); saveSource.reset(); }} />}
    {tab === "runs" && (runs.isPending ? <Spinner /> : !runs.isError && <div className="space-y-2">{runs.data?.length === 0 && <p className="text-sm text-slate-500">尚无研究记录。</p>}{runs.data?.map(r => <div key={r.id} className="flex flex-wrap justify-between gap-3 rounded-lg border p-3 text-sm"><RunView run={r} />{["blocked", "failed", "partial"].includes(r.status) && <Button size="sm" variant="secondary" disabled={!editable || retry.isPending} onClick={() => retry.mutate(r.id)}>恢复此批次</Button>}</div>)}</div>)}
  </section>;
}
