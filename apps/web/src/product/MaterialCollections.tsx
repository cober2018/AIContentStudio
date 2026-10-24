import { UseQueryResult, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api, currentUser } from "../api";
import { Button, EmptyState, ErrorBanner, Field, Modal, Spinner, inputClass } from "../components/ui";
import { readableTime } from "./HomePage";
import { Collection, LibraryMaterial, LibraryPage, mediaKind, usePreview } from "./materialLibraryModel";

function Tile({ item }: { item: LibraryMaterial }) {
  const offline = !!item.drive && item.drive.status !== "available";
  const preview = usePreview(item.id, item.latest_revision?.id, "thumb", !!mediaKind(item) && !offline);
  return <div ref={preview.ref} className={`relative overflow-hidden ${mediaKind(item) === "audio" ? "bg-accent-50" : "bg-ink-100"}`}>
    {preview.url && <img src={preview.url} alt="" className={`absolute inset-0 h-full w-full ${mediaKind(item) === "audio" ? "object-contain px-2" : "object-cover"}`} />}
  </div>;
}

function Mosaic({ collection }: { collection: Collection }) {
  const items = useQuery({ queryKey: ["material-library", currentUser(), "mosaic", collection.id, collection.revision],
    queryFn: () => api.get<LibraryPage>(`/system-library?type=material&status=active&order=newest&limit=4&material_collection_id=${collection.id}`), retry: false });
  const tiles = items.data?.items ?? [];
  const layout = ["grid-cols-1", "grid-cols-1", "grid-cols-2", "grid-cols-2 grid-rows-2 [&>*:first-child]:row-span-2", "grid-cols-2 grid-rows-2"][tiles.length];
  return <div className={`grid aspect-[16/9] gap-0.5 overflow-hidden bg-ink-100 ${layout}`}>
    {tiles.length ? tiles.map(item => <Tile key={item.id} item={item} />) : <div className="grid place-items-center text-[12.5px] text-ink-400">还没有素材</div>}
  </div>;
}

function errorText(error: unknown) { return error instanceof Error ? error.message : "操作失败"; }

export default function MaterialCollections({ collections, open }: { collections: UseQueryResult<{ items: Collection[] }>; open: (id: number) => void }) {
  const client = useQueryClient();
  const [editing, setEditing] = useState<Collection | "new" | null>(null);
  const [form, setForm] = useState({ name: "", description: "" });
  const [state, setState] = useState<{ busy?: boolean; error?: string }>({});
  const start = (target: Collection | "new") => { setEditing(target); setState({}); setForm(target === "new" ? { name: "", description: "" } : { name: target.name, description: target.description ?? "" }); };
  const save = async () => {
    setState({ busy: true });
    try {
      const body = { name: form.name.trim(), description: form.description.trim() || null };
      if (editing === "new") await api.post("/material-collections", body);
      else if (editing) await api.patch(`/material-collections/${editing.id}`, { ...body, expected_revision: editing.revision });
      setEditing(null); setState({});
      await client.invalidateQueries({ queryKey: ["material-collections"] });
    } catch (error) { setState({ error: errorText(error) }); }
  };
  const archive = async (target: Collection) => {
    if (!window.confirm(`归档合集「${target.name}」？里面的素材不受影响。`)) return;
    try { await api.del(`/material-collections/${target.id}?expected_revision=${target.revision}`); await client.invalidateQueries({ queryKey: ["material-collections"] }); }
    catch (error) { setState({ error: errorText(error) }); }
  };
  const items = collections.data?.items ?? [];
  return <div className="space-y-6">
    <div className="flex flex-wrap items-center justify-between gap-3">
      <p className="max-w-2xl text-[13.5px] leading-relaxed text-ink-600">把一个栏目或主题常用的素材收在一起，找起来更快。素材打开后可以加入合集。</p>
      <Button onClick={() => start("new")}>新建合集</Button>
    </div>
    {state.error && !editing && <ErrorBanner message={state.error} />}
    {collections.isPending ? <Spinner /> : collections.isError ? <ErrorBanner message={errorText(collections.error)} /> : !items.length
      ? <EmptyState title="还没有合集" hint="比如「AI 工具实拍」「城市空镜」「片头片尾」。" action={<Button onClick={() => start("new")}>新建合集</Button>} />
      : <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">{items.map(item => <article key={item.id} className="card flex animate-rise flex-col overflow-hidden">
        <button aria-label={`查看合集「${item.name}」`} onClick={() => open(item.id)}><Mosaic collection={item} /></button>
        <div className="flex flex-1 flex-col p-6">
        <button className="text-left" onClick={() => open(item.id)}>
          <p className="font-serif text-[18px] font-semibold text-ink-900 hover:text-accent-700">{item.name}</p>
          {item.description && <p className="mt-1.5 line-clamp-2 text-[13px] leading-relaxed text-ink-600">{item.description}</p>}
        </button>
        <p className="mt-4 text-[12.5px] text-ink-500"><span className="font-serif text-[20px] font-semibold tabular-nums text-ink-900">{item.item_count}</span> 个素材 · {readableTime(item.updated_at ?? "")}更新</p>
        <div className="mt-auto flex gap-1 pt-4">
          <Button size="sm" variant="secondary" onClick={() => open(item.id)}>查看素材</Button>
          <Button size="sm" variant="ghost" onClick={() => start(item)}>编辑</Button>
          <Button size="sm" variant="ghost" onClick={() => void archive(item)}>归档</Button>
        </div>
        </div>
      </article>)}</div>}
    {editing && <Modal title={editing === "new" ? "新建合集" : "编辑合集"} onClose={() => setEditing(null)}>
      <div className="space-y-4">
        <Field label="名称"><input className={inputClass} value={form.name} maxLength={300} onChange={event => setForm({ ...form, name: event.target.value })} /></Field>
        <Field label="说明（可选）"><textarea className={inputClass} rows={3} value={form.description} maxLength={5000} onChange={event => setForm({ ...form, description: event.target.value })} /></Field>
        {state.error && <ErrorBanner message={state.error} />}
        <div className="flex justify-end gap-2"><Button variant="secondary" onClick={() => setEditing(null)}>取消</Button><Button disabled={state.busy || !form.name.trim()} onClick={() => void save()}>保存</Button></div>
      </div>
    </Modal>}
  </div>;
}
