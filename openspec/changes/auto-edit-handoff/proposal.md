## Why

After 采用这版, the user still has to do three manual things before an edit can start, all hidden under 更多:
1. put each row's chosen material into the master (放入草稿) and save;
2. rebuild 专业执行准备 (导演包), which goes stale whenever the master changes;
3. fill 达芬奇主剪 / AE按需制作: phase, fps, size, and tick which shots go to AE.

The user's rule: DaVinci always does the cut and colour; AE does effects for the shots that need them. The platform decides; the user should not pick (「我选择的话就会很别扭」).

## What Changes

- **Materials into the master automatically.** When autofill finishes after 采用这版 (or when the table already has material), every row with exactly one pick gets that material placed into the master and the master is saved. Rows with several picks or none are left as they are and listed as 待你选 / 缺口.
- **Edit settings decided by the platform.**
  - DaVinci: always, for every shot (cut, colour, sound).
  - AE: per row, decided by the model from that row's 画面 / 运镜 / 备注 (on-screen text, map, diagram, comparison, data, title card, special transition → AE). The reason is shown in the table. Rows whose material is already an AE template render do not go to AE again.
  - Size and fps from the video: 9:16 → 1080×1920, 16:9 → 1920×1080, 30 fps. AE compositions use the shot's length and the same size.
  - Phase: first package 粗剪; after the user accepts a rough cut with notes 修改; final export only when the user says so.
- **导演包 rebuilt automatically.** After the master is saved, 专业执行准备 is re-run and its result accepted, so it is never left stale.
- The 制作内容 page shows the result as one line per row in the table (素材 + 达芬奇 / 达芬奇+AE with the reason). The old form stays under 更多 for overrides.
- Not in this change: one-click voice, edit proxies in the standard project folder, assembling the cut by itself.

## Impact

- API: a small orchestration step after autofill (place picks, save master, decide AE rows, set postproduction, run and accept the prepare stage), reusing existing services; one model call per video for the AE decision.
- Web: 素材 column shows 后期: 达芬奇 / 达芬奇+AE and the reason; progress line under the 导演稿 header.
