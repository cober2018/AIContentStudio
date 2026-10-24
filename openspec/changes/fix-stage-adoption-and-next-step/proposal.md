## Why

On U80 (project 41) the user filled all 15 shot slots and then clicked to accept the shot plan. The platform refused with `409 · stage_adoption_context_changed`. Two things had changed since the plan was generated:

1. **Project materials.** Every material uploaded into a shot slot is referenced by the project, and the project's shared materials are part of the frozen context. Filling the slots, which is how the plan gets carried out, therefore made the plan impossible to accept.
2. **Model fingerprint.** The model's `runtime_hash` is signed with a key that is regenerated each time the API process starts (`model_capability_routing._PLAN_SIGNING_KEY = secrets.token_bytes(32)`). Any API restart makes every result that is waiting for a decision impossible to accept, even though the model, its provider and its configuration revision are the same.

Both cases break the first design principle, "the platform fixes outcomes, not steps": the user cannot be forced to finish one step before adding material, and nothing the user did changed the plan's real inputs.

Separately, the user said that on the content-project production page they do not know what comes next and have to search the page. When an error happens they see only a code.

## What Changes

- A result waiting for the user's decision SHALL stay acceptable when only these have changed:
  - the project's shared materials, as long as the materials the result itself cites are still usable;
  - the model's per-process fingerprint, as long as the model is the same: same profile, provider, model and configuration revision.

  Changes that affect what the result was based on still require regenerating. These are upstream accepted results, the fact boundary, the current master, the method and stage settings, and a real model change.
- The production page's left navigation SHALL show the workflow stages as sub-steps of the planning step, each with a plain status, and the one needing the user highlighted; clicking goes straight there. (First built as a separate card; the user chose to merge it into the navigation and drop the card.)
- Stage errors on the production page SHALL be shown in plain words, each with the next action. For example, "生成这份结果后，前面采用的内容（比如脚本）变了，需要重新生成。请点本阶段的「再次生成（新尝试）」", instead of a bare code.

- Added 2026-10-22 after the director-draft stage on U80 hit a model failure and could not move on: a stage whose model call ended "unknown" had no way forward, since no new attempt or feedback is allowed while an attempt is unknown.
  - The user SHALL be able to give up an unknown attempt explicitly, after a warning that the earlier request may have reached the model. The stage can then be generated again. The platform still never resends by itself, and the attempt stays recorded as unknown.
  - Model-call failures where the provider clearly answered SHALL be recorded as failed, with the reason and HTTP status, and can be retried directly. Examples are a rejected request, rejected credentials, or an unusable response. Only failures where the request may still be in flight, such as a timeout or a dropped connection, are recorded as unknown.

## Impact

- API: `creative_method_stage.accept`, `stage_master_adoptions` and `stage_domain_adoptions`. The adoption checks compare the plan's real inputs rather than the full frozen resolution. `creation_recipes` adds a helper for that comparison. No migration.
- Web: production page (`ProductionContextHeader` / `ProductionWorkspace`) gets the next-step card; stage error display gets plain-language text.
- Recorded provenance does not change. `input_hash`, `context_hash` and `resolution_hash` stay as recorded at generation.
- Out of scope: reorganising the workflow stages themselves, changing what the AI produces, and MCP tools.
