## 1. Built-in stage Skills

- [x] 1.1 Add `studio.video.script@3` (SKILL.md + contract) with the script ↔ material loop and request vocabulary; register in the catalog and trial keys.
- [x] 1.2 Add `studio.video.shot-director@3` with multi-source shots, pacing, crop notes and catalog references.
- [x] 1.3 Existing catalog/validator checks pass; v1/v2 hashes unchanged.

## 2. Executor Skills

- [x] 2.1 Create `.codex/skills/video-material-scout/SKILL.md` (when/where/how, verification, rights, registration, return to script).
- [x] 2.2 Add `video-production-handoff` references: motion toolkit, edit combos, finishing rules; link from SKILL.md.
- [x] 2.3 Add the parameterized AE builder script and its spec format.

## 3. Capability Memory

- [x] 3.1 Save candidate revisions for picture pacing, captions, AE packaging and finish via the existing API; do not change Persona defaults.

## 4. Verification

- [x] 4.1 Preview a persona video script/shot stage with @3 on the verification unit and confirm the loaded method text and catalog.
- [x] 4.2 Rebuild one execution-5 composition from the builder spec to confirm the template reproduces it.
- [x] 4.3 Strict validate; update README, progress and findings.

## Verification record (2026-10-21)

| Item | Evidence |
|---|---|
| 1 | `studio.video.script@3` / `shot-director@3` load through the catalog; @2 unchanged; verification unit 74 previews show the new method text and an 18-item project material catalog (shot step waits for an accepted script, as designed; no model was called) |
| 2 | `.codex/skills/video-material-scout/SKILL.md`; `video-production-handoff` references `motion-toolkit.md`, `edit-combos.md`, `finishing.md` linked from SKILL.md |
| 2.3 / 4.2 | `scripts/ae_build.py` rebuilt all 15 execution-5 compositions from a data spec; frames for the six component shots match the delivered renders |
| 3 | Capability Memory revisions 45–48 (picture pacing, captions, AE packaging, finish); Persona snapshots still pin 16/18/20/22 |
| Checks | Full API suite 2789 passed; the same 7 failures in untouched areas (migration head name, model-selection config) |
