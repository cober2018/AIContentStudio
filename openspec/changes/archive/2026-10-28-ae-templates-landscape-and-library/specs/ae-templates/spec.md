## ADDED Requirements

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
