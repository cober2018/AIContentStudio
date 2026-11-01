## ADDED Requirements

### Requirement: The persona overview matches the edit page

The persona overview SHALL show voice, portraits and speech-sample folder as named sections in the same order as the edit page, followed by identity, expression and boundaries. It SHALL NOT show the inherited brand block or list known fields under 其他资料.

#### Scenario: Persona with portraits and a speech folder under a brand
- **WHEN** the overview of 萌柚老爸 (brand 知见童年, one portrait, no speech folder) is opened
- **THEN** it shows the portrait thumbnail under 形象照, 未设置 under 逐字稿样本, and no raw `brand` or `portrait_material_revision_ids` entry
