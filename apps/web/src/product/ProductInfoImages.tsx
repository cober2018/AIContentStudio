import { useEffect, useState } from "react";
import { api, currentUser } from "../api";
import { inputClass } from "../components/ui";
import { productMaterialCategories } from "./project/ProductSetupFields";

export type InfoImage = { id: number; hash: string; category: string; preview?: string };

const TYPES = ["image/png", "image/jpeg", "image/webp"];

// Saved pictures are read through the authenticated raw endpoint, so <img> gets a blob URL instead of the API path.
function Thumb({ image, url }: { image: InfoImage; url?: string }) {
  const [src, setSrc] = useState(image.preview || "");
  useEffect(() => {
    if (image.preview || !url) return;
    let blob = "";
    let live = true;
    void fetch(url, { headers: { "X-Studio-User": currentUser() } }).then(r => r.ok ? r.blob() : null).then(b => {
      if (!b || !b.type.startsWith("image/")) return;
      blob = URL.createObjectURL(b);
      if (live) setSrc(blob); else URL.revokeObjectURL(blob);
    }).catch(() => undefined);
    return () => { live = false; if (blob) URL.revokeObjectURL(blob); };
  }, [image.preview, url]);
  return src ? <img src={src} alt="商品资料图" className="h-28 w-28 rounded-lg border border-slate-200 bg-slate-50 object-contain" />
    : <div className="flex h-28 w-28 items-center justify-center rounded-lg border border-dashed text-xs text-slate-500">素材 #{image.id}</div>;
}

// Shops block scraping, so detail, spec and certificate pictures come in by hand; certificates must be the real ones.
export default function ProductInfoImages({ value, urls, disabled, onChange, onError }: {
  value: InfoImage[]; urls: Record<string, string>; disabled: boolean;
  onChange: (next: InfoImage[]) => void; onError: (message: string) => void;
}) {
  const [busy, setBusy] = useState(false);
  async function add(files: File[]) {
    const images = files.filter(file => TYPES.includes(file.type));
    if (!images.length) { onError("没有可用的图片（支持 png、jpeg、webp）。先复制图片或截图，再点粘贴框按 ⌘V。"); return; }
    setBusy(true); onError("");
    const added: InfoImage[] = [];
    try {
      for (const file of images) {
        const data = new FormData();
        data.append("file", file);
        const m = await api.upload<{ latest_revision: { id: number; content_hash: string } }>("/materials/upload?kind=image&rights_status=cleared&public_use_allowed=true&model_use_allowed=true", data);
        added.push({ id: m.latest_revision.id, hash: m.latest_revision.content_hash, category: "real_product", preview: URL.createObjectURL(file) });
      }
    } catch (e) { onError(e instanceof Error ? e.message : "上传失败"); }
    finally {
      setBusy(false);
      const fresh = added.filter(item => !value.some(old => old.id === item.id));
      if (fresh.length) onChange([...value, ...fresh]);
    }
  }
  function paste(e: React.ClipboardEvent) {
    e.preventDefault();
    void add(Array.from(e.clipboardData.items).filter(item => item.kind === "file").map(item => item.getAsFile()).filter((file): file is File => !!file));
  }
  // Not a <label>: a label forwards every click in its area to the file input and opens the picker.
  return <div role="group" aria-label="商品资料图">
    <span className="mb-1.5 block text-[12.5px] font-medium text-ink-700">商品资料图（选填，可多张）</span>
    <input type="file" multiple aria-label="选择商品资料图" accept={TYPES.join(",")} disabled={disabled || busy} onChange={e => { void add(Array.from(e.target.files || [])); e.target.value = ""; }} />
    <div tabIndex={0} role="textbox" aria-label="粘贴商品资料图" onPaste={paste} onClick={e => { e.preventDefault(); e.currentTarget.focus(); }} className="mt-2 cursor-text rounded-lg border border-dashed border-slate-300 p-3 text-center text-xs text-slate-500 outline-none focus:border-indigo-500 focus:bg-indigo-50">{busy ? "上传中…" : "点这里，按 ⌘V 粘贴图片；可以连续粘贴多张"}</div>
    {value.length > 0 && <ul className="mt-3 flex flex-wrap gap-3">{value.map(item => <li key={item.id} className="w-28 space-y-1">
      <Thumb image={item} url={urls[String(item.id)]} />
      <select aria-label={`资料图 #${item.id} 类别`} className={`${inputClass} !px-1 !py-1 text-xs`} value={item.category} disabled={disabled} onChange={e => onChange(value.map(row => row.id === item.id ? { ...row, category: e.target.value } : row))}>
        {productMaterialCategories.map(([key, label]) => <option key={key} value={key}>{label}</option>)}
      </select>
      <button type="button" className="text-xs text-red-600 underline" disabled={disabled} onClick={() => onChange(value.filter(row => row.id !== item.id))}>删除</button>
    </li>)}</ul>}
    {value.length > 0 && <p className="mt-1 text-xs text-slate-500">点保存后生效。</p>}
    <span className="mt-1.5 block text-[12px] leading-relaxed text-ink-500">细节图、参数图、证书等。做视频时证书、参数镜头直接用这些原图，不生成。</span>
  </div>;
}
