# findings

- 卡片标签来自 content_project.status（默认 draft，仅归档时改为 archived），经 ui.tsx 通用状态表显示「草稿」。
- 作品：视频 12、文字 1、图文 1；视频链路 video_chain._state，文字/图文 article_chain._state，都有「已定稿」done 状态。
- 列表接口 GET /content-projects（list_projects）已批量取 units。
