# 规范复核

## 范围与一致性自查（2026-10-15）

| 检查 | 结论 |
| --- | --- |
| 三类来源、角色多选、统一管理 | proposal/design/spec/tasks均覆盖 |
| 已有来源重复添加与主页/RSS别名 | 复用同一owner身份，不按同域合并，不覆盖现有设置 |
| 人工角色选择与自动重研究 | 明确人工集合优先，移除不复活，画像修订不丢失关联 |
| 暂停、权限、角色归属与历史 | 沿用原边界，配置审计、无硬删除历史 |
| 失败和无角色储备 | 保存与可采集分开，显式原因，不承诺所有平台可采集 |
| 质量与执行范围 | 复用既有日批，不补题、不变更数量/时刻，不赋予事实确认或转载权 |
| 前一change授权边界 | 本提案独立待确认，不影响原43/45日批验收与归档 |

本轮为规范自查，无代码审阅或实现验收结论。实施后再在此追加独立复核及缺陷关闭证据。

校验回执：`openspec validate add-manual-discovery-source-management --strict`通过；`openspec status`四项artifact done仅表示规范齐备，非开发完成；本change 0/16开发任务。

## 实施审计与关闭结果

code-reviewer、Python reviewer及TypeScript reviewer独立只读复核通过。

| 发现 | 修复及复核证据 |
| --- | --- |
| 自动发现经feed二次命中绕过人工角色 | 最终来源统一锁定刷新后检查人工模式，HTTP期间新配置竞态操作通过 |
| 协调/启动验证旧JSON覆盖新设置 | owner→source→Persona锁序，网络外锁定快照，revision/request_id/lease共同验证 |
| 活跃容量旧计数 | 最终启用事务重新查当前容量，临时等待与恢复操作通过 |
| HTML单篇误认持续入口 | 不把单个JSON-LD文章当列表；RSS/Atom及明确JSON列表仍支持 |
| 手动+自动发现证据被refresh丢弃 | 明确flush后协调，origin=both断言通过 |
| 原类型被UI默认改写 | 保留原类型，未改kind则省略字段，独立TS复核通过 |
| 合并目标被角色过滤隐藏 | 未确认通知独立读取、按id解析目标，实际浏览器跨角色过滤验收通过 |
| SQLite缓存时间比较使采集失败 | 租约UPDATE禁用ORM内存evaluate，数据库条件保持，真实Beat增量采集成功 |

未新增测试代码。相关现有检查81通过/1既有warning，Web构建/bundle、Ruff、OpenSpec strict通过。正常UI及隔离自然Beat/Worker真实HTTP、模型产物验收均完成；原正式经营角色下一自然日仍属前一change，未借此关闭。

博主入口实际限定已验证：公开链接可添加储备；现有适配器不能识别MartinFowler首页持续入口时，明确adapter_unavailable，不承诺任意博主可采集。可用RSS可按Feed地址添加，保留当前最小支持范围。
