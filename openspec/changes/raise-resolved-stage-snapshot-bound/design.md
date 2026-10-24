## Context

`canonical(value, max_bytes=128 * 1024)` is the generic bound for every stage value. The resolved stage reuses that default in four places. The resolver retries with `_compact_method_audit` when over the bound, but that helper refuses anything other than built-in `@2` stacks.

## Decisions

- **Raise the bound instead of reshaping the snapshot.** Removing every duplicate still leaves real works above 128 KB (U72 ≈ 157 KB), and moving the Master out of context/upstream would touch the many readers of `context.master` and `upstream`. A larger bound is the shortest correct fix.
- **512 KB.** Covers four copies of a maximal 128 KB Master; the largest measured stage is 261 KB.
- **Scope only the resolved stage.** Outputs and receipts keep 128 KB because they are model- or executor-produced and their size is not driven by accepted inputs.
- **Hashing follows the larger bound.** `digest()` re-checked 128 KB, so hashing a resolved stage failed even after the snapshot bound was raised. Hashing stores nothing; persisted values (outputs, receipts, overrides, Master payload) are still bounded where they are written.
- **Keep `_compact_method_audit` unchanged.** With the new bound it rarely runs; generalising it is not needed for this fix.

## Risks

- Bigger rows in SQLite for heavy stages. Acceptable: one row per attempt, bounded at 512 KB.
- Model input grows with the snapshot. The effective prompt for the largest measured stage is ~62 KB; provider limits still fail visibly if exceeded.
