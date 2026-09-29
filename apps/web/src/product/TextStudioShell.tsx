import { useEffect, useRef, useState } from "react";
import { Mark } from "@tiptap/core";
import { EditorContent, useEditor } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import { Button, Field, inputClass } from "../components/ui";
import { api } from "../api";
import type { SharedAsset } from "./project/types";
import { appendBlock, bindCitation, insertAsset, removeBlock, replaceBlockRuns, toCodePointOffset, unbindCitation, updateTextDocument, type TextBlock, type TextDraft, type TextRun, type TextSelection } from "./TextStudioModel";
import { runsToTiptap, tiptapToRuns } from "./TextTiptapAdapter";

export type TextStudioProps = { projectId: number; unitId: number; masterId: number | null; masterHash: string | null; savedAssetIds: number[]; savedCitationIds: string[]; identitySnapshotId: number | null; boundaryRevisionId: number | null; draft: TextDraft | null; legacyPayload?: Record<string, unknown> | null; onChange: (draft: TextDraft) => void; readOnly: boolean; epoch: number; onIssue: (message: string) => void };
type Boundary = { id: number; fact_pack_id: number; fact_pack_version: number; fact_pack_checksum: string };
type EvidenceItem = { item_id: number; evidence_kind: string; snapshot_checksum: string; statement: string | null; snapshot: Record<string, unknown> | null; public_use_allowed: boolean; public_use_revoked_at: string | null };
type Suggestion = { applied_document: TextDraft["payload"]["document"]; suggested_evidence_refs: TextDraft["evidenceRefs"]; invalidated_citation_ids: string[]; before_document_hash: string; after_document_hash: string; llm_run_id: number; provenance: { operation: string; provider: string; model: string } };
type Identity = { id: number; checksum: string; effective_profile: Record<string, unknown>; field_origins: Record<string, string> };
function previewDocument(document: TextDraft["payload"]["document"]): string {
  return document.blocks.map((block) => "content" in block ? block.content.map((run) => run.text).join("") : "items" in block ? block.items.map((item) => item.content.map((run) => run.text).join("")).join("\n") : block.type === "code" ? block.code : block.type === "divider" ? "—" : `[ ${block.type} #${block.material_revision_id} ]`).join("\n\n");
}

const LinkMark = Mark.create({
  name: "link",
  addAttributes() { return { href: { default: null } }; },
  parseHTML() { return [{ tag: "a[href]" }]; },
  renderHTML({ HTMLAttributes }) { return ["a", { href: HTMLAttributes.href, rel: "noopener noreferrer" }, 0]; },
});

function InlineEditor({ runs, onChange, onSelection, readOnly, label, onIssue }: { runs: TextRun[]; onChange: (runs: TextRun[]) => void; onSelection: (range: { start: number; end: number; text: string } | null) => void; readOnly: boolean; label: string; onIssue: (message: string) => void }) {
  const [activeMarks, setActiveMarks] = useState({ bold: false, italic: false, code: false, link: false });
  const callback = useRef(onChange); callback.current = onChange;
  const currentRuns = useRef(runs); currentRuns.current = runs;
  const issue = useRef(onIssue); issue.current = onIssue;
  const selection = useRef(onSelection); selection.current = onSelection;
  const editor = useEditor({
    extensions: [StarterKit.configure({ heading: false, blockquote: false, bulletList: false, orderedList: false, codeBlock: false, horizontalRule: false }), LinkMark],
    content: runsToTiptap(runs), editable: !readOnly,
    editorProps: { attributes: { "aria-label": label, class: "min-h-14 rounded border border-slate-200 bg-white px-3 py-2 text-sm focus:outline-none" }, handleKeyDown(view, event) { if (event.key === "Enter") { view.dispatch(view.state.tr.replaceSelectionWith(view.state.schema.nodes.hardBreak.create()).scrollIntoView()); return true; } return false; } },
    onUpdate({ editor: current }) { try { const nextRuns = tiptapToRuns(current.getJSON()); if (JSON.stringify(nextRuns) !== JSON.stringify(tiptapToRuns(runsToTiptap(currentRuns.current)))) callback.current(nextRuns); issue.current(""); } catch (error) { issue.current(error instanceof Error ? error.message : "编辑器存在不支持的内容"); } },
    onSelectionUpdate({ editor: current }) {
      const { from, to, empty } = current.state.selection;
      if (empty) { selection.current(null); return; }
      const before = current.state.doc.textBetween(1, from, "", "\n");
      const through = current.state.doc.textBetween(1, to, "", "\n");
      const full = current.state.doc.textBetween(1, current.state.doc.content.size - 1, "", "\n");
      try {
        const start = toCodePointOffset(before, before.length);
        const end = toCodePointOffset(through, through.length);
        selection.current({ start, end, text: Array.from(full).slice(start, end).join("") });
      } catch { selection.current(null); }
    },
  }, []);
  useEffect(() => { editor?.setEditable(!readOnly); }, [editor, readOnly]);
  useEffect(() => {
    if (!editor) return;
    const syncMarks = () => setActiveMarks({ bold: editor.isActive("bold"), italic: editor.isActive("italic"), code: editor.isActive("code"), link: editor.isActive("link") });
    editor.on("transaction", syncMarks);
    syncMarks();
    return () => { editor.off("transaction", syncMarks); };
  }, [editor]);
  if (!editor) return <p className="text-xs text-slate-500">加载编辑器…</p>;
  return <div className="space-y-1"><div className="flex flex-wrap gap-1" role="group" aria-label={`${label} 格式`}>
    <Button size="sm" variant={activeMarks.bold ? "primary" : "secondary"} ariaPressed={activeMarks.bold} disabled={readOnly} onClick={() => editor.chain().focus().toggleBold().run()}>加粗</Button>
    <Button size="sm" variant={activeMarks.italic ? "primary" : "secondary"} ariaPressed={activeMarks.italic} disabled={readOnly} onClick={() => editor.chain().focus().toggleItalic().run()}>斜体</Button>
    <Button size="sm" variant={activeMarks.code ? "primary" : "secondary"} ariaPressed={activeMarks.code} disabled={readOnly} onClick={() => editor.chain().focus().toggleCode().run()}>行内代码</Button>
    <Button size="sm" variant={activeMarks.link ? "primary" : "secondary"} ariaPressed={activeMarks.link} disabled={readOnly} onClick={() => { const href = window.prompt("输入 https:// 链接"); if (!href) return; if (!/^https?:\/\/[^\s]+$/.test(href)) { issue.current("链接必须是完整的 http(s) 地址"); return; } editor.chain().focus().setMark("link", { href }).run(); }}>链接</Button>
    <Button size="sm" variant="ghost" disabled={readOnly} onClick={() => editor.chain().focus().unsetMark("link").run()}>移除链接</Button>
  </div><EditorContent editor={editor} /></div>;
}

function BlockEditor({ block, draft, onChange, onSelection, readOnly, onIssue, epoch }: { block: TextBlock; draft: TextDraft; onChange: (draft: TextDraft) => void; onSelection: (selection: TextSelection | null) => void; readOnly: boolean; onIssue: (message: string) => void; epoch: number }) {
  const blocks = draft.payload.document.blocks;
  const position = blocks.findIndex((item) => item.id === block.id);
  function patch(next: TextBlock) { onChange(updateTextDocument(draft, { ...draft.payload.document, blocks: blocks.map((item) => item.id === block.id ? next : item) })); }
  function move(delta: number) { const next = [...blocks]; [next[position], next[position + delta]] = [next[position + delta], next[position]]; onChange(updateTextDocument(draft, { ...draft.payload.document, blocks: next })); }
  const label = `${block.type} 区块 ${position + 1}`;
  return <div className="rounded-lg border border-slate-200 bg-slate-50 p-3" data-block-id={block.id}>
    <div className="mb-2 flex flex-wrap items-center justify-between gap-2"><span className="text-xs font-medium text-slate-600">{label} · {block.id.slice(0, 8)}</span><div className="flex gap-1"><Button size="sm" variant="ghost" disabled={readOnly || position === 0} onClick={() => move(-1)}>上移</Button><Button size="sm" variant="ghost" disabled={readOnly || position === blocks.length - 1} onClick={() => move(1)}>下移</Button><Button size="sm" variant="danger" disabled={readOnly} onClick={() => onChange(removeBlock(draft, block.id))}>删除</Button></div></div>
    {"content" in block && <div className="space-y-2">
      {block.type === "heading" && <select aria-label={`${label} 层级`} className={inputClass} value={block.level} disabled={readOnly} onChange={(event) => patch({ ...block, level: Number(event.target.value) })}>{[1, 2, 3, 4].map((level) => <option key={level} value={level}>H{level}</option>)}</select>}
      {block.type === "callout" && <select aria-label={`${label} 提示类型`} className={inputClass} value={block.tone} disabled={readOnly} onChange={(event) => patch({ ...block, tone: event.target.value as "info" | "note" | "warning" })}><option value="info">信息</option><option value="note">备注</option><option value="warning">警示</option></select>}
      <InlineEditor key={`${epoch}-${block.id}`} runs={block.content} readOnly={readOnly} label={label} onIssue={onIssue} onSelection={(range) => onSelection(range ? { blockId: block.id, ...range } : null)} onChange={(runs) => onChange(replaceBlockRuns(draft, block.id, runs))} />
      {block.type === "quote" && <input className={inputClass} aria-label={`${label} 署名`} value={block.attribution || ""} disabled={readOnly} onChange={(event) => patch({ ...block, attribution: event.target.value })} placeholder="可选署名" />}
    </div>}
    {"items" in block && <div className="space-y-2">{block.items.map((item, index) => <div key={item.id} className="flex items-start gap-2"><span className="pt-9 text-xs">{block.type === "bullet_list" ? "•" : `${index + 1}.`}</span><div className="min-w-0 flex-1"><InlineEditor key={`${epoch}-${item.id}`} runs={item.content} readOnly={readOnly} label={`${label} 第 ${index + 1} 项`} onIssue={onIssue} onSelection={(range) => onSelection(range ? { blockId: block.id, listItemId: item.id, ...range } : null)} onChange={(runs) => onChange(replaceBlockRuns(draft, block.id, runs, item.id))} /></div><Button size="sm" variant="ghost" disabled={readOnly || block.items.length <= 1} onClick={() => patch({ ...block, items: block.items.filter((row) => row.id !== item.id) })}>移除项</Button></div>)}<Button size="sm" variant="secondary" disabled={readOnly} onClick={() => patch({ ...block, items: [...block.items, { id: crypto.randomUUID(), content: [] }] })}>添加列表项</Button></div>}
    {block.type === "code" && <div className="space-y-2"><input className={inputClass} aria-label={`${label} 语言`} value={block.language} disabled={readOnly} onChange={(event) => patch({ ...block, language: event.target.value })} placeholder="语言，可留空" /><textarea className={`${inputClass} font-mono`} aria-label={`${label} 代码`} rows={5} value={block.code} readOnly={readOnly} onChange={(event) => patch({ ...block, code: event.target.value })} /></div>}
    {(block.type === "image" || block.type === "chart") && <p className="text-sm">MaterialRevision #{block.material_revision_id} · {block.alt_text || "未填写替代文字"} · {block.caption || "无说明"}</p>}
    {block.type === "divider" && <hr className="border-slate-300" />}
  </div>;
}

export default function TextStudioShell({ projectId, unitId, masterId, masterHash, savedAssetIds, savedCitationIds, identitySnapshotId, boundaryRevisionId, draft, legacyPayload, onChange, readOnly, epoch, onIssue }: TextStudioProps) {
  const [kind, setKind] = useState<"heading" | "paragraph" | "quote" | "bullet_list" | "ordered_list" | "callout" | "code" | "divider">("paragraph");
  const [assets, setAssets] = useState<SharedAsset[]>([]);
  const [boundary, setBoundary] = useState<Boundary | null>(null);
  const [evidence, setEvidence] = useState<EvidenceItem[]>([]);
  const [selection, setSelection] = useState<TextSelection | null>(null);
  const [panelError, setPanelError] = useState("");
  const [identity, setIdentity] = useState<Identity | null>(null);
  const [operation, setOperation] = useState<"rewrite" | "expand" | "shorten" | "tone" | "restructure">("rewrite");
  const [instruction, setInstruction] = useState("");
  const [restructureFrom, setRestructureFrom] = useState("");
  const [restructureTo, setRestructureTo] = useState("");
  const [suggestion, setSuggestion] = useState<{ result: Suggestion; baseDocument: string } | null>(null);
  const [aiBusy, setAiBusy] = useState(false);
  const [lastAcceptedDocument, setLastAcceptedDocument] = useState<string | null>(null);
  const [localEpoch, setLocalEpoch] = useState(0);
  const [editorIssues, setEditorIssues] = useState<Record<string, string>>({});
  useEffect(() => { setSuggestion(null); setLastAcceptedDocument(null); setSelection(null); setLocalEpoch(0); setEditorIssues({}); }, [epoch]);
  useEffect(() => { const active = new Set(draft?.payload.document.blocks.map((block) => block.id) || []); setEditorIssues((current) => Object.keys(current).some((id) => !active.has(id)) ? Object.fromEntries(Object.entries(current).filter(([id]) => active.has(id))) : current); }, [draft?.payload.document.blocks]);
  useEffect(() => { onIssue(Object.values(editorIssues).find(Boolean) || ""); }, [editorIssues, onIssue]);
  useEffect(() => {
    let active = true;
    setIdentity(null);
    if (identitySnapshotId) api.get<Identity>(`/identity-snapshots/${identitySnapshotId}`).then((value) => { if (active) setIdentity(value); }).catch((error) => { if (active) setPanelError(error instanceof Error ? error.message : "无法读取固定身份"); });
    return () => { active = false; };
  }, [identitySnapshotId]);
  useEffect(() => {
    let active = true;
    Promise.all([api.get<SharedAsset[]>(`/content-projects/${projectId}/shared-assets`), api.get<Boundary | null>(`/content-projects/${projectId}/fact-boundary`)]).then(async ([nextAssets, nextBoundary]) => {
      const nextEvidence = nextBoundary ? await api.get<{ items: EvidenceItem[] }>(`/fact-packs/${nextBoundary.fact_pack_id}`) : null;
      if (active) { setAssets(nextAssets.slice(0, 200)); setBoundary(nextBoundary); setEvidence(nextEvidence?.items || []); }
    }).catch((error) => { if (active) setPanelError(error instanceof Error ? error.message : "无法读取素材和事实边界"); });
    return () => { active = false; };
  }, [projectId, epoch]);
  async function attach(item: EvidenceItem) {
    if (!draft || !selection) return;
    try {
      const bytes = new TextEncoder().encode(selection.text);
      const checksum = Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256", bytes))).map((value) => value.toString(16).padStart(2, "0")).join("");
      onChange(bindCitation(draft, selection, item, checksum));
      setPanelError(""); setSelection(null);
    } catch (error) { setPanelError(error instanceof Error ? error.message : "证据引用失败"); }
  }
  async function requestSuggestion() {
    if (!draft || !masterId || !masterHash || readOnly) return;
    if (draft.assetRefs.some((ref) => !savedAssetIds.includes(ref.material_revision_id))) { setPanelError("新插入的素材必须先保存 Master，才能进入 AI 建议的可信素材上下文。"); return; }
    if (draft.payload.document.citations.some((citation) => !savedCitationIds.includes(citation.id))) { setPanelError("新绑定的证据必须先保存 Master，才能进入 AI 建议的可信引用上下文。"); return; }
    if (draft.aiEdits.length && lastAcceptedDocument !== JSON.stringify(draft.payload.document)) { setPanelError("AI 建议链已被手工编辑打断；请先保存 Master，再发起下一次 AI 建议。"); return; }
    const selected = operation === "restructure" ? { from_block_id: restructureFrom, to_block_id: restructureTo } : selection ? { block_id: selection.blockId, ...(selection.listItemId ? { list_item_id: selection.listItemId } : {}), start: selection.start, end: selection.end } : null;
    if (!selected) { setPanelError("先选中要处理的文字或区块范围。"); return; }
    setAiBusy(true); setPanelError(""); setSuggestion(null);
    try {
      const baseDocument = JSON.stringify(draft.payload.document);
      const result = await api.post<Suggestion>(`/content-projects/${projectId}/units/${unitId}/master-revisions/${masterId}/text-suggestions`, { base_payload_hash: masterHash, working_document: draft.payload.document, operation, selection: selected, instruction });
      setSuggestion({ result, baseDocument });
    } catch (error) { setPanelError(error instanceof Error ? error.message : "AI 建议不可用"); }
    finally { setAiBusy(false); }
  }
  function acceptSuggestion() {
    if (!draft || !suggestion) return;
    if (JSON.stringify(draft.payload.document) !== suggestion.baseDocument) { setPanelError("正文已变化，此建议已过期；请重新请求。"); setSuggestion(null); return; }
    const next = { ...draft, payload: { ...draft.payload, document: suggestion.result.applied_document }, evidenceRefs: suggestion.result.suggested_evidence_refs, aiEdits: [...draft.aiEdits, { llm_run_id: suggestion.result.llm_run_id }], invalidatedCitationIds: [...draft.invalidatedCitationIds, ...suggestion.result.invalidated_citation_ids] };
    onChange(next); setLastAcceptedDocument(JSON.stringify(next.payload.document)); setLocalEpoch((value) => value + 1); setSuggestion(null); setSelection(null);
  }
  if (!draft) return <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm"><p>这是历史 text.master.v1。正文只读；继续编辑需先预览并显式升级到 v2。</p><pre className="mt-2 whitespace-pre-wrap">{String(legacyPayload?.markdown || "无正文")}</pre></div>;
  return <div className="space-y-4" aria-label="专业文字工作台"><Field label="标题"><input className={inputClass} aria-label="Text Master 标题" value={draft.payload.title} disabled={readOnly} onChange={(event) => onChange({ ...draft, payload: { ...draft.payload, title: event.target.value } })} /></Field>
    <div className="space-y-3">{draft.payload.document.blocks.map((block) => <BlockEditor key={block.id} block={block} draft={draft} onChange={onChange} onSelection={setSelection} readOnly={readOnly} onIssue={(message) => setEditorIssues((current) => current[block.id] === message ? current : { ...current, [block.id]: message })} epoch={epoch + localEpoch} />)}</div>
    <div className="flex flex-wrap items-center gap-2"><select aria-label="添加区块类型" className={inputClass} value={kind} disabled={readOnly} onChange={(event) => setKind(event.target.value as typeof kind)}>{[["paragraph", "正文"], ["heading", "标题"], ["quote", "引用"], ["bullet_list", "无序列表"], ["ordered_list", "有序列表"], ["callout", "提示"], ["code", "代码"], ["divider", "分隔线"]].map(([value, name]) => <option key={value} value={value}>{name}</option>)}</select><Button variant="secondary" disabled={readOnly} onClick={() => onChange(appendBlock(draft, kind))}>添加区块</Button></div>
    {draft.invalidatedCitationIds.length > 0 && <p className="text-sm text-amber-800">正文变化已使 {draft.invalidatedCitationIds.length} 条引用失效；请重新绑定证据后保存。</p>}
    {panelError && <p role="alert" className="text-sm text-rose-700">{panelError}</p>}
    <section className="rounded-lg border border-slate-200 p-3"><h3 className="font-medium">项目共享素材</h3><p className="text-xs text-slate-500">仅引用精确 MaterialRevision；插入或移除不会复制或删除素材。保存时后端重新校验权利。</p><div className="mt-2 grid max-h-48 gap-2 overflow-auto sm:grid-cols-2">{assets.filter((item) => item.kind === "image" || item.kind === "chart").map((item) => <div key={item.key} className="rounded border p-2 text-xs"><p>{item.title || item.kind} · Revision #{item.material_revision_id}</p><p>{item.rights_status || "权利待核对"} · {item.public_use_allowed ? "允许公开" : "不可公开"}</p><Button size="sm" variant="secondary" disabled={readOnly || item.public_use_allowed !== true} onClick={() => { try { onChange(insertAsset(draft, item)); setPanelError(""); } catch (error) { setPanelError(error instanceof Error ? error.message : "无法插入素材"); } }}>插入{item.kind === "chart" ? "图表" : "图片"}</Button></div>)}</div>{assets.length === 0 && <p className="text-xs text-slate-500">项目暂无共享素材。</p>}</section>
    <section className="rounded-lg border border-slate-200 p-3"><h3 className="font-medium">事实边界与引用</h3><p className="text-xs text-slate-500">选中正文或列表文字，再绑定当前冻结 FactPack 的精确条目；文本变化会使无法重定位的引用失效。</p><p className="mt-1 text-xs">{boundary ? `FactPack #${boundary.fact_pack_id} v${boundary.fact_pack_version} · ${boundary.fact_pack_checksum.slice(0, 12)}…` : "未绑定事实边界"}{boundaryRevisionId && boundary?.id !== boundaryRevisionId ? " · Master 边界已过期，先处理上下文" : ""}</p>{selection && <p className="mt-1 text-xs text-indigo-700">已选：{selection.text}</p>}
      <div className="mt-2 max-h-48 space-y-2 overflow-auto">{evidence.map((item) => <div key={item.item_id} className="flex items-center justify-between gap-2 rounded border p-2 text-xs"><div><p>#{item.item_id} · {item.evidence_kind} · {item.statement || String(item.snapshot?.excerpt || "证据快照")} · {item.public_use_allowed && !item.public_use_revoked_at ? "允许公开" : "已撤权/不可公开"}</p><p>快照 {item.snapshot_checksum?.slice(0, 12) || "缺失"}… · 来源 {String(item.snapshot?.source_title || item.snapshot?.source_url || "待核对")} · 模型使用覆盖以 Text Fact Check 为准</p></div><Button size="sm" variant="secondary" disabled={readOnly || !selection || !boundary || (!!boundaryRevisionId && boundary.id !== boundaryRevisionId) || !item.public_use_allowed || !!item.public_use_revoked_at} onClick={() => attach(item)}>绑定</Button></div>)}</div>
      <div className="mt-2 space-y-1">{draft.payload.document.citations.map((citation) => <div key={citation.id} className="flex items-center justify-between gap-2 text-xs"><span>引用 #{citation.fact_pack_item_id} · {citation.block_id.slice(0, 8)} · [{citation.start}, {citation.end})</span><Button size="sm" variant="ghost" disabled={readOnly} onClick={() => onChange(unbindCitation(draft, citation.id))}>解除引用</Button></div>)}</div>
    </section>
    <section className="space-y-2 rounded-lg border border-slate-200 p-3"><h3 className="font-medium">AI 建议 · 不会自动保存</h3><p className="text-xs text-slate-500">{masterId ? `基于已保存 Master #${masterId}；先看差异，再选择接受或拒绝。` : "先保存第一个 Text Master，才能请求 AI 建议。"}</p>
      <div className="flex flex-wrap gap-2"><select aria-label="AI 编辑动作" className={inputClass} value={operation} disabled={readOnly || aiBusy} onChange={(event) => setOperation(event.target.value as typeof operation)}><option value="rewrite">改写</option><option value="expand">扩写</option><option value="shorten">压缩</option><option value="tone">调整语气</option><option value="restructure">结构重组</option></select><Button disabled={readOnly || aiBusy || !masterId || (operation !== "restructure" && !selection)} onClick={requestSuggestion}>{aiBusy ? "生成中…" : "生成建议"}</Button></div>
      {operation === "restructure" && <div className="flex gap-2"><select aria-label="重组起始区块" className={inputClass} value={restructureFrom} onChange={(event) => setRestructureFrom(event.target.value)}><option value="">起始区块</option>{draft.payload.document.blocks.map((block, index) => <option key={block.id} value={block.id}>{index + 1} · {block.type}</option>)}</select><select aria-label="重组结束区块" className={inputClass} value={restructureTo} onChange={(event) => setRestructureTo(event.target.value)}><option value="">结束区块</option>{draft.payload.document.blocks.map((block, index) => <option key={block.id} value={block.id}>{index + 1} · {block.type}</option>)}</select></div>}
      <textarea aria-label="AI 编辑要求" className={inputClass} rows={2} maxLength={2000} value={instruction} disabled={readOnly} onChange={(event) => setInstruction(event.target.value)} placeholder="可选：说明风格或目标；模型输出仅作为待审建议" />
      {suggestion && <div className="space-y-2 rounded bg-indigo-50 p-3 text-sm"><p>建议 #{suggestion.result.llm_run_id} · {suggestion.result.provenance.provider}/{suggestion.result.provenance.model} · {suggestion.result.provenance.operation}</p><p>前后 document hash：{suggestion.result.before_document_hash.slice(0, 12)}… → {suggestion.result.after_document_hash.slice(0, 12)}…</p><div className="grid gap-2 sm:grid-cols-2"><div><p className="font-medium">修改前</p><pre className="max-h-40 overflow-auto whitespace-pre-wrap">{previewDocument(JSON.parse(suggestion.baseDocument) as TextDraft["payload"]["document"])}</pre></div><div><p className="font-medium">建议后</p><pre className="max-h-40 overflow-auto whitespace-pre-wrap">{previewDocument(suggestion.result.applied_document)}</pre></div></div>{suggestion.result.invalidated_citation_ids.length > 0 && <p className="text-amber-800">将失效引用：{suggestion.result.invalidated_citation_ids.join("、")}</p>}<div className="flex gap-2"><Button disabled={readOnly || JSON.stringify(draft.payload.document) !== suggestion.baseDocument} onClick={acceptSuggestion}>接受到本地草稿</Button><Button variant="secondary" onClick={() => setSuggestion(null)}>拒绝建议</Button></div></div>}
    </section>
    <section className="rounded-lg border border-slate-200 p-3"><h3 className="font-medium">固定身份（只读）</h3>{identity ? <div className="mt-1 text-xs"><p>IdentitySnapshot #{identity.id} · {identity.checksum.slice(0, 12)}…</p><dl className="mt-2 grid gap-1 sm:grid-cols-2">{Object.entries(identity.effective_profile).slice(0, 30).map(([key, value]) => <div key={key}><dt className="font-medium">{key} · {identity.field_origins[key] || "来源待核对"}</dt><dd className="break-words">{typeof value === "string" ? value : JSON.stringify(value)}</dd></div>)}</dl></div> : <p className="text-xs text-amber-800">固定身份不可用；不能假定语气或边界已验证。</p>}</section>
  </div>;
}
