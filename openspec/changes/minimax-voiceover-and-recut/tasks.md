## 1. API

- [x] 1.1 TTS parameters: volume, pitch, emotion, format, sample rate, bitrate, channels, subtitles; MiniMax CLI receives them.
- [x] 1.2 Settings `voice_default` with the user's values; `GET/PUT /settings/voice`.
- [x] 1.3 `POST /content-projects/{p}/units/{u}/voiceover`: script → TTS → library material → master voice track saved; timing kept.

## 2. Web

- [x] 2.1 设置 → 配音.
- [x] 2.2 制作内容 ① 生成配音 with player.

## 3. Edit rules

- [x] 3.1 `ae_build.py`: per-cut `framing` and `camera`; skill entries updated.

## 4. Verify

- [x] 4.1 海底光缆: voice generated with the user's settings; new rough cut timed to the voice, with shot sizes, camera moves, captions and no repeated footage; submitted for review.

## 5. Docs

- [x] 5.1 README, task_plan, progress, findings.


Notes: 1.3 also aligns shot lengths to the voice (J-cut when a clip is shorter than its line) and reuses an identical earlier voice instead of paying again. 3.1 also moves full-bleed credits above captions.
