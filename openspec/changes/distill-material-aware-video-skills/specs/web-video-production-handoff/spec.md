## ADDED Requirements

### Requirement: Executor guidance covers material scouting, motion toolkit and edit combos
The project executor Skills SHALL document when and where to search for material (in a stated source order), how to verify and crop it, and how to register it through the platform with source, attribution, rights and hash before use, returning to the script when nothing suitable exists. They SHALL document a reusable motion-design toolkit (layout zones, components, timing), named edit combos (components, trigger, timing, failure check), finishing rules (mastered narration, mix loudness target, true-peak ceiling, punctuation-based caption breaks) and a parameterized After Effects builder that produces native compositions from a declared spec. Guidance SHALL NOT authorize bypassing site protections or extend local-only rights.

#### Scenario: A new film reuses the toolkit
- **WHEN** an executor builds a different explainer film
- **THEN** it supplies a new spec (cuts, crops, headlines, chips, captions) to the builder instead of rewriting composition code

#### Scenario: A source site blocks access
- **WHEN** a site requires sign-in or bot verification
- **THEN** the scout records the failure and moves to the next source without bypassing the protection
