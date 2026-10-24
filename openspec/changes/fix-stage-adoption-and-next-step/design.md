## Context

When a stage result is accepted, `creative_method_stage.accept`, `stage_master_adoptions` and `stage_domain_adoptions` re-resolve the stage and compare the result with what was frozen at generation. The comparison currently covers the whole resolution: `resolution_hash` vs `attempt.input_hash`, `current` vs `resolved["context"]`, and `expected_context_hash`. That resolution includes:

- `context.shared_asset_refs` and `shared_assets_coverage`: every active material reference in the project.
- `model.runtime_hash`: an HMAC keyed by a random secret created per API process.
- `prompt_hash` and `prompt_sections`: derived from the two above.

Verified on attempt 328 (U80 shots). With the runtime config loaded, the only differences between the frozen resolution and today's are `context.shared_asset_refs`, `model.runtime_hash`, and the hashes derived from them.

## Decisions

1. **Compare inputs, not derived hashes.** Add a helper in `creation_recipes`, for example `adoption_basis(resolved)`. It returns the resolution with these items removed:
   - `context.shared_asset_refs` and `context.shared_assets_coverage`;
   - `model.runtime_hash` and `model.status`;
   - `prompt_hash`, `prompt_sections`, `effective_prompt`, `context_hash` and `resolution_hash`.

   All three adoption paths compare `adoption_basis(frozen) == adoption_basis(current)` instead of comparing the hashes. Everything else stays in the comparison: upstream handoffs, boundary, master, asset_refs, evidence_refs, method, config, and the model's profile, provider, model and configuration revision.
2. **Cited materials must still be live.** If a candidate cites material revisions, each one must still be usable in the project: active, with model use allowed, and with an active project reference. The existing `_live_refs` check covers masters. Creative attempts reuse `selected_input`, which already checks every cited material revision (hash, status, model use, rights, bytes). Removing a material the result relies on still blocks, with a plain message.
3. **`expected_context_hash` from the client** is still checked against the frozen `resolved["context_hash"]`. That check confirms the user is accepting the result they saw. The comparison with the live state moves to decision 1.
4. **Provenance unchanged.** Stored `input_hash`, `context_hash` and `resolution_hash` keep their generation-time values, so the record still shows exactly what the AI saw.
5. **Next step lives in the left navigation, derived, not stored.** (Revised 2026-10-22 at the user's request: a separate card was a third place talking about steps, so the workflow stages became sub-steps of the planning step and the card was removed.) It is computed from the stage list the production page already loads (`stages`: node, status, accepted) and from the shot-slot counts for video. Rules, in order:
   - A stage is running: "AI 正在做 X".
   - A stage is `waiting_input`: "X 等你确认", with a button that opens that stage's candidates.
   - A stage is blocked: the reason in plain words, with the action that fixes it.
   - The next stage is pending and can start: "开始 X", with the button.
   - For video, shots that still need material: "还有 n 个镜头缺素材" (this does not block).
   - All stages are done: "去审阅与交付".

   The card sits at the top of the production page and stays in the same place.
6. **Plain-language errors.** Add a small map from stage error codes to text plus action in the web app, used wherever stage actions show errors. Unknown codes fall back to "操作没成功（code）", so the code is never hidden.

## Risks

- A result accepted after its project materials changed was generated without seeing the newer materials. That is acceptable: it cites only what it saw, and those citations are re-checked as live.
- The production page in the code (`ProductionWorkspace` steps vs the creation-recipe stage panel) has more than one notion of "step". The card follows the workflow stages, which are what actually gate the work, and links into whichever panel shows that stage.

## Unknown attempts (added 2026-10-22)

7. **Classify provider failures.** `generation.providers.provider_failure(exc)` follows the exception chain to the provider's `HTTPException` reason and the `X-Provider-Status` header, which `model_registration.provider_request` now sets on non-200 answers.
   - If the provider answered (rejected request, rejected credentials, bad encoding, invalid or unparseable body), the master-propose and creative-method stages raise `stage_provider_rejected`. That is finalized as failed with `confirmed_dispatched`, so a new attempt is allowed.
   - Anything else stays `stage_provider_failed`, which is possibly dispatched and therefore unknown.
   - The reason and status go into the attempt receipt as `provider_failure`, and into `LLMRun.error`.
8. **User abandons an unknown attempt.** `POST …/stages/{node}/abandon-unknown {run_id, attempt_id}` is for editors only, and only for the step's current unknown attempt.
   - It writes `receipt.abandoned = {by_user_id, at}`. The attempt status stays `unknown`, because that is still the truth.
   - It sets the step and run to failed with `stage_dispatch_abandoned`.
   - `_prior_unresolved` ignores abandoned attempts, so the next run is allowed.
   - The web shows the button only on an unknown stage, behind a confirm that names the possible extra call. After it, the page treats the abandon as the user's decision on that attempt, so no separate rerun feedback is sent.
