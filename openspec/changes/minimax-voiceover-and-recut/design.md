## Decisions

- The setting is one global default (the user's MiniMax setup); a later per-persona override can reuse the same shape.
- Text sent to MiniMax = the master's script blocks in shot order, joined with line breaks; one call (≤10k chars). If a line is longer than the model limit, the call fails with a plain reason instead of splitting silently.
- MiniMax subtitle timing (`--subtitles`) is stored with the voice material; the edit uses it to place each shot and the captions. If timing is missing, the edit falls back to ASR on the voice file.
- Voice files are new materials, so they go to the material library (`AIContentStudio/音频/`).
- Shot size and camera move mapping lives in the craft skills, so the AE builder gains `framing` and `camera` per cut; the platform contract does not change.
