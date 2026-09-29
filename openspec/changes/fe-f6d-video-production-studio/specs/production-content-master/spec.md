## ADDED Requirements

### Requirement: Production Core supports Video v2 without changing older schemas
Production Core SHALL dispatch `video.master.v2` through a bounded Video adapter for canonical payload, exact refs, required checks, render-input hash, preview, package projection and freeze availability. It SHALL keep `video.master.v1`, Text/Graphic and existing Candidate v1–v4 history readable under their original definitions. Ordinary save MUST NOT cross from v1 to v2; a dedicated append-only fork is required.
The verified upgrade path SHALL permit exactly `video.master.v1` → `video.master.v2` for Video; all other Video schema crossings remain forbidden. Derived Video provenance SHALL be written only by a dedicated server operation, not arbitrary save input.

#### Scenario: New Video v2 Master
- **WHEN** a Video unit explicitly saves a valid new v2 document with exact project-visible media refs
- **THEN** Production Core creates one immutable Master revision and computes readiness from the Video v2 adapter without creating a Draft

#### Scenario: Legacy read remains stable
- **WHEN** an old Video v1 Master or Candidate is read after Video v2 support is installed
- **THEN** its original schema, checksum and frozen content remain unchanged and no automatic v2 conversion occurs

### Requirement: Video v2 final-render gating uses complete current inputs
Video v2 freeze, approval, authorization and package SHALL use the shared live Candidate/Master validation path. A final video output MUST match the exact current render-input hash and live rights/bytes; a manual attestation remains distinct from a verified renderer. No v2 failure may fall back to Draft, video v1 or an older package builder.
Frozen Video v2 reads SHALL additionally verify canonical v2 content, Candidate v4 hash, ready input-bound render and exactly one frozen video render-output ref whose ID/hash/MIME matches the render declaration before Review or package projection.

#### Scenario: Render input changes after attestation
- **WHEN** a source asset, timeline item, subtitle, context or exact channel profile changes after an MP4 was attested
- **THEN** the old render cannot make the newer Master Candidate-ready
