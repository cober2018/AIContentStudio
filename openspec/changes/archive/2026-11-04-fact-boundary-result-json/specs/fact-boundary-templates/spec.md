## ADDED Requirements

### Requirement: Fact-boundary results reach the model

The results of `submit_facts` and `get_fact_template` SHALL be plain JSON in every case, including when the project already has a frozen fact boundary; the boundary's freeze time SHALL be given as an ISO 8601 string, or null when absent.

#### Scenario: Submitting facts when a boundary exists
- **WHEN** the model calls `submit_facts` on a project that already has a fact boundary and some items pass
- **THEN** it gets the kept count, the returned items with reasons, and the new current boundary, instead of an argument error

#### Scenario: Reading templates when a boundary exists
- **WHEN** the model calls `get_fact_template` on a project that has a fact boundary
- **THEN** it gets the templates and the current boundary, with `frozen_at` as an ISO string
