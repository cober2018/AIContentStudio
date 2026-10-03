# FE-F6D Video Production Studio Design

## 1. Schema

Default professional schema: `video.master.v2`.

Top-level:

```json
{
  "title":"...",
  "script":{"blocks":[]},
  "shots":[],
  "timeline":{"tracks":[],"duration_ms":0},
  "voice":{"mode":"none|recorded|tts","material_revision_id":null},
  "subtitles":{"cues":[]},
  "overlays":[],
  "music":{"material_revision_id":null},
  "cover":{"material_revision_id":null},
  "render_asset_ref": null,
  "variant_of": null
}
```

Stable IDs are required for script blocks, shots, cues, overlays and timeline items.

## 2. Shots

Each shot contains:
- id/order
- label/purpose
- script/voice text reference
- duration
- source visual MaterialRevision refs
- optional generated asset provenance
- crop/fit/framing metadata
- transition token from a bounded supported set

Changing shot content/asset/order makes dependent render stale.

## 3. Timeline

F6D timeline is bounded content assembly:
- video track(s)
- audio/voice track
- subtitle track
- overlay track
- music track

It supports order, start/end, trim, volume and visibility where applicable.
No arbitrary effect graph is required.

## 4. Voice/subtitles

Voice may be:
- none
- recorded/uploaded exact audio
- TTS exact audio output from a configured capability

Subtitles are durable text/cues in Master payload. ASR/provider output is only accepted after validation and explicit save. Subtitle text is Candidate content.

## 5. Source assets

Every video/image/audio/cover asset is an exact project-visible MaterialRevision with exact hash/rights. Provider outputs become MaterialRevision before reference.

## 6. Derived operations

Long→short, ratio conversion or shot regeneration creates a new child Master revision with explicit provenance. It never mutates the source revision.

## 7. Rendering

Candidate-ready Video requires exact final video bytes bound to canonical render-input hash.

Accepted paths:
- verified renderer capability; or
- explicit Studio/manual attestation under existing Production Core rules.

Publisher may not transcode/rewrite content after Approval except transport-only transformations proven byte/content preserving; otherwise a new Candidate is required.

## 8. Checks

Video v2:
- master_schema
- evidence
- rights
- video_structure
- video_timeline
- video_identity
- video_platform
- render

Conditional provider/profile checks may be added only when exact profiles/capabilities exist.

## 9. Frontend

Recommended:
- `product/video/VideoStudio.tsx`
- `VideoScriptPanel.tsx`
- `VideoShotList.tsx`
- `VideoShotEditor.tsx`
- `VideoTimeline.tsx`
- `VideoAssetPanel.tsx`
- `VideoVoicePanel.tsx`
- `VideoSubtitlePanel.tsx`
- `VideoOverlayPanel.tsx`
- `VideoPreview.tsx`
- `VideoChecksPanel.tsx`
- `VideoRevisionDiff.tsx`

## 10. Backend

Recommended:
- `services/video_documents.py`
- `services/video_master_checks.py`
- `services/video_master_diff.py`
- optional `services/video_master_ai.py`
- optional `routers/video_production.py`

Provider adapters remain replaceable; real verification belongs to F7.

## 11. Acceptance

`Video unit
→ script
→ shots
→ source assets
→ voice/subtitles/overlays
→ timeline
→ save v2
→ checks
→ exact final render
→ Candidate
→ Review
→ Approval
→ local package`

The package must contain the exact approved final video plus declared companion assets/manifest.
