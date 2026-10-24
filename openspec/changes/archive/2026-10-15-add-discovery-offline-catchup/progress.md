# 进度

## 2026-10-15 规范提案

`SPEC_DRAFT_FOR_REVIEW`，业务实施0/19。用户明确要求先出OpenSpec，不直接开发。

已完成当前代码路径核对、proposal/design/单一capability规范/tasks及持续计划、发现、自审记录。明确先补采后日批、历史能力与缺口、预算、重复重启及跨日行为。

未改业务代码、数据库、服务配置和现有选题；未触发采集或模型调用。工作区大量既有未提交改动不是本轮成果。

校验：`openspec validate add-discovery-offline-catchup --strict`通过；status四份制品均done，19项实施任务全部未勾选。文档齐备不代表功能已实现或用户已批准。当前Git基线main@636d60e。

已提交用户确认；确认后沿用同一清单实施、验收与归档。原日批自然验收保持独立进度。

## 开始apply

用户确认后已在线备份98表1398行，integrity_check=ok；9个涉及代码原件和hash已保存。实际当前HEAD为49e4fdc（前一提案的636d60e已过时），隔离worktree位于/private/tmp/aicontent-offline-catchup，并同步正式当前源码，原修改保全。备份目录`/Users/mshengran/Project/AIContentStudio/backups/offline-catchup-20261015-_ow9lrpu`。1/19。

## 隔离实施与首次检查

已在隔离worktree实现两表、加法迁移、分源分页进度/预算、daily/bootstrap门槛、覆盖API与原页签展示。37项相关既有检查通过，Web构建/bundle和定向Ruff通过。独立复核发现并修复等待预算后依赖漂移、模型开始前中断误用旧快照及后续补采提示遗漏，正在复核。真实Beat/Worker仅用复制库与Redis10，来源夹具为localhost，不写正式库；自然扫描缩短至10秒用于验收。

当前14/19：迁移副本97张原业务表逐值一致，head catchup000001、integrity ok。受控分页来源真实Beat/Worker读取87条（85篇新资料加2条边界版本），三页结案covered；无历史来源partial。Run9的选题快照11:02:45.665Z晚于两源结案11:02:45.637Z，真实模型阶段已开始，正在等完成。夹具逻辑80端口经仅验收进程映射至8029；产品URL/SSRF规则未修改。首次错误端口场景与模型账本独立保留，不重发未知调用。

## 隔离验收与独立复核通过（17/19）

41项相关既有检查通过，1项既有Starlette警告；Ruff与Web/bundle通过。真实模型5次调用生成1条常青选题，Run9覆盖快照partial；两源回执均先于证据冻结。实际停止Worker于source56第一页提交后，重启自然继续至3页/87版本；下一窗口0新增，今日仍1条且模型调用保持5次。

受控场景通过：300条上限、循环页、日期未知、304、HTTP失败、采集中撤权、预算结案、模型前重新补采、unknown与后续补采提示、跨日daily/bootstrap。页面研究记录实际展示失败原因和未确认区间，后续来源成功没有改写旧快照。夹具与传输映射仅在隔离环境，不能冒充真实站点历史兼容性。

独立code-reviewer两轮发现并关闭：超时依赖漂移、模型前恢复快照、迟到补采提示、旧事件缓存撤权和bootstrap跨日；最终APPROVE。未新建测试文件。开始正式接入前最新备份与空闲核对。

## 正式接入与恢复验收（18/19）

接入前再备份before-formal-integration.db、runtime.env，原9路径hash逐项匹配。仅接入8个旧路径及2个新路径；加表迁移catchup000001，原97张业务表迁移演练逐值保全。运行配置仅同步REQUIRED_SCHEMA_HEAD；正式8000/5173/Redis2恢复且health.ready/schema均true。

正式Beat在页面未打开时自动创建批次1，11:14:27Z全部结案：10个covered、11个partial、26个excluded；空闲刷新后批次2于11:17:27Z结案11/10/26。缺少公开历史、日期或达到上限如实partial；未验证/未授权来源excluded，0请求。新边界已在前300条核对时不因还存在更老内容而误报上限；无法解析的原始条目仍阻止完整覆盖，受控HTTP场景复验通过。

正式API/正常页签实际回读区间、计数、缺口原因与未知数量，截图formal-recovery-ui.jpg已保存在私有备份。两角色、今日10条机会、评估修订和creative_execution与升级前逐值一致；未新增正式选题或验收角色。正式下一自然日批独立等待，不回填今日旧任务快照。最终准确hash、版本和回执见implementation_manifest.json；代码未提交、未push。

待最后同步主规范和归档；隔离数据库、来源输入、Worker日志、模型账本和UI回执已在线复制到备份，临时服务随后关闭。

## 归档完成（19/19）

CLI已将8项要求同步至`openspec/specs/discovery-offline-catchup/spec.md`，并归档到`2026-10-15-add-discovery-offline-catchup`。19项清单全部完成。临时Worker/Beat、来源HTTP、API8019及Web5189已停止，正式API/Worker/Web保持。隔离代码与运行证据已私有备份，开发worktree随后清理；无提交/push。原每日选题9.5/9.6仍开放。
