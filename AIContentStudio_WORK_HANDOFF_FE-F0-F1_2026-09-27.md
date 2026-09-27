# AIContentStudio · WORK HANDOFF

> Workspace: AIContentStudio  
> Kind: repository (Python / FastAPI + React)  
> Role split: ChatGPT = planning/review; Codex/Work = execution  
> Date: 2026-09-27  
> Status: Product experience V5 finalized; frontend implementation starts now.

## SOURCE OF TRUTH

Use these artifacts in this order:

1. `AIContentStudio_产品战略与总体架构蓝图_NorthStar_V2_2026-09-26.md`
   - Product and architecture North Star.
2. `AIContentStudio_Product_Experience_Prototype_V5.html`
   - Finalized clickable product experience reference.
3. `AIContentStudio_Frontend_Product_Contract_V1_2026-09-27.md`
   - Authoritative frontend implementation contract for the next phase.
4. This HANDOFF
   - Current execution goal and next expected step.

If implementation details conflict, preserve the product semantics in the Frontend Product Contract V1 and the North Star invariants rather than reproducing incidental HTML implementation details.

---

## FINALIZED PRODUCT DECISIONS

### Business root
`ContentProject` is the primary business object.

A project can contain multiple:

- identities / roles;
- text, graphic and video content units;
- channels;
- workflow runs;
- shared assets;
- candidates and deliveries.

### Main user-facing workspaces

1. Today / Home
2. Opportunities
3. Content Projects
4. Production Workspace
5. Review & Distribution
6. Content Identities
7. Assets & Knowledge
8. Performance & Learning
9. Settings

### Content identity
Identity is a long-lived product asset, not just prompt text.

Hierarchy:

`Workspace → Brand → Persona/Role → Account → Series`

Identity includes stable identity, voice, visual language, long-term viewpoints, boundaries, account/channel context and content memory.

### Content matrix
Within a ContentProject, users can add/edit/delete Content Units.

A Content Unit binds:

`Identity × Modality × Channel × Workflow`

Modalities are first-class and parallel:

- Text
- Graphic / Image
- Video

### Project assets
Production pages expose a compact **Project Shared Assets** entry. Assets open in a modal/drawer instead of permanently occupying the editor.

Project assets include:

- uploads;
- web/external collected materials;
- references to system-wide reusable assets;
- workflow-generated images;
- workflow-generated charts;
- workflow-generated screenshots;
- workflow-generated video/audio fragments;
- intermediate and reusable outputs.

All are modeled conceptually as `Asset / AssetRevision`.

### Workflow
Workflow is part of the core Production Workspace.

Each role × modality may have its own default workflow.

A concrete project Content Unit instantiates a `WorkflowRun`, which can be overridden for that project without silently mutating the role template.

The mini canvas is both execution view and debugger.

It must support:

- inspect node;
- add node;
- edit node;
- delete node;
- drag/reorder nodes;
- run single node;
- run from selected node;
- inspect input/output;
- refresh data node;
- save project override;
- explicitly publish a new role × modality workflow template version.

Do **not** expose Skill as a primary product concept.

### Workflow node categories

- Data
- AI
- Tool
- Rule
- Human
- System

### Data Source Plugin
Data nodes use a plugin abstraction rather than hard-coded data systems.

Initial examples:

- quantitative/internal-data platform;
- media-analysis platform;
- Notion;
- Obsidian;
- generic API;
- SQL/database.

Future sources must be addable through the same Data Source Plugin contract.

Data refresh creates a new snapshot. Downstream derived state that depended on an older snapshot becomes `stale`.

### Review & Distribution
Default organization is project-first:

`Project → Content Unit → Candidate`

A project may contain multiple text/graphic/video items.

Supporting status view can aggregate Ready / Blocked / Stale / Unknown / Approved.

Approval lifecycle remains separated:

`Resolve blocker → Freeze Candidate → Content Approval → Delivery Authorization → Delivery`

### Performance & learning
The system must recover and analyze useful historical published content, not only newly-produced Studio content.

Historical ingestion should preserve available text, images, video, subtitles, identity/account/channel mapping, timestamps, metrics, comments and recoverable production lineage.

Missing historical data is represented explicitly with coverage/confidence; never fabricate it.

Observations become `LearningCandidate` before they can alter strategy or memory.

---

# CURRENT EXECUTION TASK

## TASK
**FE-F0-F1 — Build the finalized AIContentStudio product shell and ContentProject core.**

## GOAL
Implement the approved V5 product experience in the existing React frontend using mock/local data only.

Do not redesign backend APIs and do not introduce backend migrations in this slice.

## REQUIRED FIRST ACTION
Read the current repository before editing.

Confirm workspace identity is exactly `AIContentStudio`.

Inspect:

- frontend package structure;
- router;
- page/layout conventions;
- existing design system/components;
- state/data-fetch conventions;
- current content/project/workflow pages;
- existing tests/build scripts.

Reuse existing conventions when they do not conflict with the finalized product contract.

## SCOPE

### F0 — Shell + Mock Runtime

Implement:

- application shell;
- navigation for the nine top-level product workspaces;
- route skeletons;
- local/mock repository or fixture layer;
- shared status badges;
- modal/drawer/tabs/empty-state primitives if equivalent primitives do not already exist;
- page-level loading/error/empty states.

### F1 — ContentProject Core

Implement:

1. ContentProject list/shell.
2. ContentProject workspace with tabs:
   - overview
   - brief
   - evidence
   - assets
   - matrix
   - versions
   - activity
3. Content Matrix CRUD:
   - add Content Unit
   - edit Content Unit
   - delete Content Unit
4. Each Content Unit expresses:
   - identity
   - modality
   - channel
   - workflow reference/status
5. Project Shared Assets entry + modal/drawer.
6. Asset fixtures for:
   - upload
   - system reference
   - workflow-generated
7. Navigation from selected Content Unit into Production Workspace shell.
8. Shared distinct rendering for:
   - blocked
   - stale
   - unknown
   - ready
   - waiting_human
9. At least:
   - one healthy project fixture
   - one abnormal project fixture

## OUT OF SCOPE FOR THIS EXECUTION

Do not yet implement the full F2 workflow designer/debugger.

Do not:

- add backend migrations;
- redesign backend APIs;
- build a generic low-code DAG product;
- expose Skills as primary UI;
- bind mock view state tightly to a guessed future ORM schema.

The Production Workspace route/shell may be created in F1, but the full Workflow Debugger belongs to FE-F2.

## ACCEPTANCE

- User can browse the primary shell.
- User can open a project and navigate all seven project tabs.
- User can add/edit/delete a Content Unit.
- User can open Project Shared Assets without that asset browser permanently occupying the production page.
- Workflow-generated assets are represented in project asset fixtures.
- User can enter Production Workspace for a selected Content Unit.
- Blocked / Stale / Unknown are visibly and semantically distinct.
- Existing frontend tests/build remain green.
- No backend migration is added.

## REVIEW AFTER EXECUTION

After EXECUTED:

1. Read execution output (list, then readable output).
2. Inspect git status.
3. Review the complete git diff.
4. Verify build/tests/lint/typecheck that exist in this repo.
5. Check the implementation against the Frontend Product Contract V1 rather than only visual similarity to the HTML prototype.
6. Flag accidental backend/schema changes.
7. Verify that ContentProject remains the business root and that technical implementation terminology has not leaked into normal user-facing UI.

## NEXT_EXPECTED_STEP

If FE-F0-F1 passes review, issue:

**FE-F2 — Production Workspace + Workflow Debugger**

FE-F2 will implement:

- text / graphic / video workspace shells;
- Workflow Mini Canvas;
- Node Inspector;
- add/edit/delete node;
- drag reorder;
- run node / run from here;
- Data Node;
- Data Source Plugin selection;
- refresh snapshot → downstream stale;
- project workflow override;
- explicit save-as-new role × modality workflow-template version.

---

# C2C CONTROL MESSAGE

STATUS: READY_FOR_EXECUTION

TASK_ID: FE-F0-F1

SOURCE_OF_TRUTH:
- North Star V2
- Product Experience Prototype V5
- Frontend Product Contract V1
- this HANDOFF

NEXT_EXPECTED_STEP:
Execute FE-F0-F1 in the current AIContentStudio repository, report EXECUTED, then return changed files + tests/build/lint/typecheck results for review.
