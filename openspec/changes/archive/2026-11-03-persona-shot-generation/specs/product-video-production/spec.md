## ADDED Requirements

### Requirement: The 导演稿 groups shots that must stay consistent

The 导演稿 (video.master.v2) SHALL accept optional consistency_groups, each with an id, at least two shot_ids, an optional shared person and a shared setting; every shot SHALL exist, belong to at most one group and not be an AE template or a library shot. The external model SHALL group shots to be generated that need the same person or the same setting, and SHALL leave unrelated shots ungrouped. The draft review SHALL list the groups, and changing them is a draft change that needs approval again.

#### Scenario: Invalid group
- **WHEN** a draft is saved with a group of one shot, an unknown shot, a shot in two groups or a library shot
- **THEN** the save is refused with the reason

#### Scenario: Unrelated B-roll
- **WHEN** a draft's shots to be generated are unrelated to each other
- **THEN** no group is written and each shot is made on its own

### Requirement: Storyboard grids are made per group in a dialog

A storyboard grid SHALL be generated for one consistency group, from the group's shots, person and setting, and there SHALL be no default of drawing every shot. The page SHALL open the grid in a dialog for one group, showing the group's shots, shared person and setting, references, generation progress, the whole sheet, and per shot the candidates, use-as-first-frame, redraw, first-frame download, the image-to-video prompt in Chinese and English with copy buttons, manual / automatic mode, automatic generation and upload of the finished video. The former inline grid panel SHALL be removed. Product works keep the product reference and per-cell product check; persona works use neither. The first-frame and image-to-video prompts of a grouped shot SHALL carry the group's person and setting.

#### Scenario: Grid for a group
- **WHEN** the grid is generated for group g1 of shots 3, 4 and 5
- **THEN** only those shots are drawn on one sheet, each cell becomes that shot's first-frame candidate, and their prompts carry g1's setting

### Requirement: Persona works generate pictures and clips for shots without footage

After the 导演稿 is approved, a persona video work (production_domain persona) SHALL offer, in the 素材 step and over MCP, for every shot without the user's footage: automatic image-to-video started by the user, and a manual route — text-to-video for ungrouped shots, where the page shows a text-to-video prompt in Chinese and English with copy buttons, or image-to-video, where the platform makes the picture (a single still for an ungrouped shot, the group's storyboard grid for a grouped shot) and the page shows the image-to-video prompt in Chinese and English with copy buttons — after which the user uploads the finished video onto that shot. Web image search stays on the page. Persona works SHALL send no product reference, run no product consistency check and apply no reveal / call-to-action restriction; prompts SHALL be written from the shot's board (picture, camera, person's attitude) and the fixed rules SHALL not mention a product. Without a persona portrait no person SHALL be drawn (setting only, hands when something is handled), stated in every prompt and on the page; with a portrait the person SHALL follow it. Uploaded clips keep the existing labelling. Camera presets and publish copy stay product-only, and apart from the grid entry product works SHALL behave as before.

#### Scenario: Work 94
- **WHEN** work 94's approved 导演稿 has no groups and shots 5, 10, 14, 18 and 21 have no footage
- **THEN** the 素材 step lists those five shots with automatic, text-to-video and image-to-video entries, and states that no person will appear because the persona has no portrait

#### Scenario: Manual upload reaches the edit
- **WHEN** the user uploads a finished video for a persona shot
- **THEN** the clip is placed on that shot, read by get_shot_slots as chosen, and included in the inputs of the sample edit opened by prepare_video_edit

#### Scenario: Automatic clip without a first frame
- **WHEN** automatic image-to-video is started on a persona shot with no first frame
- **THEN** it is refused with a message to generate a first frame or switch to manual

#### Scenario: Product works unchanged
- **WHEN** a product work generates a still, an automatic clip or uploads a manual clip
- **THEN** the product reference, consistency check, reveal restriction, prompts and upload labelling are the same as before
