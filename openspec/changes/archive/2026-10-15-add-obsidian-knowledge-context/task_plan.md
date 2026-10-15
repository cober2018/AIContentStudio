# Obsidian Knowledge Context Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans after explicit proposal confirmation, task by task. Root owns formal page/config/data writes; do not delegate implementation without session authority. A single read-only plan review is required by writing-plans. User instructions override default plan location and new-test generation.

**Goal:** 用户在“来源与证据”检索Obsidian，选择专业内容和本人风格样本，正常创作出有依据且符合本人表达的新稿。

**Architecture:** 一个本地只读Markdown接入，复用SourceDocument及项目上下文/现有权限；新知识用途和模型授权须精确版本化。优先沿用已有Run snapshot，明确选择再送模型；不实现平行MCP路径。

**Tech Stack:** 现有FastAPI/SQLAlchemy/SQLite、React、Python本地文件读取、已有生成供应商。MCP/CLI/向量服务均非依赖。

---

## Task 1 — Scope and persistence decision

**Files:** 本目录已有spec/design/tasks，`apps/api/app/models.py`、`apps/api/app/services/stage_resolver.py`、`apps/api/app/routers/content_projects.py`只读确权；如确需加法迁移，先核实`apps/api/alembic/versions/`目录并回写其确切文件名，不先写schema。

- [x] /// Obtain confirmation for the recommended vault adapter and intended folder scope before apply; inspect working-tree changes and preserve hashes.
- [x] /// After scope confirmation but before apply, inspect existing project/source and invocation snapshot contracts; choose reuse or a single minimal ProjectKnowledgeContextRevision model; record exact owned files and update this plan/design before any implementation write.
- [x] /// Back up formal data/config only when actual implementation requires writes; do not scan note bodies during planning.

## Task 2 — Bounded read-only connector and normal project picker

**Files:** 新增仅本连接服务`apps/api/app/services/obsidian_knowledge.py`（先确认父目录）；优先扩展`apps/api/app/routers/content_projects.py`现有项目授权路由、`apps/web/src/product/project/ProjectEvidenceTab.tsx`现有入口；连接配置复用产品设置现有backend/UI；只有必要时触及`apps/api/app/services/data_source_plugins.py`，不得让旧workflow声明连接后仍无执行器。正式可写文件集合须在Task1确认后记录，保全其相邻已有diff。

- [x] /// Implement administrator-configured vault/folder access; search saved Markdown titles/content and return bounded snippets; preview only an explicitly selected in-scope note.
- [x] /// Reject out-of-scope real paths; skip hidden/configuration/non-Markdown files; show unavailable files honestly; never write vault content.
- [x] /// Add the sources/evidence selection panel: search, preview, choose excerpts, assign professional/style/both and intended Persona/unit scope, explicit model-use grant.
- [x] /// Save chosen Source content with note provenance/checksum and versioned project purposes; no unselected import, no automatic FactPack promotion, no duplicate content for repeated unchanged selection.

## Task 3 — Actual manuscript context

**Files:** `apps/api/app/services/stage_resolver.py`和必要的现有stage invocation/context构造路径；实现前以MCP图工具优先，未提供时仅查这些相关调用，回写确切最小文件，不改量化专用domain_knowledge.py或无关模型adapter。

- [x] /// Resolve only allowed selected excerpts; put professional and style sections into visible actual-request preview and relevant manuscript stages.
- [x] /// Freeze source versions, purposes and permissions in the existing run snapshot; explicit new selection creates later revision, not a rewrite of old run content.
- [x] /// Verify no-knowledge behavior and current fact/evidence/permission gates stay intact; notes are reference data, not executable instructions.

## Task 4 — Verify, demonstrate and close

**Files:** 本目录同一套文档；必要时根README仅本需求增量。既有相关tests/构建配置只读，本轮不写新的持久测试或示例代码。

- [x] /// Run existing relevant checks plus bounded manual path/scope/reload/currentness checks; independently review the exact code changes. Never claim OpenSpec strict as functional proof.
- [x] /// After explicit scope authority, select actual notes in normal pages for both Personas; use a small bounded real manuscript run and inspect actual inputs, outputs and style correspondence. Do not promise style matching from installation alone.
- [x] /// Verify vault content unchanged, old data and adjacent work preserved; update README/progress/findings/review and exact source/version evidence.
- [x] /// Strict validate, sync/ archive only this new change, whitelist local commit; no push/publication.

## Approval boundary

用户已明确确认本地只读方案，随后完成apply；沿用本需求14项任务与已确认有界模型批次，不重复确认。

## Confirmed implementation contract — 2026-10-15
用户已明确确认“只用连接本地”。已在apply前只读确认：ContentProject无知识字段，ProjectSourceBinding.note不是版本化授权合同；新增一张ProjectKnowledgeContextRevision最小修订表。Run使用既有WorkflowRun.context_json固定选择，Stage沿用input_snapshot_json记录实际输入。配置仅SystemSetting key obsidian_local_v1，项目知识不放SystemSetting。

确切源码白名单：apps/api/app/models.py（仅新增表class）、apps/api/alembic/versions/obsidian000001_project_knowledge_context.py（新增）、apps/api/app/services/obsidian_knowledge.py（新增）、apps/api/app/routers/obsidian_knowledge.py（新增）、apps/api/app/main.py（注册新路由）、apps/api/app/services/creation_recipes.py、apps/api/app/services/workflow_engine.py、apps/api/app/services/stage_resolver.py、apps/web/src/product/project/ObsidianKnowledgePanel.tsx（新增）、apps/web/src/product/project/ProjectEvidenceTab.tsx（接入panel）。配置入口放在该知识库面板的管理员折叠区域；不改无关产品设置或启用尚无执行器的旧Data Node占位。

边界：同一Vault默认已配置根目录内Markdown，管理员可收窄子目录；search最多返回20项并明确扫描覆盖/异常，单笔记至多256KiB，每项目修订最多5个选中笔记，单片段4000字/总6000字，页面明示。项目/Persona或Unit范围与允许模型使用明确保存，默认false。导入Source只保存所选片段，不读取未选附件或递归双链；原笔记SHA与片段SHA分开保存。两个角色各一次短稿实际生成，总注册模型派发上限4（每角色draft+refine），语义QC如触发另最多4，总8；串行/两次顶层派发起始≥10秒/Unknown不重发，预算与价格未知不当成零。

隔离工作区/分支：/Users/mshengran/.codex/worktrees/obsidian-knowledge/AIContentStudio，codex/obsidian-knowledge-context。配套私有备份为backups/obsidian-knowledge-20261015.olyuf7ao；969旧行/75旧media/477归档文件及75相邻文件已指纹保全，SQLite backup integrity ok。正式笔记只读，模型生成只由根正常页明确选用并授权后执行。

必要第11文件apps/api/app/db.py已纳入白名单：本地批准schema head和migration_only同步；实际runtime.env明确固定旧schema head，正式迁移后仅更新REQUIRED_SCHEMA_HEAD=obsidian000001，其余配置原字节保持。
