[C2C]
STATE: PLAN
WORKSPACE: AIContentStudio
TASK_ID: creation-recipe-stage-control-loop
BASE_OBSERVED: main@341ead8 + implemented uncommitted align-creative-orchestration-product
BUSINESS_APPLY: BLOCKED_PENDING_SPEC_REVIEW

GOAL:
Materialize the OpenSpec change `creation-recipe-stage-control-loop`. This turns existing Workflow Definition into the product-facing Creation Recipe: typed stage controls, effective prompt/method/model preview, exact attempt receipts, explicit stage output adoption, feedback, and human-controlled promotion of what worked to Project/default Workflow or Capability Memory.

CRITICAL PRODUCT PRINCIPLE:
Do not create a second Recipe/workflow truth. Workflow Definition remains process truth. Capability Memory stores reusable stage methods only. ProjectEvent stores feedback evidence only. Master/Variant/Material/CreativeExecution remain their existing authoritative result domains.

BASELINE PRECONDITION:
Before new business apply, close the prior align implementation lifecycle blockers:
1. align current local approved schema/readiness/runbooks to already-enabled `aco000000001`, while documenting `f8a` identity columns as inert ancestry and NOT claiming JWT/auth activation;
2. add persistent repository tests for CreativeExecution/MCP/CapabilityMemory/ACO.
Do NOT rollback the live DB.

FIRST IMPLEMENTATION FOCUS:
1. Creation Recipe stage projection/UI over current Workflow.
2. Stage Contract descriptor and server resolver.
3. Effective prompt/config preview with no external calls.
4. Run-only overrides + immutable attempt receipt.
5. `stage.master.propose@1` + explicit Master adoption for Text first.
6. Feedback + “Save what worked” Project workflow promotion.
Only then expand Graphic/Video/media/Variant/CreativeExecution integrations.

BOUNDARIES:
- Preserve current align/F8 owned files except explicit Phase-0 lifecycle correction requested by this change.
- No hidden workflow self-modification.
- No automatic Capability promotion.
- No direct Candidate/Approval/Delivery mutation from stage success.
- Legacy `builtin.generate` remains Draft-oriented.
- No professional-tool auto-dispatch.
- No push/deploy/canonical sync/archive under this handoff.

VALIDATION AFTER MATERIALIZATION:
- `openspec validate --all --strict`
- `git diff --check`
- report exact delta count and any semantic conflicts with active `align-creative-orchestration-product`
- no business code until independent SPEC review

NEXT_EXPECTED_STEP:
STATE: EXECUTED for SPEC materialization only, then return to ChatGPT for independent SPEC review.
