# 手动来源配置 Implementation Plan

**Goal:** 补齐手动添加、配置与角色关联入口，和自动来源统一管理；先完成可确认规范，确认后实施。

**Architecture:** 复用DiscoverySource、PersonaSourceSubscription、来源JSON元数据和既有HTTP/Celery流程，人工配置优先，选题统一经过已有质量检查。

**Tech Stack:** 现有FastAPI/SQLAlchemy/Celery与React/TypeScript；提案阶段仅Markdown。

同一需求持续维护本文件与tasks.md。确认后使用executing-plans逐项实施；不预设其他模型分工，不新增测试代码，不在提案阶段改产品或运行数据。

- [x] /// 核对现有来源面板/API/采集与角色维护，确认缺口及复用边界。
- [x] /// 创建本新增能力的OpenSpec proposal/design/specs/tasks，与前一每日选题change区分授权范围。
- [x] /// 完成规范一致性及strict检查，提交用户确认。
- [x] /// 获确认后按tasks.md第1节实现登记、配置、去重与持久元数据。
- [x] /// 按第2节完成后台验证、人工关联保护及自然消费。
- [x] /// 按第3节接通统一来源管理页面。
- [x] /// 按第4节完成验证、独立复核、获准的正式接入和归档。

具体路径、API、状态和验收场景以design.md及specs为准。前一change的自然日批与归档不并入本提案，也不提前关闭。

## 已确认实施

用户明确授权按方案开发。/// 先复用现有字段实现人工管理服务与API，再接订阅维护/后台扫描，最后接统一表单并验收。必要时新增单一 `services/discovery_sources.py` 承担管理、验证、人工订阅协调，避免把登记/采集职责堆入同一文件。
