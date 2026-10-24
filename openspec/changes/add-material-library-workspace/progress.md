# Progress

- 2026-10-22 素材库 implemented (A1–A5). Migration `matlib0001` applied, API restarted. Build passes; web tests 37/37; material/library API tests 72 passed. Screenshot review at desktop and 390px done (fixed drawer offset, audio card styling, collection mosaic, mobile filter row).
- Not done: full API suite, README, B (按文案找素材) not started beyond research.
- B findings: Openverse API timed out / 502 from this network; NASA images API TLS fails; Coverr needs a key and its API could not be confirmed, so Coverr is dropped. Chat routes exist (cpa: gemini-3.8-flash-high default; claude-opus-4-6-thinking; grok-4.7) via `get_provider(purpose).generate_json` with `image_inputs` for vision.
