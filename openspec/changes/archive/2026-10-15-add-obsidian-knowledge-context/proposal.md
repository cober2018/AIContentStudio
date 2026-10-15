## Why

创作原稿需要参考用户自己的专业知识和历史作品。当前“来源与证据”只支持文本、URL、文件与已有Source，Obsidian插件仅声明未连接，无法在正常页面检索Vault或把选择的个人作品带入创作。

## What Changes

- 在现有“来源与证据”加入Obsidian知识库搜索、预览及明确选用入口；先以本机指定Vault的只读Markdown接入完成需求。
- 笔记分别选作专业内容参考、个人风格样本，或同时使用。只带入用户确认的笔记与片段，并保存版本和来源。
- 专业内容参考辅助理解；可核验事实继续经过现有确认/FactPack边界。风格样本辅助表达，不自动成为事实证据。
- 文字流程的预览、生成、精修使用同一明确选定的知识上下文快照；历史结果不随Vault编辑自动改变。
- 本批不安装MCP、不升级Obsidian、不写回Vault、不做全库自动同步或付费向量索引。MCP可作为以后独立选择的接入方式，本次不同时建设两个适配器。

## Capabilities

### New Capabilities
- `obsidian-knowledge-context`: 只读Vault检索、笔记用途选择、版本化创作上下文及正常页面验收。

### Modified Capabilities
无。复用system-assets-knowledge既有Source/KnowledgeCollection和显式Fact Boundary语义；本提案不改变这些既有要求。

## Impact

涉及项目“来源与证据”、本机Vault读取适配器、已选笔记快照持久化和文字阶段上下文。复用现有Source、项目权限及提示预览；若既有持久化合同无法记录独立的用途/模型使用授权，则只新增最小的版本化项目知识上下文。最少变更文件在task_plan列出，实施前核实schema。无云端知识库、公开发布、模型微调或Obsidian笔记修改。
