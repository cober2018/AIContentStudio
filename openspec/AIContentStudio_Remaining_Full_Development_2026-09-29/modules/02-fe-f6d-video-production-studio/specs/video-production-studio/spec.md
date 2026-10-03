## ADDED Requirements

### Requirement: Video v2 is structured and revisioned
The system SHALL support `video.master.v2` with stable script, shot, timeline, voice, subtitle and overlay identities. Professional editing SHALL create new ContentMasterRevision rows and never overwrite history.

### Requirement: Video source assets are exact project-visible MaterialRevisions
Every visual/audio/cover/final render reference SHALL be exact, project-visible, hash-checked and rights-checked.

### Requirement: Video timeline is a bounded production timeline
The Studio SHALL support shot ordering, timing, source placement, voice/audio, subtitles, overlays and music without requiring an unrestricted NLE/effects graph.

### Requirement: Voice/subtitle content is Candidate content
TTS/recorded voice selection, subtitle text/cues and overlay text SHALL be versioned and frozen in Candidate provenance.

### Requirement: Video derived transforms create child revisions
Long→short, aspect-ratio conversion and shot regeneration SHALL create explicit child revisions with source provenance.

### Requirement: Final video render is input-bound
Candidate freeze requires exact final video bytes bound to the complete render-input hash. Missing/unverified render remains unavailable.

### Requirement: Provider outputs become MaterialRevision before use
Video/TTS/ASR provider outputs MUST be persisted with provider/version/hash/rights metadata before Master reference.

### Requirement: Video Review is structured
Review SHALL expose script/shot/timeline/render changes without fake whole-video text similarity.

### Requirement: Historical video remains compatible
`video.master.v1` and existing Candidates remain readable/hash-stable; professional editing from v1 requires explicit append-only v2 fork.
