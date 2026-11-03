# product-video-production Specification

## Purpose
TBD - created by archiving change add-product-video-production-skills. Update Purpose after archive.
## Requirements
### Requirement: Product video tasks retain grounded commercial inputs
The system SHALL reuse the existing product creation entry and versioned project brief to bind product identity, selected Persona, audience, objective, exact source/material references, verified claims and supplied offer conditions. Unknown prices, functions, evidence and time limits MUST remain unknown. The prepared execution SHALL freeze the available commercial inputs required by its selected methods. Optional structured offer data SHALL extend the existing product context compatibly; nested product data MUST NOT be placed in scalar-only capability arguments.

#### Scenario: A supplied product has no confirmed discount
- **WHEN** a product task has photos and specifications but no verified offer
- **THEN** feature and visual preparation remain available without invented discount, urgency or testimonial content, and offer motion is skipped or reports missing offer inputs

### Requirement: Product methods use the existing stage controls
The system SHALL expose the six product methods through existing versioned capability resources and independent ordered stage controls. Existing narration, editing, captions/color, music, export and review methods SHALL be reused. Task-level choices MUST preserve Persona expression and unrelated role defaults, and disabled methods MUST not be loaded into execution instructions. Product method selection SHALL be persisted and frozen before the first generation Run, consistently used by preview, dispatch, recovery and subsequent external handoff. A later changed selection MUST NOT retroactively alter dispatched inputs.

#### Scenario: Product methods are selected for a technology Persona task
- **WHEN** the editor chooses product methods before launching the first generation
- **THEN** the prepared package records the selected revisions, order and parameters while keeping the technology Persona's ordinary default and historical executions intact

#### Scenario: A product launch is resumed after method selection changes elsewhere
- **WHEN** the original launch is resumed while live Persona or method revisions have changed
- **THEN** it uses its original frozen selection and invocation identity, and a new selection requires an explicit new Run or task without resubmitting an uncertain dispatch

### Requirement: Product shot planning supports mixed truthful material routes
The executor SHALL classify each shot as actual capture, approved-image manual website video or native graphic/motion work, with its purpose and required input references. Capture work SHALL provide a concrete shot list. Image-to-video SHALL retain existing exact-image confirmation and prompt-image provenance requirements. Generated images or footage MUST NOT be treated as evidence of actual product performance or unknown geometry.

#### Scenario: A complex assembly shot cannot preserve product topology
- **WHEN** inspected generated material changes a critical connector, part count or contact relationship
- **THEN** the shot is not accepted as accurate product demonstration and offers a real capture or static explanation alternative with the unresolved gap recorded

#### Scenario: Only a single front-view photograph is available
- **WHEN** the executor plans product motion
- **THEN** it can plan framed movement or labeled illustrative generation but does not claim a verified backside, true 3D orbit or actual usage demonstration

### Requirement: Product native postproduction is verified through artifacts
Product AE methods SHALL map composition, layers, focal regions, typography, timing and easing to editable native operations. Resolve SHALL own the main edit and final mix/export, with AE intermediates returned to its timeline. Existing source-to-output timing, selected audio intent, optional scene music, output roles and project-reopen contracts SHALL apply.

#### Scenario: Price and product emphasis compositions are produced
- **WHEN** the executor runs the native adapter probes
- **THEN** actual AE compositions and rendered samples match the supplied product and verified numbers, and actual saved AE/Resolve projects reopen with the referenced dependencies and no missing required media

### Requirement: Product route acceptance requires a complete reviewed sample
The change SHALL distinguish source research, method delivery, native probes and complete product sample acceptance. A sample SHALL include supplied product evidence, narration when requested, explicit music/no-music selection, actual editing, required native artifacts and output review. Direct listening status and any estimated alignment SHALL be recorded honestly. Adoption of a reusable product default SHALL be explicit and versioned.

#### Scenario: Only adapter probes have passed
- **WHEN** methods and small native operations work but the first product's material is still missing
- **THEN** implementation progress records the missing product input and does not mark full-route sample acceptance or archive the change as complete

### Requirement: Product method applicability respects node execution semantics
Product method cards SHALL distinguish AI planning and external execution from deterministic workflow nodes. Ordinary prompt skills MUST NOT be passed as configuration patches to graphic composition or professional preparation. Inapplicable selections SHALL be explicitly recorded as skipped for that node, while required deterministic contracts remain effective. Capability arguments SHALL follow the existing scalar schema, with commercial evidence and asset structures retained in their versioned domain documents.

#### Scenario: A visual planning method shares the storyboard stage with graphic composition
- **WHEN** the selected product-visual-consistency method is used by the AI planning node and the following deterministic compose node is prepared
- **THEN** planning receives the selected instruction, composition receives only its validated configuration, and the applicability receipt explains the distinction without a hidden method failure

### Requirement: Reference preserving product imagery uses a capable input route
The workflow SHALL check the actual selected image route before promising reference-preserving generation. Reference editing SHALL pass authorized image bytes or a supported exact asset reference and record the source hash; textual mention of an image MUST NOT count as reference input. The original real product image SHALL remain the identity baseline. If reference editing is unavailable, the workflow SHALL offer original photography, real capture or native compositing that retains the product rather than silently generating a replacement product from text.

#### Scenario: The configured image gateway rejects reference images
- **WHEN** a product image task requires fidelity but the selected route declares reference images unsupported
- **THEN** no reference-editing request is falsely submitted as supported and the task can proceed with the documented original-image or compositing route, recording that route explicitly

### Requirement: Offer animation preserves verified commercial meaning
Offer animation SHALL use verified SKU-specific prices, currency, conditions and explicit time information, with decimal currency-aware calculations and language-appropriate discount representation. When the source supplies a verified deadline, static delivered video SHALL display it with its time zone rather than a wall-clock-dependent or apparently live countdown. Without a verified deadline, the workflow SHALL omit deadline and urgency claims while allowing verified price display. Missing or contradictory offer inputs SHALL block only the affected offer content, not unrelated product creation.

#### Scenario: A supplied percentage disagrees with the supplied sale price
- **WHEN** the claimed percentage and verified original/sale amounts conflict
- **THEN** the workflow records the conflict, retains the supplied source facts and withholds the unsupported discount claim without changing the actual sale price to fit a template

#### Scenario: Valid prices have no supplied deadline
- **WHEN** verified prices and applicable conditions are available but no deadline was supplied
- **THEN** the video can display those prices without inventing an expiration time, countdown or urgency claim

### Requirement: Reviewed product renders retain local-only binding
The system SHALL permit a reviewed accepted final to bind only as the same owner/project/unit/source local render without requiring or granting model, commercial or public reuse permissions. Existing provenance, ancestry, currentness and public Candidate checks SHALL remain effective.

#### Scenario: A restricted reviewed final is kept only as a local render
- **WHEN** a delegated review accepts an exact final from the same owner, project, unit and source document, and its inherited input rights remain valid but its model/public permissions are false
- **THEN** the final can bind only as the local render without granting model, commercial or public permissions, while Candidate and publication continue enforcing their existing rights checks

### Requirement: Product categories with their own skills

Product categories SHALL be first-class, versioned records like personas. Five built-in categories (美妆护肤, 食品零食, 家居日用, 服饰鞋包, 数码 3C) SHALL exist and users MAY add, edit or disable categories. Each category profile SHALL hold a directive, available and default script styles, recommended hooks, a default look, a camera plan and per-stage skill choices, resolved in the order global product defaults → category → SKU plan → launch and frozen into the work snapshot.

#### Scenario: Category drives defaults
- **WHEN** a work is launched for a SKU in 食品零食 without choosing a style
- **THEN** the script stage picks among that category's styles, records the reason, and the director draft uses the category's look and camera plan

### Requirement: Script style skills

Ten script style skills SHALL exist (drama, reversal, interview, story, unboxing, product-pov, comparison, talking-head, pain-point, scene). The launch form SHALL let the user pick a style or leave it to the category recommendation, pin a hook, request 1–3 hook versions and paste a reference structure. Drama-type styles SHALL output a character list and each character SHALL get a distinct voice.

#### Scenario: Pinned style and hook
- **WHEN** the user picks 开箱测评 and pins 反差对比 with two hook versions
- **THEN** the script follows the unboxing structure and returns two opening versions using that hook

### Requirement: Publish copy

A publish-copy skill SHALL produce a title, 3–5 hashtags, cover text, an interaction line and a short description for the delivery channel, saved with the work and editable. It SHALL not export or publish.

#### Scenario: Copy per channel
- **WHEN** the delivery channel is 小红书
- **THEN** the work shows editable title, hashtags, cover text, interaction line and description for 小红书

### Requirement: Camera, look and intensity presets

The platform SHALL provide built-in camera presets (at most two stacked, conflicts excluded), look presets and three motion intensities. Each director shot SHALL carry camera presets, look, intensity and whether it chains from the previous shot, defaulting from the category and editable per shot. The web video handoff prompt SHALL include these together with product-fidelity, stability, single-continuous-shot and no-voice rules; when a shot chains from the previous one, the previous shot's clip SHALL end on this shot's keyframe (its last frame); a single shot's motion prompt MAY be regenerated without changing its keyframe. Shots with people SHALL carry the real-person realism constraint.

#### Scenario: Conflicting presets
- **WHEN** a user stacks a hold-still preset with a moving preset
- **THEN** the second preset is refused with the reason

#### Scenario: Chained shots
- **WHEN** shot 3 chains from shot 2
- **THEN** shot 2's image-to-video uses shot 3's keyframe as its last frame, so the cut does not jump

### Requirement: Production modes and mixed material fill

A product work SHALL choose one of three material modes: photo-only (the whole video from product images), user-footage (edit the user's footage, list gaps) and mixed (default). In mixed mode empty shots SHALL be filled in order: user footage, licensed open stock, image-to-video, ready AE templates, then a listed gap with the reason. Product reveal and call-to-action shots SHALL use the original product image or real footage. Each shot SHALL record where its material came from.

#### Scenario: Photo only
- **WHEN** a work is launched in photo-only mode with one product photo
- **THEN** every other shot gets an image-to-video clip using the photo or the shot keyframe as the first frame, and the reveal and call-to-action shots use the original photo

#### Scenario: Mixed fill
- **WHEN** the user supplies footage for 3 of 6 shots in mixed mode
- **THEN** the other 3 are filled from open stock first, then image-to-video, and each shot shows its source

### Requirement: Image-to-video mode switch

Settings SHALL offer an image-to-video mode, manual (web handoff, default) or automatic (MiniMax H3), overridable per work and per shot. Automatic generation SHALL support a first frame, a chained last frame, aspect ratio and duration, show the number of shots before submitting, and keep results as candidates for the user to accept. A failed or rejected automatic shot SHALL switch to manual with the same prompt.

#### Scenario: Default manual
- **WHEN** a user has not changed the setting
- **THEN** image-to-video shots are prepared as web handoffs

#### Scenario: Automatic shot fails
- **WHEN** an automatic shot fails
- **THEN** that shot offers a one-click switch to a web handoff with the same prompt and first frame

### Requirement: Shot stills with the product as reference

Settings SHALL offer a shot-image model chosen from registered image-generation models. Generating a shot still SHALL send the product photo as a reference image (OpenAI-compatible image edits or the Gemini native protocol, per binding), follow the video's aspect ratio, ask to keep the product unchanged, store the result as an AI-labelled project image, and optionally set it as the shot's image-to-video first frame. Product reveal and call-to-action shots SHALL refuse a generated still as first frame.

#### Scenario: Still becomes the first frame
- **WHEN** a still is generated for shot 1 with as_first_frame
- **THEN** shot 1's next image-to-video starts from that still and the clip can be bound into the video

### Requirement: Subject consistency gate and manual / automatic paths

Every generated still SHALL be checked against the product photo by an image-capable model for shape, colour, material, logo or lettering, accessories and proportion; a failing still SHALL be regenerated with the problems fed back, at most three times, and a still that never passes SHALL not be used. Only passing stills MAY become a first frame, and the verdict SHALL be stored with the image and shown on the page. In manual mode the page SHALL offer the still for download with the video prompt and accept the user's finished video for that shot; in automatic mode the platform SHALL run still, check, image-to-video and placement into the shot, stopping with the reason at any failed step.

#### Scenario: Still fails the check
- **WHEN** a generated still changes the product's logo
- **THEN** it is regenerated with that problem stated, and after three failures it is not used and the reason is shown

#### Scenario: Manual upload
- **WHEN** a shot is manual and the user uploads a finished video
- **THEN** the video goes into the project folder and is used for that shot

### Requirement: Product works use the product's latest main image

For product video works, shot still generation, the product consistency check, image-to-video reference images and the brief SHALL use the main image of the product's latest revision that has one, while product facts stay frozen at the revision the work started with. A product reference image chosen on the work itself SHALL take precedence. Already generated stills and videos SHALL NOT change.

#### Scenario: Main image replaced after the work started
- **WHEN** work 90 started on product 8 revision 1 (main image 315) and the product is now at revision 3 (main image 319)
- **THEN** the next shot still, consistency check and image-to-video request for work 90 use image 319

#### Scenario: Manually chosen product reference
- **WHEN** a work has its own product reference image set
- **THEN** that image is used, not the product's latest main image

### Requirement: Video saves check against the current settings

When a 导演稿 or shot material choice is saved for a video work that already has a 导演稿, the save SHALL be checked against the context computed from the work's current settings, not against the context stored with the previous 导演稿 version. A settings change made by someone else while the save is in progress SHALL still be refused.

#### Scenario: Main image changed after approval
- **WHEN** work 90's product main image or footage mode changed after its 导演稿 was approved and the MCP saves a new 导演稿
- **THEN** the save succeeds and the new version records the current context

### Requirement: HLG footage is restored to its phone appearance before editing

The edit rules sent with every video brief SHALL require checking each live clip's transfer characteristic and applying the stored iPhone HLG-to-SDR LUT only to HLG clips, in a non-color-managed project, leaving SDR stock, generated images and overlays untouched, and verifying brightness on the rendered file against the phone's own display frame. The LUT files SHALL be kept in the repository with install instructions.

#### Scenario: iPhone HLG product footage
- **WHEN** a product video uses iPhone HLG clips and a stock SDR clip
- **THEN** only the HLG clips get the LUT and the rendered brightness matches the phone's display of the same frame

### Requirement: Footage is unified before the sample is exported

Before exporting a 小样, the editor SHALL correct exposure and white balance and match shots of the same scene to a reference shot without stylised grading, level each live dialogue segment to a common loudness, lightly denoise obvious noise and fix one-sided mono, then mix to the existing targets. The delivery receipt SHALL list the color and audio adjustments per shot.

#### Scenario: Clips shot on different days
- **WHEN** a 小样 uses clips from two shooting sessions with different brightness and speech levels
- **THEN** the delivered 小样 shows matched brightness between adjacent shots of the same scene and level speech, and the receipt lists what was changed

### Requirement: Delivery checks flag exposure, brightness jumps and uneven speech

On 小样 and 成片 delivery the platform SHALL sample each shot along the 导演稿 timeline and warn, without blocking, about over-exposed shots, large brightness jumps between adjacent shots and uneven dialogue loudness, naming the shot and the measured difference. Thresholds SHALL be configurable.

#### Scenario: Over-exposed shot
- **WHEN** a delivered 小样 has a shot whose highlights are largely clipped
- **THEN** the review page warns about that shot with its measured brightness

### Requirement: A finished product video can be copied

Copying a product video unit SHALL NOT require a persona. The copy SHALL keep the product link (product, product revision, plan and launch settings) and start with the original's current production settings, and SHALL restart from the original's approved 导演稿 without its materials, voice or cuts.

#### Scenario: Copying work 90
- **WHEN** the user copies the finished product video 90
- **THEN** a new product video unit is created in project 46 with the same product link and settings, starting at the approved 导演稿

### Requirement: Voiceover can cover only marked shots

A 导演稿 shot MAY carry `dub_persona` naming a persona; its line SHALL be voiced with that persona's fixed voice, and a persona without a voice SHALL be refused with a prompt to set it first. When any shot is marked, voiceover generation SHALL synthesize only the marked shots' lines in their personas' voices, fit each line within its shot (speeding up to 1.25× once, otherwise failing with the needed and available length), place them at their shots' start times on one full-length track with silence elsewhere and matching subtitle times, and SHALL NOT change any shot's duration. Without marked shots, generation SHALL behave as before.

#### Scenario: One mother line in a live-sound video
- **WHEN** work 92's shot 10 has a line and `dub_persona` naming the mother persona and voiceover is generated
- **THEN** only that line is synthesized, it starts at shot 10 and fits within it, and every other shot keeps its duration and live sound

### Requirement: Every product video has a persona

Creating a product video SHALL require a persona, and the persona SHALL be changeable later from the work's first step. A product video without a persona SHALL show a prompt to choose one, and its brief, voiceover and image generation SHALL be refused with a message that no persona is chosen. Changing the persona SHALL NOT alter already generated 导演稿, images or voice, and the page SHALL say the 导演稿 needs rewriting to speak as the new persona.

#### Scenario: Old product video without a persona
- **WHEN** the user opens product video 92, which has no persona
- **THEN** step 1 asks to choose a persona, and the editor's brief request is refused until one is chosen

### Requirement: Product video content follows the persona

A product video's brief SHALL carry the persona's profile, speech samples, brand rules, voice and portrait. Structure SHALL follow the product script style and hook, while wording, tone, catchphrases and how viewers are addressed — including the publish copy — SHALL follow the persona's profile and speech samples. The persona's own writing-method skill SHALL NOT be applied to product videos.

#### Scenario: Persona with speech samples
- **WHEN** a product video belongs to a persona with a speech-sample folder
- **THEN** the brief includes those samples and the rule to write the lines in the persona's way of speaking

### Requirement: A dubbed line may start in the previous shot's silent tail

For a shot marked with `dub_persona`, the silent tail of the previous shot — from the end of the last subtitle cue inside the previous shot to the start of this shot — SHALL be usable. A line that fits its shot at the persona's normal speed SHALL start at the shot; one that does not but fits tail plus shot SHALL start early, as late as possible, ending 0.1 s before the shot ends and never before that last cue ends; only if it still does not fit SHALL it be sped up (at most 1.25× over tail plus shot), otherwise refused. The lead in milliseconds and the actual start SHALL be recorded with the voiceover, subtitles SHALL follow, and no shot duration SHALL change. There is no tail when the previous shot is itself dubbed or the shot is first.

#### Scenario: Work 92 mother line
- **WHEN** shot-9 of work 92 is dubbed by 懒羊羊小王, the previous shot's last cue ends at 27.867 s and shot-9 runs 28.467–32.267 s
- **THEN** the line keeps speed 1.1, starts around 27.9 s, ends before 32.27 s and does not overlap 「哇，我超爱的」

### Requirement: The persona is chosen per work when creating it

The product video workbench SHALL NOT show a page-wide persona selector. Every action that creates a product video work SHALL first ask which persona this work uses (required) and create the work only after one is chosen.

#### Scenario: New video for a product
- **WHEN** the user clicks 为此商品新建视频 on 敏贝贝薯乐酥
- **THEN** a dialog asks for the work's persona, and the work is created with the chosen persona after 开始制作

### Requirement: The cover is taken from the rendered final cut

The edit rules SHALL require the cover design to be rendered as the opening of the final cut and the cover image to be extracted from the rendered file within its first 0.5 s, never composited separately from source footage; the final cut SHALL be tagged sRGB (BT.709 primaries, sRGB transfer, BT.709 matrix) by retagging without re-encoding, and the cover saved as sRGB.

#### Scenario: Cover made in AE from source footage
- **WHEN** the editor composites a cover in AE from the original clip
- **THEN** this breaks the rule; the cover must be a frame of the rendered final cut

### Requirement: Delivery warns about cover mismatch and non-sRGB tags

When both a cover and a final cut of one task are delivered, the platform SHALL compare the cover with frames from the first 0.5 s of the final cut, take the closest, and warn 「封面与成片颜色不一致」 when the average per-channel difference exceeds a configurable threshold (default 6 of 255), naming the difference and time. A final cut whose color tags are not sRGB SHALL be warned about. Warnings SHALL NOT block delivery.

#### Scenario: Cover from a different grade
- **WHEN** a final cut is delivered with a cover composited from the source footage
- **THEN** the review page shows 「封面与成片颜色不一致」 with the measured difference

### Requirement: The 导演稿 can carry a dialogue track separate from the picture

A video 导演稿 MAY contain one timeline track of kind `dialogue` whose segments name a source material, its trimmed span, the placement on the cut and optionally the script line. Segments MAY cross shot boundaries. Saving SHALL refuse a segment whose material is missing or unusable, whose trim exceeds the material's duration, whose placement falls outside the cut, whose trimmed and placed lengths differ, that overlaps another segment on the track, or that names an unknown script line, saying which segment and why. Dialogue-track materials SHALL enter the edit package and the edit-manifest check like music and voice. Without a dialogue track, editing follows each shot's own sound.

#### Scenario: Voice from a clip that is not any shot's picture
- **WHEN** work 93's 导演稿 places material 455 from 0.70–2.97 s at 12.30–14.57 s on a dialogue track
- **THEN** it saves, material 455 is in the edit package, and the 导演稿 page shows that source beside the line

#### Scenario: Overlapping segments
- **WHEN** two dialogue segments overlap in time
- **THEN** the save is refused naming both segments

### Requirement: Dialogue level checks skip shots nobody speaks in

The dialogue loudness check SHALL treat a shot as spoken only when it has a script line and its board speaker is not none; unspoken shots SHALL NOT be measured for dialogue or included in the median, while their brightness checks still run.

#### Scenario: Closing shot with on-screen text only
- **WHEN** task 40 of work 93 is checked and its last shot has speaker none with a caption line
- **THEN** no dialogue_level_uneven warning is given for it and the other shots read the same as before

### Requirement: SDR live footage is compensated for the render offset

Edit rules SHALL remove the davinciYRGB render darkening at its cause: every RGB file exported from AE, with or without alpha, is set to Data Level Full before it goes on the timeline, ordinary SDR live footage gets no compensation LUT, and HLG clips get only `iphone-hlg-apple-sdr.cube`. The rules SHALL tell the editor not to use, and to delete from Resolve's MCP folder, the old `sdr-render-comp.cube` and `iphone-hlg-apple-sdr-render.cube`, and the receipt SHALL say which AE files were set to Full.

#### Scenario: Selfie SDR clip under an AE overlay
- **WHEN** a product video puts an AE overlay over a bt709 HEVC selfie clip
- **THEN** the rules require the overlay at Data Level Full and no LUT on the selfie clip, so the render matches the source brightness

### Requirement: Delivery compares final and source brightness for live shots

On 成片 and 小样 delivery the platform SHALL, for each shot whose picture is an SDR video material, compare the mean luma of the delivered frame at the shot's middle with the source frame at the matching time, and warn when they differ by more than a configurable threshold (default 8). HLG sources and unreadable sources SHALL be skipped. Warnings SHALL NOT block delivery.

#### Scenario: Task 41
- **WHEN** task 41's final of work 93 is checked
- **THEN** its SDR selfie shots are flagged as about 20 levels darker than the source

### Requirement: Cut deliveries report each shot's source in-point

A 小样 or 成片 delivery MAY carry `shot_sources` listing, per live-picture shot, the shot id, the picture material and the source in-point in milliseconds. The platform SHALL refuse entries naming an unknown shot, a material outside the edit package, or an in-point that is negative or past the material's duration, saying which entry. Edit rules SHALL require the editor to report them.

#### Scenario: Final with in-points
- **WHEN** a final is delivered with shot-6's in-point 3200 ms in material 455
- **THEN** it is accepted and stored with the output

### Requirement: Source brightness comparison uses reported in-points

The final-versus-source brightness check SHALL sample the source at the reported in-point plus the offset of the shot's middle; shots without a reported in-point SHALL use the in-shot offset and be marked as estimated on the review page.

#### Scenario: Compensated cut
- **WHEN** task 42's final is checked with its true in-points
- **THEN** its SDR shots differ from the source by under 2 levels and no warning is shown

### Requirement: The brightness comparison is recomputed from the edit manifest

When an edit manifest passes its check, the platform SHALL recompute the final-versus-source brightness comparison using each shot's manifest trim_start_ms, converting the in-shot offset by speed_percent for speed-changed clips, and SHALL replace the review warnings with the new readings. Manifest in-points take precedence over delivered shot_sources, which take precedence over estimates.

#### Scenario: Task 42 shot-6
- **WHEN** task 42's edit manifest is applied to the comparison
- **THEN** shot-6 samples the source at about 8.55 s reading about 146.8, every shot is within 2 levels and no warning is shown

### Requirement: Product pages accept several pasted info images

The product edit page SHALL let the user paste (⌘V) or pick several images at once as product info images, each with one of the product material categories (now including certificate), shown as removable thumbnails and saved with the product revision. Certificate SHALL be an accepted product material category.

#### Scenario: Paste a certificate
- **WHEN** the user pastes three images, marks one as 证书 and saves
- **THEN** the new product revision holds the three images with their categories

### Requirement: The video brief carries the product's info images

A product work's video brief SHALL list the info images of the product's newest revision with their categories, and the rules SHALL tell the third-party model to put certificate and specification images on matching shots as they are, never generated or altered.

#### Scenario: Image added after the work started
- **WHEN** the user adds a certificate image to a product that already has a work
- **THEN** that work's next video brief lists the certificate image

### Requirement: Shot checks keep every brightness warning when many shots are flagged

The stored shot checks of a 小样 or 成片 SHALL allow up to 8000 characters, with the same allowance wherever output metadata is validated or re-read, so that 20 shots each carrying an average and a highlight warning keep every warning and their per-shot readings and can be recomputed from the edit manifest. When even that does not fit, the brightness comparison warnings SHALL be kept before any other warning is dropped. Records stored in the full, 4-item slim and 6-item slim forms SHALL still display and recompute.

#### Scenario: Twenty darkened shots
- **WHEN** a final has 20 shots each with an average and a highlight warning
- **THEN** all 40 warnings and the per-shot readings are stored, and the edit manifest recompute runs

#### Scenario: Sixty shots that do not fit
- **WHEN** the checks of 60 shots exceed the allowance
- **THEN** the brightness comparison warnings are kept first and only other warnings are dropped before them

### Requirement: Delivery checks read frames with accurate conversion

Frame readings used by the delivery checks (average, highlight, overexposure, clipping and cover colour) SHALL differ from the standard conversion (Y−16)×255/219 by at most 1 level whether the video is tagged bt709, smpte170m or untagged. Stored checks SHALL record which reader produced them, and a recompute from the edit manifest SHALL read the sources with the same reader as the stored delivered readings. Threshold defaults stay unchanged.

#### Scenario: bt709 solid colour
- **WHEN** a lossless bt709-tagged video with Y=235 is read
- **THEN** the reading is 255 within 1 level

#### Scenario: Task 42 cover
- **WHEN** task 42's cover is compared with its final using accurate conversion
- **THEN** the difference is about 2 levels, below the default threshold 6, and no warning is given

### Requirement: One brightness warning per shot

The final-versus-source comparison SHALL give at most one warning per shot, carrying the average and/or highlight difference that crossed its threshold, so that 30 darkened shots plus a colour-tag, an overexposure and a dialogue warning keep every warning and the per-shot readings and can be recomputed. When the checks still do not fit, brightness and colour-tag warnings SHALL be kept first. Older records with separate average and highlight warnings, and full, 4-item and 6-item slim readings, SHALL still display and recompute.

#### Scenario: Thirty darkened shots
- **WHEN** 30 shots are darker than their sources in average and highlight, with one colour-tag, one overexposure and one dialogue warning
- **THEN** all 33 warnings and the per-shot readings are stored and the edit manifest recompute runs

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

### Requirement: Marked shots of portrait-less persona works may show other people without faces

A 导演稿 shot board SHALL accept an optional other_people text (1–60 characters, not blank) naming people in the picture who are not the persona, such as 宝宝 or 医护人员的手; it SHALL be stored only when written so existing drafts keep their hashes, and an invalid value SHALL be refused with the reason. For a persona work without a portrait, every generated prompt of a marked shot (first-frame still, image-to-video and text-to-video in Chinese and English, single stills, storyboard sheets and cell redraws) SHALL say that the persona never appears, that the named people may appear only as hands, feet, part of the body or from behind with no face, front or side view, and that no other people appear; the "no person, no body" rule SHALL not appear for that shot. Unmarked shots keep the no-person rule unchanged, and persona works with a portrait and product works ignore the field. The page and person_notices SHALL state for a marked shot that the named people may appear without a face.

#### Scenario: Shot marked 宝宝
- **WHEN** a shot of work 94 is marked other_people 宝宝
- **THEN** its prompts allow the baby's hands, feet and body without a face, exclude the persona and anyone else, contain no "不出现身体", and the page says this shot may show 宝宝 without a face

#### Scenario: Unmarked shot
- **WHEN** a shot of the same work is not marked
- **THEN** its prompts are identical to before

#### Scenario: Invalid value
- **WHEN** a draft is saved with other_people longer than 60 characters, blank or not text
- **THEN** the save is refused with the reason

#### Scenario: Product work
- **WHEN** work 93's prompts are read
- **THEN** they are identical to before

