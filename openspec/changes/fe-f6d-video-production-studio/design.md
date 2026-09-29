## Context

F6A provides immutable Video Masters, checks, input-bound final-render gating and Candidate v4, but new Video editing still uses the v1 JSON shell. F6B and F6C establish typed Studio editors while reusing the same Production Core. F6D extends that pattern to bounded video assembly. F6C independent acceptance remains a prerequisite for F6D business-code apply; this specification can be prepared without treating F6C as accepted.

## Goals / Non-Goals

**Goals:** A canonical `video.master.v2` document; exact media and evidence lineage; bounded script/shot/timeline/voice/subtitle/overlay editing; explicit derived child revisions; honest provider/render availability; Video-specific checks/diff/Review/local package; Video-only lazy frontend.

**Non-Goals:** Full NLE/effect graph, verified Video/TTS/ASR provider integration, automatic rendering without verified capability, remote publishing, new business tables, production migration or implicit rewrite of v1/Candidate history. Provider integration and accepted external result materialization belong to F7.

## Decisions

1. **One editable Video truth.** The canonical v2 payload has stable IDs for script blocks, shots, timeline tracks/items, subtitle cues and overlays; it includes bounded duration, placement, transition and voice/music/cover declarations. The frontend editor is an adapter to this contract, not a separate durable timeline schema. Reject unknown fields, unbounded sizes/durations, non-finite geometry and local/infrastructure paths. This keeps Candidate hashing deterministic. Alternative: persist an editor-specific project file; rejected because it creates a second content truth.

2. **Exact media per use.** Every video/image/audio/cover/final-render placement maps to an exact `ContentMasterAssetRef` and project-visible `MaterialRevision`, including repeated use of the same revision in different placements. Validate media kind, byte existence/hash and live public-use rights on save and at downstream gates. Asset search/selection does not duplicate bytes. Alternative: copy media into each Video revision; rejected because it loses immutable library lineage.

3. **Explicit v1 fork and derived operations.** A dedicated preview/commit converts only provable v1 structure into v2 and emits warnings for anything else. Generic save cannot cross schema. Long-to-short, aspect-ratio change and shot-regeneration are explicit append-only child Master revisions, bound to exact source revision/payload/context, expected head, idempotency key and recorded transformation intent. No provider completion mutates the current Master. Alternative: in-place edits; rejected because historical Candidate provenance would change.

4. **Bounded timeline, not an NLE.** Validate shot order and duration, track/item start/end/trim bounds, subtitle cue ordering and non-overlap, voice/audio/overlay placement and exact cover kind. Preview projects known local state and playable exact assets; it never asserts an unrendered composition is the final video. Alternative: arbitrary effect graph; deferred outside F6D.

5. **Provider and render honesty.** F6D exposes scoped Video/TTS/ASR capability descriptors and typed unavailable errors while no provider is verified. It does not materialize provider-shaped fake results. F7 must verify real outputs, persist accepted bytes as MaterialRevision with license/provenance and redact secrets from execution/result/error metadata before the Studio can reference them. F6A's verified-renderer or explicit manual input-bound attestation paths remain; manual is always labeled manual, not verified. Final render must be exact video bytes whose attested input hash covers payload, context, media set and relevant channel profile. A stale/wrong-kind/mismatched render blocks freeze.

6. **Schema-dispatched checks and delivery.** Add Video v2 structure/timeline/identity/exact-platform checks to `ContentMasterCheckRun`; absent semantic capability is unavailable/partial rather than PASS. Review/diff show script, shot, timeline, voice, subtitle, overlay and render changes by stable ID, without whole-video text similarity. Candidate v4 freezes exact Video content/render provenance. Approval/authorization/package reuse F6A live gates; the v2 package contains only the approved final video bytes and declared companions, with no Draft/v1 fallback. Existing v1/v2/v3/v4, Text and Graphic reads retain their prior behavior.

7. **Video-only frontend boundary.** Mount typed Video editor/runtime behind the existing Video lazy route. Common Production, Text and Graphic must not statically import it; the bundle gate checks this closure. Workflow and Master dirty/save stay independent; archived/historical Video is read-only; 409 CAS conflicts preserve unsaved local state. No durable autosave revision.

## Risks / Trade-offs

- [Manual final-render attestation is not independently verified composition] → Keep `origin=manual`, show this limitation in Studio/Review and never label it automatic rendering.
- [Source media may be revoked after save or Approval] → Revalidate live byte/hash/rights at freeze, approval, authorization and package rather than trusting saved UI state.
- [Provider hooks could be mistaken for executable integration] → Report configured/executable/verified separately; unverified calls fail closed and create no MaterialRevision.
- [v1 conversion may lack timeline or rights evidence] → Return explicit warnings or reject unprovable conversion; never invent values to make a Candidate ready.
- [Editor or media libraries could inflate initial JS] → Keep Video-only dynamic imports and enforce import-graph/bundle budgets.

## Migration Plan

No new database migration is planned. Add v2 support alongside v1, then backend checks/Review/package, then the Video-only editor, then isolated browser acceptance. If a new durable structure is necessary, stop before code and amend this change. Local rollback keeps historical v2 rows intact and restores previous UI/code; no production deployment or migration is authorized by this change.

## Open Questions

No F6D product decision is required to prepare this specification. Real provider verification, media licensing integration and remote publication remain F7 work; cross-channel adaptation remains F6E work. These unavailable capabilities must not be represented as F6D success.
