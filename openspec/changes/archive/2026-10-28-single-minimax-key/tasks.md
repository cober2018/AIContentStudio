## 1. API

- [x] 1.1 `minimax_cli_provider.shared_key()`; card save syncs `~/.mmx/config.json`, `~/.dsh/env.local`, `~/.wewrite/config.yaml` (key only).
- [x] 1.2 LLM (`effective_llm_config` and profiles) uses `shared_key()` for MiniMax endpoints.
- [x] 1.3 Image (MiniMax provider) and topic search (MiniMax) use `shared_key()`.
- [x] 1.4 Settings save/views: no MiniMax key stored in `llm` / `image`; startup removes the old ones.

## 2. Web

- [x] 2.1 LLM and image sections: hide the key field for MiniMax, show "密钥：用 MiniMax 卡片".
- [x] 2.2 MiniMax card: note "所有 MiniMax 功能共用这把密钥".

## 3. Verify

- [x] 3.1 Card 测试连接 passes; LLM call, cover image and voiceover each reach MiniMax with the card key; the three local files hold the card key (checked by masked tail only). LLM checked with a direct MiniMax chat call (200).
- [x] 3.2 `tsc` and web build pass.
