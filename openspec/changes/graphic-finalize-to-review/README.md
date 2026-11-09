# graphic-finalize-to-review

- 当前阶段：已实施、已上线本地服务，未提交；等作品 100 真实验证
- 需求：图文定稿后平台自动出图、存成图、生成渠道版本并冻结候选，送进「审阅与交付」
- 成果文件：proposal.md、specs/article-writer/spec.md、tasks.md、task_plan.md、progress.md、findings.md
- 代码：apps/api/app/services/graphic_review.py（新）、article_chain.py（采用后触发、定稿锁旁路、review 状态、send_to_review）、routers/edit_agent.py（POST .../article-chain/send-to-review）、apps/web/src/product/ArticleChainPanel.tsx（状态与重试按钮）；测试 apps/api/tests/test_graphic_finalize_to_review.py
- 下一步：用户在作品 100 点「重新出图并送审」→ 审阅与交付审批 → 推「阿军的退休日记」草稿箱前再问用户；然后 archive；「提交吧」再提交

- 2026-11-09 补充需求（成图验收后才定稿；AI 标识改放正文）：方案已写，等用户确认
