# FE-F7 Capability Integrations & Delivery — implementation plan

> Goal: implement the approved F7 OpenSpec in two coherent batches on local `main`; preserve F6E and v1–v5 compatibility. No push, deployment, production migration, or unapproved remote side effect.

## Batch A — durable safety boundary

/// Verify F6E baseline, F7 strict spec, backend/frontend gates and migration head.

/// Add exactly CapabilityRegistration and append-only CapabilityVerification with safe scoped fields, additive migration, downgrade preflight, and exact runtime fingerprint/version checks.

/// Expand registry kinds without changing legacy resolution. Connect typed Data Source capability to exact ConnectorEndpoint only when verified; keep disconnected plugins unavailable.

/// Remove `allow_unverified_auto_draft` execution bypass; recheck publisher scope immediately before attempts; redact provider/connector diagnostics across persisted and returned surfaces.

/// Run targeted security/compatibility regressions, SQLite/PostgreSQL migration rehearsal, then full backend/OpenSpec/Ruff/diff gates. Record first-batch evidence in progress/findings/README.

## Batch B — capability use and product closure

/// Existing `/materials/generate` currently writes public-ready revisions from a boolean provider result and retains raw prompt text. Replace this acceptance edge under F7: bounded staged result → explicit rights/license acceptance → verified exact bytes/MIME/hash → MaterialRevision; never manufacture provider verification. Keep historical resources readable.

/// Reuse existing MaterialRevision and ProjectMaterialReference; no third capability table or new durable provider-result business entity. Provider runtime/accepted-result receipts must be server-derived and scoped to the requesting actor, exact input and bytes. If a durable new object is required, stop at the specification boundary.

/// Add bounded search/import and image/video/TTS/ASR/renderer protocols and accepted MaterialRevision provenance; reject no-byte, ambiguous-rights, secret-bearing and unverified outputs.

/// Project attachment uses exact revision; verify v5 WeChat immutable approved package projection and local/manual versus verified remote action separation.

/// Add Settings capability inventory/probe UI with safe metadata and role gates; keep reads side-effect-free and unavailable truthful.

/// Complete isolated browser, full backend/frontend/FE-P1/OpenSpec/Ruff/diff and independent reviews. Real external verification requires credentials and explicit account/side-effect authorization. Do not canonical-sync/archive F6E/F7 without separate authorization.

## F8 gate

/// After F7 implementation acceptance, review F8 production auth/tenancy/deployment OpenSpec against actual code and choose explicit identity, secret and storage contracts before business apply. Finish local full-loop acceptance; do not claim production readiness from mocks or unverified external providers.
