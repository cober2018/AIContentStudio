## ADDED Requirements

### Requirement: New AE templates for comparison and stills

The template library SHALL include `compare-pair` (two items side by side with labels, optional images and a note) and `photo-push` (one image with a slow push-in, optional caption and corner tag), each ready only after two checked renders.

#### Scenario: Compare two sizes
- **WHEN** auto-fill or an agent renders compare-pair with 海缆 and 浇花水管
- **THEN** the result shows both items side by side with their labels and the note

### Requirement: Generated pictures close remaining gaps

Before leaving a row as a gap, auto-fill SHALL generate a first-frame image from the row's prompt, keep it as AI-generated project material, render it with photo-push tagged 「AI 示意」, and record the row as 自动 · AI 示意图. It SHALL generate at most 8 images per run and skip this step when no image model is configured.

#### Scenario: Row with no stock and no template
- **WHEN** a row has no eligible stock and no fitting template
- **THEN** it gets a generated image rendered with photo-push and tagged 「AI 示意」

#### Scenario: No image model
- **WHEN** no image model is configured
- **THEN** the row stays a gap with that reason

### Requirement: Illustrations never pass as proof

For a row whose role is proof, the generated picture SHALL carry the tag 「AI 示意，非实拍」 in the frame, and the slot SHALL say real footage is still needed.

#### Scenario: Proof row filled by a picture
- **WHEN** a proof row is filled with a generated picture
- **THEN** the frame shows 「AI 示意，非实拍」 and the slot asks for real footage
