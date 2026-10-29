# Progress

- 2026-10-29: Proposal written. No code changed.
- 2026-10-29: Applied. API: `minimax_cli_provider` (`shared_key`, `is_minimax_url`, `sync_local_files`, `forget_old_keys`, card save resets LLM cache), `main.py` startup, `generation/providers.py`, `routers/settings.py` (LLM / profiles / image / LLM test), `system_settings.py`, `discovery_search.py`. Web: `RuntimeModelSettings.tsx`, `ModelRegistrationSettings.tsx`.
- Verified: card, `~/.mmx/config.json`, `~/.dsh/env.local`, `~/.wewrite/config.yaml` and topic search all end in `wLGo`; old keys removed from `llm` / `image` rows; card test ok; MiniMax chat with card key 200; `tsc` + web build pass; API and worker restarted (launchd), health 200.
- Backups of the three local files and the DB before the change: scratchpad `key-backup/` (session only).
