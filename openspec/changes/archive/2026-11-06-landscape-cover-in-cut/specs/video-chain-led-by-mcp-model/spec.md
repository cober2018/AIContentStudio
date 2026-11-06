## MODIFIED Requirements

### Requirement: Landscape works deliver two separate covers

A 成片 task opened for a work whose director document is 16:9 SHALL list an output role `cover_vertical` beside `cover`. For such a task the 16:9 cover design SHALL be laid over the first 0.5 s of the 成片 and rendered with it, without lengthening the 成片 and with voice and subtitles as usual; `cover` SHALL be one frame cut from the first 0.5 s of the rendered 成片, 1920×1080. `cover_vertical` SHALL be the same design laid out for 3:4, 1080×1440, made separately and not placed in the 成片. Both are jpg or png in sRGB, exported to cover_dir and delivered before the edit manifest, which lists both in output_hashes. Either may be redelivered until the task is approved, the newest shown on the review page. When the 成片 is approved both become the work's covers, the vertical one as `cover.vertical_material_revision_id`. A cover redo on such a task SHALL be complete only when both covers are delivered again. Tasks without `cover_vertical`, including all 9:16 works and tasks opened before the landscape change, SHALL keep the current cover rules.

#### Scenario: Landscape 成片 task
- **WHEN** a 16:9 work opens its 成片 task
- **THEN** the result and the rules say the 16:9 cover is laid over the start of the 成片 and cut from it, and the 3:4 cover is delivered separately at 1080×1440

#### Scenario: Portrait work unchanged
- **WHEN** a 9:16 work opens its 成片 task
- **THEN** the cover is still cut from the start of the 成片 and compared with it

### Requirement: Landscape covers are checked by size, not against the 成片

For a task with `cover_vertical`, the platform SHALL compare `cover` with the start of the 成片 as for other tasks (after an intro clip when there is one) and warn cover_color_mismatch on the review page when they differ; it SHALL NOT compare `cover_vertical` with the 成片. It SHALL warn, without blocking, when either cover is missing or not its required size, in plain words. With a persona cover template, both covers SHALL be checked for cover_template_missing / mismatch. The review page SHALL show both covers side by side as 横封面 16:9 and 竖封面 3:4, saying 还没交 for a missing one, and the delivery step SHALL show both covers of a landscape work with a download for each.

#### Scenario: Only one cover
- **WHEN** the model delivers only the 16:9 cover
- **THEN** the review page says the 3:4 vertical cover has not been delivered

#### Scenario: Wrong size
- **WHEN** the vertical cover is 1080×1920
- **THEN** the review page says it should be 1080×1440

#### Scenario: Horizontal cover differs from the opening
- **WHEN** the 16:9 cover does not match the first 0.5 s of the 成片
- **THEN** the review page shows the colour mismatch warning

#### Scenario: Both right
- **WHEN** both covers have the right size and the 16:9 cover matches the opening
- **THEN** the review page shows both with no cover warning
