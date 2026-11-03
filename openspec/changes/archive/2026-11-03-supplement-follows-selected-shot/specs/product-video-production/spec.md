## ADDED Requirements

### Requirement: The supplement panel follows the selected shot

In the 素材 step the supplement panel SHALL sit under the per-shot material pages and show only the shot selected there: the shot's generation entries when it lacks the user's footage and is ungrouped, the open-grid entry when it belongs to a consistency group, and a short note when it already has footage. Paging through shots above SHALL change the panel below. The panel's counts and portrait notice stay.

#### Scenario: Selecting a shot
- **WHEN** the user selects L06 of work 94 in the material pages
- **THEN** the supplement panel shows only shot 6's entries

#### Scenario: Shot with footage
- **WHEN** the user selects a shot that has footage
- **THEN** the panel says the shot already has material and needs nothing
