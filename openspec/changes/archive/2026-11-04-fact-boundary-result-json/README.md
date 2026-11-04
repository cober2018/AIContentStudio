# fact-boundary-result-json

## 需求背景
有事实边界以后，第三方模型交事实、读模板都报参数错误（数据其实存上了）。来源：fact-boundary-topic-templates 的审计记录。详见 proposal.md。

## 当前阶段
2026-11-04 用户确认，实施完成、副本验证通过（progress.md）。已重启生效，2026-11-04 已归档、已提交（未推送）。

## 代码位置
apps/api/app/services/fact_templates.py（`current()`）

## 下一步
无（推送等用户说「推送」）。
