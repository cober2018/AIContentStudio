## 1. Persistent project foundation

- [ ] 1.1 Add additive ContentProject, ContentUnit, minimal content Persona/Role identity, Persona × Modality default binding, project workflow binding, DataSnapshot, and project output association persistence with a reversible migration; preserve existing Topic/Workflow rows.
- [ ] 1.2 Add project and unit CRUD APIs with existing editor/read permission checks and stable IDs; a unit records Persona, modality, and pinned workflow version.
- [ ] 1.3 Add one shared project-run/definition authorization policy based on persisted Project/Unit ownership; apply it before serialization or mutation in both project-scoped and legacy APIs. Cover run detail/list, attempts, retry, node rerun, rerun-from-here, human completion, cancel, Workflow list/serialization, clone/publish, and raw create-run; retain Topic-only behavior.

## 2. Versioned workflow design

- [ ] 2.1 Add a server-side validator for six distinct node types, node IDs, registered plugins, dependencies, cycles, visual order, input/output mappings, execution conditions, failure policies, unsupported executors, and prohibited side effects; store visual order separately from edges.
- [ ] 2.2 Add project override save with optimistic revision precondition and immutable workflow versions; preserve historical run definitions.
- [ ] 2.3 Add a server-side template portability gate: allow-list structural fields and reusable profiles, turn provably safe project bindings into placeholders, reject non-portable project/unit/run/snapshot/asset/draft/candidate/attempt IDs or actual outputs, and leave both save scopes unchanged on rejection.
- [ ] 2.4 Add a separate, authorized “save as new Persona × Modality default” API using that portability gate, immutable Workflow versions, optimistic binding revision, and no implicit rebinding of existing units/runs; make the current default selectable by later units.
- [ ] 2.5 Add project-scoped create/run-node/run-from-here/human-complete/attempt APIs using existing engine and role checks; pin each run's definition version/checksum.

## 3. Data Node execution

- [ ] 3.1 Add typed Data Source Plugin descriptors and selector API for internal data, media data, Notion, Obsidian, API, and SQL/Database, with schema/capabilities/availability/reason; implement one verified read-only Studio Source adapter without coupling the contract to it.
- [ ] 3.2 Persist bounded source snapshots with checksum, lineage, source/version identity and normalized output; connect Data Node execution and refresh to node attempts.
- [ ] 3.3 Verify changed refresh marks dependency descendants stale, unchanged refresh preserves their state, and disconnected plugins cannot record successful execution.

## 4. Workflow output associations

- [ ] 4.1 Persist supported Draft/AssetRevision/Candidate output references to project, unit, run, node, attempt, and applicable rights/source lineage; surface generated image/chart/screenshot/video-clip revisions in Project Shared Assets without copying or fabricating media.

## 5. Production frontend

- [ ] 5.1 Replace local project/unit CRUD on real routes with backend repository calls while keeping demo fixtures explicitly separate; expose Persona × Modality default selection on new units.
- [ ] 5.2 Build selected-unit text, graphic, and video workspace shells and project-shared-assets entry.
- [ ] 5.3 Build mini canvas, six node types, node inspector, status/attempt/input/output views and bounded active-run refresh.
- [ ] 5.4 Build design mode with add/edit/disable/delete, drag-and-drop visual reorder plus keyboard/up-down alternative, explicit dependency/edge and input/output mapping editing, Provider/Model/Tool/Data Source selection, conditions/failure policy, unsaved indicator, server validation feedback, and explicit save/conflict handling; dragging alone never rewires edges.
- [ ] 5.5 Provide separate project-override save and “save as new role default version” controls with clear target, version, and conflict feedback; never silently update the other scope.
- [ ] 5.6 Add Data Source Plugin selector/configuration with server-derived disconnected/unexecutable state; wire Run Node, Run From Here, Data Refresh, and human-step completion to real project-scoped APIs without optimistic execution success.

## 6. Verification and handoff

- [ ] 6.1 Add targeted regression tests for new FE-F2 invariants using the existing test infrastructure: cross-project run denial; legacy raw-run/definition API denial; project override isolation from Persona default; new Persona default not rebinding old units; project-bound value portability rejection/parameterization; concurrent save returning 409; changed snapshot causing downstream stale; unchanged snapshot preserving downstream state; disconnected plugin blocked without synthetic snapshot; side-effect node generic rerun denied; generated AssetRevision in the owning project; historical run retaining its definition checksum; visual reorder preserving edges and explicit mapping edits receiving server validation. Run available build/typecheck and backend checks.
- [ ] 6.2 Perform local development-DB acceptance of both save paths, later-unit selection, all legacy authorization entry points, portability gate, visual-order/edge separation, safe execution/attempt readback, snapshot stale/unchanged behavior, disconnected-source blocking, project asset lineage, permission denial, and no external side effect.
- [ ] 6.3 Review owned diff against Frontend Product Contract V1, update README/task_plan/progress/findings, and archive the OpenSpec after acceptance.
