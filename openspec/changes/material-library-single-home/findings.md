# Findings

- Today: library folder `/Volumes/T1000/自媒体素材` is `material_source` id 1 (linked, read only). Other material bytes go to `MEDIA_ROOT` (`AI_STUDIO_MEDIA_ROOT` or `apps/api/app/media`), chosen in `material_storage.provider()`.
- `MEDIA_ROOT` is used by asset_media, materials, material_storage, material_previews, material_byte_lock, creative_execution_files, stage_candidate_previews, workflow_engine.
- Runtime settings already live in `system_settings` via `runtime_config`.
- The AI assistant float is `FormAssistancePanel.tsx` (fixed bottom right, z-70).
- Decision (user, 2026-10-23): all materials only in the library; editing later uses local proxies like 剪映; proxies are a separate change and use the standard project folder.
- Decision: platform writes only into `<素材库>/AIContentStudio/`, never into the user's folders; no fallback write when the drive is unplugged.
- Storage keys stay `material/xx/<hash>.ext`; only the physical home changes. This avoids touching the ~15 places that validate that key shape. Lookup order: local file if it already exists (old materials), else the library path.
- Library files are content-addressed (hash names) inside `AIContentStudio/<type>/`; human-readable naming is left to the edit-proxy change, which uses the standard project folder.
- MEDIA_ROOT is read at import time, so a local move needs an API restart; the page says so.
- Finder drop uses the existing `/materials/upload` (30MB limit). Large footage should be linked via the drive folder instead.
