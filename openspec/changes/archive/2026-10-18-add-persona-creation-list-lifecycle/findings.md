# 发现与决策

## 2026-10-18

- ProductionQueuePage.tsx 只提供继续创作与包含归档历史，缺归档/删除操作。
- content_projects.py 的旧 DELETE 根据 _has_execution_history 决定归档或物理删除；新入口拟采用显式动作，兼容旧调用。
- 旧 status=archived 还用于身份替换，不能一概恢复；新生命周期独立记录。
- ProductionWorkspace.tsx 五步入口可达；角色科技样片 unit13 的 Master 和素材可读，但当前 channel_form_missing 阻止冻结。
- unit13 creation-recipe API run_id 为 null，界面各制作阶段未开始；已有样片不能代表当前新 Recipe 完成。
- 清单含商品题材旧样片 unit14，其 production_domain 为 persona；不根据标题擅自迁移。
- 角色页“详细商品资料”“核心购买理由 / 表达”为复用文案问题，作为可选建议记录，不加入本次清单管理实施范围。
- 图谱 MCP 当前未提供可调用工具，本次使用定向文件查询。

## 实施确认

1. 新生命周期必须覆盖原归档守卫及首页/知识资料查询；历史读接口继续可读，业务制作状态原样保留。
2. 复用 lock_project_context 序列化生命周期与运行入口，现有项目权限和事件审计不另建体系。
3. 历史 bootstrap 迁移可能直接建当前模型字段，新迁移检查列是否存在，正式旧库只新增列。
4. 不清理媒体文件、不恢复身份替换旧版本，不对正式样片做删除验收。
