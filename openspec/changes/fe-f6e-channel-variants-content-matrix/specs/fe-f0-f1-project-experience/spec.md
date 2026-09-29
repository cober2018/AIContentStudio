## ADDED Requirements

### Requirement: Content Matrix suggestions require explicit confirmation
The Project Content Matrix SHALL display bounded Identity × Modality × Channel suggestions as proposals rather than persisted Units. Selection SHALL use existing authorized Unit creation/rebinding APIs and preserve their history fork/archive rules. A chosen channel is a production target, not an FE-F4 DeliveryTarget; actual Delivery Authorization requires a separately approved exact Candidate. A suggestion MUST NOT silently create a Unit, delivery authorization or Identity change.

#### Scenario: Decline suggested channel
- **WHEN** an editor closes the suggestion panel without confirming any item
- **THEN** the Project's Units, identity and delivery state remain unchanged

#### Scenario: Confirm selected suggestion
- **WHEN** an editor confirms one proposal for a new Unit
- **THEN** the Matrix persists only that Unit and reload shows its actual pinned identity and workflow state
