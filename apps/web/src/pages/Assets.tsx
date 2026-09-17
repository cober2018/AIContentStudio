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

export default function Assets() {
  const queryClient = useQueryClient();
  const [channel, setChannel] = useState("");
  const [preview, setPreview] = useState<{ filename: string; content: string } | null>(null);

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
