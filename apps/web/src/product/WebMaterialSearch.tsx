import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { api, ApiError, currentUser } from "../api";
import { Button, ErrorBanner, inputClass } from "../components/ui";

type Image = { id: string; url: string; alt: string; category: string; accepted?: { material_id: number; material_revision_id: number; content_hash: string } };
type Page = { id: string; url: string; site: string; title: string; preferred: boolean; variant_found: boolean | null; readable: boolean; reason: string | null; rendered: boolean; images: Image[]; has_text: boolean; source_id?: number };
type Search = { id: number; query: string; status: "queued" | "running" | "completed" | "failed" | "interrupted"; error_code: string | null; progress: { stage?: string; done?: number; total?: number }; pages: Page[]; skipped: { url: string; title: string; reason: string }[] };
export type PickedImage = { material_id: number; material_revision_id: number; content_hash: string; category: string };

const MIN_SIDE = 200;
const FAILURES: Record<string, string> = {
  web_material_search_unavailable: "搜索服务用不了：到 设置 → AI 与模型 检查「选题搜索」用的厂商和 Key。",
  web_material_search_interrupted: "上次搜索被中断（平台重启过），重新搜一次。",
  web_material_search_failed: "搜索出错了，已读到的网页保留在下面，可以重新搜一次。",
};
const errorText = (e: unknown) => e instanceof ApiError ? (e.detail as { message?: string } | undefined)?.message || e.message : e instanceof Error ? e.message : "操作失败";

// Previews go through the platform (which checks the address), and only once the picture scrolls into view.
function Thumb({ searchId, image, checked, onToggle, onSmall }: { searchId: number; image: Image; checked: boolean; onToggle: () => void; onSmall: () => void }) {
  const box = useRef<HTMLLabelElement>(null);
  const [src, setSrc] = useState("");
  const [state, setState] = useState<"waiting" | "loading" | "failed">("waiting");
  useEffect(() => {
    const node = box.current;
    if (!node || state !== "waiting") return;
    const watch = new IntersectionObserver(entries => { if (entries.some(entry => entry.isIntersecting)) { setState("loading"); watch.disconnect(); } }, { rootMargin: "200px" });
    watch.observe(node);
    return () => watch.disconnect();
  }, [state]);
  useEffect(() => {
    if (state !== "loading") return;
    let blob = "";
    let live = true;
    void fetch(`/api/v1/web-material-searches/${searchId}/images/${encodeURIComponent(image.id)}`, { headers: { "X-Studio-User": currentUser() } })
      .then(r => r.ok ? r.blob() : null).then(b => {
        if (!live) return;
        if (!b) { setState("failed"); return; }
        blob = URL.createObjectURL(b);
        setSrc(blob);
      }).catch(() => { if (live) setState("failed"); });
    return () => { live = false; if (blob) URL.revokeObjectURL(blob); };
  }, [state, searchId, image.id]);
  if (state === "failed") return null;
  return <label ref={box} className={`relative block w-28 cursor-pointer rounded-lg border p-1 ${checked ? "border-indigo-500 bg-indigo-50" : "border-slate-200 bg-white"}`}>
    {src ? <img src={src} alt={image.alt || "网上图片"} className="h-24 w-full rounded object-contain" onLoad={e => { if (Math.min(e.currentTarget.naturalWidth, e.currentTarget.naturalHeight) < MIN_SIDE) onSmall(); }} />
      : <div className="flex h-24 items-center justify-center text-xs text-slate-400">读取中…</div>}
    {image.accepted ? <span className="mt-1 block text-center text-xs text-emerald-700">已保存</span>
      : <span className="mt-1 flex items-center justify-center gap-1 text-xs text-slate-600"><input type="checkbox" checked={checked} onChange={onToggle} />选这张</span>}
  </label>;
}

export default function WebMaterialSearch({ skuId, projectId, unitId, defaultQuery, pickLabel, readOnly, onPicked }: {
  skuId?: number; projectId?: number; unitId?: number; defaultQuery: string; pickLabel: string; readOnly?: boolean;
  onPicked?: (items: PickedImage[]) => void;
}) {
  const client = useQueryClient();
  const key = ["web-material-search", currentUser(), skuId ?? null, projectId ?? null];
  const latest = useQuery({
    queryKey: key, retry: false,
    queryFn: () => api.get<{ search: Search | null }>(`/web-material-searches/latest?${skuId ? `sku_id=${skuId}` : `project_id=${projectId}`}`),
    refetchInterval: query => ["queued", "running"].includes(query.state.data?.search?.status || "") ? 3000 : false,
  });
  const search = latest.data?.search || null;
  const [query, setQuery] = useState(defaultQuery);
  const [picked, setPicked] = useState<Set<string>>(new Set());
  const [small, setSmall] = useState<Set<string>>(new Set());
  const [busy, setBusy] = useState(false);
  const [issue, setIssue] = useState("");
  const [notice, setNotice] = useState("");
  useEffect(() => { if (search?.query && !query) setQuery(search.query); }, [search?.query]);
  useEffect(() => { setPicked(new Set()); setSmall(new Set()); }, [search?.id]);
  const running = search && ["queued", "running"].includes(search.status);

  async function start() {
    setBusy(true); setIssue(""); setNotice("");
    try {
      await api.post("/web-material-searches", { query: query.trim(), ...(skuId ? { sku_id: skuId } : { project_id: projectId, unit_id: unitId }) });
      await client.invalidateQueries({ queryKey: key });
    } catch (e) { setIssue(errorText(e)); } finally { setBusy(false); }
  }
  async function accept() {
    if (!search || !picked.size) return;
    setBusy(true); setIssue(""); setNotice("");
    try {
      const result = await api.post<{ items: (PickedImage & { image_id: string })[] }>(`/web-material-searches/${search.id}/accept`, { image_ids: [...picked] });
      onPicked?.(result.items);
      setPicked(new Set());
      setNotice(skuId ? `已加入 ${result.items.length} 张到上面的资料图，选好类别后点保存。` : `已保存 ${result.items.length} 张到这个项目的素材。`);
      await client.invalidateQueries({ queryKey: key });
      if (projectId) await client.invalidateQueries({ queryKey: ["shared-assets"] });
    } catch (e) { setIssue(errorText(e)); } finally { setBusy(false); }
  }
  async function saveText(page: Page) {
    if (!search) return;
    setBusy(true); setIssue("");
    try {
      await api.post(`/web-material-searches/${search.id}/pages/${page.id}/source`, {});
      await client.invalidateQueries({ queryKey: key });
    } catch (e) { setIssue(errorText(e)); } finally { setBusy(false); }
  }
  function toggle(id: string) { setPicked(previous => { const next = new Set(previous); if (next.has(id)) next.delete(id); else next.add(id); return next; }); }

  const readable = (search?.pages || []).filter(page => page.readable && page.images.length);
  const unreadable = (search?.pages || []).filter(page => !page.readable || !page.images.length);
  return <section aria-label="网上找图" className="rounded-xl border border-slate-200 bg-white p-4">
    <div className="flex flex-wrap items-end gap-2">
      <div className="min-w-[220px] flex-1">
        <span className="mb-1.5 block text-[12.5px] font-medium text-ink-700">网上找图</span>
        <input aria-label="搜索词" className={inputClass} value={query} maxLength={120} disabled={readOnly || busy || !!running} onChange={e => setQuery(e.target.value)}
          // The box sits inside the product form; Enter must search, not save the product.
          onKeyDown={e => { if (e.key === "Enter") { e.preventDefault(); if (query.trim().length >= 2 && !running && !busy) void start(); } }} placeholder={skuId ? "商品名 + 型号" : "产品或主题名，如 OPPO Find X8"} />
      </div>
      <Button disabled={readOnly || busy || !!running || query.trim().length < 2} onClick={() => void start()}>{running ? "搜索中…" : search ? "重新搜" : "开始搜"}</Button>
    </div>
    <p className="mt-1.5 text-[12px] text-ink-500">去品牌官网、经销商、小电商站点和测评站点找图；淘宝、天猫、京东、拼多多读不了，会跳过。只有你勾选的图才保存，不用别家店的价格、销量和评价。</p>
    {issue && <div className="mt-2"><ErrorBanner message={issue} /></div>}
    {notice && <p className="mt-2 text-sm text-emerald-700">{notice}</p>}
    {search && <div className="mt-3 space-y-3">
      {running && <p className="text-sm text-slate-600">{search.progress.stage === "reading" ? `正在读网页 ${search.progress.done || 0}/${search.progress.total || 0}（读不出来的网页会用后台 Chrome 再读，每页最多约 20 秒）` : "正在搜索…"}</p>}
      {search.error_code && <ErrorBanner message={FAILURES[search.error_code] || "搜索没有完成，可以重新搜一次。"} />}
      {search.status === "completed" && !readable.length && <p className="text-sm text-slate-600">这次没找到能用的图。可以换个搜索词（比如加上品牌名），或者在上面手动粘贴。</p>}
      {readable.map(page => {
        const shown = page.images.filter(image => !small.has(image.id));
        return <div key={page.id} className="rounded-lg border border-slate-200 p-3">
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <span className="font-medium text-slate-900">{page.site}</span>
            {page.preferred && <span className="rounded bg-indigo-50 px-1.5 text-xs text-indigo-700">优先站点</span>}
            {page.rendered && <span className="text-xs text-slate-500">后台 Chrome 读取</span>}
            <a className="min-w-0 flex-1 truncate text-indigo-700 hover:underline" href={page.url} target="_blank" rel="noreferrer noopener">{page.title || page.url}</a>
            {page.has_text && (page.source_id ? <span className="text-xs text-slate-500">已存为资料 #{page.source_id}</span>
              : <Button size="sm" variant="secondary" disabled={readOnly || busy} onClick={() => void saveText(page)}>存为资料</Button>)}
          </div>
          {page.variant_found === false && <p className="mt-1 text-xs text-amber-700">网页标题里没有你的型号，可能不是同一款，挑之前打开网页核对一下。</p>}
          <div className="mt-2 flex flex-wrap gap-2">{shown.map(image => <Thumb key={image.id} searchId={search.id} image={image} checked={picked.has(image.id)} onToggle={() => toggle(image.id)}
            onSmall={() => setSmall(previous => new Set(previous).add(image.id))} />)}</div>
          {page.images.length > shown.length && <p className="mt-1 text-xs text-slate-400">已隐藏 {page.images.length - shown.length} 张小图</p>}
        </div>;
      })}
      {(unreadable.length > 0 || search.skipped.length > 0) && <details className="text-sm text-slate-600">
        <summary className="cursor-pointer">读不到或跳过的网页 {unreadable.length + search.skipped.length} 个</summary>
        <ul className="mt-2 space-y-1">
          {unreadable.map(page => <li key={page.id}><a className="text-indigo-700 hover:underline" href={page.url} target="_blank" rel="noreferrer noopener">{page.title || page.url}</a> · {page.reason || "没有图片"}</li>)}
          {search.skipped.map(item => <li key={item.url}><a className="text-indigo-700 hover:underline" href={item.url} target="_blank" rel="noreferrer noopener">{item.title || item.url}</a> · {item.reason}</li>)}
        </ul>
      </details>}
      {readable.length > 0 && <div className="flex items-center gap-3">
        <Button disabled={readOnly || busy || !picked.size} onClick={() => void accept()}>{busy ? "保存中…" : `${pickLabel}（${picked.size}）`}</Button>
        <span className="text-xs text-slate-500">勾选的图会下载保存，并记下来源网页；不是品牌官方的图版权属于原网站，用不用由你决定。</span>
      </div>}
    </div>}
  </section>;
}
