import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { api, ApiError, currentUser } from "../api";
import { Button, ErrorBanner, Field, Spinner, inputClass } from "../components/ui";

const errorText = (e: unknown) => e instanceof ApiError ? (e.detail as { message?: string } | undefined)?.message || e.message : e instanceof Error ? e.message : "保存失败";

// Search engines rank big portals first; this list is how the user says which sites are worth looking at before the rest.
export default function WebMaterialSiteSettings() {
  const client = useQueryClient();
  const key = ["web-material-sites", currentUser()];
  const sites = useQuery({ queryKey: key, retry: false, queryFn: () => api.get<{ sites: string[] }>("/settings/web-material-sites") });
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [issue, setIssue] = useState("");
  const [saved, setSaved] = useState(false);
  useEffect(() => { if (sites.data) setText(sites.data.sites.join("\n")); }, [sites.data]);
  async function save() {
    setBusy(true); setIssue(""); setSaved(false);
    try {
      const result = await api.put<{ sites: string[] }>("/settings/web-material-sites", { sites: text.split(/[\n,，\s]+/).filter(Boolean) });
      client.setQueryData(key, result);
      setSaved(true);
    } catch (e) { setIssue(errorText(e)); } finally { setBusy(false); }
  }
  if (sites.isLoading) return <Spinner label="读取优先站点…" />;
  return <section className="max-w-2xl space-y-4 rounded-xl border border-slate-200 bg-white p-5">
    <Field label="优先站点（一行一个网站）" hint="网上找图时，这些网站的结果排在前面并标「优先站点」。写域名即可，例如 oppo.com、sspai.com；最多 50 个。">
      <textarea aria-label="优先站点" rows={8} className={inputClass} value={text} onChange={e => { setText(e.target.value); setSaved(false); }} />
    </Field>
    {issue && <ErrorBanner message={issue} />}
    <div className="flex items-center gap-3"><Button disabled={busy} onClick={() => void save()}>{busy ? "保存中…" : "保存"}</Button>{saved && <span className="text-sm text-emerald-700">已保存</span>}</div>
  </section>;
}
