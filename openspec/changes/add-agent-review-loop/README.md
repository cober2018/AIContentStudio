# add-agent-review-loop

**Stage:** applied locally; final acceptance (task 4.3) waits for the user to decide on the platform. Not committed, archived or published.

**Background:** the user drives production with a large model through MCP and decides on the platform. See `proposal.md`.

## Where the code is (uncommitted, working tree on `main`)

| Part | Files |
|---|---|
| MCP tools | `apps/api/app/services/agent_review.py` (new)<br>`apps/api/app/services/creative_mcp.py`: 8 tools, plus stage/material error codes passed through<br>`apps/api/app/routers/creative_mcp.py`: loop described in `initialize` instructions |
| Card previews | `apps/api/app/services/stage_candidate_previews.py` (new)<br>`GET …/creation-recipe/stages/{node}/candidate-previews` in `routers/content_projects.py`<br>`apps/web/src/product/StageCandidateCards.tsx` (new)<br>`StageProposalReview.tsx` |
| Review link | `CreationRecipePanel.tsx` honours `?stage=…&open=result`; the material library already honours `?tab=match&run=…` |
| Footage rejection | `material_matching.reject`<br>`POST /material-match-runs/{id}/segments/{sid}/reject`<br>`MaterialMatchView.tsx` (`RejectSegment`)<br>wired into `MaterialScriptMatch` and `ShotMaterialFinder` |
| Skill | `.codex/skills/video-material-scout/SKILL.md`, step 2 uses MCP and waits for the user |
| Tests | `tests/test_aco_creative_mcp.py`: whitelist updated, accept/reject/bind names added as forbidden |

## Key decisions

- **The decision is derived, not stored anew.** It comes from the attempt status, the acceptance and the feedback events.
- **No push channel.** The model polls with `wait_seconds` ≤ 25.
- **Card previews are preview-only.** They are cached under `MEDIA_ROOT/.derivatives/stage-candidates` and never become material or a render attestation.
- **MCP never accepts, rejects or binds.** This is enforced by the tool whitelist test.

## Status

| Done | Next |
|---|---|
| 1.x, 2.x, 3.x, 4.2 | 4.3: the user decides on the platform<br>4.4: archive, on request |

Verification results are in `progress.md`.

## How to run

The API is restarted with `launchctl kickstart -k gui/$(id -u)/com.aicontent.api`, only when no attempts or match runs are running. Web: `npm run build` in `apps/web`.
