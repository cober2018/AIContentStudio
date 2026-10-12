# Capability Memory 与 Learning 显式桥接实施计划

> Execute the approved align-creative-orchestration-product change using executing-plans / subagent-driven-development. No new persistence, formal migration, commits or external calls.

## 目标

完成 10.1–10.16、11.1–11.4、11.6–11.7，并验证 8.5 的 MCP 发现/使用。11.5 只在已有真实重复编辑证据足够时实施，不用 execution 接受冒充编辑。

沿用现有 CapabilityArtifact/Revision/Use 三表，零新增表/迁移。方法只返回给用户/Agent，不执行后端动态代码，不自动注入模型/正文。普通发现仅 saved/pinned；所有适用范围同时返回，不合并、不挑赢家。

## 文件边界

- 后端 worker：新增 services/capability_memory.py（必要时拆 contracts）、routers/capability_memory.py，严格领域服务/API。禁止编辑 models、migration、MCP、creative router、前端。
- 前端 worker：新增 product/CapabilityMemoryPanel.tsx（可拆 types）；修改 ProductSettingsPage/ProductionWorkspace/LearningWorkspace 的 lazy 管理、上下文发现和桥接。禁止编辑后端、CreativeExecutionPanel、bundle 脚本、根 README。
- 主 agent：router 注册、MCP find/use、成果接受可选 reusable artifact 捕获接线、隔离验收与记录。

## 共用契约

API `/api/v1/capability-memory`。content 为 bounded JSON 方法定义，正常表单写 `{text,tags}`。args_schema 是受限 JSON Schema object：string/number/integer/boolean、required、有限 enum；拒绝 refs/动态执行。`{{arg}}` 仅确定性文本替换。工具定义可描述外部工具，后端不执行。

- `GET /`：owned 管理页 status/kind/q/tag/limit/offset；`{items,total,limit,offset}`。
- `GET /discover`：project_id+unit_id，可选 execution_id；相同页结构，每项 matched_scope/exact revision，saved/pinned only。
- `POST /`：`{kind,name,content,args_schema?,scope_type?,scope?}`，只 candidate。
- `GET /{id}`、`GET /{id}/revisions`：同 owner 详情/历史，历史 `{items}`。
- `POST /{id}/revisions`：`{expected_revision,content,args_schema}`，append-only/CAS。
- `POST /{id}/lifecycle`：`{expected_revision,status,scope_type?,scope?,confirm_scope_broadening?}`。禁止 content；scope/元数据变化以新 revision 冻结，promotion 不替换 content。
- `POST /{id}/use`：`{artifact_revision_id,arguments,project_id?,unit_id?,execution_id?}`；精确适用范围，返回 `{use_id,artifact_revision_id,content_hash,rendered_content,rendered_arguments_hash}`。
- `POST /uses/{id}/outcome`：`{outcome,expected_outcome}`，used/accepted/rejected/unknown，CAS 防观察覆盖，不改业务对象。
- `GET /uses/{id}`：只读回读同 owner 的精确历史使用及当前结果；409 后用户明确核对，才采用新的 CAS 基线。方法归档/修订禁止新使用，但不禁止原使用记录的结果观察。
- `POST /capture-execution`：`{execution_id,kind,name,content,args_schema?}`；整单 accepted+frozen required roles/exact package，project narrow scope，幂等去重。
- `POST /capture-learning`：`{learning_candidate_id,expected_learning_revision,kind,name,content,args_schema?}`；accepted+trusted frozen decision/support evidence，冻结安全 refs，只 candidate。
- `GET /{id}/export`、`POST /import`：versioned safe document，导入新 local id/candidate；重新鉴权/扫描，不复制 owner/status/source provenance。

公共详情：root `id/kind/name/status/scope_type/scope/source_kind=capability_memory`；`current_revision={id,revision_no,content,args_schema,content_hash,metadata,source_execution_id,source_learning_candidate_id}`；usage `{use_count,last_used}`。scope 形状：ID 范围 `{id}`，channel `{channel_id}`，executor `{executor_kind,executor_key,executor_version}`，owner 默认当前用户。真实 pinned IdentitySnapshot/unit channel 决定适用性，不信任客户端 persona/account claims。

供主 agent/MCP 调用：`discover(db,user,data)`、`use_artifact(db,user,artifact_id,data)`、`capture_execution(db,user,data)`，普通 API 共用，不造第二套鉴权。

## 步骤 ///

/// 1. 隔离 RED：当前 capability route 缺失、MCP find unavailable；计划独立复核后改代码。保留 F8 哈希与正式库基线。

/// 2. 并行领域/页面：生命周期、历史 CAS、secret/JSON/args bounds、所有适用 scope、角色/归档鉴权；lazy 管理/显式复用。Installed Skills 仍是旧外部 inventory，区分 source_kind/稳定 id，不改 skills_enabled。

/// 3. 捕获与 Learning：整单 accepted 才 capture，必需输出不齐/拒绝不能捕获；capture 失败不回滚已接受成果。Learning 仅独立动作，冻结证据，保持 ContentMemory/Identity/Fact/Workflow 不变。

/// 4. 接线：注册 router；MCP find/use 共用 owned services/响应边界。不会新增 approve/save/publish 能力。成果 decision 可带 reusable_artifact，主决策完成后再单独捕获；失败只返回安全 capture 结果。

/// 5. 临时 API 回归：六类 kind、CAS 200/409、历史 hash、broaden confirmation、sibling/project 隔离、archive/deprecate、forge/import/secret/credential URL/非有限/超界/动态 payload、multi-output accepted capture 去重、Learning refs、不改业务、exact use/outcome/计数、MCP。

/// 6. 临时浏览器：候选→保存/固定→刷新历史；项目发现→明确选择/参数→渲染/usage，不改正文；accepted Learning→candidate；viewer 只读；409 保留本地内容；lazy/budget。

/// 7. 现有 suite/build/budget/strict/Ruff/diff/F8 hash；先 SPEC 再代码/安全独立复核，修复实际问题后重验。按实测勾任务，更新 change README/progress/findings/验收。

## 验证与边界

不新增永久测试，使用现有 suite 与临时内联检查。所有写入只到 `/tmp` 隔离 SQLite/素材；不真实付费/发布。跨进程 DB write lock/CAS，不用进程内锁冒充去重；失败 rollback。范围 metadata/hash 和旧 revision 保持可追溯。

字符串上限为 8192 UTF-8 字节；方法/参数 schema 与渲染文档总量上限 64 KiB，两者分别校验，不能让合法最大正文被 JSON 包装开销卡死。嵌套文本和键 NFC 规范化后保存/哈希，键规范化冲突拒绝。普通发现分页最多 20；所有适用结果可继续分页，不把第一页排序当默认优先级。历史方法修订仍只读，新使用须当前修订。

F8 13 文件以 `/tmp/aics-f8-before-align-creative.sha256` 校验。正式 storage/credentials/schema、skills_enabled 不变，不 commit/push/deploy/archive/canonical sync。11.5、真实 Codex/Claude 专业执行恢复、Director/Legacy 退场仍未终验，不把本批当整个 change 完成。
