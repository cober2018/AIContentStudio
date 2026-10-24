## Decisions

- **Own implementation, borrowed method.**
  - Borrowed from ScriptMate's public description: segment the script before searching; keep subject, country and comparison constraints; search own material first; score candidates against the real picture; no automatic fallback; links before downloads.
  - No ScriptMate code, prompts or data files are copied; the project has no license.
- **Candidates are not materials.** Match results are private search candidates, as with today's Wikimedia search. Only an explicit accept downloads the file and creates a Material revision, using the existing staging path, so rights, revisions and project references stay single-sourced.
- **Plans are saved.** A `material_match_run` row keeps the run, so it can be reopened, resumed after a restart and audited. Each row holds:
  - owner and optional project;
  - the source text, or a reference to the script or Master revision with its content hash;
  - the settings, status and progress;
  - the result JSON (segments, candidates, scores, gaps);
  - the model and provider versions used.
  Re-running creates a new row.
- **Licenses decide visibility.**
  - Each provider maps its own license to a code: `cc0`, `pdm`, `cc-by`, `pexels`, `pixabay`, `nasa-media`, `coverr`.
  - Only codes on the allowlist are shown; `cc-by-sa` can be enabled per run.
  - The attribution text and license URL are carried into the accepted Material's `attribution_text` and rights.
  - Footage marked local-review-only stays `restricted`.
- **Visual check is evidence, not trust.**
  - The judge model receives the segment, its constraints and the thumbnail bytes the platform fetched through the outbound policy.
  - It returns a score, its reasons and what it saw.
  - Pre-filter scores never add to the visual score.
  - A thumbnail that cannot be read is recorded and leaves that candidate for human review; it does not stop the run.
- **Bounds**: at most 40 segments, a search pool of up to 20 per provider per query, at most 5 candidates kept per segment and at most 12 sent to the visual judge per segment. Every run has a cost estimate shown before it starts.
- **Own library matching** is text-based over material metadata and the drive-link index; no new embedding store.
