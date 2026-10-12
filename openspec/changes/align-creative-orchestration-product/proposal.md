## Why

AIContentStudio already has durable Project/Identity/Brief/evidence, append-only ContentMasterRevision, accepted MaterialRevision, ChannelVariant v5, Candidate/Review/Delivery, native provider generation, and Learning/Memory. The remaining product problem is no longer “add another editor.” The daily product surface is still split between new and legacy pages, `/production` is not yet the daily creation queue, System Assets still jumps to legacy pages for several writes, Settings still exposes legacy administration, and the current Video Studio is deeper than the product's long-term differentiation requires.

The approved North Star is to make AIContentStudio the content and creative decision system: it owns intent, facts, identity, source content, channel variants, exact assets, approvals, delivery facts and learning. Simple/high-frequency creation stays native. Complex/high-quality work is expressed as an exact Creative Execution Package and delegated through a local MCP/Agent boundary to replaceable professional tools, then returned as provenance-bound candidate outputs. The system must also become better with use by preserving high-quality reusable methods as explicitly promoted, versioned Capability Memory rather than silently self-modifying.

This change aligns the implemented system to that North Star without rewriting F6D/F6E/F7/F8 history, replacing current native generation, weakening Candidate/Delivery safety, or turning AIContentStudio into a professional NLE/Photoshop/DAW.

## What Changes

- Add durable, append-only creative-intent projections to current Master/Variant revisions so “why this content is shaped this way” is preserved alongside “what the content is.”
- Add `CreativeExecutionPackage` as an immutable, hash-bound handoff from one exact current Master or ChannelVariant, with a general schema and a first `director.video.v1` specialization. A package may be prepared before a final video render exists; it never approves or publishes content.
- Add `CreativeExecution` plus staged outputs for professional/external work. Native ProviderGenerationTask remains the current truth for ordinary model image/video/TTS generation; both paths converge only after explicit output acceptance into MaterialRevision.
- Add a same-machine, loopback-only AIContentStudio MCP surface for Codex/Claude/other Agents to read execution packages and authorized inputs, report checkpoints/progress/blockers, submit bounded outputs, and reconcile uncertain execution. It does not expose a second business state source.
- Add execution-specific private work directories for exact input materialization/output submission. The MCP never grants arbitrary filesystem reads and staged output paths cannot escape the execution work root.
- Preserve Unknown/no-auto-retry semantics for side-effecting external execution. Executor checkpoint/revert/recover support is capability metadata and evidence, not assumed.
- Add `Capability Memory`: versioned `prompt_skill`, `recipe`, `creative_pattern`, `preference`, `execution_template`, and externally executed `tool` artifacts with candidate → saved/pinned → archived/deprecated lifecycle, scope, provenance, safe search/use, and explicit human promotion.
- Automatically suggesting/capturing a capability candidate is allowed only from bounded successful/accepted work; candidates are non-authoritative and never become long-term behavior without explicit promotion. AIContentStudio does not execute arbitrary Capability Memory code in the first version.
- Keep Content Learning separate from Capability Memory. Performance learning may propose a capability candidate, but Learning acceptance never edits a capability automatically and capability popularity never changes facts, Identity, or evidence.
- Reframe Video as script/directing/orchestration first. Existing `video.master.v1/v2`, timelines, render attestations, v4 Candidates and historical packages remain readable. New daily work emphasizes script/scene/shot/voice/subtitle/assets/Director Package; advanced timeline/render remains compatibility/advanced functionality rather than a product expansion target.
- Consolidate daily UI into one product surface. Landing enters Home; `/production` becomes a real creation/execution queue; Project is the primary container; System Assets absorbs daily Source/Fact/FactPack/Material writes; Settings absorbs ordinary Connector/template/runtime actions; Review remains Candidate/Approval/Delivery truth.
- Add a legacy-operation parity gate: legacy menu entries cannot disappear merely because a new list exists. Every still-used state-changing operation must have a new surface and regression before the corresponding legacy page exits daily navigation. Historical data and compatibility reads remain.
- Keep the final production profile unchanged: this computer, SQLite, configured local media, loopback-only API/Web. This change adds no serverization requirement.

## Capabilities

### New Capabilities

- `creative-orchestration`: creative intent, immutable execution packages, external execution lifecycle, loopback MCP handoff, checkpoint/recovery evidence, output staging/acceptance, and director-first professional handoff.
- `capability-memory`: explicitly promoted, versioned reusable prompts/recipes/patterns/preferences/external-tool definitions with scoped discovery, usage provenance and safe lifecycle.

### Modified Capabilities

- `fe-f0-f1-project-experience`: one daily product surface, direct idea/material/opportunity starts, Project-first flow and legacy operation-parity retirement.
- `content-home-workspace`: surface execution result-ready/blocker/unknown decisions without creating duplicate task state.
- `system-assets-knowledge`: absorb ordinary upload/generation/source/fact/FactPack operations while preserving current underlying truth.
- `production-content-master`: persist bounded creative intent and support director-first external execution without weakening existing v4/v5 history.
- `fe-f2-persistent-production-workflow`: make content/execution primary and workflow design an advanced control surface; CreativeExecution is not another WorkflowRun.
- `fe-f4-project-review-distribution`: external execution results remain proposed assets until accepted and explicitly bound into a new source revision/Candidate; execution completion is never approval/publication.
- `content-learning-memory`: keep strategy/content learning distinct from reusable execution-method memory and require explicit cross-promotion.
- `product-settings`: manage safe Creative Execution/MCP status and Capability Memory while absorbing ordinary legacy settings operations without auto-probing.
- `material-library-v1`: accept verified external execution files into immutable MaterialRevision with exact provenance/rights.
- `fe-p1-frontend-bundle-performance`: lazy-load execution, capability-memory and compatibility tooling without expanding unrelated route closures.

## Impact

Additive SQLite models/migration are expected for CreativeExecutionPackage, CreativeExecution, staged CreativeExecutionOutput, CapabilityArtifact/CapabilityArtifactRevision/CapabilityUse, plus bounded creative-intent JSON/hash fields on current Master/Variant revisions. Existing ProviderGenerationTask, MaterialRevision, ContentMasterRevision, ChannelVariantRevision, Candidate, Review, Delivery and Learning tables remain authoritative and are not backfilled or rewritten.

The first MCP acceptance uses a controlled local Test Agent or Codex/Claude handoff; it does not require real Premiere, After Effects, Photoshop or DAW automation. Professional-tool connectors remain replaceable execution endpoints.

F6E is implemented and fully checked but remains an active lifecycle change at this baseline. This change must not rewrite its source package. Before canonical synchronization of overlapping requirements, reconcile F6E lifecycle explicitly. Current F8 single-machine-production documentation changes in the worktree are separately owned and must not be reset or mixed into this change.

No push, deployment, canonical sync/archive, formal database upgrade of the user's live SQLite, remote publication, paid model call, or destructive legacy-page deletion is authorized merely by this proposal.
