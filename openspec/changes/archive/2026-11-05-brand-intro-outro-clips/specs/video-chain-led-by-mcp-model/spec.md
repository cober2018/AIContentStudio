## ADDED Requirements

### Requirement: Brands carry intro and outro clips

A brand profile SHALL accept `intro_clip` and `outro_clip`, each with an optional 16:9 and an optional 9:16 video material revision. Saving SHALL refuse a clip that is not the user's own, not a video, not allowed for public use, not allowed for model use, or longer than 5 seconds. The brand settings page SHALL let the user pick a library video for each slot, preview it and clear it.

#### Scenario: Clip too long
- **WHEN** the user sets a 7-second video as the 9:16 outro
- **THEN** saving is refused saying the clip must be at most 5 seconds

### Requirement: The 成片 task carries the brand's clips

When `prepare_video_edit` opens a final task, the platform SHALL find the work's brand through its persona and, for each brand clip in the work's aspect, attach it to the project and add it to the package as a `brand_clip` asset and in `director.brand_clips` with its duration; with no brand or no matching clip it SHALL add nothing and say 本作品没有品牌收尾. 小样 tasks SHALL never carry brand clips. The edit rules SHALL say the outro goes unchanged at the very end with its own sound, voice and music ending before it; an intro goes first and the cover is then cut within 0.5 s after the intro.

#### Scenario: Persona under a brand with an outro
- **WHEN** a 9:16 work of a persona whose brand has a 9:16 outro opens its 成片 task
- **THEN** the package carries that outro and the result names it and its length

#### Scenario: No brand
- **WHEN** the work's persona has no brand
- **THEN** nothing is added and the result says 本作品没有品牌收尾

### Requirement: Brand clips are checked at delivery

When the package carries brand clips, the edit manifest SHALL list `brand_clips` [{slot, material_revision_id, start_ms, end_ms}] matching them within one frame, kept out of timeline and shot checks. On the 成片, the platform SHALL warn on the review page, without blocking, when its length is not the approved 小样 length plus the clips within one frame, or when its last (and, with an intro, first) frames do not match the clips; the cover check SHALL compare against the half second after the intro. The review page SHALL show 已加品牌收尾 X 秒（素材名）.

#### Scenario: Missing from manifest
- **WHEN** the package has an outro and the manifest has no brand_clips
- **THEN** the manifest is refused

#### Scenario: Outro not at the end
- **WHEN** the delivered 成片's last frames differ from the outro clip
- **THEN** the review page shows a warning and the delivery is kept
