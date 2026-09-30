# FE-F7 共享素材消费与 Provider 指引验收

## 范围与结果

本批依已批准 F7 tasks 4.9 / 9.7 实施，F7 84/105 → 86/105；无新表、migration、外部发布或 Provider 探测。F8 未实施。本报告不是 F7 最终验收。

```
Search fixture → preview（未入库、不可发布）
→ 人工核对许可 / 完整署名 / 权利
→ 唯一 MaterialRevision + ProjectMaterialReference
├─ Text v2 image → Master save / Production 回读
└─ Video v2 timeline → Master save / Production 回读
公开使用权撤销 → 两者 rights blocker / freeze unavailable
历史 Master / 素材字节不复制、不改写
```

Settings 模型分区指引为只读安全投影，加载 search/image/video/tts/asr descriptor 与安全 registration 标识。缺实现 unavailable；已加载或有配置记录仍 unchecked / verified=false。不会读取秘密配置、调用 runtime fingerprint、发网络请求、启动子进程或调用 Provider，也没有假 Save。

## 实际门禁

| 门禁 | 本批实跑结果 |
|---|---|
| 全后端 | 1322 passed / 2 skipped / 8 既有 warnings，52.62s |
| 搜索 / 指引 / Renderer 定向 | 48 passed / 1 既有 warning |
| TypeScript / Vite / FE-P1 | PASS |
| OpenSpec 全量 strict | 30/30 PASS |
| 范围 Ruff / git diff --check | PASS |
| 独立窄复核 | APPROVE，只读实现 / 测试 / 脚本审查，未重跑命令 |
| 隔离浏览器 | 7 gates / 0 page errors |

指引测试先因缺 `provider_guidance` 失败三项，最小实现后通过；不访问运行时的恶意 descriptor、配置不冒充 verified、非法标识过滤及每类 100 项上限均有回归。

FE-P1 raw/gzip kB：Projects 224.84/72.94，Assets 258.81/82.80，Settings 230.46/75.17，common Production 280.03/89.09；指引独立 chunk 1.24/0.91。通用 Production 不导入 TipTap / XYFlow。

## 浏览器证据与边界

脚本 `apps/web/scripts/fe-f7-search-browser-acceptance.mjs` 实际浏览器确认：显式搜索不入库、预览许可/署名锁定且默认未确认权利、人工接受精确版本、刷新持久化、跨 Unit 精确消费回读、撤权阻断、Settings 只读诚实指引。

- 报告：`/var/folders/g6/h9g70y1957s6_qn5hx6480nm0000gn/T/aicontent-f7-search-browser-RHML5J/report.json`
- SQLite/media：`/tmp/aicontent-f7-media.rfpQTj/`
- 模型 mock / 搜索与 PNG fixture 仅隔离验收，不证明真实 Wikimedia 或生成 Provider 可用。
- Video 保存 / 回读不等于自动成片；自动媒体 Renderer 仍待完成。
- 撤权阻断公开就绪与冻结，不把私有未就绪编辑误当成非法写入。
- 首次扩展脚本因重复 Master ID 文案触发 strict locator；修正定位后完整重跑七项通过，失败运行未算通过。

## 待完成与操作边界

真实单次生成 / TTS / 外部 ASR、自动媒体 Renderer、精确账号绑定且不改稿的 Publisher、F7 最终门禁和 F8 仍待完成。Renderer 迁移头保持 f7b000000001；本批无新迁移。仅本地 main 提交，不 push / deploy / 生产迁移 / canonical sync / archive。
