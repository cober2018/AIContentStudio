import { ReactNode, useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api, ApiError, currentUser } from "../api";
import { Button, ErrorBanner, inputClass } from "../components/ui";
import { errorText, FileButton, type Portrait, StoredThumb, uploadPortrait } from "./PersonaPortraits";

type Profile = Record<string, unknown>;
type Revision = { revision_no: number; profile: Profile } | undefined;
type Shape = "text" | "lines";

const MAX_LOGOS = 3;
const GROUPS: { title: string; note: string; fields: { key: string; label: string; shape: Shape; hint?: string }[] }[] = [
  { title: "品牌是什么", note: "交给模型的品牌背景", fields: [
    { key: "introduction", label: "一句话介绍", shape: "text" },
    { key: "proposition", label: "品牌主张 / 口号", shape: "text" },
    { key: "offerings", label: "主营产品或服务", shape: "lines", hint: "一行一项" },
  ] },
  { title: "品牌调性", note: "旗下所有角色都要遵守", fields: [
    { key: "tone_rules", label: "语气要求", shape: "lines", hint: "一行一条" },
    { key: "preferred_words", label: "常用词", shape: "lines", hint: "一行一个" },
    { key: "forbidden_words", label: "禁用词", shape: "lines", hint: "一行一个；稿子里出现会被拦下" },
  ] },
  { title: "视觉识别", note: "做封面和包装时用", fields: [
    { key: "colors", label: "主色", shape: "lines", hint: "一行一个颜色，如 #FCF8F2 暖米白，底色与背景" },
    { key: "fonts", label: "字体", shape: "lines", hint: "一行一个字体名" },
  ] },
  { title: "统一红线", note: "旗下所有角色都要遵守", fields: [
    { key: "compliance", label: "合规要求", shape: "lines", hint: "一行一条" },
    { key: "red_lines", label: "不能说的话", shape: "lines", hint: "一行一条；稿子里原样出现会被拦下" },
  ] },
];

const LABELS: Record<string, string> = Object.fromEntries(GROUPS.flatMap(group => group.fields).map(field => [field.key, field.label]));

function saveError(cause: unknown) {
  const detail = cause instanceof ApiError ? cause.detail as { code?: string; fields?: string[] } | undefined : undefined;
  if (detail?.code !== "identity_profile_invalid") return errorText(cause);
  const names = [...new Set((detail.fields || []).map(field => LABELS[field.split(".")[0]] || field))];
  return `这些项填写不符合要求：${names.join("、")}`;
}

const asText = (value: unknown) => Array.isArray(value) ? value.map(String).join("\n") : typeof value === "string" ? value : "";

function Block({ title, note, children }: { title: string; note: string; children: ReactNode }) {
  return <section className="border-t border-ink-200/80 py-7 first:border-t-0 first:pt-0">
    <div className="grid gap-x-10 gap-y-4 xl:grid-cols-[168px_minmax(0,1fr)]">
      <div><h3 className="font-serif text-[17px] font-semibold text-ink-900">{title}</h3><p className="mt-1 text-[12.5px] leading-relaxed text-ink-500">{note}</p></div>
      <div className="min-w-0">{children}</div>
    </div>
  </section>;
}

function useLogos(brandId: number, revisionNo: number) {
  const [items, setItems] = useState<Portrait[]>([]);
  const [issue, setIssue] = useState("");
  useEffect(() => {
    let alive = true;
    api.get<{ items: Portrait[] }>(`/content-brands/${brandId}/logos`).then(data => { if (alive) setItems(data.items); }).catch(cause => { if (alive) setIssue(errorText(cause)); });
    return () => { alive = false; };
  }, [brandId, revisionNo]);
  return { items, issue };
}

function Logos({ items }: { items: Portrait[] }) {
  return items.length ? <div className="flex flex-wrap gap-3">{items.map(item => <div key={item.material_revision_id} className="space-y-1"><StoredThumb item={item} />{!item.usable && <p className="text-[12px] text-amber-700">这张不能再用</p>}</div>)}</div> : <p className="text-[14px] text-ink-400">未设置</p>;
}

async function squarestLogo(items: Portrait[]) {
  const loaded = await Promise.all(items.filter(item => item.usable && item.material_id).map(async item => {
    const response = await fetch(`/api/v1/materials/${item.material_id}/revisions/${item.material_revision_id}/raw`, { headers: { "X-Studio-User": currentUser() } });
    if (!response.ok) return null;
    const blob = await response.blob();
    const bitmap = await createImageBitmap(blob);
    const ratio = Math.max(bitmap.width, bitmap.height) / Math.max(1, Math.min(bitmap.width, bitmap.height));
    bitmap.close();
    return { blob, ratio };
  }));
  const best = loaded.filter(row => row !== null).sort((one, two) => one.ratio - two.ratio)[0];
  return best ? URL.createObjectURL(best.blob) : null;
}

// A brand keeps wide and square logos; the card has room only for the square one. Cards of one brand share the cached pick.
export function BrandLogoMark({ brandId, brandName }: { brandId: number; brandName: string }) {
  const logo = useQuery({ queryKey: ["brand-square-logo", brandId, currentUser()], queryFn: async () => squarestLogo((await api.get<{ items: Portrait[] }>(`/content-brands/${brandId}/logos`)).items), retry: false, staleTime: 60_000 });
  return logo.data ? <img src={logo.data} alt={`${brandName} Logo`} className="h-7 w-7 rounded-md border border-ink-200 bg-white object-contain" /> : null;
}

export function BrandOverview({ brandId, revision, personas }: { brandId: number; revision: Revision; personas: ReactNode }) {
  const profile = revision?.profile || {};
  const { items, issue } = useLogos(brandId, revision?.revision_no ?? 0);
  const value = (key: string, shape: Shape) => {
    const text = asText(profile[key]);
    if (!text) return <p className="text-[14px] text-ink-400">未设置</p>;
    return shape === "lines" ? <ul className="space-y-1 text-[14px] text-ink-800">{text.split("\n").map(line => <li key={line}>{line}</li>)}</ul> : <p className="text-[14px] text-ink-800">{text}</p>;
  };
  return <div>
    {GROUPS.map(group => <Block key={group.title} title={group.title} note={group.note}>
      <div className="grid gap-5 md:grid-cols-2">{group.fields.map(field => <div key={field.key}><p className="mb-1 text-[12.5px] font-medium text-ink-500">{field.label}</p>{value(field.key, field.shape)}</div>)}
        {group.title === "视觉识别" && <div className="md:col-span-2"><p className="mb-1 text-[12.5px] font-medium text-ink-500">Logo</p><Logos items={items} />{issue && <ErrorBanner message={issue} />}</div>}</div>
    </Block>)}
    <Block title="旗下角色" note="只做展示">{personas}</Block>
  </div>;
}

// The whole brand profile is one revision; logos upload to the common library and save with the rest.
export function BrandProfileEditor({ brandId, brandName, revision, readOnly, onSaved }: {
  brandId: number; brandName: string; revision: Revision; readOnly: boolean; onSaved: () => Promise<void>;
}) {
  const revisionNo = revision?.revision_no ?? 0;
  const initial = () => Object.fromEntries(GROUPS.flatMap(group => group.fields).map(field => [field.key, asText(revision?.profile?.[field.key])]));
  const [draft, setDraft] = useState<Record<string, string>>(initial);
  const { items } = useLogos(brandId, revisionNo);
  const [logos, setLogos] = useState<number[] | null>(null);
  const [previews, setPreviews] = useState<Record<number, string>>({});
  const [busy, setBusy] = useState(false);
  const [issue, setIssue] = useState("");
  useEffect(() => { setDraft(initial()); setLogos(null); }, [brandId, revisionNo]);
  const logoIds = logos ?? items.map(item => item.material_revision_id);
  const off = readOnly || busy;
  async function save(nextLogos = logoIds) {
    setBusy(true); setIssue("");
    try {
      const profile: Profile = {};
      for (const field of GROUPS.flatMap(group => group.fields)) {
        const text = draft[field.key].trim();
        if (!text) continue;
        profile[field.key] = field.shape === "lines" ? text.split("\n").map(line => line.trim()).filter(Boolean) : text;
      }
      if (nextLogos.length) profile.logo_material_revision_ids = nextLogos;
      await api.post(`/content-brands/${brandId}/revisions`, { expected_revision: revisionNo, profile });
      await onSaved();
    } catch (cause) { setIssue(saveError(cause)); } finally { setBusy(false); }
  }
  async function addLogos(files: File[]) {
    setBusy(true); setIssue("");
    try {
      const uploaded = await Promise.all(files.map(async file => [await uploadPortrait(file, brandName, `${brandName} Logo`, "Logo"), URL.createObjectURL(file)] as const));
      setPreviews({ ...previews, ...Object.fromEntries(uploaded) });
      setLogos([...logoIds, ...uploaded.map(([id]) => id)]);
    }
    catch (cause) { setIssue(errorText(cause)); } finally { setBusy(false); }
  }
  return <div className="space-y-8">
    {GROUPS.map(group => <section key={group.title} className="min-w-0"><h3 className="mb-1 font-serif text-[20px] font-semibold text-ink-900">{group.title}</h3><p className="mb-4 text-[12.5px] text-ink-500">{group.note}</p>
      <div className="grid min-w-0 grid-cols-1 gap-4 xl:grid-cols-2">{group.fields.map(field => <div key={field.key} className="min-w-0 rounded-[16px] border border-ink-200/90 bg-surface p-5">
        <label className="font-serif text-[16px] font-semibold text-ink-900" htmlFor={`brand-${field.key}`}>{field.label}</label>
        {field.hint && <p className="mt-1 text-[12px] text-ink-500">{field.hint}</p>}
        {field.shape === "text" ? <input id={`brand-${field.key}`} disabled={off} className={`${inputClass} mt-3`} value={draft[field.key]} onChange={event => setDraft({ ...draft, [field.key]: event.target.value })} />
          : <textarea id={`brand-${field.key}`} disabled={off} className={`${inputClass} mt-3 min-h-[88px]`} value={draft[field.key]} onChange={event => setDraft({ ...draft, [field.key]: event.target.value })} />}
      </div>)}
        {group.title === "视觉识别" && <div className="min-w-0 rounded-[16px] border border-ink-200/90 bg-surface p-5 xl:col-span-2">
          <p className="font-serif text-[16px] font-semibold text-ink-900">Logo</p><p className="mt-1 text-[12px] text-ink-500">最多 {MAX_LOGOS} 张，放进通用素材库；随资料一起保存。</p>
          <div className="mt-3 flex flex-wrap gap-3">
            {logoIds.map(id => { const item = items.find(row => row.material_revision_id === id); return <div key={id} className="space-y-1">{item ? <StoredThumb item={item} /> : previews[id] ? <img src={previews[id]} alt="待保存的 Logo" className="h-24 w-24 rounded-lg border border-ink-200 object-contain" /> : <div className="flex h-24 w-24 items-center justify-center rounded-lg bg-ink-100 text-[12px] text-ink-500">待保存</div>}<button type="button" className="text-[12px] text-ink-500 hover:text-red-600" disabled={off} onClick={() => setLogos(logoIds.filter(other => other !== id))}>移除</button></div>; })}
            {logoIds.length < MAX_LOGOS && <FileButton label="＋ Logo" disabled={off} room={MAX_LOGOS - logoIds.length} onPick={files => void addLogos(files)} />}
          </div>
        </div>}
      </div>
    </section>)}
    {issue && <ErrorBanner message={issue} />}
    <div className="sticky bottom-4 z-10 flex items-center justify-between gap-4 rounded-pill border border-ink-200 bg-surface/95 py-2 pl-6 pr-2 shadow-lift backdrop-blur"><span className="text-[13px] text-ink-600">保存后生成新修订，旧作品的快照不会改变。</span><Button onClick={() => void save()} disabled={off}>{busy ? "保存中…" : `保存为 v${revisionNo + 1}`}</Button></div>
  </div>;
}
