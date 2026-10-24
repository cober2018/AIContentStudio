## Decisions

- **Reuse, don't duplicate.** MCP tools call the same service functions as the REST stage routes (`preview`, `run`, `result`, `history`/`feedback_targets`) and material matching (`start`, `read`). Authority, hashes and idempotency rules are unchanged. The MCP owner binding (`AICS_CREATIVE_MCP_OWNER_USER_ID`, loopback, bearer) stays the only identity.
- **Decision is derived, not a new table.** `get_stage_decision(project_id, unit_id, node_id, run_id, attempt_id)` reads:
  - the attempt status;
  - its accepted target (`accepted_master` / accepted result);
  - its latest feedback event (decision and note);
  - the run's continuation node.

  The state is `waiting_for_you` when the attempt is `waiting_input` with no decision.
- **Bounded wait.** `wait_seconds` (0–25) re-reads the decision once a second inside the request, then returns the current state. The MCP transport is single-request JSON with no SSE, so the model polls again if still waiting.
- **Review URL.** For a stage it is `/projects/{project_id}/units/{unit_id}/production?stage={node_id}`; for a match run it is `/materials?tab=match&run={id}`. The web opens the matching stage or run from the query.
- **Candidate image preview.**
  - Route: `POST …/creation-recipe/stages/{node}/candidate-previews` with `{run_id, attempt_id, candidate_id, canvas_id}`. It returns a PNG.
  - Only `graphic.master.v2` candidates of the exact current attempt are accepted.
  - The renderer is `LocalGraphicRenderer.render_master` with `render_input_hash = digest(payload_hash, canvas_id)`.
  - Results are cached under the derivative root by that hash plus the runtime fingerprint.
  - Nothing is written to materials or attestations.
  - If the runtime is not configured, the response is `422 graphic_preview_unavailable` and the UI keeps the text view.
- **Footage rejection.** `POST /material-match-runs/{id}/segments/{segment_id}/reject {note}` stores `{rejected_at, note}` on the segment in `result_json`. A later pick clears it.
- **No accept over MCP.** No MCP tool calls an adoption, feedback, bind or delivery function. A test asserts the tool list contains no such action.
