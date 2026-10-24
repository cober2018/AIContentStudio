## ADDED Requirements

### Requirement: Technology actionable recommendations view
For an explicitly technology-policy Persona the default opportunity list SHALL include new/qualified opportunities with relevant_until later than now regardless of generation day. It SHALL display generation date, verified source dates and category. An explicit today filter SHALL use Asia/Taipei. History SHALL expose expired, handled and missing-expiry records without treating them as current recommendations. Home technology recommendations SHALL use the same actionable definition. Lifestyle default date behavior SHALL remain unchanged. This scoped default supersedes the generic current-day default only for technology-policy Personas.

#### Scenario: Yesterday's valid technology suggestion
- **WHEN** an unhandled recent_report recommendation was created yesterday and has not expired
- **THEN** it appears in the technology default view without being re-generated or relabeled as created today

#### Scenario: Historical record without deadline
- **WHEN** an old record has no relevant_until
- **THEN** history shows its missing deadline and the default view does not assume it is permanently valid
