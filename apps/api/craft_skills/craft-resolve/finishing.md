# Finishing rules (sound, captions, Resolve assembly)

## Sound

- Master narration on the platform before editing: `POST /api/v1/materials/{material_id}/revisions/{revision_id}/loudness-master` (defaults −16 LUFS, −1.5 dBTP). Use the mastered revision in the Master's voice slot; the original stays for ASR alignment.
- Mix target: about −14 LUFS integrated, true peak at or below −1 dBTP. A mono narration on a stereo bus reads about 3 dB louder; set its clip volume around −1 dB and measure.
- Music under narration: about −15 dB (linear 0.18) with 1 s fade in and 1.5 s fade out. No music is also valid.
- Resolve scripting can enable the Dialogue Leveler but not a limiter. Do not raise gain past the peak ceiling to chase loudness; master the narration instead.
- The platform measures loudness and true peak on rough/final submit and shows warnings at review; fix the cause rather than resubmitting the same mix.

## Footage unification before the 小样 (required)

- HLG restore first: check each live clip's `color_transfer` with ffprobe; `arib-std-b67` (iPhone HLG) clips get `MCP/iphone-hlg-apple-sdr.cube` via `SetLUT(1, …)` in a `davinciYRGB` (non-colour-managed) project. Never on SDR footage, generated images or AE overlays. See `techniques/color.md` «iPhone HLG 还原».
- AE data level: every RGB file exported from AE (qtrle / ProRes 4444 / PNG), with or without alpha (overlays, captions, full-screen end cards, cover cards), gets `MediaPoolItem.SetClipProperty("Data Level", "Full")` before it goes on the timeline; confirm with `GetClipProperty("Data Level")`. Left on Auto it is read as video levels: a transparent overlay's black becomes −16/219 and darkens the whole picture under it by about 19/255, and an opaque card gets its contrast stretched with blacks and whites clipped. Ordinary SDR live clips get no compensation LUT. AI images: render once, compare a frame with the source image, compensate only if darker. See `techniques/color.md` «AE 叠层数据电平设 Full».
- LUT install: if `MCP/iphone-hlg-apple-sdr.cube` is missing from Resolve's LUT list, copy it from the repo's `craft_skills/craft-resolve/luts/` into Resolve's LUT folder under `MCP/` (macOS: `/Library/Application Support/Blackmagic Design/DaVinci Resolve/LUT/MCP/`) and refresh the LUT list. Delete `MCP/iphone-hlg-apple-sdr-render.cube` and `MCP/sdr-render-comp.cube` if present: they compensated the overlay darkening and make the cut about 20 levels too bright once overlays are Full.
- Then correct exposure / white balance and match shots of one scene to a reference shot (colour groups). No stylised grading; leave footage alone when it is already normal and consistent. See `techniques/color.md` «统一全片色调».
- Level each live dialogue segment to about −16 LUFS, denoise lightly only for obvious noise, fix one-sided mono; then mix to the Sound targets above. See `techniques/sound.md` «对白逐段拉齐».
- Verify brightness on the rendered file against the phone's own display frame (AVAssetImageGenerator), not on Resolve stills.
- The platform samples one frame per 导演稿 shot and measures speech per shot on rough/final submit, and warns at review about over-exposed shots, brightness jumps between adjacent shots and uneven dialogue; fix the cause rather than resubmitting.

## Delivery receipt

Every 小样 / 成片 receipt lists per shot: which clips got the HLG restore, which got colour correction and what changed, and which dialogue segments had their level changed (by how much) or were denoised. Shots left as shot say so.

## Captions

- Text comes from the accepted spoken script; times come from ASR-aligned cues. Break only at punctuation; split a long clause at a natural phrase boundary, never inside a word, number or name.
- Burn captions in AE when Resolve's burn-in style cannot be set; keep the Resolve subtitle track and deliver the SRT separately, with `ExportSubtitle` off at render.

## Resolve assembly

- Set the timeline resolution and frame rate before creating the timeline.
- Append the subtitle file first on an empty timeline (Resolve ignores the record frame for subtitles), then video clips by exact frame counts, then audio.
- Apply render settings one key at a time; one invalid key (for example a non-integer `VideoQuality`) silently drops the whole batch and leaves the previous settings in force.
- If the AAC tail runs past the target duration tolerance, keep the native render in `work/` and bound the delivery with a stream copy (`-c copy -t <target>`); never re-encode to fix length.
- Export the project, reimport it under a new name, read back the timeline and file paths, and confirm zero missing media before submitting.

## Pre-delivery check

Before submitting rough or final, watch the render (not the timeline):
- Every cut point: a few frames either side; no flash frame, no stray frame of the neighbouring clip, no jump in subject position unless intended.
- No black frames, no silent gaps, no clipped words at clip heads or tails, no cut-off ending.
- Loudness and true peak as in Sound above.
- Captions on screen match the spoken words and stay inside the safe area.
- Fix the cause and re-render; do not resubmit the same file.

