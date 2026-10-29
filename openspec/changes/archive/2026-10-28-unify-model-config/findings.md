# Findings (survey 2026-10-29)

- Default chat model is defined in 4 places: `models.default_profile`/routes, `llm` row (shadowed), legacy `models.profiles.deepseek`, env `LLM_*`. dsh has its own default in `~/.dsh`.
- `image` row (+ `~/.wewrite/config.yaml`) is parallel to capability routes (`minimax.image`, `cpa.*.image`).
- Capability bindings carry `base_url` and `credential_ref`; `credential_ref` is never resolved. CPA image requires binding base_url == provider base_url (copy).
- The four `minimax.*` profiles are manual, not linked to the MiniMax vendor.
- Voiceover takes `voice_default.model_id` and calls `minimax.cli` directly, skipping routes.
- Purposes `fact_review`, `identity_review` are requested but not in PURPOSES; they fall back silently.
- DeepSeek exists only in `~/.dsh`; Tavily only in env / `~/.codex`.
- Persona `model_binding` / `model_chain` and product `model_profile_ref` are free-text copies of profile ids.
- Out of scope (not models): connectors, stock sources, edit assistant, duplicate MCP editor.
- Decision (user): vendors registered once in 厂商与模型; other places only choose vendor + model.
- Decision (user, 2026-10-29): remove all per-persona / per-product / per-stage model overrides; 用途路由 is the only choice.
- Topic search: the pinned safe fetch rejects api.minimaxi.com on this machine (resolves to a reserved range via proxy), so MiniMax search keeps the local MiniMax MCP (uvx) path, now with the card key.
- The OpenAI native image path is chosen by model name (gpt-image-* / dall-e-*) for 封面生图; other image models go through wewrite (MiniMax → provider minimax, other vendors → provider openai with base_url).
- Native adapters (google/xai/minimax.native) never execute, so they may stay without a vendor; executable adapters must have one.
- Tests removed with their features: llm endpoints (9), legacy models writer (8), dsh PUT (1), save_image (1), legacy URL views (2), persona custom/composed bindings (3). Other tests switched to vendor + route setup.
