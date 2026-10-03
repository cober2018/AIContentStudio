## ADDED Requirements

### Requirement: Replaceable capabilities are versioned and discoverable
The system SHALL register exact key/type/version capability descriptors for the North Star capability categories while keeping Studio business state independent of provider implementation.

### Requirement: Capability verification is durable and scoped
The system SHALL persist safe verification records separately from secrets. Publisher verification MUST be scoped by platform/account/content-form/action/version/time.

### Requirement: Unverified capability is unavailable
Plugin existence, configuration existence or a successful settings read MUST NOT imply verified executable or side-effect capability.

### Requirement: Connector execution requires explicit mapping
A generic Connector SHALL become a Data Source capability only through an explicit typed mapping. Connector configuration alone MUST NOT mark unrelated Data Source plugin keys connected.

### Requirement: External media becomes MaterialRevision before production use
Search/image/video/TTS provider output SHALL be verified/materialized with exact bytes/hash/provenance/rights before any Master or Variant references it.

### Requirement: ASR/transforms do not mutate content automatically
External transcription/generation output SHALL require explicit user/system save into a new revision before becoming durable content.

### Requirement: Settings truthfully exposes capability state
Settings SHALL distinguish configured, executable, verified and unavailable states without leaking secrets or triggering side effects during reads.

### Requirement: Publisher only executes approved authorized content
Publisher SHALL receive exact Approved Candidate + Delivery Authorization and SHALL NOT change content or silently adapt formatting.

### Requirement: Unknown remote outcome is preserved
A remote side-effect with uncertain result SHALL remain Unknown/reconciliation-needed and MUST NOT be automatically retried.

### Requirement: Real platform verification controls verified status
A Publisher capability SHALL be marked verified only after explicit real-account verification with read-back or human confirmation appropriate to the platform.
