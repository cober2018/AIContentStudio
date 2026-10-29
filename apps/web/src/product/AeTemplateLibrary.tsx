import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { api, ApiError, currentUser } from "../api";
import { Button, ErrorBanner, Spinner } from "../components/ui";

type Field = { name: string; kind: string; required?: boolean; max?: number };
type Template = {
  id: string; version: string; name: string; category: string | null; use: string; fields: Field[];
  images: { name: string; required?: boolean }[]; duration_ms: { default: number }; alpha?: boolean;
  status: string; installed: boolean; aspects: string[]; previews: string[];
};
const ORDER = ["关键词与标题", "金句与对句", "标注与聚焦", "人物与图形", "数字与图表", "步骤、流程与对比", "开场、章节与转场", "素材与地图", "结尾引导", "商品：亮相", "商品：卖点", "商品：参数与对比", "商品：价格与优惠", "商品：材质与成分", "商品：使用方法", "商品：信任背书", "商品：下单引导"];

function errorText(error: unknown) {
  const detail = error instanceof ApiError ? error.detail as { code?: string } | string | undefined : undefined;
  if (typeof detail === "object" && detail?.code) return detail.code;
  return error instanceof Error ? error.message : "读取失败";
}

// Identity travels in a request header, so the clip is fetched with it and played from a local object URL.
function Preview({ template, aspect }: { template: Template; aspect: string }) {
  const [url, setUrl] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => () => { if (url) URL.revokeObjectURL(url); }, [url]);
  useEffect(() => { setUrl(""); setError(""); }, [template.id, aspect]);
  const key = aspect.replace(":", "x");
  if (!template.previews.includes(key)) return <p className="rounded-lg bg-slate-50 p-4 text-sm text-slate-500">{template.aspects.includes(aspect) ? "这个画幅的预览还没生成。" : "这个模板还没有这个画幅的版本。"}</p>;
  async function load() {
    setBusy(true); setError("");
    try {
      const resp = await fetch(`/api/v1/settings/ae-templates/${template.id}/${template.version}/preview/${key}`, { headers: { "X-Studio-User": currentUser() } });
      if (!resp.ok) throw new Error(`预览读取失败（${resp.status}）`);
      setUrl(URL.createObjectURL(await resp.blob()));
    } catch (cause) { setError(cause instanceof Error ? cause.message : "预览读取失败"); } finally { setBusy(false); }
  }
  if (url) return <video className={`${aspect === "9:16" ? "max-h-[520px]" : "w-full"} rounded-lg bg-black`} src={url} controls autoPlay loop muted playsInline />;
  return <div className="space-y-2"><Button variant="secondary" disabled={busy} onClick={() => void load()}>{busy ? "读取中…" : "播放预览"}</Button>{error && <ErrorBanner message={error} />}</div>;
}

export default function AeTemplateLibrary() {
  const query = useQuery({ queryKey: ["ae-templates", currentUser()], queryFn: () => api.get<{ items: Template[] }>("/settings/ae-templates"), retry: false });
  const [aspect, setAspect] = useState("9:16");
  const [open, setOpen] = useState<string | null>(null);
  if (query.isPending) return <Spinner label="读取模板库…" />;
  if (query.error) return <ErrorBanner message={errorText(query.error)} />;
  const items = query.data!.items;
  const groups = [...ORDER, "其他"].map(category => [category, items.filter(item => (item.category ?? "其他") === category || (category === "其他" && !ORDER.includes(item.category ?? "")))] as const).filter(([, list]) => list.length);
  return <section aria-label="AE 模板库" className="space-y-5 rounded-xl border border-slate-200 bg-white p-5">
    <div className="flex flex-wrap items-start justify-between gap-3">
      <div><h2 className="text-lg font-semibold">AE 模板库</h2>
        <p className="mt-1 max-w-3xl text-sm text-slate-500">做视频时由大模型按内容自己挑模板；你在微调时点名某个效果，就会用那个模板。这里只用来查看有哪些效果、长什么样、要填什么，不在这里出片。「叠加」类叠在画面上用，「整屏」类单独成镜头。</p></div>
      <div role="group" aria-label="画幅" className="flex rounded-lg border border-slate-200 p-0.5 text-sm">{["9:16", "16:9"].map(item => <button key={item} className={`rounded-md px-3 py-1 ${aspect === item ? "bg-slate-900 text-white" : "text-slate-600"}`} onClick={() => setAspect(item)}>{item === "9:16" ? "竖屏 9:16" : "横屏 16:9"}</button>)}</div>
    </div>
    {groups.map(([category, list]) => <div key={category} className="space-y-2">
      <h3 className="text-sm font-semibold text-slate-700">{category} <span className="font-normal text-slate-400">{list.length}</span></h3>
      <div className="grid gap-3 lg:grid-cols-2">{list.map(item => {
        const id = `${item.id}@${item.version}`;
        return <article key={id} className="space-y-2 rounded-xl border border-slate-200 p-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex flex-wrap items-center gap-2"><h4 className="font-semibold text-slate-900">{item.name}</h4><code className="text-xs text-slate-400">{item.id}</code>
              <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[11px] text-slate-500">{item.alpha ? "叠加" : "整屏"}</span>
              <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[11px] text-slate-500">{item.aspects.map(a => a === "9:16" ? "竖屏" : "横屏").join(" · ")}</span>
              {item.status !== "ready" && <span className="rounded bg-amber-50 px-1.5 py-0.5 text-[11px] text-amber-800">草稿，不自动选用</span>}</div>
            <Button variant="ghost" onClick={() => setOpen(open === id ? null : id)}>{open === id ? "收起" : "查看"}</Button>
          </div>
          <p className="text-sm text-slate-600">{item.use}</p>
          {open === id && <div className="space-y-3 border-t border-slate-100 pt-3">
            <Preview template={item} aspect={aspect} />
            <p className="text-xs text-slate-500">要填的文字：{item.fields.map(f => `${f.name}${f.required ? "（必填）" : ""}`).join("、") || "无"}</p>
            <p className="text-xs text-slate-500">图片：{item.images.map(i => `${i.name}${i.required ? "（必填）" : "（可选）"}`).join("、") || "无"} · 默认 {item.duration_ms.default / 1000} 秒</p>
          </div>}
        </article>;
      })}</div>
    </div>)}
  </section>;
}
