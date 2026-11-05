## ADDED Requirements

### Requirement: A persona's cover template rides with every edit task

A persona profile SHALL accept `cover_template` {id, version} naming a 封面 category template, refusing any other template. When a work's persona has one, a newly opened edit task's package SHALL carry it with its fields and limits, and the edit rules SHALL require rendering the cover text layer with `render_ae_template` of that template, laying it over the film's opening and cutting the cover from the rendered film. A cover output SHALL carry `cover_template_render` (the render's material revision id); the platform SHALL warn on the review page, without blocking, when it is missing (`cover_template_missing`) or is not a render of that template and version in this project (`cover_template_mismatch`). Personas without a cover template SHALL behave as before.

#### Scenario: Right template
- **WHEN** the cover is submitted with a render of the persona's cover template
- **THEN** no template warning is shown

#### Scenario: No receipt
- **WHEN** the cover of a persona with a cover template is submitted without `cover_template_render`
- **THEN** the review page shows 「封面没用角色的封面模板」

### Requirement: The cover can be resubmitted and redone

Before the task is accepted, the model SHALL be able to submit the cover slot again as a new attempt while the earlier one stays in history; the review page SHALL show the newest. The cover SHALL not be compared in the edit manifest's `output_hashes`. Other outputs SHALL still refuse replacement. The 小样 and 成片 review pages SHALL offer 「重做封面」 with an optional note; it SHALL record a cover-redo request without sending the cut back, `get_video_decision` SHALL return it with the note, and a newer cover submission SHALL settle it. While a cover redo is open, approving the 成片 SHALL be refused with 「封面重做中」.

#### Scenario: Cover replaced
- **WHEN** the model submits a second cover before the task is accepted
- **THEN** it is registered as attempt 2, attempt 1 stays in history and the review page shows attempt 2

#### Scenario: Other output still locked
- **WHEN** the model submits the final cut again while the first is staged
- **THEN** it is refused with `creative_execution_output_replacement_denied`

#### Scenario: Redo requested
- **WHEN** the user clicks 重做封面 with the note 「卖点字再大一点」 on the 成片
- **THEN** the 成片 stays waiting for review, `get_video_decision` returns the redo request with that note, and 通过 is refused until a new cover arrives
