export type TextMark = { type: "bold" | "italic" | "code" | "link"; href?: string };
export type TextRun = { text: string; marks: TextMark[] };
export type TextContentBlock = { id: string; type: "heading" | "paragraph" | "quote" | "callout"; content: TextRun[]; level?: number; tone?: "info" | "note" | "warning"; attribution?: string };
export type TextListBlock = { id: string; type: "bullet_list" | "ordered_list"; items: { id: string; content: TextRun[] }[] };
export type TextBlock = TextContentBlock | TextListBlock | { id: string; type: "code"; code: string; language: string } | { id: string; type: "image" | "chart"; material_revision_id: number; alt_text?: string; caption?: string } | { id: string; type: "divider" };
export type TextCitation = { id: string; block_id: string; list_item_id?: string; start: number; end: number; fact_pack_item_id: number; selected_text_hash: string; label?: string };
export type TextDocument = { schema: "studio.text.document.v1"; blocks: TextBlock[]; citations: TextCitation[] };
export type TextPayload = { title: string; document: TextDocument };
export type AssetRef = { material_revision_id: number; content_hash: string; role?: string; slot_key?: string; sort_order?: number; placement?: Record<string, unknown> };
export type EvidenceRef = { fact_pack_item_id: number; snapshot_checksum: string; role?: string; sort_order?: number; locator: Record<string, unknown> };
export type TextDraft = { payloadSchema: "text.master.v2"; payload: TextPayload; assetRefs: AssetRef[]; evidenceRefs: EvidenceRef[]; aiEdits: { llm_run_id: number }[]; invalidatedCitationIds: string[] };

export function createTextDraft(): TextDraft {
  return { payloadSchema: "text.master.v2", payload: { title: "", document: { schema: "studio.text.document.v1", blocks: [{ id: crypto.randomUUID(), type: "paragraph", content: [] }], citations: [] } }, assetRefs: [], evidenceRefs: [], aiEdits: [], invalidatedCitationIds: [] };
}

export function draftFromMaster(master: { payload_schema: string; payload: Record<string, unknown>; assets?: Record<string, unknown>[]; evidence?: Record<string, unknown>[] }): TextDraft {
  if (master.payload_schema !== "text.master.v2") throw new Error("Text Master v1 requires explicit upgrade before editing");
  const payload = master.payload as TextPayload;
  if (payload?.document?.schema !== "studio.text.document.v1" || !Array.isArray(payload.document.blocks) || !Array.isArray(payload.document.citations)) throw new Error("Unsupported Studio document");
  return {
    payloadSchema: "text.master.v2", payload: structuredClone(payload),
    assetRefs: (master.assets || []).map((row) => ({ material_revision_id: Number(row.material_revision_id), content_hash: String(row.content_hash), ...(row.role != null ? { role: String(row.role) } : {}), ...(row.slot_key != null ? { slot_key: String(row.slot_key) } : {}), ...(row.sort_order != null ? { sort_order: Number(row.sort_order) } : {}), ...(row.placement != null ? { placement: row.placement as Record<string, unknown> } : {}) })),
    evidenceRefs: (master.evidence || []).map((row) => ({ fact_pack_item_id: Number(row.fact_pack_item_id), snapshot_checksum: String(row.snapshot_checksum), ...(row.role != null ? { role: String(row.role) } : {}), ...(row.sort_order != null ? { sort_order: Number(row.sort_order) } : {}), locator: (row.locator || {}) as Record<string, unknown> })),
    aiEdits: [], invalidatedCitationIds: [],
  };
}

export function plainRuns(runs: TextRun[]): string { return runs.map((run) => run.text).join(""); }

export function toCodePointOffset(text: string, utf16Offset: number): number {
  if (!Number.isInteger(utf16Offset) || utf16Offset < 0 || utf16Offset > text.length) throw new Error("Invalid selection offset");
  if (utf16Offset > 0 && utf16Offset < text.length && /[\uD800-\uDBFF]/.test(text[utf16Offset - 1]) && /[\uDC00-\uDFFF]/.test(text[utf16Offset])) throw new Error("Selection splits surrogate pair");
  return Array.from(text.slice(0, utf16Offset)).length;
}

function targetText(document: TextDocument, citation: TextCitation): string | null {
  const block = document.blocks.find((item) => item.id === citation.block_id);
  if (!block) return null;
  if ("content" in block && !citation.list_item_id) return plainRuns(block.content);
  if ("items" in block && citation.list_item_id) return plainRuns(block.items.find((item) => item.id === citation.list_item_id)?.content || []);
  return null;
}

function rebaseCitations(draft: TextDraft, document: TextDocument): TextDraft {
  const invalidatedCitationIds: string[] = [];
  const citations = draft.payload.document.citations.flatMap((citation) => {
    const before = targetText(draft.payload.document, citation);
    const after = targetText(document, citation);
    const selected = before == null ? "" : Array.from(before).slice(citation.start, citation.end).join("");
    if (!selected || after == null) { invalidatedCitationIds.push(citation.id); return []; }
    const matches: number[] = [];
    const afterPoints = Array.from(after);
    for (let start = 0; start <= afterPoints.length - Array.from(selected).length; start += 1) {
      if (afterPoints.slice(start, start + Array.from(selected).length).join("") === selected) matches.push(start);
    }
    if (matches.length !== 1) { invalidatedCitationIds.push(citation.id); return []; }
    return [{ ...citation, start: matches[0], end: matches[0] + Array.from(selected).length }];
  });
  const byId = new Map(citations.map((item) => [item.id, item]));
  const evidenceRefs = draft.evidenceRefs.filter((ref) => !invalidatedCitationIds.includes(String(ref.locator.citation_id))).map((ref) => {
    const citation = byId.get(String(ref.locator.citation_id));
    if (!citation) return ref;
    return { ...ref, locator: { ...ref.locator, block_id: citation.block_id, ...(citation.list_item_id ? { list_item_id: citation.list_item_id } : {}), start: citation.start, end: citation.end, selected_text_hash: citation.selected_text_hash } };
  });
  return { ...draft, payload: { ...draft.payload, document: { ...document, citations } }, evidenceRefs, invalidatedCitationIds: [...draft.invalidatedCitationIds, ...invalidatedCitationIds] };
}

export function updateTextDocument(draft: TextDraft, document: TextDocument): TextDraft { return rebaseCitations(draft, document); }

export function replaceBlockRuns(draft: TextDraft, blockId: string, runs: TextRun[], listItemId?: string): TextDraft {
  const blocks = draft.payload.document.blocks.map((block): TextBlock => {
    if (block.id !== blockId) return block;
    if ("content" in block && !listItemId) return { ...block, content: runs };
    if ("items" in block && listItemId) return { ...block, items: block.items.map((item) => item.id === listItemId ? { ...item, content: runs } : item) };
    throw new Error("Text selection target is not editable");
  });
  if (!blocks.some((block) => block.id === blockId)) throw new Error("Text block not found");
  return rebaseCitations(draft, { ...draft.payload.document, blocks });
}

export function appendBlock(draft: TextDraft, kind: "heading" | "paragraph" | "quote" | "bullet_list" | "ordered_list" | "callout" | "code" | "divider"): TextDraft {
  const id = crypto.randomUUID();
  const block: TextBlock = kind === "heading" ? { id, type: kind, level: 2, content: [] } : kind === "callout" ? { id, type: kind, tone: "info", content: [] } : kind === "code" ? { id, type: kind, code: "", language: "" } : kind === "divider" ? { id, type: kind } : kind === "bullet_list" || kind === "ordered_list" ? { id, type: kind, items: [{ id: crypto.randomUUID(), content: [] }] } : { id, type: kind, content: [] };
  return { ...draft, payload: { ...draft.payload, document: { ...draft.payload.document, blocks: [...draft.payload.document.blocks, block] } } };
}

export function removeBlock(draft: TextDraft, blockId: string): TextDraft {
  const removed = draft.payload.document.blocks.find((block) => block.id === blockId);
  const blocks = draft.payload.document.blocks.filter((block) => block.id !== blockId);
  const rebased = rebaseCitations(draft, { ...draft.payload.document, blocks });
  if (!removed || (removed.type !== "image" && removed.type !== "chart")) return rebased;
  return { ...rebased, assetRefs: rebased.assetRefs.filter((ref) => ref.material_revision_id !== removed.material_revision_id || blocks.some((block) => (block.type === "image" || block.type === "chart") && block.material_revision_id === ref.material_revision_id)) };
}

export function insertAsset(draft: TextDraft, asset: { material_revision_id: number; kind: string | null; content_hash: string; public_use_allowed: boolean | null }, role: "inline" | "cover" = "inline"): TextDraft {
  if ((asset.kind !== "image" && asset.kind !== "chart") || asset.public_use_allowed !== true) throw new Error("Asset kind or public-use rights unavailable");
  if (role === "cover" && asset.kind !== "image") throw new Error("Cover requires an image");
  if (!Number.isSafeInteger(asset.material_revision_id) || asset.material_revision_id <= 0 || !/^[0-9a-f]{64}$/.test(asset.content_hash)) throw new Error("Invalid exact asset revision");
  const current = draft.assetRefs.find((ref) => ref.material_revision_id === asset.material_revision_id);
  if (current && current.content_hash !== asset.content_hash) throw new Error("Asset revision hash changed");
  const assetRefs = current ? draft.assetRefs : [...draft.assetRefs, { material_revision_id: asset.material_revision_id, content_hash: asset.content_hash, role, sort_order: draft.assetRefs.length }];
  const hasCoverBlock = role === "cover" && draft.payload.document.blocks.some((block) => block.type === "image" && block.material_revision_id === asset.material_revision_id);
  return {
    ...draft,
    payload: { ...draft.payload, document: { ...draft.payload.document, blocks: hasCoverBlock ? draft.payload.document.blocks : [...draft.payload.document.blocks, { id: crypto.randomUUID(), type: asset.kind, material_revision_id: asset.material_revision_id }] } },
    assetRefs: role === "cover" ? assetRefs.map((ref, index) => ({ ...ref, ...(ref.material_revision_id === asset.material_revision_id ? { role: "cover" } : ref.role === "cover" ? { role: "inline" } : {}), sort_order: index })) : assetRefs,
  };
}

export type TextSelection = { blockId: string; listItemId?: string; start: number; end: number; text: string };
export function bindCitation(draft: TextDraft, selection: TextSelection, evidence: { item_id: number; snapshot_checksum: string; public_use_allowed: boolean }, selectedTextHash: string): TextDraft {
  if (evidence.public_use_allowed !== true || !/^[0-9a-f]{64}$/.test(evidence.snapshot_checksum)) throw new Error("Evidence rights or snapshot unavailable");
  const locator = { block_id: selection.blockId, ...(selection.listItemId ? { list_item_id: selection.listItemId } : {}), start: selection.start, end: selection.end };
  const actual = targetText(draft.payload.document, { id: "", fact_pack_item_id: evidence.item_id, selected_text_hash: selectedTextHash, ...locator });
  if (!actual || Array.from(actual).slice(selection.start, selection.end).join("") !== selection.text || !selection.text || !/^[0-9a-f]{64}$/.test(selectedTextHash)) throw new Error("Selected text is stale");
  const id = crypto.randomUUID();
  const citation: TextCitation = { id, ...locator, fact_pack_item_id: evidence.item_id, selected_text_hash: selectedTextHash };
  const ref: EvidenceRef = { fact_pack_item_id: evidence.item_id, snapshot_checksum: evidence.snapshot_checksum, role: "claim", sort_order: draft.evidenceRefs.length, locator: { citation_id: id, ...locator, selected_text_hash: selectedTextHash } };
  return { ...draft, payload: { ...draft.payload, document: { ...draft.payload.document, citations: [...draft.payload.document.citations, citation] } }, evidenceRefs: [...draft.evidenceRefs, ref] };
}

export function unbindCitation(draft: TextDraft, citationId: string): TextDraft {
  return { ...draft, payload: { ...draft.payload, document: { ...draft.payload.document, citations: draft.payload.document.citations.filter((row) => row.id !== citationId) } }, evidenceRefs: draft.evidenceRefs.filter((row) => row.locator.citation_id !== citationId) };
}
