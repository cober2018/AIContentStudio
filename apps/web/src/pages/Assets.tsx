import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../api";
import { Button, ChannelBadge, EmptyState, Modal, Spinner, StatusBadge } from "../components/ui";

interface AssetRow {
  id: number;
  title: string;
  channel: string;
  status: string;
  fact_pack: { id: number; version: number; checksum: string | null };
  model: { provider: string | null; model: string | null };
  reviewer: string | null;
  approved_revision: number;
  created_at: string | null;
  allowed_formats: string[];
  export_count: number;
}

function copyText(text: string) {
  navigator.clipboard.writeText(text).then(
    () => alert("已复制到剪贴板"),
    () => alert("复制失败"),
  );
}


interface MediaItem {
  id: number;
  kind: string;
  source: string;
  prompt: string | null;
  mime_type: string | null;
  sort_order: number;
  url: string;
}

function MediaPanel({ asset, onClose }: { asset: AssetRow; onClose: () => void }) {
  const queryClient = useQueryClient();
  const [viewing, setViewing] = useState<string | null>(null);
  const { data: media, isLoading } = useQuery({
    queryKey: ["asset-media", asset.id],
    queryFn: () => api.get<MediaItem[]>(`/assets/${asset.id}/media`),
  });
  const upload = useMutation({
    mutationFn: ({ slotId, file }: { slotId: number; file: File }) => {
      const form = new FormData();
      form.append("file", file);
      return api.upload(`/assets/${asset.id}/media/${slotId}/upload`, form);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["asset-media", asset.id] }),
    onError: (e) => alert(e instanceof Error ? e.message : "上传失败"),
  });

  return (
    <Modal title={`配图素材 · ${asset.title.slice(0, 24)}`} onClose={onClose} wide>
      {isLoading ? (
        <Spinner />
      ) : (
        <>
          <p className="mb-3 text-xs leading-relaxed text-slate-400">
            素材统一存放底层素材池，按文章归属展示。占位图来自生成结果的配图说明
            （小红书 image_prompts / 公众号配图建议）；点击占位下方的「上传」替换为实体图，
            历史版本保留。导出 HTML/MD 时图片在公众号编辑器内插入。
          </p>
          <div className="grid grid-cols-3 gap-3">
            {(media || []).map((m) => (
              <div key={m.id} className="rounded-lg border border-slate-200 p-2">
                <button onClick={() => setViewing(m.url)} className="block w-full" title="点击放大">
                  <img src={m.url} alt={m.prompt || "配图"} className="aspect-square w-full rounded object-cover" loading="lazy" />
                </button>
                <div className="mt-1.5 flex items-center gap-1.5">
                  <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[11px] text-slate-500">
                    {m.kind === "cover" ? "封面" : `配图 ${m.sort_order}`}
                  </span>
                  <span className={`rounded px-1.5 py-0.5 text-[11px] ${m.source === "upload" ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"}`}>
                    {m.source === "upload" ? "已上传" : "占位"}
                  </span>
                </div>
                {m.prompt && <p className="mt-1 line-clamp-2 text-[11px] leading-relaxed text-slate-400">{m.prompt}</p>}
                {m.source !== "upload" && (
                  <label className="mt-1.5 block cursor-pointer rounded border border-dashed border-slate-300 px-2 py-1 text-center text-[11px] text-slate-500 hover:bg-slate-50">
                    上传图片
                    <input
                      type="file"
                      accept="image/jpeg,image/png,image/webp"
                      className="hidden"
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) upload.mutate({ slotId: m.id, file });
                      }}
                    />
                  </label>
                )}
              </div>
            ))}
          </div>
        </>
      )}
      {viewing && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-8" onClick={() => setViewing(null)}>
          <img src={viewing} alt="预览" className="max-h-full max-w-full rounded-lg shadow-2xl" />
        </div>
      )}
    </Modal>
  );
}

export default function Assets() {
  const queryClient = useQueryClient();
  const [channel, setChannel] = useState("");
  const [preview, setPreview] = useState<{ filename: string; content: string } | null>(null);
  const [mediaFor, setMediaFor] = useState<AssetRow | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["assets", channel],
    queryFn: () => api.get<AssetRow[]>(`/assets${channel ? `?channel=${channel}` : ""}`),
  });

  const exportAsset = useMutation({
    mutationFn: ({ id, fmt }: { id: number; fmt: string }) =>
      api.post<{ filename: string; content: string }>(`/assets/${id}/export`, { fmt }),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ["assets"] });
      setPreview(result);
    },
    onError: (e) => alert(e instanceof Error ? e.message : "导出失败"),
  });

  return (
    <div className="mx-auto max-w-6xl space-y-4 p-8">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">内容资产库</h1>
        <div className="flex gap-1 rounded-md bg-slate-100 p-0.5 text-sm">
          {[
            ["", "全部"],
            ["douyin", "抖音"],
            ["xiaohongshu", "小红书"],
            ["wechat", "公众号"],
          ].map(([key, label]) => (
            <button
              key={key}
              onClick={() => setChannel(key)}
              className={`rounded px-3 py-1 ${channel === key ? "bg-white font-medium shadow-sm" : "text-slate-500"}`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <Spinner />
      ) : !data || data.length === 0 ? (
        <EmptyState title="暂无资产" hint="审核批准后的内容会进入资产库" />
      ) : (
        <div className="space-y-3">
          {data.map((a) => (
            <div key={a.id} className="rounded-lg border border-slate-200 bg-white p-4">
              <div className="flex flex-wrap items-center gap-3">
                <a
                  href={`/api/v1/assets/${a.id}/cover.svg`}
                  target="_blank"
                  rel="noreferrer"
                  className="block h-[72px] w-28 shrink-0 overflow-hidden rounded-md border border-slate-100"
                  title="查看封面大图"
                >
                  <img
                    src={`/api/v1/assets/${a.id}/cover.svg`}
                    alt={`${a.channel} 封面`}
                    className="h-full w-full object-cover"
                    loading="lazy"
                  />
                </a>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="truncate font-medium text-slate-800">{a.title}</span>
                    <StatusBadge status={a.status} />
                  </div>
                  <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-slate-400">
                    <ChannelBadge channel={a.channel} />
                    <span>
                      FactPack v{a.fact_pack.version} · checksum {a.fact_pack.checksum?.slice(0, 8) || "-"}
                    </span>
                    <span>模型 {a.model.model}</span>
                    <span>审核 {a.reviewer}</span>
                    <span>r{a.approved_revision}</span>
                    <span>导出 {a.export_count} 次</span>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button size="sm" variant="secondary" onClick={() => setMediaFor(a)}>
                    配图
                  </Button>
                  {a.allowed_formats.map((fmt) => (
                    <Button
                      key={fmt}
                      size="sm"
                      variant="secondary"
                      onClick={() => exportAsset.mutate({ id: a.id, fmt })}
                      disabled={exportAsset.isPending}
                    >
                      {fmt === "srt" ? "SRT" : fmt.toUpperCase()}
                    </Button>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {mediaFor && <MediaPanel asset={mediaFor} onClose={() => setMediaFor(null)} />}
      {preview && (
        <Modal title={`导出预览：${preview.filename}`} onClose={() => setPreview(null)} wide>
          <div className="mb-3 flex justify-end gap-2">
            <Button size="sm" onClick={() => copyText(preview.content)}>
              一键复制
            </Button>
          </div>
          <pre className="max-h-[55vh] overflow-y-auto whitespace-pre-wrap rounded-md bg-slate-50 p-4 font-mono text-xs leading-relaxed">
            {preview.content}
          </pre>
        </Modal>
      )}
    </div>
  );
}
