## Why

The user wants growth analysis. Today 效果复盘 records per-post observations entered by hand, but there is no account-level view (followers over time), no comparison by topic, format, cover or posting time, and nothing turns numbers into next steps.

## What Changes

- **Account snapshots**: followers, total likes/saves, posts count per account per day, entered by hand, imported from a CSV export, or captured from a platform data page screenshot the user uploads (values confirmed by the user before saving).
- **Post metrics** keep using PerformanceObservation (views, completion, likes, saves, comments, shares, follows gained), with the same import paths.
- **Growth page** per account and per persona: follower trend, posts on the timeline, best and weakest posts, and comparisons by topic, format, cover style, length and posting hour. Metrics from different platforms are never summed.
- **Insights → suggestions**: the platform drafts findings ("3:4 covers with a question got 2× saves"), each linked to its evidence; accepting one creates a Learning Candidate (existing flow), never a silent profile change.
- **Report export**: a per-post report for a brand (used by brand deals).

## Capabilities

### Modified Capabilities

- `content-performance-history`: account-level snapshots, growth views, comparisons and evidence-linked suggestions.

## Impact

- New `account_metric_snapshot` table; import endpoints (manual, CSV, screenshot with user confirmation); analysis read models.
- Web: 效果复盘 becomes 增长分析 with account, post and suggestion views; charts drawn with inline SVG (no new heavy dependency).
