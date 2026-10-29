## Single source

`minimax_vendor.api_key` (the MiniMax card) is the source. One function, `minimax_cli_provider.shared_key()`, returns: card key → else local `mmx` login key → else empty. Every MiniMax caller uses it; none keeps its own copy.

## Which calls count as MiniMax

- LLM / model profile: endpoint host is `api.minimax.cn`, `api.minimaxi.com`, `api.minimax.io` or `api.minimax.chat`.
- Image: `provider == "minimax"`.
- Topic search: `search_provider == "minimax"`.
- Voiceover / ASR / mmx image and video: already use the card key via `--api-key`.

## Local file sync

On card save (and once at startup if the files differ), write the key into `~/.mmx/config.json`, `~/.dsh/env.local` and the MiniMax image entry in `~/.wewrite/config.yaml`. Only the key line/field changes; other content is kept. Clearing the card key does not touch these files (they become the fallback login again).

## Old keys

On first startup after this change, the `api_key` field is removed from the `llm` row and the `image` row when they point to MiniMax. Saving those sections no longer accepts a MiniMax key.
