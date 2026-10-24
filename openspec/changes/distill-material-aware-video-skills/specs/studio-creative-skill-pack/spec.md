## ADDED Requirements

### Requirement: Video script and shot planning are material-aware
The built-in pack SHALL include trial versions of the video script and shot-director Skills that plan against the supplied project material catalog. For each beat or shot the method SHALL either use exact catalog material, rewrite the beat to fit available material, or keep the beat with a structured material request naming the slot, purpose, acceptable sources and what the material must show. A shot MAY combine several exact catalog sources with use-range intent and crop notes. Earlier versions SHALL remain unchanged, and the new versions SHALL NOT become Persona defaults without explicit adoption.

#### Scenario: A beat has no matching material
- **WHEN** a drafted beat needs a visual that the catalog does not contain
- **THEN** the plan either rewrites that beat to use available material or records a structured request with acceptable sources, and never invents a material identifier

#### Scenario: Real footage is available for a claim
- **WHEN** the catalog contains footage that shows the claimed behavior
- **THEN** the plan places that exact revision on the beat making the claim, with intended range and crop notes
