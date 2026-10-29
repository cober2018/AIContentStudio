import { useQuery } from "@tanstack/react-query";
import { FormEvent, useState } from "react";
import { api, ApiError, currentUser } from "../api";
import { Button, ErrorBanner, Field, inputClass } from "../components/ui";

type Brand = { id: number; name: string; status?: string };

function errorText(cause: unknown) {
  const detail = cause instanceof ApiError ? cause.detail as { message?: string } | string | undefined : undefined;
  return typeof detail === "object" && detail?.message ? detail.message : typeof detail === "string" ? detail : cause instanceof Error ? cause.message : "创建失败";
}

const lines = (text: string) => text.split("\n").map(line => line.trim()).filter(Boolean);

// One form creates the persona under its brand, its first profile and its voice, which is fixed from then on.
export default function NewPersonaForm({ brands, disabled, onCreated }: { brands: Brand[]; disabled: boolean; onCreated: (id: number) => void }) {
  const voices = useQuery({ queryKey: ["voice-settings", currentUser()], retry: false, queryFn: () => api.get<{ items: Record<string, { name: string }> }>("/settings/voice") });
  const active = brands.filter(brand => brand.status !== "archived");
  const [form, setForm] = useState({ name: "", brand: active[0] ? String(active[0].id) : "new", brandName: "", voice: "", positioning: "", audience: "", domains: "", boundaries: "" });
  const [busy, setBusy] = useState(false);
  const [issue, setIssue] = useState("");
  const set = (patch: Partial<typeof form>) => setForm(current => ({ ...current, ...patch }));
  const ready = form.name.trim() && form.voice && (form.brand !== "new" || form.brandName.trim());
  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!ready || busy) return;
    setBusy(true); setIssue("");
    try {
      const brandId = form.brand === "new" ? (await api.post<{ id: number }>("/content-brands", { name: form.brandName.trim() })).id : Number(form.brand);
      const persona = await api.post<{ id: number }>(`/content-brands/${brandId}/personas`, { name: form.name.trim() });
      const profile: Record<string, unknown> = {};
      if (form.positioning.trim()) profile.positioning = form.positioning.trim();
      if (lines(form.audience).length) profile.target_audience = lines(form.audience);
      if (lines(form.domains).length) profile.content_domains = lines(form.domains);
      if (lines(form.boundaries).length) profile.content_boundaries = lines(form.boundaries);
      if (Object.keys(profile).length) await api.post(`/content-personas/${persona.id}/revisions`, { expected_revision: 0, profile });
      await api.put(`/personas/${persona.id}/voice-preset`, { preset_id: form.voice });
      onCreated(persona.id);
    } catch (cause) { setIssue(errorText(cause)); } finally { setBusy(false); }
  }
  const off = disabled || busy;
  return <form className="max-w-2xl space-y-4" onSubmit={event => void submit(event)}>
    <div className="grid gap-4 sm:grid-cols-2">
      <Field label="角色名称 *"><input className={inputClass} maxLength={200} value={form.name} disabled={off} onChange={event => set({ name: event.target.value })} required /></Field>
      <Field label="所属品牌 *"><select className={inputClass} value={form.brand} disabled={off} onChange={event => set({ brand: event.target.value })}>
        {active.map(brand => <option key={brand.id} value={brand.id}>{brand.name}</option>)}<option value="new">＋ 新建品牌</option></select></Field>
      {form.brand === "new" && <Field label="新品牌名称 *"><input className={inputClass} maxLength={200} value={form.brandName} disabled={off} onChange={event => set({ brandName: event.target.value })} /></Field>}
      <Field label="声音 *" hint="建好后不能改；同一套声音可以给多个角色用。在 设置 → 配音 里管理。"><select className={inputClass} value={form.voice} disabled={off} onChange={event => set({ voice: event.target.value })}>
        <option value="">请选择</option>{Object.entries(voices.data?.items || {}).map(([key, item]) => <option key={key} value={key}>{item.name}</option>)}</select></Field>
    </div>
    <Field label="定位（选填）" hint="一句话：这个角色是谁、讲什么"><input className={inputClass} value={form.positioning} disabled={off} onChange={event => set({ positioning: event.target.value })} /></Field>
    <div className="grid gap-4 sm:grid-cols-3">
      <Field label="目标受众（选填）" hint="一行一类人"><textarea className={inputClass} rows={3} value={form.audience} disabled={off} onChange={event => set({ audience: event.target.value })} /></Field>
      <Field label="内容领域（选填）" hint="一行一个"><textarea className={inputClass} rows={3} value={form.domains} disabled={off} onChange={event => set({ domains: event.target.value })} /></Field>
      <Field label="内容边界（选填）" hint="不碰的话题，一行一条"><textarea className={inputClass} rows={3} value={form.boundaries} disabled={off} onChange={event => set({ boundaries: event.target.value })} /></Field>
    </div>
    {issue && <ErrorBanner message={issue} />}
    <Button type="submit" disabled={off || !ready}>{busy ? "创建中…" : "创建角色"}</Button>
    <p className="text-[12px] text-ink-500">其他资料（表达风格、视觉语言、风险边界等）建好后在「编辑资料」里补，不填也能用。</p>
  </form>;
}
