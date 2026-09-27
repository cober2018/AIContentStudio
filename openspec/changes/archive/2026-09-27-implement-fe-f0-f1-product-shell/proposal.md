## Why

The approved Product Experience V5 and Frontend Product Contract V1 make ContentProject the user-facing root. The current React navigation remains organized around legacy Source/Topic/Workflow pages, so FE-F0-F1 needs a navigable product shell and interactive project core before FE-F2.

## What Changes

- Add nine primary workspaces and keep legacy routes reachable for existing operations.
- Add local mock ContentProject repository with healthy and abnormal fixtures, status distinctions, and local Content Unit CRUD.
- Add a seven-tab project workspace, shared-assets drawer, and selected-unit production shell.
- Preserve existing backend calls and schemas; all new project data remains local mock state.

## Capabilities

### New Capabilities

- `fe-f0-f1-project-experience`: Product navigation, project core, matrix editing, shared assets, and status semantics.

### Modified Capabilities

None.

## Impact

Changes are limited to `apps/web/src` and project documentation. No backend migrations or API changes. Source: `AIContentStudio_WORK_HANDOFF_FE-F0-F1_2026-09-27.md` and its referenced North Star V2, Frontend Contract V1, and prototype V5.
