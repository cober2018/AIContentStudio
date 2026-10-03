## Why

Production Studio has typed plugins, Connectors, local packages and a legacy WeChat draft publisher, but a registered/configured integration is not proof that it can safely execute for a specific project or account. FE-F7 makes provider output, verification scope and remote delivery truthful and auditable without moving Studio's Master/Candidate/Authorization truth into an external service.

## What Changes

- Extend the existing exact key/version plugin registry to the North Star capability kinds; keep legacy kind aliases and resolvers compatible.
- Add additive, secret-free capability registration and scoped verification records. Verification must be invalidated by changed code/config/credentials, account, scope or expiry; an inventory read never probes a provider.
- Bridge a Data Source Plugin to a ConnectorEndpoint only through an explicit authorized mapping. Existing generic Connectors and disconnected plugin descriptors remain unchanged until a mapped executor actually passes its gate.
- Add bounded search, image, video, TTS, ASR and renderer contracts. Untrusted responses are inspected; accepted media become exact MaterialRevision bytes/hash/rights/provenance before project attachment or Master/Variant use.
- **BREAKING:** Require explicit account/channel/form/action/publisher-version verification for remote delivery across new and legacy paths. The legacy `allow_unverified_auto_draft` switch is not verification and cannot authorize a remote side effect; historical targets and attempts remain readable.
- Preserve approved frozen content, DeliveryTarget/Attempt/Receipt, unknown reconciliation, local copy/manual packages and old Candidate reads. WeChat WeWrite retains only its actually proven behavior; Douyin/Xiaohongshu remote actions remain unavailable until real acceptance.
- Redact provider requests, responses, errors, logs and receipts at every API/persistence boundary, not only in Settings. Remote side-effect probes require explicit account authorization.

## Capabilities

### New Capabilities

- `capability-integrations-delivery`: versioned capability registry, safe verification, explicit Connector bridge, accepted provider media and exact remote publisher gate.

### Modified Capabilities

- `fe-f2-persistent-production-workflow`: mapped Data Source execution and snapshot lineage become available only through the typed plugin gate.
- `system-assets-knowledge`: externally sourced MaterialRevision rights and provenance remain exact through project reuse.
- `product-settings`: capability inventory shows configured/executable/verified/unavailable states without side-effect probes or secret leakage.
- `fe-f4-project-review-distribution`: remote Delivery Authorization/execution requires scoped verification and preserves immutable content/unknown semantics.

## Impact

Additive capability registration/verification persistence and migration; existing PluginRegistry, ConnectorEndpoint, Data Source Plugin, MaterialRevision, DeliveryTarget/Attempt and Settings APIs gain gated adapters/projections. The implementation follows F6E acceptance, uses isolated migrations and real-account verification only with separate credentials and side-effect authorization. No push, deployment, production migration, canonical spec sync or archive is implied.
