# 流程体检与方案复核

## 2026-10-18 只读检查

代码基线：HEAD 8539806eb3a1bebf5bf71ee08df3a286cdf9e00a 加当前未提交工作区；相邻需求改动很多，未覆盖或回退。

| 检查 | 观察 | 结论 |
| --- | --- | --- |
| 正式服务 | /api/v1/health/ready 200 | API 可达 |
| 角色列表 | /api/v1/production-workspaces?workspace=persona 200；正常页面可读 | 清单读取正常 |
| 科技样片 unit13 | 脚本、3镜头、素材、47秒主稿可读 | 已有作品可继续查看 |
| 五步导航 | 选题与资料→内容方案→制作内容→审阅修改→交付 | 页面入口接通 |
| 当前制作执行 | Recipe run_id=null，阶段未开始 | 尚未验证当前任务的新执行全链 |
| 交付冻结 | channel_form_missing，未选渠道，冻结按钮不可用 | 需先选渠道并重新检查 |
| 清单管理 | 无归档/删除菜单；旧 DELETE 语义随历史变化 | 本方案新增显式操作 |

归档文档记载以往 Persona 与多形态交付验收通过，本轮仅交叉参考，未重新调用模型、试听音频、生成视频或发布内容。结论是主流程可按步骤使用，但当前样片有明确配置阻塞，不能声称本轮已完成新任务端到端验收。

本轮不改业务代码、不改正式数据。新增能力待确认及实施，未归档。

## 2026-10-18 实施验收

- 用户已确认执行，业务实现与加法迁移已加载本机正式 API；使用独立生命周期 active/archived/deleted，原制作状态不改。
- 备份：`backups/persona-list-lifecycle-20261018-194534/`，包括初始数据库、迁移前二次快照、业务源文件及受保护的 runtime.env。两次 SQLite 备份及迁移后 integrity_check=ok。
- 正式 106 张旧业务表逐行旧字段对比：105 张完全相同；system_settings 仅后台 discovery.heartbeat/discovery.catchup_clock 正常更新。40 单元全部 active，原 status/主稿/素材/Run/身份历史不改。
- 原列保全，新增 unitlife000001；runtime.env 仅 REQUIRED_SCHEMA_HEAD 从 productdomain0001 更新。API 与空闲 Worker 通过现有 launchd 重载，Beat/队列配置保持。
- 既有检查：核心项目/审阅/Recipe 102 通过；首页/音频 129 通过；共 231 项。Web 构建、TypeScript、bundle预算、diff whitespace 与 OpenSpec strict 通过。未新增测试代码。
- 在正式备份的隔离副本：archive/restore/delete 及重复请求 200；归档后 Recipe readonly=true、编辑409；删除从全部清单隐藏，历史GET200、写入及旧DELETE409；主稿/素材/执行/Run行完全保留；unknown及运行中任务409，非所有者404，viewer403，旧身份/归档恢复409。
- 页面：正式5173可见“更多→归档/删除”；隔离5197点击归档后2条→1条，勾选包含归档历史显示归档只读，点击恢复后提示恢复成功并回到继续创作。没有对正式作品执行归档或删除。删除确认与接口已检查，未在正式页面提交删除。
- 审查曾发现首页待办与知识上下文漏检生命周期，已修复并静态复核通过；隔离运行发现审计事件未注册，已修复；音频查询行改为显式读取生命周期。前端复核通过。旧归档无变化的恢复请求调整为明确409。
- 正式健康回读ready=true；角色API正常返回生命周期。隔离验收服务已关闭。

代码基线、范围与散列见 implementation_manifest.json；未提交、未push、未公开发布。新功能验收不替代角色内容新任务的全链生成验收，也不关闭相邻每日选题自然批验收。

最终Python复核通过，未发现阻断问题；核心F821/F822/F823/E9检查通过。最后正式健康HTTP200，ready/schema/worker均true。
