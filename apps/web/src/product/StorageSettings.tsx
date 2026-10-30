import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api, ApiError, currentUser } from "../api";
import { Button, ErrorBanner, Field, Spinner, inputClass } from "../components/ui";

type Storage = {
  library: { source_id: number | null; label: string | null; path: string | null; write_folder: string | null; reachable: boolean };
  common: { path: string; reachable: boolean };
  local: { path: string; reachable: boolean; env_locked: boolean; next_path: string | null };
  move: { state: string; total?: number; done?: number; target?: string; error?: string | null };
  edit_proxy: { enabled: boolean };
};

function errorText(error: unknown) {
  const detail = error instanceof ApiError ? error.detail as { message?: string } | string | undefined : undefined;
  if (typeof detail === "object" && detail?.message) return detail.message;
  return error instanceof Error ? error.message : "操作失败";
}

function Status({ ok }: { ok: boolean }) {
  return <span className={`rounded-full px-2 py-0.5 text-xs ${ok ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-800"}`}>{ok ? "可用" : "未连接"}</span>;
}

export default function StorageSettings({ editable }: { editable: boolean }) {
  const storage = useQuery({ queryKey: ["storage-settings", currentUser()], queryFn: () => api.get<Storage>("/settings/storage"), retry: false,
    refetchInterval: query => query.state.data?.move.state === "copying" ? 2000 : false });
  const [libraryPath, setLibraryPath] = useState("");
  const [localPath, setLocalPath] = useState("");
  const [commonPath, setCommonPath] = useState("");
  const [check, setCheck] = useState<{ matched: number; total: number; path: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  async function changeLibrary(confirm: boolean) {
    const path = confirm && check ? check.path : libraryPath.trim();
    setBusy(true); setError(""); setNotice("");
    try {
      const result = await api.put<{ switched: boolean; matched: number; total: number }>("/settings/storage/library", { path, confirm });
      if (result.switched) { setCheck(null); setLibraryPath(""); setNotice("素材库位置已更换。"); await storage.refetch(); }
      else setCheck({ matched: result.matched, total: result.total, path });
    } catch (cause) { setError(errorText(cause)); } finally { setBusy(false); }
  }
  async function changeCommon() {
    setBusy(true); setError(""); setNotice("");
    try { await api.put("/settings/storage/common", { path: commonPath.trim() }); setCommonPath(""); setNotice("通用素材库位置已更换。"); await storage.refetch(); }
    catch (cause) { setError(errorText(cause)); } finally { setBusy(false); }
  }
  async function changeProxy(enabled: boolean) {
    setBusy(true); setError(""); setNotice("");
    try { await api.put("/settings/storage/edit-proxy", { enabled }); await storage.refetch(); }
    catch (cause) { setError(errorText(cause)); } finally { setBusy(false); }
  }
  async function moveLocal() {
    if (!window.confirm("把本地工作位置的文件复制到新文件夹，逐个核对后切换。旧文件夹会保留。复制期间不要生成或上传素材，复制完成后需要重启 API 才生效。继续？")) return;
    setBusy(true); setError(""); setNotice("");
    try { await api.post("/settings/storage/local/move", { path: localPath.trim() }); setLocalPath(""); await storage.refetch(); }
    catch (cause) { setError(errorText(cause)); } finally { setBusy(false); }
  }

  if (storage.isPending) return <Spinner label="读取存储位置…" />;
  if (storage.error) return <ErrorBanner message={errorText(storage.error)} />;
  const data = storage.data!;
  const move = data.move;
  return <section aria-label="存储位置" className="space-y-5 rounded-xl border border-slate-200 bg-white p-5">
    <h2 className="text-lg font-semibold">存储位置</h2>
    {error && <ErrorBanner message={error} />}{notice && <p role="status" className="text-sm text-emerald-700">{notice}</p>}
    <div className="space-y-3 rounded-lg border border-slate-200 p-4">
      <div className="flex flex-wrap items-center justify-between gap-2"><h3 className="font-semibold">素材库位置</h3><Status ok={data.library.reachable} /></div>
      <p className="break-all text-sm">{data.library.path || "还没设置"}{data.library.label ? `（${data.library.label}）` : ""}</p>
      <p className="text-xs text-slate-500">所有新素材（拖进来的、AI 生成的、AE 渲染的、配音）都存进素材库里的 <span className="break-all font-mono">{data.library.write_folder || "AIContentStudio"}</span> 文件夹，按 视频 / 图片 / 音频 分开。你自己的文件夹平台只读不写。素材库没连接时，新增素材会提示「素材库未连接」，不会存到别处。</p>
      {editable && <div className="flex flex-wrap items-end gap-2"><Field label="换成这个文件夹（完整路径，例如 /Volumes/U盘名/素材）"><input className={inputClass} value={libraryPath} disabled={busy} onChange={event => { setLibraryPath(event.target.value); setCheck(null); }} /></Field><Button variant="secondary" disabled={busy || !libraryPath.trim()} onClick={() => void changeLibrary(false)}>检查</Button></div>}
      {check && <div className="space-y-2 rounded-lg bg-amber-50 p-3 text-sm text-amber-900"><p>新位置找到已登记文件 {check.matched}/{check.total} 个（大小一致）。{check.matched < check.total ? "找不到的文件切换后会显示为不可用，原位置的文件不受影响。" : ""}</p><Button disabled={busy} onClick={() => void changeLibrary(true)}>确认切换到 {check.path}</Button></div>}
    </div>
    <div className="space-y-3 rounded-lg border border-slate-200 p-4">
      <div className="flex flex-wrap items-center justify-between gap-2"><h3 className="font-semibold">通用素材库位置</h3><Status ok={data.common.reachable} /></div>
      <p className="break-all text-sm">{data.common.path}</p>
      <p className="text-xs text-slate-500">放几乎每个视频都可能用到的素材（特效画面、转场、常用 BGM / 音效等），在 Mac 本地，移动硬盘拔掉也能用。只属于某个项目的素材跟项目放在移动硬盘上。素材详情里点「归入通用素材库」会移到这里。</p>
      {editable && <div className="flex flex-wrap items-end gap-2"><Field label="换成这个文件夹（Mac 本地完整路径，通用素材库为空时才能换）"><input className={inputClass} value={commonPath} disabled={busy} onChange={event => setCommonPath(event.target.value)} /></Field><Button variant="secondary" disabled={busy || !commonPath.trim()} onClick={() => void changeCommon()}>更换</Button></div>}
    </div>
    <div className="space-y-3 rounded-lg border border-slate-200 p-4">
      <h3 className="font-semibold">剪辑代理素材</h3>
      <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={data.edit_proxy.enabled} disabled={busy || !editable} onChange={event => void changeProxy(event.target.checked)} />第三方模型剪辑时用低清代理</label>
      <p className="text-xs text-slate-500">默认关。打开后，大视频素材（长边超过 1920 或码率很高）准备素材时先做一份 720p 代理，放在项目文件夹的 工作/代理/，同一素材只做一次；剪辑用代理，导出仍用原片。剪辑时的临时文件放在项目文件夹的 工作/ 里，小样、成片导出到 导出/。</p>
    </div>
    <div className="space-y-3 rounded-lg border border-slate-200 p-4">
      <div className="flex flex-wrap items-center justify-between gap-2"><h3 className="font-semibold">本地工作位置</h3><Status ok={data.local.reachable} /></div>
      <p className="break-all text-sm">{data.local.path}</p>
      <p className="text-xs text-slate-500">放预览图、临时文件、人工网页视频等执行文件，以及这次改动之前存的旧素材。第三方模型剪辑的文件不放这里，放在项目文件夹里。</p>
      {data.local.env_locked && <p className="text-xs text-amber-800">当前位置由启动参数 AI_STUDIO_MEDIA_ROOT 指定，要在这里修改请先去掉它。</p>}
      {data.local.next_path && <p className="text-sm text-amber-800">已复制并核对到 {data.local.next_path}，重启 API 后生效。旧文件夹保留，什么时候清理由你决定。</p>}
      {move.state === "copying" && <p role="status" className="text-sm">正在复制并核对 {move.done ?? 0}/{move.total ?? 0}…</p>}
      {move.state === "failed" && <p role="alert" className="text-sm text-rose-700">复制没完成：{move.error}。设置没有改，旧位置照常使用。</p>}
      {editable && !data.local.env_locked && move.state !== "copying" && <div className="flex flex-wrap items-end gap-2"><Field label="改到这个空文件夹（完整路径）"><input className={inputClass} value={localPath} disabled={busy} onChange={event => setLocalPath(event.target.value)} /></Field><Button variant="secondary" disabled={busy || !localPath.trim()} onClick={() => void moveLocal()}>复制并切换</Button></div>}
    </div>
  </section>;
}
