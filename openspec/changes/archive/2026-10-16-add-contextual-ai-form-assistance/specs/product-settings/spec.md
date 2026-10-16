## ADDED Requirements

### Requirement: Form completion and field polishing have independent model routes
Settings SHALL expose form_autofill and field_polish as independent text-model purposes within existing Models and AI usage routing. It MUST reuse provider registration, masked credentials and configuration revision handling, and display default inheritance and actual execution provenance.

#### Scenario: Different models for completion and polish
- **WHEN** the user saves distinct registered models for the two purposes
- **THEN** future requests use the corresponding model and report its actual provider, model and configuration version without altering historical runs

#### Scenario: Explicit model becomes unavailable
- **WHEN** a selected model is disabled or no longer executable
- **THEN** assistance reports the configuration problem rather than claiming an undisclosed substitute was the selected model

#### Scenario: Routes are not explicitly assigned
- **WHEN** either purpose has no explicit selection
- **THEN** the settings and assistance show inheritance of the existing global default, and saving the configuration alone does not trigger inference
