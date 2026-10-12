# Persona Creative Studio — 两个角色文字合同验收

## 2026-10-07 自动浏览器入口复验

用户确认Dock手动Chrome正常。本轮只修现有验收入口：显式`PERSONA_TEXT_BROWSER`仍优先；macOS未指定时复用已有Playwright headless shell，其他环境保持Playwright默认。不再硬编码日常GUI Chrome，不新增安装/依赖，不修改浏览器资料或禁用sandbox。

自动选择/实际启动探针PASS；现有脚本用全新临时SQLite与Mock重新通过**24检查点、零pageErrors、exit0**，两个角色均走到审批/授权/本地ZIP。初次旧notice断言超时后只更新为当前页面真实文案，没有为测试改变业务行为。报告和截图/ZIP：`/var/folders/g6/h9g70y1957s6_qn5hx6480nm0000gn/T/aics-persona-text-browser-CsXCh3`。临时18331/15331服务已停止，正式数据/配置/运行服务未变。

本轮不重新运行完整backend/Web构建，也不把下方10月6日历史门禁当本轮结果；当前整体仍118/147，Mock不证明真实文章、图文或声音质量。

## 需求与验收范围

2026-10-06，基于已批准的`add-persona-creative-studio`实施。用户要求先把AI科技研发技术博主与日常生活方式博主的文字创作串通，单独验收后再做图文，最后音频。当前Git为`main@341ead8`＋既有未提交ACO/Creation Recipe/F8及本轮修改，暂存区为空。

本次结果：两个角色的文字**产品链路与合同通过**，不是147项全部完成，也不是实模型创作质量已通过。任务按完整证据保守核对为65/147，剩82项。真实Provider文章、人工固定rubric、正式Starter初始化仍待单独授权。

## 已完成链路

```text
Starter预览 → 显式初始化隔离角色 → 保存身份且保留创作配置
  → Project / Unit / Brief / exact frozen Fact Boundary
  → Evidence → Angle → Outline（只接受Attempt，不制造Master）
  → Draft（3候选）→ Quality（warning逐项人工处置）
  → Refine（2候选）→ Title → Final（人工改标题、显式接受）
  → Final Quality → Master revision 3
  → Candidate v4 → Review Approval → copy_package授权 → 本地ZIP
```

两个角色的Skill/Preset/Quality及IdentitySnapshot独立。生活角色当前事实模式必须有经live Source验证的新鲜事实来源；近期opinion、legacy或未证明来源不能冒充新鲜事实。Brand仅提供约束，不继承创作风格。Intermediate output和业务Master各守真源；warning人工接受不把原检查状态改成pass。

## 持久实现与证据位置

| 范围 | 仓库文件 |
|---|---|
| 八个研究/文字方法包 | `apps/api/app/studio_skills/`，每包含SKILL、machine contract、META、fixture |
| Catalog / Resolver / Starter / Intermediate Stage | `studio_creative_catalog.py`、`creative_configuration.py`、`starter_personas.py`、`creative_method_stage.py` |
| Master / Checks / 显式接受 | `stage_master_adoptions.py`、`stage_domain_adoptions.py`、`text_master_checks.py`，复用既有Master/CheckRun |
| 页面 | `PersonaCreativeConfig.tsx`、`IdentityWorkspace.tsx`、`StageCreativeResultPanel.tsx`、`StageDomainResultPanel.tsx` |
| 持久回归 | `apps/api/tests/test_persona_creative_studio.py`及Stage/continuation相关测试 |
| 隔离浏览器脚本 | `apps/web/scripts/persona-text-browser-acceptance.mjs` |

脚本要求`PERSONA_TEXT_ISOLATED=yes`、隔离Mock API及空Persona库，拒绝非127.0.0.1浏览器请求。不得指向正式API。当前运行使用独立18331/15331端口；脚本调用Mock，不调用CPA/MiniMax或公众号。

2026-10-07启动修正：原脚本硬编码系统Google Chrome已改为可选`PERSONA_TEXT_BROWSER`，macOS未指定时复用已安装headless shell，其他环境保留Playwright默认。不新增依赖/安装、不碰日常Chrome登录资料。新鲜启动探针与全流程24检查点均通过，详情见顶部；这与下面10月6日历史证据分开。

## 新鲜门禁

| 门禁 | 本次直接运行结果 |
|---|---|
| 完整backend，既有标准环境 | **1968 passed / 28 skipped / 80 warnings，106.87s，exit0** |
| Persona＋continuation定向 | **75 passed，exit0** |
| TypeScript/Vite | **PASS** |
| FE-P1 | **PASS**；Projects 224.22 kB raw / 72.73 kB gzip |
| Common Production baseline | 282.44 kB raw / 90.17 kB gzip；无通用TipTap/XYFlow依赖污染 |
| Text lazy closure | 609.20 kB raw / 190.38 kB gzip；Graphic/Video不加载TipTap |
| 范围Ruff | **PASS** |
| 隔离真实Chrome浏览器 | **24检查点PASS，pageErrors=[]** |
| OpenSpec strict | **38 passed / 0 failed，exit0** |
| diff / 新增文件空白 | **PASS**；72个范围内untracked文件无空白诊断 |

完整backend命令为`TASK_QUEUE_ENABLED=false .venv/bin/pytest -q`，cwd为`apps/api`。80条warnings保留，没有通过修改无关健康检查掩盖它们。一次带`APP_ENV=test`的非标准全量命令触发继承health测试环境分支；改回现有标准命令通过，健康业务/断言未为此放宽。

收尾新增文件检查发现方法资源多余EOF空行，仅机械规范化33文件；runtime解析后的instruction/contract/provenance hash不变。规范化后Persona持久回归新鲜57 passed/1条继承warning。隔离18331/15331服务已停止且无监听，正式8000 readiness仍ready。

## 浏览器产物与精确绑定

本次证据目录：

`/var/folders/g6/h9g70y1957s6_qn5hx6480nm0000gn/T/aics-persona-text-browser-EOL3Fj`

包含`report.json`、两个角色Recipe/Review截图及两个ZIP。运行库为`/tmp/aics-persona-text-VCcLhl/studio.db`，已有迁移链升级到`crs000000001`；这不是正式库迁移，也没有新增migration。

| 角色 | Persona / Project / Unit | 最终Master | payload hash |
|---|---|---|---|
| AI科技研发 | 1 / 1 / 1 | 3，revision3 | `78ae8d914612b3f37bc95a8eb7fcc962d05a8b516b997c71548ccb1eb5d28ec6` |
| 日常生活 | 2 / 2 / 2 | 6，revision3 | `eaa7ec2a439c7f9b0f17c2ff27b25e64385b2b1032f7d0c8c7dc18750b323772` |

ZIP含`manifest.json`、`content.md`和`publish-guide.md`；frozen Master/Identity绑定、人工最终标题与下载包hash对应。Mock正文很短，不能称长文内容质量已验收；本地ZIP不等于公开发布。

## 定向代码复核及修正

- 数值claim引用必须覆盖同一block/list item的实际claim range；不能因段落其他位置有citation就通过。持久参数化回归、5个定向测试和独立只读探针通过。
- 身份“基本资料”保存以前会只重建常规字段，丢失creative profile。现在从本级最新revision保留非该页面管理字段，仅重建自身字段；不把effective继承值偷偷写成override。浏览器保存/刷新及独立探针通过。
- 中间结果接受后的回读以前错误假设通用`output_json.result`，造成500。现在验证accepted handoff和精确candidate，回读该不可变Attempt内容；篡改target409、foreign403、重复GET零写入均由持久测试与定向独立复核通过。

独立复核是Text共享基础与上述修正的定向backend/data/security review，不冒充所有模态UX或真实创作质量复核。

## 待完成及关键设计

Text当前仍有高级Memory组合UI、override diff/readiness、Settings inventory、部分lifestyle语义检查及可选critic等未完整验收项。跨模态资源验证只完成Text部分，不给整项勾选。接下来先单独验收两篇真实Provider文章，再按用户顺序进行Graphic与Audio。

Mock只证明合同；current事实不伪造；Custom精确模型不可用就阻断；Composed只走已声明绑定链；接受成果不自动改Persona/Workflow；不新增Master/素材真源或持久表。

## 依赖、运行和授权

沿用现有API/Web/Worker、SQLite、本地素材库与loopback启动方式，无新依赖。正式readiness只读检查返回200/ready/schema true；本批未写正式库、私有配置、Starter记录或调用真实供应商，不发送公众号，不归档/提交/推送。隔离服务验收结束后停止，正式8000/5173/Worker保持原状。

实际使用skills：OpenSpec apply约束范围/勾选证据；executing-plans/writing-plans维持Text-first计划；systematic-debugging与test-driven-development定位并固化真实断点；requesting-code-review和verification-before-completion用于定向复核与新鲜门禁。
