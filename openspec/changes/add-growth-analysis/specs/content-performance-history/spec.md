## ADDED Requirements

### Requirement: Account growth is tracked over time

The platform SHALL record dated account snapshots (followers and totals) per platform account from manual entry, CSV import or user-confirmed screenshot reading, and SHALL show the trend without combining different platforms.

#### Scenario: Weekly follower check
- **WHEN** the user imports a Douyin creator CSV
- **THEN** the account's follower trend updates and other platforms are unaffected

### Requirement: Growth suggestions cite evidence and need acceptance

Suggestions derived from metrics SHALL link to the posts and numbers behind them and SHALL only affect personas or methods after the user accepts them as Learning Candidates.

#### Scenario: Cover style finding
- **WHEN** the platform finds question-style covers earn more saves
- **THEN** it shows the posts compared and the numbers, and nothing changes until the user accepts
