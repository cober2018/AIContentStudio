# Progress

- 2026-10-22 Backend: `open_media` adapters (Pixabay, Pexels, Openverse, NASA, Commons), `material_matching` service, `material_match_run` (`matmatch0001`), routes under `/material-match*`. Fake-IP proxy exemption for stock downloads and the existing Wikimedia fetch (dev only, 198.18/15 only).
- Web: 素材库「按文案找素材」tab; AI 创作助手「为镜头找素材」on the video 逐镜素材 step (picked material binds to the shot draft after the project asset list reloads).
- Real runs on the ESP32 script: run 1 (own library only) 3/8 matched; run 3 (Pixabay + Commons, retries) 1/3 matched by own footage, 2 honest gaps. Pixabay key stored in ignored runtime env (0600).
- Network: Openverse times out, NASA / Library of Congress TLS drops via the current proxy. Internet Archive and Europeana reachable — not yet added (awaiting user decision).
- Checks: build passes; material/library/search API tests 54 passed. Full API suite not yet run.
- 2026-10-22 Internet Archive added (no key; licence allowlist CC0/PDM/CC BY; items ≤32 MB). Pexels hidden unless a key exists. Judge recalibrated (subject/scene first; conflicts only for factual mismatch). Provider retries (switch off after 4 misses). Accepted media probed for size/length. End-to-end accept verified: Pixabay clip → material #118 rev #123 with source, licence, attribution (test artefact, not attached to a project). `video-material-scout` skill updated.
- 2026-10-22 海底光缆样片驱动的匹配改进：Commons 适配改为直连并按单文件许可（公有领域 / CC0 / 任意版本 CC BY；排除 SA/NC/ND）；规划器标 footage=real|motion，动效镜头不检索（状态 motion）；检查只评价素材本身（后期元素不扣分）；按来源轮流组成待评池；档案库用短关键词；400px 以上小图作小卡片保留；默认不严格限制画幅。第五轮：镜头12 主选 Commons 版画《Grappling for the Lost Cable》0.85，镜头8/11 主选 Pixabay；5/6/9/10/13 为真实缺口。
- 2026-10-22: scope added at user request: runs shown under project/piece (2.3 extended) and manual upload per segment (2.5). Waiting for confirmation.
- 2026-10-22: 2.3 and 2.5 applied.
  - API: run JSON carries `project`/`unit` labels; `POST /material-match-runs/{id}/segments/{sid}/attach` records an uploaded revision as the segment's choice (`upload.{rev}`, `uploaded: true`), references it in the project with the segment note, clears a rejection; MCP `get_material_match` returns `project`, `unit`, `chosen_uploaded`.
  - Web: run page shows 「属于 项目 · 图文」 with link; history lists all scopes with owner labels, filtered by `?project=&unit=`; 「填入这件作品的内容」 reads the piece's latest master; 「上传自己的」 dialog (source own/third-party with licence note, AI use, public use); production header 「找素材 · N」 opens the piece's searches.
  - Verified: browser — entry 「找素材 · 1」 on unit 79 → filtered list with run 11 labelled 「… · 图文」, fill-from-piece works, run page link, 上传/都不合适 on 6 segments (cover already chosen by the user). Upload → reject → attach tested on a backup copy of the DB (201/200/200, choice = upload, rejection cleared); real DB untouched. Tests `-k "mcp or material"` 152 passed; web build passes.
  - Read via MCP: the user picked a Pixabay photo for card-0 (material 122, revision 127).
- 2026-10-22: a segment can hold several materials. Upload stays available after a choice (「再上传一份」); `_pick` keeps `picked_ids` with the latest as `chosen_id`; MCP `picks` lists every accepted candidate (older runs recorded only `accepted`). Verified on run 11: cover shows 5 accepted picks (rev 124–128, chosen by the user) and 「再上传一份」.
- 2026-10-22 修复：Pixabay 候选标题（标签串）超过 200 字，确认框预填后 /accept 被参数校验拒绝（422）；前端预填时截到 200 字（MaterialMatchView.tsx）。web build 通过。
- 2026-10-22 修复：Wikimedia 下载 429。原因是请求头 User-Agent 没有联系方式，被 Wikimedia 按其 UA 政策限流；open_media.USER_AGENT 加上仓库地址后 6/6 下载成功。已重启 API，material 测试 80 通过。
