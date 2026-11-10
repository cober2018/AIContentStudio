## ADDED Requirements

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
