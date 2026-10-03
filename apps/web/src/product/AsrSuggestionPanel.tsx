import { useEffect, useRef, useState } from "react";
import { api } from "../api";
import { Button, ErrorBanner, inputClass } from "../components/ui";
import { acceptAsrCues, type VideoCue, type VideoDraft } from "./VideoStudioModel";

type Provider = { key: string; version: string; label: string; execution_mode: "local" | "cloud"; available: boolean; reason: string; verified: false };
type Suggestion = { receipt_id: string; transcript: string; cues: VideoCue[]; provider_key: string; provider_version: string; input_hash: string; output_hash: string; source: { revision_id: number; content_hash: string } };
type Props = { projectId: number; unitId: number; masterId: number | null; masterHash: string | null; savedSourceIds: number[]; draft: VideoDraft; readOnly: boolean; dirty: boolean; onChange: (draft: VideoDraft) => void };

const unavailableReasons: Record<string, string> = {
  local_asr_not_enabled: "本机转写尚未启用",
  local_asr_configuration_missing: "未配置本机识别环境",
  local_asr_runtime_missing: "本机 Python、MLX 或字幕运行文件缺失",
  local_asr_cached_model_missing: "本机模型缓存缺失，不会自动下载",
  local_asr_offline_runtime_unavailable: "本机离线运行环境不可用",
  local_asr_audio_tools_missing: "音轨提取工具未安装",
};

export default function AsrSuggestionPanel(props: Props) {
  const { projectId, unitId, masterId, masterHash, savedSourceIds, draft, readOnly, dirty, onChange } = props;
  const [providers, setProviders] = useState<Provider[]>([]);
  const [provider, setProvider] = useState("");
  const [source, setSource] = useState("");
  const [result, setResult] = useState<Suggestion>();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const epoch = useRef(0);
  const identity = `${projectId}/${unitId}/${masterId}/${masterHash}/${dirty}`;
  const currentIdentity = useRef(identity);
  currentIdentity.current = identity;
  useEffect(() => {
    let active = true;
    setProvider(""); setProviders([]);
    api.get<Provider[]>("/asr-provider-options").then((rows) => {
      if (active) {
        setProviders(rows);
        const local = rows.find((row) => row.execution_mode === "local" && row.available);
        setProvider(local ? `${local.key}@${local.version}` : "");
      }
    }).catch(() => { if (active) setError("ASR 引擎清单读取失败"); });
    return () => { active = false; epoch.current++; };
  }, [projectId, unitId]);
  useEffect(() => { epoch.current++; setResult(undefined); setBusy(false); setError(""); setNotice(""); }, [projectId, unitId, masterId, masterHash]);
  const selected = providers.find((row) => `${row.key}@${row.version}` === provider);
  const localUnavailable = providers.find((row) => row.execution_mode === "local" && !row.available);
  const unavailable = readOnly || dirty || !masterId || !masterHash || !selected?.available || !savedSourceIds.includes(Number(source));
  async function suggest() {
    if (unavailable || !selected) return;
    const requestEpoch = ++epoch.current;
    const requestIdentity = identity;
    setBusy(true); setError(""); setNotice(""); setResult(undefined);
    try {
      const next = await api.post<Suggestion>(`/content-projects/${projectId}/units/${unitId}/master-revisions/${masterId}/asr-suggestions`, {
        provider_key: selected.key, provider_version: selected.version, source_revision_id: Number(source), base_payload_hash: masterHash,
      });
      if (requestEpoch === epoch.current && requestIdentity === currentIdentity.current) setResult(next);
    } catch { if (requestEpoch === epoch.current && requestIdentity === currentIdentity.current) setError("ASR 不可用、来源已变化、超限或结果未知；没有保存 Master，也不会自动重试。"); }
    finally { if (requestEpoch === epoch.current) setBusy(false); }
  }
  function accept() {
    if (!result || unavailable || busy) return;
    try { onChange(acceptAsrCues(draft, result.receipt_id, result.cues)); setResult(undefined); setNotice("已接受到本地字幕草稿，成片绑定已失效。尚未保存；请明确保存内容 Master，服务端将重新验证来源权利和 receipt。"); }
    catch { setError("字幕不适合当前时间线，请核对后重新请求。"); }
  }
  return <section aria-label="ASR 转录建议" className="space-y-3 rounded-xl border p-4">
    <h3 className="font-semibold">ASR 转录与字幕建议</h3>
    <p className="text-xs text-slate-600">仅从已保存 Master 的精确音频/视频版本转录；最多 10 分钟、30 MiB。本机识别不上传云端，最多等待 2 分钟；失败不自动切换云端。接受只替换本地字幕，显式保存才写不可变修订。</p>
    {localUnavailable && <p className="text-sm text-amber-800">{unavailableReasons[localUnavailable.reason] || "本机识别不可用"}。请先完成本机配置，或明确选择云端引擎。</p>}
    {providers.length > 0 && !providers.some((row) => row.execution_mode === "local") && <p className="text-sm text-amber-800">本机识别尚未启用，不会默认选择或自动调用云端引擎。</p>}
    {selected?.execution_mode === "cloud" && <p role="status" className="text-sm text-amber-800">已选择云端转录：请求会发送所选音频，并可能消耗额度。只有明确请求才执行。</p>}
    {providers.length === 0 && <p className="text-sm text-amber-800">未配置 ASR Provider，不可执行；不会生成模拟转录。请配置受支持的精确 key/version adapter。</p>}
    <div className="flex flex-wrap gap-2"><select aria-label="ASR Provider 版本" className={inputClass} value={provider} disabled={busy || readOnly} onChange={(event) => { setProvider(event.target.value); setResult(undefined); }}><option value="">请选择识别引擎</option>{providers.map((row) => <option disabled={!row.available} key={`${row.key}@${row.version}`} value={`${row.key}@${row.version}`}>{row.label || row.key} · {row.available ? (row.execution_mode === "local" ? "离线 · 请求时核验" : "云端 · 请求时核验") : "不可用"}</option>)}</select>
      <select aria-label="ASR 精确来源版本" className={inputClass} value={source} disabled={busy || readOnly} onChange={(event) => { setSource(event.target.value); setResult(undefined); }}><option value="">选择已保存的音频/视频版本</option>{savedSourceIds.map((id) => <option key={id} value={id}>MaterialRevision #{id}</option>)}</select>
      <Button disabled={busy || unavailable} onClick={() => void suggest()}>{busy ? "转录中…" : "明确请求 ASR 建议"}</Button></div>
    {dirty && <p className="text-xs text-amber-800">请先保存当前本地修改，再请求或接受 ASR。</p>}
    {result && <div className="space-y-2"><p className="whitespace-pre-wrap text-sm">{result.transcript}</p><p className="text-xs">{result.cues.length} 条字幕 · 来源 #{result.source.revision_id}</p><ol className="text-xs">{result.cues.map((cue) => <li key={cue.id}>{cue.start_ms}–{cue.end_ms} ms · {cue.text}</li>)}</ol><Button disabled={unavailable || busy} onClick={accept}>明确接受并替换本地字幕</Button><Button variant="secondary" onClick={() => setResult(undefined)}>拒绝转录建议</Button></div>}
    {notice && <p role="status" className="text-sm text-emerald-700">{notice}</p>}{error && <ErrorBanner message={error} />}
  </section>;
}
