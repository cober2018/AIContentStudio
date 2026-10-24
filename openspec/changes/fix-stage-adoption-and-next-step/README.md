# fix-stage-adoption-and-next-step

**Stage:** applied locally and checked in the browser on U80. Not committed or archived.

**What:** (1) A result waiting for a decision stays acceptable when only project materials or the API process changed. Real input changes still require regenerating, and the error names what changed. (2) The production page's left navigation shows the workflow stages under 内容方案, with the one needing the user highlighted. (3) Stage accept errors are shown in plain words. (4) A stage stuck on an unknown model call can be given up by the user and generated again; provider errors the provider clearly answered are recorded as failed with their reason.

**Trigger:** U80 (project 41) shot plan, attempt 328, refused with `409 stage_adoption_context_changed` after the user filled all 15 shot slots.

**Code (uncommitted, `main` working tree):**
- API: `app/services/creation_recipes.py` (`context_basis`, `adoption_basis`, `changed_inputs`), `creative_method_stage.py`, `stage_master_adoptions.py`, `stage_domain_adoptions.py`, `stage_invocations.py` (`detail` and `body`), the routers' stage error bodies, and `creative_mcp.py`.
- Web: `StageSubSteps.tsx`, `stageErrors.ts`, `CreationRecipePanel.tsx` (summary `next`, `open=result` on later links), `ProductionWorkspace.tsx`, `ProductionContextHeader.tsx` (shots panel opens from a link), `StageCreativeResultPanel.tsx`, `StageProposalReview.tsx`, `StageDomainResultPanel.tsx`.

**Next:** the user accepts the U80 shot plan on the platform; archive on request.
