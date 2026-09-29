## ADDED Requirements

### Requirement: Video v2 has one structured editable truth
New professional Video content SHALL use canonical `video.master.v2` with stable IDs and bounded script blocks, shots, timeline tracks/items, voice, subtitle cues, overlays, music and cover. Saving SHALL append a ContentMasterRevision, not overwrite history. Unsupported fields, unbounded values, non-finite placement or infrastructure paths MUST fail closed.

#### Scenario: Save and reload a bounded Video document
- **WHEN** a user edits script, shots and timeline and explicitly saves a current v2 Master
- **THEN** reload returns the same canonical IDs, order, content and payload hash in a new immutable revision

#### Scenario: Invalid document does not create history
- **WHEN** a save contains an unknown timeline field, non-finite placement or forbidden path
- **THEN** the server rejects it and creates no new Master or reference rows

### Requirement: Historical Video requires an explicit v2 fork
Existing `video.master.v1` and historical Candidates SHALL remain readable and hash-stable. Professional editing from a current v1 Master MUST use a dedicated preview and append-only v2 fork with source payload/context CAS, idempotency and conversion warnings; generic save MUST NOT change schema.

Because v1 did not validate aspect ratio, timeline timing or media placement, preview MUST NOT synthesize a ready v2 document. The first v2 child MUST use a complete user-submitted canonical payload and exact refs with explicit warning acknowledgment, preserve stored script text and shot IDs/order, and omit inherited final-render declaration/attestation. Later content edits require a separate revision.

#### Scenario: Fork legacy Video safely
- **WHEN** a current v1 Master is previewed and explicitly upgraded with matching expected hashes
- **THEN** a v2 child is appended, the v1 Master and its Candidates remain unchanged, and unprovable fields are warned or rejected rather than fabricated

#### Scenario: Implicit schema crossing
- **WHEN** a client submits a v2 payload through ordinary save against a v1 head
- **THEN** the server returns a conflict and leaves history unchanged

### Requirement: Every media use is an exact project-visible revision
Every source visual, audio, music, cover and final render use SHALL bind an exact project-visible MaterialRevision, content hash, role, slot key, canonical sort order and placement. Allowed roles are `shot_source`, `timeline_media`, `voice_audio`, `music_audio`, `cover_image` and `render_output`; slots SHALL use the stable declaration ID, except the sole final output uses `final`. Repeated use of one revision MUST preserve distinct placements. Duplicate role/slot, missing or orphan declarations and multiple final outputs MUST fail atomically. Role/slot/order/placement and revision hash SHALL bind to the Master; source refs participate in render-input hashing, while the final output is excluded from that input hash to avoid a cycle and is separately attested and frozen. The system MUST validate media kind, live bytes/hash, rights and revocation at each applicable save and downstream gate; it MUST NOT copy source bytes into a parallel Video resource.

#### Scenario: Reuse source media in two shots
- **WHEN** the same eligible MaterialRevision appears in two different shot placements
- **THEN** both exact placement refs are saved without duplicating bytes or conflating the shot identities

#### Scenario: Revoked source media
- **WHEN** a referenced revision is revoked or its bytes/hash no longer match
- **THEN** the next protected save, freeze or delivery action is blocked rather than trusting an earlier preview

### Requirement: Video timeline is bounded content assembly
The Studio SHALL support ordered shots, bounded duration/start/end/trim, source framing, voice/audio, subtitle cue editing/import, overlays, music and exact cover selection without an unrestricted NLE/effects graph. Imported cues MUST pass the same bounded timing/text validation before an explicit Master save. A local preview MUST NOT be described as a verified final render.

Recorded/TTS voice and music declarations identify exact whole-composition audio sources; they do not imply a verified Provider execution. Each placed `audio` or `music` timeline item MUST declare an exact source MaterialRevision, and its timing/trim/volume MUST pass the same bounded validation before save. Subtitle cues MUST remain in canonical order without overlap. An empty audio/music track is a valid editable draft; an unbound placed item is not.

#### Scenario: Invalid timing
- **WHEN** a shot, track item or subtitle cue exceeds the document duration or violates its ordering/bounds
- **THEN** the server rejects the revision with a field-level reason and no partial media reference writes

#### Scenario: Local preview
- **WHEN** a user previews the current unsaved timeline
- **THEN** the UI identifies it as a local assembly preview and does not mark Candidate render readiness

#### Scenario: Import subtitle cues
- **WHEN** a user imports cues with overlapping or out-of-range times
- **THEN** the invalid cues are rejected and no durable Master revision is created implicitly

### Requirement: Voice, subtitles and overlays are frozen Candidate content
Selected recorded/TTS voice refs, subtitle text and cues, overlay text and cover SHALL be versioned in the Master and frozen in Candidate v4. Provider-produced text or media MUST NOT become durable content without explicit acceptance and Master save.

#### Scenario: Edited subtitle after freeze
- **WHEN** subtitle text changes after a Candidate was frozen
- **THEN** the old Candidate continues to show its frozen cues and a new Master/check/render/Candidate path is required for the change

### Requirement: Derived Video operations create traceable child revisions
Long-to-short, aspect-ratio conversion and shot-regeneration SHALL produce explicit append-only child Masters bound to exact source revision/hash/context and transformation intent, with optimistic concurrency and idempotency. Only a dedicated server operation may persist `source_kind=derived_video` and server-generated `edit_summary_json.derived_video` containing source ID/hash/context, operation kind, bounded parameters and result hash; ordinary save MUST reject client-forged derivation provenance. A derived child MUST contain a concrete validated v2 payload supplied by an explicit user edit or a deterministic local transformation; intent alone MUST NOT be persisted as a successful derivation. If the requested result requires an unverified Provider, the operation MUST return typed unavailable without creating a child Master or media. They MUST NOT silently mutate the source revision or accept a stale head.

#### Scenario: Derive a short version
- **WHEN** the user explicitly accepts a long-to-short transformation against a current source Master
- **THEN** a child revision records the source and transformation while the source payload and historical Candidate hashes remain unchanged

#### Scenario: Stale derivation
- **WHEN** source payload/context or current head differs from the expected values
- **THEN** derivation returns conflict and creates no child revision

#### Scenario: Unavailable generated transformation
- **WHEN** a requested shot-regeneration or conversion needs a Provider that is not verified and no concrete user-edited or deterministic local v2 result exists
- **THEN** the operation reports unavailable and creates no child Master, generated media or successful transformation receipt

### Requirement: Unverified Video providers are unavailable
Video generation, TTS and ASR hooks SHALL expose truthful configured/executable/verified state. F6D MUST reject unverified provider-shaped calls without creating media, rights, transcripts or Master revisions. F7 owns real execution and accepted-result MaterialRevision bytes/hash/license/provenance plus provider execution/result/error secret redaction and negative tests.

#### Scenario: Disconnected TTS request
- **WHEN** a client invokes TTS while the scoped capability is unverified
- **THEN** it receives a typed unavailable result and no MaterialRevision, content change or public-use grant is created

### Requirement: Final Video render is exact and input-bound
Candidate-ready Video SHALL have one exact final video MaterialRevision with live bytes/hash/rights and an attestation for the current payload, context, source-asset set and applicable profile. An explicit manual attestation SHALL remain labeled manual; it MUST NOT be represented as verified renderer output.

#### Scenario: Stale final MP4
- **WHEN** a shot, subtitle, asset ref, context or profile changes after final-render attestation
- **THEN** freeze is unavailable until an exact current video output is bound and attested again

#### Scenario: Forged renderer provenance
- **WHEN** a client claims an unverified renderer produced the final output
- **THEN** the server rejects that provenance and creates no new Master or Candidate

### Requirement: Video checks and differences are modality-aware
Video v2 SHALL run schema-dispatched structure, timeline, identity and exact published video-profile checks through ContentMasterCheckRun. The exact published channel + content-form profile MAY specify bounded `video_requirements`: positive `max_duration_ms` and `max_shots`, bounded reduced positive integer `[width,height]` `allowed_aspect_ratios` pairs, and boolean `subtitle_required`/`cover_required`. Missing keys impose no invented rule; unknown/malformed keys or absent exact published profile are unavailable/invalid, never PASS. Profile version/rules participate in check and render-input freshness. Missing semantic capability SHALL be reported as unavailable/partial, not PASS. Master and Review diffs SHALL compare stable script/shot/timeline/voice/subtitle/overlay/render identities without fabricated whole-video text similarity.

#### Scenario: Change one shot and one cue
- **WHEN** a newer v2 revision changes a shot duration and a subtitle cue
- **THEN** diff names both changes by stable ID, marks dependent checks/render stale and does not calculate whole-video text similarity

### Requirement: Video Studio and local package preserve frozen content
The Video-only Studio SHALL support typed bounded editing, exact asset selection, history/diff/check/readiness and explicit save, while Workflow editing remains independent and archived/history views are read-only. Candidate v4, Review, Approval and local package SHALL use the frozen v2 render and exact approved final video bytes/declared companions; v2 MUST NOT fall back to Draft/v1 packaging or remote publishing.

#### Scenario: Local Video handoff
- **WHEN** a current v2 Master with current checks and exact final render is frozen, reviewed, approved and authorized for a local package
- **THEN** the package contains the approved MP4 bytes/hash, manifest and declared companions without changing Master or publishing remotely

#### Scenario: Archived Video unit
- **WHEN** a Video unit is archived
- **THEN** the Studio exposes its history as read-only and blocks save, checks, rerun and freeze actions
