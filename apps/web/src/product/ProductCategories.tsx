import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api, ApiError, currentUser } from "../api";
import { Button, ErrorBanner, Field, inputClass, Spinner } from "../components/ui";

type Directive = { focus?: string; selling_points?: string; audience?: string; tone?: string; banned_words?: string[] };
type Profile = { directive: Directive; styles: string[]; default_style: string; hooks: string[]; look: string; camera_plan: Record<string, string> };
type Category = { id: number; key: string; name: string; status: string; revision: number; builtin: boolean; profile: Profile | null };
type Motion = { camera: { id: string; name: string; group: string }[]; looks: { id: string; name: string; group: string }[] };
type View = { items: Category[]; styles: { id: string; name: string; form: string }[]; motion: Motion };

const SHOTS = [["hook", "开头"], ["pain_point", "痛点"], ["product_reveal", "商品亮相"], ["demo", "演示"], ["social_proof", "信任"], ["cta", "下单引导"]] as const;
const DIRECTIVE = [["focus", "画面重点"], ["selling_points", "卖点怎么写"], ["audience", "常见人群"], ["tone", "说话语气"]] as const;

function errorText(error: unknown) {
  const detail = error instanceof ApiError ? error.detail as { message?: string } | string | undefined : undefined;
  return typeof detail === "object" && detail?.message ? detail.message : error instanceof Error ? error.message : "操作失败";
}

const blank = (view: View): Profile => ({ directive: { focus: "", selling_points: "", audience: "", tone: "", banned_words: [] }, styles: ["scene"], default_style: "scene",
  hooks: [], look: view.motion.looks[0]?.id || "", camera_plan: {} });

// Each category works like a persona: its own directive, script styles, hooks, look and camera plan.
export default function ProductCategories() {
  const client = useQueryClient();
  const query = useQuery({ queryKey: ["product-categories", currentUser()], queryFn: () => api.get<View>("/product-categories"), retry: false });
  const mode = useQuery({ queryKey: ["product-i2v-mode", currentUser()], queryFn: () => api.get<{ mode: "manual" | "auto" }>("/product-i2v-mode"), retry: false });
  const [editing, setEditing] = useState<{ id: number | null; key: string; name: string; profile: Profile; revision: number } | null>(null);
  const [busy, setBusy] = useState(false);
  const [issue, setIssue] = useState("");
  if (query.isPending) return <Spinner label="读取商品品类…" />;
  if (query.error || !query.data) return <ErrorBanner message={errorText(query.error)} />;
  const view = query.data;
  const refresh = () => client.invalidateQueries({ queryKey: ["product-categories"] });
  async function run(action: () => Promise<unknown>) {
    setBusy(true); setIssue("");
    try { await action(); await refresh(); } catch (error) { setIssue(errorText(error)); } finally { setBusy(false); }
  }
  async function save() {
    if (!editing) return;
    await run(async () => {
      if (editing.id === null) await api.post("/product-categories", { key: editing.key, name: editing.name, profile: editing.profile });
      else await api.put(`/product-categories/${editing.id}`, { expected_revision: editing.revision, name: editing.name, profile: editing.profile });
      setEditing(null);
    });
  }
  const patch = (value: Partial<Profile>) => setEditing(current => current && { ...current, profile: { ...current.profile, ...value } });
  const groups = (items: { id: string; name: string; group: string }[]) => [...new Set(items.map(item => item.group))].map(group =>
    <optgroup key={group} label={group}>{items.filter(item => item.group === group).map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</optgroup>);
  return <section className="space-y-4">
    <div className="flex flex-wrap items-start justify-between gap-3">
      <div><h2 className="text-lg font-semibold">商品品类</h2><p className="text-sm text-slate-500">品类像角色一样带自己的写法：可用的脚本风格、推荐开头、默认光线色调和每类镜头的运镜。作品发起时冻结当时的版本。</p></div>
      <Button onClick={() => setEditing({ id: null, key: "", name: "", profile: blank(view), revision: 0 })}>新增品类</Button>
    </div>
    <div className="rounded-xl border border-slate-200 bg-white p-4"><Field label="图生视频默认方式"><select aria-label="图生视频默认方式" className={inputClass} value={mode.data?.mode || "manual"} disabled={busy || !mode.data}
      onChange={event => void run(async () => { await api.put("/product-i2v-mode", { mode: event.target.value }); await client.invalidateQueries({ queryKey: ["product-i2v-mode"] }); })}>
      <option value="manual">手动：平台准备提示词和首帧，我去 Grok / Gemini 网页生成</option><option value="auto">自动：MiniMax 直接生成（按条计费）</option></select></Field>
      <p className="mt-1 text-xs text-slate-500">每个作品、每个镜头还可以单独改；自动失败或不满意的镜头可一键转手动。</p></div>
    {issue && <ErrorBanner message={issue} />}
    <div className="grid gap-3 sm:grid-cols-2">{view.items.map(item => <article key={item.id} className={`rounded-xl border bg-white p-4 ${item.status === "active" ? "border-slate-200" : "border-dashed border-slate-300 opacity-70"}`}>
      <div className="flex items-start justify-between gap-2"><div><h3 className="font-semibold">{item.name}</h3><p className="text-xs text-slate-500">{item.builtin ? "内置" : "自建"} · v{item.revision}{item.status !== "active" && " · 已停用"}</p></div>
        <div className="flex gap-2"><Button size="sm" variant="secondary" disabled={busy || !item.profile} onClick={() => setEditing({ id: item.id, key: item.key, name: item.name, profile: item.profile!, revision: item.revision })}>编辑</Button>
          <Button size="sm" variant="ghost" disabled={busy} onClick={() => void run(() => api.put(`/product-categories/${item.id}`, { expected_revision: item.revision, status: item.status === "active" ? "disabled" : "active" }))}>{item.status === "active" ? "停用" : "启用"}</Button></div></div>
      {item.profile && <p className="mt-2 text-sm text-slate-600">风格：{item.profile.styles.map(id => view.styles.find(style => style.id === id)?.name || id).join("、")}（默认 {view.styles.find(style => style.id === item.profile!.default_style)?.name}）</p>}
      {item.profile && <p className="mt-1 text-xs text-slate-500">光线：{view.motion.looks.find(look => look.id === item.profile!.look)?.name} · 开头：{item.profile.hooks.join("、") || "按素材选"}</p>}
    </article>)}</div>
    {editing && <div className="space-y-4 rounded-xl border border-indigo-200 bg-white p-4">
      <h3 className="font-semibold">{editing.id === null ? "新增品类" : `编辑「${editing.name}」`}</h3>
      <div className="grid gap-3 sm:grid-cols-2">
        <Field label="名称"><input className={inputClass} maxLength={100} value={editing.name} onChange={event => setEditing({ ...editing, name: event.target.value })} /></Field>
        {editing.id === null && <Field label="标识（小写字母、数字、横线，如 furniture）"><input className={inputClass} maxLength={60} value={editing.key} onChange={event => setEditing({ ...editing, key: event.target.value })} /></Field>}
        {DIRECTIVE.map(([key, label]) => <Field key={key} label={label}><textarea className={inputClass} rows={2} maxLength={2000} value={editing.profile.directive[key] || ""} onChange={event => patch({ directive: { ...editing.profile.directive, [key]: event.target.value } })} /></Field>)}
        <Field label="不能用的词（用顿号或逗号分开）"><input className={inputClass} value={(editing.profile.directive.banned_words || []).join("、")} onChange={event => patch({ directive: { ...editing.profile.directive, banned_words: event.target.value.split(/[、,，]/).map(word => word.trim()).filter(Boolean) } })} /></Field>
        <Field label="推荐开头（用顿号分开）"><input className={inputClass} value={editing.profile.hooks.join("、")} onChange={event => patch({ hooks: event.target.value.split(/[、,，]/).map(word => word.trim()).filter(Boolean) })} /></Field>
      </div>
      <fieldset className="space-y-2"><legend className="text-sm font-medium">可用脚本风格</legend><div className="flex flex-wrap gap-3">{view.styles.map(style => <label key={style.id} className="flex items-center gap-1 text-sm">
        <input type="checkbox" checked={editing.profile.styles.includes(style.id)} onChange={event => { const styles = event.target.checked ? [...editing.profile.styles, style.id] : editing.profile.styles.filter(id => id !== style.id); patch({ styles, default_style: styles.includes(editing.profile.default_style) ? editing.profile.default_style : styles[0] || "" }); }} />{style.form} · {style.name}</label>)}</div>
        <Field label="默认风格"><select className={inputClass} value={editing.profile.default_style} onChange={event => patch({ default_style: event.target.value })}>{editing.profile.styles.map(id => <option key={id} value={id}>{view.styles.find(style => style.id === id)?.name}</option>)}</select></Field></fieldset>
      <div className="grid gap-3 sm:grid-cols-3">
        <Field label="默认光线色调"><select className={inputClass} value={editing.profile.look} onChange={event => patch({ look: event.target.value })}>{groups(view.motion.looks.map(look => ({ ...look, group: look.group === "real" ? "机位质感" : "光线色调" })))}</select></Field>
        {SHOTS.map(([shot, label]) => <Field key={shot} label={`${label}镜头运镜`}><select className={inputClass} value={editing.profile.camera_plan[shot] || ""} onChange={event => { const plan = { ...editing.profile.camera_plan }; if (event.target.value) plan[shot] = event.target.value; else delete plan[shot]; patch({ camera_plan: plan }); }}><option value="">由模型定</option>{groups(view.motion.camera)}</select></Field>)}
      </div>
      <div className="flex gap-2"><Button disabled={busy || !editing.name.trim() || !editing.profile.styles.length} onClick={() => void save()}>保存为新版本</Button><Button variant="secondary" disabled={busy} onClick={() => setEditing(null)}>取消</Button></div>
    </div>}
  </section>;
}
