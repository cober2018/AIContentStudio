import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../api";
import { Button, EmptyState, Field, Modal, Spinner, StatusBadge, inputClass } from "../components/ui";

interface Endpoint {
  id: number;
  name: string;
  path: string;
  params: Record<string, string>;
  title_template: string;
  as_of_path: string | null;
  trust_level: number;
  fact_mapping: { items_path?: string; statement: string; fields: Record<string, string>; as_of_field?: string };
  last_pull_at: string | null;
  last_pull_status: string | null;
  last_pull_error: string | null;
}

interface Connector {
  id: number;
  name: string;
  connector_type: string;
  base_url: string;
  api_key_env: string | null;
  auth_style: string;
  auth_header_name: string | null;
  is_active: boolean;
  endpoint_count: number;
  endpoints?: Endpoint[];
}

const EXAMPLE_MAPPING = `{
  "items_path": "data.rows",
  "statement": "{index_name} 当日涨跌幅 {pct_change}%",
  "fields": { "value": "{pct_change}", "subject": "{index_name}", "unit": "%", "predicate": "涨跌幅" }
}`;

function CreateConnectorModal({ onClose }: { onClose: () => void }) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState({ name: "", base_url: "", auth_style: "bearer", api_key_env: "", auth_header_name: "" });
  const [error, setError] = useState("");

  const create = useMutation({
    mutationFn: () =>
      api.post("/connectors", {
        name: form.name,
        base_url: form.base_url,
        auth_style: form.auth_style,
        api_key_env: form.api_key_env || null,
        auth_header_name: form.auth_header_name || null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["connectors"] });
      onClose();
    },
    onError: (e) => setError(e instanceof Error ? e.message : "创建失败"),
  });

  return (
    <Modal title="新建 Connector" onClose={onClose}>
      <div className="space-y-3">
        <Field label="名称">
          <input className={inputClass} value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="量化平台" />
        </Field>
        <Field label="Base URL">
          <input className={inputClass} value={form.base_url} onChange={(e) => setForm({ ...form, base_url: e.target.value })} placeholder="https://api.quant.example.com" />
        </Field>
        <Field label="鉴权方式">
          <select className={inputClass} value={form.auth_style} onChange={(e) => setForm({ ...form, auth_style: e.target.value })}>
            <option value="bearer">Bearer Token</option>
            <option value="header">自定义 Header</option>
            <option value="none">无鉴权</option>
          </select>
        </Field>
        {form.auth_style !== "none" && (
          <Field label="API Key 环境变量名" hint="只存变量名，密钥值放服务端环境变量，不落库">
            <input className={inputClass} value={form.api_key_env} onChange={(e) => setForm({ ...form, api_key_env: e.target.value })} placeholder="QUANT_API_KEY" />
          </Field>
        )}
        {form.auth_style === "header" && (
          <Field label="Header 名称">
            <input className={inputClass} value={form.auth_header_name} onChange={(e) => setForm({ ...form, auth_header_name: e.target.value })} placeholder="X-API-Key" />
          </Field>
        )}
        {error && <p className="text-sm text-rose-600">{error}</p>}
        <div className="flex justify-end gap-2">
          <Button variant="secondary" onClick={onClose}>取消</Button>
          <Button disabled={!form.name || !form.base_url} onClick={() => create.mutate()}>创建</Button>
        </div>
      </div>
    </Modal>
  );
}

function AddEndpointModal({ connectorId, onClose }: { connectorId: number; onClose: () => void }) {
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [path, setPath] = useState("");
  const [titleTemplate, setTitleTemplate] = useState("{today} 数据拉取");
  const [asOfPath, setAsOfPath] = useState("");
  const [mapping, setMapping] = useState(EXAMPLE_MAPPING);
  const [error, setError] = useState("");

  const create = useMutation({
    mutationFn: () => {
      const fact_mapping = JSON.parse(mapping);
      return api.post(`/connectors/${connectorId}/endpoints`, {
        name,
        path,
        title_template: titleTemplate,
        as_of_path: asOfPath || null,
        fact_mapping,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["connector", connectorId] });
      onClose();
    },
    onError: (e) => {
      const msg = e instanceof Error ? e.message : "创建失败";
      setError(msg.includes("{") ? `JSON 格式有误：${msg}` : msg);
    },
  });

  return (
    <Modal title="添加拉取端点" onClose={onClose} wide>
      <div className="space-y-3">
        <div className="grid grid-cols-2 gap-3">
          <Field label="端点名称">
            <input className={inputClass} value={name} onChange={(e) => setName(e.target.value)} placeholder="每日市场复盘" />
          </Field>
          <Field label="路径（拼在 Base URL 后）">
            <input className={inputClass} value={path} onChange={(e) => setPath(e.target.value)} placeholder="/api/v1/market/daily" />
          </Field>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <Field label="标题模板" hint="{today} 会替换为当天日期">
            <input className={inputClass} value={titleTemplate} onChange={(e) => setTitleTemplate(e.target.value)} />
          </Field>
          <Field label="as_of 字段路径" hint="从响应 JSON 取数据日期，如 data.trade_date">
            <input className={inputClass} value={asOfPath} onChange={(e) => setAsOfPath(e.target.value)} />
          </Field>
        </div>
        <Field label="JSON → Fact 映射" hint="items_path 定位数组；statement 模板用 {字段} 引用；fields.value 必填">
          <textarea className={`${inputClass} h-40 font-mono text-xs`} value={mapping} onChange={(e) => setMapping(e.target.value)} />
        </Field>
        {error && <p className="text-sm text-rose-600">{error}</p>}
        <div className="flex justify-end gap-2">
          <Button variant="secondary" onClick={onClose}>取消</Button>
          <Button disabled={!name || !path} onClick={() => create.mutate()}>添加</Button>
        </div>
      </div>
    </Modal>
  );
}

function ConnectorCard({ connector }: { connector: Connector }) {
  const queryClient = useQueryClient();
  const [showAdd, setShowAdd] = useState(false);
  const [message, setMessage] = useState("");

  const detail = useQuery({
    queryKey: ["connector", connector.id],
    queryFn: () => api.get<Connector>(`/connectors/${connector.id}`),
  });
  const endpoints = detail.data?.endpoints || [];

  const pull = useMutation({
    mutationFn: (endpointId: number) =>
      api.post<{ source_id: number; facts: number }>(`/endpoints/${endpointId}/pull`, {}),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ["connector", connector.id] });
      setMessage(`拉取成功：${result.facts} 条候选事实已进入来源库（来源 #${result.source_id}），去确认后可入 FactPack`);
    },
    onError: (e) => setMessage(e instanceof Error ? e.message : "拉取失败"),
  });

  return (
    <div className="rounded-lg border border-slate-200 bg-white">
      <div className="flex flex-wrap items-center gap-3 border-b border-slate-100 px-5 py-3">
        <StatusBadge status={connector.is_active ? "active" : "archived"} />
        <span className="font-medium">{connector.name}</span>
        <span className="text-xs text-slate-400">{connector.base_url}</span>
        <span className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-[11px] text-slate-500">
          {connector.auth_style === "none" ? "无鉴权" : `$${connector.api_key_env}`}
        </span>
        <div className="ml-auto">
          <Button size="sm" variant="secondary" onClick={() => setShowAdd(true)}>+ 添加端点</Button>
        </div>
      </div>

      {message && (
        <div className="border-b border-slate-100 bg-slate-50 px-5 py-2 text-xs text-slate-600">{message}</div>
      )}

      <div className="divide-y divide-slate-50">
        {endpoints.length === 0 ? (
          <div className="px-5 py-6 text-center text-xs text-slate-400">尚无拉取端点</div>
        ) : (
          endpoints.map((ep) => (
            <div key={ep.id} className="flex flex-wrap items-center gap-3 px-5 py-3">
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2 text-sm">
                  <span className="font-medium">{ep.name}</span>
                  <code className="text-[11px] text-slate-400">{ep.path}</code>
                </div>
                <div className="mt-0.5 text-[11px] text-slate-400">
                  {ep.last_pull_status === "ok" && `上次拉取成功 ${ep.last_pull_at ? new Date(ep.last_pull_at).toLocaleString("zh-CN") : ""}`}
                  {ep.last_pull_status === "failed" && <span className="text-rose-600">上次失败：{ep.last_pull_error?.slice(0, 80)}</span>}
                  {!ep.last_pull_status && "尚未拉取"}
                </div>
              </div>
              <Button size="sm" onClick={() => pull.mutate(ep.id)} disabled={pull.isPending}>
                {pull.isPending ? "拉取中…" : "立即拉取"}
              </Button>
            </div>
          ))
        )}
      </div>

      {showAdd && <AddEndpointModal connectorId={connector.id} onClose={() => setShowAdd(false)} />}
    </div>
  );
}

export default function Connectors() {
  const [showCreate, setShowCreate] = useState(false);
  const { data, isLoading } = useQuery({
    queryKey: ["connectors"],
    queryFn: () => api.get<Connector[]>("/connectors"),
  });

  return (
    <div className="mx-auto max-w-6xl space-y-4 p-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">数据接入 Connector</h1>
          <p className="mt-0.5 text-sm text-slate-400">
            从量化平台等外部 API 定时拉取结构化数据，自动映射为候选事实——拉取后到「来源库」确认，再进 FactPack
          </p>
        </div>
        <Button onClick={() => setShowCreate(true)}>新建 Connector</Button>
      </div>

      {isLoading ? (
        <Spinner />
      ) : !data || data.length === 0 ? (
        <EmptyState
          title="暂无 Connector"
          hint="配置外部 API 地址与鉴权（密钥只放环境变量），把量化平台的每日数据接进来"
          action={<Button onClick={() => setShowCreate(true)}>新建 Connector</Button>}
        />
      ) : (
        <div className="space-y-4">
          {data.map((c) => (
            <ConnectorCard key={c.id} connector={c} />
          ))}
        </div>
      )}

      {showCreate && <CreateConnectorModal onClose={() => setShowCreate(false)} />}
    </div>
  );
}
