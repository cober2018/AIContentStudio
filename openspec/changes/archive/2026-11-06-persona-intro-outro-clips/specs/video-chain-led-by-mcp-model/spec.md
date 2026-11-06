## ADDED Requirements

### Requirement: Personas carry intro and outro clips

A persona profile SHALL accept `intro_clip` and `outro_clip`, each with an optional 16:9 and an optional 9:16 video material revision. Saving SHALL refuse a clip that is not the user's own, not a video, not allowed for public use, not allowed for model use, or longer than 5 seconds, saying why. The persona edit page SHALL let the user pick a library video for each slot, preview it, replace it and clear it, and the persona profile view SHALL show each clip's name and length. Brand profiles SHALL no longer carry clips; older brand revisions that still hold them SHALL open without error.

#### Scenario: Clip too long
- **WHEN** the user sets a 7-second video as the persona's 9:16 outro
- **THEN** saving is refused saying the clip must be at most 5 seconds

#### Scenario: Old brand revision
- **WHEN** a brand whose earlier revision holds `outro_clip` is opened and saved
- **THEN** it opens and saves normally and the new revision has no clip fields

### Requirement: The 成片 task carries the persona's clips

When `prepare_video_edit` opens a final task, the platform SHALL take, from the current profile of the work's persona, each clip in the work's aspect, attach it to the project and add it to the package as a `persona_clip` asset and in `director.persona_clips` with its duration; with no persona or no matching clip it SHALL add nothing and say 本作品没有角色收尾. 小样 tasks SHALL never carry clips. The edit rules SHALL say the outro goes unchanged at the very end with its own sound, voice and music ending before it; an intro goes first and the cover is then cut within 0.5 s after the intro.

#### Scenario: Persona with an outro
- **WHEN** a 16:9 work of a persona whose 16:9 outro is revision 618 opens its 成片 task
- **THEN** the package carries that outro and the result says 已加角色收尾 4.2 秒 with the clip's name

#### Scenario: Persona without clips
- **WHEN** the work's persona has no clip in the work's aspect
- **THEN** nothing is added and the result says 本作品没有角色收尾

### Requirement: Persona clips are checked at delivery

When the package carries persona clips, the edit manifest SHALL list `persona_clips` [{slot, material_revision_id, start_ms, end_ms}] matching them within one frame, kept out of timeline and shot checks. On the 成片, the platform SHALL warn on the review page, without blocking, when its length is not the approved 小样 length plus the clips within one frame, or when its last (and, with an intro, first) frames do not match the clips; the cover check SHALL compare against the half second after the intro. The review page SHALL show 已加角色收尾 X 秒（素材名）.

#### Scenario: Missing from manifest
- **WHEN** the package has an outro and the manifest has no persona_clips
- **THEN** the manifest is refused

#### Scenario: Outro not at the end
- **WHEN** the delivered 成片's last frames differ from the outro clip
- **THEN** the review page shows a warning and the delivery is kept

## REMOVED Requirements

### Requirement: Brands carry intro and outro clips
**Reason**: Clips are set per persona so personas under one brand can differ.
**Migration**: Set clips on the persona; 知数Talk's outro moves to 量化研究专家 as revisions 618 / 619.

### Requirement: The 成片 task carries the brand's clips
**Reason**: Replaced by "The 成片 task carries the persona's clips".
**Migration**: None; no open task carries brand clips.

### Requirement: Brand clips are checked at delivery
**Reason**: Replaced by "Persona clips are checked at delivery".
**Migration**: None.
