## ADDED Requirements

### Requirement: Second template batch

The platform SHALL ship the AE templates listed in design.md, each with a manifest declaring fields with limits, image slots, duration range, fonts, project hash, comp and checks. A template SHALL only be auto-selectable after two renders with clearly different content pass.

#### Scenario: Template ready
- **WHEN** a template in the list passes two renders with different content
- **THEN** list_ae_templates shows it as ready and render_ae_template produces a candidate material

#### Scenario: Draft template
- **WHEN** a template has fewer than two passing renders
- **THEN** it is listed as draft and not auto-selected

### Requirement: Transparent overlay templates

A template whose manifest sets alpha SHALL render with a transparent background as a QuickTime file, so it can be stacked over footage in DaVinci Resolve; other templates SHALL keep rendering MP4.

#### Scenario: Overlay render
- **WHEN** a keyword template with alpha is rendered
- **THEN** the material is a .mov with an alpha channel and the background is transparent

### Requirement: Own design, borrowed rhythm

Templates SHALL follow the platform's own layout, fonts and colours and only borrow timing and technique from the chosen cards; they SHALL NOT include upstream code, text, media or platform trademarks.

#### Scenario: Follow card
- **WHEN** a follow card template is rendered
- **THEN** it shows a neutral card without any platform's logo or interface

### Requirement: Playback safe area

Every template's text and key content SHALL stay inside the playback safe area defined by the user-supplied guide images (9:16: x 59–1016, y 268–1482, right edge 886 where y is 769–1482; 16:9: x 91–1828, y 190–959). Full-bleed backgrounds and pictures MAY extend beyond it. Each template project SHALL carry the guide image as a non-rendering guide layer, and an automated check SHALL report any text or key shape outside the area.

#### Scenario: Name plate on a phone
- **WHEN** the name plate template is rendered at 9:16
- **THEN** the name and title sit inside the safe area, clear of the bottom caption band and the right-hand button column

#### Scenario: Automated check
- **WHEN** the safe-area check runs over all templates with their sample content
- **THEN** it reports zero layers outside the area
