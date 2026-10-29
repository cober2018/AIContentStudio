# Findings

- 2026-10-29: Card key (tail `wLGo`) passes MiniMax quota on the China endpoint; the old key (tail `kN7w`) is rejected. The old key is still in the `llm` and `image` rows, `~/.mmx/config.json` and `~/.dsh/env.local`.
- The voiceover code already passes the card key with `--api-key`; the failure came from the video agent reading `~/.mmx/config.json` itself.
- Topic search reads `MINIMAX_API_KEY` from the environment or `~/.codex/config.toml`, not the card.
- Decision (user): the MiniMax card is the only place to enter the MiniMax key.
- The default LLM route currently points to a registered non-MiniMax provider (local 127.0.0.1:8317), so the MiniMax `llm` row is only the fallback.
- New request (user, 2026-10-29, not in this change): all model configuration must live only under 设置 → AI 与模型, globally unique and applied everywhere. Needs its own proposal.
