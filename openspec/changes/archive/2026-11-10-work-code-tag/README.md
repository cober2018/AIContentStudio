# work-code-tag

## 需求背景
沟通时都按作品编号（如「作品 97」）说，但界面上编号不好找。用户要求在三个工作台的标题前面放一个醒目的作品编号标签。详见 proposal.md。

## 当前阶段
2026-11-10 用户确认（追加待审成稿页），已实现，tsc + build 通过；未提交、未归档。

## 代码位置
apps/web/src/components/ui.tsx（WorkCode）；apps/web/src/product/ProductionContextHeader.tsx、ProductionQueuePage.tsx、SearchPromotionWorkbench.tsx、ProjectReviewCenter.tsx

## 下一步
用户刷新页面看效果；说「提交吧」再归档提交。
