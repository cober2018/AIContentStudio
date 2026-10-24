## Why

Adding a material today copies its bytes into the platform media folder (`apps/api/app/media/material/xx/<hash>`). The user keeps footage, photos and music on an external drive and wants the platform to use those files where they are: link, never copy. Large footage duplicated onto the Mac disk wastes space and splits one file into two truths.

## What Changes

- **Material source folder.** The user registers a folder (for example `/Volumes/<drive>/素材`) as a named source. The platform records its absolute path and the volume identity, and shows whether it is available now (drive plugged in, readable).
- **Scan.** The platform lists the files under the folder (bounded, recursive, media types only) with size, type, modified time and whether each is already linked.
- **Link files one by one.** For each chosen file the user (or the agent on their instruction) sets kind, source, attribution and rights, as with upload. The platform reads the file once to compute its fingerprint, probes images/video/audio as upload does, and creates a normal Material + MaterialRevision whose bytes stay on the drive. Nothing is copied.
- **Availability and change detection.** Every read of a linked file checks that the drive is present and the file is unchanged (size and modified time, then fingerprint when either differs). Missing → `material_external_unavailable`; changed → `material_external_changed`. Work that needs the file is blocked with that reason, never silently substituted.
- **New version on change.** Linking the same file again after it changed creates a new revision of the same material (parent = previous revision), with the user's confirmation. Old revisions keep their recorded fingerprint and stay unusable until the original bytes return.
- **Edit execution inputs link to the drive.** For linked materials, `materialize_inputs` places a symbolic link in `inputs/` pointing at the drive file, instead of the copy-on-write clone (cloning cannot cross volumes and would otherwise fall back to copying). The fingerprint is re-checked at materialize and again before an output is submitted.
- **Never deleted by the platform.** Retention and cleanup never touch files in a source folder.
- Existing library materials, uploads, rights rules and public-use gates are unchanged.

## Capabilities

### Modified Capabilities

- `material-library-v1`: materials may live in user-registered external folders, linked in place.

## Impact

- New table `material_source` (owner, label, root path, volume identity, created) with an Alembic migration; linked revisions use `file_path` = `external/<source_id>/<relative path>` and keep size/mtime in `metadata_json`.
- `material_storage.py` resolves `external/` keys through the source root with path-escape checks; `materials.py` link flow; new router endpoints under `/api/v1/material-sources`.
- `creative_media_stream.py` / `creative_executions.py`: symlink inputs for external revisions; checks before submit.
- `retention.py`: skip `external/` keys.
- API/CLI/MCP only in this change; no web UI.
