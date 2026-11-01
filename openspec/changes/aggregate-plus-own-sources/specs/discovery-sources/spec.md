## ADDED Requirements

### Requirement: Aggregates add to a persona's own sources

A persona that uses an aggregate site SHALL still collect from, and draw daily topics from, its own enabled source subscriptions, alongside the aggregate and its radar. Daily topic limits and model budgets SHALL stay as they are.

#### Scenario: Aggregate site stops updating
- **WHEN** the persona's aggregate site has had no new items for three days
- **THEN** its own subscribed sources are still collected and daily topics still come from them

### Requirement: A withdrawn aggregate item drops only itself

When an aggregate site withdraws an item used as evidence, the daily run SHALL drop that evidence and continue with the rest; it SHALL stop only when no evidence remains.

#### Scenario: One item withdrawn
- **WHEN** one of ten evidence items has been withdrawn by the aggregate site
- **THEN** the run continues with the other nine
