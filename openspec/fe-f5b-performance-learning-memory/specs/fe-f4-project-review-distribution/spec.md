## MODIFIED Requirements

### Requirement: Project history integration

Confirmed publication receipts and DeliveryFeedback MAY feed the Performance/Learning domain as provenance. Review/Delivery remains authoritative for delivery state and Learning MUST NOT reinterpret unknown/failed delivery as published success.

#### Scenario: Confirmed receipt enters history
- **WHEN** a project DeliveryReceipt confirms publication
- **THEN** the Learning domain may idempotently materialize a PublishedContentRecord linked to the real Candidate/Target/Receipt

#### Scenario: Unknown delivery
- **WHEN** delivery remains unknown/reconciliation-needed
- **THEN** no PublishedContentRecord is claimed until publication is explicitly confirmed
