import { useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { api, ApiError, currentUser } from "../api";
import { Button, ErrorBanner, Field, inputClass } from "../components/ui";
import { previewByteHash } from "./previewByteHash";
import type { Accepted } from "./ProviderMediaPanel";

type Project = { id: number; title: string; status: string; units: { id: number; title: string; status: string }[] };
type Source = { id: number; revision_no: number; payload_schema: string; channel_id?: string; content_form?: string };
type Output = { id: number; output_index: number; attempt_no: number; state: string; mime_type: string; content_hash: string; size_bytes: number; material_revision_id: number | null };
type Execution = { id: number; package_id: number; revision_no: number; state: string; executor_key: string; outputs: Output[]; accepted_material?: Accepted };
type Configuration = { brief: string; style: string; usage: string; aspect_ratio: string; width: number; height: number; candidate_count: number };
type Package = { id: number; is_current: boolean; reasons: string[]; package_hash: string; package: { source: { kind: string; id: number }; manual_image?: { configuration: Configuration; prompt: string; prompt_hash: string } } };
type Handoff = { package: Package; execution: Execution; prompt: string; prompt_hash: string };
type Candidate = { id: string; name: string; state: "queued" | "uploading" | "validating" | "ready" | "error" | "accepted"; progress: number; url?: string; error?: string; output?: Output; hidden?: boolean };
type Props = { projectId?: number; unitId?: number; readOnly: boolean; onAccepted?: (accepted: Accepted) => void | Promise<void> };
const RATIOS: Record<string, [number, number]> = { "1:1": [1024, 1024], "4:3": [1024, 768], "3:4": [768, 1024], "3:2": [1536, 1024], "2:3": [1024, 1536], "16:9": [1280, 720], "9:16": [720, 1280] };
const MAX_BYTES = 10 * 1024 * 1024;
const TERMINAL = new Set(["accepted", "rejected", "cancelled", "superseded", "failed_before_dispatch", "unknown"]);
const MESSAGES: Record<string, string> = {
  manual_image_dimensions_mismatch: "图片实际尺寸与冻结要求不一致，请按原提示词生成，或新建匹配尺寸的交接包。",
  manual_image_decode_failed: "图片无法真实解码，请上传原始 PNG、JPEG 或 WebP。",
  manual_image_mime_invalid: "只支持 PNG、JPEG、WebP 原图。",
  execution_mime_mismatch: "文件实际格式与声明格式不一致。",
  manual_image_prompt_bounds: "来源内容超过手动提示词上限，请明确选择较小的当前渠道版本。",
  manual_image_dimensions_invalid: "尺寸需为256–4096像素且与所选比例一致。",
  creative_source_not_current: "来源已不是当前版本，旧包只读；请从当前来源新建交接包。",
  creative_package_stale: "来源上下文已变化，不能接受旧包中的图片，请重新准备。",
  creative_execution_revision_conflict: "另一项操作已更新记录，请只读刷新；不会自动重传图片。",
  creative_input_rights_changed: "引用素材的权利已变化，不能继续使用旧包。",
  creative_execution_rights_escalation: "所选使用权超出输入素材的许可，不能接受。",
  manual_image_acceptance_conflict: "已接受的结果与本次决定不同，不能覆盖。",
  creative_exactly_one_source_required: "请明确选择一个已保存的当前Master或渠道版本。",
};
function errorText(cause: unknown) {
  if (cause instanceof ApiError && Array.isArray(cause.detail)) return "输入格式不正确，请检查填写内容。";
  const message = cause instanceof Error ? cause.message : "请求失败，请刷新状态，不要自动重复操作。";
  return MESSAGES[message] ?? message;
}

export default function ManualChatGPTImagePanel(props: Props) {
  return <ScopedManualImages key={`${props.projectId ?? "choose"}:${props.unitId ?? "choose"}:${currentUser()}`} {...props} />;
}

function ScopedManualImages({ projectId, unitId, readOnly, onAccepted }: Props) {
  const queryClient = useQueryClient();
  const actor = useRef(currentUser()).current;
  const mounted = useRef(false);
  const lock = useRef(false);
  const urls = useRef(new Set<string>());
  const xhr = useRef<XMLHttpRequest>();
  const executionRef = useRef<Execution>();
  const preparation = useRef<{ request: string; key: string }>();
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState(projectId ?? 0);
  const [selectedUnit, setSelectedUnit] = useState(unitId ?? 0);
  const [sources, setSources] = useState<{ key: string; label: string }[]>([]);
  const [source, setSource] = useState("");
  const [history, setHistory] = useState<Execution[]>([]);
  const [config, setConfig] = useState<Configuration>({ brief: "", style: "遵循当前角色的视觉风格与已接受的视觉方向", usage: "文章配图 / 信息卡片", aspect_ratio: "1:1", width: 1024, height: 1024, candidate_count: 4 });
  const [handoff, setHandoff] = useState<Handoff>();
  const [rows, setRows] = useState<Candidate[]>([]);
  const [selected, setSelected] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const [title, setTitle] = useState("ChatGPT 手动生成图片");
  const [rights, setRights] = useState({ status: "unknown", public: false, model: false, commercial: false, attribution: "", license: "" });
  const base = `/content-projects/${selectedProject}/units/${selectedUnit}`;
  const project = projects.find(item => item.id === selectedProject);
  const unit = project?.units.find(item => item.id === selectedUnit);
  const locked = readOnly || !project || project.status === "archived" || !unit || unit.status === "archived";
  const current = !!handoff?.package.is_current;
  const terminal = !!handoff && TERMINAL.has(handoff.execution.state);
  function alive() { return mounted.current && currentUser() === actor; }
  function setExecution(value: Execution) {
    executionRef.current = value;
    setHandoff(old => old ? { ...old, execution: value } : old);
    setHistory(old => [value, ...old.filter(item => item.id !== value.id)]);
  }
  function clearRows() {
    urls.current.forEach(URL.revokeObjectURL); urls.current.clear(); setRows([]); setSelected(""); setConfirmed(false);
  }
  useEffect(() => {
    mounted.current = true;
    api.get<Project[]>("/content-projects").then(items => { if (alive()) setProjects(items); }).catch(cause => { if (alive()) setError(errorText(cause)); });
    return () => { mounted.current = false; xhr.current?.abort(); urls.current.forEach(URL.revokeObjectURL); urls.current.clear(); };
  }, []);
  useEffect(() => {
    let active = true;
    setSources([]); setSource(""); setHistory([]); setHandoff(undefined); executionRef.current = undefined; clearRows(); preparation.current = undefined;
    if (selectedProject && selectedUnit) {
      Promise.all([api.get<{ items: Source[] }>(`${base}/master-revisions?limit=1`),
        api.get<{ items: Source[] }>(`${base}/channel-variants?limit=100`),
        api.get<{ items: Execution[] }>(`${base}/creative-executions?limit=100`)]).then(([masters, variants, executions]) => {
        if (!active || !alive()) return;
        const options = [...masters.items.map(item => ({ key: `master:${item.id}`, label: `当前Master v${item.revision_no} · ${item.payload_schema}` })),
          ...variants.items.map(item => ({ key: `variant:${item.id}`, label: `渠道版本 #${item.id} · ${item.channel_id}/${item.content_form} v${item.revision_no}` }))];
        setSources(options); setSource(options[0]?.key ?? "");
        setHistory(executions.items.filter(item => item.executor_key === "chatgpt-manual-image"));
      }).catch(cause => { if (active && alive()) setError(errorText(cause)); });
    }
    return () => { active = false; };
  }, [selectedProject, selectedUnit]);

  async function prepare() {
    if (lock.current || locked || !source || !config.brief.trim()) return;
    lock.current = true; setBusy(true); setError(""); setNotice("");
    const [kind, id] = source.split(":");
    const request = { ...config, [`source_${kind}_revision_id`]: Number(id) };
    const fingerprint = JSON.stringify(request);
    if (preparation.current?.request !== fingerprint) preparation.current = { request: fingerprint, key: crypto.randomUUID() };
    try {
      const result = await api.post<Handoff>(`${base}/manual-chatgpt-images/prepare`, { ...request, idempotency_key: preparation.current.key });
      if (!alive()) return;
      clearRows(); setHandoff(result); executionRef.current = result.execution; setHistory(old => [result.execution, ...old.filter(item => item.id !== result.execution.id)]);
      setNotice("交接包已冻结，未调用任何模型。复制提示词后请自行在ChatGPT生成并下载原图。");
    } catch (cause) { if (alive()) setError(errorText(cause)); }
    finally { lock.current = false; if (alive()) setBusy(false); }
  }
  async function loadCandidate(output: Output, execution: Execution): Promise<Candidate> {
    const response = await fetch(`/api/v1${base}/creative-executions/${execution.id}/outputs/${output.id}/content`, { headers: { "X-Studio-User": actor }, cache: "no-store" });
    if (!response.ok) throw new Error("原图读取失败，请刷新原记录；不会重新上传或接受。");
    const bytes = await response.arrayBuffer();
    if (bytes.byteLength !== output.size_bytes || await previewByteHash(bytes) !== output.content_hash) throw new Error("原图字节/哈希不一致，不能接受。");
    const url = URL.createObjectURL(new Blob([bytes], { type: output.mime_type })); urls.current.add(url);
    return { id: `output:${output.id}`, name: `候选 ${output.output_index}`, state: output.state === "accepted" ? "accepted" : "ready", progress: 100, url, output };
  }
  async function refresh(executionId = handoff?.execution.id) {
    if (!executionId || lock.current) return;
    lock.current = true; setBusy(true); setError("");
    try {
      const execution = await api.get<Execution>(`${base}/creative-executions/${executionId}`);
      const pkg = await api.get<Package>(`${base}/creative-packages/${execution.package_id}`);
      const manual = pkg.package.manual_image;
      if (!manual || execution.executor_key !== "chatgpt-manual-image") throw new Error("不是手动ChatGPT交接记录。");
      const latest = new Map<number, Output>();
      execution.outputs.forEach(output => { if ((latest.get(output.output_index)?.attempt_no ?? 0) < output.attempt_no) latest.set(output.output_index, output); });
      const next: Candidate[] = [];
      for (const output of latest.values()) {
        if (!["staged", "accepted"].includes(output.state)) continue;
        try { next.push(await loadCandidate(output, execution)); }
        catch (cause) { next.push({ id: `output:${output.id}`, name: `候选 ${output.output_index}`, state: "error", progress: 100, output, error: errorText(cause) }); }
      }
      if (!alive()) return;
      const used = new Set(next.map(item => item.url));
      urls.current.forEach(url => { if (!used.has(url)) { URL.revokeObjectURL(url); urls.current.delete(url); } });
      setRows(next); setSelected(""); setConfirmed(false); setConfig(manual.configuration);
      setSource(`${pkg.package.source.kind}:${pkg.package.source.id}`);
      setHandoff({ package: pkg, execution, prompt: manual.prompt, prompt_hash: manual.prompt_hash }); executionRef.current = execution;
      setHistory(old => [execution, ...old.filter(item => item.id !== execution.id)]);
      if (!pkg.is_current) setNotice("旧来源只读：" + pkg.reasons.map(item => MESSAGES[item] ?? item).join("；"));
    } catch (cause) { if (alive()) setError(errorText(cause)); }
    finally { lock.current = false; if (alive()) setBusy(false); }
  }
  async function copy() {
    if (!handoff) return;
    try { await navigator.clipboard.writeText(handoff.prompt); if (alive()) setNotice("完整提示词已复制。请自行粘贴到ChatGPT；本系统没有发送请求。"); }
    catch { if (alive()) setError("剪贴板不可用，请选中下面完整提示词手动复制。"); }
  }
  function upload(file: File, execution: Execution, index: number, rowId: string): Promise<Execution> {
    return new Promise((resolve, reject) => {
      const request = new XMLHttpRequest(); xhr.current = request;
      request.open("POST", `/api/v1${base}/manual-chatgpt-images/${execution.id}/uploads`); request.setRequestHeader("X-Studio-User", actor);
      const patch = (value: Partial<Candidate>) => { if (alive()) setRows(old => old.map(row => row.id === rowId ? { ...row, ...value } : row)); };
      request.upload.onprogress = event => { if (event.lengthComputable) patch({ progress: Math.round(100 * event.loaded / event.total) }); };
      request.upload.onload = () => patch({ state: "validating", progress: 100 });
      request.onerror = () => reject(new Error("网络中断，请只读刷新核对是否已暂存；不会自动重传。"));
      request.onabort = () => reject(new Error("上传已停止，请只读刷新原记录。"));
      request.onload = () => {
        let result: { detail?: { code?: string } } | Execution;
        try { result = JSON.parse(request.responseText); } catch { reject(new Error("上传响应不可解析，请刷新原记录；不会自动重传。")); return; }
        if (request.status < 200 || request.status >= 300) reject(new Error((result as { detail?: { code?: string } }).detail?.code ?? `HTTP ${request.status}`));
        else resolve(result as Execution);
      };
      const form = new FormData(); form.append("file", file); form.append("expected_revision", String(execution.revision_no)); form.append("output_index", String(index)); request.send(form);
    });
  }
  async function addFiles(files: File[]) {
    if (lock.current || locked || !current || terminal || !handoff || !files.length) return;
    lock.current = true; setBusy(true); setError(""); setConfirmed(false);
    const pending = files.slice(0, 4).map(file => ({ file, id: crypto.randomUUID() }));
    setRows(old => [...old, ...pending.map(item => ({ id: item.id, name: item.file.name, state: "queued" as const, progress: 0 }))]);
    if (files.length > 4) setError("单次最多添加4张；超出的文件未上传。");
    try {
      for (const item of pending) {
        if (!alive()) break;
        try {
          if (!/^image\/(png|jpeg|webp)$/.test(item.file.type) || !item.file.size || item.file.size > MAX_BYTES) throw new Error("文件必须是10MiB以内的PNG、JPEG或WebP原图。");
          const execution = executionRef.current;
          if (!execution || TERMINAL.has(execution.state)) throw new Error("执行已结束，不能添加新候选。");
          const used = new Set(execution.outputs.filter(output => output.state !== "rejected").map(output => output.output_index));
          const index = Array.from({ length: handoff.package.package.manual_image!.configuration.candidate_count }, (_, i) => i + 1).find(i => !used.has(i));
          if (!index) throw new Error("冻结候选数量已用完；隐藏候选不会删除历史。请选原候选或创建新交接包。");
          setRows(old => old.map(row => row.id === item.id ? { ...row, state: "uploading" } : row));
          const next = await upload(item.file, execution, index, item.id);
          if (!alive()) break;
          setExecution(next);
          const output = next.outputs.filter(value => value.output_index === index).sort((a, b) => b.attempt_no - a.attempt_no)[0];
          if (!output) throw new Error("响应缺少暂存候选，请只读刷新原记录。");
          const candidate = await loadCandidate(output, next);
          if (alive()) setRows(old => old.map(row => row.id === item.id ? { ...candidate, id: item.id, name: item.file.name } : row));
        } catch (cause) { if (alive()) setRows(old => old.map(row => row.id === item.id ? { ...row, state: "error", error: errorText(cause) } : row)); }
      }
    } finally { lock.current = false; if (alive()) setBusy(false); }
  }
  async function accept() {
    const candidate = rows.find(row => row.id === selected);
    const execution = executionRef.current;
    if (lock.current || locked || !current || terminal || !confirmed || !candidate?.output || candidate.state !== "ready" || !execution) return;
    lock.current = true; setBusy(true); setError("");
    try {
      const result = await api.post<Execution>(`${base}/manual-chatgpt-images/${execution.id}/outputs/${candidate.output.id}/accept`, {
        expected_revision: execution.revision_no, decision: "accept", title: title.trim(), attach_to_project: true,
        rights: { rights_status: rights.status, public_use_allowed: rights.public, model_use_allowed: rights.model, commercial_use_allowed: rights.commercial,
          attribution_text: rights.attribution.trim() || null, license: rights.license.trim() ? { license: rights.license.trim() } : {} },
      });
      if (!alive()) return;
      setExecution(result); setRows(old => old.map(row => row.id === selected ? { ...row, state: "accepted", output: result.outputs.find(output => output.id === candidate.output!.id) } : row)); setConfirmed(false);
      setNotice(`已接受素材版本 #${result.accepted_material?.material_revision_id} 并引用到项目；没有改Master。`);
      await queryClient.invalidateQueries();
      if (result.accepted_material) await onAccepted?.(result.accepted_material);
    } catch (cause) { if (alive()) setError(errorText(cause)); }
    finally { lock.current = false; if (alive()) setBusy(false); }
  }
  const chosen = rows.find(row => row.id === selected);
  return <div className="space-y-4" aria-label="ChatGPT手动生图">
    <p className="text-sm text-slate-600">复制提示词 → 你在ChatGPT生成并下载 → 拖入原图 → 选择 → 接受入库。本系统不操作网页、不读取Cookie、不调用模型。图片来源仅为你的声明。</p>
    {!projectId && <Field label="来源项目"><select className={inputClass} value={selectedProject} disabled={busy || !!handoff} onChange={event => { setSelectedProject(Number(event.target.value)); setSelectedUnit(0); }}><option value={0}>请选择已保存内容的项目</option>{projects.map(item => <option key={item.id} value={item.id}>{item.title}{item.status === "archived" ? "（已归档）" : ""}</option>)}</select></Field>}
    {!unitId && <Field label="来源内容单元"><select className={inputClass} value={selectedUnit} disabled={busy || !!handoff} onChange={event => setSelectedUnit(Number(event.target.value))}><option value={0}>请选择内容单元</option>{project?.units.map(item => <option key={item.id} value={item.id}>{item.title}{item.status === "archived" ? "（已归档）" : ""}</option>)}</select></Field>}
    {!handoff && <>
      <Field label="已保存的来源"><select className={inputClass} value={source} disabled={busy || locked} onChange={event => setSource(event.target.value)}><option value="">请选择当前Master或渠道版本</option>{sources.map(item => <option key={item.key} value={item.key}>{item.label}</option>)}</select></Field>
      {selectedUnit > 0 && !sources.length && <p className="text-sm text-amber-700">先保存当前内容Master，才能建立可追溯的图片交接包。</p>}
      <Field label="图片需求 / 已接受的视觉方向"><textarea className={`${inputClass} h-24`} maxLength={2000} value={config.brief} disabled={busy || locked} onChange={event => setConfig(old => ({ ...old, brief: event.target.value }))} /></Field>
      <Field label="视觉风格"><input className={inputClass} maxLength={1000} value={config.style} disabled={busy || locked} onChange={event => setConfig(old => ({ ...old, style: event.target.value }))} /></Field>
      <Field label="使用场景"><input className={inputClass} maxLength={500} value={config.usage} disabled={busy || locked} onChange={event => setConfig(old => ({ ...old, usage: event.target.value }))} /></Field>
      <div className="grid gap-3 sm:grid-cols-2"><Field label="画面比例"><select className={inputClass} value={config.aspect_ratio} disabled={busy || locked} onChange={event => { const ratio = event.target.value; setConfig(old => ({ ...old, aspect_ratio: ratio, width: RATIOS[ratio][0], height: RATIOS[ratio][1] })); }}>{Object.keys(RATIOS).map(ratio => <option key={ratio}>{ratio}</option>)}</select></Field><Field label="候选数量"><select className={inputClass} value={config.candidate_count} disabled={busy || locked} onChange={event => setConfig(old => ({ ...old, candidate_count: Number(event.target.value) }))}>{[1, 2, 3, 4].map(count => <option key={count} value={count}>{count} 张候选，明确选一张接受</option>)}</select></Field></div>
      <details><summary className="cursor-pointer text-sm">高级设置：精确尺寸</summary><div className="mt-2 grid gap-3 sm:grid-cols-2">{(["width", "height"] as const).map(key => <Field key={key} label={key === "width" ? "宽度（像素）" : "高度（像素）"}><input className={inputClass} type="number" min={256} max={4096} value={config[key]} disabled={busy || locked} onChange={event => setConfig(old => ({ ...old, [key]: Number(event.target.value) }))} /></Field>)}</div></details>
      <Button disabled={busy || locked || !source || !config.brief.trim()} onClick={() => void prepare()}>准备提示词与交接包（不调用模型）</Button>
    </>}
    {history.length > 0 && <details><summary className="cursor-pointer text-sm">查看已有手动交接记录</summary><div className="mt-2 flex flex-wrap gap-2">{history.map(item => <Button key={item.id} size="sm" variant="secondary" disabled={busy} onClick={() => void refresh(item.id)}>#{item.id} · {item.state}</Button>)}</div></details>}
    {handoff && <>
      <p className="text-xs text-slate-500">执行 #{handoff.execution.id} · {handoff.execution.state} · 包 #{handoff.package.id} · {current ? "来源当前" : "来源已过期，仅查看"}</p>
      <Field label="完整图片提示词"><textarea className={`${inputClass} h-64`} readOnly value={handoff.prompt} /></Field>
      <p className="break-all text-xs text-slate-500">Prompt hash：{handoff.prompt_hash} · {config.width}×{config.height} · 最多{config.candidate_count}张 · PNG/JPEG/WebP，每张10MiB以内</p>
      <div className="flex flex-wrap gap-2"><Button variant="secondary" onClick={() => void copy()}>复制完整提示词</Button><Button variant="secondary" disabled={busy} onClick={() => void refresh()}>只读刷新原记录</Button><Button variant="secondary" disabled={busy} onClick={() => { clearRows(); setHandoff(undefined); executionRef.current = undefined; preparation.current = undefined; setNotice("原交接包/暂存历史保留；修改后将创建新包，不会重新生成图片。"); }}>修改需求 / 新建交接包</Button></div>
      {!current && <ErrorBanner message={handoff.package.reasons.map(item => MESSAGES[item] ?? item).join("；") || "来源已过期，不能上传或接受。"} />}
      <div className="rounded-xl border-2 border-dashed border-slate-300 bg-slate-50 p-6 text-center" onDragOver={event => { event.preventDefault(); event.dataTransfer.dropEffect = !busy && !locked && current && !terminal ? "copy" : "none"; }} onDrop={event => { event.preventDefault(); void addFiles(Array.from(event.dataTransfer.files)); }}>
        <p className="text-sm">将ChatGPT下载的图片拖到这里，立即上传到临时候选区</p><p className="mt-1 text-xs text-slate-500">上传不会入素材库，不会修改Master。返回图片必须满足上面的精确尺寸。</p>
        <label className="mt-3 inline-block text-sm">选择本地图片<input aria-label="选择ChatGPT生成图片" className="mt-2 block text-xs" type="file" accept="image/png,image/jpeg,image/webp" multiple disabled={busy || locked || !current || terminal} onChange={event => { void addFiles(Array.from(event.target.files ?? [])); event.target.value = ""; }} /></label>
      </div>
      <div className="grid gap-3 sm:grid-cols-2">{rows.filter(row => !row.hidden).map(row => <div key={row.id} className={`space-y-2 rounded-lg border p-3 ${selected === row.id ? "border-indigo-500" : "border-slate-200"}`}>
        {row.url && <img src={row.url} alt={row.name} className="max-h-64 w-full rounded object-contain" />}
        <p className="break-all text-sm">{row.name} · {({ queued: "等待上传", uploading: "上传中", validating: "校验中", ready: "待选择", error: "失败", accepted: "已接受" })[row.state]}</p>
        {["queued", "uploading", "validating"].includes(row.state) && <progress className="w-full" max={100} value={row.progress} aria-label={`${row.name}上传进度`} />}
        {row.output && <p className="break-all text-xs text-slate-500">{row.output.mime_type} · {row.output.size_bytes} bytes · {config.width}×{config.height}<br />SHA256 {row.output.content_hash}{row.output.material_revision_id ? ` · MaterialRevision #${row.output.material_revision_id}` : " · 尚未入库"}</p>}
        {row.error && <p role="alert" className="text-xs text-rose-700">{row.error}</p>}
        <div className="flex flex-wrap gap-2"><Button size="sm" variant="secondary" disabled={busy || locked || !current || terminal || row.state !== "ready"} ariaPressed={selected === row.id} onClick={() => { setSelected(row.id); setConfirmed(false); }}>{selected === row.id ? "已选中" : "选择这张"}</Button><Button size="sm" variant="ghost" disabled={busy || row.state === "accepted"} onClick={() => { setRows(old => old.map(item => item.id === row.id ? { ...item, hidden: true } : item)); if (selected === row.id) { setSelected(""); setConfirmed(false); } }}>移出当前列表</Button></div>
      </div>)}</div>
      {rows.some(row => row.hidden) && <Button variant="ghost" size="sm" disabled={busy} onClick={() => setRows(old => old.map(row => ({ ...row, hidden: false })))}>恢复隐藏候选（暂存历史未删除）</Button>}
      {chosen?.state === "ready" && !terminal && <div className="space-y-3 rounded-lg border p-4">
        <Field label="素材标题"><input className={inputClass} value={title} maxLength={255} disabled={busy || locked} onChange={event => { setTitle(event.target.value); setConfirmed(false); }} /></Field>
        <Field label="已核对的权利状态"><select className={inputClass} value={rights.status} disabled={busy || locked} onChange={event => { setRights(old => ({ ...old, status: event.target.value, public: false, model: false, commercial: false })); setConfirmed(false); }}><option value="unknown">未知：仅作为受限素材保存</option><option value="restricted">受限</option><option value="cleared">已核对许可</option></select></Field>
        <Field label="许可依据说明"><input className={inputClass} maxLength={1000} value={rights.license} disabled={busy || locked} onChange={event => { setRights(old => ({ ...old, license: event.target.value })); setConfirmed(false); }} /></Field>
        <Field label="署名 / 来源说明"><input className={inputClass} maxLength={2000} value={rights.attribution} disabled={busy || locked} onChange={event => { setRights(old => ({ ...old, attribution: event.target.value })); setConfirmed(false); }} /></Field>
        <div className="flex flex-wrap gap-3 text-sm">{([["public", "允许公开使用"], ["model", "允许模型使用"], ["commercial", "允许商业使用"]] as const).map(([key, label]) => <label key={key}><input type="checkbox" checked={rights[key]} disabled={busy || locked || rights.status !== "cleared"} onChange={event => { setRights(old => ({ ...old, [key]: event.target.checked })); setConfirmed(false); }} />{label}</label>)}</div>
        <label className="block text-sm"><input type="checkbox" checked={confirmed} disabled={busy || locked || !current} onChange={event => setConfirmed(event.target.checked)} />我已看过这张图并核对上述权利；来源为我声明的ChatGPT生成，不是系统验证。</label>
        <Button disabled={busy || locked || !current || !confirmed || !title.trim()} onClick={() => void accept()}>接受入库（不修改Master）</Button>
      </div>}
    </>}
    {notice && <p role="status" className="text-sm text-emerald-700">{notice}</p>}{error && <ErrorBanner message={error} />}
  </div>;
}
