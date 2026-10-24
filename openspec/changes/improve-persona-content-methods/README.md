# 角色内容工作台：方法、风格与成品质量改进

## PRD / 需求背景

用户于 2026-10-19 要求以角色内容工作台为主，将 Easel 可吸收方法与六项补充整理为 OpenSpec，写清页面流程、Skills 分工和科技/生活对照验收，保留已经优化好的工作台与模型配置，先确认方案。

## 当前阶段与代码位置

**接手Agent续做完成，交回主Agent独立总验收 — 当前16/25（新增5项为接手自检，待复核），2026-10-20。** 科技文字/图文与两角色音频同条件A/B、生活图文A/B、新题科技三形态与生活文字/音频、6个视频导演计划已完成并本地包回读；生活文字B（Unknown155）、生活新题图文封面、两角色B真实成片、3.6/4.2/4.4与用户采纳仍开放。最新状态与复核顺序见 [development-handoff.md](development-handoff.md) 第0节，逐件结论与素材清单见 [review.md](review.md) 顶部。新风格尚未获用户采纳，不能归档。

**2026-10-21 科技新题成片第二版（U72/执行4）**：用户评审第一版后，按“平台功能→网上素材→代码生成”顺序重做：作者演示实拍入库（仅本地评审）、作品级开启脚本方法后重写脚本（70秒竖屏）、旁白素材116、Master124带实拍剪辑表与授权配乐、AE15合成+Resolve主剪，20个产物已提交并请求人工审阅（未代为接受）。成片：`apps/api/app/media/.creative-executions/1/4/outputs/rough_cut.mp4`。发现与平台缺口见findings.md同日条目。

代码基线：`main@8539806` 加相邻未提交改动。开发提示词见 [AGENT_DEVELOPMENT_PROMPT.md](AGENT_DEVELOPMENT_PROMPT.md)。交接见 [development-handoff.md](development-handoff.md)。真实试验通过正常API新增，交接前已与私有开工快照逐行比对14张表的原有记录，新增试验行另计；没有直接写库制造完成。

## 目录结构与审阅顺序

1. [proposal.md](proposal.md)：目标、范围与保留边界。
2. [design.md](design.md)：第1节页面流程，第2节六项补充，第3节Skills分工，第7节双角色对照验收。
3. [specs/](specs/)：六项现有 capability 的增量要求。
4. [tasks.md](tasks.md)：25项实施及验收任务，按已批准范围执行。
5. [task_plan.md](task_plan.md)、[progress.md](progress.md)、[findings.md](findings.md)、[review.md](review.md)：持续计划、实际进展、研究及方案复核。
6. `evidence/`：原 Easel 布局研究证据与本提案检查。原研究目录保留跳转入口，本目录为唯一持续维护成果。

## 方案要点

- 保留角色五步：选题与资料 → 内容方案 → 制作内容 → 审阅修改 → 交付。默认展示当前结果、问题与下一步，方法/模型/历史按需展开。
- 角色参考、共用方法、角色风格、知识用途、分形态方案与定位反馈均复用现有实体；不另造角色/SKU/工作流。
- 先试用再明确采纳；新方法版本不覆盖历史。科技和生活独立，商品工作台继续独立。
- 文字/图文/音频做同条件 A/B 与新主题实际迁移；视频做 A/B 计划、各一支真实候选小样和新主题计划。缺素材时成片验收如实待完成。
- 模型、路由、原音色与生成参数保持；技术通过、内容质量和用户角色风格决定分开记录。

## 已完成

方法/参考/计划合同与上述业务接入已完成。最新代码601项相关既有检查、Web完整构建及A17最终只读重放30/30通过；实际TS函数33项/原JSX渲染36项通过。已修分页、参数继承、未知状态、冻结依据、反馈消费、导演方案丢失及真实检查误报。旧v1和原作品保全复读通过。证据在evidence/development与evidence/independent，准确时间/范围见review.md及handoff-checks.json。技术检查不表示真实质量通过。

## 待完成 / TODO

主Agent独立复核本轮5项自检勾选及A18–A21修复；用户提供/决定：科技新题成片第二版（执行4）观看试听与是否接受、是否把第二版暴露的平台缺口（视频阶段素材目录、多来源剪辑清单、响度限幅、作品配置覆盖剪辑方法）立项；生活新题图文封面素材、两角色B视频成片素材与执行方式、Unknown155处理、10段音频试听、逐角色/形式是否采纳@2；之后补3.6完整开关矩阵、4.2音视频时间定位、4.4隔离UI综合边界，再做6.1汇总、6.2采纳、6.3同步与归档。开放问题：run质检阶段图文快照超128KiB、科技角色capability-memory遮蔽@2、媒体暂存名额、UTC日期判定。

## 关键设计决策

复用原五步与原 workflow 真值；平台保存流程与产物，Skills 提供阶段方法，执行器按既有合同制作；角色方法和风格与模型配置分开。试验未通过、用户未决定或视频未交付时不提前归档。

## 依赖与启动方式

实现无新增依赖。隔离自检使用API8019 + Web5174、/tmp SQLite和Mock，关闭正式启动钩子。正式API8000已按原launchd命令加载新方法及检查修复，原环境/模型/Worker保留，Web5173未重启；回执在 `evidence/independent/*api-reload.json`。使用已安装 OpenSpec CLI：

`OPENSPEC_TELEMETRY=0 openspec validate improve-persona-content-methods --strict`

后续实现沿用本机 API8000 / Web5173、现有生成能力及 Resolve/AE MCP，不安装 Easel 工具链。CLI status 的 artifacts complete 只表示方案文件齐全，实施状态以本 README 和 tasks 为准。
