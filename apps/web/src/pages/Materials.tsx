import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRef, useState } from "react";
import { api } from "../api";
import { Button, EmptyState, Field, Modal, Spinner, StatusBadge, inputClass } from "../components/ui";
import ProviderMediaPanel from "../product/ProviderMediaPanel";

// 素材库（V1 PRD 2.0 / material-library-v1）：
// Material = 全局逻辑素材；MaterialRevision = 不可变字节版本；稿件通过 DraftMedia(use) 引用。

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
  usage?: { material_id: number; revisions: number; draft_media_uses: { draft_media_id: number; draft_id: number; role: string; sort_order: number }[] };
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

function srcOf(m: MaterialRow, revisionId?: number) {
  const rid = revisionId ?? m.latest_revision?.id;
  return `/api/v1/materials/${m.id}/revisions/${rid}/raw`;
}

function UploadModal({ onClose }: { onClose: () => void }) {
  const queryClient = useQueryClient();
  const fileRef = useRef<HTMLInputElement>(null);
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
      Object.entries(form).forEach(([k, v]) => body.append(k, String(v)));
      return api.upload<MaterialRow>("/materials/upload", body);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["materials"] });
      onClose();
    },
    onError: (e) => setError(e instanceof Error ? e.message : "上传失败"),
  });
  const set = (k: string, v: string | boolean) => setForm((f) => ({ ...f, [k]: v }));
  return (
    <Modal title="上传素材" onClose={onClose}>
      <div className="space-y-3">
        <Field label="文件 *（PNG/JPEG/GIF/WebP/PDF/MP4/MP3，≤30MB）">
          <input ref={fileRef} type="file" className={inputClass} />
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
        <Button disabled={!fileRef.current?.files?.length && !upload.isPending} onClick={() => upload.mutate()}>
          {upload.isPending ? "上传中…" : "上传"}
        </Button>
      </div>
    </Modal>
  );
}

function DetailModal({ material, onClose }: { material: MaterialRow; onClose: () => void }) {
  const queryClient = useQueryClient();
  const [attachDraftId, setAttachDraftId] = useState("");
  const [attachRole, setAttachRole] = useState("inline");
  const [attachMsg, setAttachMsg] = useState("");
  const { data } = useQuery({
    queryKey: ["material", material.id],
    queryFn: () => api.get<MaterialRow>(`/materials/${material.id}`),
  });
  const row = data || material;
  const revoke = useMutation({
    mutationFn: (rid: number) =>
      api.post(`/materials/${material.id}/revisions/${rid}/revoke-public-use`, { note: window.prompt("撤权原因（必填）") || "权限撤销" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["material", material.id] }),
  });
  const attach = useMutation({
    mutationFn: () =>
      api.post(`/drafts/${attachDraftId}/materials`, { material_revision_id: row.latest_revision?.id, role: attachRole }),
    onSuccess: () => {
      setAttachMsg("已挂到稿件");
      queryClient.invalidateQueries({ queryKey: ["material", material.id] });
    },
    onError: (e) => setAttachMsg(e instanceof Error ? e.message : "挂载失败"),
  });

  return (
    <Modal title={row.title} onClose={onClose} wide>
      <div className="flex gap-4">
        {(row.latest_revision?.mime_type || "").startsWith("image/") && (
          <img src={srcOf(row)} alt={row.title} className="h-32 w-44 rounded-md border border-slate-200 bg-slate-50 object-cover" />
        )}
        <div className="min-w-0 flex-1 space-y-1 text-xs text-slate-600">
          <div>
            类型 {row.kind} · <StatusBadge status={row.status} />
            {row.latest_revision && <> · 来源 {row.latest_revision.source_kind}</>}
          </div>
          {row.latest_revision && (
            <div className="truncate font-mono text-[10px] text-slate-400">hash {row.latest_revision.content_hash.slice(0, 24)}…</div>
          )}
          <div>
            公开使用：{row.latest_revision?.public_use_allowed ? "✅ 已授权" : "⛔ 未授权"}
            {" · "}权利：{row.latest_revision?.rights_status || "-"}
          </div>
          {row.usage && (
            <div>
              被引用：{row.usage.draft_media_uses.length} 处（{Array.from(new Set(row.usage.draft_media_uses.map((u: { draft_id: number }) => u.draft_id))).join(", ") || "无"}）
            </div>
          )}
        </div>
      </div>

      <h4 className="mb-1 mt-3 text-xs font-medium text-slate-500">版本（替换=新版本，旧版本不可变）</h4>
      <div className="max-h-40 space-y-1 overflow-y-auto">
        {(row.revisions || []).map((r: MaterialRevision) => (
          <div key={r.id} className="flex items-center justify-between rounded border border-slate-200 px-2 py-1 text-[11px]">
            <span>v{r.revision_no} · {r.source_kind} · {r.public_use_allowed ? "公开✅" : "未公开⛔"}</span>
            <span className="flex items-center gap-2">
              <StatusBadge status={r.status === "revoked" ? "changes_requested" : r.status} />
              {r.public_use_allowed && (
                <Button size="sm" variant="ghost" onClick={() => revoke.mutate(r.id)}>撤权</Button>
              )}
            </span>
          </div>
        ))}
      </div>

      <h4 className="mb-1 mt-3 text-xs font-medium text-slate-500">挂到稿件</h4>
      <div className="flex items-end gap-2">
        <Field label="Draft ID">
          <input className={`${inputClass} w-28`} value={attachDraftId} onChange={(e) => setAttachDraftId(e.target.value)} placeholder="如 12" />
        </Field>
        <Field label="角色">
          <select className={inputClass} value={attachRole} onChange={(e) => setAttachRole(e.target.value)}>
            <option value="inline">inline</option>
            <option value="cover">cover</option>
            <option value="attachment">attachment</option>
          </select>
        </Field>
        <Button className="mb-0.5" disabled={!attachDraftId || attach.isPending} onClick={() => attach.mutate()}>挂载</Button>
      </div>
      {attachMsg && <p className="mt-1 text-xs text-slate-500">{attachMsg}</p>}

      <div className="mt-4 flex justify-end">
        <Button variant="secondary" onClick={onClose}>关闭</Button>
      </div>
    </Modal>
  );
}

function GenerateModal({ onClose }: { onClose: () => void }) {
  return (
    <Modal title="AI 生成素材" onClose={onClose}>
      <ProviderMediaPanel />
    </Modal>
  );
}

function SearchModal({ onClose }: { onClose: () => void }) {
  const [query, setQuery] = useState("");
  const [error, setError] = useState("");
  const search = useMutation({
    mutationFn: () => api.post<unknown[]>("/materials/search", { query }),
    onError: (e) => setError(e instanceof Error ? e.message : "搜索失败"),
  });
  return (
    <Modal title="素材搜索" onClose={onClose}>
      <div className="flex items-end gap-2">
        <Field label="关键词">
          <input className={inputClass} value={query} onChange={(e) => setQuery(e.target.value)} />
        </Field>
        <Button className="mb-0.5" disabled={!query || search.isPending} onClick={() => search.mutate()}>搜索</Button>
      </div>
      {error && <div className="mt-3 rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-700">{error}</div>}
      <div className="mt-4 flex justify-end">
        <Button variant="secondary" onClick={onClose}>关闭</Button>
      </div>
    </Modal>
  );
}

export default function Materials() {
  const [kind, setKind] = useState("");
  const [q, setQ] = useState("");
  const [showUpload, setShowUpload] = useState(false);
  const [showGenerate, setShowGenerate] = useState(false);
  const [showSearch, setShowSearch] = useState(false);
  const [detail, setDetail] = useState<MaterialRow | null>(null);
  const { data, isLoading } = useQuery({
    queryKey: ["materials", kind, q],
    queryFn: () => api.get<MaterialRow[]>(`/materials?${new URLSearchParams({ ...(kind ? { kind } : {}), ...(q ? { q } : {}) })}`),
  });

  return (
    <div className="mx-auto max-w-6xl space-y-4 p-8">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">素材库</h1>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={() => setShowSearch(true)}>搜索素材</Button>
          <Button variant="secondary" onClick={() => setShowGenerate(true)}>AI 生成</Button>
          <Button onClick={() => setShowUpload(true)}>上传素材</Button>
        </div>
      </div>
      <div className="flex items-center gap-2 text-sm">
        <select className={`${inputClass} w-36`} value={kind} onChange={(e) => setKind(e.target.value)}>
          <option value="">全部类型</option>
          {KINDS.map(([k, label]) => (
            <option key={k} value={k}>{label}</option>
          ))}
        </select>
        <input className={`${inputClass} w-64`} placeholder="按标题筛选…" value={q} onChange={(e) => setQ(e.target.value)} />
      </div>

      {isLoading ? (
        <Spinner />
      ) : !data?.length ? (
        <EmptyState title="素材库为空" hint="上传、AI 生成或搜索加入素材；稿件通过「use」引用素材，可多稿复用" />
      ) : (
        <div className="grid grid-cols-4 gap-4">
          {data.map((m) => (
            <button
              key={m.id}
              className="rounded-lg border border-slate-200 bg-white p-3 text-left hover:border-gray-400"
              onClick={() => setDetail(m)}
            >
              {(m.latest_revision?.mime_type || "").startsWith("image/") ? (
                <img src={srcOf(m)} alt={m.title} className="mb-2 h-28 w-full rounded bg-slate-50 object-cover" />
              ) : (
                <div className="mb-2 flex h-28 w-full items-center justify-center rounded bg-slate-50 text-2xl text-slate-300">▦</div>
              )}
              <div className="truncate text-sm font-medium text-slate-800">{m.title}</div>
              <div className="mt-0.5 text-[11px] text-slate-400">
                {m.kind} · v{m.latest_revision?.revision_no ?? "-"} · {m.latest_revision?.public_use_allowed ? "公开✅" : "未公开⛔"}
              </div>
            </button>
          ))}
        </div>
      )}

      {showUpload && <UploadModal onClose={() => setShowUpload(false)} />}
      {showGenerate && <GenerateModal onClose={() => setShowGenerate(false)} />}
      {showSearch && <SearchModal onClose={() => setShowSearch(false)} />}
      {detail && <DetailModal material={detail} onClose={() => setDetail(null)} />}
    </div>
  );
}
