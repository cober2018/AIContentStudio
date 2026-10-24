## Why

Planning stages of real video works are rejected with `stage_value_too_large` before any model call. The assembled stage (the "resolved stage") must fit 128 KB, but one stage legitimately carries the same material several times:

| Measured on 2026-10-21 (DB copy) | Size | Result |
|---|---|---|
| Persona 2 new work, script, `@3` + three writing-memory methods | 133 KB | rejected |
| Same, `@3` only | 102 KB | accepted |
| Film work U72 (Master 126, 23.5 KB payload), script | 261 KB | rejected |
| U72 shots / master / prepare | 228 / 259 / 185 KB | rejected |

Where the bytes go on U72 script: the Master appears four times (context, upstream, prompt, prompt layers, about 27 KB each); prompt layers repeat the full prompt (63 KB); the method text appears in both the method record and the creative configuration (about 15 KB). The existing compaction helper only applies to built-in `@2` methods, so it cannot rescue `@3` or Capability Memory methods, and even full deduplication leaves U72 near 157 KB. The prompt itself (about 62 KB, ~20k tokens) is well within model limits; only the snapshot bound is too tight.

As a result, a persona cannot combine `@3` with its writing methods, and a work with a real Master cannot re-run script, shots, master or prepare.

## What Changes

- One named bound for the resolved stage snapshot, raised from 128 KB to 512 KB (a Master payload is itself capped at 128 KB, and appears up to four times). It applies where the resolved stage is checked: resolver, invocation validation and snapshot, the two adoption rereads, native media resolution, and the hash helper.
- All other bounds stay as they are: stage outputs, execution receipts, overrides (32 KB), Master payload (128 KB), instruction length, recipe read view.
- No change to what the model receives, to stage shapes or to the existing compaction helper.

## Capabilities

### Modified Capabilities

- `creation-recipe-stage-control-loop`: the frozen input snapshot has an explicit 512 KB bound.

## Impact

- `apps/api/app/services/stage_contracts.py` (constant, `digest`), `stage_resolver.py`, `stage_invocations.py`, `stage_master_adoptions.py`, `stage_domain_adoptions.py`, `stage_domain_integrations.py`.
- Larger `input_snapshot_json` rows for heavy stages (up to 512 KB per attempt).
- Persona 2 can turn the three writing-memory methods back on next to `@3` (only if the user asks).
