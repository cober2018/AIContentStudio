## 1. Data and storage

- [x] 1.1 `material_source` model + Alembic migration.
- [x] 1.2 Storage: resolve `external/` keys through the source root; escape checks; availability and change checks; streaming hash.
- [x] 1.3 Retention skips `external/` keys.

## 2. API

- [x] 2.1 `POST/GET /api/v1/material-sources` (register, list with availability).
- [x] 2.2 `GET /api/v1/material-sources/{id}/files` (bounded scan; linked status).
- [x] 2.3 `POST /api/v1/material-sources/{id}/links` (link one file with kind, source, attribution, rights, inspect; relink creates a new revision).
- [x] 2.4 Readers return `material_external_unavailable` / `material_external_changed`.

## 3. Execution inputs

- [x] 3.1 `materialize_inputs` creates read-only symlinks for external revisions and records the mode in the audit.
- [x] 3.2 Fingerprint check at materialize and before output submit.

## 4. Verify

- [x] 4.1 Disk image as a fake drive: register, scan, link a video and an image, project reference, preview stage catalog lists them.
- [x] 4.2 Detach the image → unavailable; reattach → available; modify a file → changed; relink → new revision.
- [x] 4.3 Edit execution: inputs are symlinks, no bytes copied; submit blocked after a change.
- [x] 4.4 Full API test suite against the known 7 unrelated failures; restart API after confirming nothing is running.

## 5. Records

- [x] 5.1 README, findings, progress; update `video-material-scout` registration section.

## Verification record (2026-10-21)

- DB copy + real drive T1000 (APFS, USB), test files in a temporary subfolder, removed afterwards.
- Register: volume UUID recorded; duplicate folder 409. Scan lists media with linked status.
- Link: video (probe 640×360, 2000 ms) and image; no bytes in the media folder; `../`, symlinked files and wrong kind rejected; same file twice 409.
- Change: image edited → read `material_external_changed`; relink → revision 2 with parent; unchanged relink 409.
- Unplug (folder renamed): source `unavailable`, reads/scans `material_external_unavailable`; restored → readable. Different volume UUID → `different_volume` / `material_external_volume_changed`.
- Execution: `inputs/<rev>-<hash>.mp4` is a symlink to the drive file; manifest accepts only the recorded link; changed drive file → `execution_input_hash_changed`.
- Project reference → script stage catalog includes the linked video (19 items).
- Tests: 2,789 passed, same 7 known unrelated failures.
- Live: DB backed up, migrated to `extmaterial0001` (runtime schema head updated), API restarted with nothing running; folder `/Volumes/T1000/自媒体素材` registered as source 1 (available, empty).
