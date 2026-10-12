## Why

AIContentStudio already has the durable business truths needed for a serious content-production system: Brand → Persona → Account → Series identity, immutable IdentitySnapshot, Creation Recipe/Workflow, Stage Contracts and receipts, Content Master, Graphic Master and local renderer, ProviderGenerationTask for image/video/TTS, Capability Memory, Creative Execution/MCP, Channel Variant, Candidate/Review/Delivery and local packages.

The remaining product gap is now clear: the system can be controlled, but it is not yet a high-quality out-of-box creative studio. A new user still has to understand raw Workflow/Prompt/Skill concepts, and the product does not ship a role-native set of creative methods, style presets, default recipes and quality gates that reliably produces good Text, Graphic and Audio outputs.

The creative defaults also belong to the Content Persona, not to the owning User. One owner may operate many personas with completely different writing, visual and voice styles. User/owner scope remains appropriate for permissions, providers, models and generic technical methods; it MUST NOT become the default source of creative voice across personas.

This change establishes a Persona-native creative system and ships two starter personas:

1. **AI科技研发技术博主** — focuses on AI Agents, software architecture, developer tooling and engineering practice; evidence-led, engineering-first, explicit about trade-offs and limitations, low-hype and low-marketing.
2. **日常生活方式博主** — shares interesting things happening now, potentially interesting near-future developments and personal observations/reflections; curious, warm, conversational, story-aware and grounded rather than preachy or artificially profound.

The goal is a large step in usability: after configuring executable Chat/Image/TTS model capabilities, the user should be able to instantiate either starter persona and run a complete default production flow without authoring Skills, Prompts or Workflows. The result must be a real article, real rendered graphic/card set and real playable audio that pass built-in quality gates and can be reviewed/accepted through existing business truths. Video remains script/director-package first and is handed to external professional Agents such as Codex/Claude for final production.

## What Changes

- Add **Persona Creative Configuration** as versioned fields inside existing Brand/Persona/Account/Series profile JSON. No new identity table is introduced. Creative defaults inherit by the existing Brand → Persona → Account → Series replacement/origin semantics and freeze into IdentitySnapshot.
- Treat Persona as the primary creative-default scope. Account and Series may explicitly override a whole modality creative profile. Owner/User creative style is not an implicit fallback.
- Ship two versioned **Starter Persona Blueprints** as product resources and provide explicit idempotent preview/apply initialization. A blueprint creates a normal ContentPersona revision plus normal Persona workflow defaults; it is not a separate persona truth.
- Add a product-owned **Studio Creative Skill Pack**, separate from Installed Agent Skills and Capability Memory. Built-in Skills ship with the product and are version-pinned resources; learned/custom methods remain Capability Memory; external skills remain separate inventory.
- Borrow the useful Easel engineering pattern without copying its runtime model wholesale: small routing metadata, concise SKILL instructions, on-demand references, deterministic registered tools, machine-readable contracts, provenance metadata and contract validators.
- Add built-in versioned **Style Presets** and **Quality Profiles** for Text, Graphic and Audio. Persona creative profiles select these defaults; Account/Series can replace them.
- Add **auto / custom / composed** creative configuration:
  - auto chooses the persona blueprint/default Studio Skill, style preset and an executable existing provider/model route;
  - custom pins exact Skill/Preset/model/profile/parameters;
  - composed uses an explicit ordered method stack: one built-in Studio Skill plus zero or more exact Capability Memory revisions and bounded stage instructions. Installed Agent Skills are included only when explicitly selected and executable.
- Extend the Effective Stage Resolver so the preview and attempt receipt show the exact Persona/Account/Series creative profile, Studio Skill, Style Preset, method stack, provider/model and quality profile that will be used.
- Add a generic intermediate **creative method stage** for Research Brief, Angles, Outline, Visual Direction, Card Plan, Spoken Adaptation and Voice Direction. These are immutable WorkflowStepAttempt candidates, not new business tables.
- Add a bounded **Stage Handoff Contract** inspired by Easel's thin manifest approach: downstream stages consume exact accepted attempt/output IDs, hashes and concise summary/projection rather than re-deriving or copying the entire upstream context.
- Add deterministic registered Graphic composition and QC tooling. LLM/Skill determines message/visual plan; deterministic composition maps it into canonical `graphic.master.v2`, the existing local renderer produces real PNG bytes, and quality gates check geometry/coverage/contrast/density/rights before acceptance.
- Add an Audio production chain using existing TTS ProviderGenerationTask truth plus persona voice direction and deterministic audio QC. Audio remains MaterialRevision truth; this change does not create a fourth Content Master modality.
- Add Text quality gates for grounding/citations, structure, identity/style fit, anti-hype/anti-slop rules and target readiness. Model-assisted critic output is advisory unless explicitly defined as a gate; deterministic checks remain authoritative where possible.
- Add Graphic quality gates for real media, canvas completeness, bounds/overlap/text density, contrast/readability, output dimensions/hash/rights and contact-sheet/human review evidence for acceptance benchmarks.
- Add Audio quality gates for real bytes/MIME/duration, silence/clipping/loudness bounds, requested voice/rate contract and optional ASR transcript alignment when an ASR capability is executable.
- Add persona-specific default Creation Recipes for Text and Graphic plus one-click Audio output recipes; Video defaults stop at accepted script/shot/director package plus CreativeExecution preparation.
- Add readiness projection: Text Ready requires executable chat; Graphic Ready requires chat plus deterministic renderer and either usable generated/search/user image inputs as the selected style requires; Audio Ready requires TTS; current-event research that claims recent facts requires a fresh Source/Data capability and MUST NOT be fabricated from stale model knowledge.
- Add a Persona Creative Configuration UI under `/identities`, showing inherited/source scopes, automatic decisions, exact Skill/Preset/Quality Profile, default recipes and override scope. Settings continues to own providers/models/runtime; it also shows read-only Studio Skill/Preset inventory distinct from Installed Skills and Capability Memory.
- Add persistent contract validation inspired by Easel's validators: every built-in Skill contract/reference/tool key exists; every exposed tunable field is consumed; every persona blueprint references valid versioned resources; default recipes are valid/portable; deterministic tool references resolve; provenance/license metadata is present.
- Define real out-of-box acceptance for both starter personas: Text, Graphic and Audio journeys must produce actual reviewable outputs using explicitly authorized real configured providers during acceptance. Mock/fixture tests prove contracts only and cannot be used to claim creative quality.

## Capabilities

### New Capabilities

- `persona-creative-configuration`: Persona/Account/Series creative profiles, starter persona blueprints, auto/custom/composed resolution and role-native defaults.
- `studio-creative-skill-pack`: product-owned versioned creative Skills, style presets, deterministic tool references, provenance and validators.
- `creative-output-quality`: deterministic/media-aware quality profiles and truthful Text/Graphic/Audio readiness/acceptance evidence.

### Modified Capabilities

- `fe-f3b-content-identity`: add modality creative-profile fields to existing versioned identity JSON and IdentitySnapshot; Persona is the creative root and Account/Series replacement overrides remain explicit.
- `creation-recipe-stage-control-loop`: add intermediate creative-method stages, persona creative defaults, method-stack resolution, Stage Handoff Contract and persona-specific default recipes.
- `content-harness-registry`: register Studio Creative Skill/Preset/Quality resources and deterministic creative tools with exact versions without conflating them with external Installed Skills.
- `capability-memory`: Persona/Account/Series remain primary creative-method scopes; owner scope is not an implicit style source; explicit exact revisions may participate in composed configurations.
- `model-capability-routing`: auto mode uses existing executable route truth and exact capability readiness; explicit custom routes remain pinned and fail closed.
- `production-content-master`: accepted deterministic/AI-assisted persona creative stages preserve exact creative-profile/skill/preset/method-stack provenance when creating Master revisions.
- `material-library-v1`: real rendered Graphic/TTS outputs remain MaterialRevision truth with exact provider/renderer/rights provenance.
- `product-settings`: show Studio built-ins separately from Installed Agent Skills and Capability Memory; provider/model configuration remains global execution infrastructure.
- `fe-f0-f1-project-experience`: Persona selection/default recipes make the supported daily journey usable without raw Workflow authoring.
- `fe-p1-frontend-bundle-performance`: Persona creative configuration, preset pickers and quality panels remain lazy and do not eagerly load heavy production/editor bundles.

## Impact

Primary backend areas include identity profile validation/resolution, Creation Recipe resolver/learning, Stage Contracts, model routing, graphic composition/renderer integration, TTS/audio QC and product settings inventory. Primary frontend areas include Identity Workspace creative configuration, Creation Recipe method/preset controls, Graphic/Audio result panels and readiness.

The implementation should aim for **zero new business tables and zero schema migration**. Persona creative defaults fit existing revision `profile_json`; Workflow remains process truth; Capability Memory remains reusable learned-method truth; attempt receipts already freeze execution; MaterialRevision remains file truth. If a later implementation proves a new durable table is unavoidable, stop and return to specification review rather than adding it silently.

This change does not own the separate twelve-platform/seventeen-form schema rollout. It consumes the same Channel Registry and `stage.variant.adapt@1`. Before the multiplatform change applies, its current `stage.variant.propose` references must be corrected to `stage.variant.adapt@1`, and persistent parameterized contract tests must be allowed.

No live provider calls, formal Persona initialization, formal DB writes, professional-tool dispatch, public publication, canonical sync/archive, commit or push are authorized merely by drafting this OpenSpec.
