import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRef, useState } from "react";
import { api } from "../api";
import { Button, Field, Modal, inputClass } from "../components/ui";

// 素材库（V1 PRD 2.0 / material-library-v1）：
// Material = 全局逻辑素材；MaterialRevision = 不可变字节版本；稿件通过 DraftMedia(use) 引用。

interface MusicMetadata {
  scene: string[]; mood: string[]; energy: string[]; instruments: string[];
  vocal: "unknown" | "instrumental" | "vocal"; tempo_bpm: number | null; loop_suitable: boolean | null;
  source: string; license: string; listening_status: "not_listened" | "partially_listened" | "listened";
}
interface MaterialRevision {
  id: number;
  material_id: number;
  revision_no: number;
  status: string;
  source_kind: string;
  source_url: string | null;
  content_hash: string;
  mime_type: string | null;
  rights_status: string | null;
  public_use_allowed: boolean | null;
  provider_key: string | null;
  prompt_text: string | null;
  created_at: string | null;
  duration_ms?: number | null;
  metadata?: { music?: MusicMetadata; tags?: string[]; previous_tags?: string[] };
}

interface MaterialRow {
  id: number;
  kind: string;
  title: string;
  tags: string[];
  status: string;
  created_at: string | null;
  latest_revision: MaterialRevision | null;
  revisions?: MaterialRevision[];
  usage?: { material_id: number; revisions: number };
}

const KINDS = [
  ["image", "图片"],
  ["chart", "图表"],
  ["screenshot", "截图"],
  ["video", "视频"],
  ["audio", "音频"],
  ["brand", "品牌"],
  ["other", "其他"],
] as const;

export function MaterialUploadModal({ onClose }: { onClose: () => void }) {
  const queryClient = useQueryClient();
  const fileRef = useRef<HTMLInputElement>(null);
  const [hasFile, setHasFile] = useState(false);
  const [form, setForm] = useState({
    kind: "image",
    title: "",
    source_kind: "upload",
    rights_status: "cleared",
    public_use_allowed: false,
    source_url: "",
  });
  const [error, setError] = useState("");
  const upload = useMutation({
    mutationFn: () => {
      const body = new FormData();
      body.append("file", fileRef.current?.files?.[0] as File);
      // The existing upload API reads metadata from query parameters, not multipart fields.
      const parameters = new URLSearchParams(Object.entries(form).map(([key, value]) => [key, String(value)]));
      return api.upload<MaterialRow>(`/materials/upload?${parameters}`, body);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["materials"] });
      queryClient.invalidateQueries({ queryKey: ["system-library"] });
      onClose();
    },
    onError: (e) => setError(e instanceof Error ? e.message : "上传失败"),
  });
  const set = (k: string, v: string | boolean) => setForm((f) => ({ ...f, [k]: v }));
  return (
    <Modal title="上传素材" onClose={onClose} closeOnBackdrop={false}>
      <div className="space-y-3">
        <Field label="文件 *（PNG/JPEG/GIF/WebP/PDF/MP4/MP3/WAV，≤30MB）">
          <input ref={fileRef} type="file" className={inputClass} onChange={(event) => setHasFile(!!event.target.files?.length)} />
        </Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label="类型">
            <select className={inputClass} value={form.kind} onChange={(e) => set("kind", e.target.value)}>
              {KINDS.map(([k, label]) => (
                <option key={k} value={k}>{label}</option>
              ))}
            </select>
          </Field>
          <Field label="来源">
            <select className={inputClass} value={form.source_kind} onChange={(e) => set("source_kind", e.target.value)}>
              <option value="upload">上传</option>
              <option value="web_search">网络搜索</option>
              <option value="screenshot">截图</option>
              <option value="chart">图表</option>
            </select>
          </Field>
        </div>
        <Field label="标题">
          <input className={inputClass} value={form.title} onChange={(e) => set("title", e.target.value)} placeholder="默认用文件名" />
        </Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label="权利状态">
            <select className={inputClass} value={form.rights_status} onChange={(e) => set("rights_status", e.target.value)}>
              <option value="cleared">cleared（已确认可用）</option>
              <option value="unknown">unknown</option>
              <option value="licensed">licensed</option>
            </select>
          </Field>
          <Field label="来源 URL（网络素材必填）">
            <input className={inputClass} value={form.source_url} onChange={(e) => set("source_url", e.target.value)} />
          </Field>
        </div>
        <label className="flex items-center gap-2 text-sm text-slate-600">
          <input type="checkbox" checked={form.public_use_allowed} onChange={(e) => set("public_use_allowed", e.target.checked)} />
          允许公开使用（未勾选不能满足成品媒体就绪）
        </label>
        {error && <div className="rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>}
      </div>
      <div className="mt-4 flex justify-end gap-2">
        <Button variant="secondary" onClick={onClose}>取消</Button>
        <Button disabled={!hasFile || upload.isPending} onClick={() => upload.mutate()}>
          {upload.isPending ? "上传中…" : "上传"}
        </Button>
      </div>
    </Modal>
  );
}
