## ADDED Requirements

### Requirement: AE template renders run one at a time

The platform SHALL run at most one aerender for `render_ae_template` at a time. A render requested while another is running SHALL wait and start after the earlier ones finish, in order of arrival, instead of failing.

#### Scenario: Two works render together
- **WHEN** two works call `render_ae_template` at the same moment
- **THEN** the second aerender starts only after the first one has ended, and both calls return their materials
