## ADDED Requirements

### Requirement: Landscape works also deliver a 4:3 cover

A 成片 task opened for a 16:9 work SHALL list an output role `cover_43` beside `cover` and `cover_vertical`. `cover_43` SHALL be 1440×1080, cut from the centre of the 16:9 cover (240 px off each side), so the cover design keeps its title within the centre 4:3 area; it is delivered like the other covers, may be redelivered until approval, counts toward a cover redo, and becomes the work's cover as `cover.four_three_material_revision_id`. The review page SHALL warn when it is missing or not 1440×1080. The delivery package SHALL carry the 4:3 and 3:4 covers for 抖音 and the 16:9 cover for other platforms. Tasks opened before this change SHALL keep their two covers.

#### Scenario: Landscape 成片 task
- **WHEN** a 16:9 work opens its 成片 task
- **THEN** the result and the rules ask for cover 1920×1080, cover_43 1440×1080 cut from its centre, and cover_vertical 1080×1440

#### Scenario: Package for 抖音
- **WHEN** a finished landscape work is authorized for 抖音 and for B站
- **THEN** the 抖音 package holds the 4:3 and 3:4 covers and the B站 package holds the 16:9 cover

### Requirement: Every work has one publish copy, in a video or a graphic format

Each work SHALL have one general publish copy, not one per platform. A video work's copy SHALL hold title, hashtags, cover text, one interaction line and description, written for persona works with studio.persona.publish-copy (title up to 30 characters, 3–5 hashtags, cover text up to 12, description up to 300) and for product works with studio.product.publish-copy as before. A graphic work's copy SHALL hold title, a lead paragraph up to 120 characters, 3–5 hashtags and one interaction line, written with studio.persona.graphic-copy. Saving SHALL refuse a copy whose format does not match the work. The delivery step SHALL show and edit it, delivery packages of finished videos and of graphic works SHALL carry it as 发布文案.txt, and saving copy for a finalized video work SHALL create a new review candidate carrying it.

#### Scenario: Persona video copy
- **WHEN** the model saves copy for work 95
- **THEN** every platform's package for work 95 carries that copy and the review center shows a new candidate to approve

#### Scenario: Wrong format
- **WHEN** a copy with a cover text is saved for a graphic work
- **THEN** it is refused saying graphic copy has no cover text
