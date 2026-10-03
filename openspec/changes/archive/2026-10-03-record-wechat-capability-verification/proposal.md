## Why

The product has successfully created a real WeChat draft and persisted the exact `media_id`, but that delivery evidence is not yet promoted into the durable scoped capability-verification record required by the publisher contract. As a result, the system cannot truthfully distinguish “this exact account/form/action was verified” from “a single attempt succeeded”.

## What Changes

- After a successful authorized WeChat draft attempt with a valid `media_id` and same-account human confirmation, append a `CapabilityVerification` record for the exact account, channel, content form, action and publisher version.
- Derive the verification evidence from the existing immutable Candidate/Target/Attempt/Receipt data and the account-bound runtime/config fingerprint; never copy credentials, raw platform responses or raw HTML into the verification record.
- Keep verification scoped to `publisher.wechat.official@1` + the exact configured account + `wechat.article` + `draft_add`; do not imply public publication, other accounts, other forms, `draft_get`, or publish actions.
- Recheck this exact verification scope at future draft dispatch and expose its safe verified/unverified state in the existing capability inventory.
- Add idempotency and negative cases for missing `media_id`, wrong account/form/action, revoked or changed runtime, and ambiguous/unknown attempts.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `account-bound-wechat-draft-publisher`: a bounded successful draft creation can append an exact scoped `CapabilityVerification` without creating a publication record or requiring `draft/get`.

## Impact

- Reuses the existing `CapabilityVerification`, `CapabilityRegistration`, `ContentAccount`, `DeliveryTarget`, `DeliveryAttempt` and `DeliveryReceipt` models; no new table or migration is expected.
- Updates the official WeChat delivery service and the capability inventory projection.
- Reuses the existing regression infrastructure and updates the F7 acceptance record; this change does not authorize new test code unless separately requested. No public publish, automatic retry, credential exposure or remote action beyond the already authorized draft flow is included.
