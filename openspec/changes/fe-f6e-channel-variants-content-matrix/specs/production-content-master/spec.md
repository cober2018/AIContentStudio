## ADDED Requirements

### Requirement: Channel-neutral Master is an explicit source-only path
New Units MAY explicitly omit channel_id, in which case their ContentMasterRevision SHALL pin null channel/content_form and remain a reusable source for ChannelVariant adaptation. A neutral Master MUST NOT be frozen directly through the channel-bound v4 Candidate path. Existing channel-bound Units/Masters and historical v4 Candidates SHALL retain their current context and hash semantics without backfill or implicit conversion.

#### Scenario: Save neutral source Master
- **WHEN** an authorized editor creates a channel-neutral Unit and saves a valid Master
- **THEN** the Master freezes null channel/form and exact Identity/Brief/Boundary context, and a channel-specific Candidate requires a saved ready Variant

#### Scenario: Existing bound Master
- **WHEN** a historical channel-bound Master is opened or frozen under v4
- **THEN** its original channel/form and v4 behavior remain unchanged; no Variant link is invented

### Requirement: Variant adaptation does not retarget source Master context
A ChannelVariant derived from a channel-bound or neutral Master SHALL pin that exact source Master ID/payload/context and IdentitySnapshot. Editing or publishing the Variant MUST NOT rewrite the Master, rebind the Unit or bypass its current context/evidence/rights gates.

#### Scenario: Adapt bound Master to another registered form
- **WHEN** an editor explicitly adapts a current channel-bound Master for a different target form
- **THEN** the Variant records both the original Master channel/form and target form while Master history is unchanged

### Requirement: Initial Variant adapters accept only explicit v2 Master schemas
Initial F6E adapters SHALL accept `text.master.v2` only for `wechat/article`, `x/thread` and `x/single`; `graphic.master.v2` only for `xiaohongshu/image_note`; and `video.master.v2` only for `douyin/spoken_script`. The target form's exact published `artifact_kind` MUST match the adapter declaration. Historical v1 Master revisions remain readable and their existing v4 behavior remains unchanged; adaptation requires an explicit F6B/C/D v2 fork, not an implicit rewrite or conversion during Variant save.

#### Scenario: Historical v1 Master is selected
- **WHEN** a user asks to adapt a historical v1 Master to a first-batch F6E target
- **THEN** adaptation reports the explicit upgrade requirement and writes no Variant or Master revision
