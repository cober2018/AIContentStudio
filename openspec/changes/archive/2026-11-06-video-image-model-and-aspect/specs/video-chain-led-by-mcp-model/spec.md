## ADDED Requirements

### Requirement: generate_video_image follows the 封面生图 setting and takes an aspect ratio

generate_video_image SHALL generate with the model chosen as 封面生图 (uses.cover_image) and, when none is chosen or it cannot generate images, with the last successful image route, saying so in the result. It SHALL accept an optional aspect_ratio of 1:1, 4:3, 3:4, 16:9 or 9:16, defaulting to the work's 导演稿 aspect ratio and to 9:16 without one. It SHALL ask for the size a cover is used at (16:9 1920×1080, 3:4 1080×1440, 9:16 1080×1920, 4:3 1440×1080, 1:1 1440×1440) within the platform's per-request pixel limit and, for a model measured to return only about one megapixel (grok-imagine-image), at 1048576 pixels directly, falling back once to 1048576 pixels when the model definitively refuses or returns another size. The result SHALL name the provider, the model id, the width and the height.

#### Scenario: Grok chosen, landscape work
- **WHEN** 封面生图 is Grok and generate_video_image runs for a 16:9 work without aspect_ratio
- **THEN** a 16:9 image of 1280×720 is made directly and the result names grok-imagine-image, its size and that the model tops out at about one megapixel

#### Scenario: Vertical cover base
- **WHEN** the same call passes aspect_ratio 3:4
- **THEN** a 3:4 image is made

#### Scenario: Setting unusable
- **WHEN** 封面生图 is not set
- **THEN** the last successful image route is used and the result says so
