## 1. MCP tools

- [x] 1.1 Add `preview_stage`, `run_stage`, `get_stage_result` to `creative_mcp` using existing stage services; add `review_url`
- [x] 1.2 Add `get_stage_decision` (derived from attempt, acceptance, feedback events, continuation) with bounded wait
- [x] 1.3 Add `start_material_match`, `get_material_match` (picks, rejections, review URL)
- [x] 1.4 Assert no MCP tool maps to adoption, feedback, bind, approval or delivery

## 2. Images before deciding

- [x] 2.1 Candidate preview route (graphic.master.v2, exact current attempt, cached, preview-only)
- [x] 2.2 `StageProposalReview`: card thumbnails per option, larger view on click, fallback when unavailable
- [x] 2.3 Web opens the stage / match run from `review_url` query

## 3. Footage decision

- [x] 3.1 Segment reject endpoint storing note in `result_json`; a pick clears it
- [x] 3.2 `SegmentResult`: "都不合适" with note

## 4. Verify and hand over

- [x] 4.1 Tests for new tools, preview route and segment reject; existing MCP, stage and material tests pass; web build passes
- [x] 4.2 Update production skill instructions to use the MCP loop and wait for decisions
- [ ] 4.3 Resume the 海底光缆 sample through the loop: agent runs cards via MCP → user decides on the platform → agent reads the signal
- [x] 4.4 README, progress, findings
