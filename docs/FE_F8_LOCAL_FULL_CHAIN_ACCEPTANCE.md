# FE-F8 本机产品闭环验收

日期：2026-10-03

正式基准：SQLite + 本地素材库 + loopback-only。外部 Publisher、公众号 API、真实模型和 PublishedContentRecord/Performance/Learning 分支不在本记录中执行。

## 同项目当前实现实测

```text
Opportunity
  → ContentProject
  → IdentitySnapshot / CreativeBrief / Fact Boundary
  → Text / Graphic / Video Master
  → ChannelVariant
  → Candidate v4/v5
  → Approval / Authorization
  → local copy_package/manual_handoff
```

## 新鲜证据

隔离 SQLite `f7d000000001`、复制的本地素材和 loopback API/Web；User 表只有批准的旧字段，没有待批准 identity issuer/subject 列。复用既有 F6E 浏览器脚本，用临时入口包装把创建项目替换为真实 Opportunity assessment/qualified/convert API；业务代码与永久验收脚本没有为通过验收而改写。

- Opportunity 4 → 显式原子转换 → Project 4；重复转换返回同一项目。转换后的 Overview 仍为 `evidence_needed`，没有自动冻结事实。
- 同一 Project 4 的 Text Unit 6 / Graphic Unit 7 / Video Unit 8 共用项目 Brief/Boundary，各自固定 IdentitySnapshot；Matrix 读取零写入，显式选择才创建 Unit。
- Text Master 6 → WeChat article / X thread / X single → Candidate 6/7/8 → Approval → Target 7/8/9 → 三份精确本地包。
- Graphic Master 8 → 经人工 attestation 的精确 image bytes → Xiaohongshu image_note → Candidate 9 / Target 11 → 有序图片包；仅 prompt 的 Master 被拦截。
- Video Master 9 → Douyin spoken_script → Candidate 10 / Target 12 → 脚本和明确标记 estimated 的 SRT。**这条链不是成片视频**；另有 Golden 的真实本地 H.264 成片验收，见 Golden README。
- 13 个浏览器 gate 全部通过，`pageErrors=[]`：包括三个渠道预览/保存/检查/审批/ZIP、异步旧响应不能覆盖当前选择、Workflow/Master 本地 dirty 独立、Unknown 不自动重发、同账号 reconciliation、Master 更新导致 Variant stale、实时撤权阻止旧包、归档只读。

证据目录：`/var/folders/g6/h9g70y1957s6_qn5hx6480nm0000gn/T/aicontent-f6e-browser-evidence-S2QaBN/`，包含 `report.json` 与五个 ZIP。只写隔离夹具，未触及正式库或真实账号。

## F8 运行状态页面

`/var/folders/g6/h9g70y1957s6_qn5hx6480nm0000gn/T/aics-f8-status-browser-rWjnmA/` 的报告记录 7 个新鲜 gate：初始库存零就绪/写操作，显式 ready 200，503 安全失败，HTTP/body 不一致不能冒充通过，超时不保留旧成功，窗口 focus 不自动重试，viewer 无操作入口且服务端 audit 403；无页面错误。

安全补丁后另复验新 Settings 运行状态和 legacy Settings：读取 dsh 配置零 HTTP 请求，显示 `not_probed` 而不是离线；未发 POST/probe。前端构建及 FE-P1 预算通过。

## 恢复后重复导出

在 Unknown/撤权/归档负向步骤前在线备份 Project 4 的数据库并复制其唯一引用的字节对象。恢复库与恢复素材同时启动后，同一五份包的 ZIP entry 集合和每个解压文件的 bytes 均与浏览器原包一致；不是只检查源素材 hash。详见恢复记录。

## 未执行项

- 真实 Publisher、远端账号读回、公众号/其他平台公开发布：`not_exercised`；不能由本地 package 或历史草稿代替。
- `PublishedContentRecord → Performance → LearningCandidate`：保持未执行，等待真实 `human_confirmed` DeliveryReceipt。
