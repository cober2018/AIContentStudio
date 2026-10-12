## ADDED Requirements

### Requirement: Capability Memory is distinct from Content Memory

ContentMemory SHALL continue to hold explicitly promoted evidence-backed learned content context. Capability Memory SHALL hold reusable prompts/recipes/patterns/preferences/execution templates/tools. Neither store SHALL silently write the other.

#### Scenario: User saves a preferred editing recipe
- **WHEN** a reusable execution method is promoted
- **THEN** it becomes Capability Memory and no ContentMemory or Identity revision is created

### Requirement: Validated Learning may propose capability candidates explicitly

An accepted LearningCandidate MAY be used in a separate authorized action to create a Capability Memory candidate with frozen LearningCandidate/evidence provenance. Candidate creation is not capability promotion and MUST NOT modify a saved/pinned artifact.

#### Scenario: Learning suggests a channel hook
- **WHEN** evidence-backed learning is accepted
- **THEN** the user may create a scoped Creative Pattern candidate for later review/promotion without changing existing channel strategy automatically

### Requirement: Capability use is not publication-performance evidence

CapabilityUse accepted/rejected outcomes MAY support process/workflow analysis but MUST NOT be counted as PublishedContent performance unless linked through the existing PublishedContentRecord/PerformanceObservation truth.

#### Scenario: A recipe is accepted many times
- **WHEN** a production recipe has many accepted uses but no published performance samples
- **THEN** Learning cannot claim the recipe improves audience performance from those uses alone
