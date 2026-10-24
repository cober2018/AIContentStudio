import { api, ApiError } from "../api";

export type HandoffResult = { master_id: number; ae: Record<string, string>; note: string | null; placed: string[]; waiting: string[]; gaps: string[]; edit?: { status: string; reason?: string } };
export type HandoffStatus = { master_id: number | null; decided: boolean; needs_handoff: boolean; ae: Record<string, string>; ae_shot_ids: string[]; note: string | null; waiting: string[]; gaps: string[] };

function failure(cause: unknown, fallback: string) {
  const detail = cause instanceof ApiError ? cause.detail as { message?: string } | undefined : undefined;
  return detail?.message || (cause instanceof Error && cause.message) || fallback;
}

// Fill empty rows first, wait for the fill to finish, then let the platform place material, decide AE and rebuild the 导演包.
export async function prepareEdit(projectId: number, unitId: number, onStep: (text: string) => void): Promise<HandoffResult> {
  const base = `/content-projects/${projectId}/units/${unitId}`;
  try {
    onStep("正在补齐空着的镜头素材…");
    try { await api.post(`${base}/material-autofill`, {}); }
    catch (cause) { if (!(cause instanceof ApiError && (cause.detail as { code?: string } | undefined)?.code === "material_autofill_nothing_to_fill")) throw cause; }
    for (let waited = 0; waited < 30 * 60; waited += 5) {
      const slots = await api.get<{ shots: { latest: { status: string } | null }[] }>(`${base}/shot-slots`);
      if (!slots.shots.some(slot => slot.latest && ["queued", "running"].includes(slot.latest.status))) break;
      await new Promise(resolve => setTimeout(resolve, 5000));
    }
  } catch (cause) { throw new Error(`补齐素材没完成：${failure(cause, "请稍后重试")}`); }
  onStep("正在准备剪辑：把素材放进主稿、判断哪些镜头要 AE、重做导演包…");
  try { return await api.post<HandoffResult>(`${base}/edit-handoff`, {}); }
  catch (cause) { throw new Error(failure(cause, "准备剪辑没完成，请重试")); }
}

export function handoffSummary(result: HandoffResult) {
  const ae = Object.keys(result.ae).length;
  return [`已准备好剪辑：达芬奇负责全部镜头${ae ? `，其中 ${ae} 个镜头还要 AE 做特效` : ""}。`,
    result.note ? `（${result.note}）` : "",
    result.waiting.length ? `${result.waiting.length} 个镜头有多个候选，待你选。` : "",
    result.gaps.length ? `${result.gaps.length} 个镜头还缺素材。` : "",
    result.edit?.status === "queued" ? "剪辑任务已排队，本机助手会自动开始剪。" : result.edit?.reason ? result.edit.reason : ""].join("");
}
