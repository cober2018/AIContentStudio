# Findings

- Today the 达芬奇主剪 / AE按需制作 form asks for phase, fps, output size, per-shot AE ticks and AE composition settings (`VideoShotMaterialPanel.tsx`, `video.postproduction.v1`).
- 专业执行准备 goes stale (`accepted_stage_input_changed`) whenever the master changes.
- Decision (user, 2026-10-23): DaVinci always cuts and colours; AE per shot as needed; the platform decides, not the user.
- A freshly run 专业执行准备 result is `waiting_input` until accepted; the handoff accepts it with the `professional` domain (package id from `domain_output.result`).
- Master save is committed before the prepare step, so a failure there keeps the placed material; a retry skips placing and only rebuilds the package.
- On 海底光缆 the model chose AE for 10 of 15 rows (graphics, data labels, maps, timelines).
