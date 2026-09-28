## MODIFIED Requirements

### Requirement: Project history integration
Candidate/approval/delivery lifecycle SHALL appear in project Activity, Versions and Overview from underlying facts. ProjectEvent and local state changes SHALL commit together; failed or idempotently repeated actions MUST NOT create misleading duplicate activity.

#### Scenario: Approve and authorize history
- **WHEN** a Candidate is approved and then separately authorized for a delivery target
- **THEN** Versions and Activity expose two distinct real records/events and Overview derives the remaining next action

Confirmed publication receipts and DeliveryFeedback MAY feed the Performance/Learning domain as provenance. Review/Delivery remains authoritative for delivery state and Learning MUST NOT reinterpret unknown/failed delivery as published success.

#### Scenario: Confirmed receipt enters history
- **WHEN** a project DeliveryReceipt confirms publication
- **THEN** the Learning domain may idempotently materialize a PublishedContentRecord linked to the real Candidate/Target/Receipt

#### Scenario: Unknown delivery
- **WHEN** delivery remains unknown/reconciliation-needed
- **THEN** no PublishedContentRecord is claimed until publication is explicitly confirmed
