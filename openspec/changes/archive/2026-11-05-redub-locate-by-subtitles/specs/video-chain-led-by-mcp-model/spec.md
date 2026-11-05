## MODIFIED Requirements

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
