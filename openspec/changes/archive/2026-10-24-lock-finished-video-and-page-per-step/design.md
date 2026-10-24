## 现状

- 视频进度 `video_chain.state()` 从最新主稿往回找导演稿（`draft_root`），跳过视频链自己写的「保留画面」修订（配音、选素材、剪辑准备）。页面「保存当前主稿」写的修订没有这些标记，就被当成新导演稿，状态回到 `not_started`。
- 所有主稿保存都走 `content_masters.save_revision`。
- 角色视频的页面步骤在 `ProductionWorkspace.tsx`：选题与资料 / 内容方案 / 制作内容 / 审阅修改 / 交付。「内容方案」页显示导演稿（`CreationRecipePanel` simple 模式内嵌 `VideoChainPanel showDraft`）；「制作内容」页显示 `ContentMasterPanel` simple 视图，里面视频进度、分镜表、配音、导演包等全部平铺。

## 决定

### 1. 同内容不算新稿
`_keeps_draft(master)` 增加一条：`master.payload_hash` 等于父修订的 `payload_hash` 时视为保留画面。`draft_root` 因此越过 v24、v25 回到原导演稿，海底光缆恢复「已完成」。不删、不改已有修订。

页面：`ContentMasterPanel` 的「保存当前主稿」在 `dirty` 为假时禁用。

### 2. 锁定与重新打开
- `video_chain.locked(db, unit_id) -> bool`：状态为 `done` 且最后一次成片通过之后没有「重新打开」记录。
- `save_revision` 开头：视频单元且 `locked` 时拒绝，`409 video_chain_locked`「成片已完成，先在成片页点『重新打开』」。视频链在成片通过时自己的写入（接受产物）不新建主稿修订，不受影响。
- 重新打开：`POST /content-projects/{p}/units/{u}/video-chain/reopen`，在视频链记录里追加 `{"stage": "reopen", "target_id": 成片任务 id, by, at}`。之后状态仍显示「已完成 · 已重新打开」，直到 Claude Code 保存新导演稿，流程按现有逻辑从导演稿开始。
- `state()` 返回 `locked: true/false`，页面据此只读。

### 3. 角色视频一步一页
只改角色视频（`simpleVideo`）；商品视频、文字、图文保持原样。

| 步骤 id | 名称 | 页内容 |
|---|---|---|
| goal | 选题与资料 | 不变 |
| plan | 导演稿 | 视频进度（导演稿段）+ 逐镜分镜；「更多」里放流程细节、主稿版本、分镜素材制作、导演包、保存主稿 |
| sample | 小样 | 小样播放、按秒意见、通过；配音面板 |
| final | 成片 | 成片播放、意见、通过；完成后「重新打开」 |
| delivery | 交付 | 不变 |

- 沿用现有步骤导航与底部「上一步 / 下一步」。`workstep` 没指定时，按 `video_chain.state` 落到当前步骤（draft_* → plan，making/sample_* → sample，finishing/final_*/done → final）。
- 当前步骤之后的页面只显示「还没到这一步」；之前的页面只读回看（看导演稿、看小样）。
- 旧链接 `workstep=make` / `review` 分别映射到 sample / final。
- `VideoChainPanel` 加 `step` 参数，只渲染对应段落。
- `StoryboardTable` 在只读时加逐镜模式：一次一个镜头卡片，「上一镜 / 下一镜」和镜头编号条。

## 不做
- 不改数据库表结构；不清理 v24、v25。
- 不做桌面端；页面按一步一页组织，以后搬到桌面端时结构可直接沿用。
