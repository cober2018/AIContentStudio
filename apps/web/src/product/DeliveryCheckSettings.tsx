import { FormEvent, useEffect, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api, currentUser } from "../api";
import { Button, ErrorBanner, Field, Spinner, inputClass } from "../components/ui";

type Name = "overexposed_mean_luma" | "overexposed_clipped_percent" | "brightness_jump_luma" | "dialogue_spread_lu" | "cover_mismatch_mean" | "source_brightness_diff";
type Thresholds = Record<Name, number>;
type View = { thresholds: Thresholds; defaults: Thresholds; limits: Record<Name, [number, number]> };

const fields: [Name, string, string, string][] = [
  ["overexposed_mean_luma", "过曝：平均亮度提示线", "镜头中间一帧的平均亮度（0–255）超过它就提示偏亮。", ""],
  ["overexposed_clipped_percent", "过曝：贴顶高光占比提示线", "亮度接近顶点（≥ 250）的像素占比超过它就提示高光贴顶。", "%"],
  ["brightness_jump_luma", "亮度跳变提示线", "相邻两个镜头平均亮度相差超过它就提示。", ""],
  ["dialogue_spread_lu", "对白音量不齐提示线", "有台词的镜头，响度和各段中间值相差超过它就提示。", " LU"],
  ["cover_mismatch_mean", "封面与成片平均色差（0–255）", "封面和成片开头 0.5 秒里最像的那一帧比，红绿蓝平均每个通道相差超过它就提示颜色不一致。", ""],
  ["source_brightness_diff", "成片与原片亮度差（0–255）", "画面来自视频素材的镜头（HLG 原片除外），成片和原片同一时刻各取一帧比平均亮度，相差超过它就提示成片比原片暗或亮。", ""],
];

const messageOf = (error: unknown, fallback: string) => error instanceof Error ? error.message : fallback;

export default function DeliveryCheckSettings() {
  const queryClient = useQueryClient();
  const key = ["delivery-checks", currentUser()];
  const view = useQuery({ queryKey: key, queryFn: () => api.get<View>("/settings/delivery-checks"), retry: false });
  const me = useQuery({ queryKey: ["product-settings-user", currentUser()], queryFn: () => api.get<{ role: string }>("/users/me"), retry: false });
  const [values, setValues] = useState<Record<Name, string>>({ overexposed_mean_luma: "", overexposed_clipped_percent: "", brightness_jump_luma: "", dialogue_spread_lu: "", cover_mismatch_mean: "", source_brightness_diff: "" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const data = view.data;
  useEffect(() => {
    if (data) setValues(Object.fromEntries(fields.map(([name]) => [name, String(data.thresholds[name])])) as Record<Name, string>);
  }, [data]);

  async function save(event: FormEvent) {
    event.preventDefault();
    if (busy || !data) return;
    const payload = Object.fromEntries(fields.map(([name]) => [name, Number(values[name])])) as Thresholds;
    const bad = fields.find(([name]) => !Number.isFinite(payload[name]) || payload[name] < data.limits[name][0] || payload[name] > data.limits[name][1]);
    if (bad) { setError(`「${bad[1]}」要在 ${data.limits[bad[0]][0]} 到 ${data.limits[bad[0]][1]} 之间。`); return; }
    setBusy(true); setError(""); setNotice("");
    try { queryClient.setQueryData(key, await api.put<View>("/settings/delivery-checks", payload)); setNotice("已保存，下次交付的小样、成片按新提示线检查。"); }
    catch (cause) { setError(messageOf(cause, "保存失败")); }
    finally { setBusy(false); }
  }

  if (view.isLoading) return <Spinner label="读取交付检查…" />;
  if (view.isError || !data) return <ErrorBanner message={messageOf(view.error, "无法读取交付检查设置")} />;
  const editable = me.data?.role === "admin";
  return <section className="space-y-5 rounded-xl border border-slate-200 bg-white p-6" aria-label="交付检查">
    <div className="space-y-1">
      <h2 className="font-semibold">交付检查</h2>
      <p className="text-sm text-slate-600">小样、成片交付时，平台按导演稿逐镜头抽一帧看亮度、逐段测对白音量，成片还会查颜色标记是不是 sRGB、封面和成片开头颜色是否一致；实拍镜头还会和原片同一时刻比亮度；超过下面的提示线就在审阅页提醒，写明是哪个镜头、差多少。只提醒，不拦交付。</p>
    </div>
    {error && <div role="alert"><ErrorBanner message={error} /></div>}
    {notice && <p role="status" className="text-sm text-emerald-700">{notice}</p>}
    <form onSubmit={save} className="space-y-3">
      {fields.map(([name, label, hint, unit]) => <Field key={name} label={label} hint={`${hint}默认 ${data.defaults[name]}${unit}。`}>
        <input type="number" step="any" min={data.limits[name][0]} max={data.limits[name][1]} className={inputClass} value={values[name]} disabled={!editable || busy} onChange={event => setValues({ ...values, [name]: event.target.value })} />
      </Field>)}
      {!editable && <p className="text-sm text-slate-500">只有管理员可以修改提示线。</p>}
      {editable && <Button type="submit" disabled={busy}>{busy ? "保存中…" : "保存提示线"}</Button>}
    </form>
  </section>;
}
