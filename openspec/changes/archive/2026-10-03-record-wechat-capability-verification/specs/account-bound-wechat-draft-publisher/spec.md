## ADDED Requirements

### Requirement: A confirmed successful WeChat draft creates a scoped capability record
The system SHALL append one durable `CapabilityVerification` with `result=verified` when the exact account-bound official WeChat `auto_draft` attempt has status `succeeded`, contains a valid non-empty `remote_id` returned by `draft/add`, and the operator records `human_confirmed` for that same target and account. The verification SHALL bind the exact publisher key/version, account, `account_ref`, channel and article form. It SHALL NOT create a publication record or claim that the article was publicly published.

#### Scenario: Confirmed draft promotes capability evidence
- **WHEN** a succeeded official WeChat article draft attempt has a valid non-empty `remote_id` and the operator confirms the draft in the same configured account
- **THEN** the receipt transaction appends an exact scoped `CapabilityVerification`, preserving the existing attempt/receipt and candidate provenance without creating `PublishedContentRecord`

#### Scenario: Receipt and verification are atomic
- **WHEN** the capability scope or runtime fingerprint cannot be validated while recording the human confirmation
- **THEN** the transaction fails closed and does not leave a new human-confirmed receipt or a partial verification record

### Requirement: Verification is reusable only for the exact bounded draft action
The system SHALL treat the new record as verification for `publisher.wechat.official@1` with `channel=wechat`, `content_form=article`, the exact configured `ContentAccount` and `account_ref`, and stored `action=auto_draft` only. A future dispatch MAY reuse it only when the complete scope, current implementation/config fingerprint and validity window match. It SHALL not authorize another account, another form, public publish, `draft/get`, or the unresolved general long-form contract.

#### Scenario: Exact account and article draft scope is reusable
- **WHEN** a later official draft target selects the same account, account reference, article form and `auto_draft` action under the same publisher implementation/config fingerprint
- **THEN** capability inventory and authorization report the exact bounded scope as verified and executable for draft creation only

#### Scenario: Different scope remains unavailable
- **WHEN** a later target selects another account, non-article form, publish action or another publisher version
- **THEN** the prior verification is not used and the requested action remains unverified/unavailable without an external request

### Requirement: Invalid or ambiguous outcomes cannot create verification
The system SHALL not append a successful `CapabilityVerification` when the attempt is missing a valid `remote_id`, is failed/unknown/reconciliation-needed, the receipt is not `human_confirmed`, the account or target scope differs, or the account/runtime/config fingerprint is revoked or changed. Existing historical attempts and verifications SHALL remain readable and SHALL not be rewritten or automatically retried.

#### Scenario: Missing media identifier
- **WHEN** a draft/add response is empty, malformed or lacks a non-empty `media_id`
- **THEN** the attempt cannot be promoted to capability verification and no new successful verification is stored

#### Scenario: Ambiguous attempt
- **WHEN** the attempt is unknown or reconciliation-needed, or the operator records failed/reconciliation-needed instead of human confirmation
- **THEN** no capability verification is created and the system preserves the existing reconciliation boundary without resubmitting the draft

#### Scenario: Runtime drift or revoked account
- **WHEN** the account is archived/revoked or the official publisher implementation/config fingerprint differs from the evidence
- **THEN** the record is not created or reused for new dispatch, while prior evidence remains auditable

### Requirement: Capability evidence is secret-safe and does not require draft readback
The system SHALL persist only allowlisted safe references, reason codes and server-derived hashes in the capability verification evidence. It MUST NOT copy credentials, tokens, raw platform responses, raw HTML, signed URLs or the raw WeChat `media_id` into the verification projection. A valid `media_id` on the exact succeeded attempt plus same-account human confirmation is sufficient; the system SHALL not claim that `draft/get` was performed when it was not.

#### Scenario: Secret-safe promotion
- **WHEN** the capability verification is appended after a confirmed draft
- **THEN** its scope/evidence contains only exact account/action identifiers and safe hashes/references, with no credentials, raw response body, HTML, signed URL or raw media identifier

#### Scenario: No readback is inferred
- **WHEN** a valid draft/create response and same-account human confirmation are recorded without calling `draft/get`
- **THEN** the capability record remains valid for the bounded draft-create scope and all readback fields remain absent or explicitly unperformed
