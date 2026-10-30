import { useEffect, useState } from "react";
import { api, ApiError, currentUser } from "../api";
import { ErrorBanner } from "../components/ui";

export const MAX_PORTRAITS = 3;
type Portrait = { material_revision_id: number; material_id: number | null; usable: boolean };
type Uploaded = { id: number; revisions: { id: number }[] };

function errorText(cause: unknown) {
  const detail = cause instanceof ApiError ? cause.detail as { message?: string } | string | undefined : undefined;
  return typeof detail === "object" && detail?.message ? detail.message : typeof detail === "string" ? detail : cause instanceof Error ? cause.message : "上传失败";
}

// A portrait is an ordinary image in the common library; the persona keeps only its revision id.
export async function uploadPortrait(file: File, personaName: string): Promise<number> {
  const body = new FormData();
  body.append("file", file);
  const parameters = new URLSearchParams({ kind: "image", title: `${personaName} 形象照`, tags: "形象照", rights_status: "cleared", public_use_allowed: "false", model_use_allowed: "true" });
  const material = await api.upload<Uploaded>(`/materials/upload?${parameters}`, body);
  await api.post(`/materials/${material.id}/to-common`);
  return material.revisions[material.revisions.length - 1].id;
}

function Thumb({ src, label }: { src: string; label: string }) {
  return src ? <img src={src} alt={label} className="h-24 w-24 rounded-lg border border-ink-200 object-cover" /> : <div className="h-24 w-24 rounded-lg bg-ink-100" />;
}

function useObjectUrl(load: (() => Promise<Blob | null>) | null, key: string) {
  const [url, setUrl] = useState("");
  useEffect(() => {
    let alive = true;
    let made = "";
    if (load) void load().then(blob => { if (blob && alive) { made = URL.createObjectURL(blob); setUrl(made); } }).catch(() => {});
    return () => { alive = false; if (made) URL.revokeObjectURL(made); };
  }, [key]);
  return url;
}

function LocalThumb({ file }: { file: File }) {
  const url = useObjectUrl(() => Promise.resolve(file), `${file.name}:${file.size}:${file.lastModified}`);
  return <Thumb src={url} label={file.name} />;
}

function StoredThumb({ item }: { item: Portrait }) {
  const url = useObjectUrl(item.material_id ? async () => {
    const response = await fetch(`/api/v1/materials/${item.material_id}/revisions/${item.material_revision_id}/raw`, { headers: { "X-Studio-User": currentUser() } });
    return response.ok ? response.blob() : null;
  } : null, `${item.material_id}:${item.material_revision_id}`);
  return <Thumb src={url} label={`形象照 #${item.material_revision_id}`} />;
}

const HINT = "选填，1–3 张真人照片。生成画面时人物长相照它来；没有形象照，生成画面里不出现人物，只拍商品和场景。";

function FileButton({ disabled, room, onPick }: { disabled: boolean; room: number; onPick: (files: File[]) => void }) {
  return <label className={`inline-flex h-24 w-24 cursor-pointer items-center justify-center rounded-lg border border-dashed border-ink-300 text-[13px] text-ink-500 ${disabled ? "pointer-events-none opacity-50" : "hover:border-accent-500"}`}>
    ＋ 照片<input type="file" accept="image/*" multiple className="hidden" disabled={disabled} onChange={event => { onPick(Array.from(event.target.files || []).slice(0, room)); event.target.value = ""; }} />
  </label>;
}

// New persona form: photos wait locally and go up when the persona is created.
export function PortraitPicker({ files, disabled, onChange }: { files: File[]; disabled: boolean; onChange: (files: File[]) => void }) {
  return <div className="space-y-2">
    <p className="text-[13px] font-medium text-ink-700">形象照（选填）</p>
    <div className="flex flex-wrap gap-3">
      {files.map((file, index) => <div key={`${file.name}:${index}`} className="space-y-1"><LocalThumb file={file} /><button type="button" className="text-[12px] text-ink-500 hover:text-red-600" disabled={disabled} onClick={() => onChange(files.filter((_, at) => at !== index))}>移除</button></div>)}
      {files.length < MAX_PORTRAITS && <FileButton disabled={disabled} room={MAX_PORTRAITS - files.length} onPick={picked => onChange([...files, ...picked])} />}
    </div>
    <p className="text-[12px] text-ink-500">{HINT}</p>
  </div>;
}

// 编辑资料: adding or removing a portrait saves a new revision of the persona profile right away.
export function PersonaPortraitEditor({ personaId, personaName, revision, readOnly, onSaved }: {
  personaId: number; personaName: string; revision: { revision_no: number; profile: Record<string, unknown> } | undefined; readOnly: boolean; onSaved: () => Promise<void>;
}) {
  const [items, setItems] = useState<Portrait[]>([]);
  const [busy, setBusy] = useState(false);
  const [issue, setIssue] = useState("");
  const revisionNo = revision?.revision_no ?? 0;
  useEffect(() => {
    let alive = true;
    api.get<{ items: Portrait[] }>(`/content-personas/${personaId}/portraits`).then(data => { if (alive) setItems(data.items); }).catch(cause => { if (alive) setIssue(errorText(cause)); });
    return () => { alive = false; };
  }, [personaId, revisionNo]);
  async function save(change: () => Promise<number[]>) {
    setBusy(true); setIssue("");
    try {
      const next = await change();
      await api.post(`/content-personas/${personaId}/revisions`, { expected_revision: revisionNo, profile: { ...(revision?.profile || {}), portrait_material_revision_ids: next } });
      await onSaved();
    } catch (cause) { setIssue(errorText(cause)); } finally { setBusy(false); }
  }
  const ids = items.map(item => item.material_revision_id);
  const off = readOnly || busy;
  return <div className="space-y-2">
    <div className="flex flex-wrap gap-3">
      {items.map(item => <div key={item.material_revision_id} className="space-y-1"><StoredThumb item={item} />
        {!item.usable && <p className="text-[12px] text-amber-700">这张不能再用</p>}
        <button type="button" className="text-[12px] text-ink-500 hover:text-red-600" disabled={off} onClick={() => void save(async () => ids.filter(id => id !== item.material_revision_id))}>移除</button></div>)}
      {items.length < MAX_PORTRAITS && <FileButton disabled={off} room={MAX_PORTRAITS - items.length} onPick={picked => void save(async () => [...ids, ...await Promise.all(picked.map(file => uploadPortrait(file, personaName)))])} />}
    </div>
    <p className="text-[12px] text-ink-500">{busy ? "保存中…" : `${HINT} 增删后立即保存为新修订。`}</p>
    {issue && <ErrorBanner message={issue} />}
  </div>;
}
