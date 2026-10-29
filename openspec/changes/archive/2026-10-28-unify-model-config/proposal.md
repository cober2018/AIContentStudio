## Why

The user's rule (2026-10-29): every large-model setting lives only under 设置 → AI 与模型, each thing once, and a change there applies everywhere. Today the same vendor or model is configured in several places (survey in `findings.md`): the default chat model in four places (用途路由 default, the `llm` row, a legacy `deepseek` profile, env `LLM_*`); image generation as a separate `image` row beside the capability routes; the writing CLI (dsh) with its own providers and keys in `~/.dsh`; capability bindings copying vendor addresses; voiceover choosing its model on the 配音 page and skipping the routes; topic search reading keys from env or `~/.codex`.

## What Changes

**One place for vendors.** 厂商与模型 is the only place to enter a vendor's address and key. MiniMax keeps its card (already the single MiniMax key). DeepSeek, currently only in `~/.dsh`, is registered there if still used.

**One place for "which model does what".** 用途路由 lists every use and each picks a registered vendor + model:
- chat uses (existing 10 purposes, plus `fact_review` and `identity_review`, which today fall back silently) and a 默认 entry;
- 封面生图 (replaces the `image` row; image size stays as a setting of this use);
- 写作执行 (dsh) default and fallback (replaces the `dsh` row; the app writes `~/.dsh/settings.yaml` and `env.local` from the registered vendors);
- media uses (image, video, voiceover TTS, ASR) — the existing capability routes, but a binding refers to a registered vendor instead of carrying its own `base_url` / `credential_ref`;
- 选题搜索 (MiniMax or Tavily; Tavily is registered as a vendor).

**Removed (only the new version stays):** the 兜底模型 `llm` row and its page; the env fallback `LLM_*`; legacy `models.profiles` with their own address/key (`deepseek`); the AI 生图 form; the dsh 执行层 form; per-binding `base_url` / `credential_ref`; the model picker on the 配音 page (voice, emotion and speed stay there — they are voice settings, not model settings); discovery's `credential_source` (env / codex); **every per-persona, per-account, per-series, per-product, per-SKU and per-stage model choice** (user decision: only 用途路由 decides, one global setup). Existing stored overrides are dropped; old runs keep their recorded model for history.

**Local CLI files** (`~/.mmx`, `~/.dsh`, `~/.wewrite`) are written from AI 与模型 on save; they are copies, never edited by hand.

Not in scope: stock-footage and data connectors (not models), the 自动剪辑 assistant choice (it uses the local Claude Code / Codex account), the duplicate MCP editor, `~/.codex/config.toml` (belongs to the Codex CLI, no longer read by the app).

## Impact

- API: `model_registration.py`, `model_capability_routing.py`, `generation/providers.py`, `system_settings.py`, `routers/settings.py`, `dsh_integration.py`, `voiceover.py`, `discovery_search.py` / `discovery_runtime.py`, `cpa_image_provider.py`, `content_harness/providers.py` (wewrite image), `config.py`; a one-time migration of existing rows into vendors + routes.
- Web: `ModelRegistrationSettings.tsx` (vendors, routes), `ModelRoutingSettings.tsx` (bindings pick a vendor), `RuntimeModelSettings.tsx` (llm / image / dsh forms removed), `ProductSettingsPage.tsx` (section list), `VoiceSettings.tsx`, `DiscoveryPanel.tsx`.
- Per-target overrides removed: `PersonaCreativeConfig.tsx` (`model_binding`, `model_chain`), `content_identity.py`, `creative_configuration.py`; product `model_profile_ref` (`ProductSettingsPage.tsx` 商品制作默认设置, `GuidedProductionProfile.tsx`, `product_skus.py`); stage `model_profile_id` pickers (`StageContractControls.tsx`, `StageTuningPanel.tsx`) and the stage APIs that accept it.
