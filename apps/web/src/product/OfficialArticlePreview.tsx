import { useEffect, useState } from "react";
import { currentUser } from "../api";
import { previewByteHash } from "./previewByteHash";

export type OfficialArticleRender = {
  schema: string;
  renderer: string;
  renderer_version: string;
  title: string;
  author: string;
  digest: string;
  html_template: string;
  render_hash: string;
  status: string;
  reasons: string[];
  remote_contract: string;
  asset_slots: { slot_key: string; usage: string; block_id?: string; material_revision_id: number; content_hash: string }[];
};

export function OfficialArticlePreview({ render, path }: { render: OfficialArticleRender; path: string }) {
  const [loaded, setLoaded] = useState<{ key: string; html: string; error: string } | null>(null);
  const actor = currentUser();
  const key = JSON.stringify([actor, path, render.html_template, render.asset_slots]);
  useEffect(() => {
    const controller = new AbortController();
    let disposed = false, timedOut = false;
    const timeout = window.setTimeout(() => { timedOut = true; controller.abort(); }, 20000);
    async function load() {
      let html = render.html_template;
      let totalBytes = 0;
      try {
        for (const slot of render.asset_slots.filter(slot => slot.usage === "inline")) {
          const placeholder = `src="aics-resource:${slot.slot_key}"`;
          if (html.split(placeholder).length !== 2) throw new Error("素材槽与冻结位置不匹配");
          const response = await fetch(`/api/v1${path}/renders/${slot.material_revision_id}`, { headers: { "X-Studio-User": actor }, signal: controller.signal });
          if (!response.ok) throw new Error(`实时权利或版本校验失败 (${response.status})`);
          const mime = (response.headers.get("Content-Type") || "").split(";")[0].trim();
          if (!["image/png", "image/jpeg"].includes(mime)) throw new Error("图片格式尚不支持官方预览");
          if (!response.body) throw new Error("缺少图片字节");
          const reader = response.body.getReader(), chunks: ArrayBuffer[] = [];
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            totalBytes += value.byteLength;
            if (totalBytes > 8 * 1024 * 1024) { await reader.cancel(); throw new Error("超出本地预览字节预算；不代表平台大小限制已核实"); }
            chunks.push(new Uint8Array(value).buffer);
          }
          const blob = new Blob(chunks, { type: mime });
          const bytes = await blob.arrayBuffer();
          const hash = await previewByteHash(bytes);
          if (hash !== slot.content_hash) throw new Error("字节哈希不匹配");
          if (controller.signal.aborted) return;
          // Opaque-origin sandbox frames cannot load parent-origin blob URLs; keep the sandbox intact.
          let binary = "";
          for (const byte of new Uint8Array(bytes)) binary += String.fromCharCode(byte);
          const url = `data:${blob.type};base64,${btoa(binary)}`;
          html = html.replace(placeholder, `src="${url}"`);
        }
        if (!disposed && !controller.signal.aborted) setLoaded({ key, html, error: "" });
      } catch (cause) {
        if (!disposed) setLoaded({ key, html: render.html_template, error: `冻结正文图片不可预览：${timedOut ? "读取超时" : cause instanceof Error ? cause.message : "读取失败"}` });
      } finally {
        window.clearTimeout(timeout);
      }
    }
    void load();
    return () => { disposed = true; window.clearTimeout(timeout); controller.abort(); };
  }, [key]);
  const current = loaded?.key === key ? loaded : null;
  // Frozen HTML is data, not an application surface: deny scripts, remote bytes and top-level navigation.
  const styles = render.renderer_version === "3" ? "'unsafe-inline'" : "'none'";
  const source = '<!doctype html><html><head><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; script-src \'none\'; style-src ' + styles + '; img-src data:; connect-src \'none\'; frame-src \'none\'; form-action \'none\'; base-uri \'none\'"></head><body>' + (current?.html ?? render.html_template) + '</body></html>';
  return <section aria-label="冻结公众号适配表示" className="space-y-3 rounded-lg border border-indigo-200 p-4">
    <h5 className="font-semibold">公众号审批时冻结的 HTML</h5>
    <p className="text-sm">{render.title} · 作者：{render.author || "未指定"} · 摘要：{render.digest || "未指定"}</p>
    <p className="text-sm text-amber-700">{render.remote_contract === "unresolved_body_limits" ? "远端不可执行：官方正文限制尚未核实" : "本地预览不代表草稿箱写入或发布成功"}</p>
    {render.status !== "local_ready" && <p className="text-sm text-amber-700">适配不可用：{render.reasons.join("、") || "未就绪"}</p>}
    {current?.error && <p role="alert" className="text-sm text-amber-700">{current.error}</p>}
    <iframe title="冻结公众号 HTML 预览" sandbox="" referrerPolicy="no-referrer" srcDoc={source} className="h-80 w-full rounded border bg-white" />
    <p className="text-xs text-slate-500">HTML 来自当前候选的冻结清单，不重读可变稿件。正文图片仅在精确版本/实时权利/字节哈希验证后按冻结槽显示，不加载外部图片，也不改写冻结清单。</p>
    <ul className="space-y-1 text-xs text-slate-600">{render.asset_slots.map(slot => <li key={slot.slot_key} className="break-all">{slot.slot_key} · {slot.usage}{slot.block_id ? ` · Block ${slot.block_id}` : ""} · Revision #{slot.material_revision_id} · {slot.content_hash}</li>)}</ul>
    <p className="break-all text-xs text-slate-500">{render.renderer}@{render.renderer_version} · {render.schema} · 冻结 hash：{render.render_hash}</p>
  </section>;
}
