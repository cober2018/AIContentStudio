# 停机补偿：先补采，再生成当天选题

## PRD / 需求背景

本机不能全天在线。恢复运行后自动补采停机期间的信息，再生成当天选题；补不到的来源、区间和原因明确显示。

## 当前阶段与代码位置

`IMPLEMENTED_ACCEPTED`，19/19，用户确认后的开发、隔离真实停启及正式恢复验收完成。正式工作区`/Users/mshengran/Project/AIContentStudio`，main@49e4fdc上的本次10个代码路径尚未提交，保留全部相邻修改；准确hash见implementation_manifest.json。开发隔离worktree `/private/tmp/aicontent-offline-catchup` 完成回执保存后清理。

## 目录结构

- [proposal.md](proposal.md)：需求范围。
- [design.md](design.md)：流程图、规则、预算、数据和页面。
- [specs/discovery-offline-catchup/spec.md](specs/discovery-offline-catchup/spec.md)：验收行为合同。
- tasks.md / task_plan.md：任务与持续计划。
- progress.md / findings.md / review.md：实际进展、发现与自审。

## 已完成

先补采后生成、页级断点、10请求/300条和后台运行15分钟预算、部分覆盖及原页签展示均已接入正式5173/8000/Redis2。41项既有检查、Web/bundle、Ruff和独立复核通过；受控Beat/Worker生成1条常青选题，回执先于证据冻结；第一页后实际停机并续跑至第三页，未重跑当天选题。

正式两次自然恢复批次均结案partial：首轮10个covered、11个partial、26个excluded；第二轮11/10/26。partial表示有明确历史缺口，不是任务仍中断。API健康、schema catchup000001、数据库完整性与保护表逐值核对通过；两个角色、今日10条机会及评估、已有创作记录保全。完整证据见progress/review/implementation_manifest及私有备份`backups/offline-catchup-20261015-_ow9lrpu/`，没有混入隔离角色或夹具来源。

## 待完成 / TODO

本需求19/19已验收归档，8项要求同步至`openspec/specs/discovery-offline-catchup/spec.md`。原`add-daily-persona-content-opportunities`的次日自然日批9.5与9.6仍独立等待；本次停启验收不能替代它。不承诺恢复公开入口已删除/下榜内容，缺口与未知数量持续展示。

## 关键设计决策

先补采结案再冻结证据；不能完整回溯时标记缺口，用成功资料生成0至5条。默认每源10请求/300条、等待累计后台运行15分钟。已完成日批不重跑，已开始模型阶段保留快照与unknown约束。完整只指公开入口的可证明连续覆盖。

## 依赖与启动方式

沿用现有API/Celery/Beat/Redis/Web，无新供应商或运行依赖。加法迁移仅新增两表，REQUIRED_SCHEMA_HEAD由discovery000001同步为catchup000001，其余runtime.env配置原样保留。正式仍由原launchd API/solo Worker+Beat运行，用户无需开网页；电脑和后台恢复后自动推进。备份含升级前数据库、9路径原件和runtime.env；回退保留新增回执，不执行删除历史的降级。

本轮实际技能：`using-superpowers`、`using-git-worktrees`、`executing-plans`、`openspec-apply-change`、`requesting-code-review`、`systematic-debugging`、`finishing-a-development-branch`、`openspec-archive-change`。没有新建测试文件、push或公开发布。
