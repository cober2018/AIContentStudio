## Why

The first rough cut of 海底光缆 (execution #6) is silent: the video has no voiceover, and the platform has no one-click way to make one. The platform's MiniMax voice call passes only the voice and speed and always writes WAV; the user's MiniMax settings (emotion, volume, pitch, MP3 32 kHz 128 kbps mono) are dropped. The user also pointed out that the cut ignores the storyboard's 景别 (shot size) and 运镜 (camera move), and that two shots reuse the same ship footage.

## What Changes

- **Voice settings (设置 → 配音).** One saved MiniMax voice setup, used by default for every video: voice `verify_clone_v2`, emotion 开心 (`happy`), speed 1, volume 1, pitch 0, MP3, 32000 Hz, 128 kbps, mono; LaTeX reading and Chinese/English normalization off. All fields editable; the model defaults to speech-2.8-hd.
- **Platform passes every setting to MiniMax.** The MiniMax voice adapter sends voice, speed, volume, pitch, emotion, format, sample rate, bitrate and channels, and asks for subtitle timing. The applied values are recorded with the result.
- **One-click 生成配音 on 制作内容.** It reads the 台词 column (narration lines in order), generates the voice with the saved settings, adds it to the material library, puts it into the master as the voice track and saves. Line timings from MiniMax are kept for captions and for the edit.
- **Re-cut follows the voice and the storyboard (edit rules, not platform code).** The next edit round times each shot to its narration line; applies 景别 (特写 → tight crop of the source, 中景 → card, 全景 → full-bleed frame) and 运镜 (推近/拉远/横移/跟拍/环绕/固定 → matching AE move); never repeats the same footage in two shots, using a close crop or a motion graphic instead; burns captions from the narration timing.
- Not in this change: music, edit proxies in the standard project folder.

## Impact

- API: `minimax_cli_provider` TTS arguments; `model_capability_routing.tts_parameters` accepts the new fields; settings key `voice_default`; a `生成配音` endpoint that runs TTS for a unit, accepts the result into the library and saves the master voice track.
- Web: settings section 配音; 制作内容 button ① 生成配音 with a player.
- Edit craft: the `resolve-edit` / `ae-motion` skill entries get the voice-timed, shot-size and camera-move rules.
