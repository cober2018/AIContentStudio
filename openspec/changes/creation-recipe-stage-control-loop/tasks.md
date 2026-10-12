> 2026-10-06 current status: 141/144 checked, 3 open. The controlled three-modality journey reached 140/144; separately authorized formal local enablement then closed 4.7 with paired SQLite/material backup, copied-DB rehearsal, explicit crs upgrade and read-only runtime verification. New permanent regressions/full backend remain user-deferred; canonical/archive/commit/push remain unexecuted. No real Provider or WeChat call this batch.

## 0. Baseline closeout before new feature work

- [x] 0.1 Re-read current workspace/HEAD/dirty ownership; preserve the current Creative Orchestration implementation and F8 owned files.
- [x] 0.2 Verify/inherit completed R1: formal schema/readiness default is `aco000000001`, `f8a` identity columns remain inert nullable ancestry and JWT/production identity is not activated; preserve the prior align task 15.7 final-review gate separately.
- [x] 0.3 Confirm the completed `LOCAL_APPROVED_SCHEMA_HEAD`, readiness tests, backup/restore and parity corrections remain present; do not repeat them, change APP_ENV/auth, re-migrate or roll back formal SQLite.
- [x] 0.4 Verify/reuse the four retained R2 regression files and 108 cases for CreativeExecution state/output/rights, MCP restrictions, Capability Memory scope/secrets/Installed Skills separation and ACO lifecycle; do not add duplicate tests or label inherited evidence as fresh execution.
- [x] 0.5 Run existing full backend, frontend build/FE-P1, OpenSpec strict and diff-check before new Creation Recipe behavior.
- [x] 0.6 Stop and revise if the design requires a second Recipe/Feedback truth table or hidden workflow self-modification.

## 1. Creation Recipe projection

- [x] 1.1 Define Creation Recipe as an API/UI projection of the existing effective Workflow ID/version/checksum and source scope.
- [x] 1.2 Add stage read model with node ID/kind/plugin/version/label, readiness, last attempt, accepted target, blockers, inherited-default diff and unsaved local state.
- [x] 1.3 Do not persist recipe status separately; derive from Workflow/Run/Attempt/ProjectEvent/accepted target truth.
- [x] 1.4 Production defaults to stage strip/list + current content editor; raw canvas moves behind Advanced without losing any existing graph action.
- [x] 1.5 Show current source scope: Series → Account → Persona default or Project override, exact revision and checksum.
- [x] 1.6 Add recipe version/diff/history projection without mutating old Workflow rows.

## 2. Stage Contract registry

- [x] 2.1 Extend PluginDescriptor with optional versioned Stage Contract metadata.
- [x] 2.2 Define bounded stage contract fields: schema/title/category/config schema/UI schema/tunable fields/input contract/output contract/method sources/preview/run-override/candidate/human-acceptance flags.
- [x] 2.3 Validate that every normal UI field maps to a declared tunable/executor-consumed field; reject unknown config.
- [x] 2.4 Legacy pinned plugin versions/definitions/reruns remain Advanced/compatibility and retain original validation/execution semantics; new Workflow definitions explicitly pin a distinct new plugin version and exact Stage Contract identity.
- [x] 2.5 Add stage contracts for checks/human nodes only through newly registered plugin versions explicitly selected in new definitions; prove registry registration does not retroactively activate old nodes.
- [x] 2.6 Add contract tests proving cosmetic/unconsumed config is rejected.

## 3. Effective Stage Resolver and prompt preview

- [x] 3.1 Implement pure server resolver for exact saved node + optional allowed override + current pinned context + explicit method/model selections + upstream outputs.
- [x] 3.2 Define canonical `ResolvedStageExecution`/hash binding exact Workflow/node/plugin/Stage Contract, overrides, context/upstream/method and applicable routing-plan/adapter/runtime identities.
- [x] 3.3 Resolve Capability Memory only by exact selected artifact revision; never silently choose conflicting scope results.
- [x] 3.4 Resolve Installed Skill only by exact installed descriptor/version and executable runtime; installed inventory alone is not execution proof.
- [x] 3.5 Resolve model profile/provider/model using existing model-capability routing and fail visibly when unavailable.
- [x] 3.6 Build layered effective prompt preview: base method, Identity, stage instruction, Brief, Creative Intent, evidence constraints, upstream output, task override.
- [x] 3.7 Bound/redact preview; no secrets/raw credential URLs/provider errors.
- [x] 3.8 Preview makes no model/provider/Agent/tool call.
- [x] 3.9 Explicit run/rerun requires preview expected_resolution_hash and invocation key; automatic successor uses recorded server-prepared resolution after acceptance with the same expected-hash gate; reject missing/drifted config/context/method/model/route/adapter/runtime identities before dispatch.
- [x] 3.10 Regress exact prompt/config/resolution identity, missing preview, same-label changed runtime and zero external calls on conflict.

## 4. Attempt execution receipt and migration

- [x] 4.1 Add one additive migration after `aco000000001` with nullable bounded `input_snapshot_json` and `execution_receipt_json` on `workflow_step_attempt`.
- [x] 4.2 Keep legacy attempt rows valid with null new fields and no backfill.
- [x] 4.3 Atomically claim the existing Step/Attempt with invocation key/fingerprint and freeze Workflow/node/plugin/contract/config/override/method/model/prompt/upstream/output-contract plus preview/route/adapter/runtime identities; commit that receipt before any external invocation.
- [x] 4.4 Freeze bounded input snapshot immutably at claim; only one outcome/output finalization is allowed and sealed history is never replaced on retry/rerun.
- [x] 4.5 Preserve failed/unknown/possible-dispatch receipt/input evidence and distinguish confirmed pre-dispatch failure from unresolved original invocation; no second invocation truth table.
- [x] 4.6 Add migration up/down/up on isolated copied SQLite; downgrade refuses only if new receipt data would be destroyed.
- [x] 4.7 Do not migrate formal SQLite until full feature acceptance and separate enablement authorization. Controlled feature acceptance and explicit 2026-10-06 enablement authorization received; paired backup/rehearsal/formal crs upgrade and historical-hash/readiness checks completed. User-deferred permanent/full-backend gates remain open separately.

## 5. Run-only stage overrides

- [x] 5.1 Add bounded run/rerun `stage_override` accepted only for declared tunable fields.
- [x] 5.2 Overrides cannot change plugin/version, dependencies, mappings outside contract, evidence/rights/human gates or side-effect classification.
- [x] 5.3 Show base config vs temporary override vs effective config before run.
- [x] 5.4 Stage rerun with override creates a new immutable attempt and does not overwrite prior attempt/config/output.
- [x] 5.5 Run-only override does not alter Project Workflow Override or scoped default.
- [x] 5.6 Serialize competing invocation claims; identical response-loss retries reuse/reconcile the original Attempt, different fingerprints conflict and possible-dispatch/unknown never auto-resubmits or creates a replacement invocation.

## 6. Project-native Master proposal stage

- [x] 6.1 Add `stage.master.propose@1` without changing legacy `builtin.generate`.
- [x] 6.2 Its Stage Contract exposes purpose/instruction/model/method/candidate count/length-creativity controls supported by actual executor.
- [x] 6.3 Resolve current Content Unit, optional current Master, pinned Identity/Brief/Fact Boundary/Creative Intent and declared upstream inputs.
- [x] 6.4 Model request uses exact Effective Stage Resolver output and records LLMRun/input hash/model/prompt receipt.
- [x] 6.5 Return 1–5 bounded `stage.master.proposal.v1` candidates with stable candidate IDs/hashes.
- [x] 6.6 Validate Text/Graphic/Video candidates with their existing canonical Master adapters; reject invented foreign refs.
- [x] 6.7 Node execution never saves a Master.
- [x] 6.8 Browser/API prove changing stage instruction/model/candidate count changes the actual resolved request/receipt, not UI only.

## 7. Stage result review and Master adoption

- [x] 7.1 Add Stage Result Review UI; separate successful generation from required acceptance, resolve only exact accepted entity/hash/decision; after acceptance commits automatically continue eligible stages until required review/blocker, without auto-adoption/unsafe side effects or duplicate invocation on replay.
- [x] 7.2 Adoption requires exact Run/StepAttempt/attempt output hash/candidate ID/candidate hash.
- [x] 7.3 Recheck exact current Unit/Run/Attempt, expected Master revision and relevant context-head CAS at commit; stale adoption offers rerun/rebase, never silent retarget.
- [x] 7.4 Add trusted transaction-owned `workflow_stage` save/adoption: validate final payload/refs through existing adapters and commit Master/refs, mandatory output association and acceptance feedback atomically; failures leave no partial writes and standalone save semantics remain unchanged.
- [x] 7.5 Freeze Workflow/run/node/attempt/config/prompt/resolution/proposal/model/method provenance in Master edit summary/source provenance.
- [x] 7.6 Accepted-with-edits records proposal hash and accepted Master hash plus bounded edit summary.
- [x] 7.7 Require an adoption-specific ProjectWorkflowOutput association that proves original proposal/receipt plus accepted Master provenance/decision; never retrofit a later Master ID into immutable Step/Attempt output or relax legacy association proofs.
- [x] 7.8 No adoption freezes Candidate, approves content or changes Delivery.
- [x] 7.9 Regress unchanged historical proposal/output/hash/receipt plus atomic rollback and acceptance-with-edits downstream stale; adoption key binds proposal/final payload/refs/decision/expected heads, identical committed replay returns original result/output/feedback before new-currentness checks and conflicting/concurrent retries cannot duplicate adoption.

## 8. Native media stage integration

- [x] 8.1 Expose ProviderGenerationTask-backed media through a distinct new stage-capable plugin version explicitly pinned in new definitions; original media.generate versions/reruns retain their exact F7 semantics.
- [x] 8.2 Stage controls map exactly to ProviderGenerationTask capability/profile/prompt/parameters and are revalidated server-side; required media Stage input/config/provenance/receipt freezes before dispatch under the common invocation claim contract, not an optional display projection.
- [x] 8.3 Result panel shows the existing generation task and explicit MaterialRevision acceptance; no duplicate media task/result table.
- [x] 8.4 Accepted material is not automatically bound into Master.
- [x] 8.5 Stage feedback can record exact chosen/rejected MaterialRevision/task result.
- [x] 8.6 Prove image, video and TTS stage controls use exact provider task inputs and Unknown/no-auto-retry remains unchanged.

## 9. Channel Variant stage integration

- [x] 9.1 Add stage wrapper over existing F6E target/profile/adapter preview/model-assist/save contract.
- [x] 9.2 Stage config includes exact target channel/form and supported adaptation instruction/method/model fields.
- [x] 9.3 Result review uses existing Variant payload diff/checks and explicit append-only save; Stage-owned adoption commits accepted revision/refs, exact output association and feedback atomically with CAS/idempotency while standalone F6E save remains unchanged.
- [x] 9.4 Changing one Variant stage never mutates source Master/sibling variants.
- [x] 9.5 Preserve existing F6E deterministic/model provenance and 409/currentness behavior.
- [x] 9.6 No generic workflow node may invent a ChannelVariantRevision outside F6E service.

## 10. Professional execution stage integration

- [x] 10.1 Add a stage surface that prepares current `CreativeExecutionPackage` / `director.video.v1` and optionally a prepared CreativeExecution.
- [x] 10.2 Stage never auto-dispatches professional tools; MCP/Agent claim/start remains explicit.
- [x] 10.3 Stage projects CreativeExecution progress/blocker/unknown/result_ready/accepted without copying state.
- [x] 10.4 Accepted external MaterialRevision still requires explicit Master/Variant incorporation.
- [x] 10.5 Checkpoint/recovery and derived-rights gates remain unchanged.
- [x] 10.6 Browser prove video Script/Director stage → prepared execution → controlled result → material acceptance → explicit Master save.

## 11. Stage feedback events

- [x] 11.1 Define `creation_recipe.stage_feedback.v1` ProjectEvent schema with exact workflow/run/node/attempt/config/prompt/output/result hashes.
- [x] 11.2 Record explicit decisions: accepted, accepted_with_edits, rejected, rerun_requested and allowed skip; Stage-owned acceptance feedback commits with its authoritative result/output association, retries return the existing exact decision and failures roll back together.
- [x] 11.3 Feedback note/reason tags are bounded and secret-safe.
- [x] 11.4 Acceptance feedback references resulting Master/Variant/Material/Execution identity and hash where applicable.
- [x] 11.5 Feedback never changes Workflow/Capability/Identity/Facts by itself.
- [x] 11.6 Provide stage history UI combining attempts and feedback without another status table.

## 12. Save what worked

- [x] 12.1 Offer deterministic promotion only for an actual explicit allowlisted base→effective tuning diff; content-only edits remain evidence, with no inferred/empty config patch and an explicit authored/selected instruction/method required before Workflow promotion.
- [x] 12.2 “保存到当前项目” applies only allowlisted stage patch to current Workflow draft and saves a new Project Override through existing CAS/versioning.
- [x] 12.3 “保存为默认流程” uses existing Series/Account/Persona × modality portability gate and creates a new immutable default Workflow version.
- [x] 12.4 Existing units/runs do not silently rebind after default promotion.
- [x] 12.5 “保存为方法” creates a Capability Memory `recipe` or `prompt_skill` candidate with exact source feedback/attempt/workflow provenance.
- [x] 12.6 Show diff and destination scope before every promotion.
- [x] 12.7 Regress stale workflow/default save conflicts and no hidden broad-scope promotion.

## 13. Workflow improvement candidates

- [x] 13.1 Define Capability Memory recipe content schema `workflow.stage.recipe.v1`.
- [x] 13.2 Freeze base Workflow checksum, node/plugin/version, Stage Contract schema, allowed config patch and feedback/attempt evidence hashes.
- [x] 13.3 Recipe candidate cannot change dependencies, plugin identity/version, rights/evidence/human gates, output business truth or side-effect policy.
- [x] 13.4 Applying a recipe to a Project/default requires explicit selection and creates a new Workflow revision; the Capability artifact is not mutated.
- [x] 13.5 Create deterministic patch candidates only from accepted explicit tunable-field changes; preserve accepted-with-edits content as feedback evidence, require user-authored/selected allowed instruction/method when no config diff exists and regress no patch inference from content corrections before any model-assisted tuner.
- [x] 13.6 Discovery returns all applicable recipes; no hidden scope precedence.
- [x] 13.7 Usage/outcome records exact recipe revision and accepted/rejected effect without auto-promotion.

## 14. Optional model-assisted tuning preview

- [x] 14.1 Only after 12/13 gates pass, allow an editor to select exact feedback events/attempts and request a tuning suggestion.
- [x] 14.2 Model input is bounded to exact receipts/config diffs/feedback and necessary context; no secrets/raw unrelated sources.
- [x] 14.3 Model may propose only Stage Contract tunable-field patch + explanation.
- [x] 14.4 Record exact successful LLMRun and suggestion hash.
- [x] 14.5 Suggestion never writes Workflow/Capability automatically.
- [x] 14.6 Reject suggestion containing graph/plugin/gate/rights changes.
- [x] 14.7 User may edit the proposed patch before saving; final diff is shown.

## 15. Product flow and usability

- [x] 15.1 Home/Project deep-link to the next actionable recipe stage for active units.
- [x] 15.2 Production normal mode supports full supported journey without raw JSON/canvas.
- [x] 15.3 Stage Drawer has Basic and Advanced tabs; Advanced exposes existing config/mapping/dependency tools.
- [x] 15.4 Show “实际将发送给 AI/Agent 的内容” preview before side-effecting model/Agent execution when supported.
- [x] 15.5 Show each stage's last accepted result and exact workflow revision.
- [x] 15.6 Preserve separate content dirty state vs recipe/workflow dirty state.
- [x] 15.7 Viewer/archive modes are read-only across tuning, run, feedback and promotion.
- [x] 15.8 Keyboard/accessibility interactions for stage navigation and controls.

## 16. E2E acceptance: Text

- [x] 16.1 Direct idea → Project/Brief/Identity/Evidence → effective Text Creation Recipe.
- [x] 16.2 Tune outline/draft stage instruction/model/method; preview exact effective request.
- [x] 16.3 Run stage, receive multiple proposals, prove unresolved review blocks accepted-content downstream, reject one and accept-with-edits another; verify next Stage automatically executes once after commit then waits for its own required review, with exact prepared request visible.
- [x] 16.4 Explicit adoption creates new text.master.v2 with exact stage provenance.
- [x] 16.5 Run checks; make one run-only tuning improvement; accept result.
- [x] 16.6 Promote tuning to Project Override; new run uses it while old attempt stays unchanged.
- [x] 16.7 Capture method candidate and explicitly save/pin it.
- [x] 16.8 Freeze Candidate/Review/local package through existing gates.

## 17. E2E acceptance: Graphic

- [x] 17.1 Graphic Unit uses stage-controlled content/visual-plan proposal plus native image-generation stage.
- [x] 17.2 Change image prompt/profile/aspect/parameters and prove ProviderGenerationTask exact inputs differ.
- [x] 17.3 Accept selected MaterialRevision and explicitly bind it into new Graphic Master.
- [x] 17.4 Reject/replace stage result without rewriting old attempts/materials.
- [x] 17.5 Save successful image-stage method as scoped Capability candidate.
- [x] 17.6 Existing Graphic render/Candidate safety remains unchanged.

## 18. E2E acceptance: Video

- [x] 18.1 Video Unit uses script/shot/director stages under Creation Recipe.
- [x] 18.2 Tune script/director instruction and accept explicit new Video Master revision.
- [x] 18.3 Native TTS/media stage remains ProviderGenerationTask-backed.
- [x] 18.4 Professional-execution stage prepares Director Package/CreativeExecution and does not auto-dispatch.
- [x] 18.5 Controlled external result returns, human accepts MaterialRevision, then explicitly binds/saves new Video Master.
- [x] 18.6 Existing render readiness, v4 Candidate, Review and local package remain exact.
- [x] 18.7 Save a successful director-stage Recipe candidate and reuse it explicitly in another Video Unit.

## 19. Security, performance, migration and closeout

- [x] 19.1 Stage preview/read inventory performs no provider/Agent/Connector/professional-tool call.
- [x] 19.2 Secret/log/audit redaction covers prompts, stage receipts, feedback and tuning suggestions.
- [x] 19.3 Stage overrides and improvement patches cannot bypass evidence/rights/approval/delivery gates.
- [ ] 19.4 Add persistent backend tests for every new stage contract/resolver/receipt/adoption/feedback/promotion safety rule.
- [x] 19.5 Keep Stage Drawer/plugin-specific editors lazy; raw automation/TipTap/media-heavy modules remain outside unrelated initial route closures.
- [ ] 19.6 Run full backend, TypeScript/Vite/FE-P1, Ruff, OpenSpec strict and diff-check.
- [x] 19.7 Rehearse new migration on copied current `aco` SQLite and extend backup/restore acceptance.
- [x] 19.8 Independent backend/data/security review.
- [x] 19.9 Independent frontend/product review centered on “can a user actually control and complete the flow.”
- [x] 19.10 Independent workflow/Agent contract review proving visible tuning equals executed tuning.
- [x] 19.11 Record limitations: professional-tool automation quality and public publication remain separate evidence.
- [ ] 19.12 Formal SQLite upgrade, canonical sync/archive, local commit and push each require their appropriate explicit authorization. Formal crs upgrade alone authorized/completed on 2026-10-06; canonical/archive/commit/push not performed.
