## ADDED Requirements

### Requirement: Daily market review article for the quant persona
On each trading day the system SHALL fetch the previous trading day's data from the data platform's public dashboard services (public-*) with this platform's own key, keep only whitelisted factual fields, normalize units, and create one text work under the persona's long-running 每日复盘 project and 每日复盘 column, with key charts rendered as images and a platform-written first draft waiting for the user's adoption. Days without data SHALL create no work. Nothing SHALL be published automatically.

#### Scenario: Normal trading day
- **WHEN** 07:30 arrives and the previous trading day's data is available
- **THEN** a work titled with that date appears in the 每日复盘 project and column, carrying filtered facts, chart images and a draft waiting at 稿子

#### Scenario: Non-trading day
- **WHEN** the data platform returns no rows for the day
- **THEN** no work is created and the guard shows the day as skipped

#### Scenario: Newest day repeats the previous day's sector moves
- **WHEN** at least 90% of the day's industry change figures equal the previous trading day's
- **THEN** the day's sector gainers and losers are left out of the facts, charts and draft, and the rest of the review is still written

### Requirement: Advisory fields never enter the platform
The system SHALL drop advisory content returned by the data platform — lifecycle phase, opportunity tags, signal priority, crowding, RRG quadrant verdicts, leader stocks, theme stage and strength score, style signals, guidance and predicted states — before storing anything, and SHALL stop pulling the old connection's lifecycle and RRG dashboards.

#### Scenario: Upstream adds an advisory column
- **WHEN** the public-industry-review service returns review_group, opportunities and opportunity_score with the day's rows
- **THEN** neither field appears in the stored facts, the charts or the draft

### Requirement: Daily review reads only through its own compliance account
The daily review SHALL call the data platform with a key bound to the `aicontent` service account, and SHALL read the macro calendar from the `calendar-facts` view.

#### Scenario: Calendar read through the facts view
- **WHEN** the review collects a trading day's facts
- **THEN** it requests `public-forward-risk-events` with `view=calendar-facts` and `window_days=7`, keeps only events after that day, and takes previous and consensus values as the numbers the view returns

#### Scenario: A granted service refuses the key
- **WHEN** any of the six granted services answers 403
- **THEN** the review does not silently drop that part; data guard shows that the key has no permission

### Requirement: Daily review is written by a third-party model over MCP
The daily review SHALL NOT be scheduled or written by the platform. The MCP tool `prepare_daily_review` SHALL create or reuse the trading day's piece, collect its facts and draw its charts (no tables), and return them with the writing rules; the third-party model saves the draft with `save_article_draft`.

#### Scenario: Draft with advice words
- **WHEN** a third-party model saves a daily review draft containing an investment-advice term
- **THEN** the save is refused with the term named, and nothing is stored
