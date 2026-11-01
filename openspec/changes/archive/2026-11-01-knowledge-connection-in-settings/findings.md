# findings

- 同一个知识库两种用途：角色风格（角色页文件夹，`speech_sample_folder`）和项目内容补充（项目「来源与证据」选用笔记）。用户确认两种都保留。
- 连接设置目前在 `apps/web/src/product/project/ObsidianKnowledgePanel.tsx` 的「管理员：本地知识库连接设置」，接口 `GET/PUT /api/v1/obsidian/connection`，本身就是全平台一份。
- 角色文件夹被名单卡住的位置：`obsidian_knowledge._sample_scope`（保存与读取）和 `read_note` 里的名单判断。
- 当前名单：`knowledge/permanent`、`自媒体/文章`。用户的知识库一级目录会不同，项目内容主要来自另一个 Agent 的固定输出目录。
- 正式设置里的知识库根目录 `/Users/mshengran/iCloud云盘（归档）/Obsidian/知识库` 在本机不存在；实际库在 `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/知识库`。连接目前读不到笔记，需用户在 设置 → 知识库 改根目录（未代改）。
- 实际库里 `自媒体/视频文案` 目前是空文件夹。
