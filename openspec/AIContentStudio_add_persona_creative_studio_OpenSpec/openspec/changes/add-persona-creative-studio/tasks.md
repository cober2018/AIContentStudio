## 0. Baseline and active-change reconciliation

- [ ] 0.1 Re-read current `main@341ead8` dirty worktree and preserve all ACO/Creation Recipe/F8 owned changes; no reset/rebase/cleanup of unrelated files.
- [ ] 0.2 Verify the currently enabled local schema/readiness remains `crs000000001`; this change targets zero new DB migration.
- [ ] 0.3 Fix `complete-multiplatform-content-handoff` wording from nonexistent `stage.variant.propose` to existing `stage.variant.adapt@1` before that change applies.
- [ ] 0.4 Replace that change's “no new test code” rule with small parameterized persistent contract tests plus concentrated 17-form smoke.
- [ ] 0.5 Run current backend persistent suite, frontend build/FE-P1, OpenSpec strict and diff-check before new behavior; record inherited evidence separately from fresh runs.

## 1. Studio Creative resource catalog

- [ ] 1.1 Add product-owned versioned `studio_builtin_skill` inventory separate from Installed Agent Skills and Capability Memory.
- [ ] 1.2 Add versioned `style_preset`, `quality_profile` and `starter_persona_blueprint` resource catalogs.
- [ ] 1.3 Implement bounded safe inventory projection with exact key/version/source_kind/provenance and no secrets/paths.
- [ ] 1.4 Define resource layout: `SKILL.md`, `STUDIO-CONTRACT.json`, `STUDIO-META.md`, optional `references/`, tests/fixtures; runtime does not execute arbitrary package scripts.
- [ ] 1.5 Add provenance/license classification: self-developed / adapted / method-reference / vendored; vendored code requires explicit license-compatible decision.
- [ ] 1.6 Add persistent resource validators for frontmatter/contracts/references/provenance/bounds/secret/path leakage.

## 2. Built-in Skill Pack

- [ ] 2.1 Add `studio.research.evidence-brief@1` and `studio.research.angle-lab@1`.
- [ ] 2.2 Add Text skills: `studio.text.outline@1`, `studio.text.longform@1`, `studio.text.answer@1`, `studio.text.social-short@1`, `studio.text.humanize@1`, `studio.text.title-hook@1`.
- [ ] 2.3 Add Graphic skills: `studio.graphic.visual-director@1`, `studio.graphic.card-plan@1`, `studio.graphic.image-brief@1`, plus registered deterministic `studio.graphic.layout-compose@1` and `studio.graphic.qc@1` tools.
- [ ] 2.4 Add Audio skills: `studio.audio.spoken-adapt@1`, `studio.audio.voice-director@1`, `studio.audio.tts@1`, `studio.audio.qc@1`.
- [ ] 2.5 Add Video planning skills: `studio.video.script@1`, `studio.video.shot-director@1`, `studio.video.director-package@1`.
- [ ] 2.6 Every Skill contract declares stage compatibility, required context, tunable fields, output schema, reference/tool keys and bounds.
- [ ] 2.7 Add validator proving every declared tunable field is consumed by the resolver/executor/tool contract; no UI-only settings.
- [ ] 2.8 Add validator proving every referenced tool/rule/provider key/version resolves or is intentionally optional with a truthful unavailable reason.

## 3. Built-in Style Presets and Quality Profiles

- [ ] 3.1 Add Text presets: deep-technical, engineering-explainer, observational-lifestyle, reflective-lifestyle, concise-social.
- [ ] 3.2 Add Graphic presets: technical-editorial, architecture-diagram, clean-infographic, warm-magazine, documentary-photo, lifestyle-cards.
- [ ] 3.3 Add Audio presets: calm-engineer, clear-explainer, warm-conversational, reflective-story.
- [ ] 3.4 Add Text quality profiles: technical and lifestyle.
- [ ] 3.5 Add Graphic quality profiles: editorial and lifestyle.
- [ ] 3.6 Add Audio quality profiles: explainer and conversational.
- [ ] 3.7 Add persistent schema/version tests and exact reference tests from persona blueprints and default recipes.

## 4. Persona Creative Profile schema

- [ ] 4.1 Extend `IdentityProfile` with bounded `text_creative_profile`, `graphic_creative_profile`, `audio_creative_profile`, `video_creative_profile` fields; no new table/column.
- [ ] 4.2 Define strict `persona.creative.<modality>.v1` validation with `auto|custom|composed`, exact resource refs, model policy, defaults and fallback policy.
- [ ] 4.3 Preserve existing identity inheritance: missing inherits, null clears, object replaces as a whole; do not deep merge modality creative profiles.
- [ ] 4.4 Freeze creative profile fields/origins into ordinary IdentitySnapshot checksum and expose them in frozen Production/Review context.
- [ ] 4.5 Reject secrets, credential-bearing URLs, raw local paths, arbitrary executable content and unknown fields.
- [ ] 4.6 Add Persona/Account/Series revision/CAS/archive tests for creative profiles.
- [ ] 4.7 Confirm owner/user scope is not used as an implicit creative-style default.

## 5. Starter Persona Blueprints

- [ ] 5.1 Implement `starter.ai-tech-engineer.v1` with the exact positioning/audience/style/visual/audio/boundary configuration defined by the design.
- [ ] 5.2 Implement `starter.lifestyle-observer.v1` with the exact positioning/audience/style/visual/audio/freshness/speculation configuration defined by the design.
- [ ] 5.3 Each blueprint pins exact Text/Graphic/Audio/Video creative profiles, built-in Skill/Preset/Quality refs and default recipe template keys.
- [ ] 5.4 Add zero-write preview endpoint/read model showing what Persona revision/default workflows would be created.
- [ ] 5.5 Add explicit idempotent apply in isolated tests: create normal ContentPersona + revision + Persona workflow defaults; store blueprint key/version in creative-profile provenance.
- [ ] 5.6 Same-name manually created Persona is never treated as blueprint-owned; collision returns a reviewable choice rather than overwrite.
- [ ] 5.7 Re-applying an already initialized blueprint with user edits returns current/diff and does not reset it silently.
- [ ] 5.8 Formal local initialization of the two Persona records remains a separate post-acceptance enablement action with backup/readback.

## 6. Creative configuration resolver

- [ ] 6.1 Add server `CreativeConfigurationResolver` used by Effective Stage Resolver; no second client-side resolver.
- [ ] 6.2 Auto mode resolves exact built-in Skill/Preset/Quality refs from effective identity and only uses existing executable model/capability route truth.
- [ ] 6.3 Custom mode pins exact Skill/Preset/Quality/model profile/default params and fails closed when unavailable.
- [ ] 6.4 Composed mode requires one exact Studio built-in base plus explicit ordered Capability Memory revision IDs; external Installed Skill allowed only when explicitly selected and executable.
- [ ] 6.5 Do not automatically select among multiple applicable Capability Memory artifacts.
- [ ] 6.6 Apply documented precedence: hard Stage/rights/channel constraints → Run override → Project Stage config → effective identity creative profile → built-in fallback → authorized provider fallback.
- [ ] 6.7 Preview returns each source scope/revision/hash, effective method stack, preset, quality profile, provider/model and fallback explanation.
- [ ] 6.8 Execution receipt freezes the same identities/hashes; drift blocks execution rather than silently replanning.

## 7. Intermediate creative method stage and handoff

- [ ] 7.1 Add `stage.creative.method@1` Stage Contract with exact Studio Skill/method-stack selection and typed output schema.
- [ ] 7.2 Support first intermediate schemas: research.brief.v1, creative.angles.v1, content.outline.v1, graphic.visual-direction.v1, graphic.card-plan.v1, audio.spoken-adaptation.v1, audio.voice-direction.v1, video.shot-plan.v1.
- [ ] 7.3 Execution creates bounded candidate output in exact WorkflowStepAttempt only; no new business table.
- [ ] 7.4 Explicit candidate acceptance is required before downstream use; rejection/rerun remain attempt history.
- [ ] 7.5 Add Stage Handoff projection with run/attempt/node/schema/hash/summary and exact business refs only.
- [ ] 7.6 Do not copy entire prior run histories or re-summarize accepted upstream content on every stage.
- [ ] 7.7 Add currentness/hash/foreign-attempt authorization tests for handoff.

## 8. Persona Text recipes

- [ ] 8.1 Create portable default Text workflow for AI科技研发技术博主: Evidence Brief → Angle Lab → Outline → longform Master proposal → technical quality → humanize/refine Master proposal → title/hook → explicit final Master → optional Variant.
- [ ] 8.2 Create portable default Text workflow for 日常生活方式博主: fresh/evidence context → angle → story/outline → lifestyle Master proposal → lifestyle quality → grounded reflection/humanize → title/hook → explicit final Master → optional Variant.
- [ ] 8.3 Ensure intermediate accepted outputs feed downstream through Stage Handoff Contract, not fabricated Master revisions.
- [ ] 8.4 Preserve exact IdentitySnapshot creative profile/Skill/Preset/quality/model provenance in proposal/adopted Master edit summary/receipt.
- [ ] 8.5 Current-event factual claims in lifestyle flow require fresh Source/Data evidence; missing freshness blocks those claims or forces clearly labeled reflection/speculation mode.
- [ ] 8.6 User can complete supported Text flow without opening raw Workflow JSON or manually authoring a Prompt.

## 9. Text quality system

- [ ] 9.1 Add deterministic technical text checks: citation/evidence coverage where required, unsupported numeric/date claim checks using existing evidence mappings, structure/empty-section bounds, excessive repetition and configured hype/marketing phrase rules.
- [ ] 9.2 Add deterministic lifestyle checks: fact/speculation labeling, title/body consistency, excessive clickbait/hype and empty generic-reflection patterns where safely detectable.
- [ ] 9.3 Reuse existing fact/check infrastructure rather than creating a second fact truth.
- [ ] 9.4 Add optional model critic rubric projection for role fit/clarity/specificity; critic cannot override deterministic blockers.
- [ ] 9.5 Quality result binds exact Master/attempt/input hash and becomes stale when content changes.

## 10. Persona Graphic recipes and deterministic composition

- [ ] 10.1 Add Graphic recipe for AI科技研发技术博主: visual direction → card plan → optional image brief/generation/search → deterministic layout compose → Graphic Master adoption → verified renderer → Graphic QC → final render readiness.
- [ ] 10.2 Add Graphic recipe for 日常生活方式博主 with warm-magazine/documentary-photo/lifestyle-card defaults and lower text density.
- [ ] 10.3 `studio.graphic.layout-compose@1` accepts only validated semantic plan + exact preset + exact Material refs and emits canonical graphic.master.v2; normal path does not ask LLM for raw pixel positions.
- [ ] 10.4 Implement bounded layout primitives/templates with deterministic typography/spacing rules and stable output hashes.
- [ ] 10.5 Extend/reuse existing local renderer scope only through explicit capability contracts; no fake render success.
- [ ] 10.6 Renderer success produces actual image bytes through existing renderer acceptance/MaterialRevision provenance; composer output alone is not final media.
- [ ] 10.7 Typography/shape-only fallback is allowed only for presets/contracts that declare it; missing requested photo/image remains blocked.

## 11. Graphic quality system

- [ ] 11.1 Check canvas/order/count and required cover/first-card roles.
- [ ] 11.2 Check element bounds/minimum margins and declared non-overlap regions.
- [ ] 11.3 Check text overflow/estimated density and supported contrast/readability thresholds.
- [ ] 11.4 Check required image/diagram refs, duplicate misuse, exact rights and live byte integrity.
- [ ] 11.5 Check rendered dimensions/MIME/hash against canvas contract.
- [ ] 11.6 Produce contact-sheet/review projection for acceptance; scripts passing does not alone claim aesthetic quality.

## 12. Persona Audio recipe

- [ ] 12.1 Add one-click Audio output recipe usable from accepted Text Master or Video spoken script; Audio is not a new ContentUnit modality/Master schema.
- [ ] 12.2 Spoken Adaptation preserves facts but rewrites for speech rhythm and pronunciation.
- [ ] 12.3 Voice Direction resolves Persona audio preset, voice preference, pace/energy/pause/pronunciation notes and exact TTS route.
- [ ] 12.4 TTS execution remains existing `media.generate` / ProviderGenerationTask truth with exact plan/Unknown/no-auto-retry behavior.
- [ ] 12.5 Explicit provider-result acceptance creates MaterialRevision; no automatic Master mutation.
- [ ] 12.6 Optional subtitle/SRT is labeled estimated unless based on real timing/alignment evidence.

## 13. Audio quality system

- [ ] 13.1 Verify exact bytes/hash/MIME and nonzero bounded duration.
- [ ] 13.2 Use existing/local media tooling to detect gross clipping, excessive leading/trailing silence and configured loudness bounds where supported.
- [ ] 13.3 Verify requested voice/provider/model/rate contract from ProviderGenerationTask receipt.
- [ ] 13.4 If ASR is executable and user enables alignment, compare transcript to accepted spoken script and report differences; no hidden paid call on read/preview.
- [ ] 13.5 Audio QC result binds exact MaterialRevision hash and becomes stale on replacement/revocation.

## 14. Persona Video planning/handoff

- [ ] 14.1 AI科技研发技术博主 default Video planning uses technical script + architecture/demo shot planning + director.video.v1 package.
- [ ] 14.2 日常生活方式博主 default Video planning uses observational/story script + scene/B-roll planning + director.video.v1 package.
- [ ] 14.3 Optional TTS/material stages may prepare assets but final edit/composite stays external.
- [ ] 14.4 `stage.professional.prepare@1` remains the bridge; no new final-video engine or auto-dispatch.

## 15. Identity Workspace creative configuration UX

- [ ] 15.1 Add `创作配置` tab for Persona/Account/Series; Brand may expose constraints but Persona is the normal editable creative root.
- [ ] 15.2 Show Text/Graphic/Audio/Video cards with effective source revision and inherit/override/clear semantics.
- [ ] 15.3 Support Auto / Custom / Composed UI without raw JSON for normal users.
- [ ] 15.4 Show exact Studio Skill, Style Preset, Quality Profile, model policy and ordered Capability Memory extensions.
- [ ] 15.5 Account/Series override starts from a copied effective object, saves a complete replacement object and shows diff/origin before commit.
- [ ] 15.6 Show persona-specific readiness `ready|partial|blocked` and exact reasons.
- [ ] 15.7 Add Starter Persona gallery/preview and explicit initialize/fork actions.
- [ ] 15.8 Archived identities remain read-only and historical snapshots show frozen creative config.

## 16. Settings and inventory UX

- [ ] 16.1 Settings shows Studio Built-in Skills/Presets/Quality Profiles as read-only product inventory with exact version/provenance.
- [ ] 16.2 Installed Agent Skills stay separate external inventory; inventory does not imply executable runtime.
- [ ] 16.3 Capability Memory remains user-managed learned methods; no automatic import/export/overwrite with Studio Skills.
- [ ] 16.4 Provider/model settings remain global execution infrastructure and do not contain Persona style.
- [ ] 16.5 Inventory reads cause no provider/model/network/tool execution.

## 17. Learning and scope safety

- [ ] 17.1 Stage feedback for Persona A defaults to Project/Persona/Account/Series context and does not influence Persona B ordinary discovery.
- [ ] 17.2 “Save method” from an accepted Persona stage creates Capability Memory candidate at the narrowest provable creative scope.
- [ ] 17.3 Broadening a creative method across personas requires explicit owner action and exact diff/scope review.
- [ ] 17.4 Capability candidate promotion never rewrites Persona creative profile or Workflow defaults automatically.
- [ ] 17.5 Persona creative profile save remains a separate identity revision action.

## 18. Persistent contract tests

- [ ] 18.1 Add parameterized resource catalog tests for all built-in skills/presets/quality profiles/blueprints.
- [ ] 18.2 Add contract-to-resolver/executor consumption tests for every exposed tunable field.
- [ ] 18.3 Add broken reference/tool/version/provenance/secret/path negative tests.
- [ ] 18.4 Add persona creative-profile inheritance/replacement/snapshot tests.
- [ ] 18.5 Add auto/custom/composed resolution and unavailable explicit-pin tests.
- [ ] 18.6 Add Stage Handoff currentness/authorization/hash tests.
- [ ] 18.7 Add deterministic graphic composition/QC fixtures across both persona presets.
- [ ] 18.8 Add audio QC fixtures with synthetic local files; no paid provider needed for contract tests.
- [ ] 18.9 Add default Workflow validity/portability tests for both personas and all supported recipes.

## 19. Out-of-box E2E acceptance — AI科技研发技术博主

- [ ] 19.1 Initialize persona from starter blueprint in isolated DB and verify exact revision/default recipes/readiness.
- [ ] 19.2 Text: real configured chat model → research/angle/outline → article Master → quality/refine → final accepted text.master.v2; no raw Workflow/Prompt authoring.
- [ ] 19.3 Graphic: accepted content → visual direction/card plan → real/declared assets as needed → deterministic compose → renderer → actual PNGs → Graphic QC → accepted Graphic Master/render.
- [ ] 19.4 Audio: accepted technical content → spoken adaptation → calm-engineer voice direction → real TTS → accepted audio MaterialRevision → Audio QC.
- [ ] 19.5 Video: script/shot plan/director package → prepared external professional handoff only; no internal final-video claim.
- [ ] 19.6 Human rubric records factual grounding, engineering fit, clarity, specificity, visual readability and audio intelligibility with exact artifact/model hashes.

## 20. Out-of-box E2E acceptance — 日常生活方式博主

- [ ] 20.1 Initialize persona from starter blueprint in isolated DB and verify exact revision/default recipes/readiness.
- [ ] 20.2 Text: use a fresh authorized source for a current-interest example → observation/angle/story → lifestyle Master → quality/refine → accepted text.master.v2 with fact/speculation distinction.
- [ ] 20.3 Graphic: lifestyle content → warm visual direction/card plan → exact/generated/search/user images → deterministic compose → actual PNGs → lifestyle Graphic QC.
- [ ] 20.4 Audio: accepted reflection/story → spoken adaptation → warm-conversational direction → real TTS → accepted audio MaterialRevision → Audio QC.
- [ ] 20.5 Verify missing fresh source never creates a fabricated current-event claim; speculation mode is explicit.
- [ ] 20.6 Human rubric records naturalness, specificity, non-preachy tone, visual warmth/readability and audio conversational quality with exact hashes.

## 21. Real-provider quality gate and truthful readiness

- [ ] 21.1 Mock/fixture suites may prove contract safety but cannot mark creative quality accepted.
- [ ] 21.2 Before final feature acceptance, obtain explicit authorization for bounded real chat/image/TTS provider calls using configured local profiles.
- [ ] 21.3 Record provider/model/profile/runtime identity, prompt/config hash, output artifact hashes, quality checks and human rubric for every required acceptance sample.
- [ ] 21.4 If a required capability is unconfigured/unavailable, mark that modality blocked/partial instead of substituting mock or another unauthorized provider.
- [ ] 21.5 A passing sample proves the tested default is usable under that configuration, not universal objective quality.

## 22. Performance, security and closeout

- [ ] 22.1 Studio Skill metadata inventory and Persona creative summary remain lightweight; references/heavy editors/Graphic/Audio panels load on demand.
- [ ] 22.2 Run frontend TypeScript/Vite/FE-P1/bundle checks and preserve route lazy boundaries.
- [ ] 22.3 Run full backend/Ruff/persistent contract suites, OpenSpec strict and git diff-check.
- [ ] 22.4 Independent backend/data/security review: no second truth, no secrets/paths, exact snapshot/currentness, no hidden provider calls, scope isolation.
- [ ] 22.5 Independent product/UX review: both personas can complete Text/Graphic/Audio without raw JSON/Workflow authoring.
- [ ] 22.6 Independent creative-quality review on real artifacts; record limitations honestly.
- [ ] 22.7 Only after code/spec acceptance and separate local-data authorization, back up formal SQLite/media and initialize the two starter Personas idempotently; verify historical rows/hashes unaffected.
- [ ] 22.8 Canonical sync/archive/local commit/push remain separately authorized lifecycle actions.
