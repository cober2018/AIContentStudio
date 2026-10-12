## ADDED Requirements

### Requirement: Persona auto configuration reuses executable capability routing

Persona creative auto mode SHALL use the existing deterministic executable model/capability route truth and its limits. It MUST NOT scan unrelated providers or infer capability from model branding. Preview SHALL show the exact selected route and why it is usable.

#### Scenario: Persona Graphic needs image generation
- **WHEN** the selected Graphic style requires generated imagery and no executable image route exists
- **THEN** readiness reports partial/blocked according to the declared typography-only fallback rather than pretending the chat model can generate images

### Requirement: Multimedia adapters declare image and audio execution capabilities

Registered Image and Audio adapters SHALL declare modality, provider/model/profile scope, supported request fields, output MIME/size constraints, candidate-count behavior and executable/readiness state. Image adapters SHALL declare whether multi-output is native and support normalized counts only within the bounded 1–4 range. Audio adapters SHALL declare exact voice-catalog/verification support, `voice_id`, rate and additional supported controls. Catalog/list operations are read-only and MUST NOT synthesize media.

Auto may use the existing authorized capability-routing policy, including bounded fan-out when an adapter explicitly permits it. Custom single-binding mode MUST block when the exact binding or requested capability is unavailable. Custom Composition MAY use only its predeclared exact chain. No route may discover an undeclared image/audio provider or silently ignore a requested field.

#### Scenario: Native multi-output image adapter
- **WHEN** the selected image model declares native four-candidate output
- **THEN** the resolver passes the bounded candidate count, preview shows it, and the receipt records the native batch capability and candidate indexes

#### Scenario: Voice catalog refresh is not media execution
- **WHEN** the user refreshes a registered TTS adapter's voice catalog
- **THEN** the adapter updates local metadata/readiness only and creates no generation task or audio bytes

#### Scenario: Requested image batch is unavailable on an exact Custom binding
- **WHEN** a Custom profile pins an image model that supports only one output while the Stage requests four
- **THEN** the Stage blocks rather than switching models or silently reducing the request

### Requirement: Explicit Persona model preference distinguishes pins from compositions

Custom creative profiles SHALL pin one exact registered provider/model/profile binding for a purpose. If that binding is unavailable or changes before execution, execution SHALL block and MUST NOT substitute another binding. A Composed/Custom Composition profile MAY instead declare an ordered chain of exact registered provider/model/profile bindings; execution SHALL use only that chain, disclose it in preview and record the selected binding and bounded fallback reason. Historical receipts SHALL retain the original route identity.

#### Scenario: Pinned TTS profile disabled
- **WHEN** the Persona audio profile pins a TTS profile that becomes disabled
- **THEN** Audio readiness blocks and never silently changes voice/provider without disclosure

#### Scenario: Custom Composition selects an explicit model fallback
- **WHEN** the primary model binding is unavailable and the next exact binding in the saved Custom Composition chain is executable
- **THEN** the route selects that declared binding, exposes the fallback reason and preserves the selected binding in the attempt receipt

### Requirement: Registered CPA image execution uses an exact image protocol

Gemini/Grok image execution through CPA SHALL reuse existing registered provider/model/profile credentials and explicitly trusted endpoint configuration. It MUST NOT require unrelated official-provider credentials, infer image capability from a chat model name, probe alternate endpoints or create a second provider configuration truth. The media adapter SHALL declare and freeze its versioned request/response protocol, exact model, supported parameters, MIME/byte constraints and native-count or explicitly authorized fan-out behavior. Effective Preview SHALL expose the server-built safe prompt and exact binding without provider I/O.

Execution SHALL consume that frozen contract and normalize actual image bytes into the same ProviderGenerationTask candidate and explicit MaterialRevision acceptance contracts used by MiniMax. Only bounded validated PNG/JPEG/WebP bytes count as success; returned prose, URLs or an available chat route do not. Unknown execution MUST NOT automatically retry or switch provider/model/protocol. Provider errors and credentials MUST NOT leak into previews, receipts or materials. No new business table or migration SHALL be introduced for this adapter.

#### Scenario: Registered Gemini chat is not an image binding
- **WHEN** an enabled registered Gemini model can chat but has no implemented exact image protocol
- **THEN** image preview reports unavailable with a safe reason and execution neither calls chat as an assumed image endpoint nor silently chooses another model

#### Scenario: CPA image candidates use the existing acceptance truth
- **WHEN** an explicitly selected executable CPA image binding returns the exact declared candidate count as valid image bytes
- **THEN** the candidates retain exact configuration/runtime/output hashes and explicit selection accepts only the chosen image into MaterialRevision without modifying Master or Variant

#### Scenario: Possible image dispatch cannot trigger protocol discovery
- **WHEN** a CPA image request times out or its external outcome is unknown
- **THEN** the original task remains uncertain and no alternate protocol, model or provider is tried automatically

### Requirement: ChatGPT manual image generation provides prompt handoff and image upload

The normal image-generation UI SHALL expose an explicit `ChatGPT（手动生图）` option. It SHALL display a complete safe effective prompt, one-click copy, and a multi-image drag/drop and file-picker entry instead of an automatic provider Generate action. The prompt SHALL deterministically consume the accepted visual brief/card plan, Persona style, usage, aspect/size, bounded requested count (1–4), reference obligations and output constraints. Preview/copy SHALL make no model request. Manual ChatGPT MUST NOT be advertised as a native executable image binding or enter Auto routing/provider fallback.

This branch SHALL reuse CreativeExecution Package/staging/acceptance truths with explicit human external execution, not ProviderGenerationTask or a new durable table. The existing package SHALL freeze the exact eligible current Master/Variant source, safe prompt snapshot/hash and bounded output contract. Changes to frozen source/prompt/configuration require a new current package. Existing source currentness, archive-read-only, required-role/min-max-count and live derived-rights rules MUST remain authoritative.

Dropping or choosing local image files SHALL immediately enqueue visible candidate rows and upload to temporary staging only. Each row SHALL show upload/validation progress, thumbnail, MIME/dimensions, error or ready state, and selection/removal controls. The server SHALL validate actual bounded PNG/JPEG/WebP bytes, MIME, dimensions, file size, count and hash against the frozen contract. Invalid/failed files MUST NOT be accepted or create partial MaterialRevision writes; other valid candidate rows remain intact. Removing a temporary row MUST NOT delete/revoke an already accepted material.

Explicit `接受入库` SHALL accept only exact selected valid staged outputs through the existing idempotent MaterialRevision acceptance service with `source_kind=external_execution`. Upload alone MUST NOT create an accepted material. Provenance SHALL distinguish user-declared ChatGPT origin from verified native provider execution and preserve prompt/package/output hashes and human decisions without fabricated LLMRun/model/runtime receipts. Accepted material MUST NOT automatically bind/save Master or modify Variant, Candidate, Approval or publication.

AIContentStudio SHALL neither require a browser/session binding nor submit prompts/download images on the user's behalf for this branch. It MUST NOT read/export Cookies, browser-profile files or site credentials, create a fake API/browser endpoint, silently choose another provider, or replay old browser-smoke requests. The user operates the external website themselves. Prompt copy or external image generation alone MUST NOT mark product execution result-ready, accepted or quality-approved.

#### Scenario: Manual ChatGPT is selected without browser automation
- **WHEN** the user selects `ChatGPT（手动生图）` without an application browser/session binding
- **THEN** the frontend exposes the full prompt/copy and upload entry, makes no provider or browser request and does not switch to CPA or MiniMax

#### Scenario: Dragged images remain temporary candidates
- **WHEN** the user drops multiple downloaded images into the manual upload area
- **THEN** each file immediately appears in the candidate list with independent upload/validation state and no accepted material or Master mutation occurs

#### Scenario: Invalid upload does not affect valid candidates
- **WHEN** one returned file violates the frozen image output contract while another is valid
- **THEN** the invalid row shows a bounded error and cannot be accepted, the valid candidate stays selectable and there is no partial material write

#### Scenario: Exact uploaded image is explicitly accepted
- **WHEN** the user selects a valid exact staged output and clicks `接受入库`
- **THEN** the existing service revalidates live derived rights and creates the exact MaterialRevision idempotently with user-declared ChatGPT provenance; Master reference/save remains separate

#### Scenario: Source changes while the user generates externally
- **WHEN** the frozen package source becomes stale before returned image acceptance
- **THEN** the existing stale/currentness gate blocks acceptance and the UI requires a new current package without overwriting the old contract or automatically regenerating

#### Scenario: Copying or uploading is not accepted production output
- **WHEN** the prompt is copied or an image is merely uploaded without explicit acceptance
- **THEN** no provider-success receipt or accepted MaterialRevision is fabricated and the existing result/acceptance states reflect only actual validated staged outputs and explicit decisions
