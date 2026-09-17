import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../api";
import { Button, EmptyState, Field, Modal, Spinner, StatusBadge, inputClass } from "../components/ui";

interface PackItem {
  item_id: number;
  fact_id: number;
  ref: string;
  statement: string;
  subject: string | null;
  value: number | string | null;
  unit: string | null;
  as_of: string | null;
  status: string;
  source_document_id: number;
}

interface Pack {
  id: number;
  name: string;
  description: string | null;
  version: number;
  status: string;
  parent_id: number | null;
  checksum: string | null;
  frozen_at: string | null;
  item_count: number;
  items?: PackItem[];
}

interface FactRow {
  id: number;
  ref: string;
  statement: string;
  status: string;
  as_of: string | null;
  source_title: string;
  value: number | string | null;
  unit: string | null;
}

function PackBuilder({ packId }: { packId: number }) {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [showCreate, setShowCreate] = useState(false);
  const [showFreeze, setShowFreeze] = useState(false);
  const [error, setError] = useState("");

  const packQuery = useQuery({
    queryKey: ["fact-pack", packId],
    queryFn: () => api.get<Pack>(`/fact-packs/${packId}`),
  });
  const pack = packQuery.data;

  const confirmedFacts = useQuery({
    queryKey: ["facts", "confirmed"],
    queryFn: () => api.get<FactRow[]>("/facts?status=confirmed"),
    enabled: pack?.status === "draft",
  });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["fact-pack", packId] });
    queryClient.invalidateQueries({ queryKey: ["fact-packs"] });
  };

  const addItem = useMutation({
    mutationFn: (factId: number) => api.post(`/fact-packs/${packId}/items`, { fact_id: factId }),
    onSuccess: invalidate,
    onError: (e) => setError(e instanceof Error ? e.message : "添加失败"),
  });
  const removeItem = useMutation({
    mutationFn: (factId: number) => api.del(`/fact-packs/${packId}/items/${factId}`),
    onSuccess: invalidate,
    onError: (e) => setError(e instanceof Error ? e.message : "移除失败"),
  });
  const freeze = useMutation({
    mutationFn: () => api.post(`/fact-packs/${packId}/freeze`),
    onSuccess: () => {
      setShowFreeze(false);
      invalidate();
    },
    onError: (e) => {
      setShowFreeze(false);
      setError(e instanceof Error ? e.message : "冻结失败");
    },
  });
  const clone = useMutation({
    mutationFn: () => api.post<{ id: number }>(`/fact-packs/${packId}/clone`),
    onSuccess: (data) => {
      invalidate();
      navigate(`/fact-packs/${data.id}`);
    },
    onError: (e) => setError(e instanceof Error ? e.message : "克隆失败"),
  });

  if (packQuery.isLoading || !pack) return <Spinner />;

  const inPack = new Set((pack.items || []).map((i) => i.fact_id));
  const conflicts = (pack.items || []).filter((i) => i.status === "conflict");
  const missingDate = (pack.items || []).filter((i) => !i.as_of);
  const available = (confirmedFacts.data || []).filter((f) => !inPack.has(f.id));

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <Button variant="ghost" size="sm" onClick={() => navigate("/fact-packs")}>
          ← 返回列表
        </Button>
        <h1 className="text-xl font-semibold">
          {pack.name} <span className="text-sm font-normal text-slate-400">v{pack.version}</span>
        </h1>
        <StatusBadge status={pack.status} />
        {pack.checksum && (
          <span className="font-mono text-[11px] text-slate-400" title={pack.checksum}>
            checksum {pack.checksum.slice(0, 12)}…
          </span>
        )}
        <div className="ml-auto flex gap-2">
          {pack.status === "draft" && (
            <Button variant="secondary" onClick={() => clone.mutate()}>
              Clone
            </Button>
          )}
          {pack.status === "draft" && <Button onClick={() => setShowFreeze(true)}>冻结版本</Button>}
          {pack.status === "frozen" && <Button onClick={() => clone.mutate()}>Clone 为 v{pack.version + 1}</Button>}
        </div>
      </div>

      {pack.status === "frozen" && (
        <div className="rounded-md bg-sky-50 px-4 py-3 text-sm text-sky-800">
          此版本已冻结（{pack.frozen_at ? new Date(pack.frozen_at).toLocaleString("zh-CN") : ""}），不可修改。
          引用它的内容永远记录此版本；如需修改请 Clone。
        </div>
      )}
      {pack.status === "archived" && (
        <div className="rounded-md bg-slate-100 px-4 py-3 text-sm text-slate-600">此版本已归档。</div>
      )}
      {error && <div className="rounded-md bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>}

      <div className="grid grid-cols-[280px_1fr] gap-4">
        <div className="space-y-3 rounded-lg border border-slate-200 bg-white p-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium">Sources</h3>
            {pack.status === "draft" && (
              <Button size="sm" variant="secondary" onClick={() => setShowCreate(true)}>
                + 添加事实
              </Button>
            )}
          </div>
          <div className="max-h-[60vh] space-y-2 overflow-y-auto">
            {available.length === 0 ? (
              <p className="text-xs text-slate-400">没有可添加的 confirmed 事实</p>
            ) : (
              available.map((f) => (
                <div key={f.id} className="rounded border border-slate-100 p-2">
                  <div className="text-xs text-slate-700">{f.statement}</div>
                  <div className="mt-1 flex items-center justify-between">
                    <span className="text-[11px] text-slate-400">
                      {f.ref} · {f.source_title.slice(0, 14)}
                    </span>
                    <Button size="sm" variant="ghost" onClick={() => addItem.mutate(f.id)}>
                      +
                    </Button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="rounded-lg border border-slate-200 bg-white">
          <div className="border-b border-slate-100 px-4 py-3 text-sm font-medium">
            Facts（{pack.item_count}）
          </div>
          {(pack.items || []).length === 0 ? (
            <EmptyState title="FactPack 为空" hint="从左侧添加 confirmed 事实后再冻结" />
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100 text-left text-xs text-slate-400">
                  <th className="px-4 py-2 font-medium">编号</th>
                  <th className="px-4 py-2 font-medium">陈述</th>
                  <th className="px-4 py-2 font-medium">数值</th>
                  <th className="px-4 py-2 font-medium">as_of</th>
                  <th className="px-4 py-2 font-medium">状态</th>
                  <th className="px-4 py-2" />
                </tr>
              </thead>
              <tbody>
                {(pack.items || []).map((item) => (
                  <tr key={item.item_id} className="border-b border-slate-50 last:border-0">
                    <td className="px-4 py-2.5 font-mono text-xs text-slate-500">{item.ref}</td>
                    <td className="px-4 py-2.5">{item.statement}</td>
                    <td className="px-4 py-2.5 text-slate-500">
                      {item.value}
                      {item.unit || ""}
                    </td>
                    <td className="px-4 py-2.5 text-slate-500">{item.as_of || "⚠️ 缺失"}</td>
                    <td className="px-4 py-2.5">
                      <StatusBadge status={item.status} />
                    </td>
                    <td className="px-4 py-2.5 text-right">
                      {pack.status === "draft" && (
                        <Button size="sm" variant="ghost" onClick={() => removeItem.mutate(item.fact_id)}>
                          移除
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      <div className="rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600">
        冲突检测：<b className={conflicts.length ? "text-rose-600" : ""}>{conflicts.length} 个</b> ｜ 缺失日期：
        <b className={missingDate.length ? "text-amber-600" : ""}>{missingDate.length} 个</b>
        {pack.status === "draft" && " ｜ 冻结要求：≥1 条全部 confirmed 且无冲突"}
      </div>

      {showFreeze && (
        <Modal title="冻结 FactPack" onClose={() => setShowFreeze(false)}>
          <p className="text-sm text-slate-600">
            冻结后此版本不可修改，生成内容将永远记录 v{pack.version}。
            {conflicts.length > 0 && <span className="text-rose-600">当前存在 {conflicts.length} 个冲突，无法冻结。</span>}
          </p>
          <div className="mt-5 flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setShowFreeze(false)}>
              取消
            </Button>
            <Button onClick={() => freeze.mutate()} disabled={conflicts.length > 0 || pack.item_count === 0}>
              确认冻结
            </Button>
          </div>
        </Modal>
      )}

      {showCreate && <AddFactsModal onClose={() => setShowCreate(false)} />}
    </div>
  );
}

function AddFactsModal({ onClose }: { onClose: () => void }) {
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const { data } = useQuery({
    queryKey: ["facts", "confirmed"],
    queryFn: () => api.get<FactRow[]>("/facts?status=confirmed"),
  });

  const create = useMutation({
    mutationFn: () => api.post("/fact-packs", { name, fact_ids: [...selected] }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["fact-packs"] });
      queryClient.invalidateQueries({ queryKey: ["facts"] });
      onClose();
    },
  });

  return (
    <Modal title="从 confirmed 事实创建 FactPack" onClose={onClose} wide>
      <div className="space-y-3">
        <Field label="FactPack 名称">
          <input className={inputClass} value={name} onChange={(e) => setName(e.target.value)} placeholder="如 2026-09-16 市场复盘" />
        </Field>
        <div className="max-h-80 space-y-1.5 overflow-y-auto">
          {(data || []).map((f) => (
            <label key={f.id} className="flex items-start gap-2 rounded border border-slate-100 p-2 hover:bg-slate-50">
              <input
                type="checkbox"
                className="mt-1"
                checked={selected.has(f.id)}
                onChange={() =>
                  setSelected((prev) => {
                    const next = new Set(prev);
                    if (next.has(f.id)) next.delete(f.id);
                    else next.add(f.id);
                    return next;
                  })
                }
              />
              <div>
                <div className="text-sm">{f.statement}</div>
                <div className="text-xs text-slate-400">
                  {f.ref} · {f.source_title} · as_of {f.as_of || "-"}
                </div>
              </div>
            </label>
          ))}
        </div>
        <div className="flex justify-end gap-2">
          <Button variant="secondary" onClick={onClose}>
            取消
          </Button>
          <Button disabled={!name || selected.size === 0} onClick={() => create.mutate()}>
            创建（{selected.size} 条事实）
          </Button>
        </div>
      </div>
    </Modal>
  );
}

export default function FactPacks() {
  const { id } = useParams();
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const navigate = useNavigate();

  const { data, isLoading } = useQuery({
    queryKey: ["fact-packs"],
    queryFn: () => api.get<Pack[]>("/fact-packs"),
  });

  const create = useMutation({
    mutationFn: (name: string) => api.post<{ id: number }>("/fact-packs", { name, fact_ids: [] }),
    onSuccess: (pack) => {
      queryClient.invalidateQueries({ queryKey: ["fact-packs"] });
      setShowCreate(false);
      navigate(`/fact-packs/${pack.id}`);
    },
  });

  if (id) {
    return (
      <div className="mx-auto max-w-6xl p-8">
        <PackBuilder key={id} packId={Number(id)} />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl space-y-4 p-8">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">FactPack</h1>
        <Button onClick={() => setShowCreate(true)}>新建 FactPack</Button>
      </div>

      {isLoading ? (
        <Spinner />
      ) : !data || data.length === 0 ? (
        <EmptyState
          title="暂无 FactPack"
          hint="FactPack 是内容生成唯一允许引用的事实集合，必须冻结后才能绑定选题"
          action={<Button onClick={() => setShowCreate(true)}>新建 FactPack</Button>}
        />
      ) : (
        <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100 bg-slate-50 text-left text-xs text-slate-400">
                <th className="px-4 py-2.5 font-medium">名称</th>
                <th className="px-4 py-2.5 font-medium">版本</th>
                <th className="px-4 py-2.5 font-medium">状态</th>
                <th className="px-4 py-2.5 font-medium">Fact 数</th>
                <th className="px-4 py-2.5 font-medium">来源版本</th>
                <th className="px-4 py-2.5 font-medium">创建时间</th>
              </tr>
            </thead>
            <tbody>
              {data.map((p) => (
                <tr
                  key={p.id}
                  className="cursor-pointer border-b border-slate-50 last:border-0 hover:bg-slate-50"
                  onClick={() => navigate(`/fact-packs/${p.id}`)}
                >
                  <td className="px-4 py-2.5 font-medium text-slate-800">{p.name}</td>
                  <td className="px-4 py-2.5 text-slate-500">v{p.version}</td>
                  <td className="px-4 py-2.5">
                    <StatusBadge status={p.status} />
                  </td>
                  <td className="px-4 py-2.5 text-slate-500">{p.item_count}</td>
                  <td className="px-4 py-2.5 text-slate-500">{p.parent_id ? `v${p.version - 1} Clone` : "-"}</td>
                  <td className="px-4 py-2.5 text-slate-500">
                    {p.frozen_at ? new Date(p.frozen_at).toLocaleDateString("zh-CN") : "-"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showCreate && (
        <Modal title="新建 FactPack" onClose={() => setShowCreate(false)}>
          <NewPackForm onSubmit={(name) => create.mutate(name)} onCancel={() => setShowCreate(false)} />
        </Modal>
      )}
    </div>
  );
}

function NewPackForm({ onSubmit, onCancel }: { onSubmit: (name: string) => void; onCancel: () => void }) {
  const [name, setName] = useState("");
  return (
    <div className="space-y-3">
      <Field label="名称">
        <input className={inputClass} value={name} onChange={(e) => setName(e.target.value)} autoFocus />
      </Field>
      <div className="flex justify-end gap-2">
        <Button variant="secondary" onClick={onCancel}>
          取消
        </Button>
        <Button disabled={!name} onClick={() => onSubmit(name)}>
          创建空包（稍后添加事实）
        </Button>
      </div>
    </div>
  );
}
