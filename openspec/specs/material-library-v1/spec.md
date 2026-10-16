# material-library-v1 Specification

## Purpose
TBD - created by archiving change align-v1-prd2-content-harness. Update Purpose after archive.
## Requirements
### Requirement: Actual media is globally reusable

系统 SHALL 通过 Material + MaterialRevision 提供全局可复用素材库，多个 Draft MUST 能通过 DraftMedia 引用同一个 MaterialRevision。

#### Scenario: 上传图片

- **WHEN** 用户上传一张图片
- **THEN** 系统建立 Material + MaterialRevision
- **AND** 多个 Draft 可以通过 DraftMedia 引用同一个 MaterialRevision

### Requirement: Web-found media starts as candidate

系统 SHALL 保存网络素材的 source URL/provenance/rights 状态；在 `public_use_allowed != true` 前 MUST NOT 满足 Candidate media readiness。

#### Scenario: 网络图片入库

- **WHEN** Material Search Provider 返回一张网络图片
- **THEN** 系统保存 source URL/provenance/rights 状态
- **AND** 在 `public_use_allowed != true` 前不能满足 Candidate media readiness

### Requirement: Approved material bytes are immutable

被 approved Candidate 引用的 MaterialRevision SHALL 不可变；替换/编辑 MUST 产生新 Revision，且历史 Candidate 可按旧 hash 重建。

#### Scenario: 替换已批准素材

- **WHEN** MaterialRevision 已被 approved Candidate 引用
- **THEN** 替换/编辑必须产生新 Revision
- **AND** 历史 Candidate 可按旧 hash 重建

### Requirement: Recipe media stages reuse existing native generation truth

A Creation Recipe media stage SHALL use existing ProviderGenerationTask/result acceptance and MaterialRevision truth. Its required Stage input snapshot, resolved configuration/provenance and execution receipt SHALL be frozen in the Workflow attempt under the common pre-dispatch claim contract; only additional non-authoritative display projections are optional. No duplicate media task/result entity is created.

#### Scenario: Image stage result
- **WHEN** a media stage produces provider candidates
- **THEN** the user accepts through the existing provider task contract and the resulting MaterialRevision remains unbound to Master until an explicit content save

### Requirement: Stage feedback may reference exact accepted material

Stage feedback MAY record an exact accepted/rejected MaterialRevision or ProviderGenerationTask result identity/hash for process improvement. Such feedback MUST NOT change material rights or publication eligibility.

#### Scenario: Record which provider result was chosen
- **WHEN** the user records feedback about an exact provider result or accepted MaterialRevision
- **THEN** the feedback preserves that identity/hash without changing material rights or publication eligibility

### Requirement: Persona Graphic and Audio results remain MaterialRevision truth

Actual rendered Graphic PNGs and accepted TTS audio SHALL be persisted through existing Material/MaterialRevision contracts with exact bytes/hash/MIME/source/provider/renderer/rights provenance. Creative Skill/Persona configuration SHALL be provenance, not a replacement file truth.

#### Scenario: Audio method changes
- **WHEN** a Persona later changes voice preset
- **THEN** an old accepted audio MaterialRevision remains immutable and traceable to the prior TTS task/configuration

### Requirement: Quality checks do not silently mutate media rights

Graphic/Audio QC MAY block, warn or reference an exact MaterialRevision but MUST NOT upgrade public/model/commercial rights, remove attribution obligations or replace bytes in place.

#### Scenario: Quality success does not grant media rights
- **WHEN** a Graphic or Audio artifact passes QC while its MaterialRevision has restricted rights or attribution obligations
- **THEN** those rights, obligations and immutable bytes remain unchanged

#### Scenario: Intermediate handoff does not bypass revoked source rights
- **WHEN** a previously accepted creative planning result references an externally derived MaterialRevision and a materialized ancestor is subsequently revoked or archived
- **THEN** later Stage consumption SHALL revalidate the exact derived ancestry and block model use without rewriting the historical result or upgrading any rights

### Requirement: Background music supports editable scene-based metadata
Existing music assets SHALL support editable multi-label scene, mood, energy, instrumentation/vocal, tempo when known, looping suitability and source/license metadata. Metadata corrections SHALL preserve prior execution references. Music selection SHALL depend on current scene needs rather than exclusive Persona ownership, and no-BGM SHALL be an explicit valid choice.

#### Scenario: A track was tagged with the wrong mood
- **WHEN** the user corrects its tags
- **THEN** future searches and suggestions use the correction while previously frozen selections remain explainable

#### Scenario: A scene needs unobstructed narration
- **WHEN** the selected audio plan omits background music
- **THEN** production completes without requiring a replacement track

### Requirement: Selected music has traceable assets and a mixing plan
The video handoff SHALL record selected music revision, source interval, target scene and mix intent including fades/ducking where used. Existing rights checks SHALL apply to each track rather than inheriting a code repository's license. Initial curated tracks SHALL have individual source evidence before production adoption.

#### Scenario: A Skill bundles an unidentified music file
- **WHEN** the file has no recoverable track-level provenance
- **THEN** it is not declared cleared for public delivery merely because the Skill repository has a permissive code license
