## Context

AIContentStudio already records an official WeChat draft attempt, including the account-bound target, immutable candidate references, attempt status and the non-empty WeChat `media_id` returned by `draft/add`. The operator also confirms the same draft in the designated account's draft box. That evidence currently stops at `DeliveryAttempt`/`DeliveryReceipt`; it is not promoted to the existing durable capability-verification ledger.

The product needs to distinguish two facts:

1. one particular draft attempt succeeded; and
2. this exact account, article form and draft-create action are verified for the currently loaded official publisher implementation.

The change must work with the existing dirty F7/F8 workspace without replacing unrelated work. It must not add a second verification table, require `draft/get`, imply public publication, or broaden the verified scope to other accounts, forms or actions.

## Goals / Non-Goals

**Goals:**

- Promote a completed, human-confirmed official WeChat draft into the existing `CapabilityVerification` record.
- Bind the record to the exact `ContentAccount`, frozen `account_ref`, `wechat/article/auto_draft` scope, publisher key/version and current implementation/config fingerprint.
- Make the promotion append-only and idempotent, with the receipt and verification committed atomically.
- Reuse the same exact verification at future official draft preparation and expose only a safe scoped status in the capability inventory.
- Keep the record secret-safe and auditable using server-derived hashes and existing immutable attempt/candidate/receipt references.

**Non-Goals:**

- No new model, table or migration.
- No `draft/get` call or required remote readback.
- No public publication, `PublishedContentRecord`, automatic retry or new remote action.
- No verification for another account, another content form, publish/send actions, or the general unresolved long-form contract.
- No new test code in this change unless separately authorized; reuse existing regression and acceptance infrastructure.

## Decisions

### 1. Reuse `CapabilityVerification` and the existing receipt transaction

The service SHALL append the verification when the existing receipt endpoint accepts `human_confirmed` for an official `auto_draft` target whose exact attempt has already succeeded with a non-empty `remote_id`. The receipt and verification are written in one database transaction. If verification validation fails, neither the new receipt state nor the verification promotion commits.

Alternative rejected: creating a `WechatDraftVerification` table would duplicate the existing capability ledger and create a second invalidation/currentness path.

### 2. Require two independent pieces of evidence

The promotion requires both:

- server-observed success: the exact `DeliveryAttempt` is `succeeded` and its `remote_id` is a valid non-empty WeChat `media_id`; and
- operator evidence: the user confirms the draft in the same configured account through the existing `human_confirmed` receipt flow.

The receipt is evidence of draft-box presence only. It does not assert public publication and does not require a `draft/get` request.

Alternative rejected: treating a successful HTTP response alone as broad capability verification would not prove the account selected in the product is the account that contains the draft.

### 3. Keep the verification scope exact and product-compatible

The persisted `scope_json` SHALL use the existing publisher scope shape and actual delivery action value:

```json
{
  "channel": "wechat",
  "content_form": "article",
  "action": "auto_draft",
  "content_account_id": "<exact account id>",
  "account_ref": "<frozen account reference>",
  "publisher_key": "publisher.wechat.official",
  "publisher_version": "1"
}
```

The product-facing phrase “draft_add” maps to the existing stored action `auto_draft`; no second action vocabulary is introduced. Future authorization may reuse this verification only when every scope field and the current implementation/config fingerprint match. The general `remote_contract_ready` state remains independent and may stay unresolved for other forms or long-form contracts.

### 4. Use safe evidence projection only

`evidence_json` SHALL contain only allowlisted reason codes, candidate/target/attempt/receipt references and server-derived hashes such as the frozen candidate hash, render/input hash and a one-way hash of the remote identifier. It SHALL NOT contain credentials, access tokens, raw WeChat responses, raw HTML, signed URLs or the raw `media_id`. The existing `DeliveryAttempt.remote_id` remains the bounded delivery record for the remote identifier and is not copied into the capability evidence projection.

### 5. Make promotion idempotent and fail closed

Repeated receipt submission, browser retries or a repeated promotion for the same exact target/attempt/receipt identity SHALL return or reuse the existing matching verified record and SHALL NOT create a duplicate successful verification. Missing/blank `remote_id`, failed/unknown/reconciliation outcomes, account mismatch, revoked account, changed runtime/config or changed candidate/target scope SHALL not create a new verified record.

Alternative rejected: “last successful attempt for this publisher” would allow one account or form to authorize another and would be unsafe after configuration rotation.

### 6. Update the existing inventory projection, not a second UI state

The Settings capability inventory SHALL report the exact account/form/action scope and its safe verification time/reason when present. It SHALL not label the entire WeChat publisher globally verified, and read-only inventory rendering SHALL not obtain a token or call WeChat.

## Risks / Trade-offs

- **A human can confirm the wrong account in the UI.** → Keep the account identity and frozen `account_ref` visible in the receipt flow and bind the verification to that exact scope; the system must not infer another account.
- **The implementation/config can change after verification.** → Store and recheck the implementation/config fingerprint; old evidence remains auditable but cannot authorize new dispatch after drift or expiry.
- **Existing official-contract gating may be broader than this bounded experiment.** → Add a narrow exact-scope verification path for `wechat/article/auto_draft`; do not relax publish, other forms, other accounts or general contract readiness.
- **A remote create may have side effects even if the client loses the response.** → Preserve the existing Unknown/reconciliation rules; only a persisted succeeded attempt with a non-empty `media_id` can promote capability evidence.

## Migration Plan

No schema migration is required. Implementation reuses the existing `CapabilityVerification` table and current receipt/delivery rows.

1. Add the post-receipt promotion and exact live-scope checks.
2. Update the capability inventory projection.
3. Reuse existing backend/browser acceptance infrastructure for the positive and negative paths.
4. Record the bounded verification evidence in the F7 acceptance document.

Rollback is code rollback only; existing capability rows, attempts and receipts remain readable. A revoked or drifted verification cannot authorize new dispatch.

## Open Questions

- The exact user-facing inventory label can be chosen during implementation, but it must state “official WeChat article draft creation” and the bound account rather than “WeChat publishing verified”.
- Expiry should use the existing capability-verification validity policy; this change does not introduce a new duration or renewal mechanism.
