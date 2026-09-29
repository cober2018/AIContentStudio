## Why

F6A makes Graphic a first-class Content Master, but the current Graphic page is a raw JSON shell. The approved North Star requires professional multi-canvas graphic production in which visible text, exact media, final rendered bytes and approval share one traceable content lineage.

## What Changes

- Introduce `graphic.master.v2` with ordered, stable-ID canvases and text/image/chart/shape layers. Visible text and every layer placement become versioned Candidate content.
- Replace normal Graphic JSON editing with a bounded multi-canvas Studio while preserving historical `graphic.master.v1` and requiring an explicit append-only upgrade to edit it as v2.
- Bind embedded image/chart layers and every final canvas render to project-visible exact MaterialRevision refs; retain F6A input-bound manual attestation until a renderer is independently verified.
- Add schema-aware Graphic structure, text/identity and exact channel-profile checks, structured revision/Review diff, ordered local package and an honest unavailable state for unconfigured search/generation/renderer providers.
- Preserve ContentMasterRevision/AssetRef/EvidenceRef/CheckRun/Candidate v4 and target zero new tables or migrations. No remote publishing or full design-tool/NLE runtime is introduced.

## Capabilities

### New Capabilities

- `graphic-production-studio`: The graphic v2 document, exact layer/media/render contracts, editor, checks, history and local Candidate delivery.

### Modified Capabilities

- `production-content-master`: Graphic v2 schema dispatch, explicit v1→v2 fork, input-bound multi-canvas rendering and checks without weakening v1/Text/Video history.
- `fe-f4-project-review-distribution`: Graphic Candidate Review and local package expose exact ordered final canvases and visible text changes before approval.
- `fe-p1-frontend-bundle-performance`: Professional Graphic editor remains lazy and does not enter common Production, Text, Video or other primary-route initial graphs.

## Impact

- Backend: modality adapter, bounded graphic document/check/diff services, existing Master/Review/package routes and project-visible MaterialRevision validation.
- Frontend: typed Graphic Studio mounted behind the existing Graphic-only lazy route; common Workflow and Content Master save states remain independent.
- Data: existing revision/ref/check tables; additive migration only if a separately reviewed contract proves it necessary. Existing Candidate v4 and channel registry remain authoritative.
- External capability: F6C defines safe hooks and unavailable behavior; real Search/Image/Renderer verification belongs to F7. A legacy channel form classified as text is not silently reclassified as Graphic.
