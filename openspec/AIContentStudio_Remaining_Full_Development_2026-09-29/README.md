# AIContentStudio — Remaining Full Development Package

Generated: 2026-09-29

This package turns the remaining North Star work into one sequential development program.

## Verified starting point

- Workspace: `AIContentStudio`
- Branch: `main`
- HEAD at planning time: `ca52aa5`
- Working tree: dirty with uncommitted FE-F6B implementation
- FE-F6B: 131/162, 31 remaining
- F6B Backend Milestone A/B: PASS
- F6B professional Text frontend 15–20: implemented
- current remaining F6B work: cross-layer proof, regressions, browser acceptance, final gates

## Module task counts

| Module | Planned tasks |
|---|---:|
| F6B Final Close | 31 |
| F6C Graphic Production Studio | 71 |
| F6D Video Production Studio | 79 |
| F6E Channel Variants + Content Matrix | 102 |
| F7 Capability Integrations + Delivery | 96 |
| F8 Production Readiness + Operations | 91 |
| **Total remaining planned tasks** | **470** |

Only the F6B 31-task count is an already-active repository OpenSpec count. F6C–F8 counts are the new planning decomposition in this package and should be normalized against the actual code before apply.

## Package structure

- `MASTER_EXECUTION_PLAN.md` — scope, ordering, invariants, migration and completion definition
- `STATUS_MATRIX.md` — what is already done vs still missing
- `MASTER_C2C_APPLY.md` — one-shot sequential implementation control message
- `modules/00-fe-f6b-final-close` — continue existing active F6B change
- `modules/01-fe-f6c-graphic-production-studio` — proposed new OpenSpec
- `modules/02-fe-f6d-video-production-studio` — proposed new OpenSpec
- `modules/03-fe-f6e-channel-variants-content-matrix` — proposed new OpenSpec
- `modules/04-fe-f7-capability-integrations-delivery` — proposed new OpenSpec
- `modules/05-fe-f8-production-readiness-operations` — proposed new OpenSpec

## Source-defined vs engineering-completion scope

Direct North Star/product-contract scope:
- professional Text/Graphic/Video Production Engines
- ChannelVariant and Channel Adapter
- Identity × Modality × Channel content matrix
- replaceable capabilities and verified Publisher behavior
- observability
- five-level testing including Real Platform verification
- safety boundaries

Engineering-completion additions derived from "production readiness":
- secure production auth mode replacing development-header mode
- storage/runtime/deployment hardening
- backup/restore/readiness runbooks

This package deliberately does **not** invent organization/invite/tenant/SSO product administration because the canonical Settings spec says these do not currently exist and North Star does not define them.

## Apply policy

This package is ready for review. It is not a repository mutation.

When the user authorizes a master apply:
- re-read current code through the AIContentStudio connector;
- normalize each future module against actual code before editing;
- implement modules in order;
- run each module's gates before proceeding;
- do not ask for a new product-design decision between passing modules;
- stop only on the explicit stop conditions in `MASTER_EXECUTION_PLAN.md`;
- do not push, deploy or run production migrations unless separately authorized;
- do not canonical-sync/archive changes unless separately authorized.
