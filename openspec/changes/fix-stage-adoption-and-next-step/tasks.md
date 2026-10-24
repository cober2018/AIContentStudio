## 1. Adoption check

- [x] 1.1 Add `adoption_basis` in `creation_recipes`. It drops the shared materials, the model's per-process fingerprint, and the derived prompt and context hashes.
- [x] 1.2 Use it in `creative_method_stage.accept`, `stage_master_adoptions` (both checks) and `stage_domain_adoptions`. Keep the `expected_context_hash` check against the frozen hash.
- [x] 1.3 Creative attempts: check that the material ids the candidate cites are still live; refuse with a named code otherwise.
- [x] 1.4 Error details name what changed (materials cited, upstream, master, settings, model) so the web can explain it.
- [x] 1.5 Verify on a DB copy that attempt 328 (U80 shots) is accepted, and that a changed upstream is still refused. Update pinned tests if any assert the old behaviour.

## 2. Next-step card

- [x] 2.1 Derive the next step from the loaded stage list (plus shot-slot counts for video).
- [x] 2.2 Show the stages as sub-steps in the left navigation (replaced the first-built top card at the user's request).
- [x] 2.3 Check in the browser on U80.

## 3. Plain-language errors

- [x] 3.1 Add the stage error text and action map; use it where stage actions show errors.
- [x] 3.2 Build passes; related API tests pass.

## 4. Docs

- [x] 4.1 Update this change's README, task_plan, progress and findings, and the root README entry.

## 5. Unknown attempts (added 2026-10-22)

- [x] 5.1 Classify provider failures (answered vs in flight); record reason and HTTP status in the receipt and LLM run.
- [x] 5.2 `abandon-unknown` route and service; `_prior_unresolved` ignores abandoned attempts.
- [x] 5.3 Web: 放弃这次结果 on unknown stages, with confirm; plain texts for the new codes.
- [x] 5.4 Verify on a DB copy with U80 attempt 330; tests; browser check without clicking.
