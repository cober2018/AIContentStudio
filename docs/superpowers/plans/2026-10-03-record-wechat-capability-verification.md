# WeChat Capability Verification Promotion Plan

> **For implementation:** use `superpowers:executing-plans` and `openspec-apply-change` only after the user explicitly authorizes apply.

## Goal

Promote an already successful, same-account human-confirmed official WeChat draft into the existing exact-scoped `CapabilityVerification` ledger.

## Constraints

- Reuse existing delivery/capability models; no new table or migration.
- Use the existing receipt endpoint and make receipt + verification atomic and idempotent.
- Scope only `publisher.wechat.official@1` + exact account + `wechat/article/auto_draft`.
- Do not call `draft/get`, publish publicly, retry Unknown, expose secrets or create a PublishedContentRecord.
- Reuse existing acceptance infrastructure; no new test code without separate authorization.

## Execution outline

/// Audit exact receipt, attempt, capability and inventory call paths.
/// Implement the bounded post-confirmation promotion and exact fingerprint/scope checks.
/// Update the existing capability inventory projection.
/// Reuse existing acceptance paths and update the F7 evidence record.
/// Run applicable gates and report this bounded result separately from total F7 completion.

## Current status

- OpenSpec proposal/design/spec/tasks: completed and archived.
- Business code: implemented in the existing delivery/capability paths.
- Validation: targeted delivery/capability/receipt regression 165 passed; OpenSpec all strict 35/35; Ruff and diff-check passed.
- Archive: `openspec/changes/archive/2026-10-03-record-wechat-capability-verification/`.
- Canonical sync: intentionally not performed in this pass; requires a separate scope decision.
