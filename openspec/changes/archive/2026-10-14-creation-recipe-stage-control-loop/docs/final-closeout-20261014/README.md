# Recipe 独立收尾证据

## PRD / 需求背景

用户2026-10-14确认补齐持久测试并独立收尾Creation Recipe；复用main既有实现，不扩展自动发布或新业务状态。

## 目录结构

- recipe-learning-feedback-red.log / green.log：非法反馈ID原TypeError两例到422、零claim/调用。
- recipe-learning-resume-green.log：48个新learning案例与既有核心相关159通过。
- candidate-backend.log / candidate-web.log / candidate-ruff.log：实际HEAD＋5路径候选完整门禁；完成状态以日志尾部为准。
- persistent-coverage.json：Requirement到既有/新增持久覆盖。
- daily-product-entry.json：正常UI入口实际读取/预览的覆盖与限制，未声称真实新生成。

## 已完成 / TODO

新增learning48、domain11、continuation5、bounds2共66持久案例，既有核心合同/receipt/resolver/Master覆盖复用。仅stage_tuning判型与set去重顺序两行修复；schema门禁期望沿用当前a3。独立Python复核48通过/Ruff批准，领域/整体独立复核通过。最终candidate2670通过/28跳过/1已知wewrite环境豁免，Web/FE-P1/Ruff/strict40通过。原中断与首轮实际失败日志均保留。

## 关键设计决策

反馈/采用/关联/事务/claim/默认隔离由真实服务与隔离SQLite执行，仅外部模型/媒体替换为受控Provider。不能将受控媒体夹具当真实创作质量。候选以HEAD和本轮5路径构造；共享脏工作区的channel_methods/plugin/Studio资源均排除、原字节保全。Recipe同步自身ADDED requirements，align15.7和已归档multiplatform原样保全。

## 依赖与启动

沿用apps/api/.venv、SQLite与React/Vite，无新增依赖或生产迁移。产品API8000，Web5173原Vite；临时隔离API18767/Web5174仅用于读取真实已有成品。原生成harness不可重跑，未调用真实生成/发布。

## 新鲜完整候选门禁通过（2026-10-14）

实际HEAD＋7归属文件候选：全量2670 passed / 28 skipped / 1既有wewrite环境失败 / 101 warnings / 152.00秒；该唯一断链已按用户口径豁免。Variant深度错误已关闭，旧Worker runtime schema初始化前提明确记录。TypeScript/Vite/FE-P1、Ruff全app＋归属测试、strict40/40、diff通过；两位独立代码/Python复核批准。19.6关闭，143/144，唯一剩生命周期19.12；本轮66持久案例和两处最小缺陷修复，无新增依赖/正式迁移/生成调用。
