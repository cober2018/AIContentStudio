# video-chain-led-by-mcp-model Specification

## Purpose
TBD - created by archiving change video-chain-led-by-mcp-model. Update Purpose after archive.
## Requirements
### Requirement: Video is led by the external model

In the video chain, the 导演稿, material choices, voiceover call, DaVinci / AE decision, 小样, 排版 and 成片 SHALL be decided by the external model through the platform MCP. The platform SHALL NOT call its own models for these steps. Articles and images SHALL keep the platform's abilities.

#### Scenario: Start from the conversation
- **WHEN** the user tells Claude Code 「做海底光缆的视频」
- **THEN** Claude Code reads the brief through MCP, writes the 导演稿 and saves it, and the page shows 导演稿待你看

#### Scenario: No platform model button
- **WHEN** the user opens a video's 内容方案
- **THEN** there is no 生成导演稿 or AI 补齐素材 button; the page shows the current state and review actions

### Requirement: Material request with the 导演稿

The 导演稿 SHALL include a material request per shot. The user SHALL be able to supply material for it; rows the user does not cover SHALL be found or made by the external model through platform tools, and the external model SHALL pick the material for every shot.

#### Scenario: User supplies some footage
- **WHEN** the user adds footage for rows 2 and 5 and approves the 导演稿
- **THEN** rows 2 and 5 use it, the other rows are found or made, and the receipt says which is which

### Requirement: Made in DaVinci Resolve and After Effects

小样, 排版 and 成片 SHALL be produced in DaVinci Resolve and After Effects as far as possible; other tools SHALL be used only for checks and format conversion.

#### Scenario: 小样
- **WHEN** a 小样 is submitted
- **THEN** it comes with its Resolve project and AE files that reopen without missing media

### Requirement: Stops for the user

The chain SHALL stop for the user after the 导演稿, after the 小样 and after the 成片, and SHALL continue only after the user approves on the page.

#### Scenario: 导演稿 changes
- **WHEN** the user leaves notes on the 导演稿
- **THEN** Claude Code saves a new 导演稿 version and waits again

#### Scenario: 小样 then 成片
- **WHEN** the user approves the 小样
- **THEN** Claude Code does 排版 and exports the 成片, which goes to 导出/成片 after the user approves it

### Requirement: The edit follows the 导演稿

Picture content SHALL change only through a new 导演稿 version. Details the 导演稿 does not specify SHALL be listed in the edit receipt.

#### Scenario: A shot must change
- **WHEN** a planned picture cannot work while editing
- **THEN** a new 导演稿 version is saved before the edit continues

### Requirement: Materials are allowed by default

Every material in the library SHALL be allowed for AI editing and publishing. Web-found materials SHALL keep their source credit.

#### Scenario: Old material missing AI permission
- **WHEN** the one-off update runs
- **THEN** every active material allows AI use and public use, and attribution text is unchanged

### Requirement: Approving a sample or final shows in progress until it is written

When the user approves a 小样 or 成片, the platform SHALL first record and save an in-progress approval, then accept the task's outputs, then record the approval and clear the marker; a failure SHALL clear the marker. While the marker exists the chain state SHALL be 「正在通过…」 on the page and `approving` in `get_video_decision`, with a note to check again later, never 「待你看」. A marker older than 5 minutes SHALL be ignored.

#### Scenario: Model asks right after the user clicks 通过
- **WHEN** the user approves the 小样 and the model calls get_video_decision while outputs are still being accepted
- **THEN** it reads state approving with the note to check again, not 小样待你看

### Requirement: Platform-written cover check is kept with the output

The platform-written `cover_check` result SHALL be an allowed output metadata field, so deliveries with a cover and a final are not refused, while an executor-supplied value is still discarded.

#### Scenario: Cover then final delivered
- **WHEN** a cover and then a final are delivered for one task
- **THEN** both are accepted and the cover check is stored and shown on the review page

### Requirement: Films default to 60 fps

When the edit is prepared for a work whose 导演稿 has no recorded frame rate, the platform SHALL set the 小样, the 成片 and every AE intermediate composition to 60 frames per second. A work whose 导演稿 already records a frame rate SHALL keep it, so videos already made are not redone. The Resolve timeline and delivery SHALL use the 导演稿's recorded frame rate.

#### Scenario: New work
- **WHEN** the model prepares the edit of a work that has never been prepared
- **THEN** the 导演稿 records 60 fps for the 小样, the 成片 and its AE compositions, and a 30 fps upload is rejected

#### Scenario: Work already at 30 fps
- **WHEN** the model prepares the 成片 of a work whose 小样 was made at 30 fps
- **THEN** the 导演稿 keeps 30 fps

### Requirement: One DaVinci edit at a time

The platform SHALL let only one video edit task (executor `codex-video-production`) be worked at a time across all works. A claim SHALL be refused with `video_edit_queue_busy` while another work's edit task is claimed, in progress or blocked and has had activity (a state change, a progress report or a submitted file) within the last 30 minutes. The refusal SHALL name the work being edited and how many other edit tasks are waiting, and tell the model to try again later. An edit task SHALL stop holding the slot once it reaches result_ready or any later state, or after 30 minutes without activity; the timeout SHALL NOT change that task's state.

#### Scenario: Second work waits
- **WHEN** the model claims work B's edit task while work A's edit task is in progress with a progress report 5 minutes ago
- **THEN** the claim is refused with `video_edit_queue_busy` naming work A, and work B's task stays prepared

#### Scenario: Slot frees on hand-in
- **WHEN** work A's edit task reaches result_ready and the model claims work B's edit task again
- **THEN** the claim succeeds

#### Scenario: Abandoned session
- **WHEN** work A's edit task has had no activity for more than 30 minutes and the model claims work B's edit task
- **THEN** the claim succeeds and work A's task keeps its state

### Requirement: Edit work files on the drive are kept

The platform SHALL NOT delete files in a work's `工作/` folder when a newer 小样 is returned or when the 成片 is approved; renders, AE shots, images and project files there stay.

#### Scenario: 成片 approved
- **WHEN** the user approves a work's 成片 while earlier task folders hold unregistered renders
- **THEN** every file in the work's `工作/` folder is still there

### Requirement: One Resolve project per work

The edit instructions SHALL tell the model to delete the `-reopen` Resolve project right after the reopen check, and, when it starts a new edit task of a work, to delete that work's Resolve projects from earlier tasks, whose exported .drp files stay on the drive.

#### Scenario: Third task of a work
- **WHEN** the model starts task 47 of a work whose tasks 43 to 46 left Resolve projects
- **THEN** after the reopen check only that work's task 47 project remains in the Resolve project list

### Requirement: Paid generations check the material drive first

Voiceover, image, shot image, shot video and storyboard grid generation SHALL check that the material library is writable before calling the provider. When it is not, the platform SHALL return `material_library_unavailable` with the message 「素材库盘没连接」 and SHALL NOT call the provider. Through MCP the model SHALL receive that code and message.

#### Scenario: Drive unplugged
- **WHEN** the material drive is not mounted and the model calls `generate_video_voiceover`
- **THEN** no request reaches MiniMax and MCP returns `material_library_unavailable` with 「素材库盘没连接」

#### Scenario: Drive mounted
- **WHEN** the drive is mounted and the model calls `generate_video_voiceover`
- **THEN** the voiceover is generated and stored as before

### Requirement: Pronunciation in the 导演稿 voice

The video.master.v2 `voice` SHALL accept an optional `pronunciation` list of at most 50 entries, each at most 40 characters in the form `原文/(pinyin+tone)…` with one bracket per character, e.g. `去重/(qu4)(chong2)`; anything else SHALL be rejected with `video_voice_pronunciation_invalid`. Every MiniMax speech request made for the work (whole voiceover, role voices, dub_persona shots, single-line redub) SHALL send it as `pronunciation_dict: {"tone": [...]}`, a cached voiceover SHALL be reused only when its pronunciation matches, saving a generated voiceover SHALL keep the list, and `get_video_brief` SHALL describe the field.

#### Scenario: Polyphonic word
- **WHEN** the 导演稿 voice has `pronunciation: ["去重/(qu4)(chong2)"]` and the line stays 「对齐、去重」
- **THEN** the voiceover request carries `pronunciation_dict: {"tone": ["去重/(qu4)(chong2)"]}`

#### Scenario: Bad entry
- **WHEN** a draft has `pronunciation: ["去重/(qu4)"]`
- **THEN** saving is refused with `video_voice_pronunciation_invalid`

### Requirement: Redub chosen lines in place

`generate_video_voiceover` SHALL accept optional `lines` (script block ids). With `lines`, it SHALL voice only those lines and splice each into the current whole TTS voiceover at the original line's start, keeping every other line's audio and the total length; seams SHALL fall in pauses with a one-frame fade. Line spans SHALL come from the voice's sentence timing; else, when the 导演稿 subtitles group by the script lines, from each line's cue start and end snapped to the nearest speech-run start and end (silence detection -40 dB, 0.15 s) within 0.3 s, checking only the boundaries the redub uses (the chosen lines, the previous line's end, the following line's start) and failing with `voiceover_line_split_unclear` naming the line, which end and how far off when one does not snap or the snapped spans overlap; else from silence detection grouped by the script and checked, failing with `voiceover_line_split_unclear` rather than guessing. A longer new line MAY use the following pause down to a 0.25 s gap; beyond that the call SHALL fail with `voiceover_line_too_long` stating the missing seconds, never changing speed. The result SHALL be a new voice material in the project's 音频 folder; the 导演稿 SHALL get the new voice id and new cue times for those lines only, with shot lengths and other cues unchanged, and only those lines SHALL be billed. Works voiced per shot (dub_persona) or with a dialogue track SHALL be refused. Without `lines`, behaviour SHALL stay as before.

#### Scenario: One line redubbed
- **WHEN** line-34 is redubbed in a 3-minute voiceover
- **THEN** every other line's audio matches the original except one frame either side of each seam, line-34 starts where it did, the total length is unchanged and one line is billed

#### Scenario: Does not fit
- **WHEN** the new line is 0.4 s longer than its line plus the usable pause
- **THEN** the call fails with `voiceover_line_too_long` saying 0.4 秒, and nothing is saved

#### Scenario: Located by subtitles
- **WHEN** a voice has no sentence timing, the 导演稿 subtitles group by line, and a line ending is spoken into the next line's word so proportional grouping would misplace it
- **THEN** each used line boundary is taken from its subtitle cue snapped to the nearest speech-run edge, and the redub proceeds

#### Scenario: Subtitle moved off
- **WHEN** the chosen line's subtitle cues are moved 2 s later
- **THEN** the call fails with `voiceover_line_split_unclear` naming that line, and no TTS is called

#### Scenario: Unused run-on boundary
- **WHEN** two other lines are spoken without a pause between them
- **THEN** redubbing a different line still succeeds

### Requirement: A work's own older edit task never blocks its new one

When the model claims an edit task, the one-edit-at-a-time check SHALL ignore other edit tasks of the same work, and the waiting count SHALL count only other works' tasks; another work's active edit SHALL still block as before.

#### Scenario: New task after a blocked one
- **WHEN** a work's task 51 is blocked with activity 20 minutes ago and the model claims the same work's new task 52
- **THEN** the claim succeeds

#### Scenario: Other work still blocks
- **WHEN** another work's edit task had activity 5 minutes ago
- **THEN** the claim is refused with `video_edit_queue_busy`

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

### Requirement: Adopting a cut keeps model use when only public use is blocked

When the user approves a 小样 or 成片, the platform SHALL accept each output as public and model-usable when every input allows it; when public use is refused but every input allows model use, it SHALL accept the output as model-usable and not public; only when model use is refused too SHALL both be off.

#### Scenario: One input cannot be public
- **WHEN** a 小样 uses an AE render of a logo that is model-usable but not public
- **THEN** the accepted 小样 is model-usable and not public, and the 成片 task can be opened on it

### Requirement: A rights refusal names the shot and the upstream material

When opening an edit task is refused with `video_asset_kind_or_rights_invalid` for rights, the error SHALL carry a message naming the material, the shot that uses it when known, the upstream material that is not public or not model-usable (followed through execution inputs and AE render image sources), and what to do; the MCP SHALL pass the message to the model.

#### Scenario: Blocked by a logo two steps up
- **WHEN** the 成片 is opened on a 小样 whose 关注卡 render used a non-public logo
- **THEN** the message names the 小样, the shot with the 关注卡, the render and the logo, and says to make the logo public, re-render and redo the 小样

### Requirement: Product publish copy lives on the delivery step

For product videos, the publish copy (title, hashtags, cover text, interaction, description) SHALL be edited and saved on the 交付 step, above channel adaptation and beside the work's current cover, through the existing publish-copy API; the 导演稿 step SHALL no longer show it. Without saved copy the page SHALL say the model writes one at finalising and the user may fill it first.

#### Scenario: Copy found after finalising
- **WHEN** the 成片 is approved and the user opens 交付
- **THEN** the five publish copy fields are shown with the work's cover beside them and can be edited and saved

#### Scenario: Not on the 导演稿 step
- **WHEN** the user opens the 导演稿 step of a product video
- **THEN** no publish copy block is shown

### Requirement: Product delivery step has no channel variants

The 交付 step of a product video SHALL show the publish copy beside the cover and SHALL NOT show the channel variant panel; its hint SHALL speak of checking the cut, cover and publish copy rather than channel adaptation. Other work types SHALL keep their delivery step as before.

#### Scenario: Product work at delivery
- **WHEN** the user opens 交付 of a product video
- **THEN** the publish copy is shown and no 渠道变体 panel appears

#### Scenario: Other work at delivery
- **WHEN** the user opens 交付 of a non-product work
- **THEN** the 渠道变体 panel is shown as before

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

### Requirement: The 成片 length check includes persona clips

When a `final` output is submitted for an edit task whose package carries `director.persona_clips`, the platform SHALL require its container and video-stream length to equal `director.timeline.duration_ms` plus the duration of every persona clip, within one frame plus 1 ms. A 小样 and a 成片 without persona clips SHALL be checked against `director.timeline.duration_ms` as before.

#### Scenario: 成片 with an outro
- **WHEN** the timeline is 217283 ms, the outro is 4200 ms and the delivered 成片 is 221483 ms at 60 fps
- **THEN** the 成片 is accepted for staging

#### Scenario: Off by more than a frame
- **WHEN** the same 成片 is two frames shorter
- **THEN** it is refused with creative_video_duration_mismatch

#### Scenario: 小样 unchanged
- **WHEN** a 小样 of the same work is delivered at 221483 ms
- **THEN** it is refused, because a 小样 carries no clips

