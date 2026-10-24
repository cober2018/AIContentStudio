# Findings

- Attempt 328 (U80 shots). With the runtime config loaded, the frozen resolution and the current one differ only in `context.shared_asset_refs`, `model.runtime_hash` and the hashes derived from them.
- `shared_asset_refs` lists every active material reference of the project. Uploads into shot slots add references, so filling slots changed the context.
- `model.runtime_hash` is an HMAC keyed by `_PLAN_SIGNING_KEY = secrets.token_bytes(32)` in `model_capability_routing`. The key is new on every API process, so any restart made every waiting result unacceptable.
- Reproducing a stage resolution in a script needs `runtime_config.load_from_db(db)` first; without it the model resolves to mock.
- Decision: compare the inputs the result was based on, not the derived hashes; keep the recorded hashes as provenance.
- Creative attempts already re-check cited materials in `selected_input`; acceptance reuses it instead of adding a new check.
- The regenerate action on a stage is the existing 「再次生成（新尝试）」 button; error text points to it rather than adding a second button.
- The production page has two notions of step: the left-hand 5/6 steps and the workflow stages. The card follows the workflow stages and lands on `workstep=plan&stage=…`.
- Decision (user, 2026-10-22): one navigation for steps. Workflow stages are sub-steps of the planning step; no separate next-step card.
- Any exception from a stage's model call was treated as possibly dispatched, so even a definite provider error sealed the attempt as unknown. An unknown attempt blocked new attempts and feedback, and there was no action to clear it, so the stage was stuck for good.
- `provider_request` throws away the HTTP status; the reason string alone could not tell a 429 from a 500. The status is now carried in the `X-Provider-Status` header on the internal exception.
- The cause of U80 attempt 330 (2026-10-22 15:27 UTC) is not recoverable: `LLMRun` 516 recorded only `stage_provider_failed`. Future failures record the reason and status.
- Unrelated: `tests/test_models_plugins.py` has 2 failing tests that come from earlier uncommitted settings/runtime-config changes. Left for a separate fix.
- The page treats any running or unknown result as a request still in flight (`restoreStageRequest`). A given-up attempt must be excluded on the page as well as on the server.
