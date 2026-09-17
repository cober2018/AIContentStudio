import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../api";
import {
  Button,
  Drawer,
  EmptyState,
  ErrorBanner,
  Field,
  Modal,
  Spinner,
  StatusBadge,
  inputClass,
} from "../components/ui";

interface SourceItem {
  id: number;
  title: string;
  source_type: string;
  as_of: string | null;
  trust_level: number;
  parse_status: string;
  parse_error: string | null;
  fact_count: number;
  is_archived: boolean;
  created_at: string | null;
}

interface FactItem {
  id: number;
  ref: string;
  statement: string;
  subject: string | null;
  value: number | string | null;
  unit: string | null;
  as_of: string | null;
  status: string;
  confidence: number;
}

interface SourceDetail extends SourceItem {
  raw_text: string | null;
  facts: FactItem[];
}

function ImportModal({ onClose }: { onClose: () => void }) {
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<"text" | "url" | "file">("text");
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [asOf, setAsOf] = useState("");
  const [url, setUrl] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit() {
    setBusy(true);
    setError("");
    try {
      if (tab === "text") {
        await api.post("/sources/text", { title, content, as_of: asOf || null });
      } else if (tab === "url") {
        await api.post("/sources/url", { url, as_of: asOf || null });
      } else if (file) {
        const form = new FormData();
        form.append("file", file);
        if (asOf) form.append("as_of", asOf);
        await api.upload("/sources/upload", form);
      }
      queryClient.invalidateQueries({ queryKey: ["sources"] });
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : "导入失败");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal title="导入来源" onClose={onClose} wide>
      <div className="mb-4 flex gap-1 rounded-md bg-slate-100 p-1">
        {(
          [
            ["text", "粘贴文本"],
            ["url", "导入 URL"],
            ["file", "上传文件"],
          ] as const
        ).map(([key, label]) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={`flex-1 rounded px-3 py-1.5 text-sm ${
              tab === key ? "bg-white font-medium text-slate-900 shadow-sm" : "text-slate-500"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="space-y-3">
        {tab === "text" && (
          <>
            <Field label="标题">
              <input className={inputClass} value={title} onChange={(e) => setTitle(e.target.value)} />
            </Field>
            <Field label="内容">
              <textarea
                className={`${inputClass} h-48 font-mono text-xs`}
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="粘贴结构化数据、研究笔记…"
              />
            </Field>
          </>
        )}
        {tab === "url" && (
          <Field label="URL（仅 http/https，禁止内网地址）">
            <input className={inputClass} value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://…" />
          </Field>
        )}
        {tab === "file" && (
          <Field label="文件（.txt .md .csv .json .pdf）">
            <input
              type="file"
              accept=".txt,.md,.markdown,.csv,.json,.pdf"
              className="text-sm"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
            />
          </Field>
        )}
        <Field label="数据日期 as_of（可选）">
          <input type="date" className={inputClass} value={asOf} onChange={(e) => setAsOf(e.target.value)} />
        </Field>
        {error && <ErrorBanner message={error} />}
      </div>

      <div className="mt-5 flex justify-end gap-2">
        <Button variant="secondary" onClick={onClose}>
          取消
        </Button>
        <Button onClick={submit} disabled={busy}>
          {busy ? "导入中…" : "导入"}
        </Button>
      </div>
    </Modal>
  );
}

function SourceDrawer({ sourceId, onClose }: { sourceId: number; onClose: () => void }) {
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ["source", sourceId],
    queryFn: () => api.get<SourceDetail>(`/sources/${sourceId}`),
  });
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [editing, setEditing] = useState<FactItem | null>(null);
  const [editStatement, setEditStatement] = useState("");

  const extract = useMutation({
    mutationFn: () => api.post(`/sources/${sourceId}/extract-facts`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["source", sourceId] }),
    onError: (e) => alert(e instanceof Error ? e.message : "抽取失败"),
  });

  const bulkStatus = useMutation({
    mutationFn: (action: "confirm" | "reject") =>
      api.post("/facts/bulk-status", { fact_ids: [...selected], action }),
    onSuccess: () => {
      setSelected(new Set());
      queryClient.invalidateQueries({ queryKey: ["source", sourceId] });
      queryClient.invalidateQueries({ queryKey: ["sources"] });
    },
    onError: (e) => alert(e instanceof Error ? e.message : "操作失败"),
  });

  const saveFact = useMutation({
    mutationFn: () => api.patch(`/facts/${editing!.id}`, { statement: editStatement }),
    onSuccess: () => {
      setEditing(null);
      queryClient.invalidateQueries({ queryKey: ["source", sourceId] });
    },
    onError: (e) => alert(e instanceof Error ? e.message : "保存失败"),
  });

  function toggle(id: number) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  return (
    <Drawer title={data ? data.title : "来源详情"} onClose={onClose}>
      {isLoading || !data ? (
        <Spinner />
      ) : (
        <div className="space-y-6">
          <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500">
            <StatusBadge status={data.parse_status} />
            <span>类型：{data.source_type}</span>
            <span>as_of：{data.as_of || "-"}</span>
            <span>可信度：{data.trust_level}</span>
            {data.parse_error && <span className="text-rose-600">解析错误：{data.parse_error}</span>}
          </div>

          <section>
            <h3 className="mb-2 text-sm font-medium">原始内容</h3>
            <pre className="max-h-56 overflow-y-auto whitespace-pre-wrap rounded-md bg-slate-50 p-3 text-xs text-slate-600">
              {data.raw_text || "（空）"}
            </pre>
          </section>

          <section>
            <div className="mb-2 flex items-center justify-between">
              <h3 className="text-sm font-medium">
                候选 Facts（{data.facts.length}）
              </h3>
              <div className="flex gap-2">
                <Button size="sm" variant="secondary" onClick={() => extract.mutate()}>
                  抽取候选
                </Button>
                {selected.size > 0 && (
                  <>
                    <Button size="sm" onClick={() => bulkStatus.mutate("confirm")}>
                      确认选中（{selected.size}）
                    </Button>
                    <Button size="sm" variant="danger" onClick={() => bulkStatus.mutate("reject")}>
                      拒绝选中
                    </Button>
                  </>
                )}
              </div>
            </div>
            {data.facts.length === 0 ? (
              <EmptyState title="尚无候选事实" hint="点击「抽取候选」从解析结果中抽取" />
            ) : (
              <div className="space-y-2">
                {data.facts.map((fact) => (
                  <div key={fact.id} className="rounded-md border border-slate-200 p-3">
                    <div className="flex items-start gap-2">
                      <input
                        type="checkbox"
                        checked={selected.has(fact.id)}
                        onChange={() => toggle(fact.id)}
                        className="mt-1"
                      />
                      <div className="min-w-0 flex-1">
                        {editing?.id === fact.id ? (
                          <div className="space-y-2">
                            <textarea
                              className={`${inputClass} h-20 text-xs`}
                              value={editStatement}
                              onChange={(e) => setEditStatement(e.target.value)}
                            />
                            <div className="flex gap-2">
                              <Button size="sm" onClick={() => saveFact.mutate()}>
                                保存
                              </Button>
                              <Button size="sm" variant="ghost" onClick={() => setEditing(null)}>
                                取消
                              </Button>
                            </div>
                          </div>
                        ) : (
                          <>
                            <div className="text-sm text-slate-800">{fact.statement}</div>
                            <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-slate-400">
                              <span className="font-mono">{fact.ref}</span>
                              <StatusBadge status={fact.status} />
                              {fact.value !== null && (
                                <span>
                                  {fact.value}
                                  {fact.unit || ""}
                                </span>
                              )}
                              <span>as_of {fact.as_of || "-"}</span>
                              <span>可信 {fact.confidence}</span>
                            </div>
                          </>
                        )}
                      </div>
                      {editing?.id !== fact.id && (
                        <div className="flex shrink-0 gap-1">
                          {fact.status === "candidate" && (
                            <Button
                              size="sm"
                              onClick={() =>
                                bulkOne("confirm", fact.id).then(() =>
                                  queryClient.invalidateQueries({ queryKey: ["source", sourceId] }),
                                )
                              }
                            >
                              确认
                            </Button>
                          )}
                          <Button
                            size="sm"
                            variant="secondary"
                            onClick={() => {
                              setEditing(fact);
                              setEditStatement(fact.statement);
                            }}
                          >
                            编辑
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() =>
                              bulkOne("reject", fact.id).then(() =>
                                queryClient.invalidateQueries({ queryKey: ["source", sourceId] }),
                              )
                            }
                          >
                            拒绝
                          </Button>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        </div>
      )}
    </Drawer>
  );
}

async function bulkOne(action: "confirm" | "reject", factId: number) {
  await api.post(`/facts/${factId}/${action}`);
}

export default function Sources() {
  const [showImport, setShowImport] = useState(false);
  const [drawerId, setDrawerId] = useState<number | null>(null);
  const { data, isLoading } = useQuery({
    queryKey: ["sources"],
    queryFn: () => api.get<SourceItem[]>("/sources"),
  });

  return (
    <div className="mx-auto max-w-6xl space-y-4 p-8">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">来源库</h1>
        <Button onClick={() => setShowImport(true)}>导入来源</Button>
      </div>

      {isLoading ? (
        <Spinner />
      ) : !data || data.length === 0 ? (
        <EmptyState
          title="暂无来源"
          hint="导入文本 / URL / 文件后，可抽取候选事实"
          action={<Button onClick={() => setShowImport(true)}>导入来源</Button>}
        />
      ) : (
        <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100 bg-slate-50 text-left text-xs text-slate-400">
                <th className="px-4 py-2.5 font-medium">标题</th>
                <th className="px-4 py-2.5 font-medium">类型</th>
                <th className="px-4 py-2.5 font-medium">日期</th>
                <th className="px-4 py-2.5 font-medium">可信等级</th>
                <th className="px-4 py-2.5 font-medium">解析状态</th>
                <th className="px-4 py-2.5 font-medium">Fact 数</th>
              </tr>
            </thead>
            <tbody>
              {data.map((s) => (
                <tr
                  key={s.id}
                  className="cursor-pointer border-b border-slate-50 last:border-0 hover:bg-slate-50"
                  onClick={() => setDrawerId(s.id)}
                >
                  <td className="max-w-xs truncate px-4 py-2.5 font-medium text-slate-800">{s.title}</td>
                  <td className="px-4 py-2.5 text-slate-500">{s.source_type}</td>
                  <td className="px-4 py-2.5 text-slate-500">{s.as_of || "-"}</td>
                  <td className="px-4 py-2.5 text-slate-500">{s.trust_level}</td>
                  <td className="px-4 py-2.5">
                    <StatusBadge status={s.parse_status} />
                  </td>
                  <td className="px-4 py-2.5 text-slate-500">{s.fact_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showImport && <ImportModal onClose={() => setShowImport(false)} />}
      {drawerId && <SourceDrawer sourceId={drawerId} onClose={() => setDrawerId(null)} />}
    </div>
  );
}
