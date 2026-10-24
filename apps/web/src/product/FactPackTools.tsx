import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api, currentUser } from "../api";
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
  public_use_allowed: boolean;
  model_use_allowed: boolean;
  public_use_revoked_at: string | null;
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

export function PackBuilder({ packId, readOnly = false, onClose, onCloned, onChanged }: { packId: number; readOnly?: boolean; onClose?: () => void; onCloned?: (id: number) => void; onChanged?: () => void }) {
  const queryClient = useQueryClient();
  const [showFreeze, setShowFreeze] = useState(false);
  const [error, setError] = useState("");
  const me = useQuery({ queryKey: ["fact-pack-user", currentUser()], queryFn: () => api.get<{ role: string }>("/users/me"), retry: false });
  const canEdit = !readOnly && me.isSuccess && ["admin", "editor"].includes(me.data.role);

  const packQuery = useQuery({
    queryKey: ["fact-pack", packId],
    queryFn: () => api.get<Pack>(`/fact-packs/${packId}`),
  });
  const pack = packQuery.data;

  const confirmedFacts = useQuery({
    queryKey: ["facts", "confirmed"],
    queryFn: () => api.get<FactRow[]>("/facts?status=confirmed"),
    enabled: canEdit && pack?.status === "draft",
  });

  const invalidate = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["fact-pack", packId] }),
      queryClient.invalidateQueries({ queryKey: ["fact-packs"] }),
      queryClient.invalidateQueries({ queryKey: ["system-library"] }),
    ]);
    onChanged?.();
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
  const permission = useMutation({
    mutationFn: ({ itemId, field, allowed }: { itemId: number; field: "public_use_allowed" | "model_use_allowed"; allowed: boolean }) => api.patch(`/fact-packs/${packId}/items/${itemId}`, { [field]: allowed }),
    onSuccess: invalidate,
    onError: (e) => setError(e instanceof Error ? e.message : "权限保存失败"),
  });
  const freeze = useMutation({
    mutationFn: () => api.post(`/fact-packs/${packId}/freeze`),
    onSuccess: () => {
      setShowFreeze(false);
      return invalidate();
    },
    onError: (e) => {
      setShowFreeze(false);
      setError(e instanceof Error ? e.message : "冻结失败");
    },
  });
  const clone = useMutation({
    mutationFn: () => api.post<{ id: number }>(`/fact-packs/${packId}/clone`),
    onSuccess: async (data) => {
      await invalidate();
      onCloned?.(data.id);
    },
    onError: (e) => setError(e instanceof Error ? e.message : "克隆失败"),
  });

  if (packQuery.isError) return <div role="alert" className="text-sm text-rose-700">{packQuery.error.message}<Button variant="secondary" onClick={() => void packQuery.refetch()}>重新读取</Button></div>;
  if (packQuery.isLoading || !pack) return <Spinner />;
  const writable = canEdit && pack.status !== "archived";
  const busy = addItem.isPending || removeItem.isPending || permission.isPending || freeze.isPending || clone.isPending;

  const inPack = new Set((pack.items || []).map((i) => i.fact_id));
  const conflicts = (pack.items || []).filter((i) => i.status === "conflict");
  const missingDate = (pack.items || []).filter((i) => !i.as_of);
  const available = (confirmedFacts.data || []).filter((f) => !inPack.has(f.id));

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <Button variant="ghost" size="sm" onClick={() => onClose?.()}>
          ← 返回
        </Button>
        <h2 className="text-lg font-semibold">
          {pack.name} <span className="text-sm font-normal text-slate-400">v{pack.version}</span>
        </h2>
        <StatusBadge status={pack.status} />
        {pack.checksum && (
          <span className="font-mono text-[11px] text-slate-400" title={pack.checksum}>
            checksum {pack.checksum.slice(0, 12)}…
          </span>
        )}
        <div className="ml-auto flex gap-2">
          {writable && pack.status === "draft" && (
            <Button variant="secondary" disabled={busy} onClick={() => clone.mutate()}>
              克隆草稿
            </Button>
          )}
          {writable && pack.status === "draft" && <Button disabled={busy} onClick={() => setShowFreeze(true)}>冻结版本</Button>}
          {writable && pack.status === "frozen" && <Button disabled={busy} onClick={() => clone.mutate()}>克隆为 v{pack.version + 1}</Button>}
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
      <p className="text-xs text-amber-800">模型使用与公开使用须分别逐条明确授权；来源信任等级、事实确认和证据包冻结都不代表授权。冻结后只能克隆新版本修改授权。</p>
      {!canEdit && <p className="text-xs text-slate-500">当前只读，或尚未确认编辑权限。</p>}

      <div className="grid gap-4 md:grid-cols-[280px_minmax(0,1fr)]">
        <div className="space-y-3 rounded-lg border border-slate-200 bg-white p-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium">Sources</h3>
          </div>
          <div className="max-h-[60vh] space-y-2 overflow-y-auto">
            {confirmedFacts.isError && <p role="alert" className="text-sm text-rose-700">无法读取可添加事实，请重新打开证据包。</p>}
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
                    <Button size="sm" variant="ghost" disabled={!writable || busy} onClick={() => addItem.mutate(f.id)}>
                      +
                    </Button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
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
                  <th className="px-4 py-2 font-medium">公开使用许可</th>
                  <th className="px-4 py-2 font-medium">模型使用许可</th>
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
                    <td className="px-4 py-2.5">
                      {writable && pack.status === "draft" ? <label className="flex items-center gap-2 text-xs">
                        <input type="checkbox" aria-label={`允许 ${item.ref} 公开使用`} checked={item.public_use_allowed === true} disabled={busy} onChange={(event) => {
                          const allowed = event.target.checked;
                          if (!window.confirm(allowed ? "已核对该证据的公开使用授权，确认允许公开使用？来源信任等级不代表授权。" : "确认将该草稿条目标为不允许公开使用？")) return;
                          setError(""); permission.mutate({ itemId: item.item_id, field: "public_use_allowed", allowed });
                        }} />允许公开使用
                      </label> : <span className="text-xs">{item.public_use_revoked_at ? "已撤销" : item.public_use_allowed === true ? "已明确允许" : "未授权"}</span>}
                    </td>
                    <td className="px-4 py-2.5">
                      {writable && pack.status === "draft" ? <label className="flex items-center gap-2 text-xs">
                        <input type="checkbox" aria-label={`允许 ${item.ref} 模型使用`} checked={item.model_use_allowed === true} disabled={busy} onChange={(event) => {
                          const allowed = event.target.checked;
                          if (!window.confirm(allowed ? "已核对该证据可提供给模型使用，确认允许模型使用？这不会授予公开使用许可。" : "确认将该草稿条目标为不允许模型使用？")) return;
                          setError(""); permission.mutate({ itemId: item.item_id, field: "model_use_allowed", allowed });
                        }} />允许模型使用
                      </label> : <span className="text-xs">{item.model_use_allowed === true ? "已明确允许" : "未授权"}</span>}
                    </td>
                    <td className="px-4 py-2.5 text-right">
                      {writable && pack.status === "draft" && (
                        <Button size="sm" variant="ghost" disabled={busy} onClick={() => removeItem.mutate(item.fact_id)}>
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
            <Button onClick={() => freeze.mutate()} disabled={!writable || busy || conflicts.length > 0 || pack.item_count === 0}>
              确认冻结
            </Button>
          </div>
        </Modal>
      )}

    </div>
  );
}

export function NewPackForm({ onSubmit, onCancel, busy = false }: { onSubmit: (name: string) => void; onCancel: () => void; busy?: boolean }) {
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
        <Button disabled={busy || !name.trim()} onClick={() => onSubmit(name.trim())}>
          创建空包（稍后添加事实）
        </Button>
      </div>
    </div>
  );
}
