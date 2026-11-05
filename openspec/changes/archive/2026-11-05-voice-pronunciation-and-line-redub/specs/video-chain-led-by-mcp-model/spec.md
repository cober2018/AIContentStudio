## ADDED Requirements

### Requirement: Pronunciation in the 导演稿 voice

The video.master.v2 `voice` SHALL accept an optional `pronunciation` list of at most 50 entries, each at most 40 characters in the form `原文/(pinyin+tone)…` with one bracket per character, e.g. `去重/(qu4)(chong2)`; anything else SHALL be rejected with `video_voice_pronunciation_invalid`. Every MiniMax speech request made for the work (whole voiceover, role voices, dub_persona shots, single-line redub) SHALL send it as `pronunciation_dict: {"tone": [...]}`, a cached voiceover SHALL be reused only when its pronunciation matches, saving a generated voiceover SHALL keep the list, and `get_video_brief` SHALL describe the field.

#### Scenario: Polyphonic word
- **WHEN** the 导演稿 voice has `pronunciation: ["去重/(qu4)(chong2)"]` and the line stays 「对齐、去重」
- **THEN** the voiceover request carries `pronunciation_dict: {"tone": ["去重/(qu4)(chong2)"]}`

#### Scenario: Bad entry
- **WHEN** a draft has `pronunciation: ["去重/(qu4)"]`
- **THEN** saving is refused with `video_voice_pronunciation_invalid`

### Requirement: Redub chosen lines in place

`generate_video_voiceover` SHALL accept optional `lines` (script block ids). With `lines`, it SHALL voice only those lines and splice each into the current whole TTS voiceover at the original line's start, keeping every other line's audio and the total length; seams SHALL fall in pauses with a one-frame fade. Line spans SHALL come from the voice's sentence timing, else from silence detection (-40 dB, 0.15 s) grouped by the script and checked, failing with `voiceover_line_split_unclear` rather than guessing. A longer new line MAY use the following pause down to a 0.25 s gap; beyond that the call SHALL fail with `voiceover_line_too_long` stating the missing seconds, never changing speed. The result SHALL be a new voice material in the project's 音频 folder; the 导演稿 SHALL get the new voice id and new cue times for those lines only, with shot lengths and other cues unchanged, and only those lines SHALL be billed. Works voiced per shot (dub_persona) or with a dialogue track SHALL be refused. Without `lines`, behaviour SHALL stay as before.

#### Scenario: One line redubbed
- **WHEN** line-34 is redubbed in a 3-minute voiceover
- **THEN** every other line's audio matches the original except one frame either side of each seam, line-34 starts where it did, the total length is unchanged and one line is billed

#### Scenario: Does not fit
- **WHEN** the new line is 0.4 s longer than its line plus the usable pause
- **THEN** the call fails with `voiceover_line_too_long` saying 0.4 秒, and nothing is saved
