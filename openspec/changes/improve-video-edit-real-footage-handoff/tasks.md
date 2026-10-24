## 1. Edit manifest multi-source shots

- [x] 1.1 `validate_edit_manifest` accepts per-shot items whose material is the shot source or a Master timeline media placement within the shot span, with trims inside that placement; every shot still requires an item.
- [x] 1.2 Keep single-source manifests and execution 1/4 manifests valid; reject a cut material that is not placed in that shot.

## 2. Linked execution inputs

- [x] 2.1 `materialize_inputs` clones (APFS copy-on-write, user-confirmed) store files to `inputs/{revision}-{hash}.{ext}` read-only with hash verification; bounded copy fallback records the reason in an audit event.
- [x] 2.2 Manifest validator accepts the extension path and legacy `.bin`; project Skill text says to reference `inputs/` directly.

## 3. Planning stages see project material

- [x] 3.1 Video unit stage context lists project-referenced model-use materials (kind, title, source kind, duration, rights flags) in the reference catalog.
- [x] 3.2 Shot plans can cite them in `reference_index`; non-catalog references stay rejected.

## 4. Per-stage work override

- [x] 4.1 Work-level `production_stages` merge per stage over Persona stages for persona units; unnamed stages keep Persona methods.

## 5. Loudness

- [x] 5.1 Deterministic mastered-narration derivative (−16 LUFS / −1.5 dBTP defaults) with parent lineage and unchanged rights.
- [x] 5.2 Edit outputs record measured integrated loudness and true peak; out-of-window values are warnings at human review.

## 6. Verification

- [x] 6.1 Run existing related checks; replay U72 through prepare → link inputs → manifest validation without copies; confirm prior executions still read back.
- [x] 6.2 Update findings/progress and README; strict validate.

## Verification record (2026-10-21)

| Item | Live evidence |
|---|---|
| 1 | Execution 5 manifest: 20 cut items over 15 shots validated; a cut naming unplaced material is rejected; execution 4 legacy `.bin` single-source manifest still valid |
| 2 | Execution 5 inputs: 6 read-only clones with real extensions; audit `creative_execution.input_materialized` mode=clone ×6; AE/Resolve reopen from `inputs/` with 0 missing; no source copies in `work/` |
| 3 | Fresh persona video unit 74 script preview lists 17 project materials with local-only flags; first registrations without model use excluded |
| 4 | Unit 74 profile naming only `script`: effective view keeps the other nine Persona stages. The package-freeze line uses the same merge but was not exercised live with a script-only profile (U72's profile names all stages) |
| 5 | Narration 116 → mastered 122 (−16.4 LUFS / −1.5 dBTP, identical frames, parent lineage, rights unchanged); execution 5 rough cut measured on submit −14.35 LUFS / −1.37 dBTP, no warnings; execution 4 mix reads `loudness_below_window` |
| Checks | Full API suite 2781 passed; 7 failures in files this change does not touch (migration head name `unitlife000001` vs expected, model-selection config `model_selection_unavailable`); a pre-change baseline run was not taken |

Open outside this change: planning-stage preview on a work whose current Master is large exceeds the 128 KB resolved-stage bound (`stage_value_too_large`), independent of the material catalog.
