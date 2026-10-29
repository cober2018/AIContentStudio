# Finishing rules (sound, captions, Resolve assembly)

## Sound

- Master narration on the platform before editing: `POST /api/v1/materials/{material_id}/revisions/{revision_id}/loudness-master` (defaults −16 LUFS, −1.5 dBTP). Use the mastered revision in the Master's voice slot; the original stays for ASR alignment.
- Mix target: about −14 LUFS integrated, true peak at or below −1 dBTP. A mono narration on a stereo bus reads about 3 dB louder; set its clip volume around −1 dB and measure.
- Music under narration: about −15 dB (linear 0.18) with 1 s fade in and 1.5 s fade out. No music is also valid.
- Resolve scripting can enable the Dialogue Leveler but not a limiter. Do not raise gain past the peak ceiling to chase loudness; master the narration instead.
- The platform measures loudness and true peak on rough/final submit and shows warnings at review; fix the cause rather than resubmitting the same mix.

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

