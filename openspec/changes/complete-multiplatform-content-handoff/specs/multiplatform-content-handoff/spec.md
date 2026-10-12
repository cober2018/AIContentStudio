## ADDED Requirements

### Requirement: Twelve platforms and seventeen independently accepted forms

The system SHALL support the following exact modern targets as platform-specific local deliverables: wechat/article; toutiao/article; baijia/article; zhihu/article and zhihu/answer; bilibili/article and bilibili/image_note; sohu/article; penguin/article; netease/article; xiaohongshu/image_note; x/single, x/thread, x/long_post and x/articles; weibo/single; douyin/spoken_script. Each form MUST have separate adaptation, preview, save, Candidate approval and package acceptance evidence. Existing other platform records MUST remain unchanged but MUST NOT silently enlarge this change's acceptance scope.

#### Scenario: Full target catalog
- **WHEN** the user opens the modern channel target selector
- **THEN** all twelve platforms and seventeen distinct forms are represented with truthful capability reasons
- **AND** the selector does not substitute five sample forms or a WeChat acceptance result for the whole scope

#### Scenario: One platform multiple forms
- **WHEN** Zhihu article/answer or X single/thread/long_post/articles are requested
- **THEN** each uses its own target contract and independent Variant/Candidate series
- **AND** success for one form does not mark the other forms complete

### Requirement: Exact source target and canonical schema contracts

The system SHALL retain the existing five F6E schema contracts unchanged and add the following versioned payload schemas. All article targets, zhihu/answer, X forms and weibo/single MUST accept only text.master.v2; bilibili/image_note and xiaohongshu/image_note MUST accept only graphic.master.v2; douyin/spoken_script MUST accept only video.master.v2. Artifact kinds MUST be text, image and script respectively and MUST match the exact published profile.

| Exact target | Added payload_schema |
|---|---|
| toutiao/article | toutiao.article.v1 |
| baijia/article | baijia.article.v1 |
| zhihu/article | zhihu.article.v1 |
| zhihu/answer | zhihu.answer.v1 |
| bilibili/article | bilibili.article.v1 |
| bilibili/image_note | bilibili.image_note.v1 |
| sohu/article | sohu.article.v1 |
| penguin/article | penguin.article.v1 |
| netease/article | netease.article.v1 |
| x/long_post | x.long_post.v1 |
| x/articles | x.articles.v1 |
| weibo/single | weibo.single.v1 |

New article envelopes SHALL contain title, summary, blocks, tags, citations and declarations with title/blocks required; ordered blocks SHALL carry stable unique IDs and typed heading/paragraph/quote/list/callout/code/divider/image fields. List items SHALL have unique stable IDs; images SHALL bind exact asset slot keys. Zhihu answer SHALL additionally require a user-confirmed question and exactly one first block with kind=direct_answer and order=0. This extra kind SHALL be allowed only in zhihu.answer.v1, with the exact id/order/kind/text fields and nonempty text; descriptors, checks and rendering SHALL treat it as the direct-answer text paragraph. Other schemas MUST reject this extra kind. X long_post SHALL be continuous text with citations/declarations rather than a thread or Articles alias. X Articles SHALL use titled article blocks. Weibo SHALL contain text/tags/ordered image refs/citations/declarations; Bilibili image_note SHALL contain title/description/tags/ordered cards/citations/declarations with genuine rendered images.

New payloads SHALL use the existing bounded stable-ID rules, NFC/newline normalization, at most 250 ordered items/refs and a 2 MB canonical JSON bound. Kind-specific field allowlists and technical limits SHALL be enforced server-side and exposed through the adapter descriptor. Unknown fields/types/enums, duplicate IDs, invalid order and over-bound content MUST fail before any Variant or event write. These technical limits MUST NOT be described as verified platform limits. Existing five-schema normalization/hash and validation behavior MUST remain unchanged.

#### Scenario: Incompatible Master
- **WHEN** a Graphic Master is submitted for an article or a historical v1 Master is submitted to a modern adapter
- **THEN** the server returns typed unavailable/explicit-upgrade-required without writing a Variant or upgrading historical content

#### Scenario: Answer without question
- **WHEN** zhihu.answer.v1 lacks a user-confirmed question or direct_answer block
- **THEN** validation rejects the proposal/save and does not invent a real question or question URL

#### Scenario: Valid direct-answer encoding
- **WHEN** zhihu.answer.v1 has a confirmed question and first block with only id/order=0/kind=direct_answer/nonempty text
- **THEN** the answer validator, typed editor and renderer accept the same canonical representation
- **AND** an article schema containing direct_answer remains rejected rather than weakening the enum allowlist

#### Scenario: Independent canonical hash
- **WHEN** an accepted target payload is saved and re-read with identical refs
- **THEN** server canonical payload and hash remain deterministic for its exact schema
- **AND** changing target/form/order/content/ref changes the relevant hashes

### Requirement: Platform-specific adaptation with visible effective instructions

Each target adapter SHALL apply its own exact published profile, audience/structure/title/tone/tags/source/declaration/media requirements and expose the effective adaptation instructions. Shared canonicalization/rendering tools MUST NOT turn all targets into the same text with a different channel label. Unverified platform restrictions SHALL be labeled product configuration or unknown. Model adaptation SHALL produce a server-validated proposal for explicit user review/save using existing model routing and verified successful LLMRun provenance; it MUST NOT mutate Master or obtain new facts/rights implicitly.

#### Scenario: Article family adaptation
- **WHEN** one Text Master is adapted to Toutiao, Zhihu article and Bilibili article
- **THEN** the user can inspect each target's independent effective profile/instruction and edit its typed target structure before saving
- **AND** the source Master and other saved target Variants remain unchanged

#### Scenario: Edited model suggestion
- **WHEN** the user modifies a proposed model adaptation before accepting
- **THEN** final content is recorded as user-edited with truthful suggestion provenance
- **AND** final content is not falsely labeled an unchanged verified model output
- **AND** provider raw output/errors/secrets are not frozen into the Variant or Candidate

### Requirement: Exact assets evidence and preserved source obligations

Adapters SHALL preserve project ownership, exact MaterialRevision IDs/bytes/hash/rights/attribution, FactPackItem IDs/snapshot checksums and provable citation location/range mappings through proposal/save/checks/freeze/package. Citation ranges SHALL reference globally unique canonical text locations using Unicode code-point offsets. Unprovable re-mapping MUST return incomplete/blocked until explicitly repaired; media prompts/URLs/names MUST NOT substitute for actual image bytes. Platform adaptation MUST NOT upgrade derived public/model/commercial rights or erase required source/license obligations.

#### Scenario: Citation moved by adaptation
- **WHEN** rewriting changes the cited target text range and the mapping cannot be proven
- **THEN** the target proposal exposes the citation problem and cannot be frozen as evidence-valid until repaired

#### Scenario: Real card output required
- **WHEN** Bilibili or Xiaohongshu image_note has only card prompts or lacks exact rendered card refs
- **THEN** packageability remains blocked and no placeholder image is exported

#### Scenario: Live media change
- **WHEN** referenced media is revoked, deleted or its bytes no longer match the frozen hash
- **THEN** approval/new authorization/local packaging fail under existing live gates without substituting another revision

### Requirement: Recipe and Production share the modern target contract

Creation Recipe channel-variant stages and Production/Review SHALL consume the same server registry/adapter descriptors rather than a second hardcoded five-target list. Existing `stage.variant.adapt@1`, Effective Preview, temporary adjustments, Attempt receipts, feedback and Save What Worked SHALL remain the execution/control sources. Preview MUST be zero model calls. A stage proposal MUST NOT automatically save Variant, freeze Candidate, approve or deliver. Workflow, Master and each Variant dirty/save state SHALL remain independent and 409 SHALL preserve local edits.

#### Scenario: Stage chooses new platform
- **WHEN** a Recipe stage selects baijia/article and the exact compatible profile/adapter are executable
- **THEN** preview, execution, typed proposal editing and explicit Variant acceptance use that exact contract
- **AND** no separate platform workflow engine or silent Master save is created

#### Scenario: Profile changes after preview
- **WHEN** target profile/source/config no longer matches the preview hashes
- **THEN** execution/save rejects stale input and preserves the local draft without an implicit model rerun

### Requirement: Frozen v5 pipeline and per-target currentness remain authoritative

New target schemas SHALL reuse existing append-only ChannelVariantRevision/checks, schema-dispatched Candidate v5, exact-hash Review/Approval/DeliveryTarget and (unit_id, variant_key) currentness. channel_variant_revision_id SHALL remain the sole v5 Candidate source FK; draft_id/topic_brief_id/mother_revision_id/content_master_revision_id/workflow_run_id MUST remain null. Projection target columns MUST match frozen channel/form/artifact kind. Currentness, profile/check freshness, ownership, archived-read-only, source integrity and live rights/evidence gates MUST NOT be weakened or fall back to v4/v3/legacy Draft.

#### Scenario: Multiple independent platform Candidates
- **WHEN** Candidates for different target series are frozen and then approved in any order
- **THEN** one series does not invalidate the current Candidate of another series
- **AND** approvals remain bound to their exact ID/hash

#### Scenario: Target or pointer tampering
- **WHEN** a v5 Candidate has a mismatched target projection, changed hash or any legacy source/workflow FK
- **THEN** Review/Approval/Authorization/package fail closed with no fallback

### Requirement: Complete platform local package from approved frozen content

Every supported form SHALL export an authorized local ZIP containing manifest.json, content.md, publish-guide.md, sources.json, declarations.json, the form-specific structure file and exact referenced media bytes in frozen order/placement. Article/answer/Articles packages SHALL contain server-deterministic safe content.html; answers SHALL additionally contain question.json; threads thread.json; image notes cards.json; Weibo post.json; Douyin scenes.json and explicitly estimated SRT when present. Package rendering SHALL use approved frozen payload/profile/render/refs, not a mutable Master/Variant/Draft or newly published profile. No local package SHALL make a remote call.

Sources/declarations SHALL be safe, publishable projections only, retaining mandatory source/license/attribution obligations. The package MUST NOT export private filesystem paths, credentials, raw provider output or entire FactPack/source/model-use-only context. This privacy projection SHALL cover all ZIP members including manifest.json. The export manifest SHALL use a versioned projection with the validated exact Candidate ID/hash, target/schema/profile/adapter, necessary publishable refs/rights/attribution, file/order/placement and per-file hashes; it SHALL have its own canonical export hash. The original Candidate hash SHALL be a source-record reference, not falsely claimed recomputable from the redacted projection. Full internal Candidate/manifest and live integrity checks MUST remain unchanged; already delivered historic five-schema packages MUST NOT be silently rewritten. Where required public disclosure is not permitted, package creation MUST block instead of leaking it or silently omitting the obligation. HTML SHALL escape unsafe content and use package-local media paths without script/active network requests. Exported HTML MUST NOT promise pixel-identical styling after a platform's editor transforms it.

#### Scenario: Inspect approved article ZIP
- **WHEN** an approved Toutiao article is exported
- **THEN** its content.md/content.html, structure, citation/source/declaration projections and media match its frozen Candidate
- **AND** manifest and guide state local package/manual handoff rather than published

#### Scenario: Protected source context
- **WHEN** a cited source contains private or model-use-only context
- **THEN** export includes only legally publishable frozen attribution metadata
- **AND** any required but non-publishable disclosure blocks the package instead of leaking the source text

#### Scenario: Script package is not finished video
- **WHEN** a Douyin spoken_script package is generated
- **THEN** its scenes/B-roll/estimated subtitles are labeled script-only and estimated
- **AND** it is not displayed as a finished video or verified audio-timed subtitle

### Requirement: Manual delivery is separate from remote draft and public publication

This phase SHALL expose copy_package/manual_handoff for all twelve platforms but MUST NOT enable non-WeChat remote publishing. Existing WeChat auto_draft SHALL retain exact approved Candidate, account/form/action/runtime capability, separate authorization, durable Attempt and Unknown/reconciliation rules. A profile, successful local ZIP or scope approval MUST NOT grant a remote capability, authorize a fresh WeChat call or authorize any public publication. Long-post/Articles account eligibility SHALL remain explicitly unverified without blocking a valid local package.

#### Scenario: Non-WeChat package completed
- **WHEN** the user downloads an approved Weibo/X/Bilibili local package
- **THEN** the delivery remains awaiting manual receipt and no remote capability or PublishedContentRecord is inferred

#### Scenario: WeChat retains bounded scope
- **WHEN** a WeChat draft action is requested without matching live verified account/form/action/runtime or explicit delivery authorization
- **THEN** automatic draft creation is unavailable and the local package option remains independent
- **AND** an unknown earlier result is not retried

### Requirement: Truthful per-form rollout and concentrated acceptance

Implementation SHALL be grouped into backend/package and frontend/acceptance batches. Each of the seventeen forms SHALL record catalog/profile/source/schema/proposal/save/checks/Candidate/Review/ZIP/media/state results separately. Controlled smoke evidence SHALL be distinguished from actual model quality, platform-editor paste behavior, account permissions and real remote publication. The implementation plan SHALL include small parameterized persistent contract tests for canonical schemas/hashes, source/target compatibility, v5 pointer/currentness, safe export projections and live-rights/tampering rejection, plus concentrated seventeen-form smoke; existing regression/build/bundle checks SHALL be reused. Writing new test code MUST await explicit user authorization, and the current Persona batch's no-new-test instruction remains effective until then. Temporary smoke MUST NOT be described as the required persistent coverage. Existing unrelated workspaces/raw packages/specs/history MUST remain preserved.

#### Scenario: Local-chain acceptance complete
- **WHEN** all seventeen controlled local-chain smoke journeys pass
- **THEN** the report may mark platform-specific local handoff complete
- **AND** real model quality/account/publication outcomes not actually exercised remain unverified

#### Scenario: One target unavailable
- **WHEN** a target lacks configuration, executable adapter, evidence or required genuine media
- **THEN** its independent completion row remains blocked with a concrete reason instead of marking all twelve platforms ready
