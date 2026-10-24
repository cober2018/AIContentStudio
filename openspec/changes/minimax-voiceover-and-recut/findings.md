# Findings

- `minimax_cli_provider` TTS sends only `--voice` and `--speed`, always `--format wav`; `mmx speech synthesize` supports volume, pitch, emotion, format, sample-rate, bitrate, channels, text-normalization, latex-read and `--subtitles`.
- Rough cut #6: all shots used one card layout with a fixed 100→104% push; 景别 and 运镜 from the table were not applied; shots 9 and 11 used the same Pixabay file (147 and 149 are the same bytes).
- User's MiniMax settings (2026-10-24): verify_clone_v2, 开心, speed 1, volume 1, pitch 0, MP3, 32000 Hz, 128 kbps, mono.
- MiniMax output at volume 1 measured −31.7 LUFS; it needs mastering before the mix.
- Resolve renders AAC slightly longer than the picture (60.139 s vs 60.067 s); the platform rejects a rough cut whose container differs from the timeline by more than one frame + 1 ms, so the delivery file is bounded by stream copy.
- Resolve scripting: audio level is `SetProperties({"AudioVolumeEnabled": True, "AudioVolume": dB})`; `SetProperty("Volume")` does not work. SRT import does not create a subtitle track, so captions are an AE alpha overlay on V2.
