# ae-templates Specification

## Purpose
TBD - created by archiving change ae-template-library-batch. Update Purpose after archive.
## Requirements
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

### Requirement: Landscape template variants

Each template in the library SHALL offer a 16:9 variant with the same id, version, fields and behaviour as its 9:16 version, laid out for landscape and kept inside the 16:9 playback safe area. Rendering SHALL pick the project for the requested aspect and SHALL fail clearly when that aspect has no project, never stretching another aspect.

#### Scenario: Render landscape
- **WHEN** a 16:9 render of a template with a landscape variant is requested
- **THEN** a 1920×1080 candidate material is produced from the landscape project

#### Scenario: Missing aspect
- **WHEN** a 16:9 render is requested for a template without a landscape variant
- **THEN** the call fails with ae_template_aspect_unavailable and nothing is rendered

### Requirement: Template previews in the library

Every template SHALL carry a preview video per available aspect stored beside its project, and its manifest SHALL record the previews and a category. The template list for models SHALL include category and preview locations, and a read-only settings page SHALL list templates by category with playable previews and usage notes.

#### Scenario: Browse templates
- **WHEN** a user opens 设置 → AE 模板库
- **THEN** templates appear grouped by category, each playable in 9:16 or 16:9 with its usage and fields

### Requirement: Model chooses templates by default

The craft-ae skill and the template tools SHALL state that the model picks and fills ready templates on its own by default, and that an effect the user names explicitly during fine-tuning SHALL be used, with the user told first if that template is unavailable for the aspect or not ready.

#### Scenario: User names an effect
- **WHEN** during fine-tuning the user asks for the slider comparison effect
- **THEN** the model renders slider-compare for that shot instead of choosing a different template

### Requirement: Product workbench templates

The template library SHALL include 15 product-video templates (product-hero, product-angles, selling-points, check-list, spec-table, compare-table, dimension-mark, price-drop, deal-timer, layer-stack, use-steps, review-cards, cert-card, buy-cta, color-swatch), each with 9:16 and 16:9 projects inside the respective playback safe areas, plus documented reuse of callout-label for selling-point callouts and magnifier for ingredient close-ups. Their usage notes SHALL require real prices, offers, reviews, certificates, dimensions and specifications, keep product images undistorted, and avoid any platform's interface or logo.

#### Scenario: Price template
- **WHEN** price-drop is rendered with an original price and a real final price
- **THEN** the original price is struck through and the final price and saving tag appear, as a transparent overlay

#### Scenario: Product library group
- **WHEN** a user opens 设置 → AE 模板库
- **THEN** the product templates appear in their own group with 9:16 and 16:9 previews

