# 进展

- 2026-11-01：方案已写，等待用户确认。
- 2026-11-01：已实施。
  - `services/creative_mcp.py`：`list_personas`（只读）、`create_project`、`create_unit`，直接调用 `routers/content_projects` 的建项目、建简报、建作品；选题理由与参考链接写进第 1 版简报 `references`（kind `third_party_model_topic`）。
  - `web/.../project/ProjectBriefTab.tsx` + `types.ts`：简报区显示「由第三方模型创建」、选题理由、参考链接（有才显示）。
  - Skill：`video-production-handoff`、`article-writing` 加「先 list_personas → create_project → create_unit」。
  - 测试名单：`tests/test_aco_creative_mcp.py` 的工具白名单和只读名单加上新工具。
- 验证：经真实 stdio MCP 通道调用——list_personas 返回 4 个角色、14 个渠道；create_project 建出项目 45（简报第 1 版，无链接）；缺选题理由返回 `rationale missing` 且不建项目；create_unit 在项目 45 建出视频作品 86（角色 3）；随后 get_video_brief(45, 86) 正常返回「待开始」。非 http(s) 链接被拒。相关测试 1104 passed；tsc 通过；API 已重启。
- 待办：用户在页面看项目 45 的简报区后，归档测试项目 45。
