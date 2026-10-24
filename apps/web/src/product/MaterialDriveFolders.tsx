import { useQuery, useQueryClient } from "@tanstack/react-query";
import { AudioLines, Check, Film, FolderOpen, HardDrive, Image as ImageIcon } from "lucide-react";
import { useMemo, useState } from "react";
import { api, currentUser } from "../api";
import { Button, Chip, EmptyState, ErrorBanner, Field, Modal, Notice, Spinner, inputClass } from "../components/ui";
import { DRIVE_STATUS, DriveSource } from "./materialLibraryModel";

type DriveFile = { relative_path: string; kind: "image" | "video" | "audio"; mime_type: string; size_bytes: number; modified_at: number; linked: { material_id: number }[] };
type Scan = { files: DriveFile[]; truncated: boolean };
const ERRORS: Record<string, string> = {
  material_external_unavailable: "硬盘未连接，接上后再试。",
  material_external_volume_changed: "插着的不是登记时那块硬盘。",
  material_source_exists: "这个文件夹已经登记过了。",
  material_source_folder_missing: "找不到这个文件夹，请检查路径。",
  material_external_already_linked: "这个文件已经链接过，内容没有变化。",
};

function errorText(error: unknown) { const text = error instanceof Error ? error.message : "操作失败"; return ERRORS[text] ?? text; }
function size(bytes: number) { return bytes >= 1 << 30 ? `${(bytes / (1 << 30)).toFixed(1)} GB` : bytes >= 1 << 20 ? `${(bytes / (1 << 20)).toFixed(1)} MB` : `${Math.max(1, Math.round(bytes / 1024))} KB`; }

function LinkDialog({ source, files, onClose, onDone }: { source: DriveSource; files: DriveFile[]; onClose: () => void; onDone: (count: number) => void }) {
  const [form, setForm] = useState({ rights: "restricted", public: false, model: true, commercial: "", attribution: "", sourceUrl: "", tags: "" });
  const [state, setState] = useState<{ busy?: boolean; done?: number; error?: string }>({});
  const submit = async () => {
    setState({ busy: true, done: 0 });
    let done = 0;
    for (const file of files) {
      try {
        await api.post(`/material-sources/${source.id}/links`, {
          relative_path: file.relative_path, kind: file.kind, rights_status: form.rights,
          public_use_allowed: form.public, model_use_allowed: form.model,
          commercial_use_allowed: form.commercial === "" ? null : form.commercial === "yes",
          attribution_text: form.attribution.trim() || null, source_url: form.sourceUrl.trim() || null,
          source_kind: form.sourceUrl.trim() ? "web_search" : "upload",
          tags: form.tags.split(/[,，\s]+/).map(tag => tag.trim()).filter(Boolean).slice(0, 30),
        });
        done += 1;
        setState({ busy: true, done });
      } catch (error) {
        setState({ done, error: `${file.relative_path}：${errorText(error)}` });
        return;
      }
    }
    onDone(done);
  };
  return <Modal title={`链接 ${files.length} 个文件`} onClose={onClose} wide>
    <div className="space-y-5">
      <Notice>文件留在硬盘里原地链接，不复制、不改动。之后硬盘里的文件被改了，平台会发现并要求重新链接成新版本。</Notice>
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="使用范围"><select className={inputClass} value={form.rights} onChange={event => setForm({ ...form, rights: event.target.value, public: event.target.value === "restricted" ? false : form.public })}>
          <option value="restricted">仅本地审阅（不公开）</option><option value="cleared">自有素材，权利清楚</option><option value="licensed">已获授权</option>
        </select></Field>
        <Field label="商业使用"><select className={inputClass} value={form.commercial} onChange={event => setForm({ ...form, commercial: event.target.value })}>
          <option value="">未确认</option><option value="yes">允许</option><option value="no">不允许</option>
        </select></Field>
      </div>
      <div className="flex flex-wrap gap-5 text-[13.5px] text-ink-800">
        <label className="inline-flex items-center gap-2"><input type="checkbox" checked={form.model} onChange={event => setForm({ ...form, model: event.target.checked })} />允许 AI 读取和剪辑</label>
        <label className="inline-flex items-center gap-2"><input type="checkbox" disabled={form.rights === "restricted"} checked={form.public} onChange={event => setForm({ ...form, public: event.target.checked })} />允许公开发布</label>
      </div>
      <Field label="原始来源网址（可选）"><input className={inputClass} value={form.sourceUrl} maxLength={1000} placeholder="网上下载的素材填原页面地址" onChange={event => setForm({ ...form, sourceUrl: event.target.value })} /></Field>
      <Field label="署名（可选）" hint="成片里需要标注的作者或来源。"><input className={inputClass} value={form.attribution} maxLength={4000} onChange={event => setForm({ ...form, attribution: event.target.value })} /></Field>
      <Field label="标签（可选）" hint="用空格或逗号分隔，之后可按标签搜索。"><input className={inputClass} value={form.tags} onChange={event => setForm({ ...form, tags: event.target.value })} /></Field>
      {state.error && <ErrorBanner message={state.error} />}
      <div className="flex items-center justify-end gap-3">
        {state.busy && <span className="text-[13px] text-ink-500">已链接 {state.done}/{files.length}…</span>}
        <Button variant="secondary" onClick={onClose}>取消</Button>
        <Button disabled={state.busy} onClick={() => void submit()}>链接</Button>
      </div>
    </div>
  </Modal>;
}

function Folder({ source, showLinked }: { source: DriveSource; showLinked: (id: number) => void }) {
  const client = useQueryClient();
  const scan = useQuery({ queryKey: ["drive-scan", currentUser(), source.id], queryFn: () => api.get<Scan>(`/material-sources/${source.id}/files`), enabled: source.status === "available", retry: false });
  const [filter, setFilter] = useState<"all" | "unlinked">("unlinked");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [dialog, setDialog] = useState(false);
  const [notice, setNotice] = useState("");
  const files = useMemo(() => (scan.data?.files ?? []).filter(file => filter === "all" || !file.linked.length), [scan.data, filter]);
  const groups = useMemo(() => {
    const result = new Map<string, DriveFile[]>();
    for (const file of files) {
      const folder = file.relative_path.includes("/") ? file.relative_path.slice(0, file.relative_path.lastIndexOf("/")) : "（根目录）";
      result.set(folder, [...(result.get(folder) ?? []), file]);
    }
    return [...result.entries()];
  }, [files]);
  const toggle = (path: string) => setSelected(current => { const next = new Set(current); if (next.has(path)) next.delete(path); else next.add(path); return next; });
  const linkedCount = (scan.data?.files ?? []).filter(file => file.linked.length).length;
  return <section className="card overflow-hidden">
    <div className="flex flex-wrap items-center justify-between gap-3 border-b border-ink-200/80 px-6 py-5">
      <div className="min-w-0">
        <p className="flex items-center gap-2 font-serif text-[18px] font-semibold text-ink-900"><HardDrive size={17} />{source.label}</p>
        <p className="mt-1 truncate font-mono text-[12px] text-ink-500">{source.root_path}</p>
      </div>
      <div className="flex items-center gap-2">
        <Chip tone={source.status === "available" ? "good" : "warn"}>{DRIVE_STATUS[source.status]}</Chip>
        {linkedCount > 0 && <Button size="sm" variant="secondary" onClick={() => showLinked(source.id)}>看已链接的 {linkedCount} 个</Button>}
      </div>
    </div>
    {source.status !== "available" ? <p className="px-6 py-8 text-[13.5px] text-ink-600">{source.status === "unavailable" ? "硬盘没有接上。已链接的素材仍在素材库里，只是暂时不能预览和使用；接上硬盘后刷新即可。" : "现在插着的不是登记时那块硬盘，为避免用错文件，暂不读取。"}</p>
      : scan.isPending ? <Spinner label="读取硬盘文件…" /> : scan.isError ? <div className="p-6"><ErrorBanner message={errorText(scan.error)} /></div> : <div>
        <div className="flex flex-wrap items-center gap-3 px-6 py-4">
          <div className="inline-flex gap-1 text-[13px]">{([["unlinked", "未链接"], ["all", "全部文件"]] as const).map(([key, text]) =>
            <button key={key} onClick={() => setFilter(key)} className={`rounded-pill px-3 py-1 ${filter === key ? "bg-ink-900 text-white" : "text-ink-600 hover:bg-ink-100"}`}>{text}</button>)}</div>
          <span className="text-[12.5px] text-ink-500">{files.length} 个文件{scan.data?.truncated ? "（只列出前 2000 个）" : ""}</span>
          <span className="ml-auto" />
          {selected.size > 0 && <Button size="sm" variant="ghost" onClick={() => setSelected(new Set())}>清除选择</Button>}
          <Button size="sm" disabled={!selected.size} onClick={() => setDialog(true)}>链接所选 {selected.size || ""}</Button>
        </div>
        {notice && <div className="px-6 pb-4"><Notice tone="good">{notice}</Notice></div>}
        {!files.length ? <p className="px-6 pb-8 text-[13.5px] text-ink-500">{filter === "unlinked" ? "这个文件夹里的素材都已链接。" : "文件夹里没有可用的图片、视频或音频。"}</p>
          : <div className="max-h-[560px] overflow-y-auto border-t border-ink-200/80">{groups.map(([folder, entries]) => <div key={folder}>
            <p className="sticky top-0 flex items-center gap-2 bg-paper/95 px-6 py-2 text-[12px] text-ink-600 backdrop-blur"><FolderOpen size={13} />{folder}</p>
            <ul>{entries.map(file => {
              const Icon = file.kind === "video" ? Film : file.kind === "audio" ? AudioLines : ImageIcon;
              const on = selected.has(file.relative_path);
              return <li key={file.relative_path}><label className={`flex cursor-pointer items-center gap-3 px-6 py-2.5 text-[13.5px] transition-colors ${on ? "bg-accent-50" : "hover:bg-ink-50"}`}>
                <input type="checkbox" checked={on} onChange={() => toggle(file.relative_path)} />
                <Icon size={15} className="shrink-0 text-ink-400" />
                <span className="min-w-0 flex-1 truncate text-ink-900">{file.relative_path.split("/").pop()}</span>
                {file.linked.length > 0 && <span className="inline-flex items-center gap-1 text-[12px] text-emerald-700"><Check size={13} />已链接</span>}
                <span className="w-20 text-right text-[12px] tabular-nums text-ink-500">{size(file.size_bytes)}</span>
              </label></li>;
            })}</ul>
          </div>)}</div>}
      </div>}
    {dialog && <LinkDialog source={source} files={(scan.data?.files ?? []).filter(file => selected.has(file.relative_path))} onClose={() => setDialog(false)}
      onDone={count => { setDialog(false); setSelected(new Set()); setNotice(`已链接 ${count} 个文件，可以在「全部素材」里看到。`); void client.invalidateQueries({ queryKey: ["drive-scan"] }); void client.invalidateQueries({ queryKey: ["material-library"] }); }} />}
  </section>;
}

export default function MaterialDriveFolders({ showLinked }: { showLinked: (id: number) => void }) {
  const client = useQueryClient();
  const sources = useQuery({ queryKey: ["material-sources", currentUser()], queryFn: () => api.get<{ items: DriveSource[] }>("/material-sources"), retry: false });
  const [adding, setAdding] = useState(false);
  const [form, setForm] = useState({ label: "", path: "" });
  const [state, setState] = useState<{ busy?: boolean; error?: string }>({});
  const add = async () => {
    setState({ busy: true });
    try {
      await api.post("/material-sources", { label: form.label.trim(), root_path: form.path.trim() });
      setAdding(false); setForm({ label: "", path: "" }); setState({});
      await client.invalidateQueries({ queryKey: ["material-sources"] });
    } catch (error) { setState({ error: errorText(error) }); }
  };
  return <div className="space-y-6">
    <div className="flex flex-wrap items-center justify-between gap-3">
      <p className="max-w-2xl text-[13.5px] leading-relaxed text-ink-600">登记一个文件夹（比如移动硬盘里的素材目录），再挑文件链接进素材库。硬盘拔掉时素材不会丢，只是暂时不能用。</p>
      <div className="flex gap-2"><Button variant="secondary" onClick={() => void client.invalidateQueries({ queryKey: ["material-sources"] })}>刷新连接状态</Button><Button onClick={() => setAdding(true)}>登记文件夹</Button></div>
    </div>
    {sources.isPending ? <Spinner /> : sources.isError ? <ErrorBanner message={errorText(sources.error)} /> : !sources.data.items.length
      ? <EmptyState title="还没有登记文件夹" hint="例如 /Volumes/T1000/自媒体素材" action={<Button onClick={() => setAdding(true)}>登记文件夹</Button>} />
      : sources.data.items.map(source => <Folder key={source.id} source={source} showLinked={showLinked} />)}
    {adding && <Modal title="登记素材文件夹" onClose={() => setAdding(false)}>
      <div className="space-y-4">
        <Field label="名称"><input className={inputClass} value={form.label} maxLength={200} placeholder="T1000 自媒体素材" onChange={event => setForm({ ...form, label: event.target.value })} /></Field>
        <Field label="文件夹路径" hint="在 Finder 里选中文件夹，按 ⌥⌘C 复制路径后粘贴。"><input className={`${inputClass} font-mono text-[13px]`} value={form.path} maxLength={1000} placeholder="/Volumes/T1000/自媒体素材" onChange={event => setForm({ ...form, path: event.target.value })} /></Field>
        {state.error && <ErrorBanner message={state.error} />}
        <div className="flex justify-end gap-2"><Button variant="secondary" onClick={() => setAdding(false)}>取消</Button><Button disabled={state.busy || !form.label.trim() || !form.path.trim()} onClick={() => void add()}>登记</Button></div>
      </div>
    </Modal>}
  </div>;
}
