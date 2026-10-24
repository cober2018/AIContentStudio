# Task plan — 素材库 + 按文案找素材

Covers two confirmed changes (2026-10-22): `add-material-library-workspace`, then `add-script-material-matching`.

/// A. 素材库
/// A1 Library list: material filters (source kind, model use, drive folder, collection), newest-first order, size/duration, drive availability — extend `system_library`.
/// A2 Preview derivatives: `material_previews` service (image thumb, video poster + 8-frame strip, audio waveform), cached by content hash under media `.derivatives/`; never a revision.
/// A3 Playback: path-limited signed stream session + Range stream for any active material revision.
/// A4 Collections: `material_collection` + `material_collection_item` (migration `matlib0001`), revision-guarded CRUD.
/// A5 Web `/materials` 素材库 page: grid/list, filters, card previews with hover scrub, detail drawer (preview, versions, rights, usage, attach to project, add to collection), drive folders tab, collections tab; nav entry; legacy page → `/legacy/materials`.
/// A6 Build, tests, screenshot review; README; tasks.md ticks.

/// B. 按文案找素材
/// B1 Open-library providers (Openverse, Pexels, Pixabay, NASA, Coverr) + Wikimedia adapter, license mapping, aspect/resolution filter, dedupe.
/// B2 `material_match_run` (migration `matmatch0001`).
/// B3 Planner (chat routing) → segments with role, constraints, queries.
/// B4 Own-library matcher (metadata + drive links, model-use rights).
/// B5 Text pre-filter + visual judge via `model_vision`; seen-picture rule.
/// B6 Background job: progress, cancel, resume; API.
/// B7 Accept → staging/acceptance → Material revision + optional project reference.
/// B8 Web 按文案找素材 tab + plan review; project entry.
/// B9 `video-material-scout` skill update; real run once keys exist; README.
