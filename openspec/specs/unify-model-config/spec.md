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

