## 1. Data
- [x] 1.1 Migration: existing `llm`, `image`, `dsh`, legacy profiles, capability bindings and `voice_default.model_id` become routes on registered vendors; register DeepSeek/Tavily if in use; drop the old rows/fields.

## 2. API
- [x] 2.1 One resolver: use → (vendor, model, key). Chat, cover image, media capabilities, voiceover, writing CLI, topic search all call it.
- [x] 2.2 Remove env `LLM_*` fallback, `credential_ref`, discovery `credential_source`.
- [x] 2.3 Write `~/.dsh`, `~/.wewrite`, `~/.mmx` from vendors + routes on save and at startup.

## 3. Web
- [x] 3.1 用途路由: all uses (chat, 默认, 封面生图, 写作执行, image/video/TTS/ASR, 选题搜索) as vendor + model pickers.
- [x] 3.2 Remove 兜底模型与生图 forms; bindings pick a vendor; 配音 page loses its model picker; discovery loses key-source choice.
- [x] 3.3 Remove model choices on persona/account/series, product defaults, SKU, work settings and stage controls (API fields too; old records keep history only).

## 4. Verify
- [x] 4.1 Change one vendor key → chat, cover image, voiceover, writing CLI and search all use it. `tsc`, web build, API tests on the touched modules pass.
