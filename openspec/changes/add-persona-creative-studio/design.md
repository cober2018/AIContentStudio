## Context

The current repository already implements most of the control-plane foundations that this change needs:

- Identity is persisted as Brand → Persona → Account → Series revisions; general identity/constraint context is resolved in that order and frozen into IdentitySnapshot, while creative-profile fields use the separate Persona → Account → Series hierarchy defined below.
- Workflow defaults already resolve Series → Account → Persona by modality and existing Units/Runs remain pinned until explicit rebind.
- Creation Recipe has stage contracts, effective preview, run-only overrides, attempt receipts, stage feedback, method promotion and `stage.variant.adapt@1` / `stage.professional.prepare@1` domain integrations.
- `stage.master.propose@1` can emit canonical text/graphic/video Master proposals, but the current default recipes use generic instructions and do not provide a mature persona-native creative method stack.
- Graphic has `graphic.master.v2`, a local Chromium renderer, exact render provenance and quality/readiness hooks, but there is no product-owned visual-direction/card-composition system that reliably turns a persona style into a good multi-canvas result.
- Native TTS exists through ProviderGenerationTask and the model capability router, but there is no persona voice-direction + audio QC production loop.
- Capability Memory already supports persona/account/series/project/channel/executor scopes, but built-in product methods are not a first-class inventory; Installed Agent Skills are an external inventory and may not be executable.
- Identity Workspace currently exposes positioning, audience, expression style, visual language, boundaries and raw workflow JSON. It does not expose role-native creative capability configuration.

The desired product is therefore not another workflow engine. It is a persona-native method/configuration/quality layer over existing truths.

## Goals / Non-Goals

**Goals**

- Ship two immediately useful Persona starter blueprints with distinct writing, graphic and audio behavior.
- Make Persona the default creative-style/method root while preserving Account/Series replacement overrides and Project/Run overrides.
- Let a new user run a good default Text/Graphic/Audio production flow without creating Skills, Prompts or Workflows.
- Keep every built-in method replaceable by exact custom or composed methods.
- Make automatic selection deterministic, visible and reversible.
- Borrow Easel's successful Skill engineering ideas: concise instructions, on-demand references, deterministic tools, output contracts, project handoff, tests and provenance.
- Keep stronger AIContentStudio truth boundaries: Skills do not directly mutate Master/Material/Variant/Approval/Delivery; domain services remain authoritative.
- Produce actual rendered images and playable audio, not plans/prompts masquerading as results.
- Create quality evidence that distinguishes deterministic contract success from subjective creative quality.
- Keep professional video execution external while providing strong script/shot/director packages.

**Non-Goals**

- User-level creative style defaults shared automatically across personas.
- A second Persona, Recipe, Material or Capability database.
- Importing Easel's complete Skill library or vendoring third-party copyleft code by default.
- Allowing arbitrary scripts inside a Skill package to execute in the API process.
- Automatically promoting feedback to persona identity or workflow defaults.
- Claiming current-event facts without fresh evidence.
- Building a new NLE/video compositor.
- Automatically publishing to social platforms.

## Decisions

### 1. Owner is infrastructure scope; Persona is creative scope

User/owner owns authentication, permissions, provider/model settings and all child identities. It is not the implicit creative style source.

Identity constraints resolve from the frozen identity hierarchy:

`Brand → Persona → Account → Series`

Creative profiles resolve through a separate hierarchy:

`Persona → Account → Series`

Persona is the normal root of creative behavior. Brand may provide organization-wide brand voice, values, boundaries, risk and compliance constraints in Effective Context, but Brand MUST NOT be the source of a default Studio Skill, Style Preset, Quality Profile, Persona Recipe, voice/graphic/writing style or creative method stack. Account/Series may explicitly replace persona modality creative profiles.

Owner-scoped Capability Memory may contain generic technical methods, but SHALL NOT be automatically selected as writing/visual/audio style for every Persona.

### 2. Extend existing identity JSON, not identity tables

Add four optional top-level fields to Persona/Account/Series IdentityProfile/profile JSON:

- `text_creative_profile`
- `graphic_creative_profile`
- `audio_creative_profile`
- `video_creative_profile`

Each is a bounded versioned object. Within the creative hierarchy, a missing field inherits; explicit null clears; an object override replaces the inherited object as a whole. No hidden deep merge is introduced.

Brand profile JSON remains valid for existing identity/brand fields, but MUST reject these four `*_creative_profile` fields as creative configuration. Brand constraints are resolved into Effective Context separately and cannot become creative-profile origin.

Each modality profile uses schema `persona.creative.<modality>.v1` and may contain:

- `configuration_mode`: `auto | custom | composed`;
- `style_preset_ref`;
- `quality_profile_ref`;
- `stage_method_defaults`: map of stage purpose → exact method selection;
- `model_policy`: auto route, one exact provider/model/profile binding, or an explicit ordered chain of exact provider/model/profile bindings;
- bounded defaults such as candidate count/length/aspect/voice/rate;
- `fallback_policy`: Auto-only policy for whether unavailable infrastructure may use the existing authorized capability route; Custom single-binding mode always blocks on an unavailable exact binding, while Composed mode uses only its explicitly declared ordered binding chain;
- optional `blueprint_ref` provenance.

#### Local voice catalog and audio control contract

This is a single-user local product. The voice catalog is one local inventory and does not introduce user roles, ownership isolation, sharing ACLs or multi-tenant voice records. A provider adapter MAY cache its catalog locally for search and readiness, but the cache is not the voice identity source; the provider/model-scoped exact `voice_id` remains authoritative.

The product exposes a user-facing `VoicePreset` projection over an exact audio binding. A preset may contain a display label, language, descriptive tags, provider/model/profile reference, exact `voice_id`, default rate and only adapter-declared supported parameters. A cloned or custom voice is registered manually by its exact provider/model-scoped ID and does not become executable merely because a label was entered. No credential or provider secret is stored in a preset or Persona profile.

Persona/Account/Series audio profiles MAY select a `VoicePreset` or an exact voice binding. Resolution SHALL freeze the effective provider, model, profile, `voice_id`, rate and supported parameter values into the IdentitySnapshot/Attempt receipt. Display name, tags and preview audio are explanatory metadata only and MUST NOT replace the exact ID. A voice ID is valid only for the provider/model/profile scope that declared it.

The normal audio UI SHALL show the selected preset, language/style summary, rate and a bounded preview/action surface. An explicit `高级设置`/Advanced Settings control SHALL expand the exact provider/model/profile, `voice_id` and additional adapter-supported controls. Unsupported or unavailable controls are hidden or visibly unavailable; the UI MUST NOT present a field that the executor ignores. A catalog with hundreds of voices SHALL use search, language/style filters, favorites and preview rather than an unbounded dropdown.

An exact Custom voice/model binding that is unavailable, mismatched or removed SHALL block execution. Auto and Custom Composition retain the existing bounded routing semantics: only Auto may use authorized policy fallback, and Composition may use only its predeclared exact chain. No mode may discover a different provider or voice at execution time.

Secrets, raw provider credentials, absolute local paths and executable code are invalid identity content.

IdentitySnapshot freezes these fields through the existing effective profile and field-origin checksum. Historical Units/Runs/Masters therefore keep the old creative profile automatically.

### 3. Starter Persona Blueprints are product resources, not hidden user records

Ship a versioned code/resource catalog with stable keys:

- `starter.ai-tech-engineer.v1`
- `starter.lifestyle-observer.v1`

Blueprint preview is read-only. Explicit apply creates normal ContentPersona + revision + normal default Workflow bindings. The blueprint key/version is stored inside the persona creative-profile provenance so apply can be idempotent without using the display name as identity.

A same-name manually created persona is never overwritten or adopted silently. A previously initialized blueprint persona may later be edited normally; re-running bootstrap shows diff and never resets user edits without explicit replace/fork choice.

New empty installations SHOULD offer the two blueprints immediately. Current formal local DB initialization is a separate explicit enablement action after code acceptance/backup.

### 4. Exact starter persona definitions

#### 4.1 AI科技研发技术博主

**Positioning**

关注 AI Agent、MCP/工具调用、LLM 应用工程、软件架构、开发工具与真实研发实践。优先回答“为什么这样设计、怎么落地、代价是什么、哪里还没解决”。

**Audience**

软件工程师、AI 应用开发者、技术负责人、对工程实践有兴趣的产品/创业者。

**Expression**

- 工程师第一视角；
- 证据/代码/架构/项目经验优先；
- 少营销话术、少夸张感叹、少“颠覆/赋能/王炸/必看”；
- 明确边界、失败、未知和 trade-off；
- 结构清晰但不写成模板味很重的八股；
- 专有名词可用，但第一次出现时提供必要解释；
- 当前事实必须有时间/来源边界。

**Visual**

技术编辑部/架构图/信息图优先；中性或深色底、克制 accent、高信息可读性；图表/流程/代码结构优先于无意义装饰图。

**Audio**

冷静、清晰、中慢速、低营销能量；技术词发音清楚；适合知识解说/技术播客旁白。

#### 4.2 日常生活方式博主

**Positioning**

分享正在发生的值得注意的事情、未来可能有趣的趋势/活动/变化，以及日常生活中的观察、体验和感悟。

**Audience**

对城市生活、文化/科技变化、未来趋势、体验与自我成长保持好奇的普通读者/观众。

**Expression**

- 像真实朋友聊天，具体、轻松、有观察；
- 允许个人感受与不确定，不装权威；
- 从具体场景/细节进入，不强行上价值；
- 对“未来可能”明确区分事实、推测和想象；
- 不虚构亲历、不伪造实时事件；
- 少鸡汤、少说教、少故作深刻；
- 标题可以有好奇心，但不用夸张欺骗式 Hook。

**Visual**

自然摄影/暖色编辑感/杂志拼贴/轻卡片；生活细节、场景和人物感优先于复杂信息图；留白与节奏感比信息堆叠重要。

**Audio**

自然、温暖、口语化、中等语速；适合生活观察、轻故事和未来趣事的旁白。

### 5. Studio Creative Skill Pack is a third method inventory

There are three clearly separated method inventories:

1. `studio_builtin_skill` — product-shipped, versioned, available without user installation;
2. `capability_memory` — user/persona/account/series learned or authored reusable methods;
3. `installed_agent_skill` — external local Agent Skill inventory, executable only with a proven runtime/binding.

Equal names do not imply equivalence or override. Promotion in Capability Memory never edits Studio built-ins or Installed Skills.

### 6. Easel-inspired Skill package contract, adapted to AIContentStudio

Each built-in Skill lives as a versioned resource package, for example:

```
studio_skills/studio.text.longform/
  SKILL.md
  STUDIO-CONTRACT.json
  STUDIO-META.md
  references/
    structure.md
    quality-rules.md
  tests/
    fixtures.json
```

Optional deterministic implementation lives in registered application tools/rules, not as arbitrary executable code loaded from SKILL.md.

**SKILL.md**: concise “how to do it” instructions and method boundaries.

**STUDIO-CONTRACT.json** freezes:

- key/version;
- modality/purpose;
- compatible stage schemas;
- required context;
- input/output schema keys;
- tunable fields/defaults;
- prompt sections;
- referenced registered tool/rule keys and versions;
- style compatibility;
- quality-profile compatibility;
- maximum context/output bounds.

**STUDIO-META.md** records provenance, method sources, whether code/rules were self-developed/adapted/referenced/vendored, and license obligations. Referencing Easel or another project as method inspiration does not imply copying its code.

References are read only when the selected skill needs them. Routing inventory loads only bounded metadata/contract summaries.

### 7. Initial Studio Skill catalog

First-version built-ins:

**Research / planning**

- `studio.research.evidence-brief@1`
- `studio.research.angle-lab@1`

**Text**

- `studio.text.outline@1`
- `studio.text.longform@1`
- `studio.text.answer@1`
- `studio.text.social-short@1`
- `studio.text.humanize@1`
- `studio.text.title-hook@1`

**Graphic**

- `studio.graphic.visual-director@1`
- `studio.graphic.card-plan@1`
- `studio.graphic.image-brief@1`
- `studio.graphic.layout-compose@1` (deterministic registered tool contract)
- `studio.graphic.qc@1` (deterministic registered quality tool)

**Audio**

- `studio.audio.spoken-adapt@1`
- `studio.audio.voice-director@1`
- `studio.audio.tts@1` (method wrapper over existing TTS ProviderGenerationTask)
- `studio.audio.qc@1`

**Video planning/handoff**

- `studio.video.script@1`
- `studio.video.shot-director@1`
- `studio.video.director-package@1`

This is a minimum product pack, not a forever-closed list. Adding a built-in Skill requires contract/provenance/validation and versioning.

### 8. Versioned Style Presets are separate from Skills

Skill answers “how to perform the creative task.” Style Preset answers “what creative language this Persona wants.”

Initial Text presets:

- `studio.text.deep-technical@1`
- `studio.text.engineering-explainer@1`
- `studio.text.observational-lifestyle@1`
- `studio.text.reflective-lifestyle@1`
- `studio.text.concise-social@1`

Initial Graphic presets:

- `studio.graphic.technical-editorial@1`
- `studio.graphic.architecture-diagram@1`
- `studio.graphic.clean-infographic@1`
- `studio.graphic.warm-magazine@1`
- `studio.graphic.documentary-photo@1`
- `studio.graphic.lifestyle-cards@1`

Initial Audio presets:

- `studio.audio.calm-engineer@1`
- `studio.audio.clear-explainer@1`
- `studio.audio.warm-conversational@1`
- `studio.audio.reflective-story@1`

Preset content is bounded declarative configuration/instruction, never credentials or executable code.

### 9. Quality Profiles are versioned and media-specific

Initial quality profiles:

- `studio.quality.text.technical@1`
- `studio.quality.text.lifestyle@1`
- `studio.quality.graphic.editorial@1`
- `studio.quality.graphic.lifestyle@1`
- `studio.quality.audio.explainer@1`
- `studio.quality.audio.conversational@1`

A Quality Profile declares required deterministic checks, optional model critic dimensions, blocking/warning thresholds, and human-review requirements.

Deterministic checks own facts they can prove. A model critic MUST NOT mark missing citations, invalid rights, corrupt bytes or failed renderer output as safe.

### 10. Auto / custom / composed configuration

Every persona creative modality profile can choose one resolution mode.

**Auto**

- Uses the exact inherited Persona/Account/Series defaults.
- Uses exact built-in skill/preset/quality refs from the persona blueprint/profile.
- Uses existing model-capability routing to select only an executable route.
- Does not scan unrelated providers or Capability Memory for a hidden “best” method.
- If a preferred route is unavailable and fallback policy permits, normal configured capability routing may choose its authorized fallback and preview explains it.

**Custom**

Pins one exact provider/model/profile binding together with exact skill/preset/quality refs and bounded default parameters. If that exact binding is unavailable or changes before execution, it blocks and is never silently replaced by another provider/model/profile.

**Composed / Custom Composition**

Uses an explicit ordered method stack:

```
base: one studio_builtin_skill@version
extensions:
  - exact capability_memory_revision_id
  - exact capability_memory_revision_id
optional_external:
  - exact installed skill descriptor only if executable
stage_instruction: bounded text
```

It MAY also declare an explicit ordered model binding chain:

```text
primary: exact provider/model/profile binding
fallbacks:
  - exact provider/model/profile binding
  - exact provider/model/profile binding
```

The chain is part of the frozen user/Persona configuration. Execution may select only the first executable binding in this declared order, and the attempt receipt records the selected binding and bounded fallback reason. There is no undeclared provider discovery, hidden merge of applicable memories, or temporary substitution. The user/Persona profile selects exact revisions and order.

For a deterministic Tool/Rule Stage, the method stack has a narrower contract. A Capability Memory extension is executable only when its exact revision resolves to a validated `workflow.stage.recipe.v1` whose `plugin`, `plugin_version` and `stage_schema` match the current node and whose `config_patch` contains only fields declared and consumed by that Stage Contract. Patches are applied in the declared method order, then the explicit run override is applied last; the final effective config and every exact source/revision/content/arguments/metadata/rendered hash are frozen into the resolution and attempt receipt. Free-form method instructions are never interpreted as deterministic parameters and never trigger a provider call. An Installed Agent Skill is usable only when its exact selected runtime and Stage adapter are executable; otherwise the Stage blocks with a typed reason and requires an explicit AI Stage for model-assisted transformation.

Deterministic layout/render therefore consumes only typed parameters explicitly supported by its Stage Contract. Within the frozen creative profile, method patches apply in their declared order as defaults; saved Project Stage fields override these defaults, and the run-only override wins last. A deterministic extension MUST NOT replace the built-in base method, output/package schema or model/provider routing selector. The resolver validates the final selected method against the final output schema (including Director `package_schema`) after run overrides, not against an earlier configuration. Persona readiness SHALL apply the same matching-recipe validation to every participating deterministic node in Graphic, Audio and Video recipes, rather than claiming a softer readiness than the actual Stage. Any AI transformation, semantic rewrite or method that cannot be represented by those parameters belongs in a visible explicit AI Stage and is not hidden inside layout, rendering or other deterministic tools.

### 11. Resolution precedence is visible and deterministic

Hard safety/business constraints always win. Creative configuration resolution is:

1. Brand constraint context plus Stage Contract and rights/evidence/approval/side-effect rules;
2. exact target/channel profile hard requirements;
3. run-only explicit override;
4. saved Project Workflow Stage configuration;
5. effective Series creative profile field;
6. effective Account creative profile field;
7. effective Persona creative profile field;
8. built-in blueprint/product fallback;
9. existing allowed provider-route fallback.

Because identity object fields replace as a whole, effective identity supplies one exact modality creative profile plus origin from Persona/Account/Series. The resolver does not deep-merge those scopes behind the user's back, and Brand constraint context cannot become that origin. The built-in/provider fallback steps apply only to Auto mode; Custom single-binding mode and Composed/Custom Composition mode remain bounded by their explicit bindings.

Effective Preview shows every layer, exact source ID/revision/hash and final selected values.

### 12. Add an intermediate Creative Method Stage

`stage.creative.method@1` is a model-backed, human-reviewed Stage Contract for non-authoritative intermediate artifacts.

It requires an exact selected Studio Skill / composed method stack and an output schema supported by that skill.

Initial output schemas:

- `research.brief.v1`
- `creative.angles.v1`
- `content.outline.v1`
- `graphic.visual-direction.v1`
- `graphic.card-plan.v1`
- `audio.spoken-adaptation.v1`
- `audio.voice-direction.v1`
- `video.shot-plan.v1`

Successful execution creates immutable candidate output in WorkflowStepAttempt. Explicit accept marks that exact attempt candidate as eligible upstream input; it does not create another business entity/table.

### 13. Stage Handoff Contract is a thin exact projection

Downstream stages SHALL receive declared accepted upstream outputs through a bounded projection:

- run ID;
- step/attempt ID and attempt number;
- node/plugin/stage schema;
- output schema;
- output hash/candidate hash;
- concise summary;
- exact business-entity refs/hashes if the output points to Master/Material/Variant;
- optional bounded selected content only when the downstream skill contract declares it necessary.

The resolver SHALL NOT re-summarize all previous stages on every call or copy complete unrelated attempt histories into prompts.

This adopts Easel's “thin manifest, full payload stays at source” principle using AIContentStudio's stronger persisted objects/hashes instead of a new manifest file/table.

### 14. Default Text recipes

#### AI科技研发技术博主 · Text

1. Evidence Brief — `studio.research.evidence-brief@1`
2. Angle Lab — `studio.research.angle-lab@1`
3. Outline — `studio.text.outline@1`
4. Draft Master proposal — `studio.text.longform@1` + deep-technical preset
5. Text quality gate — technical quality profile
6. Refine Master proposal — `studio.text.humanize@1` with accepted Master context
7. Title/Hook candidates — `studio.text.title-hook@1`
8. Explicit final Master acceptance/save
9. optional `stage.variant.adapt@1`

#### 日常生活方式博主 · Text

1. Fresh Context / Evidence Brief
2. Angle Lab focused on “why this is interesting to ordinary life”
3. Outline / story spine
4. Draft Master proposal — `studio.text.longform@1` + observational-lifestyle preset
5. Lifestyle quality gate
6. Humanize/reflection pass — grounded and non-preachy
7. Title/Hook candidates — curious, not clickbait
8. Explicit final Master acceptance/save
9. optional Variant stage

Current-event claims require fresh Source/Data evidence. “未来可能” content must label inference/speculation separately from confirmed facts.

### 15. Default Graphic recipes

#### AI科技研发技术博主 · Graphic

1. Accepted source Text/Graphic context
2. Visual Direction — technical-editorial / architecture-diagram
3. Card Plan — key conclusion per canvas, diagram/data/image need
4. Optional exact image generation/search for one or more allowed visual slots
5. Deterministic Layout Compose → canonical `graphic.master.v2`
6. Explicit Master adoption
7. Existing verified local renderer → actual PNG MaterialRevision(s)
8. Graphic QC → bounds/overlap/density/contrast/real bytes/rights
9. Explicit render binding / final Master readiness
10. Variant/Review as normal

#### 日常生活方式博主 · Graphic

1. Accepted source content/context
2. Visual Direction — warm-magazine/documentary-photo/lifestyle-cards
3. Card Plan — fewer words, stronger scene/photo rhythm, intentional whitespace
4. Exact image generation/search/user material selection
5. Deterministic Layout Compose
6. Render real PNGs
7. Lifestyle Graphic QC
8. Explicit final acceptance

The system SHALL support a typography/shape-only fallback for applicable card styles when no image provider is available; it MUST NOT pretend a missing requested photo/illustration exists.

### 16. Deterministic Graphic composition and render quality

The model/Skill creates semantic plans, not free-form pixel coordinates.

`studio.graphic.layout-compose@1` maps a validated Graphic Plan + Style Preset + exact asset refs into a bounded set of known layout primitives/templates and canonical `graphic.master.v2` coordinates. This avoids asking an LLM to invent arbitrary pixel layout as the normal path.

For new Visual Direction/Card Plan Previews, the exact resolved Graphic Style Preset's role-aware composer visual requirements SHALL also be explicit in the provider-visible output contract and frozen Prompt hash. As explicitly authorized on 2026-10-08, warm-magazine requires an exact image reference on the cover and permits `visual_type=none` on body cards; documentary-photo still requires an exact image on every card. Diagram fallback remains available only where the preset declares `shape_only`. Preview, composition and current Graphic QC use the same server-owned policy. Composition provenance and new QC input hashes bind that policy so older checks cannot silently remain current after it changes. These are planning constraints, not a render/rights/quality attestation. A missing required cover/per-card image remains an explicit incomplete-plan warning/blocker, never an invented reference or silent preset substitution. Historical resolved requests, accepted plans, Masters and frozen check requirements remain unchanged; a later composition Stage's explicit preset override still has its own Preview and validation.

The existing renderer remains renderer truth. Composer output does not claim final bytes. Actual PNGs are created/accepted through existing renderer/MaterialRevision provenance.

Graphic QC MUST at least validate:

- canvas/order/count;
- element bounds and minimum margins;
- text overflow/estimated density;
- overlap rules;
- contrast/readability threshold for supported text/background cases;
- missing/duplicate required visual refs;
- exact dimensions/MIME/hash of rendered bytes;
- live material rights;
- cover/first-card presence where the selected target/preset requires it.

### 17A. Image and Audio share one multimedia generation contract

Image generation and Audio generation are one product surface in this change, not two unrelated provider integrations. Both use the same sequence:

`user configuration → Effective Preview → exact provider/model/profile binding → generated candidate output(s) → byte/provenance validation → explicit user acceptance → existing Material/Master truth`.

The shared surface SHALL expose only adapter-declared controls, compile Persona/Stage settings into a server-derived request, freeze the effective configuration and runtime receipt, and keep generated outputs out of durable Master/Material truth until explicit acceptance. A provider adapter SHALL declare its modality, input/output schema, MIME constraints, supported controls, candidate-count behavior and whether it can return multiple outputs natively. Provider-specific fields are not shown or silently consumed when the selected adapter does not support them.

For images, the normalized request supports a bounded candidate count (1–4), aspect ratio/size, optional exact reference assets and a server-built prompt assembled from the accepted visual brief/card plan plus the selected Persona/profile. Native multi-output is preferred. If a selected Auto route cannot return multiple candidates, bounded fan-out is allowed only under the already-approved Auto policy or an explicitly declared Custom Composition; each attempt and candidate records the exact binding and index. A Custom single binding never changes provider or model merely to obtain a larger batch. All image candidates use the same normalized output contract before the user chooses one or more for explicit MaterialRevision acceptance.

For audio, the normalized request supports an adapter-declared voice preset or exact voice binding, rate and any supported advanced controls. The default candidate count is one unless the selected adapter explicitly supports more. Audio uses the same candidate/acceptance surface, but remains a MaterialRevision output rather than a fourth Master modality. Voice IDs are provider/model/profile-scoped and exact; display labels never become identity.

The normal UI shows common image/audio controls and a candidate selection surface. An explicit Advanced Settings action reveals exact binding and adapter-supported fields. Preview never calls a provider. Execution re-resolves and fails on any binding/configuration hash drift; it never silently swaps a model, ignores a requested field or accepts provider bytes that do not match the normalized contract.

### 17B. Registered CPA images and ChatGPT website images are explicit scope

These requested routes belong to the unified multimedia surface. They are not complete merely because MiniMax images work or the CPA chat route is healthy. The latest 2026-10-08 human decision replaces ChatGPT browser automation with a manual prompt-and-upload branch. Earlier selected-Chrome and browser-Agent records are historical smoke evidence, not current implementation requirements.

**Registered CPA image adapter:** reuse the existing registered provider/model/profile configuration and its protected credential and explicitly trusted endpoint. Do not copy the API key into a media binding, add another Provider truth, force official Google/xAI credentials or infer image capability from a model's family/name. The image binding must freeze a versioned protocol contract, exact model and supported fields/counts. Its protocol builder must consume the accepted visual brief and effective image settings, expose the safe effective prompt before execution, and parse only that contract's bounded output. Never probe multiple endpoints or change model/protocol after possible dispatch.

The previously examined CPA revision `fd48ea68` exposes `/v1/images/generations`, but its handler explicitly validates image models; this alone does not prove `grok-4.7` or `gemini-3.8-flash-high` can use it. A protocol/model pair must be declared and validated independently. If the configured CPA model has no implemented executable image protocol, preview reports the missing binding and execution blocks. Current registered chat selections are preserved.

Successful CPA outputs normalize into the same existing image task/candidate schema as MiniMax: exact indexes, validated PNG/JPEG/WebP bytes, dimensions, MIME and hashes, signed runtime/config/provenance, immutable candidate storage and explicit chosen MaterialRevision acceptance. URL-only responses are not accepted as image bytes or downloaded from arbitrary hosts. Custom pins, native count versus declared fan-out, Unknown/no replay, rights and explicit Master binding remain unchanged. No new durable object or migration is allowed for this route.

Implementation protocol `cpa.images@1` / `cpa.images.b64.v1` explicitly references a registered profile ID and its exact model, not a second URL/key. It uses one POST `/images/generations` under the existing registered base URL with `model`, server-built `prompt`, `n` (1–4), deterministic `size` and `response_format=b64_json`. It accepts exactly `n` `data[].b64_json` images (PNG/JPEG/WebP), at most 5MiB per image and the existing 8MiB total image response cap, with full decoding and exact requested geometry. No URL fallback or endpoint/model discovery is supported. The profile must explicitly declare image generation and the exact protocol; merely having a registered chat model does not opt it in. Effective prompt/protocol/hash are frozen in the existing task plan and shown before dispatch; no real-provider availability or quality is implied by this offline protocol implementation.

**ChatGPT manual image generation:** the normal image-generation selector exposes `ChatGPT（手动生图）` alongside existing automatic routes, without presenting it as an executable API model. Selecting it replaces the automatic Generate action with a complete prompt preview, one-click copy and an image drop/file-picker area. It never enters Auto routing or a provider fallback chain. The safe prompt is deterministically assembled from the accepted visual brief/card plan, Persona style, usage, aspect/size, bounded requested count (1–4), reference obligations and output constraints; constructing/previewing/copying it makes no model request. Manual execution does not promise that the website followed those constraints: returned bytes are checked independently.

Reuse existing CreativeExecution Package/source/rights/output/staging/acceptance services with explicitly human external execution; do not create a ProviderGenerationTask, browser integration, new durable object or migration. Freeze the exact eligible current Master/Variant source, prompt snapshot/hash and bounded image output contract in the existing package before accepting returned uploads into its staging. Prompt/source/config changes require a new current package rather than mutating the frozen package. Missing source/rights prerequisites are explained using the existing domain rules, not resolved by fabricating a source or starting an automatic provider. Copying the prompt only prepares the handoff and cannot mark the execution result-ready or accepted.

The user independently pastes the prompt into ChatGPT, downloads the result and drags or selects one or multiple local files in AIContentStudio. Drop immediately adds pending rows and starts upload into the temporary candidate area; each row exposes uploading/validating/ready/error state, thumbnail, MIME/dimensions and selection/removal controls. Failed or invalid files stay visibly failed and cannot be accepted, without discarding other valid candidates or producing partial accepted materials. The server enforces the frozen MIME/dimension/count/size contract, reads and hashes actual bytes, and preserves immutable output attempts and exact candidate identity. Removing a pending/candidate row is not deletion or revocation of an accepted MaterialRevision. Existing required-role/min-max-count and stale/history rules are unchanged.

Provenance explicitly records **user-declared ChatGPT generation**, the frozen prompt/package and uploaded output hashes plus human decisions. It does not attest the actual website model, runtime, prompt consumption or provider response; no fabricated LLMRun or native provider receipt is allowed. Explicit selection and `接受入库` call the existing acceptance path to create MaterialRevision with `source_kind=external_execution`, live derived-rights revalidation and idempotent exact-output decisions. Merely dropping/uploading a file creates no MaterialRevision. Accepted material does not automatically bind/save Master or modify Variant/Candidate/Approval/publication; Master reference/save stays explicit.

AIContentStudio neither requires nor operates a browser session for this branch: no Cookie extraction, browser-profile reading, website automation, automatic image download, credential copy or request replay. Browser login/errors are handled by the user on the external site, not treated as application provider readiness or automatically switched to CPA/MiniMax. Old uncertain browser-smoke submissions remain historical and are not replayed. Product acceptance requires the copy → drag-upload → exact selection → explicit MaterialRevision chain, not just a successful external image or prompt copy.

```text
ChatGPT（手动生图） → complete prompt → one-click copy
                                       ↓ user operates ChatGPT
temporary candidates ← drag/upload actual downloaded image files
        ↓ validate + preview + select
explicit 接受入库 → MaterialRevision → separate Master reference/save
```

### 17. Audio is a Material output, not a fourth Master modality

Implementation binding: the additive `media.generate@4` Stage consumes exact accepted spoken/voice-direction attempts and the resolved provider/model/profile, voice ID and rate. Native TTS does not consume creative instruction text; those instructions belong to preceding AI methods, not to the synthesized script. MiniMax maps the exact voice binding to `--voice`/`--speed` and signs `studio.audio.tts-applied.v1` in the existing result receipt. Its local parameter-capability probe accepts declared flags from either stdout or stderr of a successful bounded `speech synthesize --help`; nonzero exit, missing flags and timeout still block, and help never attests a real voice or generated output. `stage.audio.qc@1` freezes a file QC report in an ordinary Attempt, never a synthetic Master check. Previous media Stage contracts and historical parameterless receipts keep their prior semantics. Director method binding uses additive `stage.professional.prepare@2`, with method instructions as bounded package constraints and explicit aspect ratio as a saved-Master assertion, not a hidden reshape.

Audio planning chat and native TTS are separate capabilities: the spoken/voice AI Stage exposes its own exact chat route and receipt, while native speech enforces the frozen Audio profile's TTS binding/ordered chain. Preview exposes both purposes. The planning chat route never substitutes for a custom TTS pin and cannot attest voice/model execution or audio quality.

Native TTS Stage preparation uses the existing bounded local execution-readiness check before comparing its exact binding with the domain routing plan. It does not synthesize media or make a remote Provider call. Ordinary Persona/configuration inventory resolution remains unprobed; an inventory-only `credential_continuity_unverified` projection is not an execution plan and must not be used to reject a locally executable Stage before its continuity checks.

The additive `media.generate@4` wait control uses the existing routing range of 1–300 seconds, retaining the 25-second default. Its Stage schema and `_tts_config` must agree; no additional 25-second ceiling may reject a supported explicitly configured wait. The selected route's existing smaller limit is still enforced before dispatch and is never raised or silently clamped. The exact wait belongs to the frozen configuration/request; a later change requires a new Preview. This correction does not change historical media v2/v3 contracts, formal model settings, receipt verification or Unknown/no-replay behavior.

An explicitly authored Project Stage or run-only native `selected_profile` follows the approved higher-scope precedence, not automatic fallback. Preview/Attempt preserve the original Persona policy, exact selected binding, before/after difference and binding origin. The explicit binding remains fail-closed on drift/unavailability; without that selection, the Persona Custom pin/declared chain remains authoritative. Director user instruction parameters are bounded to2000 characters in both resource and Stage contracts; built-in method documentation retains its separately bounded package-constraint transfer.

Audio production attaches to accepted Text or Video script content.

Default chain:

1. Spoken Adaptation — transform written text into speakable script without changing facts;
2. Voice Direction — persona/style → voice characteristics, pace, energy, pause policy, pronunciation notes;
3. TTS — existing `media.generate`/ProviderGenerationTask with exact TTS provider/profile and prompt/script;
4. explicit Provider result acceptance → MaterialRevision audio;
5. Audio QC;
6. optional subtitle/SRT output when provider/timing support is real;
7. user accepts the audio result for use/export.

Audio QC MUST include real byte/hash/MIME/duration checks and, where local tooling supports it, clipping/silence/loudness checks. If ASR is executable, optional transcript alignment may compare the generated speech with the accepted spoken script. A generated SRT MUST be labeled estimated unless based on real timing/alignment evidence.

Optional local alignment is a separately named Audio Recipe, not a rewritten default. It inserts `stage.audio.asr@1` after accepted TTS and before QC. The existing local MLX adapter consumes supported WAV bytes (maximum30MiB/600seconds/120second timeout); unavailable/unsupported inputs block rather than convert silently or discover a cloud route. Preview only freezes input/runtime. Automatic continuation stops with this Stage pending, and only explicit execution may infer. Real transcript/at most256segments are stored in the immutable Attempt, bounded without truncation. Explicit generic Attempt acceptance is required before QC may consume its exact same-run/material/task/script/runtime proof and export verified segment-timing SRT; no Audio/Video Master or duplicate ASR/media table is created. Legacy saved Video ASR receipt reuse remains available and cannot be mixed ambiguously with the new direct-Stage handoff.

### 18. Video remains planning/director first

Both starter personas get video planning defaults:

- script method;
- shot/B-roll plan;
- exact asset requirements;
- voice/music direction where relevant;
- `director.video.v1` package;
- optional prepared CreativeExecution.

Final video editing/compositing remains external professional execution (Codex/Claude + Premiere/AE/Resolve/etc.). This change does not create a new internal final-video engine.

### 19. Persona-specific readiness, not one global “configured” badge

For each Persona and modality the UI returns:

- creative profile source/revision;
- recipe/default workflow source;
- required built-in skills/presets/quality profiles;
- selected model/provider route;
- deterministic tool/renderer availability;
- optional external skill availability;
- `ready | partial | blocked` and exact reasons.

Examples:

- Chat configured, image/TTS missing: Text ready; Graphic may be partial if typography-only path is supported; Audio blocked.
- TTS configured but Persona has an unavailable Custom voice/model pin: Audio is blocked until the pin changes; only Auto policy or an explicitly declared Custom Composition chain may select another binding.
- A Persona voice preset may be displayed as ready only when its exact provider/model/profile and voice ID are currently compatible; a display label alone never makes a cloned voice executable.
- Lifestyle “current events” recipe without fresh source: creation can proceed only as reflection/speculation without factual current-event claims, or the evidence stage blocks those claims.

### 20. Built-in quality does not equal fabricated quality proof

Contract tests and controlled fixtures prove schemas/safety, not that content is “good.”

Before marking this change fully accepted, run an explicitly authorized real-provider quality acceptance using the current formal configured models. Each starter persona must complete representative Text, Graphic and Audio journeys.

Human review uses fixed rubric dimensions:

**Text**: factual grounding, role fit, clarity, structure, specificity, non-generic voice, headline/content alignment.

**Graphic**: role/style fit, hierarchy, readability, information/visual balance, real asset quality, rendering cleanliness.

**Audio**: intelligibility, role/voice fit, pacing, prosody, pronunciation, absence of obvious clipping/silence defects.

The acceptance report records model/provider/profile and artifact hashes. A single passing sample does not become universal quality truth; it proves the shipped default is usable under that tested configuration.

### 21. Feedback improves a Persona, not the User globally

Stage feedback remains ProjectEvent evidence. “Save what worked” defaults to Project or the current Persona/Account/Series scope.

A reusable creative method captured from Persona A defaults to the narrowest Persona/Account/Series context that produced it. It is not automatically visible as an ordinary default for Persona B.

Broadening a creative method across personas requires explicit owner action and must remain a Capability Memory scope decision, not an implicit shared style.

Identity creative profile changes also remain explicit versioned saves. Capability Memory does not silently rewrite Persona profile JSON.

### 22. Identity UX owns creative defaults; Settings owns infrastructure

Add a `创作配置` tab for Persona/Account/Series:

- Text / Graphic / Audio / Video cards;
- inherited source and revision;
- Auto / Custom / Composed selector;
- built-in Skill / Style Preset / Quality Profile;
- exact Capability Memory extensions in order;
- provider/model policy without exposing credentials;
- default Recipe preview;
- readiness and blockers;
- diff before save.

Account/Series UI starts from the effective inherited profile and saves a complete replacement object when the user chooses override, preserving existing non-deep-merge semantics.

Product Settings shows:

- Studio Built-in Skills/Presets/Quality profiles as read-only versioned inventory;
- Installed Agent Skills as separate external inventory;
- Capability Memory link/surface as user-managed methods;
- Provider/model configuration as existing infrastructure truth.

### 23. Contract validators are first-class gates

Add persistent validators/tests inspired by Easel's `validate_skills` and command-drift checks, adapted to AIContentStudio:

- Skill package structure/frontmatter/contract bounds;
- broken reference links/resources;
- missing provenance/license metadata;
- contract references to unknown Stage schemas/tool/rule keys;
- persona blueprint references to missing skill/preset/quality/recipe versions;
- exposed tunable fields not consumed by resolver/executor;
- deterministic tool config fields not accepted by implementation;
- default recipe graph/portability errors;
- style/quality preset schema drift;
- no raw secret/path in shipped resources.

These are repository tests, not one-time acceptance scripts.

### 24. Multiplatform integration remains one downstream target system

This change consumes server Channel Registry descriptors and existing `stage.variant.adapt@1` only.

The separate `complete-multiplatform-content-handoff` change owns twelve-platform/seventeen-form payload/profile/package expansion. Before it applies:

- all `stage.variant.propose` wording MUST be corrected to `stage.variant.adapt@1`;
- its “no new test code” rule MUST be replaced by small parameterized persistent contract tests plus concentrated smoke.

Persona creative configuration may influence target adaptation instructions through the effective IdentitySnapshot, but Channel Profile hard constraints remain authoritative and no per-persona channel engine is created.

## Migration / Rollout Plan

### Phase 0 — reconcile active change dependencies

- Review current Creation Recipe implementation and retain current CRs schema/runtime behavior.
- Fix the two multiplatform spec blockers before that change is applied.
- Do not archive or rewrite current active change sources as part of this feature.

### Phase 1 — built-in catalogs and validators

- Add Studio Skill/Preset/Quality/Persona Blueprint resource catalogs and provenance.
- Add registry/inventory and persistent validation tests.
- No production behavior switch yet.

### Phase 2 — identity creative profiles and starter personas

- Extend IdentityProfile validation/effective projection and Identity Workspace creative tab.
- Add starter persona preview/apply in isolated DB tests.
- Add persona/account/series replacement/inheritance regression.

### Phase 3 — creative method resolution and intermediate stages

- Add `stage.creative.method@1`, Stage Handoff projection and Studio Skill method-stack resolution.
- Preview must prove exact skill/preset/profile/model/memory refs and zero side effects.

### Phase 4 — Text out-of-box loop

- Implement both persona Text recipes and Text quality profiles first.
- Browser/API prove a user can start from Project context and reach an accepted text.master.v2 without raw Workflow/Prompt authoring.

### Phase 5 — Graphic out-of-box loop

- Add Visual Direction/Card Plan, deterministic composer, real renderer workflow and Graphic QC.
- Prove actual PNG outputs for both starter personas.

### Phase 6 — Audio out-of-box loop

- Add Spoken Adaptation, Voice Direction, TTS result integration and Audio QC.
- Prove actual playable MaterialRevision audio for both starter personas.

### Phase 7 — Video planning/handoff and platform integration

- Refine script/shot/director default recipe and CreativeExecution preparation.
- Consume the modern Channel Registry/Variant stage; do not build final video editing.

### Phase 8 — real quality acceptance and local enablement

- Run full persistent tests/build/bundle/OpenSpec/diff.
- Isolated browser acceptance uses a disposable browser profile and a proven installed headless executable, optionally selected by `PERSONA_TEXT_BROWSER`; it does not hard-code the user's everyday GUI Chrome, install new browsers, or modify login/profile data. Browser-launch proof is separate from product-flow and real creative-quality acceptance.
- With explicit authorization, run selected real chat/image/TTS providers on the fixed persona acceptance matrix.
- Record artifact hashes and human rubric.
- Only after acceptance and explicit local-data authorization, instantiate the two starter personas in the formal SQLite and read back exact revisions/default workflows.

## Risks / Trade-offs

- **Too many abstractions** → no new business tables; one identity profile, one Workflow truth, one method resolver and three clearly separated method inventories.
- **Persona config becomes giant JSON** → four separate modality fields with strict schemas and replace-whole semantics; UI hides raw JSON.
- **“Auto” becomes black box** → exact preview, deterministic route rules, no hidden memory selection.
- **Built-in Skills become a second executable framework** → built-in Skills are declarative methods; deterministic actions remain registered tools/rules/domain services.
- **Subjective quality gets overclaimed** → deterministic gates + fixed human rubric + real-provider acceptance; mocks never prove quality.
- **Lifestyle role fabricates current events** → fresh-evidence requirement for current factual claims and explicit speculation labeling.
- **Graphic LLM produces brittle pixel layouts** → semantic visual plan + deterministic composition templates + existing renderer.
- **Cross-persona learning pollution** → Persona/Account/Series narrow scope by default; owner is not implicit creative scope.
- **Third-party licensing risk** → provenance required; method inspiration may be rewritten; vendoring/copying requires per-source license review.
