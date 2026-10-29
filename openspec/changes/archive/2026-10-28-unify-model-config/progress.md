# Progress

- 2026-10-29: Survey done, proposal written. No code changed.
- 2026-10-29: Applied locally (not committed). Backups of the DB and `~/.mmx`, `~/.dsh`, `~/.wewrite` in the session scratchpad (`unify-backup/`), not in the repo (keys).
  - Vendors: MiniMax card is vendor `minimax` (chat models registrable; address from card region/address, key from card). `models.uses` = 封面生图 / 写作工具 / 选题搜索. Purposes `fact_review`, `identity_review` added.
  - Removed: `llm` / `image` / `dsh` rows and their endpoints and forms, legacy `/settings/models`, env `LLM_BASE_URL/API_KEY/MODEL` (env can only switch to offline mock), discovery `credential_source`, voice page model picker, per-binding address/key fields, persona / product / stage / tuning model choices.
  - One-time startup migration `model_registration.migrate_to_single_source` (schema_version 3); local CLI files written by `model_registration.sync_cli_files`.
  - Media bindings: MiniMax CLI bindings tie to vendor `minimax`; OpenAI-compatible bindings must match a registered vendor; address filled from the vendor.
  - Old records keep stored model choices as history; stage resolution strips them (`USER_MODEL_KEYS`), persona profiles drop them on save.
- Verified: real migration (schema 3, old rows gone, uses set); local files hold the card key (600); MiniMax chat 200; topic search returns results; card test ok via API; voice model follows TTS route; `tsc` + web build pass; backend 2585 passed, 5 failed (4 `legacy0001` migration-head tests from commit 428357b, 1 missing local skill `wewrite-write`) — unrelated.
