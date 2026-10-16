import { useEffect, useRef, useState } from "react";
import ProductionStageControls, { type ProductionStages, type ProductionCatalog } from "./ProductionStageControls";
import type { CapabilityArtifact } from "./capabilityMemoryTypes";
import { currentUser } from "../api";
import { Button, ErrorBanner, Field, Spinner, StatusBadge, inputClass } from "../components/ui";

export interface CreativeExecutionPanelProps {
  projectId: number;
  unitId: number;
  readOnly: boolean;
  executionId?: number;
}

type Kind = "image" | "video" | "audio" | "other";
type Role = { role_id: string; kind: Kind; required: boolean; allowed_mime: string[]; min_count: number; max_count: number; max_bytes: number };
type RoleDraft = Omit<Role, "allowed_mime" | "min_count" | "max_count" | "max_bytes"> & { mime: string; min: string; max: string; bytes: string };
type Rights = { rights_status: string; public_use_allowed: boolean; model_use_allowed: boolean; commercial_use_allowed: boolean; attribution_text: string | null; license: Record<string, unknown> };
type Asset = { material_revision_id: number; content_hash: string; role?: string; slot_key?: string; mime_type?: string; rights?: Rights };
type Intent = { objective?: string; audience?: string; must_keep?: string[]; must_avoid?: string[]; creative_freedom?: string; rationales?: { stable_id: string; reason: string }[] };
type Source = { id: number; revision_no: number; payload_schema: string; payload_hash: string; context_hash: string; payload: Record<string, unknown>; assets: Asset[]; evidence: { fact_pack_item_id: number; snapshot_checksum: string }[]; creative_intent?: Intent | null; readiness?: { state: string; reasons: string[] }; variant_key?: string; source_master_revision_id?: number; channel_id?: string; content_form?: string };
type PackageDocument = { production_methods?: { manifest_hash: string; stages: { stage: string; title: string; origin: string; enabled: boolean; disabled_method_ids: string[]; methods: { id: string; method_hash: string; skill_ref?: string; revision_id?: number }[] }[] }; schema: string; objective: string; constraints: string[]; acceptance_criteria: string[]; creative_intent: Intent | null; source: { kind: string; id: number; payload_schema: string; payload_hash: string; context_hash: string; creative_intent_hash: string | null; channel_id?: string; content_form?: string; content: Record<string, unknown> }; context: { identity?: { id: number; checksum: string }; brief?: { id: number; checksum: string }; boundary?: { id: number; checksum: string } }; assets: Asset[]; evidence: { fact_pack_item_id: number; snapshot_checksum: string }[]; output_contract: { roles: Role[] }; director?: { final_render_required: boolean; aspect_ratio?: string } };
type Package = { id: number; project_id: number; content_unit_id: number; package_schema: string; package_hash: string; package: PackageDocument; is_current: boolean; reasons: string[]; created_at: string | null };
type Cleanup = { status: "pending" | "removed" | "already_absent" | "failed"; retryable: boolean; code: string | null };
type ExecutorDescriptor = { declaration_status: "declared" | "undeclared"; runtime_verified: false; supports_checkpoint: boolean | null; supports_revert: boolean | null; supports_recover: boolean | null; output_kinds: Kind[] | null };
type Output = { id: number; role_id: string; kind: Kind; output_index: number; attempt_no: number; mime_type: string; content_hash: string; size_bytes: number; metadata: Record<string, unknown>; state: string; material_revision_id: number | null; created_at: string | null; decided_by?: string; decided_at?: string; staging_cleanup?: Cleanup | null };
type Execution = { production_method_receipts?: { event_id: number; stage: string; status: string; method_hashes: string[] }[]; id: number; project_id: number; content_unit_id: number; package_id: number; package_hash: string; idempotency_key: string; executor_kind: string; executor_key: string; executor_version: string; executor_descriptor?: ExecutorDescriptor; state: string; revision_no: number; dispatch_certainty: string; safe_reason: string | null; retry_of_id: number | null; checkpoint: Record<string, unknown>; checkpoint_binding?: Record<string, unknown> | null; recovery: Record<string, unknown>; output_counts: (Role & { staged_count: number; accepted_count: number; rejected_indexes: number[] })[]; outputs?: Output[]; materialized_inputs?: Asset[]; created_at: string | null; updated_at: string | null };
type Page<T> = { items: T[] };
type PackageRequest = { production_stages?: ProductionStages; source_master_revision_id?: number; source_variant_revision_id?: number; package_schema: string; objective: string; constraints: string[]; output_contract: { roles: Role[] }; acceptance_criteria: string[] };
type DecisionDraft = { title: string; status: string; public: boolean; model: boolean; commercial: boolean; license: string; licenseId: string; licenseUrl: string; attribution: string; attach: boolean; confirmed: boolean };
type Preview = { outputId: number; url?: string; text?: string; mime: string };

const MAX_BYTES = 30 * 1024 * 1024;
const PAGE_SIZE = 100;
const KINDS: Kind[] = ["image", "video", "audio", "other"];
const MIME_DEFAULT: Record<Kind, string> = { image: "image/png", video: "video/mp4", audio: "audio/wav", other: "text/plain" };
const STATE_LABEL: Record<string, string> = { prepared: "已准备，等待执行者领取", claimed: "已领取", in_progress: "执行中", failed_before_dispatch: "发送前失败", blocked: "受阻", unknown: "结果待核对", result_ready: "成果待人工审阅", accepted: "必需成果已接受", rejected: "整次执行已拒绝", cancelled: "已取消", superseded: "已替代" };
const REASONS: Record<string, string> = {
  creative_source_not_current: "来源已不是当前版本，请重新读取并明确选择新来源。",
  creative_variant_context_stale: "渠道变体的来源或上下文已变化，需要先保存当前变体。",
  creative_package_stale: "冻结包已过期，请从当前来源创建新包。",
  creative_input_rights_changed: "输入素材权利已变化，请核对后创建新包。",
  creative_execution_revision_conflict: "执行记录已更新，请重新读取；未提交表单仍保留。",
  creative_execution_descriptor_incomplete: "能力声明需同时填写三项支持情况与输出类型，也可保留未声明。",
  creative_execution_descriptor_conflict: "本次执行的能力声明已冻结，不能在执行中更改。",
  creative_execution_output_kinds_contract_mismatch: "声明的输出类型须覆盖冻结包中的全部角色。",
  creative_execution_checkpoint_unsupported: "执行者声明不支持检查点，不能报告检查点。",
  creative_execution_recovery_unsupported: "执行者声明不支持此恢复动作。",
  creative_execution_recovery_checkpoint_mismatch: "恢复须引用原执行的精确检查点。",
  creative_execution_recovery_observation_required: "明确恢复动作须附实际回读哈希与已核对状态。",
  creative_execution_conflict: "另一个操作已更新记录，请重新读取后核对。",
  creative_execution_reconciliation_required: "已有结果未知的执行，先核对原执行，不能准备新执行或重发。",
  creative_execution_rights_escalation: "所选权利超出输入素材许可，不能接受。",
  creative_execution_license_conflict: "许可与输入素材的许可要求冲突，请核对继承的许可。",
  creative_execution_output_already_decided: "此输出已被处理或替换，请重新读取。",
  creative_execution_input_rights_changed: "输入权利已变化，请核对原素材。",
  creative_execution_project_file_rights_restricted: "专业项目文件须保留为私有素材。",
  creative_output_hash_mismatch: "成果字节与冻结哈希不一致，预览不可用。",
  creative_execution_cleanup_shared_pending: "另一份待接受成果共用此暂存文件，须先处理那份成果。",
  creative_execution_cleanup_unresolved: "执行仍待核对或受阻，须先明确解决当前状态。",
  creative_execution_cleanup_not_discardable: "此成果仍可接受，请先明确拒绝成果或结束执行。",
  creative_execution_cleanup_material_unverified: "正式素材与已接受成果尚未核对一致，保留暂存文件。",
  creative_execution_cleanup_reference_invalid: "暂存引用已变化，请重新读取后核对。",
  execution_cleanup_file_changed: "暂存文件已变化，未清理，请核对后重试。",
  execution_cleanup_target_invalid: "暂存目标不符合受控清理要求，保留文件。",
  execution_storage_unavailable: "本地暂存存储操作未完成，可重新读取后重试。",
  creative_unsafe_metadata: "要求或许可包含不允许保存的内容，请移除凭据和原始诊断信息。",
  needs_output_replacement: "必需成果被拒绝，等待同一槽位的新尝试。",
  executor_blocked: "执行者报告阻碍，需要人工处理。",
  dispatch_uncertain: "外部操作可能已发生，必须先核对。",
  reconciliation_needed: "需要核对外部实际状态。",
};
const METADATA_LABEL: Record<string, string> = { summary: "说明", checkpoint_ref: "检查点引用", observation_ref: "观察引用", observation_hash: "观察哈希", recovery_action: "恢复动作", readback_status: "执行者回读报告（未运行核验）", supports_checkpoint: "自述支持检查点", supports_revert: "自述支持撤回", supports_recover: "自述支持恢复", license: "许可", license_id: "许可编号", license_url: "许可链接", license_code: "许可代码", license_evidence_hash: "许可证据哈希", attribution: "署名", correlation_id: "关联编号", execution_id: "执行编号", package_id: "包编号", package_hash: "包哈希", executor_kind: "执行者类型", executor_key: "执行者标识", executor_version: "执行者版本", revision_no: "绑定版本", execution_revision: "绑定版本" };

function reason(code: string) { return REASONS[code] ?? code; }
function message(cause: unknown) { return cause instanceof Error ? cause.message : "请求失败，请重新读取状态。"; }
function lines(value: string) { return value.split(/\r?\n/).map(item => item.trim()).filter(Boolean); }
function roleDraft(index = 1): RoleDraft { return { role_id: `output_${index}`, kind: "image", required: true, mime: "image/png", min: "1", max: "1", bytes: String(MAX_BYTES) }; }
function decisionDraft(): DecisionDraft { return { title: "", status: "unknown", public: false, model: false, commercial: false, license: "", licenseId: "", licenseUrl: "", attribution: "", attach: false, confirmed: false }; }
function contract(roles: RoleDraft[]): Role[] {
  const ids = new Set<string>();
  if (!roles.length || roles.length > 20) throw new Error("输出角色需为 1–20 个。");
  const result = roles.map(role => {
    const id = role.role_id.trim();
    if (!/^[A-Za-z0-9][A-Za-z0-9_.:-]{0,99}$/.test(id) || ids.has(id)) throw new Error("角色标识需唯一，使用字母、数字、点、下划线、冒号或连字符。");
    ids.add(id);
    if (![role.min, role.max, role.bytes].every(value => /^\d+$/.test(value))) throw new Error("数量和字节上限必须是整数。");
    const min = Number(role.min), max = Number(role.max), bytes = Number(role.bytes);
    if (!(min >= 0 && min <= max && max >= 1 && max <= 20 && bytes >= 1 && bytes <= MAX_BYTES) || (role.required ? min < 1 : min !== 0)) throw new Error("必需角色最少 1 个，可选角色最少 0 个；最多 20 个，每文件最多 30 MiB。");
    const mimes = role.mime.split(/[,\s]+/).filter(Boolean);
    if (!mimes.length || mimes.length > 10 || new Set(mimes).size !== mimes.length || mimes.some(mime => !/^[a-z0-9.+-]+\/[a-z0-9.+-]+$/.test(mime) || (role.kind !== "other" && !mime.startsWith(`${role.kind}/`)))) throw new Error("MIME 需与类型匹配，最多 10 个，用逗号分隔且不能重复。");
    return { role_id: id, kind: role.kind, required: role.required, allowed_mime: mimes, min_count: min, max_count: max, max_bytes: bytes };
  });
  if (!result.some(role => role.required)) throw new Error("至少需要一个必需输出角色。");
  return result;
}
class CreativeApiError extends Error {
  constructor(public status: number, text: string) { super(text); }
}
async function request<T>(actor: string, path: string, signal?: AbortSignal, body?: unknown): Promise<T> {
  const response = await fetch(`/api/v1${path}`, { method: body === undefined ? "GET" : "POST", credentials: "same-origin", cache: "no-store", signal, headers: { "X-Studio-User": actor, ...(body === undefined ? {} : { "Content-Type": "application/json" }) }, ...(body === undefined ? {} : { body: JSON.stringify(body) }) });
  if (!response.ok) throw new CreativeApiError(response.status, await responseError(response));
  return response.json() as Promise<T>;
}
async function responseError(response: Response) {
  const data = await response.json().catch(() => null) as { detail?: unknown } | null;
  const detail = data?.detail;
  let text = "请求未完成，请重新读取状态。";
  if (typeof detail === "string") text = reason(detail);
  else if (Array.isArray(detail)) text = detail.map(item => `${item.loc?.slice(1).join(".") || "输入"}：${item.msg || "格式不正确"}`).join("；");
  else if (detail && typeof detail === "object" && "code" in detail) text = reason(String(detail.code));
  else if (response.status === 403) text = "没有执行此操作的权限，当前只能查看。";
  else if (response.status === 404) text = "记录或接口不可用，请核对当前项目及本地 schema。";
  else if (response.status >= 500) text = "本地接口暂不可用，请核对服务和 schema；此面板不会自动迁移或重启 API。";
  return `${response.status} · ${text}`;
}
function Metadata({ value }: { value: Record<string, unknown> }) {
  const entries = Object.entries(value).filter(([key, item]) => METADATA_LABEL[key] && ["string", "boolean", "number"].includes(typeof item));
  return entries.length ? <dl className="space-y-1 break-all text-xs text-slate-600">{entries.map(([key, item]) => <div key={key}><dt className="inline font-medium">{METADATA_LABEL[key]}：</dt><dd className="inline whitespace-pre-wrap">{typeof item === "boolean" ? item ? "是" : "否" : String(item)}</dd></div>)}</dl> : <p className="text-xs text-slate-500">暂无已记录的信息。</p>;
}
function IntentView({ intent }: { intent?: Intent | null }) {
  return intent ? <div className="space-y-1 text-sm"><p>意图：{intent.objective || "未记录"}</p><p>受众：{intent.audience || "未记录"}</p><p>必须保留：{intent.must_keep?.join("；") || "未记录"}</p><p>必须避免：{intent.must_avoid?.join("；") || "未记录"}</p><p>创作自由：{intent.creative_freedom || "未记录"}</p>{intent.rationales?.map(item => <p key={item.stable_id}>{item.stable_id}：{item.reason}</p>)}</div> : <p className="text-sm text-slate-500">来源没有记录创作意图。</p>;
}
function RoleTable({ roles }: { roles: Role[] }) {
  return <div className="overflow-x-auto"><table className="w-full text-left text-xs"><thead><tr className="border-b text-slate-500"><th className="p-2">角色 / 类型</th><th className="p-2">要求 / 数量</th><th className="p-2">MIME / 每文件字节上限</th></tr></thead><tbody>{roles.map(role => <tr key={role.role_id} className="border-b"><td className="p-2">{role.role_id} · {role.kind}</td><td className="p-2">{role.required ? "必需" : "可选"} · {role.min_count}–{role.max_count}</td><td className="break-all p-2">{role.allowed_mime.join(", ")} · {role.max_bytes.toLocaleString()} bytes</td></tr>)}</tbody></table></div>;
}
function Inputs({ assets }: { assets: Asset[] }) {
  return <div className="space-y-2">{assets.length === 0 && <p className="text-xs text-slate-500">没有素材输入。</p>}{assets.map((asset, index) => <div key={`${asset.material_revision_id}-${index}`} className="rounded bg-slate-50 p-2 text-xs"><p>MaterialRevision #{asset.material_revision_id} · {asset.role || "输入"} {asset.slot_key || ""}</p><p className="break-all">{asset.content_hash}</p>{asset.rights && <><p>权利：{asset.rights.rights_status} · 公开 {asset.rights.public_use_allowed ? "允许" : "不允许"} · 模型 {asset.rights.model_use_allowed ? "允许" : "不允许"} · 商业 {asset.rights.commercial_use_allowed ? "允许" : "不允许"}</p><p className="whitespace-pre-wrap">继承署名：{asset.rights.attribution_text || "未记录"}</p><Metadata value={asset.rights.license} />{Array.isArray(asset.rights.license.license_obligations) && asset.rights.license.license_obligations.map((obligation, i) => <div key={i}><p>继承许可 #{i + 1}</p><Metadata value={(obligation as { license?: Record<string, unknown> }).license || {}} /></div>)}</>}</div>)}</div>;
}
function PackageView({ value }: { value: Package }) {
  const document = value.package;
  return <div className="space-y-3 rounded-lg border border-slate-200 p-4"><div className="flex flex-wrap items-center justify-between gap-2"><h3 className="font-semibold">冻结包 #{value.id} · {value.package_schema}</h3><StatusBadge status={value.is_current ? "current" : "stale"} /></div><p className="break-all text-xs text-slate-500">包 hash：{value.package_hash}<br />创建：{value.created_at || "未记录"}</p><p className="text-sm">{value.is_current ? "当前来源，可明确准备执行。" : `仅供历史查看：${value.reasons.map(reason).join("；") || "当前性无法确认"}`}</p><p className="whitespace-pre-wrap text-sm">目的：{document.objective}</p><p className="break-all text-xs">来源 {document.source.kind} #{document.source.id} · {document.source.payload_schema} · {document.source.channel_id || "通用"}/{document.source.content_form || "通用"}<br />Payload {document.source.payload_hash}<br />Context {document.source.context_hash}<br />Intent {document.source.creative_intent_hash || "未记录"}</p><p className="text-xs">身份 #{document.context.identity?.id ?? "未记录"} · Brief #{document.context.brief?.id ?? "未记录"} · 事实边界 #{document.context.boundary?.id ?? "未记录"}</p><IntentView intent={document.creative_intent} /><p className="whitespace-pre-wrap text-sm">约束：{document.constraints.join("；") || "未额外指定"}</p><p className="whitespace-pre-wrap text-sm">验收标准：{document.acceptance_criteria.join("；") || "按输出合同人工核对"}</p>{document.director && <p className="text-sm">导演包 · 画幅 {document.director.aspect_ratio || "未记录"} · {document.director.final_render_required ? "仍需返回最终成片" : "已有来源成片"} · 后续正文绑定和审核仍需单独完成。</p>}{document.production_methods && <section className="space-y-2 rounded border p-3"><h4 className="text-sm font-medium">已冻结阶段方法</h4><p className="break-all text-xs">清单 {document.production_methods.manifest_hash}</p>{document.production_methods.stages.map(stage => <div key={stage.stage} className="text-xs"><p>{stage.title} · {stage.origin} · {stage.enabled ? `${stage.methods.length} 项启用` : "已关闭"}</p>{stage.methods.map(method => <p key={method.id} className="break-all">{method.id} · {method.skill_ref || `修订 #${method.revision_id}`} · {method.method_hash}</p>)}{stage.disabled_method_ids.length > 0 && <p>未注入：{stage.disabled_method_ids.join("、")}</p>}</div>)}</section>}<RoleTable roles={document.output_contract.roles} /><details><summary className="cursor-pointer text-sm">精确输入 {document.assets.length} · 证据 {document.evidence.length} · 权利与署名</summary><div className="mt-2 space-y-2"><Inputs assets={document.assets} />{document.evidence.map((item, i) => <p key={i} className="break-all text-xs">FactPackItem #{item.fact_pack_item_id} · {item.snapshot_checksum}</p>)}</div></details></div>;
}
function latestOutput(output: Output, execution: Execution) {
  return !(execution.outputs || []).some(item => item.role_id === output.role_id && item.output_index === output.output_index && item.attempt_no > output.attempt_no);
}
function decisionAllowed(execution: Execution, output: Output, pkg: Package | null, accept: boolean) {
  if (output.state !== "staged" || !latestOutput(output, execution) || !pkg || pkg.id !== execution.package_id || pkg.package_hash !== execution.package_hash) return false;
  if (!["claimed", "in_progress", "blocked", "result_ready", "accepted"].includes(execution.state)) return false;
  return accept ? pkg.is_current : execution.state !== "accepted" || !execution.output_counts.find(role => role.role_id === output.role_id)?.required;
}
function cleanupAllowed(execution: Execution, output: Output) {
  if (execution.state === "unknown" || (execution.state === "blocked" && execution.safe_reason !== "needs_output_replacement")) return false;
  if (["removed", "already_absent"].includes(output.staging_cleanup?.status || "")) return false;
  return ["rejected", "accepted"].includes(output.state) || (output.state === "staged" && ["rejected", "cancelled", "superseded", "failed_before_dispatch"].includes(execution.state));
}
function permissionAllowed(execution: Execution, pkg: Package, output: Output, key: "public_use_allowed" | "model_use_allowed" | "commercial_use_allowed") {
  if (output.kind === "other" && !["text/plain", "text/srt", "application/x-subrip", "text/vtt"].includes(output.mime_type)) return false;
  return [...pkg.package.assets, ...(execution.materialized_inputs || [])].every(asset => asset.rights?.rights_status === "cleared" && asset.rights[key] === true);
}

export default function CreativeExecutionPanel(props: CreativeExecutionPanelProps) {
  return <ScopedCreativeExecutionPanel key={`${props.projectId}:${props.unitId}:${currentUser()}`} {...props} />;
}

function ScopedCreativeExecutionPanel({ projectId, unitId, readOnly, executionId }: CreativeExecutionPanelProps) {
  const actor = useRef(currentUser()).current;
  const base = `/content-projects/${projectId}/units/${unitId}`;
  const mounted = useRef(false);
  const writeLock = useRef(false);
  const readOnlyRef = useRef(readOnly); readOnlyRef.current = readOnly;
  const refreshSequence = useRef(0);
  const refreshController = useRef<AbortController>();
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [fresh, setFresh] = useState(false);
  const [editable, setEditable] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [master, setMaster] = useState<Source | null>(null);
  const [variants, setVariants] = useState<Source[]>([]);
  const [sourceKey, setSourceKey] = useState("");
  const [variantCheck, setVariantCheck] = useState<{ id: number; current: boolean; reasons: string[] } | null>(null);
  const [packages, setPackages] = useState<Package[]>([]);
  const [executions, setExecutions] = useState<Execution[]>([]);
  const [executionPages, setExecutionPages] = useState(1);
  const [moreExecutions, setMoreExecutions] = useState(false);
  const [packageOffset, setPackageOffset] = useState(0);
  const [morePackages, setMorePackages] = useState(false);
  const [packageId, setPackageId] = useState<number | null>(null);
  const packageSelection = useRef<number | null>(null);
  const [pkg, setPackage] = useState<Package | null>(null);
  const [selectedExecutionId, setExecutionId] = useState<number | null>(executionId ?? null);
  const executionSelection = useRef<number | null>(executionId ?? null);
  const [execution, setExecution] = useState<Execution | null>(null);
  const [executionPackage, setExecutionPackage] = useState<Package | null>(null);
  const [readVersion, setReadVersion] = useState(0);
  const [schema, setSchema] = useState("creative.execution.v1");
  const [objective, setObjective] = useState("");
  const [constraints, setConstraints] = useState("");
  const [criteria, setCriteria] = useState("");
  const [roles, setRoles] = useState<RoleDraft[]>([roleDraft()]);
  const [reviewed, setReviewed] = useState("");
  const [productionConfig, setProductionConfig] = useState<{ production_stages?: ProductionStages; origin: string; catalog: ProductionCatalog; methods: CapabilityArtifact[]; methods_total: number } | null>(null);
  const [productionOverride, setProductionOverride] = useState<ProductionStages | null>(null);
  const [productionError, setProductionError] = useState("");
  const [kind, setKind] = useState("agent");
  const [executorKey, setExecutorKey] = useState("");
  const [executorVersion, setExecutorVersion] = useState("");
  const [declareExecutor, setDeclareExecutor] = useState(false);
  const [executorSupport, setExecutorSupport] = useState({ supports_checkpoint: false, supports_revert: false, supports_recover: false });
  const [executorOutputKinds, setExecutorOutputKinds] = useState<Kind[]>([]);
  const [retryParent, setRetryParent] = useState<Execution | null>(null);
  const preparation = useRef<{ input: string; key: string }>();
  const [uncertainPreparation, setUncertainPreparation] = useState(false);
  const [decisions, setDecisions] = useState<Record<number, DecisionDraft>>({});
  const [preview, setPreview] = useState<Preview | null>(null);
  const [previewBusy, setPreviewBusy] = useState(false);
  const previewController = useRef<AbortController>();
  const objectUrl = useRef("");
  const alive = () => mounted.current && actor === currentUser();
  const canEdit = fresh && editable && !readOnly && actor === currentUser();
  const currentVariants = Object.values(variants.reduce<Record<string, Source>>((result, item) => {
    if (item.variant_key && (!result[item.variant_key] || item.revision_no > result[item.variant_key].revision_no)) result[item.variant_key] = item;
    return result;
  }, {}));
  const source = sourceKey.startsWith("master:") ? master && sourceKey === `master:${master.id}` ? master : null : currentVariants.find(item => `variant:${item.id}` === sourceKey) || null;
  const sourceCurrent = !!source && master?.readiness?.state === "current" && (source === master || (source.source_master_revision_id === master.id && variantCheck?.id === source.id && variantCheck.current));
  const directorAllowed = source === master && source?.payload_schema === "video.master.v2";
  const fingerprint = JSON.stringify({ sourceKey, sourceHash: source?.payload_hash, contextHash: source?.context_hash, intent: source?.creative_intent, schema, objective, constraints, criteria, roles, productionOverride });
  const hasUnknown = executions.some(item => item.state === "unknown") || execution?.state === "unknown";
  const canPrepare = canEdit && !!pkg?.is_current && pkg.id === packageId && !hasUnknown && !moreExecutions && !uncertainPreparation;

  useEffect(() => {
    setProductionConfig(null); setProductionOverride(null); setProductionError("");
    if (!sourceCurrent || !source) return;
    const controller = new AbortController();
    const query = source === master ? `source_master_revision_id=${source.id}` : `source_variant_revision_id=${source.id}`;
    request<NonNullable<typeof productionConfig>>(actor, `${base}/production-method-configuration?${query}`, controller.signal)
      .then(value => { if (!controller.signal.aborted && alive()) setProductionConfig(value); })
      .catch(cause => { if (!controller.signal.aborted && alive()) setProductionError(message(cause)); });
    return () => controller.abort();
  }, [sourceKey, source?.id, sourceCurrent]);

  function clearPreview() {
    previewController.current?.abort();
    if (objectUrl.current) URL.revokeObjectURL(objectUrl.current);
    objectUrl.current = ""; setPreview(null); setPreviewBusy(false);
  }
  function choosePackage(id: number) { if (packageSelection.current === id) return; packageSelection.current = id; setPackage(null); setPackageId(id); setRetryParent(null); }
  function chooseExecution(id: number) { if (executionSelection.current === id) return; executionSelection.current = id; clearPreview(); setExecution(null); setExecutionPackage(null); setExecutionId(id); }
  async function refresh(pages = executionPages, offset = packageOffset) {
    refreshController.current?.abort();
    const controller = new AbortController(); refreshController.current = controller;
    const sequence = ++refreshSequence.current;
    setLoading(true); setFresh(false); setError(""); setPackage(null); setExecution(null); setExecutionPackage(null); clearPreview();
    try {
      const [user, project, masters, nextVariants, nextPackages, executionLists] = await Promise.all([
        request<{ role: string }>(actor, "/users/me", controller.signal),
        request<{ status: string; units: { id: number; status: string }[] }>(actor, `/content-projects/${projectId}`, controller.signal),
        request<Page<Source>>(actor, `${base}/master-revisions?limit=1`, controller.signal),
        request<Page<Source>>(actor, `${base}/channel-variants?limit=100`, controller.signal),
        request<Page<Package>>(actor, `${base}/creative-packages?limit=${PAGE_SIZE}&offset=${offset}`, controller.signal),
        Promise.all(Array.from({ length: pages }, (_, index) => request<Page<Execution>>(actor, `${base}/creative-executions?limit=${PAGE_SIZE}&offset=${index * PAGE_SIZE}`, controller.signal))),
      ]);
      if (!alive() || controller.signal.aborted || sequence !== refreshSequence.current) return;
      const unit = project.units.find(item => item.id === unitId);
      setEditable(["admin", "editor"].includes(user.role) && project.status !== "archived" && !!unit && unit.status !== "archived");
      setMaster(masters.items[0] || null); setVariants(nextVariants.items); setPackages(nextPackages.items);
      const rows = executionLists.flatMap(page => page.items);
      setExecutions(rows); setMoreExecutions(executionLists[pages - 1].items.length === PAGE_SIZE); setMorePackages(nextPackages.items.length === PAGE_SIZE);
      setExecutionPages(pages); setPackageOffset(offset);
      setSourceKey(previous => previous || (masters.items[0] ? `master:${masters.items[0].id}` : ""));
      if (packageSelection.current == null) packageSelection.current = nextPackages.items[0]?.id ?? null;
      if (executionSelection.current == null) executionSelection.current = rows[0]?.id ?? null;
      setPackageId(packageSelection.current); setExecutionId(executionSelection.current);
      if (preparation.current && rows.some(item => item.idempotency_key === preparation.current?.key)) setUncertainPreparation(false);
      setFresh(true); setReadVersion(value => value + 1);
    } catch (cause) { if (alive() && !controller.signal.aborted && sequence === refreshSequence.current) setError(message(cause)); }
    finally { if (alive() && sequence === refreshSequence.current) setLoading(false); }
  }
  useEffect(() => {
    mounted.current = true; void refresh();
    return () => { mounted.current = false; refreshController.current?.abort(); previewController.current?.abort(); if (objectUrl.current) URL.revokeObjectURL(objectUrl.current); };
  }, []);
  useEffect(() => { if (executionId != null) chooseExecution(executionId); }, [executionId]);
  useEffect(() => {
    setVariantCheck(null);
    if (!fresh || !source || source === master) return;
    const controller = new AbortController();
    void request<{ drift_reasons: string[] }>(actor, `${base}/channel-variants/${source.id}/checks`, controller.signal)
      .then(value => { if (alive() && !controller.signal.aborted) setVariantCheck({ id: source.id, current: value.drift_reasons.length === 0, reasons: value.drift_reasons }); })
      .catch(cause => { if (alive() && !controller.signal.aborted) setError(message(cause)); });
    return () => controller.abort();
  }, [sourceKey, readVersion, fresh]);
  useEffect(() => {
    setPackage(null);
    if (!fresh || packageId == null) return;
    const controller = new AbortController();
    void request<Package>(actor, `${base}/creative-packages/${packageId}`, controller.signal)
      .then(value => { if (alive() && !controller.signal.aborted && packageSelection.current === packageId) setPackage(value); })
      .catch(cause => { if (alive() && !controller.signal.aborted) setError(message(cause)); });
    return () => controller.abort();
  }, [packageId, readVersion, fresh]);
  useEffect(() => {
    setExecution(null); setExecutionPackage(null); clearPreview();
    if (!fresh || selectedExecutionId == null) return;
    const controller = new AbortController();
    void (async () => {
      try {
        const value = await request<Execution>(actor, `${base}/creative-executions/${selectedExecutionId}`, controller.signal);
        const exactPackage = await request<Package>(actor, `${base}/creative-packages/${value.package_id}`, controller.signal);
        if (alive() && !controller.signal.aborted && executionSelection.current === selectedExecutionId) { setExecution(value); setExecutionPackage(exactPackage); }
      } catch (cause) { if (alive() && !controller.signal.aborted) setError(message(cause)); }
    })();
    return () => controller.abort();
  }, [selectedExecutionId, readVersion, fresh]);

  function buildRequest(): PackageRequest {
    if (!source || !sourceCurrent) throw new Error("请选择已保存且当前有效的 Master 或渠道变体。");
    if (schema === "director.video.v1" && !directorAllowed) throw new Error("导演包需来自当前 Video Master v2。");
    if (!objective.trim() || objective.trim().length > 2000) throw new Error("请填写 1–2000 字的执行目的。");
    const lists = [lines(constraints), lines(criteria)];
    if (lists.some(items => items.length > 50 || items.some(item => item.length > 2000))) throw new Error("约束与验收标准各最多 50 条，每条最多 2000 字。");
    return { ...(source === master ? { source_master_revision_id: source.id } : { source_variant_revision_id: source.id }), ...(productionOverride !== null ? { production_stages: productionOverride } : {}), package_schema: schema, objective: objective.trim(), constraints: lists[0], acceptance_criteria: lists[1], output_contract: { roles: contract(roles) } };
  }
  async function mutate(action: () => Promise<void>) {
    if (writeLock.current || !canEdit || readOnlyRef.current || !alive()) return;
    writeLock.current = true; setBusy(true); setError(""); setNotice("");
    try { await action(); }
    catch (cause) { if (alive()) { setError(message(cause)); setFresh(false); } }
    finally { writeLock.current = false; if (alive()) setBusy(false); }
  }
  async function createPackage() {
    if (reviewed !== fingerprint || !sourceCurrent) return;
    await mutate(async () => {
      const created = await request<Package>(actor, `${base}/creative-packages`, undefined, buildRequest());
      if (!alive()) return;
      choosePackage(created.id); setNotice(`已创建不可变包 #${created.id}，尚未准备或执行。`); await refresh();
    });
  }
  async function prepare() {
    if (!canPrepare || !pkg) return;
    const executor = { executor_kind: kind.trim(), executor_key: executorKey.trim(), executor_version: executorVersion.trim() };
    if (Object.values(executor).some((value, index) => !/^[A-Za-z0-9][A-Za-z0-9_.:-]*$/.test(value) || value.length > [30, 150, 50][index])) { setError("请填写执行者类型、标识和版本，使用字母数字及 . _ : -。"); return; }
    if (declareExecutor && (!executorOutputKinds.length || pkg.package.output_contract.roles.some(role => !executorOutputKinds.includes(role.kind)))) { setError("声明的输出类型须覆盖冻结包的全部角色；不确定能力时请保留未声明。"); return; }
    await mutate(async () => {
      if (retryParent && (retryParent.state !== "failed_before_dispatch" || retryParent.dispatch_certainty !== "not_dispatched" || retryParent.package_id !== pkg.id || Object.entries(executor).some(([key, value]) => retryParent[key as keyof Execution] !== value))) throw new Error("关联重试必须使用确认未发送的原执行及同一执行者。");
      const input = { package_id: pkg.id, ...executor, ...(retryParent ? { retry_of_id: retryParent.id } : {}), ...(declareExecutor ? { metadata: { ...executorSupport, output_kinds: [...executorOutputKinds].sort() } } : {}) };
      const fingerprint = JSON.stringify(input);
      if (preparation.current?.input !== fingerprint) preparation.current = { input: fingerprint, key: crypto.randomUUID() };
      let prepared: Execution;
      try { prepared = await request<Execution>(actor, `${base}/creative-executions`, undefined, { ...input, idempotency_key: preparation.current.key }); }
      catch (cause) { if (alive()) setUncertainPreparation(!(cause instanceof CreativeApiError) || cause.status >= 500); throw cause; }
      if (!alive()) return;
      setUncertainPreparation(false); chooseExecution(prepared.id); setRetryParent(null);
      setNotice(`执行 #${prepared.id}：${STATE_LABEL[prepared.state] || prepared.state}。此操作没有调用执行者。`); await refresh();
    });
  }
  function updateDecision(id: number, patch: Partial<DecisionDraft>) { setDecisions(previous => ({ ...previous, [id]: { ...(previous[id] || decisionDraft()), ...patch } })); }
  async function decide(output: Output, accept: boolean) {
    if (!execution || !decisionAllowed(execution, output, executionPackage, accept)) return;
    const draft = decisions[output.id] || decisionDraft();
    if (accept && !draft.confirmed) return;
    await mutate(async () => {
      if (accept && (!executionPackage || (["public", "model", "commercial"] as const).some(key => draft[key] && (draft.status !== "cleared" || !permissionAllowed(execution, executionPackage, output, `${key === "public" ? "public" : key === "model" ? "model" : "commercial"}_use_allowed`))))) throw new Error("所选权利超出输入素材限制，请核对权利表单。");
      const license = { ...(draft.license.trim() ? { license: draft.license.trim() } : {}), ...(draft.licenseId.trim() ? { license_id: draft.licenseId.trim() } : {}), ...(draft.licenseUrl.trim() ? { license_url: draft.licenseUrl.trim() } : {}) };
      const value = await request<Execution>(actor, `${base}/creative-executions/${execution.id}/outputs/${output.id}/decision`, undefined, { expected_revision: execution.revision_no, decision: accept ? "accept" : "reject", ...(accept ? { rights: { rights_status: draft.status, public_use_allowed: draft.public, model_use_allowed: draft.model, commercial_use_allowed: draft.commercial, attribution_text: draft.attribution.trim() || null, license }, ...(draft.title.trim() ? { title: draft.title.trim() } : {}), attach_to_project: draft.attach } : {}) });
      if (!alive()) return;
      const accepted = value.outputs?.find(item => item.id === output.id);
      setNotice(accept ? `已接受为 MaterialRevision #${accepted?.material_revision_id ?? "待回读"}${draft.attach ? "，并明确附加项目引用" : ""}。使用此素材仍需单独保存正文。` : "已拒绝此输出，历史记录保留；必需槽位需返回新尝试。");
      updateDecision(output.id, { confirmed: false }); await refresh();
    });
  }
  async function cleanupOutput(output: Output) {
    if (!execution || !cleanupAllowed(execution, output) || !canEdit || busy || loading) return;
    if (!window.confirm(`确认清理执行 #${execution.id} 的输出 #${output.id}（${output.role_id}，槽位 ${output.output_index}，尝试 ${output.attempt_no}）？\n哈希：${output.content_hash}\n只移除这份成果的临时暂存副本，移除后无法恢复；输出历史、接受/拒绝决定和正式素材均保留。共用文件的待接受成果会阻止清理；已接受成果须先核对正式素材字节。`)) return;
    await mutate(async () => {
      const value = await request<Execution & { staging_cleanup: Cleanup }>(actor, `${base}/creative-executions/${execution.id}/outputs/${output.id}/cleanup`, undefined, { expected_revision: execution.revision_no, confirm_temporary_only: true });
      if (!alive()) return;
      clearPreview();
      setNotice(value.staging_cleanup.status === "failed" ? `暂存清理未完成，可重试：${reason(value.staging_cleanup.code || "execution_storage_unavailable")}` : value.staging_cleanup.status === "already_absent" ? "暂存副本已不存在，已记录核对结果；输出历史与正式素材保留。" : "已清理临时暂存副本；输出历史、接受/拒绝决定和正式素材保留。");
      await refresh();
    });
  }
  async function previewOutput(output: Output) {
    if (!execution || !alive()) return;
    clearPreview(); const controller = new AbortController(); previewController.current = controller;
    setPreviewBusy(true); setError("");
    try {
      if (output.kind === "video") {
        const session = await request<{ url: string }>(actor, `${base}/creative-executions/${execution.id}/outputs/${output.id}/preview-session`, controller.signal, {});
        if (!session.url.startsWith("/api/v1/content-projects/")) throw new Error("视频预览地址不符合本地授权范围。");
        if (alive() && !controller.signal.aborted) setPreview({ outputId: output.id, url: session.url, mime: output.mime_type });
        return;
      }
      if (output.size_bytes > MAX_BYTES) throw new Error("成果超过受控预览上限。");
      const response = await fetch(`/api/v1${base}/creative-executions/${execution.id}/outputs/${output.id}/content`, { credentials: "same-origin", cache: "no-store", signal: controller.signal, headers: { "X-Studio-User": actor } });
      if (!response.ok) throw new Error(await responseError(response));
      const blob = await response.blob();
      if (blob.size !== output.size_bytes) throw new Error("预览大小与成果记录不一致。");
      const hash = Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256", await blob.arrayBuffer())), byte => byte.toString(16).padStart(2, "0")).join("");
      if (hash !== output.content_hash) throw new Error("预览字节与成果哈希不一致。");
      if (!alive() || controller.signal.aborted) return;
      const mime = output.mime_type;
      if (["image/png", "image/jpeg", "image/webp", "image/gif", "video/mp4", "video/webm", "audio/wav", "audio/x-wav", "audio/mpeg", "audio/ogg", "audio/mp4"].includes(mime)) {
        objectUrl.current = URL.createObjectURL(new Blob([blob], { type: mime })); setPreview({ outputId: output.id, url: objectUrl.current, mime });
      } else if (["text/plain", "text/markdown", "application/json", "text/srt", "application/x-subrip", "text/vtt"].includes(mime)) {
        const text = (await blob.slice(0, 64 * 1024).text()) + (blob.size > 64 * 1024 ? "\n（仅展示前 64 KiB）" : "");
        if (alive() && !controller.signal.aborted) setPreview({ outputId: output.id, text, mime });
      } else throw new Error("此文件类型只提供元数据审阅，不能在页面执行或嵌入预览。");
    } catch (cause) { if (alive() && !controller.signal.aborted) setError(message(cause)); }
    finally { if (alive() && !controller.signal.aborted) setPreviewBusy(false); }
  }
  function updateRole(index: number, patch: Partial<RoleDraft>) { setRoles(previous => previous.map((role, i) => i === index ? { ...role, ...patch } : role)); }

  return <section className="space-y-4 rounded-2xl border border-slate-200 bg-white p-5" aria-label="创作执行包与成果审阅">
    <div className="flex flex-wrap items-center justify-between gap-3"><div><h2 className="text-lg font-semibold">外部创作与成果审阅</h2><p className="mt-1 text-xs text-slate-500">冻结已保存的创作来源，明确准备后由执行者领取；每份成果由你决定是否收入素材库。</p></div><Button size="sm" variant="secondary" disabled={busy || loading} onClick={() => void refresh()}>重新读取状态</Button></div>
    {error && <ErrorBanner message={error} />}{notice && <p role="status" className="rounded-lg bg-emerald-50 p-3 text-sm text-emerald-800">{notice}</p>}
    {loading && <Spinner label="读取当前来源、冻结包与执行状态…" />}
    {!loading && (!canEdit || hasUnknown || moreExecutions || uncertainPreparation) && <p className="rounded-lg bg-amber-50 p-3 text-sm text-amber-800">{!fresh ? "状态未成功读取，先刷新后再操作。" : readOnly || !editable ? "当前身份或已归档项目/单元仅可查看。" : uncertainPreparation ? "准备请求的结果未确认。请重新读取核对原记录；不会再次发送准备请求。" : hasUnknown ? "已有执行结果待核对，禁止新执行与重发。" : "更早的执行记录尚未读取，核对完历史后才可准备新执行。"}</p>}
    <details open className="rounded-lg border border-slate-200 p-4"><summary className="cursor-pointer font-semibold">从当前内容创建冻结包</summary><fieldset disabled={!canEdit || busy || loading} className="mt-3 space-y-3">
      <div className="grid gap-3 sm:grid-cols-2"><Field label="已保存的来源"><select className={inputClass} value={sourceKey} onChange={event => { setSourceKey(event.target.value); setSchema("creative.execution.v1"); }}><option value="">选择来源</option>{sourceKey && ![...(master ? [`master:${master.id}`] : []), ...currentVariants.map(item => `variant:${item.id}`)].includes(sourceKey) && <option value={sourceKey}>原选择 {sourceKey} 已不是当前版本，请明确重选</option>}{master && <option value={`master:${master.id}`}>Master #{master.id} · v{master.revision_no} · {master.payload_schema}</option>}{currentVariants.map(item => <option key={item.id} value={`variant:${item.id}`}>Variant #{item.id} · {item.variant_key} · v{item.revision_no}{item.source_master_revision_id !== master?.id ? " · 来源已过期" : ""}</option>)}</select></Field><Field label="包类型"><select className={inputClass} value={schema} onChange={event => setSchema(event.target.value)}><option value="creative.execution.v1">通用创作包</option><option value="director.video.v1" disabled={!directorAllowed}>视频导演包（Video Master v2）</option></select></Field></div>
      <p className="text-xs text-slate-500">来源：{sourceCurrent ? "当前" : variantCheck?.reasons.map(reason).join("；") || master?.readiness?.reasons.map(reason).join("；") || "尚未确认当前性"} · 读取最近 100 条变体；只使用明确选择的已保存版本。</p>
      {source && <IntentView intent={source.creative_intent} />}
      <details className="rounded-lg border p-3"><summary className="cursor-pointer text-sm font-medium">阶段方法：继承与本次覆盖</summary>
        {productionError && <p role="alert" className="mt-2 text-xs text-amber-700">{productionError}</p>}
        {productionConfig && <div className="mt-3 space-y-3"><label className="flex gap-2 text-sm"><input type="checkbox" checked={productionOverride !== null} onChange={event => setProductionOverride(event.target.checked ? structuredClone(productionConfig.production_stages || {}) : null)} />仅覆盖这次项目执行包，不写回角色</label>
          <ProductionStageControls catalog={productionConfig.catalog} methods={productionConfig.methods} value={productionOverride ?? productionConfig.production_stages} disabled={productionOverride === null || !canEdit} origin={productionOverride !== null ? "本次项目覆盖" : productionConfig.origin} onChange={setProductionOverride} />
          {productionConfig.methods_total > productionConfig.methods.length && <p className="text-xs text-amber-700">当前显示部分适用方法，可在方法库查看其余项。</p>}
        </div>}
      </details>
      <Field label="这次执行要完成什么"><textarea className={inputClass} rows={3} maxLength={2000} value={objective} onChange={event => setObjective(event.target.value)} /></Field>
      <div className="grid gap-3 sm:grid-cols-2"><Field label="额外约束（每行一条）"><textarea className={inputClass} rows={3} value={constraints} onChange={event => setConstraints(event.target.value)} /></Field><Field label="人工验收标准（每行一条）"><textarea className={inputClass} rows={3} value={criteria} onChange={event => setCriteria(event.target.value)} /></Field></div>
      <h3 className="text-sm font-medium">输出合同</h3>{roles.map((role, index) => <div key={index} className="space-y-2 rounded-lg bg-slate-50 p-3"><div className="grid gap-2 sm:grid-cols-3"><Field label={`角色 ${index + 1} 标识`}><input className={inputClass} maxLength={100} value={role.role_id} onChange={event => updateRole(index, { role_id: event.target.value })} /></Field><Field label="类型"><select className={inputClass} value={role.kind} onChange={event => { const kind = event.target.value as Kind; updateRole(index, { kind, mime: MIME_DEFAULT[kind] }); }}>{KINDS.map(kind => <option key={kind}>{kind}</option>)}</select></Field><Field label="允许的 MIME（逗号分隔）"><input className={inputClass} value={role.mime} onChange={event => updateRole(index, { mime: event.target.value })} /></Field></div><div className="grid gap-2 sm:grid-cols-4"><label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={role.required} onChange={event => updateRole(index, { required: event.target.checked, min: event.target.checked ? "1" : "0" })} />必需输出</label><Field label="最少数量"><input type="number" min={role.required ? 1 : 0} max={20} disabled={!role.required} className={inputClass} value={role.min} onChange={event => updateRole(index, { min: event.target.value })} /></Field><Field label="最多数量"><input type="number" min={1} max={20} className={inputClass} value={role.max} onChange={event => updateRole(index, { max: event.target.value })} /></Field><Field label="每文件最多 bytes"><input type="number" min={1} max={MAX_BYTES} className={inputClass} value={role.bytes} onChange={event => updateRole(index, { bytes: event.target.value })} /></Field></div><Button size="sm" variant="ghost" disabled={roles.length === 1} onClick={() => setRoles(previous => previous.filter((_, i) => i !== index))}>移除此角色</Button></div>)}
      <div className="flex flex-wrap gap-2"><Button size="sm" variant="secondary" disabled={roles.length >= 20} onClick={() => setRoles(previous => { let index = previous.length + 1; while (previous.some(role => role.role_id === `output_${index}`)) index += 1; return [...previous, roleDraft(index)]; })}>增加输出角色</Button><Button variant="secondary" disabled={!sourceCurrent} onClick={() => { try { buildRequest(); setReviewed(fingerprint); setError(""); } catch (cause) { setError(message(cause)); } }}>预览待冻结要求</Button><Button disabled={!sourceCurrent || reviewed !== fingerprint} onClick={() => void createPackage()}>明确创建不可变包</Button></div>
      {reviewed === fingerprint && <div className="space-y-2 rounded-lg border border-indigo-200 p-3"><p className="text-sm">待冻结预览：{sourceKey} · {schema}</p><p className="whitespace-pre-wrap text-sm">目的：{objective}</p><p className="whitespace-pre-wrap text-xs">约束：{constraints || "未指定"}<br />验收：{criteria || "按合同核对"}</p><RoleTable roles={contract(roles)} /><p className="break-all text-xs">来源 hash：{source?.payload_hash} · 上下文 {source?.context_hash}<br />素材 {source?.assets.length || 0} · 证据 {source?.evidence.length || 0}；精确输入权利以服务端冻结包为准。</p></div>}
    </fieldset></details>
    <div className="space-y-3"><h3 className="font-semibold">冻结包历史</h3><div className="flex flex-wrap gap-2">{packages.map(item => <Button key={item.id} size="sm" variant={item.id === packageId ? "primary" : "secondary"} disabled={busy || loading} onClick={() => choosePackage(item.id)}>#{item.id} · {item.is_current ? "当前" : "历史"}</Button>)}</div>{!packages.length && !loading && <p className="text-sm text-slate-500">此页暂无冻结包。</p>}<div className="flex gap-2">{packageOffset > 0 && <Button size="sm" variant="secondary" disabled={busy || loading} onClick={() => void refresh(executionPages, Math.max(0, packageOffset - PAGE_SIZE))}>较新的包</Button>}{morePackages && <Button size="sm" variant="secondary" disabled={busy || loading} onClick={() => void refresh(executionPages, packageOffset + PAGE_SIZE)}>更早的包</Button>}</div>{pkg && <PackageView value={pkg} />}
      <fieldset disabled={!canPrepare || busy || loading} className="space-y-3 rounded-lg bg-slate-50 p-3"><p className="text-sm">准备包 #{pkg?.id ?? "未选择"}：仅建立持久执行记录，随后由外部执行者明确领取并开始。</p>{retryParent && <p className="text-xs">关联发送前失败执行 #{retryParent.id}；使用原执行者，新记录保留重试来源。</p>}<div className="grid gap-3 sm:grid-cols-3"><Field label="执行者类型"><input className={inputClass} maxLength={30} value={kind} onChange={event => setKind(event.target.value)} /></Field><Field label="执行者标识"><input className={inputClass} maxLength={150} value={executorKey} onChange={event => setExecutorKey(event.target.value)} placeholder="明确填写本机执行者" /></Field><Field label="执行者版本"><input className={inputClass} maxLength={50} value={executorVersion} onChange={event => setExecutorVersion(event.target.value)} /></Field></div>
        <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={declareExecutor} onChange={event => setDeclareExecutor(event.target.checked)} />明确填写此版本执行者的能力声明（可保留未声明）</label>
        {declareExecutor && <div className="space-y-2"><p className="text-xs text-slate-500">仅记录执行者自述，不代表运行核验或自动调用。勾选表示支持，未勾选表示不支持；声明随本次执行冻结。</p><div className="flex flex-wrap gap-3">{(["supports_checkpoint", "supports_revert", "supports_recover"] as const).map(key => <label key={key} className="flex items-center gap-2 text-sm"><input type="checkbox" checked={executorSupport[key]} onChange={event => setExecutorSupport(previous => ({ ...previous, [key]: event.target.checked }))} />{METADATA_LABEL[key]}</label>)}</div><p className="text-xs">声明可产出的类型（至少一项，须覆盖冻结包角色）：</p><div className="flex flex-wrap gap-3">{KINDS.map(outputKind => <label key={outputKind} className="flex items-center gap-2 text-sm"><input type="checkbox" checked={executorOutputKinds.includes(outputKind)} onChange={event => setExecutorOutputKinds(previous => event.target.checked ? [...previous, outputKind] : previous.filter(item => item !== outputKind))} />{{ image: "图片", video: "视频", audio: "音频", other: "文本 / 项目文件" }[outputKind]}</label>)}</div></div>}
        <Button disabled={!executorKey.trim() || !executorVersion.trim() || (declareExecutor && !executorOutputKinds.length)} onClick={() => void prepare()}>明确准备执行（不发送）</Button></fieldset>
    </div>
    <div className="space-y-3"><h3 className="font-semibold">执行历史与待审阅成果</h3><div className="flex flex-wrap gap-2">{executions.map(item => <Button key={item.id} size="sm" variant={item.id === selectedExecutionId ? "primary" : "secondary"} disabled={busy || loading} onClick={() => chooseExecution(item.id)}>#{item.id} · {STATE_LABEL[item.state] || item.state}</Button>)}</div>{!executions.length && !loading && <p className="text-sm text-slate-500">尚无执行记录。</p>}{moreExecutions && <Button variant="secondary" size="sm" disabled={busy || loading || executionPages >= 10} onClick={() => void refresh(executionPages + 1)}>读取更早的执行（已读取 {executions.length} 条）</Button>}{moreExecutions && executionPages >= 10 && <p className="text-xs text-amber-800">已达到 1000 条读取上限；可通过队列的精确执行链接查看，新准备保持关闭。</p>}{selectedExecutionId != null && !execution && !loading && <p className="text-sm text-slate-500">正在读取执行 #{selectedExecutionId} 的精确详情；读取失败时请刷新。</p>}
      {execution && executionPackage && <div className="space-y-3 rounded-lg border border-slate-200 p-4"><div className="flex flex-wrap items-center justify-between gap-2"><h3 className="font-semibold">执行 #{execution.id} · {STATE_LABEL[execution.state] || execution.state}</h3><StatusBadge status={execution.state} /></div><p className="break-all text-xs">版本 {execution.revision_no} · 执行者 {execution.executor_kind}/{execution.executor_key}@{execution.executor_version}<br />包 #{execution.package_id} · {execution.package_hash}<br />发送确定性：{execution.dispatch_certainty} · 重试来源 {execution.retry_of_id ? `#${execution.retry_of_id}` : "无"}<br />创建 {execution.created_at || "未记录"} · 更新 {execution.updated_at || "未记录"}</p>{execution.production_method_receipts && <section className="rounded border p-3 text-xs"><p className="font-medium">方法载入回执（已交给执行者，不代表成品验收）</p>{execution.production_method_receipts.length ? execution.production_method_receipts.map(receipt => <p key={receipt.event_id} className="mt-1 break-all">{receipt.stage} · {receipt.status} · {receipt.method_hashes.join("、") || "无启用方法"}</p>) : <p>尚无执行者载入回执</p>}</section>}{execution.safe_reason && <p className="rounded bg-amber-50 p-2 text-sm text-amber-800">阻碍：{reason(execution.safe_reason)}</p>}{execution.state === "unknown" && <p className="text-sm text-violet-800">先由原执行者核对实际结果及检查点。此页面不会重发、恢复或把未知状态改成成功。</p>}<details><summary className="cursor-pointer text-sm">查看此执行的精确冻结包及创作目的</summary><div className="mt-2"><PackageView value={executionPackage} /></div></details><div className="grid gap-3 sm:grid-cols-2"><div><h4 className="mb-1 text-sm font-medium">检查点</h4><Metadata value={execution.checkpoint} />{execution.checkpoint_binding && <div className="mt-2"><p className="text-xs font-medium">精确检查点绑定</p><Metadata value={execution.checkpoint_binding} /></div>}</div><div><h4 className="mb-1 text-sm font-medium">恢复与回读</h4><Metadata value={execution.recovery} /></div></div>
        <p className="break-all text-xs text-slate-600">能力声明：{execution.executor_descriptor?.declaration_status === "declared" ? `执行者自述，未运行核验 · 检查点 ${execution.executor_descriptor.supports_checkpoint ? "支持" : "不支持"} · 撤回 ${execution.executor_descriptor.supports_revert ? "支持" : "不支持"} · 恢复 ${execution.executor_descriptor.supports_recover ? "支持" : "不支持"} · 输出 ${execution.executor_descriptor.output_kinds?.join(" / ")}` : "未完整声明（旧记录保持原行为，不推断能力）"}。专业工具实际项目状态由执行者负责，页面不自动恢复或调用工具。</p>
        <div className="overflow-x-auto"><table className="w-full text-left text-xs"><thead><tr className="border-b text-slate-500"><th className="p-2">角色 / 合同</th><th className="p-2">有效暂存 / 已接受</th><th className="p-2">缺少 / 待替换槽位</th></tr></thead><tbody>{execution.output_counts.map(role => <tr key={role.role_id} className="border-b"><td className="p-2">{role.role_id} · {role.required ? "必需" : "可选"} {role.min_count}–{role.max_count}</td><td className="p-2">{role.staged_count} / {role.accepted_count}</td><td className="p-2">尚缺 {Math.max(0, role.min_count - role.staged_count)} · 待接受 {Math.max(0, role.min_count - role.accepted_count)} · 替换 {role.rejected_indexes.join(", ") || "无"}</td></tr>)}</tbody></table></div>
        <details><summary className="cursor-pointer text-sm">已实际提供给执行者的输入权利（{execution.materialized_inputs?.length || 0}）</summary><div className="mt-2"><Inputs assets={execution.materialized_inputs || []} /></div></details>
        {execution.state === "failed_before_dispatch" && execution.dispatch_certainty === "not_dispatched" && <Button variant="secondary" disabled={!canEdit || busy || hasUnknown || moreExecutions || uncertainPreparation || !executionPackage.is_current} onClick={() => { choosePackage(execution.package_id); setPackage(executionPackage); setRetryParent(execution); setKind(execution.executor_kind); setExecutorKey(execution.executor_key); setExecutorVersion(execution.executor_version); const descriptor = execution.executor_descriptor; setDeclareExecutor(descriptor?.declaration_status === "declared"); setExecutorSupport({ supports_checkpoint: descriptor?.supports_checkpoint === true, supports_revert: descriptor?.supports_revert === true, supports_recover: descriptor?.supports_recover === true }); setExecutorOutputKinds(descriptor?.output_kinds || []); }}>选择此记录作为新准备的重试来源</Button>}
        {(execution.outputs || []).length === 0 && <p className="text-sm text-slate-500">尚无暂存成果，缺少的必需角色不会被自动豁免。</p>}
        {(execution.outputs || []).map(output => {
          const draft = decisions[output.id] || decisionDraft();
          const acceptAllowed = canEdit && decisionAllowed(execution, output, executionPackage, true);
          const rejectAllowed = canEdit && decisionAllowed(execution, output, executionPackage, false);
          const stagingRemoved = ["removed", "already_absent"].includes(output.staging_cleanup?.status || "");
          return <article key={output.id} className="space-y-3 rounded-lg border border-slate-200 p-3"><h4 className="text-sm font-semibold">{output.role_id} · 槽位 {output.output_index} · 尝试 {output.attempt_no} · 输出 #{output.id}</h4><p className="text-xs">{output.state === "staged" ? "暂存，尚未入素材库" : output.state === "accepted" ? `已入 MaterialRevision #${output.material_revision_id}` : "已拒绝，保留历史"}{!latestOutput(output, execution) ? " · 已有较新的替换尝试" : ""}</p><p className="break-all text-xs text-slate-500">{output.kind} · {output.mime_type} · {output.size_bytes.toLocaleString()} bytes<br />hash {output.content_hash}<br />提交 {output.created_at || "未记录"}{output.decided_by ? ` · 决定 ${output.decided_by} · ${output.decided_at || ""}` : ""}</p><Metadata value={output.metadata} /><Button size="sm" variant="secondary" disabled={loading || busy || previewBusy || (stagingRemoved && output.state !== "accepted")} onClick={() => void previewOutput(output)}>读取受控成果预览</Button>
            {preview?.outputId === output.id && <div className="rounded bg-slate-50 p-3">{preview.text !== undefined ? <pre className="max-h-80 overflow-auto whitespace-pre-wrap break-words text-xs">{preview.text}</pre> : preview.mime.startsWith("image/") ? <img className="max-h-80 max-w-full" src={preview.url} alt={`${output.role_id} 槽位 ${output.output_index} 的成果预览`} /> : preview.mime.startsWith("video/") ? <video className="max-h-80 max-w-full" src={preview.url} controls preload="metadata" /> : <audio src={preview.url} controls preload="metadata" />}<Button size="sm" variant="ghost" onClick={clearPreview}>关闭预览</Button></div>}
            {output.state === "staged" && latestOutput(output, execution) && <fieldset disabled={!acceptAllowed || busy || loading} className="space-y-3"><p className="text-xs text-slate-500">每份成果单独决定权利，输入的署名与许可义务会继承；未证明的权限默认为不允许。</p><div className="grid gap-3 sm:grid-cols-2"><Field label="素材标题（可选）"><input className={inputClass} maxLength={255} value={draft.title} onChange={event => updateDecision(output.id, { title: event.target.value })} /></Field><Field label="权利状态"><select className={inputClass} value={draft.status} onChange={event => updateDecision(output.id, { status: event.target.value, public: false, model: false, commercial: false, confirmed: false })}><option value="unknown">尚未证明</option><option value="restricted">受限</option><option value="cleared">已确认许可</option></select></Field></div><div className="flex flex-wrap gap-4">{(["public", "model", "commercial"] as const).map(key => <label key={key} className="flex items-center gap-2 text-sm"><input type="checkbox" checked={draft[key]} disabled={draft.status !== "cleared" || !permissionAllowed(execution, executionPackage, output, `${key}_use_allowed`)} onChange={event => updateDecision(output.id, { [key]: event.target.checked, confirmed: false })} />{{ public: "允许公开使用", model: "允许模型使用", commercial: "允许商业使用" }[key]}</label>)}</div><div className="grid gap-3 sm:grid-cols-3"><Field label="许可（可选，不覆盖继承许可）"><input className={inputClass} maxLength={2000} value={draft.license} onChange={event => updateDecision(output.id, { license: event.target.value, confirmed: false })} /></Field><Field label="许可编号（可选）"><input className={inputClass} maxLength={2000} value={draft.licenseId} onChange={event => updateDecision(output.id, { licenseId: event.target.value, confirmed: false })} /></Field><Field label="许可链接（可选）"><input className={inputClass} maxLength={2000} value={draft.licenseUrl} onChange={event => updateDecision(output.id, { licenseUrl: event.target.value, confirmed: false })} /></Field></div><Field label="额外署名（继承署名会保留）"><textarea className={inputClass} rows={2} maxLength={4000} value={draft.attribution} onChange={event => updateDecision(output.id, { attribution: event.target.value, confirmed: false })} /></Field><label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={draft.attach} onChange={event => updateDecision(output.id, { attach: event.target.checked, confirmed: false })} />同时明确添加到当前项目素材引用</label><label className="flex items-start gap-2 text-sm"><input type="checkbox" checked={draft.confirmed} onChange={event => updateDecision(output.id, { confirmed: event.target.checked })} />我已审阅这份成果，并确认以上权利与署名决定</label><Button disabled={!draft.confirmed} onClick={() => void decide(output, true)}>明确接受到素材库</Button></fieldset>}
            {output.state === "staged" && latestOutput(output, execution) && <Button size="sm" variant="danger" disabled={!rejectAllowed || busy || loading} onClick={() => void decide(output, false)}>拒绝此输出{execution.output_counts.find(role => role.role_id === output.role_id)?.required ? "，要求同槽位替换" : ""}</Button>}
            {output.staging_cleanup && <p className="text-xs text-slate-500">暂存清理：{output.staging_cleanup.status === "removed" ? "临时副本已移除，历史与正式素材保留" : output.staging_cleanup.status === "already_absent" ? "临时副本已不存在，历史与正式素材保留" : output.staging_cleanup.status === "pending" ? "已记录意图，结果待核对，可重新读取后重试" : `未完成，可重试：${reason(output.staging_cleanup.code || "execution_storage_unavailable")}`}</p>}
            {cleanupAllowed(execution, output) && <Button size="sm" variant="danger" disabled={!canEdit || busy || loading} onClick={() => void cleanupOutput(output)}>明确清理此输出的临时副本</Button>}
          </article>;
        })}<p className="text-xs text-slate-500">接受只建立精确 MaterialRevision，项目引用由表单明确选择。使用成果须另行绑定并保存 Master / Variant；审批和发布沿用原流程。</p>
      </div>}
    </div>
  </section>;
}
