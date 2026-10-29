## Why

MiniMax keys are stored in several places: the 厂商与模型 → MiniMax card, the 主模型 (LLM) settings, the AI 生图 settings, the local `~/.mmx/config.json`, the writing CLI `~/.dsh/env.local`, and the topic search (environment variable / `~/.codex/config.toml`). The user entered a new key on the MiniMax card (it works), but the other places still hold the old key that MiniMax now rejects. Voiceover failed because the video agent read `~/.mmx/config.json`; article writing and cover images would fail the same way. The user's rule: **one MiniMax key, entered on the MiniMax card, used everywhere.**

## What Changes

- The MiniMax card's API key is the only MiniMax key. Everything that calls MiniMax reads it from there. If the card has no key, the existing fallback to the local `mmx` login stays.
- Saving the card also writes the key into the local files that outside tools read: `~/.mmx/config.json` (`api_key`), `~/.dsh/env.local` (`MINIMAX_API_KEY`), and the `image` entry in `~/.wewrite/config.yaml` when its provider is MiniMax. The video agent and these CLIs then see the same key.
- 主模型 (LLM) and model profiles: when the endpoint is a MiniMax address, the call uses the card's key. The section shows "密钥：用 MiniMax 卡片" instead of its own key field.
- AI 生图: when the provider is MiniMax, the call uses the card's key, and the section shows the same note instead of a key field.
- Topic search with provider MiniMax uses the card's key.
- Old MiniMax keys stored in the LLM and image rows are removed (only the new version is kept).
- Not changed: keys for other vendors (OpenAI, Gemini, DeepSeek, etc.), the MiniMax card's region and endpoint fields, and voice settings.

## Impact

- API: `minimax_cli_provider.py` (one shared key reader + local file sync on save), `generation/providers.py` (LLM key), `system_settings.py` / `routers/settings.py` (image key, views), `discovery_search.py`, `openai_image_provider.py` / `routers/materials.py` only where they read the MiniMax image key.
- Web: `RuntimeModelSettings.tsx` (LLM and image sections hide the MiniMax key field), `ModelRegistrationSettings.tsx` (card text: "所有 MiniMax 功能共用这把密钥").
- Local files written on save: `~/.mmx/config.json`, `~/.dsh/env.local`, `~/.wewrite/config.yaml`. Other fields in these files are kept.
