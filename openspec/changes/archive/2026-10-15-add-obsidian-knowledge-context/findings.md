# Findings

- 已有system-assets-knowledge规范明确KnowledgeCollection组织Source/FactPack引用，不等于Fact Boundary，Source级公开权利仍not_decided；不能把个人历史文章一律塞进事实包。
- `data_source_plugins.py`的Obsidian key只是available=false占位；`ProjectEvidenceTab.tsx`是“来源与证据”正常入口，已有文本/URL/文件及既有Source引用。
- 本机Obsidian注册表显示一个名为“知识库”的已打开Vault，目录存在。只读取了注册表和安装包版本元数据，未遍历或读取笔记正文。磁盘版1.11.7，PATH无obsidian CLI；官方CLI文档要求1.12安装包。当前无必要为了读Markdown升级应用。
- 插件目录搜索Obsidian未返回可用插件；这仅说明当前插件目录结果，不代表社区没有MCP。社区Local REST API项目维护者文档实际提供MCP及检索/读写，不能误称Obsidian内置官方MCP。
- 官方数据文档确认Vault是本地Markdown文件目录；本机AIContentStudio接只读文件已足够支撑本次检索与选用；装在外部客户端的MCP不会自动接入Web页面/生成请求。
- 技术接通、知识选用和风格参考是三个验收点。风格参照是上下文提示，不是模型微调或承诺绝对一致；验收须实际对稿。
- 当前工具清单未提供代码图MCP，已按不足fallback仅读取指定知识/来源/阶段文件，未全库扫描。
- 本change独立于前三个已归档交付，不重开旧change；工作区已有相邻dirty源文件，实施必须先确权保全。

实施确认：新增一张project_knowledge_context_revision，使用现有WorkflowRun.context_json固定和Stage.input_snapshot_json回执；db.py须同步本地批准head obsidian000001并将新表列入migration_only，避免启动自动建表。实际runtime.env固定旧head，因此正式迁移时仅更新REQUIRED_SCHEMA_HEAD=obsidian000001，其余配置不变。旧Data Node Obsidian占位不假称可执行，本次独立本地面板真实连接。知识正文在解析快照出现多次，预算6000中文字已由评阅在128KiB解析及invocation封装下实核通过。

实际产品验证：连接范围knowledge/permanent与自媒体/文章，本次搜索读取72篇的本地有界匹配，未把搜索结果全部导入或发送模型。仅选择三篇笔记的必要连续片段：科技交接点164字、生活质量边界90字、共享风格455字；风格Source5在两个项目去重复用，各自范围与授权独立。两个项目均为明确假想/个人感悟（reflection），未将知识提升为FactPack或声称当前技术主张已核验。正常“直接生成候选”流程以两次独立Run完成初稿→基于已接受Master精修，不修改Persona默认九阶段流程。四请求快照约64–87KB，输入已查实。
