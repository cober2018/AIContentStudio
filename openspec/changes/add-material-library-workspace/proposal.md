## Why

Material is central to every piece, but today it sits in a text list inside 素材与知识 next to documents and evidence. There are no thumbnails, no video preview, no way to browse by type, rights, source or drive folder, and the new drive-folder linking has no page. The user asked for a material library that "承接素材" (2026-10-21).

## What Changes

- A **素材库** page of its own in navigation (资料 group); 素材与知识 keeps documents, evidence and knowledge collections.
- **Visual grid** with thumbnails (images), poster frames and hover scrub (video), waveform strip (audio); list view for dense work.
- **Filters**: type, tag, rights (public/model use/commercial), source (upload, web, generated, drive folder, execution output), project, availability (drive connected or not).
- **Detail drawer**: preview, versions with lineage, rights and attribution, where it is used, linked file location, actions (attach to project, new version, archive).
- **Drive folders**: register a folder, browse its files, link with rights (UI over the existing `/material-sources` API).
- **Collections**: save a set of materials for a series or topic (reuses knowledge-collection style revision guard).
- Thumbnails and poster frames are generated once per revision and cached; nothing changes the original bytes.

## Capabilities

### Modified Capabilities

- `material-library-v1`: a browsable library workspace with previews, filters, detail and drive folders.

## Impact

- API: list endpoint with filters and pagination; thumbnail/poster endpoint (cached derivative, never a new revision); usage read model.
- Web: new `/materials` route (replacing the legacy page), navigation entry.
