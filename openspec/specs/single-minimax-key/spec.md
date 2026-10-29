# single-minimax-key Specification

## Purpose
TBD - created by archiving change single-minimax-key. Update Purpose after archive.
## Requirements
### Requirement: One MiniMax key

The system SHALL use the API key saved on the 厂商与模型 → MiniMax card for every MiniMax call. If the card has no key, it SHALL fall back to the local `mmx` login.

#### Scenario: Voiceover, writing, cover image and search
- **WHEN** a voiceover, an LLM call to a MiniMax endpoint, a MiniMax cover image or a MiniMax topic search runs
- **THEN** it uses the card's key, not a key stored in another section or local file

#### Scenario: Key changed on the card
- **WHEN** the user saves a new key on the MiniMax card
- **THEN** the next MiniMax call of every kind uses the new key without a restart, and `~/.mmx/config.json`, `~/.dsh/env.local` and the MiniMax image entry in `~/.wewrite/config.yaml` hold the new key

### Requirement: No second MiniMax key field

The 主模型 and AI 生图 sections SHALL NOT offer their own key field when they point to MiniMax; they SHALL say the key comes from the MiniMax card.

#### Scenario: LLM section on MiniMax
- **WHEN** the LLM endpoint is a MiniMax address
- **THEN** the section shows "密钥：用 MiniMax 卡片" and saving it stores no key

#### Scenario: Other vendors
- **WHEN** the LLM endpoint or image provider is not MiniMax
- **THEN** the section keeps its own key field as today

