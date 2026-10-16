# Native AE and Resolve execution

These are technical adapter notes. Creative choices come from the frozen enabled methods and current task, not this file.

## AE lifecycle

Read the live AE execution guide before selecting an execution route, bind the exact project and preserve unrelated projects. Search the existing tool library before repeating a composite operation. Use stable composition/layer identifiers and verify edited properties from AE; a successful dispatch is not visual approval.

Separate edits and render execution. With the local MCP host wrapping operations in an undo group, invoking synchronous render inside that group produced an undo-group-mismatch warning after media was written. Finish the edit/queue operation, then schedule rendering after the wrapper returns. Read the original queue item status and inspect the output before retrying an uncertain request. Saving/opening a project is a lifecycle operation and must not be nested in an editing undo group. Do not work around an error by dropping checkpoint protection from the actual edits.

For screen emphasis, derive the focus rectangle from the actual source frame and inspect it at output resolution. Relationship diagrams retain independently editable objects and connectors. Title/number reveals retain text layers and readable hold time. Respect each requested composition's duration, frame rate, resolution and alpha contract; no universal styling or duration is prescribed here.

## Resolve timing and audio

Use exact media IDs/paths, explicit tracks, source ranges and record frames. Read timeline start and frame rate; do not assume zero. On the verified Resolve build, source start 24/end 72 produced 48 frames, while end 71 produced 47. Verify the returned item's start/end/duration instead of copying an upstream inclusive-end calculation.

Keep the narration timing provenance: provider timestamps, aligned ASR, or estimated. ASR word intervals are estimates, not proof of the spoken words. Maintain one edit-decision mapping from source intervals to output intervals; derive picture, subtitles and any sound effects from that mapping after dialogue edits. Preserve natural pauses according to the selected method, not a fixed silence threshold.

Mute generated source sound unless explicitly retained. Set and read back intended audio volume and fades; `SetProperties`/`GetProperties` and `SetFades`/`GetFades` were verified on native timeline items. This does not prove that ducking, EQ or intelligibility succeeded. Inspect the rendered audio and preserve whether it was directly auditioned. For ducking, verify the actual automation/level changes using an available supported route, or report the uncompleted operation; do not label a constant gain as ducking.

## Interchange and recovery

AE intermediates return to the Resolve main timeline for final mixing/export. Save source dependencies and export/reopen the native projects. Check file-backed media for missing paths; timeline objects may legitimately have an empty FilePath. Verify actual render duration, dimensions, frame rate, audio presence, required alpha and content hashes. A technical silent three-shot probe is not a finished narrated work.

Music references pin a MaterialRevision and preserve attribution/license and source metadata. Tag revisions affect future selection, not existing edit references. No-music is a valid choice; never fill missing licensing, vocal, tempo or looping data by guessing.

## Product combinations verified on 2026-10-16

AE 26.5x89 and Resolve 21.1.0.14 rendered and reopened a three-scene, 1080×1920/30fps single-photo product test. Independent photo windows preserved source aspect, editable headlines and estimated subtitles. The separate offer probe used a visibly fictional 1000→800 TWD example, never the sample product price. Use the actual source/task values and supported easing, not these probe values as a preset. A decorative grid has no measurement meaning.

Read available AE output templates from the active installation; the verified H.264 template was localized. Save the current project before opening another to avoid an unsaved-project modal. A timed-out open was reconciled from an actual read of the target file and compositions; do not replay it blindly. Protected edits require an absolute work_dir and a current project binding. Native render was scheduled after the edit wrapper returned.

Resolve's main timeline had exact 150/150/180-frame picture spans, independent narration and music tracks, and read-back segmented music levels/fades. It was exported, its DRP imported under a separate reopen project name, and file-backed dependencies checked with missing_media=0. AE's three source comps reopened with exact 150/150/180 frames and missing_media=0. The rendered 480-frame video retained original pixels; no alpha was requested, so this sample is not a new alpha-path acceptance. Existing alpha verification remains separate.

The final H.264/AAC delivery container was bounded with stream copy; retain the native render and verify actual decoded duration. Full narration ASR matched, fine subtitle divisions were estimated, and direct listening was not performed. These are evidence boundaries, not inferred hearing approval.
