## Context

Evidence: `openspec/changes/improve-persona-content-methods/findings.md` (2026-10-21 entries) and execution 4 under `apps/api/app/media/.creative-executions/1/4/`. The Master timeline already stores per-cut MaterialRevision placements with trims on additional video tracks; only the downstream contracts ignore them.

## Goals / Non-Goals

**Goals:** record real multi-source edits exactly; stop duplicating media bytes per execution; let planning cite real material; keep Persona edit methods unless explicitly replaced; deliver a non-clipping mix at a normal loudness.

**Non-Goals:** new Master schema, new rights semantics, automatic acceptance, publishing, templating, replacing Resolve/AE.

## Decisions

1. **Multi-source manifest items.** A manifest timeline item for a shot is valid when its `material_revision_id` is the shot source OR a Master timeline media item placed inside that shot's span, and its trims lie within that placement's trims. Every shot still needs at least one item. Single-source manifests stay valid.
2. **Linked inputs (APFS clone, user-confirmed 2026-10-21).** `materialize_inputs` clones the content-addressed store file with `fclonefileat` to `inputs/{revision}-{hash}.{ext}` (extension from the verified MIME), sets it read-only and verifies the hash. A clone shares disk blocks like a link but is a separate inode, so the existing one-link safeguard stays and an executor write can never alter the library. Hard links/symlinks were rejected: same-user writes would reach the library's only copy. Without clone support it falls back to the bounded copy and an audit event records `copy` and the reason. Readback and the manifest validator accept both the extension name and legacy `.bin`. The project Skill tells executors to import from `inputs/` directly.
3. **Planning catalog.** For persona video units (product units unchanged), the stage context adds the project-referenced materials (image, video, audio) with kind, title, source kind, duration, and rights flags (`public_use`, `model_use`, `local_only`) into `reference_catalog`; only `model_use_allowed` materials are listed. Shot-plan `reference_index` validation keeps rejecting anything not in the catalog.
4. **Per-stage work override.** When freezing the edit package (`creative_packages`) and in its read view, work-level `production_stages` are merged per stage over the Persona stages for persona units (previously the Persona edit stages vanished when the work named only `script`; `frozen_stage` already fell back per stage).
5. **Loudness.** A deterministic audio step derives a mastered narration (EBU R128 two-pass loudnorm, default −16 LUFS integrated, −1.5 dBTP) as a new MaterialRevision with parent lineage and unchanged rights. Edit output validation measures integrated loudness and true peak of the rough/final MP4 and stores them; values above −1 dBTP or outside a configurable window raise a warning shown at human review, not an automatic rejection.

## Risks / Trade-offs

- Filesystems without clone support → recorded copy fallback.
- Mastered narration changes the timing source → derived file keeps exact duration; ASR alignment remains bound to the original revision and is reused.
