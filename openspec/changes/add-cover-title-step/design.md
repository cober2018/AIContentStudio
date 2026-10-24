## Decisions

- **Cover is a ChannelVariant media role, not a new entity.** Every platform version already owns its media slots and is frozen into the candidate; adding a required-or-optional `cover` role per channel reuses approval and delivery without a new truth.
- **Candidates are MaterialRevisions.** Frames, uploads, generated images and compositions all become revisions with rights, so a chosen cover is traceable and reusable.
- **Choice is explicit.** No automatic winner; generation only proposes.
- **Specs live in the channel registry** so delivery packages export the right sizes.
