# 交事实、读模板的结果能传回第三方模型

## Why
项目有了事实边界以后，第三方模型调 `submit_facts`、`get_fact_template` 都返回参数错误（422），但事实其实已冻结入库（作品 94：事实边界第 1、2 版）。原因是 `fact_templates.current()` 把冻结时间 `frozen_at` 原样（datetime）放进结果，MCP 结果转不成 JSON。模型因此以为没交成功、会重复提交（每次多一版事实边界），也看不到退回原因和当前事实边界。审计记录见 `openspec/changes/archive/2026-11-03-fact-boundary-topic-templates/review.md`。

## What Changes
- `fact_templates.current()` 的 `frozen_at` 改成 ISO 字符串（没有时为 null），和 `routers/fact_packs.py` 的写法一致。
- 网页「当前事实边界」接口同样返回字符串，页面没用这个字段，不受影响。

## Impact
- 代码：`apps/api/app/services/fact_templates.py` 一行。
- 不改数据、不改接口字段名；已存的事实边界不动。
- 生效要重启 API。
