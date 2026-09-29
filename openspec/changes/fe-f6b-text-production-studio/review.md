# FE-F6B SPEC review — 2026-09-29

## Scope and baseline

- Actual workspace: AIContentStudio, local main@ca52aa5 (F6A canonical + archived).
- Source: openspec/fe-f6b-text-production-studio and its user-supplied ZIP; original eight files preserved byte-for-byte. ZIP SHA-256: 28554d11bc3a79e538ef10db5fa4ee0f9cfef8b3919a0beafa5c9a3938846095.
- Only specification normalization and review are authorized. Implementation remains 0/162. No business/test code, new DB table, migration, canonical sync, archive, commit, push or deployment.
- Three existing canonical specs were fully read. The fourth capability, text-production-studio, is intentionally new and has no canonical spec yet.

## Required corrections incorporated

| Finding | Normalized contract |
| --- | --- |
| MODIFIED fragments would replace and lose existing scenarios/constraints | Restore full canonical requirement blocks before adding F6B. Only legacy seed default-schema wording changes intentionally. |
| document-first legacy conversion could substitute non-authoritative content | Markdown/body stays authoritative; composition text must prove equivalence or become explicit mismatch/loss warning. Upgrade is explicit and current-parent/context CAS protected. |
| Citation offsets ambiguous across Python/JS/ProseMirror; valid old ranges can cite changed claims | Unicode scalar/code-point offsets, list-item paths, selected-text hash, repeated uses and atomic binding invalidation/rebind. |
| Successful LLMRun proves an issued suggestion, not its application | Server validates/applies once to derive before/after/patch hashes; save checks final hash or continuous hash chain; verified_output_match is distinguished from issued/subsequently_modified. |
| LLMRun retention clears parsed output | Uncommitted cleared receipts cannot verify; successful save freezes compact service-verified receipts in existing edit_summary JSON. |
| warning disposition before Freeze conflicts with F6A Approval | Freeze accepts current pass/warning; exact dispositions stay at Approval, with no new pre-freeze state. |
| Wildcard discoverability lookup could claim exact profile coverage | Explicit published channel + content_form only for v2; retain legacy wildcard behavior separately. |
| Media Markdown and ZIP naming could diverge | Frozen ordered exact-ref media mapping established before freeze; package uses frozen render and fails closed on mismatch. |
| Text-only dependency wording conflicts with preserved legacy TipTap | Distinct Text/legacy lazy boundaries; common Production/Graphic/Video and existing budgets/XYFlow isolation preserved. |

## Actual implementation evidence read

- models.py: ContentMasterRevision payload/edit_summary, exact refs/locator JSON, ContentMasterCheckRun report/profile fields and LLMRun parsed output already support bounded storage; target zero migration is feasible, not yet implemented.
- production_modalities.py and persisted-schema callers: current lookup is modality-only and Text v1 renders Markdown. F6B must dispatch by persisted schema across save/readiness/checks/Candidate/live validation/Review/package, not reinterpret v1.
- document_composition.py: Draft document_json is composition; Markdown is its textual authority.
- generation/providers.py and routers/generate.py: existing rewrite route/provider and LLMRun recording can be reused, but F6B adds server-controlled Project/Unit/context/receipt metadata and actual route runtime provenance.
- factchecker.py: legacy semantic review truncates to 50 facts/4,000 characters and may fall back to deterministic results. v2 must expose exact coverage/provider/model-use omissions rather than declare complete semantic pass.
- discoverability.py: legacy profile resolution has empty-channel/nullable-form fallback; not exact F6B matching.
- project_review.py: warning disposition is checked in Approval; retention.py clears old LLMRun parsed/raw output.
- production_packages.py: content.md must equal frozen render; media file layout is generated from exact ordered refs. Review v4 currently assumes content.markdown and needs frozen-schema dispatch.
- ModalityWorkspace.tsx, TextStudioShell.tsx, ContentMasterPanel.tsx, components/editor.tsx and check-bundle.mjs: explicit modality lazy boundary exists; common-route budget is raw JS <500,000 with heavy dependency detection. ProseMirror positions are not business locators.
- Graph discovery tools were unavailable; only narrowly scoped text searches/source reads were used.

## Preservation audit

| Capability | Modified blocks | Old scenarios preserved verbatim | Whole canonical unchanged |
| --- | ---: | ---: | --- |
| production-content-master | 4 | 9 | yes: 19 requirements / 38 scenarios |
| fe-f4-project-review-distribution | 1 | 3 | yes: 11 requirements / 38 scenarios |
| fe-p1-frontend-bundle-performance | 2 | 4 | yes: 5 requirements / 10 scenarios |

All seven modified blocks retain sixteen old scenarios verbatim. The original package remains unchanged. Standard tasks still total 162 unchecked entries; corrections refine existing tasks instead of creating more slices.

## Review and verification status

- Initial independent SPEC/plan and frontend/Review/package reviews identified the source gaps above; backend review proposed the smaller receipt/retention design adopted here.
- Normalized change strict: PASS. Final all-spec/all-change strict: 25/25 PASS.
- Preservation audit: PASS; original eight source files and three canonical files unchanged.
- Tracked diff-check and all nine new artifact whitespace checks: PASS. No business-code diff.
- Independent normalized-package SPEC/plan: APPROVE (Confucius); backend contracts: APPROVE (Euler); frontend/Review/package/performance: APPROVE (Archimedes). These are specification approvals only, not apply authority or implementation acceptance.
- No build/backend/browser result is claimed for F6B; this is SPEC review, not implementation acceptance.

## Next authorization boundary

### Apply batch 1 — 2026-09-29

User separately authorized apply. Local main remains at ca52aa5 with uncommitted F6B foundation changes; source package, canonical specs and migrations remain unchanged. Completed tasks: 39/162. Exact-schema adapters, bounded Studio Document/canonical text maps, deterministic rendering, exact assets/citations and generic v2 append-only persistence are implemented. Legacy callers remain v1; schema crossing is rejected. Professional check handlers deliberately return incomplete and unverified AI receipts are rejected until their later tasks are implemented. Upgrade/seed/check/AI/diff/Review/frontend/browser milestones remain open.

Fresh batch gates: 835 backend tests passed, 2 opt-in PostgreSQL tests skipped, 6 existing warnings; 84 new targeted tests passed; relevant Ruff, all strict 25/25, whitespace and preservation of all sixteen pre-existing scenarios passed. The frontend build/budget was freshly run as the initial baseline, not as Text Studio acceptance. Euler approved only the backend foundation after renderer edge-case regressions; Confucius found no confirmed over-checking in the read scope, without claiming an independent execution-log or true parallel-race audit. This is not final F6B acceptance or archive readiness.

Default assumptions: preserve historical contracts, no new persistent structures, no automatic AI/identity/workflow mutation. No product-scope question is outstanding. Most common mistake here is treating a syntax-valid delta or issued AI suggestion as semantic proof. Final status SPEC_READY; the one separate decision is whether to authorize apply of this calibrated specification. Actual implementation/bundle sizes require future fresh verification, and any durable-schema expansion requires a stop and revised authorization.

## Implementation close — 2026-09-29

The preceding SPEC_READY and batch-1 text is historical, not the current implementation status. FE-F6B implementation and acceptance tasks are now 162/162. Independent SPEC/preservation and backend/Text-schema/check/AI-provenance reviews approved the completed work. Frontend/accessibility/performance review initially required active formatting state and correct keyboard semantics; the Text-only editor now exposes `aria-pressed` and visible active state in a labelled button group, with native Tab order. Focused browser verification and a second independent frontend review approved the repair.

Final gates: 913 backend passed, 2 PostgreSQL opt-in skipped, 5 warnings; targeted cross-modality 130 passed; frontend model 9/9; TypeScript/Vite and FE-P1 budgets passed; OpenSpec strict 25/25; changed Python Ruff and diff-check passed. `/projects` initial JS is 224.75 kB raw / 72.91 kB gzip; common Production 269.38/86.71; Text Studio lazy closure 596.13/186.92. No new table or migration. Browser acceptance was isolated to a temporary SQLite database; package ZIP bytes were inspected through the local API after the browser download event did not return. Real semantic provider and production publishing were not claimed. The change remains active; canonical sync/archive requires separate authorization. The local commit is reported in the handoff, not encoded as a self-referential hash in this file.
