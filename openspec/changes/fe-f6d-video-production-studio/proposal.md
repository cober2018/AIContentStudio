## Why

F6A made Video a first-class Content Master, but its production page is still a raw `video.master.v1` JSON shell. The North Star needs a bounded, traceable video workflow from script and shots through final rendered bytes, Review and local delivery, without pretending to be a full NLE or a verified external generator.

## What Changes

- Introduce `video.master.v2` with stable script, shot, timeline, voice, subtitle, overlay and cover identities; normal Video editing uses a typed Studio instead of raw JSON.
- Preserve v1 and historical Candidates unchanged; editing v1 as v2 requires an explicit append-only fork.
- Bind every source and final media use to exact project-visible MaterialRevision placement, live bytes/hash/rights and input-bound render attestation.
- Add deterministic Video structure/timeline checks, coverage-honest identity/channel checks, structured Master/Review diff and an exact local video package.
- Make long-to-short, aspect-ratio and shot-regeneration operations explicit child revisions with provenance; no silent source mutation.
- Expose provider-neutral Video/TTS/ASR capability state and fail closed while unverified. F7 owns real provider execution and accepted-result MaterialRevision/rights/provenance verification; F6D neither fabricates generated video nor implicitly updates Master.
- Reuse existing ContentMasterRevision/AssetRef/EvidenceRef/CheckRun/Candidate v4/Review/Delivery objects. Target zero new tables and migrations; stop and revise the specification if a durable schema proves necessary.

## Capabilities

### New Capabilities

- `video-production-studio`: Video v2 structure, exact media/render lineage, bounded editor, checks, derived revisions and local Candidate delivery.

### Modified Capabilities

- `production-content-master`: Add schema-dispatched Video v2 and explicit v1 fork while preserving existing Text/Graphic/v1 history.
- `fe-f4-project-review-distribution`: Review and local package expose frozen script/shot/timeline/render provenance without fake whole-video text similarity or Draft fallback.
- `fe-p1-frontend-bundle-performance`: Video-only editor/runtime remains lazy and outside common Production, Text, Graphic and other primary-route initial graphs.

## Impact

- Backend: Video document/adapter/check/diff services plus existing Master, project asset, Review and package paths.
- Frontend: typed Video Studio behind the existing Video-only lazy route; Workflow and Content Master dirty/save states stay independent.
- Data: existing immutable revision/ref/check tables and Candidate v4 manifest; no planned migration.
- External capability: safe unavailable hooks only in F6D; provider verification, accepted media and remote publishing remain F7.
