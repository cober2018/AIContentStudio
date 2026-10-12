## 0. Baseline closeout before new feature work

- [ ] 0.1 Re-read current workspace/HEAD/dirty ownership; preserve the current Creative Orchestration implementation and F8 owned files.
- [ ] 0.2 Reconcile current single-machine schema truth: formal DB/readiness is `aco000000001`; document `f8a` identity columns as inert nullable ancestry only, not JWT/production-identity activation.
- [ ] 0.3 Update `LOCAL_APPROVED_SCHEMA_HEAD`, readiness tests, backup/restore current-head guidance and stale parity text without changing APP_ENV/auth behavior or rolling back the live DB.
- [ ] 0.4 Add persistent backend regression tests for existing CreativeExecution state/output/rights, MCP auth/tool restrictions, Capability Memory lifecycle/scope/secret rejection/Installed Skills separation, and ACO migration/downgrade guard.
- [ ] 0.5 Run existing full backend, frontend build/FE-P1, OpenSpec strict and diff-check before new Creation Recipe behavior.
- [ ] 0.6 Stop and revise if the design requires a second Recipe/Feedback truth table or hidden workflow self-modification.

## 1. Creation Recipe projection

- [ ] 1.1 Define Creation Recipe as an API/UI projection of the existing effective Workflow ID/version/checksum and source scope.
- [ ] 1.2 Add stage read model with node ID/kind/plugin/version/label, readiness, last attempt, accepted target, blockers, inherited-default diff and unsaved local state.
- [ ] 1.3 Do not persist recipe status separately; derive from Workflow/Run/Attempt/ProjectEvent/accepted target truth.
- [ ] 1.4 Production defaults to stage strip/list + current content editor; raw canvas moves behind Advanced without losing any existing graph action.
- [ ] 1.5 Show current source scope: Series → Account → Persona default or Project override, exact revision and checksum.
- [ ] 1.6 Add recipe version/diff/history projection without mutating old Workflow rows.

## 2. Stage Contract registry

- [ ] 2.1 Extend PluginDescriptor with optional versioned Stage Contract metadata.
- [ ] 2.2 Define bounded stage contract fields: schema/title/category/config schema/UI schema/tunable fields/input contract/output contract/method sources/preview/run-override/candidate/human-acceptance flags.
- [ ] 2.3 Validate that every normal UI field maps to a declared tunable/executor-consumed field; reject unknown config.
- [ ] 2.4 Legacy plugins without a Stage Contract remain Advanced/compatibility only and keep semantics.
- [ ] 2.5 Add stage contracts for current checks/human nodes that are safe to expose without changing their business truth.
- [ ] 2.6 Add contract tests proving cosmetic/unconsumed config is rejected.

## 3. Effective Stage Resolver and prompt preview

- [ ] 3.1 Implement pure server resolver for exact saved node + optional allowed override + current pinned context + explicit method/model selections + upstream outputs.
- [ ] 3.2 Define `ResolvedStageExecution` canonical schema and hash.
- [ ] 3.3 Resolve Capability Memory only by exact selected artifact revision; never silently choose conflicting scope results.
- [ ] 3.4 Resolve Installed Skill only by exact installed descriptor/version and executable runtime; installed inventory alone is not execution proof.
- [ ] 3.5 Resolve model profile/provider/model using existing model-capability routing and fail visibly when unavailable.
- [ ] 3.6 Build layered effective prompt preview: base method, Identity, stage instruction, Brief, Creative Intent, evidence constraints, upstream output, task override.
- [ ] 3.7 Bound/redact preview; no secrets/raw credential URLs/provider errors.
- [ ] 3.8 Preview makes no model/provider/Agent/tool call.
- [ ] 3.9 Actual execution re-resolves and fails on config/context/method/model drift instead of silently using a different request.
- [ ] 3.10 Add exact prompt/config/resolution hash regression.

## 4. Attempt execution receipt and migration

- [ ] 4.1 Add one additive migration after `aco000000001` with nullable bounded `input_snapshot_json` and `execution_receipt_json` on `workflow_step_attempt`.
- [ ] 4.2 Keep legacy attempt rows valid with null new fields and no backfill.
- [ ] 4.3 Freeze Workflow ID/version/checksum, node/plugin, base config hash, run override, effective config/method/model/prompt/upstream hashes and output contract into every Stage Contract attempt.
- [ ] 4.4 Freeze bounded exact resolved input snapshot required to explain the attempt.
- [ ] 4.5 Failed attempts also retain the receipt/input snapshot.
- [ ] 4.6 Add migration up/down/up on isolated copied SQLite; downgrade refuses only if new receipt data would be destroyed.
- [ ] 4.7 Do not migrate formal SQLite until full feature acceptance and separate enablement authorization.

## 5. Run-only stage overrides

- [ ] 5.1 Add bounded run/rerun `stage_override` accepted only for declared tunable fields.
- [ ] 5.2 Overrides cannot change plugin/version, dependencies, mappings outside contract, evidence/rights/human gates or side-effect classification.
- [ ] 5.3 Show base config vs temporary override vs effective config before run.
- [ ] 5.4 Stage rerun with override creates a new immutable attempt and does not overwrite prior attempt/config/output.
- [ ] 5.5 Run-only override does not alter Project Workflow Override or scoped default.
- [ ] 5.6 Repeated response-loss retries use attempt/CAS/idempotency protections and do not duplicate side effects.

## 6. Project-native Master proposal stage

- [ ] 6.1 Add `stage.master.propose@1` without changing legacy `builtin.generate`.
- [ ] 6.2 Its Stage Contract exposes purpose/instruction/model/method/candidate count/length-creativity controls supported by actual executor.
- [ ] 6.3 Resolve current Content Unit, optional current Master, pinned Identity/Brief/Fact Boundary/Creative Intent and declared upstream inputs.
- [ ] 6.4 Model request uses exact Effective Stage Resolver output and records LLMRun/input hash/model/prompt receipt.
- [ ] 6.5 Return 1–5 bounded `stage.master.proposal.v1` candidates with stable candidate IDs/hashes.
- [ ] 6.6 Validate Text/Graphic/Video candidates with their existing canonical Master adapters; reject invented foreign refs.
- [ ] 6.7 Node execution never saves a Master.
- [ ] 6.8 Browser/API prove changing stage instruction/model/candidate count changes the actual resolved request/receipt, not UI only.

## 7. Stage result review and Master adoption

- [ ] 7.1 Add Stage Result Review UI: candidate preview/diff, receipt, accept, accept-with-edits, reject, rerun, rerun-with-override.
- [ ] 7.2 Adoption requires exact Run/StepAttempt/attempt output hash/candidate ID/candidate hash.
- [ ] 7.3 Recheck current unit/context and reject stale candidate adoption; offer rerun/rebase, never silent retarget.
- [ ] 7.4 Add trusted `workflow_stage` Content Master save path that validates final payload/refs through existing modality adapters.
- [ ] 7.5 Freeze Workflow/run/node/attempt/config/prompt/resolution/proposal/model/method provenance in Master edit summary/source provenance.
- [ ] 7.6 Accepted-with-edits records proposal hash and accepted Master hash plus bounded edit summary.
- [ ] 7.7 After Master exists, associate ProjectWorkflowOutput `content_master_revision` with exact run/node/attempt; raw proposal is never a ProjectWorkflowOutput entity.
- [ ] 7.8 No adoption freezes Candidate, approves content or changes Delivery.
- [ ] 7.9 Historical attempt/proposal remains readable after newer Master revisions.

## 8. Native media stage integration

- [ ] 8.1 Expose existing `media.generate` through a typed Stage Contract rather than raw JSON for ordinary use.
- [ ] 8.2 Stage controls map exactly to ProviderGenerationTask capability/profile/prompt/parameters and are revalidated server-side.
- [ ] 8.3 Result panel shows the existing generation task and explicit MaterialRevision acceptance; no duplicate media task/result table.
- [ ] 8.4 Accepted material is not automatically bound into Master.
- [ ] 8.5 Stage feedback can record exact chosen/rejected MaterialRevision/task result.
- [ ] 8.6 Prove image, video and TTS stage controls use exact provider task inputs and Unknown/no-auto-retry remains unchanged.

## 9. Channel Variant stage integration

- [ ] 9.1 Add stage wrapper over existing F6E target/profile/adapter preview/model-assist/save contract.
- [ ] 9.2 Stage config includes exact target channel/form and supported adaptation instruction/method/model fields.
- [ ] 9.3 Result review uses existing Variant payload diff/checks and explicit append-only save.
- [ ] 9.4 Changing one Variant stage never mutates source Master/sibling variants.
- [ ] 9.5 Preserve existing F6E deterministic/model provenance and 409/currentness behavior.
- [ ] 9.6 No generic workflow node may invent a ChannelVariantRevision outside F6E service.

## 10. Professional execution stage integration

- [ ] 10.1 Add a stage surface that prepares current `CreativeExecutionPackage` / `director.video.v1` and optionally a prepared CreativeExecution.
- [ ] 10.2 Stage never auto-dispatches professional tools; MCP/Agent claim/start remains explicit.
- [ ] 10.3 Stage projects CreativeExecution progress/blocker/unknown/result_ready/accepted without copying state.
- [ ] 10.4 Accepted external MaterialRevision still requires explicit Master/Variant incorporation.
- [ ] 10.5 Checkpoint/recovery and derived-rights gates remain unchanged.
- [ ] 10.6 Browser prove video Script/Director stage → prepared execution → controlled result → material acceptance → explicit Master save.

## 11. Stage feedback events

- [ ] 11.1 Define `creation_recipe.stage_feedback.v1` ProjectEvent schema with exact workflow/run/node/attempt/config/prompt/output/result hashes.
- [ ] 11.2 Record explicit decisions: accepted, accepted_with_edits, rejected, rerun_requested and allowed skip.
- [ ] 11.3 Feedback note/reason tags are bounded and secret-safe.
- [ ] 11.4 Acceptance feedback references resulting Master/Variant/Material/Execution identity and hash where applicable.
- [ ] 11.5 Feedback never changes Workflow/Capability/Identity/Facts by itself.
- [ ] 11.6 Provide stage history UI combining attempts and feedback without another status table.

## 12. Save what worked

- [ ] 12.1 If an accepted attempt used a run override, show exact base→effective config diff.
- [ ] 12.2 “保存到当前项目” applies only allowlisted stage patch to current Workflow draft and saves a new Project Override through existing CAS/versioning.
- [ ] 12.3 “保存为默认流程” uses existing Series/Account/Persona × modality portability gate and creates a new immutable default Workflow version.
- [ ] 12.4 Existing units/runs do not silently rebind after default promotion.
- [ ] 12.5 “保存为方法” creates a Capability Memory `recipe` or `prompt_skill` candidate with exact source feedback/attempt/workflow provenance.
- [ ] 12.6 Show diff and destination scope before every promotion.
- [ ] 12.7 Regress stale workflow/default save conflicts and no hidden broad-scope promotion.

## 13. Workflow improvement candidates

- [ ] 13.1 Define Capability Memory recipe content schema `workflow.stage.recipe.v1`.
- [ ] 13.2 Freeze base Workflow checksum, node/plugin/version, Stage Contract schema, allowed config patch and feedback/attempt evidence hashes.
- [ ] 13.3 Recipe candidate cannot change dependencies, plugin identity/version, rights/evidence/human gates, output business truth or side-effect policy.
- [ ] 13.4 Applying a recipe to a Project/default requires explicit selection and creates a new Workflow revision; the Capability artifact is not mutated.
- [ ] 13.5 Implement deterministic candidate creation from accepted successful overrides/accepted-with-edits before any model-assisted tuner.
- [ ] 13.6 Discovery returns all applicable recipes; no hidden scope precedence.
- [ ] 13.7 Usage/outcome records exact recipe revision and accepted/rejected effect without auto-promotion.

## 14. Optional model-assisted tuning preview

- [ ] 14.1 Only after 12/13 gates pass, allow an editor to select exact feedback events/attempts and request a tuning suggestion.
- [ ] 14.2 Model input is bounded to exact receipts/config diffs/feedback and necessary context; no secrets/raw unrelated sources.
- [ ] 14.3 Model may propose only Stage Contract tunable-field patch + explanation.
- [ ] 14.4 Record exact successful LLMRun and suggestion hash.
- [ ] 14.5 Suggestion never writes Workflow/Capability automatically.
- [ ] 14.6 Reject suggestion containing graph/plugin/gate/rights changes.
- [ ] 14.7 User may edit the proposed patch before saving; final diff is shown.

## 15. Product flow and usability

- [ ] 15.1 Home/Project deep-link to the next actionable recipe stage for active units.
- [ ] 15.2 Production normal mode supports full supported journey without raw JSON/canvas.
- [ ] 15.3 Stage Drawer has Basic and Advanced tabs; Advanced exposes existing config/mapping/dependency tools.
- [ ] 15.4 Show “实际将发送给 AI/Agent 的内容” preview before side-effecting model/Agent execution when supported.
- [ ] 15.5 Show each stage's last accepted result and exact workflow revision.
- [ ] 15.6 Preserve separate content dirty state vs recipe/workflow dirty state.
- [ ] 15.7 Viewer/archive modes are read-only across tuning, run, feedback and promotion.
- [ ] 15.8 Keyboard/accessibility interactions for stage navigation and controls.

## 16. E2E acceptance: Text

- [ ] 16.1 Direct idea → Project/Brief/Identity/Evidence → effective Text Creation Recipe.
- [ ] 16.2 Tune outline/draft stage instruction/model/method; preview exact effective request.
- [ ] 16.3 Run stage, receive multiple proposals, reject one and accept-with-edits another.
- [ ] 16.4 Explicit adoption creates new text.master.v2 with exact stage provenance.
- [ ] 16.5 Run checks; make one run-only tuning improvement; accept result.
- [ ] 16.6 Promote tuning to Project Override; new run uses it while old attempt stays unchanged.
- [ ] 16.7 Capture method candidate and explicitly save/pin it.
- [ ] 16.8 Freeze Candidate/Review/local package through existing gates.

## 17. E2E acceptance: Graphic

- [ ] 17.1 Graphic Unit uses stage-controlled content/visual-plan proposal plus native image-generation stage.
- [ ] 17.2 Change image prompt/profile/aspect/parameters and prove ProviderGenerationTask exact inputs differ.
- [ ] 17.3 Accept selected MaterialRevision and explicitly bind it into new Graphic Master.
- [ ] 17.4 Reject/replace stage result without rewriting old attempts/materials.
- [ ] 17.5 Save successful image-stage method as scoped Capability candidate.
- [ ] 17.6 Existing Graphic render/Candidate safety remains unchanged.

## 18. E2E acceptance: Video

- [ ] 18.1 Video Unit uses script/shot/director stages under Creation Recipe.
- [ ] 18.2 Tune script/director instruction and accept explicit new Video Master revision.
- [ ] 18.3 Native TTS/media stage remains ProviderGenerationTask-backed.
- [ ] 18.4 Professional-execution stage prepares Director Package/CreativeExecution and does not auto-dispatch.
- [ ] 18.5 Controlled external result returns, human accepts MaterialRevision, then explicitly binds/saves new Video Master.
- [ ] 18.6 Existing render readiness, v4 Candidate, Review and local package remain exact.
- [ ] 18.7 Save a successful director-stage Recipe candidate and reuse it explicitly in another Video Unit.

## 19. Security, performance, migration and closeout

- [ ] 19.1 Stage preview/read inventory performs no provider/Agent/Connector/professional-tool call.
- [ ] 19.2 Secret/log/audit redaction covers prompts, stage receipts, feedback and tuning suggestions.
- [ ] 19.3 Stage overrides and improvement patches cannot bypass evidence/rights/approval/delivery gates.
- [ ] 19.4 Add persistent backend tests for every new stage contract/resolver/receipt/adoption/feedback/promotion safety rule.
- [ ] 19.5 Keep Stage Drawer/plugin-specific editors lazy; raw automation/TipTap/media-heavy modules remain outside unrelated initial route closures.
- [ ] 19.6 Run full backend, TypeScript/Vite/FE-P1, Ruff, OpenSpec strict and diff-check.
- [ ] 19.7 Rehearse new migration on copied current `aco` SQLite and extend backup/restore acceptance.
- [ ] 19.8 Independent backend/data/security review.
- [ ] 19.9 Independent frontend/product review centered on “can a user actually control and complete the flow.”
- [ ] 19.10 Independent workflow/Agent contract review proving visible tuning equals executed tuning.
- [ ] 19.11 Record limitations: professional-tool automation quality and public publication remain separate evidence.
- [ ] 19.12 Formal SQLite upgrade, canonical sync/archive, local commit and push each require their appropriate explicit authorization.
