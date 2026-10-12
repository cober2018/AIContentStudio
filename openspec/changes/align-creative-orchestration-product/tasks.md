## 0. Baseline, lifecycle and authorization

- [x] 0.1 Re-read current `main`, confirm AIContentStudio workspace, actual HEAD, dirty ownership and current SQLite/Alembic head before apply.
- [x] 0.2 Preserve the existing F8 single-machine-production documentation work without reset, overwrite or mixed ownership.
- [x] 0.3 Confirm completed F6E implementation/tasks remain unchanged; record its active lifecycle/canonical-sync state before touching overlapping specs.
- [x] 0.4 Independently review this proposal/design/all deltas and obtain explicit apply confirmation before business-code changes.
- [x] 0.5 Record current backend/full frontend/FE-P1/OpenSpec/Ruff/diff baselines and current daily-route browser behavior.
- [x] 0.6 Stop and revise the specification if implementation requires destructive migration, a second content truth store, automatic capability self-modification, arbitrary backend code execution, or weaker Candidate/Delivery/rights gates.

## 1. North Star and operation-parity inventory

- [x] 1.1 Add the approved North Star document as `docs/AI_CONTENT_STUDIO_NORTH_STAR.md`, including capability layering, context compression, result round-trip, creative intent, replaceable executors and Capability Memory.
- [x] 1.2 Inventory every current daily route and legacy route from `App.tsx`, including Landing, Dashboard, Sources, FactPacks, Materials, Workspace, ReviewPublish, Review, Assets, Handoff, Workflows, Templates and legacy Settings.
- [x] 1.3 Produce `docs/LEGACY_OPERATION_PARITY.md` at operation level, not page level: each create/edit/delete/approve/freeze/generate/pull/upload/revoke action, its current API/data truth, target new surface, historical behavior and regression.
- [x] 1.4 Classify every old action as `move_to_new_surface`, `advanced_compatibility`, `historical_read_only` or `obsolete_after_parity`; no action is dropped merely because its menu is hidden.
- [x] 1.5 Record current Project-first normal journey and at least three direct starts: idea → Project, material/source → Project, Opportunity → Project.
- [x] 1.6 Define daily UX vocabulary that hides internal F6/F7 implementation names while preserving exact backend states.
- [x] 1.7 Obtain product/UX spec review of the parity matrix before hiding any legacy entry.

## 2. Daily surface consolidation using existing APIs first

- [x] 2.1 Make `/` enter `/home` rather than legacy `/dashboard`; preserve an explicit compatibility route for legacy dashboard reads until retirement.
- [x] 2.2 Replace `/production` placeholder with a bounded Creation & Execution queue derived from current projects/units, existing native ProviderGenerationTask and later CreativeExecution state; do not create a second task table for projection.
- [x] 2.3 Add clear Project paths for Content, Channel Variants and Execution while preserving existing Brief/Evidence/Assets/Versions/Activity and archived read-only behavior.
- [x] 2.4 Move Source text/URL/file import, fact extraction, fact confirm/reject/edit and bounded bulk actions into the new Assets/Project surfaces using existing Source/Fact APIs.
- [x] 2.5 Move FactPack create/add/remove/clone/freeze and Project fact-boundary actions into the new Assets/Project surfaces using existing FactPack truth.
- [x] 2.6 Keep Material upload/native generation/search/revision/rights/revoke/project-reference operations reachable from the new Assets/Project surfaces without cloning Material truth.
- [x] 2.7 Move ordinary Connector configuration/explicit pull and template/rule actions into Product Settings; keep advanced local-runtime tools lazy and explicit.
- [x] 2.8 Preserve every legacy deep link until its parity row is accepted; do not remove route components in this batch.
- [x] 2.9 Browser-prove a full Source→Fact→FactPack→Project path and Material upload/generation path without navigating to legacy pages.
- [x] 2.10 Run FE-P1/import-graph gates after each surface consolidation batch.

## 3. Additive persistence and migration

- [x] 3.1 Add bounded nullable `creative_intent_json` and `creative_intent_hash` to ContentMasterRevision.
- [x] 3.2 Add bounded nullable `creative_intent_json` and `creative_intent_hash` to ChannelVariantRevision without rewriting existing F6E rows.
- [x] 3.3 Add immutable CreativeExecutionPackage with exact owner/project/unit, one source pointer (Master or Variant), package schema/json/hash, source hashes/context/intent and actor/time.
- [x] 3.4 Add CreativeExecution with owner/project/unit/package, owner-scoped idempotency key/request fingerprint, executor kind/key/version, explicit state set `prepared/claimed/in_progress/failed_before_dispatch/blocked/unknown/result_ready/accepted/rejected/cancelled/superseded`, dispatch certainty, current checkpoint/recovery metadata, safe reason and timestamps; make `failed_before_dispatch` terminal and link retries to a new execution.
- [x] 3.5 Add immutable CreativeExecutionOutput rows with bounded role/kind/staging key/MIME/hash/size, positive `output_index`, monotonic `attempt_no`, result metadata, acceptance state and optional accepted MaterialRevision FK; allow replacement attempts without overwriting rejected history.
- [x] 3.6 Add CapabilityArtifact root with owner, kind, status, scope type/IDs, stable name/current revision and lifecycle timestamps.
- [x] 3.7 Add append-only CapabilityArtifactRevision with revision number, typed bounded content/args schema/metadata, content hash, source execution/learning refs and actor/time.
- [x] 3.8 Add CapabilityUse binding exact artifact revision to actor/project/execution, rendered-argument hash, use time and bounded outcome.
- [x] 3.9 Add FK/check/unique/index constraints for exactly-one execution source, legal states/kinds/scopes, required/optional output contract count invariants, per-role output index/attempt uniqueness, per-owner idempotency, per-artifact revision and hash dedupe where appropriate.
- [x] 3.10 Add downgrade preflight that refuses destructive removal while any new retained execution/capability/intent history exists.
- [x] 3.11 Rehearse isolated SQLite up/down/up with a copied current database and prove v3/v4/v5/Master/Variant/Material/Review history hashes unchanged.
- [x] 3.12 Do not apply the new migration to the user's formal SQLite until separately authorized after full implementation acceptance.

## 4. Creative intent contract

- [x] 4.1 Define versioned bounded creative-intent schema with objective/audience/must_keep/must_avoid/creative_freedom and stable-ID rationale entries.
- [x] 4.2 Canonicalize intent server-side and derive `creative_intent_hash`; reject secrets, raw provider payloads, full source bodies, non-finite/unbounded JSON and duplicate stable IDs.
- [x] 4.3 Extend Master save to accept optional intent under existing expected_revision/idempotency/atomic event gates; changing intent creates a new Master revision.
- [x] 4.4 Extend Variant save to accept optional target-specific intent under existing variant-key CAS/idempotency; changing target intent creates a new Variant revision only.
- [x] 4.5 Project intent history/diff without rewriting payload or evidence truth.
- [x] 4.6 Preserve old Master/Variant rows with null intent as valid historical/current content; never invent backfilled rationales.
- [x] 4.7 Add UI for must-keep/must-avoid/creative-freedom and bounded rationale editing without forcing ordinary users to edit raw JSON.
- [x] 4.8 Regress cross-project raw-ID denial, archived read-only, 409 conflict retention and no fact/Identity mutation.

## 5. Creative Execution Package and Director Package

- [x] 5.1 Implement pure package builder that accepts one exact current project-owned Master or Variant and never writes the source.
- [x] 5.2 Define canonical `creative.execution.v1` with source/context/intent, exact asset/evidence manifests, objective, constraints, and a hashed output contract whose roles define `role_id`, `kind`, `required`, allowed MIME types, minimum/maximum count and maximum bytes, plus acceptance criteria.
- [x] 5.3 Define `director.video.v1` derived from existing Video Master structures plus creative intent: script/scenes/shots/voice/subtitles/overlays/B-roll requirements/selected assets/pacing/duration/aspect/output criteria.
- [x] 5.4 Permit Director Package creation before final Video render exists; require source schema/context/evidence and exact referenced inputs to be internally valid, while recording the missing final-render requirement honestly.
- [x] 5.5 Include Video v2 timeline only as optional advanced execution guidance and preserve its exact data when present.
- [x] 5.6 Bind package hash to exact source id/payload/context/intent/profile and exact ref/evidence hashes so source drift never silently retargets a package.
- [x] 5.7 Make packages immutable/readable after source advances; stale/historical packages are inspection-only and cannot be claimed or started for side-effecting execution, so re-execution must create a new package from the current Master/Variant.
- [x] 5.8 Add Project/Production package preview that explains must-keep, creative freedom, exact inputs and expected outputs before dispatch.
- [x] 5.9 Regress package canonical hash determinism, foreign refs, stale source, revoked input rights/model-use restrictions, derived-rights non-escalation and archived Project.

## 6. Creative Execution state machine and local work root

- [x] 6.1 Implement prepare with owner-scoped idempotency and exact package/request fingerprint.
- [x] 6.2 Implement claim/start transition with explicit executor identity and no external action during inventory/read.
- [x] 6.3 Implement progress/blocker/checkpoint reporting with revision/CAS and safe bounded metadata.
- [x] 6.4 Implement `failed_before_dispatch`, `unknown` and reconciliation semantics; only the confirmed pre-dispatch terminal state may be retried, through a new linked execution/idempotency key, while possible dispatch never triggers automatic resend/restart.
- [x] 6.5 Implement per-execution private work root under configured local state, with owner-only permissions and no business truth stored only there.
- [x] 6.6 Implement exact input materialization from authorized package MaterialRevision refs with live byte/hash/model-use/attribution/license checks and bounded total bytes/count; record the exact input rights boundary used for output acceptance.
- [x] 6.7 Reject arbitrary path access, symlink/path escape, device/special files and material not in the package.
- [x] 6.8 Implement output staging only from regular files under the execution work root; validate each frozen contract role/count, assign immutable `output_index`/`attempt_no`, rehash/sniff/limit, and enter `result_ready` only after every required role has valid staged count >= `min_count` and no role exceeds `max_count`.
- [x] 6.9 Preserve staging across blocked/unknown until explicit resolve/discard; cleanup must never delete accepted MaterialRevision bytes.
- [x] 6.10 Add cancellation/supersede rules that cannot erase history or resolve unknown side effects falsely.
- [x] 6.11 Regress concurrent claim/output submission/acceptance and process-restart readback.

## 7. External result acceptance and existing truth integration

- [x] 7.1 Add result review UI showing the frozen output contract, per-role required/optional counts, missing/replaceable indexes, source package/hash, executor, file/MIME/hash/size, checkpoint/recovery summary, inherited input rights/attribution obligations and rights/license form.
- [x] 7.2 Accept each eligible output explicitly into Material/MaterialRevision using current local StorageProvider, exact byte/hash checks, additive `source_kind=external_execution` and derived-rights non-escalation; a required rejection returns the execution to `blocked/needs_output_replacement`, a higher-attempt replacement may be submitted in the same execution, and `accepted` requires accepted count >= `min_count` for every required role while preserving all existing source kinds/rows.
- [x] 7.3 Record external-execution provenance in accepted revision metadata without storing secrets/raw errors/arbitrary paths.
- [x] 7.4 Optionally attach accepted revision to the owning Project through existing ProjectMaterialReference in the same authorized acceptance flow.
- [x] 7.5 Do not automatically mutate Master, Variant, Candidate, Review, DeliveryTarget or PublishedContentRecord.
- [x] 7.6 For a final Video result, explicitly select/bind the accepted render in Video Studio and save a new Video Master revision before existing v4 freeze gates can pass.
- [x] 7.7 For image/audio outputs, require the normal explicit Master/Variant edit/save to use the accepted revision.
- [x] 7.8 Recheck live rights, source/package currentness, inherited attribution/license obligations and staging hash at acceptance; drift or rights escalation returns a controlled no-partial-write failure.
- [x] 7.9 Preserve rejected outputs/execution history while allowing bounded staged-file cleanup after explicit rejection/discard policy; do not accept replacement output after terminal execution states.
- [x] 7.10 Regress same output hash dedupe semantics, multi-output required/optional completion, required-output replacement attempts, explicit whole-execution rejection and derived-rights non-escalation without falsely reusing provenance from another owner/project/execution.

## 8. Loopback MCP first version

- [x] 8.1 Add same-process Streamable HTTP MCP endpoint bound to the current loopback API deployment; no second daemon required.
- [x] 8.2 Require an ignored-runtime local bearer token and explicit existing owner user ID; never map MCP identity from untrusted email/role claims.
- [x] 8.3 Refuse non-loopback callers, missing/invalid token and foreign project/entity IDs before serialization.
- [x] 8.4 Expose bounded project/unit/Identity/Brief/Fact Boundary/Master/Variant/CreativeExecutionPackage/execution-state resources without secrets/raw source bodies unless the exact package contract includes bounded excerpts.
- [x] 8.5 Expose applicable saved/pinned Capability Memory discovery/use resources with exact revision/scope/hash.
- [x] 8.6 Implement mutation tools: claim/start prepared execution, materialize inputs, report progress, report blocker, report checkpoint, submit output, mark/reconcile unknown and request human review.
- [x] 8.7 Do not expose direct Master/Variant save, Candidate approval, Delivery Authorization, publication, arbitrary filesystem or raw SQL tools.
- [x] 8.8 All MCP writes call the same domain services/CAS/idempotency and ProjectEvent/AuditLog paths as UI/API operations.
- [x] 8.9 Add response size limits, redaction, stable error categories and trace correlation; MCP inventory/list calls make no provider/professional-tool call.
- [x] 8.10 Validate first against a controlled local Test Agent completing package→input→output→result-ready→human acceptance.
- [x] 8.11 Validate one Codex or Claude local-client connection after Test Agent gates pass; this does not require a real professional editor.
- [x] 8.12 Document setup without exposing the bearer token in Settings/logs/screenshots.

## 9. Checkpoint, recovery and professional executor descriptors

- [x] 9.1 Define executor descriptor fields for kind/key/version and supports_checkpoint/supports_revert/supports_recover plus bounded output kinds.
- [x] 9.2 Permit a checkpoint reference only after execution claim and bind it to exact execution/package/executor revision.
- [x] 9.3 Record `failed_before_dispatch`, `blocked` and `unknown` distinctly; `failed_before_dispatch` is terminal and only it can be retried without state reconciliation, by creating a new linked execution rather than rewriting history.
- [x] 9.4 Add reconcile action requiring bounded current-state observation and actor confirmation before continue/revert/recover from unknown.
- [x] 9.5 Never claim an external revert succeeded without executor/Agent readback evidence.
- [x] 9.6 Keep checkpoint identifiers/paths as safe bounded metadata; no arbitrary external path becomes project truth.
- [x] 9.7 Test executor: prove checkpoint→mutate→failure→unknown/readback→revert/recover→new result without duplicate dispatch.
- [x] 9.8 Keep real After Effects/Premiere/Resolve/Photoshop integration outside first acceptance; add one pilot only after generic contracts pass.

## 10. Capability Memory

- [x] 10.1 Implement artifact kinds `prompt_skill`, `recipe`, `creative_pattern`, `preference`, `execution_template`, `tool`.
- [x] 10.2 Implement statuses `candidate`, `saved`, `pinned`, `archived`, `deprecated`; candidate cannot be made authoritative by usage alone.
- [x] 10.3 Implement explicit scopes `owner`, `persona`, `account`, `series`, `project`, `channel`, `executor` with ownership/hierarchy validation; return all applicable revisions and require explicit selection instead of hidden merge/override/precedence.
- [x] 10.4 Canonicalize bounded artifact content/args schema and compute revision content hash; reject the entire capture/save for secrets, credential URLs, raw private source dumps and unsafe/unbounded payloads, while allowing only allowlisted external provenance/diagnostic metadata to be omitted.
- [x] 10.5 Auto-capture/deduplicate a candidate only from an execution that is fully top-level `accepted` under its frozen output contract and supplies an explicitly reusable artifact; one accepted output or partial required-output acceptance cannot create a capability candidate, and capture failure never changes execution result.
- [x] 10.6 Default auto-captured candidate to the narrowest safe source scope; broadening scope requires explicit human confirmation.
- [x] 10.7 Implement promote candidate → saved, save/pin/archive/deprecate and append-only revision update with expected_revision/CAS.
- [x] 10.8 Candidate promotion may change display metadata/scope/status but may not silently replace captured content; changing content creates a new artifact revision after explicit edit.
- [x] 10.9 Implement search/discovery by kind/scope/tags/text with exact revision identity and stable presentation ordering; do not treat ordering as automatic scope precedence or silently choose a conflicting revision.
- [x] 10.10 Implement `use` as render/return of artifact content + validated arguments to UI/MCP; do not execute arbitrary artifact code in backend v1.
- [x] 10.11 Record CapabilityUse with exact revision, context and optional later accepted/rejected/unknown outcome; update use_count/last_used safely.
- [x] 10.12 Do not auto-edit Identity, facts, Workflow defaults, channel config, Master/Variant or other capabilities based on use count/outcome.
- [x] 10.13 Add explicit import/export only after core lifecycle is stable; imported content is scanned, gets a new local identity and never becomes pinned automatically.
- [x] 10.14 Add UI for Candidates, Saved, Pinned and Archived plus source provenance, scope, revision history and usage.
- [x] 10.15 Regress project/private-scope leakage, sibling Persona/Account isolation, stale revision conflicts, archive/deprecated discovery and secret rejection.
- [x] 10.16 Keep Installed Agent Skills from configured local skill directories as a separate external inventory with distinct `source_kind`/stable identity; do not import/export/install/enable/overwrite/promote them through Capability Memory, and do not change `skills_enabled` during Capability promotion.

## 11. Learning and personalization bridge

- [x] 11.1 Extend Learning categories/projections only as needed to propose a reusable method/pattern candidate without changing existing publication-evidence semantics.
- [x] 11.2 Add explicit action from an accepted evidence-backed LearningCandidate to a Capability Memory candidate; freeze source candidate/evidence refs.
- [x] 11.3 Learning acceptance alone creates no capability artifact; capability promotion remains separate.
- [x] 11.4 Capability use/outcome may be cited as workflow/process evidence but never as public-performance evidence unless backed by existing Published/Performance truth.
- [x] 11.5 Allow explicit user preference candidates from repeated accepted edits only as suggestions; no invisible preference update.
- [x] 11.6 Show applicable saved preferences/patterns in creation UI with scope and an opt-out/override, never as hidden mandatory prompts.
- [x] 11.7 Regress facts/evidence unaffected by preference/artifact changes and ContentMemory unaffected unless its existing validated promotion is invoked.

## 12. Content-first Production and Video reframe

- [x] 12.1 Make per-unit Production prioritize Content Master, creative intent, assets, Channel Variants, native generation and Creative Execution.
- [x] 12.2 Move Workflow design/Node Inspector/Run internals into explicit Advanced/Automation UI without changing FE-F2 persistence or execution.
- [x] 12.3 Add bounded form-specific Channel Variant editing that saves a new existing F6E Variant revision and never mutates Master/sibling variants.
- [x] 12.4 Reframe Video main surface around Script, Scene/Shot intent, Assets, Voice, Subtitles, Cover, Director Package and External Execution.
- [x] 12.5 Keep current Video v2 timeline/render controls available under advanced/compatibility and preserve all historical v1/v2 editing/read rules required by existing specs.
- [x] 12.6 Do not require a professional-tool execution to save a Video Master draft or Director Package; final Candidate readiness still follows existing render gates.
- [x] 12.7 Native basic image/TTS/ASR generation remains reachable from the same creation experience and continues to use ProviderGenerationTask/MaterialRevision.
- [x] 12.8 Browser: create one video Director Package before render, complete external Test Agent result, accept MP4, bind/save new Master, freeze/review/package using existing v4 contract.
- [x] 12.9 Browser: historical Video Candidate/ZIP remains byte/hash stable after the UI reframe.

## 13. Home, Review, Assets, Settings and legacy retirement

- [x] 13.1 Home projects CreativeExecution `result_ready`, `blocked`, `unknown` and human-review needs with precedence consistent with existing operational risks; no Home task table.
- [x] 13.2 `/production` queue deep-links to exact Project/Unit/native task/external execution.
- [x] 13.3 Assets/Knowledge completes every parity row for Sources/Facts/FactPacks/Materials before those legacy menu items are removed.
- [x] 13.4 Settings completes every parity row for Connector/Templates/ordinary runtime operations before legacy Settings loses daily entry status.
- [x] 13.5 Review displays external execution provenance only after the output has been explicitly incorporated into the source Candidate path; raw result_ready is not a Candidate.
- [x] 13.6 Preserve legacy Topic Review/Handoff/Workflow history reads until their parity rows explicitly classify them historical/compatibility.
- [x] 13.7 Remove `LEGACY_NAV` daily visibility only after the complete parity inventory is green; keep compatibility URLs or explicit redirects with record identity.
- [x] 13.8 Never redirect every legacy URL to a generic project list; preserve entity context where a mapping exists.
- [x] 13.9 Browser: normal new project from source through local package uses only daily new navigation.
- [x] 13.10 Browser: historical old draft/candidate/receipt remains readable and cannot be silently converted into new execution/capability state.

## 14. Performance, recovery, security and closeout

- [x] 14.1 Keep Creative Execution/Capability Memory/MCP UI lazy; preserve Home/Projects/Settings/Assets and unrelated modality FE-P1 budgets.
- [x] 14.2 Extend single-machine backup/restore rehearsal to new durable tables; accepted outputs are recovered through MaterialRevision bytes, while disposable staging is not required after acceptance.
- [x] 14.3 Verify secret redaction across MCP, execution metadata, capability artifacts, audit/logs/errors and exported diagnostics.
- [x] 14.4 Verify no read-only inventory triggers native generation, external dispatch, MCP side effects or professional-tool calls.
- [x] 14.5 Full backend, frontend TypeScript/Vite, FE-P1, OpenSpec strict, relevant lint and diff-check.
- [x] 14.6 Browser acceptance: direct idea start; Source/Fact/FactPack path; Material native generation; Text/Graphic/Video editing; five existing Channel Variants; Candidate/Approval/local package; Creative Execution round trip; Capability candidate→promotion→reuse; legacy historical read.
- [x] 14.7 Independent backend/data/security review of migration, scope authorization, staging paths, Unknown/recovery and Capability Memory non-execution boundary.
- [x] 14.8 Independent frontend/product review of one daily surface, operation parity, content-first Production, Video reframe and no lost legacy operation.
- [x] 14.9 Independent MCP review proving no arbitrary filesystem/SQL/content mutation or approval/publication bypass.
- [x] 14.10 Record exact limitations: first acceptance does not prove Premiere/AE/Resolve/Photoshop automation or generative-quality superiority.
- [x] 14.11 Update North Star, parity inventory, README, roadmap/progress/findings and acceptance record with exact outcomes.
- [x] 14.12 Keep canonical sync/archive, push, deployment, live SQLite migration and deletion of compatibility pages pending separate explicit authorization.

## 15. Post-enable closeout review R1 / R2

- [x] 15.1 Align local approved schema/readiness default and F8/current recovery/parity documentation to aco; preserve historical f7d acceptance and null/inert identity semantics without live rollback/auth activation.
- [x] 15.2 Retain isolated CreativeExecution stale/Unknown/multi-output replacement/derived-rights regressions in the repository.
- [x] 15.3 Retain isolated MCP loopback/auth/whitelist/no approval-publication regressions.
- [x] 15.4 Retain Capability candidate/promotion/scope-conflict/secret/Installed Skills separation regressions.
- [x] 15.5 Retain ACO upgrade from approved old head, new schema/history checks, downgrade refusal and identity-null/default-readiness regressions.
- [x] 15.6 Run fresh full backend, TypeScript/Vite/FE-P1, OpenSpec strict, Ruff and diff-check; update closeout receipt without claiming archive or commit.
- [ ] 15.7 Obtain final same-workspace closeout review before canonical sync/archive/local feature commit; preserve running local services and require separate push authorization.
