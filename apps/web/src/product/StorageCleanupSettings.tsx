import { FormEvent, useEffect, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api, currentUser } from "../api";
import { Button, ErrorBanner, Field, Modal, Spinner, inputClass } from "../components/ui";

type Days = { source_document_text_days: number; generation_result_days: number; candidate_material_days: number };
type Stats = Partial<Record<"source_texts_cleared" | "source_text_bytes_freed" | "generation_files_deleted" | "generation_bytes_freed" | "generation_tasks_expired" | "candidate_materials_deleted" | "candidate_bytes_freed", number>> & Record<string, number | boolean>;
type Last = { at: string; trigger: string; stats: Stats; vacuum?: { status: string; bytes_before?: number | null; bytes_after?: number | null }; vacuum_at?: string };
type Overview = {
  sizes: Record<"database" | "generation_results" | "local_materials" | "common_library" | "source_texts", number | null>;
  counts: Record<"source_documents" | "source_documents_with_text" | "candidate_materials" | "candidate_materials_unattached", number>;
  days: Days; defaults: Days; last: Last | null;
};

const dayFields: [keyof Days, string, string][] = [
  ["source_document_text_days", "采集文章全文保留天数", "超过天数、且没被选为选题或作品来源的文章，清空全文，只留标题和链接。"],
  ["generation_result_days", "生成结果文件保留天数", "超过天数仍没采用成素材的生成图片、视频、配音原文件会删除。"],
  ["candidate_material_days", "候选素材保留天数", "超过天数没采用、也没挂到任何项目的候选素材会删除。已采用的素材一律不动。"],
];

function size(bytes: number | null | undefined) {
  if (bytes === null || bytes === undefined) return "未找到";
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  if (bytes < 1024 ** 3) return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  return `${(bytes / 1024 ** 3).toFixed(2)} GB`;
}

const time = (value?: string) => value ? new Date(value).toLocaleString("zh-CN") : "还没有";
const messageOf = (error: unknown, fallback: string) => error instanceof Error ? error.message : fallback;

export default function StorageCleanupSettings() {
  const queryClient = useQueryClient();
  const key = ["storage-cleanup", currentUser()];
  const overview = useQuery({ queryKey: key, queryFn: () => api.get<Overview>("/settings/storage/cleanup"), retry: false });
  const me = useQuery({ queryKey: ["product-settings-user", currentUser()], queryFn: () => api.get<{ role: string }>("/users/me"), retry: false });
  const [days, setDays] = useState<Record<keyof Days, string>>({ source_document_text_days: "", generation_result_days: "", candidate_material_days: "" });
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const data = overview.data;
  useEffect(() => {
    if (data) setDays({ source_document_text_days: String(data.days.source_document_text_days), generation_result_days: String(data.days.generation_result_days), candidate_material_days: String(data.days.candidate_material_days) });
  }, [data]);

  async function saveDays(event: FormEvent) {
    event.preventDefault();
    if (busy) return;
    const payload = Object.fromEntries(Object.entries(days).map(([name, value]) => [name, Number(value)]));
    if (Object.values(payload).some(value => !Number.isInteger(value) || value < 1 || value > 3650)) { setError("天数要填 1 到 3650 之间的整数。"); return; }
    setBusy(true); setError(""); setNotice("");
    try { queryClient.setQueryData(key, await api.put<Overview>("/settings/storage/cleanup/days", payload)); setNotice("保留天数已保存，下次清理按新天数执行。"); }
    catch (cause) { setError(messageOf(cause, "保存失败")); }
    finally { setBusy(false); }
  }

  async function runNow() {
    setConfirming(false); setBusy(true); setError(""); setNotice("");
    try {
      const result = await api.post<{ overview: Overview }>("/settings/storage/cleanup/run", {});
      queryClient.setQueryData(key, result.overview); setNotice("清理完成，结果见下方。");
    } catch (cause) { setError(messageOf(cause, "清理失败")); }
    finally { setBusy(false); }
  }

  if (overview.isLoading) return <Spinner label="读取存储情况…" />;
  if (overview.isError || !data) return <ErrorBanner message={messageOf(overview.error, "无法读取存储情况")} />;
  const editable = me.data?.role === "admin";
  const stats = data.last?.stats ?? {};
  const failed = Object.keys(stats).filter(name => name.endsWith("_error"));
  const rows: [string, string, string][] = [
    ["数据库", size(data.sizes.database), "含采集文章全文、记录等"],
    ["采集文章全文", size(data.sizes.source_texts), `${data.counts.source_documents_with_text} / ${data.counts.source_documents} 篇还留着全文`],
    ["生成结果暂存", size(data.sizes.generation_results), "模型生成后还没采用的原文件"],
    ["本机素材文件", size(data.sizes.local_materials), "放在本机工作文件夹里的素材"],
    ["通用素材库", size(data.sizes.common_library), "Mac 本地通用素材，不会被清理"],
    ["候选素材", `${data.counts.candidate_materials} 条`, `其中 ${data.counts.candidate_materials_unattached} 条没挂项目`],
  ];
  const lastRows: [string, string][] = data.last ? [
    ["清空文章全文", `${stats.source_texts_cleared ?? 0} 篇，省出 ${size(stats.source_text_bytes_freed ?? 0)}`],
    ["删除生成结果文件", `${stats.generation_files_deleted ?? 0} 个，省出 ${size(stats.generation_bytes_freed ?? 0)}`],
    ["删除候选素材", `${stats.candidate_materials_deleted ?? 0} 条，省出 ${size(stats.candidate_bytes_freed ?? 0)}`],
    ["数据库整理压缩", data.last.vacuum ? data.last.vacuum.status === "done" ? `已完成：${size(data.last.vacuum.bytes_before)} → ${size(data.last.vacuum.bytes_after)}` : data.last.vacuum.status === "busy" ? "数据库正忙，下次再试" : "不是本机数据库，跳过" : `本次没到时间（每周一次，上次 ${time(data.last.vacuum_at)}）`],
  ] : [];

  return <section className="space-y-5 rounded-xl border border-slate-200 bg-white p-6" aria-label="存储与清理">
    <div className="space-y-1">
      <h2 className="font-semibold">存储与清理</h2>
      <p className="text-sm text-slate-600">平台每天自动清理一次用不上的大文件，每周整理压缩一次数据库。已采用的素材、移动硬盘上的项目文件和成片都不会动。</p>
    </div>
    {error && <div role="alert"><ErrorBanner message={error} /></div>}
    {notice && <p role="status" className="text-sm text-emerald-700">{notice}</p>}
    <table className="w-full text-sm">
      <thead><tr className="border-b border-slate-200 text-left text-xs text-slate-500"><th className="py-2 font-normal">内容</th><th className="py-2 font-normal">占用</th><th className="py-2 font-normal">说明</th></tr></thead>
      <tbody>{rows.map(([label, value, hint]) => <tr key={label} className="border-b border-slate-100"><td className="py-2">{label}</td><td className="py-2 tabular-nums">{value}</td><td className="py-2 text-slate-500">{hint}</td></tr>)}</tbody>
    </table>
    <div className="space-y-2">
      <h3 className="text-sm font-medium">上次清理</h3>
      {data.last ? <>
        <p className="text-xs text-slate-500">{time(data.last.at)} · {data.last.trigger === "manual" ? "手动清理" : "每日自动清理"}</p>
        <dl className="grid gap-1 text-sm sm:grid-cols-[10rem_1fr]">{lastRows.map(([label, value]) => <div key={label} className="contents"><dt className="text-slate-500">{label}</dt><dd>{value}</dd></div>)}</dl>
        {failed.length > 0 && <p className="text-sm text-amber-800">有 {failed.length} 项清理没完成，下次会再试。</p>}
      </> : <p className="text-sm text-slate-500">还没有清理过。</p>}
    </div>
    <form onSubmit={saveDays} className="space-y-3">
      {dayFields.map(([name, label, hint]) => <Field key={name} label={label} hint={`${hint}默认 ${data.defaults[name]} 天。`}>
        <input type="number" min={1} max={3650} className={inputClass} value={days[name]} disabled={!editable || busy} onChange={event => setDays({ ...days, [name]: event.target.value })} />
      </Field>)}
      {!editable && <p className="text-sm text-slate-500">只有管理员可以修改天数和立即清理。</p>}
      {editable && <div className="flex flex-wrap gap-2"><Button type="submit" disabled={busy}>{busy ? "处理中…" : "保存天数"}</Button><Button variant="secondary" disabled={busy} onClick={() => setConfirming(true)}>立即清理</Button></div>}
    </form>
    {confirming && <Modal title="现在清理？" onClose={() => setConfirming(false)}>
      <p className="text-sm leading-6 text-slate-600">会按上面保存的天数马上清理：清空过期的采集文章全文、删除没采用的生成结果文件和候选素材，并整理压缩数据库。删掉的文件找不回来。清理期间平台可能会卡几秒。</p>
      <div className="mt-5 flex flex-wrap justify-end gap-2"><Button variant="secondary" onClick={() => setConfirming(false)}>取消</Button><Button variant="danger" onClick={() => void runNow()}>确认清理</Button></div>
    </Modal>}
  </section>;
}
