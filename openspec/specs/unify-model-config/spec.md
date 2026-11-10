# unify-model-config Specification

## Purpose
TBD - created by archiving change unify-model-config. Update Purpose after archive.
## Requirements
### Requirement: Vendors are configured once

A vendor's address and key SHALL be entered only in 设置 → AI 与模型 → 厂商与模型. No other page, setting row, environment variable or local file SHALL be a source of a model vendor's address or key.

#### Scenario: Key changed
- **WHEN** the user changes a vendor's key in 厂商与模型
- **THEN** every use of that vendor (chat, images, video, voiceover, ASR, writing CLI, topic search) uses the new key without a restart

### Requirement: Every use picks a registered vendor and model

Each model use SHALL be chosen in 用途路由 as a registered vendor + model. Other pages SHALL NOT offer free-text vendor, address, key or model fields.

#### Scenario: Cover images
- **WHEN** the user sets 封面生图 to a vendor's image model in 用途路由
- **THEN** cover generation uses that vendor and model, and no separate AI 生图 form exists

#### Scenario: Voiceover
- **WHEN** voiceover runs
- **THEN** it uses the TTS model chosen in 用途路由; the 配音 page only sets voice, emotion and speed

#### Scenario: No per-target override
- **WHEN** a persona, product, SKU or production stage runs
- **THEN** it uses the model from 用途路由, and none of those pages offers a model choice

#### Scenario: Unrouted use
- **WHEN** a use has no route
- **THEN** it uses the 默认 route, and the 用途路由 page lists that use by name

### Requirement: A use may name a backup model
Each text use and the cover-image and shot-image uses in 用途路由 SHALL keep one required primary model and MAY name one backup model. Every call SHALL try the primary first. When the primary fails for a vendor-side reason (no quota or balance, rate limit, connection failure or reset, vendor server error, or for text a timeout), that call SHALL be retried once with the backup. A call SHALL NOT switch to the backup when the model answered but the output was invalid, when the content failed a check, or when the request itself was invalid. An image call SHALL switch only after a definite failure of the primary and SHALL NOT resend a call whose outcome is uncertain. No "current model" state SHALL be kept: the next call tries the primary again. When the backup is used, the record SHALL name the model actually used and why the primary was not. Voiceover, image-to-video and web-search vendors are out of scope.

#### Scenario: Primary out of quota
- **WHEN** 平台适配 has grok-4.7 as primary and gemini-3.8-flash-high as backup, and grok-4.7 refuses for lack of quota
- **THEN** that rewrite is done by gemini-3.8-flash-high and the run record says the backup was used and why

#### Scenario: Primary recovers
- **WHEN** grok-4.7 has quota again
- **THEN** the next call uses grok-4.7 without any setting being changed

#### Scenario: Bad output does not switch
- **WHEN** the primary answers with JSON missing required fields
- **THEN** the call does not switch to the backup; the existing rewrite or failure handling applies

#### Scenario: No backup set
- **WHEN** a use has no backup and its primary fails
- **THEN** the call fails as today

