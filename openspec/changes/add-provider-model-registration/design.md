## Context

真实基线 main@da73bbb，加未提交 F7/模型能力路由改动。当前模型配置在 SystemSetting(models)，默认在旧 llm 覆盖/env；purpose routes 包括 generate/rewrite/fact_check/topic_discovery/discoverability/platform_adaptation，text_master_edit 继承 rewrite。新能力配置已有 revision CAS，绑定只允许 HTTPS，不能直接接收用户提供的局域网 HTTP 网关。不得使用旧无版本 writer 覆盖 schema v2。

## Goals / Non-Goals

Goals：实现“厂商登记 → 获取模型 → 选择注册 → 默认/环节路由 → 实际消费者按选择执行”闭环。CPA 注册三个用户指定模型，Gemini 为全局默认；保留显式场景选择。

Non-Goals：不实现新的原厂生成协议，不凭模型名称启用媒体能力，不新增表/迁移，不迁移历史 Run，不自动调用付费模型，不重试微信 Unknown，不处理 Commons。

## Decisions

1. 推荐扩展现有 Settings/SystemSetting；不另建独立注册库，也不只修改 env 而让前端缺入口。providers 以稳定 provider_id 保存名称、协议、base_url、启用状态和内部 credential；注册 profile 绑定 provider_id + exact model_id。所有保存同一 models revision CAS，保留既有字段。读取只回 configured/掩码；空白密钥表示保持，清除必须显式操作。复用现有服务端密钥存储边界，不能声称现有数据库明文已加密；生产 secret vault/加密策略属于后续安全收口。
2. 默认 OpenAI-compatible chat 协议。获取模型由服务器向该厂商的 /models 发起只读认证 GET，限时/限量/限响应字节，不跟随重定向，不返回原始错误或 header。返回 ID 列表，仅用户选中并显式保存后登记。失败不删除已有模型、不自动改默认；可手动补录准确 ID。
3. HTTPS 保持默认。CPA 的 HTTP + 非标准端口仅通过管理员显式确认可信局域网的精确 scheme/host/port/path allowlist 接受，凭据仅发往该 endpoint。不能全局开启 ssrf_allow_private；拒绝 URL userinfo/query/fragment、回环/链路本地/云 metadata 和未授权目标。HTTP 风险在保存前显示；发现与调用复用相同目标校验，DNS/连接目标必须一致。媒体下载及 native media bindings 不因此放宽。
4. 引用优先级：显式受支持任务/节点选择 > 已保存功能路由 > 全局 default_profile > 无新默认时原 legacy llm/env。disabled/deleted/missing/能力不匹配的显式选择返回原因，不能静默换模型。将新的默认设为 Gemini 不覆盖现有显式 routes。text_master_edit 保留 rewrite 兼容继承；前端列出真实消费者清单，不虚构尚未接入的功能。
5. 路由 UI 首批覆盖当前六类 purpose 加 text_master_edit，按实际消费者识别标签。Workflow 已有节点选择复用已注册模型目录；生成图片/视频/语音由既有 capability routing 和插件选择处理，不把 chat 默认自动当媒体 executor。运行冻结所选 profile/model/配置版本，不回写历史。
6. 页面流程：厂商卡片登记协议、API、密钥 → 获取模型列表 → 勾选注册/手动新增 → 设默认 → 功能模型下拉。只读用户可看安全配置，编辑/发现按服务端权限。409 保留草稿；切换用户清空密钥输入与异步结果；Settings lazy 性能不退化。

## Risks / Trade-offs

- HTTP 会明文传输密钥 → 仅用户明确的可信局域网 endpoint，并提示风险，生产优先 HTTPS。
- /models 缺失或包含别名 → 手动准确 ID 补录，不冒充真实可执行验证。
- 既有 secret 存储非 vault → 明确边界，严禁源代码/日志/文档泄漏；不借本任务未经批准扩大持久模型。
- 并发多个配置入口 → 共用 revision CAS、提交后刷新进程缓存；失败不部分更新默认或密钥。

## Migration Plan

无需 DB migration。增量扩展配置 envelope；旧 profile/route 与 llm/env 保持可读。只在用户显式保存后改变默认。回退不删除注册数据；不恢复旧整份 JSON 覆盖当前配置。

## Open Questions

方案及 apply 待用户确认。CPA /models 实际可用性尚未验证，密钥未读取或写入配置；模型能力除默认聊天意图外不推断。首次真实生成的额度与测试内容另行授权。
