# 实施计划

1. 读 `routers/content_projects.py` 的 create_project / brief revisions / create_unit，把可复用部分抽成服务函数或直接调用（只做必要抽取）。
2. `services/creative_mcp.py`：TOOLS 加 3 项、`_execute` 分发、输入校验（选题理由必填、链接 ≤10 条且为 http(s)）。
3. `ProjectBriefTab.tsx`：识别 references 里第三方模型标记，显示标签、理由、链接。
4. 更新 skill 文档，验证，回写 progress / README。
