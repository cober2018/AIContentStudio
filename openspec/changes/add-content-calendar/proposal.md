## Why

The workflow map includes a content calendar: what goes out when, on which account. Today home says scheduling is not implemented, and project update time is the only date.

## What Changes

- **Planned slots** per account: date, time, platform version, status (planned, ready, published, missed).
- **Calendar views**: week and month across accounts, filtered by persona; drag a work onto a slot.
- **Readiness**: a slot shows whether its work is approved and delivered; missed slots are flagged on home.
- **Brand deal dates** (publish dates, review deadlines) appear on the calendar.
- No automatic publishing: a slot is a plan; publishing stays the existing manual or authorized flow.

## Capabilities

### New Capabilities

- `content-calendar`: planned publishing slots and calendar views.

## Impact

- New `publishing_slot` table and API; home reads upcoming and missed slots; web calendar page.
