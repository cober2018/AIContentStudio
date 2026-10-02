# F7 模型提交与真实调用验收

## 范围

2026-10-03 用户确认：先把模型登记、能力路由的必要依赖和整理后的“模型与 AI”页面提交到本地 main，再验证已保存的 CPA 模型。其他未完成的 F7 消费者/持久任务和 F8 改动不混入本次提交。不 push、部署、迁移正式库或重复生成视频。

## 可复现提交门禁

在 main@931915d 导出快照中只加入本次选定文件，沿用已有依赖；配置类只加入 shared runtime guard 必需的 app_env，Team 页面保留已提交行为，不带入未完成 F8。

- 既有模型路由/设置回归：85 passed，1 个既有弃用警告。
- Web TypeScript/Vite、FE-P1 和既有路由状态脚本：PASS。
- /settings：236.26 kB raw / 77.16 kB gzip；/projects：224.89 / 72.97 kB。
- 全部 OpenSpec strict：33/33；范围 Ruff：PASS。
- 首次全量：1655 passed / 28 skipped / 1 failed。旧 Worker 测试使用模块级文件数据库，而导出快照未初始化该库，失败为 no such table: content_job；未修改代码，随后仅初始化隔离临时数据库重跑。
- 隔离临时库初始化后全量重跑通过；补入工作区已有的 models_section 安全投影依赖（不含同文件 F8 Team 修改）后，再次精确全量：1656 passed / 28 skipped / 8 warnings（75.69 秒）。85 项相关回归与范围 Ruff 重新通过。未新增测试代码；跳过项不算 PASS。
- 隔离进程实际验证停用默认模型后设置仍 editable、availability=false，而模型执行继续拒绝，不借读取保护放宽执行。
- 精确 index diff-check、独立依赖复核与本地提交：执行后补记。

## 真实模型验收

使用系统已保存配置，凭据不回显、不改默认或用途路由。CPA 验收目标为 gemini-3.8-flash-high、claude-opus-4-6-thinking、grok-4.7 的短聊天及实际消费者路由；调用结果尚待执行，不引用旧 401 作为当前状态。

媒体验收与聊天分开。当前配置 revision 3 没有 media_plugins 或 capability_routes；不能把 CPA 聊天成功记为图像/视频/TTS/ASR 成功。MiniMax 优先查询原 H3 任务 448101822222777，禁止再次提交。正式任务恢复、素材权利与接受、完整浏览器验收继续按 active OpenSpec 判断，不提前勾选或归档。

## 依赖与操作边界

启动方式沿用根 README；无新增包或本次迁移。提交包含模型登记/路由服务、固定 MiniMax CLI adapter、模型设置 UI、已有回归文件及对应规格，不包含用户数据库、凭据或任何临时生成结果。

```text
精确提交快照 → 既有门禁/依赖复核 → 本地 commit
已保存 CPA 配置 → 实际短聊天 → 按能力记录证据
原 MiniMax job → 只读查询/安全下载 → 不确定则保留，不重发
```
