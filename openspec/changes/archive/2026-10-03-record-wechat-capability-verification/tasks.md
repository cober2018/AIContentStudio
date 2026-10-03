## 1. Exact capability promotion

- [x] 1.1 Reuse the existing `CapabilityVerification`, `DeliveryAttempt`, `DeliveryReceipt`, `ContentAccount` and publisher registration models; confirm no migration or duplicate verification object is needed.
- [x] 1.2 Implement the atomic post-receipt promotion for a succeeded official WeChat `auto_draft` attempt with a valid `remote_id` and same-account `human_confirmed` evidence.
- [x] 1.3 Enforce exact scope, current implementation/config fingerprint, account status, validity and candidate/target provenance; keep other forms, accounts and publish actions unavailable.
- [x] 1.4 Make repeated receipt/promotion requests idempotent and preserve Unknown, reconciliation-needed, failed and revoked boundaries without automatic resend.

## 2. Safe projection and reuse

- [x] 2.1 Update the existing capability inventory projection to show the exact account/article/auto-draft verification state and safe reason without exposing secrets or globally enabling WeChat publishing.
- [x] 2.2 Ensure future official draft authorization can reuse only the exact bounded verification while general contract readiness and unrelated scopes remain independent.
- [x] 2.3 Keep readback optional and accurately unperformed; do not create `PublishedContentRecord` or infer public publication.

## 3. Acceptance and records

- [x] 3.1 Reuse existing backend/browser acceptance infrastructure for one positive confirmed draft and the specified negative cases; do not add new test code unless separately authorized.
- [x] 3.2 Record the exact account/form/action/config-scope evidence and update the F7 acceptance documentation and task status without including credentials, raw media IDs or raw platform responses.
- [x] 3.3 Run the applicable OpenSpec, diff and existing regression gates, then report the bounded result separately from the overall F7 status.
