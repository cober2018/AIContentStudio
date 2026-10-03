## Why

FE-F6A made Video a first-class modality but only shipped a JSON shell over `video.master.v1`. North Star requires video as a real Production Engine with script, storyboard/shot planning, source assets, voice, subtitles, overlays, timeline, cover and final render lineage. F6D completes that product surface without turning the Studio into a full professional NLE.

## What Changes

- Add `video.master.v2` as the default professional Video schema.
- Keep `video.master.v1` and historical Candidates compatible.
- Define stable script/shot/timeline/voice/subtitle/overlay/cover structures.
- Bind every source/final media element to exact MaterialRevision refs.
- Support shot reorder, duration, asset placement, subtitle/voice association and overlays.
- Add local preview timeline and bounded editing rather than arbitrary NLE effects.
- Add TTS/ASR/video-generation capability hooks; accepted outputs become MaterialRevision before use.
- Add long→short and aspect-ratio transformation as explicit derived revisions, never in-place mutation.
- Preserve exact final render attestation/verification and Candidate hash behavior.
- Add video-specific checks, structured diff and professional frontend.
- Target no new business table/migration; store durable video content in ContentMasterRevision v2 and exact refs.

## Non-goals

- Full Premiere/DaVinci-style NLE.
- Unbounded effects/plugin ecosystem.
- False claims of AI-generated or rendered video when provider capability is unavailable.
- Publisher-side last-minute transcoding that changes approved content.
