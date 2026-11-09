## ADDED Requirements

### Requirement: Finalized graphic piece is rendered and sent to review
When the user approves a third-party-written graphic piece's draft, the platform SHALL render every canvas with the local graphic renderer, register the images as the work's render outputs and save them on a platform revision, then stop at 成图待你验收. Only when the user accepts the rendered images SHALL the piece become final and the platform build the channel variant for the work's channel and form, run its checks, and freeze a candidate in 审阅与交付 awaiting the user's approval. It SHALL NOT push to any platform.

#### Scenario: Approve a graphic draft
- **WHEN** the user clicks 采用 on a graphic draft whose image layers are all public-use materials
- **THEN** the work shows 成图待你验收 with one rendered image per canvas in order, is not yet locked, and has no new candidate

#### Scenario: Accept the rendered images
- **WHEN** the user accepts the rendered images
- **THEN** the piece is 已定稿 and locked, and 审阅与交付 lists a frozen candidate whose preview shows the rendered images plus the publish copy

#### Scenario: Send the rendered images back
- **WHEN** the user writes notes on the rendered images instead of accepting
- **THEN** the third-party model can save the next draft in the same work without copying it

#### Scenario: No platform-added AI mark
- **WHEN** a rendered piece uses AI-generated images and is sent as a WeChat image message
- **THEN** neither the images nor the message body carry a platform-added AI mark; the user labels it on the publishing platform
