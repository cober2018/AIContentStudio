# 进度

## 2026-10-15 规范提案

已核对当前入口、API和后台订阅维护；创建proposal、design、一份capability规范、16项实施任务及持续计划。当前仅文档，产品开发0/16，正式数据、配置与服务未变更。此前每日选题change保持43/45，自然日批跟进继续按原授权执行。

规范自查、OpenSpec strict与diff空白检查通过；proposal/design/specs/tasks四项产物已齐，16项开发任务均未开始。当前交付供用户确认，尚未执行apply。

## 2026-10-15 开始apply

用户已确认开发，复用既有隔离worktree并同步六个目标文件的正式最新版本。在线SQLite与代码原件备份至 `backups/manual-sources-20261015-2bf76qck`；0产品迁移/正式数据修改，1/16。本轮未暴露代码图工具，继续限定文件读取。

## 第一批实现与隔离验证（11/16）

新增单一来源管理service，六个既有路径完成登记/配置/角色保护/后台验证/正常来源面板。复用现有字段，无迁移/新依赖/新测试文件。已有81检查通过；Web构建通过。临时隔离操作已验证重复与别名、跨owner、0/多角色、single-article候选、HTTP期间人工配置变化、画像修订保留关联、容量pending/恢复、旧PATCH兼容。独立审阅发现并关闭自动endpoint二次命中和管理JSON并发覆盖；正在复核最终修订。

当前API8018/Web5188/Redis9/受限Beat仅使用备份复制SQLite，验证与调度均独立于正式8000/5173/Redis2；原测试8017/5187未中断。正式代码、来源和今日10条尚未改动。

## 正式接入与真实后台验收

- 已在线备份最新正式SQLite及runtime.env，白名单接入6旧路径+1管理service；未迁移/新增依赖/新测试文件。API/Worker空闲检查后刷新，正式8000/5173/Redis2健康。正式manual来源0，没有把隔离验收数据加进用户来源库。
- 独立8018/5188/Redis9/SQLite通过正常页面添加Go新闻网站、角色多选与暂停/权限开关；页面转about:blank后，Beat17:41:26自然扫描→validate 17:41:32完成，自动发现公开Atom并保存10条。
- 隔离Persona4预备已完成画像研究夹具，先暂停，来源验证后恢复有效；未改时钟/业务日。Beat17:42:26自然派发当天日批Run9，Worker17:44:27完成；只使用手动来源54，5模型调用/56758预算，实际生成1条合格近期报道，不凑数。原经营角色正式下一自然日验收不由该结果代替。
- 单独将隔离source54设为已到增量采集时间以验收采集租约，Beat17:45:26自然扫描，collect 17:45:35 succeeded/new_versions=0，重复条目不增。该夹具未改正式频率。
- RSS地址重复添加立即打开已有记录，保留原角色4，未套用提交的角色3；另一网站别名后台合并后，角色3过滤下仍看到独立通知，可打开角色4的目标配置，显式保存后通知清除。
- 临时隔离验证覆盖：重复/别名/0角色、跨owner原子拒绝、旧PATCH兼容、单篇网页不误作持续来源、角色修订保留、容量等待/恢复、验证与自动探测期间真实第二session配置修改保护。
- 独立code-reviewer/Python reviewer/TypeScript reviewer通过。审查发现的最终URL命中绕过、陈旧JSON覆盖、容量竞态、发现证据flush和SQLite采集租约时间比较均已修复。现有81检查通过/1既有warning，正式Web构建与Ruff通过，strict通过。
- 正式Persona、PersonaRevision、ContentOpportunity及全部AssessmentRevision与接入前逐值一致，SQLite integrity_check=ok；七路径hash与复核版本一致。完整运行/版本证据见implementation_manifest.json及私有备份。

三类入口收口：新闻网站成功验证/真实日批消费；RSS直接重复添加准确复用；博主主页MartinFowler以0角色储备保存，后台实际返回adapter_unavailable并保留candidate，未谎报可采集。网站query别名异步合并已验证跨角色提示/打开原配置/显式保存后清除；15/16，最后同步规范与归档开放。

最终正式页面已显示添加/配置入口，0控制台错误；API健康与discovery worker_enabled=true，原5建议未变。正式来源无验收新增，博主失败候选留在隔离库。隔离Worker/Beat、API和Vite在空闲与队列为空后已停止，复制库/回执留在私有备份；未push/公开发布，复用worktree留给前一change后续验收。开始同步本capability与归档。

归档完成：16/16，CLI同步manual-discovery-source-management新增7项要求，归档至2026-10-15-add-manual-discovery-source-management；原每日选题change43/45未归档，仍等待正式下一自然日验收。
