import { ApiError } from "../api";

const regenerate = "请点本阶段的「再次生成（新尝试）」。";
const changedLabels: Record<string, string> = {
  upstream: "前面采用的内容（比如脚本）", master: "当前主稿", facts: "事实资料", references: "引用的资料",
  settings: "本阶段的方法或设置", model: "模型设置", context: "项目资料",
};
const texts: Record<string, string> = {
  stage_attempt_not_current: "这份结果已经不是最新的一次，请刷新页面看最新结果。",
  stage_already_accepted: "这份结果已经采用过了，刷新页面即可看到。",
  stage_output_changed: "这份结果在你打开后有变化，请刷新页面再确认。",
  stage_resolution_changed: `生成这份结果后，本阶段的输入有变化，需要重新生成。${regenerate}`,
  creative_method_candidate_changed: "你选的候选已经变了，请刷新页面重新选择。",
  stage_material_model_use_blocked: "这份结果引用的素材已经不能用了（被撤回、归档或取消了模型使用授权），请核对素材后重新生成。",
  stage_master_revision_conflict: "主稿在这期间被保存过新版本，请刷新页面再确认。",
  stage_feedback_readonly: "当前账号没有修改权限。",
  stage_provider_rejected: "模型服务返回了错误，没有生成内容，可以直接重新生成。",
  stage_dispatch_unknown: "调用模型没拿到确定结果，请求可能已经到了模型那边。确认后可以放弃这次结果再重新生成。",
  stage_unknown_reconciliation_required: "这一步上次的结果还不确定，要先放弃那次结果，才能重新生成。",
  stage_reconciliation_required: "这一步上次的结果还不确定，要先放弃那次结果，才能继续。",
};

export function stageErrorText(cause: unknown, fallback = "操作没成功，请刷新后重试。") {
  if (!(cause instanceof ApiError)) return fallback;
  const code = cause.message;
  if (code === "stage_adoption_context_changed") {
    const changed = ((cause.detail as { changed?: string[] } | undefined)?.changed || []).map(key => changedLabels[key] || key);
    return `${changed.length ? `生成这份结果后，${changed.join("、")}变了` : "生成这份结果后，它依据的内容变了"}，需要重新生成。${regenerate}`;
  }
  return texts[code] || `操作没成功（${cause.status} · ${code}）`;
}
