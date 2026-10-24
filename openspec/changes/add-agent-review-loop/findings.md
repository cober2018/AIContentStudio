# Findings

- Existing: stage proposals stop at waiting_input; web accept/accept-with-edits; stage feedback (rejected/rerun_requested/commented) as ProjectEvents; history; auto-continuation after accept.
- Missing: MCP has only creative-execution tools (no stage tools, no decision read); graphic images only after Master acceptance; footage has pick but no reject-with-note.
- MCP acts as one owner user (loopback + bearer); keeping accept/feedback tools out of MCP is what makes the decision the user's.
- 2026-10-22 decision (user): build the loop as platform capability; first cards and footage.
- Stage routes use `StagePreviewRoute`, which requires a JSON body, so GET routes must live on the plain router (first attempt returned `stage_input_invalid`).
- `digest()` rejects tuples; cache keys must use lists.
- MCP masked all domain codes as `creative_domain_*`; stage/material/graphic codes are fixed identifiers and now pass through so the agent can recover.
- The review link alone left the options collapsed behind 「查看本次结果」; `&open=result` opens them directly.
