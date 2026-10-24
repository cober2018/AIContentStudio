# link-external-material-folders

- Stage: applied and verified 2026-10-21 (user chose: register a folder, scan, link files one by one; folder `/Volumes/T1000/自媒体素材`). Not committed or archived.
- Need: use materials where they live (external drive), link instead of copy.
- Code (main branch, uncommitted): `apps/api/app/services/material_external.py` (new), `material_storage.py`, `creative_media_stream.py`, `creative_execution_files.py`, `creative_executions.py`, `routers/materials.py`, `models.py` (`MaterialSource`), `alembic/versions/extmaterial0001_material_source.py`, `db.py` (schema head).
- API: `POST/GET /api/v1/material-sources`, `GET /material-sources/{id}/files?subpath=`, `POST /material-sources/{id}/links` (`material_id` for a new version of a changed file).
- Key decisions: key `external/<source>/<hash>/<relative path>`; size+mtime check on use, full hash on read/execution; drive identity by volume UUID; edit inputs are symlinks; platform never writes to the folder.
- Live state: source 1 registered (available, empty). Pre-migration backup deleted at user request.
- Next: user puts material in the folder → scan → link with rights → project reference. Commit/archive on request.
