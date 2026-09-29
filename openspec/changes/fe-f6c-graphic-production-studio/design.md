## Context

F6A already persists Graphic Masters and verifies one `render_output` MaterialRevision per canvas with a render-input hash, but the normal UI is a raw JSON textarea and the adapter only validates stable canvas IDs. F6B established schema-specific adapters and a Text-only lazy editor. The source F6C package predates the completed F6B commit, has no OpenSpec scenarios, and assumes capability hooks that F7 has not yet verified.

## Goals / Non-Goals

**Goals:** A bounded `graphic.master.v2` document, professional multi-canvas editor, exact layer/media/evidence lineage, input-bound real final renders, Graphic checks/diff, preserved v1 history, schema-aware Review/local package and measured route isolation.

**Non-Goals:** Full Figma/Photoshop runtime, unverified AI image/search/renderer or publisher claims, implicit v1 reinterpretation, new business table, channel reclassification, F6D–F8 implementation in this change.

## Decisions

1. **One v2 content truth.** A server-canonicalized payload contains title, ordered canvases and stable-ID layers. A duplicated canvas may record an optional `variant_of_canvas_id` pointing to an existing canvas in the same document; the variant is still independently versioned content, not a second entity or an implicit channel adaptation. Geometry is finite/bounded, dimensions are positive and capped, text runs/styles use a closed token set, and infrastructure URLs/paths/bytes are forbidden. Candidate content includes all visible text and geometry. The frontend may use a canvas UI library, but its editor state is not the persistent business schema. Alternative—persist arbitrary browser canvas JSON—would make rendering and review non-deterministic.

   Existing API callers that omit `payload_schema` continue to create Graphic v1 for compatibility; the new Graphic Studio explicitly submits `graphic.master.v2`. This is a new-editor default, not a reinterpretation of old writes.

2. **Keep F6A revision/ref/check storage.** A media layer points to an exact MaterialRevision and a matching `ContentMasterAssetRef` whose `slot_key` is the stable layer ID and placement identifies canvas/layer. Reusing one revision in multiple layers creates distinct refs, not copied bytes. A claim on a text layer uses `ContentMasterEvidenceRef.content_locator_json` with canvas/layer/range plus FactPackItem checksum. Save validates payload and refs atomically. Alternative—new GraphicAsset table—would split rights and historical lineage.

3. **Explicit v1 upgrade.** The generic save remains schema-stable. A dedicated preview and CAS-protected fork converts only provable v1 canvas/layer fields; unsupported material/text semantics become warnings or a blocked upgrade, never invented content. Old v1 Masters/Candidates remain unchanged. This follows the Text v1→v2 boundary.

4. **Exact profile and render.** An image-classified published channel/content-form profile supplies dimension/card limits when present; unsupported or legacy text-classified forms are unavailable for direct Graphic freeze (F6E owns future adaptation). Use F6A `render_asset_ref` plus manual attestation until a renderer capability is independently verified. One real image MaterialRevision per canvas is required, in canvas order, with unique canvas IDs, exact hashes/MIME/bytes/live rights and the canonical render-input hash. Changing any content/ref/context invalidates the binding. Alternative—treating any image as final—would permit an old render on new text.

   Profile rules live in the exact published form's optional `graphic_requirements`: `min_canvases`, `max_canvases`, `allowed_dimensions` pairs, `cover_required` and non-mutating `presets`. A canvas may declare `role=cover|body`; if `cover_required=true`, the first canvas must explicitly be `cover`. Missing optional rules impose no invented size or card limit. Unknown/invalid profile rules fail closed as unavailable, and `presets` are suggestions rather than silent payload rewrites.

5. **Checks and review are schema-dispatched.** `graphic_structure`, text/fact/identity coverage and exact `graphic_platform` write append-only `ContentMasterCheckRun`. Deterministic checks only attest deterministic facts; missing semantic provider is reported as unavailable/partial, not pass. Diff compares stable IDs, order, geometry, text, refs, evidence and render. Review/local package use the frozen Candidate v4 snapshot; whole-graphic text similarity is not manufactured.

6. **Provider hooks are honest.** F6C exposes project-scoped capability state and fails closed while no provider is verified. Existing project-visible uploaded/library MaterialRevision references remain available through their exact rights gates. F6C does not materialize an external provider result or infer public/commercial rights from provider success. F7 owns verified search/image provider execution, accepted-result MaterialRevision creation, source/provider/version/prompt/hash/license metadata, explicit Project attachment and negative provenance/rights tests. This maps former F6C tasks 5.4–5.7 to F7 material-search tasks 4.3–4.8 and image-provider tasks 5.3–5.9, plus the mandatory F7 provider-response redaction task below; these requirements are not declared implemented by F6C. Existing generic Material APIs are not proof of project capability.

   **F7 provider-response redaction handoff.** When normalizing the F7 source package into its active OpenSpec change, add a dedicated requirement and negative test task: provider execution/result responses, errors and provenance metadata MUST NOT serialize API keys, tokens, cookies, credential-bearing URLs, raw provider configuration or secret headers. F7 source tasks 1.4 (persistence) and 9.6 (Settings) do not cover these execution surfaces. F7 implementation MUST remain incomplete until this new task and its negative tests pass.

7. **UI isolation.** Graphic-only lazy chunks own canvas/list/layer editing, asset selection, readiness and history. Common Production/Workflow state stays independent; Text TipTap and Video shell are not imported by Graphic. Saving Master is explicit and append-only, with 409 conflict handling and archived/history read-only behavior.

## Risks / Trade-offs

- **Manual final render may not match the canvas visually.** Input-hash binding proves the editor confirmed exact bytes for exact inputs, not that a renderer independently generated them. Review must label `origin=manual`; verified renderer claims wait for F7.
- **Current generic Material generation may mark rights allowed automatically.** F6C project flow must not infer public rights from provider success; rights remain a separate live gate and a scoped generated revision needs explicit rights provenance.
- **Legacy Xiaohongshu `image_note` is registered as text.** F6C cannot silently reinterpret it as image; use an exact image profile for Graphic acceptance and leave cross-channel adaptation to F6E.
- **Provider/semantic services can be absent.** Structure/editing and local manual-render flow still work; absent features remain visibly unavailable rather than simulated.
- **Large multi-canvas payloads could harm performance.** Bound canvas/layer counts and text/geometry, keep graphic editor route-lazy, and measure FE-P1 budgets.

## Migration Plan

No new table or migration is planned. Existing `ContentMasterRevision`, refs, checks and Candidate v4 store v2 state. Historical v1 rows are never backfilled. An isolated database is used for tests and browser acceptance; no production migration/deploy or remote publication is part of this change. If an unavoidable durable schema addition appears, amend the OpenSpec before implementing it.

## Open Questions

No product-scope decision is required to begin: unavailable external capabilities stay unavailable and F6E handles cross-channel variants. Exact provider-specific licensing/verification and remote Publisher support remain F7 decisions and cannot be claimed by F6C acceptance.
